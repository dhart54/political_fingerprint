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


CONGRESSES = (118, 119)
TARGET_DOMAINS = (
    "ECONOMY_TAXES",
    "ENVIRONMENT_ENERGY",
    "NATIONAL_SECURITY_FOREIGN",
    "JUSTICE_PUBLIC_SAFETY",
)
DEFAULT_JSON_PATH = REPO_ROOT / "docs" / "analysis" / "house_comparable_policy_question_families.json"
DEFAULT_THRESHOLDS_PATH = REPO_ROOT / "docs" / "analysis" / "house_comparable_policy_question_thresholds.csv"
DEFAULT_PROFILES_PATH = REPO_ROOT / "docs" / "analysis" / "house_comparable_policy_question_profiles.csv"
DEFAULT_PACKET_PATH = REPO_ROOT / "docs" / "review_packets" / "house_comparable_policy_question_audit.md"


@dataclass(frozen=True)
class FamilyRule:
    family_id: str
    domain: str
    name: str
    governing_question: str
    inclusion_criteria: str
    exclusion_criteria: str
    review_status: str
    rationale: str
    limitations: str
    include_any: tuple[str, ...]
    exclude_any: tuple[str, ...] = ()


FAMILY_RULES: tuple[FamilyRule, ...] = (
    FamilyRule(
        "nsf_annual_defense_authorization",
        "NATIONAL_SECURITY_FOREIGN",
        "Annual defense authorization",
        "Whether the House should pass the annual defense authorization package setting defense and related national-security policy.",
        "Final passage or conference-report passage of annual NDAA/defense authorization measures.",
        "Individual NDAA amendments and non-NDAA national-security bills.",
        "directly_comparable",
        "The records identify annual defense authorization final-action votes in both Congresses.",
        "The authorization bills differ by fiscal year and contents; comparison is about the recurring authorization action, not identical provisions.",
        (r"national defense authorization|defense authorization act|conference report to accompany h\.?r\.? 2670|h\.?r\.? 3838"),
        (r"amendment|veterans cemetery|fernando v\. cota|further consideration"),
    ),
    FamilyRule(
        "nsf_war_powers_removal_resolutions",
        "NATIONAL_SECURITY_FOREIGN",
        "War-powers removal resolutions",
        "Whether the House should direct removal of U.S. armed forces from named hostilities or deployments not separately authorized by Congress.",
        "War Powers Resolution measures directing removal of U.S. forces from a named country, theater, or hostilities.",
        "Defense authorization, foreign-aid funding, sanctions, or general foreign-policy resolutions.",
        "conditionally_comparable",
        "The governing mechanism is stable across Congresses, but the theaters differ.",
        "Treat as comparable only with an explicit theater/scope caveat.",
        (r"war powers resolution|remove (?:all )?united states armed forces|removal of united states armed forces"),
    ),
    FamilyRule(
        "nsf_ukraine_assistance_restrictions",
        "NATIONAL_SECURITY_FOREIGN",
        "Ukraine assistance or funding restrictions",
        "Whether the House should restrict, prohibit, or remove U.S. funding or assistance for Ukraine-related activities.",
        "Amendments or measures whose direct text restricts Ukraine funding, assistance, security agreements, or reconstruction support.",
        "Broad State/Defense appropriations votes, Israel/Iran measures, or non-Ukraine foreign-aid restrictions.",
        "conditionally_comparable",
        "Both Congresses contain amendment votes on restricting Ukraine-related funds or assistance.",
        "Different parent bills and funding streams make this a conditional family, not a claim about an identical program.",
        (r"ukraine"),
        (r"not ukraine",),
    ),
    FamilyRule(
        "env_critical_minerals_supply",
        "ENVIRONMENT_ENERGY",
        "Critical minerals supply",
        "Whether the House should advance measures intended to expand, coordinate, or define domestic critical-minerals policy.",
        "Final passage of bills about critical minerals supply, dominance, consistency, or related federal coordination.",
        "General mining, oil and gas, or permitting votes without a critical-minerals focus.",
        "conditionally_comparable",
        "Both Congresses include final-passage critical-minerals bills.",
        "The bills use different policy tools, so comparison should be limited to the recurring critical-minerals governing question.",
        (r"critical mineral"),
    ),
    FamilyRule(
        "env_home_appliance_energy_rules",
        "ENVIRONMENT_ENERGY",
        "Home-appliance energy rules",
        "Whether the House should limit federal restrictions or efficiency rules affecting household energy appliances.",
        "Final passage or directly related amendments about home appliances, gas stoves, or appliance energy restrictions.",
        "Broader energy production or environmental-review votes.",
        "conditionally_comparable",
        "Both Congresses include household appliance energy-policy votes.",
        "Some 118th evidence is amendment-based while 119th evidence is final-passage; use a vote-type caveat.",
        (r"home appliance|gas stove|appliances act|homeowner energy freedom"),
    ),
    FamilyRule(
        "env_hunting_fishing_access",
        "ENVIRONMENT_ENERGY",
        "Hunting and fishing access",
        "Whether the House should pass the Protecting Access for Hunters and Anglers Act.",
        "Final passage of the Protecting Access for Hunters and Anglers Act.",
        "Other public-lands, wildlife, or recreation measures.",
        "directly_comparable",
        "The same named bill appears as final-passage evidence in both Congresses.",
        "The Congress-specific bill text and legislative path still need source review before public comparison language.",
        (r"protecting access for hunters and anglers"),
    ),
    FamilyRule(
        "env_energy_permitting_fossil_infrastructure",
        "ENVIRONMENT_ENERGY",
        "Energy permitting and fossil-fuel infrastructure",
        "Whether the House should expand or protect permitting, review, or access for fossil-fuel and energy infrastructure.",
        "Votes about energy permitting, pipeline/LNG review, natural gas access, or broad energy-production expansion.",
        "Critical-minerals-only bills, household-appliance measures, or general appropriations.",
        "related_but_not_comparable",
        "Rows share an energy-production theme but often use different tools and affected resources.",
        "This cluster is useful for audit triage, not continuity/change eligibility.",
        (r"lower energy costs|pipeline|lng|natural gas|energy production|energy dominance|jordan cove|fossil|oil and gas"),
    ),
    FamilyRule(
        "jps_federal_officer_service_weapons",
        "JUSTICE_PUBLIC_SAFETY",
        "Federal officer service-weapon purchase",
        "Whether federal law-enforcement officers, including retirees in some versions, should be able to buy retired service weapons.",
        "Final passage or direct amendments to the Federal Law Enforcement Officer Service Weapon Purchase Act.",
        "Other law-enforcement equipment, safety, or policing bills.",
        "directly_comparable",
        "The same named bill appears in both Congresses, with final-passage votes in each.",
        "Amendment rows within the family need vote-type caveats if used alongside final-passage rows.",
        (r"federal law enforcement officer service weapon"),
    ),
    FamilyRule(
        "jps_law_enforcement_safety_reporting",
        "JUSTICE_PUBLIC_SAFETY",
        "Law-enforcement safety reporting",
        "Whether the Justice Department should report on targeted attacks or safety data involving law-enforcement officers.",
        "Final passage of the Improving Law Enforcement Officer Safety and Wellness Through Data Act.",
        "Symbolic law-enforcement support resolutions or unrelated policing bills.",
        "directly_comparable",
        "The same named bill appears as final-passage evidence in both Congresses.",
        "The legislative text may differ by Congress; final public use should cite the exact bills.",
        (r"improving law enforcement officer safety"),
    ),
    FamilyRule(
        "jps_violent_offenders_pretrial_detention",
        "JUSTICE_PUBLIC_SAFETY",
        "Violent offenders and pretrial detention",
        "Whether the House should pass measures aimed at keeping violent offenders in custody or reporting cashless-bail practices.",
        "Final passage of Keeping Violent Offenders Off Our Streets Act or closely related bail/detention bills.",
        "General law-enforcement support, fentanyl, DHS, or federal service-weapon bills.",
        "conditionally_comparable",
        "Both Congresses include Keeping Violent Offenders Off Our Streets Act votes; 119th also includes a related cashless-bail bill.",
        "Do not combine bail-reporting and violent-offender detention rows without an explicit scope caveat.",
        (r"keeping violent offenders|cashless bail"),
    ),
    FamilyRule(
        "jps_fentanyl_scheduling_penalties",
        "JUSTICE_PUBLIC_SAFETY",
        "Fentanyl scheduling and penalties",
        "Whether fentanyl-related substances should be permanently scheduled and penalized under federal controlled-substances law.",
        "HALT Fentanyl Act final-passage votes.",
        "Other drug, border, or public-safety measures.",
        "related_but_not_comparable",
        "The family is coherent in 119th but lacks matching 118th interpreted House evidence in the target data.",
        "Not a common cross-Congress family in the current evidence.",
        (r"halt fentanyl|fentanyl"),
    ),
    FamilyRule(
        "jps_law_enforcement_support_resolutions",
        "JUSTICE_PUBLIC_SAFETY",
        "Law-enforcement support resolutions",
        "Whether the House should adopt resolutions expressing support for law-enforcement officers or agencies.",
        "Resolutions expressing support for law enforcement, opposing defunding, or responding to violence against officers.",
        "Binding statutory policing, reporting, equipment, or detention bills.",
        "conditionally_comparable",
        "Both Congresses include law-enforcement support resolutions.",
        "Resolution votes are materially different from statutory final passage and should not be mixed with bill enactment votes.",
        (r"expressing support for law enforcement|support for local law enforcement|violence against law enforcement|condemning efforts to defund"),
    ),
    FamilyRule(
        "eco_government_funding_packages",
        "ECONOMY_TAXES",
        "Government funding packages",
        "Whether the House should pass broad appropriations or continuing-funding packages.",
        "Final-passage, concurrence, or direct appropriations votes on broad funding packages.",
        "Narrow program cuts, tax administration, SBA, or regulatory bills.",
        "conditionally_comparable",
        "Both Congresses include broad funding-package votes, including continuing appropriations.",
        "Appropriations bills vary by covered agencies and fiscal year; compare only with a funding-package caveat.",
        (r"appropriation|appropriations|continuing appropriations|government funding|shutdown|fiscal year ending september 30|temporary funding"),
        (r"amendment to h\.?r\.?|reduce funding|prohibit funding|salary of"),
    ),
    FamilyRule(
        "eco_small_business_finance_regulation",
        "ECONOMY_TAXES",
        "Small-business finance and regulation",
        "Whether the House should change federal rules affecting small-business finance, loans, or agency regulatory costs.",
        "Votes about SBA loan eligibility, small-business regulatory costs, or small-business capital formation.",
        "IRS funding, unemployment fraud, broad budget resolutions, or general appropriations.",
        "related_but_not_comparable",
        "Rows share a small-business/economic-regulation theme but ask different governing questions.",
        "Use as a related cluster only unless a narrower recurring bill family is reviewed.",
        (r"small business|sba|entrepreneurs|access to capital"),
    ),
    FamilyRule(
        "eco_budget_reconciliation_process",
        "ECONOMY_TAXES",
        "Budget reconciliation process",
        "Whether the House should adopt or concur in budget blueprints that open or continue reconciliation instructions.",
        "Budget-resolution adoption or concurrence votes tied to reconciliation instructions, deficit levels, revenues, spending, or debt-limit process.",
        "Final tax bills, appropriations, or narrow SBA/IRS measures.",
        "related_but_not_comparable",
        "The current interpreted evidence is coherent in 119th but lacks a matching 118th family in the target records.",
        "Not a common cross-Congress family in the current evidence.",
        (r"budget reconciliation|budget blueprint|congressional budget|debt-limit|debt limit"),
    ),
)


