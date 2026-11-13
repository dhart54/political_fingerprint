"""Capacity-only local rehearsal. No production DSN, candidate mutation or installs.

Creates a brand-new private cluster with installed PostgreSQL17 binaries. Only
loopback connections to that verified data_directory are possible. Stores an
explicitly hypothetical candidate review mirror with the existing insert_bundle
and exact0016DDL. All artifacts stay pending/nonpromoted/ineligible. No pipeline
gate is bypassed or approval state changed. Stops server; retains private files.
"""
from pathlib import Path
import argparse
import copy
import datetime as dt
import gc
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
MAIN='af6cd6d78d6944d64a68a92653066c4c1625f96b'
IMM='a327f4ccd6f5d95ea12331bb91a8606382a59e50'
PG=Path('C:/Program Files/PostgreSQL/17/bin')
PRODUCTS=['shared_action_core.json','shared_issue_mapping.json','member_projections.json',
          'compiled_ir.json','readable_candidates.json','compiler_input.json','reproducibility_proof.json']
TABLES=['editorial_artifact_batches','editorial_artifact_versions',
        'editorial_artifact_relationships','editorial_publication_registry']
SELECTION=None


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(x):return hashlib.sha256(canon(x)).hexdigest()
def write(name,x):(OUT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str)+'\n',encoding='utf8',newline='\n')
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def nul_count(v):
    if isinstance(v,str):return v.count('\0')
    if isinstance(v,list):return sum(nul_count(x)for x in v)
    if isinstance(v,dict):return sum(nul_count(k)+nul_count(x)for k,x in v.items())
    return 0


def load_inputs(domain):
    ref=IMM if domain=='immigration' else MAIN
    prefix=f'docs/editorial/shared_candidates/house_119_{domain}_20260916/'
    values={};records=[]
    for n in PRODUCTS:
        path=prefix+'generated/'+n;b=git('show',ref+':'+path);x=json.loads(b)
        records.append({'path':path,'snapshot':ref,'git_blob_oid':git('rev-parse',ref+':'+path).decode().strip(),
                        'raw_git_bytes':len(b),'raw_sha256':hashlib.sha256(b).hexdigest(),
                        'canonical_json_bytes':len(canon(x)),'canonical_sha256':digest(x)})
        values[n]=x
    inventory=[]
    for line in git('ls-tree','-r','-l',ref,'--',prefix).decode().splitlines():
        meta,path=line.split('\t');mode,kind,oid,size=meta.split()
        inventory.append({'path':path,'git_blob_oid':oid,'bytes':int(size),'selected_generated':path in {r['path']for r in records}})
    return ref,values,records,inventory


