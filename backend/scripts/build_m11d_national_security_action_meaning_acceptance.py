from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation_decisions import (  # noqa: E402
    ACCEPTED_DECISION,
    DOWNSTREAM_AUTHORIZATIONS,
    IMPLEMENTATION_STATE,
    build_authority_record,
    build_implementation_bundle,
    validate_authority_record,
    validate_implementation_bundle,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    load_json,
    sha256_json,
)


POST_M11C_MERGE_MAIN = "6b11a20b18d8e98df3ed5d63606f0e94e8ed47f1"
ACCEPTED_PR = 135
ACCEPTED_HEAD = "59ecdf805ca89ce01d8dc6eeb441542a9f68571f"
ACCEPTED_CANDIDATE_FILE_SHA256 = (
    "6d3c0c26d56b7ace999debbc45efc0945f27320425b0f2bda55aca013630543d"
)
ACCEPTED_CANDIDATE_SUBJECT_SHA256 = (
    "db88b7e4e5f180fa72f901132b56e8f41b975a5e12d102600b45a7df766ad840"
)
DECISION_TEMPLATE_FILE_SHA256 = (
    "445d9e1bc79828dfab8f9aff60d4cb2d78d6cb76ce77331e5f84f612361fa431"
)
DECISION_TEMPLATE_SUBJECT_SHA256 = (
    "da8862353cd5cc08a9f0438cb8c0d27d6e6379de3e2d81b2d703eace6b0fdd1c"
)
REVIEWER_IDENTITY = "dhart54"
REVIEWER_AUTHORITY = "full_record_action_interpretation_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-09T15:32:56Z"

CANDIDATE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates"
    / "f000477_national_security_foreign_119_v1"
)
CANDIDATE_PATH = CANDIDATE_ROOT / "candidate_batch.json"
DECISION_TEMPLATE_PATH = CANDIDATE_ROOT / "human_decision_template.json"
READINESS_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/source_readiness"
    / "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions"
    / "f000477_national_security_foreign_119_v1"
)
AUTHORITY_PATH = OUTPUT_ROOT / "human_action_meaning_authority.json"
IMPLEMENTATION_PATH = OUTPUT_ROOT / "decision_implementation_bundle.json"
DOSSIER_PATH = OUTPUT_ROOT / "decision_implementation_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "implementation_parity_manifest.json"

AUTHORITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_action_interpretation_authority_v1.schema.json"
)
IMPLEMENTATION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_action_interpretation_decision_implementation_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_action_interpretation_implementation_parity_v1.schema.json"
)

AUTHORITY_ID = (
    "human-action-interpretation-authority:f000477:national_security_foreign:119:v1"
)
IMPLEMENTATION_ID = (
    "action-interpretation-decision-implementation:f000477:"
    "national_security_foreign:119:v1"
)
PARITY_ID = (
    "action-interpretation-decision-implementation-parity:f000477:"
    "national_security_foreign:119:v1"
)


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def _file_sha256(content: bytes) -> str:
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def _sha_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": "^[0-9a-f]{64}$"}


def _git_sha_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": "^[0-9a-f]{40}$"}


def _downstream_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(DOWNSTREAM_AUTHORIZATIONS),
        "properties": {key: {"const": False} for key in DOWNSTREAM_AUTHORIZATIONS},
    }


