from __future__ import annotations

from typing import Any

from app.analysis.house_comparable_families import ComparableFamilyArtifact
from app.analysis.house_comparable_family_legislator import (
    LegislatorComparableFamilyEvidenceResult,
    get_house_comparable_family_legislator_evidence,
)


PRODUCT_FRAMING = "Record Across Congresses"
RESPONSE_KIND = "internal_house_record_across_congresses_family_evidence"
SUPPORTED_CONGRESSES = (118, 119)
DISALLOWED_RESPONSE_FIELD_TERMS = (
    "changed",
    "change",
    "trend",
    "movement",
    "shift",
    "increased",
    "decreased",
    "more_supportive",
    "less_supportive",
    "consistent",
    "continuity",
    "flip",
    "alignment_change",
)


def build_house_record_across_congresses_response(
    legislator_identifier: str,
    *,
    artifact: ComparableFamilyArtifact | None = None,
    connection: Any | None = None,
) -> dict[str, Any]:
    """Build an internal response contract for House family evidence availability."""

    evidence = get_house_comparable_family_legislator_evidence(
        legislator_identifier,
        artifact=artifact,
        connection=connection,
    )
    response = build_response_from_house_family_evidence(evidence)
    _assert_no_disallowed_response_field_names(response)
    return response


def build_response_from_house_family_evidence(
    evidence: LegislatorComparableFamilyEvidenceResult,
) -> dict[str, Any]:
    """Convert helper evidence into a stable internal API-facing shape."""

    families = [_build_family_row(family) for family in evidence.families]
    display_eligible_families = [
        family
        for family in evidence.families
        if family.record_across_congresses_display_eligible
    ]
    response = {
        "response_kind": RESPONSE_KIND,
        "product_framing": PRODUCT_FRAMING,
        "availability_explanation": (
            "This internal response reports factual family-level evidence "
            "availability and counts only."
        ),
        "legislator_identifier": evidence.legislator.legislator_identifier,
        "requested_legislator_identifier": evidence.legislator_identifier,
        "artifact_version": evidence.artifact_version_used,
        "supported_congresses": list(SUPPORTED_CONGRESSES),
        "legislator": {
            "database_id": evidence.legislator.database_id,
            "legislator_identifier": evidence.legislator.legislator_identifier,
            "bioguide_id": evidence.legislator.bioguide_id,
            "name": evidence.legislator.name,
            "chamber": evidence.legislator.chamber,
            "state": evidence.legislator.state,
            "district": evidence.legislator.district,
            "party": evidence.legislator.party,
        },
        "summary": {
            "eligible_comparable_family_count": evidence.eligible_comparable_families_considered,
            "record_across_congresses_available": bool(display_eligible_families),
            "display_eligible_family_count": len(display_eligible_families),
            "directly_comparable_display_eligible_family_count": sum(
                1
                for family in display_eligible_families
                if family.comparability_status == "directly_comparable"
            ),
            "conditionally_comparable_display_eligible_family_count": sum(
                1
                for family in display_eligible_families
                if family.comparability_status == "conditionally_comparable"
            ),
        },
        "non_authorization_metadata": _build_non_authorization_metadata(),
        "families": families,
    }
    _assert_no_disallowed_response_field_names(response)
    return response


def _build_family_row(family: Any) -> dict[str, Any]:
    evidence_available = family.record_across_congresses_display_eligible
    row = {
        "family_id": family.family_id,
        "family_name": family.family_name,
        "issue_domain": family.issue_domain,
        "comparability_status": family.comparability_status,
        "governing_question": family.governing_question,
        "comparability_caveat": family.caveats_and_limitations,
        "record_across_congresses_available": evidence_available,
        "evidence_available_in_both_congresses": family.has_family_vote_in_both_congresses,
        "unavailable_reason": None if evidence_available else _unavailable_reason(family),
        "roll_call_ids_considered_by_congress": {
            str(congress): list(roll_call_ids)
            for congress, roll_call_ids in sorted(family.roll_call_ids_considered_by_congress.items())
        },
        "family_evidence_counts_by_congress": {
            str(congress): _build_congress_counts(counts)
            for congress, counts in sorted(family.counts_by_congress.items())
        },
    }
    return row


def _build_congress_counts(counts: Any) -> dict[str, Any]:
    return {
        "congress": counts.congress,
        "roll_call_ids_considered": list(counts.roll_call_ids_considered),
        "cast_substantive_yes_count": counts.cast_substantive_yes_count,
        "cast_substantive_no_count": counts.cast_substantive_no_count,
        "not_voting_count": counts.not_voting_count,
        "present_count": counts.present_count,
        "missing_no_record_count": counts.missing_no_record_count,
        "total_artifact_roll_calls": counts.total_artifact_roll_calls,
        "total_cast_substantive_yes_no_rows": counts.total_cast_substantive_yes_no_rows,
    }


def _unavailable_reason(family: Any) -> str:
    if not family.family_eligibility_flag:
        return "family_not_eligible_for_this_internal_response"
    if not family.has_family_vote_in_both_congresses:
        return "substantive_yes_no_evidence_not_available_in_both_congresses"
    return "family_evidence_not_available_for_internal_display"


def _build_non_authorization_metadata() -> dict[str, Any]:
    return {
        "internal_response_only": True,
        "public_route_exposed": False,
        "only_factual_evidence_availability_and_counts": True,
        "unsupported_inferences_are_not_generated": True,
        "frontend_copy_not_authorized": True,
        "voting_recommendation_not_authorized": True,
        "requires_review_before_public_product_use": True,
    }


def _assert_no_disallowed_response_field_names(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            for term in DISALLOWED_RESPONSE_FIELD_TERMS:
                if term in normalized_key:
                    raise ValueError(f"Disallowed response field name: {key}")
            _assert_no_disallowed_response_field_names(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_disallowed_response_field_names(child)
