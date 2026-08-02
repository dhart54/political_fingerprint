from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.record_foushee_justice_launch_ratification_m7 import OUT
from scripts.verify_foushee_justice_launch_ratification_m7 import verify


def mutate(tmp_path: Path, filename: str, mutation) -> Path:
    root = tmp_path / "m7"
    shutil.copytree(OUT, root)
    path = root / filename
    value = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


def test_m7_user_ratification_passes() -> None:
    assert verify() == {
        "status": "pass",
        "user": "dhart54",
        "risks": 4,
        "calibration_samples": 4,
        "candidate_immutable": True,
        "production_eligible": False,
        "publication_active": False,
        "selector_unchanged": True,
    }


@pytest.mark.parametrize(
    ("filename", "mutation"),
    [
        (
            "f000477_justice_public_safety_119_user_launch_ratification_v1.json",
            lambda value: value.update(subject_content_subject_sha256="0" * 64),
        ),
        (
            "f000477_justice_public_safety_119_user_launch_ratification_v1.json",
            lambda value: value["approved_public_candidate"].update(
                reviewed_wording_sha256="0" * 64
            ),
        ),
        (
            "f000477_justice_public_safety_119_user_launch_ratification_v1.json",
            lambda value: value["approved_public_candidate"].update(
                mapping_set_sha256="0" * 64
            ),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value["risk_selections"][0].update(selection="withhold"),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value["calibration_approvals"].pop(),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value["control_state"].update(production_eligible=True),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value["control_state"].update(benchmark="promoted"),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value["control_state"].update(publication="active"),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value.update(user_identity="delegated_authority"),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value.update(decision_timestamp="2026-08-02T17:36:00-04:00"),
        ),
        (
            "user_launch_ratification_receipt.json",
            lambda value: value.update(user_identity="delegate"),
        ),
        (
            "public_presentation_candidate.json",
            lambda value: value["editorial_wording"]["conclusion"]["body"].update(
                text="Changed"
            ),
        ),
        (
            "launch_risk_register_m7.json",
            lambda value: value["resolved_user_choices"][0].update(
                historical_limitation_retained=False
            ),
        ),
        (
            "user_launch_ratification_state.json",
            lambda value: value.update(candidate_publicly_selectable=True),
        ),
        (
            "user_launch_ratification_state.json",
            lambda value: value.update(
                ratification_receipt_content_subject_sha256="0" * 64
            ),
        ),
    ],
)
def test_adversarial_ratification_mutations_fail_closed(
    tmp_path: Path, filename: str, mutation
) -> None:
    root = mutate(tmp_path, filename, mutation)
    with pytest.raises(Exception):
        verify(root)
