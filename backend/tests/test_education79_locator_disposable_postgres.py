"""Actual locator graph/runtime proof in one dedicated normalized PostgreSQL17 fixture."""
import copy
import gzip
import json
import os
import subprocess
from pathlib import Path

import pytest
from psycopg import sql

from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_governance_v2 import PublicationReplacementGovernanceError
from app.editorial_presentations.publication_replacement_store_v2r import (
    capture_preflight, registry_row, replace_publication,
)
from scripts import education79_locator_preparation as prep
from scripts.editorial_artifact_store import _connect, StoreSafetyError
from scripts.foushee_m15a2_core_repair import insert_row, public_reads_in_transaction
from test_education79_locator_preparation import synthetic_candidate_approval
from test_m15b_actual_persistence import snapshot
from test_reusable_publication_replacement_v2r import runtime, seal

DSN = os.getenv('EDUCATION79_DISPOSABLE_DATABASE_URL')
pytestmark = pytest.mark.skipif(not DSN, reason='dedicated Education79 PostgreSQL17 fixture required')


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def seed_fixture(database_url):
    from scripts.disposable_database_url import require_exact_loopback_postgres_url
    from urllib.parse import urlsplit
    require_exact_loopback_postgres_url(database_url)
    assert urlsplit(database_url).path == '/' + prep.FIXTURE_DATABASE
    fixture = read_gzip(prep.ROOT / 'docs/editorial/publication_replacements/m15b_green_authorization/disposable_baseline.json.gz')
    current = read_gzip(prep.ROOT / 'docs/editorial/publication_replacements/m15b_green_activation/production_audits.json.gz')['after-justice']
    tables = {**fixture['tables'], **current['editorial_rows']}
    # Preparation audits contain the persisted graph before registry replacement.
    # Replay the separately recorded executed registry, not that historical row.
    executed = read_gzip(prep.ROOT / 'docs/editorial/publication_replacements/m15b_green_activation_execution/production_audits.json.gz')['after-justice']
    tables['editorial_publication_registry'] = executed['registry']
    assert {row['issue_id']: row['artifact_id'] for row in executed['registry']} == {
        'EDUCATION_WORKFORCE': 245, 'ENVIRONMENT_ENERGY': 239,
        'NATIONAL_SECURITY_FOREIGN': 248, 'JUSTICE_PUBLIC_SAFETY': 251}
    # The normalized vote fixture contains Foushee only. Keep that same member
    # boundary for the historical artifact graph instead of inventing profiles.
    tables['editorial_artifact_versions'] = [row for row in tables['editorial_artifact_versions']
                                            if row['member_bioguide_id'] in (None, 'F000477')]
    artifact_ids = {row['artifact_id'] for row in tables['editorial_artifact_versions']}
    tables['editorial_artifact_relationships'] = [row for row in tables['editorial_artifact_relationships']
                                                 if row['parent_artifact_id'] in artifact_ids
                                                 and row['child_artifact_id'] in artifact_ids]
    assert all(row['artifact_id'] in artifact_ids for row in tables['editorial_publication_registry'])
    with _connect(database_url, autocommit=True) as conn:
        assert conn.info.dbname == prep.FIXTURE_DATABASE
        assert conn.execute('SHOW server_version_num').fetchone()['server_version_num'].startswith('17')
        # Refuse an occupied database; never drop/reset a caller's schema.
        assert conn.execute("SELECT COUNT(*) AS n FROM pg_tables WHERE schemaname='public'").fetchone()['n'] == 0
        conn.execute("DO $$ BEGIN IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon; END IF; IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated; END IF; END $$")
        backend = prep.ROOT / 'backend'
        for path in sorted((backend / 'migrations').glob('*.sql')):
            if path.name != '0015_zip_mapping_source_evidence.sql':
                conn.execute(path.read_text(encoding='utf-8-sig'))
        conn.execute((backend / 'migrations/staged/normalize_vote_storage.sql').read_text(encoding='utf-8-sig'))
        order = ('legislators', 'bills', 'roll_calls', 'votes_cast', 'vote_context_members',
                 'vote_classifications', 'vote_interpretations', 'senate_amendment_references', 'fingerprints',
                 'editorial_artifact_batches', 'editorial_artifact_versions',
                 'editorial_artifact_relationships', 'editorial_publication_registry')
        with conn.transaction():
            conn.execute("SET LOCAL timezone='UTC'")
            for table in order:
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(sql.Identifier(table)))
                for row in tables[table]:
                    insert_row(conn, table, row)
                conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(sql.Identifier(table)))
            for name, state in current['sequences'].items():
                conn.execute('SELECT setval(%s,%s,%s)', ('public.' + name, state['last_value'], state['is_called']))


