from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from jsonschema import Draft7Validator

from backend.app.etl.full_record_action_interpretation_decisions import (
    ActionInterpretationDecisionError,
    validate_authority_record,
    validate_implementation_bundle,
)
from backend.app.etl.full_record_source_readiness import load_json, sha256_json
from backend.scripts.build_m11d_national_security_action_meaning_acceptance import (
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    build_outputs,
)


ROOT = Path(__file__).resolve().parents[2]


class FullRecordActionInterpretationDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate = load_json(CANDIDATE_PATH)
        cls.authority = load_json(AUTHORITY_PATH)
        cls.implementation = load_json(IMPLEMENTATION_PATH)
        cls.parity = load_json(PARITY_PATH)

    @staticmethod
    def _resign_decision(decision: dict) -> None:
        subject = {
            key: value
            for key, value in decision.items()
            if key != "decision_subject_sha256"
        }
        decision["decision_subject_sha256"] = sha256_json(subject)

    @staticmethod
    def _resign_authority(authority: dict) -> None:
        authority["authority_subject_sha256"] = sha256_json(authority["subject"])

    @staticmethod
    def _resign_record(record: dict) -> None:
        subject = {
            key: value
            for key, value in record.items()
            if key != "record_subject_sha256"
        }
        record["record_subject_sha256"] = sha256_json(subject)

    @staticmethod
    def _resign_implementation(implementation: dict) -> None:
        implementation["implementation_subject_sha256"] = sha256_json(
            implementation["subject"]
        )

    def _validate_authority(self, authority: dict) -> None:
        validate_authority_record(authority, candidate_artifact=self.candidate)

    def _validate_implementation(self, implementation: dict) -> None:
        validate_implementation_bundle(
            implementation,
            authority=self.authority,
            candidate_artifact=self.candidate,
        )

    def test_repository_artifacts_validate(self) -> None:
        self._validate_authority(self.authority)
        self._validate_implementation(self.implementation)

    def test_schemas_are_draft7_and_artifacts_conform(self) -> None:
        for schema_path, artifact in (
            (AUTHORITY_SCHEMA_PATH, self.authority),
            (IMPLEMENTATION_SCHEMA_PATH, self.implementation),
            (PARITY_SCHEMA_PATH, self.parity),
        ):
            schema = load_json(schema_path)
            Draft7Validator.check_schema(schema)
            self.assertEqual([], list(Draft7Validator(schema).iter_errors(artifact)))

    def test_builder_is_deterministic(self) -> None:
        for path, content in build_outputs().items():
            self.assertEqual(path.read_bytes().replace(b"\r\n", b"\n"), content)

    def test_exact_accounting_is_82_81_1(self) -> None:
        subject = self.authority["subject"]
        self.assertEqual(82, subject["approved_universe_count"])
        self.assertEqual(81, subject["accepted_decision_count"])
        self.assertEqual(1, subject["source_blocked_count"])
        self.assertEqual(
            ["house:119:2:278"],
            [item["action_id"] for item in subject["source_blocked_actions"]],
        )

    def test_missing_authority_decision_fails_closed(self) -> None:
        authority = deepcopy(self.authority)
        authority["subject"]["decisions"].pop()
        authority["subject"]["accepted_decision_count"] = 80
        authority["subject"]["decision_accounting"] = {
            "accept_candidate_as_written": 80
        }
        self._resign_authority(authority)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "decision count/uniqueness"
        ):
            self._validate_authority(authority)

    def test_authority_cannot_rewrite_accepted_meaning(self) -> None:
        authority = deepcopy(self.authority)
        decision = authority["subject"]["decisions"][0]
        decision["accepted_exact_action_meaning"] += " Unsupported revision."
        self._resign_decision(decision)
        self._resign_authority(authority)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "differs from accepted candidate"
        ):
            self._validate_authority(authority)

    def test_authority_cannot_flip_position_effect(self) -> None:
        authority = deepcopy(self.authority)
        decision = authority["subject"]["decisions"][0]
        decision["accepted_exact_choice_position_effect"] = (
            "opposes_exact_choice"
            if decision["accepted_exact_choice_position_effect"]
            == "supports_exact_choice"
            else "supports_exact_choice"
        )
        self._resign_decision(decision)
        self._resign_authority(authority)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "differs from accepted candidate"
        ):
            self._validate_authority(authority)

    def test_authority_cannot_drop_limitation(self) -> None:
        authority = deepcopy(self.authority)
        decision = next(
            item
            for item in authority["subject"]["decisions"]
            if item["accepted_limitations"]
        )
        decision["accepted_limitations"].pop()
        self._resign_decision(decision)
        self._resign_authority(authority)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "differs from accepted candidate"
        ):
            self._validate_authority(authority)

    def test_source_blocked_action_cannot_enter_authority(self) -> None:
        authority = deepcopy(self.authority)
        blocked = authority["subject"]["source_blocked_actions"][0]
        blocked["accepted_for_interpretation"] = True
        self._resign_authority(authority)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "blocked action entered authority"
        ):
            self._validate_authority(authority)

    def test_authority_cannot_enable_downstream_stage(self) -> None:
        authority = deepcopy(self.authority)
        authority["subject"]["downstream_authorizations"][
            "policy_episode_construction"
        ] = True
        self._resign_authority(authority)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "crosses downstream boundary"
        ):
            self._validate_authority(authority)

    def test_implementation_cannot_diverge_from_authority(self) -> None:
        implementation = deepcopy(self.implementation)
        record = implementation["subject"]["implementation_records"][0]
        record["accepted_exact_action_meaning"] += " Unsupported implementation."
        self._resign_record(record)
        self._resign_implementation(implementation)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "differs from authority"
        ):
            self._validate_implementation(implementation)

    def test_internal_canonical_state_cannot_become_semantic_acceptance(self) -> None:
        implementation = deepcopy(self.implementation)
        implementation["subject"]["canonical_semantic_acceptance"] = True
        self._resign_implementation(implementation)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "crosses downstream boundary"
        ):
            self._validate_implementation(implementation)

    def test_detailed_meaning_remains_internal_presentation_input(self) -> None:
        implementation = deepcopy(self.implementation)
        record = implementation["subject"]["implementation_records"][0]
        record["presentation_state"] = "default_public_wording"
        self._resign_record(record)
        self._resign_implementation(implementation)
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "differs from authority"
        ):
            self._validate_implementation(implementation)


if __name__ == "__main__":
    unittest.main()
