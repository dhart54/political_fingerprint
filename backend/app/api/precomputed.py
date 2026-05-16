import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.db import get_connection
from app.etl.classify import run_classification
from app.etl.compute import run_etl
from app.etl.ingest import run_ingest
from app.etl.interpret import run_interpretation


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


@dataclass(frozen=True)
class PositionResponseRow:
    domain: str
    yea_count: int
    nay_count: int
    other_count: int
    total_votes: int
    recorded_votes: int
    yea_share: float
    nay_share: float
    interpreted_support_count: int
    interpreted_oppose_count: int
    interpreted_other_count: int
    interpreted_total: int


def has_legislator(*, legislator_id: str) -> bool:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is not None:
        return True
    return any(
        _serialize_legislator(fixture_legislator)["id"] == legislator_id
        for fixture_legislator in FALLBACK_FIXTURE_DATA.legislators
    )


def get_legislator_profile(*, legislator_id: str) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is not None:
        return _serialize_legislator(legislator)

    fixture_legislator = next(
        (
            row
            for row in FALLBACK_FIXTURE_DATA.legislators
            if _serialize_legislator(row)["id"] == legislator_id
        ),
        None,
    )
    if fixture_legislator is None:
        return None
    return _serialize_legislator(fixture_legislator)


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


def get_coverage_metadata() -> dict[str, object]:
    db_metadata = _get_db_coverage_metadata()
    if db_metadata is not None:
        return db_metadata

    return _get_fallback_coverage_metadata()


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


def get_position_response(*, legislator_id: str) -> dict[str, object] | None:
    db_response = _get_db_position_response(legislator_id=legislator_id)
    if db_response is not None:
        return db_response

    return _get_fallback_position_response(legislator_id=legislator_id)


def get_position_evidence_response(*, legislator_id: str, domain: str) -> dict[str, object] | None:
    normalized_domain = domain.strip().upper()
    if normalized_domain not in DOMAIN_ORDER:
        return None

    db_response = _get_db_position_evidence_response(
        legislator_id=legislator_id,
        domain=normalized_domain,
    )
    if db_response is not None:
        return db_response

    return _get_fallback_position_evidence_response(
        legislator_id=legislator_id,
        domain=normalized_domain,
    )


def get_alignment_response(*, legislator_id: str, preferences: dict[str, str]) -> dict[str, object] | None:
    normalized_preferences = {
        domain.strip().upper(): stance
        for domain, stance in preferences.items()
        if domain.strip().upper() in DOMAIN_ORDER
    }
    if not normalized_preferences:
        return {
            "legislator_id": legislator_id,
            "preferences": {},
            "alignment": [],
        } if has_legislator(legislator_id=legislator_id) else None

    db_response = _get_db_alignment_response(
        legislator_id=legislator_id,
        preferences=normalized_preferences,
    )
    if db_response is not None:
        return db_response

    return _get_fallback_alignment_response(
        legislator_id=legislator_id,
        preferences=normalized_preferences,
    )


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


