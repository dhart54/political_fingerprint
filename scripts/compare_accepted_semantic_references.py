"""Compile and compare all accepted Editorial Semantic IR V1 references."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import (  # noqa: E402
    compile_semantic_ir,
    project_compiler_input,
)


ACCEPTED = ROOT / "docs/semantic_ir/accepted/development_cases.json"


class ReferenceComparisonError(AssertionError):
    """Raised when compiled semantics drift from an accepted reference."""


def _set(values: list[str]) -> tuple[str, ...]:
    return tuple(sorted(values))


def _prop_signature(proposition: dict[str, Any]) -> tuple[Any, ...]:
    return (
        proposition["semantic_role"],
        proposition["proposition_type"],
        proposition["direction"],
        _set(proposition["evidence_action_ids"]),
        _set(proposition["evidence_episode_ids"]),
        _set(proposition["mechanism_or_trait_refs"]),
        proposition["presentation_target"],
        proposition["conclusion_relevance"],
    )


def _normalized_graph(
    propositions: list[dict[str, Any]],
) -> tuple[set[tuple[Any, ...]], set[tuple[Any, ...]]]:
    signatures = {
        proposition["proposition_id"]: _prop_signature(proposition)
        for proposition in propositions
    }
    relationships = set()
    for proposition in propositions:
        source = signatures[proposition["proposition_id"]]
        for relation in ("supported_by", "limited_by"):
            for target_id in proposition["relationships"][relation]:
                relationships.add((source, relation, signatures[target_id]))
    return set(signatures.values()), relationships


def _normalized_membership(
    ids: list[str], propositions: list[dict[str, Any]]
) -> set[tuple[Any, ...]]:
    signatures = {
        proposition["proposition_id"]: _prop_signature(proposition)
        for proposition in propositions
    }
    return {signatures[proposition_id] for proposition_id in ids}


def _normalized_ownership(
    ownership: dict[str, list[str]], propositions: list[dict[str, Any]]
) -> dict[str, set[tuple[Any, ...]]]:
    signatures = {
        proposition["proposition_id"]: _prop_signature(proposition)
        for proposition in propositions
    }
    return {
        target: {signatures[proposition_id] for proposition_id in ids}
        for target, ids in ownership.items()
    }


def _normalized_boundaries(
    boundaries: list[dict[str, Any]],
) -> set[tuple[str, tuple[str, ...], str]]:
    return {
        (
            boundary["boundary_type"],
            _set(boundary["action_ids"]),
            boundary["presentation_target"],
        )
        for boundary in boundaries
    }


def _normalized_accounting(accounting: dict[str, Any]) -> dict[str, Any]:
    return {
        "behavioral": set(accounting["behavioral_proposition_action_ids"]),
        "reasons": {
            (reason["action_id"], reason["reason_code"])
            for reason in accounting["non_proposition_reasons"]
        },
    }


def semantic_projection(result: dict[str, Any]) -> dict[str, Any]:
    """Return identity-neutral semantic output for property comparisons."""

    propositions = result["proposition_graph"]["propositions"]
    graph, relationships = _normalized_graph(propositions)
    composition = result["composition"]
    return {
        "coverage": result["coverage"],
        "graph": graph,
        "relationships": relationships,
        "primary": _normalized_membership(
            composition["conclusion_plan"]["primary_proposition_ids"], propositions
        ),
        "limiting": _normalized_membership(
            composition["conclusion_plan"]["limiting_proposition_ids"], propositions
        ),
        "ownership": _normalized_ownership(
            composition["presentation_ownership"], propositions
        ),
        "coverage_boundaries": _normalized_boundaries(
            composition["coverage_boundaries"]
        ),
        "method_boundaries": _normalized_boundaries(
            composition["method_boundaries"]
        ),
        "accounting": _normalized_accounting(result["action_accounting"]),
        "review_route": result["review_route"],
    }


def expected_projection(
    case: dict[str, Any], member: dict[str, Any]
) -> dict[str, Any]:
    propositions = case["proposition_graph"]["propositions"]
    composition = case["composition"]
    graph, relationships = _normalized_graph(propositions)
    return {
        "coverage": member["coverage"],
        "graph": graph,
        "relationships": relationships,
        "primary": _normalized_membership(
            composition["conclusion_plan"]["primary_proposition_ids"], propositions
        ),
        "limiting": _normalized_membership(
            composition["conclusion_plan"]["limiting_proposition_ids"], propositions
        ),
        "ownership": _normalized_ownership(
            composition["presentation_ownership"], propositions
        ),
        "coverage_boundaries": _normalized_boundaries(
            composition["coverage_boundaries"]
        ),
        "method_boundaries": _normalized_boundaries(
            composition["method_boundaries"]
        ),
        "accounting": _normalized_accounting(case["action_accounting"]),
        "review_route": case["member_semantics"]["review_route"],
    }


def compare_case(case: dict[str, Any]) -> None:
    compiled = compile_semantic_ir(project_compiler_input(case))
    expected_members = case["member_semantics"]["members"]
    if len(compiled["members"]) != len(expected_members):
        raise ReferenceComparisonError(
            f"{case['case_id']}: compiled member count drift"
        )
    for expected_member, actual_member in zip(expected_members, compiled["members"]):
        expected = expected_projection(case, expected_member)
        actual = semantic_projection(actual_member)
        if actual != expected:
            differing = [
                key for key in expected if expected[key] != actual.get(key)
            ]
            raise ReferenceComparisonError(
                f"{case['case_id']}: semantic drift in {', '.join(differing)}"
            )
    if compiled["source_render_constraints"] != case["shared_semantics"].get(
        "source_render_constraints", []
    ):
        raise ReferenceComparisonError(
            f"{case['case_id']}: source/render constraint drift"
        )


def run() -> dict[str, Any]:
    started = time.perf_counter()
    corpus = json.loads(ACCEPTED.read_text(encoding="utf-8"))
    case_ids = []
    for case in corpus["cases"]:
        compare_case(case)
        case_ids.append(case["case_id"])
    return {
        "status": "pass",
        "accepted_reference_comparisons": len(case_ids),
        "case_ids": case_ids,
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine JSON")
    args = parser.parse_args(argv)
    try:
        result = run()
    except ReferenceComparisonError as exc:
        print(f"Accepted-reference comparison failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "Accepted-reference comparison passed: "
            f"{result['accepted_reference_comparisons']} cases, "
            f"{result['elapsed_seconds']:.4f}s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
