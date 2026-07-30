from __future__ import annotations

import copy

import pytest

from app.editorial_presentations.receipt_projection import (
    GovernedReceiptProjectionError,
    attach_governed_receipt_projections,
)
from app.editorial_presentations.review_state_catalog import (
    PublicReviewStateCatalogError,
    public_review_state_entries,
    validate_public_catalog,
)
from app.editorial_presentations.selector import select_public_presentations
from app.api.positions import get_legislator_position_evidence
from backend.tests.test_api_editorial_presentations import (
    _approved_artifact,
    _row,
)


def _catalog(receipts: list[dict] | None = None) -> dict:
    entry = copy.deepcopy(public_review_state_entries()[0])
    if receipts is not None:
        entry["exact_action_receipts"] = receipts
    return {
        "schema_version": "public_review_state_catalog_v1",
        "entries": [entry],
    }


def _presentation() -> dict:
    payload = select_public_presentations(
        [_row(_approved_artifact())],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    return next(
        item
        for item in payload["presentations"]
        if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
    )


def _raw_row(receipt: dict, *, status: str = "ambiguous") -> dict:
    _, congress, session, roll_call = receipt["canonical_action_id"].split(":")
    start_year = 1789 + ((int(congress) - 1) * 2)
    return {
        "roll_call_id": str(int(roll_call) + 1000),
        "vote_date": f"{start_year + int(session) - 1}-02-06",
        "chamber": "house",
        "congress": int(congress),
        "rollcall_number": int(roll_call),
        "position": receipt["member_action"].lower().replace(" ", "_"),
        "interpretation_status": status,
        "plain_english_summary": None,
        "interpretation_reason": "Stale raw interpretation.",
        "source_url": "https://clerk.house.gov/stale",
        "source_basis": [],
    }


def test_all_seven_governed_actions_have_closed_agreeing_receipt_projections() -> None:
    entry = public_review_state_entries()[0]
    receipts = entry["exact_action_receipts"]
    assert len(receipts) == entry["interpreted_actions"] == 7
    assert {receipt["canonical_action_id"] for receipt in receipts} == {
        "house:119:1:32",
        "house:119:1:33",
        "house:119:1:130",
        "house:119:1:131",
        "house:119:1:166",
        "house:119:1:275",
        "house:119:1:299",
    }
    for receipt in receipts:
        assert receipt["member_id"] == "F000477"
        assert receipt["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        assert receipt["congress_scope"] == [119]
        assert receipt["published_artifact_identity"] == (
            "f000477:justice_public_safety:119:v1"
        )
        assert receipt["interpretation_status"] == "interpreted"
        assert receipt["vote_sources"]
        assert receipt["action_meaning_sources"]


def test_roll_32_projection_uses_governed_certification_meaning_and_sources() -> None:
    roll_32 = next(
        receipt
        for receipt in public_review_state_entries()[0][
            "exact_action_receipts"
        ]
        if receipt["canonical_action_id"] == "house:119:1:32"
    )
    assert roll_32["member_action"] == "Yea"
    assert roll_32["interpretation_disposition"] == (
        "interpreted_substantive_directional"
    )
    assert "overdose-reduction certification" in roll_32["exact_action_meaning"]
    assert roll_32["episode_id"] == "halt-fentanyl-legislative-path"
    assert [source["source_id"] for source in roll_32["vote_sources"]] == [
        "clerk_roll_032"
    ]
    assert [
        source["source_id"] for source in roll_32["action_meaning_sources"]
    ] == ["congress_hamdt5"]


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_projection",
        "mismatched_member",
        "changed_digest",
        "missing_vote_source",
        "missing_meaning_source",
        "outside_sample",
    ],
)
def test_catalog_fails_closed_for_missing_stale_or_outside_projection(
    mutation: str,
) -> None:
    receipts = copy.deepcopy(
        public_review_state_entries()[0]["exact_action_receipts"]
    )
    if mutation == "missing_projection":
        receipts.pop()
    elif mutation == "mismatched_member":
        receipts[0]["member_id"] = "X000001"
    elif mutation == "changed_digest":
        receipts[0]["action_interpretation_sha256"] = "0" * 64
    elif mutation == "missing_vote_source":
        receipts[0]["vote_sources"] = []
    elif mutation == "missing_meaning_source":
        receipts[0]["action_meaning_sources"] = []
    elif mutation == "outside_sample":
        extra = copy.deepcopy(receipts[0])
        extra["canonical_action_id"] = "house:119:1:999"
        receipts.append(extra)
    with pytest.raises(PublicReviewStateCatalogError):
        validate_public_catalog(_catalog(receipts))


