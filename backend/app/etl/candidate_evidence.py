import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.db import get_connection


ALLOWED_EVIDENCE_TIERS = {
    "institutional_record",
    "sourced_stated_position",
    "insufficient_evidence",
}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
FORBIDDEN_TEXT = {
    "corrupt",
    "extreme",
    "radical",
    "worst",
    "best",
    "biased",
    "bought",
    "you should vote for",
    "you should vote against",
    "support this candidate",
    "oppose this candidate",
}


@dataclass(frozen=True)
class CandidateEvidenceRecord:
    external_candidate_id: str
    evidence_tier: str
    issue_domain: str | None
    statement_text: str | None
    neutral_summary: str
    confidence: str
    source_url: str
    source_type: str
    source_retrieved_at: str | None
    external_evidence_id: str


@dataclass(frozen=True)
class CandidateEvidenceImportResult:
    records_seen: int
    records_imported: int


def load_candidate_evidence(path: Path) -> list[CandidateEvidenceRecord]:
    raw_records = json.loads(path.read_text(encoding="utf-8"))
    return [_parse_record(record) for record in raw_records]


def persist_candidate_evidence(records: list[CandidateEvidenceRecord]) -> CandidateEvidenceImportResult:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        imported = 0
        for record in records:
            candidate_id = _get_race_candidate_id(cursor, external_candidate_id=record.external_candidate_id)
            if candidate_id is None:
                continue
            _upsert_candidate_evidence(cursor, candidate_id=candidate_id, record=record)
            imported += 1
        connection.commit()
        return CandidateEvidenceImportResult(records_seen=len(records), records_imported=imported)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _parse_record(record: dict[str, Any]) -> CandidateEvidenceRecord:
    parsed = CandidateEvidenceRecord(
        external_candidate_id=_required_text(record, "external_candidate_id"),
        evidence_tier=_required_text(record, "evidence_tier"),
        issue_domain=_optional_text(record, "issue_domain"),
        statement_text=_optional_text(record, "statement_text"),
        neutral_summary=_required_text(record, "neutral_summary"),
        confidence=_required_text(record, "confidence"),
        source_url=_required_text(record, "source_url"),
        source_type=_required_text(record, "source_type"),
        source_retrieved_at=_optional_text(record, "source_retrieved_at"),
        external_evidence_id=_required_text(record, "external_evidence_id"),
    )
    _validate_record(parsed)
    return parsed


def _validate_record(record: CandidateEvidenceRecord) -> None:
    if record.evidence_tier not in ALLOWED_EVIDENCE_TIERS:
        raise ValueError(f"Unsupported evidence_tier: {record.evidence_tier}")
    if record.confidence not in ALLOWED_CONFIDENCE:
        raise ValueError(f"Unsupported confidence: {record.confidence}")
    if record.evidence_tier == "sourced_stated_position" and record.confidence == "high":
        raise ValueError("sourced_stated_position evidence must remain lower confidence than recorded votes")
    if not record.source_url.startswith(("http://", "https://")):
        raise ValueError("source_url must be an HTTP(S) URL")

    combined_text = " ".join(
        value
        for value in (record.statement_text, record.neutral_summary)
        if value
    ).lower()
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in combined_text:
            raise ValueError(f"Forbidden candidate evidence language: {forbidden}")


def _get_race_candidate_id(cursor: Any, *, external_candidate_id: str) -> int | None:
    cursor.execute(
        """
        SELECT id
        FROM race_candidates
        WHERE external_candidate_id = %s
        ORDER BY id
        LIMIT 1
        """,
        (external_candidate_id,),
    )
    row = cursor.fetchone()
    return None if row is None else int(row[0])


def _upsert_candidate_evidence(
    cursor: Any,
    *,
    candidate_id: int,
    record: CandidateEvidenceRecord,
) -> None:
    cursor.execute(
        """
        INSERT INTO candidate_evidence (
            race_candidate_id,
            evidence_tier,
            issue_domain,
            statement_text,
            neutral_summary,
            confidence,
            source_url,
            source_type,
            source_retrieved_at,
            external_evidence_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (race_candidate_id, source_type, external_evidence_id)
            WHERE external_evidence_id IS NOT NULL
        DO UPDATE SET
            evidence_tier = EXCLUDED.evidence_tier,
            issue_domain = EXCLUDED.issue_domain,
            statement_text = EXCLUDED.statement_text,
            neutral_summary = EXCLUDED.neutral_summary,
            confidence = EXCLUDED.confidence,
            source_url = EXCLUDED.source_url,
            source_retrieved_at = EXCLUDED.source_retrieved_at
        """,
        (
            candidate_id,
            record.evidence_tier,
            record.issue_domain,
            record.statement_text,
            record.neutral_summary,
            record.confidence,
            record.source_url,
            record.source_type,
            record.source_retrieved_at,
            record.external_evidence_id,
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

    records = load_candidate_evidence(args.input)
    if args.dry_run:
        print(f"Parsed {len(records)} candidate evidence records.")
        return

    print(persist_candidate_evidence(records))


if __name__ == "__main__":
    main()
