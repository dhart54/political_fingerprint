from __future__ import annotations

from copy import deepcopy
import unittest

from backend.app.etl.full_record_synthesis_decisions import (
    SynthesisDecisionError,
    seal,
    validate_implementation,
)
from backend.scripts.build_m11j_national_security_synthesis_acceptance import (
    ASSISTANCE_ID,
    WAR_POWERS_ID,
    build_authority,
    build_implementation,
    preflight,
)


class SynthesisDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package, cls.template, cls.m11h_authority, cls.m11h_implementation = (
            preflight()
        )
        cls.authority = build_authority(cls.package, cls.template)
        cls.implementation = build_implementation(
            cls.package,
            cls.template,
            cls.authority,
            cls.m11h_authority,
            cls.m11h_implementation,
        )
        cls.by_id = {
            row["synthesis_candidate_id"]: index
            for index, row in enumerate(
                cls.implementation["subject"]["implementation_records"]
            )
        }

    def reseal_record(self, value, candidate_id: str) -> None:
        index = self.by_id[candidate_id]
        value["subject"]["implementation_records"][index] = seal(
            value["subject"]["implementation_records"][index],
            "record_subject_sha256",
        )

    def assert_rejected(self, mutate) -> None:
        value = deepcopy(self.implementation)
        mutate(value)
        value = seal(value, "implementation_subject_sha256")
        with self.assertRaises(SynthesisDecisionError):
            validate_implementation(
                value,
                authority=self.authority,
                package=self.package,
                decision_template=self.template,
                m11h_authority=self.m11h_authority,
                m11h_implementation=self.m11h_implementation,
            )

    def test_valid_exact_decisions(self) -> None:
        result = validate_implementation(
            self.implementation,
            authority=self.authority,
            package=self.package,
            decision_template=self.template,
            m11h_authority=self.m11h_authority,
            m11h_implementation=self.m11h_implementation,
        )
        self.assertEqual(
            result["decision_accounting"],
            {
                "accept_candidate_as_written": 1,
                "accept_with_bounded_revision": 1,
                "rejected": 0,
                "unresolved": 0,
            },
        )
        self.assertEqual(result["final_accounting"]["standalone_proposition_count"], 7)

    def test_modified_accepted_as_written_synthesis_fails(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[WAR_POWERS_ID]]
            row["implemented_synthesis_content"]["proposition"] += " Changed."
            self.reseal_record(value, WAR_POWERS_ID)

        self.assert_rejected(mutate)

    def test_revision_beyond_human_scope_fails(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[ASSISTANCE_ID]]
            row["implemented_synthesis_content"]["synthesis_type"] = "uniform_direction"
            self.reseal_record(value, ASSISTANCE_ID)

        self.assert_rejected(mutate)

    def test_changed_input_proposition_fails(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[ASSISTANCE_ID]]
            row["behavioral_proposition_lineage"][0]["proposition_id"] = "replacement"
            self.reseal_record(value, ASSISTANCE_ID)

        self.assert_rejected(mutate)

    def test_changed_relationship_role_fails(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[ASSISTANCE_ID]]
            row["behavioral_proposition_lineage"][2]["relationship_role"] = (
                "primary_support"
            )
            self.reseal_record(value, ASSISTANCE_ID)

        self.assert_rejected(mutate)

    def test_excluded_notable_cannot_become_primary(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[ASSISTANCE_ID]]
            row["implemented_synthesis_content"]["input_bindings"][2][
                "relationship_role"
            ] = "primary_support"
            self.reseal_record(value, ASSISTANCE_ID)

        self.assert_rejected(mutate)

    def test_standalone_proposition_injection_fails(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[WAR_POWERS_ID]]
            row["behavioral_proposition_lineage"].append(
                {
                    "proposition_id": "pattern-fisa-title-vii-extension-opposition",
                    "relationship_role": "primary_support",
                }
            )
            self.reseal_record(value, WAR_POWERS_ID)

        self.assert_rejected(mutate)

    def test_raw_episode_or_action_injection_fails(self) -> None:
        for key, value in (
            ("unique_episode_ids", "synthetic-episode"),
            ("unique_action_ids", "synthetic-action"),
        ):
            with self.subTest(key=key):

                def mutate(document, key=key, injected=value):
                    row = document["subject"]["implementation_records"][
                        self.by_id[WAR_POWERS_ID]
                    ]
                    row["underlying_evidence"][key].append(injected)
                    self.reseal_record(document, WAR_POWERS_ID)

                self.assert_rejected(mutate)

    def test_inflated_underlying_count_fails(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[WAR_POWERS_ID]]
            row["underlying_evidence"]["unique_episode_count"] += 1
            self.reseal_record(value, WAR_POWERS_ID)

        self.assert_rejected(mutate)

    def test_source_mixed_metadata_cannot_be_sole_semantic_basis(self) -> None:
        def mutate(value):
            row = value["subject"]["implementation_records"][self.by_id[ASSISTANCE_ID]]
            guard = row["source_direction_semantic_guard"]
            guard["semantic_claim_basis"] = "source_direction_metadata_only"
            guard["mixed_direction_alone_establishes_mixed_policy_orientation"] = True
            self.reseal_record(value, ASSISTANCE_ID)

        self.assert_rejected(mutate)

    def test_public_or_production_authority_leak_fails(self) -> None:
        for key in (
            "public_wording",
            "publication",
            "production_persistence",
            "database_writes",
            "production_writes",
            "deployment",
        ):
            with self.subTest(key=key):

                def mutate(value, key=key):
                    value["subject"]["downstream_authorizations"][key] = True

                self.assert_rejected(mutate)


if __name__ == "__main__":
    unittest.main()
