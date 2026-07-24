from copy import deepcopy
import json
from pathlib import Path

import pytest

from backend.app.summaries.editorial_candidate_selection import (
    assert_selection_locked,
    select_blind_candidate,
    select_featured_episode_ids,
)
from backend.scripts.build_blind_editorial_pipeline_validation import (
    BUILD_IDENTIFIER,
    REFERENCE_MEMBER_IDS,
    STARTING_COMMIT,
    build,
)
from backend.scripts.build_justice_cross_member_validation import EPISODE_ROLLS


ROOT = Path(__file__).resolve().parents[2]
COHORT_PATH = ROOT / "docs/editorial/justice_cross_member_validation_v1/member_overlays.json"
ARTIFACT_PATH = ROOT / "docs/editorial/blind_editorial_pipeline_validation_v1"


def overlays():
    return json.loads(COHORT_PATH.read_text(encoding="utf-8"))["overlays"]


def select(values=None):
    return select_blind_candidate(
        overlays=values or overlays(),
        reference_member_ids=REFERENCE_MEMBER_IDS,
        episode_rolls=EPISODE_ROLLS,
        starting_commit=STARTING_COMMIT,
        build_identifier=BUILD_IDENTIFIER,
    )


def test_selection_excludes_references_incomplete_and_identical_vectors():
    value = select()
    by_id = {item["member_id"]: item for item in value["candidates"]}
    assert "existing_reference_fixture" in by_id["F000477"]["exclusion_reasons"]
    assert "existing_reference_fixture" in by_id["M001184"]["exclusion_reasons"]
    assert "identical_to_reference_fixture:F000477" in by_id["A000370"]["exclusion_reasons"]

    changed = deepcopy(overlays())
    bishop = next(item for item in changed if item["member"]["bioguide_id"] == "B000490")
    next(item for item in bishop["roll_actions"] if item["counting"])["action"] = "Not Voting"
    by_id = {item["member_id"]: item for item in select(changed)["candidates"]}
    assert "incomplete_seven_action_record" in by_id["B000490"]["exclusion_reasons"]


def test_selection_is_party_blind_deterministic_and_locked_before_generation():
    baseline = select()
    changed = deepcopy(overlays())
    for index, overlay in enumerate(changed):
        overlay["member"]["party"] = ["D", "R", "I"][index % 3]
    assert select(changed)["selected_member"] == baseline["selected_member"]
    assert select(list(reversed(overlays()))) == baseline
    assert baseline["selected_member"]["member_id"] == "G000586"

    first = json.loads((ARTIFACT_PATH / "first_generated_candidate.json").read_text(encoding="utf-8"))
    assert_selection_locked(baseline, first)
    rebound = deepcopy(first)
    rebound["selected_member"]["member_id"] = "M001217"
    with pytest.raises(ValueError, match="cannot change"):
        assert_selection_locked(baseline, rebound)


def test_generation_uses_authoritative_seven_action_five_episode_contract():
    selection, generated = build()
    assert generated["selected_member"]["member_id"] == selection["selected_member"]["member_id"]
    assert generated["overlay"]["coverage"]["substantive_rolls_expected"] == 7
    assert generated["overlay"]["coverage"]["substantive_yes_no_actions"] == 7
    assert generated["overlay"]["coverage"]["independent_episodes_expected"] == 5
    assert generated["overlay"]["coverage"]["independent_episodes_complete"] == 5
    fentanyl = next(
        item for item in generated["overlay"]["episode_trajectories"]
        if item["episode_id"] == "halt-fentanyl-legislative-path"
    )
    assert fentanyl["rolls"] == [32, 33, 166]
    assert len(fentanyl["action_signature"]) == 3
    assert set(generated["inference"]["episode_references"]) == set(EPISODE_ROLLS)
    assert len(generated["featured_episode_ids"]) == 5
    assert generated["publication"] == {
        "editorial_status": "human_approval_pending",
        "benchmark_status": "not_promoted",
        "production_eligible": False,
    }
    inference = generated["inference"]
    assert inference["candidate_id"] == "uniform_direction_without_common_policy_rationale"
    assert inference["evidence_strength_label"] == "Uniform opposition across the reviewed proposals"
    assert inference["primary_conclusion"] == (
        "Across the reviewed record, García of Illinois voted Nay on every substantive proposal. "
        "That opposition extended both to proposals expanding enforcement or police authority and to "
        "proposals adding safeguards, research access, or reporting, so the uniform vote direction does "
        "not reveal one consistent public-safety policy throughline."
    )
    assert inference["reader_facing_label"] == "Uniform opposition without a common policy throughline"
    assert inference["review_route"] == "sampled_audit_candidate"
    assert [item["theme_id"] for item in inference["repeated_cross_episode_themes"]] == ["dc-policing-change-opposition"]


def test_featured_selection_uses_episode_evidence_and_never_procedural_controls():
    _, generated = build()
    selected = select_featured_episode_ids(
        overlay=generated["overlay"],
        inference=generated["inference"],
    )
    assert selected == generated["featured_episode_ids"]
    assert set(selected) == set(EPISODE_ROLLS)
    assert not set(selected).intersection({160, 161, 267, 268, 290, 291})


def test_generic_selection_and_generation_sources_have_no_member_party_or_vector_branch():
    paths = [
        ROOT / "backend/app/summaries/editorial_candidate_selection.py",
        ROOT / "backend/app/summaries/editorial_candidate_evaluation.py",
        ROOT / "backend/app/summaries/editorial_member_overlay.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for forbidden in (
        "g000586",
        "garcía",
        "selected candidate ==",
        "party ==",
        "tuple(actions",
        "exact seven-action",
    ):
        assert forbidden not in source
