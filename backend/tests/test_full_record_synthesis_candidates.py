from __future__ import annotations

import copy
import unittest

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import digest, seal
from backend.app.etl.full_record_synthesis_candidates import (
    SynthesisCandidateError,
    compile_synthesis_candidate_package,
    validate_synthesis_candidate_package,
)
from backend.scripts.build_m11i_national_security_synthesis_candidates import build


def synthetic_inputs() -> tuple[dict, dict, list[dict], list[dict], dict]:
    source_specs = [
        ("pattern-a", "repeated_pattern", "support", "primary", ["episode-a"]),
        ("pattern-b", "repeated_pattern", "support", "primary", ["episode-b"]),
        ("notable-c", "notable_choice", "opposition", "excluded", ["episode-c"]),
    ]
    records = []
    decisions = []
    for (
        proposition_id,
        proposition_type,
        direction,
        relevance,
        episodes,
    ) in source_specs:
        content = {
            "proposition_id": proposition_id,
            "proposition_type": proposition_type,
            "direction": direction,
            "conclusion_relevance": relevance,
            "proposition": f"Accepted {proposition_id}",
            "evidence_episode_ids": episodes,
            "evidence_action_ids": [f"action-{episodes[0][-1]}"],
        }
        decision = seal(
            {
                "proposition_id": proposition_id,
                "candidate_proposition_content_sha256": digest(content),
                "decision": "accept_candidate_as_written",
            },
            "decision_subject_sha256",
        )
        decisions.append(decision)
        records.append(
            seal(
                {
                    "record_id": f"record-{proposition_id}",
                    "proposition_id": proposition_id,
                    "accepted_candidate_content": content,
                    "accepted_candidate_content_sha256": digest(content),
                    "authority_decision_subject_sha256": decision[
                        "decision_subject_sha256"
                    ],
                    "canonical_internal_behavioral_semantic_ir": True,
                },
                "record_subject_sha256",
            )
        )
    authority = seal(
        {
            "artifact_id": "synthetic-behavioral-authority",
            "accepted": True,
            "canonical_internal_behavioral_semantic_ir_authority": True,
            "subject": {"proposition_decisions": decisions},
        },
        "authority_subject_sha256",
    )
    implementation = seal(
        {
            "artifact_id": "synthetic-behavioral-implementation",
            "accepted_human_decisions_implemented": True,
            "canonical_internal_behavioral_semantic_ir": True,
            "subject": {
                "authority_binding": {
                    "artifact_id": authority["artifact_id"],
                    "authority_subject_sha256": authority["authority_subject_sha256"],
                },
                "implementation_records": records,
                "accepted_episode_disposition_ledger": [
                    {"episode_id": f"episode-{suffix}", "primary_proposition_id": pid}
                    for suffix, pid in (
                        ("a", "pattern-a"),
                        ("b", "pattern-b"),
                        ("c", "notable-c"),
                    )
                ],
                "accepted_episode_disposition_accounting": {
                    "accepted_episode_count": 3
                },
                "blocked_actions": [],
            },
        },
        "implementation_subject_sha256",
    )
    definitions = [
        {
            "synthesis_candidate_id": "synthetic-uniform",
            "semantic_role": "synthesis",
            "synthesis_type": "uniform_direction",
            "direction": "support",
            "conclusion_relevance": "primary",
            "proposition": "Across two accepted patterns, the bounded direction is shared.",
            "inputs": [
                {
                    "proposition_id": "pattern-a",
                    "relationship_role": "primary_support",
                    "concise_input_summary": "First accepted pattern.",
                },
                {
                    "proposition_id": "pattern-b",
                    "relationship_role": "primary_support",
                    "concise_input_summary": "Second accepted pattern.",
                },
            ],
            "relationship_basis": {
                "basis_type": "shared_policy_mechanism_across_distinct_targets",
                "semantic_relationship": "The accepted patterns share one bounded mechanism and direction.",
                "topic_similarity_only": False,
            },
            "relationship_rationale": "Two accepted recurring patterns establish the relationship.",
            "why_synthesis_not_topic_grouping": "The relationship binds a shared mechanism and direction.",
            "material_limitations": ["The underlying targets remain distinct."],
            "competing_interpretation": "Keep the patterns separate.",
            "unresolved_ambiguity": "Human review remains required.",
            "prohibited_inferences": ["motive"],
        }
    ]
    accounting = [
        {
            "proposition_id": "pattern-a",
            "accounting_role": "primary_input",
            "reason": "Primary input.",
        },
        {
            "proposition_id": "pattern-b",
            "accounting_role": "primary_input",
            "reason": "Primary input.",
        },
        {
            "proposition_id": "notable-c",
            "accounting_role": "intentionally_standalone_no_safe_synthesis",
            "reason": "Excluded singleton remains standalone.",
        },
    ]
    subject = {"artifact_id": "synthetic-synthesis-package", "member_id": "TEST"}
    return authority, implementation, definitions, accounting, subject


def compile_synthetic() -> tuple[dict, dict, dict]:
    authority, implementation, definitions, accounting, subject = synthetic_inputs()
    package = compile_synthesis_candidate_package(
        authority=authority,
        implementation=implementation,
        candidate_definitions=definitions,
        proposition_accounting=accounting,
        subject=subject,
    )
    return package, authority, implementation


