"""Exact persisted production IDs, replayed only on isolated PostgreSQL17."""
import copy
import gzip
import json
import os
from datetime import datetime, timezone

import pytest

from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_store_v2r import (
    capture_preflight, replace_publication, registry_row,
)
from app.editorial_presentations.publication_replacement_governance_v2 import PublicationReplacementGovernanceError
from scripts.editorial_artifact_store import _connect
from scripts.foushee_m15a2_core_repair import insert_row
from scripts.disposable_database_url import require_exact_loopback_postgres_url
from scripts import m15b_persistence_preparation as prep
from scripts.prepare_m15b_green_activation import OUT, load, build_write_sets
from test_m15b_actual_persistence import prepare_normalized_database, public, same_public, snapshot
from test_reusable_publication_replacement_v2r import seal


def test_activation_inputs_are_exact_and_not_authority():
    receipts = load('persistence_receipts.json')
    assert receipts['persistence_execution_head'] == 'b1820d2b598eb2b5767e84040f6a8d6c0ef22d36'
    assert receipts['activation_authorized'] is False
    runtime = load('execution_evidence/runtime_evidence.json')
    writes = load('execution_evidence/write_sets.json')
    owned = {i: {k: r[k] for k in ('artifact_ids', 'batch_id')} for i, r in receipts['receipts'].items()}
    assert writes == build_write_sets(runtime, owned)
    assert {i: w['subject']['proposed_new']['artifact_id'] for i, w in writes.items()} == {
        'NATIONAL_SECURITY_FOREIGN': 248, 'JUSTICE_PUBLIC_SAFETY': 251}


