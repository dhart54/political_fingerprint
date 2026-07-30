from __future__ import annotations

import os
import unittest
from urllib.parse import urlparse

from backend.app.etl.readonly_discovery import (
    QuerySpec,
    ReadOnlyDiscoverySession,
    connect_read_only,
    sha256_json,
    validate_read_query,
)


DISPOSABLE_DATABASE_URL = os.getenv(
    "UNIVERSE_DISCOVERY_DISPOSABLE_DATABASE_URL"
)


@unittest.skipUnless(
    DISPOSABLE_DATABASE_URL,
    "set UNIVERSE_DISCOVERY_DISPOSABLE_DATABASE_URL for disposable PostgreSQL tests",
)
class ReadonlyDiscoveryPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from psycopg import connect

        cls.url = str(DISPOSABLE_DATABASE_URL)
        cls.database_name = urlparse(cls.url).path.lstrip("/")
        with connect(cls.url, autocommit=True) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS universe_discovery_fixture (
                    snapshot_label text NOT NULL,
                    canonical_action_id text NOT NULL,
                    member_action text NOT NULL,
                    source_resolved boolean NOT NULL
                )
                """
            )
            connection.execute("TRUNCATE universe_discovery_fixture")
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO universe_discovery_fixture (
                        snapshot_label,
                        canonical_action_id,
                        member_action,
                        source_resolved
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    [
                        ("a", "house:119:1:1", "yea", True),
                        ("a", "house:119:1:2", "nay", False),
                        ("a", "house:119:1:2", "yea", False),
                        ("b", "house:119:1:2", "nay", True),
                        ("b", "house:119:1:3", "yea", True),
                    ],
                )

    @classmethod
    def tearDownClass(cls) -> None:
        from psycopg import connect

        with connect(cls.url, autocommit=True) as connection:
            connection.execute("DROP TABLE universe_discovery_fixture")

    def test_real_read_only_transaction_and_adversarial_snapshot_cases(self) -> None:
        from psycopg import errors

        connection = connect_read_only(self.url)
        session = ReadOnlyDiscoverySession(
            connection,
            expected_database_name=self.database_name,
        )
        try:
            session.begin()
            proof = session.prove(
                snapshot_started_at="2026-07-30T00:00:00Z"
            )
            session.apply_local_controls(
                snapshot_started_at="2026-07-30T00:00:00Z"
            )
            rows = session.execute(
                QuerySpec(
                    "disposable_snapshot",
                    "Exercise deterministic discovery ordering.",
                    """
                    SELECT
                        snapshot_label,
                        canonical_action_id,
                        member_action,
                        source_resolved
                    FROM universe_discovery_fixture
                    ORDER BY
                        snapshot_label,
                        canonical_action_id,
                        member_action
                    """,
                    (),
                    (),
                ),
                snapshot_started_at="2026-07-30T00:00:00Z",
            )
            self.assertEqual(proof["transaction_read_only"], "on")
            self.assertEqual(
                proof["transaction_isolation"], "repeatable read"
            )
            self.assertEqual(
                rows,
                sorted(
                    rows,
                    key=lambda row: (
                        row["snapshot_label"],
                        row["canonical_action_id"],
                        row["member_action"],
                    ),
                ),
            )

            snapshot_a = [
                row for row in rows if row["snapshot_label"] == "a"
            ]
            snapshot_b = [
                row for row in rows if row["snapshot_label"] == "b"
            ]
            action_ids_a = [
                row["canonical_action_id"] for row in snapshot_a
            ]
            action_ids_b = [
                row["canonical_action_id"] for row in snapshot_b
            ]
            self.assertNotEqual(
                sha256_json(sorted(set(action_ids_a))),
                sha256_json(sorted(set(action_ids_b))),
            )
            self.assertEqual(
                sorted(
                    action_id
                    for action_id in set(action_ids_a)
                    if action_ids_a.count(action_id) > 1
                ),
                ["house:119:1:2"],
            )
            self.assertTrue(
                any(not row["source_resolved"] for row in snapshot_a)
            )
            self.assertEqual(
                set(action_ids_a) - set(action_ids_b),
                {"house:119:1:1"},
            )
            conflicting = {
                row["member_action"]
                for row in snapshot_a
                if row["canonical_action_id"] == "house:119:1:2"
            }
            self.assertEqual(conflicting, {"yea", "nay"})

            with self.assertRaises(ValueError):
                validate_read_query(
                    "INSERT INTO universe_discovery_fixture VALUES "
                    "('x', 'house:119:1:9', 'yea', true)"
                )
            with self.assertRaises(errors.ReadOnlySqlTransaction):
                connection.execute(
                    """
                    INSERT INTO universe_discovery_fixture VALUES (
                        'x', 'house:119:1:9', 'yea', true
                    )
                    """
                )
        finally:
            session.rollback()
            connection.close()
        self.assertTrue(session.rollback_succeeded)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
