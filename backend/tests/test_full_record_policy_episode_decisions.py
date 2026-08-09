"""Adversarial tests for full-record policy-episode decisions."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_decisions import (  # noqa: E402
    DOWNSTREAM_AUTHORIZATIONS,
    PolicyEpisodeDecisionError,
    seal,
    validate_implementation,
)
from backend.scripts.build_m11f_national_security_policy_episode_acceptance import (  # noqa: E402
    AUTHORITY_PATH,
    BLOCKED_ACTION_ID,
    IMPLEMENTATION_PATH,
    IMPLEMENTATION_SCHEMA_PATH,
    M11D_IMPLEMENTATION_PATH,
    REJECTED_EPISODE_IDS,
    build,
)


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(bundle: dict[str, object]) -> dict[str, int]:
    return validate_implementation(
        bundle,
        authority=load(AUTHORITY_PATH),
        m11d_records=load(M11D_IMPLEMENTATION_PATH)["subject"][
            "implementation_records"
        ],
        blocked_action_id=BLOCKED_ACTION_ID,
        rejected_episode_ids=REJECTED_EPISODE_IDS,
    )


def reseal(bundle: dict[str, object]) -> dict[str, object]:
    return seal(bundle, "implementation_subject_sha256")


def synthetic_generic_fixture(
    grouping_type: str,
    *,
    continuity: dict[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    action_ids = ["house:119:1:900", "house:119:1:901"]
    measure_ids = (
        ["119:hr:9000", "119:hr:9000"]
        if grouping_type == "same_measure_multi_action"
        else ["119:hr:9000", "119:s:9000"]
    )
    m11d_records = []
    actions = []
    for action_id, measure_id in zip(action_ids, measure_ids, strict=True):
        source = {
            "action_id": action_id,
            "record_id": f"action-interpretation:{action_id}:v1",
            "accepted_exact_action_meaning": "The House choice was whether to advance the same bounded legislative path.",
            "accepted_exact_choice_position_effect": "supports_exact_choice",
            "accepted_limitations": ["Synthetic generic contract fixture."],
            "source_references": [f"synthetic:{action_id}"],
        }
        source = seal(source, "record_subject_sha256")
        m11d_records.append(source)
        actions.append(
            {
                "action_id": action_id,
                "exact_action_identity": measure_id,
                "accepted_interpretation_record_id": source["record_id"],
                "accepted_interpretation_record_subject_sha256": source[
                    "record_subject_sha256"
                ],
                "accepted_exact_action_meaning": source[
                    "accepted_exact_action_meaning"
                ],
                "accepted_exact_choice_position_effect": source[
                    "accepted_exact_choice_position_effect"
                ],
                "accepted_limitations": source["accepted_limitations"],
                "source_references": source["source_references"],
            }
        )
    episode_id = f"synthetic-{grouping_type}"
    decision = seal(
        {
            "episode_id": episode_id,
            "decision": "accept_candidate_as_written",
            "replacement_episode_ids": [],
        },
        "decision_subject_sha256",
    )
    authority = seal(
        {"subject": {"episode_decisions": [decision]}},
        "authority_subject_sha256",
    )
    record = {
        "episode_id": episode_id,
        "record_id": f"policy-episode:{episode_id}:v1",
        "source_candidate_episode_id": episode_id,
        "authority_subject_sha256": authority["authority_subject_sha256"],
        "authority_decision_subject_sha256": decision["decision_subject_sha256"],
        "policy_proposition": "Whether to advance the same bounded policy proposition.",
        "grouping_type": grouping_type,
        "primary_action_ids": action_ids,
        "actions": actions,
        "member_direction": "supports_policy_proposition",
        "direction_derivation": {
            "accepted_position_effects_by_action": {
                action_id: "supports_exact_choice" for action_id in action_ids
            }
        },
        "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
    }
    if continuity is not None:
        record["legislative_event_continuity"] = continuity
    record = seal(record, "record_subject_sha256")
    accounting = [
        seal(
            {
                "action_id": source["action_id"],
                "primary_episode_id": episode_id,
                "implementation_record_id": record["record_id"],
                "implementation_record_subject_sha256": record["record_subject_sha256"],
                "accepted_interpretation_record_id": source["record_id"],
                "accepted_interpretation_record_subject_sha256": source[
                    "record_subject_sha256"
                ],
                "primary_membership_count": 1,
            },
            "accounting_subject_sha256",
        )
        for source in m11d_records
    ]
    bundle = seal(
        {
            "subject": {
                "authority_binding": {
                    "authority_subject_sha256": authority["authority_subject_sha256"]
                },
                "implementation_records": [record],
                "action_accounting": accounting,
                "non_primary_relationship_evidence": [],
                "final_accounting": {
                    "accepted_action_count": 2,
                    "accepted_episode_count": 1,
                    "single_action_episode_count": 0,
                    "multi_action_episode_count": 1,
                    "cross_measure_episode_count": int(
                        grouping_type == "cross_measure"
                    ),
                    "ambiguous_or_unassigned_action_count": 0,
                    "blocked_action_count": 1,
                },
                "downstream_authorizations": deepcopy(DOWNSTREAM_AUTHORIZATIONS),
            }
        },
        "implementation_subject_sha256",
    )
    return bundle, authority, m11d_records


def validate_synthetic(
    bundle: dict[str, object],
    authority: dict[str, object],
    m11d_records: list[dict[str, object]],
) -> dict[str, int]:
    return validate_implementation(
        bundle,
        authority=authority,
        m11d_records=m11d_records,
        blocked_action_id="house:119:1:999",
        rejected_episode_ids=set(),
    )


class FullRecordPolicyEpisodeDecisionTests(unittest.TestCase):
    def test_repository_implementation_and_regeneration(self) -> None:
        self.assertEqual(
            validate(load(IMPLEMENTATION_PATH))["accepted_episode_count"], 81
        )
        self.assertEqual(build(check=True)["single_action_episode_count"], 81)

    def test_cross_measure_without_explicit_continuity_rejected(self) -> None:
        bundle, authority, m11d = synthetic_generic_fixture("cross_measure")
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "continuity"):
            validate_synthetic(bundle, authority, m11d)

    def test_proposition_equivalence_alone_still_rejected(self) -> None:
        bundle, authority, m11d = synthetic_generic_fixture("cross_measure")
        bundle["subject"]["implementation_records"][0]["semantic_grouping_evidence"] = [
            "Both measures state the same proposition."
        ]
        record = seal(
            bundle["subject"]["implementation_records"][0],
            "record_subject_sha256",
        )
        bundle["subject"]["implementation_records"][0] = record
        bundle = reseal(bundle)
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "continuity"):
            validate_synthetic(bundle, authority, m11d)

    def test_cross_measure_passes_actual_validator_with_continuity(self) -> None:
        bundle, authority, m11d = synthetic_generic_fixture(
            "cross_measure",
            continuity={
                "state": "established",
                "same_legislative_path_or_event": True,
                "evidence": [
                    "The second measure is the other chamber vehicle for the same legislative path."
                ],
            },
        )
        result = validate_synthetic(bundle, authority, m11d)
        self.assertEqual(result["cross_measure_episode_count"], 1)
        self.assertEqual(result["multi_action_episode_count"], 1)

    def test_same_measure_multi_action_passes_actual_validator(self) -> None:
        bundle, authority, m11d = synthetic_generic_fixture("same_measure_multi_action")
        result = validate_synthetic(bundle, authority, m11d)
        self.assertEqual(result["multi_action_episode_count"], 1)
        self.assertEqual(result["cross_measure_episode_count"], 0)

    def test_malformed_or_empty_continuity_rejected(self) -> None:
        malformed = [
            {
                "state": "proposed",
                "same_legislative_path_or_event": True,
                "evidence": ["Evidence."],
            },
            {
                "state": "established",
                "same_legislative_path_or_event": False,
                "evidence": ["Evidence."],
            },
            {
                "state": "established",
                "same_legislative_path_or_event": True,
                "evidence": [],
            },
            {
                "state": "established",
                "same_legislative_path_or_event": True,
                "evidence": [""],
            },
        ]
        for continuity in malformed:
            with self.subTest(continuity=continuity):
                bundle, authority, m11d = synthetic_generic_fixture(
                    "cross_measure", continuity=continuity
                )
                with self.assertRaisesRegex(PolicyEpisodeDecisionError, "continuity"):
                    validate_synthetic(bundle, authority, m11d)

    def test_schema_has_optional_conditional_continuity_object(self) -> None:
        schema = load(IMPLEMENTATION_SCHEMA_PATH)
        record = schema["properties"]["subject"]["properties"][
            "implementation_records"
        ]["items"]
        self.assertIn("legislative_event_continuity", record["properties"])
        self.assertNotIn("legislative_event_continuity", record["required"])
        self.assertEqual(
            record["allOf"][0]["then"]["required"],
            ["legislative_event_continuity"],
        )
        validator = Draft7Validator(schema)
        repository_bundle = load(IMPLEMENTATION_PATH)
        self.assertEqual(list(validator.iter_errors(repository_bundle)), [])
        cross_measure = deepcopy(repository_bundle)
        cross_measure["subject"]["implementation_records"][0]["grouping_type"] = (
            "cross_measure"
        )
        self.assertTrue(list(validator.iter_errors(cross_measure)))
        cross_measure["subject"]["implementation_records"][0][
            "legislative_event_continuity"
        ] = {
            "state": "established",
            "same_legislative_path_or_event": True,
            "evidence": ["Synthetic schema representation evidence."],
        }
        self.assertEqual(list(validator.iter_errors(cross_measure)), [])

    def test_rejected_group_cannot_remain_primary(self) -> None:
        bundle = load(IMPLEMENTATION_PATH)
        record = bundle["subject"]["implementation_records"][0]
        record["episode_id"] = sorted(REJECTED_EPISODE_IDS)[0]
        record = seal(record, "record_subject_sha256")
        bundle["subject"]["implementation_records"][0] = record
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "rejected grouping"):
            validate(reseal(bundle))

    def test_reassigned_action_must_appear_exactly_once(self) -> None:
        bundle = load(IMPLEMENTATION_PATH)
        duplicated = deepcopy(bundle["subject"]["implementation_records"][0])
        duplicated["episode_id"] += "-duplicate"
        duplicated = seal(duplicated, "record_subject_sha256")
        bundle["subject"]["implementation_records"].append(duplicated)
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "more than once"):
            validate(reseal(bundle))

    def test_relationship_evidence_cannot_change_primary_accounting(self) -> None:
        bundle = load(IMPLEMENTATION_PATH)
        relationship = bundle["subject"]["non_primary_relationship_evidence"][0]
        relationship["primary_authority_effect"] = True
        relationship = seal(relationship, "relationship_subject_sha256")
        bundle["subject"]["non_primary_relationship_evidence"][0] = relationship
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "relationship altered"):
            validate(reseal(bundle))


if __name__ == "__main__":
    unittest.main()
