import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.db import get_connection
from app.etl.compute import run_etl
from app.etl.ingest import run_ingest


FIXTURE_AS_OF_DATE = date(2026, 3, 12)
FALLBACK_PRECOMPUTED_DATA = run_etl(as_of=FIXTURE_AS_OF_DATE)
FALLBACK_FIXTURE_DATA = run_ingest().fixtures
DOMAIN_ORDER = [
    "ECONOMY_TAXES",
    "HEALTH_SOCIAL",
    "EDUCATION_WORKFORCE",
    "ENVIRONMENT_ENERGY",
    "NATIONAL_SECURITY_FOREIGN",
    "IMMIGRATION_BORDER",
    "JUSTICE_PUBLIC_SAFETY",
    "INFRASTRUCTURE_TECH_TRANSPORT",
]


@dataclass(frozen=True)
class FingerprintResponseRow:
    domain: str
    vote_count: int
    total_votes: int
    vote_share: float
    median_share: float


def has_legislator(*, legislator_id: str) -> bool:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is not None:
        return True
    return any(
        _serialize_legislator(fixture_legislator)["id"] == legislator_id
        for fixture_legislator in FALLBACK_FIXTURE_DATA.legislators
    )


def search_legislators(*, query: str = "") -> list[dict[str, object]]:
    database_results = _search_db_legislators(query=query)
    if database_results is not None:
        return database_results

    normalized_query = query.strip().lower()
    matches = [
        _serialize_legislator(legislator)
        for legislator in FALLBACK_FIXTURE_DATA.legislators
        if not normalized_query or normalized_query in str(legislator["name_display"]).lower()
    ]
    return sorted(
        matches,
        key=lambda legislator: (
            str(legislator["name_display"]).lower(),
            str(legislator["id"]).lower(),
        ),
    )


def get_fingerprint_response(*, legislator_id: str, comparison_party: str = "ALL") -> dict[str, object] | None:
    db_response = _get_db_fingerprint_response(
        legislator_id=legislator_id,
        comparison_party=comparison_party,
    )
    if db_response is not None:
        return db_response

    return _get_fallback_fingerprint_response(
        legislator_id=legislator_id,
        comparison_party=comparison_party,
    )


def get_drift_response(*, legislator_id: str) -> dict[str, object] | None:
    db_response = _get_db_drift_response(legislator_id=legislator_id)
    if db_response is not None:
        return db_response

    return _get_fallback_drift_response(legislator_id=legislator_id)


def get_summary_response(*, legislator_id: str) -> dict[str, object] | None:
    db_response = _get_db_summary_response(legislator_id=legislator_id)
    if db_response is not None:
        return db_response
    return None


def get_zip_lookup_response(*, zip_code: str) -> dict[str, object] | None:
    db_response = _get_db_zip_lookup_response(zip_code=zip_code)
    if db_response is not None:
        return db_response

    zip_record = next((row for row in FALLBACK_FIXTURE_DATA.zip_district_map if row["zip"] == zip_code), None)
    if zip_record is None:
        return None

    house_rep = next(
        (
            legislator
            for legislator in FALLBACK_FIXTURE_DATA.legislators
            if legislator["chamber"] == "house"
            and legislator["state"] == zip_record["state"]
            and legislator["district"] == zip_record["district"]
        ),
        None,
    )
    senators = [
        legislator
        for legislator in FALLBACK_FIXTURE_DATA.legislators
        if legislator["chamber"] == "senate" and legislator["state"] == zip_record["state"]
    ]

    return {
        "zip": zip_record["zip"],
        "state": zip_record["state"],
        "district": zip_record["district"],
        "house_rep": _serialize_legislator(house_rep) if house_rep is not None else None,
        "senators": [_serialize_legislator(legislator) for legislator in senators],
    }


def _get_db_fingerprint_response(*, legislator_id: str, comparison_party: str) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is None:
        return None

    fingerprint_rows = _get_db_fingerprint_rows(legislator_db_id=int(legislator["id"]))
    if fingerprint_rows is None:
        return None
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    median_rows = _get_db_chamber_medians(
        chamber=str(legislator["chamber"]),
        comparison_party=comparison_party,
        window_start=str(first_row["window_start"]),
        window_end=str(first_row["window_end"]),
        classification_version=str(first_row["classification_version"]),
    )
    if median_rows is None:
        return None

    median_map = {
        str(row["domain"]): float(row["median_share"])
        for row in median_rows
    }

    return {
        "legislator_id": legislator_id,
        "window_start": str(first_row["window_start"]),
        "window_end": str(first_row["window_end"]),
        "classification_version": str(first_row["classification_version"]),
        "last_updated": str(first_row["created_at"]),
        "comparison_party": comparison_party,
        "fingerprint": [
            FingerprintResponseRow(
                domain=str(row["domain"]),
                vote_count=int(row["vote_count"]),
                total_votes=int(row["total_votes"]),
                vote_share=float(row["vote_share"]),
                median_share=median_map.get(str(row["domain"]), 0.0),
            ).__dict__
            for row in fingerprint_rows
        ],
    }


