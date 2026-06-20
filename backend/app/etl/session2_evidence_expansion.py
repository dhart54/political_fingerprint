from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.db import get_connection
from app.etl.amendment_evidence import WritePrecondition, require_write_precondition


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROLLBACK_PATH = REPO_ROOT / "docs" / "review_packets" / "session2_evidence_expansion_rollback.sql"

CLASSIFICATION_APPROVAL = (
    "Approve production classification update for 2026 session-2 evidence expansion, "
    "bounded to reviewed 119th Congress session-2 roll_call_ids, with no support/opposition inference, "
    "no vote_interpretations writes in the classification step, rollback generated before write, "
    "and no readiness or alignment methodology changes."
)
INTERPRETATION_APPROVAL = (
    "Approve production interpretation update for 2026 session-2 evidence expansion, "
    "bounded to reviewed 119th Congress session-2 roll_call_ids, with procedural rows non-counting, "
    "not-voting excluded, rollback generated before write, and no readiness or alignment methodology changes."
)

SUBSTANTIVE_TYPES = {"final_passage", "appropriations", "other", "concurrence"}
PROCEDURAL_TYPES = {"motion", "rule"}
AMENDMENT_TYPES = {"amendment"}

DOMAIN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "JUSTICE_PUBLIC_SAFETY",
        (
            "law enforcement",
            "violent offenders",
            "cashless bail",
            "crime",
            "policing",
            "fisa",
            "surveillance",
            "2nd amendment",
            "firearm",
            "department of homeland security",
            "homeland security",
        ),
    ),
    (
        "NATIONAL_SECURITY_FOREIGN",
        (
            "defense",
            "military",
            "armed forces",
            "war powers",
            "iran",
            "venezuela",
            "foreign",
            "fisa",
            "intelligence",
            "national security",
            "undersea cable",
        ),
    ),
    (
        "ECONOMY_TAXES",
        (
            "appropriations",
            "budget",
            "tax",
            "financial services",
            "small business",
            "retirement savings",
            "consumer",
            "fuel",
            "federal infrastructure",
        ),
    ),
    (
        "HEALTH_SOCIAL",
        (
            "pregnant",
            "families",
            "child care",
            "tanf",
            "food and drug",
            "nutrition",
            "health",
        ),
    ),
    (
        "EDUCATION_WORKFORCE",
        (
            "education",
            "students",
            "workforce",
            "workers",
            "employee",
            "smithsonian american women",
        ),
    ),
    (
        "ENVIRONMENT_ENERGY",
        (
            "energy",
            "critical mineral",
            "minerals",
            "home appliances",
            "homeowner energy",
            "hunters and anglers",
            "rural communities",
            "environment",
        ),
    ),
    (
        "IMMIGRATION_BORDER",
        (
            "border",
            "immigration",
            "deportation",
            "haiti",
            "temporary protected status",
        ),
    ),
    (
        "INFRASTRUCTURE_TECH_TRANSPORT",
        (
            "infrastructure",
            "undersea cable",
            "transportation",
            "broadband",
            "technology",
            "cyber",
            "remote access",
        ),
    ),
)


@dataclass(frozen=True)
class Candidate:
    roll_call_id: int
    chamber: str
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


def audit_session2_rows() -> dict[str, object]:
    rows = _load_session2_rows()
    reason_distribution: dict[str, int] = {}
    vote_type_distribution: dict[str, int] = {}
    opportunity_distribution: dict[str, int] = {}
    top_groups: dict[str, dict[str, object]] = {}

    for row in rows:
        reason_key = f"{row['chamber']}:{row['eligibility_reason']}"
        reason_distribution[reason_key] = reason_distribution.get(reason_key, 0) + 1
        vote_type_key = f"{row['chamber']}:{row['vote_type']}"
        vote_type_distribution[vote_type_key] = vote_type_distribution.get(vote_type_key, 0) + 1

        candidate, defer_reason = build_candidate(row)
        category = candidate.category if candidate else defer_reason
        opportunity_distribution[category] = opportunity_distribution.get(category, 0) + 1

        group_key = _group_key(row=row, candidate=candidate, defer_reason=defer_reason)
        group = top_groups.setdefault(
            group_key,
            {
                "group": group_key,
                "rows": 0,
                "category": category,
                "domain": candidate.domain if candidate else None,
                "vote_type": row["vote_type"],
                "examples": [],
            },
        )
        group["rows"] = int(group["rows"]) + 1
        if len(group["examples"]) < 3:
            group["examples"].append(
                {
                    "roll_call_id": row["roll_call_id"],
                    "roll_number": row["rollcall_number"],
                    "question": row["question"],
                    "description": row["description"],
                    "bill_title": row["bill_title"],
                }
            )

    groups = sorted(top_groups.values(), key=lambda item: (-int(item["rows"]), str(item["group"])))
    return {
        "total_rows": len(rows),
        "reason_distribution": reason_distribution,
        "vote_type_distribution": vote_type_distribution,
        "opportunity_distribution": opportunity_distribution,
        "top_opportunity_groups": groups[:20],
    }


