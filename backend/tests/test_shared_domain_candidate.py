"""Real Health source bindings and focused candidate/update invariants."""
import copy
import json
import unittest
from pathlib import Path

from scripts.prepare_shared_domain_candidate import prepare, readable_candidates, reproducibility_proof, review_text
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

    def test_complete_supplied_accounting_and_paired_episode_gate(self):
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
        open_mapping = copy.deepcopy(mapping); open_mapping["source_render_constraints"] = []
        open_mapping["mapping_sha256"] = sealed_digest(open_mapping, "mapping_sha256")
        inputs = adapt_to_semantic_ir_input(ROOT, core, open_mapping, projections)
        with self.assertRaisesRegex(SemanticCompilerInputError, "new trajectory requires"):
            run_editorial_pipeline(inputs)

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
        self.assertEqual(result["members"][0]["coverage"]["eligible_substantive_actions"], 10)

    def test_readable_output_preserves_package_limits_and_actual_mechanisms(self):
        core, _, projections, _, result = self.products
        readable = readable_candidates(self.author, core, projections, result)
        f = readable["members"][0]
        self.assertEqual(len(f["findings"]), 9)
        by_action = {x["action_ids"][0]: x for x in f["findings"]}
        self.assertIn("abortion", by_action["house:119:1:349"]["detail"][1])
        self.assertIn("each provision", " ".join(by_action["house:119:1:349"]["qualifications_on_both_levels"]))
        self.assertIn("5 percent", by_action["house:119:2:198"]["detail"][1])
        self.assertIsNone(f["synthesis"])

    def test_discovery_accounting_is_complete_but_membership_not_claimed_closed(self):
        universe = json.loads((DATA / "universe_proposal.json").read_text(encoding="utf-8"))
        rows = universe["accounting"]["rows"]
        expected = {f"house:119:{s}:{r}" for s, last in [(1, 362), (2, 314)] for r in range(1, last + 1)}
        self.assertEqual({r["action_id"] for r in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertEqual(sum(universe["accounting"]["counts"].values()), len(rows))
        self.assertEqual(universe["universe_subject_sha256"], sealed_digest(universe, "universe_subject_sha256"))
        self.assertFalse(universe["full_record_claim"])
        self.assertIsNone(universe["approval_receipt"])
        self.assertEqual(sum(r["after_historical_july23_boundary"] for r in rows), 31)
        self.assertTrue(all(r.get("historical_raw_hash_matches", True) for r in rows))
        self.assertEqual(universe["cutoff"]["end_date"], "2026-09-16")
        self.assertEqual(universe["interpretation_action_set_cutoff"], "2026-07-23")

    def test_wrong_stage_cannot_borrow_parent_passage_meaning(self):
        author = copy.deepcopy(self.author)
        author["actions"][0]["stage"] = "final_passage"
        with self.assertRaisesRegex(ValueError, "stage differs"):
            prepare(author, self.capture, ["F000477"])


if __name__ == "__main__":
    unittest.main()
