"""Reserved decisions fail before connections or SQL; no real positive approval."""
import copy
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
