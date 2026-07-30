from __future__ import annotations

import sys
import json
import tempfile
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
    validate_completion_record,
    write_completion_record,
    write_raw_snapshot,
)

PROOF = {
    "default_read_only": "off",
    "transaction_read_only": "on",
    "transaction_isolation": "repeatable read",
    "database_name": "postgres",
    "current_schema": "public",
    "postgres_version": "PostgreSQL 17.4 on test",
}
TEST_TEMP_ROOT = Path.cwd() / ".local"
TEST_TEMP_ROOT.mkdir(exist_ok=True)


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

    def test_completion_record_is_bound_to_closed_rolled_back_snapshot(self) -> None:
        results = {"complete_member_actions": [{"canonical_action_id": "a"}]}
        audit = [
            {"query_id": "complete_member_actions"},
            {"query_id": "transaction_rollback"},
        ]
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            output = Path(directory)
            raw = write_raw_snapshot(
                output,
                snapshot_id="snapshot-a",
                proof=PROOF,
                results=results,
                audit=audit,
            )
            completion = write_completion_record(
                output,
                snapshot_id="snapshot-a",
                raw_snapshot_path=raw,
                results=results,
                audit=audit,
                command_ids=[
                    "complete_member_actions",
                    "transaction_rollback",
                ],
                rollback_attempted=True,
                rollback_succeeded=True,
                connection_close_attempted=True,
                connection_close_succeeded=True,
                connection_closed_state_supported=True,
                connection_closed_state_verified=True,
            )
            snapshot, proof = validate_completion_record(raw, completion)
        self.assertEqual(snapshot["snapshot_id"], "snapshot-a")
        self.assertTrue(proof["rollback"]["succeeded"])
        self.assertTrue(
            proof["connection_close"]["client_closed_state_verified"]
        )

    def test_completion_record_rejects_substitution_and_false_states(self) -> None:
        results = {"complete_member_actions": [{"canonical_action_id": "a"}]}
        audit = [
            {"query_id": "complete_member_actions"},
            {"query_id": "transaction_rollback"},
        ]
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            output = Path(directory)
            raw = write_raw_snapshot(
                output,
                snapshot_id="snapshot-a",
                proof=PROOF,
                results=results,
                audit=audit,
            )
            completion = write_completion_record(
                output,
                snapshot_id="snapshot-a",
                raw_snapshot_path=raw,
                results=results,
                audit=audit,
                command_ids=[
                    "complete_member_actions",
                    "transaction_rollback",
                ],
                rollback_attempted=True,
                rollback_succeeded=True,
                connection_close_attempted=True,
                connection_close_succeeded=True,
                connection_closed_state_supported=True,
                connection_closed_state_verified=True,
            )
            original = json.loads(completion.read_text(encoding="utf-8"))
            for field_path in (
                ("snapshot_id",),
                ("raw_snapshot", "sha256"),
                ("rollback", "succeeded"),
                ("connection_close", "succeeded"),
                ("connection_close", "client_closed_state_verified"),
            ):
                altered = json.loads(json.dumps(original))
                target = altered
                for key in field_path[:-1]:
                    target = target[key]
                key = field_path[-1]
                target[key] = (
                    "snapshot-b"
                    if field_path == ("snapshot_id",)
                    else "0" * 64
                    if field_path == ("raw_snapshot", "sha256")
                    else False
                )
                altered["completion_subject_sha256"] = sha256_json(
                    {
                        key: value
                        for key, value in altered.items()
                        if key != "completion_subject_sha256"
                    }
                )
                completion.write_text(json.dumps(altered), encoding="utf-8")
                with self.subTest(field_path=field_path):
                    with self.assertRaises(ValueError):
                        validate_completion_record(raw, completion)

    def test_completion_record_rejects_cross_run_pair(self) -> None:
        audit = [
            {"query_id": "complete_member_actions"},
            {"query_id": "transaction_rollback"},
        ]
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            output = Path(directory)
            raw_a = write_raw_snapshot(
                output,
                snapshot_id="snapshot-a",
                proof=PROOF,
                results={"x": [{"run": "a"}]},
                audit=audit,
            )
            raw_b = write_raw_snapshot(
                output,
                snapshot_id="snapshot-b",
                proof=PROOF,
                results={"x": [{"run": "b"}]},
                audit=audit,
            )
            completion_b = write_completion_record(
                output,
                snapshot_id="snapshot-b",
                raw_snapshot_path=raw_b,
                results={"x": [{"run": "b"}]},
                audit=audit,
                command_ids=[
                    "complete_member_actions",
                    "transaction_rollback",
                ],
                rollback_attempted=True,
                rollback_succeeded=True,
                connection_close_attempted=True,
                connection_close_succeeded=True,
                connection_closed_state_supported=True,
                connection_closed_state_verified=True,
            )
            with self.assertRaises(ValueError):
                validate_completion_record(raw_a, completion_b)

    def test_copied_true_without_bound_runner_proof_fails(self) -> None:
        audit = [
            {"query_id": "complete_member_actions"},
            {"query_id": "transaction_rollback"},
        ]
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            output = Path(directory)
            raw = write_raw_snapshot(
                output,
                snapshot_id="snapshot-a",
                proof=PROOF,
                results={"x": []},
                audit=audit,
            )
            authored = output / "authored.completion.json"
            authored.write_text(
                json.dumps(
                    {
                        "snapshot_id": "snapshot-a",
                        "rollback": {"attempted": True, "succeeded": True},
                        "connection_close": {
                            "attempted": True,
                            "succeeded": True,
                            "client_closed_state_supported": True,
                            "client_closed_state_verified": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                validate_completion_record(raw, authored)


if __name__ == "__main__":
    unittest.main()
