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

    def test_short_title_alone_cannot_be_high_confidence_meaning(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:2:142"
        )
        candidate["official_title_or_purpose"]["locator"] = "official-title"
        candidate["proposed_exact_action_meaning"] = (
            "The House choice was whether to pass S. 1318, an operative measure "
            "identified only by its short title."
        )
        candidate["claim_components"] = candidate["claim_components"][:1]
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        candidate["claim_components"][0]["locator"] = "official-title"
        candidate["coverage_assessment"] = "bounded_official_purpose_summary"
        candidate["confidence"] = "high"
        candidate["limitations"] = []
        candidate["unresolved_editorial_questions"] = []
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "short-title-only meaning treated as complete"
        ):
            self._validate(artifact)

    def test_compound_package_cannot_collapse_to_first_short_title(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:2:142"
        )
        candidate["proposed_exact_action_meaning"] = (
            "The House choice was whether to pass S. 1318, the Foreign "
            "Intelligence Accountability Act."
        )
        candidate["claim_components"] = candidate["claim_components"][:1]
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "structured operative components mismatch"
        ):
            self._validate(artifact)

    def test_source_native_structured_package_summaries_validate(self) -> None:
        candidates = {
            item["action_id"]: item for item in self.artifact["subject"]["candidates"]
        }
        for action_id in ("house:119:1:320", "house:119:2:142"):
            candidate = candidates[action_id]
            self.assertEqual(
                "structured_operative_summary",
                candidate["official_title_or_purpose"]["locator"],
            )
            self.assertEqual(
                "package_level_bounded_summary", candidate["coverage_assessment"]
            )
            self.assertEqual("medium", candidate["confidence"])
        self._validate(self.artifact)

    def test_fabricated_structural_component_fails_validation(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:1:320"
        )
        fabricated = deepcopy(candidate["claim_components"][-1])
        fabricated["component_id"] += ":fabricated"
        fabricated["wording"] = "Fabricated authorization component"
        candidate["claim_components"].append(fabricated)
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "structured operative components mismatch"
        ):
            self._validate(artifact)

    def test_package_component_position_attribution_is_prohibited(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:1:320"
        )
        candidate["proposed_exact_action_meaning"] += (
            " The member supported the Department of Defense component."
        )
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "component-level member attribution prohibited"
        ):
            self._validate(artifact)

    def test_governed_structured_meaning_regressions(self) -> None:
        candidates = {
            item["action_id"]: item for item in self.artifact["subject"]["candidates"]
        }
        s1071 = candidates["house:119:1:320"]["proposed_exact_action_meaning"]
        self.assertIn("top-level divisions", s1071)
        self.assertIn("Department of Defense Authorizations", s1071)
        self.assertIn("Intelligence Authorization Act", s1071)
        s1318 = candidates["house:119:2:142"]["proposed_exact_action_meaning"]
        self.assertIn("Foreign Intelligence Accountability Act", s1318)
        self.assertIn("Extension of authorities of title VII", s1318)
        self.assertIn("Anti-CBDC Surveillance State Act", s1318)
        self.assertIn("central bank digital currency", s1318)

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
