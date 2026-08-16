from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    SourceReadinessError,
    assert_neutral_projection,
    canonical_file_sha256,
    derive_readiness,
    sha256_json,
    validate_artifact,
)
from scripts.validate_m12b_environment_energy_source_readiness import (  # noqa: E402
    ARTIFACT_PATH,
    AUTHORITY_PATH,
    EXPECTED_ACTION_SET_SHA,
    EXPECTED_RECEIPT_SHA,
    INVENTORY_PATH,
    PROPOSAL_PATH,
    SCHEMA_PATH,
    validate_repository,
)
from scripts.validate_m11b_national_security_source_readiness import (  # noqa: E402
    _governed_clerk_rows,
)

M11B_ARTIFACT_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _reseal_record(record: dict[str, object]) -> None:
    packet = {
        key: value for key, value in record.items() if key != "source_packet_sha256"
    }
    record["source_packet_sha256"] = sha256_json(packet)


class M12BEnvironmentEnergySourceReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = _load(ARTIFACT_PATH)
        cls.authority = _load(AUTHORITY_PATH)
        cls.schema = _load(SCHEMA_PATH)

    def test_repository_validator_passes_exact_governed_result(self) -> None:
        result = validate_repository()
        self.assertEqual(result["total_action_count"], 63)
        self.assertEqual(result["ready_count"], 63)
        self.assertEqual(result["blocked_count"], 0)
        self.assertEqual(result["unresolved_excluded_count"], 25)
        self.assertEqual(result["source_binding_count"], 189)

    def test_receipt_is_the_exact_immutable_membership_authority(self) -> None:
        approved = self.authority["approval_binding"]["approved_action_ids"]
        records = self.artifact["subject"]["action_readiness"]
        self.assertEqual(canonical_file_sha256(AUTHORITY_PATH), EXPECTED_RECEIPT_SHA)
        self.assertEqual(
            self.artifact["subject"]["action_set_sha256"], EXPECTED_ACTION_SET_SHA
        )
        self.assertEqual([record["action_id"] for record in records], approved)
        self.assertEqual(len(approved), len(set(approved)), 63)

    def test_clerk_digest_is_bound_before_governed_xml_parse(self) -> None:
        record = copy.deepcopy(self.artifact["subject"]["action_readiness"][0])
        action_id = record["action_id"]
        clerk = next(
            source
            for source in record["sources"]
            if source["source_type"] == "house_clerk_roll_call"
        )
        clerk["raw_provenance"]["sha256"] = "0" * 64
        proposal = _load(PROPOSAL_PATH)
        inventory = _load(INVENTORY_PATH)
        candidates = {
            row["action_id"]: row
            for row in proposal["candidate_dispositions"]
            if row["action_id"] == action_id
        }
        inventory_rows = {
            row["action_id"]: row
            for row in inventory["selected_candidate_source_bindings"]
            if row["action_id"] == action_id
        }
        with self.assertRaisesRegex(SourceReadinessError, "approved Clerk digest"):
            _governed_clerk_rows(
                [record],
                candidates=candidates,
                source_inventory_bindings=inventory_rows,
            )

    def test_all_25_unresolved_and_every_outside_action_are_absent(self) -> None:
        approved = set(self.artifact["subject"]["action_ids"])
        unresolved = set(
            self.authority["approval_binding"]["exclusion_categories"][
                "boundary_review_required"
            ]["action_ids"]
        )
        self.assertEqual(len(unresolved), 25)
        self.assertTrue(approved.isdisjoint(unresolved))
        self.assertEqual(
            {
                record["action_id"]
                for record in self.artifact["subject"]["action_readiness"]
            },
            approved,
        )

    def test_generic_schema_accepts_63_and_unchanged_82_action_artifacts(self) -> None:
        schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
        self.assertNotIn('"const": 82', schema_text)
        self.assertNotIn('"minItems": 82', schema_text)
        self.assertNotIn('"maxItems": 82', schema_text)
        validator = Draft7Validator(self.schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(self.artifact)), [])
        self.assertEqual(list(validator.iter_errors(_load(M11B_ARTIFACT_PATH))), [])

    def test_readiness_state_cannot_change_without_evidence_change(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        record = artifact["subject"]["action_readiness"][0]
        record["readiness_state"] = "blocked_missing_operative_content"
        _reseal_record(record)
        artifact["source_readiness_subject_sha256"] = sha256_json(artifact["subject"])
        with self.assertRaisesRegex(SourceReadinessError, "asserted readiness state"):
            validate_artifact(artifact, repository_root=ROOT)

    def test_source_from_another_action_fails_exact_identity(self) -> None:
        first, second = copy.deepcopy(self.artifact["subject"]["action_readiness"][:2])
        first["sources"][2] = second["sources"][2]
        first["source_roles"]["operative_content_interpretation_input"] = [
            second["sources"][2]["source_id"]
        ]
        criteria, blockers, state = derive_readiness(first, repository_root=ROOT)
        self.assertFalse(criteria["all_role_bindings_resolve"])
        self.assertIn("blocked_source_conflict", blockers)
        self.assertIn("blocked_exact_action_identity", blockers)
        self.assertEqual(state, "blocked_source_conflict")

    def test_missing_operative_content_fails_closed(self) -> None:
        record = copy.deepcopy(self.artifact["subject"]["action_readiness"][0])
        record["source_roles"]["operative_content_interpretation_input"] = []
        criteria, blockers, state = derive_readiness(record, repository_root=ROOT)
        self.assertFalse(criteria["operative_content_present"])
        self.assertIn("blocked_missing_operative_content", blockers)
        self.assertEqual(state, "blocked_missing_operative_content")

    def test_source_conflict_has_deterministic_precedence(self) -> None:
        record = copy.deepcopy(self.artifact["subject"]["action_readiness"][0])
        record["source_conflict"] = True
        record["source_roles"]["operative_content_interpretation_input"] = []
        _criteria, blockers, state = derive_readiness(record, repository_root=ROOT)
        self.assertEqual(
            blockers,
            ["blocked_source_conflict", "blocked_missing_operative_content"],
        )
        self.assertEqual(state, "blocked_source_conflict")

    def test_senate_origin_house_action_rejects_house_version(self) -> None:
        record = copy.deepcopy(
            next(
                row
                for row in self.artifact["subject"]["action_readiness"]
                if row["exact_action_identity"].split(":")[1] in {"s", "sjres"}
            )
        )
        operative_id = record["source_roles"]["operative_content_interpretation_input"][
            0
        ]
        operative = next(
            source
            for source in record["sources"]
            if source["source_id"] == operative_id
        )
        operative["neutral_projection"]["text_version"] = "eh"
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        criteria, blockers, state = derive_readiness(record, repository_root=ROOT)
        self.assertFalse(criteria["operative_text_version_stage_compatible"])
        self.assertIn("blocked_stage_mismatch", blockers)
        self.assertEqual(state, "blocked_stage_mismatch")

    def test_contextual_evidence_cannot_masquerade_as_operative_content(self) -> None:
        record = copy.deepcopy(self.artifact["subject"]["action_readiness"][0])
        operative_id = record["source_roles"]["operative_content_interpretation_input"][
            0
        ]
        operative = next(
            source
            for source in record["sources"]
            if source["source_id"] == operative_id
        )
        operative["source_type"] = "house_rules_committee_report"
        operative["content_class"] = "pre_floor_house_rules_report_context"
        operative["source_url"] = "https://docs.house.gov/pre-floor-context.pdf"
        operative["neutral_projection"]["source_url"] = operative["source_url"]
        operative["neutral_projection"]["text_version"] = "pre-floor"
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        criteria, blockers, state = derive_readiness(record, repository_root=ROOT)
        self.assertFalse(criteria["operative_context_sufficient"])
        self.assertIn("blocked_stage_mismatch", blockers)
        self.assertEqual(state, "blocked_stage_mismatch")

    def test_neutral_projection_rejects_semantic_and_partisan_leakage(self) -> None:
        projection = copy.deepcopy(
            self.artifact["subject"]["action_readiness"][0]["sources"][0][
                "neutral_projection"
            ]
        )
        for key, value in (
            ("party", "D"),
            ("support_opposition", "Support"),
            ("ideology", "environmentalist"),
            ("episode", "pattern"),
            ("synthesis", "finding"),
            ("public_wording", "claim"),
        ):
            candidate = {**projection, key: value}
            with self.subTest(key=key):
                with self.assertRaises(SourceReadinessError):
                    assert_neutral_projection(candidate)


if __name__ == "__main__":
    unittest.main()
