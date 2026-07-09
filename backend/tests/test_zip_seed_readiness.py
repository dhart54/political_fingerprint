from __future__ import annotations

from app.etl.zip_seed_readiness import (
    PAYLOAD_AMBIGUOUS_ZIP,
    PAYLOAD_FIXTURE_SAMPLE_ONLY,
    PAYLOAD_MULTI_STATE_ZIP,
    PAYLOAD_SINGLE_DISTRICT_READY,
    PAYLOAD_STALE_OR_UNKNOWN_SOURCE,
    PAYLOAD_UNSUPPORTED_ZIP,
    classify_zip_rows,
    validate_seed_rows,
)


def test_seed_validator_accepts_single_current_source_backed_ready_row() -> None:
    report = validate_seed_rows([seed_row(zip="27701", state="NC", district="04")])

    assert report["valid"] is True
    assert report["auto_select_eligible_count"] == 1
    assert report["current_source_backed_count"] == 1
    assert report["payload_classification_by_zip"] == {"27701": PAYLOAD_SINGLE_DISTRICT_READY}
    assert report["production_coverage_claimed"] is False


def test_seed_validator_detects_ambiguous_multistate_fixture_stale_and_unsupported_states() -> None:
    rows = [
        seed_row(zip="27601", state="NC", district="02", provider_record_id="split-nc02"),
        seed_row(zip="27601", state="NC", district="04", provider_record_id="split-nc04"),
        seed_row(zip="42223", state="KY", district="01", provider_record_id="cross-ky01"),
        seed_row(zip="42223", state="TN", district="07", provider_record_id="cross-tn07"),
        seed_row(
            zip="09993",
            state="NC",
            district="04",
            source_type="fixture_sample",
            source_currentness="fixture_sample",
            confidence="unknown",
            provider_record_id="fixture",
        ),
        seed_row(
            zip="09994",
            state="NC",
            district="04",
            source_name="",
            source_retrieved_at=None,
            source_effective_date=None,
            source_version="",
            source_currentness="stale_or_unknown",
            confidence="unknown",
            provider_record_id="stale",
        ),
    ]

    report = validate_seed_rows(rows)

    assert report["valid"] is True
    assert report["auto_select_eligible_count"] == 0
    assert report["payload_classification_by_zip"]["27601"] == PAYLOAD_AMBIGUOUS_ZIP
    assert report["payload_classification_by_zip"]["42223"] == PAYLOAD_MULTI_STATE_ZIP
    assert report["payload_classification_by_zip"]["09993"] == PAYLOAD_FIXTURE_SAMPLE_ONLY
    assert report["payload_classification_by_zip"]["09994"] == PAYLOAD_STALE_OR_UNKNOWN_SOURCE
    assert classify_zip_rows([]) == PAYLOAD_UNSUPPORTED_ZIP


def test_seed_validator_detects_duplicate_active_source_period_rows() -> None:
    rows = [
        seed_row(zip="27701", state="NC", district="04", provider_record_id="first"),
        seed_row(zip="27701", state="NC", district="04", provider_record_id="second"),
    ]

    report = validate_seed_rows(rows)

    assert report["valid"] is False
    assert report["duplicate_active_source_period_key_count"] == 1
    assert any(error["field"] == "active_source_period" for error in report["errors"])


def test_seed_validator_rejects_bad_zip_state_and_current_low_confidence() -> None:
    report = validate_seed_rows(
        [
            seed_row(
                zip="1234",
                state="nc",
                district="04",
                confidence="low",
                provider_record_id="bad-format",
            )
        ]
    )

    fields = {error["field"] for error in report["errors"]}
    assert {"zip", "state", "confidence"} <= fields
    assert report["valid"] is False


def seed_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "zip": "27701",
        "state": "NC",
        "district": "04",
        "source_name": "reviewed_seed_unit_test",
        "source_type": "reviewed_zip_map",
        "source_retrieved_at": "2026-07-01",
        "source_effective_date": "2026-01-03",
        "source_version": "reviewed-seed-test-v1",
        "source_currentness": "current",
        "confidence": "source_backed",
        "is_primary": True,
        "district_type": "house",
        "congress": 119,
        "cycle": "2026",
        "valid_from": "2026-01-03",
        "valid_to": None,
        "provider_record_id": "reviewed-seed-unit-test",
        "notes": "Unit-test seed row.",
    }
    row.update(overrides)
    return row
