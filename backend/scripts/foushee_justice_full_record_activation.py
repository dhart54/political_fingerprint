"""Bounded M10-R1 full-record publication activation preparation operator.

The default path is read-only.  Write modes require an exact content-bound
bundle and explicit confirmation, and are intended for disposable proof until a
separate user authorization permits production activation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import semantic_hash  # noqa: E402
from app.editorial_presentations.compiler import artifact_digest  # noqa: E402
from app.editorial_presentations.selector import (  # noqa: E402
    select_public_presentations,
)
from scripts.editorial_artifact_store import (  # noqa: E402
    StoreSafetyError,
    _connect,
    target_info,
)


BUNDLE_ID = "foushee_justice_public_safety_119_full_record_activation_v1"
MEMBER_ID = "F000477"
ISSUE_ID = "JUSTICE_PUBLIC_SAFETY"
TARGET_DIR = (
    ROOT
    / "docs/editorial/full_record_reviews/publication_preparations"
    / "f000477_justice_public_safety_119_v1"
)
PRESENTATION_PATH = TARGET_DIR / "approved_public_presentation_projection.json"
APPROVAL_PATH = TARGET_DIR / "full_record_publication_approval_projection.json"
RESOLUTION_PATH = TARGET_DIR / "semantic_review_exception_resolution.json"
REVIEW_STATE_PATH = TARGET_DIR / "public_review_state_projection.json"
LEDGER_PATH = TARGET_DIR / "routing_trigger_ledger.json"
PRESENTATION_KEY = (
    "public-issue-presentation-candidate:f000477:justice_public_safety:119:v1"
)
SOURCE_KEY = f"{PRESENTATION_KEY}:publication-source-manifest"
VALIDATION_KEY = f"{PRESENTATION_KEY}:publication-validation"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
LOCK_KEY = f"political_fingerprint:{BUNDLE_ID}"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StoreSafetyError(f"expected JSON object: {path.name}")
    return value


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str, sort_keys=True))


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _counts(conn: Any) -> dict[str, int]:
    tables = {
        "batches": "editorial_artifact_batches",
        "artifacts": "editorial_artifact_versions",
        "relationships": "editorial_artifact_relationships",
        "publication_registry": "editorial_publication_registry",
    }
    return {
        key: int(conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])
        for key, table in tables.items()
    }


def _state_fingerprint(conn: Any) -> str:
    queries = (
        """SELECT deterministic_batch_key,source_commit_sha,manifest_sha256,status,
                  artifact_count,relationship_count
             FROM editorial_artifact_batches ORDER BY deterministic_batch_key""",
        """SELECT artifact_type,natural_key,schema_version,artifact_version,
                  content_sha256,source_manifest_sha256,source_commit_sha,batch_id,
                  member_bioguide_id,issue_id,congress,chamber,canonical_action_id,
                  episode_id,policy_family_id,editorial_status,benchmark_status,
                  production_eligible,review_route
             FROM editorial_artifact_versions
             ORDER BY natural_key,artifact_version,content_sha256""",
        """SELECT parent.natural_key AS parent_natural_key,
                  child.natural_key AS child_natural_key,relationship_type,ordinal,
                  metadata_jsonb
             FROM editorial_artifact_relationships rel
             JOIN editorial_artifact_versions parent
               ON parent.artifact_id=rel.parent_artifact_id
             JOIN editorial_artifact_versions child
               ON child.artifact_id=rel.child_artifact_id
             ORDER BY parent.natural_key,relationship_type,ordinal,child.natural_key""",
        """SELECT member_bioguide_id,issue_id,artifact.natural_key,
                  artifact.artifact_version,registry.publicly_active,
                  registry.publication_metadata_jsonb
             FROM editorial_publication_registry registry
             JOIN editorial_artifact_versions artifact
               ON artifact.artifact_id=registry.artifact_id
             ORDER BY member_bioguide_id,issue_id""",
    )
    return semantic_hash(
        [
            [_jsonable(dict(row)) for row in conn.execute(query).fetchall()]
            for query in queries
        ]
    )


def _registry_row(conn: Any) -> dict[str, Any] | None:
    row = conn.execute(
        """SELECT registry.artifact_id,registry.publicly_active,
                  registry.publication_metadata_jsonb,artifact.natural_key,
                  artifact.artifact_version,artifact.content_sha256,
                  artifact.payload_jsonb
             FROM editorial_publication_registry registry
             JOIN editorial_artifact_versions artifact
               ON artifact.artifact_id=registry.artifact_id
            WHERE registry.member_bioguide_id=%s AND registry.issue_id=%s""",
        (MEMBER_ID, ISSUE_ID),
    ).fetchone()
    return _jsonable(dict(row)) if row else None


def _target_rows(conn: Any) -> list[dict[str, Any]]:
    return [
        _jsonable(dict(row))
        for row in conn.execute(
            """SELECT artifact_id,natural_key,artifact_version,content_sha256
                 FROM editorial_artifact_versions
                WHERE natural_key=ANY(%s)
                ORDER BY natural_key,artifact_version""",
            ([PRESENTATION_KEY, SOURCE_KEY, VALIDATION_KEY],),
        ).fetchall()
    ]


def _selector(conn: Any) -> dict[str, Any]:
    from app.editorial_artifacts.repository import EditorialArtifactRepository

    rows = EditorialArtifactRepository(conn).publication_selector()
    scopes: dict[str, dict[str, Any]] = {}
    for scope in ("119", "all", "118"):
        response = select_public_presentations(
            rows,
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id=MEMBER_ID,
            scope=scope,
        )
        justice = next(
            item for item in response["presentations"] if item["issue_id"] == ISSUE_ID
        )
        scopes[scope] = {
            "tier": justice["tier"],
            "receipt_count": len(justice.get("exact_action_receipts", [])),
            "review_scope": (justice.get("review_state") or {}).get("review_scope"),
        }
    return {"selector_rows": len(rows), "scopes": scopes}


def preflight(conn: Any, deployed_commit: str) -> dict[str, Any]:
    if not SHA40.fullmatch(deployed_commit):
        raise StoreSafetyError("deployed commit must be an exact lowercase SHA-40")
    counts = _counts(conn)
    if counts != {
        "batches": 3,
        "artifacts": 143,
        "relationships": 157,
        "publication_registry": 1,
    }:
        raise StoreSafetyError(f"unexpected pre-activation counts: {counts}")
    predecessor = _registry_row(conn)
    if (
        predecessor is None
        or predecessor["natural_key"] != "f000477:justice_public_safety:119:v1"
        or predecessor["artifact_version"] != 1
        or predecessor["content_sha256"]
        != "fd7a8b5e440654147bbb6b738be3bb683034f07b0c9cc4e26eba9cce84e07e59"
        or predecessor["publicly_active"] is not True
    ):
        raise StoreSafetyError("compact predecessor identity is not exact and active")
    targets = _target_rows(conn)
    if targets:
        raise StoreSafetyError("full-record activation target already exists")
    selector = _selector(conn)
    if selector["scopes"]["119"]["tier"] != "reviewed_conclusion":
        raise StoreSafetyError("compact predecessor selector is not reviewed")
    body = {
        "schema_version": "foushee_justice_full_record_preflight_v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "deployed_commit": deployed_commit,
        "read_only": True,
        "counts": counts,
        "state_fingerprint_sha256": _state_fingerprint(conn),
        "predecessor": predecessor,
        "target_rows": targets,
        "selector": selector,
    }
    body["preflight_sha256"] = semantic_hash(body)
    return body


def _file_record(path: Path) -> dict[str, Any]:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "size": len(path.read_bytes()),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _artifact(
    artifact_type: str,
    natural_key: str,
    payload: dict[str, Any],
    *,
    source_commit: str,
    source_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload["schema_version"],
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": source_manifest_sha256,
        "source_commit_sha": source_commit,
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "chamber": "house",
        "canonical_action_id": None,
        "episode_id": None,
        "policy_family_id": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "review_route": "human_exception",
    }


def build_bundle(
    preflight_report: dict[str, Any], deployed_commit: str
) -> dict[str, Any]:
    if preflight_report.get("deployed_commit") != deployed_commit:
        raise StoreSafetyError("preflight deployed-commit binding mismatch")
    claimed = preflight_report.get("preflight_sha256")
    check = copy.deepcopy(preflight_report)
    check.pop("preflight_sha256", None)
    if claimed != semantic_hash(check):
        raise StoreSafetyError("preflight digest mismatch")
    presentation = _load(PRESENTATION_PATH)
    approval = _load(APPROVAL_PATH)
    resolution = _load(RESOLUTION_PATH)
    review_state = _load(REVIEW_STATE_PATH)
    source_files = [
        _file_record(path)
        for path in (
            PRESENTATION_PATH,
            APPROVAL_PATH,
            RESOLUTION_PATH,
            REVIEW_STATE_PATH,
            LEDGER_PATH,
        )
    ]
    source_manifest_sha256 = semantic_hash(source_files)
    source_payload = {
        "schema_version": "editorial_publication_source_manifest_v1",
        "activation_bundle_id": BUNDLE_ID,
        "complete_required_sources": True,
        "source_files": source_files,
    }
    validation_payload = {
        "schema_version": "editorial_publication_validation_v1",
        "activation_bundle_id": BUNDLE_ID,
        "successful": True,
        "current": True,
        "blocking_findings": 0,
        "semantic_tier": "reviewed_conclusion",
        "accepted_substantive_actions": 35,
        "noncounting_controls": 2,
        "deployed_commit": deployed_commit,
    }
    artifacts = [
        _artifact(
            "issue_public_presentation",
            PRESENTATION_KEY,
            presentation,
            source_commit=deployed_commit,
            source_manifest_sha256=source_manifest_sha256,
        ),
        _artifact(
            "source_manifest",
            SOURCE_KEY,
            source_payload,
            source_commit=deployed_commit,
            source_manifest_sha256=source_manifest_sha256,
        ),
        _artifact(
            "standardization_validation_result",
            VALIDATION_KEY,
            validation_payload,
            source_commit=deployed_commit,
            source_manifest_sha256=source_manifest_sha256,
        ),
    ]
    artifacts.sort(key=lambda item: item["natural_key"])
    relationships = [
        {
            "parent_natural_key": PRESENTATION_KEY,
            "child_natural_key": SOURCE_KEY,
            "relationship_type": "uses_source_manifest",
            "ordinal": 0,
            "metadata": {"activation_bundle_id": BUNDLE_ID},
        },
        {
            "parent_natural_key": PRESENTATION_KEY,
            "child_natural_key": VALIDATION_KEY,
            "relationship_type": "has_validation",
            "ordinal": 0,
            "metadata": {"activation_bundle_id": BUNDLE_ID},
        },
    ]
    relationships.sort(key=lambda item: item["relationship_type"])
    metadata = {
        "activation_bundle_id": BUNDLE_ID,
        "approval_receipt": approval,
        "semantic_review_exception_resolution": resolution,
        "approval_subject_sha256": approval["binding"]["approval_subject_sha256"],
        "active_artifact_sha256": artifact_digest(presentation),
        "presentation_natural_key": PRESENTATION_KEY,
        "presentation_artifact_version": 1,
        "validation_natural_key": VALIDATION_KEY,
        "validation_artifact_version": 1,
        "validation_content_sha256": next(
            item["content_sha256"]
            for item in artifacts
            if item["natural_key"] == VALIDATION_KEY
        ),
        "source_manifest_natural_key": SOURCE_KEY,
        "source_manifest_artifact_version": 1,
        "source_manifest_content_sha256": next(
            item["content_sha256"]
            for item in artifacts
            if item["natural_key"] == SOURCE_KEY
        ),
        "relationship_metadata": {"activation_bundle_id": BUNDLE_ID},
    }
    body = {
        "schema_version": "foushee_justice_full_record_activation_bundle_v1",
        "bundle_id": BUNDLE_ID,
        "deterministic_batch_key": f"{BUNDLE_ID}-{deployed_commit[:8]}",
        "source_commit_sha": deployed_commit,
        "preflight_binding": {
            "preflight_sha256": claimed,
            "state_fingerprint_sha256": preflight_report["state_fingerprint_sha256"],
        },
        "predecessor": preflight_report["predecessor"],
        "artifacts": artifacts,
        "relationships": relationships,
        "publication_registry": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "presentation_natural_key": PRESENTATION_KEY,
            "publication_metadata": metadata,
        },
        "review_state_projection": review_state,
        "expected_counts": {
            "before": preflight_report["counts"],
            "after": {
                "batches": 4,
                "artifacts": 146,
                "relationships": 159,
                "publication_registry": 1,
            },
        },
        "write_caps": {
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 0,
            "registry_updates": 1,
            "deletes_during_activation": 0,
        },
        "public_smoke_contract": {
            "119": {"tier": "reviewed_conclusion", "receipt_count": 35},
            "all": {"tier": "reviewed_conclusion", "receipt_count": 35},
            "118": {"tier": "receipts_only", "receipt_count": 0},
        },
        "rollback": {
            "restore_predecessor_artifact_id": preflight_report["predecessor"][
                "artifact_id"
            ],
            "restore_predecessor_metadata": preflight_report["predecessor"][
                "publication_metadata_jsonb"
            ],
            "restore_fingerprint_sha256": preflight_report["state_fingerprint_sha256"],
        },
    }
    body["bundle_sha256"] = semantic_hash(body)
    validate_bundle(body)
    return body


def validate_bundle(bundle: dict[str, Any]) -> None:
    claimed = bundle.get("bundle_sha256")
    body = copy.deepcopy(bundle)
    body.pop("bundle_sha256", None)
    if claimed != semantic_hash(body):
        raise StoreSafetyError("activation bundle digest mismatch")
    if (
        bundle.get("schema_version")
        != "foushee_justice_full_record_activation_bundle_v1"
        or bundle.get("bundle_id") != BUNDLE_ID
        or not SHA40.fullmatch(bundle.get("source_commit_sha", ""))
        or bundle.get("write_caps")
        != {
            "batch_inserts": 1,
            "artifact_inserts": 3,
            "relationship_inserts": 2,
            "registry_inserts": 0,
            "registry_updates": 1,
            "deletes_during_activation": 0,
        }
    ):
        raise StoreSafetyError("activation bundle identity or cap mismatch")
    if len(bundle["artifacts"]) != 3 or len(bundle["relationships"]) != 2:
        raise StoreSafetyError("activation graph size mismatch")
    for artifact in bundle["artifacts"]:
        if artifact["content_sha256"] != semantic_hash(artifact["payload"]):
            raise StoreSafetyError("activation artifact digest mismatch")


def _assert_bound_preflight(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    actual = preflight(conn, bundle["source_commit_sha"])
    if (
        actual["state_fingerprint_sha256"]
        != bundle["preflight_binding"]["state_fingerprint_sha256"]
    ):
        raise StoreSafetyError("database state drifted from bundle preflight")
    return actual


def _postcheck(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    if _counts(conn) != bundle["expected_counts"]["after"]:
        raise StoreSafetyError("post-activation count mismatch")
    registry = _registry_row(conn)
    if (
        registry is None
        or registry["natural_key"] != PRESENTATION_KEY
        or registry["publication_metadata_jsonb"]
        != bundle["publication_registry"]["publication_metadata"]
    ):
        raise StoreSafetyError("post-activation registry identity mismatch")
    selector = _selector(conn)
    if selector["scopes"] != bundle["public_smoke_contract"]:
        raise StoreSafetyError(f"public selector mismatch: {selector['scopes']}")
    return {"counts": _counts(conn), "registry": registry, "selector": selector}


def _apply(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    if _counts(conn) == bundle["expected_counts"]["after"]:
        return {"already_applied": True, "postcheck": _postcheck(conn, bundle)}
    bound = _assert_bound_preflight(conn, bundle)
    batch = conn.execute(
        """INSERT INTO editorial_artifact_batches
           (deterministic_batch_key,source_commit_sha,manifest_sha256,status,
            artifact_count,relationship_count,applied_at)
           VALUES (%s,%s,%s,'applied',3,2,NOW()) RETURNING batch_id""",
        (
            bundle["deterministic_batch_key"],
            bundle["source_commit_sha"],
            bundle["bundle_sha256"],
        ),
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
                item["artifact_type"],
                item["natural_key"],
                item["schema_version"],
                item["artifact_version"],
                Jsonb(item["payload"]),
                item["content_sha256"],
                item["source_manifest_sha256"],
                item["source_commit_sha"],
                batch_id,
                item["member_bioguide_id"],
                item["issue_id"],
                item["congress"],
                item["chamber"],
                item["canonical_action_id"],
                item["episode_id"],
                item["policy_family_id"],
                item["editorial_status"],
                item["benchmark_status"],
                item["production_eligible"],
                item["review_route"],
            ),
        ).fetchone()
        ids[item["natural_key"]] = int(row["artifact_id"])
    for relation in bundle["relationships"]:
        conn.execute(
            """INSERT INTO editorial_artifact_relationships
               (parent_artifact_id,child_artifact_id,relationship_type,ordinal,metadata_jsonb)
               VALUES (%s,%s,%s,%s,%s)""",
            (
                ids[relation["parent_natural_key"]],
                ids[relation["child_natural_key"]],
                relation["relationship_type"],
                relation["ordinal"],
                Jsonb(relation["metadata"]),
            ),
        )
    updated = conn.execute(
        """UPDATE editorial_publication_registry
              SET artifact_id=%s,publicly_active=TRUE,activated_at=NOW(),
                  deactivated_at=NULL,publication_metadata_jsonb=%s
            WHERE member_bioguide_id=%s AND issue_id=%s""",
        (
            ids[PRESENTATION_KEY],
            Jsonb(bundle["publication_registry"]["publication_metadata"]),
            MEMBER_ID,
            ISSUE_ID,
        ),
    )
    if updated.rowcount != 1:
        raise StoreSafetyError("activation registry update count mismatch")
    return {
        "already_applied": False,
        "batch_id": batch_id,
        "artifact_ids": sorted(ids.values()),
        "preflight": bound,
        "postcheck": _postcheck(conn, bundle),
    }


def _rollback(conn: Any, bundle: dict[str, Any]) -> dict[str, Any]:
    from psycopg.types.json import Jsonb

    post = _postcheck(conn, bundle)
    batch = conn.execute(
        "SELECT batch_id FROM editorial_artifact_batches WHERE deterministic_batch_key=%s",
        (bundle["deterministic_batch_key"],),
    ).fetchone()
    if batch is None:
        raise StoreSafetyError("rollback batch is absent")
    batch_id = int(batch["batch_id"])
    restored = conn.execute(
        """UPDATE editorial_publication_registry
              SET artifact_id=%s,publicly_active=TRUE,activated_at=NOW(),
                  deactivated_at=NULL,publication_metadata_jsonb=%s
            WHERE member_bioguide_id=%s AND issue_id=%s""",
        (
            bundle["rollback"]["restore_predecessor_artifact_id"],
            Jsonb(bundle["rollback"]["restore_predecessor_metadata"]),
            MEMBER_ID,
            ISSUE_ID,
        ),
    )
    deleted_relationships = conn.execute(
        """DELETE FROM editorial_artifact_relationships rel
            USING editorial_artifact_versions parent
            WHERE rel.parent_artifact_id=parent.artifact_id AND parent.batch_id=%s""",
        (batch_id,),
    )
    conn.execute(
        "SELECT set_config('app.editorial_artifact_rollback_batch',%s,true)",
        (bundle["deterministic_batch_key"],),
    )
    deleted_artifacts = conn.execute(
        "DELETE FROM editorial_artifact_versions WHERE batch_id=%s", (batch_id,)
    )
    deleted_batch = conn.execute(
        "DELETE FROM editorial_artifact_batches WHERE batch_id=%s", (batch_id,)
    )
    if (
        restored.rowcount,
        deleted_relationships.rowcount,
        deleted_artifacts.rowcount,
        deleted_batch.rowcount,
    ) != (1, 2, 3, 1):
        raise StoreSafetyError("rollback write-count mismatch")
    if _counts(conn) != bundle["expected_counts"]["before"]:
        raise StoreSafetyError("rollback count restoration mismatch")
    fingerprint = _state_fingerprint(conn)
    if fingerprint != bundle["rollback"]["restore_fingerprint_sha256"]:
        raise StoreSafetyError("rollback exact-state fingerprint mismatch")
    return {
        "before": post,
        "counts": _counts(conn),
        "state_fingerprint_sha256": fingerprint,
        "selector": _selector(conn),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "preflight",
            "build-bundle",
            "dry-run",
            "apply",
            "postcheck",
            "rollback",
        ),
    )
    parser.add_argument("--database-url")
    parser.add_argument(
        "--target", choices=("disposable", "production"), default="disposable"
    )
    parser.add_argument("--deployed-commit")
    parser.add_argument("--report-path", type=Path)
    parser.add_argument("--preflight-report", type=Path)
    parser.add_argument("--bundle-path", type=Path)
    parser.add_argument("--confirm-bundle-digest")
    parser.add_argument("--confirm-production-activation", action="store_true")
    parser.add_argument("--confirm-production-rollback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "build-bundle":
        if (
            not args.preflight_report
            or not args.bundle_path
            or not args.deployed_commit
        ):
            raise StoreSafetyError(
                "build-bundle requires preflight, output, and deployed commit"
            )
        bundle = build_bundle(_load(args.preflight_report), args.deployed_commit)
        _write(args.bundle_path, bundle)
        print(
            json.dumps(
                {
                    "bundle_id": BUNDLE_ID,
                    "bundle_sha256": bundle["bundle_sha256"],
                    "path": str(args.bundle_path.resolve()),
                },
                indent=2,
            )
        )
        return 0
    db_url = args.database_url or (
        os.getenv("DATABASE_URL")
        if args.target == "production"
        else os.getenv("EDITORIAL_DISPOSABLE_DATABASE_URL")
    )
    if not db_url:
        raise StoreSafetyError("an explicit database URL is required")
    target_info(db_url, args.target, None)
    if args.mode == "preflight":
        if not args.deployed_commit:
            raise StoreSafetyError("preflight requires deployed commit")
        with _connect(db_url, autocommit=True) as conn:
            conn.execute("SET default_transaction_read_only=on")
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                result = preflight(conn, args.deployed_commit)
        if args.report_path:
            _write(args.report_path, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if not args.bundle_path:
        raise StoreSafetyError("write and postcheck modes require --bundle-path")
    bundle = _load(args.bundle_path)
    validate_bundle(bundle)
    if (
        args.mode in {"dry-run", "apply", "rollback"}
        and args.confirm_bundle_digest != bundle["bundle_sha256"]
    ):
        raise StoreSafetyError("write mode requires exact bundle digest confirmation")
    if (
        args.target == "production"
        and args.mode in {"dry-run", "apply"}
        and not args.confirm_production_activation
    ):
        raise StoreSafetyError(
            "production activation lacks explicit authorization flag"
        )
    if (
        args.target == "production"
        and args.mode == "rollback"
        and not args.confirm_production_rollback
    ):
        raise StoreSafetyError("production rollback lacks explicit authorization flag")
    read_only = args.mode == "postcheck"
    with _connect(db_url, autocommit=read_only) as conn:
        if read_only:
            conn.execute("SET default_transaction_read_only=on")
        with conn.transaction(force_rollback=args.mode == "dry-run"):
            conn.execute("SET LOCAL lock_timeout='10000ms'")
            conn.execute("SET LOCAL statement_timeout='120000ms'")
            if not read_only:
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,))
            if args.mode in {"dry-run", "apply"}:
                result = _apply(conn, bundle)
            elif args.mode == "postcheck":
                result = _postcheck(conn, bundle)
            else:
                result = _rollback(conn, bundle)
    print(
        json.dumps(
            {
                "mode": args.mode,
                "bundle_sha256": bundle["bundle_sha256"],
                "result": result,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StoreSafetyError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
