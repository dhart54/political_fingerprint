"""Inert one-action candidate preparation and refusal of unauthorized outputs."""
import copy
import hashlib
import json
import unittest

from scripts import prepare_health_one_action_review as review
from scripts import prepare_health_one_action_decision_packet as decision_packet
from jsonschema import Draft7Validator, ValidationError
from backend.app.semantic_ir.adapters import build_review_payload
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


class HealthOwnerDecisionPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = decision_packet.read_products()
        cls.outputs = decision_packet.build_packet(cls.products)
        cls.document = cls.outputs["OWNER-DECISION-PACKET.md"].decode("utf-8")
        cls.payload = json.loads(cls.outputs["review_payload.json"])

    def test_existing_typed_review_payload_binds_both_members_without_approval(self):
        self.assertEqual(self.payload, build_review_payload(self.products["compiled_ir.json"]))
        self.assertEqual([m["member_id"] for m in self.payload["members"]], ["F000477", "M001184"])
        self.assertIs(self.payload["approval_conferred"], False)
        self.assertEqual(self.payload["review_state"], review.CANDIDATE)
        self.assertEqual(set(self.outputs), {"review_payload.json", "OWNER-DECISION-PACKET.md"})

    def test_exact_graph_accounting_and_all_seven_mapping_objects_are_reviewable(self):
        records = [record for m in self.products["presentation_inputs.json"]["members"] for record in m["records"].values()]
        self.assertEqual(len(records), 7)
        for record in records:
            self.assertIn(decision_packet.code(record), self.document)
        for member in self.products["compiled_ir.json"]["members"]:
            exact = {key: member[key] for key in ("proposition_graph", "coverage", "action_accounting")}
            self.assertIn(decision_packet.code(exact), self.document)
        self.assertIn("conclusion_relevance=supporting", self.document)
        self.assertIn("zero behavioral propositions", self.document)
        self.assertIn("Bundle decision: __________", self.document)
        self.assertEqual(self.document.count("| Pending |"), 2)

    def test_documentary_scope_and_executable_admission_are_explicitly_distinct(self):
        for text in ("not an executable formal acceptance-chain subject", "approval_conferred=false", "executable acceptance-chain admission is unresolved", "bounded_partial_record", "Those constants are incompatible with this bounded pilot", "Original ZIP remains **unverified**", "No National Security authority is substituted"):
            self.assertIn(text, self.document)
        self.assertIn(self.payload["compiled_ir_sha256"], self.document)
        self.assertIn(review.PACKET_SHA, self.document)

    def test_review_payload_cannot_gain_approval_drop_a_member_or_change_binding(self):
        for change in ("approval", "member", "digest", "candidate"):
            value = copy.deepcopy(self.payload)
            if change == "approval": value["approval_conferred"] = True
            elif change == "member": value["members"].pop()
            elif change == "digest": value["compiled_ir_sha256"] = "0" * 64
            else: value.pop("review_state")
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "pending review payload differs"):
                decision_packet.validate_review_payload(value, self.products["compiled_ir.json"])

    def test_graph_scope_and_member_disposition_changes_are_rejected(self):
        for change in ("primary", "massie_direction", "extra_action", "full_scope"):
            products = copy.deepcopy(self.products)
            graph = products["compiled_ir.json"]["members"]
            if change == "primary": graph[0]["proposition_graph"]["propositions"][0]["conclusion_relevance"] = "primary"
            elif change == "massie_direction": graph[1]["proposition_graph"]["propositions"] = copy.deepcopy(graph[0]["proposition_graph"]["propositions"])
            elif change == "extra_action": products["shared_issue_mapping.json"]["episodes"][0]["action_ids"].append("house:119:2:181")
            else: products["presentation_inputs.json"]["review_scope"] = "full_defined_issue_record"
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "frozen Health object differs"):
                decision_packet.build_packet(products)

    def test_all_wording_and_mapping_changes_are_rejected(self):
        for index, member in enumerate(self.products["presentation_inputs.json"]["members"]):
            for field in member["records"]:
                for change in ("text", "mapping"):
                    products = copy.deepcopy(self.products)
                    record = products["presentation_inputs.json"]["members"][index]["records"][field]
                    if change == "text": record["text"] += " Unsupported expansion."
                    else: record["mapping"]["presentation_target"] = "unsupported_target"
                    with self.subTest(member=member["member_id"], field=field, change=change), self.assertRaisesRegex(ValueError, "frozen Health object differs"):
                        decision_packet.build_packet(products)

    def test_original_source_identity_and_zip_limit_cannot_be_replaced(self):
        for change in ("normalized_source", "zip_verified"):
            products = copy.deepcopy(self.products)
            if change == "normalized_source": products["governed_sources.json"]["sources"][0]["raw_sha256"] = decision_packet.RAW_EVIDENCE[1][1][:64]
            else: products["provenance.json"]["original_zip_verified"] = True
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "frozen Health object differs"):
                decision_packet.build_packet(products)

    def test_additional_raw_bytes_are_pinned_and_cannot_be_substituted(self):
        raw = {source_id: decision_packet.git_bytes(decision_packet.RAW_ROOT + name) for source_id, name in decision_packet.RAW_EVIDENCE}
        decision_packet.validate_raw_evidence(raw)
        for source_id, name in decision_packet.RAW_EVIDENCE:
            self.assertEqual(hashlib.sha256(raw[source_id]).hexdigest(), name[:64])
            changed = dict(raw)
            changed[source_id] += b"\n"
            with self.subTest(source=source_id), self.assertRaisesRegex(ValueError, "additional raw bytes differ"):
                decision_packet.build_packet(self.products, raw_sources=changed)
            self.assertIn(decision_packet.RAW_ROOT + name, self.document)
            self.assertIn(name[:64], self.document)

    def test_full_universe_receipt_cannot_admit_a_pending_bounded_review(self):
        schema = json.loads((review.ROOT / "docs/methodology/full_issue_universe_authority_receipt_v1.schema.json").read_text(encoding="utf-8"))
        for field, value in (("review_scope", "bounded_partial_record"), ("decision", None)):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Draft7Validator(schema["properties"][field]).validate(value)

    def test_existing_pending_decision_format_does_not_require_a_massie_proposition(self):
        schema = json.loads((review.ROOT / "docs/methodology/full_record_behavioral_semantic_ir_human_decision_v1.schema.json").read_text(encoding="utf-8"))
        for member, count in zip(self.products["compiled_ir.json"]["members"], (1, 0)):
            decisions = [{"proposition_id": p["proposition_id"], "decision": None, "bounded_revision": None, "reviewer_notes": None} for p in member["proposition_graph"]["propositions"]]
            self.assertEqual(len(decisions), count)
            Draft7Validator(schema["properties"]["decisions"]).validate(decisions)
            if decisions:
                decisions[0]["decision"] = "accept_candidate_as_written"
                with self.assertRaises(ValidationError):
                    Draft7Validator(schema["properties"]["decisions"]).validate(decisions)
        # Fragment conformance is deliberately not advertised as a complete
        # full-record candidate/authority-chain validation.
        self.assertIn("not proof of complete acceptance-chain admission", self.document)

    def test_candidate_public_and_persistence_guards_remain_active(self):
        for kwargs in ({"prepare_persistence_proposal": True}, {"public_presentation_authoring": self.products["presentation_inputs.json"]}):
            with self.assertRaisesRegex(ValueError, "shared candidates cannot prepare public or persistence"):
                run_editorial_pipeline(self.products["compiler_input.json"], **kwargs)

    def test_deterministic_outputs_and_no_input_or_guard_writes(self):
        paths = [review.PACKAGE / name for name in ("DECISION-PACKET.md", *decision_packet.NAMES)]
        paths += [review.ROOT / p for p in ("backend/app/semantic_ir/pipeline.py", "backend/app/semantic_ir/adapters.py", "backend/app/editorial_presentations/compiler.py")]
        before = {str(p): p.read_bytes() for p in paths}
        self.assertEqual(decision_packet.build_packet(self.products), self.outputs)
        self.assertEqual({str(p): p.read_bytes() for p in paths}, before)
        for name, expected in self.outputs.items():
            self.assertEqual((decision_packet.OUTPUT / name).read_text(encoding="utf-8"), expected.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
