from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation_decisions import (  # noqa: E402
    ACCEPTED_DECISION,
    IMPLEMENTATION_STATE,
    ActionInterpretationDecisionError,
    validate_authority_record,
    validate_implementation_bundle,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    load_json,
    sha256_json,
)
from backend.scripts.build_m11d_national_security_action_meaning_acceptance import (  # noqa: E402
    ACCEPTED_CANDIDATE_FILE_SHA256,
    ACCEPTED_CANDIDATE_SUBJECT_SHA256,
    ACCEPTED_HEAD,
    ACCEPTED_PR,
    AUTHORITY_ID,
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_PATH,
    DECISION_TEMPLATE_FILE_SHA256,
    DECISION_TEMPLATE_PATH,
    DECISION_TEMPLATE_SUBJECT_SHA256,
    DOSSIER_PATH,
    IMPLEMENTATION_ID,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    POST_M11C_MERGE_MAIN,
    REVIEWER_AUTHORITY,
    REVIEWER_IDENTITY,
    build_outputs,
)
from scripts.validate_m11a_universe_authority import (  # noqa: E402
    validate_repository as validate_m11a,
)
from scripts.validate_m11b_national_security_source_readiness import (  # noqa: E402
    validate_repository as validate_m11b,
)
from scripts.validate_m11c_national_security_action_interpretation import (  # noqa: E402
    validate_repository as validate_m11c,
)


CURRENT_STATE_PATH = ROOT / "docs/editorial/current_state_index.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActionInterpretationDecisionError(message)


def _validate_schema(path: Path, value: dict[str, Any]) -> None:
    schema = load_json(path)
    Draft7Validator.check_schema(schema)
    errors = list(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value)
    )
    _require(
        not errors,
        f"{path.name} schema failure: {errors[0].message if errors else ''}",
    )


def _validate_authority_independently(
    authority: dict[str, Any], candidate: dict[str, Any]
) -> None:
    subject = authority["subject"]
    _require(
        authority["artifact_id"] == AUTHORITY_ID
        and sha256_json(subject) == authority["authority_subject_sha256"],
        "authority identity/digest mismatch",
    )
    _require(
        subject["authority_decision"]
        == {
            "reviewer_identity": REVIEWER_IDENTITY,
            "reviewer_authority": REVIEWER_AUTHORITY,
            "decision": "approved_all_candidate_meanings_and_position_effects",
            "decision_timestamp": "2026-08-09T15:32:56Z",
        },
        "human decision authority mismatch",
    )
    binding = subject["input_bindings"]["candidate_artifact"]
    _require(
        binding
        == {
            "artifact_id": candidate["artifact_id"],
            "file_sha256": ACCEPTED_CANDIDATE_FILE_SHA256,
            "interpretation_subject_sha256": ACCEPTED_CANDIDATE_SUBJECT_SHA256,
            "accepted_pr": ACCEPTED_PR,
            "accepted_head": ACCEPTED_HEAD,
            "post_merge_main": POST_M11C_MERGE_MAIN,
        },
        "accepted M11C binding mismatch",
    )
    template_binding = subject["input_bindings"]["decision_template"]
    template = load_json(DECISION_TEMPLATE_PATH)
    _require(
        template_binding["template_id"] == template["template_id"]
        and template_binding["file_sha256"] == DECISION_TEMPLATE_FILE_SHA256
        and template_binding["decision_template_subject_sha256"]
        == DECISION_TEMPLATE_SUBJECT_SHA256,
        "decision-template binding mismatch",
    )
    candidates = {
        item["action_id"]: item for item in candidate["subject"]["candidates"]
    }
    decisions = subject["decisions"]
    _require(len(decisions) == 81, "authority decision count is not 81")
    _require(
        len({item["action_id"] for item in decisions}) == 81,
        "authority decision action duplicated",
    )
    _require(
        {item["action_id"] for item in decisions} == set(candidates),
        "authority decision set differs from accepted candidates",
    )
    for decision in decisions:
        action_id = decision["action_id"]
        candidate_row = candidates[action_id]
        decision_subject = {
            key: value
            for key, value in decision.items()
            if key != "decision_subject_sha256"
        }
        _require(
            sha256_json(decision_subject) == decision["decision_subject_sha256"],
            f"authority decision digest mismatch: {action_id}",
        )
        _require(
            decision["decision"] == ACCEPTED_DECISION
            and decision["candidate_id"] == candidate_row["candidate_id"]
            and decision["candidate_content_subject_sha256"]
            == candidate_row["candidate_content_subject_sha256"]
            and decision["accepted_exact_action_meaning"]
            == candidate_row["proposed_exact_action_meaning"]
            and decision["accepted_exact_choice_position_effect"]
            == candidate_row["proposed_member_position_effect"]
            and decision["accepted_confidence"] == candidate_row["confidence"]
            and decision["accepted_limitations"] == candidate_row["limitations"]
            and decision["accepted_coverage_assessment"]
            == candidate_row["coverage_assessment"]
            and decision["accepted_source_references"]
            == candidate_row["source_references"],
            f"accepted decision differs from M11C: {action_id}",
        )
    _require(
        subject["decision_accounting"] == {ACCEPTED_DECISION: 81}
        and subject["accepted_decision_count"] == 81,
        "authority accounting mismatch",
    )
    _require(
        subject["source_blocked_actions"]
        == [
            {
                "action_id": "house:119:2:278",
                "disposition": "source_blocked_not_interpreted",
                "readiness_state": "blocked_stage_mismatch",
                "source_packet_sha256": next(
                    item["source_packet_sha256"]
                    for item in candidate["subject"]["accounting"]
                    if item["action_id"] == "house:119:2:278"
                ),
                "accepted_for_interpretation": False,
            }
        ],
        "H.R. 8800 authority boundary mismatch",
    )
    _require(
        subject["internal_action_meanings_canonical"] is True
        and subject["canonical_semantic_acceptance"] is False
        and all(
            value is False for value in subject["downstream_authorizations"].values()
        ),
        "authority crossed downstream boundary",
    )


