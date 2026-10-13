"""Existing FK facts become additive evidence identity, never reviewed meaning."""
import copy

import pytest

from app.api import precomputed
from app.editorial_presentations.reviewed_record import (
    GovernedReceiptProjectionError, overlay_reviewed_actions, union_database_actions,
)
from app.editorial_presentations.publication_replacement_runtime_v2r import install_publication_replacement_runtime_v2r
from app.api import positions
from scripts.prepare_m15b_replacement_artifacts import build, current_receipt_rows

REFERENCE = {"congress": 119, "type": "hconres", "number": 89}


def db_row(**changes):
    return {
        "roll_call_id": "3143", "vote_date": "2026-07-23", "chamber": "house",
        "congress": 119, "session": 2, "rollcall_number": 282, "position": "yea",
        "question": "On Agreeing to the Resolution", "description": "Official Iran action",
        "bill_title": "Iran War Powers resolution", "bill_summary": "",
        "classification_reason": "governed_publication_evidence",
        "measure_congress": 119, "measure_type": "hconres", "measure_number": 89,
        **changes,
    }


def test_exact_fk_identity_is_additive_without_grouping_aliases():
    payload = precomputed._serialize_evidence_row(db_row())
    assert payload["measure_reference"] == REFERENCE
    assert payload["canonical_action_id"] == "house:119:2:282"
    assert not {"bill_id", "bill_ref", "bill_type", "bill_number"} & payload.keys()


@pytest.mark.parametrize("changes", [
    {"measure_congress": None}, {"measure_type": None}, {"measure_number": None},
    {"measure_congress": 118}, {"measure_type": "amendment"}, {"measure_type": "hconres89"},
    {"measure_number": 0}, {"measure_number": -1}, {"measure_number": True},
    {"measure_number": 89.5}, {"measure_number": "89x"}, {"measure_congress": True},
    {"measure_number": 2**53}, {"measure_congress": 119.0}, {"measure_type": ""},
])
def test_missing_invalid_and_cross_congress_identity_is_nullable(changes):
    assert precomputed._serialize_evidence_row(db_row(**changes))["measure_reference"] is None


@pytest.mark.parametrize("chamber,measure_type", [("house", "sjres"), ("senate", "hr")])
def test_associated_measure_may_originate_in_other_chamber(chamber, measure_type):
    row = precomputed._serialize_evidence_row(db_row(chamber=chamber, measure_type=measure_type))
    assert row["measure_reference"] == {**REFERENCE, "type": measure_type}


def test_db_type_case_normalizes_only_known_type_tokens():
    assert precomputed._serialize_evidence_row(db_row(measure_type=" HCONRES "))["measure_reference"] == REFERENCE


def test_all_three_selects_use_existing_fk_and_typed_columns(monkeypatch):
    queries = []
    monkeypatch.setattr(precomputed, "_query_all_dicts", lambda sql, params: queries.append((sql, params)) or [])
    precomputed._get_db_position_evidence_rows(legislator_db_id=1, domain="NATIONAL_SECURITY_FOREIGN", window_start="2025-01-03", window_end="2026-07-23", classification_version="v1")
    precomputed._get_db_scoped_position_evidence_rows(legislator_db_id=1, domain="NATIONAL_SECURITY_FOREIGN", scope="119", classification_version="v1")
    precomputed._get_db_governed_position_evidence_rows(legislator_db_id=1, identities=[("house", 119, 2, 282)])
    assert len(queries) == 3
    for sql, _ in queries:
        sql = " ".join(sql.lower().split())
        assert "left join bills b on b.id = rc.bill_id" in sql
        assert "b.congress as measure_congress" in sql
        assert "b.bill_type as measure_type" in sql
        assert "b.bill_number as measure_number" in sql


def test_union_keeps_first_raw_row_and_rejects_conflicting_references():
    row = {**precomputed._serialize_evidence_row(db_row()), "measure_reference": REFERENCE}
    other = {**row, "bill_title": "Second query title"}
    assert union_database_actions([row], [other]) == [row]
    missing = {**row, "measure_reference": None}
    assert union_database_actions([missing], [row]) == [missing]
    for reference in [{**REFERENCE, "number": 90}, {**REFERENCE, "type": "hres"}]:
        with pytest.raises(GovernedReceiptProjectionError, match="measure reference"):
            union_database_actions([row], [{**other, "measure_reference": reference}])


def test_overlay_preserves_raw_measure_fact_and_never_promotes_projection_identity():
    row = {**precomputed._serialize_evidence_row(db_row()), "measure_reference": REFERENCE}
    projection = {**row, "description": "Accepted exact-action meaning"}
    original = copy.deepcopy(projection)
    response = overlay_reviewed_actions({"evidence": [row]}, [projection], domain="NATIONAL_SECURITY_FOREIGN")
    assert response["evidence"][0]["measure_reference"] == REFERENCE
    assert response["evidence"][0]["raw_evidence"]["measure_reference"] == REFERENCE
    assert projection == original
    missing = {**row, "measure_reference": None}
    assert overlay_reviewed_actions({"evidence": [missing]}, [projection], domain="NATIONAL_SECURITY_FOREIGN")["evidence"][0]["measure_reference"] is None
    with pytest.raises(GovernedReceiptProjectionError, match="measure reference"):
        overlay_reviewed_actions({"evidence": [row]}, [{**projection, "measure_reference": {**REFERENCE, "number": 90}}], domain="NATIONAL_SECURITY_FOREIGN")


