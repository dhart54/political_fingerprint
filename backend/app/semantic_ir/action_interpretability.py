"""Deterministic validation for detached Shared Action interpretability candidates."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

from backend.app.etl.full_record_source_readiness import sha256_file


SCHEMA_VERSION = "action_interpretability_candidate_set_v1"
COMPLETE = "candidate_complete_for_semantic_review"
HOLD_STATES = {"source_enrichment_required", "insufficient_for_useful_interpretation"}
SUBSTANTIVE_FIELDS = {
    "policy_choice",
    "mechanism",
    "affected_entities",
    "direct_effect",
    "plain_language_meaning",
}
CHECK_NAMES = {
    "exact_identity_and_source_binding",
    "substantive_source_mappings",
    "mechanism_present_when_supported",
    "affected_entities_present_when_supported",
    "direct_effect_is_concrete",
    "shared_meaning_is_member_neutral",
    "proposal_outcome_enactment_separated",
    "exact_action_boundary_preserved",
    "downstream_claims_supported_or_omitted",
    "non_authorizing_state_preserved",
}
FORBIDDEN_SHARED_PATTERNS = (
    re.compile(r"\bfoushee\b", re.IGNORECASE),
    re.compile(r"\b(?:democrat(?:ic)?|republican|political party|party affiliation|party-line|member(?:'s)? party)\b", re.IGNORECASE),
    re.compile(r"\b[a-z][0-9]{6}\b", re.IGNORECASE),
    re.compile(r"\b(?:she|he|they) voted\b", re.IGNORECASE),
    re.compile(r"\b(?:official )?member (?:id|vote|action|position|status)\b", re.IGNORECASE),
    re.compile(r"\bnot voting\b", re.IGNORECASE),
    re.compile(r"\b(?:supported|opposed) (?:the|this) (?:bill|measure|amendment|proposal)\b", re.IGNORECASE),
)
UNSUPPORTED_ENACTMENT_PATTERNS = (
    re.compile(r"\bbecame law\b", re.IGNORECASE),
    re.compile(r"\bwas enacted\b", re.IGNORECASE),
    re.compile(r"\bsigned into law\b", re.IGNORECASE),
)
PREDICTION_PATTERNS = (
    re.compile(r"\blikely\b", re.IGNORECASE),
    re.compile(r"\bexpected to\b", re.IGNORECASE),
    re.compile(r"\bwould lead to\b", re.IGNORECASE),
    re.compile(r"\bwill cause\b", re.IGNORECASE),
)
VAGUE_TERMS = {
    "address",
    "framework",
    "institutional relationships",
    "support",
    "time-to-contract",
}
CONCRETE_VERBS = {
    "begin",
    "condition",
    "disclose",
    "exclude",
    "extend",
    "fund",
    "maintain",
    "mediate",
    "notify",
    "nullify",
    "prohibit",
    "report",
    "require",
    "rescind",
    "restrict",
    "screen",
    "submit",
}


class ActionInterpretabilityValidationError(ValueError):
    """Raised when a candidate violates the M14B contract."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validate(root: Path, artifact: dict[str, Any]) -> None:
    schema = load_json(root / "docs/semantic_ir/action_interpretability_v1.schema.json")
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(artifact),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise ActionInterpretabilityValidationError(
            f"action interpretability schema failure at {location}: {error.message}"
        )


def _semantic_text(candidate: dict[str, Any]) -> str:
    values: list[str] = [
        candidate["policy_choice"],
        candidate["mechanism"]["description"],
        candidate["direct_effect"],
        candidate["plain_language_meaning"],
        *candidate["affected_entities"],
        *candidate["limitations"],
    ]
    values.extend(item["claim"] for item in candidate["downstream_effects"])
    return "\n".join(values)


