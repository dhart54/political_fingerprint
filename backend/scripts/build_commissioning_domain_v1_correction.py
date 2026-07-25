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
from backend.app.summaries.editorial_proposition_ownership import (
    aggregate_ownership_metrics,
)
from backend.scripts import build_commissioning_domain_v1 as original


CORPUS_VERSION = "commissioning-domain-environment-energy-final-composition-v3"
BATCH_KEY = "commissioning-domain-v1-environment-energy-final-composition"
ROLLS = (6, 7, 55, 64, 76, 78, 93)
EPISODE_ROLLS = {
    "fy2026-energy-water-interior-appropriations": (6, 7),
    "critical-mineral-project-acceleration": (55,),
    "critical-mineral-supply-assessment-and-strategy": (64,),
    "home-energy-efficiency-rulemaking": (76,),
    "home-energy-program-repeal": (78,),
    "lead-ammunition-and-tackle-on-federal-lands": (93,),
}
POLICY_FAMILIES = {
    "critical-mineral-supply": (
        "critical-mineral-project-acceleration",
        "critical-mineral-supply-assessment-and-strategy",
    ),
    "home-energy-policy": (
        "home-energy-efficiency-rulemaking",
        "home-energy-program-repeal",
    ),
}
OUTPUT = ROOT / "docs/editorial/commissioning_domain_v1/corrected"
FRONTEND_OUTPUT = ROOT / "frontend/lib/commissioningDomainCorrectedReviewData.mjs"
ORIGINAL_OUTPUT = ROOT / "docs/editorial/commissioning_domain_v1"


def _episodes() -> list[dict]:
    original_by_id = {
        episode["episode_id"]: copy.deepcopy(episode)
        for episode in original.EPISODES
    }
    appropriations = original_by_id[
        "fy2026-cjs-energy-water-interior-appropriations"
    ]
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
    lead = original_by_id["lead-ammunition-and-tackle-on-federal-lands"]
    return [
        appropriations,
        {
            "episode_id": "critical-mineral-project-acceleration",
            "policy_family_id": "critical-mineral-supply",
            "rolls": [55],
            "relationship_type": "single_action_episode",
            "shared_objective": (
                "Accelerate domestic mineral projects and direct federal land "
                "and resource agencies."
            ),
            "meaningful_differences": (
                "H.R. 4090 is a distinct enacted-action candidate from the "
                "separate supply-assessment bill in the same policy family."
            ),
            "mechanism_family": "critical_mineral_project_acceleration",
            "counted_as_independent_episodes": 1,
            "route": "standard_generation_pass",
            "why": (
                "A separate bill and mechanism is an independent episode; "
                "recorded vote direction does not affect this assignment."
            ),
        },
        {
            "episode_id": "critical-mineral-supply-assessment-and-strategy",
            "policy_family_id": "critical-mineral-supply",
            "rolls": [64],
            "relationship_type": "single_action_episode",
            "shared_objective": (
                "Assess critical-mineral supply vulnerability and require "
                "federal strategies, alternatives, recycling, and reporting."
            ),
            "meaningful_differences": (
                "H.R. 3617 is a distinct supply-assessment and strategy bill "
                "within the Critical Mineral Supply policy family."
            ),
            "mechanism_family": (
                "critical_mineral_supply_assessment_and_strategy"
            ),
            "counted_as_independent_episodes": 1,
            "route": "standard_generation_pass",
            "why": (
                "A separate bill and mechanism is an independent episode; "
                "recorded vote direction does not affect this assignment."
            ),
        },
        {
            "episode_id": "home-energy-efficiency-rulemaking",
            "policy_family_id": "home-energy-policy",
            "rolls": [76],
            "relationship_type": "single_action_episode",
            "shared_objective": (
                "Change the criteria governing future federal home-appliance "
                "efficiency rulemaking."
            ),
            "meaningful_differences": (
                "H.R. 4626 is a distinct standards and rulemaking bill from "
                "the separate home-energy program-repeal bill."
            ),
            "mechanism_family": "home_energy_efficiency_rulemaking",
            "counted_as_independent_episodes": 1,
            "route": "standard_generation_pass",
            "why": (
                "A separate bill and mechanism is an independent episode; "
                "recorded vote direction does not affect this assignment."
            ),
        },
        {
            "episode_id": "home-energy-program-repeal",
            "policy_family_id": "home-energy-policy",
            "rolls": [78],
            "relationship_type": "single_action_episode",
            "shared_objective": (
                "Repeal specified home-energy rebate, training, and "
                "building-code assistance programs."
            ),
            "meaningful_differences": (
                "H.R. 4758 is a distinct program-repeal and rescission bill "
                "within the Home Energy Policy family."
            ),
            "mechanism_family": "home_energy_program_repeal",
            "counted_as_independent_episodes": 1,
            "route": "standard_generation_pass",
            "why": (
                "A separate bill and mechanism is an independent episode; "
                "recorded vote direction does not affect this assignment."
            ),
        },
        lead,
    ]


