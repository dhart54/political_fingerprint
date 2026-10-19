"""Exact Health admission and public isolation; no real owner decision."""

from __future__ import annotations

import json

import pytest

from app.editorial_presentations import bounded_choice_review as r
from app.editorial_presentations import bounded_choice_publication as p
from app.editorial_presentations.selector import select_public_presentations
from scripts.validate_full_record_issue_interpretation import validate_review

DIRECTORY = r.ROOT / "docs/editorial/review_packages/health_bounded_choice_v1"


def load(member, suffix):
    return json.loads(
        (DIRECTORY / f"{member.lower()}-{suffix}.json").read_text(encoding="utf-8")
    )


def synthetic_candidate(member="F000477"):
    """In-memory test authority only. Never exported as a review artifact."""
    subject, presentation, rendering, receipt = [
        load(member, name)
        for name in ["semantic", "presentation", "rendering", "pending-receipt"]
    ]
    receipt.update(
        decision="accept_exact_bounded_choice_and_rendering",
        reviewer="SYNTHETIC TEST ONLY",
        reviewer_authority="bounded_choice_review_authority_v1",
        decided_at_utc="2026-10-19T00:00:00Z",
    )
    receipt = r.seal(receipt, "receipt_subject_sha256")
    return p.candidate(subject, presentation, rendering, receipt)


@pytest.mark.parametrize("member", r.MEMBERS)
def test_checked_candidates_reproduce_exact_frozen_inputs_and_bounded_accounting(
    member,
):
    foundation = r.load_foundation()
    semantic = load(member, "semantic")
    r.validate_semantic_subject(semantic, foundation)
    r.validate_presentation(load(member, "presentation"), semantic, foundation)
    accounting = load(member, "accounting")
    assert accounting == semantic["accounting_review"]
    assert validate_review(accounting)["action_count"] == 1
    assert all(v is None for v in accounting["external_authority"].values())
    assert accounting["synthesis"]["full_issue_synthesis_eligible"] is False
    assert len(semantic["member_ir"]["proposition_graph"]["propositions"]) == (
        1 if member == "F000477" else 0
    )
    assert r.source_evidence() == semantic["additional_raw_evidence"]


@pytest.mark.parametrize("member", r.MEMBERS)
def test_pending_receipts_reject_at_every_acceptance_dependent_boundary(member):
    subject, presentation, rendering, receipt = [
        load(member, n)
        for n in ["semantic", "presentation", "rendering", "pending-receipt"]
    ]
    r.validate_receipt(
        receipt,
        subject=subject,
        presentation=presentation,
        rendering=rendering,
        require_accepted=False,
    )
    with pytest.raises(ValueError, match="pending"):
        p.candidate(subject, presentation, rendering, receipt)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x.update(member_id="M001184"),
        lambda x: x.update(issue_id="NATIONAL_SECURITY_FOREIGN"),
        lambda x: x.update(review_scope="full_defined_issue_record"),
        lambda x: x.update(action_ids=["house:119:2:181"]),
        lambda x: x.update(normalized_source_sha256="0" * 64),
        lambda x: x["presentation_inputs"]["records"]["finding"].update(
            text="Broad Health conclusion"
        ),
        lambda x: x["member_ir"]["proposition_graph"]["propositions"][0].update(
            conclusion_relevance="primary"
        ),
        lambda x: x["presentation_inputs"]["boundaries"].clear(),
        lambda x: x["additional_raw_evidence"][0].update(raw_sha256="0" * 64),
    ],
)
def test_resealed_wrong_semantic_subject_cannot_gain_authority(mutation):
    value = load("F000477", "semantic")
    mutation(value)
    with pytest.raises(ValueError):
        r.validate_semantic_subject(r.seal(value, "semantic_subject_sha256"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer_authority", "gold"),
        ("decided_at_utc", "2999-01-01T00:00:00Z"),
        ("reviewer", " "),
        ("decision", "approve_all_health"),
        ("rendering_subject_sha256", "0" * 64),
        ("member_id", "M001184"),
        ("authorizations", {"publication": True}),
    ],
)
def test_resealed_wrong_receipt_rejected(field, value):
    candidate = synthetic_candidate()
    candidate["acceptance"][field] = value
    candidate["acceptance"] = r.seal(candidate["acceptance"], "receipt_subject_sha256")
    with pytest.raises(ValueError):
        p.validate_candidate(candidate)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x["runtime_manifest"].update({"frontend/app/globals.css": "0" * 64}),
        lambda x: x["captures"][0].update(sha256="0" * 64),
        lambda x: x["captures"][0].update(page_errors=["error"]),
        lambda x: x["captures"].pop(),
    ],
)
def test_resealed_stale_render_or_capture_rejected(mutation):
    value = synthetic_candidate()
    mutation(value["rendering"])
    value["rendering"] = r.seal(value["rendering"], "rendering_subject_sha256")
    with pytest.raises(ValueError):
        p.validate_candidate(value)


