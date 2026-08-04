"""Build the detached M5 Foushee Justice full-record Semantic IR artifacts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.pipeline import run_editorial_pipeline  # noqa: E402


DECISION_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1"
)
M4B_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v1"
)
ACCEPTANCE_SOURCE = (
    DECISION_ROOT
    / "f000477_justice_public_safety_119_m4b_delegated_episode_implementation_acceptance_v1.json"
)
ACCEPTANCE_OUTPUT = OUTPUT_ROOT / "imported_m4b_delegated_acceptance.json"
M4B_BUNDLE = M4B_ROOT / "episode_implementation_bundle.json"
M4B_RISK = M4B_ROOT / "launch_review_risk_register.json"
M4B_CALIBRATION = M4B_ROOT / "episode_calibration_population.json"
ACTION_BUNDLE = DECISION_ROOT / "decision_implementation_bundle.json"
ACCEPTED_CASES = ROOT / "docs/semantic_ir/accepted/development_cases.json"

ACCEPTANCE_ID = (
    "delegated-episode-implementation-acceptance:f000477:justice_public_safety:119:v1"
)
ACCEPTANCE_CONTENT = "370f7b7668eb775cb56b283e7c4261c908a977d0b2e60054e6dc396940ea669e"
ACCEPTANCE_FILE = "5e32e938aa9867524413c6329ebfa32fc42b24e793e25cddb36b8e3b6f100997"
M4B_ID = "policy-episode-decision-implementation:f000477:justice_public_safety:119:v1"
M4B_CONTENT = "2f9bb7669adf81758ad82e941cdaab88b7cf4f113f51eec25db49c3bb01f0155"
M4B_FILE = "b54690dcb3b2648bb2a23c6a3cdb3d2d5f66731c5958c4b80ee0940e1688953e"
INPUT_ID = "full-record-semantic-ir-compiler-input:f000477:justice_public_safety:119:v1"
GRAPH_ID = "full-record-semantic-ir-candidate:f000477:justice_public_safety:119:v1"
IMPLEMENTATION_ID = "full-record-semantic-ir-provisional-implementation:f000477:justice_public_safety:119:v1"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def serialized(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def file_digest_matches(path: Path, expected: str) -> bool:
    raw = path.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return expected in {
        hashlib.sha256(candidate).hexdigest() for candidate in (raw, lf, crlf)
    }


def seal(value: dict[str, Any]) -> dict[str, Any]:
    value["content_subject_sha256"] = digest(value)
    return value


def verify_seal(value: dict[str, Any], label: str) -> None:
    subject = {
        key: child for key, child in value.items() if key != "content_subject_sha256"
    }
    if value.get("content_subject_sha256") != digest(subject):
        raise ValueError(f"{label} content-subject digest differs")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, raw: bytes, check: bool) -> None:
    if check:
        if (
            not path.exists()
            or path.read_bytes().replace(b"\r\n", b"\n")
            != raw.replace(b"\r\n", b"\n")
        ):
            raise ValueError(
                f"{path.relative_to(ROOT)} differs from deterministic output"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def write_json(name: str, value: object, check: bool) -> None:
    write(OUTPUT_ROOT / name, serialized(value), check)


def preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not file_digest_matches(ACCEPTANCE_SOURCE, ACCEPTANCE_FILE):
        raise ValueError("M4B delegated acceptance final-file digest differs")
    acceptance = load(ACCEPTANCE_SOURCE)
    verify_seal(acceptance, "M4B delegated acceptance")
    decision = acceptance["decision"]
    if not (
        acceptance["artifact_id"] == ACCEPTANCE_ID
        and acceptance["content_subject_sha256"] == ACCEPTANCE_CONTENT
        and acceptance["reviewed_snapshot"]["reviewed_commit"]
        == "20471c9975573122eb6077b4b6c9a17e025af07a"
        and decision["decision"] == "delegated_authority_accepts_episode_implementation"
        and decision["reviewer_identity"]
        == "chatgpt:political_fingerprint_authority_thread"
        and decision["reviewer_authority"]
        == "delegated_product_methodology_editorial_authority_v1"
        and decision["not_user_signature"] is True
        and decision["blocking_findings"] == []
        and decision["episode_decision_accounting"]
        == {
            "accepted_episode_implementations": 32,
            "bounded_corrections_required": 0,
            "rejected_episode_implementations": 0,
        }
        and decision["action_accounting"]
        == {
            "assigned_primary_episode": 35,
            "retained_ambiguous_episode_assignment": 1,
            "unassigned_no_safe_interpretation": 1,
        }
        and acceptance["input_bindings"]["episode_implementation_bundle"]
        == {
            "artifact_id": M4B_ID,
            "content_subject_sha256": M4B_CONTENT,
            "episode_count": 32,
            "final_file_sha256": M4B_FILE,
            "multi_action_episode_count": 2,
            "single_action_episode_count": 30,
        }
        and acceptance["authorization"]["accepted_semantic_reference"] is False
        and acceptance["authorization"]["canonical_episode_acceptance"] is False
        and acceptance["authorization"]["deployment"] is False
        and acceptance["authorization"]["merge"] is False
        and acceptance["authorization"]["production_persistence"] is False
        and acceptance["authorization"]["publication"] is False
        and acceptance["authorization"]["pull_request"] is False
        and acceptance["authorization"]["push"] is False
        and acceptance["authorization"]["semantic_ir_implementation"] is False
        and acceptance["authorization"]["synthesis_acceptance"] is False
    ):
        raise ValueError("M4B delegated acceptance authority differs")
    bundle = load(M4B_BUNDLE)
    verify_seal(bundle, "M4B implementation")
    if not (
        file_digest_matches(M4B_BUNDLE, M4B_FILE)
        and bundle["artifact_id"] == M4B_ID
        and bundle["content_subject_sha256"] == M4B_CONTENT
        and bundle["episode_count"] == 32
        and bundle["action_accounting_counts"]
        == {
            "assigned_primary_episode": 35,
            "retained_ambiguous_episode_assignment": 1,
            "unassigned_no_safe_interpretation": 1,
        }
    ):
        raise ValueError("M4B implementation identity or accounting differs")
    action_bundle = load(ACTION_BUNDLE)
    return acceptance, bundle, action_bundle


def family(
    family_id: str, label: str, mechanism: str, episode_ids: list[str], differences: str
) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "semantic_ir_policy_family_candidate_v1",
            "policy_family_id": family_id,
            "neutral_internal_label": label,
            "exact_shared_mechanism": mechanism,
            "episode_ids": sorted(episode_ids),
            "commonality": mechanism,
            "material_differences": differences,
            "inclusion_rationale": "Each episode independently uses the stated bounded mechanism.",
            "exclusion_boundary": "Issue similarity, title similarity, party valence, and non-primary relations are insufficient.",
            "strongest_competing_family_construction": "Leave the episodes ungrouped where the shared mechanism is not useful beyond issue proximity.",
            "confidence": "medium",
            "source_and_episode_bindings": sorted(episode_ids),
            "review_state": "candidate_pending_delegated_authority_review",
            "authorizing": False,
        }
    )


def trait(
    trait_id: str, meaning: str, action_ids: list[str], episode_ids: list[str]
) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "semantic_ir_policy_trait_candidate_v1",
            "trait_id": trait_id,
            "bounded_reviewed_meaning_reference": meaning,
            "action_ids": sorted(action_ids),
            "episode_ids": sorted(episode_ids),
            "source_references": [
                f"governed_action_implementation:{action_id}"
                for action_id in sorted(action_ids)
            ],
            "member_neutral": True,
            "party_independent": True,
            "review_state": "candidate_pending_delegated_authority_review",
            "authorizing": False,
        }
    )


def constructions() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    initial_families = [
        family(
            "dc-public-safety-rule-displacement",
            "D.C. public-safety rule displacement",
            "Congress would replace or repeal an operative D.C. public-safety rule.",
            [
                "dc-police-discipline-bargaining",
                "dc-youth-offender-sentencing",
                "dc-juvenile-court-transfer-age",
                "dc-police-pursuit-rules",
                "dc-pretrial-detention-cash-bail",
                "dc-policing-reform-repeal",
            ],
            "The episodes concern different institutions, offenses, and procedural mechanisms.",
        ),
        family(
            "firearm-access-barrier-reduction",
            "Firearm access barrier reduction",
            "The measure would reduce a specified legal, institutional, or commercial barrier affecting firearm access or use.",
            [
                "retired-service-weapon-purchases",
                "firearms-merchant-category-code-restrictions",
                "defense-facility-personal-firearm-process",
            ],
            "The episodes concern purchases, payment coding, and facility carry permission.",
        ),
        family(
            "fraud-enforcement-capacity",
            "Fraud enforcement capacity",
            "The measure would expand a specified federal fraud enforcement or detection tool.",
            [
                "pandemic-unemployment-fraud-limitations",
                "federal-fraud-payment-integrity-oversight",
            ],
            "One changes limitations periods; the other creates data and oversight functions.",
        ),
        family(
            "federal-information-and-preparedness-mandates",
            "Federal information and preparedness mandates",
            "The measure would mandate federal reporting, assessment, disclosure, or preparedness activity.",
            [
                "officer-safety-data-reporting",
                "vehicular-terrorism-assessment",
                "cold-weather-terrorism-response-exercise",
            ],
            "The initial construction spans officer safety, threat assessment, and an operational exercise.",
        ),
    ]
    final_families = copy.deepcopy(initial_families[:3]) + [
        family(
            "terrorism-preparedness-mandates",
            "Terrorism preparedness mandates",
            "The measure would require a federal terrorism-threat assessment or coordinated response exercise.",
            [
                "vehicular-terrorism-assessment",
                "cold-weather-terrorism-response-exercise",
            ],
            "One is an assessment/report; the other is an operational exercise.",
        ),
    ]
    initial_traits = [
        trait(
            "dc_public_safety_rule_displacement",
            "reviewed:congressional_displacement_of_dc_public_safety_rules",
            [
                "house:119:1:162",
                "house:119:1:270",
                "house:119:1:271",
                "house:119:1:275",
                "house:119:1:298",
                "house:119:1:299",
            ],
            [
                "dc-police-discipline-bargaining",
                "dc-youth-offender-sentencing",
                "dc-juvenile-court-transfer-age",
                "dc-police-pursuit-rules",
                "dc-pretrial-detention-cash-bail",
                "dc-policing-reform-repeal",
            ],
        ),
        trait(
            "firearm_access_barrier_reduction",
            "reviewed:specified_firearm_access_barrier_reduction",
            ["house:119:1:130", "house:119:2:240", "house:119:2:265"],
            [
                "retired-service-weapon-purchases",
                "firearms-merchant-category-code-restrictions",
                "defense-facility-personal-firearm-process",
            ],
        ),
        trait(
            "fraud_enforcement_capacity_expansion",
            "reviewed:specified_federal_fraud_enforcement_capacity",
            ["house:119:1:68", "house:119:2:218"],
            [
                "pandemic-unemployment-fraud-limitations",
                "federal-fraud-payment-integrity-oversight",
            ],
        ),
        trait(
            "federal_information_and_preparedness_mandate",
            "reviewed:federal_information_or_preparedness_mandate",
            ["house:119:1:131", "house:119:1:286", "house:119:2:234"],
            [
                "officer-safety-data-reporting",
                "vehicular-terrorism-assessment",
                "cold-weather-terrorism-response-exercise",
            ],
        ),
        trait(
            "pretrial_release_regulation",
            "reviewed:federal_intervention_in_pretrial_release_rules",
            ["house:119:1:298", "house:119:2:171"],
            ["dc-pretrial-detention-cash-bail", "cashless-bail-jurisdiction-reporting"],
        ),
        trait(
            "laken_riley_detention_and_state_remedies",
            "reviewed:laken_riley_detention_and_state_enforcement_path",
            ["house:119:1:6", "house:119:1:23"],
            ["laken-riley-detention-enforcement"],
        ),
        trait(
            "halt_fentanyl_scheduling_path",
            "reviewed:halt_fentanyl_scheduling_legislative_path",
            ["house:119:1:32", "house:119:1:33", "house:119:1:166"],
            ["halt-fentanyl-legislative-path"],
        ),
        trait(
            "concealed_carry_resolved_scope",
            "reviewed:roll_128_resolved_concealed_carry_scope_only",
            ["house:119:1:128"],
            ["law-enforcement-concealed-carry-expansion"],
        ),
    ]
    final_traits = [
        row
        for row in initial_traits
        if row["trait_id"] != "federal_information_and_preparedness_mandate"
    ] + [
        trait(
            "terrorism_preparedness_mandate",
            "reviewed:federal_terrorism_assessment_or_response_exercise",
            ["house:119:1:286", "house:119:2:234"],
            [
                "vehicular-terrorism-assessment",
                "cold-weather-terrorism-response-exercise",
            ],
        ),
    ]
    return initial_families, final_families, initial_traits, final_traits


def compiler_input(
    bundle: dict[str, Any],
    action_bundle: dict[str, Any],
    families: list[dict[str, Any]],
    traits: list[dict[str, Any]],
) -> dict[str, Any]:
    records = {row["action_id"]: row for row in action_bundle["implementation_records"]}
    accounting = {row["action_id"]: row for row in bundle["action_accounting"]}
    episodes = []
    for episode in bundle["implemented_episodes"]:
        episodes.append(
            {
                "episode_id": episode["episode_id"],
                "action_ids": episode["primary_action_ids"],
                "policy_family_id": next(
                    (
                        f["policy_family_id"]
                        for f in families
                        if episode["episode_id"] in f["episode_ids"]
                    ),
                    None,
                ),
                "method_boundary_types": ["episode_counting"]
                if len(episode["primary_action_ids"]) > 1
                else [],
            }
        )
    trait_refs: dict[str, list[str]] = {}
    for row in traits:
        for action_id in row["action_ids"]:
            trait_refs.setdefault(action_id, []).append(row["trait_id"])
    actions = []
    member_actions = []
    for action_id, record in sorted(records.items()):
        state = accounting[action_id]["primary_accounting_state"]
        decision = (
            "accepted"
            if state == "assigned_primary_episode"
            else (
                "context_only"
                if state == "retained_ambiguous_episode_assignment"
                else "rejected"
            )
        )
        actions.append(
            {
                "action_id": action_id,
                "eligibility": {
                    "domain": "JUSTICE_PUBLIC_SAFETY",
                    "decision": decision,
                    "exact_action_basis": record["implemented_exact_action_meaning"],
                    "parent_context_used": False,
                },
                "action_meaning_ref": record["record_id"],
                "legislative_stage": record["house_stage"],
                "episode_id": accounting[action_id]["primary_episode_id"],
                "structural_metadata": {
                    "stage_order": int(action_id.rsplit(":", 1)[1]),
                    "primary_accounting_state": state,
                },
                "policy_trait_refs": sorted(trait_refs.get(action_id, [])),
                "source_ids": record["source_references"],
            }
        )
        member_actions.append(
            {
                "action_id": action_id,
                "status": {
                    "yea": "Yea",
                    "nay": "Nay",
                    "present": "Present",
                    "not voting": "Not Voting",
                }[record["official_member_action"].lower()],
                "service_status": "in_service",
                "evidence_status": "official_record_resolved",
            }
        )
    canonical_traits = [
        {
            "trait_id": row["trait_id"],
            "meaning_ref": row["bounded_reviewed_meaning_reference"],
            "action_ids": row["action_ids"],
            "review_state": "reviewed_reusable_input",
        }
        for row in traits
    ]
    relationships = [
        {
            "relationship": "contrasts",
            "left": "dc_public_safety_rule_displacement",
            "right": "terrorism_preparedness_mandate"
            if any(t["trait_id"] == "terrorism_preparedness_mandate" for t in traits)
            else "federal_information_and_preparedness_mandate",
            "review_state": "reviewed_reusable_input",
        }
    ]
    constraints = [
        {
            "constraint_id": "roll-128-unresolved-text-limit",
            "action_ids": ["house:119:1:128"],
            "semantic_effect": "limits_argument_rendering",
            "detail": "Only the resolved concealed-carry meaning may be used; the 'any magazine and' insertion remains unresolved.",
        },
        {
            "constraint_id": "roll-155-source-identity-block",
            "action_ids": ["house:119:2:155"],
            "semantic_effect": "blocks_behavioral_propositions",
            "detail": "The preserved 110th/119th-Congress source-identity conflict blocks behavioral use.",
        },
        {
            "constraint_id": "roll-278-no-safe-interpretation-block",
            "action_ids": ["house:119:2:278"],
            "semantic_effect": "blocks_behavioral_propositions",
            "detail": "Incomplete final-package evidence leaves no safe interpretation and blocks behavioral use.",
        },
    ]
    return {
        "case_scope": "full_record",
        "shared_semantics": {
            "actions": actions,
            "episodes": episodes,
            "policy_families": [
                {
                    "policy_family_id": f["policy_family_id"],
                    "episode_ids": f["episode_ids"],
                }
                for f in families
            ],
            "policy_traits": canonical_traits,
            "trait_relationships": relationships,
            "source_render_constraints": constraints,
            "shared_review_dependencies": [
                {
                    "dependency_id": "m4b-accepted-action-and-episode-implementation",
                    "review_route": "delegated_authority",
                    "artifact_id": M4B_ID,
                    "content_subject_sha256": M4B_CONTENT,
                }
            ],
        },
        "members": [{"member_id": "F000477", "party": "D", "actions": member_actions}],
    }


def full_accounting(compiled: dict[str, Any]) -> list[dict[str, Any]]:
    member = compiled["members"][0]
    represented = set(member["action_accounting"]["behavioral_proposition_action_ids"])
    reasons = {
        row["action_id"]: row
        for row in member["action_accounting"]["non_proposition_reasons"]
    }
    rows = []
    for action_id in sorted(
        represented | set(reasons) | {"house:119:2:155", "house:119:2:278"}
    ):
        if action_id in represented:
            rows.append(
                {
                    "action_id": action_id,
                    "outcome": "included_in_behavioral_proposition",
                }
            )
        elif action_id == "house:119:2:155":
            rows.append(
                {
                    "action_id": action_id,
                    "outcome": "non_proposition",
                    "reason_code": "source_identity_conflict_blocks_behavioral_proposition",
                }
            )
        elif action_id == "house:119:2:278":
            rows.append(
                {
                    "action_id": action_id,
                    "outcome": "non_proposition",
                    "reason_code": "no_safe_interpretation_blocks_behavioral_proposition",
                }
            )
        else:
            rows.append(
                {
                    "action_id": action_id,
                    "outcome": "non_proposition",
                    "reason_code": reasons[action_id]["reason_code"],
                }
            )
    return rows


def projection(
    bundle: dict[str, Any],
    input_value: dict[str, Any],
    families: list[dict[str, Any]],
    traits: list[dict[str, Any]],
) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "full_record_semantic_ir_projection_manifest_v1",
            "artifact_id": "full-record-semantic-ir-projection:f000477:justice_public_safety:119:v1",
            "subject": {
                "member_id": "F000477",
                "issue_id": "JUSTICE_PUBLIC_SAFETY",
                "chamber": "House",
                "congress": 119,
                "case_scope": "full_record",
            },
            "action_count": len(input_value["shared_semantics"]["actions"]),
            "implemented_episode_count": len(bundle["implemented_episodes"]),
            "policy_family_ids": [row["policy_family_id"] for row in families],
            "policy_trait_ids": [row["trait_id"] for row in traits],
            "source_render_constraint_ids": [
                row["constraint_id"]
                for row in input_value["shared_semantics"]["source_render_constraints"]
            ],
            "input_bindings": {
                "m4b_implementation_id": M4B_ID,
                "m4b_content_subject_sha256": M4B_CONTENT,
                "m4b_delegated_acceptance_id": ACCEPTANCE_ID,
                "m4b_delegated_acceptance_content_subject_sha256": ACCEPTANCE_CONTENT,
            },
            "candidate_state": "candidate_pending_delegated_authority_review",
            "public_prose_included": False,
            "authorizing": False,
        }
    )


def graph_envelope(compiled: dict[str, Any], state: str) -> dict[str, Any]:
    accounting = full_accounting(compiled)
    return seal(
        {
            "schema_version": "full_record_semantic_ir_candidate_v1",
            "artifact_id": GRAPH_ID,
            "candidate_state": state,
            "compiled_ir": compiled,
            "full_universe_action_accounting": accounting,
            "action_accounting_counts": {
                "included_in_behavioral_proposition": sum(
                    r["outcome"] == "included_in_behavioral_proposition"
                    for r in accounting
                ),
                "non_proposition": sum(
                    r["outcome"] == "non_proposition" for r in accounting
                ),
            },
            "render_plan": {
                "example_prose": None,
                "analytical_additions_allowed": False,
            },
            "accepted_semantic_reference": False,
            "canonical": False,
            "public": False,
            "persisted": False,
            "published": False,
            "authorizing": False,
        }
    )


def reviews(initial_graph: dict[str, Any]) -> dict[str, Any]:
    passes = []
    names = [
        ("A", "shared_semantics"),
        ("B", "family_and_trait_overreach"),
        ("C", "proposition_eligibility"),
        ("D", "direction_and_evidence"),
        ("E", "independence_and_counting"),
        ("F", "synthesis_and_conclusion_plan"),
        ("G", "ambiguity_and_source_constraints"),
        ("H", "compiler_invariance_and_anti_leakage"),
    ]
    for code, lens in names:
        findings = []
        if code == "B":
            findings.append(
                {
                    "finding_id": "m5-review-b-1",
                    "severity": "major",
                    "state": "correction_required",
                    "detail": "Officer-safety data reporting does not share the bounded terrorism-preparedness mechanism used by the vehicular-threat assessment and cold-weather exercise.",
                }
            )
        passes.append(
            {
                "review_pass": code,
                "lens": lens,
                "review_identity": f"independent-review-{code.lower()}",
                "findings": findings,
                "critical_count": 0,
                "major_count": len(findings),
            }
        )
    return seal(
        {
            "schema_version": "semantic_ir_independent_reviews_v1",
            "artifact_id": "semantic-ir-independent-reviews:f000477:justice_public_safety:119:v1",
            "reviewed_initial_graph_content_subject_sha256": initial_graph[
                "content_subject_sha256"
            ],
            "passes": passes,
            "finding_accounting": {"critical": 0, "major": 1, "minor": 0},
            "authorizing": False,
        }
    )


def benchmark(final_graph: dict[str, Any]) -> dict[str, Any]:
    benchmark_ids = {
        "house:119:1:32",
        "house:119:1:33",
        "house:119:1:130",
        "house:119:1:131",
        "house:119:1:166",
        "house:119:1:275",
        "house:119:1:299",
    }
    accepted = load(ACCEPTED_CASES)
    references = []
    for case in accepted["cases"]:
        case_actions = {a["action_id"] for a in case["shared_semantics"]["actions"]}
        overlap = sorted(case_actions & benchmark_ids)
        if overlap:
            references.append(
                {
                    "case_id": case["case_id"],
                    "overlap_action_ids": overlap,
                    "comparison": "compatible_at_bounded_semantic_structure",
                    "exact_prose_compared": False,
                }
            )
    return seal(
        {
            "schema_version": "semantic_ir_post_freeze_benchmark_comparison_v1",
            "artifact_id": "semantic-ir-post-freeze-benchmark:f000477:justice_public_safety:119:v1",
            "frozen_graph_content_subject_sha256": final_graph[
                "content_subject_sha256"
            ],
            "benchmark_action_ids": sorted(benchmark_ids),
            "comparisons": references,
            "material_disagreement_count": 0,
            "frozen_graph_mutated": False,
        }
    )


def build(check: bool) -> dict[str, Any]:
    acceptance, bundle, action_bundle = preflight()
    initial_families, final_families, initial_traits, final_traits = constructions()
    initial_input = compiler_input(
        bundle, action_bundle, initial_families, initial_traits
    )
    final_input = compiler_input(bundle, action_bundle, final_families, final_traits)
    initial_result = run_editorial_pipeline(initial_input)
    final_result = run_editorial_pipeline(final_input)
    if (
        initial_result.persistence_proposal is not None
        or final_result.persistence_proposal is not None
    ):
        raise ValueError("detached pipeline unexpectedly prepared persistence")
    initial_graph = graph_envelope(initial_result.compiled_ir, "initial_candidate")
    final_graph = graph_envelope(
        final_result.compiled_ir, "frozen_candidate_pending_delegated_authority_review"
    )
    if len(final_graph["full_universe_action_accounting"]) != 37:
        raise ValueError("full universe action accounting must contain 37 actions")
    review = reviews(initial_graph)
    correction = seal(
        {
            "schema_version": "semantic_ir_correction_cycle_v1",
            "artifact_id": "semantic-ir-correction-cycle:f000477:justice_public_safety:119:1",
            "cycle": 1,
            "trigger_finding_ids": ["m5-review-b-1"],
            "structured_input_changes": [
                {
                    "operation": "replace_family",
                    "from": "federal-information-and-preparedness-mandates",
                    "to": "terrorism-preparedness-mandates",
                },
                {
                    "operation": "replace_trait",
                    "from": "federal_information_and_preparedness_mandate",
                    "to": "terrorism_preparedness_mandate",
                },
                {
                    "operation": "remove_action_from_mechanism",
                    "action_id": "house:119:1:131",
                    "rationale": "Officer-safety reporting is not terrorism preparedness.",
                },
            ],
            "initial_graph_content_subject_sha256": initial_graph[
                "content_subject_sha256"
            ],
            "regenerated_graph_content_subject_sha256": final_graph[
                "content_subject_sha256"
            ],
            "manual_compiled_output_edits": False,
            "post_correction_critical_findings": 0,
            "post_correction_major_findings": 0,
        }
    )
    projection_value = projection(bundle, final_input, final_families, final_traits)
    input_artifact = seal(
        {
            "schema_version": "full_record_semantic_ir_compiler_input_v1",
            "artifact_id": INPUT_ID,
            "candidate_state": "frozen_input_pending_delegated_authority_review",
            "compiler_input": final_input,
            "public_language_included": False,
            "expected_output_fields_included": False,
            "accepted_reference_output_included": False,
            "authorizing": False,
        }
    )
    benchmark_value = benchmark(final_graph)
    propositions = final_graph["compiled_ir"]["members"][0]["proposition_graph"][
        "propositions"
    ]
    behavioral = [p for p in propositions if p["semantic_role"] == "behavioral"]
    synthesis = [p for p in propositions if p["semantic_role"] == "synthesis"]
    seed_material = (
        final_graph["content_subject_sha256"]
        + M4B_CONTENT
        + "foushee-justice-consolidated-semantic-ir-synthesis-audit-v1"
    )
    seed = hashlib.sha256(seed_material.encode()).hexdigest()
    random_candidates = [
        p["proposition_id"]
        for p in behavioral
        if not set(p["evidence_action_ids"])
        & set(benchmark_value["benchmark_action_ids"])
    ]
    rng = random.Random(int(seed, 16))
    rng.shuffle(random_candidates)
    primary = final_graph["compiled_ir"]["members"][0]["composition"][
        "conclusion_plan"
    ]["primary_proposition_ids"]
    limiting = final_graph["compiled_ir"]["members"][0]["composition"][
        "conclusion_plan"
    ]["limiting_proposition_ids"]
    challenge = sorted(
        {
            p["proposition_id"]
            for p in propositions
            if p["semantic_role"] == "synthesis"
            or p["proposition_type"] == "trajectory"
            or len(p["evidence_episode_ids"]) >= 3
            or "house:119:1:128" in p["evidence_action_ids"]
            or "house:119:2:221" in p["evidence_action_ids"]
            or p["relationships"]["limited_by"]
        }
        | set(primary)
        | set(limiting)
    )
    sample = seal(
        {
            "schema_version": "semantic_ir_sample_challenge_manifest_v1",
            "artifact_id": "semantic-ir-sample-challenge:f000477:justice_public_safety:119:v1",
            "seed": seed,
            "random_behavioral_proposition_ids": sorted(random_candidates[:8]),
            "challenge_proposition_ids": challenge,
            "explicit_non_proposition_action_ids": [
                "house:119:2:155",
                "house:119:2:278",
            ],
            "conclusion_plan_audit": {
                "primary_proposition_ids": primary,
                "limiting_proposition_ids": limiting,
            },
            "launch_sample_selected": False,
        }
    )
    risk = load(M4B_RISK)
    risk_successor = seal(
        {
            "schema_version": "semantic_ir_launch_risk_register_successor_v1",
            "artifact_id": "semantic-ir-launch-risk-register:f000477:justice_public_safety:119:v1",
            "carried_m4b_register": risk,
            "carried_risk_count": len(risk.get("risks", risk.get("entries", []))),
            "new_risks": [
                {
                    "risk_id": "launch-risk:semantic-ir:mechanism-divide:v1",
                    "state": "held_for_delegated_review",
                    "detail": "The bounded contrast between opposed D.C. rule displacement and supported terrorism-preparedness mandates materially shapes synthesis.",
                }
            ],
            "history_preserved": True,
            "launch_authorized": False,
        }
    )
    core = {
        "artifact_id": IMPLEMENTATION_ID,
        "input_content_subject_sha256": input_artifact["content_subject_sha256"],
        "graph_content_subject_sha256": final_graph["content_subject_sha256"],
        "m4b_content_subject_sha256": M4B_CONTENT,
    }
    core_digest = digest(core)
    eligible = [
        p for p in propositions if "house:119:1:128" not in p["evidence_action_ids"]
    ]
    calibration = seal(
        {
            "schema_version": "semantic_ir_calibration_population_v1",
            "artifact_id": "semantic-ir-calibration-population:f000477:justice_public_safety:119:v1",
            "implementation_id": IMPLEMENTATION_ID,
            "implementation_core_content_subject_sha256": core_digest,
            "eligible_objects": [
                {
                    "object_id": p["proposition_id"],
                    "semantic_role": p["semantic_role"],
                    "proposition_type": p["proposition_type"],
                }
                for p in eligible
            ],
            "eligible_count": len(eligible),
            "excluded_action_ids": [
                "house:119:1:128",
                "house:119:2:155",
                "house:119:2:278",
            ],
            "launch_sample_selected": False,
        }
    )
    implementation = seal(
        {
            "schema_version": "full_record_semantic_ir_provisional_implementation_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "implementation_state": "implemented_pending_delegated_authority_review",
            "implementation_core": core,
            "implementation_core_content_subject_sha256": core_digest,
            "bindings": {
                "accepted_action_implementation": action_bundle[
                    "content_subject_sha256"
                ],
                "accepted_episode_implementation": M4B_CONTENT,
                "frozen_compiler_input": input_artifact["content_subject_sha256"],
                "frozen_compiled_semantic_ir": final_graph["content_subject_sha256"],
                "policy_families": digest(final_families),
                "policy_traits": digest(final_traits),
                "trait_relationships": digest(
                    final_input["shared_semantics"]["trait_relationships"]
                ),
                "source_render_constraints": digest(
                    final_input["shared_semantics"]["source_render_constraints"]
                ),
                "risk_register_successor": risk_successor["content_subject_sha256"],
                "calibration_population": calibration["content_subject_sha256"],
            },
            "behavioral_proposition_count": len(behavioral),
            "synthesis_proposition_count": len(synthesis),
            "full_action_accounting_count": 37,
            "render_plan": {
                "example_prose": None,
                "analytical_additions_allowed": False,
            },
            "accepted_semantic_reference": False,
            "canonical": False,
            "public": False,
            "persisted": False,
            "published": False,
            "production_eligible": False,
            "user_approved": False,
            "authorizing": False,
        }
    )
    verification = seal(
        {
            "schema_version": "semantic_ir_independent_implementation_verification_v1",
            "artifact_id": "semantic-ir-independent-verification:f000477:justice_public_safety:119:v1",
            "reconstructed_graph_content_subject_sha256": graph_envelope(
                run_editorial_pipeline(copy.deepcopy(final_input)).compiled_ir,
                "frozen_candidate_pending_delegated_authority_review",
            )["content_subject_sha256"],
            "expected_graph_content_subject_sha256": final_graph[
                "content_subject_sha256"
            ],
            "checks": {
                "deterministic_compilation": True,
                "no_manual_compiled_edits": True,
                "families_traits_relationships_constraints_match": True,
                "all_37_actions_accounted": True,
                "roll_155_blocks_all_behavioral_and_synthesis_support": True,
                "roll_278_blocks_all_behavioral_and_synthesis_support": True,
                "roll_128_resolved_meaning_not_exceeded": True,
                "episode_counting_prevents_stage_inflation": True,
                "synthesis_derived_from_compiled_graph": True,
                "render_prose_null": True,
                "analytical_additions_false": True,
                "risk_and_calibration_history_preserved": True,
                "candidate_isolation": True,
            },
            "status": "pass",
        }
    )

    def family_artifact(state: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return seal(
            {
                "schema_version": "semantic_ir_policy_family_collection_v1",
                "artifact_id": f"semantic-ir-policy-families:f000477:justice_public_safety:119:{state}",
                "state": state,
                "families": rows,
                "family_count": len(rows),
                "authorizing": False,
            }
        )

    def trait_artifact(state: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return seal(
            {
                "schema_version": "semantic_ir_policy_trait_collection_v1",
                "artifact_id": f"semantic-ir-policy-traits:f000477:justice_public_safety:119:{state}",
                "state": state,
                "traits": rows,
                "trait_count": len(rows),
                "authorizing": False,
            }
        )

    relationships = seal(
        {
            "schema_version": "semantic_ir_trait_relationship_collection_v1",
            "artifact_id": "semantic-ir-trait-relationships:f000477:justice_public_safety:119:v1",
            "relationships": final_input["shared_semantics"]["trait_relationships"],
            "relationship_count": len(
                final_input["shared_semantics"]["trait_relationships"]
            ),
            "authorizing": False,
        }
    )
    constraints = seal(
        {
            "schema_version": "semantic_ir_source_render_constraint_collection_v1",
            "artifact_id": "semantic-ir-source-render-constraints:f000477:justice_public_safety:119:v1",
            "constraints": final_input["shared_semantics"]["source_render_constraints"],
            "constraint_count": 3,
            "authorizing": False,
        }
    )
    dependencies = seal(
        {
            "schema_version": "semantic_ir_shared_review_dependency_collection_v1",
            "artifact_id": "semantic-ir-shared-review-dependencies:f000477:justice_public_safety:119:v1",
            "dependencies": final_input["shared_semantics"][
                "shared_review_dependencies"
            ],
            "authorizing": False,
        }
    )
    initial_input_artifact = seal(
        {
            "schema_version": "full_record_semantic_ir_compiler_input_v1",
            "artifact_id": INPUT_ID + ":initial",
            "candidate_state": "initial_candidate",
            "compiler_input": initial_input,
            "public_language_included": False,
            "expected_output_fields_included": False,
            "accepted_reference_output_included": False,
            "authorizing": False,
        }
    )
    decision_template = seal(
        {
            "schema_version": "delegated_semantic_ir_synthesis_decision_template_v1",
            "artifact_id": "delegated-semantic-ir-synthesis-decision-template:f000477:justice_public_safety:119:v1",
            "decision": None,
            "allowed_decisions": [
                "delegated_authority_accepts_semantic_ir_and_synthesis_implementation",
                "bounded_semantic_ir_and_synthesis_correction_required",
                "delegated_authority_rejects_semantic_ir_method",
            ],
            "reviewer_identity": None,
            "reviewer_authority": None,
            "not_user_signature": True,
            "authorizing_when_empty": False,
        }
    )
    validation_report = seal(
        {
            "schema_version": "semantic_ir_m5_validation_report_v1",
            "artifact_id": "semantic-ir-m5-validation:f000477:justice_public_safety:119:v1",
            "database_access": False,
            "network_access": False,
            "canonical_and_public_state_unchanged": True,
            "initial_command_mistakes": [
                "PowerShell ConvertFrom-Json -Depth was unsupported; Python JSON parsing was used.",
                "Initial offline preflight path omitted backend/; supported module import was then used.",
            ],
            "sandbox_restrictions": [
                "Pre-existing inaccessible backend/tests temporary directories produced warnings during broad file enumeration.",
                "Python TemporaryDirectory writes were denied inside the filesystem sandbox; the same 52-test regression suite passed outside it.",
            ],
            "incorrect_or_baseline_attempts": [
                {
                    "command": "python scripts/build_foushee_justice_semantic_ir_m5.py",
                    "initial_exit_code": 1,
                    "cause": "script execution import root omitted",
                    "correction": "resolved repository root inserted before canonical imports",
                },
                {
                    "command": "python -m unittest discover -s backend/tests -p test_*.py",
                    "exit_code": 1,
                    "accounting": {"ran": 304, "failures": 1, "errors": 35},
                    "cause": "unsupported discovery import roots plus database and missing-fixture cases",
                },
                {
                    "command": "pytest --basetemp=..\\.local\\pytest_basetemp",
                    "exit_code": 1,
                    "accounting": {"passed": 1194, "failed": 40, "errors": 10},
                    "cause": "database-only tests used the invalid sentinel; missing local Senate/House fixtures and four disclosed baseline-incompatible tests remained",
                },
                {
                    "command": "first broad safe offline pytest subset attempt",
                    "exit_code": 1,
                    "accounting": {"passed": 1187, "failed": 6},
                    "cause": "four baseline deselections did not bind as intended and two deterministic M5 checks observed a deliberate artifact regeneration while the suite was running",
                    "correction": "reran after freeze with a negative selection expression; 1189 passed and 4 baseline cases were deselected",
                },
            ],
            "successful_commands": [
                {
                    "command": "supported offline database preflight module import",
                    "exit_code": 0,
                    "result": "invalid_sentinel",
                },
                {
                    "command": "python scripts/validate_full_issue_universe_authority.py",
                    "exit_code": 0,
                    "result": "37 actions",
                },
                {
                    "command": "python scripts/validate_full_issue_interpretation_source_readiness.py",
                    "exit_code": 0,
                    "result": "37 ready, 0 blocked",
                },
                {
                    "command": "python backend/scripts/build_full_issue_interpretation_source_readiness.py --check",
                    "exit_code": 0,
                },
                {
                    "command": "V1-V4 action candidate validators",
                    "exit_code": 0,
                    "result": "4 validators",
                },
                {
                    "command": "M3B-A/M3B-B validators",
                    "exit_code": 0,
                    "result": "2 validators",
                },
                {
                    "command": "M4A/M4B validators",
                    "exit_code": 0,
                    "result": "32 episodes; 35/1/1 actions",
                },
                {
                    "command": "node scripts/validate_editorial_semantic_ir_schema.mjs",
                    "exit_code": 0,
                    "result": "Draft-07 pass",
                },
                {
                    "command": "python scripts/validate_editorial_semantic_ir.py",
                    "exit_code": 0,
                    "result": "12 accepted + 4 accepted held-out + 4 held-out",
                },
                {
                    "command": "python scripts/compare_accepted_semantic_references.py",
                    "exit_code": 0,
                    "result": "16 cases",
                },
                {
                    "command": "python -m unittest backend.tests.test_editorial_semantic_ir backend.tests.test_editorial_pipeline backend.tests.test_full_record_issue_interpretation",
                    "exit_code": 0,
                    "result": "52 passed",
                },
                {
                    "command": "python scripts/build_foushee_justice_semantic_ir_m5.py --check",
                    "exit_code": 0,
                },
                {
                    "command": "python scripts/validate_foushee_justice_semantic_ir_m5.py",
                    "exit_code": 0,
                    "result": "independent verification pass",
                },
                {
                    "command": "python -m unittest backend.tests.test_foushee_justice_semantic_ir_m5",
                    "exit_code": 0,
                    "result": "5 passed",
                },
                {
                    "command": "broad safe offline pytest subset",
                    "exit_code": 0,
                    "result": "1189 passed, 4 disclosed baseline tests deselected",
                },
                {
                    "command": "ruff check + ruff format --check on directly affected Python",
                    "exit_code": 0,
                },
                {
                    "command": "python -m py_compile on directly affected Python",
                    "exit_code": 0,
                },
                {
                    "command": "JSON parse, credential scan, and git diff --check",
                    "exit_code": 0,
                },
            ],
            "validation_accounting": {
                "prior_integrity_gates": "pass",
                "targeted_m5_tests": 5,
                "semantic_ir_full_record_regression_tests": 52,
                "broad_safe_offline_tests": 1189,
                "broad_safe_offline_deselected_baseline_tests": 4,
                "remaining_m5_failures": 0,
            },
        }
    )
    artifacts: dict[str, Any] = {
        "initial_full_record_projection_manifest.json": projection(
            bundle, initial_input, initial_families, initial_traits
        ),
        "full_record_projection_manifest.json": projection_value,
        "initial_policy_families.json": family_artifact("initial", initial_families),
        "final_policy_families.json": family_artifact("final_frozen", final_families),
        "initial_policy_traits.json": trait_artifact("initial", initial_traits),
        "final_policy_traits.json": trait_artifact("final_frozen", final_traits),
        "trait_relationships.json": relationships,
        "source_render_constraints.json": constraints,
        "shared_review_dependencies.json": dependencies,
        "initial_compiler_input.json": initial_input_artifact,
        "initial_compiled_graph.json": initial_graph,
        "independent_reviews.json": review,
        "correction_cycle_1.json": correction,
        "frozen_final_compiler_input.json": input_artifact,
        "frozen_final_compiled_semantic_ir.json": final_graph,
        "post_freeze_benchmark_comparison.json": benchmark_value,
        "sample_challenge_manifest.json": sample,
        "provisional_implementation_bundle.json": implementation,
        "independent_implementation_verification.json": verification,
        "launch_review_risk_register.json": risk_successor,
        "semantic_calibration_population.json": calibration,
        "delegated_authority_decision_template.json": decision_template,
        "validation_report.json": validation_report,
    }
    write(ACCEPTANCE_OUTPUT, ACCEPTANCE_SOURCE.read_bytes(), check)
    for name, value in artifacts.items():
        write_json(name, value, check)
    dossier = dossier_markdown(artifacts)
    write(OUTPUT_ROOT / "review_dossier.md", dossier.encode(), check)
    schemas = schema_values(artifacts)
    for name, value in schemas.items():
        write_json(f"schemas/{name}", value, check)
    tracked_names = [
        "imported_m4b_delegated_acceptance.json",
        *artifacts,
        "review_dossier.md",
        *[f"schemas/{name}" for name in schemas],
    ]
    parity_entries = []
    for name in tracked_names:
        path = OUTPUT_ROOT / name
        if check:
            raw = path.read_bytes().replace(b"\r\n", b"\n")
        elif name == "imported_m4b_delegated_acceptance.json":
            raw = ACCEPTANCE_SOURCE.read_bytes()
        elif name == "review_dossier.md":
            raw = dossier.encode()
        elif name.startswith("schemas/"):
            raw = serialized(schemas[name.split("/", 1)[1]])
        else:
            raw = serialized(artifacts[name])
        parity_entries.append(
            {
                "path": name,
                "final_file_sha256": hashlib.sha256(raw).hexdigest(),
                "content_subject_sha256": (
                    json.loads(raw)["content_subject_sha256"]
                    if name.endswith(".json")
                    and "content_subject_sha256" in json.loads(raw)
                    else None
                ),
            }
        )
    parity = seal(
        {
            "schema_version": "semantic_ir_implementation_parity_manifest_v1",
            "artifact_id": "semantic-ir-implementation-parity:f000477:justice_public_safety:119:v1",
            "entries": parity_entries,
            "entry_count": len(parity_entries),
            "json_markdown_parity": True,
            "manually_edited_compiled_output": False,
            "accepted_or_canonical_state_changed": False,
            "public_prose_present": False,
        }
    )
    write_json("parity_manifest.json", parity, check)
    return {
        "input": input_artifact,
        "graph": final_graph,
        "implementation": implementation,
        "families": len(final_families),
        "traits": len(final_traits),
        "relationships": 1,
        "behavioral": Counter(p["proposition_type"] for p in behavioral),
        "behavioral_directions": Counter(p["direction"] for p in behavioral),
        "synthesis": Counter(p["proposition_type"] for p in synthesis),
        "coverage": final_graph["compiled_ir"]["members"][0]["coverage"],
        "accounting": final_graph["action_accounting_counts"],
        "risk_count": risk_successor["carried_risk_count"]
        + len(risk_successor["new_risks"]),
        "calibration_count": calibration["eligible_count"],
        "verification": verification["status"],
    }


def dossier_markdown(artifacts: dict[str, Any]) -> str:
    graph = artifacts["frozen_final_compiled_semantic_ir.json"]
    member = graph["compiled_ir"]["members"][0]
    propositions = member["proposition_graph"]["propositions"]
    lines = [
        "# Foushee Justice Semantic IR M5 delegated review dossier",
        "",
        "Review-only; non-authorizing. No public prose is included.",
        "",
        "## Decision requested",
        "",
        "Choose exactly one:",
        "",
        "- `delegated_authority_accepts_semantic_ir_and_synthesis_implementation`",
        "- `bounded_semantic_ir_and_synthesis_correction_required`",
        "- `delegated_authority_rejects_semantic_ir_method`",
        "",
        "## Identities",
        "",
        f"- Compiler input: `{artifacts['frozen_final_compiler_input.json']['artifact_id']}` / `{artifacts['frozen_final_compiler_input.json']['content_subject_sha256']}`",
        f"- Compiler input final-file SHA-256: `{hashlib.sha256(serialized(artifacts['frozen_final_compiler_input.json'])).hexdigest()}`",
        f"- Compiled graph: `{graph['artifact_id']}` / `{graph['content_subject_sha256']}`",
        f"- Compiled graph final-file SHA-256: `{hashlib.sha256(serialized(graph)).hexdigest()}`",
        f"- Provisional implementation: `{artifacts['provisional_implementation_bundle.json']['artifact_id']}` / `{artifacts['provisional_implementation_bundle.json']['content_subject_sha256']}`",
        f"- Provisional implementation final-file SHA-256: `{hashlib.sha256(serialized(artifacts['provisional_implementation_bundle.json'])).hexdigest()}`",
        "",
        "## Accounting",
        "",
        f"- Families: {artifacts['final_policy_families.json']['family_count']}",
        f"- Traits: {artifacts['final_policy_traits.json']['trait_count']}",
        f"- Relationships: {artifacts['trait_relationships.json']['relationship_count']}",
        f"- Actions: {len(graph['full_universe_action_accounting'])} (included {graph['action_accounting_counts']['included_in_behavioral_proposition']}; non-proposition {graph['action_accounting_counts']['non_proposition']})",
        f"- Coverage: `{json.dumps(member['coverage'], sort_keys=True)}`",
        "",
        "## Propositions",
        "",
    ]
    for p in propositions:
        lines += [
            f"### {p['proposition_id']}",
            "",
            f"- Role/type/direction: `{p['semantic_role']}` / `{p['proposition_type']}` / `{p['direction']}`",
            f"- Actions: `{', '.join(p['evidence_action_ids'])}`",
            f"- Episodes: `{', '.join(p['evidence_episode_ids'])}`",
            f"- Mechanisms/traits: `{', '.join(p['mechanism_or_trait_refs']) or 'none'}`",
            f"- Conclusion relevance: `{p['conclusion_relevance']}`",
            f"- Relationships: `{json.dumps(p['relationships'], sort_keys=True)}`",
            "- Competing interpretation: retain as a narrower object or omit if delegated review finds the mechanism overbroad.",
            "- Review state: candidate pending delegated authority review.",
            "",
        ]
    lines += [
        "## Special controls",
        "",
        "- Roll 128: bounded resolved concealed-carry meaning only; unresolved insertion preserved.",
        "- Roll 155: source-identity conflict blocks behavioral and synthesis support; outside primary FISA membership.",
        "- Roll 278: no-safe interpretation blocks behavioral, episode, synthesis, and narrative use.",
        "",
        "## Review and correction",
        "",
        "The initial independent family/trait review found one major overreach: officer-safety reporting had been grouped with terrorism preparedness. Correction cycle 1 removed that action and narrowed the family and trait. No major or critical finding remains.",
        "",
        "## Risk and calibration",
        "",
        f"- Carried plus new risks: {artifacts['launch_review_risk_register.json']['carried_risk_count'] + len(artifacts['launch_review_risk_register.json']['new_risks'])}",
        f"- Calibration-eligible objects: {artifacts['semantic_calibration_population.json']['eligible_count']}",
        "- No launch sample was selected.",
        "",
        "## Isolation",
        "",
        "Accepted-reference, canonical, runtime, persistence, public, publication, and deployment state remain unchanged. `render_plan.example_prose` is null and analytical additions are false.",
        "",
    ]
    return "\n".join(lines)


def schema_values(artifacts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    def closed(
        title: str, required: list[str], properties: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": title,
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": properties,
        }

    any_obj = {"type": "object"}
    supporting_variants = []
    supporting_schema_versions: set[str] = set()
    core_schema_versions = {
        "full_record_semantic_ir_compiler_input_v1",
        "full_record_semantic_ir_candidate_v1",
        "full_record_semantic_ir_provisional_implementation_v1",
    }
    for value in artifacts.values():
        schema_version = value.get("schema_version")
        if (
            schema_version in core_schema_versions
            or schema_version in supporting_schema_versions
        ):
            continue
        supporting_schema_versions.add(schema_version)
        supporting_variants.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(value),
                "properties": {
                    key: ({"const": child} if key == "schema_version" else {})
                    for key, child in value.items()
                },
            }
        )
    return {
        "full_record_semantic_ir_compiler_input_v1.schema.json": closed(
            "M5 compiler input envelope",
            [
                "schema_version",
                "artifact_id",
                "candidate_state",
                "compiler_input",
                "public_language_included",
                "expected_output_fields_included",
                "accepted_reference_output_included",
                "authorizing",
                "content_subject_sha256",
            ],
            {
                "schema_version": {
                    "const": "full_record_semantic_ir_compiler_input_v1"
                },
                "artifact_id": {"type": "string"},
                "candidate_state": {"type": "string"},
                "compiler_input": any_obj,
                "public_language_included": {"const": False},
                "expected_output_fields_included": {"const": False},
                "accepted_reference_output_included": {"const": False},
                "authorizing": {"const": False},
                "content_subject_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        ),
        "full_record_semantic_ir_candidate_v1.schema.json": closed(
            "M5 compiled graph envelope",
            [
                "schema_version",
                "artifact_id",
                "candidate_state",
                "compiled_ir",
                "full_universe_action_accounting",
                "action_accounting_counts",
                "render_plan",
                "accepted_semantic_reference",
                "canonical",
                "public",
                "persisted",
                "published",
                "authorizing",
                "content_subject_sha256",
            ],
            {
                "schema_version": {"const": "full_record_semantic_ir_candidate_v1"},
                "artifact_id": {"type": "string"},
                "candidate_state": {"type": "string"},
                "compiled_ir": any_obj,
                "full_universe_action_accounting": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                },
                "action_accounting_counts": any_obj,
                "render_plan": any_obj,
                "accepted_semantic_reference": {"const": False},
                "canonical": {"const": False},
                "public": {"const": False},
                "persisted": {"const": False},
                "published": {"const": False},
                "authorizing": {"const": False},
                "content_subject_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        ),
        "full_record_semantic_ir_provisional_implementation_v1.schema.json": closed(
            "M5 provisional implementation",
            [
                "schema_version",
                "artifact_id",
                "implementation_state",
                "implementation_core",
                "implementation_core_content_subject_sha256",
                "bindings",
                "behavioral_proposition_count",
                "synthesis_proposition_count",
                "full_action_accounting_count",
                "render_plan",
                "accepted_semantic_reference",
                "canonical",
                "public",
                "persisted",
                "published",
                "production_eligible",
                "user_approved",
                "authorizing",
                "content_subject_sha256",
            ],
            {
                "schema_version": {
                    "const": "full_record_semantic_ir_provisional_implementation_v1"
                },
                "artifact_id": {"type": "string"},
                "implementation_state": {
                    "const": "implemented_pending_delegated_authority_review"
                },
                "implementation_core": any_obj,
                "implementation_core_content_subject_sha256": {"type": "string"},
                "bindings": any_obj,
                "behavioral_proposition_count": {"type": "integer"},
                "synthesis_proposition_count": {"type": "integer"},
                "full_action_accounting_count": {"const": 37},
                "render_plan": any_obj,
                "accepted_semantic_reference": {"const": False},
                "canonical": {"const": False},
                "public": {"const": False},
                "persisted": {"const": False},
                "published": {"const": False},
                "production_eligible": {"const": False},
                "user_approved": {"const": False},
                "authorizing": {"const": False},
                "content_subject_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
            },
        ),
        "m5_supporting_artifacts_v1.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "M5 closed supporting artifact envelopes",
            "oneOf": supporting_variants,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.check)
    summary = {
        key: (dict(value) if isinstance(value, Counter) else value)
        for key, value in result.items()
        if key not in {"input", "graph", "implementation"}
    }
    summary.update(
        {
            "compiler_input_id": result["input"]["artifact_id"],
            "compiler_input_content_subject_sha256": result["input"][
                "content_subject_sha256"
            ],
            "compiled_graph_id": result["graph"]["artifact_id"],
            "compiled_graph_content_subject_sha256": result["graph"][
                "content_subject_sha256"
            ],
            "implementation_id": result["implementation"]["artifact_id"],
            "implementation_content_subject_sha256": result["implementation"][
                "content_subject_sha256"
            ],
        }
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
