"""Independently validate the detached M11I synthesis candidate package."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (  # noqa: E402
    verify_seal,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.app.etl.full_record_synthesis_candidates import (  # noqa: E402
    validate_synthesis_candidate_package,
)
from backend.scripts.build_m11i_national_security_synthesis_candidates import (  # noqa: E402
    ACCEPTED_M11H_HEAD,
    ACCEPTED_M11H_PR,
    DECISION_SCHEMA_PATH,
    DECISION_TEMPLATE_PATH,
    DOSSIER_PATH,
    M11H_AUTHORITY_FILE_SHA256,
    M11H_AUTHORITY_ID,
    M11H_AUTHORITY_PATH,
    M11H_AUTHORITY_SUBJECT_SHA256,
    M11H_IMPLEMENTATION_FILE_SHA256,
    M11H_IMPLEMENTATION_ID,
    M11H_IMPLEMENTATION_PATH,
    M11H_IMPLEMENTATION_SUBJECT_SHA256,
    M11H_PARITY_SUBJECT_SHA256,
    PACKAGE_PATH,
    PACKAGE_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11H_MERGE_MAIN,
    build,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"


class M11IValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise M11IValidationError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_repository() -> dict[str, Any]:
    build(check=True)
    package = load(PACKAGE_PATH)
    decision = load(DECISION_TEMPLATE_PATH)
    parity = load(PARITY_PATH)
    authority = load(M11H_AUTHORITY_PATH)
    implementation = load(M11H_IMPLEMENTATION_PATH)
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    Draft7Validator(load(DECISION_SCHEMA_PATH)).validate(decision)
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    generic = validate_synthesis_candidate_package(
        package,
        authority=authority,
        implementation=implementation,
    )
    require(
        authority["artifact_id"] == M11H_AUTHORITY_ID
        and canonical_file_sha256(M11H_AUTHORITY_PATH) == M11H_AUTHORITY_FILE_SHA256
        and authority["authority_subject_sha256"] == M11H_AUTHORITY_SUBJECT_SHA256,
        "accepted M11H authority differs",
    )
    require(
        implementation["artifact_id"] == M11H_IMPLEMENTATION_ID
        and canonical_file_sha256(M11H_IMPLEMENTATION_PATH)
        == M11H_IMPLEMENTATION_FILE_SHA256
        and implementation["implementation_subject_sha256"]
        == M11H_IMPLEMENTATION_SUBJECT_SHA256,
        "accepted M11H implementation differs",
    )
    subject = package["subject"]
    require(
        subject["base_binding"]
        == {
            "accepted_m11h_pr": ACCEPTED_M11H_PR,
            "accepted_m11h_head": ACCEPTED_M11H_HEAD,
            "post_m11h_merge_main": POST_M11H_MERGE_MAIN,
        },
        "post-M11H base binding differs",
    )
    require(
        subject["accepted_m11h_file_bindings"]
        == {
            "authority_file_sha256": M11H_AUTHORITY_FILE_SHA256,
            "implementation_file_sha256": M11H_IMPLEMENTATION_FILE_SHA256,
            "parity_subject_sha256": M11H_PARITY_SUBJECT_SHA256,
        },
        "accepted M11H file binding differs",
    )
    candidates = {
        row["synthesis_candidate_id"]: row for row in subject["synthesis_candidates"]
    }
    require(
        set(candidates)
        == {
            "synthesis-war-powers-cross-target-uniform-direction",
            "synthesis-security-assistance-interpretive-boundary",
        },
        "M11I synthesis candidate set differs",
    )
    war = candidates["synthesis-war-powers-cross-target-uniform-direction"]
    assistance = candidates["synthesis-security-assistance-interpretive-boundary"]
    require(
        war["synthesis_type"] == "uniform_direction"
        and war["direction"] == "support"
        and war["underlying_evidence"]["unique_episode_count"] == 10
        and war["relationships"]["supported_by"]
        == [
            "pattern-iran-war-powers-removal-support",
            "pattern-lebanon-war-powers-removal-support",
            "pattern-venezuela-war-powers-removal-support",
        ]
        and war["relationships"]["contextualized_by"]
        == ["notable-aumf-repeal-1991-2002"],
        "War Powers synthesis candidate differs",
    )
    require(
        assistance["synthesis_type"] == "interpretive_boundary"
        and assistance["direction"] == "mixed"
        and assistance["underlying_evidence"]["unique_episode_count"] == 8
        and assistance["relationships"]["supported_by"]
        == [
            "pattern-ukraine-assistance-mixed",
            "pattern-jordan-assistance-restriction-opposition",
        ]
        and assistance["relationships"]["contextualized_by"]
        == ["notable-taiwan-security-cooperation-funding"]
        and assistance["relationships"]["contrasted_by"]
        == ["notable-israel-foreign-military-financing-reduction"],
        "security-assistance synthesis candidate differs",
    )
    require(
        subject["source_behavioral_proposition_count"] == 15
        and len(subject["complete_proposition_accounting"]) == 15
        and subject["proposition_accounting_counts"]
        == {
            "contextual_input": 2,
            "contrast_input": 1,
            "intentionally_standalone_no_safe_synthesis": 7,
            "primary_input": 5,
        },
        "complete 15-proposition synthesis-role accounting differs",
    )
    require(
        subject["candidate_overlap_accounting"]
        == [
            {
                "left_candidate_id": "synthesis-war-powers-cross-target-uniform-direction",
                "right_candidate_id": "synthesis-security-assistance-interpretive-boundary",
                "shared_proposition_ids": [],
                "shared_episode_ids": [],
                "overlap_state": "no_overlap",
                "overlap_does_not_create_independent_evidence": True,
            }
        ],
        "candidate overlap accounting differs",
    )
    require(
        len(subject["accepted_episode_disposition_ledger"]) == 81
        and subject["episode_disposition_accounting"]["contrast_only_episode_count"]
        == 24
        and subject["episode_disposition_accounting"][
            "no_safe_proposition_episode_count"
        ]
        == 25,
        "accepted M11H episode ledger differs",
    )
    require(
        decision["candidate_binding"]["synthesis_candidate_package_subject_sha256"]
        == package["synthesis_candidate_package_subject_sha256"]
        and all(row["decision"] is None for row in decision["candidate_decisions"])
        and decision["authorizing"] is False
        and not any(decision["downstream_authorizations"].values()),
        "empty non-authorizing decision template differs",
    )
    verify_seal(parity, "parity_subject_sha256", "M11I parity")
    expected_paths = {PACKAGE_PATH, DECISION_TEMPLATE_PATH, DOSSIER_PATH}
    parity_paths = {PACKAGE_PATH.parent / row["path"] for row in parity["entries"]}
    require(parity_paths == expected_paths, "M11I parity file set differs")
    for row in parity["entries"]:
        path = PACKAGE_PATH.parent / row["path"]
        require(
            canonical_file_sha256(path) == row["file_sha256"],
            f"M11I parity file digest differs: {path.name}",
        )
    state = load(CURRENT_STATE_PATH)
    milestone = state["active_synthesis_candidate_milestone"]
    require(
        milestone["milestone"] == "m11i_national_security_synthesis_candidates_v1"
        and milestone["post_m11h_merge_base"] == POST_M11H_MERGE_MAIN
        and milestone["candidate_count"] == 2
        and milestone["source_behavioral_proposition_count"] == 15
        and milestone["synthesis_state"]
        == "human_decisions_implemented_by_m11j_pending_mechanical_review"
        and milestone["accepted_head"] == "8535163aee1d2a548ec7d0c23935b1322a05b863"
        and milestone["post_merge_main"] == "e9e771b23eb65629e0a3ed7ecb6c32748d7ebf59"
        and not any(milestone["downstream_authorizations"].values()),
        "M11I current-state boundary differs",
    )
    return {
        **generic,
        "package_file_sha256": canonical_file_sha256(PACKAGE_PATH),
        "package_subject_sha256": package["synthesis_candidate_package_subject_sha256"],
        "decision_template_file_sha256": canonical_file_sha256(DECISION_TEMPLATE_PATH),
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "war_powers_unique_episode_count": 10,
        "assistance_unique_episode_count": 8,
        "downstream_authorizations_false": True,
    }


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
