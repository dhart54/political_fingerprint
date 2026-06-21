from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.analysis.house_comparable_families import (  # noqa: E402
    ARTIFACT_VERSION,
    ComparableFamily,
    ComparableFamilyArtifact,
    UngroupedComparableRows,
)
from app.analysis.house_record_across_congresses import (  # noqa: E402
    build_house_record_across_congresses_response,
)
from app.analysis.house_record_across_congresses_transport import (  # noqa: E402
    PUBLIC_ROUTE_EXPOSED,
    TRANSPORT_KIND,
    build_internal_house_record_across_congresses_response,
)
from app.main import app  # noqa: E402


def family(
    family_id: str,
    status: str,
    *,
    eligible: bool,
    roll_call_ids_by_congress: dict[int, tuple[int, ...]],
    caveat: str = "Fixture caveat preserved.",
) -> ComparableFamily:
    return ComparableFamily(
        family_id=family_id,
        family_name=family_id.replace("_", " ").title(),
        issue_domain="NATIONAL_SECURITY_FOREIGN",
        comparability_status=status,
        eligible_for_future_limited_record_across_congresses=eligible,
        governing_question=f"Whether the House should act on {family_id}.",
        inclusion_criteria="Reviewed fixture family.",
        exclusion_criteria="Related and ungrouped rows stay out.",
        source_grounded_rationale="Fixture source-grounded rationale.",
        caveats_and_limitations=caveat,
        congresses_represented=tuple(sorted(roll_call_ids_by_congress)),
        vote_types_represented=("final_passage",),
        roll_call_ids_by_congress=roll_call_ids_by_congress,
        measures_and_amendments_represented=(),
        representative_examples=(),
    )


def artifact_fixture() -> ComparableFamilyArtifact:
    return ComparableFamilyArtifact(
        artifact_version=ARTIFACT_VERSION,
        generated_at="2026-06-21T00:00:00Z",
        recommendations={"product_framing_recommendation": "Record Across Congresses"},
        totals={},
        explicit_non_authorization={"source_artifact_has_non_authorization": True},
        families=(
            family(
                "direct_family",
                "directly_comparable",
                eligible=True,
                roll_call_ids_by_congress={118: (101, 102), 119: (201, 202)},
                caveat="Direct fixture caveat preserved.",
            ),
            family(
                "conditional_family",
                "conditionally_comparable",
                eligible=True,
                roll_call_ids_by_congress={118: (103,), 119: (203,)},
                caveat="Conditional fixture caveat preserved.",
            ),
            family(
                "related_family",
                "related_but_not_comparable",
                eligible=False,
                roll_call_ids_by_congress={118: (104,), 119: (204,)},
            ),
        ),
        ungrouped=UngroupedComparableRows(
            comparability_status="ungrouped",
            eligible_for_future_limited_record_across_congresses=False,
            roll_call_count=2,
            roll_call_ids_by_congress={118: (105,), 119: (205,)},
            exclusion_reason="Fixture ungrouped rows.",
        ),
    )


