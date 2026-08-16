"""Build detached M12K Environment & Energy public-wording candidates."""

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
from scripts.m12k_public_wording_candidate_data import (  # noqa: E402
    build_wording_definitions,
)


POST_M12I_MAIN = "ea6b93cd51110dd2e8da71448ce2a5b14f864ba3"
ACCEPTED_M12I_PR = 154
ACCEPTED_M12I_HEAD = "95a7c59cd1876c7934fea9547008e2b8e86e8be0"
REVIEWED_BASE = "d3bc0fddad701e0621c87857ed80288c23a867aa"

M12H_AUTHORITY_ID = (
    "human-behavioral-semantic-ir-authority:f000477:environment_energy:119:v1"
)
M12H_AUTHORITY_FILE_SHA256 = (
    "eb6388827648aaa6ee6cabda3e45cf0c93f35116a6f97e9540263dec7ae7c4af"
)
M12H_AUTHORITY_SUBJECT_SHA256 = (
    "31b26aa0a671a3ffb5226a26862df3bca10de3aee93a795d92cfc3abe26be276"
)
M12H_IMPLEMENTATION_ID = (
    "behavioral-semantic-ir-decision-implementation:f000477:environment_energy:119:v1"
)
M12H_IMPLEMENTATION_FILE_SHA256 = (
    "ae403e7334f02f4135e857d4663efa79a75540648184a444572138f1812da491"
)
M12H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "8621aecaafc8352c31b16284ed6acde9d0d290f3e345af41ec6e231d774c9c32"
)
M12J_AUTHORITY_ID = "human-synthesis-authority:f000477:environment_energy:119:v1"
M12J_AUTHORITY_FILE_SHA256 = (
    "edf92b4543376b94ccebbc87d3ec85ea734d0ab7a38952848062bfe7cc78be5c"
)
M12J_AUTHORITY_SUBJECT_SHA256 = (
    "060386625bebf6095bd91e20c7a63578b170cd94ced89a0d58996adbf606a187"
)
M12J_IMPLEMENTATION_ID = (
    "synthesis-decision-implementation:f000477:environment_energy:119:v1"
)
M12J_IMPLEMENTATION_FILE_SHA256 = (
    "74f573f40e8f26eadb6b126a0d0ecaa0b6abb5ca5ac539dd8c4a80d8851692cd"
)
M12J_IMPLEMENTATION_SUBJECT_SHA256 = (
    "bd7a786523fb2e969f44c1374edc96ea59d0885a4d83ceafb5ff14d9cb135a72"
)

