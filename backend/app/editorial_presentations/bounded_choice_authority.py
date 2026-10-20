"""Governed owner evidence, separate from the self-sealed candidate/receipt.

The registry is empty until a separately authorized owner-decision recording.
It is trusted repository data, not a request-supplied trust store. Registering
evidence is outside the four-artifact publication writer's authority.
"""

import hashlib
import json

from .compiler import canonical_digest

DIRECTORY = "docs/editorial/review_packages/health_bounded_choice_v1/"
DECISION_FIELDS = (
    "member_id",
    "issue_id",
    "review_scope",
    "semantic_subject_sha256",
    "presentation_subject_sha256",
    "rendering_subject_sha256",
    "decision",
    "reviewer",
    "reviewer_authority",
    "decided_at_utc",
)
TEST_EVIDENCE = {"kind": "synthetic_test", "fixture_id": "health-choice-contract-v1"}


def require_trusted_decision(receipt: dict) -> None:
    from .bounded_choice_review import ROOT, require

    ref = receipt.get("authority_evidence")
    require(
        isinstance(ref, dict)
        and set(ref) == {"kind", "decision_id", "decision_sha256"}
        and ref["kind"] == "owner_decision",
        "trusted owner decision evidence is required",
    )
    registry = json.loads(
        (ROOT / DIRECTORY / "owner_decision_registry.json").read_text(encoding="utf-8")
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
    path = (ROOT / entry["path"]).resolve()
    require(
        path.is_relative_to((ROOT / DIRECTORY / "owner_decisions").resolve()),
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
