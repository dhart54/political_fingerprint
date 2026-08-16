from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from backend.app.etl.full_record_action_interpretation import (
    BLOCKED_DISPOSITION,
    validate_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import sha256_json


AUTHORITY_SCHEMA_VERSION = "full_record_action_interpretation_authority_v1"
IMPLEMENTATION_SCHEMA_VERSION = (
    "full_record_action_interpretation_decision_implementation_v1"
)
ACCEPTED_DECISION = "accept_candidate_as_written"
IMPLEMENTATION_STATE = "implemented_human_accepted_as_written"
REVIEWER_AUTHORITY = "full_record_action_interpretation_review_authority_v1"

DOWNSTREAM_AUTHORIZATIONS = {
    "policy_episode_construction": False,
    "policy_episode_acceptance": False,
    "semantic_ir": False,
    "synthesis": False,
    "public_wording": False,
    "publication": False,
    "production_persistence": False,
    "deployment": False,
}


class ActionInterpretationDecisionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionInterpretationDecisionError(message)


def _seal(value: dict[str, Any], digest_field: str) -> dict[str, Any]:
    return {**value, digest_field: sha256_json(value)}


def _subject_identity(candidate_artifact: dict[str, Any]) -> dict[str, Any]:
    subject = candidate_artifact["subject"]
    return {
        "member_id": subject["member_id"],
        "legislator_id": subject["legislator_id"],
        "issue_id": subject["issue_id"],
        "congress": subject["congress"],
        "official_cutoff": deepcopy(subject["official_cutoff"]),
    }


def build_authority_record(
    *,
    candidate_artifact: dict[str, Any],
    readiness_artifact: dict[str, Any],
    repository_root: Path,
    artifact_id: str,
    candidate_file_sha256: str,
    decision_template_binding: dict[str, str],
    accepted_pr: int,
    accepted_head: str,
    post_merge_main: str,
    reviewer_identity: str,
    reviewer_authority: str,
    decision_timestamp: str,
) -> dict[str, Any]:
    _require(bool(reviewer_identity.strip()), "reviewer identity must be nonempty")
    _require(
        reviewer_authority == REVIEWER_AUTHORITY,
        "reviewer authority class differs",
    )
    validate_candidate_artifact(
        candidate_artifact,
        readiness_artifact=readiness_artifact,
        repository_root=repository_root,
    )
    candidates = candidate_artifact["subject"]["candidates"]
    decisions = []
    for candidate in sorted(candidates, key=lambda item: item["action_id"]):
        decision_subject = {
            "action_id": candidate["action_id"],
            "candidate_id": candidate["candidate_id"],
            "candidate_content_subject_sha256": candidate[
                "candidate_content_subject_sha256"
            ],
            "decision": ACCEPTED_DECISION,
            "accepted_exact_action_meaning": candidate["proposed_exact_action_meaning"],
            "accepted_exact_choice_position_effect": candidate[
                "proposed_member_position_effect"
            ],
            "accepted_confidence": candidate["confidence"],
            "accepted_limitations": deepcopy(candidate["limitations"]),
            "accepted_coverage_assessment": candidate["coverage_assessment"],
            "accepted_source_references": deepcopy(candidate["source_references"]),
            "accepted_evidence_map_id": candidate["evidence_map_id"],
            "accepted_evidence_map_subject_sha256": candidate[
                "evidence_map_subject_sha256"
            ],
        }
        decisions.append(_seal(decision_subject, "decision_subject_sha256"))

    blocked = [
        {
            "action_id": item["action_id"],
            "disposition": item["disposition"],
            "readiness_state": item["readiness_state"],
            "source_packet_sha256": item["source_packet_sha256"],
            "accepted_for_interpretation": False,
        }
        for item in candidate_artifact["subject"]["accounting"]
        if item["disposition"] == BLOCKED_DISPOSITION
    ]
    subject = {
        **_subject_identity(candidate_artifact),
        "authority_decision": {
            "reviewer_identity": reviewer_identity,
            "reviewer_authority": reviewer_authority,
            "decision": "approved_all_candidate_meanings_and_position_effects",
            "decision_timestamp": decision_timestamp,
        },
        "input_bindings": {
            "candidate_artifact": {
                "artifact_id": candidate_artifact["artifact_id"],
                "file_sha256": candidate_file_sha256,
                "interpretation_subject_sha256": candidate_artifact[
                    "interpretation_subject_sha256"
                ],
                "accepted_pr": accepted_pr,
                "accepted_head": accepted_head,
                "post_merge_main": post_merge_main,
            },
            "decision_template": deepcopy(decision_template_binding),
            "upstream_bindings": deepcopy(
                candidate_artifact["subject"]["upstream_bindings"]
            ),
        },
        "approved_universe_count": len(candidate_artifact["subject"]["action_ids"]),
        "accepted_decision_count": len(decisions),
        "source_blocked_count": len(blocked),
        "action_ids": deepcopy(candidate_artifact["subject"]["action_ids"]),
        "decisions": decisions,
        "source_blocked_actions": blocked,
        "decision_accounting": {ACCEPTED_DECISION: len(decisions)},
        "internal_action_interpretation_state": "human_accepted_internal",
        "internal_action_meanings_canonical": True,
        "canonical_semantic_acceptance": False,
        "presentation_boundary": (
            "Detailed accepted meanings are internal evidence-backed semantic inputs; "
            "later public wording must be separately authorized, concise by default, "
            "and progressively disclose detail and sources when useful."
        ),
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    return {
        "schema_version": AUTHORITY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_role": "immutable_human_action_interpretation_authority",
        "accepted": True,
        "immutable": True,
        "canonical_internal_action_interpretation_authority": True,
        "canonical_semantic_acceptance": False,
        "public": False,
        "publication_authorized": False,
        "production_selectable": False,
        "subject": subject,
        "authority_subject_sha256": sha256_json(subject),
    }


def validate_authority_record(
    authority: dict[str, Any], *, candidate_artifact: dict[str, Any]
) -> None:
    _require(
        authority.get("schema_version") == AUTHORITY_SCHEMA_VERSION,
        "authority schema version",
    )
    _require(authority.get("accepted") is True, "human authority not accepted")
    _require(authority.get("immutable") is True, "human authority not immutable")
    _require(
        authority.get("canonical_internal_action_interpretation_authority") is True
        and authority.get("canonical_semantic_acceptance") is False,
        "authority canonical boundary",
    )
    _require(
        authority.get("public") is False
        and authority.get("publication_authorized") is False
        and authority.get("production_selectable") is False,
        "authority public/production boundary",
    )
    subject = authority["subject"]
    _require(
        bool(subject["authority_decision"]["reviewer_identity"].strip())
        and subject["authority_decision"]["reviewer_authority"] == REVIEWER_AUTHORITY,
        "authority reviewer identity/class differs",
    )
    _require(
        sha256_json(subject) == authority["authority_subject_sha256"],
        "authority subject digest mismatch",
    )
    candidates = {
        item["action_id"]: item for item in candidate_artifact["subject"]["candidates"]
    }
    decisions = {item["action_id"]: item for item in subject["decisions"]}
    _require(
        len(decisions) == len(subject["decisions"]) == len(candidates),
        "authority decision count/uniqueness mismatch",
    )
    _require(
        set(decisions) == set(candidates), "authority decision action set mismatch"
    )
    for action_id, decision in decisions.items():
        candidate = candidates[action_id]
        decision_subject = {
            key: value
            for key, value in decision.items()
            if key != "decision_subject_sha256"
        }
        _require(
            sha256_json(decision_subject) == decision["decision_subject_sha256"],
            f"authority decision digest mismatch: {action_id}",
        )
        _require(
            decision["candidate_id"] == candidate["candidate_id"]
            and decision["candidate_content_subject_sha256"]
            == candidate["candidate_content_subject_sha256"]
            and decision["decision"] == ACCEPTED_DECISION
            and decision["accepted_exact_action_meaning"]
            == candidate["proposed_exact_action_meaning"]
            and decision["accepted_exact_choice_position_effect"]
            == candidate["proposed_member_position_effect"]
            and decision["accepted_confidence"] == candidate["confidence"]
            and decision["accepted_limitations"] == candidate["limitations"]
            and decision["accepted_coverage_assessment"]
            == candidate["coverage_assessment"]
            and decision["accepted_source_references"] == candidate["source_references"]
            and decision["accepted_evidence_map_id"] == candidate["evidence_map_id"]
            and decision["accepted_evidence_map_subject_sha256"]
            == candidate["evidence_map_subject_sha256"],
            f"authority decision differs from accepted candidate: {action_id}",
        )
    blocked = subject["source_blocked_actions"]
    _require(
        [item["action_id"] for item in blocked]
        == candidate_artifact["subject"]["blocked_action_ids"]
        and all(item["accepted_for_interpretation"] is False for item in blocked),
        "blocked action entered authority",
    )
    _require(
        subject["accepted_decision_count"] == len(decisions)
        and subject["source_blocked_count"] == len(blocked)
        and subject["decision_accounting"] == {ACCEPTED_DECISION: len(decisions)},
        "authority accounting mismatch",
    )
    _require(
        subject["internal_action_meanings_canonical"] is True
        and subject["canonical_semantic_acceptance"] is False
        and all(
            value is False for value in subject["downstream_authorizations"].values()
        ),
        "authority crosses downstream boundary",
    )


def build_implementation_bundle(
    *,
    authority: dict[str, Any],
    authority_file_sha256: str,
    candidate_artifact: dict[str, Any],
    artifact_id: str,
    implementation_namespace: str = "m11d",
) -> dict[str, Any]:
    _require(
        bool(re.fullmatch(r"[a-z][a-z0-9_]*", implementation_namespace)),
        "invalid implementation namespace",
    )
    validate_authority_record(authority, candidate_artifact=candidate_artifact)
    decisions = {item["action_id"]: item for item in authority["subject"]["decisions"]}
    candidates = {
        item["action_id"]: item for item in candidate_artifact["subject"]["candidates"]
    }
    records = []
    for action_id in sorted(decisions):
        decision = decisions[action_id]
        candidate = candidates[action_id]
        record_subject = {
            "action_id": action_id,
            "record_id": (
                "action-interpretation-decision-implementation:"
                f"{action_id}:{implementation_namespace}:v1"
            ),
            "candidate_id": candidate["candidate_id"],
            "candidate_content_subject_sha256": candidate[
                "candidate_content_subject_sha256"
            ],
            "authority_artifact_id": authority["artifact_id"],
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "authority_file_sha256": authority_file_sha256,
            "authority_decision_subject_sha256": decision["decision_subject_sha256"],
            "implementation_state": IMPLEMENTATION_STATE,
            "accepted_exact_action_meaning": decision["accepted_exact_action_meaning"],
            "accepted_exact_choice_position_effect": decision[
                "accepted_exact_choice_position_effect"
            ],
            "accepted_confidence": decision["accepted_confidence"],
            "accepted_limitations": deepcopy(decision["accepted_limitations"]),
            "accepted_coverage_assessment": decision["accepted_coverage_assessment"],
            "source_references": deepcopy(decision["accepted_source_references"]),
            "evidence_map_id": decision["accepted_evidence_map_id"],
            "evidence_map_subject_sha256": decision[
                "accepted_evidence_map_subject_sha256"
            ],
            "canonical_internal_action_interpretation": True,
            "canonical_semantic_acceptance": False,
            "public": False,
            "publication_authorized": False,
            "presentation_state": "internal_evidence_backed_semantic_input",
            "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
        }
        records.append(_seal(record_subject, "record_subject_sha256"))

    subject = {
        **_subject_identity(candidate_artifact),
        "input_bindings": {
            "authority_artifact_id": authority["artifact_id"],
            "authority_subject_sha256": authority["authority_subject_sha256"],
            "authority_file_sha256": authority_file_sha256,
            "candidate_artifact_id": candidate_artifact["artifact_id"],
            "candidate_interpretation_subject_sha256": candidate_artifact[
                "interpretation_subject_sha256"
            ],
        },
        "implementation_record_count": len(records),
        "implementation_records": records,
        "implementation_accounting": dict(
            sorted(Counter(item["implementation_state"] for item in records).items())
        ),
        "source_blocked_actions": deepcopy(
            authority["subject"]["source_blocked_actions"]
        ),
        "source_blocked_count": authority["subject"]["source_blocked_count"],
        "internal_action_interpretation_state": "human_accepted_internal",
        "internal_action_meanings_canonical": True,
        "canonical_semantic_acceptance": False,
        "mechanical_review_state": "pending_human_review",
        "policy_episode_state": "not_started_not_authorized",
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    return {
        "schema_version": IMPLEMENTATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "artifact_role": "detached_human_accepted_action_interpretation_implementation",
        "accepted_human_decisions_implemented": True,
        "canonical_internal_action_interpretation": True,
        "canonical_semantic_acceptance": False,
        "public": False,
        "publication_authorized": False,
        "production_selectable": False,
        "subject": subject,
        "implementation_subject_sha256": sha256_json(subject),
    }


def validate_implementation_bundle(
    implementation: dict[str, Any],
    *,
    authority: dict[str, Any],
    candidate_artifact: dict[str, Any],
) -> None:
    validate_authority_record(authority, candidate_artifact=candidate_artifact)
    _require(
        implementation.get("schema_version") == IMPLEMENTATION_SCHEMA_VERSION,
        "implementation schema version",
    )
    _require(
        implementation.get("accepted_human_decisions_implemented") is True
        and implementation.get("canonical_internal_action_interpretation") is True
        and implementation.get("canonical_semantic_acceptance") is False,
        "implementation acceptance/canonical boundary",
    )
    _require(
        implementation.get("public") is False
        and implementation.get("publication_authorized") is False
        and implementation.get("production_selectable") is False,
        "implementation public/production boundary",
    )
    subject = implementation["subject"]
    _require(
        sha256_json(subject) == implementation["implementation_subject_sha256"],
        "implementation subject digest mismatch",
    )
    decisions = {item["action_id"]: item for item in authority["subject"]["decisions"]}
    records = {item["action_id"]: item for item in subject["implementation_records"]}
    _require(
        len(records) == len(subject["implementation_records"]) == len(decisions),
        "implementation record count/uniqueness mismatch",
    )
    _require(set(records) == set(decisions), "implementation action set mismatch")
    for action_id, record in records.items():
        decision = decisions[action_id]
        record_subject = {
            key: value
            for key, value in record.items()
            if key != "record_subject_sha256"
        }
        _require(
            sha256_json(record_subject) == record["record_subject_sha256"],
            f"implementation record digest mismatch: {action_id}",
        )
        _require(
            record["authority_decision_subject_sha256"]
            == decision["decision_subject_sha256"]
            and record["implementation_state"] == IMPLEMENTATION_STATE
            and record["accepted_exact_action_meaning"]
            == decision["accepted_exact_action_meaning"]
            and record["accepted_exact_choice_position_effect"]
            == decision["accepted_exact_choice_position_effect"]
            and record["accepted_confidence"] == decision["accepted_confidence"]
            and record["accepted_limitations"] == decision["accepted_limitations"]
            and record["canonical_internal_action_interpretation"] is True
            and record["canonical_semantic_acceptance"] is False
            and record["public"] is False
            and record["publication_authorized"] is False
            and record["presentation_state"]
            == "internal_evidence_backed_semantic_input"
            and all(
                value is False for value in record["downstream_authorizations"].values()
            ),
            f"implementation differs from authority: {action_id}",
        )
    _require(
        subject["implementation_record_count"] == len(records)
        and subject["implementation_accounting"] == {IMPLEMENTATION_STATE: len(records)}
        and subject["source_blocked_actions"]
        == authority["subject"]["source_blocked_actions"]
        and subject["source_blocked_count"]
        == authority["subject"]["source_blocked_count"],
        "implementation accounting/blocked mismatch",
    )
    _require(
        subject["internal_action_meanings_canonical"] is True
        and subject["canonical_semantic_acceptance"] is False
        and subject["mechanical_review_state"] == "pending_human_review"
        and subject["policy_episode_state"] == "not_started_not_authorized"
        and all(
            value is False for value in subject["downstream_authorizations"].values()
        ),
        "implementation crosses downstream boundary",
    )
