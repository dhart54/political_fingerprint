"""Generic fail-closed human synthesis authority and implementation contract."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from typing import Any


DOWNSTREAM_AUTHORIZATIONS = {
    "public_wording": False,
    "publication": False,
    "production_persistence": False,
    "database_writes": False,
    "production_writes": False,
    "deployment": False,
}
ALLOWED_DECISIONS = {"accept_candidate_as_written", "accept_with_bounded_revision"}


class SynthesisDecisionError(ValueError):
    """Raised when synthesis authority or implementation exceeds human review."""


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
        raise SynthesisDecisionError(f"{label}: {field} differs")


def _candidates(package: dict[str, Any]) -> list[dict[str, Any]]:
    return package["subject"]["synthesis_candidates"]


def structural_projection(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the synthesis fields that a wording revision cannot change."""

    input_fields = (
        "proposition_id",
        "relationship_role",
        "implementation_record_id",
        "implementation_record_subject_sha256",
        "accepted_candidate_content_sha256",
        "source_proposition_type",
        "source_direction",
        "source_conclusion_relevance",
        "evidence_episode_ids",
        "evidence_action_ids",
    )
    return {
        "synthesis_candidate_id": candidate["synthesis_candidate_id"],
        "synthesis_candidate_subject_sha256": candidate.get(
            "synthesis_candidate_subject_sha256"
        ),
        "semantic_role": candidate["semantic_role"],
        "synthesis_type": candidate["synthesis_type"],
        "direction": candidate["direction"],
        "conclusion_relevance": candidate["conclusion_relevance"],
        "input_bindings": [
            {field: deepcopy(row[field]) for field in input_fields}
            for row in candidate["input_bindings"]
        ],
        "relationships": deepcopy(candidate["relationships"]),
        "relationship_basis": {
            "basis_type": candidate["relationship_basis"]["basis_type"],
            "topic_similarity_only": candidate["relationship_basis"][
                "topic_similarity_only"
            ],
        },
        "underlying_evidence": deepcopy(candidate["underlying_evidence"]),
        "candidate_state": candidate["candidate_state"],
        "accepted": candidate["accepted"],
        "canonical": candidate["canonical"],
        "authorizing": candidate["authorizing"],
        "downstream_authorizations": deepcopy(candidate["downstream_authorizations"]),
    }


def require_structural_invariance(
    original: dict[str, Any], revised: dict[str, Any]
) -> None:
    if structural_projection(original) != structural_projection(revised):
        raise SynthesisDecisionError(
            "bounded revision changed structural or evidence identity"
        )


def _replace_path(value: object, path: list[object], replacement: object) -> None:
    if not path:
        raise SynthesisDecisionError("bounded revision path is empty")
    cursor = value
    for key in path[:-1]:
        if isinstance(cursor, list) and isinstance(key, int):
            if key < 0 or key >= len(cursor):
                raise SynthesisDecisionError("bounded revision list path differs")
            cursor = cursor[key]
        elif isinstance(cursor, dict) and isinstance(key, str) and key in cursor:
            cursor = cursor[key]
        else:
            raise SynthesisDecisionError("bounded revision path differs")
    key = path[-1]
    if isinstance(cursor, list) and isinstance(key, int) and 0 <= key < len(cursor):
        cursor[key] = deepcopy(replacement)
    elif isinstance(cursor, dict) and isinstance(key, str) and key in cursor:
        cursor[key] = deepcopy(replacement)
    else:
        raise SynthesisDecisionError("bounded revision target differs")


