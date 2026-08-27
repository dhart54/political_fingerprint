"""M14D promotion provenance, isolation, and explicit candidate regression tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_m14d_education_reanalysis as m  # noqa: E402
from backend.app.semantic_ir.compiler import (  # noqa: E402
    SemanticCompilerInputError, compile_behavioral_candidate_ir,
)
from backend.app.semantic_ir.shared_corpus import SharedCorpusValidationError  # noqa: E402


class M14DEducationReanalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = m.build_outputs()
        cls.core = json.loads(cls.outputs[f"{m.V2}/shared_action_core.json"])
        cls.member = json.loads(cls.outputs[f"{m.V2}/member_projections/f000477.json"])
        cls.manifest = json.loads(cls.outputs[f"{m.V2}/promotion_manifest.json"])
        cls.payload = json.loads(cls.outputs[f"{m.OUT}/compiler_input.json"])
        cls.graph = json.loads(cls.outputs[f"{m.OUT}/behavioral_candidate_graph.json"])
        cls.review = json.loads(cls.outputs[f"{m.OUT}/review_package.json"])
        cls.old = m.load(f"{m.V1}/shared_action_core.json")
        cls.accepted = m.load(f"{m.ACCEPTED}/action_interpretability_candidates.json")["candidates"]
        cls.authorities = [m.load(f"{m.ACCEPTED}/{name}") for name in (
            "human_acceptance_authority.json", "human_acceptance_authority_enriched3.json")]
        cls.overlay = m.load(f"{m.ACCEPTED}/source_overlay.json")

    def test_reproduction_and_frozen_scope(self):
        for path, content in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"), content)
        self.assertFalse(m.git("diff", m.BASE, "--", m.V1, m.ACCEPTED, m.EPISODES))
        # Git blob identities prove all V1 files, not just the core, unchanged.
        tree = m.git("ls-tree", "-r", m.BASE, m.V1).splitlines()
        self.assertGreater(len(tree), 1)
        for line in tree:
            meta, name = line.split("\t", 1)
            with self.subTest(frozen=name):
                self.assertEqual(m.git("hash-object", "--path=" + name, name), meta.split()[2])

    def test_exact_membership_and_36_record_identical_inherited_actions(self):
        old = {a["action_id"]: a for a in self.old["actions"]}
        new = {a["action_id"]: a for a in self.core["actions"]}
        self.assertEqual(len(self.core["actions"]), 53)
        self.assertEqual(len(new), 53)
        self.assertEqual(set(new) - set(old), set(self.manifest["new_action_ids"]))
        self.assertEqual(len(set(new) - set(old)), 16)
        self.assertEqual([aid for aid in old if old[aid] != new[aid]], [m.OVERLAP])
        self.assertEqual(sum(m.canonical_bytes(old[aid]) == m.canonical_bytes(new[aid]) for aid in old), 36)
        self.assertEqual(self.core["schema_version"], "shared_action_core_v1")
        self.assertEqual(self.core["artifact_id"], "shared-action-core:house:119:v2")

    def test_17_exact_semantic_projections_and_additive_acceptance(self):
        decisions = m.acceptance_index(self.accepted, self.authorities)
        new = {a["action_id"]: a for a in self.core["actions"]}
        promoted = {p["action_id"]: p for p in self.manifest["semantic_promotions"]}
        self.assertEqual(len(promoted), 17)
        for c in self.accepted:
            a, p = new[c["action_id"]], promoted[c["action_id"]]
            self.assertEqual(a["accepted_exact_action_meaning"], c["plain_language_meaning"])
            self.assertEqual(a["mechanism"], c["mechanism"]["description"])
            self.assertEqual(a["accepted_shared_limitations"], c["limitations"])
            self.assertEqual(a["action_meaning_ref"], c["candidate_id"])
            for key in ("exact_action_identity", "legislative_stage", "action_date"):
                self.assertEqual(a[key], c[key])
            self.assertEqual(a["chamber_outcome"], c["exact_action_boundary"]["house_action_outcome"])
            self.assertEqual(a["enactment_status"], "not_inferred_from_house_outcome")
            self.assertFalse(a["package_component_boundary"]["parent_package_meaning_projected"])
            self.assertEqual(p["candidate_record_sha256"], m.digest(c))
            self.assertEqual(p["v2_action_core_sha256"], a["action_core_sha256"])
            self.assertEqual(p["authority_artifact_id"], decisions[c["action_id"]]["authority_artifact_id"])
        self.assertEqual(promoted[m.OVERLAP]["promotion_kind"], "approved_overlap_revision")
        self.assertEqual(len(self.manifest["acceptance_authorities"]), 2)
        self.assertFalse(self.manifest["new_human_decision"])

    def test_acceptance_missing_or_resealed_tampering_rejected(self):
        for mutation in ("missing_authority", "wrong_digest", "changed_candidate", "not_accepted"):
            with self.subTest(mutation=mutation):
                candidates, authorities = copy.deepcopy(self.accepted), copy.deepcopy(self.authorities)
                if mutation == "missing_authority":
                    authorities.pop()
                elif mutation == "wrong_digest":
                    authorities[0]["subject"]["accepted_records"][0]["candidate_record_sha256"] = "0" * 64
                    authorities[0]["authority_subject_sha256"] = m.digest(authorities[0]["subject"])
                elif mutation == "not_accepted":
                    authorities[0]["subject"]["accepted_records"][0]["decision"] = "revise"
                    authorities[0]["authority_subject_sha256"] = m.digest(authorities[0]["subject"])
                else:
                    candidates[0]["plain_language_meaning"] = "Altered accepted meaning"
                with self.assertRaises(ValueError):
                    m.acceptance_index(candidates, authorities)

    def test_exact_source_identities_raw_bytes_and_operative_roles(self):
        readiness = {r["action_id"]: r for r in self.overlay["subject"]["action_readiness"]}
        for p in self.manifest["semantic_promotions"]:
            sources = p["governed_sources"]
            self.assertEqual({r["accepted_source_identity"]["source_id"] for r in sources},
                             {s["source_id"] for s in readiness[p["action_id"]]["sources"]})
            for s in sources:
                self.assertEqual(hashlib.sha256((ROOT / s["raw_path"]).read_bytes()).hexdigest(), s["accepted_source_identity"]["raw_sha256"])
            actual = {s["accepted_source_identity"]["source_id"] for s in sources if s["role"] == "operative_meaning"}
            self.assertEqual(actual, set(readiness[p["action_id"]]["source_roles"]["operative_content_interpretation_input"]))
        am = next(p for p in self.manifest["semantic_promotions"] if p["action_id"] == "house:119:1:79")
        operative = [s["core_source_identity"]["source_id"] for s in am["governed_sources"] if s["role"] == "operative_meaning"]
        self.assertEqual(len(operative), 2)  # printed substitute and incorporated gift exception
        self.assertNotIn("congress-text:119:hr:1048:eh", operative)

    def test_member_projection_exact_all_53_official_statuses_and_inheritance(self):
        core = {a["action_id"]: a for a in self.core["actions"]}
        rows = {a["action_id"]: a for a in self.member["actions"]}
        self.assertEqual(len(self.member["actions"]), 53)
        self.assertEqual(set(rows), set(core))
        old = m.load(f"{m.V1}/member_projections/f000477.json")
        for row in old["actions"]:
            expected = copy.deepcopy(row)
            expected["action_core_sha256"] = core[row["action_id"]]["action_core_sha256"]
            self.assertEqual(rows[row["action_id"]], expected)
        promoted = {p["action_id"]: p for p in self.manifest["semantic_promotions"]}
        for aid, row in rows.items():
            if aid in promoted:
                path = next(s["raw_path"] for s in promoted[aid]["governed_sources"] if s["role"] == "action_outcome_and_member_status")
            else:
                a = core[aid]
                path = f"docs/editorial/full_record_reviews/source_readiness/evidence/roll{a['congress']}_{a['session']}_{a['roll']:03d}.xml"
            self.assertEqual(row["official_status"], m.official_status(ROOT / path))
            self.assertEqual(row["exact_choice_effect"], m.choice_effect(row["official_status"]))
        self.assertEqual(rows["house:119:1:312"]["official_status"], "Not Voting")
        self.assertEqual(rows["house:119:1:312"]["exact_choice_effect"], "resolved_non_directional")
        self.assertNotIn(f"{m.V2}/member_projections/g000576.json", self.outputs)

    def test_core_and_member_boundaries_fail_closed(self):
        changed = copy.deepcopy(self.core)
        changed["actions"][0]["member_id"] = "F000477"
        with self.assertRaises(SharedCorpusValidationError):
            m.validate_shared_action_core(ROOT, changed)
        changed = copy.deepcopy(self.member)
        changed["actions"][0]["accepted_exact_action_meaning"] = "Forbidden"
        with self.assertRaises(SharedCorpusValidationError):
            m.validate_member_projection(ROOT, changed, self.core)
        changed = copy.deepcopy(self.member)
        changed["actions"][0]["action_core_sha256"] = "0" * 64
        m.seal(changed, "projection_sha256")
        with self.assertRaises(SharedCorpusValidationError):
            m.validate_member_projection(ROOT, changed, self.core)

    def test_old_episode_prose_cannot_affect_new_candidates(self):
        bundle = m.load(f"{m.EPISODES}/episode_decision_implementation_bundle.json")
        for e in bundle["subject"]["implementation_records"]:
            for key in ("policy_proposition", "grouping_rationale", "material_limitations", "material_policy_differences", "semantic_grouping_evidence"):
                e[key] = "OLD PROSE MUST NEVER ENTER NEW SEMANTICS"
            for action in e["actions"]:
                action["accepted_limitations"] = ["OLD PROSE"]
                action["accepted_exact_action_meaning"] = "OLD PROSE"
        episodes = m.candidate_episodes(self.accepted, self.member, bundle)
        self.assertEqual(episodes, self.payload["episodes"])
        self.assertEqual(m.analytical_input(self.accepted, episodes), self.payload)

    def test_complete_accounting_and_hr1048_one_episode(self):
        m.validate_analytical(self.payload, self.graph)
        episodes = self.payload["episodes"]
        self.assertEqual(len(episodes), 16)
        self.assertEqual(sum(len(e["primary_action_ids"]) for e in episodes), 17)
        multi = [e for e in episodes if len(e["primary_action_ids"]) > 1]
        self.assertEqual(len(multi), 1)
        self.assertEqual(multi[0]["primary_action_ids"], ["house:119:1:79", "house:119:1:83"])
        self.assertEqual(self.review["episode_disposition_counts"], {
            "supports_proposed_repeated_pattern": 4, "supports_proposed_notable_choice": 1,
            "retained_as_useful_contrast": 2, "non_directional_receipt": 1, "receipt_only_no_elevation": 8})
        changed = copy.deepcopy(self.payload)
        changed["episode_accounting"].pop()
        with self.assertRaises(SemanticCompilerInputError):
            compile_behavioral_candidate_ir(changed)

    def test_no_directional_leftover_fallback_or_synthesis(self):
        empty = copy.deepcopy(self.payload)
        empty["proposition_candidates"] = []
        empty["relationship_evidence_by_proposition"] = {}
        for row in empty["episode_accounting"]:
            row["primary_proposition_id"] = None
            if row["disposition"].startswith("supports_proposed_"):
                row["disposition"] = "receipt_only_no_elevation"
                row["reason"] = "No explicit finding selected in this no-fallback test."
        graph = compile_behavioral_candidate_ir(empty)
        self.assertEqual(graph["proposition_graph"]["propositions"], [])
        self.assertEqual(graph["synthesis_propositions"], [])
        self.assertFalse(any(graph["downstream_authorizations"].values()))
        self.assertIsNone(self.review["acceptance_authority"])
        self.assertFalse(self.review["accepted"])
        self.assertFalse(self.review["authorizing"])
        self.assertFalse(self.review["production_selectable"])

    def test_patterns_require_relationship_evidence_and_nondirectional_exclusion(self):
        for mutation in ("no_relationship", "not_voting", "single_episode", "same_episode_trajectory"):
            with self.subTest(mutation=mutation):
                payload = copy.deepcopy(self.payload)
                candidate = payload["proposition_candidates"][0]
                if mutation == "no_relationship":
                    payload["relationship_evidence_by_proposition"] = {}
                elif mutation == "not_voting":
                    eid = "single-119-hr-1005-1-312"
                    candidate["evidence_episode_ids"].append(eid)
                    candidate["episode_semantic_evidence"][eid] = "Understood, Not Voting"
                    payload["relationship_evidence_by_proposition"][candidate["proposition_id"]]["episode_support"][eid] = "Not directional"
                elif mutation == "single_episode":
                    candidate["evidence_episode_ids"] = candidate["evidence_episode_ids"][:1]
                else:
                    payload["proposition_candidates"][-1]["proposition_type"] = "trajectory"
                with self.assertRaises(SemanticCompilerInputError):
                    compile_behavioral_candidate_ir(payload)

    def test_comparison_is_after_generation_and_search_covers_all_actions(self):
        searched = {aid for lane in self.review["search_review"] for aid in lane["actions"]}
        self.assertEqual(searched, {c["action_id"] for c in self.accepted})
        comparison = self.review["historical_comparison_after_generation"]
        self.assertFalse(comparison["input_to_candidate_generation"])
        self.assertEqual([c["status"] for c in comparison["changes"]].count("new"), 1)
        self.assertEqual([c["status"] for c in comparison["changes"]].count("materially_changed_semantic_basis"), 2)
        with patch.object(m, "historical_comparison", side_effect=AssertionError("Not an authoring input")):
            self.assertEqual(m.analytical_input(self.accepted, self.payload["episodes"]), self.payload)

    def test_scope_guard_rejects_historical_public_production_changes(self):
        for forbidden in (f"{m.V1}/shared_action_core.json", "frontend/app/page.tsx",
                          "backend/migrations/unauthorized.sql",
                          "docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/human_action_meaning_authority.json"):
            with self.subTest(forbidden=forbidden):
                with patch.object(m, "git", side_effect=[forbidden, ""]):
                    with self.assertRaisesRegex(ValueError, "scope violation"):
                        m.validate_scope()
        with patch.object(m, "git", side_effect=["scripts/build_m14d_education_reanalysis.py", f"{m.OUT}/review_package.json", ""]):
            m.validate_scope()


if __name__ == "__main__":
    unittest.main()