@pytest.mark.skipif(not os.getenv('M15B_GREEN_DISPOSABLE_DATABASE_URL'), reason='dedicated normalized PostgreSQL17 required')
def test_actual_production_id_activation_and_owned_rollback(monkeypatch):
    dsn = require_exact_loopback_postgres_url(os.environ['M15B_GREEN_DISPOSABLE_DATABASE_URL'])
    prepare_normalized_database(dsn)
    monkeypatch.setenv('DATABASE_URL', dsn)
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK', '0')
    monkeypatch.setenv('NORMALIZED_VOTE_STORAGE', '1')
    from app.api import editorial_presentations, positions
    from app.editorial_presentations.selector import select_public_presentations
    from app.editorial_presentations.site_publication import active_site_integration_candidate
    monkeypatch.setattr(editorial_presentations, 'select_public_presentations',
        lambda *a, **kw: select_public_presentations(*a, **kw, allow_test_activation_authority=True))
    monkeypatch.setattr(positions, 'active_site_integration_candidate',
        lambda *a, **kw: active_site_integration_candidate(*a, **kw, allow_test_authority=True))
    rows = json.loads(gzip.decompress((OUT/'persisted_rows.json.gz').read_bytes()))
    writes = load('execution_evidence/write_sets.json')
    package = prep.load(prep.OUT/'persistence_package.json')
    # Test-only freshness clock: immutable observed manifests stay hash-identical.
    # No production evidence file or human authority is created or modified here.
    runtime = copy.deepcopy(load('execution_evidence/runtime_evidence.json'))
    runtime.pop('runtime_health_proof_subject_sha256')
    runtime['captured_at_utc'] = datetime.now(timezone.utc).isoformat()
    runtime['runtime_health_proof_subject_sha256'] = digest(runtime)
    with _connect(dsn, autocommit=False) as conn:
        conn.execute("SET timezone='UTC'"); conn.execute('SET extra_float_digits=0')
        before = public(conn)
        for table in ('editorial_artifact_batches', 'editorial_artifact_versions', 'editorial_artifact_relationships'):
            for row in rows[table]: insert_row(conn, table, row)
        for issue in writes:
            assert prep.preflight(conn, package['replacements'][issue])['artifact_ids'] == load('persistence_receipts.json')['receipts'][issue]['artifact_ids']
        conn.commit()
        persisted = snapshot(conn)
        assert public(conn) == before
        authorities = {}
        for issue in ('NATIONAL_SECURITY_FOREIGN', 'JUSTICE_PUBLIC_SAFETY'):
            ws = writes[issue]; identity = ws['subject']['production_target_identity_sha256']
            with _connect(dsn, autocommit=False) as read:
                read.execute('SET TRANSACTION READ ONLY'); read.execute("SET LOCAL timezone='UTC'")
                preflight = capture_preflight(read, ws, production_target_identity_sha256=identity)
            kw = dict(runtime_evidence=runtime, production_preflight=preflight,
                      production_target_identity_sha256=identity, allow_test_authority=True)
            pre = snapshot(conn)
            with pytest.raises(PublicationReplacementGovernanceError):
                replace_publication(conn, ws, {}, **kw)
            assert snapshot(conn) == pre
            authority = seal(ws)  # Existing explicitly synthetic, disposable-only test helper.
            authorities[issue] = authority
            with conn.transaction(force_rollback=True):
                conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"competing\":true}'::jsonb WHERE issue_id=%s", (issue,))
                with pytest.raises(PublicationReplacementGovernanceError): replace_publication(conn, ws, authority, **kw)
            with pytest.raises(RuntimeError, match='injected'):
                with conn.transaction(): replace_publication(conn, ws, authority, **kw, fault_after_update=True)
            assert snapshot(conn) == pre
            assert replace_publication(conn, ws, authority, **kw)['status'] == 'APPLIED'
            assert sum(replace_publication(conn, ws, authority, **kw)['mutation_counts'].values()) == 0
            assert {k for k, v in snapshot(conn).items() if v != pre[k]} == {'editorial_publication_registry'}
            conn.commit()
        after = public(conn)
        for scope, state in before.items():
            old = {p['issue_id']: p for p in state['presentations']['presentations']}
            selected = {p['issue_id']: p for p in after[scope]['presentations']['presentations']}
            for issue, item in old.items():
                same_public(selected[issue], package['replacements'][issue]['artifacts'][0]['payload']['subject']['presentations'][scope] if issue in writes else item)
            ns = selected['NATIONAL_SECURITY_FOREIGN']
            findings = ns['repeated_patterns'] + ns['notable_choices'] + ns['policy_trajectories']
            assert not ns['policy_trajectories'] and len(findings) == 14
            assert len({a for f in findings for a in f['action_ids']}) == 30
            assert selected['JUSTICE_PUBLIC_SAFETY']['policy_trajectories'] == old['JUSTICE_PUBLIC_SAFETY']['policy_trajectories']
            for issue, detail in state['details'].items():
                actual = after[scope]['details'][issue]
                assert actual['review_accounting'] == detail['review_accounting']
                if issue not in writes: assert actual == detail
                assert [(r['canonical_action_id'], r['position']) for r in actual['evidence']] == [(r['canonical_action_id'], r['position']) for r in detail['evidence']]
                unreviewed = lambda x: [r for r in x['evidence'] if r['interpretation_review_state'] == 'not_yet_in_reviewed_interpretation']
                assert unreviewed(actual) == unreviewed(detail)
                for a, b in zip(actual['evidence'], detail['evidence']):
                    assert a.get('governed_receipt_control') == b.get('governed_receipt_control')
                    left, right = copy.deepcopy(a.get('governed_receipt_projection')), copy.deepcopy(b.get('governed_receipt_projection'))
                    if issue == 'JUSTICE_PUBLIC_SAFETY' and left:
                        for field in ('limitation_treatments', 'public_caveats'): left.pop(field, None); right.pop(field, None)
                    same_public(left, right)
                discovery = next(p for p in after[scope]['discovery']['positions'] if p['domain'] == issue)
                assert discovery['total_votes'] == len(actual['evidence'])
            justice = after[scope]['details']['JUSTICE_PUBLIC_SAFETY']['evidence']
            wording = 'This action alone does not establish motive, ideology, or a broader position on this issue.'
            assert sum(wording in (r.get('governed_receipt_projection') or {}).get('public_caveats', []) for r in justice) == 35
            assert sum(bool(r.get('governed_receipt_control')) for r in justice) == 2
        expected = OUT/'expected_public_after.json.gz'
        if os.getenv('M15B_RECORD_EXPECTED_AFTER') == '1':
            assert not expected.exists()
            expected.write_bytes(gzip.compress(json.dumps(after, sort_keys=True).encode(), mtime=0))
        else:
            same_public(after, json.loads(gzip.decompress(expected.read_bytes())))
        for issue in ('JUSTICE_PUBLIC_SAFETY', 'NATIONAL_SECURITY_FOREIGN'):
            ws = writes[issue]
            assert replace_publication(conn, ws, authorities[issue], runtime_evidence=None, production_preflight=None,
                production_target_identity_sha256=ws['subject']['production_target_identity_sha256'], allow_test_authority=True,
                rollback=True)['status'] == 'ROLLED_BACK'
            assert registry_row(conn, ws['subject']['registry_key']) == ws['subject']['stable_production_baseline']['prior_registry_row']
        assert snapshot(conn) == persisted and public(conn) == before
        print('EXACT_PRODUCTION_IDS_ACTIVATION_PASS: 227->248 and 221->251; unchanged core; exact after-state; owned rollback')
