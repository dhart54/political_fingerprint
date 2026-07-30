"""Seed a 76-action Frontend Pass A ledger in a disposable loopback database."""

from __future__ import annotations

import argparse
import json
import os
from urllib.parse import parse_qsl, urlsplit


FIXTURE_MARKER = "disposable Frontend Pass A complete-ledger fixture"
CLASSIFICATION_VERSION = "foushee-http-proof-v1"
GOVERNED_ROLLS = (32, 33, 130, 131, 166, 275, 299)
SUPPLEMENTAL_ROLLS = tuple(range(9001, 9070))
APPROVED_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
ROUTING_OVERRIDE_PARAMETERS = frozenset(
    {"host", "hostaddr", "service", "servicefile"}
)


def require_exact_loopback_postgres_url(database_url: str | None) -> str:
    """Return a structurally validated loopback PostgreSQL connection URL."""

    if not database_url:
        raise ValueError("a disposable PostgreSQL database URL is required")
    try:
        parsed = urlsplit(database_url)
        scheme = parsed.scheme.casefold()
        hostname = (parsed.hostname or "").casefold()
        port = parsed.port
        query_parameters = {
            key.casefold() for key, _value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
        }
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "the disposable PostgreSQL database target is malformed"
        ) from exc
    if scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "the disposable PostgreSQL database target must use postgres or postgresql"
        )
    if hostname not in APPROVED_LOOPBACK_HOSTS:
        raise ValueError(
            "the disposable PostgreSQL database host is not an approved loopback host"
        )
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(
            "the disposable PostgreSQL database port is invalid"
        )
    if (
        not parsed.path.startswith("/")
        or not parsed.path[1:]
        or "/" in parsed.path[1:]
    ):
        raise ValueError(
            "the disposable PostgreSQL database target requires a database name"
        )
    if parsed.fragment:
        raise ValueError(
            "the disposable PostgreSQL database target must not include a fragment"
        )
    blocked_parameters = sorted(
        query_parameters & ROUTING_OVERRIDE_PARAMETERS
    )
    if blocked_parameters:
        raise ValueError(
            "the disposable PostgreSQL database target contains a forbidden "
            f"routing parameter: {', '.join(blocked_parameters)}"
        )
    return database_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database-url-env",
        default="EDITORIAL_DISPOSABLE_DATABASE_URL",
    )
    args = parser.parse_args()
    try:
        database_url = require_exact_loopback_postgres_url(
            os.getenv(args.database_url_env)
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(
        database_url,
        autocommit=False,
        row_factory=dict_row,
    ) as conn:
        member = conn.execute(
            """SELECT id
               FROM legislators
               WHERE bioguide_id = 'F000477'"""
        ).fetchone()
        if not member:
            raise RuntimeError("F000477 is absent from the disposable database")

        governed = conn.execute(
            """SELECT rc.rollcall_number
               FROM roll_calls rc
               JOIN votes_cast vote ON vote.roll_call_id = rc.id
               WHERE vote.legislator_id = %s
                 AND rc.chamber = 'house'
                 AND rc.congress = 119
                 AND rc.session = 1
                 AND rc.rollcall_number = ANY(%s)
               ORDER BY rc.rollcall_number""",
            (member["id"], list(GOVERNED_ROLLS)),
        ).fetchall()
        governed_rolls = tuple(row["rollcall_number"] for row in governed)
        if governed_rolls != GOVERNED_ROLLS:
            raise RuntimeError(
                "the exact seven governed Foushee receipts are required before "
                f"seeding the navigation fixture: {governed_rolls}"
            )

        existing = conn.execute(
            """SELECT
                 COUNT(*) AS count,
                 COUNT(*) FILTER (
                   WHERE classification_version = %s
                 ) AS current_version_count
               FROM vote_classifications
               WHERE eligibility_reason = %s""",
            (CLASSIFICATION_VERSION, FIXTURE_MARKER),
        ).fetchone()
        existing_fixture = existing["count"]
        if existing_fixture not in (0, len(SUPPLEMENTAL_ROLLS)) or (
            existing_fixture
            and existing["current_version_count"] != existing_fixture
        ):
            raise RuntimeError(
                "partial Frontend Pass A disposable fixture detected: "
                f"{existing_fixture}"
            )
        if existing_fixture == 0:
            for index, roll in enumerate(SUPPLEMENTAL_ROLLS, start=1):
                roll_call = conn.execute(
                    """INSERT INTO roll_calls
                       (chamber, congress, session, rollcall_number, vote_date,
                        question, description, source_url)
                       VALUES (
                         'house', 119, 1, %s,
                         TIMESTAMPTZ '2025-01-02 12:00:00Z'
                           - (%s * INTERVAL '1 minute'),
                         %s,
                         'Deterministic unreviewed receipt used only for '
                         'disposable complete-ledger navigation validation.',
                         NULL
                       )
                       RETURNING id""",
                    (roll, index, f"Local validation receipt {index:02d}"),
                ).fetchone()
                conn.execute(
                    """INSERT INTO votes_cast
                       (roll_call_id, legislator_id, position)
                       VALUES (%s, %s, %s)""",
                    (
                        roll_call["id"],
                        member["id"],
                        "yea" if index % 2 else "nay",
                    ),
                )
                conn.execute(
                    """INSERT INTO vote_classifications
                       (roll_call_id, is_eligible, eligibility_reason,
                        primary_domain, score_breakdown,
                        classification_version)
                       VALUES (
                         %s, TRUE,
                         %s,
                         'JUSTICE_PUBLIC_SAFETY', '{}'::jsonb, %s
                       )""",
                    (
                        roll_call["id"],
                        FIXTURE_MARKER,
                        CLASSIFICATION_VERSION,
                    ),
                )

        total = conn.execute(
            """SELECT COUNT(*) AS count
               FROM votes_cast vote
               JOIN legislators member ON member.id = vote.legislator_id
               JOIN roll_calls rc ON rc.id = vote.roll_call_id
               JOIN vote_classifications classification
                 ON classification.roll_call_id = rc.id
               WHERE member.bioguide_id = 'F000477'
                 AND classification.primary_domain = 'JUSTICE_PUBLIC_SAFETY'"""
        ).fetchone()["count"]
        if total != 76:
            raise RuntimeError(
                f"Frontend Pass A disposable ledger must total 76 actions: {total}"
            )
        conn.commit()

    print(
        json.dumps(
            {
                "database": "loopback disposable",
                "fixture_marker": FIXTURE_MARKER,
                "classification_version": CLASSIFICATION_VERSION,
                "governed_actions_preserved": len(GOVERNED_ROLLS),
                "unreviewed_navigation_receipts": len(SUPPLEMENTAL_ROLLS),
                "total_actions": total,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
