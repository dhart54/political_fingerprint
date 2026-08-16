from __future__ import annotations

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
from backend.scripts.build_m12e_environment_energy_policy_episode_candidates import (  # noqa: E402
    BATCH_PATH,
    CANDIDATE_PATH,
    DECISION_PATH,
    GENERIC_BATCH_SCHEMA_PATH,
    IMPLEMENTATION_PATH,
    M11_BATCH_PATH,
    PERMITTED_CROSS_MEASURE_SETS,
    PROHIBITED_GROUPED_SETS,
    build,
)
from scripts.validate_m12e_environment_energy_policy_episode_candidates import (  # noqa: E402
    validate_repository,
)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_episode(batch: dict[str, object], action_id: str) -> dict[str, object]:
    return next(
        row
        for row in batch["subject"]["episodes"]
        if action_id in row["primary_action_ids"]
    )


def reseal_episode(batch: dict[str, object], episode: dict[str, object]) -> None:
    sealed = seal(episode, "episode_subject_sha256")
    episode.clear()
    episode.update(sealed)
    sealed_batch = seal(batch, "episode_candidate_subject_sha256")
    batch.clear()
    batch.update(sealed_batch)


def merge_singletons(
    batch: dict[str, object], first_action_id: str, second_action_id: str
) -> None:
    subject = batch["subject"]
    first = find_episode(batch, first_action_id)
    second = find_episode(batch, second_action_id)
    first["actions"] += second["actions"]
    first["actions"].sort(
        key=lambda row: (row["official_action_date"], row["action_id"])
    )
    first["primary_action_ids"] = [row["action_id"] for row in first["actions"]]
    first["grouping_type"] = "cross_measure"
    first["direction_derivation"]["accepted_position_effects_by_action"].update(
        second["direction_derivation"]["accepted_position_effects_by_action"]
    )
    subject["episodes"].remove(second)
    for row in subject["action_accounting"]:
        if row["action_id"] == second_action_id:
            row["primary_episode_id"] = first["episode_id"]
            sealed_row = seal(row, "accounting_subject_sha256")
            row.clear()
            row.update(sealed_row)
    subject["episode_count"] -= 1
    subject["single_action_episode_count"] -= 2
    subject["multi_action_episode_count"] += 1
    subject["cross_measure_episode_count"] += 1
    reseal_episode(batch, first)


def validate(batch: dict[str, object]) -> dict[str, object]:
    return validate_candidate_batch(
        batch=batch,
        implementation=load(IMPLEMENTATION_PATH),
        candidate_artifact=load(CANDIDATE_PATH),
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id=None,
    )


class M12EEnvironmentEnergyPolicyEpisodeCandidateTests(unittest.TestCase):
    def test_repository_package_is_exact_63_singletons(self) -> None:
        result = validate_repository()
        self.assertEqual(result["episode_count"], 63)
        self.assertEqual(result["single_action_episode_count"], 63)
        self.assertEqual(result["multi_action_episode_count"], 0)
        self.assertEqual(result["cross_measure_episode_count"], 0)
        self.assertEqual(result["assigned_action_count"], 63)

    def test_deterministic_regeneration(self) -> None:
        self.assertEqual(build(check=True)["episode_count"], 63)

    def test_generic_schema_accepts_historical_and_current_batches(self) -> None:
        validator = Draft7Validator(load(GENERIC_BATCH_SCHEMA_PATH))
        self.assertEqual(list(validator.iter_errors(load(M11_BATCH_PATH))), [])
        self.assertEqual(list(validator.iter_errors(load(BATCH_PATH))), [])

    def test_shared_cra_mechanism_cannot_create_episode(self) -> None:
        batch = load(BATCH_PATH)
        merge_singletons(batch, "house:119:1:110", "house:119:1:112")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "same-topic or parent-package overreach"
        ):
            validate(batch)

    def test_common_topic_or_direction_without_relationship_cannot_group(self) -> None:
        batch = load(BATCH_PATH)
        merge_singletons(batch, "house:119:1:18", "house:119:1:19")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError,
            "cross-measure grouping lacks governed semantic evidence",
        ):
            validate(batch)

    def test_not_voting_cannot_create_directional_episode(self) -> None:
        batch = load(BATCH_PATH)
        episode = find_episode(batch, "house:119:2:136")
        episode["member_direction_candidate"] = "opposes_policy_proposition"
        reseal_episode(batch, episode)
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError,
            "episode direction not derived from accepted meaning/effect",
        ):
            validate(batch)

    def test_not_voting_is_accounted_for_nondirectionally(self) -> None:
        episode = find_episode(load(BATCH_PATH), "house:119:2:136")
        self.assertEqual(
            episode["member_direction_candidate"], "non_directional_not_voting"
        )
        self.assertEqual(episode["primary_action_ids"], ["house:119:2:136"])

    def test_broad_package_cannot_be_split_into_component_proposition(self) -> None:
        batch = load(BATCH_PATH)
        episode = find_episode(batch, "house:119:1:25")
        episode["policy_proposition"] = (
            "Whether to support one selected forest-management component of H.R. 471."
        )
        reseal_episode(batch, episode)
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError,
            "singleton proposition differs from accepted action meaning",
        ):
            validate(batch)

    def test_second_broad_package_remains_indivisible(self) -> None:
        episode = find_episode(load(BATCH_PATH), "house:119:1:330")
        self.assertEqual(episode["primary_action_ids"], ["house:119:1:330"])
        self.assertTrue(
            any(
                "whole-package" in value.lower()
                for value in episode["material_limitations"]
            )
        )

    def test_missing_or_duplicated_action_rejected(self) -> None:
        batch = load(BATCH_PATH)
        batch["subject"]["episodes"].remove(find_episode(batch, "house:119:1:18"))
        batch = seal(batch, "episode_candidate_subject_sha256")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "accepted action omitted"
        ):
            validate(batch)

    def test_decision_template_is_entirely_empty(self) -> None:
        decision = load(DECISION_PATH)
        self.assertEqual(decision["decision_count"], 63)
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
            batch = load(BATCH_PATH)
            batch["subject"]["episodes"][0][field] = "forbidden"
            errors = list(
                Draft7Validator(load(GENERIC_BATCH_SCHEMA_PATH)).iter_errors(batch)
            )
            self.assertTrue(errors, field)

    def test_downstream_authority_leakage_rejected(self) -> None:
        batch = load(BATCH_PATH)
        batch["subject"]["downstream_authorizations"]["episode_acceptance"] = True
        batch = seal(batch, "episode_candidate_subject_sha256")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "downstream authority leakage"
        ):
            validate(batch)


if __name__ == "__main__":
    unittest.main()
