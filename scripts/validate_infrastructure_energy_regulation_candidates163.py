"""Validate isolated held163 preparation; never acquire, accept or apply."""
import copy, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT / 'docs/review_packets/infrastructure_batch163_energy_regulation'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
BASE = '65575bf9a045f23c99f07a0750e6560fbd937655'
AUTHORING_SHA = 'b1d86ef06ce1ee6f0481b5d689c23765414ea1546d849cfdda411d74591c9d5f'
PREFLIGHT_SHA = 'd754b48643ff80297b2c0106dd4b50ab7cfa8fce1a8c3cd4fe823fd9edbf363c'
BUNDLE_SHA = 'e96e7a0675e7a94c571e1011754ed29fe2657172276abf0a981dbd0a70dc8d5e'
MANIFEST_SHA = 'b88c17b40ef605c596b3361aa500bc7605016dff4beaab4a28ffa59a1656adb0'
PRESERVATION_SHA = 'd1ce0f76fcc5f51e45e25079aae6a682ff209e2dd67463fec68c65bd983fa12f'
SPECS = [(1,304,1949),(2,23,4593),(2,55,4090),(2,116,6409),(2,137,5587)]
ACTIONS = [f'house:119:{session}:{roll}' for session,roll,bill in SPECS]
PRODUCTS = ['shared_action_core','shared_issue_mapping','member_projections','compiler_input','compiled_ir','readable_candidates']
RAW_LABELS = {'F000477':['Nay','Nay','Nay','Nay','Nay'], 'M001184':['Not Voting','Yea','Yea','Yea','Yea']}
STAGES=['final_passage']*5
DECISIONS=['include','scope_judgment','include','scope_judgment','include']
READY=[False,False,True,False,True]

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def require(value, message):
    if not value:
        raise ValueError(message)

def pin_bytes(path, mode):
    raw = path.read_bytes()
    return raw if mode == 'raw' else raw.replace(b'\r\n',b'\n')

def validate_manifests():
    for name, expected in [('preservation_manifest.json',PRESERVATION_SHA),('packet_manifest.json',MANIFEST_SHA)]:
        manifest = read(P/name)
        require(digest(manifest)==expected, name+' seal changed')
        require(sealed_digest(manifest,'manifest_sha256')==manifest['manifest_sha256'], name+' self seal changed')
        for name, pin in manifest['files'].items():
            raw = pin_bytes(ROOT/name, pin['mode'])
            require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'], 'pinned file changed: '+name)
    preservation = read(P/'preservation_manifest.json')
    require(len(preservation['files'])==715 and preservation['base_commit']==BASE, 'wrong preserved baseline')
    packet = read(P/'packet_manifest.json')
    actual = {p.relative_to(ROOT).as_posix() for p in P.rglob('*') if p.is_file() and p.name not in ['packet_manifest.json','preservation_manifest.json']}
    require(actual==set(packet['files']), 'extra or missing packet files')
    return len(packet['files'])

def inputs():
    return {name:read(P/(name+'.json')) for name in ['authoring','sources','preparation_preflight','decision_bundle']}

def validate_member_neutral(authoring):
    for action in authoring['actions']:
        text=' '.join([action['meaning'],action['short_description'],action['compact_description'],*action['limitations'],*action['choice_meanings'].values()]).casefold()
        require(not any(name in text for name in ['foushee','massie','f000477','m001184']), 'shared meaning contains member-specific status or identity')

def extract_pre(raw):
    from html.parser import HTMLParser
    class Text(HTMLParser):
        def __init__(self): super().__init__(convert_charrefs=True);self.pre=False;self.parts=[]
        def handle_starttag(self,tag,attrs):
            if tag=='pre':self.pre=True
        def handle_endtag(self,tag):
            if tag=='pre':self.pre=False
        def handle_data(self,data):
            if self.pre:self.parts.append(data)
    parser=Text();parser.feed(raw.decode('utf-8'));return ' '.join(''.join(parser.parts).split())

