"""Validate reviewed ZIP seed rows without loading them into any database."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any


REQUIRED_SEED_FIELDS = [
    "zip",
    "state",
    "district",
    "source_name",
    "source_type",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
    "source_currentness",
    "confidence",
    "is_primary",
    "district_type",
    "congress",
    "cycle",
    "valid_from",
    "valid_to",
    "provider_record_id",
    "notes",
]

SOURCE_METADATA_FIELDS = [
    "source_name",
    "source_type",
    "source_retrieved_at",
    "source_effective_date",
    "source_version",
]

HIGH_CONFIDENCE_VALUES = {"source_backed", "reviewed"}
SOURCE_CURRENTNESS_VALUES = {"current", "stale_or_unknown", "fixture_sample", "unsupported", "expired"}
CONFIDENCE_VALUES = {"source_backed", "reviewed", "inferred", "low", "unknown"}

PAYLOAD_SINGLE_DISTRICT_READY = "single_district_ready"
PAYLOAD_AMBIGUOUS_ZIP = "ambiguous_zip"
PAYLOAD_MULTI_STATE_ZIP = "multi_state_zip"
PAYLOAD_STALE_OR_UNKNOWN_SOURCE = "stale_or_unknown_source"
PAYLOAD_FIXTURE_SAMPLE_ONLY = "fixture_sample_only"
PAYLOAD_UNSUPPORTED_ZIP = "unsupported_zip"


def validate_seed_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_rows = [normalize_seed_row(row, index) for index, row in enumerate(rows)]
    rows_by_zip: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for row in normalized_rows:
        if row["zip"]:
            rows_by_zip[row["zip"]].append(row)
        errors.extend(validate_seed_row(row))

    duplicate_keys = [
        key
        for key, count in sorted(Counter(active_source_period_key(row) for row in normalized_rows).items())
        if key and count > 1
    ]
    for key in duplicate_keys:
        errors.append(
            {
                "row_id": "seed",
                "field": "active_source_period",
                "message": f"Duplicate active source-period row: {key}",
            }
        )

    classifications = {
        zip_code: classify_zip_rows(zip_rows)
        for zip_code, zip_rows in sorted(rows_by_zip.items())
    }
    ineligible_counts = Counter()
    auto_select_eligible_count = 0
    for zip_code, zip_rows in sorted(rows_by_zip.items()):
        classification = classifications[zip_code]
        if classification == PAYLOAD_SINGLE_DISTRICT_READY and zip_is_auto_select_eligible(zip_rows):
            auto_select_eligible_count += 1
            continue
        for reason in ineligible_reasons(zip_rows, classification):
            ineligible_counts[reason] += 1

    multi_district_zips = {}
    multi_state_zips = {}
    for zip_code, zip_rows in sorted(rows_by_zip.items()):
        district_keys = sorted({district_key(row) for row in zip_rows if district_key(row)})
        states = sorted({row["state"] for row in zip_rows if row["state"]})
        if len(district_keys) > 1:
            multi_district_zips[zip_code] = district_keys
        if len(states) > 1:
            multi_state_zips[zip_code] = states

    missing_metadata_rows = [
        row["row_id"]
        for row in normalized_rows
        if not row_has_all_source_metadata(row)
    ]
    current_rows = [
        row
        for row in normalized_rows
        if row["source_currentness"] == "current"
    ]
    current_source_backed_rows = [
        row["row_id"]
        for row in current_rows
        if row["confidence"] in HIGH_CONFIDENCE_VALUES and row_has_all_source_metadata(row)
    ]
    fixture_sample_rows = [
        row["row_id"]
        for row in normalized_rows
        if row["source_currentness"] == "fixture_sample" or row["source_type"] == "fixture_sample"
    ]
    stale_or_unknown_rows = [
        row["row_id"]
        for row in normalized_rows
        if row["source_currentness"] == "stale_or_unknown" or not row_has_all_source_metadata(row)
    ]

    if auto_select_eligible_count and fixture_sample_rows:
        warnings.append(
            {
                "row_id": "seed",
                "field": "auto_select_eligibility",
                "message": "Fixture/sample rows are excluded from auto-select eligibility.",
            }
        )

    return {
        "row_count": len(normalized_rows),
        "unique_zip_count": len(rows_by_zip),
        "required_fields": REQUIRED_SEED_FIELDS,
        "all_rows_have_required_fields": not any(error["field"] == "required_fields" for error in errors),
        "errors": errors,
        "error_count": len(errors),
        "warnings": warnings,
        "warning_count": len(warnings),
        "valid": len(errors) == 0,
        "multi_district_zips": multi_district_zips,
        "multi_state_zips": multi_state_zips,
        "duplicate_active_source_period_keys": duplicate_keys,
        "duplicate_active_source_period_key_count": len(duplicate_keys),
        "missing_metadata_rows": missing_metadata_rows,
        "missing_metadata_count": len(missing_metadata_rows),
        "stale_or_unknown_rows": stale_or_unknown_rows,
        "stale_or_unknown_count": len(stale_or_unknown_rows),
        "fixture_sample_rows": fixture_sample_rows,
        "fixture_sample_count": len(fixture_sample_rows),
        "current_source_backed_rows": current_source_backed_rows,
        "current_source_backed_count": len(current_source_backed_rows),
        "auto_select_eligible_count": auto_select_eligible_count,
        "ineligible_counts_by_reason": dict(sorted(ineligible_counts.items())),
        "payload_classification_by_zip": classifications,
        "production_coverage_claimed": False,
        "production_coverage_statement": (
            "Seed rows are readiness inputs only; they are not production coverage unless a later "
            "approved milestone loads reviewed/source-backed rows and verifies coverage read-only."
        ),
    }


def validate_seed_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    row_id = row["row_id"]
    missing_fields = [field for field in REQUIRED_SEED_FIELDS if not row["fields_present"].get(field)]
    if missing_fields:
        errors.append(
            {
                "row_id": row_id,
                "field": "required_fields",
                "message": f"Missing required field(s): {', '.join(missing_fields)}",
            }
        )

    if not re.fullmatch(r"\d{5}", row["zip"]):
        errors.append({"row_id": row_id, "field": "zip", "message": "ZIP must be five digits."})
    if not re.fullmatch(r"[A-Z]{2}", row["state"]):
        errors.append({"row_id": row_id, "field": "state", "message": "State must be two uppercase letters."})
    if row["source_currentness"] not in SOURCE_CURRENTNESS_VALUES:
        errors.append(
            {
                "row_id": row_id,
                "field": "source_currentness",
                "message": "source_currentness is not a controlled value.",
            }
        )
    if row["confidence"] not in CONFIDENCE_VALUES:
        errors.append({"row_id": row_id, "field": "confidence", "message": "confidence is not a controlled value."})
    if row["source_currentness"] == "current":
        if not row_has_all_source_metadata(row):
            errors.append(
                {
                    "row_id": row_id,
                    "field": "source_metadata",
                    "message": "Current rows require source name/type/retrieved/effective/version metadata.",
                }
            )
        if row["confidence"] not in HIGH_CONFIDENCE_VALUES:
            errors.append(
                {
                    "row_id": row_id,
                    "field": "confidence",
                    "message": "Current rows require source_backed or reviewed confidence.",
                }
            )
    return errors


def classify_zip_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return PAYLOAD_UNSUPPORTED_ZIP

    states = {row["state"] for row in rows if row["state"]}
    district_keys = {district_key(row) for row in rows if district_key(row)}
    if len(states) > 1:
        return PAYLOAD_MULTI_STATE_ZIP
    if len(district_keys) > 1:
        return PAYLOAD_AMBIGUOUS_ZIP
    if any(row["source_currentness"] == "fixture_sample" or row["source_type"] == "fixture_sample" for row in rows):
        return PAYLOAD_FIXTURE_SAMPLE_ONLY
    if any(row["source_currentness"] != "current" or not row_has_all_source_metadata(row) for row in rows):
        return PAYLOAD_STALE_OR_UNKNOWN_SOURCE
    if any(row["confidence"] not in HIGH_CONFIDENCE_VALUES for row in rows):
        return PAYLOAD_STALE_OR_UNKNOWN_SOURCE
    return PAYLOAD_SINGLE_DISTRICT_READY


def zip_is_auto_select_eligible(rows: list[dict[str, Any]]) -> bool:
    if classify_zip_rows(rows) != PAYLOAD_SINGLE_DISTRICT_READY:
        return False
    return all(
        row["source_currentness"] == "current"
        and row["source_type"] != "fixture_sample"
        and row["confidence"] in HIGH_CONFIDENCE_VALUES
        and row_has_all_source_metadata(row)
        for row in rows
    )


def ineligible_reasons(rows: list[dict[str, Any]], classification: str) -> set[str]:
    reasons = {classification}
    if any(not row_has_all_source_metadata(row) for row in rows):
        reasons.add("missing_metadata")
    if any(row["source_currentness"] == "fixture_sample" or row["source_type"] == "fixture_sample" for row in rows):
        reasons.add("fixture_sample")
    if any(row["source_currentness"] == "stale_or_unknown" for row in rows):
        reasons.add("stale_or_unknown")
    if any(row["confidence"] not in HIGH_CONFIDENCE_VALUES for row in rows):
        reasons.add("low_or_unknown_confidence")
    return reasons


def normalize_seed_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    normalized = {
        "row_id": str(row.get("provider_record_id") or row.get("case") or index),
        "fields_present": {field: field in row for field in REQUIRED_SEED_FIELDS},
    }
    for field in REQUIRED_SEED_FIELDS:
        normalized[field] = _clean(row.get(field))
    return normalized


def row_has_all_source_metadata(row: dict[str, Any]) -> bool:
    return all(row.get(field) for field in SOURCE_METADATA_FIELDS)


def district_key(row: dict[str, Any]) -> str:
    if not row.get("state") or not row.get("district"):
        return ""
    return f"{row['state']}-{row['district']}"


def active_source_period_key(row: dict[str, Any]) -> str:
    if not row.get("zip") or not row.get("state") or not row.get("district"):
        return ""
    return "|".join(
        [
            row["zip"],
            row["state"],
            row["district"],
            row["source_name"],
            row["source_version"],
            row["valid_from"] or row["source_effective_date"],
            row["valid_to"] or "9999-12-31",
        ]
    )


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()
