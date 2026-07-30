from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from backend.app.etl.readonly_discovery import (
    BEGIN_SQL,
    QuerySpec,
    ReadOnlyDiscoverySession,
    canonical_json_bytes,
    normalize_sql,
    sha256_json,
    validate_read_query,
)

PROOF = {
    "default_read_only": "off",
    "transaction_read_only": "on",
    "transaction_isolation": "repeatable read",
    "database_name": "postgres",
    "current_schema": "public",
    "postgres_version": "PostgreSQL 17.4 on test",
}


class FakeResult:
    def __init__(self, *, row=None, rows=None) -> None:
        self._row = row
        self._rows = rows if rows is not None else ([] if row is None else [row])

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, proof=None) -> None:
        self.proof = dict(PROOF if proof is None else proof)
        self.commands: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False

    def execute(self, sql, params=()):
        self.commands.append((normalize_sql(sql), tuple(params)))
        normalized = normalize_sql(sql)
        if normalized == BEGIN_SQL:
            return FakeResult()
        if "current_setting('transaction_read_only')" in normalized:
            return FakeResult(row=self.proof)
        if normalized.startswith("SET LOCAL") or normalized == "ROLLBACK":
            return FakeResult()
        return FakeResult(rows=[{"value": 1}])

    def close(self) -> None:
        self.closed = True


class ReadonlyDiscoverySqlTests(unittest.TestCase):
    def test_accepts_bounded_read_queries(self) -> None:
        self.assertEqual(validate_read_query(" SELECT 1 "), "SELECT 1")
        self.assertEqual(validate_read_query("SHOW transaction_read_only"), "SHOW transaction_read_only")
        self.assertTrue(validate_read_query("WITH x AS (SELECT 1) SELECT * FROM x"))

    def test_rejects_writes_locking_and_multiple_statements(self) -> None:
        rejected = [
            "INSERT INTO x VALUES (1)",
            "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x",
            "SELECT * FROM t FOR UPDATE",
            "SELECT * FROM t FOR SHARE",
            "SELECT nextval('s')",
            "SELECT 1; SELECT 2",
            "CALL mutate()",
            "COPY t TO STDOUT",
            "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY",
            "SET LOCAL statement_timeout = '1s'",
            "SELECT pg_sleep(1)",
        ]
        for sql in rejected:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    validate_read_query(sql)

    def test_comments_do_not_hide_forbidden_operations(self) -> None:
        with self.assertRaises(ValueError):
            validate_read_query("WITH x AS (/* hidden */ UPDATE t SET x=1) SELECT 1")

    def test_normalized_query_identity_ignores_formatting_and_comments(self) -> None:
        left = normalize_sql("SELECT  a\nFROM t -- comment\nORDER BY a")
        right = normalize_sql(" SELECT a FROM t ORDER BY a; ")
        self.assertEqual(left, right)

    def test_json_digest_is_key_order_independent_but_action_sensitive(self) -> None:
        left = [{"action_id": "a", "member_action": "Yea"}]
        reordered_keys = [{"member_action": "Yea", "action_id": "a"}]
        changed = left + [{"action_id": "b", "member_action": "Nay"}]
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(reordered_keys))
        self.assertEqual(sha256_json(left), sha256_json(reordered_keys))
        self.assertNotEqual(sha256_json(left), sha256_json(changed))


class ReadonlyDiscoveryTransactionTests(unittest.TestCase):
    def test_default_off_with_active_read_only_is_accepted(self) -> None:
        connection = FakeConnection()
        session = ReadOnlyDiscoverySession(
            connection,
            expected_database_name="postgres",
        )
        session.begin()
        proof = session.prove(snapshot_started_at="2026-07-30T00:00:00Z")
        self.assertEqual(proof["default_read_only"], "off")
        self.assertEqual(proof["transaction_read_only"], "on")
        self.assertEqual(connection.commands[0][0], BEGIN_SQL)

    def test_active_read_write_transaction_is_rejected(self) -> None:
        connection = FakeConnection(
            {**PROOF, "transaction_read_only": "off"}
        )
        session = ReadOnlyDiscoverySession(
            connection,
            expected_database_name="postgres",
        )
        try:
            session.begin()
            with self.assertRaisesRegex(RuntimeError, "not read-only"):
                session.prove(snapshot_started_at="2026-07-30T00:00:00Z")
        finally:
            session.rollback()
        self.assertEqual(connection.commands[-1][0], "ROLLBACK")

    def test_wrong_isolation_is_rejected(self) -> None:
        connection = FakeConnection(
            {**PROOF, "transaction_isolation": "read committed"}
        )
        session = ReadOnlyDiscoverySession(
            connection,
            expected_database_name="postgres",
        )
        try:
            session.begin()
            with self.assertRaisesRegex(RuntimeError, "REPEATABLE READ"):
                session.prove(snapshot_started_at="2026-07-30T00:00:00Z")
        finally:
            session.rollback()
        self.assertTrue(session.rollback_succeeded)

    def test_query_before_explicit_begin_is_rejected_without_sql(self) -> None:
        connection = FakeConnection()
        session = ReadOnlyDiscoverySession(
            connection,
            expected_database_name="postgres",
        )
        with self.assertRaisesRegex(RuntimeError, "proven, controlled"):
            session.execute(
                QuerySpec(
                    "fixed_query",
                    "test",
                    "SELECT 1",
                    (),
                    (),
                ),
                snapshot_started_at="2026-07-30T00:00:00Z",
            )
        self.assertEqual(connection.commands, [])

    def test_rollback_occurs_after_success(self) -> None:
        connection = FakeConnection()
        session = ReadOnlyDiscoverySession(
            connection,
            expected_database_name="postgres",
        )
        try:
            session.begin()
            session.prove(snapshot_started_at="2026-07-30T00:00:00Z")
            session.apply_local_controls(
                snapshot_started_at="2026-07-30T00:00:00Z"
            )
            session.execute(
                QuerySpec("fixed_query", "test", "SELECT 1", (), ()),
                snapshot_started_at="2026-07-30T00:00:00Z",
            )
        finally:
            session.rollback()
        self.assertTrue(session.rollback_succeeded)
        self.assertEqual(connection.commands[-1][0], "ROLLBACK")

    def test_failed_gate_emits_no_production_result_artifact(self) -> None:
        import backend.scripts.run_readonly_universe_discovery as runner

        connection = FakeConnection(
            {**PROOF, "transaction_read_only": "off"}
        )
        output_dir = (
            Path.cwd() / ".local" / f"failed-gate-{uuid4().hex}"
        )
        argv = [
            "run_readonly_universe_discovery.py",
            "--bioguide-id",
            "F000477",
            "--congress",
            "119",
            "--output-dir",
            str(output_dir),
        ]
        with (
            patch.object(sys, "argv", argv),
            patch.object(
                runner,
                "_load_database_target",
                return_value=("secret", "postgres", "test"),
            ),
            patch.object(
                runner,
                "connect_read_only",
                return_value=connection,
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "not read-only"):
                runner.main()
        self.assertFalse(output_dir.exists())
        self.assertEqual(connection.commands[-1][0], "ROLLBACK")
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
