from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.editorial_presentations.compiler import (
    REQUIRED_DETACHED_DECISIONS,
    accepted_substantive_action_ids_for_artifact,
    approval_subject_for_artifact,
    artifact_digest,
    canonical_digest,
    publication_gates_pass,
    semantic_review_exception_resolution_matches,
    semantic_review_exception_subject_for_artifact,
    semantic_tier_for_artifact,
)
from app.editorial_presentations.selector import select_public_presentations


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = (
    ROOT
    / "docs/editorial/full_record_reviews/public_interface_candidates"
    / "f000477_justice_public_safety_119_v1/public_presentation_candidate.json"
)
PREPARATION = (
    ROOT
    / "docs/editorial/full_record_reviews/publication_preparations"
    / "f000477_justice_public_safety_119_v1"
)

APPROVAL_ROLES = (
    "semantic_ir_acceptance",
    "semantic_validation",
    "user_ratification",
    "risk_treatments",
    "full_record_synthesis_approval",
    "production_eligibility",
    "semantic_routing_correction_authorization",
)


def _artifact() -> dict:
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


def _resolution(artifact: dict) -> dict:
    return {
        "schema_version": "semantic_review_exception_resolution_v1",
        "receipt_id": ("semantic-review-exception-resolution:synthetic:justice:119:v1"),
        "status": "approved",
        "binding": semantic_review_exception_subject_for_artifact(artifact),
        "routing_trigger_ledger_sha256": canonical_digest({"triggers": []}),
        "approval_bindings": [
            {
                "role": role,
                "artifact_id": f"test:{role}",
                "content_subject_sha256": canonical_digest({"role": role}),
                "final_file_sha256": canonical_digest({"file": role}),
                "decision": "approved",
            }
            for role in APPROVAL_ROLES
        ],
        "resolution": {
            "all_triggers_accounted": True,
            "accepted_substantive_blocker_count": 0,
            "compiled_ir_unchanged": True,
            "wording_and_mappings_unchanged": True,
            "resulting_semantic_tier": "reviewed_conclusion",
        },
        "reviewer": {
            "reviewer_id": "reviewer:semantic-routing-authority",
            "authority": "delegated_product_methodology_editorial_authority_v1",
        },
        "decision_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _tier(artifact: dict, resolution: dict | None = None) -> str:
    return semantic_tier_for_artifact(
        artifact,
        semantic_review_exception_resolution=resolution,
    )


def _publication_receipt(artifact: dict) -> dict:
    subject = approval_subject_for_artifact(artifact)
    limitations = [
        {**item, "acknowledged": True}
        for item in artifact["provenance"]["review_limitations"]
    ]
    return {
        "schema_version": "editorial_public_issue_approval_receipt_v1",
        "receipt_id": "approval-receipt:synthetic-full-record-routing",
        "status": "approved",
        "binding": subject,
        "approved_statement_ids": subject["statement_ids"],
        "approved_mapping_ids": subject["mapping_ids"],
        "reviewer": {
            "reviewer_id": "reviewer:dhart54",
            "authority": "editorial_publication_review_authority_v1",
        },
        "decision_timestamp": datetime.now(timezone.utc).isoformat(),
        "limitations_sha256": subject["limitations_sha256"],
        "limitations_acknowledged": limitations,
        "decisions": REQUIRED_DETACHED_DECISIONS,
        "publication_activation": {
            "active": False,
            "decision_scope": "out_of_scope",
        },
    }


def test_complete_human_exception_resolution_allows_reviewed_conclusion() -> None:
    artifact = _artifact()
    assert artifact["compiled_semantic_meaning"]["review_route"] == (
        "human_exception_required"
    )
    assert _tier(artifact) == "reviewed_conclusion"
    assert _tier(artifact, _resolution(artifact)) == "reviewed_conclusion"


def test_noncounting_constraint_scope_is_compiler_owned() -> None:
    artifact = _artifact()
    accepted = accepted_substantive_action_ids_for_artifact(artifact)
    assert len(accepted) == 35
    assert "house:119:2:155" not in accepted
    assert "house:119:2:278" not in accepted
    assert "house:119:1:128" in accepted
    assert _tier(artifact, _resolution(artifact)) == "reviewed_conclusion"


def test_human_exception_without_resolution_remains_nonpublishable() -> None:
    artifact = _artifact()
    controls = copy.deepcopy(artifact["controls"])
    controls["semantic"] = {
        "status": "accepted_semantic_reference",
        "validation_status": "passed",
    }
    controls["editorial"]["human_approval_status"] = "human_approved"
    controls["benchmark"]["status"] = "gold_benchmark"
    controls["production"]["eligible"] = True
    controls["publication"]["active"] = True
    subject = approval_subject_for_artifact(artifact)
    approval = _publication_receipt(artifact)
    assert not publication_gates_pass(
        controls,
        expected_subject=subject,
        detached_receipt=approval,
        review_route="human_exception_required",
        semantic_review_exception_resolution_required=True,
    )
    assert publication_gates_pass(
        controls,
        expected_subject=subject,
        detached_receipt=approval,
        review_route="human_exception_required",
        semantic_review_exception_resolution_required=True,
        semantic_review_exception_resolution_valid=True,
    )


def test_accepted_substantive_block_cannot_be_approved_away() -> None:
    artifact = _artifact()
    artifact["compiled_semantic_meaning"]["source_render_constraints"][1][
        "action_ids"
    ] = ["house:119:1:128"]
    assert _tier(artifact, _resolution(artifact)) == "receipts_only"


def test_blocked_route_cannot_be_approved_away() -> None:
    artifact = _artifact()
    artifact["compiled_semantic_meaning"]["review_route"] = "blocked"
    assert _tier(artifact, _resolution(artifact)) == "receipts_only"


@pytest.mark.parametrize(
    "field",
    ["missing_evidence_actions", "unresolved_service_actions", "partial_episodes"],
)
def test_coverage_blockers_cannot_be_approved_away(field: str) -> None:
    artifact = _artifact()
    artifact["evidence_metadata"]["coverage"][field] = 1
    assert _tier(artifact, _resolution(artifact)) == "receipts_only"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda receipt: receipt["approval_bindings"].pop(),
        lambda receipt: receipt["approval_bindings"][0].__setitem__(
            "final_file_sha256", "not-a-digest"
        ),
        lambda receipt: receipt["resolution"].__setitem__(
            "accepted_substantive_blocker_count", 1
        ),
        lambda receipt: receipt["binding"].__setitem__("compiled_ir_sha256", "0" * 64),
    ],
)
def test_partial_or_forged_resolution_fails_closed(mutate) -> None:
    artifact = _artifact()
    receipt = _resolution(artifact)
    mutate(receipt)
    assert not semantic_review_exception_resolution_matches(
        receipt,
        artifact=artifact,
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda artifact: artifact["compiled_semantic_meaning"]["propositions"][
            0
        ].__setitem__("direction", "support"),
        lambda artifact: artifact["editorial_wording"]["conclusion"][
            "body"
        ].__setitem__(
            "text",
            artifact["editorial_wording"]["conclusion"]["body"]["text"] + " changed",
        ),
        lambda artifact: artifact["editorial_wording"]["conclusion"]["body"]["mapping"][
            "source_refs"
        ].reverse(),
        lambda artifact: artifact["provenance"]["review_limitations"][0].__setitem__(
            "text", "Changed limitation."
        ),
    ],
)
def test_changed_semantics_wording_mapping_or_limitation_invalidates_resolution(
    mutate,
) -> None:
    artifact = _artifact()
    receipt = _resolution(artifact)
    mutate(artifact)
    assert not semantic_review_exception_resolution_matches(
        receipt,
        artifact=artifact,
    )


