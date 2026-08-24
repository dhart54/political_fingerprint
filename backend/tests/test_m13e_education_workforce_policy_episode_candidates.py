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

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    PolicyEpisodeCandidateError,
    seal,
    validate_candidate_batch,
)
from backend.scripts.build_m13e_education_workforce_policy_episode_candidates import (  # noqa: E402
    AMENDMENT_ACTION_ID,
    BATCH_PATH,
    CANDIDATE_PATH,
    DECISION_PATH,
    GENERIC_BATCH_SCHEMA_PATH,
    HR1048_EPISODE_ID,
    IMPLEMENTATION_PATH,
    M11_BATCH_PATH,
    M12_BATCH_PATH,
    PASSAGE_ACTION_ID,
    PERMITTED_CROSS_MEASURE_SETS,
    PROHIBITED_GROUPED_SETS,
    build,
)
from scripts.validate_m13e_education_workforce_policy_episode_candidates import (  # noqa: E402
    validate_repository,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_episode(batch: dict, action_id: str) -> dict:
    return next(
        row
        for row in batch["subject"]["episodes"]
        if action_id in row["primary_action_ids"]
    )


def reseal_episode(batch: dict, episode: dict) -> None:
    episode.update(seal(episode, "episode_subject_sha256"))
    batch.update(seal(batch, "episode_candidate_subject_sha256"))


def validate(batch: dict) -> dict:
    return validate_candidate_batch(
        batch=batch,
        implementation=load(IMPLEMENTATION_PATH),
        candidate_artifact=load(CANDIDATE_PATH),
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id=None,
    )


class M13EEducationWorkforcePolicyEpisodeCandidateTests(unittest.TestCase):
    def test_repository_package_is_complete_16_episode_frontier(self) -> None:
        result = validate_repository()
        self.assertEqual(result["assigned_action_count"], 17)
        self.assertEqual(result["episode_count"], 16)
        self.assertEqual(result["single_action_episode_count"], 15)
        self.assertEqual(result["multi_action_episode_count"], 1)
        self.assertEqual(result["blocked_count"], 0)
        self.assertEqual(result["ambiguous_or_unassigned_count"], 0)

    def test_deterministic_regeneration(self) -> None:
        self.assertEqual(build(check=True)["episode_count"], 16)

    def test_generic_schema_accepts_m11_m12_and_m13(self) -> None:
        validator = Draft7Validator(load(GENERIC_BATCH_SCHEMA_PATH))
        for path in (M11_BATCH_PATH, M12_BATCH_PATH, BATCH_PATH):
            self.assertEqual(list(validator.iter_errors(load(path))), [])

    def test_hr1048_event_preserves_two_distinct_choices(self) -> None:
        episode = find_episode(load(BATCH_PATH), AMENDMENT_ACTION_ID)
        self.assertEqual(episode["episode_id"], HR1048_EPISODE_ID)
        self.assertEqual(
            episode["primary_action_ids"], [AMENDMENT_ACTION_ID, PASSAGE_ACTION_ID]
        )
        self.assertEqual(
            episode["member_direction_candidate"], "mixed_on_episode_choices"
        )
        self.assertEqual(
            episode["direction_derivation"]["accepted_position_effects_by_action"],
            {
                AMENDMENT_ACTION_ID: "supports_exact_choice",
                PASSAGE_ACTION_ID: "opposes_exact_choice",
            },
        )
        self.assertIn("whole-package", episode["material_policy_differences"])

    def test_grouped_episode_cannot_rewrite_amendment_meaning(self) -> None:
        batch = load(BATCH_PATH)
        episode = find_episode(batch, AMENDMENT_ACTION_ID)
        episode["actions"][0]["accepted_exact_action_meaning"] = (
            "The House choice was whether to pass H.R. 1048 as a whole."
        )
        reseal_episode(batch, episode)
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "accepted interpretation binding differs"
        ):
            validate(batch)

    def test_same_topic_cannot_group_distinct_school_measures(self) -> None:
        batch = load(BATCH_PATH)
        first = find_episode(batch, "house:119:1:312")
        second = find_episode(batch, "house:119:1:313")
        first["actions"] += second["actions"]
        first["primary_action_ids"] += second["primary_action_ids"]
        first["direction_derivation"]["accepted_position_effects_by_action"].update(
            second["direction_derivation"]["accepted_position_effects_by_action"]
        )
        batch["subject"]["episodes"].remove(second)
        reseal_episode(batch, first)
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "same-topic or parent-package overreach"
        ):
            validate(batch)

    def test_unreviewed_cross_measure_grouping_fails_closed(self) -> None:
        batch = load(BATCH_PATH)
        first = find_episode(batch, "house:119:1:68")
        second = find_episode(batch, "house:119:1:315")
        first["actions"] += second["actions"]
        first["primary_action_ids"] += second["primary_action_ids"]
        first["direction_derivation"]["accepted_position_effects_by_action"].update(
            second["direction_derivation"]["accepted_position_effects_by_action"]
        )
        batch["subject"]["episodes"].remove(second)
        reseal_episode(batch, first)
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError,
            "cross-measure grouping lacks governed semantic evidence",
        ):
            validate(batch)

    def test_roll312_remains_nondirectional_singleton(self) -> None:
        episode = find_episode(load(BATCH_PATH), "house:119:1:312")
        self.assertEqual(episode["primary_action_ids"], ["house:119:1:312"])
        self.assertEqual(
            episode["member_direction_candidate"], "non_directional_not_voting"
        )

    def test_missing_action_is_rejected(self) -> None:
        batch = load(BATCH_PATH)
        batch["subject"]["episodes"].remove(find_episode(batch, "house:119:1:68"))
        batch.update(seal(batch, "episode_candidate_subject_sha256"))
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "accepted action omitted"
        ):
            validate(batch)

    def test_decision_template_is_entirely_empty(self) -> None:
        decision = load(DECISION_PATH)
        self.assertEqual(decision["decision_count"], 16)
        self.assertIsNone(decision["selected_batch_decision"])
        self.assertTrue(
            all(
                row["selected_decision"] is None
                and row["bounded_revision"] is None
                and row["reviewer_id"] is None
                and row["reviewer_authority"] is None
                and row["decision_timestamp"] is None
                for row in decision["decisions"]
            )
        )

    def test_party_sponsor_ideology_and_raw_vote_fields_rejected(self) -> None:
        for field in ("party", "sponsor", "ideology", "raw_vote_direction"):
            with self.subTest(field=field):
                batch = deepcopy(load(BATCH_PATH))
                batch["subject"]["episodes"][0][field] = "forbidden"
                errors = list(
                    Draft7Validator(load(GENERIC_BATCH_SCHEMA_PATH)).iter_errors(batch)
                )
                self.assertTrue(errors)

    def test_downstream_authority_leakage_rejected(self) -> None:
        batch = load(BATCH_PATH)
        batch["subject"]["downstream_authorizations"]["semantic_ir"] = True
        batch.update(seal(batch, "episode_candidate_subject_sha256"))
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "downstream authority leakage"
        ):
            validate(batch)


if __name__ == "__main__":
    unittest.main()
