from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import Mock
import asyncio
import json
from pathlib import Path

import pytest

from app import db
from app.api import precomputed, positions
from app.api.public_data import PublicDataUnavailable
from app import request_timing


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = [('value',)]

    def execute(self, query, params):
        self.connection.calls.append((query, params))
        if self.connection.fault == 'execute':
            raise RuntimeError('private query detail')

    def fetchall(self):
        if self.connection.fault == 'fetch':
            raise RuntimeError('private fetch detail')
        if self.connection.fault == 'conversion':
            self.description = [None]
        return [(7,)]

    def close(self):
        self.connection.cursor_closes += 1
        if self.connection.fault == 'cursor_close':
            raise RuntimeError('private cursor detail')


class Connection:
    def __init__(self, fault=None):
        self.fault = fault
        self.calls = []
        self.rollbacks = self.closes = self.cursor_closes = 0

    def cursor(self):
        return Cursor(self)

    def rollback(self):
        self.rollbacks += 1
        if self.fault == 'rollback':
            raise RuntimeError('private reset detail')

    def close(self):
        self.closes += 1
        if self.fault == 'close':
            raise RuntimeError('private close detail')


def test_reuses_only_inside_scope_with_identical_queries(monkeypatch):
    connections = []
    def connect():
        result = Connection()
        connections.append(result)
        return result
    monkeypatch.setattr(precomputed, 'get_connection', connect)
    queries = [('SELECT %s', (7,)), ('SELECT %s + 0', (7,))]
    baseline = [precomputed._query_all_dicts(*q) for q in queries]
    with db.precomputed_read_scope():
        actual = [precomputed._query_all_dicts(*q) for q in queries]
    assert actual == baseline
    assert len(connections) == 3
    assert connections[-1].calls == queries
    assert connections[-1].rollbacks == 2
    assert connections[-1].cursor_closes == 2
    assert [c.closes for c in connections] == [1, 1, 1]
    assert db._read_scope.get() is None


@pytest.mark.parametrize('fault', ['execute', 'fetch', 'conversion', 'cursor_close', 'rollback'])
def test_fault_discards_before_later_read_and_preserves_sanitization(monkeypatch, fault):
    failed, good = Connection(fault), Connection()
    connect = Mock(side_effect=[failed, good])
    monkeypatch.setattr(precomputed, 'get_connection', connect)
    with db.precomputed_read_scope():
        with pytest.raises(PublicDataUnavailable) as error:
            precomputed._query_all_dicts('SELECT %s', (7,))
        assert 'private' not in str(error.value)
        assert failed.closes == 1
        assert precomputed._query_all_dicts('SELECT %s', (7,)) == [{'value': 7}]
    assert good.rollbacks == good.closes == 1


def test_connect_failure_can_retry_in_fixture_continuation(monkeypatch):
    good = Connection()
    monkeypatch.setattr(precomputed, 'get_connection', Mock(side_effect=[RuntimeError('private'), good]))
    with db.precomputed_read_scope():
        with pytest.raises(PublicDataUnavailable):
            precomputed._query_all_dicts('SELECT 7')
        assert precomputed._query_all_dicts('SELECT 7') == [{'value': 7}]


def test_final_close_failure_is_sanitized_at_positions_boundary(monkeypatch):
    monkeypatch.setattr(precomputed, 'get_connection', lambda: Connection('close'))
    monkeypatch.setattr(positions, '_get_legislator_positions', lambda *a: precomputed._query_all_dicts('SELECT 7'))
    with pytest.raises(PublicDataUnavailable):
        positions.get_legislator_positions('unused', '119', None)
    assert db._read_scope.get() is None


def test_original_route_failure_survives_close_failure():
    with pytest.raises(ValueError, match='original'):
        with db.precomputed_read_scope():
            with db.precomputed_read_connection(lambda: Connection('close')):
                pass
            raise ValueError('original')
    assert db._read_scope.get() is None


