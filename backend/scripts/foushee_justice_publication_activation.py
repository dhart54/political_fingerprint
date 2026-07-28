from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
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
        "deployed_commit": actual,
        "compatible": True,
    }


def _verify_backup_proof(path: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    try:
        proof = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoreSafetyError("backup proof is missing or invalid") from exc
    expected = {
        "schema_version": "editorial_publication_backup_proof_v1",
        "bundle_id": BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "database_snapshot_created": True,
        "restore_test_passed": True,
        "pre_activation_counts": bundle["expected_counts"]["before"],
    }
    for key, value in expected.items():
        if proof.get(key) != value:
            raise StoreSafetyError(f"backup proof mismatch: {key}")
    snapshot_sha = proof.get("snapshot_sha256")
    if not isinstance(snapshot_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", snapshot_sha):
        raise StoreSafetyError("backup proof lacks an exact snapshot digest")
    return {key: proof[key] for key in (*expected, "snapshot_sha256")}


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
    row = _row_for_selector(conn)
    scopes: dict[str, str] = {}
    for scope in ("119", "all", "118"):
        response = select_public_presentations(
            [row],
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
        [row],
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
        "selector_rows": len(
            EditorialArtifactRepository(conn).publication_selector()
        ),
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
        "rows_inserted": 6,
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
        choices=("verify-bundle", "preflight", "apply", "postcheck", "rollback"),
    )
    parser.add_argument("--database-url")
    parser.add_argument("--target", choices=("disposable", "production"), default="disposable")
    parser.add_argument("--bundle-id", default=BUNDLE_ID)
    parser.add_argument("--bundle-sha256")
    parser.add_argument("--deployed-commit")
    parser.add_argument("--required-schema", default="0016")
    parser.add_argument("--backup-proof", type=Path)
    parser.add_argument("--confirm-production-activation", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    parser.add_argument("--confirm-batch-id", type=int)
    parser.add_argument("--confirm-artifact-ids")
    parser.add_argument("--api-base-url")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    bundle = load_activation_bundle()
    if args.required_schema != "0016":
        raise StoreSafetyError("deployed schema expectation must be exactly migration 0016")
    if args.bundle_id != BUNDLE_ID:
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
    db_url = args.database_url or os.getenv("EDITORIAL_DISPOSABLE_DATABASE_URL")
    if args.target == "production":
        db_url = args.database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise StoreSafetyError("an explicit database URL is required")
    result["target"] = target_info(db_url, args.target, None)
    if args.mode in {"apply", "rollback"}:
        if not args.bundle_sha256:
            raise StoreSafetyError("write modes require the exact bundle digest")
        if not args.deployed_commit:
            raise StoreSafetyError("write modes require the deployed commit")
        result["deployment"] = _exact_deployed_commit(args.deployed_commit)
        if not args.backup_proof:
            raise StoreSafetyError("write modes require a validated backup proof")
        result["backup"] = _verify_backup_proof(args.backup_proof, bundle)
    if args.target == "production" and args.mode == "apply":
        if not args.confirm_production_activation:
            raise StoreSafetyError("production activation lacks explicit confirmation")
    if args.target == "production" and args.mode == "rollback":
        if not args.confirm_production_rollback:
            raise StoreSafetyError("production rollback lacks explicit confirmation")
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
            elif args.mode == "apply":
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