def apply_bounded_revision(
    original: dict[str, Any], revision: dict[str, Any] | None
) -> dict[str, Any]:
    if revision is None:
        return deepcopy(original)
    result = deepcopy(original)
    replacements = revision["field_replacements"]
    paths = [json.dumps(row["path"], separators=(",", ":")) for row in replacements]
    if len(paths) != len(set(paths)):
        raise SynthesisDecisionError("duplicate bounded revision path")
    for row in replacements:
        cursor: object = original
        for key in row["path"]:
            if (
                isinstance(cursor, list)
                and isinstance(key, int)
                and 0 <= key < len(cursor)
            ):
                cursor = cursor[key]
            elif isinstance(cursor, dict) and isinstance(key, str) and key in cursor:
                cursor = cursor[key]
            else:
                raise SynthesisDecisionError("bounded revision original path differs")
        if digest(cursor) != row["original_value_sha256"]:
            raise SynthesisDecisionError("bounded revision original value differs")
        _replace_path(result, row["path"], row["revised_value"])
    if digest(result) != revision["revised_candidate_content_sha256"]:
        raise SynthesisDecisionError("bounded revision result differs")
    return result


def _validate_direction_guard(record: dict[str, Any]) -> None:
    guard = record["source_direction_semantic_guard"]
    if not (
        guard["direction_metadata_role"] == "proposition_relative_structural_metadata"
        and guard["semantic_claim_basis"] == "accepted_behavioral_proposition_content"
        and guard["mixed_direction_alone_establishes_mixed_policy_orientation"] is False
        and guard["accepted_input_content_sha256s"]
        == [
            row["accepted_candidate_content_sha256"]
            for row in record["original_candidate_content"]["input_bindings"]
        ]
    ):
        raise SynthesisDecisionError("source-direction semantic guard differs")


def validate_authority(
    authority: dict[str, Any],
    *,
    package: dict[str, Any],
    decision_template: dict[str, Any],
) -> dict[str, int]:
    verify_seal(authority, "authority_subject_sha256", "synthesis authority")
    if not (
        authority.get("accepted") is True
        and authority.get("immutable") is True
        and authority.get("canonical_internal_synthesis_authority") is True
        and authority.get("public") is False
        and authority.get("production_selectable") is False
    ):
        raise SynthesisDecisionError("authority state differs")
    subject = authority["subject"]
    if any(subject["downstream_authorizations"].values()):
        raise SynthesisDecisionError("downstream authority leakage")
    if not (
        subject["candidate_binding"]["artifact_id"] == package["artifact_id"]
        and subject["candidate_binding"]["candidate_subject_sha256"]
        == package["synthesis_candidate_package_subject_sha256"]
        and subject["decision_template_binding"]["artifact_id"]
        == decision_template["artifact_id"]
        and subject["decision_template_binding"]["decision_template_subject_sha256"]
        == decision_template["decision_template_subject_sha256"]
    ):
        raise SynthesisDecisionError("M11I binding differs")
    candidates = _candidates(package)
    by_id = {row["synthesis_candidate_id"]: row for row in candidates}
    if len(by_id) != len(candidates):
        raise SynthesisDecisionError("duplicate M11I candidate")
    decisions = subject["synthesis_decisions"]
    if len(decisions) != len(by_id) or {
        row["synthesis_candidate_id"] for row in decisions
    } != set(by_id):
        raise SynthesisDecisionError("synthesis decision set differs")
    for decision in decisions:
        verify_seal(
            decision,
            "decision_subject_sha256",
            f"synthesis decision {decision['synthesis_candidate_id']}",
        )
        original = by_id[decision["synthesis_candidate_id"]]
        if not (
            decision["decision"] in ALLOWED_DECISIONS
            and decision["original_candidate_subject_sha256"]
            == original["synthesis_candidate_subject_sha256"]
            and decision["original_candidate_content_sha256"] == digest(original)
        ):
            raise SynthesisDecisionError("original candidate decision binding differs")
        revision = decision["bounded_revision"]
        if (
            decision["decision"] == "accept_candidate_as_written"
            and revision is not None
        ):
            raise SynthesisDecisionError("accepted-as-written decision has revision")
        if decision["decision"] == "accept_with_bounded_revision" and revision is None:
            raise SynthesisDecisionError("bounded revision is absent")
        revised = apply_bounded_revision(original, revision)
        require_structural_invariance(original, revised)
    counts = Counter(row["decision"] for row in decisions)
    expected_counts = {
        "accept_candidate_as_written": counts["accept_candidate_as_written"],
        "accept_with_bounded_revision": counts["accept_with_bounded_revision"],
        "rejected": 0,
        "unresolved": 0,
    }
    if subject["decision_accounting"] != expected_counts:
        raise SynthesisDecisionError("decision accounting differs")
    if (
        subject["accepted_proposition_role_accounting"]
        != package["subject"]["complete_proposition_accounting"]
    ):
        raise SynthesisDecisionError("complete proposition-role accounting differs")
    return expected_counts


