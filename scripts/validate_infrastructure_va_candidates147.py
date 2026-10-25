"""Offline held VA candidate replay, shared-version audit and preservation.

Checkpoint144 supplies previously authenticated captures and selected extents.
This validator verifies their frozen bytes; it neither recaptures nor claims a
new visual review, semantic acceptance, current-law certification or application.
"""
import json
import sys
import hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest, candidate_update_impact
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

PACKET = ROOT / 'docs/review_packets/infrastructure_batch147_va_candidates'
CHECKPOINT = ROOT / 'docs/review_packets/infrastructure_batch144_va_research_administration'
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch145_20260916'
ACTIONS = ['house:119:1:89', 'house:119:1:90', 'house:119:1:115', 'house:119:1:133', 'house:119:2:49']
MEMBERS = ['F000477', 'M001184']
OUTPUTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections', 'compiler_input', 'compiled_ir', 'readable_candidates']
AUTHORITY = ['canonical_state_changed', 'source_registered', 'semantic_acceptance', 'publication_authorized',
             'production_authorized', 'issue_propositions_authorized', 'six_source_holds_changed']
PACKET_MANIFEST_SHA = 'cb36f08c610fe4965d962c1d92fa11cc8fb3767c37f145f790b50d315e4ce594'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(value, message):
    if not value:
        raise ValueError(message)


def lf_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def validate_preservation():
    packet = read(PACKET / 'packet_manifest.json')
    require(digest(packet) == PACKET_MANIFEST_SHA
            and packet['manifest_sha256'] == sealed_digest(packet, 'manifest_sha256'), 'Frozen packet manifest differs')
    actual = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*')
              if p.is_file() and p.name != 'packet_manifest.json'}
    require(actual == set(packet['files']), 'Frozen packet cohort differs')
    for name, expected in packet['files'].items():
        path = (PACKET / name).resolve()
        require(path.is_relative_to(PACKET.resolve()) and path.stat().st_size < 195000
                and lf_hash(path) == expected, 'Frozen packet file differs: ' + name)
    m = read(PACKET / 'preservation_manifest.json')
    require(m['manifest_sha256'] == sealed_digest(m, 'manifest_sha256'), 'Preservation seal differs')
    # Immutable subjects include every checkpoint file, the current membership
    # snapshot and original Health files, not merely the selected five records.
    for name, expected in m['preserved_files'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT.resolve()), 'Preservation path escaped')
        require(lf_hash(path) == expected, 'Preserved file changed: ' + name)
    require(m['checkpoint_manifest_sha256'] == read(CHECKPOINT / 'checkpoint_manifest.json')['manifest_sha256']
            == '029ff5b2b3261d7497187c9c5cf571993e1cd3a1e505cf71132ff1d91ce6f909',
            'Checkpoint identity differs')
    return len(m['preserved_files'])


def validate_sources(capture=None):
    s = read(CHECKPOINT / 'sources.json') if capture is None else capture
    expected = read(PACKET / 'decision_bundle.json')['source_pool_sha256']
    require(digest(s) == expected, 'Frozen checkpoint source pool differs')
    pool = {x['source_id']: x for x in s['sources']}
    require(len(pool) == len(s['sources']) == 39, 'Source cohort differs')
    require(all(x['governed_bytes_sha256'] == sealed_digest(x, 'governed_bytes_sha256') for x in pool.values()),
            'Governed source differs')
    for number, roll in [(586, 89), (1039, 90), (530, 115), (1286, 133), (980, 49)]:
        prefix = f'govinfo:context144:hr{number}_'
        require('postpon' in pool[prefix + 'question_postponement']['text']
                and f'(H.R. {number})' in pool[prefix + f'resumption_roll{roll}']['text']
                and f'[Roll No. {roll}]' in pool[prefix + f'resumption_roll{roll}']['text']
                and 'bill, as amended, was passed' in pool[prefix + 'passage_result']['text'],
                'Own amended-passage sequence differs')
    return s


def validate_bundle(bundle, authoring):
    require(bundle['bundle_sha256'] == sealed_digest(bundle, 'bundle_sha256'), 'Bundle seal differs')
    require(all(bundle[k] is False for k in AUTHORITY), 'Candidate gained authority')
    require([x['action_id'] for x in bundle['cases']] == ACTIONS
            == [x['action_id'] for x in authoring['actions']], 'Case cohort differs')
    require(bundle['authoring_sha256'] == digest(authoring), 'Authored subject changed')
    require(authoring['blocked_episode_ids'] == [x['episode_id'] for x in authoring['actions']], 'Episode holds differ')
    for c in bundle['cases']:
        require(c['candidate_sha256'] == sealed_digest(c, 'candidate_sha256'), 'Case seal differs')
        require(c['eligibility_accepted'] is c['meaning_accepted'] is c['canonical_binding_changed'] is False,
                'Case acquired acceptance/application')
        require(c['strongest_case_specific_counterevidence'] and c['requested_content_bound_decision'],
                'Case-specific decision boundary lost')


