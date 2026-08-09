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
from backend.scripts.build_m11c_national_security_action_interpretation import (
    ARTIFACT_PATH,
    READINESS_PATH,
    SCHEMA_PATH,
    build,
    build_outputs,
)


ROOT = Path(__file__).resolve().parents[2]


class FullRecordActionInterpretationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_json(ARTIFACT_PATH)
        cls.readiness = load_json(READINESS_PATH)

    def _validate(self, artifact: dict) -> None:
        validate_candidate_artifact(
            artifact,
            readiness_artifact=self.readiness,
            repository_root=ROOT,
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

    def test_repository_artifact_validates(self) -> None:
        self._validate(self.artifact)

    def test_schema_is_draft7_and_artifact_conforms(self) -> None:
        schema = load_json(SCHEMA_PATH)
        Draft7Validator.check_schema(schema)
        self.assertEqual([], list(Draft7Validator(schema).iter_errors(self.artifact)))

    def test_builder_is_deterministic(self) -> None:
        self.assertEqual(self.artifact, build())
        for path, content in build_outputs().items():
            self.assertEqual(path.read_bytes().replace(b"\r\n", b"\n"), content)

    def test_exact_accounting_is_82_81_1(self) -> None:
        subject = self.artifact["subject"]
        self.assertEqual(82, len(subject["accounting"]))
        self.assertEqual(81, len(subject["candidates"]))
        self.assertEqual(["house:119:2:278"], subject["blocked_action_ids"])
        self.assertNotIn(
            "house:119:2:278",
            {candidate["action_id"] for candidate in subject["candidates"]},
        )

    def test_candidate_removal_fails_closed(self) -> None:
        artifact = deepcopy(self.artifact)
        artifact["subject"]["candidates"].pop()
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "candidate action set"):
            self._validate(artifact)

    def test_blocked_action_cannot_receive_candidate(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = deepcopy(artifact["subject"]["candidates"][0])
        candidate["action_id"] = "house:119:2:278"
        candidate["candidate_id"] = (
            "action-interpretation-candidate:house:119:2:278:m11c:v1"
        )
        self._resign_candidate(candidate)
        artifact["subject"]["candidates"].append(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "candidate action set"):
            self._validate(artifact)

    def test_member_position_effect_cannot_be_flipped(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = artifact["subject"]["candidates"][0]
        candidate["proposed_member_position_effect"] = "supports_exact_choice"
        if candidate["official_member_action"] == "yea":
            candidate["proposed_member_position_effect"] = "opposes_exact_choice"
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "effect mismatch"):
            self._validate(artifact)

    def test_party_language_cannot_enter_meaning(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = artifact["subject"]["candidates"][0]
        candidate["proposed_exact_action_meaning"] += " Most Democrats opposed it."
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "forbidden semantic"):
            self._validate(artifact)

    def test_amendment_meaning_cannot_use_clerk_or_parent_source(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["mechanism_class"] == "amendment"
        )
        candidate["claim_components"][0]["source_id"] = next(
            source_id
            for source_id in candidate["source_references"]
            if source_id.startswith("clerk:")
        )
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "non-exact source"):
            self._validate(artifact)

    def test_package_boundary_cannot_be_removed(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["coverage_assessment"] == "package_level_bounded_summary"
        )
        candidate["limitations"] = []
        candidate["unresolved_editorial_questions"] = []
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "package-level boundary"
        ):
            self._validate(artifact)

    def test_source_digest_mutation_fails_closed(self) -> None:
        artifact = deepcopy(self.artifact)
        evidence = artifact["subject"]["evidence_maps"][0]
        evidence["source_bindings"][0]["raw_provenance"]["sha256"] = "0" * 64
        evidence_subject = {
            key: value
            for key, value in evidence.items()
            if key not in {"evidence_map_id", "evidence_map_subject_sha256"}
        }
        evidence["evidence_map_subject_sha256"] = sha256_json(evidence_subject)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["evidence_map_id"] == evidence["evidence_map_id"]
        )
        candidate["evidence_map_subject_sha256"] = evidence[
            "evidence_map_subject_sha256"
        ]
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "raw source digest"):
            self._validate(artifact)

    def test_downstream_authority_cannot_be_enabled(self) -> None:
        artifact = deepcopy(self.artifact)
        artifact["subject"]["downstream_authorizations"]["semantic_ir"] = True
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "downstream authority"):
            self._validate(artifact)


if __name__ == "__main__":
    unittest.main()
