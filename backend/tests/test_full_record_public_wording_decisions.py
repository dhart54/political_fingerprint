from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from backend.app.etl.full_record_public_wording_decisions import (
    PublicWordingDecisionError,
    apply_bounded_revision,
    digest,
    seal,
    validate_implementation,
)


ROOT = Path(__file__).resolve().parents[2]
M11K = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_candidates/f000477_national_security_foreign_119_v1"
)
M11L = (
    ROOT
    / "docs/editorial/full_record_reviews/public_wording_implementations/f000477_national_security_foreign_119_v1"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class PublicWordingDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = load(M11K / "public_wording_candidate_package.json")
        cls.template = load(M11K / "human_public_wording_decision_template.json")
        cls.parity = load(M11K / "parity_manifest.json")
        cls.authority = load(M11L / "human_public_wording_authority.json")
        cls.implementation = load(
            M11L / "reviewed_wording_decision_implementation.json"
        )

    def validate(self, authority=None, implementation=None):
        return validate_implementation(
            implementation or self.implementation,
            authority=authority or self.authority,
            package=self.package,
            decision_template=self.template,
            parity=self.parity,
        )

    def test_complete_package_passes(self):
        result = self.validate()
        self.assertEqual(18, result["canonical_reviewed_wording_count"])
        self.assertEqual(
            14, result["decision_accounting"]["accept_with_bounded_revision"]
        )

    def test_all_four_accepted_as_written_remain_exact(self):
        records = {
            row["wording_item_id"]: row
            for row in self.implementation["subject"]["implementation_records"]
        }
        ids = {
            key
            for key, row in records.items()
            if row["decision"] == "accept_candidate_as_written"
        }
        self.assertEqual(
            {
                "wording:synthesis:war-powers",
                "wording:trajectory:milcon-va",
                "wording:notable:haiti-tps",
                "wording:notable:fy2026-ndaa",
            },
            ids,
        )
        for key in ids:
            self.assertEqual(
                records[key]["original_candidate_content"],
                records[key]["implemented_reviewed_wording"],
            )

    def test_all_fourteen_revisions_are_implemented(self):
        records = self.implementation["subject"]["implementation_records"]
        self.assertEqual(
            14,
            sum(row["decision"] == "accept_with_bounded_revision" for row in records),
        )
        self.assertTrue(
            all(
                row["bounded_revision"]
                for row in records
                if row["decision"] == "accept_with_bounded_revision"
            )
        )

    def test_allowed_copy_and_existing_limitation_copy_pass(self):
        original = deepcopy(self.package["subject"]["wording_items"][0])
        revision = {
            "field_replacements": [
                {
                    "path": ["public_title"],
                    "original_value_sha256": digest(original["public_title"]),
                    "revised_value": "Reviewed title",
                }
            ]
        }
        revised = deepcopy(original)
        revised["public_title"] = "Reviewed title"
        revised = seal(revised, "wording_item_subject_sha256")
        revision["revised_wording_item_content_sha256"] = digest(revised)
        self.assertEqual(revised, apply_bounded_revision(original, revision))

    def test_source_identity_attack_fails_even_when_resealed(self):
        implementation = deepcopy(self.implementation)
        record = implementation["subject"]["implementation_records"][0]
        record["implemented_reviewed_wording"]["semantic_source_bindings"][0][
            "source_id"
        ] += ":attack"
        record["implemented_reviewed_wording"] = seal(
            record["implemented_reviewed_wording"], "wording_item_subject_sha256"
        )
        record["implemented_reviewed_wording_sha256"] = digest(
            record["implemented_reviewed_wording"]
        )
        implementation["subject"]["implementation_records"][0] = seal(
            record, "record_subject_sha256"
        )
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(PublicWordingDecisionError):
            self.validate(implementation=implementation)

    def test_direction_or_conclusion_attack_fails(self):
        original = deepcopy(self.package["subject"]["wording_items"][1])
        field = "direction_display" if "direction_display" in original else "surface"
        revision = {
            "field_replacements": [
                {
                    "path": [field],
                    "original_value_sha256": digest(original[field]),
                    "revised_value": "attack",
                }
            ],
            "revised_wording_item_content_sha256": "0" * 64,
        }
        with self.assertRaises(PublicWordingDecisionError):
            apply_bounded_revision(original, revision)

    def test_synthesis_relationship_role_attack_fails(self):
        implementation = deepcopy(self.implementation)
        implementation["subject"]["complete_synthesis_role_accounting"][0][
            "accounting_role"
        ] = "primary_input"
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(PublicWordingDecisionError):
            self.validate(implementation=implementation)

    def test_blocked_action_inclusion_attack_fails(self):
        implementation = deepcopy(self.implementation)
        implementation["subject"]["blocked_actions"] = []
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(PublicWordingDecisionError):
            self.validate(implementation=implementation)

    def test_downstream_authority_leakage_fails(self):
        authority = deepcopy(self.authority)
        authority["subject"]["downstream_authorizations"]["publication"] = True
        authority = seal(authority, "authority_subject_sha256")
        with self.assertRaises(PublicWordingDecisionError):
            self.validate(authority=authority)

    def test_implementation_binding_swap_fails(self):
        implementation = deepcopy(self.implementation)
        implementation["subject"]["m11j_implementation_binding"][
            "implementation_subject_sha256"
        ] = "0" * 64
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(PublicWordingDecisionError):
            self.validate(implementation=implementation)

    def test_ukraine_has_no_mixed_display(self):
        item = next(
            row["implemented_reviewed_wording"]
            for row in self.implementation["subject"]["implementation_records"]
            if row["wording_item_id"] == "wording:pattern:ukraine-assistance"
        )
        self.assertIsNone(item["direction_display"])
        self.assertNotIn("Mixed", item["primary_sentence"])

    def test_new_limitation_or_duplicate_path_fails(self):
        original = deepcopy(self.package["subject"]["wording_items"][0])
        row = {
            "path": ["public_title"],
            "original_value_sha256": digest(original["public_title"]),
            "revised_value": "x",
        }
        with self.assertRaises(PublicWordingDecisionError):
            apply_bounded_revision(
                original,
                {
                    "field_replacements": [row, row],
                    "revised_wording_item_content_sha256": "0" * 64,
                },
            )


if __name__ == "__main__":
    unittest.main()
