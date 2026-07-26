from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import (  # noqa: E402
    OUTPUT_FIELDS,
    SemanticCompilerInputError,
    compile_semantic_ir,
    project_compiler_input,
)
from scripts.compare_accepted_semantic_references import (  # noqa: E402
    compare_case,
    semantic_projection,
)
from scripts.validate_editorial_semantic_ir import (  # noqa: E402
    ACCEPTED,
    HELD_OUT,
    SemanticValidationError,
    _load,
    validate_accepted_references,
    validate_held_out,
)


HELD_OUT_BASELINE_SHA256 = (
    "767cbacce790c45537833e46e59fe4b1c558b440c2844835a07414e45396a9d1"
)


def _cases() -> dict[str, dict[str, Any]]:
    return {
        case["case_id"]: case for case in _load(ACCEPTED)["cases"]
    }


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key for child in value.values() for key in _walk_keys(child)
        }
    if isinstance(value, list):
        return {key for child in value for key in _walk_keys(child)}
    return set()


def _replace_ids(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_ids(child, replacements) for key, child in value.items()}
    if isinstance(value, list):
        return [_replace_ids(child, replacements) for child in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value


def _selection(result: dict[str, Any]) -> set[tuple[Any, ...]]:
    return {
        (
            proposition["semantic_role"],
            proposition["proposition_type"],
            tuple(sorted(proposition["evidence_action_ids"])),
            tuple(sorted(proposition["evidence_episode_ids"])),
            tuple(sorted(proposition["mechanism_or_trait_refs"])),
            proposition["presentation_target"],
        )
        for proposition in result["proposition_graph"]["propositions"]
    }


class EditorialSemanticIRReferenceTests(unittest.TestCase):
    def test_committed_accepted_references_validate(self) -> None:
        case_ids = validate_accepted_references(_load(ACCEPTED))
        self.assertEqual(len(case_ids), 12)

    def test_all_accepted_references_compile_to_semantic_equality(self) -> None:
        for case in _load(ACCEPTED)["cases"]:
            with self.subTest(case_id=case["case_id"]):
                compare_case(case)

    def test_compiler_projection_excludes_every_expected_output_field(self) -> None:
        for case in _load(ACCEPTED)["cases"]:
            projected = project_compiler_input(case)
            self.assertFalse(
                OUTPUT_FIELDS & _walk_keys(projected),
                case["case_id"],
            )

    def test_compiler_rejects_expected_output_fields(self) -> None:
        case = next(iter(_cases().values()))
        projected = project_compiler_input(case)
        projected["proposition_graph"] = {"propositions": []}
        with self.assertRaisesRegex(
            SemanticCompilerInputError, "expected-output field"
        ):
            compile_semantic_ir(projected)

    def test_present_and_not_voting_are_non_directional_coverage(self) -> None:
        cases = _cases()
        present = cases["semir-dev-10-present-known-coverage"]
        not_voting = cases["semir-dev-09-not-voting-heavy-record"]
        present_result = compile_semantic_ir(project_compiler_input(present))["members"][0]
        not_voting_result = compile_semantic_ir(
            project_compiler_input(not_voting)
        )["members"][0]
        self.assertEqual(present_result["coverage"]["directional_yes_no_positions"], 6)
        self.assertEqual(not_voting_result["coverage"]["not_voting_actions"], 5)
        self.assertTrue(
            all(
                action_id not in not_voting_result["action_accounting"][
                    "behavioral_proposition_action_ids"
                ]
                for action_id in {
                    reason["action_id"]
                    for reason in not_voting_result["action_accounting"][
                        "non_proposition_reasons"
                    ]
                }
            )
        )

    def test_context_controls_do_not_inflate_substantive_coverage(self) -> None:
        case = _cases()["semir-dev-03-economy-noncounting-boundaries"]
        result = compile_semantic_ir(project_compiler_input(case))["members"][0]
        self.assertEqual(result["coverage"]["eligible_substantive_actions"], 1)
        self.assertEqual(result["coverage"]["context_only_control_actions"], 2)
        self.assertEqual(result["coverage"]["directional_yes_no_positions"], 0)

    def test_full_record_requires_complete_action_accounting(self) -> None:
        corpus = _load(ACCEPTED)
        mutated = copy.deepcopy(corpus)
        mutated["cases"][1]["action_accounting"][
            "behavioral_proposition_action_ids"
        ].pop()
        with self.assertRaisesRegex(
            SemanticValidationError, "behavioral action accounting drift"
        ):
            validate_accepted_references(mutated)

    def test_parent_context_cannot_establish_exact_action_eligibility(self) -> None:
        corpus = _load(ACCEPTED)
        mutated = copy.deepcopy(corpus)
        mutated["cases"][6]["shared_semantics"]["actions"][1]["eligibility"][
            "parent_context_used"
        ] = True
        with self.assertRaisesRegex(
            SemanticValidationError, "parent context established eligibility"
        ):
            validate_accepted_references(mutated)
        with self.assertRaisesRegex(
            SemanticCompilerInputError, "parent context cannot establish eligibility"
        ):
            compile_semantic_ir(project_compiler_input(mutated["cases"][6]))

    def test_single_action_episode_cannot_be_trajectory(self) -> None:
        corpus = _load(ACCEPTED)
        mutated = copy.deepcopy(corpus)
        proposition = mutated["cases"][6]["proposition_graph"]["propositions"][0]
        proposition["proposition_type"] = "trajectory"
        with self.assertRaisesRegex(SemanticValidationError, "single-action trajectory"):
            validate_accepted_references(mutated)


class EditorialSemanticIRPropertyTests(unittest.TestCase):
    def test_identity_party_title_and_order_are_semantically_opaque(self) -> None:
        case = _cases()["semir-dev-12-identity-title-order-invariance"]
        projected = project_compiler_input(case)
        baseline = compile_semantic_ir(projected)["members"]
        self.assertEqual(
            semantic_projection(baseline[0]),
            semantic_projection(baseline[1]),
        )

        mutated = copy.deepcopy(projected)
        for index, member in enumerate(mutated["members"]):
            member["member_id"] = f"opaque-member-{index}"
            member["party"] = "unknown"
            member["actions"].reverse()
        for action in mutated["shared_semantics"]["actions"]:
            action["action_meaning_ref"] = "opaque-reviewed-meaning"
            action["legislative_stage"] = "opaque-stage-title"
            action["structural_metadata"]["division"] = (
                "opaque-structural-metadata-not-a-policy-trait"
            )
        mutated["shared_semantics"]["actions"].reverse()
        mutated["shared_semantics"]["episodes"].reverse()
        mutated["shared_semantics"]["policy_families"].reverse()
        mutated["shared_semantics"]["policy_traits"].reverse()
        for episode in mutated["shared_semantics"]["episodes"]:
            episode["action_ids"].reverse()
        for trait in mutated["shared_semantics"]["policy_traits"]:
            trait["action_ids"].reverse()

        actual = compile_semantic_ir(mutated)["members"]
        self.assertEqual(
            semantic_projection(baseline[0]),
            semantic_projection(actual[0]),
        )

    def test_vote_direction_cannot_change_shared_hierarchy_or_selection(self) -> None:
        case = _cases()["semir-dev-08-environment-separate-family-episodes"]
        projected = project_compiler_input(case)
        shared_before = copy.deepcopy(projected["shared_semantics"])
        baseline = compile_semantic_ir(projected)["members"][0]
        mutated = copy.deepcopy(projected)
        for action in mutated["members"][0]["actions"]:
            action["status"] = "Nay" if action["status"] == "Yea" else "Yea"
        flipped = compile_semantic_ir(mutated)["members"][0]
        self.assertEqual(projected["shared_semantics"], shared_before)
        self.assertEqual(_selection(baseline), _selection(flipped))
        baseline_directions = {
            tuple(proposition["mechanism_or_trait_refs"]): proposition["direction"]
            for proposition in baseline["proposition_graph"]["propositions"]
            if proposition["semantic_role"] == "behavioral"
        }
        flipped_directions = {
            tuple(proposition["mechanism_or_trait_refs"]): proposition["direction"]
            for proposition in flipped["proposition_graph"]["propositions"]
            if proposition["semantic_role"] == "behavioral"
        }
        self.assertEqual(
            flipped_directions,
            {
                trait_refs: (
                    "opposition" if direction == "support" else "support"
                )
                for trait_refs, direction in baseline_directions.items()
            },
        )

    def test_equivalent_stable_id_substitution_preserves_semantics(self) -> None:
        case = _cases()["semir-dev-08-environment-separate-family-episodes"]
        projected = project_compiler_input(case)
        baseline = compile_semantic_ir(projected)["members"][0]
        action_ids = [
            action["action_id"] for action in projected["shared_semantics"]["actions"]
        ]
        episode_ids = [
            episode["episode_id"]
            for episode in projected["shared_semantics"]["episodes"]
        ]
        replacements = {
            **{
                action_id: f"opaque-action-{index:02d}"
                for index, action_id in enumerate(action_ids)
            },
            **{
                episode_id: f"opaque-episode-{index:02d}"
                for index, episode_id in enumerate(episode_ids)
            },
        }
        substituted = _replace_ids(projected, replacements)
        actual = compile_semantic_ir(substituted)["members"][0]
        restored = _replace_ids(actual, {value: key for key, value in replacements.items()})
        self.assertEqual(semantic_projection(baseline), semantic_projection(restored))

    def test_engine_source_contains_no_reference_id_branches(self) -> None:
        source = (
            ROOT / "backend/app/semantic_ir/compiler.py"
        ).read_text(encoding="utf-8")
        corpus = _load(ACCEPTED)
        forbidden = {
            case["case_id"]
            for case in corpus["cases"]
        } | {
            member["member_id"]
            for case in corpus["cases"]
            for member in case["member_semantics"]["members"]
        } | {
            action["action_id"]
            for case in corpus["cases"]
            for action in case["shared_semantics"]["actions"]
        } | {
            case["domain"] for case in corpus["cases"]
        }
        self.assertFalse({value for value in forbidden if value in source})

    def test_shared_novelty_is_not_duplicated_per_identical_member(self) -> None:
        case = _cases()["semir-dev-12-identity-title-order-invariance"]
        compiled = compile_semantic_ir(project_compiler_input(case))["members"]
        self.assertEqual(
            _selection(compiled[0]),
            _selection(compiled[1]),
        )
        self.assertEqual(compiled[0]["review_route"], compiled[1]["review_route"])

    def test_tied_material_patterns_remain_owned_once_each(self) -> None:
        case = _cases()["semir-dev-11-tied-pattern-ownership"]
        result = compile_semantic_ir(project_compiler_input(case))["members"][0]
        patterns = [
            proposition
            for proposition in result["proposition_graph"]["propositions"]
            if proposition["proposition_type"] == "repeated_pattern"
        ]
        self.assertEqual(len(patterns), 2)
        owned = result["composition"]["presentation_ownership"][
            "repeated_patterns"
        ]
        self.assertEqual(set(owned), {item["proposition_id"] for item in patterns})


class EditorialSemanticIRHeldOutTests(unittest.TestCase):
    def test_committed_held_out_inputs_validate_and_remain_answer_free(self) -> None:
        case_ids = validate_held_out(_load(HELD_OUT))
        self.assertEqual(len(case_ids), 4)

    def test_held_out_file_is_byte_identical_to_phase_b_baseline(self) -> None:
        digest = hashlib.sha256(HELD_OUT.read_bytes()).hexdigest()
        self.assertEqual(digest, HELD_OUT_BASELINE_SHA256)

    def test_held_out_expected_answer_is_rejected(self) -> None:
        corpus = _load(HELD_OUT)
        mutated = copy.deepcopy(corpus)
        mutated["cases"][0]["expected_conclusion"] = "must not be committed"
        with self.assertRaisesRegex(SemanticValidationError, "answers leaked"):
            validate_held_out(mutated)


if __name__ == "__main__":
    unittest.main()
