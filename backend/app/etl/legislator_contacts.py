import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.db import get_connection


ALLOWED_SOURCE_TYPES = {
    "official_house_website",
    "official_senate_website",
}


@dataclass(frozen=True)
class LegislatorContactRecord:
    bioguide_id: str
    official_website_url: str | None
    contact_form_url: str | None
    phone: str | None
    source_url: str
    source_type: str
    source_retrieved_at: str


@dataclass(frozen=True)
class LegislatorContactImportResult:
    records_seen: int
    records_imported: int


def load_legislator_contacts(path: Path) -> list[LegislatorContactRecord]:
    raw_records = json.loads(path.read_text(encoding="utf-8"))
    return [_parse_record(record) for record in raw_records]


def persist_legislator_contacts(records: list[LegislatorContactRecord]) -> LegislatorContactImportResult:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        imported = 0
        for record in records:
            legislator_id = _get_legislator_id(cursor, bioguide_id=record.bioguide_id)
            if legislator_id is None:
                continue
            _upsert_legislator_contact(cursor, legislator_id=legislator_id, record=record)
            imported += 1
        connection.commit()
        return LegislatorContactImportResult(records_seen=len(records), records_imported=imported)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _parse_record(record: dict[str, Any]) -> LegislatorContactRecord:
    parsed = LegislatorContactRecord(
        bioguide_id=_required_text(record, "bioguide_id"),
        official_website_url=_optional_text(record, "official_website_url"),
        contact_form_url=_optional_text(record, "contact_form_url"),
        phone=_optional_text(record, "phone"),
        source_url=_required_text(record, "source_url"),
        source_type=_required_text(record, "source_type"),
        source_retrieved_at=_required_text(record, "source_retrieved_at"),
    )
    _validate_record(parsed)
    return parsed


def _validate_record(record: LegislatorContactRecord) -> None:
    if record.source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"Unsupported source_type: {record.source_type}")
    if not record.source_url.startswith(("http://", "https://")):
        raise ValueError("source_url must be an HTTP(S) URL")
    if not any((record.official_website_url, record.contact_form_url, record.phone)):
        raise ValueError("At least one contact field is required")

    for url in (record.official_website_url, record.contact_form_url):
        if url and not url.startswith(("http://", "https://")):
            raise ValueError("Contact URLs must be HTTP(S) URLs")


def _get_legislator_id(cursor: Any, *, bioguide_id: str) -> int | None:
    cursor.execute(
        """
        SELECT id
        FROM legislators
        WHERE bioguide_id = %s
        ORDER BY id
        LIMIT 1
        """,
        (bioguide_id,),
    )
    row = cursor.fetchone()
    return None if row is None else int(row[0])


def _upsert_legislator_contact(
    cursor: Any,
    *,
    legislator_id: int,
    record: LegislatorContactRecord,
) -> None:
    cursor.execute(
        """
        INSERT INTO legislator_contacts (
            legislator_id,
            official_website_url,
            contact_form_url,
            phone,
            source_url,
            source_type,
            source_retrieved_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (legislator_id)
        DO UPDATE SET
            official_website_url = EXCLUDED.official_website_url,
            contact_form_url = EXCLUDED.contact_form_url,
            phone = EXCLUDED.phone,
            source_url = EXCLUDED.source_url,
            source_type = EXCLUDED.source_type,
            source_retrieved_at = EXCLUDED.source_retrieved_at,
            updated_at = NOW()
        """,
        (
            legislator_id,
            record.official_website_url,
            record.contact_form_url,
            record.phone,
            record.source_url,
            record.source_type,
            record.source_retrieved_at,
        ),
    )


def _required_text(record: dict[str, Any], key: str) -> str:
    value = str(record.get(key) or "").strip()
    if not value:
        raise ValueError(f"Missing required field: {key}")
    return value


def _optional_text(record: dict[str, Any], key: str) -> str | None:
    value = str(record.get(key) or "").strip()
    return value or None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    records = load_legislator_contacts(args.input)
    if args.dry_run:
        print(f"Parsed {len(records)} legislator contact records.")
        return

    print(persist_legislator_contacts(records))


if __name__ == "__main__":
    main()
