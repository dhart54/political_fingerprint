"""Generic detached synthesis-candidate compiler and fail-closed validator."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import combinations
from typing import Any

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (
    BehavioralSemanticIRDecisionError,
    digest,
    seal,
    verify_seal,
)


SYNTHESIS_TYPES = {
    "uniform_direction",
    "mechanism_divide",
    "interpretive_boundary",
    "no_common_throughline",
}
RELATIONSHIP_ROLES = {
    "primary_support",
    "contextual_support",
    "contrast",
    "limitation",
}
ACCOUNTING_ROLES = {
    "primary_input",
    "contextual_input",
    "contrast_input",
    "limiting_input",
    "intentionally_standalone_no_safe_synthesis",
}
DOWNSTREAM_AUTHORIZATIONS = {
    "synthesis_acceptance": False,
    "public_wording": False,
    "publication": False,
    "production_persistence": False,
    "database_writes": False,
    "production_writes": False,
    "deployment": False,
}
PROHIBITED_SYNTHESIS_CLAIM_FRAGMENTS = {
    "because of motive",
    "motivated by",
    "ideology",
    "ideological",
    "pacifist",
    "pacifism",
    "isolationist",
    "isolationism",
    "anti-israel",
    "pro-israel",
    "party loyalty",
}


class SynthesisCandidateError(ValueError):
    """Raised when a synthesis candidate crosses its governed boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SynthesisCandidateError(message)


