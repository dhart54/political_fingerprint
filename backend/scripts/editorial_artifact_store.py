from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes, urlsplit

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from dotenv import dotenv_values

from app.editorial_artifacts.bundle import (
    BATCH_KEY,
    STARTING_COMMIT,
    build_seed_bundle,
    canonical_json,
    semantic_hash,
    validate_bundle,
)
from app.editorial_artifacts.migration import (
    MIGRATION,
    MIGRATION_SHA256,
    TABLES,
    strip_transaction_wrappers,
    validate_migration,
)
from app.editorial_artifacts.repository import EditorialArtifactRepository

MANIFEST = ROOT / "docs/editorial/editorial_artifact_persistence_v1/seed_manifest.json"
REPORT = ROOT / "docs/review_packets/editorial_artifact_persistence_v1.json"
LOCK_KEY = "political_fingerprint:editorial_artifact_persistence_v1"
EXPECTED_PRODUCTION_TARGET = {
    "scheme": "postgresql",
    "host": "aws-1-us-east-1.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
}
EXPECTED_DATABASE_USERNAME_SHA256 = "5c6d4369c3ac8d639153290471b0f185e5bbae0465c1d9f275e114b016be0f76"
PROTECTED_TABLES = ("legislators", "bills", "roll_calls", "vote_interpretations")
EXPECTED_COLUMNS = {
    "editorial_artifact_batches": {
        "batch_id", "deterministic_batch_key", "source_commit_sha", "manifest_sha256",
        "status", "artifact_count", "relationship_count", "created_at", "applied_at",
    },
    "editorial_artifact_versions": {
        "artifact_id", "artifact_type", "natural_key", "schema_version", "artifact_version",
        "payload_jsonb", "content_sha256", "source_manifest_sha256", "source_commit_sha",
        "batch_id", "supersedes_artifact_id", "member_bioguide_id", "issue_id", "congress",
        "chamber", "canonical_roll_call_id", "canonical_action_id", "episode_id",
        "policy_family_id", "editorial_status", "benchmark_status", "production_eligible",
        "review_route", "created_at",
    },
    "editorial_artifact_relationships": {
        "parent_artifact_id", "child_artifact_id", "relationship_type", "ordinal", "metadata_jsonb",
    },
    "editorial_publication_registry": {
        "member_bioguide_id", "issue_id", "artifact_id", "publicly_active",
        "activated_at", "deactivated_at", "publication_metadata_jsonb",
    },
}
EXPECTED_TRIGGERS = {
    "editorial_artifact_versions_immutable",
    "editorial_publication_registry_fail_closed",
}
EXPECTED_FUNCTIONS = {
    "guard_editorial_artifact_immutability",
    "guard_editorial_publication_activation",
}
EXPECTED_CUSTOM_INDEXES = {
    "idx_editorial_artifact_versions_type_key",
    "idx_editorial_artifact_versions_member_issue",
    "idx_editorial_artifact_versions_action",
    "idx_editorial_artifact_versions_episode",
    "idx_editorial_artifact_versions_family",
    "idx_editorial_artifact_versions_status",
    "idx_editorial_artifact_versions_hash",
    "idx_editorial_artifact_versions_batch",
    "idx_editorial_artifact_relationships_child",
}


class StoreSafetyError(RuntimeError):
    pass


def load_manifest() -> dict[str, Any]:
    checked_in = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = build_seed_bundle()
    if checked_in != generated:
        raise StoreSafetyError("checked-in seed manifest differs from the deterministic builder")
    validate_bundle(checked_in)
    return checked_in


