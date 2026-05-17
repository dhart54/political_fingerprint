from pathlib import Path

import pytest

from app.etl.candidate_evidence import _parse_record, load_candidate_evidence


SEED_PATH = Path(__file__).resolve().parents[2] / "docs" / "candidate_evidence" / "nc04_nida_allam_seed.json"


def test_load_candidate_evidence_accepts_seed_records() -> None:
    records = load_candidate_evidence(SEED_PATH)

    assert len(records) == 3
    assert {record.issue_domain for record in records} == {
        "ECONOMY_TAXES",
        "EDUCATION_WORKFORCE",
        "HEALTH_SOCIAL",
    }
    assert all(record.evidence_tier == "institutional_record" for record in records)
    assert all(record.confidence == "medium" for record in records)


def test_load_candidate_evidence_rejects_persuasive_language() -> None:
    with pytest.raises(ValueError, match="Forbidden candidate evidence language"):
        _parse_record(
            {
                "external_candidate_id": "H2NC06098",
                "evidence_tier": "sourced_stated_position",
                "issue_domain": "HEALTH_SOCIAL",
                "statement_text": "Support this candidate on healthcare.",
                "neutral_summary": "Support this candidate.",
                "confidence": "medium",
                "source_url": "https://example.com",
                "source_type": "campaign_issue_page",
                "source_retrieved_at": "2026-05-17T00:00:00Z",
                "external_evidence_id": "bad",
            }
        )
