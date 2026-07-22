from copy import deepcopy
from pathlib import Path

from backend.app.summaries.editorial_inference import build_editorial_inference


def episode(identifier, mechanism, direction="strengthens", weight=2, themes=(), repeated=""):
    return {
        "episode_id": identifier,
        "independent": True,
        "relationship_to_repeated_stages": repeated,
        "mechanism_family": mechanism,
        "member_trajectory": f"Reviewed trajectory for {identifier}",
        "practical_policy_direction": f"Reviewed direction for {identifier}",
        "candidate_theme_tags": list(themes),
        "theme_evidence": [
            {"theme_id": theme, "rationale": f"{identifier} supplies reviewed evidence for {theme}."}
            for theme in themes
        ],
        "contrary_or_limiting_evidence": [],
        "package_vote_limitations": [],
        "source_confidence": "high",
        "reviewed_period": "synthetic period",
        "conclusion_effect": {
            "candidate_id": "conditional-action",
            "direction": direction,
            "weight": weight,
            "rationale": f"{identifier} {direction} the candidate.",
        },
    }


def conclusion():
    return {
        "candidate_id": "conditional-action",
        "inference_level": "bounded_pattern",
        "evidence_strength_label": "Synthetic candidate",
        "primary_conclusion": "The reviewed actions condition support on specified safeguards.",
        "theme_candidates": [{
            "theme_id": "reviewed-safeguards",
            "label": "Reviewed safeguards",
            "finding": "Supported action paired with reviewed safeguards across different mechanisms.",
            "editorially_defensible": True,
            "minimum_mechanism_diversity": 2,
        }],
        "global_limitations": ["Synthetic evidence is deliberately bounded."],
        "why_conclusion_does_not_go_further": "The sample does not cover every relevant action.",
        "future_expansion_rule": "Recompute from the expanded episode annotations.",
        "reviewed_period": "synthetic period",
        "human_review_status": "human_approval_pending",
    }


def test_future_unconstrained_actions_can_weaken_or_replace_candidate():
    baseline = [episode("a", "reporting", themes=("reviewed-safeguards",)), episode("b", "licensing", themes=("reviewed-safeguards",))]
    initial = build_editorial_inference(baseline, conclusion())
    expanded = baseline + [episode("c", "penalties", "weakens", 3), episode("d", "search authority", "weakens", 3)]
    revised = build_editorial_inference(expanded, conclusion())
    assert initial["assessment"] == "candidate_supported_by_current_sample"
    assert revised["assessment"] == "candidate_not_supported_by_current_sample"
    assert revised["support_balance"] < initial["support_balance"]


def test_more_evidence_based_actions_strengthen_candidate():
    baseline = [episode("a", "reporting", themes=("reviewed-safeguards",)), episode("b", "licensing", themes=("reviewed-safeguards",))]
    strengthened = build_editorial_inference(baseline + [episode("c", "research access", weight=3, themes=("reviewed-safeguards",))], conclusion())
    assert strengthened["support_balance"] == 7
    assert len(strengthened["supporting_independent_episodes"]) == 3


def test_removing_two_episodes_changes_cross_episode_theme_strength():
    episodes = [
        episode("a", "reporting", themes=("reviewed-safeguards",)),
        episode("b", "licensing", themes=("reviewed-safeguards",)),
        episode("c", "oversight", themes=("reviewed-safeguards",)),
    ]
    full = build_editorial_inference(episodes, conclusion())
    reduced = build_editorial_inference(episodes[:1], conclusion())
    assert len(full["repeated_cross_episode_themes"]) == 1
    assert len(reduced["repeated_cross_episode_themes"]) == 0
    assert len(reduced["one_off_or_unproven_themes"]) == 1


def test_repeated_stages_do_not_increase_episode_breadth():
    item = episode("a", "reporting", repeated="three actions within one episode")
    result = build_editorial_inference([item], conclusion())
    assert result["independent_episode_count"] == 1
    assert len(result["within_episode_trajectories"]) == 1


def test_one_off_is_not_automatically_a_repeated_pattern():
    result = build_editorial_inference([episode("a", "reporting", themes=("reviewed-safeguards",))], conclusion())
    assert not result["repeated_cross_episode_themes"]
    assert result["one_off_or_unproven_themes"][0]["theme_id"] == "reviewed-safeguards"


def test_contrary_evidence_is_preserved_in_rationale():
    item = episode("a", "reporting")
    item["contrary_or_limiting_evidence"] = ["A reviewed action points in another direction."]
    item["package_vote_limitations"] = ["The action covered several provisions."]
    result = build_editorial_inference([item], conclusion())
    assert [value["text"] for value in result["contrary_or_limiting_evidence"][:2]] == [
        "A reviewed action points in another direction.", "The action covered several provisions."
    ]


def test_generic_helper_contains_no_worked_example_conditions():
    source = (Path(__file__).parents[1] / "app/summaries/editorial_inference.py").read_text(encoding="utf-8").lower()
    for forbidden in ("foushee", "justice_public_safety", "fentanyl", "firearm", "d.c.", "roll 32"):
        assert forbidden not in source