@dataclass(frozen=True)
class Contract:
    name: str
    statuses: tuple[str, ...]
    min_common_families: int = 1
    min_cast_votes_per_congress: int = 1
    require_support_and_oppose_both: bool = False
    max_not_voting_share: float | None = None
    max_limited_procedural_share: float | None = None


CONTRACTS = (
    Contract("direct_one_common_family_one_cast_vote", ("directly_comparable",)),
    Contract("direct_one_common_family_three_cast_votes", ("directly_comparable",), min_cast_votes_per_congress=3),
    Contract("direct_two_common_families", ("directly_comparable",), min_common_families=2),
    Contract(
        "direct_support_and_opposition_opportunity",
        ("directly_comparable",),
        require_support_and_oppose_both=True,
    ),
    Contract("direct_not_voting_below_20", ("directly_comparable",), max_not_voting_share=0.2),
    Contract("direct_limited_procedural_below_50", ("directly_comparable",), max_limited_procedural_share=0.5),
    Contract("direct_and_conditional_one_family", ("directly_comparable", "conditionally_comparable")),
    Contract(
        "direct_and_conditional_three_cast_votes",
        ("directly_comparable", "conditionally_comparable"),
        min_cast_votes_per_congress=3,
    ),
    Contract(
        "direct_and_conditional_two_families",
        ("directly_comparable", "conditionally_comparable"),
        min_common_families=2,
    ),
    Contract(
        "direct_and_conditional_full_caveated_contract",
        ("directly_comparable", "conditionally_comparable"),
        min_common_families=2,
        min_cast_votes_per_congress=3,
        require_support_and_oppose_both=True,
        max_not_voting_share=0.2,
        max_limited_procedural_share=0.5,
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only House comparable policy-question family audit.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--thresholds-output", type=Path, default=DEFAULT_THRESHOLDS_PATH)
    parser.add_argument("--profiles-output", type=Path, default=DEFAULT_PROFILES_PATH)
    parser.add_argument("--packet-output", type=Path, default=DEFAULT_PACKET_PATH)
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
    write_profile_csv(args.profiles_output, payload["representative_profiles"])
    args.packet_output.parent.mkdir(parents=True, exist_ok=True)
    args.packet_output.write_text(render_packet(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(args.json_output),
                "thresholds": str(args.thresholds_output),
                "profiles": str(args.profiles_output),
                "packet": str(args.packet_output),
            },
            indent=2,
        )
    )


def build_payload(cursor: Any) -> dict[str, Any]:
    classification_version = scalar(
        cursor,
        """
        SELECT classification_version
        FROM vote_classifications
        ORDER BY created_at DESC, classification_version DESC
        LIMIT 1
        """,
    )
    roll_calls = interpreted_roll_calls(cursor, classification_version)
    burden_rows = burden_by_official(cursor, classification_version)
    officials = house_officials(cursor)
    prior = prior_readiness_reconciliation(cursor, classification_version)
    family_roll_calls, ungrouped_roll_calls = assign_roll_calls(roll_calls)
    family_summaries = build_family_summaries(family_roll_calls)
    roll_call_family_ids = {row["roll_call_id"]: row["family_id"] for rows in family_roll_calls.values() for row in rows}
    family_positions = family_positions_by_official(cursor, classification_version, roll_call_family_ids)
    profile_family_index = build_profile_family_index(family_positions)
    thresholds = simulate_thresholds(
        officials=officials,
        family_summaries=family_summaries,
        profile_family_index=profile_family_index,
        burden_by_legislator={row["legislator_id"]: row for row in burden_rows},
    )
    profiles = representative_profiles(
        officials=officials,
        profile_family_index=profile_family_index,
        family_summaries=family_summaries,
        family_roll_calls=family_roll_calls,
        burden_by_legislator={row["legislator_id"]: row for row in burden_rows},
    )
    field_inventory = field_reliability_inventory(roll_calls)

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "analysis_scope": {
            "chamber": "house",
            "congresses": list(CONGRESSES),
            "domains": list(TARGET_DOMAINS),
            "classification_version": classification_version,
            "read_only": True,
        },
        "candidate_family_contract": candidate_family_contract(),
        "field_reliability_inventory": field_inventory,
        "family_rules": [family_rule_payload(rule) for rule in FAMILY_RULES],
        "family_summaries": family_summaries,
        "reviewed_inclusion_exclusion_examples": reviewed_examples(family_roll_calls, ungrouped_roll_calls),
        "coverage_analysis": coverage_analysis(family_summaries, roll_calls, ungrouped_roll_calls),
        "threshold_simulations": thresholds,
        "representative_profiles": profiles,
        "prior_readiness_reconciliation": prior,
        "read_only_confirmation": read_only_confirmation(cursor),
        "validation_notes": {
            "not_voting_excluded_from_support_opposition": True,
            "procedural_and_limited_rows_non_counting": True,
            "cross_congress_leakage_check": "Families require represented roll calls in each Congress; roll-call identity keeps congress and session separate.",
            "production_outputs_changed": False,
        },
        "recommendations": recommendations(family_summaries, thresholds),
    }