def _get_db_drift_response(*, legislator_id: str) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is None:
        return None

    drift_row = _get_db_latest_drift_row(legislator_db_id=int(legislator["id"]))
    if drift_row is None:
        return None

    return {
        "legislator_id": legislator_id,
        "window_start": str(drift_row["window_start"]),
        "window_end": str(drift_row["window_end"]),
        "early_window_start": str(drift_row["early_window_start"]),
        "early_window_end": str(drift_row["early_window_end"]),
        "recent_window_start": str(drift_row["recent_window_start"]),
        "recent_window_end": str(drift_row["recent_window_end"]),
        "classification_version": str(drift_row["classification_version"]),
        "total_votes": int(drift_row["total_votes"]),
        "early_total_votes": int(drift_row["early_total_votes"]),
        "recent_total_votes": int(drift_row["recent_total_votes"]),
        "insufficient_data": bool(drift_row["insufficient_data"]),
        "drift_value": None
        if drift_row["drift_value"] is None
        else float(drift_row["drift_value"]),
    }


def _get_db_summary_response(*, legislator_id: str) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is None:
        return None

    summary_row = _get_db_latest_summary_row(legislator_db_id=int(legislator["id"]))
    if summary_row is None:
        return None

    return {
        "legislator_id": legislator_id,
        "window_end": str(summary_row["window_end"]),
        "classification_version": str(summary_row["classification_version"]),
        "summary_text": str(summary_row["summary_text"]),
        "generation_method": str(summary_row["generation_method"]),
        "created_at": str(summary_row["created_at"]),
    }


def _get_db_zip_lookup_response(*, zip_code: str) -> dict[str, object] | None:
    zip_record = _get_db_zip_record(zip_code=zip_code)
    if zip_record is None:
        return None

    house_rep = _get_db_house_rep(
        state=str(zip_record["state"]),
        district=str(zip_record["district"]),
    )
    senators = _get_db_senators(state=str(zip_record["state"]))
    if senators is None:
        return None

    return {
        "zip": str(zip_record["zip"]),
        "state": str(zip_record["state"]),
        "district": str(zip_record["district"]),
        "house_rep": _serialize_legislator(house_rep) if house_rep is not None else None,
        "senators": [_serialize_legislator(legislator) for legislator in senators],
    }


def _get_fallback_fingerprint_response(*, legislator_id: str, comparison_party: str = "ALL") -> dict[str, object] | None:
    fingerprint_rows = [
        row
        for row in FALLBACK_PRECOMPUTED_DATA.fingerprint_records
        if row.legislator_id == legislator_id
    ]
    if not fingerprint_rows:
        return None

    chamber = _infer_fallback_legislator_chamber(legislator_id)
    median_map = {
        median_record.domain: median_record
        for median_record in FALLBACK_PRECOMPUTED_DATA.chamber_medians
        if median_record.chamber == chamber and median_record.party == comparison_party
    }

    first_row = fingerprint_rows[0]
    return {
        "legislator_id": legislator_id,
        "window_start": first_row.window_start.isoformat(),
        "window_end": first_row.window_end.isoformat(),
        "classification_version": first_row.classification_version,
        "last_updated": f"{FIXTURE_AS_OF_DATE.isoformat()}T00:00:00+00:00",
        "comparison_party": comparison_party,
        "fingerprint": [
            FingerprintResponseRow(
                domain=row.domain,
                vote_count=row.vote_count,
                total_votes=row.total_votes,
                vote_share=row.vote_share,
                median_share=median_map[row.domain].median_share if row.domain in median_map else 0.0,
            ).__dict__
            for row in fingerprint_rows
        ],
    }


def _get_fallback_drift_response(*, legislator_id: str) -> dict[str, object] | None:
    drift_row = next(
        (row for row in FALLBACK_PRECOMPUTED_DATA.drift_results if row.legislator_id == legislator_id),
        None,
    )
    if drift_row is None:
        return None

    return {
        "legislator_id": legislator_id,
        "window_start": drift_row.window_start.isoformat(),
        "window_end": drift_row.window_end.isoformat(),
        "early_window_start": drift_row.early_window_start.isoformat(),
        "early_window_end": drift_row.early_window_end.isoformat(),
        "recent_window_start": drift_row.recent_window_start.isoformat(),
        "recent_window_end": drift_row.recent_window_end.isoformat(),
        "classification_version": drift_row.classification_version,
        "total_votes": drift_row.total_votes,
        "early_total_votes": drift_row.early_total_votes,
        "recent_total_votes": drift_row.recent_total_votes,
        "insufficient_data": drift_row.insufficient_data,
        "drift_value": drift_row.drift_value,
    }


def _search_db_legislators(*, query: str) -> list[dict[str, object]] | None:
    normalized_query = query.strip().lower()
    search_value = f"%{normalized_query}%"
    rows = _query_all_dicts(
        """
        SELECT id, bioguide_id, name_display, chamber, state, district, party
        FROM legislators
        WHERE (%s = '' OR lower(name_display) LIKE %s)
        ORDER BY lower(name_display), id
        """,
        (normalized_query, search_value),
    )
    if rows is None:
        return None
    return [_serialize_legislator(row) for row in rows]


