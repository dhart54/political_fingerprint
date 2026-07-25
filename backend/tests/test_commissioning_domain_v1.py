from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from backend.app.editorial_artifacts.bundle import ARTIFACT_TYPES, semantic_hash
from backend.scripts.build_commissioning_domain_v1 import (
    ACTION_DOSSIERS,
    EPISODES,
    ISSUE,
    PUBLICATION,
    ROLLS,
    build,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/editorial/commissioning_domain_v1"
SOURCE = ROOT / "backend/data_sources/house_clerk/2026"


def load(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_builder_matches_checked_in_artifacts() -> None:
    generated = build(SOURCE)
    for name, payload in generated.items():
        assert load(name) == payload


def test_shared_corpus_is_member_neutral_and_bounded() -> None:
    assert len(ROLLS) == 8
    assert len(EPISODES) == 4
    assert sum(len(item["rolls"]) > 1 for item in EPISODES) >= 1
    assert len({item["mechanism_family"] for item in EPISODES}) >= 2
    forbidden = {"member", "party", "member_vote", "member_conclusion"}
    for dossier in ACTION_DOSSIERS.values():
        assert not forbidden.intersection(dossier)
        assert dossier["source_ids"]
        assert dossier["exact_stage"]
        assert dossier["caveats"]


def test_claims_are_mapped_or_have_supported_absence() -> None:
    claim_map = load("claim_source_map.json")
    assert claim_map["counts"]["claim_supported"] == 66
    assert claim_map["counts"]["supported_absence"] == 6
    for claim in claim_map["claims"]:
        assert claim["state"] in {"claim_supported", "supported_absence"}
        if claim["state"] == "claim_supported":
            assert claim["source_ids"]
        else:
            assert claim["absence_reason"]


def test_corpus_was_frozen_before_member_selection() -> None:
    freeze = load("corpus_freeze.json")
    cohort = load("cohort_selection.json")
    assert freeze["frozen_before_member_selection"] is True
    assert cohort["frozen_corpus_sha256"] == freeze["semantic_sha256"]
    assert cohort["counts"]["selected"] in range(6, 9)
    assert cohort["counts"]["unique_vectors"] >= 4


def test_all_house_and_binary_generality_results_are_bounded() -> None:
    actual = load("actual_member_vector_evaluation.json")
    binary = load("binary_vector_evaluation.json")
    mutation = load("mutation_report.json")
    assert actual["members_evaluated"] >= 400
    assert actual["unique_actual_vectors"] >= 4
    assert actual["identity_invariance_failures"] == 0
    assert actual["party_invariance_failures"] == 0
    assert actual["direction_only_winners"] == 0
    assert actual["member_specific_branch_required"] == 0
    assert binary["binary_vector_count"] == 256
    assert binary["direction_only_winner_count"] == 0
    assert binary["member_party_title_domain_or_exact_vector_branch_count"] == 0
    assert mutation["counts"]["failed"] == 0


def test_pending_bundle_is_complete_immutable_and_unpublished() -> None:
    bundle = load("persistence_batch_manifest.json")
    copy_for_hash = copy.deepcopy(bundle)
    claimed = copy_for_hash.pop("manifest_sha256")
    assert claimed == semantic_hash(copy_for_hash)
    assert bundle["publication_registry_expected_rows"] == 0
    assert {item["artifact_type"] for item in bundle["artifacts"]} == set(ARTIFACT_TYPES)
    assert bundle["expected_counts"]["artifacts"] == len(bundle["artifacts"])
    assert bundle["expected_counts"]["relationships"] == len(bundle["relationships"])
    natural_keys = {item["natural_key"] for item in bundle["artifacts"]}
    for item in bundle["artifacts"]:
        assert item["editorial_status"] == PUBLICATION["editorial_status"]
        assert item["benchmark_status"] == PUBLICATION["benchmark_status"]
        assert item["production_eligible"] is False
        assert item["content_sha256"] == semantic_hash(item["payload"])
        assert item["issue_id"] == ISSUE
    for relationship in bundle["relationships"]:
        assert relationship["parent_natural_key"] in natural_keys
        assert relationship["child_natural_key"] in natural_keys


def test_first_failures_are_preserved() -> None:
    failures = load("first_failures.json")["failures"]
    assert {item["failure_id"] for item in failures} == {
        "COMM-V1-001", "COMM-V1-002", "COMM-V1-003",
    }
    assert all(item["preserved"] and item["regression_proof"] for item in failures)


def test_publication_state_mutation_is_rejected_by_overlay_contract() -> None:
    from backend.app.summaries.editorial_member_overlay import build_member_overlay

    outputs = build(SOURCE)
    overlay = outputs["member_overlays.json"]["overlays"][0]
    with pytest.raises(ValueError, match="publication production_eligible"):
        build_member_overlay(
            member=overlay["member"],
            reviewed_period=overlay["reviewed_period"],
            shared_episode_set=overlay["shared_episode_set"],
            roll_actions=overlay["roll_actions"],
            episode_action_interpretations={
                row["episode_id"]: {
                    "mechanism_family": row["mechanism_family"],
                    "signatures": {
                        "|".join(row["action_signature"]): {
                            "member_trajectory": row["member_trajectory"],
                            "practical_policy_direction": row["practical_policy_direction"],
                            "theme_evidence": [],
                        }
                    },
                    "non_counting": {
                        "member_trajectory": "No counting trajectory.",
                        "practical_policy_direction": "No direction.",
                        "theme_evidence": [],
                    },
                }
                for row in overlay["episode_trajectories"]
            },
            publication={**PUBLICATION, "production_eligible": True},
        )