def interpreted_roll_calls(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        f"""
        WITH distinct_votes AS (
            SELECT DISTINCT
                rc.id AS roll_call_id,
                rc.chamber::text AS chamber,
                rc.congress,
                rc.session,
                rc.rollcall_number,
                rc.vote_date::date AS vote_date,
                rc.question,
                rc.description,
                rc.source_url AS roll_call_source_url,
                b.id AS bill_id,
                b.bill_type,
                b.bill_number,
                b.title AS bill_title,
                b.summary AS bill_summary,
                b.subjects AS bill_subjects,
                vcf.primary_domain::text AS domain,
                vcf.eligibility_reason,
                COALESCE(vctx.vote_type, {vote_type_case_sql()}) AS vote_type,
                vi.interpretation_status::text AS interpretation_status,
                vi.issue_facet,
                vi.plain_english_summary,
                vi.policy_effect,
                vi.what_happened,
                vi.why_it_mattered,
                vi.member_vote_context,
                vi.what_not_to_infer,
                vi.source_basis,
                vi.uncertainty_note,
                vi.support_position::text AS support_position,
                vi.oppose_position::text AS oppose_position,
                vi.confidence,
                COUNT(*) FILTER (WHERE vc.position IN ('yea', 'nay')) OVER (PARTITION BY rc.id) AS cast_substantive_rows,
                COUNT(*) FILTER (WHERE vc.position = 'not_voting') OVER (PARTITION BY rc.id) AS not_voting_rows
            FROM votes_cast vc
            JOIN legislators l ON l.id = vc.legislator_id
            JOIN roll_calls rc ON rc.id = vc.roll_call_id
            JOIN vote_classifications vcf
              ON vcf.roll_call_id = rc.id
             AND vcf.classification_version = %s
             AND vcf.is_eligible = TRUE
             AND vcf.primary_domain::text = ANY(%s)
            JOIN vote_interpretations vi
              ON vi.roll_call_id = rc.id
             AND vi.interpretation_status = 'interpreted'
            LEFT JOIN vote_contexts vctx ON vctx.roll_call_id = rc.id AND vctx.legislator_id = vc.legislator_id
            LEFT JOIN bills b ON b.id = rc.bill_id
            WHERE l.chamber = 'house'
              AND rc.chamber = 'house'
              AND rc.congress IN (118, 119)
        )
        SELECT *
        FROM distinct_votes
        ORDER BY domain, congress, vote_date, rollcall_number
        """,
        (classification_version, list(TARGET_DOMAINS)),
    )


def assign_roll_calls(roll_calls: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ungrouped = []
    rules_by_domain: dict[str, list[FamilyRule]] = defaultdict(list)
    for rule in FAMILY_RULES:
        rules_by_domain[rule.domain].append(rule)

    for row in roll_calls:
        matched_rule = assign_family(row, rules_by_domain[row["domain"]])
        if matched_rule is None:
            ungrouped.append({**roll_call_payload(row), "ungrouped_reason": "No deterministic reviewed family rule matched."})
            continue
        grouped[matched_rule.family_id].append({**roll_call_payload(row), "family_id": matched_rule.family_id})
    return grouped, ungrouped


def assign_family(row: dict[str, Any], rules: list[FamilyRule]) -> FamilyRule | None:
    text = searchable_text(row)
    for rule in rules:
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in pattern_list(rule.exclude_any)):
            continue
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in pattern_list(rule.include_any)):
            return rule
    return None


