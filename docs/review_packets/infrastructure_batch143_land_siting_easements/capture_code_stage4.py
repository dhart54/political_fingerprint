import base64,gzip,hashlib,json,sys,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.validate_infrastructure_hr859_scope137 import TextParser
T=Path('.tmp/infra_batch143');P=Path('docs/review_packets/infrastructure_batch143_land_siting_easements');S=json.loads((T/'capture_preflight.json').read_text());remaining=S['max_total_response_bytes']-sum(json.loads(p.read_text(encoding='utf8'))['raw_response_bytes'] for p in P.glob('*_capture.json'));results=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
selected=set(sys.argv[1:]);assert selected and selected<=set(u['key'] for u in S['source_units'])
for unit in [u for u in S['source_units'] if u['key'] in selected]:
 key,url=unit['key'],unit['url'];path=P/(key+'_capture.json')
 if path.exists():raise RuntimeError('Capture exists; no re-request permitted: '+key)
 request=urllib.request.Request(url,headers={'User-Agent':'PoliticalFingerprintResearch/1.0'})
 now=datetime.now(timezone.utc).isoformat();status=None;final=url;headers={};error=None;raw=b''
 try:
  with urllib.request.urlopen(request,timeout=S['timeout_seconds']) as response:
   status=response.status;final=response.geturl();headers={k:response.headers.get(k) for k in ['Content-Type','Last-Modified','Date']};raw=response.read(min(S['max_response_bytes'],remaining)+1)
 except urllib.error.HTTPError as exc:
  status=exc.code;final=exc.geturl();raw=exc.read(min(S['max_response_bytes'],remaining)+1);error=type(exc).__name__+': '+str(exc)
 except (urllib.error.URLError,TimeoutError) as exc:error=type(exc).__name__+': '+str(exc)
 encoding='base64';payload=raw
 if len(raw)>100000:encoding='gzip+base64';payload=gzip.compress(raw,mtime=0)
 record={'source_key':key,'requested_url':url,'final_url':final,'attempt_number':1,'capture_started_utc':now,'http_status':status,'headers':headers,'transport_error':error,'raw_response_bytes':len(raw),'raw_response_sha256':sha(raw),'raw_response_encoding':encoding,'raw_response_base64':base64.b64encode(payload).decode(),'content_validation':'NOT_YET_RUN; raw persisted first','body_exceeds_cap':len(raw)>min(S['max_response_bytes'],remaining),'source_registered':False,'canonical_state_changed':False}
 path.write_bytes((json.dumps(record,indent=2)+'\n').encode())
 # Every response, including bad-status or wrong-content responses, is retained
 # before edition/title/extraction checks. No network retries or alternates.
 remaining-=len(raw)
 if status!=200 or error or record['body_exceeds_cap']:
  record['content_validation']='FAILED_OR_UNCLASSIFIED; no retry/alternate'
 elif unit.get('format')=='pdf':
  record['format']='pdf';record['content_validation']='PDF_TRANSPORT_PASS; relevant pages not yet extracted or visually read' if raw.startswith(b'%PDF') else 'PDF_IDENTITY_FAIL'
  if raw.startswith(b'%PDF'):(T/(key+'.pdf')).write_bytes(raw)
 else:
  parser=TextParser();parser.feed(raw.decode('utf8'));text=' '.join(' '.join(parser.parts).split());record.update(normalized_text=text,normalized_text_sha256=sha(text.encode()),normalized_text_characters=len(text))
  identity=('117-80' in text and '135 STAT.' in text) if key=='plaw11780' else ('2024 Edition' in text and 'United States Code' in text)
  record['content_validation']='EDITION_IDENTITY_PASS; selected operative extent not yet read' if identity else 'EDITION_IDENTITY_FAIL; no source meaning accepted'
 path.write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode());results.append({k:record.get(k) for k in ['source_key','http_status','raw_response_bytes','raw_response_sha256','content_validation','transport_error']});print(json.dumps(results[-1]),flush=True)
 (T/'capture_results.json').write_bytes((json.dumps(results,indent=2)+'\n').encode())
 if status in [401,403,429] or error or record['body_exceeds_cap'] or remaining<=0:
  print('STOP remaining transport; no workaround or retry',flush=True);break
