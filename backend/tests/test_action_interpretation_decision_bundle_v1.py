"""Adversarial tests for the detached M3B-A decision bundle."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_action_interpretation_decision_bundle_v1 import BUNDLE_ID, OUTPUT_ROOT  # noqa: E402
from validate_action_interpretation_decision_bundle_v1 import (  # noqa: E402
    DecisionBundleValidationError,
    validate,
    validate_parity,
    validate_values,
)


NAMES = (
    "decision_preparation_bundle.json",
    "human_decision_record.json",
    "codex_recommendations.json",
    "secondary_detail_register.json",
)


def artifacts() -> dict[str, dict[str, object]]:
    return {
        name: json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))
        for name in NAMES
    }


class DecisionBundleTests(unittest.TestCase):
    def test_complete_bundle(self) -> None:
        result = validate()
        self.assertEqual(result["bundle_id"], BUNDLE_ID)
        self.assertEqual(result["action_count"], 37)

    def test_missing_decision_unit_rejected(self) -> None:
        values = artifacts()
        values["decision_preparation_bundle.json"]["decision_units"].pop()
        with self.assertRaisesRegex(DecisionBundleValidationError, "completeness"):
            validate_values(values)

    def test_duplicate_decision_unit_rejected(self) -> None:
        values = artifacts()
        values["decision_preparation_bundle.json"]["decision_units"][-1] = deepcopy(
            values["decision_preparation_bundle.json"]["decision_units"][0]
        )
        with self.assertRaisesRegex(DecisionBundleValidationError, "duplicated"):
            validate_values(values)

    def test_filled_human_decision_rejected(self) -> None:
        values = artifacts()
        values["human_decision_record.json"]["decisions"][0]["selected_decision"] = (
            "accept_candidate"
        )
        with self.assertRaisesRegex(
            DecisionBundleValidationError, "human scalar field filled"
        ):
            validate_values(values)

    def test_reviewer_identity_rejected(self) -> None:
        values = artifacts()
        values["human_decision_record.json"]["decisions"][0]["reviewer_identity"] = (
            "invented"
        )
        with self.assertRaisesRegex(
            DecisionBundleValidationError, "human scalar field filled"
        ):
            validate_values(values)

    def test_recommendation_cannot_be_human_decision(self) -> None:
        values = artifacts()
        values["codex_recommendations.json"]["recommendations_are_human_decisions"] = (
            True
        )
        with self.assertRaisesRegex(DecisionBundleValidationError, "separation"):
            validate_values(values)

    def test_special_actions_are_tier_one(self) -> None:
        values = artifacts()
        by_id = {
            row["action_id"]: row
            for row in values["decision_preparation_bundle.json"]["decision_units"]
        }
        for action_id in ("house:119:1:128", "house:119:2:155", "house:119:2:278"):
            self.assertEqual(by_id[action_id]["review_tier"], 1)

    def test_special_recommendations_preserved(self) -> None:
        values = artifacts()
        by_id = {
            row["action_id"]: row["recommendation"]
            for row in values["codex_recommendations.json"]["recommendations"]
        }
        self.assertEqual(by_id["house:119:1:128"], "recommend_preserve_ambiguous")
        self.assertEqual(by_id["house:119:2:155"], "recommend_preserve_ambiguous")
        self.assertEqual(
            by_id["house:119:2:278"], "recommend_preserve_no_safe_candidate"
        )

    def test_required_secondary_details_present(self) -> None:
        values = artifacts()
        text = " ".join(
            row["source_bound_detail"]
            for row in values["secondary_detail_register.json"]["entries"]
        )
        self.assertIn("$10,000,000", text)
        self.assertIn("two days", text)
        self.assertIn("30 days", text)

    def test_benchmark_is_comparison_only(self) -> None:
        values = artifacts()
        compared = [
            row
            for row in values["decision_preparation_bundle.json"]["decision_units"]
            if row["benchmark_comparison"]
        ]
        self.assertEqual(len(compared), 7)
        self.assertTrue(
            all(row["benchmark_comparison"]["comparison_only"] for row in compared)
        )

    def test_closed_decision_schema_rejects_unknown_unit_field(self) -> None:
        value = artifacts()["decision_preparation_bundle.json"]
        value["decision_units"][0]["invented_authority"] = True
        schema = json.loads(
            (
                OUTPUT_ROOT / "schemas/decision_preparation_bundle_v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        errors = list(Draft7Validator(schema).iter_errors(value))
        self.assertTrue(errors)
        self.assertIn("Additional properties", errors[0].message)

    def test_parity_rejects_final_byte_mutation(self) -> None:
        parity = json.loads(
            (OUTPUT_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
        )
        path = parity["canonical_artifacts"][0]["path"]
        with self.assertRaisesRegex(
            DecisionBundleValidationError, "final-byte mismatch"
        ):
            validate_parity(byte_overrides={path: (ROOT / path).read_bytes() + b" "})


if __name__ == "__main__":
    unittest.main()
