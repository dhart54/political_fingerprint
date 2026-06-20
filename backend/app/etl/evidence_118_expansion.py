from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.db import get_connection
from app.etl.amendment_evidence import WritePrecondition, require_write_precondition
from app.etl.session2_evidence_expansion import (
    _has_context_mismatch,
    _is_direct_substantive_question,
    _is_focused_procedural_context,
    _is_procedural_text,
    _source_basis,
    _sql_bool,
    _sql_domain,
    _sql_interpretation_status,
    _sql_json,
    _sql_value,
    _sql_vote_position,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CLASSIFICATION_ROLLBACK_PATH = REPO_ROOT / "docs" / "review_packets" / "118th_evidence_classification_rollback.sql"
DEFAULT_INTERPRETATION_ROLLBACK_PATH = REPO_ROOT / "docs" / "review_packets" / "118th_evidence_interpretation_rollback.sql"

CLASSIFICATION_APPROVAL = (
    "Approve production classification update for 118th Congress evidence expansion, "
    "bounded to reviewed 118th Congress roll_call_ids, with no fact-table writes, "
    "procedural context non-counting for support/opposition, rollback generated before write, "
    "119th preserved, not-voting excluded, and no support/opposition, readiness, alignment, "
    "or interpretation methodology changes."
)
INTERPRETATION_APPROVAL = (
    "Approve production interpretation update for 118th Congress evidence expansion, "
    "bounded to reviewed 118th Congress roll_call_ids, with substantive rows source-grounded, "
    "procedural rows non-counting with null support/opposition, rollback generated before write, "
    "119th preserved, not-voting excluded, and no support/opposition, readiness, alignment, "
    "or interpretation methodology changes."
)

SUBSTANTIVE_TYPES = {"final_passage", "appropriations", "other", "concurrence"}
PROCEDURAL_TYPES = {"motion", "rule"}
AMENDMENT_TYPES = {"amendment"}
DIRECT_CRA_MARKERS = (
    "providing for congressional disapproval under chapter 8",
    "congressional disapproval under chapter 8",
)
DOMAIN_RULES_118: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "NATIONAL_SECURITY_FOREIGN",
        (
            "armed forces",
            "war powers",
            "national defense",
            "defense",
            "defense authorization",
            "department of defense",
            "defense appropriations",
            "military",
            "ukraine",
            "israel",
            "iran",
            "china",
            "indo-pacific",
            "taiwan",
            "nato",
            "department of state",
            "foreign operations",
            "foreign aid",
            "foreign assistance",
            "foreign adversaries",
            "sanctions",
            "intelligence",
            "fisa",
            "syria",
            "somalia",
            "hamas",
            "terrorism",
            "terror-financing",
        ),
    ),
    (
        "IMMIGRATION_BORDER",
        (
            "border",
            "immigration",
            "deportation",
            "asylum",
            "migrant",
            "no immigration benefits",
        ),
    ),
    (
        "HEALTH_SOCIAL",
        (
            "health",
            "medicaid",
            "medicare",
            "cdc",
            "covid",
            "vaccination",
            "pandemic",
            "pregnant",
            "families",
            "nutrition",
            "whole milk",
        ),
    ),
    (
        "EDUCATION_WORKFORCE",
        (
            "education",
            "student",
            "school",
            "workforce",
            "labor",
            "loan",
            "direct loan",
        ),
    ),
    (
        "ENVIRONMENT_ENERGY",
        (
            "energy",
            "environmental protection agency",
            "environment",
            "emissions",
            "air pollution",
            "critical mineral",
            "minerals",
            "hunters and anglers",
            "home appliances",
            "public lands",
            "pipeline",
        ),
    ),
    (
        "JUSTICE_PUBLIC_SAFETY",
        (
            "law enforcement",
            "violent offenders",
            "crime",
            "crimes act",
            "firearm",
            "firearms",
            "atf",
            "bureau of alcohol",
            "surveillance",
            "homeland security",
            "department of homeland security",
        ),
    ),
    (
        "INFRASTRUCTURE_TECH_TRANSPORT",
        (
            "infrastructure",
            "technology",
            "innovation",
            "transportation",
            "aviation",
            "rail",
            "broadband",
            "cyber",
        ),
    ),
    (
        "ECONOMY_TAXES",
        (
            "tax",
            "taxpayer",
            "small business",
            "consumer financial",
            "budget",
            "appropriations",
            "continuing appropriations",
            "legislative branch appropriations",
            "spending reduction",
            "unemployment fraud",
            "hostages act",
        ),
    ),
)
DOMAIN_DEFER_MARKERS = (
    "impeach",
    "impeaching",
    "high crimes and misdemeanors",
    "removing a certain member",
)


