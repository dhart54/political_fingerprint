from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path

from backend.app.summaries.editorial_candidate_evaluation import evaluate_candidates
from backend.app.summaries.editorial_conclusion_synthesis import build_conclusion_model


ROOT = Path(__file__).resolve().parents[2]


def load_builder():
    path = ROOT / "backend/scripts/build_justice_cross_member_validation.py"
    spec = importlib.util.spec_from_file_location("conclusion_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shared_episodes(builder):
    return json.loads((ROOT / builder.SHARED_SET["episode_map_path"]).read_text(encoding="utf-8"))["episodes"]


def inference(builder, vector, *, name="Alex Example", party="D", shared=None, traits=None):
    overlay = builder.build_overlay_from_actions(
        {"bioguide_id": "X1", "display_name": name, "party": party},
        dict(zip(builder.SUBSTANTIVE_ROLLS, vector)),
    )
    return evaluate_candidates(
        overlay=overlay,
        shared_episodes=shared or shared_episodes(builder),
        theme_catalog=builder.THEME_CATALOG,
        candidate_catalog=builder.CANDIDATE_CATALOG,
        trait_contract=traits or builder.POLICY_TRAIT_CONTRACT,
    )


def test_all_128_vectors_produce_bounded_propositions_and_routes():
    builder = load_builder()
    routes = set()
    archetypes = set()
    for vector in itertools.product(("Yea", "Nay"), repeat=7):
        result = inference(builder, vector)
        model = result["conclusion_model"]
        report = result["compression_report"]
        routes.add(result["review_route"])
        archetypes.add(model["archetype"])
        assert result["primary_conclusion"] == model["public_conclusion"]
        assert report["individually_named_episode_count"] <= 2
        assert report["public_word_count"] <= 80
        assert result["review_route"] in {
            "standard_generation_pass",
            "sampled_audit_candidate",
            "human_exception_required",
            "blocked",
        }
        if model["archetype"] in {
            "substantive_repeated_pattern",
            "selective_or_conditional_pattern",
            "policy_mechanism_divide",
        }:
            assert model["thesis_proposition"]["policy_dimension_present"]
    assert "uniform_direction_without_common_policy_throughline" in archetypes
    assert {"standard_generation_pass", "sampled_audit_candidate", "human_exception_required"} <= routes


def test_identity_party_episode_order_and_opaque_labels_do_not_change_meaning():
    builder = load_builder()
    vector = ("Nay",) * 7
    baseline = inference(builder, vector)
    mutated_identity = inference(builder, vector, name="Jordan Placeholder", party="R")
    reversed_shared = list(reversed(shared_episodes(builder)))
    opaque_shared = [
        {**item, "mechanism_family": f"opaque-{index}", "practical_question": f"Question {index}"}
        for index, item in enumerate(reversed_shared)
    ]
    reordered = inference(builder, vector, shared=reversed_shared)
    opaque = inference(builder, vector, shared=opaque_shared)
    for result in (mutated_identity, reordered, opaque):
        assert result["candidate_id"] == baseline["candidate_id"]
        assert result["conclusion_model"]["archetype"] == baseline["conclusion_model"]["archetype"]
        assert result["conclusion_model"]["supporting_policy_clusters"] == baseline["conclusion_model"]["supporting_policy_clusters"]
    assert "Jordan Placeholder" in mutated_identity["primary_conclusion"]
    assert "Alex Example" in baseline["primary_conclusion"]


def test_load_bearing_trait_mutation_changes_only_trait_dependent_synthesis():
    builder = load_builder()
    vector = ("Nay",) * 7
    baseline = inference(builder, vector)
    changed = deepcopy(builder.POLICY_TRAIT_CONTRACT)
    changed["policy_clusters"]["implementation_safeguards_research_reporting"]["trait_ids"] = ["unmapped_trait"]
    mutated = inference(builder, vector, traits=changed)
    assert baseline["conclusion_model"]["contrast_proposition"]
    assert mutated["conclusion_model"]["contrast_proposition"] is None
    assert mutated["review_route"] == "human_exception_required"
    assert baseline["candidate_id"] == mutated["candidate_id"]
    assert baseline["primary_conclusion"] != mutated["primary_conclusion"]


def test_direction_and_ontology_are_independent_inputs():
    builder = load_builder()
    all_nay = inference(builder, ("Nay",) * 7)
    split = inference(builder, ("Nay", "Nay", "Yea", "Yea", "Nay", "Yea", "Yea"))
    assert all_nay["conclusion_model"]["archetype"] != split["conclusion_model"]["archetype"]

    changed = deepcopy(builder.POLICY_TRAIT_CONTRACT)
    changed["cluster_relationships"] = []
    same_vector_changed_ontology = inference(builder, ("Nay",) * 7, traits=changed)
    assert all_nay["conclusion_model"]["action_direction"] == same_vector_changed_ontology["conclusion_model"]["action_direction"]
    assert all_nay["primary_conclusion"] != same_vector_changed_ontology["primary_conclusion"]


def test_existing_economy_ontology_uses_the_same_issue_neutral_composer():
    roll_actions = [
        {"roll": 50, "action": "Nay", "counting": True},
        {"roll": 100, "action": "Nay", "counting": True},
        {"roll": 156, "action": "Nay", "counting": True},
        {"roll": 182, "action": "Nay", "counting": True},
        {"roll": 281, "action": "Nay", "counting": True},
        {"roll": 285, "action": "Nay", "counting": True},
    ]
    trajectories = [
        {"episode_id": "budget_framework_hconres14", "rolls": [50, 100]},
        {"episode_id": "sba_loan_eligibility_hr2966", "rolls": [156]},
        {"episode_id": "milcon_va_hr3944", "rolls": [182]},
        {"episode_id": "government_funding_hr5371", "rolls": [281, 285]},
    ]
    traits = {
        "action_traits": {
            "50": {"traits": ["funding_framework"]},
            "100": {"traits": ["funding_framework"]},
            "156": {"traits": ["program_eligibility_restriction"]},
            "182": {"traits": ["appropriations_package"]},
            "281": {"traits": ["government_funding_package"]},
            "285": {"traits": ["government_funding_package"]},
        },
        "policy_clusters": {
            "funding_frameworks_and_packages": {
                "reader_phrase": "proposals creating or revising funding frameworks and packages",
                "trait_ids": ["funding_framework", "appropriations_package", "government_funding_package"],
            },
            "program_eligibility": {
                "reader_phrase": "a proposal restricting program eligibility",
                "trait_ids": ["program_eligibility_restriction"],
            },
        },
        "cluster_relationships": [{
            "cluster_ids": ["funding_frameworks_and_packages", "program_eligibility"],
            "relationship": "contrasts",
            "basis": "funding design differs from program eligibility",
        }],
    }
    candidate = {
        "conclusion_archetype": "uniform_direction_without_common_policy_throughline",
        "proposition_spec": {
            "policy_cluster_ids": ["funding_frameworks_and_packages", "program_eligibility"],
            "reader_label_concept": "Consistent opposition without an overarching economic philosophy",
            "boundary_proposition": {"role": "boundary", "policy_domain_label": "economic", "public_text": ""},
        },
    }
    model = build_conclusion_model(
        member_name="Foushee",
        roll_actions=roll_actions,
        complete_trajectories=trajectories,
        candidate=candidate,
        selected_theme_ids=[],
        trait_contract=traits,
    )
    assert model["archetype"] == "uniform_direction_without_common_policy_throughline"
    assert model["compression_report"]["individually_named_episode_count"] == 0
    assert model["compression_report"]["source_episode_count"] == 4
    assert "funding frameworks and packages" in model["public_conclusion"]
    assert "program eligibility" in model["public_conclusion"]
    assert "economic policy throughline" in model["public_conclusion"]


def test_core_composer_has_no_member_party_issue_or_exact_vector_prose_branch():
    core = (
        ROOT / "backend/app/summaries/editorial_conclusion_synthesis.py"
    ).read_text(encoding="utf-8").lower()
    evaluator = (
        ROOT / "backend/app/summaries/editorial_candidate_evaluation.py"
    ).read_text(encoding="utf-8").lower()
    for forbidden in (
        "g000586",
        "garcía",
        "foushee",
        "massie",
        "fentanyl",
        "police",
        "economy",
        "party ==",
        "exact vector",
        "tuple(actions",
    ):
        assert forbidden not in core
        assert forbidden not in evaluator
