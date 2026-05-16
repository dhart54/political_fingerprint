import pytest
from fastapi import HTTPException

from app.api.lookup import list_supported_zips, lookup_zip
from app.main import app


def test_app_registers_zip_lookup_route() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/lookup/zip/{zip_code}" in route_paths
    assert "/lookup/zips" in route_paths


def test_lookup_zip_returns_house_rep_and_senators() -> None:
    payload = lookup_zip("27701")

    assert payload["zip"] == "27701"
    assert payload["state"] == "NC"
    assert payload["district"] == "04"
    assert payload["house_rep"]["name_display"] == "Alex Morgan"
    assert [senator["name_display"] for senator in payload["senators"]] == [
        "Jordan Lee",
        "Taylor Nguyen",
    ]


def test_lookup_zip_supports_second_fixture_zip() -> None:
    payload = lookup_zip("27601")

    assert payload["zip"] == "27601"
    assert payload["house_rep"]["bioguide_id"] == "H000001"
    assert len(payload["senators"]) == 2


def test_lookup_zip_returns_404_for_unknown_zip() -> None:
    with pytest.raises(HTTPException) as exc_info:
        lookup_zip("99999")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "ZIP code not found"


def test_list_supported_zips_returns_loaded_lookup_options() -> None:
    payload = list_supported_zips()

    assert payload["data_source"] in {"fixtures", "database"}
    assert payload["zips"]
    assert {"zip": "27601", "state": "NC", "district": "04"} in payload["zips"]
    assert {"zip": "27701", "state": "NC", "district": "04"} in payload["zips"]
