"""Build exact M13J Education & Workforce no-safe-synthesis acceptance."""

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

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.app.etl.full_record_synthesis_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m11j_national_security_synthesis_acceptance import (  # noqa: E402
    content_sha256,
    serialized,
    write_or_check,
)


ACCEPTED_M13I_PR = 168
ACCEPTED_M13I_HEAD = "bbdb50e790ce8e8f8f9c242c8b763c9b1503701e"
REVIEWED_BASE = "38a1e6faa4d766104009129ee699f8ad323bd078"
POST_M13I_MERGE_MAIN = "b69dae58112adbf90db31c4037ddfaffe1a09551"
REVIEWER_ID = "chatgpt:political_fingerprint_authority_thread"
REVIEWER_AUTHORITY = "full_record_synthesis_review_authority_v1"
REVIEW_DECISION = "approved_no_safe_synthesis_state"
DECISION_TIMESTAMP = "2026-08-24T21:35:00Z"

M13I_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_education_workforce_119_v1"
)
PACKAGE_PATH = M13I_ROOT / "synthesis_candidate_package.json"
TEMPLATE_PATH = M13I_ROOT / "human_synthesis_decision_template.json"
M13I_PARITY_PATH = M13I_ROOT / "parity_manifest.json"
M13H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_education_workforce_119_v1"
)
M13H_AUTHORITY_PATH = M13H_ROOT / "human_behavioral_semantic_ir_authority.json"
M13H_IMPLEMENTATION_PATH = (
    M13H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
M13H_PARITY_PATH = M13H_ROOT / "implementation_parity_manifest.json"
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_implementations/f000477_education_workforce_119_v1"
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

PACKAGE_ID = "synthesis-candidates:f000477:education_workforce:119:v1"
PACKAGE_FILE_SHA256 = "09f18212828e9dcbb31f75c1d80acfdee849519fb314fbd1cd64a426aebdefd3"
PACKAGE_SUBJECT_SHA256 = (
    "4c2d5270f4795b26ceca287f654a2e8973c022dfbcb983326f19a77c90a1406e"
)
TEMPLATE_ID = "human-synthesis-decision-template:f000477:education_workforce:119:v1"
TEMPLATE_FILE_SHA256 = (
    "867194246dce032fa73274224e5433d3222bce93245f68b3311fbc8354850d82"
)
TEMPLATE_SUBJECT_SHA256 = (
    "29970336bc866f215b0592bc54cfef37c59c23776f870468d5f5328af21d63f7"
)
M13I_PARITY_ID = "synthesis-candidate-parity:f000477:education_workforce:119:v1"
M13I_PARITY_FILE_SHA256 = (
    "170feeca382335c87ce41d3591978a02c6365380fbdaefcfed6d0c396024c7c3"
)
M13I_PARITY_SUBJECT_SHA256 = (
    "83f8c44f7b85021e4af90e40f42eb5e856a4cbab22500be787b6b399ab0f771f"
)
M13H_AUTHORITY_FILE_SHA256 = (
    "2a441ae485cc534677858bad82914781e94068e7d34ccd0ac95da4e4b5c55887"
)
M13H_AUTHORITY_SUBJECT_SHA256 = (
    "83e9cf85898d35e8f952db6e514e1495f5398e0bdc80a65824ab2777c8cac20c"
)
M13H_IMPLEMENTATION_FILE_SHA256 = (
    "30329ed2ca0b6d8f32b30d573858ebbc653c38f2280a6432410b8a5e491424a9"
)
M13H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "e9bdf0b1b365aa48f19b20d4f5c871bb5ad1f3aa47f2eaa035dea62be725f6c3"
)
M13H_PARITY_FILE_SHA256 = (
    "ac39a8ce1a4254eef41098df22540a06cdbfe1e28ed14a2f1473c7e6ca517acd"
)
M13H_PARITY_SUBJECT_SHA256 = (
    "c40134c79de66e75c23e8698835dfec9f7cb8dd626dbab1b50a0bd387345bdf5"
)