def authority_schema() -> dict[str, Any]:
    decision_properties = {
        "action_id": {
            "type": "string",
            "pattern": "^house:[0-9]+:[0-9]+:[0-9]+$",
        },
        "candidate_id": {"type": "string", "minLength": 1},
        "candidate_content_subject_sha256": _sha_schema(),
        "decision": {"const": ACCEPTED_DECISION},
        "accepted_exact_action_meaning": {"type": "string", "minLength": 1},
        "accepted_exact_choice_position_effect": {
            "enum": [
                "supports_exact_choice",
                "opposes_exact_choice",
                "non_directional_present",
                "non_directional_not_voting",
            ]
        },
        "accepted_confidence": {"enum": ["high", "medium", "low"]},
        "accepted_limitations": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
        "accepted_coverage_assessment": {
            "enum": [
                "bounded_official_purpose_summary",
                "package_level_bounded_summary",
            ]
        },
        "accepted_source_references": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
        "accepted_evidence_map_id": {"type": "string", "minLength": 1},
        "accepted_evidence_map_subject_sha256": _sha_schema(),
        "decision_subject_sha256": _sha_schema(),
    }
    blocked_properties = {
        "action_id": {"type": "string"},
        "disposition": {"const": "source_blocked_not_interpreted"},
        "readiness_state": {"type": "string"},
        "source_packet_sha256": _sha_schema(),
        "accepted_for_interpretation": {"const": False},
    }
    subject_properties = {
        "member_id": {"type": "string", "minLength": 1},
        "legislator_id": {"type": "string", "minLength": 1},
        "issue_id": {"type": "string", "minLength": 1},
        "congress": {"type": "integer", "minimum": 1},
        "official_cutoff": {"type": "object"},
        "authority_decision": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "reviewer_identity",
                "reviewer_authority",
                "decision",
                "decision_timestamp",
            ],
            "properties": {
                "reviewer_identity": {"type": "string", "minLength": 1},
                "reviewer_authority": {"const": REVIEWER_AUTHORITY},
                "decision": {
                    "const": "approved_all_candidate_meanings_and_position_effects"
                },
                "decision_timestamp": {"type": "string", "format": "date-time"},
            },
        },
        "input_bindings": {"type": "object"},
        "approved_universe_count": {"type": "integer", "minimum": 0},
        "accepted_decision_count": {"type": "integer", "minimum": 0},
        "source_blocked_count": {"type": "integer", "minimum": 0},
        "action_ids": {
            "type": "array",
            "uniqueItems": True,
            "items": {"type": "string"},
        },
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": list(decision_properties),
                "properties": decision_properties,
            },
        },
        "source_blocked_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": list(blocked_properties),
                "properties": blocked_properties,
            },
        },
        "decision_accounting": {
            "type": "object",
            "additionalProperties": False,
            "required": [ACCEPTED_DECISION],
            "properties": {ACCEPTED_DECISION: {"type": "integer", "minimum": 0}},
        },
        "internal_action_interpretation_state": {"const": "human_accepted_internal"},
        "internal_action_meanings_canonical": {"const": True},
        "canonical_semantic_acceptance": {"const": False},
        "presentation_boundary": {"type": "string", "minLength": 1},
        "downstream_authorizations": _downstream_schema(),
    }
    properties = {
        "schema_version": {"const": "full_record_action_interpretation_authority_v1"},
        "artifact_id": {"type": "string", "minLength": 1},
        "artifact_role": {"const": "immutable_human_action_interpretation_authority"},
        "accepted": {"const": True},
        "immutable": {"const": True},
        "canonical_internal_action_interpretation_authority": {"const": True},
        "canonical_semantic_acceptance": {"const": False},
        "public": {"const": False},
        "publication_authorized": {"const": False},
        "production_selectable": {"const": False},
        "subject": {
            "type": "object",
            "additionalProperties": False,
            "required": list(subject_properties),
            "properties": subject_properties,
        },
        "authority_subject_sha256": _sha_schema(),
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Full-Record Action Interpretation Human Authority V1",
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def implementation_schema() -> dict[str, Any]:
    record_properties = {
        "action_id": {"type": "string"},
        "record_id": {"type": "string"},
        "candidate_id": {"type": "string"},
        "candidate_content_subject_sha256": _sha_schema(),
        "authority_artifact_id": {"type": "string", "minLength": 1},
        "authority_subject_sha256": _sha_schema(),
        "authority_file_sha256": _sha_schema(),
        "authority_decision_subject_sha256": _sha_schema(),
        "implementation_state": {"const": IMPLEMENTATION_STATE},
        "accepted_exact_action_meaning": {"type": "string", "minLength": 1},
        "accepted_exact_choice_position_effect": {
            "enum": [
                "supports_exact_choice",
                "opposes_exact_choice",
                "non_directional_present",
                "non_directional_not_voting",
            ]
        },
        "accepted_confidence": {"enum": ["high", "medium", "low"]},
        "accepted_limitations": {"type": "array", "items": {"type": "string"}},
        "accepted_coverage_assessment": {
            "enum": [
                "bounded_official_purpose_summary",
                "package_level_bounded_summary",
            ]
        },
        "source_references": {"type": "array", "items": {"type": "string"}},
        "evidence_map_id": {"type": "string"},
        "evidence_map_subject_sha256": _sha_schema(),
        "canonical_internal_action_interpretation": {"const": True},
        "canonical_semantic_acceptance": {"const": False},
        "public": {"const": False},
        "publication_authorized": {"const": False},
        "presentation_state": {"const": "internal_evidence_backed_semantic_input"},
        "downstream_authorizations": _downstream_schema(),
        "record_subject_sha256": _sha_schema(),
    }
    subject_properties = {
        "member_id": {"type": "string", "minLength": 1},
        "legislator_id": {"type": "string", "minLength": 1},
        "issue_id": {"type": "string", "minLength": 1},
        "congress": {"type": "integer", "minimum": 1},
        "official_cutoff": {"type": "object"},
        "input_bindings": {"type": "object"},
        "implementation_record_count": {"type": "integer", "minimum": 0},
        "implementation_records": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": list(record_properties),
                "properties": record_properties,
            },
        },
        "implementation_accounting": {
            "type": "object",
            "additionalProperties": False,
            "required": [IMPLEMENTATION_STATE],
            "properties": {IMPLEMENTATION_STATE: {"type": "integer", "minimum": 0}},
        },
        "source_blocked_actions": {"type": "array"},
        "source_blocked_count": {"type": "integer", "minimum": 0},
        "internal_action_interpretation_state": {"const": "human_accepted_internal"},
        "internal_action_meanings_canonical": {"const": True},
        "canonical_semantic_acceptance": {"const": False},
        "mechanical_review_state": {"const": "pending_human_review"},
        "policy_episode_state": {"const": "not_started_not_authorized"},
        "downstream_authorizations": _downstream_schema(),
    }
    properties = {
        "schema_version": {
            "const": "full_record_action_interpretation_decision_implementation_v1"
        },
        "artifact_id": {"type": "string", "minLength": 1},
        "artifact_role": {
            "const": "detached_human_accepted_action_interpretation_implementation"
        },
        "accepted_human_decisions_implemented": {"const": True},
        "canonical_internal_action_interpretation": {"const": True},
        "canonical_semantic_acceptance": {"const": False},
        "public": {"const": False},
        "publication_authorized": {"const": False},
        "production_selectable": {"const": False},
        "subject": {
            "type": "object",
            "additionalProperties": False,
            "required": list(subject_properties),
            "properties": subject_properties,
        },
        "implementation_subject_sha256": _sha_schema(),
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Full-Record Action Interpretation Decision Implementation V1",
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def parity_schema() -> dict[str, Any]:
    properties = {
        "schema_version": {
            "const": "full_record_action_interpretation_implementation_parity_v1"
        },
        "artifact_id": {"type": "string", "minLength": 1},
        "generated_last": {"const": True},
        "parity_state": {"const": "pass"},
        "accepted_candidate_binding": {"type": "object"},
        "generated_artifacts": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "file_sha256"],
                "properties": {
                    "path": {"type": "string"},
                    "file_sha256": _sha_schema(),
                    "content_subject_sha256": _sha_schema(),
                },
            },
        },
        "decision_count": {"type": "integer", "minimum": 0},
        "source_blocked_count": {"type": "integer", "minimum": 0},
        "downstream_authorizations": _downstream_schema(),
        "parity_subject_sha256": _sha_schema(),
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Full-Record Action Interpretation Implementation Parity V1",
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    subject = implementation["subject"]
    lines = [
        "# M11D National Security Action-Meaning Acceptance Review",
        "",
        "Status: 81 human-accepted action meanings and exact-choice effects are "
        "implemented as internal canonical action interpretations; mechanical review "
        "is pending before any policy-episode work.",
        "",
        f"- Post-M11C merge main: `{POST_M11C_MERGE_MAIN}`",
        f"- Accepted PR/head: `#{ACCEPTED_PR}` / `{ACCEPTED_HEAD}`",
        f"- Authority artifact: `{authority['artifact_id']}`",
        f"- Authority subject SHA-256: `{authority['authority_subject_sha256']}`",
        f"- Implementation artifact: `{implementation['artifact_id']}`",
        f"- Implementation subject SHA-256: `{implementation['implementation_subject_sha256']}`",
        "- Accepted decisions: 81",
        "- Source blocked and uninterpreted: `house:119:2:278` / H.R. 8800",
        "",
        "## Authority boundary",
        "",
        "The human decision accepts every M11C candidate meaning, exact-choice effect, "
        "confidence, limitation, source reference, and coverage state as written. The "
        "implementation is canonical only as an internal action-interpretation input. "
        "Canonical Semantic IR acceptance, episodes, synthesis, public wording, "
        "publication, persistence, production, and deployment remain unauthorized.",
        "",
        "Detailed meanings remain internal evidence-backed semantic inputs. Later public "
        "wording must be separately authorized, concise by default, and disclose detail "
        "and sources progressively when useful.",
        "",
        "## Implemented decisions",
        "",
        "| Action | Effect | Coverage | Confidence | Accepted meaning | Limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in subject["implementation_records"]:
        lines.append(
            "| "
            + " | ".join(
                _escape(value)
                for value in (
                    record["action_id"],
                    record["accepted_exact_choice_position_effect"],
                    record["accepted_coverage_assessment"],
                    record["accepted_confidence"],
                    record["accepted_exact_action_meaning"],
                    "; ".join(record["accepted_limitations"]) or "None recorded",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Next human gate",
            "",
            "Mechanically verify the authority and implementation identities, exact "
            "81-row parity, preserved H.R. 8800 block, current-state boundary, and "
            "validation evidence. Do not begin policy-episode construction in this PR.",
            "",
        ]
    )
    return "\n".join(lines)


def build_artifacts() -> dict[str, Any]:
    candidate = load_json(CANDIDATE_PATH)
    readiness = load_json(READINESS_PATH)
    template = load_json(DECISION_TEMPLATE_PATH)
    if canonical_file_sha256(CANDIDATE_PATH) != ACCEPTED_CANDIDATE_FILE_SHA256:
        raise ValueError("accepted M11C candidate file digest mismatch")
    if candidate["interpretation_subject_sha256"] != ACCEPTED_CANDIDATE_SUBJECT_SHA256:
        raise ValueError("accepted M11C candidate subject digest mismatch")
    if canonical_file_sha256(DECISION_TEMPLATE_PATH) != DECISION_TEMPLATE_FILE_SHA256:
        raise ValueError("M11C decision template file digest mismatch")
    if template["decision_template_subject_sha256"] != DECISION_TEMPLATE_SUBJECT_SHA256:
        raise ValueError("M11C decision template subject digest mismatch")

    authority = build_authority_record(
        candidate_artifact=candidate,
        readiness_artifact=readiness,
        repository_root=ROOT,
        artifact_id=AUTHORITY_ID,
        candidate_file_sha256=ACCEPTED_CANDIDATE_FILE_SHA256,
        decision_template_binding={
            "template_id": template["template_id"],
            "file_sha256": DECISION_TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": DECISION_TEMPLATE_SUBJECT_SHA256,
        },
        accepted_pr=ACCEPTED_PR,
        accepted_head=ACCEPTED_HEAD,
        post_merge_main=POST_M11C_MERGE_MAIN,
        reviewer_identity=REVIEWER_IDENTITY,
        reviewer_authority=REVIEWER_AUTHORITY,
        decision_timestamp=DECISION_TIMESTAMP,
    )
    authority_bytes = _json_bytes(authority)
    authority_file_sha256 = _file_sha256(authority_bytes)
    implementation = build_implementation_bundle(
        authority=authority,
        authority_file_sha256=authority_file_sha256,
        candidate_artifact=candidate,
        artifact_id=IMPLEMENTATION_ID,
    )
    dossier = render_dossier(authority, implementation)
    dossier_bytes = dossier.encode("utf-8")
    implementation_bytes = _json_bytes(implementation)
    parity_subject = {
        "schema_version": "full_record_action_interpretation_implementation_parity_v1",
        "artifact_id": PARITY_ID,
        "generated_last": True,
        "parity_state": "pass",
        "accepted_candidate_binding": {
            "artifact_id": candidate["artifact_id"],
            "file_sha256": ACCEPTED_CANDIDATE_FILE_SHA256,
            "interpretation_subject_sha256": ACCEPTED_CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_PR,
            "accepted_head": ACCEPTED_HEAD,
            "post_merge_main": POST_M11C_MERGE_MAIN,
        },
        "generated_artifacts": [
            {
                "path": AUTHORITY_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": authority_file_sha256,
                "content_subject_sha256": authority["authority_subject_sha256"],
            },
            {
                "path": IMPLEMENTATION_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": _file_sha256(implementation_bytes),
                "content_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
            {
                "path": DOSSIER_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": _file_sha256(dossier_bytes),
            },
        ],
        "decision_count": 81,
        "source_blocked_count": 1,
        "downstream_authorizations": dict(DOWNSTREAM_AUTHORIZATIONS),
    }
    parity = {
        **parity_subject,
        "parity_subject_sha256": sha256_json(parity_subject),
    }
    validate_authority_record(authority, candidate_artifact=candidate)
    validate_implementation_bundle(
        implementation, authority=authority, candidate_artifact=candidate
    )
    for schema, value in (
        (authority_schema(), authority),
        (implementation_schema(), implementation),
        (parity_schema(), parity),
    ):
        Draft7Validator.check_schema(schema)
        errors = list(Draft7Validator(schema).iter_errors(value))
        if errors:
            raise ValueError(f"generated schema failure: {errors[0].message}")
    return {
        "authority": authority,
        "implementation": implementation,
        "dossier": dossier,
        "parity": parity,
        "authority_schema": authority_schema(),
        "implementation_schema": implementation_schema(),
        "parity_schema": parity_schema(),
    }


def build_outputs() -> dict[Path, bytes]:
    artifacts = build_artifacts()
    return {
        AUTHORITY_PATH: _json_bytes(artifacts["authority"]),
        IMPLEMENTATION_PATH: _json_bytes(artifacts["implementation"]),
        DOSSIER_PATH: artifacts["dossier"].encode("utf-8"),
        PARITY_PATH: _json_bytes(artifacts["parity"]),
        AUTHORITY_SCHEMA_PATH: _json_bytes(artifacts["authority_schema"]),
        IMPLEMENTATION_SCHEMA_PATH: _json_bytes(artifacts["implementation_schema"]),
        PARITY_SCHEMA_PATH: _json_bytes(artifacts["parity_schema"]),
    }


def write_outputs(*, check: bool) -> dict[str, Any]:
    outputs = build_outputs()
    for path, content in outputs.items():
        if check:
            if (
                not path.is_file()
                or path.read_bytes().replace(b"\r\n", b"\n") != content
            ):
                raise ValueError(
                    f"deterministic regeneration mismatch: {path.relative_to(ROOT)}"
                )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    authority = json.loads(outputs[AUTHORITY_PATH].decode("utf-8"))
    implementation = json.loads(outputs[IMPLEMENTATION_PATH].decode("utf-8"))
    return {
        "authority_id": authority["artifact_id"],
        "authority_file_sha256": _file_sha256(outputs[AUTHORITY_PATH]),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": implementation["artifact_id"],
        "implementation_file_sha256": _file_sha256(outputs[IMPLEMENTATION_PATH]),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "accepted_decision_count": implementation["subject"][
            "implementation_record_count"
        ],
        "source_blocked_count": implementation["subject"]["source_blocked_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(write_outputs(check=args.check), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
