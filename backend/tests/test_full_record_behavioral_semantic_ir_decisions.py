from __future__ import annotations

from copy import deepcopy
import unittest

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (
    BehavioralSemanticIRDecisionError,
    seal,
    validate_implementation,
)
from backend.scripts.build_m11h_national_security_semantic_ir_acceptance import (
    BLOCKED_ACTION_ID,
    build_authority,
    build_implementation,
    preflight,
)


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
                blocked_action_id=BLOCKED_ACTION_ID,
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
            blocked_action_id=BLOCKED_ACTION_ID,
        )
        self.assertEqual(result["accepted_proposition_count"], 15)

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
