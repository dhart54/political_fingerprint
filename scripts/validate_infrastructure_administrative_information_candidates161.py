"""Validate isolated held161 preparation; never acquire, accept or apply."""
import copy, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT / 'docs/review_packets/infrastructure_batch161_administrative_information'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
BASE = '65575bf9a045f23c99f07a0750e6560fbd937655'
AUTHORING_SHA = '5a931e2e22daa7e8894ed0febd0202b77956746597c151f7e07cc03a89ac1d22'
PREFLIGHT_SHA = '57b03de75f76df9f92f2783de61e39f02d0f7107b68389faae6ce6fddc505ac4'
BUNDLE_SHA = '8f83395dd32e416e0e64cbd5ebb1957f8ba0730ec2ef5d20e20d9e4e45ca3639'
MANIFEST_SHA = '42cbfd7dc8ae4af6dd980b1780aae27ee27d8c9ddf8365ebb5f82d0bc5174d76'
PRESERVATION_SHA = '4b563fa74acca10c647ce14b568dae80be14ef4326b4fdbdf43ca8c56f757971'
SPECS = [(84,517),(85,997),(213,3095),(214,3351),(301,6019)]
ACTIONS = [f'house:119:1:{roll}' for roll, bill in SPECS]
PRODUCTS = ['shared_action_core','shared_issue_mapping','member_projections','compiler_input','compiled_ir','readable_candidates']
RAW_LABELS = {'F000477':['Yea','Yea','Nay','Yea','Yea'], 'M001184':['Yea','Yea','Yea','Nay','Yea']}

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

def comparable(text):
    return re.sub(r'\s+','',re.sub(r'\[\[Page[^\]]+\]\]','',text))

def validate_sources(capture, authoring):
    canonical = {s['source_id']:s for s in read(B/'sources.json')['sources']}
    sources = {s['source_id']:s for s in capture['sources']}
    require(len(sources)==len(capture['sources'])==18, 'source pool changed')
    new = {f'govinfo:admin161:hr{bill}-offering' for roll,bill in SPECS if bill!=6019}
    require(set(sources)-set(canonical)==new, 'unregistered or unexpected source entered pool')
    for sid,s in sources.items():
        require(s['governed_bytes_sha256']==sealed_digest(s,'governed_bytes_sha256'), 'governed source seal changed')
        if sid not in new:
            require(digest(s)==digest(canonical[sid]), 'canonical retained source changed: '+sid)
    for action in authoring['actions']:
        bill = action['bill_number']
        if bill==6019:
            continue
        source = sources[f'govinfo:admin161:hr{bill}-offering']
        raw = (P/'captures'/f'hr{bill}-offering.html').read_bytes()
        require(hashlib.sha256(raw).hexdigest()==source['raw_sha256'], 'offering raw changed')
        # Reproduce the declared HTML PRE extraction, without rewriting source bytes.
        from html.parser import HTMLParser
        class Extract(HTMLParser):
            def __init__(self): super().__init__(convert_charrefs=True); self.pre=False; self.parts=[]
            def handle_starttag(self, tag, attrs):
                if tag=='pre': self.pre=True
            def handle_endtag(self, tag):
                if tag=='pre': self.pre=False
            def handle_data(self,data):
                if self.pre: self.parts.append(data)
        parser=Extract(); parser.feed(raw.decode('utf-8'))
        require(' '.join(''.join(parser.parts).split())==source['text'], 'offering extraction changed')
        text=source['text']; start=text.index('Be it enacted'); end=text.index('The SPEAKER pro tempore.',start)
        eh=sources[f'govinfo:hr{bill}eh']['text']; eh=eh[eh.index('Be it enacted'):eh.index('Passed the House of Representatives')]
        require(comparable(text[start:end])==comparable(eh), 'complete offered text differs from EH')
        require(f'H.R. {bill}' in text[:start] and 'as amended' in text[:start], 'own amended motion missing')
        require(f'H.R. {bill}, as amended' in text[end:] and 'further proceedings on this motion will be postponed' in text[end:], 'own postponed question missing')
        claims=[x for x in action['claim_source_map'] if x['source_id']==source['source_id']]
        require(len(claims)==2 and claims[0]['passage']==text[:end], 'initial offered-text passage changed')
        require(claims[0]['locator']=='Opening amended motion and complete printed operative unit; final question/postponement mapped separately. Debate claims are not adopted.', 'initial locator overstates its passage')
        require(f'H.R. {bill}, as amended' in claims[1]['passage'] and 'further proceedings on this motion will be postponed' in claims[1]['passage'], 'separate final question/postponement missing')
        if bill==3095:
            require('Mr. COMER.' in text[:start] and 'Ms. Boebert' in claims[1]['passage'], 'literal mover attribution changed')
            require(any('Literal Comer/Boebert mover discrepancy' in limit for limit in action['limitations']), 'literal mover discrepancy omitted')
    return sources

