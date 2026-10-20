"""Shared two-member decision closure; no authority or database mutations."""

import json
from . import bounded_choice_review as review
from .compiler import canonical_digest

PAIR_ROOT = review.ROOT
DIRECTORY = "docs/editorial/review_packages/health_bounded_choice_v1"


def pending_preparation(member, subject, presentation, receipt, pair_sha256):
    result = {
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
        "owner_evidence_registration": {
            "state": "pending_separate_exact_registration_approval",
            "table": "editorial_bounded_choice_owner_decisions",
            "mutation_caps": review.owner_authority.REGISTRATION_CAPS,
            "exact_row": None,
            "exact_row_sha256": None,
            "registration_approval": None,
            "fresh_database_baseline": None,
            "authorizing": False,
            "rollback": "retain_append_only_audit_evidence; remove_serving_access",
        },
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
            "trusted repository evidence registration with exact file and decision hashes",
            "separate positive approval for exactly one owner-evidence database row per member; no other writes",
            "verify registration delta and retained immutable audit state before taking the publication baseline",
            "separate positive V2 initial-publication authority",
            "fresh per-member read-only baseline and runtime identity",
            "validated exact rollback before writing",
        ],
        "authorizing": False,
    }
    result["pair_subject_sha256"] = pair_sha256
    return result


def build_pair_subject(bundles):
    review.require(
        set(bundles) == set(review.MEMBERS), "both bounded members are required"
    )
    members = {}
    for member, b in bundles.items():
        review.validate_semantic_subject(b["semantic"])
        review.validate_presentation(b["presentation"], b["semantic"])
        review.validate_rendering(b["rendering"], b["presentation"], root=PAIR_ROOT)
        review.require(
            canonical_digest(b["accounting"])
            == canonical_digest(b["semantic"]["accounting_review"]),
            "counterpart accounting differs",
        )
        members[member] = {
            "semantic_subject_sha256": b["semantic"]["semantic_subject_sha256"],
            "accounting_sha256": canonical_digest(b["accounting"]),
            "presentation_subject_sha256": b["presentation"][
                "presentation_subject_sha256"
            ],
            "rendering_subject_sha256": b["rendering"]["rendering_subject_sha256"],
        }
    return review.seal(
        {
            "schema_version": "bounded_choice_pair_subject_v1",
            "members": members,
            "authorizing": False,
        },
        "pair_subject_sha256",
    )


def validate_pair_subject():
    directory = PAIR_ROOT / DIRECTORY
    pair = json.loads((directory / "pair-subject.json").read_text(encoding="utf-8"))
    review.check_seal(pair, "pair_subject_sha256")
    bundles = {
        member: {
            suffix: json.loads(
                (directory / f"{member.lower()}-{suffix}.json").read_text(
                    encoding="utf-8"
                )
            )
            for suffix in ["semantic", "accounting", "presentation", "rendering"]
        }
        for member in review.MEMBERS
    }
    review.require(
        canonical_digest(pair) == canonical_digest(build_pair_subject(bundles)),
        "two-member decision subject differs",
    )
    for member, b in bundles.items():
        receipt = review.pending_receipt(
            b["semantic"],
            b["presentation"],
            b["rendering"]["rendering_subject_sha256"],
            pair["pair_subject_sha256"],
        )
        pending = json.loads(
            (directory / f"{member.lower()}-pending-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        preparation = json.loads(
            (
                directory / f"{member.lower()}-initial-publication-preparation.json"
            ).read_text(encoding="utf-8")
        )
        review.require(
            canonical_digest(pending) == canonical_digest(receipt),
            "counterpart pending receipt differs",
        )
        review.require(
            canonical_digest(preparation)
            == canonical_digest(
                pending_preparation(
                    member,
                    b["semantic"],
                    b["presentation"],
                    receipt,
                    pair["pair_subject_sha256"],
                )
            ),
            "counterpart preparation differs",
        )
    return pair
