"""Build the governed M10-R1 routing ledger and exception resolution receipt."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.editorial_presentations.compiler import (  # noqa: E402
    REQUIRED_DETACHED_DECISIONS,
    accepted_substantive_action_ids_for_artifact,
    approval_subject_for_artifact,
    canonical_digest,
    detached_receipt_matches,
    fallback_display,
    semantic_review_exception_resolution_matches,
    semantic_review_exception_subject_for_artifact,
    semantic_tier_for_artifact,
)
from backend.app.editorial_presentations.validation import (  # noqa: E402
    validate_public_issue_presentation,
)
from backend.app.editorial_presentations.review_state_catalog import (  # noqa: E402
    catalog_key,
    receipt_projection_key,
    validate_public_catalog,
)


PUBLIC_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/public_interface_candidates"
    / "f000477_justice_public_safety_119_v1"
)
SEMANTIC_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations"
    / "f000477_justice_public_safety_119_v2"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/publication_preparations"
    / "f000477_justice_public_safety_119_v1"
)
DECISION_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions"
    / "f000477_justice_public_safety_119_v1"
)

ROUTING_AUTHORITY = OUTPUT_ROOT / (
    "f000477_justice_public_safety_119_semantic_routing_"
    "correction_authorization_v1.json"
)
PRODUCTION_APPROVAL = OUTPUT_ROOT / (
    "f000477_justice_public_safety_119_production_eligibility_approval_v1.json"
)
CANDIDATE = PUBLIC_ROOT / "public_presentation_candidate.json"
COMPILER_INPUT = SEMANTIC_ROOT / "frozen_final_compiler_input.json"
COMPILED_IR = SEMANTIC_ROOT / "frozen_final_compiled_semantic_ir.json"
EXACT_ACTION_LEDGER = PUBLIC_ROOT / "exact_action_ledger.json"
ACTION_SOURCE_CONTRACT = PUBLIC_ROOT / "full_record_action_source_contract.json"
SOURCE_MANIFEST = (
    ROOT
    / "docs/editorial/full_record_reviews/source_readiness"
    / "f000477_justice_public_safety_119_official_source_manifest_v1.json"
)
ACTION_IMPLEMENTATION = DECISION_ROOT / "decision_implementation_bundle.json"
EPISODE_IMPLEMENTATION = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations"
    / "f000477_justice_public_safety_119_v1/episode_implementation_bundle.json"
)

EXPECTED_FILES = {
    ROUTING_AUTHORITY: "059a3bb4008909009aaef0e365ac8d94b8b53fd35bd37455bcba7312c3d6ae7a",
    PRODUCTION_APPROVAL: "432123d7e27a3505e0e8039594a8b15fa260a60205ff56b52c78bfddca9c3ca9",
    COMPILED_IR: "6a385770ce670e19329e56dfde13c48ae4b581bd740eac7dd7a54bed692abc14",
    CANDIDATE: "9254e396c85b442e605203f2ebb48f4bbc28cb1c4709ad10bbb084445f5c6021",
    PUBLIC_ROOT
    / "f000477_justice_public_safety_119_user_launch_ratification_v1.json": "eb5f6aa7775f8765c1319d80849dfeedbb41c85f8e30f30a21a53819a0f615d8",
    PUBLIC_ROOT
    / "user_launch_ratification_receipt.json": "40754c51f1832afbeaaccb9624dc7c505a2882b13e6b8f6095cc14fba1f8aef4",
    PUBLIC_ROOT
    / "f000477_justice_public_safety_119_m5r1_delegated_semantic_ir_acceptance_v1.json": "23d27f84ce196380b6d02ca2d1a2e679847e7a0855c00d60b6df1542d499b405",
    PUBLIC_ROOT
    / "full_record_semantic_validation_receipt.json": "86747bc3777c0b514c1d1089afa8274a66792e780b9b5d93823e1f98d937b1a2",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _serialized(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _normalized_file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _raw_file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract_file_digest(path: Path) -> str:
    expected = EXPECTED_FILES.get(path)
    if expected is not None:
        return expected
    return _normalized_file_digest(path)


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_subject_sha256"] = canonical_digest(result)
    return result


def _write_or_check(path: Path, value: dict[str, Any], *, check: bool) -> None:
    raw = _serialized(value)
    if check:
        if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != raw:
            raise ValueError(
                f"{path.relative_to(ROOT)} differs from deterministic output"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _validate_schema(value: dict[str, Any], schema_name: str) -> None:
    schema = _load(ROOT / "docs/methodology" / schema_name)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(value)


def _verify_content_subject(value: dict[str, Any], *, path: Path) -> None:
    subject = copy.deepcopy(value)
    claimed = subject.pop("content_subject_sha256", None)
    if claimed != canonical_digest(subject):
        raise ValueError(f"{path.relative_to(ROOT)} content-subject digest differs")


def _preflight() -> None:
    for path, expected in EXPECTED_FILES.items():
        actual = _raw_file_digest(path)
        normalized = _normalized_file_digest(path)
        if expected not in {actual, normalized}:
            raise ValueError(
                f"{path.relative_to(ROOT)} final-file digest differs: "
                f"raw={actual}, lf={normalized}"
            )
    for path in (ROUTING_AUTHORITY, PRODUCTION_APPROVAL):
        _verify_content_subject(_load(path), path=path)


def _trigger(
    trigger_id: str,
    trigger_type: str,
    *,
    triggered: bool,
    action_ids: list[str] | None = None,
    episode_ids: list[str] | None = None,
    eligibility_state: str,
    enters_substantive_denominator: bool,
    true_semantic_blocker: bool,
    human_review_can_resolve: bool,
    controlling_approval_or_boundary: str,
    routing_treatment: str,
) -> dict[str, Any]:
    return {
        "trigger_id": trigger_id,
        "trigger_type": trigger_type,
        "triggered": triggered,
        "action_ids": sorted(action_ids or []),
        "episode_ids": sorted(episode_ids or []),
        "eligibility_state": eligibility_state,
        "enters_substantive_denominator": enters_substantive_denominator,
        "true_semantic_blocker": true_semantic_blocker,
        "human_review_can_resolve": human_review_can_resolve,
        "controlling_approval_or_boundary": controlling_approval_or_boundary,
        "routing_treatment": routing_treatment,
    }


def build_routing_trigger_ledger() -> dict[str, Any]:
    input_envelope = _load(COMPILER_INPUT)
    compiled_envelope = _load(COMPILED_IR)
    candidate = _load(CANDIDATE)
    exact_records = {
        item["canonical_action_id"]: item
        for item in _load(EXACT_ACTION_LEDGER)["records"]
    }
    compiler_input = input_envelope["compiler_input"]
    shared = compiler_input["shared_semantics"]
    member = compiled_envelope["compiled_ir"]["members"][0]
    if member["review_route"] != "human_exception_required":
        raise ValueError("compiled review route changed")
    eligibility = {
        action["action_id"]: action["eligibility"]["decision"]
        for action in shared["actions"]
    }
    accepted = accepted_substantive_action_ids_for_artifact(candidate)
    triggers: list[dict[str, Any]] = []
    nonaccepted = {
        action_id: state
        for action_id, state in eligibility.items()
        if state != "accepted"
    }
    boundary_for_action = {
        action_id: boundary["boundary_id"]
        for boundary in candidate["compiled_semantic_meaning"][
            "presentation_boundaries"
        ]
        if boundary.get("boundary_type")
        in {"context_only_control_exclusion", "exact_action_eligibility"}
        for action_id in boundary.get("action_ids", [])
    }
    for action_id, state in sorted(nonaccepted.items()):
        episode_id = exact_records[action_id].get("episode_id")
        triggers.append(
            _trigger(
                f"nonaccepted:{action_id}",
                "nonaccepted_action",
                triggered=True,
                action_ids=[action_id],
                episode_ids=[episode_id] if episode_id else [],
                eligibility_state=state,
                enters_substantive_denominator=False,
                true_semantic_blocker=False,
                human_review_can_resolve=True,
                controlling_approval_or_boundary=boundary_for_action[action_id],
                routing_treatment=(
                    "retain_visible_context_only_nonproposition_control"
                    if state == "context_only"
                    else "retain_visible_rejected_no_safe_ledger_only_control"
                ),
            )
        )
    for constraint in shared["source_render_constraints"]:
        action_ids = constraint["action_ids"]
        substantive = bool(set(action_ids) & accepted)
        semantic_block = (
            constraint["semantic_effect"] == "blocks_behavioral_propositions"
            and substantive
        )
        triggers.append(
            _trigger(
                f"source:{constraint['constraint_id']}",
                "source_render_constraint",
                triggered=True,
                action_ids=action_ids,
                episode_ids=sorted(
                    {
                        exact_records[action_id]["episode_id"]
                        for action_id in action_ids
                        if exact_records[action_id].get("episode_id")
                    }
                ),
                eligibility_state=(
                    "accepted_substantive" if substantive else "noncounting_control"
                ),
                enters_substantive_denominator=substantive,
                true_semantic_blocker=semantic_block,
                human_review_can_resolve=not semantic_block,
                controlling_approval_or_boundary=(
                    "launch-risk:roll-128:v1"
                    if action_ids == ["house:119:1:128"]
                    else boundary_for_action[action_ids[0]]
                ),
                routing_treatment=(
                    "retain_bounded_interpretation_and_rendering_limitation"
                    if constraint["semantic_effect"] == "limits_argument_rendering"
                    else "retain_noncounting_source_block_as_visible_control"
                ),
            )
        )
    mixed = [
        item
        for item in member["proposition_graph"]["propositions"]
        if item["proposition_type"] == "trajectory" and item["direction"] == "mixed"
    ]
    for proposition in mixed:
        triggers.append(
            _trigger(
                f"mixed:{proposition['proposition_id']}",
                "mixed_trajectory",
                triggered=True,
                action_ids=proposition["evidence_action_ids"],
                episode_ids=proposition["evidence_episode_ids"],
                eligibility_state="accepted_substantive",
                enters_substantive_denominator=True,
                true_semantic_blocker=False,
                human_review_can_resolve=True,
                controlling_approval_or_boundary=(
                    "launch-risk:semantic-ir:mechanism-divide:v1"
                ),
                routing_treatment="retain_explicit_limiting_proposition",
            )
        )
    pending_relationships = [
        item
        for item in shared.get("trait_relationships", [])
        if item.get("review_state") == "human_review_pending"
    ]
    triggers.append(
        _trigger(
            "compiler-condition:pending-shared-review",
            "pending_shared_review",
            triggered=bool(pending_relationships),
            eligibility_state="not_applicable",
            enters_substantive_denominator=False,
            true_semantic_blocker=False,
            human_review_can_resolve=True,
            controlling_approval_or_boundary=(
                "delegated-semantic-ir-acceptance:f000477:justice_public_safety:119:v1"
            ),
            routing_treatment="no_pending_shared_relationship_review",
        )
    )
    nondirectional = (
        member["coverage"]["present_actions"] + member["coverage"]["not_voting_actions"]
    )
    triggers.append(
        _trigger(
            "compiler-condition:present-or-not-voting",
            "present_or_not_voting",
            triggered=bool(nondirectional),
            eligibility_state="accepted_non_directional",
            enters_substantive_denominator=True,
            true_semantic_blocker=False,
            human_review_can_resolve=True,
            controlling_approval_or_boundary="Editorial Semantic IR V1 coverage contract",
            routing_treatment="none_present_or_not_voting",
        )
    )
    outside_service = member["coverage"]["outside_service_actions"]
    triggers.append(
        _trigger(
            "compiler-condition:outside-service",
            "outside_service",
            triggered=bool(outside_service),
            eligibility_state="accepted_outside_verified_service",
            enters_substantive_denominator=True,
            true_semantic_blocker=False,
            human_review_can_resolve=True,
            controlling_approval_or_boundary="Editorial Semantic IR V1 service boundary",
            routing_treatment="none_outside_service",
        )
    )
    single_episode = member["coverage"]["complete_episodes"] <= 1
    triggers.append(
        _trigger(
            "compiler-condition:single-episode-record",
            "single_episode_record",
            triggered=single_episode,
            eligibility_state="accepted_substantive",
            enters_substantive_denominator=True,
            true_semantic_blocker=False,
            human_review_can_resolve=True,
            controlling_approval_or_boundary="Editorial Semantic IR V1 synthesis threshold",
            routing_treatment="not_applicable_32_complete_episodes",
        )
    )
    true_blockers = [item for item in triggers if item["true_semantic_blocker"]]
    if true_blockers:
        raise ValueError("routing ledger found an accepted substantive blocker")
    ledger = _seal(
        {
            "schema_version": "semantic_routing_trigger_ledger_v1",
            "ledger_id": "semantic-routing-trigger-ledger:f000477:justice_public_safety:119:v1",
            "artifact_id": candidate["artifact_identity"]["artifact_id"],
            "review_route": member["review_route"],
            "triggers": triggers,
            "summary": {
                "triggered_condition_count": sum(
                    1 for item in triggers if item["triggered"]
                ),
                "accepted_substantive_action_count": len(accepted),
                "noncounting_control_count": len(nonaccepted),
                "accepted_substantive_blocker_count": 0,
                "all_exception_choices_content_bound": True,
                "resulting_semantic_tier": semantic_tier_for_artifact(candidate),
            },
        }
    )
    _validate_schema(ledger, "semantic_routing_trigger_ledger_v1.schema.json")
    return ledger


def _approval_binding(
    role: str,
    path: Path,
    *,
    artifact_id: str | None = None,
) -> dict[str, str]:
    value = _load(path)
    return {
        "role": role,
        "artifact_id": artifact_id or value["artifact_id"],
        "content_subject_sha256": value["content_subject_sha256"],
        "final_file_sha256": _contract_file_digest(path),
        "decision": "approved",
    }


def build_exception_resolution(ledger: dict[str, Any]) -> dict[str, Any]:
    candidate = _load(CANDIDATE)
    ratification = (
        PUBLIC_ROOT
        / "f000477_justice_public_safety_119_user_launch_ratification_v1.json"
    )
    ratification_receipt = PUBLIC_ROOT / "user_launch_ratification_receipt.json"
    approval_bindings = [
        _approval_binding(
            "semantic_ir_acceptance",
            PUBLIC_ROOT
            / "f000477_justice_public_safety_119_m5r1_delegated_semantic_ir_acceptance_v1.json",
        ),
        _approval_binding(
            "semantic_validation",
            PUBLIC_ROOT / "full_record_semantic_validation_receipt.json",
        ),
        _approval_binding("user_ratification", ratification),
        _approval_binding("risk_treatments", ratification_receipt),
        _approval_binding(
            "full_record_synthesis_approval",
            ratification,
            artifact_id=(
                "full-record-synthesis-approval-projection:"
                "f000477:justice_public_safety:119:v1"
            ),
        ),
        _approval_binding("production_eligibility", PRODUCTION_APPROVAL),
        _approval_binding(
            "semantic_routing_correction_authorization", ROUTING_AUTHORITY
        ),
    ]
    receipt = {
        "schema_version": "semantic_review_exception_resolution_v1",
        "receipt_id": (
            "semantic-review-exception-resolution:f000477:justice_public_safety:119:v1"
        ),
        "status": "approved",
        "binding": semantic_review_exception_subject_for_artifact(candidate),
        "routing_trigger_ledger_sha256": ledger["content_subject_sha256"],
        "approval_bindings": approval_bindings,
        "resolution": {
            "all_triggers_accounted": True,
            "accepted_substantive_blocker_count": 0,
            "compiled_ir_unchanged": True,
            "wording_and_mappings_unchanged": True,
            "resulting_semantic_tier": "reviewed_conclusion",
        },
        "reviewer": {
            "reviewer_id": "reviewer:political-fingerprint-authority-thread",
            "authority": "delegated_product_methodology_editorial_authority_v1",
        },
        "decision_timestamp": _load(ROUTING_AUTHORITY)["decision"][
            "decision_timestamp"
        ],
    }
    _validate_schema(receipt, "semantic_review_exception_resolution_v1.schema.json")
    if not semantic_review_exception_resolution_matches(receipt, artifact=candidate):
        raise ValueError("exception resolution does not bind the frozen candidate")
    return receipt


def _public_source(source: dict[str, Any]) -> dict[str, str]:
    projection = source.get("neutral_projection", {})
    name = projection.get("official_action_description") or source["source_id"]
    return {
        "source_id": source["source_id"],
        "source_type": source["source_type"],
        "name": name,
        "url": source["url"],
    }


def build_public_review_state_projection() -> dict[str, Any]:
    candidate = _load(CANDIDATE)
    contract = _load(ACTION_SOURCE_CONTRACT)
    manifest = _load(SOURCE_MANIFEST)
    action_implementation = _load(ACTION_IMPLEMENTATION)
    episode_implementation = _load(EPISODE_IMPLEMENTATION)
    exact_records = {
        item["canonical_action_id"]: item
        for item in _load(EXACT_ACTION_LEDGER)["records"]
    }
    accepted = accepted_substantive_action_ids_for_artifact(candidate)
    implementation_records = {
        item["action_id"]: item
        for item in action_implementation["implementation_records"]
    }
    episodes = {
        item["episode_id"]: item
        for item in episode_implementation["implemented_episodes"]
    }
    sources: dict[str, dict[str, Any]] = {}
    for action_sources in manifest["subject"]["action_sources"]:
        for source in action_sources["sources"]:
            existing = sources.setdefault(source["source_id"], source)
            if existing != source:
                raise ValueError("official source identity is inconsistent")
    if set(contract["actions"]) != set(exact_records):
        raise ValueError("source contract and full exact-action ledger differ")
    artifact_id = candidate["artifact_identity"]["artifact_id"]
    receipt_refs = [
        (
            "docs/editorial/full_record_reviews/interpretation_decisions/"
            "f000477_justice_public_safety_119_v1/"
            "f000477_justice_public_safety_119_m3bb_delegated_acceptance_v1.json"
        ),
        (
            "docs/editorial/full_record_reviews/interpretation_decisions/"
            "f000477_justice_public_safety_119_v1/"
            "f000477_justice_public_safety_119_m4b_delegated_episode_"
            "implementation_acceptance_v1.json"
        ),
        (
            "docs/editorial/full_record_reviews/public_interface_candidates/"
            "f000477_justice_public_safety_119_v1/"
            "f000477_justice_public_safety_119_m5r1_delegated_semantic_ir_"
            "acceptance_v1.json"
        ),
        (
            "docs/editorial/full_record_reviews/public_interface_candidates/"
            "f000477_justice_public_safety_119_v1/"
            "user_launch_ratification_receipt.json"
        ),
    ]
    receipts = []
    for action_id in sorted(accepted):
        ledger = exact_records[action_id]
        implementation = implementation_records[action_id]
        episode = episodes[ledger["episode_id"]]
        source_rule = contract["actions"][action_id]
        vote_sources = [
            _public_source(sources[source_id])
            for source_id in source_rule["vote_source_refs"]
        ]
        meaning_sources = [
            _public_source(sources[source_id])
            for source_id in source_rule["action_meaning_source_refs"]
        ]
        action_interpretation_id = implementation["record_id"]
        action_interpretation_sha256 = implementation["content_subject_sha256"]
        receipt = {
            "projection_key": receipt_projection_key(
                member_id="F000477",
                issue_id="JUSTICE_PUBLIC_SAFETY",
                congress_scope=[119],
                published_artifact_identity=artifact_id,
                canonical_action_id=action_id,
                action_interpretation_id=action_interpretation_id,
                action_interpretation_sha256=action_interpretation_sha256,
            ),
            "member_id": "F000477",
            "issue_id": "JUSTICE_PUBLIC_SAFETY",
            "congress_scope": [119],
            "published_artifact_identity": artifact_id,
            "canonical_action_id": action_id,
            "action_interpretation_id": action_interpretation_id,
            "action_interpretation_sha256": action_interpretation_sha256,
            "action_meaning_id": f"action-meaning:{action_id}:v1",
            "member_action": ledger["member_action"].title(),
            "interpretation_disposition": "interpreted_substantive_directional",
            "interpretation_status": "interpreted",
            "exact_action_meaning": ledger["governed_action_meaning"],
            "policy_question": episode["neutral_policy_question"],
            "episode_id": ledger["episode_id"],
            "vote_sources": vote_sources,
            "action_meaning_sources": meaning_sources,
            "interpretation_receipt_refs": receipt_refs,
            "review_scope": "full_defined_issue_record",
            "public_claim_class": "full_issue_synthesis",
            "caveats": sorted(set(ledger["limitations"] + episode["limitations"])),
            "projection_source": {
                "review_id": "full-review:f000477:justice_public_safety:119:m10r1:v1",
                "source_contract_id": contract["contract_id"],
                "source_manifest_sha256": contract["source_manifest"]["sha256"],
            },
        }
        receipts.append(receipt)
    teaser = candidate["editorial_wording"]["tier_display"]["reviewed_conclusion"][
        "teaser"
    ]["text"]
    entry = {
        "catalog_key": catalog_key(
            member_id="F000477",
            issue_id="JUSTICE_PUBLIC_SAFETY",
            congress_scope=[119],
            published_artifact_identity=artifact_id,
        ),
        "member_id": "F000477",
        "issue_id": "JUSTICE_PUBLIC_SAFETY",
        "congress_scope": [119],
        "published_artifact_identity": artifact_id,
        "semantic_tier": "reviewed_conclusion",
        "review_scope": "full_defined_issue_record",
        "review_completion_state": "complete",
        "public_claim_class": "full_issue_synthesis",
        "total_recorded_actions": 37,
        "review_friendly_actions": 35,
        "interpreted_actions": 35,
        "unresolved_actions": 0,
        "procedural_context_actions": 2,
        "present_actions": 0,
        "not_voting_actions": 0,
        "complete_episode_count": 32,
        "partial_episode_count": 0,
        "full_issue_synthesis_eligible": True,
        "benchmark_sample_available": True,
        "scope_bounded_teaser": {
            "text": teaser,
            "valid_scope": "full_defined_issue_record",
        },
        "public_status_label": "Full issue interpretation available",
        "exact_action_receipts": receipts,
    }
    validate_public_catalog(
        {"schema_version": "public_review_state_catalog_v1", "entries": [entry]}
    )
    return entry


def build_approved_publication_projection(
    resolution: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact = copy.deepcopy(_load(CANDIDATE))
    controls = artifact["controls"]
    controls["semantic"] = {
        "status": "accepted_semantic_reference",
        "validation_status": "passed",
    }
    controls["editorial"]["human_approval_status"] = "human_approved"
    controls["benchmark"]["status"] = "gold_benchmark"
    controls["production"]["eligible"] = True
    controls["publication"]["active"] = True
    controls["derived_semantic_tier"] = "reviewed_conclusion"
    controls["effective_public_tier"] = "receipts_only"
    controls["publication_gates_passed"] = False
    artifact["frontend_display"] = fallback_display()
    validate_public_issue_presentation(
        artifact,
        semantic_review_exception_resolution=resolution,
    )
    subject = approval_subject_for_artifact(artifact)
    approval = {
        "schema_version": "editorial_public_issue_approval_receipt_v1",
        "receipt_id": "approval-receipt:f000477-full-record-justice-119-m10r1",
        "status": "approved",
        "binding": subject,
        "approved_statement_ids": subject["statement_ids"],
        "approved_mapping_ids": subject["mapping_ids"],
        "reviewer": {
            "reviewer_id": "reviewer:dhart54",
            "authority": "editorial_publication_review_authority_v1",
        },
        "decision_timestamp": _load(PRODUCTION_APPROVAL)["decision"][
            "decision_timestamp"
        ],
        "limitations_sha256": subject["limitations_sha256"],
        "limitations_acknowledged": [
            {**item, "acknowledged": True}
            for item in artifact["provenance"]["review_limitations"]
        ],
        "decisions": copy.deepcopy(REQUIRED_DETACHED_DECISIONS),
        "publication_activation": {
            "active": False,
            "decision_scope": "out_of_scope",
        },
    }
    if not detached_receipt_matches(approval, expected_subject=subject):
        raise ValueError("full-record approval projection is not content-bound")
    return artifact, approval


def build(*, check: bool = False) -> dict[str, Any]:
    _preflight()
    ledger = build_routing_trigger_ledger()
    resolution = build_exception_resolution(ledger)
    public_review_state = build_public_review_state_projection()
    approved_projection, approval_projection = build_approved_publication_projection(
        resolution
    )
    _write_or_check(OUTPUT_ROOT / "routing_trigger_ledger.json", ledger, check=check)
    _write_or_check(
        OUTPUT_ROOT / "semantic_review_exception_resolution.json",
        resolution,
        check=check,
    )
    _write_or_check(
        OUTPUT_ROOT / "public_review_state_projection.json",
        public_review_state,
        check=check,
    )
    _write_or_check(
        OUTPUT_ROOT / "approved_public_presentation_projection.json",
        approved_projection,
        check=check,
    )
    _write_or_check(
        OUTPUT_ROOT / "full_record_publication_approval_projection.json",
        approval_projection,
        check=check,
    )
    return {
        "status": "pass",
        "review_route": resolution["binding"]["review_route"],
        "semantic_tier": resolution["resolution"]["resulting_semantic_tier"],
        "accepted_substantive_actions": ledger["summary"][
            "accepted_substantive_action_count"
        ],
        "noncounting_controls": ledger["summary"]["noncounting_control_count"],
        "accepted_substantive_blockers": 0,
        "routing_trigger_ledger_sha256": ledger["content_subject_sha256"],
        "exception_resolution_sha256": hashlib.sha256(
            _canonical_bytes(resolution)
        ).hexdigest(),
        "public_receipt_count": len(public_review_state["exact_action_receipts"]),
        "approved_projection_sha256": hashlib.sha256(
            _canonical_bytes(approved_projection)
        ).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