@dataclass(frozen=True)
class Candidate:
    roll_call_id: int
    chamber: str
    session: int
    roll_number: int
    vote_date: str
    vote_type: str
    category: str
    domain: str
    question: str
    description: str
    bill_title: str
    source_url: str | None
    score_breakdown: dict[str, Any]


def audit_118_rows() -> dict[str, object]:
    rows = _load_118_rows()
    reason_distribution: Counter[str] = Counter()
    interpretation_distribution: Counter[str] = Counter()
    vote_type_distribution: Counter[str] = Counter()
    opportunity_distribution: Counter[str] = Counter()
    groups: dict[str, dict[str, Any]] = {}

    for row in rows:
        reason_distribution[f"{row['chamber']}:s{row['session']}:{row['eligibility_reason']}"] += 1
        interpretation_distribution[
            f"{row['chamber']}:s{row['session']}:{row.get('interpretation_status') or 'missing'}"
        ] += 1
        vote_type_distribution[f"{row['chamber']}:s{row['session']}:{row.get('vote_type') or 'unknown'}"] += 1
        candidate, defer_reason = build_candidate(row)
        category = candidate.category if candidate else defer_reason
        opportunity_distribution[category] += 1
        group_key = _group_key(row=row, candidate=candidate, defer_reason=defer_reason)
        group = groups.setdefault(
            group_key,
            {
                "group": group_key,
                "rows": 0,
                "category": category,
                "domain": candidate.domain if candidate else None,
                "vote_type": row.get("vote_type"),
                "decision": _decision_for(candidate=candidate, defer_reason=defer_reason),
                "source_strength": _source_strength_for(candidate=candidate, defer_reason=defer_reason),
                "trust_risk": _trust_risk_for(candidate=candidate, defer_reason=defer_reason),
                "examples": [],
            },
        )
        group["rows"] += 1
        if len(group["examples"]) < 5:
            group["examples"].append(_example(row))

    ranked = sorted(
        groups.values(),
        key=lambda group: (
            -_rank_score(group),
            -int(group["rows"]),
            str(group["group"]),
        ),
    )
    return {
        "total_rows": len(rows),
        "reason_distribution": dict(sorted(reason_distribution.items())),
        "interpretation_status_distribution": dict(sorted(interpretation_distribution.items())),
        "vote_type_distribution": dict(sorted(vote_type_distribution.items())),
        "opportunity_distribution": dict(opportunity_distribution.most_common()),
        "top_opportunity_groups": ranked[:20],
    }


def build_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for row in _load_118_rows():
        candidate, _defer_reason = build_candidate(row)
        if candidate:
            candidates.append(candidate)
    return candidates


def build_candidate(row: dict[str, Any]) -> tuple[Candidate | None, str]:
    vote_type = str(row.get("vote_type") or "")
    question = str(row.get("question") or "")
    description = str(row.get("description") or "")
    bill_title = str(row.get("bill_title") or "")
    text = f"{bill_title} {question} {description}".lower()

    if _has_context_mismatch(row):
        return None, "defer_context_mismatch"

    if _has_domain_defer_marker(text):
        return None, "defer_no_safe_issue_domain"

    if vote_type in AMENDMENT_TYPES:
        return None, "defer_amendment_needs_direct_purpose"

    if vote_type in PROCEDURAL_TYPES or _is_procedural_text(text):
        if _is_direct_cra_passage(question=question, text=text):
            domain, breakdown = _domain_from_118_text(text)
            if domain:
                return _candidate(row, category="substantive_interpretation", domain=domain, score_breakdown=breakdown), ""
        domain, breakdown = _domain_from_118_text(text)
        if domain and _is_focused_procedural_context(text):
            return _candidate(row, category="procedural_context", domain=domain, score_breakdown=breakdown), ""
        return None, "defer_broad_or_low_value_procedural"

    if vote_type not in SUBSTANTIVE_TYPES:
        return None, "defer_unsupported_vote_type"

    domain, breakdown = _domain_from_118_text(text)
    if not domain:
        return None, "still_insufficient_no_domain_signal"

    if _is_direct_substantive_question(question=question, vote_type=vote_type):
        return _candidate(row, category="substantive_interpretation", domain=domain, score_breakdown=breakdown), ""

    return None, "still_insufficient_ambiguous_question"


