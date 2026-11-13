"""Offline checks for the frozen, unaccepted resource/habitat candidates."""
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

P = ROOT / 'docs/review_packets/infrastructure_batch159_resource_habitat'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:227','house:119:1:259','house:119:1:316','house:119:1:358','house:119:2:297']
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
            'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = '970d21c5012d9b9d627038aa2bbe160abd175773bad2416976d2777bc8cdc493'
PRESERVATION_SHA = '3cc5b0c39f9b152ed53825ef6ec61d43f9d56eb35ac5e92e7b32ee131e625010'


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
         ('b829ae75b37eff31fd30f44d669e05e434362091','7131ca816e61e8628ca67fee0c3605210df1d06d')]
SPECS = [('house:119:1:227',4553,'amendment','congressional-record:4553-amend23-roll227-choice150'),
         ('house:119:1:259',3838,'amendment','congressional-record:3838-amend29-roll259-choice158'),
         ('house:119:1:316',1676,'suspension_and_passage','govinfo:hr1676eh'),
         ('house:119:1:358',1366,'final_passage','govinfo:hr1366eh'),
         ('house:119:2:297',3276,'suspension_and_passage','govinfo:hr3276eh')]
EPISODES = [f'episode:hr{n}:119' for _,n,_,_ in SPECS]
DOCS = [('16usc1538','1538','https://www.govinfo.gov/content/pkg/USCODE-2024-title16/html/USCODE-2024-title16-chap35-sec1538.htm'),
        ('16usc1539','1539','https://www.govinfo.gov/content/pkg/USCODE-2024-title16/html/USCODE-2024-title16-chap35-sec1539.htm'),
        ('16usc670a','670a','https://www.govinfo.gov/content/pkg/USCODE-2024-title16/html/USCODE-2024-title16-chap5C-subchapI-sec670a.htm'),
        ('30usc1245','1245','https://www.govinfo.gov/content/pkg/USCODE-2024-title30/html/USCODE-2024-title30-chap25-subchapIV-sec1245.htm')]
CLOSED = 'https://www.govinfo.gov/content/pkg/USCODE-2024-title16/html/USCODE-2024-title16-chap54-sec3709.htm'
RAW_LABELS = {'F000477':['No','No','Yea','Nay','Yea'],
              'M001184':['Aye','Aye','Yea','Yea','Nay']}
STATUSES = {'F000477':['Nay','Nay','Yea','Nay','Yea'],
            'M001184':['Yea','Yea','Yea','Yea','Nay']}


def validate_prior_branch(index, authoring, core):
    pin = read(P/'preparation_preflight.json')['prior_non_main_identity_pins'][index]
    require((pin['commit'],pin['tree']) == PRIOR[index], 'Prior branch identity changed')
    require(digest(authoring) == pin['authoring']['object_sha256'] and
            digest(core) == pin['core']['object_sha256'], 'Prior frozen objects changed')
    require([x['action_id'] for x in authoring['actions']] ==
            [x['action_id'] for x in core['actions']] == pin['action_ids'] and
            not set(ACTIONS)&set(pin['action_ids']), 'Prior held identity duplicated')
    return len(pin['action_ids'])


