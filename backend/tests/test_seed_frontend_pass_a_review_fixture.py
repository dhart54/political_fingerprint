from __future__ import annotations

import sys
from unittest.mock import Mock

import pytest

from scripts import seed_frontend_pass_a_review_fixture as seed


ACCEPTED_URLS = (
    "postgresql://user:secret@localhost:5432/political_fingerprint",
    "postgres://user:secret@127.0.0.1:5432/political_fingerprint",
    "postgresql://user:secret@[::1]:5432/political_fingerprint",
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
    "postgresql://user@remote.example/db?host=localhost",
    "postgresql://user@localhost/db?host=remote.example",
    "postgresql://user@localhost/db?hostaddr=127.0.0.1",
    "postgresql://user@localhost/db?service=local",
    "postgresql://user@localhost/db?servicefile=%2Ftmp%2Fservice.conf",
    "https://user@localhost/db",
    "postgresql:///db",
    "postgresql://user@[::1/db",
    "postgresql://user@localhost,remote.example/db",
    "postgresql://user@remote.example/localhost",
    "postgresql://user@remote.example/db?label=127.0.0.1",
    "postgresql://user@remote.example/db#localhost",
    "postgresql://user@%6cocalhost/db",
    "postgresql://user@localhost:not-a-port/db",
    "postgresql://user@localhost:0/db",
    "postgresql://user@localhost/",
)


@pytest.mark.parametrize("database_url", ACCEPTED_URLS)
def test_exact_loopback_postgres_urls_are_accepted(database_url: str) -> None:
    assert seed.require_exact_loopback_postgres_url(database_url) == database_url


def test_normal_frontend_pass_a_disposable_url_is_accepted() -> None:
    database_url = (
        "postgresql://postgres:postgres@127.0.0.1:55432/"
        "political_fingerprint_editorial"
    )

    assert seed.require_exact_loopback_postgres_url(database_url) == database_url


@pytest.mark.parametrize("database_url", REJECTED_URLS)
def test_invalid_target_fails_before_connection_or_writes(
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect = Mock(
        side_effect=AssertionError(
            "connection and write paths must not be entered for an invalid target"
        )
    )
    fake_psycopg = type("FakePsycopg", (), {"connect": connect})()
    fake_rows = type("FakeRows", (), {"dict_row": object()})()
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)
    monkeypatch.setenv("EDITORIAL_DISPOSABLE_DATABASE_URL", database_url)
    monkeypatch.setattr(
        sys,
        "argv",
        ["seed_frontend_pass_a_review_fixture.py"],
    )

    with pytest.raises(SystemExit, match="disposable PostgreSQL database"):
        seed.main()

    connect.assert_not_called()


@pytest.mark.parametrize(
    "database_url",
    (
        "postgresql://user@localhost/db?host=remote.example",
        "postgresql://user@localhost/db?hostaddr=127.0.0.1",
        "postgresql://user@localhost/db?service=local",
        "postgresql://user@localhost/db?servicefile=local.conf",
    ),
)
def test_rejected_routing_error_names_parameter_without_exposing_url(
    database_url: str,
) -> None:
    parameter = database_url.split("?", maxsplit=1)[1].split("=", maxsplit=1)[0]

    with pytest.raises(ValueError) as caught:
        seed.require_exact_loopback_postgres_url(database_url)

    message = str(caught.value)
    assert parameter in message
    assert database_url not in message