def qualify_candidate(candidate: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    source_ids = {item["source_id"] for item in readiness["sources"]}
    operative_ids = set(readiness["source_roles"]["operative_content_interpretation_input"])
    mapped_fields = {item["field"] for item in candidate["claim_source_mappings"]}
    mapped_ids = {item["source_id"] for item in candidate["claim_source_mappings"]}
    mapping_ids = {item["mapping_id"] for item in candidate["claim_source_mappings"]}
    expected_claims = {
        "policy_choice": candidate["policy_choice"],
        "mechanism": candidate["mechanism"]["description"],
        "affected_entities": "; ".join(candidate["affected_entities"]),
        "direct_effect": candidate["direct_effect"],
        "plain_language_meaning": candidate["plain_language_meaning"],
    }
    substantive_mappings_valid = all(
        any(
            mapping["field"] == field
            and mapping["claim"] == claim
            and mapping["source_id"] in operative_ids
            for mapping in candidate["claim_source_mappings"]
        )
        for field, claim in expected_claims.items()
    )
    limitations_mapped = all(
        any(
            mapping["field"] == "limitations"
            and mapping["claim"] == limitation
            and mapping["source_id"] in operative_ids
            for mapping in candidate["claim_source_mappings"]
        )
        for limitation in candidate["limitations"]
    )
    downstream_mappings_valid = all(
        set(item["source_mapping_ids"]) <= mapping_ids
        and all(
            mapping["field"] == "downstream_effects"
            and mapping["claim"] == item["claim"]
            for mapping in candidate["claim_source_mappings"]
            if mapping["mapping_id"] in item["source_mapping_ids"]
        )
        for item in candidate["downstream_effects"]
    )
    semantic_text = _semantic_text(candidate)
    direct_lower = candidate["direct_effect"].lower()
    concrete = any(re.search(rf"\b{re.escape(verb)}\w*\b", direct_lower) for verb in CONCRETE_VERBS)
    vague_unexplained = any(
        term in direct_lower and len(candidate["direct_effect"].split()) < 18
        for term in VAGUE_TERMS
    )
    member_neutral = not any(pattern.search(semantic_text) for pattern in FORBIDDEN_SHARED_PATTERNS)
    no_enactment_claim = not any(pattern.search(semantic_text) for pattern in UNSUPPORTED_ENACTMENT_PATTERNS)
    no_prediction = not any(pattern.search(semantic_text) for pattern in PREDICTION_PATTERNS)
    boundary = candidate["exact_action_boundary"]
    exact_boundary = (
        boundary["parent_package_meaning_projected"] is False
        and boundary["ungoverned_component_projection"] is False
        and boundary["proposal_effect"] == candidate["direct_effect"]
        and (
            readiness["house_action_stage"] != "amendment"
            or bool(operative_ids & mapped_ids)
        )
    )
    expected_sources = [
        {
            "source_id": item["source_id"],
            "source_type": item["source_type"],
            "content_class": item["content_class"],
            "raw_sha256": item["raw_provenance"]["sha256"],
            "neutral_projection_sha256": item["neutral_projection_sha256"],
        }
        for item in readiness["sources"]
    ]
    checks = {
        "exact_identity_and_source_binding": (
            candidate["exact_action_identity"] == readiness["exact_action_identity"]
            and candidate["legislative_stage"] == readiness["house_action_stage"]
            and candidate["action_date"] == readiness["official_action_date"]
            and candidate["governed_source_packet_sha256"] == readiness["source_packet_sha256"]
            and candidate["governed_sources"] == expected_sources
            and mapped_ids <= source_ids
        ),
        "substantive_source_mappings": (
            SUBSTANTIVE_FIELDS <= mapped_fields
            and substantive_mappings_valid
            and limitations_mapped
            and len(mapping_ids) == len(candidate["claim_source_mappings"])
        ),
        "mechanism_present_when_supported": bool(candidate["mechanism"]["type"] and candidate["mechanism"]["description"]),
        "affected_entities_present_when_supported": bool(candidate["affected_entities"]),
        "direct_effect_is_concrete": bool(candidate["direct_effect"]) and concrete and not vague_unexplained,
        "shared_meaning_is_member_neutral": member_neutral,
        "proposal_outcome_enactment_separated": (
            no_enactment_claim
            and boundary["enactment_status"] == "not_inferred_from_house_action"
            and bool(boundary["house_action_outcome"])
        ),
        "exact_action_boundary_preserved": exact_boundary,
        "downstream_claims_supported_or_omitted": no_prediction and downstream_mappings_valid,
        "non_authorizing_state_preserved": (
            candidate["authorizing"] is False
            and candidate["accepted"] is False
            and candidate["public"] is False
            and candidate["production_selectable"] is False
        ),
    }
    if set(checks) != CHECK_NAMES:
        raise AssertionError("qualification check registry differs")
    if candidate["candidate_state"] == COMPLETE:
        result = "pass" if all(checks.values()) else "fail"
    else:
        result = "hold" if candidate["candidate_state"] in HOLD_STATES else "fail"
    return {"result": result, "checks": checks}


def validate_candidate_set(root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    _schema_validate(root, artifact)
    if artifact["schema_version"] != SCHEMA_VERSION:
        raise ActionInterpretabilityValidationError("unsupported schema version")
    if any(artifact[key] for key in ("authorizing", "accepted", "public", "production_selectable")):
        raise ActionInterpretabilityValidationError("candidate set became authorizing or public")

    readiness_binding = artifact["input_bindings"]["source_readiness"]
    readiness_path = root / readiness_binding["path"]
    if file_sha256(readiness_path) != readiness_binding["sha256"]:
        raise ActionInterpretabilityValidationError("source-readiness file digest differs")
    readiness_artifact = load_json(readiness_path)
    if readiness_artifact["artifact_id"] != readiness_binding["artifact_id"]:
        raise ActionInterpretabilityValidationError("source-readiness artifact identity differs")
    if readiness_artifact["source_readiness_subject_sha256"] != readiness_binding["subject_sha256"]:
        raise ActionInterpretabilityValidationError("source-readiness subject digest differs")

    legacy_binding = artifact["input_bindings"]["legacy_decision_implementation"]
    legacy_path = root / legacy_binding["path"]
    if file_sha256(legacy_path) != legacy_binding["sha256"]:
        raise ActionInterpretabilityValidationError("legacy decision artifact digest differs")
    legacy_artifact = load_json(legacy_path)
    if legacy_artifact["artifact_id"] != legacy_binding["artifact_id"]:
        raise ActionInterpretabilityValidationError("legacy decision artifact identity differs")
    if legacy_artifact["implementation_subject_sha256"] != legacy_binding["subject_sha256"]:
        raise ActionInterpretabilityValidationError("legacy decision subject digest differs")

    for protected in artifact["protected_historical_artifacts"]:
        if file_sha256(root / protected["path"]) != protected["sha256"]:
            raise ActionInterpretabilityValidationError(
                f"protected historical artifact differs: {protected['path']}"
            )

    readiness_by_id = {
        item["action_id"]: item for item in readiness_artifact["subject"]["action_readiness"]
    }
    for readiness in readiness_by_id.values():
        for source in readiness["sources"]:
            raw = source["raw_provenance"]
            raw_path = root / raw["governed_local_path"]
            if raw_path.suffix.lower() == ".zip":
                raise ActionInterpretabilityValidationError("ZIP sources are outside this contract")
            if not raw_path.is_file() or sha256_file(raw_path) != raw["sha256"]:
                raise ActionInterpretabilityValidationError(
                    f"governed raw source missing or corrupt: {source['source_id']}"
                )
            if digest(source["neutral_projection"]) != source["neutral_projection_sha256"]:
                raise ActionInterpretabilityValidationError(
                    f"governed source projection digest differs: {source['source_id']}"
                )
    legacy_by_id = {
        item["action_id"]: item for item in legacy_artifact["subject"]["implementation_records"]
    }
    candidates = artifact["candidates"]
    action_ids = [item["action_id"] for item in candidates]
    if len(action_ids) != len(set(action_ids)):
        raise ActionInterpretabilityValidationError("duplicate action in candidate set")
    if set(action_ids) != set(readiness_by_id) or set(action_ids) != set(legacy_by_id):
        raise ActionInterpretabilityValidationError("candidate action set differs from governed input set")
    identities = [(item["exact_action_identity"], item["governed_source_packet_sha256"]) for item in candidates]
    if len(identities) != len(set(identities)):
        raise ActionInterpretabilityValidationError("duplicate exact-action/source identity")

    core = load_json(root / "docs/editorial/shared_corpora/house_119_v1/shared_action_core.json")
    core_by_id = {item["action_id"]: item for item in core["actions"]}
    states: dict[str, int] = {}
    legacy_assessments: dict[str, int] = {}
    qualification_by_action: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        action_id = candidate["action_id"]
        readiness = readiness_by_id[action_id]
        if candidate["current_accepted_legacy_meaning"] != legacy_by_id[action_id]["accepted_exact_action_meaning"]:
            raise ActionInterpretabilityValidationError(f"legacy meaning differs: {action_id}")
        expected_core = core_by_id.get(action_id)
        core_ref = candidate["shared_action_core_reference"]
        if expected_core is None and core_ref is not None:
            raise ActionInterpretabilityValidationError(f"unexpected Shared Action Core reference: {action_id}")
        if expected_core is not None:
            if core_ref is None or core_ref["action_core_sha256"] != expected_core["action_core_sha256"]:
                raise ActionInterpretabilityValidationError(f"missing or wrong Shared Action Core reference: {action_id}")
            if core_ref["governed_source_identity_sha256"] != expected_core["governed_source_identity_sha256"]:
                raise ActionInterpretabilityValidationError(f"wrong Shared Action Core source binding: {action_id}")
        computed = qualify_candidate(candidate, readiness)
        if candidate["qualification"] != computed:
            raise ActionInterpretabilityValidationError(f"stored qualification differs: {action_id}")
        if computed["result"] == "fail":
            failures = sorted(name for name, passed in computed["checks"].items() if not passed)
            raise ActionInterpretabilityValidationError(f"candidate qualification failed: {action_id}: {failures}")
        if candidate["candidate_state"] in HOLD_STATES and not candidate["limitations"]:
            raise ActionInterpretabilityValidationError(
                f"interpretability hold lacks an evidence limitation: {action_id}"
            )
        states[candidate["candidate_state"]] = states.get(candidate["candidate_state"], 0) + 1
        assessment = candidate["legacy_interpretability_assessment"]
        legacy_assessments[assessment] = legacy_assessments.get(assessment, 0) + 1
        qualification_by_action[action_id] = computed

    return {
        "candidate_count": len(candidates),
        "candidate_state_counts": dict(sorted(states.items())),
        "legacy_assessment_counts": dict(sorted(legacy_assessments.items())),
        "qualification_by_action": qualification_by_action,
        "candidate_set_digest": digest(candidates),
    }
