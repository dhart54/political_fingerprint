from __future__ import annotations

import json
from pathlib import Path

from app.api.precomputed import build_unsupported_zip_lookup_response, get_zip_lookup_response


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "backend/fixtures/zip_multi_row_schema_sample/zip_district_mappings.json"


def test_new_table_single_current_source_backed_payload_can_be_ready() -> None:
    payload = build_payload_from_fixture("09990")

    assert classify_payload(payload) == "single_district_ready"
    assert payload["lookup_metadata"]["source_currentness"] == "current"
    assert payload["lookup_metadata"]["ambiguity_detection_level"] == "multi_row_source"
    assert len(payload["district_mappings"]) == 1


def test_new_table_same_state_multi_district_payload_is_ambiguous() -> None:
    payload = build_payload_from_fixture("09991")

    assert classify_payload(payload) == "ambiguous_zip"
    assert payload["lookup_metadata"]["can_represent_multiple_districts"] is True
    assert {row["district"] for row in payload["district_mappings"]} == {"02", "04"}


def test_new_table_multi_state_payload_is_multi_state() -> None:
    payload = build_payload_from_fixture("09992")

    assert classify_payload(payload) == "multi_state_zip"
    assert {row["state"] for row in payload["district_mappings"]} == {"NC", "SC"}


def test_new_table_fixture_sample_payload_stays_blocked() -> None:
    payload = build_payload_from_fixture("09993")

    assert classify_payload(payload) == "fixture_sample_only"
    assert payload["data_source"] == "fixtures"
    assert payload["lookup_metadata"]["fixture_sample_only"] is True


def test_new_table_missing_source_metadata_payload_stays_stale_unknown() -> None:
    payload = build_payload_from_fixture("09994")

    assert classify_payload(payload) == "stale_or_unknown_source"
    assert payload["lookup_metadata"]["stale_or_unknown_source"] is True


def test_new_table_unsupported_payload_uses_pr77_contract_shape() -> None:
    payload = build_payload_from_rows("09999", [])

    assert classify_payload(payload) == "unsupported_zip"
    assert payload["data_source"] == "none"
    assert payload["house_rep"] is None
    assert payload["senators"] == []
    assert payload["district_mappings"] == []


def test_backend_owned_unsupported_zip_payload_contract_is_standardized() -> None:
    payload = build_unsupported_zip_lookup_response(zip_code="99999")

    assert payload["zip"] == "99999"
    assert payload["status"] == "unsupported_zip"
    assert payload["lookup_state"] == "unsupported_zip"
    assert payload["data_source"] == "none"
    assert payload["state"] is None
    assert payload["district"] is None
    assert payload["house_rep"] is None
    assert payload["senators"] == []
    assert payload["district_mappings"] == []
    assert payload["lookup_metadata"] == {
        "source_type": "none",
        "source_name": None,
        "source_retrieved_at": None,
        "source_effective_date": None,
        "source_version": None,
        "source_currentness": "unsupported",
        "fixture_sample_only": False,
        "stale_or_unknown_source": False,
        "member_metadata_uncertain": False,
        "can_represent_multiple_districts": False,
        "ambiguity_detection_level": "none",
        "confidence": "unknown",
    }
    assert "invalid" not in json.dumps(payload).lower()
    assert classify_payload(payload) == "unsupported_zip"


def test_existing_old_table_zip_lookup_path_remains_stale_unknown_and_gated(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.precomputed._get_db_zip_record",
        lambda *, zip_code: {"zip": "27701", "state": "NC", "district": "04"},
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_house_rep",
        lambda **kwargs: {
            "id": 11,
            "bioguide_id": "H009999",
            "name_display": "Casey Rivera",
            "chamber": "house",
            "state": "NC",
            "district": "04",
            "party": "I",
        },
    )
    monkeypatch.setattr("app.api.precomputed._get_db_senators", lambda **kwargs: [])

    payload = get_zip_lookup_response(zip_code="27701")

    assert payload["data_source"] == "database"
    assert payload["lookup_metadata"]["source_currentness"] == "stale_or_unknown"
    assert payload["lookup_metadata"]["stale_or_unknown_source"] is True
    assert payload["lookup_metadata"]["ambiguity_detection_level"] == "single_row"
    assert classify_payload(payload) == "stale_or_unknown_source"


