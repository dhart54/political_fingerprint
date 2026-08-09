from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_cross_issue_full_record_expansion",
    ROOT / "backend/scripts/build_cross_issue_full_record_expansion.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def action(
    *, question: str, description: str = "National defense", roll: int = 10
) -> dict:
    return {
        "action_id": f"house:119:1:{roll}",
        "session": 1,
        "roll": roll,
        "date": "2025-01-10",
        "bill_ref": "bill_119_hr_100",
        "question": question,
        "description": description,
        "member_action": "yea",
        "vote_source": {
            "source_id": f"clerk:119:1:{roll}",
            "source_type": "house_clerk_roll_call_xml",
            "url": f"https://clerk.house.gov/evs/2025/roll{roll:03d}.xml",
            "sha256": "a" * 64,
        },
    }


METADATA = {
    "title": "National Defense Authorization Act",
    "policy_area": "Armed Forces and National Security",
    "url": "https://www.congress.gov/bill/119th-congress/house-bill/100",
    "sha256": "b" * 64,
}


class CrossIssueExpansionTests(unittest.TestCase):
    def test_exact_amendment_binding_owns_child_membership(self) -> None:
        amendment = {
            "identity": "119:hamdt:20",
            "description": "Requires a report on military readiness",
            "purpose": "National defense readiness reporting",
            "latest_action": "On agreeing to the amendment Roll No. 10",
            "url": "https://api.congress.gov/v3/amendment/119/hamdt/20",
            "sha256": "c" * 64,
            "source_id": "congress-amendment-index:bill_119_hr_100",
        }
        record = MODULE.build_candidate_record(
            "NATIONAL_SECURITY_FOREIGN",
            action(question="On Agreeing to the Amendment"),
            METADATA,
            None,
            amendment,
        )
        self.assertEqual(record["disposition"], "proposed_in_scope_substantive")
        self.assertEqual(
            record["exact_action_source_binding"]["exact_identity"], "119:hamdt:20"
        )
        self.assertEqual(
            record["exact_action_source_binding"]["canonical_action_id"],
            "house:119:1:10",
        )

    def test_parent_measure_cannot_resolve_unbound_child_action(self) -> None:
        record = MODULE.build_candidate_record(
            "NATIONAL_SECURITY_FOREIGN",
            action(question="On Agreeing to the Amendment"),
            METADATA,
            {"primary_domain": "NATIONAL_SECURITY_FOREIGN", "score_breakdown": {}},
            None,
        )
        self.assertEqual(record["disposition"], "boundary_review_required")
        self.assertEqual(
            record["unresolved_reason"], "missing_exact_child_action_binding"
        )
        self.assertIsNone(record["exact_action_source_binding"])

    def test_cross_domain_exact_amendment_is_not_relabelled_from_parent(self) -> None:
        amendment = {
            "identity": "119:hamdt:21",
            "description": "Expands student loan repayment eligibility",
            "purpose": "Education assistance",
            "latest_action": "On agreeing to the amendment Roll No. 10",
            "url": "https://api.congress.gov/v3/amendment/119/hamdt/21",
            "sha256": "d" * 64,
            "source_id": "congress-amendment-index:bill_119_hr_100",
        }
        record = MODULE.build_candidate_record(
            "NATIONAL_SECURITY_FOREIGN",
            action(question="On Agreeing to the Amendment"),
            METADATA,
            None,
            amendment,
        )
        self.assertEqual(record["disposition"], "exact_action_ineligible")

    def test_procedural_and_expressive_actions_are_noncounting(self) -> None:
        procedural = MODULE.build_candidate_record(
            "NATIONAL_SECURITY_FOREIGN",
            action(question="On Ordering the Previous Question"),
            METADATA,
            None,
            None,
        )
        expressive_action = action(question="On Agreeing to the Resolution", roll=11)
        expressive_action["bill_ref"] = "bill_119_hconres_20"
        expressive = MODULE.build_candidate_record(
            "NATIONAL_SECURITY_FOREIGN",
            expressive_action,
            {**METADATA, "title": "Expressing support for the armed forces"},
            None,
            None,
        )
        self.assertEqual(procedural["disposition"], "procedural_context")
        self.assertEqual(expressive["disposition"], "expressive_nonbinding_context")
        accounting = MODULE.domain_accounting(
            "NATIONAL_SECURITY_FOREIGN", [procedural, expressive]
        )
        self.assertEqual(accounting["substantive_eligible_actions"], 0)
        self.assertEqual(accounting["procedural_context_actions"], 1)
        self.assertEqual(accounting["expressive_nonbinding_actions"], 1)


if __name__ == "__main__":
    unittest.main()
