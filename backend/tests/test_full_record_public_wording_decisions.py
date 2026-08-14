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
    validate_authority,
    validate_implementation,
)
from scripts.validate_public_wording_decision_implementation_v1 import (
    validate_direct_sources,
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


def replace_path(value: object, path: list[object], replacement: object) -> None:
    cursor = value
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[path[-1]] = deepcopy(replacement)  # type: ignore[index]


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

    def authority_with_revision(self, path: list[object], value: object) -> dict:
        authority = deepcopy(self.authority)
        item_id = "wording:issue-overview:national-security-foreign:119"
        original = next(
            row
            for row in self.package["subject"]["wording_items"]
            if row["wording_item_id"] == item_id
        )
        revised = deepcopy(original)
        replace_path(revised, path, value)
        revised = seal(revised, "wording_item_subject_sha256")
        decision = next(
            row
            for row in authority["subject"]["wording_decisions"]
            if row["wording_item_id"] == item_id
        )
        decision["decision"] = "accept_with_bounded_revision"
        decision["bounded_revision"] = {
            "field_replacements": [
                {
                    "path": path,
                    "original_value_sha256": digest(self.value_at_path(original, path)),
                    "revised_value": value,
                }
            ],
            "revised_wording_item_content_sha256": digest(revised),
        }
        authority["subject"]["wording_decisions"] = [
            seal(row, "decision_subject_sha256")
            if row["wording_item_id"] == item_id
            else row
            for row in authority["subject"]["wording_decisions"]
        ]
        return seal(authority, "authority_subject_sha256")

    @staticmethod
    def value_at_path(value: object, path: list[object]) -> object:
        cursor = value
        for key in path:
            cursor = cursor[key]  # type: ignore[index]
        return cursor

    def different_sized_fixture(self):
        selected_ids = {
            "wording:synthesis:war-powers",
            "wording:pattern:fisa-title-vii",
            "wording:notable:haiti-tps",
        }
        package = deepcopy(self.package)
        package["artifact_id"] = "public-wording-candidates:synthetic:other:1:v1"
        package["subject"]["wording_items"] = [
            row
            for row in package["subject"]["wording_items"]
            if row["wording_item_id"] in selected_ids
        ]
        package = seal(package, "public_wording_candidate_package_subject_sha256")

        template = deepcopy(self.template)
        template["artifact_id"] = (
            "human-public-wording-decision-template:synthetic:other:1:v1"
        )
        template["wording_decisions"] = [
            row
            for row in template["wording_decisions"]
            if row["wording_item_id"] in selected_ids
        ]
        template = seal(template, "decision_template_subject_sha256")

        parity = deepcopy(self.parity)
        parity["artifact_id"] = "public-wording-candidate-parity:synthetic:other:1:v1"
        parity = seal(parity, "parity_subject_sha256")

        authority = deepcopy(self.authority)
        authority["artifact_id"] = "human-public-wording-authority:synthetic:other:1:v1"
        authority["subject"]["reviewer"] = "reviewer-other"
        authority["subject"]["reviewer_authority"] = (
            "synthetic_public_wording_review_authority_v1"
        )
        authority["subject"]["candidate_binding"] = {
            "artifact_id": package["artifact_id"],
            "file_sha256": "1" * 64,
            "package_subject_sha256": package[
                "public_wording_candidate_package_subject_sha256"
            ],
        }
        authority["subject"]["decision_template_binding"] = {
            "artifact_id": template["artifact_id"],
            "file_sha256": "2" * 64,
            "decision_template_subject_sha256": template[
                "decision_template_subject_sha256"
            ],
        }
        authority["subject"]["parity_binding"] = {
            "artifact_id": parity["artifact_id"],
            "file_sha256": "3" * 64,
            "parity_subject_sha256": parity["parity_subject_sha256"],
        }
        decisions = []
        for row in authority["subject"]["wording_decisions"]:
            if row["wording_item_id"] not in selected_ids:
                continue
            row["reviewer"] = "reviewer-other"
            row["reviewer_authority"] = "synthetic_public_wording_review_authority_v1"
            decisions.append(seal(row, "decision_subject_sha256"))
        authority["subject"]["wording_decisions"] = decisions
        authority["subject"]["decision_accounting"] = {
            "accept_candidate_as_written": 2,
            "accept_with_bounded_revision": 1,
            "rejected": 0,
            "unresolved": 0,
        }
        authority = seal(authority, "authority_subject_sha256")

        decision_by_id = {row["wording_item_id"]: row for row in decisions}
        implementation = deepcopy(self.implementation)
        implementation["artifact_id"] = (
            "reviewed-wording-decision-implementation:synthetic:other:1:v1"
        )
        implementation["subject"]["authority_binding"] = {
            "artifact_id": authority["artifact_id"],
            "authority_subject_sha256": authority["authority_subject_sha256"],
        }
        implementation["subject"]["candidate_binding"] = authority["subject"][
            "candidate_binding"
        ]
        records = []
        for row in implementation["subject"]["implementation_records"]:
            if row["wording_item_id"] not in selected_ids:
                continue
            decision = decision_by_id[row["wording_item_id"]]
            row["authority_artifact_id"] = authority["artifact_id"]
            row["authority_subject_sha256"] = authority["authority_subject_sha256"]
            row["authority_decision_subject_sha256"] = decision[
                "decision_subject_sha256"
            ]
            records.append(seal(row, "record_subject_sha256"))
        implementation["subject"]["implementation_records"] = records
        implementation["subject"]["final_accounting"] = {
            "canonical_reviewed_wording_count": 3,
            "surface_accounting": {
                "synthesis": 1,
                "repeated_pattern": 1,
                "notable_choice": 1,
            },
            "decision_accounting": authority["subject"]["decision_accounting"],
        }
        implementation = seal(implementation, "implementation_subject_sha256")
        return package, template, parity, authority, implementation

    def test_complete_package_passes(self):
        result = self.validate()
        self.assertEqual(18, result["canonical_reviewed_wording_count"])
        self.assertEqual(
            14, result["decision_accounting"]["accept_with_bounded_revision"]
        )

    def test_direct_source_package_template_and_parity_integrity_passes(self):
        validate_direct_sources(
            authority=self.authority,
            package=self.package,
            package_path=M11K / "public_wording_candidate_package.json",
            decision_template=self.template,
            decision_template_path=M11K / "human_public_wording_decision_template.json",
            candidate_parity=self.parity,
            candidate_parity_path=M11K / "parity_manifest.json",
        )

    def test_direct_source_identity_attacks_fail(self):
        cases = (
            (
                "package",
                seal(
                    {**deepcopy(self.package), "artifact_id": "package-attack"},
                    "public_wording_candidate_package_subject_sha256",
                ),
                self.template,
                self.parity,
            ),
            (
                "template",
                self.package,
                seal(
                    {**deepcopy(self.template), "artifact_id": "template-attack"},
                    "decision_template_subject_sha256",
                ),
                self.parity,
            ),
            (
                "parity",
                self.package,
                self.template,
                seal(
                    {**deepcopy(self.parity), "artifact_id": "parity-attack"},
                    "parity_subject_sha256",
                ),
            ),
        )
        for label, package, template, parity in cases:
            with self.subTest(source=label), self.assertRaises(ValueError):
                validate_direct_sources(
                    authority=self.authority,
                    package=package,
                    package_path=M11K / "public_wording_candidate_package.json",
                    decision_template=template,
                    decision_template_path=M11K
                    / "human_public_wording_decision_template.json",
                    candidate_parity=parity,
                    candidate_parity_path=M11K / "parity_manifest.json",
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

    def test_allowed_authority_copy_revisions_pass(self):
        cases = (
            (["public_title"], "Reviewed title"),
            (["primary_sentence"], "Reviewed primary sentence."),
            (["secondary_clarification"], "Reviewed clarification."),
            (["evidence_count_label"], "Reviewed evidence label"),
            (
                ["limitation_treatments", 0, "public_copy"],
                "Reviewed limitation copy.",
            ),
            (
                ["limitation_treatments", 0, "reason"],
                "Reviewed explanatory reason.",
            ),
        )
        for path, value in cases:
            with self.subTest(path=path):
                validate_authority(
                    self.authority_with_revision(path, value),
                    package=self.package,
                    decision_template=self.template,
                    parity=self.parity,
                )

    def test_resealed_authority_cannot_revise_structural_or_evidence_state(self):
        item = next(
            row
            for row in self.package["subject"]["wording_items"]
            if row["wording_item_id"]
            == "wording:issue-overview:national-security-foreign:119"
        )
        synthesis_index = next(
            index
            for index, source in enumerate(item["semantic_source_bindings"])
            if source["relationship_roles"]
        )
        cases = (
            (["wording_item_id"], "wording:attack"),
            (["surface"], "attack_surface"),
            (["semantic_source_bindings", 0, "source_id"], "source-attack"),
            (["semantic_source_bindings", 0, "source_kind"], "attack-kind"),
            (
                ["semantic_source_bindings", 0, "implementation_record_id"],
                "implementation-attack",
            ),
            (
                [
                    "semantic_source_bindings",
                    0,
                    "implementation_record_subject_sha256",
                ],
                "0" * 64,
            ),
            (
                ["semantic_source_bindings", 0, "accepted_semantic_content_sha256"],
                "0" * 64,
            ),
            (["semantic_source_bindings", 0, "source_direction"], "support"),
            (
                [
                    "semantic_source_bindings",
                    synthesis_index,
                    "relationship_roles",
                    0,
                    "relationship_role",
                ],
                "attack_role",
            ),
            (
                ["semantic_source_bindings", 0, "evidence_episode_ids", 0],
                "episode-attack",
            ),
            (
                ["semantic_source_bindings", 0, "evidence_action_ids", 0],
                "action-attack",
            ),
            (["limitation_treatments", 0, "source_id"], "limitation-attack"),
        )
        for path, value in cases:
            with self.subTest(path=path), self.assertRaises(PublicWordingDecisionError):
                validate_authority(
                    self.authority_with_revision(path, value),
                    package=self.package,
                    decision_template=self.template,
                    parity=self.parity,
                )

    def test_resealed_authority_cannot_change_other_governed_boundaries(self):
        attacks = (
            (
                [
                    "complete_synthesis_role_accounting",
                    0,
                    "source_conclusion_relevance",
                ],
                "attack",
            ),
            (["blocked_action_boundary", "state"], "available"),
            (["downstream_authorizations", "publication"], True),
            (["downstream_authorizations", "production_writes"], True),
        )
        for path, value in attacks:
            authority = deepcopy(self.authority)
            replace_path(authority["subject"], path, value)
            authority = seal(authority, "authority_subject_sha256")
            with self.subTest(path=path), self.assertRaises(PublicWordingDecisionError):
                validate_authority(
                    authority,
                    package=self.package,
                    decision_template=self.template,
                    parity=self.parity,
                )

    def test_differently_sized_different_reviewer_fixture_passes(self):
        package, template, parity, authority, implementation = (
            self.different_sized_fixture()
        )
        accounting = validate_authority(
            authority,
            package=package,
            decision_template=template,
            parity=parity,
        )
        result = validate_implementation(
            implementation,
            authority=authority,
            package=package,
            decision_template=template,
            parity=parity,
        )
        self.assertEqual("reviewer-other", authority["subject"]["reviewer"])
        self.assertEqual(3, result["canonical_reviewed_wording_count"])
        self.assertEqual(
            {"synthesis": 1, "repeated_pattern": 1, "notable_choice": 1},
            result["surface_accounting"],
        )
        self.assertEqual(accounting, result["decision_accounting"])

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
