import copy
import gzip
import json
import os

import pytest

from scripts import m15b_persistence_preparation as prep
from scripts.editorial_artifact_store import _connect, StoreSafetyError
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_store_v2r import (
    prepare_write_set,capture_preflight,replace_publication,registry_row,
)
from app.editorial_presentations.publication_replacement_governance_v2 import PublicationReplacementGovernanceError
from test_reusable_publication_replacement_v2r import runtime,seal


def test_actual_package_is_exact_additive_and_unresolved():
    package=prep.load(prep.OUT/'persistence_package.json');prep.validate_package(package)
    approved=prep.load(prep.APPROVED)
    for issue,bundle in package['replacements'].items():
        assert bundle['artifacts'][0]['payload']==approved['replacements'][issue]['payload']
        assert bundle['proposed_new']['artifact_id'] is None
        assert bundle['expected_counts']==dict(batches=1,artifacts=3,relationships=2,registry_updates=0,other_writes=0)
        assert bundle['artifacts'][0]['supersedes_artifact_id']==bundle['expected_old']['artifact_id']
        assert bundle['manifest_sha256']==digest({k:v for k,v in bundle.items() if k!='manifest_sha256'})
    assert package['production_persistence_authorized'] is False
    assert package['production_activation_authorized'] is False


def snapshot(conn, registry=True):
    from psycopg import sql
    tables=conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
    return {r['tablename']:conn.execute(sql.SQL(
        "SELECT md5(COALESCE(string_agg(to_jsonb(t)::text, chr(10) ORDER BY to_jsonb(t)::text), '')) AS hash FROM {} t"
    ).format(sql.Identifier(r['tablename']))).fetchone()['hash'] for r in tables if registry or r['tablename']!='editorial_publication_registry'}


def public(conn):
    from scripts.foushee_m15a2_core_repair import public_reads_in_transaction
    from app.api import editorial_presentations,positions
    result={}
    with public_reads_in_transaction(conn):
        for scope in ('119','all'):
            result[scope]={'presentations':editorial_presentations.get_editorial_presentations('leg_valerie_p_foushee',scope,None),
                'discovery':positions.get_legislator_positions('leg_valerie_p_foushee',scope,None),
                'details':{d:positions.get_legislator_position_evidence('leg_valerie_p_foushee',d,scope,None) for d in (
                    'NATIONAL_SECURITY_FOREIGN','JUSTICE_PUBLIC_SAFETY','ENVIRONMENT_ENERGY','EDUCATION_WORKFORCE')}}
    return json.loads(json.dumps(result,default=str))


