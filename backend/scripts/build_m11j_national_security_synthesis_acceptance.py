"""Build M11J human synthesis authority and deterministic implementation."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from backend.app.etl.full_record_synthesis_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    apply_bounded_revision,
    digest,
    seal,
    validate_authority,
    validate_implementation,
)


ACCEPTED_M11I_PR = 141
ACCEPTED_M11I_HEAD = "8535163aee1d2a548ec7d0c23935b1322a05b863"
POST_M11I_MERGE_MAIN = "e9e771b23eb65629e0a3ed7ecb6c32748d7ebf59"
REVIEWER_ID = "dhart54"
REVIEWER_AUTHORITY = "full_record_synthesis_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-10T01:47:27Z"

M11I_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_national_security_foreign_119_v1"
)
PACKAGE_PATH = M11I_ROOT / "synthesis_candidate_package.json"
TEMPLATE_PATH = M11I_ROOT / "human_synthesis_decision_template.json"
M11I_PARITY_PATH = M11I_ROOT / "parity_manifest.json"
M11H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)
M11H_AUTHORITY_PATH = M11H_ROOT / "human_behavioral_semantic_ir_authority.json"
M11H_IMPLEMENTATION_PATH = (
    M11H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
M11H_PARITY_PATH = M11H_ROOT / "implementation_parity_manifest.json"
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_national_security_foreign_119_v1"
)
AUTHORITY_PATH = OUTPUT_ROOT / "human_synthesis_authority.json"
IMPLEMENTATION_PATH = OUTPUT_ROOT / "synthesis_decision_implementation.json"
PARITY_PATH = OUTPUT_ROOT / "implementation_parity_manifest.json"
DOSSIER_PATH = OUTPUT_ROOT / "implementation_dossier.md"

AUTHORITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_authority_v1.schema.json"
)
IMPLEMENTATION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_synthesis_decision_implementation_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_implementation_parity_v1.schema.json"
)

PACKAGE_ID = "synthesis-candidates:f000477:national_security_foreign:119:v1"
PACKAGE_FILE_SHA256 = "e5cfd7305babb5690d496a02b3c1dcc056d4368d980f0d25e5dd1c8d988345c8"
PACKAGE_SUBJECT_SHA256 = (
    "662917b23193042cd8bfd2b8db3666fa951351ef988fe37056902236109ea1ad"
)
TEMPLATE_ID = (
    "human-synthesis-decision-template:f000477:national_security_foreign:119:v1"
)
TEMPLATE_FILE_SHA256 = (
    "9727717a17b5cbf48786f8eee0f1ece71f347dff1d9fceec983eaa060f2f3a11"
)
TEMPLATE_SUBJECT_SHA256 = (
    "0a1bbbf303fb5ddb364fc646d67d74c8f8b0d5e40164a257ea413ed01f566a39"
)
M11I_PARITY_ID = "synthesis-candidate-parity:f000477:national_security_foreign:119:v1"
M11I_PARITY_FILE_SHA256 = (
    "412103e7c380c6da506b9a03512626cd35b613af9782676572a87f7c3757b7e0"
)
M11I_PARITY_SUBJECT_SHA256 = (
    "eb857e98f7a1c824116537967d08c61bb6d846eb47f08be359c04bc38ead4ea4"
)
M11H_AUTHORITY_FILE_SHA256 = (
    "d1de0f28a09a01ea9b5bbe5607128564daa6aedb929a2be1255cb50f1a99fc93"
)
M11H_AUTHORITY_SUBJECT_SHA256 = (
    "22262c77622df938b3ab3642bf49452005b549706bb20160dd7c91a88ba29714"
)
M11H_IMPLEMENTATION_FILE_SHA256 = (
    "13927cade21c85f95c097acf7afe831e55bdb0de79c93e54646e14640d444ecc"
)
M11H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "6113be3d0fad4d8da21a47ed76c089f5a7d96becd45abb9c888cf2a437bf8d67"
)
M11H_PARITY_FILE_SHA256 = (
    "c797e00d3aa13825361c878e84ed7b3607d5a705d64674ca3a01cada9952a8b9"
)
M11H_PARITY_SUBJECT_SHA256 = (
    "fcd319db713eb15d65c5cef380d9800db51a3ab1d578925a6131ed63ae78859e"
)

AUTHORITY_ID = "human-synthesis-authority:f000477:national_security_foreign:119:v1"
IMPLEMENTATION_ID = (
    "synthesis-decision-implementation:f000477:national_security_foreign:119:v1"
)
PARITY_ID = "synthesis-implementation-parity:f000477:national_security_foreign:119:v1"
WAR_POWERS_ID = "synthesis-war-powers-cross-target-uniform-direction"
ASSISTANCE_ID = "synthesis-security-assistance-interpretive-boundary"

REVISED_ASSISTANCE_PROPOSITION = (
    "Across the accepted Ukraine, Jordan, Taiwan, and Israel assistance propositions, "
    "Foushee’s Ukraine, Jordan, and Taiwan choices generally preserved or authorized "
    "assistance, while the Israel choice supported a specific $3.3 billion Foreign "
    "Military Financing reduction; these accepted inputs therefore do not support a "
    "single uniform cross-country assistance position."
)
UKRAINE_DIRECTION_LIMITATION = (
    "The Ukraine source direction `mixed` is proposition-relative mechanical metadata "
    "reflecting opposition to restrictive propositions plus support for an authorizing "
    "proposition; it does not itself establish mixed substantive orientation toward "
    "Ukraine assistance."
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def content_sha256(content: str) -> str:
    import hashlib

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"{path.relative_to(ROOT)} differs from regeneration")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def inferred_schema(value: object) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        return {
            "type": "array",
            "items": merge_schemas([inferred_schema(v) for v in value]),
        }
    if isinstance(value, dict):
        return {
            "type": "object",
            "additionalProperties": False,
            "required": sorted(value),
            "properties": {k: inferred_schema(v) for k, v in sorted(value.items())},
        }
    raise TypeError(type(value))


def merge_schemas(values: list[dict[str, Any]]) -> dict[str, Any]:
    unique = {json.dumps(v, sort_keys=True, separators=(",", ":")): v for v in values}
    schemas = list(unique.values())
    if not schemas:
        return {}
    if len(schemas) == 1:
        return schemas[0]
    if all(v.get("type") == "object" for v in schemas):
        keys = set(schemas[0].get("properties", {}))
        required = schemas[0].get("required")
        if all(
            set(v.get("properties", {})) == keys and v.get("required") == required
            for v in schemas
        ):
            return {
                "type": "object",
                "additionalProperties": False,
                "required": required,
                "properties": {
                    k: merge_schemas([v["properties"][k] for v in schemas])
                    for k in sorted(keys)
                },
            }
    return {"anyOf": schemas}


def schema(value: dict[str, Any], schema_id: str) -> dict[str, Any]:
    result = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": schema_id,
        **inferred_schema(value),
    }

    def exactly_one_alias(node: dict[str, Any], legacy: str, generic: str) -> None:
        properties = node.get("properties", {})
        required = node.get("required", [])
        if legacy not in properties:
            return
        properties[generic] = deepcopy(properties[legacy])
        if legacy in required:
            required.remove(legacy)
        node.setdefault("allOf", []).append(
            {"oneOf": [{"required": [legacy]}, {"required": [generic]}]}
        )

    def generalize(node: object) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            if {"accepted_head", "accepted_pr", "post_merge_main"}.issubset(properties):
                properties.setdefault("reviewed_base", {"type": "string"})
            accounting = properties.get("accepted_episode_disposition_accounting")
            if isinstance(accounting, dict):
                accounting.setdefault("properties", {})[
                    "unused_non_directional_evidence_episode_count"
                ] = {"type": "integer"}
            for legacy, generic in (
                (
                    "m11h_authority_binding",
                    "accepted_behavioral_semantic_ir_authority_binding",
                ),
                (
                    "m11h_implementation_binding",
                    "accepted_behavioral_semantic_ir_implementation_binding",
                ),
                (
                    "m11h_parity_binding",
                    "accepted_behavioral_semantic_ir_parity_binding",
                ),
                ("m11i_parity_binding", "synthesis_candidate_parity_binding"),
                (
                    "m11h_record_id",
                    "accepted_behavioral_semantic_ir_record_id",
                ),
                (
                    "m11h_record_subject_sha256",
                    "accepted_behavioral_semantic_ir_record_subject_sha256",
                ),
            ):
                exactly_one_alias(node, legacy, generic)
        for child in node.values():
            if isinstance(child, dict):
                generalize(child)

    generalize(result)
    return result


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    expected = {
        PACKAGE_PATH: PACKAGE_FILE_SHA256,
        TEMPLATE_PATH: TEMPLATE_FILE_SHA256,
        M11I_PARITY_PATH: M11I_PARITY_FILE_SHA256,
        M11H_AUTHORITY_PATH: M11H_AUTHORITY_FILE_SHA256,
        M11H_IMPLEMENTATION_PATH: M11H_IMPLEMENTATION_FILE_SHA256,
        M11H_PARITY_PATH: M11H_PARITY_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    package, template, m11h_authority, m11h_implementation = (
        load(PACKAGE_PATH),
        load(TEMPLATE_PATH),
        load(M11H_AUTHORITY_PATH),
        load(M11H_IMPLEMENTATION_PATH),
    )
    if not (
        package["artifact_id"] == PACKAGE_ID
        and package["synthesis_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256
        and template["artifact_id"] == TEMPLATE_ID
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and m11h_authority["authority_subject_sha256"] == M11H_AUTHORITY_SUBJECT_SHA256
        and m11h_implementation["implementation_subject_sha256"]
        == M11H_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M11H/M11I identity differs")
    return package, template, m11h_authority, m11h_implementation


def bindings() -> dict[str, Any]:
    return {
        "candidate_binding": {
            "artifact_id": PACKAGE_ID,
            "file_sha256": PACKAGE_FILE_SHA256,
            "candidate_subject_sha256": PACKAGE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M11I_PR,
            "accepted_head": ACCEPTED_M11I_HEAD,
            "post_merge_main": POST_M11I_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": TEMPLATE_ID,
            "file_sha256": TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": TEMPLATE_SUBJECT_SHA256,
        },
        "m11i_parity_binding": {
            "artifact_id": M11I_PARITY_ID,
            "file_sha256": M11I_PARITY_FILE_SHA256,
            "parity_subject_sha256": M11I_PARITY_SUBJECT_SHA256,
        },
        "m11h_authority_binding": {
            "artifact_id": "human-behavioral-semantic-ir-authority:f000477:national_security_foreign:119:v1",
            "file_sha256": M11H_AUTHORITY_FILE_SHA256,
            "authority_subject_sha256": M11H_AUTHORITY_SUBJECT_SHA256,
        },
        "m11h_implementation_binding": {
            "artifact_id": "behavioral-semantic-ir-decision-implementation:f000477:national_security_foreign:119:v1",
            "file_sha256": M11H_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M11H_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "m11h_parity_binding": {
            "file_sha256": M11H_PARITY_FILE_SHA256,
            "parity_subject_sha256": M11H_PARITY_SUBJECT_SHA256,
        },
    }


def replacement(
    path: list[object], original: object, revised: object
) -> dict[str, Any]:
    return {
        "path": path,
        "original_value_sha256": digest(original),
        "revised_value": revised,
    }


def assistance_revision(candidate: dict[str, Any]) -> dict[str, Any]:
    revised_limitations = [
        "The countries, accounts, measures, and restriction mechanisms differ.",
        "The Ukraine proposition includes one whole-measure authorization.",
        "The Taiwan and Israel inputs are singleton notable choices and remain excluded at the Behavioral Semantic IR layer.",
        "No reason for the country-specific differences is inferred.",
        UKRAINE_DIRECTION_LIMITATION,
    ]
    replacements = [
        replacement(
            ["proposition"], candidate["proposition"], REVISED_ASSISTANCE_PROPOSITION
        ),
        replacement(
            ["input_bindings", 0, "concise_input_summary"],
            candidate["input_bindings"][0]["concise_input_summary"],
            "Opposed three Ukraine-assistance restrictions and supported one Ukraine-support authorization.",
        ),
        replacement(
            ["relationship_basis", "semantic_relationship"],
            candidate["relationship_basis"]["semantic_relationship"],
            "The accepted Ukraine, Jordan, and Taiwan choices generally preserve or authorize the bounded assistance at issue, while the accepted Israel choice supports a specific $3.3 billion FMF reduction; that country-specific contrast prevents a uniform cross-country conclusion.",
        ),
        replacement(
            ["relationship_rationale"],
            candidate["relationship_rationale"],
            "The accepted semantic content—not proposition-relative direction labels—shows assistance-preserving or authorizing choices for Ukraine, Jordan, and Taiwan and a specific Israel FMF reduction choice. The contrast supports an interpretive boundary rather than a general pro-aid or anti-aid conclusion.",
        ),
        replacement(
            ["material_limitations"],
            candidate["material_limitations"],
            revised_limitations,
        ),
        replacement(
            ["why_synthesis_not_topic_grouping"],
            candidate["why_synthesis_not_topic_grouping"],
            "The relationship is an explicit interpretive boundary grounded in the accepted semantic effects of four country-specific assistance propositions, not topic similarity or direction metadata alone.",
        ),
    ]
    draft = {"field_replacements": replacements}
    revised = deepcopy(candidate)
    for row in replacements:
        cursor = revised
        for key in row["path"][:-1]:
            cursor = cursor[key]
        cursor[row["path"][-1]] = deepcopy(row["revised_value"])
    draft["revised_candidate_content_sha256"] = digest(revised)
    draft["revision_scope"] = "exact_human_bounded_semantic_wording_revision"
    return draft


def build_authority(
    package: dict[str, Any], template: dict[str, Any]
) -> dict[str, Any]:
    by_id = {
        row["synthesis_candidate_id"]: row
        for row in package["subject"]["synthesis_candidates"]
    }
    decisions = []
    for candidate_id in (WAR_POWERS_ID, ASSISTANCE_ID):
        candidate = by_id[candidate_id]
        decision = (
            "accept_candidate_as_written"
            if candidate_id == WAR_POWERS_ID
            else "accept_with_bounded_revision"
        )
        decisions.append(
            seal(
                {
                    "synthesis_candidate_id": candidate_id,
                    "original_candidate_subject_sha256": candidate[
                        "synthesis_candidate_subject_sha256"
                    ],
                    "original_candidate_content_sha256": digest(candidate),
                    "decision": decision,
                    "bounded_revision": None
                    if candidate_id == WAR_POWERS_ID
                    else assistance_revision(candidate),
                    "reviewer_id": REVIEWER_ID,
                    "reviewer_authority": REVIEWER_AUTHORITY,
                    "decision_timestamp": DECISION_TIMESTAMP,
                },
                "decision_subject_sha256",
            )
        )
    authority = seal(
        {
            "schema_version": "full_record_synthesis_authority_v1",
            "artifact_id": AUTHORITY_ID,
            "artifact_role": "immutable_human_full_record_synthesis_authority",
            "subject": {
                "subject": {
                    "member_name": "Valerie Foushee",
                    "member_id": "F000477",
                    "legislator_id": "leg_valerie_p_foushee",
                    "chamber": "house",
                    "congress": 119,
                    "issue_id": "NATIONAL_SECURITY_FOREIGN",
                },
                "authority_decision": {
                    "reviewer_id": REVIEWER_ID,
                    "reviewer_authority": REVIEWER_AUTHORITY,
                    "decision": "approve_complete_full_record_synthesis_as_reviewed",
                    "decision_timestamp": DECISION_TIMESTAMP,
                },
                **bindings(),
                "synthesis_decisions": decisions,
                "decision_accounting": {
                    "accept_candidate_as_written": 1,
                    "accept_with_bounded_revision": 1,
                    "rejected": 0,
                    "unresolved": 0,
                },
                "accepted_proposition_role_accounting": deepcopy(
                    package["subject"]["complete_proposition_accounting"]
                ),
                "accepted_episode_disposition_accounting": deepcopy(
                    package["subject"]["episode_disposition_accounting"]
                ),
                "authority_effect": "canonical_internal_synthesis_only",
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
            "accepted": True,
            "immutable": True,
            "canonical_internal_synthesis_authority": True,
            "public": False,
            "production_selectable": False,
            "authorizing": True,
        },
        "authority_subject_sha256",
    )
    validate_authority(authority, package=package, decision_template=template)
    return authority


def build_implementation(
    package: dict[str, Any],
    template: dict[str, Any],
    authority: dict[str, Any],
    m11h_authority: dict[str, Any],
    m11h_implementation: dict[str, Any],
) -> dict[str, Any]:
    decisions = {
        row["synthesis_candidate_id"]: row
        for row in authority["subject"]["synthesis_decisions"]
    }
    source_records = {
        row["proposition_id"]: row
        for row in m11h_implementation["subject"]["implementation_records"]
    }
    records = []
    observed_episodes: list[str] = []
    observed_actions: list[str] = []
    observed_inputs: set[str] = set()
    for original in package["subject"]["synthesis_candidates"]:
        candidate_id = original["synthesis_candidate_id"]
        decision = decisions[candidate_id]
        implemented = apply_bounded_revision(original, decision["bounded_revision"])
        lineage = []
        for binding in original["input_bindings"]:
            source = source_records[binding["proposition_id"]]
            lineage.append(
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
        observed_episodes.extend(original["underlying_evidence"]["unique_episode_ids"])
        observed_actions.extend(original["underlying_evidence"]["unique_action_ids"])
        records.append(
            seal(
                {
                    "schema_version": "full_record_synthesis_implementation_record_v1",
                    "record_id": f"synthesis-decision-implementation:{candidate_id}:m11j:v1",
                    "synthesis_candidate_id": candidate_id,
                    "authority_decision_subject_sha256": decision[
                        "decision_subject_sha256"
                    ],
                    "decision": decision["decision"],
                    "original_candidate_content": deepcopy(original),
                    "original_candidate_content_sha256": digest(original),
                    "original_candidate_subject_sha256": original[
                        "synthesis_candidate_subject_sha256"
                    ],
                    "bounded_revision": deepcopy(decision["bounded_revision"]),
                    "implemented_synthesis_content": implemented,
                    "implemented_synthesis_content_sha256": digest(implemented),
                    "behavioral_proposition_lineage": lineage,
                    "underlying_evidence": deepcopy(original["underlying_evidence"]),
                    "source_direction_semantic_guard": {
                        "direction_metadata_role": "proposition_relative_structural_metadata",
                        "semantic_claim_basis": "accepted_behavioral_proposition_content",
                        "mixed_direction_alone_establishes_mixed_policy_orientation": False,
                        "accepted_input_content_sha256s": [
                            row["accepted_candidate_content_sha256"]
                            for row in original["input_bindings"]
                        ],
                    },
                    "canonical_internal_synthesis": True,
                    "public": False,
                    "production_selectable": False,
                    "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
                },
                "record_subject_sha256",
            )
        )
    standalone = [
        row
        for row in package["subject"]["complete_proposition_accounting"]
        if row["accounting_role"] == "intentionally_standalone_no_safe_synthesis"
    ]
    final_accounting = {
        "canonical_internal_synthesis_count": 2,
        "unique_behavioral_proposition_input_count": len(observed_inputs),
        "candidate_episode_reference_count": len(observed_episodes),
        "candidate_action_reference_count": len(observed_actions),
        "cross_candidate_episode_overlap_count": len(observed_episodes)
        - len(set(observed_episodes)),
        "cross_candidate_action_overlap_count": len(observed_actions)
        - len(set(observed_actions)),
        "standalone_proposition_count": len(standalone),
    }
    implementation = seal(
        {
            "schema_version": "full_record_synthesis_decision_implementation_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "artifact_role": "deterministic_human_synthesis_decision_implementation",
            "subject": {
                "subject": authority["subject"]["subject"],
                "authority_binding": {
                    "artifact_id": authority["artifact_id"],
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                },
                **bindings(),
                "implementation_records": records,
                "accepted_proposition_role_accounting": deepcopy(
                    package["subject"]["complete_proposition_accounting"]
                ),
                "accepted_episode_disposition_accounting": deepcopy(
                    package["subject"]["episode_disposition_accounting"]
                ),
                "candidate_overlap_accounting": deepcopy(
                    package["subject"]["candidate_overlap_accounting"]
                ),
                "final_accounting": final_accounting,
                "canonical_internal_synthesis_state": "human_authority_implementation_present_pending_final_mechanical_review",
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
            "accepted_human_decisions_implemented": True,
            "canonical_internal_synthesis": True,
            "mechanical_review_state": "pending_human_mechanical_review",
            "public": False,
            "production_selectable": False,
        },
        "implementation_subject_sha256",
    )
    validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        m11h_authority=m11h_authority,
        m11h_implementation=m11h_implementation,
    )
    return implementation


def dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    records = {
        row["synthesis_candidate_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    return f"""# M11J National Security Synthesis Acceptance V1

