import copy,json,sys,re
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.validate_infrastructure_disaster_candidates142 import sha,normalized_pdf
T=Path('.tmp/infra_batch144');P=Path('docs/review_packets/infrastructure_batch144_va_research_administration');I=Path('docs/editorial/shared_candidates/house_119_infrastructure_batch139_20260916');H=Path('docs/editorial/shared_candidates/house_119_health_20260916');BASE='1d4496ef28a2180dbd842fe6ece8dcf785da4003'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
ip={s['source_id']:s for s in read(I/'sources.json')['sources']};hp={s['source_id']:s for s in read(H/'sources.json')['sources']}
aids=['house:119:1:89','house:119:1:90','house:119:1:115','house:119:1:133','house:119:2:49'];bills=[586,1039,530,1286,980]
ids=[x.replace('house:','clerk:') for x in aids]+[f'govinfo:hr{b}eh' for b in bills]+['govinfo:38usc5503d-2024-pension-cap','govinfo:38usc3697A-B-operative']
sources=[];retained=[]
for pool,folder,names in [(ip,I,ids),(hp,H,['govinfo:38usc3104-operative','govinfo:38usc3105-operative','govinfo:38usc3680A-flight','govinfo:pl119-43-pension-expiry'])]:
 for sid in names:
  s=pool[sid];assert sealed_digest(s,'governed_bytes_sha256')==s['governed_bytes_sha256']
  if sid in ip and sid in hp:assert digest(ip[sid])==digest(hp[sid]),sid
  sources.append(copy.deepcopy(s));retained.append(dict(source_id=sid,snapshot=folder.as_posix(),source_object_sha256=digest(s),governed_bytes_sha256=s['governed_bytes_sha256'],raw_sha256=s['raw_sha256'],read_extent='Complete retained selected text; Clerk object metadata and both named member rows only' if not s.get('text') else 'Complete retained text unit, not unretained parent'))
assert len(sources)==16
captures={p.name.removesuffix('_capture.json'):read(p) for p in P.glob('*_capture.json')};assert len(captures)==7
assert captures['crec20260202house']['raw_response_sha256']==hp['congressional-record:2026-02-02-veterans']['raw_sha256']
units=[]
def add(u,text,kind,version):
 c=captures[u['capture_key']];sid='govinfo:context144:'+u['unit_key'];source=dict(source_id=sid,source_type=kind,url=c['requested_url'],text_version=version,text=text,raw_sha256=c['raw_response_sha256']);source['governed_bytes_sha256']=sealed_digest(source,'governed_bytes_sha256');sources.append(source)
 u=copy.deepcopy(u);u.pop('text',None);u.update(source_id=sid,source_object_sha256=digest(source),passage_sha256=sha(text.encode()));units.append(u)
for key in ['38usc101','38usc5100','38usc5902']:
 text=(T/(key+'_text.txt')).read_text(encoding='utf8')
 if key=='38usc101':start=text.index('(29)');end=text.index('(30)',start);label='Dated2024Code101(29)Vietnam-era definition only; no whole101/currentlaw claim'
 else:
  section=key.replace('38usc','');start=text.index('§'+section+'.');end=text.index('(Added Pub.' if key=='38usc5100' else '(Pub. L.',start);label='Dated2024Code complete operative'+section+'only; historical notes excluded'
 add(dict(unit_key=key+'_operative',capture_key=key,html_extent=dict(start=start,end=end),complete_selected_operative_extent=True,whole_parent_document_reviewed=False),text[start:end],'official_statutory_text',label)
for unit in read(T/'floor_units.json'):
 add(unit,unit['text'],'official_congressional_record_excerpt','Exact own floor call-up/operative or question/result extent; identified physical pages; adjacent actions excluded')
qa=[]
for item in read(T/'render_inventory.json'):
 key,n=item['capture_key'],item['page'];raw=(T/(key+f'_page{n}.txt')).read_text(encoding='utf8');qa.append(dict(capture_key=key,one_based_pdf_page=n,raw_page_text=raw,raw_page_text_sha256=sha(raw.encode()),normalized_page_text_sha256=sha(normalized_pdf(raw).encode()),rendered_image_sha256=sha(Path(item['image']).read_bytes()),visual_read_completed=True,relevant_extent_only=True))
assert len(qa)==20
write(P/'pdf_pages_review.json',dict(pages=qa,whole_House_parent_PDFs_claimed_read=False,renderer='pdftoppm;2200pixelmax; separate diagnostic files retained locally',diagnostic_errors_observed=False,review_scope='Own exact choice/version chains on selected pages; unrelated adjacent actions are not evidence for these candidates'))
write(P/'source_units.json',dict(base_head=BASE,source_objects=len(sources),retained_source_objects_used_unchanged=16,units=units,raw_response_invocations=7,raw_bytes=sum(c['raw_response_bytes'] for c in captures.values()),successful_document_identities=7,canonical_state_changed=False,source_registered=False,current_law_certified=False))
write(P/'sources.json',dict(capture_date='2026-10-21',capture_method='Sixteen unchanged retained objects plus23explicit selected primary source units; no canonical registration or acceptance',sources=sources))
ha={x['action_id']:x for x in read(H/'authoring.json')['actions']};hc={x['action_id']:x for x in read(H/'generated/shared_action_core.json')['actions']};hm={x['action_id']:x for x in read(H/'membership_review.json')['records']};im={x['action_id']:x for x in read(I/'membership_review.json')['records']};ir={x['action_id']:x for x in read(I/'universe_proposal.json')['candidate_dispositions']}
history=[]
for aid in aids:
 history.append(dict(action_id=aid,existing_Health_candidate_authoring=ha[aid],existing_Health_candidate_core=hc[aid],existing_Health_membership_record=hm[aid],Infrastructure_before_record_sha256=digest(im[aid]),Infrastructure_before_row_sha256=digest(ir[aid]),meaning_previously_accepted=False,Health_artifacts_rewritten=False))
 # Keep each complete historical shared candidate separately to bound file size.
 write(P/('historical_shared_'+aid.replace(':','_')+'.json'),history[-1])
pins={}
for folder,names in [(I,['authoring.json','sources.json','membership_review.json','universe_proposal.json','generated/shared_action_core.json','generated/shared_issue_mapping.json','generated/member_projections.json','generated/compiled_ir.json']),(H,['authoring.json','sources.json','membership_review.json','generated/shared_action_core.json','generated/shared_issue_mapping.json','generated/member_projections.json','generated/compiled_ir.json'])]:
 for name in names:p=folder/name;pins[p.as_posix()]=sha(p.read_bytes().replace(b'\r\n',b'\n'))
write(P/'retained_input_manifest.json',dict(base_head=BASE,cases=aids,retained_objects=retained,preserved_snapshot_files=pins,Health_original_Record_raw_identity_matches=True,existing_Health_candidates_accepted=False,Health_frozen_S2393_one_action_package_changed=False,canonical_state_changed=False))
write(P/'operative_comparison.json',dict(method='Compare complete own Be-it-enacted operative bodies only after casefold and removing nonalphanumeric characters; page boundary marker excluded. Verify literal qualifiers and own action chains separately. Typography/spelling is not substantively repaired.',cases=read(T/'operative_comparison.json'),exact_binding_accepted=False,canonical_binding_changed=False))
print(dict(retained=len(retained),new_units=len(units),source_objects=len(sources),PDF_pages=len(qa),largest_packet_file=max(p.stat().st_size for p in P.iterdir() if p.is_file())))
