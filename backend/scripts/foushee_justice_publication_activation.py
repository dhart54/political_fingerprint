from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_artifacts.migration import TABLES
from app.editorial_artifacts.publication_activation import (
    ACTIVE_ARTIFACT_SHA256,
    BATCH_KEY,
    BUNDLE_ID,
    BUNDLE_PATH,
    ISSUE_ID,
    MEMBER_ID,
    PRESENTATION_KEY,
    SOURCE_COMMIT,
    load_activation_bundle,
)
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.selector import select_public_presentations
from scripts.editorial_artifact_store import (
    StoreSafetyError,
    _connect,
    export_bundle,
    live_schema_contract,
    target_info,
)


LOCK_KEY = f"political_fingerprint:{BUNDLE_ID}"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_SCHEMAS = {
    name: ROOT / "docs" / f"{name}.schema.json"
    for name in (
        "editorial_publication_preflight_report_v1",
        "editorial_publication_backup_inventory_v1",
        "editorial_publication_restore_receipt_v1",
        "editorial_publication_backup_proof_v1",
    )
}


def _counts(conn: Any) -> dict[str, int]:
    return {
        "batches": int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM editorial_artifact_batches"
            ).fetchone()["n"]
        ),
        "artifacts": int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM editorial_artifact_versions"
            ).fetchone()["n"]
        ),
        "relationships": int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM editorial_artifact_relationships"
            ).fetchone()["n"]
        ),
        "publication_registry": int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM editorial_publication_registry"
            ).fetchone()["n"]
        ),
    }


