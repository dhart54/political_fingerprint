from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.verify_foushee_justice_launch_review_m6 import OUT, verify


def mutate(tmp_path: Path, filename: str, mutation) -> Path:
    root = tmp_path / "m6"
    shutil.copytree(OUT, root)
    path = root / filename
    value = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


def test_frozen_m6_package_passes_independent_verification() -> None:
    result = verify()
    assert result == {
        "status": "pass",
        "mappings": 22,
        "actions": 37,
        "primary_patterns": 4,
        "screenshots": 8,
        "calibration_samples": 4,
        "unresolved_risks": 4,
        "selector_isolated": True,
    }


@pytest.mark.parametrize(
    ("filename", "mutation"),
    [
        ("analytical_string_mappings.json", lambda value: value["mappings"].pop()),
        (
            "analytical_string_mappings.json",
            lambda value: value["mappings"][0]["mapping"]["proposition_ids"].append(
                "prop:unknown"
            ),
        ),
        (
            "analytical_string_mappings.json",
            lambda value: value["mappings"][0]["mapping"]["action_ids"].append(
                "house:119:1:999"
            ),
        ),
        (
            "public_presentation_candidate.json",
            lambda value: value["editorial_wording"]["repeated_patterns"].pop(),
        ),
        (
            "public_presentation_candidate.json",
            lambda value: value["editorial_wording"]["conclusion"]["body"].update(
                text="Her record divides between two complete explanations."
            ),
        ),
        (
            "exact_action_ledger.json",
            lambda value: next(
                item
                for item in value["records"]
                if item["canonical_action_id"] == "house:119:2:155"
            )["proposition_ids"].append("prop:698e503c786f2f72"),
        ),
        (
            "exact_action_ledger.json",
            lambda value: next(
                item
                for item in value["records"]
                if item["canonical_action_id"] == "house:119:2:278"
            ).update(governed_action_meaning="Unsupported meaning"),
        ),
        (
            "public_presentation_candidate.json",
            lambda value: value["controls"]["production"].update(eligible=True),
        ),
        (
            "calibration_sample.json",
            lambda value: value["samples"][0].update(object_id="house:119:1:128"),
        ),
        (
            "screenshot_manifest.json",
            lambda value: value["images"][0].update(final_file_sha256="0" * 64),
        ),
        (
            "empty_launch_ratification_template.json",
            lambda value: value.update(user_decision="approved"),
        ),
    ],
)
def test_adversarial_mutations_fail_closed(
    tmp_path: Path, filename: str, mutation
) -> None:
    root = mutate(tmp_path, filename, mutation)
    with pytest.raises((AssertionError, KeyError)):
        verify(root)


def test_review_fixture_is_not_a_public_selector_input() -> None:
    candidate = json.loads(
        (OUT / "public_presentation_candidate.json").read_text(encoding="utf-8")
    )
    assert candidate["controls"]["effective_public_tier"] == "receipts_only"
    assert candidate["controls"]["publication_gates_passed"] is False
