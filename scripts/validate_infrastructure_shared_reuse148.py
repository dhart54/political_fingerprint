"""Replay held shared successors and the bounded human-inventory extension.

No acquisition, historical corpus restoration, editorial acceptance or application.
Selected historical objects were authenticated against immutable Git at preparation;
this offline replay verifies the frozen selections, not an entire origin corpus.
"""
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest, candidate_update_impact
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

PACKET = ROOT / 'docs/review_packets/infrastructure_batch148_shared_reuse'
INDEX = ROOT / 'docs/review_packets/infrastructure_human_decisions_20261021/decision_index.json'
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch145_20260916'
VA = ROOT / 'docs/review_packets/infrastructure_batch147_va_candidates'
HEAD147 = '323343335855b0b3729bb02111637e735a777eda'
ACTIONS = ['house:119:2:180', 'house:119:2:78', 'house:119:2:101']
MEMBERS = ['F000477', 'M001184']
OUTPUTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections', 'compiler_input', 'compiled_ir', 'readable_candidates']
FALSE_FLAGS = ['canonical_state_changed', 'source_registered', 'semantic_acceptance', 'publication_authorized',
               'production_authorized', 'issue_propositions_authorized', 'six_source_holds_changed']
PACKET_MANIFEST_SHA = '00cdec5a8876394955f851b3a84e33e68da473dfeacca859840dc63dc332304d'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(value, message):
    if not value:
        raise ValueError(message)


def lf_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def validate_preservation():
    m = read(PACKET / 'packet_manifest.json')
    require(digest(m) == PACKET_MANIFEST_SHA, 'Frozen packet manifest differs')
    actual = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file() and p.name != 'packet_manifest.json'}
    require(actual == set(m['files']), 'Packet cohort differs')
    for name, expected in m['files'].items():
        path = (PACKET / name).resolve()
        require(path.is_relative_to(PACKET.resolve()) and path.stat().st_size < 195000
                and lf_hash(path) == expected, 'Packet transport changed: ' + name)
    preservation = read(PACKET / 'preservation_manifest.json')
    for name, expected in preservation['preserved_files'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT.resolve()) and lf_hash(path) == expected, 'Preserved input changed: ' + name)
    return len(preservation['preserved_files'])


def validate_sources(capture=None):
    s = read(PACKET / 'sources.json') if capture is None else capture
    expected = read(PACKET / 'decision_bundle.json')['source_pool_sha256']
    require(digest(s) == expected, 'Frozen retained source pool differs')
    pool = {x['source_id']: x for x in s['sources']}
    require(len(pool) == len(s['sources']) == 15, 'Retained source cohort differs')
    require(all(sealed_digest(x, 'governed_bytes_sha256') == x['governed_bytes_sha256'] for x in pool.values()),
            'Governed source seal differs')
    origins = read(PACKET / 'retained_origins.json')
    require(origins['new_acquisition'] is origins['historical_artifacts_rewritten'] is origins['new_bill_research'] is False,
            'Reuse provenance gained new authority')
    require([x['action_id'] for x in origins['cases']] == ACTIONS, 'Origin cohort differs')
    bound = set()
    for c in origins['cases']:
        for sid, expected in c['selected_source_objects'].items():
            require(digest(pool[sid]) == expected, 'Selected historical object changed')
            bound.add(sid)
    require(bound == set(pool), 'Unattributed source entered reuse pool')
    return s


def minimally_neutral_actions():
    import copy
    actions = copy.deepcopy(read(PACKET / 'historical_authoring.json')['actions'])
    actions[0]['meaning'] = actions[0]['meaning'].replace(
        'Defined clinical infrastructure establishes proposed Health membership, within a mixed medical/admin/site project rather than wholly direct treatment spending.',
        'This is a mixed medical/admin/site construction project rather than wholly direct treatment spending.')
    actions[1]['meaning'] = actions[1]['meaning'].replace('The direct household support explains proposed Health & Social Policy membership. ', '')
    actions[2]['short_description'] = 'Establishing the whole DC Commission and public-space maintenance program'
    actions[2]['compact_description'] = ('H.R. 5103 would establish a DC Commission for the listed law-enforcement/immigration recommendations and review, '
        'alongside a separate Interior public-space maintenance and qualified monument-restoration program, with both sections ending January 2, 2029. '
        'The whole choice retains its law-limited authorities and dated executive baseline.')
    actions[2]['meaning'] = actions[2]['meaning'].replace('they are whole-package context, not independently attributed Immigration component choices.',
        'they remain parts of the same whole Commission/program choice, not separate component votes.')
    return actions


