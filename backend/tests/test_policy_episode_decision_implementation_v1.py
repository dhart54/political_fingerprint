from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_policy_episode_decision_implementation_v1 import (  # noqa: E402
    ACCEPTANCE_FILE_SHA256,
    ACCEPTANCE_OUTPUT,
    ACCEPTANCE_SOURCE,
    JSON_NAMES,
    OUTPUT_ROOT,
    SCHEMA_ROOT,
    digest,
)
from validate_policy_episode_decision_implementation_v1 import (  # noqa: E402
    EpisodeImplementationValidationError,
    validate,
    validate_artifacts,
    validate_final_byte_parity,
)


def artifacts() -> dict[str, dict[str, object]]:
    return {
        name: json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))
        for name in JSON_NAMES
    }


def reseal(value: dict[str, object]) -> None:
    value.pop("content_subject_sha256", None)
    value["content_subject_sha256"] = digest(value)


def implemented(
    values: dict[str, dict[str, object]], episode_id: str
) -> dict[str, object]:
    bundle = values["episode_implementation_bundle.json"]
    return next(
        row for row in bundle["implemented_episodes"] if row["episode_id"] == episode_id
    )


def accounting(
    values: dict[str, dict[str, object]], action_id: str
) -> dict[str, object]:
    bundle = values["episode_implementation_bundle.json"]
    return next(
        row for row in bundle["action_accounting"] if row["action_id"] == action_id
    )


def reseal_bundle(values: dict[str, dict[str, object]]) -> None:
    reseal(values["episode_implementation_bundle.json"])


