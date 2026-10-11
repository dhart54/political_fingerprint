"""Exact Education locator preparation; writes are restricted to a named fixture DB.

No production connection, persistence, activation, or approval entry point exists.
Final eligible statuses require a separately supplied sealed candidate approval.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import re
import runpy
from pathlib import Path
from urllib.parse import urlsplit

from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_store_v2r import (
    bound_artifact, prepare_write_set, registry_row,
)
from scripts import editorial_artifact_store as store
from scripts.disposable_database_url import require_exact_loopback_postgres_url
from scripts.m15b_persistence_preparation import owned_state

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / 'docs/review_packets/education79_locator_v1'
FIXTURE_DATABASE = 'pf_education79_locator'
FINAL_STATUSES = {'editorial_status': 'human_approved',
                  'benchmark_status': 'gold_benchmark', 'production_eligible': True}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise store.StoreSafetyError(message)


def candidate_outputs():
    outputs = runpy.run_path(str(ROOT / 'scripts/prepare_education79_locator_release.py'))['build']()
    require(all(value == load(PACKET / 'prepared' / name) for name, value in outputs.items()),
            'exact reviewed packet differs')
    return outputs


def approval_subject(outputs, *, reviewer, recorded_at):
    """Proposed decision subject only; does not assert approval or seal authority."""
    proposal = outputs['persistence-preparation.json']
    return {'decision': 'approve_exact_locator_candidate_for_immutable_persistence',
            'reviewer': reviewer, 'decision_recorded_at_utc': recorded_at,
            'registry_key': proposal['registry_key'], 'expected_old': proposal['expected_old'],
            'candidate': proposal['candidate'], 'provenance': proposal['artifacts'],
            'source_locator': outputs['candidate-source-manifest.json']['source_locator_binding'],
            'final_eligible_statuses': dict(FINAL_STATUSES), 'production_execution_authorized': False}


def build_bundle(approval, *, source_commit_sha):
    require(isinstance(approval, dict), 'separately sealed exact candidate approval required')
    outputs = candidate_outputs()
    subject = approval.get('subject', {})
    fields = {'schema_version', 'artifact_id', 'immutable', 'accepted', 'sealed', 'subject', 'subject_sha256'}
    require(set(approval) in (fields, fields | {'test_only_synthetic'})
            and ('test_only_synthetic' not in approval or approval['test_only_synthetic'] is True),
            'candidate approval envelope differs')
    require(re.fullmatch(r'[0-9a-f]{40}', source_commit_sha or '') is not None,
            'exact source commit required')
    require(approval.get('schema_version') == 'education79_locator_candidate_approval_v1'
            and approval.get('accepted') is True and approval.get('sealed') is True
            and approval.get('immutable') is True and approval.get('artifact_id')
            and subject.get('reviewer') and subject.get('decision_recorded_at_utc'),
            'separately sealed exact candidate approval required before eligible persistence')
    require(subject == approval_subject(outputs, reviewer=subject['reviewer'],
                                         recorded_at=subject['decision_recorded_at_utc'])
            and approval.get('subject_sha256') == digest(subject), 'candidate approval binding differs')
    try:
        recorded = datetime.fromisoformat(subject['decision_recorded_at_utc'].replace('Z', '+00:00'))
        require(recorded.tzinfo is not None and recorded.utcoffset() == timezone.utc.utcoffset(recorded),
                'UTC candidate decision timestamp required')
    except (TypeError, ValueError) as exc:
        raise store.StoreSafetyError('UTC candidate decision timestamp required') from exc
    proposal = outputs['persistence-preparation.json']
    source_sha = proposal['candidate']['source_manifest_sha256']
    artifacts = []
    for item in proposal['artifacts']:
        payload = outputs[item['payload_file']]
        artifacts.append({k: item[k] for k in ('artifact_type', 'natural_key', 'artifact_version', 'content_sha256')}
                         | {'schema_version': payload['schema_version'], 'payload': copy.deepcopy(payload),
                            'source_manifest_sha256': source_sha, 'source_commit_sha': source_commit_sha,
                            'supersedes_artifact_id': 245 if item['artifact_type'] == 'issue_public_presentation' else None,
                            **proposal['registry_key'], 'congress': 119, 'chamber': 'house',
                            'canonical_action_id': None, 'episode_id': None, 'policy_family_id': None,
                            **FINAL_STATUSES, 'review_route': 'human_exception'})
    relationships = [{'parent_natural_key': proposal['candidate']['natural_key'],
                      'child_natural_key': item['child_natural_key'],
                      'relationship_type': item['relationship_type'], 'ordinal': item['ordinal'],
                      'metadata': item['metadata_jsonb']} for item in proposal['relationships']]
    metadata = {'presentation_natural_key': artifacts[0]['natural_key'],
                'presentation_artifact_version': 1, 'active_artifact_sha256': artifacts[0]['content_sha256'],
                'relationship_metadata': relationships[0]['metadata']}
    for prefix, item in zip(('source_manifest', 'validation'), artifacts[1:]):
        metadata.update({prefix + '_' + k: item[k] for k in ('natural_key', 'artifact_version', 'content_sha256')})
    prior = load(PACKET / 'baseline/persisted-education.json')['registry']
    # Match the existing V2R registry_row serializer, preserving the same instant.
    for field in ('activated_at', 'deactivated_at'):
        if prior[field] is not None:
            prior[field] = str(datetime.fromisoformat(prior[field]))
    body = {'registry_key': proposal['registry_key'], 'expected_old': proposal['expected_old'],
            'proposed_new': {k: artifacts[0][k] for k in ('natural_key', 'artifact_version', 'content_sha256')} | {'artifact_id': None},
            'prior_registry_row': prior,
            'semantic_authority_binding': {'artifact_id': approval['artifact_id'], 'subject_sha256': approval['subject_sha256']},
            'candidate_approval': copy.deepcopy(approval), 'source_commit_sha': source_commit_sha,
            'deterministic_batch_key': 'education79-locator:' + artifacts[0]['content_sha256'][:16],
            'artifacts': artifacts, 'relationships': relationships, 'publication_metadata': metadata,
            'expected_counts': {'batches': 1, 'artifacts': 3, 'relationships': 2, 'registry_updates': 0, 'other_writes': 0}}
    body['manifest_sha256'] = digest(body)
    return body


def validate_bundle(bundle):
    require(bundle == build_bundle(bundle['candidate_approval'], source_commit_sha=bundle['source_commit_sha']),
            'exact approved bundle differs')


def require_fixture_connection(conn, database_url):
    parsed = urlsplit(require_exact_loopback_postgres_url(database_url))
    require(parsed.path == '/' + FIXTURE_DATABASE and conn.info.dbname == FIXTURE_DATABASE
            and conn.info.host == parsed.hostname and conn.info.port == (parsed.port or 5432),
            'dedicated loopback Education fixture connection required')
    require(not conn.autocommit, 'owned fixture transaction required')


def persist_disposable(conn, bundle, *, database_url, fault_after=False):
    require_fixture_connection(conn, database_url)
    validate_bundle(bundle)
    require(bundle['candidate_approval'].get('test_only_synthetic') is True,
            'fixture writes require visibly synthetic candidate approval')
    store.live_schema_contract(conn)
    conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (bundle['deterministic_batch_key'],))
    prior = registry_row(conn, bundle['registry_key'], lock=True)
    require(prior == bundle['prior_registry_row'], 'current registry drift; no retargeting')
    bound_artifact(conn, bundle['expected_old'], bundle['registry_key'])
    from app.editorial_artifacts.repository import EditorialArtifactRepository
    require(any(row['artifact_id'] == 245 for row in EditorialArtifactRepository(conn).publication_selector()),
            'current publication provenance is no longer eligible')
    existing = owned_state(conn, bundle)
    if existing:
        return {'status': 'ALREADY_PERSISTED', 'writes': {k: 0 for k in bundle['expected_counts']}, **existing}
    result = store.insert_bundle(conn, bundle, {}, batch_key=bundle['deterministic_batch_key'],
                                 source_commit=bundle['source_commit_sha'])
    require(result['artifacts_inserted'] == 3 and result['artifacts_idempotent'] == 0
            and result['relationships_inserted'] == 2, 'persistence caps differ')
    state = owned_state(conn, bundle)
    require(state is not None, 'complete owned eligible graph required')
    if fault_after:
        raise store.StoreSafetyError('injected fixture persistence failure')
    return {'status': 'PERSISTED', 'writes': bundle['expected_counts'], **state}


def bind_write_set(conn, bundle, *, database_url, target_identity_sha256, runtime_manifest_binding):
    """Resolve IDs only from complete exact ownership, then use the existing V2R builder."""
    require_fixture_connection(conn, database_url)
    validate_bundle(bundle)
    require(registry_row(conn, bundle['registry_key']) == bundle['prior_registry_row'],
            'current registry drift; no retargeting')
    state = owned_state(conn, bundle)
    require(state is not None, 'persisted IDs cannot be guessed')
    return prepare_write_set(registry_key=bundle['registry_key'], prior_row=bundle['prior_registry_row'],
                             expected_old=bundle['expected_old'],
                             proposed_new={**bundle['proposed_new'], 'artifact_id': state['artifact_ids'][bundle['proposed_new']['natural_key']]},
                             semantic_authority_binding=bundle['semantic_authority_binding'],
                             publication_metadata=bundle['publication_metadata'],
                             production_target_identity_sha256=target_identity_sha256,
                             public_runtime_manifest_binding=runtime_manifest_binding)
