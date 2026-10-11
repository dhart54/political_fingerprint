"""Reserved decisions fail before connections or SQL; no real positive approval."""
import copy
import hashlib
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.editorial_presentations.compiler import canonical_digest as digest
from scripts import education79_locator_operator as operator
from scripts import education79_locator_preparation as prep
from scripts.editorial_artifact_store import StoreSafetyError
from test_education79_locator_preparation import fixture_bundle


def fixture_preflight(bundle):
    state = {'owned_state': None, 'public_tables': {}, 'registry_row': bundle['prior_registry_row']}
    result = {'schema_version': 'education79_locator_persistence_preflight_v1',
              'production_target_identity_sha256': operator.TARGET_SHA,
              'bundle_manifest_sha256': bundle['manifest_sha256'],
              'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'transaction_read_only': True, 'state': state, 'stable_preflight_sha256': digest(state),
              'test_only_synthetic': True}
    result['observed_started_at_utc'] = result['observed_completed_at_utc'] = result['captured_at_utc']
    result['preflight_subject_sha256'] = digest(result)
    return result


def fixture_authority(bundle, baseline):
    subject = operator.authority_subject(bundle, baseline, reviewer='synthetic fixture only',
                                         recorded_at=datetime.now(timezone.utc).isoformat())
    return {'schema_version': 'education79_locator_persistence_authority_v1', 'artifact_id': 'synthetic:education79:persistence',
            'immutable': True, 'accepted': True, 'sealed': True, 'test_only_synthetic': True,
            'subject': subject, 'subject_sha256': digest(subject)}


@pytest.mark.parametrize('operation', ['build', 'preflight', 'persist', 'resolve'])
def test_production_default_rejects_fixture_approval(operation):
    conn = Mock();bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    authority = fixture_authority(bundle, baseline)
    with pytest.raises(StoreSafetyError, match='synthetic'):
        if operation == 'build': operator.validate_bundle(bundle)
        elif operation == 'preflight': operator.capture_preflight(conn, bundle)
        elif operation == 'resolve': operator.resolve_ids(conn, bundle, {})
        else: operator.persist(conn, bundle, baseline, authority, confirm=True)
    conn.execute.assert_not_called()


def test_persistence_confirmation_is_separate_from_approval():
    conn = Mock()
    with pytest.raises(StoreSafetyError, match='confirmation'):
        operator.persist(conn, {}, {}, {}, confirm=False)
    conn.execute.assert_not_called()


@pytest.mark.parametrize('mutation', ['accepted', 'sealed', 'candidate', 'caps', 'activation', 'baseline', 'future'])
def test_wrong_or_unsealed_persistence_decision_rejected(mutation):
    bundle = fixture_bundle();baseline = fixture_preflight(bundle);authority = fixture_authority(bundle, baseline)
    if mutation in ('accepted', 'sealed'): authority[mutation] = False
    elif mutation == 'candidate': authority['subject']['bundle_manifest_sha256'] = '0' * 64
    elif mutation == 'caps': authority['subject']['mutation_caps'] = {**operator.CAPS, 'artifacts': 4}
    elif mutation == 'activation': authority['subject']['authorizations'] = {**operator.AUTHORIZATIONS, 'publication_activation': True}
    elif mutation == 'baseline': authority['subject']['stable_preflight_sha256'] = '0' * 64
    else: authority['subject']['decision_recorded_at_utc'] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    authority['subject_sha256'] = digest(authority['subject'])
    with pytest.raises(StoreSafetyError): operator.validate_authority(bundle, baseline, authority, fixture=True)


@pytest.mark.parametrize('mutation', ['stale', 'future', 'not_read_only', 'tampered', 'target', 'synthetic_authority'])
def test_fresh_execution_evidence_is_independent_of_stable_authority(mutation):
    bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    if mutation == 'stale': baseline['captured_at_utc'] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    elif mutation == 'future': baseline['captured_at_utc'] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    elif mutation == 'not_read_only': baseline['transaction_read_only'] = False
    elif mutation == 'target': baseline['production_target_identity_sha256'] = '0' * 64
    if mutation in ('stale', 'future'):
        baseline['observed_started_at_utc'] = baseline['observed_completed_at_utc'] = baseline['captured_at_utc']
    baseline['preflight_subject_sha256'] = digest({k:v for k,v in baseline.items() if k != 'preflight_subject_sha256'})
    authority = fixture_authority(bundle, baseline)
    if mutation == 'tampered': baseline['state']['public_tables']['changed'] = 'bad'
    if mutation == 'synthetic_authority':
        # Real-shaped approval here is still only an in-memory negative-test input.
        bundle = copy.deepcopy(bundle);bundle['candidate_approval'].pop('test_only_synthetic')
        bundle = prep.build_bundle(bundle['candidate_approval'], source_commit_sha=bundle['source_commit_sha'])
        baseline = fixture_preflight(bundle);authority = fixture_authority(bundle, baseline)
    with pytest.raises(StoreSafetyError): operator.validate_authority(bundle, baseline, authority, fixture=mutation != 'synthetic_authority')


