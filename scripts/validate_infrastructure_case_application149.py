"""Validate scoped acceptance/application without promoting candidate research."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core, validate_shared_issue_mapping, validate_member_projection,
)
from scripts.apply_infrastructure_case_decisions149 import (
    PACKET, BASE, ACCEPT, ADMIT, EXCLUDE, EXCLUDED_ACCEPTED, BINDINGS, SCOPE, MEMBERS,
    load_inputs, build_application, validate_lossless, materialized_payload, before_payload, apply_to_current, require, same_json,
)
from scripts.prepare_shared_domain_candidate import validate_universe_proposal

P = ROOT / PACKET
A = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch149_20260916'
OUTPUT_MANIFEST_SHA = '8df44a41ad694fd34e56d8a8f9d887dcba60bbd6b2b3769a10381c0670076785'
PRESERVATION_MANIFEST_SHA = 'ca14b52f7a4c983b1ea3e5d16bb8f56cf488c4de4cf46002be5158aeaaa50260'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def lfsha(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def current_state():
    research = {p.stem: read(p) for p in (A / 'generated').glob('*.json')}
    accepted = {p.stem: read(p) for p in (A / 'accepted_cases').glob('*.json')}
    return dict(membership=read(A / 'membership_review.json'), universe=read(A / 'universe_proposal.json'),
        sources=read(A / 'sources.json'), authoring=read(A / 'authoring.json'), research=research,
        accepted=accepted, receipt=read(P / 'application_receipt.json'))


def validate_preservation():
    manifest = read(P / 'preservation_manifest.json')
    require(digest(manifest) == PRESERVATION_MANIFEST_SHA and manifest['manifest_sha256'] == sealed_digest(manifest, 'manifest_sha256'), 'Historical preservation seal differs')
    for name, expected in manifest['files'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT.resolve()) and lfsha(path) == expected, 'Preserved evidence changed: ' + name)
    return len(manifest['files'])


def validate_output_bytes():
    m = read(P / 'output_manifest.json')
    require(digest(m) == OUTPUT_MANIFEST_SHA and m['manifest_sha256'] == sealed_digest(m, 'manifest_sha256'),
            'Frozen output manifest differs')
    for name, expected in m['files'].items():
        path = (ROOT / name).resolve();raw = path.read_bytes().replace(b'\r\n', b'\n')
        require(path.is_relative_to(ROOT.resolve()) and len(raw) == expected['bytes']
                and hashlib.sha256(raw).hexdigest() == expected['lf_sha256'], 'Materialized bytes changed: ' + name)
    return len(m['files'])


def validate_state(state, inputs):
    files, authority, ledger, additions, subjects, witnesses = inputs
    m, u, s = state['membership'], state['universe'], state['sources']
    accepted = state['accepted'];research = state['research'];receipt = state['receipt']
    require(receipt['receipt_sha256'] == sealed_digest(receipt, 'receipt_sha256'), 'Application receipt self-seal differs')
    require(m['review_sha256'] == sealed_digest(m, 'review_sha256') == receipt['after_membership_sha256']
            and u['proposal_sha256'] == sealed_digest(u, 'proposal_sha256') == receipt['after_universe_sha256'], 'Post-state seals differ')
    require(receipt['accepted_meaning_ids'] == ACCEPT and receipt['admitted_action_ids'] == ADMIT
            and receipt['excluded_action_ids'] == EXCLUDE and receipt['accepted_excluded_meaning_ids'] == EXCLUDED_ACCEPTED
            and receipt['newly_resolved_binding_ids'] == BINDINGS and receipt['exact_nine_meaning_acceptance'] is True,
            'Approved acceptance/application cohort differs')
    for k in ['candidate70_or_VA147_148_accepted', 'HR28_meaning_accepted', 'global_universe_approval', 'synthesis_authorized',
              'publication_authorized', 'production_authorized', 'Health_activation', 'source_holds_changed', 'new_acquisition',
              'public_presentation_prepared', 'persistence_proposal_prepared']:
        require(receipt[k] is False, 'Application escalated authority: ' + k)
    require(m['authoritative_for_new_editorial_work'] is False and u['approval_receipt'] is None
            and all(u[k] is False for k in ['full_record_claim', 'synthesis_eligible', 'publication_authorized',
                'episode_acceptance_authorized', 'synthesis_authorized', 'publication_changes', 'production_writes', 'full_issue_universe_closed']),
            'Whole candidate universe promoted')
    # Existing optional authoring argument cannot describe mixed lifecycle cohorts.
    # Validate the same schema/membership contract, then assert their disjoint union.
    validate_universe_proposal(u, capture=s, membership=m)
    old_ids = [c['action_id'] for c in files['generated/shared_action_core.json']['actions']]
    require(set(old_ids).isdisjoint(ACCEPT) and len(old_ids) == 70
            and set(u['interpretation_action_ids']) == set(old_ids) | set(ADMIT)
            and set(u['proposed_action_ids']) == set(u['interpretation_action_ids']), 'Candidate/accepted interpretation union differs')
    require(same_json(state['authoring'], files['authoring.json']), 'Old70 source authoring changed')
    for name in ['shared_action_core', 'shared_issue_mapping', 'member_projections', 'compiler_input', 'compiled_ir', 'readable_candidates']:
        require(same_json(research[name], files['generated/' + name + '.json']), 'Old70 semantic/member artifact changed: ' + name)
    require(research['shared_action_core']['authoritative_for_new_editorial_work'] is False
            and research['shared_issue_mapping']['authoritative_for_new_editorial_work'] is False, 'Candidate70 was accepted')
    validate_shared_action_core(ROOT, research['shared_action_core'])
    validate_shared_issue_mapping(ROOT, research['shared_issue_mapping'], research['shared_action_core'])
    core = accepted['shared_action_core'];mapping = accepted['shared_issue_mapping']
    require(core['authoritative_for_new_editorial_work'] is mapping['authoritative_for_new_editorial_work'] is True
            and 'review_state' not in core and 'review_state' not in mapping
            and [c['action_id'] for c in core['actions']] == ACCEPT
            and [r['action_id'] for r in mapping['action_mappings']] == ADMIT
            and all(same_json(r['eligibility'], {'decision': 'accepted', 'parent_context_used': False}) for r in mapping['action_mappings']),
            'Bounded accepted facet scope or authority differs')
    validate_shared_action_core(ROOT, core);validate_shared_issue_mapping(ROOT, mapping, core)
    core_by_id = {c['action_id']: c for c in core['actions']}
    correspondence = {c['action_id']: c for c in receipt['lifecycle_correspondence']}
    require(set(correspondence) == set(ACCEPT), 'Lifecycle correspondence cohort differs')
    for aid in ACCEPT:
        c = core_by_id[aid];original = subjects[aid]['core'];validate_lossless(original, c)
        relation = correspondence[aid]
        require(relation['original_core_sha256'] == original['action_core_sha256']
                and relation['accepted_core_sha256'] == c['action_core_sha256']
                and relation['literal_meaning_sha256'] == digest(original['candidate_exact_action_meaning'])
                and relation['original_meaning_ref'] == relation['accepted_meaning_ref'] == original['action_meaning_ref']
                and relation['only_lifecycle_fields_renamed'] is True and relation['issue_admitted'] is (aid in ADMIT),
                'Approved origin-to-accepted correspondence changed')
        bound = {r['source_id'] for r in c['operative_meaning_source_identities']}
        for ref in c['governed_source_identities']:
            source = witnesses[ref['source_id']]
            require(all(source[k] == v for k, v in ref.items()), 'Accepted source identity differs')
        for claim in c['claim_source_map']:
            require(claim['source_id'] in bound and claim['passage'] in witnesses[claim['source_id']]['text'],
                    'Accepted claim escaped the exact governed source')
    pool = {source['source_id']: source for source in s['sources']}
    before_pool = {source['source_id']: source for source in files['sources.json']['sources']}
    require(len(pool) == len(s['sources']) == 1662 and same_json(s['sources'][:1621], files['sources.json']['sources']),
            'Old source object changed or source population drift')
    require(set(pool) - set(before_pool) == {r['source_id'] for r in additions['sources']}, 'Unauthorized source import')
    for row in additions['sources']:
        source = pool[row['source_id']]
        require(digest(source) == row['source_object_sha256']
                and source['governed_bytes_sha256'] == sealed_digest(source, 'governed_bytes_sha256'), 'Bounded source addition drift')
    before_records = {r['action_id']: r for r in files['membership_review.json']['records']}
    after_records = {r['action_id']: r for r in m['records']}
    before_rows = {r['action_id']: r for r in files['universe_proposal.json']['candidate_dispositions']}
    after_rows = {r['action_id']: r for r in u['candidate_dispositions']}
    require(len(after_records) == len(after_rows) == 676 and set(after_records) == set(before_records), 'Official action population changed')
    for aid in before_records:
        if aid not in SCOPE:
            require(same_json(before_records[aid], after_records[aid]) and same_json(before_rows[aid], after_rows[aid]), 'Other666record/row changed: ' + aid)
            continue
        r = after_records[aid];old = before_records[aid]
        allowed = {'rationale', 'disposition'} | ({'exact_action_binding_unresolved', 'sources', 'claim_source_map', 'claim_source_map_ref', 'episode_candidate_id'} if aid in ADMIT else set())
        require(same_json({k: v for k, v in old.items() if k not in allowed}, {k: v for k, v in r.items() if k not in allowed}),
                'Approved case changed unrelated source/evidence fields: ' + aid)
        require(r['disposition'] == ('interpreted_substantive_directional' if aid in ADMIT else 'exact_action_ineligible')
                and r['exact_action_binding_unresolved'] is False, 'Approved case disposition/binding differs')
        immutable_row_keys = set(before_rows[aid]) - {'disposition', 'reason', 'rationale', 'issue_boundary_status', 'unresolved_reason',
            'episode_candidate_id', 'sources', 'exact_action_source_binding', 'review_progress'}
        require(all(same_json(after_rows[aid][k], before_rows[aid][k]) for k in immutable_row_keys), 'Official member/action facts changed: ' + aid)
    require(same_json([r for r in m['records'] if r['disposition'] == 'source_unresolved'],
            [r for r in files['membership_review.json']['records'] if r['disposition'] == 'source_unresolved']), 'Six source holds changed')
    require([p['member_id'] for p in accepted['member_projections']] == MEMBERS, 'Accepted member cohort differs')
    for p in accepted['member_projections']:
        validate_member_projection(ROOT, p, core)
        require([r['action_id'] for r in p['actions']] == ADMIT, 'Excluded accepted meaning entered member issue accounting')
        for row in p['actions']:
            original = subjects[row['action_id']]['projections'][p['member_id']]
            require(same_json({k: v for k, v in row.items() if k != 'action_core_sha256'},
                    {k: v for k, v in original.items() if k != 'action_core_sha256'}), 'Original member observation changed')
    for member in accepted['compiled_ir']['members']:
        nv = 1 if member['member_id'] == 'M001184' else 0
        require(member['coverage']['eligible_substantive_actions'] == 7
                and member['coverage']['directional_yes_no_positions'] == 7 - nv
                and member['coverage']['not_voting_actions'] == nv
                and member['coverage']['missing_evidence_actions'] == 0
                and member['coverage']['unresolved_service_actions'] == 0, 'Bounded accepted coverage drift')
        for prop in member['proposition_graph']['propositions']:
            require(set(prop['evidence_action_ids']) <= set(ADMIT), 'Unapproved/excluded case entered accepted graph')
            if member['member_id'] == 'M001184':
                require('house:119:2:188' not in prop['evidence_action_ids'], 'Not Voting became directional evidence')
    return {'accepted_meanings': 9, 'admissions': 7, 'exclusions': 3, 'unchanged_other_records': 666,
            'sources': 1662, 'new_existing_sources': 41, 'pending': 248, 'ineligible': 127, 'source_holds': 6,
            'candidate70_accepted': False, 'publication_authorized': False, 'production_authorized': False}


def validate(state=None, expected=None, inputs=None):
    inputs = load_inputs() if inputs is None else inputs
    current = current_state() if state is None else state
    result = validate_state(current, inputs)
    expected = build_application(inputs) if expected is None else expected
    require(same_json(current, materialized_payload(expected)), 'Actual materialized application differs from frozen-input replay')
    return result


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), output_files=validate_output_bytes(), application=validate()), indent=2))