def get_supported_zip_responses(*, limit: int = 12) -> dict[str, object]:
    db_rows = _get_db_supported_zip_rows(limit=limit)
    if db_rows is not None:
        return {
            "data_source": "database",
            "zips": [_serialize_zip_row(row) for row in db_rows],
        }

    return {
        "data_source": "fixtures",
        "zips": [
            _serialize_zip_row(row)
            for row in sorted(FALLBACK_FIXTURE_DATA.zip_district_map, key=lambda item: str(item["zip"]))[:limit]
        ],
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


def _get_db_position_response(*, legislator_id: str) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is None:
        return None

    fingerprint_rows = _get_db_fingerprint_rows(legislator_db_id=int(legislator["id"]))
    if fingerprint_rows is None:
        return None
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    position_rows = _get_db_position_rows(
        legislator_db_id=int(legislator["id"]),
        window_start=str(first_row["window_start"]),
        window_end=str(first_row["window_end"]),
        classification_version=str(first_row["classification_version"]),
    )
    if position_rows is None:
        return None

    position_map = {str(row["domain"]): row for row in position_rows}
    serialized_rows = []
    for domain in DOMAIN_ORDER:
        row = position_map.get(domain, {})
        yea_count = int(row.get("yea_count", 0) or 0)
        nay_count = int(row.get("nay_count", 0) or 0)
        other_count = int(row.get("other_count", 0) or 0)
        interpreted_support_count = int(row.get("interpreted_support_count", 0) or 0)
        interpreted_oppose_count = int(row.get("interpreted_oppose_count", 0) or 0)
        interpreted_other_count = int(row.get("interpreted_other_count", 0) or 0)
        recorded_votes = yea_count + nay_count
        total_votes = recorded_votes + other_count
        interpreted_total = interpreted_support_count + interpreted_oppose_count + interpreted_other_count
        serialized_rows.append(
            PositionResponseRow(
                domain=domain,
                yea_count=yea_count,
                nay_count=nay_count,
                other_count=other_count,
                total_votes=total_votes,
                recorded_votes=recorded_votes,
                yea_share=(yea_count / recorded_votes) if recorded_votes else 0.0,
                nay_share=(nay_count / recorded_votes) if recorded_votes else 0.0,
                interpreted_support_count=interpreted_support_count,
                interpreted_oppose_count=interpreted_oppose_count,
                interpreted_other_count=interpreted_other_count,
                interpreted_total=interpreted_total,
            ).__dict__
        )

    return {
        "legislator_id": legislator_id,
        "window_start": str(first_row["window_start"]),
        "window_end": str(first_row["window_end"]),
        "classification_version": str(first_row["classification_version"]),
        "positions": serialized_rows,
    }


def _get_db_position_evidence_response(*, legislator_id: str, domain: str) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is None:
        return None

    fingerprint_rows = _get_db_fingerprint_rows(legislator_db_id=int(legislator["id"]))
    if fingerprint_rows is None:
        return None
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    evidence_rows = _get_db_position_evidence_rows(
        legislator_db_id=int(legislator["id"]),
        domain=domain,
        window_start=str(first_row["window_start"]),
        window_end=str(first_row["window_end"]),
        classification_version=str(first_row["classification_version"]),
    )
    if evidence_rows is None:
        return None

    return {
        "legislator_id": legislator_id,
        "domain": domain,
        "window_start": str(first_row["window_start"]),
        "window_end": str(first_row["window_end"]),
        "classification_version": str(first_row["classification_version"]),
        "evidence": [_serialize_evidence_row(row) for row in evidence_rows],
    }


def _get_db_alignment_response(*, legislator_id: str, preferences: dict[str, str]) -> dict[str, object] | None:
    legislator = _get_db_legislator_by_external_id(legislator_id)
    if legislator is None:
        return None

    fingerprint_rows = _get_db_fingerprint_rows(legislator_db_id=int(legislator["id"]))
    if fingerprint_rows is None:
        return None
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    evidence_rows = _get_db_alignment_rows(
        legislator_db_id=int(legislator["id"]),
        domains=tuple(preferences.keys()),
        window_start=str(first_row["window_start"]),
        window_end=str(first_row["window_end"]),
        classification_version=str(first_row["classification_version"]),
    )
    if evidence_rows is None:
        evidence_rows = []

    return _build_alignment_payload(
        legislator_id=legislator_id,
        preferences=preferences,
        evidence_rows=[_serialize_alignment_row(row) for row in evidence_rows],
        window_start=str(first_row["window_start"]),
        window_end=str(first_row["window_end"]),
        classification_version=str(first_row["classification_version"]),
    )


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


def _get_fallback_position_response(*, legislator_id: str) -> dict[str, object] | None:
    fingerprint_rows = [
        row
        for row in FALLBACK_PRECOMPUTED_DATA.fingerprint_records
        if row.legislator_id == legislator_id
    ]
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    roll_calls_by_id = {row["id"]: row for row in FALLBACK_FIXTURE_DATA.roll_calls}
    ingest_result = run_ingest()
    classification_step = run_classification(
        ingest_result,
        classification_version=first_row.classification_version,
    )
    classification_result = {
        row.roll_call_id: row
        for row in classification_step.classified_roll_calls
    }
    interpretation_result = {
        row.roll_call_id: row
        for row in run_interpretation(
            ingest_result,
            classification_step,
        ).vote_interpretations
    }

    counts_by_domain = {
        domain: {
            "yea_count": 0,
            "nay_count": 0,
            "other_count": 0,
            "interpreted_support_count": 0,
            "interpreted_oppose_count": 0,
            "interpreted_other_count": 0,
        }
        for domain in DOMAIN_ORDER
    }
    for vote in FALLBACK_FIXTURE_DATA.votes_cast:
        if vote["legislator_id"] != legislator_id:
            continue
        classified = classification_result.get(vote["roll_call_id"])
        if classified is None or not classified.is_eligible or classified.primary_domain is None:
            continue
        vote_date = str(roll_calls_by_id[vote["roll_call_id"]]["vote_date"])
        if not (first_row.window_start.isoformat() <= vote_date <= first_row.window_end.isoformat()):
            continue
        if vote["position"] == "yea":
            counts_by_domain[classified.primary_domain]["yea_count"] += 1
        elif vote["position"] == "nay":
            counts_by_domain[classified.primary_domain]["nay_count"] += 1
        else:
            counts_by_domain[classified.primary_domain]["other_count"] += 1
        interpretation = interpretation_result.get(vote["roll_call_id"])
        if interpretation is None or interpretation.interpretation_status != "interpreted":
            continue
        if vote["position"] == interpretation.support_position:
            counts_by_domain[classified.primary_domain]["interpreted_support_count"] += 1
        elif vote["position"] == interpretation.oppose_position:
            counts_by_domain[classified.primary_domain]["interpreted_oppose_count"] += 1
        else:
            counts_by_domain[classified.primary_domain]["interpreted_other_count"] += 1

    return {
        "legislator_id": legislator_id,
        "window_start": first_row.window_start.isoformat(),
        "window_end": first_row.window_end.isoformat(),
        "classification_version": first_row.classification_version,
        "positions": [
            PositionResponseRow(
                domain=domain,
                yea_count=counts["yea_count"],
                nay_count=counts["nay_count"],
                other_count=counts["other_count"],
                total_votes=counts["yea_count"] + counts["nay_count"] + counts["other_count"],
                recorded_votes=counts["yea_count"] + counts["nay_count"],
                yea_share=(
                    counts["yea_count"] / (counts["yea_count"] + counts["nay_count"])
                    if (counts["yea_count"] + counts["nay_count"])
                    else 0.0
                ),
                nay_share=(
                    counts["nay_count"] / (counts["yea_count"] + counts["nay_count"])
                    if (counts["yea_count"] + counts["nay_count"])
                    else 0.0
                ),
                interpreted_support_count=counts["interpreted_support_count"],
                interpreted_oppose_count=counts["interpreted_oppose_count"],
                interpreted_other_count=counts["interpreted_other_count"],
                interpreted_total=(
                    counts["interpreted_support_count"]
                    + counts["interpreted_oppose_count"]
                    + counts["interpreted_other_count"]
                ),
            ).__dict__
            for domain, counts in counts_by_domain.items()
        ],
    }


def _get_fallback_position_evidence_response(*, legislator_id: str, domain: str) -> dict[str, object] | None:
    fingerprint_rows = [
        row
        for row in FALLBACK_PRECOMPUTED_DATA.fingerprint_records
        if row.legislator_id == legislator_id
    ]
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    ingest_result = run_ingest()
    roll_calls_by_id = {row["id"]: row for row in FALLBACK_FIXTURE_DATA.roll_calls}
    bills_by_id = {row["id"]: row for row in FALLBACK_FIXTURE_DATA.bills}
    classification_step = run_classification(
        ingest_result,
        classification_version=first_row.classification_version,
    )
    interpretation_step = run_interpretation(ingest_result, classification_step)
    classification_result = {
        row.roll_call_id: row
        for row in classification_step.classified_roll_calls
    }
    interpretation_result = {
        row.roll_call_id: row
        for row in interpretation_step.vote_interpretations
    }

    evidence_rows = []
    for vote in FALLBACK_FIXTURE_DATA.votes_cast:
        if vote["legislator_id"] != legislator_id:
            continue
        classified = classification_result.get(vote["roll_call_id"])
        if (
            classified is None
            or not classified.is_eligible
            or classified.primary_domain != domain
        ):
            continue
        roll_call = roll_calls_by_id[vote["roll_call_id"]]
        vote_date = str(roll_call["vote_date"])
        if not (first_row.window_start.isoformat() <= vote_date <= first_row.window_end.isoformat()):
            continue
        bill = bills_by_id.get(str(roll_call.get("bill_ref")))
        interpreted = interpretation_result.get(vote["roll_call_id"])
        evidence_rows.append(
            {
                "roll_call_id": str(roll_call["id"]),
                "vote_date": vote_date,
                "chamber": str(roll_call["chamber"]),
                "congress": int(roll_call["congress"]),
                "rollcall_number": int(roll_call["rollcall_number"]),
                "position": str(vote["position"]),
                "question": str(roll_call["question"]),
                "description": str(roll_call["description"]),
                "bill_title": str(bill["title"]) if bill is not None else None,
                "bill_summary": str(bill["summary"]) if bill is not None else None,
                "classification_reason": str(classified.eligibility_reason),
                "score_breakdown": classified.score_breakdown,
                "source_url": roll_call.get("source_url"),
                "interpretation_status": interpreted.interpretation_status if interpreted is not None else None,
                "support_position": interpreted.support_position if interpreted is not None else None,
                "oppose_position": interpreted.oppose_position if interpreted is not None else None,
                "interpretation_reason": interpreted.interpretation_reason if interpreted is not None else None,
                "plain_english_summary": None,
                "yea_meaning": None,
                "nay_meaning": None,
                "policy_effect": None,
                "issue_facet": None,
                "confidence": None,
                "source_basis": [],
                "uncertainty_note": None,
            }
        )

    evidence_rows.sort(key=lambda row: (str(row["vote_date"]), int(row["rollcall_number"])))
    return {
        "legislator_id": legislator_id,
        "domain": domain,
        "window_start": first_row.window_start.isoformat(),
        "window_end": first_row.window_end.isoformat(),
        "classification_version": first_row.classification_version,
        "evidence": evidence_rows,
    }


def _get_fallback_alignment_response(*, legislator_id: str, preferences: dict[str, str]) -> dict[str, object] | None:
    fingerprint_rows = [
        row
        for row in FALLBACK_PRECOMPUTED_DATA.fingerprint_records
        if row.legislator_id == legislator_id
    ]
    if not fingerprint_rows:
        return None

    first_row = fingerprint_rows[0]
    ingest_result = run_ingest()
    classification_result = run_classification(
        ingest_result,
        classification_version=first_row.classification_version,
    )
    interpretation_result = run_interpretation(ingest_result, classification_result)
    roll_calls_by_id = {row["id"]: row for row in FALLBACK_FIXTURE_DATA.roll_calls}
    classification_by_roll_call = {
        row.roll_call_id: row
        for row in classification_result.classified_roll_calls
    }
    interpretation_by_roll_call = {
        row.roll_call_id: row
        for row in interpretation_result.vote_interpretations
    }

    evidence_rows = []
    for vote in FALLBACK_FIXTURE_DATA.votes_cast:
        if vote["legislator_id"] != legislator_id:
            continue
        classified = classification_by_roll_call.get(vote["roll_call_id"])
        if (
            classified is None
            or not classified.is_eligible
            or classified.primary_domain not in preferences
        ):
            continue
        roll_call = roll_calls_by_id[vote["roll_call_id"]]
        vote_date = str(roll_call["vote_date"])
        if not (first_row.window_start.isoformat() <= vote_date <= first_row.window_end.isoformat()):
            continue
        interpreted = interpretation_by_roll_call.get(vote["roll_call_id"])
        if interpreted is None:
            continue
        evidence_rows.append(
            {
                "domain": classified.primary_domain,
                "roll_call_id": str(vote["roll_call_id"]),
                "position": str(vote["position"]),
                "interpretation_status": interpreted.interpretation_status,
                "support_position": interpreted.support_position,
                "oppose_position": interpreted.oppose_position,
            }
        )

    return _build_alignment_payload(
        legislator_id=legislator_id,
        preferences=preferences,
        evidence_rows=evidence_rows,
        window_start=first_row.window_start.isoformat(),
        window_end=first_row.window_end.isoformat(),
        classification_version=first_row.classification_version,
    )


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


def _get_db_position_rows(
    *,
    legislator_db_id: int,
    window_start: str,
    window_end: str,
    classification_version: str,
) -> list[dict[str, Any]] | None:
    return _query_all_dicts(
        f"""
        SELECT
            vcf.primary_domain AS domain,
            COUNT(*) FILTER (WHERE vc.position = 'yea') AS yea_count,
            COUNT(*) FILTER (WHERE vc.position = 'nay') AS nay_count,
            COUNT(*) FILTER (WHERE vc.position NOT IN ('yea', 'nay')) AS other_count,
            COUNT(*) FILTER (
                WHERE vi.interpretation_status = 'interpreted'
                  AND vc.position = vi.support_position
            ) AS interpreted_support_count,
            COUNT(*) FILTER (
                WHERE vi.interpretation_status = 'interpreted'
                  AND vc.position = vi.oppose_position
            ) AS interpreted_oppose_count,
            COUNT(*) FILTER (
                WHERE vi.interpretation_status = 'interpreted'
                  AND vc.position NOT IN (vi.support_position, vi.oppose_position)
            ) AS interpreted_other_count
        FROM votes_cast vc
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi
          ON vi.roll_call_id = rc.id
         AND vi.classification_version = vcf.classification_version
        WHERE vc.legislator_id = %s
          AND vcf.is_eligible = TRUE
          AND vcf.primary_domain IS NOT NULL
          AND vcf.classification_version = %s
          AND DATE(rc.vote_date) BETWEEN %s AND %s
        GROUP BY vcf.primary_domain
        ORDER BY CASE vcf.primary_domain
            {''.join(f" WHEN '{domain}' THEN {index}" for index, domain in enumerate(DOMAIN_ORDER, start=1))}
            ELSE 999
          END
        """,
        (legislator_db_id, classification_version, window_start, window_end),
    )


def _get_db_position_evidence_rows(
    *,
    legislator_db_id: int,
    domain: str,
    window_start: str,
    window_end: str,
    classification_version: str,
) -> list[dict[str, Any]] | None:
    return _query_all_dicts(
        """
        SELECT
            rc.id AS roll_call_id,
            rc.vote_date,
            rc.chamber,
            rc.congress,
            rc.rollcall_number,
            vc.position,
            rc.question,
            rc.description,
            b.title AS bill_title,
            b.summary AS bill_summary,
            vcf.eligibility_reason AS classification_reason,
            vcf.score_breakdown,
            rc.source_url,
            vi.interpretation_status,
            vi.support_position,
            vi.oppose_position,
            vi.interpretation_reason,
            vi.plain_english_summary,
            vi.yea_meaning,
            vi.nay_meaning,
            vi.policy_effect,
            vi.issue_facet,
            vi.confidence,
            vi.source_basis,
            vi.uncertainty_note
        FROM votes_cast vc
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi
          ON vi.roll_call_id = rc.id
         AND vi.classification_version = vcf.classification_version
        LEFT JOIN bills b ON b.id = rc.bill_id
        WHERE vc.legislator_id = %s
          AND vcf.is_eligible = TRUE
          AND vcf.primary_domain = %s
          AND vcf.classification_version = %s
          AND DATE(rc.vote_date) BETWEEN %s AND %s
        ORDER BY rc.vote_date, rc.rollcall_number
        """,
        (legislator_db_id, domain, classification_version, window_start, window_end),
    )


def _get_db_alignment_rows(
    *,
    legislator_db_id: int,
    domains: tuple[str, ...],
    window_start: str,
    window_end: str,
    classification_version: str,
) -> list[dict[str, Any]] | None:
    placeholders = ", ".join(["%s"] * len(domains))
    return _query_all_dicts(
        f"""
        SELECT
            vcf.primary_domain AS domain,
            rc.id AS roll_call_id,
            vc.position,
            vi.interpretation_status,
            vi.support_position,
            vi.oppose_position
        FROM votes_cast vc
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE vc.legislator_id = %s
          AND vcf.is_eligible = TRUE
          AND vcf.primary_domain IN ({placeholders})
          AND vcf.classification_version = %s
          AND vi.classification_version = %s
          AND DATE(rc.vote_date) BETWEEN %s AND %s
        ORDER BY rc.vote_date, rc.rollcall_number
        """,
        (
            legislator_db_id,
            *domains,
            classification_version,
            classification_version,
            window_start,
            window_end,
        ),
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


def _get_db_supported_zip_rows(*, limit: int) -> list[dict[str, Any]] | None:
    return _query_all_dicts(
        """
        SELECT zip, state, district
        FROM zip_district_map
        ORDER BY zip
        LIMIT %s
        """,
        (limit,),
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


def _get_db_coverage_metadata() -> dict[str, object] | None:
    row = _query_one_dict(
        """
        SELECT
            (SELECT COUNT(*) FROM legislators WHERE in_office = TRUE) AS legislator_count,
            (SELECT COUNT(*) FROM roll_calls) AS roll_call_count,
            (SELECT COUNT(*) FROM roll_calls WHERE source_url IS NOT NULL AND source_url <> '') AS source_url_count,
            (SELECT COUNT(*) FROM vote_classifications WHERE is_eligible = TRUE) AS eligible_roll_call_count,
            (SELECT MIN(window_start) FROM fingerprints) AS window_start,
            (SELECT MAX(window_end) FROM fingerprints) AS window_end,
            (SELECT classification_version FROM fingerprints ORDER BY window_end DESC, classification_version DESC LIMIT 1) AS classification_version
        """,
    )
    if row is None or row.get("window_end") is None:
        return None

    roll_call_count = int(row["roll_call_count"] or 0)
    source_url_count = int(row["source_url_count"] or 0)
    return {
        "data_source": "database",
        "window_start": str(row["window_start"]),
        "window_end": str(row["window_end"]),
        "classification_version": str(row["classification_version"] or "unknown"),
        "legislator_count": int(row["legislator_count"] or 0),
        "roll_call_count": roll_call_count,
        "eligible_roll_call_count": int(row["eligible_roll_call_count"] or 0),
        "source_url_count": source_url_count,
        "source_url_share": _safe_share(source_url_count, roll_call_count),
    }


def _get_fallback_coverage_metadata() -> dict[str, object]:
    classification_result = run_classification(run_ingest(), classification_version="v1")
    roll_call_count = len(FALLBACK_FIXTURE_DATA.roll_calls)
    source_url_count = sum(
        1
        for roll_call in FALLBACK_FIXTURE_DATA.roll_calls
        if str(roll_call.get("source_url") or "").strip()
    )
    fingerprint_rows = FALLBACK_PRECOMPUTED_DATA.fingerprint_records
    window_start = min(row.window_start for row in fingerprint_rows)
    window_end = max(row.window_end for row in fingerprint_rows)
    classification_version = fingerprint_rows[0].classification_version if fingerprint_rows else "v1"

    return {
        "data_source": "fixtures",
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "classification_version": classification_version,
        "legislator_count": len(FALLBACK_FIXTURE_DATA.legislators),
        "roll_call_count": roll_call_count,
        "eligible_roll_call_count": sum(1 for row in classification_result.classified_roll_calls if row.is_eligible),
        "source_url_count": source_url_count,
        "source_url_share": _safe_share(source_url_count, roll_call_count),
    }


def _safe_share(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


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


def _serialize_evidence_row(row: dict[str, Any]) -> dict[str, object]:
    return {
        "roll_call_id": str(row["roll_call_id"]),
        "vote_date": str(row["vote_date"]),
        "chamber": str(row["chamber"]),
        "congress": int(row["congress"]),
        "rollcall_number": int(row["rollcall_number"]),
        "position": str(row["position"]),
        "question": str(row["question"]),
        "description": str(row["description"]),
        "bill_title": None if row.get("bill_title") is None else str(row["bill_title"]),
        "bill_summary": None if row.get("bill_summary") is None else str(row["bill_summary"]),
        "classification_reason": str(row["classification_reason"]),
        "score_breakdown": row.get("score_breakdown") or {},
        "source_url": row.get("source_url"),
        "interpretation_status": None if row.get("interpretation_status") is None else str(row["interpretation_status"]),
        "support_position": None if row.get("support_position") is None else str(row["support_position"]),
        "oppose_position": None if row.get("oppose_position") is None else str(row["oppose_position"]),
        "interpretation_reason": None if row.get("interpretation_reason") is None else str(row["interpretation_reason"]),
        "plain_english_summary": None if row.get("plain_english_summary") is None else str(row["plain_english_summary"]),
        "yea_meaning": None if row.get("yea_meaning") is None else str(row["yea_meaning"]),
        "nay_meaning": None if row.get("nay_meaning") is None else str(row["nay_meaning"]),
        "policy_effect": None if row.get("policy_effect") is None else str(row["policy_effect"]),
        "issue_facet": None if row.get("issue_facet") is None else str(row["issue_facet"]),
        "confidence": None if row.get("confidence") is None else str(row["confidence"]),
        "source_basis": row.get("source_basis") or [],
        "uncertainty_note": None if row.get("uncertainty_note") is None else str(row["uncertainty_note"]),
    }


def _serialize_zip_row(row: dict[str, Any]) -> dict[str, object]:
    return {
        "zip": str(row["zip"]),
        "state": str(row["state"]),
        "district": str(row["district"]),
    }


def _serialize_alignment_row(row: dict[str, Any]) -> dict[str, object]:
    return {
        "domain": str(row["domain"]),
        "roll_call_id": str(row["roll_call_id"]),
        "position": str(row["position"]),
        "interpretation_status": str(row["interpretation_status"]),
        "support_position": None if row.get("support_position") is None else str(row["support_position"]),
        "oppose_position": None if row.get("oppose_position") is None else str(row["oppose_position"]),
    }


def _build_alignment_payload(
    *,
    legislator_id: str,
    preferences: dict[str, str],
    evidence_rows: list[dict[str, object]],
    window_start: str,
    window_end: str,
    classification_version: str,
) -> dict[str, object]:
    rows_by_domain = {
        domain: [
            row
            for row in evidence_rows
            if row["domain"] == domain
        ]
        for domain in preferences
    }

    return {
        "legislator_id": legislator_id,
        "window_start": window_start,
        "window_end": window_end,
        "classification_version": classification_version,
        "preferences": preferences,
        "alignment": [
            _build_domain_alignment(
                domain=domain,
                preference=preference,
                evidence_rows=rows_by_domain.get(domain, []),
            )
            for domain, preference in preferences.items()
        ],
    }


def _build_domain_alignment(
    *,
    domain: str,
    preference: str,
    evidence_rows: list[dict[str, object]],
) -> dict[str, object]:
    aligned_count = 0
    not_aligned_count = 0
    interpreted_count = 0
    ambiguous_count = 0
    evidence_roll_call_ids = []

    for row in evidence_rows:
        if row["interpretation_status"] != "interpreted":
            ambiguous_count += 1
            continue
        evidence_roll_call_ids.append(row["roll_call_id"])
        if row["position"] not in {row["support_position"], row["oppose_position"]}:
            ambiguous_count += 1
            continue
        interpreted_count += 1
        if preference == "show_record":
            continue
        preferred_position = row["support_position"] if preference == "support_more_action" else row["oppose_position"]
        if row["position"] == preferred_position:
            aligned_count += 1
        else:
            not_aligned_count += 1

    label = _alignment_label(
        preference=preference,
        interpreted_count=interpreted_count,
        aligned_count=aligned_count,
        not_aligned_count=not_aligned_count,
    )

    return {
        "domain": domain,
        "preference": preference,
        "label": label,
        "aligned_count": aligned_count,
        "not_aligned_count": not_aligned_count,
        "interpreted_count": interpreted_count,
        "ambiguous_count": ambiguous_count,
        "evidence_count": len(evidence_rows),
        "evidence_roll_call_ids": evidence_roll_call_ids,
    }


def _alignment_label(
    *,
    preference: str,
    interpreted_count: int,
    aligned_count: int,
    not_aligned_count: int,
) -> str:
    if interpreted_count == 0:
        return "insufficient_evidence"
    if preference == "show_record":
        return "mixed"
    if aligned_count > 0 and not_aligned_count == 0:
        return "aligned"
    if not_aligned_count > 0 and aligned_count == 0:
        return "not_aligned"
    return "mixed"


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
