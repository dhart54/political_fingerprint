from app.api.metadata import get_metadata_coverage
from app.main import app


def test_app_registers_metadata_coverage_route() -> None:
    routes = {route.path for route in app.routes}
    assert "/metadata/coverage" in routes
    assert "/coverage/metadata" in routes


def test_metadata_coverage_returns_fixture_window_and_counts() -> None:
    payload = get_metadata_coverage()

    assert payload["data_source"] in {"fixtures", "database"}
    assert payload["window_start"] == "2024-03-13"
    assert payload["window_end"] == "2026-03-12"
    assert payload["classification_version"] == "v1"
    assert payload["legislator_count"] >= 3
    assert payload["roll_call_count"] >= payload["eligible_roll_call_count"]
    assert 0 <= payload["source_url_share"] <= 1

