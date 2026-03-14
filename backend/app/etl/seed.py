from dataclasses import dataclass
from datetime import date

from app.db import get_connection
from app.etl.classify import run_classification
from app.etl.compute import run_compute
from app.etl.ingest import IngestResult, run_ingest
from app.summaries.cache import build_fallback_summary


@dataclass(frozen=True)
class SeedBundle:
    legislators: list[dict[str, object]]
    bills: list[dict[str, object]]
    roll_calls: list[dict[str, object]]
    votes_cast: list[dict[str, object]]
    vote_classifications: list[dict[str, object]]
    fingerprints: list[dict[str, object]]
    chamber_medians: list[dict[str, object]]
    drift_scores: list[dict[str, object]]
    summaries: list[dict[str, object]]
    zip_district_map: list[dict[str, object]]


@dataclass(frozen=True)
class SeedResult:
    source: str
    legislators_seeded: int
    bills_seeded: int
    roll_calls_seeded: int
    votes_seeded: int
    classifications_seeded: int
    fingerprints_seeded: int
    chamber_medians_seeded: int
    drift_scores_seeded: int
    summaries_seeded: int
    zip_mappings_seeded: int


def seed_fixture_database(*, as_of: date) -> SeedResult:
    return run_etl_and_persist(source="fixtures", as_of=as_of)


def run_etl_and_persist(*, source: str = "fixtures", as_of: date) -> SeedResult:
    bundle = build_seed_bundle(source=source, as_of=as_of)
    persist_seed_bundle(bundle)
    return _build_seed_result(source=source, bundle=bundle)


def run_etl_and_persist_sources(*, sources: list[str], as_of: date) -> SeedResult:
    bundle = build_seed_bundle_for_sources(sources=sources, as_of=as_of)
    persist_seed_bundle(bundle)
    return _build_seed_result(source="+".join(sources), bundle=bundle)


def build_seed_bundle(*, source: str = "fixtures", as_of: date) -> SeedBundle:
    ingest_result = run_ingest(source=source)
    return _build_seed_bundle_from_ingest_result(ingest_result=ingest_result, as_of=as_of)


def build_seed_bundle_for_sources(*, sources: list[str], as_of: date) -> SeedBundle:
    ingest_results = [run_ingest(source=source) for source in sources]
    combined_ingest_result = _merge_ingest_results(ingest_results)
    return _build_seed_bundle_from_ingest_result(ingest_result=combined_ingest_result, as_of=as_of)


