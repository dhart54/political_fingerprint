from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_action_interpretation_candidate_review import (  # noqa: E402
    BENCHMARK_ACTIONS,
    OUTPUT_ROOT,
    build_freeze,
    build_post_freeze,
)
from validate_action_interpretation_candidate_review import validate  # noqa: E402


class ActionInterpretationCandidateReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.batch = json.loads(
            (OUTPUT_ROOT / "candidate_batch.json").read_text(encoding="utf-8")
        )
        cls.reviews = json.loads(
            (OUTPUT_ROOT / "adversarial_reviews.json").read_text(encoding="utf-8")
        )
        cls.sample = json.loads(
            (OUTPUT_ROOT / "sample_manifest.json").read_text(encoding="utf-8")
        )

    def test_complete_candidate_and_review_accounting(self) -> None:
        self.assertEqual(len(self.batch["primary_candidates"]), 37)
        self.assertEqual(len(self.batch["final_candidates"]), 37)
        self.assertEqual(len(self.reviews["reviews"]), 37)
        self.assertEqual(
            len({row["action_id"] for row in self.batch["final_candidates"]}), 37
        )

    def test_candidate_status_and_confidence_accounting(self) -> None:
        self.assertEqual(
            Counter(row["status"] for row in self.batch["final_candidates"]),
            {"proposed": 35, "ambiguous": 1, "no_safe_candidate": 1},
        )
        self.assertEqual(
            Counter(row["confidence"] for row in self.batch["final_candidates"]),
            {"high": 28, "medium": 7, "low": 2},
        )

    def test_one_bounded_correction_cycle_preserves_originals(self) -> None:
        self.assertEqual(
            {row["action_id"] for row in self.batch["corrections"]},
            {"house:119:2:155", "house:119:2:278"},
        )
        self.assertTrue(
            all(
                row["correction_cycle"] == 1 and not row["benchmark_used"]
                for row in self.batch["corrections"]
            )
        )
        self.assertEqual(
            len(self.batch["primary_candidates"]), len(self.batch["final_candidates"])
        )

    def test_fisa_candidates_keep_cross_domain_scope_limits(self) -> None:
        candidates = {row["action_id"]: row for row in self.batch["final_candidates"]}
        expected = {
            "surveillance_authority",
            "fisc_and_court_authority",
            "civil_liberty_protections",
        }
        for action_id in ("house:119:2:155", "house:119:2:221"):
            self.assertEqual(
                set(candidates[action_id]["cross_domain_limitations"]), expected
            )

    def test_random_population_excludes_benchmarks_and_selection_is_unique(
        self,
    ) -> None:
        self.assertEqual(len(self.sample["ordered_population"]), 30)
        self.assertFalse(set(self.sample["ordered_population"]) & BENCHMARK_ACTIONS)
        self.assertEqual(len(self.sample["selected_random_action_ids"]), 12)
        self.assertEqual(len(set(self.sample["selected_random_action_ids"])), 12)

    def test_required_challenge_cases_are_present_with_reasons(self) -> None:
        challenge = {
            row["action_id"]: row["inclusion_reasons"]
            for row in self.sample["challenge_actions"]
        }
        self.assertIn("house:119:2:155", challenge)
        self.assertIn("house:119:2:221", challenge)
        self.assertIn("house:119:1:166", challenge)
        self.assertTrue(all(challenge.values()))

    def test_benchmark_is_evaluation_only_and_post_freeze(self) -> None:
        comparison = json.loads(
            (OUTPUT_ROOT / "benchmark_comparison.json").read_text(encoding="utf-8")
        )
        self.assertTrue(comparison["post_freeze_only"])
        self.assertTrue(self.batch["freeze_precedes_benchmark_access"])
        self.assertTrue(
            all(
                row["evaluation_only_no_candidate_mutation"]
                for row in comparison["comparisons"]
            )
        )

    def test_worker_packets_contain_no_benchmark_or_party_fields(self) -> None:
        forbidden = {
            "member_party",
            "sponsor_party",
            "cosponsor_party",
            "accepted_benchmark_interpretations",
            "benchmark_conclusion",
            "semantic_ir",
            "public_language",
            "episode_membership",
            "synthesis_outcomes",
            "other_action_candidates",
        }
        for path in (OUTPUT_ROOT / "worker_packets").glob("*.json"):
            packet = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(forbidden & set(packet))
            self.assertNotIn(
                "accepted_semantic_reference", path.read_text(encoding="utf-8")
            )

    def test_candidate_root_is_not_referenced_by_canonical_or_runtime_state(
        self,
    ) -> None:
        paths = [
            ROOT
            / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json",
            ROOT / "backend/app/etl/manual_interpretations.py",
            ROOT / "backend/app/etl/ndaa_amendment_interpretations.py",
        ]
        self.assertTrue(
            all(
                "interpretation_candidates" not in path.read_text(encoding="utf-8")
                for path in paths
            )
        )

    def test_freeze_and_post_freeze_outputs_are_deterministic(self) -> None:
        self.assertEqual(
            build_freeze(check=True)["candidate_batch_subject_sha256"],
            self.batch["candidate_batch_subject_sha256"],
        )
        self.assertEqual(
            build_post_freeze(check=True)["parity"]["parity_state"], "pass"
        )

    def test_full_validator_passes(self) -> None:
        self.assertEqual(validate()["status"], "pass")


if __name__ == "__main__":
    unittest.main()
