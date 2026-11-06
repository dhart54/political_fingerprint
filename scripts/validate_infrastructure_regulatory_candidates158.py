"""Offline checks for the frozen, unaccepted regulatory-choice candidates."""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core,
    validate_shared_issue_mapping, validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT / 'docs/review_packets/infrastructure_batch158_regulatory_choices'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:'+str(n) for n in [35,52,71,110,113]]
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
            'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = '8fe7f2ecbbb22453b71fa7613f18eb617461ab0f32dc33641151fdba455d39ac'
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


PRIOR = [('c6e6df3537ce464abcde22b13401cc7ae878aaf1', 'c095133b5dbc148a59e135e00e5d3e851b4265e0'),
         ('f684d89987498efb335db9c14fdf3da848734de1', '30f154c235954ea9067b84b50e6432ec5eede618'),
         ('328aaa56266ffd643a1eb74ed1ebbab95d19b428', '4f4028db10185ace7e3f622c59afbcd5485f2352')]
SPECS = [(35,'hr',26,'govinfo:hr26eh'),(52,'hjres',35,'govinfo:hjres35eh'),
         (71,'hjres',25,'govinfo:hjres25eh'),(110,'hjres',60,'govinfo:hjres60eh'),
         (113,'hjres',78,'govinfo:hjres78eh')]
EPISODES = [f'episode:{bt}{n}:119' for _,bt,n,_ in SPECS]
DOCS = [('2024-26643','2024-11-18','91094-91195'),
        ('2024-30496','2024-12-30','106928-106960'),
        ('2025-00509','2025-01-13','2621-2631'),
        ('2024-16380','2024-07-30','61029-61049')]


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
    require(len(capture['attempts']) == len(bindings['sources']) == 4, 'Capture inventory changed')
    pool = {x['source_id']:x for x in sources['sources']}
    total = 0
    for (number,date,pages), attempt, binding in zip(DOCS,capture['attempts'],bindings['sources']):
        url = f'https://www.govinfo.gov/content/pkg/FR-{date}/html/{number}.htm'
        require(attempt['url'] == attempt['final_url'] == url and attempt['status'] == 200 and
                attempt['result'] == 'captured' and attempt['file'] == f'captures/{number}.html',
                'Capture identity/result changed')
        raw = (P/attempt['file']).read_bytes()
        require(len(raw) == attempt['bytes'] <= 4194304 and
                hashlib.sha256(raw).hexdigest() == attempt['sha256'], 'Raw capture changed')
        total += len(raw)
        sid = 'govinfo:regulatory158:'+number
        require(binding['source_id'] == sid and binding['raw_path'] ==
                (P/attempt['file']).relative_to(ROOT).as_posix(), 'Raw/source binding changed')
        source = pool[sid]
        require(source['source_type'] == 'official_rule_text' and source['url'] == url and
                source['raw_sha256'] == attempt['sha256'] and source['text'] == extract(raw) and
                source['governed_bytes_sha256'] == sealed_digest(source,'governed_bytes_sha256'),
                'HTML source or authority drift')
        require(f'[FR Doc No: {number}]' in source['text'] and f'[Pages {pages}]' in source['text'],
                'Wrong official rule unit')
    require(total == 1248915 <= 12582912, 'Capture cumulative bytes changed')
    require(pool['govinfo:regulatory158:2024-26643']['text'].count('[GRAPHIC]') == 33 and
            pool['govinfo:regulatory158:2024-16380']['text'].count('[GRAPHIC]') == 3,
            'Omitted graphics silently repaired')
    return dict(new_html=4,raw_bytes=total,original_pdf_or_visual=False)


