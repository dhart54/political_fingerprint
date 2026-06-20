from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from psycopg.rows import dict_row


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db import get_connection  # noqa: E402


DOMAINS = (
    "ECONOMY_TAXES",
    "HEALTH_SOCIAL",
    "EDUCATION_WORKFORCE",
    "ENVIRONMENT_ENERGY",
    "NATIONAL_SECURITY_FOREIGN",
    "IMMIGRATION_BORDER",
    "JUSTICE_PUBLIC_SAFETY",
    "INFRASTRUCTURE_TECH_TRANSPORT",
)
CONGRESSES = (118, 119)
DEFAULT_JSON_PATH = REPO_ROOT / "docs" / "analysis" / "house_continuity_readiness_analysis.json"
DEFAULT_THRESHOLDS_PATH = REPO_ROOT / "docs" / "analysis" / "house_continuity_thresholds.csv"
DEFAULT_PROFILES_PATH = REPO_ROOT / "docs" / "analysis" / "house_continuity_profile_examples.csv"


@dataclass(frozen=True)
class Contract:
    name: str
    min_rows_per_common_domain_per_congress: int
    min_common_domains: int
    max_limited_procedural_share: float | None = None
    max_not_voting_share: float | None = None
    require_topic_overlap: bool = False
    require_balanced_opportunities: bool = False
    current_only: bool = True


CONTRACTS = (
    Contract("floor_any_common_domain", 1, 1),
    Contract("api_like_three_rows_one_domain", 3, 1),
    Contract("multi_domain_three_rows", 3, 2),
    Contract("strict_burden_controls", 3, 1, max_limited_procedural_share=0.5, max_not_voting_share=0.2),
    Contract(
        "topic_overlap_and_balance",
        3,
        1,
        max_limited_procedural_share=0.5,
        max_not_voting_share=0.2,
        require_topic_overlap=True,
        require_balanced_opportunities=True,
    ),
    Contract(
        "limited_profile_contract",
        3,
        2,
        max_limited_procedural_share=0.5,
        max_not_voting_share=0.2,
        require_topic_overlap=True,
        require_balanced_opportunities=True,
    ),
)

DOMAIN_COMPARABILITY_OVERRIDE = {
    "ECONOMY_TAXES": "conditionally comparable",
    "HEALTH_SOCIAL": "not currently comparable",
    "EDUCATION_WORKFORCE": "not currently comparable",
    "ENVIRONMENT_ENERGY": "conditionally comparable",
    "NATIONAL_SECURITY_FOREIGN": "conditionally comparable",
    "IMMIGRATION_BORDER": "not currently comparable",
    "JUSTICE_PUBLIC_SAFETY": "conditionally comparable",
    "INFRASTRUCTURE_TECH_TRANSPORT": "not currently comparable",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only House 118th/119th continuity readiness analysis.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--thresholds-output", type=Path, default=DEFAULT_THRESHOLDS_PATH)
    parser.add_argument("--profiles-output", type=Path, default=DEFAULT_PROFILES_PATH)
    args = parser.parse_args()

    with get_connection() as connection:
        connection.read_only = True
        connection.autocommit = False
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            payload = build_payload(cursor)

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    write_threshold_csv(args.thresholds_output, payload["threshold_simulations"])
    write_profile_csv(args.profiles_output, payload["profile_validation_examples"])
    print(json.dumps({"json": str(args.json_output), "thresholds": str(args.thresholds_output), "profiles": str(args.profiles_output)}, indent=2))


def build_payload(cursor: Any) -> dict[str, Any]:
    latest_classification_version = scalar(
        cursor,
        f"""
        SELECT classification_version
        FROM vote_classifications
        ORDER BY created_at DESC, classification_version DESC
        LIMIT 1
        """,
    )
    coverage_metadata = coverage_metadata_rows(cursor)
    officials = official_rollups(cursor, latest_classification_version)
    domain_rows = domain_rollups(cursor, latest_classification_version)
    profile_domains = profile_domain_rows(cursor, latest_classification_version)
    evidence_rows = substantive_evidence_rows(cursor, latest_classification_version)
    burden_rows = burden_by_official(cursor, latest_classification_version)

    officials_by_id = {row["legislator_id"]: row for row in officials}
    profile_domain_index = build_profile_domain_index(profile_domains)
    domain_analysis = analyze_domains(domain_rows, profile_domain_index)
    common_domain_summary = summarize_common_domains(profile_domain_index)
    threshold_simulations = simulate_thresholds(
        contracts=CONTRACTS,
        officials=officials,
        profile_domain_index=profile_domain_index,
        domain_analysis=domain_analysis,
        burden_by_legislator={row["legislator_id"]: row for row in burden_rows},
    )
    examples = choose_profile_examples(
        officials=officials,
        profile_domain_index=profile_domain_index,
        evidence_rows=evidence_rows,
        domain_analysis=domain_analysis,
        burden_by_legislator={row["legislator_id"]: row for row in burden_rows},
    )

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "analysis_scope": {
            "chamber": "house",
            "congresses": list(CONGRESSES),
            "read_only": True,
            "classification_version": latest_classification_version,
        },
        "coverage_metadata": coverage_metadata,
        "coverage_inventory": {
            "official_counts": official_counts(officials),
            "universe_roll_calls": universe_roll_call_counts(cursor, latest_classification_version),
            "house_vote_rows": house_vote_row_counts(cursor, latest_classification_version),
            "official_rollups": officials,
            "common_domain_summary": common_domain_summary,
        },
        "domain_comparability": domain_analysis,
        "threshold_simulations": threshold_simulations,
        "profile_validation_examples": examples,
        "api_semantics": api_semantics(cursor),
        "read_only_confirmation": read_only_confirmation(cursor),
        "notes": {
            "substantive_evidence_row_definition": "House official vote row where the roll call is eligible, interpreted, and the member vote is yea or nay.",
            "not_voting_definition": "Member vote rows with position not_voting; these are excluded from support/opposition and substantive evidence rows.",
            "limited_or_procedural_definition": "Rows with missing/ambiguous/insufficient interpretation or ineligible/procedural classification; these remain non-counting for support/opposition.",
            "topic_overlap_heuristic": "Issue-facet overlap is required first; measure-family and vote-type overlap are supporting signals. Shared issue domain alone is not enough.",
        },
        "selected_profile_ids": sorted({example["legislator_id"] for example in examples}),
        "officials_by_id_snapshot": {
            legislator_id: {
                "name": row["name"],
                "party": row["party"],
                "state": row["state"],
                "district": row["district"],
                "in_office": row["in_office"],
            }
            for legislator_id, row in officials_by_id.items()
        },
    }


