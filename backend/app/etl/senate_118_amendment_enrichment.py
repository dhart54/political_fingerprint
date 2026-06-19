from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.db import get_connection
from app.etl.evidence_118_expansion import DOMAIN_RULES_118, audit_118_rows
from app.etl.fetch_sources import resolve_congress_api_key
from app.etl.manual_interpretations import validate_manual_interpretations
from app.etl.session2_evidence_expansion import _sql_domain, _sql_json, _sql_value, _sql_vote_position


REPO_ROOT = Path(__file__).resolve().parents[3]
SENATE_XML_DIR = REPO_ROOT / "backend" / "data_sources" / "senate_xml"
AMENDMENT_CACHE_DIR = REPO_ROOT / "backend" / "data_sources" / "congress" / "amendments"
PACKET_PATH = REPO_ROOT / "docs" / "review_packets" / "senate_118_amendment_source_packets.json"
CLASSIFICATION_ROLLBACK_PATH = (
    REPO_ROOT / "docs" / "review_packets" / "senate_118_amendment_classification_rollback.sql"
)
INTERPRETATION_ROLLBACK_PATH = (
    REPO_ROOT / "docs" / "review_packets" / "senate_118_amendment_interpretation_rollback.sql"
)

CLASSIFICATION_VERSION = "v1"
REVIEWED_BY = "senate_118_amendment_source_enrichment"
CLASSIFICATION_APPROVAL = (
    "Approve bounded production classification update for 118th Senate amendment source enrichment, "
    "limited to source-packet-approved 118th Senate roll_call_ids, with no fact-table writes, "
    "procedural rows non-counting, rollback generated before write, 119th preserved, not-voting "
    "excluded, and no methodology changes."
)
INTERPRETATION_APPROVAL = (
    "Approve bounded production interpretation update for 118th Senate amendment source enrichment, "
    "limited to source-packet-approved 118th Senate roll_call_ids, with substantive rows grounded in "
    "direct amendment purpose, procedural rows non-counting with null support/opposition, rollback "
    "generated before write, 119th preserved, not-voting excluded, and no methodology changes."
)

GENERIC_PURPOSE_MARKERS = (
    "no statement of purpose",
    "in the nature of a substitute",
    "to improve the bill",
    "to require a certification",
    "to provide for a manager's amendment",
)
PROCEDURAL_QUESTIONS = (
    "cloture",
    "motion to table",
    "on the motion",
)


@dataclass(frozen=True)
class AmendmentPacket:
    roll_call_id: int
    session: int
    roll_number: int
    question: str
    description: str
    bill_title: str
    source_url: str | None
    vote_type: str
    amendment_number: str | None
    amendment_purpose: str | None
    congressgov_url: str | None
    source_status: str
    proposed_category: str
    proposed_domain: str | None
    proposed_facet: str | None
    defer_reason: str | None
    source_basis: list[str]
    score_breakdown: dict[str, Any]


def audit_deferred_amendments() -> dict[str, Any]:
    audit = audit_118_rows()["opportunity_distribution"]
    rows = _load_118_amendment_rows()
    distribution = Counter(f"{row['chamber']}:s{row['session']}:{row['vote_type']}" for row in rows)
    senate_rows = [row for row in rows if row["chamber"] == "senate"]
    return {
        "deferred_amendment_bucket": int(audit.get("defer_amendment_needs_direct_purpose", 0)),
        "bucket_distribution": dict(sorted(distribution.items())),
        "senate_loaded_amendment_roll_calls": len(senate_rows),
        "senate_sessions": dict(Counter(f"s{row['session']}" for row in senate_rows)),
        "note": (
            "The 588 deferred amendment bucket is the full 118th roll-call amendment bucket: "
            "566 House amendment roll calls plus 22 Senate amendment roll calls."
        ),
    }


def build_source_packets(*, fetch_missing: bool = False) -> dict[str, Any]:
    rows = _load_118_senate_amendment_rows()
    packets = [_packet_for_row(row, fetch_missing=fetch_missing) for row in rows]
    payload = {
        "schema_version": "senate_118_amendment_source_packets_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classification_version": CLASSIFICATION_VERSION,
        "guardrails": [
            "Direct amendment number and purpose are required for substantive interpretation.",
            "Parent measure context is supporting context only.",
            "Procedural motions remain non-counting.",
            "Rows with generic or unavailable amendment purpose remain deferred.",
            "No PN nominations or treaty/executive votes are included.",
        ],
        "deferred_amendment_audit": audit_deferred_amendments(),
        "summary": _packet_summary(packets),
        "top_opportunity_families": _rank_families(packets)[:10],
        "packets": [_packet_dict(packet) for packet in packets],
    }
    PACKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    PACKET_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(PACKET_PATH), "summary": payload["summary"], "top_opportunity_families": payload["top_opportunity_families"]}


