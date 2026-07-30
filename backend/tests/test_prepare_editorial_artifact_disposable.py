from __future__ import annotations

import builtins
import json
import subprocess
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from scripts import prepare_editorial_artifact_disposable as prepare
from scripts import seed_frontend_pass_a_review_fixture as seed


ACCEPTED_URLS = (
    "postgresql://user:secret@localhost:5432/political_fingerprint",
    "postgres://user:secret@127.0.0.1/political_fingerprint",
    "postgresql://user:secret@[::1]:65535/political_fingerprint",
    (
        "POSTGRESQL://user:secret@LOCALHOST:5432/political_fingerprint"
        "?sslmode=disable&connect_timeout=5"
    ),
)

REJECTED_URLS = (
    "postgresql://localhost:password@remote.example/db",
    "postgresql://user:127.0.0.1@remote.example/db",
    "postgresql://user@localhost.example.com/db",
    "postgresql://user@127.0.0.1.example.com/db",
    "postgresql://user@remote.example/localhost",
    "postgresql://user@remote.example/db?label=127.0.0.1",
    "postgresql://user@remote.example/db#localhost",
    "postgresql://user@localhost/db?host=remote.example",
    "postgresql://user@localhost/db?HOST=remote.example",
    "postgresql://user@localhost/db?hostaddr=127.0.0.1",
    "postgresql://user@localhost/db?service=local",
    "postgresql://user@localhost/db?servicefile=%2Ftmp%2Fservice.conf",
    "postgresql://user@localhost/db?%68ost=remote.example",
    "https://user@localhost/db",
    "postgresql:///db",
    "postgresql://user@[::1/db",
    "postgresql://user@::1/db",
    "postgresql://user@localhost,remote.example/db",
    "postgresql://user@%6cocalhost/db",
    "postgresql://user@2130706433/db",
    "postgresql://user@0177.0.0.1/db",
    "postgresql://user@0x7f000001/db",
    "postgresql://user@localhost:not-a-port/db",
    "postgresql://user@localhost:0/db",
    "postgresql://user@localhost:65536/db",
    "postgresql://user@localhost:-1/db",
    "postgresql://user@localhost/",
    "postgresql://user@localhost",
    "postgresql://user@localhost//db",
    "",
)


def _install_fake_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    connect: Mock,
) -> None:
    psycopg = ModuleType("psycopg")
    psycopg.__path__ = []  # type: ignore[attr-defined]
    psycopg.connect = connect  # type: ignore[attr-defined]
    rows = ModuleType("psycopg.rows")
    rows.dict_row = object()
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", rows)


@pytest.mark.parametrize("database_url", ACCEPTED_URLS)
def test_preparation_and_seeder_share_the_accepted_contract(
    database_url: str,
) -> None:
    assert prepare.require_exact_loopback_postgres_url is (
        seed.require_exact_loopback_postgres_url
    )
    assert prepare.require_exact_loopback_postgres_url(database_url) == database_url


@pytest.mark.parametrize("database_url", REJECTED_URLS)
def test_invalid_target_stops_before_every_preparation_side_effect(
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    connect = Mock(side_effect=AssertionError("database connection was attempted"))
    _install_fake_psycopg(monkeypatch, connect)
    build_seed_bundle = Mock(side_effect=AssertionError("bundle loading began"))
    load_baseline = Mock(side_effect=AssertionError("baseline loading began"))
    insert_bundle = Mock(side_effect=AssertionError("row insertion began"))
    run = Mock(side_effect=AssertionError("database subprocess was attempted"))
    popen = Mock(side_effect=AssertionError("database subprocess was attempted"))
    imports: list[str] = []
    original_import = builtins.__import__

    def record_import(name: str, *args: object, **kwargs: object) -> object:
        imports.append(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(prepare, "build_seed_bundle", build_seed_bundle)
    monkeypatch.setattr(
        prepare,
        "load_pre_activation_baseline_manifests",
        load_baseline,
    )
    monkeypatch.setattr(prepare.store, "insert_bundle", insert_bundle)
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(builtins, "__import__", record_import)
    monkeypatch.setenv("EDITORIAL_DISPOSABLE_DATABASE_URL", database_url)
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare_editorial_artifact_disposable.py"],
    )

    with pytest.raises(SystemExit) as caught:
        prepare.main()

    message = str(caught.value)
    assert "disposable PostgreSQL database" in message
    if database_url:
        assert database_url not in message
    assert not any(name == "psycopg" for name in imports)
    connect.assert_not_called()
    build_seed_bundle.assert_not_called()
    load_baseline.assert_not_called()
    insert_bundle.assert_not_called()
    run.assert_not_called()
    popen.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_normal_disposable_editorial_preparation_reaches_success_receipt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_url = (
        "postgresql://postgres:postgres@127.0.0.1:55432/"
        "political_fingerprint_editorial"
    )

    class FakeConnection:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def __enter__(self) -> FakeConnection:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def execute(
            self,
            statement: str,
            _parameters: object = None,
        ) -> FakeConnection:
            self.statements.append(statement)
            return self

    connection = FakeConnection()
    connect = Mock(return_value=connection)
    _install_fake_psycopg(monkeypatch, connect)
    monkeypatch.setattr(prepare, "build_seed_bundle", lambda: {"artifacts": []})
    monkeypatch.setenv("EDITORIAL_DISPOSABLE_DATABASE_URL", database_url)
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare_editorial_artifact_disposable.py"],
    )

    assert prepare.main() == 0

    connect.assert_called_once()
    assert connect.call_args.args == (database_url,)
    assert connection.statements
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["initialized"] is True
    assert receipt["canonical_members"] == 0
    assert receipt["canonical_actions"] == 0
