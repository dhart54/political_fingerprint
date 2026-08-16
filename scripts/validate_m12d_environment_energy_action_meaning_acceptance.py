from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation_decisions import (  # noqa: E402
    ACCEPTED_DECISION,
    DOWNSTREAM_AUTHORIZATIONS,
    validate_authority_record,
    validate_implementation_bundle,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    sha256_json,
)
from backend.scripts.build_m12d_environment_energy_action_meaning_acceptance import (  # noqa: E402
    ACCEPTED_CANDIDATE_FILE_SHA256,
    ACCEPTED_CANDIDATE_SUBJECT_SHA256,
    ACCEPTED_HEAD,
    ACCEPTED_PR,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    DECISION_TIMESTAMP,
    DOSSIER_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M12C_MERGE_MAIN,
    REVIEWER_AUTHORITY,
    REVIEWER_IDENTITY,
    CANDIDATE_PATH,
    write_outputs,
)

M11_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions"
    / "f000477_national_security_foreign_119_v1"
)
M11_AUTHORITY_PATH = M11_ROOT / "human_action_meaning_authority.json"
M11_IMPLEMENTATION_PATH = M11_ROOT / "decision_implementation_bundle.json"
M11_PARITY_PATH = M11_ROOT / "implementation_parity_manifest.json"
M11_AUTHORITY_FILE_SHA256 = (
    "b67fc818a59e441055a6b6ca32ee0f09cc91c0eec1ec99e6d4f6cd61499cc544"
)
M11_AUTHORITY_SUBJECT_SHA256 = (
    "cde23f35cf8f876909dc5e7b779dbb600f919dc4aaa36dcd37cd08aecbacfa82"
)
M11_IMPLEMENTATION_FILE_SHA256 = (
    "402928780286f98fec90242132a829058f57517328c532e60371afab3c2173ff"
)
M11_IMPLEMENTATION_SUBJECT_SHA256 = (
    "360f0ce47d52cb5a0d0234a88026411e94697c38cac9fca8dc87a7db6ad9ad5b"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_schema(schema_path: Path, value: dict[str, Any]) -> None:
    errors = list(Draft7Validator(load(schema_path)).iter_errors(value))
    require(not errors, f"{schema_path.name}: {errors[0].message if errors else ''}")


def validate_repository() -> dict[str, Any]:
    candidate = load(CANDIDATE_PATH)
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    parity = load(PARITY_PATH)
    validate_authority_record(authority, candidate_artifact=candidate)
    validate_implementation_bundle(
        implementation, authority=authority, candidate_artifact=candidate
    )
    for schema_path, value in (
        (AUTHORITY_SCHEMA_PATH, authority),
        (IMPLEMENTATION_SCHEMA_PATH, implementation),
        (PARITY_SCHEMA_PATH, parity),
    ):
        validate_schema(schema_path, value)

    subject = authority["subject"]
    binding = subject["input_bindings"]["candidate_artifact"]
    require(
        canonical_file_sha256(CANDIDATE_PATH) == ACCEPTED_CANDIDATE_FILE_SHA256
        and candidate["interpretation_subject_sha256"]
        == ACCEPTED_CANDIDATE_SUBJECT_SHA256,
        "accepted M12C identity differs",
    )
    require(
        binding
        == {
            "artifact_id": candidate["artifact_id"],
            "file_sha256": ACCEPTED_CANDIDATE_FILE_SHA256,
            "interpretation_subject_sha256": ACCEPTED_CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_PR,
            "accepted_head": ACCEPTED_HEAD,
            "post_merge_main": POST_M12C_MERGE_MAIN,
        },
        "accepted PR/head/merge binding differs",
    )
    require(
        subject["authority_decision"]
        == {
            "reviewer_identity": REVIEWER_IDENTITY,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approved_all_candidate_meanings_and_position_effects",
            "decision_timestamp": DECISION_TIMESTAMP,
        },
        "review authority differs",
    )
    decisions = {row["action_id"]: row for row in subject["decisions"]}
    candidates = {row["action_id"]: row for row in candidate["subject"]["candidates"]}
    records = {
        row["action_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(
        len(decisions) == len(records) == len(candidates) == 63
        and set(decisions) == set(records) == set(candidates),
        "exact 63-record action set differs",
    )
    for action_id, decision in decisions.items():
        candidate_row = candidates[action_id]
        record = records[action_id]
        require(
            decision["decision"] == ACCEPTED_DECISION, f"{action_id}: decision differs"
        )
        require(
            decision["candidate_content_subject_sha256"]
            == candidate_row["candidate_content_subject_sha256"]
            and decision["accepted_evidence_map_subject_sha256"]
            == candidate_row["evidence_map_subject_sha256"]
            and decision["accepted_exact_action_meaning"]
            == candidate_row["proposed_exact_action_meaning"]
            and decision["accepted_exact_choice_position_effect"]
            == candidate_row["proposed_member_position_effect"]
            and decision["accepted_confidence"] == candidate_row["confidence"]
            and decision["accepted_coverage_assessment"]
            == candidate_row["coverage_assessment"]
            and decision["accepted_limitations"] == candidate_row["limitations"]
            and decision["accepted_source_references"]
            == candidate_row["source_references"],
            f"{action_id}: accepted content differs from candidate",
        )
        require(
            record["record_id"].endswith(":m12d:v1")
            and record["accepted_exact_action_meaning"]
            == decision["accepted_exact_action_meaning"]
            and record["accepted_exact_choice_position_effect"]
            == decision["accepted_exact_choice_position_effect"],
            f"{action_id}: implementation differs from authority",
        )

    effect_counts = Counter(
        row["accepted_exact_choice_position_effect"] for row in decisions.values()
    )
    coverage_counts = Counter(
        row["accepted_coverage_assessment"] for row in decisions.values()
    )
    require(
        effect_counts
        == {
            "opposes_exact_choice": 47,
            "supports_exact_choice": 15,
            "non_directional_not_voting": 1,
        },
        "effect accounting differs",
    )
    require(
        coverage_counts
        == {
            "bounded_official_purpose_summary": 61,
            "package_level_bounded_summary": 2,
        },
        "coverage accounting differs",
    )
    require(
        decisions["house:119:2:136"]["accepted_exact_choice_position_effect"]
        == "non_directional_not_voting",
        "H.R. 6387 became directional",
    )
    for action_id in ("house:119:1:25", "house:119:1:330"):
        require(
            decisions[action_id]["accepted_coverage_assessment"]
            == "package_level_bounded_summary"
            and decisions[action_id]["accepted_limitations"]
            == candidates[action_id]["limitations"],
            f"{action_id}: whole-package limitation differs",
        )
    require(
        subject["source_blocked_count"] == 0
        and implementation["subject"]["source_blocked_count"] == 0
        and subject["downstream_authorizations"] == DOWNSTREAM_AUTHORIZATIONS
        and implementation["subject"]["downstream_authorizations"]
        == DOWNSTREAM_AUTHORIZATIONS,
        "M12D downstream/source-blocked boundary differs",
    )
    require(
        sha256_json({k: v for k, v in parity.items() if k != "parity_subject_sha256"})
        == parity["parity_subject_sha256"],
        "M12D parity seal differs",
    )
    entries = {Path(row["path"]).name: row for row in parity["generated_artifacts"]}
    for path in (AUTHORITY_PATH, IMPLEMENTATION_PATH, DOSSIER_PATH):
        require(
            file_sha256(path) == entries[path.name]["file_sha256"],
            f"{path.name}: parity differs",
        )

    m11_authority = load(M11_AUTHORITY_PATH)
    m11_implementation = load(M11_IMPLEMENTATION_PATH)
    for schema_path, value in (
        (AUTHORITY_SCHEMA_PATH, m11_authority),
        (IMPLEMENTATION_SCHEMA_PATH, m11_implementation),
        (PARITY_SCHEMA_PATH, load(M11_PARITY_PATH)),
    ):
        validate_schema(schema_path, value)
    require(
        file_sha256(M11_AUTHORITY_PATH) == M11_AUTHORITY_FILE_SHA256
        and m11_authority["authority_subject_sha256"] == M11_AUTHORITY_SUBJECT_SHA256
        and file_sha256(M11_IMPLEMENTATION_PATH) == M11_IMPLEMENTATION_FILE_SHA256
        and m11_implementation["implementation_subject_sha256"]
        == M11_IMPLEMENTATION_SUBJECT_SHA256,
        "accepted M11D artifacts changed",
    )
    state = load(ROOT / "docs/editorial/current_state_index.json")
    m12c = state["active_m12c_action_interpretation_milestone"]
    m12d = state["active_m12d_action_interpretation_decision_milestone"]
    require(
        m12c["reviewed_pr"] == ACCEPTED_PR
        and m12c["reviewed_head"] == ACCEPTED_HEAD
        and m12c["post_merge_main"] == POST_M12C_MERGE_MAIN
        and m12d["accepted_decision_count"] == 63
        and m12d["source_blocked_count"] == 0
        and m12d["authority"]["sha256"] == file_sha256(AUTHORITY_PATH)
        and m12d["authority"]["authority_subject_sha256"]
        == authority["authority_subject_sha256"]
        and m12d["implementation"]["sha256"] == file_sha256(IMPLEMENTATION_PATH)
        and m12d["implementation"]["implementation_subject_sha256"]
        == implementation["implementation_subject_sha256"]
        and m12d["canonical_internal_action_interpretation"] is True
        and m12d["canonical_semantic_acceptance"] is False
        and all(value is False for value in m12d["downstream_authorizations"].values()),
        "M12C/M12D current state differs",
    )
    generated = write_outputs(check=True)
    return {
        "status": "pass",
        **generated,
        "effect_counts": dict(sorted(effect_counts.items())),
        "coverage_counts": dict(sorted(coverage_counts.items())),
        "parity_file_sha256": file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
        "dossier_file_sha256": file_sha256(DOSSIER_PATH),
        "m11d_backward_compatibility": "81_records_1_blocked_exact_identity_passed",
    }


def main() -> int:
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
