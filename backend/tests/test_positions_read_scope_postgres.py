"""Opt-in real transaction checks; never uses DATABASE_URL."""
from pathlib import Path
import os

import pytest
from psycopg import IsolationLevel
from psycopg.pq import TransactionStatus

from app import db
from app.api import precomputed
from app.api.public_data import PublicDataUnavailable
from backend.tests.positions_disposable_postgres import DisposablePostgres


pytestmark = pytest.mark.skipif(os.getenv('RUN_POSITIONS_DISPOSABLE') != '1', reason='explicit owned local PostgreSQL opt-in required')


@pytest.fixture(scope='module')
def postgres():
    with DisposablePostgres(Path(__file__).resolve().parents[2] / '.tmp/positions-reuse') as server:
        yield server


@pytest.mark.parametrize('isolation', [IsolationLevel.READ_COMMITTED, IsolationLevel.REPEATABLE_READ])
def test_queries_end_transactions_and_refresh_snapshots(postgres, monkeypatch, isolation):
    with postgres.connect() as setup:
        setup.execute('CREATE TABLE IF NOT EXISTS scope_snapshot (value integer)')
        setup.execute('TRUNCATE scope_snapshot')
        setup.execute('INSERT INTO scope_snapshot VALUES (1)')
    connections = []
    def connect():
        connection = postgres.connect()
        connection.isolation_level = isolation
        connections.append(connection)
        return connection
    monkeypatch.setattr(precomputed, 'get_connection', connect)
    with db.precomputed_read_scope():
        assert precomputed._query_all_dicts('SELECT value FROM scope_snapshot') == [{'value': 1}]
        assert connections[0].info.transaction_status == TransactionStatus.IDLE
        with postgres.connect() as update:
            update.execute('UPDATE scope_snapshot SET value = 2')
        assert precomputed._query_all_dicts('SELECT value FROM scope_snapshot') == [{'value': 2}]
        assert len(connections) == 1
        assert connections[0].autocommit is False
        assert connections[0].isolation_level == isolation
    assert connections[0].closed


def test_local_session_state_and_preparation_do_not_survive_query(postgres, monkeypatch):
    connections = []
    def connect():
        connection = postgres.connect()
        connections.append(connection)
        return connection
    monkeypatch.setattr(precomputed, 'get_connection', connect)
    with db.precomputed_read_scope():
        baseline = precomputed._query_all_dicts("SELECT current_setting('application_name') AS value")
        precomputed._query_all_dicts("SELECT set_config('application_name', 'transaction-only', true) AS value")
        assert precomputed._query_all_dicts("SELECT current_setting('application_name') AS value") == baseline
        for _ in range(8):
            assert precomputed._query_all_dicts('SELECT %s::integer AS value', (7,)) == [{'value': 7}]
        assert precomputed._query_all_dicts('SELECT count(*) AS value FROM pg_prepared_statements') == [{'value': 0}]
        assert connections[0].prepare_threshold == 5
        assert connections[0].info.transaction_status == TransactionStatus.IDLE


def test_failed_query_discarded_and_later_read_works(postgres, monkeypatch):
    connections = []
    def connect():
        c = postgres.connect()
        connections.append(c)
        return c
    monkeypatch.setattr(precomputed, 'get_connection', connect)
    with db.precomputed_read_scope():
        with pytest.raises(PublicDataUnavailable):
            precomputed._query_all_dicts('SELECT 1 / 0')
        assert connections[0].closed
        assert precomputed._query_all_dicts('SELECT 7 AS value') == [{'value': 7}]
        assert len(connections) == 2
    assert all(c.closed for c in connections)


@pytest.mark.parametrize('fail_read', [False, True])
def test_borrowed_operator_transaction_retains_writes_and_ownership(postgres, fail_read):
    from scripts.foushee_m15a2_core_repair import public_reads_in_transaction

    with postgres.connect() as owner:
        owner.execute('CREATE TEMP TABLE borrowed_scope (value integer)')
        owner.commit()
        owner.execute('INSERT INTO borrowed_scope VALUES (7)')
        with public_reads_in_transaction(owner):
            with db.precomputed_read_scope():
                assert precomputed._query_all_dicts('SELECT value FROM borrowed_scope') == [{'value': 7}]
                assert owner.info.transaction_status == TransactionStatus.INTRANS
                db.release_precomputed_read_connection()
                assert not owner.closed
                assert precomputed._query_all_dicts('SELECT value FROM borrowed_scope') == [{'value': 7}]
                if fail_read:
                    # The owner controls recovery even when a borrowed read fails.
                    with pytest.raises(PublicDataUnavailable):
                        precomputed._query_all_dicts('SELECT 1 / 0')
                    assert owner.info.transaction_status == TransactionStatus.INERROR
        assert not owner.closed
        if not fail_read:
            assert owner.execute('SELECT value FROM borrowed_scope').fetchall() == [(7,)]
        owner.rollback()
        assert owner.execute('SELECT count(*) FROM borrowed_scope').fetchone() == (0,)
