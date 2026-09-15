"""Fresh read-only blue capture for the single reviewed normalized-green move."""
from __future__ import annotations
import argparse, gzip, hashlib, json, os, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from dotenv import dotenv_values
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.editorial_artifact_store import target_info
from scripts.capture_vote_storage_baseline import SHARED, MEMBER

MAIN='638eac771e2d32db27258716c6334e2a7d7ea089'
BLUE='wfhnmuxlbfpweupisfao'
GREEN='yalpfkaxkxebwolhorha'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pg_env(url,readonly=True):
    p=urlsplit(url)
    return dict(os.environ,PGHOST=p.hostname,PGPORT=str(p.port or 5432),PGDATABASE=p.path.lstrip('/'),PGUSER=unquote(p.username),PGPASSWORD=unquote(p.password or ''),PGSSLMODE='require' if p.hostname not in ('127.0.0.1','localhost') else 'prefer',PGCONNECT_TIMEOUT='15',PGOPTIONS='-c default_transaction_read_only='+('on' if readonly else 'off'))
def primary_order(c,name):
    rows=c.execute("SELECT a.attname FROM pg_constraint k CROSS JOIN LATERAL unnest(k.conkey) WITH ORDINALITY x(attnum,n) JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=x.attnum WHERE k.conrelid=%s::regclass AND k.contype='p' ORDER BY x.n",('public.'+name,)).fetchall()
    if not rows:raise ValueError('stable primary-key ordering required: '+name)
    return sql.SQL(',').join(sql.Identifier(r['attname']) for r in rows)

def capture(url,out,pgbin):
    target=target_info(url,'production',None)
    if out.exists():raise ValueError('capture directory already exists; do not overwrite evidence')
    out.mkdir(parents=True)
    with psycopg.connect(url,options='-c default_transaction_read_only=on -c statement_timeout=120000 -c lock_timeout=3000',connect_timeout=15,row_factory=dict_row) as c:
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        assert c.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        runtime=c.execute("SELECT current_setting('extra_float_digits') extra_float_digits,current_setting('TimeZone') timezone").fetchone()
        c.execute("SET LOCAL extra_float_digits=3");c.execute("SET LOCAL timezone='UTC'")
        snap=c.execute('SELECT pg_export_snapshot() snapshot').fetchone()['snapshot']
        meta=c.execute('SELECT now() captured_at,pg_database_size(current_database()) database_bytes,current_setting(\'server_version\') version,current_user role').fetchone()
        fields=sql.SQL(',').join(map(sql.Identifier,SHARED))
        conflicts=c.execute(sql.SQL('SELECT count(*) n FROM (SELECT roll_call_id FROM public.vote_contexts GROUP BY roll_call_id HAVING count(DISTINCT ROW({}))<>1) x').format(fields)).fetchone()['n']
        if conflicts:raise ValueError('roll context ambiguity')
        meta.update(runtime_settings=runtime,shared_fields=SHARED,member_fields=MEMBER,shared_conflicts=0)
        seqs=[r['sequencename'] for r in c.execute("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY 1")]
        sequences={n:c.execute(sql.SQL('SELECT last_value,is_called FROM public.{}').format(sql.Identifier(n))).fetchone() for n in seqs}
        tables=[r['tablename'] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")]
        accepted=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/normalized_vote_storage_sequences.json').read_text())
        if set(seqs)!=set(accepted['sequences']):raise ValueError('sequence inventory changed')
        subprocess.run([str(pgbin/'pg_dump.exe'),'--schema=public','--format=custom','--snapshot='+snap,'--file='+str(out/'blue-public.dump')],env=pg_env(url),check=True,capture_output=True,timeout=600)
        hashes={};counts={};columns_by_table={}
        with gzip.open(out/'fresh.jsonl.gz','wt',encoding='utf-8') as stream:
            stream.write(json.dumps({'metadata':meta},default=str)+'\n')
            for name in tables:
                columns=[r['column_name'] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",(name,))]
                columns_by_table[name]=columns
                h=hashlib.sha256()
                with c.cursor().copy(sql.SQL('COPY (SELECT * FROM public.{} ORDER BY {}) TO STDOUT').format(sql.Identifier(name),primary_order(c,name))) as reader:
                    for chunk in reader:h.update(chunk)
                hashes[name]=h.hexdigest()
                exported=list(MEMBER) if name=='vote_contexts' else columns
                stream.write(json.dumps({'table':name,'columns':exported})+'\n');count=0
                with c.cursor(name='green_capture') as cur:
                    cur.itersize=5000
                    cur.execute(sql.SQL('SELECT {} FROM public.{} ORDER BY {}').format(sql.SQL(',').join(map(sql.Identifier,exported)),sql.Identifier(name),primary_order(c,name)))
                    for row in cur:
                        stream.write(json.dumps([row[k] for k in exported],default=str,separators=(',',':'))+'\n');count+=1
                        if count>2000000:raise ValueError('table cap exceeded')
                counts[name]=count;stream.write('null\n')
            cols=['roll_call_id',*SHARED]
            stream.write(json.dumps({'table':'shared_context_snapshot','columns':cols})+'\n')
            for row in c.execute(sql.SQL('SELECT DISTINCT ON (roll_call_id) {} FROM public.vote_contexts ORDER BY roll_call_id,legislator_id').format(sql.SQL(',').join(map(sql.Identifier,cols)))):
                stream.write(json.dumps([row[k] for k in cols],default=str,separators=(',',':'))+'\n')
            stream.write('null\n')
        after={n:c.execute(sql.SQL('SELECT last_value,is_called FROM public.{}').format(sql.Identifier(n))).fetchone() for n in seqs}
        if after!=sequences:raise ValueError('writer activity: sequence state changed during capture')
        inventory={'rls':c.execute("SELECT c.relname,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','v') ORDER BY 1").fetchall(), 'grants':c.execute("SELECT table_name,grantee,privilege_type FROM information_schema.role_table_grants WHERE table_schema='public' ORDER BY 1,2,3").fetchall(),'extensions':c.execute('SELECT extname,extversion FROM pg_extension ORDER BY 1').fetchall()}
        c.rollback()
    (out/'sequences.json').write_text(json.dumps({'sequences':sequences},indent=2),encoding='utf-8')
    manifest={'main_sha':MAIN,'blue_ref':BLUE,'green_ref':GREEN,'target':target,'metadata':meta,'tables':columns_by_table,'counts':counts,'hashes':hashes,'sequences':sequences,'inventory':inventory,'blue_dump_sha256':sha(out/'blue-public.dump'),'fixture_sha256':sha(out/'fresh.jsonl.gz'),'blue_writes':False}
    (out/'capture.json').write_text(json.dumps(manifest,default=str,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps({'capture_sha256':sha(out/'capture.json'),'captured_at':str(meta['captured_at']),'counts':counts,'blue_writes':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--blue-env',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pg-bin',type=Path,required=True);a=p.parse_args()
    try:capture(dotenv_values(a.blue_env)['DATABASE_URL'],a.output,a.pg_bin)
    except Exception as e:raise SystemExit('Fresh blue capture failed: '+type(e).__name__) from None
