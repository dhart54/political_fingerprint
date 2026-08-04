"""Adversarial M3A-R3 V4 material-detail closure tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from action_interpretation_candidate_v4_data import (  # noqa: E402
    FINAL_DEFINITIONS,
    TARGETED_CORRECTIONS,
)
from build_action_interpretation_candidate_review_v4 import (  # noqa: E402
    BATCH_ID,
    OUTPUT_ROOT,
    PACKET_ROOT,
)
from validate_action_interpretation_candidate_review_v4 import (  # noqa: E402
    CandidateReviewV4ValidationError,
    validate,
    validate_parity,
    validate_values,
)


NAMES = (
    "candidate_batch.json",
    "material_scope_ledgers.json",
    "material_scope_closure_reviews.json",
    "quantitative_enumeration_closure_reviews.json",
    "textual_amendment_closure_reviews.json",
    "cross_field_consistency_reviews.json",
    "bounded_correction_diff.json",
)


def artifacts() -> dict[str, dict[str, object]]:
    return {
        name: json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))
        for name in NAMES
    }


def candidate(
    values: dict[str, dict[str, object]], action_id: str
) -> dict[str, object]:
    return next(
        row
        for row in values["candidate_batch.json"]["final_candidates"]
        if row["action_id"] == action_id
    )


class CandidateReviewV4Tests(unittest.TestCase):
    def test_complete_bundle(self) -> None:
        result = validate()
        self.assertEqual(result["batch_id"], BATCH_ID)
        self.assertEqual(result["action_count"], 37)

    def test_worker_blindness_and_membership(self) -> None:
        packets = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in PACKET_ROOT.glob("*.json")
        ]
        self.assertEqual({row["action_id"] for row in packets}, set(FINAL_DEFINITIONS))
        for row in packets:
            self.assertIn("v3_action_candidates", row["worker_input_forbidden"])
            self.assertNotIn(
                "member_party",
                {key.casefold() for key in row if key != "worker_input_forbidden"},
            )

    def test_candidate_blind_material_scope_ledgers(self) -> None:
        values = artifacts()
        ledger = values["material_scope_ledgers.json"]
        self.assertTrue(ledger["candidate_blind"])
        self.assertTrue(
            all(
                row["candidate_inaccessible_during_derivation"]
                for row in ledger["ledgers"]
            )
        )

    def test_candidate_visible_ledger_rejected(self) -> None:
        values = artifacts()
        values["material_scope_ledgers.json"]["candidate_blind"] = False
        with self.assertRaisesRegex(
            CandidateReviewV4ValidationError, "candidate-visible"
        ):
            validate_values(values)

    def test_every_item_has_one_disposition(self) -> None:
        values = artifacts()
        review = values["material_scope_closure_reviews.json"]["reviews"][0]
        review["item_dispositions"].pop()
        with self.assertRaisesRegex(
            CandidateReviewV4ValidationError, "incomplete item disposition"
        ):
            validate_values(values)

    def test_proposed_candidate_cannot_have_missing_blocker(self) -> None:
        values = artifacts()
        review = next(
            row
            for row in values["material_scope_closure_reviews.json"]["reviews"]
            if row["action_id"] == "house:119:1:6"
        )
        review["item_dispositions"][0]["final_disposition"] = (
            "missing_blocking_candidate"
        )
        with self.assertRaisesRegex(
            CandidateReviewV4ValidationError, "proposed candidate missing item"
        ):
            validate_values(values)

    def test_hr2478_definition_and_duration(self) -> None:
        values = artifacts()
        row = candidate(values, "house:119:2:227")
        row["proposed_exact_action_meaning"] = row[
            "proposed_exact_action_meaning"
        ].replace("age 65 or older", "older adults")
        with self.assertRaisesRegex(CandidateReviewV4ValidationError, "H.R.2478 omits"):
            validate_values(values)

    def test_hr2853_threshold(self) -> None:
        values = artifacts()
        row = candidate(values, "house:119:2:157")
        row["proposed_exact_action_meaning"] = row[
            "proposed_exact_action_meaning"
        ].replace("$5,000", "a threshold")
        row["limitations"] = [
            text.replace("$5,000", "a threshold") for text in row["limitations"]
        ]
        with self.assertRaisesRegex(
            CandidateReviewV4ValidationError, "H.R.2853 threshold"
        ):
            validate_values(values)

    def test_hr35_penalty_ranges(self) -> None:
        values = artifacts()
        row = candidate(values, "house:119:1:42")
        row["proposed_exact_action_meaning"] = row[
            "proposed_exact_action_meaning"
        ].replace("five to 20 years", "an enhanced range")
        row["limitations"] = [
            text.replace("five-to-20 years", "an enhanced range")
            for text in row["limitations"]
        ]
        with self.assertRaisesRegex(CandidateReviewV4ValidationError, "H.R.35 penalty"):
            validate_values(values)

    def test_hr2243_textual_amendment_and_confidence(self) -> None:
        values = artifacts()
        row = candidate(values, "house:119:1:128")
        row["proposed_exact_action_meaning"] = row[
            "proposed_exact_action_meaning"
        ].replace("any magazine and", "a phrase")
        row["limitations"] = [
            text.replace("any magazine and", "a phrase") for text in row["limitations"]
        ]
        with self.assertRaisesRegex(
            CandidateReviewV4ValidationError, "H.R.2243 amendment"
        ):
            validate_values(values)

    def test_all_quantitative_checks_close(self) -> None:
        values = artifacts()
        checks = [
            check
            for review in values["quantitative_enumeration_closure_reviews.json"][
                "reviews"
            ]
            for check in review["checks"]
        ]
        self.assertTrue(checks)
        self.assertTrue(all(check["severity"] == "none" for check in checks))

    def test_textual_amendment_is_unresolved_and_disclosed(self) -> None:
        values = artifacts()
        review = next(
            row
            for row in values["textual_amendment_closure_reviews.json"]["reviews"]
            if row["action_id"] == "house:119:1:128"
        )
        self.assertEqual(
            review["amendments"][0]["candidate_disposition"], "unresolved_and_disclosed"
        )
        self.assertEqual(review["amendments"][0]["context_sufficiency"], "insufficient")

    def test_single_global_correction_cycle(self) -> None:
        values = artifacts()
        correction = values["bounded_correction_diff.json"]
        self.assertEqual(correction["correction_cycle_count"], 1)
        self.assertEqual(
            {row["action_id"] for row in correction["corrections"]},
            TARGETED_CORRECTIONS,
        )

    def test_roll155_and_roll278_preserved(self) -> None:
        values = artifacts()
        self.assertEqual(candidate(values, "house:119:2:155")["status"], "ambiguous")
        self.assertEqual(
            candidate(values, "house:119:2:278")["status"], "no_safe_candidate"
        )

    def test_parity_detects_final_byte_mutation(self) -> None:
        parity = json.loads(
            (OUTPUT_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
        )
        path = parity["canonical_artifacts"][0]["path"]
        with self.assertRaisesRegex(
            CandidateReviewV4ValidationError, "final-byte mismatch"
        ):
            validate_parity(byte_overrides={path: (ROOT / path).read_bytes() + b" "})


if __name__ == "__main__":
    unittest.main()