def validate_sources(capture,authoring):
    canonical={s['source_id']:s for s in read(B/'sources.json')['sources']}
    sources={s['source_id']:s for s in capture['sources']}
    require(len(sources)==len(capture['sources'])==18, 'native source pool changed')
    new={f'govinfo:energy163:hr{bill}rh-substitute' for bill in [4090,5587]}
    require(set(sources)-set(canonical)==new, 'unexpected new source entered pool')
    expected=set()
    for action in authoring['actions']:
        expected.add('clerk:'+action['action_id'].split(':',1)[1]);expected.update([action['source_id'],*action['additional_source_ids']])
    require(set(sources)==expected, 'unattributed/missing native source')
    for sid,source in sources.items():
        require(source['governed_bytes_sha256']==sealed_digest(source,'governed_bytes_sha256'), 'governed source seal changed')
        if sid not in new:require(digest(source)==digest(canonical[sid]), 'canonical retained source changed: '+sid)
        else:
            bill=4090 if '4090' in sid else 5587;raw=(P/'captures'/f'hr{bill}rh.html').read_bytes();full=extract_pre(raw);start=full.index('Be it enacted');end=full.rfind('Union Calendar No.')
            require(source['url']==f'https://www.govinfo.gov/content/pkg/BILLS-119hr{bill}rh/html/BILLS-119hr{bill}rh.htm' and hashlib.sha256(raw).hexdigest()==source['raw_sha256'], 'reported source raw/URL changed')
            extent=source['declared_extent']
            require(full.count('Be it enacted')==1 and end>start and extent['start']==start and extent['end']==end and source['text']==full[start:end], 'reported substitute extent changed')
            require(hashlib.sha256(full.encode()).hexdigest()==extent['full_normalized_sha256'] and hashlib.sha256(source['text'].encode()).hexdigest()==extent['selected_sha256'], 'reported extraction hash changed')
            require('Strike out all after the enacting clause and insert the part printed in italic' in full[:start] and 'For text of introduced bill, see copy of bill as introduced' in full[:start], 'reported replacement instruction missing')
    return sources

CHAIN_SPECS={4090:{'rule':1032,'section':3,'rule_roll':52,'mtr_roll':54,'pass_roll':55,'reported_date':'2025-11-25','report':'119-387'},5587:{'rule':1189,'section':4,'rule_roll':131,'mtr_roll':None,'pass_roll':137,'reported_date':'2026-04-15','report':'119-613'}}