def test_cli_requires_confirmation_before_loading_files_or_connecting(monkeypatch):
    connect = Mock();monkeypatch.setattr(operator.store, '_connect', connect)
    with pytest.raises(SystemExit):
        operator.main(['persist', '--expected-code-head', 'a' * 40, '--report-path', 'unused.json'])
    connect.assert_not_called()


def test_pending_decision_template_cannot_assign_final_eligible_statuses():
    request = prep.load(prep.PACKET / 'candidate-approval.request.json')
    with pytest.raises(StoreSafetyError, match='approval required'):
        prep.build_bundle(request, source_commit_sha='a' * 40)


def test_pending_persistence_template_is_not_execution_authority():
    bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    request = prep.load(prep.PACKET / 'persistence-authority.request.json')
    with pytest.raises(StoreSafetyError, match='authority required'):
        operator.validate_authority(bundle, baseline, request, fixture=True)


def test_decision_subject_cannot_mutate_the_fixed_caps_or_authorizations():
    bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    subject = operator.authority_subject(bundle, baseline, reviewer='pending', recorded_at=None)
    subject['mutation_caps']['artifacts'] = 4
    subject['authorizations']['publication_activation'] = True
    assert operator.CAPS['artifacts'] == 3
    assert operator.AUTHORIZATIONS['publication_activation'] is False


def production_url(sslmode='verify-full'):
    target = operator.GREEN_IDENTITY
    return f"postgresql://{target['username']}:fake-test-password@{target['host']}:{target['port']}/{target['database']}?sslmode={sslmode}"


def fake_production_connection():
    conn = Mock();target = operator.GREEN_IDENTITY
    conn.info.host = target['host'];conn.info.user = target['username']
    conn.info.dbname = target['database'];conn.info.port = target['port']
    conn.info.get_parameters.return_value = {'sslmode': 'verify-full'}
    conn.pgconn.ssl_in_use = True
    return conn


def context_for(conn):
    context = Mock();context.__enter__ = Mock(return_value=conn)
    context.__exit__ = Mock(return_value=False)
    return context


@pytest.mark.parametrize('key', ['PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'])
def test_inherited_routing_rejected_without_connection_or_sql(monkeypatch, key):
    conn = fake_production_connection();connect = Mock(return_value=context_for(conn))
    monkeypatch.setattr(operator.store, '_connect', connect)
    with pytest.raises(StoreSafetyError, match='inherited'):
        with operator.production_connection(production_url(), {key: 'synthetic-routing-override'}):
            pytest.fail('untrusted route yielded a connection')
    connect.assert_not_called();conn.execute.assert_not_called()


def test_encrypted_only_tls_rejected_without_connection_or_sql(monkeypatch):
    connect = Mock();monkeypatch.setattr(operator.store, '_connect', connect)
    with pytest.raises(StoreSafetyError, match='TLS server identity'):
        with operator.production_connection(production_url('require'), {}):
            pytest.fail('unverified TLS yielded a connection')
    connect.assert_not_called()


@pytest.mark.parametrize('field,value', [('host','remote.invalid'), ('user','wrong-project'), ('dbname','other'), ('port',6543)])
def test_actual_connected_target_mismatch_rejected_before_first_sql(monkeypatch, field, value):
    conn = fake_production_connection();setattr(conn.info, field, value)
    monkeypatch.setattr(operator.store, '_connect', Mock(return_value=context_for(conn)))
    with pytest.raises(StoreSafetyError, match='actual connected'):
        with operator.production_connection(production_url(), {}):
            pytest.fail('wrong connected tuple yielded')
    conn.execute.assert_not_called()  # Fake handle only; never a remote DB test.


