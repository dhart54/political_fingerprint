"""Offline checks for the frozen, unaccepted foreign-disclosure/finance candidates."""
import hashlib
import json
import sys
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core,
    validate_shared_issue_mapping, validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT / 'docs/review_packets/infrastructure_batch160_foreign_disclosure_finance'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:'+str(n) for n in [15,80,81,82,307]]
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
            'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = '541c3622e9987343bbc2b5241562ab9e190aa13d62a5226093bbe0ffa9ab4b88'
PRESERVATION_SHA = 'd019e817648fe46c6a88c5572439a289c3b1f2e0be04f02441aa6df6b3599706'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(value, message):
    if not value:
        raise ValueError(message)


def inputs():
    names = dict(authoring='authoring.json', sources='sources.json',
                 preflight='preparation_preflight.json', bundle='decision_bundle.json',
                 retained='retained_sources.json', capture='capture_receipt.json',
                 bindings='new_source_bindings.json')
    return {**{k: read(P/v) for k,v in names.items()},
            'products': {k: read(P/'generated'/(k+'.json')) for k in PRODUCTS}}


def replay(authoring, sources):
    core, mapping, projections, compiler_input, result = prepare(authoring, sources, MEMBERS)
    return dict(shared_action_core=core, shared_issue_mapping=mapping,
                member_projections=projections, compiler_input=compiler_input,
                compiled_ir=result.compiled_ir,
                readable_candidates=readable_candidates(authoring, core, projections, result))


def validate_files(name, expected, packet):
    manifest = read(P / name)
    require(digest(manifest) == expected and
            manifest['manifest_sha256'] == sealed_digest(manifest, 'manifest_sha256'),
            'Frozen manifest changed')
    for name, entry in manifest['files'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to((P if packet else ROOT).resolve()), 'Manifest escaped')
        raw = path.read_bytes()
        if entry['mode'] == 'lf':
            raw = raw.replace(b'\r\n', b'\n')
        require(len(raw) == entry['bytes'] and
                hashlib.sha256(raw).hexdigest() == entry['sha256'], 'Frozen bytes differ: ' + name)
    return len(manifest['files'])


def validate_manifest():
    return validate_files('packet_manifest.json', MANIFEST_SHA, True)


def validate_preservation():
    return validate_files('preservation_manifest.json', PRESERVATION_SHA, False)


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, text):
        self.parts.append(text)


def extract(raw):
    parser = HTMLText()
    parser.feed(raw.decode('utf-8'))
    return ' '.join(' '.join(parser.parts).split())


PRIOR = [('c6e6df3537ce464abcde22b13401cc7ae878aaf1','c095133b5dbc148a59e135e00e5d3e851b4265e0'),
         ('f684d89987498efb335db9c14fdf3da848734de1','30f154c235954ea9067b84b50e6432ec5eede618'),
         ('328aaa56266ffd643a1eb74ed1ebbab95d19b428','4f4028db10185ace7e3f622c59afbcd5485f2352'),
         ('b829ae75b37eff31fd30f44d669e05e434362091','7131ca816e61e8628ca67fee0c3605210df1d06d'),
         ('f4914598425418361bdebf514937fbbfe5691afc','1d9438b79f00bcb4eee9d88f00e49f79f35dfd3e')]
SPECS = [('house:119:1:15',33,'final_passage','govinfo:hr33eh'),
         ('house:119:1:80',1048,'amendment','immigration:hr1048-package-initial175'),
         ('house:119:1:81',1048,'amendment','immigration:hr1048-package-initial175'),
         ('house:119:1:82',1048,'amendment','immigration:hr1048-package-initial175'),
         ('house:119:1:307',4423,'suspension_and_passage','govinfo:hr4423eh')]
EPISODES = ['episode:hr33:119','episode:hr1048:119','episode:hr4423:119']
BASE='65575bf9a045f23c99f07a0750e6560fbd937655'
NEW_SOURCE='govinfo:foreign160:20usc1011f-2024-full'
NEW_URL='https://www.govinfo.gov/content/pkg/USCODE-2024-title20/html/USCODE-2024-title20-chap28-subchapI-partB-sec1011f.htm'
RAW_LABELS={'F000477':['Yea','No','No','No','Yea'],
            'M001184':['Nay','Aye','No','No','Not Voting']}
STATUSES={'F000477':['Yea','Nay','Nay','Nay','Yea'],
          'M001184':['Nay','Yea','Nay','Nay','Not Voting']}


def validate_prior_branch(index, authoring, core):
    pin = read(P/'preparation_preflight.json')['prior_non_main_identity_pins'][index]
    require((pin['commit'],pin['tree']) == PRIOR[index], 'Prior branch identity changed')
    require(digest(authoring) == pin['authoring']['object_sha256'] and
            digest(core) == pin['core']['object_sha256'], 'Prior frozen objects changed')
    require([x['action_id'] for x in authoring['actions']] ==
            [x['action_id'] for x in core['actions']] == pin['action_ids'] and
            not set(ACTIONS)&set(pin['action_ids']), 'Prior held identity duplicated')
    return len(pin['action_ids'])