def test_copied_context_cannot_cross_threads_or_reopen_closed_scope():
    with ThreadPoolExecutor(max_workers=1) as executor:
        with db.precomputed_read_scope():
            inherited = copy_context()
            def borrow():
                with db.precomputed_read_connection(lambda: pytest.fail('foreign connect')):
                    pass
            with pytest.raises(RuntimeError, match='foreign'):
                executor.submit(inherited.run, borrow).result()
        with pytest.raises(RuntimeError, match='closed'):
            inherited.run(borrow)


def test_nested_scope_and_overlapping_borrow_rejected():
    with db.precomputed_read_scope():
        with pytest.raises(RuntimeError, match='Nested'):
            with db.precomputed_read_scope():
                pass
        with db.precomputed_read_connection(Connection):
            with pytest.raises(RuntimeError, match='borrowed'):
                with db.precomputed_read_connection(Connection):
                    pass


def test_separate_workers_and_late_worker_keep_their_own_lifetime():
    entered, release = Event(), Event()
    connections = [Connection(), Connection()]
    def worker(index):
        with db.precomputed_read_scope():
            with db.precomputed_read_connection(lambda: connections[index]):
                if index == 0:
                    entered.set()
                    assert release.wait(5)
        return connections[index]
    with ThreadPoolExecutor(max_workers=2) as executor:
        late = executor.submit(worker, 0)
        assert entered.wait(5)
        other = executor.submit(worker, 1).result()
        assert other.closes == 1 and connections[0].closes == 0
        assert not late.cancel()  # Running sync work cannot be force-cancelled.
        release.set()
        assert late.result().closes == 1


@pytest.mark.parametrize('scope', ['119', '118', 'all'])
@pytest.mark.parametrize('published', [False, True])
def test_positions_scope_does_not_change_four_domain_dispatch(monkeypatch, scope, published):
    domains = ['JUSTICE_PUBLIC_SAFETY', 'NATIONAL_SECURITY_FOREIGN', 'ENVIRONMENT_ENERGY', 'EDUCATION_WORKFORCE']
    monkeypatch.setattr(positions, 'get_position_response', lambda **kw: {'positions': [{'domain': d} for d in domains]})
    monkeypatch.setattr(positions, 'get_legislator_profile', lambda **kw: {'bioguide_id': 'test'})
    monkeypatch.setattr(positions, 'public_review_state_entries', lambda: [{'member_id': 'test'}])
    publication_rows = [{'active': published}]
    monkeypatch.setattr(positions, '_load_publication_rows', lambda: publication_rows)
    seen = []
    def compose(*args):
        seen.append(args)
        return {'evidence': []}
    monkeypatch.setattr(positions, '_compose_position_evidence', compose)
    monkeypatch.setattr(positions, 'governed_position_summary', lambda *a, **k: {'recorded_votes': 0, 'yea_count': 0, 'nay_count': 0})
    baseline = positions._get_legislator_positions('test', scope, None)
    expected = list(seen)
    seen.clear()
    assert positions.get_legislator_positions('test', scope, None) == baseline
    assert seen == expected
    assert all(args[-1] is publication_rows for args in seen)


def test_global_connections_are_not_borrowed(monkeypatch):
    connections = []
    def connect():
        c = Connection()
        connections.append(c)
        return c
    monkeypatch.setattr(db, 'get_database', lambda: Mock(connect=connect))
    with db.precomputed_read_scope():
        with db.precomputed_read_connection():
            unrelated = db.get_connection()
            unrelated.close()
    assert len(connections) == 2
    assert [c.closes for c in connections] == [1, 1]


