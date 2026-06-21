from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.analysis.house_comparable_families import (  # noqa: E402
    ARTIFACT_VERSION,
    ComparableFamily,
    ComparableFamilyArtifact,
    UngroupedComparableRows,
    load_house_comparable_family_artifact,
)
from app.analysis import house_comparable_family_legislator as helper  # noqa: E402
from app.main import app  # noqa: E402


def family(
    family_id: str,
    status: str,
    *,
    eligible: bool,
    roll_call_ids_by_congress: dict[int, tuple[int, ...]],
) -> ComparableFamily:
    return ComparableFamily(
        family_id=family_id,
        family_name=family_id.replace("_", " ").title(),
        issue_domain="NATIONAL_SECURITY_FOREIGN",
        comparability_status=status,
        eligible_for_future_limited_record_across_congresses=eligible,
        governing_question=f"Whether the House should act on {family_id}.",
        inclusion_criteria="Reviewed family fixture.",
        exclusion_criteria="Related and ungrouped rows stay out.",
        source_grounded_rationale="Fixture source-grounded rationale.",
        caveats_and_limitations="Fixture caveat.",
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
        explicit_non_authorization={"does_not_authorize_continuity_change_claims": True},
        families=(
            family("direct_family", "directly_comparable", eligible=True, roll_call_ids_by_congress={118: (101, 102), 119: (201, 202)}),
            family("conditional_family", "conditionally_comparable", eligible=True, roll_call_ids_by_congress={118: (103,), 119: (203,)}),
            family("related_family", "related_but_not_comparable", eligible=False, roll_call_ids_by_congress={118: (104,), 119: (204,)}),
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
        self.executed: list[str] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.executed.append(sql)
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
        {"id": 2, "bioguide_id": "S000000", "name_display": "Adam Smith", "chamber": "house", "state": "WA", "district": "09", "party": "D"},
        {"id": 3, "bioguide_id": "H000000", "name_display": "Abraham J. Hamadeh", "chamber": "house", "state": "AZ", "district": "08", "party": "R"},
        {"id": 4, "bioguide_id": "A000000", "name_display": "Allred", "chamber": "house", "state": "TX", "district": "00", "party": "D"},
        {"id": 5, "bioguide_id": "R000000", "name_display": "Aumua Amata Coleman Radewagen", "chamber": "house", "state": "AS", "district": "00", "party": "R"},
        {"id": 6, "bioguide_id": "G000000", "name_display": "James Gallagher", "chamber": "house", "state": "CA", "district": "01", "party": "R"},
        {"id": 7, "bioguide_id": "T000000", "name_display": "Ted Budd", "chamber": "senate", "state": "NC", "district": None, "party": "R"},
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


def vote_rows() -> list[dict[str, Any]]:
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


def build_result(identifier: str = "leg_valerie_p_foushee") -> helper.LegislatorComparableFamilyEvidenceResult:
    cursor = FakeCursor(legislator_rows(), vote_rows())
    connection = FakeConnection(cursor)
    return helper.get_house_comparable_family_legislator_evidence(
        identifier,
        artifact=artifact_fixture(),
        connection=connection,
    )


def test_loads_through_pr46_accessor() -> None:
    artifact = load_house_comparable_family_artifact()

    assert artifact.artifact_version == ARTIFACT_VERSION
    assert artifact.eligible_families()


def test_helper_output_shape_and_valid_house_legislator_counts() -> None:
    result = build_result()

    assert result.legislator_identifier == "leg_valerie_p_foushee"
    assert result.artifact_version_used == ARTIFACT_VERSION
    assert result.eligible_comparable_families_considered == 2
    assert [family.family_id for family in result.families] == ["direct_family", "conditional_family"]
    assert result.non_authorization_metadata["does_not_authorize_continuity_change_claims"] is True


def test_not_voting_present_and_missing_are_separate_from_yes_no_counts() -> None:
    direct = build_result().families[0]

    counts_118 = direct.counts_by_congress[118]
    counts_119 = direct.counts_by_congress[119]
    assert counts_118.cast_substantive_yes_count == 1
    assert counts_118.cast_substantive_no_count == 0
    assert counts_118.not_voting_count == 1
    assert counts_118.total_cast_substantive_yes_no_rows == 1
    assert counts_119.cast_substantive_yes_count == 0
    assert counts_119.cast_substantive_no_count == 1
    assert counts_119.present_count == 1
    assert counts_119.total_cast_substantive_yes_no_rows == 1


def test_118th_only_119th_only_sparse_and_no_both_flags() -> None:
    artifact = artifact_fixture()
    allred_rows = [row(101, 118, "yea"), row(102, 118, "nay"), row(103, 118, "yea")]
    hamadeh_rows = [row(201, 119, "yea"), row(202, 119, "nay"), row(203, 119, "yea")]
    sparse_rows = [row(101, 118, "yea")]
    for identifier, rows in (
        ("leg_allred", allred_rows),
        ("leg_abraham_j_hamadeh", hamadeh_rows),
        ("leg_james_gallagher", sparse_rows),
    ):
        result = helper.get_house_comparable_family_legislator_evidence(
            identifier,
            artifact=artifact,
            connection=FakeConnection(FakeCursor(legislator_rows(), rows)),
        )
        assert not any(family.record_across_congresses_display_eligible for family in result.families)


def test_not_voting_burden_profile_does_not_mix_not_voting_into_yes_no() -> None:
    result = helper.get_house_comparable_family_legislator_evidence(
        "leg_aumua_amata_coleman_radewagen",
        artifact=artifact_fixture(),
        connection=FakeConnection(FakeCursor(legislator_rows(), [row(101, 118, "not_voting"), row(201, 119, "yea")])),
    )
    direct = result.families[0]

    assert direct.counts_by_congress[118].not_voting_count == 1
    assert direct.counts_by_congress[118].total_cast_substantive_yes_no_rows == 0
    assert direct.counts_by_congress[119].cast_substantive_yes_count == 1


def test_related_and_ungrouped_rows_are_excluded_from_eligible_output() -> None:
    serialized = json.dumps(build_result().to_dict(), sort_keys=True)

    assert "related_family" not in serialized
    assert "105" not in serialized
    assert "205" not in serialized


def test_direct_and_conditional_family_distinction() -> None:
    direct, conditional = build_result().families

    assert direct.has_direct_family_vote_in_both_congresses is True
    assert direct.has_conditional_family_vote_in_both_congresses is False
    assert conditional.has_direct_family_vote_in_both_congresses is False
    assert conditional.has_conditional_family_vote_in_both_congresses is True


def test_118th_and_119th_counts_remain_separate() -> None:
    direct = build_result().families[0]

    assert direct.counts_by_congress[118].roll_call_ids_considered == (101, 102)
    assert direct.counts_by_congress[119].roll_call_ids_considered == (201, 202)
    assert direct.counts_by_congress[118].cast_substantive_yes_count == 1
    assert direct.counts_by_congress[119].cast_substantive_no_count == 1


def test_no_continuity_change_or_movement_fields_are_generated() -> None:
    output = build_result().to_dict()
    keys = set()

    def collect_keys(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                keys.add(str(key))
                collect_keys(child)
        elif isinstance(value, list):
            for child in value:
                collect_keys(child)

    collect_keys(output)
    assert keys.isdisjoint(helper.FORBIDDEN_OUTPUT_KEYS)


def test_no_public_endpoint_added() -> None:
    routes = {getattr(route, "path", "") for route in app.routes}

    assert not any("comparable" in route or "family" in route for route in routes)


def test_owning_connection_uses_read_only_transaction(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = FakeCursor(legislator_rows(), vote_rows())
    connection = FakeConnection(cursor)
    monkeypatch.setattr(helper, "get_connection", lambda: connection)

    helper.get_house_comparable_family_legislator_evidence("leg_valerie_p_foushee", artifact=artifact_fixture())

    assert connection.read_only is True
    assert connection.autocommit is False
    assert connection.closed is True
    assert any("SET TRANSACTION READ ONLY" in sql for sql in cursor.executed)


def test_unknown_or_non_house_identifier_fails() -> None:
    with pytest.raises(helper.HouseComparableFamilyLegislatorError, match="Unknown"):
        helper.get_house_comparable_family_legislator_evidence(
            "leg_missing",
            artifact=artifact_fixture(),
            connection=FakeConnection(FakeCursor(legislator_rows(), [])),
        )
    with pytest.raises(helper.HouseComparableFamilyLegislatorError, match="House-only"):
        helper.get_house_comparable_family_legislator_evidence(
            "leg_ted_budd",
            artifact=artifact_fixture(),
            connection=FakeConnection(FakeCursor(legislator_rows(), [])),
        )
