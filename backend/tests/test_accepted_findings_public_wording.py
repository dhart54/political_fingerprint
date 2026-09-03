"""M14F current-path public-wording and prominence review proofs."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import re
import subprocess
import unittest
from unittest.mock import patch

from backend.app.semantic_ir import accepted_findings_public_wording as w
from backend.app.semantic_ir.shared_corpus import digest
from scripts import build_m14f_education_public_wording as m


class AcceptedFindingsPublicWordingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.findings = m.load(m.BINDING.findings_path)
        cls.behavioral_authority = m.load(m.BINDING.behavioral_authority_path)
        cls.synthesis = m.load(m.BINDING.synthesis_path)
        cls.synthesis_authority = m.load(m.BINDING.synthesis_authority_path)
        cls.definitions = m.definitions(cls.findings, cls.synthesis)
        cls.prominence = m.prominence_review()
        cls.outputs = m.build_outputs()
        cls.package = json.loads(cls.outputs[f"{m.OUT}/public_wording_candidate_package.json"])
        cls.review = json.loads(cls.outputs[f"{m.OUT}/review_package.json"])

    def compile(self, definitions=None, findings=None, behavioral_authority=None,
                synthesis=None, synthesis_authority=None, binding=None):
        return w.compile_public_wording(
            self.findings if findings is None else findings,
            self.behavioral_authority if behavioral_authority is None else behavioral_authority,
            self.synthesis if synthesis is None else synthesis,
            self.synthesis_authority if synthesis_authority is None else synthesis_authority,
            m.BINDING if binding is None else binding,
            self.definitions if definitions is None else definitions,
            self.prominence,
        )

    def test_exact_reproduction_and_output_directory_contains_only_two_files(self):
        self.assertEqual(set(self.outputs), {
            f"{m.OUT}/public_wording_candidate_package.json", f"{m.OUT}/review_package.json"})
        self.assertEqual({p.name for p in (m.ROOT / m.OUT).iterdir()}, {
            "public_wording_candidate_package.json", "review_package.json"})
        for name, content in self.outputs.items():
            self.assertEqual((m.ROOT / name).read_bytes().replace(b"\r\n", b"\n"), content)
        w.validate_public_wording(
            self.package, self.findings, self.behavioral_authority, self.synthesis,
            self.synthesis_authority, m.BINDING, self.definitions, self.prominence)

    def test_exact_pinned_accepted_sources_and_subject_seals(self):
        self.assertEqual(digest(self.findings), m.BINDING.findings_document_sha256)
        self.assertEqual(digest(self.behavioral_authority), m.BINDING.behavioral_authority_document_sha256)
        self.assertEqual(digest(self.synthesis), m.BINDING.synthesis_document_sha256)
        self.assertEqual(digest(self.synthesis_authority), m.BINDING.synthesis_authority_document_sha256)
        self.assertEqual(self.findings["findings_subject_sha256"],
                         "795027fdcf49a4956b99804be9d44ec7bd233877e4bc76caa4121f7b61df169d")
        self.assertEqual(self.behavioral_authority["authority_subject_sha256"],
                         "456d9f6f9577e8604480cdb40a08cb1f92e443ab3e02ff33cb2ecd193ca16638")
        self.assertEqual(self.synthesis["accepted_internal_synthesis_subject_sha256"],
                         "efbd6105b9320cc8f16e203f16f2da37cd1f6acaf6eb6e7cd153f0c860d2a1ef")
        self.assertEqual(self.synthesis_authority["authority_subject_sha256"],
                         "a7e9e599100d4128b2a4414bd21a415d1663eb79d81d92397ddf056795668c82")
        for path in vars(m.BINDING).values():
            if isinstance(path, str) and path.endswith(".json"):
                before = subprocess.check_output(["git", "show", f"{m.BASE}:{path}"], cwd=m.ROOT)
                self.assertEqual(json.loads(before), m.load(path))

    def test_three_behavioral_sources_and_one_internal_synthesis(self):
        records, synthesis = w.accepted_semantics(
            self.findings, self.behavioral_authority, self.synthesis,
            self.synthesis_authority, m.BINDING)
        self.assertEqual(set(records), {m.FUNDING, m.BARGAINING, m.HR1048})
        self.assertEqual(synthesis["proposition_id"], m.SYNTHESIS)
        self.assertEqual(synthesis["candidate_sha256"],
                         "e1f897237de6934c96f034205b4e2fdf6b73afafbe6081507c5d3861180bdc4d")
        self.assertEqual(self.synthesis["subject"]["accepted_synthesis_count"], 1)

    def test_four_exact_candidate_items_and_digests(self):
        items = self.package["subject"]["wording_items"]
        self.assertEqual(len(items), 4)
        expected = {
            m.OVERVIEW: ("issue_overview", "Education & Workforce",
                         "2 linked findings · 4 House votes", None, m.MAIN_TAKEAWAY, m.SYNTHESIS),
            m.FUNDING_ITEM: ("repeated_pattern", "Opposed two China-linked education funding restrictions",
                             "2 bills · 2 House votes", None,
                             self.definitions[1]["primary_sentence"], m.FUNDING),
            m.BARGAINING_ITEM: ("repeated_pattern", "Supported keeping collective bargaining in force",
                                "2 bills · 2 House votes", None,
                                self.definitions[2]["primary_sentence"], m.BARGAINING),
            m.HR1048_ITEM: ("notable_choice",
                            "Supported a reporting substitute, opposed the final H.R. 1048 package",
                            "1 legislative episode · 2 House votes",
                            {"label": "Mixed", "symbol": "±"},
                            self.definitions[3]["primary_sentence"], m.HR1048),
        }
        self.assertEqual(set(self.review["wording_item_digests"]), set(expected))
        for item in items:
            item_id = item["wording_item_id"]
            self.assertEqual(tuple(item[k] for k in (
                "surface", "public_title", "evidence_count_label", "direction_display",
                "primary_sentence", "semantic_source_id")), expected[item_id])
            self.assertEqual(item["wording_item_sha256"],
                             digest({k: v for k, v in item.items() if k != "wording_item_sha256"}))
            self.assertEqual(self.review["wording_item_digests"][item_id], item["wording_item_sha256"])

    def test_each_source_has_exactly_one_primary_item(self):
        subject = self.package["subject"]
        accounting = subject["behavioral_finding_accounting"]
        self.assertEqual(len(accounting), 3)
        self.assertEqual({r["source_finding_id"] for r in accounting},
                         {m.FUNDING, m.BARGAINING, m.HR1048})
        self.assertEqual(subject["synthesis_accounting"], {
            "source_synthesis_id": m.SYNTHESIS, "disposition": "proposed_issue_overview",
            "wording_item_ids": [m.OVERVIEW]})
        source_ids = [item["semantic_source_id"] for item in subject["wording_items"]]
        self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_lineage_counts_and_mixed_episode_boundaries(self):
        items = {i["wording_item_id"]: i for i in self.package["subject"]["wording_items"]}
        overview = items[m.OVERVIEW]["derived_lineage"]
        self.assertEqual(overview["accepted_findings"], 2)
        self.assertEqual((len(overview["episode_ids"]), len(overview["action_ids"])), (3, 4))
        behavioral = [items[i]["derived_lineage"] for i in
                      (m.FUNDING_ITEM, m.BARGAINING_ITEM, m.HR1048_ITEM)]
        self.assertEqual((sum(len(r["episode_ids"]) for r in behavioral),
                          sum(len(r["action_ids"]) for r in behavioral)), (5, 6))
        self.assertEqual((len(items[m.HR1048_ITEM]["derived_lineage"]["episode_ids"]),
                          len(items[m.HR1048_ITEM]["derived_lineage"]["action_ids"])), (1, 2))
        self.assertEqual(self.review["lineage_counts"], {
            "behavioral_findings": 3, "behavioral_episodes": 5, "behavioral_actions": 6,
            "overview_source_findings": 2, "overview_episodes": 3, "overview_actions": 4,
            "full_issue_episodes": 16, "full_issue_actions": 17})

    def test_hr1005_is_non_directional_and_never_wording_evidence(self):
        non_directional = self.package["subject"]["excluded_non_directional_receipts"]
        self.assertEqual(len(non_directional), 1)
        self.assertIn("house:119:1:312", non_directional[0]["action_ids"])
        self.assertIn("Not Voting", non_directional[0]["reason"])
        all_evidence = {action for item in self.package["subject"]["wording_items"]
                        for action in item["derived_lineage"]["action_ids"]}
        self.assertNotIn("house:119:1:312", all_evidence)
        self.assertFalse(any(item["surface"] == "trajectory"
                             for item in self.package["subject"]["wording_items"]))

    def test_all_eighteen_limitations_have_one_explicit_treatment(self):
        items = self.package["subject"]["wording_items"]
        treatments = [row for item in items for row in item["limitation_treatments"]]
        self.assertEqual(len(treatments), 18)
        self.assertEqual(self.review["limitation_treatment_counts"], {
            "compressed_or_omitted": 11, "retained_public_copy": 7})
        self.assertEqual({row["treatment"] for row in treatments}, w.TREATMENTS)
        self.assertTrue(all(row["reason"] for row in treatments
                            if row["treatment"] == "compressed_or_omitted"))
        self.assertTrue(all(row["reason"] is None for row in treatments
                            if row["treatment"] == "retained_public_copy"))

    def test_raw_ids_unknown_sources_and_topic_similarity_cannot_bypass_semantics(self):
        for field in ("action_ids", "episode_ids", "raw_votes", "source_lineage"):
            definitions = deepcopy(self.definitions)
            definitions[0][field] = ["house:119:1:312"]
            with self.subTest(field=field), self.assertRaises(w.PublicWordingReviewError):
                self.compile(definitions=definitions)
        definitions = deepcopy(self.definitions)
        definitions[0]["semantic_source_id"] = "topic:foreign_influence_in_education"
        with self.assertRaisesRegex(w.PublicWordingReviewError, "unknown or topic-only"):
            self.compile(definitions=definitions)

    def test_zero_main_takeaway_variant_is_valid_and_keeps_three_findings(self):
        zero = self.compile(definitions=self.definitions[1:])
        w.validate_public_wording(
            zero, self.findings, self.behavioral_authority, self.synthesis,
            self.synthesis_authority, m.BINDING, self.definitions[1:], self.prominence)
        self.assertEqual([i["wording_item_id"] for i in zero["subject"]["wording_items"]],
                         [m.FUNDING_ITEM, m.BARGAINING_ITEM, m.HR1048_ITEM])
        self.assertEqual(zero["subject"]["synthesis_accounting"]["disposition"],
                         "accepted_semantics_retained_no_overview_wording")
        self.assertEqual(zero["subject"]["synthesis_accounting"]["wording_item_ids"], [])
        self.assertEqual(self.review["zero_main_takeaway_variant"]["package_sha256"],
                         zero["package_sha256"])

    def test_behavioral_omission_or_duplicate_is_rejected(self):
        with self.assertRaises(w.PublicWordingReviewError):
            self.compile(definitions=[self.definitions[0], *self.definitions[2:]])
        duplicated = deepcopy(self.definitions)
        duplicated[2]["semantic_source_id"] = m.FUNDING
        with self.assertRaises(w.PublicWordingReviewError):
            self.compile(definitions=duplicated)

    def test_prominence_is_pending_and_a_b_remain_unselected(self):
        prominence = self.package["subject"]["prominence_review"]
        self.assertEqual(prominence["semantic_validity"], "accepted_internal_synthesis_not_reopened")
        self.assertEqual(prominence["decision_state"], "pending_independent_human_product_review")
        self.assertEqual(prominence["proposed_prominence_note"], m.PROMINENCE_NOTE)
        self.assertEqual(prominence["main_takeaway_alternative"],
                         "omit_main_takeaway_and_retain_all_three_findings")
        self.assertEqual(len(prominence["option_a_main_takeaway"]), 4)
        self.assertEqual(len(prominence["option_b_no_main_takeaway"]), 2)

    def test_candidate_and_all_downstream_permissions_remain_false(self):
        for artifact in (self.package, self.review):
            for flag in ("accepted", "authorizing", "public", "production_selectable"):
                self.assertIs(artifact[flag], False)
            self.assertEqual(artifact.get("subject", artifact)["downstream_authorizations"], w.DENIED)
        for item in self.package["subject"]["wording_items"]:
            for flag in ("accepted", "authorizing", "public", "production_selectable"):
                self.assertIs(item[flag], False)
            self.assertEqual(item["candidate_state"], "proposed_not_accepted")
            self.assertEqual(item["downstream_authorizations"], w.DENIED)
        self.assertTrue(all(value is False for value in w.DENIED.values()))

    def test_unsafe_public_language_is_rejected(self):
        for text in ("Her ideology explains these votes.", "This was a good bill.",
                     "Voters should vote for her.", "This framework became law.",
                     "She generally opposes foreign-influence regulation.",
                     "She always opposes China policy.", "She is pro-labor."):
            definitions = deepcopy(self.definitions)
            definitions[1]["primary_sentence"] = text
            with self.subTest(text=text), self.assertRaisesRegex(
                    w.PublicWordingReviewError, "prohibited public language"):
                self.compile(definitions=definitions)

    def test_mutated_or_resealed_sources_cannot_escape_cross_bindings(self):
        for target in ("findings", "behavioral_authority", "synthesis", "synthesis_authority"):
            changed = deepcopy(getattr(self, target))
            if target == "findings":
                changed["subject"]["accepted_proposition_records"][0]["summary"] += " changed"
                changed["findings_subject_sha256"] = digest(changed["subject"])
                binding = replace(m.BINDING, findings_document_sha256=digest(changed))
            elif target == "behavioral_authority":
                changed["subject"]["decisions"].pop()
                changed["authority_subject_sha256"] = digest(changed["subject"])
                binding = replace(m.BINDING, behavioral_authority_document_sha256=digest(changed))
            elif target == "synthesis":
                changed["subject"]["evidence_counts"]["actions"] = 5
                changed["accepted_internal_synthesis_subject_sha256"] = digest(changed["subject"])
                binding = replace(m.BINDING, synthesis_document_sha256=digest(changed))
            else:
                changed["subject"]["decision"] = "revise"
                changed["authority_subject_sha256"] = digest(changed["subject"])
                binding = replace(m.BINDING, synthesis_authority_document_sha256=digest(changed))
            with self.subTest(target=target), self.assertRaises(w.PublicWordingReviewError):
                self.compile(**{target: changed, "binding": binding})

    def test_resealed_output_tampering_is_rejected_by_exact_recompilation(self):
        for mutation in ("wording", "lineage", "limitation", "authority"):
            package = deepcopy(self.package)
            item = package["subject"]["wording_items"][0]
            if mutation == "wording":
                item["primary_sentence"] += " Changed."
            elif mutation == "lineage":
                item["derived_lineage"]["action_ids"].pop()
            elif mutation == "limitation":
                item["limitation_treatments"].pop()
            else:
                package["subject"]["downstream_authorizations"]["publication"] = True
            item["wording_item_sha256"] = digest(
                {k: v for k, v in item.items() if k != "wording_item_sha256"})
            package["package_sha256"] = digest(
                {k: v for k, v in package.items() if k != "package_sha256"})
            with self.subTest(mutation=mutation), self.assertRaises(w.PublicWordingReviewError):
                w.validate_public_wording(
                    package, self.findings, self.behavioral_authority, self.synthesis,
                    self.synthesis_authority, m.BINDING, self.definitions, self.prominence)

    def test_upstream_historical_and_prior_ci_blocks_are_unchanged(self):
        frozen = [m.M14D, m.M14E,
                  "docs/editorial/shared_corpora/house_119_v2",
                  "docs/editorial/full_record_reviews/public_wording_candidates/f000477_education_workforce_119_v1",
                  "docs/editorial/full_record_reviews/site_integration_candidates/f000477_education_workforce_119_v1"]
        self.assertEqual(subprocess.check_output(
            ["git", "diff", "--name-only", m.BASE, "--", *frozen], cwd=m.ROOT), b"")
        workflow = ".github/workflows/backend-tests.yml"
        before = subprocess.check_output(["git", "show", f"{m.BASE}:{workflow}"], cwd=m.ROOT).decode()
        after = (m.ROOT / workflow).read_text(encoding="utf-8")
        starts = [match.start() for match in re.finditer(r"(?m)^  [a-z0-9-]+:\r?\n", before)]
        for start, end in zip(starts, [*starts[1:], len(before)], strict=True):
            self.assertIn(before[start:end].replace("\r\n", "\n").rstrip(), after)
        with patch.object(m.subprocess, "check_output",
                          side_effect=[f"{m.M14D}/accepted_behavioral_findings.json\n", ""]):
            with self.assertRaisesRegex(w.PublicWordingReviewError, "scope violation"):
                m.validate_scope()


if __name__ == "__main__":
    unittest.main()