def dry_run(packet_path: Path = PACKET_PATH) -> dict[str, Any]:
    payload = _load_json(packet_path)
    packets = payload["packets"]
    write_packets = [packet for packet in packets if packet["proposed_category"] in {"substantive_interpretation", "procedural_context"}]
    substantive = [packet for packet in write_packets if packet["proposed_category"] == "substantive_interpretation"]
    procedural = [packet for packet in write_packets if packet["proposed_category"] == "procedural_context"]
    existing = _load_existing_rows([int(packet["roll_call_id"]) for packet in write_packets])
    errors: list[str] = []
    for packet in write_packets:
        if packet["source_status"] != "direct_purpose_available":
            errors.append(f"Roll {packet['roll_number']} selected without direct purpose.")
        if packet["proposed_category"] == "substantive_interpretation" and not packet.get("proposed_domain"):
            errors.append(f"Roll {packet['roll_number']} substantive packet lacks domain.")
        if packet["proposed_category"] == "procedural_context" and packet.get("support_position") is not None:
            errors.append(f"Roll {packet['roll_number']} procedural packet has support position.")
    return {
        "target_rows": len(write_packets),
        "classification_updates": _changed_classification_count(write_packets, existing),
        "interpretation_updates": _changed_interpretation_count(write_packets, existing),
        "substantive_rows": len(substantive),
        "procedural_context_rows": len(procedural),
        "deferred_rows": len(packets) - len(write_packets),
        "target_roll_call_ids": [int(packet["roll_call_id"]) for packet in write_packets],
        "domain_distribution": dict(Counter(packet["proposed_domain"] for packet in substantive).most_common()),
        "errors": errors,
        "safe_to_write": not errors,
    }


def write_classification_rollback(packet_path: Path = PACKET_PATH, output: Path = CLASSIFICATION_ROLLBACK_PATH) -> dict[str, Any]:
    packets = _write_packets(packet_path)
    rows = _load_existing_rows([int(packet["roll_call_id"]) for packet in packets])
    lines = [
        "-- Rollback for 118th Senate amendment source-enrichment classifications.",
        "-- Scope: exact source-packet-approved roll_call_ids only.",
        "BEGIN;",
        "",
    ]
    for row in rows.values():
        lines.extend(_classification_rollback_sql(row))
    lines.append("COMMIT;")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(output), "rows": len(rows)}


def write_interpretation_rollback(packet_path: Path = PACKET_PATH, output: Path = INTERPRETATION_ROLLBACK_PATH) -> dict[str, Any]:
    packets = _write_packets(packet_path)
    rows = _load_existing_rows([int(packet["roll_call_id"]) for packet in packets])
    lines = [
        "-- Rollback for 118th Senate amendment source-enrichment interpretations.",
        "-- Scope: exact source-packet-approved roll_call_ids only.",
        "BEGIN;",
        "",
    ]
    for row in rows.values():
        lines.extend(_interpretation_rollback_sql(row))
    lines.append("COMMIT;")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(output), "rows": len(rows)}


def write_classifications(*, approval_phrase: str, packet_path: Path = PACKET_PATH) -> dict[str, Any]:
    if approval_phrase != CLASSIFICATION_APPROVAL:
        raise ValueError("Classification approval phrase does not match.")
    result = dry_run(packet_path)
    if result["errors"]:
        raise ValueError(f"Dry-run failed: {result['errors']}")
    packets = _write_packets(packet_path)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            updated = _update_classifications(cursor, packets)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"updated_classifications": updated, "dry_run": result}


def write_interpretations(*, approval_phrase: str, packet_path: Path = PACKET_PATH) -> dict[str, Any]:
    if approval_phrase != INTERPRETATION_APPROVAL:
        raise ValueError("Interpretation approval phrase does not match.")
    result = dry_run(packet_path)
    if result["errors"]:
        raise ValueError(f"Dry-run failed: {result['errors']}")
    packets = _write_packets(packet_path)
    validation = validate_manual_interpretations([_interpretation_record(packet) for packet in packets])
    if validation.errors:
        raise ValueError(f"Interpretation validation failed: {validation.errors}")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            updated = _update_interpretations(cursor, packets)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"updated_interpretations": updated, "dry_run": result}


