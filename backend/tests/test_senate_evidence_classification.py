from pathlib import Path

from app.etl.senate_evidence_classification import (
    PHASE_20B_APPROVAL_PHRASE,
    _build_manifest_row,
    validate_senate_evidence_classification_manifest,
    write_senate_evidence_classifications,
)


def test_senate_amendment_classification_uses_amendment_purpose_first() -> None:
    row = _base_row(
        amendment_number="S.Amdt. 1029",
        amendment_purpose="To establish a deficit-neutral reserve fund relating to protecting Medicare and Medicaid.",
        question="On the Amendment",
        description="Sullivan Amdt. No. 1029",
    )

    manifest_row = _build_manifest_row(row)

    assert manifest_row["fact_type"] == "senate_amendment_fact"
    assert manifest_row["eligible_for_write"] is True
    assert manifest_row["operation"] == "insert"
    classification = manifest_row["proposed_classification"]
    assert classification["primary_domain"] == "HEALTH_SOCIAL"
    assert classification["proposed_facet"] == "medicaid_and_medicare"
    assert classification["support_oppose_positions_inferred"] is False
    assert "Amendment purpose/identity" in classification["classification_basis"][0]


def test_senate_amendment_classification_defers_missing_purpose() -> None:
    row = _base_row(
        amendment_number="S.Amdt. 344",
        amendment_purpose="No Statement of Purpose on File.",
        question="On the Amendment",
        description="Amdt. No. 344",
    )

    manifest_row = _build_manifest_row(row)

    assert manifest_row["eligible_for_write"] is False
    assert manifest_row["operation"] == "defer"
    assert manifest_row["proposed_classification"]["eligibility_reason"] == "amendment_purpose_missing_or_ambiguous"


def test_bill_centered_motion_to_discharge_remains_deferred() -> None:
    row = _base_row(
        amendment_number=None,
        amendment_purpose=None,
        question="On the Motion to Discharge",
        description="Motion to Discharge H.R. 4 from the Committees on Appropriations and the Budget",
        bill_title="Rescissions Act of 2025",
    )

    manifest_row = _build_manifest_row(row)

    assert manifest_row["fact_type"] == "bill_centered"
    assert manifest_row["eligible_for_write"] is False
    assert manifest_row["proposed_classification"]["eligibility_reason"] == "procedural_vote"


def test_manifest_validation_rejects_parent_only_amendment_classification() -> None:
    manifest_row = _build_manifest_row(
        _base_row(
            amendment_number="S.Amdt. 1029",
            amendment_purpose="To establish a deficit-neutral reserve fund relating to protecting Medicare and Medicaid.",
            question="On the Amendment",
            description="Sullivan Amdt. No. 1029",
        )
    )
    manifest_row["proposed_classification"]["classification_basis"] = ["Parent bill title only."]
    manifest = {
        "schema_version": "senate_evidence_classification_manifest_v1",
        "considered_roll_calls": [manifest_row],
    }

    result = validate_senate_evidence_classification_manifest(manifest)

    assert result["valid"] is False
    assert "amendment classification must cite amendment purpose first" in result["errors"][0]


def test_classification_write_requires_exact_phase20b_approval_phrase_before_database_access() -> None:
    try:
        write_senate_evidence_classifications(
            manifest_path=Path("does-not-exist.json"),
            approval_phrase=PHASE_20B_APPROVAL_PHRASE.replace("Phase 20B", "Phase XXB"),
        )
    except ValueError as error:
        assert "Phase 20B approval gate" in str(error)
    else:
        raise AssertionError("Phase 20B classification write must require exact approval phrase")


def _base_row(
    *,
    amendment_number: str | None,
    amendment_purpose: str | None,
    question: str,
    description: str,
    bill_title: str = "S.Con.Res. 7",
) -> dict[str, object]:
    return {
        "roll_call_id": 1001,
        "chamber": "senate",
        "congress": 119,
        "session": 1,
        "rollcall_number": 70,
        "vote_date": "2025-02-20",
        "question": question,
        "description": description,
        "source_url": "https://www.senate.gov/example.xml",
        "bill_type": "sconres",
        "bill_number": 7,
        "bill_title": bill_title,
        "bill_summary": "",
        "bill_subjects": [],
        "amendment_number": amendment_number,
        "amendment_type": "S.Amdt." if amendment_number else None,
        "amendment_to_amendment_number": None,
        "parent_bill_type": "sconres" if amendment_number else None,
        "parent_bill_number": 7 if amendment_number else None,
        "parent_bill_display": "S.Con.Res. 7" if amendment_number else None,
        "amendment_purpose": amendment_purpose,
        "amendment_fact_status": "fact_only_uninterpreted" if amendment_number else None,
        "amendment_source_url": "https://www.senate.gov/example.xml" if amendment_number else None,
        "existing_classification_version": None,
        "existing_is_eligible": None,
        "existing_eligibility_reason": None,
        "existing_primary_domain": None,
        "existing_score_breakdown": None,
    }
