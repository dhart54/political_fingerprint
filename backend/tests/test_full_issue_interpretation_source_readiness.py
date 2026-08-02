from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.etl.interpretation_source_readiness import (  # noqa: E402
    SourceReadinessError,
    build_readiness_artifact,
    canonical_file_sha256,
    load_json,
    sha256_json,
)
from scripts.validate_full_issue_interpretation_source_readiness import (  # noqa: E402
    ARTIFACT_PATH,
    AUTHORITY_PATH,
    CURRENT_STATE_PATH,
    DISCOVERY_PATH,
    MANIFEST_PATH,
    SCHEMA_PATH,
    SOURCE_MANIFEST_PATH,
    SOURCE_MANIFEST_SCHEMA_PATH,
    validate_values,
)


class FullIssueInterpretationSourceReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load_json(ROOT / ARTIFACT_PATH)
        cls.source_manifest = load_json(ROOT / SOURCE_MANIFEST_PATH)
        cls.manifest = load_json(ROOT / MANIFEST_PATH)
        cls.authority = load_json(ROOT / AUTHORITY_PATH)
        cls.discovery = load_json(ROOT / DISCOVERY_PATH)
        cls.schema = load_json(ROOT / SCHEMA_PATH)
        cls.source_schema = load_json(ROOT / SOURCE_MANIFEST_SCHEMA_PATH)
        cls.current_state = load_json(ROOT / CURRENT_STATE_PATH)

    def _validate(
        self,
        *,
        artifact=None,
        source_manifest=None,
        current_state=None,
    ):
        return validate_values(
            artifact=artifact or copy.deepcopy(self.artifact),
            source_manifest=source_manifest or copy.deepcopy(self.source_manifest),
            approved_manifest=copy.deepcopy(self.manifest),
            authority=copy.deepcopy(self.authority),
            discovery=copy.deepcopy(self.discovery),
            schema=copy.deepcopy(self.schema),
            source_manifest_schema=copy.deepcopy(self.source_schema),
            current_state=current_state or copy.deepcopy(self.current_state),
            repository_root=ROOT,
        )

    def _build(self, source_manifest):
        return build_readiness_artifact(
            approved_manifest=self.manifest,
            authority_receipt=self.authority,
            authority_receipt_sha256=canonical_file_sha256(ROOT / AUTHORITY_PATH),
            manifest_sha256=canonical_file_sha256(ROOT / MANIFEST_PATH),
            source_manifest=source_manifest,
            source_manifest_sha256=canonical_file_sha256(ROOT / SOURCE_MANIFEST_PATH),
            discovery=self.discovery,
        )

    @staticmethod
    def _rehash_manifest(source_manifest) -> None:
        source_manifest["source_manifest_subject_sha256"] = sha256_json(
            source_manifest["subject"]
        )

    @staticmethod
    def _rehash_artifact(artifact) -> None:
        records = artifact["subject"]["action_readiness"]
        for record in records:
            record["source_packet_sha256"] = sha256_json(
                {
                    key: value
                    for key, value in record.items()
                    if key != "source_packet_sha256"
                }
            )
        readiness = Counter(record["readiness_state"] for record in records)
        blockers = Counter(
            code for record in records for code in record["blocker_codes"]
        )
        artifact["subject"]["aggregate"] = {
            "total_action_count": len(records),
            "ready_count": readiness["ready"],
            "blocked_count": len(records) - readiness["ready"],
            "counts_by_readiness_state": dict(sorted(readiness.items())),
            "counts_by_blocker": dict(sorted(blockers.items())),
        }
        artifact["source_readiness_subject_sha256"] = sha256_json(artifact["subject"])

    @staticmethod
    def _row(source_manifest, action_id):
        return next(
            row
            for row in source_manifest["subject"]["action_sources"]
            if row["action_id"] == action_id
        )

    @staticmethod
    def _source(row, source_id):
        return next(
            source for source in row["sources"] if source["source_id"] == source_id
        )

    def test_repository_artifact_passes_with_37_ready_actions(self) -> None:
        result = self._validate()
        self.assertEqual(result["total_action_count"], 37)
        self.assertEqual(result["ready_count"], 37)
        self.assertEqual(result["blocked_count"], 0)

    def test_all_actions_have_three_distinct_evidence_roles(self) -> None:
        for row in self.source_manifest["subject"]["action_sources"]:
            with self.subTest(action_id=row["action_id"]):
                roles = row["role_bindings"]
                self.assertTrue(roles["member_action_evidence"])
                self.assertTrue(roles["exact_action_identity_and_stage_evidence"])
                self.assertTrue(roles["operative_content_interpretation_input"])

    def test_identity_only_evidence_cannot_be_escalated_to_operative_content(
        self,
    ) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:1:27")
        identity_id = row["role_bindings"]["exact_action_identity_and_stage_evidence"][
            0
        ]
        row["role_bindings"]["operative_content_interpretation_input"] = [identity_id]
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        with self.assertRaisesRegex(SourceReadinessError, "identity-only"):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_generic_v3_bill_metadata_cannot_be_an_exact_action_record(self) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:2:227")
        raw_only = row["raw_provenance_only_sources"][0]
        identity_id = row["role_bindings"]["exact_action_identity_and_stage_evidence"][
            0
        ]
        source = self._source(row, identity_id)
        source["source_type"] = "congress_gov_bill_metadata"
        source["raw_provenance"] = copy.deepcopy(raw_only["raw_provenance"])
        source["neutral_projection"]["raw_provenance_sha256"] = source[
            "raw_provenance"
        ]["sha256"]
        source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_later_senate_action_cannot_replace_exact_house_action(self) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:2:227")
        identity_id = row["role_bindings"]["exact_action_identity_and_stage_evidence"][
            0
        ]
        source = self._source(row, identity_id)
        source["neutral_projection"]["official_action_description"] = (
            "Received in the Senate and referred to committee."
        )
        source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_passage_cannot_be_ready_from_title_or_policy_area_only(self) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:1:27")
        identity_id = row["role_bindings"]["exact_action_identity_and_stage_evidence"][
            0
        ]
        source = self._source(row, identity_id)
        source["neutral_projection"]["official_action_description"] = (
            "Born-Alive Abortion Survivors Protection Act"
        )
        source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_amendment_without_exact_text_cannot_be_m3_eligible(self) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:1:32")
        row["role_bindings"]["operative_content_interpretation_input"] = []
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        record = next(
            item
            for item in artifact["subject"]["action_readiness"]
            if item["action_id"] == "house:119:1:32"
        )
        self.assertIn(
            "blocked_missing_operative_content_source", record["blocker_codes"]
        )
        artifact["result"] = "complete_ready"
        record["readiness_state"] = "ready"
        record["blocker_codes"] = []
        self._rehash_artifact(artifact)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_as_amended_suspension_rejects_wrong_text_version(self) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:2:227")
        operative_id = row["role_bindings"]["operative_content_interpretation_input"][0]
        source = self._source(row, operative_id)
        source["text_version"] = "ih"
        source["neutral_projection"]["text_version"] = "ih"
        source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_raw_party_metadata_is_bound_only_as_ineligible_provenance(self) -> None:
        rows = [
            self._row(self.source_manifest, action_id)
            for action_id in (
                "house:119:2:227",
                "house:119:2:234",
                "house:119:2:240",
            )
        ]
        for row in rows:
            self.assertEqual(len(row["raw_provenance_only_sources"]), 1)
            raw = row["raw_provenance_only_sources"][0]
            self.assertEqual(raw["source_type"], "congress_gov_bill_metadata")
            self.assertFalse(raw["m3_input_eligible"])
            self.assertNotIn(raw["source_id"], json.dumps(row["role_bindings"]))

    def test_neutral_projection_rejects_sponsor_and_party_fields(self) -> None:
        for field in ("party", "sponsor", "sponsors"):
            source_manifest = copy.deepcopy(self.source_manifest)
            row = source_manifest["subject"]["action_sources"][0]
            source = row["sources"][0]
            source["neutral_projection"][field] = "excluded"
            source["neutral_projection_sha256"] = sha256_json(
                source["neutral_projection"]
            )
            self._rehash_manifest(source_manifest)
            artifact = self._build(source_manifest)
            with self.subTest(field=field), self.assertRaises(SourceReadinessError):
                self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_asserted_availability_conflict_and_constraint_states_are_rejected(
        self,
    ) -> None:
        for state_field, value in (
            ("source_availability_state", "missing"),
            ("source_conflict_state", "conflicting"),
            ("source_constraint_state", "blocked"),
        ):
            artifact = copy.deepcopy(self.artifact)
            artifact["subject"]["action_readiness"][0]["source_state"][state_field] = (
                value
            )
            self._rehash_artifact(artifact)
            with (
                self.subTest(field=state_field),
                self.assertRaisesRegex(SourceReadinessError, "asserted source state"),
            ):
                self._validate(artifact=artifact)

    def test_changed_source_identity_is_rejected_after_internal_rehash(self) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:1:27")
        identity_id = row["role_bindings"]["exact_action_identity_and_stage_evidence"][
            0
        ]
        source = self._source(row, identity_id)
        source["source_subject"] = "119:hr:9999"
        source["neutral_projection"]["measure_identity"] = "119:hr:9999"
        source["neutral_projection_sha256"] = sha256_json(source["neutral_projection"])
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_missing_operative_source_blocks_complete_ready_even_after_rehash(
        self,
    ) -> None:
        source_manifest = copy.deepcopy(self.source_manifest)
        row = self._row(source_manifest, "house:119:1:27")
        row["role_bindings"]["operative_content_interpretation_input"] = []
        self._rehash_manifest(source_manifest)
        artifact = self._build(source_manifest)
        self.assertEqual(artifact["result"], "complete_blocked")
        record = next(
            item
            for item in artifact["subject"]["action_readiness"]
            if item["action_id"] == "house:119:1:27"
        )
        self.assertEqual(
            record["readiness_state"], "blocked_missing_operative_content_source"
        )
        artifact["result"] = "complete_ready"
        with self.assertRaises(SourceReadinessError):
            self._validate(artifact=artifact, source_manifest=source_manifest)

    def test_missing_duplicate_and_outside_actions_are_rejected(self) -> None:
        for mutation in (
            lambda value: value["subject"]["action_readiness"].pop(),
            lambda value: value["subject"]["action_readiness"].append(
                copy.deepcopy(value["subject"]["action_readiness"][0])
            ),
            lambda value: value["subject"]["action_readiness"][0].__setitem__(
                "action_id", "house:119:2:999"
            ),
        ):
            artifact = copy.deepcopy(self.artifact)
            mutation(artifact)
            with self.assertRaises(SourceReadinessError):
                self._validate(artifact=artifact)

    def test_fisa_memberships_and_limitations_remain_exact(self) -> None:
        for action_id in ("house:119:2:155", "house:119:2:221"):
            artifact = copy.deepcopy(self.artifact)
            record = next(
                row
                for row in artifact["subject"]["action_readiness"]
                if row["action_id"] == action_id
            )
            record["cross_domain_scope_limitations"].pop()
            self._rehash_artifact(artifact)
            with (
                self.subTest(action_id=action_id),
                self.assertRaises(SourceReadinessError),
            ):
                self._validate(artifact=artifact)

    def test_current_state_cannot_claim_interpretation_started(self) -> None:
        state = copy.deepcopy(self.current_state)
        state["full_record_issue_interpretation"][
            "f000477_justice_119_action_interpretation_state"
        ] = "in_progress"
        with self.assertRaises(SourceReadinessError):
            self._validate(current_state=state)

    def test_build_is_deterministic(self) -> None:
        first = self._build(self.source_manifest)
        second = self._build(self.source_manifest)
        self.assertEqual(first, second)
        self.assertEqual(first, self.artifact)


if __name__ == "__main__":
    unittest.main()
