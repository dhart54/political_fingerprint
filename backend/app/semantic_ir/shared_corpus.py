"""Member-neutral legislative corpus contracts and Semantic IR adapter.

The contracts in this module are deliberately House/exact-action scoped.  They
split accepted legislative meaning and issue taxonomy from member action state;
they do not replace the Editorial Semantic IR compiler.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA_VERSION = "shared_legislative_corpus_v1"
MEMBER_FIELDS = {
    "evidence_status",
    "exact_choice_effect",
    "legislator_id",
    "member_action",
    "member_bioguide_id",
    "member_direction",
    "member_id",
    "member_name",
    "member_position_effect",
    "member_status",
    "official_member_action",
    "party",
    "service_status",
    "status",
}
MEANING_FIELDS = {
    "accepted_exact_action_meaning",
    "action_meaning",
    "action_meaning_override",
    "exact_action_basis",
    "implemented_exact_action_meaning",
    "policy_meaning",
}


class SharedCorpusValidationError(ValueError):
    """Raised when a shared-corpus boundary or digest contract is violated."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sealed_digest(record: dict[str, Any], field: str) -> str:
    subject = {key: value for key, value in record.items() if key != field}
    return digest(subject)


def _identity_set(identities: list[dict[str, Any]]) -> set[bytes]:
    """Compare governed source identities by their complete typed identity."""
    return {canonical_bytes(identity) for identity in identities}


def _walk_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(
            *(_walk_keys(item) for item in value.values()), set()
        )
    if isinstance(value, list):
        return set().union(*(_walk_keys(item) for item in value), set())
    return set()


