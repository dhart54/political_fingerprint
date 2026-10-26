"""Offline held153 source, shared-successor and decision-inventory checks."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest,sealed_digest,validate_shared_action_core,validate_shared_issue_mapping,validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare,readable_candidates
from scripts.validate_infrastructure_water_resource_candidates152 import compare_operative

P=ROOT/'docs/review_packets/infrastructure_batch153_energy_governance'
BASE=ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch149_20260916'
HEALTH=ROOT/'docs/editorial/shared_candidates/house_119_health_20260916'
INVENTORY=ROOT/'docs/review_packets/infrastructure_prepared_held_decisions153.json'
ACTIONS=['house:119:1:'+str(n) for n in [73,229,231,236,279]]
MEMBERS=['F000477','M001184']
PRODUCTS=['shared_action_core','shared_issue_mapping','member_projections','compiler_input','compiled_ir','readable_candidates']
MANIFEST_SHA='4ed3a60181aec27a68ebcf458479273d5e71b2bf6260049181d1c994697ab630'
PRESERVATION_SHA='0b2deaf2e3e45b27ecc369023a772c43430c0ec2bd207fb2098c803ba908bf81'
INVENTORY_SHA='f489dd32a7610fa7934f7224a8c0405b4d5caf497c616a4e0f60a718a533d42a'


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def require(value,message):
    if not value:raise ValueError(message)
def same(a,b):return digest(a)==digest(b)


def files_manifest(name,expected,packet):
    m=read(P/name);require(digest(m)==expected and m['manifest_sha256']==sealed_digest(m,'manifest_sha256'),'Frozen manifest changed')
    for name,e in m['files'].items():
        path=(ROOT/name).resolve();require(path.is_relative_to((P if packet else ROOT).resolve()),'Manifest path escaped')
        raw=path.read_bytes()
        if e['mode']=='lf':raw=raw.replace(b'\r\n',b'\n')
        require(len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'],'Frozen bytes differ: '+name)
    return len(m['files'])


def validate_manifest():return files_manifest('packet_manifest.json',MANIFEST_SHA,True)
def validate_preservation():return files_manifest('preservation_manifest.json',PRESERVATION_SHA,False)


def inputs():
    return {**{k:read(P/n) for k,n in dict(authoring='authoring.json',sources='sources.json',preflight='preparation_preflight.json',bundle='decision_bundle.json',capture='capture_receipt.json',conformance='1047_version_conformance.json',reuse='reused_qualified236_core.json',questions='source_questions.json',proof='held_replay_proof.json').items()},'inventory':read(INVENTORY),'products':{n:read(P/'generated'/(n+'.json')) for n in PRODUCTS}}


def replay(a,s):
    c,m,p,i,r=prepare(a,s,MEMBERS)
    return dict(shared_action_core=c,shared_issue_mapping=m,member_projections=p,compiler_input=i,compiled_ir=r.compiled_ir,readable_candidates=readable_candidates(a,c,p,r))


def validate_inventory(inv=None):
    inv=read(INVENTORY) if inv is None else inv
    require(digest(inv)==INVENTORY_SHA and inv['inventory_sha256']==sealed_digest(inv,'inventory_sha256'),'Pinned23-case inventory changed')
    require(inv['prepared_held_cases']==23 and inv['remaining_not_prepared_cases']==225 and inv['total_pending_canonical_cases']==248,'Prepared versus unfinished scope changed')
    require(same(inv['eligibility_proposal_counts'],dict(proposed_inclusion=18,proposed_exclusion=3,scope_judgment_required=2)),'Case recommendation totals changed')
    require(all(inv[k] is False for k in ['decisions_applied','canonical_changes','source_registration','publication','production']),'Inventory acquired authority')
    records={r['action_id']:r for r in read(BASE/'membership_review.json')['records']}
    for pins in inv['artifact_pins'].values():
        for pin in pins.values():
            raw=(ROOT/pin['path']).read_bytes().replace(b'\r\n',b'\n')
            require(hashlib.sha256(raw).hexdigest()==pin['raw_sha256'] and digest(read(ROOT/pin['path']))==pin['object_sha256'],'Pinned historical decision artifact changed')
    require(len({c['action_id'] for c in inv['cases']})==23,'Inventory duplicated/omitted case')
    for c in inv['cases']:
        require(digest(records[c['action_id']])==c['current_record_sha256'] and records[c['action_id']]['disposition']=='pending_interpretation','Inventory canonical preimage changed')
        require(records[c['action_id']]['exact_action_binding_unresolved'] is c['binding']['canonical_unresolved'],'Binding state changed')
        require(all(c[k] is False for k in ['meaning_accepted','eligibility_applied','binding_applied']),'Inventory case acquired authority')
        if c['batch'] in [151,152] and c['binding']['canonical_unresolved']:
            require(c['binding']['original_binding_approval_requested'] is False and c['binding']['state']=='held_evidence_not_requested','Conformance silently became a request')
    return 23


def validate_capture(c):
    require(same(c,read(P/'capture_receipt.json')),'Capture attempt/envelope drift')
    require(same(c['prospective_limits'],dict(locators=15,seconds_per_invocation=45,bytes_per_response=4194304,total_raw_bytes=16777216)),'Capture caps changed')
    require(len(c['captures'])==len({x['requested_url'] for x in c['captures']})==2 and c['retries']==0,'Duplicate, omitted or retried capture')
    total=0
    for x in c['captures']:
        path=(ROOT/x['raw_path']).resolve();require(path.is_relative_to((P/'raw').resolve()),'Capture escaped')
        raw=path.read_bytes();total+=len(raw)
        require(len(raw)==x['retained_bytes']<=4194304 and hashlib.sha256(raw).hexdigest()==x['raw_sha256'],'Raw capture changed')
        require(x['identity_accepted'] is True and x['status']==200 and x['requested_url']==x['final_url'] and not x['redirects'] and not x.get('error'),'Capture identity/route changed')
    require(total==c['total_retained_raw_bytes']==688639 and c['canonical_registration'] is c['editorial_acceptance'] is False,'Capture accounting/authority changed')
    return dict(invocations=2,raw_bytes=total,retries=0)


def validate_versions(pool,conformance,capture=None):
    from pypdf import PdfReader,__version__
    require(__version__=='6.10.0','Use pinned pypdf6.10.0 extraction')
    c=read(P/'capture_receipt.json') if capture is None else capture;texts={};pages={}
    for row in c['captures']:
        ps=[p.extract_text() for p in PdfReader(ROOT/row['raw_path']).pages];full='\n\n'.join(ps);name=row['name'];pages[name]=ps;texts[name]=full
        require(len(ps)==row['PDF_pages'] and hashlib.sha256(full.encode()).hexdigest()==row['PDF_text_utf8_sha256'] and (P/'extracted'/(name+'.txt')).read_text(encoding='utf-8')==full,'Complete PDF extraction changed')
    r=conformance;require(r['receipt_sha256']==sealed_digest(r,'receipt_sha256') and r['binding_approved_or_applied'] is False and r['canonical_binding_already_resolved'] is True,'Conformance acquired authority')
    cleaned=[];transforms=[]
    for i,page in enumerate(pages['1047-RCP119-9']):
        start=page.index('SECTION 1.') if i==0 else page.index('\n')+1;end=page.index('September 11, 2025 (1:10 p.m.)');body=page[start:end].replace('◊','');lines=[];counter=1
        for line in body.splitlines():
            if line.strip():
                m=re.search(r'(\d{1,2})\s*$',line);require(bool(m) and int(m[1])==counter,'Printed line-number sequence changed')
                transforms.append(dict(page=i+1,line=line,removed_printed_line_number=counter));line=line[:m.start()];counter+=1
            lines.append(line)
        cleaned.append('\n'.join(lines))
    eh=pool['govinfo:hr1047eh']['text'];body=eh[eh.index('SECTION 1.'):eh.index('Passed the House')];g,hy=compare_operative(body,'\n\n'.join(cleaned))
    require(transforms==r['RCP_printed_line_number_removals'] and hy==r['RCP_line_wrap_hyphens'] and hashlib.sha256(g.encode()).hexdigest()==r['RCP_comparison_sha256'],'RCP comparison receipt drift')
    require(pool['house-rules:energy153:RCP119-9']['text']==texts['1047-RCP119-9'],'Governed RCP text changed')
    full=texts['1047-House-2025-09-18'];units={u['role']:full[u['start']:u['end']] for u in r['selected_units']}
    require(pool['govinfo:energy153:1047-own-floor']['text']=='\n\n'.join(units.values()),'Own floor unit selection changed')
    for u in r['selected_units']:require(hashlib.sha256(units[u['role']].encode()).hexdigest()==u['utf8_sha256'],'Floor extent changed')
    g,hy=compare_operative(eh[eh.index('Be it enacted'):eh.index('Passed the House')],units['complete_printed_operative_body'])
    require(hy==r['floor_line_wrap_hyphens'] and hashlib.sha256(g.encode()).hexdigest()==r['floor_comparison_sha256'],'Own floor/EH comparison drift')
    clause=pool['govinfo:hres707eh']['text'];require('Rules Committee Print 119-9 shall be considered as adopted' in clause and 'H.R. 1047' in clause,'Deemed substitute identity lost')
    call=' '.join(units['own_callup_and_RCP_adoption'].split());question=' '.join(units['resumed_recorded_question_and_roll'].split());result=' '.join(units['recorded_passage_result'].split())
    require('119–9 is adopted' in call and '1047' in call and '[Roll No. 279]' in question and '216, nays 206, not voting 9' in question,'Wrong own recorded choice')
    require('So the bill was passed.' in result and 'result of the vote' in result,'Wrong final passage outcome')
    return dict(RCP_complete=True,own_floor_complete_operative=True,recorded_passage=True)


def validate_qualifications(a):
    terms={73:['enumerated coordination activities are optional','competitive, merit-reviewed','within two years','no new appropriation'],229:['entire $350million','$40million OF THAT AMOUNT','does not delete','legal','rejected this exact amendment77–347'],231:['general-fund','up to $35million','already estimated at zero','legal availability','$150million','COSTS','no more than3percent','rejected amendment27 by120–306'],236:['OF THE SAME SUM','not a $2.053billion','no Spending Reduction Account','prior balances','rejected this exact amendment127–297'],279:['within90days','within180days','within60days','reliability AND resource adequacy','reliability OR grid resilience','if necessary','not an automatic queue jump']}
    for x in a['actions']:
        for key in ['meaning','compact_description']:
            for term in terms[int(x['action_id'].split(':')[-1])]:require(term in x[key],'Material operator/qualification omitted: '+term)


def validate(d=None):
    d=inputs() if d is None else d;m=read(P/'packet_manifest.json');require(digest(m)==MANIFEST_SHA,'Frozen packet changed')
    names=dict(authoring='authoring.json',sources='sources.json',preflight='preparation_preflight.json',bundle='decision_bundle.json',capture='capture_receipt.json',conformance='1047_version_conformance.json',reuse='reused_qualified236_core.json',questions='source_questions.json',proof='held_replay_proof.json')
    for k,n in names.items():require(digest(d[k])==m['object_sha256'][n],'Frozen input changed: '+k)
    a,s,pre,b=(d[k] for k in ['authoring','sources','preflight','bundle']);membership=read(BASE/'membership_review.json');universe=read(BASE/'universe_proposal.json');old=read(BASE/'sources.json')
    require(pre['preflight_sha256']==sealed_digest(pre,'preflight_sha256') and pre['base_commit']=='f91fad3b6f345d63a56e17b5b092949bd7b7fe96','Preflight/base changed')
    require(membership['review_sha256']==pre['membership_seal'] and universe['proposal_sha256']==pre['universe_seal'] and digest(old)==pre['source_pool_sha256'],'Canonical149 changed')
    records={x['action_id']:x for x in membership['records']};rows={x['action_id']:x for x in universe['candidate_dispositions']};pool={x['source_id']:x for x in s['sources']};op={x['source_id']:x for x in old['sources']};hp={x['source_id']:x for x in read(HEALTH/'sources.json')['sources']}
    require(len(pool)==len(s['sources'])==32,'Source inventory changed')
    for x in read(P/'retained_sources.json')['sources']:require(same(x,pool[x['source_id']]) and same(x,op[x['source_id']]),'Original27 object changed')
    for e in read(P/'additional_preserved_sources.json')['sources']:
        x=e['source'];origin=op if e['origin']=='current149' else hp;require(digest(x)==e['object_sha256'] and same(x,origin[x['source_id']]) and same(x,pool[x['source_id']]),'Additional existing witness changed')
    reuse=d['reuse'];hc=read(HEALTH/'generated/shared_action_core.json');previous=next(x for x in hc['actions'] if x['action_id']=='house:119:1:236')
    require(digest(hc)==reuse['origin_core_object_sha256'] and same(previous,reuse['original236']) and digest(previous)==reuse['original236_object_sha256'],'Original qualified Health236 core changed')
    require([x['action_id'] for x in a['actions']]==[x['action_id'] for x in b['cases']]==[x['action_id'] for x in pre['cases']]==ACTIONS,'Case correspondence changed')
    require(a['blocked_episode_ids']==['episode:hr1326:119','episode:hr4553:119','episode:hr1047:119'],'Episode hold removed')
    for c,x,v in zip(pre['cases'],a['actions'],b['cases']):
        aid=c['action_id'];require(same(records[aid],c['record']) and same(rows[aid],c['row']) and digest(records[aid])==c['before_record_sha256'] and digest(rows[aid])==c['before_row_sha256'],'Current record/row preimage changed')
        require(records[aid]['disposition']=='pending_interpretation' and records[aid]['exact_action_binding_unresolved'] is records[aid]['required_evidence_unavailable'] is records[aid]['authoritative_source_conflict'] is False,'Canonical flags changed')
        require(v['canonical_binding_already_resolved'] is True and all(v[k] is False for k in ['binding_approval_requested','binding_applied','meaning_accepted','eligibility_applied','canonical_sources_registered','source_holds_changed']),'Decision acquired authority')
    require(b['bundle_sha256']==sealed_digest(b,'bundle_sha256') and all(b[k] is False for k in ['accepted','canonical_application','publication','production']),'Bundle acquired authority')
    validate_qualifications(a);version=validate_versions(pool,d['conformance'],d['capture']);actual=d['products'];require(same(actual,replay(a,s)),'Native held replay differs')
    core=actual['shared_action_core'];validate_shared_action_core(ROOT,core);validate_shared_issue_mapping(ROOT,actual['shared_issue_mapping'],core)
    for v,x in zip(b['cases'],core['actions']):require(v['candidate_core_sha256']==x['action_core_sha256'] and v['meaning_ref']==x['action_meaning_ref'],'Decision subject changed')
    for p in actual['member_projections']:
        validate_member_projection(ROOT,p,core);expected=['Yea','Nay','Nay','Nay','Nay'] if p['member_id']=='F000477' else ['Nay','Yea','Yea','Yea','Yea'];require([x['official_status'] for x in p['actions']]==expected,'Official labels changed')
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),'Held action generated proposition')
    require(d['proof']['product_sha256']=={k:digest(v) for k,v in actual.items()} and d['proof']['behavioral_update_proof_exercised'] is False,'Replay proof overclaims')
    return dict(cores=5,official_observations=10,sources=32,held_episodes=3,issue_propositions=0,canonical149_changed=False,binding_or_meaning_accepted=False,version=version,capture=validate_capture(d['capture']),prior_held_decisions=validate_inventory(d['inventory']))


if __name__=='__main__':print(json.dumps(dict(preserved_files=validate_preservation(),packet_files=validate_manifest(),validation=validate()),indent=2))
