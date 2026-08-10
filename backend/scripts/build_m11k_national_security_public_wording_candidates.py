"""Build detached M11K National Security public-wording candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_candidates import (  # noqa: E402
    compile_public_wording_candidate_package,
    seal,
    validate_public_wording_candidate_package,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from scripts.m11k_public_wording_candidate_data import (  # noqa: E402
    build_wording_definitions,
)


POST_M11J_MAIN = "03b14aa030ea302c1c109b0efd6a2ad7cef23f1b"
ACCEPTED_M11J_PR = 142
ACCEPTED_M11J_HEAD = "ed0d3b65f287b3bc1b8985a7ef85a72a9e574043"

M11H_AUTHORITY_ID = (
    "human-behavioral-semantic-ir-authority:f000477:national_security_foreign:119:v1"
)
M11H_AUTHORITY_FILE_SHA256 = (
    "d1de0f28a09a01ea9b5bbe5607128564daa6aedb929a2be1255cb50f1a99fc93"
)
M11H_AUTHORITY_SUBJECT_SHA256 = (
    "22262c77622df938b3ab3642bf49452005b549706bb20160dd7c91a88ba29714"
)
M11H_IMPLEMENTATION_ID = "behavioral-semantic-ir-decision-implementation:f000477:national_security_foreign:119:v1"
M11H_IMPLEMENTATION_FILE_SHA256 = (
    "13927cade21c85f95c097acf7afe831e55bdb0de79c93e54646e14640d444ecc"
)
M11H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "6113be3d0fad4d8da21a47ed76c089f5a7d96becd45abb9c888cf2a437bf8d67"
)

M11J_AUTHORITY_ID = "human-synthesis-authority:f000477:national_security_foreign:119:v1"
M11J_AUTHORITY_FILE_SHA256 = (
    "4fd4f7b1490415df3c1f10cc088fcc95d9f48f3eec3504b9312cb447b8e0a1cc"
)
M11J_AUTHORITY_SUBJECT_SHA256 = (
    "fdbf0b068e117322da5388c3ebc17c21d2b9a3bfbc81f4e7b92654972a9fe407"
)
M11J_IMPLEMENTATION_ID = (
    "synthesis-decision-implementation:f000477:national_security_foreign:119:v1"
)
M11J_IMPLEMENTATION_FILE_SHA256 = (
    "bd2a08caa9100cf3b5326cb739f0ce99db2f6c4650667df8087dc254d1509500"
)
M11J_IMPLEMENTATION_SUBJECT_SHA256 = (
    "d960dd7512b36c6b5b0d10c4cecc0c66251906ac624873e8618e7168bf50333f"
)

M11H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)
M11H_AUTHORITY_PATH = M11H_ROOT / "human_behavioral_semantic_ir_authority.json"
M11H_IMPLEMENTATION_PATH = (
    M11H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
M11J_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_national_security_foreign_119_v1"
)
M11J_AUTHORITY_PATH = M11J_ROOT / "human_synthesis_authority.json"
M11J_IMPLEMENTATION_PATH = M11J_ROOT / "synthesis_decision_implementation.json"

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_national_security_foreign_119_v1"
)
PACKAGE_PATH = OUTPUT_ROOT / "public_wording_candidate_package.json"
DECISION_TEMPLATE_PATH = OUTPUT_ROOT / "human_public_wording_decision_template.json"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PACKAGE_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_public_wording_candidates_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_public_wording_decision_template_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_public_wording_candidate_parity_v1.schema.json"
)

PACKAGE_ID = "public-wording-candidates:f000477:national_security_foreign:119:v1"
DECISION_TEMPLATE_ID = (
    "human-public-wording-decision-template:f000477:national_security_foreign:119:v1"
)
PARITY_ID = "public-wording-candidate-parity:f000477:national_security_foreign:119:v1"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M11K artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    h_authority = load(M11H_AUTHORITY_PATH)
    h_implementation = load(M11H_IMPLEMENTATION_PATH)
    j_authority = load(M11J_AUTHORITY_PATH)
    j_implementation = load(M11J_IMPLEMENTATION_PATH)
    checks = [
        canonical_file_sha256(M11H_AUTHORITY_PATH) == M11H_AUTHORITY_FILE_SHA256,
        h_authority["artifact_id"] == M11H_AUTHORITY_ID,
        h_authority["authority_subject_sha256"] == M11H_AUTHORITY_SUBJECT_SHA256,
        canonical_file_sha256(M11H_IMPLEMENTATION_PATH)
        == M11H_IMPLEMENTATION_FILE_SHA256,
        h_implementation["artifact_id"] == M11H_IMPLEMENTATION_ID,
        h_implementation["implementation_subject_sha256"]
        == M11H_IMPLEMENTATION_SUBJECT_SHA256,
        canonical_file_sha256(M11J_AUTHORITY_PATH) == M11J_AUTHORITY_FILE_SHA256,
        j_authority["artifact_id"] == M11J_AUTHORITY_ID,
        j_authority["authority_subject_sha256"] == M11J_AUTHORITY_SUBJECT_SHA256,
        canonical_file_sha256(M11J_IMPLEMENTATION_PATH)
        == M11J_IMPLEMENTATION_FILE_SHA256,
        j_implementation["artifact_id"] == M11J_IMPLEMENTATION_ID,
        j_implementation["implementation_subject_sha256"]
        == M11J_IMPLEMENTATION_SUBJECT_SHA256,
        len(h_implementation["subject"]["implementation_records"]) == 15,
        len(j_implementation["subject"]["implementation_records"]) == 2,
        j_authority["subject"]["accepted_proposition_role_accounting"],
    ]
    if not all(checks):
        raise ValueError("accepted M11H/M11J identity or accounting differs")
    return h_authority, h_implementation, j_authority, j_implementation


def build_package(
    h_authority: dict[str, Any],
    h_implementation: dict[str, Any],
    j_authority: dict[str, Any],
    j_implementation: dict[str, Any],
) -> dict[str, Any]:
    definitions = build_wording_definitions(h_implementation, j_implementation)
    return compile_public_wording_candidate_package(
        behavioral_authority=h_authority,
        behavioral_implementation=h_implementation,
        synthesis_authority=j_authority,
        synthesis_implementation=j_implementation,
        wording_definitions=definitions,
        subject={
            "artifact_id": PACKAGE_ID,
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
            "chamber": "House",
            "base_binding": {
                "accepted_m11j_pr": ACCEPTED_M11J_PR,
                "accepted_m11j_head": ACCEPTED_M11J_HEAD,
                "post_m11j_main": POST_M11J_MAIN,
            },
            "source_authority_boundary": "Accepted M11H Behavioral Semantic IR and accepted M11J canonical internal synthesis are the sole semantic sources. Episode and action lineage is traceability only.",
            "presentation_contract": "Selected Issue Experience V1.1",
            "blocked_action_boundary": {
                "action_id": "house:119:2:278",
                "state": "source_blocked_uninterpreted_unavailable_for_public_wording",
            },
        },
    )


def build_decision_template(package: dict[str, Any]) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "full_record_public_wording_decision_template_v1",
            "artifact_id": DECISION_TEMPLATE_ID,
            "candidate_binding": {
                "artifact_id": package["artifact_id"],
                "public_wording_candidate_package_subject_sha256": package[
                    "public_wording_candidate_package_subject_sha256"
                ],
            },
            "decision_state": "empty_pending_human_substantive_wording_review",
            "wording_decisions": [
                {
                    "wording_item_id": row["wording_item_id"],
                    "wording_item_subject_sha256": row["wording_item_subject_sha256"],
                    "decision": None,
                    "bounded_revision": None,
                    "reviewer_notes": None,
                }
                for row in package["subject"]["wording_items"]
            ],
            "reviewer": None,
            "reviewer_authority": None,
            "reviewed_at_utc": None,
            "authorizing": False,
            "production_selectable": False,
            "downstream_authorizations": {
                "publication": False,
                "production_persistence": False,
                "database_writes": False,
                "production_writes": False,
                "deployment": False,
            },
        },
        "decision_template_subject_sha256",
    )


def render_dossier(package: dict[str, Any]) -> str:
    items = package["subject"]["wording_items"]
    sections = [
        ("Issue overview", "issue_overview"),
        ("Cross-pattern synthesis", "synthesis"),
        ("Repeated patterns", "repeated_pattern"),
        ("Limiting trajectory", "trajectory"),
        ("Notable choices", "notable_choice"),
    ]
    lines = [
        "# M11K National Security Public-Wording Review",
        "",
        "These are detached, non-authorizing wording candidates. They do not activate public copy, change runtime behavior, or authorize publication or production use.",
        "",
    ]
    for heading, surface in sections:
        lines.extend([f"## {heading}", ""])
        for item in [row for row in items if row["surface"] == surface]:
            lines.extend(
                [
                    f"### {item['public_title']}",
                    "",
                    f"**Proposed public wording:** {item['primary_sentence']}",
                    "",
                ]
            )
            if item["secondary_clarification"]:
                lines.extend(
                    [f"**Short clarification:** {item['secondary_clarification']}", ""]
                )
            display = item["direction_display"]
            direction = (
                "none; exact behavior is stated instead"
                if display is None
                else f"{display['symbol']} {display['label']}"
            )
            lines.extend(
                [
                    f"**Direction / evidence label:** {direction}; {item['evidence_count_label']}",
                    "",
                    "**Internal governed semantic source:**",
                    "",
                ]
            )
            for binding in item["semantic_source_bindings"]:
                lines.append(f"- `{binding['source_id']}` — {binding['proposition']}")
            retained = [
                row["public_copy"]
                for row in item["limitation_treatments"]
                if row["treatment"] == "retained_public_copy"
            ]
            lines.extend(["", "**Public limitation/context copy:**", ""])
            lines.extend(f"- {value}" for value in retained)
            lines.extend(
                [
                    "",
                    f"**Intentionally compressed or omitted:** {item['compression_notes']}",
                    "",
                    f"**Prohibited inference risks:** {', '.join(item['prohibited_inference_risks'])}.",
                    "",
                ]
            )
    lines.extend(
        [
            "## Required human decisions",
            "",
            "Review all 18 wording items for clarity, semantic fidelity, compression, limitation placement, and prohibited-inference risk. Accept, revise within the bound semantic source, or reject each item.",
            "",
            "H.R. 8800 (`house:119:2:278`) remains source-blocked and unavailable for wording. Publication, persistence, database writes, production writes, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build(check: bool = False) -> dict[str, Any]:
    h_authority, h_implementation, j_authority, j_implementation = preflight()
    package = build_package(
        h_authority, h_implementation, j_authority, j_implementation
    )
    decision = build_decision_template(package)
    dossier = render_dossier(package)
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    Draft7Validator(load(DECISION_SCHEMA_PATH)).validate(decision)
    validate_public_wording_candidate_package(
        package,
        behavioral_authority=h_authority,
        behavioral_implementation=h_implementation,
        synthesis_authority=j_authority,
        synthesis_implementation=j_implementation,
    )
    package_text = json_text(package)
    decision_text = json_text(decision)
    entries = [
        {
            "path": PACKAGE_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(package_text),
            "content_subject_sha256": package[
                "public_wording_candidate_package_subject_sha256"
            ],
        },
        {
            "path": DECISION_TEMPLATE_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(decision_text),
            "content_subject_sha256": decision["decision_template_subject_sha256"],
        },
        {
            "path": DOSSIER_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(dossier),
            "content_subject_sha256": None,
        },
    ]
    parity = seal(
        {
            "schema_version": "full_record_public_wording_candidate_parity_v1",
            "artifact_id": PARITY_ID,
            "package_binding": {
                "artifact_id": package["artifact_id"],
                "public_wording_candidate_package_subject_sha256": package[
                    "public_wording_candidate_package_subject_sha256"
                ],
            },
            "entries": entries,
        },
        "parity_subject_sha256",
    )
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    write_or_check(PACKAGE_PATH, package_text, check)
    write_or_check(DECISION_TEMPLATE_PATH, decision_text, check)
    write_or_check(DOSSIER_PATH, dossier, check)
    write_or_check(PARITY_PATH, json_text(parity), check)
    return {"package": package, "decision": decision, "parity": parity}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.check)
    package = result["package"]
    print(
        json.dumps(
            {
                "artifact_id": package["artifact_id"],
                "wording_item_count": len(package["subject"]["wording_items"]),
                "package_subject_sha256": package[
                    "public_wording_candidate_package_subject_sha256"
                ],
                "decision_template_subject_sha256": result["decision"][
                    "decision_template_subject_sha256"
                ],
                "parity_subject_sha256": result["parity"]["parity_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
