from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

from scripts import foushee_justice_publication_http_proof as proof


class FakeLifecycle:
    instances: list["FakeLifecycle"] = []

    def __init__(self, image: str):
        self.image = image
        self.label = "political-fingerprint.http-proof-run=fake"
        self.database_url = "postgresql://fake@127.0.0.1:5432/fake"
        self.resources = {"container", "volume", "network"}
        self.destroy_called = False
        FakeLifecycle.instances.append(self)

    def create(self) -> None:
        return None

    def restore(self, _snapshot: Path) -> None:
        return None

    def destroy(self) -> dict[str, Any]:
        self.destroy_called = True
        self.resources.clear()
        return {
            "run_label": self.label,
            "remaining": {"containers": [], "volumes": [], "networks": []},
            "verified_absent": True,
            "diagnostics": [],
        }


class FakeServer:
    instances: list["FakeServer"] = []

    def __init__(
        self, host: str, port: int, _database_url: str, deployed_commit: str
    ):
        self.base_url = f"http://{host}:{port}"
        self.deployed_commit = deployed_commit
        self.stopped = False
        FakeServer.instances.append(self)

    def start(self) -> dict[str, Any]:
        return {"status": "ok", "commit_sha": self.deployed_commit}

    def stop(self) -> None:
        self.stopped = True


class RestoreFailureLifecycle(FakeLifecycle):
    def restore(self, _snapshot: Path) -> None:
        raise RuntimeError("injected snapshot restore failure")


class StartupFailureServer(FakeServer):
    def start(self) -> dict[str, Any]:
        raise RuntimeError("injected Uvicorn startup failure")


def _args(tmp_path: Path) -> argparse.Namespace:
    snapshot = tmp_path / "pre-activation.dump"
    snapshot.write_bytes(b"snapshot")
    backup = tmp_path / "backup-proof.json"
    backup.write_text(
        json.dumps(
            {
                "snapshot": {
                    "path": snapshot.name,
                    "sha256": "a" * 64,
                }
            }
        ),
        encoding="utf-8",
    )
    preflight = tmp_path / "preflight-report.json"
    preflight.write_text("{}", encoding="utf-8")
    return argparse.Namespace(
        deployed_commit="a" * 40,
        preflight_report=preflight,
        backup_proof=backup,
        bundle_id=proof.activation.BUNDLE_ID,
        bundle_sha256=(
            "df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813"
        ),
        evidence_dir=tmp_path / "output",
        postgres_image=proof.POSTGRES_IMAGE,
        host="127.0.0.1",
        port=8012,
    )


