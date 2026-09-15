import sys,json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path('backend').resolve()))
import httpx
from psycopg import sql
from dotenv import dotenv_values
from scripts.green_production_target import target_identity
from scripts.green_vote_storage import connect_readonly,schema_state,digest as schema_digest
from scripts.capture_green_source import primary_order
from scripts import m15b_persistence_preparation as prep
from scripts.capture_m15b_preparation_baseline import capture
from app.editorial_presentations.compiler import canonical_digest as digest
OUT=Path('.local/persist-m15b');label=sys.argv[1]
assert label in ('before','after-ns','after-justice')
env=dotenv_values('.local/green-production.env');assert env['NORMALIZED_VOTE_STORAGE']=='1'
url=env['DATABASE_URL'];identity=target_identity(url,'production')
assert identity=='0bdeba5d97ecc77e9117d15f50d952f534a6e6dd9c66950d98d96bcad72523ea'
p=prep.load(prep.OUT/'persistence_package.json');prep.validate_package(p)
assert p['package_sha256']=='55f81e763c085c4128de30863ec7d77c7f5bfb51695bbe739c4709cb3d80e362'
assert p['production_baseline_sha256']=='9e10eaf2738a6ba4baedb6dd7d2776674c200071da9c03e79bb0858b04d1864c'
state={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'transaction_read_only':True,'production_target_identity_sha256':identity}
with connect_readonly(url) as c:
 c.execute("SET LOCAL timezone='UTC'");c.execute('SET LOCAL extra_float_digits=3')
 names=[r['tablename'] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")]
 fingerprints={}
 for name in names:
  q=sql.SQL("SELECT count(*) n, encode(sha256(convert_to(COALESCE(string_agg(encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex'),'' ORDER BY {}),''),'UTF8')),'hex') sha256 FROM public.{} t").format(primary_order(c,name),sql.Identifier(name))
  fingerprints[name]=dict(c.execute(q).fetchone())
  print('READ_ONLY_TABLE',name,flush=True)
 state['table_fingerprints']=fingerprints
 state['schema_sha256']=schema_digest(schema_state(c))
 state['owned']={i:prep.preflight(c,b) for i,b in p['replacements'].items()}
 state['editorial_rows']={n:c.execute(sql.SQL('SELECT * FROM public.{} ORDER BY 1').format(sql.Identifier(n))).fetchall() for n in ('editorial_artifact_batches','editorial_artifact_versions','editorial_artifact_relationships','editorial_publication_registry')}
 baseline,fixture,public=capture(c,identity)
 state['sequences']=baseline['sequences'];state['database_bytes']=baseline['database_bytes'];state['public_sha256']=digest(public)
 assert public==json.loads(gzip.decompress((prep.OUT/'public_before.json.gz').read_bytes())), 'current public changed from reviewed baseline'
 state['registry_roots']={r['issue_id']:r['artifact_id'] for r in state['editorial_rows']['editorial_publication_registry']}
 if label=='before':assert all(v is None for v in state['owned'].values()),'proposed owned state must be absent'
 c.rollback()
state=json.loads(json.dumps(state,default=str))
with httpx.Client(timeout=90,follow_redirects=False) as h:
 health=h.get('https://political-fingerprint.onrender.com/health');health.raise_for_status();assert health.json()=={'status':'ok','commit_sha':prep.MERGED}
 live={}
 for scope in ('118','119','all'):
  paths=['editorial-presentations','positions','fingerprint']+['positions/'+d+'/evidence' for d in ('NATIONAL_SECURITY_FOREIGN','JUSTICE_PUBLIC_SAFETY','EDUCATION_WORKFORCE','ENVIRONMENT_ENERGY')]
  for path in paths:
   r=h.get('https://political-fingerprint.onrender.com/legislators/leg_valerie_p_foushee/'+path,params={'scope':scope});r.raise_for_status();live[scope+'/'+path]=r.json()
state['live_sha256']=digest(live);state['live_responses']=len(live);state['health']=health.json()
if label!='before':
 prior=json.loads((OUT/'before.json').read_text());count=1 if label=='after-ns' else 2
 expected={'editorial_artifact_batches':count,'editorial_artifact_versions':count*3,'editorial_artifact_relationships':count*2}
 assert state['schema_sha256']==prior['schema_sha256'] and state['database_bytes']<400000000
 assert state['registry_roots']==prior['registry_roots'] and state['public_sha256']==prior['public_sha256'] and state['live_sha256']==prior['live_sha256']
 assert json.loads(gzip.decompress((OUT/'before-live.json.gz').read_bytes()))==live
 for name,fp in state['table_fingerprints'].items():
  if name not in expected:assert fp==prior['table_fingerprints'][name], 'unrelated table changed: '+name
  else:assert fp['n']==prior['table_fingerprints'][name]['n']+expected[name], 'count mismatch: '+name
 for name,rows in prior['editorial_rows'].items():
  idkey={'editorial_artifact_batches':'batch_id','editorial_artifact_versions':'artifact_id','editorial_artifact_relationships':None}.get(name)
  if idkey:
   ids={r[idkey] for r in rows};assert [r for r in state['editorial_rows'][name] if r[idkey] in ids]==rows,'existing editorial rows changed'
  elif name=='editorial_artifact_relationships':
   parents={r['parent_artifact_id'] for r in rows}
   assert sorted([r for r in state['editorial_rows'][name] if r['parent_artifact_id'] in parents],key=digest)==sorted(rows,key=digest),'existing relationships changed'
  else:assert state['editorial_rows'][name]==rows,'registry changed'
 allowed={'editorial_artifact_batches_batch_id_seq':count,'editorial_artifact_versions_artifact_id_seq':count*3,'editorial_artifact_relationships_relationship_id_seq':count*2}
 for name,s in state['sequences'].items():
  old=prior['sequences'][name]
  assert s['last_value']==old['last_value']+allowed.get(name,0),'unexpected sequence change: '+name
 state['verified_combined_mutation_counts']={'batches':count,'artifacts':count*3,'relationships':count*2,'registry_updates':0,'other_writes':0}
state['audit_sha256']=digest(state)
assert not (OUT/(label+'.json')).exists(),'preserve receipt'
(OUT/(label+'.json')).write_text(json.dumps(state,indent=2,sort_keys=True)+'\n',encoding='utf-8')
(OUT/(label+'-live.json.gz')).write_bytes(gzip.compress(json.dumps(live,sort_keys=True).encode(),mtime=0))
print(json.dumps({k:state[k] for k in ('audit_sha256','owned','database_bytes','registry_roots','live_responses','live_sha256')}),flush=True)