def target_info(db_url: str, target: str, env_path: Path | None) -> dict[str, Any]:
    try:
        parsed = urlsplit(db_url)
        encoded_username = parsed.username
        if not encoded_username or re.search(r"%(?![0-9A-Fa-f]{2})", encoded_username):
            raise ValueError("missing or malformed username")
        username = unicodedata.normalize(
            "NFC", unquote_to_bytes(encoded_username).decode("utf-8", "strict")
        )
    except (TypeError, ValueError, UnicodeDecodeError) as exc:
        raise StoreSafetyError("configured database target URL is invalid") from exc
    try:
        reported_env = str(env_path.relative_to(ROOT)) if env_path else None
    except ValueError:
        reported_env = "configured external backend environment"
    result = {
        "target": target,
        "environment_file": reported_env,
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "username_present": True,
        "password_present": bool(parsed.password),
        "raw_url_recorded": False,
    }
    if target == "production":
        username_match = hashlib.sha256(username.encode("utf-8")).hexdigest() == EXPECTED_DATABASE_USERNAME_SHA256
        result["username_identity_pinned"] = True
        result["username_sha256_matches"] = username_match
        exact = all(result[key] == value for key, value in EXPECTED_PRODUCTION_TARGET.items())
        if not exact or not result["password_present"] or not username_match:
            raise StoreSafetyError("configured database does not match the exact approved production target")
        result["exact_approved_target"] = True
    else:
        if parsed.scheme not in {"postgresql", "postgres"} or not result["host"] or not result["database"]:
            raise StoreSafetyError("disposable target is not a PostgreSQL database")
        result["exact_approved_target"] = False
    return result


def _connect(db_url: str, *, autocommit: bool = False):
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(db_url, row_factory=dict_row, autocommit=autocommit)


def _fingerprint(conn: Any, table: str) -> dict[str, Any]:
    rows = [
        dict(row)
        for row in conn.execute(
            f"SELECT to_jsonb(source) AS row FROM (SELECT * FROM public.{table} ORDER BY 1) source"
        ).fetchall()
    ]
    payload = [row["row"] for row in rows]
    return {"row_count": len(payload), "sha256": semantic_hash(payload)}


def schema_state(conn: Any) -> dict[str, Any]:
    rows = conn.execute(
        """SELECT table_name FROM information_schema.tables
           WHERE table_schema = 'public' AND table_name = ANY(%s)""",
        (list(TABLES),),
    ).fetchall()
    existing = {row["table_name"] for row in rows}
    return {
        "existing_tables": sorted(existing),
        "state": "absent" if not existing else "complete" if existing == TABLES else "partial",
    }


def live_schema_contract(conn: Any) -> dict[str, Any]:
    columns: dict[str, set[str]] = {table: set() for table in TABLES}
    for row in conn.execute(
        """SELECT table_name, column_name FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = ANY(%s)""",
        (list(TABLES),),
    ).fetchall():
        columns[row["table_name"]].add(row["column_name"])
    triggers = {
        row["trigger_name"]
        for row in conn.execute(
            """SELECT trigger_name FROM information_schema.triggers
               WHERE trigger_schema = 'public' AND event_object_table = ANY(%s)""",
            (list(TABLES),),
        ).fetchall()
    }
    functions = {
        row["routine_name"]
        for row in conn.execute(
            """SELECT routine_name FROM information_schema.routines
               WHERE routine_schema = 'public' AND routine_name = ANY(%s)""",
            (list(EXPECTED_FUNCTIONS),),
        ).fetchall()
    }
    indexes = {
        row["indexname"]
        for row in conn.execute(
            """SELECT indexname FROM pg_indexes
               WHERE schemaname = 'public' AND tablename = ANY(%s)""",
            (list(TABLES),),
        ).fetchall()
    }
    constraints = [
        dict(row)
        for row in conn.execute(
            """SELECT table_name, constraint_name, constraint_type
               FROM information_schema.table_constraints
               WHERE table_schema = 'public' AND table_name = ANY(%s)
               ORDER BY table_name, constraint_name""",
            (list(TABLES),),
        ).fetchall()
    ]
    exact_columns = columns == EXPECTED_COLUMNS
    required_objects = (
        triggers == EXPECTED_TRIGGERS
        and functions == EXPECTED_FUNCTIONS
        and EXPECTED_CUSTOM_INDEXES <= indexes
    )
    constraint_types = {row["constraint_type"] for row in constraints}
    required_constraint_classes = {
        "PRIMARY KEY", "UNIQUE", "CHECK", "FOREIGN KEY"
    } <= constraint_types
    if not exact_columns or not required_objects or not required_constraint_classes:
        raise StoreSafetyError("live editorial schema differs from the reviewed contract")
    return {
        "exact_columns": True,
        "triggers_exact": True,
        "functions_exact": True,
        "required_indexes_present": True,
        "required_constraint_classes_present": True,
        "columns": {table: sorted(names) for table, names in sorted(columns.items())},
        "triggers": sorted(triggers),
        "functions": sorted(functions),
        "indexes": sorted(indexes),
        "constraints": constraints,
    }


