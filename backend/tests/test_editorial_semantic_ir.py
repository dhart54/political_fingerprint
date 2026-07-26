from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_editorial_semantic_ir import (  # noqa: E402
    CANDIDATES,
    HELD_OUT,
    SemanticValidationError,
    _load,
    validate_development,
    validate_held_out,
)


class EditorialSemanticIRTests(unittest.TestCase):
    def test_committed_development_candidates_validate(self) -> None:
        case_ids = validate_development(_load(CANDIDATES))
        self.assertEqual(len(case_ids), 12)

    def test_committed_held_out_inputs_validate(self) -> None:
        case_ids = validate_held_out(_load(HELD_OUT))
        self.assertEqual(len(case_ids), 4)

    def test_present_and_not_voting_are_non_directional_coverage(self) -> None:
        corpus = _load(CANDIDATES)
        cases = {case["case_id"]: case for case in corpus["cases"]}
        present = cases["semir-dev-10-present-known-coverage"]
        not_voting = cases["semir-dev-09-not-voting-heavy-record"]
        self.assertEqual(
            present["member_semantics"]["members"][0]["coverage"]["yes_no_actions"], 6
        )
        self.assertEqual(
            not_voting["member_semantics"]["members"][0]["coverage"][
                "not_voting_actions"
            ],
            5,
        )

    def test_single_action_episode_cannot_be_trajectory(self) -> None:
        corpus = _load(CANDIDATES)
        mutated = copy.deepcopy(corpus)
        case = mutated["cases"][6]
        proposition = case["proposition_graph"]["propositions"][0]
        proposition["proposition_type"] = "trajectory"
        with self.assertRaisesRegex(SemanticValidationError, "single-action trajectory"):
            validate_development(mutated)

    def test_held_out_expected_answer_is_rejected(self) -> None:
        corpus = _load(HELD_OUT)
        mutated = copy.deepcopy(corpus)
        mutated["cases"][0]["expected_conclusion"] = "must not be committed"
        with self.assertRaisesRegex(SemanticValidationError, "answers leaked"):
            validate_held_out(mutated)


if __name__ == "__main__":
    unittest.main()
