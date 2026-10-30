"""Governed owner evidence, separate from the self-sealed candidate/receipt.

The registry is empty until a separately authorized owner-decision recording.
It is trusted repository data, not a request-supplied trust store. Registering
evidence is outside the four-artifact publication writer's authority.
"""

import hashlib
import json
from pathlib import Path

from .compiler import canonical_digest

DIRECTORY = "docs/editorial/review_packages/health_bounded_choice_v1/"
TRUST_ROOT = Path(__file__).resolve().parents[3]
# Registration is separate from the four-artifact publication transaction.
# These caps describe one member's separately approved evidence registration.
REGISTRATION_CAPS = {
    "insert_owner_decision_rows": 1,
    "insert_batches": 0,
    "insert_artifacts": 0,
    "insert_relationships": 0,
    "insert_publication_registry_rows": 0,
    "updates": 0,
    "deletes": 0,
    "unauthorized_table_writes": 0,
}
DECISION_FIELDS = (
    "member_id",
    "issue_id",
    "review_scope",
    "semantic_subject_sha256",
    "presentation_subject_sha256",
    "rendering_subject_sha256",
    "pair_subject_sha256",
    "decision",
    "reviewer",
    "reviewer_authority",
    "decided_at_utc",
)
TEST_EVIDENCE = {"kind": "synthetic_test", "fixture_id": "health-choice-contract-v1"}


def require_trusted_decision(receipt: dict) -> dict:
    from .bounded_choice_review import require

    ref = receipt.get("authority_evidence")
    require(
        isinstance(ref, dict)
        and set(ref) == {"kind", "decision_id", "decision_sha256"}
        and ref["kind"] == "owner_decision",
        "trusted owner decision evidence is required",
    )
    registry = json.loads(
        (TRUST_ROOT / DIRECTORY / "owner_decision_registry.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        set(registry) == {"schema_version", "records"}
        and registry["schema_version"] == "bounded_choice_owner_decision_registry_v1"
        and isinstance(registry["records"], list),
        "owner decision registry differs",
    )
    entries = [
        r for r in registry["records"] if r.get("decision_id") == ref["decision_id"]
    ]
    require(len(entries) == 1, "owner decision is not registered")
    entry = entries[0]
    require(
        set(entry) == {"decision_id", "path", "file_sha256", "decision_sha256"},
        "owner evidence binding differs",
    )
    path = (TRUST_ROOT / entry["path"]).resolve()
    require(
        path.is_relative_to((TRUST_ROOT / DIRECTORY / "owner_decisions").resolve()),
        "owner evidence path differs",
    )
    raw = path.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == entry["file_sha256"],
        "owner evidence bytes differ",
    )
    decision = json.loads(raw)
    require(
        canonical_digest(decision)
        == entry["decision_sha256"]
        == ref["decision_sha256"],
        "owner decision subject differs",
    )
    require(
        set(decision)
        == {"schema_version", "decision_id", "provenance", *DECISION_FIELDS}
        and decision["schema_version"] == "bounded_choice_owner_decision_v1"
        and decision["decision_id"] == ref["decision_id"],
        "owner decision envelope differs",
    )
    provenance = decision["provenance"]
    require(
        isinstance(provenance, dict)
        and set(provenance) == {"kind", "source_ref", "decision_quote"}
        and provenance["kind"] == "direct_owner_decision"
        and all(
            isinstance(provenance[k], str) and provenance[k].strip()
            for k in ["source_ref", "decision_quote"]
        ),
        "direct owner decision provenance is required",
    )
    require(
        canonical_digest({k: decision[k] for k in DECISION_FIELDS})
        == canonical_digest({k: receipt[k] for k in DECISION_FIELDS}),
        "owner decision does not accept this exact subject",
    )
    return {
        "decision_id": entry["decision_id"],
        "decision_sha256": entry["decision_sha256"],
        "file_sha256": entry["file_sha256"],
        "decision_jsonb": decision,
    }


def registration_plan(receipt: dict) -> dict:
    """Prepare one exact row; never register it or authorize a database write."""
    from .bounded_choice_pair import validate_pair_subject
    from .bounded_choice_review import require

    pair = validate_pair_subject()
    require(
        receipt["pair_subject_sha256"] == pair["pair_subject_sha256"],
        "registration pair binding differs",
    )
    row = require_trusted_decision(receipt)
    return {
        "schema_version": "bounded_choice_owner_registration_plan_v1",
        "member_id": receipt["member_id"],
        "table": "editorial_bounded_choice_owner_decisions",
        "exact_row": row,
        "exact_row_sha256": canonical_digest(row),
        "mutation_caps": dict(REGISTRATION_CAPS),
        "required_approval": "separate_positive_exact_owner_evidence_database_registration",
        "preconditions": [
            "fresh_target_database_identity_and_baseline",
            "decision_id_absent",
            "trusted_file_and_full_decision_binding_verified",
        ],
        "postconditions": {
            "owner_decision_rows_delta": 1,
            "all_other_table_rows_unchanged": True,
        },
        "rollback": "retain_immutable_audit_row; revoke_serving_access_on_compatibility_rollback",
        "authorizing": False,
    }