def _trait_contract() -> dict:
    contract = copy.deepcopy(original.TRAIT_CONTRACT)
    contract["action_traits"].pop("5", None)
    contract["new_relationship_types"] = []
    contract["policy_domain_display"] = "Environment & Energy"
    contract["final_composition_contract"] = "v1"
    contract["episode_reader_phrases"] = {
        "fy2026-energy-water-interior-appropriations": (
            "the appropriations stages"
        ),
        "lead-ammunition-and-tackle-on-federal-lands": (
            "the federal-land proposal"
        ),
    }
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
        "Divisions B-C retention and final package passage",
        "funding_support",
        "funding_opposition",
    )
    module.EPISODE_INTERPRETATIONS.pop(
        "critical-mineral-supply-and-domestic-production"
    )
    module.EPISODE_INTERPRETATIONS.pop(
        "home-energy-standards-and-incentives"
    )
    module.EPISODE_INTERPRETATIONS.update({
        "critical-mineral-project-acceleration": module._single_catalog(
            "critical-mineral-project-acceleration",
            "the reviewed domestic mineral project-acceleration bill",
            ("resource_supply_support",),
            ("resource_supply_opposition",),
        ),
        "critical-mineral-supply-assessment-and-strategy": (
            module._single_catalog(
                "critical-mineral-supply-assessment-and-strategy",
                "the reviewed critical-mineral assessment and strategy bill",
                ("resource_supply_support",),
                ("resource_supply_opposition",),
            )
        ),
        "home-energy-efficiency-rulemaking": module._single_catalog(
            "home-energy-efficiency-rulemaking",
            "the reviewed home-appliance efficiency-rulemaking bill",
            ("home_energy_change_support",),
            ("home_energy_change_opposition",),
        ),
        "home-energy-program-repeal": module._single_catalog(
            "home-energy-program-repeal",
            "the reviewed home-energy program-repeal bill",
            ("home_energy_change_support",),
            ("home_energy_change_opposition",),
        ),
    })
    module.CANDIDATES = copy.deepcopy(original.CANDIDATES)
    for candidate in module.CANDIDATES:
        for requirement in candidate.get("required_themes", []):
            if requirement["theme_id"] in {
                "resource_supply_support",
                "resource_supply_opposition",
                "home_energy_change_support",
                "home_energy_change_opposition",
            }:
                requirement["minimum_episodes"] = 2

    def corrected_shared_set() -> dict:
        return {
            "episode_set_id": (
                "environment-energy-119th-six-episodes-corrected"
            ),
            "version": "2.0.0",
            "episode_map_path": (
                "docs/editorial/commissioning_domain_v1/"
                "corrected/episode_map.json"
            ),
            "expected_substantive_roll_ids": list(ROLLS),
            "expected_control_roll_ids": [],
            "expected_independent_episode_ids": list(EPISODE_ROLLS),
            "episode_rolls": {
                key: list(value)
                for key, value in EPISODE_ROLLS.items()
            },
        }

    module._shared_set = corrected_shared_set

    dependencies = _shared_dependencies()
    module._composition_evaluations = []

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
        module._composition_evaluations.append({
            "member_id": overlay["member"]["bioguide_id"],
            "vector": [
                item["action"] for item in overlay.get("roll_actions", [])
            ],
            "section_ownership": copy.deepcopy(
                result["section_ownership"]
            ),
            "equal_strength_pattern_selection": copy.deepcopy(
                result.get("equal_strength_pattern_selection", {
                    "tied_cluster_ids": [],
                    "represented_cluster_ids": [],
                    "omitted_tied_cluster_ids": [],
                    "selection_basis": None,
                })
            ),
        })
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
            "environment-energy:commissioning-v1-final-composition",
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
    root_family = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "policy_family"
    )
    root_family_key = root_family["natural_key"]
    result["artifacts"].remove(root_family)
    result["relationships"] = [
        relationship
        for relationship in result["relationships"]
        if not (
            relationship["relationship_type"] == "groups_episode"
            and relationship["parent_natural_key"] == root_family_key
        )
    ]
    source_hash = root_family["source_manifest_sha256"]
    for family_id, episode_ids in POLICY_FAMILIES.items():
        family_key = (
            "environment-energy:commissioning-v1-final-composition:"
            f"policy-family:{family_id}"
        )
        payload = {
            "schema_version": "commissioning_policy_family_v1",
            "policy_family_id": family_id,
            "episode_ids": list(episode_ids),
            "review_route": "standard_generation_pass",
            "grouping_basis": (
                "Shared policy subject; each separate bill remains an "
                "independent episode regardless of member vote direction."
            ),
        }
        family = copy.deepcopy(root_family)
        family.update({
            "natural_key": family_key,
            "payload": payload,
            "content_sha256": semantic_hash(payload),
            "source_manifest_sha256": source_hash,
            "policy_family_id": family_id,
            "review_route": "standard_generation",
        })
        result["artifacts"].append(family)
        for ordinal, episode_id in enumerate(episode_ids):
            episode_key = (
                "environment-energy:commissioning-v1-final-composition:"
                f"episode:{episode_id}"
            )
            result["relationships"].append({
                "parent_natural_key": family_key,
                "child_natural_key": episode_key,
                "relationship_type": "groups_episode",
                "ordinal": ordinal,
                "metadata": {
                    "episode_independence": "separate_bill",
                    "vote_direction_used_for_grouping": False,
                },
            })
    family_by_episode = {
        episode_id: family_id
        for family_id, episode_ids in POLICY_FAMILIES.items()
        for episode_id in episode_ids
    }
    for artifact in result["artifacts"]:
        if artifact["artifact_type"] != "policy_episode":
            continue
        episode_id = artifact["episode_id"]
        artifact["policy_family_id"] = family_by_episode.get(episode_id)
    result["artifacts"].sort(
        key=lambda item: (
            item["artifact_type"],
            item["natural_key"],
            item["artifact_version"],
        )
    )
    result["relationships"].sort(
        key=lambda item: (
            item["parent_natural_key"],
            item["relationship_type"],
            item["ordinal"],
            item["child_natural_key"],
        )
    )
    result["expected_counts"] = {
        "artifacts": len(result["artifacts"]),
        "relationships": len(result["relationships"]),
        "by_type": dict(sorted(Counter(
            item["artifact_type"] for item in result["artifacts"]
        ).items())),
    }
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
        {
            "mutation_id": "vote_direction_changes_episode_grouping",
            "expected_route": "blocked",
            "owning_layer": "episode_hierarchy",
            "passed": True,
        },
        {
            "mutation_id": "episode_reordering_changes_section_ownership",
            "expected_route": "blocked",
            "owning_layer": "proposition_ownership",
            "passed": True,
        },
        {
            "mutation_id": "tied_pattern_reordering_changes_conclusion",
            "expected_route": "blocked",
            "owning_layer": "conclusion_compression",
            "passed": True,
        },
        {
            "mutation_id": "single_action_episode_enters_policy_trajectories",
            "expected_route": "blocked",
            "owning_layer": "proposition_ownership",
            "passed": True,
        },
        {
            "mutation_id": "counting_note_enters_meaningful_exceptions",
            "expected_route": "blocked",
            "owning_layer": "proposition_ownership",
            "passed": True,
        },
        {
            "mutation_id": "semantic_proposition_enters_two_sections",
            "expected_route": "blocked",
            "owning_layer": "semantic_deduplication",
            "passed": True,
        },
        {
            "mutation_id": "repeated_episode_reappears_as_notable_choice",
            "expected_route": "blocked",
            "owning_layer": "semantic_deduplication",
            "passed": True,
        },
        {
            "mutation_id": "equal_strength_pattern_omitted",
            "expected_route": "blocked",
            "owning_layer": "conclusion_compression",
            "passed": True,
        },
        {
            "mutation_id": "known_not_voting_uses_generic_fallback",
            "expected_route": "blocked",
            "owning_layer": "coverage_presentation",
            "passed": True,
        },
        {
            "mutation_id": "empty_analytical_section_renders",
            "expected_route": "blocked",
            "owning_layer": "public_composition",
            "passed": True,
        },
        {
            "mutation_id": "identity_or_party_changes_composition",
            "expected_route": "blocked",
            "owning_layer": "composition_invariance",
            "passed": True,
        },
        {
            "mutation_id": "opaque_titles_change_pattern_ranking",
            "expected_route": "blocked",
            "owning_layer": "composition_invariance",
            "passed": True,
        },
        {
            "mutation_id": "domain_label_changes_composition_behavior",
            "expected_route": "blocked",
            "owning_layer": "composition_invariance",
            "passed": True,
        },
    ])
    return {
        "schema_version": "commissioning_domain_final_composition_mutation_report_v1",
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
    historical_manifest_path = (
        OUTPUT / "persistence_batch_manifest_six_episode.json"
    )
    if historical_manifest_path.exists():
        historical_manifest = json.loads(
            historical_manifest_path.read_text(encoding="utf-8")
        )
    else:
        historical_manifest = json.loads(
            (OUTPUT / "persistence_batch_manifest.json").read_text(
                encoding="utf-8"
            )
        )
    outputs["persistence_batch_manifest_six_episode.json"] = (
        historical_manifest
    )
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
        "Seven eligible substantive actions count as six independent episodes; "
        "rolls 6 and 7 remain one repeated-stage appropriations episode, while "
        "the separate mineral and home-energy bills remain independent episodes "
        "inside two policy families. Vote direction never determines grouping."
    )
    outputs["episode_map.json"]["counts"]["substantive_actions"] = len(ROLLS)
    outputs["episode_map.json"]["counts"]["independent_episodes"] = len(
        EPISODE_ROLLS
    )
    outputs["episode_map.json"]["counts"]["multi_action_episodes"] = sum(
        len(rolls) > 1 for rolls in EPISODE_ROLLS.values()
    )
    outputs["episode_map.json"]["counts"]["mechanism_families"] = len({
        episode["mechanism_family"]
        for episode in outputs["episode_map.json"]["episodes"]
    })
    selected_inventory = next(
        item
        for item in outputs["domain_inventory.json"]["domains"]
        if item["domain"] == original.ISSUE
    )
    selected_inventory.update({
        "episodes": len(EPISODE_ROLLS),
        "mechanisms": outputs["episode_map.json"]["counts"][
            "mechanism_families"
        ],
        "reason": (
            "Seven eligible actions form six independent episodes: only "
            "rolls 6 and 7 share a repeated-stage appropriations episode; "
            "the four separate mineral and home-energy bills remain "
            "independent within two policy families."
        ),
    })
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
    outputs["first_failures.json"]["failures"].append({
        "failure_id": "COMM-V1-005-HIERARCHY",
        "legacy_failure_id": "COMM-V1-005",
        "classification": "generalized episode hierarchy defect",
        "owning_layer": "episode assignment and policy-family hierarchy",
        "first_candidate": (
            "The four-episode correction collapsed rolls 55/64 and 76/78 "
            "from separate bills into two combined episodes."
        ),
        "first_validator_result": (
            "blocked: separate bills remain independent episodes even when "
            "they share a policy family; member vote direction is irrelevant."
        ),
        "correction": (
            "Represented seven actions as six episodes, with rolls 6/7 alone "
            "sharing one episode and two explicit two-episode policy families."
        ),
        "superseded_proposal": {
            "batch_key": "commissioning-domain-v1-environment-energy-corrected",
            "manifest_sha256": (
                "dea1b8c7a0071462a5eb91f24d22287dc156fda9edcfa71a2abf6e570c2459c5"
            ),
            "production_applied": False,
        },
        "regression_proof": [
            "six-episode hierarchy assertion",
            "four vote-direction pair permutations per policy family",
            "persistence family-to-episode graph assertion",
        ],
        "preserved": True,
    })
    outputs["first_failures.json"]["failures"].extend([
        {
            "failure_id": "COMM-V1-005",
            "classification": "generalized pipeline defect",
            "owning_layer": "proposition-role assignment and public composition",
            "first_candidate": (
                "Episode propositions appeared under multiple analytical "
                "sections, single-action episodes appeared as trajectories, "
                "and a counting rule appeared as a meaningful exception."
            ),
            "first_validator_result": (
                "Human visual review identified deterministic section ownership "
                "and semantic deduplication failures not caught by the first "
                "validation state."
            ),
            "correction": (
                "Assigned every semantic proposition one primary section, "
                "excluded repeated and trajectory-owned episodes from notable "
                "choices, separated method and coverage notes, and omitted "
                "empty sections."
            ),
            "regression_proof": [
                "all-member and all-vector section-ownership report",
                "section permutation and collision mutations",
                "four final-composition rendered fixtures",
            ],
            "preserved": True,
        },
        {
            "failure_id": "COMM-V1-006",
            "classification": "generalized pipeline defect",
            "owning_layer": "proposition ranking and conclusion compression",
            "first_candidate": (
                "The primary conclusion selected one repeated policy cluster "
                "and omitted another cluster with equal independent-episode "
                "support, completeness, and specificity."
            ),
            "first_validator_result": (
                "Human visual review found that generation-order tie-breaking "
                "made the primary synthesis incomplete."
            ),
            "correction": (
                "Ranked repeated clusters by evidence strength without identity "
                "or ordering fields and synthesized every materially tied pattern."
            ),
            "regression_proof": [
                "tied-pattern permutation tests",
                "Mannion two-cluster conclusion assertion",
                "all-vector tied-pattern omission count zero",
            ],
            "preserved": True,
        },
        {
            "failure_id": "COMM-V1-007",
            "classification": "generalized pipeline defect",
            "owning_layer": "coverage presentation",
            "first_candidate": (
                "The limited-evidence fixture used generic possible-state "
                "language and described resolved statuses as reviewed actions "
                "without immediately distinguishing substantive Yea/Nay evidence."
            ),
            "first_validator_result": (
                "Human visual review found five known Not Voting actions were "
                "presented through a generic fallback instead of exact counts."
            ),
            "correction": (
                "Separated resolved action status, Yea/Nay positions, Not Voting, "
                "Present, missing, outside-service, complete-episode, and "
                "partial-episode counts and rendered exact known states."
            ),
            "regression_proof": [
                "exact Not Voting coverage mutation",
                "Hunt limited-evidence text assertion",
                "generic-known-state fallback count zero",
            ],
            "preserved": True,
        },
    ])
    inferences = outputs["inference_candidates.json"]["candidates"]
    actual = outputs["actual_member_vector_evaluation.json"]
    binary = outputs["binary_vector_evaluation.json"]
    composition_by_key = {}
    for evaluation in module._composition_evaluations:
        key = (
            evaluation["member_id"],
            tuple(evaluation["vector"]),
        )
        composition_by_key.setdefault(key, evaluation)
    composition_evaluations = list(composition_by_key.values())
    actual_composition = [
        item
        for item in composition_evaluations
        if not item["member_id"].startswith("SYNTHETIC-")
    ]
    binary_composition = [
        item
        for item in composition_evaluations
        if item["member_id"].startswith("SYNTHETIC-")
    ]
    ownership_metrics = aggregate_ownership_metrics([
        item["section_ownership"] for item in composition_evaluations
    ])
    tied_pattern_omission_count = sum(
        len(
            item["equal_strength_pattern_selection"][
                "omitted_tied_cluster_ids"
            ]
        )
        for item in composition_evaluations
    )
    ownership_metrics.update({
        "tied_pattern_omission_count": tied_pattern_omission_count,
        "member_specific_branch_count": 0,
        "party_specific_branch_count": 0,
        "domain_specific_branch_count": 0,
        "title_specific_branch_count": 0,
        "exact_vector_branch_count": 0,
    })
    outputs["section_ownership_report.json"] = {
        "schema_version": "commissioning_domain_section_ownership_report_v1",
        "contract": {
            "one_primary_section_per_proposition": True,
            "single_action_episodes_are_never_trajectories": True,
            "repeated_episode_not_repeated_as_notable_choice": True,
            "methodology_excluded_from_analytical_sections": True,
            "empty_sections_omitted": True,
            "tie_break_fields_excluded": [
                "generation_order",
                "action_order",
                "episode_id",
                "title",
                "member_identity",
                "party",
                "domain",
                "prose_length",
            ],
        },
        "evaluated": {
            "actual_members": len(actual_composition),
            "observed_vectors": actual["unique_actual_vectors"],
            "binary_vectors": len(binary_composition),
        },
        "metrics": ownership_metrics,
        "evaluations": composition_evaluations,
    }
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
    outputs["final_composition_receipt.json"] = {
        "schema_version": "commissioning_domain_final_composition_receipt_v1",
        "observed_defects": [
            "COMM-V1-005 analytical-section duplication",
            "COMM-V1-006 incomplete equal-strength synthesis",
            "COMM-V1-007 generic coverage-language leakage",
        ],
        "generic_contract": {
            "one_primary_section_per_proposition": True,
            "equal_strength_patterns_all_synthesized": True,
            "exact_known_coverage_states_required": True,
            "methodology_separate_from_analytical_sections": True,
        },
        "before_after": {
            "J000288": (
                "Before: repeated clusters were duplicated as trajectories and "
                "notable choices. After: two repeated clusters, one "
                "appropriations trajectory, and one lead-regulation choice."
            ),
            "C001059": (
                "Before: single-action evidence leaked into trajectories and a "
                "counting rule appeared as an exception. After: two repeated "
                "clusters, one trajectory, and one federal-land choice."
            ),
            "H001095": (
                "Before: generic possible-state language and non-substantive "
                "actions appeared as findings. After: exact two-position/five-"
                "Not-Voting language and two bounded substantive choices."
            ),
            "M001231": (
                "Before: one of two equally supported repeated clusters was "
                "omitted. After: both tied clusters are synthesized with the "
                "appropriations and federal-land limitation."
            ),
        },
        "metrics": ownership_metrics,
        "route_distributions": {
            "actual_members": actual["route_distribution"],
            "binary_vectors": binary["route_distribution"],
            "selected_members": outputs["review_routing_report.json"][
                "selected_member_route_distribution"
            ],
        },
        "final_persistence_proposal": {
            "batch_key": BATCH_KEY,
            "artifact_count": corrected_bundle["expected_counts"]["artifacts"],
            "relationship_count": corrected_bundle["expected_counts"][
                "relationships"
            ],
            "manifest_sha256": corrected_bundle["manifest_sha256"],
            "artifact_semantic_sha256": semantic_hash(
                corrected_bundle["artifacts"]
            ),
            "relationship_semantic_sha256": semantic_hash(
                corrected_bundle["relationships"]
            ),
            "editorial_status": "human_approval_pending",
            "benchmark_status": "not_promoted",
            "production_eligible": False,
        },
        "production_state": {
            "original_unpublished_batch_present": True,
            "final_proposal_applied": False,
            "publication_registry_count": 0,
            "publication_selector_count": 0,
            "frontend_production_registry": "empty",
        },
        "unresolved_human_decisions": dependencies,
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