def validate_captures(capture,bindings,sources):
    require(capture['limits']==dict(locators=1,timeout_seconds=45,response_bytes=1048576,
            total_bytes=1048576,attempts_per_locator=1,redirects_allowed=False) and
            capture['limits']['redirects_allowed'] is False,'Capture envelope changed')
    require(len(capture['attempts'])==len(bindings['sources'])==1,'Capture inventory changed')
    attempt=capture['attempts'][0];binding=bindings['sources'][0]
    require(attempt['url']==attempt['final_url']==NEW_URL and attempt['status']==200 and
            attempt['result']=='captured' and attempt['file']=='captures/20usc1011f.html',
            'Capture identity/redirect changed')
    raw=(P/attempt['file']).read_bytes()
    require(len(raw)==attempt['bytes']==10707<=1048576 and
            hashlib.sha256(raw).hexdigest()==attempt['sha256'],'Raw source drift')
    full=extract(raw);start=full.index(chr(167)+'1011f.');end=full.index('(Pub. L.',start)
    require(binding['source_id']==NEW_SOURCE and binding['raw_path']==
            (P/attempt['file']).relative_to(ROOT).as_posix() and
            binding['start_marker']==chr(167)+'1011f.' and binding['stop_marker']=='(Pub. L.' and
            binding['normalized_full_characters']==len(full) and binding['governed_start']==start and
            binding['governed_end']==end and binding['governed_characters']==end-start==6781 and
            binding['governed_text_sha256']==hashlib.sha256(full[start:end].encode()).hexdigest(),
            'Declared operative extent changed')
    pool={x['source_id']:x for x in sources['sources']};source=pool[NEW_SOURCE]
    require(source['source_type']=='official_statutory_text' and source['url']==NEW_URL and
            source['raw_sha256']==attempt['sha256'] and source['text']==full[start:end] and
            source['governed_bytes_sha256']==sealed_digest(source,'governed_bytes_sha256') and
            '2024 Edition' in full and 'Editorial Notes' not in source['text'],
            'Dated operative source or authority changed')
    require('$250,000' in source['text'] and 'January 31 or July 31, whichever is sooner' in source['text'],
            'Old baseline overwritten by proposed child')
    return dict(new_html=1,raw_bytes=len(raw),operative_characters=end-start,original_pdf_or_visual=False)


def prose(text):
    return ' '.join(re.sub(r'-[ \t]*\r?\n\s*','',text).split()).casefold()


def own_initial(pool,number):
    text=pool['immigration:hr1048-package-initial175']['text']
    begin=text.index('AMENDMENT NO. '+str(number)+' OFFERED BY')
    end=text.index('AMENDMENT NO. '+str(number+1)+' OFFERED BY',begin) if number<6 else text.index('The Acting CHAIR. The Chair under-',begin)
    return text[begin:end]


def own_recorded(pool,roll):
    text=pool['immigration:hr1048-package-recorded175']['text'];i=text.index('[Roll No. '+str(roll)+']')
    begin=text.rfind('RECORDED VOTE',0,i);end=text.find('RECORDED VOTE',i)
    return text[begin:end if end>=0 else len(text)]


