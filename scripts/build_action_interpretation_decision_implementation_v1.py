"""Build the detached M3B-B delegated-decision implementation artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1"
)
V4_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v4"
)
SCHEMA_ROOT = DECISION_ROOT / "schemas"
AUTHORITY_PATH = (
    DECISION_ROOT / "f000477_justice_public_safety_119_authority_decisions_v1.json"
)
AUTHORITY_MARKDOWN_PATH = (
    DECISION_ROOT / "f000477_justice_public_safety_119_authority_decisions_v1.md"
)
PREPARATION_PATH = DECISION_ROOT / "decision_preparation_bundle.json"

AUTHORITY_ID = (
    "action-interpretation-authority-decisions:f000477:justice_public_safety:119:v1"
)
AUTHORITY_CONTENT_SHA256 = (
    "08c0c09580e86af21a09158193d296989017a0c2aa239b19be0794c9b677ff7f"
)
AUTHORITY_FILE_SHA256 = (
    "f1eededb0d3c8a895607eae1fe4e0f93734f80c5e6d1540c772756e7dfb60f35"
)
AUTHORITY_MARKDOWN_FILE_SHA256 = (
    "b10edc6da9c4bbc46adaa9dc621a83d44f8ef115964ec4f95ad469d1533089ea"
)
PREPARATION_CONTENT_SHA256 = (
    "56ecf9df6be92b70185efcd78a89465586d817b08fa9ecbe6ecd0685d0797d51"
)
V4_CONTENT_SHA256 = "72ea57109ab169deb88b308b54c5c31b9d1c781b1db1b49f6b73c980a7c2f403"
V4_FILE_SHA256 = "a3f6218a33f9ef4789242248e60ba31b41d2563a8c163409ef88be569454d445"
IMPLEMENTATION_ID = (
    "action-interpretation-decision-implementation:f000477:justice_public_safety:119:v1"
)
MAPPING_ID = (
    "delegated-editorial-authority-mapping:f000477:justice_public_safety:119:v1"
)
REVIEWER_IDENTITY = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "delegated_product_methodology_editorial_authority_v1"

OUTPUT_NAMES = (
    "decision_implementation_bundle.json",
    "delegated_authority_mapping.json",
    "launch_review_risk_register.json",
    "launch_calibration_population.json",
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(value: dict[str, Any]) -> dict[str, Any]:
    return {**value, "content_subject_sha256": digest(value)}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_or_check(path: Path, value: object, check: bool) -> None:
    if check:
        if (
            not path.exists()
            or (
                json.loads(path.read_text(encoding="utf-8"))
                if path.suffix == ".json"
                else path.read_text(encoding="utf-8")
            )
            != value
        ):
            raise ValueError(f"deterministic check failed: {path.relative_to(ROOT)}")
    elif path.suffix == ".json":
        write_json(path, value)
    else:
        path.write_text(str(value), encoding="utf-8")


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    if value.get("content_subject_sha256") != digest(subject):
        raise ValueError(f"{label} content-subject digest differs")


def preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if file_digest(AUTHORITY_PATH) != AUTHORITY_FILE_SHA256:
        raise ValueError("authority final bytes differ")
    if file_digest(AUTHORITY_MARKDOWN_PATH) != AUTHORITY_MARKDOWN_FILE_SHA256:
        raise ValueError("authority companion Markdown final bytes differ")
    authority = load(AUTHORITY_PATH)
    verify_seal(authority, "authority")
    if (
        authority["artifact_id"] != AUTHORITY_ID
        or authority["content_subject_sha256"] != AUTHORITY_CONTENT_SHA256
    ):
        raise ValueError("authority identity differs")
    if authority["authority"] != {
        "decision_timestamp": "2026-08-02T11:35:00-04:00",
        "delegation_basis": "User explicitly designated this ChatGPT thread as continuous product, methodology, editorial, authorization, and acceptance authority for Political Fingerprint.",
        "not_user_signature": True,
        "reviewer_authority": REVIEWER_AUTHORITY,
        "reviewer_identity": REVIEWER_IDENTITY,
    }:
        raise ValueError("delegated authority identity or boundary differs")
    if authority["decision_accounting"] != {
        "accept_candidate": 32,
        "accept_with_required_revision": 2,
        "preserve_ambiguous": 2,
        "preserve_no_safe_candidate": 1,
    }:
        raise ValueError("authority decision accounting differs")
    if any(
        authority["authorization"][key]
        for key in (
            "canonical_semantic_acceptance",
            "policy_episode_construction",
            "semantic_ir_compilation",
            "synthesis",
            "production_persistence",
            "publication",
            "push",
            "pull_request",
            "merge",
            "deployment",
        )
    ):
        raise ValueError("authority grants prohibited downstream or delivery authority")
    preparation = load(PREPARATION_PATH)
    verify_seal(preparation, "decision preparation")
    if preparation["content_subject_sha256"] != PREPARATION_CONTENT_SHA256:
        raise ValueError("M3B-A decision preparation differs")
    v4_path = V4_ROOT / "candidate_batch.json"
    v4 = load(v4_path)
    verify_seal(v4, "V4 candidate batch")
    if (
        v4["content_subject_sha256"] != V4_CONTENT_SHA256
        or file_digest(v4_path) != V4_FILE_SHA256
    ):
        raise ValueError("V4 candidate identity differs")
    return authority, preparation, v4


STATE_BY_DECISION = {
    "accept_candidate": "implemented_accepted_candidate",
    "accept_with_required_revision": "implemented_accepted_with_revision",
    "preserve_ambiguous": "implemented_preserved_ambiguous",
    "preserve_no_safe_candidate": "implemented_preserved_no_safe_candidate",
}


def implementation_records(
    authority: dict[str, Any], preparation: dict[str, Any], v4: dict[str, Any]
) -> list[dict[str, Any]]:
    units = {row["action_id"]: row for row in preparation["decision_units"]}
    candidates = {row["action_id"]: row for row in v4["final_candidates"]}
    records = []
    for decision in sorted(authority["decisions"], key=lambda row: row["action_id"]):
        action_id = decision["action_id"]
        unit, candidate = units[action_id], candidates[action_id]
        if (
            decision["candidate_id"] != candidate["candidate_id"]
            or decision["candidate_content_subject_sha256"]
            != candidate["candidate_content_subject_sha256"]
        ):
            raise ValueError(f"{action_id}: authority-to-V4 binding differs")
        if (
            decision["decision_unit_content_subject_sha256"]
            != unit["content_subject_sha256"]
        ):
            raise ValueError(f"{action_id}: authority-to-M3B-A binding differs")
        selected = decision["selected_decision"]
        if selected not in STATE_BY_DECISION:
            raise ValueError(f"{action_id}: decision is not implementation-authorized")
        record = seal(
            {
                "schema_version": "action_interpretation_decision_implementation_record_v1",
                "record_id": f"action-interpretation-decision-implementation:{action_id}:v1",
                "action_id": action_id,
                "exact_action_identity": unit["exact_action_identity"],
                "official_member_action": unit["official_member_action"],
                "house_stage": unit["house_stage"],
                "candidate_id": candidate["candidate_id"],
                "candidate_content_subject_sha256": candidate[
                    "candidate_content_subject_sha256"
                ],
                "candidate_status": candidate["status"],
                "candidate_exact_action_meaning": candidate[
                    "proposed_exact_action_meaning"
                ],
                "candidate_exact_choice_position_effect": candidate[
                    "proposed_member_position_effect"
                ],
                "decision_unit_id": unit["decision_unit_id"],
                "decision_unit_content_subject_sha256": unit["content_subject_sha256"],
                "authority_artifact_id": AUTHORITY_ID,
                "authority_artifact_content_subject_sha256": AUTHORITY_CONTENT_SHA256,
                "authority_decision_content_subject_sha256": decision[
                    "content_subject_sha256"
                ],
                "selected_decision": selected,
                "implementation_state": STATE_BY_DECISION[selected],
                "implemented_interpretation_status": "ambiguous"
                if selected == "preserve_ambiguous"
                else "no_safe_candidate"
                if selected == "preserve_no_safe_candidate"
                else "internally_implemented",
                "implemented_exact_action_meaning": decision[
                    "accepted_exact_action_meaning"
                ],
                "implemented_exact_choice_position_effect": decision[
                    "accepted_exact_choice_position_effect"
                ],
                "implemented_confidence": decision["confidence_decision"],
                "implemented_limitations": decision["accepted_limitations"],
                "implemented_competing_interpretation": decision[
                    "accepted_competing_interpretation"
                ],
                "unresolved_question": decision["unresolved_question"],
                "required_wording_or_field_revisions": decision[
                    "required_wording_or_field_revisions"
                ],
                "secondary_detail_decisions": decision["secondary_detail_decisions"],
                "source_references": unit["source_references"],
                "evidence_map_id": unit["evidence_map_id"],
                "evidence_map_content_subject_sha256": unit[
                    "evidence_map_content_subject_sha256"
                ],
                "related_action_contrast_groups": unit["sample_memberships"][
                    "contrast_groups"
                ],
                "cross_domain_limitations": candidate["cross_domain_limitations"],
                "delegated_editorial_acceptance_state": "delegated_editorial_acceptance_pending",
                "launch_ratification_state": "launch_ratification_pending",
                "canonical": False,
                "public": False,
                "publication_authorized": False,
            }
        )
        records.append(record)
    return records


def authority_mapping(authority: dict[str, Any]) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "delegated_editorial_authority_mapping_v1",
            "artifact_id": MAPPING_ID,
            "authority_record": {
                "artifact_id": AUTHORITY_ID,
                "path": AUTHORITY_PATH.relative_to(ROOT).as_posix(),
                "content_subject_sha256": AUTHORITY_CONTENT_SHA256,
                "final_file_sha256": AUTHORITY_FILE_SHA256,
                "immutable": True,
                "legacy_decision_record_status": authority["decision_record_status"],
            },
            "delegated_decision_maker": {
                "reviewer_identity": REVIEWER_IDENTITY,
                "reviewer_authority": REVIEWER_AUTHORITY,
            },
            "not_user_signature": True,
            "decision_state": "delegated_editorial_decisions_recorded",
            "implementation_state": "implementation_pending_delegated_authority_acceptance",
            "delegated_editorial_acceptance_state": "delegated_editorial_acceptance_pending",
            "launch_ratification_state": "launch_ratification_pending",
            "authorized_scope": {
                "internal_decision_implementation": True,
                "action_count": 37,
            },
            "unauthorized_scope": {
                "canonical_semantic_acceptance": True,
                "publication": True,
                "production_persistence": True,
                "deployment": True,
            },
            "publication_authorized": False,
        }
    )


RISK_SPECS = {
    "house:119:1:27": (
        "material_compression",
        "Does the concise public meaning surface the general five-year maximum without overstating the separate civil remedy?",
        "resolved_internal",
    ),
    "house:119:1:128": (
        "unresolved_statutory_context",
        "What is the exact legal effect of inserting `any magazine and` into the two LEOSA provisions?",
        "retained_ambiguous",
    ),
    "house:119:2:155": (
        "unresolved_source_conflict",
        "Which Congress metadata governs the source that identifies both the 110th and 119th Congresses?",
        "retained_ambiguous",
    ),
    "house:119:2:157": (
        "material_compression",
        "Does the concise public meaning make the coordination center's seven-year sunset visible?",
        "resolved_internal",
    ),
    "house:119:2:218": (
        "material_scope_boundary",
        "Could omission of the funding and covered-award thresholds materially overstate H.R. 8312's scope?",
        "resolved_internal",
    ),
    "house:119:2:240": (
        "material_process_boundary",
        "Could omission of the complaint-process and cure deadlines materially overstate immediate enforceability?",
        "resolved_internal",
    ),
    "house:119:2:278": (
        "incomplete_governed_evidence",
        "What complete final House-passed package did the vote adopt?",
        "retained_no_safe",
    ),
}


def risk_register(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["action_id"]: row for row in records}
    entries = []
    for action_id, (risk_class, question, status) in RISK_SPECS.items():
        row = by_id[action_id]
        competing = (
            [row["implemented_competing_interpretation"]]
            if row["implemented_competing_interpretation"]
            else []
        )
        entries.append(
            seal(
                {
                    "risk_id": f"launch-risk:{action_id}:v1",
                    "subject": {"subject_type": "action", "action_id": action_id},
                    "risk_class": risk_class,
                    "exact_unresolved_question": row["unresolved_question"] or question,
                    "governed_evidence": {
                        "source_references": row["source_references"],
                        "evidence_map_id": row["evidence_map_id"],
                        "evidence_map_content_subject_sha256": row[
                            "evidence_map_content_subject_sha256"
                        ],
                        "authority_decision_content_subject_sha256": row[
                            "authority_decision_content_subject_sha256"
                        ],
                    },
                    "strongest_competing_interpretations": competing,
                    "codex_recommendation": "Preserve the delegated decision and its explicit boundary; do not infer beyond the governed evidence.",
                    "delegated_authority_disposition": row["selected_decision"],
                    "likely_public_output_consequence": "Later public-language work must carry this boundary or omit the unsupported meaning.",
                    "current_status": status,
                    "resolution_history": [
                        {
                            "stage": "M3B-B",
                            "disposition": row["selected_decision"],
                            "authority": REVIEWER_AUTHORITY,
                        }
                    ],
                    "downstream_artifacts_affected": [
                        "policy_episode_candidates",
                        "semantic_ir_candidates",
                        "public_language_candidates",
                        "launch_review_packet",
                    ],
                }
            )
        )
    counts = dict(sorted(Counter(row["current_status"] for row in entries).items()))
    return seal(
        {
            "schema_version": "launch_review_risk_register_v1",
            "artifact_id": "launch-review-risk-register:f000477:justice_public_safety:119:v1",
            "cumulative": True,
            "entry_count": len(entries),
            "status_counts": counts,
            "entries": entries,
            "carry_forward_required": True,
            "canonical": False,
            "public": False,
        }
    )


def calibration_population(
    records: list[dict[str, Any]], risk: dict[str, Any]
) -> dict[str, Any]:
    held = {
        row["subject"]["action_id"]
        for row in risk["entries"]
        if row["current_status"] != "resolved_internal"
    }
    eligible = []
    for row in records:
        if row["action_id"] in held or row["selected_decision"] not in {
            "accept_candidate",
            "accept_with_required_revision",
        }:
            continue
        eligible.append(
            seal(
                {
                    "eligibility_id": f"launch-calibration-eligible:{row['action_id']}:v1",
                    "action_id": row["action_id"],
                    "implementation_record_content_subject_sha256": row[
                        "content_subject_sha256"
                    ],
                    "house_stage": row["house_stage"],
                    "mechanism_complexity": "complex"
                    if len(row["source_references"]) > 2
                    or len(row["implemented_limitations"]) > 1
                    else "simple",
                    "confidence": row["implemented_confidence"],
                    "related_action_case": bool(row["related_action_contrast_groups"]),
                    "cross_domain_case": bool(row["cross_domain_limitations"]),
                    "not_held_for_launch_review": True,
                }
            )
        )
    return seal(
        {
            "schema_version": "launch_calibration_eligibility_population_v1",
            "artifact_id": "launch-calibration-eligibility:f000477:justice_public_safety:119:v1",
            "eligibility_rule": "Internally implemented accepted or revised actions not retained for launch review.",
            "eligible_count": len(eligible),
            "eligible_items": eligible,
            "sample_selected": False,
            "selected_sample": [],
            "sample_selection_deferred_until": "final_public_interface_candidate_bundle_frozen",
            "future_seed_inputs": [
                "final_public_interface_bundle_content_subject_sha256",
                "final_risk_register_content_subject_sha256",
                "political_fingerprint_launch_calibration_audit_v1",
            ],
            "canonical": False,
            "public": False,
        }
    )


def inferred_schema(examples: list[object]) -> dict[str, Any]:
    nonnull = [value for value in examples if value is not None]
    nullable = len(nonnull) != len(examples)
    if not nonnull:
        return {"type": "null"}
    if all(isinstance(value, dict) for value in nonnull):
        keys = sorted({key for value in nonnull for key in value})
        schema: dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "required": [key for key in keys if all(key in value for value in nonnull)],
            "properties": {
                key: inferred_schema([value[key] for value in nonnull if key in value])
                for key in keys
            },
        }
    elif all(isinstance(value, list) for value in nonnull):
        children = [child for value in nonnull for child in value]
        schema = {
            "type": "array",
            "items": inferred_schema(children) if children else {},
        }
    else:
        types = []
        for value in nonnull:
            kind = (
                "boolean"
                if isinstance(value, bool)
                else "integer"
                if isinstance(value, int)
                else "number"
                if isinstance(value, float)
                else "string"
            )
            if kind not in types:
                types.append(kind)
        schema = {"type": types[0] if len(types) == 1 else types}
    if nullable and schema.get("type") != "null":
        schema["type"] = (
            [schema["type"], "null"]
            if isinstance(schema["type"], str)
            else [*schema["type"], "null"]
        )
    return schema


def dossier(
    bundle: dict[str, Any],
    mapping: dict[str, Any],
    risk: dict[str, Any],
    calibration: dict[str, Any],
) -> str:
    lines = [
        "# Foushee Justice 119th-Congress Decision Implementation V1",
        "",
        f"- Implementation bundle: `{bundle['artifact_id']}`",
        f"- Authority: `{AUTHORITY_ID}`",
        f"- Authority content-subject SHA-256: `{AUTHORITY_CONTENT_SHA256}`",
        f"- Authority final-file SHA-256: `{AUTHORITY_FILE_SHA256}`",
        f"- Reviewer identity: `{REVIEWER_IDENTITY}`",
        f"- Reviewer authority: `{REVIEWER_AUTHORITY}`",
        "- `not_user_signature`: `true`",
        "- Delegated editorial acceptance: `delegated_editorial_acceptance_pending`",
        "- Launch ratification: `launch_ratification_pending`",
        "- Canonical/public/publication authority: `false`",
        "",
        "## Accounting",
        "",
        f"`{json.dumps(bundle['implementation_accounting'], sort_keys=True)}`",
        f"- Accepted limitations: `{bundle['accepted_limitation_count']}`",
        f"- Secondary-detail decisions: `{bundle['secondary_detail_decision_count']}` / `{json.dumps(bundle['secondary_detail_decision_accounting'], sort_keys=True)}`",
        "",
        "## Implemented actions",
        "",
    ]
    for row in bundle["implementation_records"]:
        changed = (
            row["candidate_exact_action_meaning"]
            != row["implemented_exact_action_meaning"]
        )
        lines += [
            f"### `{row['action_id']}`",
            "",
            f"- Decision: `{row['selected_decision']}`",
            f"- State: `{row['implementation_state']}`",
            f"- Confidence: `{row['implemented_confidence']}`",
            f"- Field-level meaning difference: `{'authorized_revision' if changed else 'none'}`",
            "",
            "**V4 candidate meaning**",
            "",
            str(row["candidate_exact_action_meaning"]),
            "",
            "**Implemented meaning**",
            "",
            str(row["implemented_exact_action_meaning"]),
            "",
            f"- Exact-choice effect: `{row['implemented_exact_choice_position_effect']}`",
            f"- Limitations: `{json.dumps(row['implemented_limitations'], ensure_ascii=False)}`",
            f"- Competing interpretation: `{row['implemented_competing_interpretation']}`",
            f"- Unresolved question: `{row['unresolved_question']}`",
            f"- Secondary-detail decisions: `{json.dumps(row['secondary_detail_decisions'], ensure_ascii=False)}`",
            f"- Record content-subject SHA-256: `{row['content_subject_sha256']}`",
            "",
        ]
    lines += [
        "## Launch-review continuity",
        "",
        f"- Risk-register entries: `{risk['entry_count']}`; status counts: `{json.dumps(risk['status_counts'], sort_keys=True)}`",
        f"- Calibration eligibility population: `{calibration['eligible_count']}`; sample selected: `false`",
        "",
        "## Provenance",
        "",
        f"- V4 content-subject SHA-256: `{V4_CONTENT_SHA256}`",
        f"- M3B-A content-subject SHA-256: `{PREPARATION_CONTENT_SHA256}`",
        f"- Successor mapping: `{mapping['artifact_id']}` / `{mapping['content_subject_sha256']}`",
        "",
        "## Exact decision requested",
        "",
        "- `delegated_authority_accepts_implementation`",
        "- `bounded_implementation_correction_required`",
        "- `delegated_authority_rejects_implementation`",
        "",
    ]
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    authority, preparation, v4 = preflight()
    records = implementation_records(authority, preparation, v4)
    accounting = dict(
        sorted(Counter(row["implementation_state"] for row in records).items())
    )
    secondary_accounting = dict(
        sorted(
            Counter(
                detail["decision"]
                for row in records
                for detail in row["secondary_detail_decisions"]
            ).items()
        )
    )
    bundle = seal(
        {
            "schema_version": "action_interpretation_decision_implementation_bundle_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "subject": authority["subject"],
            "input_bindings": {
                "m1": authority["input_bindings"]["m1"],
                "m2": authority["input_bindings"]["m2"],
                "v4_candidate_batch": authority["input_bindings"]["v4_candidate_batch"],
                "m3b_a_decision_preparation": authority["input_bindings"][
                    "decision_preparation_bundle"
                ],
                "authority_record": {
                    "artifact_id": AUTHORITY_ID,
                    "content_subject_sha256": AUTHORITY_CONTENT_SHA256,
                    "final_file_sha256": AUTHORITY_FILE_SHA256,
                },
            },
            "implementation_record_count": len(records),
            "implementation_records": records,
            "implementation_accounting": accounting,
            "accepted_limitation_count": sum(
                len(row["implemented_limitations"]) for row in records
            ),
            "secondary_detail_decision_count": sum(
                len(row["secondary_detail_decisions"]) for row in records
            ),
            "secondary_detail_decision_accounting": secondary_accounting,
            "decision_state": "delegated_editorial_decisions_recorded",
            "implementation_state": "implementation_pending_delegated_authority_acceptance",
            "delegated_editorial_acceptance_state": "delegated_editorial_acceptance_pending",
            "launch_ratification_state": "launch_ratification_pending",
            "canonical": False,
            "public": False,
            "episode_authorized": False,
            "semantic_ir_authorized": False,
            "synthesis_authorized": False,
            "persistence_authorized": False,
            "publication_authorized": False,
        }
    )
    mapping = authority_mapping(authority)
    risk = risk_register(records)
    calibration = calibration_population(records, risk)
    artifacts = {
        "decision_implementation_bundle.json": bundle,
        "delegated_authority_mapping.json": mapping,
        "launch_review_risk_register.json": risk,
        "launch_calibration_population.json": calibration,
    }
    for name, value in artifacts.items():
        write_or_check(DECISION_ROOT / name, value, check)
    schemas = {"authority_decisions_v1.schema.json": inferred_schema([authority])}
    for name, value in artifacts.items():
        schemas[name.replace(".json", "_v1.schema.json")] = inferred_schema([value])
    for name, schema in schemas.items():
        write_or_check(
            SCHEMA_ROOT / name,
            {"$schema": "http://json-schema.org/draft-07/schema#", **schema},
            check,
        )
    markdown = dossier(bundle, mapping, risk, calibration)
    dossier_path = DECISION_ROOT / "decision_implementation_dossier.md"
    write_or_check(dossier_path, markdown, check)
    referenced = []
    schema_paths = [
        SCHEMA_ROOT / "authority_decisions_v1.schema.json",
        SCHEMA_ROOT / "decision_implementation_bundle_v1.schema.json",
        SCHEMA_ROOT / "delegated_authority_mapping_v1.schema.json",
        SCHEMA_ROOT / "launch_review_risk_register_v1.schema.json",
        SCHEMA_ROOT / "launch_calibration_population_v1.schema.json",
    ]
    for path in [
        *(DECISION_ROOT / name for name in OUTPUT_NAMES),
        *schema_paths,
        dossier_path,
    ]:
        if path.exists():
            item = {
                "path": path.relative_to(ROOT).as_posix(),
                "final_file_sha256": file_digest(path),
            }
            if path.suffix == ".json" and "schema" not in path.name:
                item["content_subject_sha256"] = load(path)["content_subject_sha256"]
            referenced.append(item)
    parity = seal(
        {
            "schema_version": "action_interpretation_decision_implementation_parity_v1",
            "artifact_id": "action-interpretation-decision-implementation-parity:f000477:justice_public_safety:119:v1",
            "generated_last": True,
            "parity_state": "pass",
            "implementation_bundle_content_subject_sha256": bundle[
                "content_subject_sha256"
            ],
            "imported_authority": {
                "json_path": AUTHORITY_PATH.relative_to(ROOT).as_posix(),
                "content_subject_sha256": AUTHORITY_CONTENT_SHA256,
                "final_file_sha256": AUTHORITY_FILE_SHA256,
                "companion_markdown_path": AUTHORITY_MARKDOWN_PATH.relative_to(
                    ROOT
                ).as_posix(),
                "companion_markdown_final_file_sha256": AUTHORITY_MARKDOWN_FILE_SHA256,
            },
            "referenced_artifacts": referenced,
            "referenced_file_count": len(referenced),
            "json_markdown_semantic_parity": True,
            "all_final_file_sha256_recomputed": True,
        }
    )
    parity_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        **inferred_schema([parity]),
    }
    write_or_check(
        SCHEMA_ROOT / "implementation_parity_manifest_v1.schema.json",
        parity_schema,
        check,
    )
    write_or_check(DECISION_ROOT / "implementation_parity_manifest.json", parity, check)
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    bundle = build(check=args.check)
    print(
        json.dumps(
            {
                "status": "pass",
                "bundle_id": bundle["artifact_id"],
                "content_subject_sha256": bundle["content_subject_sha256"],
                "action_count": bundle["implementation_record_count"],
                "accounting": bundle["implementation_accounting"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
