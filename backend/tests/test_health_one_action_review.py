"""Inert one-action candidate preparation and refusal of unauthorized outputs."""
import copy
import hashlib
import json
import unittest

from scripts import prepare_health_one_action_review as review
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, sealed_digest, SharedCorpusValidationError,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.semantic_ir.adapters import build_persistence_proposal
from backend.app.editorial_presentations.compiler import compile_public_issue_presentation
from backend.app.editorial_presentations.validation import EditorialPresentationError
from backend.app.editorial_artifacts.bundle import validate_bundle, semantic_hash


class HealthOneActionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = (review.PACKAGE / "DECISION-PACKET.md").read_bytes()
        cls.products = review.build_package(cls.packet)
        cls.wording = review.packet_wording(cls.packet)

    def presentation_check(self, value):
        review.validate_presentation_inputs(value, self.products["compiled_ir.json"], self.products["review_source_contract.json"], self.wording)

    def test_original_packet_and_exact_wording_parity(self):
        self.assertEqual(hashlib.sha256(self.packet).hexdigest(), review.PACKET_SHA)
        self.assertNotIn(b"\r", self.packet)
        self.assertIn(b"Decision status: **unfilled**", self.packet)
        self.assertEqual(self.packet.count(b": __________"), 6)
        self.assertIn("$1,762,668,000", self.wording["finding"])
        self.assertIn("does not itself appropriate", self.wording["finding"])
        self.assertIn("not a claim of enactment", self.wording["qualifications"])
        self.presentation_check(self.products["presentation_inputs.json"])

    def test_packet_mutation_and_newlines_fail_identity(self):
        for changed in [self.packet.replace(b"Not Voting", b"Nay", 1), self.packet.replace(b"\n", b"\r\n"), self.packet + b"\n"]:
            with self.subTest(sha=hashlib.sha256(changed).hexdigest()):
                with self.assertRaisesRegex(ValueError, "packet SHA-256 mismatch"):
                    review.build_package(changed)

    def test_exact_singleton_and_source_closure(self):
        core = self.products["shared_action_core.json"]
        mapping = self.products["shared_issue_mapping.json"]
        self.assertEqual([a["action_id"] for a in core["actions"]], [review.ACTION])
        self.assertEqual(mapping["episodes"], [{"episode_id": review.EPISODE, "action_ids": [review.ACTION], "method_boundary_types": [], "policy_family_id": None}])
        self.assertEqual(mapping["policy_families"], [])
        self.assertEqual(mapping["policy_traits"], [])
        self.assertEqual(core["actions"][0]["action_core_sha256"], "7df0c99b81ac06d558a9a6906202b25993e3f38eb9fe9a9421fd3c827e95e3e5")
        sources = self.products["governed_sources.json"]["sources"]
        self.assertEqual([s["source_id"] for s in sources], review.SOURCE_IDS)
        self.assertEqual(set(sources[0]["member_records"]), {"F000477", "M001184"})
        self.assertEqual(sources[1]["text_version"], "ES")
        self.assertEqual(len(sources[1]["text"]), 1736)
        self.assertEqual(self.products["claim_source_map.json"][0]["passage"], sources[1]["text"])

    def test_foushee_direction_and_massie_non_directional(self):
        foushee, massie = self.products["compiled_ir.json"]["members"]
        self.assertEqual(len(foushee["proposition_graph"]["propositions"]), 1)
        prop = foushee["proposition_graph"]["propositions"][0]
        self.assertEqual(prop["proposition_id"], "prop:75edca987585935c")
        self.assertEqual(prop["direction"], "support")
        self.assertEqual(foushee["coverage"]["directional_yes_no_positions"], 1)
        self.assertEqual(massie["proposition_graph"]["propositions"], [])
        self.assertEqual(massie["coverage"]["directional_yes_no_positions"], 0)
        self.assertEqual(massie["coverage"]["not_voting_actions"], 1)
        self.assertEqual(massie["action_accounting"]["non_proposition_reasons"][0]["reason_code"], "non_directional_status")
        massie_text = self.products["presentation_inputs.json"]["members"][1]["records"]["accounting"]
        self.assertEqual(massie_text["mapping"]["proposition_ids"], [])
        self.assertEqual(massie_text["mapping"]["episode_ids"], [])

    def test_shared_member_separation_and_no_expanded_authority(self):
        core_text = json.dumps(self.products["shared_action_core.json"], ensure_ascii=False)
        for name in ["Foushee", "Massie", "F000477", "M001184"]:
            self.assertNotIn(name, core_text)
        provenance = self.products["provenance.json"]
        for flag in ["new_artifacts_accepted", "production_eligible", "publication_authorized", "persistence_authorized", "full_issue_claim", "original_zip_verified"]:
            self.assertIs(provenance[flag], False)
        self.assertEqual(provenance["review_scope"], "bounded_partial_record")
        self.assertEqual(self.products["compiler_input.json"]["case_scope"], "full_record")
        self.assertIn("not original archive", provenance["git_evidence_route"])
        membership = self.products["membership_evidence.json"]
        self.assertEqual(membership["action_id"], review.ACTION)
        self.assertEqual(review.digest(membership), "cf9b26e72cfb61551dd29f4e02128d93816fb90313e7f93ba614287218669009")

    def test_build_preserves_upstream_files_and_rejection_guards(self):
        paths = [review.ROOT / review.UPSTREAM / name for name in self.products["provenance.json"]["upstream_files"]]
        paths += [review.ROOT / path for path in ["backend/app/semantic_ir/pipeline.py", "backend/app/semantic_ir/adapters.py", "backend/app/editorial_presentations/compiler.py"]]
        before = {str(p): p.read_bytes() for p in paths}
        review.build_package(self.packet)
        self.assertEqual({str(p): p.read_bytes() for p in paths}, before)

    def test_candidate_state_cannot_be_promoted_by_flag(self):
        core = copy.deepcopy(self.products["shared_action_core.json"])
        core["authoritative_for_new_editorial_work"] = True
        with self.assertRaises(SharedCorpusValidationError):
            adapt_to_semantic_ir_input(review.ROOT, core, self.products["shared_issue_mapping.json"], self.products["member_projections.json"])
        mapping = copy.deepcopy(self.products["shared_issue_mapping.json"])
        mapping["action_mappings"][0]["eligibility"]["decision"] = "accepted"
        mapping["action_mappings"][0]["mapping_sha256"] = sealed_digest(mapping["action_mappings"][0], "mapping_sha256")
        mapping["mapping_sha256"] = sealed_digest(mapping, "mapping_sha256")
        with self.assertRaisesRegex(SharedCorpusValidationError, "candidate mapping cannot claim accepted"):
            adapt_to_semantic_ir_input(review.ROOT, self.products["shared_action_core.json"], mapping, self.products["member_projections.json"])

    def test_public_and_persistence_guards_still_reject(self):
        inputs = self.products["compiler_input.json"]
        compiled = self.products["compiled_ir.json"]
        before = copy.deepcopy((inputs, compiled))
        with self.assertRaisesRegex(ValueError, "shared candidates cannot prepare"):
            run_editorial_pipeline(inputs, prepare_persistence_proposal=True)
        with self.assertRaisesRegex(ValueError, "shared candidates cannot prepare"):
            run_editorial_pipeline(inputs, public_presentation_authoring=self.products["presentation_inputs.json"])
        with self.assertRaisesRegex(ValueError, "shared candidates cannot prepare persistence"):
            build_persistence_proposal(compiled)
        with self.assertRaisesRegex(EditorialPresentationError, "shared candidates cannot compile"):
            compile_public_issue_presentation(compiled, self.products["presentation_inputs.json"], trusted_action_source_contract=self.products["review_source_contract.json"])
        self.assertEqual((inputs, compiled), before)

    def test_wording_and_semantic_reference_mutations_fail(self):
        for field in ["text", "source", "action", "episode", "proposition", "boundary", "scope"]:
            with self.subTest(field=field):
                inputs = copy.deepcopy(self.products["presentation_inputs.json"])
                record = inputs["members"][0]["records"]["finding"]
                if field == "text": record["text"] = record["text"].replace("authorize", "fund")
                elif field == "source": record["mapping"]["source_refs"] = [review.SOURCE_IDS[0]]
                elif field == "action": record["mapping"]["action_ids"].append("house:119:2:181")
                elif field == "episode": record["mapping"]["episode_ids"].append("episode:unreviewed")
                elif field == "proposition": record["mapping"]["proposition_ids"] = ["prop:unreviewed"]
                elif field == "boundary": inputs["members"][0]["boundaries"][0]["action_ids"].append("house:119:2:181")
                else: inputs["review_scope"] = "full_defined_issue_record"
                with self.assertRaises((ValueError, EditorialPresentationError)):
                    self.presentation_check(inputs)

    def test_massie_cannot_be_rendered_as_a_directional_finding(self):
        inputs = copy.deepcopy(self.products["presentation_inputs.json"])
        record = inputs["members"][1]["records"]["accounting"]
        record["mapping"]["proposition_ids"] = ["prop:75edca987585935c"]
        record["mapping"]["boundary_ids"] = []
        with self.assertRaises(ValueError):
            self.presentation_check(inputs)

    def assert_massie_boundary_swap_rejected(self, field, boundary_index):
        inputs = copy.deepcopy(self.products["presentation_inputs.json"])
        massie = inputs["members"][1]
        boundary = massie["boundaries"][boundary_index]
        mapping = massie["records"][field]["mapping"]
        # Keep the generic boundary mapping internally consistent so this tests
        # the field-specific contract, rather than an unrelated reference error.
        mapping["boundary_ids"] = [boundary["boundary_id"]]
        mapping["presentation_target"] = boundary["presentation_target"]
        mapping["action_ids"] = copy.deepcopy(boundary["action_ids"])
        mapping["episode_ids"] = copy.deepcopy(boundary.get("episode_ids", []))
        with self.assertRaisesRegex(ValueError, "field semantic reference differs"):
            self.presentation_check(inputs)

    def test_accounting_cannot_map_to_scope_boundary(self):
        self.assert_massie_boundary_swap_rejected("accounting", 0)

    def test_scope_cannot_map_to_not_voting_boundary(self):
        self.assert_massie_boundary_swap_rejected("scope_label", 1)

    def test_qualifications_cannot_map_to_not_voting_boundary(self):
        self.assert_massie_boundary_swap_rejected("qualifications", 1)

    def test_legitimate_field_mappings_keep_exact_evidence_closure(self):
        inputs = self.products["presentation_inputs.json"]
        self.presentation_check(inputs)
        for member in inputs["members"]:
            for field in ["scope_label", "qualifications"]:
                mapping = member["records"][field]["mapping"]
                self.assertEqual(mapping["boundary_ids"], [member["boundaries"][0]["boundary_id"]])
                self.assertEqual(mapping["presentation_target"], "scope_note")
                self.assertEqual(mapping["action_ids"], [review.ACTION])
                self.assertEqual(mapping["episode_ids"], [review.EPISODE])
        accounting = inputs["members"][1]["records"]["accounting"]["mapping"]
        self.assertEqual(accounting["boundary_ids"], [inputs["members"][1]["boundaries"][1]["boundary_id"]])
        self.assertEqual(accounting["presentation_target"], "coverage_note")
        self.assertEqual(accounting["action_ids"], [review.ACTION])
        self.assertEqual(accounting["episode_ids"], [])

    def test_deterministic_replay_and_checked_in_products(self):
        self.assertEqual(review.build_package(self.packet), self.products)
        for name, expected in self.products.items():
            with self.subTest(name=name):
                self.assertEqual(json.loads((review.PACKAGE / name).read_text(encoding="utf-8")), expected)
        for name, digest in self.products["provenance.json"]["derived_file_sha256"].items():
            self.assertEqual(hashlib.sha256(review.encoded(self.products[name])).hexdigest(), digest)

    def test_historical_seed_is_not_a_health_importer(self):
        substitute = {"deterministic_batch_key": "health-s2393-review", "starting_commit": review.BASE}
        substitute["manifest_sha256"] = semantic_hash(substitute)
        with self.assertRaisesRegex(ValueError, "bundle identity mismatch"):
            validate_bundle(substitute)


if __name__ == "__main__":
    unittest.main()
