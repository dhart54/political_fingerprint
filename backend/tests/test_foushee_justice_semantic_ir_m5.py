from __future__ import annotations

import unittest

from jsonschema import Draft7Validator

from scripts.build_foushee_justice_semantic_ir_m5 import OUTPUT_ROOT, build, load
from scripts.validate_foushee_justice_semantic_ir_m5 import validate


class FousheeJusticeSemanticIRM5Tests(unittest.TestCase):
    def test_deterministic_builder_check(self) -> None:
        result = build(True)
        self.assertEqual(
            result["accounting"],
            {"included_in_behavioral_proposition": 35, "non_proposition": 2},
        )

    def test_independent_verifier(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["independent_verification"], "pass")

    def test_closed_schemas(self) -> None:
        cases = [
            (
                "full_record_semantic_ir_compiler_input_v1.schema.json",
                "frozen_final_compiler_input.json",
            ),
            (
                "full_record_semantic_ir_candidate_v1.schema.json",
                "frozen_final_compiled_semantic_ir.json",
            ),
            (
                "full_record_semantic_ir_provisional_implementation_v1.schema.json",
                "provisional_implementation_bundle.json",
            ),
        ]
        for schema_name, artifact_name in cases:
            schema = load(OUTPUT_ROOT / "schemas" / schema_name)
            Draft7Validator.check_schema(schema)
            errors = list(
                Draft7Validator(schema).iter_errors(load(OUTPUT_ROOT / artifact_name))
            )
            self.assertEqual(errors, [], [error.message for error in errors])
        supporting = load(
            OUTPUT_ROOT / "schemas" / "m5_supporting_artifacts_v1.schema.json"
        )
        Draft7Validator.check_schema(supporting)
        core_versions = {
            "full_record_semantic_ir_compiler_input_v1",
            "full_record_semantic_ir_candidate_v1",
            "full_record_semantic_ir_provisional_implementation_v1",
        }
        for path in OUTPUT_ROOT.glob("*.json"):
            value = load(path)
            if value.get("schema_version") in core_versions or path.name in {
                "parity_manifest.json",
                "imported_m4b_delegated_acceptance.json",
            }:
                continue
            errors = list(Draft7Validator(supporting).iter_errors(value))
            self.assertEqual(
                errors, [], (path.name, [error.message for error in errors])
            )

    def test_special_action_controls(self) -> None:
        graph = load(OUTPUT_ROOT / "frozen_final_compiled_semantic_ir.json")
        propositions = graph["compiled_ir"]["members"][0]["proposition_graph"][
            "propositions"
        ]
        support = {
            action_id for p in propositions for action_id in p["evidence_action_ids"]
        }
        self.assertNotIn("house:119:2:155", support)
        self.assertNotIn("house:119:2:278", support)
        self.assertIn("house:119:1:128", support)

    def test_no_public_or_authorizing_state(self) -> None:
        bundle = load(OUTPUT_ROOT / "provisional_implementation_bundle.json")
        for key in (
            "accepted_semantic_reference",
            "canonical",
            "public",
            "persisted",
            "published",
            "production_eligible",
            "user_approved",
            "authorizing",
        ):
            self.assertFalse(bundle[key])
        self.assertIsNone(bundle["render_plan"]["example_prose"])
        self.assertFalse(bundle["render_plan"]["analytical_additions_allowed"])


if __name__ == "__main__":
    unittest.main()