def coverage_metadata_rows(cursor: Any) -> dict[str, Any]:
    rows = query_all(
        cursor,
        f"""
        SELECT
            CASE
                WHEN rc.congress IN (118, 119) THEN rc.congress::text
                ELSE 'other'
            END AS scope,
            MIN(DATE(rc.vote_date)) AS window_start,
            MAX(DATE(rc.vote_date)) AS window_end,
            ARRAY_AGG(DISTINCT rc.congress ORDER BY rc.congress) AS congresses,
            COUNT(DISTINCT rc.id) AS roll_call_count,
            COUNT(DISTINCT rc.id) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible_roll_call_count,
            COUNT(DISTINCT rc.id) FILTER (WHERE vi.interpretation_status = 'interpreted') AS interpreted_roll_call_count
        FROM roll_calls rc
        LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE rc.congress IN (118, 119)
        GROUP BY rc.congress
        UNION ALL
        SELECT
            'all' AS scope,
            MIN(DATE(rc.vote_date)) AS window_start,
            MAX(DATE(rc.vote_date)) AS window_end,
            ARRAY_AGG(DISTINCT rc.congress ORDER BY rc.congress) AS congresses,
            COUNT(DISTINCT rc.id) AS roll_call_count,
            COUNT(DISTINCT rc.id) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible_roll_call_count,
            COUNT(DISTINCT rc.id) FILTER (WHERE vi.interpretation_status = 'interpreted') AS interpreted_roll_call_count
        FROM roll_calls rc
        LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE rc.congress IN (118, 119)
        ORDER BY scope
        """,
    )
    return {str(row["scope"]): row for row in rows}


def official_rollups(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        f"""
        WITH per_official AS (
            SELECT
                l.id AS legislator_id,
                l.bioguide_id,
                l.name_display AS name,
                l.party,
                l.state,
                l.district,
                l.in_office,
                COUNT(vc.id) FILTER (WHERE rc.congress = 118) AS cast_rows_118,
                COUNT(vc.id) FILTER (WHERE rc.congress = 119) AS cast_rows_119,
                COUNT(vc.id) FILTER (WHERE rc.congress = 118 AND vcf.is_eligible = TRUE) AS eligible_participation_118,
                COUNT(vc.id) FILTER (WHERE rc.congress = 119 AND vcf.is_eligible = TRUE) AS eligible_participation_119,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 118
                      AND vcf.is_eligible = TRUE
                      AND vi.interpretation_status = 'interpreted'
                      AND vc.position IN ('yea', 'nay')
                ) AS substantive_rows_118,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 119
                      AND vcf.is_eligible = TRUE
                      AND vi.interpretation_status = 'interpreted'
                      AND vc.position IN ('yea', 'nay')
                ) AS substantive_rows_119,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 118
                      AND vcf.is_eligible = TRUE
                      AND vi.interpretation_status = 'interpreted'
                      AND vc.position = 'not_voting'
                ) AS not_voting_interpreted_118,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 119
                      AND vcf.is_eligible = TRUE
                      AND vi.interpretation_status = 'interpreted'
                      AND vc.position = 'not_voting'
                ) AS not_voting_interpreted_119,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 118
                      AND (vcf.is_eligible IS DISTINCT FROM TRUE OR vi.interpretation_status IS DISTINCT FROM 'interpreted')
                ) AS limited_or_procedural_rows_118,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 119
                      AND (vcf.is_eligible IS DISTINCT FROM TRUE OR vi.interpretation_status IS DISTINCT FROM 'interpreted')
                ) AS limited_or_procedural_rows_119
            FROM legislators l
            LEFT JOIN votes_cast vc ON vc.legislator_id = l.id
            LEFT JOIN roll_calls rc ON rc.id = vc.roll_call_id AND rc.congress IN (118, 119)
            LEFT JOIN vote_classifications vcf
              ON vcf.roll_call_id = rc.id
             AND vcf.classification_version = %s
            LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
            WHERE l.chamber = 'house'
            GROUP BY l.id, l.bioguide_id, l.name_display, l.party, l.state, l.district, l.in_office
        )
        SELECT *,
            (substantive_rows_118 > 0) AS has_118_substantive,
            (substantive_rows_119 > 0) AS has_119_substantive,
            (substantive_rows_118 > 0 AND substantive_rows_119 > 0) AS has_both_substantive
        FROM per_official
        ORDER BY in_office DESC, name
        """,
        (classification_version,),
    )


def universe_roll_call_counts(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        """
        SELECT
            rc.congress,
            COUNT(DISTINCT rc.id) AS universe_roll_calls,
            COUNT(DISTINCT rc.id) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible_roll_calls,
            COUNT(DISTINCT rc.id) FILTER (WHERE vcf.is_eligible = FALSE) AS ineligible_roll_calls,
            COUNT(DISTINCT rc.id) FILTER (WHERE vcf.eligibility_reason = 'procedural_vote') AS procedural_roll_calls,
            COUNT(DISTINCT rc.id) FILTER (WHERE vi.interpretation_status = 'interpreted') AS interpreted_roll_calls,
            COUNT(DISTINCT rc.id) FILTER (WHERE vi.interpretation_status = 'insufficient_evidence') AS limited_roll_calls,
            COUNT(DISTINCT rc.id) FILTER (WHERE vi.interpretation_status = 'ambiguous') AS ambiguous_roll_calls
        FROM roll_calls rc
        LEFT JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE rc.chamber = 'house'
          AND rc.congress IN (118, 119)
        GROUP BY rc.congress
        ORDER BY rc.congress
        """,
        (classification_version,),
    )