def _validate_implementation_independently(
    implementation: dict[str, Any], authority: dict[str, Any]
) -> None:
    subject = implementation["subject"]
    _require(
        implementation["artifact_id"] == IMPLEMENTATION_ID
        and sha256_json(subject) == implementation["implementation_subject_sha256"],
        "implementation identity/digest mismatch",
    )
    decisions = {item["action_id"]: item for item in authority["subject"]["decisions"]}
    records = subject["implementation_records"]
    _require(len(records) == 81, "implementation record count is not 81")
    _require(
        len({item["action_id"] for item in records}) == 81
        and {item["action_id"] for item in records} == set(decisions),
        "implementation action set/uniqueness mismatch",
    )
    for record in records:
        action_id = record["action_id"]
        decision = decisions[action_id]
        record_subject = {
            key: value
            for key, value in record.items()
            if key != "record_subject_sha256"
        }
        _require(
            sha256_json(record_subject) == record["record_subject_sha256"],
            f"implementation record digest mismatch: {action_id}",
        )
        _require(
            record["implementation_state"] == IMPLEMENTATION_STATE
            and record["authority_decision_subject_sha256"]
            == decision["decision_subject_sha256"]
            and record["accepted_exact_action_meaning"]
            == decision["accepted_exact_action_meaning"]
            and record["accepted_exact_choice_position_effect"]
            == decision["accepted_exact_choice_position_effect"]
            and record["accepted_confidence"] == decision["accepted_confidence"]
            and record["accepted_limitations"] == decision["accepted_limitations"]
            and record["canonical_internal_action_interpretation"] is True
            and record["canonical_semantic_acceptance"] is False
            and record["public"] is False
            and record["publication_authorized"] is False
            and record["presentation_state"]
            == "internal_evidence_backed_semantic_input"
            and all(
                value is False for value in record["downstream_authorizations"].values()
            ),
            f"implementation differs from human authority: {action_id}",
        )
    _require(
        subject["implementation_accounting"] == {IMPLEMENTATION_STATE: 81}
        and subject["source_blocked_actions"]
        == authority["subject"]["source_blocked_actions"]
        and subject["source_blocked_count"] == 1,
        "implementation accounting/blocked mismatch",
    )
    _require(
        subject["mechanical_review_state"] == "pending_human_review"
        and subject["policy_episode_state"] == "not_started_not_authorized"
        and subject["canonical_semantic_acceptance"] is False
        and all(
            value is False for value in subject["downstream_authorizations"].values()
        ),
        "implementation crossed review/downstream boundary",
    )


def _validate_parity(
    parity: dict[str, Any], authority: dict[str, Any], implementation: dict[str, Any]
) -> None:
    subject = {
        key: value for key, value in parity.items() if key != "parity_subject_sha256"
    }
    _require(
        sha256_json(subject) == parity["parity_subject_sha256"],
        "parity subject digest mismatch",
    )
    _require(
        parity["parity_state"] == "pass"
        and parity["generated_last"] is True
        and parity["decision_count"] == 81
        and parity["source_blocked_count"] == 1,
        "parity accounting mismatch",
    )
    expected_subjects = {
        AUTHORITY_PATH.relative_to(ROOT).as_posix(): authority[
            "authority_subject_sha256"
        ],
        IMPLEMENTATION_PATH.relative_to(ROOT).as_posix(): implementation[
            "implementation_subject_sha256"
        ],
    }
    for item in parity["generated_artifacts"]:
        path = ROOT / item["path"]
        _require(
            path.is_file() and canonical_file_sha256(path) == item["file_sha256"],
            f"parity final-file digest mismatch: {item['path']}",
        )
        if item["path"] in expected_subjects:
            _require(
                item["content_subject_sha256"] == expected_subjects[item["path"]],
                f"parity content-subject mismatch: {item['path']}",
            )
    dossier = DOSSIER_PATH.read_text(encoding="utf-8")
    for record in implementation["subject"]["implementation_records"]:
        _require(
            record["action_id"] in dossier
            and record["accepted_exact_action_meaning"] in dossier,
            f"dossier parity mismatch: {record['action_id']}",
        )
    _require(
        all(value is False for value in parity["downstream_authorizations"].values()),
        "parity grants downstream authority",
    )


