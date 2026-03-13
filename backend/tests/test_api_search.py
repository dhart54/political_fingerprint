from app.api.search import search_for_legislators
from app.main import app


def test_app_registers_legislator_search_route() -> None:
    assert "/legislators/search" in {route.path for route in app.routes}


def test_search_legislators_returns_all_fixture_legislators_by_default() -> None:
    payload = search_for_legislators()

    assert payload["query"] == ""
    assert payload["count"] == 3
    assert [result["name_display"] for result in payload["results"]] == [
        "Alex Morgan",
        "Jordan Lee",
        "Taylor Nguyen",
    ]


def test_search_legislators_filters_case_insensitively_by_name() -> None:
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
    payload = search_for_legislators(q="zzz")

    assert payload["count"] == 0
    assert payload["results"] == []
