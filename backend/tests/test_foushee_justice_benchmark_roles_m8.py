from __future__ import annotations

import copy
import json

import pytest

from scripts.validate_foushee_justice_benchmark_roles_m8 import (
    BenchmarkRoleValidationError,
    RECORD,
    validate,
)


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


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
