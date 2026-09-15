"""Exact M15B package and thin use of the existing immutable artifact store."""
import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND=Path(__file__).resolve().parents[1]
ROOT=BACKEND.parent
sys.path.insert(0,str(BACKEND))
from app.editorial_presentations.compiler import canonical_digest as digest
from app.editorial_presentations.publication_replacement_store_v2r import registry_row, bound_artifact, validate_eligible_graph
from scripts import editorial_artifact_store as store
from scripts.foushee_education_workforce_m14h_replacement import target_identity
from scripts.disposable_database_url import require_exact_loopback_postgres_url

MERGED='5843bab9b1bed3e5db57976bae3b05466f2cbafe'
OUT=ROOT/'docs/editorial/publication_replacements/m15b_authorization'
APPROVED=ROOT/'docs/editorial/publication_replacements/m15b_preparation/approved_semantics_preparation.json'


def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def require(condition,message):
    if not condition: raise store.StoreSafetyError(message)


def build():
    approved=load(APPROVED);baseline=load(OUT/'production_baseline.json')
    products={}
    for issue,item in approved['replacements'].items():
        old=item['expected_old'];new=item['proposed_new'];key=new['natural_key']
        require(baseline['verified'][issue]['expected_old']==old,'captured old identity differs')
        require(baseline['existing_proposed_artifacts'][issue]==[],'proposed production artifacts already exist')
        graph=item['additive_graph'];source=graph['source_manifest'];validation=graph['validation']
        artifacts=[]
        for kind,identity,payload in [('issue_public_presentation',new,item['payload']),
                ('source_manifest',source,source['payload']),('standardization_validation_result',validation,validation['payload'])]:
            require(digest(payload)==identity['content_sha256'],'approved payload digest differs')
            artifacts.append({'artifact_type':kind,'natural_key':identity['natural_key'],'artifact_version':identity['artifact_version'],
                'schema_version':payload['schema_version'],'payload':payload,'content_sha256':identity['content_sha256'],
                'source_manifest_sha256':source['content_sha256'],'source_commit_sha':MERGED,
                'supersedes_artifact_id':old['artifact_id'] if kind=='issue_public_presentation' else None,
                **item['registry_key'],'congress':119,'chamber':'house','canonical_action_id':None,'episode_id':None,
                'policy_family_id':None,'editorial_status':'human_approved','benchmark_status':'gold_benchmark',
                'production_eligible':True,'review_route':'human_exception'})
        relationships=[{'parent_natural_key':key,'child_natural_key':r['child_natural_key'],
            'relationship_type':r['relationship_type'],'ordinal':r['ordinal'],'metadata':r['metadata_jsonb']} for r in graph['relationships']]
        metadata={'presentation_natural_key':key,'presentation_artifact_version':new['artifact_version'],'active_artifact_sha256':new['content_sha256'],
            **{prefix+'_'+field:value[field] for prefix,value in [('source_manifest',source),('validation',validation)]
               for field in ('natural_key','artifact_version','content_sha256')},'relationship_metadata':relationships[0]['metadata']}
        body={'registry_key':item['registry_key'],'expected_old':old,'proposed_new':{**new,'artifact_id':None},
            'prior_registry_row':baseline['verified'][issue]['registry_row'],
            'semantic_authority_binding':item['semantic_authority_binding'],
            'production_target_identity_sha256':baseline['production_target_identity_sha256'],
            'deterministic_batch_key':'m15b:'+issue.lower()+':'+new['content_sha256'][:16],
            'source_commit_sha':MERGED,'artifacts':artifacts,'relationships':relationships,'publication_metadata':metadata,
            'expected_counts':{'batches':1,'artifacts':len(artifacts),'relationships':len(relationships),'registry_updates':0,'other_writes':0}}
        body['manifest_sha256']=digest(body);products[issue]=body
    package={'merged_main':MERGED,'approved_preparation_sha256':digest(approved),'production_baseline_sha256':digest(baseline),
        'production_persistence_authorized':False,'production_activation_authorized':False,'replacements':products}
    package['package_sha256']=digest(package)
    return package


def validate_package(package):
    require(package==build(),'package differs from exact reviewed preparation')


def owned_state(conn,bundle):
    """ABSENT or complete exact immutable ownership; partial states fail closed."""
    batch=conn.execute('SELECT * FROM editorial_artifact_batches WHERE deterministic_batch_key=%s',(bundle['deterministic_batch_key'],)).fetchone()
    keys=[a['natural_key'] for a in bundle['artifacts']]
    versions=conn.execute('SELECT * FROM editorial_artifact_versions WHERE natural_key=ANY(%s)',(keys,)).fetchall()
    if batch is None:
        require(not versions,'unowned or partial artifact identities exist');return None
    require(batch['manifest_sha256']==bundle['manifest_sha256'] and batch['source_commit_sha']==bundle['source_commit_sha']
        and batch['status']=='applied' and batch['artifact_count']==len(bundle['artifacts'])
        and batch['relationship_count']==len(bundle['relationships']),'batch ownership differs')
    actual=conn.execute('SELECT * FROM editorial_artifact_versions WHERE batch_id=%s',(batch['batch_id'],)).fetchall()
    require(len(actual)==len(versions)==len(bundle['artifacts']),'partial/conflicting persisted graph')
    ids={}
    for expected in bundle['artifacts']:
        matches=[r for r in actual if r['natural_key']==expected['natural_key']]
        require(len(matches)==1,'artifact identity missing/duplicated')
        row=matches[0]
        require(all(row['payload_jsonb' if k=='payload' else k]==v for k,v in expected.items()),'persisted artifact content/ownership differs')
        ids[row['natural_key']]=row['artifact_id']
    rels=conn.execute('''SELECT p.natural_key AS parent_natural_key,c.natural_key AS child_natural_key,
        r.relationship_type,r.ordinal,r.metadata_jsonb AS metadata FROM editorial_artifact_relationships r
        JOIN editorial_artifact_versions p ON p.artifact_id=r.parent_artifact_id
        JOIN editorial_artifact_versions c ON c.artifact_id=r.child_artifact_id
        WHERE p.batch_id=%s OR c.batch_id=%s''',(batch['batch_id'],batch['batch_id'])).fetchall()
    require(sorted(rels,key=digest)==sorted(bundle['relationships'],key=digest),'persisted relationships differ')
    root=next(r for r in actual if r['artifact_type']=='issue_public_presentation')
    validate_eligible_graph(conn,root,bundle['publication_metadata'])
    return {'batch_id':batch['batch_id'],'artifact_ids':ids}