def post_validate(packet_path: Path = PACKET_PATH) -> dict[str, Any]:
    packets = _write_packets(packet_path)
    ids = [int(packet["roll_call_id"]) for packet in packets]
    if not ids:
        return {"target_rows": 0, "errors": []}
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE rc.congress = 118 AND rc.chamber = 'senate') AS target_rows,
                  COUNT(*) FILTER (WHERE rc.congress <> 118 OR rc.chamber <> 'senate') AS non_target_rows,
                  COUNT(*) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible_rows,
                  COUNT(*) FILTER (WHERE vi.interpretation_status = 'interpreted') AS interpreted_rows,
                  COUNT(*) FILTER (WHERE vi.support_position IS NOT NULL) AS support_non_null,
                  COUNT(*) FILTER (WHERE vi.oppose_position IS NOT NULL) AS oppose_non_null,
                  COUNT(*) FILTER (
                    WHERE vi.interpretation_status = 'insufficient_evidence'
                      AND vi.support_position IS NULL
                      AND vi.oppose_position IS NULL
                  ) AS procedural_non_counting
                FROM roll_calls rc
                JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
                WHERE rc.id = ANY(%s)
                """,
                (ids,),
            )
            row = cursor.fetchone()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM votes_cast vc
                JOIN vote_interpretations vi ON vi.roll_call_id = vc.roll_call_id
                WHERE vi.roll_call_id = ANY(%s)
                  AND vc.position = 'not_voting'
                  AND vc.position IN (vi.support_position, vi.oppose_position)
                """,
                (ids,),
            )
            not_voting_counted = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM vote_classifications vcf
                JOIN roll_calls rc ON rc.id = vcf.roll_call_id
                WHERE rc.congress = 119
                """,
            )
            classifications_119 = int(cursor.fetchone()[0])
    finally:
        connection.close()
    errors = []
    if int(row[1]) != 0:
        errors.append("Target set includes non-118 Senate rows.")
    if not_voting_counted != 0:
        errors.append("Not-voting rows counted as support/opposition.")
    return {
        "target_rows": int(row[0]),
        "non_target_rows": int(row[1]),
        "eligible_rows": int(row[2]),
        "interpreted_rows": int(row[3]),
        "support_non_null": int(row[4]),
        "oppose_non_null": int(row[5]),
        "procedural_non_counting": int(row[6]),
        "not_voting_counted_as_support_or_oppose": not_voting_counted,
        "classifications_119_reference_count": classifications_119,
        "errors": errors,
    }


def _load_118_amendment_rows() -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT rc.id AS roll_call_id, rc.chamber, rc.session, rc.rollcall_number,
                       COALESCE(vctx.vote_type, 'unknown') AS vote_type
                FROM roll_calls rc
                JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                LEFT JOIN vote_contexts vctx ON vctx.roll_call_id = rc.id
                WHERE rc.congress = 118
                  AND COALESCE(vctx.vote_type, 'unknown') = 'amendment'
                ORDER BY rc.chamber, rc.session, rc.rollcall_number
                """
            )
            columns = [column.name for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _load_118_senate_amendment_rows() -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT
                    rc.id AS roll_call_id,
                    rc.session,
                    rc.rollcall_number,
                    rc.question,
                    rc.description,
                    rc.source_url,
                    COALESCE(b.title, '') AS bill_title,
                    COALESCE(vctx.vote_type, 'unknown') AS vote_type,
                    vcf.is_eligible,
                    vcf.eligibility_reason,
                    vcf.primary_domain::text,
                    vi.interpretation_status::text
                FROM roll_calls rc
                JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
                LEFT JOIN vote_contexts vctx ON vctx.roll_call_id = rc.id
                LEFT JOIN bills b ON b.id = rc.bill_id
                WHERE rc.congress = 118
                  AND rc.chamber = 'senate'
                  AND COALESCE(vctx.vote_type, 'unknown') = 'amendment'
                ORDER BY rc.session, rc.rollcall_number
                """
            )
            columns = [column.name for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _packet_for_row(row: dict[str, Any], *, fetch_missing: bool) -> AmendmentPacket:
    xml = _load_senate_xml(session=int(row["session"]), roll_number=int(row["rollcall_number"]))
    amendment_number = _extract_amendment_number(row=row, xml=xml)
    amendment = _load_or_fetch_amendment(amendment_number, fetch_missing=fetch_missing) if amendment_number else None
    purpose = _purpose_from_sources(xml=xml, amendment=amendment)
    source_status = "direct_purpose_available" if purpose and not _purpose_is_generic(purpose) else "direct_purpose_missing_or_generic"
    category = "defer"
    defer_reason = None
    domain = None
    facet = None
    score: dict[str, Any] = {}
    if source_status != "direct_purpose_available":
        defer_reason = "defer_amendment_purpose_missing_or_generic"
    else:
        domain, score = _domain_from_text(" ".join([purpose or "", str(row.get("description") or ""), str(row.get("bill_title") or "")]))
        if not domain:
            defer_reason = "defer_no_safe_issue_domain"
        elif _is_procedural_amendment_action(str(row.get("question") or ""), str(row.get("description") or "")):
            category = "procedural_context"
            facet = "procedural_amendment_context"
        else:
            category = "substantive_interpretation"
            facet = domain.lower()
    return AmendmentPacket(
        roll_call_id=int(row["roll_call_id"]),
        session=int(row["session"]),
        roll_number=int(row["rollcall_number"]),
        question=str(row.get("question") or ""),
        description=str(row.get("description") or ""),
        bill_title=str(row.get("bill_title") or ""),
        source_url=None if row.get("source_url") is None else str(row["source_url"]),
        vote_type=str(row.get("vote_type") or ""),
        amendment_number=amendment_number,
        amendment_purpose=purpose,
        congressgov_url=_congressgov_public_url(amendment_number) if amendment_number else None,
        source_status=source_status,
        proposed_category=category,
        proposed_domain=domain,
        proposed_facet=facet,
        defer_reason=defer_reason,
        source_basis=_source_basis(row=row, amendment_number=amendment_number, purpose=purpose, amendment=amendment),
        score_breakdown=score,
    )


def _load_senate_xml(*, session: int, roll_number: int) -> dict[str, str | None]:
    path = SENATE_XML_DIR / f"118_{session}" / f"vote_{roll_number:03d}.xml"
    root = ElementTree.parse(path).getroot()
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "question": root.findtext("question"),
        "vote_title": root.findtext("vote_title"),
        "vote_question_text": root.findtext("vote_question_text"),
        "document_type": root.findtext("document/document_type"),
        "document_name": root.findtext("document/document_name"),
        "amendment_number": root.findtext("amendment/amendment_number"),
        "amendment_to_amendment_number": root.findtext("amendment/amendment_to_amendment_number"),
        "amendment_purpose": root.findtext("amendment/amendment_purpose"),
    }


def _extract_amendment_number(*, row: dict[str, Any], xml: dict[str, str | None]) -> str | None:
    xml_number = (xml.get("amendment_number") or "").strip()
    if xml_number:
        return _normalize_amendment_number(xml_number)
    text = " ".join(str(value or "") for value in (row.get("description"), row.get("bill_title"), xml.get("vote_title"), xml.get("vote_question_text")))
    patterns = (
        r"\bAmdt\.?\s*(?:No\.?|N\.)?\s*(\d{1,5})\b",
        r"\bAmendment\s*(?:No\.?|N\.)?\s*(\d{1,5})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return f"S.Amdt. {int(match.group(1))}"
    return None


def _normalize_amendment_number(value: str) -> str:
    match = re.search(r"(\d{1,5})", value)
    if not match:
        return value.strip()
    return f"S.Amdt. {int(match.group(1))}"


def _load_or_fetch_amendment(amendment_number: str, *, fetch_missing: bool) -> dict[str, Any] | None:
    match = re.search(r"(\d{1,5})", amendment_number)
    if not match:
        return None
    number = int(match.group(1))
    path = AMENDMENT_CACHE_DIR / f"118_samdt_{number}.json"
    if path.exists():
        return _load_json(path).get("amendment")
    if not fetch_missing:
        return None
    api_key = resolve_congress_api_key()
    url = "https://api.congress.gov/v3/amendment/118/samdt/%d?%s" % (
        number,
        urlencode({"format": "json", "api_key": api_key}),
    )
    with urlopen(Request(url, headers={"User-Agent": "political-fingerprint/0.1"}), timeout=30) as response:
        payload = json.loads(response.read())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload.get("amendment")


def _purpose_from_sources(*, xml: dict[str, str | None], amendment: dict[str, Any] | None) -> str | None:
    congress_purpose = (amendment or {}).get("purpose")
    if isinstance(congress_purpose, str) and congress_purpose.strip():
        return congress_purpose.strip()
    xml_purpose = (xml.get("amendment_purpose") or "").strip()
    if xml_purpose:
        return xml_purpose
    return None


def _purpose_is_generic(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or any(marker in lowered for marker in GENERIC_PURPOSE_MARKERS)


def _is_procedural_amendment_action(question: str, description: str) -> bool:
    text = f"{question} {description}".lower()
    return any(marker in text for marker in PROCEDURAL_QUESTIONS) and "on the amendment" not in question.lower()


def _domain_from_text(text: str) -> tuple[str | None, dict[str, Any]]:
    lowered = text.lower()
    hits: list[tuple[int, str, list[str]]] = []
    for domain, terms in DOMAIN_RULES_118:
        matched = [term for term in terms if term in lowered]
        if matched:
            hits.append((len(matched), domain, matched))
    if not hits:
        return None, {}
    hits.sort(key=lambda item: (-item[0], item[1]))
    if len(hits) > 1 and hits[0][0] == hits[1][0]:
        return None, {domain: {"keyword_match": len(matched), "matched_terms": matched} for _, domain, matched in hits}
    _, domain, matched = hits[0]
    return domain, {domain: {"senate_118_amendment_source_match": len(matched) * 2, "matched_terms": matched}}


def _source_basis(*, row: dict[str, Any], amendment_number: str | None, purpose: str | None, amendment: dict[str, Any] | None) -> list[str]:
    basis = [f"Official Senate roll {row['session']}-{int(row['rollcall_number']):03d} question/title"]
    if amendment_number:
        basis.append(f"Direct amendment identity: {amendment_number}")
    if purpose and not _purpose_is_generic(purpose):
        basis.append("Direct amendment purpose from Congress.gov amendment record or Senate XML")
    if amendment and amendment.get("latestAction"):
        basis.append("Congress.gov latest amendment action")
    return basis


def _congressgov_public_url(amendment_number: str) -> str:
    number = int(re.search(r"(\d{1,5})", amendment_number).group(1))
    return f"https://www.congress.gov/amendment/118th-congress/senate-amendment/{number}"


def _packet_dict(packet: AmendmentPacket) -> dict[str, Any]:
    return {
        "roll_call_id": packet.roll_call_id,
        "session": packet.session,
        "roll_number": packet.roll_number,
        "question": packet.question,
        "description": packet.description,
        "bill_title": packet.bill_title,
        "source_url": packet.source_url,
        "vote_type": packet.vote_type,
        "amendment_number": packet.amendment_number,
        "amendment_purpose": packet.amendment_purpose,
        "congressgov_url": packet.congressgov_url,
        "source_status": packet.source_status,
        "proposed_category": packet.proposed_category,
        "proposed_domain": packet.proposed_domain,
        "proposed_facet": packet.proposed_facet,
        "defer_reason": packet.defer_reason,
        "source_basis": packet.source_basis,
        "score_breakdown": packet.score_breakdown,
    }


def _packet_summary(packets: list[AmendmentPacket]) -> dict[str, Any]:
    return {
        "loaded_118_senate_amendment_roll_calls": len(packets),
        "source_status": dict(Counter(packet.source_status for packet in packets).most_common()),
        "proposed_category": dict(Counter(packet.proposed_category for packet in packets).most_common()),
        "proposed_domain": dict(Counter(packet.proposed_domain for packet in packets if packet.proposed_domain).most_common()),
        "defer_reasons": dict(Counter(packet.defer_reason for packet in packets if packet.defer_reason).most_common()),
    }


def _rank_families(packets: list[AmendmentPacket]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for packet in packets:
        family = _family_key(packet)
        group = groups.setdefault(
            family,
            {
                "family": family,
                "rows": 0,
                "proposed_category": packet.proposed_category,
                "domain": packet.proposed_domain,
                "source_strength": "direct amendment purpose" if packet.source_status == "direct_purpose_available" else "insufficient direct purpose",
                "trust_risk": _trust_risk(packet),
                "decision": "defer" if packet.proposed_category == "defer" else packet.proposed_category,
                "examples": [],
            },
        )
        group["rows"] += 1
        if len(group["examples"]) < 5:
            group["examples"].append(
                {
                    "roll_call_id": packet.roll_call_id,
                    "session": packet.session,
                    "roll_number": packet.roll_number,
                    "description": packet.description,
                    "amendment_number": packet.amendment_number,
                    "amendment_purpose": packet.amendment_purpose,
                }
            )
    return sorted(groups.values(), key=lambda item: (-_family_score(item), -int(item["rows"]), str(item["family"])))


def _family_key(packet: AmendmentPacket) -> str:
    if packet.proposed_category == "defer":
        return f"{packet.defer_reason}:{packet.vote_type}"
    return f"{packet.proposed_category}:{packet.proposed_domain}:{packet.vote_type}"


def _trust_risk(packet: AmendmentPacket) -> str:
    if packet.source_status != "direct_purpose_available":
        return "high"
    if packet.proposed_category == "procedural_context":
        return "medium"
    return "low"


def _family_score(group: dict[str, Any]) -> int:
    score = int(group["rows"])
    if group["source_strength"] == "direct amendment purpose":
        score += 10
    if group["decision"] == "substantive_interpretation":
        score += 8
    elif group["decision"] == "procedural_context":
        score += 4
    if group["trust_risk"] == "high":
        score -= 10
    return score


def _write_packets(packet_path: Path) -> list[dict[str, Any]]:
    payload = _load_json(packet_path)
    return [
        packet
        for packet in payload["packets"]
        if packet["proposed_category"] in {"substantive_interpretation", "procedural_context"}
    ]


def _load_existing_rows(ids: list[int]) -> dict[int, dict[str, Any]]:
    if not ids:
        return {}
    connection = get_connection()
    try:
        connection.execute("SET default_transaction_read_only = on")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rc.id AS roll_call_id,
                    vcf.is_eligible,
                    vcf.eligibility_reason,
                    vcf.primary_domain::text,
                    vcf.score_breakdown,
                    vcf.classification_version,
                    vi.interpretation_status::text,
                    vi.support_position::text,
                    vi.oppose_position::text,
                    vi.interpretation_reason,
                    vi.source_url AS interpretation_source_url,
                    vi.interpretation_version,
                    vi.classification_version AS interpretation_classification_version,
                    vi.plain_english_summary,
                    vi.yea_meaning,
                    vi.nay_meaning,
                    vi.policy_effect,
                    vi.issue_facet,
                    vi.confidence,
                    vi.source_basis,
                    vi.uncertainty_note,
                    vi.what_happened,
                    vi.why_it_mattered,
                    vi.member_vote_context,
                    vi.what_not_to_infer,
                    vi.reviewed_by
                FROM roll_calls rc
                JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
                WHERE rc.id = ANY(%s)
                ORDER BY rc.id
                """,
                (ids,),
            )
            columns = [column.name for column in cursor.description]
            return {int(row[0]): dict(zip(columns, row)) for row in cursor.fetchall()}
    finally:
        connection.close()


