"""Adversarial tests for the detached M3A-R2 V3 candidate bundle."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from action_interpretation_candidate_v3_data import FINAL_DEFINITIONS  # noqa: E402
from build_action_interpretation_candidate_review_v3 import (  # noqa: E402
    BATCH_ID,
    OUTPUT_ROOT,
    PACKET_ROOT,
)
from validate_action_interpretation_candidate_review_v3 import (  # noqa: E402
    CandidateReviewV3ValidationError,
    validate,
    validate_parity,
    validate_values,
)


ARTIFACT_NAMES = (
    "revision_directive.json",
    "review_contracts.json",
    "related_action_lineage_map.json",
    "evidence_maps.json",
    "expected_provision_inventories.json",
    "initial_candidate_batch.json",
    "source_first_coverage_reviews.json",
    "related_action_differential_reviews.json",
    "cross_field_consistency_reviews.json",
    "scope_neutrality_reviews.json",
    "bounded_correction_diff.json",
    "candidate_batch.json",
    "benchmark_comparison.json",
    "sample_manifest.json",
    "human_decision_template.json",
    "parity_manifest.json",
)


def _artifacts() -> dict[str, dict[str, object]]:
    return {
        name: json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))
        for name in ARTIFACT_NAMES
    }


def _candidate(
    artifacts: dict[str, dict[str, object]], action_id: str
) -> dict[str, object]:
    return next(
        row
        for row in artifacts["candidate_batch.json"]["final_candidates"]
        if row["action_id"] == action_id
    )


class ActionInterpretationCandidateReviewV3Tests(unittest.TestCase):
    def test_complete_bundle_validates(self) -> None:
        result = validate()
        self.assertEqual(result["action_count"], 37)
        self.assertEqual(result["batch_id"], BATCH_ID)
        self.assertEqual(result["parity_state"], "pass")

    def test_primary_worker_packets_are_blind_and_complete(self) -> None:
        packets = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in PACKET_ROOT.glob("*.json")
        ]
        self.assertEqual({row["action_id"] for row in packets}, set(FINAL_DEFINITIONS))
        for packet in packets:
            self.assertNotIn("member_party", packet)
            self.assertNotIn("benchmark_interpretation", packet)
            self.assertNotIn("other_action_candidates", packet)
            self.assertIn(
                "accepted_benchmark_interpretations", packet["worker_input_forbidden"]
            )

    def test_source_first_inventory_is_candidate_blind(self) -> None:
        artifacts = _artifacts()
        inventories = artifacts["expected_provision_inventories.json"]
        self.assertTrue(inventories["stage_1_candidate_inaccessible"])
        for row in inventories["inventories"]:
            self.assertTrue(row["candidate_inaccessible_during_inventory_derivation"])
            ids = [
                item.get("expected_provision_id") or item.get("expected_limit_id")
                for item in [
                    *row["expected_provisions"],
                    *row["expected_limits_and_exceptions"],
                ]
            ]
            self.assertTrue(all(item_id.startswith("expected-") for item_id in ids))

    def test_candidate_visible_inventory_is_rejected(self) -> None:
        artifacts = _artifacts()
        artifacts["expected_provision_inventories.json"]["inventories"][0][
            "candidate_inaccessible_during_inventory_derivation"
        ] = False
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "candidate-visible inventory"
        ):
            validate_values(artifacts)

    def test_candidate_authored_inventory_id_is_rejected(self) -> None:
        artifacts = _artifacts()
        item = artifacts["expected_provision_inventories.json"]["inventories"][0][
            "expected_provisions"
        ][0]
        item["expected_provision_id"] = "p1"
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "candidate IDs define inventory"
        ):
            validate_values(artifacts)

    def test_s5_exact_version_regression(self) -> None:
        artifacts = _artifacts()
        candidate = _candidate(artifacts, "house:119:1:23")
        text = candidate["proposed_exact_action_meaning"].casefold()
        self.assertIn("assault of a law-enforcement officer", text)
        self.assertIn("death or serious bodily injury", text)
        candidate["proposed_exact_action_meaning"] = candidate[
            "proposed_exact_action_meaning"
        ].replace("assault of a law-enforcement officer", "assault")
        candidate["material_provisions"][0]["wording"] = (
            "Require detention for burglary, theft, larceny, or shoplifting."
        )
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "S.5 omits exact trigger"
        ):
            validate_values(artifacts)

    def test_hr29_does_not_absorb_senate_only_triggers(self) -> None:
        artifacts = _artifacts()
        candidate = _candidate(artifacts, "house:119:1:6")
        candidate["proposed_exact_action_meaning"] += (
            " It includes assault of a law-enforcement officer."
        )
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "H.R.29 absorbed"
        ):
            validate_values(artifacts)

    def test_related_action_differentials_identify_shared_mechanisms(self) -> None:
        artifacts = _artifacts()
        reviews = {
            row["group_id"]: row
            for row in artifacts["related_action_differential_reviews.json"]["reviews"]
        }
        self.assertEqual(
            len(reviews["laken-riley-house-senate-versions"]["shared_provisions"]),
            2,
        )
        self.assertEqual(
            len(reviews["halt-fentanyl-house-senate-versions"]["shared_provisions"]),
            3,
        )
        self.assertEqual(
            len(reviews["fisa-short-term-extensions"]["shared_provisions"]),
            1,
        )
        self.assertEqual(
            reviews["dc-criminal-justice-and-policing"]["shared_provisions"], []
        )

    def test_hr1156_four_program_regression(self) -> None:
        artifacts = _artifacts()
        candidate = _candidate(artifacts, "house:119:1:68")
        for field in ("proposed_exact_action_meaning",):
            candidate[field] = candidate[field].replace(
                "four pandemic", "three pandemic"
            )
        candidate["claim_components"][0]["wording"] = candidate["claim_components"][0][
            "wording"
        ].replace("four pandemic", "three pandemic")
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "named-count regression"
        ):
            validate_values(artifacts)

    def test_quantities_dates_amounts_thresholds_and_penalties_pass(self) -> None:
        artifacts = _artifacts()
        reviews = artifacts["cross_field_consistency_reviews.json"]["reviews"]
        self.assertTrue(
            all(
                not row["final_checks"][
                    "missing_quantities_dates_amounts_thresholds_or_penalties"
                ]
                for row in reviews
            )
        )
        self.assertTrue(all(row["final_checks"]["result"] == "pass" for row in reviews))

    def test_unbound_expected_item_is_rejected(self) -> None:
        artifacts = _artifacts()
        artifacts["expected_provision_inventories.json"]["inventories"][0][
            "expected_provisions"
        ][0]["locator"] = ""
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "unbound expected item"
        ):
            validate_values(artifacts)

    def test_proposed_candidate_cannot_retain_major_consistency_finding(self) -> None:
        artifacts = _artifacts()
        artifacts["cross_field_consistency_reviews.json"]["reviews"][0][
            "remaining_severity_after_correction"
        ] = "major"
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "retains consistency major"
        ):
            validate_values(artifacts)

    def test_roll155_source_conflict_and_ambiguity_are_preserved(self) -> None:
        artifacts = _artifacts()
        candidate = _candidate(artifacts, "house:119:2:155")
        candidate["source_identity_reconciliation"]["dublin_core_title"] = (
            "119 S4465 ES"
        )
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "roll 155 source conflict"
        ):
            validate_values(artifacts)

    def test_roll278_no_safe_abstention_is_preserved(self) -> None:
        artifacts = _artifacts()
        candidate = _candidate(artifacts, "house:119:2:278")
        candidate["status"] = "proposed"
        candidate["proposed_exact_action_meaning"] = (
            "The House choice was whether to pass an incomplete package."
        )
        with self.assertRaises(CandidateReviewV3ValidationError):
            validate_values(artifacts)

    def test_benchmark_cannot_precede_freeze(self) -> None:
        artifacts = _artifacts()
        artifacts["candidate_batch.json"]["freeze_precedes_benchmark_access"] = False
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "not frozen before benchmark"
        ):
            validate_values(artifacts)

    def test_sampling_is_deterministic_and_benchmark_blind(self) -> None:
        artifacts = _artifacts()
        sample = artifacts["sample_manifest.json"]
        self.assertEqual(len(sample["selected_random_action_ids"]), 12)
        sample["selected_random_action_ids"] = list(
            reversed(sample["selected_random_action_ids"])
        )
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "not deterministic"
        ):
            validate_values(artifacts)

    def test_final_file_parity_detects_mutation(self) -> None:
        parity = json.loads(
            (OUTPUT_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
        )
        path = parity["canonical_artifacts"][0]["path"]
        mutated = (ROOT / path).read_bytes() + b" "
        with self.assertRaisesRegex(
            CandidateReviewV3ValidationError, "final-byte mismatch"
        ):
            validate_parity(
                parity_override=deepcopy(parity), byte_overrides={path: mutated}
            )

    def test_runtime_and_public_selectors_do_not_reference_v3(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "pass")


if __name__ == "__main__":
    unittest.main()