def _exact_deployed_commit(actual: str) -> dict[str, Any]:
    if not SHA40.fullmatch(actual):
        raise StoreSafetyError("deployed commit must be an exact lowercase 40-character SHA")
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, actual],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise StoreSafetyError(
            "deployed commit is not proven to contain the reviewed activation baseline"
        )
    return {
        "required_ancestor": SOURCE_COMMIT,
        "supplied_identity": actual,
        "compatible": True,
        "verification_method": "git_merge_base_is_ancestor",
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest_body(value: dict[str, Any], digest_key: str) -> str:
    body = {key: item for key, item in value.items() if key != digest_key}
    return semantic_hash(body)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_record(path: Path, *, relative_to: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(relative_to.resolve()).as_posix(),
        "byte_size": path.stat().st_size,
        "sha256": _file_sha256(path),
    }


def _validate_evidence(value: dict[str, Any], schema_name: str) -> None:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource

    schema = json.loads(EVIDENCE_SCHEMAS[schema_name].read_text(encoding="utf-8"))
    registry = Registry()
    for schema_path in EVIDENCE_SCHEMAS.values():
        resource_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        registry = registry.with_resource(
            schema_path.name, Resource.from_contents(resource_schema)
        )
    errors = sorted(
        Draft202012Validator(
            schema, format_checker=FormatChecker(), registry=registry
        ).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise StoreSafetyError(
            f"{schema_name} schema mismatch: {errors[0].message}"
        )


def _load_evidence(path: Path, schema_name: str, digest_key: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoreSafetyError(f"{schema_name} is missing or invalid") from exc
    _validate_evidence(value, schema_name)
    if not hashlib.sha256(
        json.dumps(
            {key: item for key, item in value.items() if key != digest_key},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest() == value[digest_key]:
        raise StoreSafetyError(f"{schema_name} canonical digest mismatch")
    return value


def _database_fingerprint(conn: Any) -> str:
    row = conn.execute(
        """SELECT current_database() AS database,
                  current_setting('server_version_num') AS server_version_num,
                  current_user AS database_user"""
    ).fetchone()
    return semantic_hash(dict(row))


def _schema_semantics(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_columns": schema["exact_columns"],
        "triggers_exact": schema["triggers_exact"],
        "functions_exact": schema["functions_exact"],
        "required_indexes_present": schema["required_indexes_present"],
        "required_constraint_classes_present": schema[
            "required_constraint_classes_present"
        ],
        "columns": schema["columns"],
        "triggers": schema["triggers"],
        "functions": schema["functions"],
        "indexes": schema["indexes"],
        "constraint_classes": sorted(
            {
                (item["table_name"], item["constraint_type"])
                for item in schema["constraints"]
            }
        ),
    }


def _inventory(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    schema = live_schema_contract(conn)
    preflight = _preflight(conn, bundle)
    exported = export_bundle(
        conn,
        __import__(
            "app.editorial_artifacts.bundle",
            fromlist=["build_seed_bundle"],
        ).build_seed_bundle(),
    )
    artifact_keys = [item["natural_key"] for item in bundle["artifacts"]]
    target_queries = {
        "artifact_versions": [
            dict(row)
            for row in conn.execute(
                """SELECT natural_key, artifact_version, content_sha256
                   FROM editorial_artifact_versions
                   WHERE natural_key = ANY(%s)
                   ORDER BY natural_key, artifact_version""",
                (artifact_keys,),
            ).fetchall()
        ],
        "activation_batch": [
            dict(row)
            for row in conn.execute(
                """SELECT deterministic_batch_key, manifest_sha256
                   FROM editorial_artifact_batches
                   WHERE deterministic_batch_key = %s""",
                (BATCH_KEY,),
            ).fetchall()
        ],
        "publication_registry": [
            dict(row)
            for row in conn.execute(
                """SELECT member_bioguide_id, issue_id, artifact_id
                   FROM editorial_publication_registry
                   WHERE member_bioguide_id = %s AND issue_id = %s""",
                (MEMBER_ID, ISSUE_ID),
            ).fetchall()
        ],
        "relationships": [
            dict(row)
            for row in conn.execute(
                """SELECT parent.natural_key AS parent_natural_key,
                          child.natural_key AS child_natural_key,
                          rel.relationship_type
                   FROM editorial_artifact_relationships rel
                   JOIN editorial_artifact_versions parent
                     ON parent.artifact_id = rel.parent_artifact_id
                   JOIN editorial_artifact_versions child
                     ON child.artifact_id = rel.child_artifact_id
                   WHERE parent.natural_key = %s
                   ORDER BY rel.relationship_type, child.natural_key""",
                (PRESENTATION_KEY,),
            ).fetchall()
        ],
    }
    value = {
        "schema_version": "editorial_publication_backup_inventory_v1",
        "captured_at": _utc_now(),
        "bundle_id": BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "preflight_binding": None,
        "database_fingerprint": _database_fingerprint(conn),
        "counts": preflight["counts"],
        "historical_seed": preflight["historical_seed"],
        "schema_contract": schema,
        "security": preflight["security"],
        "target_absent": preflight["target_absent"],
        "target_queries": target_queries,
        "semantic_hashes": {
            "historical_export_sha256": semantic_hash(exported),
            "schema_contract_sha256": semantic_hash(_schema_semantics(schema)),
        },
    }
    value["inventory_sha256"] = _digest_body(value, "inventory_sha256")
    _validate_evidence(value, value["schema_version"])
    return value


def _inventory_semantics(value: dict[str, Any]) -> dict[str, Any]:
    semantics = {
        key: value[key]
        for key in (
            "bundle_id",
            "bundle_sha256",
            "preflight_binding",
            "counts",
            "historical_seed",
            "security",
            "target_absent",
            "target_queries",
            "semantic_hashes",
        )
    }
    semantics["schema_contract"] = _schema_semantics(value["schema_contract"])
    return semantics


def _bind_inventory(
    inventory: dict[str, Any], report: dict[str, Any]
) -> dict[str, Any]:
    bound = json.loads(json.dumps(inventory))
    bound["preflight_binding"] = {
        "report_id": report["report_id"],
        "report_sha256": report["report_sha256"],
    }
    bound["inventory_sha256"] = _digest_body(bound, "inventory_sha256")
    _validate_evidence(bound, bound["schema_version"])
    return bound


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _preflight_report(
    conn: Any,
    bundle: dict[str, Any],
    deployed_commit: str,
) -> dict[str, Any]:
    inventory = _inventory(conn, bundle)
    value = {
        "schema_version": "editorial_publication_preflight_report_v1",
        "report_id": f"{BUNDLE_ID}:{inventory['database_fingerprint']}:{deployed_commit}",
        "created_at": _utc_now(),
        "bundle_id": BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "deployment_compatibility": _exact_deployed_commit(deployed_commit),
        "database_fingerprint": inventory["database_fingerprint"],
        "inventory": inventory,
    }
    value["report_sha256"] = _digest_body(value, "report_sha256")
    _validate_evidence(value, value["schema_version"])
    return value


def _verify_preflight_report(
    path: Path,
    bundle: dict[str, Any],
    deployed_commit: str,
    conn: Any | None = None,
) -> dict[str, Any]:
    report = _load_evidence(
        path, "editorial_publication_preflight_report_v1", "report_sha256"
    )
    _validate_evidence(
        report["inventory"], "editorial_publication_backup_inventory_v1"
    )
    if (
        _digest_body(report["inventory"], "inventory_sha256")
        != report["inventory"]["inventory_sha256"]
    ):
        raise StoreSafetyError("preflight inventory canonical digest mismatch")
    if (
        report["bundle_id"] != BUNDLE_ID
        or report["bundle_sha256"] != bundle["bundle_sha256"]
        or report["deployment_compatibility"]["supplied_identity"]
        != deployed_commit
    ):
        raise StoreSafetyError("preflight report identity mismatch")
    if conn is not None:
        current = _inventory(conn, bundle)
        if (
            report["database_fingerprint"] != current["database_fingerprint"]
            or _inventory_semantics(report["inventory"])
            != _inventory_semantics(current)
        ):
            raise StoreSafetyError("preflight report is stale or targets another database")
    return report


def _verify_backup_proof(
    path: Path,
    bundle: dict[str, Any],
    deployed_commit: str,
    preflight_report_path: Path,
) -> dict[str, Any]:
    proof = _load_evidence(
        path, "editorial_publication_backup_proof_v1", "proof_sha256"
    )
    if (
        proof["bundle_id"] != BUNDLE_ID
        or proof["bundle_sha256"] != bundle["bundle_sha256"]
        or proof["deployed_commit"] != deployed_commit
    ):
        raise StoreSafetyError("backup proof identity mismatch")
    created_at = datetime.fromisoformat(proof["created_at"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age < -300 or age > 14400:
        raise StoreSafetyError("backup proof is stale or has a future timestamp")
    base = path.resolve().parent
    loaded: dict[str, dict[str, Any]] = {}
    for name, schema_name, digest_key in (
        ("preflight_report", "editorial_publication_preflight_report_v1", "report_sha256"),
        ("source_inventory", "editorial_publication_backup_inventory_v1", "inventory_sha256"),
        ("restored_inventory", "editorial_publication_backup_inventory_v1", "inventory_sha256"),
        ("restore_receipt", "editorial_publication_restore_receipt_v1", "receipt_sha256"),
    ):
        record = proof[name]
        evidence_path = (base / record["path"]).resolve()
        if base not in evidence_path.parents:
            raise StoreSafetyError("backup evidence path escapes its evidence directory")
        if (
            not evidence_path.is_file()
            or evidence_path.stat().st_size != record["byte_size"]
            or _file_sha256(evidence_path) != record["sha256"]
        ):
            raise StoreSafetyError(f"backup evidence file mismatch: {name}")
        loaded[name] = _load_evidence(evidence_path, schema_name, digest_key)
    snapshot_path = (base / proof["snapshot"]["path"]).resolve()
    snapshot = proof["snapshot"]
    if (
        base not in snapshot_path.parents
        or not snapshot_path.is_file()
        or snapshot_path.stat().st_size != snapshot["byte_size"]
        or _file_sha256(snapshot_path) != snapshot["sha256"]
    ):
        raise StoreSafetyError("backup snapshot file mismatch")
    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        raise StoreSafetyError("pg_restore is required to verify the snapshot archive")
    archive = subprocess.run(
        [pg_restore, "--list", str(snapshot_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if archive.returncode != 0 or "editorial_artifact_batches" not in archive.stdout:
        raise StoreSafetyError("snapshot is not a valid required PostgreSQL archive")
    report = loaded["preflight_report"]
    source = loaded["source_inventory"]
    restored = loaded["restored_inventory"]
    restore = loaded["restore_receipt"]
    expected_report = preflight_report_path.resolve()
    actual_report = (base / proof["preflight_report"]["path"]).resolve()
    if actual_report != expected_report:
        raise StoreSafetyError("backup proof does not bind the supplied preflight report")
    if (
        proof["preflight_report_id"] != report["report_id"]
        or proof["preflight_report_digest"] != report["report_sha256"]
        or proof["verification"]["source_commit"] != SOURCE_COMMIT
        or report["database_fingerprint"] != proof["database_fingerprint"]
        or source["database_fingerprint"] != proof["database_fingerprint"]
        or source["preflight_binding"]
        != {
            "report_id": report["report_id"],
            "report_sha256": report["report_sha256"],
        }
        or restored["preflight_binding"] != source["preflight_binding"]
        or restore["snapshot_sha256"] != snapshot["sha256"]
        or restore["source_inventory_sha256"] != source["inventory_sha256"]
        or restore["restored_inventory_sha256"] != restored["inventory_sha256"]
        or restore["source_counts"] != source["counts"]
        or restore["restored_counts"] != restored["counts"]
        or restore["source_semantic_hashes"] != source["semantic_hashes"]
        or restore["restored_semantic_hashes"] != restored["semantic_hashes"]
        or restore["source_schema_object_digest"]
        != source["semantic_hashes"]["schema_contract_sha256"]
        or restore["restored_schema_object_digest"]
        != restored["semantic_hashes"]["schema_contract_sha256"]
        or _inventory_semantics(source) != _inventory_semantics(restored)
        or restore["semantic_equality"] is not True
        or restore["selector_state"] != "receipts_only"
    ):
        raise StoreSafetyError("backup evidence chain mismatch")
    return {
        "proof_sha256": proof["proof_sha256"],
        "snapshot_sha256": snapshot["sha256"],
        "preflight_report_sha256": report["report_sha256"],
        "restore_receipt_sha256": restore["receipt_sha256"],
        "verified": True,
    }


def _prepare_backup(
    source_database_url: str,
    restore_database_url: str,
    evidence_dir: Path,
    bundle: dict[str, Any],
    deployed_commit: str,
    preflight_report_path: Path,
) -> Path:
    pg_dump = shutil.which("pg_dump")
    pg_restore = shutil.which("pg_restore")
    if not pg_dump or not pg_restore:
        raise StoreSafetyError("pg_dump and pg_restore are required")
    evidence_dir = evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report = _verify_preflight_report(
        preflight_report_path, bundle, deployed_commit
    )
    with _connect(source_database_url, autocommit=True) as source_conn:
        source_conn.execute("SET default_transaction_read_only = on")
        with source_conn.transaction():
            source_conn.execute("SET TRANSACTION READ ONLY")
            source_inventory = _inventory(source_conn, bundle)
    if (
        source_inventory["database_fingerprint"] != report["database_fingerprint"]
        or _inventory_semantics(source_inventory)
        != _inventory_semantics(report["inventory"])
    ):
        raise StoreSafetyError("backup source differs from the successful preflight")
    source_inventory = _bind_inventory(source_inventory, report)
    source_path = evidence_dir / "source-inventory.json"
    report_path = evidence_dir / "preflight-report.json"
    restored_path = evidence_dir / "restored-inventory.json"
    receipt_path = evidence_dir / "restore-receipt.json"
    snapshot_path = evidence_dir / "pre-activation.dump"
    proof_path = evidence_dir / "backup-proof.json"
    _write_json(report_path, report)
    _write_json(source_path, source_inventory)
    dump = subprocess.run(
        [
            pg_dump,
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--file",
            str(snapshot_path),
            source_database_url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if dump.returncode != 0:
        raise StoreSafetyError(f"pg_dump failed: {dump.stderr.strip()}")
    restore = subprocess.run(
        [
            pg_restore,
            "--exit-on-error",
            "--no-owner",
            "--no-privileges",
            "--dbname",
            restore_database_url,
            str(snapshot_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if restore.returncode != 0:
        raise StoreSafetyError(f"pg_restore failed: {restore.stderr.strip()}")
    with _connect(restore_database_url, autocommit=True) as restored_conn:
        restored_conn.execute("SET default_transaction_read_only = on")
        with restored_conn.transaction():
            restored_conn.execute("SET TRANSACTION READ ONLY")
            restored_inventory = _inventory(restored_conn, bundle)
            restored_rows = EditorialArtifactRepository(
                restored_conn
            ).publication_selector()
            if restored_rows:
                raise StoreSafetyError(
                    "restored pre-activation selector is not receipts-only"
                )
            for scope in ("119", "all", "118"):
                response = select_public_presentations(
                    restored_rows,
                    legislator_id="leg_valerie_p_foushee",
                    member_bioguide_id=MEMBER_ID,
                    scope=scope,
                )
                if any(
                    item["tier"] != "receipts_only"
                    for item in response["presentations"]
                ):
                    raise StoreSafetyError(
                        "restored pre-activation API contract is not receipts-only"
                    )
    restored_inventory = _bind_inventory(restored_inventory, report)
    if _inventory_semantics(source_inventory) != _inventory_semantics(
        restored_inventory
    ):
        raise StoreSafetyError("restored database differs from the source inventory")
    _write_json(restored_path, restored_inventory)
    snapshot_sha256 = _file_sha256(snapshot_path)
    pg_dump_version = subprocess.run(
        [pg_dump, "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    pg_restore_version = subprocess.run(
        [pg_restore, "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    receipt = {
        "schema_version": "editorial_publication_restore_receipt_v1",
        "restored_at": _utc_now(),
        "bundle_id": BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "snapshot_sha256": snapshot_sha256,
        "source_inventory_sha256": source_inventory["inventory_sha256"],
        "restored_inventory_sha256": restored_inventory["inventory_sha256"],
        "source_counts": source_inventory["counts"],
        "restored_counts": restored_inventory["counts"],
        "source_semantic_hashes": source_inventory["semantic_hashes"],
        "restored_semantic_hashes": restored_inventory["semantic_hashes"],
        "source_schema_object_digest": source_inventory["semantic_hashes"][
            "schema_contract_sha256"
        ],
        "restored_schema_object_digest": restored_inventory["semantic_hashes"][
            "schema_contract_sha256"
        ],
        "semantic_equality": True,
        "selector_state": "receipts_only",
    }
    receipt["receipt_sha256"] = _digest_body(receipt, "receipt_sha256")
    _validate_evidence(receipt, receipt["schema_version"])
    _write_json(receipt_path, receipt)
    proof = {
        "schema_version": "editorial_publication_backup_proof_v1",
        "proof_id": (
            f"{BUNDLE_ID}:{report['report_sha256']}:{snapshot_sha256}"
        ),
        "created_at": _utc_now(),
        "bundle_id": BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "deployed_commit": deployed_commit,
        "database_fingerprint": source_inventory["database_fingerprint"],
        "preflight_report_id": report["report_id"],
        "preflight_report_digest": report["report_sha256"],
        "preflight_report": _file_record(
            report_path, relative_to=evidence_dir
        ),
        "snapshot": {
            **_file_record(snapshot_path, relative_to=evidence_dir),
            "format": "postgresql_custom_archive",
            "created_at": _utc_now(),
            "tool": "pg_dump",
            "tool_version": pg_dump_version,
        },
        "source_inventory": _file_record(source_path, relative_to=evidence_dir),
        "restored_inventory": _file_record(restored_path, relative_to=evidence_dir),
        "restore_receipt": _file_record(receipt_path, relative_to=evidence_dir),
        "verification": {
            "tool": "foushee_justice_publication_activation.py",
            "tool_version": "editorial_publication_activation_operator_v1",
            "source_commit": SOURCE_COMMIT,
            "pg_restore_version": pg_restore_version,
        },
    }
    proof["proof_sha256"] = _digest_body(proof, "proof_sha256")
    _validate_evidence(proof, proof["schema_version"])
    _write_json(proof_path, proof)
    _verify_backup_proof(
        proof_path, bundle, deployed_commit, report_path
    )
    return proof_path


def _historical_seed_exact(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    batch = conn.execute(
        """SELECT source_commit_sha, manifest_sha256, artifact_count,
                  relationship_count, status
           FROM editorial_artifact_batches
           WHERE deterministic_batch_key = %s""",
        (bundle["historical_seed"]["deterministic_batch_key"],),
    ).fetchone()
    if not batch:
        raise StoreSafetyError("historical 71-artifact seed batch is absent")
    expected = bundle["historical_seed"]
    if (
        batch["manifest_sha256"] != expected["manifest_sha256"]
        or batch["artifact_count"] != 71
        or batch["relationship_count"] != 95
        or batch["status"] != "applied"
    ):
        raise StoreSafetyError("historical seed batch is not the pinned 71/95 state")
    exported = export_bundle(conn, __import__(
        "app.editorial_artifacts.bundle",
        fromlist=["build_seed_bundle"],
    ).build_seed_bundle())
    if not exported["semantic_match"]:
        raise StoreSafetyError("historical seed database export differs from frozen input")
    return {
        "manifest_sha256": batch["manifest_sha256"],
        "artifact_count": batch["artifact_count"],
        "relationship_count": batch["relationship_count"],
        "semantic_match": True,
    }


def _security_state(conn: Any) -> dict[str, Any]:
    privileges = {
        role: {
            table: bool(
                conn.execute(
                    "SELECT has_table_privilege(%s, %s, 'SELECT') AS allowed",
                    (role, f"public.{table}"),
                ).fetchone()["allowed"]
            )
            for table in sorted(TABLES)
        }
        for role in ("anon", "authenticated")
    }
    if any(any(tables.values()) for tables in privileges.values()):
        raise StoreSafetyError(
            "anon or authenticated has direct editorial artifact access"
        )
    rls = {
        row["relname"]: bool(row["relrowsecurity"])
        for row in conn.execute(
            """SELECT relname, relrowsecurity
               FROM pg_class
               JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
               WHERE pg_namespace.nspname = 'public'
                 AND relname = ANY(%s)""",
            (list(TABLES),),
        ).fetchall()
    }
    if set(rls) != TABLES or not all(rls.values()):
        raise StoreSafetyError("RLS is not enabled on every editorial table")
    return {"direct_select_privileges": privileges, "rls_enabled": rls}


def _preflight(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    live_schema_contract(conn)
    security = _security_state(conn)
    counts = _counts(conn)
    if counts != bundle["expected_counts"]["before"]:
        raise StoreSafetyError(f"pre-activation database counts mismatch: {counts}")
    historical = _historical_seed_exact(conn, bundle)
    keys = [item["natural_key"] for item in bundle["artifacts"]]
    conflicting = conn.execute(
        """SELECT natural_key, artifact_version, content_sha256
           FROM editorial_artifact_versions
           WHERE natural_key = ANY(%s)""",
        (keys,),
    ).fetchall()
    existing_batch = conn.execute(
        "SELECT batch_id FROM editorial_artifact_batches WHERE deterministic_batch_key = %s",
        (BATCH_KEY,),
    ).fetchone()
    registry = conn.execute(
        """SELECT artifact_id FROM editorial_publication_registry
           WHERE member_bioguide_id = %s AND issue_id = %s""",
        (MEMBER_ID, ISSUE_ID),
    ).fetchone()
    if conflicting or existing_batch or registry:
        raise StoreSafetyError("activation target is not absent")
    return {
        "read_only": True,
        "schema_exact": True,
        "historical_seed": historical,
        "counts": counts,
        "security": security,
        "target_absent": True,
    }


def _row_for_selector(conn: Any) -> dict[str, Any]:
    row = conn.execute(
        """SELECT registry.*, artifact.payload_jsonb, artifact.content_sha256,
                  artifact.editorial_status, artifact.benchmark_status,
                  artifact.production_eligible, artifact.schema_version,
                  artifact.artifact_version, artifact.natural_key
           FROM editorial_publication_registry registry
           JOIN editorial_artifact_versions artifact
             ON artifact.artifact_id = registry.artifact_id
           WHERE registry.member_bioguide_id = %s AND registry.issue_id = %s""",
        (MEMBER_ID, ISSUE_ID),
    ).fetchone()
    if not row:
        raise StoreSafetyError("activation registry row is absent")
    return dict(row)


def _selector_check(conn: Any) -> dict[str, Any]:
    rows = EditorialArtifactRepository(conn).publication_selector()
    if len(rows) != 1:
        raise StoreSafetyError("runtime selector relationship graph failed")
    scopes: dict[str, str] = {}
    for scope in ("119", "all", "118"):
        response = select_public_presentations(
            rows,
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id=MEMBER_ID,
            scope=scope,
        )
        justice = next(
            item
            for item in response["presentations"]
            if item["issue_id"] == ISSUE_ID
        )
        scopes[scope] = justice["tier"]
    other = select_public_presentations(
        rows,
        legislator_id="leg_other",
        member_bioguide_id="A000001",
        scope="119",
    )
    other_justice = next(
        item for item in other["presentations"] if item["issue_id"] == ISSUE_ID
    )
    if scopes != {
        "119": "reviewed_conclusion",
        "all": "reviewed_conclusion",
        "118": "receipts_only",
    } or other_justice["tier"] != "receipts_only":
        raise StoreSafetyError("runtime selector contract failed")
    return {
        "F000477": scopes,
        "other_member_119": other_justice["tier"],
        "selector_rows": len(rows),
    }


def _postcheck(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    counts = _counts(conn)
    if counts != bundle["expected_counts"]["after"]:
        raise StoreSafetyError(f"post-activation counts mismatch: {counts}")
    batch = conn.execute(
        """SELECT batch_id, source_commit_sha, manifest_sha256, artifact_count,
                  relationship_count, status
           FROM editorial_artifact_batches WHERE deterministic_batch_key = %s""",
        (BATCH_KEY,),
    ).fetchone()
    if not batch or (
        batch["source_commit_sha"],
        batch["manifest_sha256"],
        batch["artifact_count"],
        batch["relationship_count"],
        batch["status"],
    ) != (SOURCE_COMMIT, bundle["bundle_sha256"], 3, 2, "applied"):
        raise StoreSafetyError("activation batch receipt mismatch")
    stored = conn.execute(
        """SELECT natural_key, artifact_version, content_sha256, payload_jsonb
           FROM editorial_artifact_versions WHERE batch_id = %s
           ORDER BY natural_key""",
        (batch["batch_id"],),
    ).fetchall()
    expected = sorted(
        (
            item["natural_key"],
            item["artifact_version"],
            item["content_sha256"],
        )
        for item in bundle["artifacts"]
    )
    actual = sorted(
        (row["natural_key"], row["artifact_version"], row["content_sha256"])
        for row in stored
    )
    if actual != expected:
        raise StoreSafetyError("stored activation artifacts differ from bundle")
    if any(
        row["content_sha256"] != semantic_hash(row["payload_jsonb"])
        for row in stored
    ):
        raise StoreSafetyError("stored activation payload digest mismatch")
    relationships = [
        {
            "parent_natural_key": row["parent_natural_key"],
            "child_natural_key": row["child_natural_key"],
            "relationship_type": row["relationship_type"],
            "ordinal": row["ordinal"],
            "metadata": row["metadata_jsonb"],
        }
        for row in conn.execute(
            """SELECT parent.natural_key AS parent_natural_key,
                      child.natural_key AS child_natural_key,
                      rel.relationship_type, rel.ordinal, rel.metadata_jsonb
               FROM editorial_artifact_relationships rel
               JOIN editorial_artifact_versions parent
                 ON parent.artifact_id = rel.parent_artifact_id
               JOIN editorial_artifact_versions child
                 ON child.artifact_id = rel.child_artifact_id
               WHERE parent.batch_id = %s
               ORDER BY parent.natural_key, rel.relationship_type,
                        child.natural_key""",
            (batch["batch_id"],),
        ).fetchall()
    ]
    if relationships != bundle["relationships"]:
        raise StoreSafetyError("stored activation relationships differ from bundle")
    registry_row = _row_for_selector(conn)
    if (
        registry_row["publicly_active"] is not True
        or registry_row["deactivated_at"] is not None
        or registry_row["publication_metadata_jsonb"]
        != bundle["publication_registry"]["publication_metadata"]
    ):
        raise StoreSafetyError("stored publication registry metadata differs from bundle")
    return {
        "counts": counts,
        "batch_id": int(batch["batch_id"]),
        "artifact_ids": [
            int(row["artifact_id"])
            for row in conn.execute(
                """SELECT artifact_id FROM editorial_artifact_versions
                   WHERE batch_id = %s ORDER BY artifact_id""",
                (batch["batch_id"],),
            ).fetchall()
        ],
        "selector": _selector_check(conn),
        "semantic_hashes": {
            "artifacts_sha256": semantic_hash(bundle["artifacts"]),
            "relationships_sha256": semantic_hash(relationships),
        },
    }


def _apply(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    counts = _counts(conn)
    if counts == bundle["expected_counts"]["after"]:
        return {
            "already_applied": True,
            "rows_inserted": 0,
            "postcheck": _postcheck(conn, bundle),
        }
    preflight = _preflight(conn, bundle)
    batch = conn.execute(
        """INSERT INTO editorial_artifact_batches
           (deterministic_batch_key, source_commit_sha, manifest_sha256, status,
            artifact_count, relationship_count, applied_at)
           VALUES (%s,%s,%s,'applied',3,2,NOW()) RETURNING batch_id""",
        (BATCH_KEY, SOURCE_COMMIT, bundle["bundle_sha256"]),
    ).fetchone()
    batch_id = int(batch["batch_id"])
    ids: dict[str, int] = {}
    for item in bundle["artifacts"]:
        row = conn.execute(
            """INSERT INTO editorial_artifact_versions
               (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,
                content_sha256,source_manifest_sha256,source_commit_sha,batch_id,
                member_bioguide_id,issue_id,congress,chamber,canonical_action_id,
                episode_id,policy_family_id,editorial_status,benchmark_status,
                production_eligible,review_route)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING artifact_id""",
            (
                item["artifact_type"], item["natural_key"], item["schema_version"],
                item["artifact_version"], Jsonb(item["payload"]), item["content_sha256"],
                item["source_manifest_sha256"], item["source_commit_sha"], batch_id,
                item["member_bioguide_id"], item["issue_id"], item["congress"],
                item["chamber"], item["canonical_action_id"], item["episode_id"],
                item["policy_family_id"], item["editorial_status"],
                item["benchmark_status"], item["production_eligible"],
                item["review_route"],
            ),
        ).fetchone()
        ids[item["natural_key"]] = int(row["artifact_id"])
    for rel in bundle["relationships"]:
        conn.execute(
            """INSERT INTO editorial_artifact_relationships
               (parent_artifact_id,child_artifact_id,relationship_type,ordinal,metadata_jsonb)
               VALUES (%s,%s,%s,%s,%s)""",
            (
                ids[rel["parent_natural_key"]],
                ids[rel["child_natural_key"]],
                rel["relationship_type"],
                rel["ordinal"],
                Jsonb(rel["metadata"]),
            ),
        )
    registry = bundle["publication_registry"]
    deleted_registry = conn.execute(
        """INSERT INTO editorial_publication_registry
           (member_bioguide_id,issue_id,artifact_id,publicly_active,activated_at,
            publication_metadata_jsonb)
           VALUES (%s,%s,%s,TRUE,NOW(),%s)""",
        (
            MEMBER_ID,
            ISSUE_ID,
            ids[PRESENTATION_KEY],
            Jsonb(registry["publication_metadata"]),
        ),
    )
    return {
        "already_applied": False,
        "rows_inserted": 7,
        "preflight": preflight,
        "postcheck": _postcheck(conn, bundle),
    }


def _rollback(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    registry = _row_for_selector(conn)
    metadata = registry["publication_metadata_jsonb"]
    if (
        registry["content_sha256"] != ACTIVE_ARTIFACT_SHA256
        or metadata.get("activation_bundle_id") != BUNDLE_ID
        or metadata.get("approval_receipt", {}).get("receipt_id")
        != bundle["activation_target"]["approval_receipt_id"]
    ):
        raise StoreSafetyError("rollback registry identity mismatch")
    post = _postcheck(conn, bundle)
    deleted_registry = conn.execute(
        """DELETE FROM editorial_publication_registry
           WHERE member_bioguide_id = %s AND issue_id = %s""",
        (MEMBER_ID, ISSUE_ID),
    )
    batch = conn.execute(
        "SELECT batch_id FROM editorial_artifact_batches WHERE deterministic_batch_key = %s",
        (BATCH_KEY,),
    ).fetchone()
    deleted_relationships = conn.execute(
        """DELETE FROM editorial_artifact_relationships rel
           USING editorial_artifact_versions parent
           WHERE rel.parent_artifact_id = parent.artifact_id
             AND parent.batch_id = %s""",
        (batch["batch_id"],),
    )
    conn.execute(
        "SELECT set_config('app.editorial_artifact_rollback_batch', %s, true)",
        (BATCH_KEY,),
    )
    deleted_artifacts = conn.execute(
        "DELETE FROM editorial_artifact_versions WHERE batch_id = %s",
        (batch["batch_id"],),
    )
    deleted_batch = conn.execute(
        "DELETE FROM editorial_artifact_batches WHERE batch_id = %s",
        (batch["batch_id"],),
    )
    if (
        deleted_registry.rowcount,
        deleted_relationships.rowcount,
        deleted_artifacts.rowcount,
        deleted_batch.rowcount,
    ) != (1, 2, 3, 1):
        raise StoreSafetyError("rollback deletion count mismatch")
    counts = _counts(conn)
    if counts != bundle["expected_counts"]["before"]:
        raise StoreSafetyError(f"rollback counts mismatch: {counts}")
    historical = _historical_seed_exact(conn, bundle)
    return {"removed_batch_id": post["batch_id"], "counts": counts, "historical_seed": historical}


def _api_smoke(base_url: str) -> dict[str, Any]:
    base = base_url.rstrip("/")
    with urlopen(f"{base}/health", timeout=20) as response:
        health = json.load(response)
    commit = health.get("commit_sha")
    _exact_deployed_commit(commit)
    tiers: dict[str, str] = {}
    for scope in ("119", "all", "118"):
        url = (
            f"{base}/legislators/leg_valerie_p_foushee/"
            f"editorial-presentations?scope={scope}"
        )
        with urlopen(url, timeout=20) as response:
            payload = json.load(response)
        justice = next(
            item for item in payload["presentations"] if item["issue_id"] == ISSUE_ID
        )
        tiers[scope] = justice["tier"]
    if tiers != {
        "119": "reviewed_conclusion",
        "all": "reviewed_conclusion",
        "118": "receipts_only",
    }:
        raise StoreSafetyError(f"public API smoke contract failed: {tiers}")
    return {"health": health, "tiers": tiers}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pinned Foushee Justice publication activation operator"
    )
    parser.add_argument(
        "mode",
        choices=(
            "verify-bundle",
            "preflight",
            "prepare-backup",
            "apply",
            "postcheck",
            "rollback",
        ),
    )
    parser.add_argument("--database-url")
    parser.add_argument("--target", choices=("disposable", "production"), default="disposable")
    parser.add_argument("--bundle-id")
    parser.add_argument("--bundle-sha256")
    parser.add_argument("--confirm-bundle-digest")
    parser.add_argument("--deployed-commit")
    parser.add_argument("--required-schema", default="0016")
    parser.add_argument("--preflight-report", type=Path)
    parser.add_argument("--report-path", type=Path)
    parser.add_argument("--backup-proof", type=Path)
    parser.add_argument("--restore-database-url")
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--confirm-production-activation", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    parser.add_argument("--confirm-rollback-token")
    parser.add_argument("--confirm-batch-id", type=int)
    parser.add_argument("--confirm-artifact-ids")
    parser.add_argument("--api-base-url")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    bundle = load_activation_bundle()
    if args.required_schema != "0016":
        raise StoreSafetyError("deployed schema expectation must be exactly migration 0016")
    if args.mode != "verify-bundle" and not args.bundle_id:
        _parser().error("DB-facing modes require an explicit --bundle-id")
    if args.bundle_id is not None and args.bundle_id != BUNDLE_ID:
        raise StoreSafetyError("bundle ID confirmation mismatch")
    if args.bundle_sha256 and args.bundle_sha256 != bundle["bundle_sha256"]:
        raise StoreSafetyError("bundle digest confirmation mismatch")
    result: dict[str, Any] = {
        "mode": args.mode,
        "bundle_path": BUNDLE_PATH.relative_to(ROOT).as_posix(),
        "bundle_id": BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "source_commit": SOURCE_COMMIT,
        "offline_verification": "passed",
    }
    if args.mode == "verify-bundle":
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.mode != "rollback" and not args.deployed_commit:
        raise StoreSafetyError(
            "DB-facing modes require the exact deployed backend commit"
        )
    result["deployment"] = (
        _exact_deployed_commit(args.deployed_commit)
        if args.deployed_commit
        else {"verification": "database_only_safe_rollback"}
    )
    db_url = args.database_url or os.getenv("EDITORIAL_DISPOSABLE_DATABASE_URL")
    if args.target == "production":
        db_url = args.database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise StoreSafetyError("an explicit database URL is required")
    result["target"] = target_info(db_url, args.target, None)
    if args.mode in {"apply", "rollback"}:
        if args.confirm_bundle_digest != bundle["bundle_sha256"]:
            raise StoreSafetyError(
                "write modes require --confirm-bundle-digest with the exact digest"
            )
    if args.mode == "prepare-backup":
        if not args.preflight_report or not args.restore_database_url or not args.evidence_dir:
            raise StoreSafetyError(
                "prepare-backup requires preflight report, restore database URL, and evidence directory"
            )
        proof_path = _prepare_backup(
            db_url,
            args.restore_database_url,
            args.evidence_dir,
            bundle,
            args.deployed_commit,
            args.preflight_report,
        )
        result["backup_proof"] = str(proof_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.mode == "apply":
        if not args.preflight_report:
            raise StoreSafetyError("apply requires the successful preflight report")
        if not args.backup_proof:
            raise StoreSafetyError("apply requires a validated backup proof")
        result["backup"] = _verify_backup_proof(
            args.backup_proof,
            bundle,
            args.deployed_commit,
            args.preflight_report,
        )
    if args.target == "production" and args.mode == "apply":
        if not args.confirm_production_activation:
            raise StoreSafetyError("production activation lacks explicit confirmation")
    if args.target == "production" and args.mode == "rollback":
        if not args.confirm_production_rollback:
            raise StoreSafetyError("production rollback lacks explicit confirmation")
    if args.mode == "rollback":
        expected_token = f"ROLLBACK:{BUNDLE_ID}:{bundle['bundle_sha256']}"
        if args.confirm_rollback_token != expected_token:
            raise StoreSafetyError("rollback requires the exact confirmation token")
    read_only = args.mode in {"preflight", "postcheck"}
    with _connect(db_url, autocommit=read_only) as conn:
        if read_only:
            conn.execute("SET default_transaction_read_only = on")
        with conn.transaction():
            if read_only:
                conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL lock_timeout = '10000ms'")
            conn.execute("SET LOCAL statement_timeout = '120000ms'")
            if args.mode in {"apply", "rollback"}:
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
            if args.mode == "preflight":
                result["preflight"] = _preflight(conn, bundle)
                report = _preflight_report(
                    conn, bundle, args.deployed_commit
                )
                result["preflight_report"] = report
                if args.report_path:
                    _write_json(args.report_path, report)
                    result["preflight_report_path"] = str(
                        args.report_path.resolve()
                    )
            elif args.mode == "apply":
                result["bound_preflight"] = _verify_preflight_report(
                    args.preflight_report,
                    bundle,
                    args.deployed_commit,
                    conn,
                )
                result["application"] = _apply(conn, bundle)
            elif args.mode == "postcheck":
                result["postcheck"] = _postcheck(conn, bundle)
            else:
                post = _postcheck(conn, bundle)
                expected_ids = ",".join(str(item) for item in post["artifact_ids"])
                if (
                    args.confirm_batch_id != post["batch_id"]
                    or args.confirm_artifact_ids != expected_ids
                ):
                    raise StoreSafetyError(
                        "rollback requires the exact live batch and artifact IDs"
                    )
                result["rollback"] = _rollback(conn, bundle)
    if args.api_base_url:
        result["api_smoke"] = _api_smoke(args.api_base_url)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StoreSafetyError, ValueError) as exc:
        mode = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        failure = {"status": "blocked", "mode": mode, "error": str(exc)}
        if mode == "postcheck":
            failure["recommendation"] = (
                "Run the exact rollback mode immediately after confirming the "
                "reported live batch and artifact identities."
            )
        print(json.dumps(failure, indent=2), file=sys.stderr)
        raise SystemExit(2)