def resolve_canonical_identities(conn: Any, bundle: dict[str, Any]) -> dict[str, int]:
    member_ids = sorted({
        item["member_bioguide_id"] for item in bundle["artifacts"]
        if item["member_bioguide_id"]
    })
    found_members = {
        row["bioguide_id"]
        for row in conn.execute(
            "SELECT bioguide_id FROM legislators WHERE bioguide_id = ANY(%s)",
            (member_ids,),
        ).fetchall()
    }
    if found_members != set(member_ids):
        raise StoreSafetyError(f"canonical member identity mismatch: {sorted(set(member_ids) - found_members)}")
    action_ids = sorted({
        item["canonical_action_id"] for item in bundle["artifacts"]
        if item["canonical_action_id"]
    })
    resolved: dict[str, int] = {}
    for action_id in action_ids:
        chamber, congress, session, roll = action_id.split(":")
        row = conn.execute(
            """SELECT id FROM roll_calls
               WHERE chamber = %s AND congress = %s AND session = %s AND rollcall_number = %s""",
            (chamber, int(congress), int(session), int(roll)),
        ).fetchone()
        if not row:
            raise StoreSafetyError(f"canonical roll-call identity cannot be resolved: {action_id}")
        resolved[action_id] = int(row["id"])
    return resolved


