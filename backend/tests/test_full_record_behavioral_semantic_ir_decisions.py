from __future__ import annotations

from copy import deepcopy
import unittest

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (
    BehavioralSemanticIRDecisionError,
    digest,
    seal,
    validate_implementation,
)
from backend.scripts.build_m11h_national_security_semantic_ir_acceptance import (
    BLOCKED_ACTION_ID,
    build_authority,
    build_implementation,
    preflight,
)


def synthetic_generic_fixture():
    m11d_records = []
    for index in (1, 2):
        m11d_records.append(
            seal(
                {
                    "action_id": f"synthetic-action-{index}",
                    "record_id": f"synthetic-m11d-record-{index}",
                    "accepted_exact_action_meaning": f"Synthetic meaning {index}",
                    "accepted_exact_choice_position_effect": "supports_exact_choice",
                },
                "record_subject_sha256",
            )
        )
    m11d_subject = {"implementation_records": m11d_records}
    m11d = {
        "artifact_id": "synthetic-m11d-implementation",
        "subject": m11d_subject,
        "implementation_subject_sha256": digest(m11d_subject),
    }

    episodes = []
    for index, action in enumerate(m11d_records, start=1):
        episodes.append(
            seal(
                {
                    "episode_id": f"synthetic-episode-{index}",
                    "record_id": f"synthetic-m11f-record-{index}",
                    "member_direction": "supports_policy_proposition",
                    "primary_action_ids": [action["action_id"]],
                    "actions": [
                        {
                            "action_id": action["action_id"],
                            "accepted_interpretation_record_id": action["record_id"],
                            "accepted_interpretation_record_subject_sha256": action[
                                "record_subject_sha256"
                            ],
                            "accepted_exact_action_meaning": action[
                                "accepted_exact_action_meaning"
                            ],
                            "accepted_exact_choice_position_effect": action[
                                "accepted_exact_choice_position_effect"
                            ],
                        }
                    ],
                },
                "record_subject_sha256",
            )
        )
    m11f_authority = seal(
        {"artifact_id": "synthetic-m11f-authority", "subject": {}},
        "authority_subject_sha256",
    )
    m11f = seal(
        {
            "artifact_id": "synthetic-m11f-implementation",
            "subject": {
                "authority_binding": {
                    "artifact_id": m11f_authority["artifact_id"],
                    "authority_subject_sha256": m11f_authority[
                        "authority_subject_sha256"
                    ],
                },
                "m11d_implementation_binding": {
                    "artifact_id": m11d["artifact_id"],
                    "implementation_subject_sha256": m11d[
                        "implementation_subject_sha256"
                    ],
                },
                "implementation_records": episodes,
            },
        },
        "implementation_subject_sha256",
    )

    proposition = {
        "proposition_id": "synthetic-repeated-pattern",
        "proposition_type": "repeated_pattern",
        "direction": "support",
        "conclusion_relevance": "primary",
        "proposition": "Across two synthetic episodes, the member supported the choice.",
        "evidence_episode_ids": [row["episode_id"] for row in episodes],
        "evidence_action_ids": [row["primary_action_ids"][0] for row in episodes],
    }
    ledger = [
        {
            "episode_id": row["episode_id"],
            "disposition": "supports_proposed_repeated_pattern",
            "primary_proposition_id": proposition["proposition_id"],
            "reason": "Synthetic accepted evidence.",
        }
        for row in episodes
    ]
    candidate = {
        "artifact_id": "synthetic-behavioral-candidate",
        "candidate_subject_sha256": "synthetic-candidate-subject",
        "blocked_action_ids": [],
        "compiled_candidate_ir": {
            "proposition_graph": {"propositions": [proposition]},
            "episode_accounting": ledger,
        },
    }
    decision = seal(
        {
            "proposition_id": proposition["proposition_id"],
            "candidate_proposition_content_sha256": digest(proposition),
            "candidate_proposition_type": proposition["proposition_type"],
            "candidate_direction": proposition["direction"],
            "candidate_conclusion_relevance": proposition["conclusion_relevance"],
            "decision": "accept_candidate_as_written",
        },
        "decision_subject_sha256",
    )
    episode_accounting = {
        "accepted_episode_count": 2,
        "repeated_pattern_evidence_episode_count": 2,
        "trajectory_evidence_episode_count": 0,
        "notable_choice_evidence_episode_count": 0,
        "contrast_only_episode_count": 0,
        "no_safe_proposition_episode_count": 0,
        "primary_overlap_count": 0,
    }
    authority = seal(
        {
            "artifact_id": "synthetic-behavioral-authority",
            "accepted": True,
            "immutable": True,
            "canonical_internal_behavioral_semantic_ir_authority": True,
            "subject": {
                "candidate_binding": {
                    "artifact_id": candidate["artifact_id"],
                    "candidate_subject_sha256": candidate["candidate_subject_sha256"],
                },
                "proposition_decisions": [decision],
                "decision_accounting": {"accept_candidate_as_written": 1},
                "accepted_proposition_accounting": {
                    "total": 1,
                    "repeated_pattern": 1,
                    "trajectory": 0,
                    "notable_choice": 0,
                    "primary_conclusion_relevance": 1,
                    "limiting_conclusion_relevance": 0,
                    "excluded_conclusion_relevance": 0,
                },
                "accepted_episode_disposition_ledger": ledger,
                "accepted_episode_disposition_accounting": episode_accounting,
                "blocked_actions": [],
                "downstream_authorizations": {
                    "synthesis": False,
                    "publication": False,
                },
            },
        },
        "authority_subject_sha256",
    )
    implementation_record = seal(
        {
            "record_id": "synthetic-behavioral-implementation-record",
            "proposition_id": proposition["proposition_id"],
            "authority_decision_subject_sha256": decision["decision_subject_sha256"],
            "accepted_candidate_content": proposition,
            "accepted_candidate_content_sha256": digest(proposition),
            "evidence_lineage": [
                {
                    "episode_id": episode["episode_id"],
                    "episode_record_id": episode["record_id"],
                    "episode_record_subject_sha256": episode["record_subject_sha256"],
                    "member_direction": episode["member_direction"],
                    "accepted_action_lineage": [
                        {
                            "action_id": action["action_id"],
                            "accepted_interpretation_record_id": action[
                                "accepted_interpretation_record_id"
                            ],
                            "accepted_interpretation_record_subject_sha256": action[
                                "accepted_interpretation_record_subject_sha256"
                            ],
                        }
                        for action in episode["actions"]
                    ],
                }
                for episode in episodes
            ],
            "canonical_internal_behavioral_semantic_ir": True,
            "downstream_authorizations": {
                "synthesis": False,
                "publication": False,
            },
        },
        "record_subject_sha256",
    )
    implementation = seal(
        {
            "artifact_id": "synthetic-behavioral-implementation",
            "subject": {
                "authority_binding": {
                    "artifact_id": authority["artifact_id"],
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                },
                "m11f_authority_binding": {
                    "artifact_id": m11f_authority["artifact_id"],
                    "authority_subject_sha256": m11f_authority[
                        "authority_subject_sha256"
                    ],
                },
                "m11f_implementation_binding": {
                    "artifact_id": m11f["artifact_id"],
                    "implementation_subject_sha256": m11f[
                        "implementation_subject_sha256"
                    ],
                },
                "m11d_implementation_binding": {
                    "artifact_id": m11d["artifact_id"],
                    "implementation_subject_sha256": m11d[
                        "implementation_subject_sha256"
                    ],
                },
                "implementation_records": [implementation_record],
                "accepted_episode_disposition_ledger": ledger,
                "accepted_episode_disposition_accounting": episode_accounting,
                "final_accounting": {
                    "accepted_proposition_count": 1,
                    "repeated_pattern_count": 1,
                    "trajectory_count": 0,
                    "notable_choice_count": 0,
                    "primary_evidence_episode_count": 2,
                    "primary_overlap_count": 0,
                    "accepted_episode_count": 2,
                    "contrast_only_episode_count": 0,
                    "no_safe_proposition_episode_count": 0,
                    "blocked_action_count": 0,
                },
                "blocked_actions": [],
                "downstream_authorizations": {
                    "synthesis": False,
                    "publication": False,
                },
            },
        },
        "implementation_subject_sha256",
    )
    return candidate, authority, implementation, m11f_authority, m11f, m11d


class BehavioralSemanticIRDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (
            cls.candidate,
            _,
            cls.m11f_authority,
            cls.m11f_implementation,
            cls.m11d_implementation,
        ) = preflight()
        cls.authority = build_authority(cls.candidate)
        cls.implementation = build_implementation(
            cls.candidate,
            cls.authority,
            cls.m11f_authority,
            cls.m11f_implementation,
            cls.m11d_implementation,
        )

    def assert_rejected(self, mutate) -> None:
        value = deepcopy(self.implementation)
        mutate(value)
        value = seal(value, "implementation_subject_sha256")
        with self.assertRaises(BehavioralSemanticIRDecisionError):
            validate_implementation(
                value,
                authority=self.authority,
                candidate=self.candidate,
                m11f_authority=self.m11f_authority,
                m11f_implementation=self.m11f_implementation,
                m11d_implementation=self.m11d_implementation,
            )

    @staticmethod
    def reseal_record(value, index=0) -> None:
        value["subject"]["implementation_records"][index] = seal(
            value["subject"]["implementation_records"][index], "record_subject_sha256"
        )

    def test_valid_implementation(self) -> None:
        result = validate_implementation(
            self.implementation,
            authority=self.authority,
            candidate=self.candidate,
            m11f_authority=self.m11f_authority,
            m11f_implementation=self.m11f_implementation,
            m11d_implementation=self.m11d_implementation,
        )
        self.assertEqual(result["accepted_proposition_count"], 15)

    def test_differently_sized_generic_fixture_passes(self) -> None:
        candidate, authority, implementation, m11f_authority, m11f, m11d = (
            synthetic_generic_fixture()
        )
        result = validate_implementation(
            implementation,
            authority=authority,
            candidate=candidate,
            m11f_authority=m11f_authority,
            m11f_implementation=m11f,
            m11d_implementation=m11d,
        )
        self.assertEqual(result["accepted_proposition_count"], 1)
        self.assertEqual(result["accepted_episode_count"], 2)
        self.assertEqual(result["blocked_action_count"], 0)

    def test_differently_sized_generic_fixture_rejects_ledger_drift(self) -> None:
        candidate, authority, implementation, m11f_authority, m11f, m11d = (
            synthetic_generic_fixture()
        )
        implementation["subject"]["accepted_episode_disposition_ledger"][0][
            "primary_proposition_id"
        ] = None
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(BehavioralSemanticIRDecisionError):
            validate_implementation(
                implementation,
                authority=authority,
                candidate=candidate,
                m11f_authority=m11f_authority,
                m11f_implementation=m11f,
                m11d_implementation=m11d,
            )

    def test_differently_sized_generic_fixture_rejects_lineage_drift(self) -> None:
        candidate, authority, implementation, m11f_authority, m11f, m11d = (
            synthetic_generic_fixture()
        )
        record = implementation["subject"]["implementation_records"][0]
        record["evidence_lineage"][0]["accepted_action_lineage"][0][
            "accepted_interpretation_record_id"
        ] = "drifted-record"
        implementation["subject"]["implementation_records"][0] = seal(
            record, "record_subject_sha256"
        )
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(BehavioralSemanticIRDecisionError):
            validate_implementation(
                implementation,
                authority=authority,
                candidate=candidate,
                m11f_authority=m11f_authority,
                m11f_implementation=m11f,
                m11d_implementation=m11d,
            )

    def test_modified_meaning_fails(self) -> None:
        def mutate(v):
            v["subject"]["implementation_records"][0]["accepted_candidate_content"][
                "proposition"
            ] += " changed"
            self.reseal_record(v)

        self.assert_rejected(mutate)

    def test_type_or_direction_change_fails(self) -> None:
        def mutate(v):
            v["subject"]["implementation_records"][0]["accepted_candidate_content"][
                "direction"
            ] = "mixed"
            self.reseal_record(v)

        self.assert_rejected(mutate)

    def test_evidence_episode_add_remove_duplicate_or_replace_fails(self) -> None:
        for operation in ("add", "remove", "duplicate", "replace"):

            def mutate(v, operation=operation):
                row = v["subject"]["implementation_records"][0]
                if operation == "add":
                    row["evidence_lineage"].append(deepcopy(row["evidence_lineage"][0]))
                elif operation == "remove":
                    row["evidence_lineage"].pop()
                elif operation == "duplicate":
                    row["evidence_lineage"][1] = deepcopy(row["evidence_lineage"][0])
                else:
                    row["evidence_lineage"][0]["episode_id"] = "replacement"
                self.reseal_record(v)

            with self.subTest(operation=operation):
                self.assert_rejected(mutate)

    def test_evidence_action_without_episode_lineage_fails(self) -> None:
        def mutate(v):
            v["subject"]["implementation_records"][0]["evidence_lineage"][0][
                "accepted_action_lineage"
            ][0]["action_id"] = "house:119:1:999"
            self.reseal_record(v)

        self.assert_rejected(mutate)

    def test_limiting_or_excluded_promotion_fails(self) -> None:
        for relevance in ("limiting", "excluded"):
            index = next(
                i
                for i, row in enumerate(
                    self.implementation["subject"]["implementation_records"]
                )
                if row["accepted_candidate_content"]["conclusion_relevance"]
                == relevance
            )

            def mutate(v, index=index):
                v["subject"]["implementation_records"][index][
                    "accepted_candidate_content"
                ]["conclusion_relevance"] = "primary"
                self.reseal_record(v, index)

            with self.subTest(relevance=relevance):
                self.assert_rejected(mutate)

    def test_contrast_or_no_safe_episode_promotion_fails(self) -> None:
        def mutate(v):
            v["subject"]["accepted_episode_disposition_ledger"][0][
                "primary_proposition_id"
            ] = v["subject"]["implementation_records"][0]["proposition_id"]

        self.assert_rejected(mutate)

    def test_second_primary_owner_fails(self) -> None:
        def mutate(v):
            v["subject"]["implementation_records"][1]["evidence_lineage"][0] = deepcopy(
                v["subject"]["implementation_records"][0]["evidence_lineage"][0]
            )
            self.reseal_record(v, 1)

        self.assert_rejected(mutate)

    def test_structured_trajectory_change_fails(self) -> None:
        index = next(
            i
            for i, row in enumerate(
                self.implementation["subject"]["implementation_records"]
            )
            if row["accepted_candidate_content"]["proposition_type"] == "trajectory"
        )

        def mutate(v):
            v["subject"]["implementation_records"][index]["accepted_candidate_content"][
                "trajectory_change"
            ]["change_type"] = "changed"
            self.reseal_record(v, index)

        self.assert_rejected(mutate)

    def test_blocked_action_in_evidence_fails(self) -> None:
        def mutate(v):
            v["subject"]["implementation_records"][0]["accepted_candidate_content"][
                "evidence_action_ids"
            ][0] = BLOCKED_ACTION_ID
            self.reseal_record(v)

        self.assert_rejected(mutate)

    def test_downstream_authority_leakage_fails(self) -> None:
        def mutate(v):
            v["subject"]["downstream_authorizations"]["synthesis"] = True

        self.assert_rejected(mutate)


if __name__ == "__main__":
    unittest.main()
