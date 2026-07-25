from __future__ import annotations

import copy
import json
from pathlib import Path

from backend.app.editorial_artifacts.bundle import ARTIFACT_TYPES, semantic_hash
from backend.scripts.build_commissioning_domain_v1_correction import (
    BATCH_KEY,
    EPISODE_ROLLS,
    ORIGINAL_OUTPUT,
    OUTPUT,
    POLICY_FAMILIES,
    ROLLS,
    _configured_original,
    build,
)
from backend.scripts.commissioning_domain_corrected_artifact_store import (
    BATCH_KEY as STORE_BATCH_KEY,
    load_manifest,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend/data_sources/house_clerk/2026"


def load(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_corrected_builder_matches_checked_in_artifacts() -> None:
    generated = build(SOURCE)
    for name, payload in generated.items():
        assert load(name) == payload


def test_original_evidence_and_manifest_are_preserved() -> None:
    receipt = load("original_preservation_receipt.json")
    assert receipt["status"] == "preserved_unchanged_historical_evidence"
    original_manifest = json.loads(
        (ORIGINAL_OUTPUT / "persistence_batch_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        receipt["original_manifest_sha256"]
        == original_manifest["manifest_sha256"]
        == "5821e12ca1e5666ed6ff39b1a9a2402a9f61e067d56dcd69a1870b5a64333c38"
    )
    for name, record in receipt["artifacts"].items():
        current = json.loads((ORIGINAL_OUTPUT / name).read_text(encoding="utf-8"))
        assert record["semantic_sha256"] == semantic_hash(current)


def test_roll_five_is_rejected_and_rolls_six_and_seven_are_bounded() -> None:
    assert ROLLS == (6, 7, 55, 64, 76, 78, 93)
    accepted = load("accepted_actions.json")
    rejected = load("rejected_actions.json")
    eligibility = load("domain_eligibility_report.json")
    assert [item["roll"] for item in accepted["actions"]] == list(ROLLS)
    roll_five = next(item for item in rejected["actions"] if item["roll"] == 5)
    assert roll_five["reason"] == "exact_action_not_materially_environment_energy"
    assert eligibility["decisions"]["5"]["eligible"] is False
    assert eligibility["decisions"]["6"]["eligible"] is True
    assert eligibility["decisions"]["7"]["eligible"] is True
    assert "cross-domain" in eligibility["decisions"]["7"]["exact_action_boundary"]
    assert "combined" in next(
        item for item in accepted["actions"] if item["roll"] == 6
    )["caveats"][1].lower()


def test_corrected_generality_and_shared_review_deduplication() -> None:
    actual = load("actual_member_vector_evaluation.json")
    binary = load("binary_vector_evaluation.json")
    routing = load("review_routing_report.json")
    mutation = load("mutation_report.json")
    assert actual["members_evaluated"] == 432
    assert actual["unique_actual_vectors"] == 35
    assert binary["binary_vector_count"] == 128
    assert actual["human_exception_count"] < actual["members_evaluated"] / 2
    assert routing["shared_human_review_queue_count"] == len(
        routing["shared_review_dependencies"]
    )
    assert routing["shared_dependency_member_route_amplification"] == 0
    assert routing["member_route_basis"] == "member_specific_findings_only"
    assert set(routing["allowed_member_routes"]) == {
        "standard_generation_pass",
        "sampled_audit_candidate",
        "human_exception_required",
        "blocked",
    }
    assert routing["invariance_and_branch_results"] == {
        "identity_invariance_failures": 0,
        "party_invariance_failures": 0,
        "direction_only_winners": 0,
        "member_specific_branches": 0,
        "domain_specific_branches": 0,
        "title_specific_branches": 0,
        "roll_specific_branches": 0,
        "exact_vector_branches": 0,
    }
    assert mutation["original_mutation_count"] == 17
    assert mutation["counts"]["total"] == 39
    assert mutation["counts"]["failed"] == 0


def test_seven_actions_form_six_vote_direction_invariant_episodes() -> None:
    assert EPISODE_ROLLS == {
        "fy2026-energy-water-interior-appropriations": (6, 7),
        "critical-mineral-project-acceleration": (55,),
        "critical-mineral-supply-assessment-and-strategy": (64,),
        "home-energy-efficiency-rulemaking": (76,),
        "home-energy-program-repeal": (78,),
        "lead-ammunition-and-tackle-on-federal-lands": (93,),
    }
    assert POLICY_FAMILIES == {
        "critical-mineral-supply": (
            "critical-mineral-project-acceleration",
            "critical-mineral-supply-assessment-and-strategy",
        ),
        "home-energy-policy": (
            "home-energy-efficiency-rulemaking",
            "home-energy-program-repeal",
        ),
    }
    episode_map = load("episode_map.json")
    assert episode_map["counts"]["independent_episodes"] == 6
    assert episode_map["counts"]["multi_action_episodes"] == 1

    module = _configured_original()
    identifier = "DIRECTION-INVARIANCE"
    for first in ("Yea", "Nay"):
        for second in ("Yea", "Nay"):
            actions = {
                roll: {identifier: {"action": "Yea"}}
                for roll in ROLLS
            }
            actions[55][identifier]["action"] = first
            actions[64][identifier]["action"] = second
            actions[76][identifier]["action"] = first
            actions[78][identifier]["action"] = second
            overlay = module._overlay(
                {
                    "bioguide_id": identifier,
                    "display_name": "Direction Invariance",
                    "party": None,
                    "state": "",
                },
                actions,
            )
            by_roll = {
                item["roll"]: item
                for item in overlay["roll_actions"]
            }
            assert by_roll[55]["action"] == first
            assert by_roll[64]["action"] == second
            assert by_roll[55]["episode_id"] != by_roll[64]["episode_id"]
            assert by_roll[76]["action"] == first
            assert by_roll[78]["action"] == second
            assert by_roll[76]["episode_id"] != by_roll[78]["episode_id"]


def test_corrected_pending_bundle_is_distinct_complete_and_unpublished() -> None:
    bundle = load("persistence_batch_manifest.json")
    for_hash = copy.deepcopy(bundle)
    claimed = for_hash.pop("manifest_sha256")
    assert claimed == semantic_hash(for_hash)
    assert bundle["deterministic_batch_key"] == BATCH_KEY
    assert bundle["publication_registry_expected_rows"] == 0
    assert {item["artifact_type"] for item in bundle["artifacts"]} == set(
        ARTIFACT_TYPES
    )
    assert all(
        "commissioning-v1-final-composition" in item["natural_key"]
        for item in bundle["artifacts"]
    )
    original_keys = {
        item["natural_key"]
        for item in json.loads(
            (ORIGINAL_OUTPUT / "persistence_batch_manifest.json").read_text(
                encoding="utf-8"
            )
        )["artifacts"]
    }
    assert not original_keys.intersection(
        item["natural_key"] for item in bundle["artifacts"]
    )
    for item in bundle["artifacts"]:
        assert item["editorial_status"] == "human_approval_pending"
        assert item["benchmark_status"] == "not_promoted"
        assert item["production_eligible"] is False
        if item["member_bioguide_id"]:
            dependencies = item["payload"]["shared_review_dependencies"]
            assert dependencies["review_queue_scope"] == "shared_corpus"
            assert dependencies["dependency_review_state"] == "human_review_pending"
            assert dependencies["publication_blocked_until_resolved"] is True
            assert len(dependencies["dependency_ids"]) == 7
    policy_families = [
        item for item in bundle["artifacts"]
        if item["artifact_type"] == "policy_family"
    ]
    policy_episodes = [
        item for item in bundle["artifacts"]
        if item["artifact_type"] == "policy_episode"
    ]
    assert len(policy_families) == 2
    assert len(policy_episodes) == 6
    assert {
        item["policy_family_id"] for item in policy_families
    } == set(POLICY_FAMILIES)
    assert sum(
        item["relationship_type"] == "groups_episode"
        for item in bundle["relationships"]
    ) == 4
    assert sum(
        item["relationship_type"] == "contains_action"
        for item in bundle["relationships"]
    ) == 7
    assert STORE_BATCH_KEY == BATCH_KEY
    assert load_manifest() == bundle


def test_failure_history_records_human_discovery_truthfully() -> None:
    failures = load("first_failures.json")["failures"]
    assert [item["failure_id"] for item in failures] == [
        "COMM-V1-001",
        "COMM-V1-002",
        "COMM-V1-003",
        "COMM-V1-004",
        "COMM-V1-005-HIERARCHY",
        "COMM-V1-005",
        "COMM-V1-006",
        "COMM-V1-007",
    ]
    correction = next(item for item in failures if item["failure_id"] == "COMM-V1-004")
    assert correction["preserved"] is True
    assert "first_validator_result" in correction
    assert "roll 5" in correction["first_candidate"].lower()
    hierarchy = next(
        item for item in failures
        if item["failure_id"] == "COMM-V1-005-HIERARCHY"
    )
    assert hierarchy["preserved"] is True
    assert hierarchy["superseded_proposal"]["production_applied"] is False
    assert failures[-1]["failure_id"] == "COMM-V1-007"


def test_section_ownership_and_equal_strength_synthesis_are_complete() -> None:
    report = load("section_ownership_report.json")
    assert report["evaluated"] == {
        "actual_members": 432,
        "observed_vectors": 35,
        "binary_vectors": 128,
    }
    assert all(value == 0 for value in report["metrics"].values())

    inferences = {
        item["member"]["bioguide_id"]: item
        for item in load("inference_candidates.json")["candidates"]
    }
    mannion = inferences["M001231"]
    tied = mannion["equal_strength_pattern_selection"]
    assert tied["tied_cluster_ids"] == [
        "domestic_resource_supply_actions",
        "home_energy_federal_role_changes",
    ]
    assert tied["omitted_tied_cluster_ids"] == []
    assert "domestic resource-supply proposals" in mannion["primary_conclusion"]
    assert "home-energy standards or programs" in mannion["primary_conclusion"]
    assert "appropriations stages and the federal-land proposal" in (
        mannion["primary_conclusion"]
    )

    for member_id in ("J000288", "C001059", "M001231"):
        sections = inferences[member_id]["analytical_sections"]
        assert len(sections["repeated_patterns"]) == 2
        assert len(sections["policy_trajectories"]) == 1
        assert len(sections["other_notable_choices"]) == 1
        assert sections["meaningful_exceptions"] == []
        assert inferences[member_id]["method_note"]

    hunt = inferences["H001095"]
    assert hunt["analytical_sections"]["repeated_patterns"] == []
    assert hunt["analytical_sections"]["policy_trajectories"] == []
    assert len(hunt["analytical_sections"]["other_notable_choices"]) == 2
    assert hunt["analytical_sections"]["meaningful_exceptions"] == []
    assert "only 2 contain Yea/Nay positions; 5 are Not Voting" in (
        hunt["primary_conclusion"]
    )
    assert "Present" not in hunt["coverage_note"]
    assert "outside service" not in hunt["coverage_note"]


def test_composition_is_invariant_to_episode_and_tied_pattern_order() -> None:
    module = _configured_original()
    identifier = "ORDER-INVARIANCE"
    vector = ("Yea", "Yea", "Nay", "Nay", "Nay", "Nay", "Yea")
    actions = {
        roll: {identifier: {"action": action}}
        for roll, action in zip(ROLLS, vector)
    }
    member = {
        "bioguide_id": identifier,
        "display_name": "Order Invariance",
        "party": None,
        "state": "",
    }
    overlay = module._overlay(member, actions)
    forward = module.evaluate_candidates(
        overlay=overlay,
        shared_episodes=module.EPISODES,
        theme_catalog=module.THEMES,
        candidate_catalog=module.CANDIDATES,
        trait_contract=module.TRAIT_CONTRACT,
    )
    reversed_overlay = copy.deepcopy(overlay)
    reversed_overlay["episode_trajectories"].reverse()
    reverse = module.evaluate_candidates(
        overlay=reversed_overlay,
        shared_episodes=list(reversed(module.EPISODES)),
        theme_catalog=dict(reversed(list(module.THEMES.items()))),
        candidate_catalog=list(reversed(module.CANDIDATES)),
        trait_contract={
            **module.TRAIT_CONTRACT,
            "policy_clusters": dict(
                reversed(list(module.TRAIT_CONTRACT["policy_clusters"].items()))
            ),
        },
    )
    assert forward["primary_conclusion"] == reverse["primary_conclusion"]
    assert forward["analytical_sections"] == reverse["analytical_sections"]
    assert forward["equal_strength_pattern_selection"] == (
        reverse["equal_strength_pattern_selection"]
    )


def test_generic_corrections_have_no_case_specific_branches() -> None:
    eligibility = (
        ROOT / "backend/app/summaries/editorial_domain_eligibility.py"
    ).read_text(encoding="utf-8").lower()
    routing = (
        ROOT / "backend/app/summaries/editorial_review_routing.py"
    ).read_text(encoding="utf-8").lower()
    for forbidden in (
        "roll 5",
        "h.r. 6938",
        "environment_energy",
        "division a",
        "party ==",
        "exact vector",
    ):
        assert forbidden not in eligibility
        assert forbidden not in routing
