"""Adversarial tests for full-record policy-episode decisions."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_decisions import (  # noqa: E402
    PolicyEpisodeDecisionError,
    require_cross_measure_continuity,
    seal,
    validate_implementation,
)
from backend.scripts.build_m11f_national_security_policy_episode_acceptance import (  # noqa: E402
    AUTHORITY_PATH,
    BLOCKED_ACTION_ID,
    IMPLEMENTATION_PATH,
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


class FullRecordPolicyEpisodeDecisionTests(unittest.TestCase):
    def test_repository_implementation_and_regeneration(self) -> None:
        self.assertEqual(
            validate(load(IMPLEMENTATION_PATH))["accepted_episode_count"], 81
        )
        self.assertEqual(build(check=True)["single_action_episode_count"], 81)

    def test_repeated_same_proposition_without_continuity_rejected(self) -> None:
        with self.assertRaisesRegex(PolicyEpisodeDecisionError, "continuity"):
            require_cross_measure_continuity(
                {"grouping_type": "cross_measure", "policy_proposition": "same"}
            )

    def test_cross_measure_allowed_with_explicit_legislative_path_continuity(
        self,
    ) -> None:
        require_cross_measure_continuity(
            {
                "grouping_type": "cross_measure",
                "legislative_event_continuity": {
                    "state": "established",
                    "same_legislative_path_or_event": True,
                    "evidence": [
                        "The second action is a chamber step on the same enacted measure."
                    ],
                },
            }
        )

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