def _changed_classification_count(packets: list[dict[str, Any]], existing: dict[int, dict[str, Any]]) -> int:
    changed = 0
    for packet in packets:
        row = existing[int(packet["roll_call_id"])]
        if (
            row["is_eligible"] is not True
            or row["eligibility_reason"] != _eligibility_reason(packet)
            or row["primary_domain"] != packet["proposed_domain"]
            or row["score_breakdown"] != packet["score_breakdown"]
            or row["classification_version"] != CLASSIFICATION_VERSION
        ):
            changed += 1
    return changed


def _changed_interpretation_count(packets: list[dict[str, Any]], existing: dict[int, dict[str, Any]]) -> int:
    changed = 0
    for packet in packets:
        row = existing[int(packet["roll_call_id"])]
        record = _interpretation_record(packet)
        for field in (
            "interpretation_status",
            "support_position",
            "oppose_position",
            "plain_english_summary",
            "yea_meaning",
            "nay_meaning",
            "policy_effect",
            "issue_facet",
            "confidence",
            "uncertainty_note",
            "what_happened",
            "why_it_mattered",
            "member_vote_context",
            "what_not_to_infer",
        ):
            if _normalize(row.get(field)) != _normalize(record.get(field)):
                changed += 1
                break
    return changed


def _update_classifications(cursor, packets: list[dict[str, Any]]) -> int:
    cursor.executemany(
        """
        WITH next_values AS (
            SELECT TRUE AS is_eligible,
                   %s AS eligibility_reason,
                   %s::issue_domain AS primary_domain,
                   %s::jsonb AS score_breakdown,
                   %s AS classification_version
        )
        UPDATE vote_classifications vcf
        SET is_eligible = next_values.is_eligible,
            eligibility_reason = next_values.eligibility_reason,
            primary_domain = next_values.primary_domain,
            score_breakdown = next_values.score_breakdown,
            classification_version = next_values.classification_version,
            updated_at = NOW()
        FROM next_values, roll_calls rc
        WHERE vcf.roll_call_id = %s
          AND rc.id = vcf.roll_call_id
          AND rc.congress = 118
          AND rc.chamber = 'senate'
          AND (
            vcf.is_eligible IS DISTINCT FROM next_values.is_eligible
            OR vcf.eligibility_reason IS DISTINCT FROM next_values.eligibility_reason
            OR vcf.primary_domain IS DISTINCT FROM next_values.primary_domain
            OR vcf.score_breakdown IS DISTINCT FROM next_values.score_breakdown
            OR vcf.classification_version IS DISTINCT FROM next_values.classification_version
          )
        """,
        [
            (
                _eligibility_reason(packet),
                packet["proposed_domain"],
                json.dumps(packet["score_breakdown"], sort_keys=True),
                CLASSIFICATION_VERSION,
                int(packet["roll_call_id"]),
            )
            for packet in packets
        ],
    )
    return max(cursor.rowcount, 0)