def validate_implementation(
    implementation: dict[str, Any],
    *,
    authority: dict[str, Any],
    package: dict[str, Any],
    decision_template: dict[str, Any],
    m11h_authority: dict[str, Any],
    m11h_implementation: dict[str, Any],
) -> dict[str, Any]:
    decision_counts = validate_authority(
        authority, package=package, decision_template=decision_template
    )
    verify_seal(
        implementation, "implementation_subject_sha256", "synthesis implementation"
    )
    subject = implementation["subject"]
    if any(subject["downstream_authorizations"].values()):
        raise SynthesisDecisionError("downstream implementation leakage")
    if not (
        subject["authority_binding"]["artifact_id"] == authority["artifact_id"]
        and subject["authority_binding"]["authority_subject_sha256"]
        == authority["authority_subject_sha256"]
    ):
        raise SynthesisDecisionError("implementation authority binding differs")
    verify_seal(m11h_authority, "authority_subject_sha256", "M11H authority")
    verify_seal(
        m11h_implementation, "implementation_subject_sha256", "M11H implementation"
    )
    if not (
        subject["m11h_authority_binding"]["artifact_id"]
        == m11h_authority["artifact_id"]
        and subject["m11h_authority_binding"]["authority_subject_sha256"]
        == m11h_authority["authority_subject_sha256"]
        and subject["m11h_implementation_binding"]["artifact_id"]
        == m11h_implementation["artifact_id"]
        and subject["m11h_implementation_binding"]["implementation_subject_sha256"]
        == m11h_implementation["implementation_subject_sha256"]
    ):
        raise SynthesisDecisionError("accepted M11H binding differs")
    source_records = {
        row["proposition_id"]: row
        for row in m11h_implementation["subject"]["implementation_records"]
    }
    if len(source_records) != len(
        m11h_implementation["subject"]["implementation_records"]
    ):
        raise SynthesisDecisionError("duplicate M11H proposition")
    candidates = {row["synthesis_candidate_id"]: row for row in _candidates(package)}
    decisions = {
        row["synthesis_candidate_id"]: row
        for row in authority["subject"]["synthesis_decisions"]
    }
    records = subject["implementation_records"]
    if len(records) != len(candidates) or {
        row["synthesis_candidate_id"] for row in records
    } != set(candidates):
        raise SynthesisDecisionError("implementation candidate set differs")
    observed_episodes: list[str] = []
    observed_actions: list[str] = []
    observed_inputs: set[str] = set()
    for record in records:
        verify_seal(
            record,
            "record_subject_sha256",
            f"synthesis implementation {record['synthesis_candidate_id']}",
        )
        original = candidates[record["synthesis_candidate_id"]]
        decision = decisions[record["synthesis_candidate_id"]]
        expected = apply_bounded_revision(original, decision["bounded_revision"])
        require_structural_invariance(original, expected)
        require_structural_invariance(
            record["original_candidate_content"],
            record["implemented_synthesis_content"],
        )
        if not (
            record["original_candidate_content"] == original
            and record["original_candidate_content_sha256"] == digest(original)
            and record["original_candidate_subject_sha256"]
            == original["synthesis_candidate_subject_sha256"]
            and record["implemented_synthesis_content"] == expected
            and record["implemented_synthesis_content_sha256"] == digest(expected)
            and record["authority_decision_subject_sha256"]
            == decision["decision_subject_sha256"]
            and record["decision"] == decision["decision"]
            and record["bounded_revision"] == decision["bounded_revision"]
            and record["canonical_internal_synthesis"] is True
            and not any(record["downstream_authorizations"].values())
        ):
            raise SynthesisDecisionError("implemented synthesis differs from decision")
        _validate_direction_guard(record)
        expected_lineage = []
        for binding in original["input_bindings"]:
            source = source_records.get(binding["proposition_id"])
            if source is None or not (
                source["record_id"] == binding["implementation_record_id"]
                and source["record_subject_sha256"]
                == binding["implementation_record_subject_sha256"]
                and source["accepted_candidate_content_sha256"]
                == binding["accepted_candidate_content_sha256"]
            ):
                raise SynthesisDecisionError("M11H input proposition binding differs")
            source_content = source["accepted_candidate_content"]
            if not (
                source_content["direction"] == binding["source_direction"]
                and source_content["conclusion_relevance"]
                == binding["source_conclusion_relevance"]
                and source_content["proposition_type"]
                == binding["source_proposition_type"]
                and source_content["evidence_episode_ids"]
                == binding["evidence_episode_ids"]
                and source_content["evidence_action_ids"]
                == binding["evidence_action_ids"]
            ):
                raise SynthesisDecisionError("M11H semantic input differs")
            expected_lineage.append(
                {
                    "proposition_id": binding["proposition_id"],
                    "relationship_role": binding["relationship_role"],
                    "m11h_record_id": source["record_id"],
                    "m11h_record_subject_sha256": source["record_subject_sha256"],
                    "accepted_candidate_content_sha256": source[
                        "accepted_candidate_content_sha256"
                    ],
                    "evidence_episode_ids": binding["evidence_episode_ids"],
                    "evidence_action_ids": binding["evidence_action_ids"],
                }
            )
            observed_inputs.add(binding["proposition_id"])
        if record["behavioral_proposition_lineage"] != expected_lineage:
            raise SynthesisDecisionError("behavioral proposition lineage differs")
        evidence = original["underlying_evidence"]
        if not (
            record["underlying_evidence"] == evidence
            and len(evidence["unique_episode_ids"]) == evidence["unique_episode_count"]
            and len(evidence["unique_action_ids"]) == evidence["unique_action_count"]
            and len(evidence["unique_episode_ids"])
            == len(set(evidence["unique_episode_ids"]))
            and len(evidence["unique_action_ids"])
            == len(set(evidence["unique_action_ids"]))
        ):
            raise SynthesisDecisionError("underlying evidence inflation")
        observed_episodes.extend(evidence["unique_episode_ids"])
        observed_actions.extend(evidence["unique_action_ids"])
    accounting = package["subject"]["complete_proposition_accounting"]
    standalone = {
        row["proposition_id"]
        for row in accounting
        if row["accounting_role"] == "intentionally_standalone_no_safe_synthesis"
    }
    if observed_inputs & standalone:
        raise SynthesisDecisionError("standalone proposition entered synthesis")
    if subject["accepted_proposition_role_accounting"] != accounting:
        raise SynthesisDecisionError("implementation proposition accounting differs")
    expected_overlap = package["subject"]["candidate_overlap_accounting"]
    if subject["candidate_overlap_accounting"] != expected_overlap:
        raise SynthesisDecisionError("candidate overlap accounting differs")
    expected_final = {
        "canonical_internal_synthesis_count": len(records),
        "unique_behavioral_proposition_input_count": len(observed_inputs),
        "candidate_episode_reference_count": len(observed_episodes),
        "candidate_action_reference_count": len(observed_actions),
        "cross_candidate_episode_overlap_count": len(observed_episodes)
        - len(set(observed_episodes)),
        "cross_candidate_action_overlap_count": len(observed_actions)
        - len(set(observed_actions)),
        "standalone_proposition_count": len(standalone),
    }
    if subject["final_accounting"] != expected_final:
        raise SynthesisDecisionError("final synthesis accounting differs")
    return {"decision_accounting": decision_counts, "final_accounting": expected_final}
