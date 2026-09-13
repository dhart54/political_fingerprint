"""One persisted-artifact V2R registry replacement; no artifact/data writes.

The caller owns the transaction. Row locks plus a complete compare-and-swap keep
the preflight advisory: every governed identity is checked again before mutation.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

from .compiler import canonical_digest
from .publication_replacement_governance_v2 import (
    PERSISTED_CAPS, REPLACEMENT_PREFLIGHT_SCHEMA_V2, artifact_identity,
    validate_positive_authority, validate_execution, validate_projection, _fail,
    REPLACEMENT_WRITE_SET_SCHEMA_V2, replacement_write_set_subject_sha256, validate_write_set,
)


def prepare_write_set(*, registry_key, prior_row, expected_old, proposed_new,
                      semantic_authority_binding, publication_metadata,
                      production_target_identity_sha256, public_runtime_manifest_binding):
    """Pure preparation from explicitly supplied identities; never discover a target."""
    baseline = {"prior_registry_row": copy.deepcopy(prior_row), "expected_old": expected_old,
                "proposed_new": proposed_new, "production_target_identity_sha256": production_target_identity_sha256}
    result = {"schema_version": REPLACEMENT_WRITE_SET_SCHEMA_V2,
              "artifact_id": f"replacement:{registry_key['member_bioguide_id']}:{registry_key['issue_id']}:{proposed_new['content_sha256']}",
              "immutable": True, "subject": {
                  "replacement_mode": "persisted_artifact", "registry_key": registry_key,
                  "expected_old": expected_old, "proposed_new": proposed_new,
                  "replacement_authority_binding": semantic_authority_binding,
                  "production_target_identity_sha256": production_target_identity_sha256,
                  "stable_production_baseline": baseline, "rollback_target": expected_old,
                  "public_runtime_manifest_binding": public_runtime_manifest_binding,
                  "mutation_caps": dict(PERSISTED_CAPS), "publication_registry_update": {
                      "primary_key": registry_key, "prior_row": copy.deepcopy(prior_row), "require_rowcount": 1,
                      "insert_allowed": False, "delete_allowed": False,
                      "publication_metadata_jsonb": copy.deepcopy(publication_metadata),
                  },
              }}
    result["write_set_subject_sha256"] = replacement_write_set_subject_sha256(result)
    result["subject"]["publication_registry_update"]["publication_metadata_jsonb"]["v2r_write_set_subject_sha256"] = result["write_set_subject_sha256"]
    validate_write_set(result)
    return result


def registry_row(conn, key, *, lock=False):
    row = conn.execute(
        "SELECT * FROM editorial_publication_registry WHERE member_bioguide_id=%s AND issue_id=%s"
        + (" FOR UPDATE" if lock else ""), (key["member_bioguide_id"], key["issue_id"]),
    ).fetchone()
    if row is None:
        _fail("expected active registry row is absent")
    return json.loads(json.dumps(dict(row), default=str))


def bound_artifact(conn, identity, key, *, lock=False):
    row = conn.execute("SELECT * FROM editorial_artifact_versions WHERE artifact_id=%s" + (" FOR SHARE" if lock else ""),
                       (identity["artifact_id"],)).fetchone()
    if (row is None or artifact_identity(row) != identity
            or canonical_digest(row["payload_jsonb"]) != identity["content_sha256"]
            or any(row[k] != v for k, v in key.items())):
        _fail("exact bound artifact is absent or drifted")
    return row


def validate_eligible_graph(conn, artifact, metadata, *, lock=False):
    validate_projection(artifact["payload_jsonb"])
    if (artifact["artifact_type"] != "issue_public_presentation" or artifact["editorial_status"] != "human_approved"
            or artifact["benchmark_status"] != "gold_benchmark" or artifact["production_eligible"] is not True
            or artifact["schema_version"] != artifact["payload_jsonb"]["schema_version"]
            or artifact["congress"] != artifact["payload_jsonb"]["subject"]["congress"]):
        _fail("replacement artifact is not publication eligible")
    for role, kind, prefix in (("has_validation", "standardization_validation_result", "validation"),
                               ("uses_source_manifest", "source_manifest", "source_manifest")):
        rows = conn.execute(
            """SELECT a.*,r.ordinal,r.metadata_jsonb FROM editorial_artifact_relationships r
               JOIN editorial_artifact_versions a ON a.artifact_id=r.child_artifact_id
               WHERE r.parent_artifact_id=%s AND r.relationship_type=%s""" + (" FOR SHARE OF a,r" if lock else ""),
            (artifact["artifact_id"], role),
        ).fetchall()
        if len(rows) != 1:
            _fail("replacement provenance graph incomplete or conflicting")
        child = rows[0]
        if (child["artifact_type"] != kind or child["ordinal"] != 0
                or any(child[k] != artifact[k] for k in ("member_bioguide_id", "issue_id"))
                or child["metadata_jsonb"] != metadata["relationship_metadata"]
                or child["natural_key"] != metadata[f"{prefix}_natural_key"]
                or child["artifact_version"] != metadata[f"{prefix}_artifact_version"]
                or child["content_sha256"] != metadata[f"{prefix}_content_sha256"]
                or child["content_sha256"] != canonical_digest(child["payload_jsonb"])):
            _fail("replacement provenance identity differs")
        payload = child["payload_jsonb"]
        if prefix == "validation" and (payload.get("successful") is not True or payload.get("current") is not True
                or payload.get("blocking_findings") != 0
                or payload.get("presentation_content_sha256") != artifact["content_sha256"]):
            _fail("replacement validation failed or blocks publication")
        if prefix == "source_manifest" and (not payload.get("source_artifacts") or payload.get("complete_required_sources") is not True
                or payload.get("presentation_content_sha256") != artifact["content_sha256"]
                or artifact["source_manifest_sha256"] != child["content_sha256"]):
            _fail("replacement source manifest differs")
        if prefix == "source_manifest":
            if not isinstance(payload["source_artifacts"], list):
                _fail("replacement source identities are missing")
            for identity in payload["source_artifacts"]:
                bound_artifact(conn, identity, {k: artifact[k] for k in ("member_bioguide_id", "issue_id")}, lock=lock)


def publication_metadata(write_set, authority):
    result = copy.deepcopy(write_set["subject"]["publication_registry_update"]["publication_metadata_jsonb"])
    result["publication_replacement_activation_authority"] = copy.deepcopy(authority)
    result["publication_replacement_write_set"] = copy.deepcopy(write_set)
    return result


def capture_preflight(conn, write_set, *, production_target_identity_sha256, require_read_only=True):
    validate_write_set(write_set)
    if production_target_identity_sha256 != write_set["subject"]["production_target_identity_sha256"]:
        _fail("production target differs")
    read_only = conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
    if require_read_only and not read_only:
        _fail("preflight must run in a read-only transaction")
    s = write_set["subject"]
    old = bound_artifact(conn, s["expected_old"], s["registry_key"])
    new = bound_artifact(conn, s["proposed_new"], s["registry_key"])
    validate_eligible_graph(conn, new, s["publication_registry_update"]["publication_metadata_jsonb"])
    if new["supersedes_artifact_id"] != old["artifact_id"]:
        _fail("replacement does not supersede the bound prior artifact")
    other = conn.execute("SELECT member_bioguide_id,issue_id FROM editorial_publication_registry WHERE artifact_id=%s AND publicly_active=TRUE",
                         (new["artifact_id"],)).fetchall()
    if any(dict(r) != s["registry_key"] for r in other):
        _fail("replacement is active at an unrelated registry key")
    baseline = {
        "prior_registry_row": registry_row(conn, s["registry_key"]),
        "expected_old": artifact_identity(old), "proposed_new": artifact_identity(new),
        "production_target_identity_sha256": production_target_identity_sha256,
    }
    if baseline != s["stable_production_baseline"]:
        _fail("prior registry or persisted graph drifted")
    evidence = {**baseline, "schema_version": REPLACEMENT_PREFLIGHT_SCHEMA_V2,
                "captured_at_utc": datetime.now(timezone.utc).isoformat(), "transaction_read_only": read_only}
    evidence["preflight_subject_sha256"] = canonical_digest(evidence)
    return evidence


def _owned(row, write_set, authority):
    s = write_set["subject"]
    prior = s["stable_production_baseline"]["prior_registry_row"]
    # Preserve activated_at: operation ownership is the exact authority/write-set,
    # and rollback restores the complete original row without guessed timestamps.
    return row == {**prior, "artifact_id": s["proposed_new"]["artifact_id"],
                   "publication_metadata_jsonb": publication_metadata(write_set, authority)}


def replace_publication(conn, write_set, authority, *, runtime_evidence,
                        production_preflight, production_target_identity_sha256,
                        allow_test_authority=False, rollback=False, fault_after_update=False):
    from psycopg.types.json import Jsonb
    if conn.autocommit:
        _fail("V2R replacement requires an owned transaction")
    if authority.get("test_only_synthetic") and not allow_test_authority:
        _fail("synthetic authority cannot execute in production")
    s = write_set["subject"]
    if production_target_identity_sha256 != s["production_target_identity_sha256"]:
        _fail("production target differs")
    current = registry_row(conn, s["registry_key"], lock=True)
    old = bound_artifact(conn, s["expected_old"], s["registry_key"], lock=True)
    new = bound_artifact(conn, s["proposed_new"], s["registry_key"], lock=True)
    validate_positive_authority(authority, write_set=write_set, candidate=new["payload_jsonb"])
    validate_eligible_graph(conn, new, s["publication_registry_update"]["publication_metadata_jsonb"], lock=True)
    if new["supersedes_artifact_id"] != old["artifact_id"]:
        _fail("replacement supersedes identity differs")
    if not rollback and _owned(current, write_set, authority):
        return {"status": "ALREADY_APPLIED", "mutation_counts": {k: 0 for k in PERSISTED_CAPS}}
    prior = s["stable_production_baseline"]["prior_registry_row"]
    if rollback:
        if not _owned(current, write_set, authority):
            _fail("rollback requires the exact owned post-replacement state")
        destination = prior
    else:
        validate_execution(authority=authority, write_set=write_set, candidate=new["payload_jsonb"],
                           runtime_evidence=runtime_evidence, production_preflight=production_preflight)
        fresh = capture_preflight(conn, write_set, production_target_identity_sha256=production_target_identity_sha256, require_read_only=False)
        if current != prior or any(fresh.get(k) != v for k, v in s["stable_production_baseline"].items()):
            _fail("prior registry or persisted graph drifted")
        destination = {**prior, "artifact_id": new["artifact_id"],
                       "publication_metadata_jsonb": publication_metadata(write_set, authority)}
    updated = conn.execute(
        """UPDATE editorial_publication_registry SET artifact_id=%s,publication_metadata_jsonb=%s
           WHERE member_bioguide_id=%s AND issue_id=%s AND artifact_id=%s
             AND publicly_active=TRUE AND deactivated_at IS NULL AND publication_metadata_jsonb=%s""",
        (destination["artifact_id"], Jsonb(destination["publication_metadata_jsonb"]),
         s["registry_key"]["member_bioguide_id"], s["registry_key"]["issue_id"], current["artifact_id"], Jsonb(current["publication_metadata_jsonb"])),
    )
    if updated.rowcount != 1 or registry_row(conn, s["registry_key"]) != destination:
        _fail("exact one-row replacement postcondition differs")
    if fault_after_update:
        raise RuntimeError("injected replacement failure")
    return {"status": "ROLLED_BACK" if rollback else "APPLIED", "mutation_counts": dict(PERSISTED_CAPS)}
