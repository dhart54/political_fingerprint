"""Offline checks for the frozen, unaccepted transport-governance candidates."""
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

P = ROOT / 'docs/review_packets/infrastructure_batch155_transport_governance'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:103', 'house:119:1:112', 'house:119:1:114',
           'house:119:2:306', 'house:119:2:311']
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
            'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = '0520c7c41d01f0aff94a1349a7fe4682e85bb3fa82658f2b2db8439245e9a965'
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


def extract(raw):
    parser = HTMLText()
    parser.feed(raw.decode('utf-8'))
    return ' '.join(' '.join(parser.parts).split())


def inputs():
    names = dict(authoring='authoring.json', sources='sources.json',
                 preflight='preparation_preflight.json', bundle='decision_bundle.json',
                 capture='capture_receipt.json', bindings='new_source_bindings.json',
                 retained='retained_sources.json', proof='held_replay_proof.json')
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


def validate_capture(capture=None, bindings=None, sources=None):
    capture = read(P / 'capture_receipt.json') if capture is None else capture
    bindings = read(P / 'new_source_bindings.json') if bindings is None else bindings
    sources = read(P / 'sources.json') if sources is None else sources
    limits = {'locators': 8, 'timeout_seconds': 45, 'response_bytes': 4194304,
              'total_bytes': 12582912, 'attempts_per_locator': 1, 'redirects_allowed': False}
    require(digest(capture['limits']) == digest(limits), 'Prospective source limits changed')
    attempts = capture['attempts']
    require(len(attempts) == 4 and len({x['url'] for x in attempts}) == 4,
            'Capture attempts repeated or omitted')
    require(attempts[0]['result'] == 'closed_failure' and
            attempts[0]['error'] == 'HTTP Error 400: Bad Request', 'Closed API locator changed')
    captured = attempts[1:]
    require([x['file'] for x in captured] == ['captures/90fr643.html',
            'captures/90fr642.html', 'captures/42usc7543-2024.html'], 'Capture identity/order changed')
    pool = {x['source_id']: x for x in sources['sources']}
    require(len(bindings['sources']) == 3, 'New source bindings changed')
    total = 0
    for e in captured:
        require(e['status'] == 200 and e['result'] == 'captured' and
                e['url'] == e['final_url'] and e['url'].startswith('https://www.govinfo.gov/'),
                'Capture status/redirect/host changed')
        raw = (P / e['file']).read_bytes()
        require(type(e['bytes']) is int and 0 < len(raw) == e['bytes'] <= 4194304 and
                hashlib.sha256(raw).hexdigest() == e['sha256'], 'Raw capture drift/cap')
        total += len(raw)
        binding = next(x for x in bindings['sources'] if x['raw_path'] ==
                       (P / e['file']).relative_to(ROOT).as_posix())
        source = pool[binding['source_id']]
        require(source['url'] == e['url'] and source['raw_sha256'] == e['sha256'] and
                source['text'] == extract(raw), 'Raw extraction/source identity drift')
    require(total == 39380 <= limits['total_bytes'], 'Total capture bytes changed')
    return dict(successful=3, closed_failures=1, raw_bytes=total)


def validate(data=None):
    data = inputs() if data is None else data
    # These are frozen reviewed candidate inputs, not a general truth/acceptance engine.
    for key, filename in [('authoring', 'authoring.json'), ('sources', 'sources.json'),
                          ('preflight', 'preparation_preflight.json'),
                          ('bundle', 'decision_bundle.json'), ('retained', 'retained_sources.json'),
                          ('bindings', 'new_source_bindings.json'), ('proof', 'held_replay_proof.json')]:
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
    require(len(pool) == len(s['sources']) == 19, 'Source inventory changed')
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
    require(not set(ACTIONS) & set(pre['prior_prepared_identities']), 'Prior held preparation duplicated')
    require([x['action_id'] for x in a['actions']] ==
            [x['action_id'] for x in pre['cases']] ==
            [x['action_id'] for x in bundle['cases']] == ACTIONS, 'Case correspondence changed')
    require(a['blocked_episode_ids'] == ['episode:hr973:119', 'episode:hjres89:119',
            'episode:hjres88:119', 'episode:hjres210:119', 'episode:hjres213:119'], 'Hold removed')
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
        expected = ['Yea', 'Nay', 'Nay', 'Nay', 'Nay'] if member['member_id'] == 'F000477' else ['Nay', 'Yea', 'Yea', 'Yea', 'Yea']
        require([x['official_status'] for x in member['actions']] == expected, 'Official choice changed')
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),
            'Held choice produced proposition')
    require(data['proof']['product_sha256'] == {k: digest(v) for k, v in actual.items()} and
            data['proof']['behavioral_update_proof_exercised'] is False, 'Replay proof overclaims')
    return dict(cores=5, official_observations=10, held_episodes=5, propositions=0, sources=19,
                canonical_changes=False, acceptance=False,
                capture=validate_capture(data['capture'], data['bindings'], s))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), packet_files=validate_manifest(),
                         validation=validate()), indent=2))