def inspect(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    state = schema_state(conn)
    if state["state"] == "partial":
        raise StoreSafetyError("partial or conflicting editorial artifact schema exists")
    canonical = {table: _fingerprint(conn, table) for table in PROTECTED_TABLES}
    resolved = resolve_canonical_identities(conn, bundle)
    result = {
        "schema": state,
        "canonical_fingerprints": canonical,
        "canonical_member_count": len({
            item["member_bioguide_id"] for item in bundle["artifacts"] if item["member_bioguide_id"]
        }),
        "canonical_action_count": len(resolved),
        "read_only": True,
    }
    if state["state"] == "complete":
        batch = conn.execute(
            """SELECT deterministic_batch_key, source_commit_sha, manifest_sha256,
                      artifact_count, relationship_count, status
               FROM editorial_artifact_batches WHERE deterministic_batch_key = %s""",
            (BATCH_KEY,),
        ).fetchone()
        result["batch"] = dict(batch) if batch else None
        result["publication_registry_count"] = int(
            conn.execute("SELECT COUNT(*) AS n FROM editorial_publication_registry").fetchone()["n"]
        )
    return result


def insert_bundle(conn: Any, bundle: dict[str, Any], roll_ids: dict[str, int]) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    batch = conn.execute(
        """INSERT INTO editorial_artifact_batches
           (deterministic_batch_key, source_commit_sha, manifest_sha256, status,
            artifact_count, relationship_count, applied_at)
           VALUES (%s, %s, %s, 'applied', %s, %s, NOW())
           ON CONFLICT (deterministic_batch_key) DO NOTHING
           RETURNING batch_id""",
        (
            BATCH_KEY,
            STARTING_COMMIT,
            bundle["manifest_sha256"],
            bundle["expected_counts"]["artifacts"],
            bundle["expected_counts"]["relationships"],
        ),
    ).fetchone()
    if batch is None:
        existing = conn.execute(
            "SELECT * FROM editorial_artifact_batches WHERE deterministic_batch_key = %s",
            (BATCH_KEY,),
        ).fetchone()
        expected = (
            STARTING_COMMIT,
            bundle["manifest_sha256"],
            bundle["expected_counts"]["artifacts"],
            bundle["expected_counts"]["relationships"],
        )
        actual = (
            existing["source_commit_sha"],
            existing["manifest_sha256"],
            existing["artifact_count"],
            existing["relationship_count"],
        )
        if actual != expected:
            raise StoreSafetyError("existing deterministic batch conflicts with the reviewed manifest")
        batch_id = int(existing["batch_id"])
    else:
        batch_id = int(batch["batch_id"])

    ids: dict[str, int] = {}
    inserted = 0
    idempotent = 0
    for item in bundle["artifacts"]:
        existing = conn.execute(
            """SELECT artifact_id, content_sha256 FROM editorial_artifact_versions
               WHERE natural_key = %s AND artifact_version = %s""",
            (item["natural_key"], item["artifact_version"]),
        ).fetchone()
        if existing:
            if existing["content_sha256"] != item["content_sha256"]:
                raise StoreSafetyError(f"conflicting immutable artifact version: {item['natural_key']}")
            ids[item["natural_key"]] = int(existing["artifact_id"])
            idempotent += 1
            continue
        row = conn.execute(
            """INSERT INTO editorial_artifact_versions
               (artifact_type, natural_key, schema_version, artifact_version, payload_jsonb,
                content_sha256, source_manifest_sha256, source_commit_sha, batch_id,
                member_bioguide_id, issue_id, congress, chamber, canonical_roll_call_id,
                canonical_action_id, episode_id, policy_family_id, editorial_status,
                benchmark_status, production_eligible, review_route)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING artifact_id""",
            (
                item["artifact_type"], item["natural_key"], item["schema_version"],
                item["artifact_version"], Jsonb(item["payload"]), item["content_sha256"],
                item["source_manifest_sha256"], item["source_commit_sha"], batch_id,
                item["member_bioguide_id"], item["issue_id"], item["congress"], item["chamber"],
                roll_ids.get(item["canonical_action_id"]), item["canonical_action_id"],
                item["episode_id"], item["policy_family_id"], item["editorial_status"],
                item["benchmark_status"], item["production_eligible"], item["review_route"],
            ),
        ).fetchone()
        ids[item["natural_key"]] = int(row["artifact_id"])
        inserted += 1

    relationships_inserted = 0
    for rel in bundle["relationships"]:
        result = conn.execute(
            """INSERT INTO editorial_artifact_relationships
               (parent_artifact_id, child_artifact_id, relationship_type, ordinal, metadata_jsonb)
               VALUES (%s,%s,%s,%s,%s)
               ON CONFLICT DO NOTHING""",
            (
                ids[rel["parent_natural_key"]], ids[rel["child_natural_key"]],
                rel["relationship_type"], rel["ordinal"], Jsonb(rel["metadata"]),
            ),
        )
        relationships_inserted += result.rowcount
    return {
        "batch_id": batch_id,
        "artifacts_inserted": inserted,
        "artifacts_idempotent": idempotent,
        "relationships_inserted": relationships_inserted,
    }


def export_bundle(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    batch = conn.execute(
        "SELECT batch_id FROM editorial_artifact_batches WHERE deterministic_batch_key = %s",
        (BATCH_KEY,),
    ).fetchone()
    if not batch:
        raise StoreSafetyError("reviewed batch is absent")
    rows = conn.execute(
        """SELECT artifact_type, natural_key, schema_version, artifact_version, payload_jsonb,
                  content_sha256, source_manifest_sha256, source_commit_sha,
                  member_bioguide_id, issue_id, congress, chamber, canonical_action_id,
                  episode_id, policy_family_id, editorial_status, benchmark_status,
                  production_eligible, review_route
           FROM editorial_artifact_versions WHERE batch_id = %s
           ORDER BY artifact_type, natural_key, artifact_version""",
        (batch["batch_id"],),
    ).fetchall()
    artifacts = []
    for row in rows:
        item = dict(row)
        item["payload"] = item.pop("payload_jsonb")
        if item["content_sha256"] != semantic_hash(item["payload"]):
            raise StoreSafetyError(f"database content hash mismatch: {item['natural_key']}")
        artifacts.append(item)
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
               JOIN editorial_artifact_versions parent ON parent.artifact_id = rel.parent_artifact_id
               JOIN editorial_artifact_versions child ON child.artifact_id = rel.child_artifact_id
               WHERE parent.batch_id = %s
               ORDER BY parent.natural_key, rel.relationship_type, rel.ordinal, child.natural_key""",
            (batch["batch_id"],),
        ).fetchall()
    ]
    semantic_match = artifacts == bundle["artifacts"] and relationships == bundle["relationships"]
    return {
        "artifact_count": len(artifacts),
        "relationship_count": len(relationships),
        "artifact_semantic_sha256": semantic_hash(artifacts),
        "relationship_semantic_sha256": semantic_hash(relationships),
        "repository_artifact_semantic_sha256": semantic_hash(bundle["artifacts"]),
        "repository_relationship_semantic_sha256": semantic_hash(bundle["relationships"]),
        "semantic_match": semantic_match,
    }


def probe_fail_closed_guards(conn: Any, bundle: dict[str, Any]) -> dict[str, bool]:
    import psycopg

    candidate = conn.execute(
        """SELECT artifact_id, member_bioguide_id, issue_id
           FROM editorial_artifact_versions
           WHERE artifact_type = 'issue_public_presentation'
           ORDER BY artifact_id LIMIT 1"""
    ).fetchone()
    conn.execute("SAVEPOINT editorial_publication_guard_probe")
    try:
        conn.execute(
            """INSERT INTO editorial_publication_registry
               (member_bioguide_id, issue_id, artifact_id, publicly_active, activated_at)
               VALUES (%s, %s, %s, TRUE, NOW())""",
            (candidate["member_bioguide_id"], candidate["issue_id"], candidate["artifact_id"]),
        )
    except psycopg.Error:
        conn.execute("ROLLBACK TO SAVEPOINT editorial_publication_guard_probe")
        publication_rejected = True
    else:
        conn.execute("ROLLBACK TO SAVEPOINT editorial_publication_guard_probe")
        publication_rejected = False
    conn.execute("RELEASE SAVEPOINT editorial_publication_guard_probe")

    changed = copy.deepcopy(bundle)
    changed["artifacts"][0]["content_sha256"] = "1" * 64
    try:
        insert_bundle(conn, changed, resolve_canonical_identities(conn, changed))
    except StoreSafetyError:
        conflict_rejected = True
    else:
        conflict_rejected = False
    if not publication_rejected or not conflict_rejected:
        raise StoreSafetyError("fail-closed production guard probe failed")
    return {
        "pending_publication_rejected": publication_rejected,
        "conflicting_version_rejected": conflict_rejected,
        "probe_rows_committed": False,
    }


def postcheck(
    conn: Any,
    bundle: dict[str, Any],
    pre_fingerprints: dict[str, Any] | None,
    *,
    probe_guards: bool = False,
) -> dict[str, Any]:
    state = schema_state(conn)
    if state["state"] != "complete":
        raise StoreSafetyError("editorial artifact schema is not complete")
    schema_contract = live_schema_contract(conn)
    counts = {
        "artifacts": int(conn.execute(
            """SELECT COUNT(*) AS n FROM editorial_artifact_versions version
               JOIN editorial_artifact_batches batch ON batch.batch_id = version.batch_id
               WHERE batch.deterministic_batch_key = %s""", (BATCH_KEY,)
        ).fetchone()["n"]),
        "relationships": int(conn.execute(
            """SELECT COUNT(*) AS n FROM editorial_artifact_relationships rel
               JOIN editorial_artifact_versions version ON version.artifact_id = rel.parent_artifact_id
               JOIN editorial_artifact_batches batch ON batch.batch_id = version.batch_id
               WHERE batch.deterministic_batch_key = %s""", (BATCH_KEY,)
        ).fetchone()["n"]),
        "publication_registry": int(conn.execute(
            "SELECT COUNT(*) AS n FROM editorial_publication_registry"
        ).fetchone()["n"]),
    }
    if counts != {
        "artifacts": bundle["expected_counts"]["artifacts"],
        "relationships": bundle["expected_counts"]["relationships"],
        "publication_registry": 0,
    }:
        raise StoreSafetyError(f"production row count mismatch: {counts}")
    pending = int(conn.execute(
        """SELECT COUNT(*) AS n FROM editorial_artifact_versions
           WHERE artifact_type = 'issue_public_presentation'
             AND editorial_status = 'human_approval_pending'
             AND benchmark_status = 'not_promoted'
             AND production_eligible = FALSE"""
    ).fetchone()["n"])
    selector_count = len(EditorialArtifactRepository(conn).publication_selector())
    privileges = {
        role: {
            table: bool(conn.execute(
                "SELECT has_table_privilege(%s, %s, 'SELECT') AS allowed",
                (role, f"public.{table}"),
            ).fetchone()["allowed"])
            for table in sorted(TABLES)
        }
        for role in ("anon", "authenticated")
    }
    if any(any(tables.values()) for tables in privileges.values()):
        raise StoreSafetyError("anon or authenticated has direct editorial artifact access")
    rls = {
        row["relname"]: {"enabled": row["relrowsecurity"], "forced": row["relforcerowsecurity"]}
        for row in conn.execute(
            """SELECT relname, relrowsecurity, relforcerowsecurity
               FROM pg_class JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
               WHERE pg_namespace.nspname = 'public' AND relname = ANY(%s)""",
            (list(TABLES),),
        ).fetchall()
    }
    if set(rls) != TABLES or not all(item["enabled"] for item in rls.values()):
        raise StoreSafetyError("RLS is not enabled on every editorial table")
    post_fingerprints = {table: _fingerprint(conn, table) for table in PROTECTED_TABLES}
    if pre_fingerprints and post_fingerprints != pre_fingerprints:
        raise StoreSafetyError("canonical table fingerprints changed")
    roundtrip = export_bundle(conn, bundle)
    if not roundtrip["semantic_match"]:
        raise StoreSafetyError("repository/database/export semantic round-trip failed")
    result = {
        "schema": state,
        "schema_contract": schema_contract,
        "counts": counts,
        "pending_slice_count": pending,
        "publication_selector_count": selector_count,
        "security": {"direct_select_privileges": privileges, "rls": rls},
        "canonical_fingerprints": post_fingerprints,
        "canonical_fingerprints_unchanged": pre_fingerprints is None or post_fingerprints == pre_fingerprints,
        "roundtrip": roundtrip,
    }
    if probe_guards:
        result["fail_closed_guard_probe"] = probe_fail_closed_guards(conn, bundle)
        if int(conn.execute("SELECT COUNT(*) AS n FROM editorial_publication_registry").fetchone()["n"]) != 0:
            raise StoreSafetyError("publication guard probe changed registry state")
    return result


def rollback_batch(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    batch = conn.execute(
        """SELECT batch_id, manifest_sha256 FROM editorial_artifact_batches
           WHERE deterministic_batch_key = %s FOR UPDATE""",
        (BATCH_KEY,),
    ).fetchone()
    if not batch or batch["manifest_sha256"] != bundle["manifest_sha256"]:
        raise StoreSafetyError("exact reviewed rollback batch is absent or hash-mismatched")
    published = int(conn.execute(
        """SELECT COUNT(*) AS n FROM editorial_publication_registry registry
           JOIN editorial_artifact_versions version ON version.artifact_id = registry.artifact_id
           WHERE version.batch_id = %s""",
        (batch["batch_id"],),
    ).fetchone()["n"])
    if published:
        raise StoreSafetyError("rollback refused because batch artifacts are published")
    before = {
        "artifacts": int(conn.execute(
            "SELECT COUNT(*) AS n FROM editorial_artifact_versions WHERE batch_id = %s",
            (batch["batch_id"],),
        ).fetchone()["n"]),
        "relationships": int(conn.execute(
            """SELECT COUNT(*) AS n FROM editorial_artifact_relationships
               WHERE parent_artifact_id IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id = %s)
                  OR child_artifact_id IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id = %s)""",
            (batch["batch_id"], batch["batch_id"]),
        ).fetchone()["n"]),
    }
    if before != {
        "artifacts": bundle["expected_counts"]["artifacts"],
        "relationships": bundle["expected_counts"]["relationships"],
    }:
        raise StoreSafetyError("rollback count precheck failed")
    conn.execute("SELECT set_config('app.editorial_artifact_rollback_batch', %s, TRUE)", (BATCH_KEY,))
    conn.execute(
        """DELETE FROM editorial_artifact_relationships
           WHERE parent_artifact_id IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id = %s)
              OR child_artifact_id IN (SELECT artifact_id FROM editorial_artifact_versions WHERE batch_id = %s)""",
        (batch["batch_id"], batch["batch_id"]),
    )
    conn.execute("DELETE FROM editorial_artifact_versions WHERE batch_id = %s", (batch["batch_id"],))
    conn.execute("DELETE FROM editorial_artifact_batches WHERE batch_id = %s", (batch["batch_id"],))
    return {"executed": True, "deleted": before, "schema_left_intact": True}


def _database_url(args: argparse.Namespace) -> tuple[str, Path | None]:
    if args.target == "production":
        env_path = args.env_path.resolve()
        db_url = dotenv_values(env_path).get("DATABASE_URL")
    else:
        env_path = None
        db_url = os.getenv(args.database_url_env)
    if not db_url:
        raise StoreSafetyError("database URL is missing for the explicit target")
    return str(db_url), env_path


def _write_report(report: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--postcheck", action="store_true")
    modes.add_argument("--export", action="store_true")
    modes.add_argument("--rollback", action="store_true")
    parser.add_argument("--target", choices=("production", "disposable"), required=True)
    parser.add_argument("--env-path", type=Path, default=ROOT / "backend/.env")
    parser.add_argument("--database-url-env", default="EDITORIAL_DISPOSABLE_DATABASE_URL")
    parser.add_argument("--batch-key", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--migration-sha256", required=True)
    parser.add_argument("--confirm-production-apply", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)

    bundle = load_manifest()
    migration = validate_migration(args.migration_sha256)
    if args.batch_key != BATCH_KEY or args.source_commit != STARTING_COMMIT:
        raise StoreSafetyError("batch key or source commit does not match the reviewed bundle")
    if args.manifest_sha256 != bundle["manifest_sha256"]:
        raise StoreSafetyError("manifest SHA-256 does not match the reviewed bundle")
    if args.migration_sha256 != MIGRATION_SHA256:
        raise StoreSafetyError("migration SHA-256 does not match the reviewed migration")

    base = {
        "mode": "dry-run" if args.dry_run else "check" if args.check else "apply" if args.apply else "postcheck" if args.postcheck else "export" if args.export else "rollback",
        "batch_key": BATCH_KEY,
        "source_commit": STARTING_COMMIT,
        "manifest_sha256": bundle["manifest_sha256"],
        "migration": migration,
        "expected_counts": bundle["expected_counts"],
        "publication_registry_expected_rows": 0,
    }
    if args.dry_run:
        print(json.dumps(base, indent=2, sort_keys=True))
        return 0

    db_url, env_path = _database_url(args)
    base["target"] = target_info(db_url, args.target, env_path)
    if args.target == "production" and args.apply and not args.confirm_production_apply:
        raise StoreSafetyError("production apply requires the exact confirmation flag")
    if args.target == "production" and args.rollback and not args.confirm_production_rollback:
        raise StoreSafetyError("production rollback requires the exact confirmation flag")

    if args.check:
        with _connect(db_url, autocommit=True) as conn:
            conn.execute("SET default_transaction_read_only = on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                conn.execute("SET LOCAL statement_timeout = '30000ms'")
                base["preflight"] = inspect(conn, bundle)
    elif args.apply:
        with _connect(db_url) as conn:
            with conn.transaction():
                conn.execute("SET LOCAL lock_timeout = '10000ms'")
                conn.execute("SET LOCAL statement_timeout = '120000ms'")
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
                pre = inspect(conn, bundle)
                base["preflight"] = pre
                if pre["schema"]["state"] == "absent":
                    conn.execute(strip_transaction_wrappers(MIGRATION.read_text(encoding="utf-8")))
                elif not pre.get("batch"):
                    pass
                base["application"] = insert_bundle(conn, bundle, resolve_canonical_identities(conn, bundle))
                base["postcheck"] = postcheck(
                    conn, bundle, pre["canonical_fingerprints"], probe_guards=True
                )
    elif args.postcheck or args.export:
        with _connect(db_url, autocommit=True) as conn:
            conn.execute("SET default_transaction_read_only = on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                conn.execute("SET LOCAL statement_timeout = '30000ms'")
                base["postcheck" if args.postcheck else "export"] = (
                    postcheck(conn, bundle, None) if args.postcheck else export_bundle(conn, bundle)
                )
    else:
        with _connect(db_url) as conn:
            with conn.transaction():
                conn.execute("SET LOCAL lock_timeout = '10000ms'")
                conn.execute("SET LOCAL statement_timeout = '120000ms'")
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
                base["rollback"] = rollback_batch(conn, bundle)

    if args.write_report:
        _write_report(base)
    print(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StoreSafetyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