def _update_interpretations(cursor, packets: list[dict[str, Any]]) -> int:
    cursor.executemany(
        """
        WITH next_values AS (
            SELECT
                %s::vote_interpretation_status AS interpretation_status,
                %s::vote_position AS support_position,
                %s::vote_position AS oppose_position,
                %s AS interpretation_reason,
                %s AS source_url,
                'interpretation_v1' AS interpretation_version,
                %s AS classification_version,
                %s AS plain_english_summary,
                %s AS yea_meaning,
                %s AS nay_meaning,
                %s AS policy_effect,
                %s AS issue_facet,
                %s AS confidence,
                %s::jsonb AS source_basis,
                %s AS uncertainty_note,
                %s AS what_happened,
                %s AS why_it_mattered,
                %s AS member_vote_context,
                %s AS what_not_to_infer
        )
        UPDATE vote_interpretations vi
        SET interpretation_status = next_values.interpretation_status,
            support_position = next_values.support_position,
            oppose_position = next_values.oppose_position,
            interpretation_reason = next_values.interpretation_reason,
            source_url = next_values.source_url,
            interpretation_version = next_values.interpretation_version,
            classification_version = next_values.classification_version,
            plain_english_summary = next_values.plain_english_summary,
            yea_meaning = next_values.yea_meaning,
            nay_meaning = next_values.nay_meaning,
            policy_effect = next_values.policy_effect,
            issue_facet = next_values.issue_facet,
            confidence = next_values.confidence,
            source_basis = next_values.source_basis,
            uncertainty_note = next_values.uncertainty_note,
            reviewed_by = %s,
            reviewed_at = NOW(),
            what_happened = next_values.what_happened,
            why_it_mattered = next_values.why_it_mattered,
            member_vote_context = next_values.member_vote_context,
            what_not_to_infer = next_values.what_not_to_infer,
            updated_at = NOW()
        FROM next_values, roll_calls rc
        WHERE vi.roll_call_id = %s
          AND rc.id = vi.roll_call_id
          AND rc.congress = 118
          AND rc.chamber = 'senate'
          AND (
            vi.interpretation_status IS DISTINCT FROM next_values.interpretation_status
            OR vi.support_position IS DISTINCT FROM next_values.support_position
            OR vi.oppose_position IS DISTINCT FROM next_values.oppose_position
            OR vi.plain_english_summary IS DISTINCT FROM next_values.plain_english_summary
            OR vi.yea_meaning IS DISTINCT FROM next_values.yea_meaning
            OR vi.nay_meaning IS DISTINCT FROM next_values.nay_meaning
            OR vi.policy_effect IS DISTINCT FROM next_values.policy_effect
            OR vi.issue_facet IS DISTINCT FROM next_values.issue_facet
            OR vi.confidence IS DISTINCT FROM next_values.confidence
            OR vi.source_basis IS DISTINCT FROM next_values.source_basis
            OR vi.uncertainty_note IS DISTINCT FROM next_values.uncertainty_note
            OR vi.what_happened IS DISTINCT FROM next_values.what_happened
            OR vi.why_it_mattered IS DISTINCT FROM next_values.why_it_mattered
            OR vi.member_vote_context IS DISTINCT FROM next_values.member_vote_context
            OR vi.what_not_to_infer IS DISTINCT FROM next_values.what_not_to_infer
          )
        """,
        [_interpretation_params(packet) for packet in packets],
    )
    return max(cursor.rowcount, 0)


