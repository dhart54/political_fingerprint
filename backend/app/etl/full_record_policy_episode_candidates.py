"""Generic construction and validation for detached policy-episode candidates."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import re
from typing import Any


SCHEMA_VERSION = "full_record_policy_episode_candidate_batch_v1"
EPISODE_SCHEMA_VERSION = "full_record_policy_episode_candidate_v1"
DECISION_SCHEMA_VERSION = "full_record_policy_episode_human_decision_template_v1"

DOWNSTREAM_AUTHORIZATIONS = {
    "episode_acceptance": False,
    "semantic_ir": False,
    "synthesis": False,
    "public_wording": False,
    "publication": False,
    "production_persistence": False,
    "database_writes": False,
    "deployment": False,
}


class PolicyEpisodeCandidateError(ValueError):
    """Raised when a candidate package violates the governed contract."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def seal(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result.pop(field, None)
    result[field] = digest(result)
    return result


def verify_seal(value: dict[str, Any], field: str, label: str) -> None:
    subject = {key: child for key, child in value.items() if key != field}
    if value.get(field) != digest(subject):
        raise PolicyEpisodeCandidateError(f"{label}: {field} differs")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _policy_proposition(meaning: str) -> str:
    prefix = "The House choice was whether to "
    if meaning.startswith(prefix):
        return "Whether to " + meaning[len(prefix) :]
    return meaning


def _session_roll(action_id: str) -> tuple[int, int]:
    _, _, session, roll = action_id.split(":")
    return int(session), int(roll)


def _direction(records: list[dict[str, Any]]) -> str:
    effects = {row["accepted_exact_choice_position_effect"] for row in records}
    if effects == {"supports_exact_choice"}:
        return "supports_policy_proposition"
    if effects == {"opposes_exact_choice"}:
        return "opposes_policy_proposition"
    if effects <= {"supports_exact_choice", "opposes_exact_choice"}:
        return "mixed_on_episode_choices"
    raise PolicyEpisodeCandidateError("unsupported accepted exact-choice effect")


def _role(candidate: dict[str, Any]) -> str:
    if candidate["house_action_stage"] == "amendment":
        return "amendment_choice"
    if candidate["house_action_stage"].startswith("suspension"):
        return "suspension_passage_choice"
    return "measure_choice"


