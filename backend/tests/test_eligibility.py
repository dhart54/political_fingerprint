import pytest

from app.classification.eligibility import EligibilityResult, evaluate_eligibility, is_procedural


@pytest.mark.parametrize(
    ("question", "description"),
    [
        ("Cloture Motion on S.42", "A cloture motion to end debate"),
        ("Motion to Recommit H.R.88", "Procedural recommit motion"),
        ("Rule for consideration of H.R.900", "House rule governing floor debate"),
        ("Point of Order Raised", "Procedural point of order against the amendment"),
    ],
)
def test_is_procedural_matches_locked_keywords(question: str, description: str) -> None:
    assert is_procedural(question, description) is True


@pytest.mark.parametrize(
    ("question", "description"),
    [
        ("Passage of H.R.201", "A bill to expand broadband infrastructure"),
        ("On Passage", "A bill to improve veterans health services"),
        ("Confirmation Vote", "Nomination of an ambassador"),
    ],
)
def test_is_procedural_returns_false_for_non_procedural_votes(question: str, description: str) -> None:
    assert is_procedural(question, description) is False


def test_evaluate_eligibility_marks_procedural_votes_ineligible() -> None:
    result = evaluate_eligibility(
        "Cloture on the Motion to Proceed",
        "Procedural cloture motion",
    )

    assert result == EligibilityResult(
        is_eligible=False,
        eligibility_reason="procedural_vote",
    )


def test_evaluate_eligibility_marks_policy_votes_eligible() -> None:
    result = evaluate_eligibility(
        "On Passage of H.R.100",
        "A bill to modernize bridges and highways",
    )

    assert result == EligibilityResult(
        is_eligible=True,
        eligibility_reason="policy_vote",
    )
