from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.build_legislative_interpretation_quality_benchmark import (
    DOMAINS,
    MISSING,
    build_benchmark,
)
from scripts.score_legislative_interpretation_quality_benchmark import (
    analyze,
    detect_fatal_defects,
    score_interpretation,
    score_issue_synthesis,
    validate_benchmark,
    validate_claim_map,
    validate_issue_slice,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def benchmark():
    return build_benchmark()


def test_benchmark_sample_size_strata_and_domain_coverage(benchmark):
    assert benchmark["composition"]["total"] == 48
    assert benchmark["composition"]["cohorts"] == {
        "house_substantive": 32,
        "senate_substantive": 8,
        "control": 8,
    }
    assert set(DOMAINS).issubset(benchmark["composition"]["domains"])
    assert set(benchmark["composition"]["domains"]) <= set(DOMAINS) | {"UNRESOLVED"}


def test_duplicate_roll_calls_are_rejected(benchmark):
    broken = copy.deepcopy(benchmark)
    broken["cases"][1]["benchmark_id"] = broken["cases"][0]["benchmark_id"]
    assert "duplicate roll-call identity" in validate_benchmark(broken)


def test_source_urls_and_claim_maps_are_valid(benchmark):
    assert all(not validate_claim_map(case) for case in benchmark["cases"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("affected_entities", "Unsupported population"),
        ("documented_amounts_dates_thresholds", "$999 billion"),
        ("subsequent_legislative_or_legal_status", "Became law"),
        ("policy_baseline", "Unsupported prior law"),
    ],
)
def test_unsupported_material_claims_are_rejected(benchmark, field, value):
    case = copy.deepcopy(benchmark["cases"][0])
    case["dossier"][field] = value
    assert any(field in error for error in validate_claim_map(case))


def test_missing_fields_use_explicit_markers(benchmark):
    required = ("policy_baseline", "practical_effect_if_adopted", "affected_entities")
    for case in benchmark["cases"]:
        for field in required:
            assert field in case["dossier"]
            assert case["dossier"][field] is not None


def test_missing_practical_effect_cannot_score_strong():
    result = score_interpretation(
        {
            "one_sentence_decision": "The House voted on an amendment.",
            "practical_effect": MISSING,
            "affected_entities": MISSING,
            "member_vote_meaning": {"yea": "A Yea adopted it.", "nay": "A Nay rejected it."},
            "credible_dispute": {"supporter_rationale": MISSING, "opponent_rationale": MISSING},
            "consequence_and_outcome": {"stage": "amendment"},
            "bounded_inference": "This does not establish motive.",
        },
        surface="candidate_gold",
        vote_type="amendment",
        source_mapped=True,
    )
    assert result["automated_dimension_diagnostics"]["practical_effect_clarity"] == 0
    assert result["automated_diagnostic_tier"] != "strong"


def test_missing_member_vote_meaning_cannot_pass_comprehension_gate():
    result = score_interpretation(
        {"one_sentence_decision": "The Senate voted on passage.", "practical_effect": "The bill would change agency reporting.", "bounded_inference": "No motive inference."},
        surface="candidate_gold",
        vote_type="final_passage",
        source_mapped=True,
    )
    assert result["automated_dimension_diagnostics"]["member_vote_meaning"] == 0
    assert not result["strong_comprehension_gate"]


def test_yea_nay_reversal_is_fatal():
    normalized = {"member": {"yea": "blocked the policy", "nay": "advanced the policy"}}
    assert "yea_nay_reversal" in detect_fatal_defects(
        normalized,
        vote_type="final_passage",
        source_mapped=True,
        expected_yea="advanced the policy",
        expected_nay="blocked the policy",
    )


def test_procedural_final_passage_confusion_is_fatal_but_negation_is_not():
    bad = {"decision": "This procedural motion enacted the underlying bill by final passage."}
    good = {"decision": "This was procedure, not final passage of the underlying bill."}
    assert "procedural_final_passage_confusion" in detect_fatal_defects(bad, vote_type="motion", source_mapped=True)
    assert "procedural_final_passage_confusion" not in detect_fatal_defects(good, vote_type="motion", source_mapped=True)


def test_title_restatement_fatal_override():
    payload = {
        "one_sentence_decision": "The House voted on passage.",
        "practical_effect": "Would advance the measure identified by the official title.",
        "member_vote_meaning": {"yea": "A Yea passed it.", "nay": "A Nay rejected it."},
        "bounded_inference": "No motive inference.",
    }
    result = score_interpretation(payload, surface="candidate_gold", vote_type="final_passage", source_mapped=True)
    assert "title_restatement_as_practical_explanation" in result["fatal_defects"]
    assert result["automated_diagnostic_tier"] == "unacceptable"


def test_attributed_arguments_score_higher_than_missing_arguments():
    base = {
        "one_sentence_decision": "The Senate voted on an amendment.",
        "practical_effect": "The amendment would change an agency reporting deadline.",
        "member_vote_meaning": {"yea": "A Yea adopted it.", "nay": "A Nay rejected it."},
        "bounded_inference": "The vote does not establish motive.",
    }
    missing = score_interpretation(base, surface="candidate_gold", vote_type="amendment", source_mapped=True)
    attributed_payload = copy.deepcopy(base)
    attributed_payload["credible_dispute"] = {
        "supporter_rationale": "Supporters argued the deadline improved oversight.",
        "opponent_rationale": "Opponents argued the deadline burdened implementation.",
    }
    attributed = score_interpretation(attributed_payload, surface="candidate_gold", vote_type="amendment", source_mapped=True)
    assert attributed["automated_dimension_diagnostics"]["credible_argument_framing"] > missing["automated_dimension_diagnostics"]["credible_argument_framing"]


def test_insufficient_evidence_controls_do_not_fabricate_substantive_effect(benchmark):
    controls = [case for case in benchmark["cases"] if case["cohort"] == "control"]
    assert len(controls) == 8
    assert all(case["dossier"]["practical_effect_if_adopted"] in {MISSING, "not_applicable"} for case in controls)
    assert all(case["candidate_gold_interpretation"]["review_status"] == "machine_draft" for case in controls)


def test_scoring_is_deterministic(benchmark):
    assert analyze(benchmark) == analyze(copy.deepcopy(benchmark))


def test_issue_synthesis_minimum_evidence_gate():
    slice_ = {
        "slice_id": "too-small",
        "included_roll_calls": ["a", "b"],
        "excluded_roll_calls": [],
        "claim_to_vote_support": {"bounded_pattern": ["a", "b"]},
        "candidate_gold_synthesis": "This pattern shows repeated choices.",
    }
    assert any("three-vote gate" in error for error in validate_issue_slice(slice_))


def test_issue_synthesis_scores_current_and_candidate_separately(benchmark):
    slice_ = benchmark["issue_synthesis_slices"][0]
    current = score_issue_synthesis(slice_, surface="current")
    candidate = score_issue_synthesis(slice_, surface="candidate")
    assert current["automated_diagnostic_tier"] == "generic_but_structurally_adequate"
    assert candidate["automated_diagnostic_score"] > current["automated_diagnostic_score"]


def test_procedural_votes_are_excluded_from_substantive_synthesis(benchmark):
    controls = {case["benchmark_id"] for case in benchmark["cases"] if case["cohort"] == "control"}
    for slice_ in benchmark["issue_synthesis_slices"]:
        assert controls.isdisjoint(slice_["included_roll_calls"])
        assert all(row["roll_call"] in controls for row in slice_["excluded_roll_calls"])


def test_issue_claim_to_vote_mapping_rejects_excluded_vote():
    slice_ = {
        "slice_id": "bad-map",
        "included_roll_calls": ["a", "b", "c"],
        "excluded_roll_calls": [{"roll_call": "d", "reason": "procedural"}],
        "claim_to_vote_support": {"bounded_pattern": ["a", "d"]},
        "candidate_gold_synthesis": "A bounded finding.",
    }
    assert any("excluded vote" in error for error in validate_issue_slice(slice_))


def test_comprehension_question_contract_is_complete(benchmark):
    for case in benchmark["cases"]:
        assert [q["question"] for q in case["comprehension_test"]] == [
            "What was Congress deciding?",
            "What would have changed?",
            "Who or what was affected?",
            "What did this member's vote mean?",
        ]
        assert all(q["allowed_equivalents"] and q["critical_misconceptions"] and q["fields_needed"] for q in case["comprehension_test"])


def test_raw_field_public_copy_boundary_inventory(benchmark):
    inventory = benchmark["public_copy_boundary_inventory"]
    assert "policy_effect" in inventory["blocked_from_top_level"]
    assert "curated facet theme" in inventory["allowed_top_level"]
    assert "mechanism" in inventory["information_loss_hypothesis"].lower()


def test_public_surface_does_not_silently_gain_blocked_storage_fields(benchmark):
    for case in benchmark["cases"]:
        assert "policy_effect" not in case["public_field_availability_proxy"]
        assert "source_basis" not in case["public_field_availability_proxy"]


def test_domain_assignment_has_no_index_fallback(benchmark):
    builder = (ROOT / "backend/scripts/build_legislative_interpretation_quality_benchmark.py").read_text(encoding="utf-8")
    assert "DOMAINS[index %" not in builder
    assert "return \"UNRESOLVED\"" in builder


def test_issue_synthesis_fixtures_have_no_real_person_attribution(benchmark):
    domains_by_id = {case["benchmark_id"]: case["issue_domain"] for case in benchmark["cases"]}
    for slice_ in benchmark["issue_synthesis_slices"]:
        assert slice_["fixture_type"] == "synthetic_issue_synthesis_fixture"
        assert slice_["representative"] is None
        assert slice_["real_person_attribution"] is False
        assert "not attributed to a real representative" in slice_["candidate_gold_synthesis"]
        assert all(domains_by_id[roll_call] == slice_["issue_domain"] for roll_call in slice_["included_roll_calls"])


def test_scorecard_labels_are_explicitly_diagnostic(benchmark):
    report = analyze(benchmark)
    assert report["diagnostic_scope"]["verified_editorial_quality_judgment"] is False
    assert report["diagnostic_scope"]["human_editorial_scoring_status"] == "pending"
    assert report["diagnostic_scope"]["source_map_presence_proves_factual_support"] is False
    assert "public_field_availability_proxy" in report["aggregate_scores"]
    assert report["measure_reuse"]["estimate_kind"] == "heuristic_noncanonical_grouping_estimate"
    assert report["measure_reuse"]["canonical_measure_dossier_count"] is None


def test_scripts_have_no_production_credentials_or_database_writes():
    script_paths = [
        ROOT / "backend/scripts/build_legislative_interpretation_quality_benchmark.py",
        ROOT / "backend/scripts/score_legislative_interpretation_quality_benchmark.py",
    ]
    forbidden = ("SUPABASE_SERVICE_ROLE_KEY", "DATABASE_URL", "psycopg", "sqlalchemy", ".insert(", ".update(", ".delete(")
    for path in script_paths:
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden)


def test_milestone_changes_are_non_runtime_by_contract():
    allowed_roots = {"backend/scripts", "backend/tests", "docs/benchmarks", "docs/design", "docs/plans", "docs/review_packets"}
    required_files = [
        "backend/scripts/build_legislative_interpretation_quality_benchmark.py",
        "backend/scripts/score_legislative_interpretation_quality_benchmark.py",
        "docs/benchmarks/legislative_interpretation_quality_v1.json",
        "docs/benchmarks/legislative_interpretation_quality_rubric_v1.json",
    ]
    assert all((ROOT / path).exists() for path in required_files)
    assert all(any(path.startswith(root) for root in allowed_roots) for path in required_files)


def test_checked_in_benchmark_matches_builder(benchmark):
    checked_in = json.loads((ROOT / "docs/benchmarks/legislative_interpretation_quality_v1.json").read_text(encoding="utf-8"))
    assert checked_in == benchmark
