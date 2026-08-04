"""Fail-closed verification for the M7 user launch-ratification state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.editorial_presentations.compiler import canonical_digest  # noqa: E402
from app.editorial_presentations.selector import select_public_presentations  # noqa: E402
from scripts.record_foushee_justice_launch_ratification_m7 import (  # noqa: E402
    CONTROL_STATE,
    EXPECTED_CONTENT_SHA,
    EXPECTED_FILE_SHA,
    EXPECTED_RISKS,
    EXPECTED_SAMPLES,
    EXPECTED_SUBJECT_SHA,
    OUT,
)
from scripts.verify_foushee_justice_launch_review_m6 import verify as verify_m6  # noqa: E402

EXPECTED_CANDIDATE_FILE_SHA = (
    "9254e396c85b442e605203f2ebb48f4bbc28cb1c4709ad10bbb084445f5c6021"
)
EXPECTED_MAPPING_FILE_SHA = (
    "a4b95555f2517bfce0eec3118765e813f6fd802ac48935281667c2339865d7fe"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_sha_matches(path: Path, expected: str) -> bool:
    import hashlib

    raw = path.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return expected in {
        hashlib.sha256(candidate).hexdigest() for candidate in (raw, lf, crlf)
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_digest(value: dict, label: str) -> None:
    stated = value.get("content_subject_sha256")
    subject = {
        key: item for key, item in value.items() if key != "content_subject_sha256"
    }
    require(stated == canonical_digest(subject), f"{label}: stale content digest")


def verify(root: Path = OUT) -> dict[str, object]:
    verify_m6(root)
    record_path = (
        root / "f000477_justice_public_safety_119_user_launch_ratification_v1.json"
    )
    record = load(record_path)
    Draft7Validator(
        load(root / "user_launch_ratification_record_v1.schema.json")
    ).validate(record)
    require(
        file_sha_matches(record_path, EXPECTED_FILE_SHA),
        "ratification final bytes differ",
    )
    require(
        record["content_subject_sha256"] == EXPECTED_CONTENT_SHA,
        "ratification subject digest differs",
    )
    require_digest(record, "ratification record")

    subject = load(root / "launch_ratification_subject.json")
    require_digest(subject, "ratification subject")
    require(
        subject["content_subject_sha256"] == EXPECTED_SUBJECT_SHA,
        "M6 subject identity differs",
    )
    approved = record["approved_public_candidate"]
    subject_pairs = {
        "public_presentation_content": "presentation_content_sha256",
        "reviewed_wording": "reviewed_wording_sha256",
        "mapping_set": "mapping_set_sha256",
        "risk_packet": "risk_packet_sha256",
        "screenshot_manifest": "screenshot_manifest_sha256",
        "calibration_sample": "calibration_sample_sha256",
        "freeze": "freeze_sha256",
    }
    require(
        all(subject[left] == approved[right] for left, right in subject_pairs.items()),
        "ratification subject binding differs",
    )

    candidate_path = root / "public_presentation_candidate.json"
    mappings_path = root / "analytical_string_mappings.json"
    require(
        file_sha_matches(candidate_path, EXPECTED_CANDIDATE_FILE_SHA),
        "frozen candidate bytes changed",
    )
    require(
        file_sha_matches(mappings_path, EXPECTED_MAPPING_FILE_SHA),
        "frozen mappings bytes changed",
    )

    receipt = load(root / "user_launch_ratification_receipt.json")
    Draft7Validator(
        load(root / "user_launch_ratification_receipt_v1.schema.json")
    ).validate(receipt)
    require_digest(receipt, "ratification receipt")
    require(
        receipt["ratification_record_binding"]
        == {
            "artifact_id": record["artifact_id"],
            "content_subject_sha256": EXPECTED_CONTENT_SHA,
            "final_file_sha256": EXPECTED_FILE_SHA,
        },
        "receipt record binding differs",
    )
    require(receipt["subject_binding"] == subject, "receipt subject binding differs")
    require(
        receipt["candidate_binding"]["final_file_sha256"]
        == EXPECTED_CANDIDATE_FILE_SHA,
        "receipt candidate binding differs",
    )
    require(
        receipt["control_state"] == CONTROL_STATE, "receipt control state is untruthful"
    )
    require(
        receipt["user_identity"] == "dhart54"
        and receipt["decision_timestamp"] == "2026-08-02T17:35:00-04:00",
        "user identity or timestamp differs",
    )
    for name, digest in receipt["immutable_file_bindings"].items():
        require(
            file_sha_matches(root / name, digest),
            f"immutable M6 file changed: {name}",
        )

    risks = load(root / "launch_risk_register_m7.json")
    require_digest(risks, "risk successor")
    require(
        risks["terminal_review_state"] == "user_ratified_treatment"
        and risks["open_user_choice_count"] == 0,
        "risk review state is not terminal",
    )
    risk_map = {
        item["risk_id"]: item["selection"] for item in risks["resolved_user_choices"]
    }
    require(risk_map == EXPECTED_RISKS, "risk treatment differs")
    require(
        all(
            item["historical_limitation_retained"]
            for item in risks["resolved_user_choices"]
        ),
        "historical risk limitation removed",
    )
    receipt_risks = {
        item["risk_id"]: item["selection"] for item in receipt["risk_selections"]
    }
    require(receipt_risks == EXPECTED_RISKS, "receipt risk treatment differs")

    calibration = load(root / "calibration_sample.json")
    sample_by_id = {item["sample_id"]: item for item in calibration["samples"]}
    approvals = {item["sample_id"]: item for item in receipt["calibration_approvals"]}
    require(set(approvals) == EXPECTED_SAMPLES, "calibration approval omitted")
    for sample_id, approval in approvals.items():
        require(approval["decision"] == "approved", f"{sample_id}: not approved")
        require(
            approval["selection_proof"] == sample_by_id[sample_id]["selection_proof"],
            f"{sample_id}: selection proof differs",
        )
        require(
            approval["sample_content_subject_sha256"]
            == canonical_digest(sample_by_id[sample_id]),
            f"{sample_id}: sample binding differs",
        )

    state = load(root / "user_launch_ratification_state.json")
    require_digest(state, "ratification state")
    require(state["controls"] == CONTROL_STATE, "current-state controls differ")
    require(
        state["ratification_receipt_content_subject_sha256"]
        == receipt["content_subject_sha256"],
        "current state uses stale receipt",
    )
    require(
        state["risk_register_content_subject_sha256"]
        == risks["content_subject_sha256"],
        "current state uses stale risk successor",
    )
    require(
        state["candidate_publicly_selectable"] is False
        and state["historical_active_publication_unchanged"] is True,
        "candidate selection or historical publication changed",
    )

    selected = select_public_presentations(
        [],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    require(
        all(item["tier"] == "receipts_only" for item in selected["presentations"]),
        "candidate became publicly selectable",
    )
    return {
        "status": "pass",
        "user": record["user_identity"],
        "risks": len(risk_map),
        "calibration_samples": len(approvals),
        "candidate_immutable": True,
        "production_eligible": False,
        "publication_active": False,
        "selector_unchanged": True,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