@pytest.mark.parametrize('mode,encrypted', [('require',True), ('verify-full',False)])
def test_actual_tls_mode_checked_before_sql(monkeypatch, mode, encrypted):
    conn = fake_production_connection();conn.info.get_parameters.return_value = {'sslmode': mode}
    conn.pgconn.ssl_in_use = encrypted
    monkeypatch.setattr(operator.store, '_connect', Mock(return_value=context_for(conn)))
    with pytest.raises(StoreSafetyError, match='actual connection'):
        with operator.production_connection(production_url(), {}):
            pytest.fail('TLS mismatch yielded')
    conn.execute.assert_not_called()


def test_verified_fake_connection_uses_bounded_connect_option(monkeypatch):
    conn = fake_production_connection();connect = Mock(return_value=context_for(conn))
    monkeypatch.setattr(operator.store, '_connect', connect)
    with operator.production_connection(production_url(), {}) as actual:
        assert actual is conn
    connect.assert_called_once_with(production_url() + '&connect_timeout=10', autocommit=False)
    conn.execute.assert_not_called()


def fake_fixture_connection():
    conn = Mock();conn.autocommit = False
    conn.info.host = conn.info.hostaddr = '127.0.0.1';conn.info.port = 5432
    conn.info.dbname = prep.FIXTURE_DATABASE
    conn.execute.return_value.fetchone.return_value = {'transaction_read_only':'on'}
    return conn


FIXTURE_URL = 'postgresql://fake@127.0.0.1/' + prep.FIXTURE_DATABASE


@pytest.mark.parametrize('duration,valid', [(1,True), (121,False)])
def test_preflight_records_actual_observation_window_and_rejects_slow_capture(monkeypatch, duration, valid):
    conn = fake_fixture_connection();bundle = fixture_bundle()
    started = datetime.now(timezone.utc);clock = [0]
    monkeypatch.setattr(operator, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(operator, 'utc_now', lambda: started + timedelta(seconds=clock[0]))
    def state(*args, **kwargs):
        clock[0] = duration
        return {'owned_state': None, 'public_tables': {}, 'registry_row': bundle['prior_registry_row']}
    monkeypatch.setattr(operator, 'current_state', state)
    if not valid:
        with pytest.raises(StoreSafetyError, match='budget|observation'):
            operator.capture_preflight(conn, bundle, fixture_url=FIXTURE_URL)
        return
    report = operator.capture_preflight(conn, bundle, fixture_url=FIXTURE_URL)
    assert report['captured_at_utc'] == report['observed_started_at_utc'] == started.isoformat()
    assert report['observed_completed_at_utc'] == (started + timedelta(seconds=duration)).isoformat()
    assert "SET LOCAL lock_timeout = '5s'" in [call.args[0] for call in conn.execute.call_args_list]
    assert "SET LOCAL statement_timeout = '60s'" in [call.args[0] for call in conn.execute.call_args_list]


@pytest.mark.parametrize('phase', ['lock','scan'])
def test_freshness_rechecked_after_waits_immediately_before_insert(monkeypatch, phase):
    conn = fake_fixture_connection();bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    began = datetime.now(timezone.utc) - timedelta(seconds=1790)
    for key in ('captured_at_utc','observed_started_at_utc','observed_completed_at_utc'): baseline[key] = began.isoformat()
    baseline['preflight_subject_sha256'] = digest({k:v for k,v in baseline.items() if k != 'preflight_subject_sha256'})
    authority = fixture_authority(bundle, baseline);clock = [datetime.now(timezone.utc)]
    monkeypatch.setattr(operator, 'utc_now', lambda: clock[0])
    def execute(statement, *args):
        if phase == 'lock' and 'pg_advisory_xact_lock' in statement: clock[0] += timedelta(seconds=20)
        return Mock()
    conn.execute.side_effect = execute
    def state(*args, **kwargs):
        if phase == 'scan': clock[0] += timedelta(seconds=20)
        return baseline['state']
    monkeypatch.setattr(operator, 'current_state', state)
    monkeypatch.setattr(prep, 'registry_row', Mock(return_value=bundle['prior_registry_row']))
    insert = Mock();monkeypatch.setattr(operator.store, 'insert_bundle', insert)
    with pytest.raises(StoreSafetyError, match='fresh persistence'):
        operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=FIXTURE_URL)
    insert.assert_not_called()


