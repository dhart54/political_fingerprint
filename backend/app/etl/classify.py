from dataclasses import dataclass

from app.classification.classifier import ClassificationResult, classify_vote
from app.classification.eligibility import evaluate_eligibility
from app.etl.ingest import IngestResult


@dataclass(frozen=True)
class ClassifiedRollCall:
    roll_call_id: str
    bill_id: str
    chamber: str
    vote_date: str
    is_eligible: bool
    eligibility_reason: str
    primary_domain: str | None
    score_breakdown: dict[str, dict[str, int]]
    classification_version: str


@dataclass(frozen=True)
class ClassificationStepResult:
    source: str
    records_loaded: int
    records_classified: int
    classified_roll_calls: list[ClassifiedRollCall]


def run_classification(
    ingest_result: IngestResult,
    *,
    classification_version: str = "v1",
) -> ClassificationStepResult:
    bills_by_id = {bill["id"]: bill for bill in ingest_result.fixtures.bills}
    classified_roll_calls: list[ClassifiedRollCall] = []

    for roll_call in ingest_result.fixtures.roll_calls:
        bill = bills_by_id[roll_call["bill_ref"]]
        eligibility = evaluate_eligibility(roll_call["question"], roll_call["description"])

        if not eligibility.is_eligible:
            classified_roll_calls.append(
                ClassifiedRollCall(
                    roll_call_id=roll_call["id"],
                    bill_id=bill["id"],
                    chamber=roll_call["chamber"],
                    vote_date=roll_call["vote_date"],
                    is_eligible=False,
                    eligibility_reason=eligibility.eligibility_reason,
                    primary_domain=None,
                    score_breakdown={},
                    classification_version=classification_version,
                )
            )
            continue

        classification: ClassificationResult = classify_vote(
            committee=bill.get("committee"),
            title=bill["title"],
            summary=bill["summary"],
            subject_tags=ingest_result.fixtures.vote_subject_tags.get(bill["id"], bill.get("subjects", [])),
            classification_version=classification_version,
        )
        classified_roll_calls.append(
            ClassifiedRollCall(
                roll_call_id=roll_call["id"],
                bill_id=bill["id"],
                chamber=roll_call["chamber"],
                vote_date=roll_call["vote_date"],
                is_eligible=classification.is_eligible,
                eligibility_reason=classification.eligibility_reason,
                primary_domain=classification.primary_domain,
                score_breakdown=classification.score_breakdown,
                classification_version=classification.classification_version,
            )
        )

    return ClassificationStepResult(
        source=ingest_result.source,
        records_loaded=ingest_result.records_loaded,
        records_classified=len(classified_roll_calls),
        classified_roll_calls=classified_roll_calls,
    )
