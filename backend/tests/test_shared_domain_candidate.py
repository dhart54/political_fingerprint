"""Real Health source bindings and focused candidate/update invariants."""
import copy
import json
import unittest
from pathlib import Path

from scripts.prepare_shared_domain_candidate import prepare, readable_candidates, reproducibility_proof, review_text, validate_universe_proposal
from backend.app.semantic_ir.shared_corpus import (
    adapt_to_semantic_ir_input, candidate_update_impact, choice_effect, digest,
    sealed_digest, validate_member_projection, validate_shared_action_core,
    SharedCorpusValidationError,
)
from backend.app.semantic_ir.pipeline import run_editorial_pipeline
from backend.app.semantic_ir.compiler import SemanticCompilerInputError
from backend.app.semantic_ir.adapters import build_persistence_proposal
from backend.app.editorial_presentations.compiler import compile_public_issue_presentation, EditorialPresentationError

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/editorial/shared_candidates/house_119_health_20260916"


class SharedDomainCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author = json.loads((DATA / "authoring.json").read_text(encoding="utf-8"))
        cls.capture = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
        cls.products = prepare(cls.author, cls.capture, ["F000477", "M001184"])

    def test_offline_determinism_and_checked_in_outputs(self):
        core, mapping, projections, inputs, result = self.products
        again = prepare(self.author, self.capture, ["F000477", "M001184"])
        self.assertEqual(digest(result.compiled_ir), digest(again[-1].compiled_ir))
        outputs = {"shared_action_core": core, "shared_issue_mapping": mapping,
            "member_projections": projections, "compiler_input": inputs, "compiled_ir": result.compiled_ir,
            "readable_candidates": readable_candidates(self.author, core, projections, result)}
        for name, value in outputs.items():
            self.assertEqual(value, json.loads((DATA / "generated" / f"{name}.json").read_text(encoding="utf-8")), name)

    def test_real_members_reuse_meaning_for_matching_different_and_nonvoting_choices(self):
        core, _, projections, _, _ = self.products
        f, m = [{a["action_id"]: a for a in p["actions"]} for p in projections]
        self.assertEqual(f["house:119:1:349"]["official_status"], m["house:119:1:349"]["official_status"])
        self.assertEqual((f["house:119:1:362"]["official_status"], m["house:119:1:362"]["official_status"]), ("Nay", "Yea"))
        self.assertEqual(m["house:119:1:306"]["official_status"], "Not Voting")
        for action in core["actions"]:
            aid = action["action_id"]
            self.assertEqual(f[aid]["action_core_sha256"], m[aid]["action_core_sha256"])
            for row in [f[aid], m[aid]]:
                self.assertEqual(row["exact_choice_effect"], choice_effect(row["official_status"]))

    def test_proof_and_readable_packet_are_reproducible(self):
        proof = reproducibility_proof(self.author, self.capture, ["F000477", "M001184"])
        self.assertEqual(proof, json.loads((DATA / "generated/reproducibility_proof.json").read_text(encoding="utf-8")))
        core, _, projections, _, result = self.products
        packet = (ROOT / "docs/review_packets/foushee_health_shared_candidate.md").read_text(encoding="utf-8")
        generated = packet.split("<!-- GENERATED CANDIDATE START -->\n", 1)[1].split("<!-- GENERATED CANDIDATE END -->", 1)[0]
        self.assertEqual(generated, review_text(self.author, core, projections, result, self.capture))
        other = prepare(self.author, self.capture, ["M001184"])
        self.assertTrue(review_text(self.author, other[0], other[2], other[-1], self.capture).startswith("## Generated Massie candidate findings"))

    def test_member_identity_and_party_do_not_change_graph(self):
        inputs = copy.deepcopy(self.products[3])
        expected = self.products[-1].compiled_ir["members"][0]
        inputs["members"] = [inputs["members"][0]]
        inputs["members"][0].update(member_id="synthetic-identity", party="synthetic-party")
        result = run_editorial_pipeline(inputs).compiled_ir["members"][0]
        for field in ["coverage", "proposition_graph", "composition", "action_accounting"]:
            self.assertEqual(expected[field], result[field])

    def test_projection_cannot_override_meaning(self):
        core, _, projections, _, _ = self.products
        p = copy.deepcopy(projections[0])
        p["actions"][0]["candidate_exact_action_meaning"] = "different"
        p["projection_sha256"] = sealed_digest(p, "projection_sha256")
        with self.assertRaises(SharedCorpusValidationError):
            validate_member_projection(ROOT, p, core)

    def test_proposed_state_cannot_be_laundered_as_accepted(self):
        core = copy.deepcopy(self.products[0])
        core["authoritative_for_new_editorial_work"] = True
        core.pop("review_state")
        with self.assertRaisesRegex(SharedCorpusValidationError, "authority disagree"):
            validate_shared_action_core(ROOT, core)
        inputs = copy.deepcopy(self.products[3]); inputs.pop("review_state")
        with self.assertRaisesRegex(SemanticCompilerInputError, "explicit candidate"):
            run_editorial_pipeline(inputs)

    def test_candidates_cannot_prepare_public_or_persistence_artifacts(self):
        inputs = self.products[3]; compiled = self.products[-1].compiled_ir
        with self.assertRaisesRegex(ValueError, "cannot prepare"):
            run_editorial_pipeline(inputs, prepare_persistence_proposal=True)
        with self.assertRaises(ValueError):
            build_persistence_proposal(compiled)
        with self.assertRaises(EditorialPresentationError):
            compile_public_issue_presentation(compiled, {}, trusted_action_source_contract={})

    def test_source_and_claim_mutations_fail(self):
        capture = copy.deepcopy(self.capture); capture["sources"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "governed source changed"):
            prepare(self.author, capture, ["F000477"])
        author = copy.deepcopy(self.author); author["actions"][2]["claim_source_map"][0]["passage"] = "invented passage"
        with self.assertRaisesRegex(ValueError, "claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_exact_action_cutoff_and_member_guards(self):
        author = copy.deepcopy(self.author); author["interpretation_action_set_cutoff"] = "2026-07-22"
        with self.assertRaisesRegex(ValueError, "cannot extend"):
            prepare(author, self.capture, ["F000477"])
        with self.assertRaisesRegex(ValueError, "does not contain member"):
            prepare(self.author, self.capture, ["synthetic-absent"])

    def test_raw_ledger_update_does_not_extend_interpretation(self):
        capture = copy.deepcopy(self.capture)
        source = {"source_id": "synthetic:raw-later", "text": "new uninterpreted ledger observation"}
        source["governed_bytes_sha256"] = digest(source); capture["sources"].append(source)
        result = prepare(self.author, capture, ["F000477", "M001184"])
        self.assertEqual(digest(self.products[-1].compiled_ir), digest(result[-1].compiled_ir))
        self.assertEqual(self.products[0], result[0])

    def test_shared_correction_identifies_both_members_and_findings(self):
        core, _, projections, _, result = self.products
        changed = copy.deepcopy(core)
        action = next(a for a in changed["actions"] if a["action_id"] == "house:119:1:362")
        action["candidate_shared_limitations"].append("Synthetic controlled correction; not accepted or published.")
        action["action_core_sha256"] = sealed_digest(action, "action_core_sha256")
        changed["corpus_sha256"] = digest(changed["actions"])
        impact = candidate_update_impact(core, changed, projections, result.compiled_ir)
        self.assertEqual(impact["changed_action_ids"], ["house:119:1:362"])
        self.assertEqual({x["member_id"] for x in impact["affected_projections"]}, {"F000477", "M001184"})
        self.assertEqual(len(impact["affected_findings"]), 2)
        with self.assertRaisesRegex(SharedCorpusValidationError, "wrong action digest"):
            validate_member_projection(ROOT, projections[0], changed)
        self.assertNotEqual(core["corpus_sha256"], changed["corpus_sha256"])

    def test_complete_supplied_accounting_and_real_paired_episode(self):
        core, mapping, projections, _, result = self.products
        all_ids = {a["action_id"] for a in core["actions"]}
        for member in result.compiled_ir["members"]:
            acc = member["action_accounting"]
            represented = set(acc["behavioral_proposition_action_ids"])
            reasons = {r["action_id"] for r in acc["non_proposition_reasons"]}
            self.assertFalse(represented & reasons)
            self.assertEqual(represented | reasons, all_ids)
        pair = next(e for e in mapping["episodes"] if len(e["action_ids"]) == 2)
        self.assertEqual(pair["action_ids"], ["house:119:1:150", "house:119:1:151"])
        for member, status, direction in zip(result.compiled_ir["members"], ["Yea", "Nay"], ["support", "opposition"]):
            p = next(p for p in member["proposition_graph"]["propositions"] if any(o["action_id"] == "house:119:1:150" for o in p.get("action_observations", [])))
            self.assertEqual(p["proposition_type"], "notable_choice")
            self.assertEqual(p["direction"], direction)
            self.assertEqual([o["action_id"] for o in p["action_observations"]], pair["action_ids"])
            self.assertEqual([o["status"] for o in p["action_observations"]], [status, status])
            self.assertEqual(len(p["evidence_episode_ids"]), 1)
        self.assertEqual(result.review_payload["review_state"], self.author["review_state"])
        self.assertEqual(result.presentation_payload["review_state"], self.author["review_state"])

    def test_genuine_trajectory_path_still_requires_trusted_comparison(self):
        # Synthetic request to the unchanged non-candidate trajectory path;
        # this constructs no accepted artifact or comparison authority.
        inputs = copy.deepcopy(self.products[3]); inputs.pop("review_state")
        for action in inputs["shared_semantics"]["actions"]:
            action["eligibility"]["decision"] = "accepted"
        with self.assertRaisesRegex(SemanticCompilerInputError, "new trajectory requires"):
            run_editorial_pipeline(inputs)

    def test_paired_synthetic_mixed_and_missing_observations(self):
        for statuses in [("Yea", "Nay"), ("Nay", "Yea"), ("Yea", "Not Voting"),
                         ("Present", "Nay"), ("Yea", "Missing Evidence"), ("Present", "Not Voting")]:
            inputs = copy.deepcopy(self.products[3]); inputs["members"] = inputs["members"][:1]
            for action, status in zip(inputs["members"][0]["actions"][:2], statuses):
                action["status"] = status
                if status == "Missing Evidence": action["evidence_status"] = "missing"
            result = run_editorial_pipeline(inputs).compiled_ir["members"][0]
            pairs = [p for p in result["proposition_graph"]["propositions"] if any(o["action_id"] == "house:119:1:150" for o in p.get("action_observations", []))]
            directional = [s for s in statuses if s in {"Yea", "Nay"}]
            if not directional:
                self.assertFalse(pairs)
                continue
            pair = pairs[0]
            self.assertEqual([o["status"] for o in pair["action_observations"]], list(statuses))
            self.assertEqual(len(pair["evidence_action_ids"]), len(directional))
            self.assertEqual(pair["direction"], "mixed" if len(set(directional)) == 2 else {"Yea":"support","Nay":"opposition"}[directional[0]])

    def test_synthetic_status_and_context_controls_do_not_count(self):
        for status in ["Present", "Not Voting", "Missing Evidence"]:
            inputs = copy.deepcopy(self.products[3]); inputs["members"] = inputs["members"][:1]
            inputs["members"][0]["actions"][2]["status"] = status
            if status == "Missing Evidence":
                inputs["members"][0]["actions"][2]["evidence_status"] = "missing"
            compiled = run_editorial_pipeline(inputs).compiled_ir["members"][0]
            self.assertNotIn("house:119:1:306", compiled["action_accounting"]["behavioral_proposition_action_ids"])
        inputs = copy.deepcopy(self.products[3])
        action = inputs["shared_semantics"]["actions"][2]
        action["eligibility"]["decision"] = "context_only"
        inputs["shared_semantics"]["episodes"] = [e for e in inputs["shared_semantics"]["episodes"] if action["action_id"] not in e["action_ids"]]
        result = run_editorial_pipeline(inputs).compiled_ir
        self.assertEqual(result["members"][0]["coverage"]["eligible_substantive_actions"], len(self.author["actions"]) - 1)

    def test_readable_output_preserves_package_limits_and_actual_mechanisms(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        f = readable["members"][0]
        self.assertEqual(len(f["findings"]), 49)
        by_action = {x["action_ids"][0]: x for x in f["findings"]}
        self.assertIn("abortion", by_action["house:119:1:349"]["detail"][1])
        self.assertIn("each provision", " ".join(by_action["house:119:1:349"]["qualifications_on_both_levels"]))
        self.assertIn("5 percent", by_action["house:119:2:198"]["detail"][1])
        self.assertIsNone(f["synthesis"])

    def test_compact_is_shared_explicit_and_not_sentence_extraction(self):
        author = copy.deepcopy(self.author)
        action = author["actions"][3]
        action["meaning"] = "H.R. is an abbreviation. A later sentence describes another package mechanism."
        products = prepare(author, self.capture, ["F000477", "M001184"])
        readable = readable_candidates(author, products[0], products[2], products[-1])
        for member in readable["members"]:
            finding = next(f for f in member["findings"] if f["action_ids"] == [action["action_id"]])
            self.assertIn(action["compact_description"], finding["compact"])
            self.assertNotIn("abbreviation", finding["compact"])
            self.assertIn(action["meaning"], finding["detail"])
            self.assertIn("cost-sharing", finding["compact"])
            self.assertIn("abortion", finding["compact"])
            self.assertTrue(finding["action_observations"][0]["claim_source_map"])

    def test_discovery_accounting_is_complete_but_membership_not_claimed_closed(self):
        universe = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        validate_universe_proposal(universe, self.author, self.capture, json.loads((DATA / "membership_review.json").read_text(encoding="utf-8")))
        rows = universe["candidate_dispositions"]
        expected = {f"house:119:{s}:{r}" for s, last in [(1, 362), (2, 314)] for r in range(1, last + 1)}
        self.assertEqual({r["action_id"] for r in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertEqual(sum(universe["accounting"]["counts"].values()), len(rows))
        self.assertEqual(universe["proposal_sha256"], sealed_digest(universe, "proposal_sha256"))
        self.assertFalse(universe["full_record_claim"])
        self.assertIsNone(universe["approval_receipt"])
        self.assertEqual(sum(r["after_historical_july23_boundary"] for r in rows), 31)
        self.assertTrue(all(r.get("historical_raw_hash_matches", True) for r in rows))
        self.assertEqual(universe["cutoff"]["end_date"], "2026-09-16")
        self.assertEqual(universe["interpretation_action_set_cutoff"], "2026-09-16")

    def test_wrong_stage_cannot_borrow_parent_passage_meaning(self):
        author = copy.deepcopy(self.author)
        author["actions"][0]["stage"] = "final_passage"
        with self.assertRaisesRegex(ValueError, "stage differs"):
            prepare(author, self.capture, ["F000477"])

    def test_compact_requires_a_bound_operative_passage(self):
        author = copy.deepcopy(self.author)
        author["actions"][0]["compact_source_refs"] = ["clerk:119:1:150"]
        with self.assertRaisesRegex(ValueError, "compact meaning"):
            prepare(author, self.capture, ["F000477"])

    def test_member_service_and_evidence_controls_remain_non_counting_in_pair(self):
        for field, value in [("service_status", "not_yet_serving"), ("service_status", "unresolved"),
                             ("evidence_status", "missing")]:
            inputs = copy.deepcopy(self.products[3]); inputs["members"] = inputs["members"][:1]
            row = inputs["members"][0]["actions"][0]
            row[field] = value
            member = run_editorial_pipeline(inputs).compiled_ir["members"][0]
            pair = next(p for p in member["proposition_graph"]["propositions"]
                        if any(o["action_id"] == row["action_id"] for o in p.get("action_observations", [])))
            self.assertIsNone(pair["action_observations"][0]["direction"])
            self.assertEqual(pair["evidence_action_ids"], ["house:119:1:151"])

    def test_membership_queue_distinguishes_work_from_exact_binding_and_unavailable_sources(self):
        u = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        rows = {r["action_id"]: r for r in u["candidate_dispositions"]}
        self.assertEqual(u["accounting"]["counts"], {"procedural_context":185, "source_unresolved":258,
            "interpreted_substantive_directional":66, "expressive_nonbinding_context":11, "exact_action_ineligible":156})
        for aid in ["house:119:2:53", "house:119:2:308", "house:119:2:313"]:
            self.assertFalse(rows[aid]["review_progress"]["exact_action_binding_unresolved"])
            self.assertTrue(rows[aid]["review_progress"]["substantive_review_performed"])
        self.assertTrue(rows["house:119:1:72"]["review_progress"]["substantive_review_performed"])
        self.assertEqual(rows["house:119:1:72"]["disposition"], "exact_action_ineligible")
        self.assertTrue(rows["house:119:1:180"]["review_progress"]["substantive_review_performed"])
        self.assertEqual(rows["house:119:1:180"]["disposition"], "interpreted_substantive_directional")
        self.assertTrue(rows["house:119:1:199"]["review_progress"]["substantive_review_performed"])
        self.assertTrue(rows["house:119:1:204"]["review_progress"]["substantive_review_performed"])
        self.assertTrue(rows["house:119:1:209"]["review_progress"]["substantive_review_performed"])
        self.assertEqual(rows["house:119:1:209"]["disposition"], "interpreted_substantive_directional")
        self.assertTrue(rows["house:119:1:218"]["review_progress"]["substantive_review_performed"])
        self.assertFalse(rows["house:119:1:224"]["review_progress"]["substantive_review_performed"])
        self.assertFalse(any(r["review_progress"]["required_evidence_unavailable"] for r in rows.values()))
        self.assertEqual([aid for aid, r in rows.items() if r["review_progress"]["authoritative_source_conflict"]],
                         ["house:119:1:237"])
        unresolved = [r for r in rows.values() if r["disposition"] == "source_unresolved"]
        self.assertEqual(sum(not r["review_progress"]["substantive_review_performed"] for r in unresolved), 257)
        self.assertEqual(rows["house:119:2:310"]["disposition"], "interpreted_substantive_directional")
        self.assertEqual(rows["house:119:2:309"]["disposition"], "exact_action_ineligible")

    def test_stale_universe_cannot_replay_new_interpretations(self):
        u = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        author = copy.deepcopy(self.author); author["actions"].pop()
        with self.assertRaisesRegex(ValueError, "interpretation set differs"):
            validate_universe_proposal(u, author)
        author = copy.deepcopy(self.author); author["interpretation_action_set_cutoff"] = "2026-07-23"
        with self.assertRaisesRegex(ValueError, "cutoff differs"):
            validate_universe_proposal(u, author)
        m = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        m["records"][0]["sources"][0]["raw_sha256"] = "0" * 64
        m["review_sha256"] = sealed_digest(m, "review_sha256")
        u["membership_review_sha256"] = m["review_sha256"]
        u["candidate_dispositions"][149]["review_progress"]["shared_review_record_sha256"] = digest(m["records"][0])
        u["universe_subject_sha256"] = digest({"subject":u["subject"], "cutoff":u["cutoff"], "candidate_records":u["candidate_dispositions"]})
        u["proposal_sha256"] = sealed_digest(u, "proposal_sha256")
        with self.assertRaisesRegex(ValueError, "membership source identity differs"):
            validate_universe_proposal(u, self.author, self.capture, m)

    def test_new_versions_are_separate_observations_with_shared_limits(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        f = readable["members"][0]
        pair = next(x for x in f["findings"] if "house:119:1:145" in x["action_ids"])
        self.assertEqual(pair["action_ids"], ["house:119:1:145", "house:119:1:190"])
        self.assertIn("$10 billion", pair["action_observations"][1]["compact"])
        self.assertNotIn("$10 billion", pair["action_observations"][0]["compact"])
        fraud = next(x for x in f["findings"] if x["action_ids"] == ["house:119:2:310"])
        self.assertIn("HIPAA", " ".join(fraud["detail"]))
        self.assertIn("congressional-record:2026-09-15", fraud["source_ids"])
        self.assertIn("deletion", fraud["compact"])

    def test_resumed_priority_bindings_preserve_changed_and_retained_provisions(self):
        actions = {a["action_id"]: a for a in self.author["actions"]}
        concurrence = actions["house:119:2:53"]
        self.assertEqual(concurrence["episode_id"], actions["house:119:2:45"]["episode_id"])
        self.assertTrue({"govinfo:hr7148eas", "govinfo:pl119-37", "govinfo:hr7148eh-page-binding"}
                        <= {c["source_id"] for c in concurrence["claim_source_map"]})
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        self.assertEqual([p["pdf_page"] for p in sources["govinfo:hr7148eh-page-binding"]["page_extracts"]],
                         [4, 1132, 1152, 1153, 1181, 1235])
        sanctions = actions["house:119:2:308"]
        self.assertTrue({"govinfo:hr5334eas", "govinfo:hr5334eh", "congressional-record:2026-09-15"}
                        <= set(sanctions["compact_source_refs"]))
        # Incorporated-law claims cannot survive removal of that source binding.
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == concurrence["action_id"])["additional_source_ids"].remove("govinfo:pl119-37")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        water = next(r for r in membership["records"] if r["action_id"] == "house:119:2:313")
        self.assertEqual(water["disposition"], "exact_action_ineligible")
        self.assertIn("Clerk roll313 matches", water["binding_method"])
        self.assertTrue(water["claim_source_map"])
        self.assertNotIn(water["action_id"], actions)

    def test_real_fentanyl_pair_preserves_failed_condition_and_whole_passage(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        for member in readable["members"]:
            pair = next(f for f in member["findings"] if "house:119:1:32" in f["action_ids"])
            self.assertEqual(pair["action_ids"], ["house:119:1:32", "house:119:1:33"])
            expected = ["Yea", "Nay"] if member["member_id"] == "F000477" else ["Nay", "Nay"]
            self.assertEqual([o["status"] for o in pair["action_observations"]], expected)
            self.assertIn("It failed and was not part", pair["compact"])
            self.assertIn("govinfo:hrpt2", pair["source_ids"])
            self.assertIn("congressional-record:2025-02-06", pair["source_ids"])
            self.assertIsNone(member["synthesis"])
        for member in result.compiled_ir["members"]:
            proposition = next(p for p in member["proposition_graph"]["propositions"]
                               if any(o["action_id"] == "house:119:1:32" for o in p.get("action_observations", [])))
            self.assertEqual(proposition["proposition_type"], "notable_choice")

    def test_new_funding_and_pension_details_retain_incorporated_offsets(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        for member in readable["members"]:
            by_action = {a: f for f in member["findings"] for a in f["action_ids"]}
            pension = by_action["house:119:1:51"]
            self.assertIn("govinfo:38usc5503-2024", pension["source_ids"])
            self.assertIn("$90", " ".join(pension["detail"]))
            self.assertIn("Medicaid", pension["compact"])
            unemployment = by_action["house:119:1:68"]
            self.assertIn("govinfo:pl117-2", unemployment["source_ids"])
            self.assertIn("rescinded", unemployment["compact"])
            funding = by_action["house:119:1:70"]
            self.assertIn("govinfo:2usc901a-2024", funding["source_ids"])
            self.assertIn("sequestration", funding["compact"])
            self.assertIn("ten months at 2 percent", " ".join(funding["detail"]))


    def test_senate_origin_preserves_exact_house_action_and_rejects_measure_drift(self):
        core, _, projections, _, result = self.products
        action = next(a for a in core["actions"] if a["action_id"] == "house:119:1:104")
        self.assertEqual(action["chamber"], "house")
        self.assertEqual(action["exact_question"], "On Motion to Suspend the Rules and Pass")
        self.assertIn("govinfo:s146es", action["semantic_ir_source_ids"])
        for bill_type in [None, "hr", "sjres", "S"]:
            with self.subTest(bill_type=bill_type):
                author = copy.deepcopy(self.author)
                proposed = next(a for a in author["actions"] if a["action_id"] == action["action_id"])
                if bill_type is None:
                    proposed.pop("bill_type")
                else:
                    proposed["bill_type"] = bill_type
                with self.assertRaisesRegex(ValueError, "Clerk measure"):
                    prepare(author, self.capture, ["F000477"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == action["action_id"])["bill_number"] = 147
        with self.assertRaisesRegex(ValueError, "Clerk measure"):
            prepare(author, self.capture, ["F000477"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if action["action_id"] in f["action_ids"])
            self.assertIn("restitution", finding["compact"])
            self.assertIn("govinfo:18usc2264-2024", finding["source_ids"])
            self.assertIn("not proof of collection", " ".join(finding["qualifications_on_both_levels"]))

    def test_scott_clinical_trial_exception_is_not_inherited_by_other_questions(self):
        actions = {a["action_id"]: a for a in self.author["actions"]}
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        records = {r["action_id"]: r for r in membership["records"]}
        amendment = actions["house:119:1:79"]
        self.assertIn("solely", amendment["meaning"])
        self.assertEqual(amendment["stage"], "amendment")
        self.assertTrue({"govinfo:hrpt38", "house-rules:rcp119-1", "congressional-record:2025-03-27"}
                        <= set(amendment["compact_source_refs"]))
        for roll in [80, 81, 82, 83]:
            aid = f"house:119:1:{roll}"
            self.assertNotIn(aid, actions)
            self.assertEqual(records[aid]["disposition"], "exact_action_ineligible")
            self.assertTrue(records[aid]["claim_source_map"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == amendment["action_id"])["additional_source_ids"].remove("house-rules:rcp119-1")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        # A medical word in a preserved consumer-product exclusion is not a new medical mechanism.
        sodium = records["house:119:1:108"]
        self.assertEqual(sodium["disposition"], "exact_action_ineligible")
        self.assertIn("govinfo:15usc2052-2024", {s["source_id"] for s in sodium["sources"]})
        self.assertNotIn(sodium["action_id"], actions)

    def test_separate_veterans_proposals_keep_each_deadline_and_existing_pension_limit(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            by_action = {aid: f for f in member["findings"] for aid in f["action_ids"]}
            for roll in [89, 90, 115, 133]:
                aid = f"house:119:1:{roll}"
                finding = by_action[aid]
                self.assertEqual(finding["action_ids"], [aid])
                self.assertIn("December 31, 2031", finding["compact"])
                self.assertIn("govinfo:38usc5503-2024", finding["source_ids"])
                self.assertIn("$90", " ".join(finding["detail"]))
            self.assertIn("one year after commencement", " ".join(by_action["house:119:1:90"]["detail"]))
            self.assertIn("two years after commencement", " ".join(by_action["house:119:1:133"]["detail"]))

    def test_senate_fentanyl_bill_does_not_absorb_the_failed_house_amendment(self):
        core, _, projections, _, result = self.products
        actions = {a["action_id"]: a for a in self.author["actions"]}
        self.assertNotEqual(actions["house:119:1:166"]["episode_id"], actions["house:119:1:33"]["episode_id"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:166" in f["action_ids"])
            self.assertEqual(finding["action_ids"], ["house:119:1:166"])
            self.assertIn("did not include the failed H.R.27 amendment", finding["compact"])
            self.assertIn("govinfo:s331es", finding["source_ids"])
            pair = next(f for f in member["findings"] if "house:119:1:32" in f["action_ids"])
            self.assertEqual(pair["action_ids"], ["house:119:1:32", "house:119:1:33"])

    def test_milcon_va_pair_retains_separate_effects_and_source_dependencies(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:180" in f["action_ids"])
            self.assertEqual(finding["action_ids"], ["house:119:1:180", "house:119:1:182"])
            observations = finding["action_observations"]
            self.assertEqual([next(a["legislative_stage"] for a in core["actions"] if a["action_id"] == o["action_id"]) for o in observations], ["amendment", "final_passage"])
            self.assertIn("netted to zero", finding["compact"])
            self.assertIn("rescinding some prior VA balances", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("not an additional $4.1 million", detail)
            self.assertIn("already set aside in December2024", detail)
            self.assertIn("except rape, incest", detail)
            self.assertIn("not a new expansion", detail)
            self.assertIn("July1,2026", detail)
            self.assertIn("July1,2027", detail)
            self.assertTrue({"house-rules:rcp119-5", "govinfo:pl115-141", "govinfo:transport-court2024"} <= set(finding["source_ids"]))
        # Losing the page/line binding must not leave an apparently replayable amendment.
        author = copy.deepcopy(self.author)
        amendment = next(a for a in author["actions"] if a["action_id"] == "house:119:1:180")
        amendment["additional_source_ids"].remove("house-rules:rcp119-5")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_stablecoin_incorporation_and_nonvote_do_not_become_generic_health_opposition(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        members = {m["member_id"]: m for m in readable["members"]}
        finding = next(f for f in members["F000477"]["findings"] if "house:119:1:200" in f["action_ids"])
        self.assertIn("reserve-shortfall", finding["compact"])
        self.assertIn("does not itself reduce", finding["compact"])
        self.assertIn("full stablecoin package", " ".join(finding["qualifications_on_both_levels"]))
        self.assertIn("govinfo:11usc507-2024", finding["source_ids"])
        self.assertFalse(any("house:119:1:200" in f["action_ids"] for f in members["M001184"]["findings"]))
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:200")
        action["additional_source_ids"].remove("govinfo:11usc507-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule = records["house:119:1:203"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertIn("govinfo:hr4eas", {s["source_id"] for s in rule["sources"]})
        self.assertIn("omits the earlier separate $400-million", rule["rationale"])
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in core["actions"]})

    def test_digital_commodity_customer_pool_is_distinct_from_stablecoin_estate_priority(self):
        core, _, projections, _, result = self.products
        members = {m["member_id"]: m for m in readable_candidates(self.author, core, projections, result)["members"]}
        finding = next(f for f in members["F000477"]["findings"] if "house:119:1:199" in f["action_ids"])
        self.assertIn("customer-property pool", finding["compact"])
        self.assertTrue({"govinfo:11usc766-2024", "govinfo:11usc726-2024", "govinfo:11usc507-2024"}.issubset(finding["source_ids"]))
        self.assertIn("excess property and unpaid customer claims follow ordinary estate distribution", " ".join(finding["qualifications_on_both_levels"]))
        self.assertNotIn("house:119:1:200", finding["action_ids"])
        self.assertFalse(any("house:119:1:199" in f["action_ids"] for f in members["M001184"]["findings"]))
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:199")
        action["additional_source_ids"].remove("govinfo:11usc766-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_hiv_amendment_reduces_nested_minimum_without_inheriting_whole_package(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:206" in f["action_ids"])
            self.assertIn("not the total Defense Health appropriation", finding["compact"])
            self.assertIn("did not expressly prohibit", finding["compact"])
            self.assertIn("earlier adopted amendment", finding["compact"])
            self.assertNotIn("to zero", finding["compact"])
            self.assertIn("govinfo:hr4016rh-page-binding", finding["source_ids"])
            self.assertIn("congressional-record:2025-07-16", finding["source_ids"])
            self.assertEqual(finding["action_ids"], [f"house:119:1:{n}" for n in [204, 206, 209, 212]])
            self.assertIn("$117.988 million", finding["compact"])
            self.assertIn("govinfo:10usc401-2024", finding["source_ids"])
            self.assertIn("not the underlying authorities", finding["compact"])
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:206")
        action["additional_source_ids"].remove("govinfo:hr4016rh-page-binding")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [205, 207, 208]:
            self.assertEqual(records[f"house:119:1:{roll}"]["disposition"], "exact_action_ineligible")
            self.assertNotIn(f"house:119:1:{roll}", {a["action_id"] for a in core["actions"]})

    def test_defense_episode_preserves_country_scope_and_mixed_member_choices(self):
        core, _, projections, _, result = self.products
        readings = readable_candidates(self.author, core, projections, result)
        for member in readings["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:212" in f["action_ids"])
            observations = {o["action_id"]: o for o in finding["action_observations"]}
            self.assertEqual(list(observations), [f"house:119:1:{r}" for r in [204, 206, 209, 212]])
            expected = ["Nay"] * 4 if member["member_id"] == "F000477" else ["Yea", "Yea", "Yea", "Nay"]
            self.assertEqual([o["status"] for o in observations.values()], expected)
            ukraine = observations["house:119:1:209"]["compact"]
            self.assertIn("otherwise qualifying humanitarian medical assistance", ukraine)
            self.assertIn("not cut the whole aid account", ukraine)
            passage = observations["house:119:1:212"]["compact"]
            self.assertIn("funded military health care", passage)
            self.assertIn("restricting spending", passage)
            self.assertIn("protected civilian access", passage)
            self.assertIn("one vote on the full defense package", passage)
            detail = " ".join(observations["house:119:1:212"]["detail"])
            self.assertIn("$701 million", detail)
            self.assertIn("$14 million", detail)
            self.assertIn("not a guaranteed executed total", detail)
            self.assertIn("does not portray all2012 eligibility terms as unchanged", detail)
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertEqual(records["house:119:1:210"]["disposition"], "exact_action_ineligible")
        self.assertIn("not reach all Lebanese civilian", records["house:119:1:210"]["rationale"])
        self.assertNotIn("house:119:1:210", {a["action_id"] for a in core["actions"]})
        for aid, sid in [("house:119:1:209", "govinfo:10usc401-2024"),
                         ("house:119:1:212", "dod:reproductive-care-2022-10-20")]:
            author = copy.deepcopy(self.author)
            action = next(a for a in author["actions"] if a["action_id"] == aid)
            action["additional_source_ids"].remove(sid)
            with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
                prepare(author, self.capture, ["F000477"])

    def test_opioid_sanctions_preserve_incorporated_waiver_and_separate_sunset(self):
        core, _, projections, _, result = self.products
        readings = readable_candidates(self.author, core, projections, result)
        for member in readings["members"]:
            finding = next(f for f in member["findings"] if f["action_ids"] == ["house:119:1:220"])
            self.assertEqual(finding["action_observations"][0]["status"], "Yea")
            self.assertIn("conditional waiver", finding["compact"])
            self.assertIn("not a new treatment benefit", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("neither creates that waiver nor guarantees", detail)
            self.assertIn("does not amend the separate2334 seven-year termination", detail)
            self.assertIn("suspend the rules and pass as amended", detail)
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:220")
        action["additional_source_ids"].remove("govinfo:21usc-ch28-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [213, 214, 215, 216, 217, 219]:
            self.assertEqual(records[f"house:119:1:{roll}"]["disposition"], "exact_action_ineligible")
            self.assertTrue(records[f"house:119:1:{roll}"]["claim_source_map"])

    def test_coast_guard_package_preserves_conditional_care_and_source_text_defect(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if f["action_ids"] == ["house:119:1:218"])
            expected = "Yea" if member["member_id"] == "F000477" else "Nay"
            self.assertEqual(finding["action_observations"][0]["status"], expected)
            self.assertIn("authorizations were not appropriations", finding["compact"])
            self.assertIn("cross-reference error", finding["compact"])
            detail = " ".join(finding["detail"])
            for boundary in ["pilot terminates September30,2029", "already preserves medical/dental",
                             "October1,2025", "does not silently replace2519 with2520",
                             "victim’s permission", "court-martial exclusion remains",
                             "75percent federal-share ceiling"]:
                self.assertIn(boundary, detail)
        author = copy.deepcopy(self.author)
        action = next(a for a in author["actions"] if a["action_id"] == "house:119:1:218")
        action["additional_source_ids"].remove("govinfo:14usc-ch25-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_september_rule_accounts_for_deemed_and_tabled_resolutions_without_health_finding(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule = records["house:119:1:222"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertTrue({"govinfo:hres672eh", "govinfo:hres668eh", "govinfo:hres605eh",
                         "govinfo:hres598rh", "govinfo:hres589ih"} <= {s["source_id"] for s in rule["sources"]})
        self.assertIn("Tabling that proposal is distinct", rule["rationale"])
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in self.products[0]["actions"]})

    def test_regional_account_amendments_keep_exact_amounts_and_health_eligibility_limits(self):
        core, _, projections, _, result = self.products
        ids = [f"house:119:1:{r}" for r in range(232, 236)]
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if ids[0] in f["action_ids"])
            self.assertEqual(finding["action_ids"][:4], ids)
            self.assertEqual([o["status"] for o in finding["action_observations"][:4]],
                             ["Nay" if member["member_id"] == "F000477" else "Yea"] * 4)
            for name in ["Northern Border", "Southwest Border", "Southeast Crescent", "Great Lakes"]:
                self.assertIn(name, finding["compact"])
            for amount in ["$13,319,727", "$2,063,381", "$16,003,526", "$250,000"]:
                self.assertIn(amount, finding["compact"])
            self.assertIn("No health-only amount or loss of services", finding["compact"])
            self.assertIn("amendment failed", finding["compact"])
            detail = " ".join(finding["detail"])
            for boundary in ["If a commission elects", "cost-sharing conditions remain",
                             "neither is a medical allocation", "not guarantee a grant",
                             "notwithstanding40USC15751(b)"]:
                self.assertIn(boundary, detail)
            self.assertTrue({"govinfo:40usc-subtitleV-2024", "govinfo:pl118-272-regional-commissions"}
                            <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == ids[0])["additional_source_ids"].remove("govinfo:40usc-subtitleV-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_eere_amendment_binds_incorporated_household_assistance_and_nested_amounts(self):
        core, _, projections, _, result = self.products
        aid = "house:119:1:236"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertIn("not a $2.053-billion combined cut", action["meaning"])
        self.assertIn("$180million Weatherization Assistance Program", action["meaning"])
        self.assertIn("annually adjusted average-cost caps", action["meaning"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"][:5], [f"house:119:1:{r}" for r in range(232, 237)])
            observation = next(o for o in finding["action_observations"] if o["action_id"] == aid)
            self.assertEqual(observation["status"], "Nay" if member["member_id"] == "F000477" else "Yea")
            self.assertIn("$223-million administration reduction is already inside", finding["compact"])
            self.assertIn("not repeal the programs or rescind every other funding source", finding["compact"])
            self.assertTrue({"govinfo:hrpt119-213-eere", "govinfo:42usc6863-2024"} <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("govinfo:hrpt119-213-eere")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_energy_amendment_exclusions_do_not_turn_administration_cuts_into_repeal(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll in [229, 230, 231]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("does not itself repeal the loan program", records["house:119:1:230"]["rationale"])
        self.assertIn("separate $150-million", records["house:119:1:231"]["rationale"])
        self.assertIn("leaving the amount unchanged", records["house:119:1:231"]["rationale"])
        self.assertIn("earlier repeal/rescission", records["house:119:1:230"]["rationale"])

    def test_drbc_exclusions_preserve_public_health_context_and_separate_funding_scopes(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        rule, agency = [records[f"house:119:1:{r}"] for r in [227, 228]]
        for row in [rule, agency]:
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertIn("Public-health", row["rationale"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("300,000 or more gallons", rule["rationale"])
        self.assertIn("adjacent Social Security rule", rule["rationale"])
        self.assertIn("bill-specific implementation/enforcement", rule["rationale"])
        self.assertIn("not abolition of the commission", agency["rationale"])
        self.assertIn("not patient coverage", agency["rationale"])

    def test_july_membership_reuses_consumer_definition_without_promoting_rule_votes(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertEqual(records["house:119:1:192"]["disposition"], "exact_action_ineligible")
        self.assertIn("govinfo:15usc2052-2024", {s["source_id"] for s in records["house:119:1:192"]["sources"]})
        self.assertEqual(records["house:119:1:193"]["disposition"], "exact_action_ineligible")
        for roll, version in [(195, "rh"), (198, "eh")]:
            aid = f"house:119:1:{roll}"
            self.assertEqual(records[aid]["disposition"], "procedural_context")
            self.assertIn("govinfo:hres580" + version, {s["source_id"] for s in records[aid]["sources"]})
            self.assertNotIn(aid, {a["action_id"] for a in self.products[0]["actions"]})

    def test_rescission_accounts_and_rule_amendment_have_separate_source_boundaries(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:168" in f["action_ids"])
            self.assertIn("$500 million and $400 million", finding["compact"])
            self.assertIn("unobligated", finding["compact"])
            self.assertTrue({"govinfo:hr4eh", "govinfo:pl119-4", "govinfo:pl118-47"} <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:1:168")["additional_source_ids"].remove("govinfo:pl118-47")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        membership = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))
        records = {r["action_id"]: r for r in membership["records"]}
        rule = records["house:119:1:188"]
        self.assertEqual(rule["disposition"], "procedural_context")
        self.assertIn("congressional-record:2025-07-02", {s["source_id"] for s in rule["sources"]})
        self.assertNotIn(rule["action_id"], {a["action_id"] for a in core["actions"]})
        self.assertIn("penalties", records["house:119:1:162"]["rationale"])
        self.assertIn("dc-council:law24-345", {s["source_id"] for s in records["house:119:1:162"]["sources"]})


    def test_energy_passage_keeps_health_riders_and_separate_unresolved_amendment(self):
        core, _, projections, _, result = self.products
        aid = "house:119:1:239"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        for boundary in ["not substituted for the House bill", "excludes molybdenum-99",
                         "does not name the separate", "previous appropriations",
                         "this Act or any other Act", "not a separate vote"]:
            self.assertIn(boundary, action["meaning"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [f"house:119:1:{r}" for r in [232,233,234,235,236,239]])
            self.assertEqual([o["status"] for o in finding["action_observations"]],
                             (["Nay"] * 6 if member["member_id"] == "F000477" else ["Yea"] * 5 + ["Nay"]))
            self.assertIn("COVID-19 mask or vaccine mandates", finding["compact"])
            self.assertIn("vote does not identify a position on each", finding["compact"])
            self.assertTrue({"govinfo:hr4553eh", "energy:fy2026-oda-health-programs",
                             "govinfo:hrpt119-213-passage-health", "govinfo:42usc18649-2024"}
                            <= set(finding["source_ids"]))
        records = json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]
        pending = next(r for r in records if r["action_id"] == "house:119:1:237")
        self.assertEqual(pending["disposition"], "source_unresolved")
        self.assertTrue(pending["substantive_review_performed"])
        self.assertTrue(pending["authoritative_source_conflict"])
        self.assertFalse(pending["required_evidence_unavailable"])
        self.assertNotIn(pending["action_id"], {a["action_id"] for a in core["actions"]})
        for amount in ["$1,114,784,219.49", "$1,114,734,219.49"]:
            self.assertIn(amount, pending["rationale"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("energy:fy2026-oda-health-programs")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_ndaa_care_amendments_preserve_distinct_scope_and_choice_sources(self):
        core, _, projections, _, result = self.products
        ids = ["house:119:1:245", "house:119:1:246"]
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if ids[0] in f["action_ids"])
            self.assertEqual(finding["action_ids"][:2], ids)
            self.assertEqual([o["status"] for o in finding["action_observations"][:2]],
                             ["Nay", "Nay"] if member["member_id"] == "F000477" else ["Yea", "Yea"])
            for boundary in ["referrals and duty-station changes", "sterilization condition",
                             "Two exception clauses refer to minors", "not all care or TRICARE coverage"]:
                self.assertIn(boundary, finding["compact"])
            detail = " ".join(finding["detail"])
            for boundary in ["purpose-bound", "without an express minor-only limit",
                             "should not be read into the separately edited", "not a claim that EFMP itself is a health insurer"]:
                self.assertIn(boundary, detail)
            self.assertTrue({"govinfo:hrpt119-255-amend13", "govinfo:hrpt119-255-amend14",
                             "govinfo:10usc1781c-2024-operative", "govinfo:10usc1079-2024-operative"}
                            <= set(finding["source_ids"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == ids[1])["additional_source_ids"].remove("govinfo:10usc1079-2024-operative")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_ndaa_aid_choices_keep_country_and_account_scopes_and_full_episode(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if "house:119:1:255" in f["action_ids"])
            self.assertEqual(finding["action_ids"], [f"house:119:1:{r}" for r in [245, 246, 255, 256]])
            self.assertEqual([o["status"] for o in finding["action_observations"]],
                             ["Nay"] * 4 if member["member_id"] == "F000477" else ["Yea"] * 4)
            for boundary in ["funds made available by this bill", "not a medical-only vote",
                             "$115.317-million authorization", "not a rescission or repeal"]:
                self.assertIn(boundary, finding["compact"])
            self.assertTrue({"govinfo:pl115-91-usai-1234", "govinfo:pl116-92-usai-1244",
                             "govinfo:budget2026-ohdaca-authorities"} <= set(finding["source_ids"]))
            self.assertNotIn("house:119:1:257", finding["action_ids"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertEqual(records["house:119:1:257"]["disposition"], "exact_action_ineligible")
        self.assertIn("Taiwan, not Ukraine", records["house:119:1:257"]["rationale"])
        for aid, sid in [("house:119:1:255", "govinfo:pl115-91-usai-1234"),
                         ("house:119:1:256", "govinfo:budget2026-ohdaca-authorities")]:
            author = copy.deepcopy(self.author)
            next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(sid)
            with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
                prepare(author, self.capture, ["F000477"])


    def test_july_passage_does_not_inherit_september_engrossment_addition(self):
        action = next(a for a in self.author["actions"] if a["action_id"] == "house:119:1:199")
        self.assertEqual(action["source_id"], "govinfo:rcp119-6-july-version")
        self.assertIn("not attributed to the July17 roll199", action["meaning"])
        self.assertNotIn("Federal Reserve digital-currency package", action["compact_description"])
        self.assertFalse(any(m["locator"].startswith("TITLE VI--") for m in action["claim_source_map"]))
        self.assertTrue({"govinfo:hrpt119-199-partsBC", "govinfo:hres707-engrossment-instruction",
                         "congressional-record:2025-07-17-3633-version"} <= set(action["additional_source_ids"]))
        core, _, projections, _, result = self.products
        members = {m["member_id"]: m for m in readable_candidates(self.author, core, projections, result)["members"]}
        finding = next(f for f in members["F000477"]["findings"] if action["action_id"] in f["action_ids"])
        self.assertIn("customer-property pool", finding["compact"])
        self.assertNotIn("Federal Reserve digital-currency package", finding["compact"])
        self.assertFalse(any(action["action_id"] in f["action_ids"] for f in members["M001184"]["findings"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == action["action_id"])["additional_source_ids"].remove("govinfo:hres707-engrossment-instruction")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_veterans_packages_keep_distinct_pension_dates_and_qualified_benefits(self):
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            for roll, date in [(266, "December 31, 2032"), (269, "February 29, 2032")]:
                aid = f"house:119:1:{roll}"
                finding = next(f for f in member["findings"] if aid in f["action_ids"])
                self.assertEqual(finding["action_ids"], [aid])
                self.assertEqual(finding["action_observations"][0]["status"], "Yea")
                self.assertIn(date, finding["compact"])
                self.assertIn("$90 monthly VA pension limit for specified Medicaid-covered", finding["compact"])
                detail = " ".join(finding["detail"])
                self.assertIn("State homes", detail)
                self.assertIn("willful-concealment", detail)
                self.assertIn("govinfo:38usc5503-2024", finding["source_ids"])
            physicians = next(f for f in member["findings"] if "house:119:1:266" in f["action_ids"])
            self.assertIn("assignments remain discretionary", physicians["compact"])
            burial = next(f for f in member["findings"] if "house:119:1:269" in f["action_ids"])
            self.assertIn("seven years", burial["compact"])
            self.assertIn("not portrayed as the first possible pre 1990 medallion", " ".join(burial["detail"]))
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == "house:119:1:269")["additional_source_ids"].remove("govinfo:38usc5503-2024")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_dc_youth_package_uses_operative_age_and_care_plan_not_title_or_predicted_harm(self):
        aid = "house:119:1:270"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        core, _, projections, _, result = self.products
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_observations"][0]["status"], "Nay")
            for phrase in ["under 18 at the time of the offense", "behavioral and physical health care",
                           "without personally identifiable information", "One vote covered the whole package"]:
                self.assertIn(phrase, finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("no such Home Rule Act prohibition appears", detail)
            self.assertIn("16-2341 while the new website section is numbered 16-2340a", detail)
            self.assertIn("not a newly imposed deadline", detail)
        source = next(s for s in self.capture["sources"] if s["source_id"] == "dc-council:code-24-902-20250916")
        self.assertIn("8ed3f5ccaac32256a14f10b86418a98c93ff8c8a", source["url"])
        self.assertIn("behavioral and physical health care", source["text"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(source["source_id"])
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])


    def test_dc_transfer_candidate_preserves_treatment_binding_and_separate_noncounting_controls(self):
        aid = "house:119:1:271"
        action = next(a for a in self.author["actions"] if a["action_id"] == aid)
        self.assertEqual(action["episode_id"], "episode:hr5140:119")
        self.assertIn("before 18 delinquent-act language is not rewritten", action["meaning"])
        self.assertIn("existing under 18 firearm-location transfer provision", action["meaning"])
        self.assertIn("16-2320(c)(1)", action["meaning"])
        self.assertIn("offenses committed on or after enactment", action["meaning"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove("dc-council:code-16-2320-20250916")
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll, disposition in [(268, "procedural_context"), (273, "procedural_context"),
                                  (274, "exact_action_ineligible"), (275, "exact_action_ineligible"),
                                  (282, "expressive_nonbinding_context"), (284, "procedural_context")]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], disposition)
            self.assertEqual(row["substantive_review_performed"], disposition != "procedural_context")
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("Section8’s separate resolution-of-inquiry date is not changed", records["house:119:1:273"]["rationale"])
        self.assertIn("does not itself adopt the Senate amendment", records["house:119:1:284"]["rationale"])


    def test_energy_membership_uses_original_charter_and_exact_incorporated_provisions(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        sources = {s["source_id"]: s for s in self.capture["sources"]}
        for roll in [277, 278, 279]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], "exact_action_ineligible")
            self.assertTrue(row["substantive_review_performed"])
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        charter = sources["doe:ncc-charter-20191120"]
        self.assertIn("November 20, 2019", charter["text"])
        self.assertIn("solely advisory", charter["text"])
        self.assertIn("govinfo:5usc1006-2024-operative", {s["source_id"] for s in records["house:119:1:278"]["sources"]})
        grid_sources = {s["source_id"] for s in records["house:119:1:279"]["sources"]}
        self.assertIn("govinfo:16usc824-e-2024", grid_sources)
        self.assertNotIn("govinfo:16usc824e-2024", grid_sources)
        self.assertIn("public utility", sources["govinfo:16usc824-e-2024"]["text"])
        self.assertIn("Standard generator interconnection", sources["govinfo:18cfr35-28-f-2025"]["text"])
        self.assertIn("shall remain in full effect", sources["govinfo:eo13867-2024"]["text"])


    def test_dc_bail_candidate_keeps_treatment_source_and_whole_package_limits(self):
        aid = "house:119:1:298"
        core, _, projections, _, result = self.products
        source_id = "dc-council:code-23-1321-20251113-operative"
        source = next(s for s in self.capture["sources"] if s["source_id"] == source_id)
        self.assertIn("88a738d1a240ebd405e0d5fcb9e0e66a01804b5a", source["url"])
        self.assertIn("Undergo medical, psychological, or psychiatric treatment", source["text"])
        for member in readable_candidates(self.author, core, projections, result)["members"]:
            finding = next(f for f in member["findings"] if aid in f["action_ids"])
            self.assertEqual(finding["action_ids"], [aid])
            self.assertIn("property or sureties can qualify", finding["compact"])
            self.assertIn("treatment option itself remains", finding["compact"])
            detail = " ".join(finding["detail"])
            self.assertIn("removing its least-restrictive-condition standard", detail)
            self.assertIn("does not delete the treatment option itself", detail)
            self.assertIn("mismatch between section 4(a-1)", detail)
            self.assertIn("individuals charged with an offense", detail)
            self.assertIn(source_id, finding["source_ids"])
        author = copy.deepcopy(self.author)
        next(a for a in author["actions"] if a["action_id"] == aid)["additional_source_ids"].remove(source_id)
        with self.assertRaisesRegex(ValueError, "compact meaning|claim passage absent"):
            prepare(author, self.capture, ["F000477"])

    def test_november_controls_keep_procedure_expression_and_actual_institutional_actions_distinct(self):
        records = {r["action_id"]: r for r in json.loads((DATA / "membership_review.json").read_text(encoding="utf-8"))["records"]}
        for roll, disposition in [(286, "exact_action_ineligible"), (287, "exact_action_ineligible"),
                                  (289, "exact_action_ineligible"), (291, "procedural_context"),
                                  (292, "expressive_nonbinding_context"), (293, "procedural_context"),
                                  (297, "exact_action_ineligible"), (300, "exact_action_ineligible"),
                                  (301, "exact_action_ineligible"), (302, "procedural_context"),
                                  (303, "exact_action_ineligible"), (305, "expressive_nonbinding_context")]:
            row = records[f"house:119:1:{roll}"]
            self.assertEqual(row["disposition"], disposition)
            self.assertTrue(row["claim_source_map"])
            self.assertNotIn(row["action_id"], {a["action_id"] for a in self.products[0]["actions"]})
        self.assertIn("does not itself pass either bill", records["house:119:1:291"]["rationale"])
        self.assertIn("not adoption", records["house:119:1:293"]["rationale"])
        self.assertIn("remove her from the Intelligence Committee", records["house:119:1:297"]["rationale"])
        self.assertIn("not the whole appropriations law", records["house:119:1:301"]["rationale"])
        self.assertIn("not adoption", records["house:119:1:302"]["rationale"])
        self.assertIn("not completion of the report", records["house:119:1:303"]["rationale"])
        self.assertIn("does not amend Medicare", records["house:119:1:305"]["rationale"])
        self.assertIn("does not assert that no underlying award", records["house:119:1:300"]["rationale"])
        self.assertIn("(h)(4)", records["house:119:1:287"]["rationale"])


if __name__ == "__main__":
    unittest.main()
