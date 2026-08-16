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
    DOWNSTREAM_AUTHORIZATIONS,
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


POST_M12C_MERGE_MAIN = "cdd1cf652b92b9577f698149534b7683d47c554e"
ACCEPTED_PR = 151
ACCEPTED_HEAD = "013fc57dbff538fd9d2b0b99b85c0a2285c2faba"
ACCEPTED_CANDIDATE_FILE_SHA256 = (
    "84713da4156f8a3f0347384225905351017bf21615ebcdca76e147aa2294b242"
)
ACCEPTED_CANDIDATE_SUBJECT_SHA256 = (
    "e7a9b92d6d8972d3c01b052cbe85140ed449baf38ca2e5774ee58c322c03795c"
)
DECISION_TEMPLATE_FILE_SHA256 = (
    "41105762b2d036829aec520772a38bfd65ba49d8941b11531278a5c6699db463"
)
DECISION_TEMPLATE_SUBJECT_SHA256 = (
    "ea2b27433c0c6c9e5b47dd3ad6f06cf0ce93c796409d179d9a982356a3114ea6"
)
REVIEWER_IDENTITY = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_record_action_interpretation_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-16T01:01:00Z"

CANDIDATE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates"
    / "f000477_environment_energy_119_v1"
)
CANDIDATE_PATH = CANDIDATE_ROOT / "candidate_batch.json"
DECISION_TEMPLATE_PATH = CANDIDATE_ROOT / "human_decision_template.json"
READINESS_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/source_readiness"
    / "f000477_environment_energy_119_interpretation_source_readiness_v1.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions"
    / "f000477_environment_energy_119_v1"
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

AUTHORITY_ID = "human-action-interpretation-authority:f000477:environment_energy:119:v1"
IMPLEMENTATION_ID = (
    "action-interpretation-decision-implementation:f000477:environment_energy:119:v1"
)
PARITY_ID = (
    "action-interpretation-decision-implementation-parity:"
    "f000477:environment_energy:119:v1"
)


def json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def content_sha256(content: bytes) -> str:
    return hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()


def escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    records = implementation["subject"]["implementation_records"]
    lines = [
        "# M12D Environment & Energy Action-Meaning Acceptance",
        "",
        "Status: all 63 independently reviewed M12C meanings and exact-choice effects "
        "are implemented without revision as canonical internal action interpretations.",
        "",
        f"- Post-M12C main: `{POST_M12C_MERGE_MAIN}`",
        f"- Accepted PR/head: `#{ACCEPTED_PR}` / `{ACCEPTED_HEAD}`",
        f"- Authority artifact: `{authority['artifact_id']}`",
        f"- Authority subject SHA-256: `{authority['authority_subject_sha256']}`",
        f"- Implementation artifact: `{implementation['artifact_id']}`",
        f"- Implementation subject SHA-256: `{implementation['implementation_subject_sha256']}`",
        "- Accepted decisions: 63 `accept_candidate_as_written`",
        "- Source blocked: 0",
        "",
        "## Mechanical acceptance boundary",
        "",
        "This stage reproduces the independent M12C review decision exactly. It does "
        "not reinterpret or revise meaning, effects, confidence, coverage, limitations, "
        "or evidence. Policy-episode candidates may use these records as semantic input, "
        "but episode acceptance and all later authorities remain false.",
        "",
        "## Canonical internal records",
        "",
        "| Action | Effect | Coverage | Confidence | Accepted meaning | Limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                escape(value)
                for value in (
                    record["action_id"],
                    record["accepted_exact_choice_position_effect"],
                    record["accepted_coverage_assessment"],
                    record["accepted_confidence"],
                    record["accepted_exact_action_meaning"],
                    "; ".join(record["accepted_limitations"]),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "H.R. 6387 remains `non_directional_not_voting`. H.R. 471 and H.R. 3898 "
            "retain their accepted whole-package limitations exactly.",
            "",
        ]
    )
    return "\n".join(lines)