def house_vote_row_counts(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        """
        SELECT
            rc.congress,
            vc.position,
            COUNT(*) AS vote_rows,
            COUNT(*) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible_vote_rows,
            COUNT(*) FILTER (WHERE vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted') AS interpreted_eligible_vote_rows,
            COUNT(*) FILTER (
                WHERE vcf.is_eligible = TRUE
                  AND vi.interpretation_status = 'interpreted'
                  AND vc.position IN ('yea', 'nay')
            ) AS substantive_vote_rows
        FROM votes_cast vc
        JOIN legislators l ON l.id = vc.legislator_id
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        LEFT JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE l.chamber = 'house'
          AND rc.chamber = 'house'
          AND rc.congress IN (118, 119)
        GROUP BY rc.congress, vc.position
        ORDER BY rc.congress, vc.position
        """,
        (classification_version,),
    )


def domain_rollups(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        f"""
        WITH domain_votes AS (
            SELECT
                rc.congress,
                vcf.primary_domain AS domain,
                rc.id AS roll_call_id,
                COALESCE(NULLIF(vi.issue_facet, ''), 'unspecified') AS issue_facet,
                COALESCE(vctx.vote_type, {vote_type_case_sql()}) AS vote_type,
                rc.question,
                rc.description,
                COALESCE(b.title, '') AS bill_title,
                vc.legislator_id,
                vc.position,
                vi.support_position,
                vi.oppose_position,
                vi.confidence
            FROM votes_cast vc
            JOIN legislators l ON l.id = vc.legislator_id
            JOIN roll_calls rc ON rc.id = vc.roll_call_id
            JOIN vote_classifications vcf
              ON vcf.roll_call_id = rc.id
             AND vcf.classification_version = %s
             AND vcf.is_eligible = TRUE
             AND vcf.primary_domain IS NOT NULL
            JOIN vote_interpretations vi
              ON vi.roll_call_id = rc.id
             AND vi.interpretation_status = 'interpreted'
            LEFT JOIN vote_contexts vctx
              ON vctx.roll_call_id = rc.id
             AND vctx.legislator_id = vc.legislator_id
            LEFT JOIN bills b ON b.id = rc.bill_id
            WHERE l.chamber = 'house'
              AND rc.chamber = 'house'
              AND rc.congress IN (118, 119)
        )
        SELECT
            congress,
            domain,
            COUNT(*) FILTER (WHERE position IN ('yea', 'nay')) AS substantive_rows,
            COUNT(DISTINCT legislator_id) FILTER (WHERE position IN ('yea', 'nay')) AS officials_with_substantive_rows,
            COUNT(DISTINCT roll_call_id) AS interpreted_roll_calls,
            COUNT(DISTINCT issue_facet) AS issue_facets,
            ARRAY_AGG(DISTINCT issue_facet ORDER BY issue_facet) AS issue_facet_values,
            COUNT(*) FILTER (WHERE vote_type = 'amendment' AND position IN ('yea', 'nay')) AS amendment_rows,
            COUNT(*) FILTER (WHERE vote_type = 'final_passage' AND position IN ('yea', 'nay')) AS final_passage_rows,
            COUNT(*) FILTER (WHERE vote_type NOT IN ('amendment', 'final_passage') AND position IN ('yea', 'nay')) AS other_vote_type_rows,
            COUNT(*) FILTER (WHERE position = 'not_voting') AS not_voting_rows,
            COUNT(*) FILTER (WHERE position = support_position) AS support_rows,
            COUNT(*) FILTER (WHERE position = oppose_position) AS oppose_rows,
            COUNT(*) FILTER (WHERE confidence IS NOT NULL AND LOWER(confidence) IN ('low', 'medium_low')) AS lower_confidence_rows,
            ARRAY_AGG(DISTINCT vote_type ORDER BY vote_type) AS vote_types,
            ARRAY_AGG(DISTINCT LEFT(question, 180) ORDER BY LEFT(question, 180)) FILTER (WHERE question IS NOT NULL) AS question_samples,
            ARRAY_AGG(DISTINCT LEFT(bill_title, 180) ORDER BY LEFT(bill_title, 180)) FILTER (WHERE bill_title <> '') AS bill_title_samples
        FROM domain_votes
        GROUP BY congress, domain
        ORDER BY domain, congress
        """,
        (classification_version,),
    )


def profile_domain_rows(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        f"""
        SELECT
            l.id AS legislator_id,
            l.name_display AS name,
            l.in_office,
            rc.congress,
            vcf.primary_domain AS domain,
            COUNT(*) FILTER (WHERE vc.position IN ('yea', 'nay')) AS substantive_rows,
            COUNT(*) FILTER (WHERE vc.position = vi.support_position) AS support_rows,
            COUNT(*) FILTER (WHERE vc.position = vi.oppose_position) AS oppose_rows,
            COUNT(*) FILTER (WHERE vc.position = 'not_voting') AS not_voting_rows,
            COUNT(DISTINCT rc.id) AS interpreted_roll_calls,
            ARRAY_AGG(DISTINCT COALESCE(NULLIF(vi.issue_facet, ''), 'unspecified') ORDER BY COALESCE(NULLIF(vi.issue_facet, ''), 'unspecified')) AS issue_facets,
            ARRAY_AGG(DISTINCT COALESCE(vctx.vote_type, {vote_type_case_sql()}) ORDER BY COALESCE(vctx.vote_type, {vote_type_case_sql()})) AS vote_types
        FROM legislators l
        JOIN votes_cast vc ON vc.legislator_id = l.id
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
         AND vcf.is_eligible = TRUE
         AND vcf.primary_domain IS NOT NULL
        JOIN vote_interpretations vi
          ON vi.roll_call_id = rc.id
         AND vi.interpretation_status = 'interpreted'
        LEFT JOIN vote_contexts vctx
          ON vctx.roll_call_id = rc.id
         AND vctx.legislator_id = l.id
        WHERE l.chamber = 'house'
          AND rc.chamber = 'house'
          AND rc.congress IN (118, 119)
        GROUP BY l.id, l.name_display, l.in_office, rc.congress, vcf.primary_domain
        ORDER BY l.name_display, vcf.primary_domain, rc.congress
        """,
        (classification_version,),
    )


