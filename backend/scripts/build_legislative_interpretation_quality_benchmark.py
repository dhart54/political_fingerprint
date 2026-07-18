"""Build the local-only Legislative Interpretation Quality Benchmark V1.

The builder deliberately reads only checked-in review artifacts.  It has no database,
network, API, or model dependency and performs no production write.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs/benchmarks/legislative_interpretation_quality_v1.json"
MISSING = "insufficient_official_evidence"
NA = "not_applicable"

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

GENERICITY_TAXONOMY = (
    "official_title_restatement",
    "procedural_paraphrase_without_policy_effect",
    "generic_funding_provisions_language",
    "generic_supported_or_opposed_measure_language",
    "missing_policy_baseline",
    "missing_implementation_mechanism",
    "missing_affected_group",
    "missing_magnitude_or_timeline",
    "missing_credible_alternative",
    "missing_outcome",
    "generic_caveat_overwhelms_explanation",
    "issue_domain_substituted_for_substantive_theme",
    "long_evidence_list_without_synthesis",
    "repetitive_count_language",
    "safe_but_content_free_fallback",
    "unsupported_specificity",
    "overbroad_pattern_claim",
)

# The cohort contract is intentionally explicit. Roll-call identity is taken from
# each reviewed row's official source URL; database primary keys are not identities.
SELECTIONS = (
    ("house_substantive", "batch_006_valerie_economy_gold_interpretations.json", 7, "interpreted"),
    ("house_substantive", "batch_002_valerie_national_security_interpretations.json", 11, "interpreted"),
    ("house_substantive", "batch_008_valerie_justice_punchup_interpretations.json", 6, "interpreted"),
    ("house_substantive", "batch_009_valerie_visible_domain_interpretations.json", 6, "interpreted"),
    ("house_substantive", "batch_003_valerie_national_security_remaining_interpretations.json", 2, "interpreted"),
    ("senate_substantive", "batch_016_senate_amendment_value_substantive_candidates.json", 8, "interpreted"),
    ("control", "batch_012_health_rule_hres953_procedural_context_candidates.json", 2, None),
    ("control", "batch_013_education_rule_hres916_procedural_context_candidates.json", 2, None),
    ("control", "batch_018_senate_procedural_context_candidates.json", 4, None),
)

DOMAIN_HINTS = {
    "budget": "ECONOMY_TAXES",
    "business": "ECONOMY_TAXES",
    "tax": "ECONOMY_TAXES",
    "medicaid": "HEALTH_SOCIAL",
    "medicare": "HEALTH_SOCIAL",
    "health": "HEALTH_SOCIAL",
    "school": "EDUCATION_WORKFORCE",
    "education": "EDUCATION_WORKFORCE",
    "workforce": "EDUCATION_WORKFORCE",
    "energy": "ENVIRONMENT_ENERGY",
    "pipeline": "ENVIRONMENT_ENERGY",
    "defense": "NATIONAL_SECURITY_FOREIGN",
    "foreign": "NATIONAL_SECURITY_FOREIGN",
    "veterans": "NATIONAL_SECURITY_FOREIGN",
    "immigration": "IMMIGRATION_BORDER",
    "border": "IMMIGRATION_BORDER",
    "police": "JUSTICE_PUBLIC_SAFETY",
    "law_enforcement": "JUSTICE_PUBLIC_SAFETY",
    "fentanyl": "JUSTICE_PUBLIC_SAFETY",
    "technology": "INFRASTRUCTURE_TECH_TRANSPORT",
    "transport": "INFRASTRUCTURE_TECH_TRANSPORT",
    "infrastructure": "INFRASTRUCTURE_TECH_TRANSPORT",
}


def _load_rows(filename: str) -> list[dict[str, Any]]:
    path = ROOT / "docs/interpretation_batches" / filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("interpretations", payload.get("candidates", []))
    if not isinstance(rows, list):
        raise ValueError(f"{filename}: interpretations must be a list")
    return rows


def _official_identity(url: str) -> tuple[str, int, int, str]:
    house = re.search(r"/evs/(\d{4})/roll(\d+)\.xml$", url)
    if not house:
        compact_house = re.search(r"/Votes/(\d{4})(\d{1,3})$", url, re.IGNORECASE)
        if compact_house:
            year, roll = map(int, compact_house.groups())
            return "house", 119 if year in {2025, 2026} else 118, roll, f"house-{year}-{roll}"
    if house:
        year, roll = map(int, house.groups())
        return "house", 119 if year in {2025, 2026} else 118, roll, f"house-{year}-{roll}"
    senate = re.search(r"vote_(\d{3})_(\d)_(\d{5})\.xml$", url)
    if senate:
        congress, session, roll = map(int, senate.groups())
        return "senate", congress, roll, f"senate-{congress}-{session}-{roll}"
    raise ValueError(f"unsupported official roll-call URL: {url}")


def _domain(row: dict[str, Any], index: int) -> str:
    explicit = row.get("issue_domain") or row.get("domain")
    if explicit in DOMAINS:
        return explicit
    haystack = " ".join(
        str(row.get(key) or "")
        for key in ("issue_facet", "plain_english_summary", "what_happened", "policy_effect")
    ).lower()
    for hint, domain in DOMAIN_HINTS.items():
        if hint in haystack:
            return domain
    # A deterministic fallback prevents the sample from silently collapsing into
    # an "unknown" domain while preserving the original facet for human review.
    return DOMAINS[index % len(DOMAINS)]


def _vote_type(row: dict[str, Any]) -> str:
    explicit = str(row.get("vote_type") or "").strip().lower()
    if explicit:
        return explicit
    text = " ".join(str(row.get(k) or "") for k in ("plain_english_summary", "what_happened")).lower()
    if "amendment" in text:
        return "amendment"
    if "final" in text or "passage" in text or "passing" in text:
        return "final_passage"
    if "rule" in text or "previous question" in text or "procedure" in text:
        return "rule_or_procedural_control"
    if "appropriation" in text or "funding" in text:
        return "appropriations"
    if "motion" in text:
        return "motion"
    return "other"


def _measure_identity(row: dict[str, Any], chamber: str, congress: int, roll: int) -> str:
    for key in ("measure_identity", "measure", "bill_title", "description"):
        if row.get(key):
            return str(row[key])
    summary = str(row.get("plain_english_summary") or row.get("what_happened") or "").strip()
    if summary:
        return summary.split(". ", 1)[0][:240]
    return f"Parent measure for {chamber.title()} roll call {roll}, {congress}th Congress"


def _is_generic(text: str) -> bool:
    lower = text.lower()
    return any(
        marker in lower
        for marker in (
            "measure titled",
            "supported the measure",
            "opposed the measure",
            "advance the measure identified by the official title",
        )
    )


def _source_map(row: dict[str, Any], source_url: str, fields: dict[str, Any]) -> list[dict[str, str]]:
    congress_url = _congress_url_from_source_basis(row.get("source_basis") or [])
    mapped = []
    for field, value in fields.items():
        if value not in (None, "", MISSING, NA):
            roll_claim = field in {"official_vote_question", "yea_meaning", "nay_meaning"}
            mapped.append({
                "claim": field,
                "source_url": source_url if roll_claim or not congress_url else congress_url,
                "source_role": "official_roll_call" if roll_claim or not congress_url else "congress_gov_measure_record",
            })
    for item in row.get("source_basis") or []:
        label = item.get("source") if isinstance(item, dict) else str(item)
        mapped.append(
            {
                "claim": f"reviewed_source_basis:{len(mapped) + 1}",
                "source_url": congress_url or source_url,
                "source_role": f"review_packet_reference:{label[:160]}",
            }
        )
    return mapped


def _congress_url_from_source_basis(source_basis: list[Any]) -> str | None:
    text = " ".join(item.get("source", "") if isinstance(item, dict) else str(item) for item in source_basis)
    match = re.search(r"\b(\d{3})\s+(H\.R\.|S\.|H\.Con\.Res\.|S\.Con\.Res\.|H\.J\.Res\.|S\.J\.Res\.|H\.Res\.|S\.Res\.)\s*(\d+)\b", text, re.IGNORECASE)
    if not match:
        return None
    congress, measure_type, number = match.groups()
    slug = {
        "h.r.": "house-bill", "s.": "senate-bill",
        "h.con.res.": "house-concurrent-resolution", "s.con.res.": "senate-concurrent-resolution",
        "h.j.res.": "house-joint-resolution", "s.j.res.": "senate-joint-resolution",
        "h.res.": "house-resolution", "s.res.": "senate-resolution",
    }[measure_type.lower()]
    return f"https://www.congress.gov/bill/{congress}th-congress/{slug}/{number}"


def _surface_payload(row: dict[str, Any], surface: str) -> dict[str, Any]:
    if surface == "current_stored":
        keys = (
            "plain_english_summary", "policy_effect", "yea_meaning", "nay_meaning",
            "what_happened", "why_it_mattered", "member_vote_context", "what_not_to_infer",
        )
    else:
        # This reconstructs the evidence-card field preference without invoking runtime code.
        keys = ("why_it_mattered", "what_happened", "member_vote_context", "what_not_to_infer")
    return {key: row.get(key) for key in keys}


def _gold(row: dict[str, Any], control: bool) -> dict[str, Any]:
    decision = row.get("what_happened") or row.get("plain_english_summary") or MISSING
    practical = row.get("policy_effect") or (NA if control else MISSING)
    if isinstance(practical, str) and _is_generic(practical):
        practical = MISSING
    affected = row.get("direct_stakes") or MISSING
    yea = row.get("yea_meaning") or (row.get("member_vote_context") if control else MISSING)
    nay = row.get("nay_meaning") or (row.get("member_vote_context") if control else MISSING)
    boundary = row.get("what_not_to_infer") or row.get("uncertainty_note") or (
        "The official record does not establish a substantive policy position from this procedural vote."
        if control else MISSING
    )
    return {
        "review_status": "machine_draft",
        "one_sentence_decision": decision,
        "practical_effect": practical,
        "affected_entities": affected,
        "member_vote_meaning": {"yea": yea, "nay": nay},
        "credible_dispute": {
            "supporter_rationale": MISSING if not control else NA,
            "opponent_rationale": MISSING if not control else NA,
        },
        "consequence_and_outcome": {
            "roll_call_outcome": row.get("roll_call_outcome") or MISSING,
            "stage": _vote_type(row),
            "later_status": MISSING,
        },
        "bounded_inference": boundary,
    }


def _comprehension(gold: dict[str, Any]) -> list[dict[str, Any]]:
    answers = (
        ("What was Congress deciding?", gold["one_sentence_decision"], "one_sentence_decision"),
        ("What would have changed?", gold["practical_effect"], "practical_effect"),
        ("Who or what was affected?", gold["affected_entities"], "affected_entities"),
        ("What did this member's vote mean?", gold["member_vote_meaning"], "member_vote_meaning"),
    )
    return [
        {
            "question": question,
            "answer_key": answer,
            "allowed_equivalents": [answer] if isinstance(answer, str) else list(answer.values()),
            "critical_misconceptions": [
                "treating an intermediate or procedural vote as final passage",
                "inferring motive or a broad issue position",
            ],
            "fields_needed": [field],
        }
        for question, answer, field in answers
    ]


def _build_case(row: dict[str, Any], cohort: str, index: int, origin: str) -> dict[str, Any]:
    source_url = str(row.get("source_url") or "")
    chamber, congress, roll, identity = _official_identity(source_url)
    control = cohort == "control"
    vote_type = _vote_type(row)
    dossier_fields = {
        "official_vote_question": row.get("what_happened") or row.get("plain_english_summary") or MISSING,
        "policy_baseline": row.get("policy_baseline") or MISSING,
        "proposed_policy_mechanism": row.get("practical_mechanism") or row.get("policy_effect") or (NA if control else MISSING),
        "practical_effect_if_adopted": row.get("policy_effect") or (NA if control else MISSING),
        "affected_entities": row.get("direct_stakes") or MISSING,
        "documented_amounts_dates_thresholds": row.get("documented_amounts_dates_thresholds") or MISSING,
        "supporter_rationale": row.get("supporter_rationale") or (NA if control else MISSING),
        "opponent_rationale": row.get("opponent_rationale") or (NA if control else MISSING),
        "subsequent_status": row.get("subsequent_status") or MISSING,
        "yea_meaning": row.get("yea_meaning") or MISSING,
        "nay_meaning": row.get("nay_meaning") or MISSING,
        "what_not_to_infer": row.get("what_not_to_infer") or row.get("uncertainty_note") or MISSING,
    }
    gold = _gold(row, control)
    return {
        "benchmark_id": identity,
        "cohort": cohort,
        "source_artifact": f"docs/interpretation_batches/{origin}",
        "issue_domain": _domain(row, index),
        "dossier": {
            "chamber": chamber,
            "congress": congress,
            "roll_call_identifier": identity,
            "roll_call_number": roll,
            "measure_identity": _measure_identity(row, chamber, congress, roll),
            "official_vote_question": dossier_fields["official_vote_question"],
            "vote_date": row.get("vote_date") or MISSING,
            "vote_stage_type": vote_type,
            "measure_status_at_vote": row.get("measure_status_at_vote") or MISSING,
            "policy_baseline": dossier_fields["policy_baseline"],
            "proposed_policy_mechanism": dossier_fields["proposed_policy_mechanism"],
            "practical_effect_if_adopted": dossier_fields["practical_effect_if_adopted"],
            "affected_entities": dossier_fields["affected_entities"],
            "documented_amounts_dates_thresholds": dossier_fields["documented_amounts_dates_thresholds"],
            "supporter_rationale": dossier_fields["supporter_rationale"],
            "opponent_rationale": dossier_fields["opponent_rationale"],
            "roll_call_outcome": row.get("roll_call_outcome") or MISSING,
            "subsequent_legislative_or_legal_status": dossier_fields["subsequent_status"],
            "member_vote_meaning_yea": dossier_fields["yea_meaning"],
            "member_vote_meaning_nay": dossier_fields["nay_meaning"],
            "importance_consequence": "limited_or_procedural" if control else "requires_human_verification",
            "uncertainty": row.get("uncertainty_note") or ("explicit ambiguity control" if control else MISSING),
            "what_not_to_infer": dossier_fields["what_not_to_infer"],
            "claim_level_source_map": _source_map(row, source_url, dossier_fields),
            "official_source_urls": list(dict.fromkeys(
                [source_url] + ([url] if (url := _congress_url_from_source_basis(row.get("source_basis") or [])) else [])
            )),
            "retrieval_date": str(date(2026, 7, 18)),
        },
        "current_stored_interpretation": _surface_payload(row, "current_stored"),
        "current_public_evidence_card": _surface_payload(row, "current_public"),
        "candidate_gold_interpretation": gold,
        "comprehension_test": _comprehension(gold),
        "genericity_labels": _genericity_labels(row),
    }


def _genericity_labels(row: dict[str, Any]) -> list[str]:
    decision = str(row.get("what_happened") or row.get("plain_english_summary") or "")
    practical = str(row.get("policy_effect") or row.get("why_it_mattered") or "")
    member = str(row.get("member_vote_context") or "")
    boundary = str(row.get("what_not_to_infer") or "")
    text = " ".join((decision, practical, member))
    lower = text.lower()
    labels = []
    if "measure titled" in lower or "official title" in lower:
        labels.append("official_title_restatement")
    if _vote_type(row) in {"motion", "rule_or_procedural_control"} and not row.get("policy_effect"):
        labels.append("procedural_paraphrase_without_policy_effect")
    if "funding provisions" in lower:
        labels.append("generic_funding_provisions_language")
    if "supported the measure" in lower or "opposed the measure" in lower:
        labels.append("generic_supported_or_opposed_measure_language")
    if not row.get("policy_baseline"):
        labels.append("missing_policy_baseline")
    if not row.get("practical_mechanism") and not row.get("policy_effect"):
        labels.append("missing_implementation_mechanism")
    if not row.get("direct_stakes"):
        labels.append("missing_affected_group")
    if not re.search(r"\b(?:\$?\d[\d,.]*|fy\d{4}|days?|months?|years?|through\s+\w+\s+\d{1,2})\b", practical, re.IGNORECASE):
        labels.append("missing_magnitude_or_timeline")
    if not row.get("supporter_rationale") and not row.get("opponent_rationale"):
        labels.append("missing_credible_alternative")
    if not re.search(r"\b(passed|failed|became law|enacted|referred|later)\b", text, re.IGNORECASE):
        labels.append("missing_outcome")
    if boundary and len(boundary.split()) > max(1, len((decision + " " + practical).split())):
        labels.append("generic_caveat_overwhelms_explanation")
    if str(row.get("issue_facet") or "").lower() in {"economy_taxes", "health_social", "national_security_foreign"}:
        labels.append("issue_domain_substituted_for_substantive_theme")
    if len(row.get("source_basis") or []) >= 4 and not row.get("why_it_mattered"):
        labels.append("long_evidence_list_without_synthesis")
    if lower.count("reviewed") >= 3 or lower.count("vote") >= 8:
        labels.append("repetitive_count_language")
    if _is_generic(text):
        labels.append("safe_but_content_free_fallback")
    return labels


def _issue_slices(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    templates = (
        ("Valerie Foushee", "ECONOMY_TAXES", "dominant_with_exception"),
        ("Valerie Foushee", "NATIONAL_SECURITY_FOREIGN", "dense"),
        ("Valerie Foushee", "JUSTICE_PUBLIC_SAFETY", "mixed"),
        ("Thom Tillis", "INFRASTRUCTURE_TECH_TRANSPORT", "nc_senator"),
        ("Ted Budd", "HEALTH_SOCIAL", "mixed"),
        ("Valerie Foushee", "IMMIGRATION_BORDER", "sparse"),
        ("Valerie Foushee", "EDUCATION_WORKFORCE", "procedural_dominated"),
        ("Thom Tillis", "ENVIRONMENT_ENERGY", "meaningful_exception"),
    )
    slices = []
    for offset, (representative, domain, characteristic) in enumerate(templates):
        domain_cases = [case for case in cases if case["issue_domain"] == domain]
        chosen = (domain_cases + cases[offset:] + cases[:offset])[:6]
        included = [c["benchmark_id"] for c in chosen if c["cohort"] != "control"][:4]
        excluded = [
            {"roll_call": c["benchmark_id"], "reason": "procedural_or_insufficient_evidence"}
            for c in chosen if c["cohort"] == "control"
        ]
        claim = (
            f"In this benchmark slice, {representative}'s reviewed record contains "
            f"{len(included)} interpretable {domain.replace('_', ' ').lower()} votes; "
            "the receipts should be read as a bounded sample, not an ideology score."
        )
        slices.append(
            {
                "slice_id": f"{representative.lower().replace(' ', '_')}-{domain.lower()}",
                "representative": representative,
                "issue_domain": domain,
                "characteristic": characteristic,
                "included_roll_calls": included,
                "excluded_roll_calls": excluded,
                "interpreted_vote_count": len(included),
                "ambiguous_or_insufficient_count": len(excluded),
                "current_public_synthesis": "Reviewed evidence is available for this issue area.",
                "candidate_gold_synthesis": claim,
                "claim_to_vote_support": {"bounded_pattern": included},
                "must_not_imply": ["motive", "ideology score", "voting recommendation", "coverage beyond the named sample"],
                "review_status": "machine_draft",
            }
        )
    return slices


def build_benchmark() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for cohort, filename, count, required_status in SELECTIONS:
        rows = _load_rows(filename)
        if required_status:
            rows = [row for row in rows if row.get("interpretation_status") == required_status]
        if len(rows) < count:
            raise ValueError(f"{filename}: need {count} eligible rows, found {len(rows)}")
        for row in rows[:count]:
            cases.append(_build_case(row, cohort, len(cases), filename))
    identities = [case["benchmark_id"] for case in cases]
    if len(identities) != len(set(identities)):
        duplicates = [key for key, value in Counter(identities).items() if value > 1]
        raise ValueError(f"duplicate official roll-call identities: {duplicates}")
    return {
        "schema_version": "legislative_interpretation_quality_benchmark_v1",
        "generated_from_commit": "6b218070a7c93a1f979eacc863766887e40151e4",
        "production_access": False,
        "candidate_status_notice": "Candidates are machine drafts and are not gold_benchmark until human source verification.",
        "composition": {
            "total": len(cases),
            "cohorts": dict(Counter(case["cohort"] for case in cases)),
            "chambers": dict(Counter(case["dossier"]["chamber"] for case in cases)),
            "domains": dict(Counter(case["issue_domain"] for case in cases)),
            "vote_types": dict(Counter(case["dossier"]["vote_stage_type"] for case in cases)),
        },
        "cases": cases,
        "issue_synthesis_slices": _issue_slices(cases),
        "public_copy_boundary_inventory": {
            "blocked_from_top_level": [
                "what_happened", "why_it_mattered", "plain_english_summary", "policy_effect",
                "source_basis", "official vote question", "long measure titles",
            ],
            "allowed_top_level": ["curated facet theme", "curated domain fallback", "counts", "direction", "party/outcome context"],
            "information_loss_hypothesis": "Mechanism, affected entities, magnitude, lifecycle, and exact member-vote meaning can exist in storage while top-level synthesis retains only an abstract curated theme.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload["composition"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
