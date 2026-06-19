import pytest

from app.etl.evidence_118_expansion import (
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
        "session": 2,
        "rollcall_number": 215,
        "vote_date": "2024-05-16",
        "vote_type": "final_passage",
        "question": "On Passage",
        "description": "Secure the Border Act",
        "bill_title": "Secure the Border Act",
        "source_url": "https://clerk.house.gov/evs/2024/roll215.xml",
        "eligibility_reason": "low_classification_confidence",
        "interpretation_status": "insufficient_evidence",
    }
    row.update(overrides)
    return row


def test_build_candidate_promotes_source_grounded_118th_final_passage() -> None:
    candidate, defer_reason = build_candidate(_row())

    assert defer_reason == ""
    assert candidate is not None
    assert candidate.category == "substantive_interpretation"
    assert candidate.domain == "IMMIGRATION_BORDER"


def test_build_candidate_defers_amendment_without_direct_purpose() -> None:
    candidate, defer_reason = build_candidate(
        _row(vote_type="amendment", question="On Agreeing to the Amendment")
    )

    assert candidate is None
    assert defer_reason == "defer_amendment_needs_direct_purpose"


def test_build_candidate_uses_health_signal_before_broad_foreign_text() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            question="On Passage",
            description=(
                "To terminate the requirement imposed by the Director of the Centers for Disease Control "
                "and Prevention for proof of COVID-19 vaccination for foreign travelers"
            ),
            bill_title=(
                "To terminate the requirement imposed by the Director of the Centers for Disease Control "
                "and Prevention for proof of COVID-19 vaccination for foreign travelers"
            ),
        )
    )

    assert defer_reason == ""
    assert candidate is not None
    assert candidate.domain == "HEALTH_SOCIAL"


def test_build_candidate_defers_impeachment_rows_without_issue_domain() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            vote_type="other",
            question="On Agreeing to the Resolution",
            description="Impeaching an official for high crimes and misdemeanors",
            bill_title="Impeaching an official for high crimes and misdemeanors",
        )
    )

    assert candidate is None
    assert defer_reason == "defer_no_safe_issue_domain"


def test_build_candidate_classifies_defense_appropriations_as_security() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            vote_type="appropriations",
            question="On Passage",
            description="Making appropriations for the Department of Defense for fiscal year 2024",
            bill_title="Making appropriations for the Department of Defense for fiscal year 2024",
        )
    )

    assert defer_reason == ""
    assert candidate is not None
    assert candidate.domain == "NATIONAL_SECURITY_FOREIGN"


def test_build_candidate_promotes_focused_procedural_context_as_non_counting() -> None:
    candidate, defer_reason = build_candidate(
        _row(
            vote_type="motion",
            question="On Motion to Recommit",
            description="Protecting Taxpayers and Victims of Unemployment Fraud Act",
            bill_title="Protecting Taxpayers and Victims of Unemployment Fraud Act",
        )
    )

    assert defer_reason == ""
    assert candidate is not None
    assert candidate.category == "procedural_context"

    params = _interpretation_params(candidate)
    assert params[0] == "insufficient_evidence"
    assert params[1] is None
    assert params[2] is None


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
    monkeypatch.setattr("app.etl.evidence_118_expansion._load_118_rows", lambda: rows)

    result = dry_run()

    assert result["candidate_count"] == 2
    assert result["candidate_split"] == {
        "substantive_interpretation": 1,
        "procedural_context": 1,
    }


def test_classification_write_requires_exact_approval_phrase() -> None:
    with pytest.raises(ValueError, match="approval phrase"):
        write_classifications(approval_phrase=CLASSIFICATION_APPROVAL.lower())