def build_candidate_batch(
    *,
    artifact_id: str,
    subject: dict[str, Any],
    input_bindings: dict[str, Any],
    implementation: dict[str, Any],
    candidate_artifact: dict[str, Any],
    multi_action_definitions: list[dict[str, Any]],
    contrast_groups: list[dict[str, Any]],
    blocked_action: dict[str, Any],
) -> dict[str, Any]:
    records = implementation["subject"]["implementation_records"]
    candidates = candidate_artifact["subject"]["candidates"]
    by_id = {row["action_id"]: row for row in records}
    candidate_by_id = {row["action_id"]: row for row in candidates}
    if len(by_id) != len(records) or len(candidate_by_id) != len(candidates):
        raise PolicyEpisodeCandidateError("duplicate upstream action identity")
    if set(by_id) != set(candidate_by_id):
        raise PolicyEpisodeCandidateError(
            "implementation/candidate action-set mismatch"
        )

    primary_group: dict[str, dict[str, Any]] = {}
    for definition in multi_action_definitions:
        action_ids = definition["action_ids"]
        if len(action_ids) < 2 or len(action_ids) != len(set(action_ids)):
            raise PolicyEpisodeCandidateError("multi-action definition is not unique")
        for action_id in action_ids:
            if action_id not in by_id:
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: multi-action definition outside implementation"
                )
            if action_id in primary_group:
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: duplicate multi-action definition"
                )
            primary_group[action_id] = definition

    contrast_by_action: dict[str, list[str]] = {action_id: [] for action_id in by_id}
    contrast_reviews = []
    for group in contrast_groups:
        action_ids = group["action_ids"]
        if not set(action_ids) <= set(by_id):
            raise PolicyEpisodeCandidateError("contrast group outside implementation")
        contrast_reviews.append(deepcopy(group))
        for action_id in action_ids:
            contrast_by_action[action_id].append(group["contrast_id"])

    definitions = list(multi_action_definitions)
    for action_id in sorted(set(by_id) - set(primary_group)):
        candidate = candidate_by_id[action_id]
        identity = _slug(candidate["exact_action_identity"])
        definitions.append(
            {
                "episode_id": (
                    f"single-{identity}-{_session_roll(action_id)[0]}-"
                    f"{_session_roll(action_id)[1]}"
                ),
                "action_ids": [action_id],
                "policy_proposition": _policy_proposition(
                    by_id[action_id]["accepted_exact_action_meaning"]
                ),
                "grouping_rationale": (
                    "This accepted exact action states one self-contained policy choice; "
                    "no same-parent or topical relationship safely establishes a broader episode."
                ),
                "semantic_grouping_evidence": [
                    "The accepted action meaning itself establishes the bounded single-action proposition."
                ],
                "material_policy_differences": (
                    "Any topically related action uses a different measure, mechanism, target, package, or proposition unless separately reviewed."
                ),
                "competing_plausible_groupings": [],
                "additional_limitations": [],
                "confidence": by_id[action_id]["accepted_confidence"],
            }
        )

    episodes: list[dict[str, Any]] = []
    action_to_episode: dict[str, str] = {}
    for definition in definitions:
        ordered_ids = sorted(
            definition["action_ids"],
            key=lambda action_id: (
                candidate_by_id[action_id]["official_action_date"],
                _session_roll(action_id)[0],
                _session_roll(action_id)[1],
            ),
        )
        episode_records = [by_id[action_id] for action_id in ordered_ids]
        episode_candidates = [candidate_by_id[action_id] for action_id in ordered_ids]
        measure_ids = {row["exact_action_identity"] for row in episode_candidates}
        grouping_type = (
            "single_action"
            if len(ordered_ids) == 1
            else "cross_measure"
            if len(measure_ids) > 1
            else "same_measure_multi_action"
        )
        for action_id in ordered_ids:
            if action_id in action_to_episode:
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: duplicate primary episode membership"
                )
            action_to_episode[action_id] = definition["episode_id"]
        limitations = list(
            dict.fromkeys(
                [
                    *sum((row["accepted_limitations"] for row in episode_records), []),
                    *definition["additional_limitations"],
                    "This candidate establishes only episode organization and a direction derived from accepted exact-choice effects; it does not establish motive, ideology, a broader pattern, or synthesis.",
                ]
            )
        )
        episode = {
            "schema_version": EPISODE_SCHEMA_VERSION,
            "episode_id": definition["episode_id"],
            "policy_proposition": definition["policy_proposition"],
            "member_direction_candidate": _direction(episode_records),
            "direction_derivation": {
                "accepted_position_effects_by_action": {
                    row["action_id"]: row["accepted_exact_choice_position_effect"]
                    for row in episode_records
                },
                "rule": "Derive only from M11D accepted exact-choice position effects after episode membership is proposed; never derive from raw Yea/Nay, party, sponsor, ideology, or expected behavior.",
            },
            "grouping_type": grouping_type,
            "primary_action_ids": ordered_ids,
            "actions": [
                {
                    "action_id": row["action_id"],
                    "official_action_date": candidate["official_action_date"],
                    "exact_action_identity": candidate["exact_action_identity"],
                    "action_role": _role(candidate),
                    "accepted_interpretation_record_id": row["record_id"],
                    "accepted_interpretation_record_subject_sha256": row[
                        "record_subject_sha256"
                    ],
                    "accepted_exact_action_meaning": row[
                        "accepted_exact_action_meaning"
                    ],
                    "accepted_exact_choice_position_effect": row[
                        "accepted_exact_choice_position_effect"
                    ],
                    "accepted_limitations": row["accepted_limitations"],
                    "source_references": row["source_references"],
                }
                for row, candidate in zip(
                    episode_records, episode_candidates, strict=True
                )
            ],
            "grouping_rationale": definition["grouping_rationale"],
            "semantic_grouping_evidence": definition["semantic_grouping_evidence"],
            "relevant_contrast_ids": sorted(
                {
                    contrast_id
                    for action_id in ordered_ids
                    for contrast_id in contrast_by_action[action_id]
                }
            ),
            "material_policy_differences": definition["material_policy_differences"],
            "material_limitations": limitations,
            "competing_plausible_groupings": definition[
                "competing_plausible_groupings"
            ],
            "confidence": definition["confidence"],
            "human_review_priority": (
                "cross_measure_high"
                if grouping_type == "cross_measure"
                else "multi_action_high"
                if grouping_type == "same_measure_multi_action"
                else "routine_single_action"
            ),
            "candidate": True,
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        }
        episodes.append(seal(episode, "episode_subject_sha256"))

    episodes.sort(
        key=lambda episode: (
            max(action["official_action_date"] for action in episode["actions"]),
            episode["episode_id"],
        ),
        reverse=True,
    )
    accounting = [
        seal(
            {
                "action_id": action_id,
                "primary_accounting_state": "assigned_primary_episode_candidate",
                "primary_episode_id": action_to_episode[action_id],
                "accepted_interpretation_record_id": by_id[action_id]["record_id"],
                "accepted_interpretation_record_subject_sha256": by_id[action_id][
                    "record_subject_sha256"
                ],
            },
            "accounting_subject_sha256",
        )
        for action_id in sorted(by_id)
    ]
    episode_subject = {
        **deepcopy(subject),
        "input_bindings": deepcopy(input_bindings),
        "accepted_action_count": len(records),
        "episode_count": len(episodes),
        "single_action_episode_count": sum(
            len(row["primary_action_ids"]) == 1 for row in episodes
        ),
        "multi_action_episode_count": sum(
            len(row["primary_action_ids"]) > 1 for row in episodes
        ),
        "cross_measure_episode_count": sum(
            row["grouping_type"] == "cross_measure" for row in episodes
        ),
        "episodes": episodes,
        "action_accounting": accounting,
        "action_accounting_counts": dict(
            Counter(row["primary_accounting_state"] for row in accounting)
        ),
        "ambiguous_or_unassigned_action_ids": [],
        "blocked_actions": [deepcopy(blocked_action)],
        "contrast_reviews": contrast_reviews,
        "episode_candidate_generation_state": "complete_non_authorizing",
        "episode_acceptance_state": "not_started_not_authorized",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    value = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_role": "detached_non_authorizing_policy_episode_candidates",
        "candidate": True,
        "accepted": False,
        "canonical": False,
        "public": False,
        "authorizing": False,
        "production_selectable": False,
        "subject": episode_subject,
    }
    return seal(value, "episode_candidate_subject_sha256")


