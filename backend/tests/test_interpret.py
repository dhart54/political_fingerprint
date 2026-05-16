from app.etl.classify import run_classification
from app.etl.ingest import run_ingest
from app.etl.interpret import interpret_roll_call, run_interpretation


def test_run_interpretation_marks_obvious_passage_votes_as_yea_support() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result, classification_version="v1")

    result = run_interpretation(ingest_result, classification_result)

    economy_vote = next(row for row in result.vote_interpretations if row.roll_call_id == "rc_house_001")
    assert economy_vote.interpretation_status == "interpreted"
    assert economy_vote.support_position == "yea"
    assert economy_vote.oppose_position == "nay"
    assert economy_vote.classification_version == "v1"


def test_run_interpretation_does_not_interpret_ineligible_votes() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result, classification_version="v1")

    result = run_interpretation(ingest_result, classification_result)

    procedural_vote = next(row for row in result.vote_interpretations if row.roll_call_id == "rc_senate_006")
    assert procedural_vote.interpretation_status == "insufficient_evidence"
    assert procedural_vote.support_position is None
    assert "classified as procedural_vote" in procedural_vote.interpretation_reason


def test_interpret_roll_call_marks_amendment_wording_ambiguous() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result, classification_version="v1")
    classification = next(row for row in classification_result.classified_roll_calls if row.roll_call_id == "rc_house_001")

    interpretation = interpret_roll_call(
        roll_call={
            "id": "rc_custom_amendment",
            "question": "On Agreeing to the Amendment",
            "description": "Amendment to the underlying bill.",
            "source_url": "https://example.com/amendment",
        },
        classification=classification,
    )

    assert interpretation.interpretation_status == "ambiguous"
    assert interpretation.support_position is None
    assert interpretation.oppose_position is None


def test_interpret_roll_call_marks_vague_wording_insufficient() -> None:
    ingest_result = run_ingest()
    classification_result = run_classification(ingest_result, classification_version="v1")
    classification = next(row for row in classification_result.classified_roll_calls if row.roll_call_id == "rc_house_001")

    interpretation = interpret_roll_call(
        roll_call={
            "id": "rc_custom_vague",
            "question": "Question",
            "description": "Recorded vote.",
        },
        classification=classification,
    )

    assert interpretation.interpretation_status == "insufficient_evidence"
    assert interpretation.source_url is None
