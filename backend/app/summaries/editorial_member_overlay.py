"""Generic review-only member overlays for shared editorial episode research.

The overlay carries only member-varying recorded actions, trajectories, candidate
evidence, coverage, and review metadata. Shared measure and roll-stage facts stay
in the referenced episode set and are joined only while computing an inference.
Party metadata is deliberately never passed into inference computation.
"""

from __future__ import annotations

from copy import deepcopy

from backend.app.summaries.editorial_inference import build_editorial_inference


VALID_ACTIONS = {"Yea", "Nay", "Present", "Not Voting"}
VALID_COVERAGE = {"complete", "partial", "missing"}
FORBIDDEN_OVERLAY_FACT_KEYS = {
    "bill_title",
    "measure_summary",
    "primary_purpose",
    "source_url",
    "supporter_argument",
    "opponent_argument",
    "legislative_history",
}


def build_member_overlay(
    *,
    member: dict,
    reviewed_period: str,
    shared_episode_set: dict,
    roll_actions: list[dict],
    episode_trajectories: list[dict],
    publication: dict,
) -> dict:
    """Validate and normalize one member's overlay on a shared episode set."""
    normalized_actions = [_normalize_action(item) for item in roll_actions]
    rolls = [item["roll"] for item in normalized_actions]
    if len(rolls) != len(set(rolls)):
        raise ValueError("member overlay contains duplicate roll actions")

    normalized_trajectories = [_normalize_trajectory(item) for item in episode_trajectories]
    episode_ids = [item["episode_id"] for item in normalized_trajectories]
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("member overlay contains duplicate episode trajectories")

    substantive = [item for item in normalized_actions if item["counting"]]
    yes_no = [item for item in substantive if item["action"] in {"Yea", "Nay"}]
    not_voting = [item for item in substantive if item["action"] == "Not Voting"]
    complete_episodes = [item for item in normalized_trajectories if item["coverage_status"] == "complete"]

    result = {
        "schema_version": "editorial_member_overlay_v1",
        "member": _required_mapping(member, ("bioguide_id", "display_name")),
        "reviewed_period": _required_text(reviewed_period, "reviewed_period"),
        "shared_episode_set": _required_mapping(shared_episode_set, ("episode_set_id", "version", "episode_map_path")),
        "roll_actions": normalized_actions,
        "episode_trajectories": normalized_trajectories,
        "coverage": {
            "substantive_rolls_expected": len(substantive),
            "substantive_yes_no_actions": len(yes_no),
            "not_voting_actions": len(not_voting),
            "independent_episodes_expected": len(normalized_trajectories),
            "independent_episodes_complete": len(complete_episodes),
        },
        "publication": _normalize_publication(publication),
    }
    _reject_duplicated_facts(result)
    return result


