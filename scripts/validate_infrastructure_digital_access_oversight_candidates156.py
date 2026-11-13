"""Offline checks for the frozen, unaccepted digital-access/oversight candidates."""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core,
    validate_shared_issue_mapping, validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates
from scripts.validate_infrastructure_water_resource_candidates152 import compare_operative

P = ROOT / 'docs/review_packets/infrastructure_batch156_digital_access_oversight'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:107', 'house:119:1:147', 'house:119:1:300',
           'house:119:1:311', 'house:119:2:301']
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
            'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = '555002e57f6eb7a114581ac9d06580ab6ab1ca59bb41149ee2499ec3feff8954'
PRESERVATION_SHA = '3cc5b0c39f9b152ed53825ef6ec61d43f9d56eb35ac5e92e7b32ee131e625010'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(value, message):
    if not value:
        raise ValueError(message)


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, text):
        self.parts.append(text)


def extract(raw, xml=False):
    if xml:
        return " ".join(" ".join(ET.fromstring(raw).itertext()).split())
    parser = HTMLText()
    parser.feed(raw.decode('utf-8'))
    return ' '.join(' '.join(parser.parts).split())


def inputs():
    names = dict(authoring='authoring.json', sources='sources.json',
                 preflight='preparation_preflight.json', bundle='decision_bundle.json',
                 capture='capture_receipt.json', bindings='new_source_bindings.json',
                 retained='retained_sources.json', proof='held_replay_proof.json',
                 conformance='floor_version_conformance.json')
    return {**{k: read(P / v) for k, v in names.items()},
            'products': {k: read(P / 'generated' / (k + '.json')) for k in PRODUCTS}}


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


def validate_prior_branch(authoring, core):
    pins = read(P / 'preparation_preflight.json')['prior_non_main_identity_pins']
    require(pins['commit'] == 'c6e6df3537ce464abcde22b13401cc7ae878aaf1' and
            pins['tree'] == 'c095133b5dbc148a59e135e00e5d3e851b4265e0', 'Prior branch pin changed')
    require(digest(authoring) == pins['authoring']['object_sha256'] and
            digest(core) == pins['core']['object_sha256'], 'Frozen155 object changed')
    require([x['action_id'] for x in authoring['actions']] ==
            [x['action_id'] for x in core['actions']] == pins['action_ids'] and
            not set(ACTIONS) & set(pins['action_ids']), 'Non-main held155 duplicated')
    return len(pins['action_ids'])


def validate_floor(pool, proof):
    require(proof['receipt_sha256'] == sealed_digest(proof, 'receipt_sha256') and
            proof['binding_approved'] is proof['binding_applied'] is False, 'Conformance acquired authority')
    eh = pool[proof['eh_source_id']]['text']
    floor = pool[proof['floor_source_id']]['text']
    eh = eh[eh.index('SECTION 1.'):eh.index('Passed the House')]
    floor = floor[floor.index('SECTION 1.'):]
    compared, edits = compare_operative(eh, floor)
    require(len(eh) == proof['eh_operative_characters'] and
            len(floor) == proof['floor_operative_characters'] and
            len(compared) == proof['compared_characters'] == 7151 and
            hashlib.sha256(compared.encode()).hexdigest() == proof['compared_sha256'] and
            digest(edits) == digest(proof['layout_hyphen_edits']), 'Whole floor/EH conformance drift')
    def prose(s):
        return ' '.join(re.sub(r'-[ \t]*\r?\n\s*', '', s).split())
    initial = prose(pool[proof['initial_source_id']]['text'])
    recorded = prose(pool[proof['recorded_source_id']]['text'])
    require(initial.index('question is on the motion') < initial.index('The question was taken') <
            initial.index('two-thirds being') < initial.index('demand the yeas and nays') <
            initial.index('further proceedings'), 'Initial opinion/demand/postponement sequence changed')
    require('H.R. 2978, as amended' in initial and 'unfinished business' in recorded and
            '(H.R. 2978)' in recorded and 'yeas 414, nays 7' in recorded and
            'not voting 12' in recorded and 'bill, as amended, was passed' in recorded,
            'Own resumed recorded choice/result changed')
    return dict(compared_characters=len(compared), layout_hyphen_decisions=len(edits))


