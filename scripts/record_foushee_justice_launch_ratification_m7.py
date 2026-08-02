"""Import and record the content-bound M7 user launch ratification."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.editorial_presentations.compiler import canonical_digest  # noqa: E402

OUT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_interface_candidates/f000477_justice_public_safety_119_v1"
)
IMPORTED = OUT / "f000477_justice_public_safety_119_user_launch_ratification_v1.json"
RECORD_SCHEMA = OUT / "user_launch_ratification_record_v1.schema.json"
RECEIPT_SCHEMA = OUT / "user_launch_ratification_receipt_v1.schema.json"
RECEIPT = OUT / "user_launch_ratification_receipt.json"
RISK_SUCCESSOR = OUT / "launch_risk_register_m7.json"
STATE = OUT / "user_launch_ratification_state.json"

EXPECTED_FILE_SHA = "eb5f6aa7775f8765c1319d80849dfeedbb41c85f8e30f30a21a53819a0f615d8"
EXPECTED_CONTENT_SHA = (
    "22faba18c447ba9ebd5045b74666c09cb0d030f36187e727732c68d561f0721e"
)
EXPECTED_SUBJECT_SHA = (
    "10d61d55a83177a1cb8c6b65e76fa11199a1bca0b46098c467012c429fcf28c2"
)
EXPECTED_RISKS = {
    "launch-risk:roll-128:v1": "retain_bounded_meaning_with_adjacent_limitation",
    "launch-risk:roll-155-and-fisa-grouping:v1": "retain_non_counting_treatment",
    "launch-risk:roll-278:v1": "retain_no_safe_ledger_only_state",
    "launch-risk:semantic-ir:mechanism-divide:v1": "option_a_retain_bounded_mechanism_contrast",
}
EXPECTED_SAMPLES = {
    "calibration:action",
    "calibration:episode",
    "calibration:pattern",
    "calibration:mapping",
}
CONTROL_STATE = {
    "editorial_wording": "user_approved",
    "risk_treatments": "user_approved",
    "blind_calibration": "user_approved",
    "launch_ratification": "user_ratified_with_production_eligibility_deferred",
    "benchmark": "not_promoted",
    "production_eligible": False,
    "publication": "inactive",
    "public_selector": "unchanged",
    "deployment": "unauthorized",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def with_digest(value: dict) -> dict:
    result = dict(value)
    result["content_subject_sha256"] = canonical_digest(result)
    return result


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_record(path: Path) -> dict:
    if file_sha(path) != EXPECTED_FILE_SHA:
        raise ValueError("ratification final-file digest differs")
    record = load(path)
    Draft7Validator(load(RECORD_SCHEMA)).validate(record)
    if (
        canonical_digest(
            {k: v for k, v in record.items() if k != "content_subject_sha256"}
        )
        != EXPECTED_CONTENT_SHA
    ):
        raise ValueError("ratification content-subject digest differs")
    if {
        item["risk_id"]: item["selection"]
        for item in record["risk_specific_selections"]
    } != EXPECTED_RISKS:
        raise ValueError("ratification risk selections differ")
    if {
        item["sample_id"] for item in record["calibration_sample_decisions"]
    } != EXPECTED_SAMPLES:
        raise ValueError("ratification calibration approvals differ")
    return record


def build(source: Path) -> dict[str, str]:
    record = validate_record(source)
    subject = load(OUT / "launch_ratification_subject.json")
    if (
        subject["content_subject_sha256"] != EXPECTED_SUBJECT_SHA
        or canonical_digest(
            {k: v for k, v in subject.items() if k != "content_subject_sha256"}
        )
        != EXPECTED_SUBJECT_SHA
    ):
        raise ValueError("frozen M6 ratification subject differs")
    approved = record["approved_public_candidate"]
    expected_subject_fields = {
        "public_presentation_content": approved["presentation_content_sha256"],
        "reviewed_wording": approved["reviewed_wording_sha256"],
        "mapping_set": approved["mapping_set_sha256"],
        "risk_packet": approved["risk_packet_sha256"],
        "screenshot_manifest": approved["screenshot_manifest_sha256"],
        "calibration_sample": approved["calibration_sample_sha256"],
        "freeze": approved["freeze_sha256"],
    }
    if any(subject[key] != value for key, value in expected_subject_fields.items()):
        raise ValueError("ratification does not bind the frozen M6 subject")

    if source.resolve() != IMPORTED.resolve():
        shutil.copyfile(source, IMPORTED)
    if file_sha(IMPORTED) != EXPECTED_FILE_SHA:
        raise ValueError("import did not preserve exact ratification bytes")

    risks = load(OUT / "launch_risk_register.json")
    risk_by_id = {item["risk_id"]: item for item in risks["unresolved"]}
    resolved = []
    for risk_id, selection in EXPECTED_RISKS.items():
        original = risk_by_id[risk_id]
        resolved.append(
            {
                "risk_id": risk_id,
                "selection": selection,
                "review_state": "user_ratified_treatment",
                "historical_limitation_retained": True,
                "underlying_question": original["question"],
                "retained_effect": original["effect"],
                "retained_current_treatment": original["current_treatment"],
            }
        )
    risk_successor = with_digest(
        {
            "schema_version": "cumulative_launch_risk_register_v2",
            "artifact_id": "launch-risk-register:f000477:justice_public_safety:119:m7:v1",
            "predecessor_artifact_id": risks["artifact_id"],
            "predecessor_content_subject_sha256": risks["content_subject_sha256"],
            "ratification_record_artifact_id": record["artifact_id"],
            "ratification_record_content_subject_sha256": record[
                "content_subject_sha256"
            ],
            "terminal_review_state": "user_ratified_treatment",
            "resolved_user_choices": resolved,
            "open_user_choice_count": 0,
            "retained_historical_limitation_count": 4,
        }
    )
    write_json(RISK_SUCCESSOR, risk_successor)

    calibration = load(OUT / "calibration_sample.json")
    calibration_by_id = {item["sample_id"]: item for item in calibration["samples"]}
    approvals = []
    for decision in record["calibration_sample_decisions"]:
        sample = calibration_by_id[decision["sample_id"]]
        approvals.append(
            {
                "sample_id": decision["sample_id"],
                "decision": "approved",
                "selection_proof": sample["selection_proof"],
                "sample_content_subject_sha256": canonical_digest(sample),
            }
        )

    immutable_names = [
        "public_presentation_candidate.json",
        "analytical_string_mappings.json",
        "exact_action_ledger.json",
        "launch_ratification_subject.json",
        "launch_risk_register.json",
        "calibration_sample.json",
        "public_interface_freeze.json",
        "screenshot_manifest.json",
        "full_record_semantic_artifact.json",
        "full_record_semantic_validation_receipt.json",
    ]
    immutable = {name: file_sha(OUT / name) for name in immutable_names}
    candidate = load(OUT / "public_presentation_candidate.json")
    receipt = with_digest(
        {
            "schema_version": "user_launch_ratification_receipt_v1",
            "artifact_id": "user-launch-ratification-receipt:f000477:justice_public_safety:119:v1",
            "ratification_record_binding": {
                "artifact_id": record["artifact_id"],
                "content_subject_sha256": record["content_subject_sha256"],
                "final_file_sha256": file_sha(IMPORTED),
            },
            "subject_binding": subject,
            "candidate_binding": {
                "artifact_id": candidate["artifact_identity"]["artifact_id"],
                "presentation_content_sha256": candidate["provenance"][
                    "presentation_content_sha256"
                ],
                "final_file_sha256": file_sha(
                    OUT / "public_presentation_candidate.json"
                ),
            },
            "immutable_file_bindings": immutable,
            "risk_selections": [
                {
                    "risk_id": item["risk_id"],
                    "selection": item["selection"],
                    "review_state": item["review_state"],
                    "historical_limitation_retained": True,
                }
                for item in resolved
            ],
            "calibration_approvals": approvals,
            "user_identity": record["user_identity"],
            "decision_timestamp": record["decision_timestamp"],
            "control_state": CONTROL_STATE,
        }
    )
    Draft7Validator(load(RECEIPT_SCHEMA)).validate(receipt)
    write_json(RECEIPT, receipt)

    state = with_digest(
        {
            "schema_version": "user_launch_ratification_state_v1",
            "artifact_id": "user-launch-ratification-state:f000477:justice_public_safety:119:v1",
            "subject": {
                "member_id": "F000477",
                "issue_id": "JUSTICE_PUBLIC_SAFETY",
                "congress_scope": [119],
            },
            "candidate_artifact_id": candidate["artifact_identity"]["artifact_id"],
            "candidate_presentation_content_sha256": candidate["provenance"][
                "presentation_content_sha256"
            ],
            "ratification_receipt_artifact_id": receipt["artifact_id"],
            "ratification_receipt_content_subject_sha256": receipt[
                "content_subject_sha256"
            ],
            "risk_register_artifact_id": risk_successor["artifact_id"],
            "risk_register_content_subject_sha256": risk_successor[
                "content_subject_sha256"
            ],
            "controls": CONTROL_STATE,
            "historical_active_publication_unchanged": True,
            "candidate_publicly_selectable": False,
            "next_separate_decisions": [
                "production_eligibility",
                "benchmark_promotion",
                "publication_activation",
            ],
        }
    )
    write_json(STATE, state)
    return {
        "receipt": receipt["content_subject_sha256"],
        "receipt_file": file_sha(RECEIPT),
        "state": state["content_subject_sha256"],
        "risk_successor": risk_successor["content_subject_sha256"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source), sort_keys=True))
