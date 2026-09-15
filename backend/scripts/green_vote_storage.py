"""Single target-bound green load. No blue write or production cutover operation."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from urllib.parse import quote, urlsplit, unquote
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from dotenv import dotenv_values
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.capture_green_source import MAIN, BLUE, GREEN, pg_env, sha, primary_order
from scripts.editorial_artifact_store import target_info

GREEN_HOST='aws-0-us-east-1.pooler.supabase.com'
MODE='load-empty-normalized-public-v1'

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),default=str)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def green_url(password_path):
    password=password_path.read_text(encoding='utf-8-sig').strip()
    if not password:raise ValueError('missing external green password')
    return 'postgresql://postgres.'+GREEN+':'+quote(password,safe='')+'@'+GREEN_HOST+':5432/postgres?sslmode=require'
def require_green(green):
    g=urlsplit(green)
    if (g.scheme,g.hostname,g.port,g.path,unquote(g.username or ''))!=('postgresql',GREEN_HOST,5432,'/postgres','postgres.'+GREEN):raise ValueError('green identity mismatch')

def require_targets(blue,green):
    require_green(green)
    target_info(blue,'production',None)
    b=urlsplit(blue);g=urlsplit(green)
    if unquote(b.username or '')!='postgres.'+BLUE:raise ValueError('blue identity mismatch')
    if (g.scheme,g.hostname,g.port,g.path,unquote(g.username or ''))!=('postgresql',GREEN_HOST,5432,'/postgres','postgres.'+GREEN):raise ValueError('green identity mismatch')
    if (b.hostname,b.port,b.path,b.username)==(g.hostname,g.port,g.path,g.username) or BLUE==GREEN:raise ValueError('source and destination must differ')
def connect_readonly(url):
    c=psycopg.connect(url,connect_timeout=15,options='-c default_transaction_read_only=on -c statement_timeout=120000 -c lock_timeout=3000',row_factory=dict_row)
    c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    if c.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']!='on':raise ValueError('read-only connection required')
    return c

def logical_state(c,tables,sequences):
    c.execute("SET LOCAL extra_float_digits=3");c.execute("SET LOCAL timezone='UTC'")
    hashes={};counts={}
    for name,columns in sorted(tables.items()):
        h=hashlib.sha256()
        with c.cursor().copy(sql.SQL('COPY (SELECT {} FROM public.{} ORDER BY {}) TO STDOUT').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(name),primary_order(c,'vote_context_members' if name=='vote_contexts' and c.execute("SELECT relkind FROM pg_class WHERE oid='public.vote_contexts'::regclass").fetchone()['relkind']=='v' else name))) as reader:
            for chunk in reader:h.update(chunk)
        hashes[name]=h.hexdigest()
        counts[name]=c.execute(sql.SQL('SELECT count(*) n FROM public.{}').format(sql.Identifier(name))).fetchone()['n']
    seq={n:c.execute(sql.SQL('SELECT last_value,is_called FROM public.{}').format(sql.Identifier(n))).fetchone() for n in sequences}
    return {'hashes':hashes,'counts':counts,'sequences':seq}

def schema_state(c):
    queries={
      'relations':"SELECT relname,relkind,relrowsecurity,relforcerowsecurity,reloptions FROM pg_class WHERE relnamespace='public'::regnamespace ORDER BY 1",
      'columns':"SELECT table_name,column_name,ordinal_position,data_type,udt_name,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY 1,3",
      'constraints':"SELECT c.relname,k.conname,pg_get_constraintdef(k.oid) definition,k.convalidated FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid WHERE c.relnamespace='public'::regnamespace ORDER BY 1,2",
      'functions':"SELECT proname,pg_get_functiondef(oid) definition FROM pg_proc WHERE pronamespace='public'::regnamespace ORDER BY 1,2",
      'views':"SELECT viewname,definition FROM pg_views WHERE schemaname='public' ORDER BY 1",
      'policies':"SELECT tablename,policyname,permissive,roles,cmd,qual,with_check FROM pg_policies WHERE schemaname='public' ORDER BY 1,2",
      'indexes':"SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1,2",
      'triggers':"SELECT c.relname,t.tgname,pg_get_triggerdef(t.oid) definition,t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal ORDER BY 1,2",
      'enums':"SELECT t.typname,e.enumlabel,e.enumsortorder FROM pg_type t JOIN pg_enum e ON e.enumtypid=t.oid WHERE t.typnamespace='public'::regnamespace ORDER BY 1,3"}
    return {name:c.execute(q).fetchall() for name,q in queries.items()}

def services(c):
    result={}
    for name in ('auth.users','auth.identities','auth.sessions','auth.refresh_tokens','storage.buckets','storage.objects','realtime.subscription','vault.secrets','cron.job','supabase_migrations.schema_migrations'):
        exists=c.execute('SELECT to_regclass(%s) r',(name,)).fetchone()['r']
        result[name]=c.execute(sql.SQL('SELECT count(*) n FROM {}').format(sql.Identifier(*name.split('.')))).fetchone()['n'] if exists else 0
    result['realtime_published_tables']=c.execute("SELECT count(*) n FROM pg_publication_tables WHERE pubname='supabase_realtime'").fetchone()['n']
    return result

def read_manifest(path,expected_sha):
    if sha(path)!=expected_sha:raise ValueError('manifest digest mismatch')
    m=json.loads(path.read_text(encoding='utf-8'))
    if (m['main_sha'],m['blue_ref'],m['green_ref'],m['mode'])!=(MAIN,BLUE,GREEN,MODE):raise ValueError('authority binding mismatch')
    base=path.parent
    for name in ('capture.json','normalized.dump','normalized.sql','load-guard.sql','permissions.sql','source-schema.json'):
        if sha(base/name)!=m['files'][name]:raise ValueError('package digest mismatch: '+name)
    if m['source']!=json.loads((base/'capture.json').read_text(encoding='utf-8')):raise ValueError('source capture binding mismatch')
    schema_proof=json.loads((base/'source-schema.json').read_text(encoding='utf-8'))
    if schema_proof['source_dump_sha256']!=m['source']['blue_dump_sha256'] or digest(schema_proof['schema'])!=m['source_schema_digest']:raise ValueError('source schema binding mismatch')
    return m

def verify_data(c,m):
    cap=m['source']
    state=logical_state(c,cap['tables'],cap['sequences'])
    if state!={k:cap[k] for k in ('hashes','counts','sequences')}:raise ValueError('complete logical state mismatch')
    if digest(schema_state(c))!=m['normalized_schema_digest']:raise ValueError('normalized schema mismatch')
    size=c.execute('SELECT pg_database_size(current_database()) n').fetchone()['n']
    if size>=400000000:raise ValueError('green exceeds storage cap')
    return {'status':'EXACT_NORMALIZED_STATE','database_bytes':size,'tables':len(state['hashes']),'sequences':len(state['sequences'])}

def preflight(blue,green,m):
    require_targets(blue,green)
    with connect_readonly(blue) as source:
        if digest(schema_state(source))!=m['source_schema_digest']:raise ValueError('blue schema changed since capture')
        current=logical_state(source,m['source']['tables'],m['source']['sequences'])
        if current!={k:m['source'][k] for k in ('hashes','counts','sequences')}:raise ValueError('blue changed since frozen capture')
        if any(services(source).values()):raise ValueError('blue service state populated')
        source.rollback()
    with connect_readonly(green) as dest:
        if any(services(dest).values()):raise ValueError('green service state populated')
        schema=schema_state(dest)
        if digest(schema)==m['empty_green_schema_digest']:result={'status':'EMPTY_GREEN'}
        else:result=verify_data(dest,m)
        dest.rollback()
    return result

def execute(operation,blue,green,manifest_path,manifest_sha,pgbin,confirm=False):
    if operation=='load' and not confirm:raise ValueError('explicit green-load confirmation required')
    m=read_manifest(manifest_path,manifest_sha)
    state=preflight(blue,green,m)
    if operation=='preflight' or state['status']=='EXACT_NORMALIZED_STATE':return dict(state,writes=0)
    # The only write connection is the separately bound green DSN. psql executes
    # guard + exact package + permissions in one transaction; no cleanup/retry DDL.
    base=manifest_path.parent
    subprocess.run([str(pgbin/'psql.exe'),'--no-psqlrc','--single-transaction','--set=ON_ERROR_STOP=1','--file='+str(base/'load-guard.sql'),'--file='+str(base/'normalized.sql'),'--file='+str(base/'permissions.sql')],env=pg_env(green,readonly=False),check=True,capture_output=True,timeout=1200)
    with connect_readonly(green) as dest:
        result=verify_data(dest,m);dest.rollback()
    return dict(result,writes='bounded initial green application load',blue_writes=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=('preflight','load'));p.add_argument('--blue-env',type=Path,required=True);p.add_argument('--green-password-file',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--pg-bin',type=Path,required=True);p.add_argument('--confirm-green-load',action='store_true');a=p.parse_args()
    try:print(json.dumps(execute(a.operation,dotenv_values(a.blue_env)['DATABASE_URL'],green_url(a.green_password_file),a.manifest,a.manifest_sha256,a.pg_bin,a.confirm_green_load)))
    except Exception as e:raise SystemExit('Bound green operation failed: '+type(e).__name__+(' ('+str(e)+')' if isinstance(e,ValueError) else '')) from None