def dry_run() -> dict[str, object]:
    candidates = build_candidates()
    substantive = [candidate for candidate in candidates if candidate.category == "substantive_interpretation"]
    procedural = [candidate for candidate in candidates if candidate.category == "procedural_context"]
    return {
        "audit": audit_118_rows(),
        "candidate_count": len(candidates),
        "candidate_split": {
            "substantive_interpretation": len(substantive),
            "procedural_context": len(procedural),
        },
        "classification_updates": len(candidates),
        "interpretation_updates": len(candidates),
        "support_position_updates": len(substantive),
        "oppose_position_updates": len(substantive),
        "procedural_null_support_oppose": len(procedural),
        "target_roll_call_ids": [candidate.roll_call_id for candidate in candidates],
        "domain_distribution": dict(Counter(candidate.domain for candidate in candidates).most_common()),
        "category_domain_distribution": dict(
            Counter(f"{candidate.category}:{candidate.domain}" for candidate in candidates).most_common()
        ),
    }


def write_classification_rollback(path: Path) -> dict[str, object]:
    candidates = build_candidates()
    rows = _load_existing_rows([candidate.roll_call_id for candidate in candidates])
    lines = [
        "-- Rollback for 118th Congress Evidence Expansion classifications.",
        "-- Scope: exact roll_call_ids selected by evidence_118_expansion dry-run.",
        "BEGIN;",
        "",
    ]
    for row in rows:
        lines.extend(_classification_rollback_sql(row))
    lines.append("COMMIT;")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"rollback_path": str(path), "rows": len(rows)}


def write_interpretation_rollback(path: Path) -> dict[str, object]:
    candidates = build_candidates()
    rows = _load_existing_rows([candidate.roll_call_id for candidate in candidates])
    lines = [
        "-- Rollback for 118th Congress Evidence Expansion interpretations.",
        "-- Scope: exact roll_call_ids selected by evidence_118_expansion dry-run.",
        "BEGIN;",
        "",
    ]
    for row in rows:
        lines.extend(_interpretation_rollback_sql(row))
    lines.append("COMMIT;")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"rollback_path": str(path), "rows": len(rows)}


def write_precompute_rollback(path: Path, *, window_end: str = "2026-06-19") -> dict[str, object]:
    snapshot = _load_precompute_snapshot(window_end=window_end)
    lines = [
        "-- Rollback for 118th Congress Evidence Expansion derived precomputes.",
        f"-- Restores prewrite rows for window_end {window_end} / classification_version v1.",
        "BEGIN;",
        "",
    ]
    for table in ("summaries", "drift_scores", "chamber_medians", "fingerprints"):
        lines.extend(
            [
                f"DELETE FROM {table}",
                f"WHERE {_precompute_window_predicate(table, window_end=window_end)};",
                "",
            ]
        )
    lines.extend(_restore_fingerprints_sql(snapshot["fingerprints"]))
    lines.extend(_restore_chamber_medians_sql(snapshot["chamber_medians"]))
    lines.extend(_restore_drift_scores_sql(snapshot["drift_scores"]))
    lines.extend(_restore_summaries_sql(snapshot["summaries"]))
    lines.append("COMMIT;")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "rollback_path": str(path),
        "rows": {key: len(value) for key, value in snapshot.items()},
    }


def write_classifications(*, approval_phrase: str) -> dict[str, object]:
    if approval_phrase != CLASSIFICATION_APPROVAL:
        raise ValueError("Classification approval phrase does not match.")
    candidates = build_candidates()
    require_write_precondition(
        WritePrecondition(
            scope="118th Congress evidence expansion classifications",
            approval_phrase=CLASSIFICATION_APPROVAL,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(candidate.roll_call_id for candidate in candidates),
            rollback_path=DEFAULT_CLASSIFICATION_ROLLBACK_PATH,
            planned_vote_interpretation_writes=0,
            expected_vote_interpretation_writes=0,
        )
    )
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            updated = _update_classifications(cursor, candidates)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"updated_classifications": updated}


def write_interpretations(*, approval_phrase: str) -> dict[str, object]:
    if approval_phrase != INTERPRETATION_APPROVAL:
        raise ValueError("Interpretation approval phrase does not match.")
    candidates = build_candidates()
    require_write_precondition(
        WritePrecondition(
            scope="118th Congress evidence expansion interpretations",
            approval_phrase=INTERPRETATION_APPROVAL,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(candidate.roll_call_id for candidate in candidates),
            rollback_path=DEFAULT_INTERPRETATION_ROLLBACK_PATH,
            planned_vote_interpretation_writes=len(candidates),
            expected_vote_interpretation_writes=len(candidates),
        )
    )
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            updated = _update_interpretations(cursor, candidates)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"updated_interpretations": updated}