def _validate_schema(root: Path, artifact: dict[str, Any], definition: str) -> None:
    schema = json.loads(
        (root / "docs/semantic_ir/shared_legislative_corpus_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(
        {"$ref": f"#/$defs/{definition}", **schema},
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(artifact), key=lambda error: list(error.absolute_path)
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise SharedCorpusValidationError(
            f"{definition} schema failure at {location}: {error.message}"
        )


def choice_effect(status: str) -> str:
    try:
        return {
            "Yea": "supports_exact_choice",
            "Nay": "opposes_exact_choice",
            "Present": "resolved_non_directional",
            "Not Voting": "resolved_non_directional",
            "Missing Evidence": "missing_evidence",
        }[status]
    except KeyError as exc:
        raise SharedCorpusValidationError(
            f"unsupported official House status: {status}"
        ) from exc


def validate_shared_action_core(root: Path, artifact: dict[str, Any]) -> None:
    _validate_schema(root, artifact, "sharedActionCoreArtifact")
    forbidden = _walk_keys(artifact) & MEMBER_FIELDS
    if forbidden:
        raise SharedCorpusValidationError(
            f"Shared Action Core contains member fields: {sorted(forbidden)}"
        )
    identities: dict[tuple[str, str], str] = {}
    for action in artifact["actions"]:
        if action["action_core_sha256"] != sealed_digest(action, "action_core_sha256"):
            raise SharedCorpusValidationError(
                f"shared action digest differs: {action['action_id']}"
            )
        source_digest = digest(action["governed_source_identities"])
        if action["governed_source_identity_sha256"] != source_digest:
            raise SharedCorpusValidationError(
                f"shared source digest differs: {action['action_id']}"
            )
        governed_sources = _identity_set(action["governed_source_identities"])
        outcome_sources = _identity_set(action["action_outcome_source_identities"])
        operative_sources = _identity_set(
            action["operative_meaning_source_identities"]
        )
        if not outcome_sources <= governed_sources:
            raise SharedCorpusValidationError(
                f"action-outcome source is not governed for exact action: {action['action_id']}"
            )
        if not operative_sources <= governed_sources:
            raise SharedCorpusValidationError(
                f"operative-meaning source is not governed for exact action: {action['action_id']}"
            )
        if (
            outcome_sources & operative_sources
            or outcome_sources | operative_sources != governed_sources
        ):
            raise SharedCorpusValidationError(
                f"governed sources are not partitioned by exact-action role: {action['action_id']}"
            )
        expected_clerk_id = (
            f"clerk:{action['congress']}:{action['session']}:{action['roll']}"
        )
        if not any(
            source["source_id"] == expected_clerk_id
            and source["source_type"] == "house_clerk_roll_call"
            for source in action["action_outcome_source_identities"]
        ):
            raise SharedCorpusValidationError(
                f"action-outcome source does not identify exact House action: {action['action_id']}"
            )
        governed_source_ids = {
            source["source_id"] for source in action["governed_source_identities"]
        }
        if not set(action["semantic_ir_source_ids"]) <= governed_source_ids:
            raise SharedCorpusValidationError(
                f"Semantic IR source does not resolve to governed identity: {action['action_id']}"
            )
        key = (action["exact_action_identity"], source_digest)
        meaning_digest = digest(action["accepted_exact_action_meaning"])
        if key in identities and identities[key] != meaning_digest:
            raise SharedCorpusValidationError(
                "same exact action/source version has conflicting current meanings"
            )
        identities[key] = meaning_digest
        if action["enactment_status"] != "not_inferred_from_house_outcome":
            raise SharedCorpusValidationError(
                f"enactment inferred from chamber outcome: {action['action_id']}"
            )
    if len({row["action_id"] for row in artifact["actions"]}) != len(
        artifact["actions"]
    ):
        raise SharedCorpusValidationError(
            "Shared Action Core action identities must be unique"
        )
    if artifact["corpus_sha256"] != digest(artifact["actions"]):
        raise SharedCorpusValidationError("Shared Action Core corpus digest differs")


def validate_shared_issue_mapping(
    root: Path, artifact: dict[str, Any], core: dict[str, Any]
) -> None:
    _validate_schema(root, artifact, "sharedIssueMappingArtifact")
    forbidden = _walk_keys(artifact) & (MEMBER_FIELDS | MEANING_FIELDS)
    if forbidden:
        raise SharedCorpusValidationError(
            f"Shared Issue Mapping contains forbidden fields: {sorted(forbidden)}"
        )
    core_ids = {row["action_id"] for row in core["actions"]}
    mapping_ids = [row["action_id"] for row in artifact["action_mappings"]]
    if len(mapping_ids) != len(set(mapping_ids)):
        raise SharedCorpusValidationError(
            "Shared Issue Mapping action identities must be unique"
        )
    episodes = {row["episode_id"]: row for row in artifact["episodes"]}
    families = {row["policy_family_id"] for row in artifact["policy_families"]}
    traits = {row["trait_id"] for row in artifact["policy_traits"]}
    for mapping in artifact["action_mappings"]:
        if mapping["action_id"] not in core_ids:
            raise SharedCorpusValidationError(
                f"issue mapping references unknown action: {mapping['action_id']}"
            )
        if mapping["mapping_sha256"] != sealed_digest(mapping, "mapping_sha256"):
            raise SharedCorpusValidationError(
                f"issue mapping digest differs: {mapping['action_id']}"
            )
        if mapping["episode_id"] is not None and mapping["episode_id"] not in episodes:
            raise SharedCorpusValidationError(
                f"issue mapping references unknown episode: {mapping['action_id']}"
            )
        if not set(mapping["policy_family_refs"]) <= families:
            raise SharedCorpusValidationError(
                f"issue mapping references unknown family: {mapping['action_id']}"
            )
        if not set(mapping["policy_trait_refs"]) <= traits:
            raise SharedCorpusValidationError(
                f"issue mapping references unknown trait: {mapping['action_id']}"
            )
    for episode in episodes.values():
        if not set(episode["action_ids"]) <= set(mapping_ids):
            raise SharedCorpusValidationError(
                f"episode references an unmapped action: {episode['episode_id']}"
            )
    if artifact["mapping_sha256"] != digest(
        {key: value for key, value in artifact.items() if key != "mapping_sha256"}
    ):
        raise SharedCorpusValidationError(
            "Shared Issue Mapping artifact digest differs"
        )


def validate_member_projection(
    root: Path, artifact: dict[str, Any], core: dict[str, Any]
) -> None:
    _validate_schema(root, artifact, "memberActionProjectionArtifact")
    forbidden = _walk_keys(artifact) & MEANING_FIELDS
    if forbidden:
        raise SharedCorpusValidationError(
            f"Member Action Projection attempts to author meaning: {sorted(forbidden)}"
        )
    core_by_id = {row["action_id"]: row for row in core["actions"]}
    projected_ids = [row["action_id"] for row in artifact["actions"]]
    if len(projected_ids) != len(set(projected_ids)):
        raise SharedCorpusValidationError(
            "Member Action Projection action identities must be unique"
        )
    for action in artifact["actions"]:
        action_id = action["action_id"]
        if action_id not in core_by_id:
            raise SharedCorpusValidationError(
                f"member projection references unknown action: {action_id}"
            )
        if action["action_core_sha256"] != core_by_id[action_id]["action_core_sha256"]:
            raise SharedCorpusValidationError(
                f"member projection references wrong action digest: {action_id}"
            )
        if action["member_action_source_identity_sha256"] != digest(
            action["member_action_source_identities"]
        ):
            raise SharedCorpusValidationError(
                f"member projection references wrong source digest: {action_id}"
            )
        if _identity_set(action["member_action_source_identities"]) != _identity_set(
            core_by_id[action_id]["action_outcome_source_identities"]
        ):
            raise SharedCorpusValidationError(
                f"member projection source does not match governed exact-action source: {action_id}"
            )
        if action["exact_choice_effect"] != choice_effect(action["official_status"]):
            raise SharedCorpusValidationError(
                f"member exact-choice effect is not deterministic: {action_id}"
            )
        component = action.get("component_ref")
        if component and component not in core_by_id[action_id][
            "package_component_boundary"
        ].get("governed_component_relationships", []):
            raise SharedCorpusValidationError(
                f"ungoverned package component projection: {action_id}"
            )
    if artifact["projection_sha256"] != digest(
        {key: value for key, value in artifact.items() if key != "projection_sha256"}
    ):
        raise SharedCorpusValidationError(
            "Member Action Projection artifact digest differs"
        )


def adapt_to_semantic_ir_input(
    root: Path,
    core: dict[str, Any],
    mapping: dict[str, Any],
    member_projections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reconstruct the existing compiler input without reinterpreting semantics."""
    validate_shared_action_core(root, core)
    validate_shared_issue_mapping(root, mapping, core)
    for projection in member_projections:
        validate_member_projection(root, projection, core)
    core_by_id = {row["action_id"]: row for row in core["actions"]}
    mapped_action_ids = [row["action_id"] for row in mapping["action_mappings"]]
    projection_actions: dict[str, dict[str, dict[str, Any]]] = {}
    for projection in member_projections:
        by_id = {row["action_id"]: row for row in projection["actions"]}
        missing = sorted(set(mapped_action_ids) - set(by_id))
        if missing:
            raise SharedCorpusValidationError(
                f"Member Action Projection lacks mapped actions: {missing}"
            )
        projection_actions[projection["member_id"]] = by_id
    shared_actions = []
    for row in mapping["action_mappings"]:
        action = core_by_id[row["action_id"]]
        shared_actions.append(
            {
                "action_id": row["action_id"],
                "action_meaning_ref": action["action_meaning_ref"],
                "eligibility": {
                    "decision": row["eligibility"]["decision"],
                    "domain": mapping["domain_id"],
                    "exact_action_basis": action["accepted_exact_action_meaning"],
                    "parent_context_used": row["eligibility"]["parent_context_used"],
                },
                "episode_id": row["episode_id"],
                "legislative_stage": action["legislative_stage"],
                "policy_trait_refs": copy.deepcopy(row["policy_trait_refs"]),
                "source_ids": copy.deepcopy(action["semantic_ir_source_ids"]),
                "structural_metadata": copy.deepcopy(row["structural_metadata"]),
            }
        )
    return {
        "case_scope": copy.deepcopy(mapping["semantic_ir_case_scope"]),
        "members": [
            {
                "member_id": projection["member_id"],
                "party": projection["party"],
                "actions": [
                    {
                        "action_id": row["action_id"],
                        "evidence_status": row["evidence_status"],
                        "service_status": row["service_status"],
                        "status": row["official_status"],
                    }
                    for action_id in mapped_action_ids
                    for row in [projection_actions[projection["member_id"]][action_id]]
                ],
            }
            for projection in member_projections
        ],
        "shared_semantics": {
            "actions": shared_actions,
            "episodes": copy.deepcopy(mapping["episodes"]),
            "policy_families": copy.deepcopy(mapping["policy_families"]),
            "policy_traits": copy.deepcopy(mapping["policy_traits"]),
            "shared_review_dependencies": copy.deepcopy(
                mapping["shared_review_dependencies"]
            ),
            "source_render_constraints": copy.deepcopy(
                mapping["source_render_constraints"]
            ),
            "trait_relationships": copy.deepcopy(mapping["trait_relationships"]),
        },
    }


def validate_migration_parity(actual: object, accepted: object, label: str) -> None:
    """Fail closed when a parity-only migration changes an accepted object."""
    if canonical_bytes(actual) != canonical_bytes(accepted):
        raise SharedCorpusValidationError(f"parity-only migration changed {label}")


def assert_no_protected_artifact_changes(paths: list[str]) -> None:
    """Reject changes to historical accepted domain/member artifact families."""
    protected = (
        "f000477_justice_public_safety",
        "f000477_education_workforce",
        "f000477_national_security_foreign",
        "f000477_environment_energy",
    )
    violations = sorted(
        path for path in paths if any(token in path.lower() for token in protected)
    )
    if violations:
        raise SharedCorpusValidationError(
            f"historical protected artifacts changed: {violations}"
        )
