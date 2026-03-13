import pytest

from app.summaries.cache import (
    SummaryRecord,
    get_or_create_summary,
    persist_summary_record,
    validate_summary_text,
)


def test_get_or_create_summary_persists_generated_fallback(monkeypatch) -> None:
    persisted = {}

    monkeypatch.setattr("app.summaries.cache.has_legislator", lambda **kwargs: True)
    monkeypatch.setattr("app.summaries.cache.load_summary_record", lambda **kwargs: None)
    monkeypatch.setattr(
        "app.summaries.cache.get_fingerprint_response",
        lambda **kwargs: {
            "window_end": "2026-03-12",
            "classification_version": "v1",
            "fingerprint": [
                {
                    "domain": "EDUCATION_WORKFORCE",
                    "vote_count": 2,
                    "total_votes": 5,
                    "vote_share": 0.4,
                }
            ],
        },
    )
    monkeypatch.setattr(
        "app.summaries.cache.get_drift_response",
        lambda **kwargs: {
            "insufficient_data": True,
            "drift_value": None,
        },
    )

    def fake_persist_summary_record(**kwargs):
        persisted.update(kwargs)
        return SummaryRecord(**kwargs)

    monkeypatch.setattr("app.summaries.cache.persist_summary_record", fake_persist_summary_record)

    record = get_or_create_summary(legislator_id="leg_alex_morgan")

    assert record is not None
    assert persisted["generation_method"] == "deterministic_fallback"
    assert persisted["classification_version"] == "v1"
    assert "eligible votes" in persisted["summary_text"]


def test_persist_summary_record_returns_record_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("app.summaries.cache._get_legislator_db_row", lambda **kwargs: None)

    record = persist_summary_record(
        legislator_id="leg_alex_morgan",
        window_end="2026-03-12",
        classification_version="v1",
        summary_text="Stored fallback summary.",
        generation_method="deterministic_fallback",
        created_at="2026-03-13T12:00:00+00:00",
    )

    assert record == SummaryRecord(
        legislator_id="leg_alex_morgan",
        window_end="2026-03-12",
        classification_version="v1",
        summary_text="Stored fallback summary.",
        generation_method="deterministic_fallback",
        created_at="2026-03-13T12:00:00+00:00",
    )


def test_validate_summary_text_blocks_forbidden_words() -> None:
    with pytest.raises(ValueError) as exc_info:
        validate_summary_text("This politician is extreme.")

    assert "forbidden term" in str(exc_info.value)
