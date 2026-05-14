from dataclasses import dataclass

from app.etl.classify import ClassificationStepResult
from app.etl.ingest import IngestResult


INTERPRETATION_VERSION = "interpretation_v1"

AMBIGUOUS_PATTERNS = (
    "amendment",
    "motion",
    "table",
    "recommit",
    "reconsider",
    "suspend the rules",
)

SUPPORT_PATTERNS = (
    "on passage",
    "on agreeing",
    "on agreeing to",
    "on adoption",
    "on the bill",
)


@dataclass(frozen=True)
class VoteInterpretation:
    roll_call_id: str
    interpretation_status: str
    support_position: str | None
    oppose_position: str | None
    interpretation_reason: str
    source_url: str | None
    interpretation_version: str
    classification_version: str


@dataclass(frozen=True)
class InterpretationStepResult:
    source: str
    records_interpreted: int
    vote_interpretations: list[VoteInterpretation]


def run_interpretation(
    ingest_result: IngestResult,
    classification_result: ClassificationStepResult,
    *,
    interpretation_version: str = INTERPRETATION_VERSION,
) -> InterpretationStepResult:
    classifications_by_roll_call = {
        row.roll_call_id: row
        for row in classification_result.classified_roll_calls
    }

    interpretations = [
        interpret_roll_call(
            roll_call=roll_call,
            classification=classifications_by_roll_call[roll_call["id"]],
            interpretation_version=interpretation_version,
        )
        for roll_call in ingest_result.fixtures.roll_calls
        if roll_call["id"] in classifications_by_roll_call
    ]

    return InterpretationStepResult(
        source=ingest_result.source,
        records_interpreted=len(interpretations),
        vote_interpretations=interpretations,
    )


def interpret_roll_call(
    *,
    roll_call: dict[str, object],
    classification,
    interpretation_version: str = INTERPRETATION_VERSION,
) -> VoteInterpretation:
    if not classification.is_eligible:
        return VoteInterpretation(
            roll_call_id=str(roll_call["id"]),
            interpretation_status="insufficient_evidence",
            support_position=None,
            oppose_position=None,
            interpretation_reason=f"Not interpreted because the roll call is classified as {classification.eligibility_reason}.",
            source_url=_optional_text(roll_call.get("source_url")),
            interpretation_version=interpretation_version,
            classification_version=classification.classification_version,
        )

    question = str(roll_call.get("question", ""))
    description = str(roll_call.get("description", ""))
    combined_text = f"{question} {description}".lower()

    if any(pattern in combined_text for pattern in AMBIGUOUS_PATTERNS):
        return VoteInterpretation(
            roll_call_id=str(roll_call["id"]),
            interpretation_status="ambiguous",
            support_position=None,
            oppose_position=None,
            interpretation_reason="The roll call wording may involve an amendment or motion, so yea/nay meaning is not interpreted automatically.",
            source_url=_optional_text(roll_call.get("source_url")),
            interpretation_version=interpretation_version,
            classification_version=classification.classification_version,
        )

    if any(pattern in combined_text for pattern in SUPPORT_PATTERNS):
        return VoteInterpretation(
            roll_call_id=str(roll_call["id"]),
            interpretation_status="interpreted",
            support_position="yea",
            oppose_position="nay",
            interpretation_reason="The roll call wording indicates that a yea vote supported passage, adoption, or agreement.",
            source_url=_optional_text(roll_call.get("source_url")),
            interpretation_version=interpretation_version,
            classification_version=classification.classification_version,
        )

    return VoteInterpretation(
        roll_call_id=str(roll_call["id"]),
        interpretation_status="insufficient_evidence",
        support_position=None,
        oppose_position=None,
        interpretation_reason="The roll call wording does not provide enough deterministic signal to interpret yea/nay meaning.",
        source_url=_optional_text(roll_call.get("source_url")),
        interpretation_version=interpretation_version,
        classification_version=classification.classification_version,
    )


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