def validate_units(authoring,pool,preflight):
    for i,(aid,n,stage,sid) in enumerate(SPECS):
        row=authoring['actions'][i];case=preflight['cases'][i]
        require(row['action_id']==case['action_id']==aid and row['source_id']==case['primary_source_id']==sid and
                row['bill_type']=='hr' and row['bill_number']==n and row['stage']==stage and
                row['episode_id']=='episode:hr'+str(n)+':119','Exact choice subject/stage drift')
        clerk=pool['clerk:'+aid.split(':',1)[1]]
        question='On Agreeing to the Amendment' if 1<=i<=3 else 'On Passage' if i==0 else 'On Motion to Suspend the Rules and Pass, as Amended'
        require(clerk['metadata']['vote-question']==question and clerk['metadata']['rollcall-num']==aid.split(':')[-1],
                'Official question/roll drift')
        for member,labels in RAW_LABELS.items():
            require(clerk['member_records'][member]['official_label']==labels[i],'Raw official status drift')
        for claim in row['claim_source_map']:
            require(claim['source_id'] in row['compact_source_refs'] and
                    claim['passage'] in pool[claim['source_id']]['text'],'Claim escaped own source')
        if 1<=i<=3:
            claims={x['source_id']:x['passage'] for x in row['claim_source_map']}
            require(claims[sid]==own_initial(pool,i+3) and
                    claims['immigration:hr1048-package-recorded175']==own_recorded(pool,79+i),
                    'Another child/component supplied this choice')
            recorded=prose(own_recorded(pool,79+i));require('amendment was rejected' in recorded,'Failed child changed to passage')
    initial=[prose(own_initial(pool,n)) for n in [4,5,6]]
    require(all(x in initial[0] for x in ['page 2, line 5','50,000','$1']), 'Self offered target drift')
    require(all(x in initial[1] for x in ['page 57, after line 18','alleged violation','outstanding arrest warrants']),
            'Country criterion target/allegation drift')
    require(all(x in initial[2] for x in ['page 39, after line 21','secretary of state','consistently, knowingly, and directly',
            'state violence and repression, war and occupation, or severe violations','alleged violation']),
            'Investment criterion actor/conduct logic drift')
    rcp=pool['house-rules:rcp119-1']['text']
    require('$50,000' in rcp and 'INVESTMENT OF CONCERN' in rcp and
            'F OREIGN COUNTRY OF CONCERN' in rcp,'Own proposed target replaced by old/final text')
    require('text of Rules Committee Print 119-1' in pool['govinfo:hres242eh']['text'],
            'Deemed base/version chain changed')
    require('$250,000' in pool[NEW_SOURCE]['text'],'Old reporting baseline changed')
    operators=[
        ['TWO TITLES','QUALIFIED','NON-US-CITIZENS','OR regular international ship/aircraft crew',
         'BOTH payment by/on behalf','MORE THAN12MONTHS','MORE THAN30DAYS','TREASURY RECIPROCITY DETERMINATION',
         'AFTER that determination','PRE-NEGOTIATION','BEFORE entering','AFTER entering',
         'ENTRY INTO FORCE','approval legislation AND implementing legislation','CODE-CONTROL'],
        ['RCP119-1PAGE2LINE5','ONE DOLLAR OR MORE','ALONE OR AGGREGATED WITH THE SAME FOREIGN SOURCE WITHIN THE CALENDAR YEAR',
         'indeterminate-value alternative','NOT AUTOMATICALLY INCORPORATED','does NOT CREATE A SEARCHABLE DATABASE',
         'Recorded92–321REJECTION'],
        ['ALTERNATIVE COUNTRY CRITERIA','RCP119-1PAGE57LINE18','ALLEGED','OUTSTANDING ICCARREST WARRANTS',
         'NOT A GUILT DETERMINATION','rather than requiring both','Recorded3–410REJECTION'],
        ['RCP119-1PAGE39LINE21','117C(h)(1)(A)INVESTMENT OF CONCERN','NOT A WHOLESALE',
         'SECRETARY OF STATE DETERMINATION','CONSISTENTLY, KNOWINGLY, AND DIRECTLY',
         'state violence AND repression, war AND occupation, OR severe violations of international law AND human rights',
         'ALONE DOES NOT REPLACE THE DETERMINATION AND CONDUCT PREDICATES','Recorded4–404REJECTION',
         'aggregate Present is not either observed member'],
        ['DIRECT THE USIBRDEXECUTIVE DIRECTOR TO USE USVOICE AND VOTE','BOTH DISBURSEMENTS AND NEW FINANCING COMMITMENTS TO THE GOVERNMENT OF BURMA',
         'UNLESS TREASURY DETERMINES CONTINUATION IS NOT IN THE NATIONAL INTEREST','neither unilateral UScontrol',
         'legislative attribution']]
    for row,needed in zip(authoring['actions'],operators):
        for field in ['meaning','compact_description']:
            require(all(x in row[field] for x in needed),'Material meaning operator drift')
    return dict(exact_choices=5,rejected_children=3,whole_passage=2,
                claim_passages=sum(len(x['claim_source_map']) for x in authoring['actions']))


def validate_preserved_parent_refs(pre):
    refs=pre['existing_parent_or_other_core_refs_to_preserve']
    require(len(refs)==3 and {x['action_id'] for x in refs}=={'house:119:1:79','house:119:1:83'},
            'Existing parent/other truth inventory changed')
    for ref in refs:
        core=read(ROOT/ref['path']);rows=[x for x in core['actions'] if x['action_id']==ref['action_id']]
        require(len(rows)==1 and rows[0]['action_meaning_ref']==ref['meaning_ref'] and
                rows[0]['action_core_sha256']==ref['action_core_sha256'],'Existing parent/other truth changed')
    return len(refs)


