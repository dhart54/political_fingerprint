"""New operator candidate in its own fresh dedicated fixture, never production."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import education79_locator_operator as operator
from scripts import education79_locator_preparation as prep
from scripts.editorial_artifact_store import _connect, StoreSafetyError
from test_education79_locator_preparation import synthetic_candidate_approval
from test_education79_locator_operator import fixture_authority
from test_education79_locator_disposable_postgres import seed_fixture, public
from test_reusable_publication_replacement_v2r import runtime

DSN = os.getenv('EDUCATION79_OPERATOR_DATABASE_URL')
pytestmark = pytest.mark.skipif(not DSN, reason='separate dedicated PostgreSQL17 operator fixture required')


def test_candidate_bounded_persistence_capture_drift_idempotency_and_failed_transaction(monkeypatch):
    monkeypatch.setenv('NORMALIZED_VOTE_STORAGE', '1')
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK', '0')
    seed_fixture(DSN)  # Same exact guarded DB name, separate CI job/service.
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=prep.ROOT, text=True).strip()
    bundle = prep.build_bundle(synthetic_candidate_approval(), source_commit_sha=head)
    with _connect(DSN, autocommit=False) as conn:
        before = public(conn)
        initial = operator.protected_state(conn)
        conn.rollback()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        baseline = operator.capture_preflight(conn, bundle, fixture_url=DSN)
        assert conn.execute('SHOW lock_timeout').fetchone()['lock_timeout'] == '5s'
        assert conn.execute('SHOW statement_timeout').fetchone()['statement_timeout'] in ('1min', '60s')
        assert baseline['captured_at_utc'] == baseline['observed_started_at_utc']
        binding = {f'{s}_submanifest_sha256': runtime()[f'{s}_deployment']['submanifest_sha256'] for s in ('backend', 'frontend')}
        with pytest.raises(StoreSafetyError, match='IDs'):
            operator.resolve_ids(conn, bundle, binding, fixture_url=DSN)
        conn.rollback()
        authority = fixture_authority(bundle, baseline)
        with pytest.raises(StoreSafetyError, match='synthetic'):
            operator.persist(conn, bundle, baseline, authority, confirm=True)
        assert operator.protected_state(conn) == initial
        with pytest.raises(StoreSafetyError, match='injected'):
            with conn.transaction():
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN, fault_after=True)
        assert operator.protected_state(conn) == initial
        with conn.transaction(force_rollback=True):
            conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"operator_drift\":true}'::jsonb WHERE issue_id='EDUCATION_WORKFORCE'")
            with pytest.raises(StoreSafetyError, match='registry drift'):
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        result = operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        assert result['writes'] == operator.CAPS and result['registry_unchanged'] is True
        assert operator.protected_state(conn, exclude_batch_id=result['batch_id']) == initial
        assert public(conn) == before
        repeat = operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        assert repeat['status'] == 'ALREADY_PERSISTED' and not any(repeat['writes'].values())
        with conn.transaction(force_rollback=True):
            conn.execute('UPDATE editorial_artifact_batches SET manifest_sha256=%s WHERE batch_id=%s', ('0' * 64, result['batch_id']))
            with pytest.raises(StoreSafetyError, match='ownership differs'):
                operator.persist(conn, bundle, baseline, authority, confirm=True, fixture_url=DSN)
        conn.commit()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        ws = operator.resolve_ids(conn, bundle, binding, fixture_url=DSN)
        assert ws['subject']['proposed_new']['artifact_id'] == result['artifact_ids'][bundle['proposed_new']['natural_key']]
        assert ws['subject']['expected_old']['artifact_id'] == 245
        assert ws['subject']['stable_production_baseline']['prior_registry_row'] == bundle['prior_registry_row']
        assert public(conn) == before
        proof = {'code_head': head, 'disposable_only': True, 'production_execution_authorized': False,
                 'candidate_approval': bundle['candidate_approval'], 'persistence_authority': authority,
                 'preflight': baseline, 'persistence': result, 'id_capture_write_set': ws,
                 'idempotent_repeat': repeat, 'before': before, 'after_persistence': public(conn),
                 'registry_unchanged': True, 'failed_transaction_rollback': True,
                 'synthetic_default_rejected': True, 'execution_limits': operator.LIMITS,
                 'observation_window_preserved': True, 'transaction_wait_limits_verified': True}
        if folder := os.getenv('EDUCATION79_OPERATOR_PROOF_DIR'):
            path = Path(folder);path.mkdir(parents=True, exist_ok=True)
            (path / 'operator-proof.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n', encoding='utf-8')
