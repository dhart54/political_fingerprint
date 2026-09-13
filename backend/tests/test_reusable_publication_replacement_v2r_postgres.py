"""Same PostgreSQL lifecycle and seed as M14H; synthetic replacements only."""
import copy
import os

import pytest
from psycopg.types.json import Jsonb

from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations import publication_replacement_runtime_v2r as runtime_adapter
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_presentations.publication_replacement_store_v2r import (
    registry_row, capture_preflight, replace_publication,
)
from app.editorial_presentations.publication_replacement_governance_v2 import (
    PROJECTION_SCHEMA_V2R, artifact_identity, PublicationReplacementGovernanceError,
)
from scripts.editorial_artifact_store import _connect
from scripts.foushee_education_workforce_m14h_replacement import (
    apply_replacement as apply_m14h, rollback_replacement as rollback_m14h,
)
from test_m14h_education_publication_replacement_postgres import _prepare_old_education, _package
from test_reusable_publication_replacement_v2r import sample

DATABASE_URL=os.getenv('M14H_DISPOSABLE_DATABASE_URL')
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason='existing M14H disposable PostgreSQL is required')


def public(conn, scope='119'):
    rows=EditorialArtifactRepository(conn).publication_selector()
    return select_public_presentations(rows,member_bioguide_id='F000477',legislator_id='leg_valerie_p_foushee',
                                      scope=scope,allow_test_activation_authority=True)


def all_registry(conn):
    return conn.execute('SELECT to_jsonb(r) AS row FROM editorial_publication_registry r ORDER BY member_bioguide_id,issue_id').fetchall()


def protected_state(conn):
    # All existing public tables except the only authorized mutation target.
    from psycopg import sql
    tables=conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename!='editorial_publication_registry' ORDER BY tablename").fetchall()
    return {r['tablename']:conn.execute(sql.SQL(
        'SELECT md5(COALESCE(string_agg(to_jsonb(t)::text, chr(10) ORDER BY to_jsonb(t)::text), %s)) AS digest FROM {} t'
    ).format(sql.Identifier(r['tablename'])), ('',)).fetchone()['digest'] for r in tables}


def stage_synthetic(conn, issue, presentation):
    # Fixture persistence uses the existing batch/artifact/relationship tables.
    # Activation itself cannot insert into them.
    from scripts.prepare_m15b_replacement_artifacts import current_receipt_rows
    key={'member_bioguide_id':'F000477','issue_id':issue}
    prior=registry_row(conn,key)
    old=dict(conn.execute('SELECT * FROM editorial_artifact_versions WHERE artifact_id=%s',(prior['artifact_id'],)).fetchone())
    name='synthetic-replacement:'+issue
    payload={'schema_version':PROJECTION_SCHEMA_V2R,'artifact_id':name,'subject':{
        **key,'member_slug':'leg_valerie_p_foushee','congress':119,
        'presentations':{scope:copy.deepcopy(presentation[scope]) for scope in ('119','all')},
        'receipt_projections':current_receipt_rows(issue)}}
    for p in payload['subject']['presentations'].values():
        p['teaser']='Synthetic replacement display.'
    content=digest(payload)
    source={'schema_version':'editorial_publication_source_manifest_v1','source_artifacts':[artifact_identity(old)],
            'presentation_content_sha256':content}
    validation={'schema_version':'editorial_publication_validation_v1','status':'PASS','blockers':[],
                'presentation_content_sha256':content}
    batch=conn.execute("""INSERT INTO editorial_artifact_batches
        (deterministic_batch_key,source_commit_sha,manifest_sha256,status,artifact_count,relationship_count,applied_at)
        VALUES (%s,%s,%s,'applied',3,2,NOW()) RETURNING batch_id""",(name,'a'*40,digest([payload,source,validation]))).fetchone()['batch_id']
    ids={}
    for kind,suffix,body in [('issue_public_presentation','',payload),('source_manifest',':source',source),('standardization_validation_result',':validation',validation)]:
        ids[suffix]=conn.execute("""INSERT INTO editorial_artifact_versions
            (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_manifest_sha256,
             source_commit_sha,batch_id,supersedes_artifact_id,member_bioguide_id,issue_id,congress,chamber,
             editorial_status,benchmark_status,production_eligible,review_route)
            VALUES (%s,%s,%s,1,%s,%s,%s,%s,%s,%s,'F000477',%s,119,'house','human_approved','gold_benchmark',TRUE,'human_exception') RETURNING artifact_id""",
            (kind,name+suffix,body['schema_version'],Jsonb(body),digest(body),digest(source),'a'*40,batch,
             old['artifact_id'] if not suffix else None,issue)).fetchone()['artifact_id']
    relmeta={'activation_bundle_id':name}
    for suffix,role in [(':source','uses_source_manifest'),(':validation','has_validation')]:
        conn.execute('INSERT INTO editorial_artifact_relationships (parent_artifact_id,child_artifact_id,relationship_type,ordinal,metadata_jsonb) VALUES (%s,%s,%s,0,%s)',
                     (ids[''],ids[suffix],role,Jsonb(relmeta)))
    metadata={'presentation_natural_key':name,'presentation_artifact_version':1,'active_artifact_sha256':content,
        'source_manifest_natural_key':name+':source','source_manifest_artifact_version':1,'source_manifest_content_sha256':digest(source),
        'validation_natural_key':name+':validation','validation_artifact_version':1,'validation_content_sha256':digest(validation),
        'relationship_metadata':relmeta}
    _,ws,authority,rt=sample(issue,payload=payload,prior=prior,old=artifact_identity(old),new_id=ids[''],metadata=metadata)
    return ws,authority,rt,batch


