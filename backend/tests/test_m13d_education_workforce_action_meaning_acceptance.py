from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation_decisions import (  # noqa: E402
    ActionInterpretationDecisionError,
    build_authority_record,
    validate_authority_record,
    validate_implementation_bundle,
)
from backend.scripts.build_m13d_education_workforce_action_meaning_acceptance import (  # noqa: E402
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    PARITY_PATH,
    PARITY_SCHEMA_PATH,
    READINESS_PATH,
    build_artifacts,
    write_outputs,
)
from scripts.validate_m13d_education_workforce_action_meaning_acceptance import (  # noqa: E402
    M11_AUTHORITY_PATH,
    M11_IMPLEMENTATION_PATH,
    M11_PARITY_PATH,
    validate_repository,
)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class M13DEducationWorkforceActionMeaningAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate = load(CANDIDATE_PATH)
        cls.readiness = load(READINESS_PATH)
        cls.authority = load(AUTHORITY_PATH)
        cls.implementation = load(IMPLEMENTATION_PATH)

    def test_repository_authority_and_implementation_are_exact_17(self) -> None:
        result = validate_repository()
        self.assertEqual(result["accepted_decision_count"], 17)
        self.assertEqual(result["source_blocked_count"], 0)
        self.assertEqual(
            result["effect_counts"],
            {
                "non_directional_not_voting": 1,
                "opposes_exact_choice": 10,
                "supports_exact_choice": 6,
            },
        )

    def test_deterministic_regeneration(self) -> None:
        self.assertEqual(write_outputs(check=True)["accepted_decision_count"], 17)
        self.assertEqual(build_artifacts()["authority"], self.authority)

    def test_generic_schemas_accept_m11d_and_m13d(self) -> None:
        for schema_path, historical_path, current_path in (
            (AUTHORITY_SCHEMA_PATH, M11_AUTHORITY_PATH, AUTHORITY_PATH),
            (IMPLEMENTATION_SCHEMA_PATH, M11_IMPLEMENTATION_PATH, IMPLEMENTATION_PATH),
            (PARITY_SCHEMA_PATH, M11_PARITY_PATH, PARITY_PATH),
        ):
            validator = Draft7Validator(load(schema_path))
            self.assertEqual(list(validator.iter_errors(load(historical_path))), [])
            self.assertEqual(list(validator.iter_errors(load(current_path))), [])

    def test_reviewer_identity_is_content_bound_not_hard_coded(self) -> None:
        artifact = build_authority_record(
            candidate_artifact=self.candidate,
            readiness_artifact=self.readiness,
            repository_root=ROOT,
            artifact_id="human-action-interpretation-authority:test:alternate:v1",
            candidate_file_sha256="0" * 64,
            decision_template_binding={"template_id": "test", "file_sha256": "0" * 64},
            accepted_pr=1,
            accepted_head="0" * 40,
            post_merge_main="1" * 40,
            reviewer_identity="independent:reviewer",
            reviewer_authority="full_record_action_interpretation_review_authority_v1",
            decision_timestamp="2026-08-16T01:01:00Z",
        )
        self.assertEqual(
            artifact["subject"]["authority_decision"]["reviewer_identity"],
            "independent:reviewer",
        )

    def test_empty_or_wrong_reviewer_authority_rejected(self) -> None:
        common = dict(
            candidate_artifact=self.candidate,
            readiness_artifact=self.readiness,
            repository_root=ROOT,
            artifact_id="test",
            candidate_file_sha256="0" * 64,
            decision_template_binding={},
            accepted_pr=1,
            accepted_head="0" * 40,
            post_merge_main="1" * 40,
            decision_timestamp="2026-08-16T01:01:00Z",
        )
        with self.assertRaisesRegex(ActionInterpretationDecisionError, "nonempty"):
            build_authority_record(
                **common,
                reviewer_identity="",
                reviewer_authority="full_record_action_interpretation_review_authority_v1",
            )
        with self.assertRaisesRegex(ActionInterpretationDecisionError, "class differs"):
            build_authority_record(
                **common,
                reviewer_identity="reviewer",
                reviewer_authority="unrecognized_authority",
            )

    def test_accepted_wording_cannot_differ_from_candidate(self) -> None:
        authority = deepcopy(self.authority)
        authority["subject"]["decisions"][0]["accepted_exact_action_meaning"] += (
            " changed"
        )
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "authority subject digest mismatch"
        ):
            validate_authority_record(authority, candidate_artifact=self.candidate)

    def test_implementation_cannot_differ_from_authority(self) -> None:
        implementation = deepcopy(self.implementation)
        implementation["subject"]["implementation_records"][0][
            "accepted_exact_choice_position_effect"
        ] = "supports_exact_choice"
        with self.assertRaisesRegex(
            ActionInterpretationDecisionError, "implementation subject digest mismatch"
        ):
            validate_implementation_bundle(
                implementation,
                authority=self.authority,
                candidate_artifact=self.candidate,
            )

    def test_not_voting_remains_nondirectional(self) -> None:
        records = {
            row["action_id"]: row
            for row in self.implementation["subject"]["implementation_records"]
        }
        self.assertEqual(
            records["house:119:1:312"]["accepted_exact_choice_position_effect"],
            "non_directional_not_voting",
        )

    def test_broad_package_limitations_remain_exact(self) -> None:
        decisions = {
            row["action_id"]: row for row in self.authority["subject"]["decisions"]
        }
        candidates = {
            row["action_id"]: row for row in self.candidate["subject"]["candidates"]
        }
        for action_id in ("house:119:1:83", "house:119:2:31"):
            self.assertEqual(
                decisions[action_id]["accepted_coverage_assessment"],
                "package_level_bounded_summary",
            )
            self.assertEqual(
                decisions[action_id]["accepted_limitations"],
                candidates[action_id]["limitations"],
            )

    def test_every_source_and_evidence_binding_is_preserved(self) -> None:
        decisions = {
            row["action_id"]: row for row in self.authority["subject"]["decisions"]
        }
        for candidate in self.candidate["subject"]["candidates"]:
            decision = decisions[candidate["action_id"]]
            self.assertEqual(
                decision["accepted_source_references"], candidate["source_references"]
            )
            self.assertEqual(
                decision["accepted_evidence_map_subject_sha256"],
                candidate["evidence_map_subject_sha256"],
            )

    def test_downstream_authority_leakage_rejected(self) -> None:
        authority = deepcopy(self.authority)
        authority["subject"]["downstream_authorizations"]["semantic_ir"] = True
        with self.assertRaises(ActionInterpretationDecisionError):
            validate_authority_record(authority, candidate_artifact=self.candidate)


if __name__ == "__main__":
    unittest.main()
