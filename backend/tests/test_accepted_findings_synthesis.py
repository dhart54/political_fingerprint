"""M14E accepted-input, lineage, review-boundary, and zero-candidate proofs."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import re
import subprocess
import unittest
from unittest.mock import patch

from backend.app.semantic_ir import accepted_findings_synthesis as s
from scripts import build_m14e_education_synthesis as m


class AcceptedFindingsSynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.findings = m.load(m.BINDING.findings_path)
        cls.authority = m.load(m.BINDING.authority_path)
        cls.proposal = m.proposal(cls.findings)
        cls.standalone = {m.BARGAINING: m.STANDALONE_REASON}
        cls.outputs = m.build_outputs()
        cls.package = json.loads(cls.outputs[f"{m.OUT}/synthesis_candidate_package.json"])
        cls.review = json.loads(cls.outputs[f"{m.OUT}/review_package.json"])
        cls.candidate = cls.package["subject"]["synthesis_candidates"][0]

    def compile(self, proposals=None, standalone=None, findings=None, authority=None, binding=None):
        return s.compile_detached_synthesis(
            self.findings if findings is None else findings,
            self.authority if authority is None else authority,
            m.BINDING if binding is None else binding,
            [self.proposal] if proposals is None else proposals,
            self.standalone if standalone is None else standalone,
        )

    def test_exact_reproduction_and_two_review_files(self):
        self.assertEqual(set(self.outputs), {f"{m.OUT}/synthesis_candidate_package.json", f"{m.OUT}/review_package.json"})
        self.assertEqual({p.name for p in (m.ROOT / m.OUT).iterdir()}, {"synthesis_candidate_package.json", "review_package.json"})
        for name, content in self.outputs.items():
            self.assertEqual((m.ROOT / name).read_bytes().replace(b"\r\n", b"\n"), content)
        s.validate_detached_synthesis(self.package, self.findings, self.authority, m.BINDING, [self.proposal], self.standalone)

    def test_exact_pinned_sources_and_human_acceptance_despite_candidate_flags(self):
        records = s.accepted_records(self.findings, self.authority, m.BINDING)
        self.assertEqual(set(records), {m.FUNDING, m.HR1048, m.BARGAINING})
        self.assertEqual(self.findings["findings_subject_sha256"], "795027fdcf49a4956b99804be9d44ec7bd233877e4bc76caa4121f7b61df169d")
        self.assertEqual(self.authority["authority_subject_sha256"], "456d9f6f9577e8604480cdb40a08cb1f92e443ab3e02ff33cb2ecd193ca16638")
        for record in records.values():
            self.assertEqual(record["candidate_state"], "proposed_not_accepted")
            self.assertIs(record["authorizing"], False)
        for path in (m.BINDING.findings_path, m.BINDING.authority_path):
            before = subprocess.check_output(["git", "show", f"{m.BASE}:{path}"], cwd=m.ROOT)
            self.assertEqual(json.loads(before), m.load(path))

    def test_resealed_source_mutations_cannot_change_trusted_pins(self):
        for target in ("findings", "authority"):
            changed = deepcopy(getattr(self, target))
            if target == "findings":
                changed["subject"]["accepted_proposition_records"][0]["summary"] += " changed"
                changed["findings_subject_sha256"] = m.digest(changed["subject"])
            else:
                changed["subject"]["decisions"][0]["decision"] = "accepted_as_written_but_changed"
                changed["authority_subject_sha256"] = m.digest(changed["subject"])
            with self.subTest(target=target), self.assertRaisesRegex(s.DetachedSynthesisError, "trusted pin"):
                self.compile(**{target: changed})

    def test_exact_authority_reference_record_and_ledger_cross_bindings(self):
        for mutation in ("authority_reference", "record", "ledger", "graph", "relationship", "decision"):
            findings, authority = deepcopy(self.findings), deepcopy(self.authority)
            if mutation == "authority_reference":
                findings["subject"]["human_authority"]["path"] = "wrong.json"
            elif mutation == "record":
                findings["subject"]["accepted_proposition_records"][0]["direction"] = "support"
            elif mutation == "ledger":
                findings["subject"]["accepted_episode_disposition_ledger"].pop()
            elif mutation == "graph":
                findings["subject"]["candidate_graph_sha256"] = "0" * 64
            elif mutation == "relationship":
                findings["subject"]["relationship_evidence_by_proposition"] = {}
            else:
                authority["subject"]["decisions"].pop()
                authority["authority_subject_sha256"] = m.digest(authority["subject"])
                findings["subject"]["human_authority"]["authority_subject_sha256"] = authority["authority_subject_sha256"]
            findings["findings_subject_sha256"] = m.digest(findings["subject"])
            # Even a separately repinned fixture must obey all internal cross-bindings.
            binding = replace(m.BINDING, findings_document_sha256=m.digest(findings), authority_document_sha256=m.digest(authority))
            with self.subTest(mutation=mutation), self.assertRaises(s.DetachedSynthesisError):
                self.compile(findings=findings, authority=authority, binding=binding)

    def test_one_exact_hypothesis_with_two_findings_three_episodes_four_actions(self):
        self.assertEqual(self.candidate["proposition_id"], m.CANDIDATE)
        self.assertEqual(self.candidate["proposition_type"], "mechanism_divide")
        self.assertEqual(self.candidate["summary"], "Within the reviewed education foreign-influence record, Foushee opposed two proposals that would make educational institutions ineligible for specified federal funds because of China-linked relationships, while supporting an H.R. 1048 substitute that would impose detailed foreign-gift and contract reporting and compliance rules. Her later opposition to the distinct final H.R. 1048 package does not identify which broader provision she rejected and prevents treating these votes as a general position on foreign-influence regulation.")
        self.assertEqual(self.candidate["source_finding_ids"], [m.FUNDING, m.HR1048])
        self.assertEqual(self.candidate["evidence_counts"], {"accepted_findings": 2, "episodes": 3, "actions": 4})
        self.assertEqual(set(self.candidate["evidence_action_ids"]), {"house:119:1:120", "house:119:1:313", "house:119:1:79", "house:119:1:83"})
        self.assertEqual(self.candidate["evidence_episode_ids"].count("hr-1048-amendment-and-final-passage"), 1)

    def test_complete_three_finding_accounting_and_bargaining_standalone(self):
        accounting = {r["source_finding_id"]: r for r in self.package["subject"]["source_finding_accounting"]}
        self.assertEqual(set(accounting), {m.FUNDING, m.HR1048, m.BARGAINING})
        self.assertEqual(accounting[m.BARGAINING]["disposition"], "intentionally_standalone_no_safe_synthesis")
        self.assertEqual(accounting[m.BARGAINING]["candidate_ids"], [])
        self.assertTrue(accounting[m.HR1048]["material_limiter"])
        self.assertEqual(sum(r["disposition"] == "primary_synthesis_input" for r in accounting.values()), 2)
        self.assertEqual(self.review["accounting_counts"], {
            "accepted_source_findings": 3, "primary_synthesis_findings": 2, "standalone_findings": 1,
            "candidate_episodes": 3, "candidate_actions": 4, "all_source_finding_episodes": 5,
            "all_source_finding_actions": 6, "inherited_ledger_episodes": 16, "inherited_ledger_actions": 17,
        })
        with self.assertRaises(s.DetachedSynthesisError):
            self.compile(standalone={})
        with self.assertRaises(s.DetachedSynthesisError):
            self.compile(standalone=self.standalone | {m.FUNDING: "Already used"})

    def test_zero_candidate_outcome_preserves_all_findings_and_ledger(self):
        reasons = {pid: "No safe synthesis is proposed; preserve the accepted finding independently."
                   for pid in (m.FUNDING, m.HR1048, m.BARGAINING)}
        package = self.compile(proposals=[], standalone=reasons)
        s.validate_detached_synthesis(package, self.findings, self.authority, m.BINDING, [], reasons)
        self.assertEqual(package["subject"]["synthesis_candidates"], [])
        self.assertEqual(len(package["subject"]["source_finding_accounting"]), 3)
        self.assertTrue(all(r["disposition"] == "intentionally_standalone_no_safe_synthesis"
                            and r["candidate_ids"] == [] for r in package["subject"]["source_finding_accounting"]))
        self.assertEqual(package["subject"]["inherited_episode_disposition_ledger"], self.findings["subject"]["accepted_episode_disposition_ledger"])
        self.assertEqual(package["subject"]["accepted_synthesis_count"], 0)

    def test_no_raw_actions_or_episodes_can_bypass_accepted_lineage(self):
        for field in ("evidence_action_ids", "evidence_episode_ids", "raw_votes", "source_lineage"):
            proposal = deepcopy(self.proposal)
            proposal[field] = ["house:119:1:312"]
            with self.subTest(field=field), self.assertRaises(s.DetachedSynthesisError):
                self.compile(proposals=[proposal])
        for ids in (["house:119:1:120", "house:119:1:313"], [m.FUNDING], [m.FUNDING, m.FUNDING]):
            proposal = deepcopy(self.proposal)
            proposal["source_finding_ids"] = ids
            with self.subTest(ids=ids), self.assertRaises(s.DetachedSynthesisError):
                self.compile(proposals=[proposal])
        proposal = deepcopy(self.proposal)
        proposal["relationship_evidence"]["mechanisms_by_finding"][m.FUNDING]["action_ids"] = ["house:119:1:312"]
        with self.assertRaises(s.DetachedSynthesisError):
            self.compile(proposals=[proposal])

    def test_topic_only_or_unmapped_relationship_is_rejected(self):
        for mutation in ("topic", "same_mechanism", "unknown_mechanism", "unmapped_quote", "missing_finding", "empty_contrast", "scope"):
            proposal = deepcopy(self.proposal)
            rel = proposal["relationship_evidence"]
            if mutation == "topic":
                rel["basis"] = "shared_topic"
            elif mutation == "same_mechanism":
                rel["mechanisms_by_finding"][m.HR1048]["mechanism"] = "funding_eligibility_restriction"
            elif mutation == "unknown_mechanism":
                rel["mechanisms_by_finding"][m.HR1048]["mechanism"] = "foreign_influence_topic"
            elif mutation == "unmapped_quote":
                rel["mechanisms_by_finding"][m.HR1048]["source_quote"] = "Unaccepted reinterpretation"
            elif mutation == "missing_finding":
                rel["mechanisms_by_finding"].pop(m.HR1048)
            elif mutation == "empty_contrast":
                rel["contrast"] = ""
            else:
                rel["claim_scope"] = "general_regulatory_preference"
            with self.subTest(mutation=mutation), self.assertRaises(s.DetachedSynthesisError):
                self.compile(proposals=[proposal])

    def test_all_limits_and_complete_mixed_episode_are_inherited_verbatim(self):
        source = {r["proposition_id"]: r for r in self.findings["subject"]["accepted_proposition_records"]}
        for pid in (m.FUNDING, m.HR1048):
            self.assertEqual(self.candidate["inherited_material_limitations"][pid], source[pid]["material_limitations"])
            self.assertEqual(self.candidate["inherited_episode_semantic_evidence"][pid], source[pid]["episode_semantic_evidence"])
        self.assertEqual(sum(len(v) for v in self.candidate["inherited_material_limitations"].values()), 7)
        self.assertIn("it does not establish opposition to any one component", self.review["hr1048_final_passage_boundary"][1])
        self.assertIn("fines", self.candidate["relationship_evidence"]["mechanisms_by_finding"][m.HR1048]["source_quote"])
        self.assertEqual(self.package["subject"]["accepted_source_findings"], list(source.values()))
        proposal = deepcopy(self.proposal)
        proposal["material_limiter_finding_ids"] = []
        with self.assertRaisesRegex(s.DetachedSynthesisError, "mixed finding"):
            self.compile(proposals=[proposal])

    def test_full_ledger_not_voting_receipts_and_no_trajectory(self):
        ledger = self.package["subject"]["inherited_episode_disposition_ledger"]
        self.assertEqual(ledger, self.findings["subject"]["accepted_episode_disposition_ledger"])
        self.assertEqual(len(ledger), 16)
        self.assertEqual(sum(r["disposition"] == "receipt_only_no_elevation" for r in ledger), 8)
        non_directional = next(r for r in ledger if "house:119:1:312" in r["action_ids"])
        self.assertEqual(non_directional["disposition"], "non_directional_receipt")
        self.assertIn("Not Voting", non_directional["reason"])
        self.assertFalse(any("trajectory" in r["disposition"] for r in ledger))
        self.assertNotIn("house:119:1:312", self.candidate["evidence_action_ids"])

    def test_competing_interpretation_and_prohibited_claims(self):
        self.assertIn("bill-specific judgments", self.candidate["competing_interpretation"])
        self.assertEqual(self.candidate["prohibited_inferences"], s.PROHIBITED_INFERENCES)
        for field, text in (("summary", "Foushee is motivated by party loyalty."),
                            ("summary", "Her ideology explains these votes."),
                            ("summary", "Foushee generally prefers disclosure over enforcement."),
                            ("competing_interpretation", "")):
            proposal = deepcopy(self.proposal)
            proposal[field] = text
            with self.subTest(text=text), self.assertRaises(s.DetachedSynthesisError):
                self.compile(proposals=[proposal])

    def test_no_downstream_authority_or_additional_synthesis_type(self):
        for obj in (self.package, self.review, self.candidate):
            for flag in ("accepted", "authorizing", "public", "production_selectable"):
                self.assertIs(obj[flag], False)
        for subject in (self.package["subject"], self.review, self.candidate):
            self.assertEqual(subject["downstream_authorizations"], s.DENIED)
            self.assertTrue(all(v is False for v in subject["downstream_authorizations"].values()))
        for mutation in ("synthesis_type", "authority"):
            proposal = deepcopy(self.proposal)
            if mutation == "synthesis_type":
                proposal["proposition_type"] = "uniform_direction"
            else:
                proposal["accepted"] = True
            with self.subTest(mutation=mutation), self.assertRaises(s.DetachedSynthesisError):
                self.compile(proposals=[proposal])
        with self.assertRaises(s.DetachedSynthesisError):
            self.compile(proposals=[self.proposal, self.proposal])

    def test_resealed_output_loss_or_escalation_is_rejected(self):
        for mutation in ("limitation", "lineage", "accounting", "ledger", "authority"):
            package = deepcopy(self.package)
            subject = package["subject"]
            candidate = subject["synthesis_candidates"][0]
            if mutation == "limitation":
                candidate["inherited_material_limitations"][m.HR1048].pop(1)
            elif mutation == "lineage":
                candidate["evidence_action_ids"].pop()
            elif mutation == "accounting":
                subject["source_finding_accounting"].pop()
            elif mutation == "ledger":
                subject["inherited_episode_disposition_ledger"].pop()
            else:
                subject["downstream_authorizations"]["publication"] = True
            candidate["candidate_sha256"] = m.digest({k: v for k, v in candidate.items() if k != "candidate_sha256"})
            package["package_sha256"] = m.digest({k: v for k, v in package.items() if k != "package_sha256"})
            with self.subTest(mutation=mutation), self.assertRaises(s.DetachedSynthesisError):
                s.validate_detached_synthesis(package, self.findings, self.authority, m.BINDING, [self.proposal], self.standalone)

    def test_frozen_upstream_paths_and_existing_ci_jobs(self):
        paths = [m.SOURCE, "docs/editorial/shared_corpora/house_119_v2",
                 "backend/app/etl/full_record_synthesis_candidates.py",
                 "scripts/build_m14d_education_reanalysis.py", "backend/tests/test_m14d_education_reanalysis.py"]
        self.assertEqual(subprocess.check_output(["git", "diff", "--name-only", m.BASE, "--", *paths], cwd=m.ROOT), b"")
        workflow = ".github/workflows/backend-tests.yml"
        before = subprocess.check_output(["git", "show", f"{m.BASE}:{workflow}"], cwd=m.ROOT).decode().replace("\r\n", "\n")
        after = (m.ROOT / workflow).read_text(encoding="utf-8")
        # Preserve prior jobs without preventing a later milestone from adding its own job.
        starts = [match.start() for match in re.finditer(r"(?m)^  [a-z0-9-]+:\n", before)]
        for start, end in zip(starts, [*starts[1:], len(before)], strict=True):
            self.assertIn(before[start:end].rstrip(), after)
        with patch.object(m.subprocess, "check_output", side_effect=[f"{m.SOURCE}/accepted_behavioral_findings.json\n", ""]):
            with self.assertRaisesRegex(s.DetachedSynthesisError, "scope violation"):
                m.validate_scope()


if __name__ == "__main__":
    unittest.main()