def build_artifacts() -> dict[str, Any]:
    candidate = load_json(CANDIDATE_PATH)
    readiness = load_json(READINESS_PATH)
    template = load_json(DECISION_TEMPLATE_PATH)
    if canonical_file_sha256(CANDIDATE_PATH) != ACCEPTED_CANDIDATE_FILE_SHA256:
        raise ValueError("accepted M12C candidate file digest mismatch")
    if candidate["interpretation_subject_sha256"] != ACCEPTED_CANDIDATE_SUBJECT_SHA256:
        raise ValueError("accepted M12C candidate subject digest mismatch")
    if canonical_file_sha256(DECISION_TEMPLATE_PATH) != DECISION_TEMPLATE_FILE_SHA256:
        raise ValueError("accepted M12C decision-template file digest mismatch")
    if template["decision_template_subject_sha256"] != DECISION_TEMPLATE_SUBJECT_SHA256:
        raise ValueError("accepted M12C decision-template subject digest mismatch")

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
        post_merge_main=POST_M12C_MERGE_MAIN,
        reviewer_identity=REVIEWER_IDENTITY,
        reviewer_authority=REVIEWER_AUTHORITY,
        decision_timestamp=DECISION_TIMESTAMP,
    )
    authority_content = json_bytes(authority)
    authority_file_sha256 = content_sha256(authority_content)
    implementation = build_implementation_bundle(
        authority=authority,
        authority_file_sha256=authority_file_sha256,
        candidate_artifact=candidate,
        artifact_id=IMPLEMENTATION_ID,
        implementation_namespace="m12d",
    )
    dossier = render_dossier(authority, implementation)
    implementation_content = json_bytes(implementation)
    dossier_content = dossier.encode("utf-8")
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
            "post_merge_main": POST_M12C_MERGE_MAIN,
        },
        "generated_artifacts": [
            {
                "path": AUTHORITY_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": authority_file_sha256,
                "content_subject_sha256": authority["authority_subject_sha256"],
            },
            {
                "path": IMPLEMENTATION_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": content_sha256(implementation_content),
                "content_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
            {
                "path": DOSSIER_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": content_sha256(dossier_content),
            },
        ],
        "decision_count": len(authority["subject"]["decisions"]),
        "source_blocked_count": len(authority["subject"]["source_blocked_actions"]),
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
    for schema_path, value in (
        (AUTHORITY_SCHEMA_PATH, authority),
        (IMPLEMENTATION_SCHEMA_PATH, implementation),
        (PARITY_SCHEMA_PATH, parity),
    ):
        schema = load_json(schema_path)
        errors = list(Draft7Validator(schema).iter_errors(value))
        if errors:
            raise ValueError(f"{schema_path.name}: {errors[0].message}")
    return {
        "authority": authority,
        "implementation": implementation,
        "dossier": dossier,
        "parity": parity,
    }


def outputs() -> dict[Path, bytes]:
    artifacts = build_artifacts()
    return {
        AUTHORITY_PATH: json_bytes(artifacts["authority"]),
        IMPLEMENTATION_PATH: json_bytes(artifacts["implementation"]),
        DOSSIER_PATH: artifacts["dossier"].encode("utf-8"),
        PARITY_PATH: json_bytes(artifacts["parity"]),
    }


def write_outputs(*, check: bool) -> dict[str, Any]:
    generated = outputs()
    for path, content in generated.items():
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
    authority = json.loads(generated[AUTHORITY_PATH])
    implementation = json.loads(generated[IMPLEMENTATION_PATH])
    return {
        "authority_id": authority["artifact_id"],
        "authority_file_sha256": content_sha256(generated[AUTHORITY_PATH]),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": implementation["artifact_id"],
        "implementation_file_sha256": content_sha256(generated[IMPLEMENTATION_PATH]),
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
