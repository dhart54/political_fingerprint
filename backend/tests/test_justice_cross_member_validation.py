import importlib.util
import inspect
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "docs/editorial/justice_cross_member_validation_v1"


def load_json(name): return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def load_builder():
    path = ROOT / "backend/scripts/build_justice_cross_member_validation.py"
    spec = importlib.util.spec_from_file_location("justice_builder", path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def synthetic(builder, vector, party="D", omit=()):
    actions = {roll: action for roll, action in zip(builder.SUBSTANTIVE_ROLLS, vector) if roll not in omit}
    overlay = builder.build_overlay_from_actions({"bioguide_id": "X1", "display_name": "Alex Example", "party": party}, actions)
    shared = json.loads((ROOT / builder.SHARED_SET["episode_map_path"]).read_text(encoding="utf-8"))["episodes"]
    return overlay, builder.evaluate_overlay(overlay, shared)


def test_selected_cohort_actions_coverage_and_expected_candidates():
    expected = {"F000477": "conditional-guardrail-boundary", "A000370": "conditional-guardrail-boundary", "A000055": "reviewed-enforcement-expansion", "M001184": "police-authority-fentanyl-divide", "B000490": "national-action-dc-boundary", "G000586": "uniform_direction_without_common_policy_rationale", "M001217": "broad-support-safeguard-exception"}
    candidates = load_json("inference_candidates.json")["candidates"]
    assert {item["member"]["bioguide_id"]: item["candidate_id"] for item in candidates} == expected
    overlays = load_json("member_overlays.json")["overlays"]
    assert all(item["coverage"]["substantive_rolls_expected"] == 7 for item in overlays)
    assert all(item["coverage"]["independent_episodes_expected"] == 5 for item in overlays)


def test_identical_actions_receive_equivalent_evidence_and_party_is_descriptive_only():
    builder = load_builder(); vector = ("Yea", "Nay", "Nay", "Yea", "Yea", "Nay", "Nay")
    left_overlay, left = synthetic(builder, vector, "D"); right_overlay, right = synthetic(builder, vector, "R")
    assert [item["theme_evidence"] for item in left_overlay["episode_trajectories"]] == [item["theme_evidence"] for item in right_overlay["episode_trajectories"]]
    for key in ("candidate_id", "assessment", "support_balance", "repeated_cross_episode_themes", "candidate_evaluation"):
        assert left[key] == right[key]


def test_unselected_complete_vector_is_meaningful_and_different_vectors_can_share_candidate():
    builder = load_builder()
    aderholt = ("Nay", "Yea", "Yea", "Yea", "Yea", "Yea", "Yea")
    variant = ("Nay", "Yea", "Yea", "Nay", "Yea", "Yea", "Yea")
    _, first = synthetic(builder, aderholt); _, second = synthetic(builder, variant)
    assert first["candidate_id"] == second["candidate_id"] == "reviewed-enforcement-expansion"
    assert second["primary_conclusion"] and second["candidate_evaluation"]


def test_all_128_complete_yes_no_combinations_evaluate_without_templates():
    builder = load_builder()
    results = []
    for vector in itertools.product(("Yea", "Nay"), repeat=7):
        overlay, inference = synthetic(builder, vector); results.append(inference["candidate_id"])
        assert overlay["coverage"]["substantive_yes_no_actions"] == 7
        assert inference["independent_episode_count"] == 5
    assert len(results) == 128 and len(set(results)) >= 7
    assert results.count("uniform_direction_without_common_policy_rationale") >= 1
    assert "cross-mechanism-opposition" not in results


def test_committed_complete_vector_distribution_matches_generic_evaluation():
    builder = load_builder()
    shared = json.loads((ROOT / builder.SHARED_SET["episode_map_path"]).read_text(encoding="utf-8"))["episodes"]
    assert load_json("complete_vector_distribution.json") == builder.complete_vector_distribution(shared)


def test_uniform_direction_is_descriptive_not_a_substantive_policy_rationale():
    builder = load_builder()
    _, nay = synthetic(builder, ("Nay",) * 7)
    assert nay["candidate_id"] == "uniform_direction_without_common_policy_rationale"
    assert nay["candidate_basis"] == {
        "basis_type": "uniform_action_direction",
        "substantive_theme_ids": [],
        "uniform_action_direction": {"direction": "Nay", "count": 7, "total": 7, "uniform": True},
    }
    assert nay["evidence_strength_label"] == "Uniform opposition across the reviewed proposals"
    assert "does not establish one overarching public-safety philosophy" in nay["primary_conclusion"]
    assert [item["theme_id"] for item in nay["repeated_cross_episode_themes"]] == ["dc-policing-change-opposition"]
    assert [item["episode_id"] for item in nay["notable_one_off_choices"]] == [
        "officer-safety-data-reporting",
        "retired-service-weapon-purchases",
    ]


def test_direction_only_candidate_cannot_become_eligible_by_mechanism_label_substitution():
    builder = load_builder()
    overlay, _ = synthetic(builder, ("Nay",) * 7)
    shared = json.loads((ROOT / builder.SHARED_SET["episode_map_path"]).read_text(encoding="utf-8"))["episodes"]
    changed = [dict(item, mechanism_family=f"renamed-{index}") for index, item in enumerate(shared)]
    inference = builder.evaluate_overlay(overlay, changed)
    assert inference["candidate_id"] == "uniform_direction_without_common_policy_rationale"
    assert inference["candidate_basis"]["substantive_theme_ids"] == []


def test_changing_one_action_changes_only_its_episode_evidence():
    builder = load_builder(); baseline = ("Yea", "Nay", "Nay", "Yea", "Yea", "Nay", "Nay"); changed = list(baseline); changed[2] = "Yea"
    left, _ = synthetic(builder, baseline); right, _ = synthetic(builder, changed)
    differences = [a["episode_id"] for a, b in zip(left["episode_trajectories"], right["episode_trajectories"]) if a["theme_evidence"] != b["theme_evidence"]]
    assert differences == ["retired-service-weapon-purchases"]


def test_removing_load_bearing_roll_removes_candidate_and_keeps_denominators():
    builder = load_builder(); vector = ("Yea", "Nay", "Nay", "Yea", "Yea", "Nay", "Nay")
    overlay, inference = synthetic(builder, vector, omit=(275,))
    assert overlay["coverage"]["substantive_rolls_expected"] == 7
    assert overlay["coverage"]["independent_episodes_expected"] == 5
    assert overlay["coverage"]["independent_episodes_complete"] == 4
    assert inference["candidate_id"] != "conditional-guardrail-boundary"


def test_inverse_actions_generate_competing_episode_evidence_and_fentanyl_counts_once():
    builder = load_builder(); yea, _ = synthetic(builder, ("Yea", "Yea", "Yea", "Yea", "Yea", "Yea", "Yea")); nay, inference = synthetic(builder, ("Nay", "Nay", "Nay", "Nay", "Nay", "Nay", "Nay"))
    yea_last = yea["episode_trajectories"][-1]; nay_last = nay["episode_trajectories"][-1]
    assert {item["theme_id"] for item in yea_last["theme_evidence"]}.isdisjoint({item["theme_id"] for item in nay_last["theme_evidence"]})
    fentanyl = nay["episode_trajectories"][0]
    assert fentanyl["rolls"] == [32, 33, 166] and len(fentanyl["action_signature"]) == 3
    assert inference["independent_episode_count"] == 5


def test_present_not_voting_and_missing_are_excluded_from_support_opposition():
    builder = load_builder(); base = ["Yea"] * 7
    for action in ("Present", "Not Voting"):
        vector = list(base); vector[2] = action; overlay, _ = synthetic(builder, vector)
        episode = next(item for item in overlay["episode_trajectories"] if item["episode_id"] == "retired-service-weapon-purchases")
        assert episode["coverage_status"] == "partial" and episode["theme_evidence"] == []


def test_forbidden_condition_scan_covers_actual_decision_code():
    builder = load_builder()
    evaluator = __import__("backend.app.summaries.editorial_candidate_evaluation", fromlist=["x"])
    decision_source = inspect.getsource(evaluator) + inspect.getsource(builder.evaluate_overlay)
    builder_source = inspect.getsource(builder)
    for forbidden in ("F000477", "A000370", "A000055", "M001184", "B000490", "G000586", "M001217", "party ==", "party in"):
        assert forbidden not in decision_source
    assert "_select_pattern" not in builder_source and "_pattern_spec" not in builder_source
    assert "tuple(actions[roll]" not in builder_source


def test_shared_contract_and_publication_isolation_are_serialized():
    overlays = load_json("member_overlays.json")["overlays"]
    contract = overlays[0]["shared_episode_set"]
    assert contract["expected_substantive_roll_ids"] == [32, 33, 130, 131, 166, 275, 299]
    assert contract["expected_control_roll_ids"] == [160, 161, 267, 268, 290, 291]
    assert len(contract["expected_independent_episode_ids"]) == 5
    for filename in ("member_overlays.json", "inference_candidates.json", "comparison_matrix.json"):
        assert load_json(filename)["publication"] == {"editorial_status": "human_approval_pending", "benchmark_status": "not_promoted", "production_eligible": False}
    registry = (ROOT / "frontend/lib/editorialIssueProductionSlices.mjs").read_text(encoding="utf-8")
    assert all(identifier not in registry for identifier in ("A000370", "A000055", "M001184", "B000490", "G000586", "M001217"))


def test_cohort_roles_and_rationales_are_action_structural_not_party_methodology():
    overlays = load_json("member_overlays.json")["overlays"]
    text = " ".join(f"{item['validation_case']} {item['selection_rationale']}" for item in overlays).lower()
    assert "republican_outlier" not in text and "democratic vector" not in text and "republican vector" not in text


def test_committed_catalog_and_inferences_match_the_generic_evaluator_without_source_retrieval():
    builder = load_builder()
    catalog = load_json("candidate_catalog.json")
    assert catalog["themes"] == builder.THEME_CATALOG
    assert catalog["candidates"] == builder.CANDIDATE_CATALOG

    shared = json.loads((ROOT / builder.SHARED_SET["episode_map_path"]).read_text(encoding="utf-8"))["episodes"]
    actual_by_id = {
        item["member"]["bioguide_id"]: item
        for item in load_json("inference_candidates.json")["candidates"]
    }
    for overlay in load_json("member_overlays.json")["overlays"]:
        expected = builder.evaluate_overlay(overlay, shared)
        actual = dict(actual_by_id[overlay["member"]["bioguide_id"]])
        actual.pop("publication")
        assert actual == expected