AUTHORITY_ID = "human-synthesis-authority:f000477:education_workforce:119:v1"
IMPLEMENTATION_ID = (
    "synthesis-decision-implementation:f000477:education_workforce:119:v1"
)
PARITY_ID = "synthesis-implementation-parity:f000477:education_workforce:119:v1"
PROPOSITION_IDS = {
    "pattern-education-relationship-triggered-funding-restriction-opposition",
    "notable-hr1048-amendment-support-final-passage-opposition",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def preflight() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    expected = {
        PACKAGE_PATH: PACKAGE_FILE_SHA256,
        TEMPLATE_PATH: TEMPLATE_FILE_SHA256,
        M13I_PARITY_PATH: M13I_PARITY_FILE_SHA256,
        M13H_AUTHORITY_PATH: M13H_AUTHORITY_FILE_SHA256,
        M13H_IMPLEMENTATION_PATH: M13H_IMPLEMENTATION_FILE_SHA256,
        M13H_PARITY_PATH: M13H_PARITY_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted input digest differs: {path.relative_to(ROOT)}")
    package = load(PACKAGE_PATH)
    template = load(TEMPLATE_PATH)
    behavioral_authority = load(M13H_AUTHORITY_PATH)
    behavioral_implementation = load(M13H_IMPLEMENTATION_PATH)
    if not (
        package["artifact_id"] == PACKAGE_ID
        and package["synthesis_candidate_package_subject_sha256"]
        == PACKAGE_SUBJECT_SHA256
        and package["subject"]["synthesis_candidates"] == []
        and package["subject"]["synthesis_candidate_count"] == 0
        and template["artifact_id"] == TEMPLATE_ID
        and template["decision_template_subject_sha256"] == TEMPLATE_SUBJECT_SHA256
        and template["candidate_decisions"] == []
        and behavioral_authority["authority_subject_sha256"]
        == M13H_AUTHORITY_SUBJECT_SHA256
        and behavioral_implementation["implementation_subject_sha256"]
        == M13H_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M13H/M13I identity or zero-candidate state differs")
    accounting = package["subject"]["complete_proposition_accounting"]
    if not (
        {row["proposition_id"] for row in accounting} == PROPOSITION_IDS
        and all(
            row["accounting_role"] == "intentionally_standalone_no_safe_synthesis"
            and row["candidate_relationships"] == []
            for row in accounting
        )
    ):
        raise ValueError("accepted standalone proposition accounting differs")
    return package, template, behavioral_authority, behavioral_implementation


def bindings() -> dict[str, Any]:
    return {
        "candidate_binding": {
            "artifact_id": PACKAGE_ID,
            "file_sha256": PACKAGE_FILE_SHA256,
            "candidate_subject_sha256": PACKAGE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_M13I_PR,
            "accepted_head": ACCEPTED_M13I_HEAD,
            "reviewed_base": REVIEWED_BASE,
            "post_merge_main": POST_M13I_MERGE_MAIN,
        },
        "decision_template_binding": {
            "artifact_id": TEMPLATE_ID,
            "file_sha256": TEMPLATE_FILE_SHA256,
            "decision_template_subject_sha256": TEMPLATE_SUBJECT_SHA256,
        },
        "synthesis_candidate_parity_binding": {
            "artifact_id": M13I_PARITY_ID,
            "file_sha256": M13I_PARITY_FILE_SHA256,
            "parity_subject_sha256": M13I_PARITY_SUBJECT_SHA256,
        },
        "accepted_behavioral_semantic_ir_authority_binding": {
            "artifact_id": "human-behavioral-semantic-ir-authority:f000477:education_workforce:119:v1",
            "file_sha256": M13H_AUTHORITY_FILE_SHA256,
            "authority_subject_sha256": M13H_AUTHORITY_SUBJECT_SHA256,
        },
        "accepted_behavioral_semantic_ir_implementation_binding": {
            "artifact_id": "behavioral-semantic-ir-decision-implementation:f000477:education_workforce:119:v1",
            "file_sha256": M13H_IMPLEMENTATION_FILE_SHA256,
            "implementation_subject_sha256": M13H_IMPLEMENTATION_SUBJECT_SHA256,
        },
        "accepted_behavioral_semantic_ir_parity_binding": {
            "file_sha256": M13H_PARITY_FILE_SHA256,
            "parity_subject_sha256": M13H_PARITY_SUBJECT_SHA256,
        },
    }


def build_authority(
    package: dict[str, Any], template: dict[str, Any]
) -> dict[str, Any]:
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
                    "issue_id": "EDUCATION_WORKFORCE",
                },
                "authority_decision": {
                    "reviewer_id": REVIEWER_ID,
                    "reviewer_authority": REVIEWER_AUTHORITY,
                    "decision": REVIEW_DECISION,
                    "decision_timestamp": DECISION_TIMESTAMP,
                },
                **bindings(),
                "synthesis_decisions": [],
                "decision_accounting": {
                    "accept_candidate_as_written": 0,
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
                "authority_effect": (
                    "canonical_internal_human_accepted_no_safe_synthesis"
                ),
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
                "implementation_records": [],
                "accepted_proposition_role_accounting": deepcopy(
                    package["subject"]["complete_proposition_accounting"]
                ),
                "accepted_episode_disposition_accounting": deepcopy(
                    package["subject"]["episode_disposition_accounting"]
                ),
                "candidate_overlap_accounting": [],
                "final_accounting": {
                    "canonical_internal_synthesis_count": 0,
                    "unique_behavioral_proposition_input_count": 0,
                    "candidate_episode_reference_count": 0,
                    "candidate_action_reference_count": 0,
                    "cross_candidate_episode_overlap_count": 0,
                    "cross_candidate_action_overlap_count": 0,
                    "standalone_proposition_count": 2,
                },
                "canonical_internal_synthesis_state": (
                    "human_accepted_no_safe_synthesis"
                ),
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            },
            "accepted_human_decisions_implemented": True,
            "canonical_internal_synthesis": True,
            "mechanical_review_state": (
                "validated_accepted_absence_by_independent_repository_validator"
            ),
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
    return f"""# M13J Education & Workforce No-Safe-Synthesis Acceptance

- Authority: `{AUTHORITY_ID}`
- Authority subject: `{authority["authority_subject_sha256"]}`
- Implementation: `{IMPLEMENTATION_ID}`
- Implementation subject: `{implementation["implementation_subject_sha256"]}`
- Package decision: `{REVIEW_DECISION}`
- Synthesis candidates / candidate decisions / implementation records: 0 / 0 / 0
- Standalone accepted Behavioral Semantic IR propositions: 2
- Canonical state: accepted absence of safe synthesis

The bounded funding-restriction opposition pattern and mixed H.R. 1048 notable
choice remain standalone. No relationship, placeholder synthesis, common
throughline, interpretive boundary, or other synthetic proposition was created.

H.R. 1005 remains non-directional Not Voting, H.R. 1049 remains contrast-only,
and eleven no-safe episodes remain outside synthesis. Public wording,
publication, persistence, database or production writes, and deployment remain
unauthorized.
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
    Draft7Validator(load(AUTHORITY_SCHEMA_PATH)).validate(authority)
    Draft7Validator(load(IMPLEMENTATION_SCHEMA_PATH)).validate(implementation)
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
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
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
        "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_file_sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "parity_id": PARITY_ID,
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        **implementation["subject"]["final_accounting"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
