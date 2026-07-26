"""Validation of compiled Editorial Semantic IR without re-deriving meaning."""

from __future__ import annotations

from typing import Any


class CompiledSemanticIRError(ValueError):
    """Raised when compiled IR violates a downstream structural invariant."""


def validate_compiled_ir(compiled: dict[str, Any]) -> dict[str, int]:
    """Validate identities, references, ownership, and action accounting."""

    if set(compiled) != {"members", "source_render_constraints"}:
        raise CompiledSemanticIRError("compiled IR has unexpected top-level fields")
    proposition_count = 0
    for member in compiled["members"]:
        propositions = member["proposition_graph"]["propositions"]
        by_id = {item["proposition_id"]: item for item in propositions}
        if len(by_id) != len(propositions):
            raise CompiledSemanticIRError("proposition identities must be unique")
        proposition_ids = set(by_id)
        for proposition in propositions:
            related = set(proposition["relationships"]["supported_by"])
            related.update(proposition["relationships"]["limited_by"])
            if not related <= proposition_ids:
                raise CompiledSemanticIRError("proposition relationship is unresolved")

        composition = member["composition"]
        conclusion_ids = set(
            composition["conclusion_plan"]["primary_proposition_ids"]
        )
        conclusion_ids.update(
            composition["conclusion_plan"]["limiting_proposition_ids"]
        )
        if not conclusion_ids <= proposition_ids:
            raise CompiledSemanticIRError("conclusion plan references unknown meaning")

        owned: dict[str, str] = {}
        for target, ids in composition["presentation_ownership"].items():
            for proposition_id in ids:
                if proposition_id not in proposition_ids:
                    raise CompiledSemanticIRError(
                        "presentation ownership references unknown meaning"
                    )
                if proposition_id in owned:
                    raise CompiledSemanticIRError(
                        "proposition has more than one presentation owner"
                    )
                if by_id[proposition_id]["presentation_target"] != target:
                    raise CompiledSemanticIRError(
                        "presentation ownership changes compiled target"
                    )
                owned[proposition_id] = target

        behavioral = {
            action_id
            for proposition in propositions
            if proposition["semantic_role"] == "behavioral"
            for action_id in proposition["evidence_action_ids"]
        }
        accounting = member["action_accounting"]
        if behavioral != set(accounting["behavioral_proposition_action_ids"]):
            raise CompiledSemanticIRError(
                "behavioral action accounting does not match propositions"
            )
        reason_ids = [
            item["action_id"] for item in accounting["non_proposition_reasons"]
        ]
        if len(reason_ids) != len(set(reason_ids)):
            raise CompiledSemanticIRError(
                "an action has duplicate non-proposition reasons"
            )
        if behavioral & set(reason_ids):
            raise CompiledSemanticIRError(
                "an action is both behavioral evidence and non-proposition evidence"
            )
        proposition_count += len(propositions)
    return {
        "member_count": len(compiled["members"]),
        "proposition_count": proposition_count,
        "source_render_constraint_count": len(
            compiled["source_render_constraints"]
        ),
    }