def public_row(value):
    return {
        "publication_basis": "bounded_choice_review",
        "member_bioguide_id": value["semantic"]["member_id"],
        "issue_id": r.ISSUE,
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "not_promoted",
        "production_eligible": True,
        "payload_jsonb": value,
        "content_sha256": p.canonical_digest(value),
        "schema_version": value["schema_version"],
        "artifact_version": 1,
        "natural_key": value["artifact_id"],
        "publication_metadata_jsonb": {
            "activation_authority_sha256": "0" * 64,
            "publication_basis": "bounded_choice_review",
            "presentation_natural_key": value["artifact_id"],
            "presentation_artifact_version": 1,
            "active_artifact_sha256": p.canonical_digest(value),
        },
    }


@pytest.mark.parametrize("member", r.MEMBERS)
def test_closed_selector_only_exposes_bounded_card_after_exact_acceptance(member):
    value = synthetic_candidate(member)
    row = public_row(value)
    selected = select_public_presentations(
        [row], legislator_id="test", member_bioguide_id=member, scope="119"
    )
    health = next(x for x in selected["presentations"] if x["issue_id"] == r.ISSUE)
    assert health["presentation_branch"] == "bounded_choice_review"
    assert health["conclusion"] is health["teaser"] is None
    assert health["notable_choices"] == []  # no implicit primary/summary projection
    assert p.select_bounded_publication(row, member_id=member, scope="118") is None
    assert p.select_bounded_publication(row, member_id="wrong", scope="119") is None
    row["payload_jsonb"]["acceptance"] = load(member, "pending-receipt")
    row["content_sha256"] = p.canonical_digest(row["payload_jsonb"])
    assert p.select_bounded_publication(row, member_id=member, scope="119") is None


def test_empty_candidate_and_unrelated_gold_rows_preserve_defaults():
    args = dict(
        legislator_id="test",
        member_bioguide_id="F000477",
        scope="all",
        review_states=[],
    )
    expected = select_public_presentations([], **args)
    row = public_row(synthetic_candidate())
    row["benchmark_status"] = "gold_benchmark"
    assert select_public_presentations([row], **args) == expected


def test_auto_deployment_has_no_staged_migration_or_activation_hook():
    # This is an executable interface with no CLI entry point or startup import.
    module = (
        r.ROOT / "backend/app/editorial_presentations/bounded_choice_publication.py"
    ).read_text()
    assert "__main__" not in module
    for directory in [r.ROOT / ".github/workflows", r.ROOT / "frontend"]:
        files = (
            list(directory.glob("*.yml"))
            if directory.name == "workflows"
            else [directory / "package.json"]
        )
        for file in files:
            text = file.read_text()
            assert "db push" not in text and "supabase migration up" not in text
    assert (
        r.ROOT / "backend/migrations/0016_editorial_artifact_persistence.sql"
    ).is_file()


def test_closed_receipt_schema_matches_pending_and_synthetic_positive_subjects():
    from jsonschema import Draft7Validator

    schema = json.loads((DIRECTORY / "acceptance_receipt.schema.json").read_text())
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    for member in r.MEMBERS:
        validator.validate(load(member, "pending-receipt"))
        validator.validate(synthetic_candidate(member)["acceptance"])
