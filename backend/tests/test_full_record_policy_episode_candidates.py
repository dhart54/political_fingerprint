"""Adversarial tests for the generic full-record policy-episode candidate contract."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    PolicyEpisodeCandidateError,
    seal,
    validate_candidate_batch,
)
from backend.scripts.build_m11e_national_security_policy_episode_candidates import (  # noqa: E402
    BATCH_PATH,
    BATCH_SCHEMA_PATH,
    CANDIDATE_PATH,
    DECISION_PATH,
    DECISION_SCHEMA_PATH,
    IMPLEMENTATION_PATH,
    PERMITTED_CROSS_MEASURE_SETS,
    PROHIBITED_GROUPED_SETS,
    build,
)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(batch: dict[str, object]) -> dict[str, object]:
    return validate_candidate_batch(
        batch=batch,
        implementation=load(IMPLEMENTATION_PATH),
        candidate_artifact=load(CANDIDATE_PATH),
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id="house:119:2:278",
    )


def find_episode(batch: dict[str, object], action_id: str) -> dict[str, object]:
    return next(
        episode
        for episode in batch["subject"]["episodes"]
        if action_id in episode["primary_action_ids"]
    )


def merge_singletons(
    batch: dict[str, object], first_action_id: str, second_action_id: str
) -> None:
    subject = batch["subject"]
    first = find_episode(batch, first_action_id)
    second = find_episode(batch, second_action_id)
    first["primary_action_ids"] += second["primary_action_ids"]
    first["actions"] += second["actions"]
    first["actions"].sort(
        key=lambda row: (row["official_action_date"], row["action_id"])
    )
    first["primary_action_ids"] = [row["action_id"] for row in first["actions"]]
    first["grouping_type"] = "cross_measure"
    first["direction_derivation"]["accepted_position_effects_by_action"].update(
        second["direction_derivation"]["accepted_position_effects_by_action"]
    )
    sealed = seal(first, "episode_subject_sha256")
    first.clear()
    first.update(sealed)
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
    sealed_batch = seal(batch, "episode_candidate_subject_sha256")
    batch.clear()
    batch.update(sealed_batch)


class FullRecordPolicyEpisodeCandidateTests(unittest.TestCase):
    def test_repository_candidate_package(self) -> None:
        result = validate(load(BATCH_PATH))
        self.assertEqual(result["episode_count"], 74)
        self.assertEqual(result["single_action_episode_count"], 70)
        self.assertEqual(result["multi_action_episode_count"], 4)
        self.assertEqual(result["cross_measure_episode_count"], 4)
        self.assertEqual(result["assigned_action_count"], 81)
        self.assertEqual(result["blocked_count"], 1)

    def test_deterministic_regeneration(self) -> None:
        self.assertEqual(build(check=True)["episode_count"], 74)

    def test_same_topic_different_policy_grouping_rejected(self) -> None:
        batch = load(BATCH_PATH)
        merge_singletons(batch, "house:119:1:209", "house:119:1:255")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "same-topic or parent-package overreach"
        ):
            validate(batch)

    def test_parent_package_overreach_rejected(self) -> None:
        batch = load(BATCH_PATH)
        merge_singletons(batch, "house:119:1:208", "house:119:1:212")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "same-topic or parent-package overreach"
        ):
            validate(batch)

    def test_cross_measure_grouping_without_semantic_evidence_rejected(self) -> None:
        batch = load(BATCH_PATH)
        merge_singletons(batch, "house:119:1:115", "house:119:1:116")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError,
            "cross-measure grouping lacks governed semantic evidence",
        ):
            validate(batch)

    def test_direction_not_derived_from_raw_vote_rejected(self) -> None:
        batch = load(BATCH_PATH)
        episode = find_episode(batch, "house:119:1:115")
        episode["member_direction_candidate"] = "opposes_policy_proposition"
        sealed = seal(episode, "episode_subject_sha256")
        episode.clear()
        episode.update(sealed)
        batch = seal(batch, "episode_candidate_subject_sha256")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError,
            "episode direction not derived from accepted meaning/effect",
        ):
            validate(batch)

    def test_blocked_action_inclusion_rejected(self) -> None:
        batch = load(BATCH_PATH)
        episode = find_episode(batch, "house:119:1:115")
        episode["primary_action_ids"].append("house:119:2:278")
        fake = deepcopy(episode["actions"][0])
        fake["action_id"] = "house:119:2:278"
        episode["actions"].append(fake)
        sealed = seal(episode, "episode_subject_sha256")
        episode.clear()
        episode.update(sealed)
        batch = seal(batch, "episode_candidate_subject_sha256")
        with self.assertRaisesRegex(PolicyEpisodeCandidateError, "blocked action"):
            validate(batch)

    def test_downstream_authority_leakage_rejected(self) -> None:
        batch = load(BATCH_PATH)
        batch["subject"]["downstream_authorizations"]["episode_acceptance"] = True
        batch = seal(batch, "episode_candidate_subject_sha256")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "downstream authority leakage"
        ):
            validate(batch)

    def test_duplicate_or_omitted_action_rejected(self) -> None:
        batch = load(BATCH_PATH)
        episode = find_episode(batch, "house:119:1:115")
        batch["subject"]["episodes"].remove(episode)
        batch = seal(batch, "episode_candidate_subject_sha256")
        with self.assertRaisesRegex(
            PolicyEpisodeCandidateError, "accepted action omitted"
        ):
            validate(batch)

    def test_empty_human_decision_template(self) -> None:
        decision = load(DECISION_PATH)
        self.assertEqual(decision["decision_count"], 74)
        self.assertEqual(
            decision["decision_state"], "awaiting_human_policy_episode_review"
        )
        self.assertTrue(
            all(row["selected_decision"] is None for row in decision["decisions"])
        )

    def test_closed_schemas_reject_unknown_fields(self) -> None:
        for artifact_path, schema_path in (
            (BATCH_PATH, BATCH_SCHEMA_PATH),
            (DECISION_PATH, DECISION_SCHEMA_PATH),
        ):
            artifact = load(artifact_path)
            artifact["invented_authority"] = True
            errors = list(Draft7Validator(load(schema_path)).iter_errors(artifact))
            self.assertTrue(errors)
            self.assertTrue(
                any("Additional properties" in error.message for error in errors)
            )


if __name__ == "__main__":
    unittest.main()