def validate_candidate_batch(
    *,
    batch: dict[str, Any],
    implementation: dict[str, Any],
    candidate_artifact: dict[str, Any],
    permitted_cross_measure_sets: set[frozenset[str]],
    prohibited_grouped_sets: list[set[str]],
    blocked_action_id: str,
) -> dict[str, Any]:
    verify_seal(batch, "episode_candidate_subject_sha256", "candidate batch")
    if not (
        batch["candidate"]
        and batch["accepted"] is False
        and batch["canonical"] is False
        and batch["public"] is False
        and batch["authorizing"] is False
        and batch["production_selectable"] is False
    ):
        raise PolicyEpisodeCandidateError("candidate authority boundary differs")
    subject = batch["subject"]
    records = implementation["subject"]["implementation_records"]
    by_id = {row["action_id"]: row for row in records}
    candidate_by_id = {
        row["action_id"]: row for row in candidate_artifact["subject"]["candidates"]
    }
    if set(by_id) != set(candidate_by_id):
        raise PolicyEpisodeCandidateError("upstream action sets differ")
    if blocked_action_id in by_id:
        raise PolicyEpisodeCandidateError("blocked action entered M11D implementation")
    if subject["blocked_actions"] != [
        {
            "action_id": blocked_action_id,
            "state": "source_blocked_uninterpreted_unavailable_for_episode_construction",
            "primary_episode_id": None,
        }
    ]:
        raise PolicyEpisodeCandidateError("blocked-action boundary differs")

    primary: dict[str, str] = {}
    cross_measure_count = 0
    for episode in subject["episodes"]:
        verify_seal(episode, "episode_subject_sha256", episode["episode_id"])
        action_ids = episode["primary_action_ids"]
        if action_ids != [row["action_id"] for row in episode["actions"]]:
            raise PolicyEpisodeCandidateError("episode action sequence differs")
        if len(action_ids) != len(set(action_ids)):
            raise PolicyEpisodeCandidateError("duplicate action within episode")
        if blocked_action_id in action_ids:
            raise PolicyEpisodeCandidateError("blocked action included in episode")
        for prohibited in prohibited_grouped_sets:
            if len(set(action_ids) & prohibited) > 1:
                raise PolicyEpisodeCandidateError(
                    "same-topic or parent-package overreach detected"
                )
        measure_ids = {
            candidate_by_id[action_id]["exact_action_identity"]
            for action_id in action_ids
        }
        if len(measure_ids) > 1:
            cross_measure_count += 1
            if frozenset(action_ids) not in permitted_cross_measure_sets:
                raise PolicyEpisodeCandidateError(
                    "cross-measure grouping lacks governed semantic evidence"
                )
            if episode["grouping_type"] != "cross_measure":
                raise PolicyEpisodeCandidateError("cross-measure type differs")
        for action in episode["actions"]:
            action_id = action["action_id"]
            if action_id in primary:
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: duplicate primary episode membership"
                )
            if action_id not in by_id:
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: episode action outside M11D implementation"
                )
            primary[action_id] = episode["episode_id"]
            record = by_id[action_id]
            if not (
                action["accepted_interpretation_record_id"] == record["record_id"]
                and action["accepted_interpretation_record_subject_sha256"]
                == record["record_subject_sha256"]
                and action["accepted_exact_action_meaning"]
                == record["accepted_exact_action_meaning"]
                and action["accepted_exact_choice_position_effect"]
                == record["accepted_exact_choice_position_effect"]
                and action["accepted_limitations"] == record["accepted_limitations"]
                and action["source_references"] == record["source_references"]
            ):
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: accepted interpretation binding differs"
                )
            candidate = candidate_by_id[action_id]
            if not (
                action["official_action_date"] == candidate["official_action_date"]
                and action["exact_action_identity"]
                == candidate["exact_action_identity"]
                and action["action_role"] == _role(candidate)
            ):
                raise PolicyEpisodeCandidateError(
                    f"{action_id}: action chronology or role differs"
                )
        episode_records = [by_id[action_id] for action_id in action_ids]
        if episode["member_direction_candidate"] != _direction(episode_records):
            raise PolicyEpisodeCandidateError(
                "episode direction not derived from accepted meaning/effect"
            )
        expected_effects = {
            row["action_id"]: row["accepted_exact_choice_position_effect"]
            for row in episode_records
        }
        if episode["direction_derivation"]["accepted_position_effects_by_action"] != (
            expected_effects
        ):
            raise PolicyEpisodeCandidateError(
                "episode direction derivation input differs"
            )
        if not (
            episode["candidate"]
            and episode["accepted"] is False
            and episode["canonical"] is False
            and episode["public"] is False
            and episode["authorizing"] is False
        ):
            raise PolicyEpisodeCandidateError("episode authority boundary differs")

    if set(primary) != set(by_id):
        raise PolicyEpisodeCandidateError(
            "accepted action omitted from episode accounting"
        )
    accounting = subject["action_accounting"]
    if len(accounting) != len(by_id):
        raise PolicyEpisodeCandidateError("action accounting count differs")
    for row in accounting:
        verify_seal(row, "accounting_subject_sha256", row["action_id"])
        record = by_id[row["action_id"]]
        if not (
            row["primary_accounting_state"] == "assigned_primary_episode_candidate"
            and row["primary_episode_id"] == primary[row["action_id"]]
            and row["accepted_interpretation_record_id"] == record["record_id"]
            and row["accepted_interpretation_record_subject_sha256"]
            == record["record_subject_sha256"]
        ):
            raise PolicyEpisodeCandidateError("action accounting binding differs")
    if subject["ambiguous_or_unassigned_action_ids"]:
        raise PolicyEpisodeCandidateError("unexpected ambiguous/unassigned action")
    if subject["downstream_authorizations"] != DOWNSTREAM_AUTHORIZATIONS:
        raise PolicyEpisodeCandidateError("downstream authority leakage")
    if not (
        subject["episode_acceptance_state"] == "not_started_not_authorized"
        and subject["episode_candidate_generation_state"] == "complete_non_authorizing"
    ):
        raise PolicyEpisodeCandidateError("candidate/acceptance state differs")
    return {
        "episode_count": len(subject["episodes"]),
        "single_action_episode_count": sum(
            len(row["primary_action_ids"]) == 1 for row in subject["episodes"]
        ),
        "multi_action_episode_count": sum(
            len(row["primary_action_ids"]) > 1 for row in subject["episodes"]
        ),
        "cross_measure_episode_count": cross_measure_count,
        "assigned_action_count": len(primary),
        "ambiguous_or_unassigned_count": 0,
        "blocked_count": 1,
    }


