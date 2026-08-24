from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft7Validator

from backend.app.etl.full_record_policy_episode_decisions import (
    PolicyEpisodeDecisionError,
    seal,
    validate_authority,
    validate_implementation,
)
from backend.scripts.build_m13f_education_workforce_policy_episode_acceptance import (
    AUTHORITY_PATH,
    AUTHORITY_SCHEMA_PATH,
    CANDIDATE_PATH,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    INTERPRETATION_IMPLEMENTATION_PATH,
    REVIEWER_AUTHORITY,
    REVIEWER_ID,
    build,
)
from scripts.validate_m13f_education_workforce_policy_episode_acceptance import validate


ROOT = Path(__file__).resolve().parents[2]
M11F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class M13fEducationWorkforcePolicyEpisodeAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = load(AUTHORITY_PATH)
        cls.implementation = load(IMPLEMENTATION_PATH)
        cls.interpretation_records = load(INTERPRETATION_IMPLEMENTATION_PATH)[
            "subject"
        ]["implementation_records"]

    def test_deterministic_exact_acceptance(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["decision_count"], 16)
        self.assertEqual(result["final_accounting"]["accepted_action_count"], 17)
        self.assertEqual(result["final_accounting"]["accepted_episode_count"], 16)
        self.assertEqual(build(check=True)["single_action_episode_count"], 15)
        self.assertEqual(build(check=True)["multi_action_episode_count"], 1)

    def test_all_review_decisions_are_exact_acceptances(self) -> None:
        decisions = self.authority["subject"]["episode_decisions"]
        self.assertEqual(len(decisions), 16)
        self.assertTrue(
            all(
                row["decision"] == "accept_candidate_as_written"
                and row["replacement_episode_ids"] == []
                and row["reviewer_id"] == REVIEWER_ID
                and row["reviewer_authority"] == REVIEWER_AUTHORITY
                for row in decisions
            )
        )

    def test_generic_schemas_accept_unchanged_m11f_and_m13f(self) -> None:
        for schema_path, historical_path, current_path in (
            (
                AUTHORITY_SCHEMA_PATH,
                M11F_ROOT / "human_policy_episode_authority.json",
                AUTHORITY_PATH,
            ),
            (
                IMPLEMENTATION_SCHEMA_PATH,
                M11F_ROOT / "episode_decision_implementation_bundle.json",
                IMPLEMENTATION_PATH,
            ),
        ):
            validator = Draft7Validator(load(schema_path))
            self.assertEqual(list(validator.iter_errors(load(historical_path))), [])
            self.assertEqual(list(validator.iter_errors(load(current_path))), [])

    def test_non_directional_not_voting_is_preserved(self) -> None:
        episode = next(
            row
            for row in self.implementation["subject"]["implementation_records"]
            if row["primary_action_ids"] == ["house:119:1:312"]
        )
        self.assertEqual(episode["member_direction"], "non_directional_not_voting")
        self.assertEqual(
            episode["actions"][0]["accepted_exact_choice_position_effect"],
            "non_directional_not_voting",
        )

    def test_hr1048_mixed_choices_and_package_boundary_are_preserved(self) -> None:
        episode = next(
            row
            for row in self.implementation["subject"]["implementation_records"]
            if row["episode_id"] == "hr-1048-amendment-and-final-passage"
        )
        self.assertEqual(episode["grouping_type"], "cross_measure")
        self.assertEqual(episode["member_direction"], "mixed_on_episode_choices")
        self.assertEqual(
            {
                row["action_id"]: row["accepted_exact_choice_position_effect"]
                for row in episode["actions"]
            },
            {
                "house:119:1:79": "supports_exact_choice",
                "house:119:1:83": "opposes_exact_choice",
            },
        )
        self.assertTrue(
            any("whole-package" in value for value in episode["material_limitations"])
        )

    def test_missing_action_is_rejected(self) -> None:
        changed = copy.deepcopy(self.implementation)
        changed["subject"]["implementation_records"].pop()
        changed = seal(changed, "implementation_subject_sha256")
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "omitted"):
            validate_implementation(
                changed,
                authority=self.authority,
                accepted_interpretation_records=self.interpretation_records,
                blocked_action_id=None,
                rejected_episode_ids=set(),
            )

    def test_duplicate_action_assignment_is_rejected(self) -> None:
        changed = copy.deepcopy(self.implementation)
        source = changed["subject"]["implementation_records"][0]
        target = changed["subject"]["implementation_records"][1]
        target["primary_action_ids"] = source["primary_action_ids"]
        target["actions"] = copy.deepcopy(source["actions"])
        target = seal(target, "record_subject_sha256")
        changed["subject"]["implementation_records"][1] = target
        changed = seal(changed, "implementation_subject_sha256")
        with self.assertRaisesRegex(
            PolicyEpisodeDecisionError, "more than once|single-action grouping"
        ):
            validate_implementation(
                changed,
                authority=self.authority,
                accepted_interpretation_records=self.interpretation_records,
                blocked_action_id=None,
                rejected_episode_ids=set(),
            )

    def test_wrong_reviewer_authority_is_rejected(self) -> None:
        candidate = load(CANDIDATE_PATH)
        changed = copy.deepcopy(self.authority)
        changed["subject"]["authority_decision"]["reviewer_authority"] = "wrong"
        changed = seal(changed, "authority_subject_sha256")
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "reviewer"):
            validate_authority(
                changed,
                candidate=candidate,
                accepted_single_episode_ids={
                    row["episode_id"] for row in candidate["subject"]["episodes"]
                },
                rejected_episode_ids=set(),
            )


if __name__ == "__main__":
    unittest.main()