def _get_db_legislator_by_external_id(legislator_id: str) -> dict[str, Any] | None:
    rows = _query_all_dicts(
        """
        SELECT id, bioguide_id, name_display, chamber, state, district, party
        FROM legislators
        ORDER BY id
        """
    )
    if rows is None:
        return None
    for row in rows:
        if _serialize_legislator(row)["id"] == legislator_id:
            return row
    return None


def _get_db_fingerprint_rows(*, legislator_db_id: int) -> list[dict[str, Any]] | None:
    return _query_all_dicts(
        f"""
        WITH latest AS (
            SELECT window_start, window_end, classification_version
            FROM fingerprints
            WHERE legislator_id = %s
            ORDER BY window_end DESC, classification_version DESC
            LIMIT 1
        )
        SELECT domain, vote_count, total_votes, vote_share, window_start, window_end, classification_version, created_at
        FROM fingerprints
        WHERE legislator_id = %s
          AND (window_start, window_end, classification_version) IN (
            SELECT window_start, window_end, classification_version FROM latest
          )
        ORDER BY CASE domain
            {''.join(f" WHEN '{domain}' THEN {index}" for index, domain in enumerate(DOMAIN_ORDER, start=1))}
            ELSE 999
          END
        """,
        (legislator_db_id, legislator_db_id),
    )


def _get_db_chamber_medians(
    *,
    chamber: str,
    comparison_party: str,
    window_start: str,
    window_end: str,
    classification_version: str,
) -> list[dict[str, Any]] | None:
    return _query_all_dicts(
        f"""
        SELECT domain, median_share
        FROM chamber_medians
        WHERE chamber = %s
          AND party = %s
          AND window_start = %s
          AND window_end = %s
          AND classification_version = %s
        ORDER BY CASE domain
            {''.join(f" WHEN '{domain}' THEN {index}" for index, domain in enumerate(DOMAIN_ORDER, start=1))}
            ELSE 999
          END
        """,
        (chamber, comparison_party, window_start, window_end, classification_version),
    )


def _get_db_latest_drift_row(*, legislator_db_id: int) -> dict[str, Any] | None:
    return _query_one_dict(
        """
        SELECT window_start, window_end, early_window_start, early_window_end,
               recent_window_start, recent_window_end, classification_version,
               total_votes, early_total_votes, recent_total_votes,
               insufficient_data, drift_value
        FROM drift_scores
        WHERE legislator_id = %s
        ORDER BY window_end DESC, classification_version DESC
        LIMIT 1
        """,
        (legislator_db_id,),
    )


def _get_db_latest_summary_row(*, legislator_db_id: int) -> dict[str, Any] | None:
    return _query_one_dict(
        """
        SELECT window_end, classification_version, summary_text, generation_method, created_at
        FROM summaries
        WHERE legislator_id = %s
        ORDER BY window_end DESC, classification_version DESC
        LIMIT 1
        """,
        (legislator_db_id,),
    )


def _get_db_zip_record(*, zip_code: str) -> dict[str, Any] | None:
    return _query_one_dict(
        """
        SELECT zip, state, district
        FROM zip_district_map
        WHERE zip = %s
        """,
        (zip_code,),
    )


def _get_db_house_rep(*, state: str, district: str) -> dict[str, Any] | None:
    return _query_one_dict(
        """
        SELECT id, bioguide_id, name_display, chamber, state, district, party
        FROM legislators
        WHERE chamber = 'house' AND state = %s AND district = %s
        ORDER BY id
        LIMIT 1
        """,
        (state, district),
    )


def _get_db_senators(*, state: str) -> list[dict[str, Any]] | None:
    return _query_all_dicts(
        """
        SELECT id, bioguide_id, name_display, chamber, state, district, party
        FROM legislators
        WHERE chamber = 'senate' AND state = %s
        ORDER BY lower(name_display), id
        """,
        (state,),
    )


def _query_all_dicts(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]] | None:
    try:
        connection = get_connection()
    except Exception:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description or []]
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        return None
    finally:
        connection.close()


def _query_one_dict(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _query_all_dicts(query, params)
    if rows is None or not rows:
        return None
    return rows[0]


def _infer_fallback_legislator_chamber(legislator_id: str) -> str:
    legislator = next(
        (
            _serialize_legislator(row)
            for row in FALLBACK_FIXTURE_DATA.legislators
            if _serialize_legislator(row)["id"] == legislator_id
        ),
        None,
    )
    if legislator is None:
        raise KeyError(f"Unknown legislator_id: {legislator_id}")
    return str(legislator["chamber"])


def _serialize_legislator(legislator: dict[str, object]) -> dict[str, object]:
    return {
        "id": _to_external_legislator_id(str(legislator["name_display"])),
        "bioguide_id": legislator["bioguide_id"],
        "name_display": legislator["name_display"],
        "chamber": legislator["chamber"],
        "state": legislator["state"],
        "district": legislator["district"],
        "party": legislator["party"],
    }


def _to_external_legislator_id(name_display: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name_display.lower()).strip("_")
    return f"leg_{slug}"
