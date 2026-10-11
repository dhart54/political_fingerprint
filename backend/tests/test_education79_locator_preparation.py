"""Exact inert preparation; synthetic decisions never confer production authority."""
import copy
from unittest.mock import Mock

import pytest

from app.editorial_presentations.compiler import canonical_digest as digest
from scripts import education79_locator_preparation as prep
from scripts.editorial_artifact_store import StoreSafetyError


def synthetic_candidate_approval():
    subject = prep.approval_subject(prep.candidate_outputs(), reviewer='synthetic disposable only',
                                    recorded_at='2026-10-11T00:00:00+00:00')
    return {'schema_version': 'education79_locator_candidate_approval_v1',
            'artifact_id': 'synthetic-education79-candidate-approval', 'immutable': True,
            'accepted': True, 'sealed': True, 'test_only_synthetic': True,
            'subject': subject, 'subject_sha256': digest(subject)}


def fixture_bundle():
    return prep.build_bundle(synthetic_candidate_approval(), source_commit_sha='a' * 40)


def test_final_eligible_graph_requires_prior_exact_approval_and_has_no_guessed_ids():
    bundle = fixture_bundle()
    prep.validate_bundle(bundle)
    assert bundle['proposed_new']['artifact_id'] is None
    assert bundle['candidate_approval']['subject']['production_execution_authorized'] is False
    assert len(bundle['artifacts']) == 3 and len(bundle['relationships']) == 2
    assert all(all(a[k] == v for k, v in prep.FINAL_STATUSES.items()) for a in bundle['artifacts'])
    assert bundle['artifacts'][0]['supersedes_artifact_id'] == 245
    assert bundle['manifest_sha256'] == digest({k: v for k, v in bundle.items() if k != 'manifest_sha256'})
    assert bundle['prior_registry_row']['activated_at'] == '2026-09-08 20:29:08.400792+00:00'


@pytest.mark.parametrize('field,value', [('accepted', False), ('sealed', False), ('immutable', False)])
def test_pending_approval_cannot_produce_eligible_persistence(field, value):
    approval = synthetic_candidate_approval()
    approval[field] = value
    with pytest.raises(StoreSafetyError, match='approval required'):
        prep.build_bundle(approval, source_commit_sha='a' * 40)


@pytest.mark.parametrize('mutation', ['candidate_hash', 'source_url', 'statuses', 'provenance'])
def test_resealed_wrong_candidate_is_rejected(mutation):
    approval = synthetic_candidate_approval()
    subject = approval['subject']
    if mutation == 'candidate_hash': subject['candidate']['content_sha256'] = '0' * 64
    if mutation == 'source_url': subject['source_locator']['url'] = 'https://example.invalid/source'
    if mutation == 'statuses': subject['final_eligible_statuses']['production_eligible'] = False
    if mutation == 'provenance': subject['provenance'][1]['content_sha256'] = '0' * 64
    approval['subject_sha256'] = digest(subject)
    with pytest.raises(StoreSafetyError, match='binding differs'):
        prep.build_bundle(approval, source_commit_sha='a' * 40)


@pytest.mark.parametrize('url', ['postgresql://test@remote.invalid/pf_education79_locator',
                                'postgresql://test@127.0.0.1/postgres',
                                'postgresql://test@127.0.0.1/pf_education79_locator?hostaddr=remote.invalid'])
def test_disposable_write_rejects_other_targets_before_any_sql(url):
    conn = Mock()
    with pytest.raises((ValueError, StoreSafetyError)):
        prep.persist_disposable(conn, {}, database_url=url)
    conn.execute.assert_not_called()


def test_conflicting_bundle_fails_before_persistence():
    bundle = fixture_bundle()
    altered = copy.deepcopy(bundle)
    altered['artifacts'][0]['editorial_status'] = 'human_approval_pending'
    with pytest.raises(StoreSafetyError, match='bundle differs'):
        prep.validate_bundle(altered)


@pytest.mark.parametrize('hostaddr', ['203.0.113.4', '2001:db8::1', '', None, 'localhost'])
@pytest.mark.parametrize('operation', ['persist', 'bind'])
def test_actual_remote_or_unknown_address_is_rejected_before_any_sql(hostaddr, operation):
    conn = Mock()
    conn.info.dbname = prep.FIXTURE_DATABASE
    conn.info.host = '127.0.0.1'
    conn.info.port = 5432
    conn.info.hostaddr = hostaddr
    conn.autocommit = False
    url = 'postgresql://fixture@127.0.0.1/' + prep.FIXTURE_DATABASE
    with pytest.raises(StoreSafetyError, match='address'):
        if operation == 'persist':
            prep.persist_disposable(conn, {}, database_url=url)
        else:
            prep.bind_write_set(conn, {}, database_url=url,
                                target_identity_sha256='0' * 64, runtime_manifest_binding={})
    conn.execute.assert_not_called()


@pytest.mark.parametrize('hostaddr', ['127.0.0.1', '::1'])
def test_connected_loopback_endpoint_is_accepted_without_sql(hostaddr):
    conn = Mock()
    conn.info.dbname = prep.FIXTURE_DATABASE
    conn.info.host = 'localhost'
    conn.info.port = 5432
    conn.info.hostaddr = hostaddr
    prep.require_fixture_endpoint(conn, 'postgresql://fixture@localhost/' + prep.FIXTURE_DATABASE)
    conn.execute.assert_not_called()


@pytest.mark.parametrize('hostaddr', ['203.0.113.4', '2001:db8::1', '', None, 'localhost'])
def test_seeder_rejects_remote_or_unknown_hostaddr_before_first_sql(monkeypatch, hostaddr):
    import test_education79_locator_disposable_postgres as proof
    conn = Mock()
    conn.info.dbname = prep.FIXTURE_DATABASE
    conn.info.host = '127.0.0.1'
    conn.info.port = 5432
    conn.info.hostaddr = hostaddr
    connection = Mock()
    connection.__enter__ = Mock(return_value=conn)
    connection.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(proof, '_connect', Mock(return_value=connection))
    with pytest.raises(StoreSafetyError, match='address'):
        proof.seed_fixture('postgresql://fixture@127.0.0.1/' + prep.FIXTURE_DATABASE)
    conn.execute.assert_not_called()
