import copy
import csv
import io
import unittest

from backend.app.semantic_ir.shared_corpus import sealed_digest
from scripts.shared_candidate_research import governed_sources_at_url, research_queue, queue_table


class SharedCandidateResearchTests(unittest.TestCase):
    def test_compact_queue_retains_dependency_flags_and_escaped_questions(self):
        row = dict(action_id="house:119:2:44", date="2026-01-22", measure="exact",
                   question='Question with\ta tab and "quotation"', disposition="source_unresolved",
                   has_membership_record=True, review_progress=dict(substantive_review_performed=True,
                       exact_action_binding_unresolved=True, required_evidence_unavailable=False,
                       authoritative_source_conflict=True))
        before = copy.deepcopy(row)
        parsed = list(csv.DictReader(io.StringIO(queue_table([row])), delimiter="\t"))[0]
        self.assertEqual(parsed["question"], row["question"])
        for field in ["has_membership_record", *row["review_progress"]]:
            value = row.get(field, row["review_progress"].get(field))
            self.assertEqual(parsed[field], str(value))
        self.assertEqual(row, before)

    def test_exact_url_preserves_editions_and_excerpts_and_rejects_changed_bytes(self):
        sources = []
        for sid, url, text in [("a", "https://official/2024", "first excerpt"),
                               ("b", "https://official/2024", "second excerpt"),
                               ("c", "https://official/2025", "new edition")]:
            s = {"source_id": sid, "url": url, "text": text}
            s["governed_bytes_sha256"] = sealed_digest(s, "governed_bytes_sha256")
            sources.append(s)
        capture = {"sources": sources}
        before = copy.deepcopy(capture)
        self.assertEqual([s["source_id"] for s in governed_sources_at_url(capture, "https://official/2024")], ["a", "b"])
        self.assertEqual(governed_sources_at_url(capture, "https://official/2024/"), [])
        self.assertEqual(capture, before)
        sources[0]["text"] = "changed"
        with self.assertRaisesRegex(ValueError, "governed source changed"):
            governed_sources_at_url(capture, "https://official/2024")

    def test_duplicate_identity_fails_even_if_url_does_not_match(self):
        with self.assertRaisesRegex(ValueError, "duplicate source"):
            governed_sources_at_url({"sources": [{"source_id": "a", "url": "x"}] * 2}, "y")

    def test_queue_keeps_unreviewed_controls_and_examined_dependencies_without_mutation(self):
        rows = []
        for roll, disposition in [(79, "procedural_context"), (80, "source_unresolved"),
                                  (81, "exact_action_ineligible"), (82, "source_unresolved")]:
            rows.append({"action_id": str(roll), "session": 2, "roll": roll,
                         "date": "date", "measure": "measure", "question": "question",
                         "disposition": disposition, "review_progress": {"substantive_review_performed": roll == 82}})
        universe = {"candidate_dispositions": rows}
        membership = {"records": [{"action_id": "81"}, {"action_id": "82"}]}
        before = copy.deepcopy((universe, membership))
        result = research_queue(universe, membership, session=2, start_roll=79, limit=20)
        self.assertEqual([r["action_id"] for r in result], ["79", "80", "82"])
        self.assertTrue(result[-1]["has_membership_record"])
        self.assertEqual((universe, membership), before)
        self.assertEqual(len(research_queue(universe, membership, limit=1)), 1)
        self.assertEqual(research_queue(universe, membership, session=1), [])
        with self.assertRaises(ValueError):
            research_queue(universe, membership, limit=0)
