from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.analysis.house_comparable_families import (  # noqa: E402
    ARTIFACT_VERSION,
    ComparableFamily,
    ComparableFamilyArtifact,
    UngroupedComparableRows,
)
from app.analysis import house_record_across_congresses as adapter  # noqa: E402
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


def row(roll_call_id: int, congress: int, position: str | None, *, eligible: bool = True, status: str = "interpreted") -> dict[str, Any]:
    return {
        "roll_call_id": roll_call_id,
        "congress": congress,
        "position": position,
        "is_eligible": eligible,
        "primary_domain": "NATIONAL_SECURITY_FOREIGN" if eligible else None,
        "interpretation_status": status,
        "support_position": "yea" if status == "interpreted" else None,
        "oppose_position": "nay" if status == "interpreted" else None,
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


def build_response(
    identifier: str = "leg_valerie_p_foushee",
    vote_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return adapter.build_house_record_across_congresses_response(
        identifier,
        artifact=artifact_fixture(),
        connection=FakeConnection(FakeCursor(legislator_rows(), vote_rows or default_vote_rows())),
    )


def collect_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(collect_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(collect_keys(child))
    return keys


def test_response_shape_product_framing_and_non_authorization_metadata() -> None:
    response = build_response()

    assert response["response_kind"] == adapter.RESPONSE_KIND
    assert response["product_framing"] == "Record Across Congresses"
    assert response["availability_explanation"] == "This internal response reports factual family-level evidence availability and counts only."
    assert response["artifact_version"] == ARTIFACT_VERSION
    assert response["non_authorization_metadata"] == {
        "internal_response_only": True,
        "public_route_exposed": False,
        "only_factual_evidence_availability_and_counts": True,
        "unsupported_inferences_are_not_generated": True,
        "frontend_copy_not_authorized": True,
        "voting_recommendation_not_authorized": True,
        "requires_review_before_public_product_use": True,
    }


def test_allowed_field_names_and_absence_of_disallowed_field_names() -> None:
    response = build_response()
    keys = collect_keys(response)

    assert {
        "record_across_congresses_available",
        "evidence_available_in_both_congresses",
        "family_evidence_counts_by_congress",
        "not_voting_count",
        "missing_no_record_count",
        "comparability_caveat",
    }.issubset(keys)
    for key in keys:
        normalized_key = key.lower()
        assert not any(term in normalized_key for term in adapter.DISALLOWED_RESPONSE_FIELD_TERMS)


def test_no_generated_unsupported_label_wording() -> None:
    response_text = json.dumps(build_response(), sort_keys=True).lower()

    assert "label" not in response_text
    assert not any(term in response_text for term in adapter.DISALLOWED_RESPONSE_FIELD_TERMS)


def test_direct_conditional_and_display_summary_counts() -> None:
    summary = build_response()["summary"]

    assert summary["eligible_comparable_family_count"] == 2
    assert summary["record_across_congresses_available"] is True
    assert summary["display_eligible_family_count"] == 2
    assert summary["directly_comparable_display_eligible_family_count"] == 1
    assert summary["conditionally_comparable_display_eligible_family_count"] == 1


def test_ineligible_profile_response_has_unavailable_reasons() -> None:
    response = build_response("leg_james_gallagher", [row(101, 118, "yea")])

    assert response["summary"]["record_across_congresses_available"] is False
    assert response["summary"]["display_eligible_family_count"] == 0
    assert {family["unavailable_reason"] for family in response["families"]} == {
        "substantive_yes_no_evidence_not_available_in_both_congresses"
    }


def test_caveats_and_separated_counts_are_preserved() -> None:
    direct = build_response()["families"][0]
    counts_118 = direct["family_evidence_counts_by_congress"]["118"]
    counts_119 = direct["family_evidence_counts_by_congress"]["119"]

    assert direct["comparability_caveat"] == "Direct fixture caveat preserved."
    assert counts_118["cast_substantive_yes_count"] == 1
    assert counts_118["cast_substantive_no_count"] == 0
    assert counts_118["not_voting_count"] == 1
    assert counts_118["present_count"] == 0
    assert counts_118["missing_no_record_count"] == 0
    assert counts_119["cast_substantive_yes_count"] == 0
    assert counts_119["cast_substantive_no_count"] == 1
    assert counts_119["not_voting_count"] == 0
    assert counts_119["present_count"] == 1
    assert counts_119["missing_no_record_count"] == 0
    assert counts_118["roll_call_ids_considered"] == [101, 102]
    assert counts_119["roll_call_ids_considered"] == [201, 202]


def test_missing_counts_are_preserved_separately() -> None:
    response = build_response("leg_allred", [row(101, 118, "yea")])
    direct = response["families"][0]

    assert direct["family_evidence_counts_by_congress"]["118"]["missing_no_record_count"] == 1
    assert direct["family_evidence_counts_by_congress"]["119"]["missing_no_record_count"] == 2
    assert direct["family_evidence_counts_by_congress"]["119"]["cast_substantive_yes_count"] == 0
    assert direct["family_evidence_counts_by_congress"]["119"]["cast_substantive_no_count"] == 0


def test_related_and_ungrouped_rows_are_not_exposed_as_eligible() -> None:
    response_text = json.dumps(build_response(), sort_keys=True)

    assert "related_family" not in response_text
    assert "105" not in response_text
    assert "205" not in response_text


def test_required_validation_profile_identifiers_build_response() -> None:
    profile_rows = {
        "leg_valerie_p_foushee": default_vote_rows(),
        "leg_aaron_bean": default_vote_rows(),
        "leg_adam_smith": default_vote_rows(),
        "leg_abraham_j_hamadeh": [row(201, 119, "yea"), row(203, 119, "nay")],
        "leg_allred": [row(101, 118, "yea"), row(103, 118, "nay")],
        "leg_aumua_amata_coleman_radewagen": [row(101, 118, "not_voting"), row(201, 119, "yea")],
        "leg_james_gallagher": [row(101, 118, "yea")],
    }

    for identifier, rows in profile_rows.items():
        response = build_response(identifier, rows)
        assert response["legislator_identifier"] == identifier
        assert response["families"]
        assert "comparability_caveat" in response["families"][0]
        assert set(response["families"][0]["family_evidence_counts_by_congress"]) == {"118", "119"}


def test_no_public_route_or_openapi_exposure_added() -> None:
    route_paths = {getattr(route, "path", "") for route in app.routes}
    openapi_paths = set(app.openapi()["paths"])

    assert not any("record-across" in path or "record_across" in path for path in route_paths)
    assert not any("record-across" in path or "record_across" in path for path in openapi_paths)
    assert not any("comparable" in path or "family" in path for path in route_paths)
