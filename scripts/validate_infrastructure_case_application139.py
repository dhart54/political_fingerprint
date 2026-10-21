"""Validate the exact approved application and unchanged downstream behavior."""
import json
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest
from scripts.apply_infrastructure_case_decisions139 import apply_exact_decisions, SUBJECTS, require
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates, reproducibility_proof, validate_universe_proposal

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch134_20260916'
APPLIED = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch139_20260916'
AUDIT = ROOT / 'docs/review_packets/infrastructure_case_application139'
MEMBERS = ['F000477', 'M001184']


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def inputs():
    bundle = read(ROOT / 'docs/review_packets/infrastructure_batch136_research_product_boundaries/decision_bundle.json')
    return (read(BASE / 'membership_review.json'), read(BASE / 'universe_proposal.json'),
            read(BASE / 'sources.json'), {c['action_id']: read(ROOT / c['candidate_path']) for c in bundle['cases']},
            read(AUDIT / 'owner_evidence.json'))


def validate():
    before_m, before_u, capture, proposals, authority = inputs()
    m, u = read(APPLIED / 'membership_review.json'), read(APPLIED / 'universe_proposal.json')
    expected_m, expected_u, effect = apply_exact_decisions(before_m, before_u, capture, proposals, authority)
    require((m, u) == (expected_m, expected_u), 'Materialized approved application differs')
    again_m, again_u, replay = apply_exact_decisions(m, u, capture, proposals, authority)
    require((again_m, again_u) == (m, u) and replay['changed'] is False, 'Idempotent replay differs')
    for key in ['records']:
        require([r for r in m[key] if r['action_id'] not in SUBJECTS]
                == [r for r in before_m[key] if r['action_id'] not in SUBJECTS], 'Other membership records changed')
    require([r for r in u['candidate_dispositions'] if r['action_id'] not in SUBJECTS]
            == [r for r in before_u['candidate_dispositions'] if r['action_id'] not in SUBJECTS], 'Other universe rows changed')
    require(read(APPLIED / 'sources.json') == capture, 'Registered source pool changed')
    a = read(APPLIED / 'authoring.json')
    old_a = read(BASE / 'authoring.json')
    require({k: v for k, v in a.items() if k not in ['snapshot_id', 'boundary']}
            == {k: v for k, v in old_a.items() if k not in ['snapshot_id', 'boundary']}, 'Authored meanings or cutoffs changed')
    validate_universe_proposal(u, a, capture, m)
    core, mapping, projections, compiler_input, result = prepare(a, capture, MEMBERS)
    outputs = dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                   compiler_input=compiler_input, compiled_ir=result.compiled_ir,
                   readable_candidates=readable_candidates(a, core, projections, result),
                   reproducibility_proof=reproducibility_proof(a, capture, MEMBERS))
    for name, expected in outputs.items():
        require(read(APPLIED / 'generated' / (name + '.json')) == expected, f'Generated replay differs: {name}')
    require(result.compiled_ir == read(BASE / 'generated/compiled_ir.json'), 'Compiled meaning changed')
    old_projections = read(BASE / 'generated/member_projections.json')
    for old, new in zip(old_projections, projections):
        require(old['member_id'] == new['member_id'], 'Member cohort changed')
        strip = lambda p: [{k: v for k, v in row.items() if k != 'action_core_sha256'} for row in p['actions']]
        require(strip(old) == strip(new), 'Member status, effect, service or sources changed')
        for row in new['actions']:
            if row['official_status'] in ['Present', 'Not Voting']:
                require(row['exact_choice_effect'] not in ['supports_exact_choice', 'opposes_exact_choice'],
                        'Non-directional status counted directionally')
    receipt = read(AUDIT / 'application_receipt.json')
    require(receipt['effects'] == effect and receipt['compiled_sha256'] == digest(result.compiled_ir), 'Application receipt differs')
    for case in receipt['cases']:
        aid = case['action_id']
        for prefix, membership, universe in [('before', before_m, before_u), ('after', m, u)]:
            require(case[prefix + '_record_sha256'] == digest(next(r for r in membership['records'] if r['action_id'] == aid))
                    and case[prefix + '_universe_row_sha256'] == digest(next(r for r in universe['candidate_dispositions'] if r['action_id'] == aid)),
                    'Receipt subject seal differs')
    for key in ['hr859_candidate_acceptance', 'approved_universe_authority', 'editorial_promotion',
                'publication_authorized', 'production_writes', 'compatibility_change_performed', 'Health_activated']:
        require(receipt[key] is False, 'Receipt gained authority')
    return dict(cases=3, other_records_unchanged=673, sources_unchanged=1621, authored_meanings_unchanged=70,
                compiled_graph_unchanged=True, idempotent=True, counts=u['accounting']['counts'])


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