def package(domain,version,conn=None):
    ref,v,records,inventory=load_inputs(domain)
    assert v['compiled_ir.json']['review_state']=='candidate_pending_external_semantic_review'
    members=[m['member_id']for m in v['compiled_ir.json']['members']]
    assert members==['F000477','M001184']
    # Verify the actual adapter still refuses these unchanged candidate bytes.
    from app.semantic_ir.adapters import build_persistence_proposal
    try:build_persistence_proposal(v['compiled_ir.json'])
    except ValueError as e:assert str(e)=='shared candidates cannot prepare persistence artifacts'
    else:raise AssertionError('Candidate persistence guard failed')
    rows=[];relationships=[]
    def add(label,kind,payload,member=None,action=None):
        key='capacity-only:'+domain+':'+label
        rows.append({'artifact_type':kind,'natural_key':key,'artifact_version':version,
          'schema_version':'hypothetical_candidate_capacity_proxy_v1','payload':payload,
          'content_sha256':digest(payload),'source_manifest_sha256':None,'source_commit_sha':ref,
          'member_bioguide_id':member,'issue_id':'capacity-only:'+domain,'congress':119,'chamber':'house',
          'canonical_action_id':action,'episode_id':None,'policy_family_id':None,
          'editorial_status':'human_approval_pending','benchmark_status':'not_promoted',
          'production_eligible':False,'review_route':'blocked','supersedes_artifact_id':None})
        return key
    core=v['shared_action_core.json']
    context={k:x for k,x in core.items()if k!='actions'}
    for a in core['actions']:
        add('action:'+a['action_id'],'shared_action_dossier',{'context':context,'action':a},action=a['action_id'])
    add('issue-mapping','issue_ontology',v['shared_issue_mapping.json'])
    for m in v['member_projections.json']:add('projection:'+m['member_id'],'member_action_overlay',m,m['member_id'])
    root=add('compiled-ir','issue_conclusion_propositions',v['compiled_ir.json'])
    readable=v['readable_candidates.json'];context={k:x for k,x in readable.items()if k!='members'}
    for m in readable['members']:add('readable:'+m['member_id'],'issue_public_presentation',{**context,'members':[m]},m['member_id'])
    add('compiler-input','reference_fixture_metadata',v['compiler_input.json'])
    add('reproducibility','standardization_validation_result',v['reproducibility_proof.json'])
    source_payload={'schema_version':'capacity_file_reference_manifest_v1','capacity_only':True,
      'production_selection_authorized':False,'complete_required_sources':False,
      'selected_generated_files':records,'excluded_sources_bank':[r for r in inventory if r['path']==f'docs/editorial/shared_candidates/house_119_{domain}_20260916/sources.json']}
    source_key=add('source-references','source_manifest',source_payload)
    omitted=[]
    if SELECTION=='jsonb-compatible-subset':
        omitted=[{'natural_key':r['natural_key'],'canonical_payload_bytes':len(canon(r['payload'])),
                   'content_sha256':r['content_sha256'],'nul_count':nul_count(r['payload'])}
                  for r in rows if nul_count(r['payload'])]
        rows=[r for r in rows if not nul_count(r['payload'])]
        rows[-1]['payload']['measurement_selection']='INCOMPLETE jsonb-compatible subset, not the full candidate package'
        rows[-1]['payload']['omitted_whole_artifacts']=omitted
        rows[-1]['content_sha256']=digest(rows[-1]['payload'])
    source_hash=rows[-1]['content_sha256']
    for r in rows:
        r['source_manifest_sha256']=source_hash
        if version>1:
            old=conn.execute('SELECT artifact_id FROM editorial_artifact_versions WHERE natural_key=%s AND artifact_version=%s',(r['natural_key'],version-1)).fetchone()
            assert old;r['supersedes_artifact_id']=old['artifact_id']
        if r['natural_key']==root:continue
        kind={'source_manifest':'uses_source_manifest','shared_action_dossier':'contains_action',
              'standardization_validation_result':'has_validation','issue_public_presentation':'has_public_presentation',
              'member_action_overlay':'has_member_overlay'}.get(r['artifact_type'],'has_reference_metadata')
        relationships.append({'parent_natural_key':root,'child_natural_key':r['natural_key'],'relationship_type':kind,
                               'ordinal':len(relationships),'metadata':{'capacity_only':True}})
    manifest={'domain':domain,'version':version,'records':records,'policy':'hypothetical-granular-generated-review-mirror-v1','selection':SELECTION}
    bundle={'manifest_sha256':digest(manifest),'artifacts':rows,'relationships':relationships,
            'expected_counts':{'artifacts':len(rows),'relationships':len(relationships)}}
    info={'domain':domain,'snapshot':ref,'members':members,'records':records,'inventory':inventory,
      'row_count':len(rows),'relationship_count':len(relationships),'shared_actions':len(core['actions']),
      'canonical_payload_bytes':sum(len(canon(r['payload']))for r in rows),'package_manifest_sha256':bundle['manifest_sha256'],
      'gate_check':'unchanged candidate rejected by real persistence adapter','selection':SELECTION,
      'omitted_whole_artifacts':omitted,'full_candidate_size_measured':not omitted}
    return bundle,info