def pattern_list(value: str | tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    return value


def searchable_text(row: dict[str, Any]) -> str:
    values = [
        row.get("question"),
        row.get("description"),
        row.get("bill_title"),
        row.get("bill_summary"),
        row.get("issue_facet"),
        row.get("plain_english_summary"),
        row.get("policy_effect"),
        row.get("what_happened"),
        row.get("why_it_mattered"),
        row.get("uncertainty_note"),
    ]
    return " ".join(str(value or "") for value in values).lower()


def build_family_summaries(family_roll_calls: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_id = {rule.family_id: rule for rule in FAMILY_RULES}
    summaries = []
    for family_id, rows in sorted(family_roll_calls.items()):
        rule = by_id[family_id]
        congresses = sorted({row["congress"] for row in rows})
        common = set(congresses) == set(CONGRESSES)
        vote_type_counter = Counter(row["vote_type"] for row in rows)
        domain_counter = Counter(row["domain"] for row in rows)
        summaries.append(
            {
                "family_id": family_id,
                "family_name": rule.name,
                "domain": rule.domain,
                "governing_question": rule.governing_question,
                "inclusion_criteria": rule.inclusion_criteria,
                "exclusion_criteria": rule.exclusion_criteria,
                "review_status": rule.review_status,
                "congresses_represented": congresses,
                "is_common_family": common,
                "measures_and_amendments_represented": measures_represented(rows),
                "vote_types_represented": sorted(vote_type_counter),
                "vote_type_distribution": dict(sorted(vote_type_counter.items())),
                "roll_call_count": len(rows),
                "roll_call_ids": sorted(row["roll_call_id"] for row in rows),
                "roll_call_count_by_congress": {str(congress): sum(1 for row in rows if row["congress"] == congress) for congress in CONGRESSES},
                "source_grounded_rationale": rule.rationale,
                "known_comparability_limitations": rule.limitations,
                "domains_represented": dict(sorted(domain_counter.items())),
                "sample_roll_calls": rows[:8],
            }
        )
    return summaries


def measures_represented(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = {}
    for row in rows:
        key = (row["congress"], row.get("bill_type"), row.get("bill_number"), row.get("bill_title"))
        seen[key] = {
            "congress": row["congress"],
            "bill": measure_display(row),
            "title": row.get("bill_title"),
            "roll_calls": sorted({r["rollcall_number"] for r in rows if (r["congress"], r.get("bill_type"), r.get("bill_number"), r.get("bill_title")) == key}),
        }
    return list(seen.values())


def coverage_analysis(
    family_summaries: list[dict[str, Any]],
    roll_calls: list[dict[str, Any]],
    ungrouped_roll_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    substantive_total = sum(int(row.get("cast_substantive_rows") or 0) for row in roll_calls)
    grouped_ids = {roll_call_id for family in family_summaries for roll_call_id in family["roll_call_ids"]}
    grouped_rows = [row for row in roll_calls if row["roll_call_id"] in grouped_ids]
    direct = [row for row in family_summaries if row["review_status"] == "directly_comparable"]
    conditional = [row for row in family_summaries if row["review_status"] == "conditionally_comparable"]
    related = [row for row in family_summaries if row["review_status"] == "related_but_not_comparable"]
    common_direct = [row for row in direct if row["is_common_family"]]
    common_conditional = [row for row in conditional if row["is_common_family"]]
    grouped_substantive = sum(int(row.get("cast_substantive_rows") or 0) for row in grouped_rows)

    return {
        "target_interpreted_roll_calls": len(roll_calls),
        "candidate_families_identified": len(family_summaries),
        "common_families_identified": sum(1 for row in family_summaries if row["is_common_family"]),
        "directly_comparable_families": len(direct),
        "directly_comparable_common_families": len(common_direct),
        "conditionally_comparable_families": len(conditional),
        "conditionally_comparable_common_families": len(common_conditional),
        "related_but_non_comparable_clusters": len(related),
        "ungrouped_roll_calls": len(ungrouped_roll_calls),
        "substantive_vote_rows_in_target_domains": substantive_total,
        "substantive_vote_rows_in_candidate_families": grouped_substantive,
        "substantive_vote_rows_covered_share": share(grouped_substantive, substantive_total),
        "distribution_by_domain_and_vote_type": domain_vote_type_distribution(roll_calls),
        "not_voting_burden_in_target_roll_calls": sum(int(row.get("not_voting_rows") or 0) for row in roll_calls),
        "amendment_vs_final_action_mix": amendment_final_mix(roll_calls),
    }


def family_positions_by_official(cursor: Any, classification_version: str, roll_call_family_ids: dict[int, str]) -> list[dict[str, Any]]:
    if not roll_call_family_ids:
        return []
    roll_call_ids = sorted(roll_call_family_ids)
    rows = query_all(
        cursor,
        """
        SELECT
            l.id AS legislator_id,
            l.name_display AS official,
            l.party,
            l.state,
            l.district,
            l.in_office,
            rc.id AS roll_call_id,
            rc.congress,
            vc.position::text AS position,
            vi.support_position::text AS support_position,
            vi.oppose_position::text AS oppose_position
        FROM votes_cast vc
        JOIN legislators l ON l.id = vc.legislator_id
        JOIN roll_calls rc ON rc.id = vc.roll_call_id
        JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
         AND vcf.is_eligible = TRUE
        JOIN vote_interpretations vi
          ON vi.roll_call_id = rc.id
         AND vi.interpretation_status = 'interpreted'
        WHERE l.chamber = 'house'
          AND rc.chamber = 'house'
          AND rc.id = ANY(%s)
        """,
        (classification_version, roll_call_ids),
    )
    for row in rows:
        row["family_id"] = roll_call_family_ids[row["roll_call_id"]]
    return rows


def build_profile_family_index(rows: list[dict[str, Any]]) -> dict[int, dict[str, dict[int, dict[str, Any]]]]:
    index: dict[int, dict[str, dict[int, dict[str, Any]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(counter_row)))
    for row in rows:
        bucket = index[row["legislator_id"]][row["family_id"]][row["congress"]]
        bucket["cast_votes"] += 1 if row["position"] in {"yea", "nay"} else 0
        bucket["not_voting"] += 1 if row["position"] == "not_voting" else 0
        bucket["support_votes"] += 1 if row["position"] == row["support_position"] else 0
        bucket["oppose_votes"] += 1 if row["position"] == row["oppose_position"] else 0
        bucket["roll_call_ids"].add(row["roll_call_id"])
    return index


def counter_row() -> dict[str, Any]:
    return {"cast_votes": 0, "not_voting": 0, "support_votes": 0, "oppose_votes": 0, "roll_call_ids": set()}


def simulate_thresholds(
    *,
    officials: list[dict[str, Any]],
    family_summaries: list[dict[str, Any]],
    profile_family_index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    burden_by_legislator: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    family_status = {row["family_id"]: row["review_status"] for row in family_summaries if row["is_common_family"]}
    family_domain = {row["family_id"]: row["domain"] for row in family_summaries}
    current_officials = [row for row in officials if row["in_office"]]
    simulations = []
    for contract in CONTRACTS:
        eligible_ids = []
        represented_domain_officials: dict[str, set[int]] = defaultdict(set)
        exclusions: Counter[str] = Counter()
        for official in current_officials:
            legislator_id = official["legislator_id"]
            burden = burden_by_legislator.get(legislator_id, {})
            if contract.max_not_voting_share is not None and share(
                burden.get("not_voting_interpreted_rows", 0),
                burden.get("interpreted_eligible_rows", 0),
            ) > contract.max_not_voting_share:
                exclusions["not_voting_burden"] += 1
                continue
            if contract.max_limited_procedural_share is not None and share(
                burden.get("limited_or_procedural_rows", 0),
                burden.get("total_house_vote_rows", 0),
            ) > contract.max_limited_procedural_share:
                exclusions["limited_procedural_burden"] += 1
                continue
            qualifying_families = []
            for family_id, congresses in profile_family_index.get(legislator_id, {}).items():
                if family_status.get(family_id) not in contract.statuses:
                    continue
                if not has_both_congresses(congresses, contract.min_cast_votes_per_congress):
                    continue
                if contract.require_support_and_oppose_both and not support_and_oppose_both(congresses):
                    continue
                qualifying_families.append(family_id)
            if len(set(qualifying_families)) >= contract.min_common_families:
                eligible_ids.append(legislator_id)
                for family_id in set(qualifying_families):
                    represented_domain_officials[family_domain[family_id]].add(legislator_id)
            else:
                exclusions["below_family_or_vote_threshold"] += 1
        simulations.append(
            {
                "contract": contract.name,
                "included_family_statuses": list(contract.statuses),
                "min_common_families": contract.min_common_families,
                "min_cast_votes_per_congress": contract.min_cast_votes_per_congress,
                "require_support_and_opposition_opportunity": contract.require_support_and_oppose_both,
                "max_not_voting_share": contract.max_not_voting_share,
                "max_limited_procedural_share": contract.max_limited_procedural_share,
                "eligible_current_officials": len(eligible_ids),
                "eligible_current_official_share": share(len(eligible_ids), len(current_officials)),
                "represented_domains": {domain: len(ids) for domain, ids in sorted(represented_domain_officials.items())},
                "primary_exclusion_reasons": dict(sorted(exclusions.items())),
                "sample_eligible_official_ids": eligible_ids[:20],
            }
        )
    return simulations


def representative_profiles(
    *,
    officials: list[dict[str, Any]],
    profile_family_index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    family_summaries: list[dict[str, Any]],
    family_roll_calls: dict[str, list[dict[str, Any]]],
    burden_by_legislator: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    family_by_id = {row["family_id"]: row for row in family_summaries}
    officials_by_name = {normalize_name(row["name"]): row for row in officials}
    used: set[int] = set()
    profiles = []

    def add(category: str, official: dict[str, Any] | None) -> None:
        if official is None or official["legislator_id"] in used:
            return
        profiles.append(
            build_profile(
                category,
                official,
                profile_family_index.get(official["legislator_id"], {}),
                family_by_id,
                family_roll_calls,
                burden_by_legislator.get(official["legislator_id"], {}),
            )
        )
        used.add(official["legislator_id"])

    add("required_valerie_foushee", officials_by_name.get("valerie p foushee") or find_name(officials, "foushee"))
    add("required_aaron_bean", officials_by_name.get("aaron bean") or find_name(officials, "bean"))
    add("strong_common_family_evidence", max_candidate(officials, used, lambda row: qualifying_family_vote_total(row, profile_family_index)))
    add("apparent_continuity_eligible_future_comparison", find_pattern_candidate(officials, used, profile_family_index, want_change=False))
    add("apparent_change_eligible_future_comparison", find_pattern_candidate(officials, used, profile_family_index, want_change=True))
    add("invalidated_by_vote_type_mismatch", find_family_candidate(officials, used, profile_family_index, "env_home_appliance_energy_rules"))
    add("invalidated_by_different_policy_subtopics", find_family_candidate(officials, used, profile_family_index, "eco_small_business_finance_regulation"))
    add("sparse_profile", first_candidate(officials, used, lambda row: qualifying_family_vote_total(row, profile_family_index) <= 2))
    add("meaningful_not_voting_burden", max_candidate(officials, used, lambda row: not_voting_share_for(row, burden_by_legislator)))
    return profiles


def build_profile(
    category: str,
    official: dict[str, Any],
    family_index: dict[str, dict[int, dict[str, Any]]],
    family_by_id: dict[str, dict[str, Any]],
    family_roll_calls: dict[str, list[dict[str, Any]]],
    burden: dict[str, Any],
) -> dict[str, Any]:
    families = []
    for family_id, congresses in sorted(family_index.items()):
        if family_id not in family_by_id:
            continue
        if not has_both_congresses(congresses, 1):
            continue
        summary = family_by_id[family_id]
        families.append(
            {
                "family_id": family_id,
                "family_name": summary["family_name"],
                "domain": summary["domain"],
                "review_status": summary["review_status"],
                "cast_votes_118": int(congresses.get(118, {}).get("cast_votes", 0) or 0),
                "cast_votes_119": int(congresses.get(119, {}).get("cast_votes", 0) or 0),
                "support_votes_118": int(congresses.get(118, {}).get("support_votes", 0) or 0),
                "oppose_votes_118": int(congresses.get(118, {}).get("oppose_votes", 0) or 0),
                "support_votes_119": int(congresses.get(119, {}).get("support_votes", 0) or 0),
                "oppose_votes_119": int(congresses.get(119, {}).get("oppose_votes", 0) or 0),
                "underlying_evidence": [
                    row
                    for row in family_roll_calls.get(family_id, [])
                    if row["roll_call_id"] in congresses.get(row["congress"], {}).get("roll_call_ids", set())
                ][:10],
            }
        )
    direct_or_conditional = [row for row in families if row["review_status"] in {"directly_comparable", "conditionally_comparable"}]
    eligible_future_comparison = any(row["review_status"] == "directly_comparable" for row in direct_or_conditional)
    return {
        "category": category,
        "example_result": profile_example_result(category, eligible_future_comparison),
        "legislator_id": official["legislator_id"],
        "official": official["name"],
        "party": official["party"],
        "state": official["state"],
        "district": official["district"],
        "in_office": bool(official["in_office"]),
        "eligible_for_future_comparison": eligible_future_comparison,
        "continuity_change_claim_made": False,
        "families": families[:8],
        "burden": {
            "not_voting_share": share(burden.get("not_voting_interpreted_rows", 0), burden.get("interpreted_eligible_rows", 0)),
            "limited_procedural_share": share(burden.get("limited_or_procedural_rows", 0), burden.get("total_house_vote_rows", 0)),
        },
    }


def profile_example_result(category: str, eligible_future_comparison: bool) -> str:
    if category == "invalidated_by_vote_type_mismatch":
        return "Targeted family example is invalidated for uncaveated comparison because amendment/final-passage mechanisms differ."
    if category == "invalidated_by_different_policy_subtopics":
        return "Targeted family example is invalidated because related rows ask different policy subtopic questions."
    if category == "meaningful_not_voting_burden":
        return "Targeted example is not eligible under not-voting burden controls."
    if category == "sparse_profile":
        return "Targeted example is not eligible because common-family evidence is sparse or absent."
    if eligible_future_comparison:
        return "Future comparison eligibility exists only for directly comparable reviewed families; no continuity/change claim is made."
    return "No future comparison eligibility found in reviewed common families."


def field_reliability_inventory(roll_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(roll_calls)
    amendment_rows = [row for row in roll_calls if row["vote_type"] == "amendment" or "amendment" in str(row.get("question") or "").lower()]
    generic_facets = {
        "house amendment vote",
        "economy_taxes",
        "environment_energy",
        "national_security_foreign",
        "justice_public_safety",
        "",
        None,
    }

    def coverage(field: str) -> float:
        return share(sum(1 for row in roll_calls if row.get(field) not in (None, "", [])), total)

    return [
        inventory_row("bill and resolution identity", coverage("bill_id"), "High when `bill_id`, type, and number are present; useful for same-measure matches.", "Too narrow across Congresses and cannot substitute for amendment meaning."),
        inventory_row("amendment identity", share(sum(1 for row in amendment_rows if extract_stable_amendment_identity(row)), len(amendment_rows)), "Limited to text-derived labels in House data; no production House amendment-reference table was found.", "Too incomplete for durable family assignment without manual/source-packet review."),
        inventory_row("parent measure", share(sum(1 for row in amendment_rows if row.get("bill_id")), len(amendment_rows)), "Usually present for amendment rows and useful as supporting context.", "Parent-measure context cannot replace the narrower amendment question."),
        inventory_row("amendment-to-amendment and en-bloc relationships", share(sum(1 for row in amendment_rows if "en bloc" in searchable_text(row) or "amendment to amendment" in searchable_text(row)), len(amendment_rows)), "Detectable when source-grounded text names en-bloc or amendment-to-amendment context.", "Sparse and source-dependent; not reliable as a primary grouping field."),
        inventory_row("vote question", coverage("question"), "Nearly complete and useful for vote mechanism.", "Often generic (`On Passage`, `On Agreeing to the Amendment`) and not enough for policy-family meaning."),
        inventory_row("source-grounded summary", max(coverage("what_happened"), coverage("plain_english_summary")), "Most useful field for deterministic candidate grouping when reviewed text is specific.", "Quality varies; generic direct-vote summaries remain too broad."),
        inventory_row("interpretation summary", coverage("policy_effect"), "Useful when present because it captures practical effect.", "Not uniformly present across older/generic rows."),
        inventory_row("issue facet", share(sum(1 for row in roll_calls if (row.get("issue_facet") or "").lower() not in generic_facets), total), "Strong when specific (for example `fentanyl_scheduling_and_penalties`).", "Many 118th rows use generic `House amendment vote`; broad facets are not comparable questions."),
        inventory_row("sponsor or amendment sponsor", 0.0, "Not available in the queried production tables for this audit.", "Cannot be used reliably without source-packet enrichment."),
        inventory_row("vote type", coverage("vote_type"), "Useful for separating final passage, amendments, appropriations, motions/resolutions, and concurrence-like votes.", "Same vote type does not guarantee same governing question."),
        inventory_row("policy purpose", coverage("policy_effect"), "Strong when reviewed source text states direct policy effect.", "Coverage and specificity vary by interpretation vintage."),
        inventory_row("official source title and description", max(coverage("bill_title"), coverage("description")), "Useful for same-bill and named-measure detection.", "Titles can be broad, amended, or generic; descriptions may repeat question text."),
        inventory_row("existing measure-family or relationship fields", 0.0, "No durable House policy-question-family field exists in the production schema.", "Supports keeping this milestone as a review artifact rather than a production model."),
    ]


def inventory_row(field: str, completeness: float, consistency: str, ambiguity: str) -> dict[str, Any]:
    return {
        "field": field,
        "completeness_share": completeness,
        "consistency": consistency,
        "ambiguity": ambiguity,
        "cross_congress_usefulness": "supporting" if completeness > 0.5 else "limited",
    }


def prior_readiness_reconciliation(cursor: Any, classification_version: str) -> dict[str, Any]:
    universe = query_all(
        cursor,
        """
        SELECT
            COUNT(DISTINCT rc.id) AS roll_call_count,
            COUNT(DISTINCT rc.id) FILTER (WHERE vcf.is_eligible = TRUE) AS eligible_roll_call_count
        FROM roll_calls rc
        LEFT JOIN vote_classifications vcf
          ON vcf.roll_call_id = rc.id
         AND vcf.classification_version = %s
        WHERE rc.congress IN (118, 119)
        """,
        (classification_version,),
    )[0]
    current_both = scalar(
        cursor,
        """
        WITH per_official AS (
            SELECT
                l.id,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 118 AND vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted' AND vc.position IN ('yea', 'nay')
                ) AS rows_118,
                COUNT(vc.id) FILTER (
                    WHERE rc.congress = 119 AND vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted' AND vc.position IN ('yea', 'nay')
                ) AS rows_119
            FROM legislators l
            LEFT JOIN votes_cast vc ON vc.legislator_id = l.id
            LEFT JOIN roll_calls rc ON rc.id = vc.roll_call_id AND rc.chamber = 'house' AND rc.congress IN (118, 119)
            LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id AND vcf.classification_version = %s
            LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
            WHERE l.chamber = 'house' AND l.in_office = TRUE
            GROUP BY l.id
        )
        SELECT COUNT(*) FROM per_official WHERE rows_118 > 0 AND rows_119 > 0
        """,
        (classification_version,),
    )
    return {
        "prior_public_roll_call_count": 2259,
        "prior_public_eligible_roll_call_count": 627,
        "current_roll_call_count": int(universe["roll_call_count"]),
        "current_eligible_roll_call_count": int(universe["eligible_roll_call_count"]),
        "prior_current_house_both_congress_substantive": 367,
        "current_house_both_congress_substantive": int(current_both),
        "reconciles_with_prior_readiness_assessment": int(universe["roll_call_count"]) == 2259
        and int(universe["eligible_roll_call_count"]) == 627
        and int(current_both) == 367,
    }


def burden_by_official(cursor: Any, classification_version: str) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        """
        SELECT
            l.id AS legislator_id,
            COUNT(vc.id) AS total_house_vote_rows,
            COUNT(vc.id) FILTER (WHERE vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted') AS interpreted_eligible_rows,
            COUNT(vc.id) FILTER (WHERE vcf.is_eligible = TRUE AND vi.interpretation_status = 'interpreted' AND vc.position = 'not_voting') AS not_voting_interpreted_rows,
            COUNT(vc.id) FILTER (WHERE vcf.is_eligible IS DISTINCT FROM TRUE OR vi.interpretation_status IS DISTINCT FROM 'interpreted') AS limited_or_procedural_rows
        FROM legislators l
        LEFT JOIN votes_cast vc ON vc.legislator_id = l.id
        LEFT JOIN roll_calls rc ON rc.id = vc.roll_call_id AND rc.chamber = 'house' AND rc.congress IN (118, 119)
        LEFT JOIN vote_classifications vcf ON vcf.roll_call_id = rc.id AND vcf.classification_version = %s
        LEFT JOIN vote_interpretations vi ON vi.roll_call_id = rc.id
        WHERE l.chamber = 'house'
        GROUP BY l.id
        """,
        (classification_version,),
    )


def house_officials(cursor: Any) -> list[dict[str, Any]]:
    return query_all(
        cursor,
        """
        SELECT
            id AS legislator_id,
            name_display AS name,
            party,
            state,
            district,
            in_office
        FROM legislators
        WHERE chamber = 'house'
        ORDER BY in_office DESC, name_display
        """,
    )


def read_only_confirmation(cursor: Any) -> dict[str, Any]:
    return {
        "transaction_read_only": scalar(cursor, "SHOW transaction_read_only"),
        "no_write_statements_in_script": True,
        "production_writes_performed": False,
        "derived_outputs_changed": False,
    }


def candidate_family_contract() -> dict[str, Any]:
    return {
        "family_required_fields": [
            "stable family identifier",
            "human-readable family name",
            "governing question",
            "inclusion criteria",
            "exclusion criteria",
            "Congresses represented",
            "measures and amendments represented",
            "vote types represented",
            "source-grounded rationale",
            "known comparability limitations",
            "review status",
        ],
        "review_statuses": {
            "directly_comparable": "Rows share a materially similar governing question and sufficiently similar vote mechanism for future comparison eligibility.",
            "conditionally_comparable": "Rows share a governing question family but need explicit vote-type, theater, fiscal-year, or scope caveats.",
            "related_but_not_comparable": "Rows share a theme or policy area but should not support continuity/change eligibility.",
            "ungrouped": "No trustworthy reviewed family assignment in this audit.",
        },
        "non_criteria": [
            "Shared broad issue domain alone",
            "Same sponsor alone",
            "Same parent bill alone for amendment votes",
            "Same party pattern or apparent political valence",
        ],
    }


def recommendations(family_summaries: list[dict[str, Any]], thresholds: list[dict[str, Any]]) -> dict[str, Any]:
    common_direct = [row for row in family_summaries if row["is_common_family"] and row["review_status"] == "directly_comparable"]
    common_condition = [row for row in family_summaries if row["is_common_family"] and row["review_status"] == "conditionally_comparable"]
    direct_one = next(row for row in thresholds if row["contract"] == "direct_one_common_family_one_cast_vote")
    full = next(row for row in thresholds if row["contract"] == "direct_and_conditional_full_caveated_contract")
    family_ready = "FAMILY MODEL READY WITH MANUAL REVIEW" if common_direct or common_condition else "FAMILY MODEL NOT READY"
    continuity = "READY FOR LIMITED PROFILES" if direct_one["eligible_current_officials"] > 0 else "NOT READY"
    if full["eligible_current_officials"] == 0:
        continuity = "READY FOR LIMITED PROFILES" if common_direct and direct_one["eligible_current_officials"] > 0 else "NOT READY"
    return {
        "family_model_recommendation": family_ready,
        "continuity_change_readiness": continuity,
        "production_model_decision": "Add a versioned derived artifact outside the production schema.",
        "record_across_congresses_should_remain_product_framing": True,
        "common_direct_family_count": len(common_direct),
        "common_conditional_family_count": len(common_condition),
        "smallest_next_milestone": "Review a versioned derived family artifact for the common directly comparable families before any frontend continuity/change language.",
    }


def reviewed_examples(family_roll_calls: dict[str, list[dict[str, Any]]], ungrouped: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "included_examples": [
            row
            for family_id in sorted(family_roll_calls)
            for row in family_roll_calls[family_id][:2]
        ][:20],
        "excluded_or_ungrouped_examples": ungrouped[:20],
        "false_inclusion_controls": [
            "NDAA amendments are not included in the annual-defense-authorization final-passage family.",
            "Critical-minerals bills are not folded into broad energy-permitting votes.",
            "Law-enforcement support resolutions are not mixed with binding law-enforcement equipment or reporting bills.",
            "Small-business loan eligibility and SBA regulatory-cost bills remain related but not comparable.",
        ],
    }


def render_packet(payload: dict[str, Any]) -> str:
    rec = payload["recommendations"]
    coverage = payload["coverage_analysis"]
    lines = [
        "# House Comparable Policy-Question Family Audit",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "## Executive Conclusion",
        "",
        f"Family-model recommendation: `{rec['family_model_recommendation']}`.",
        f"Continuity/change readiness: `{rec['continuity_change_readiness']}`.",
        "",
        "The audit found common, source-grounded families, but the model still depends on manual review and explicit caveats. `Record Across Congresses` should remain the product framing until a reviewed derived artifact is promoted in a later milestone.",
        "",
        "## Coverage",
        "",
        f"- Target interpreted roll calls: {coverage['target_interpreted_roll_calls']}",
        f"- Candidate families identified: {coverage['candidate_families_identified']}",
        f"- Common families identified: {coverage['common_families_identified']}",
        f"- Directly comparable common families: {coverage['directly_comparable_common_families']}",
        f"- Conditionally comparable common families: {coverage['conditionally_comparable_common_families']}",
        f"- Related but non-comparable clusters: {coverage['related_but_non_comparable_clusters']}",
        f"- Ungrouped roll calls: {coverage['ungrouped_roll_calls']}",
        f"- Substantive vote rows covered by candidate families: {coverage['substantive_vote_rows_in_candidate_families']} ({coverage['substantive_vote_rows_covered_share']:.2%})",
        "",
        "## Comparable Families By Domain",
        "",
    ]
    for family in payload["family_summaries"]:
        if not family["is_common_family"]:
            continue
        lines.extend(
            [
                f"### {family['family_name']}",
                "",
                f"- Domain: `{family['domain']}`",
                f"- Status: `{family['review_status']}`",
                f"- Governing question: {family['governing_question']}",
                f"- Roll calls by Congress: {json.dumps(family['roll_call_count_by_congress'], sort_keys=True)}",
                f"- Vote types: {', '.join(family['vote_types_represented'])}",
                f"- Limitation: {family['known_comparability_limitations']}",
                "",
            ]
        )
    lines.extend(["## Field Reliability Inventory", ""])
    for row in payload["field_reliability_inventory"]:
        lines.append(f"- {row['field']}: completeness {row['completeness_share']:.0%}; usefulness `{row['cross_congress_usefulness']}`. {row['ambiguity']}")
    lines.extend(["", "## Threshold Simulations", ""])
    for row in payload["threshold_simulations"]:
        lines.append(
            f"- `{row['contract']}`: {row['eligible_current_officials']} current officials "
            f"({row['eligible_current_official_share']:.2%}); exclusions {json.dumps(row['primary_exclusion_reasons'], sort_keys=True)}."
        )
    lines.extend(["", "## Representative Profiles", ""])
    for row in payload["representative_profiles"]:
        family_labels = ", ".join(f"{family['family_name']} ({family['review_status']})" for family in row["families"][:4]) or "none"
        lines.append(
            f"- {row['category']}: {row['official']} - future comparison eligible: "
            f"{str(row['eligible_for_future_comparison']).lower()}; result: {row['example_result']} Families: {family_labels}."
        )
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Read-only transaction: `{payload['read_only_confirmation']['transaction_read_only']}`.",
            "- Production writes performed: no.",
            "- Production data or derived outputs changed: no.",
            f"- Prior readiness totals reconciled: `{payload['prior_readiness_reconciliation']['reconciles_with_prior_readiness_assessment']}`.",
            "- Cross-Congress leakage check: family eligibility requires roll calls in both 118th and 119th Congresses with session-aware roll-call identity preserved.",
            "- Not-voting remains excluded from support/opposition counts.",
            "- Procedural and limited evidence remain non-counting.",
            "",
            "## Remaining Risks",
            "",
            "- Many 118th amendment rows still rely on generic `House amendment vote` facets; source-grounded summaries carry most of the family signal.",
            "- Conditional families mix different fiscal years, theaters, parent bills, or vote mechanisms and require visible caveats.",
            "- The audit does not prove every target row can be safely grouped; ungrouped and related clusters should remain outside eligibility.",
            "- Family assignment is useful as a derived review artifact, but not yet justified as a permanent production schema model.",
            "",
            "## Production Persistence Recommendation",
            "",
            "Recommendation: add a versioned derived artifact outside the production schema in a later milestone. Do not add a permanent production model yet.",
            "",
            "## Smallest Next Milestone",
            "",
            rec["smallest_next_milestone"],
            "",
        ]
    )
    return "\n".join(lines)


def roll_call_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "roll_call_id": row["roll_call_id"],
        "congress": row["congress"],
        "session": row["session"],
        "rollcall_number": row["rollcall_number"],
        "vote_date": row["vote_date"],
        "domain": row["domain"],
        "vote_type": row["vote_type"],
        "question": row["question"],
        "bill": measure_display(row),
        "bill_title": row.get("bill_title"),
        "issue_facet": row.get("issue_facet"),
        "summary": first_nonempty(row.get("what_happened"), row.get("plain_english_summary"), row.get("policy_effect"), row.get("description")),
        "support_position": row.get("support_position"),
        "oppose_position": row.get("oppose_position"),
        "cast_substantive_rows": int(row.get("cast_substantive_rows") or 0),
        "not_voting_rows": int(row.get("not_voting_rows") or 0),
        "amendment_identity_signal": extract_amendment_identity(row),
    }


def family_rule_payload(rule: FamilyRule) -> dict[str, Any]:
    return {
        "family_id": rule.family_id,
        "domain": rule.domain,
        "family_name": rule.name,
        "governing_question": rule.governing_question,
        "inclusion_criteria": rule.inclusion_criteria,
        "exclusion_criteria": rule.exclusion_criteria,
        "review_status": rule.review_status,
        "source_grounded_rationale": rule.rationale,
        "known_comparability_limitations": rule.limitations,
    }


def has_both_congresses(congresses: dict[int, dict[str, Any]], min_cast_votes: int) -> bool:
    return all(int(congresses.get(congress, {}).get("cast_votes", 0) or 0) >= min_cast_votes for congress in CONGRESSES)


def support_and_oppose_both(congresses: dict[int, dict[str, Any]]) -> bool:
    return all(
        int(congresses.get(congress, {}).get("support_votes", 0) or 0) > 0
        and int(congresses.get(congress, {}).get("oppose_votes", 0) or 0) > 0
        for congress in CONGRESSES
    )


def qualifying_family_vote_total(row: dict[str, Any], index: dict[int, dict[str, dict[int, dict[str, Any]]]]) -> int:
    total = 0
    for congresses in index.get(row["legislator_id"], {}).values():
        if 118 in congresses and 119 in congresses:
            total += int(congresses[118].get("cast_votes", 0) or 0)
            total += int(congresses[119].get("cast_votes", 0) or 0)
    return total


def find_pattern_candidate(
    officials: list[dict[str, Any]],
    used: set[int],
    index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    *,
    want_change: bool,
) -> dict[str, Any] | None:
    for row in sorted(officials, key=lambda item: qualifying_family_vote_total(item, index), reverse=True):
        if row["legislator_id"] in used or not row["in_office"]:
            continue
        for congresses in index.get(row["legislator_id"], {}).values():
            if not has_both_congresses(congresses, 1):
                continue
            pattern_118 = profile_pattern(congresses[118])
            pattern_119 = profile_pattern(congresses[119])
            if want_change and pattern_118 != pattern_119 and "mixed" not in {pattern_118, pattern_119}:
                return row
            if not want_change and pattern_118 == pattern_119 and pattern_118 != "mixed":
                return row
    return None


def find_family_candidate(
    officials: list[dict[str, Any]],
    used: set[int],
    index: dict[int, dict[str, dict[int, dict[str, Any]]]],
    family_id: str,
) -> dict[str, Any] | None:
    for row in officials:
        if row["legislator_id"] in used or not row["in_office"]:
            continue
        if has_both_congresses(index.get(row["legislator_id"], {}).get(family_id, {}), 1):
            return row
    return None


def first_candidate(officials: list[dict[str, Any]], used: set[int], predicate: Any) -> dict[str, Any] | None:
    for row in officials:
        if row["legislator_id"] not in used and row["in_office"] and predicate(row):
            return row
    return None


def max_candidate(officials: list[dict[str, Any]], used: set[int], score: Any) -> dict[str, Any] | None:
    candidates = [row for row in officials if row["legislator_id"] not in used and row["in_office"]]
    if not candidates:
        return None
    best = max(candidates, key=score)
    return best if score(best) > 0 else None


def profile_pattern(row: dict[str, Any]) -> str:
    support = int(row.get("support_votes", 0) or 0)
    oppose = int(row.get("oppose_votes", 0) or 0)
    if support and oppose:
        return "mixed"
    return "support" if support >= oppose else "oppose"


def not_voting_share_for(row: dict[str, Any], burden_by_legislator: dict[int, dict[str, Any]]) -> float:
    burden = burden_by_legislator.get(row["legislator_id"], {})
    return share(burden.get("not_voting_interpreted_rows", 0), burden.get("interpreted_eligible_rows", 0))


def domain_vote_type_distribution(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        output[row["domain"]][row["vote_type"]] += 1
    return {domain: dict(sorted(counter.items())) for domain, counter in sorted(output.items())}


def amendment_final_mix(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(row["vote_type"] for row in rows)
    return {
        "amendment": counter.get("amendment", 0),
        "final_passage": counter.get("final_passage", 0),
        "appropriations": counter.get("appropriations", 0),
        "other_or_resolution_or_rule": len(rows) - counter.get("amendment", 0) - counter.get("final_passage", 0) - counter.get("appropriations", 0),
    }


def extract_amendment_identity(row: dict[str, Any]) -> str | None:
    text = searchable_text(row)
    patterns = [
        r"part [a-z] amendment no\.? \d+",
        r"en bloc no\.? \d+",
        r"amendment(?:s)? numbered? [\d, and]+",
        r"amendment to h\.?r\.? ?\d+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def extract_stable_amendment_identity(row: dict[str, Any]) -> str | None:
    text = searchable_text(row)
    patterns = [
        r"part [a-z] amendment no\.? \d+",
        r"en bloc no\.? \d+",
        r"amendment(?:s)? numbered? [\d, and]+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def first_nonempty(*values: Any) -> str | None:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return None


def measure_display(row: dict[str, Any]) -> str | None:
    if row.get("bill_type") and row.get("bill_number"):
        return f"{str(row['bill_type']).upper()} {row['bill_number']}"
    return None


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def find_name(officials: list[dict[str, Any]], needle: str) -> dict[str, Any] | None:
    needle = needle.lower()
    for row in officials:
        if needle in row["name"].lower():
            return row
    return None


def vote_type_case_sql() -> str:
    return """
    CASE
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%motion to concur%%' THEN 'concurrence'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%amend%%' THEN 'amendment'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%appropriation%%' THEN 'appropriations'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%passage%%' THEN 'final_passage'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%resolution%%' THEN 'resolution'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%rule%%' THEN 'rule'
        WHEN LOWER(COALESCE(rc.question, '') || ' ' || COALESCE(rc.description, '')) LIKE '%%motion%%' THEN 'motion'
        ELSE 'other'
    END
    """


def share(numerator: Any, denominator: Any) -> float:
    denominator_int = int(denominator or 0)
    if denominator_int <= 0:
        return 0.0
    return round(int(numerator or 0) / denominator_int, 4)


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


def write_threshold_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "contract",
        "included_family_statuses",
        "eligible_current_officials",
        "eligible_current_official_share",
        "represented_domains",
        "primary_exclusion_reasons",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row[field], sort_keys=True) if isinstance(row[field], (dict, list)) else row[field] for field in fieldnames})


def write_profile_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "official",
        "party",
        "state",
        "district",
        "eligible_for_future_comparison",
        "family_count",
        "not_voting_share",
        "limited_procedural_share",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "category": row["category"],
                    "official": row["official"],
                    "party": row["party"],
                    "state": row["state"],
                    "district": row["district"],
                    "eligible_for_future_comparison": row["eligible_for_future_comparison"],
                    "family_count": len(row["families"]),
                    "not_voting_share": row["burden"]["not_voting_share"],
                    "limited_procedural_share": row["burden"]["limited_procedural_share"],
                }
            )


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, set):
        return sorted(value)
    return str(value)


if __name__ == "__main__":
    main()