def substantive_evidence_rows(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        f"""
        SELECT
            l.id AS legislator_id,
            l.bioguide_id,
            l.name_display AS name,
            l.party,
            l.state,
            l.district,
            l.in_office,
            rc.congress,
            vcf.primary_domain AS domain,
            rc.id AS roll_call_id,
            rc.rollcall_number,
            DATE(rc.vote_date) AS vote_date,
            vc.position,
            vi.support_position,
            vi.oppose_position,
            COALESCE(NULLIF(vi.issue_facet, ''), 'unspecified') AS issue_facet,
            COALESCE(vctx.vote_type, {vote_type_case_sql()}) AS vote_type,
            rc.question,
            rc.description,
            COALESCE(b.bill_type, '') AS bill_type,
            b.bill_number,
            COALESCE(b.title, '') AS bill_title,
            vi.plain_english_summary,
            vi.what_happened,
            vi.why_it_mattered,
            vi.what_not_to_infer,
            vi.uncertainty_note,
            vi.source_basis
        FROM legislators l
        JOIN votes_cast vc ON vc.legislator_id = l.id
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
         AND vcf.is_eligible = TRUE
         AND vcf.primary_domain IS NOT NULL
        JOIN vote_interpretations vi
          ON vi.roll_call_id = rc.id
         AND vi.interpretation_status = 'interpreted'
        LEFT JOIN vote_contexts vctx
          ON vctx.roll_call_id = rc.id
         AND vctx.legislator_id = l.id
        LEFT JOIN bills b ON b.id = rc.bill_id
        WHERE l.chamber = 'house'
          AND rc.chamber = 'house'
          AND rc.congress IN (118, 119)
        ORDER BY l.name_display, rc.congress, vcf.primary_domain, rc.vote_date, rc.rollcall_number
        """,
        (classification_version,),
    )


def burden_by_official(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        """
        SELECT
            l.id AS legislator_id,
            COUNT(*) AS total_house_vote_rows,
            COUNT(*) FILTER (WHERE vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted') AS interpreted_eligible_rows,
            COUNT(*) FILTER (WHERE vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted' AND vc.position = 'not_voting') AS not_voting_interpreted_rows,
            COUNT(*) FILTER (WHERE vcf.is_eligible IS DISTINCT FROM TRUE OR vi.interpretation_status IS DISTINCT FROM 'interpreted') AS limited_or_procedural_rows
        FROM legislators l
        LEFT JOIN votes_cast vc ON vc.legislator_id = l.id
        LEFT JOIN roll_calls rc ON rc.id = vc.roll_call_id AND rc.chamber = 'house' AND rc.congress IN (118, 119)
        LEFT JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE l.chamber = 'house'
        GROUP BY l.id
        """,
        (classification_version,),
    )