def snapshot(conn):
    rows=conn.execute("""SELECT c.relname,
      pg_relation_size(c.oid) heap_main_bytes,pg_table_size(c.oid) table_including_toast_bytes,
      pg_indexes_size(c.oid) direct_index_bytes,pg_total_relation_size(c.oid) total_bytes,
      CASE WHEN c.reltoastrelid=0 THEN 0 ELSE pg_relation_size(c.reltoastrelid) END toast_heap_main_bytes,
      CASE WHEN c.reltoastrelid=0 THEN 0 ELSE pg_indexes_size(c.reltoastrelid) END toast_index_bytes,
      CASE WHEN c.reltoastrelid=0 THEN 0 ELSE pg_total_relation_size(c.reltoastrelid) END toast_total_bytes
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public'AND c.relname=ANY(%s)ORDER BY c.relname""",(TABLES,)).fetchall()
    counts={t:conn.execute('SELECT count(*) n FROM '+t).fetchone()['n']for t in TABLES}
    return {'at_utc':now(),'relations':rows,'counts':counts,
      'store_total_bytes':sum(r['total_bytes']for r in rows),
      'database_bytes':conn.execute('SELECT pg_database_size(current_database()) n').fetchone()['n'],
      'row_sizes':conn.execute("""SELECT natural_key,artifact_version,pg_column_size(payload_jsonb) payload_stored_bytes,
            pg_column_compression(payload_jsonb) compression FROM editorial_artifact_versions
            ORDER BY natural_key,artifact_version""").fetchall()}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute-new-local-cluster',action='store_true')
    parser.add_argument('--selection',choices=['full-generated-mirror','jsonb-compatible-subset'],required=True)
    a=parser.parse_args()
    if not a.execute_new_local_cluster:raise SystemExit('Explicit new-local-cluster flag required')
    os.chdir(ROOT);sys.path.insert(0,str(ROOT/'backend'))
    global SELECTION
    SELECTION=a.selection
    # Pin importer/schema code rather than accepting an active working-tree edit.
    code_paths=['backend/scripts/editorial_artifact_store.py','backend/app/editorial_artifacts/bundle.py',
      'backend/app/editorial_artifacts/migration.py','backend/app/semantic_ir/adapters.py',
      'backend/app/semantic_ir/pipeline.py','backend/migrations/0016_editorial_artifact_persistence.sql']
    code=[]
    for p in code_paths:
        b=git('show',MAIN+':'+p);assert (ROOT/p).read_text(encoding='utf8').replace('\r\n','\n')==b.decode().replace('\r\n','\n')
        code.append({'path':p,'git_blob_oid':git('rev-parse',MAIN+':'+p).decode().strip(),'sha256':hashlib.sha256(b).hexdigest()})
    from scripts.editorial_artifact_store import insert_bundle
    import psycopg
    from psycopg.rows import dict_row
    from psycopg import sql
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')
    private=ROOT/'.local'/('capacity-pg-'+run_id);assert not private.exists();private.mkdir(parents=True)
    data=private/'data';log=private/'postgres.log'
    with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    receipt={'started_utc':now(),'host':'local','source_code':code,'method':'hypothetical-granular-generated-review-mirror-v1',
      'selection':SELECTION,'full_candidate_size_measured':SELECTION=='full-generated-mirror',
      'production_connections':0,'production_writes':0,'server':{'data_directory':str(data),'port':port},'stages':{},'inputs':{},'commands':[]}
    write('measurement.json',receipt)
    def command(label,args):
        # Daemon children may inherit Windows PIPE handles; files avoid an EOF wait.
        t=time.perf_counter()
        with (private/(label+'.log')).open('w',encoding='utf8')as output:
            r=subprocess.run([str(x)for x in args],stdout=output,stderr=subprocess.STDOUT,
                timeout=40,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'BELOW_NORMAL_PRIORITY_CLASS',0))
        receipt['commands'].append({'label':label,'seconds':time.perf_counter()-t,'exit_code':r.returncode})
        if r.returncode:raise RuntimeError(label+' failed: '+(private/(label+'.log')).read_text(encoding='utf8',errors='replace')[-1200:])
    started=False
    try:
        command('initdb',[PG/'initdb.exe','-D',data,'--username=capacity_local','--auth=trust','--encoding=UTF8','--locale=C'])
        started=True  # Any failed start is still cleaned up against this unique new directory.
        command('start',[PG/'pg_ctl.exe','start','-D',data,'-l',log,'-w','-t','25','-o',
            f'-h 127.0.0.1 -p {port} -c shared_buffers=32MB -c max_connections=10 -c max_parallel_workers_per_gather=0 -c autovacuum=off'])
        def connect(db):
            assert db=='postgres'or db.startswith('capacity_')
            c=psycopg.connect(host='127.0.0.1',port=port,user='capacity_local',dbname=db,connect_timeout=5,autocommit=True,row_factory=dict_row)
            assert Path(c.execute('SHOW data_directory').fetchone()['data_directory']).resolve()==data.resolve()
            c.execute("SET statement_timeout='60s';SET lock_timeout='2s'")
            return c
        with connect('postgres')as admin:
            receipt['server'].update(admin.execute("SELECT version() version,current_setting('block_size')block_size,current_setting('default_toast_compression')default_toast_compression,(SELECT datcollate FROM pg_database WHERE datname=current_database())lc_collate,(SELECT system_identifier FROM pg_control_system())system_identifier").fetchone())
            for role in ['anon','authenticated']:admin.execute(sql.SQL('CREATE ROLE {} NOLOGIN').format(sql.Identifier(role)))
            for case,domains in [('immigration',['immigration']),('health',['health']),('combined',['immigration','health'])]:
                db='capacity_'+case;admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db)))
                with connect(db)as conn:
                    conn.execute("CREATE TYPE chamber AS ENUM('house','senate');CREATE TABLE legislators(bioguide_id TEXT PRIMARY KEY);CREATE TABLE roll_calls(id BIGSERIAL PRIMARY KEY);INSERT INTO legislators VALUES('F000477'),('M001184')")
                    conn.execute(git('show',MAIN+':backend/migrations/0016_editorial_artifact_persistence.sql').decode())
                    state={'baseline':snapshot(conn),'loads':[]};roll_ids={}
                    for domain in domains:
                        t=time.perf_counter();bundle,info=package(domain,1,conn);receipt['inputs'][domain]=info
                        for r in bundle['artifacts']:
                            aid=r['canonical_action_id']
                            if aid and aid not in roll_ids:roll_ids[aid]=conn.execute('INSERT INTO roll_calls DEFAULT VALUES RETURNING id').fetchone()['id']
                        with conn.transaction():
                            outcome=insert_bundle(conn,bundle,roll_ids,batch_key='capacity:'+case+':'+domain+':1',source_commit=IMM if domain=='immigration'else MAIN)
                        # Independent round trip against exact canonical payload digests.
                        for r in bundle['artifacts']:
                            actual=conn.execute('SELECT payload_jsonb,editorial_status,production_eligible FROM editorial_artifact_versions WHERE natural_key=%s AND artifact_version=1',(r['natural_key'],)).fetchone()
                            assert digest(actual['payload_jsonb'])==r['content_sha256'];assert actual['editorial_status']=='human_approval_pending'and not actual['production_eligible']
                        before=snapshot(conn)
                        with conn.transaction():
                            idem=insert_bundle(conn,bundle,roll_ids,batch_key='capacity:'+case+':'+domain+':1',source_commit=IMM if domain=='immigration'else MAIN)
                        after=snapshot(conn)
                        assert idem['artifacts_inserted']==0 and idem['relationships_inserted']==0
                        assert before['counts']==after['counts']and before['store_total_bytes']==after['store_total_bytes']
                        state['loads'].append({'domain':domain,'seconds':time.perf_counter()-t,'insert':outcome,'idempotent':idem,'snapshot':after})
                        print(json.dumps({'case':case,'domain':domain,'seconds':state['loads'][-1]['seconds'],'store_total_bytes':after['store_total_bytes']}),flush=True)
                        del bundle;gc.collect()
                    state['after_v1']=snapshot(conn)
                    if case=='combined':
                        state['retained_revision_loads']=[]
                        for domain in domains:
                            t=time.perf_counter();bundle,_=package(domain,2,conn)
                            with conn.transaction():
                                outcome=insert_bundle(conn,bundle,roll_ids,batch_key='capacity:'+case+':'+domain+':2',source_commit=IMM if domain=='immigration'else MAIN)
                            state['retained_revision_loads'].append({'domain':domain,'seconds':time.perf_counter()-t,'insert':outcome})
                            del bundle;gc.collect()
                        state['after_retained_identical_v2']=snapshot(conn)
                        assert state['after_retained_identical_v2']['counts']['editorial_artifact_versions']==2*state['after_v1']['counts']['editorial_artifact_versions']
                        assert conn.execute('SELECT count(*) n FROM editorial_artifact_versions WHERE artifact_version=2 AND supersedes_artifact_id IS NOT NULL').fetchone()['n']==state['after_v1']['counts']['editorial_artifact_versions']
                    assert conn.execute('SELECT count(*)n FROM editorial_publication_registry').fetchone()['n']==0
                    state['index_definitions']=conn.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public'AND tablename=ANY(%s)ORDER BY indexname",(TABLES,)).fetchall()
                    receipt['stages'][case]=state;write('measurement.json',receipt)
    except BaseException as e:
        receipt['error']=repr(e);raise
    finally:
        if started:
            try:command('stop',[PG/'pg_ctl.exe','stop','-D',data,'-m','fast','-w','-t','25']);receipt['server']['stopped']=True
            except BaseException as e:receipt['stop_error']=repr(e)
        receipt['finished_utc']=now();write('measurement.json',receipt)
    print(json.dumps({'finished_utc':receipt['finished_utc'],'server_stopped':receipt['server'].get('stopped'),'cases':list(receipt['stages'])}),flush=True)


if __name__=='__main__':main()
