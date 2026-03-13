from dataclasses import dataclass
from typing import Any


ISSUE_DOMAINS = (
    "ECONOMY_TAXES",
    "HEALTH_SOCIAL",
    "EDUCATION_WORKFORCE",
    "ENVIRONMENT_ENERGY",
    "NATIONAL_SECURITY_FOREIGN",
    "IMMIGRATION_BORDER",
    "JUSTICE_PUBLIC_SAFETY",
    "INFRASTRUCTURE_TECH_TRANSPORT",
)

CLASSIFICATION_THRESHOLD = 3

COMMITTEE_WEIGHT = 3
KEYWORD_WEIGHT = 2
SUBJECT_WEIGHT = 2

DOMAIN_SIGNALS = {
    "ECONOMY_TAXES": {
        "committees": ("finance", "ways and means", "banking", "tax", "budget", "appropriations"),
        "keywords": ("tax", "budget", "inflation", "small business", "bank", "trade", "tariff", "irs"),
        "subjects": ("economics", "taxation", "budget", "commerce", "finance"),
    },
    "HEALTH_SOCIAL": {
        "committees": ("health", "energy and commerce", "aging", "veterans affairs"),
        "keywords": ("health", "medicaid", "medicare", "hospital", "prescription", "mental health", "nutrition"),
        "subjects": ("health", "public health", "medicare", "medicaid", "social services"),
    },
    "EDUCATION_WORKFORCE": {
        "committees": ("education", "workforce", "labor"),
        "keywords": ("school", "education", "college", "student", "teacher", "workforce", "apprenticeship", "labor"),
        "subjects": ("education", "schools", "students", "workforce", "labor"),
    },
    "ENVIRONMENT_ENERGY": {
        "committees": ("environment", "natural resources", "energy"),
        "keywords": ("climate", "clean energy", "emissions", "pipeline", "drilling", "wildfire", "conservation"),
        "subjects": ("energy", "environment", "climate", "public lands", "conservation"),
    },
    "NATIONAL_SECURITY_FOREIGN": {
        "committees": ("armed services", "foreign affairs", "foreign relations", "intelligence"),
        "keywords": ("defense", "military", "missile", "alliance", "ukraine", "foreign aid", "navy", "terrorism"),
        "subjects": ("defense", "foreign policy", "national security", "military", "international affairs"),
    },
    "IMMIGRATION_BORDER": {
        "committees": ("homeland security", "judiciary"),
        "keywords": ("border", "asylum", "visa", "immigration", "migrant", "deportation", "customs"),
        "subjects": ("immigration", "border security", "visas", "asylum"),
    },
    "JUSTICE_PUBLIC_SAFETY": {
        "committees": ("judiciary", "public safety", "homeland security"),
        "keywords": ("crime", "policing", "sentencing", "fentanyl", "firearm", "prison", "law enforcement"),
        "subjects": ("criminal justice", "public safety", "policing", "courts", "crime"),
    },
    "INFRASTRUCTURE_TECH_TRANSPORT": {
        "committees": ("transportation", "infrastructure", "commerce", "science"),
        "keywords": ("bridge", "broadband", "rail", "airport", "highway", "transit", "technology", "cyber"),
        "subjects": ("transportation", "infrastructure", "technology", "broadband", "cybersecurity"),
    },
}


@dataclass(frozen=True)
class ClassificationResult:
    is_eligible: bool
    primary_domain: str | None
    score_breakdown: dict[str, dict[str, int]]
    classification_version: str
    eligibility_reason: str


def classify_vote(
    *,
    committee: str | None,
    title: str,
    summary: str,
    subject_tags: list[str] | None = None,
    classification_version: str = "v1",
) -> ClassificationResult:
    normalized_committee = normalize_text(committee)
    normalized_title = normalize_text(title)
    normalized_summary = normalize_text(summary)
    normalized_subjects = [normalize_text(tag) for tag in subject_tags or []]

    score_breakdown: dict[str, dict[str, int]] = {}
    scores: dict[str, int] = {}

    for domain in ISSUE_DOMAINS:
        signals = DOMAIN_SIGNALS[domain]
        breakdown: dict[str, int] = {}

        if contains_signal(normalized_committee, signals["committees"]):
            breakdown["committee_match"] = COMMITTEE_WEIGHT

        keyword_hits = count_signal_hits(
            f"{normalized_title} {normalized_summary}",
            signals["keywords"],
        )
        if keyword_hits:
            breakdown["keyword_match"] = keyword_hits * KEYWORD_WEIGHT

        subject_hits = sum(1 for subject in normalized_subjects if contains_signal(subject, signals["subjects"]))
        if subject_hits:
            breakdown["subject_match"] = subject_hits * SUBJECT_WEIGHT

        total_score = sum(breakdown.values())
        if total_score:
            score_breakdown[domain] = breakdown
        scores[domain] = total_score

    winning_domain = max(scores, key=scores.get)
    winning_score = scores[winning_domain]

    if winning_score < CLASSIFICATION_THRESHOLD:
        return ClassificationResult(
            is_eligible=False,
            primary_domain=None,
            score_breakdown=score_breakdown,
            classification_version=classification_version,
            eligibility_reason="low_classification_confidence",
        )

    return ClassificationResult(
        is_eligible=True,
        primary_domain=winning_domain,
        score_breakdown=score_breakdown,
        classification_version=classification_version,
        eligibility_reason="policy_vote",
    )


def normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def contains_signal(text: str, signals: tuple[str, ...]) -> bool:
    return any(signal in text for signal in signals)


def count_signal_hits(text: str, signals: tuple[str, ...]) -> int:
    return sum(1 for signal in signals if signal in text)