def public(conn):
    from app.api import positions, editorial_presentations
    result = {}
    with public_reads_in_transaction(conn):
        for scope in ('119', 'all', '118'):
            member = 'leg_valerie_p_foushee'
            result[f'{member}:{scope}:positions'] = positions.get_legislator_positions(member, scope, None)
            result[f'{member}:{scope}:editorial'] = editorial_presentations.get_editorial_presentations(member, scope, None)
            for domain in ('EDUCATION_WORKFORCE', 'NATIONAL_SECURITY_FOREIGN', 'ENVIRONMENT_ENERGY', 'JUSTICE_PUBLIC_SAFETY'):
                result[f'{member}:{scope}:{domain}'] = positions.get_legislator_position_evidence(member, domain, scope, None)
    return json.loads(json.dumps(result, default=str))


def exact_delta(before, after, path=''):
    if type(before) is not type(after): return [path]
    if isinstance(before, dict):
        assert before.keys() == after.keys(), path
        return [p for k in before for p in exact_delta(before[k], after[k], path + '/' + k)]
    if isinstance(before, list):
        assert len(before) == len(after), path
        return [p for i, (a, b) in enumerate(zip(before, after)) for p in exact_delta(a, b, path + '/' + str(i))]
    return [] if before == after else [path]


def test_exact_candidate_persistence_runtime_idempotency_drift_and_rollback(monkeypatch):
    seed_fixture(DSN)
    monkeypatch.setenv('DATABASE_URL', DSN)
    monkeypatch.setenv('NORMALIZED_VOTE_STORAGE', '1')
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK', '0')
    from app.api import editorial_presentations, positions
    from app.editorial_presentations.selector import select_public_presentations
    from app.editorial_presentations.site_publication import active_site_integration_candidate
    from app.editorial_artifacts.repository import EditorialArtifactRepository
    monkeypatch.setattr(editorial_presentations, 'select_public_presentations',
                        lambda *a, **kw: select_public_presentations(*a, **kw, allow_test_activation_authority=True))
    monkeypatch.setattr(positions, 'active_site_integration_candidate',
                        lambda *a, **kw: active_site_integration_candidate(*a, **kw, allow_test_authority=True))
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=prep.ROOT, text=True).strip()
    bundle = prep.build_bundle(synthetic_candidate_approval(), source_commit_sha=head)
    with _connect(DSN, autocommit=False) as conn:
        conn.execute("SET timezone='UTC'")
        conn.execute('SET extra_float_digits=0')
        initial = snapshot(conn)
        before = public(conn)
        prior = registry_row(conn, bundle['registry_key'])
        assert prior == bundle['prior_registry_row']
        with pytest.raises(StoreSafetyError, match='persisted IDs cannot be guessed'):
            prep.bind_write_set(conn, bundle, database_url=DSN, target_identity_sha256='f' * 64,
                                runtime_manifest_binding={})
        with pytest.raises(StoreSafetyError, match='injected'):
            with conn.transaction():
                prep.persist_disposable(conn, bundle, database_url=DSN, fault_after=True)
        assert snapshot(conn) == initial
        with conn.transaction(force_rollback=True):
            conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"drift\":true}'::jsonb WHERE issue_id='EDUCATION_WORKFORCE'")
            with pytest.raises(StoreSafetyError, match='registry drift'):
                prep.persist_disposable(conn, bundle, database_url=DSN)
        assert snapshot(conn) == initial
        persisted = prep.persist_disposable(conn, bundle, database_url=DSN)
        assert persisted['writes'] == bundle['expected_counts']
        assert len(set(persisted['artifact_ids'].values())) == 3
        assert all(type(v) is int and v > 253 for v in persisted['artifact_ids'].values())
        after_persist = snapshot(conn)
        assert {k for k in initial if initial[k] != after_persist[k]} == {
            'editorial_artifact_batches', 'editorial_artifact_versions', 'editorial_artifact_relationships'}
        assert public(conn) == before
        assert not any(prep.persist_disposable(conn, bundle, database_url=DSN)['writes'].values())
        assert snapshot(conn) == after_persist
        with conn.transaction(force_rollback=True):
            conn.execute('UPDATE editorial_artifact_batches SET manifest_sha256=%s WHERE batch_id=%s', ('0' * 64, persisted['batch_id']))
            with pytest.raises(StoreSafetyError, match='ownership differs'):
                prep.persist_disposable(conn, bundle, database_url=DSN)
        rt = runtime()  # Clearly synthetic execution evidence, not a deployment proof.
        ws = prep.bind_write_set(conn, bundle, database_url=DSN, target_identity_sha256='f' * 64,
                                 runtime_manifest_binding={f'{s}_submanifest_sha256': rt[f'{s}_deployment']['submanifest_sha256'] for s in ('backend', 'frontend')})
        authority = seal(ws)
        conn.commit()
        with _connect(DSN, autocommit=False) as read:
            read.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            read.execute("SET LOCAL timezone='UTC'")
            preflight = capture_preflight(read, ws, production_target_identity_sha256='f' * 64)
        kw = dict(runtime_evidence=rt, production_preflight=preflight,
                  production_target_identity_sha256='f' * 64, allow_test_authority=True)
        with pytest.raises(PublicationReplacementGovernanceError, match='synthetic authority'):
            replace_publication(conn, ws, authority, **{**kw, 'allow_test_authority': False})
        protected = snapshot(conn, registry=False)
        with pytest.raises(RuntimeError, match='injected'):
            with conn.transaction():
                replace_publication(conn, ws, authority, **kw, fault_after_update=True)
        assert registry_row(conn, bundle['registry_key']) == prior
        result = replace_publication(conn, ws, authority, **kw)
        assert result['status'] == 'APPLIED' and sum(result['mutation_counts'].values()) == 1
        assert snapshot(conn, registry=False) == protected
        after = public(conn)
        changes = exact_delta(before, after)
        assert len(changes) == 6
        assert all(('EDUCATION_WORKFORCE' in p or ':editorial/' in p)
                   and (':119:' in p or ':all:' in p) and p.endswith('/url') for p in changes)
        assert replace_publication(conn, ws, authority, **kw)['status'] == 'ALREADY_APPLIED'
        default = select_public_presentations(EditorialArtifactRepository(conn).publication_selector(),
                                              member_bioguide_id='F000477', legislator_id='leg_valerie_p_foushee', scope='119')
        assert next(p for p in default['presentations'] if p['issue_id'] == 'EDUCATION_WORKFORCE')['tier'] == 'receipts_only'
        with conn.transaction(force_rollback=True):
            conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"conflict\":true}'::jsonb WHERE issue_id='EDUCATION_WORKFORCE'")
            with pytest.raises(PublicationReplacementGovernanceError, match='owned'):
                replace_publication(conn, ws, authority, **kw, rollback=True)
        restored = replace_publication(conn, ws, authority, **kw, rollback=True)
        assert restored['status'] == 'ROLLED_BACK'
        assert registry_row(conn, bundle['registry_key']) == prior
        assert snapshot(conn) == after_persist and public(conn) == before
        report = {'disposable_only': True, 'production_execution_authorized': False, 'code_head': head,
                  'candidate_approval': bundle['candidate_approval'], 'persistence': persisted,
                  'write_set': ws, 'activation_authority': authority, 'synthetic_runtime': rt,
                  'fixture_preflight': preflight, 'public_url_delta_paths': changes,
                  'before': before, 'after': after, 'rollback_full_registry_restored': True,
                  'immutable_graph_retained': True, 'default_selector_rejects_synthetic_authority': True}
        output = os.getenv('EDUCATION79_PROOF_DIR')
        if output:
            folder = Path(output); folder.mkdir(parents=True, exist_ok=True)
            (folder / 'disposable-proof.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n', encoding='utf-8')