def post_validate() -> dict[str, object]:
    candidates = build_candidates()
    ids = [candidate.roll_call_id for candidate in candidates]
    if not ids:
        return {"target_rows": 0}
    substantive_count = sum(1 for candidate in candidates if candidate.category == "substantive_interpretation")
    procedural_count = sum(1 for candidate in candidates if candidate.category == "procedural_context")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible,
                  COUNT(*) FILTER (WHERE vi.interpretation_status = 'interpreted') AS interpreted,
                  COUNT(*) FILTER (WHERE vi.support_position IS NOT NULL) AS support_non_null,
                  COUNT(*) FILTER (WHERE vi.oppose_position IS NOT NULL) AS oppose_non_null,
                  COUNT(*) FILTER (
                    WHERE vi.interpretation_status = 'insufficient_evidence'
                      AND vi.support_position IS NULL
                      AND vi.oppose_position IS NULL
                  ) AS non_counting,
                  COUNT(*) FILTER (WHERE rc.congress <> 118) AS non_118_targets
                FROM vote_classifications vcf
                JOIN roll_calls rc ON rc.id = vcf.roll_call_id
                JOIN vote_interpretations vi ON vi.roll_call_id = vcf.roll_call_id
                WHERE vcf.roll_call_id = ANY(%s)
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
    finally:
        connection.close()
    return {
        "target_rows": len(ids),
        "expected_substantive_rows": substantive_count,
        "expected_procedural_context_rows": procedural_count,
        "eligible_classifications": int(row[0]),
        "interpreted_rows": int(row[1]),
        "support_non_null": int(row[2]),
        "oppose_non_null": int(row[3]),
        "non_counting_rows": int(row[4]),
        "non_118_targets": int(row[5]),
        "not_voting_counted_as_support_or_oppose": not_voting_counted,
    }