def preflight(conn,bundle):
    bound_artifact(conn,bundle['expected_old'],bundle['registry_key'])
    require(registry_row(conn,bundle['registry_key'])==bundle['prior_registry_row'],'current registry drift; no retargeting')
    from app.editorial_artifacts.repository import EditorialArtifactRepository
    require(any(r['artifact_id']==bundle['expected_old']['artifact_id'] for r in EditorialArtifactRepository(conn).publication_selector()),
        'current publication provenance is no longer eligible')
    return owned_state(conn,bundle)


def persist(conn,package,issue,*,fault_after=False):
    validate_package(package);bundle=package['replacements'][issue]
    require(not conn.autocommit,'owned transaction required')
    conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(bundle['deterministic_batch_key'],))
    registry_row(conn,bundle['registry_key'],lock=True)
    existing=preflight(conn,bundle)
    if existing: return {'status':'ALREADY_PERSISTED','writes':{k:0 for k in bundle['expected_counts']},**existing}
    result=store.insert_bundle(conn,bundle,{},batch_key=bundle['deterministic_batch_key'],source_commit=bundle['source_commit_sha'])
    require(result['artifacts_inserted']==len(bundle['artifacts']) and result['artifacts_idempotent']==0
        and result['relationships_inserted']==len(bundle['relationships']),'actual persistence counts differ')
    state=preflight(conn,bundle)
    if fault_after: raise store.StoreSafetyError('injected persistence failure')
    return {'status':'PERSISTED','writes':bundle['expected_counts'],**state}


def recover(conn,package,issue):
    validate_package(package);bundle=package['replacements'][issue]
    require(not conn.autocommit,'owned transaction required')
    conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(bundle['deterministic_batch_key'],))
    registry_row(conn,bundle['registry_key'],lock=True)
    require(preflight(conn,bundle) is not None,'owned persistence absent')
    result=store.rollback_batch(conn,bundle,batch_key=bundle['deterministic_batch_key'])
    require(preflight(conn,bundle) is None,'owned recovery incomplete')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['build','check','preflight','persist','recover'])
    parser.add_argument('--issue',choices=['NATIONAL_SECURITY_FOREIGN','JUSTICE_PUBLIC_SAFETY'])
    parser.add_argument('--target',choices=['production','disposable'])
    parser.add_argument('--env-path',type=Path)
    parser.add_argument('--database-url-env')
    parser.add_argument('--package-sha256')
    parser.add_argument('--expected-code-head')
    parser.add_argument('--confirm-production-persistence',action='store_true')
    parser.add_argument('--confirm-production-rollback',action='store_true')
    parser.add_argument('--report-path',type=Path)
    args=parser.parse_args();path=OUT/'persistence_package.json'
    if args.mode in ('build','check'):
        text=json.dumps(build(),sort_keys=True,ensure_ascii=False,indent=2)+'\n'
        if args.mode=='build': path.write_text(text,encoding='utf-8')
        else: require(path.read_text(encoding='utf-8')==text,'package drift')
        print('Exact actual M15B package verified');return
    require(args.issue and args.target and args.report_path,'explicit issue/target/report required')
    if args.target=='production':
        require(args.mode!='persist' or args.confirm_production_persistence,'explicit production persistence confirmation required')
        require(args.mode!='recover' or args.confirm_production_rollback,'explicit production rollback confirmation required')
    package=load(path);validate_package(package)
    require(args.package_sha256==package['package_sha256'],'exact reviewed package hash required')
    require(args.expected_code_head==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'exact reviewed code head required')
    require(not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip(),'tracked worktree is dirty')
    from dotenv import dotenv_values
    url=dotenv_values(args.env_path).get('DATABASE_URL') if args.env_path else os.environ[args.database_url_env]
    identity=target_identity(url,args.target)
    if args.target=='disposable': require_exact_loopback_postgres_url(url)
    else: require(identity==package['replacements'][args.issue]['production_target_identity_sha256'],'production target drift')
    # All credentials are local to this operator, never exported to test processes.
    with store._connect(url,autocommit=False) as conn:
        if args.mode=='preflight':
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            result={'transaction_read_only':True,'state':preflight(conn,package['replacements'][args.issue])}
        elif args.mode=='persist': result=persist(conn,package,args.issue)
        else: result=recover(conn,package,args.issue)
    args.report_path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print('Exact bounded operation completed')


if __name__=='__main__': main()