def _accepted_records(
    authority: dict[str, Any], implementation: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    try:
        verify_seal(
            authority, "authority_subject_sha256", "Behavioral Semantic IR authority"
        )
        verify_seal(
            implementation,
            "implementation_subject_sha256",
            "Behavioral Semantic IR implementation",
        )
    except BehavioralSemanticIRDecisionError as error:
        raise SynthesisCandidateError(str(error)) from error
    _require(
        authority.get("accepted") is True
        and authority.get("canonical_internal_behavioral_semantic_ir_authority")
        is True,
        "Behavioral Semantic IR authority is not accepted canonical internal authority",
    )
    _require(
        implementation.get("canonical_internal_behavioral_semantic_ir") is True
        and implementation.get("accepted_human_decisions_implemented") is True,
        "Behavioral Semantic IR implementation is not canonical internal accepted input",
    )
    binding = implementation["subject"]["authority_binding"]
    _require(
        binding["artifact_id"] == authority["artifact_id"]
        and binding["authority_subject_sha256"]
        == authority["authority_subject_sha256"],
        "Behavioral Semantic IR implementation authority binding differs",
    )
    records = {
        row["proposition_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    _require(
        len(records) == len(implementation["subject"]["implementation_records"]),
        "duplicate accepted Behavioral Semantic IR proposition",
    )
    decisions = {
        row["proposition_id"]: row
        for row in authority["subject"]["proposition_decisions"]
    }
    _require(
        len(decisions) == len(authority["subject"]["proposition_decisions"])
        and set(decisions) == set(records),
        "accepted Behavioral Semantic IR decision set differs",
    )
    ledger = {
        row["episode_id"]: row
        for row in implementation["subject"]["accepted_episode_disposition_ledger"]
    }
    _require(
        len(ledger)
        == len(implementation["subject"]["accepted_episode_disposition_ledger"]),
        "duplicate accepted episode disposition",
    )
    blocked_action_ids = {
        row["action_id"] for row in implementation["subject"]["blocked_actions"]
    }
    for proposition_id, record in records.items():
        try:
            verify_seal(
                record,
                "record_subject_sha256",
                f"Behavioral Semantic IR proposition {proposition_id}",
            )
        except BehavioralSemanticIRDecisionError as error:
            raise SynthesisCandidateError(str(error)) from error
        decision = decisions[proposition_id]
        try:
            verify_seal(
                decision,
                "decision_subject_sha256",
                f"Behavioral Semantic IR decision {proposition_id}",
            )
        except BehavioralSemanticIRDecisionError as error:
            raise SynthesisCandidateError(str(error)) from error
        _require(
            record["canonical_internal_behavioral_semantic_ir"] is True
            and record["accepted_candidate_content"]["proposition_id"] == proposition_id
            and record["accepted_candidate_content_sha256"]
            == digest(record["accepted_candidate_content"]),
            f"accepted Behavioral Semantic IR content differs: {proposition_id}",
        )
        _require(
            decision["decision"] == "accept_candidate_as_written"
            and decision["candidate_proposition_content_sha256"]
            == record["accepted_candidate_content_sha256"]
            and record["authority_decision_subject_sha256"]
            == decision["decision_subject_sha256"],
            f"accepted Behavioral Semantic IR decision binding differs: {proposition_id}",
        )
        content = record["accepted_candidate_content"]
        _require(
            all(
                episode_id in ledger
                and ledger[episode_id]["primary_proposition_id"] == proposition_id
                for episode_id in content["evidence_episode_ids"]
            ),
            f"contrast/no-safe episode entered accepted proposition evidence: {proposition_id}",
        )
        _require(
            not blocked_action_ids.intersection(content["evidence_action_ids"]),
            f"blocked action entered accepted proposition evidence: {proposition_id}",
        )
    return records


def _derive_direction(
    input_rows: list[dict[str, Any]], records: dict[str, dict[str, Any]]
) -> str:
    primary = [
        records[row["proposition_id"]]["accepted_candidate_content"]["direction"]
        for row in input_rows
        if row["relationship_role"] == "primary_support"
    ]
    directions = set(primary)
    if len(directions) == 1 and "mixed" not in directions:
        return next(iter(directions))
    return "mixed"


def _input_binding(row: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    content = record["accepted_candidate_content"]
    return {
        "proposition_id": row["proposition_id"],
        "relationship_role": row["relationship_role"],
        "concise_input_summary": row["concise_input_summary"],
        "implementation_record_id": record["record_id"],
        "implementation_record_subject_sha256": record["record_subject_sha256"],
        "accepted_candidate_content_sha256": record[
            "accepted_candidate_content_sha256"
        ],
        "source_proposition_type": content["proposition_type"],
        "source_direction": content["direction"],
        "source_conclusion_relevance": content["conclusion_relevance"],
        "evidence_episode_ids": deepcopy(content["evidence_episode_ids"]),
        "evidence_action_ids": deepcopy(content["evidence_action_ids"]),
    }


def _compile_candidate(
    definition: dict[str, Any],
    records: dict[str, dict[str, Any]],
    *,
    legacy_binding_names: bool,
) -> dict[str, Any]:
    candidate_id = definition["synthesis_candidate_id"]
    _require(
        definition["synthesis_type"] in SYNTHESIS_TYPES,
        f"unsupported synthesis type: {definition['synthesis_type']}",
    )
    _require(
        definition.get("semantic_role") == "synthesis",
        f"{candidate_id}: semantic role differs",
    )
    _require(
        not any(
            fragment in definition["proposition"].lower()
            for fragment in PROHIBITED_SYNTHESIS_CLAIM_FRAGMENTS
        ),
        f"{candidate_id}: prohibited motive or ideology claim",
    )
    forbidden_evidence_keys = {
        "evidence_episode_ids",
        "evidence_action_ids",
        "action_ids",
        "raw_vote_ids",
    }
    _require(
        not forbidden_evidence_keys.intersection(definition),
        f"{candidate_id}: raw action or episode evidence supplied directly",
    )
    basis = definition["relationship_basis"]
    _require(
        basis["topic_similarity_only"] is False
        and isinstance(basis["semantic_relationship"], str)
        and basis["semantic_relationship"].strip()
        and isinstance(definition["why_synthesis_not_topic_grouping"], str)
        and definition["why_synthesis_not_topic_grouping"].strip(),
        f"{candidate_id}: unsupported topic-only grouping",
    )
    inputs = definition["inputs"]
    input_ids = [row["proposition_id"] for row in inputs]
    _require(
        len(inputs) >= 2 and len(input_ids) == len(set(input_ids)),
        f"{candidate_id}: synthesis inputs must be distinct and plural",
    )
    _require(
        set(input_ids) <= set(records),
        f"{candidate_id}: unknown or unaccepted Behavioral Semantic IR input",
    )
    _require(
        all(row["relationship_role"] in RELATIONSHIP_ROLES for row in inputs),
        f"{candidate_id}: unsupported relationship role",
    )
    for row in inputs:
        content = records[row["proposition_id"]]["accepted_candidate_content"]
        relevance = content["conclusion_relevance"]
        role = row["relationship_role"]
        _require(
            not (relevance == "excluded" and role == "primary_support"),
            f"{candidate_id}: excluded notable silently promoted",
        )
        _require(
            not (relevance == "limiting" and role != "limitation"),
            f"{candidate_id}: limiting input silently upgraded",
        )
    derived_direction = _derive_direction(inputs, records)
    _require(
        definition["direction"] == derived_direction,
        f"{candidate_id}: direction differs from accepted proposition inputs",
    )
    if definition["synthesis_type"] == "uniform_direction":
        primary_directions = {
            records[row["proposition_id"]]["accepted_candidate_content"]["direction"]
            for row in inputs
            if row["relationship_role"] == "primary_support"
        }
        _require(
            len(primary_directions) == 1 and "mixed" not in primary_directions,
            f"{candidate_id}: uniform direction is not established",
        )

    bindings = [_input_binding(row, records[row["proposition_id"]]) for row in inputs]
    episode_ids_by_role = {
        role: sorted(
            {
                episode_id
                for row in bindings
                if row["relationship_role"] == role
                for episode_id in row["evidence_episode_ids"]
            }
        )
        for role in sorted(RELATIONSHIP_ROLES)
    }
    all_episode_ids = sorted(
        {episode_id for row in bindings for episode_id in row["evidence_episode_ids"]}
    )
    all_action_ids = sorted(
        {action_id for row in bindings for action_id in row["evidence_action_ids"]}
    )
    relationships = {
        "supported_by": [
            row["proposition_id"]
            for row in inputs
            if row["relationship_role"] == "primary_support"
        ],
        "contextualized_by": [
            row["proposition_id"]
            for row in inputs
            if row["relationship_role"] == "contextual_support"
        ],
        "contrasted_by": [
            row["proposition_id"]
            for row in inputs
            if row["relationship_role"] == "contrast"
        ],
        "limited_by": [
            row["proposition_id"]
            for row in inputs
            if row["relationship_role"] == "limitation"
        ],
    }
    candidate = {
        "synthesis_candidate_id": candidate_id,
        "semantic_role": "synthesis",
        "synthesis_type": definition["synthesis_type"],
        "direction": definition["direction"],
        "conclusion_relevance": definition["conclusion_relevance"],
        "proposition": definition["proposition"],
        "input_bindings": bindings,
        "relationships": relationships,
        "relationship_basis": deepcopy(basis),
        "relationship_rationale": definition["relationship_rationale"],
        "why_synthesis_not_topic_grouping": definition[
            "why_synthesis_not_topic_grouping"
        ],
        "material_limitations": deepcopy(definition["material_limitations"]),
        "competing_interpretation": definition["competing_interpretation"],
        "unresolved_ambiguity": definition["unresolved_ambiguity"],
        "prohibited_inferences": deepcopy(definition["prohibited_inferences"]),
        "underlying_evidence": {
            "episode_ids_by_relationship_role": episode_ids_by_role,
            "unique_episode_ids": all_episode_ids,
            "unique_episode_count": len(all_episode_ids),
            "unique_action_ids": all_action_ids,
            "unique_action_count": len(all_action_ids),
            "behavioral_proposition_input_count": len(bindings),
            "independent_evidence_unit": (
                "accepted_m11h_underlying_episode"
                if legacy_binding_names
                else "accepted_behavioral_semantic_ir_underlying_episode"
            ),
            "pattern_nodes_and_episodes_are_not_additive": True,
        },
        "candidate_state": "proposed_pending_human_synthesis_review",
        "accepted": False,
        "canonical": False,
        "authorizing": False,
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    return seal(candidate, "synthesis_candidate_subject_sha256")


def _compile_accounting(
    rows: list[dict[str, Any]],
    *,
    records: dict[str, dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {row["proposition_id"]: row for row in rows}
    _require(
        len(by_id) == len(rows) and set(by_id) == set(records),
        "complete accepted Behavioral Semantic IR proposition accounting differs",
    )
    candidate_roles = {
        proposition_id: [
            {
                "synthesis_candidate_id": candidate["synthesis_candidate_id"],
                "relationship_role": binding["relationship_role"],
            }
            for candidate in candidates
            for binding in candidate["input_bindings"]
            if binding["proposition_id"] == proposition_id
        ]
        for proposition_id in records
    }
    result = []
    for proposition_id in sorted(records):
        source = records[proposition_id]
        content = source["accepted_candidate_content"]
        row = by_id[proposition_id]
        relationships = candidate_roles[proposition_id]
        _require(
            row["accounting_role"] in ACCOUNTING_ROLES,
            f"unsupported synthesis accounting role: {proposition_id}",
        )
        if row["accounting_role"] == "intentionally_standalone_no_safe_synthesis":
            _require(
                not relationships,
                f"standalone proposition enters synthesis: {proposition_id}",
            )
        else:
            expected_role = {
                "primary_input": "primary_support",
                "contextual_input": "contextual_support",
                "contrast_input": "contrast",
                "limiting_input": "limitation",
            }[row["accounting_role"]]
            _require(
                relationships
                and all(
                    item["relationship_role"] == expected_role for item in relationships
                ),
                f"synthesis accounting relationship differs: {proposition_id}",
            )
        result.append(
            {
                "proposition_id": proposition_id,
                "implementation_record_id": source["record_id"],
                "implementation_record_subject_sha256": source["record_subject_sha256"],
                "accepted_candidate_content_sha256": source[
                    "accepted_candidate_content_sha256"
                ],
                "source_proposition_type": content["proposition_type"],
                "source_conclusion_relevance": content["conclusion_relevance"],
                "accounting_role": row["accounting_role"],
                "candidate_relationships": relationships,
                "reason": row["reason"],
            }
        )
    return result


def _overlap_accounting(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for left, right in combinations(candidates, 2):
        left_props = {row["proposition_id"] for row in left["input_bindings"]}
        right_props = {row["proposition_id"] for row in right["input_bindings"]}
        left_episodes = set(left["underlying_evidence"]["unique_episode_ids"])
        right_episodes = set(right["underlying_evidence"]["unique_episode_ids"])
        shared_props = sorted(left_props & right_props)
        shared_episodes = sorted(left_episodes & right_episodes)
        rows.append(
            {
                "left_candidate_id": left["synthesis_candidate_id"],
                "right_candidate_id": right["synthesis_candidate_id"],
                "shared_proposition_ids": shared_props,
                "shared_episode_ids": shared_episodes,
                "overlap_state": "explicit_overlap"
                if shared_props or shared_episodes
                else "no_overlap",
                "overlap_does_not_create_independent_evidence": True,
            }
        )
    return rows


def compile_synthesis_candidate_package(
    *,
    authority: dict[str, Any],
    implementation: dict[str, Any],
    candidate_definitions: list[dict[str, Any]],
    proposition_accounting: list[dict[str, Any]],
    subject: dict[str, Any],
    legacy_binding_names: bool = True,
) -> dict[str, Any]:
    """Compile only candidate synthesis from accepted Behavioral Semantic IR."""

    records = _accepted_records(authority, implementation)
    candidate_ids = [row["synthesis_candidate_id"] for row in candidate_definitions]
    _require(
        len(candidate_ids) == len(set(candidate_ids)),
        "duplicate synthesis candidate identity",
    )
    candidates = [
        _compile_candidate(
            definition,
            records,
            legacy_binding_names=legacy_binding_names,
        )
        for definition in candidate_definitions
    ]
    accounting = _compile_accounting(
        proposition_accounting,
        records=records,
        candidates=candidates,
    )
    role_counts = dict(
        sorted(Counter(row["accounting_role"] for row in accounting).items())
    )
    semantic_bindings = (
        {
            "m11h_authority_binding": {
                "artifact_id": authority["artifact_id"],
                "authority_subject_sha256": authority["authority_subject_sha256"],
            },
            "m11h_implementation_binding": {
                "artifact_id": implementation["artifact_id"],
                "implementation_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
        }
        if legacy_binding_names
        else {
            "accepted_behavioral_semantic_ir_authority_binding": {
                "artifact_id": authority["artifact_id"],
                "authority_subject_sha256": authority["authority_subject_sha256"],
            },
            "accepted_behavioral_semantic_ir_implementation_binding": {
                "artifact_id": implementation["artifact_id"],
                "implementation_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
        }
    )
    package = {
        "schema_version": "full_record_synthesis_candidates_v1",
        "artifact_id": subject["artifact_id"],
        "artifact_role": "detached_non_authorizing_synthesis_candidate_package",
        "subject": {
            **deepcopy(subject),
            **semantic_bindings,
            "candidate_definitions": deepcopy(candidate_definitions),
            "synthesis_candidates": candidates,
            "complete_proposition_accounting": accounting,
            "proposition_accounting_counts": role_counts,
            "candidate_overlap_accounting": _overlap_accounting(candidates),
            "source_behavioral_proposition_count": len(records),
            "synthesis_candidate_count": len(candidates),
            "accepted_episode_disposition_ledger": deepcopy(
                implementation["subject"]["accepted_episode_disposition_ledger"]
            ),
            "episode_disposition_accounting": deepcopy(
                implementation["subject"]["accepted_episode_disposition_accounting"]
            ),
            "blocked_actions": deepcopy(implementation["subject"]["blocked_actions"]),
            "candidate_state": "complete_pending_human_substantive_synthesis_review",
            "accepted": False,
            "canonical": False,
            "authorizing": False,
            "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
        },
        "public": False,
        "production_selectable": False,
    }
    return seal(package, "synthesis_candidate_package_subject_sha256")


def validate_synthesis_candidate_package(
    package: dict[str, Any],
    *,
    authority: dict[str, Any],
    implementation: dict[str, Any],
) -> dict[str, Any]:
    """Independently rebuild and compare a synthesis candidate package."""

    verify_seal(
        package,
        "synthesis_candidate_package_subject_sha256",
        "synthesis candidate package",
    )
    subject = package["subject"]
    _require(
        not any(subject["downstream_authorizations"].values())
        and subject["accepted"] is False
        and subject["canonical"] is False
        and subject["authorizing"] is False
        and package["public"] is False
        and package["production_selectable"] is False,
        "synthesis candidate crossed downstream authority boundary",
    )
    legacy_binding_names = "m11h_authority_binding" in subject
    generic_binding_names = (
        "accepted_behavioral_semantic_ir_authority_binding" in subject
    )
    _require(
        legacy_binding_names != generic_binding_names
        and (
            "m11h_implementation_binding" in subject
            if legacy_binding_names
            else "accepted_behavioral_semantic_ir_implementation_binding" in subject
        ),
        "provide exactly one Behavioral Semantic IR binding vocabulary",
    )
    rebuilt_subject = {
        key: deepcopy(value)
        for key, value in subject.items()
        if key
        not in {
            "m11h_authority_binding",
            "m11h_implementation_binding",
            "accepted_behavioral_semantic_ir_authority_binding",
            "accepted_behavioral_semantic_ir_implementation_binding",
            "candidate_definitions",
            "synthesis_candidates",
            "complete_proposition_accounting",
            "proposition_accounting_counts",
            "candidate_overlap_accounting",
            "source_behavioral_proposition_count",
            "synthesis_candidate_count",
            "accepted_episode_disposition_ledger",
            "episode_disposition_accounting",
            "blocked_actions",
            "candidate_state",
            "accepted",
            "canonical",
            "authorizing",
            "downstream_authorizations",
        }
    }
    expected = compile_synthesis_candidate_package(
        authority=authority,
        implementation=implementation,
        candidate_definitions=subject["candidate_definitions"],
        proposition_accounting=[
            {
                "proposition_id": row["proposition_id"],
                "accounting_role": row["accounting_role"],
                "reason": row["reason"],
            }
            for row in subject["complete_proposition_accounting"]
        ],
        subject=rebuilt_subject,
        legacy_binding_names=legacy_binding_names,
    )
    _require(package == expected, "synthesis candidate deterministic rebuild differs")
    return {
        "artifact_id": package["artifact_id"],
        "candidate_count": subject["synthesis_candidate_count"],
        "source_proposition_count": subject["source_behavioral_proposition_count"],
        "accounting_counts": subject["proposition_accounting_counts"],
        "status": "valid",
    }
