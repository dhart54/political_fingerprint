from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import dotenv_values


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.etl.readonly_discovery import (  # noqa: E402
    QuerySpec,
    ReadOnlyDiscoverySession,
    connect_read_only,
    execute_query_pack,
    sanitized_session_proof,
    sha256_json,
    write_raw_snapshot,
)


CATALOG_QUERY = QuerySpec(
    query_id="public_schema_catalog",
    purpose="Map production tables, views, columns, types, and nullability.",
    sql="""
        SELECT
            c.table_name,
            t.table_type,
            c.ordinal_position,
            c.column_name,
            c.data_type,
            c.udt_name,
            c.is_nullable
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema = c.table_schema
         AND t.table_name = c.table_name
        WHERE c.table_schema = 'public'
        ORDER BY c.table_name, c.ordinal_position
    """,
    parameter_schema=(),
)


def _queries_for_catalog(catalog: list[dict[str, Any]], bioguide_id: str, congress: int):
    table_names = {str(row["table_name"]) for row in catalog}
    required = {
        "legislators",
        "bills",
        "roll_calls",
        "votes_cast",
        "vote_classifications",
        "vote_interpretations",
        "vote_contexts",
        "fingerprints",
    }
    missing = sorted(required - table_names)
    if missing:
        raise RuntimeError(f"required production tables missing: {', '.join(missing)}")

    queries = [
        QuerySpec(
            "member_identity",
            "Resolve the stable member record and current operational service flag.",
            """
                SELECT
                    id, bioguide_id, name_display, chamber::text AS chamber,
                    state, district, party, in_office, created_at, updated_at
                FROM legislators
                WHERE bioguide_id = %s
                ORDER BY bioguide_id
            """,
            (bioguide_id,),
            ("bioguide_id:text",),
        ),
        QuerySpec(
            "complete_member_actions",
            "Capture every recorded member action in the requested Congress.",
            """
                SELECT
                    lower(rc.chamber::text) || ':' || rc.congress::text || ':' ||
                        rc.session::text || ':' || rc.rollcall_number::text
                        AS canonical_action_id,
                    rc.id AS production_roll_call_id,
                    vc.id AS production_vote_id,
                    l.id AS production_legislator_id,
                    rc.chamber::text AS chamber,
                    rc.congress,
                    rc.session,
                    rc.rollcall_number,
                    rc.vote_date,
                    rc.question,
                    rc.description,
                    vc.position::text AS member_action,
                    rc.source_url AS vote_source_url,
                    rc.created_at AS roll_call_created_at,
                    rc.updated_at AS roll_call_updated_at,
                    vc.created_at AS vote_created_at,
                    b.id AS production_bill_id,
                    b.bill_type,
                    b.bill_number,
                    b.title AS bill_title,
                    b.summary AS bill_summary,
                    b.committee,
                    b.subjects,
                    b.created_at AS bill_created_at,
                    b.updated_at AS bill_updated_at,
                    vcf.is_eligible,
                    vcf.eligibility_reason,
                    vcf.primary_domain::text AS primary_domain,
                    vcf.score_breakdown,
                    vcf.classification_version,
                    vcf.created_at AS classification_created_at,
                    vcf.updated_at AS classification_updated_at,
                    vi.interpretation_status::text AS interpretation_status,
                    vi.support_position::text AS support_position,
                    vi.oppose_position::text AS oppose_position,
                    vi.interpretation_reason,
                    vi.source_url AS interpretation_source_url,
                    vi.interpretation_version,
                    vi.plain_english_summary,
                    vi.issue_facet,
                    vi.confidence,
                    vi.source_basis,
                    vi.created_at AS interpretation_created_at,
                    vi.updated_at AS interpretation_updated_at,
                    vctx.vote_type,
                    vctx.final_result,
                    vctx.context_source_list,
                    vctx.context_version,
                    vctx.created_at AS context_created_at,
                    vctx.updated_at AS context_updated_at
                FROM legislators l
                JOIN votes_cast vc ON vc.legislator_id = l.id
                JOIN roll_calls rc ON rc.id = vc.roll_call_id
                LEFT JOIN bills b ON b.id = rc.bill_id
                LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
                LEFT JOIN vote_contexts vctx
                  ON vctx.roll_call_id = rc.id
                 AND vctx.legislator_id = l.id
                WHERE l.bioguide_id = %s
                  AND rc.congress = %s
                ORDER BY rc.chamber, rc.congress, rc.session, rc.rollcall_number
            """,
            (bioguide_id, congress),
            ("bioguide_id:text", "congress:integer"),
        ),
        QuerySpec(
            "latest_classification_state",
            "Identify the current classification version and source-ingest cutoff.",
            """
                SELECT
                    classification_version,
                    COUNT(*) AS classification_count,
                    MAX(created_at) AS latest_created_at,
                    MAX(updated_at) AS latest_updated_at
                FROM vote_classifications
                GROUP BY classification_version
                ORDER BY latest_updated_at DESC, classification_version
            """,
            parameter_schema=(),
        ),
        QuerySpec(
            "member_fingerprints",
            "Capture production precompute membership and freshness for the member.",
            """
                SELECT
                    f.domain::text AS domain,
                    f.window_start,
                    f.window_end,
                    f.classification_version,
                    f.vote_count,
                    f.total_votes,
                    f.vote_share,
                    f.created_at,
                    f.updated_at
                FROM fingerprints f
                JOIN legislators l ON l.id = f.legislator_id
                WHERE l.bioguide_id = %s
                ORDER BY f.window_end, f.classification_version, f.domain
            """,
            (bioguide_id,),
            ("bioguide_id:text",),
        ),
    ]
    if "house_member_service_evidence" in table_names:
        queries.append(
            QuerySpec(
                "member_service_evidence",
                "Capture the governed House member service boundary.",
                """
                    SELECT
                        hmse.snapshot_id,
                        hmse.bioguide_id,
                        hmse.congress,
                        hmse.chamber,
                        hmse.canonical_state,
                        hmse.canonical_district,
                        hmse.member_type,
                        hmse.current_member,
                        hmse.service_start_year,
                        hmse.service_end_year,
                        hmse.service_date_precision,
                        hmse.metadata_currentness,
                        hmse.source_type,
                        hmse.source_update_date,
                        hmse.source_retrieved_at,
                        hmse.source_checksum,
                        hmms.retrieval_started_at,
                        hmms.retrieval_completed_at,
                        hmms.snapshot_status,
                        hmms.manifest_checksum
                    FROM house_member_service_evidence hmse
                    JOIN house_member_metadata_snapshots hmms
                      ON hmms.snapshot_id = hmse.snapshot_id
                    WHERE hmse.bioguide_id = %s
                      AND hmse.congress = %s
                    ORDER BY hmse.source_retrieved_at, hmse.snapshot_id
                """,
                (bioguide_id, congress),
                ("bioguide_id:text", "congress:integer"),
            )
        )
    editorial_required = {
        "editorial_artifact_versions",
        "editorial_publication_registry",
        "editorial_artifact_relationships",
    }
    if editorial_required <= table_names:
        queries.extend(
            [
                QuerySpec(
                    "member_editorial_artifacts",
                    "Capture relevant persisted editorial artifacts without projecting authority.",
                    """
                        SELECT
                            artifact_id, artifact_type, natural_key, schema_version,
                            artifact_version, content_sha256, source_manifest_sha256,
                            source_commit_sha, member_bioguide_id, issue_id, congress,
                            chamber::text AS chamber, canonical_action_id, episode_id,
                            policy_family_id, editorial_status, benchmark_status,
                            production_eligible, review_route, created_at
                        FROM editorial_artifact_versions
                        WHERE member_bioguide_id = %s
                           OR canonical_action_id LIKE %s
                        ORDER BY artifact_type, natural_key, artifact_version
                    """,
                    (bioguide_id, f"house:{congress}:%"),
                    (
                        "bioguide_id:text",
                        "canonical_action_pattern:derived_text",
                    ),
                ),
                QuerySpec(
                    "member_publication_registry",
                    "Capture active editorial publication identity for the member.",
                    """
                        SELECT
                            r.member_bioguide_id, r.issue_id, r.artifact_id,
                            r.publicly_active, r.activated_at, r.deactivated_at,
                            a.natural_key, a.artifact_version, a.content_sha256,
                            a.source_commit_sha, a.editorial_status,
                            a.benchmark_status, a.production_eligible
                        FROM editorial_publication_registry r
                        JOIN editorial_artifact_versions a
                          ON a.artifact_id = r.artifact_id
                        WHERE r.member_bioguide_id = %s
                        ORDER BY r.issue_id
                    """,
                    (bioguide_id,),
                    ("bioguide_id:text",),
                ),
            ]
        )
    return queries


