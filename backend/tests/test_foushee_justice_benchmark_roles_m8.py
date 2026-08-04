from __future__ import annotations

import copy
import json

import pytest

from scripts.validate_foushee_justice_benchmark_roles_m8 import (
    BenchmarkRoleValidationError,
    GRAPH,
    RECORD,
    validate,
    validate_primary_proposition_overlap,
)


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _propositions() -> list[dict]:
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    return graph["compiled_ir"]["members"][0]["proposition_graph"]["propositions"]


def test_layered_benchmark_roles_validate() -> None:
    result = validate()
    assert result == {
        "status": "pass",
        "roles": ["compact_regression_fixture", "full_record_reference"],
        "compact_actions": 7,
        "full_actions": 37,
        "full_episodes": 32,
        "normalized_propositions": 24,
        "production_eligible": False,
        "publication_active": False,
        "public_selector_active": False,
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data["roles"].pop(),
        lambda data: data["roles"][0].update({"role": "full_record_reference"}),
        lambda data: data["roles"][0]["scope"].update({"action_count": 8}),
        lambda data: data["roles"][1]["artifact"].update(
            {"final_file_sha256": "0" * 64}
        ),
        lambda data: data["semantic_comparison"].update(
            {"normalized_graph_sha256": "0" * 64}
        ),
        lambda data: data["runtime_boundaries"].update(
            {"full_record_production_eligible": True}
        ),
    ],
)
def test_layered_benchmark_mutations_fail_closed(mutation) -> None:
    data = copy.deepcopy(_record())
    mutation(data)
    with pytest.raises(BenchmarkRoleValidationError):
        validate(data)


def test_accepted_graph_primary_evidence_is_nonoverlapping() -> None:
    result = validate_primary_proposition_overlap(_propositions())
    assert result == {
        "primary_propositions": 4,
        "primary_actions": 13,
        "primary_episodes": 13,
    }


def test_duplicate_primary_action_reuse_fails() -> None:
    propositions = copy.deepcopy(_propositions())
    primary = [
        item
        for item in propositions
        if item["semantic_role"] == "behavioral"
        and item["conclusion_relevance"] == "primary"
    ]
    primary[1]["evidence_action_ids"].append(primary[0]["evidence_action_ids"][0])

    with pytest.raises(
        BenchmarkRoleValidationError,
        match="primary action reused",
    ):
        validate_primary_proposition_overlap(propositions)


def test_same_episode_through_different_primary_actions_fails() -> None:
    propositions = copy.deepcopy(_propositions())
    primary = [
        item
        for item in propositions
        if item["semantic_role"] == "behavioral"
        and item["conclusion_relevance"] == "primary"
    ]
    assert set(primary[0]["evidence_action_ids"]).isdisjoint(
        primary[1]["evidence_action_ids"]
    )
    primary[1]["evidence_episode_ids"][0] = primary[0]["evidence_episode_ids"][0]

    with pytest.raises(
        BenchmarkRoleValidationError,
        match="primary episode reused",
    ):
        validate_primary_proposition_overlap(propositions)
