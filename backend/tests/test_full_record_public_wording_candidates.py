"""Adversarial tests for generic detached public-wording candidates."""

from __future__ import annotations

from copy import deepcopy
import unittest

from backend.app.etl.full_record_public_wording_candidates import (
    PublicWordingCandidateError,
    compile_public_wording_candidate_package,
    seal,
    validate_public_wording_candidate_package,
)
from backend.scripts.build_m11k_national_security_public_wording_candidates import (
    build_package,
    preflight,
)


class PublicWordingCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ha, cls.hi, cls.ja, cls.ji = preflight()

    def package(self):
        return build_package(self.ha, self.hi, self.ja, self.ji)

    def compile_definitions(self, definitions):
        package = self.package()
        subject = package["subject"]
        excluded = {
            "m11h_authority_binding",
            "m11h_implementation_binding",
            "m11j_authority_binding",
            "m11j_implementation_binding",
            "wording_definitions",
            "wording_items",
            "wording_item_accounting",
            "complete_behavioral_synthesis_role_accounting",
            "blocked_actions",
            "source_accounting",
            "candidate_state",
            "accepted",
            "canonical_public_copy",
            "authorizing",
            "production_selectable",
            "downstream_authorizations",
        }
        base = {
            key: deepcopy(value)
            for key, value in subject.items()
            if key not in excluded
        }
        return compile_public_wording_candidate_package(
            behavioral_authority=self.ha,
            behavioral_implementation=self.hi,
            synthesis_authority=self.ja,
            synthesis_implementation=self.ji,
            wording_definitions=definitions,
            subject=base,
        )

    def test_valid_package_accounts_for_all_surfaces_and_sources(self) -> None:
        result = validate_public_wording_candidate_package(
            self.package(),
            behavioral_authority=self.ha,
            behavioral_implementation=self.hi,
            synthesis_authority=self.ja,
            synthesis_implementation=self.ji,
        )
        self.assertEqual(result["wording_item_count"], 18)
        self.assertEqual(result["wording_item_accounting"]["repeated_pattern"], 8)
        self.assertEqual(
            result["source_accounting"]["behavioral_proposition_count"], 15
        )

    def test_unknown_or_unaccepted_semantic_source_is_rejected(self) -> None:
        definitions = deepcopy(self.package()["subject"]["wording_definitions"])
        definitions[0]["semantic_sources"][0]["source_id"] = "unknown"
        with self.assertRaisesRegex(
            PublicWordingCandidateError, "unknown or unaccepted"
        ):
            self.compile_definitions(definitions)

    def test_notable_choice_cannot_become_repeated_pattern(self) -> None:
        definitions = deepcopy(self.package()["subject"]["wording_definitions"])
        notable = next(row for row in definitions if row["surface"] == "notable_choice")
        notable["surface"] = "repeated_pattern"
        with self.assertRaisesRegex(
            PublicWordingCandidateError, "semantic role changed"
        ):
            self.compile_definitions(definitions)

    def test_trajectory_cannot_become_primary_pattern(self) -> None:
        definitions = deepcopy(self.package()["subject"]["wording_definitions"])
        trajectory = next(row for row in definitions if row["surface"] == "trajectory")
        trajectory["surface"] = "repeated_pattern"
        with self.assertRaisesRegex(
            PublicWordingCandidateError, "semantic role changed"
        ):
            self.compile_definitions(definitions)

    def test_raw_yea_nay_cannot_map_to_direction(self) -> None:
        definitions = deepcopy(self.package()["subject"]["wording_definitions"])
        definitions[3]["semantic_guard"]["raw_yea_nay_maps_to_direction"] = True
        with self.assertRaisesRegex(PublicWordingCandidateError, "semantic guard"):
            self.compile_definitions(definitions)

    def test_direction_metadata_cannot_replace_semantic_content(self) -> None:
        definitions = deepcopy(self.package()["subject"]["wording_definitions"])
        definitions[2]["semantic_guard"][
            "direction_metadata_alone_establishes_public_meaning"
        ] = True
        with self.assertRaisesRegex(PublicWordingCandidateError, "semantic guard"):
            self.compile_definitions(definitions)

    def test_limitation_cannot_be_silently_removed(self) -> None:
        definitions = deepcopy(self.package()["subject"]["wording_definitions"])
        definitions[3]["limitation_treatments"].pop()
        with self.assertRaisesRegex(
            PublicWordingCandidateError, "limitation accounting"
        ):
            self.compile_definitions(definitions)

    def test_downstream_authority_leakage_fails_closed(self) -> None:
        package = self.package()
        package["subject"]["downstream_authorizations"]["publication"] = True
        package = seal(package, "public_wording_candidate_package_subject_sha256")
        with self.assertRaisesRegex(PublicWordingCandidateError, "authority boundary"):
            validate_public_wording_candidate_package(
                package,
                behavioral_authority=self.ha,
                behavioral_implementation=self.hi,
                synthesis_authority=self.ja,
                synthesis_implementation=self.ji,
            )

    def test_source_content_binding_cannot_be_rewritten(self) -> None:
        package = self.package()
        item = package["subject"]["wording_items"][3]
        item["semantic_source_bindings"][0]["proposition"] += " changed"
        package["subject"]["wording_items"][3] = seal(
            item, "wording_item_subject_sha256"
        )
        package = seal(package, "public_wording_candidate_package_subject_sha256")
        with self.assertRaisesRegex(
            PublicWordingCandidateError, "deterministic rebuild"
        ):
            validate_public_wording_candidate_package(
                package,
                behavioral_authority=self.ha,
                behavioral_implementation=self.hi,
                synthesis_authority=self.ja,
                synthesis_implementation=self.ji,
            )

    def test_ukraine_public_copy_uses_explicit_behavior_not_mixed_label(self) -> None:
        item = next(
            row
            for row in self.package()["subject"]["wording_items"]
            if row["wording_item_id"] == "wording:pattern:ukraine-assistance"
        )
        self.assertIsNone(item["direction_display"])
        self.assertEqual(
            item["semantic_source_bindings"][0]["source_direction"], "mixed"
        )
        self.assertIn("Opposed three proposals", item["primary_sentence"])
        self.assertNotIn("Mixed on Ukraine", item["primary_sentence"])

    def test_blocked_action_cannot_enter_wording_evidence(self) -> None:
        action_ids = {
            action_id
            for item in self.package()["subject"]["wording_items"]
            for binding in item["semantic_source_bindings"]
            for action_id in binding["evidence_action_ids"]
        }
        self.assertNotIn("house:119:2:278", action_ids)


if __name__ == "__main__":
    unittest.main()
