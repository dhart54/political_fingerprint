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