def validate_reuse(authoring):
    require(authoring['actions'] == minimally_neutral_actions(), 'Whole source-qualified reuse changed beyond explicit neutralization')
    for a in authoring['actions']:
        prose = '\n'.join([a['meaning'], a['short_description'], a['compact_description'], *a['limitations']]).casefold()
        require(not any(x in prose for x in ['foushee', 'massie', 'f000477', 'm001184', 'health membership', 'health & social policy membership']),
                'Shared meaning contains member or issue-membership interpretation')


def validate_index(index=None):
    i = read(INDEX) if index is None else index
    previous = read(PACKET / 'previous_human_decision_index.json')
    require(len(i['cases']) == 17 and i['cases'][:12] == previous['cases'], 'Original twelve human subjects changed')
    require(i['index_sha256'] == sealed_digest(i, 'index_sha256') and i['previous_index_sha256'] == previous['index_sha256']
            and i['original_twelve_cases_sha256'] == digest(previous['cases']), 'Inventory continuity seal differs')
    require(i['existing_independent_review_attribution'][:-1] == previous['existing_independent_review_attribution'],
            'Prior independent attribution changed')
    for k in ['semantic_acceptance', 'canonical_application_authorized', 'publication_authorized', 'production_authorized', 'Health_activation']:
        require(i[k] is False, 'Inventory gained authority')
    records = {r['action_id']: r for r in read(BASE / 'membership_review.json')['records']}
    rows = {r['action_id']: r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions']}
    for c in i['cases']:
        aid = c['action_id']
        require(c['current_record_sha256'] == digest(records[aid]) and c['current_universe_row_sha256'] == digest(rows[aid]),
                'Inventory current145 preimage changed')
        require(c['accepted_by_this_index'] is c['application_authorized_by_this_index'] is False, 'Inventory case gained authority')
        require(c['current_disposition'] == records[aid]['disposition']
                and c['canonical_binding_unresolved'] is records[aid]['exact_action_binding_unresolved'], 'Inventory canonical status drift')
    for name, expected in i['candidate_file_pins'].items():
        require(lf_hash(ROOT / name) == expected, 'Inventory candidate file changed')
    bundle = read(VA / 'decision_bundle.json');cores = read(VA / 'generated/shared_action_core.json')['actions']
    authoring = read(VA / 'authoring.json')['actions']
    meaning_lines = [n + 1 for n, line in enumerate((VA / 'authoring.json').read_text(encoding='utf-8').splitlines())
                     if '"meaning":' in line]
    prefix = 'https://github.com/dhart54/political_fingerprint/blob/' + HEAD147 + '/' + VA.relative_to(ROOT).as_posix() + '/'
    for n, (c, original, core, authored) in enumerate(zip(i['cases'][12:], bundle['cases'], cores, authoring)):
        require(c['action_id'] == original['action_id'] and c['candidate_core_sha256'] == core['action_core_sha256']
                and c['action_id'] == core['action_id'] == authored['action_id']
                and c['bundle_canonical_sha256'] == digest(bundle) and c['bundle_seal'] == bundle['bundle_sha256']
                and c['prior_reviewed_case_sha256'] == original['candidate_sha256']
                and c['canonical_binding_unresolved'] is True, 'VA decision subject drift')
        require(c['member_observations'] == {m: r['official_label'] for m, r in original['actual_official_member_records'].items()},
                'VA official member facts changed')
        require(c['material_counterevidence'] == original['strongest_case_specific_counterevidence']
                and c['eligibility_choice'] == original['requested_content_bound_decision']
                and c['text_binding_choice'] and c['authored_meaning_choice'], 'VA separate decision/counterevidence boundary changed')
        require(c['meaning_pointer'] == '/actions/' + str(n)
                and c['sealed_meaning_link'] == prefix + 'authoring.json#L' + str(meaning_lines[n])
                and c['sealed_bundle_link'] == prefix + 'decision_bundle.json'
                and c['sealed_core_link'] == prefix + 'generated/shared_action_core.json'
                and c['shared_successor_proposal_link'] == prefix + 'shared_successor_proposals.json',
                'VA exact action/pointer/immutable packet link binding differs')
    review = i['existing_independent_review_attribution'][-1]
    require(review['checkpoint'] == 147 and review['reviewed_head'] == HEAD147
            and review['report_sha256'] == '9086bf1f1609c7ac779faa7b0b1563d5eb74cd69ea49019ceb4c0067340db8d3'
            and [r['run_id'] for r in review['hosted_runs']] == [40230733163, 40230733110]
            and all(r['result'] == 'success' for r in review['hosted_runs']), 'VA review/CI attribution differs')
    return 17


def validate(authoring=None, bundle=None, outputs=None):
    a = read(PACKET / 'authoring.json') if authoring is None else authoring
    b = read(PACKET / 'decision_bundle.json') if bundle is None else bundle
    require(all(b[k] is False for k in FALSE_FLAGS), 'Candidate gained authority')
    require(b['bundle_sha256'] == sealed_digest(b, 'bundle_sha256') and b['authoring_sha256'] == digest(a), 'Candidate subject seal differs')
    require([x['action_id'] for x in a['actions']] == ACTIONS == [x['action_id'] for x in b['cases']]
            and a['blocked_episode_ids'] == [x['episode_id'] for x in a['actions']], 'Cohort or holds changed')
    validate_reuse(a);sources = validate_sources()
    core, mapping, projections, inputs, result = prepare(a, sources, MEMBERS)
    expected = dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                    compiler_input=inputs, compiled_ir=result.compiled_ir,
                    readable_candidates=readable_candidates(a, core, projections, result))
    actual = {k: read(PACKET / 'generated' / (k + '.json')) for k in OUTPUTS} if outputs is None else outputs
    require(digest(actual) == digest(expected), 'Typed held replay changed')
    origins = read(PACKET / 'retained_origins.json')['cases']
    old_authoring = read(PACKET / 'historical_authoring.json')['actions'];old_core = read(PACKET / 'historical_cores.json')['actions']
    successor = read(PACKET / 'shared_successor_proposals.json')
    require(all([x['action_id'] for x in cohort] == ACTIONS
                for cohort in [old_authoring, old_core, successor['cases']]), 'Historical/successor cohort changed')
    require(successor['historical_replacement_applied'] is successor['semantic_acceptance'] is False, 'Historical replacement gained authority')
    records = {r['action_id']: r for r in read(BASE / 'membership_review.json')['records']}
    rows = {r['action_id']: r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions']}
    pool = {s['source_id']: s for s in sources['sources']}
    for c, origin, authored, before, after, version in zip(b['cases'], origins, old_authoring, old_core, core['actions'], successor['cases']):
        aid = c['action_id']
        require(digest(authored) == origin['historical_authoring_sha256']
                and before['action_core_sha256'] == sealed_digest(before, 'action_core_sha256') == origin['historical_core_sha256'],
                'Historical selected meaning/core changed')
        require(c['candidate_sha256'] == sealed_digest(c, 'candidate_sha256')
                and c['current_record_sha256'] == digest(records[aid]) == origin['current_record_sha256']
                and c['current_row_sha256'] == digest(rows[aid]) == origin['current_row_sha256']
                and records[aid]['disposition'] == 'pending_interpretation'
                and records[aid]['exact_action_binding_unresolved'] is True, 'Current145 candidate preimage changed')
        require(c['eligibility_accepted'] is c['meaning_accepted'] is c['canonical_binding_changed'] is False
                and c['candidate_core_sha256'] == after['action_core_sha256']
                and c['official_member_records'] == pool['clerk:' + aid.removeprefix('house:')]['member_records'], 'Case gained authority or member drift')
        changes = {k: {'before_sha256': digest(before.get(k)), 'after_sha256': digest(after.get(k))}
                   for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
        require(version['action_id'] == aid and version['changed_fields'] == changes
                and version['old_core_sha256'] == before['action_core_sha256'] and version['new_core_sha256'] == after['action_core_sha256']
                and version['old_meaning_ref'] == before['action_meaning_ref'] and version['new_meaning_ref'] == after['action_meaning_ref']
                and version['historical_replacement_applied'] is version['semantic_acceptance'] is False, 'Explicit successor delta changed')
    require(successor['dependency_impact'] == candidate_update_impact({'actions': old_core}, core, projections, result.compiled_ir),
            'Limited shared dependency impact changed')
    require(result.validation['proposition_count'] == 0 and result.validation['source_render_constraint_count'] == 1
            and expected['readable_candidates']['production_eligible'] is False, 'Held candidate gained analytical authority')
    require([r['official_status'] for r in projections[0]['actions']] == ['Yea', 'Nay', 'Nay']
            and [r['official_status'] for r in projections[1]['actions']] == ['Not Voting', 'Yea', 'Yea']
            and projections[1]['actions'][0]['exact_choice_effect'] == 'resolved_non_directional', 'Official status/effect changed')
    for m in result.compiled_ir['members']:
        require(m['review_route'] == 'blocked' and not m['proposition_graph']['propositions'], 'Episode hold lost')
        require(m['coverage']['directional_yes_no_positions'] == (2 if m['member_id'] == 'M001184' else 3), 'Not Voting entered direction')
    return dict(actions=3, shared_cores=3, member_observations=6, not_voting=1, sources_reused=15,
                new_acquisition=False, propositions=0, canonical_mutation=False, semantic_acceptance=False)


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), candidate=validate(), human_subjects=validate_index()), indent=2))