def _load_118_rows() -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rc.id AS roll_call_id,
                    rc.chamber,
                    rc.session,
                    rc.rollcall_number,
                    rc.vote_date::date::text,
                    rc.question,
                    rc.description,
                    rc.source_url,
                    COALESCE(b.title, '') AS bill_title,
                    COALESCE(b.bill_type, '') AS bill_type,
                    b.bill_number,
                    vcf.is_eligible,
                    vcf.eligibility_reason,
                    vcf.primary_domain::text,
                    vi.interpretation_status::text,
                    COALESCE(vctx.vote_type, 'unknown') AS vote_type
                FROM roll_calls rc
                JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
                LEFT JOIN vote_contexts vctx
                  ON vctx.roll_call_id = rc.id
                 AND vctx.legislator_id = (
                    SELECT MIN(legislator_id) FROM vote_contexts WHERE roll_call_id = rc.id
                 )
                LEFT JOIN bills b ON b.id = rc.bill_id
                WHERE rc.congress = 118
                ORDER BY rc.chamber, rc.session, rc.rollcall_number
                """
            )
            columns = [description[0] for description in cursor.description or []]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _candidate(row: dict[str, Any], *, category: str, domain: str, score_breakdown: dict[str, Any]) -> Candidate:
    return Candidate(
        roll_call_id=int(row["roll_call_id"]),
        chamber=str(row["chamber"]),
        session=int(row["session"]),
        roll_number=int(row["rollcall_number"]),
        vote_date=str(row["vote_date"]),
        vote_type=str(row.get("vote_type") or ""),
        category=category,
        domain=domain,
        question=str(row.get("question") or ""),
        description=str(row.get("description") or ""),
        bill_title=str(row.get("bill_title") or ""),
        source_url=None if row.get("source_url") is None else str(row["source_url"]),
        score_breakdown=score_breakdown,
    )


def _is_direct_cra_passage(*, question: str, text: str) -> bool:
    normalized_question = question.lower()
    return (
        ("on passage" in normalized_question or "objections of the president" in normalized_question)
        and any(marker in text for marker in DIRECT_CRA_MARKERS)
    )


def _domain_from_118_text(text: str) -> tuple[str | None, dict[str, Any]]:
    if _has_domain_defer_marker(text):
        return None, {}
    hits: list[tuple[int, str, list[str]]] = []
    for domain, terms in DOMAIN_RULES_118:
        matched = [term for term in terms if term in text]
        if matched:
            hits.append((len(matched), domain, matched))
    if not hits:
        return None, {}
    hits.sort(key=lambda item: (-item[0], item[1]))
    if len(hits) > 1 and hits[0][0] == hits[1][0]:
        return None, {
            domain: {"keyword_match": len(matched), "matched_terms": matched}
            for _, domain, matched in hits
        }
    _, domain, matched_terms = hits[0]
    return domain, {domain: {"keyword_match": len(matched_terms) * 2, "matched_terms": matched_terms}}


def _has_domain_defer_marker(text: str) -> bool:
    return any(marker in text for marker in DOMAIN_DEFER_MARKERS)


def _group_key(*, row: dict[str, Any], candidate: Candidate | None, defer_reason: str) -> str:
    if candidate:
        return f"{candidate.category}:{candidate.domain}:{candidate.vote_type}"
    vote_type = str(row.get("vote_type") or "unknown")
    return f"{defer_reason}:{vote_type}"


def _decision_for(*, candidate: Candidate | None, defer_reason: str) -> str:
    if candidate and candidate.category == "substantive_interpretation":
        return "promote_counting_interpretation"
    if candidate and candidate.category == "procedural_context":
        return "promote_visible_non_counting_context"
    return "defer"


def _source_strength_for(*, candidate: Candidate | None, defer_reason: str) -> str:
    if candidate and candidate.category == "substantive_interpretation":
        return "strong direct vote question plus measure title"
    if candidate and candidate.category == "procedural_context":
        return "moderate procedural question plus focused measure title"
    if "amendment" in defer_reason:
        return "weak without direct amendment purpose"
    return "limited or broad context"


def _trust_risk_for(*, candidate: Candidate | None, defer_reason: str) -> str:
    if candidate and candidate.category == "substantive_interpretation":
        return "low"
    if candidate and candidate.category == "procedural_context":
        return "medium kept non-counting"
    if "amendment" in defer_reason:
        return "high if parent-measure context replaced amendment meaning"
    return "medium/high"


def _rank_score(group: dict[str, Any]) -> int:
    decision = str(group.get("decision"))
    rows = int(group.get("rows") or 0)
    if decision == "promote_counting_interpretation":
        return 3000 + rows
    if decision == "promote_visible_non_counting_context":
        return 2000 + rows
    return 1000 + rows


def _example(row: dict[str, Any]) -> dict[str, object]:
    return {
        "roll_call_id": row["roll_call_id"],
        "chamber": row["chamber"],
        "session": row["session"],
        "rollcall_number": row["rollcall_number"],
        "vote_date": row["vote_date"],
        "question": row["question"],
        "description": row["description"],
        "bill_title": row["bill_title"],
        "vote_type": row.get("vote_type"),
        "eligibility_reason": row["eligibility_reason"],
        "interpretation_status": row.get("interpretation_status"),
    }


def _load_existing_rows(ids: list[int]) -> list[dict[str, Any]]:
    if not ids:
        return []
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    vcf.roll_call_id,
                    vcf.is_eligible,
                    vcf.eligibility_reason,
                    vcf.primary_domain,
                    vcf.score_breakdown,
                    vcf.classification_version,
                    vi.interpretation_status,
                    vi.support_position,
                    vi.oppose_position,
                    vi.interpretation_reason,
                    vi.source_url,
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
                    vi.reviewed_by,
                    vi.reviewed_at,
                    vi.what_happened,
                    vi.why_it_mattered,
                    vi.member_vote_context,
                    vi.what_not_to_infer
                FROM vote_classifications vcf
                JOIN vote_interpretations vi ON vi.roll_call_id = vcf.roll_call_id
                WHERE vcf.roll_call_id = ANY(%s)
                ORDER BY vcf.roll_call_id
                """,
                (ids,),
            )
            columns = [description[0] for description in cursor.description or []]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def _load_precompute_snapshot(*, window_end: str) -> dict[str, list[dict[str, Any]]]:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT legislator_id, window_start::text, window_end::text, classification_version,
                       domain::text, vote_count, total_votes, vote_share::float
                FROM fingerprints
                WHERE window_end = %s AND classification_version = 'v1'
                ORDER BY legislator_id, domain
                """,
                (window_end,),
            )
            fingerprints = [_dict_rows(cursor, row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT chamber::text, party, window_start::text, window_end::text, classification_version,
                       domain::text, legislator_count, median_share::float
                FROM chamber_medians
                WHERE window_end = %s AND classification_version = 'v1'
                ORDER BY chamber, party, domain
                """,
                (window_end,),
            )
            chamber_medians = [_dict_rows(cursor, row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT legislator_id, window_start::text, window_end::text, early_window_start::text,
                       early_window_end::text, recent_window_start::text, recent_window_end::text,
                       classification_version, total_votes, early_total_votes, recent_total_votes,
                       insufficient_data, drift_value::float
                FROM drift_scores
                WHERE window_end = %s AND classification_version = 'v1'
                ORDER BY legislator_id
                """,
                (window_end,),
            )
            drift_scores = [_dict_rows(cursor, row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT legislator_id, window_end::text, classification_version,
                       summary_text, generation_method, created_at::text
                FROM summaries
                WHERE window_end = %s AND classification_version = 'v1'
                ORDER BY legislator_id
                """,
                (window_end,),
            )
            summaries = [_dict_rows(cursor, row) for row in cursor.fetchall()]
    finally:
        connection.close()
    return {
        "fingerprints": fingerprints,
        "chamber_medians": chamber_medians,
        "drift_scores": drift_scores,
        "summaries": summaries,
    }


def _dict_rows(cursor, row) -> dict[str, Any]:
    columns = [description[0] for description in cursor.description or []]
    return dict(zip(columns, row))


def _precompute_window_predicate(table: str, *, window_end: str) -> str:
    return f"window_end = DATE '{window_end}' AND classification_version = 'v1'"


def _restore_fingerprints_sql(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [
        "INSERT INTO fingerprints (",
        "    legislator_id, window_start, window_end, classification_version,",
        "    domain, vote_count, total_votes, vote_share",
        ")",
        "SELECT legislator_id, window_start::date, window_end::date, classification_version,",
        "       domain::issue_domain, vote_count, total_votes, vote_share",
        "FROM jsonb_to_recordset(" + _sql_json_literal(rows) + "::jsonb)",
        "AS row(legislator_id int, window_start text, window_end text, classification_version text,",
        "       domain text, vote_count int, total_votes int, vote_share numeric)",
        "ON CONFLICT (legislator_id, window_start, window_end, classification_version, domain)",
        "DO UPDATE SET vote_count = EXCLUDED.vote_count,",
        "              total_votes = EXCLUDED.total_votes,",
        "              vote_share = EXCLUDED.vote_share,",
        "              updated_at = NOW();",
        "",
    ]


def _restore_chamber_medians_sql(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [
        "INSERT INTO chamber_medians (",
        "    chamber, party, window_start, window_end, classification_version,",
        "    domain, legislator_count, median_share",
        ")",
        "SELECT chamber::chamber, party, window_start::date, window_end::date, classification_version,",
        "       domain::issue_domain, legislator_count, median_share",
        "FROM jsonb_to_recordset(" + _sql_json_literal(rows) + "::jsonb)",
        "AS row(chamber text, party text, window_start text, window_end text, classification_version text,",
        "       domain text, legislator_count int, median_share numeric)",
        "ON CONFLICT (chamber, party, window_start, window_end, classification_version, domain)",
        "DO UPDATE SET legislator_count = EXCLUDED.legislator_count,",
        "              median_share = EXCLUDED.median_share,",
        "              updated_at = NOW();",
        "",
    ]


def _restore_drift_scores_sql(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [
        "INSERT INTO drift_scores (",
        "    legislator_id, window_start, window_end, early_window_start, early_window_end,",
        "    recent_window_start, recent_window_end, classification_version, total_votes,",
        "    early_total_votes, recent_total_votes, insufficient_data, drift_value",
        ")",
        "SELECT legislator_id, window_start::date, window_end::date, early_window_start::date,",
        "       early_window_end::date, recent_window_start::date, recent_window_end::date,",
        "       classification_version, total_votes, early_total_votes, recent_total_votes,",
        "       insufficient_data, drift_value",
        "FROM jsonb_to_recordset(" + _sql_json_literal(rows) + "::jsonb)",
        "AS row(legislator_id int, window_start text, window_end text, early_window_start text,",
        "       early_window_end text, recent_window_start text, recent_window_end text,",
        "       classification_version text, total_votes int, early_total_votes int,",
        "       recent_total_votes int, insufficient_data boolean, drift_value numeric)",
        "ON CONFLICT (legislator_id, window_start, window_end, classification_version)",
        "DO UPDATE SET early_window_start = EXCLUDED.early_window_start,",
        "              early_window_end = EXCLUDED.early_window_end,",
        "              recent_window_start = EXCLUDED.recent_window_start,",
        "              recent_window_end = EXCLUDED.recent_window_end,",
        "              total_votes = EXCLUDED.total_votes,",
        "              early_total_votes = EXCLUDED.early_total_votes,",
        "              recent_total_votes = EXCLUDED.recent_total_votes,",
        "              insufficient_data = EXCLUDED.insufficient_data,",
        "              drift_value = EXCLUDED.drift_value,",
        "              updated_at = NOW();",
        "",
    ]


def _restore_summaries_sql(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [
        "INSERT INTO summaries (",
        "    legislator_id, window_end, classification_version, summary_text, generation_method, created_at",
        ")",
        "SELECT legislator_id, window_end::date, classification_version, summary_text,",
        "       generation_method, created_at::timestamptz",
        "FROM jsonb_to_recordset(" + _sql_json_literal(rows) + "::jsonb)",
        "AS row(legislator_id int, window_end text, classification_version text,",
        "       summary_text text, generation_method text, created_at text)",
        "ON CONFLICT (legislator_id, window_end, classification_version)",
        "DO UPDATE SET summary_text = EXCLUDED.summary_text,",
        "              generation_method = EXCLUDED.generation_method,",
        "              created_at = EXCLUDED.created_at,",
        "              updated_at = NOW();",
        "",
    ]


def _sql_json_literal(value: Any) -> str:
    return _sql_value(json.dumps(value, sort_keys=True))


def _classification_rollback_sql(row: dict[str, Any]) -> list[str]:
    return [
        "UPDATE vote_classifications",
        "SET",
        f"    is_eligible = {_sql_bool(row['is_eligible'])},",
        f"    eligibility_reason = {_sql_value(row['eligibility_reason'])},",
        f"    primary_domain = {_sql_domain(row['primary_domain'])},",
        f"    score_breakdown = {_sql_json(row['score_breakdown'])},",
        f"    classification_version = {_sql_value(row['classification_version'])},",
        "    updated_at = NOW()",
        f"WHERE roll_call_id = {int(row['roll_call_id'])};",
        "",
    ]


def _interpretation_rollback_sql(row: dict[str, Any]) -> list[str]:
    fields = (
        "interpretation_status",
        "support_position",
        "oppose_position",
        "interpretation_reason",
        "source_url",
        "interpretation_version",
        "classification_version",
        "plain_english_summary",
        "yea_meaning",
        "nay_meaning",
        "policy_effect",
        "issue_facet",
        "confidence",
        "source_basis",
        "uncertainty_note",
        "reviewed_by",
        "reviewed_at",
        "what_happened",
        "why_it_mattered",
        "member_vote_context",
        "what_not_to_infer",
    )
    assignments = []
    for field in fields:
        value = row["interpretation_classification_version"] if field == "classification_version" else row[field]
        if field == "source_basis":
            assignments.append(f"    {field} = {_sql_json(value)}")
        elif field in {"support_position", "oppose_position"}:
            assignments.append(f"    {field} = {_sql_vote_position(value)}")
        elif field == "interpretation_status":
            assignments.append(f"    {field} = {_sql_interpretation_status(value)}")
        else:
            assignments.append(f"    {field} = {_sql_value(value)}")
    return [
        "UPDATE vote_interpretations",
        "SET",
        ",\n".join(assignments) + ",",
        "    updated_at = NOW()",
        f"WHERE roll_call_id = {int(row['roll_call_id'])};",
        "",
    ]


def _update_classifications(cursor, candidates: list[Candidate]) -> int:
    cursor.executemany(
        """
        WITH next_values AS (
            SELECT
                TRUE AS is_eligible,
                %s AS eligibility_reason,
                %s::issue_domain AS primary_domain,
                %s::jsonb AS score_breakdown,
                'v1' AS classification_version
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
                "procedural_context" if candidate.category == "procedural_context" else "policy_vote",
                candidate.domain,
                json.dumps(candidate.score_breakdown),
                candidate.roll_call_id,
            )
            for candidate in candidates
        ],
    )
    return max(cursor.rowcount, 0)


def _update_interpretations(cursor, candidates: list[Candidate]) -> int:
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
                'v1' AS classification_version,
                %s AS plain_english_summary,
                %s AS yea_meaning,
                %s AS nay_meaning,
                %s AS policy_effect,
                %s AS issue_facet,
                %s AS confidence,
                %s::jsonb AS source_basis,
                %s AS uncertainty_note,
                'deterministic_118th_expansion' AS reviewed_by,
                %s AS what_happened,
                %s AS why_it_mattered,
                NULL::text AS member_vote_context,
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
            reviewed_by = 'deterministic_118th_expansion',
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
          AND (
            vi.interpretation_status IS DISTINCT FROM next_values.interpretation_status
            OR vi.support_position IS DISTINCT FROM next_values.support_position
            OR vi.oppose_position IS DISTINCT FROM next_values.oppose_position
            OR vi.interpretation_reason IS DISTINCT FROM next_values.interpretation_reason
            OR vi.source_url IS DISTINCT FROM next_values.source_url
            OR vi.interpretation_version IS DISTINCT FROM next_values.interpretation_version
            OR vi.classification_version IS DISTINCT FROM next_values.classification_version
            OR vi.plain_english_summary IS DISTINCT FROM next_values.plain_english_summary
            OR vi.yea_meaning IS DISTINCT FROM next_values.yea_meaning
            OR vi.nay_meaning IS DISTINCT FROM next_values.nay_meaning
            OR vi.policy_effect IS DISTINCT FROM next_values.policy_effect
            OR vi.issue_facet IS DISTINCT FROM next_values.issue_facet
            OR vi.confidence IS DISTINCT FROM next_values.confidence
            OR vi.source_basis IS DISTINCT FROM next_values.source_basis
            OR vi.uncertainty_note IS DISTINCT FROM next_values.uncertainty_note
            OR vi.reviewed_by IS DISTINCT FROM next_values.reviewed_by
            OR vi.what_happened IS DISTINCT FROM next_values.what_happened
            OR vi.why_it_mattered IS DISTINCT FROM next_values.why_it_mattered
            OR vi.member_vote_context IS DISTINCT FROM next_values.member_vote_context
            OR vi.what_not_to_infer IS DISTINCT FROM next_values.what_not_to_infer
          )
        """,
        [_interpretation_params(candidate) for candidate in candidates],
    )
    return max(cursor.rowcount, 0)


def _interpretation_params(candidate: Candidate) -> tuple[object, ...]:
    if candidate.category == "procedural_context":
        measure = candidate.bill_title or candidate.description
        summary = f"This was a procedural vote connected to {measure}."
        return (
            "insufficient_evidence",
            None,
            None,
            "Deterministic review classified this as procedural context; support/opposition meaning is not inferred.",
            candidate.source_url,
            summary,
            None,
            None,
            None,
            "procedural_context",
            "medium",
            json.dumps(_source_basis(candidate)),
            "Procedural context is visible for comprehension but remains non-counting for support/opposition.",
            summary,
            "It helps explain floor process and agenda control, but it is not treated as substantive support or opposition.",
            "Do not infer support for or opposition to the underlying policy from this procedural vote alone.",
            candidate.roll_call_id,
        )

    measure = candidate.bill_title or candidate.description
    summary = f"This was a direct vote on {measure}."
    return (
        "interpreted",
        "yea",
        "nay",
        "Official roll-call question and measure title directly establish the vote as a substantive yea/nay measure vote.",
        candidate.source_url,
        summary,
        "A Yea vote supported the measure named in the official roll-call source.",
        "A Nay vote opposed the measure named in the official roll-call source.",
        f"The vote advanced or rejected the measure identified by the official source: {measure}.",
        candidate.domain.lower(),
        "medium",
        json.dumps(_source_basis(candidate)),
        "This interpretation is limited to the vote on the named measure and does not infer motive or broader ideology.",
        summary,
        "The vote is useful because it records a direct position on the named measure in the 118th Congress.",
        "Do not infer the member's motive, ideology, or position on every provision beyond this recorded vote.",
        candidate.roll_call_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="118th Congress evidence eligibility and interpretation expansion.")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-classification-rollback", type=Path)
    parser.add_argument("--write-interpretation-rollback", type=Path)
    parser.add_argument("--write-precompute-rollback", type=Path)
    parser.add_argument("--precompute-window-end", default="2026-06-19")
    parser.add_argument("--write-classifications", action="store_true")
    parser.add_argument("--write-interpretations", action="store_true")
    parser.add_argument("--post-validate", action="store_true")
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()

    output: dict[str, object] = {}
    if args.audit:
        output["audit"] = audit_118_rows()
    if args.dry_run:
        output["dry_run"] = dry_run()
    if args.write_classification_rollback:
        output["classification_rollback"] = write_classification_rollback(args.write_classification_rollback)
    if args.write_interpretation_rollback:
        output["interpretation_rollback"] = write_interpretation_rollback(args.write_interpretation_rollback)
    if args.write_precompute_rollback:
        output["precompute_rollback"] = write_precompute_rollback(
            args.write_precompute_rollback,
            window_end=args.precompute_window_end,
        )
    if args.write_classifications:
        output["classification_write"] = write_classifications(approval_phrase=args.approval_phrase)
    if args.write_interpretations:
        output["interpretation_write"] = write_interpretations(approval_phrase=args.approval_phrase)
    if args.post_validate:
        output["post_validate"] = post_validate()
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
