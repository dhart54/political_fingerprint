"""Offline checks for the frozen, unaccepted defense-amendment candidates."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core,
    validate_shared_issue_mapping, validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT / 'docs/review_packets/infrastructure_batch157_defense_amendments'
B = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:'+str(n) for n in [248,249,250,252,257]]
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
            'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = 'a41ba892f72111a33de586015ff093691720f04588f51688b4f0adafe5df1c7f'
PRESERVATION_SHA = '3cc5b0c39f9b152ed53825ef6ec61d43f9d56eb35ac5e92e7b32ee131e625010'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(value, message):
    if not value:
        raise ValueError(message)


def inputs():
    names = dict(authoring='authoring.json', sources='sources.json',
                 preflight='preparation_preflight.json', bundle='decision_bundle.json',
                 retained='retained_sources.json', extents='retained_extent_receipt.json')

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


def validate_prior_branch(index, authoring, core):
    pins = read(P / 'preparation_preflight.json')['prior_non_main_identity_pins'][index]
    expected = [('c6e6df3537ce464abcde22b13401cc7ae878aaf1', 'c095133b5dbc148a59e135e00e5d3e851b4265e0'),
                ('f684d89987498efb335db9c14fdf3da848734de1', '30f154c235954ea9067b84b50e6432ec5eede618')]
    require((pins['commit'], pins['tree']) == expected[index], 'Prior branch pin changed')
    require(digest(authoring) == pins['authoring']['object_sha256'] and
            digest(core) == pins['core']['object_sha256'], 'Frozen prior object changed')
    require([x['action_id'] for x in authoring['actions']] ==
            [x['action_id'] for x in core['actions']] == pins['action_ids'] and
            not set(ACTIONS) & set(pins['action_ids']), 'Prior held identity duplicated')
    return len(pins['action_ids'])


def prose(text):
    return ' '.join(re.sub(r'-[ \t]*\r?\n\s*', '', text).split()).casefold()


def validate_units(authoring, pool, pre):
    numbers = [16,17,7,11,24]
    recorded = ['congressional-record:3838-amend16-roll248-choice155',
                'congressional-record:3838-amend17-roll249-choice156',
                'congressional-record:3838-amend7-roll250-choice158',
                'immigration:wilson252-resumed-recorded223',
                'congressional-record:3838-amend24-roll257-choice160']
    outcomes = ['agreed to', 'agreed to', 'rejected', 'agreed to', 'rejected']
    for action, case, number, sid, outcome in zip(authoring['actions'], pre['cases'], numbers, recorded, outcomes):
        require(action['source_id'] == case['primary_source_id'] and
                action['source_id'] in {x['source_id'] for x in case['record']['sources']} and
                action['stage'] == 'amendment' and action['bill_number'] == 3838 and
                case['amendment_number'] == number, 'Exact amendment source/stage drift')
        text = prose(pool[sid]['text'])
        roll = action['action_id'].split(':')[-1]
        report_refs = re.findall(r'house report\s+119\s*[–—-]\s*(\d+)', text)
        require(f'amendment no. {number}' in text and f'[roll no. {roll}]' in text and
                report_refs and set(report_refs) == {'255'} and
                'so the amendment was '+outcome in text, 'Own designation/recorded result drift')
    target = pool['govinfo:rcp119-8-humanitarian-taiwan']['text']
    target = target[target.index('SEC. 1313.'):target.index('SEC. 1314.')]
    own = next(x for x in authoring['actions'][-1]['claim_source_map']
               if x['source_id'] == 'govinfo:rcp119-8-humanitarian-taiwan')['passage']
    require(own == target and all(x in target for x in ['1323', 'fiscal year 2026',
            'not more than $1,000,000,000', '(1)', '(2)']), 'Exact printed1313target drift')
    report = prose(pool['house-rules:119255-partA-amend24-operative160']['text'])
    require('page 793, beginning line 8, strike section 1313.' in report, 'Exact deletion instruction drift')
    baseline = pool['govinfo:pl118159-sec1323-taiwan-operative151']['text']
    require(all(x in baseline for x in ['fiscal year 2025', '$300,000,000', 'December 31, 2029']),
            'Retained1323funding/termination scope drift')
    return dict(exact_amendments=5, bounded_held_episode=1, parent_bill_completion=False)


def validate_extents(extents, sources):
    require(extents['new_acquisitions'] == extents['new_extractions'] == 0 and
            all(extents[k] is False for k in ['original_pdfs_or_visual_review', 'source_holds_changed',
                'editorial_acceptance', 'production']), 'Retained evidence acquired scope/authority')
    pool = {x['source_id']:x for x in sources['sources']}
    require(len(extents['sources']) == len(pool) == 19, 'Retained extent inventory changed')
    for pin in extents['sources']:
        source = pool[pin['source_id']]
        require(digest(source) == pin['object_sha256'] and source['source_type'] == pin['source_type'] and
                source.get('text_version') == pin['text_version'] and
                len(source.get('text', '')) == pin['text_characters'] and
                source['raw_sha256'] == pin['raw_sha256'], 'Retained source extent/identity drift')
    return dict(retained_objects=19, new_acquisitions=0, new_extractions=0)


def validate(data=None):
    data = inputs() if data is None else data
    # These are frozen reviewed candidate inputs, not a general truth/acceptance engine.
    for key, filename in [('authoring', 'authoring.json'), ('sources', 'sources.json'),
                          ('preflight', 'preparation_preflight.json'), ('bundle', 'decision_bundle.json'),
                          ('retained', 'retained_sources.json'), ('extents', 'retained_extent_receipt.json')]:
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
    require(len(data['retained']['sources']) == 19, 'Retained source count changed')
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
    require(len(pre['prior_prepared_identities']) == 38 and
            not set(ACTIONS) & set(pre['prior_prepared_identities']), 'Prior held preparation duplicated')
    require([x['action_id'] for x in a['actions']] ==
            [x['action_id'] for x in pre['cases']] ==
            [x['action_id'] for x in bundle['cases']] == ACTIONS, 'Case correspondence changed')
    require(a['blocked_episode_ids'] == ['episode:hr3838:119'], 'Hold removed')
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
        expected = ['Nay']*5 if member['member_id'] == 'F000477' else ['Yea']*5
        require([x['official_status'] for x in member['actions']] == expected, 'Official choice changed')
    require(all(not x['proposition_graph']['propositions'] for x in actual['compiled_ir']['members']),
            'Held choice produced proposition')
    proof = read(P/'held_replay_proof.json')
    require(proof['product_sha256'] == {k: digest(v) for k, v in actual.items()} and
            proof['behavioral_update_proof_exercised'] is False, 'Replay proof overclaims')
    return dict(cores=5, official_observations=10, held_episodes=1, propositions=0, sources=19,
                canonical_changes=False, acceptance=False,
                retained=validate_extents(data['extents'], s),
                units=validate_units(a, pool, pre))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), packet_files=validate_manifest(),
                         validation=validate()), indent=2))
