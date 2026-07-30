"""Create canonical identities or the governed Foushee baseline in a disposable DB."""

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
from app.editorial_artifacts.migration import MIGRATION, strip_transaction_wrappers
from app.editorial_artifacts.publication_activation import (
    load_activation_bundle,
    load_pre_activation_baseline_manifests,
)
from scripts.disposable_database_url import require_exact_loopback_postgres_url
from scripts import editorial_artifact_store as store

FOUSHEE_JUSTICE_119_POSITIONS = {
    32: ("yea", "https://clerk.house.gov/Votes/202532?Page=2"),
    33: ("nay", "https://clerk.house.gov/Votes/2025033"),
    130: ("nay", "https://clerk.house.gov/Votes/2025130"),
    131: ("yea", "https://clerk.house.gov/Votes/2025131"),
    166: ("yea", "https://clerk.house.gov/Votes/2025166"),
    275: ("nay", "https://clerk.house.gov/Votes/2025275"),
    299: ("nay", "https://clerk.house.gov/Votes/2025299"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url-env", default="EDITORIAL_DISPOSABLE_DATABASE_URL")
    parser.add_argument(
        "--additional-manifest",
        type=Path,
        action="append",
        default=[],
        help="Manifest used only to seed canonical identities; may be repeated.",
    )
    parser.add_argument(
        "--seed-foushee-activation-baseline",
        action="store_true",
        help=(
            "Apply migration 0016 and seed the exact governed 2/140/155/0 "
            "pre-activation baseline; disposable loopback databases only."
        ),
    )
    args = parser.parse_args()
    try:
        db_url = require_exact_loopback_postgres_url(
            os.getenv(args.database_url_env)
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    import psycopg
    from psycopg.rows import dict_row

    bundles = (
        load_pre_activation_baseline_manifests()
        if args.seed_foushee_activation_baseline
        else [build_seed_bundle()]
    )
    bundles.extend(
        json.loads(path.read_text(encoding="utf-8"))
        for path in args.additional_manifest
    )
    members = {
        item["member_bioguide_id"]
        for bundle in bundles
        for item in bundle["artifacts"]
        if item["member_bioguide_id"]
    }
    actions = {
        item["canonical_action_id"]
        for bundle in bundles
        for item in bundle["artifacts"]
        if item["canonical_action_id"]
    }
    member_metadata = {}
    for bundle in bundles:
        for item in bundle["artifacts"]:
            identifier = item.get("member_bioguide_id")
            if not identifier:
                continue
            payload = item.get("payload", {})
            member = payload.get("overlay", {}).get("member") or payload.get("member") or {}
            if member:
                member_metadata[identifier] = member
    with psycopg.connect(
        db_url, autocommit=True, row_factory=dict_row
    ) as conn:
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
            if member_id in names:
                name, state, district, party = names[member_id]
            else:
                member = member_metadata[member_id]
                name = member["display_name"]
                state = member.get("state") or "NA"
                district = str(member.get("district") or "0")
                party = member.get("party") or "I"
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
                   (chamber, congress, session, rollcall_number, vote_date,
                    question, description, source_url)
                   VALUES (%s, %s, %s, %s, '2025-01-03T12:00:00Z',
                           'Disposable identity', '', %s)""",
                (
                    chamber,
                    int(congress),
                    int(session),
                    int(roll),
                    (
                        FOUSHEE_JUSTICE_119_POSITIONS[int(roll)][1]
                        if int(roll) in FOUSHEE_JUSTICE_119_POSITIONS
                        else f"https://clerk.house.gov/Votes/2025{int(roll):03d}"
                    )
                    if chamber == "house" and int(congress) == 119
                    else None
                ),
            )
        if args.seed_foushee_activation_baseline:
            # Exact accepted statuses from semir-dev-05 and its reviewed
            # House Clerk sources; these populate only the disposable HTTP
            # receipt boundary and do not participate in editorial hashes.
            for roll, (position, _source_url) in (
                FOUSHEE_JUSTICE_119_POSITIONS.items()
            ):
                conn.execute(
                    """INSERT INTO votes_cast
                       (roll_call_id, legislator_id, position)
                       SELECT rc.id, legislator.id, %s
                       FROM roll_calls rc
                       CROSS JOIN LATERAL (
                         SELECT id FROM legislators
                         WHERE bioguide_id = 'F000477'
                       ) legislator
                       WHERE rc.chamber = 'house'
                         AND rc.congress = 119
                         AND rc.session = 1
                         AND rc.rollcall_number = %s""",
                    (position, roll),
                )
                conn.execute(
                    """INSERT INTO vote_classifications
                       (roll_call_id, is_eligible, eligibility_reason,
                        primary_domain, score_breakdown,
                        classification_version)
                       SELECT id, TRUE, 'reviewed disposable HTTP proof receipt',
                              'JUSTICE_PUBLIC_SAFETY', '{}'::jsonb,
                              'foushee-http-proof-v1'
                       FROM roll_calls
                       WHERE chamber = 'house'
                         AND congress = 119
                         AND session = 1
                         AND rollcall_number = %s""",
                    (roll,),
                )
        baseline_application = []
        if args.seed_foushee_activation_baseline:
            conn.execute(
                strip_transaction_wrappers(MIGRATION.read_text(encoding="utf-8"))
            )
            original_batch_key = store.BATCH_KEY
            original_starting_commit = store.STARTING_COMMIT
            for index, bundle in enumerate(bundles):
                if index == 1:
                    conn.execute(
                        "SELECT setval("
                        "'editorial_artifact_batches_batch_id_seq', 7, true)"
                    )
                store.BATCH_KEY = bundle["deterministic_batch_key"]
                store.STARTING_COMMIT = bundle["starting_commit"]
                baseline_application.append(
                    store.insert_bundle(
                        conn,
                        bundle,
                        store.resolve_canonical_identities(conn, bundle),
                    )
                )
            store.BATCH_KEY = original_batch_key
            store.STARTING_COMMIT = original_starting_commit
            counts = {
                "batches": int(
                    conn.execute(
                        "SELECT COUNT(*) AS n FROM editorial_artifact_batches"
                    ).fetchone()["n"]
                ),
                "artifacts": int(
                    conn.execute(
                        "SELECT COUNT(*) AS n FROM editorial_artifact_versions"
                    ).fetchone()["n"]
                ),
                "relationships": int(
                    conn.execute(
                        "SELECT COUNT(*) AS n "
                        "FROM editorial_artifact_relationships"
                    ).fetchone()["n"]
                ),
                "publication_registry": int(
                    conn.execute(
                        "SELECT COUNT(*) AS n "
                        "FROM editorial_publication_registry"
                    ).fetchone()["n"]
                ),
            }
            if counts != {
                "batches": 2,
                "artifacts": 140,
                "relationships": 155,
                "publication_registry": 0,
            } or [item["batch_id"] for item in baseline_application] != [1, 8]:
                raise RuntimeError(
                    f"disposable governed baseline mismatch: "
                    f"{counts}, {baseline_application}"
                )
            from scripts.foushee_justice_publication_activation import (
                _preflight,
            )

            exact_preflight = _preflight(conn, load_activation_bundle())
        else:
            exact_preflight = None
    print(json.dumps({
        "initialized": True,
        "migrations_applied_through": (
            "0016" if args.seed_foushee_activation_baseline else "0015"
        ),
        "canonical_members": len(members),
        "canonical_actions": len(actions),
        "bundle_count": len(bundles),
        "baseline_application": baseline_application
        if args.seed_foushee_activation_baseline
        else None,
        "exact_preflight": {
            "counts": exact_preflight["counts"],
            "batch_graphs": [
                {
                    "database_batch_id": item["database_batch_id"],
                    "graph_sha256": item["graph_sha256"],
                }
                for item in exact_preflight["governed_baseline"]["batches"]
            ],
            "canonical_semantic_hashes": exact_preflight[
                "governed_baseline"
            ]["canonical_semantic_hashes"],
            "fingerprint_sha256": exact_preflight["governed_baseline"][
                "reconciled_fingerprint"
            ]["sha256"],
            "selector": exact_preflight["selector"],
        }
        if exact_preflight
        else None,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
