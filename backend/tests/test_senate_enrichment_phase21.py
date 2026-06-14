from app.etl.senate_enrichment_phase21 import (
    _purpose_is_generic,
    _substantive_source_safe,
    validate_manifest,
)


def test_phase21_defers_generic_amendment_purpose() -> None:
    assert _purpose_is_generic("In the nature of a substitute.") is True
    assert _purpose_is_generic("To improve the bill.") is True
    assert _purpose_is_generic("To reduce prescription drug prices under Medicare.") is False


def test_phase21_rejects_procedural_rule_like_substantive_source() -> None:
    row = {
        "amendment_purpose": (
            "To establish a deficit-neutral reserve fund relating to Congress continuing "
            "its work to rein in the administrative state by supporting legislation that "
            "prevents Federal agencies from finalizing major rules without congressional approval."
        ),
        "question": "On the Amendment",
        "description": "Example Amdt.",
    }

    assert _substantive_source_safe(row) is False


def test_phase21_manifest_validation_requires_amendment_purpose_basis() -> None:
    manifest = {
        "schema_version": "senate_enrichment_phase_21_v1",
        "considered_roll_calls": [
            {
                "roll_call_id": 123,
                "eligible_for_write": True,
                "evidence_type": "senate_amendment_fact",
                "amendment_purpose": "To reduce prescription drug prices under Medicare.",
                "proposed_classification": {
                    "primary_domain": "HEALTH_SOCIAL",
                    "classification_basis": ["Parent bill title only."],
                    "support_oppose_positions_inferred": False,
                },
            }
        ],
    }

    result = validate_manifest(manifest)

    assert result["valid"] is False
    assert "amendment classification must use amendment purpose first" in result["errors"][0]
