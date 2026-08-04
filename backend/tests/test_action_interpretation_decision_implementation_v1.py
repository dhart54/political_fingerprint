"""Adversarial tests for the detached M3B-B decision implementation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_action_interpretation_decision_implementation_v1 import (  # noqa: E402
    DECISION_ROOT,
    OUTPUT_NAMES,
    SCHEMA_ROOT,
)
from validate_action_interpretation_decision_implementation_v1 import (  # noqa: E402
    ImplementationValidationError,
    validate,
    validate_parity,
    validate_values,
)


def artifacts() -> dict[str, dict[str, object]]:
    return {
        name: json.loads((DECISION_ROOT / name).read_text(encoding="utf-8"))
        for name in OUTPUT_NAMES
    }


def record(values: dict[str, dict[str, object]], action_id: str) -> dict[str, object]:
    return next(
        row
        for row in values["decision_implementation_bundle.json"][
            "implementation_records"
        ]
        if row["action_id"] == action_id
    )


class DecisionImplementationTests(unittest.TestCase):
    def test_complete_implementation(self) -> None:
        result = validate()
        self.assertEqual(result["action_count"], 37)
        self.assertEqual(result["calibration_eligible_count"], 34)

    def test_missing_action_rejected(self) -> None:
        values = artifacts()
        values["decision_implementation_bundle.json"]["implementation_records"].pop()
        with self.assertRaisesRegex(ImplementationValidationError, "completeness"):
            validate_values(values)

    def test_duplicate_action_rejected(self) -> None:
        values = artifacts()
        rows = values["decision_implementation_bundle.json"]["implementation_records"]
        rows[-1] = deepcopy(rows[0])
        with self.assertRaisesRegex(ImplementationValidationError, "duplicated"):
            validate_values(values)

    def test_changed_decision_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:1:6")["selected_decision"] = "preserve_ambiguous"
        with self.assertRaisesRegex(
            ImplementationValidationError, "selected_decision differs"
        ):
            validate_values(values)

    def test_accept_substituted_for_ambiguity_rejected(self) -> None:
        values = artifacts()
        row = record(values, "house:119:1:128")
        row["selected_decision"] = "accept_candidate"
        row["implementation_state"] = "implemented_accepted_candidate"
        with self.assertRaisesRegex(
            ImplementationValidationError, "selected_decision differs"
        ):
            validate_values(values)

    def test_roll_278_prose_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:2:278")["implemented_exact_action_meaning"] = (
            "Invented meaning"
        )
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_exact_action_meaning differs"
        ):
            validate_values(values)

    def test_roll_155_metadata_conflict_removal_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:2:155")["implemented_limitations"] = []
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_limitations differs"
        ):
            validate_values(values)

    def test_roll_128_uncertainty_removal_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:1:128")["unresolved_question"] = None
        with self.assertRaisesRegex(
            ImplementationValidationError, "unresolved_question differs"
        ):
            validate_values(values)

    def test_roll_27_five_year_maximum_omission_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:1:27")["implemented_exact_action_meaning"] = (
            "Superseded wording"
        )
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_exact_action_meaning differs"
        ):
            validate_values(values)

    def test_roll_157_seven_year_sunset_omission_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:2:157")["implemented_exact_action_meaning"] = (
            "Superseded wording"
        )
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_exact_action_meaning differs"
        ):
            validate_values(values)

    def test_roll_218_limitations_removal_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:2:218")["implemented_limitations"] = []
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_limitations differs"
        ):
            validate_values(values)

    def test_roll_240_timing_limitations_removal_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:2:240")["implemented_limitations"] = []
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_limitations differs"
        ):
            validate_values(values)

    def test_safely_compressed_detail_promotion_rejected(self) -> None:
        values = artifacts()
        row = record(values, "house:119:1:130")
        row["implemented_exact_action_meaning"] += (
            " The program must be established within one year."
        )
        with self.assertRaisesRegex(
            ImplementationValidationError, "implemented_exact_action_meaning differs"
        ):
            validate_values(values)

    def test_reviewer_identity_change_rejected(self) -> None:
        values = artifacts()
        values["delegated_authority_mapping.json"]["delegated_decision_maker"][
            "reviewer_identity"
        ] = "dhart54"
        with self.assertRaisesRegex(
            ImplementationValidationError, "reviewer identity changed"
        ):
            validate_values(values)

    def test_false_user_signature_rejected(self) -> None:
        values = artifacts()
        values["delegated_authority_mapping.json"]["not_user_signature"] = False
        with self.assertRaisesRegex(ImplementationValidationError, "mapping differs"):
            validate_values(values)

    def test_changed_authority_digest_rejected(self) -> None:
        values = artifacts()
        values["delegated_authority_mapping.json"]["authority_record"][
            "content_subject_sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(
            ImplementationValidationError, "authority-record digest changed"
        ):
            validate_values(values)

    def test_recommendation_cannot_replace_decision(self) -> None:
        values = artifacts()
        record(values, "house:119:1:128")["selected_decision"] = (
            "recommend_preserve_ambiguous"
        )
        with self.assertRaisesRegex(
            ImplementationValidationError, "selected_decision differs"
        ):
            validate_values(values)

    def test_canonical_or_public_assertion_rejected(self) -> None:
        values = artifacts()
        record(values, "house:119:1:6")["public"] = True
        with self.assertRaisesRegex(ImplementationValidationError, "canonical/public"):
            validate_values(values)

    def test_closed_schema_rejects_unknown_record_field(self) -> None:
        value = artifacts()["decision_implementation_bundle.json"]
        value["implementation_records"][0]["invented_authority"] = True
        schema = json.loads(
            (SCHEMA_ROOT / "decision_implementation_bundle_v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        errors = list(Draft7Validator(schema).iter_errors(value))
        self.assertTrue(errors)
        self.assertTrue(
            any("Additional properties" in error.message for error in errors)
        )

    def test_stale_final_file_hash_rejected(self) -> None:
        parity = json.loads(
            (DECISION_ROOT / "implementation_parity_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        item = parity["referenced_artifacts"][0]
        with self.assertRaisesRegex(
            ImplementationValidationError, "stale final-file hash"
        ):
            validate_parity(
                byte_overrides={item["path"]: (ROOT / item["path"]).read_bytes() + b" "}
            )

    def test_stale_markdown_rejected(self) -> None:
        with self.assertRaisesRegex(
            ImplementationValidationError, "Markdown differs from JSON"
        ):
            validate_parity(markdown_override="# stale")


if __name__ == "__main__":
    unittest.main()
