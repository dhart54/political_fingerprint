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
REVIEWER_AUTHORITY = "full_record_behavioral_semantic_ir_review_authority_v1"


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


def verify_subject_seal(value: dict[str, Any], field: str, label: str) -> None:
    if value.get(field) != digest(value["subject"]):
        raise BehavioralSemanticIRDecisionError(f"{label}: {field} differs")


def _propositions(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return candidate["compiled_candidate_ir"]["proposition_graph"]["propositions"]


def _proposition_accounting(
    propositions: list[dict[str, Any]],
) -> dict[str, int]:
    types = Counter(row["proposition_type"] for row in propositions)
    relevance = Counter(row["conclusion_relevance"] for row in propositions)
    return {
        "total": len(propositions),
        "repeated_pattern": types["repeated_pattern"],
        "trajectory": types["trajectory"],
        "notable_choice": types["notable_choice"],
        "primary_conclusion_relevance": relevance["primary"],
        "limiting_conclusion_relevance": relevance["limiting"],
        "excluded_conclusion_relevance": relevance["excluded"],
    }


def _episode_disposition_accounting(
    ledger: list[dict[str, Any]],
) -> dict[str, int]:
    dispositions = Counter(row["disposition"] for row in ledger)
    primary_rows = Counter(
        row["episode_id"] for row in ledger if row["primary_proposition_id"] is not None
    )
    result = {
        "accepted_episode_count": len(ledger),
        "repeated_pattern_evidence_episode_count": dispositions[
            "supports_proposed_repeated_pattern"
        ],
        "trajectory_evidence_episode_count": dispositions[
            "supports_proposed_trajectory"
        ],
        "notable_choice_evidence_episode_count": dispositions[
            "supports_proposed_notable_choice"
        ],
        "contrast_only_episode_count": dispositions["retained_as_limit_or_contrast"],
        "no_safe_proposition_episode_count": dispositions[
            "no_safe_higher_level_behavioral_proposition"
        ],
        "primary_overlap_count": sum(count > 1 for count in primary_rows.values()),
    }
    if dispositions["unused_non_directional_evidence"]:
        result["unused_non_directional_evidence_episode_count"] = dispositions[
            "unused_non_directional_evidence"
        ]
    return result


def _final_accounting(
    *,
    propositions: list[dict[str, Any]],
    ledger: list[dict[str, Any]],
    blocked_action_ids: set[str],
) -> dict[str, int]:
    proposition_counts = _proposition_accounting(propositions)
    episode_counts = _episode_disposition_accounting(ledger)
    result = {
        "accepted_proposition_count": proposition_counts["total"],
        "repeated_pattern_count": proposition_counts["repeated_pattern"],
        "trajectory_count": proposition_counts["trajectory"],
        "notable_choice_count": proposition_counts["notable_choice"],
        "primary_evidence_episode_count": (
            episode_counts["repeated_pattern_evidence_episode_count"]
            + episode_counts["trajectory_evidence_episode_count"]
            + episode_counts["notable_choice_evidence_episode_count"]
        ),
        "primary_overlap_count": episode_counts["primary_overlap_count"],
        "accepted_episode_count": episode_counts["accepted_episode_count"],
        "contrast_only_episode_count": episode_counts["contrast_only_episode_count"],
        "no_safe_proposition_episode_count": episode_counts[
            "no_safe_proposition_episode_count"
        ],
        "blocked_action_count": len(blocked_action_ids),
    }
    if "unused_non_directional_evidence_episode_count" in episode_counts:
        result["unused_non_directional_evidence_episode_count"] = episode_counts[
            "unused_non_directional_evidence_episode_count"
        ]
    return result


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
    authority_decision = subject.get("authority_decision")
    if authority_decision is not None and not (
        authority_decision["reviewer_id"].strip()
        and authority_decision["reviewer_authority"] == REVIEWER_AUTHORITY
    ):
        raise BehavioralSemanticIRDecisionError(
            "reviewer identity or authority differs"
        )
    if not (
        subject["candidate_binding"]["artifact_id"] == candidate["artifact_id"]
        and subject["candidate_binding"]["candidate_subject_sha256"]
        == candidate["candidate_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError("candidate authority binding differs")
    blocked_action_ids = [row["action_id"] for row in subject["blocked_actions"]]
    if not (
        len(blocked_action_ids) == len(set(blocked_action_ids))
        and set(blocked_action_ids) == set(candidate["blocked_action_ids"])
    ):
        raise BehavioralSemanticIRDecisionError("governed blocked action set differs")

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
    if subject["accepted_proposition_accounting"] != _proposition_accounting(
        propositions
    ):
        raise BehavioralSemanticIRDecisionError(
            "accepted proposition accounting differs"
        )
    ledger = subject["accepted_episode_disposition_ledger"]
    if len({row["episode_id"] for row in ledger}) != len(ledger):
        raise BehavioralSemanticIRDecisionError("duplicate episode disposition")
    expected_episode_accounting = _episode_disposition_accounting(ledger)
    if expected_episode_accounting["primary_overlap_count"] != 0:
        raise BehavioralSemanticIRDecisionError("primary episode overlap")
    if (
        subject["accepted_episode_disposition_accounting"]
        != expected_episode_accounting
    ):
        raise BehavioralSemanticIRDecisionError(
            "accepted episode disposition summary differs"
        )
    return dict(counts)


def validate_implementation(
    implementation: dict[str, Any],
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    m11f_authority: dict[str, Any] | None = None,
    m11f_implementation: dict[str, Any] | None = None,
    m11d_implementation: dict[str, Any] | None = None,
    accepted_episode_authority: dict[str, Any] | None = None,
    accepted_episode_implementation: dict[str, Any] | None = None,
    accepted_action_interpretation_implementation: dict[str, Any] | None = None,
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
    if (m11f_authority is None) == (accepted_episode_authority is None):
        raise BehavioralSemanticIRDecisionError(
            "provide exactly one accepted policy-episode authority"
        )
    if (m11f_implementation is None) == (accepted_episode_implementation is None):
        raise BehavioralSemanticIRDecisionError(
            "provide exactly one accepted policy-episode implementation"
        )
    if (m11d_implementation is None) == (
        accepted_action_interpretation_implementation is None
    ):
        raise BehavioralSemanticIRDecisionError(
            "provide exactly one accepted action-interpretation implementation"
        )
    episode_authority = accepted_episode_authority or m11f_authority
    episode_implementation = accepted_episode_implementation or m11f_implementation
    action_implementation = (
        accepted_action_interpretation_implementation or m11d_implementation
    )
    assert episode_authority is not None
    assert episode_implementation is not None
    assert action_implementation is not None

    def binding(container: dict[str, Any], generic: str, legacy: str) -> dict[str, Any]:
        present = [name for name in (generic, legacy) if name in container]
        if len(present) != 1:
            raise BehavioralSemanticIRDecisionError(
                f"provide exactly one {generic} binding"
            )
        return container[present[0]]

    verify_seal(
        episode_authority, "authority_subject_sha256", "policy-episode authority"
    )
    verify_seal(
        episode_implementation,
        "implementation_subject_sha256",
        "policy-episode implementation",
    )
    verify_subject_seal(
        action_implementation,
        "implementation_subject_sha256",
        "action-interpretation implementation",
    )
    episode_subject = episode_implementation["subject"]
    action_binding = binding(
        episode_subject,
        "interpretation_implementation_binding",
        "m11d_implementation_binding",
    )
    if not (
        episode_subject["authority_binding"]["artifact_id"]
        == episode_authority["artifact_id"]
        and episode_subject["authority_binding"]["authority_subject_sha256"]
        == episode_authority["authority_subject_sha256"]
        and action_binding["artifact_id"] == action_implementation["artifact_id"]
        and action_binding["implementation_subject_sha256"]
        == action_implementation["implementation_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError(
            "accepted policy-episode lineage binding differs"
        )
    episode_authority_binding = binding(
        subject, "policy_episode_authority_binding", "m11f_authority_binding"
    )
    episode_implementation_binding = binding(
        subject,
        "policy_episode_implementation_binding",
        "m11f_implementation_binding",
    )
    if not (
        episode_authority_binding["artifact_id"] == episode_authority["artifact_id"]
        and episode_authority_binding["authority_subject_sha256"]
        == episode_authority["authority_subject_sha256"]
        and episode_implementation_binding["artifact_id"]
        == episode_implementation["artifact_id"]
        and episode_implementation_binding["implementation_subject_sha256"]
        == episode_implementation["implementation_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError("policy-episode identity differs")
    action_interpretation_binding = binding(
        subject,
        "action_interpretation_implementation_binding",
        "m11d_implementation_binding",
    )
    if not (
        action_interpretation_binding["artifact_id"]
        == action_implementation["artifact_id"]
        and action_interpretation_binding["implementation_subject_sha256"]
        == action_implementation["implementation_subject_sha256"]
    ):
        raise BehavioralSemanticIRDecisionError(
            "action-interpretation identity differs"
        )

    candidate_props = _propositions(candidate)
    by_id = {row["proposition_id"]: row for row in candidate_props}
    decisions = {
        row["proposition_id"]: row
        for row in authority["subject"]["proposition_decisions"]
    }
    episode_records = {
        row["episode_id"]: row
        for row in episode_implementation["subject"]["implementation_records"]
    }
    if len(episode_records) != len(
        episode_implementation["subject"]["implementation_records"]
    ):
        raise BehavioralSemanticIRDecisionError("duplicate policy-episode identity")
    action_records = {
        row["action_id"]: row
        for row in action_implementation["subject"]["implementation_records"]
    }
    if len(action_records) != len(
        action_implementation["subject"]["implementation_records"]
    ):
        raise BehavioralSemanticIRDecisionError(
            "duplicate action-interpretation identity"
        )
    for action in action_records.values():
        verify_seal(
            action,
            "record_subject_sha256",
            f"accepted action {action['action_id']}",
        )
    blocked_rows = authority["subject"]["blocked_actions"]
    blocked_action_ids = {row["action_id"] for row in blocked_rows}
    if len(blocked_action_ids) != len(blocked_rows):
        raise BehavioralSemanticIRDecisionError("duplicate governed blocked action")
    if subject["blocked_actions"] != blocked_rows:
        raise BehavioralSemanticIRDecisionError("blocked action binding differs")

    episode_action_owners: Counter[str] = Counter()
    for episode in episode_records.values():
        verify_seal(
            episode,
            "record_subject_sha256",
            f"accepted episode {episode['episode_id']}",
        )
        action_ids = [row["action_id"] for row in episode["actions"]]
        if not (
            action_ids == episode["primary_action_ids"]
            and len(action_ids) == len(set(action_ids))
        ):
            raise BehavioralSemanticIRDecisionError(
                "policy-episode action membership differs"
            )
        episode_action_owners.update(action_ids)
    if any(count != 1 for count in episode_action_owners.values()):
        raise BehavioralSemanticIRDecisionError(
            "policy-episode action assigned more than once"
        )
    if set(episode_action_owners) != set(action_records):
        raise BehavioralSemanticIRDecisionError(
            "policy episodes do not exhaust accepted action interpretations"
        )
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
        if blocked_action_ids.intersection(source["evidence_action_ids"]):
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
                source_action = action_records.get(action["action_id"])
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
                        "action-interpretation lineage differs"
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

    implemented_propositions = [row["accepted_candidate_content"] for row in records]
    expected = _final_accounting(
        propositions=implemented_propositions,
        ledger=ledger,
        blocked_action_ids=blocked_action_ids,
    )
    if subject["final_accounting"] != expected:
        raise BehavioralSemanticIRDecisionError("final semantic accounting differs")
    return expected
