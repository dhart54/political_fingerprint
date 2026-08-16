from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation import (  # noqa: E402
    ActionInterpretationError,
    validate_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    load_json,
    sha256_json,
)
from backend.scripts.build_m12c_environment_energy_action_interpretation import (  # noqa: E402
    ARTIFACT_PATH,
    DECISION_PATH,
    DECISION_SCHEMA_PATH,
    DOSSIER_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M12B_MERGE_BASE,
    READINESS_PATH,
    SCHEMA_PATH,
    build_outputs,
)
from scripts.validate_m11c_national_security_action_interpretation import (  # noqa: E402
    validate_repository as validate_m11c,
)
from scripts.validate_m12a_universe_authority import (  # noqa: E402
    validate_repository as validate_m12a,
)
from scripts.validate_m12b_environment_energy_source_readiness import (  # noqa: E402
    validate_repository as validate_m12b,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"
EXPECTED_ARTIFACT_SHA256 = (
    "84713da4156f8a3f0347384225905351017bf21615ebcdca76e147aa2294b242"
)
EXPECTED_SUBJECT_SHA256 = (
    "e7a9b92d6d8972d3c01b052cbe85140ed449baf38ca2e5774ee58c322c03795c"
)
EXPECTED_DECISION_SHA256 = (
    "41105762b2d036829aec520772a38bfd65ba49d8941b11531278a5c6699db463"
)
EXPECTED_DOSSIER_SHA256 = (
    "bc3f25cb176abd3d46edf490900e7b54a91d3ebfc22ddcee6bbfeae3c9db888a"
)
EXPECTED_PARITY_SUBJECT_SHA256 = (
    "f427c932a62d679f17f04487b30c6c30b6ed1a0e2a2bfac2f66e5f4b084eec9a"
)
NON_DIRECTIONAL_ACTION_ID = "house:119:2:136"
BROAD_PACKAGE_ACTION_IDS = {"house:119:1:25", "house:119:1:330"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionInterpretationError(message)


def _validate_schema(value: dict[str, Any], path: Path, *, label: str) -> None:
    schema = load_json(path)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    _require(
        not errors, f"{label} schema failed: {errors[0].message if errors else ''}"
    )


def _validate_decision_template(artifact: dict[str, Any]) -> dict[str, Any]:
    decision = load_json(DECISION_PATH)
    _validate_schema(decision, DECISION_SCHEMA_PATH, label="M12C decision template")
    subject = decision["subject"]
    candidates = artifact["subject"]["candidates"]
    _require(
        decision["empty_non_authorizing_template"] is True, "decision template filled"
    )
    _require(
        subject["candidate_artifact_id"] == artifact["artifact_id"]
        and subject["candidate_interpretation_subject_sha256"]
        == artifact["interpretation_subject_sha256"]
        and subject["decision_count"] == len(candidates) == 63,
        "decision template candidate binding mismatch",
    )
    expected = {
        (
            candidate["action_id"],
            candidate["candidate_id"],
            candidate["candidate_content_subject_sha256"],
        )
        for candidate in candidates
    }
    recorded = {
        (
            item["action_id"],
            item["candidate_id"],
            item["candidate_content_subject_sha256"],
        )
        for item in subject["decisions"]
    }
    _require(recorded == expected, "decision template candidate digest mismatch")
    _require(
        all(
            item[field] is None
            for item in subject["decisions"]
            for field in (
                "decision",
                "reviewer_id",
                "reviewer_authority",
                "rationale",
                "decision_timestamp",
            )
        ),
        "decision template contains a human decision",
    )
    _require(
        sha256_json(subject) == decision["decision_template_subject_sha256"],
        "decision template subject digest mismatch",
    )
    return decision


def _validate_parity(artifact: dict[str, Any]) -> dict[str, Any]:
    parity = load_json(PARITY_PATH)
    _validate_schema(parity, PARITY_SCHEMA_PATH, label="M12C parity")
    subject = parity["subject"]
    _require(
        subject["candidate_artifact_id"] == artifact["artifact_id"]
        and subject["candidate_interpretation_subject_sha256"]
        == artifact["interpretation_subject_sha256"]
        and subject["candidate_count"] == 63
        and subject["blocked_count"] == 0
        and subject["json_markdown_substantive_parity"] is True,
        "parity manifest accounting mismatch",
    )
    expected_paths = {ARTIFACT_PATH, DECISION_PATH, DOSSIER_PATH}
    recorded_paths = {ROOT / item["path"] for item in subject["files"]}
    _require(recorded_paths == expected_paths, "parity file set mismatch")
    for item in subject["files"]:
        path = ROOT / item["path"]
        _require(
            canonical_file_sha256(path) == item["sha256"],
            f"parity file digest mismatch: {item['path']}",
        )
    _require(
        sha256_json(subject) == parity["parity_subject_sha256"],
        "parity subject digest mismatch",
    )
    return parity


def validate_repository() -> dict[str, Any]:
    m12a = validate_m12a()
    m12b = validate_m12b()
    m11c = validate_m11c()
    readiness = load_json(READINESS_PATH)
    artifact = load_json(ARTIFACT_PATH)
    _validate_schema(artifact, SCHEMA_PATH, label="M12C candidate")
    validate_candidate_artifact(
        artifact, readiness_artifact=readiness, repository_root=ROOT
    )
    subject = artifact["subject"]
    candidates = subject["candidates"]
    candidate_by_id = {item["action_id"]: item for item in candidates}
    aggregate = subject["aggregate"]

    _require(
        canonical_file_sha256(ARTIFACT_PATH) == EXPECTED_ARTIFACT_SHA256
        and artifact["interpretation_subject_sha256"] == EXPECTED_SUBJECT_SHA256,
        "M12C candidate identity mismatch",
    )
    _require(
        subject["post_source_readiness_merge_base"] == POST_M12B_MERGE_BASE,
        "post-M12B merge-base mismatch",
    )
    _require(
        subject["action_ids"] == readiness["subject"]["action_ids"]
        and len(subject["action_ids"]) == len(candidates) == 63
        and not subject["blocked_action_ids"],
        "63/63 candidate accounting mismatch",
    )
    _require(
        aggregate
        == {
            "approved_universe_count": 63,
            "interpretation_eligible_count": 63,
            "candidate_count": 63,
            "source_blocked_count": 0,
            "evidence_source_binding_count": 189,
            "unique_evidence_source_count": 189,
            "candidate_status_counts": {
                "proposed": 36,
                "proposed_with_material_limitation": 27,
            },
            "coverage_assessment_counts": {
                "bounded_official_purpose_summary": 61,
                "package_level_bounded_summary": 2,
            },
            "member_action_counts": {"nay": 47, "not_voting": 1, "yea": 15},
            "position_effect_counts": {
                "non_directional_not_voting": 1,
                "opposes_exact_choice": 47,
                "supports_exact_choice": 15,
            },
        },
        "M12C aggregate mismatch",
    )
    non_directional = candidate_by_id[NON_DIRECTIONAL_ACTION_ID]
    _require(
        non_directional["official_member_action"] == "not_voting"
        and non_directional["proposed_member_position_effect"]
        == "non_directional_not_voting",
        "non-directional action was made directional",
    )
    broad = {
        item["action_id"]
        for item in candidates
        if item["coverage_assessment"] == "package_level_bounded_summary"
    }
    structured = {
        item["action_id"]
        for item in candidates
        if item["official_title_or_purpose"]["locator"]
        == "structured_operative_summary"
    }
    _require(broad == BROAD_PACKAGE_ACTION_IDS, "broad-package class mismatch")
    _require(not structured, "unexpected structured-summary candidate")
    _require(
        all(
            "whole-package choice"
            in " ".join(candidate_by_id[action_id]["limitations"])
            for action_id in broad
        ),
        "broad-package component boundary missing",
    )
    _require(
        m12a["approved_action_count"] == 63
        and m12a["approved_action_set_sha256"]
        == "843740a27ef191294bcf0cc3d2b29aeda1751351d775f8fadd7f44708e2312c8"
        and m12b["artifact_sha256"]
        == "ebdb1ba1a3fc40394ebd108e229a885a27eaadd964151a0843fa64e8c5e947ba"
        and m12b["ready_count"] == 63
        and m12b["blocked_count"] == 0,
        "M12A/M12B authority or readiness changed",
    )
    _require(
        m11c["artifact_sha256"]
        == "6d3c0c26d56b7ace999debbc45efc0945f27320425b0f2bda55aca013630543d"
        and m11c["candidate_count"] == 81
        and m11c["blocked_count"] == 1,
        "accepted M11C regression changed",
    )

    decision = _validate_decision_template(artifact)
    parity = _validate_parity(artifact)
    _require(
        canonical_file_sha256(DECISION_PATH) == EXPECTED_DECISION_SHA256
        and canonical_file_sha256(DOSSIER_PATH) == EXPECTED_DOSSIER_SHA256
        and parity["parity_subject_sha256"] == EXPECTED_PARITY_SUBJECT_SHA256,
        "M12C review artifact digest mismatch",
    )
    rebuilt = build_outputs()
    for path, content in rebuilt.items():
        _require(
            path.is_file() and path.read_bytes().replace(b"\r\n", b"\n") == content,
            f"deterministic regeneration mismatch: {path.relative_to(ROOT)}",
        )

    current = load_json(CURRENT_STATE_PATH)
    m12b_state = current["active_source_readiness_milestone"]
    m12c_state = current["active_m12c_action_interpretation_milestone"]
    _require(
        m12b_state["milestone_state"] == "completed_independent_review_accepted"
        and m12b_state["accepted_pr"] == 150
        and m12b_state["accepted_head"] == "2973fc234de292ed6e61cadca966fcc2f586ca4f"
        and m12b_state["post_merge_main"] == POST_M12B_MERGE_BASE,
        "M12B accepted checkpoint state mismatch",
    )
    _require(
        m12c_state["milestone"] == "m12c_environment_energy_action_interpretation_v1"
        and m12c_state["milestone_state"]
        == "complete_pending_independent_semantic_review"
        and m12c_state["approved_universe_count"] == 63
        and m12c_state["candidate_count"] == 63
        and m12c_state["action_meaning_state"]
        == "not_accepted_candidates_pending_human_review"
        and m12c_state["candidate_identity"]["sha256"]
        == canonical_file_sha256(ARTIFACT_PATH)
        and m12c_state["candidate_identity"]["interpretation_subject_sha256"]
        == artifact["interpretation_subject_sha256"]
        and all(
            value is False for value in m12c_state["downstream_authorizations"].values()
        ),
        "M12C current-state boundary mismatch",
    )
    _require(
        all(value is False for value in subject["downstream_authorizations"].values())
        and all(
            value is False
            for value in decision["subject"]["downstream_authorizations"].values()
        ),
        "downstream authority became true",
    )

    return {
        "status": "pass",
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": canonical_file_sha256(ARTIFACT_PATH),
        "interpretation_subject_sha256": artifact["interpretation_subject_sha256"],
        "decision_template_sha256": canonical_file_sha256(DECISION_PATH),
        "dossier_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "candidate_count": len(candidates),
        "blocked_count": 0,
        "non_directional_action_id": NON_DIRECTIONAL_ACTION_ID,
        "broad_package_action_ids": sorted(broad),
        "structured_summary_action_ids": sorted(structured),
        "aggregate": aggregate,
    }


def main() -> int:
    try:
        print(json.dumps(validate_repository(), sort_keys=True))
    except (ActionInterpretationError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
