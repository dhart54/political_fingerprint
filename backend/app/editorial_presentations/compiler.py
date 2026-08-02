"""Deterministic compiler from compiled Semantic IR to a gated public artifact."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from typing import Any

PUBLIC_TIERS = {
    "reviewed_conclusion",
    "developing_read",
    "non_directional_or_limited_evidence",
    "receipts_only",
}
REQUIRED_DETACHED_DECISIONS = {
    "editorial_wording": "approved",
    "gold_benchmark_promotion": "approved",
    "production_eligibility": "approved",
}
IMMUTABLE_PROVENANCE_FIELDS = (
    "semantic_source_case_id",
    "focused_validation_case_ids",
    "dossier_refs",
    "source_refs",
    "claim_refs",
    "receipt_refs",
    "action_source_contract_id",
    "action_source_contract_sha256",
    "review_limitations",
)
AUTHORING_PROVENANCE_FIELDS = (
    "semantic_source_case_id",
    "focused_validation_case_ids",
    "dossier_refs",
    "source_refs",
    "claim_refs",
    "receipt_refs",
    "review_limitations",
)
RECOGNIZED_REVIEWER_AUTHORITIES = {
    "editorial_publication_review_authority_v1",
}
APPROVAL_RECEIPT_ID = re.compile(r"^approval-receipt:[a-z0-9][a-z0-9._-]{2,127}$")
REVIEWER_ID = re.compile(r"^reviewer:[a-z0-9][a-z0-9._-]{2,127}$")
ANALYTICAL_TIERS = PUBLIC_TIERS - {"receipts_only"}
BENCHMARK_STATUSES = {"not_promoted", "gold_benchmark"}


class EditorialPresentationError(ValueError):
    """Raised when wording or controls do not preserve compiled meaning."""


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def artifact_bytes(artifact: dict[str, Any]) -> bytes:
    """Return canonical UTF-8 bytes for an immutable artifact."""

    return json.dumps(
        artifact,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def artifact_digest(artifact: dict[str, Any]) -> str:
    return hashlib.sha256(artifact_bytes(artifact)).hexdigest()


def reviewed_wording_digest(wording: dict[str, Any]) -> str:
    return canonical_digest(wording)


def _mapped_records(wording: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def collect(record: Any) -> None:
        if isinstance(record, dict):
            mapping = record.get("mapping")
            statement_id = record.get("statement_id")
            if isinstance(mapping, dict) and isinstance(statement_id, str):
                result.append(
                    {
                        "statement_id": statement_id,
                        "mapping": copy.deepcopy(mapping),
                    }
                )
            for value in record.values():
                collect(value)
        elif isinstance(record, list):
            for value in record:
                collect(value)

    collect(wording)
    return sorted(
        result,
        key=lambda item: item["mapping"]["mapping_id"],
    )


def mapping_set_digest(wording: dict[str, Any]) -> str:
    return canonical_digest(_mapped_records(wording))


def _immutable_provenance(provenance: dict[str, Any]) -> dict[str, Any]:
    try:
        return {
            field: copy.deepcopy(provenance[field])
            for field in IMMUTABLE_PROVENANCE_FIELDS
        }
    except KeyError as exc:
        raise EditorialPresentationError(
            "immutable evidence provenance is incomplete"
        ) from exc


def evidence_provenance_digest(provenance: dict[str, Any]) -> str:
    return canonical_digest(_immutable_provenance(provenance))


def canonical_limitations(
    limitations: Any,
) -> list[dict[str, str]]:
    if not isinstance(limitations, list) or not limitations:
        raise EditorialPresentationError(
            "review limitations must be a non-empty canonical set"
        )
    normalized: list[dict[str, str]] = []
    for item in limitations:
        if (
            not isinstance(item, dict)
            or set(item) != {"limitation_id", "text"}
            or not isinstance(item["limitation_id"], str)
            or not item["limitation_id"].strip()
            or not isinstance(item["text"], str)
            or not item["text"].strip()
        ):
            raise EditorialPresentationError(
                "review limitations require exact IDs and text"
            )
        normalized.append(copy.deepcopy(item))
    normalized.sort(key=lambda item: item["limitation_id"])
    if len({item["limitation_id"] for item in normalized}) != len(normalized):
        raise EditorialPresentationError("review limitation IDs are not unique")
    return normalized


def limitations_digest(limitations: Any) -> str:
    return canonical_digest(canonical_limitations(limitations))


def validate_trusted_action_source_contract(
    contract: dict[str, Any],
) -> str:
    if not isinstance(contract, dict) or set(contract) != {
        "schema_version",
        "contract_id",
        "source_manifest",
        "claim_source_map",
        "source_authorities",
        "actions",
    }:
        raise EditorialPresentationError("trusted action/source contract is malformed")
    if (
        contract["schema_version"] != "editorial_action_source_contract_v1"
        or not isinstance(contract["contract_id"], str)
        or not contract["contract_id"]
    ):
        raise EditorialPresentationError(
            "trusted action/source contract identity is invalid"
        )
    for reference in ("source_manifest", "claim_source_map"):
        value = contract[reference]
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "sha256"}
            or not isinstance(value["path"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])
        ):
            raise EditorialPresentationError(
                "trusted action/source authority reference is invalid"
            )
    authorities = contract["source_authorities"]
    actions = contract["actions"]
    if not isinstance(authorities, dict) or not isinstance(actions, dict):
        raise EditorialPresentationError(
            "trusted action/source contract registry is invalid"
        )
    for source_id, source_type in authorities.items():
        if not source_id or not isinstance(source_type, str) or not source_type:
            raise EditorialPresentationError("trusted source authority is invalid")
    for action_id, requirement in actions.items():
        if (
            not isinstance(action_id, str)
            or not re.fullmatch(
                r"^house:[1-9][0-9]*:[1-9][0-9]*:[1-9][0-9]*$",
                action_id,
            )
            or not isinstance(requirement, dict)
            or set(requirement)
            != {
                "vote_source_refs",
                "action_meaning_source_refs",
                "required_action_meaning_source_types",
            }
        ):
            raise EditorialPresentationError(
                "trusted exact-action requirement is invalid"
            )
        vote_sources = requirement["vote_source_refs"]
        meaning_sources = requirement["action_meaning_source_refs"]
        required_types = requirement["required_action_meaning_source_types"]
        if (
            not vote_sources
            or not meaning_sources
            or not required_types
            or len(vote_sources) != len(set(vote_sources))
            or len(meaning_sources) != len(set(meaning_sources))
            or any(
                source not in authorities
                for source in [*vote_sources, *meaning_sources]
            )
            or any(
                authorities[source] != "house_clerk_roll_call"
                for source in vote_sources
            )
            or not set(required_types)
            <= {authorities[source] for source in meaning_sources}
        ):
            raise EditorialPresentationError(
                "trusted exact-action sources or authority types are invalid"
            )
    return canonical_digest(contract)


def _prepare_provenance(
    provenance: dict[str, Any],
    trusted_action_source_contract: dict[str, Any],
) -> dict[str, Any]:
    if set(provenance) != set(AUTHORING_PROVENANCE_FIELDS):
        raise EditorialPresentationError(
            "authoring provenance must contain exactly the permitted fields"
        )
    result = copy.deepcopy(provenance)
    result["review_limitations"] = canonical_limitations(result["review_limitations"])
    contract_sha256 = validate_trusted_action_source_contract(
        trusted_action_source_contract
    )
    result["action_source_contract_id"] = trusted_action_source_contract["contract_id"]
    result["action_source_contract_sha256"] = contract_sha256
    return result


def _member(compiled_ir: dict[str, Any], member_id: str) -> dict[str, Any]:
    matches = [
        member
        for member in compiled_ir.get("members", [])
        if member.get("member_id") == member_id
    ]
    if len(matches) != 1:
        raise EditorialPresentationError(
            "compiled IR must contain exactly one requested member"
        )
    return matches[0]


def _proposition_index(member: dict[str, Any]) -> dict[str, dict[str, Any]]:
    propositions = member["proposition_graph"]["propositions"]
    result = {item["proposition_id"]: item for item in propositions}
    if len(result) != len(propositions):
        raise EditorialPresentationError(
            "compiled proposition identities are not unique"
        )
    return result


def _semantic_tier_from_parts(
    *,
    coverage: dict[str, Any],
    primary_propositions: list[dict[str, Any]],
    review_route: str,
    source_constraints: list[dict[str, Any]],
    coverage_boundaries: list[dict[str, Any]],
) -> str:
    if (
        review_route == "blocked"
        or coverage["missing_evidence_actions"]
        or coverage["unresolved_service_actions"]
        or any(
            item.get("semantic_effect") == "blocks_behavioral_propositions"
            for item in source_constraints
        )
    ):
        return "receipts_only"

    if not primary_propositions:
        if (
            coverage["present_actions"]
            or coverage["not_voting_actions"]
            or coverage["directional_yes_no_positions"] == 0
            or coverage_boundaries
        ):
            return "non_directional_or_limited_evidence"
        return "receipts_only"

    has_repeated_pattern = any(
        item["semantic_role"] == "behavioral"
        and item["proposition_type"] == "repeated_pattern"
        for item in primary_propositions
    )
    has_conclusion_synthesis = any(
        item["semantic_role"] == "synthesis"
        and item["proposition_type"]
        in {"mechanism_divide", "uniform_direction", "no_common_throughline"}
        for item in primary_propositions
    )
    if has_repeated_pattern and has_conclusion_synthesis:
        return "reviewed_conclusion"
    return "developing_read"


def semantic_tier_for_artifact(artifact: dict[str, Any]) -> str:
    meaning = artifact["compiled_semantic_meaning"]
    propositions = {item["proposition_id"]: item for item in meaning["propositions"]}
    return _semantic_tier_from_parts(
        coverage=artifact["evidence_metadata"]["coverage"],
        primary_propositions=[
            propositions[item] for item in meaning["primary_proposition_ids"]
        ],
        review_route=meaning["review_route"],
        source_constraints=meaning["source_render_constraints"],
        coverage_boundaries=meaning["coverage_boundaries"],
    )


def _presentation_boundaries(
    identity: dict[str, Any],
    member: dict[str, Any],
    propositions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    planned_action_ids = {
        action_id
        for proposition in propositions
        for action_id in proposition["evidence_action_ids"]
    }
    planned_episode_ids = {
        episode_id
        for proposition in propositions
        for episode_id in proposition["evidence_episode_ids"]
    }
    complete_action_ids = {
        action_id
        for proposition in member["proposition_graph"]["propositions"]
        for action_id in proposition["evidence_action_ids"]
    }
    complete_action_ids.update(
        action_id
        for boundary in member["composition"]["method_boundaries"]
        for action_id in boundary.get("action_ids", [])
    )
    complete_episode_ids = {
        episode_id
        for proposition in member["proposition_graph"]["propositions"]
        for episode_id in proposition["evidence_episode_ids"]
    }
    full_record_boundary = (
        member["coverage"]["missing_evidence_actions"] == 0
        and member["coverage"]["partial_episodes"] == 0
        and member["coverage"]["complete_episodes"] == len(complete_episode_ids)
        and member["coverage"]["resolved_eligible_actions"]
        + member["coverage"]["context_only_control_actions"]
        == len(complete_action_ids)
    )
    action_ids = sorted(
        complete_action_ids if full_record_boundary else planned_action_ids
    )
    episode_ids = sorted(
        complete_episode_ids if full_record_boundary else planned_episode_ids
    )
    suffix = (
        f"{identity['member_id']}:{identity['issue_id']}:{identity['scope']}"
    ).lower()
    boundaries = [
        {
            "boundary_id": f"boundary:coverage:{suffix}",
            "boundary_type": "reviewed_evidence_coverage",
            "presentation_target": "coverage_note",
            "action_ids": action_ids,
            "episode_ids": episode_ids,
        },
        {
            "boundary_id": f"boundary:scope:{suffix}",
            "boundary_type": "reviewed_congress_scope",
            "presentation_target": "scope_note",
            "action_ids": action_ids,
            "episode_ids": episode_ids,
        },
    ]
    boundaries.extend(copy.deepcopy(member["composition"]["coverage_boundaries"]))
    boundaries.extend(copy.deepcopy(member["composition"]["method_boundaries"]))
    return boundaries


def source_constraint_boundaries(
    constraints: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": item["constraint_id"],
            "boundary_type": item.get("constraint_type", "source_render_constraint"),
            "presentation_target": item.get("presentation_target", "source_note"),
            "action_ids": copy.deepcopy(item.get("action_ids", [])),
            "episode_ids": copy.deepcopy(item.get("episode_ids", [])),
        }
        for item in constraints
    ]


def _mapping_ids(wording: dict[str, Any]) -> list[str]:
    result: list[str] = []

    def collect(record: Any) -> None:
        if isinstance(record, dict):
            mapping = record.get("mapping")
            if isinstance(mapping, dict) and isinstance(mapping.get("mapping_id"), str):
                result.append(mapping["mapping_id"])
            for value in record.values():
                collect(value)
        elif isinstance(record, list):
            for value in record:
                collect(value)

    collect(wording)
    return sorted(result)


def _validate_analytical_text(
    record: dict[str, Any],
    *,
    allowed_targets: set[str],
    propositions: dict[str, dict[str, Any]],
    boundaries: dict[str, dict[str, Any]],
    source_refs: set[str],
    receipt_refs: set[str],
    trusted_action_source_contract: dict[str, Any] | None,
) -> None:
    if (
        set(record) != {"statement_id", "text", "mapping"}
        or not isinstance(record["statement_id"], str)
        or not record["statement_id"].strip()
        or not isinstance(record["text"], str)
        or not record["text"].strip()
    ):
        raise EditorialPresentationError(
            "analytical wording must contain a statement ID, text, and an explicit mapping"
        )
    mapping = record["mapping"]
    required = {
        "mapping_id",
        "proposition_ids",
        "boundary_ids",
        "presentation_target",
        "action_ids",
        "episode_ids",
        "source_refs",
        "receipt_refs",
    }
    if set(mapping) != required or not mapping["mapping_id"]:
        raise EditorialPresentationError("analytical wording mapping is incomplete")
    proposition_ids = set(mapping["proposition_ids"])
    boundary_ids = set(mapping["boundary_ids"])
    if bool(proposition_ids) == bool(boundary_ids):
        raise EditorialPresentationError(
            "analytical wording must map to propositions or typed boundaries"
        )
    unknown_propositions = proposition_ids - set(propositions)
    unknown_boundaries = boundary_ids - set(boundaries)
    if unknown_propositions or unknown_boundaries:
        raise EditorialPresentationError(
            "analytical wording references an unknown proposition or boundary"
        )
    referenced = [
        *(propositions[item] for item in proposition_ids),
        *(boundaries[item] for item in boundary_ids),
    ]
    targets = {item["presentation_target"] for item in referenced}
    if mapping["presentation_target"] not in allowed_targets or targets != {
        mapping["presentation_target"]
    }:
        raise EditorialPresentationError(
            "analytical wording is mapped to the wrong presentation section"
        )
    expected_actions = {
        action_id
        for item in referenced
        for action_id in item.get("evidence_action_ids", item.get("action_ids", []))
    }
    expected_episodes = {
        episode_id
        for item in referenced
        for episode_id in item.get("evidence_episode_ids", item.get("episode_ids", []))
    }
    if set(mapping["action_ids"]) != expected_actions:
        raise EditorialPresentationError(
            "wording action IDs must exactly match compiled semantic evidence"
        )
    if set(mapping["episode_ids"]) != expected_episodes:
        raise EditorialPresentationError(
            "wording episode IDs must exactly match compiled semantic evidence"
        )
    if (
        not mapping["source_refs"]
        or not set(mapping["source_refs"]) <= source_refs
        or not mapping["receipt_refs"]
        or not set(mapping["receipt_refs"]) <= receipt_refs
    ):
        raise EditorialPresentationError(
            "analytical wording lacks valid source and receipt references"
        )
    mapped_sources = set(mapping["source_refs"])
    if trusted_action_source_contract is None:
        return
    action_source_requirements = trusted_action_source_contract["actions"]
    authorities = trusted_action_source_contract["source_authorities"]
    if not expected_actions:
        if not mapped_sources <= set(authorities):
            raise EditorialPresentationError(
                "analytical wording uses an unknown source"
            )
        return
    permitted_sources: set[str] = set()
    for action_id in expected_actions:
        requirement = action_source_requirements.get(action_id)
        if not isinstance(requirement, dict):
            raise EditorialPresentationError(
                f"analytical wording lacks source requirements for {action_id}"
            )
        permitted_sources.update(requirement.get("vote_source_refs", []))
        permitted_sources.update(requirement.get("action_meaning_source_refs", []))
    if (
        not mapped_sources <= set(authorities)
        or not mapped_sources <= permitted_sources
    ):
        raise EditorialPresentationError(
            "analytical wording uses a source not authorized for its exact actions"
        )
    for action_id in expected_actions:
        requirement = action_source_requirements.get(action_id)
        if not isinstance(requirement, dict):
            raise EditorialPresentationError(
                f"analytical wording lacks source requirements for {action_id}"
            )
        vote_sources = set(requirement.get("vote_source_refs", []))
        meaning_sources = set(requirement.get("action_meaning_source_refs", []))
        required_types = set(
            requirement.get("required_action_meaning_source_types", [])
        )
        mapped_meaning_types = {
            authorities[source] for source in mapped_sources & meaning_sources
        }
        if (
            not vote_sources
            or not meaning_sources
            or not vote_sources <= source_refs
            or not meaning_sources <= source_refs
            or not vote_sources <= mapped_sources
            or not meaning_sources <= mapped_sources
            or not required_types <= mapped_meaning_types
        ):
            raise EditorialPresentationError(
                "analytical wording lacks direct vote or action-meaning provenance"
            )


def validate_editorial_wording(
    wording: dict[str, Any],
    *,
    primary_ids: list[str],
    limiting_ids: list[str],
    propositions: dict[str, dict[str, Any]],
    boundaries: list[dict[str, Any]],
    provenance: dict[str, Any],
    trusted_action_source_contract: dict[str, Any] | None = None,
) -> list[str]:
    boundary_index = {item["boundary_id"]: item for item in boundaries}
    if len(boundary_index) != len(boundaries):
        raise EditorialPresentationError("typed boundary identities are not unique")
    source_refs = set(provenance["source_refs"])
    receipt_refs = set(provenance["receipt_refs"])

    def validate(record: dict[str, Any], targets: set[str]) -> None:
        _validate_analytical_text(
            record,
            allowed_targets=targets,
            propositions=propositions,
            boundaries=boundary_index,
            source_refs=source_refs,
            receipt_refs=receipt_refs,
            trusted_action_source_contract=trusted_action_source_contract,
        )

    for tier_wording in wording["tier_display"].values():
        if set(tier_wording) != {"badge", "teaser"} or not isinstance(
            tier_wording["badge"], str
        ):
            raise EditorialPresentationError(
                "tier display must separate a neutral badge from mapped teaser copy"
            )
        validate(
            tier_wording["teaser"],
            {
                "conclusion_only",
                "repeated_patterns",
                "policy_trajectories",
                "other_notable_choices",
                "coverage_note",
            },
        )
    validate(wording["coverage_text"], {"coverage_note"})
    validate(wording["scope_boundary"], {"scope_note"})

    conclusion_ids = {
        proposition_id
        for proposition_id in primary_ids
        if propositions[proposition_id]["presentation_target"] == "conclusion_only"
    }
    conclusion = wording.get("conclusion")
    if conclusion_ids:
        if not conclusion:
            raise EditorialPresentationError(
                "conclusion-only propositions require mapped conclusion wording"
            )
        validate(conclusion["headline"], {"conclusion_only"})
        validate(conclusion["body"], {"conclusion_only"})
        for field in ("headline", "body"):
            if set(conclusion[field]["mapping"]["proposition_ids"]) != conclusion_ids:
                raise EditorialPresentationError(
                    "conclusion wording must map to every conclusion-only proposition"
                )
    elif conclusion is not None:
        raise EditorialPresentationError(
            "conclusion wording is not allowed without a conclusion-only proposition"
        )

    expected_sections = {
        "repeated_patterns": {
            proposition_id
            for proposition_id in [*primary_ids, *limiting_ids]
            if propositions[proposition_id]["presentation_target"]
            == "repeated_patterns"
        },
        "policy_trajectories": {
            proposition_id
            for proposition_id in [*primary_ids, *limiting_ids]
            if propositions[proposition_id]["presentation_target"]
            == "policy_trajectories"
        },
    }
    for section, expected_ids in expected_sections.items():
        records = wording.get(section, [])
        actual_ids: list[str] = []
        for item in records:
            proposition_id = item["proposition_id"]
            actual_ids.append(proposition_id)
            for field in ("heading", "body"):
                validate(item[field], {section})
                if item[field]["mapping"]["proposition_ids"] != [proposition_id]:
                    raise EditorialPresentationError(
                        "section wording must map only its declared proposition"
                    )
        if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != expected_ids:
            raise EditorialPresentationError(
                f"{section} wording must map every proposition in its section"
            )

    for limitation in wording.get("limitations", []):
        for field in ("heading", "body"):
            validate(
                limitation[field],
                {"meaningful_limitations", "source_note", "scope_note"},
            )

    mapping_ids = _mapping_ids(wording)
    if len(mapping_ids) != len(set(mapping_ids)):
        raise EditorialPresentationError(
            "every analytical display field requires a unique mapping identity"
        )
    statement_ids = [item["statement_id"] for item in _mapped_records(wording)]
    if len(statement_ids) != len(set(statement_ids)):
        raise EditorialPresentationError(
            "every analytical display field requires a unique statement identity"
        )
    return mapping_ids


def _statement_ids(wording: dict[str, Any]) -> list[str]:
    return sorted(item["statement_id"] for item in _mapped_records(wording))


def expected_approval_subject(
    *,
    schema_version: str,
    identity: dict[str, Any],
    compiled_ir_sha256: str,
    wording: dict[str, Any],
    compiled_semantic_meaning: dict[str, Any],
    evidence_metadata: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    mapping_ids = _mapping_ids(wording)
    provenance_identity = _immutable_provenance(provenance)
    presentation_content = {
        "schema_version": schema_version,
        "artifact_identity": copy.deepcopy(identity),
        "compiled_semantic_meaning": copy.deepcopy(compiled_semantic_meaning),
        "editorial_wording": copy.deepcopy(wording),
        "evidence_metadata": copy.deepcopy(evidence_metadata),
        "evidence_provenance": provenance_identity,
    }
    subject = {
        "artifact_id": identity["artifact_id"],
        "artifact_version": identity["artifact_version"],
        "member_id": identity["member_id"],
        "issue_id": identity["issue_id"],
        "congress": identity["congress"],
        "approved_scope": identity["scope"],
        "schema_version": schema_version,
        "compiled_ir_sha256": compiled_ir_sha256,
        "reviewed_wording_sha256": reviewed_wording_digest(wording),
        "mapping_set_sha256": mapping_set_digest(wording),
        "evidence_provenance_sha256": canonical_digest(provenance_identity),
        "action_source_contract_id": provenance_identity["action_source_contract_id"],
        "action_source_contract_sha256": provenance_identity[
            "action_source_contract_sha256"
        ],
        "limitation_ids": [
            item["limitation_id"] for item in provenance_identity["review_limitations"]
        ],
        "limitations_sha256": limitations_digest(
            provenance_identity["review_limitations"]
        ),
        "presentation_content_sha256": canonical_digest(presentation_content),
        "statement_ids": _statement_ids(wording),
        "mapping_ids": sorted(mapping_ids),
    }
    return {
        **subject,
        "approval_subject_sha256": canonical_digest(subject),
    }


def approval_subject_for_artifact(
    artifact: dict[str, Any],
) -> dict[str, Any]:
    return expected_approval_subject(
        schema_version=artifact["schema_version"],
        identity=artifact["artifact_identity"],
        compiled_ir_sha256=artifact["provenance"]["compiled_ir_sha256"],
        wording=artifact["editorial_wording"],
        compiled_semantic_meaning=artifact["compiled_semantic_meaning"],
        evidence_metadata=artifact["evidence_metadata"],
        provenance=artifact["provenance"],
    )


def detached_receipt_matches(
    receipt: dict[str, Any] | None,
    *,
    expected_subject: dict[str, Any],
) -> bool:
    if not isinstance(receipt, dict):
        return False
    if set(receipt) != {
        "schema_version",
        "receipt_id",
        "status",
        "binding",
        "approved_statement_ids",
        "approved_mapping_ids",
        "reviewer",
        "decision_timestamp",
        "limitations_sha256",
        "limitations_acknowledged",
        "decisions",
        "publication_activation",
    }:
        return False
    reviewer = receipt.get("reviewer", {})
    limitations = receipt.get("limitations_acknowledged", [])
    timestamp = receipt.get("decision_timestamp")
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        normalized_receipt_limitations = canonical_limitations(
            [
                {
                    "limitation_id": item.get("limitation_id"),
                    "text": item.get("text"),
                }
                for item in limitations
                if isinstance(item, dict)
            ]
        )
    except (AttributeError, ValueError, EditorialPresentationError):
        return False
    return bool(
        receipt.get("schema_version") == "editorial_public_issue_approval_receipt_v1"
        and isinstance(receipt.get("receipt_id"), str)
        and APPROVAL_RECEIPT_ID.fullmatch(receipt["receipt_id"])
        and receipt.get("status") == "approved"
        and receipt.get("binding") == expected_subject
        and receipt.get("approved_statement_ids") == expected_subject["statement_ids"]
        and receipt.get("approved_mapping_ids") == expected_subject["mapping_ids"]
        and isinstance(reviewer, dict)
        and set(reviewer) == {"reviewer_id", "authority"}
        and isinstance(reviewer.get("reviewer_id"), str)
        and REVIEWER_ID.fullmatch(reviewer["reviewer_id"])
        and reviewer.get("authority") in RECOGNIZED_REVIEWER_AUTHORITIES
        and parsed_timestamp.tzinfo is not None
        and isinstance(limitations, list)
        and receipt.get("limitations_sha256") == expected_subject["limitations_sha256"]
        and [item["limitation_id"] for item in normalized_receipt_limitations]
        == expected_subject["limitation_ids"]
        and limitations_digest(normalized_receipt_limitations)
        == expected_subject["limitations_sha256"]
        and all(
            isinstance(item, dict)
            and set(item) == {"limitation_id", "text", "acknowledged"}
            and item.get("limitation_id")
            and item.get("text")
            and item.get("acknowledged") is True
            for item in limitations
        )
        and receipt.get("decisions") == REQUIRED_DETACHED_DECISIONS
        and receipt.get("publication_activation")
        == {"active": False, "decision_scope": "out_of_scope"}
    )


def publication_gates_pass(
    controls: dict[str, Any],
    *,
    expected_subject: dict[str, Any],
    detached_receipt: dict[str, Any] | None = None,
) -> bool:
    if controls["benchmark"]["status"] not in BENCHMARK_STATUSES:
        return False
    return bool(
        controls["semantic"]["status"] == "accepted_semantic_reference"
        and controls["semantic"]["validation_status"] == "passed"
        and controls["editorial"]["human_approval_status"] == "human_approved"
        and controls["approval_mode"] == "detached_receipt_required"
        and detached_receipt_matches(
            detached_receipt,
            expected_subject=expected_subject,
        )
        and controls["benchmark"]["status"] == "gold_benchmark"
        and controls["production"]["eligible"] is True
        and controls["publication"]["active"] is True
    )


def build_approval_subject(
    compiled_ir: dict[str, Any],
    editorial_input: dict[str, Any],
    *,
    trusted_action_source_contract: dict[str, Any],
) -> dict[str, Any]:
    snapshot = copy.deepcopy(compiled_ir)
    identity = editorial_input["artifact_identity"]
    member = _member(snapshot, identity["member_id"])
    propositions = _proposition_index(member)
    plan = member["composition"]["conclusion_plan"]
    all_plan_ids = [
        *plan["primary_proposition_ids"],
        *plan["limiting_proposition_ids"],
    ]
    planned = [copy.deepcopy(propositions[item]) for item in all_plan_ids]
    boundaries = _presentation_boundaries(identity, member, planned)
    mapping_boundaries = [
        *boundaries,
        *source_constraint_boundaries(snapshot.get("source_render_constraints", [])),
    ]
    provenance = _prepare_provenance(
        editorial_input["provenance"],
        trusted_action_source_contract,
    )
    validate_editorial_wording(
        editorial_input["editorial_wording"],
        primary_ids=plan["primary_proposition_ids"],
        limiting_ids=plan["limiting_proposition_ids"],
        propositions=propositions,
        boundaries=mapping_boundaries,
        provenance=provenance,
        trusted_action_source_contract=trusted_action_source_contract,
    )
    action_ids = sorted(
        {
            action_id
            for proposition in planned
            for action_id in proposition["evidence_action_ids"]
        }
    )
    episode_ids = sorted(
        {
            episode_id
            for proposition in planned
            for episode_id in proposition["evidence_episode_ids"]
        }
    )
    meaning = {
        "primary_proposition_ids": copy.deepcopy(plan["primary_proposition_ids"]),
        "limiting_proposition_ids": copy.deepcopy(plan["limiting_proposition_ids"]),
        "propositions": planned,
        "source_render_constraints": copy.deepcopy(
            snapshot.get("source_render_constraints", [])
        ),
        "coverage_boundaries": copy.deepcopy(
            member["composition"]["coverage_boundaries"]
        ),
        "presentation_boundaries": boundaries,
        "review_route": member["review_route"],
    }
    evidence = {
        "coverage": copy.deepcopy(member["coverage"]),
        "action_ids": action_ids,
        "episode_ids": episode_ids,
        "action_accounting": copy.deepcopy(member["action_accounting"]),
    }
    return expected_approval_subject(
        schema_version="editorial_public_issue_presentation_v1",
        identity=identity,
        compiled_ir_sha256=canonical_digest(snapshot),
        wording=editorial_input["editorial_wording"],
        compiled_semantic_meaning=meaning,
        evidence_metadata=evidence,
        provenance=provenance,
    )


def _unwrap(record: dict[str, Any]) -> str:
    return record["text"]


def _copy_display_wording(
    wording: dict[str, Any],
    *,
    semantic_tier: str,
) -> dict[str, Any]:
    tier_wording = wording["tier_display"][semantic_tier]

    def section_item(item: dict[str, Any]) -> dict[str, Any]:
        mapping = item["body"]["mapping"]
        result = {
            "heading": _unwrap(item["heading"]),
            "body": _unwrap(item["body"]),
            "action_ids": copy.deepcopy(mapping["action_ids"]),
        }
        if item.get("proposition_id"):
            result["proposition_id"] = item["proposition_id"]
        if item.get("boundary_id"):
            result["boundary_id"] = item["boundary_id"]
        return result

    conclusion = wording.get("conclusion")
    return {
        "tier": semantic_tier,
        "tier_badge": tier_wording["badge"],
        "teaser": _unwrap(tier_wording["teaser"]),
        "coverage_text": _unwrap(wording["coverage_text"]),
        "scope_boundary": _unwrap(wording["scope_boundary"]),
        "conclusion": (
            {
                "headline": _unwrap(conclusion["headline"]),
                "body": _unwrap(conclusion["body"]),
            }
            if conclusion
            else None
        ),
        "repeated_patterns": [
            section_item(item) for item in wording.get("repeated_patterns", [])
        ],
        "policy_trajectories": [
            section_item(item) for item in wording.get("policy_trajectories", [])
        ],
        "limitations": [section_item(item) for item in wording.get("limitations", [])],
    }


def fallback_display() -> dict[str, Any]:
    return {
        "tier": "receipts_only",
        "tier_badge": "Vote receipts",
        "teaser": (
            "Reviewed analytical wording is not published for this record scope."
        ),
        "coverage_text": None,
        "scope_boundary": None,
        "conclusion": None,
        "repeated_patterns": [],
        "policy_trajectories": [],
        "limitations": [],
    }


def compile_public_issue_presentation(
    compiled_ir: dict[str, Any],
    editorial_input: dict[str, Any],
    *,
    trusted_action_source_contract: dict[str, Any],
) -> dict[str, Any]:
    """Compile reviewed wording without deriving or rewriting analytical prose."""

    snapshot = copy.deepcopy(compiled_ir)
    identity = editorial_input["artifact_identity"]
    member = _member(snapshot, identity["member_id"])
    propositions = _proposition_index(member)
    plan = member["composition"]["conclusion_plan"]
    all_plan_ids = [
        *plan["primary_proposition_ids"],
        *plan["limiting_proposition_ids"],
    ]
    if not set(all_plan_ids) <= set(propositions):
        raise EditorialPresentationError("compiled conclusion plan is unresolved")

    planned_propositions = [
        copy.deepcopy(propositions[proposition_id]) for proposition_id in all_plan_ids
    ]
    boundaries = _presentation_boundaries(identity, member, planned_propositions)
    mapping_boundaries = [
        *boundaries,
        *source_constraint_boundaries(snapshot.get("source_render_constraints", [])),
    ]
    wording = editorial_input["editorial_wording"]
    provenance_input = _prepare_provenance(
        editorial_input["provenance"],
        trusted_action_source_contract,
    )
    validate_editorial_wording(
        wording,
        primary_ids=plan["primary_proposition_ids"],
        limiting_ids=plan["limiting_proposition_ids"],
        propositions=propositions,
        boundaries=mapping_boundaries,
        provenance=provenance_input,
        trusted_action_source_contract=trusted_action_source_contract,
    )
    compiled_digest = canonical_digest(snapshot)
    controls = copy.deepcopy(editorial_input["controls"])
    semantic_tier = _semantic_tier_from_parts(
        coverage=member["coverage"],
        primary_propositions=[
            propositions[item] for item in plan["primary_proposition_ids"]
        ],
        review_route=member["review_route"],
        source_constraints=snapshot.get("source_render_constraints", []),
        coverage_boundaries=member["composition"]["coverage_boundaries"],
    )
    action_ids = sorted(
        {
            action_id
            for proposition in planned_propositions
            for action_id in proposition["evidence_action_ids"]
        }
    )
    episode_ids = sorted(
        {
            episode_id
            for proposition in planned_propositions
            for episode_id in proposition["evidence_episode_ids"]
        }
    )
    meaning = {
        "primary_proposition_ids": copy.deepcopy(plan["primary_proposition_ids"]),
        "limiting_proposition_ids": copy.deepcopy(plan["limiting_proposition_ids"]),
        "propositions": planned_propositions,
        "source_render_constraints": copy.deepcopy(
            snapshot.get("source_render_constraints", [])
        ),
        "coverage_boundaries": copy.deepcopy(
            member["composition"]["coverage_boundaries"]
        ),
        "presentation_boundaries": boundaries,
        "review_route": member["review_route"],
    }
    evidence = {
        "coverage": copy.deepcopy(member["coverage"]),
        "action_ids": action_ids,
        "episode_ids": episode_ids,
        "action_accounting": copy.deepcopy(member["action_accounting"]),
    }
    subject = expected_approval_subject(
        schema_version="editorial_public_issue_presentation_v1",
        identity=identity,
        compiled_ir_sha256=compiled_digest,
        wording=wording,
        compiled_semantic_meaning=meaning,
        evidence_metadata=evidence,
        provenance=provenance_input,
    )
    gates_pass = publication_gates_pass(
        controls,
        expected_subject=subject,
    )
    public_tier = (
        semantic_tier
        if semantic_tier in ANALYTICAL_TIERS and gates_pass
        else "receipts_only"
    )
    provenance = copy.deepcopy(provenance_input)
    provenance["compiled_ir_sha256"] = compiled_digest
    provenance["reviewed_wording_sha256"] = subject["reviewed_wording_sha256"]
    provenance["mapping_set_sha256"] = subject["mapping_set_sha256"]
    provenance["evidence_provenance_sha256"] = subject["evidence_provenance_sha256"]
    provenance["presentation_content_sha256"] = subject["presentation_content_sha256"]
    provenance["limitations_sha256"] = subject["limitations_sha256"]
    provenance["approval_subject_sha256"] = subject["approval_subject_sha256"]
    provenance["compiler_receipt"] = copy.deepcopy(subject)

    artifact = {
        "schema_version": "editorial_public_issue_presentation_v1",
        "artifact_identity": copy.deepcopy(identity),
        "compiled_semantic_meaning": meaning,
        "editorial_wording": copy.deepcopy(wording),
        "frontend_display": (
            _copy_display_wording(wording, semantic_tier=semantic_tier)
            if public_tier != "receipts_only"
            else fallback_display()
        ),
        "evidence_metadata": evidence,
        "provenance": provenance,
        "controls": {
            **controls,
            "derived_semantic_tier": semantic_tier,
            "effective_public_tier": public_tier,
            "publication_gates_passed": gates_pass,
        },
    }
    if canonical_digest(snapshot) != compiled_digest:
        raise RuntimeError("presentation compilation mutated compiled Semantic IR")
    return artifact
