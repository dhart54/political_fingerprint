from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.search import legislator_profile, search_for_legislators
from app.main import app


def test_app_registers_legislator_search_route() -> None:
    assert "/legislators/search" in {route.path for route in app.routes}
    assert "/legislators/{legislator_id}/profile" in {
        route.path for route in app.routes
    }


def test_route_ready_profile_lookup_returns_public_identity_fields() -> None:
    with patch(
        "app.api.precomputed._get_db_legislator_by_external_id",
        return_value=None,
    ):
        assert legislator_profile("leg_jordan_lee") == {
            "id": "leg_jordan_lee",
            "bioguide_id": "S000001",
            "name_display": "Jordan Lee",
            "chamber": "senate",
            "state": "NC",
            "district": None,
            "party": "R",
        }
        with pytest.raises(HTTPException) as exc:
            legislator_profile("leg_not_available")
    assert exc.value.status_code == 404


def test_search_legislators_returns_all_fixture_legislators_by_default() -> None:
    with patch("app.api.precomputed._search_db_legislators", return_value=None):
        payload = search_for_legislators()

    assert payload["query"] == ""
    assert payload["count"] == 3
    assert [result["name_display"] for result in payload["results"]] == [
        "Alex Morgan",
        "Jordan Lee",
        "Taylor Nguyen",
    ]


def test_search_legislators_filters_case_insensitively_by_name() -> None:
    with patch("app.api.precomputed._search_db_legislators", return_value=None):
        payload = search_for_legislators(q="jOrDaN")

    assert payload["count"] == 1
    assert payload["results"][0] == {
        "id": "leg_jordan_lee",
        "bioguide_id": "S000001",
        "name_display": "Jordan Lee",
        "chamber": "senate",
        "state": "NC",
        "district": None,
        "party": "R",
    }


def test_search_legislators_returns_empty_results_for_non_match() -> None:
    with patch("app.api.precomputed._search_db_legislators", return_value=None):
        payload = search_for_legislators(q="zzz")

    assert payload["count"] == 0
    assert payload["results"] == []