def test_operation_budget_exhaustion_prevents_insert(monkeypatch):
    conn = fake_fixture_connection();bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    authority = fixture_authority(bundle, baseline);clock = [0]
    monkeypatch.setattr(operator, 'monotonic', lambda: clock[0])
    def state(*args, **kwargs): clock[0] = 121;return baseline['state']
    monkeypatch.setattr(operator, 'current_state', state)
    monkeypatch.setattr(prep, 'registry_row', Mock(return_value=bundle['prior_registry_row']))
    insert = Mock();monkeypatch.setattr(operator.store, 'insert_bundle', insert)
    with pytest.raises(StoreSafetyError, match='budget'):
        operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=FIXTURE_URL)
    insert.assert_not_called()


class ScanConnection:
    """Active lazy stream detects missing close(), without a real connection."""
    def __init__(self, tables, clock=None, error_at=None, error=None):
        self.tables = tables;self.clock = clock;self.statements = [];self.streams = []
        self.active = False;self.error_at = error_at;self.error = error

    def execute(self, statement):
        assert statement == "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        result = Mock()
        result.fetchall.return_value = [{'tablename': t} for t in sorted(self.tables)]
        return result

    def cursor(self, **kwargs):
        assert kwargs == {}  # Single-row streaming uses an ordinary cursor.
        connection = self
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def stream(self, statement, params, *, size):
                assert size == 1  # Never invoke libpq17-only chunked mode.
                text = statement.as_string();connection.statements.append((text, params))
                table = re.search(r'FROM "([^"]+)" t', text).group(1)
                class Stream:
                    index = 0
                    closed = False
                    def __iter__(self): return self
                    def __next__(self):
                        assert not connection.active or self.index > 0
                        connection.active = True
                        if self.index == connection.error_at: raise connection.error
                        if self.index == len(connection.tables[table]): raise StopIteration
                        if connection.clock is not None: connection.clock[0] += 0.01
                        value = connection.tables[table][self.index];self.index += 1
                        return {'row_text': value}
                    def close(self):
                        self.closed = True;connection.active = False
                result = Stream();connection.streams.append(result)
                return result
        return Cursor()


def reference_fingerprint(rows):
    checksum = hashlib.sha256()
    for text in rows:
        checksum.update((text + '\n').encode('utf-8'))
    return {'count': len(rows), 'sha256': checksum.hexdigest()}


@pytest.mark.parametrize('count', [0, 1, 128, 129, 4095, 4096, 4097, 8192, 8193])
def test_complete_stream_matches_independent_fingerprint_at_old_batch_boundaries(count):
    rows = sorted(['{"n": null, "text": "é雪\\n\\\""}', '{"duplicate": true}',
                   '{"wide": "' + 'ø' * 8192 + '"}'][i % 3] for i in range(count))
    conn = ScanConnection({'empty': [], 'rows': rows}); timings = []
    current = operator.protected_state(conn, scan_timings=timings)
    assert current == {'empty': reference_fingerprint([]), 'rows': reference_fingerprint(rows)}
    assert all(set(t) == {'table','stream_size','excludes_owned_batch','rows','utf8_bytes',
                         'query_setup_seconds','first_row_seconds','fetch_seconds','hash_seconds','status','elapsed_seconds'} for t in timings)
    assert sum(t['rows'] for t in timings) == count
    assert all(t['status'] == 'COMPLETE' for t in timings)
    assert all(s.closed for s in conn.streams) and not conn.active
    assert timings[0]['first_row_seconds'] is None


@pytest.mark.parametrize('excluded', [None, 17])
def test_stream_retains_exact_owned_batch_exclusion_predicates(excluded):
    conn = ScanConnection({t: [] for t in ('editorial_artifact_batches','editorial_artifact_versions',
                                          'editorial_artifact_relationships','unrelated')})
    operator.protected_state(conn, exclude_batch_id=excluded)
    statements = conn.statements
    assert [params for q,params in statements] == ([(),(),(),()] if excluded is None
                                                  else [(excluded,),(excluded,excluded),(excluded,),()])
    assert all(s.closed for s in conn.streams) and not conn.active
    assert all('ORDER BY row_text' in q and 'LIMIT' not in q and 'OFFSET' not in q for q, _ in statements)
    assert all('WHERE' not in q or 'batch_id' in q for q, _ in statements)