M12H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_environment_energy_119_v1"
)
M12J_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_environment_energy_119_v1"
)
M12H_AUTHORITY_PATH = M12H_ROOT / "human_behavioral_semantic_ir_authority.json"
M12H_IMPLEMENTATION_PATH = (
    M12H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
M12J_AUTHORITY_PATH = M12J_ROOT / "human_synthesis_authority.json"
M12J_IMPLEMENTATION_PATH = M12J_ROOT / "synthesis_decision_implementation.json"

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_environment_energy_119_v1"
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

PACKAGE_ID = "public-wording-candidates:f000477:environment_energy:119:v1"
DECISION_TEMPLATE_ID = (
    "human-public-wording-decision-template:f000477:environment_energy:119:v1"
)
PARITY_ID = "public-wording-candidate-parity:f000477:environment_energy:119:v1"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M12K artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    paths = {
        M12H_AUTHORITY_PATH: M12H_AUTHORITY_FILE_SHA256,
        M12H_IMPLEMENTATION_PATH: M12H_IMPLEMENTATION_FILE_SHA256,
        M12J_AUTHORITY_PATH: M12J_AUTHORITY_FILE_SHA256,
        M12J_IMPLEMENTATION_PATH: M12J_IMPLEMENTATION_FILE_SHA256,
    }
    for path, expected in paths.items():
        if canonical_file_sha256(path) != expected:
            raise ValueError(
                f"accepted semantic input differs: {path.relative_to(ROOT)}"
            )
    h_authority = load(M12H_AUTHORITY_PATH)
    h_implementation = load(M12H_IMPLEMENTATION_PATH)
    j_authority = load(M12J_AUTHORITY_PATH)
    j_implementation = load(M12J_IMPLEMENTATION_PATH)
    checks = [
        h_authority["artifact_id"] == M12H_AUTHORITY_ID,
        h_authority["authority_subject_sha256"] == M12H_AUTHORITY_SUBJECT_SHA256,
        h_implementation["artifact_id"] == M12H_IMPLEMENTATION_ID,
        h_implementation["implementation_subject_sha256"]
        == M12H_IMPLEMENTATION_SUBJECT_SHA256,
        j_authority["artifact_id"] == M12J_AUTHORITY_ID,
        j_authority["authority_subject_sha256"] == M12J_AUTHORITY_SUBJECT_SHA256,
        j_implementation["artifact_id"] == M12J_IMPLEMENTATION_ID,
        j_implementation["implementation_subject_sha256"]
        == M12J_IMPLEMENTATION_SUBJECT_SHA256,
        len(h_implementation["subject"]["implementation_records"]) == 3,
        len(j_implementation["subject"]["implementation_records"]) == 1,
        h_implementation["subject"]["blocked_actions"] == [],
    ]
    if not all(checks):
        raise ValueError("accepted M12H/M12J identity or accounting differs")
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
        legacy_binding_names=False,
        subject={
            "artifact_id": PACKAGE_ID,
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "ENVIRONMENT_ENERGY",
            "congress": 119,
            "chamber": "House",
            "base_binding": {
                "accepted_m12i_pr": ACCEPTED_M12I_PR,
                "accepted_m12i_head": ACCEPTED_M12I_HEAD,
                "reviewed_base": REVIEWED_BASE,
                "post_m12i_main": POST_M12I_MAIN,
            },
            "source_authority_boundary": "Accepted M12H Behavioral Semantic IR and accepted M12J canonical internal synthesis are the sole semantic sources. Episode and action lineage is traceability only.",
            "presentation_contract": "Selected Issue Experience V1.1",
            "blocked_action_boundaries": [],
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
    lines = [
        "# M12K Environment & Energy Public-Wording Review",
        "",
        "These five detached candidates are non-authorizing. Proposed public copy is shown first; governed semantic sources and complete limitation treatment follow each item.",
        "",
    ]
    for item in package["subject"]["wording_items"]:
        direction = (
            "omitted; the sentence states the object of opposition"
            if item["direction_display"] is None
            else item["direction_display"]["label"]
        )
        lines.extend(
            [
                f"## {item['public_title']} (`{item['surface']}`)",
                "",
                f"### {item['primary_sentence']}",
                "",
                f"**Clarification:** {item['secondary_clarification'] or 'None'}",
                "",
                f"**Evidence label:** {item['evidence_count_label']}",
                "",
                f"**Direction display:** {direction}",
                "",
                "**Exact accepted semantic sources:**",
                "",
            ]
        )
        for binding in item["semantic_source_bindings"]:
            lines.extend(
                [
                    f"- `{binding['source_kind']}:{binding['source_id']}`",
                    f"  - Proposition: {binding['proposition']}",
                    f"  - Semantic type/direction: `{binding['semantic_type']}` / `{binding['source_direction']}`",
                ]
            )
        lines.extend(["", "**Complete source-limitation treatment:**", ""])
        for treatment in item["limitation_treatments"]:
            detail = treatment.get("public_copy") or treatment.get("reason")
            lines.extend(
                [
                    f"- `{treatment['treatment']}` — {treatment['source_limitation']}",
                    f"  - Treatment detail: {detail}",
                ]
            )
        lines.extend(
            [
                "",
                f"**Compression rationale:** {item['compression_notes']}",
                "",
                f"**Prohibited-inference risks:** {', '.join(item['prohibited_inference_risks'])}.",
                "",
                f"**Semantic guard:** `{json.dumps(item['semantic_guard'], ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Required human decisions",
            "",
            "Review exactly five wording items. The decision template contains no decisions and grants no authority. Public-wording acceptance, site integration, publication, persistence, production/database writes, and deployment remain false.",
            "",
            "No Environment & Energy blocked action exists or is represented.",
            "",
        ]
    )
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
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
    outputs = {
        PACKAGE_PATH: package_text,
        DECISION_TEMPLATE_PATH: decision_text,
        DOSSIER_PATH: dossier,
        PARITY_PATH: json_text(parity),
    }
    for path, content in outputs.items():
        write_or_check(path, content, check)
    return {
        "package_id": PACKAGE_ID,
        "package_file_sha256": text_sha256(package_text),
        "package_subject_sha256": package[
            "public_wording_candidate_package_subject_sha256"
        ],
        "decision_template_id": DECISION_TEMPLATE_ID,
        "decision_template_file_sha256": text_sha256(decision_text),
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "dossier_file_sha256": text_sha256(dossier),
        "parity_id": PARITY_ID,
        "parity_file_sha256": text_sha256(json_text(parity)),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "wording_item_accounting": package["subject"]["wording_item_accounting"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