def _build_seed_bundle_from_ingest_result(*, ingest_result: IngestResult, as_of: date) -> SeedBundle:
    classification_result = run_classification(ingest_result, classification_version="v1")
    compute_result = run_compute(classification_result, ingest_result, as_of=as_of)

    legislator_id_map = {
        legislator["id"]: index
        for index, legislator in enumerate(ingest_result.fixtures.legislators, start=1)
    }
    bill_id_map = {
        bill["id"]: index
        for index, bill in enumerate(ingest_result.fixtures.bills, start=1)
    }
    roll_call_id_map = {
        roll_call["id"]: index
        for index, roll_call in enumerate(ingest_result.fixtures.roll_calls, start=1)
    }

    legislators = [
        {
            "id": legislator_id_map[legislator["id"]],
            "bioguide_id": legislator["bioguide_id"],
            "name_display": legislator["name_display"],
            "chamber": legislator["chamber"],
            "state": legislator["state"],
            "district": legislator["district"],
            "party": legislator["party"],
            "in_office": legislator["in_office"],
        }
        for legislator in ingest_result.fixtures.legislators
    ]
    bills = [
        {
            "id": bill_id_map[bill["id"]],
            "congress": bill["congress"],
            "bill_type": bill["bill_type"],
            "bill_number": bill["bill_number"],
            "title": bill["title"],
            "summary": bill["summary"],
            "committee": bill.get("committee"),
            "subjects": bill.get("subjects", []),
        }
        for bill in ingest_result.fixtures.bills
    ]
    roll_calls = [
        {
            "id": roll_call_id_map[roll_call["id"]],
            "chamber": roll_call["chamber"],
            "congress": roll_call["congress"],
            "rollcall_number": roll_call["rollcall_number"],
            "vote_date": roll_call["vote_date"],
            "question": roll_call["question"],
            "description": roll_call["description"],
            "bill_id": bill_id_map[roll_call["bill_ref"]],
            "source_url": roll_call.get("source_url"),
        }
        for roll_call in ingest_result.fixtures.roll_calls
    ]
    votes_cast = [
        {
            "id": index,
            "roll_call_id": roll_call_id_map[vote["roll_call_id"]],
            "legislator_id": legislator_id_map[vote["legislator_id"]],
            "position": vote["position"],
        }
        for index, vote in enumerate(ingest_result.fixtures.votes_cast, start=1)
    ]
    vote_classifications = [
        {
            "roll_call_id": roll_call_id_map[row.roll_call_id],
            "is_eligible": row.is_eligible,
            "eligibility_reason": row.eligibility_reason,
            "primary_domain": row.primary_domain,
            "score_breakdown": row.score_breakdown,
            "classification_version": row.classification_version,
        }
        for row in classification_result.classified_roll_calls
    ]
    fingerprints = [
        {
            "id": index,
            "legislator_id": legislator_id_map[row.legislator_id],
            "window_start": row.window_start.isoformat(),
            "window_end": row.window_end.isoformat(),
            "classification_version": row.classification_version,
            "domain": row.domain,
            "vote_count": row.vote_count,
            "total_votes": row.total_votes,
            "vote_share": row.vote_share,
        }
        for index, row in enumerate(compute_result.fingerprint_records, start=1)
    ]
    chamber_medians = [
        {
            "id": index,
            "chamber": row.chamber,
            "party": row.party,
            "window_start": compute_result.fingerprint_records[0].window_start.isoformat(),
            "window_end": compute_result.fingerprint_records[0].window_end.isoformat(),
            "classification_version": "v1",
            "domain": row.domain,
            "legislator_count": row.legislator_count,
            "median_share": row.median_share,
        }
        for index, row in enumerate(compute_result.chamber_medians, start=1)
    ]
    drift_scores = [
        {
            "id": index,
            "legislator_id": legislator_id_map[row.legislator_id],
            "window_start": row.window_start.isoformat(),
            "window_end": row.window_end.isoformat(),
            "early_window_start": row.early_window_start.isoformat(),
            "early_window_end": row.early_window_end.isoformat(),
            "recent_window_start": row.recent_window_start.isoformat(),
            "recent_window_end": row.recent_window_end.isoformat(),
            "classification_version": row.classification_version,
            "total_votes": row.total_votes,
            "early_total_votes": row.early_total_votes,
            "recent_total_votes": row.recent_total_votes,
            "insufficient_data": row.insufficient_data,
            "drift_value": row.drift_value,
        }
        for index, row in enumerate(compute_result.drift_results, start=1)
    ]
    summaries = [
        {
            "id": index,
            "legislator_id": legislator_id_map[legislator["id"]],
            "window_end": compute_result.fingerprint_records[0].window_end.isoformat(),
            "classification_version": "v1",
            "summary_text": build_fallback_summary(
                fingerprint=_build_summary_fingerprint_payload(
                    legislator_id=legislator["id"],
                    fingerprint_rows=compute_result.fingerprint_records,
                ),
                drift=_build_summary_drift_payload(
                    legislator_id=legislator["id"],
                    drift_rows=compute_result.drift_results,
                ),
            ),
            "generation_method": "deterministic_fallback",
            "created_at": f"{as_of.isoformat()}T00:00:00+00:00",
        }
        for index, legislator in enumerate(ingest_result.fixtures.legislators, start=1)
    ]
    zip_district_map = list(ingest_result.fixtures.zip_district_map)

    return SeedBundle(
        legislators=legislators,
        bills=bills,
        roll_calls=roll_calls,
        votes_cast=votes_cast,
        vote_classifications=vote_classifications,
        fingerprints=fingerprints,
        chamber_medians=chamber_medians,
        drift_scores=drift_scores,
        summaries=summaries,
        zip_district_map=zip_district_map,
    )


