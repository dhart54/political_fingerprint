"""Deterministic, identity-minimal selection for blind editorial validation."""

from __future__ import annotations

from hashlib import sha256
import json


YES_NO = {"Yea", "Nay"}


def select_blind_candidate(
    *,
    overlays: list[dict],
    reference_member_ids: tuple[str, ...],
    episode_rolls: dict[str, list[int] | tuple[int, ...]],
    starting_commit: str,
    build_identifier: str,
) -> dict:
    """Select the most novel complete action structure without using party or copy."""
    if len(reference_member_ids) != 2:
        raise ValueError("blind selection requires exactly two reference members")
    by_id = {item["member"]["bioguide_id"]: item for item in overlays}
    missing_references = [member_id for member_id in reference_member_ids if member_id not in by_id]
    if missing_references:
        raise ValueError(f"missing reference overlays: {missing_references}")

    roll_order = list(by_id[reference_member_ids[0]]["shared_episode_set"]["expected_substantive_roll_ids"])
    reference_vectors = {
        member_id: _action_vector(by_id[member_id], roll_order)
        for member_id in reference_member_ids
    }
    rows = []
    eligible = []
    for overlay in sorted(overlays, key=lambda item: item["member"]["bioguide_id"]):
        member_id = overlay["member"]["bioguide_id"]
        vector = _action_vector(overlay, roll_order)
        exclusion_reasons = _exclusion_reasons(
            overlay=overlay,
            member_id=member_id,
            vector=vector,
            reference_member_ids=reference_member_ids,
            reference_vectors=reference_vectors,
            roll_order=roll_order,
        )
        novelty = None if exclusion_reasons else _novelty(
            vector=vector,
            reference_vectors=reference_vectors,
            roll_order=roll_order,
            episode_rolls=episode_rolls,
        )
        row = {
            "member_id": member_id,
            "member_display_name": overlay["member"]["display_name"],
            "action_vector": vector,
            "eligible": not exclusion_reasons,
            "exclusion_reasons": exclusion_reasons,
            "novelty": novelty,
        }
        rows.append(row)
        if novelty:
            eligible.append(row)
    if not eligible:
        raise ValueError("no eligible complete candidate exists")

    selected = sorted(
        eligible,
        key=lambda item: (
            -item["novelty"]["score_components"]["minimum_reference_distance"],
            -item["novelty"]["score_components"]["novel_episode_signature_count"],
            -item["novelty"]["score_components"]["action_balance_distance"],
            -item["novelty"]["score_components"]["total_reference_distance"],
            item["member_id"],
        ),
    )[0]
    lock_payload = {
        "starting_commit": starting_commit,
        "build_identifier": build_identifier,
        "reference_member_ids": list(reference_member_ids),
        "selected_member_id": selected["member_id"],
        "eligible_scores": [
            {"member_id": item["member_id"], "score_components": item["novelty"]["score_components"]}
            for item in eligible
        ],
    }
    return {
        "schema_version": "blind_editorial_candidate_selection_v1",
        "starting_commit": starting_commit,
        "deterministic_build_identifier": build_identifier,
        "selection_inputs": [
            "complete authoritative Yes/No action vector",
            "Hamming distance from both reference vectors",
            "episode signatures distinct from both references",
            "action-balance distance from both references",
        ],
        "excluded_inputs": [
            "party",
            "ideology",
            "electoral competitiveness",
            "fame",
            "expected conclusion wording",
            "manually judged political interest",
        ],
        "roll_order": roll_order,
        "episode_rolls": {key: list(value) for key, value in episode_rolls.items()},
        "reference_member_ids": list(reference_member_ids),
        "reference_action_vectors": reference_vectors,
        "tie_break_rule": "Lexicographically maximize the recorded score components, then choose the smallest member ID.",
        "candidates": rows,
        "eligible_candidates": [item["member_id"] for item in eligible],
        "selected_member": {
            "member_id": selected["member_id"],
            "member_display_name": selected["member_display_name"],
            "action_vector": selected["action_vector"],
            "novelty": selected["novelty"],
        },
        "selection_lock": sha256(_canonical(lock_payload).encode("utf-8")).hexdigest(),
    }


def assert_selection_locked(selection: dict, generated_candidate: dict) -> None:
    """Prevent an already generated conclusion from being rebound to a new member."""
    expected = (
        selection.get("selected_member", {}).get("member_id"),
        selection.get("selection_lock"),
    )
    actual = (
        generated_candidate.get("selected_member", {}).get("member_id"),
        generated_candidate.get("selection_lock"),
    )
    if actual != expected:
        raise ValueError("selected member cannot change after conclusion generation")