def _load_database_target() -> tuple[str, str, str]:
    url = os.getenv("DATABASE_URL")
    if not url:
        url = str(dotenv_values(BACKEND / ".env").get("DATABASE_URL") or "")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("DATABASE_URL is not PostgreSQL")
    if not parsed.hostname or "supabase" not in parsed.hostname.lower():
        raise RuntimeError("DATABASE_URL is not the expected Supabase target")
    database_name = parsed.path.lstrip("/")
    if not database_name:
        raise RuntimeError("DATABASE_URL lacks a database name")
    host = parsed.hostname.lower()
    if "pooler.supabase.com" not in host:
        connection_mode = "direct_supabase"
    elif parsed.port == 6543:
        connection_mode = "supavisor_transaction_pooler"
    elif parsed.port == 5432:
        connection_mode = "supavisor_session_pooler"
    else:
        connection_mode = "supavisor_pooler_mode_unresolved"
    return url, database_name, connection_mode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bioguide-id", required=True)
    parser.add_argument("--congress", required=True, type=int)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--snapshot-label", default="production_snapshot")
    args = parser.parse_args()

    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot_id = (
        f"{args.snapshot_label}-"
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )
    database_url, expected_database_name, connection_mode = _load_database_target()
    connection = connect_read_only(database_url)
    session = ReadOnlyDiscoverySession(
        connection,
        expected_database_name=expected_database_name,
    )
    success = False
    try:
        session.begin()
        proof = session.prove(snapshot_started_at=started)
        session.apply_local_controls(snapshot_started_at=started)
        catalog_results, catalog_audit = execute_query_pack(
            session, [CATALOG_QUERY], started_at=started
        )
        queries = _queries_for_catalog(
            catalog_results["public_schema_catalog"],
            args.bioguide_id,
            args.congress,
        )
        results, audit = execute_query_pack(session, queries, started_at=started)
        results.update(catalog_results)
        audit = list(session.audit)
        success = True
    finally:
        session.rollback()
        connection.close()

    if not success:
        raise RuntimeError("production discovery transaction did not complete")
    if not session.rollback_succeeded:
        raise RuntimeError("production discovery transaction did not roll back")
    audit = list(session.audit)

    raw_path = write_raw_snapshot(
        args.output_dir,
        snapshot_id=snapshot_id,
        proof=proof,
        results=results,
        audit=audit,
    )
    summary = {
        "snapshot_id": snapshot_id,
        "discovery_as_of_utc": started,
        "read_only_session_proof": sanitized_session_proof(proof),
        "connection_mode": connection_mode,
        "first_sql_command": "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY",
        "transaction_rollback_succeeded": session.rollback_succeeded,
        "connection_closed": bool(getattr(connection, "closed", False)),
        "executed_query_ids": session.command_ids,
        "query_audit": audit,
        "result_counts": {key: len(value) for key, value in sorted(results.items())},
        "result_digests": {
            key: sha256_json(value) for key, value in sorted(results.items())
        },
        "raw_snapshot_path": str(raw_path),
        "raw_snapshot_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
