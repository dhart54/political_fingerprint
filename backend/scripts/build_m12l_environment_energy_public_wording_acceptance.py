"""Build M12L Environment & Energy public-wording acceptance artifacts."""

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
    digest,
    seal,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import canonical_file_sha256  # noqa: E402

ACCEPTED_PR = 155
ACCEPTED_HEAD = "42a032ae4f6a8497e953e645c70e796b333c5920"
POST_M12K_MAIN = "fef90fd33aa1d3e838f2ac2a6cc366d3e5ef32cb"
APPROVED_AT_UTC = "2026-08-16T04:34:00Z"
REVIEWER = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_record_public_wording_review_authority_v1"

CANDIDATE_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_environment_energy_119_v1"
)
PACKAGE_PATH = CANDIDATE_ROOT / "public_wording_candidate_package.json"
TEMPLATE_PATH = CANDIDATE_ROOT / "human_public_wording_decision_template.json"
CANDIDATE_PARITY_PATH = CANDIDATE_ROOT / "parity_manifest.json"
PACKAGE_FILE_SHA256 = "805ac5a3231d5a611037a59d9cb38b80875c746bb16a4c8db307dd36a090af00"
PACKAGE_SUBJECT_SHA256 = (
    "4729332d5481ee9d0ef28cc393a875de875d9d7ccea6160a77e53a1f7218b231"
)
TEMPLATE_FILE_SHA256 = (
    "34206d07fedcc0bf70e3bb207e5c4eb784c35c5377097582f5a1e4d612c2c3c2"
)
TEMPLATE_SUBJECT_SHA256 = (
    "a61523d4765794a71b3ae8d8b3b718bd56f56030d3946ae8f0094f2277296a6f"
)
CANDIDATE_PARITY_FILE_SHA256 = (
    "774a415fc9ed0e46c78f7fa8cdff829af831fac685243d95bc20925b82019e07"
)
CANDIDATE_PARITY_SUBJECT_SHA256 = (
    "fbb3c0cfac631a53f4f9eec3ace2533af4ea8343677236f40cf0d617e27184bc"
)

SEMANTIC_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_environment_energy_119_v1"
)
SYNTHESIS_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_environment_energy_119_v1"
)
UPSTREAM_PATHS = {
    "behavioral_semantic_ir_authority_binding": SEMANTIC_ROOT
    / "human_behavioral_semantic_ir_authority.json",
    "behavioral_semantic_ir_implementation_binding": SEMANTIC_ROOT
    / "behavioral_semantic_ir_decision_implementation.json",
    "synthesis_authority_binding": SYNTHESIS_ROOT / "human_synthesis_authority.json",
    "synthesis_implementation_binding": SYNTHESIS_ROOT
    / "synthesis_decision_implementation.json",
}

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_implementations/f000477_environment_energy_119_v1"
)
AUTHORITY_PATH = OUTPUT_ROOT / "human_public_wording_authority.json"
IMPLEMENTATION_PATH = OUTPUT_ROOT / "reviewed_wording_decision_implementation.json"
DOSSIER_PATH = OUTPUT_ROOT / "implementation_dossier.md"
STATE_PATH = OUTPUT_ROOT / "current_state.json"
PARITY_PATH = OUTPUT_ROOT / "implementation_parity_manifest.json"
AUTHORITY_ID = "human-public-wording-authority:f000477:environment_energy:119:v1"
IMPLEMENTATION_ID = (
    "reviewed-wording-decision-implementation:f000477:environment_energy:119:v1"
)
PARITY_ID = "public-wording-implementation-parity:f000477:environment_energy:119:v1"