def test_deadline_between_individual_rows_closes_active_stream(monkeypatch):
    clock = [0.0];conn = ScanConnection({'rows': ['same'] * 4097}, clock)
    monkeypatch.setattr(operator, 'monotonic', lambda: clock[0])
    timings = []
    with pytest.raises(StoreSafetyError, match='budget'):
        operator.protected_state(conn, deadline=0.045, scan_timings=timings)
    assert timings[0]['status'] == 'FAILED' and timings[0]['rows'] == 4
    assert 'same' not in str(timings)
    assert conn.streams[0].closed and not conn.active


@pytest.mark.parametrize('error', [StoreSafetyError('hash rejected'),ConnectionError('network interrupted'),
                                 RuntimeError('SQL failed'),KeyboardInterrupt()])
def test_all_read_failures_or_early_interruptions_close_the_active_stream(error):
    conn = ScanConnection({'rows':['same']*100},error_at=3,error=error);timings=[]
    with pytest.raises(type(error)):
        operator.protected_state(conn,scan_timings=timings)
    assert conn.streams[0].closed and not conn.active
    assert timings[0]['status']=='FAILED' and timings[0]['rows']==3


def test_rejection_during_hashing_closes_stream(monkeypatch):
    class RejectedText(str):
        def encode(self,*args,**kwargs):raise StoreSafetyError('hash rejected')
    conn=ScanConnection({'rows':['first',RejectedText('second'),'third']})
    with pytest.raises(StoreSafetyError,match='hash rejected'):
        operator.protected_state(conn)
    assert conn.streams[0].closed and not conn.active


def test_timing_sidecar_cannot_change_preflight_envelope_or_stable_hash(monkeypatch):
    conn = fake_fixture_connection();bundle = fixture_bundle()
    now = datetime.now(timezone.utc);monkeypatch.setattr(operator, 'utc_now', lambda: now)
    def state(*args, scan_timings=None, **kwargs):
        if scan_timings is not None: scan_timings.append({'seconds': 99, 'rows': 123})
        return {'owned_state': None, 'public_tables': {}, 'registry_row': bundle['prior_registry_row']}
    monkeypatch.setattr(operator, 'current_state', state)
    plain = operator.capture_preflight(conn, bundle, fixture_url=FIXTURE_URL)
    timings = []
    measured = operator.capture_preflight(conn, bundle, fixture_url=FIXTURE_URL, scan_timings=timings)
    assert measured == plain and timings
    assert measured['stable_preflight_sha256'] == digest(measured['state'])


def test_drift_after_last_full_page_changes_complete_fingerprint():
    rows = ['duplicate'] * 8193
    original = operator.protected_state(ScanConnection({'rows': rows}))
    rows[-1] = 'changed final row'
    changed = operator.protected_state(ScanConnection({'rows': rows}))
    assert original['rows']['count'] == changed['rows']['count'] == 8193
    assert original['rows']['sha256'] != changed['rows']['sha256']


@pytest.mark.parametrize('expiry', ['budget','freshness'])
def test_post_insert_scan_cannot_reset_operation_budget_or_evidence_age(monkeypatch, expiry):
    conn = fake_fixture_connection();bundle = fixture_bundle();baseline = fixture_preflight(bundle)
    authority = fixture_authority(bundle, baseline);clock = [0]
    utc_clock = [datetime.now(timezone.utc)]
    monkeypatch.setattr(operator, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(operator, 'utc_now', lambda: utc_clock[0])
    monkeypatch.setattr(operator, 'current_state', Mock(return_value=baseline['state']))
    monkeypatch.setattr(prep, 'registry_row', Mock(return_value=bundle['prior_registry_row']))
    monkeypatch.setattr(prep, 'owned_state', Mock(return_value={'batch_id':17,'artifact_ids':{}}))
    insert = Mock(return_value={'artifacts_inserted':3,'artifacts_idempotent':0,'relationships_inserted':2})
    monkeypatch.setattr(operator.store, 'insert_bundle', insert)
    def after(*args, **kwargs):
        assert kwargs['deadline'] == operator.LIMITS['observation_budget_seconds']
        if expiry == 'budget': clock[0] = 121
        else: utc_clock[0] += timedelta(seconds=1801)
        return baseline['state']['public_tables']
    monkeypatch.setattr(operator, 'protected_state', after)
    with pytest.raises(StoreSafetyError, match='budget|fresh persistence'):
        operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=FIXTURE_URL, scan_timings=[])
    insert.assert_called_once()  # Fake write only; caller must abort instead of commit.
