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
        **({"review_state": compiled["review_state"]} if "review_state" in compiled else {}),
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
        **({"review_state": compiled["review_state"]} if "review_state" in compiled else {}),
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

    if compiled.get("review_state") == "candidate_pending_external_semantic_review":
        raise ValueError("shared candidates cannot prepare persistence artifacts")
    return {
        "schema_version": "editorial_semantic_ir_persistence_proposal_v1",
        "compiled_ir_sha256": semantic_digest(compiled),
        "compiled_ir": copy.deepcopy(compiled),
        "persistence_authorized": False,
        "publication_authorized": False,
        "production_write_performed": False,
    }


def build_shared_candidate_readable(core, projections, compiled, boundary):
    """Reusable exact-choice wording for candidate review, never public copy.

    No policy inference occurs here. Unsupported proposition shapes fail rather
    than falling back to hand-authored member summaries or generic link text.
    """
    candidate = "candidate_pending_external_semantic_review"
    if core.get("review_state") != candidate or compiled.get("review_state") != candidate:
        raise ValueError("readable candidate form requires explicit candidate inputs")
    actions = {a["action_id"]: a for a in core["actions"]}
    by_member = {m["member_id"]: m for m in compiled["members"]}
    output = []
    for projection in projections:
        member = by_member[projection["member_id"]]
        votes = {a["action_id"]: a for a in projection["actions"]}
        name = projection["context_metadata"]["display_name"]
        findings = []
        for proposition in member["proposition_graph"]["propositions"]:
            if proposition["semantic_role"] != "behavioral":
                continue
            if proposition["proposition_type"] != "notable_choice" or len(proposition["evidence_action_ids"]) != 1:
                raise ValueError("candidate presentation form needs review for this proposition shape")
            aid = proposition["evidence_action_ids"][0]
            action, vote = actions[aid], votes[aid]
            status = vote["official_status"]
            if vote["action_core_sha256"] != action["action_core_sha256"] or status not in {"Yea", "Nay"}:
                raise ValueError("candidate finding is not bound to a directional shared choice")
            if proposition["direction"] != {"Yea": "support", "Nay": "opposition"}[status]:
                raise ValueError("compiled finding changes the recorded choice")
            choice = f"{name} {action['choice_meanings'][status]}."
            meaning = action["candidate_exact_action_meaning"]
            findings.append({
                "proposition_id": proposition["proposition_id"], "action_ids": [aid],
                "episode_ids": proposition["evidence_episode_ids"], "shared_meaning_sha256": action["action_core_sha256"],
                "headline": action["candidate_short_description"],
                "compact": choice + " " + meaning.split(". ", 1)[0].rstrip(".") + ".",
                "detail": [choice, meaning,
                    f"The Clerk recorded the House result as '{action['chamber_outcome']}' on {action['action_date']}. This does not establish enactment."],
                "qualifications_on_both_levels": action["candidate_shared_limitations"],
                "claim_source_map": action["claim_source_map"],
                "source_ids": action["semantic_ir_source_ids"],
            })
        output.append({"member_id": projection["member_id"], "boundary": boundary,
            "findings": findings, "non_proposition_accounting": member["action_accounting"]["non_proposition_reasons"],
            "synthesis": None,
            "synthesis_reason": "Issue membership remains incomplete and no reviewed common-policy relationship has been supplied. These exact choices do not establish an issue-wide position."})
    return {"review_state": candidate, "production_eligible": False,
        "form_version": "shared-exact-choice-candidate-v1", "members": output}
