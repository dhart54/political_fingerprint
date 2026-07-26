"""Fast, dependency-free contract validation for Editorial Semantic IR V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/semantic_ir/editorial_semantic_ir_v1.schema.json"
ACCEPTED = ROOT / "docs/semantic_ir/accepted/development_cases.json"
ACCEPTANCE_RECEIPT = ROOT / "docs/semantic_ir/accepted/acceptance_receipt.json"
HELD_OUT = ROOT / "docs/semantic_ir/held_out_inputs/held_out_cases.json"
REVIEW_JSON = (
    ROOT
    / "docs/review_packets/editorial_semantic_ir_gold_v1_candidate_review.json"
)
SOURCE_MANIFESTS = (
    ROOT / "docs/editorial/valerie_foushee_economy_gold_v2/source_manifest.json",
    ROOT
    / "docs/editorial/valerie_foushee_justice_public_safety_gold_v1/source_manifest.json",
    ROOT / "docs/editorial/commissioning_domain_v1/corrected/source_manifest.json",
)

REVIEW_STATE = "candidate_pending_external_semantic_review"
ACCEPTED_STATE = "accepted_semantic_reference"
STATUS_VALUES = {"Yea", "Nay", "Present", "Not Voting", "Missing Evidence"}
SECTION_RENDERED_TARGETS = {
    "repeated_patterns",
    "policy_trajectories",
    "other_notable_choices",
}
PRESENTATION_TARGETS = SECTION_RENDERED_TARGETS | {
    "meaningful_limitations",
    "conclusion_only",
    "coverage_note",
    "method_note",
    "source_note",
    "omitted",
}
HELD_OUT_FORBIDDEN_KEYS = {
    "proposition_graph",
    "propositions",
    "composition",
    "conclusion_plan",
    "expected_result",
    "expected_propositions",
    "expected_conclusion",
    "coverage_boundaries",
    "method_boundaries",
    "action_accounting",
    "external_review_decisions",
}
ID_PATTERNS = {
    "development": re.compile(r"^semir-dev-\d{2}-[a-z0-9-]+$"),
    "held_out": re.compile(r"^semir-held-\d{2}-[a-z0-9-]+$"),
    "action": re.compile(r"^house:\d+:\d+:\d+$"),
    "proposition": re.compile(r"^prop:[a-z0-9-]+$"),
}


class SemanticValidationError(ValueError):
    """Raised when an IR contract invariant fails."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticValidationError(f"{path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticValidationError(f"{path.relative_to(ROOT)}: root must be object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SemanticValidationError(message)


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    return {value for value in values if value in seen or seen.add(value)}


def _known_source_ids() -> set[str]:
    source_ids: set[str] = set()
    for path in SOURCE_MANIFESTS:
        manifest = _load(path)
        for source in manifest.get("sources", []):
            source_id = source.get("source_id")
            if isinstance(source_id, str):
                source_ids.add(source_id)
    return source_ids


def _validate_coverage(
    case_id: str,
    member: dict[str, Any],
    shared_actions: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
) -> None:
    actions = member["actions"]
    coverage = member["coverage"]
    eligible_ids = {
        action["action_id"]
        for action in shared_actions
        if action["eligibility"]["decision"] == "accepted"
    }
    context_ids = {
        action["action_id"]
        for action in shared_actions
        if action["eligibility"]["decision"] != "accepted"
    }
    eligible_actions = [item for item in actions if item["action_id"] in eligible_ids]
    statuses = [item["status"] for item in eligible_actions]
    _require(set(statuses) <= STATUS_VALUES, f"{case_id}: invalid member status")
    in_service = sum(item["service_status"] == "in_service" for item in eligible_actions)
    resolved = sum(
        item["evidence_status"] == "official_record_resolved"
        for item in eligible_actions
    )
    yes_no = sum(status in {"Yea", "Nay"} for status in statuses)
    present = statuses.count("Present")
    not_voting = statuses.count("Not Voting")
    missing = sum(
        item["evidence_status"] != "official_record_resolved"
        for item in eligible_actions
    )
    outside_service = sum(
        item["service_status"] != "in_service" for item in eligible_actions
    )
    by_id = {item["action_id"]: item for item in actions}
    complete_episodes = 0
    partial_episodes = 0
    for episode in episodes:
        episode_actions = [by_id.get(action_id) for action_id in episode["action_ids"]]
        if all(
            action
            and action["service_status"] == "in_service"
            and action["evidence_status"] == "official_record_resolved"
            for action in episode_actions
        ):
            complete_episodes += 1
        else:
            partial_episodes += 1

    _require(
        coverage["eligible_substantive_actions"] == len(eligible_ids),
        f"{case_id}: eligible substantive coverage",
    )
    _require(
        coverage["context_only_control_actions"] == len(context_ids),
        f"{case_id}: context/control coverage",
    )
    _require(
        coverage["in_service_eligible_actions"] == in_service,
        f"{case_id}: in-service coverage",
    )
    _require(
        coverage["resolved_eligible_actions"] == resolved,
        f"{case_id}: resolved eligible coverage",
    )
    _require(
        coverage["directional_yes_no_positions"] == yes_no,
        f"{case_id}: directional Yea/Nay coverage",
    )
    _require(coverage["present_actions"] == present, f"{case_id}: Present coverage")
    _require(coverage["not_voting_actions"] == not_voting, f"{case_id}: Not Voting coverage")
    _require(
        coverage["missing_evidence_actions"] == missing,
        f"{case_id}: missing evidence coverage",
    )
    _require(
        coverage["outside_service_actions"] == outside_service,
        f"{case_id}: outside-service coverage",
    )
    _require(
        coverage["complete_episodes"] == complete_episodes,
        f"{case_id}: complete episode coverage",
    )
    _require(
        coverage["partial_episodes"] == partial_episodes,
        f"{case_id}: partial episode coverage",
    )
    _require(
        yes_no + present + not_voting + missing == len(eligible_actions),
        f"{case_id}: eligible-status arithmetic",
    )
    _require(
        len(eligible_actions) == len(eligible_ids),
        f"{case_id}: missing eligible member action",
    )


def validate_accepted_references(
    corpus: dict[str, Any], known_source_ids: set[str] | None = None
) -> list[str]:
    known_source_ids = known_source_ids or _known_source_ids()
    _require(corpus.get("schema_version") == "editorial_semantic_ir_v1", "accepted schema")
    _require(
        corpus.get("corpus_kind") == "accepted_semantic_reference_corpus",
        "accepted corpus kind",
    )
    _require(
        corpus.get("review_state") == ACCEPTED_STATE,
        "accepted corpus review state",
    )
    cases = corpus.get("cases")
    _require(isinstance(cases, list) and len(cases) == 12, "accepted case count")
    case_ids = [case.get("case_id", "") for case in cases]
    _require(not _duplicates(case_ids), "duplicate development case ID")

    all_proposition_ids: list[str] = []
    for case in cases:
        case_id = case.get("case_id", "")
        _require(bool(ID_PATTERNS["development"].fullmatch(case_id)), f"{case_id}: case ID")
        _require(case.get("case_kind") == ACCEPTED_STATE, f"{case_id}: kind")
        _require(case.get("review_state") == ACCEPTED_STATE, f"{case_id}: review state")
        case_scope = case.get("case_scope")
        _require(
            case_scope in {"full_record", "focused_invariant_fixture"},
            f"{case_id}: case scope",
        )
        _require(
            case_scope != "focused_invariant_fixture"
            or bool(case.get("scope_boundary")),
            f"{case_id}: focused fixture lacks scope boundary",
        )
        _require(
            case_scope != "focused_invariant_fixture"
            or bool(case.get("compiler_scope")),
            f"{case_id}: focused fixture lacks compiler scope",
        )
        _require(
            bool(case.get("external_review_decisions")),
            f"{case_id}: external review decisions",
        )
        refs = case["source_references"]
        for path in refs["dossier_paths"]:
            _require((ROOT / path).is_file(), f"{case_id}: missing dossier {path}")
        _require(
            set(refs["source_ids"]) <= known_source_ids,
            f"{case_id}: unknown source ID",
        )

        shared = case["shared_semantics"]
        actions = shared["actions"]
        action_ids = [action["action_id"] for action in actions]
        accepted = {
            action["action_id"]
            for action in actions
            if action["eligibility"]["decision"] == "accepted"
        }
        _require(not _duplicates(action_ids), f"{case_id}: duplicate action ID")
        for action in actions:
            action_id = action["action_id"]
            _require(bool(ID_PATTERNS["action"].fullmatch(action_id)), f"{case_id}: action ID")
            _require(
                action["eligibility"]["parent_context_used"] is False,
                f"{case_id}: parent context established eligibility",
            )
            _require(
                set(action["source_ids"]) <= set(refs["source_ids"]),
                f"{case_id}: action source outside reference set",
            )

        episodes = shared["episodes"]
        episode_ids = [episode["episode_id"] for episode in episodes]
        _require(not _duplicates(episode_ids), f"{case_id}: duplicate episode ID")
        for episode in episodes:
            _require(
                set(episode["action_ids"]) <= set(action_ids),
                f"{case_id}: episode has unknown action",
            )
            _require(
                set(episode["action_ids"]) <= accepted,
                f"{case_id}: rejected action assigned to episode",
            )

        families = shared["policy_families"]
        family_ids = [family["policy_family_id"] for family in families]
        _require(not _duplicates(family_ids), f"{case_id}: duplicate family ID")
        for family in families:
            _require(
                set(family["episode_ids"]) <= set(episode_ids),
                f"{case_id}: family has unknown episode",
            )

        traits = shared.get("policy_traits", [])
        trait_ids = [trait["trait_id"] for trait in traits]
        _require(not _duplicates(trait_ids), f"{case_id}: duplicate policy trait")
        for trait in traits:
            _require(
                set(trait["action_ids"]) <= accepted,
                f"{case_id}: policy trait has non-accepted action",
            )
            _require(
                trait["review_state"]
                in {"reviewed_reusable_input", "human_review_pending"},
                f"{case_id}: policy trait review state",
            )
        if case_scope == "focused_invariant_fixture":
            compiler_scope = case["compiler_scope"]
            scoped_traits = set(
                compiler_scope["included_policy_trait_refs"]
                + compiler_scope["limiting_policy_trait_refs"]
            )
            _require(
                scoped_traits <= set(trait_ids),
                f"{case_id}: compiler scope has unknown trait",
            )

        for member in case["member_semantics"]["members"]:
            member_action_ids = [item["action_id"] for item in member["actions"]]
            _require(
                set(member_action_ids) <= set(action_ids),
                f"{case_id}: member has unknown action",
            )
            _require(not _duplicates(member_action_ids), f"{case_id}: duplicate member action")
            _validate_coverage(case_id, member, actions, episodes)

        for constraint in shared["source_render_constraints"]:
            _require(
                constraint["presentation_target"] == "source_note",
                f"{case_id}: source constraint target",
            )
            _require(
                set(constraint["action_ids"]) <= set(action_ids),
                f"{case_id}: source constraint has unknown action",
            )
            _require(
                set(constraint["source_ids"]) <= set(refs["source_ids"]),
                f"{case_id}: source constraint has unknown source",
            )

        propositions = case["proposition_graph"]["propositions"]
        proposition_ids = [item["proposition_id"] for item in propositions]
        _require(not _duplicates(proposition_ids), f"{case_id}: duplicate proposition")
        all_proposition_ids.extend(proposition_ids)
        behavioral_action_ids: set[str] = set()
        for proposition in propositions:
            prop_id = proposition["proposition_id"]
            _require(bool(ID_PATTERNS["proposition"].fullmatch(prop_id)), f"{case_id}: prop ID")
            _require(
                proposition["review_state"] == ACCEPTED_STATE,
                f"{case_id}: prop state",
            )
            role = proposition["semantic_role"]
            target = proposition["presentation_target"]
            _require(role in {"behavioral", "synthesis"}, f"{case_id}: prop role")
            _require(target in PRESENTATION_TARGETS, f"{case_id}: presentation target")
            if role == "behavioral":
                _require(
                    target in SECTION_RENDERED_TARGETS,
                    f"{case_id}: behavioral proposition lacks analytical section",
                )
                behavioral_action_ids.update(proposition["evidence_action_ids"])
            else:
                _require(
                    target
                    in {"meaningful_limitations", "conclusion_only", "omitted"},
                    f"{case_id}: synthesis presentation target",
                )
            _require(
                set(proposition["evidence_action_ids"]) <= set(action_ids),
                f"{case_id}: proposition has unknown action",
            )
            _require(
                set(proposition["evidence_episode_ids"]) <= set(episode_ids),
                f"{case_id}: proposition has unknown episode",
            )
            if proposition["proposition_type"] == "trajectory":
                _require(
                    len(proposition["evidence_episode_ids"]) == 1,
                    f"{case_id}: trajectory must use one episode",
                )
                episode_id = proposition["evidence_episode_ids"][0]
                episode = next(item for item in episodes if item["episode_id"] == episode_id)
                _require(
                    len(episode["action_ids"]) >= 2,
                    f"{case_id}: single-action trajectory",
                )
            if proposition["proposition_type"] == "repeated_pattern":
                _require(
                    len(set(proposition["evidence_episode_ids"])) >= 2,
                    f"{case_id}: repeated pattern needs independent episodes",
                )

        composition = case["composition"]
        owned = composition["presentation_ownership"]
        owned_ids = [value for values in owned.values() for value in values]
        _require(not _duplicates(owned_ids), f"{case_id}: proposition section collision")
        _require(set(owned_ids) == set(proposition_ids), f"{case_id}: proposition ownership")
        for proposition in propositions:
            _require(
                proposition["proposition_id"]
                in owned.get(proposition["presentation_target"], []),
                f"{case_id}: presentation ownership mismatch",
            )
            related = (
                proposition["relationships"]["supported_by"]
                + proposition["relationships"]["limited_by"]
            )
            _require(set(related) <= set(proposition_ids), f"{case_id}: bad prop relation")
        conclusion_plan = composition["conclusion_plan"]
        _require(
            set(conclusion_plan["primary_proposition_ids"]) <= set(proposition_ids),
            f"{case_id}: unknown primary conclusion proposition",
        )
        _require(
            set(conclusion_plan["limiting_proposition_ids"]) <= set(proposition_ids),
            f"{case_id}: unknown limiting proposition",
        )
        coverage_boundary_ids = [
            boundary["boundary_id"] for boundary in composition["coverage_boundaries"]
        ]
        method_boundary_ids = [
            boundary["boundary_id"] for boundary in composition["method_boundaries"]
        ]
        _require(
            not _duplicates(coverage_boundary_ids),
            f"{case_id}: duplicate coverage boundary",
        )
        _require(
            not _duplicates(method_boundary_ids),
            f"{case_id}: duplicate method boundary",
        )
        for boundary in composition["coverage_boundaries"]:
            _require(
                boundary["presentation_target"] == "coverage_note",
                f"{case_id}: coverage boundary target",
            )
            _require(
                set(boundary["action_ids"]) <= accepted,
                f"{case_id}: coverage boundary has non-eligible action",
            )
        for boundary in composition["method_boundaries"]:
            _require(
                boundary["presentation_target"] == "method_note",
                f"{case_id}: method boundary target",
            )
            _require(
                set(boundary["action_ids"]) <= set(action_ids),
                f"{case_id}: method boundary has unknown action",
            )

        accounting = case["action_accounting"]
        declared_behavioral = set(accounting["behavioral_proposition_action_ids"])
        reason_ids = [
            reason["action_id"] for reason in accounting["non_proposition_reasons"]
        ]
        _require(
            declared_behavioral == behavioral_action_ids,
            f"{case_id}: behavioral action accounting drift",
        )
        _require(
            not _duplicates(reason_ids),
            f"{case_id}: duplicate non-proposition reason",
        )
        _require(
            declared_behavioral.isdisjoint(reason_ids),
            f"{case_id}: action both behavioral and non-proposition",
        )
        _require(
            declared_behavioral | set(reason_ids) == accepted,
            f"{case_id}: incomplete accepted-action accounting",
        )
        _require(
            declared_behavioral <= accepted,
            f"{case_id}: rejected action in behavioral proposition",
        )
        _require(
            composition["render_plan"]["analytical_additions_allowed"] is False,
            f"{case_id}: renderer may add analysis",
        )

    _require(not _duplicates(all_proposition_ids), "proposition IDs must be corpus-stable")
    return case_ids


# Compatibility name for callers that validate a corpus passed explicitly.
validate_development = validate_accepted_references


def _walk_forbidden(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in HELD_OUT_FORBIDDEN_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_walk_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_forbidden(child, f"{path}[{index}]"))
    return found


def validate_held_out(
    corpus: dict[str, Any], known_source_ids: set[str] | None = None
) -> list[str]:
    known_source_ids = known_source_ids or _known_source_ids()
    _require(corpus.get("schema_version") == "editorial_semantic_ir_v1", "held schema")
    _require(corpus.get("corpus_kind") == "held_out_input_corpus", "held kind")
    _require("review_state" not in corpus, "held corpus leaks expected review state")
    cases = corpus.get("cases")
    _require(isinstance(cases, list) and 4 <= len(cases) <= 5, "held case count")
    case_ids = [case.get("case_id", "") for case in cases]
    _require(not _duplicates(case_ids), "duplicate held-out case ID")
    for case in cases:
        case_id = case.get("case_id", "")
        _require(bool(ID_PATTERNS["held_out"].fullmatch(case_id)), f"{case_id}: case ID")
        _require(case.get("case_kind") == "held_out_input", f"{case_id}: kind")
        for path in case["authoritative_inputs"]["dossier_paths"]:
            _require((ROOT / path).is_file(), f"{case_id}: missing input {path}")
        inputs = case["authoritative_inputs"]
        referenced_text = "\n".join(
            (ROOT / path).read_text(encoding="utf-8") for path in inputs["dossier_paths"]
        )
        _require(
            all(
                source_id in known_source_ids or source_id in referenced_text
                for source_id in inputs["source_ids"]
            ),
            f"{case_id}: unknown source ID",
        )
        _require(
            all(mutation_id in referenced_text for mutation_id in inputs["mutation_ids"]),
            f"{case_id}: unknown mutation ID",
        )
        forbidden = _walk_forbidden(case)
        _require(not forbidden, f"{case_id}: held-out answers leaked: {forbidden}")
        for member in case["member_action_statuses"]:
            for action in member["actions"]:
                _require(action["status"] in STATUS_VALUES, f"{case_id}: invalid status")
                _require(
                    action["action_id"] in inputs["action_ids"],
                    f"{case_id}: member action outside input set",
                )
    return case_ids


def validate_review_packet(
    packet: dict[str, Any], candidate_ids: list[str], held_out_ids: list[str]
) -> None:
    _require(packet.get("review_state") == REVIEW_STATE, "review packet state")
    _require(
        packet.get("external_review_disposition")
        == "decisions_applied_candidate_revision",
        "review packet external decision disposition",
    )
    _require(packet.get("candidate_case_ids") == candidate_ids, "review packet case order")
    _require(packet.get("development_candidate_count") == len(candidate_ids), "packet count")
    _require(packet.get("held_out_case_ids") == held_out_ids, "packet held-out order")
    _require(packet.get("held_out_input_count") == len(held_out_ids), "held-out count")
    coverage_matrix = packet.get("coverage_matrix", {})
    _require(len(coverage_matrix) == 20, "twenty structural purposes must be mapped")
    known_cases = set(candidate_ids + held_out_ids)
    _require(
        all(values and set(values) <= known_cases for values in coverage_matrix.values()),
        "coverage matrix has unknown or empty case mapping",
    )
    serialized_packet = json.dumps(packet, sort_keys=True)
    _require(
        "external_review_questions" not in serialized_packet,
        "review packet still presents resolved questions",
    )
    forbidden = {"human_approved", "gold_benchmark", "production_eligible"}
    _require(
        not any(token in serialized_packet for token in forbidden),
        "packet crosses gate",
    )


def validate_acceptance_receipt(
    receipt: dict[str, Any], accepted_ids: list[str]
) -> None:
    _require(
        receipt.get("receipt_kind")
        == "editorial_semantic_ir_v1_external_acceptance",
        "acceptance receipt kind",
    )
    _require(
        receipt.get("review_state") == ACCEPTED_STATE,
        "acceptance receipt state",
    )
    _require(
        receipt.get("corpus_kind") == "accepted_semantic_reference_corpus",
        "acceptance receipt corpus kind",
    )
    _require(
        receipt.get("accepted_case_ids") == accepted_ids,
        "acceptance receipt case order",
    )
    _require(
        receipt.get("accepted_case_count") == len(accepted_ids),
        "acceptance receipt case count",
    )
    boundary = receipt.get("external_acceptance_boundary", {})
    _require(
        boundary.get("semantic_test_reference") is True,
        "semantic reference acceptance missing",
    )
    forbidden_authority = {
        "public_editorial_approval",
        "benchmark_promotion_outside_semantic_contract",
        "production_eligible",
        "persistence_authorized",
        "publication_authorized",
        "registry_inclusion_authorized",
        "deployment_authorized",
    }
    _require(
        all(boundary.get(key) is False for key in forbidden_authority),
        "acceptance receipt crosses publication or production boundary",
    )
    held = receipt.get("held_out", {})
    held_digest = hashlib.sha256(HELD_OUT.read_bytes()).hexdigest()
    _require(held.get("case_count") == 4, "receipt held-out count")
    _require(
        held.get("evaluation_state") == "unevaluated_input_only",
        "receipt held-out state",
    )
    _require(
        held.get("phase_b_start_sha256") == held_digest,
        "held-out file changed from Phase B baseline",
    )
    _require(
        held.get("expected_answers_present") is False,
        "receipt claims held-out answers",
    )


def run() -> dict[str, Any]:
    started = time.perf_counter()
    schema = _load(SCHEMA)
    _require(schema.get("$schema", "").endswith("draft-07/schema#"), "schema draft")
    _require(
        "definitions" in schema and "developmentCase" in schema["definitions"],
        "schema definitions",
    )
    accepted = _load(ACCEPTED)
    receipt = _load(ACCEPTANCE_RECEIPT)
    held_out = _load(HELD_OUT)
    packet = _load(REVIEW_JSON)
    known_source_ids = _known_source_ids()
    accepted_ids = validate_accepted_references(accepted, known_source_ids)
    held_out_ids = validate_held_out(held_out, known_source_ids)
    validate_review_packet(packet, accepted_ids, held_out_ids)
    validate_acceptance_receipt(receipt, accepted_ids)
    elapsed = time.perf_counter() - started
    return {
        "status": "pass",
        "accepted_semantic_references": len(accepted_ids),
        "held_out_inputs": len(held_out_ids),
        "elapsed_seconds": round(elapsed, 4),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine JSON")
    args = parser.parse_args(argv)
    try:
        result = run()
    except SemanticValidationError as exc:
        print(f"Semantic IR validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True) if args.json else (
        "Semantic IR validation passed: "
        f"{result['accepted_semantic_references']} accepted references, "
        f"{result['held_out_inputs']} held-out, "
        f"{result['elapsed_seconds']:.4f}s"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