## Mechanical review gate

M11J implements two human-accepted canonical internal synthesis propositions.
It does not authorize public wording or any production effect.

## Exact binding

- Post-M11I main: `{POST_M11I_MERGE_MAIN}`
- Accepted M11I head: `{ACCEPTED_M11I_HEAD}`
- Authority subject: `{authority["authority_subject_sha256"]}`
- Implementation subject: `{implementation["implementation_subject_sha256"]}`

## Decisions

- `{WAR_POWERS_ID}`: accepted as written.
- `{ASSISTANCE_ID}`: accepted with the exact bounded human revision.

## Canonical internal synthesis

### War Powers

{records[WAR_POWERS_ID]["implemented_synthesis_content"]["proposition"]}

### Security assistance boundary

{records[ASSISTANCE_ID]["implemented_synthesis_content"]["proposition"]}

The assistance record preserves canonical `direction: mixed` as structural,
proposition-relative metadata. Its semantic claim is based on the accepted
Behavioral Semantic IR content, not that direction field alone.

## Accounting and boundary

- Decisions: 1 accepted as written; 1 accepted with bounded revision.
- Behavioral proposition inputs: 8 role uses across 8 unique propositions.
- Underlying accepted episode/action references: 18/18, with zero cross-candidate overlap.
- Seven Behavioral Semantic IR propositions remain intentionally standalone.
- Public wording, publication, persistence, database/production writes, and deployment remain false.
"""


def build(*, check: bool = False, schemas_only: bool = False) -> dict[str, Any]:
    package, template, m11h_authority, m11h_implementation = preflight()
    authority = build_authority(package, template)
    implementation = build_implementation(
        package, template, authority, m11h_authority, m11h_implementation
    )
    authority_schema = schema(
        authority,
        "https://politicalfingerprint.org/schemas/full_record_synthesis_authority_v1",
    )
    implementation_schema = schema(
        implementation,
        "https://politicalfingerprint.org/schemas/full_record_synthesis_decision_implementation_v1",
    )
    parity_subject = {
        "artifact_id": PARITY_ID,
        "authority_binding": {
            "artifact_id": authority["artifact_id"],
            "file_sha256": content_sha256(serialized(authority)),
            "authority_subject_sha256": authority["authority_subject_sha256"],
        },
        "implementation_binding": {
            "artifact_id": implementation["artifact_id"],
            "file_sha256": content_sha256(serialized(implementation)),
            "implementation_subject_sha256": implementation[
                "implementation_subject_sha256"
            ],
        },
        "upstream_candidate_subject_sha256": PACKAGE_SUBJECT_SHA256,
        "decision_accounting": authority["subject"]["decision_accounting"],
        "final_accounting": implementation["subject"]["final_accounting"],
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    # Canonical file digests are over parsed JSON, matching repository contracts.
    parity = seal(
        {
            "schema_version": "full_record_synthesis_implementation_parity_v1",
            **parity_subject,
        },
        "parity_subject_sha256",
    )
    parity_schema = schema(
        parity,
        "https://politicalfingerprint.org/schemas/full_record_synthesis_implementation_parity_v1",
    )
    outputs = {
        AUTHORITY_PATH: serialized(authority),
        IMPLEMENTATION_PATH: serialized(implementation),
        PARITY_PATH: serialized(parity),
        DOSSIER_PATH: dossier(authority, implementation),
        AUTHORITY_SCHEMA_PATH: serialized(authority_schema),
        IMPLEMENTATION_SCHEMA_PATH: serialized(implementation_schema),
        PARITY_SCHEMA_PATH: serialized(parity_schema),
    }
    if schemas_only:
        outputs = {
            AUTHORITY_SCHEMA_PATH: serialized(authority_schema),
            IMPLEMENTATION_SCHEMA_PATH: serialized(implementation_schema),
            PARITY_SCHEMA_PATH: serialized(parity_schema),
        }
    for path, content in outputs.items():
        write_or_check(path, content, check=check)
    Draft7Validator(authority_schema).validate(authority)
    Draft7Validator(implementation_schema).validate(implementation)
    Draft7Validator(parity_schema).validate(parity)
    return {
        "authority_id": AUTHORITY_ID,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_id": PARITY_ID,
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "decision_accounting": authority["subject"]["decision_accounting"],
        "final_accounting": implementation["subject"]["final_accounting"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--schemas-only", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            build(check=args.check, schemas_only=args.schemas_only),
            indent=2,
            sort_keys=True,
        )
    )
