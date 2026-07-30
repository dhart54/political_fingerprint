from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft7Validator

from backend.app.etl.universe_discovery import (
    action_set,
    discovery_disposition,
    load_congress_metadata,
    load_house_clerk_member_actions,
    sha256_json,
)
from backend.scripts.build_full_issue_universe_discovery import (
    _comparison,
    _final_freshness_check,
)
from scripts.validate_full_issue_universe_discovery import (
    COMPARISON_PATH,
    DISCOVERY_PATH,
    DISCOVERY_SCHEMA,
    REPAIR_PLAN_PATH,
    UniverseDiscoveryValidationError,
    validate_action_source_bindings,
    validate_candidate_accounting,
    validate_bundle,
    validate_source_completeness_statement,
)

class FullIssueUniverseDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.discovery = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
        cls.comparison = json.loads(
            COMPARISON_PATH.read_text(encoding="utf-8")
        )
        cls.repair_plan = json.loads(
            REPAIR_PLAN_PATH.read_text(encoding="utf-8")
        )
        source_path = (
            DISCOVERY_PATH.parents[4]
            / cls.discovery["source_inventory"]["path"]
        )
        cls.source_inventory = json.loads(
            source_path.read_text(encoding="utf-8")
        )
        cls.current_state = json.loads(
            (
                DISCOVERY_PATH.parents[4]
                / "docs/editorial/current_state_index.json"
            ).read_text(encoding="utf-8")
        )
        cls.current_state_markdown = (
            DISCOVERY_PATH.parents[4]
            / "docs/editorial/current_state_index.md"
        ).read_text(encoding="utf-8")

    @staticmethod
    def _source_binding_fixture(
        *,
        stage: str = "passage",
        source_type: str = "govinfo_bill_text",
        source_subject: str = "119:hr:1",
        text_version: str = "eh",
    ) -> tuple[dict, dict]:
        action_id = "house:119:1:1"
        meaning = {
            "source_id": "official-text",
            "source_type": source_type,
            "url": "https://www.govinfo.gov/example.xml",
            "source_content_sha256": "a" * 64,
            "source_subject": source_subject,
            "text_version": text_version,
            "evidence_role": (
                "exact_amendment_text"
                if stage == "amendment"
                else "exact_house_passage_text"
            ),
            "digest_basis": "raw_official_file_sha256",
        }
        row = {
            "action_id": action_id,
            "disposition": "proposed_in_scope_substantive",
            "exact_action_source_binding": {
                "canonical_action_id": action_id,
                "exact_measure_or_amendment_identity": (
                    "119:hamdt:1"
                    if stage == "amendment"
                    else "119:hr:1"
                ),
                "house_action_stage": stage,
                "vote_source_bindings": [
                    {
                        "source_id": "clerk:119:1:1",
                        "source_type": "house_clerk_roll_call",
                        "url": "https://clerk.house.gov/evs/2025/roll001.xml",
                        "source_content_sha256": "b" * 64,
                        "source_subject": action_id,
                        "text_version": "2025-01-03",
                        "evidence_role": (
                            "recorded_house_action_and_member_vote"
                        ),
                        "digest_basis": (
                            "canonical_clerk_action_projection_sha256"
                        ),
                    }
                ],
                "exact_action_meaning_source_bindings": [meaning],
                "boundary_review_sufficiency_state": "sufficient",
                "boundary_review_sufficiency_basis": "Exact official source.",
            },
            "source_readiness": {
                "boundary_review_source_state": "sufficient",
                "action_interpretation_source_state": "not_started",
                "episode_construction_source_state": "not_started",
                "synthesis_provenance_source_state": "not_started",
                "remaining_source_gaps": [],
                "boundary_gap_nonblocking_reason": None,
            },
        }
        return (
            {"candidate_dispositions": [row]},
            {"action_meaning_sources": [copy.deepcopy(meaning)]},
        )

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

    def test_v1_is_preserved_but_superseded_for_authority(self) -> None:
        historical = self.comparison["historical_v1"]
        self.assertEqual(
            historical["status"],
            "historical_non_authoritative_superseded_for_review",
        )
        self.assertFalse(self.comparison["authorizing"])
        self.assertIsNone(self.comparison["authority_receipt"])

    def test_every_official_action_through_roll_283_is_in_v2(self) -> None:
        ids = self.discovery["complete_member_action_snapshot"]["action_ids"]
        self.assertEqual(len(ids), 638)
        self.assertIn("house:119:2:283", ids)
        self.assertEqual(
            self.discovery["cutoff"]["boundary"]["end_date"],
            "2026-07-23",
        )

    def test_repository_official_sources_parse_deterministically(self) -> None:
        root = Path(__file__).resolve().parents[2]
        actions = load_house_clerk_member_actions(
            (
                root / "backend/data_sources/house_clerk",
                root / "backend/data_sources/house_clerk/2026",
            ),
            bioguide_id="F000477",
        )
        metadata = load_congress_metadata(
            (root / "backend/data_sources/congress/bills",)
        )
        self.assertEqual(len(actions), 577)
        self.assertIn("bill_119_hr_1", metadata)

    def test_expressive_actions_are_visible_but_never_substantive(self) -> None:
        expected = {
            "house:119:1:123",
            "house:119:1:158",
            "house:119:1:159",
            "house:119:1:179",
            "house:119:1:185",
            "house:119:2:162",
            "house:119:2:165",
        }
        rows = {
            row["action_id"]: row["disposition"]
            for row in self.discovery["candidate_dispositions"]
        }
        self.assertEqual(
            {action_id for action_id, value in rows.items()
             if value == "expressive_nonbinding_context"},
            expected,
        )
        self.assertTrue(
            expected.isdisjoint(
                self.discovery["proposed_universe_set"]["action_ids"]
            )
        )

    def test_fisa_cross_domain_membership_is_vote_invariant(self) -> None:
        config = {
            "reviewed_dispositions": {
                action_id: {
                    "disposition": "proposed_in_scope_substantive",
                    "confidence": "high",
                    "rationale": "FISA exact-action cross-domain review.",
                }
                for action_id in (
                    "house:119:2:155",
                    "house:119:2:221",
                )
            },
            "boundary_review_action_ids": [],
            "official_in_scope_policy_areas": [],
            "benchmark_action_ids": [],
            "subject": {"issue_id": "JUSTICE_PUBLIC_SAFETY"},
        }
        outcomes = set()
        for action_id in config["reviewed_dispositions"]:
            for member_action, party in (
                ("yea", "D"),
                ("nay", "R"),
            ):
                action = {
                    "canonical_action_id": action_id,
                    "question": "On Passage",
                    "description": "FISA",
                    "member_action": member_action,
                    "bill_ref": "bill_119_hr_1",
                }
                outcomes.add(
                    discovery_disposition(
                        action,
                        production_row={"party": party},
                        metadata={"policy_area": "National Security"},
                        config=config,
                    )[0]
                )
        self.assertEqual(outcomes, {"proposed_in_scope_substantive"})

    def test_reviewed_june_11_corrections_are_present(self) -> None:
        rows = {
            row["action_id"]: row["disposition"]
            for row in self.discovery["candidate_dispositions"]
        }
        expected = {
            "house:119:1:6": "proposed_in_scope_substantive",
            "house:119:1:17": "proposed_exact_action_ineligible",
            "house:119:2:40": "procedural_context",
            "house:119:2:155": "proposed_in_scope_substantive",
            "house:119:2:162": "expressive_nonbinding_context",
            "house:119:2:221": "proposed_in_scope_substantive",
        }
        self.assertEqual(
            {key: rows[key] for key in expected},
            expected,
        )

    def test_all_post_cutoff_actions_have_one_resolved_disposition(self) -> None:
        new_ids = self.comparison["new_action_ids"]
        rows = self.comparison["new_action_dispositions"]
        self.assertEqual(len(new_ids), 61)
        self.assertEqual([row["action_id"] for row in rows], new_ids)
        self.assertTrue(
            all(row["boundary_evidence_sufficient"] for row in rows)
        )
        self.assertFalse(
            {
                row["disposition"] for row in rows
            } & {
                "source_missing",
                "source_unresolved",
                "source_conflicting",
                "boundary_review_required",
            }
        )

    def test_exact_amendments_have_exact_action_sources(self) -> None:
        for row in self.comparison["new_action_dispositions"]:
            if row["action_stage"] != "amendment":
                continue
            self.assertTrue(
                any(
                    source["source_type"]
                    == "house_rules_committee_report"
                    for source in row["source_references"]
                ),
                row["action_id"],
            )

    def test_production_gaps_do_not_remove_official_actions(self) -> None:
        complete = set(
            self.discovery["complete_member_action_snapshot"]["action_ids"]
        )
        gaps = set(
            self.repair_plan["member_action_ingestion_gaps"]["action_ids"]
        )
        self.assertEqual(len(gaps), 83)
        self.assertTrue(gaps <= complete)

    def test_narrow_source_completeness_wording_is_enforced(self) -> None:
        validate_source_completeness_statement(
            self.comparison["source_completeness_statement"]
        )
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "exceeds the approved boundary",
        ):
            validate_source_completeness_statement(
                "No candidate official-source gaps remain."
            )

    def test_proposed_clerk_only_source_is_rejected(self) -> None:
        discovery, inventory = self._source_binding_fixture()
        discovery["candidate_dispositions"][0][
            "exact_action_source_binding"
        ] = None
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "Clerk-only",
        ):
            validate_action_source_bindings(discovery, inventory)

    def test_proposed_passage_exact_text_passes(self) -> None:
        discovery, inventory = self._source_binding_fixture()
        validate_action_source_bindings(discovery, inventory)

    def test_amendment_parent_only_source_is_rejected(self) -> None:
        discovery, inventory = self._source_binding_fixture(
            stage="amendment",
            source_type="congress_gov_action_record",
            source_subject="119:hr:1",
        )
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "wrong subject|parent-only",
        ):
            validate_action_source_bindings(discovery, inventory)

    def test_amendment_exact_source_passes(self) -> None:
        discovery, inventory = self._source_binding_fixture(
            stage="amendment",
            source_type="congress_gov_amendment",
            source_subject="119:hamdt:1",
        )
        validate_action_source_bindings(discovery, inventory)

    def test_wrong_action_source_is_rejected(self) -> None:
        discovery, inventory = self._source_binding_fixture()
        discovery["candidate_dispositions"][0][
            "exact_action_source_binding"
        ]["canonical_action_id"] = "house:119:1:2"
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "another action",
        ):
            validate_action_source_bindings(discovery, inventory)

    def test_wrong_text_version_is_rejected(self) -> None:
        discovery, inventory = self._source_binding_fixture(
            text_version="ih"
        )
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "wrong text version",
        ):
            validate_action_source_bindings(discovery, inventory)

    def test_substituted_source_digest_is_rejected(self) -> None:
        discovery, inventory = self._source_binding_fixture()
        inventory["action_meaning_sources"][0][
            "source_content_sha256"
        ] = "c" * 64
        with self.assertRaisesRegex(
            UniverseDiscoveryValidationError,
            "identity/digest mismatch",
        ):
            validate_action_source_bindings(discovery, inventory)

    def test_seven_corrected_actions_have_exact_bindings(self) -> None:
        expected = {
            "house:119:1:32": ("119:hamdt:5", "congress_hamdt5"),
            "house:119:2:155": ("119:s:4465", "govinfo_text_119_s4465_es"),
            "house:119:2:157": ("119:hr:2853", "govinfo_text_119_hr2853_eh"),
            "house:119:2:169": ("119:hr:6260", "govinfo_text_119_hr6260_eh"),
            "house:119:2:171": ("119:hr:5625", "govinfo_text_119_hr5625_eh"),
            "house:119:2:218": ("119:hr:8312", "govinfo_text_119_hr8312_eh"),
            "house:119:2:221": ("119:hr:9238", "govinfo_text_119_hr9238_cdh"),
        }
        rows = {
            row["action_id"]: row
            for row in self.discovery["candidate_dispositions"]
        }
        for action_id, (identity, source_id) in expected.items():
            binding = rows[action_id]["exact_action_source_binding"]
            self.assertEqual(
                binding["exact_measure_or_amendment_identity"],
                identity,
            )
            self.assertIn(
                source_id,
                {
                    source["source_id"]
                    for source in binding[
                        "exact_action_meaning_source_bindings"
                    ]
                },
            )

    def test_all_22_review_corrections_are_source_bound(self) -> None:
        corrections = [
            row
            for row in self.comparison["boundary_diff"]
            if row["change_type"] == "review_correction"
        ]
        self.assertEqual(len(corrections), 22)
        self.assertTrue(
            all(
                row["exact_source_ids"]
                and row["content_digests"]
                and row["evidence_roles"]
                and row["review_sufficiency_status"] == "sufficient"
                for row in corrections
            )
        )

    def test_stage_readiness_and_metadata_gaps_remain_distinct(self) -> None:
        rows = self.comparison["source_readiness_by_candidate"]
        self.assertTrue(
            all(
                row["boundary_review_source_state"] == "sufficient"
                and row["action_interpretation_source_state"]
                == "not_started"
                for row in rows
            )
        )
        self.assertEqual(
            self.source_inventory["stage_source_gap_summary"][
                "counts_by_disposition"
            ],
            {
                "proposed": 0,
                "expressive": 2,
                "procedural": 21,
                "ineligible": 11,
            },
        )

    def test_current_state_selects_v2_and_preserves_v1_as_history(self) -> None:
        state = self.current_state["full_record_issue_interpretation"]
        self.assertEqual(
            state["f000477_justice_119_current_universe_proposal_version"],
            2,
        )
        for selector in (
            "f000477_justice_119_authority_review_selector",
            "f000477_justice_119_interpretation_planning_selector",
            "f000477_justice_119_universe_discovery_artifact",
            "f000477_justice_119_source_inventory",
        ):
            self.assertIn("_v2.", state[selector])
            self.assertNotIn("_v1.", state[selector])
        historical = state[
            "f000477_justice_119_historical_universe_discovery_v1"
        ]
        self.assertIn("_v1.", historical["discovery"])
        self.assertFalse(historical["selectable_for_authority_review"])
        self.assertFalse(
            historical["selectable_for_interpretation_planning"]
        )

    def test_current_state_json_and_markdown_agree(self) -> None:
        state = self.current_state["full_record_issue_interpretation"]
        for value in (
            state["f000477_justice_119_complete_member_action_count"],
            state["f000477_justice_119_candidate_recall_count"],
            state["f000477_justice_119_proposed_universe_count"],
            state["f000477_justice_119_latest_official_roll"],
        ):
            self.assertIn(str(value), self.current_state_markdown)
        self.assertIn("July 23, 2026", self.current_state_markdown)
        self.assertIn("V1 remains discoverable", self.current_state_markdown)

    def test_boundary_diff_digest_recomputes(self) -> None:
        self.assertEqual(
            self.comparison["boundary_diff_sha256"],
            sha256_json(self.comparison["boundary_diff"]),
        )

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
                baseline_completion={
                    "completion_subject_sha256": "a" * 64,
                    "rollback": {"succeeded": True},
                    "connection_close": {
                        "client_closed_state_verified": True
                    },
                },
                freshness_completion={
                    "completion_subject_sha256": "b" * 64,
                    "rollback": {"succeeded": True},
                    "connection_close": {
                        "client_closed_state_verified": True
                    },
                },
            )


if __name__ == "__main__":
    unittest.main()
