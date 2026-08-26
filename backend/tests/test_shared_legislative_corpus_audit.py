from __future__ import annotations

import copy
import hashlib
import json
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_shared_legislative_corpus as audit


AUDIT_OUTPUT = ROOT / "docs/architecture/m0_shared_legislative_corpus_audit_v1.json"
PROOF_OUTPUT = ROOT / "docs/architecture/m0_two_member_reuse_proof_v1.json"
MARKDOWN_OUTPUT = ROOT / "docs/architecture/m0_shared_legislative_corpus_audit_v1.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SharedLegislativeCorpusAuditTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.proof = json.loads(PROOF_OUTPUT.read_text(encoding="utf-8"))
        self.audit = json.loads(AUDIT_OUTPUT.read_text(encoding="utf-8"))

    def test_deterministic_regeneration_matches_checked_in_artifacts(self) -> None:
        self.assertEqual(
            audit.EXPECTED_BASELINE,
            "d9e4d27b66253b20e1871d2e038f999fd212f565",
        )
        source_before = {
            str(path): sha256(ROOT / path) for path in audit.INPUT_PATHS
        }
        first_audit, first_proof, first_markdown = audit.build_reports(ROOT)
        second_audit, second_proof, second_markdown = audit.build_reports(ROOT)
        self.assertEqual(first_audit, second_audit)
        self.assertEqual(first_proof, second_proof)
        self.assertEqual(first_markdown, second_markdown)
        self.assertEqual(first_audit, self.audit)
        self.assertEqual(first_proof, self.proof)
        self.assertEqual(first_markdown, MARKDOWN_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(
            first_audit["audited_source_baseline"], audit.EXPECTED_BASELINE
        )
        self.assertEqual(
            first_proof["audited_source_baseline"], audit.EXPECTED_BASELINE
        )
        self.assertNotIn("repository_head", first_audit)
        self.assertNotIn("repository_head", first_proof)
        self.assertTrue(
            first_audit["source_baseline_binding"][
                "current_worktree_inputs_match_baseline"
            ]
        )
        source_after = {str(path): sha256(ROOT / path) for path in audit.INPUT_PATHS}
        self.assertEqual(source_before, source_after)

    def test_shared_digest_is_invariant_to_member_and_party(self) -> None:
        for row in self.proof["complete_action_index"]:
            projection = row["shared_projection"]
            baseline = audit.digest(projection)
            for member_id, party in (("MUTATED", "X"), ("F000477", "D")):
                wrapper = {
                    "member_id": member_id,
                    "party": party,
                    "shared_projection": copy.deepcopy(projection),
                }
                self.assertEqual(
                    audit.digest(wrapper["shared_projection"]), baseline
                )
            self.assertEqual(row["shared_projection_sha256"], baseline)
            for member_key in ("member_a", "member_b"):
                overlay = row[member_key]
                self.assertEqual(overlay["action_id"], row["action_id"])
                self.assertEqual(
                    overlay["shared_projection_sha256"],
                    row["shared_projection_sha256"],
                )
                self.assertEqual(
                    overlay["governed_source_identity_set"],
                    projection["governed_source_identity_set"],
                )
                self.assertEqual(
                    overlay["governed_source_identity_sha256"],
                    projection["governed_source_identity_sha256"],
                )
            self.assertFalse(audit.contains_member_field(projection))

    def test_member_action_changes_only_member_projection(self) -> None:
        differing = [
            row
            for row in self.proof["complete_action_index"]
            if row["member_a"]["official_status"]
            != row["member_b"]["official_status"]
        ]
        self.assertTrue(differing)
        for row in differing:
            self.assertEqual(
                row["shared_projection_sha256"],
                audit.digest(row["shared_projection"]),
            )
            self.assertNotEqual(
                row["member_a"]["exact_choice_effect"],
                row["member_b"]["exact_choice_effect"],
            )

    def test_present_and_not_voting_are_never_directional(self) -> None:
        self.assertEqual(audit.choice_effect("Present"), "resolved_non_directional")
        self.assertEqual(
            audit.choice_effect("Not Voting"), "resolved_non_directional"
        )
        self.assertEqual(audit.choice_effect("Yea"), "supports_exact_choice")
        self.assertEqual(audit.choice_effect("Nay"), "opposes_exact_choice")
        for row in self.proof["complete_action_index"]:
            for member_key in ("member_a", "member_b"):
                overlay = row[member_key]
                if overlay["official_status"] in {"Present", "Not Voting"}:
                    self.assertEqual(
                        overlay["exact_choice_effect"], "resolved_non_directional"
                    )
        assertion = next(
            row
            for row in self.proof["assertions"]
            if row["assertion_id"] == "present_and_not_voting_non_directional"
        )
        pilot_count = assertion["observed"]["pilot_example_count"]
        self.assertEqual(
            assertion["status"],
            "passed" if pilot_count else "not_applicable_no_pilot_example",
        )

    def test_five_layers_and_semantic_fields_are_typed(self) -> None:
        self.assertEqual(
            [row["name"] for row in self.audit["target_layer_mapping"]],
            [
                "Shared Action Core",
                "Shared Issue Mapping",
                "Member Action Projection",
                "Member Analytical Result",
                "Reviewed Presentation",
            ],
        )
        for row in self.proof["complete_action_index"]:
            projection = row["shared_projection"]
            core = projection["shared_action_core"]
            issue_mapping = projection["shared_issue_mapping"]
            self.assertIsNone(core["mechanism_class"])
            self.assertEqual(
                core["mechanism_availability"],
                "unavailable_in_legacy_accepted_projection",
            )
            self.assertNotIn("policy_trait_refs", core)
            self.assertIn("policy_trait_refs", issue_mapping)
            self.assertIn("domain_eligibility", issue_mapping)
            self.assertIn("episode_id", issue_mapping)
            clerk_sources = core["action_outcome_source_identities"]
            self.assertEqual(
                clerk_sources,
                row["member_a"]["member_action_source_identity_set"],
            )
            self.assertEqual(
                clerk_sources,
                row["member_b"]["member_action_source_identity_set"],
            )

    def test_conflicts_metrics_and_migration_counts_are_derived(self) -> None:
        conflict_rows = [
            {
                "action_id": row["action_id"],
                "accepted_meaning_source_digests": row[
                    "current_accepted_meaning_source_digests"
                ],
                "conflicting_source_identity_digests": row[
                    "conflicting_accepted_source_identity_digests"
                ],
                "classification": row["difference_classification"],
            }
            for row in self.audit["duplication_audit"]["repeated_action_details"]
            if row["difference_classification"] == "current accepted conflict"
        ]
        self.assertEqual(
            self.audit["duplication_audit"][
                "conflicting_current_meanings_same_action_source_version"
            ],
            conflict_rows,
        )
        self.assertEqual(self.audit["canonical_conflicts"], conflict_rows)
        self.assertEqual(
            audit.m0_verdict([], [{"action_id": "synthetic-conflict"}]),
            "INCOMPLETE_AUDIT",
        )
        metrics = self.proof["metrics"]
        self.assertNotIn("semantic_reuse_multiplier", metrics)
        self.assertNotIn("avoided_duplicate_authoring_instances", metrics)
        review = metrics["review_units_under_target_model"]
        self.assertEqual(review["new_or_changed_shared_meanings"], 0)
        self.assertEqual(
            review["migration_parity_shared_meanings"],
            metrics["pilot_action_count"],
        )
        self.assertEqual(review["novel_shared_issue_relationships"], 0)
        derived_member_b_regenerations = sum(
            row["member_b"]["shared_meaning_binding"]
            != "reference_existing_shared_projection"
            or row["member_b"]["shared_projection_sha256"]
            != row["shared_projection_sha256"]
            for row in self.proof["complete_action_index"]
        )
        self.assertEqual(
            metrics["member_b_meanings_regenerated"],
            derived_member_b_regenerations,
        )

    def test_no_network_or_database_access_is_required(self) -> None:
        original_socket = socket.socket
        with mock.patch("socket.socket", side_effect=AssertionError("network access")):
            generated_audit, generated_proof, _ = audit.build_reports(ROOT)
        self.assertEqual(generated_audit["verdict"], self.audit["verdict"])
        self.assertEqual(
            generated_proof["proof_subject_sha256"],
            self.proof["proof_subject_sha256"],
        )
        self.assertIsNotNone(original_socket)
        script = (ROOT / "scripts/audit_shared_legislative_corpus.py").read_text(
            encoding="utf-8"
        )
        for forbidden in (
            "requests.",
            "urllib.request",
            "psycopg",
            "sqlalchemy",
            "supabase",
        ):
            self.assertNotIn(forbidden, script)

    def test_assertions_and_metrics_reconcile_to_complete_index(self) -> None:
        rows = self.proof["complete_action_index"]
        metrics = self.proof["metrics"]
        self.assertEqual(len(rows), metrics["pilot_action_count"])
        self.assertEqual(
            sum(
                row["member_a"]["official_status"] == row["member_b"]["official_status"]
                for row in rows
                if row["member_a"]["official_status"] in {"Yea", "Nay"}
                and row["member_b"]["official_status"] in {"Yea", "Nay"}
            ),
            metrics["directional_agreement_count"],
        )
        self.assertEqual(
            sum(
                row["member_a"]["official_status"] != row["member_b"]["official_status"]
                for row in rows
                if row["member_a"]["official_status"] in {"Yea", "Nay"}
                and row["member_b"]["official_status"] in {"Yea", "Nay"}
            ),
            metrics["directional_disagreement_count"],
        )
        self.assertEqual(metrics["member_b_meanings_regenerated"], 0)
        self.assertEqual(metrics["identical_shared_digest_count"], len(rows))
        self.assertFalse(self.proof["failures"])
        self.assertTrue(
            all(
                item["status"]
                in {"passed", "not_applicable_no_pilot_example"}
                for item in self.proof["assertions"]
            )
        )
        subject = copy.deepcopy(self.proof)
        proof_digest = subject.pop("proof_subject_sha256")
        self.assertEqual(audit.digest(subject), proof_digest)

    def test_output_paths_are_bounded(self) -> None:
        with self.assertRaises(ValueError):
            audit.allowed_output(ROOT, ROOT / "unapproved-output.json")
        self.assertEqual(
            audit.allowed_output(ROOT, AUDIT_OUTPUT), AUDIT_OUTPUT.resolve()
        )


if __name__ == "__main__":
    unittest.main()
