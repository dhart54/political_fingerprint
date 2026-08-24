from __future__ import annotations

import copy
from collections import Counter
import json
from pathlib import Path
import unittest

from backend.app.semantic_ir.compiler import (
    SemanticCompilerInputError,
    compile_behavioral_candidate_ir,
)
from backend.scripts.build_m13g_education_workforce_behavioral_semantic_ir_candidates import (
    DECISION_PATH,
    IMPLEMENTATION_PATH,
    PROPOSITIONS,
    build,
    build_input,
    preflight,
)
from scripts.validate_m13g_education_workforce_behavioral_semantic_ir_candidates import (
    validate,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class M13gEducationWorkforceBehavioralSemanticIrCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiler_input = build_input(preflight())

    def test_deterministic_candidate_package(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            result["proposition_counts"],
            {"notable_choice": 1, "repeated_pattern": 1},
        )
        self.assertEqual(
            build(check=True)["counts"],
            Counter({"notable_choice": 1, "repeated_pattern": 1}),
        )

    def test_exact_candidate_evidence_sets(self) -> None:
        result = build(check=True)
        propositions = {
            row["proposition_id"]: row
            for row in result["graph"]["compiled_candidate_ir"]["proposition_graph"][
                "propositions"
            ]
        }
        self.assertEqual(
            set(propositions), {row["proposition_id"] for row in PROPOSITIONS}
        )
        for definition in PROPOSITIONS:
            self.assertEqual(
                propositions[definition["proposition_id"]]["evidence_episode_ids"],
                definition["evidence_episode_ids"],
            )

    def test_non_directional_episode_cannot_enter_candidate_evidence(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        candidate = changed["proposition_candidates"][0]
        replaced = candidate["evidence_episode_ids"][0]
        non_directional = "single-119-hr-1005-1-312"
        candidate["evidence_episode_ids"][0] = non_directional
        candidate["episode_semantic_evidence"].pop(replaced)
        candidate["episode_semantic_evidence"][non_directional] = (
            "Accepted Not Voting episode."
        )
        relationship = changed["relationship_evidence_by_proposition"][
            candidate["proposition_id"]
        ]
        relationship["episode_support"].pop(replaced)
        relationship["episode_support"][non_directional] = (
            "Accepted Not Voting episode."
        )
        with self.assertRaisesRegex(SemanticCompilerInputError, "non-directional"):
            compile_behavioral_candidate_ir(changed)

    def test_topic_or_shared_mechanism_alone_is_rejected(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        proposition_id = changed["proposition_candidates"][0]["proposition_id"]
        changed["relationship_evidence_by_proposition"][proposition_id][
            "insufficient_bases_rejected"
        ] = ["shared_topic", "shared_agency", "shared_vote_direction"]
        with self.assertRaisesRegex(SemanticCompilerInputError, "incomplete"):
            compile_behavioral_candidate_ir(changed)

    def test_repeated_pattern_requires_multiple_episodes(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        candidate = changed["proposition_candidates"][0]
        keep = candidate["evidence_episode_ids"][0]
        candidate["evidence_episode_ids"] = [keep]
        candidate["episode_semantic_evidence"] = {
            keep: candidate["episode_semantic_evidence"][keep]
        }
        relationship = changed["relationship_evidence_by_proposition"][
            candidate["proposition_id"]
        ]
        relationship["episode_support"] = {keep: relationship["episode_support"][keep]}
        with self.assertRaisesRegex(SemanticCompilerInputError, "at least two"):
            compile_behavioral_candidate_ir(changed)

    def test_hr1048_component_tampering_breaks_accepted_episode_seal(self) -> None:
        changed = copy.deepcopy(self.compiler_input)
        package = next(
            row
            for row in changed["episodes"]
            if row["episode_id"] == "hr-1048-amendment-and-final-passage"
        )
        package["primary_action_ids"] = ["house:119:1:79"]
        with self.assertRaisesRegex(SemanticCompilerInputError, "seal differs"):
            compile_behavioral_candidate_ir(changed)

    def test_only_explicit_notable_choice_and_no_trajectory(self) -> None:
        result = build(check=True)
        propositions = result["graph"]["compiled_candidate_ir"]["proposition_graph"][
            "propositions"
        ]
        self.assertEqual(
            Counter(row["proposition_type"] for row in propositions),
            Counter({"notable_choice": 1, "repeated_pattern": 1}),
        )
        self.assertNotIn(
            "trajectory", {row["proposition_type"] for row in propositions}
        )
        self.assertEqual(
            len(result["graph"]["compiled_candidate_ir"]["episode_accounting"]),
            16,
        )

    def test_decision_template_is_entirely_empty(self) -> None:
        decision = load(DECISION_PATH)
        self.assertEqual(decision["decision_state"], "empty_not_authorizing")
        self.assertIsNone(decision["reviewer"])
        self.assertIsNone(decision["reviewed_at_utc"])
        self.assertTrue(
            all(
                row["decision"] is None
                and row["bounded_revision"] is None
                and row["reviewer_notes"] is None
                for row in decision["decisions"]
            )
        )

    def test_m13f_input_has_exact_accepted_accounting(self) -> None:
        implementation = load(IMPLEMENTATION_PATH)
        self.assertEqual(
            implementation["subject"]["final_accounting"],
            {
                "accepted_action_count": 17,
                "accepted_episode_count": 16,
                "single_action_episode_count": 15,
                "multi_action_episode_count": 1,
                "cross_measure_episode_count": 1,
                "ambiguous_or_unassigned_action_count": 0,
                "blocked_action_count": 0,
            },
        )


if __name__ == "__main__":
    unittest.main()
