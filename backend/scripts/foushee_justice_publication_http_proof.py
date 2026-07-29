from __future__ import annotations

import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import urlopen

import uvicorn

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts import foushee_justice_publication_activation as activation
from scripts.editorial_artifact_store import StoreSafetyError, _connect, target_info

POSTGRES_IMAGE = "supabase/postgres:17.6.1.156"
BASELINE_COUNTS = {
    "batches": 2,
    "artifacts": 140,
    "relationships": 155,
    "publication_registry": 0,
}
ACTIVATED_COUNTS = {
    "batches": 3,
    "artifacts": 143,
    "relationships": 157,
    "publication_registry": 1,
}
BASELINE_FINGERPRINT = (
    "3328dd38b4483f651a8459adec9b1d4ed2cfb8baa61ad413a282d3617d726b18"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _checkpoint(_stage: str) -> None:
    """Fault-injection seam used only by lifecycle containment tests."""


def _docker(arguments: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["docker", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise StoreSafetyError(f"disposable Docker command failed: {detail}")
    return result


class OwnedDockerPostgres:
    """One proof run's uniquely named and labeled disposable PostgreSQL."""

    def __init__(self, image: str = POSTGRES_IMAGE):
        self.run_id = uuid.uuid4().hex
        suffix = self.run_id[:12]
        self.container = f"pf-http-proof-{suffix}"
        self.volume = f"pf-http-proof-data-{suffix}"
        self.network = f"pf-http-proof-net-{suffix}"
        self.label = f"political-fingerprint.http-proof-run={self.run_id}"
        self.image = image
        self.password = secrets.token_urlsafe(32)
        self.database = "political_fingerprint_http_proof"
        self.database_url = ""
        self._created = {"container": False, "volume": False, "network": False}

    def _refuse_existing_name(self, kind: str, name: str) -> None:
        command = {
            "container": ["container", "inspect", name],
            "volume": ["volume", "inspect", name],
            "network": ["network", "inspect", name],
        }[kind]
        if _docker(command, check=False).returncode == 0:
            raise StoreSafetyError(
                f"refusing to reuse existing disposable {kind} {name}"
            )

    def create(self) -> None:
        for kind, name in (
            ("container", self.container),
            ("volume", self.volume),
            ("network", self.network),
        ):
            self._refuse_existing_name(kind, name)
        _docker(["network", "create", "--label", self.label, self.network])
        self._created["network"] = True
        _docker(["volume", "create", "--label", self.label, self.volume])
        self._created["volume"] = True
        _docker(
            [
                "run",
                "-d",
                "--name",
                self.container,
                "--label",
                self.label,
                "--network",
                self.network,
                "--mount",
                f"source={self.volume},target=/var/lib/postgresql/data",
                "-p",
                "127.0.0.1::5432",
                "-e",
                f"POSTGRES_PASSWORD={self.password}",
                self.image,
            ]
        )
        self._created["container"] = True
        deadline = time.monotonic() + 120
        ready_streak = 0
        while time.monotonic() < deadline:
            ready = _docker(
                [
                    "exec",
                    self.container,
                    "pg_isready",
                    "-U",
                    "supabase_admin",
                    "-d",
                    "postgres",
                ],
                check=False,
            )
            if ready.returncode == 0:
                ready_streak += 1
                if ready_streak >= 20:
                    break
            else:
                ready_streak = 0
            state = _docker(
                ["inspect", "-f", "{{.State.Running}}", self.container],
                check=False,
            )
            if state.returncode == 0 and state.stdout.strip() == "false":
                raise StoreSafetyError("disposable PostgreSQL stopped before readiness")
            time.sleep(0.5)
        else:
            raise StoreSafetyError("disposable PostgreSQL readiness timed out")
        _docker(
            [
                "exec",
                self.container,
                "createdb",
                "-U",
                "supabase_admin",
                "-O",
                "supabase_admin",
                self.database,
            ]
        )
        published = _docker(["port", self.container, "5432/tcp"]).stdout.strip()
        try:
            port = int(published.rsplit(":", 1)[1])
        except (IndexError, ValueError) as exc:
            raise StoreSafetyError("could not resolve disposable loopback port") from exc
        self.database_url = (
            f"postgresql://supabase_admin:{quote(self.password, safe='')}"
            f"@127.0.0.1:{port}/{self.database}"
        )
        target = target_info(self.database_url, "disposable", None)
        if target["host"] != "127.0.0.1":
            raise StoreSafetyError("disposable PostgreSQL is not loopback-bound")

    def restore(self, snapshot: Path) -> None:
        pg_restore = activation._postgres_tool("pg_restore")
        if not pg_restore:
            raise StoreSafetyError("pg_restore is required for the owned HTTP proof")
        restored = subprocess.run(
            [
                pg_restore,
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                self.database_url,
                str(snapshot),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if restored.returncode != 0:
            raise StoreSafetyError(
                "owned disposable snapshot restore failed: "
                f"{restored.stderr.strip() or 'unknown pg_restore error'}"
            )

    def destroy(self) -> dict[str, Any]:
        diagnostics: list[str] = []
        if self._created["container"]:
            result = _docker(["rm", "-f", self.container], check=False)
            if result.returncode != 0:
                diagnostics.append("container removal failed")
        if self._created["volume"]:
            result = _docker(["volume", "rm", "-f", self.volume], check=False)
            if result.returncode != 0:
                diagnostics.append("volume removal failed")
        if self._created["network"]:
            result = _docker(["network", "rm", self.network], check=False)
            if result.returncode != 0:
                diagnostics.append("network removal failed")
        remaining = {
            "containers": _docker(
                ["ps", "-aq", "--filter", f"label={self.label}"], check=False
            ).stdout.split(),
            "volumes": _docker(
                ["volume", "ls", "-q", "--filter", f"label={self.label}"],
                check=False,
            ).stdout.split(),
            "networks": _docker(
                ["network", "ls", "-q", "--filter", f"label={self.label}"],
                check=False,
            ).stdout.split(),
        }
        if any(remaining.values()):
            diagnostics.append("current-run labeled Docker resources remain")
        result = {
            "run_label": self.label,
            "remaining": remaining,
            "verified_absent": not diagnostics,
            "diagnostics": diagnostics,
        }
        if diagnostics:
            raise StoreSafetyError(
                "owned disposable resource teardown failed: "
                + "; ".join(diagnostics)
            )
        return result


class LocalUvicorn:
    def __init__(self, host: str, port: int, database_url: str, deployed_commit: str):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.database_url = database_url
        self.deployed_commit = deployed_commit
        self.server = uvicorn.Server(
            uvicorn.Config(
                "app.main:app",
                host=host,
                port=port,
                log_level="warning",
                access_log=False,
            )
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self._old_database_url: str | None = None
        self._old_source_commit: str | None = None

    def start(self) -> dict[str, Any]:
        self._old_database_url = os.environ.get("DATABASE_URL")
        self._old_source_commit = os.environ.get("SOURCE_COMMIT_SHA")
        os.environ["DATABASE_URL"] = self.database_url
        os.environ["SOURCE_COMMIT_SHA"] = self.deployed_commit
        self.thread.start()
        for _ in range(240):
            if self.server.should_exit:
                break
            try:
                with urlopen(f"{self.base_url}/health", timeout=1) as response:
                    health = json.load(response)
                if health.get("commit_sha") != self.deployed_commit:
                    raise StoreSafetyError("local HTTP health commit mismatch")
                return health
            except OSError:
                time.sleep(0.05)
        raise StoreSafetyError("local HTTP proof server did not become ready")

    def stop(self) -> None:
        self.server.should_exit = True
        if self.thread.ident is not None:
            self.thread.join(timeout=10)
        if self._old_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._old_database_url
        if self._old_source_commit is None:
            os.environ.pop("SOURCE_COMMIT_SHA", None)
        else:
            os.environ["SOURCE_COMMIT_SHA"] = self._old_source_commit
        if self.thread.is_alive():
            raise StoreSafetyError("local HTTP proof server did not stop")


def _restored_preflight(database_url: str, bundle: dict[str, Any]) -> dict[str, Any]:
    with _connect(database_url, autocommit=True) as connection:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            return activation._preflight(connection, bundle)


def _apply_exact(database_url: str, bundle: dict[str, Any]) -> dict[str, Any]:
    with _connect(database_url, autocommit=False) as connection:
        with connection.transaction():
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (activation.LOCK_KEY,)
            )
            result = activation._apply(connection, bundle)
    if result["already_applied"] or result["rows_inserted"] != 7:
        raise StoreSafetyError("owned proof activation was not the exact seven-row apply")
    return result


def _postcheck_exact(database_url: str, bundle: dict[str, Any]) -> dict[str, Any]:
    with _connect(database_url, autocommit=True) as connection:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            return activation._postcheck(connection, bundle)


def _rollback_captured(
    database_url: str,
    bundle: dict[str, Any],
    identity: dict[str, Any],
) -> dict[str, Any]:
    with _connect(database_url, autocommit=False) as connection:
        with connection.transaction():
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (activation.LOCK_KEY,)
            )
            return activation._rollback(
                connection, bundle, expected_identity=identity
            )


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the authoritative real-Uvicorn proof in a lifecycle-owned "
            "disposable PostgreSQL environment"
        )
    )
    parser.add_argument("--deployed-commit", required=True)
    parser.add_argument("--preflight-report", required=True, type=Path)
    parser.add_argument("--backup-proof", required=True, type=Path)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--postgres-image", default=POSTGRES_IMAGE)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8012, type=int)
    return parser


def _run_owned_proof(
    args: argparse.Namespace,
    *,
    lifecycle_factory: Callable[[str], OwnedDockerPostgres] = OwnedDockerPostgres,
    server_factory: Callable[[str, int, str, str], LocalUvicorn] = LocalUvicorn,
) -> dict[str, Any]:
    if args.host not in {"127.0.0.1", "localhost"}:
        raise StoreSafetyError("HTTP proof server must bind to loopback")
    activation._exact_deployed_commit(args.deployed_commit)
    bundle = activation.load_activation_bundle()
    if args.bundle_id != activation.BUNDLE_ID:
        raise StoreSafetyError("HTTP proof bundle ID mismatch")
    if (
        args.bundle_sha256 != bundle["bundle_sha256"]
        or args.bundle_sha256
        != "df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813"
    ):
        raise StoreSafetyError("HTTP proof bundle digest mismatch")
    proof_verification = activation._verify_backup_proof(
        args.backup_proof,
        bundle,
        args.deployed_commit,
        args.preflight_report,
    )
    proof = json.loads(args.backup_proof.read_text(encoding="utf-8"))
    snapshot = (args.backup_proof.resolve().parent / proof["snapshot"]["path"]).resolve()
    evidence_dir = args.evidence_dir.resolve()
    report_path = evidence_dir / "http-integration-proof.json"
    lifecycle = lifecycle_factory(args.postgres_image)
    server: LocalUvicorn | None = None
    apply_identity: dict[str, Any] | None = None
    rollback_completed = False
    primary_error: BaseException | None = None
    report: dict[str, Any] = {
        "schema_version": "foushee_publication_http_integration_proof_v2",
        "created_at_utc": _utc_now(),
        "bundle_id": activation.BUNDLE_ID,
        "bundle_sha256": bundle["bundle_sha256"],
        "deployed_commit": args.deployed_commit,
        "authoritative_mode": "owned_disposable_lifecycle",
        "backup_verification": proof_verification,
        "snapshot": {
            "path_recorded": False,
            "sha256": proof["snapshot"]["sha256"],
        },
        "disposable": {
            "image": args.postgres_image,
            "run_label": lifecycle.label,
            "credentials_recorded": False,
        },
    }
    try:
        lifecycle.create()
        lifecycle.restore(snapshot)
        _checkpoint("restore")
        restored = _restored_preflight(lifecycle.database_url, bundle)
        report["restored_preflight"] = {
            "counts": restored["counts"],
            "fingerprint_sha256": restored["governed_baseline"][
                "reconciled_fingerprint"
            ]["sha256"],
        }
        server = server_factory(
            args.host, args.port, lifecycle.database_url, args.deployed_commit
        )
        health = server.start()
        _checkpoint("uvicorn_start")
        report["health"] = health
        report["before_http"] = activation._api_receipts_only_smoke(server.base_url)
        _checkpoint("pre_http")
        _checkpoint("apply")
        apply_result = _apply_exact(lifecycle.database_url, bundle)
        applied = apply_result["postcheck"]
        apply_identity = {
            "batch_id": int(applied["batch_id"]),
            "artifact_ids": [int(item) for item in applied["artifact_ids"]],
            "relationship_identities": bundle["relationships"],
            "registry_target": {
                "member_bioguide_id": activation.MEMBER_ID,
                "issue_id": activation.ISSUE_ID,
            },
            "bundle_id": activation.BUNDLE_ID,
            "bundle_sha256": bundle["bundle_sha256"],
        }
        report["apply_receipt"] = {
            **apply_identity,
            "rows_inserted": 7,
        }
        _checkpoint("postcheck")
        postcheck = _postcheck_exact(lifecycle.database_url, bundle)
        report["postcheck"] = {
            "counts": postcheck["counts"],
            "batch_id": postcheck["batch_id"],
            "artifact_ids": postcheck["artifact_ids"],
        }
        _checkpoint("activated_http")
        report["activated_http"] = activation._api_smoke(server.base_url)
        _checkpoint("rollback_command")
        rollback = _rollback_captured(
            lifecycle.database_url, bundle, apply_identity
        )
        rollback_completed = True
        _checkpoint("rollback_verification")
        report["rollback"] = {
            "counts": rollback["counts"],
            "removed_batch_id": rollback["removed_batch_id"],
            "target_absent": rollback["target_absent"],
            "fingerprint_sha256": rollback["governed_baseline"][
                "reconciled_fingerprint"
            ]["sha256"],
            "verified": True,
        }
        report["after_http"] = activation._api_receipts_only_smoke(server.base_url)
    except BaseException as exc:
        primary_error = exc
        report["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
    finally:
        if server is not None:
            try:
                server.stop()
                report["uvicorn_teardown"] = {"verified_stopped": True}
            except BaseException as exc:
                report["uvicorn_teardown"] = {
                    "verified_stopped": False,
                    "error": str(exc),
                }
                if primary_error is None:
                    primary_error = exc
        if apply_identity is not None and not rollback_completed:
            try:
                rollback = _rollback_captured(
                    lifecycle.database_url, bundle, apply_identity
                )
                rollback_completed = True
                report["failure_rollback"] = {
                    "attempted_from_captured_identity": True,
                    "verified": True,
                    "counts": rollback["counts"],
                    "fingerprint_sha256": rollback["governed_baseline"][
                        "reconciled_fingerprint"
                    ]["sha256"],
                }
            except BaseException as exc:
                report["failure_rollback"] = {
                    "attempted_from_captured_identity": True,
                    "verified": False,
                    "error": str(exc),
                }
                if primary_error is None:
                    primary_error = exc
        try:
            report["resource_teardown"] = lifecycle.destroy()
        except BaseException as exc:
            report["resource_teardown"] = {
                "verified_absent": False,
                "error": str(exc),
            }
            if primary_error is None:
                primary_error = exc
    if primary_error is not None:
        report["status"] = "failed"
        report["report_sha256"] = activation.semantic_hash(report)
        _write_report(report_path, report)
        raise primary_error
    if (
        report["restored_preflight"]["counts"] != BASELINE_COUNTS
        or report["restored_preflight"]["fingerprint_sha256"]
        != BASELINE_FINGERPRINT
        or report["postcheck"]["counts"] != ACTIVATED_COUNTS
        or report["rollback"]["counts"] != BASELINE_COUNTS
        or report["rollback"]["fingerprint_sha256"] != BASELINE_FINGERPRINT
        or report["after_http"]["tiers"]
        != {"119": "receipts_only", "all": "receipts_only", "118": "receipts_only"}
        or not report["resource_teardown"]["verified_absent"]
    ):
        raise StoreSafetyError(
            "HTTP proof did not verify exact rollback and resource teardown"
        )
    report["status"] = "passed"
    report["report_sha256"] = activation.semantic_hash(report)
    _write_report(report_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    previous_handlers: dict[signal.Signals, Any] = {}

    def terminate(signum: int, _frame: Any) -> None:
        raise KeyboardInterrupt(f"received termination signal {signum}")

    for name in ("SIGINT", "SIGTERM"):
        candidate = getattr(signal, name, None)
        if candidate is not None:
            previous_handlers[candidate] = signal.getsignal(candidate)
            signal.signal(candidate, terminate)
    try:
        report = _run_owned_proof(_parser().parse_args(argv))
    finally:
        for candidate, handler in previous_handlers.items():
            signal.signal(candidate, handler)
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