def validate_capture(capture=None, bindings=None, sources=None):
    capture = read(P / 'capture_receipt.json') if capture is None else capture
    bindings = read(P / 'new_source_bindings.json') if bindings is None else bindings
    sources = read(P / 'sources.json') if sources is None else sources
    limits = {'locators': 12, 'timeout_seconds': 45, 'response_bytes': 4194304,
              'total_bytes': 20971520, 'attempts_per_locator': 1, 'redirects_allowed': False}
    require(digest(capture['limits']) == digest(limits), 'Prospective source limits changed')
    attempts = capture['attempts']
    require(len(attempts) == 12 and len({x['url'] for x in attempts}) == 12,
            'Capture attempts repeated or omitted')
    closed = [x for x in attempts if x['result'] == 'closed_failure']
    require([x['file'] for x in closed] == ['captures/6usc604-2024.html',
            'captures/6usc605-2024.html', 'captures/6usc609-2024.html'] and
            all(x['error'] == 'HTTP Error 302: Found' for x in closed), 'Closed redirects changed')
    captured = [x for x in attempts if x['result'] == 'captured']
    pool = {x['source_id']: x for x in sources['sources']}
    require(len(captured) == len(bindings['sources']) == 9, 'Capture inventory changed')
    total = 0
    for e in captured:
        require(e['status'] == 200 and e['url'] == e['final_url'] and
                e['url'].startswith('https://www.govinfo.gov/'), 'Capture status/redirect/host changed')
        raw = (P / e['file']).read_bytes()
        require(type(e['bytes']) is int and 0 < len(raw) == e['bytes'] <= 4194304 and
                hashlib.sha256(raw).hexdigest() == e['sha256'], 'Raw capture drift/cap')
        total += len(raw)
        binding = next(x for x in bindings['sources'] if x['raw_path'] ==
                       (P / e['file']).relative_to(ROOT).as_posix())
        source = pool[binding['source_id']]
        require(source['url'] == e['url'] and source['raw_sha256'] == e['sha256'] and
                source['text'] == extract(raw, e['file'].endswith('.xml')),
                'Raw extraction/source identity drift')
    require(total == 143510 <= limits['total_bytes'], 'Total capture bytes changed')
    return dict(successful=9, closed_redirects=3, raw_bytes=total)