def _merge_ingest_results(ingest_results: list[IngestResult]) -> IngestResult:
    if not ingest_results:
        raise ValueError("At least one ingest result is required")

    merged_fixtures = ingest_results[0].fixtures
    for ingest_result in ingest_results[1:]:
        merged_fixtures = _merge_fixture_bundles(merged_fixtures, ingest_result.fixtures)

    return IngestResult(
        source="+".join(result.source for result in ingest_results),
        records_loaded=sum(result.records_loaded for result in ingest_results),
        fixtures=merged_fixtures,
    )


def _merge_fixture_bundles(left, right):
    return type(left)(
        legislators=_dedupe_rows(left.legislators + right.legislators, key="id"),
        bills=_dedupe_rows(left.bills + right.bills, key="id"),
        roll_calls=_dedupe_rows(left.roll_calls + right.roll_calls, key="id"),
        votes_cast=_dedupe_vote_rows(left.votes_cast + right.votes_cast),
        vote_subject_tags=_merge_vote_subject_tags(left.vote_subject_tags, right.vote_subject_tags),
        zip_district_map=_dedupe_rows(left.zip_district_map + right.zip_district_map, key="zip"),
    )


def _build_seed_result(*, source: str, bundle: SeedBundle) -> SeedResult:
    return SeedResult(
        source=source,
        legislators_seeded=len(bundle.legislators),
        bills_seeded=len(bundle.bills),
        roll_calls_seeded=len(bundle.roll_calls),
        votes_seeded=len(bundle.votes_cast),
        classifications_seeded=len(bundle.vote_classifications),
        fingerprints_seeded=len(bundle.fingerprints),
        chamber_medians_seeded=len(bundle.chamber_medians),
        drift_scores_seeded=len(bundle.drift_scores),
        summaries_seeded=len(bundle.summaries),
        zip_mappings_seeded=len(bundle.zip_district_map),
    )


def _dedupe_rows(rows: list[dict[str, object]], *, key: str) -> list[dict[str, object]]:
    deduped: dict[object, dict[str, object]] = {}
    for row in rows:
        deduped[row[key]] = row
    return list(deduped.values())


def _dedupe_vote_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[object, object, object], dict[str, object]] = {}
    for row in rows:
        deduped[(row["roll_call_id"], row["legislator_id"], row["position"])] = row
    return list(deduped.values())


