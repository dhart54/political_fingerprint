"""Bounded existing-contract application of the October25 exact case approval.

The accepted-nine facet and its seven-action issue mapping are separate from
the unchanged candidate70 research graph. No schema, global promotion or write.
"""
import copy
import json
from collections import Counter
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, adapt_to_semantic_ir_input, validate_shared_action_core, choice_effect,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates, reproducibility_proof

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('docs/editorial/shared_candidates/house_119_infrastructure_batch145_20260916')
PACKET = Path('docs/review_packets/infrastructure_case_application149')
AUTHORITY_SHA = '4a59bc8e4090241626d64a6b32b16e42a09b81351664848b8d591234c892ca82'
LEDGER_SHA = '49561f082d49f3efd504174ce18fe0b232e63f70d534384272040787124565eb'
ADDITIONS_SHA = '2c40b8f40d3440c9d2ff512e2137c006a5a629fb9c775b17fb69b049ae96b545'
BEFORE_MANIFEST_SHA = 'f87ec712ae6329a489d9caf9ec302acb83e4b6c26996fbce1cf131cbe4f76fae'
SUBJECT_INPUT_SHA = 'e599607d3657226d9d04c80931633c231a754eabaa2510e637aee013791de755'
ACCEPT = ['house:119:1:18', 'house:119:1:22', 'house:119:1:28', 'house:119:2:188', 'house:119:2:260',
          'house:119:1:109', 'house:119:1:9', 'house:119:1:10', 'house:119:1:13']
EXCLUDED_ACCEPTED = ['house:119:1:22', 'house:119:1:28']
ADMIT = [x for x in ACCEPT if x not in EXCLUDED_ACCEPTED]
EXCLUDE = EXCLUDED_ACCEPTED + ['house:119:1:12']
BINDINGS = ['house:119:2:188', 'house:119:2:260']
SCOPE = ACCEPT + ['house:119:1:12']
MEMBERS = ['F000477', 'M001184']
BOUNDARY = ('October25 exact case application: nine pinned meanings accepted through a lossless bounded accepted SharedCorpusV1 facet; '
    'seven issue admissions and three exclusions, only two newly resolved bindings. Old70 candidate research and VA147/148 remain unpromoted. '
    'No full-universe, synthesis, publication, production, Health activation or benchmark authority.')
