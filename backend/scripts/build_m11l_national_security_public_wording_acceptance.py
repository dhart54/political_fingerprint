"""Build M11L human public-wording authority and deterministic implementation."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_public_wording_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    apply_bounded_revision,
    digest,
    seal,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402
from scripts.m11l_public_wording_decision_data import (  # noqa: E402
    ACCEPTED_AS_WRITTEN,
    resolved_replacements,
    validate_decision_ids,
)


POST_M11K_MAIN = "649bb508e2cdb92ab8cb0afe82dd266c2f503944"
ACCEPTED_M11K_PR = 143
ACCEPTED_M11K_HEAD = "57f29bd156c0f6c747fd21084491558d3277bd22"
APPROVED_AT_UTC = "2026-08-14T00:10:44Z"

M11K_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_national_security_foreign_119_v1"
)
PACKAGE_PATH = M11K_ROOT / "public_wording_candidate_package.json"
TEMPLATE_PATH = M11K_ROOT / "human_public_wording_decision_template.json"
M11K_PARITY_PATH = M11K_ROOT / "parity_manifest.json"
PACKAGE_ID = "public-wording-candidates:f000477:national_security_foreign:119:v1"
PACKAGE_FILE_SHA256 = "eef9c35e08fd0ccecf931c1a47d6f88793954f92a649386a2032b305b3cc24bb"
PACKAGE_SUBJECT_SHA256 = (
    "7647db4d58cdfc34c7ee6f5aef955ea67eef650e43084e1ed58383a0b64ddd93"
)
TEMPLATE_ID = (
    "human-public-wording-decision-template:f000477:national_security_foreign:119:v1"
)
TEMPLATE_FILE_SHA256 = (
    "6e96a461d2d052906b038a8ddf6d7d6fa92ba4309f292f45f88da9fcbf225def"
)
TEMPLATE_SUBJECT_SHA256 = (
    "16b146441ff93797301467f64b58d66da45796fdfc8091d6e3b1c6f08353c50a"
)
M11K_PARITY_ID = (
    "public-wording-candidate-parity:f000477:national_security_foreign:119:v1"
)
M11K_PARITY_FILE_SHA256 = (
    "1d9f02eba933033e6b794d451f93603d826f1e3b0d6565b871ed1fd8512e541d"
)
M11K_PARITY_SUBJECT_SHA256 = (
    "8d79f1fb7ca6bbc7ac25c26ca764760c1de2b736ff57882c682458a5ea0be235"
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
    / "docs/editorial/full_record_reviews/public_wording_implementations/f000477_national_security_foreign_119_v1"
)
AUTHORITY_PATH = OUTPUT_ROOT / "human_public_wording_authority.json"
IMPLEMENTATION_PATH = OUTPUT_ROOT / "reviewed_wording_decision_implementation.json"
PARITY_PATH = OUTPUT_ROOT / "implementation_parity_manifest.json"
DOSSIER_PATH = OUTPUT_ROOT / "implementation_dossier.md"
AUTHORITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_public_wording_authority_v1.schema.json"
)
IMPLEMENTATION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_public_wording_decision_implementation_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_public_wording_implementation_parity_v1.schema.json"
)

AUTHORITY_ID = "human-public-wording-authority:f000477:national_security_foreign:119:v1"
IMPLEMENTATION_ID = (
    "reviewed-wording-decision-implementation:f000477:national_security_foreign:119:v1"
)
PARITY_ID = (
    "public-wording-implementation-parity:f000477:national_security_foreign:119:v1"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M11L artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _replace(value: object, path: list[object], replacement: object) -> None:
    cursor = value
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[path[-1]] = deepcopy(replacement)  # type: ignore[index]


def preflight() -> tuple[dict[str, Any], ...]:
    package = load(PACKAGE_PATH)
    template = load(TEMPLATE_PATH)
    parity = load(M11K_PARITY_PATH)
    h_authority = load(M11H_AUTHORITY_PATH)
    h_implementation = load(M11H_IMPLEMENTATION_PATH)
    j_authority = load(M11J_AUTHORITY_PATH)
    j_implementation = load(M11J_IMPLEMENTATION_PATH)
    if not (
        canonical_file_sha256(PACKAGE_PATH) == PACKAGE_FILE_SHA256
        and package["artifact_id"] == PACKAGE_ID
        and package["public_wording_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256
        and canonical_file_sha256(TEMPLATE_PATH) == TEMPLATE_FILE_SHA256
        and template["artifact_id"] == TEMPLATE_ID
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and canonical_file_sha256(M11K_PARITY_PATH) == M11K_PARITY_FILE_SHA256
        and parity["artifact_id"] == M11K_PARITY_ID
        and parity["parity_subject_sha256"] == M11K_PARITY_SUBJECT_SHA256
    ):
        raise ValueError("accepted M11K identity differs")
    validate_decision_ids(
        {row["wording_item_id"] for row in package["subject"]["wording_items"]}
    )
    return (
        package,
        template,
        parity,
        h_authority,
        h_implementation,
        j_authority,
        j_implementation,
    )


def _revision(item: dict[str, Any]) -> dict[str, Any] | None:
    replacements = resolved_replacements(item)
    if not replacements:
        return None
    revised = deepcopy(item)
    fields = []
    for replacement in replacements:
        path = replacement["path"]
        cursor: object = item
        for key in path:
            cursor = cursor[key]  # type: ignore[index]
        fields.append(
            {
                "path": path,
                "original_value_sha256": digest(cursor),
                "revised_value": replacement["value"],
            }
        )
        _replace(revised, path, replacement["value"])
    revised = seal(revised, "wording_item_subject_sha256")
    return {
        "field_replacements": fields,
        "revised_wording_item_content_sha256": digest(revised),
    }


def build_authority(
    package: dict[str, Any], template: dict[str, Any], parity: dict[str, Any]
) -> dict[str, Any]:
    decisions = []
    for item in package["subject"]["wording_items"]:
        decision = (
            "accept_candidate_as_written"
            if item["wording_item_id"] in ACCEPTED_AS_WRITTEN
            else "accept_with_bounded_revision"
        )
        decisions.append(
            seal(
                {
                    "wording_item_id": item["wording_item_id"],
                    "original_wording_item_subject_sha256": item[
                        "wording_item_subject_sha256"
                    ],
                    "original_wording_item_content_sha256": digest(item),
                    "decision": decision,
                    "bounded_revision": _revision(item),
                    "reviewer": "dhart54",
                    "reviewer_authority": "full_record_public_wording_review_authority_v1",
                    "reviewed_at_utc": APPROVED_AT_UTC,
                },
                "decision_subject_sha256",
            )
        )
    return seal(
        {
            "schema_version": "full_record_public_wording_authority_v1",
            "artifact_id": AUTHORITY_ID,
            "accepted": True,
            "immutable": True,
            "canonical_reviewed_wording_authority": True,
            "public": False,
            "production_selectable": False,
            "subject": {
                "member_bioguide_id": "F000477",
                "member_slug": "leg_valerie_p_foushee",
                "issue_id": "NATIONAL_SECURITY_FOREIGN",
                "congress": 119,
                "chamber": "House",
                "reviewer": "dhart54",
                "reviewer_authority": "full_record_public_wording_review_authority_v1",
                "approved_at_utc": APPROVED_AT_UTC,
                "base_binding": {
                    "accepted_m11k_pr": ACCEPTED_M11K_PR,
                    "accepted_m11k_head": ACCEPTED_M11K_HEAD,
                    "post_m11k_main": POST_M11K_MAIN,
                },
                "candidate_binding": {
                    "artifact_id": package["artifact_id"],
                    "file_sha256": PACKAGE_FILE_SHA256,
                    "package_subject_sha256": package[
                        "public_wording_candidate_package_subject_sha256"
                    ],
                },
                "decision_template_binding": {
                    "artifact_id": template["artifact_id"],
                    "file_sha256": TEMPLATE_FILE_SHA256,
                    "decision_template_subject_sha256": template[
                        "decision_template_subject_sha256"
                    ],
                },
                "parity_binding": {
                    "artifact_id": parity["artifact_id"],
                    "file_sha256": M11K_PARITY_FILE_SHA256,
                    "parity_subject_sha256": parity["parity_subject_sha256"],
                },
                "m11h_authority_binding": {
                    **package["subject"]["m11h_authority_binding"],
                    "file_sha256": canonical_file_sha256(M11H_AUTHORITY_PATH),
                },
                "m11h_implementation_binding": {
                    **package["subject"]["m11h_implementation_binding"],
                    "file_sha256": canonical_file_sha256(M11H_IMPLEMENTATION_PATH),
                },
                "m11j_authority_binding": {
                    **package["subject"]["m11j_authority_binding"],
                    "file_sha256": canonical_file_sha256(M11J_AUTHORITY_PATH),
                },
                "m11j_implementation_binding": {
                    **package["subject"]["m11j_implementation_binding"],
                    "file_sha256": canonical_file_sha256(M11J_IMPLEMENTATION_PATH),
                },
                "wording_decisions": decisions,
                "decision_accounting": {
                    "accept_candidate_as_written": 4,
                    "accept_with_bounded_revision": 14,
                    "rejected": 0,
                    "unresolved": 0,
                },
                "complete_source_accounting": package["subject"]["source_accounting"],
                "complete_synthesis_role_accounting": package["subject"][
                    "complete_behavioral_synthesis_role_accounting"
                ],
                "blocked_actions": package["subject"]["blocked_actions"],
                "blocked_action_boundary": package["subject"][
                    "blocked_action_boundary"
                ],
                "authority_effect": "canonical_reviewed_wording_internal_only",
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
        },
        "authority_subject_sha256",
    )


def build_implementation(
    authority: dict[str, Any], package: dict[str, Any]
) -> dict[str, Any]:
    decisions = {
        row["wording_item_id"]: row for row in authority["subject"]["wording_decisions"]
    }
    records = []
    for item in package["subject"]["wording_items"]:
        decision = decisions[item["wording_item_id"]]
        implemented = apply_bounded_revision(item, decision["bounded_revision"])
        records.append(
            seal(
                {
                    "schema_version": "full_record_public_wording_implementation_record_v1",
                    "record_id": f"reviewed-wording-decision-implementation:{item['wording_item_id']}:m11l:v1",
                    "wording_item_id": item["wording_item_id"],
                    "authority_artifact_id": authority["artifact_id"],
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                    "authority_decision_subject_sha256": decision[
                        "decision_subject_sha256"
                    ],
                    "decision": decision["decision"],
                    "bounded_revision": decision["bounded_revision"],
                    "original_candidate_content": item,
                    "original_candidate_content_sha256": digest(item),
                    "original_candidate_subject_sha256": item[
                        "wording_item_subject_sha256"
                    ],
                    "implemented_reviewed_wording": implemented,
                    "implemented_reviewed_wording_sha256": digest(implemented),
                    "canonical_reviewed_wording": True,
                    "public": False,
                    "production_selectable": False,
                    "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
                },
                "record_subject_sha256",
            )
        )
    return seal(
        {
            "schema_version": "full_record_public_wording_decision_implementation_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "subject": {
                "authority_binding": {
                    "artifact_id": authority["artifact_id"],
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                },
                "candidate_binding": authority["subject"]["candidate_binding"],
                "m11h_authority_binding": authority["subject"][
                    "m11h_authority_binding"
                ],
                "m11h_implementation_binding": authority["subject"][
                    "m11h_implementation_binding"
                ],
                "m11j_authority_binding": authority["subject"][
                    "m11j_authority_binding"
                ],
                "m11j_implementation_binding": authority["subject"][
                    "m11j_implementation_binding"
                ],
                "implementation_records": records,
                "complete_source_accounting": authority["subject"][
                    "complete_source_accounting"
                ],
                "complete_synthesis_role_accounting": authority["subject"][
                    "complete_synthesis_role_accounting"
                ],
                "blocked_actions": authority["subject"]["blocked_actions"],
                "blocked_action_boundary": authority["subject"][
                    "blocked_action_boundary"
                ],
                "final_accounting": {
                    "canonical_reviewed_wording_count": 18,
                    "surface_accounting": {
                        "issue_overview": 1,
                        "synthesis": 2,
                        "repeated_pattern": 8,
                        "trajectory": 1,
                        "notable_choice": 6,
                    },
                    "decision_accounting": authority["subject"]["decision_accounting"],
                },
                "canonical_reviewed_wording_present": True,
                "public": False,
                "production_selectable": False,
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
        },
        "implementation_subject_sha256",
    )


def render_dossier(implementation: dict[str, Any]) -> str:
    lines = [
        "# M11L National Security Reviewed-Wording Implementation",
        "",
        "This implements the 18 exact human wording decisions as canonical reviewed wording for internal use only. Publication and production selection remain false.",
        "",
        "## Decision accounting",
        "",
        "- Accepted as written: 4",
        "- Accepted with bounded revision: 14",
        "- Rejected: 0",
        "- Unresolved: 0",
        "",
        "## Final reviewed wording",
        "",
    ]
    for record in implementation["subject"]["implementation_records"]:
        item = record["implemented_reviewed_wording"]
        lines.extend(
            [
                f"### `{item['wording_item_id']}`",
                "",
                f"- Decision: `{record['decision']}`",
                f"- Title: {item['public_title']}",
                f"- Primary: {item['primary_sentence']}",
                f"- Secondary: {item['secondary_clarification'] or 'None'}",
                f"- Evidence label: {item['evidence_count_label']}",
                "- Public limitations:",
            ]
        )
        lines.extend(
            f"  - {row['public_copy']}"
            for row in item["limitation_treatments"]
            if row["treatment"] == "retained_public_copy"
        )
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "The original M11K candidate objects remain embedded unchanged. Semantic sources, evidence, direction metadata, synthesis roles, blocked actions, and limitation identities are invariant. National Security publication, persistence, production selection, database writes, production writes, runtime changes, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build(check: bool = False) -> dict[str, Any]:
    package, template, m11k_parity, *_ = preflight()
    authority = build_authority(package, template, m11k_parity)
    implementation = build_implementation(authority, package)
    validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        parity=m11k_parity,
    )
    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
    authority_text = json_text(authority)
    implementation_text = json_text(implementation)
    dossier = render_dossier(implementation)
    entries = [
        {
            "path": AUTHORITY_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(authority_text),
            "content_subject_sha256": authority["authority_subject_sha256"],
        },
        {
            "path": IMPLEMENTATION_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(implementation_text),
            "content_subject_sha256": implementation["implementation_subject_sha256"],
        },
        {
            "path": DOSSIER_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(dossier),
            "content_subject_sha256": None,
        },
    ]
    parity = seal(
        {
            "schema_version": "full_record_public_wording_implementation_parity_v1",
            "artifact_id": PARITY_ID,
            "authority_binding": {
                "artifact_id": authority["artifact_id"],
                "authority_subject_sha256": authority["authority_subject_sha256"],
            },
            "implementation_binding": {
                "artifact_id": implementation["artifact_id"],
                "implementation_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
            "entries": entries,
        },
        "parity_subject_sha256",
    )
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    write_or_check(AUTHORITY_PATH, authority_text, check)
    write_or_check(IMPLEMENTATION_PATH, implementation_text, check)
    write_or_check(DOSSIER_PATH, dossier, check)
    write_or_check(PARITY_PATH, json_text(parity), check)
    return {"authority": authority, "implementation": implementation, "parity": parity}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.check)
    print(
        json.dumps(
            {
                "authority_id": result["authority"]["artifact_id"],
                "authority_subject_sha256": result["authority"][
                    "authority_subject_sha256"
                ],
                "implementation_id": result["implementation"]["artifact_id"],
                "implementation_subject_sha256": result["implementation"][
                    "implementation_subject_sha256"
                ],
                "parity_subject_sha256": result["parity"]["parity_subject_sha256"],
                "decision_accounting": result["authority"]["subject"][
                    "decision_accounting"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