class FakeCursor:
    def __init__(self, legislators: list[dict[str, Any]], vote_rows: list[dict[str, Any]]) -> None:
        self.legislators = legislators
        self.vote_rows = vote_rows
        self.results: list[dict[str, Any]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        if "SET TRANSACTION READ ONLY" in sql:
            self.results = []
        elif "FROM legislators" in sql:
            self.results = self.legislators
        elif "FROM roll_calls rc" in sql:
            requested_ids = set(params[1])
            self.results = [row for row in self.vote_rows if row["roll_call_id"] in requested_ids]
        else:
            raise AssertionError(f"Unexpected SQL: {sql}")

    def fetchall(self) -> list[dict[str, Any]]:
        return self.results


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor
        self.read_only = False
        self.autocommit = True
        self.closed = False

    def cursor(self, **_: object) -> FakeCursor:
        return self.fake_cursor

    def close(self) -> None:
        self.closed = True


def legislator_rows() -> list[dict[str, Any]]:
    return [
        {"id": 1, "bioguide_id": "F000000", "name_display": "Valerie P. Foushee", "chamber": "house", "state": "NC", "district": "04", "party": "D"},
        {"id": 2, "bioguide_id": "B000000", "name_display": "Aaron Bean", "chamber": "house", "state": "FL", "district": "04", "party": "R"},
        {"id": 3, "bioguide_id": "S000000", "name_display": "Adam Smith", "chamber": "house", "state": "WA", "district": "09", "party": "D"},
        {"id": 4, "bioguide_id": "H000000", "name_display": "Abraham J. Hamadeh", "chamber": "house", "state": "AZ", "district": "08", "party": "R"},
        {"id": 5, "bioguide_id": "A000000", "name_display": "Allred", "chamber": "house", "state": "TX", "district": "00", "party": "D"},
        {"id": 6, "bioguide_id": "R000000", "name_display": "Aumua Amata Coleman Radewagen", "chamber": "house", "state": "AS", "district": "00", "party": "R"},
        {"id": 7, "bioguide_id": "G000000", "name_display": "James Gallagher", "chamber": "house", "state": "CA", "district": "01", "party": "R"},
    ]


def row(roll_call_id: int, congress: int, position: str | None) -> dict[str, Any]:
    return {
        "roll_call_id": roll_call_id,
        "congress": congress,
        "position": position,
        "is_eligible": True,
        "primary_domain": "NATIONAL_SECURITY_FOREIGN",
        "interpretation_status": "interpreted",
        "support_position": "yea",
        "oppose_position": "nay",
    }


def default_vote_rows() -> list[dict[str, Any]]:
    return [
        row(101, 118, "yea"),
        row(102, 118, "not_voting"),
        row(103, 118, "nay"),
        row(104, 118, "yea"),
        row(105, 118, "yea"),
        row(201, 119, "nay"),
        row(202, 119, "present"),
        row(203, 119, "yea"),
        row(204, 119, "yea"),
        row(205, 119, "yea"),
    ]


def build_response(identifier: str = "leg_valerie_p_foushee", vote_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return build_internal_house_record_across_congresses_response(
        identifier,
        artifact=artifact_fixture(),
        connection=FakeConnection(FakeCursor(legislator_rows(), vote_rows or default_vote_rows())),
    )


def test_internal_transport_returns_adapter_response_shape_without_route() -> None:
    transport_response = build_response()
    adapter_response = build_house_record_across_congresses_response(
        "leg_valerie_p_foushee",
        artifact=artifact_fixture(),
        connection=FakeConnection(FakeCursor(legislator_rows(), default_vote_rows())),
    )

    assert TRANSPORT_KIND == "no_route_internal_backend_callable"
    assert PUBLIC_ROUTE_EXPOSED is False
    assert transport_response == adapter_response
    assert transport_response["product_framing"] == "Record Across Congresses"
    assert transport_response["non_authorization_metadata"]["internal_response_only"] is True


def test_public_route_list_and_openapi_do_not_expose_internal_transport() -> None:
    route_paths = {getattr(route, "path", "") for route in app.routes}
    openapi_paths = set(app.openapi()["paths"])

    for paths in (route_paths, openapi_paths):
        assert not any("record-across" in path or "record_across" in path for path in paths)
        assert not any("comparable" in path or "family" in path or "congress" in path for path in paths)


def test_response_has_no_disallowed_fields_or_copy_terms() -> None:
    guardrail = json.loads(
        (REPO_ROOT / "docs" / "review_packets" / "record_across_congresses_frontend_copy_guardrails.json").read_text()
    )
    response_text = json.dumps(build_response(), sort_keys=True).lower()

    for term in guardrail["disallowed_terms"]:
        assert term.lower() not in response_text


def test_approved_copy_guardrail_artifact_still_passes() -> None:
    guardrail = json.loads(
        (REPO_ROOT / "docs" / "review_packets" / "record_across_congresses_frontend_copy_guardrails.json").read_text()
    )
    approved_text = json.dumps(guardrail["approved_copy"], sort_keys=True).lower()

    assert guardrail["product_framing"] == "Record Across Congresses"
    assert not [term for term in guardrail["disallowed_terms"] if term.lower() in approved_text]


def test_required_profiles_return_expected_availability_summaries() -> None:
    profiles = {
        "leg_valerie_p_foushee": (default_vote_rows(), True, 2, 1, 1),
        "leg_aaron_bean": (default_vote_rows(), True, 2, 1, 1),
        "leg_adam_smith": (default_vote_rows(), True, 2, 1, 1),
        "leg_abraham_j_hamadeh": ([row(201, 119, "yea"), row(203, 119, "nay")], False, 0, 0, 0),
        "leg_allred": ([row(101, 118, "yea"), row(103, 118, "nay")], False, 0, 0, 0),
        "leg_aumua_amata_coleman_radewagen": ([row(101, 118, "not_voting"), row(201, 119, "yea")], False, 0, 0, 0),
        "leg_james_gallagher": ([row(101, 118, "yea")], False, 0, 0, 0),
    }

    for identifier, (rows, available, display_count, direct_count, conditional_count) in profiles.items():
        summary = build_response(identifier, rows)["summary"]
        assert summary["record_across_congresses_available"] is available
        assert summary["display_eligible_family_count"] == display_count
        assert summary["directly_comparable_display_eligible_family_count"] == direct_count
        assert summary["conditionally_comparable_display_eligible_family_count"] == conditional_count


def test_counts_caveats_and_exclusions_are_preserved() -> None:
    response = build_response()
    serialized = json.dumps(response, sort_keys=True)
    direct = response["families"][0]
    counts_118 = direct["family_evidence_counts_by_congress"]["118"]
    counts_119 = direct["family_evidence_counts_by_congress"]["119"]

    assert direct["comparability_caveat"] == "Direct fixture caveat preserved."
    assert counts_118["cast_substantive_yes_count"] == 1
    assert counts_118["cast_substantive_no_count"] == 0
    assert counts_118["not_voting_count"] == 1
    assert counts_119["cast_substantive_no_count"] == 1
    assert counts_119["present_count"] == 1
    assert "related_family" not in serialized
    assert "105" not in serialized
    assert "205" not in serialized