REASONS = {
    'house:119:1:18': 'Owner-approved exact-case inclusion for the mandatory physical siting rule for the authorized monument, preserving its complete construction-location, funding and other qualifications.',
    'house:119:1:22': 'Owner-approved exact-case exclusion for the conditional restricted-fee land-status/use choice, preserving operative utility/access rights. Its exact whole meaning is accepted separately without Infrastructure admission.',
    'house:119:1:28': 'Owner-approved exact-case exclusion for the conditional village trust/property administration choice, preserving community/access/roadway conditions. Its exact whole meaning is accepted separately without Infrastructure admission.',
    'house:119:2:188': 'Owner-approved inclusion of the whole exact modified museum choice, including site/construction, mission, viewpoints and reporting; its failed passage and all literal anomalies/qualifications remain unchanged.',
    'house:119:2:260': 'Owner-approved inclusion of the whole exact Hunt amendment7 pipeline easement/license/operation choice, including State/litigation conditions and the printed subchapterIII/II anomaly without repair.',
    'house:119:1:109': 'Owner-approved exact pre-purchase disclosure/enforcement regulation of defined connected technology. This is not a requirement for device, software or infrastructure deployment and establishes no blanket disclosure rule.',
    'house:119:1:9': 'Owner-approved exact-case system/research-governance inclusion for the disaster-assessment information, planning, interagency assessment, public-reporting and technology-identification regime. It does not deploy assessment technology or implement every recommendation.',
    'house:119:1:10': 'Retain the previously approved exact-case eligibility for the structured public disaster-data service; now admit the separately accepted pinned whole meaning without a website-label rule or broader authority.',
    'house:119:1:13': 'Retain the previously approved exact-case eligibility for power restoration/mitigation coordination; now admit its separately accepted pinned whole meaning, preserving existing eligibility/cost-effectiveness and no-appropriation qualifications.',
    'house:119:1:12': "Owner's new exact-case exclusion: this substantive mandatory GAO evaluation/report is judged insufficient on this record to establish an independent Infrastructure research-governance connection. Preserve the study duty; this is not an athletics-subject, social-research, GAO-study or general-study exclusion. No H.R.28 meaning is accepted.",
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(value, message):
    if not value:
        raise ValueError(message)


def same_json(left, right):
    """Canonical JSON equality preserves boolean, integer and float distinctions."""
    return digest(left) == digest(right)


def convert_literal_core(original):
    """Only existing lifecycle-field renames; all other source payloads persist."""
    require(original['action_id'] in ACCEPT and original['action_core_sha256'] == sealed_digest(original, 'action_core_sha256'),
            'Unapproved or changed candidate core')
    accepted = copy.deepcopy(original)
    accepted['accepted_exact_action_meaning'] = accepted.pop('candidate_exact_action_meaning')
    accepted['accepted_shared_limitations'] = accepted.pop('candidate_shared_limitations')
    accepted['action_core_sha256'] = sealed_digest(accepted, 'action_core_sha256')
    validate_lossless(original, accepted)
    return accepted


def validate_lossless(original, accepted):
    require('candidate_exact_action_meaning' not in accepted and 'candidate_shared_limitations' not in accepted
            and 'accepted_exact_action_meaning' in accepted and 'accepted_shared_limitations' in accepted,
            'Accepted core lifecycle fields are ambiguous')
    require(accepted['action_core_sha256'] == sealed_digest(accepted, 'action_core_sha256'), 'Accepted core seal differs')
    inverse = copy.deepcopy(accepted)
    inverse['candidate_exact_action_meaning'] = inverse.pop('accepted_exact_action_meaning')
    inverse['candidate_shared_limitations'] = inverse.pop('accepted_shared_limitations')
    inverse['action_core_sha256'] = sealed_digest(inverse, 'action_core_sha256')
    require(same_json(inverse, original), 'Accepted lifecycle conversion changed literal/qualification/choice/source payload')


def load_inputs(root=ROOT):
    manifest = read(root / PACKET / 'before_state_manifest.json')
    authority = read(root / PACKET / 'owner_evidence.json')
    ledger = read(root / PACKET / 'approved_subjects.json')
    additions = read(root / PACKET / 'source_additions.json')
    require(digest(manifest) == BEFORE_MANIFEST_SHA and digest(authority) == AUTHORITY_SHA
            and digest(ledger) == LEDGER_SHA and digest(additions) == ADDITIONS_SHA, 'Approval, subject or before-state manifest drift')
    files = {name: read(root / BASE / name) for name in manifest['object_sha256']}
    for name, expected in manifest['object_sha256'].items():
        require(digest(files[name]) == expected, 'Immutable before-state changed: ' + name)
    packets = {};subjects = {};witnesses = {}
    for row in ledger['cases']:
        aid = row['action_id']
        if not row['meaning_accepted']:
            continue
        folder = row['origin_packet']
        if folder not in packets:
            packets[folder] = {n: read(root / folder / n) for n in
                ['authoring.json', 'sources.json', 'generated/shared_action_core.json',
                 'generated/shared_issue_mapping.json', 'generated/member_projections.json']}
        p = packets[folder];source_pool = {s['source_id']: s for s in p['sources.json']['sources']}
        core = next(c for c in p['generated/shared_action_core.json']['actions'] if c['action_id'] == aid)
        authored = next(a for a in p['authoring.json']['actions'] if a['action_id'] == aid)
        require(core['action_core_sha256'] == row['original_core_sha256'] and digest(core) == row['original_core_object_sha256']
                and digest(authored) == row['original_authoring_action_sha256'] and digest(p['sources.json']) == row['source_pool_sha256'],
                'Pinned approved literal subject drift: ' + aid)
        subjects[aid] = {'core': core, 'authoring': authored,
            'mapping': next(m for m in p['generated/shared_issue_mapping.json']['action_mappings'] if m['action_id'] == aid),
            'episode': next(e for e in p['generated/shared_issue_mapping.json']['episodes'] if aid in e['action_ids']),
            'projections': {p['member_id']: next(a for a in p['actions'] if a['action_id'] == aid)
                            for p in p['generated/member_projections.json']}}
        for ref in core['governed_source_identities']:
            source = source_pool[ref['source_id']]
            require(all(source[k] == v for k, v in ref.items())
                    and source['governed_bytes_sha256'] == sealed_digest(source, 'governed_bytes_sha256'), 'Approved source identity drift')
            if source['source_id'] in witnesses:
                require(same_json(witnesses[source['source_id']], source), 'Conflicting approved source version')
            witnesses[source['source_id']] = source
    require(digest(subjects) == SUBJECT_INPUT_SHA and list(subjects) == ACCEPT and len(witnesses) == 67, 'Approved nine/witness cohort differs')
    return files, authority, ledger, additions, subjects, witnesses


def reference(source):
    return {k: source[k] for k in ['source_id', 'url', 'raw_sha256', 'governed_bytes_sha256']}


def build_application(inputs, root=ROOT):
    """Pure materialization: caller owns any disk writes and idempotent readback."""
    files, authority, ledger, additions, subjects, witnesses = inputs
    require(digest(subjects) == SUBJECT_INPUT_SHA, 'Prepared approved subject/episode/member input drift')
    require(digest(authority) == AUTHORITY_SHA and digest(ledger) == LEDGER_SHA and digest(additions) == ADDITIONS_SHA,
            'Unapproved authority or source manifest')
    manifest = read(root / PACKET / 'before_state_manifest.json')
    require(digest(manifest) == BEFORE_MANIFEST_SHA, 'Before-state manifest drift')
    for name, expected in manifest['object_sha256'].items():
        require(digest(files[name]) == expected, 'Prepared before-state input drift: ' + name)
    old_m = files['membership_review.json'];old_u = files['universe_proposal.json'];old_s = files['sources.json']
    require(old_m['review_sha256'] == sealed_digest(old_m, 'review_sha256')
            and old_u['proposal_sha256'] == sealed_digest(old_u, 'proposal_sha256'), 'Before-state seals invalid')
    records = {r['action_id']: r for r in old_m['records']};rows = {r['action_id']: r for r in old_u['candidate_dispositions']}
    require(len(records) == len(rows) == 676 and set(subjects) == set(ACCEPT), 'Bounded action population differs')
    for c in ledger['cases']:
        aid = c['action_id']
        require(digest(records[aid]) == c['before_record_sha256'] and digest(rows[aid]) == c['before_row_sha256'], 'Affected case preimage drift: ' + aid)
        require(records[aid]['required_evidence_unavailable'] is records[aid]['authoritative_source_conflict'] is False,
                'Affected case has an unapproved source block: ' + aid)
        require(records[aid]['exact_action_binding_unresolved'] is (aid in BINDINGS), 'Affected binding state differs: ' + aid)
        if aid in ACCEPT:
            subject = subjects[aid]
            require(subject['core']['action_core_sha256'] == c['original_core_sha256']
                    and digest(subject['core']) == c['original_core_object_sha256']
                    and digest(subject['authoring']) == c['original_authoring_action_sha256'], 'Prepared pinned subject drift: ' + aid)
            for ref in subject['core']['governed_source_identities']:
                witness = witnesses[ref['source_id']]
                require(all(witness[k] == v for k, v in ref.items())
                        and witness['governed_bytes_sha256'] == sealed_digest(witness, 'governed_bytes_sha256'),
                        'Prepared accepted witness drift: ' + aid)
    sources = copy.deepcopy(old_s);pool = {s['source_id']: s for s in sources['sources']}
    require(len(pool) == len(sources['sources']) == 1621, 'Before source population differs')
    for item in additions['sources']:
        sid = item['source_id'];source = witnesses[sid]
        require(sid not in pool and digest(source) == item['source_object_sha256'], 'Unauthorized source addition/version')
        sources['sources'].append(copy.deepcopy(source));pool[sid] = source
    require(len(pool) == 1662 and len(additions['sources']) == 41 and additions['new_object_serialized_bytes'] <= 300000,
            'Source closure cap exceeded')
    for aid in ADMIT:
        for ref in subjects[aid]['core']['governed_source_identities']:
            require(all(pool[ref['source_id']][k] == v for k, v in ref.items()), 'Admission lacks exact approved source closure')

    accepted_actions = [convert_literal_core(subjects[aid]['core']) for aid in ACCEPT]
    accepted_core = {'schema_version': 'shared_action_core_v1', 'artifact_id': 'shared-action-core:house:119:v149',
        'identity_unit': 'exact House legislative action and governed source version',
        'authoritative_for_new_editorial_work': True, 'historical_inputs_rewritten': False,
        'actions': accepted_actions, 'corpus_sha256': digest(accepted_actions)}
    validate_shared_action_core(root, accepted_core)
    accepted_by_id = {a['action_id']: a for a in accepted_actions}
    mappings = [];episodes = []
    for aid in ADMIT:
        row = copy.deepcopy(subjects[aid]['mapping']);row['eligibility']['decision'] = 'accepted'
        require(not row['policy_family_refs'] and not row['policy_trait_refs'], 'Unapproved policy relationship')
        original = subjects[aid]['core'];authored = subjects[aid]['authoring']
        require(row['action_id'] == aid and row['eligibility']['parent_context_used'] is False
                and row['episode_id'] == authored['episode_id']
                and same_json(row['structural_metadata'], {'stage_order': original['session'] * 10000 + original['roll']}),
                'Unapproved action/episode/structural mapping')
        row['mapping_sha256'] = sealed_digest(row, 'mapping_sha256');mappings.append(row)
        episode = copy.deepcopy(subjects[aid]['episode'])
        require(episode['action_ids'] == [aid], 'Unapproved episode aggregation')
        episodes.append(episode)
    mapping = {'schema_version': 'shared_issue_mapping_v1', 'artifact_id': 'accepted-bounded-case149:INFRASTRUCTURE_TECH_TRANSPORT',
        'domain_id': 'INFRASTRUCTURE_TECH_TRANSPORT', 'scope_boundaries': [BOUNDARY],
        'authoritative_for_new_editorial_work': True, 'historical_inputs_rewritten': False,
        'semantic_ir_case_scope': 'full_record', 'action_mappings': mappings, 'episodes': episodes,
        'policy_families': [], 'policy_traits': [], 'trait_relationships': [], 'shared_review_dependencies': [], 'source_render_constraints': []}
    mapping['mapping_sha256'] = digest(mapping)
    projections = []
    for old in files['generated/member_projections.json']:
        p = copy.deepcopy(old);p['artifact_id'] = f"member-action-projection:{p['member_id'].lower()}:house:119:v149"
        p['actions'] = []
        for aid in ADMIT:
            row = copy.deepcopy(subjects[aid]['projections'][p['member_id']])
            clerk = pool['clerk:' + aid.removeprefix('house:')]
            official = clerk['member_records'][p['member_id']]['official_label']
            status = {'Aye': 'Yea', 'No': 'Nay'}.get(official, official)
            require(row['action_id'] == aid and row['official_status'] == status
                    and row['service_status'] == 'in_service' and row['evidence_status'] == 'official_record_resolved'
                    and row['exact_choice_effect'] == choice_effect(status), 'Prepared member observation differs from official source')
            row['action_core_sha256'] = accepted_by_id[aid]['action_core_sha256'];p['actions'].append(row)
        p['projection_sha256'] = sealed_digest(p, 'projection_sha256');projections.append(p)
    accepted_input = adapt_to_semantic_ir_input(root, accepted_core, mapping, projections)
    accepted_result = run_editorial_pipeline(accepted_input)

    m = copy.deepcopy(old_m);u = copy.deepcopy(old_u)
    for r in m['records']:
        aid = r['action_id']
        if aid not in SCOPE:
            continue
        r['rationale'] = REASONS[aid];r['exact_action_binding_unresolved'] = False
        if aid in ADMIT:
            r['disposition'] = 'interpreted_substantive_directional';r['episode_candidate_id'] = subjects[aid]['authoring']['episode_id']
            r['sources'] = [reference(pool[x['source_id']]) for x in subjects[aid]['core']['operative_meaning_source_identities']]
            r.pop('claim_source_map', None);r['claim_source_map_ref'] = 'accepted_cases/source_authoring.json#action_id=' + aid
        else:
            r['disposition'] = 'exact_action_ineligible'
    m['review_sha256'] = sealed_digest(m, 'review_sha256');after_records = {r['action_id']: r for r in m['records']}
    for row in u['candidate_dispositions']:
        aid = row['action_id']
        if aid not in SCOPE:
            continue
        r = after_records[aid]
        row.update(disposition=r['disposition'], reason=r['rationale'], rationale=r['rationale'],
                   issue_boundary_status=r['disposition'], unresolved_reason=None, episode_candidate_id=r['episode_candidate_id'])
        if aid in ADMIT:
            ids = subjects[aid]['core']['semantic_ir_source_ids'];row['sources'] = [reference(pool[sid]) for sid in ids]
            row['exact_action_source_binding']['source_ids'] = ids[:]
        row['exact_action_source_binding']['complete'] = True
        row['review_progress'].update({k: r[k] for k in ['substantive_review_performed', 'exact_action_binding_unresolved', 'required_evidence_unavailable', 'authoritative_source_conflict']})
        row['review_progress']['shared_review_record_sha256'] = digest(r)
    counts = dict(Counter(r['disposition'] for r in u['candidate_dispositions']))
    interpreted = list(old_u['interpretation_action_ids']) + ADMIT
    require(len(set(interpreted)) == 77 and set(old_u['interpretation_action_ids']).isdisjoint(ADMIT), 'Research/accepted admission overlap')
    u.update(proposal_id='full-universe-proposal:f000477:infrastructure:119:20260916:bounded-case149',
        membership_review_sha256=m['review_sha256'], interpretation_action_ids=interpreted, proposed_action_ids=interpreted[:],
        unresolved_action_ids=[r['action_id'] for r in u['candidate_dispositions'] if r['disposition'] in ['pending_interpretation', 'source_unresolved']],
        episode_completeness='70 unchanged candidate research episodes plus7bounded accepted-case episodes; no full676action-universe approval.',
        action_interpretation_authority_basis=BOUNDARY)
    accounting = u['accounting'];accounting.update(counts=counts,
        action_ids_by_disposition={k: [r['action_id'] for r in u['candidate_dispositions'] if r['disposition'] == k] for k in counts},
        substantive_eligible_actions=77, directional_substantive_actions=76, non_directional_substantive_actions=1,
        exact_action_ineligible_actions=127, unresolved_boundary_cases=254, independent_episode_count=77,
        accounting_scope=BOUNDARY)
    accounting['official_source_readiness'].update(ready_substantive_actions=77, substantive_actions=77, pending_package_version_bindings=248)
    u['universe_subject_sha256'] = digest({'subject': u['subject'], 'cutoff': u['cutoff'], 'candidate_records': u['candidate_dispositions']})
    u['proposal_sha256'] = sealed_digest(u, 'proposal_sha256')
    require(counts == dict(procedural_context=199, exact_action_ineligible=127, interpreted_substantive_directional=76,
                          pending_interpretation=248, source_unresolved=6, expressive_nonbinding=19, interpreted_substantive_non_directional=1),
            'Expected exact application counts differ')

    # A changed active source pool justifies replay; none of the old70 is promoted.
    authoring = files['authoring.json'];research_core, research_mapping, research_projections, research_input, research_result = prepare(authoring, sources, MEMBERS)
    research = dict(shared_action_core=research_core, shared_issue_mapping=research_mapping, member_projections=research_projections,
        compiler_input=research_input, compiled_ir=research_result.compiled_ir,
        readable_candidates=readable_candidates(authoring, research_core, research_projections, research_result))
    for name, value in research.items():
        require(same_json(value, files['generated/' + name + '.json']), 'Old70 candidate semantic/member output changed: ' + name)
    research['reproducibility_proof'] = reproducibility_proof(authoring, sources, MEMBERS)
    accepted = dict(shared_action_core=accepted_core, shared_issue_mapping=mapping, member_projections=projections,
        compiler_input=accepted_input, compiled_ir=accepted_result.compiled_ir,
        review_payload=accepted_result.review_payload, presentation_payload=accepted_result.presentation_payload,
        source_authoring={'kind': 'pinned_source_correspondence_only', 'actions': [subjects[aid]['authoring'] for aid in ACCEPT]})
    correspondence = [{'action_id': aid, 'original_core_sha256': subjects[aid]['core']['action_core_sha256'],
        'accepted_core_sha256': accepted_by_id[aid]['action_core_sha256'], 'literal_meaning_sha256': digest(subjects[aid]['core']['candidate_exact_action_meaning']),
        'original_meaning_ref': subjects[aid]['core']['action_meaning_ref'], 'accepted_meaning_ref': accepted_by_id[aid]['action_meaning_ref'],
        'only_lifecycle_fields_renamed': True, 'issue_admitted': aid in ADMIT} for aid in ACCEPT]
    receipt = {'kind': 'bounded_exact_case_application149', 'approval_evidence_sha256': digest(authority),
        'approved_subject_ledger_sha256': digest(ledger), 'source_additions_manifest_sha256': digest(additions),
        'accepted_meaning_ids': ACCEPT[:], 'admitted_action_ids': ADMIT[:], 'excluded_action_ids': EXCLUDE[:],
        'accepted_excluded_meaning_ids': EXCLUDED_ACCEPTED[:], 'newly_resolved_binding_ids': BINDINGS[:],
        'lifecycle_correspondence': correspondence, 'before_membership_sha256': old_m['review_sha256'],
        'after_membership_sha256': m['review_sha256'], 'before_universe_sha256': old_u['proposal_sha256'], 'after_universe_sha256': u['proposal_sha256'],
        'source_objects_before': 1621, 'source_objects_after': 1662, 'new_existing_source_objects_registered': 41,
        'accepted_nine_witness_objects': 67, 'admission_required_witness_objects': 58,
        'before_counts': old_u['accounting']['counts'], 'after_counts': counts, 'other_records_unchanged': 666,
        'research70_semantics_and_members_unchanged': True, 'accepted_nine_corpus_sha256': accepted_core['corpus_sha256'],
        'accepted_seven_compiled_sha256': digest(accepted_result.compiled_ir), 'exact_nine_meaning_acceptance': True,
        'review_scope': 'bounded_partial_record',
        'compiler_case_scope_note': 'full_record means all7supplied actions, not full676domain authority; no public claim is authorized.',
        'public_presentation_prepared': accepted_result.public_presentation_artifact is not None,
        'persistence_proposal_prepared': accepted_result.persistence_proposal is not None,
        'candidate70_or_VA147_148_accepted': False, 'HR28_meaning_accepted': False, 'global_universe_approval': False,
        'synthesis_authorized': False, 'publication_authorized': False, 'production_authorized': False,
        'Health_activation': False, 'source_holds_changed': False, 'new_acquisition': False,
        'cases': [{'action_id': aid, 'before_record_sha256': digest(records[aid]), 'after_record_sha256': digest(after_records[aid]),
                   'before_row_sha256': digest(rows[aid]), 'after_row_sha256': digest(next(r for r in u['candidate_dispositions'] if r['action_id'] == aid)),
                   'meaning_accepted': aid in ACCEPT, 'issue_admitted': aid in ADMIT} for aid in SCOPE]}
    receipt['receipt_sha256'] = digest(receipt)
    return dict(membership=m, universe=u, sources=sources, authoring=copy.deepcopy(authoring), research=research,
                accepted=accepted, receipt=receipt, witnesses=witnesses)


def materialized_payload(state):
    return {k: state[k] for k in ['membership', 'universe', 'sources', 'authoring', 'research', 'accepted', 'receipt']}


def before_payload(inputs):
    files = inputs[0]
    return dict(membership=files['membership_review.json'], universe=files['universe_proposal.json'],
        sources=files['sources.json'], authoring=files['authoring.json'],
        research={name: files['generated/' + name + '.json'] for name in
                  ['shared_action_core', 'shared_issue_mapping', 'member_projections', 'compiler_input',
                   'compiled_ir', 'readable_candidates', 'reproducibility_proof']})


def apply_to_current(current, inputs, root=ROOT):
    """Authenticate both initial and repeated no-write paths against frozen inputs."""
    expected = build_application(inputs, root)
    after = materialized_payload(expected)
    if same_json(current, after):
        return copy.deepcopy(after), {'changed': False, 'scope': SCOPE[:]}
    require(same_json(current, before_payload(inputs)), 'Partial, drifted or unapproved current application state')
    return copy.deepcopy(after), {'changed': True, 'scope': SCOPE[:]}
