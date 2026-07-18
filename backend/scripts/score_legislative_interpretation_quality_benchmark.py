"""Validate and score Legislative Interpretation Quality Benchmark V1."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from scripts.build_legislative_interpretation_quality_benchmark import GENERICITY_TAXONOMY
except ModuleNotFoundError:  # Direct script execution adds backend/scripts to sys.path.
    from build_legislative_interpretation_quality_benchmark import GENERICITY_TAXONOMY


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK = ROOT / "docs/benchmarks/legislative_interpretation_quality_v1.json"
DEFAULT_RUBRIC = ROOT / "docs/benchmarks/legislative_interpretation_quality_rubric_v1.json"
DEFAULT_JSON = ROOT / "docs/review_packets/legislative_interpretation_quality_benchmark_v1.json"
DEFAULT_MD = ROOT / "docs/review_packets/legislative_interpretation_quality_benchmark_v1.md"
MISSING = {None, "", "insufficient_official_evidence", "not_applicable"}

DIMENSIONS = (
    "factual_support_structure",
    "procedural_description_structure",
    "policy_mechanism_specificity",
    "practical_effect_clarity",
    "affected_entity_specificity",
    "member_vote_meaning",
    "credible_argument_framing",
    "outcome_and_later_status_clarity",
    "source_map_presence",
    "calibration_and_non_overclaiming",
    "plain_language_comprehension",
    "distinctiveness_from_title_or_summary",
)

FATAL_DEFINITIONS = (
    "yea_nay_reversal",
    "procedural_final_passage_confusion",
    "false_enactment_claim",
    "invented_effect",
    "unsupported_affected_group",
    "motive_attribution",
    "advocacy_as_neutral_fact",
    "insufficient_issue_pattern_evidence",
    "title_restatement_as_practical_explanation",
    "unmapped_material_claim",
)

RUBRIC = {
    "schema_version": "legislative_interpretation_quality_rubric_v1",
    "rubric_kind": "automated_structural_heuristic_diagnostic",
    "editorial_quality_status": "unverified_human_editorial_scoring_pending",
    "source_map_caveat": "Source-map presence proves only that a mapping entry exists; it does not prove that the cited source factually supports the claim.",
    "dimensions": [
        {
            "name": name,
            "range": [0, 4],
            "anchor_0": "expected structural signal is missing or a fatal heuristic is triggered",
            "anchor_2": "structurally partial, generic, incomplete, or weakly mapped",
            "anchor_4": "expected structural signals are present; factual and editorial verification remains pending",
        }
        for name in DIMENSIONS
    ],
    "maximum_score": 48,
    "fatal_defects": list(FATAL_DEFINITIONS),
    "tiers": {
        "unacceptable": "automated diagnostic: fatal defect or score below 24",
        "generic_but_structurally_adequate": "automated diagnostic only: 24-32; factual accuracy is not verified",
        "useful": "automated diagnostic only: 33-39",
        "strong": "strong under the automated diagnostic rubric only: 40-44",
        "exceptional": "exceptional under the automated diagnostic rubric only: 45-48",
    },
    "threshold_status": "benchmark hypothesis; not an approved production threshold",
    "strong_comprehension_gate": [
        "What was Congress deciding?",
        "What would have changed?",
        "What did this member's vote mean?",
    ],
    "human_review_override": "Automated scores and tiers are structural/heuristic diagnostics, not verified editorial-quality judgments. Human editorial scoring is pending.",
}


def _present(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_present(v) for v in value.values())
    if isinstance(value, list):
        return bool(value)
    return value not in MISSING


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_text(v) for v in value)
    return "" if value is None else str(value)


def _normalize(payload: dict[str, Any], surface: str) -> dict[str, Any]:
    if surface == "candidate_gold":
        return {
            "decision": payload.get("one_sentence_decision"),
            "practical": payload.get("practical_effect"),
            "affected": payload.get("affected_entities"),
            "member": payload.get("member_vote_meaning"),
            "arguments": payload.get("credible_dispute"),
            "outcome": payload.get("consequence_and_outcome"),
            "boundary": payload.get("bounded_inference"),
        }
    return {
        "decision": payload.get("what_happened") or payload.get("plain_english_summary"),
        "practical": payload.get("policy_effect") or payload.get("why_it_mattered"),
        "affected": payload.get("direct_stakes"),
        "member": {
            "yea": payload.get("yea_meaning"),
            "nay": payload.get("nay_meaning"),
            "member": payload.get("member_vote_context"),
        },
        "arguments": None,
        "outcome": payload.get("what_happened"),
        "boundary": payload.get("what_not_to_infer"),
    }


def detect_fatal_defects(
    normalized: dict[str, Any],
    *,
    vote_type: str,
    source_mapped: bool,
    expected_yea: str | None = None,
    expected_nay: str | None = None,
    issue_evidence_count: int | None = None,
) -> list[str]:
    text = _text(normalized).lower()
    asserted_effect = " ".join(
        _text(normalized.get(key)).lower() for key in ("decision", "practical", "outcome")
    )
    defects: list[str] = []
    practical = _text(normalized.get("practical")).lower()
    member = normalized.get("member") or {}
    if expected_yea and expected_nay:
        actual_yea = _text(member.get("yea")).lower()
        actual_nay = _text(member.get("nay")).lower()
        if expected_yea.lower() in actual_nay or expected_nay.lower() in actual_yea:
            defects.append("yea_nay_reversal")
    if vote_type in {"motion", "rule_or_procedural_control", "procedure"} and re.search(
        r"\b(final passage|became law|enacted the underlying)\b", asserted_effect
    ) and not re.search(r"\b(not|rather than|did not)\b.{0,30}\b(final passage|became law|enact)", asserted_effect):
        defects.append("procedural_final_passage_confusion")
    if "became law" in asserted_effect and any(marker in asserted_effect for marker in ("not enact", "house passage rather", "referred to the senate")):
        defects.append("false_enactment_claim")
    if any(marker in text for marker in ("because the member wanted", "intended to harm", "shows their motive")):
        defects.append("motive_attribution")
    if any(marker in practical for marker in ("measure titled", "official title identifies", "advance the measure identified by the official title")):
        defects.append("title_restatement_as_practical_explanation")
    if not source_mapped and any(_present(normalized.get(k)) for k in ("decision", "practical", "affected", "member")):
        defects.append("unmapped_material_claim")
    if issue_evidence_count is not None and issue_evidence_count < 3 and "pattern" in text:
        defects.append("insufficient_issue_pattern_evidence")
    return sorted(set(defects))


def score_interpretation(
    payload: dict[str, Any],
    *,
    surface: str,
    vote_type: str,
    source_mapped: bool,
    comprehension: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    value = _normalize(payload, surface)
    text = _text(value)
    lower = text.lower()
    decision, practical = value["decision"], value["practical"]
    member, arguments, outcome = value["member"], value["arguments"], value["outcome"]
    generic = any(marker in lower for marker in ("measure titled", "supported the measure", "opposed the measure", "official title"))
    scores = {
        "factual_support_structure": 4 if source_mapped else 1,
        "procedural_description_structure": 4 if vote_type.replace("_", " ") in lower or any(
            token in lower for token in ("passage", "amendment", "motion", "rule", "procedural", "agreed")
        ) else 2,
        "policy_mechanism_specificity": 4 if _present(practical) and len(_text(practical).split()) >= 12 and not generic else (2 if _present(practical) else 0),
        "practical_effect_clarity": 4 if _present(practical) and not generic else (2 if _present(practical) else 0),
        "affected_entity_specificity": 4 if _present(value["affected"]) else (2 if _present(practical) and any(c.isupper() for c in _text(practical)) else 1),
        "member_vote_meaning": 4 if _present(member) and ("yea" in _text(member).lower() or "nay" in _text(member).lower()) else (2 if _present(member) else 0),
        "credible_argument_framing": 4 if isinstance(arguments, dict) and all(
            _present(arguments.get(k)) or arguments.get(k) == "not_applicable"
            for k in ("supporter_rationale", "opponent_rationale")
        ) else (2 if isinstance(arguments, dict) else 1),
        "outcome_and_later_status_clarity": 4 if any(token in _text(outcome).lower() for token in ("passed", "failed", "became law", "later", "final")) else (2 if _present(outcome) else 0),
        "source_map_presence": 4 if source_mapped else 0,
        "calibration_and_non_overclaiming": 4 if _present(value["boundary"]) else 1,
        "plain_language_comprehension": 4 if _present(decision) and _present(practical) else (2 if _present(decision) else 0),
        "distinctiveness_from_title_or_summary": 4 if _present(practical) and not generic else (1 if generic else 2),
    }
    fatal = detect_fatal_defects(value, vote_type=vote_type, source_mapped=source_mapped)
    total = sum(scores.values())
    answerable = {}
    if comprehension:
        for item in comprehension:
            answerable[item["question"]] = _present(item.get("answer_key"))
    strong_gate = all(
        answerable.get(question, False)
        for question in RUBRIC["strong_comprehension_gate"]
    ) if comprehension else _present(decision) and _present(practical) and _present(member)
    if fatal or total < 24:
        tier = "unacceptable"
    elif total <= 32:
        tier = "generic_but_structurally_adequate"
    elif total <= 39 or not strong_gate:
        tier = "useful"
    elif total <= 44:
        tier = "strong"
    else:
        tier = "exceptional"
    return {
        "automated_diagnostic_score": total,
        "maximum": 48,
        "automated_diagnostic_tier": tier,
        "fatal_defects": fatal,
        "automated_dimension_diagnostics": scores,
        "comprehension_answerable": answerable,
        "strong_comprehension_gate": strong_gate,
    }


def validate_claim_map(case: dict[str, Any]) -> list[str]:
    dossier = case["dossier"]
    source_map = dossier.get("claim_level_source_map") or []
    errors = []
    urls = dossier.get("official_source_urls") or []
    for url in urls:
        if not re.match(r"^https://(clerk\.house\.gov|www\.senate\.gov|www\.congress\.gov)/", url):
            errors.append(f"{case['benchmark_id']}: non-official roll-call URL {url}")
    mapped = {entry.get("claim") for entry in source_map}
    required_mapping = {
        "official_vote_question": "official_vote_question",
        "policy_baseline": "policy_baseline",
        "proposed_policy_mechanism": "proposed_policy_mechanism",
        "practical_effect_if_adopted": "practical_effect_if_adopted",
        "affected_entities": "affected_entities",
        "documented_amounts_dates_thresholds": "documented_amounts_dates_thresholds",
        "supporter_rationale": "supporter_rationale",
        "opponent_rationale": "opponent_rationale",
        "subsequent_legislative_or_legal_status": "subsequent_status",
        "member_vote_meaning_yea": "yea_meaning",
        "member_vote_meaning_nay": "nay_meaning",
        "what_not_to_infer": "what_not_to_infer",
    }
    for field, claim in required_mapping.items():
        if _present(dossier.get(field)) and claim not in mapped:
            errors.append(f"{case['benchmark_id']}: material field {field} lacks claim map")
    for entry in source_map:
        if entry.get("source_url") not in urls:
            errors.append(f"{case['benchmark_id']}: claim map URL is not declared")
    return errors


def validate_issue_slice(slice_: dict[str, Any]) -> list[str]:
    errors = []
    included = slice_.get("included_roll_calls") or []
    mapped = slice_.get("claim_to_vote_support", {}).get("bounded_pattern") or []
    if set(mapped) - set(included):
        errors.append(f"{slice_['slice_id']}: claim maps to excluded vote")
    if len(included) < 3 and "pattern" in slice_.get("candidate_gold_synthesis", "").lower():
        errors.append(f"{slice_['slice_id']}: pattern claim below three-vote gate")
    return errors


def score_issue_synthesis(slice_: dict[str, Any], *, surface: str) -> dict[str, Any]:
    included = slice_.get("included_roll_calls") or []
    excluded = slice_.get("excluded_roll_calls") or []
    mapped = slice_.get("claim_to_vote_support", {}).get("bounded_pattern") or []
    if surface == "current":
        score = 24 if slice_.get("current_public_synthesis") else 0
        fatal = []
    else:
        fatal = ["insufficient_issue_pattern_evidence"] if len(included) < 3 and "pattern" in slice_.get("candidate_gold_synthesis", "").lower() else []
        score = 36
        score += 2 if set(mapped) == set(included) else -8
        score += 2 if all(row.get("reason") for row in excluded) else 0
        score += 2 if len(slice_.get("must_not_imply") or []) >= 3 else 0
        if len(included) < 3:
            score = min(score, 32)
    if fatal or score < 24:
        tier = "unacceptable"
    elif score <= 32:
        tier = "generic_but_structurally_adequate"
    elif score <= 39:
        tier = "useful"
    elif score <= 44:
        tier = "strong"
    else:
        tier = "exceptional"
    return {
        "automated_diagnostic_score": score,
        "maximum": 48,
        "automated_diagnostic_tier": tier,
        "fatal_defects": fatal,
    }


def validate_benchmark(payload: dict[str, Any]) -> list[str]:
    errors = []
    cases = payload.get("cases") or []
    if len(cases) < 48:
        errors.append("benchmark must contain at least 48 cases")
    ids = [case.get("benchmark_id") for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("duplicate roll-call identity")
    cohorts = Counter(case.get("cohort") for case in cases)
    if cohorts != Counter({"house_substantive": 32, "senate_substantive": 8, "control": 8}):
        errors.append(f"unexpected cohort composition: {dict(cohorts)}")
    domains = {case.get("issue_domain") for case in cases}
    expected_domains = {
        "ECONOMY_TAXES", "HEALTH_SOCIAL", "EDUCATION_WORKFORCE", "ENVIRONMENT_ENERGY",
        "NATIONAL_SECURITY_FOREIGN", "IMMIGRATION_BORDER", "JUSTICE_PUBLIC_SAFETY",
        "INFRASTRUCTURE_TECH_TRANSPORT",
    }
    if not expected_domains.issubset(domains) or domains - expected_domains - {"UNRESOLVED"}:
        errors.append(f"domain coverage mismatch: {sorted(domains)}")
    for case in cases:
        errors.extend(validate_claim_map(case))
        questions = case.get("comprehension_test") or []
        if len(questions) != 4 or any(not q.get("answer_key") or not q.get("fields_needed") for q in questions):
            errors.append(f"{case.get('benchmark_id')}: incomplete comprehension contract")
    if len(payload.get("issue_synthesis_slices") or []) < 8:
        errors.append("need at least eight issue-synthesis slices")
    for slice_ in payload.get("issue_synthesis_slices") or []:
        errors.extend(validate_issue_slice(slice_))
        if slice_.get("representative") is not None or slice_.get("real_person_attribution") is not False:
            errors.append(f"{slice_.get('slice_id')}: unsupported real-person attribution")
    if payload.get("production_access") is not False:
        errors.append("benchmark must explicitly disable production access")
    return errors


def _distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(row["automated_diagnostic_tier"] for row in rows))


def _rates(cases: list[dict[str, Any]]) -> dict[str, float]:
    dossier_fields = (
        "policy_baseline", "proposed_policy_mechanism", "practical_effect_if_adopted",
        "affected_entities", "documented_amounts_dates_thresholds", "supporter_rationale",
        "opponent_rationale", "subsequent_legislative_or_legal_status",
        "member_vote_meaning_yea", "member_vote_meaning_nay",
    )
    substantive = [case for case in cases if case["cohort"] != "control"]
    field_total = len(substantive) * len(dossier_fields)
    field_present = sum(_present(case["dossier"].get(field)) for case in substantive for field in dossier_fields)
    source_complete = sum(not validate_claim_map(case) for case in cases)
    questions = [q for case in cases for q in case["comprehension_test"]]
    return {
        "field_completeness_percent": round(100 * field_present / field_total, 1),
        "claim_map_presence_rate_percent": round(100 * source_complete / len(cases), 1),
        "claim_map_support_verified_percent": 0.0,
        "claim_map_support_verification_status": "pending_human_source_verification",
        "comprehension_answerability_percent": round(100 * sum(_present(q["answer_key"]) for q in questions) / len(questions), 1),
    }


def _genericity(cases: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(label for case in cases for label in case.get("genericity_labels", []))
    return {label: counts[label] for label in GENERICITY_TAXONOMY}


def _genericity_examples(cases: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        label: [case["benchmark_id"] for case in cases if label in case.get("genericity_labels", [])][:3]
        for label in GENERICITY_TAXONOMY
    }


def _group_findings(scored_cases: list[dict[str, Any]], key_fn) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in scored_cases:
        groups[str(key_fn(case))].append(case)
    return {
        key: {
            "cases": len(rows),
            "current_stored_structural_diagnostic_mean": round(mean(r["diagnostics"]["current_stored_structural_diagnostic"]["automated_diagnostic_score"] for r in rows), 1),
            "public_field_availability_proxy_mean": round(mean(r["diagnostics"]["public_field_availability_proxy"]["automated_diagnostic_score"] for r in rows), 1),
            "candidate_draft_structural_diagnostic_mean": round(mean(r["diagnostics"]["candidate_draft_structural_diagnostic"]["automated_diagnostic_score"] for r in rows), 1),
        }
        for key, rows in sorted(groups.items())
    }


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    errors = validate_benchmark(payload)
    if errors:
        raise ValueError("benchmark validation failed:\n- " + "\n- ".join(errors))
    scored_cases = []
    for case in payload["cases"]:
        mapped = not validate_claim_map(case)
        diagnostics = {
            "current_stored_structural_diagnostic": score_interpretation(
                case["current_stored_interpretation"], surface="current_stored",
                vote_type=case["dossier"]["vote_stage_type"], source_mapped=mapped,
            ),
            "public_field_availability_proxy": score_interpretation(
                case["public_field_availability_proxy"], surface="public_field_availability_proxy",
                vote_type=case["dossier"]["vote_stage_type"], source_mapped=mapped,
            ),
            "candidate_draft_structural_diagnostic": score_interpretation(
                case["candidate_gold_interpretation"], surface="candidate_gold",
                vote_type=case["dossier"]["vote_stage_type"], source_mapped=mapped,
                comprehension=case["comprehension_test"],
            ),
        }
        scored_cases.append({
            "benchmark_id": case["benchmark_id"], "cohort": case["cohort"],
            "chamber": case["dossier"]["chamber"], "vote_type": case["dossier"]["vote_stage_type"],
            "issue_domain": case["issue_domain"], "diagnostics": diagnostics,
        })
    surfaces = (
        "current_stored_structural_diagnostic",
        "public_field_availability_proxy",
        "candidate_draft_structural_diagnostic",
    )
    aggregate = {}
    for surface in surfaces:
        rows = [case["diagnostics"][surface] for case in scored_cases]
        aggregate[surface] = {
            "distribution": _distribution(rows),
            "automated_diagnostic_mean_score": round(mean(row["automated_diagnostic_score"] for row in rows), 1),
            "fatal_defect_count": sum(bool(row["fatal_defects"]) for row in rows),
            "generic_structural_diagnostic_rate_percent": round(100 * sum(row["automated_diagnostic_tier"] == "generic_but_structurally_adequate" for row in rows) / len(rows), 1),
            "useful_or_better_diagnostic_rate_percent": round(100 * sum(row["automated_diagnostic_tier"] in {"useful", "strong", "exceptional"} for row in rows) / len(rows), 1),
            "strong_or_better_diagnostic_rate_percent": round(100 * sum(row["automated_diagnostic_tier"] in {"strong", "exceptional"} for row in rows) / len(rows), 1),
            "diagnostic_label_caveat": "Tiers are automated structural/heuristic diagnostics only; human editorial scoring is pending.",
        }
    # Conservative parent-measure grouping: same source artifact + normalized facet can share
    # baseline research, but amendments retain their own amendment dossier.
    reuse_keys = {
        (case["source_artifact"], case["issue_domain"], case["dossier"]["vote_stage_type"] != "amendment")
        for case in payload["cases"]
    }
    heuristic_group_count = len(reuse_keys)
    issue_results = [
        {
            "slice_id": slice_["slice_id"],
            "current_synthesis_structural_diagnostic": score_issue_synthesis(slice_, surface="current"),
            "candidate_synthesis_structural_diagnostic": score_issue_synthesis(slice_, surface="candidate"),
        }
        for slice_ in payload["issue_synthesis_slices"]
    ]
    return {
        "schema_version": "legislative_interpretation_quality_structural_diagnostic_scorecard_v1",
        "diagnostic_scope": {
            "kind": "automated_structural_heuristic_only",
            "verified_editorial_quality_judgment": False,
            "human_editorial_scoring_status": "pending",
            "strong_label_meaning": "strong under the automated diagnostic rubric only",
            "source_map_presence_proves_factual_support": False,
            "candidate_drafts_remain_machine_drafts": True,
        },
        "benchmark_composition": payload["composition"],
        "aggregate_scores": aggregate,
        "genericity_counts": _genericity(payload["cases"]),
        "genericity_examples": _genericity_examples(payload["cases"]),
        "completeness": _rates(payload["cases"]),
        "findings_by_vote_type": _group_findings(scored_cases, lambda c: c["vote_type"]),
        "findings_by_domain": _group_findings(scored_cases, lambda c: c["issue_domain"]),
        "findings_by_chamber": _group_findings(scored_cases, lambda c: c["chamber"]),
        "findings_by_review_mode": _group_findings(scored_cases, lambda c: "reviewed" if c["cohort"] != "control" else "deterministic_control"),
        "issue_synthesis": {
            "slice_count": len(payload["issue_synthesis_slices"]),
            "minimum_evidence_gate": 3,
            "procedural_votes_excluded": sum(len(s["excluded_roll_calls"]) for s in payload["issue_synthesis_slices"]),
            "all_claims_mapped": all(not validate_issue_slice(s) for s in payload["issue_synthesis_slices"]),
            "human_review_required": True,
            "current_automated_diagnostic_distribution": dict(Counter(row["current_synthesis_structural_diagnostic"]["automated_diagnostic_tier"] for row in issue_results)),
            "candidate_automated_diagnostic_distribution": dict(Counter(row["candidate_synthesis_structural_diagnostic"]["automated_diagnostic_tier"] for row in issue_results)),
            "slice_scores": issue_results,
        },
        "public_copy_information_loss": payload["public_copy_boundary_inventory"],
        "measure_reuse": {
            "benchmark_roll_calls": len(payload["cases"]),
            "estimate_kind": "heuristic_noncanonical_grouping_estimate",
            "grouping_method": "source artifact + issue domain + amendment/non-amendment flag",
            "canonical_measure_dossier_count": None,
            "heuristic_group_count": heuristic_group_count,
            "amendments_requiring_separate_dossiers": sum(c["dossier"]["vote_stage_type"] == "amendment" for c in payload["cases"]),
            "procedural_votes_that_can_reference_parent": sum(c["cohort"] == "control" for c in payload["cases"]),
            "heuristic_workload_reduction_estimate_percent": round(100 * (len(payload["cases"]) - heuristic_group_count) / len(payload["cases"]), 1),
            "canonical_identity_resolution_pending": True,
        },
        "human_review": {
            "statuses": ["machine_draft", "structurally_validated", "source_verified", "human_reviewed", "gold_benchmark", "rejected"],
            "must_verify": ["policy mechanism", "affected entities", "yea/nay meaning", "argument attribution", "outcome/status", "issue-pattern conclusion"],
            "automated_scoring_replaces_editorial_judgment": False,
        },
        "recommended_next_milestone": "Valerie Foushee Economy & Taxes Interpretation Quality V2",
        "case_scores": scored_cases,
        "production_or_runtime_mutation": False,
    }


def _markdown(report: dict[str, Any]) -> str:
    agg = report["aggregate_scores"]
    composition = report["benchmark_composition"]
    lines = [
        "# Legislative Interpretation Quality Benchmark V1 Review Packet", "",
        "## Summary", "",
        f"The benchmark contains **{composition['total']} unique official roll calls**: "
        f"{composition['cohorts']['house_substantive']} House substantive cases, "
        f"{composition['cohorts']['senate_substantive']} Senate substantive cases, and "
        f"{composition['cohorts']['control']} explicit ambiguity/procedure controls. "
        "All candidate interpretations remain machine drafts. All scores and tiers are automated structural/heuristic diagnostics, not verified editorial-quality judgments; human editorial scoring and source verification are pending.", "",
        "## Why Current Interpretations Feel Generic", "",
        "The failure is usually not a false topic label. It is the absence of the policy baseline, concrete government lever, affected entity, magnitude/timing, attributed dispute, and lifecycle. Older rows often restate an official title; newer reviewed rows contain useful mechanism and status detail. The public-copy safety boundary then deliberately removes raw row fields from top-level synthesis, so even strong stored detail can collapse to a short curated facet or generic domain theme.", "",
        "## Existing Pipeline Map", "",
        "1. Official House/Senate and Congress.gov records enter chamber adapters and source caches.",
        "2. Deterministic classifiers decide domain, vote eligibility, and procedural/limited-context treatment.",
        "3. `vote_interpretations` stores status, support/opposition positions, reviewed plain-language fields, source basis, uncertainty, and review metadata.",
        "4. Manual export/import packets support supervised review; LLM text does not decide eligibility or vote meaning.",
        "5. Backend issue reads aggregate only eligible interpreted Yes/No rows; procedural and not-voting rows remain excluded.",
        "6. Frontend evidence cards may show reviewed row fields, while top-level issue copy uses curated safe themes and generic fallbacks.",
        "7. Golden-render fixtures exercise the current public surface deterministically.", "",
        "## Benchmark Composition", "",
        f"- Cohorts: `{json.dumps(composition['cohorts'], sort_keys=True)}`",
        f"- Chambers (controls included): `{json.dumps(composition['chambers'], sort_keys=True)}`",
        f"- Vote types: `{json.dumps(composition['vote_types'], sort_keys=True)}`",
        f"- Domains: `{json.dumps(composition['domains'], sort_keys=True)}`", "",
        "## Source Hierarchy", "",
        "The benchmark prefers official chamber and Congress.gov records, then CRS, CBO, committee reports, measure text, the Congressional Record, executive-agency material, attributed official advocacy, and other directly relevant government reports. Search snippets are never evidence, and advocacy is never presented as neutral fact.", "",
        "## Dossier Contract", "",
        "The reusable hierarchy is measure dossier → amendment dossier → roll-call interpretation → member-specific vote context → issue-synthesis evidence unit. Unknown facts remain `insufficient_official_evidence`; genuinely inapplicable fields use `not_applicable`. Structural claim maps are mandatory, and human source verification remains a separate status.", "",
        "## Quality Rubric And Fatal Defects", "",
        "Twelve dimensions score 0–4 (48 maximum). Fatal overrides cover reversed Yea/Nay mechanics, procedural/final confusion, false enactment, invented effects or affected groups, motive, neutralized advocacy, under-evidenced patterns, title restatements used as explanation, and unmapped material claims.", "",
        "## Automated Structural/Heuristic Diagnostic Scorecard", "",
        "`strong` means strong under the automated diagnostic rubric only. It does not mean human-reviewed, source-verified, or editorially approved. Source-map presence does not prove that a cited source supports a claim.", "",
        "| Diagnostic target | Mean / 48 | Automated diagnostic tier distribution | Fatal flags | Diagnostic strong+ |",
        "|---|---:|---|---:|---:|",
    ]
    for surface, label in (
        ("current_stored_structural_diagnostic", "Stored-field structure"),
        ("public_field_availability_proxy", "Public field availability proxy"),
        ("candidate_draft_structural_diagnostic", "Candidate machine-draft structure"),
    ):
        row = agg[surface]
        lines.append(f"| {label} | {row['automated_diagnostic_mean_score']} | `{json.dumps(row['distribution'], sort_keys=True)}` | {row['fatal_defect_count']} | {row['strong_or_better_diagnostic_rate_percent']}% |")
    lines += [
        "", "Thresholds are benchmark hypotheses, not production acceptance rules. Fatal flags override the automated diagnostic score. Human editorial scoring is pending.", "",
        "## Genericity Taxonomy", "",
    ]
    for key, value in report["genericity_counts"].items():
        examples = ", ".join(report["genericity_examples"][key]) or "none in V1 sample"
        lines.append(f"- `{key}`: {value}; examples: {examples}.")
    lines += [
        "", "## Field, Source, And Comprehension Completeness", "",
        f"- Dossier field completeness: {report['completeness']['field_completeness_percent']}%.",
        f"- Claim-map presence rate: {report['completeness']['claim_map_presence_rate_percent']}%.",
        f"- Human-verified claim support recorded by this automated milestone: {report['completeness']['claim_map_support_verified_percent']}%; status `{report['completeness']['claim_map_support_verification_status']}`.",
        "- A mapping entry's presence does not establish that its cited source factually supports the claim.",
        f"- Four-question answerability: {report['completeness']['comprehension_answerability_percent']}%.",
        "- `insufficient_official_evidence` is counted as incomplete, not silently converted into a claim.", "",
        "## Public-Rendering Information Loss", "",
        "Raw reviewed evidence fields are correctly blocked from uncontrolled top-level use. This benchmark measures a `public_field_availability_proxy`; it does not execute the exact runtime rendering path. The proxy shows that baseline, mechanism, affected entities, amounts/timing, arguments, later status, and exact yea/nay translation may be unavailable to public-copy helpers. The future contract should allow human-approved claim objects—not arbitrary raw text—to flow to top-level copy.", "",
        "## Issue-Synthesis Findings", "",
        f"Eight synthetic, non-person-attributed domain fixtures are included. Current automated diagnostic distribution: `{json.dumps(report['issue_synthesis']['current_automated_diagnostic_distribution'], sort_keys=True)}`. Candidate automated diagnostic distribution: `{json.dumps(report['issue_synthesis']['candidate_automated_diagnostic_distribution'], sort_keys=True)}`. The deterministic minimum is {report['issue_synthesis']['minimum_evidence_gate']} substantive interpreted votes; {report['issue_synthesis']['procedural_votes_excluded']} procedural/control appearances are explicitly excluded. Each candidate claim maps to included votes and remains subject to human review. Sparse fixtures must say evidence is limited rather than assert a pattern.", "",
        "## Measure Reuse Findings", "",
        f"A noncanonical heuristic groups the {report['measure_reuse']['benchmark_roll_calls']} roll calls into {report['measure_reuse']['heuristic_group_count']} provisional research groups using `{report['measure_reuse']['grouping_method']}`. It yields a {report['measure_reuse']['heuristic_workload_reduction_estimate_percent']}% heuristic workload-reduction estimate. This is not a canonical measure-dossier count; canonical identity resolution is pending. {report['measure_reuse']['amendments_requiring_separate_dossiers']} amendments still require amendment dossiers, and {report['measure_reuse']['procedural_votes_that_can_reference_parent']} controls can reference parent context without inheriting substantive meaning.", "",
        "Recommended hierarchy: measure dossier → amendment dossier → roll-call interpretation → member-specific vote context → issue-synthesis evidence unit.", "",
        "## Human Review Requirements", "",
        "Machine generation may draft paraphrases, propose claim links, identify missing fields, and calculate structural/heuristic diagnostics. Human reviewers must verify policy mechanism, affected entities, yea/nay mechanics, advocacy attribution, outcome/later status, and every issue-pattern conclusion before `gold_benchmark` status. Candidate drafts remain machine drafts, and human editorial scoring is pending.", "",
        "## Comprehension Protocol", "",
        "Each case asks what Congress was deciding, what would change, who/what was affected, and what the member's vote meant. A candidate cannot receive a `strong` automated diagnostic tier unless questions 1, 2, and 4 are structurally answerable. Later human testing must evaluate factual and editorial quality.", "",
        "## Recommended Next Implementation Milestone", "",
        "**Valerie Foushee Economy & Taxes Interpretation Quality V2**: add the dossier and claim-map objects for one existing golden slice; source-verify the vote mechanics; expose only human-approved public claims; update vote cards and one issue synthesis; then run rendered comprehension checks before scaling coverage.", "",
        "## Production Safety", "",
        "No production connection, database write, schema/migration, interpretation import, API change, frontend change, runtime change, alignment/readiness change, or paid model call occurred.", "",
        "## Stop Conditions And Limitations", "",
        "- Machine-draft candidates are not approved gold.",
        "- Missing official evidence remains explicit.",
        "- Claim-map presence here is structural and does not prove factual source support.",
        "- Publication must stop if unrelated artifacts would be staged.", "",
        "## Detailed Breakdowns", "",
    ]
    for heading, key in (("Vote type", "findings_by_vote_type"), ("Issue domain", "findings_by_domain"), ("Chamber", "findings_by_chamber"), ("Review mode", "findings_by_review_mode")):
        lines += [f"### {heading}", "", "| Group | Cases | Stored-field diagnostic | Public availability proxy | Candidate-draft diagnostic |", "|---|---:|---:|---:|---:|"]
        for name, row in report[key].items():
            lines.append(f"| {name} | {row['cases']} | {row['current_stored_structural_diagnostic_mean']} | {row['public_field_availability_proxy_mean']} | {row['candidate_draft_structural_diagnostic_mean']} |")
        lines.append("")
    lines += [
        "## Tests", "",
        "Validation commands and final results are recorded in the active plan and PR body after execution.", "",
        "## Files Changed", "",
        "This milestone adds only benchmark scripts, focused tests, generated benchmark/rubric artifacts, design contracts, the active plan, and review packets.", "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--rubric-output", type=Path, default=DEFAULT_RUBRIC)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    payload = json.loads(args.benchmark.read_text(encoding="utf-8"))
    report = analyze(payload)
    for path in (args.rubric_output, args.json_output, args.markdown_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.rubric_output.write_text(json.dumps(RUBRIC, indent=2) + "\n", encoding="utf-8")
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate_scores"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
