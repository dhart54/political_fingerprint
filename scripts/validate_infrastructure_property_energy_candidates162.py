"""Validate isolated held162 preparation; never acquire, accept or apply."""
import copy, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT / 'docs/review_packets/infrastructure_batch162_property_energy_governance'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
BASE = '65575bf9a045f23c99f07a0750e6560fbd937655'
AUTHORING_SHA = '5343c78865567acaf3b65a8562f99baeeb4c90cf448e4b27889c938c1b90671d'
PREFLIGHT_SHA = '15597f7dcd21ef881190fb5eb9812cbc0053eb0b07dd5619b6949157cfbc1def'
BUNDLE_SHA = 'c8aeace55a92886cb6d8741800e2d13771b416970a252cecdb3a9234efca0fdb'
MANIFEST_SHA = 'c8cd359eea7824316f7922dbf20bcc13c19c8ad0765fd6ca6030a038ab1eb3ef'
PRESERVATION_SHA = 'bf7672527cb5066832fa432e2d3a1764d33360aee81d3bc019622d8234ad872c'
SPECS = [(215,3937),(240,3424),(278,3015),(324,3638),(336,3187)]
ACTIONS = [f'house:119:1:{roll}' for roll, bill in SPECS]
PRODUCTS = ['shared_action_core','shared_issue_mapping','member_projections','compiler_input','compiled_ir','readable_candidates']
RAW_LABELS = {'F000477':['Yea','Yea','Nay','Nay','Yea'], 'M001184':['Yea','Yea','Yea','Yea','Yea']}
STAGES=['suspension_and_passage','suspension_and_passage','final_passage','final_passage','suspension_and_passage']
DECISIONS=['include','include','scope_judgment','include','include']

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

def validate_sources(capture, authoring):
    canonical = {s['source_id']:s for s in read(B/'sources.json')['sources']}
    sources = {s['source_id']:s for s in capture['sources']}
    require(len(sources)==len(capture['sources'])==17, 'source pool changed')
    expected=set()
    for action in authoring['actions']:
        expected.add('clerk:'+action['action_id'].split(':',1)[1])
        expected.update([action['source_id'],*action['additional_source_ids']])
        require(action['meaning'].startswith('The complete retained H.R.'), 'source-version qualification omitted')
        require(any('canonical exact binding remains unresolved' in x for x in action['limitations']), 'unresolved source-version limit removed')
    require(set(sources)==expected, 'unexpected or missing source entered pool')
    for sid,source in sources.items():
        require(sid in canonical, 'new source acquisition/registration proposed')
        require(source['governed_bytes_sha256']==sealed_digest(source,'governed_bytes_sha256'), 'governed source seal changed')
        require(digest(source)==digest(canonical[sid]), 'canonical retained source changed: '+sid)
    return sources

def validate_source_extent():
    extent=read(P/'source_extent_receipt.json')
    require(extent['new_acquisitions']==0 and extent['retained_unchanged_objects']==17, 'source acquisition scope changed')
    require(extent['exact_floor_binding_cleared'] is False and extent['source_holds_changed'] is False and extent['canonical_source_registration'] is False, 'source authority changed')
    require(extent['CERCLA_extent']=='Selected retained(h)(1)–(3), not wholeh/9620; no claim of unretained provisions.', 'CERCLA scope changed')
    sources={s['source_id']:s for s in read(B/'sources.json')['sources']}
    for bill,count in extent['complete_EH_characters'].items():
        require(len(sources['govinfo:hr'+bill+'eh']['text'])==count, 'complete EH extent changed')
    for sid,count in extent['dated_baseline_characters'].items():
        require(len(sources[sid]['text'])==count, 'dated baseline extent changed')

def validate_preflight(pre):
    require(digest(pre)==PREFLIGHT_SHA, 'preflight subject/scope drift')
    require(pre['base_commit']==BASE and pre['accepted'] is False and pre['canonical_changes'] is False, 'preflight authority changed')
    for name,key in [('membership_review.json','membership_sha256'),('universe_proposal.json','universe_sha256'),('sources.json','source_pool_sha256')]:
        require(digest(read(B/name))==pre[key], 'canonical154 changed')
    prior=set(pre['prior_prepared_identities'])
    require(len(prior)==63 and not prior.intersection(ACTIONS), 'duplicate prior preparation')
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
    require(result=={'canonical_records':676,'canonical_pending':246,'prepared_total':68,'prepared_pending':66,'prepared_not_pending':2,'not_prepared':180,'unresolved_among_not_prepared':164,'canonical_source_holds':6},'actual operational queue changed')
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
    for i,((roll,bill),action) in enumerate(zip(SPECS,a['actions'])):
        require(action['stage']==STAGES[i] and action['bill_number']==bill, 'exact stage/measure changed')
        require(action['episode_id'] in a['blocked_episode_ids'], 'candidate hold removed')
        require(set(x['source_id']for x in action['claim_source_map'])==set(action['compact_source_refs']), 'claim/source coverage differs')
    require(sealed_digest(bundle,'bundle_sha256')==bundle['bundle_sha256'] and bundle['authoring_sha256']==digest(a) and bundle['sources_sha256']==digest(data['sources']), 'decision subjects changed')
    require(all(bundle[k] is False for k in ['accepted','canonical_application','publication','production']), 'decision authority changed')
    for i,case in enumerate(bundle['cases']):
        require(case['action_id']==ACTIONS[i] and case['proposed_eligibility']==DECISIONS[i], 'scope decision changed')
        require(case['binding_approval_requested'] is True and case['canonical_binding_already_resolved'] is False, 'binding request changed')
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
    packet_files=validate_manifests(); validate_source_extent(); result=validate()
    print(json.dumps({'preserved_files':715,'packet_files':packet_files,**result},indent=2))

if __name__=='__main__': main()
