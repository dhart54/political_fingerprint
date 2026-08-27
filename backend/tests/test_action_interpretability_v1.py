from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from backend.app.semantic_ir.action_interpretability import (
    ActionInterpretabilityValidationError,
    load_json,
    qualify_candidate,
    validate_candidate_set,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = ROOT / "docs/editorial/interpretability_candidates/house_119_v1/education_workforce_v1/action_interpretability_candidates.json"


class ActionInterpretabilityV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_json(CANDIDATE_PATH)

    def changed(self) -> dict:
        return copy.deepcopy(self.artifact)

    def assert_invalid(self, artifact: dict, root: Path = ROOT) -> None:
        # Do not let stale cached qualification be the reason a negative case fails.
        readiness = load_json(ROOT / self.artifact["input_bindings"]["source_readiness"]["path"])
        by_id = {row["action_id"]: row for row in readiness["subject"]["action_readiness"]}
        for candidate in artifact["candidates"]:
            candidate["qualification"] = qualify_candidate(candidate, by_id[candidate["action_id"]])
        with self.assertRaises(ActionInterpretabilityValidationError):
            validate_candidate_set(root, artifact)

    def test_real_candidate_set_validates_and_accounts_for_all_actions(self) -> None:
        result = validate_candidate_set(ROOT, self.artifact)
        self.assertEqual(result["candidate_count"], 17)
        self.assertEqual(result["candidate_state_counts"], {"candidate_complete_for_semantic_review": 15, "source_enrichment_required": 2})
        self.assertEqual(result["legacy_assessment_counts"], {"revision_would_be_required": 6, "source_enrichment_required": 2, "sufficient_unchanged": 9})

    def test_member_id_or_party_in_shared_semantics_fails(self) -> None:
        for text in ("F000477 would face this choice.", "The Democratic Party would face this choice."):
            with self.subTest(text=text):
                changed = self.changed()
                changed["candidates"][0]["policy_choice"] = text
                self.assert_invalid(changed)

    def test_member_vote_or_support_language_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["direct_effect"] = "The official member vote was Yea and supported this bill."
        self.assert_invalid(changed)

    def test_missing_substantive_source_mapping_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["claim_source_mappings"] = [
            row for row in changed["candidates"][0]["claim_source_mappings"]
            if row["field"] != "direct_effect"
        ]
        self.assert_invalid(changed)

    def test_source_mapping_claim_must_equal_the_mapped_field(self) -> None:
        changed = self.changed()
        mapping = next(
            row for row in changed["candidates"][0]["claim_source_mappings"]
            if row["field"] == "direct_effect"
        )
        mapping["claim"] = "A different claim."
        self.assert_invalid(changed)

    def test_complete_candidate_cannot_omit_plain_language_meaning(self) -> None:
        changed = self.changed()
        candidate = changed["candidates"][0]
        candidate["plain_language_meaning"] = ""
        candidate["claim_source_mappings"] = [
            row for row in candidate["claim_source_mappings"] if row["field"] != "plain_language_meaning"
        ]
        self.assert_invalid(changed)

    def test_wrong_exact_action_source_digest_binding_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["governed_source_packet_sha256"] = "0" * 64
        self.assert_invalid(changed)

    def test_amendment_relying_only_on_parent_bill_meaning_fails(self) -> None:
        changed = self.changed()
        amendment = next(row for row in changed["candidates"] if row["action_id"] == "house:119:1:79")
        for mapping in amendment["claim_source_mappings"]:
            mapping["source_id"] = "congress-text:119:hr:1048:eh"
        self.assert_invalid(changed)

    def test_whole_package_ungoverned_component_projection_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["exact_action_boundary"]["ungoverned_component_projection"] = True
        self.assert_invalid(changed)

    def test_enactment_inferred_from_house_outcome_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["plain_language_meaning"] = "This proposal became law after the House passed it."
        self.assert_invalid(changed)

    def test_downstream_prediction_as_direct_effect_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["direct_effect"] = "The proposal would likely increase university research security."
        self.assert_invalid(changed)

    def test_vague_direct_effect_with_mechanism_evidence_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["direct_effect"] = "Address institutional relationships."
        self.assert_invalid(changed)

    def test_candidate_cannot_be_silently_promoted(self) -> None:
        changed = self.changed()
        changed["candidates"][0]["accepted"] = True
        self.assert_invalid(changed)

    def test_mutation_of_each_protected_domain_artifact_fails(self) -> None:
        protected = self.artifact["protected_historical_artifacts"][:4]
        for binding in protected:
            with self.subTest(path=binding["path"]):
                target = (ROOT / binding["path"]).resolve()
                from backend.app.semantic_ir import action_interpretability as module

                original = module.file_sha256

                def mutated_digest(path: Path) -> str:
                    if path.resolve() == target:
                        return "0" * 64
                    return original(path)

                with mock.patch.object(module, "file_sha256", side_effect=mutated_digest):
                    self.assert_invalid(self.changed())

    def test_duplicate_exact_action_source_identity_fails(self) -> None:
        changed = self.changed()
        changed["candidates"][-1]["exact_action_identity"] = changed["candidates"][0]["exact_action_identity"]
        changed["candidates"][-1]["governed_source_packet_sha256"] = changed["candidates"][0]["governed_source_packet_sha256"]
        self.assert_invalid(changed)

    def test_explicit_source_hold_can_omit_unsupported_semantics(self) -> None:
        changed = self.changed()
        candidate = changed["candidates"][0]
        candidate["candidate_state"] = "source_enrichment_required"
        candidate["mechanism"] = {"type": "", "description": ""}
        candidate["affected_entities"] = []
        candidate["direct_effect"] = ""
        candidate["exact_action_boundary"]["proposal_effect"] = ""
        candidate["plain_language_meaning"] = ""
        candidate["claim_source_mappings"] = [
            row for row in candidate["claim_source_mappings"] if row["field"] in {"policy_choice", "limitations"}
        ]
        readiness = load_json(ROOT / changed["input_bindings"]["source_readiness"]["path"])
        row = next(item for item in readiness["subject"]["action_readiness"] if item["action_id"] == candidate["action_id"])
        candidate["qualification"] = qualify_candidate(candidate, row)
        result = validate_candidate_set(ROOT, changed)
        self.assertEqual(result["candidate_state_counts"]["source_enrichment_required"], 3)

    def test_hold_cannot_bypass_binding_neutrality_or_source_mappings(self) -> None:
        for failure in ("binding", "neutrality", "mapping", "boundary"):
            with self.subTest(failure=failure):
                changed = self.changed()
                candidate = next(row for row in changed["candidates"] if row["action_id"] == "house:119:1:79")
                if failure == "binding":
                    candidate["governed_source_packet_sha256"] = "0" * 64
                elif failure == "neutrality":
                    candidate["policy_choice"] = "The Democratic Party would require reporting."
                    for mapping in candidate["claim_source_mappings"]:
                        if mapping["field"] == "policy_choice":
                            mapping["claim"] = candidate["policy_choice"]
                elif failure == "mapping":
                    candidate["claim_source_mappings"] = []
                else:
                    candidate["exact_action_boundary"]["boundary_type"] = "whole_measure"
                self.assert_invalid(changed)

    def test_builder_check_does_not_regenerate_frozen_candidate_bytes(self) -> None:
        before = hashlib.sha256(CANDIDATE_PATH.read_bytes()).hexdigest()
        completed = subprocess.run(
            [sys.executable, "scripts/build_m14b_action_interpretability.py", "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(hashlib.sha256(CANDIDATE_PATH.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
