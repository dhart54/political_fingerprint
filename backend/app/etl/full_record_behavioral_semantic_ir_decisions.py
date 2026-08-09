"""Generic fail-closed contract for human-reviewed Behavioral Semantic IR."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from typing import Any


DOWNSTREAM_AUTHORIZATIONS = {
    "synthesis": False,
    "public_wording": False,
    "publication": False,
    "production_persistence": False,
    "database_writes": False,
    "deployment": False,
}


class BehavioralSemanticIRDecisionError(ValueError):
    """Raised when authority or implementation differs from reviewed content."""


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
        raise BehavioralSemanticIRDecisionError(f"{label}: {field} differs")


def _propositions(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return candidate["compiled_candidate_ir"]["proposition_graph"]["propositions"]


def validate_authority(
    authority: dict[str, Any], *, candidate: dict[str, Any]
) -> dict[str, int]:
    verify_seal(authority, "authority_subject_sha256", "behavioral authority")
    if not (
        authority.get("accepted") is True
        and authority.get("immutable") is True
        and authority.get("canonical_internal_behavioral_semantic_ir_authority") is True
    ):
        raise BehavioralSemanticIRDecisionError("authority is not accepted/immutable")
    subject = authority["subject"]
    if any(subject["downstream_authorizations"].values()):
        raise BehavioralSemanticIRDecisionError("downstream authority leakage")
    if not (
        subject["candidate_binding"]["artifact_id"] == candidate["artifact_id"]
        and subject["candidate_binding"]["candidate_subject_sha256"]
        == candidate["candidate_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError("candidate authority binding differs")

    propositions = _propositions(candidate)
    by_id = {row["proposition_id"]: row for row in propositions}
    decisions = subject["proposition_decisions"]
    if len(by_id) != len(propositions) or len(decisions) != len(propositions):
        raise BehavioralSemanticIRDecisionError("proposition decision count differs")
    if {row["proposition_id"] for row in decisions} != set(by_id):
        raise BehavioralSemanticIRDecisionError("proposition decision set differs")
    for decision in decisions:
        verify_seal(
            decision,
            "decision_subject_sha256",
            f"decision {decision['proposition_id']}",
        )
        candidate_row = by_id[decision["proposition_id"]]
        if not (
            decision["decision"] == "accept_candidate_as_written"
            and decision["candidate_proposition_content_sha256"]
            == digest(candidate_row)
            and decision["candidate_proposition_type"]
            == candidate_row["proposition_type"]
            and decision["candidate_direction"] == candidate_row["direction"]
            and decision["candidate_conclusion_relevance"]
            == candidate_row["conclusion_relevance"]
        ):
            raise BehavioralSemanticIRDecisionError("accepted proposition differs")
    counts = Counter(row["decision"] for row in decisions)
    if subject["decision_accounting"] != dict(sorted(counts.items())):
        raise BehavioralSemanticIRDecisionError("decision accounting differs")
    if (
        subject["accepted_episode_disposition_ledger"]
        != candidate["compiled_candidate_ir"]["episode_accounting"]
    ):
        raise BehavioralSemanticIRDecisionError("accepted episode ledger differs")
    proposition_counts = Counter(row["proposition_type"] for row in propositions)
    relevance_counts = Counter(row["conclusion_relevance"] for row in propositions)
    if not (
        subject["accepted_proposition_accounting"]
        == {
            "total": 15,
            "repeated_pattern": 8,
            "trajectory": 1,
            "notable_choice": 6,
            "primary_conclusion_relevance": 8,
            "limiting_conclusion_relevance": 1,
            "excluded_conclusion_relevance": 6,
        }
        and proposition_counts
        == Counter({"repeated_pattern": 8, "trajectory": 1, "notable_choice": 6})
        and relevance_counts == Counter({"primary": 8, "excluded": 6, "limiting": 1})
    ):
        raise BehavioralSemanticIRDecisionError(
            "accepted proposition accounting differs"
        )
    disposition_counts = Counter(
        row["disposition"] for row in subject["accepted_episode_disposition_ledger"]
    )
    if disposition_counts != Counter(
        {
            "supports_proposed_repeated_pattern": 24,
            "supports_proposed_trajectory": 2,
            "supports_proposed_notable_choice": 6,
            "retained_as_limit_or_contrast": 24,
            "no_safe_higher_level_behavioral_proposition": 25,
        }
    ):
        raise BehavioralSemanticIRDecisionError("accepted episode accounting differs")
    if subject["accepted_episode_disposition_accounting"] != {
        "accepted_episode_count": 81,
        "repeated_pattern_evidence_episode_count": 24,
        "trajectory_evidence_episode_count": 2,
        "notable_choice_evidence_episode_count": 6,
        "contrast_only_episode_count": 24,
        "no_safe_proposition_episode_count": 25,
        "primary_overlap_count": 0,
    }:
        raise BehavioralSemanticIRDecisionError(
            "accepted episode disposition summary differs"
        )
    return dict(counts)


def validate_implementation(
    implementation: dict[str, Any],
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    m11f_authority: dict[str, Any],
    m11f_implementation: dict[str, Any],
    m11d_implementation: dict[str, Any],
    blocked_action_id: str,
) -> dict[str, int]:
    validate_authority(authority, candidate=candidate)
    verify_seal(
        implementation,
        "implementation_subject_sha256",
        "behavioral implementation",
    )
    subject = implementation["subject"]
    if any(subject["downstream_authorizations"].values()):
        raise BehavioralSemanticIRDecisionError("downstream authority leakage")
    if not (
        subject["authority_binding"]["artifact_id"] == authority["artifact_id"]
        and subject["authority_binding"]["authority_subject_sha256"]
        == authority["authority_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError("implementation authority differs")
    if not (
        subject["m11f_authority_binding"]["artifact_id"]
        == m11f_authority["artifact_id"]
        and subject["m11f_authority_binding"]["authority_subject_sha256"]
        == m11f_authority["authority_subject_sha256"]
        and subject["m11f_implementation_binding"]["artifact_id"]
        == m11f_implementation["artifact_id"]
        and subject["m11f_implementation_binding"]["implementation_subject_sha256"]
        == m11f_implementation["implementation_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError("M11F identity differs")
    if not (
        subject["m11d_implementation_binding"]["artifact_id"]
        == m11d_implementation["artifact_id"]
        and subject["m11d_implementation_binding"]["implementation_subject_sha256"]
        == m11d_implementation["implementation_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError("M11D identity differs")

    candidate_props = _propositions(candidate)
    by_id = {row["proposition_id"]: row for row in candidate_props}
    decisions = {
        row["proposition_id"]: row
        for row in authority["subject"]["proposition_decisions"]
    }
    episode_records = {
        row["episode_id"]: row
        for row in m11f_implementation["subject"]["implementation_records"]
    }
    if len(episode_records) != 81:
        raise BehavioralSemanticIRDecisionError("M11F episode set differs")
    m11d_records = {
        row["action_id"]: row
        for row in m11d_implementation["subject"]["implementation_records"]
    }
    if len(m11d_records) != 81:
        raise BehavioralSemanticIRDecisionError("M11D action set differs")
    records = subject["implementation_records"]
    if len(records) != len(by_id) or {row["proposition_id"] for row in records} != set(
        by_id
    ):
        raise BehavioralSemanticIRDecisionError(
            "implementation proposition set differs"
        )

    primary_owners: Counter[str] = Counter()
    primary_owner_ids: dict[str, list[str]] = {}
    for record in records:
        verify_seal(
            record,
            "record_subject_sha256",
            f"implementation {record['proposition_id']}",
        )
        source = by_id[record["proposition_id"]]
        decision = decisions[record["proposition_id"]]
        if not (
            record["accepted_candidate_content"] == source
            and record["accepted_candidate_content_sha256"] == digest(source)
            and record["authority_decision_subject_sha256"]
            == decision["decision_subject_sha256"]
            and record["canonical_internal_behavioral_semantic_ir"] is True
            and not any(record["downstream_authorizations"].values())
        ):
            raise BehavioralSemanticIRDecisionError(
                "implemented proposition differs from accepted candidate"
            )
        if blocked_action_id in source["evidence_action_ids"]:
            raise BehavioralSemanticIRDecisionError("blocked action entered evidence")
        lineage = record["evidence_lineage"]
        if [row["episode_id"] for row in lineage] != source["evidence_episode_ids"]:
            raise BehavioralSemanticIRDecisionError("evidence episode lineage differs")
        derived_actions: list[str] = []
        for row in lineage:
            episode = episode_records.get(row["episode_id"])
            if episode is None or not (
                row["episode_record_id"] == episode["record_id"]
                and row["episode_record_subject_sha256"]
                == episode["record_subject_sha256"]
                and row["member_direction"] == episode["member_direction"]
            ):
                raise BehavioralSemanticIRDecisionError(
                    "accepted episode binding differs"
                )
            expected_actions = [
                {
                    "action_id": action["action_id"],
                    "accepted_interpretation_record_id": action[
                        "accepted_interpretation_record_id"
                    ],
                    "accepted_interpretation_record_subject_sha256": action[
                        "accepted_interpretation_record_subject_sha256"
                    ],
                }
                for action in episode["actions"]
            ]
            if row["accepted_action_lineage"] != expected_actions:
                raise BehavioralSemanticIRDecisionError(
                    "accepted action lineage differs"
                )
            for action in episode["actions"]:
                source_action = m11d_records.get(action["action_id"])
                if source_action is None or not (
                    action["accepted_interpretation_record_id"]
                    == source_action["record_id"]
                    and action["accepted_interpretation_record_subject_sha256"]
                    == source_action["record_subject_sha256"]
                    and action["accepted_exact_action_meaning"]
                    == source_action["accepted_exact_action_meaning"]
                    and action["accepted_exact_choice_position_effect"]
                    == source_action["accepted_exact_choice_position_effect"]
                ):
                    raise BehavioralSemanticIRDecisionError(
                        "M11D action interpretation lineage differs"
                    )
            derived_actions.extend(episode["primary_action_ids"])
            primary_owners[row["episode_id"]] += 1
            primary_owner_ids.setdefault(row["episode_id"], []).append(
                record["proposition_id"]
            )
        if not (
            len(derived_actions) == len(set(derived_actions))
            and sorted(derived_actions) == sorted(source["evidence_action_ids"])
        ):
            raise BehavioralSemanticIRDecisionError("derived evidence actions differ")

    if any(count != 1 for count in primary_owners.values()):
        raise BehavioralSemanticIRDecisionError("undeclared primary evidence overlap")
    ledger = candidate["compiled_candidate_ir"]["episode_accounting"]
    if not (
        subject["accepted_episode_disposition_ledger"] == ledger
        and authority["subject"]["accepted_episode_disposition_ledger"] == ledger
    ):
        raise BehavioralSemanticIRDecisionError("episode disposition ledger differs")
    ledger_by_episode = {row["episode_id"]: row for row in ledger}
    if set(ledger_by_episode) != set(episode_records):
        raise BehavioralSemanticIRDecisionError("complete episode accounting differs")
    for episode_id, disposition in ledger_by_episode.items():
        expected_owner = disposition["primary_proposition_id"]
        if expected_owner is None and primary_owners[episode_id]:
            raise BehavioralSemanticIRDecisionError(
                "non-primary episode silently promoted"
            )
        if expected_owner is not None and not (
            primary_owners[episode_id] == 1
            and primary_owner_ids[episode_id] == [expected_owner]
        ):
            raise BehavioralSemanticIRDecisionError("primary episode owner differs")

    counts = Counter(
        row["accepted_candidate_content"]["proposition_type"] for row in records
    )
    expected = {
        "accepted_proposition_count": 15,
        "repeated_pattern_count": 8,
        "trajectory_count": 1,
        "notable_choice_count": 6,
        "primary_evidence_episode_count": 32,
        "primary_overlap_count": 0,
        "accepted_episode_count": 81,
        "contrast_only_episode_count": 24,
        "no_safe_proposition_episode_count": 25,
        "blocked_action_count": 1,
    }
    if not (
        counts == Counter({"repeated_pattern": 8, "trajectory": 1, "notable_choice": 6})
        and subject["final_accounting"] == expected
    ):
        raise BehavioralSemanticIRDecisionError("final semantic accounting differs")
    return expected
