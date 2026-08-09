from __future__ import annotations

import copy
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
        self.assertEqual(len(graph["proposition_graph"]["propositions"]), 4)
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
