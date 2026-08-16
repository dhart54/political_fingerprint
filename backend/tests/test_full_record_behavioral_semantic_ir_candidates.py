from __future__ import annotations

import copy
from collections import Counter
import unittest

from backend.app.semantic_ir.compiler import (
    SemanticCompilerInputError,
    compile_behavioral_candidate_ir,
)
from backend.scripts.build_m11g_national_security_behavioral_semantic_ir_candidates import (
    build,
    build_input,
    preflight,
)


class BehavioralSemanticIrCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiler_input, _ = build_input(preflight())

    def test_m11g_is_deterministic_and_non_authorizing(self) -> None:
        result = build(True)
        graph = result["graph"]["compiled_candidate_ir"]
        self.assertEqual(len(graph["episode_accounting"]), 81)
        self.assertEqual(
            Counter(
                row["proposition_type"]
                for row in graph["proposition_graph"]["propositions"]
            ),
            Counter({"repeated_pattern": 8, "trajectory": 1, "notable_choice": 6}),
        )
        self.assertEqual(graph["synthesis_propositions"], [])
        self.assertFalse(any(graph["downstream_authorizations"].values()))

    def test_episode_lineage_is_primary(self) -> None:
        graph = compile_behavioral_candidate_ir(copy.deepcopy(self.compiler_input))
        episodes = {row["episode_id"]: row for row in self.compiler_input["episodes"]}
        for proposition in graph["proposition_graph"]["propositions"]:
            expected = sorted(
                action_id
                for episode_id in proposition["evidence_episode_ids"]
                for action_id in episodes[episode_id]["primary_action_ids"]
            )
            self.assertEqual(proposition["evidence_action_ids"], expected)

    def test_repeated_pattern_requires_two_semantically_bound_episodes(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        changed["proposition_candidates"][0]["evidence_episode_ids"] = changed[
            "proposition_candidates"
        ][0]["evidence_episode_ids"][:1]
        with self.assertRaises(SemanticCompilerInputError):
            compile_behavioral_candidate_ir(changed)

    def test_topic_or_mechanism_only_relationship_evidence_is_rejected(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        proposition = next(
            row
            for row in changed["proposition_candidates"]
            if row["proposition_type"] == "repeated_pattern"
        )
        evidence = changed["relationship_evidence_by_proposition"][
            proposition["proposition_id"]
        ]
        evidence["insufficient_bases_rejected"] = [
            "shared_topic",
            "shared_cra_mechanism",
        ]
        with self.assertRaisesRegex(SemanticCompilerInputError, "incomplete"):
            compile_behavioral_candidate_ir(changed)

    def test_tampered_accepted_episode_record_is_rejected(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        changed["episodes"][0]["primary_action_ids"] = ["invented-component"]
        with self.assertRaisesRegex(SemanticCompilerInputError, "seal differs"):
            compile_behavioral_candidate_ir(changed)

    @staticmethod
    def _generic_input(
        *,
        before: str = "opposes_policy_proposition",
        after: str = "supports_policy_proposition",
    ) -> dict:
        episodes = [
            {
                "episode_id": "before",
                "canonical_internal_policy_episode": True,
                "member_direction": before,
                "primary_action_ids": ["action-before"],
                "actions": [{"official_action_date": "2025-01-01"}],
            },
            {
                "episode_id": "after",
                "canonical_internal_policy_episode": True,
                "member_direction": after,
                "primary_action_ids": ["action-after"],
                "actions": [{"official_action_date": "2026-01-01"}],
            },
        ]
        return {
            "subject": {"member_id": "TEST"},
            "episodes": episodes,
            "blocked_action_ids": [],
            "relationship_evidence_by_proposition": {},
            "proposition_candidates": [
                {
                    "proposition_id": "trajectory-test",
                    "proposition_type": "trajectory",
                    "proposition": "A bounded direction change.",
                    "direction": "mixed" if before != after else "support",
                    "evidence_episode_ids": ["before", "after"],
                    "episode_semantic_evidence": {
                        "before": "Accepted before meaning.",
                        "after": "Accepted after meaning.",
                    },
                    "overlap_relationships": [],
                    "trajectory_change": {
                        "change_type": "direction_change",
                        "ordered_evidence_episode_ids": ["before", "after"],
                        "accepted_chronology": [
                            {"episode_id": "before", "accepted_date": "2025-01-01"},
                            {"episode_id": "after", "accepted_date": "2026-01-01"},
                        ],
                        "accepted_before_direction": before,
                        "accepted_after_direction": after,
                        "bounded_change_description": "The accepted direction changed across successive annual packages.",
                    },
                }
            ],
            "episode_accounting": [
                {"episode_id": "before", "primary_proposition_id": "trajectory-test"},
                {"episode_id": "after", "primary_proposition_id": "trajectory-test"},
            ],
        }

    def test_valid_structured_direction_change_trajectory(self) -> None:
        graph = compile_behavioral_candidate_ir(self._generic_input())
        proposition = graph["proposition_graph"]["propositions"][0]
        self.assertEqual(proposition["direction"], "mixed")

    def test_trajectory_rejects_reversed_chronology(self) -> None:
        changed = self._generic_input()
        proposition = changed["proposition_candidates"][0]
        proposition["evidence_episode_ids"].reverse()
        change = proposition["trajectory_change"]
        change["ordered_evidence_episode_ids"].reverse()
        change["accepted_chronology"].reverse()
        change["accepted_before_direction"] = "supports_policy_proposition"
        change["accepted_after_direction"] = "opposes_policy_proposition"
        with self.assertRaisesRegex(
            SemanticCompilerInputError, "strictly chronological"
        ):
            compile_behavioral_candidate_ir(changed)

    def test_trajectory_rejects_duplicate_episodes(self) -> None:
        changed = self._generic_input()
        changed["proposition_candidates"][0]["evidence_episode_ids"][1] = "before"
        with self.assertRaisesRegex(SemanticCompilerInputError, "duplicate episode"):
            compile_behavioral_candidate_ir(changed)

    def test_trajectory_rejects_claimed_direction_mismatches(self) -> None:
        for field, value in (
            ("accepted_before_direction", "supports_policy_proposition"),
            ("accepted_after_direction", "opposes_policy_proposition"),
        ):
            with self.subTest(field=field):
                changed = self._generic_input()
                changed["proposition_candidates"][0]["trajectory_change"][field] = value
                with self.assertRaises(SemanticCompilerInputError):
                    compile_behavioral_candidate_ir(changed)

    def test_trajectory_rejects_identical_directions(self) -> None:
        changed = self._generic_input(
            before="supports_policy_proposition", after="supports_policy_proposition"
        )
        with self.assertRaisesRegex(SemanticCompilerInputError, "differing directions"):
            compile_behavioral_candidate_ir(changed)

    def test_trajectory_rejects_chronology_without_substantive_change(self) -> None:
        changed = self._generic_input()
        changed["proposition_candidates"][0]["trajectory_change"][
            "bounded_change_description"
        ] = ""
        with self.assertRaisesRegex(SemanticCompilerInputError, "substantive-change"):
            compile_behavioral_candidate_ir(changed)

    def test_canonical_mixed_episode_direction_compiles(self) -> None:
        payload = {
            "subject": {"member_id": "TEST"},
            "episodes": [
                {
                    "episode_id": "mixed-episode",
                    "canonical_internal_policy_episode": True,
                    "member_direction": "mixed_on_episode_choices",
                    "primary_action_ids": ["action-a", "action-b"],
                    "actions": [
                        {"official_action_date": "2026-01-01"},
                        {"official_action_date": "2026-01-01"},
                    ],
                }
            ],
            "blocked_action_ids": [],
            "relationship_evidence_by_proposition": {},
            "proposition_candidates": [
                {
                    "proposition_id": "mixed-notable",
                    "proposition_type": "notable_choice",
                    "proposition": "A bounded mixed episode.",
                    "direction": "mixed",
                    "evidence_episode_ids": ["mixed-episode"],
                    "episode_semantic_evidence": {
                        "mixed-episode": "Accepted mixed choices."
                    },
                    "overlap_relationships": [],
                    "trajectory_change": None,
                }
            ],
            "episode_accounting": [
                {
                    "episode_id": "mixed-episode",
                    "primary_proposition_id": "mixed-notable",
                }
            ],
        }
        for episode_direction in (
            "mixed_on_episode_choices",
            "mixed_or_non_directional",
        ):
            with self.subTest(episode_direction=episode_direction):
                changed = copy.deepcopy(payload)
                changed["episodes"][0]["member_direction"] = episode_direction
                graph = compile_behavioral_candidate_ir(changed)
                self.assertEqual(
                    graph["proposition_graph"]["propositions"][0]["direction"],
                    "mixed",
                )

    def test_non_directional_episode_cannot_enter_directional_evidence(self) -> None:
        changed = self._generic_input()
        proposition = changed["proposition_candidates"][0]
        proposition["proposition_type"] = "repeated_pattern"
        proposition["trajectory_change"] = None
        changed["episodes"][0]["member_direction"] = "non_directional_not_voting"
        changed["relationship_evidence_by_proposition"] = {
            proposition["proposition_id"]: {
                "shared_bounded_choice": "Synthetic bounded repeated choice.",
                "episode_support": {
                    "before": "Accepted before meaning.",
                    "after": "Accepted after meaning.",
                },
                "insufficient_bases_rejected": [
                    "shared_topic",
                    "shared_agency",
                    "shared_statute",
                    "shared_cra_mechanism",
                    "shared_vote_direction",
                    "party",
                    "sponsor",
                    "ideology",
                ],
                "material_differences_preserved": ["Synthetic difference."],
            }
        }
        with self.assertRaisesRegex(SemanticCompilerInputError, "non-directional"):
            compile_behavioral_candidate_ir(changed)

    def test_direction_cannot_override_accepted_episode_effects(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        changed["proposition_candidates"][0]["direction"] = "support"
        with self.assertRaises(SemanticCompilerInputError):
            compile_behavioral_candidate_ir(changed)

    def test_blocked_action_is_unavailable(self) -> None:
        graph = compile_behavioral_candidate_ir(copy.deepcopy(self.compiler_input))
        self.assertFalse(
            any(
                "house:119:2:278" in proposition["evidence_action_ids"]
                for proposition in graph["proposition_graph"]["propositions"]
            )
        )

        changed = copy.deepcopy(self.compiler_input)
        blocked_episode = copy.deepcopy(changed["episodes"][0])
        blocked_episode["episode_id"] = "blocked-hr-8800"
        blocked_episode["primary_action_ids"] = ["house:119:2:278"]
        changed["episodes"].append(blocked_episode)
        changed["episode_accounting"].append(
            {
                "episode_id": "blocked-hr-8800",
                "primary_proposition_id": None,
                "disposition": "no_safe_higher_level_behavioral_proposition",
                "reason": "malicious inclusion",
            }
        )
        with self.assertRaises(SemanticCompilerInputError):
            compile_behavioral_candidate_ir(changed)


if __name__ == "__main__":
    unittest.main()