def _install_success_fakes(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    FakeLifecycle.instances.clear()
    FakeServer.instances.clear()
    rollback_calls: list[dict[str, Any]] = []
    monkeypatch.setattr(proof.activation, "_exact_deployed_commit", lambda _sha: {})
    monkeypatch.setattr(
        proof.activation,
        "_verify_backup_proof",
        lambda *_args: {
            "verified": True,
            "proof_sha256": "b" * 64,
            "snapshot_sha256": "a" * 64,
            "preflight_report_sha256": "c" * 64,
            "restore_receipt_sha256": "d" * 64,
        },
    )
    monkeypatch.setattr(
        proof,
        "_restored_preflight",
        lambda *_args: {
            "counts": proof.BASELINE_COUNTS,
            "governed_baseline": {
                "reconciled_fingerprint": {
                    "sha256": proof.BASELINE_FINGERPRINT
                }
            },
        },
    )
    monkeypatch.setattr(
        proof.activation,
        "_api_receipts_only_smoke",
        lambda _url: {
            "tiers": {
                "119": "receipts_only",
                "all": "receipts_only",
                "118": "receipts_only",
            }
        },
    )
    monkeypatch.setattr(
        proof.activation, "_api_smoke", lambda _url: {"tiers": {"119": "reviewed_conclusion"}}
    )
    monkeypatch.setattr(
        proof,
        "_apply_exact",
        lambda *_args: {
            "already_applied": False,
            "rows_inserted": 7,
            "postcheck": {
                "counts": proof.ACTIVATED_COUNTS,
                "batch_id": 9,
                "artifact_ids": [141, 142, 143],
            },
        },
    )
    monkeypatch.setattr(
        proof,
        "_postcheck_exact",
        lambda *_args: {
            "counts": proof.ACTIVATED_COUNTS,
            "batch_id": 9,
            "artifact_ids": [141, 142, 143],
        },
    )

    def rollback(
        _url: str, _bundle: dict[str, Any], identity: dict[str, Any]
    ) -> dict[str, Any]:
        rollback_calls.append(identity)
        return {
            "counts": proof.BASELINE_COUNTS,
            "removed_batch_id": 9,
            "target_absent": {"absent": True},
            "governed_baseline": {
                "reconciled_fingerprint": {
                    "sha256": proof.BASELINE_FINGERPRINT
                }
            },
        }

    monkeypatch.setattr(proof, "_rollback_captured", rollback)
    return rollback_calls


@pytest.mark.parametrize(
    "stage",
    [
        "pre_http",
        "apply",
        "postcheck",
        "activated_http",
    ],
)
def test_owned_resources_are_destroyed_after_injected_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    rollback_calls = _install_success_fakes(monkeypatch)

    def fail_at(actual: str) -> None:
        if actual == stage:
            raise RuntimeError(f"injected {stage} failure")

    monkeypatch.setattr(proof, "_checkpoint", fail_at)
    with pytest.raises(RuntimeError, match=f"injected {stage} failure"):
        proof._run_owned_proof(
            _args(tmp_path),
            lifecycle_factory=FakeLifecycle,
            server_factory=FakeServer,
        )
    lifecycle = FakeLifecycle.instances[-1]
    assert lifecycle.destroy_called
    assert lifecycle.resources == set()
    if stage in {"postcheck", "activated_http"}:
        assert len(rollback_calls) == 1
        assert rollback_calls[0]["batch_id"] == 9
        assert rollback_calls[0]["artifact_ids"] == [141, 142, 143]
        assert rollback_calls[0]["bundle_id"] == proof.activation.BUNDLE_ID
    else:
        assert rollback_calls == []


def test_snapshot_restore_failure_destroys_owned_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_success_fakes(monkeypatch)
    with pytest.raises(RuntimeError, match="snapshot restore failure"):
        proof._run_owned_proof(
            _args(tmp_path),
            lifecycle_factory=RestoreFailureLifecycle,
            server_factory=FakeServer,
        )
    lifecycle = FakeLifecycle.instances[-1]
    assert lifecycle.destroy_called
    assert lifecycle.resources == set()


def test_uvicorn_startup_failure_stops_server_and_destroys_owned_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_success_fakes(monkeypatch)
    with pytest.raises(RuntimeError, match="Uvicorn startup failure"):
        proof._run_owned_proof(
            _args(tmp_path),
            lifecycle_factory=FakeLifecycle,
            server_factory=StartupFailureServer,
        )
    assert FakeServer.instances[-1].stopped is True
    lifecycle = FakeLifecycle.instances[-1]
    assert lifecycle.destroy_called
    assert lifecycle.resources == set()


@pytest.mark.parametrize("failure_kind", ["command", "verification"])
def test_rollback_failure_is_loud_but_resources_are_destroyed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_kind: str
) -> None:
    _install_success_fakes(monkeypatch)

    def fail_rollback(*_args: object) -> dict[str, Any]:
        raise RuntimeError(f"injected rollback {failure_kind} failure")

    monkeypatch.setattr(proof, "_rollback_captured", fail_rollback)
    with pytest.raises(
        RuntimeError, match=f"injected rollback {failure_kind} failure"
    ):
        proof._run_owned_proof(
            _args(tmp_path),
            lifecycle_factory=FakeLifecycle,
            server_factory=FakeServer,
        )
    lifecycle = FakeLifecycle.instances[-1]
    assert lifecycle.destroy_called
    assert lifecycle.resources == set()
    report = json.loads(
        (
            tmp_path / "output" / "http-integration-proof.json"
        ).read_text(encoding="utf-8")
    )
    assert report["failure_rollback"]["attempted_from_captured_identity"] is True
    assert report["failure_rollback"]["verified"] is False
    assert report["resource_teardown"]["verified_absent"] is True


def test_owned_lifecycle_success_requires_rollback_and_teardown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rollback_calls = _install_success_fakes(monkeypatch)
    result = proof._run_owned_proof(
        _args(tmp_path),
        lifecycle_factory=FakeLifecycle,
        server_factory=FakeServer,
    )
    assert result["status"] == "passed"
    assert result["rollback"]["counts"] == proof.BASELINE_COUNTS
    assert result["rollback"]["fingerprint_sha256"] == proof.BASELINE_FINGERPRINT
    assert result["after_http"]["tiers"] == {
        "119": "receipts_only",
        "all": "receipts_only",
        "118": "receipts_only",
    }
    assert len(rollback_calls) == 1
    assert rollback_calls[0]["batch_id"] == 9
    assert rollback_calls[0]["artifact_ids"] == [141, 142, 143]
    assert rollback_calls[0]["bundle_id"] == proof.activation.BUNDLE_ID
    assert result["resource_teardown"]["verified_absent"] is True
    assert FakeLifecycle.instances[-1].resources == set()
