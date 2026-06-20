from pathlib import Path

import pytest

from app.etl.amendment_evidence import (
    CANONICAL_AMENDMENT_EVIDENCE_STEPS,
    WritePrecondition,
    interpretation_package_respects_counting_boundary,
    parse_house_amendment_identity,
    parse_senate_amendment_identity,
    require_write_precondition,
    validate_write_precondition,
)


def test_canonical_path_names_required_pipeline_stages() -> None:
    assert CANONICAL_AMENDMENT_EVIDENCE_STEPS == (
        "fetch/cache",
        "normalize identity and relationships",
        "validate direct-source grounding",
        "classify eligibility and issue",
        "build interpretation package",
        "preview writes",
        "capture rollback",
        "perform bounded writes",
        "recompute affected outputs",
        "reconcile and verify",
        "rerun to prove idempotency",
    )


def test_house_amendment_identity_preserves_printed_number_and_sponsor() -> None:
    identity = parse_house_amendment_identity(
        description="Scott of Virginia Part B Amendment No. 8",
        congress=119,
    )

    assert identity.chamber == "house"
    assert identity.amendment_number == "8"
    assert identity.label == "Part B Amendment No. 8"
    assert identity.sponsor_text == "Scott of Virginia"
    assert identity.has_direct_identity is True


def test_senate_amendment_identity_preserves_parent_and_amendment_to_amendment() -> None:
    identity = parse_senate_amendment_identity(
        {
            "amendment_number": "S.Amdt. 3947",
            "amendment_type": "S.Amdt.",
            "amendment_to_amendment_number": "S.Amdt. 3946",
            "parent_bill_type": "hr",
            "parent_bill_number": 1,
        },
        congress=119,
    )

    assert identity.key == ("senate", 119, "S.Amdt.", "S.Amdt. 3947", "hr", 1, "S.Amdt. 3946")


def test_interpretation_package_boundary_keeps_non_counting_rows_null() -> None:
    assert interpretation_package_respects_counting_boundary(
        {
            "interpretation_status": "insufficient_evidence",
            "support_position": None,
            "oppose_position": None,
        }
    )
    assert not interpretation_package_respects_counting_boundary(
        {
            "interpretation_status": "ambiguous",
            "support_position": "yea",
            "oppose_position": None,
        }
    )
    assert interpretation_package_respects_counting_boundary(
        {
            "interpretation_status": "interpreted",
            "support_position": "yea",
            "oppose_position": "nay",
        }
    )


def test_write_precondition_requires_scope_targets_rollback_and_exact_approval() -> None:
    result = validate_write_precondition(
        WritePrecondition(
            scope="",
            approval_phrase="Approve exact package",
            provided_approval_phrase="approve exact package",
            target_row_ids=(10, 10),
            rollback_path=None,
            planned_vote_interpretation_writes=1,
            expected_vote_interpretation_writes=0,
        )
    )

    assert result["valid"] is False
    assert "Production write scope is required." in result["errors"]
    assert "Approval phrase does not exactly match." in result["errors"]
    assert "Exact target row ids must not contain duplicates." in result["errors"]
    assert "Rollback artifact path is required before writing." in result["errors"]
    assert "Planned vote_interpretation writes do not match the approved write class." in result["errors"]


def test_write_precondition_passes_with_exact_scope_and_rows() -> None:
    result = require_write_precondition(
        WritePrecondition(
            scope="118th House amendment preview",
            approval_phrase="Approve exact package",
            provided_approval_phrase="Approve exact package",
            target_row_ids=(101, 102),
            rollback_path=Path("docs/review_packets/rollback.sql"),
            planned_vote_interpretation_writes=0,
            expected_vote_interpretation_writes=0,
        )
    )

    assert result["valid"] is True
    assert result["target_row_ids"] == [101, 102]


def test_write_precondition_raises_before_database_write() -> None:
    with pytest.raises(ValueError, match="Production write precondition failed"):
        require_write_precondition(
            WritePrecondition(
                scope="missing rows",
                approval_phrase="Approve",
                provided_approval_phrase="Approve",
                target_row_ids=(),
                rollback_path=Path("rollback.sql"),
            )
        )