def build_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for row in _load_session2_rows():
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

    if vote_type in AMENDMENT_TYPES:
        return None, "defer_amendment_needs_purpose"

    if vote_type in PROCEDURAL_TYPES or _is_procedural_text(text):
        domain, breakdown = _domain_from_text(text)
        if domain and _is_focused_procedural_context(text):
            return _candidate(row, category="procedural_context", domain=domain, score_breakdown=breakdown), ""
        return None, "defer_broad_or_low_value_procedural"

    if vote_type not in SUBSTANTIVE_TYPES:
        return None, "defer_unsupported_vote_type"

    domain, breakdown = _domain_from_text(text)
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
        "audit": audit_session2_rows(),
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
        "domain_distribution": _count(candidate.domain for candidate in candidates),
    }


def write_rollback(path: Path) -> dict[str, object]:
    candidates = build_candidates()
    ids = [candidate.roll_call_id for candidate in candidates]
    rows = _load_existing_rows(ids)
    lines = [
        "-- Rollback for 2026 Evidence Eligibility And Interpretation Expansion.",
        "-- Scope: exact roll_call_ids selected by session2_evidence_expansion dry-run.",
        "BEGIN;",
        "",
    ]
    for row in rows:
        lines.extend(_classification_rollback_sql(row))
        lines.extend(_interpretation_rollback_sql(row))
    lines.append("COMMIT;")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"rollback_path": str(path), "rows": len(rows)}


