import importlib.util
import inspect
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "docs/editorial/justice_cross_member_validation_v1"


def load_json(name):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def load_builder():
    path = ROOT / "backend/scripts/build_justice_cross_member_validation.py"
    spec = importlib.util.spec_from_file_location("justice_cross_member_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selected_cohort_vectors_and_complete_coverage():
    expected = {
        "F000477": ["Yea", "Nay", "Nay", "Yea", "Yea", "Nay", "Nay"],
        "A000370": ["Yea", "Nay", "Nay", "Yea", "Yea", "Nay", "Nay"],
        "A000055": ["Nay", "Yea", "Yea", "Yea", "Yea", "Yea", "Yea"],
        "M001184": ["Nay", "Nay", "Yea", "Yea", "Nay", "Yea", "Yea"],
        "B000490": ["Nay", "Yea", "Yea", "Yea", "Yea", "Nay", "Nay"],
        "G000586": ["Nay", "Nay", "Nay", "Nay", "Nay", "Nay", "Nay"],
        "M001217": ["Yea", "Yea", "Yea", "Yea", "Yea", "Yea", "Nay"],
    }
    matrix = load_json("comparison_matrix.json")
    actual = {item["member"]["bioguide_id"]: item["vote_vector"] for item in matrix["members"]}
    assert actual == expected
    assert all(item["coverage"]["substantive_yes_no_actions"] == 7 for item in matrix["members"])
    assert all(item["coverage"]["independent_episodes_complete"] == 5 for item in matrix["members"])


def test_all_eligible_members_are_documented_and_selection_inputs_are_bounded():
    selection = load_json("cohort_selection.json")
    assert selection["counts"] == {"all_considered": 437, "complete_yes_no": 370, "selected": 7}
    assert len(selection["members_considered"]) == selection["counts"]["all_considered"]
    assert "party as a score" in selection["excluded_inputs"]
    assert all(len(item["vote_vector"]) == 7 for item in selection["members_considered"])


def test_shared_research_is_referenced_not_duplicated():
    overlays = load_json("member_overlays.json")["overlays"]
    expected_path = "docs/editorial/valerie_foushee_justice_public_safety_gold_v1/policy_episode_map.json"
    forbidden = {"bill_title", "measure_summary", "primary_purpose", "source_url", "supporter_argument", "opponent_argument"}
    for overlay in overlays:
        assert overlay["shared_episode_set"]["episode_map_path"] == expected_path
        serialized = json.dumps(overlay)
        assert all(f'"{key}"' not in serialized for key in forbidden)


def test_different_vectors_produce_meaningfully_different_trajectories_and_candidates():
    matrix = load_json("comparison_matrix.json")["members"]
    by_id = {item["member"]["bioguide_id"]: item for item in matrix}
    foushee = by_id["F000477"]
    aderholt = by_id["A000055"]
    assert foushee["vote_vector"] != aderholt["vote_vector"]
    assert foushee["episode_trajectories"] != aderholt["episode_trajectories"]
    assert "selective boundary" in foushee["primary_conclusion"]
    assert "reviewed expansions and permanent enforcement mechanisms" in aderholt["primary_conclusion"]
    assert "selective boundary" not in aderholt["primary_conclusion"]


def test_equivalent_vectors_receive_structurally_equivalent_evidence():
    overlays = load_json("member_overlays.json")["overlays"]
    inferences = load_json("inference_candidates.json")["candidates"]
    overlay_by_id = {item["member"]["bioguide_id"]: item for item in overlays}
    inference_by_id = {item["member"]["bioguide_id"]: item for item in inferences}
    foushee_overlay = overlay_by_id["F000477"]
    adams_overlay = overlay_by_id["A000370"]
    assert [item["action_signature"] for item in foushee_overlay["episode_trajectories"]] == [item["action_signature"] for item in adams_overlay["episode_trajectories"]]
    for key in ("candidate_id", "assessment", "support_balance", "independent_episode_count"):
        assert inference_by_id["F000477"][key] == inference_by_id["A000370"][key]
    assert [item["theme_id"] for item in inference_by_id["F000477"]["repeated_cross_episode_themes"]] == [item["theme_id"] for item in inference_by_id["A000370"]["repeated_cross_episode_themes"]]
    assert inference_by_id["F000477"]["member"] != inference_by_id["A000370"]["member"]


def test_fentanyl_stages_count_as_one_episode_for_every_member():
    overlays = load_json("member_overlays.json")["overlays"]
    inferences = load_json("inference_candidates.json")["candidates"]
    for overlay in overlays:
        fentanyl = next(item for item in overlay["episode_trajectories"] if item["episode_id"] == "halt-fentanyl-legislative-path")
        assert fentanyl["rolls"] == [32, 33, 166]
        assert len(fentanyl["action_signature"]) == 3
    assert all(item["independent_episode_count"] == 5 for item in inferences)


def test_changing_a_load_bearing_episode_can_replace_candidate_theme():
    builder = load_builder()
    baseline = dict(zip(builder.SUBSTANTIVE_ROLLS, ["Yea", "Yea", "Yea", "Yea", "Yea", "Yea", "Nay"]))
    changed = {**baseline, 299: "Yea"}
    assert builder._select_pattern(baseline) == "broad_support_safeguard_exception"
    assert builder._select_pattern(changed) == "contested_mixed_record"


def test_contrary_episode_is_preserved_and_can_limit_candidate():
    by_id = {item["member"]["bioguide_id"]: item for item in load_json("comparison_matrix.json")["members"]}
    moskowitz = by_id["M001217"]
    assert moskowitz["vote_vector"][-1] == "Nay"
    assert "specific boundary around the safeguard-repeal proposal" in moskowitz["primary_conclusion"]
    assert moskowitz["evidence_strength_label"] == "Strong reviewed sample with contrary evidence"


def test_copy_has_no_hard_coded_selected_member_names_in_decision_logic():
    builder = load_builder()
    source = inspect.getsource(builder._select_pattern) + inspect.getsource(builder._pattern_spec)
    for name in ("Valerie", "Foushee", "Alma", "Adams", "Aderholt", "Massie", "Bishop", "García", "Moskowitz"):
        assert name not in source


def test_every_artifact_remains_pending_and_production_ineligible():
    for filename in ("member_overlays.json", "inference_candidates.json", "comparison_matrix.json"):
        artifact = load_json(filename)
        assert artifact["publication"] == {
            "editorial_status": "human_approval_pending",
            "benchmark_status": "not_promoted",
            "production_eligible": False,
        }
    production_registry = (ROOT / "frontend/lib/editorialIssueProductionSlices.mjs").read_text(encoding="utf-8")
    for identifier in ("A000370", "A000055", "M001184", "B000490", "G000586", "M001217"):
        assert identifier not in production_registry
