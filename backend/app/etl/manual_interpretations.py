import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db import get_connection
from app.etl.congress_adapter import load_congress_bill_cache
from app.etl.fetch_sources import CONGRESS_BILL_CACHE_DIR
from app.etl.interpret import INTERPRETATION_VERSION


MANUAL_INTERPRETATION_VERSION = "manual_interpretation_v1"
CONFIDENCE_VALUES = {"low", "medium", "high"}
INTERPRETATION_STATUSES = {"interpreted", "ambiguous", "insufficient_evidence"}
VOTE_POSITIONS = {"yea", "nay", "present", "not_voting"}
FORBIDDEN_LANGUAGE = (
    "corrupt",
    "extreme",
    "radical",
    "worst",
    "best",
    "biased",
    "bought",
    "you should vote",
    "support this candidate",
    "oppose this candidate",
    "good thing",
    "bad thing",
)


@dataclass(frozen=True)
class ManualInterpretationValidationResult:
    valid_count: int
    errors: list[str]


def export_interpretation_packets(
    *,
    output_path: Path,
    legislator_ids: list[str] | None = None,
    domains: list[str] | None = None,
    limit: int = 50,
) -> dict[str, object]:
    packets = _fetch_interpretation_packets(
        legislator_ids=legislator_ids or [],
        domains=[domain.upper() for domain in domains or []],
        limit=limit,
    )
    packets = _enrich_packets_from_congress_cache(packets)
    payload = {
        "schema_version": MANUAL_INTERPRETATION_VERSION,
        "instructions": [
            "Interpret only from the official/source text in each packet.",
            "Explain what the vote appears to do; do not judge whether the outcome is good or bad.",
            "Use insufficient_evidence when the source text does not support a plain-English interpretation.",
            "Keep every claim neutral and traceable to source_basis fields.",
        ],
        "packets": packets,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "output_path": str(output_path),
        "packet_count": len(packets),
    }


def import_manual_interpretations(*, input_path: Path, reviewed_by: str = "manual") -> dict[str, object]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    records = payload.get("interpretations", [])
    validation = validate_manual_interpretations(records)
    if validation.errors:
        return {
            "imported_count": 0,
            "errors": validation.errors,
        }

    rows = [_build_import_row(record=record, reviewed_by=reviewed_by) for record in records]
    _persist_manual_interpretations(rows)
    return {
        "imported_count": len(rows),
        "errors": [],
    }


def validate_manual_interpretations(records: list[dict[str, object]]) -> ManualInterpretationValidationResult:
    errors: list[str] = []

    for index, record in enumerate(records):
        label = f"interpretations[{index}]"
        roll_call_id = record.get("roll_call_id")
        status = record.get("interpretation_status")

        if not roll_call_id:
            errors.append(f"{label}: roll_call_id is required")
        if status not in INTERPRETATION_STATUSES:
            errors.append(f"{label}: interpretation_status must be one of {sorted(INTERPRETATION_STATUSES)}")

        support_position = record.get("support_position")
        oppose_position = record.get("oppose_position")
        if status == "interpreted":
            if support_position not in VOTE_POSITIONS or oppose_position not in VOTE_POSITIONS:
                errors.append(f"{label}: interpreted records require support_position and oppose_position")
            if support_position == oppose_position:
                errors.append(f"{label}: support_position and oppose_position must differ")
        elif support_position is not None or oppose_position is not None:
            errors.append(f"{label}: non-interpreted records must leave support_position and oppose_position null")

        confidence = record.get("confidence")
        if confidence is not None and confidence not in CONFIDENCE_VALUES:
            errors.append(f"{label}: confidence must be low, medium, high, or null")

        source_basis = record.get("source_basis", [])
        if not isinstance(source_basis, list):
            errors.append(f"{label}: source_basis must be a list")

        if status == "interpreted":
            for field in ("plain_english_summary", "yea_meaning", "nay_meaning", "policy_effect"):
                if not _clean_text(record.get(field)):
                    errors.append(f"{label}: {field} is required for interpreted records")
            if not source_basis:
                errors.append(f"{label}: interpreted records require at least one source_basis item")

        for field in (
            "plain_english_summary",
            "yea_meaning",
            "nay_meaning",
            "policy_effect",
            "issue_facet",
            "uncertainty_note",
            "interpretation_reason",
        ):
            text = _clean_text(record.get(field))
            lowered = text.lower()
            for forbidden in FORBIDDEN_LANGUAGE:
                if forbidden in lowered:
                    errors.append(f"{label}: {field} contains forbidden language `{forbidden}`")

    return ManualInterpretationValidationResult(
        valid_count=len(records) if not errors else 0,
        errors=errors,
    )