def validate_member_neutral(authoring):
    for a in authoring['actions']:
        fields = [a['meaning'], a['short_description'], a['compact_description'], *a['limitations'], *a['choice_meanings'].values()]
        require(not any(token in '\n'.join(fields).casefold() for token in
                        ['foushee', 'massie', 'f000477', 'm001184', 'health membership', 'infrastructure membership']),
                'Shared core contains member/issue eligibility interpretation')


def validate_successors(core, projections, compiled, proposal=None):
    p = read(PACKET / 'shared_successor_proposals.json') if proposal is None else proposal
    require(p['historical_Health_changed'] is p['semantic_acceptance'] is False, 'Successor gained authority')
    require([x['action_id'] for x in p['cases']] == ACTIONS, 'Successor cohort differs')
    oldcores = []
    for case, new in zip(p['cases'], core['actions']):
        old = read(CHECKPOINT / ('historical_shared_' + new['action_id'].replace(':', '_') + '.json'))['existing_Health_candidate_core']
        oldcores.append(old)
        changed = {k: dict(before_sha256=digest(old.get(k)), after_sha256=digest(new.get(k)))
                   for k in old.keys() | new.keys() if old.get(k) != new.get(k)}
        require(case['mode'] == 'explicit_unaccepted_shared_successor_proposal'
                and case['before_core_sha256'] == old['action_core_sha256']
                and case['after_core_sha256'] == new['action_core_sha256']
                and case['before_meaning_ref'] == old['action_meaning_ref']
                and case['after_meaning_ref'] == new['action_meaning_ref'] != old['action_meaning_ref']
                and case['changed_fields'] == changed and case['reason']
                and case['historical_Health_changed'] is case['successor_accepted'] is False,
                'Shared successor proposal differs')
    require(p['dependency_impact'] == candidate_update_impact(dict(actions=oldcores), core, projections, compiled),
            'Shared version dependency impact differs')


def validate(authoring=None, bundle=None, outputs=None):
    a = read(PACKET / 'authoring.json') if authoring is None else authoring
    b = read(PACKET / 'decision_bundle.json') if bundle is None else bundle
    validate_bundle(b, a)
    validate_member_neutral(a)
    s = validate_sources()
    core, mapping, projections, inputs, result = prepare(a, s, MEMBERS)
    expected = dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                    compiler_input=inputs, compiled_ir=result.compiled_ir,
                    readable_candidates=readable_candidates(a, core, projections, result))
    actual = {k: read(PACKET / 'generated' / (k + '.json')) for k in OUTPUTS} if outputs is None else outputs
    require(digest(actual) == digest(expected), 'Typed candidate replay differs')
    validate_successors(core, projections, result.compiled_ir)
    require(result.validation['proposition_count'] == 0 and result.validation['source_render_constraint_count'] == 1
            and core['authoritative_for_new_editorial_work'] is mapping['authoritative_for_new_editorial_work'] is False
            and expected['readable_candidates']['production_eligible'] is False, 'Held candidate gained authority')
    records = {r['action_id']: r for r in read(BASE / 'membership_review.json')['records']}
    rows = {r['action_id']: r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions']}
    counts = Counter(r['disposition'] for r in records.values())
    require(len(records) == 676 and counts['pending_interpretation'] == 258
            and counts['exact_action_ineligible'] == 124 and counts['source_unresolved'] == 6,
            'Current145 accounting differs')
    pool = {x['source_id']: x for x in s['sources']}
    for c, shared in zip(b['cases'], core['actions']):
        aid = c['action_id']
        require(c['governed_before_record_sha256'] == digest(records[aid])
                and c['governed_before_row_sha256'] == digest(rows[aid])
                and records[aid]['exact_action_binding_unresolved'] is True
                and records[aid]['disposition'] == 'pending_interpretation', 'Current145 case preimage differs')
        require(c['candidate_action_core_sha256'] == shared['action_core_sha256'], 'Case shared core differs')
        require(c['actual_official_member_records'] == pool['clerk:' + aid.removeprefix('house:')]['member_records'],
                'Official member witness differs')
    require([x['official_status'] for x in projections[0]['actions']] == ['Yea'] * 5
            and [x['official_status'] for x in projections[1]['actions']] == ['Yea'] * 4 + ['Not Voting']
            and projections[1]['actions'][-1]['exact_choice_effect'] == 'resolved_non_directional',
            'Official member status/effect differs')
    for m in result.compiled_ir['members']:
        require(m['review_route'] == 'blocked' and not m['proposition_graph']['propositions'], 'Candidate hold lost')
        require(m['coverage']['directional_yes_no_positions'] == (4 if m['member_id'] == 'M001184' else 5)
                and m['coverage']['not_voting_actions'] == (1 if m['member_id'] == 'M001184' else 0),
                'Not Voting entered directional accounting')
    return dict(actions=5, cores=5, official_observations=10, not_voting_observations=1,
                reused_checkpoint_sources=39, new_captures=0, issue_propositions=0,
                canonical_state_changed=False, semantic_acceptance=False)


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), candidate=validate()), indent=2))
