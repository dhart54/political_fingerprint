"""Create the existing schema and minimum canonical identities in a disposable DB only."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import build_seed_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url-env", default="EDITORIAL_DISPOSABLE_DATABASE_URL")
    args = parser.parse_args()
    db_url = os.getenv(args.database_url_env)
    if not db_url or "localhost" not in db_url and "127.0.0.1" not in db_url:
        raise SystemExit("disposable initializer requires a loopback PostgreSQL URL")

    import psycopg

    bundle = build_seed_bundle()
    members = {
        item["member_bioguide_id"]
        for item in bundle["artifacts"]
        if item["member_bioguide_id"]
    }
    actions = {
        item["canonical_action_id"]
        for item in bundle["artifacts"]
        if item["canonical_action_id"]
    }
    with psycopg.connect(db_url, autocommit=True) as conn:
        for role in ("anon", "authenticated"):
            conn.execute(
                f"""DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                        CREATE ROLE {role} NOLOGIN;
                    END IF;
                END $$"""
            )
        for migration in sorted((BACKEND / "migrations").glob("*.sql")):
            if migration.name.startswith("0016_"):
                continue
            conn.execute(migration.read_text(encoding="utf-8"))
        for member_id in sorted(members):
            names = {
                "F000477": ("Valerie P. Foushee", "NC", "4", "D"),
                "M001184": ("Thomas Massie", "KY", "4", "R"),
                "G000586": ('Jesús G. "Chuy" García', "IL", "4", "D"),
            }
            name, state, district, party = names[member_id]
            conn.execute(
                """INSERT INTO legislators
                   (bioguide_id, name_display, chamber, state, district, party)
                   VALUES (%s, %s, 'house', %s, %s, %s)""",
                (member_id, name, state, district, party),
            )
        for action_id in sorted(actions):
            chamber, congress, session, roll = action_id.split(":")
            conn.execute(
                """INSERT INTO roll_calls
                   (chamber, congress, session, rollcall_number, vote_date, question, description)
                   VALUES (%s, %s, %s, %s, '2025-01-03T12:00:00Z', 'Disposable identity', '')""",
                (chamber, int(congress), int(session), int(roll)),
            )
    print(json.dumps({
        "initialized": True,
        "migrations_applied_through": "0015",
        "canonical_members": len(members),
        "canonical_actions": len(actions),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