def _fetch_interpretation_packets(*, legislator_ids: list[str], domains: list[str], limit: int) -> list[dict[str, object]]:
    where_clauses = ["vcf.is_eligible = TRUE"]
    params: dict[str, object] = {"limit": limit}

    if legislator_ids:
        where_clauses.append(
            """
            (
                'leg_' || trim(both '_' from regexp_replace(lower(l.name_display), '[^a-z0-9]+', '_', 'g'))
            ) = ANY(%(legislator_ids)s)
            """
        )
        params["legislator_ids"] = legislator_ids
    if domains:
        where_clauses.append("vcf.primary_domain::text = ANY(%(domains)s)")
        params["domains"] = domains

    query = f"""
        SELECT DISTINCT
            rc.id AS roll_call_id,
            rc.chamber,
            rc.congress,
            rc.rollcall_number,
            rc.vote_date,
            rc.question,
            rc.description,
            rc.source_url,
            b.congress AS bill_congress,
            b.bill_type,
            b.bill_number,
            b.title AS bill_title,
            b.summary AS bill_summary,
            b.subjects AS bill_subjects,
            vcf.primary_domain,
            vcf.eligibility_reason AS classification_reason,
            vcf.classification_version,
            vi.interpretation_status,
            vi.interpretation_reason,
            vi.plain_english_summary,
            vi.yea_meaning,
            vi.nay_meaning,
            vi.policy_effect,
            vi.issue_facet,
            vi.confidence,
            vi.uncertainty_note,
            vc.position AS member_vote,
            l.party AS member_party,
            vctx.vote_type,
            vctx.final_result,
            vctx.vote_margin,
            vctx.winning_position,
            vctx.party_vote_totals,
            vctx.member_party_majority_position,
            vctx.member_voted_with_party_majority,
            vctx.member_voted_with_winning_side,
            vctx.bipartisan_majority,
            vctx.sponsor_party,
            vctx.context_source_list,
            vctx.context_version
        FROM roll_calls rc
        JOIN bills b ON b.id = rc.bill_id
        JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        LEFT JOIN votes_cast vc ON vc.roll_call_id = rc.id
        LEFT JOIN legislators l ON l.id = vc.legislator_id
        LEFT JOIN vote_contexts vctx ON vctx.roll_call_id = rc.id AND vctx.legislator_id = l.id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY rc.vote_date DESC, rc.id DESC
        LIMIT %(limit)s
    """

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [column.name for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()

    return [_serialize_packet(row) for row in rows]


def _enrich_packets_from_congress_cache(packets: list[dict[str, object]]) -> list[dict[str, object]]:
    congress_cache = load_congress_bill_cache(CONGRESS_BILL_CACHE_DIR)
    if not congress_cache:
        return packets

    for packet in packets:
        official_text = packet.get("official_text")
        if not isinstance(official_text, dict):
            continue
        try:
            bill_key = (
                int(official_text["bill_congress"]),
                str(official_text["bill_type"]),
                int(official_text["bill_number"]),
            )
        except (KeyError, TypeError, ValueError):
            continue

        cached_bill = congress_cache.get(bill_key)
        if cached_bill is None:
            continue
        if cached_bill.get("summary"):
            official_text["bill_summary"] = cached_bill["summary"]
        if cached_bill.get("subjects"):
            official_text["bill_subjects"] = cached_bill["subjects"]
        packet["so_what_context"] = _build_so_what_context(cached_bill)

    return packets


def _build_so_what_context(cached_bill: dict[str, Any]) -> dict[str, object]:
    latest_action = cached_bill.get("latest_action")
    laws = cached_bill.get("laws") or []
    text_versions = cached_bill.get("text_versions") or []
    cbo_cost_estimates = cached_bill.get("cbo_cost_estimates") or []
    amendments = cached_bill.get("amendments") or []
    actions = cached_bill.get("actions") or []
    committees = cached_bill.get("committees") or []

    return {
        "bill_lifecycle": {
            "introduced_date": cached_bill.get("introduced_date"),
            "origin_chamber": cached_bill.get("origin_chamber"),
            "latest_action": latest_action,
            "laws": laws,
            "became_law": bool(laws)
            or (
                isinstance(latest_action, dict)
                and "became public law" in str(latest_action.get("text") or "").lower()
            ),
        },
        "practical_stakes_prompts": [
            "What government lever would change: funding, eligibility, penalties, agency authority, reporting, repeal, delay, enforcement, procurement, disclosure, or procedure?",
            "Who or what is directly affected by the source text: programs, agencies, regulated entities, legal standards, or groups of people?",
            "Where is this vote in the bill lifecycle: final passage, amendment, rule/procedure, CRA disapproval, appropriations, or another step?",
            "What cannot be concluded from the available source text?",
        ],
        "available_enrichment": {
            "bill_detail": True,
            "latest_action": latest_action is not None,
            "public_law": bool(laws),
            "cbo_cost_estimates": len(cbo_cost_estimates),
            "text_versions": len(text_versions),
            "actions": len(actions),
            "amendments": len(amendments),
            "committees": len(committees),
        },
        "cbo_cost_estimates": [
            {
                "title": estimate.get("title"),
                "description": estimate.get("description"),
                "pub_date": estimate.get("pubDate"),
                "url": estimate.get("url"),
            }
            for estimate in cbo_cost_estimates
            if isinstance(estimate, dict)
        ],
        "text_versions": text_versions[:5],
        "actions": actions[:8],
        "amendments": amendments[:12],
        "committees": committees,
        "legislation_url": cached_bill.get("legislation_url"),
    }


def _persist_manual_interpretations(rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    query = """
        INSERT INTO vote_interpretations (
            roll_call_id, interpretation_status, support_position, oppose_position,
            interpretation_reason, source_url, interpretation_version, classification_version,
            plain_english_summary, yea_meaning, nay_meaning, policy_effect, issue_facet,
            confidence, source_basis, uncertainty_note, reviewed_by, reviewed_at
        )
        VALUES (
            %(roll_call_id)s, %(interpretation_status)s, %(support_position)s, %(oppose_position)s,
            %(interpretation_reason)s, %(source_url)s, %(interpretation_version)s, %(classification_version)s,
            %(plain_english_summary)s, %(yea_meaning)s, %(nay_meaning)s, %(policy_effect)s, %(issue_facet)s,
            %(confidence)s, %(source_basis)s::jsonb, %(uncertainty_note)s, %(reviewed_by)s, %(reviewed_at)s
        )
        ON CONFLICT (roll_call_id) DO UPDATE SET
            interpretation_status = EXCLUDED.interpretation_status,
            support_position = EXCLUDED.support_position,
            oppose_position = EXCLUDED.oppose_position,
            interpretation_reason = EXCLUDED.interpretation_reason,
            source_url = EXCLUDED.source_url,
            interpretation_version = EXCLUDED.interpretation_version,
            classification_version = EXCLUDED.classification_version,
            plain_english_summary = EXCLUDED.plain_english_summary,
            yea_meaning = EXCLUDED.yea_meaning,
            nay_meaning = EXCLUDED.nay_meaning,
            policy_effect = EXCLUDED.policy_effect,
            issue_facet = EXCLUDED.issue_facet,
            confidence = EXCLUDED.confidence,
            source_basis = EXCLUDED.source_basis,
            uncertainty_note = EXCLUDED.uncertainty_note,
            reviewed_by = EXCLUDED.reviewed_by,
            reviewed_at = EXCLUDED.reviewed_at,
            updated_at = NOW()
    """

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.executemany(query, rows)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _build_import_row(*, record: dict[str, object], reviewed_by: str) -> dict[str, object]:
    return {
        "roll_call_id": record["roll_call_id"],
        "interpretation_status": record["interpretation_status"],
        "support_position": record.get("support_position"),
        "oppose_position": record.get("oppose_position"),
        "interpretation_reason": _clean_text(record.get("interpretation_reason")) or _default_reason(record),
        "source_url": record.get("source_url"),
        "interpretation_version": record.get("interpretation_version") or INTERPRETATION_VERSION,
        "classification_version": record.get("classification_version") or "v1",
        "plain_english_summary": _nullable_text(record.get("plain_english_summary")),
        "yea_meaning": _nullable_text(record.get("yea_meaning")),
        "nay_meaning": _nullable_text(record.get("nay_meaning")),
        "policy_effect": _nullable_text(record.get("policy_effect")),
        "issue_facet": _nullable_text(record.get("issue_facet")),
        "confidence": record.get("confidence"),
        "source_basis": json.dumps(record.get("source_basis", []), sort_keys=True),
        "uncertainty_note": _nullable_text(record.get("uncertainty_note")),
        "reviewed_by": reviewed_by,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }


def _serialize_packet(row: dict[str, Any]) -> dict[str, object]:
    return {
        "roll_call_id": row["roll_call_id"],
        "chamber": row["chamber"],
        "congress": row["congress"],
        "rollcall_number": row["rollcall_number"],
        "vote_date": row["vote_date"].isoformat() if hasattr(row["vote_date"], "isoformat") else row["vote_date"],
        "primary_domain": row["primary_domain"],
        "classification_reason": row["classification_reason"],
        "classification_version": row["classification_version"],
        "official_text": {
            "bill_title": row["bill_title"],
            "bill_congress": row["bill_congress"],
            "bill_type": row["bill_type"],
            "bill_number": row["bill_number"],
            "bill_summary": row["bill_summary"],
            "bill_subjects": row["bill_subjects"] or [],
            "question": row["question"],
            "description": row["description"],
            "source_url": row["source_url"],
        },
        "vote_context": {
            "member_vote": row["member_vote"],
            "member_party": row["member_party"],
            "vote_type": row["vote_type"],
            "final_result": row["final_result"],
            "vote_margin": row["vote_margin"],
            "winning_position": row["winning_position"],
            "party_vote_totals": row["party_vote_totals"] or {},
            "member_party_majority_position": row["member_party_majority_position"],
            "member_voted_with_party_majority": row["member_voted_with_party_majority"],
            "member_voted_with_winning_side": row["member_voted_with_winning_side"],
            "bipartisan_majority": row["bipartisan_majority"],
            "sponsor_party": row["sponsor_party"],
            "context_source_list": row["context_source_list"] or [],
            "context_version": row["context_version"],
        },
        "current_interpretation": {
            "interpretation_status": row["interpretation_status"],
            "interpretation_reason": row["interpretation_reason"],
            "plain_english_summary": row["plain_english_summary"],
            "yea_meaning": row["yea_meaning"],
            "nay_meaning": row["nay_meaning"],
            "policy_effect": row["policy_effect"],
            "issue_facet": row["issue_facet"],
            "confidence": row["confidence"],
            "uncertainty_note": row["uncertainty_note"],
        },
        "draft_template": {
            "roll_call_id": row["roll_call_id"],
            "interpretation_status": "interpreted | ambiguous | insufficient_evidence",
            "support_position": "yea | nay | null",
            "oppose_position": "yea | nay | null",
            "vote_type": "final_passage | amendment | rule | motion | concurrence | procedural | nomination | appropriations | cra_disapproval | other",
            "what_happened": "",
            "why_it_mattered": "",
            "member_vote_context": "",
            "what_not_to_infer": "",
            "practical_mechanism": "funding | eligibility | penalties | agency_authority | reporting | repeal | delay | enforcement | procurement | disclosure | procedure | other",
            "direct_stakes": "",
            "evidence_boundary": "",
            "so_what_summary": "",
            "plain_english_summary": "",
            "yea_meaning": "",
            "nay_meaning": "",
            "policy_effect": "",
            "issue_facet": "",
            "confidence": "low | medium | high | null",
            "source_basis": [],
            "uncertainty_note": "",
            "interpretation_reason": "",
            "source_url": row["source_url"],
            "classification_version": row["classification_version"],
            "interpretation_version": INTERPRETATION_VERSION,
        },
    }


def _default_reason(record: dict[str, object]) -> str:
    if record.get("interpretation_status") == "interpreted":
        return "Manual source-grounded interpretation reviewed from official roll-call and bill text."
    return "Manual review found insufficient source-grounded detail for a plain-English interpretation."


def _nullable_text(value: object) -> str | None:
    text = _clean_text(value)
    return text or None


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export or import manual vote interpretation batches.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--output", required=True)
    export_parser.add_argument("--legislator-id", action="append", default=[])
    export_parser.add_argument("--domain", action="append", default=[])
    export_parser.add_argument("--limit", type=int, default=50)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--input", required=True)
    import_parser.add_argument("--reviewed-by", default="manual")

    args = parser.parse_args()

    if args.command == "export":
        result = export_interpretation_packets(
            output_path=Path(args.output),
            legislator_ids=args.legislator_id,
            domains=args.domain,
            limit=args.limit,
        )
    else:
        result = import_manual_interpretations(
            input_path=Path(args.input),
            reviewed_by=args.reviewed_by,
        )

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
