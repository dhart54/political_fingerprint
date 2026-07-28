from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import uvicorn

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts import foushee_justice_publication_activation as activation
from scripts.editorial_artifact_store import StoreSafetyError, _connect, target_info


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_cli(arguments: list[str]) -> dict[str, Any]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        status = activation.main(arguments)
    if status != 0:
        raise StoreSafetyError(f"activation CLI returned status {status}")
    return json.loads(output.getvalue())


def _wait_for_server(base_url: str, server: uvicorn.Server) -> dict[str, Any]:
    for _ in range(200):
        if server.should_exit:
            break
        try:
            with urlopen(f"{base_url}/health", timeout=1) as response:
                return json.load(response)
        except OSError:
            time.sleep(0.05)
    raise StoreSafetyError("local HTTP proof server did not become ready")


def _activation_present(database_url: str) -> bool:
    with _connect(database_url, autocommit=True) as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS n
               FROM editorial_artifact_batches
               WHERE deterministic_batch_key = %s""",
            (activation.BATCH_KEY,),
        ).fetchone()
    count = int(row["n"])
    if count not in {0, 1}:
        raise StoreSafetyError("disposable activation batch identity is ambiguous")
    return count == 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Foushee activation through a real local HTTP server and "
            "always restore the exact governed disposable baseline"
        )
    )
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--deployed-commit", required=True)
    parser.add_argument("--preflight-report", required=True, type=Path)
    parser.add_argument("--backup-proof", required=True, type=Path)
    parser.add_argument("--report-path", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8012, type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.host not in {"127.0.0.1", "localhost"}:
        raise StoreSafetyError("HTTP proof server must bind to loopback")
    target = target_info(args.database_url, "disposable", None)
    if target["host"] not in {
        "127.0.0.1",
        "localhost",
    }:
        raise StoreSafetyError("HTTP proof requires a loopback disposable database")
    activation._exact_deployed_commit(args.deployed_commit)
    base_url = f"http://{args.host}:{args.port}"
    old_database_url = os.environ.get("DATABASE_URL")
    old_source_commit = os.environ.get("SOURCE_COMMIT_SHA")
    os.environ["DATABASE_URL"] = args.database_url
    os.environ["SOURCE_COMMIT_SHA"] = args.deployed_commit
    config = uvicorn.Config(
        "app.main:app",
        host=args.host,
        port=args.port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    apply_attempted = False
    postcheck: dict[str, Any] | None = None
    report: dict[str, Any] = {
        "schema_version": "foushee_publication_http_integration_proof_v1",
        "created_at_utc": _utc_now(),
        "bundle_id": activation.BUNDLE_ID,
        "bundle_sha256": activation.load_activation_bundle()["bundle_sha256"],
        "deployed_commit": args.deployed_commit,
        "database_target": {
            "target": "disposable",
            "host": target["host"],
            "port": target["port"],
            "database": target["database"],
            "raw_url_recorded": False,
        },
    }
    thread.start()
    try:
        health = _wait_for_server(base_url, server)
        if health.get("commit_sha") != args.deployed_commit:
            raise StoreSafetyError("local HTTP health commit mismatch")
        report["health"] = health
        report["before_http"] = activation._api_receipts_only_smoke(base_url)
        apply_attempted = True
        apply_result = _run_cli(
            [
                "apply",
                "--database-url",
                args.database_url,
                "--target",
                "disposable",
                "--bundle-id",
                activation.BUNDLE_ID,
                "--confirm-bundle-digest",
                report["bundle_sha256"],
                "--deployed-commit",
                args.deployed_commit,
                "--preflight-report",
                str(args.preflight_report),
                "--backup-proof",
                str(args.backup_proof),
                "--api-base-url",
                base_url,
            ]
        )
        applied_postcheck = apply_result["application"]["postcheck"]
        report["apply"] = {
            "counts": applied_postcheck["counts"],
            "batch_id": applied_postcheck["batch_id"],
            "artifact_ids": applied_postcheck["artifact_ids"],
        }
        report["activated_http"] = apply_result["api_smoke"]
        postcheck = _run_cli(
            [
                "postcheck",
                "--database-url",
                args.database_url,
                "--target",
                "disposable",
                "--bundle-id",
                activation.BUNDLE_ID,
                "--deployed-commit",
                args.deployed_commit,
            ]
        )["postcheck"]
    finally:
        try:
            if apply_attempted and _activation_present(args.database_url):
                if postcheck is None:
                    postcheck = _run_cli(
                        [
                            "postcheck",
                            "--database-url",
                            args.database_url,
                            "--target",
                            "disposable",
                            "--bundle-id",
                            activation.BUNDLE_ID,
                            "--deployed-commit",
                            args.deployed_commit,
                        ]
                    )["postcheck"]
                rollback = _run_cli(
                    [
                        "rollback",
                        "--database-url",
                        args.database_url,
                        "--target",
                        "disposable",
                        "--bundle-id",
                        activation.BUNDLE_ID,
                        "--confirm-bundle-digest",
                        report["bundle_sha256"],
                        "--confirm-rollback-token",
                        (
                            f"ROLLBACK:{activation.BUNDLE_ID}:"
                            f"{report['bundle_sha256']}"
                        ),
                        "--confirm-batch-id",
                        str(postcheck["batch_id"]),
                        "--confirm-artifact-ids",
                        ",".join(str(item) for item in postcheck["artifact_ids"]),
                    ]
                )["rollback"]
                report["rollback"] = {
                    "counts": rollback["counts"],
                    "removed_batch_id": rollback["removed_batch_id"],
                    "target_absent": rollback["target_absent"],
                    "fingerprint_sha256": rollback["governed_baseline"][
                        "reconciled_fingerprint"
                    ]["sha256"],
                }
                report["after_http"] = activation._api_receipts_only_smoke(
                    base_url
                )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            if old_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old_database_url
            if old_source_commit is None:
                os.environ.pop("SOURCE_COMMIT_SHA", None)
            else:
                os.environ["SOURCE_COMMIT_SHA"] = old_source_commit
            if thread.is_alive():
                raise StoreSafetyError("local HTTP proof server did not stop")
    required_counts = {
        "batches": 2,
        "artifacts": 140,
        "relationships": 155,
        "publication_registry": 0,
    }
    if (
        report.get("apply", {}).get("counts")
        != {
            "batches": 3,
            "artifacts": 143,
            "relationships": 157,
            "publication_registry": 1,
        }
        or report.get("rollback", {}).get("counts") != required_counts
        or report.get("rollback", {}).get("fingerprint_sha256")
        != "3328dd38b4483f651a8459adec9b1d4ed2cfb8baa61ad413a282d3617d726b18"
    ):
        raise StoreSafetyError("HTTP proof did not restore the exact governed baseline")
    report["status"] = "passed"
    report["report_sha256"] = activation.semantic_hash(report)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StoreSafetyError, ValueError) as exc:
        print(
            json.dumps({"status": "blocked", "error": str(exc)}, indent=2),
            file=sys.stderr,
        )
        raise SystemExit(2)
