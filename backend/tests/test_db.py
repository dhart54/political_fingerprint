from unittest.mock import MagicMock

import pytest

from app import db


def test_get_database_url_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/political_fingerprint")

    assert db.get_database_url() == "postgresql://user:pass@localhost:5432/political_fingerprint"


def test_get_database_url_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        db.get_database_url()


def test_get_connection_uses_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_connection = MagicMock()
    captured = {}

    def fake_connect(dsn: str):
        captured["dsn"] = dsn
        return fake_connection

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/political_fingerprint")
    monkeypatch.setattr(db, "psycopg_connect", fake_connect)

    connection = db.get_connection()

    assert connection is fake_connection
    assert captured["dsn"] == "postgresql://user:pass@localhost:5432/political_fingerprint"


def test_database_connection_context_closes_connection() -> None:
    fake_connection = MagicMock()
    database = db.Database(dsn="postgresql://user:pass@localhost:5432/political_fingerprint")
    object.__setattr__(database, "connect", MagicMock(return_value=fake_connection))

    with database.connection() as connection:
        assert connection is fake_connection

    fake_connection.close.assert_called_once_with()
