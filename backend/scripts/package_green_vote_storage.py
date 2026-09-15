"""Package the already-proven local normalized state for the one green target."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.green_vote_storage import MODE,MAIN,BLUE,GREEN,sha,digest,connect_readonly,schema_state,logical_state,pg_env

GUARD="""SET lock_timeout='5s';
SET statement_timeout='600s';
SELECT pg_advisory_xact_lock(188017);
DO $$ BEGIN
 IF current_user<>'postgres' OR current_database()<>'postgres' THEN RAISE EXCEPTION 'green backend role/database required'; END IF;
 IF EXISTS(SELECT 1 FROM pg_class WHERE relnamespace='public'::regnamespace)
 OR EXISTS(SELECT 1 FROM pg_proc WHERE pronamespace='public'::regnamespace)
 OR EXISTS(SELECT 1 FROM pg_type WHERE typnamespace='public'::regnamespace)
 THEN RAISE EXCEPTION 'green app schema is not empty; refusing partial/conflicting state'; END IF;
END $$;
"""
PERMISSIONS="""REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC,anon,authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC,anon,authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC,anon,authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC,anon,authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC,anon,authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM PUBLIC,anon,authenticated;
"""

def package(capture_path,proof_path,empty_path,source_schema_path,out,pgbin,clone):
    if clone!='postgresql://postgres@127.0.0.1:55433/pf_normalized_storage':raise ValueError('exact dedicated clone required')
    if out.exists():raise ValueError('package already exists')
    cap=json.loads(capture_path.read_text());proof=json.loads(proof_path.read_text());empty=json.loads(empty_path.read_text())
    if cap['main_sha']!=MAIN or proof['complete_api_outputs']!=525 or proof['sequences_preserved']!=17:raise ValueError('full fresh proof required')
    if proof['source']!=cap['metadata']:raise ValueError('proof does not bind fresh source')
    with connect_readonly(clone) as c:
        current=logical_state(c,cap['tables'],cap['sequences'])
        if current!={k:cap[k] for k in ('hashes','counts','sequences')}:raise ValueError('normalized clone differs from source')
        schema=schema_state(c);c.rollback()
    source_schema=json.loads(source_schema_path.read_text())
    if source_schema['source_dump_sha256']!=cap['blue_dump_sha256']:raise ValueError('source schema proof mismatch')
    out.mkdir(parents=True)
    (out/'source-schema.json').write_bytes(source_schema_path.read_bytes())
    (out/'capture.json').write_bytes(capture_path.read_bytes())
    subprocess.run([str(pgbin/'pg_dump.exe'),'--schema=public','--format=custom','--file='+str(out/'normalized.dump')],env=pg_env(clone),check=True,capture_output=True,timeout=180)
    toc=subprocess.check_output([str(pgbin/'pg_restore.exe'),'--list',str(out/'normalized.dump')],text=True)
    lines=[l for l in toc.splitlines() if ' SCHEMA - public ' not in l and ' COMMENT - SCHEMA public ' not in l]
    (out/'restore.toc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    subprocess.run([str(pgbin/'pg_restore.exe'),'--no-owner','--no-privileges','--use-list='+str(out/'restore.toc'),'--file='+str(out/'normalized.sql'),str(out/'normalized.dump')],check=True,capture_output=True,timeout=180)
    (out/'load-guard.sql').write_text(GUARD,encoding='utf-8');(out/'permissions.sql').write_text(PERMISSIONS,encoding='utf-8')
    m={'main_sha':MAIN,'blue_ref':BLUE,'green_ref':GREEN,'mode':MODE,'source':cap,'source_schema_digest':digest(source_schema['schema']),'normalized_schema_digest':digest(schema),'empty_green_schema_digest':digest(empty['schema']),'fresh_proof_sha256':sha(proof_path),'files':{n:sha(out/n) for n in ('capture.json','normalized.dump','normalized.sql','load-guard.sql','permissions.sql','source-schema.json')}}
    (out/'manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2),encoding='utf-8')
    print(json.dumps({'manifest_sha256':sha(out/'manifest.json'),'dump_sha256':m['files']['normalized.dump'],'sql_sha256':m['files']['normalized.sql']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--empty-green',type=Path,required=True);p.add_argument('--source-schema-proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pg-bin',type=Path,required=True);a=p.parse_args()
    package(a.capture,a.proof,a.empty_green,a.source_schema_proof,a.output,a.pg_bin,'postgresql://postgres@127.0.0.1:55433/pf_normalized_storage')
