import copy
import pytest

from backend.app.semantic_ir.compiler import compile_behavioral_candidate_ir, SemanticCompilerInputError
from backend.app.semantic_ir.trajectory_comparability import digest
from backend.app.editorial_presentations.limitation_treatment import public_caveats
from backend.tests import test_full_record_behavioral_semantic_ir_candidates as behavioral_cases


def comparable_case():
    payload = behavioral_cases.BehavioralSemanticIrCandidateTests._generic_input()
    for episode in payload['episodes']:
        episode.update(policy_proposition='Whether to renew the same ban on transfers above the stated threshold.')
        episode['actions'][0].update(accepted_exact_action_meaning=episode['policy_proposition'],
            accepted_interpretation_record_subject_sha256='a'*64, source_references=['synthetic-official-text'])
    candidate = payload['proposition_candidates'][0]
    candidate['trajectory_change']['bounded_change_description']='Member direction changed on renewal of the same transfer restriction.'
    basis = dict(comparison_id='synthetic-same-restriction', accepted=True,
        basis_kind='same_policy_mechanism', common_policy_choice=payload['episodes'][0]['policy_proposition'],
        comparison_scope='bounded_choice', change_dimension='member_direction',
        limitations=['Only the same restriction is compared; motive is not established.'],
        observations=[dict(episode_id=e['episode_id'],episode_content_sha256=digest(e),
                           action_ids=e['primary_action_ids'],policy_proposition=e['policy_proposition'],choice_scope='bounded_choice') for e in payload['episodes']])
    candidate['comparison_binding']={'comparison_id':basis['comparison_id'],'content_sha256':digest(basis)}
    return payload, {basis['comparison_id']:basis}


def test_supported_same_mechanism_with_lineage_and_limits_passes():
    payload, trusted = comparable_case()
    graph=compile_behavioral_candidate_ir(payload,trusted_comparisons=trusted)
    proposition=graph['proposition_graph']['propositions'][0]
    assert proposition['direction']=='mixed'
    assert proposition['evidence_action_ids']==['action-after','action-before']
    assert proposition['comparison_binding']==payload['proposition_candidates'][0]['comparison_binding']


@pytest.mark.parametrize('basis_kind',['annual_appropriations','annual_bill_family','same_issue','chronology','opposite_direction'])
def test_structural_bases_fail_even_when_marked_accepted(basis_kind):
    payload,trusted=comparable_case();basis=next(iter(trusted.values()))
    basis['basis_kind']=basis_kind
    payload['proposition_candidates'][0]['comparison_binding']['content_sha256']=digest(basis)
    with pytest.raises(SemanticCompilerInputError,match='cannot establish comparability'):
        compile_behavioral_candidate_ir(payload,trusted_comparisons=trusted)


def test_authored_comparability_prose_or_self_asserted_authority_cannot_bypass():
    payload,trusted=comparable_case()
    payload['comparability_basis']='Same annual appropriations family with opposite votes.'
    payload['accepted_comparisons']=trusted
    with pytest.raises(SemanticCompilerInputError,match='separately trusted'):
        compile_behavioral_candidate_ir(payload)


def test_whole_package_cannot_borrow_component_comparison():
    payload,trusted=comparable_case();basis=next(iter(trusted.values()))
    for episode,observation in zip(payload['episodes'],basis['observations']):
        observation['choice_scope']='whole_package'
        observation['episode_content_sha256']=digest(episode)
    payload['proposition_candidates'][0]['comparison_binding']['content_sha256']=digest(basis)
    with pytest.raises(SemanticCompilerInputError,match='component-level'):
        compile_behavioral_candidate_ir(payload,trusted_comparisons=trusted)


def test_materially_different_package_cannot_reuse_accepted_comparison():
    payload,trusted=comparable_case()
    payload['episodes'][1]['policy_proposition']='A materially different annual package with different restrictions.'
    with pytest.raises(SemanticCompilerInputError,match='exact accepted episode'):
        compile_behavioral_candidate_ir(payload,trusted_comparisons=trusted)


def test_comparison_requires_limits_and_exact_action_sources():
    payload,trusted=comparable_case();basis=next(iter(trusted.values()))
    basis['limitations']=[]
    payload['proposition_candidates'][0]['comparison_binding']['content_sha256']=digest(basis)
    with pytest.raises(SemanticCompilerInputError,match='limitations'):
        compile_behavioral_candidate_ir(payload,trusted_comparisons=trusted)


def test_treatment_covers_source_and_never_extracts_words():
    source='The reviewed interpretation remains a candidate because implementation depends on incomplete official amendment text.'
    assert public_caveats([dict(source_text=source,treatment='public',public_copy='Official amendment text is incomplete.')],source_caveats=[source])==['Official amendment text is incomplete.']
    with pytest.raises(ValueError,match='each exact source'):
        public_caveats([],source_caveats=[source])
    with pytest.raises(ValueError,match='authored public copy'):
        public_caveats([dict(source_text=source,treatment='public',public_copy='')],source_caveats=[source])


def test_new_pipeline_cannot_promote_structural_stages_to_trajectory():
    import json
    from pathlib import Path
    from backend.app.semantic_ir.compiler import project_compiler_input
    from backend.app.semantic_ir.pipeline import run_editorial_pipeline, replay_accepted_reference
    cases=json.loads((Path(__file__).resolve().parents[2]/'docs/semantic_ir/accepted/development_cases.json').read_text(encoding='utf-8'))['cases']
    case=next(c for c in cases if c['case_id']=='semir-dev-01-economy-funding-stages')
    with pytest.raises(SemanticCompilerInputError,match='separately trusted substantive comparison'):
        run_editorial_pipeline(project_compiler_input(case))
    # Explicit historical replay neither revises the accepted fixture nor grants
    # new comparability. New commissioning still fails above.
    assert replay_accepted_reference(case).validation['member_count']==1
    changed=copy.deepcopy(case)
    changed['shared_semantics']['episodes'][0]['episode_id'] += '-new-authoring'
    with pytest.raises(SemanticCompilerInputError,match='exact frozen accepted reference'):
        replay_accepted_reference(changed)


def test_receipt_overlay_projects_complete_treatments_and_rejects_conflict():
    from backend.app.editorial_presentations.reviewed_record import overlay_reviewed_actions, GovernedReceiptProjectionError
    source='The reviewed interpretation remains a candidate because implementation depends on incomplete official amendment text.'
    raw={'canonical_action_id':'house:119:1:1','position':'nay'}
    receipt={'caveats':[source],'limitation_treatments':[dict(source_text=source,treatment='public',public_copy='Official amendment text is incomplete.')]}
    reviewed={**raw,'governed_receipt_projection':receipt}
    result=overlay_reviewed_actions({'evidence':[raw]},[reviewed],domain='TEST')
    assert result['evidence'][0]['governed_receipt_projection']['public_caveats']==['Official amendment text is incomplete.']
    assert 'public_caveats' not in receipt
    receipt['public_caveats']=[]
    with pytest.raises(GovernedReceiptProjectionError,match='conflict'):
        overlay_reviewed_actions({'evidence':[raw]},[reviewed],domain='TEST')