def test_asgi_cancellation_does_not_close_active_worker_connection(monkeypatch):
    entered, release, done = Event(), Event(), Event()
    connection = Connection()
    original_cursor = connection.cursor
    def cursor():
        value = original_cursor()
        original_execute = value.execute
        def execute(*args):
            entered.set()
            assert release.wait(5)
            original_execute(*args)
        value.execute = execute
        return value
    connection.cursor = cursor
    records = []
    monkeypatch.setattr(precomputed, 'get_connection', lambda: connection)
    monkeypatch.setattr(positions, '_get_legislator_positions', lambda *a: precomputed._query_all_dicts('SELECT 7'))
    monkeypatch.setattr(request_timing._logger, 'info', lambda fmt, payload: records.append(json.loads(payload)))
    def worker():
        try:
            return positions.get_legislator_positions('unused', '119', None)
        finally:
            done.set()
    async def application(scope, receive, send):
        await asyncio.to_thread(worker)
    async def noop(*args):
        pass
    async def scenario():
        task = asyncio.create_task(request_timing.RequestTimingMiddleware(application)(
            {'type': 'http', 'endpoint': positions.get_legislator_positions}, noop, noop))
        assert await asyncio.to_thread(entered.wait, 3)
        try:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert connection.closes == 0
            assert len(records) == 1
            assert 'request_aborted_wall_ms' in records[0]['positions']
        finally:
            release.set()
        assert await asyncio.to_thread(done.wait, 3)
        assert connection.closes == connection.rollbacks == 1
        assert len(records) == 1
    asyncio.run(scenario())


@pytest.mark.parametrize('scope', ['119', '118', 'all'])
def test_real_precomputed_callgraph_has_query_and_response_parity(monkeypatch, scope):
    trace = []
    connections = []
    class RowsCursor(Cursor):
        def execute(self, query, params):
            trace.append((query, params))
            if 'FROM legislators' in query:
                rows = [{'id': 1, 'bioguide_id': 'F000477', 'name_display': 'Valerie P. Foushee', 'chamber': 'house', 'state': 'NC', 'district': '4', 'party': 'D'}]
            elif 'SELECT classification_version' in query:
                rows = [{'classification_version': 'v1'}]
            elif 'MIN(DATE(rc.vote_date))' in query:
                rows = [{'window_start': '2025-01-01', 'window_end': '2025-12-31', 'congresses': [119], 'eligible_roll_call_count': 0}]
            else:
                rows = []
            self.description = [(key,) for key in rows[0]] if rows else []
            self.rows = [tuple(row.values()) for row in rows]
        def fetchall(self):
            return self.rows
    class RowsConnection(Connection):
        def cursor(self):
            return RowsCursor(self)
    def connect():
        c = RowsConnection()
        connections.append(c)
        return c
    monkeypatch.setattr(precomputed, 'get_connection', connect)
    monkeypatch.setattr(positions, '_load_publication_rows', lambda: [])
    baseline = positions._get_legislator_positions('leg_valerie_p_foushee', scope, None)
    queries = list(trace)
    baseline_connections = len(connections)
    trace.clear()
    connections.clear()
    assert positions.get_legislator_positions('leg_valerie_p_foushee', scope, None) == baseline
    assert trace == queries
    assert len(connections) == 2
    assert baseline_connections == len(queries)
    assert sum(c.rollbacks for c in connections) == len(queries)
    assert sum(c.cursor_closes for c in connections) == len(queries)


def test_disposable_harness_pins_address_and_credentials(monkeypatch):
    import psycopg
    from backend.tests.positions_disposable_postgres import DisposablePostgres
    # This guard test mocks connect and starts no cluster or filesystem writes.
    server = DisposablePostgres(Path(__file__).resolve().parents[2] / '.tmp/positions-reuse/mock-address-guard')
    server.started, server.port = True, 54321
    connect = Mock()
    monkeypatch.setattr(psycopg, 'connect', connect)
    monkeypatch.setenv('PGHOSTADDR', '192.0.2.1')
    monkeypatch.setenv('PGSERVICE', 'unowned')
    with pytest.raises(RuntimeError, match='Inherited libpq'):
        server.connect()
    connect.assert_not_called()
    monkeypatch.delenv('PGHOSTADDR')
    monkeypatch.delenv('PGSERVICE')
    server.connect()
    parameters = connect.call_args.kwargs
    assert parameters['host'] == parameters['hostaddr'] == '127.0.0.1'
    assert parameters['port'] == 54321
    assert parameters['password'] == ''
    assert parameters['user'] == 'experiment'
    assert parameters['passfile'] == str(server.directory / 'no-password-file')