class FullRecordSynthesisCandidateTests(unittest.TestCase):
    def test_m11i_is_deterministic_and_non_authorizing(self) -> None:
        result = build(check=True)
        package = result["package"]
        self.assertEqual(package["subject"]["synthesis_candidate_count"], 2)
        self.assertEqual(package["subject"]["source_behavioral_proposition_count"], 15)
        self.assertFalse(any(package["subject"]["downstream_authorizations"].values()))

    def test_differently_sized_generic_fixture_passes(self) -> None:
        package, authority, implementation = compile_synthetic()
        result = validate_synthesis_candidate_package(
            package, authority=authority, implementation=implementation
        )
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["source_proposition_count"], 3)
        candidate = package["subject"]["synthesis_candidates"][0]
        self.assertEqual(candidate["underlying_evidence"]["unique_episode_count"], 2)

    def test_unknown_behavioral_proposition_fails(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        definitions[0]["inputs"][0]["proposition_id"] = "unknown"
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_changed_accepted_behavioral_proposition_fails(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        implementation["subject"]["implementation_records"][0][
            "accepted_candidate_content"
        ]["proposition"] = "Changed accepted meaning"
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_raw_episode_or_action_evidence_fails(self) -> None:
        for key in ("evidence_episode_ids", "evidence_action_ids", "raw_vote_ids"):
            with self.subTest(key=key):
                authority, implementation, definitions, accounting, subject = (
                    synthetic_inputs()
                )
                definitions[0][key] = ["malicious"]
                with self.assertRaises(SynthesisCandidateError):
                    compile_synthesis_candidate_package(
                        authority=authority,
                        implementation=implementation,
                        candidate_definitions=definitions,
                        proposition_accounting=accounting,
                        subject=subject,
                    )

    def test_contrast_or_no_safe_episode_cannot_enter_synthesis_evidence(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        implementation["subject"]["accepted_episode_disposition_ledger"][0][
            "primary_proposition_id"
        ] = None
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_excluded_notable_primary_promotion_fails(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        definitions[0]["inputs"].append(
            {
                "proposition_id": "notable-c",
                "relationship_role": "primary_support",
                "concise_input_summary": "Malicious promotion.",
            }
        )
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_topic_only_grouping_fails(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        definitions[0]["relationship_basis"]["topic_similarity_only"] = True
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_motive_or_ideology_claim_fails(self) -> None:
        for claim in ("The pattern is motivated by ideology.", "This proves pacifism."):
            with self.subTest(claim=claim):
                authority, implementation, definitions, accounting, subject = (
                    synthetic_inputs()
                )
                definitions[0]["proposition"] = claim
                with self.assertRaises(SynthesisCandidateError):
                    compile_synthesis_candidate_package(
                        authority=authority,
                        implementation=implementation,
                        candidate_definitions=definitions,
                        proposition_accounting=accounting,
                        subject=subject,
                    )

    def test_limiting_input_upgrade_fails(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        content = implementation["subject"]["implementation_records"][0][
            "accepted_candidate_content"
        ]
        content["conclusion_relevance"] = "limiting"
        implementation["subject"]["implementation_records"][0][
            "accepted_candidate_content_sha256"
        ] = digest(content)
        implementation["subject"]["implementation_records"][0] = seal(
            implementation["subject"]["implementation_records"][0],
            "record_subject_sha256",
        )
        implementation = seal(implementation, "implementation_subject_sha256")
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_double_counted_underlying_evidence_fails_rebuild(self) -> None:
        package, authority, implementation = compile_synthetic()
        changed = copy.deepcopy(package)
        changed["subject"]["synthesis_candidates"][0]["underlying_evidence"][
            "unique_episode_count"
        ] = 4
        changed["subject"]["synthesis_candidates"][0] = seal(
            changed["subject"]["synthesis_candidates"][0],
            "synthesis_candidate_subject_sha256",
        )
        changed = seal(changed, "synthesis_candidate_package_subject_sha256")
        with self.assertRaises(SynthesisCandidateError):
            validate_synthesis_candidate_package(
                changed, authority=authority, implementation=implementation
            )

    def test_incomplete_proposition_accounting_fails(self) -> None:
        authority, implementation, definitions, accounting, subject = synthetic_inputs()
        accounting.pop()
        with self.assertRaises(SynthesisCandidateError):
            compile_synthesis_candidate_package(
                authority=authority,
                implementation=implementation,
                candidate_definitions=definitions,
                proposition_accounting=accounting,
                subject=subject,
            )

    def test_downstream_authority_leakage_fails(self) -> None:
        package, authority, implementation = compile_synthetic()
        changed = copy.deepcopy(package)
        changed["subject"]["downstream_authorizations"]["publication"] = True
        changed = seal(changed, "synthesis_candidate_package_subject_sha256")
        with self.assertRaises(SynthesisCandidateError):
            validate_synthesis_candidate_package(
                changed, authority=authority, implementation=implementation
            )


if __name__ == "__main__":
    unittest.main()