def _eligibility_reason(packet: dict[str, Any]) -> str:
    return "procedural_context" if packet["proposed_category"] == "procedural_context" else "policy_vote"


def _interpretation_params(packet: dict[str, Any]) -> tuple[Any, ...]:
    record = _interpretation_record(packet)
    return (
        record["interpretation_status"],
        record["support_position"],
        record["oppose_position"],
        record["interpretation_reason"],
        record["source_url"],
        CLASSIFICATION_VERSION,
        record["plain_english_summary"],
        record["yea_meaning"],
        record["nay_meaning"],
        record["policy_effect"],
        record["issue_facet"],
        record["confidence"],
        json.dumps(record["source_basis"], sort_keys=True),
        record["uncertainty_note"],
        record["what_happened"],
        record["why_it_mattered"],
        record["member_vote_context"],
        record["what_not_to_infer"],
        REVIEWED_BY,
        int(packet["roll_call_id"]),
    )


def _interpretation_record(packet: dict[str, Any]) -> dict[str, Any]:
    amendment = packet["amendment_number"]
    purpose = packet["amendment_purpose"]
    if packet["proposed_category"] == "procedural_context":
        summary = f"This was a procedural Senate action connected to {amendment}: {purpose}"
        return {
            "roll_call_id": packet["roll_call_id"],
            "interpretation_status": "insufficient_evidence",
            "support_position": None,
            "oppose_position": None,
            "interpretation_reason": "Source-grounded procedural context; support/opposition meaning is not inferred.",
            "source_url": packet["source_url"] or packet["congressgov_url"],
            "plain_english_summary": summary,
            "yea_meaning": None,
            "nay_meaning": None,
            "policy_effect": None,
            "issue_facet": packet["proposed_facet"],
            "confidence": "medium",
            "source_basis": packet["source_basis"],
            "uncertainty_note": "This row is visible for context but remains non-counting because the roll-call action is procedural.",
            "what_happened": summary,
            "why_it_mattered": "It helps explain Senate floor process around an amendment without treating the vote as direct policy support or opposition.",
            "member_vote_context": None,
            "what_not_to_infer": "Do not infer support for or opposition to the underlying policy from this procedural action alone.",
        }
    summary = f"The Senate voted on {amendment}, whose official purpose was: {purpose}"
    return {
        "roll_call_id": packet["roll_call_id"],
        "interpretation_status": "interpreted",
        "support_position": "yea",
        "oppose_position": "nay",
        "interpretation_reason": "Direct amendment identity and purpose support a source-grounded amendment interpretation.",
        "source_url": packet["source_url"] or packet["congressgov_url"],
        "plain_english_summary": summary,
        "yea_meaning": f"A Yea vote supported agreeing to {amendment}.",
        "nay_meaning": f"A Nay vote opposed agreeing to {amendment}.",
        "policy_effect": f"If agreed to, {amendment} would have changed the measure in the way described by the official purpose: {purpose}",
        "issue_facet": packet["proposed_facet"],
        "confidence": "high",
        "source_basis": packet["source_basis"],
        "uncertainty_note": "This interpretation is limited to the amendment vote and does not infer motive or support for the whole parent measure.",
        "what_happened": summary,
        "why_it_mattered": "The amendment purpose identifies the narrower policy change before the Senate.",
        "member_vote_context": "A Yea vote supported the described amendment action. A Nay vote opposed it.",
        "what_not_to_infer": "Do not infer motive, ideology, character, a voting recommendation, or support for every provision of the parent measure.",
    }


