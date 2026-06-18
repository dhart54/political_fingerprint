import pytest

from app.etl.session2_evidence_expansion import (
    CLASSIFICATION_APPROVAL,
    build_candidate,
    dry_run,
    write_classifications,
    _interpretation_params,
)


def _row(**overrides):
    row = {
        "roll_call_id": 1001,
        "chamber": "house",
        "rollcall_number": 12,
        "vote_date": "2026-01-10",
        "vote_type": "final_passage",
        "question": "On Passage",
        "description": "Protecting Prudent Investment of Retirement Savings Act",
        "bill_title": "Protecting Prudent Investment of Retirement Savings Act",
        "source_url": "https://clerk.house.gov/evs/2026/roll012.xml",
        "eligibility_reason": "low_classification_confidence",
    }
    row.update(overrides)
    return row


def test_build_candidate_promotes_source_grounded_final_passage() -> None:
    candidate, defer_reason = build_candidate(_row())

    assert defer_reason == ""
    assert candidate is not None
    assert candidate.category == "substantive_interpretation"
    assert candidate.domain == "ECONOMY_TAXES"
    assert candidate.vote_type == "final_passage"


def test_build_candidate_defers_amendments_without_purpose() -> None:
    candidate, defer_reason = build_candidate(
        _row(vote_type="amendment", question="On Agreeing to the Amendment")
    )

    assert candidate is None
    assert defer_reason == "defer_amendment_needs_purpose"


def test_build_candidate_defers_broad_multi_bill_procedural_rules() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            vote_type="rule",
            question="On Agreeing to the Resolution",
            description=(
                "Providing for consideration of the bills H.R. 1, H.R. 2, "
                "H.R. 3, and H.R. 4"
            ),
            bill_title="Providing for consideration of the bills H.R. 1, H.R. 2, H.R. 3, and H.R. 4",
        )
    )

    assert candidate is None
    assert defer_reason == "defer_broad_or_low_value_procedural"


def test_build_candidate_defers_cross_chamber_context_mismatch() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            chamber="house",
            vote_type="appropriations",
            question="On Passage",
            description="Making appropriations for fiscal year 2026",
            bill_title="Motion to Invoke Cloture: Motion to Proceed to H.R. 7147",
        )
    )

    assert candidate is None
    assert defer_reason == "defer_context_mismatch"


def test_procedural_context_interpretation_is_non_counting() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            vote_type="motion",
            question="On Motion to Recommit",
            description="Critical Mineral Dominance Act",
            bill_title="Critical Mineral Dominance Act",
        )
    )

    assert defer_reason == ""
    assert candidate is not None
    assert candidate.category == "procedural_context"

    params = _interpretation_params(candidate)

    assert params[0] == "insufficient_evidence"
    assert params[1] is None
    assert params[2] is None
    assert params[9] == "procedural_context"


def test_dry_run_counts_candidates_from_loaded_rows(monkeypatch) -> None:
    rows = [
        _row(roll_call_id=1, vote_type="final_passage", question="On Passage"),
        _row(roll_call_id=2, vote_type="amendment", question="On Agreeing to the Amendment"),
        _row(
            roll_call_id=3,
            vote_type="motion",
            question="On Motion to Recommit",
            description="Critical Mineral Dominance Act",
            bill_title="Critical Mineral Dominance Act",
        ),
    ]
    monkeypatch.setattr("app.etl.session2_evidence_expansion._load_session2_rows", lambda: rows)

    result = dry_run()

    assert result["candidate_count"] == 2
    assert result["candidate_split"] == {
        "substantive_interpretation": 1,
        "procedural_context": 1,
    }
    assert result["classification_updates"] == 2
    assert result["interpretation_updates"] == 2


def test_classification_write_requires_exact_approval_phrase() -> None:
    with pytest.raises(ValueError, match="approval phrase"):
        write_classifications(approval_phrase=CLASSIFICATION_APPROVAL.lower())