def validate_prepared_chain(chain,capture,procedural):
    from datetime import datetime
    require(chain['bill'] in CHAIN_SPECS, 'unknown version-chain subject')
    bill=chain['bill'];spec=CHAIN_SPECS[bill];sources={s['source_id']:s for s in capture['sources']};canonical={s['source_id']:s for s in read(B/'sources.json')['sources']}
    aux={s['source_id']:s for s in procedural['sources']}
    require(set(aux)=={'clerk:119:2:52','clerk:119:2:54','clerk:119:2:131'} and len(procedural['sources'])==3, 'auxiliary role-source set changed')
    for sid,source in aux.items():require(digest(source)==digest(canonical[sid]), 'canonical procedural witness changed')
    available={**sources,**aux};date=lambda value:datetime.strptime(value,'%d-%b-%Y').date()
    final=date(available[f"clerk:119:2:{spec['pass_roll']}"]['metadata']['action-date']);rule_date=date(available[f"clerk:119:2:{spec['rule_roll']}"]['metadata']['action-date']);reported=datetime.fromisoformat(spec['reported_date']).date()
    require(reported<=rule_date<=final, 'reported/rule/final chronology invalid')
    roles={'rule_adoption':(spec['rule_roll'],f"H RES {spec['rule']}",'On Agreeing to the Resolution','Passed'),'final_passage':(spec['pass_roll'],f'H R {bill}','On Passage','Passed')}
    if spec['mtr_roll'] is not None:roles['motion_to_recommit']=(spec['mtr_roll'],f'H R {bill}','On Motion to Recommit','Failed')
    require({w['role'] for w in chain['procedural_witnesses']}==set(roles) and len(chain['procedural_witnesses'])==len(roles), 'unexpected, duplicate or missing procedural role')
    for witness in chain['procedural_witnesses']:
        roll,measure,question,outcome=roles[witness['role']];expected=available[f'clerk:119:2:{roll}'];meta=witness['metadata']
        require(witness['source_id']==expected['source_id'] and witness['governed_source_sha256']==expected['governed_bytes_sha256'] and digest(meta)==digest(expected['metadata']), 'procedural source identity changed')
        require(meta['legis-num']==measure and meta['vote-question']==question and meta['vote-result']==outcome, 'measure/question/outcome does not support procedural role')
        require(date(meta['action-date'])==(rule_date if witness['role']=='rule_adoption' else final), 'procedural date does not support role')
    raw=(P/'captures'/f'hr{bill}rh.html').read_bytes();full=extract_pre(raw);start=full.index('Be it enacted');end=full.rfind('Union Calendar No.');body=full[start:end]
    require(reported.strftime('%B')+f' {reported.day}, {reported.year}' in full[:start] and f"[Report No. {spec['report']}]" in full[:start], 'reported document/date identity changed')
    eh=sources[f'govinfo:hr{bill}eh']['text'];a=eh.index('Be it enacted');b=eh.index('Passed the House of Representatives')
    require(chain['reported_extent']==[start,end] and chain['reported_extent_sha256']==hashlib.sha256(body.encode()).hexdigest() and chain['EH_extent']==[a,b], 'prepared operative extents changed')
    require(chain['complete_operative_match_after_whitespace_only'] is True and re.sub(r'\s+','',body)==re.sub(r'\s+','',eh[a:b]), 'complete RH/EH operative tokens differ')
    require(f"Passed the House of Representatives {final.strftime('%B')} {final.day}, {final.year}." in eh, 'own final date/attestation mismatch')
    rule=sources[f"govinfo:hres{spec['rule']}eh"]['text'];begin=rule.index(f"Sec. {spec['section']}.");finish=rule.index('Attest: Clerk.',begin);unit=rule[begin:finish]
    require(chain['rule']==spec['rule'] and chain['own_rule_section']==spec['section'] and f'H.R. {bill}' in unit and 'amendment in the nature of a substitute recommended by the Committee on Natural Resources now printed in the bill shall be considered as adopted' in unit, 'own rule/substitute link changed')
    if bill==5587:require('Roll2:136is unrelatedHR6387and excluded' in chain['procedural_scope_limit'], 'unrelated adjacent-roll limitation omitted')

def validate_source_extent():
    extent=read(P/'source_extent_receipt.json');receipt=read(P/'capture_receipt.json');total=0
    require(extent['native_sources']==18 and extent['unchanged_native_objects']==16 and extent['new_RH_objects']==2 and extent['auxiliary_unchanged_procedural_objects']==3 and extent['unique_governed_evidence_objects']==21, 'source extent accounting changed')
    require(extent['canonical_binding_cleared'] is False and extent['source_holds_changed'] is False and extent['canonical_source_registration'] is False, 'source authority changed')
    require(extent['material_6291_scope']=='Retained(1)–(7), not old(31)(D)or unretainedASME2024definition.', 'unretained definition/standard scope changed')
    require(len(receipt['attempts'])==2 and receipt['limits']=={'URLs':2,'attempts_per_exact_URL':1,'seconds_per_attempt':45,'response_bytes':1048576,'total_response_bytes':2097152,'redirects':False,'PDFs':False,'alternative_route_retries':False}, 'prospective capture bounds changed')
    require([x['bill'] for x in receipt['attempts']]==[4090,5587], 'unexpected capture subject')
    for cap in receipt['attempts']:
        require(cap['retained'] is True and cap['attempts']==1 and cap['status']==200 and cap['elapsed_seconds']<=45, 'capture attempt/redirect/time drift')
        raw=(P/'captures'/f"hr{cap['bill']}rh.html").read_bytes();total+=len(raw)
        require(len(raw)==cap['raw_bytes']<=1048576 and hashlib.sha256(raw).hexdigest()==cap['raw_sha256'], 'captured raw body changed')
        require(cap['url']==f"https://www.govinfo.gov/content/pkg/BILLS-119hr{cap['bill']}rh/html/BILLS-119hr{cap['bill']}rh.htm", 'capture URL changed')
    require(total==receipt['total_successful_body_bytes']==extent['new_raw_bytes']==19262 and total<=2097152, 'capture total changed')

