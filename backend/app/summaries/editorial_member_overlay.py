"""Domain-neutral member overlays for a declared shared episode set."""

from __future__ import annotations

from copy import deepcopy
from datetime import date


VALID_ACTIONS = {
    "Yea", "Nay", "Present", "Not Voting",
    "Not Yet Serving", "No Longer Serving", "Missing Evidence",
}
OUTSIDE_SERVICE_ACTIONS = {"Not Yet Serving", "No Longer Serving"}
FORBIDDEN_OVERLAY_FACT_KEYS = {
    "bill_title", "measure_summary", "primary_purpose", "source_url",
    "supporter_argument", "opponent_argument", "legislative_history",
}


def build_member_overlay(*, member: dict, reviewed_period: str, shared_episode_set: dict,
                         roll_actions: list[dict], episode_action_interpretations: dict,
                         publication: dict) -> dict:
    """Validate actions against the shared contract and derive coverage/trajectories."""
    _reject_duplicated_facts(episode_action_interpretations)
    contract = _normalize_contract(shared_episode_set)
    expected_substantive = contract["expected_substantive_roll_ids"]
    expected_controls = contract["expected_control_roll_ids"]
    expected_rolls = set(expected_substantive + expected_controls)
    roll_to_episode = {
        roll: episode_id
        for episode_id, rolls in contract["episode_rolls"].items()
        for roll in rolls
    }
    normalized_actions = [_normalize_action(item) for item in roll_actions]
    supplied_rolls = [item["roll"] for item in normalized_actions]
    if len(supplied_rolls) != len(set(supplied_rolls)):
        raise ValueError("member overlay contains duplicate roll actions")
    unknown = sorted(set(supplied_rolls) - expected_rolls)
    if unknown:
        raise ValueError(f"member overlay contains unknown rolls: {unknown}")
    for item in normalized_actions:
        expected_episode = roll_to_episode.get(item["roll"])
        if item.get("episode_id") != expected_episode:
            raise ValueError(f"roll {item['roll']} episode_id does not match shared episode set")
        if item["counting"] != (item["roll"] in expected_substantive):
            raise ValueError(f"roll {item['roll']} counting status does not match shared episode set")

    by_roll = {item["roll"]: item for item in normalized_actions}
    trajectories = []
    for episode_id in contract["expected_independent_episode_ids"]:
        if episode_id not in episode_action_interpretations:
            raise ValueError(f"missing action interpretation for episode: {episode_id}")
        rolls = contract["episode_rolls"][episode_id]
        signature = [by_roll[roll]["action"] if roll in by_roll else "Missing Evidence" for roll in rolls]
        in_service = [action for action in signature if action not in OUTSIDE_SERVICE_ACTIONS]
        yes_no = sum(action in {"Yea", "Nay"} for action in in_service)
        coverage = (
            "outside_service" if not in_service
            else "complete" if yes_no == len(in_service)
            else "partial" if any(action != "Missing Evidence" for action in in_service)
            else "missing"
        )
        catalog = episode_action_interpretations[episode_id]
        interpretation = deepcopy(catalog.get("signatures", {}).get("|".join(signature), catalog.get("non_counting")))
        if not interpretation:
            raise ValueError(f"episode {episode_id} has no interpretation for action signature {signature}")
        trajectories.append({
            "episode_id": episode_id,
            "rolls": list(rolls),
            "action_signature": signature,
            "coverage_status": coverage,
            "mechanism_family": _required_text(catalog.get("mechanism_family"), "mechanism_family"),
            "relationship_to_repeated_stages": catalog.get("relationship_to_repeated_stages", ""),
            "member_trajectory": _required_text(interpretation.get("member_trajectory"), "member_trajectory"),
            "practical_policy_direction": _required_text(interpretation.get("practical_policy_direction"), "practical_policy_direction"),
            "theme_evidence": deepcopy(interpretation.get("theme_evidence", [])) if coverage == "complete" else [],
            "contrary_or_limiting_evidence": deepcopy(interpretation.get("contrary_or_limiting_evidence", [])),
            "package_vote_limitations": deepcopy(interpretation.get("package_vote_limitations", [])),
        })

    substantive_actions = [by_roll[roll]["action"] if roll in by_roll else "Missing Evidence" for roll in expected_substantive]
    in_service_actions = [action for action in substantive_actions if action not in OUTSIDE_SERVICE_ACTIONS]
    result = {
        "schema_version": "editorial_member_overlay_v2",
        "member": _required_mapping(member, ("bioguide_id", "display_name")),
        "reviewed_period": _required_text(reviewed_period, "reviewed_period"),
        "shared_episode_set": contract,
        "roll_actions": normalized_actions,
        "episode_trajectories": trajectories,
        "coverage": {
            "substantive_rolls_expected": len(expected_substantive),
            "substantive_rolls_observed": sum(roll in by_roll for roll in expected_substantive),
            "substantive_yes_no_actions": sum(action in {"Yea", "Nay"} for action in substantive_actions),
            "present_actions": substantive_actions.count("Present"),
            "not_voting_actions": substantive_actions.count("Not Voting"),
            "not_yet_serving_actions": substantive_actions.count("Not Yet Serving"),
            "no_longer_serving_actions": substantive_actions.count("No Longer Serving"),
            "expected_in_service_actions": len(in_service_actions),
            "missing_actions": substantive_actions.count("Missing Evidence"),
            "independent_episodes_expected": len(contract["expected_independent_episode_ids"]),
            "independent_episodes_complete": sum(item["coverage_status"] == "complete" for item in trajectories),
            "independent_episodes_partial": sum(item["coverage_status"] == "partial" for item in trajectories),
            "independent_episodes_missing": sum(item["coverage_status"] == "missing" for item in trajectories),
            "independent_episodes_outside_service": sum(item["coverage_status"] == "outside_service" for item in trajectories),
        },
        "publication": _normalize_publication(publication),
    }
    _reject_duplicated_facts(result)
    return result