def test_selector_drops_analytical_copy_when_a_linked_projection_is_missing() -> None:
    state = copy.deepcopy(public_review_state_entries()[0])
    state["exact_action_receipts"] = state["exact_action_receipts"][:-1]
    result = select_public_presentations(
        [_row(_approved_artifact())],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
        review_states=[state],
    )
    justice = result["presentations"][6]
    assert justice["tier"] == "receipts_only"
    assert justice["conclusion"] is None


def test_evidence_projection_preserves_raw_row_and_replaces_stale_public_display() -> None:
    presentation = _presentation()
    rows = [
        _raw_row(receipt)
        for receipt in presentation["exact_action_receipts"]
    ]
    response = attach_governed_receipt_projections(
        {"domain": "JUSTICE_PUBLIC_SAFETY", "evidence": rows},
        presentation,
    )
    roll_32 = next(
        row
        for row in response["evidence"]
        if row["canonical_action_id"] == "house:119:1:32"
    )
    assert roll_32["interpretation_status"] == "interpreted"
    assert "overdose-reduction certification" in roll_32[
        "plain_english_summary"
    ]
    assert roll_32["raw_evidence"]["interpretation_status"] == "ambiguous"
    assert roll_32["raw_evidence"]["interpretation_reason"] == (
        "Stale raw interpretation."
    )
    assert roll_32["governed_receipt_projection"][
        "projection_source"
    ]["source_contract_id"] == "foushee_justice_public_safety_119_v1"
    assert response["governed_receipt_projection"][
        "projected_action_count"
    ] == 7


def test_evidence_projection_rejects_missing_or_conflicting_raw_action() -> None:
    presentation = _presentation()
    rows = [
        _raw_row(receipt)
        for receipt in presentation["exact_action_receipts"]
    ]
    with pytest.raises(GovernedReceiptProjectionError, match="missing"):
        attach_governed_receipt_projections(
            {"domain": "JUSTICE_PUBLIC_SAFETY", "evidence": rows[:-1]},
            presentation,
        )
    rows[0]["position"] = "nay" if rows[0]["position"] == "yea" else "yea"
    with pytest.raises(GovernedReceiptProjectionError, match="conflicts"):
        attach_governed_receipt_projections(
            {"domain": "JUSTICE_PUBLIC_SAFETY", "evidence": rows},
            presentation,
        )


def test_evidence_api_exposes_projection_source_and_preserved_raw_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    presentation = _presentation()
    rows = [
        _raw_row(receipt)
        for receipt in presentation["exact_action_receipts"]
    ]
    monkeypatch.setattr(
        "app.api.positions.get_position_evidence_response",
        lambda **_kwargs: {
            "legislator_id": "leg_valerie_p_foushee",
            "domain": "JUSTICE_PUBLIC_SAFETY",
            "evidence": rows,
        },
    )
    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr(
        "app.api.positions._load_publication_rows",
        lambda: [_row(_approved_artifact())],
    )
    response = get_legislator_position_evidence(
        "leg_valerie_p_foushee",
        "JUSTICE_PUBLIC_SAFETY",
        scope="119",
    )
    assert response["governed_receipt_projection"][
        "projected_action_count"
    ] == 7
    assert all(
        "raw_evidence" in row and "governed_receipt_projection" in row
        for row in response["evidence"]
    )