SCHEMAS = {
    "authority": ROOT
    / "docs/methodology/full_record_public_wording_authority_v1.schema.json",
    "implementation": ROOT
    / "docs/methodology/full_record_public_wording_decision_implementation_v1.schema.json",
    "parity": ROOT
    / "docs/methodology/full_record_public_wording_implementation_parity_v1.schema.json",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M12L artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    package, template, parity = (
        load(PACKAGE_PATH),
        load(TEMPLATE_PATH),
        load(CANDIDATE_PARITY_PATH),
    )
    checks = (
        canonical_file_sha256(PACKAGE_PATH) == PACKAGE_FILE_SHA256,
        package["public_wording_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256,
        canonical_file_sha256(TEMPLATE_PATH) == TEMPLATE_FILE_SHA256,
        template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256,
        canonical_file_sha256(CANDIDATE_PARITY_PATH) == CANDIDATE_PARITY_FILE_SHA256,
        parity["parity_subject_sha256"] == CANDIDATE_PARITY_SUBJECT_SHA256,
        len(template["wording_decisions"]) == 5
        and all(
            row["decision"] is None and row["bounded_revision"] is None
            for row in template["wording_decisions"]
        ),
    )
    if not all(checks):
        raise ValueError("accepted M12K identity or empty decision template differs")
    if len(package["subject"]["wording_items"]) != 5:
        raise ValueError("accepted M12K wording count differs")
    return package, template, parity


def bound_upstreams(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for name, path in UPSTREAM_PATHS.items():
        result[name] = {
            **package["subject"][name],
            "file_sha256": canonical_file_sha256(path),
        }
    return result


def build_authority(
    package: dict[str, Any], template: dict[str, Any], parity: dict[str, Any]
) -> dict[str, Any]:
    decisions = []
    for item in package["subject"]["wording_items"]:
        decisions.append(
            seal(
                {
                    "wording_item_id": item["wording_item_id"],
                    "original_wording_item_subject_sha256": item[
                        "wording_item_subject_sha256"
                    ],
                    "original_wording_item_content_sha256": digest(item),
                    "decision": "accept_candidate_as_written",
                    "bounded_revision": None,
                    "reviewer": REVIEWER,
                    "reviewer_authority": REVIEWER_AUTHORITY,
                    "reviewed_at_utc": APPROVED_AT_UTC,
                },
                "decision_subject_sha256",
            )
        )
    upstreams = bound_upstreams(package)
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
                "issue_id": "ENVIRONMENT_ENERGY",
                "congress": 119,
                "chamber": "House",
                "reviewer": REVIEWER,
                "reviewer_authority": REVIEWER_AUTHORITY,
                "approved_at_utc": APPROVED_AT_UTC,
                "base_binding": {
                    "accepted_m12k_pr": ACCEPTED_PR,
                    "accepted_m12k_head": ACCEPTED_HEAD,
                    "post_m12k_main": POST_M12K_MAIN,
                },
                "candidate_binding": {
                    "artifact_id": package["artifact_id"],
                    "file_sha256": PACKAGE_FILE_SHA256,
                    "package_subject_sha256": PACKAGE_SUBJECT_SHA256,
                },
                "decision_template_binding": {
                    "artifact_id": template["artifact_id"],
                    "file_sha256": TEMPLATE_FILE_SHA256,
                    "decision_template_subject_sha256": TEMPLATE_SUBJECT_SHA256,
                },
                "parity_binding": {
                    "artifact_id": parity["artifact_id"],
                    "file_sha256": CANDIDATE_PARITY_FILE_SHA256,
                    "parity_subject_sha256": CANDIDATE_PARITY_SUBJECT_SHA256,
                },
                **upstreams,
                "wording_decisions": decisions,
                "decision_accounting": {
                    "accept_candidate_as_written": 5,
                    "accept_with_bounded_revision": 0,
                    "rejected": 0,
                    "unresolved": 0,
                },
                "complete_source_accounting": deepcopy(
                    package["subject"]["source_accounting"]
                ),
                "complete_synthesis_role_accounting": deepcopy(
                    package["subject"]["complete_behavioral_synthesis_role_accounting"]
                ),
                "blocked_actions": [],
                "blocked_action_boundaries": [],
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
        records.append(
            seal(
                {
                    "schema_version": "full_record_public_wording_implementation_record_v1",
                    "record_id": f"reviewed-wording-decision-implementation:{item['wording_item_id']}:m12l:v1",
                    "wording_item_id": item["wording_item_id"],
                    "authority_artifact_id": authority["artifact_id"],
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                    "authority_decision_subject_sha256": decision[
                        "decision_subject_sha256"
                    ],
                    "decision": "accept_candidate_as_written",
                    "bounded_revision": None,
                    "original_candidate_content": deepcopy(item),
                    "original_candidate_content_sha256": digest(item),
                    "original_candidate_subject_sha256": item[
                        "wording_item_subject_sha256"
                    ],
                    "implemented_reviewed_wording": deepcopy(item),
                    "implemented_reviewed_wording_sha256": digest(item),
                    "canonical_reviewed_wording": True,
                    "public": False,
                    "production_selectable": False,
                    "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
                },
                "record_subject_sha256",
            )
        )
    upstream_names = (
        "behavioral_semantic_ir_authority_binding",
        "behavioral_semantic_ir_implementation_binding",
        "synthesis_authority_binding",
        "synthesis_implementation_binding",
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
                "candidate_binding": deepcopy(
                    authority["subject"]["candidate_binding"]
                ),
                **{
                    name: deepcopy(authority["subject"][name])
                    for name in upstream_names
                },
                "implementation_records": records,
                "complete_source_accounting": deepcopy(
                    authority["subject"]["complete_source_accounting"]
                ),
                "complete_synthesis_role_accounting": deepcopy(
                    authority["subject"]["complete_synthesis_role_accounting"]
                ),
                "blocked_actions": [],
                "blocked_action_boundaries": [],
                "final_accounting": {
                    "canonical_reviewed_wording_count": 5,
                    "surface_accounting": {
                        "issue_overview": 1,
                        "synthesis": 1,
                        "repeated_pattern": 3,
                    },
                    "decision_accounting": {
                        "accept_candidate_as_written": 5,
                        "accept_with_bounded_revision": 0,
                        "rejected": 0,
                        "unresolved": 0,
                    },
                },
                "canonical_reviewed_wording_present": True,
                "public": False,
                "production_selectable": False,
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
        },
        "implementation_subject_sha256",
    )


def dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    lines = [
        "# M12L Environment & Energy Public-Wording Acceptance",
        "",
        "All five independently reviewed M12K wording items are accepted as written with no bounded revision.",
        "",
        f"- Authority: `{authority['artifact_id']}`",
        f"- Implementation: `{implementation['artifact_id']}`",
        f"- Reviewer: `{REVIEWER}`",
        "- Accounting: `5 accept_candidate_as_written / 0 revised / 0 rejected / 0 unresolved`",
        "- Blocked actions and boundaries: `0 / 0`",
        "- Public and production selectable: `false / false`",
        "",
        "## Exact wording records",
        "",
    ]
    for record in implementation["subject"]["implementation_records"]:
        item = record["implemented_reviewed_wording"]
        lines += [
            f"### {item['public_title']}",
            "",
            f"- ID: `{item['wording_item_id']}`",
            f"- Surface: `{item['surface']}`",
            f"- Evidence: `{item['evidence_count_label']}`",
            "- Direction display: `null`",
            f"- Primary: {item['primary_sentence']}",
        ]
        if item["secondary_clarification"]:
            lines.append(f"- Clarification: {item['secondary_clarification']}")
        lines.append("")
    lines += [
        "## Boundary",
        "",
        "M12L establishes canonical reviewed wording for internal downstream use only. Publication, persistence, database writes, production writes, and deployment remain unauthorized.",
        "",
    ]
    return "\n".join(lines)


def build(check: bool = False) -> dict[str, Any]:
    package, template, candidate_parity = preflight()
    authority = build_authority(package, template, candidate_parity)
    implementation = build_implementation(authority, package)
    validate_implementation(
        implementation,
        authority=authority,
        package=package,
        decision_template=template,
        parity=candidate_parity,
    )
    Draft7Validator(load(SCHEMAS["authority"])).validate(authority)
    Draft7Validator(load(SCHEMAS["implementation"])).validate(implementation)
    dossier_text = dossier(authority, implementation)
    state = {
        "milestone": "M12L",
        "canonical_reviewed_wording": True,
        "wording_item_count": 5,
        "site_integration_candidate": False,
        "public": False,
        "production_selectable": False,
        "publication": False,
        "persistence": False,
        "database_writes": False,
        "production_writes": False,
        "deployment": False,
    }
    state_text = json_text(state)
    authority_text, implementation_text = (
        json_text(authority),
        json_text(implementation),
    )
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
            "entries": [
                {
                    "path": AUTHORITY_PATH.name,
                    "file_sha256": text_sha256(authority_text),
                    "content_subject_sha256": authority["authority_subject_sha256"],
                },
                {
                    "path": IMPLEMENTATION_PATH.name,
                    "file_sha256": text_sha256(implementation_text),
                    "content_subject_sha256": implementation[
                        "implementation_subject_sha256"
                    ],
                },
                {
                    "path": DOSSIER_PATH.name,
                    "file_sha256": text_sha256(dossier_text),
                    "content_subject_sha256": None,
                },
                {
                    "path": STATE_PATH.name,
                    "file_sha256": text_sha256(state_text),
                    "content_subject_sha256": None,
                },
            ],
        },
        "parity_subject_sha256",
    )
    Draft7Validator(load(SCHEMAS["parity"])).validate(parity)
    for path, content in (
        (AUTHORITY_PATH, authority_text),
        (IMPLEMENTATION_PATH, implementation_text),
        (DOSSIER_PATH, dossier_text),
        (STATE_PATH, state_text),
        (PARITY_PATH, json_text(parity)),
    ):
        write_or_check(path, content, check)
    return {"authority": authority, "implementation": implementation, "parity": parity}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    built = build(check=args.check)
    print(
        json.dumps(
            {
                "authority": built["authority"]["authority_subject_sha256"],
                "implementation": built["implementation"][
                    "implementation_subject_sha256"
                ],
                "parity": built["parity"]["parity_subject_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
