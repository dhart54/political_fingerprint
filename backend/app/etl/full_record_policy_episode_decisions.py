"""Generic authority and implementation contract for reviewed policy episodes."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from typing import Any


DOWNSTREAM_AUTHORIZATIONS = {
    "semantic_ir": False,
    "synthesis": False,
    "public_wording": False,
    "publication": False,
    "production_persistence": False,
    "database_writes": False,
    "deployment": False,
}


class PolicyEpisodeDecisionError(ValueError):
    """Raised when reviewed episode authority or implementation fails closed."""


def digest(value: object) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def seal(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop(field, None)
    result[field] = digest(result)
    return result


def verify_seal(value: dict[str, Any], field: str, label: str) -> None:
    subject = {key: child for key, child in value.items() if key != field}
    if value.get(field) != digest(subject):
        raise PolicyEpisodeDecisionError(f"{label}: {field} differs")


def require_cross_measure_continuity(episode: dict[str, Any]) -> None:
    """Require more than a shared proposition for a primary cross-measure episode."""
    if episode["grouping_type"] != "cross_measure":
        return
    continuity = episode.get("legislative_event_continuity")
    if not isinstance(continuity, dict) or not (
        continuity.get("state") == "established"
        and continuity.get("evidence")
        and continuity.get("same_legislative_path_or_event") is True
    ):
        raise PolicyEpisodeDecisionError(
            "cross-measure primary grouping lacks explicit legislative/event continuity"
        )


def validate_authority(
    authority: dict[str, Any],
    *,
    candidate: dict[str, Any],
    accepted_single_episode_ids: set[str],
    rejected_episode_ids: set[str],
) -> dict[str, int]:
    verify_seal(authority, "authority_subject_sha256", "episode authority")
    subject = authority["subject"]
    if authority.get("accepted") is not True or authority.get("immutable") is not True:
        raise PolicyEpisodeDecisionError("episode authority is not immutable/accepted")
    if authority.get("canonical_internal_episode_authority") is not True:
        raise PolicyEpisodeDecisionError("internal episode authority missing")
    if any(subject["downstream_authorizations"].values()):
        raise PolicyEpisodeDecisionError("downstream authority leakage")
    if subject["candidate_binding"]["artifact_id"] != candidate["artifact_id"]:
        raise PolicyEpisodeDecisionError("candidate identity differs")
    candidate_by_id = {
        row["episode_id"]: row for row in candidate["subject"]["episodes"]
    }
    decisions = subject["episode_decisions"]
    if len(decisions) != len(candidate_by_id) or len(
        {row["episode_id"] for row in decisions}
    ) != len(decisions):
        raise PolicyEpisodeDecisionError("episode decision accounting differs")
    if {row["episode_id"] for row in decisions} != set(candidate_by_id):
        raise PolicyEpisodeDecisionError("episode decision set differs")
    for row in decisions:
        verify_seal(row, "decision_subject_sha256", row["episode_id"])
        source = candidate_by_id[row["episode_id"]]
        if row["candidate_episode_subject_sha256"] != source["episode_subject_sha256"]:
            raise PolicyEpisodeDecisionError("decision candidate binding differs")
        expected = (
            "accept_candidate_as_written"
            if row["episode_id"] in accepted_single_episode_ids
            else "reject_and_reassign_actions"
        )
        if row["decision"] != expected:
            raise PolicyEpisodeDecisionError("human episode decision differs")
        if expected == "accept_candidate_as_written" and row["replacement_episode_ids"]:
            raise PolicyEpisodeDecisionError("accepted candidate has replacements")
        if expected == "reject_and_reassign_actions" and (
            row["episode_id"] not in rejected_episode_ids
            or len(row["replacement_episode_ids"]) != len(source["primary_action_ids"])
        ):
            raise PolicyEpisodeDecisionError("reassignment decision differs")
    counts = Counter(row["decision"] for row in decisions)
    if subject["decision_accounting"] != dict(sorted(counts.items())):
        raise PolicyEpisodeDecisionError("decision summary differs")
    return dict(counts)


def validate_implementation(
    bundle: dict[str, Any],
    *,
    authority: dict[str, Any],
    m11d_records: list[dict[str, Any]],
    blocked_action_id: str,
    rejected_episode_ids: set[str],
) -> dict[str, int]:
    verify_seal(bundle, "implementation_subject_sha256", "episode implementation")
    subject = bundle["subject"]
    if any(subject["downstream_authorizations"].values()):
        raise PolicyEpisodeDecisionError("downstream authority leakage")
    if (
        subject["authority_binding"]["authority_subject_sha256"]
        != authority["authority_subject_sha256"]
    ):
        raise PolicyEpisodeDecisionError("authority implementation binding differs")
    upstream = {row["action_id"]: row for row in m11d_records}
    records = subject["implementation_records"]
    action_to_episode: dict[str, str] = {}
    for episode in records:
        verify_seal(episode, "record_subject_sha256", episode["episode_id"])
        if episode["episode_id"] in rejected_episode_ids:
            raise PolicyEpisodeDecisionError("rejected grouping remains primary")
        if (
            episode["grouping_type"] != "single_action"
            or len(episode["primary_action_ids"]) != 1
        ):
            require_cross_measure_continuity(episode)
            raise PolicyEpisodeDecisionError(
                "final implementation is not singleton-only"
            )
        action_id = episode["primary_action_ids"][0]
        if action_id == blocked_action_id:
            raise PolicyEpisodeDecisionError(
                "blocked action entered episode implementation"
            )
        if action_id in action_to_episode:
            raise PolicyEpisodeDecisionError("action assigned more than once")
        if action_id not in upstream:
            raise PolicyEpisodeDecisionError("episode action outside M11D")
        action_to_episode[action_id] = episode["episode_id"]
        action = episode["actions"][0]
        source = upstream[action_id]
        exact = {
            "accepted_interpretation_record_id": source["record_id"],
            "accepted_interpretation_record_subject_sha256": source[
                "record_subject_sha256"
            ],
            "accepted_exact_action_meaning": source["accepted_exact_action_meaning"],
            "accepted_exact_choice_position_effect": source[
                "accepted_exact_choice_position_effect"
            ],
            "accepted_limitations": source["accepted_limitations"],
            "source_references": source["source_references"],
        }
        if any(action[key] != value for key, value in exact.items()):
            raise PolicyEpisodeDecisionError(
                "accepted action meaning/effect binding differs"
            )
    if set(action_to_episode) != set(upstream):
        raise PolicyEpisodeDecisionError("accepted M11D action omitted")
    accounting = subject["action_accounting"]
    if len(accounting) != len(upstream) or {
        row["action_id"] for row in accounting
    } != set(upstream):
        raise PolicyEpisodeDecisionError("primary action accounting differs")
    for row in accounting:
        if row["primary_episode_id"] != action_to_episode[row["action_id"]]:
            raise PolicyEpisodeDecisionError("accounting episode binding differs")
    for relationship in subject["non_primary_relationship_evidence"]:
        if relationship["primary_authority_effect"] is not False:
            raise PolicyEpisodeDecisionError("relationship altered primary accounting")
        if relationship["relationship_id"] not in rejected_episode_ids:
            raise PolicyEpisodeDecisionError(
                "unexpected rejected relationship evidence"
            )
    expected = {
        "accepted_action_count": len(upstream),
        "accepted_episode_count": len(records),
        "single_action_episode_count": len(records),
        "multi_action_episode_count": 0,
        "cross_measure_episode_count": 0,
        "ambiguous_or_unassigned_action_count": 0,
        "blocked_action_count": 1,
    }
    if subject["final_accounting"] != expected:
        raise PolicyEpisodeDecisionError("final episode accounting differs")
    return expected