def validate(data=None):
    data = inputs() if data is None else data
    # These are frozen reviewed candidate inputs, not a general truth/acceptance engine.
    for key, filename in [('authoring', 'authoring.json'), ('sources', 'sources.json'),
                          ('preflight', 'preparation_preflight.json'),
                          ('bundle', 'decision_bundle.json'), ('retained', 'retained_sources.json'),
                          ('bindings', 'new_source_bindings.json'), ('proof', 'held_replay_proof.json'),
                          ('conformance', 'floor_version_conformance.json')]:
        require(digest(data[key]) == digest(read(P / filename)), 'Frozen input drift: ' + key)
    a, s, pre, bundle = [data[k] for k in ['authoring', 'sources', 'preflight', 'bundle']]
    require(pre['preflight_sha256'] == sealed_digest(pre, 'preflight_sha256') and
            all(pre[k] is False for k in ['accepted', 'canonical_changes', 'source_holds_changed']),
            'Preflight acquired authority')
    membership, universe, baseline = [read(B / name) for name in
                                    ['membership_review.json', 'universe_proposal.json', 'sources.json']]
    require([digest(x) for x in [membership, universe, baseline]] ==
            [pre[k] for k in ['membership_sha256', 'universe_sha256', 'source_pool_sha256']],
            'Canonical154 changed')
    records = {x['action_id']: x for x in membership['records']}
    rows = {x['action_id']: x for x in universe['candidate_dispositions']}
    pool = {x['source_id']: x for x in s['sources']}
    original = {x['source_id']: x for x in baseline['sources']}
    require(len(pool) == len(s['sources']) == 25, 'Source inventory changed')
    require(len(data['retained']['sources']) == 16, 'Retained source count changed')
    for source in data['retained']['sources']:
        sid = source['source_id']
        require(digest(source) == digest(original[sid]) == digest(pool[sid]),
                'Retained source changed')
    prior = pre['all_existing_shared_core_checks']
    require(len(prior) == 153, 'Prior-artifact check incomplete')
    for pin in prior:
        core = read(ROOT / pin['path'])
        require(digest(core) == pin['object_sha256'] and not pin['matching_action_ids'] and
                not set(ACTIONS) & {x['action_id'] for x in core.get('actions', [])},
                'Existing shared truth/collision changed')
    require(len(pre['prior_prepared_identities']) == 33 and
            not set(ACTIONS) & set(pre['prior_prepared_identities']), 'Prior held preparation duplicated')
    require([x['action_id'] for x in a['actions']] ==
            [x['action_id'] for x in pre['cases']] ==
            [x['action_id'] for x in bundle['cases']] == ACTIONS, 'Case correspondence changed')
    require(a['blocked_episode_ids'] == ['episode:hr1402:119', 'episode:hr1804:119',
            'episode:hr4058:119', 'episode:hr4305:119', 'episode:hr2978:119'], 'Hold removed')
    for case, decision in zip(pre['cases'], bundle['cases']):
        aid = case['action_id']
        require(digest(records[aid]) == digest(case['record']) == case['record_sha256'] and
                digest(rows[aid]) == digest(case['row']) == case['row_sha256'], 'Canonical preimage changed')
        require(records[aid]['disposition'] == 'pending_interpretation' and
                all(records[aid][k] is False for k in ['exact_action_binding_unresolved',
                    'required_evidence_unavailable', 'authoritative_source_conflict']), 'Canonical flags changed')
        require(decision['canonical_binding_already_resolved'] is True and
                all(decision[k] is False for k in ['binding_approval_requested', 'binding_applied',
                    'meaning_accepted', 'eligibility_applied', 'canonical_sources_registered',
                    'source_holds_changed']), 'Case acquired authority')
    require(bundle['bundle_sha256'] == sealed_digest(bundle, 'bundle_sha256') and
            all(bundle[k] is False for k in ['accepted', 'canonical_application', 'publication', 'production']),
            'Decision bundle acquired authority')
    actual = data['products']
    require(digest(actual) == digest(replay(a, s)), 'Native held replay differs')
    core = actual['shared_action_core']
    validate_shared_action_core(ROOT, core)
    validate_shared_issue_mapping(ROOT, actual['shared_issue_mapping'], core)
    for action, decision in zip(core['actions'], bundle['cases']):
        require(action['action_meaning_ref'] == decision['meaning_ref'] and
                action['action_core_sha256'] == decision['candidate_core_sha256'], 'Decision subject changed')
    for member in actual['member_projections']:
        validate_member_projection(ROOT, member, core)
        expected = ['Yea', 'Yea', 'Yea', 'Not Voting', 'Yea'] if member['member_id'] == 'F000477' else ['Nay', 'Yea', 'Nay', 'Yea', 'Yea']
        require([x['official_status'] for x in member['actions']] == expected, 'Official choice changed')
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),
            'Held choice produced proposition')
    require(data['proof']['product_sha256'] == {k: digest(v) for k, v in actual.items()} and
            data['proof']['behavioral_update_proof_exercised'] is False, 'Replay proof overclaims')
    return dict(cores=5, official_observations=10, held_episodes=5, propositions=0, sources=25,
                canonical_changes=False, acceptance=False,
                capture=validate_capture(data['capture'], data['bindings'], s),
                floor=validate_floor(pool, data['conformance']))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), packet_files=validate_manifest(),
                         validation=validate()), indent=2))