@pytest.mark.skipif(not os.getenv('M15A2_DISPOSABLE_DATABASE_URL'),reason='existing disposable PostgreSQL lane required')
def test_actual_persistence_publication_and_owned_recovery(monkeypatch):
    # Reuse the existing snapshot replay harness and exact loopback DB guard.
    # No production configuration is loaded or inherited by this proof.
    from scripts.disposable_database_url import require_exact_loopback_postgres_url
    dsn=require_exact_loopback_postgres_url(os.environ['M15A2_DISPOSABLE_DATABASE_URL'])
    from test_m15a2_core_repair_postgres import prepare_database,repair
    with monkeypatch.context() as setup:
        setup.setattr(repair,'DIRECTORY',prep.OUT)
        prepare_database()
    monkeypatch.setenv('DATABASE_URL',dsn)
    monkeypatch.setenv('ENABLE_FIXTURE_FALLBACK','0')
    from app.main import app
    from app.api import editorial_presentations,positions
    from app.editorial_presentations.site_publication import active_site_integration_candidate
    from app.editorial_presentations.selector import select_public_presentations
    from app.editorial_artifacts.repository import EditorialArtifactRepository
    # Test-only opt-in at the established selector seams, never strip authority flags.
    monkeypatch.setattr(editorial_presentations,'select_public_presentations',lambda *a,**kw:select_public_presentations(*a,**kw,allow_test_activation_authority=True))
    monkeypatch.setattr(positions,'active_site_integration_candidate',lambda *a,**kw:active_site_integration_candidate(*a,**kw,allow_test_authority=True))
    package=prep.load(prep.OUT/'persistence_package.json')
    with _connect(dsn,autocommit=False) as conn:
        initial=snapshot(conn);before=public(conn)
        assert before==json.loads(gzip.decompress((prep.OUT/'public_before.json.gz').read_bytes()))
        original_rows={i:registry_row(conn,b['registry_key']) for i,b in package['replacements'].items()}
        unrelated=select_public_presentations(EditorialArtifactRepository(conn).publication_selector(),member_bioguide_id='UNRELATED',legislator_id='unrelated',scope='119')
        operations=[]
        for issue,bundle in package['replacements'].items():
            pre=snapshot(conn)
            with pytest.raises(StoreSafetyError,match='injected'):
                with conn.transaction(): prep.persist(conn,package,issue,fault_after=True)
            assert snapshot(conn)==pre
            result=prep.persist(conn,package,issue)
            assert result['writes']==bundle['expected_counts']
            persisted=snapshot(conn)
            assert {k for k in pre if pre[k]!=persisted[k]}=={'editorial_artifact_batches','editorial_artifact_versions','editorial_artifact_relationships'}
            assert prep.persist(conn,package,issue)['writes']=={k:0 for k in bundle['expected_counts']}
            assert snapshot(conn)==persisted and public(conn)==before
            rt=runtime()
            ws=prepare_write_set(registry_key=bundle['registry_key'],prior_row=original_rows[issue],expected_old=bundle['expected_old'],
                proposed_new={**bundle['proposed_new'],'artifact_id':result['artifact_ids'][bundle['proposed_new']['natural_key']]},
                semantic_authority_binding=bundle['semantic_authority_binding'],publication_metadata=bundle['publication_metadata'],
                production_target_identity_sha256='f'*64,
                public_runtime_manifest_binding={f'{side}_submanifest_sha256':rt[f'{side}_deployment']['submanifest_sha256'] for side in ('backend','frontend')})
            operations.append((issue,ws,seal(ws),rt))
        conn.commit()
        protected=snapshot(conn,registry=False)
        for issue,ws,authority,rt in operations:
            with _connect(dsn,autocommit=False) as read:
                read.execute('SET TRANSACTION READ ONLY')
                preflight=capture_preflight(read,ws,production_target_identity_sha256='f'*64)
            kw=dict(runtime_evidence=rt,production_preflight=preflight,production_target_identity_sha256='f'*64,allow_test_authority=True)
            pre=snapshot(conn)
            wrong=copy.deepcopy(authority);wrong['subject']['proposed_new']['artifact_id']+=1
            with pytest.raises(PublicationReplacementGovernanceError): replace_publication(conn,ws,wrong,**kw)
            assert snapshot(conn)==pre
            with pytest.raises(RuntimeError,match='injected'):
                with conn.transaction(): replace_publication(conn,ws,authority,**kw,fault_after_update=True)
            assert snapshot(conn)==pre
            for drift in ('pointer','provenance'):
                with conn.transaction(force_rollback=True):
                    if drift=='pointer':
                        conn.execute('UPDATE editorial_publication_registry SET artifact_id=%s WHERE member_bioguide_id=%s AND issue_id=%s',
                            (ws['subject']['proposed_new']['artifact_id'],'F000477',issue))
                    else:
                        conn.execute("UPDATE editorial_artifact_relationships SET metadata_jsonb='{}'::jsonb WHERE parent_artifact_id=%s",(ws['subject']['proposed_new']['artifact_id'],))
                    with pytest.raises(PublicationReplacementGovernanceError): replace_publication(conn,ws,authority,**kw)
            assert snapshot(conn)==pre
            rows=conn.execute('SELECT to_jsonb(r) AS row FROM editorial_publication_registry r ORDER BY issue_id').fetchall()
            assert replace_publication(conn,ws,authority,**kw)['status']=='APPLIED'
            afterrows=conn.execute('SELECT to_jsonb(r) AS row FROM editorial_publication_registry r ORDER BY issue_id').fetchall()
            assert sum(a!=b for a,b in zip(rows,afterrows))==1
            assert snapshot(conn,registry=False)==protected
            assert sum(replace_publication(conn,ws,authority,**kw)['mutation_counts'].values())==0
            with conn.transaction(force_rollback=True):
                conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"competing\":true}'::jsonb WHERE issue_id=%s",(issue,))
                with pytest.raises(PublicationReplacementGovernanceError): replace_publication(conn,ws,authority,**kw,rollback=True)
            conn.commit()
        after=public(conn)
        for scope in before:
            selected={p['issue_id']:p for p in after[scope]['presentations']['presentations']}
            for issue,bundle in package['replacements'].items():
                assert selected[issue]==bundle['artifacts'][0]['payload']['subject']['presentations'][scope]
            for issue,detail in before[scope]['details'].items():
                observed=after[scope]['details'][issue]
                assert observed['review_accounting']==detail['review_accounting']
                raw=lambda p:[(r['canonical_action_id'],r['position']) for r in p['evidence']]
                assert raw(observed)==raw(detail)
                unreviewed=lambda p:[r for r in p['evidence'] if r['interpretation_review_state']=='not_yet_in_reviewed_interpretation']
                assert unreviewed(observed)==unreviewed(detail)
                summary=next(r for r in after[scope]['discovery']['positions'] if r['domain']==issue)
                assert summary['total_votes']==len(observed['evidence'])
                if issue not in package['replacements']: assert observed==detail
            justice=after[scope]['details']['JUSTICE_PUBLIC_SAFETY']['evidence']
            copytext='This action alone does not establish motive, ideology, or a broader position on this issue.'
            assert sum(copytext in (r.get('governed_receipt_projection') or {}).get('public_caveats',[]) for r in justice)==35
            assert sum(bool(r.get('governed_receipt_control')) for r in justice)==2
        assert select_public_presentations(EditorialArtifactRepository(conn).publication_selector(),member_bioguide_id='UNRELATED',legislator_id='unrelated',scope='119')==unrelated
        for issue,ws,authority,rt in reversed(operations):
            assert replace_publication(conn,ws,authority,runtime_evidence=None,production_preflight=None,
                production_target_identity_sha256='f'*64,allow_test_authority=True,rollback=True)['status']=='ROLLED_BACK'
            assert registry_row(conn,ws['subject']['registry_key'])==original_rows[issue]
        assert snapshot(conn,registry=False)==protected and public(conn)==before
        for issue in package['replacements']: prep.recover(conn,package,issue)
        assert snapshot(conn)==initial
        print('ACTUAL_M15B_LIFECYCLE_PASS: exact persistence, sequential replacement, both scopes, current ledger, controls, drift, idempotency, owned rollback and recovery')