def _merge_vote_subject_tags(
    left: dict[str, list[str]],
    right: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged = {key: list(value) for key, value in left.items()}
    for bill_id, subjects in right.items():
        merged[bill_id] = list(dict.fromkeys(merged.get(bill_id, []) + list(subjects)))
    return merged


def persist_seed_bundle(bundle: SeedBundle) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for statement in _delete_statements():
            cursor.execute(statement)

        _executemany(
            cursor,
            """
            INSERT INTO legislators (id, bioguide_id, name_display, chamber, state, district, party, in_office)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["bioguide_id"],
                    row["name_display"],
                    row["chamber"],
                    row["state"],
                    row["district"],
                    row["party"],
                    row["in_office"],
                )
                for row in bundle.legislators
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO bills (id, congress, bill_type, bill_number, title, summary, committee, subjects)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            [
                (
                    row["id"],
                    row["congress"],
                    row["bill_type"],
                    row["bill_number"],
                    row["title"],
                    row["summary"],
                    row["committee"],
                    _to_json(row["subjects"]),
                )
                for row in bundle.bills
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO roll_calls (id, chamber, congress, rollcall_number, vote_date, question, description, bill_id, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["chamber"],
                    row["congress"],
                    row["rollcall_number"],
                    row["vote_date"],
                    row["question"],
                    row["description"],
                    row["bill_id"],
                    row["source_url"],
                )
                for row in bundle.roll_calls
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO votes_cast (id, roll_call_id, legislator_id, position)
            VALUES (%s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["roll_call_id"],
                    row["legislator_id"],
                    row["position"],
                )
                for row in bundle.votes_cast
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO vote_classifications (
                roll_call_id, is_eligible, eligibility_reason, primary_domain, score_breakdown, classification_version
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            """,
            [
                (
                    row["roll_call_id"],
                    row["is_eligible"],
                    row["eligibility_reason"],
                    row["primary_domain"],
                    _to_json(row["score_breakdown"]),
                    row["classification_version"],
                )
                for row in bundle.vote_classifications
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO fingerprints (
                id, legislator_id, window_start, window_end, classification_version, domain, vote_count, total_votes, vote_share
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["legislator_id"],
                    row["window_start"],
                    row["window_end"],
                    row["classification_version"],
                    row["domain"],
                    row["vote_count"],
                    row["total_votes"],
                    row["vote_share"],
                )
                for row in bundle.fingerprints
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO chamber_medians (
                id, chamber, party, window_start, window_end, classification_version, domain, legislator_count, median_share
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["chamber"],
                    row["party"],
                    row["window_start"],
                    row["window_end"],
                    row["classification_version"],
                    row["domain"],
                    row["legislator_count"],
                    row["median_share"],
                )
                for row in bundle.chamber_medians
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO drift_scores (
                id, legislator_id, window_start, window_end, early_window_start, early_window_end,
                recent_window_start, recent_window_end, classification_version, total_votes,
                early_total_votes, recent_total_votes, insufficient_data, drift_value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["legislator_id"],
                    row["window_start"],
                    row["window_end"],
                    row["early_window_start"],
                    row["early_window_end"],
                    row["recent_window_start"],
                    row["recent_window_end"],
                    row["classification_version"],
                    row["total_votes"],
                    row["early_total_votes"],
                    row["recent_total_votes"],
                    row["insufficient_data"],
                    row["drift_value"],
                )
                for row in bundle.drift_scores
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO summaries (
                id, legislator_id, window_end, classification_version, summary_text, generation_method, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    row["id"],
                    row["legislator_id"],
                    row["window_end"],
                    row["classification_version"],
                    row["summary_text"],
                    row["generation_method"],
                    row["created_at"],
                )
                for row in bundle.summaries
            ],
        )
        _executemany(
            cursor,
            """
            INSERT INTO zip_district_map (zip, state, district)
            VALUES (%s, %s, %s)
            """,
            [
                (
                    row["zip"],
                    row["state"],
                    row["district"],
                )
                for row in bundle.zip_district_map
            ],
        )
        for statement in _sequence_statements(bundle):
            cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _build_summary_fingerprint_payload(*, legislator_id: str, fingerprint_rows: list[object]) -> dict[str, object]:
    rows = [row for row in fingerprint_rows if row.legislator_id == legislator_id]
    first_row = rows[0]
    return {
        "window_end": first_row.window_end.isoformat(),
        "classification_version": first_row.classification_version,
        "fingerprint": [
            {
                "domain": row.domain,
                "vote_count": row.vote_count,
                "total_votes": row.total_votes,
                "vote_share": row.vote_share,
            }
            for row in rows
        ],
    }


def _build_summary_drift_payload(*, legislator_id: str, drift_rows: list[object]) -> dict[str, object]:
    row = next(item for item in drift_rows if item.legislator_id == legislator_id)
    return {
        "insufficient_data": row.insufficient_data,
        "drift_value": row.drift_value,
    }


def _delete_statements() -> list[str]:
    return [
        """
        TRUNCATE TABLE
            summaries,
            drift_scores,
            chamber_medians,
            fingerprints,
            vote_classifications,
            votes_cast,
            roll_calls,
            bills,
            legislators,
            zip_district_map
        RESTART IDENTITY CASCADE
        """.strip(),
    ]


def _sequence_statements(bundle: SeedBundle) -> list[str]:
    return [
        _set_sequence_statement("legislators", len(bundle.legislators)),
        _set_sequence_statement("bills", len(bundle.bills)),
        _set_sequence_statement("roll_calls", len(bundle.roll_calls)),
        _set_sequence_statement("votes_cast", len(bundle.votes_cast)),
        _set_sequence_statement("fingerprints", len(bundle.fingerprints)),
        _set_sequence_statement("chamber_medians", len(bundle.chamber_medians)),
        _set_sequence_statement("drift_scores", len(bundle.drift_scores)),
        _set_sequence_statement("summaries", len(bundle.summaries)),
    ]


def _set_sequence_statement(table_name: str, current_max_id: int) -> str:
    return (
        "SELECT setval("
        f"pg_get_serial_sequence('{table_name}', 'id'), "
        f"{current_max_id}, true)"
    )


def _to_json(value: object) -> str:
    import json

    return json.dumps(value)


def _executemany(cursor, statement: str, rows: list[tuple[object, ...]]) -> None:
    if not rows:
        return
    cursor.executemany(statement, rows)
