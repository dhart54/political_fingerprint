from dataclasses import dataclass


PROCEDURAL_KEYWORDS = (
    "cloture",
    "motion to proceed",
    "quorum",
    "adjourn",
    "rule",
    "tabling",
    "recommit",
    "reconsider",
    "point of order",
)


@dataclass(frozen=True)
class EligibilityResult:
    is_eligible: bool
    eligibility_reason: str


def is_procedural(*text_values: str | None) -> bool:
    haystack = " ".join(value.strip().lower() for value in text_values if value and value.strip())
    return any(keyword in haystack for keyword in PROCEDURAL_KEYWORDS)


def evaluate_eligibility(question: str | None, description: str | None) -> EligibilityResult:
    if is_procedural(question, description):
        return EligibilityResult(
            is_eligible=False,
            eligibility_reason="procedural_vote",
        )

    return EligibilityResult(
        is_eligible=True,
        eligibility_reason="policy_vote",
    )