class PolicyEpisodeDecisionImplementationTests(unittest.TestCase):
    def test_complete_implementation_bundle(self) -> None:
        self.assertEqual(validate()["status"], "pass")

    def test_imported_acceptance_exact_bytes(self) -> None:
        self.assertEqual(ACCEPTANCE_OUTPUT.read_bytes(), ACCEPTANCE_SOURCE.read_bytes())
        self.assertEqual(
            hashlib.sha256(ACCEPTANCE_OUTPUT.read_bytes()).hexdigest(),
            ACCEPTANCE_FILE_SHA256,
        )

    def test_missing_episode_rejected(self) -> None:
        values = artifacts()
        values["episode_implementation_bundle.json"]["implemented_episodes"].pop()
        reseal_bundle(values)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "missing"):
            validate_artifacts(values)

    def test_extra_episode_rejected(self) -> None:
        values = artifacts()
        extra = copy.deepcopy(
            values["episode_implementation_bundle.json"]["implemented_episodes"][0]
        )
        extra["episode_id"] = "unauthorized-extra-episode"
        reseal(extra)
        values["episode_implementation_bundle.json"]["implemented_episodes"].append(
            extra
        )
        reseal_bundle(values)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "extra"):
            validate_artifacts(values)

    def test_changed_episode_id_rejected(self) -> None:
        values = artifacts()
        row = values["episode_implementation_bundle.json"]["implemented_episodes"][0]
        row["episode_id"] = "changed-episode-id"
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "changed"):
            validate_artifacts(values)

    def test_changed_policy_question_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "retired-service-weapon-purchases")
        row["neutral_policy_question"] += " Changed."
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(
            EpisodeImplementationValidationError, "neutral_policy_question"
        ):
            validate_artifacts(values)

    def test_changed_membership_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "laken-riley-detention-enforcement")
        row["primary_action_ids"] = row["primary_action_ids"][:1]
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(
            EpisodeImplementationValidationError, "primary_action_ids"
        ):
            validate_artifacts(values)

    def test_changed_chronology_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "laken-riley-detention-enforcement")
        row["chronological_action_sequence"].reverse()
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(
            EpisodeImplementationValidationError, "chronological_action_sequence"
        ):
            validate_artifacts(values)

    def test_changed_action_role_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "halt-fentanyl-legislative-path")
        row["action_roles"][0]["action_role"] = "standalone_action"
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(
            EpisodeImplementationValidationError, "action_roles"
        ):
            validate_artifacts(values)

    def test_changed_behavior_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "halt-fentanyl-legislative-path")
        row["implemented_episode_level_behavior"] = "supports_episode_direction"
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(
            EpisodeImplementationValidationError, "implemented_episode_level_behavior"
        ):
            validate_artifacts(values)

    def test_changed_confidence_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "laken-riley-detention-enforcement")
        row["confidence"] = "high"
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "confidence"):
            validate_artifacts(values)

    def test_laken_riley_versions_split_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "laken-riley-detention-enforcement")
        row["primary_action_ids"] = ["house:119:1:6"]
        row["chronological_action_sequence"] = row["chronological_action_sequence"][:1]
        row["action_roles"] = row["action_roles"][:1]
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_dc_juvenile_recombination_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "dc-youth-offender-sentencing")
        row["primary_action_ids"].append("house:119:1:271")
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_halt_path_flattening_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "halt-fentanyl-legislative-path")
        for role in row["action_roles"]:
            role["action_role"] = "standalone_action"
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_roll_155_primary_assignment_rejected(self) -> None:
        values = artifacts()
        row = accounting(values, "house:119:2:155")
        episode = implemented(values, "fisa-title-vii-short-term-extension")
        row["primary_accounting_state"] = "assigned_primary_episode"
        row["primary_episode_id"] = episode["episode_id"]
        row["implemented_episode_record_id"] = episode["record_id"]
        row["implemented_episode_content_subject_sha256"] = episode[
            "content_subject_sha256"
        ]
        row["counts_toward_episode_behavior"] = True
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_roll_155_behavior_count_rejected(self) -> None:
        values = artifacts()
        row = accounting(values, "house:119:2:155")
        row["counts_toward_episode_behavior"] = True
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_roll_278_assignment_rejected(self) -> None:
        values = artifacts()
        row = accounting(values, "house:119:2:278")
        row["primary_accounting_state"] = "assigned_primary_episode"
        row["primary_episode_id"] = "military-speed-camera-funding-ban"
        row["counts_toward_episode_behavior"] = True
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_duplicate_primary_action_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "retired-service-weapon-purchases")
        duplicate = copy.deepcopy(
            implemented(values, "law-enforcement-concealed-carry-expansion")[
                "chronological_action_sequence"
            ][0]
        )
        row["primary_action_ids"].append(duplicate["action_id"])
        row["chronological_action_sequence"].append(duplicate)
        row["action_roles"].append(
            {
                "action_id": duplicate["action_id"],
                "action_role": duplicate["action_role"],
            }
        )
        reseal(row)
        reseal_bundle(values)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values)

    def test_removed_risk_rejected(self) -> None:
        values = artifacts()
        risk = values["launch_review_risk_register.json"]
        risk["entries"].pop()
        reseal(risk)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "risk"):
            validate_artifacts(values)

    def test_fisa_risk_false_resolution_rejected(self) -> None:
        values = artifacts()
        risk = values["launch_review_risk_register.json"]
        risk["entries"][-1]["current_status"] = "resolved"
        reseal(risk["entries"][-1])
        reseal(risk)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "risk"):
            validate_artifacts(values)

    def test_calibration_risk_item_rejected(self) -> None:
        values = artifacts()
        calibration = values["episode_calibration_population.json"]
        calibration["eligible_items"][0]["episode_id"] = (
            "fisa-title-vii-short-term-extension"
        )
        reseal(calibration["eligible_items"][0])
        reseal(calibration)
        with self.assertRaisesRegex(
            EpisodeImplementationValidationError, "calibration"
        ):
            validate_artifacts(values)

    def test_calibration_sample_selection_rejected(self) -> None:
        values = artifacts()
        calibration = values["episode_calibration_population.json"]
        calibration["sample_selected"] = True
        calibration["selected_sample"] = [
            calibration["eligible_items"][0]["episode_id"]
        ]
        reseal(calibration)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "sample"):
            validate_artifacts(values)

    def test_recommendation_substituted_for_acceptance_rejected(self) -> None:
        values = artifacts()
        acceptance = json.loads(ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
        acceptance["decision"]["episode_decisions"][0]["decision"] = "recommend_accept"
        reseal(acceptance)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values, acceptance_override=acceptance)

    def test_false_user_signature_rejected(self) -> None:
        values = artifacts()
        acceptance = json.loads(ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
        acceptance["decision"]["not_user_signature"] = False
        reseal(acceptance)
        with self.assertRaises(EpisodeImplementationValidationError):
            validate_artifacts(values, acceptance_override=acceptance)

    def test_canonical_or_public_state_rejected(self) -> None:
        values = artifacts()
        row = implemented(values, "officer-safety-data-reporting")
        row["canonical"] = True
        reseal(row)
        reseal_bundle(values)
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "authority"):
            validate_artifacts(values)

    def test_closed_schema_rejects_unknown_implementation_field(self) -> None:
        value = artifacts()["episode_implementation_bundle.json"]
        schema = json.loads(
            (SCHEMA_ROOT / "episode_implementation_bundle_v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        value["implemented_episodes"][0]["unauthorized_field"] = True
        errors = list(Draft7Validator(schema).iter_errors(value))
        self.assertTrue(errors)

    def test_stale_parity_hash_rejected(self) -> None:
        parity = json.loads(
            (OUTPUT_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
        )
        target = parity["referenced_artifacts"][0]["path"]
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "stale"):
            validate_final_byte_parity(byte_overrides={target: b"changed"})

    def test_stale_markdown_rejected(self) -> None:
        with self.assertRaisesRegex(EpisodeImplementationValidationError, "Markdown"):
            validate_final_byte_parity(markdown_override="# stale\n")


if __name__ == "__main__":
    unittest.main()
