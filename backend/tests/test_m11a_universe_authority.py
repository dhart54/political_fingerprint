from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.universe_authority import UniverseAuthorityError  # noqa: E402
from scripts.validate_m11a_universe_authority import (  # noqa: E402
    CURRENT_STATE_PATH,
    EXPECTED,
    EXPECTED_UNRESOLVED,
    INVENTORY_PATH,
    RECEIPT_PATH,
    SELECTION_PATH,
    UNIVERSE_PATH,
    validate_repository,
    validate_values,
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class M11AUniverseAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values = {
            "receipt": _load(RECEIPT_PATH),
            "selection": _load(SELECTION_PATH),
            "universe": _load(UNIVERSE_PATH),
            "inventory": _load(INVENTORY_PATH),
            "current_state": _load(CURRENT_STATE_PATH),
        }

    def _validate(
        self,
        mutator: Callable[[dict[str, dict[str, Any]]], None] | None = None,
        *,
        receipt_path: Path = RECEIPT_PATH,
    ) -> dict[str, Any]:
        values = copy.deepcopy(self.values)
        if mutator is not None:
            mutator(values)
        return validate_values(**values, receipt_path=receipt_path)

    def assert_rejected(
        self, mutator: Callable[[dict[str, dict[str, Any]]], None]
    ) -> None:
        with self.assertRaises(UniverseAuthorityError):
            self._validate(mutator)

    def test_repository_receipt_recomputes_approved_boundary(self) -> None:
        result = validate_repository()
        self.assertEqual(result["approved_action_count"], 82)
        self.assertEqual(
            result["approved_action_set_sha256"],
            EXPECTED["approved_action_set_sha256"],
        )
        self.assertEqual(result["candidate_count"], 149)
        self.assertEqual(
            result["exclusion_counts"],
            {
                "procedural_context": 33,
                "expressive_nonbinding_context": 2,
                "exact_action_ineligible": 26,
                "boundary_review_required": 6,
            },
        )
        self.assertEqual(result["unresolved_action_ids"], EXPECTED_UNRESOLVED)

    def test_receipt_is_detached_and_binds_exact_accepted_head(self) -> None:
        before = RECEIPT_PATH.read_bytes()
        result = self._validate()
        self.assertEqual(RECEIPT_PATH.read_bytes(), before)
        self.assertEqual(result["accepted_head"], EXPECTED["accepted_head"])
        with self.assertRaisesRegex(UniverseAuthorityError, "detached"):
            self._validate(receipt_path=UNIVERSE_PATH)

    def test_selection_digest_tampering_rejects(self) -> None:
        self.assert_rejected(
            lambda values: values["selection"].__setitem__(
                "selected_domain", "ENVIRONMENT_ENERGY"
            )
        )
        self.assert_rejected(
            lambda values: values["receipt"]["approval_binding"][
                "selection"
            ].__setitem__("sha256", "0" * 64)
        )

    def test_approved_action_add_remove_and_substitution_reject(self) -> None:
        mutations = (
            lambda values: values["receipt"]["approval_binding"][
                "approved_action_ids"
            ].append("house:119:2:999"),
            lambda values: values["receipt"]["approval_binding"][
                "approved_action_ids"
            ].pop(),
            lambda values: values["receipt"]["approval_binding"][
                "approved_action_ids"
            ].__setitem__(0, "house:119:2:999"),
            lambda values: values["universe"]["proposed_action_ids"].pop(),
        )
        for mutator in mutations:
            with self.subTest(mutator=mutator):
                self.assert_rejected(mutator)

    def test_exclusion_and_unresolved_tampering_rejects(self) -> None:
        self.assert_rejected(
            lambda values: values["receipt"]["approval_binding"][
                "exclusion_categories"
            ]["procedural_context"]["action_ids"].pop()
        )
        self.assert_rejected(
            lambda values: values["universe"]["unresolved_action_ids"].pop()
        )
        self.assert_rejected(
            lambda values: values["universe"]["candidate_dispositions"][0].__setitem__(
                "disposition", "procedural_context"
            )
        )

    def test_subject_cutoff_and_complete_house_identity_tampering_rejects(self) -> None:
        mutations = (
            lambda values: values["receipt"]["approval_binding"]["subject"].__setitem__(
                "congress", 118
            ),
            lambda values: values["universe"]["cutoff"].__setitem__(
                "end_date", "2026-07-22"
            ),
            lambda values: values["receipt"]["approval_binding"][
                "complete_house_action_set"
            ].__setitem__("action_set_sha256", "0" * 64),
        )
        for mutator in mutations:
            with self.subTest(mutator=mutator):
                self.assert_rejected(mutator)

    def test_source_inventory_and_exact_binding_tampering_rejects(self) -> None:
        self.assert_rejected(
            lambda values: values["inventory"].__setitem__("inventory_sha256", "0" * 64)
        )
        self.assert_rejected(
            lambda values: values["inventory"]["selected_candidate_source_bindings"][
                0
            ].__setitem__("sources", [])
        )
        proposed_id = self.values["universe"]["proposed_action_ids"][0]

        def remove_exact_binding(values: dict[str, dict[str, Any]]) -> None:
            row = next(
                row
                for row in values["inventory"]["selected_candidate_source_bindings"]
                if row["action_id"] == proposed_id
            )
            row["exact_action_source_binding"] = None

        self.assert_rejected(remove_exact_binding)

    def test_receipt_cannot_authorize_interpretation_or_publication(self) -> None:
        for field in (
            "action_interpretation",
            "episode_acceptance",
            "semantic_ir",
            "synthesis",
            "public_wording",
            "publication",
            "production_persistence",
        ):
            with self.subTest(field=field):
                self.assert_rejected(
                    lambda values, field=field: values["receipt"]["approval_binding"][
                        "downstream_authorizations"
                    ].__setitem__(field, True)
                )

    def test_current_state_cannot_cross_universe_only_boundary(self) -> None:
        self.assert_rejected(
            lambda values: values["current_state"][
                "active_scaling_milestone"
            ].__setitem__("interpretation_state", "started")
        )
        self.assert_rejected(
            lambda values: values["current_state"]["active_scaling_milestone"][
                "downstream_authorizations"
            ].__setitem__("episode_acceptance", True)
        )

    def test_accepted_justice_state_must_remain_unchanged(self) -> None:
        self.assert_rejected(
            lambda values: values["current_state"][
                "full_record_issue_interpretation"
            ].__setitem__("f000477_justice_119_publication_state", "inactive")
        )

    def test_historical_proposal_remains_pending_and_non_authorizing(self) -> None:
        universe = self.values["universe"]
        self.assertEqual(
            universe["authority_status"], "pending_human_universe_boundary_review"
        )
        self.assertFalse(universe["action_interpretation_started"])
        self.assertFalse(universe["action_interpretation_authorized"])
        self.assertFalse(universe["episode_acceptance_authorized"])
        self.assertFalse(universe["semantic_ir_started"])
        self.assertFalse(universe["synthesis_authorized"])
        self.assertFalse(universe["publication_authorized"])
        self.assertFalse(universe["production_writes"])


if __name__ == "__main__":
    unittest.main()