def inference_evidence_view(inference: dict) -> dict:
    excluded = {"member", "coverage", "reviewed_period", "human_review_status"}
    return {key: deepcopy(value) for key, value in inference.items() if key not in excluded}


def classify_missing_action_status(*, action_date: str, service_start_date: str | None = None,
                                   service_end_date: str | None = None,
                                   service_date_precision: str | None = None) -> str:
    """Classify a missing action only when exact day-level eligibility is established."""
    if service_date_precision != "day":
        return "Missing Evidence"
    action_day = _iso_date(action_date, "action_date")
    start_day = _iso_date(service_start_date, "service_start_date") if service_start_date else None
    end_day = _iso_date(service_end_date, "service_end_date") if service_end_date else None
    if start_day and action_day < start_day:
        return "Not Yet Serving"
    if end_day and action_day > end_day:
        return "No Longer Serving"
    return "Missing Evidence"


def _normalize_contract(value: dict) -> dict:
    result = _required_mapping(value, (
        "episode_set_id", "version", "episode_map_path", "expected_substantive_roll_ids",
        "expected_control_roll_ids", "expected_independent_episode_ids", "episode_rolls",
    ))
    for key in ("expected_substantive_roll_ids", "expected_control_roll_ids", "expected_independent_episode_ids"):
        result[key] = list(result[key])
        if len(result[key]) != len(set(result[key])):
            raise ValueError(f"shared episode set contains duplicate {key}")
    result["episode_rolls"] = {key: list(rolls) for key, rolls in result["episode_rolls"].items()}
    if set(result["episode_rolls"]) != set(result["expected_independent_episode_ids"]):
        raise ValueError("shared episode set episode identifiers do not match episode_rolls")
    mapped = [roll for rolls in result["episode_rolls"].values() for roll in rolls]
    if len(mapped) != len(set(mapped)) or set(mapped) != set(result["expected_substantive_roll_ids"]):
        raise ValueError("shared episode set substantive rolls must map to exactly one episode")
    if set(result["expected_substantive_roll_ids"]) & set(result["expected_control_roll_ids"]):
        raise ValueError("shared episode set substantive and control rolls overlap")
    return result


def _normalize_action(item: dict) -> dict:
    result = deepcopy(item)
    if not isinstance(result.get("roll"), int) or result["roll"] <= 0:
        raise ValueError("roll action requires a positive integer roll")
    if result.get("action") not in VALID_ACTIONS:
        raise ValueError(f"roll {result['roll']} has unsupported member action")
    result["counting"] = bool(result.get("counting"))
    if "aligned_with_party_majority" in result and result["aligned_with_party_majority"] not in {True, False, None}:
        raise ValueError(f"roll {result['roll']} has invalid descriptive party alignment")
    return result


def _normalize_publication(publication: dict) -> dict:
    result = deepcopy(publication)
    expected = {"editorial_status": "human_approval_pending", "benchmark_status": "not_promoted", "production_eligible": False}
    for key, expected_value in expected.items():
        if result.get(key) != expected_value:
            raise ValueError(f"member overlay publication {key} must remain {expected_value!r}")
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


def _iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an exact ISO date") from exc