def validate_units(authoring, pool, preflight):
    # Independent positive/negative checks are callable without frozen input equality.
    for i,(roll,bt,n,sid) in enumerate(SPECS):
        row=authoring['actions'][i];case=preflight['cases'][i]
        require(row['action_id'] == case['action_id'] == ACTIONS[i] and
                row['source_id'] == case['primary_source_id'] == sid and row['bill_type'] == bt and
                row['bill_number'] == n and row['stage'] == 'final_passage' and
                row['episode_id'] == EPISODES[i], 'Exact whole-passage subject drift')
        clerk=pool['clerk:119:1:'+str(roll)]
        require(clerk['metadata']['vote-question'] == 'On Passage' and
                clerk['metadata']['rollcall-num'] == str(roll), 'Official question/roll drift')
        for member,label in [('F000477','Nay'),('M001184','Yea')]:
            require(clerk['member_records'][member]['official_label'] == label, 'Official status drift')
        if i:
            require('Congress disapproves' in pool[sid]['text'] and
                    'such rule shall have no force or effect' in pool[sid]['text'], 'CRA target operator drift')
            require(row['additional_source_ids'] == ['govinfo:regulatory158:'+DOCS[i-1][0]],
                    'Rule context crossed between resolutions')
        else:
            require('unless such moratorium is authorized by an Act of Congress' in pool[sid]['text'],
                    'Congressional exception omitted')
        for claim in row['claim_source_map']:
            require(claim['source_id'] in row['compact_source_refs'] and
                    claim['passage'] in pool[claim['source_id']]['text'], 'Claim escaped own source')
    operators = [
        ['NONBINDING','PRESIDENT MAY NOT DECLARE A MORATORIUM','UNLESS authorized by an Act of Congress',
         'subsection(b)prints no such land limitation','neither a ban on every'],
        ['THAT RULE','MORE THAN25000metrictonsCO2e','METHANE INTENSITY THRESHOLDS',
         '36months','following year','next business day','not unrestricted cross-owner',
         'omitted graphical equations are unintegrated'],
        ['THAT RULE','GROSS PROCEEDS','POSITION TO KNOW','actual fee collection is not required',
         'VALIDATION-ONLY','only for sales using those services','ON OR AFTER JANUARY1,2027',
         'February28,2025'],
        ['THAT RULE','VEHICLE/ROAD/AREA-SPECIFIC','BELOW FOR SEVEN CONSECUTIVE DAYS',
         'ABOVE FOR SEVEN CONSECUTIVE DAYS','within14days','superintendent discretion',
         'except LoneRockBeach','seven named unpaved','unchanged starred text'],
        ['THAT RULE','THAT DPS','ENDANGERED(E)','does NOT ITSELF DESIGNATE CRITICAL HABITAT',
         'attributed to the agency','written not-likely-adversely-affect concurrence exception',
         'not a universal project exemption']]
    for row,required in zip(authoring['actions'],operators):
        for field in ['meaning','compact_description']:
            require(all(token in row[field] for token in required), 'Material meaning operator drift')
    return dict(exact_passage_choices=5,claim_passages=sum(len(x['claim_source_map']) for x in authoring['actions']))


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
    require(len(pool) == len(s['sources']) == 14 and len(data['retained']['sources']) == 10,
            'Source inventory changed')
    for source in data['retained']['sources']:
        sid=source['source_id'];require(digest(source) == digest(original[sid]) == digest(pool[sid]),'Retained source changed')
    require(len(pre['all_existing_shared_core_checks']) == 153,'Prior-artifact check incomplete')
    for pin in pre['all_existing_shared_core_checks']:
        core=read(ROOT/pin['path'])
        require(digest(core) == pin['object_sha256'] and not pin['matching_action_ids'] and
                not set(ACTIONS)&{x['action_id'] for x in core['actions']},'Existing shared truth changed')
    require(len(pre['prior_prepared_identities']) == len(set(pre['prior_prepared_identities'])) == 43 and
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
        expected=['Nay']*5 if member['member_id']=='F000477' else ['Yea']*5
        require([x['official_status'] for x in member['actions']] == expected,'Official choice changed')
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),
            'Held choice produced proposition')
    proof=read(P/'held_replay_proof.json')
    require(proof['product_sha256'] == {k:digest(v) for k,v in actual.items()} and
            proof['behavioral_update_proof_exercised'] is False,'Replay proof overclaims')
    return dict(cores=5,official_observations=10,held_episodes=5,propositions=0,sources=14,
                canonical_changes=False,acceptance=False,
                captures=validate_captures(data['capture'],data['bindings'],s),units=validate_units(a,pool,pre))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(),packet_files=validate_manifest(),
                         validation=validate()),indent=2))
