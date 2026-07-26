"""Meaning-preserving adapters for already compiled Editorial Semantic IR."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


def semantic_digest(compiled: dict[str, Any]) -> str:
    """Return a deterministic boundary hash without changing the payload."""

    encoded = json.dumps(
        compiled, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_review_payload(compiled: dict[str, Any]) -> dict[str, Any]:
    """Expose compiler-owned routes and constraints for review tooling."""

    return {
        "schema_version": "editorial_semantic_ir_review_payload_v1",
        "compiled_ir_sha256": semantic_digest(compiled),
        "members": [
            {
                "member_id": member["member_id"],
                "review_route": member["review_route"],
                "coverage": copy.deepcopy(member["coverage"]),
            }
            for member in compiled["members"]
        ],
        "source_render_constraints": copy.deepcopy(
            compiled["source_render_constraints"]
        ),
        "authority": "compiled_editorial_semantic_ir_v1",
        "approval_conferred": False,
    }


def build_presentation_payload(compiled: dict[str, Any]) -> dict[str, Any]:
    """Select compiled presentation objects; never create analytical meaning."""

    return {
        "schema_version": "editorial_semantic_ir_presentation_payload_v1",
        "compiled_ir_sha256": semantic_digest(compiled),
        "members": [
            {
                "member_id": member["member_id"],
                "party": member["party"],
                "proposition_graph": copy.deepcopy(member["proposition_graph"]),
                "composition": copy.deepcopy(member["composition"]),
                "coverage": copy.deepcopy(member["coverage"]),
                "review_route": member["review_route"],
            }
            for member in compiled["members"]
        ],
        "source_render_constraints": copy.deepcopy(
            compiled["source_render_constraints"]
        ),
        "rendering_may_add_analytical_meaning": False,
    }


def build_persistence_proposal(compiled: dict[str, Any]) -> dict[str, Any]:
    """Prepare an inert proposal; this function performs no persistence."""

    return {
        "schema_version": "editorial_semantic_ir_persistence_proposal_v1",
        "compiled_ir_sha256": semantic_digest(compiled),
        "compiled_ir": copy.deepcopy(compiled),
        "persistence_authorized": False,
        "publication_authorized": False,
        "production_write_performed": False,
    }