def test_member_identity_does_not_change_evidence_routing_with_fresh_binding() -> None:
    artifact = _artifact()
    artifact["artifact_identity"]["member_id"] = "X000001"
    assert _tier(artifact, _resolution(artifact)) == "reviewed_conclusion"


def test_mixed_trajectory_and_roll_128_limitation_remain_visible() -> None:
    artifact = _artifact()
    propositions = artifact["compiled_semantic_meaning"]["propositions"]
    assert any(
        item["proposition_type"] == "trajectory"
        and item["direction"] == "mixed"
        and set(item["evidence_action_ids"])
        == {"house:119:1:32", "house:119:1:33", "house:119:1:166"}
        for item in propositions
    )
    constraint = artifact["compiled_semantic_meaning"]["source_render_constraints"][0]
    assert constraint["action_ids"] == ["house:119:1:128"]
    assert constraint["semantic_effect"] == "limits_argument_rendering"


def test_full_record_selector_requires_resolution_and_preserves_scope() -> None:
    artifact = json.loads(
        (PREPARATION / "approved_public_presentation_projection.json").read_text(
            encoding="utf-8"
        )
    )
    approval = json.loads(
        (PREPARATION / "full_record_publication_approval_projection.json").read_text(
            encoding="utf-8"
        )
    )
    resolution = json.loads(
        (PREPARATION / "semantic_review_exception_resolution.json").read_text(
            encoding="utf-8"
        )
    )
    review_state = json.loads(
        (PREPARATION / "public_review_state_projection.json").read_text(
            encoding="utf-8"
        )
    )
    row = {
        "member_bioguide_id": "F000477",
        "issue_id": "JUSTICE_PUBLIC_SAFETY",
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "payload_jsonb": artifact,
        "content_sha256": artifact_digest(artifact),
        "natural_key": artifact["artifact_identity"]["artifact_id"],
        "artifact_version": artifact["artifact_identity"]["artifact_version"],
        "schema_version": artifact["schema_version"],
        "publication_metadata_jsonb": {
            "approval_receipt": approval,
            "semantic_review_exception_resolution": resolution,
        },
    }
    selected = select_public_presentations(
        [row],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
        review_states=[review_state],
    )["presentations"][6]
    assert selected["tier"] == "reviewed_conclusion"
    assert selected["review_state"]["review_scope"] == "full_defined_issue_record"
    assert len(selected["exact_action_receipts"]) == 35
    stale = copy.deepcopy(row)
    stale["publication_metadata_jsonb"].pop("semantic_review_exception_resolution")
    assert (
        select_public_presentations(
            [stale],
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id="F000477",
            scope="119",
            review_states=[review_state],
        )["presentations"][6]["tier"]
        == "receipts_only"
    )
    assert (
        select_public_presentations(
            [row],
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id="F000477",
            scope="118",
            review_states=[review_state],
        )["presentations"][6]["tier"]
        == "receipts_only"
    )