def validate(data=None):
    data=inputs() if data is None else data
    for key,file in [('authoring','authoring.json'),('sources','sources.json'),
                     ('preflight','preparation_preflight.json'),('bundle','decision_bundle.json'),
                     ('retained','retained_sources.json'),('capture','capture_receipt.json'),
                     ('bindings','new_source_bindings.json')]:
        require(digest(data[key]) == digest(read(P/file)), 'Frozen input drift: '+key)
    a,s,pre,bundle=[data[k] for k in ['authoring','sources','preflight','bundle']]
    require(pre['base_commit']==BASE,'Actual feature parent changed')
    validate_preserved_parent_refs(pre)
    require(pre['preflight_sha256'] == sealed_digest(pre,'preflight_sha256') and
            all(pre[k] is False for k in ['accepted','canonical_changes','source_holds_changed']),
            'Preflight acquired authority')
    membership,universe,baseline=[read(B/name) for name in ['membership_review.json','universe_proposal.json','sources.json']]
    require([digest(x) for x in [membership,universe,baseline]] ==
            [pre[k] for k in ['membership_sha256','universe_sha256','source_pool_sha256']], 'Canonical154 changed')
    records={x['action_id']:x for x in membership['records']};rows={x['action_id']:x for x in universe['candidate_dispositions']}
    pool={x['source_id']:x for x in s['sources']};original={x['source_id']:x for x in baseline['sources']}
    require(len(pool) == len(s['sources']) == 13 and len(data['retained']['sources']) == 12,
            'Source inventory changed')
    for source in data['retained']['sources']:
        sid=source['source_id'];require(digest(source) == digest(original[sid]) == digest(pool[sid]),'Retained source changed')
    require(len(pre['all_existing_shared_core_checks']) == 153,'Prior-artifact check incomplete')
    for pin in pre['all_existing_shared_core_checks']:
        core=read(ROOT/pin['path'])
        require(digest(core) == pin['object_sha256'] and not pin['matching_action_ids'] and
                not set(ACTIONS)&{x['action_id'] for x in core['actions']},'Existing shared truth changed')
    require(len(pre['prior_prepared_identities']) == len(set(pre['prior_prepared_identities'])) == 53 and
            not set(ACTIONS)&set(pre['prior_prepared_identities']),'Prior held preparation duplicated')
    require([x['action_id'] for x in a['actions']] == [x['action_id'] for x in pre['cases']] ==
            [x['action_id'] for x in bundle['cases']] == ACTIONS,'Case correspondence changed')
    require(a['blocked_episode_ids'] == EPISODES,'Hold removed')
    for case,decision in zip(pre['cases'],bundle['cases']):
        aid=case['action_id'];require(digest(records[aid]) == digest(case['record']) == case['record_sha256'] and
                digest(rows[aid]) == digest(case['row']) == case['row_sha256'],'Canonical preimage changed')
        require(records[aid]['disposition'] == 'pending_interpretation' and
                all(records[aid][k] is False for k in ['exact_action_binding_unresolved','required_evidence_unavailable','authoritative_source_conflict']),
                'Canonical flags changed')
        require(decision['canonical_binding_already_resolved'] is True and
                all(decision[k] is False for k in ['binding_approval_requested','binding_applied','meaning_accepted',
                    'eligibility_applied','canonical_sources_registered','source_holds_changed']),'Case acquired authority')
    require(bundle['bundle_sha256'] == sealed_digest(bundle,'bundle_sha256') and
            all(bundle[k] is False for k in ['accepted','canonical_application','publication','production']), 'Bundle acquired authority')
    actual=data['products'];require(digest(actual) == digest(replay(a,s)),'Native held replay differs')
    core=actual['shared_action_core'];validate_shared_action_core(ROOT,core)
    validate_shared_issue_mapping(ROOT,actual['shared_issue_mapping'],core)
    for action,decision in zip(core['actions'],bundle['cases']):
        require(action['action_meaning_ref'] == decision['meaning_ref'] and
                action['action_core_sha256'] == decision['candidate_core_sha256'],'Decision subject changed')
    for member in actual['member_projections']:
        validate_member_projection(ROOT,member,core)
        expected=STATUSES[member['member_id']]
        require([x['official_status'] for x in member['actions']] == expected,'Official choice changed')
    for member in actual['compiled_ir']['members']:
        cov=member['coverage'];expected=(5,0) if member['member_id']=='F000477' else (4,1)
        require((cov['directional_yes_no_positions'],cov['not_voting_actions'])==expected and
                cov['resolved_eligible_actions']==5 and cov['missing_evidence_actions']==0 and
                cov['present_actions']==0,'Non-directional or chamber status transferred')
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),
            'Held choice produced proposition')
    proof=read(P/'held_replay_proof.json')
    require(proof['product_sha256'] == {k:digest(v) for k,v in actual.items()} and
            proof['behavioral_update_proof_exercised'] is False,'Replay proof overclaims')
    return dict(cores=5,official_observations=10,held_episodes=3,propositions=0,sources=13,
                canonical_changes=False,acceptance=False,
                captures=validate_captures(data['capture'],data['bindings'],s),units=validate_units(a,pool,pre))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(),packet_files=validate_manifest(),
                         validation=validate()),indent=2))
