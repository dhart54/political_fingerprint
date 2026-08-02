from __future__ import annotations

import copy
import unittest

from scripts.build_foushee_justice_semantic_ir_m5r1 import (
    OUTPUT_ROOT,
    ROLL_131,
    ROLL_171,
    ROLL_298,
    build,
    load,
)
from scripts.validate_foushee_justice_semantic_ir_m5r1 import (
    validate,
    validate_no_inflating_primary_overlap,
    validate_parity,
    validate_reconstruction,
    validate_semantic_invariants,
)


class FousheeJusticeSemanticIRM5R1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = load(OUTPUT_ROOT / "frozen_final_compiled_semantic_ir.json")
        cls.compiler_input = load(OUTPUT_ROOT / "frozen_final_compiler_input.json")[
            "compiler_input"
        ]

    def test_01_deterministic_builder(self) -> None:
        result = build(True)
        self.assertEqual(result["initial_overlap_count"], 2)
        self.assertEqual(result["corrected_overlap_count"], 0)

    def test_02_independent_verifier(self) -> None:
        self.assertEqual(validate()["status"], "pass")

    def test_03_action_in_two_primary_repeated_patterns_is_rejected(self) -> None:
        graph = copy.deepcopy(self.graph)
        primary = [
            p
            for p in graph["compiled_ir"]["members"][0]["proposition_graph"][
                "propositions"
            ]
            if p["proposition_type"] == "repeated_pattern"
            and p["proposition_id"] != "prop:354da734fec2fcf6"
        ][0]
        primary["evidence_action_ids"].append(ROLL_298)
        with self.assertRaisesRegex(ValueError, "prohibited primary"):
            validate_no_inflating_primary_overlap(graph)

    def test_04_episode_in_two_primary_repeated_patterns_is_rejected(self) -> None:
        graph = copy.deepcopy(self.graph)
        primary = [
            p
            for p in graph["compiled_ir"]["members"][0]["proposition_graph"][
                "propositions"
            ]
            if p["proposition_type"] == "repeated_pattern"
            and p["proposition_id"] != "prop:354da734fec2fcf6"
        ][0]
        primary["evidence_episode_ids"].append("dc-pretrial-detention-cash-bail")
        with self.assertRaisesRegex(ValueError, "prohibited primary"):
            validate_no_inflating_primary_overlap(graph)

    def test_05_set_accounting_cannot_mask_overlap(self) -> None:
        graph = copy.deepcopy(self.graph)
        original_accounting = copy.deepcopy(graph["full_universe_action_accounting"])
        repeated = [
            p
            for p in graph["compiled_ir"]["members"][0]["proposition_graph"][
                "propositions"
            ]
            if p["proposition_type"] == "repeated_pattern"
            and p["proposition_id"] != "prop:354da734fec2fcf6"
        ][0]
        repeated["evidence_action_ids"].append(ROLL_298)
        self.assertEqual(graph["full_universe_action_accounting"], original_accounting)
        with self.assertRaises(ValueError):
            validate_semantic_invariants(graph, self.compiler_input)

    def test_06_two_patterns_cannot_claim_same_episode_independently(self) -> None:
        graph = copy.deepcopy(self.graph)
        repeated = [
            p
            for p in graph["compiled_ir"]["members"][0]["proposition_graph"][
                "propositions"
            ]
            if p["proposition_type"] == "repeated_pattern"
            and p["proposition_id"] != "prop:354da734fec2fcf6"
        ][0]
        repeated["evidence_episode_ids"].append("dc-pretrial-detention-cash-bail")
        with self.assertRaises(ValueError):
            validate_semantic_invariants(graph, self.compiler_input)

    def test_07_limiting_label_cannot_hide_primary_weight(self) -> None:
        graph = copy.deepcopy(self.graph)
        repeated = [
            p
            for p in graph["compiled_ir"]["members"][0]["proposition_graph"][
                "propositions"
            ]
            if p["proposition_type"] == "repeated_pattern"
            and p["proposition_id"] != "prop:354da734fec2fcf6"
        ][0]
        repeated["conclusion_relevance"] = "limiting"
        repeated["evidence_action_ids"].append(ROLL_298)
        repeated["evidence_episode_ids"].append("dc-pretrial-detention-cash-bail")
        with self.assertRaises(ValueError):
            validate_no_inflating_primary_overlap(graph)

    def test_08_roll_171_cannot_disappear(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["full_universe_action_accounting"] = [
            row
            for row in graph["full_universe_action_accounting"]
            if row["action_id"] != ROLL_171
        ]
        with self.assertRaisesRegex(ValueError, "37-action|roll 171"):
            validate_semantic_invariants(graph, self.compiler_input)

    def test_09_roll_298_cannot_leave_behavioral_accounting(self) -> None:
        graph = copy.deepcopy(self.graph)
        for proposition in graph["compiled_ir"]["members"][0]["proposition_graph"][
            "propositions"
        ]:
            proposition["evidence_action_ids"] = [
                action_id
                for action_id in proposition["evidence_action_ids"]
                if action_id != ROLL_298
            ]
        with self.assertRaisesRegex(ValueError, "roll 298"):
            validate_semantic_invariants(graph, self.compiler_input)

    def test_10_roll_131_cannot_reenter_terrorism_trait(self) -> None:
        compiler_input = copy.deepcopy(self.compiler_input)
        terrorism = next(
            trait
            for trait in compiler_input["shared_semantics"]["policy_traits"]
            if trait["trait_id"] == "terrorism_preparedness_mandate"
        )
        terrorism["action_ids"].append(ROLL_131)
        with self.assertRaisesRegex(ValueError, "roll 131"):
            validate_semantic_invariants(self.graph, compiler_input)

    def test_11_blocked_actions_cannot_enter_propositions(self) -> None:
        for blocked in ("house:119:2:155", "house:119:2:278"):
            with self.subTest(blocked=blocked):
                graph = copy.deepcopy(self.graph)
                graph["compiled_ir"]["members"][0]["proposition_graph"]["propositions"][
                    0
                ]["evidence_action_ids"].append(blocked)
                with self.assertRaisesRegex(ValueError, "entered proposition"):
                    validate_semantic_invariants(graph, self.compiler_input)

    def test_12_stale_synthesis_is_rejected(self) -> None:
        graph = copy.deepcopy(self.graph)
        synthesis = next(
            p
            for p in graph["compiled_ir"]["members"][0]["proposition_graph"][
                "propositions"
            ]
            if p["semantic_role"] == "synthesis"
        )
        synthesis["relationships"]["supported_by"] = ["prop:stale-support-test"]
        with self.assertRaisesRegex(ValueError, "stale synthesis"):
            validate_semantic_invariants(graph, self.compiler_input)

    def test_13_manual_compiled_patch_is_rejected(self) -> None:
        graph = copy.deepcopy(self.graph)
        graph["compiled_ir"]["members"][0]["proposition_graph"]["propositions"][0][
            "direction"
        ] = "support"
        with self.assertRaisesRegex(ValueError, "manual or stale"):
            validate_reconstruction(graph, self.compiler_input)

    def test_14_stale_parity_is_rejected(self) -> None:
        parity = load(OUTPUT_ROOT / "parity_manifest.json")
        parity["entries"][0]["final_file_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "stale parity"):
            validate_parity(parity)


if __name__ == "__main__":
    unittest.main()
