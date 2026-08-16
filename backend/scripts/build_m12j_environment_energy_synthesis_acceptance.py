"""Build exact M12J Environment & Energy synthesis acceptance."""

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
    digest,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m11j_national_security_synthesis_acceptance import (  # noqa: E402
    content_sha256,
    serialized,
    write_or_check,
)


ACCEPTED_M12I_PR = 154
ACCEPTED_M12I_HEAD = "95a7c59cd1876c7934fea9547008e2b8e86e8be0"
REVIEWED_BASE = "d3bc0fddad701e0621c87857ed80288c23a867aa"
POST_M12I_MERGE_MAIN = "ea6b93cd51110dd2e8da71448ce2a5b14f864ba3"
REVIEWER_ID = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_record_synthesis_review_authority_v1"
DECISION_TIMESTAMP = "2026-08-16T03:40:00Z"

M12I_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_environment_energy_119_v1"
)
PACKAGE_PATH = M12I_ROOT / "synthesis_candidate_package.json"
TEMPLATE_PATH = M12I_ROOT / "human_synthesis_decision_template.json"
M12I_PARITY_PATH = M12I_ROOT / "parity_manifest.json"
M12H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_environment_energy_119_v1"
)
M12H_AUTHORITY_PATH = M12H_ROOT / "human_behavioral_semantic_ir_authority.json"
M12H_IMPLEMENTATION_PATH = (
    M12H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
M12H_PARITY_PATH = M12H_ROOT / "implementation_parity_manifest.json"
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_environment_energy_119_v1"
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

PACKAGE_ID = "synthesis-candidates:f000477:environment_energy:119:v1"
PACKAGE_FILE_SHA256 = "d6518f33bffacc4b2953e967098979d39cb5bb19e1b995a5376831e8cd69e378"
PACKAGE_SUBJECT_SHA256 = (
    "df5d7209f7cc08b80e6164a5952fa08549e0dc9b6b4627db8d6fe2a7fc7cddae"
)
TEMPLATE_ID = "human-synthesis-decision-template:f000477:environment_energy:119:v1"
TEMPLATE_FILE_SHA256 = (
    "1e8eaff4d410d11942fc6bd1b57aed05957e720b4d2b7b9dc74f68f17fb0114c"
)
TEMPLATE_SUBJECT_SHA256 = (
    "b3f8f69f5cdb357b4f84c29af423162138c5128328a0d9cfe0898edb8ef66f1f"
)
M12I_PARITY_ID = "synthesis-candidate-parity:f000477:environment_energy:119:v1"
M12I_PARITY_FILE_SHA256 = (
    "f93435edb5fa347310a089366993ae57a51c86daf3ec344a56a9b9fa7cb38b8f"
)
M12I_PARITY_SUBJECT_SHA256 = (
    "f9fd4cf93d403d600fa1c55921275be25ca713e30f6d260c4a704c5d9998dc21"
)
M12H_AUTHORITY_FILE_SHA256 = (
    "eb6388827648aaa6ee6cabda3e45cf0c93f35116a6f97e9540263dec7ae7c4af"
)
M12H_AUTHORITY_SUBJECT_SHA256 = (
    "31b26aa0a671a3ffb5226a26862df3bca10de3aee93a795d92cfc3abe26be276"
)
M12H_IMPLEMENTATION_FILE_SHA256 = (
    "ae403e7334f02f4135e857d4663efa79a75540648184a444572138f1812da491"
)
M12H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "8621aecaafc8352c31b16284ed6acde9d0d290f3e345af41ec6e231d774c9c32"
)
M12H_PARITY_FILE_SHA256 = (
    "0b03010e8038c7cce45cdc97b39e725329d807279a0ebf2bc50956aa4b5f431a"
)
M12H_PARITY_SUBJECT_SHA256 = (
    "ef8fbbb4b7a15a03518f140a47e9d57d7a2690b19e5d4a60ce24ed350325da04"
)