def validate_capture():
    metadata=read(P/'corrected_metadata_receipt.json'); failed=read(P/'metadata_receipt.json'); offering=read(P/'offering_receipt.json')
    require(len(failed['attempts'])==2 and all(a.get('route_closed') is True and a['retained'] is False and '404' in a['error'] for a in failed['attempts']), 'failed locator route reopened')
    total=0
    for a in metadata['attempts']:
        require(a['retained'] is True and a['attempts']==1 and a['status']==200 and a['elapsed_seconds']<=45, 'metadata acquisition drift')
        raw=(P/'captures'/a['path']).read_bytes()
        require(len(raw)==a['read_bytes']<=2*1024*1024 and hashlib.sha256(raw).hexdigest()==a['sha256'], 'metadata raw changed')
        total+=len(raw)
    require(len(metadata['attempts'])==2 and len(offering['attempts'])==4, 'acquisition cap/count drift')
    for a in offering['attempts']:
        require(a['retained'] is True and a['attempts']==1 and a['status']==200 and a['elapsed_seconds']<=45, 'offering acquisition drift')
        raw=(P/'captures'/f"hr{a['bill']}-offering.html").read_bytes()
        require(len(raw)==a['raw_bytes']<=1024*1024 and hashlib.sha256(raw).hexdigest()==a['raw_sha256'], 'offering capture changed')
        require(any(a['url'] in item['text'] for attempt in metadata['attempts'] for item in attempt['selected_metadata_items']), 'offering URL not linked by metadata')
        total+=len(raw)
    require(total==4018503==offering['total_body_bytes'] and total<=8*1024*1024, 'total response scope changed')

def validate_preflight(pre):
    require(digest(pre)==PREFLIGHT_SHA, 'preflight subject/scope drift')
    require(pre['base_commit']==BASE and pre['accepted'] is False and pre['canonical_changes'] is False, 'preflight authority changed')
    for name,key in [('membership_review.json','membership_sha256'),('universe_proposal.json','universe_sha256'),('sources.json','source_pool_sha256')]:
        require(digest(read(B/name))==pre[key], 'canonical154 changed')
    prior=set(pre['prior_prepared_identities'])
    require(len(prior)==58 and not prior.intersection(ACTIONS), 'duplicate prior preparation')
    require(len(pre['all_existing_shared_core_checks'])==153, 'typed core inventory changed')
    for pin in pre['all_existing_shared_core_checks']:
        core=read(ROOT/pin['path'])
        require(digest(core)==pin['object_sha256'], 'existing shared core changed')
        require(not set(ACTIONS).intersection(a['action_id'] for a in core['actions']), 'existing meaning would be reauthored')
    for i,case in enumerate(pre['cases']):
        require(case['action_id']==ACTIONS[i], 'wrong exact case')
        r=case['record']; require(r['disposition']=='pending_interpretation', 'case is not pending')
        require(r['exact_action_binding_unresolved'] is (i!=4), 'canonical binding flag changed')
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
    require(result=={'canonical_records':676,'canonical_pending':246,'prepared_total':63,'prepared_pending':61,'prepared_not_pending':2,'not_prepared':185,'unresolved_among_not_prepared':169,'canonical_source_holds':6},'actual operational queue changed')
    return result

def validate_prior_branch(index, authoring, core):
    pin=read(P/'preparation_preflight.json')['prior_non_main_identity_pins'][index]
    require(digest(authoring)==pin['authoring']['object_sha256'] and digest(core)==pin['core']['object_sha256'], 'immutable prior identity payload changed')
    ids={a['action_id']for a in authoring['actions']}
    require(len(ids)==5 and ids=={a['action_id']for a in core['actions']} and not ids.intersection(ACTIONS), 'prior/new identity overlap')
    return len(ids)

def validate(data=None):
    data=inputs() if data is None else data
    a=data['authoring']; pre=data['preparation_preflight']; bundle=data['decision_bundle']
    require(digest(a)==AUTHORING_SHA, 'held meaning/qualification/source scope changed')
    require(digest(bundle)==BUNDLE_SHA, 'held decision bundle changed')
    validate_preflight(pre); sources=validate_sources(data['sources'],a)
    require([x['action_id']for x in a['actions']]==ACTIONS, 'selected action list changed')
    for (roll,bill),action in zip(SPECS,a['actions']):
        require(action['stage']=='suspension_and_passage' and action['bill_number']==bill, 'exact stage/measure changed')
        require(action['episode_id'] in a['blocked_episode_ids'], 'candidate hold removed')
        require(set(x['source_id']for x in action['claim_source_map'])==set(action['compact_source_refs']), 'claim/source coverage differs')
    require(sealed_digest(bundle,'bundle_sha256')==bundle['bundle_sha256'] and bundle['authoring_sha256']==digest(a) and bundle['sources_sha256']==digest(data['sources']), 'decision subjects changed')
    require(all(bundle[k] is False for k in ['accepted','canonical_application','publication','production']), 'decision authority changed')
    for i,case in enumerate(bundle['cases']):
        require(case['action_id']==ACTIONS[i] and case['proposed_eligibility']=='scope_judgment', 'scope decision changed')
        require(case['binding_approval_requested'] is (i!=4) and case['canonical_binding_already_resolved'] is (i==4), 'binding request changed')
        require(all(case[k] is False for k in ['binding_applied','meaning_accepted','eligibility_applied','canonical_sources_registered','source_holds_changed']), 'case accepted/applied')
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
        require(member['coverage']['directional_yes_no_positions']==5 and member['coverage']['not_voting_actions']==0 and member['coverage']['present_actions']==0, 'member accounting changed')
    return {'sources':len(sources),'shared_cores':5,'official_observations':10,'held_contexts':5,'propositions':0,'accepted_or_applied':False,'operational_queue_after_preparation':queue_accounting(pre)}

def main():
    packet_files=validate_manifests(); validate_capture(); result=validate()
    print(json.dumps({'preserved_files':715,'packet_files':packet_files,**result},indent=2))

if __name__=='__main__': main()
