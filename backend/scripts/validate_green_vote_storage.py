"""Managed-green proof: exact data/API, actual backend role, permissions, rolled-back ETL."""
import argparse,copy,hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from scripts.green_vote_storage import green_url,read_manifest,verify_data,schema_state,services,digest,require_green
from tests.test_normalized_vote_storage_postgres import public_outputs,benchmark,storage
from app.etl import normalized_vote_storage as norm,current_congress_refresh,senate_fact_import,senate_amendment_facts,seed

def validate(url,m,proof):
    require_green(url)
    os.environ['NORMALIZED_VOTE_STORAGE']='1';os.environ['ENABLE_FIXTURE_FALLBACK']='0'
    from scripts.green_vote_storage import require_targets
    # Static green URL construction and bound manifest are checked by the caller.
    with psycopg.connect(url,connect_timeout=15,row_factory=dict_row,autocommit=True,options='-c statement_timeout=120000 -c lock_timeout=5000') as c:
        c.execute("SET timezone='UTC'")
        role=c.execute('SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()
        assert role['current_user']=='postgres' and role['rolsuper'] is False
        with c.transaction():
            c.execute('SET TRANSACTION READ ONLY');data=verify_data(c,m)
        print('GREEN_COMPLETE_LOGICAL_PARITY',flush=True)
        with c.transaction():
            c.execute('SET TRANSACTION READ ONLY')
            api=public_outputs(c,proof['members'])
        api_digest=hashlib.sha256(json.dumps(api,sort_keys=True).encode()).hexdigest()
        assert api_digest==proof['api_sha256'], 'complete managed-green API output differs'
        print('GREEN_COMPLETE_API_PARITY',len(api),flush=True)
        denied={}
        relations=[r['relname'] for r in c.execute("SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','v','S') ORDER BY 1")]
        for role_name in ('anon','authenticated'):
            for rel in relations:
                kind=c.execute('SELECT relkind FROM pg_class WHERE oid=%s::regclass',('public.'+rel,)).fetchone()['relkind']
                function='has_sequence_privilege' if kind=='S' else 'has_table_privilege'
                privileges='SELECT,USAGE,UPDATE' if kind=='S' else 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'
                assert not c.execute(sql.SQL('SELECT {}(%s,%s,%s) allowed').format(sql.Identifier(function)),(role_name,'public.'+rel,privileges)).fetchone()['allowed']
            with c.transaction():
                c.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(role_name)))
                try:
                    with c.transaction():c.execute('SELECT * FROM public.vote_contexts LIMIT 1')
                except psycopg.errors.InsufficientPrivilege:denied[role_name]=True
                else:raise AssertionError('protected view exposed')
        assert c.execute("SELECT reloptions FROM pg_class WHERE oid='public.vote_contexts'::regclass").fetchone()['reloptions']==['security_invoker=true']
        assert c.execute("SELECT relrowsecurity FROM pg_class WHERE oid='public.vote_context_members'::regclass").fetchone()['relrowsecurity']
        member=c.execute("SELECT id FROM legislators WHERE bioguide_id='F000477'").fetchone()['id']
        sample=c.execute('SELECT * FROM vote_contexts WHERE legislator_id=%s ORDER BY roll_call_id',(member,)).fetchall()
        with c.transaction(force_rollback=True),c.cursor() as cur:
            assert norm.write_contexts(cur,sample)==0
            raw=dict(c.execute('SELECT * FROM roll_calls WHERE id=%s',(sample[0]['roll_call_id'],)).fetchone())
            raw={k:v for k,v in raw.items() if not k.startswith('context_')};raw['id']=-188;raw['rollcall_number']=999999
            cur.execute(sql.SQL('INSERT INTO roll_calls ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,raw)),sql.SQL(',').join(sql.Placeholder() for _ in raw)),tuple(raw.values()))
            incoming=c.execute('SELECT * FROM vote_contexts WHERE roll_call_id=%s ORDER BY legislator_id LIMIT 3',(sample[0]['roll_call_id'],)).fetchall()
            incoming=[dict(row,roll_call_id=-188) for row in incoming]
            args=(cur,incoming,{'-188':'new'},{str(r['legislator_id']):str(r['legislator_id']) for r in incoming},{'new':-188},{str(r['legislator_id']):r['legislator_id'] for r in incoming})
            assert current_congress_refresh._insert_vote_contexts(*args)==len(incoming)
            for producer in (current_congress_refresh,senate_fact_import,senate_amendment_facts):assert producer._insert_vote_contexts(*args)==0
            seed._write_rows(cur,insert_statement='',copy_statement='COPY vote_contexts (',rows=[tuple(r[k] for k in norm.LOGICAL) for r in incoming])
            bad=copy.deepcopy(incoming[:1]);bad[0]['context_source_list']=[{'drift':True}]
            try:
                with c.transaction():norm.write_contexts(cur,bad)
            except ValueError:pass
            else:raise AssertionError('shared drift accepted')
            first=incoming[0]
            c.execute('DELETE FROM vote_contexts WHERE roll_call_id=-188 AND legislator_id=%s',(first['legislator_id'],))
            cur.execute(sql.SQL('INSERT INTO vote_contexts ({}) VALUES ({})').format(sql.SQL(',').join(map(sql.Identifier,norm.LOGICAL)),sql.SQL(',').join(sql.Placeholder() for _ in norm.LOGICAL)),tuple(Jsonb(first[k]) if k in ('party_vote_totals','context_source_list') else first[k] for k in norm.LOGICAL))
            c.execute('UPDATE vote_contexts SET member_party=%s WHERE roll_call_id=-188 AND legislator_id=%s',('validation-only',first['legislator_id']))
            assert c.execute('SELECT count(*) n FROM vote_context_members WHERE roll_call_id=-188').fetchone()['n']==3
        assert c.execute('SELECT count(*) n FROM roll_calls WHERE id=-188').fetchone()['n']==0
        print('GREEN_ROLE_SECURITY_AND_ROLLBACK_ETL_PASS',flush=True)
        performance=benchmark(c,member)
        for name,v in performance.items():assert v['median_ms']<=max(50,proof['after_queries'][name]['median_ms']*3),name
        with c.transaction():
            c.execute('SET TRANSACTION READ ONLY');after=verify_data(c,m)
        return {'data':after,'api_outputs':len(api),'api_sha256':api_digest,'role':role,'denied_roles':denied,'security_invoker':True,'etl_rollback':True,'services':services(c),'storage':storage(c),'performance':performance,'blue_writes':False,'durable_synthetic_records':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--green-password-file',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    m=read_manifest(a.manifest,a.manifest_sha256)
    if hashlib.sha256(a.proof.read_bytes()).hexdigest()!=m['fresh_proof_sha256']:raise SystemExit('proof digest mismatch')
    result=validate(green_url(a.green_password_file),m,json.loads(a.proof.read_text()))
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2,default=str),encoding='utf-8');print('MANAGED_GREEN_PROOF_PASS',flush=True)