def build_payload_from_fixture(zip_code: str) -> dict[str, object]:
    rows = [
        row
        for row in json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        if row.get("zip") == zip_code and row.get("case") != "duplicate_active_row"
    ]
    return build_payload_from_rows(zip_code, rows)


def build_payload_from_rows(zip_code: str, rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "zip": zip_code,
            "state": None,
            "district": None,
            "data_source": "none",
            "lookup_metadata": {
                "source_type": "none",
                "source_name": None,
                "source_retrieved_at": None,
                "source_effective_date": None,
                "source_version": None,
                "source_currentness": "unsupported",
                "fixture_sample_only": False,
                "stale_or_unknown_source": False,
                "member_metadata_uncertain": False,
                "can_represent_multiple_districts": False,
                "ambiguity_detection_level": "none",
                "confidence": "unknown",
            },
            "district_mappings": [],
            "house_rep": None,
            "senators": [],
        }

    first = rows[0]
    source_metadata_present = all(
        first.get(field)
        for field in ["source_name", "source_type", "source_retrieved_at", "source_effective_date", "source_version"]
    )
    fixture_sample_only = any(
        row.get("source_currentness") == "fixture_sample" or row.get("source_type") == "fixture_sample"
        for row in rows
    )
    stale_or_unknown = (
        any(row.get("source_currentness") == "stale_or_unknown" for row in rows)
        or not source_metadata_present
    )
    source_currentness = "fixture_sample" if fixture_sample_only else "stale_or_unknown" if stale_or_unknown else "current"
    data_source = "fixtures" if fixture_sample_only else "database"
    return {
        "zip": zip_code,
        "state": first.get("state"),
        "district": first.get("district"),
        "data_source": data_source,
        "lookup_metadata": {
            "source_type": first.get("source_type"),
            "source_name": first.get("source_name") or None,
            "source_retrieved_at": first.get("source_retrieved_at"),
            "source_effective_date": first.get("source_effective_date"),
            "source_version": first.get("source_version") or None,
            "source_currentness": source_currentness,
            "fixture_sample_only": fixture_sample_only,
            "stale_or_unknown_source": stale_or_unknown,
            "member_metadata_uncertain": False,
            "can_represent_multiple_districts": True,
            "ambiguity_detection_level": "multi_row_source",
            "confidence": first.get("confidence"),
        },
        "district_mappings": [
            {
                "zip": row.get("zip"),
                "state": row.get("state"),
                "district": row.get("district"),
                "source_type": row.get("source_type"),
                "source_name": row.get("source_name") or None,
                "source_version": row.get("source_version") or None,
                "source_currentness": row.get("source_currentness"),
                "confidence": row.get("confidence"),
            }
            for row in rows
        ],
        "house_rep": {"id": "leg_synthetic_house", "state": first.get("state"), "district": first.get("district")},
        "senators": [{"id": "leg_synthetic_senate", "state": first.get("state")}],
    }


def classify_payload(payload: dict[str, object]) -> str:
    metadata = payload.get("lookup_metadata") or {}
    mappings = payload.get("district_mappings") or []
    states = {row.get("state") for row in mappings if row.get("state")}
    district_keys = {
        f"{row.get('state')}-{row.get('district')}"
        for row in mappings
        if row.get("state") and row.get("district")
    }
    source_known = bool(
        metadata.get("source_currentness") == "current"
        or metadata.get("source_retrieved_at")
        or metadata.get("source_effective_date")
        or metadata.get("source_version")
    )
    is_fixture = (
        payload.get("data_source") == "fixtures"
        or metadata.get("fixture_sample_only") is True
        or metadata.get("source_currentness") == "fixture_sample"
    )
    if payload.get("data_source") == "none" or metadata.get("source_currentness") == "unsupported":
        return "unsupported_zip"
    if len(states) > 1:
        return "multi_state_zip"
    if len(district_keys) > 1:
        return "ambiguous_zip"
    if is_fixture:
        return "fixture_sample_only"
    if metadata.get("stale_or_unknown_source") is True or metadata.get("source_currentness") == "stale_or_unknown":
        return "stale_or_unknown_source"
    if not source_known:
        return "stale_or_unknown_source"
    return "single_district_ready"