def build_profile_domain_index(rows: list[dict[str, Any]]) -> dict[int, dict[str, dict[int, dict[str, Any]]]]:
    index: dict[int, dict[str, dict[int, dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        index[row["legislator_id"]][row["domain"]][row["congress"]] = row
    return index


def analyze_domains(
    domain_rows: list[dict[str, Any]],
    profile_domain_index: dict[int, dict[str, dict[int, dict[str, Any]]]],
) -> list[dict[str, Any]]:
    by_domain: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in domain_rows:
        by_domain[row["domain"]][row["congress"]] = row

    results = []
    for domain in DOMAINS:
        row_118 = by_domain.get(domain, {}).get(118, empty_domain_row(domain, 118))
        row_119 = by_domain.get(domain, {}).get(119, empty_domain_row(domain, 119))
        facets_118 = set(row_118.get("issue_facet_values") or [])
        facets_119 = set(row_119.get("issue_facet_values") or [])
        common_facets = sorted(facets_118 & facets_119)
        material_topic_overlap = has_material_topic_overlap(domain, common_facets)
        officials_both = officials_with_domain_both(profile_domain_index, domain)
        vote_type_overlap = sorted(set(row_118.get("vote_types") or []) & set(row_119.get("vote_types") or []))
        opportunity_balance = opportunity_balance_score(row_118, row_119)
        classification = classify_domain(
            domain,
            row_118,
            row_119,
            common_facets,
            material_topic_overlap,
            officials_both,
            vote_type_overlap,
            opportunity_balance,
        )
        results.append(
            {
                "domain": domain,
                "classification": classification,
                "material_topic_overlap_from_structured_fields": material_topic_overlap,
                "interpreted_substantive_rows_118": int(row_118["substantive_rows"] or 0),
                "interpreted_substantive_rows_119": int(row_119["substantive_rows"] or 0),
                "interpreted_roll_calls_118": int(row_118["interpreted_roll_calls"] or 0),
                "interpreted_roll_calls_119": int(row_119["interpreted_roll_calls"] or 0),
                "officials_with_evidence_both": len(officials_both),
                "common_issue_facets": common_facets,
                "issue_facets_118": sorted(facets_118),
                "issue_facets_119": sorted(facets_119),
                "vote_type_overlap": vote_type_overlap,
                "composition_118": vote_composition(row_118),
                "composition_119": vote_composition(row_119),
                "support_opposition_balance": opportunity_balance,
                "not_voting_burden_118": share(row_118.get("not_voting_rows", 0), int(row_118.get("not_voting_rows", 0) or 0) + int(row_118.get("substantive_rows", 0) or 0)),
                "not_voting_burden_119": share(row_119.get("not_voting_rows", 0), int(row_119.get("not_voting_rows", 0) or 0) + int(row_119.get("substantive_rows", 0) or 0)),
                "confidence_ambiguity_signal": {
                    "lower_confidence_rows_118": int(row_118.get("lower_confidence_rows", 0) or 0),
                    "lower_confidence_rows_119": int(row_119.get("lower_confidence_rows", 0) or 0),
                },
                "question_samples_118": list(row_118.get("question_samples") or [])[:5],
                "question_samples_119": list(row_119.get("question_samples") or [])[:5],
                "bill_title_samples_118": list(row_118.get("bill_title_samples") or [])[:5],
                "bill_title_samples_119": list(row_119.get("bill_title_samples") or [])[:5],
                "risk_notes": domain_risk_notes(row_118, row_119, common_facets, vote_type_overlap, opportunity_balance),
            }
        )
    return results


def classify_domain(
    domain: str,
    row_118: dict[str, Any],
    row_119: dict[str, Any],
    common_facets: list[str],
    material_topic_overlap: bool,
    officials_both: set[int],
    vote_type_overlap: list[str],
    opportunity_balance: dict[str, Any],
) -> str:
    rows_118 = int(row_118.get("substantive_rows", 0) or 0)
    rows_119 = int(row_119.get("substantive_rows", 0) or 0)
    if rows_118 < 50 or rows_119 < 50 or len(officials_both) < 25:
        return "not currently comparable"
    if not common_facets or not vote_type_overlap:
        return "not currently comparable"
    if material_topic_overlap and opportunity_balance["has_support_and_oppose_both_congresses"] and len(common_facets) >= 2 and len(officials_both) >= 100:
        return "strongly comparable"
    return DOMAIN_COMPARABILITY_OVERRIDE.get(domain, "not currently comparable")


def domain_risk_notes(
    row_118: dict[str, Any],
    row_119: dict[str, Any],
    common_facets: list[str],
    vote_type_overlap: list[str],
    opportunity_balance: dict[str, Any],
) -> list[str]:
    notes = []
    if not common_facets:
        notes.append("No issue-facet overlap across Congresses; agenda composition can dominate apparent change.")
    elif set(common_facets) <= {"unspecified", str(row_118.get("domain", "")).lower()}:
        notes.append("Common issue facets are broad-domain labels, not material policy-question matches.")
    if not vote_type_overlap:
        notes.append("Vote-type mix does not overlap; amendment/final-passage composition can distort comparison.")
    if not opportunity_balance["has_support_and_oppose_both_congresses"]:
        notes.append("Support/opposition opportunity balance is one-sided in at least one Congress.")
    for congress, row in ((118, row_118), (119, row_119)):
        substantive = int(row.get("substantive_rows", 0) or 0)
        not_voting = int(row.get("not_voting_rows", 0) or 0)
        if substantive and share(not_voting, substantive + not_voting) >= 0.2:
            notes.append(f"{congress} has a material not-voting burden.")
    return notes or ["Comparable only to the extent the underlying policy questions and vote types align."]


def summarize_common_domains(index: dict[int, dict[str, dict[int, dict[str, Any]]]]) -> dict[str, Any]:
    counts = Counter()
    distribution = Counter()
    for domains in index.values():
        common = [domain for domain, congresses in domains.items() if 118 in congresses and 119 in congresses]
        common_with_rows = [
            domain
            for domain, congresses in domains.items()
            if int(congresses.get(118, {}).get("substantive_rows", 0) or 0) > 0
            and int(congresses.get(119, {}).get("substantive_rows", 0) or 0) > 0
        ]
        if common_with_rows:
            counts["officials_with_at_least_one_common_domain"] += 1
        if len(common_with_rows) > 1:
            counts["officials_with_multiple_common_domains"] += 1
        distribution[len(common)] += 1
    return {
        **counts,
        "common_domain_count_distribution": {str(key): value for key, value in sorted(distribution.items())},
    }


def simulate_thresholds(
    *,
    contracts: tuple[Contract, ...],
    officials: list[dict[str, Any]],
    profile_domain_index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    domain_analysis: list[dict[str, Any]],
    burden_by_legislator: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_comparable = {row["domain"]: row for row in domain_analysis}
    current_house_total = sum(1 for row in officials if row["in_office"])
    all_house_total = len(officials)
    results = []
    for contract in contracts:
        eligible_ids = []
        represented_domains = Counter()
        exclusions = Counter()
        for official in officials:
            if contract.current_only and not official["in_office"]:
                continue
            legislator_id = official["legislator_id"]
            eligible_domains = []
            primary_exclusion = "no_common_domain"
            for domain, congresses in profile_domain_index.get(legislator_id, {}).items():
                row_118 = congresses.get(118)
                row_119 = congresses.get(119)
                if not row_118 or not row_119:
                    continue
                if int(row_118.get("substantive_rows", 0) or 0) < contract.min_rows_per_common_domain_per_congress:
                    primary_exclusion = "below_row_threshold"
                    continue
                if int(row_119.get("substantive_rows", 0) or 0) < contract.min_rows_per_common_domain_per_congress:
                    primary_exclusion = "below_row_threshold"
                    continue
                domain_row = domain_comparable[domain]
                if contract.require_topic_overlap and domain_row["classification"] == "not currently comparable":
                    primary_exclusion = "no_material_topic_overlap"
                    continue
                if contract.require_balanced_opportunities and not domain_row["support_opposition_balance"]["has_support_and_oppose_both_congresses"]:
                    primary_exclusion = "one_sided_opportunities"
                    continue
                eligible_domains.append(domain)
            burden = burden_by_legislator.get(legislator_id, {})
            if len(eligible_domains) >= contract.min_common_domains:
                if exceeds_burden(contract, burden):
                    exclusions["burden_controls"] += 1
                else:
                    eligible_ids.append(legislator_id)
                    represented_domains.update(eligible_domains)
            else:
                exclusions[primary_exclusion] += 1
        eligible_current = len(eligible_ids)
        results.append(
            {
                "contract": contract.name,
                "min_rows_per_common_domain_per_congress": contract.min_rows_per_common_domain_per_congress,
                "min_common_domains": contract.min_common_domains,
                "max_limited_procedural_share": contract.max_limited_procedural_share,
                "max_not_voting_share": contract.max_not_voting_share,
                "require_topic_overlap": contract.require_topic_overlap,
                "require_balanced_opportunities": contract.require_balanced_opportunities,
                "eligible_current_house_officials": eligible_current,
                "eligible_current_house_share": share(eligible_current, current_house_total),
                "eligible_all_house_profiles": eligible_current if contract.current_only else len(eligible_ids),
                "eligible_all_house_share": share(eligible_current if contract.current_only else len(eligible_ids), all_house_total),
                "represented_domains": dict(sorted(represented_domains.items())),
                "primary_exclusion_reasons": dict(sorted(exclusions.items())),
                "false_or_overstated_change_risk": contract_risk(contract, eligible_current, current_house_total),
            }
        )
    return results


def choose_profile_examples(
    *,
    officials: list[dict[str, Any]],
    profile_domain_index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    evidence_rows: list[dict[str, Any]],
    domain_analysis: list[dict[str, Any]],
    burden_by_legislator: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_official: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        rows_by_official[row["legislator_id"]].append(row)
    official_by_id = {row["legislator_id"]: row for row in officials}
    by_name = {normalize_name(row["name"]): row for row in officials}
    examples: list[dict[str, Any]] = []
    used: set[int] = set()

    def add(category: str, row: dict[str, Any] | None) -> None:
        if row is None:
            return
        legislator_id = row["legislator_id"]
        example = build_profile_example(
            category=category,
            official=row,
            domains=profile_domain_index.get(legislator_id, {}),
            evidence=rows_by_official.get(legislator_id, []),
            domain_analysis=domain_analysis,
            burden=burden_by_legislator.get(legislator_id, {}),
        )
        examples.append(example)
        used.add(legislator_id)

    add("required_valerie_foushee", by_name.get("valerie p foushee") or find_name(officials, "foushee"))
    add("required_aaron_bean", by_name.get("aaron bean") or find_name(officials, "bean"))
    add("strong_evidence_both", max_candidate(officials, profile_domain_index, used, lambda row: common_substantive_total(row, profile_domain_index)))
    add("apparent_continuity", find_pattern_candidate(officials, profile_domain_index, used, want_change=False))
    add("apparent_change", find_pattern_candidate(officials, profile_domain_index, used, want_change=True))
    add("agenda_difference_unsafe", find_agenda_unsafe_candidate(officials, profile_domain_index, domain_analysis, used))
    add("118th_only", first_candidate(officials, used, lambda row: row["substantive_rows_118"] > 0 and row["substantive_rows_119"] == 0))
    add("119th_only", first_candidate(officials, used, lambda row: row["substantive_rows_119"] > 0 and row["substantive_rows_118"] == 0))
    add("sparse_profile", first_candidate(officials, used, lambda row: 0 < row["substantive_rows_118"] + row["substantive_rows_119"] <= 3))
    add("meaningful_not_voting_burden", max_candidate(officials, profile_domain_index, used, lambda row: not_voting_share(row)))

    for example in examples:
        if "official" not in example and example["legislator_id"] in official_by_id:
            example["official"] = official_by_id[example["legislator_id"]]["name"]
    return examples


def build_profile_example(
    *,
    category: str,
    official: dict[str, Any],
    domains: dict[str, dict[int, dict[str, Any]]],
    evidence: list[dict[str, Any]],
    domain_analysis: list[dict[str, Any]],
    burden: dict[str, Any],
) -> dict[str, Any]:
    common_domains = [
        domain
        for domain, congresses in domains.items()
        if int(congresses.get(118, {}).get("substantive_rows", 0) or 0) > 0
        and int(congresses.get(119, {}).get("substantive_rows", 0) or 0) > 0
    ]
    comparable_by_domain = {row["domain"]: row for row in domain_analysis}
    comparable_questions = []
    non_comparable_questions = []
    for domain in common_domains:
        domain_row = comparable_by_domain[domain]
        target = comparable_questions if domain_row["classification"] != "not currently comparable" else non_comparable_questions
        target.append(
            {
                "domain": domain,
                "common_issue_facets": domain_row["common_issue_facets"],
                "classification": domain_row["classification"],
            }
        )
    samples = sample_evidence(evidence)
    allowed = False
    if not common_domains:
        safest = "Record across Congresses with single-Congress or insufficient-comparison language."
    elif allowed:
        safest = "Issue-by-issue comparison with explicit evidence counts and agenda caveats."
    else:
        safest = "Record across Congresses; do not state continuity/change."
    return {
        "category": category,
        "legislator_id": official["legislator_id"],
        "official": official["name"],
        "party": official["party"],
        "state": official["state"],
        "district": official["district"],
        "in_office": bool(official["in_office"]),
        "evidence_basis_118": {
            "substantive_rows": int(official["substantive_rows_118"] or 0),
            "not_voting_interpreted": int(official["not_voting_interpreted_118"] or 0),
            "sample_rows": samples.get(118, []),
        },
        "evidence_basis_119": {
            "substantive_rows": int(official["substantive_rows_119"] or 0),
            "not_voting_interpreted": int(official["not_voting_interpreted_119"] or 0),
            "sample_rows": samples.get(119, []),
        },
        "common_domains": sorted(common_domains),
        "comparable_policy_questions": comparable_questions,
        "non_comparable_questions": non_comparable_questions,
        "continuity_change_claim_allowed": allowed,
        "safest_user_facing_framing": safest,
        "burden": {
            "not_voting_share": share(burden.get("not_voting_interpreted_rows", 0), burden.get("interpreted_eligible_rows", 0)),
            "limited_procedural_share": share(burden.get("limited_or_procedural_rows", 0), burden.get("total_house_vote_rows", 0)),
        },
    }


def sample_evidence(evidence: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    samples: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[int, str]] = set()
    for row in evidence:
        if row["position"] not in {"yea", "nay"}:
            continue
        key = (row["congress"], row["domain"])
        if key in seen and len(samples[row["congress"]]) >= 5:
            continue
        if len(samples[row["congress"]]) >= 6:
            continue
        samples[row["congress"]].append(
            {
                "domain": row["domain"],
                "roll_call_id": row["roll_call_id"],
                "rollcall_number": row["rollcall_number"],
                "vote_date": row["vote_date"],
                "position": row["position"],
                "support_position": row["support_position"],
                "oppose_position": row["oppose_position"],
                "issue_facet": row["issue_facet"],
                "vote_type": row["vote_type"],
                "question": row["question"],
                "bill_title": row["bill_title"],
                "plain_english_summary": row["plain_english_summary"],
            }
        )
        seen.add(key)
    return samples


def official_counts(officials: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "all_house_profiles": len(officials),
        "current_house_officials": sum(1 for row in officials if row["in_office"]),
        "former_house_officials": sum(1 for row in officials if not row["in_office"]),
        "current_with_118_substantive": sum(1 for row in officials if row["in_office"] and row["substantive_rows_118"] > 0),
        "current_with_119_substantive": sum(1 for row in officials if row["in_office"] and row["substantive_rows_119"] > 0),
        "current_with_both_substantive": sum(1 for row in officials if row["in_office"] and row["has_both_substantive"]),
        "current_with_only_one_congress_substantive": sum(
            1
            for row in officials
            if row["in_office"] and ((row["substantive_rows_118"] > 0) ^ (row["substantive_rows_119"] > 0))
        ),
        "current_with_no_substantive_interpreted_evidence": sum(
            1 for row in officials if row["in_office"] and row["substantive_rows_118"] == 0 and row["substantive_rows_119"] == 0
        ),
        "former_with_118_substantive": sum(1 for row in officials if not row["in_office"] and row["substantive_rows_118"] > 0),
        "former_with_119_substantive": sum(1 for row in officials if not row["in_office"] and row["substantive_rows_119"] > 0),
        "former_with_both_substantive": sum(1 for row in officials if not row["in_office"] and row["has_both_substantive"]),
    }


def api_semantics(cursor: Any) -> dict[str, Any]:
    rows = coverage_metadata_rows(cursor)
    return {
        "scope_all_congresses": rows["all"]["congresses"],
        "scope_118_congresses": rows["118"]["congresses"],
        "scope_119_congresses": rows["119"]["congresses"],
        "coverage_counts_are_universe_level": True,
        "official_specific_records_require_votes_cast_join": True,
        "public_label_note": "/metadata/coverage and scope_metadata eligible_roll_call_count count distinct eligible roll calls in the selected Congress scope; they do not count per-official vote rows.",
    }


def read_only_confirmation(cursor: Any) -> dict[str, Any]:
    return {
        "transaction_read_only": scalar(cursor, "SHOW transaction_read_only"),
        "no_write_statements_in_script": True,
        "tables_changed": "not_applicable_read_only_transaction",
    }


def empty_domain_row(domain: str, congress: int) -> dict[str, Any]:
    return {
        "domain": domain,
        "congress": congress,
        "substantive_rows": 0,
        "officials_with_substantive_rows": 0,
        "interpreted_roll_calls": 0,
        "issue_facet_values": [],
        "vote_types": [],
        "amendment_rows": 0,
        "final_passage_rows": 0,
        "other_vote_type_rows": 0,
        "not_voting_rows": 0,
        "support_rows": 0,
        "oppose_rows": 0,
        "lower_confidence_rows": 0,
        "question_samples": [],
        "bill_title_samples": [],
    }


def vote_composition(row: dict[str, Any]) -> dict[str, int]:
    return {
        "amendment_rows": int(row.get("amendment_rows", 0) or 0),
        "final_passage_rows": int(row.get("final_passage_rows", 0) or 0),
        "other_vote_type_rows": int(row.get("other_vote_type_rows", 0) or 0),
    }


def opportunity_balance_score(row_118: dict[str, Any], row_119: dict[str, Any]) -> dict[str, Any]:
    support_118 = int(row_118.get("support_rows", 0) or 0)
    oppose_118 = int(row_118.get("oppose_rows", 0) or 0)
    support_119 = int(row_119.get("support_rows", 0) or 0)
    oppose_119 = int(row_119.get("oppose_rows", 0) or 0)
    return {
        "support_rows_118": support_118,
        "oppose_rows_118": oppose_118,
        "support_rows_119": support_119,
        "oppose_rows_119": oppose_119,
        "support_share_118": share(support_118, support_118 + oppose_118),
        "support_share_119": share(support_119, support_119 + oppose_119),
        "has_support_and_oppose_both_congresses": support_118 > 0 and oppose_118 > 0 and support_119 > 0 and oppose_119 > 0,
    }


def has_material_topic_overlap(domain: str, common_facets: list[str]) -> bool:
    broad_labels = {domain.lower(), "unspecified"}
    return bool(set(common_facets) - broad_labels)


def officials_with_domain_both(index: dict[int, dict[str, dict[int, dict[str, Any]]]], domain: str) -> set[int]:
    ids = set()
    for legislator_id, domains in index.items():
        congresses = domains.get(domain, {})
        if int(congresses.get(118, {}).get("substantive_rows", 0) or 0) > 0 and int(congresses.get(119, {}).get("substantive_rows", 0) or 0) > 0:
            ids.add(legislator_id)
    return ids


def exceeds_burden(contract: Contract, burden: dict[str, Any]) -> bool:
    if contract.max_not_voting_share is not None:
        if share(burden.get("not_voting_interpreted_rows", 0), burden.get("interpreted_eligible_rows", 0)) > contract.max_not_voting_share:
            return True
    if contract.max_limited_procedural_share is not None:
        if share(burden.get("limited_or_procedural_rows", 0), burden.get("total_house_vote_rows", 0)) > contract.max_limited_procedural_share:
            return True
    return False


def contract_risk(contract: Contract, eligible: int, total: int) -> str:
    if not contract.require_topic_overlap:
        return "high: shared broad issue domain can hide different agendas."
    if not contract.require_balanced_opportunities:
        return "medium-high: topic overlap exists but one-sided opportunity mix can overstate change."
    if contract.min_common_domains < 2:
        return "medium: one domain can still be agenda-sensitive."
    if share(eligible, total) < 0.1:
        return "lower for qualifying profiles, but coverage is too narrow for broad product value."
    return "lower for qualifying profiles with explicit caveats."


def common_substantive_total(row: dict[str, Any], index: dict[int, dict[str, dict[int, dict[str, Any]]]]) -> int:
    total = 0
    for congresses in index.get(row["legislator_id"], {}).values():
        if 118 in congresses and 119 in congresses:
            total += int(congresses[118].get("substantive_rows", 0) or 0)
            total += int(congresses[119].get("substantive_rows", 0) or 0)
    return total


def not_voting_share(row: dict[str, Any]) -> float:
    not_voting = int(row.get("not_voting_interpreted_118", 0) or 0) + int(row.get("not_voting_interpreted_119", 0) or 0)
    substantive = int(row.get("substantive_rows_118", 0) or 0) + int(row.get("substantive_rows_119", 0) or 0)
    return share(not_voting, not_voting + substantive)


def find_pattern_candidate(
    officials: list[dict[str, Any]],
    index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    used: set[int],
    *,
    want_change: bool,
) -> dict[str, Any] | None:
    for row in sorted(officials, key=lambda official: common_substantive_total(official, index), reverse=True):
        if row["legislator_id"] in used or not row["in_office"]:
            continue
        for congresses in index.get(row["legislator_id"], {}).values():
            if 118 not in congresses or 119 not in congresses:
                continue
            pattern_118 = pattern(congresses[118])
            pattern_119 = pattern(congresses[119])
            if pattern_118 == "mixed" or pattern_119 == "mixed":
                continue
            if want_change and pattern_118 != pattern_119:
                return row
            if not want_change and pattern_118 == pattern_119 and pattern_118 != "insufficient":
                return row
    return None


def find_agenda_unsafe_candidate(
    officials: list[dict[str, Any]],
    index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    domain_analysis: list[dict[str, Any]],
    used: set[int],
) -> dict[str, Any] | None:
    unsafe_domains = {row["domain"] for row in domain_analysis if not row["common_issue_facets"] or row["classification"] == "not currently comparable"}
    for row in sorted(officials, key=lambda official: common_substantive_total(official, index), reverse=True):
        if row["legislator_id"] in used or not row["in_office"]:
            continue
        for domain in unsafe_domains:
            congresses = index.get(row["legislator_id"], {}).get(domain, {})
            if 118 in congresses and 119 in congresses:
                return row
    return None


def first_candidate(officials: list[dict[str, Any]], used: set[int], predicate: Any) -> dict[str, Any] | None:
    for row in officials:
        if row["legislator_id"] not in used and predicate(row):
            return row
    return None


def max_candidate(
    officials: list[dict[str, Any]],
    index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    used: set[int],
    score: Any,
) -> dict[str, Any] | None:
    candidates = [row for row in officials if row["legislator_id"] not in used and row["in_office"]]
    if not candidates:
        return None
    best = max(candidates, key=score)
    return best if score(best) > 0 else None


def pattern(row: dict[str, Any]) -> str:
    support_rows = int(row.get("support_rows", 0) or 0)
    oppose_rows = int(row.get("oppose_rows", 0) or 0)
    if support_rows <= 0 and oppose_rows <= 0:
        return "insufficient"
    if support_rows > 0 and oppose_rows > 0:
        return "mixed"
    if support_rows > oppose_rows:
        return "mostly_supported"
    return "mostly_opposed"


def find_name(officials: list[dict[str, Any]], needle: str) -> dict[str, Any] | None:
    needle = needle.lower()
    for row in officials:
        if needle in row["name"].lower():
            return row
    return None


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def vote_type_case_sql() -> str:
    return """
    CASE
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%amend%%' THEN 'amendment'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%passage%%'
          OR LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%on passage%%' THEN 'final_passage'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%rule%%' THEN 'rule'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%motion%%' THEN 'motion'
        ELSE 'other'
    END
    """


def query_all(cursor: Any, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]


def scalar(cursor: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    cursor.execute(sql, params)
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def share(numerator: Any, denominator: Any) -> float:
    denominator_int = int(denominator or 0)
    if denominator_int <= 0:
        return 0.0
    return round(int(numerator or 0) / denominator_int, 4)


def write_threshold_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "contract",
        "eligible_current_house_officials",
        "eligible_current_house_share",
        "eligible_all_house_profiles",
        "eligible_all_house_share",
        "represented_domains",
        "primary_exclusion_reasons",
        "false_or_overstated_change_risk",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row[field], sort_keys=True) if isinstance(row[field], dict) else row[field] for field in fieldnames})


def write_profile_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "official",
        "party",
        "state",
        "district",
        "in_office",
        "common_domains",
        "continuity_change_claim_allowed",
        "safest_user_facing_framing",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row[field], sort_keys=True) if isinstance(row[field], list) else row[field] for field in fieldnames})


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    main()
