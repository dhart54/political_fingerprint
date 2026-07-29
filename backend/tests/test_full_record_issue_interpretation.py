from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_full_record_terminology import check, check_text  # noqa: E402
from scripts.validate_full_record_issue_interpretation import (  # noqa: E402
    FullRecordValidationError,
    compute_universe_sha256,
    validate_review,
)


REVIEW_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/"
    "f000477_justice_public_safety_119_review_state_v1.json"
)


def _review() -> dict[str, Any]:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def _as_full_record(review: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(review)
    result["axes"].update(
        {
            "review_scope": "full_defined_issue_record",
            "public_claim_class": "full_issue_synthesis",
        }
    )
    result["issue_universe"]["definition"] = (
        "Synthetic complete defined issue record for contract validation."
    )
    result["synthesis"].update(
        {
            "full_record_action_accounting": "passed",
            "full_issue_synthesis_eligible": True,
            "eligibility_blockers": [],
        }
    )
    result["frontend_state"].update(
        {
            "review_scope": "full_defined_issue_record",
            "public_claim_class": "full_issue_synthesis",
            "full_issue_synthesis_eligible": True,
            "available_labels": [
                "Full review complete",
                "Full issue interpretation available",
                "Vote receipts available",
            ],
        }
    )
    result["frontend_state"]["conclusion_teaser"][
        "valid_scope"
    ] = "full_defined_issue_record"
    result["issue_universe"]["snapshot_sha256"] = compute_universe_sha256(result)
    return result


class FullRecordIssueInterpretationContractTests(unittest.TestCase):
    def test_committed_foushee_state_validates(self) -> None:
        summary = validate_review(_review())
        self.assertEqual(
            summary,
            {
                "action_count": 7,
                "episode_count": 5,
                "review_friendly_action_count": 7,
            },
        )

    def test_every_action_is_accounted_for_exactly_once(self) -> None:
        mutated = _review()
        mutated["action_accounting"].append(
            copy.deepcopy(mutated["action_accounting"][0])
        )
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "accounted for exactly once",
        ):
            validate_review(mutated)

    def test_review_friendly_action_cannot_remain_uninterpreted_when_complete(
        self,
    ) -> None:
        mutated = _review()
        action = mutated["action_accounting"][0]
        action["disposition"] = "pending_interpretation"
        action["interpretation"] = None
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "review-friendly action remains uninterpreted",
        ):
            validate_review(mutated)

    def test_in_progress_review_may_account_for_pending_interpretation(self) -> None:
        mutated = _review()
        action = mutated["action_accounting"][0]
        action["disposition"] = "pending_interpretation"
        action["interpretation"] = None
        episode = next(
            item
            for item in mutated["episodes"]
            if item["episode_id"] == action["episode_id"]
        )
        episode.update(
            {
                "outcome": "unresolved",
                "completion_state": "partial",
                "unresolved_action_ids": [action["action_id"]],
            }
        )
        mutated["axes"].update(
            {
                "semantic_tier": "developing_read",
                "review_completion_state": "in_progress",
                "public_claim_class": "vote_record_only",
            }
        )
        mutated["synthesis"].update(
            {
                "outcome": "not_yet_determined",
                "all_interpreted_episode_outcomes_supplied": False,
                "semantic_validation": "not_run",
                "human_editorial_review": "in_progress",
                "human_approval_receipt_refs": [],
                "eligibility_blockers": [
                    "review_scope_not_full_defined_issue_record",
                    "review_completion_not_complete",
                    "action_accounting_incomplete",
                    "review_friendly_action_uninterpreted",
                    "partial_episode",
                    "episode_outcomes_not_supplied",
                    "semantic_validation_not_passed",
                    "human_editorial_review_not_approved",
                ],
            }
        )
        mutated["frontend_state"].update(
            {
                "review_completion_state": "in_progress",
                "public_claim_class": "vote_record_only",
                "interpreted_actions": 6,
                "unresolved_actions": 1,
                "complete_episode_count": 4,
                "partial_episode_count": 1,
                "conclusion_teaser": None,
            }
        )
        validate_review(mutated)

    def test_conflicting_evidence_blocks_full_synthesis(self) -> None:
        mutated = _as_full_record(_review())
        action = next(
            item
            for item in mutated["action_accounting"]
            if item["action_id"] == "house:119:1:299"
        )
        action["disposition"] = "source_conflicting"
        action["interpretation"] = None
        action["review_friendliness"].update(
            {
                "action_meaning_evidence": "conflicting",
                "action_meaning_provenance": "conflicting",
                "source_conflict_state": "conflicting",
                "is_review_friendly": False,
            }
        )
        episode = next(
            item
            for item in mutated["episodes"]
            if item["episode_id"] == "dc-policing-reform-repeal"
        )
        episode.update(
            {
                "outcome": "unresolved",
                "source_completeness": "partial",
                "completion_state": "partial",
                "unresolved_action_ids": ["house:119:1:299"],
            }
        )
        mutated["axes"].update(
            {
                "semantic_tier": "receipts_only",
                "public_claim_class": "vote_record_only",
            }
        )
        mutated["synthesis"].update(
            {
                "source_boundaries": "synthesis_blocking",
                "full_issue_synthesis_eligible": False,
                "eligibility_blockers": [
                    "partial_episode",
                    "source_unresolved",
                    "source_conflicting",
                ],
            }
        )
        mutated["frontend_state"].update(
            {
                "public_claim_class": "vote_record_only",
                "review_friendly_actions": 6,
                "interpreted_actions": 6,
                "unresolved_actions": 1,
                "complete_episode_count": 4,
                "partial_episode_count": 1,
                "full_issue_synthesis_eligible": False,
                "conclusion_teaser": None,
                "available_labels": [
                    "Full review complete",
                    "Vote receipts available",
                ],
            }
        )
        validate_review(mutated)
        self.assertFalse(mutated["synthesis"]["full_issue_synthesis_eligible"])
        self.assertIn(
            "source_conflicting",
            mutated["synthesis"]["eligibility_blockers"],
        )

    def test_sample_cannot_claim_full_record_completion_or_synthesis(self) -> None:
        mutated = _review()
        mutated["synthesis"]["full_record_action_accounting"] = "passed"
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "sample or partial review cannot claim full-record action accounting",
        ):
            validate_review(mutated)

        mutated = _review()
        mutated["axes"]["public_claim_class"] = "full_issue_synthesis"
        mutated["frontend_state"]["public_claim_class"] = "full_issue_synthesis"
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "full issue synthesis lacks full-record eligibility",
        ):
            validate_review(mutated)

    def test_benchmark_status_does_not_confer_full_record_scope(self) -> None:
        review = _review()
        self.assertTrue(review["benchmark"]["benchmark_sample_available"])
        self.assertEqual(review["axes"]["review_scope"], "benchmark_sample")
        self.assertFalse(review["synthesis"]["full_issue_synthesis_eligible"])
        validate_review(review)

    def test_complete_review_may_find_no_common_throughline(self) -> None:
        review = _as_full_record(_review())
        review["synthesis"]["outcome"] = "no_common_throughline"
        review["axes"]["public_claim_class"] = "full_review_no_common_throughline"
        review["frontend_state"].update(
            {
                "public_claim_class": "full_review_no_common_throughline",
                "available_labels": [
                    "Full review complete",
                    "No common throughline found",
                    "Vote receipts available",
                ],
            }
        )
        validate_review(review)
        self.assertTrue(review["synthesis"]["full_issue_synthesis_eligible"])

    def test_complete_review_may_find_no_safe_synthesis(self) -> None:
        review = _as_full_record(_review())
        review["synthesis"].update(
            {
                "outcome": "no_safe_synthesis",
                "full_issue_synthesis_eligible": False,
                "eligibility_blockers": ["no_safe_synthesis"],
            }
        )
        review["axes"].update(
            {
                "semantic_tier": "receipts_only",
                "public_claim_class": "full_review_no_safe_synthesis",
            }
        )
        review["frontend_state"].update(
            {
                "public_claim_class": "full_review_no_safe_synthesis",
                "full_issue_synthesis_eligible": False,
                "conclusion_teaser": None,
                "available_labels": [
                    "Full review complete",
                    "No safe synthesis available",
                    "Vote receipts available",
                ],
            }
        )
        validate_review(review)

    def test_reordering_inputs_cannot_change_identity_or_completion(self) -> None:
        baseline = _review()
        mutated = copy.deepcopy(baseline)
        mutated["issue_universe"]["action_ids"].reverse()
        mutated["action_accounting"].reverse()
        fentanyl = next(
            item
            for item in mutated["episodes"]
            if item["episode_id"] == "halt-fentanyl-legislative-path"
        )
        fentanyl["action_ids"].reverse()
        self.assertEqual(
            compute_universe_sha256(baseline),
            compute_universe_sha256(mutated),
        )
        validate_review(mutated)
        self.assertEqual(
            mutated["axes"]["review_completion_state"],
            baseline["axes"]["review_completion_state"],
        )

    def test_vote_direction_and_party_cannot_change_eligibility_or_scope(self) -> None:
        baseline = _review()
        mutated = copy.deepcopy(baseline)
        action = next(
            item
            for item in mutated["action_accounting"]
            if item["action_id"] == "house:119:1:32"
        )
        action["review_friendliness"]["member_action"] = "Nay"
        action["interpretation"]["member_action"] = "Nay"
        episode = next(
            item
            for item in mutated["episodes"]
            if item["episode_id"] == "halt-fentanyl-legislative-path"
        )
        next(
            item
            for item in episode["member_record"]
            if item["action_id"] == "house:119:1:32"
        )["member_action"] = "Nay"
        validate_review(mutated)
        self.assertEqual(
            compute_universe_sha256(mutated),
            compute_universe_sha256(baseline),
        )
        self.assertEqual(mutated["axes"]["review_scope"], baseline["axes"]["review_scope"])
        self.assertEqual(
            mutated["action_accounting"][0]["review_friendliness"][
                "is_review_friendly"
            ],
            baseline["action_accounting"][0]["review_friendliness"][
                "is_review_friendly"
            ],
        )

        party_mutation = _review()
        party_mutation["subject"]["party"] = "R"
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "schema validation failed",
        ):
            validate_review(party_mutation)

    def test_new_action_invalidates_snapshot_until_accounted_for(self) -> None:
        mutated = _review()
        mutated["issue_universe"]["action_ids"].append("house:119:1:999")
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "content digest does not match",
        ):
            validate_review(mutated)

        mutated["issue_universe"]["snapshot_sha256"] = compute_universe_sha256(mutated)
        with self.assertRaisesRegex(
            FullRecordValidationError,
            "action accounting must exactly equal",
        ):
            validate_review(mutated)

    def test_protected_benchmarks_and_receipts_remain_byte_stable(self) -> None:
        review = _review()
        for protected in review["provenance"]["protected_files"]:
            digest = hashlib.sha256((ROOT / protected["path"]).read_bytes()).hexdigest()
            self.assertEqual(digest, protected["sha256"], protected["path"])
        validate_review(review)


class FullRecordTerminologyGovernanceTests(unittest.TestCase):
    def test_current_authoritative_documents_pass(self) -> None:
        self.assertEqual(check(), [])

    def test_benchmark_broadening_phrase_is_rejected(self) -> None:
        errors = check_text(
            "This benchmark is a full issue conclusion.",
            path="docs/current.md",
        )
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