def _classification_rollback_sql(row: dict[str, Any]) -> list[str]:
    return [
        "UPDATE vote_classifications",
        "SET",
        f"    is_eligible = {'TRUE' if row['is_eligible'] else 'FALSE'},",
        f"    eligibility_reason = {_sql_value(row['eligibility_reason'])},",
        f"    primary_domain = {_sql_domain(row['primary_domain'])},",
        f"    score_breakdown = {_sql_json(row['score_breakdown'])},",
        f"    classification_version = {_sql_value(row['classification_version'])},",
        "    updated_at = NOW()",
        f"WHERE roll_call_id = {int(row['roll_call_id'])};",
        "",
    ]


def _interpretation_rollback_sql(row: dict[str, Any]) -> list[str]:
    fields = [
        "interpretation_status",
        "support_position",
        "oppose_position",
        "interpretation_reason",
        "interpretation_source_url",
        "interpretation_version",
        "interpretation_classification_version",
        "plain_english_summary",
        "yea_meaning",
        "nay_meaning",
        "policy_effect",
        "issue_facet",
        "confidence",
        "source_basis",
        "uncertainty_note",
        "what_happened",
        "why_it_mattered",
        "member_vote_context",
        "what_not_to_infer",
        "reviewed_by",
    ]
    assignment_names = {
        "interpretation_source_url": "source_url",
        "interpretation_classification_version": "classification_version",
    }
    assignments = []
    for field in fields:
        name = assignment_names.get(field, field)
        value = row[field]
        if name == "source_basis":
            sql = _sql_json(value)
        elif name in {"support_position", "oppose_position"}:
            sql = _sql_vote_position(value)
        else:
            sql = _sql_value(value)
        assignments.append(f"    {name} = {sql}")
    return [
        "UPDATE vote_interpretations",
        "SET",
        ",\n".join(assignments) + ",",
        "    updated_at = NOW()",
        f"WHERE roll_call_id = {int(row['roll_call_id'])};",
        "",
    ]


