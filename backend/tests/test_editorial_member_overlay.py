from copy import deepcopy
from pathlib import Path

import pytest

from backend.app.summaries.editorial_member_overlay import (
    build_member_inference,
    build_member_overlay,
    inference_evidence_view,
)


PUBLICATION = {
    "editorial_status": "human_approval_pending",
    "benchmark_status": "not_promoted",
    "production_eligible": False,
}
SHARED_SET = {
    "episode_set_id": "synthetic-shared-set",
    "version": "1.0.0",
    "episode_map_path": "synthetic/shared.json",
}


def shared_episodes(count=3):
    return [
        {
            "episode_id": f"episode-{index}",
            "independent_evidence": True,
            "relationship": "one shared episode",
            "mechanism_family": f"mechanism-{index}",
            "source_confidence": "high",
        }
        for index in range(1, count + 1)
    ]


def overlay(*, party="D", covered=3, actions=None):
    actions = actions or ["Yea", "Nay", "Yea"]
    trajectories = []
    for index in range(1, 4):
        complete = index <= covered
        trajectories.append({
            "episode_id": f"episode-{index}",
            "rolls": [index],
            "action_signature": [actions[index - 1]],
            "coverage_status": "complete" if complete else "partial",
            "member_trajectory": f"Synthetic trajectory {index}.",
            "practical_policy_direction": f"Synthetic direction {index}.",
            "candidate_theme_tags": ["synthetic-theme"] if complete else [],
            "theme_evidence": [{"theme_id": "synthetic-theme", "rationale": "Synthetic evidence."}] if complete else [],
            "contrary_or_limiting_evidence": [],
            "package_vote_limitations": [],
            "conclusion_effect": {
                "candidate_id": "synthetic-candidate",
                "direction": "strengthens" if complete else "neutral",
                "weight": 2 if complete else 0,
                "rationale": "Synthetic candidate evidence.",
            },
        })
    return build_member_overlay(
        member={"bioguide_id": "X000001", "display_name": "Alex Example", "party": party},
        reviewed_period="synthetic period",
        shared_episode_set=SHARED_SET,
        roll_actions=[
            {
                "roll": index,
                "action": action,
                "counting": True,
                "episode_id": f"episode-{index}",
                "party_majority_action": action,
                "aligned_with_party_majority": True,
            }
            for index, action in enumerate(actions, start=1)
        ],
        episode_trajectories=trajectories,
        publication=PUBLICATION,
    )


def conclusion():
    return {
        "candidate_id": "synthetic-candidate",
        "inference_level": "bounded_pattern",
        "evidence_strength_label": "Synthetic reviewed sample",
        "primary_conclusion": "The structured synthetic evidence supports this bounded candidate.",
        "theme_candidates": [{
            "theme_id": "synthetic-theme",
            "label": "Synthetic theme",
            "finding": "Independent synthetic episodes support the theme.",
            "editorially_defensible": True,
            "minimum_mechanism_diversity": 2,
        }],
        "global_limitations": [],
        "why_conclusion_does_not_go_further": "The sample is deliberately bounded.",
        "future_expansion_rule": "Recompute with expanded evidence.",
        "reviewed_period": "synthetic period",
        "human_review_status": "human_approval_pending",
        "minimum_independent_episodes": 2,
        "insufficient_evidence_conclusion": "Not enough independent synthetic evidence is available.",
        "insufficient_evidence_reason": "Fewer than two episodes are complete.",
    }


def test_party_metadata_cannot_change_inference_when_evidence_is_held_constant():
    democratic = build_member_inference(overlay=overlay(party="D"), shared_episodes=shared_episodes(), conclusion=conclusion())
    republican = build_member_inference(overlay=overlay(party="R"), shared_episodes=shared_episodes(), conclusion=conclusion())
    assert inference_evidence_view(democratic) == inference_evidence_view(republican)


def test_not_voting_is_excluded_and_insufficient_coverage_prevents_inference():
    value = overlay(covered=1, actions=["Yea", "Not Voting", "Not Voting"])
    result = build_member_inference(overlay=value, shared_episodes=shared_episodes(), conclusion=conclusion())
    assert value["coverage"]["substantive_yes_no_actions"] == 1
    assert value["coverage"]["not_voting_actions"] == 2
    assert result["assessment"] == "insufficient_coverage"
    assert result["inference_level"] == "insufficient_evidence"
    assert result["independent_episode_count"] == 1


def test_overlay_rejects_duplicated_shared_measure_facts():
    value = overlay()
    trajectories = deepcopy(value["episode_trajectories"])
    trajectories[0]["bill_title"] = "This belongs in the shared dossier"
    with pytest.raises(ValueError, match="duplicates shared dossier facts"):
        build_member_overlay(
            member=value["member"],
            reviewed_period=value["reviewed_period"],
            shared_episode_set=value["shared_episode_set"],
            roll_actions=value["roll_actions"],
            episode_trajectories=trajectories,
            publication=PUBLICATION,
        )


def test_overlay_enforces_pending_publication_gate():
    with pytest.raises(ValueError, match="production_eligible"):
        build_member_overlay(
            member={"bioguide_id": "X000001", "display_name": "Alex Example"},
            reviewed_period="synthetic period",
            shared_episode_set=SHARED_SET,
            roll_actions=[],
            episode_trajectories=[],
            publication={**PUBLICATION, "production_eligible": True},
        )


def test_generic_overlay_runtime_contains_no_worked_example_or_party_branch():
    source = (Path(__file__).parents[1] / "app/summaries/editorial_member_overlay.py").read_text(encoding="utf-8").lower()
    for forbidden in ("foushee", "aderholt", "massie", "fentanyl", "roll 32", 'party ==', 'party in'):
        assert forbidden not in source
