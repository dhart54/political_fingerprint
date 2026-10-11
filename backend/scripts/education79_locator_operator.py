"""Review candidate: bounded immutable persistence; never activates publication.

No approval or positive authority is generated here. Production execution needs
separate sealed decisions, an exact reviewed head and fresh read-only evidence.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from psycopg import sql
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_store_v2r import prepare_write_set
from scripts import education79_locator_preparation as prep
from scripts import editorial_artifact_store as store
from scripts.green_production_target import GREEN_IDENTITY, target_identity
from scripts.green_vote_storage import schema_state, digest as schema_digest

require = prep.require
TARGET_SHA = digest(GREEN_IDENTITY)
CAPS = {'batches': 1, 'artifacts': 3, 'relationships': 2, 'registry_updates': 0, 'other_writes': 0}
AUTHORIZATIONS = {'persist_exact_immutable_graph': True, 'production_database_write': True,
                  'publication_activation': False, 'delete_persisted_graph': False}
ROLLBACK = 'rollback_failed_transaction; retain_committed_inert_graph; registry_unchanged'


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0,
                'UTC decision/evidence timestamp required')
        return parsed
    except (AttributeError, TypeError, ValueError) as exc:
        raise store.StoreSafetyError('UTC decision/evidence timestamp required') from exc


def validate_bundle(bundle, *, fixture=False):
    prep.validate_bundle(bundle)
    require(bundle['expected_counts'] == CAPS, 'exact immutable persistence caps required')
    require(fixture or 'test_only_synthetic' not in bundle['candidate_approval'],
            'synthetic candidate approval cannot authorize production')


def authority_subject(bundle, baseline, *, reviewer, recorded_at):
    """Decision subject only; no accepted/sealed authority is created."""
    return {'decision': 'persist_exact_education79_locator_immutable_graph',
            'reviewer': reviewer, 'decision_recorded_at_utc': recorded_at,
            'bundle_manifest_sha256': bundle['manifest_sha256'],
            'candidate_approval_binding': bundle['semantic_authority_binding'],
            'source_commit_sha': bundle['source_commit_sha'],
            'production_target_identity_sha256': TARGET_SHA,
            'stable_preflight_sha256': baseline['stable_preflight_sha256'],
            'mutation_caps': dict(CAPS), 'rollback_policy': ROLLBACK,
            'authorizations': dict(AUTHORIZATIONS)}


def validate_authority(bundle, baseline, authority, *, fixture=False, now=None):
    validate_bundle(bundle, fixture=fixture)
    require(isinstance(baseline, dict), 'exact read-only persistence preflight required')
    preflight_fields = {'schema_version', 'production_target_identity_sha256', 'bundle_manifest_sha256',
                        'captured_at_utc', 'transaction_read_only', 'state', 'stable_preflight_sha256',
                        'preflight_subject_sha256'}
    require(set(baseline) in (preflight_fields, preflight_fields | {'test_only_synthetic'})
            and isinstance(baseline['state'], dict), 'preflight envelope differs')
    require(fixture or 'test_only_synthetic' not in baseline, 'synthetic preflight cannot authorize production')
    fields = {'schema_version', 'artifact_id', 'immutable', 'accepted', 'sealed', 'subject', 'subject_sha256'}
    require(isinstance(authority, dict) and set(authority) in (fields, fields | {'test_only_synthetic'}),
            'separately sealed persistence authority required')
    require(fixture or 'test_only_synthetic' not in authority, 'synthetic persistence authority cannot authorize production')
    require('test_only_synthetic' not in authority or authority['test_only_synthetic'] is True,
            'synthetic envelope differs')
    subject = authority.get('subject', {})
    require(authority.get('schema_version') == 'education79_locator_persistence_authority_v1'
            and authority.get('accepted') is True and authority.get('sealed') is True
            and authority.get('immutable') is True and authority.get('artifact_id')
            and isinstance(subject.get('reviewer'), str) and subject['reviewer'].strip(),
            'separately sealed persistence authority required')
    require(subject == authority_subject(bundle, baseline, reviewer=subject['reviewer'],
                                          recorded_at=subject.get('decision_recorded_at_utc'))
            and authority['subject_sha256'] == digest(subject), 'persistence authority binding differs')
    current = now or datetime.now(timezone.utc)
    decision = timestamp(subject['decision_recorded_at_utc'])
    require(timestamp(bundle['candidate_approval']['subject']['decision_recorded_at_utc']) <= decision <= current,
            'persistence decision chronology differs')
    body = {k: v for k, v in baseline.items() if k != 'preflight_subject_sha256'}
    require(baseline.get('schema_version') == 'education79_locator_persistence_preflight_v1'
            and baseline.get('transaction_read_only') is True
            and baseline.get('production_target_identity_sha256') == TARGET_SHA
            and baseline.get('bundle_manifest_sha256') == bundle['manifest_sha256']
            and baseline.get('preflight_subject_sha256') == digest(body)
            and baseline.get('stable_preflight_sha256') == digest(baseline['state']),
            'exact read-only persistence preflight required')
    age = (current - timestamp(baseline['captured_at_utc'])).total_seconds()
    require(0 <= age <= 1800, 'fresh persistence preflight required')


def protected_state(conn, *, exclude_batch_id=None):
    """Stream full-table SHA256 comparison, excluding only owned inserts."""
    result = {}
    for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall():
        table = row['tablename']
        condition = sql.SQL('')
        params = ()
        if exclude_batch_id is not None:
            if table == 'editorial_artifact_batches':
                condition = sql.SQL(' WHERE batch_id <> %s'); params = (exclude_batch_id,)
            elif table == 'editorial_artifact_versions':
                condition = sql.SQL(' WHERE batch_id <> %s'); params = (exclude_batch_id,)
            elif table == 'editorial_artifact_relationships':
                condition = sql.SQL(' WHERE parent_artifact_id NOT IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id=%s) AND child_artifact_id NOT IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id=%s)')
                params = (exclude_batch_id, exclude_batch_id)
        statement = sql.SQL('SELECT to_jsonb(t)::text AS row_text FROM {} t{} ORDER BY row_text').format(sql.Identifier(table), condition)
        checksum = hashlib.sha256(); count = 0
        with conn.cursor(name='education79_protected_rows') as cursor:
            cursor.itersize = 128
            cursor.execute(statement, params)
            for item in cursor:
                checksum.update(item['row_text'].encode('utf-8'))
                checksum.update(b'\n')
                count += 1
        result[table] = {'count': count, 'sha256': checksum.hexdigest()}
    return result


def current_state(conn, bundle):
    store.live_schema_contract(conn)
    require(conn.execute("SELECT relkind FROM pg_class WHERE oid='public.vote_contexts'::regclass").fetchone()['relkind'] == 'v',
            'normalized compatibility view required')
    require(conn.execute('SELECT pg_database_size(current_database()) AS n').fetchone()['n'] < 400000000,
            'bounded database capacity exceeded')
    prep.bound_artifact(conn, bundle['expected_old'], bundle['registry_key'])
    row = prep.registry_row(conn, bundle['registry_key'])
    require(row == bundle['prior_registry_row'], 'current registry drift; no retargeting')
    from app.editorial_artifacts.repository import EditorialArtifactRepository
    require(any(r['artifact_id'] == 245 for r in EditorialArtifactRepository(conn).publication_selector()),
            'prior publication provenance no longer eligible')
    return {'normalized_schema_sha256': schema_digest(schema_state(conn)),
            'registry_row': row, 'owned_state': prep.owned_state(conn, bundle),
            'public_tables': protected_state(conn)}


def capture_preflight(conn, bundle, *, fixture_url=None):
    fixture = fixture_url is not None
    if fixture:
        prep.require_fixture_connection(conn, fixture_url)
    validate_bundle(bundle, fixture=fixture)
    require(conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'] == 'on',
            'preflight must run read-only')
    state = current_state(conn, bundle)
    report = {'schema_version': 'education79_locator_persistence_preflight_v1',
              'production_target_identity_sha256': TARGET_SHA, 'bundle_manifest_sha256': bundle['manifest_sha256'],
              'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'transaction_read_only': True,
              'state': state, 'stable_preflight_sha256': digest(state)}
    if fixture:
        report['test_only_synthetic'] = True
    report['preflight_subject_sha256'] = digest(report)
    return report


def persist(conn, bundle, baseline, authority, *, confirm=False, fixture_url=None, fault_after=False):
    require(confirm, 'explicit bounded production persistence confirmation required')
    fixture = fixture_url is not None
    if fixture:
        prep.require_fixture_connection(conn, fixture_url)
    else:
        require('test_only_synthetic' not in baseline, 'synthetic preflight cannot authorize production')
    validate_authority(bundle, baseline, authority, fixture=fixture)
    require(not conn.autocommit, 'owned transaction required')
    conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (bundle['deterministic_batch_key'],))
    prep.registry_row(conn, bundle['registry_key'], lock=True)
    before = current_state(conn, bundle)
    if before['owned_state'] is not None:
        without_owned = copy.deepcopy(before)
        without_owned['public_tables'] = protected_state(conn, exclude_batch_id=before['owned_state']['batch_id'])
        without_owned['owned_state'] = None
        require(before == baseline['state'] or without_owned == baseline['state'], 'fresh persistence baseline drift')
        return {'status': 'ALREADY_PERSISTED', 'writes': {k: 0 for k in CAPS}, **before['owned_state']}
    require(before == baseline['state'], 'fresh persistence baseline drift')
    result = store.insert_bundle(conn, bundle, {}, batch_key=bundle['deterministic_batch_key'],
                                 source_commit=bundle['source_commit_sha'])
    require(result['artifacts_inserted'] == 3 and result['artifacts_idempotent'] == 0
            and result['relationships_inserted'] == 2, 'persistence insert counts differ')
    owned = prep.owned_state(conn, bundle)
    require(owned is not None and protected_state(conn, exclude_batch_id=owned['batch_id']) == before['public_tables'],
            'protected tables or prior rows changed')
    require(prep.registry_row(conn, bundle['registry_key']) == bundle['prior_registry_row'], 'registry changed during persistence')
    if fault_after:
        raise store.StoreSafetyError('injected candidate persistence failure')
    return {'status': 'PERSISTED', 'writes': CAPS, **owned,
            'registry_unchanged': True, 'activation_authorized': False}


def resolve_ids(conn, bundle, runtime_binding, *, fixture_url=None):
    fixture = fixture_url is not None
    if fixture:
        prep.require_fixture_connection(conn, fixture_url)
    validate_bundle(bundle, fixture=fixture)
    require(conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'] == 'on', 'ID capture must run read-only')
    state = current_state(conn, bundle)
    require(state['owned_state'] is not None, 'exact persisted IDs required; no guessed IDs')
    root_id = state['owned_state']['artifact_ids'][bundle['proposed_new']['natural_key']]
    return prepare_write_set(registry_key=bundle['registry_key'], prior_row=bundle['prior_registry_row'],
                             expected_old=bundle['expected_old'], proposed_new={**bundle['proposed_new'], 'artifact_id': root_id},
                             semantic_authority_binding=bundle['semantic_authority_binding'],
                             publication_metadata=bundle['publication_metadata'], production_target_identity_sha256=TARGET_SHA,
                             public_runtime_manifest_binding=runtime_binding)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['build', 'preflight', 'persist', 'resolve'])
    parser.add_argument('--approval', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--bundle-sha256')
    parser.add_argument('--database-url-env')
    parser.add_argument('--expected-code-head', required=True)
    parser.add_argument('--preflight', type=Path)
    parser.add_argument('--authority', type=Path)
    parser.add_argument('--runtime-binding', type=Path)
    parser.add_argument('--confirm-production-persistence', action='store_true')
    parser.add_argument('--report-path', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.operation == 'persist' and not args.confirm_production_persistence:
        parser.error('explicit production persistence confirmation required')
    require(args.expected_code_head == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=prep.ROOT, text=True).strip(), 'exact reviewed code head required')
    require(not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=prep.ROOT, text=True).strip(), 'tracked worktree is dirty')
    require(subprocess.run(['git', 'cat-file', '-e', args.expected_code_head + ':backend/scripts/education79_locator_operator.py'],
                           cwd=prep.ROOT, capture_output=True).returncode == 0,
            'operator must exist in the exact reviewed code head')
    if args.operation == 'build':
        require(args.approval is not None, 'separate approved candidate required')
        result = prep.build_bundle(prep.load(args.approval), source_commit_sha=args.expected_code_head)
        validate_bundle(result)
    else:
        require(args.bundle is not None and args.database_url_env, 'explicit bundle and target variable required')
        bundle = prep.load(args.bundle); validate_bundle(bundle)
        require(bundle['manifest_sha256'] == args.bundle_sha256 and bundle['source_commit_sha'] == args.expected_code_head,
                'exact reviewed bundle and source head required')
        require(os.getenv('NORMALIZED_VOTE_STORAGE') == '1', 'normalized production environment required')
        url = os.environ[args.database_url_env]
        require(target_identity(url, 'production') == TARGET_SHA, 'approved production target differs')
        baseline = prep.load(args.preflight) if args.preflight else None
        authority = prep.load(args.authority) if args.authority else None
        binding = prep.load(args.runtime_binding) if args.runtime_binding else None
        if args.operation == 'persist':
            validate_authority(bundle, baseline, authority)
            require('test_only_synthetic' not in baseline, 'synthetic preflight cannot authorize production')
        if args.operation == 'resolve':
            require(binding is not None, 'separately reviewed runtime binding required')
        with store._connect(url, autocommit=False) as conn:
            if args.operation in ('preflight', 'resolve'):
                conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            else:
                conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            conn.execute("SET LOCAL timezone='UTC'")
            if args.operation == 'preflight': result = capture_preflight(conn, bundle)
            elif args.operation == 'resolve': result = resolve_ids(conn, bundle, binding)
            else: result = persist(conn, bundle, baseline, authority, confirm=True)
    args.report_path.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print('Exact candidate operation completed; no publication activation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
