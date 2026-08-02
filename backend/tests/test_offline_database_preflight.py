from __future__ import annotations

import subprocess

import pytest

from scripts.offline_database_preflight import (
    INVALID_OFFLINE_DATABASE_URL,
    OfflineDatabaseSafetyError,
    inspect_offline_database_environment,
)
from scripts.run_offline_backend_tests import build_child_environment, main


def test_inherited_remote_database_url_is_rejected_without_secret_leakage() -> None:
    secret_url = (
        "postgresql://sensitive-user:sensitive-password@db.example.test/private"
    )
    with pytest.raises(OfflineDatabaseSafetyError) as caught:
        inspect_offline_database_environment({"DATABASE_URL": secret_url})
    message = str(caught.value)
    assert "DATABASE_URL" in message
    assert "state=non_loopback" in message
    assert secret_url not in message
    assert "sensitive" not in message


@pytest.mark.parametrize(
    "database_url",
    (
        "postgresql://user:secret@localhost:5432/test_db",
        "postgres://user:secret@127.0.0.1/test_db",
        "postgresql://user:secret@[::1]:5432/test_db",
        INVALID_OFFLINE_DATABASE_URL,
    ),
)
def test_loopback_and_intentionally_invalid_primary_targets_are_accepted(
    database_url: str,
) -> None:
    result = inspect_offline_database_environment({"DATABASE_URL": database_url})
    assert result.database_url_state in {"loopback", "invalid_sentinel"}


def test_unset_primary_is_forced_to_invalid_and_disposable_targets_are_removed() -> (
    None
):
    child, summary = build_child_environment(
        {"EDITORIAL_DISPOSABLE_DATABASE_URL": INVALID_OFFLINE_DATABASE_URL},
        allow_disposable_integration=False,
    )
    assert child["DATABASE_URL"] == INVALID_OFFLINE_DATABASE_URL
    assert "EDITORIAL_DISPOSABLE_DATABASE_URL" not in child
    assert "disposable_integration=disabled" in summary


def test_disposable_loopback_requires_explicit_integration_opt_in() -> None:
    environment = {
        "DATABASE_URL": INVALID_OFFLINE_DATABASE_URL,
        "EDITORIAL_DISPOSABLE_DATABASE_URL": (
            "postgresql://user:secret@localhost:5432/disposable"
        ),
    }
    with pytest.raises(OfflineDatabaseSafetyError, match="opt_in=missing"):
        inspect_offline_database_environment(environment)
    result = inspect_offline_database_environment(
        environment, allow_disposable_integration=True
    )
    assert result.disposable_integration_enabled is True
    assert result.disposable_environment_names == ("EDITORIAL_DISPOSABLE_DATABASE_URL",)


def test_integration_opt_in_rejects_remote_and_requires_a_loopback_target() -> None:
    with pytest.raises(OfflineDatabaseSafetyError, match="missing_loopback_target"):
        inspect_offline_database_environment(
            {"DATABASE_URL": INVALID_OFFLINE_DATABASE_URL},
            allow_disposable_integration=True,
        )
    with pytest.raises(OfflineDatabaseSafetyError, match="non_loopback"):
        inspect_offline_database_environment(
            {
                "DATABASE_URL": INVALID_OFFLINE_DATABASE_URL,
                "EDITORIAL_DISPOSABLE_DATABASE_URL": (
                    "postgresql://user:secret@remote.example.test/db"
                ),
            },
            allow_disposable_integration=True,
        )


def test_runner_stops_before_subprocess_for_remote_target(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = False

    def fail_run(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True
        raise AssertionError("subprocess must not run")

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:top-secret@remote.example.test/private",
    )
    monkeypatch.setattr(subprocess, "run", fail_run)
    monkeypatch.setattr("sys.argv", ["run_offline_backend_tests.py", "--", "echo"])
    assert main() == 2
    assert called is False
    captured = capsys.readouterr()
    assert "top-secret" not in captured.err