def build_human_decision_template(
    *, batch: dict[str, Any], artifact_id: str
) -> dict[str, Any]:
    decisions = [
        seal(
            {
                "episode_id": episode["episode_id"],
                "episode_subject_sha256": episode["episode_subject_sha256"],
                "grouping_type": episode["grouping_type"],
                "human_review_priority": episode["human_review_priority"],
                "allowed_decisions": [
                    "accept_candidate_as_written",
                    "accept_with_bounded_revision",
                    "reject_and_reassign_actions",
                    "retain_actions_unassigned_ambiguous",
                ],
                "selected_decision": None,
                "bounded_revision": None,
                "reviewer_id": None,
                "reviewer_authority": None,
                "decision_timestamp": None,
            },
            "decision_subject_sha256",
        )
        for episode in batch["subject"]["episodes"]
    ]
    value = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "candidate_batch": {
            "artifact_id": batch["artifact_id"],
            "episode_candidate_subject_sha256": batch[
                "episode_candidate_subject_sha256"
            ],
        },
        "decision_state": "awaiting_human_policy_episode_review",
        "decision_count": len(decisions),
        "decisions": decisions,
        "selected_batch_decision": None,
        "explicit_non_acceptance": "This empty template records no episode acceptance or downstream authority.",
        "accepted": False,
        "canonical": False,
        "public": False,
        "authorizing": False,
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    return seal(value, "decision_template_subject_sha256")