AUTHORITY_ID = "human-synthesis-authority:f000477:environment_energy:119:v1"
IMPLEMENTATION_ID = (
    "synthesis-decision-implementation:f000477:environment_energy:119:v1"
)
PARITY_ID = "synthesis-implementation-parity:f000477:environment_energy:119:v1"
CANDIDATE_ID = "synthesis-congressional-disapproval-uniform-opposition"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    expected = {
        PACKAGE_PATH: PACKAGE_FILE_SHA256,
        TEMPLATE_PATH: TEMPLATE_FILE_SHA256,
        M12I_PARITY_PATH: M12I_PARITY_FILE_SHA256,
        M12H_AUTHORITY_PATH: M12H_AUTHORITY_FILE_SHA256,
        M12H_IMPLEMENTATION_PATH: M12H_IMPLEMENTATION_FILE_SHA256,
        M12H_PARITY_PATH: M12H_PARITY_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    package = load(PACKAGE_PATH)
    template = load(TEMPLATE_PATH)
    behavioral_authority = load(M12H_AUTHORITY_PATH)
    behavioral_implementation = load(M12H_IMPLEMENTATION_PATH)
    if not (
        package["artifact_id"] == PACKAGE_ID
        and package["synthesis_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256
        and template["artifact_id"] == TEMPLATE_ID
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and behavioral_authority["authority_subject_sha256"]
        == M12H_AUTHORITY_SUBJECT_SHA256
        and behavioral_implementation["implementation_subject_sha256"]
        == M12H_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M12H/M12I identity differs")
    return package, template, behavioral_authority, behavioral_implementation


def bindings() -> dict[str, Any]:
    return {
        "candidate_binding": {
            "artifact_id": PACKAGE_ID,
            "file_sha256": PACKAGE_FILE_SHA256,
            "candidate_subject_sha256": PACKAGE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M12I_PR,
            "accepted_head": ACCEPTED_M12I_HEAD,
            "reviewed_base": REVIEWED_BASE,
            "post_merge_main": POST_M12I_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": TEMPLATE_ID,
            "file_sha256": TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": TEMPLATE_SUBJECT_SHA256,
        },
        "synthesis_candidate_parity_binding": {
            "artifact_id": M12I_PARITY_ID,
            "file_sha256": M12I_PARITY_FILE_SHA256,
            "parity_subject_sha256": M12I_PARITY_SUBJECT_SHA256,
        },
        "accepted_behavioral_semantic_ir_authority_binding": {
            "artifact_id": "human-behavioral-semantic-ir-authority:f000477:environment_energy:119:v1",
            "file_sha256": M12H_AUTHORITY_FILE_SHA256,
            "authority_subject_sha256": M12H_AUTHORITY_SUBJECT_SHA256,
        },
        "accepted_behavioral_semantic_ir_implementation_binding": {
            "artifact_id": "behavioral-semantic-ir-decision-implementation:f000477:environment_energy:119:v1",
            "file_sha256": M12H_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M12H_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "accepted_behavioral_semantic_ir_parity_binding": {
            "file_sha256": M12H_PARITY_FILE_SHA256,
            "parity_subject_sha256": M12H_PARITY_SUBJECT_SHA256,
        },
    }


def build_authority(
    package: dict[str, Any], template: dict[str, Any]
) -> dict[str, Any]:
    candidates = package["subject"]["synthesis_candidates"]
    if len(candidates) != 1 or candidates[0]["synthesis_candidate_id"] != CANDIDATE_ID:
        raise ValueError("exact accepted synthesis candidate set differs")
    candidate = candidates[0]
    decision = seal(
        {
            "synthesis_candidate_id": CANDIDATE_ID,
            "original_candidate_subject_sha256": candidate[
                "synthesis_candidate_subject_sha256"
            ],
            "original_candidate_content_sha256": digest(candidate),
            "decision": "accept_candidate_as_written",
            "bounded_revision": None,
            "reviewer_id": REVIEWER_ID,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision_timestamp": DECISION_TIMESTAMP,
        },
        "decision_subject_sha256",
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
                    "issue_id": "ENVIRONMENT_ENERGY",
                },
                "authority_decision": {
                    "reviewer_id": REVIEWER_ID,
                    "reviewer_authority": REVIEWER_AUTHORITY,
                    "decision": "approved_all_synthesis_candidates_as_written",
                    "decision_timestamp": DECISION_TIMESTAMP,
                },
                **bindings(),
                "synthesis_decisions": [decision],
                "decision_accounting": {
                    "accept_candidate_as_written": 1,
                    "accept_with_bounded_revision": 0,
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
    behavioral_authority: dict[str, Any],
    behavioral_implementation: dict[str, Any],
) -> dict[str, Any]:
    original = package["subject"]["synthesis_candidates"][0]
    decision = authority["subject"]["synthesis_decisions"][0]
    source_records = {
        row["proposition_id"]: row
        for row in behavioral_implementation["subject"]["implementation_records"]
    }
    lineage = []
    for binding in original["input_bindings"]:
        source = source_records[binding["proposition_id"]]
        lineage.append(
            {
                "proposition_id": binding["proposition_id"],
                "relationship_role": binding["relationship_role"],
                "accepted_behavioral_semantic_ir_record_id": source["record_id"],
                "accepted_behavioral_semantic_ir_record_subject_sha256": source[
                    "record_subject_sha256"
                ],
                "accepted_candidate_content_sha256": source[
                    "accepted_candidate_content_sha256"
                ],
                "evidence_episode_ids": binding["evidence_episode_ids"],
                "evidence_action_ids": binding["evidence_action_ids"],
            }
        )
    record = seal(
        {
            "schema_version": "full_record_synthesis_implementation_record_v1",
            "record_id": f"synthesis-decision-implementation:{CANDIDATE_ID}:m12j:v1",
            "synthesis_candidate_id": CANDIDATE_ID,
            "authority_decision_subject_sha256": decision["decision_subject_sha256"],
            "decision": "accept_candidate_as_written",
            "original_candidate_content": deepcopy(original),
            "original_candidate_content_sha256": digest(original),
            "original_candidate_subject_sha256": original[
                "synthesis_candidate_subject_sha256"
            ],
            "bounded_revision": None,
            "implemented_synthesis_content": deepcopy(original),
            "implemented_synthesis_content_sha256": digest(original),
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
                "implementation_records": [record],
                "accepted_proposition_role_accounting": deepcopy(
                    package["subject"]["complete_proposition_accounting"]
                ),
                "accepted_episode_disposition_accounting": deepcopy(
                    package["subject"]["episode_disposition_accounting"]
                ),
                "candidate_overlap_accounting": deepcopy(
                    package["subject"]["candidate_overlap_accounting"]
                ),
                "final_accounting": {
                    "canonical_internal_synthesis_count": 1,
                    "unique_behavioral_proposition_input_count": 3,
                    "candidate_episode_reference_count": 13,
                    "candidate_action_reference_count": 13,
                    "cross_candidate_episode_overlap_count": 0,
                    "cross_candidate_action_overlap_count": 0,
                    "standalone_proposition_count": 0,
                },
                "canonical_internal_synthesis_state": "human_authority_implemented_and_validated",
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
            "accepted_human_decisions_implemented": True,
            "canonical_internal_synthesis": True,
            "mechanical_review_state": "validated_by_independent_repository_validator",
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
        accepted_behavioral_semantic_ir_authority=behavioral_authority,
        accepted_behavioral_semantic_ir_implementation=behavioral_implementation,
    )
    return implementation


def dossier(authority: dict[str, Any], implementation: dict[str, Any]) -> str:
    proposition = implementation["subject"]["implementation_records"][0][
        "implemented_synthesis_content"
    ]["proposition"]
    return f"""# M12J Environment & Energy Synthesis Acceptance

- Authority: `{AUTHORITY_ID}`
- Authority subject: `{authority["authority_subject_sha256"]}`
- Implementation: `{IMPLEMENTATION_ID}`
- Implementation subject: `{implementation["implementation_subject_sha256"]}`
- Decision: one `accept_candidate_as_written`; no bounded revision
- Inputs: three accepted Behavioral Semantic IR propositions
- Deduplicated lineage: 13 episodes / 13 actions
- Complete episode dispositions: 13 primary, 25 contrast-only, 24 no-safe, 1 unused non-directional

## Canonical internal synthesis

{proposition}

The complete reviewed candidate object, including its candidate-era unresolved
ambiguity and authority fields, is preserved unchanged. M12J establishes
canonical internal synthesis only. Public wording, publication, persistence,
database or production writes, and deployment remain unauthorized.
"""


def build(*, check: bool = False) -> dict[str, Any]:
    package, template, behavioral_authority, behavioral_implementation = preflight()
    authority = build_authority(package, template)
    implementation = build_implementation(
        package,
        template,
        authority,
        behavioral_authority,
        behavioral_implementation,
    )
    authority_schema = load(AUTHORITY_SCHEMA_PATH)
    implementation_schema = load(IMPLEMENTATION_SCHEMA_PATH)
    parity_schema = load(PARITY_SCHEMA_PATH)
    Draft7Validator(authority_schema).validate(authority)
    Draft7Validator(implementation_schema).validate(implementation)
    parity = seal(
        {
            "schema_version": "full_record_synthesis_implementation_parity_v1",
            "artifact_id": PARITY_ID,
            "authority_binding": {
                "artifact_id": AUTHORITY_ID,
                "file_sha256": content_sha256(serialized(authority)),
                "authority_subject_sha256": authority["authority_subject_sha256"],
            },
            "implementation_binding": {
                "artifact_id": IMPLEMENTATION_ID,
                "file_sha256": content_sha256(serialized(implementation)),
                "implementation_subject_sha256": implementation[
                    "implementation_subject_sha256"
                ],
            },
            "upstream_candidate_subject_sha256": PACKAGE_SUBJECT_SHA256,
            "decision_accounting": authority["subject"]["decision_accounting"],
            "final_accounting": implementation["subject"]["final_accounting"],
            "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
        },
        "parity_subject_sha256",
    )
    Draft7Validator(parity_schema).validate(parity)
    outputs = {
        AUTHORITY_PATH: serialized(authority),
        IMPLEMENTATION_PATH: serialized(implementation),
        PARITY_PATH: serialized(parity),
        DOSSIER_PATH: dossier(authority, implementation),
    }
    for path, content in outputs.items():
        write_or_check(path, content, check=check)
    return {
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": content_sha256(serialized(authority)),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_file_sha256": content_sha256(serialized(implementation)),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_id": PARITY_ID,
        "parity_file_sha256": content_sha256(serialized(parity)),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "dossier_file_sha256": content_sha256(dossier(authority, implementation)),
        "decision_accounting": authority["subject"]["decision_accounting"],
        "final_accounting": implementation["subject"]["final_accounting"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
