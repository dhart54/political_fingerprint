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
            present["member_semantics"]["members"][0]["coverage"][
                "directional_yes_no_positions"
            ],
            6,
        )
        self.assertEqual(
            not_voting["member_semantics"]["members"][0]["coverage"][
                "not_voting_actions"
            ],
            5,
        )

    def test_context_controls_do_not_inflate_substantive_coverage(self) -> None:
        corpus = _load(CANDIDATES)
        cases = {case["case_id"]: case for case in corpus["cases"]}
        coverage = cases["semir-dev-03-economy-noncounting-boundaries"][
            "member_semantics"
        ]["members"][0]["coverage"]
        self.assertEqual(coverage["eligible_substantive_actions"], 1)
        self.assertEqual(coverage["context_only_control_actions"], 2)
        self.assertEqual(coverage["directional_yes_no_positions"], 0)

    def test_synthesis_is_conclusion_only_and_coverage_is_not_behavioral(self) -> None:
        corpus = _load(CANDIDATES)
        cases = {case["case_id"]: case for case in corpus["cases"]}
        mechanism = cases["semir-dev-05-justice-mechanism-divide"][
            "proposition_graph"
        ]["propositions"][-1]
        self.assertEqual(mechanism["semantic_role"], "synthesis")
        self.assertEqual(mechanism["presentation_target"], "conclusion_only")
        not_voting = cases["semir-dev-09-not-voting-heavy-record"]
        self.assertTrue(not_voting["composition"]["coverage_boundaries"])
        self.assertTrue(
            all(
                proposition["semantic_role"] == "behavioral"
                for proposition in not_voting["proposition_graph"]["propositions"]
            )
        )

    def test_full_record_requires_complete_action_accounting(self) -> None:
        corpus = _load(CANDIDATES)
        mutated = copy.deepcopy(corpus)
        case = mutated["cases"][1]
        case["action_accounting"]["behavioral_proposition_action_ids"].pop()
        with self.assertRaisesRegex(
            SemanticValidationError, "behavioral action accounting drift"
        ):
            validate_development(mutated)

    def test_focused_fixture_declares_scope_boundary(self) -> None:
        corpus = _load(CANDIDATES)
        cases = {case["case_id"]: case for case in corpus["cases"]}
        focused = cases["semir-dev-12-identity-title-order-invariance"]
        self.assertEqual(focused["case_scope"], "focused_invariant_fixture")
        self.assertTrue(focused["scope_boundary"])

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
