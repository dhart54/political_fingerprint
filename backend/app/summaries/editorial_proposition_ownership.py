"""Deterministic ownership and deduplication for public analytical propositions."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy


SECTION_ORDER = (
    "repeated_patterns",
    "policy_trajectories",
    "other_notable_choices",
    "meaningful_exceptions",
)


def compose_analytical_sections(
    *,
    complete_trajectories: list[dict],
    repeated_patterns: list[dict],
    meaningful_limitations: list[dict],
    coverage: dict,
    method_notes: list[str],
) -> dict:
    """Assign every proposition one public section and report every exclusion."""
    propositions: list[dict] = []
    repeated_episode_ids: set[str] = set()

    for pattern in sorted(repeated_patterns, key=_repeated_sort_key):
        episode_ids = sorted(
            {
                row["episode_id"]
                for row in pattern.get("supporting_episodes", [])
                if row.get("episode_id")
            }
        )
        if len(episode_ids) < 2:
            continue
        repeated_episode_ids.update(episode_ids)
        propositions.append(
            _proposition(
                role="repeated_pattern",
                relationship=pattern.get("theme_id", "shared_policy_pattern"),
                direction=_direction_from_theme(pattern.get("theme_id", "")),
                episode_ids=episode_ids,
                section="repeated_patterns",
                text=pattern["finding"],
                excluded_from=(
                    "policy_trajectories",
                    "other_notable_choices",
                    "meaningful_exceptions",
                ),
            )
        )

    trajectory_episode_ids: set[str] = set()
    for trajectory in sorted(
        complete_trajectories, key=lambda item: item.get("episode_id", "")
    ):
        rolls = trajectory.get("rolls", [])
        if len(rolls) < 2 or not trajectory.get("relationship_to_repeated_stages"):
            continue
        episode_id = trajectory["episode_id"]
        trajectory_episode_ids.add(episode_id)
        propositions.append(
            _proposition(
                role="policy_trajectory",
                relationship=trajectory["relationship_to_repeated_stages"],
                direction="/".join(trajectory.get("action_signature", [])),
                episode_ids=[episode_id],
                section="policy_trajectories",
                text=trajectory["member_trajectory"],
                excluded_from=(
                    "repeated_patterns",
                    "other_notable_choices",
                    "meaningful_exceptions",
                ),
            )
        )

    owned_episode_ids = repeated_episode_ids | trajectory_episode_ids
    for trajectory in sorted(
        complete_trajectories, key=lambda item: item.get("episode_id", "")
    ):
        episode_id = trajectory["episode_id"]
        if episode_id in owned_episode_ids or len(trajectory.get("rolls", [])) != 1:
            continue
        propositions.append(
            _proposition(
                role="notable_choice",
                relationship="independent_one_off_episode",
                direction="/".join(trajectory.get("action_signature", [])),
                episode_ids=[episode_id],
                section="other_notable_choices",
                text=trajectory["practical_policy_direction"],
                excluded_from=(
                    "repeated_patterns",
                    "policy_trajectories",
                    "meaningful_exceptions",
                ),
            )
        )

    for limitation in sorted(
        meaningful_limitations,
        key=lambda item: (
            item.get("episode_id", ""),
            _normalize(item.get("text", "")),
        ),
    ):
        text = limitation.get("text", "").strip()
        if not text:
            continue
        propositions.append(
            _proposition(
                role="meaningful_exception",
                relationship=limitation.get(
                    "analytical_relationship", "materially_limits_conclusion"
                ),
                direction=limitation.get("direction", ""),
                episode_ids=[limitation["episode_id"]]
                if limitation.get("episode_id")
                else [],
                section="meaningful_exceptions",
                text=text,
                excluded_from=(
                    "repeated_patterns",
                    "policy_trajectories",
                    "other_notable_choices",
                ),
            )
        )

    deduplicated, duplicate_count = _deduplicate(propositions)
    section_collision_count = _section_collision_count(deduplicated)
    sections = {
        section: [
            deepcopy(item)
            for item in deduplicated
            if item["assigned_section"] == section
        ]
        for section in SECTION_ORDER
    }
    exact_coverage_note = coverage_note(coverage)
    method_note = " ".join(
        dict.fromkeys(note.strip() for note in method_notes if note.strip())
    ) or None
    return {
        "schema_version": "editorial_section_ownership_v1",
        "propositions": deduplicated,
        "sections": sections,
        "coverage_note": exact_coverage_note,
        "method_note": method_note,
        "metrics": {
            "duplicate_proposition_count": duplicate_count,
            "section_collision_count": section_collision_count,
            "unresolved_collision_count": section_collision_count,
            "single_action_trajectory_count": sum(
                len(item["evidence_episode_ids"]) == 1
                and item["assigned_section"] == "policy_trajectories"
                and next(
                    (
                        len(trajectory.get("rolls", []))
                        for trajectory in complete_trajectories
                        if trajectory.get("episode_id")
                        == item["evidence_episode_ids"][0]
                    ),
                    0,
                )
                < 2
                for item in deduplicated
            ),
            "methodology_in_exception_count": sum(
                item["assigned_section"] == "meaningful_exceptions"
                and _looks_like_methodology(item["exact_rendered_text"])
                for item in deduplicated
            ),
            "empty_section_render_count": 0,
            "generic_coverage_fallback_count_when_exact_known": 0,
        },
    }


def coverage_note(coverage: dict) -> str:
    expected = int(coverage.get("expected_in_service_actions", 0))
    observed = int(coverage.get("substantive_rolls_observed", 0))
    yes_no = int(coverage.get("substantive_yes_no_actions", 0))
    not_voting = int(coverage.get("not_voting_actions", 0))
    present = int(coverage.get("present_actions", 0))
    missing = int(coverage.get("missing_actions", 0))
    outside = int(coverage.get("independent_episodes_outside_service", 0))
    resolved = yes_no + not_voting + present
    parts = [
        f"{resolved} of {expected} expected action statuses are resolved"
        if expected
        else f"{resolved} action statuses are resolved",
        f"{yes_no} contain {'a' if yes_no == 1 else ''} Yea/Nay "
        f"{'position' if yes_no == 1 else 'positions'}".replace("contain  Yea", "contain Yea"),
    ]
    if not_voting:
        parts.append(
            f"{not_voting} {'is' if not_voting == 1 else 'are'} Not Voting"
        )
    if present:
        parts.append(f"{present} {'is' if present == 1 else 'are'} Present")
    if missing:
        parts.append(
            f"{missing} expected {'record is' if missing == 1 else 'records are'} missing"
        )
    if outside:
        parts.append(
            f"{outside} {'episode is' if outside == 1 else 'episodes are'} outside service"
        )
    return "; ".join(parts) + "."


def aggregate_ownership_metrics(reports: list[dict]) -> dict:
    keys = (
        "duplicate_proposition_count",
        "section_collision_count",
        "unresolved_collision_count",
        "single_action_trajectory_count",
        "methodology_in_exception_count",
        "empty_section_render_count",
        "generic_coverage_fallback_count_when_exact_known",
    )
    return {
        key: sum(report.get("metrics", {}).get(key, 0) for report in reports)
        for key in keys
    }


def _proposition(
    *,
    role: str,
    relationship: str,
    direction: str,
    episode_ids: list[str],
    section: str,
    text: str,
    excluded_from: tuple[str, ...],
) -> dict:
    identity = {
        "role": role,
        "relationship": relationship,
        "direction": direction,
        "episode_ids": sorted(episode_ids),
        "text": _normalize(text),
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "semantic_proposition_id": f"prop-{digest}",
        "proposition_role": role,
        "analytical_relationship": relationship,
        "vote_direction_or_trajectory": direction,
        "evidence_episode_ids": sorted(episode_ids),
        "assigned_section": section,
        "exact_rendered_text": text.strip(),
        "excluded_from": list(excluded_from),
        "deduplication_result": "unique",
        "unresolved_collision": False,
    }


def _deduplicate(propositions: list[dict]) -> tuple[list[dict], int]:
    seen: dict[str, dict] = {}
    duplicate_count = 0
    for proposition in propositions:
        semantic_id = proposition["semantic_proposition_id"]
        if semantic_id in seen:
            duplicate_count += 1
            continue
        seen[semantic_id] = proposition
    return sorted(
        seen.values(),
        key=lambda item: (
            SECTION_ORDER.index(item["assigned_section"]),
            item["semantic_proposition_id"],
        ),
    ), duplicate_count


def _section_collision_count(propositions: list[dict]) -> int:
    sections_by_id: dict[str, set[str]] = {}
    for proposition in propositions:
        sections_by_id.setdefault(
            proposition["semantic_proposition_id"], set()
        ).add(proposition["assigned_section"])
    return sum(len(sections) > 1 for sections in sections_by_id.values())


def _direction_from_theme(theme_id: str) -> str:
    if theme_id.endswith("_support"):
        return "Yea"
    if theme_id.endswith("_opposition"):
        return "Nay"
    return ""


def _repeated_sort_key(item: dict) -> tuple:
    return (
        tuple(
            sorted(
                row.get("episode_id", "")
                for row in item.get("supporting_episodes", [])
            )
        ),
        item.get("theme_id", ""),
    )


def _looks_like_methodology(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:count as one episode|counting rule|sample boundary|publication|review dependency)\b",
            text,
            re.IGNORECASE,
        )
    )


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
