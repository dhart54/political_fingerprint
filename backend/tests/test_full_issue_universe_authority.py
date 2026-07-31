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

from backend.app.etl.universe_authority import (  # noqa: E402
    UniverseAuthorityError,
    canonical_file_sha256,
    sha256_json,
)
from scripts.validate_full_issue_universe_authority import (  # noqa: E402
    COMPARISON_PATH,
    CONFIG_PATH,
    CURRENT_STATE_PATH,
    DISCOVERY_PATH,
    EXPECTED,
    INVENTORY_PATH,
    MANIFEST_PATH,
    RECEIPT_PATH,
    validate_authority_values,
    validate_current_state,
    validate_repository_authority,
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class FullIssueUniverseAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values = {
            "receipt": _load(RECEIPT_PATH),
            "manifest": _load(MANIFEST_PATH),
            "discovery": _load(DISCOVERY_PATH),
            "inventory": _load(INVENTORY_PATH),
            "config": _load(CONFIG_PATH),
            "comparison": _load(COMPARISON_PATH),
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
        return validate_authority_values(
            **values,
            manifest_path=ROOT / MANIFEST_PATH,
            authority_root=ROOT,
            receipt_path=receipt_path,
        )

    def assert_rejected(
        self, mutator: Callable[[dict[str, dict[str, Any]]], None]
    ) -> None:
        with self.assertRaises(UniverseAuthorityError):
            self._validate(mutator)

    def test_repository_authority_reproduces_all_approved_values(self) -> None:
        result = validate_repository_authority()
        self.assertEqual(result["manifest_file_sha256"], EXPECTED["manifest_sha256"])
        self.assertEqual(result["action_set_sha256"], EXPECTED["action_set_sha256"])
        self.assertEqual(
            result["universe_subject_sha256"], EXPECTED["universe_subject_sha256"]
        )
        self.assertEqual(
            (
                result["complete_action_count"],
                result["candidate_count"],
                result["action_count"],
                result["expressive_count"],
                result["procedural_count"],
                result["ineligible_count"],
                result["unresolved_count"],
            ),
            (638, 172, 37, 7, 69, 59, 0),
        )
        self.assertEqual(result["inclusion_cutoff"], "2026-07-23")
        self.assertEqual(result["latest_included_roll"], 283)

    def test_receipt_is_detached_and_timestamp_is_stable(self) -> None:
        before = (ROOT / RECEIPT_PATH).read_bytes()
        self._validate()
        self._validate()
        self.assertEqual((ROOT / RECEIPT_PATH).read_bytes(), before)
        self.assertEqual(
            self.values["receipt"]["decision_timestamp"],
            "2026-07-31T12:41:23.5179477Z",
        )
        with self.assertRaisesRegex(UniverseAuthorityError, "detached"):
            self._validate(receipt_path=Path("docs/proposals/authority.json"))

    def test_manifest_content_digest_and_rules_tampering_reject(self) -> None:
        self.assert_rejected(
            lambda values: values["receipt"].__setitem__("manifest_sha256", "0" * 64)
        )
        self.assert_rejected(
            lambda values: values["manifest"]["rules"]["inclusion"].append(
                "Unauthorized inclusion rule."
            )
        )

    def test_action_add_remove_duplicate_and_substitution_reject(self) -> None:
        def add(values: dict[str, dict[str, Any]]) -> None:
            values["manifest"]["action_ids"].append("house:119:2:999")

        def remove(values: dict[str, dict[str, Any]]) -> None:
            values["manifest"]["action_ids"].pop()

        def duplicate(values: dict[str, dict[str, Any]]) -> None:
            values["manifest"]["action_ids"].append(values["manifest"]["action_ids"][0])

        def substitute(values: dict[str, dict[str, Any]]) -> None:
            values["manifest"]["action_ids"][0] = "house:119:2:999"

        for name, mutator in (
            ("add", add),
            ("remove", remove),
            ("duplicate", duplicate),
            ("substitute", substitute),
        ):
            with self.subTest(name=name):
                self.assert_rejected(mutator)

    def test_action_subject_and_boundary_digest_tampering_reject(self) -> None:
        mutations = (
            lambda values: values["receipt"].__setitem__("action_set_sha256", "0" * 64),
            lambda values: values["receipt"].__setitem__(
                "universe_subject_sha256", "0" * 64
            ),
            lambda values: values["receipt"].__setitem__("boundary_sha256", "0" * 64),
        )
        for mutator in mutations:
            self.assert_rejected(mutator)

    def test_member_issue_congress_chamber_cutoff_and_latest_roll_tampering_reject(
        self,
    ) -> None:
        mutations = (
            lambda values: values["receipt"].__setitem__("member_id", "A000001"),
            lambda values: values["receipt"].__setitem__("issue_id", "ECONOMY_TAXES"),
            lambda values: values["config"]["subject"].__setitem__(
                "congress_scope", [118]
            ),
            lambda values: values["receipt"]["boundary"].__setitem__(
                "chambers", ["senate"]
            ),
            lambda values: values["config"]["boundary"].__setitem__(
                "end_date", "2026-07-22"
            ),
        )
        for mutator in mutations:
            self.assert_rejected(mutator)

        def remove_latest_roll(values: dict[str, dict[str, Any]]) -> None:
            action_set = values["discovery"]["complete_member_action_snapshot"]
            action_set["action_ids"].remove("house:119:2:283")
            action_set["action_count"] = len(action_set["action_ids"])
            action_set["action_set_sha256"] = sha256_json(
                sorted(action_set["action_ids"])
            )

        self.assert_rejected(remove_latest_roll)

    def test_governed_source_and_inventory_tampering_reject(self) -> None:
        self.assert_rejected(
            lambda values: values["receipt"]["source_manifest_identities"].__setitem__(
                0, "source-inventory:changed"
            )
        )
        self.assert_rejected(
            lambda values: values["manifest"]["source_manifests"][0].__setitem__(
                "sha256", "0" * 64
            )
        )
        self.assert_rejected(
            lambda values: values["discovery"]["source_inventory"].__setitem__(
                "inventory_id", "source-inventory:changed"
            )
        )

    def test_accounting_and_unresolved_tampering_reject(self) -> None:
        self.assert_rejected(
            lambda values: values["discovery"]["candidate_dispositions"][0].__setitem__(
                "disposition", "expressive_nonbinding_context"
            )
        )
        self.assert_rejected(
            lambda values: values["discovery"]["candidate_dispositions"].pop()
        )

        def add_unresolved(values: dict[str, dict[str, Any]]) -> None:
            action_set = values["discovery"]["unresolved_candidate_set"]
            action_set["action_ids"] = [
                values["discovery"]["candidate_recall_set"]["action_ids"][0]
            ]
            action_set["action_count"] = 1
            action_set["action_set_sha256"] = sha256_json(action_set["action_ids"])

        self.assert_rejected(add_unresolved)

    def test_expressive_and_fisa_scope_tampering_reject(self) -> None:
        expressive_id = self.values["manifest"]["expressive_nonbinding_action_set"][
            "action_ids"
        ][0]

        def promote_expressive(values: dict[str, dict[str, Any]]) -> None:
            row = next(
                row
                for row in values["discovery"]["candidate_dispositions"]
                if row["action_id"] == expressive_id
            )
            row["disposition"] = "proposed_in_scope_substantive"

        self.assert_rejected(promote_expressive)
        self.assert_rejected(
            lambda values: values["config"]["cross_domain_scope_limitations"][
                "house:119:2:155"
            ].pop()
        )
        self.assert_rejected(
            lambda values: values["comparison"]["cross_domain_memberships"][
                "house:119:2:221"
            ].remove("NATIONAL_SECURITY")
        )

    def test_reviewer_authority_decision_and_semantic_claim_tampering_reject(
        self,
    ) -> None:
        self.assert_rejected(
            lambda values: values["receipt"]["reviewer"].__setitem__(
                "reviewer_id", "someone_else"
            )
        )
        self.assert_rejected(
            lambda values: values["receipt"]["reviewer"].__setitem__(
                "authority", "test_authority"
            )
        )
        self.assert_rejected(
            lambda values: values["receipt"].__setitem__("decision", "pending")
        )
        self.assert_rejected(
            lambda values: values["receipt"].__setitem__("semantic_ir_authority", True)
        )

    def test_state_cannot_claim_downstream_authority(self) -> None:
        receipt_sha = canonical_file_sha256(ROOT / RECEIPT_PATH)
        state = _load(CURRENT_STATE_PATH)
        validate_current_state(
            state, receipt_path=RECEIPT_PATH, receipt_sha256=receipt_sha
        )
        for field, bad_value in (
            ("f000477_justice_119_action_interpretation_state", "complete"),
            ("f000477_justice_119_policy_episode_state", "complete"),
            ("f000477_justice_119_full_record_semantic_ir", "approved"),
            ("f000477_justice_119_full_record_synthesis", "approved"),
            ("f000477_justice_119_production_persistence", "complete"),
            ("f000477_justice_119_publication_state", "full_record_active"),
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(state)
                mutated["full_record_issue_interpretation"][field] = bad_value
                with self.assertRaises(UniverseAuthorityError):
                    validate_current_state(
                        mutated,
                        receipt_path=RECEIPT_PATH,
                        receipt_sha256=receipt_sha,
                    )


if __name__ == "__main__":
    unittest.main()
