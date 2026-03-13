from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any

from app.api.precomputed import (
    get_drift_response,
    get_fingerprint_response,
    get_summary_response,
    has_legislator,
)
from app.db import get_connection


@dataclass(frozen=True)
class SummaryRecord:
    legislator_id: str
    window_end: str
    classification_version: str
    summary_text: str
    generation_method: str
    created_at: str

FORBIDDEN_SUMMARY_TERMS = (
    "corrupt",
    "extreme",
    "radical",
    "worst",
    "best",
    "biased",
    "bought",
)


def get_or_create_summary(*, legislator_id: str) -> SummaryRecord | None:
    if not has_legislator(legislator_id=legislator_id):
        return None

    stored_summary = load_summary_record(legislator_id=legislator_id)
    if stored_summary is not None:
        return stored_summary

    fingerprint = get_fingerprint_response(legislator_id=legislator_id, comparison_party="ALL")
    drift = get_drift_response(legislator_id=legislator_id)
    if fingerprint is None or drift is None:
        return None

    summary_text = build_fallback_summary(fingerprint=fingerprint, drift=drift)
    validate_summary_text(summary_text)
    record = persist_summary_record(
        legislator_id=legislator_id,
        window_end=str(fingerprint["window_end"]),
        classification_version=str(fingerprint["classification_version"]),
        summary_text=summary_text,
        generation_method="deterministic_fallback",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return record


def load_summary_record(*, legislator_id: str) -> SummaryRecord | None:
    stored_summary = get_summary_response(legislator_id=legislator_id)
    if stored_summary is None:
        return None

    return SummaryRecord(
        legislator_id=str(stored_summary["legislator_id"]),
        window_end=str(stored_summary["window_end"]),
        classification_version=str(stored_summary["classification_version"]),
        summary_text=str(stored_summary["summary_text"]),
        generation_method=str(stored_summary["generation_method"]),
        created_at=str(stored_summary["created_at"]),
    )


def persist_summary_record(
    *,
    legislator_id: str,
    window_end: str,
    classification_version: str,
    summary_text: str,
    generation_method: str,
    created_at: str,
) -> SummaryRecord:
    legislator_db_row = _get_legislator_db_row(legislator_id=legislator_id)
    if legislator_db_row is None:
        return SummaryRecord(
            legislator_id=legislator_id,
            window_end=window_end,
            classification_version=classification_version,
            summary_text=summary_text,
            generation_method=generation_method,
            created_at=created_at,
        )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO summaries (
                legislator_id, window_end, classification_version, summary_text, generation_method, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (legislator_id, window_end, classification_version)
            DO UPDATE SET
                summary_text = EXCLUDED.summary_text,
                generation_method = EXCLUDED.generation_method,
                created_at = EXCLUDED.created_at,
                updated_at = NOW()
            """,
            (
                int(legislator_db_row["id"]),
                window_end,
                classification_version,
                summary_text,
                generation_method,
                created_at,
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
    finally:
        connection.close()

    return SummaryRecord(
        legislator_id=legislator_id,
        window_end=window_end,
        classification_version=classification_version,
        summary_text=summary_text,
        generation_method=generation_method,
        created_at=created_at,
    )


def build_fallback_summary(*, fingerprint: dict[str, object], drift: dict[str, object]) -> str:
    fingerprint_rows = list(fingerprint["fingerprint"])
    total_votes = int(fingerprint_rows[0]["total_votes"]) if fingerprint_rows else 0
    top_domains = sorted(
        fingerprint_rows,
        key=lambda row: (-float(row["vote_share"]), str(row["domain"])),
    )[:2]
    emphasis_text = ", ".join(
        f"{row['domain']} ({float(row['vote_share']):.0%})"
        for row in top_domains
        if float(row["vote_share"]) > 0
    )
    if not emphasis_text:
        emphasis_text = "no eligible issue domains"

    if bool(drift["insufficient_data"]):
        drift_text = "Drift is unavailable because the legislator has fewer than 20 eligible votes in the current 730-day window."
    else:
        drift_text = f"Drift for the current window is {float(drift['drift_value']):.2f}."

    return (
        f"This fingerprint is based on {total_votes} eligible votes in the current 730-day window. "
        f"The largest areas of vote emphasis are {emphasis_text}. "
        f"{drift_text}"
    )


def validate_summary_text(summary_text: str) -> None:
    normalized = summary_text.lower()
    for term in FORBIDDEN_SUMMARY_TERMS:
        if term in normalized:
            raise ValueError(f"Summary contains forbidden term: {term}")


def _get_legislator_db_row(*, legislator_id: str) -> dict[str, Any] | None:
    try:
        connection = get_connection()
    except Exception:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name_display
            FROM legislators
            ORDER BY id
            """
        )
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description or []]
        for row in rows:
            mapped = dict(zip(columns, row))
            normalized_id = "leg_" + re.sub(r"[^a-z0-9]+", "_", str(mapped["name_display"]).lower()).strip("_")
            if normalized_id == legislator_id:
                return mapped
        return None
    except Exception:
        return None
    finally:
        connection.close()
