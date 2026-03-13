from app.api.precomputed import (
    get_drift_response,
    get_fingerprint_response,
    get_summary_response,
    get_zip_lookup_response,
    search_legislators,
)


def test_search_legislators_prefers_database_results(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.precomputed._search_db_legislators",
        lambda *, query: [
            {
                "id": "leg_casey_rivera",
                "bioguide_id": "H009999",
                "name_display": "Casey Rivera",
                "chamber": "house",
                "state": "AZ",
                "district": "02",
                "party": "I",
            }
        ],
    )

    payload = search_legislators(query="casey")

    assert payload == [
        {
            "id": "leg_casey_rivera",
            "bioguide_id": "H009999",
            "name_display": "Casey Rivera",
            "chamber": "house",
            "state": "AZ",
            "district": "02",
            "party": "I",
        }
    ]


def test_get_fingerprint_response_uses_database_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.precomputed._get_db_legislator_by_external_id",
        lambda legislator_id: {
            "id": 11,
            "name_display": "Casey Rivera",
            "chamber": "house",
            "state": "AZ",
            "district": "02",
            "party": "I",
            "bioguide_id": "H009999",
        },
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_fingerprint_rows",
        lambda *, legislator_db_id: [
            {
                "domain": "ECONOMY_TAXES",
                "vote_count": 3,
                "total_votes": 9,
                "vote_share": 1 / 3,
                "window_start": "2024-03-12",
                "window_end": "2026-03-12",
                "classification_version": "db-v1",
            },
            {
                "domain": "HEALTH_SOCIAL",
                "vote_count": 0,
                "total_votes": 9,
                "vote_share": 0.0,
                "window_start": "2024-03-12",
                "window_end": "2026-03-12",
                "classification_version": "db-v1",
            },
        ],
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_chamber_medians",
        lambda **kwargs: [
            {"domain": "ECONOMY_TAXES", "median_share": 0.25},
            {"domain": "HEALTH_SOCIAL", "median_share": 0.15},
        ],
    )

    payload = get_fingerprint_response(legislator_id="leg_casey_rivera", comparison_party="ALL")

    assert payload["classification_version"] == "db-v1"
    assert payload["window_end"] == "2026-03-12"
    assert payload["fingerprint"][0]["median_share"] == 0.25


def test_get_drift_response_uses_database_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.precomputed._get_db_legislator_by_external_id",
        lambda legislator_id: {"id": 11},
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_latest_drift_row",
        lambda *, legislator_db_id: {
            "window_start": "2024-03-12",
            "window_end": "2026-03-12",
            "early_window_start": "2024-03-12",
            "early_window_end": "2025-03-11",
            "recent_window_start": "2025-03-12",
            "recent_window_end": "2026-03-12",
            "classification_version": "db-v1",
            "total_votes": 24,
            "early_total_votes": 12,
            "recent_total_votes": 12,
            "insufficient_data": False,
            "drift_value": 0.25,
        },
    )

    payload = get_drift_response(legislator_id="leg_casey_rivera")

    assert payload["classification_version"] == "db-v1"
    assert payload["drift_value"] == 0.25
    assert payload["insufficient_data"] is False


def test_get_summary_response_uses_database_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.precomputed._get_db_legislator_by_external_id",
        lambda legislator_id: {"id": 11},
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_latest_summary_row",
        lambda *, legislator_db_id: {
            "window_end": "2026-03-12",
            "classification_version": "db-v1",
            "summary_text": "Stored summary.",
            "generation_method": "cached_llm",
            "created_at": "2026-03-13T10:00:00+00:00",
        },
    )

    payload = get_summary_response(legislator_id="leg_casey_rivera")

    assert payload == {
        "legislator_id": "leg_casey_rivera",
        "window_end": "2026-03-12",
        "classification_version": "db-v1",
        "summary_text": "Stored summary.",
        "generation_method": "cached_llm",
        "created_at": "2026-03-13T10:00:00+00:00",
    }


def test_get_zip_lookup_response_uses_database_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.precomputed._get_db_zip_record",
        lambda *, zip_code: {"zip": "85001", "state": "AZ", "district": "02"},
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_house_rep",
        lambda **kwargs: {
            "id": 11,
            "bioguide_id": "H009999",
            "name_display": "Casey Rivera",
            "chamber": "house",
            "state": "AZ",
            "district": "02",
            "party": "I",
        },
    )
    monkeypatch.setattr(
        "app.api.precomputed._get_db_senators",
        lambda **kwargs: [
            {
                "id": 21,
                "bioguide_id": "S009991",
                "name_display": "Morgan Patel",
                "chamber": "senate",
                "state": "AZ",
                "district": None,
                "party": "D",
            },
            {
                "id": 22,
                "bioguide_id": "S009992",
                "name_display": "Avery Brooks",
                "chamber": "senate",
                "state": "AZ",
                "district": None,
                "party": "R",
            },
        ],
    )

    payload = get_zip_lookup_response(zip_code="85001")

    assert payload["zip"] == "85001"
    assert payload["house_rep"]["id"] == "leg_casey_rivera"
    assert [senator["id"] for senator in payload["senators"]] == [
        "leg_morgan_patel",
        "leg_avery_brooks",
    ]