def validate_captures(capture, bindings, sources):
    require(capture['limits'] == dict(locators=8,timeout_seconds=45,response_bytes=4194304,
            total_bytes=12582912,attempts_per_locator=1,redirects_allowed=False) and
            capture['limits']['redirects_allowed'] is False, 'Capture envelope changed')
    require(len(capture['attempts']) == 5 and len(bindings['sources']) == 4, 'Capture inventory changed')
    require(len({x['url'] for x in capture['attempts']}) == 5, 'Closed locator retried')
    failed=[x for x in capture['attempts'] if x['result'] != 'captured']
    require(len(failed) == 1 and failed[0]['url'] == CLOSED and
            failed[0]['result'] == 'closed_failure' and '302' in failed[0]['error'] and
            not (P/'captures/16usc3709.html').exists(), 'Closed redirect was followed or repaired')
    pool={x['source_id']:x for x in sources['sources']};total=0
    for (name,section,url),binding in zip(DOCS,bindings['sources']):
        attempts=[x for x in capture['attempts'] if x['url']==url];require(len(attempts)==1,'Capture identity changed')
        attempt=attempts[0]
        require(attempt['final_url']==url and attempt['status']==200 and attempt['result']=='captured' and
                attempt['file']==f'captures/{name}.html','Capture result changed')
        raw=(P/attempt['file']).read_bytes();total+=len(raw)
        require(len(raw)==attempt['bytes']<=4194304 and hashlib.sha256(raw).hexdigest()==attempt['sha256'],
                'Raw capture drift')
        full=extract(raw);start=full.index('§'+section+'.');end=full.index('(Pub. L.',start)
        sid='govinfo:resource159:'+name;source=pool[sid]
        require(binding['source_id']==sid and binding['raw_path']==(P/attempt['file']).relative_to(ROOT).as_posix()
                and binding['start_marker']=='§'+section+'.' and binding['stop_marker']=='(Pub. L.' and
                binding['normalized_full_characters']==len(full) and binding['governed_start']==start and
                binding['governed_end']==end and binding['governed_characters']==end-start and
                binding['governed_text_sha256']==hashlib.sha256(full[start:end].encode()).hexdigest(),
                'Declared operative extent changed')
        require(source['source_type']=='official_statutory_text' and source['url']==url and
                source['raw_sha256']==attempt['sha256'] and source['text']==full[start:end] and
                source['governed_bytes_sha256']==sealed_digest(source,'governed_bytes_sha256'),
                'Governed source or authority drift')
        require('2024 Edition' in full and 'Editorial Notes' not in source['text'] and
                'Statutory Notes' not in source['text'], 'Dated operative unit crossed into notes')
    require(total==179378<=12582912,'Cumulative capture bytes changed')
    require('Good Samaritan' not in pool['govinfo:resource159:30usc1245']['text'],
            'Unrelated statutory note supplied funding baseline')
    return dict(new_html=4,closed_redirects=1,raw_bytes=total,original_pdf_or_visual=False)


def prose(text):
    return ' '.join(re.sub(r'-[ \t]*\r?\n\s*','',text).split()).casefold()


def validate_units(authoring,pool,preflight):
    for i,(aid,n,stage,sid) in enumerate(SPECS):
        row=authoring['actions'][i];case=preflight['cases'][i]
        require(row['action_id']==case['action_id']==aid and row['source_id']==case['primary_source_id']==sid and
                row['bill_type']=='hr' and row['bill_number']==n and row['stage']==stage and
                row['episode_id']==EPISODES[i],'Exact whole-choice subject/stage drift')
        clerk=pool['clerk:'+aid.split(':',1)[1]]
        question='On Agreeing to the Amendment' if i<2 else 'On Passage' if i==3 else 'On Motion to Suspend the Rules and Pass, as Amended'
        require(clerk['metadata']['vote-question']==question and clerk['metadata']['rollcall-num']==aid.split(':')[-1],
                'Official question/roll drift')
        for member,labels in RAW_LABELS.items():
            require(clerk['member_records'][member]['official_label']==labels[i], 'Raw official label drift')
        for claim in row['claim_source_map']:
            require(claim['source_id'] in row['compact_source_refs'] and
                    claim['passage'] in pool[claim['source_id']]['text'],'Claim escaped own source')
    perry=prose(pool[SPECS[0][3]]['text'])
    require(all(x in perry for x in ['amendment no. 23','119–232','none of the funds made available by this act',
            'implement or enforce','86 fed. reg. 20628','[roll no. 227]','amendment was rejected']),
            'Perry own target or recorded outcome drift')
    biggs=prose(pool[SPECS[1][3]]['text'])
    require(all(x in biggs for x in ['119–225','119–255','amendment no. 29','[roll no. 259]','amendment was rejected']),
            'Biggs report discrepancy or final result repaired')
    report=pool['house-rules:119255-partA-amend29-operative158']['text']
    require(all(x in report for x in ['29. An Amendment','Section 4(a)(3)(B)','Section 10','subcontractor at any tier',
            'results from, but is not the purpose of','submitted to the Secretary of the Interior']),
            'Independent own Biggs clause drift')
    require('shall not be eligible for patenting' in pool['govinfo:hr1366eh']['text'] and
            'under this section' in pool['govinfo:hr1366eh']['text'],'Printed patent boundary lost')
    require('shall be for available' in pool['govinfo:resource159:30usc1245']['text'], 'Printed baseline silently repaired')
    operators=[
        ['ONLY FUNDS MADE AVAILABLE BY THIS ACT','WHOLE named DRBC','COMBINED TOTAL OF300000OR MORE GALLONS',
         'WITHDRAWN','Recorded195–235REJECTION','asterisks omitting unchanged'],
        ['OTHER qualifying','REGARDLESS OF AN INTEGRATED NATURAL RESOURCES PLAN','BUT NOT THE PURPOSE OF',
         'ANY TIER','overseas Defense support','Initial floor119–225, resumed119–255','Recorded200–228REJECTION',
         'not a technology-only','first installation branch is distinct'],
        ['180-DAY','CONDITIONALLY AUTHORIZE','SET ASIDE','JUNE1OF THE IMMEDIATELY FOLLOWING YEAR',
         'NOT FINAL APPROVAL OR IMMEDIATE PAYMENT','NOT EXCEEDING75PERCENT OF ESTIMATED PROGRAM COST',
         'SEPARATE10PERCENT','EXCLUDING LAW ENFORCEMENT','not a new100percent share'],
        ['REASONABLY NECESSARY','USE/OCCUPY LAND UNDER AN APPROVED PLAN','SINGLE SITE','NO MINERAL RIGHTS',
         'UNDER THIS SECTION','MAY expend AVAILABLE FUND AMOUNTS WITHOUT FURTHER APPROPRIATIONS ONLY',
         'not new guaranteed revenue','Clerical28fchanges'],
        ['VOLUNTARY','COMPETITIVE GRANT PROGRAM','COVERED entities','ELIGIBLE GRANT entities',
         'MAY agree','SHALL NOT APPLY','TO THE EXTENT PRACTICABLE','ALTERNATIVE urban-area branches',
         '50000PLUS CENSUS DESIGNATION','AUTHORIZES200000DOLLARS FOR EACH FY2027–2033']]
    for row,needed in zip(authoring['actions'],operators):
        for field in ['meaning','compact_description']:
            require(all(x in row[field] for x in needed),'Material operator drift')
    return dict(exact_choices=5,amendments=2,whole_passage=3,
                claim_passages=sum(len(x['claim_source_map']) for x in authoring['actions']))


