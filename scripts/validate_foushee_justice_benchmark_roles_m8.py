"""Validate the detached M8 layered benchmark-role contract."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.etl.universe_authority import file_digest_matches  # noqa: E402


RECORD = (
    ROOT / "docs/benchmarks/foushee_justice_public_safety_119_benchmark_roles_v1.json"
)
SCHEMA = (
    ROOT
    / "docs/benchmarks/foushee_justice_public_safety_119_benchmark_roles_v1.schema.json"
)
GRAPH = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2/frozen_final_compiled_semantic_ir.json"
)


class BenchmarkRoleValidationError(ValueError):
    """Raised when a benchmark role or immutable binding drifts."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _content_digest(value: dict[str, Any]) -> str:
    return _digest(
        {key: item for key, item in value.items() if key != "content_subject_sha256"}
    )


def semantic_identities(graph: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    member = graph["compiled_ir"]["members"][0]
    propositions = member["proposition_graph"]["propositions"]
    base_by_id: dict[str, dict[str, Any]] = {}
    for proposition in propositions:
        base_by_id[proposition["proposition_id"]] = {
            "semantic_role": proposition["semantic_role"],
            "proposition_type": proposition["proposition_type"],
            "direction": proposition["direction"],
            "evidence_actions": sorted(proposition["evidence_action_ids"]),
            "evidence_episodes": sorted(proposition["evidence_episode_ids"]),
            "traits": sorted(proposition["mechanism_or_trait_refs"]),
            "conclusion_membership": proposition["conclusion_relevance"],
            "presentation_target": proposition["presentation_target"],
        }
    identities: list[dict[str, Any]] = []
    for proposition in propositions:
        item = dict(base_by_id[proposition["proposition_id"]])
        item["relationships"] = {
            name: sorted(_digest(base_by_id[target]) for target in targets)
            for name, targets in proposition["relationships"].items()
        }
        identities.append(item)
    identities.sort(key=lambda item: _canonical(item))
    boundaries = {
        "action_accounting": member["action_accounting"],
        "coverage": member["coverage"],
        "source_render_constraints": graph["compiled_ir"]["source_render_constraints"],
        "review_route": member["review_route"],
    }
    return _digest(identities), _digest(boundaries), identities


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkRoleValidationError(message)


def validate_primary_proposition_overlap(
    propositions: list[dict[str, Any]],
) -> dict[str, int]:
    """Require independent primary action and episode evidence."""
    primary = [
        item
        for item in propositions
        if item["semantic_role"] == "behavioral"
        and item["conclusion_relevance"] == "primary"
    ]
    action_roles = Counter(
        action for item in primary for action in item["evidence_action_ids"]
    )
    _require(
        max(action_roles.values(), default=0) <= 1,
        "primary action reused across primary behavioral propositions",
    )
    episode_roles = Counter(
        episode for item in primary for episode in item["evidence_episode_ids"]
    )
    _require(
        max(episode_roles.values(), default=0) <= 1,
        "primary episode reused across primary behavioral propositions",
    )
    return {
        "primary_propositions": len(primary),
        "primary_actions": len(action_roles),
        "primary_episodes": len(episode_roles),
    }


def validate(record: dict[str, Any] | None = None) -> dict[str, Any]:
    role_record = _load(RECORD) if record is None else record
    errors = sorted(
        Draft202012Validator(_load(SCHEMA)).iter_errors(role_record),
        key=lambda error: list(error.path),
    )
    if errors:
        raise BenchmarkRoleValidationError(
            f"schema validation failed: {errors[0].message}"
        )
    _require(
        role_record["content_subject_sha256"] == _content_digest(role_record),
        "role-record content digest drift",
    )

    roles = {item["role"]: item for item in role_record["roles"]}
    _require(
        set(roles) == {"compact_regression_fixture", "full_record_reference"},
        "exact layered roles required",
    )
    for role in roles.values():
        artifact = role["artifact"]
        path = ROOT / artifact["path"]
        _require(path.is_file(), f"missing benchmark artifact: {artifact['path']}")
        _require(
            file_digest_matches(path, artifact["final_file_sha256"]),
            f"artifact byte drift: {artifact['path']}",
        )
        for binding in artifact.get("supporting_bindings", []):
            bound_path = ROOT / binding["path"]
            _require(
                bound_path.is_file(), f"missing supporting binding: {binding['path']}"
            )
            _require(
                file_digest_matches(bound_path, binding["final_file_sha256"]),
                f"supporting byte drift: {binding['path']}",
            )

    compact = _load(ROOT / roles["compact_regression_fixture"]["artifact"]["path"])
    _require(
        compact["controls"]["benchmark"]["status"] == "gold_benchmark",
        "compact benchmark promotion drift",
    )
    _require(
        len(compact["provenance"]["claim_refs"]) == 7,
        "compact fixture must remain seven actions",
    )

    full = _load(ROOT / roles["full_record_reference"]["artifact"]["path"])
    _require(
        full["accounting"]
        == {
            "complete_episodes": 32,
            "directional_actions": 35,
            "missing_actions": 0,
            "non_proposition_controls": 2,
            "total_actions": 37,
        },
        "full-record accounting drift",
    )
    _require(
        full["controls"]["production_eligible"] is False,
        "benchmark role cannot grant production eligibility",
    )
    _require(
        full["controls"]["publication_active"] is False,
        "benchmark role cannot activate publication",
    )
    _require(
        full["controls"]["runtime_selectable"] is False,
        "benchmark role cannot activate selectors",
    )

    graph = _load(GRAPH)
    graph_digest, boundary_digest, identities = semantic_identities(graph)
    comparison = role_record["semantic_comparison"]
    _require(
        graph_digest == comparison["normalized_graph_sha256"],
        "normalized semantic identity drift",
    )
    _require(
        boundary_digest == comparison["normalized_boundary_sha256"],
        "normalized boundary drift",
    )

    propositions = graph["compiled_ir"]["members"][0]["proposition_graph"][
        "propositions"
    ]
    counts = Counter(
        (item["semantic_role"], item["proposition_type"]) for item in propositions
    )
    _require(
        counts[("behavioral", "repeated_pattern")] == 4,
        "four primary repeated patterns required",
    )
    _require(
        any(
            item["proposition_type"] == "trajectory"
            and item["evidence_episode_ids"] == ["halt-fentanyl-legislative-path"]
            for item in propositions
        ),
        "HALT Fentanyl trajectory missing",
    )
    overlap = validate_primary_proposition_overlap(propositions)
    _require(
        overlap["primary_propositions"] == 4,
        "four primary behavioral propositions required",
    )
    _require(
        any(
            item["semantic_role"] == "synthesis"
            and item["proposition_type"] == "mechanism_divide"
            and item["direction"] == "mixed"
            for item in propositions
        ),
        "bounded mechanism contrast missing",
    )

    return {
        "status": "pass",
        "roles": sorted(roles),
        "compact_actions": 7,
        "full_actions": 37,
        "full_episodes": 32,
        "normalized_propositions": len(identities),
        "production_eligible": False,
        "publication_active": False,
        "public_selector_active": False,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
