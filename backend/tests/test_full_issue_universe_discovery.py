from __future__ import annotations

import copy
import json
import unittest

from jsonschema import Draft7Validator

from backend.app.etl.universe_discovery import (
    action_set,
    discovery_disposition,
    sha256_json,
)
from backend.scripts.build_full_issue_universe_discovery import (
    _comparison,
    _final_freshness_check,
)
from scripts.validate_full_issue_universe_discovery import (
    DISCOVERY_PATH,
    DISCOVERY_SCHEMA,
    UniverseDiscoveryValidationError,
    validate_candidate_accounting,
    validate_bundle,
)

class FullIssueUniverseDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.discovery = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))

    def test_repository_discovery_bundle_validates(self) -> None:
        validated = validate_bundle()
        self.assertEqual(
            validated["authority_status"],
            "pending_human_universe_review",
        )
        self.assertIsNone(validated["universe_authority_receipt"])
        self.assertFalse(validated["synthesis_eligible"])

    def test_schema_is_closed(self) -> None:
        schema = json.loads(DISCOVERY_SCHEMA.read_text(encoding="utf-8"))
        altered = copy.deepcopy(self.discovery)
        altered["unexpected"] = True
        errors = list(Draft7Validator(schema).iter_errors(altered))
        self.assertTrue(errors)

    def test_candidate_accounting_is_exactly_once(self) -> None:
        candidates = self.discovery["candidate_recall_set"]["action_ids"]
        dispositions = [
            row["action_id"]
            for row in self.discovery["candidate_dispositions"]
        ]
        self.assertEqual(set(candidates), set(dispositions))
        self.assertEqual(len(dispositions), len(set(dispositions)))

    def test_reordering_does_not_change_identity(self) -> None:
        ids = self.discovery["candidate_recall_set"]["action_ids"]
        self.assertEqual(
            sha256_json(sorted(ids)),
            sha256_json(sorted(reversed(ids))),
        )

    def test_adding_or_removing_action_changes_identity(self) -> None:
        ids = self.discovery["candidate_recall_set"]["action_ids"]
        baseline = action_set(ids)["action_set_sha256"]
        added = action_set([*ids, "house:119:2:999"])
        removed = action_set(ids[:-1])
        self.assertNotEqual(baseline, added["action_set_sha256"])
        self.assertNotEqual(baseline, removed["action_set_sha256"])

    def test_missing_production_row_is_reconciled(self) -> None:
        production = [
            {
                "canonical_action_id": "house:119:1:1",
                "bill_type": "hr",
                "bill_number": 1,
                "chamber": "house",
                "congress": 119,
                "description": "one",
                "member_action": "yea",
                "question": "On Passage",
                "rollcall_number": 1,
                "session": 1,
                "vote_date": "2025-01-03",
            }
        ]
        official = [
            {
                "canonical_action_id": f"house:119:1:{roll}",
                "bill_ref": f"bill_119_hr_{roll}",
                "chamber": "house",
                "congress": 119,
                "description": str(roll),
                "member_action": "yea",
                "question": "On Passage",
                "rollcall_number": roll,
                "session": 1,
                "source_url": f"https://clerk.house.gov/{roll}",
                "vote_date": "2025-01-03",
            }
            for roll in (1, 2)
        ]
        comparison = _comparison(production, official, [])
        self.assertEqual(
            comparison["repository_official_only_before_cutoff"],
            ["house:119:1:2"],
        )

    def test_conflicting_vote_is_reconciled(self) -> None:
        production = [
            {
                "canonical_action_id": "house:119:1:1",
                "bill_type": "hr",
                "bill_number": 1,
                "chamber": "house",
                "congress": 119,
                "description": "one",
                "member_action": "nay",
                "question": "On Passage",
                "rollcall_number": 1,
                "session": 1,
                "vote_date": "2025-01-03",
            }
        ]
        official = [
            {
                "canonical_action_id": "house:119:1:1",
                "bill_ref": "bill_119_hr_1",
                "chamber": "house",
                "congress": 119,
                "description": "one",
                "member_action": "yea",
                "question": "On Passage",
                "rollcall_number": 1,
                "session": 1,
                "source_url": "https://clerk.house.gov/1",
                "vote_date": "2025-01-03",
            }
        ]
        comparison = _comparison(production, official, [])
        self.assertEqual(
            comparison["conflicting_vote_or_measure_state"][0]["fields"],
            ["member_action"],
        )

    def test_unresolved_source_remains_explicit(self) -> None:
        action = {
            "canonical_action_id": "house:119:1:1",
            "question": "On Passage",
            "description": "Candidate",
            "member_action": "yea",
            "bill_ref": "bill_119_hr_1",
        }
        disposition, confidence, _ = discovery_disposition(
            action,
            production_row=None,
            metadata=None,
            config={
                "boundary_review_action_ids": [],
                "official_in_scope_policy_areas": [
                    "Crime and Law Enforcement"
                ],
                "benchmark_action_ids": [],
                "subject": {"issue_id": "JUSTICE_PUBLIC_SAFETY"},
            },
        )
        self.assertEqual(disposition, "source_missing")
        self.assertEqual(confidence, "low")

    def test_duplicate_or_missing_candidate_fails_bundle_validation(self) -> None:
        altered = copy.deepcopy(self.discovery)
        altered["candidate_dispositions"].append(
            copy.deepcopy(altered["candidate_dispositions"][0])
        )
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "duplicate action IDs",
        ):
            validate_candidate_accounting(altered)

    def test_freshness_check_rejects_changed_query_result(self) -> None:
        baseline = {
            "snapshot_id": "baseline",
            "read_only_session_proof": {
                "database_name": "fixture",
                "default_read_only": "off",
                "current_schema": "public",
                "postgres_version": "PostgreSQL 17.6, fixture",
                "transaction_read_only": "on",
                "transaction_isolation": "repeatable read",
            },
            "query_audit": [
                {
                    "query_id": "transaction_begin",
                    "snapshot_started_at": "2026-07-30T00:00:00Z",
                },
                {
                    "query_id": "transaction_safety_proof",
                    "snapshot_started_at": "2026-07-30T00:00:00Z",
                },
                {"query_id": "transaction_rollback"},
            ],
            "results": {
                "complete_member_actions": [
                    {
                        "canonical_action_id": "house:119:1:1",
                        "bill_type": "hr",
                        "bill_number": 1,
                        "chamber": "house",
                        "congress": 119,
                        "description": "one",
                        "member_action": "yea",
                        "question": "On Passage",
                        "rollcall_number": 1,
                        "roll_call_created_at": "2025-01-04T00:00:00Z",
                        "session": 1,
                        "vote_date": "2025-01-03",
                        "primary_domain": "JUSTICE_PUBLIC_SAFETY",
                    }
                ],
                "member_identity": [{"bioguide_id": "F000477"}],
            },
        }
        changed = copy.deepcopy(baseline)
        changed["snapshot_id"] = "freshness"
        changed["results"]["member_identity"][0]["display_name"] = "Changed"
        with self.assertRaisesRegex(
            ValueError,
            "all_result_digests_match",
        ):
            _final_freshness_check(
                baseline,
                changed,
                baseline_snapshot_path=DISCOVERY_PATH,
                freshness_snapshot_path=DISCOVERY_PATH,
                issue_id="JUSTICE_PUBLIC_SAFETY",
                benchmark_action_ids=["house:119:1:1"],
            )


if __name__ == "__main__":
    unittest.main()
