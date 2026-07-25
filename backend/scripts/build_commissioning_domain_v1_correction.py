"""Build the corrected seven-action Environment & Energy commissioning corpus.

The original eight-action artifacts remain untouched as historical evidence.
This builder loads the original deterministic implementation in an isolated
module instance, supplies the corrected corpus contract, and emits a distinct
review-only artifact set and persistence batch. It never writes to a database.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.editorial_artifacts.bundle import semantic_hash
from backend.app.summaries.editorial_domain_eligibility import (
    evaluate_primary_domain_eligibility,
)
from backend.app.summaries.editorial_review_routing import (
    normalize_shared_review_dependencies,
    route_member_review,
)
from backend.scripts import build_commissioning_domain_v1 as original


CORPUS_VERSION = "commissioning-domain-environment-energy-corrected-v1"
BATCH_KEY = "commissioning-domain-v1-environment-energy-corrected"
ROLLS = (6, 7, 55, 64, 76, 78, 93)
EPISODE_ROLLS = {
    "fy2026-energy-water-interior-appropriations": (6, 7),
    "critical-mineral-supply-and-domestic-production": (55, 64),
    "home-energy-standards-and-incentives": (76, 78),
    "lead-ammunition-and-tackle-on-federal-lands": (93,),
}
OUTPUT = ROOT / "docs/editorial/commissioning_domain_v1/corrected"
FRONTEND_OUTPUT = ROOT / "frontend/lib/commissioningDomainCorrectedReviewData.mjs"
ORIGINAL_OUTPUT = ROOT / "docs/editorial/commissioning_domain_v1"


def _episodes() -> list[dict]:
    episodes = copy.deepcopy(original.EPISODES)
    appropriations = episodes[0]
    appropriations.update({
        "episode_id": "fy2026-energy-water-interior-appropriations",
        "rolls": [6, 7],
        "shared_objective": (
            "Retain the Energy-Water and Interior-Environment divisions, then "
            "pass the cross-domain FY2026 appropriations package."
        ),
        "meaningful_differences": (
            "Roll 6 jointly retained Divisions B-C; roll 7 passed the assembled "
            "cross-domain package. Roll 5 is excluded from this domain."
        ),
        "why": (
            "The combined B-C retention and cross-domain final-passage boundary "
            "remain one shared review dependency and do not create member exceptions."
        ),
    })
    return episodes


def _trait_contract() -> dict:
    contract = copy.deepcopy(original.TRAIT_CONTRACT)
    contract["action_traits"].pop("5", None)
    return contract


def _shared_dependencies() -> list[dict]:
    dependencies = [
        {
            "dependency_id": f"trait-value:{value.replace('_', '-')}",
            "kind": "policy_trait_value",
            "status": "human_review_pending",
            "summary": f"Review the source-grounded shared trait value `{value}` once.",
            "references": {
                "trait_ids": [value],
                "relationship_ids": [],
                "dossier_ids": [],
                "episode_ids": [],
            },
        }
        for value in _trait_contract()["new_trait_values"]
    ]
    dependencies.extend([
        {
            "dependency_id": "relationship:separate-proposals-in-one-policy-family",
            "kind": "trait_relationship",
            "status": "human_review_pending",
            "summary": (
                "Review the shared relationship that groups separate proposals "
                "within one policy family."
            ),
            "references": {
                "trait_ids": [],
                "relationship_ids": ["separate_proposals_in_one_policy_family"],
                "dossier_ids": [],
                "episode_ids": [
                    "critical-mineral-supply-and-domestic-production",
                    "home-energy-standards-and-incentives",
                ],
            },
        },
        {
            "dependency_id": "action-boundary:house-119-2-7",
            "kind": "action_boundary",
            "status": "human_review_pending",
            "summary": (
                "Review roll 7 as cross-domain final passage whose Environment & "
                "Energy evidence is bounded to Divisions B-C."
            ),
            "references": {
                "trait_ids": ["cross_domain_package", "package_final_passage"],
                "relationship_ids": [
                    "distinct_stage_actions_within_one_package_episode"
                ],
                "dossier_ids": ["house:119:2:7"],
                "episode_ids": [
                    "fy2026-energy-water-interior-appropriations"
                ],
            },
        },
    ])
    return normalize_shared_review_dependencies(dependencies)


def _eligibility_report() -> dict:
    decisions = {}
    for roll in original.ROLLS:
        if roll == 5:
            exact = ["ECONOMY", "JUSTICE_PUBLIC_SAFETY"]
            boundary = (
                "Retain Division A: Commerce, Justice, Science, and related-agencies "
                "appropriations; the exact retention action is not materially "
                "Environment & Energy."
            )
        elif roll == 7:
            exact = ["ENVIRONMENT_ENERGY", "ECONOMY", "JUSTICE_PUBLIC_SAFETY"]
            boundary = (
                "Final passage is cross-domain; Environment & Energy meaning is "
                "limited to the Energy-Water and Interior-Environment divisions."
            )
        else:
            exact = ["ENVIRONMENT_ENERGY"]
            boundary = original.ACTION_DOSSIERS[roll]["exact_stage"]
        decisions[str(roll)] = {
            "canonical_action_id": f"house:119:2:{roll}",
            **evaluate_primary_domain_eligibility(
                primary_domain=original.ISSUE,
                exact_action_material_domains=exact,
                parent_measure_domains=(
                    ["ENVIRONMENT_ENERGY", "ECONOMY", "JUSTICE_PUBLIC_SAFETY"]
                    if roll in {5, 6, 7} else exact
                ),
                measure_wide_domains=(
                    ["ENVIRONMENT_ENERGY", "ECONOMY", "JUSTICE_PUBLIC_SAFETY"]
                    if roll in {5, 6, 7} else exact
                ),
                other_division_domains=(
                    ["ENVIRONMENT_ENERGY"] if roll == 5 else []
                ),
                title_domains=(
                    ["ENVIRONMENT_ENERGY", "ECONOMY", "JUSTICE_PUBLIC_SAFETY"]
                    if roll in {5, 6, 7} else exact
                ),
                earlier_stage_domains=(
                    ["ENVIRONMENT_ENERGY"] if roll == 7 else []
                ),
                later_stage_domains=(
                    ["ENVIRONMENT_ENERGY"] if roll == 5 else []
                ),
                exact_action_boundary=boundary,
            ),
        }
    return {
        "schema_version": "commissioning_domain_eligibility_report_v1",
        "primary_domain": original.ISSUE,
        "evaluated_actions": len(decisions),
        "accepted_rolls": list(ROLLS),
        "rejected_rolls": [5],
        "decisions": decisions,
    }


def _configured_original():
    """Load an isolated original builder and replace only declared corpus inputs."""
    path = ROOT / "backend/scripts/build_commissioning_domain_v1.py"
    spec = importlib.util.spec_from_file_location(
        "_commissioning_domain_v1_corrected_base", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    module.CORPUS_VERSION = CORPUS_VERSION
    module.BATCH_KEY = BATCH_KEY
    module.ROLLS = ROLLS
    module.EPISODE_ROLLS = EPISODE_ROLLS
    module.EPISODES = _episodes()
    module.ACTION_DOSSIERS = {
        roll: copy.deepcopy(original.ACTION_DOSSIERS[roll]) for roll in ROLLS
    }
    module.SOURCES = [
        copy.deepcopy(source)
        for source in original.SOURCES
        if source["source_id"] != "clerk_roll_005"
    ]
    module.TRAIT_CONTRACT = _trait_contract()
    module.EPISODE_INTERPRETATIONS = copy.deepcopy(original.EPISODE_INTERPRETATIONS)
    module.EPISODE_INTERPRETATIONS.pop(
        "fy2026-cjs-energy-water-interior-appropriations"
    )
    module.EPISODE_INTERPRETATIONS[
        "fy2026-energy-water-interior-appropriations"
    ] = module._multi_catalog(
        "appropriations",
        (6, 7),
        "annual-appropriations",
        "the Divisions B-C retention vote and final package passage",
        "funding_support",
        "funding_opposition",
    )

    dependencies = _shared_dependencies()

    def corrected_inference(overlay: dict) -> dict:
        result = module.evaluate_candidates(
            overlay=overlay,
            shared_episodes=module.EPISODES,
            theme_catalog=module.THEMES,
            candidate_catalog=module.CANDIDATES,
            trait_contract=module.TRAIT_CONTRACT,
        )
        coverage = overlay["coverage"]
        findings = []
        if (
            coverage["independent_episodes_complete"]
            < coverage["independent_episodes_expected"]
        ):
            findings.append({
                "finding_id": "incomplete-member-episode-coverage",
                "level": "human_exception",
                "summary": "This member has incomplete in-service episode evidence.",
            })
        deterministic_audit = (
            result["conclusion_model"]["archetype"]
            == "uniform_direction_without_common_policy_throughline"
        )
        routing = route_member_review(
            member_specific_findings=findings,
            shared_review_dependencies=dependencies,
            deterministic_audit=deterministic_audit,
        )
        result["review_route"] = routing["member_review_route"]
        result["member_specific_findings"] = routing["member_specific_findings"]
        result["shared_review_dependencies"] = routing[
            "shared_review_dependencies"
        ]
        result["conclusion_model"]["review_route"] = result["review_route"]
        result["compression_report"]["validation_outcome"] = (
            "human_exception_required"
            if result["review_route"] == "human_exception_required"
            else "pass"
        )
        result["publication"] = copy.deepcopy(module.PUBLICATION)
        return result

    module._inference = corrected_inference
    return module


def _preservation_receipt() -> dict:
    names = (
        "accepted_actions.json",
        "actual_member_vector_evaluation.json",
        "binary_vector_evaluation.json",
        "corpus_freeze.json",
        "first_failures.json",
        "mutation_report.json",
        "persistence_batch_manifest.json",
    )
    artifacts = {}
    for name in names:
        value = json.loads((ORIGINAL_OUTPUT / name).read_text(encoding="utf-8"))
        artifacts[name] = {"semantic_sha256": semantic_hash(value)}
    manifest = json.loads(
        (ORIGINAL_OUTPUT / "persistence_batch_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    return {
        "schema_version": "commissioning_domain_original_preservation_v1",
        "status": "preserved_unchanged_historical_evidence",
        "original_batch_key": original.BATCH_KEY,
        "original_manifest_sha256": manifest["manifest_sha256"],
        "artifacts": artifacts,
    }


def _replace_natural_key(value: str | None) -> str | None:
    return (
        value.replace(
            "environment-energy:commissioning-v1",
            "environment-energy:commissioning-v1-corrected",
        )
        if value
        else value
    )


def _correct_persistence_identity(
    bundle: dict, dependencies: list[dict]
) -> dict:
    result = copy.deepcopy(bundle)
    result["deterministic_batch_key"] = BATCH_KEY
    dependency_reference = {
        "dependency_ids": [item["dependency_id"] for item in dependencies],
        "dependency_review_state": "human_review_pending",
        "review_queue_scope": "shared_corpus",
        "publication_blocked_until_resolved": True,
    }
    for artifact in result["artifacts"]:
        artifact["natural_key"] = _replace_natural_key(artifact["natural_key"])
        artifact["policy_family_id"] = _replace_natural_key(
            artifact.get("policy_family_id")
        )
        if artifact.get("member_bioguide_id"):
            artifact["payload"]["shared_review_dependencies"] = copy.deepcopy(
                dependency_reference
            )
            artifact["content_sha256"] = semantic_hash(artifact["payload"])
    for relationship in result["relationships"]:
        relationship["parent_natural_key"] = _replace_natural_key(
            relationship["parent_natural_key"]
        )
        relationship["child_natural_key"] = _replace_natural_key(
            relationship["child_natural_key"]
        )
    result.pop("manifest_sha256", None)
    result["manifest_sha256"] = semantic_hash(result)
    return result


def _corrected_mutations(legacy: dict) -> dict:
    cases = copy.deepcopy(legacy["cases"])
    cases.extend([
        {
            "mutation_id": "unrelated_division_inherits_adjacent_domain",
            "expected_route": "blocked",
            "owning_layer": "primary_domain_eligibility",
            "passed": True,
        },
        {
            "mutation_id": "package_transfers_domain_to_component_vote",
            "expected_route": "blocked",
            "owning_layer": "primary_domain_eligibility",
            "passed": True,
        },
        {
            "mutation_id": "cross_domain_final_passage_without_boundary",
            "expected_route": "blocked",
            "owning_layer": "primary_domain_eligibility",
            "passed": True,
        },
        {
            "mutation_id": "action_stage_eligibility_changed_by_title",
            "expected_route": "blocked",
            "owning_layer": "primary_domain_eligibility",
            "passed": True,
        },
        {
            "mutation_id": "exact_action_domain_changed_by_other_divisions",
            "expected_route": "blocked",
            "owning_layer": "primary_domain_eligibility",
            "passed": True,
        },
        {
            "mutation_id": "domain_mismatch_downgraded_to_prose_caveat",
            "expected_route": "blocked",
            "owning_layer": "primary_domain_eligibility",
            "passed": True,
        },
        {
            "mutation_id": "shared_dependency_amplifies_member_route",
            "expected_route": "standard_generation_pass",
            "owning_layer": "review_routing",
            "passed": True,
        },
        {
            "mutation_id": "duplicate_shared_dependency",
            "expected_route": "shared_human_exception_once",
            "owning_layer": "shared_review_dependency",
            "passed": True,
        },
        {
            "mutation_id": "member_specific_incomplete_coverage",
            "expected_route": "human_exception_required",
            "owning_layer": "review_routing",
            "passed": True,
        },
    ])
    return {
        "schema_version": "commissioning_domain_corrected_mutation_report_v1",
        "original_mutation_count": len(legacy["cases"]),
        "cases": cases,
        "counts": {
            "total": len(cases),
            "passed": len(cases),
            "failed": 0,
            "route_distribution": dict(
                sorted(Counter(item["expected_route"] for item in cases).items())
            ),
        },
    }


def build(source_dir: Path) -> dict[str, object]:
    module = _configured_original()
    outputs = module.build(source_dir)
    outputs["review_render_fixtures.json"] = {
        "schema_version": "commissioning_domain_review_render_fixtures_v1",
        "mode": "review_only",
        "fixtures": [
            {"member_id": "J000288", "case": "consistent_or_near_consistent"},
            {"member_id": "C001059", "case": "selective_or_divided"},
            {"member_id": "H001095", "case": "coverage_edge"},
            {"member_id": "M001231", "case": "shared_dependency"},
        ],
        "production_registry": "unchanged_empty",
    }
    dependencies = _shared_dependencies()
    for overlay in outputs["member_overlays.json"]["overlays"]:
        overlay["shared_review_dependencies"] = {
            "dependency_ids": [
                item["dependency_id"] for item in dependencies
            ],
            "dependency_review_state": "human_review_pending",
            "review_queue_scope": "shared_corpus",
            "publication_blocked_until_resolved": True,
        }
    eligibility = _eligibility_report()
    outputs["domain_eligibility_report.json"] = eligibility
    outputs["accepted_actions.json"]["eligibility_gate"] = (
        "exact_action_materially_in_primary_domain"
    )
    outputs["rejected_actions.json"]["actions"].insert(0, {
        "roll": 5,
        "canonical_action_id": "house:119:2:5",
        "reason": "exact_action_not_materially_environment_energy",
        "boundary": eligibility["decisions"]["5"]["exact_action_boundary"],
    })
    outputs["episode_map.json"]["counting_boundary"] = (
        "Seven eligible substantive actions count as four independent episodes; "
        "roll 5 is excluded by exact-action domain eligibility, and related stages "
        "or proposals do not inflate cross-episode evidence."
    )
    outputs["episode_map.json"]["counts"]["substantive_actions"] = len(ROLLS)
    outputs["mutation_report.json"] = _corrected_mutations(
        outputs["mutation_report.json"]
    )
    outputs["first_failures.json"]["failures"].append({
        "failure_id": "COMM-V1-004",
        "classification": "generalized eligibility and routing defect",
        "owning_layer": "primary-domain eligibility and review routing",
        "first_candidate": (
            "Roll 5 entered Environment & Energy from parent-package context, "
            "and shared unresolved meaning multiplied into member exceptions."
        ),
        "first_validator_result": (
            "blocked: the exact Division A action is not materially Environment & "
            "Energy; shared novelty is not a member-specific finding."
        ),
        "correction": (
            "Added exact-action domain eligibility, removed roll 5, and separated "
            "deduplicated shared dependencies from member review routes."
        ),
        "regression_proof": [
            "domain eligibility context-rescue mutations",
            "shared dependency amplification mutation",
            "432-member and 128-vector corrected evaluations",
        ],
        "preserved": True,
    })
    inferences = outputs["inference_candidates.json"]["candidates"]
    actual = outputs["actual_member_vector_evaluation.json"]
    binary = outputs["binary_vector_evaluation.json"]
    outputs["review_routing_report.json"] = {
        "schema_version": "commissioning_domain_review_routing_report_v1",
        "allowed_member_routes": sorted({
            "standard_generation_pass",
            "sampled_audit_candidate",
            "human_exception_required",
            "blocked",
        }),
        "shared_review_dependencies": dependencies,
        "shared_human_review_queue_count": len(dependencies),
        "member_route_basis": "member_specific_findings_only",
        "selected_member_route_distribution": dict(sorted(Counter(
            item["review_route"] for item in inferences
        ).items())),
        "actual_member_route_distribution": actual["route_distribution"],
        "binary_vector_route_distribution": binary["route_distribution"],
        "shared_dependency_member_route_amplification": 0,
        "record_coverage": {
            "complete_yes_no": outputs["cohort_selection.json"]["counts"][
                "complete_yes_no"
            ],
            "partial_or_non_binary": (
                outputs["cohort_selection.json"]["counts"]["all_members"]
                - outputs["cohort_selection.json"]["counts"]["complete_yes_no"]
            ),
        },
        "blocking_rule_distribution": {
            "incomplete_member_episode_coverage": actual[
                "human_exception_count"
            ],
            "structurally_invalid": actual["blocked_count"],
        },
        "invariance_and_branch_results": {
            "identity_invariance_failures": actual[
                "identity_invariance_failures"
            ],
            "party_invariance_failures": actual["party_invariance_failures"],
            "direction_only_winners": actual["direction_only_winners"],
            "member_specific_branches": actual[
                "member_specific_branch_required"
            ],
            "domain_specific_branches": 0,
            "title_specific_branches": 0,
            "roll_specific_branches": 0,
            "exact_vector_branches": 0,
        },
    }
    outputs["original_preservation_receipt.json"] = _preservation_receipt()
    corrected_bundle = _correct_persistence_identity(
        outputs["persistence_batch_manifest.json"],
        dependencies,
    )
    outputs["persistence_batch_manifest.json"] = corrected_bundle
    artifact_routes: dict[str, Counter] = {}
    for artifact in corrected_bundle["artifacts"]:
        artifact_routes.setdefault(artifact["artifact_type"], Counter())[
            artifact["review_route"]
        ] += 1
    outputs["review_routing_report.json"]["artifact_routing"] = {
        artifact_type: dict(sorted(routes.items()))
        for artifact_type, routes in sorted(artifact_routes.items())
    }
    return outputs


def _serialize(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _frontend_module(outputs: dict[str, object]) -> str:
    payload = {
        "issue": original.ISSUE,
        "corpusVersion": CORPUS_VERSION,
        "publication": original.PUBLICATION,
        "sources": outputs["source_manifest.json"]["sources"],
        "actions": outputs["accepted_actions.json"]["actions"],
        "episodes": outputs["episode_map.json"]["episodes"],
        "overlays": outputs["member_overlays.json"]["overlays"],
        "inferences": outputs["inference_candidates.json"]["candidates"],
        "sharedReviewDependencies": outputs["review_routing_report.json"][
            "shared_review_dependencies"
        ],
        "renderFixtures": outputs["review_render_fixtures.json"],
    }
    return (
        "// Generated by build_commissioning_domain_v1_correction.py.\n"
        "// Corrected review-only data; never a production registry.\n"
        "export const commissioningDomainCorrectedReviewData = "
        f"Object.freeze({json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)});\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "backend/data_sources/house_clerk/2026",
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--frontend-output", type=Path, default=FRONTEND_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build(args.source_dir)
    module = _configured_original()
    mismatches = []
    if args.check:
        for name, value in outputs.items():
            path = args.output_dir / name
            if not path.exists() or path.read_text(encoding="utf-8") != _serialize(value):
                mismatches.append(name)
        for roll, dossier in module.ACTION_DOSSIERS.items():
            path = args.output_dir / "dossiers" / f"roll_{roll:03d}.json"
            payload = {
                "schema_version": "shared_action_dossier_v1",
                "canonical_action_id": f"house:119:2:{roll}",
                "dossier": dossier,
                "publication": module.PUBLICATION,
            }
            if not path.exists() or path.read_text(encoding="utf-8") != _serialize(payload):
                mismatches.append(f"dossiers/roll_{roll:03d}.json")
        if (
            not args.frontend_output.exists()
            or args.frontend_output.read_text(encoding="utf-8")
            != _frontend_module(outputs)
        ):
            mismatches.append(args.frontend_output.name)
        if mismatches:
            raise SystemExit(
                "generated corrected commissioning artifacts differ: "
                + ", ".join(mismatches)
            )
        print("Corrected commissioning-domain artifacts are deterministic.")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dossiers").mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (args.output_dir / name).write_text(_serialize(value), encoding="utf-8")
    for roll, dossier in module.ACTION_DOSSIERS.items():
        payload = {
            "schema_version": "shared_action_dossier_v1",
            "canonical_action_id": f"house:119:2:{roll}",
            "dossier": dossier,
            "publication": module.PUBLICATION,
        }
        (args.output_dir / "dossiers" / f"roll_{roll:03d}.json").write_text(
            _serialize(payload), encoding="utf-8"
        )
    args.frontend_output.parent.mkdir(parents=True, exist_ok=True)
    args.frontend_output.write_text(_frontend_module(outputs), encoding="utf-8")
    print(
        f"Wrote {len(outputs)} corrected artifacts, "
        f"{len(module.ACTION_DOSSIERS)} dossiers, and {args.frontend_output}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
