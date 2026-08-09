from __future__ import annotations

import json
import unittest
from pathlib import Path

from backend.app.etl.full_record_source_readiness import (
    SourceReadinessError,
    assert_neutral_projection,
    build_readiness_artifact,
    derive_readiness,
    sha256_file,
    sha256_json,
    validate_artifact,
)


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "docs/editorial/full_record_reviews/source_readiness/evidence"


class FullRecordSourceReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_path = EVIDENCE_ROOT / "_m11b_test_tmp"
        self.temp_path.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        for path in self.temp_path.iterdir():
            path.unlink()
        self.temp_path.rmdir()

    def _raw(self, name: str, content: bytes) -> dict[str, str]:
        path = self.temp_path / name
        path.write_bytes(content)
        return {
            "governed_local_path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
        }

    def _projection(
        self,
        *,
        source_id: str,
        identity: str = "119:hr:1",
        stage: str = "final_passage_or_suspension_passage",
        member_action: str = "yea",
        purpose: str | None = None,
        description: str | None = None,
    ) -> dict[str, object]:
        return {
            "schema_version": "neutral_interpretation_source_projection_v1",
            "action_id": "house:119:1:1",
            "source_id": source_id,
            "congress": 119,
            "chamber": "house",
            "exact_action_identity": identity,
            "house_action_stage": stage,
            "action_date": "2025-01-03",
            "roll_number": 1,
            "member_action": member_action,
            "official_action_description": "Official action record",
            "official_purpose": purpose,
            "official_description": description,
            "text_version": "eh",
            "source_url": "https://www.congress.gov/119/bills/hr1/BILLS-119hr1eh.xml",
            "raw_provenance_sha256": "0" * 64,
        }

    def _source(
        self,
        *,
        source_id: str,
        source_type: str,
        content_class: str,
        raw: dict[str, str],
        projection: dict[str, object],
    ) -> dict[str, object]:
        projection["raw_provenance_sha256"] = raw["sha256"]
        return {
            "source_id": source_id,
            "source_type": source_type,
            "source_subject": projection["exact_action_identity"],
            "content_class": content_class,
            "source_url": projection["source_url"],
            "raw_provenance": raw,
            "neutral_projection": projection,
            "neutral_projection_sha256": sha256_json(projection),
        }

    def _ready_record(self, *, mechanism: str = "whole_measure") -> dict[str, object]:
        identity = "119:hamdt:1" if mechanism == "amendment" else "119:hr:1"
        stage = (
            "amendment"
            if mechanism == "amendment"
            else "final_passage_or_suspension_passage"
        )
        clerk_raw = self._raw("clerk.xml", b"<rollcall-vote/>")
        clerk_projection = self._projection(
            source_id="clerk", identity=identity, stage=stage
        )
        clerk_projection["source_url"] = "https://clerk.house.gov/evs/2025/roll001.xml"
        clerk = self._source(
            source_id="clerk",
            source_type="house_clerk_roll_call",
            content_class="member_action_record",
            raw=clerk_raw,
            projection=clerk_projection,
        )
        if mechanism == "amendment":
            operative_raw = self._raw("amendment.json", b'{"amendments": []}')
            operative_projection = self._projection(
                source_id="operative",
                identity=identity,
                stage=stage,
                purpose="Official amendment purpose",
            )
            operative_projection["text_version"] = (
                "official_amendment_purpose_or_description_v3"
            )
            operative_projection["source_url"] = (
                "https://api.congress.gov/v3/amendment/119/hamdt/1"
            )
            operative = self._source(
                source_id="operative",
                source_type="congress_gov_amendment_index",
                content_class="exact_amendment_purpose",
                raw=operative_raw,
                projection=operative_projection,
            )
        else:
            operative_raw = self._raw(
                "BILLS-119hr1eh.xml",
                b"<bill><legis-body><section /></legis-body></bill>",
            )
            operative_projection = self._projection(
                source_id="operative", identity=identity, stage=stage
            )
            operative = self._source(
                source_id="operative",
                source_type="congress_gov_bill_text",
                content_class="operative_measure_text",
                raw=operative_raw,
                projection=operative_projection,
            )
        return {
            "action_id": "house:119:1:1",
            "approved_universe_member": True,
            "congress": 119,
            "session": 1,
            "roll_number": 1,
            "official_action_date": "2025-01-03",
            "official_member_action": "yea",
            "exact_action_identity": identity,
            "mechanism_class": mechanism,
            "house_action_stage": stage,
            "source_conflict": False,
            "source_roles": {
                "member_action_evidence": ["clerk"],
                "exact_action_identity_and_stage_evidence": ["operative"],
                "operative_content_interpretation_input": ["operative"],
            },
            "sources": [clerk, operative],
        }

    def _state(self, record: dict[str, object]) -> str:
        return derive_readiness(record, repository_root=ROOT)[2]

    def _rules_report_record(
        self, *, renamed_as_final_text: bool = False
    ) -> dict[str, object]:
        record = self._ready_record()
        raw = self._raw("RulesReport.pdf", b"%PDF-1.7 pre-floor rules report")
        projection = self._projection(source_id="operative")
        projection["source_url"] = (
            "https://docs.house.gov/billsthisweek/20260720/RulesReport.pdf"
        )
        projection["text_version"] = (
            "eh" if renamed_as_final_text else "pre-floor-rules-report"
        )
        record["sources"][1] = self._source(
            source_id="operative",
            source_type="house_rules_committee_report",
            content_class=(
                "operative_measure_text"
                if renamed_as_final_text
                else "pre_floor_house_rules_report_context"
            ),
            raw=raw,
            projection=projection,
        )
        return record

    def test_whole_measure_with_stage_compatible_operative_text_is_ready(self) -> None:
        self.assertEqual(
            self._state(self._ready_record()), "ready_for_action_interpretation"
        )

    def test_exact_official_house_engrossed_xml_is_ready(self) -> None:
        record = self._ready_record()
        operative = record["sources"][1]
        self.assertEqual(operative["content_class"], "operative_measure_text")
        self.assertEqual(operative["neutral_projection"]["text_version"], "eh")
        self.assertTrue(operative["source_url"].endswith("eh.xml"))
        self.assertEqual(self._state(record), "ready_for_action_interpretation")

    def test_pre_floor_rules_report_alone_cannot_satisfy_final_passage(self) -> None:
        self.assertEqual(
            self._state(self._rules_report_record()), "blocked_stage_mismatch"
        )

    def test_renaming_pre_floor_rules_report_final_text_does_not_make_it_ready(
        self,
    ) -> None:
        self.assertNotEqual(
            self._state(self._rules_report_record(renamed_as_final_text=True)),
            "ready_for_action_interpretation",
        )

    def test_exact_amendment_purpose_is_ready(self) -> None:
        self.assertEqual(
            self._state(self._ready_record(mechanism="amendment")),
            "ready_for_action_interpretation",
        )

    def test_parent_metadata_cannot_replace_amendment_content(self) -> None:
        record = self._ready_record(mechanism="amendment")
        operative = record["sources"][1]
        operative["neutral_projection"]["official_purpose"] = None
        operative["neutral_projection"]["official_description"] = None
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        self.assertEqual(self._state(record), "blocked_insufficient_context")

    def test_whole_measure_metadata_without_operative_role_is_blocked(self) -> None:
        record = self._ready_record()
        record["source_roles"]["operative_content_interpretation_input"] = []
        self.assertEqual(self._state(record), "blocked_missing_operative_content")

    def test_stage_mismatch_fails_closed(self) -> None:
        record = self._ready_record()
        operative = record["sources"][1]
        operative["neutral_projection"]["house_action_stage"] = "resolution_adoption"
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        self.assertEqual(self._state(record), "blocked_stage_mismatch")

    def test_later_enacted_text_cannot_replace_house_stage_text(self) -> None:
        record = self._ready_record()
        operative = record["sources"][1]
        operative["neutral_projection"]["text_version"] = "enr"
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        self.assertEqual(self._state(record), "blocked_stage_mismatch")

    def test_source_native_description_date_cannot_override_action_date(self) -> None:
        record = self._ready_record()
        operative = record["sources"][1]
        operative["neutral_projection"]["official_action_description"] = (
            "Passed House (text: 01/03/2026 CR H1)"
        )
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        self.assertEqual(record["official_action_date"], "2025-01-03")
        self.assertEqual(operative["neutral_projection"]["action_date"], "2025-01-03")
        self.assertEqual(self._state(record), "ready_for_action_interpretation")

    def test_exact_action_identity_mismatch_fails_closed(self) -> None:
        record = self._ready_record()
        operative = record["sources"][1]
        operative["neutral_projection"]["exact_action_identity"] = "119:hr:2"
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        self.assertEqual(self._state(record), "blocked_exact_action_identity")

    def test_wrong_amendment_roll_binding_fails_closed(self) -> None:
        record = self._ready_record(mechanism="amendment")
        operative = record["sources"][1]
        operative["neutral_projection"]["roll_number"] = 2
        operative["neutral_projection_sha256"] = sha256_json(
            operative["neutral_projection"]
        )
        self.assertEqual(self._state(record), "blocked_exact_action_identity")

    def test_missing_clerk_vote_fails_closed(self) -> None:
        record = self._ready_record()
        record["source_roles"]["member_action_evidence"] = []
        self.assertEqual(self._state(record), "blocked_exact_action_identity")

    def test_source_conflict_has_closed_precedence(self) -> None:
        record = self._ready_record()
        record["source_conflict"] = True
        self.assertEqual(self._state(record), "blocked_source_conflict")

    def test_raw_digest_mismatch_fails_closed(self) -> None:
        record = self._ready_record()
        record["sources"][1]["raw_provenance"]["sha256"] = "f" * 64
        self.assertEqual(self._state(record), "blocked_exact_action_identity")

    def test_outside_universe_action_fails_closed(self) -> None:
        record = self._ready_record()
        record["approved_universe_member"] = False
        self.assertEqual(self._state(record), "blocked_exact_action_identity")

    def test_sponsor_leakage_is_rejected(self) -> None:
        projection = self._projection(source_id="source")
        projection["sponsor"] = "Member"
        with self.assertRaises(SourceReadinessError):
            assert_neutral_projection(projection)

    def test_party_leakage_is_rejected(self) -> None:
        projection = self._projection(source_id="source")
        projection["party"] = "D"
        with self.assertRaises(SourceReadinessError):
            assert_neutral_projection(projection)

    def test_cosponsor_leakage_is_rejected(self) -> None:
        projection = self._projection(source_id="source")
        projection["cosponsors"] = ["Member"]
        with self.assertRaises(SourceReadinessError):
            assert_neutral_projection(projection)

    def test_vote_direction_interpretation_leakage_is_rejected(self) -> None:
        projection = self._projection(source_id="source")
        projection["vote_direction_interpretation"] = "support"
        with self.assertRaises(SourceReadinessError):
            assert_neutral_projection(projection)

    def test_duplicate_action_records_are_rejected(self) -> None:
        artifact = build_readiness_artifact(
            artifact_id="test",
            input_bindings={},
            subject={
                "action_ids": ["house:119:1:1", "house:119:1:1"],
                "action_set_sha256": sha256_json(["house:119:1:1"]),
            },
            action_records=[self._ready_record(), self._ready_record()],
            repository_root=ROOT,
        )
        with self.assertRaisesRegex(SourceReadinessError, "duplicate"):
            validate_artifact(artifact, repository_root=ROOT)

    def test_packet_digest_tamper_is_rejected(self) -> None:
        artifact = build_readiness_artifact(
            artifact_id="test",
            input_bindings={},
            subject={
                "action_ids": ["house:119:1:1"],
                "action_set_sha256": sha256_json(["house:119:1:1"]),
            },
            action_records=[self._ready_record()],
            repository_root=ROOT,
        )
        artifact["subject"]["action_readiness"][0]["source_packet_sha256"] = "0" * 64
        with self.assertRaisesRegex(SourceReadinessError, "packet digest"):
            validate_artifact(artifact, repository_root=ROOT)

    def test_generic_evaluator_contains_no_member_or_issue_constant(self) -> None:
        module = (ROOT / "backend/app/etl/full_record_source_readiness.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("F000477", module)
        self.assertNotIn("NATIONAL_SECURITY_FOREIGN", module)
        self.assertNotIn("RulesReport07202026-final-passage", module)
        self.assertNotIn("house_rules_report_final_text", module)

    def test_m11b_correction_preserves_other_81_ready_actions(self) -> None:
        artifact_path = (
            ROOT / "docs/editorial/full_record_reviews/source_readiness/"
            "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
        )
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        records = artifact["subject"]["action_readiness"]
        self.assertEqual(len(records), 82)
        blocked = [
            record
            for record in records
            if record["readiness_state"] != "ready_for_action_interpretation"
        ]
        self.assertEqual(
            [(record["action_id"], record["readiness_state"]) for record in blocked],
            [("house:119:2:278", "blocked_stage_mismatch")],
        )


if __name__ == "__main__":
    unittest.main()
