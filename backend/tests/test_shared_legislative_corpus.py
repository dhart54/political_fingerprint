from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.pipeline import run_editorial_pipeline  # noqa: E402
from backend.app.semantic_ir.shared_corpus import (  # noqa: E402
    SharedCorpusValidationError,
    adapt_to_semantic_ir_input,
    assert_no_protected_artifact_changes,
    digest,
    sealed_digest,
    validate_member_projection,
    validate_migration_parity,
    validate_shared_action_core,
    validate_shared_issue_mapping,
)


CORPUS = ROOT / "docs/editorial/shared_corpora/house_119_v1"
ISSUE = CORPUS / "issue_mappings/justice_public_safety_v1"
LEGACY_INPUT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiler_input.json"
)
LEGACY_OUTPUT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiled_semantic_ir.json"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SharedLegislativeCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = load(CORPUS / "shared_action_core.json")
        cls.mapping = load(ISSUE / "shared_issue_mapping.json")
        cls.foushee = load(CORPUS / "member_projections/f000477.json")
        cls.grothman = load(CORPUS / "member_projections/g000576.json")
        cls.legacy_input = load(LEGACY_INPUT)["compiler_input"]
        cls.legacy_output = load(LEGACY_OUTPUT)["compiled_ir"]

    def test_contracts_and_two_member_compiler_proof(self) -> None:
        validate_shared_action_core(ROOT, self.core)
        validate_shared_issue_mapping(ROOT, self.mapping, self.core)
        validate_member_projection(ROOT, self.foushee, self.core)
        validate_member_projection(ROOT, self.grothman, self.core)
        self.assertEqual(len(self.core["actions"]), 37)
        payload = adapt_to_semantic_ir_input(
            ROOT, self.core, self.mapping, [self.foushee, self.grothman]
        )
        result = run_editorial_pipeline(
            payload,
            prepare_persistence_proposal=False,
            public_presentation_authoring=None,
        ).compiled_ir
        counts = {
            row["member_id"]: len(row["proposition_graph"]["propositions"])
            for row in result["members"]
        }
        self.assertEqual(counts, {"F000477": 24, "G000576": 24})

    def test_foushee_adapter_input_and_output_parity(self) -> None:
        payload = adapt_to_semantic_ir_input(
            ROOT, self.core, self.mapping, [self.foushee]
        )
        validate_migration_parity(
            payload, self.legacy_input, "accepted Foushee compiler input"
        )
        result = run_editorial_pipeline(
            payload,
            prepare_persistence_proposal=False,
            public_presentation_authoring=None,
        ).compiled_ir
        validate_migration_parity(
            result, self.legacy_output, "accepted Foushee Semantic IR output"
        )

    def test_member_and_party_fields_in_shared_action_fail(self) -> None:
        changed = copy.deepcopy(self.core)
        changed["actions"][0]["party"] = "D"
        with self.assertRaises(SharedCorpusValidationError):
            validate_shared_action_core(ROOT, changed)

    def test_shared_action_core_identity_is_issue_neutral(self) -> None:
        self.assertEqual(self.core["artifact_id"], "shared-action-core:house:119:v1")
        changed = copy.deepcopy(self.core)
        changed["artifact_id"] = "shared-action-core:justice-public-safety:119:v1"
        with self.assertRaises(SharedCorpusValidationError):
            validate_shared_action_core(ROOT, changed)

    def test_member_and_party_fields_in_shared_mapping_fail(self) -> None:
        changed = copy.deepcopy(self.mapping)
        changed["action_mappings"][0]["member_id"] = "F000477"
        with self.assertRaises(SharedCorpusValidationError):
            validate_shared_issue_mapping(ROOT, changed, self.core)

    def test_changed_meaning_and_source_binding_fail_parity(self) -> None:
        changed = copy.deepcopy(self.core)
        changed["actions"][0]["accepted_exact_action_meaning"] += " Changed."
        with self.assertRaises(SharedCorpusValidationError):
            validate_migration_parity(changed, self.core, "shared action meaning")
        changed = copy.deepcopy(self.core)
        changed["actions"][0]["semantic_ir_source_ids"][0] = "changed-source"
        with self.assertRaises(SharedCorpusValidationError):
            validate_migration_parity(changed, self.core, "source binding")

    def test_conflicting_current_meanings_fail(self) -> None:
        changed = copy.deepcopy(self.core)
        duplicate = copy.deepcopy(changed["actions"][0])
        duplicate["accepted_exact_action_meaning"] += " Conflict."
        duplicate["action_core_sha256"] = sealed_digest(duplicate, "action_core_sha256")
        changed["actions"].append(duplicate)
        changed["corpus_sha256"] = digest(changed["actions"])
        with self.assertRaisesRegex(
            SharedCorpusValidationError, "conflicting current meanings"
        ):
            validate_shared_action_core(ROOT, changed)

    def test_member_projection_cannot_override_meaning(self) -> None:
        changed = copy.deepcopy(self.foushee)
        changed["actions"][0]["action_meaning_override"] = "member prose"
        with self.assertRaises(SharedCorpusValidationError):
            validate_member_projection(ROOT, changed, self.core)

    def test_wrong_action_or_source_digest_fails(self) -> None:
        changed = copy.deepcopy(self.foushee)
        changed["actions"][0]["action_core_sha256"] = "0" * 64
        with self.assertRaisesRegex(SharedCorpusValidationError, "wrong action digest"):
            validate_member_projection(ROOT, changed, self.core)
        changed = copy.deepcopy(self.foushee)
        changed["actions"][0]["member_action_source_identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(SharedCorpusValidationError, "wrong source digest"):
            validate_member_projection(ROOT, changed, self.core)

    def test_internally_consistent_wrong_member_source_identity_fails(self) -> None:
        changed = copy.deepcopy(self.foushee)
        wrong_source = copy.deepcopy(
            self.core["actions"][1]["action_outcome_source_identities"]
        )
        changed["actions"][0]["member_action_source_identities"] = wrong_source
        changed["actions"][0]["member_action_source_identity_sha256"] = digest(
            wrong_source
        )
        changed["projection_sha256"] = sealed_digest(changed, "projection_sha256")
        with self.assertRaisesRegex(
            SharedCorpusValidationError, "does not match governed exact-action source"
        ):
            validate_member_projection(ROOT, changed, self.core)

    def test_core_source_roles_and_semantic_ids_must_be_governed(self) -> None:
        changed = copy.deepcopy(self.core)
        changed["actions"][0]["operative_meaning_source_identities"] = copy.deepcopy(
            changed["actions"][1]["operative_meaning_source_identities"]
        )
        changed["actions"][0]["action_core_sha256"] = sealed_digest(
            changed["actions"][0], "action_core_sha256"
        )
        changed["corpus_sha256"] = digest(changed["actions"])
        with self.assertRaisesRegex(SharedCorpusValidationError, "not governed"):
            validate_shared_action_core(ROOT, changed)

        changed = copy.deepcopy(self.core)
        changed["actions"][0]["semantic_ir_source_ids"] = ["wrong-source"]
        changed["actions"][0]["action_core_sha256"] = sealed_digest(
            changed["actions"][0], "action_core_sha256"
        )
        changed["corpus_sha256"] = digest(changed["actions"])
        with self.assertRaisesRegex(SharedCorpusValidationError, "does not resolve"):
            validate_shared_action_core(ROOT, changed)

    def test_ungoverned_package_component_projection_fails(self) -> None:
        changed = copy.deepcopy(self.foushee)
        package = next(
            row for row in changed["actions"] if row["action_id"] == "house:119:2:278"
        )
        package["component_ref"] = "justice-component"
        changed["projection_sha256"] = digest(
            {key: value for key, value in changed.items() if key != "projection_sha256"}
        )
        with self.assertRaisesRegex(
            SharedCorpusValidationError, "ungoverned package component"
        ):
            validate_member_projection(ROOT, changed, self.core)

    def test_member_projection_is_reusable_with_separate_issue_mapping(self) -> None:
        projection = copy.deepcopy(self.foushee)
        alternate_mapping = copy.deepcopy(self.mapping)
        alternate_mapping["artifact_id"] = "shared-issue-mapping:reuse-proof:119:v1"
        alternate_mapping["domain_id"] = "REUSE_PROOF"
        singleton_episode = next(
            episode
            for episode in alternate_mapping["episodes"]
            if len(episode["action_ids"]) == 1
        )
        selected_action_id = singleton_episode["action_ids"][0]
        alternate_mapping["action_mappings"] = [
            row
            for row in alternate_mapping["action_mappings"]
            if row["action_id"] == selected_action_id
        ]
        alternate_mapping["episodes"] = [singleton_episode]
        alternate_mapping["mapping_sha256"] = sealed_digest(
            alternate_mapping, "mapping_sha256"
        )
        before = projection["projection_sha256"]
        validate_member_projection(ROOT, projection, self.core)
        payload = adapt_to_semantic_ir_input(
            ROOT, self.core, alternate_mapping, [projection]
        )
        self.assertEqual(before, projection["projection_sha256"])
        self.assertEqual(
            [row["action_id"] for row in payload["members"][0]["actions"]],
            [selected_action_id],
        )
        self.assertEqual(
            payload["shared_semantics"]["actions"][0]["eligibility"]["domain"],
            "REUSE_PROOF",
        )

        incomplete_projection = copy.deepcopy(projection)
        incomplete_projection["actions"] = [
            row
            for row in incomplete_projection["actions"]
            if row["action_id"] != selected_action_id
        ]
        incomplete_projection["projection_sha256"] = sealed_digest(
            incomplete_projection, "projection_sha256"
        )
        with self.assertRaisesRegex(SharedCorpusValidationError, "lacks mapped actions"):
            adapt_to_semantic_ir_input(
                ROOT, self.core, alternate_mapping, [incomplete_projection]
            )

    def test_non_directional_contract_and_party_invariance(self) -> None:
        from backend.app.semantic_ir.shared_corpus import choice_effect

        self.assertEqual(choice_effect("Present"), "resolved_non_directional")
        self.assertEqual(choice_effect("Not Voting"), "resolved_non_directional")
        before = (self.core["corpus_sha256"], self.mapping["mapping_sha256"])
        changed = copy.deepcopy(self.grothman)
        changed["party"] = "MUTATED"
        self.assertEqual(
            before, (self.core["corpus_sha256"], self.mapping["mapping_sha256"])
        )

    def test_adapter_parity_and_historical_protection_fail_closed(self) -> None:
        changed = copy.deepcopy(self.mapping)
        changed["action_mappings"][0]["policy_trait_refs"] = []
        changed["action_mappings"][0]["mapping_sha256"] = sealed_digest(
            changed["action_mappings"][0], "mapping_sha256"
        )
        changed["mapping_sha256"] = sealed_digest(changed, "mapping_sha256")
        payload = adapt_to_semantic_ir_input(ROOT, self.core, changed, [self.foushee])
        with self.assertRaisesRegex(
            SharedCorpusValidationError, "accepted Foushee compiler input"
        ):
            validate_migration_parity(
                payload, self.legacy_input, "accepted Foushee compiler input"
            )
        with self.assertRaisesRegex(
            SharedCorpusValidationError, "historical protected artifacts"
        ):
            assert_no_protected_artifact_changes(
                [
                    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/example.json"
                ]
            )


if __name__ == "__main__":
    unittest.main()