def validate_preflight(pre):
    require(digest(pre)==PREFLIGHT_SHA, 'preflight subject/scope drift')
    require(pre['base_commit']==BASE and pre['accepted'] is False and pre['canonical_changes'] is False, 'preflight authority changed')
    for name,key in [('membership_review.json','membership_sha256'),('universe_proposal.json','universe_sha256'),('sources.json','source_pool_sha256')]:
        require(digest(read(B/name))==pre[key], 'canonical154 changed')
    prior=set(pre['prior_prepared_identities'])
    require(len(prior)==68 and not prior.intersection(ACTIONS), 'duplicate prior preparation')
    require(len(pre['all_existing_shared_core_checks'])==153, 'typed core inventory changed')
    for pin in pre['all_existing_shared_core_checks']:
        core=read(ROOT/pin['path'])
        require(digest(core)==pin['object_sha256'], 'existing shared core changed')
        require(not set(ACTIONS).intersection(a['action_id'] for a in core['actions']), 'existing meaning would be reauthored')
    for i,case in enumerate(pre['cases']):
        require(case['action_id']==ACTIONS[i], 'wrong exact case')
        r=case['record']; require(r['disposition']=='pending_interpretation', 'case is not pending')
        require(r['exact_action_binding_unresolved'] is True, 'canonical binding flag changed')
        require(r['required_evidence_unavailable'] is False and r['authoritative_source_conflict'] is False, 'evidence/conflict state changed')
        require(digest(r)==case['record_sha256'] and digest(case['row'])==case['row_sha256'], 'canonical preimage drift')

def queue_accounting(pre):
    records=read(B/'membership_review.json')['records']
    pending={r['action_id'] for r in records if r['disposition']=='pending_interpretation'}
    prepared=set(pre['prior_prepared_identities'])|set(ACTIONS)
    remaining=pending-prepared
    result={'canonical_records':len(records),'canonical_pending':len(pending),
            'prepared_total':len(prepared),'prepared_pending':len(prepared&pending),
            'prepared_not_pending':len(prepared-pending),'not_prepared':len(remaining),
            'unresolved_among_not_prepared':sum(r['action_id'] in remaining and r['exact_action_binding_unresolved'] is True for r in records),
            'canonical_source_holds':sum(r['disposition']=='source_unresolved' for r in records)}
    require(result=={'canonical_records':676,'canonical_pending':246,'prepared_total':73,'prepared_pending':71,'prepared_not_pending':2,'not_prepared':175,'unresolved_among_not_prepared':159,'canonical_source_holds':6},'actual operational queue changed')
    return result

def validate_prior_branch(index, authoring, core):
    pin=read(P/'preparation_preflight.json')['prior_non_main_identity_pins'][index]
    require(digest(authoring)==pin['authoring']['object_sha256'] and digest(core)==pin['core']['object_sha256'], 'immutable prior identity payload changed')
    ids={a['action_id']for a in authoring['actions']}
    require(len(ids)==5 and ids=={a['action_id']for a in core['actions']} and not ids.intersection(ACTIONS), 'prior/new identity overlap')
    return len(ids)

def validate_binding_readiness(bundle, evidence=None, capture=None, procedural=None):
    evidence=read(P/'proposed_bindings.json') if evidence is None else evidence
    capture=read(P/'sources.json') if capture is None else capture
    procedural=read(P/'procedural_witnesses.json') if procedural is None else procedural
    require(evidence['auxiliary_procedural_witnesses_sha256']==digest(procedural), 'procedural witnesses changed')
    require(evidence['procedural_history_complete'] is False and evidence['binding_accepted_or_applied'] is False and evidence['canonical_changes'] is False, 'binding evidence claims acceptance or exhaustive history')
    require([c['bill'] for c in evidence['prepared_chains']]==[4090,5587], 'wrong prepared chain subjects')
    for artifact in [bundle,evidence]:
        require([x['action_id'] for x in artifact['cases']]==ACTIONS, 'binding evidence subjects changed')
        for i,case in enumerate(artifact['cases']):
            state='prepared_reported_rule_EH_chain_pending_approval' if READY[i] else 'pending_exact_version_reconciliation'
            require(case['binding_approval_requested'] is READY[i] and case['binding_review_ready'] is READY[i] and case['binding_evidence_state']==state and case['binding_applied'] is False, 'binding readiness does not match available evidence')
            require(bool(case['binding_evidence_reason']), 'binding evidence reason omitted')
    for chain in evidence['prepared_chains']: validate_prepared_chain(chain,capture,procedural)

