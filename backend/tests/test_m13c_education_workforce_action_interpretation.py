from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from jsonschema import Draft7Validator

from backend.app.etl.full_record_action_interpretation import (
    ActionInterpretationError,
    sha256_json,
    validate_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import load_json
from backend.scripts.build_m13c_education_workforce_action_interpretation import (
    ARTIFACT_PATH,
    READINESS_PATH,
    SCHEMA_PATH,
    build,
    build_outputs,
)
from scripts.validate_m13c_education_workforce_action_interpretation import (
    ROLL19_SOURCE_ID,
    validate_semantic_boundaries,
)


ROOT = Path(__file__).resolve().parents[2]


class M13CEducationWorkforceActionInterpretationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_json(ARTIFACT_PATH)
        cls.readiness = load_json(READINESS_PATH)

    @staticmethod
    def _candidate(artifact: dict, action_id: str) -> dict:
        return next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == action_id
        )

    @staticmethod
    def _resign_candidate(candidate: dict) -> None:
        subject = {
            key: value
            for key, value in candidate.items()
            if key != "candidate_content_subject_sha256"
        }
        candidate["candidate_content_subject_sha256"] = sha256_json(subject)

    @staticmethod
    def _resign_artifact(artifact: dict) -> None:
        artifact["interpretation_subject_sha256"] = sha256_json(artifact["subject"])

    def _validate(self, artifact: dict) -> None:
        validate_candidate_artifact(
            artifact,
            readiness_artifact=self.readiness,
            repository_root=ROOT,
        )
        validate_semantic_boundaries(artifact, self.readiness)

    def _mutate_meaning(self, action_id: str, addition: str) -> dict:
        artifact = deepcopy(self.artifact)
        candidate = self._candidate(artifact, action_id)
        candidate["proposed_exact_action_meaning"] += addition
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        return artifact

    def test_repository_artifact_is_exact_17_of_17_and_deterministic(self) -> None:
        self._validate(self.artifact)
        subject = self.artifact["subject"]
        self.assertEqual(17, len(subject["action_ids"]))
        self.assertEqual(17, len(subject["accounting"]))
        self.assertEqual(17, len(subject["evidence_maps"]))
        self.assertEqual(17, len(subject["candidates"]))
        self.assertEqual([], subject["blocked_action_ids"])
        schema = load_json(SCHEMA_PATH)
        Draft7Validator.check_schema(schema)
        self.assertEqual([], list(Draft7Validator(schema).iter_errors(self.artifact)))
        self.assertEqual(self.artifact, build())
        for path, content in build_outputs().items():
            self.assertEqual(path.read_bytes().replace(b"\r\n", b"\n"), content)

    def test_roll79_cannot_inherit_whole_bill_meaning(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = self._candidate(artifact, "house:119:1:79")
        candidate["proposed_exact_action_meaning"] = (
            "The House choice was whether to pass H.R. 1048 as a whole."
        )
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "roll 79"):
            validate_semantic_boundaries(artifact, self.readiness)

    def test_roll312_not_voting_cannot_gain_directionality(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = self._candidate(artifact, "house:119:1:312")
        candidate["proposed_member_position_effect"] = "supports_exact_choice"
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "effect mismatch"):
            validate_candidate_artifact(
                artifact,
                readiness_artifact=self.readiness,
                repository_root=ROOT,
            )

    def test_hr1642_cannot_become_generic_education_support(self) -> None:
        artifact = self._mutate_meaning(
            "house:119:1:146", " It shows general support for education."
        )
        with self.assertRaisesRegex(ActionInterpretationError, "roll 146"):
            validate_semantic_boundaries(artifact, self.readiness)

    def test_s356_cannot_become_generic_public_lands_support(self) -> None:
        artifact = self._mutate_meaning(
            "house:119:1:315", " It shows general support for public lands."
        )
        with self.assertRaisesRegex(ActionInterpretationError, "roll 315"):
            validate_semantic_boundaries(artifact, self.readiness)

    def test_roll19_cannot_use_old_defective_source(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = self._candidate(artifact, "house:119:2:19")
        candidate["source_references"] = [
            item for item in candidate["source_references"] if item != ROLL19_SOURCE_ID
        ]
        candidate["source_references"].append(
            "congressional-record:2026-01-13:H676-H677:hr2262"
        )
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "roll 19"):
            validate_semantic_boundaries(artifact, self.readiness)

    def test_roll19_cannot_use_earlier_bill_version(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = self._candidate(artifact, "house:119:2:19")
        candidate["source_references"].append("congress-text:119:hr:2262:ih")
        candidate["claim_components"][0]["source_id"] = "congress-text:119:hr:2262:ih"
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "roll 19"):
            validate_semantic_boundaries(artifact, self.readiness)

    def test_source_native_advocacy_cannot_become_meaning(self) -> None:
        artifact = self._mutate_meaning(
            "house:119:2:19", " This is commonsense legislation."
        )
        with self.assertRaisesRegex(ActionInterpretationError, "advocacy"):
            validate_semantic_boundaries(artifact, self.readiness)

    def test_member_or_broad_issue_inference_exceeds_operational_source(self) -> None:
        artifact = self._mutate_meaning(
            "house:119:1:313", " Foushee supported education generally."
        )
        with self.assertRaisesRegex(ActionInterpretationError, "member attribution"):
            validate_candidate_artifact(
                artifact,
                readiness_artifact=self.readiness,
                repository_root=ROOT,
            )

    def test_another_actions_operational_source_cannot_be_substituted(self) -> None:
        artifact = deepcopy(self.artifact)
        first, second = artifact["subject"]["candidates"][:2]
        first["source_references"] = list(second["source_references"])
        self._resign_candidate(first)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "source references"):
            validate_candidate_artifact(
                artifact,
                readiness_artifact=self.readiness,
                repository_root=ROOT,
            )

    def test_roll19_floor_text_locator_is_required(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = self._candidate(artifact, "house:119:2:19")
        candidate["official_title_or_purpose"]["locator"] = "official-title"
        candidate["claim_components"][0]["locator"] = "official-title"
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "floor-text handling"):
            validate_candidate_artifact(
                artifact,
                readiness_artifact=self.readiness,
                repository_root=ROOT,
            )


if __name__ == "__main__":
    unittest.main()