def test_four_domain_sequential_exact_replacements_and_owned_lifecycle(monkeypatch):
    runtime_adapter.install_publication_replacement_runtime_v2r()
    with _connect(DATABASE_URL,autocommit=False) as conn:
        _prepare_old_education(conn)
        _,_,m14ws,m14authority=_package(conn)
        apply_m14h(conn,m14ws,m14authority,allow_test_authority=True)
        before={scope:public(conn,scope) for scope in ('119','all')}
        generic=runtime_adapter.eligible_persisted_replacement
        monkeypatch.setattr(runtime_adapter,'eligible_persisted_replacement',lambda *a,**kw:None)
        assert before=={scope:public(conn,scope) for scope in ('119','all')}
        monkeypatch.setattr(runtime_adapter,'eligible_persisted_replacement',generic)
        operations=[]
        for issue in ('NATIONAL_SECURITY_FOREIGN','JUSTICE_PUBLIC_SAFETY'):
            p={scope:next(p for p in before[scope]['presentations'] if p['issue_id']==issue) for scope in before}
            operations.append(stage_synthetic(conn,issue,p))
        conn.commit()
        staged_registry=all_registry(conn)
        staged_protected=protected_state(conn)
        conn.commit()
        for ws,authority,rt,_ in operations:
            with _connect(DATABASE_URL,autocommit=False) as read:
                read.execute('SET TRANSACTION READ ONLY')
                preflight=capture_preflight(read,ws,production_target_identity_sha256='f'*64)
            kwargs=dict(runtime_evidence=rt,production_preflight=preflight,
                        production_target_identity_sha256='f'*64,allow_test_authority=True)
            before_rows=all_registry(conn)
            # One authority cannot be reused for the other explicitly keyed request.
            other=next(item for item in operations if item[0]['subject']['registry_key']!=ws['subject']['registry_key'])
            with pytest.raises(PublicationReplacementGovernanceError):
                replace_publication(conn,other[0],authority,**kwargs)
            # Pointer drift and revoked eligibility fail before any registry write.
            with conn.transaction(force_rollback=True):
                conn.execute('UPDATE editorial_publication_registry SET artifact_id=%s WHERE member_bioguide_id=%s AND issue_id=%s',
                    (ws['subject']['proposed_new']['artifact_id'],'F000477',ws['subject']['registry_key']['issue_id']))
                with pytest.raises(PublicationReplacementGovernanceError):
                    replace_publication(conn,ws,authority,**kwargs)
            with conn.transaction(force_rollback=True):
                conn.execute('UPDATE editorial_artifact_versions SET production_eligible=FALSE WHERE artifact_id=%s',
                    (ws['subject']['proposed_new']['artifact_id'],))
                with pytest.raises(PublicationReplacementGovernanceError,match='eligible'):
                    replace_publication(conn,ws,authority,**kwargs)
            with pytest.raises(RuntimeError,match='injected'):
                with conn.transaction():
                    replace_publication(conn,ws,authority,**kwargs,fault_after_update=True)
            assert all_registry(conn)==before_rows
            with conn.transaction():
                result=replace_publication(conn,ws,authority,**kwargs)
            assert result['status']=='APPLIED' and sum(result['mutation_counts'].values())==1
            after_rows=all_registry(conn)
            assert sum(a!=b for a,b in zip(before_rows,after_rows))==1
            assert protected_state(conn)==staged_protected
            assert replace_publication(conn,ws,authority,**kwargs)['status']=='ALREADY_APPLIED'
            assert sum(replace_publication(conn,ws,authority,**kwargs)['mutation_counts'].values())==0
            issue=ws['subject']['registry_key']['issue_id']
            assert next(p for p in public(conn)['presentations'] if p['issue_id']==issue)['teaser']=='Synthetic replacement display.'
            # Any competing mutation destroys ownership; rollback must not guess.
            with conn.transaction(force_rollback=True):
                conn.execute("UPDATE editorial_publication_registry SET publication_metadata_jsonb=publication_metadata_jsonb || '{\"conflict\":true}'::jsonb WHERE member_bioguide_id=%s AND issue_id=%s",('F000477',issue))
                with pytest.raises(PublicationReplacementGovernanceError,match='owned'):
                    replace_publication(conn,ws,authority,**kwargs,rollback=True)
                with pytest.raises(PublicationReplacementGovernanceError):
                    replace_publication(conn,ws,authority,**kwargs)
            with conn.transaction(force_rollback=True):
                conn.execute('UPDATE editorial_publication_registry SET artifact_id=%s WHERE member_bioguide_id=%s AND issue_id=%s',
                    (ws['subject']['expected_old']['artifact_id'],'F000477',issue))
                with pytest.raises(PublicationReplacementGovernanceError,match='owned'):
                    replace_publication(conn,ws,authority,**kwargs,rollback=True)
            conn.commit()
        for ws,authority,rt,_ in reversed(operations):
            result=replace_publication(conn,ws,authority,runtime_evidence=None,production_preflight=None,
                production_target_identity_sha256='f'*64,allow_test_authority=True,rollback=True)
            assert result['status']=='ROLLED_BACK' and result['mutation_counts']['update_registry_rows']==1
        assert all_registry(conn)==staged_registry
        assert protected_state(conn)==staged_protected
        assert before=={scope:public(conn,scope) for scope in before}
        for _,_,_,batch in operations:
            conn.execute('DELETE FROM editorial_artifact_batches WHERE batch_id=%s',(batch,))
        rollback_m14h(conn,m14ws,m14authority,allow_test_authority=True)