def _normalize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="118th Senate amendment source enrichment.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    build = sub.add_parser("build-source-packets")
    build.add_argument("--fetch-missing", action="store_true")
    sub.add_parser("dry-run")
    sub.add_parser("write-classification-rollback")
    sub.add_parser("write-interpretation-rollback")
    write_classifications_parser = sub.add_parser("write-classifications")
    write_classifications_parser.add_argument("--approval-phrase", required=True)
    write_interpretations_parser = sub.add_parser("write-interpretations")
    write_interpretations_parser.add_argument("--approval-phrase", required=True)
    sub.add_parser("post-validate")
    args = parser.parse_args()

    if args.command == "audit":
        result = audit_deferred_amendments()
    elif args.command == "build-source-packets":
        result = build_source_packets(fetch_missing=args.fetch_missing)
    elif args.command == "dry-run":
        result = dry_run()
    elif args.command == "write-classification-rollback":
        result = write_classification_rollback()
    elif args.command == "write-interpretation-rollback":
        result = write_interpretation_rollback()
    elif args.command == "write-classifications":
        result = write_classifications(approval_phrase=args.approval_phrase)
    elif args.command == "write-interpretations":
        result = write_interpretations(approval_phrase=args.approval_phrase)
    else:
        result = post_validate()
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
