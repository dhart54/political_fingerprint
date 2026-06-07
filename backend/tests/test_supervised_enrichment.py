from app.etl.supervised_enrichment import (
    PROCEDURAL_CONTEXT,
    STILL_INSUFFICIENT,
    SUBSTANTIVE_INTERPRETATION,
    build_approval_gate_checklist,
    classify_enrichment_candidate,
    validate_supervised_batch,
)


def test_classifies_source_grounded_substantive_candidate() -> None:
    classification = classify_enrichment_candidate(
        {
            "roll_call_id": 100,
            "interpretation_status": "interpreted",
            "support_position": "yea",
            "oppose_position": "nay",
            "source_basis": ["Official roll-call question", "Matched amendment purpose"],
            "plain_english_summary": "The vote was on agreeing to a source-matched amendment.",
        }
    )

    assert classification.candidate_type == SUBSTANTIVE_INTERPRETATION
    assert classification.errors == []


def test_procedural_context_must_remain_non_counting() -> None:
    classification = classify_enrichment_candidate(
        {
            "roll_call_id": 145,
            "candidate_category": "procedural-context",
            "interpretation_status": "insufficient_evidence",
            "support_position": None,
            "oppose_position": None,
            "procedural_context": True,
            "source_basis": ["House Clerk roll-call question", "Congress.gov rule resolution"],
            "what_not_to_infer": "Do not treat this as final passage of the underlying bill.",
        }
    )

    assert classification.candidate_type == PROCEDURAL_CONTEXT
    assert classification.errors == []


def test_procedural_context_rejects_support_or_oppose_positions() -> None:
    classification = classify_enrichment_candidate(
        {
            "roll_call_id": 146,
            "candidate_type": "procedural_context",
            "interpretation_status": "insufficient_evidence",
            "support_position": "yea",
            "oppose_position": None,
            "procedural_context": True,
        }
    )

    assert classification.candidate_type == PROCEDURAL_CONTEXT
    assert "procedural-context candidates must leave support_position and oppose_position null" in classification.errors


def test_issue_facet_alone_stays_insufficient() -> None:
    classification = classify_enrichment_candidate(
        {
            "roll_call_id": 200,
            "interpretation_status": "insufficient_evidence",
            "support_position": None,
            "oppose_position": None,
            "issue_facet": "house_of_representatives",
        }
    )

    assert classification.candidate_type == STILL_INSUFFICIENT
    assert classification.errors == []
    assert classification.warnings == [
        "issue_facet alone is not source meaning; keep this row insufficient without closer context"
    ]


def test_validates_mixed_supervised_batch_counts_and_errors() -> None:
    payload = {
        "candidates": [
            {
                "roll_call_id": 1,
                "interpretation_status": "interpreted",
                "support_position": "yea",
                "oppose_position": "nay",
                "source_basis": ["Matched amendment purpose"],
            },
            {
                "roll_call_id": 2,
                "candidate_type": "procedural_context",
                "interpretation_status": "insufficient_evidence",
                "support_position": None,
                "oppose_position": None,
                "procedural_context": True,
                "source_basis": ["House Clerk roll-call question"],
            },
            {
                "roll_call_id": 3,
                "interpretation_status": "insufficient_evidence",
                "support_position": None,
                "oppose_position": None,
            },
        ]
    }

    result = validate_supervised_batch(payload)

    assert result["candidate_count"] == 3
    assert result["candidate_type_counts"] == {
        SUBSTANTIVE_INTERPRETATION: 1,
        PROCEDURAL_CONTEXT: 1,
        STILL_INSUFFICIENT: 1,
    }
    assert result["errors"] == []
    assert "does not import or write production data" in " ".join(result["workflow_boundary"]).lower()


def test_approval_checklist_names_required_production_write_gates() -> None:
    checklist = build_approval_gate_checklist(
        {
            "interpretations": [
                {
                    "roll_call_id": 145,
                    "candidate_type": "procedural_context",
                    "interpretation_status": "insufficient_evidence",
                    "support_position": None,
                    "oppose_position": None,
                    "procedural_context": True,
                    "source_basis": ["House Clerk roll-call question"],
                }
            ]
        }
    )

    assert checklist["roll_call_ids"] == [145]
    assert any("Rollback artifact exists" in item for item in checklist["required_confirmations"])
    assert "support_position and oppose_position null" in checklist["approval_phrases"][PROCEDURAL_CONTEXT]