def select_featured_episode_ids(*, overlay: dict, inference: dict, maximum: int = 5) -> list[str]:
    """Select bounded featured evidence upstream from structured inference references."""
    if maximum < 3 or maximum > 5:
        raise ValueError("featured episode maximum must stay between three and five")
    expected = list(overlay["shared_episode_set"]["expected_independent_episode_ids"])
    complete = {
        item["episode_id"]
        for item in overlay["episode_trajectories"]
        if item["coverage_status"] == "complete"
    }
    priority = []
    for key in ("weakening_independent_episodes", "supporting_independent_episodes"):
        priority.extend(item["episode_id"] for item in inference.get(key, []))
    priority.extend(item["episode_id"] for item in inference.get("within_episode_trajectories", []))
    priority.extend(item["episode_id"] for item in inference.get("notable_one_off_choices", []))
    priority.extend(expected)
    selected = []
    for episode_id in priority:
        if episode_id in complete and episode_id not in selected:
            selected.append(episode_id)
        if len(selected) == maximum:
            break
    if len(selected) < min(3, len(complete)):
        raise ValueError("structured evidence cannot supply the minimum featured episodes")
    return selected


def _exclusion_reasons(
    *,
    overlay: dict,
    member_id: str,
    vector: list[str],
    reference_member_ids: tuple[str, ...],
    reference_vectors: dict[str, list[str]],
    roll_order: list[int],
) -> list[str]:
    reasons = []
    if member_id in reference_member_ids:
        reasons.append("existing_reference_fixture")
    if len(vector) != len(roll_order) or any(action not in YES_NO for action in vector):
        reasons.append("incomplete_seven_action_record")
    substantive = [item for item in overlay.get("roll_actions", []) if item.get("counting")]
    if len(substantive) != len(roll_order) or any(not item.get("source_id") for item in substantive):
        reasons.append("unresolved_action_identity")
    if any(action in {"Not Yet Serving", "No Longer Serving", "Missing Evidence"} for action in vector):
        reasons.append("service_status_does_not_support_recorded_actions")
    for reference_id, reference_vector in reference_vectors.items():
        if member_id not in reference_member_ids and vector == reference_vector:
            reasons.append(f"identical_to_reference_fixture:{reference_id}")
    return reasons


def _novelty(
    *,
    vector: list[str],
    reference_vectors: dict[str, list[str]],
    roll_order: list[int],
    episode_rolls: dict[str, list[int] | tuple[int, ...]],
) -> dict:
    distances = {
        member_id: sum(left != right for left, right in zip(vector, reference))
        for member_id, reference in reference_vectors.items()
    }
    by_roll = dict(zip(roll_order, vector))
    reference_by_roll = {
        member_id: dict(zip(roll_order, reference))
        for member_id, reference in reference_vectors.items()
    }
    episode_signatures = {
        episode_id: [by_roll[roll] for roll in rolls]
        for episode_id, rolls in episode_rolls.items()
    }
    novel_episodes = [
        episode_id
        for episode_id, signature in episode_signatures.items()
        if all(
            signature != [reference_by_roll[member_id][roll] for roll in episode_rolls[episode_id]]
            for member_id in reference_vectors
        )
    ]
    candidate_minority = min(vector.count("Yea"), vector.count("Nay"))
    reference_minorities = [
        min(reference.count("Yea"), reference.count("Nay"))
        for reference in reference_vectors.values()
    ]
    return {
        "distance_from_references": distances,
        "episode_signatures": episode_signatures,
        "episode_signatures_distinct_from_both_references": novel_episodes,
        "candidate_minority_action_count": candidate_minority,
        "reference_minority_action_counts": reference_minorities,
        "score_components": {
            "minimum_reference_distance": min(distances.values()),
            "novel_episode_signature_count": len(novel_episodes),
            "action_balance_distance": min(abs(candidate_minority - value) for value in reference_minorities),
            "total_reference_distance": sum(distances.values()),
        },
    }


def _action_vector(overlay: dict, roll_order: list[int]) -> list[str]:
    actions = {
        item["roll"]: item["action"]
        for item in overlay.get("roll_actions", [])
        if item.get("counting")
    }
    return [actions.get(roll, "Missing Evidence") for roll in roll_order]


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