def test_fixture_fallback_uses_only_existing_typed_bill_fields(monkeypatch):
    monkeypatch.setattr(precomputed, "get_connection", lambda: None)
    response = precomputed._get_fallback_position_evidence_response(legislator_id="leg_alex_morgan", domain="ECONOMY_TAXES", scope="all")
    bills = {str(bill["id"]): bill for bill in precomputed.FALLBACK_FIXTURE_DATA.bills}
    calls = {str(call["id"]): call for call in precomputed.FALLBACK_FIXTURE_DATA.roll_calls}
    assert response["evidence"]
    for row in response["evidence"]:
        bill = bills.get(str(calls[row["roll_call_id"]].get("bill_ref")))
        supplied = bill and bill.get("congress") == row["congress"] and all(bill.get(field) is not None for field in ["congress", "bill_type", "bill_number"])
        assert row["measure_reference"] == ({"congress": bill["congress"], "type": bill["bill_type"], "number": bill["bill_number"]} if supplied else None)


def test_measure_reference_is_the_only_serializer_difference():
    supplied = precomputed._serialize_evidence_row(db_row())
    absent = precomputed._serialize_evidence_row(db_row(measure_number=None))
    assert supplied.pop("measure_reference") == REFERENCE
    assert absent.pop("measure_reference") is None
    assert supplied == absent


@pytest.mark.parametrize("reference", [{**REFERENCE, "number": "89"}, {**REFERENCE, "congress": 118}, {**REFERENCE, "number": True}, {**REFERENCE, "extra": "not a fact"}])
def test_invalid_references_fail_closed_in_union_and_overlay(reference):
    row = precomputed._serialize_evidence_row(db_row())
    invalid = {**row, "measure_reference": reference}
    with pytest.raises(GovernedReceiptProjectionError, match="measure reference"):
        union_database_actions([row], [invalid])
    with pytest.raises(GovernedReceiptProjectionError, match="measure reference"):
        overlay_reviewed_actions({"evidence": [row]}, [invalid], domain="NATIONAL_SECURITY_FOREIGN")


def test_existing_raw_snapshot_conflict_cannot_be_hidden_by_reviewed_overlay():
    row = precomputed._serialize_evidence_row(db_row())
    row["raw_evidence"] = {**row, "measure_reference": {**REFERENCE, "number": 90}}
    with pytest.raises(GovernedReceiptProjectionError, match="measure reference"):
        overlay_reviewed_actions({"evidence": [row]}, [row], domain="NATIONAL_SECURITY_FOREIGN")


@pytest.mark.parametrize("scope", ["119", "all"])
def test_published_overlay_changes_only_measure_reference_fields(monkeypatch, scope):
    """Same reviewed artifact/current rows before and after a typed read fact."""
    install_publication_replacement_runtime_v2r()
    issue = "NATIONAL_SECURITY_FOREIGN"
    candidate = build()["replacements"][issue]["payload"]
    untouched = copy.deepcopy(candidate)
    rows = [{key: copy.deepcopy(value) for key, value in row.items() if key not in {
        "governed_receipt_projection", "governed_receipt_control", "interpretation_review_state", "raw_evidence",
    }} for row in current_receipt_rows(issue)]
    target = next(row for row in rows if row["canonical_action_id"] == "house:119:2:282")
    monkeypatch.setattr(positions, "get_legislator_profile", lambda **kw: {"bioguide_id": "F000477"})
    monkeypatch.setattr(positions, "_load_publication_rows", lambda: [])
    monkeypatch.setattr(positions, "_active_site_integration_publication", lambda **kw: candidate)
    monkeypatch.setattr(positions, "get_position_evidence_response", lambda **kw: {"domain": issue, "evidence": copy.deepcopy(rows)})
    monkeypatch.setattr(positions, "get_governed_position_evidence_rows", lambda **kw: copy.deepcopy(rows))
    before = positions.get_legislator_position_evidence("leg_valerie_p_foushee", issue, scope=scope)
    for row in rows:
        row["measure_reference"] = REFERENCE if row is target else None
    after = positions.get_legislator_position_evidence("leg_valerie_p_foushee", issue, scope=scope)

    def without_measure(value):
        if isinstance(value, dict):
            return {key: without_measure(item) for key, item in value.items() if key != "measure_reference"}
        if isinstance(value, list):
            return [without_measure(item) for item in value]
        return value

    assert without_measure(after) == before
    result = next(row for row in after["evidence"] if row["canonical_action_id"] == target["canonical_action_id"])
    assert result["measure_reference"] == result["raw_evidence"]["measure_reference"] == REFERENCE
    assert after["review_accounting"] == before["review_accounting"]
    assert candidate == untouched  # Includes all presentations, finding IDs and provenance hashes.
