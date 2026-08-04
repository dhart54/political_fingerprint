"""Adversarial tests for M4A policy-episode candidate construction."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_policy_episode_candidates_v1 import (  # noqa: E402
    ACCEPTANCE_FILE_SHA256,
    ACCEPTANCE_OUTPUT,
    JSON_NAMES,
    OUTPUT_ROOT,
    SCHEMA_ROOT,
    digest,
    file_digest,
)
from validate_policy_episode_candidates_v1 import (  # noqa: E402
    EpisodeCandidateValidationError,
    validate,
    validate_artifacts,
    validate_parity,
)


def artifacts() -> dict[str, dict[str, object]]:
    return {
        name: json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))
        for name in JSON_NAMES
    }


def episode(values: dict[str, dict[str, object]], episode_id: str) -> dict[str, object]:
    return next(
        row
        for row in values["frozen_episode_candidate_batch.json"]["episodes"]
        if row["episode_id"] == episode_id
    )


def reseal(value: dict[str, object]) -> None:
    value.pop("content_subject_sha256", None)
    value["content_subject_sha256"] = digest(value)


def reseal_final(values: dict[str, dict[str, object]]) -> None:
    reseal(values["frozen_episode_candidate_batch.json"])


class PolicyEpisodeCandidateTests(unittest.TestCase):
    def test_complete_candidate_bundle(self) -> None:
        result = validate()
        self.assertEqual(result["episode_count"], 32)
        self.assertEqual(result["accounting"]["assigned_primary_episode"], 35)

    def test_imported_acceptance_exact_bytes(self) -> None:
        self.assertEqual(file_digest(ACCEPTANCE_OUTPUT), ACCEPTANCE_FILE_SHA256)

    def test_missing_action_accounting_rejected(self) -> None:
        values = artifacts()
        values["frozen_episode_candidate_batch.json"]["action_accounting"].pop()
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "37-action accounting"
        ):
            validate_artifacts(values)

    def test_duplicate_primary_membership_rejected(self) -> None:
        values = artifacts()
        target = episode(values, "born-alive-care-and-remedies")
        source = episode(values, "laken-riley-detention-enforcement")[
            "chronological_action_sequence"
        ][0]
        target["primary_action_ids"].insert(0, source["action_id"])
        target["chronological_action_sequence"].insert(0, deepcopy(source))
        reseal(target)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "duplicate primary"
        ):
            validate_artifacts(values)

    def test_lineage_episode_conclusion_rejected(self) -> None:
        values = artifacts()
        values["action_lineage_map.json"]["neutral_no_episode_conclusions"] = False
        reseal(values["action_lineage_map.json"])
        with self.assertRaisesRegex(EpisodeCandidateValidationError, "lineage map"):
            validate_artifacts(values)

    def test_overgrouped_dc_mechanisms_rejected(self) -> None:
        values = artifacts()
        first = episode(values, "dc-youth-offender-sentencing")
        second = episode(values, "dc-juvenile-court-transfer-age")
        first["primary_action_ids"] += second["primary_action_ids"]
        first["chronological_action_sequence"] += second[
            "chronological_action_sequence"
        ]
        reseal(first)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "duplicate primary"
        ):
            validate_artifacts(values)

    def test_halt_undergrouping_rejected(self) -> None:
        values = artifacts()
        halt = episode(values, "halt-fentanyl-legislative-path")
        halt["primary_action_ids"].pop()
        halt["chronological_action_sequence"].pop()
        reseal(halt)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "assigned primary"
        ):
            validate_artifacts(values)

    def test_chronology_reordering_rejected(self) -> None:
        values = artifacts()
        halt = episode(values, "halt-fentanyl-legislative-path")
        halt["primary_action_ids"].reverse()
        halt["chronological_action_sequence"].reverse()
        reseal(halt)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "chronological order"
        ):
            validate_artifacts(values)

    def test_amendment_role_rejected(self) -> None:
        values = artifacts()
        halt = episode(values, "halt-fentanyl-legislative-path")
        halt["chronological_action_sequence"][0]["action_role"] = "standalone_action"
        reseal(halt)
        reseal_final(values)
        with self.assertRaisesRegex(EpisodeCandidateValidationError, "amendment role"):
            validate_artifacts(values)

    def test_behavior_drift_rejected(self) -> None:
        values = artifacts()
        episode(values, "halt-fentanyl-legislative-path")[
            "candidate_episode_level_behavior"
        ] = "supports_episode_direction"
        reseal(episode(values, "halt-fentanyl-legislative-path"))
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "behavior derivation"
        ):
            validate_artifacts(values)

    def test_roll_128_ambiguity_rejected(self) -> None:
        values = artifacts()
        episode(values, "law-enforcement-concealed-carry-expansion")[
            "candidate_episode_level_behavior"
        ] = "opposes_episode_direction"
        reseal(episode(values, "law-enforcement-concealed-carry-expansion"))
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "behavior derivation"
        ):
            validate_artifacts(values)

    def test_roll_155_primary_assignment_rejected(self) -> None:
        values = artifacts()
        row = next(
            row
            for row in values["frozen_episode_candidate_batch.json"][
                "action_accounting"
            ]
            if row["action_id"] == "house:119:2:155"
        )
        row["primary_accounting_state"] = "assigned_primary_episode"
        row["primary_episode_id"] = "fisa-title-vii-short-term-extension"
        reseal(row)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "assigned primary"
        ):
            validate_artifacts(values)

    def test_roll_278_episode_assignment_rejected(self) -> None:
        values = artifacts()
        row = next(
            row
            for row in values["frozen_episode_candidate_batch.json"][
                "action_accounting"
            ]
            if row["action_id"] == "house:119:2:278"
        )
        row["primary_accounting_state"] = "assigned_primary_episode"
        row["primary_episode_id"] = "military-chaplain-protections"
        reseal(row)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "assigned primary"
        ):
            validate_artifacts(values)

    def test_benchmark_exposure_before_freeze_rejected(self) -> None:
        values = artifacts()
        values["initial_episode_candidate_batch.json"][
            "benchmark_evidence_used_in_construction"
        ] = True
        reseal(values["initial_episode_candidate_batch.json"])
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "benchmark exposed"
        ):
            validate_artifacts(values)

    def test_nondeterministic_sample_rejected(self) -> None:
        values = artifacts()
        values["sample_challenge_manifest.json"]["episode_review_sample_ids"].reverse()
        reseal(values["sample_challenge_manifest.json"])
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "deterministic sample"
        ):
            validate_artifacts(values)

    def test_prior_risk_mutation_rejected(self) -> None:
        values = artifacts()
        values["launch_review_risk_register.json"]["entries"][0]["current_status"] = (
            "held_for_launch_review"
        )
        reseal(values["launch_review_risk_register.json"]["entries"][0])
        reseal(values["launch_review_risk_register.json"])
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "prior launch-risk"
        ):
            validate_artifacts(values)

    def test_calibration_sample_selection_rejected(self) -> None:
        values = artifacts()
        values["episode_calibration_population.json"]["sample_selected"] = True
        reseal(values["episode_calibration_population.json"])
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "selected prematurely"
        ):
            validate_artifacts(values)

    def test_filled_delegated_decision_rejected(self) -> None:
        values = artifacts()
        values["delegated_authority_decision_template.json"]["decisions"][0][
            "selected_decision"
        ] = "delegated_authority_accepts_episode_candidate"
        reseal(values["delegated_authority_decision_template.json"]["decisions"][0])
        reseal(values["delegated_authority_decision_template.json"])
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "represented as delegated"
        ):
            validate_artifacts(values)

    def test_accepted_or_canonical_episode_rejected(self) -> None:
        values = artifacts()
        target = episode(values, "born-alive-care-and-remedies")
        target["accepted"] = True
        reseal(target)
        reseal_final(values)
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "candidate boundary"
        ):
            validate_artifacts(values)

    def test_closed_schema_rejects_unknown_episode_field(self) -> None:
        value = artifacts()["frozen_episode_candidate_batch.json"]
        value["episodes"][0]["invented_authority"] = True
        schema = json.loads(
            (SCHEMA_ROOT / "frozen_episode_candidate_batch_v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        errors = list(Draft7Validator(schema).iter_errors(value))
        self.assertTrue(errors)
        self.assertTrue(
            any("Additional properties" in error.message for error in errors)
        )

    def test_stale_parity_hash_rejected(self) -> None:
        parity = json.loads(
            (OUTPUT_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
        )
        item = parity["referenced_artifacts"][0]
        with self.assertRaisesRegex(
            EpisodeCandidateValidationError, "stale final-file"
        ):
            validate_parity(
                byte_overrides={item["path"]: (ROOT / item["path"]).read_bytes() + b" "}
            )

    def test_stale_markdown_rejected(self) -> None:
        with self.assertRaisesRegex(EpisodeCandidateValidationError, "Markdown"):
            validate_parity(markdown_override="# stale")


if __name__ == "__main__":
    unittest.main()