def build_member_inference(
    *,
    overlay: dict,
    shared_episodes: list[dict],
    conclusion: dict,
) -> dict:
    """Join shared annotations to member evidence and build a coverage-aware candidate."""
    minimum = int(conclusion.get("minimum_independent_episodes", 2))
    trajectories = {
        item["episode_id"]: item
        for item in overlay["episode_trajectories"]
        if item["coverage_status"] == "complete"
    }
    if len(trajectories) < minimum:
        return {
            "schema_version": "editorial_member_inference_v1",
            "member": deepcopy(overlay["member"]),
            "candidate_id": conclusion["candidate_id"],
            "inference_level": "insufficient_evidence",
            "evidence_strength_label": "Not enough reviewed evidence",
            "primary_conclusion": _required_text(
                conclusion.get("insufficient_evidence_conclusion"),
                "insufficient_evidence_conclusion",
            ),
            "assessment": "insufficient_coverage",
            "independent_episode_count": len(trajectories),
            "coverage": deepcopy(overlay["coverage"]),
            "episode_references": sorted(trajectories),
            "why_conclusion_does_not_go_further": _required_text(
                conclusion.get("insufficient_evidence_reason"),
                "insufficient_evidence_reason",
            ),
            "future_expansion_rule": _required_text(conclusion.get("future_expansion_rule"), "future_expansion_rule"),
            "reviewed_period": overlay["reviewed_period"],
            "human_review_status": "human_approval_pending",
        }

    shared_by_id = {item["episode_id"]: item for item in shared_episodes}
    annotations = []
    for episode_id, trajectory in trajectories.items():
        if episode_id not in shared_by_id:
            raise ValueError(f"overlay references unknown shared episode: {episode_id}")
        shared = shared_by_id[episode_id]
        annotations.append({
            "episode_id": episode_id,
            "independent": bool(shared.get("independent_evidence", True)),
            "relationship_to_repeated_stages": shared.get("relationship", ""),
            "mechanism_family": shared["mechanism_family"],
            "member_trajectory": trajectory["member_trajectory"],
            "practical_policy_direction": trajectory["practical_policy_direction"],
            "candidate_theme_tags": trajectory.get("candidate_theme_tags", []),
            "theme_evidence": trajectory.get("theme_evidence", []),
            "contrary_or_limiting_evidence": trajectory.get("contrary_or_limiting_evidence", []),
            "package_vote_limitations": trajectory.get("package_vote_limitations", []),
            "notable_one_off": bool(trajectory.get("notable_one_off")),
            "source_confidence": shared.get("source_confidence", "high"),
            "reviewed_period": overlay["reviewed_period"],
            "conclusion_effect": trajectory["conclusion_effect"],
        })

    generic_conclusion = {
        key: deepcopy(value)
        for key, value in conclusion.items()
        if key not in {"minimum_independent_episodes", "insufficient_evidence_conclusion", "insufficient_evidence_reason"}
    }
    result = build_editorial_inference(annotations, generic_conclusion)
    result["schema_version"] = "editorial_member_inference_v1"
    result["member"] = deepcopy(overlay["member"])
    result["coverage"] = deepcopy(overlay["coverage"])
    result["episode_references"] = [item["episode_id"] for item in annotations]
    # Avoid serializing joined shared facts once per member. They can be recomputed
    # from the stable episode-set reference and the member overlay.
    result.pop("episode_annotations", None)
    return result


def inference_evidence_view(inference: dict) -> dict:
    """Return the decision-relevant inference fields, excluding identity/context metadata."""
    excluded = {"member", "coverage", "reviewed_period", "human_review_status"}
    return {key: deepcopy(value) for key, value in inference.items() if key not in excluded}


def _normalize_action(item: dict) -> dict:
    result = deepcopy(item)
    roll = result.get("roll")
    if not isinstance(roll, int) or roll <= 0:
        raise ValueError("roll action requires a positive integer roll")
    if result.get("action") not in VALID_ACTIONS:
        raise ValueError(f"roll {roll} has unsupported member action")
    result["counting"] = bool(result.get("counting"))
    if "aligned_with_party_majority" in result and result["aligned_with_party_majority"] not in {True, False, None}:
        raise ValueError(f"roll {roll} has invalid descriptive party alignment")
    return result


def _normalize_trajectory(item: dict) -> dict:
    result = deepcopy(item)
    _required_mapping(result, ("episode_id", "member_trajectory", "practical_policy_direction", "coverage_status"))
    if result["coverage_status"] not in VALID_COVERAGE:
        raise ValueError(f"episode {result['episode_id']} has invalid coverage status")
    result["rolls"] = list(result.get("rolls", []))
    result["action_signature"] = list(result.get("action_signature", []))
    result["candidate_theme_tags"] = list(result.get("candidate_theme_tags", []))
    result["theme_evidence"] = list(result.get("theme_evidence", []))
    result["contrary_or_limiting_evidence"] = list(result.get("contrary_or_limiting_evidence", []))
    result["package_vote_limitations"] = list(result.get("package_vote_limitations", []))
    return result


def _normalize_publication(publication: dict) -> dict:
    result = deepcopy(publication)
    expected = {
        "editorial_status": "human_approval_pending",
        "benchmark_status": "not_promoted",
        "production_eligible": False,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError(f"member overlay publication {key} must remain {value!r}")
    return result


def _reject_duplicated_facts(value) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_OVERLAY_FACT_KEYS.intersection(value)
        if forbidden:
            raise ValueError(f"member overlay duplicates shared dossier facts: {sorted(forbidden)}")
        for nested in value.values():
            _reject_duplicated_facts(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_duplicated_facts(nested)


def _required_mapping(value: dict, keys: tuple[str, ...]) -> dict:
    if not isinstance(value, dict):
        raise ValueError("expected mapping")
    for key in keys:
        if value.get(key) in (None, ""):
            raise ValueError(f"missing required overlay field: {key}")
    return deepcopy(value)


def _required_text(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required overlay field: {field}")
    return value
