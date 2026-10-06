"""Validation of compiled Editorial Semantic IR without re-deriving meaning."""

from __future__ import annotations

from typing import Any


class CompiledSemanticIRError(ValueError):
    """Raised when compiled IR violates a downstream structural invariant."""


def validate_compiled_ir(compiled: dict[str, Any]) -> dict[str, int]:
    """Validate identities, references, ownership, and action accounting."""

    expected = {"members", "source_render_constraints"}
    if compiled.get("review_state") == "candidate_pending_external_semantic_review":
        expected.add("review_state")
    if set(compiled) != expected:
        raise CompiledSemanticIRError("compiled IR has unexpected top-level fields")
    proposition_count = 0
    for member in compiled["members"]:
        propositions = member["proposition_graph"]["propositions"]
        by_id = {item["proposition_id"]: item for item in propositions}
        if len(by_id) != len(propositions):
            raise CompiledSemanticIRError("proposition identities must be unique")
        proposition_ids = set(by_id)
        for proposition in propositions:
            observations = proposition.get("action_observations")
            if observations is not None:
                if (compiled.get("review_state") != "candidate_pending_external_semantic_review"
                        or proposition["proposition_type"] != "notable_choice"
                        or len(proposition["evidence_episode_ids"]) != 1 or len(observations) < 2):
                    raise CompiledSemanticIRError("ordered observations require one candidate notable-choice episode")
                ids = [o["action_id"] for o in observations]
                if len(ids) != len(set(ids)):
                    raise CompiledSemanticIRError("duplicate episode observation")
                directions = set()
                directional = set()
                for observation in observations:
                    direction = observation["direction"]
                    if direction is not None:
                        expected_direction = {"Yea": "support", "Nay": "opposition"}.get(observation["status"])
                        if (direction != expected_direction or observation["service_status"] != "in_service"
                                or observation["evidence_status"] != "official_record_resolved"):
                            raise CompiledSemanticIRError("non-directional or unresolved observation cannot count")
                        directional.add(observation["action_id"]); directions.add(direction)
                if directional != set(proposition["evidence_action_ids"]):
                    raise CompiledSemanticIRError("observation evidence accounting differs")
                if proposition["direction"] != (next(iter(directions)) if len(directions) == 1 else "mixed"):
                    raise CompiledSemanticIRError("episode direction differs from its exact choices")
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