def validate_repository() -> dict[str, Any]:
    m11a = validate_m11a()
    m11b = validate_m11b()
    m11c = validate_m11c()
    candidate = load_json(CANDIDATE_PATH)
    authority = load_json(AUTHORITY_PATH)
    implementation = load_json(IMPLEMENTATION_PATH)
    parity = load_json(PARITY_PATH)

    _require(
        canonical_file_sha256(CANDIDATE_PATH) == ACCEPTED_CANDIDATE_FILE_SHA256
        and candidate["interpretation_subject_sha256"]
        == ACCEPTED_CANDIDATE_SUBJECT_SHA256,
        "accepted M11C artifact changed",
    )
    _require(
        canonical_file_sha256(DECISION_TEMPLATE_PATH) == DECISION_TEMPLATE_FILE_SHA256,
        "M11C decision template changed",
    )
    _validate_schema(AUTHORITY_SCHEMA_PATH, authority)
    _validate_schema(IMPLEMENTATION_SCHEMA_PATH, implementation)
    _validate_schema(PARITY_SCHEMA_PATH, parity)
    _validate_authority_independently(authority, candidate)
    _validate_implementation_independently(implementation, authority)
    _validate_parity(parity, authority, implementation)
    validate_authority_record(authority, candidate_artifact=candidate)
    validate_implementation_bundle(
        implementation, authority=authority, candidate_artifact=candidate
    )

    rebuilt = build_outputs()
    for path, content in rebuilt.items():
        _require(
            path.is_file() and path.read_bytes().replace(b"\r\n", b"\n") == content,
            f"deterministic regeneration mismatch: {path.relative_to(ROOT)}",
        )

    current = load_json(CURRENT_STATE_PATH)
    m11c_state = current["active_action_interpretation_milestone"]
    m11d_state = current["active_action_interpretation_decision_milestone"]
    _require(
        m11c_state["milestone_state"] == "completed_human_accepted"
        and m11c_state["accepted_pr"] == ACCEPTED_PR
        and m11c_state["accepted_head"] == ACCEPTED_HEAD
        and m11c_state["post_merge_main"] == POST_M11C_MERGE_MAIN,
        "current-state M11C closeout mismatch",
    )
    _require(
        m11d_state["milestone"] == "m11d_national_security_action_meaning_acceptance_v1"
        and m11d_state["milestone_state"] == "complete_pending_human_mechanical_review"
        and m11d_state["accepted_decision_count"] == 81
        and m11d_state["source_blocked_action_ids"] == ["house:119:2:278"]
        and m11d_state["authority_identity"]
        == {
            "id": AUTHORITY_ID,
            "sha256": canonical_file_sha256(AUTHORITY_PATH),
            "authority_subject_sha256": authority["authority_subject_sha256"],
        }
        and m11d_state["implementation_identity"]
        == {
            "id": IMPLEMENTATION_ID,
            "sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
            "implementation_subject_sha256": implementation[
                "implementation_subject_sha256"
            ],
        }
        and m11d_state["internal_action_meanings_canonical"] is True
        and m11d_state["canonical_semantic_acceptance"] is False
        and m11d_state["policy_episode_state"] == "not_started_not_authorized"
        and all(
            value is False for value in m11d_state["downstream_authorizations"].values()
        ),
        "current-state M11D boundary mismatch",
    )

    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend/app/api", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    _require(
        not any(
            IMPLEMENTATION_ID.encode() in (ROOT / path).read_bytes()
            for path in tracked_runtime
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "M11D implementation entered runtime/public selectors",
    )
    return {
        "status": "pass",
        "authority_id": AUTHORITY_ID,
        "authority_file_sha256": canonical_file_sha256(AUTHORITY_PATH),
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "implementation_id": IMPLEMENTATION_ID,
        "implementation_file_sha256": canonical_file_sha256(IMPLEMENTATION_PATH),
        "implementation_subject_sha256": implementation[
            "implementation_subject_sha256"
        ],
        "accepted_decision_count": 81,
        "source_blocked_count": 1,
        "implementation_accounting": dict(
            sorted(
                Counter(
                    item["implementation_state"]
                    for item in implementation["subject"]["implementation_records"]
                ).items()
            )
        ),
        "downstream_authorizations": implementation["subject"][
            "downstream_authorizations"
        ],
        "m11a": m11a,
        "m11b": m11b,
        "m11c": m11c,
    }


def main() -> int:
    print(json.dumps(validate_repository(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