def validate(data=None):
    data=inputs() if data is None else data
    a=data['authoring']; pre=data['preparation_preflight']; bundle=data['decision_bundle']
    validate_member_neutral(a)
    require(digest(a)==AUTHORING_SHA, 'held meaning/qualification/source scope changed')
    require(digest(bundle)==BUNDLE_SHA, 'held decision bundle changed')
    validate_preflight(pre); sources=validate_sources(data['sources'],a)
    require([x['action_id']for x in a['actions']]==ACTIONS, 'selected action list changed')
    for i,((session,roll,bill),action) in enumerate(zip(SPECS,a['actions'])):
        require(action['stage']==STAGES[i] and action['bill_number']==bill, 'exact stage/measure changed')
        require(action['episode_id'] in a['blocked_episode_ids'], 'candidate hold removed')
        require(set(x['source_id']for x in action['claim_source_map'])==set(action['compact_source_refs']), 'claim/source coverage differs')
    require(sealed_digest(bundle,'bundle_sha256')==bundle['bundle_sha256'] and bundle['authoring_sha256']==digest(a) and bundle['sources_sha256']==digest(data['sources']), 'decision subjects changed')
    require(all(bundle[k] is False for k in ['accepted','canonical_application','publication','production']), 'decision authority changed')
    for i,case in enumerate(bundle['cases']):
        require(case['action_id']==ACTIONS[i] and case['proposed_eligibility']==DECISIONS[i], 'scope decision changed')
        require(case['binding_approval_requested'] is READY[i] and case['binding_review_ready'] is READY[i] and case['canonical_binding_already_resolved'] is False, 'binding request changed')
        require(all(case[k] is False for k in ['binding_applied','meaning_accepted','eligibility_applied','canonical_sources_registered','source_holds_changed']), 'case accepted/applied')
    validate_binding_readiness(bundle,capture=data['sources'])
    core,mapping,projections,compiler_input,result=prepare(a,data['sources'],['F000477','M001184'])
    require([x['action_id'] for x in bundle['cases']]==ACTIONS, 'missing or extra decision case')
    for i,case in enumerate(bundle['cases']):
        require(case['meaning_ref']==core['actions'][i]['action_meaning_ref'] and case['candidate_core_sha256']==core['actions'][i]['action_core_sha256'], 'decision points to wrong candidate core')
    generated=dict(zip(PRODUCTS,[core,mapping,projections,compiler_input,result.compiled_ir,readable_candidates(a,core,projections,result)]))
    for name,obj in generated.items(): require(digest(obj)==digest(read(P/'generated'/(name+'.json'))), 'native product drift: '+name)
    for projection in projections:
        require([x['official_status']for x in projection['actions']]==RAW_LABELS[projection['member_id']], 'official member status changed')
    for member in result.compiled_ir['members']:
        require(member['proposition_graph']['propositions']==[] and len(member['action_accounting']['non_proposition_reasons'])==5, 'held interpretation escaped')
        require(member['coverage']['directional_yes_no_positions']==(5 if member['member_id']=='F000477' else 4) and member['coverage']['not_voting_actions']==(0 if member['member_id']=='F000477' else 1) and member['coverage']['present_actions']==0 and member['coverage']['missing_evidence_actions']==0, 'member accounting changed')
    return {'sources':len(sources),'auxiliary_procedural_objects':3,'unique_governed_evidence_objects':21,'prepared_binding_proposals':sum(READY),'deferred_binding_cases':len(READY)-sum(READY),'shared_cores':5,'official_observations':10,'held_contexts':5,'propositions':0,'accepted_or_applied':False,'operational_queue_after_preparation':queue_accounting(pre)}

def main():
    packet_files=validate_manifests(); validate_source_extent(); result=validate()
    print(json.dumps({'preserved_files':715,'packet_files':packet_files,**result},indent=2))

if __name__=='__main__': main()