def validate(data=None):
    data=inputs() if data is None else data
    for key,file in [('authoring','authoring.json'),('sources','sources.json'),
                     ('preflight','preparation_preflight.json'),('bundle','decision_bundle.json'),
                     ('retained','retained_sources.json'),('capture','capture_receipt.json'),
                     ('bindings','new_source_bindings.json')]:
        require(digest(data[key]) == digest(read(P/file)), 'Frozen input drift: '+key)
    a,s,pre,bundle=[data[k] for k in ['authoring','sources','preflight','bundle']]
    require(pre['preflight_sha256'] == sealed_digest(pre,'preflight_sha256') and
            all(pre[k] is False for k in ['accepted','canonical_changes','source_holds_changed']),
            'Preflight acquired authority')
    membership,universe,baseline=[read(B/name) for name in ['membership_review.json','universe_proposal.json','sources.json']]
    require([digest(x) for x in [membership,universe,baseline]] ==
            [pre[k] for k in ['membership_sha256','universe_sha256','source_pool_sha256']], 'Canonical154 changed')
    records={x['action_id']:x for x in membership['records']};rows={x['action_id']:x for x in universe['candidate_dispositions']}
    pool={x['source_id']:x for x in s['sources']};original={x['source_id']:x for x in baseline['sources']}
    require(len(pool) == len(s['sources']) == 26 and len(data['retained']['sources']) == 22,
            'Source inventory changed')
    for source in data['retained']['sources']:
        sid=source['source_id'];require(digest(source) == digest(original[sid]) == digest(pool[sid]),'Retained source changed')
    require(len(pre['all_existing_shared_core_checks']) == 153,'Prior-artifact check incomplete')
    for pin in pre['all_existing_shared_core_checks']:
        core=read(ROOT/pin['path'])
        require(digest(core) == pin['object_sha256'] and not pin['matching_action_ids'] and
                not set(ACTIONS)&{x['action_id'] for x in core['actions']},'Existing shared truth changed')
    require(len(pre['prior_prepared_identities']) == len(set(pre['prior_prepared_identities'])) == 48 and
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
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),
            'Held choice produced proposition')
    proof=read(P/'held_replay_proof.json')
    require(proof['product_sha256'] == {k:digest(v) for k,v in actual.items()} and
            proof['behavioral_update_proof_exercised'] is False,'Replay proof overclaims')
    return dict(cores=5,official_observations=10,held_episodes=5,propositions=0,sources=26,
                canonical_changes=False,acceptance=False,
                captures=validate_captures(data['capture'],data['bindings'],s),units=validate_units(a,pool,pre))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(),packet_files=validate_manifest(),
                         validation=validate()),indent=2))
