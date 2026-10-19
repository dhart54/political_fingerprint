"""Build/check detached Health candidates. Never invent an owner decision."""

from __future__ import annotations

import argparse
import json

from backend.app.editorial_presentations import bounded_choice_review as review
from scripts.validate_full_record_issue_interpretation import validate_review

OUTPUT = review.ROOT / "docs/editorial/review_packages/health_bounded_choice_v1"


def products() -> dict[str, dict]:
    foundation = review.load_foundation()
    review.source_evidence()
    result = {}
    for member in review.MEMBERS:
        stem = member.lower()
        subject = review.build_semantic_subject(foundation, member)
        accounting = subject["accounting_review"]
        validate_review(accounting, authority_root=review.ROOT)
        presentation = review.build_presentation(subject, foundation)
        rendering_path = OUTPUT / f"{stem}-rendering.json"
        rendering = (
            json.loads(rendering_path.read_text(encoding="utf-8"))
            if rendering_path.exists()
            else None
        )
        if rendering is not None:
            review.validate_rendering(rendering, presentation)
        receipt = review.pending_receipt(
            subject,
            presentation,
            rendering["rendering_subject_sha256"] if rendering else None,
        )
        result.update(
            {
                f"{stem}-semantic.json": subject,
                f"{stem}-accounting.json": accounting,
                f"{stem}-presentation.json": presentation,
                f"{stem}-pending-receipt.json": receipt,
            }
        )
        result[f"{stem}-initial-publication-preparation.json"] = {
            "schema_version": "bounded_choice_initial_publication_preparation_v1",
            "member_id": member,
            "issue_id": review.ISSUE,
            "congress": 119,
            "state": "pending_content_rendering_and_activation_authority",
            "semantic_subject_sha256": subject["semantic_subject_sha256"],
            "presentation_subject_sha256": presentation["presentation_subject_sha256"],
            "rendering_subject_sha256": receipt["rendering_subject_sha256"],
            "pending_receipt_subject_sha256": receipt["receipt_subject_sha256"],
            "initial_write_invariants": "publication_activation_governance_v2",
            "replacement_path": False,
            "mutation_caps": {
                "insert_batches": 1,
                "insert_artifacts": 4,
                "insert_relationships": 3,
                "insert_registry_rows": 1,
                "updates": 0,
                "deletes": 0,
                "unauthorized_table_writes": 0,
            },
            "accepted_receipt": None,
            "stable_activation_authority": None,
            "exact_write_set": None,
            "fresh_database_baseline": None,
            "fresh_runtime_proof": None,
            "future_requirements": [
                "separate staged-migration authorization",
                "exact content and rendering acceptance",
                "separate positive V2 initial-publication authority",
                "fresh per-member read-only baseline and runtime identity",
                "validated exact rollback before writing",
            ],
            "authorizing": False,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.check:
        for member in review.MEMBERS:
            review.require(
                (OUTPUT / f"{member.lower()}-rendering.json").is_file(),
                "rendered subject is missing",
            )
    for name, value in products().items():
        path = OUTPUT / name
        raw = (
            json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        if args.check:
            review.require(
                path.read_bytes().replace(b"\r\n", b"\n") == raw,
                "generated candidate differs: " + name,
            )
        else:
            path.write_bytes(raw)
    print(
        "bounded Health candidates: valid; owner acceptance pending; no operational authority"
    )


if __name__ == "__main__":
    main()