def write_classifications(*, approval_phrase: str) -> dict[str, object]:
    if approval_phrase != CLASSIFICATION_APPROVAL:
        raise ValueError("Classification approval phrase does not match.")
    candidates = build_candidates()
    require_write_precondition(
        WritePrecondition(
            scope="2026 session-2 evidence expansion classifications",
            approval_phrase=CLASSIFICATION_APPROVAL,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(candidate.roll_call_id for candidate in candidates),
            rollback_path=DEFAULT_ROLLBACK_PATH,
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
            scope="2026 session-2 evidence expansion interpretations",
            approval_phrase=INTERPRETATION_APPROVAL,
            provided_approval_phrase=approval_phrase,
            target_row_ids=tuple(candidate.roll_call_id for candidate in candidates),
            rollback_path=DEFAULT_ROLLBACK_PATH,
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
    ids = [candidate.roll_call_id for candidate in build_candidates()]
    if not ids:
        return {"target_rows": 0}
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
                  ) AS non_counting
                FROM vote_classifications vcf
                JOIN vote_interpretations vi ON vi.roll_call_id = vcf.roll_call_id
                WHERE vcf.roll_call_id = ANY(%s)
                """,
                (ids,),
            )
            row = cursor.fetchone()
    finally:
        connection.close()
    return {
        "target_rows": len(ids),
        "eligible_classifications": int(row[0]),
        "interpreted_rows": int(row[1]),
        "support_non_null": int(row[2]),
        "oppose_non_null": int(row[3]),
        "non_counting_rows": int(row[4]),
    }


def _load_session2_rows() -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rc.id AS roll_call_id,
                    rc.chamber,
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
                    vctx.vote_type
                FROM roll_calls rc
                JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
                LEFT JOIN vote_contexts vctx
                  ON vctx.roll_call_id = rc.id
                 AND vctx.legislator_id = (
                    SELECT MIN(legislator_id) FROM vote_contexts WHERE roll_call_id = rc.id
                 )
                LEFT JOIN bills b ON b.id = rc.bill_id
                WHERE rc.congress = 119
                  AND rc.session = 2
                ORDER BY rc.chamber, rc.rollcall_number
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


def _domain_from_text(text: str) -> tuple[str | None, dict[str, Any]]:
    hits: list[tuple[int, str, list[str]]] = []
    for domain, terms in DOMAIN_RULES:
        matched = [term for term in terms if term in text]
        if matched:
            hits.append((len(matched), domain, matched))
    if not hits:
        return None, {}
    hits.sort(key=lambda item: (-item[0], item[1]))
    if len(hits) > 1 and hits[0][0] == hits[1][0]:
        return None, {domain: {"keyword_match": len(matched), "matched_terms": matched} for _, domain, matched in hits}
    _, domain, matched_terms = hits[0]
    return domain, {domain: {"keyword_match": len(matched_terms) * 2, "matched_terms": matched_terms}}


def _is_procedural_text(text: str) -> bool:
    procedural_terms = ("previous question", "motion to proceed", "cloture", "point of order", "motion to table")
    return any(term in text for term in procedural_terms)


def _is_focused_procedural_context(text: str) -> bool:
    if "providing for consideration of the bills" in text:
        return False
    if text.count("h.r.") + text.count("s.") + text.count("h.j. res") + text.count("s.j. res") > 2:
        return False
    return True


def _is_direct_substantive_question(*, question: str, vote_type: str) -> bool:
    normalized = question.lower()
    if vote_type == "appropriations" and ("on passage" in normalized or "on retaining" in normalized):
        return True
    return any(
        pattern in normalized
        for pattern in (
            "on passage",
            "passage, objections",
            "on the joint resolution",
            "on the resolution",
            "on the concurrent resolution",
            "on agreeing to the resolution",
        )
    )


def _has_context_mismatch(row: dict[str, Any]) -> bool:
    chamber = str(row.get("chamber") or "").lower()
    bill_title = str(row.get("bill_title") or "").lower()
    if chamber == "house" and (
        "motion to invoke cloture" in bill_title or "motion to proceed" in bill_title
    ):
        return True
    return False


def _count(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _group_key(*, row: dict[str, Any], candidate: Candidate | None, defer_reason: str) -> str:
    if candidate:
        return f"{candidate.category}:{candidate.domain}:{candidate.vote_type}"
    return f"{defer_reason}:{row.get('vote_type')}"


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
        FROM next_values
        WHERE vcf.roll_call_id = %s
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
                'deterministic_session2_expansion' AS reviewed_by,
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
            reviewed_by = 'deterministic_session2_expansion',
            reviewed_at = NOW(),
            what_happened = next_values.what_happened,
            why_it_mattered = next_values.why_it_mattered,
            member_vote_context = next_values.member_vote_context,
            what_not_to_infer = next_values.what_not_to_infer,
            updated_at = NOW()
        FROM next_values
        WHERE vi.roll_call_id = %s
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
        summary = f"This was a procedural vote connected to {candidate.bill_title or candidate.description}."
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
            "Procedural context is visible for comprehension but remains non-counting.",
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
        "The vote is useful because it records a direct position on the named measure in the reviewed 2026 session.",
        "Do not infer the member's motive, ideology, or position on every provision beyond this recorded vote.",
        candidate.roll_call_id,
    )


def _source_basis(candidate: Candidate) -> list[dict[str, str]]:
    return [
        {"field": "question", "source": f"Official roll call {candidate.roll_number}"},
        {"field": "description", "source": "Official roll-call description"},
        {"field": "bill_title", "source": "Loaded official bill/measure title"},
    ]


def _sql_value(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _sql_bool(value: Any) -> str:
    return "TRUE" if bool(value) else "FALSE"


def _sql_json(value: Any) -> str:
    if value is None:
        return "NULL"
    return _sql_value(json.dumps(value)) + "::jsonb"


def _sql_domain(value: Any) -> str:
    if value is None:
        return "NULL"
    return _sql_value(value) + "::issue_domain"


def _sql_vote_position(value: Any) -> str:
    if value is None:
        return "NULL"
    return _sql_value(value) + "::vote_position"


def _sql_interpretation_status(value: Any) -> str:
    if value is None:
        return "NULL"
    return _sql_value(value) + "::vote_interpretation_status"


def main() -> None:
    parser = argparse.ArgumentParser(description="2026 session-2 evidence eligibility and interpretation expansion.")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-rollback", type=Path)
    parser.add_argument("--write-classifications", action="store_true")
    parser.add_argument("--write-interpretations", action="store_true")
    parser.add_argument("--post-validate", action="store_true")
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()

    output: dict[str, object] = {}
    if args.audit:
        output["audit"] = audit_session2_rows()
    if args.dry_run:
        output["dry_run"] = dry_run()
    if args.write_rollback:
        output["rollback"] = write_rollback(args.write_rollback)
    if args.write_classifications:
        output["classification_write"] = write_classifications(approval_phrase=args.approval_phrase)
    if args.write_interpretations:
        output["interpretation_write"] = write_interpretations(approval_phrase=args.approval_phrase)
    if args.post_validate:
        output["post_validate"] = post_validate()
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
