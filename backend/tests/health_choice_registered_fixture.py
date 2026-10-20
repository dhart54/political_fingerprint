"""TEST ONLY trust-store simulation. Never export real owner authorization.

Only the fixed trust-store data location is redirected to an owned temporary
directory. The actual verifier, constructors, writer, SQL view and selector all
run with ordinary defaults. No verifier mock or synthetic-mode flag is used.
"""

import json
from pathlib import Path

from app.editorial_presentations import bounded_choice_review as r
from app.editorial_presentations import bounded_choice_publication as p
from test_health_bounded_choice import load


def registered_fixture(tmp_path: Path, monkeypatch):
    authority = r.owner_authority
    monkeypatch.setattr(authority, "TRUST_ROOT", tmp_path)
    entries, inputs = [], {}
    for member in r.MEMBERS:
        subject, presentation, rendering, receipt = [
            load(member, suffix)
            for suffix in ["semantic", "presentation", "rendering", "pending-receipt"]
        ]
        decision_id = "TEST_ONLY_ephemeral_owner_evidence_" + member
        receipt.update(
            decision="accept_exact_bounded_choice_and_rendering",
            reviewer="TEST ONLY ephemeral registered-evidence rehearsal",
            reviewer_authority="bounded_choice_review_authority_v1",
            decided_at_utc="2026-10-19T00:00:00Z",
        )
        decision = {
            "schema_version": "bounded_choice_owner_decision_v1",
            "decision_id": decision_id,
            "provenance": {
                "kind": "direct_owner_decision",
                "source_ref": "TEST ONLY temporary trust-store fixture; no actual owner decision",
                "decision_quote": "TEST ONLY rehearsal accepting the exact two-member closure; no real authorization",
            },
            **{field: receipt[field] for field in authority.DECISION_FIELDS},
        }
        raw = (json.dumps(decision, ensure_ascii=False, sort_keys=True) + "\n").encode()
        path = (
            tmp_path / authority.DIRECTORY / "owner_decisions" / (decision_id + ".json")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        entry = {
            "decision_id": decision_id,
            "path": path.relative_to(tmp_path).as_posix(),
            "file_sha256": r.hashlib.sha256(raw).hexdigest(),
            "decision_sha256": p.canonical_digest(decision),
        }
        entries.append(entry)
        receipt["authority_evidence"] = {
            "kind": "owner_decision",
            "decision_id": decision_id,
            "decision_sha256": entry["decision_sha256"],
        }
        inputs[member] = (
            subject,
            presentation,
            rendering,
            r.seal(receipt, "receipt_subject_sha256"),
        )
    registry = tmp_path / authority.DIRECTORY / "owner_decision_registry.json"
    registry.write_text(
        json.dumps(
            {
                "schema_version": "bounded_choice_owner_decision_registry_v1",
                "records": entries,
            }
        ),
        encoding="utf-8",
    )
    return {member: p.candidate(*values) for member, values in inputs.items()}
