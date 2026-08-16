from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from jsonschema import Draft7Validator

from backend.app.etl.full_record_action_interpretation import (
    ActionInterpretationError,
    _build_candidate,
    _build_evidence_map,
    sha256_json,
    validate_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import load_json
from backend.scripts.build_m12c_environment_energy_action_interpretation import (
    ARTIFACT_PATH,
    READINESS_PATH,
    SCHEMA_PATH,
    build,
    build_outputs,
)


ROOT = Path(__file__).resolve().parents[2]


class M12CEnvironmentEnergyActionInterpretationTests(unittest.TestCase):
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

    def test_repository_artifact_is_exact_63_of_63(self) -> None:
        self._validate(self.artifact)
        subject = self.artifact["subject"]
        self.assertEqual(63, len(subject["action_ids"]))
        self.assertEqual(63, len(subject["accounting"]))
        self.assertEqual(63, len(subject["evidence_maps"]))
        self.assertEqual(63, len(subject["candidates"]))
        self.assertEqual([], subject["blocked_action_ids"])

    def test_generic_schema_and_deterministic_outputs(self) -> None:
        schema = load_json(SCHEMA_PATH)
        Draft7Validator.check_schema(schema)
        self.assertEqual([], list(Draft7Validator(schema).iter_errors(self.artifact)))
        self.assertEqual(self.artifact, build())
        for path, content in build_outputs().items():
            self.assertEqual(path.read_bytes().replace(b"\r\n", b"\n"), content)

    def test_raw_yea_or_nay_cannot_determine_meaning(self) -> None:
        record = deepcopy(self.readiness["subject"]["action_readiness"][0])
        evidence = _build_evidence_map(record, candidate_namespace="m12c-test")
        original = _build_candidate(
            record,
            evidence_map=evidence,
            repository_root=ROOT,
            candidate_namespace="m12c-test",
        )
        record["official_member_action"] = (
            "yea" if record["official_member_action"] != "yea" else "nay"
        )
        flipped = _build_candidate(
            record,
            evidence_map=evidence,
            repository_root=ROOT,
            candidate_namespace="m12c-test",
        )
        self.assertEqual(
            original["proposed_exact_action_meaning"],
            flipped["proposed_exact_action_meaning"],
        )
        self.assertNotEqual(
            original["proposed_member_position_effect"],
            flipped["proposed_member_position_effect"],
        )

    def test_not_voting_cannot_become_support_or_opposition(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:2:136"
        )
        self.assertEqual("not_voting", candidate["official_member_action"])
        candidate["proposed_member_position_effect"] = "opposes_exact_choice"
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "effect mismatch"):
            self._validate(artifact)

    def test_short_or_proper_title_cannot_stand_alone(self) -> None:
        m11_artifact = load_json(
            ROOT / "docs/editorial/full_record_reviews/interpretation_candidates/"
            "f000477_national_security_foreign_119_v1/candidate_batch.json"
        )
        m11_readiness = load_json(
            ROOT / "docs/editorial/full_record_reviews/source_readiness/"
            "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
        )
        candidate = next(
            item
            for item in m11_artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:2:142"
        )
        candidate["official_title_or_purpose"]["locator"] = "official-title"
        candidate["claim_components"] = candidate["claim_components"][:1]
        candidate["claim_components"][0]["locator"] = "official-title"
        candidate["coverage_assessment"] = "bounded_official_purpose_summary"
        candidate["confidence"] = "high"
        candidate["limitations"] = []
        candidate["unresolved_editorial_questions"] = []
        self._resign_candidate(candidate)
        self._resign_artifact(m11_artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "short-title-only meaning treated as complete"
        ):
            validate_candidate_artifact(
                m11_artifact,
                readiness_artifact=m11_readiness,
                repository_root=ROOT,
            )

    def test_source_structure_cannot_omit_or_invent_components(self) -> None:
        m11_artifact = load_json(
            ROOT / "docs/editorial/full_record_reviews/interpretation_candidates/"
            "f000477_national_security_foreign_119_v1/candidate_batch.json"
        )
        m11_readiness = load_json(
            ROOT / "docs/editorial/full_record_reviews/source_readiness/"
            "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
        )
        candidate = next(
            item
            for item in m11_artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:1:320"
        )
        candidate["claim_components"].pop()
        self._resign_candidate(candidate)
        self._resign_artifact(m11_artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "structured operative components mismatch"
        ):
            validate_candidate_artifact(
                m11_artifact,
                readiness_artifact=m11_readiness,
                repository_root=ROOT,
            )

    def test_broad_package_cannot_become_component_position(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = next(
            item
            for item in artifact["subject"]["candidates"]
            if item["action_id"] == "house:119:1:25"
        )
        candidate["proposed_exact_action_meaning"] += (
            " The member opposed an individual forest-management component."
        )
        candidate["claim_components"][0]["wording"] = candidate[
            "proposed_exact_action_meaning"
        ]
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(
            ActionInterpretationError, "component-level member attribution"
        ):
            self._validate(artifact)

    def test_another_actions_source_cannot_be_substituted(self) -> None:
        artifact = deepcopy(self.artifact)
        first, second = artifact["subject"]["candidates"][:2]
        first["source_references"] = list(second["source_references"])
        self._resign_candidate(first)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "source references"):
            self._validate(artifact)

    def test_party_sponsor_and_ideology_fields_cannot_affect_meaning(self) -> None:
        record = deepcopy(self.readiness["subject"]["action_readiness"][0])
        evidence = _build_evidence_map(record, candidate_namespace="m12c-test")
        baseline = _build_candidate(
            record,
            evidence_map=evidence,
            repository_root=ROOT,
            candidate_namespace="m12c-test",
        )
        record.update(
            {
                "party": "synthetic",
                "sponsor": "synthetic",
                "ideology": "synthetic",
            }
        )
        mutated = _build_candidate(
            record,
            evidence_map=evidence,
            repository_root=ROOT,
            candidate_namespace="m12c-test",
        )
        self.assertEqual(
            baseline["proposed_exact_action_meaning"],
            mutated["proposed_exact_action_meaning"],
        )

    def test_weaker_context_cannot_replace_operative_evidence(self) -> None:
        artifact = deepcopy(self.artifact)
        candidate = artifact["subject"]["candidates"][0]
        clerk_id = next(
            source_id
            for source_id in candidate["source_references"]
            if source_id.startswith("clerk:")
        )
        candidate["claim_components"][0]["source_id"] = clerk_id
        self._resign_candidate(candidate)
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "non-exact source"):
            self._validate(artifact)

    def test_meaning_change_requires_content_binding_change(self) -> None:
        artifact = deepcopy(self.artifact)
        artifact["subject"]["candidates"][0]["proposed_exact_action_meaning"] += (
            " Changed without resigning."
        )
        self._resign_artifact(artifact)
        with self.assertRaisesRegex(ActionInterpretationError, "candidate digest"):
            self._validate(artifact)

    def test_episode_synthesis_public_motive_and_advice_fields_cannot_leak(
        self,
    ) -> None:
        schema = load_json(SCHEMA_PATH)
        for field in (
            "episode_id",
            "synthesis",
            "public_wording",
            "motive",
            "voting_advice",
        ):
            artifact = deepcopy(self.artifact)
            artifact["subject"]["candidates"][0][field] = "forbidden"
            errors = list(Draft7Validator(schema).iter_errors(artifact))
            self.assertTrue(errors, field)


if __name__ == "__main__":
    unittest.main()
