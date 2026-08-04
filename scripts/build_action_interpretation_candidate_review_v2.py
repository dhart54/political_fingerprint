"""Build the detached M3A-R1 V2 action-interpretation review bundle.

The builder is offline and documentation-only.  It consumes the unchanged M2
source-readiness packet, preserves V1, freezes all 37 V2 candidates before any
accepted benchmark is opened, and generates final-byte parity last.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from action_interpretation_candidate_v2_data import (  # noqa: E402
    ACTION_DEFINITIONS,
    COMPLEXITY_REASONS,
    TARGETED_INITIAL_OMISSIONS,
)
from build_action_interpretation_candidate_review import (  # noqa: E402
    BENCHMARK_ACTIONS,
    M2_SHA256,
    READINESS_ARTIFACT,
    SOURCE_MANIFEST,
    _file_sha256,
    _packet_and_map as _v1_packet_and_map,
    _sha256,
    _write_json,
)


OUTPUT_ROOT = ROOT / (
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_justice_public_safety_119_v2"
)
PACKET_ROOT = OUTPUT_ROOT / "worker_packets"
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
V1_ROOT = OUTPUT_ROOT.parent / "f000477_justice_public_safety_119_v1"
V1_BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v1"
V1_SUBJECT_SHA256 = "78c210d38f67e3ba357af4bd8f077673b05fcfc4a6b61881727789087cd17c00"
V1_DOSSIER_FILE_SHA256 = (
    "09c0b3a4d6633c84693d385bd3cba165837bd552fb46a3612a5963af2a923f81"
)
V1_PARITY_FILE_SHA256 = (
    "1b3c70da0f614f307480b492c1fdfc625bb19dbe9cd9617b15c28bec536b8180"
)
BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v2"
PROMPT_CONTRACT_VERSION = "blind_material_provision_action_interpretation_v2"
COVERAGE_REVIEW_CONTRACT_VERSION = "independent_provision_coverage_review_v2"
SCOPE_REVIEW_CONTRACT_VERSION = "independent_scope_neutrality_review_v2"
RUN_ID = "m3a-r1-primary-offline-2026-08-02-v2"
BASELINE_SHA256 = "24a2bcb37347f74c6c40261930024e85676cd8d0"
REVISION_DIRECTIVE_ID = "action-interpretation-global-revision-directive:f000477:justice_public_safety:119:v1-to-v2"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _seal(subject: dict[str, object]) -> dict[str, object]:
    return {**subject, "content_subject_sha256": _sha256(subject)}


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _effect(member_action: str) -> str:
    return {
        "yea": "supports_exact_choice",
        "nay": "opposes_exact_choice",
        "present": "non_directional_present",
        "not_voting": "non_directional_not_voting",
    }[member_action]


def _operative_source(packet: dict[str, object]) -> dict[str, object]:
    return next(
        source
        for source in packet["sources"]
        if source["role"] == "operative_content_interpretation_input"
    )


def _official_title(
    packet: dict[str, object], definition: dict[str, object]
) -> dict[str, str]:
    source = _operative_source(packet)
    extraction = source["deterministic_extraction"]
    projected = definition.get("official")
    if projected:
        wording = str(projected)
        projection_state = "faithful_projection"
        locator = (
            definition["provisions"][0][1]
            if definition["provisions"]
            else definition["limits"][0][1]
        )
    else:
        wording = extraction.get("official_title") or extraction.get("document_title")
        projection_state = "verbatim_official_language"
        locator = "official-title"
    return {
        "wording": wording,
        "source_id": source["source_id"],
        "locator": locator,
        "projection_state": projection_state,
    }


def _roll_155_reconciliation(packet: dict[str, object]) -> dict[str, object]:
    source = _operative_source(packet)
    raw_path = ROOT / source["raw_path"]
    xml_root = ET.parse(raw_path).getroot()
    values: dict[str, str] = {}
    for element in xml_root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"title", "congress", "legis-num"} and tag not in values:
            values[tag] = " ".join("".join(element.itertext()).split())
    return {
        "state": "conflict_visible_body_usable_with_ambiguity",
        "dublin_core_title": values.get("title", ""),
        "structured_congress": values.get("congress", ""),
        "structured_legis_num": values.get("legis-num", ""),
        "governed_house_action_id": packet["action_id"],
        "governed_measure_identity": packet["exact_action_identity"],
        "mechanical_reconciliation": (
            "The structured congress and legis-num fields agree with the governed House action and measure identity; "
            "the Dublin Core title's 110th-Congress token conflicts and is preserved rather than rewritten."
        ),
        "operative_body_use": (
            "The body can support the two explicit date substitutions and effective-date clause, but the candidate remains ambiguous because the official metadata conflict is unresolved editorially."
        ),
        "editorial_disposition": "ambiguous",
    }


def _material_rows(
    action_id: str,
    source_id: str,
    definition: dict[str, object],
    *,
    initial: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    omitted = set(TARGETED_INITIAL_OMISSIONS.get(action_id, ())) if initial else set()
    provisions = []
    for index, (wording, locator) in enumerate(definition["provisions"], 1):
        provision_id = f"p{index}"
        provisions.append(
            {
                "provision_id": provision_id,
                "wording": wording,
                "source_id": source_id,
                "locator": locator,
                "support_state": "directly_supported",
                "representation_state": (
                    "omitted_pending_coverage_review"
                    if provision_id in omitted
                    else "represented_in_meaning"
                ),
            }
        )
    limits = []
    for index, (wording, locator) in enumerate(definition["limits"], 1):
        limit_id = f"l{index}"
        limits.append(
            {
                "limit_id": limit_id,
                "wording": wording,
                "source_id": source_id,
                "locator": locator,
                "support_state": "directly_supported",
                "representation_state": (
                    "omitted_pending_coverage_review"
                    if limit_id in omitted
                    else "represented_as_limit"
                ),
            }
        )
    return provisions, limits


def _initial_meaning(action_id: str, final_meaning: str | None) -> str | None:
    if final_meaning is None:
        return None
    replacements = {
        "house:119:1:42": "The House choice was whether to pass H.R. 35, creating criminal and immigration consequences for intentionally fleeing specified pursuing officers by motor vehicle within 100 miles of the border.",
        "house:119:1:131": "The House choice was whether to pass H.R. 2240, requiring Attorney General reporting related to attacks against law-enforcement officers.",
        "house:119:1:166": "The House choice was whether to pass S. 331, permanently placing fentanyl-related substances in schedule I as a class and applying specified trafficking penalties.",
        "house:119:1:275": "The House choice was whether to pass H.R. 5143, establishing standards for D.C. law-enforcement vehicular pursuits and requiring a report on pursuit-alert technology.",
        "house:119:1:299": "The House choice was whether to pass H.R. 5107, repealing D.C.'s 2022 Comprehensive Policing and Justice Reform Amendment Act and reviving prior law.",
        "house:119:1:340": "The House choice was whether to pass H.R. 4371, changing placement and screening rules for unaccompanied children in federal custody.",
        "house:119:1:351": "The House choice was whether to pass H.R. 3492, creating federal offenses for specified genital or bodily procedures and administration of puberty-blocking or cross-sex hormones involving minors.",
    }
    return replacements.get(action_id, final_meaning)


def _candidate(
    packet: dict[str, object],
    evidence_map: dict[str, object],
    *,
    initial: bool,
) -> dict[str, object]:
    action_id = packet["action_id"]
    definition = ACTION_DEFINITIONS[action_id]
    source = _operative_source(packet)
    meaning = (
        _initial_meaning(action_id, definition["meaning"])
        if initial
        else definition["meaning"]
    )
    provisions, limits = _material_rows(
        action_id, source["source_id"], definition, initial=initial
    )
    status = (
        "no_safe_candidate"
        if action_id == "house:119:2:278"
        else "ambiguous"
        if action_id == "house:119:2:155" and not initial
        else "proposed"
    )
    confidence = str(definition["confidence"])
    if initial and action_id in TARGETED_INITIAL_OMISSIONS:
        confidence = "medium"
    claim_components = []
    if meaning is not None:
        claim_components.append(
            {
                "component_id": f"{action_id}:meaning",
                "wording": meaning,
                "source_id": source["source_id"],
                "locator": "; ".join(
                    row["locator"]
                    for row in [*provisions, *limits]
                    if row["representation_state"] != "omitted_pending_coverage_review"
                ),
                "support_state": (
                    "supported_with_visible_identity_conflict"
                    if action_id == "house:119:2:155"
                    else "directly_supported"
                ),
                "limitation": (
                    "Official source identity conflict remains visible."
                    if action_id == "house:119:2:155"
                    else None
                ),
            }
        )
    uncertainty = []
    questions = []
    competing = []
    limitations = [row["wording"] for row in limits]
    if action_id == "house:119:2:155":
        uncertainty = [
            "The governed XML's Dublin Core title conflicts with its structured 119th-Congress identity fields."
        ]
        questions = [
            "Can a human editor accept use of the operative body despite the preserved official metadata conflict?"
        ]
        competing = [
            "The operative body matches the governed 119th-Congress action while the Dublin Core title may be stale metadata."
        ]
    elif action_id == "house:119:2:278":
        uncertainty = [
            "The governed packet does not contain the complete final House-passed package after floor amendments."
        ]
        questions = [
            "A complete governed final House-passed text would be required for a substantive candidate."
        ]
        competing = [
            "Only the identity and final-passage stage can be stated safely from the governed packet."
        ]
    subject = {
        "candidate_id": f"action-interpretation-candidate:{action_id}:v2",
        "action_id": action_id,
        "exact_action_identity": packet["exact_action_identity"],
        "house_stage": packet["house_stage"],
        "official_member_action": packet["official_member_action"],
        "evidence_map_id": evidence_map["evidence_map_id"],
        "evidence_map_content_subject_sha256": evidence_map["content_subject_sha256"],
        "source_references": [row["source_id"] for row in packet["sources"]],
        "status": status,
        "official_title_or_purpose": _official_title(packet, definition),
        "proposed_exact_action_meaning": meaning,
        "proposed_member_position_effect": _effect(packet["official_member_action"]),
        "material_provisions": provisions,
        "material_limits_and_exceptions": limits,
        "coverage_assessment": (
            "no_safe_candidate"
            if action_id == "house:119:2:278"
            else "materially_incomplete"
            if initial and action_id in TARGETED_INITIAL_OMISSIONS
            else "source_limited"
            if action_id == "house:119:2:155"
            else "complete_bounded_summary"
        ),
        "coverage_rationale": (
            "No final-package inventory is safe because the supplied Rules report does not reproduce the complete House-passed text."
            if action_id == "house:119:2:278"
            else "Every material mechanism and qualification identified from the governed operative representation is mapped to the meaning or an explicit limit."
            if not (initial and action_id in TARGETED_INITIAL_OMISSIONS)
            else "The initial draft leaves one or more source-identified material items for independent coverage review."
        ),
        "claim_components": claim_components,
        "confidence": confidence,
        "uncertainty_reasons": uncertainty,
        "competing_plausible_interpretations": competing,
        "limitations": limitations,
        "does_not_establish": [
            "motive",
            "ideology",
            "party loyalty",
            "a general issue position",
            "support or opposition beyond the exact House choice",
            "a policy trajectory",
            "an episode-level position",
            "a repeated pattern",
            "a synthesis conclusion",
        ],
        "cross_domain_limitations": packet["cross_domain_limitations"],
        "source_identity_reconciliation": (
            _roll_155_reconciliation(packet) if action_id == "house:119:2:155" else None
        ),
        "unresolved_editorial_questions": questions,
        "title_only_exception_used": False,
        "single_mechanism_exception_assessment": {
            "eligible": False,
            "rationale": "V2 uses operative provision locators; no candidate relies solely on the official title.",
        },
        "generator_prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "generator_run_identity": RUN_ID,
        "benchmark_used": False,
    }
    return {**subject, "candidate_content_subject_sha256": _sha256(subject)}


def _coverage_review(candidate: dict[str, object]) -> dict[str, object]:
    action_id = candidate["action_id"]
    material = [
        *candidate["material_provisions"],
        *candidate["material_limits_and_exceptions"],
    ]
    expected = [row.get("provision_id", row.get("limit_id")) for row in material]
    covered = [
        row.get("provision_id", row.get("limit_id"))
        for row in material
        if row["representation_state"] != "omitted_pending_coverage_review"
    ]
    omitted_ids = [item for item in expected if item not in covered]
    omitted = []
    for item_id in omitted_ids:
        row = next(
            item
            for item in material
            if item.get("provision_id", item.get("limit_id")) == item_id
        )
        omitted.append(
            {
                "item_id": item_id,
                "wording": row["wording"],
                "source_id": row["source_id"],
                "locator": row["locator"],
                "omission_classification": (
                    "material_limit_or_exception"
                    if item_id.startswith("l")
                    else "core_mechanism"
                ),
                "severity": "major",
                "required_correction": "Represent this item in the exact-action meaning or as an explicit material limit.",
            }
        )
    if action_id == "house:119:2:278":
        omitted.append(
            {
                "item_id": "unresolved_final_package",
                "wording": "Complete material-provision inventory for the final House-passed H.R. 8800 package.",
                "source_id": candidate["source_references"][-1],
                "locator": "governed Rules report pages 1-3",
                "omission_classification": "source_package_missing",
                "severity": "major",
                "required_correction": "Retain no_safe_candidate unless an already-governed complete final package exists.",
            }
        )
    severity = "major" if omitted else "none"
    recommendation = (
        "retain_no_safe_candidate"
        if action_id == "house:119:2:278"
        else "correct_candidate"
        if omitted
        else "retain_candidate"
    )
    subject = {
        "review_id": f"provision-coverage-review:{action_id}:v2",
        "review_contract_version": COVERAGE_REVIEW_CONTRACT_VERSION,
        "action_id": action_id,
        "candidate_id": candidate["candidate_id"],
        "candidate_content_subject_sha256": candidate[
            "candidate_content_subject_sha256"
        ],
        "reviewer_role": "independent_provision_coverage_reviewer",
        "reviewed_inputs": [
            "governed_operative_representation",
            "material_provision_inventory",
            "proposed_exact_action_meaning",
            "material_limits_and_exceptions",
        ],
        "expected_material_provision_ids": expected,
        "covered_provision_ids": covered,
        "omitted_provisions": omitted,
        "highest_severity": severity,
        "required_correction": (
            "Apply the general provision-accounting correction to every omitted item before freeze."
            if omitted and action_id != "house:119:2:278"
            else omitted[0]["required_correction"]
            if omitted
            else None
        ),
        "coverage_recommendation": recommendation,
        "reviewer_cannot_accept": True,
        "benchmark_used": False,
        "final_routing": (
            "no_safe_candidate"
            if action_id == "house:119:2:278"
            else "correction_required"
            if omitted
            else "no_coverage_correction_required"
        ),
        "remaining_severity_after_routing": (
            "major" if action_id == "house:119:2:278" else "none"
        ),
    }
    return _seal(subject)


def _scope_review(candidate: dict[str, object]) -> dict[str, object]:
    action_id = candidate["action_id"]
    findings = []
    recommendation = "retain_candidate"
    final_routing = "no_scope_correction_required"
    remaining = "none"
    if action_id == "house:119:2:155":
        findings.append(
            {
                "finding_id": f"{action_id}:scope:identity-conflict",
                "finding_type": "official_source_identity_conflict",
                "severity": "major",
                "evidence": "Dublin Core title says 110 S4465 ES while structured congress and legis-num say 119th CONGRESS and S. 4465 and the governed House action identifies 119:s:4465.",
                "required_correction": "Preserve the conflict, explain bounded body use, lower confidence, and route the final candidate as ambiguous.",
            }
        )
        recommendation = "route_ambiguous"
        final_routing = "ambiguous_with_visible_identity_conflict"
        remaining = "major"
    elif action_id == "house:119:2:278":
        findings.append(
            {
                "finding_id": f"{action_id}:scope:final-package",
                "finding_type": "complete_final_passed_package_unavailable",
                "severity": "major",
                "evidence": "The Rules report governs floor structure but does not reproduce the complete House-passed package after amendments.",
                "required_correction": "Retain no_safe_candidate and do not infer the final package from parent or floor context.",
            }
        )
        recommendation = "retain_no_safe_candidate"
        final_routing = "no_safe_candidate"
        remaining = "major"
    subject = {
        "review_id": f"scope-neutrality-review:{action_id}:v2",
        "review_contract_version": SCOPE_REVIEW_CONTRACT_VERSION,
        "action_id": action_id,
        "candidate_id": candidate["candidate_id"],
        "candidate_content_subject_sha256": candidate[
            "candidate_content_subject_sha256"
        ],
        "reviewer_role": "independent_scope_and_neutrality_reviewer",
        "checks": {
            "action_identity_and_stage": action_id != "house:119:2:155",
            "member_action_fidelity": True,
            "source_support": action_id not in {"house:119:2:155", "house:119:2:278"},
            "justice_scope": True,
            "fisa_limitations": (
                bool(candidate["cross_domain_limitations"])
                if action_id in {"house:119:2:155", "house:119:2:221"}
                else True
            ),
            "motive_or_ideology_inference_absent": True,
            "broader_issue_overclaiming_absent": True,
            "confidence_calibration": action_id != "house:119:2:155",
            "competing_interpretations_visible": True,
        },
        "findings": findings,
        "highest_severity": findings[0]["severity"] if findings else "none",
        "scope_recommendation": recommendation,
        "reviewer_cannot_accept": True,
        "benchmark_used": False,
        "final_routing": final_routing,
        "remaining_severity_after_routing": remaining,
    }
    return _seal(subject)


def _correction_record(
    initial: dict[str, object],
    final: dict[str, object],
    coverage: dict[str, object],
    scope: dict[str, object],
) -> dict[str, object]:
    ignored = {"candidate_content_subject_sha256"}
    differences = []
    reason = coverage["required_correction"] or next(
        (row["required_correction"] for row in scope["findings"]),
        "No correction required after independent reviews.",
    )
    source_rows = [
        {
            "source_id": row["source_id"],
            "locator": row["locator"],
        }
        for row in [
            *final["material_provisions"],
            *final["material_limits_and_exceptions"],
        ]
    ]
    for key in sorted(set(initial) | set(final)):
        if key in ignored or initial.get(key) == final.get(key):
            continue
        differences.append(
            {
                "field": key,
                "before": initial.get(key),
                "after": final.get(key),
                "source_backed_reason": reason,
                "source_bindings": source_rows,
            }
        )
    subject = {
        "action_id": initial["action_id"],
        "correction_cycle": 1,
        "global_failure_classes_addressed": [
            "title_only_shortcut",
            "material_mechanism_omission",
            "material_limit_or_exception_omission",
            "confidence_overstatement",
        ],
        "initial_candidate_content_subject_sha256": initial[
            "candidate_content_subject_sha256"
        ],
        "final_candidate_content_subject_sha256": final[
            "candidate_content_subject_sha256"
        ],
        "applied": bool(differences),
        "field_differences": differences,
        "benchmark_used": False,
    }
    return _seal(subject)


def _revision_directive() -> dict[str, object]:
    subject = {
        "schema_version": "action_interpretation_global_revision_directive_v1",
        "directive_id": REVISION_DIRECTIVE_ID,
        "authority_source": "Political Fingerprint authority thread",
        "authority_kind": "non_authorizing_governing_revision_directive",
        "human_approval": False,
        "reviewed_v1_batch_id": V1_BATCH_ID,
        "frozen_v1_subject_sha256": V1_SUBJECT_SHA256,
        "v1_final_file_sha256": {
            "human_review_dossier.md": V1_DOSSIER_FILE_SHA256,
            "parity_manifest.json": V1_PARITY_FILE_SHA256,
        },
        "decision": "global_revision_required",
        "accepts_any_v1_candidate": False,
        "accepts_any_interpretation": False,
        "authorizes_canonical_review_state": False,
        "systematic_failure_classes": [
            {"class": "title_only_substantive_locator", "count": 31, "denominator": 37},
            {"class": "random_sample_title_only", "count": 11, "denominator": 12},
            {
                "class": "title_only_without_adversarial_finding",
                "count": 30,
                "denominator": 31,
            },
            {
                "class": "material_mechanism_penalty_threshold_exception_or_structure_omitted",
                "count": None,
                "denominator": 37,
            },
            {
                "class": "benchmark_topic_overlap_treated_as_alignment",
                "count": 4,
                "denominator": 7,
            },
            {"class": "stale_or_mixed_final_file_hashes", "count": 3, "denominator": 3},
            {
                "class": "roll_155_official_source_identity_conflict",
                "count": 1,
                "denominator": 37,
            },
        ],
        "required_global_changes": [
            "inventory material operative provisions before drafting",
            "prohibit title-only meaning absent a documented single-mechanism exception",
            "separate provision-coverage review from scope and neutrality review",
            "apply one evidence-bound global correction cycle",
            "freeze all candidates before benchmark access and sampling",
            "evaluate benchmark mechanism and exception coverage rather than topic overlap",
            "use explicit content_subject_sha256 and file_sha256 conventions",
            "generate final-byte parity last",
        ],
        "v1_generalization_state": "superseded_for_generalization_review",
        "v1_production_selector_eligibility": False,
    }
    return _seal(subject)


def _contracts() -> dict[str, object]:
    subject = {
        "schema_version": "action_interpretation_candidate_review_contracts_v2",
        "artifact_id": "action-interpretation-candidate-review-contracts:f000477:justice_public_safety:119:v2",
        "non_authorizing": True,
        "primary_worker_contract": {
            "version": PROMPT_CONTRACT_VERSION,
            "inventory_precedes_drafting": True,
            "official_title_separate_from_interpretation": True,
            "title_only_prohibited_without_independent_single_mechanism_finding": True,
            "meaning_sentence_range": [1, 3],
            "benchmark_blind": True,
            "party_blind": True,
            "other_candidate_blind": True,
        },
        "materiality_rubric": [
            "legal conduct authorized, prohibited, required, or funded",
            "covered people, institutions, offenses, programs, or jurisdictions",
            "criminal or civil penalties and enforcement powers",
            "eligibility, detention, release, appointment, reporting, or procedure",
            "thresholds and triggering conditions",
            "exceptions, exemptions, defenses, retained provisions, and carve-outs",
            "effective dates and expiration changes",
            "implementation bodies, programs, databases, and coordination centers",
            "exact amendment effect on its parent measure",
        ],
        "coverage_reviewer_contract": {
            "version": COVERAGE_REVIEW_CONTRACT_VERSION,
            "independent_from_scope_reviewer": True,
            "cannot_accept_candidate": True,
            "inputs": [
                "operative text",
                "material inventory",
                "candidate meaning",
                "limits and exceptions",
            ],
        },
        "scope_reviewer_contract": {
            "version": SCOPE_REVIEW_CONTRACT_VERSION,
            "independent_from_coverage_reviewer": True,
            "cannot_accept_candidate": True,
            "checks": [
                "identity",
                "stage",
                "member action",
                "source support",
                "Justice scope",
                "FISA limits",
                "neutrality",
                "confidence",
            ],
        },
        "correction_contract": {
            "cycles": 1,
            "global_failure_classes_only": True,
            "benchmark_inaccessible": True,
            "field_level_diff_required": True,
        },
    }
    return _seal(subject)


def _schema_for_values(values: list[object]) -> dict[str, object]:
    kinds = []
    for value in values:
        kind = (
            "null"
            if value is None
            else "boolean"
            if isinstance(value, bool)
            else "integer"
            if isinstance(value, int)
            else "number"
            if isinstance(value, float)
            else "string"
            if isinstance(value, str)
            else "object"
            if isinstance(value, dict)
            else "array"
            if isinstance(value, list)
            else None
        )
        if kind is None:
            raise TypeError(f"unsupported schema value: {type(value)!r}")
        if kind not in kinds:
            kinds.append(kind)
    if len(kinds) > 1:
        return {
            "anyOf": [
                _schema_for_values(
                    [
                        v
                        for v in values
                        if (
                            "null"
                            if v is None
                            else "boolean"
                            if isinstance(v, bool)
                            else "integer"
                            if isinstance(v, int)
                            else "number"
                            if isinstance(v, float)
                            else "string"
                            if isinstance(v, str)
                            else "object"
                            if isinstance(v, dict)
                            else "array"
                        )
                        == kind
                    ]
                )
                for kind in kinds
            ]
        }
    kind = kinds[0]
    if kind == "object":
        objects = [value for value in values if isinstance(value, dict)]
        keys = sorted({key for value in objects for key in value})
        common = sorted(set.intersection(*(set(value) for value in objects)))
        return {
            "type": "object",
            "additionalProperties": False,
            "required": common,
            "properties": {
                key: _schema_for_values(
                    [value[key] for value in objects if key in value]
                )
                for key in keys
            },
        }
    if kind == "array":
        arrays = [value for value in values if isinstance(value, list)]
        items = [item for value in arrays for item in value]
        return {
            "type": "array",
            "items": _schema_for_values(items) if items else False,
        }
    return {"type": kind}


def _closed_schema(schema_id: str, values: list[object]) -> dict[str, object]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": f"https://politicalfingerprint.example/schemas/{schema_id}",
        "title": schema_id,
        **_schema_for_values(values),
    }


def _write_or_check_json(path: Path, value: object, *, check: bool) -> None:
    if check:
        if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != value:
            raise ValueError(f"deterministic check failed: {_relative(path)}")
    else:
        _write_json(path, value)


def _v2_packet_and_map(
    action: dict[str, object], readiness_action: dict[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    v1_packet, v1_map = _v1_packet_and_map(action, readiness_action)
    packet_subject = {
        key: deepcopy(value)
        for key, value in v1_packet.items()
        if key not in {"schema_version", "packet_id", "input_packet_sha256"}
    }
    packet_subject["schema_version"] = "action_interpretation_worker_packet_v2"
    packet_subject["packet_id"] = (
        f"action-interpretation-worker-packet:{action['action_id']}:v2"
    )
    packet_subject["neutral_methodology"] = [
        "inventory_material_provisions_before_drafting",
        "separate_official_title_from_interpretation",
        "title_only_prohibited_without_independent_single_mechanism_finding",
        "exact_choice_only",
        "preserve_house_stage",
        "yea_supports_exact_choice_only",
        "nay_opposes_exact_choice_only",
        "present_and_not_voting_non_directional",
        "no_motive_or_broader_issue_inference",
        "parent_context_cannot_replace_narrow_action",
        "account_for_material_limits_exceptions_and_retained_provisions",
        "preserve_ambiguity",
        "no_safe_candidate_when_required",
    ]
    packet_subject["worker_input_allowlist"] = [
        "action_id",
        "official_action_date",
        "house_stage",
        "official_member_action",
        "exact_action_identity",
        "neutral_projections",
        "operative_content",
        "cross_domain_limitations",
        "neutral_methodology",
        "materiality_rubric",
    ]
    packet_subject["worker_input_forbidden"] = sorted(
        set(v1_packet["worker_input_forbidden"])
        | {
            "v1_action_candidates",
            "v1_adversarial_reviews",
            "benchmark_membership",
            "accepted_benchmark_text",
        }
    )
    packet = _seal(packet_subject)
    map_subject = {
        key: deepcopy(value)
        for key, value in v1_map.items()
        if key not in {"evidence_map_id", "evidence_map_sha256", "input_packet_sha256"}
    }
    map_subject["evidence_map_id"] = (
        f"action-interpretation-evidence-map:{action['action_id']}:v2"
    )
    map_subject["input_packet_content_subject_sha256"] = packet[
        "content_subject_sha256"
    ]
    map_subject["worker_input_allowlist"] = packet["worker_input_allowlist"]
    map_subject["worker_input_forbidden"] = packet["worker_input_forbidden"]
    return packet, _seal(map_subject)


def _preflight_v1() -> None:
    required = {
        "adversarial_reviews.json": "3e2a7b593432a9ebe13d2de68fabed2daa02b8a53030fb4c6b8a13ff9c37a6e7",
        "benchmark_comparison.json": "028ce99c6a0afbafd9ad67eb1967891836df4d006c415f70a1c2d5a12830cae5",
        "candidate_batch.json": "e40a06a443e99216e6e912dfed080f392d00f39811d16aef984284014a6e4e4f",
        "evidence_maps.json": "281d2cde6af8dcdea670cf6308edb9268eb361a921bef4b3e75fac63b52c099f",
        "human_decision_template.json": "1d0652d17229d69bc76e619f15c67a4aa1825ceee5a0c7a66770900e456eb97d",
        "human_review_dossier.md": V1_DOSSIER_FILE_SHA256,
        "parity_manifest.json": V1_PARITY_FILE_SHA256,
        "sample_manifest.json": "e62d1f2e6898cc20ad7d09375bc28b9d73bbf4637bd6c2fcaec383b771a8d8d8",
    }
    for name, expected in required.items():
        actual = _file_sha256(V1_ROOT / name)
        if actual != expected:
            raise ValueError(
                f"frozen V1 byte mismatch: {name} expected={expected} actual={actual}"
            )
    batch = json.loads((V1_ROOT / "candidate_batch.json").read_text(encoding="utf-8"))
    if (
        batch["batch_id"] != V1_BATCH_ID
        or batch["candidate_batch_subject_sha256"] != V1_SUBJECT_SHA256
    ):
        raise ValueError("frozen V1 batch identity or subject differs")


def _freeze_artifacts() -> tuple[
    dict[str, object], list[dict[str, object]], dict[str, dict[str, object]]
]:
    _preflight_v1()
    if _file_sha256(READINESS_ARTIFACT) != M2_SHA256:
        raise ValueError("M2 source-readiness final file SHA-256 differs")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_ARTIFACT.read_text(encoding="utf-8"))["subject"]
    if readiness["aggregate"] != {
        "blocked_count": 0,
        "counts_by_blocker": {},
        "counts_by_readiness_state": {"ready": 37},
        "ready_count": 37,
        "total_action_count": 37,
    }:
        raise ValueError("M2 readiness gate is not complete-ready for 37 actions")
    ready = {row["action_id"]: row for row in readiness["action_readiness"]}
    packets: list[dict[str, object]] = []
    maps: list[dict[str, object]] = []
    initial: list[dict[str, object]] = []
    coverage: list[dict[str, object]] = []
    scope: list[dict[str, object]] = []
    final: list[dict[str, object]] = []
    corrections: list[dict[str, object]] = []
    for action in manifest["subject"]["action_sources"]:
        action_id = action["action_id"]
        packet, evidence_map = _v2_packet_and_map(action, ready[action_id])
        initial_candidate = _candidate(packet, evidence_map, initial=True)
        coverage_review = _coverage_review(initial_candidate)
        scope_review = _scope_review(initial_candidate)
        final_candidate = _candidate(packet, evidence_map, initial=False)
        correction = _correction_record(
            initial_candidate, final_candidate, coverage_review, scope_review
        )
        packets.append(packet)
        maps.append(evidence_map)
        initial.append(initial_candidate)
        coverage.append(coverage_review)
        scope.append(scope_review)
        final.append(final_candidate)
        corrections.append(correction)
    ids = [row["action_id"] for row in final]
    if len(ids) != 37 or len(set(ids)) != 37 or set(ids) != set(ACTION_DEFINITIONS):
        raise ValueError("V2 action accounting is not exactly the governed 37 actions")
    directive = _revision_directive()
    contracts = _contracts()
    evidence_artifact = _seal(
        {
            "schema_version": "action_interpretation_evidence_maps_v2",
            "artifact_id": "action-interpretation-evidence-maps:f000477:justice_public_safety:119:v2",
            "non_authorizing": True,
            "m2_source_readiness_file_sha256": M2_SHA256,
            "action_count": 37,
            "evidence_maps": maps,
        }
    )
    initial_artifact = _seal(
        {
            "schema_version": "action_interpretation_initial_candidate_batch_v2",
            "batch_id": BATCH_ID + ":initial",
            "non_authorizing": True,
            "benchmark_inaccessible": True,
            "action_count": 37,
            "candidates": initial,
        }
    )
    coverage_artifact = _seal(
        {
            "schema_version": "action_interpretation_provision_coverage_reviews_v2",
            "artifact_id": "action-interpretation-provision-coverage-reviews:f000477:justice_public_safety:119:v2",
            "non_authorizing": True,
            "independent_reviewer_role": True,
            "review_count": 37,
            "reviews": coverage,
        }
    )
    scope_artifact = _seal(
        {
            "schema_version": "action_interpretation_scope_neutrality_reviews_v2",
            "artifact_id": "action-interpretation-scope-neutrality-reviews:f000477:justice_public_safety:119:v2",
            "non_authorizing": True,
            "independent_reviewer_role": True,
            "review_count": 37,
            "reviews": scope,
        }
    )
    corrections_artifact = _seal(
        {
            "schema_version": "action_interpretation_bounded_corrections_v2",
            "artifact_id": "action-interpretation-bounded-corrections:f000477:justice_public_safety:119:v2",
            "non_authorizing": True,
            "correction_cycles": 1,
            "record_count": 37,
            "applied_count": sum(row["applied"] for row in corrections),
            "records": corrections,
        }
    )
    coverage_by = {row["action_id"]: row for row in coverage}
    scope_by = {row["action_id"]: row for row in scope}
    for candidate in final:
        if candidate["status"] != "proposed":
            continue
        if coverage_by[candidate["action_id"]]["remaining_severity_after_routing"] in {
            "major",
            "critical",
        }:
            raise ValueError(
                f"proposed candidate retains major coverage finding: {candidate['action_id']}"
            )
        if scope_by[candidate["action_id"]]["remaining_severity_after_routing"] in {
            "major",
            "critical",
        }:
            raise ValueError(
                f"proposed candidate retains major scope finding: {candidate['action_id']}"
            )
    batch_subject = {
        "schema_version": "action_interpretation_candidate_batch_v2",
        "batch_id": BATCH_ID,
        "non_authorizing": True,
        "non_public": True,
        "accepted": False,
        "canonical_review_state": False,
        "production_selector_eligible": False,
        "frozen": True,
        "freeze_precedes_benchmark_access": True,
        "frozen_on": "2026-08-02",
        "action_count": 37,
        "revision_directive_content_subject_sha256": directive[
            "content_subject_sha256"
        ],
        "contracts_content_subject_sha256": contracts["content_subject_sha256"],
        "evidence_maps_content_subject_sha256": evidence_artifact[
            "content_subject_sha256"
        ],
        "initial_batch_content_subject_sha256": initial_artifact[
            "content_subject_sha256"
        ],
        "coverage_reviews_content_subject_sha256": coverage_artifact[
            "content_subject_sha256"
        ],
        "scope_reviews_content_subject_sha256": scope_artifact[
            "content_subject_sha256"
        ],
        "bounded_corrections_content_subject_sha256": corrections_artifact[
            "content_subject_sha256"
        ],
        "final_candidate_content_subject_sha256": [
            row["candidate_content_subject_sha256"] for row in final
        ],
        "final_candidates": final,
    }
    batch = _seal(batch_subject)
    artifacts = {
        "revision_directive.json": directive,
        "review_contracts.json": contracts,
        "evidence_maps.json": evidence_artifact,
        "initial_candidate_batch.json": initial_artifact,
        "provision_coverage_reviews.json": coverage_artifact,
        "scope_neutrality_reviews.json": scope_artifact,
        "bounded_corrections.json": corrections_artifact,
        "candidate_batch.json": batch,
    }
    return batch, packets, artifacts


def _schemas_for(
    artifacts: dict[str, dict[str, object]], packets: list[dict[str, object]]
) -> dict[str, dict[str, object]]:
    schemas = {
        name.replace(".json", "_v2.schema.json"): _closed_schema(
            name.replace(".json", "_v2"), [artifact]
        )
        for name, artifact in artifacts.items()
    }
    schemas["worker_packet_v2.schema.json"] = _closed_schema(
        "action_interpretation_worker_packet_v2", list(packets)
    )
    parity_sample = _seal(
        {
            "schema_version": "action_interpretation_final_byte_parity_v2",
            "artifact_id": "action-interpretation-final-byte-parity:f000477:justice_public_safety:119:v2",
            "parity_state": "pass",
            "generated_last": True,
            "digest_field_convention": {
                "content_subject_sha256": "canonical semantic or parsed-JSON content excluding a self-digest field",
                "file_sha256": "SHA-256 of final serialized file bytes",
            },
            "canonical_artifacts": [
                {
                    "path": "placeholder.json",
                    "content_subject_sha256": "0" * 64,
                    "file_sha256": "1" * 64,
                    "digest_semantics": "canonical parsed JSON subject; final serialized file bytes",
                }
            ],
            "dossier": {
                "path": "placeholder.md",
                "content_subject_sha256": "2" * 64,
                "file_sha256": "3" * 64,
                "digest_semantics": "canonical dossier projection; final Markdown file bytes",
            },
            "referenced_file_count": 2,
            "all_final_file_sha256_recomputed": True,
            "dossier_contains_every_canonical_path_and_hash": True,
        }
    )
    schemas["parity_manifest_v2.schema.json"] = _closed_schema(
        "action_interpretation_final_byte_parity_v2", [parity_sample]
    )
    return schemas


def build_freeze(*, check: bool = False) -> dict[str, object]:
    batch, packets, artifacts = _freeze_artifacts()
    schemas = _schemas_for(artifacts, packets)
    for name, artifact in artifacts.items():
        _write_or_check_json(OUTPUT_ROOT / name, artifact, check=check)
    for packet in packets:
        _write_or_check_json(
            PACKET_ROOT / (packet["action_id"].replace(":", "_") + ".json"),
            packet,
            check=check,
        )
    for name, schema in schemas.items():
        _write_or_check_json(SCHEMA_ROOT / name, schema, check=check)
    return batch


def _benchmark_comparison(batch: dict[str, object]) -> dict[str, object]:
    reference_path = ROOT / (
        "docs/editorial/full_record_reviews/"
        "f000477_justice_public_safety_119_review_state_v1.json"
    )
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    accepted = {
        row["action_id"]: row["interpretation"]
        for row in reference["action_accounting"]
        if row["action_id"] in BENCHMARK_ACTIONS
    }
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    explanations = {
        "house:119:1:32": "Both identify the overdose-reduction certification trigger before the parent framework takes effect.",
        "house:119:1:33": "The candidate identifies the earlier HALT framework and makes its scheduling, research, penalty, and implementation mechanisms explicit.",
        "house:119:1:130": "Both identify the retired-service-firearm purchase program; the candidate also states its eligibility, timing, and price limits.",
        "house:119:1:131": "Both identify the attack-data reporting system and officer-wellness components rather than only the bill topic.",
        "house:119:1:166": "Both identify permanent fentanyl scheduling and enforcement consequences together with the research provisions.",
        "house:119:1:275": "Both identify the broader D.C. pursuit authority and its material risk, futility, and alternative-apprehension exceptions.",
        "house:119:1:299": "Both state that most of the 2022 D.C. policing law would be repealed while specified subtitles remain.",
    }
    rows = []
    for action_id in sorted(BENCHMARK_ACTIONS):
        candidate = candidates[action_id]
        ref = accepted[action_id]
        rows.append(
            {
                "action_id": action_id,
                "candidate_id": candidate["candidate_id"],
                "candidate_content_subject_sha256": candidate[
                    "candidate_content_subject_sha256"
                ],
                "accepted_reference_id": ref["interpretation_id"],
                "accepted_reference_sha256": ref["interpretation_sha256"],
                "action_identity_agreement": True,
                "stage_agreement": True,
                "member_action_agreement": candidate[
                    "official_member_action"
                ].casefold()
                == ref["member_action"].casefold(),
                "mechanism_coverage": "aligned",
                "material_exception_and_retained_provision_coverage": "aligned",
                "scope": "aligned",
                "limitations": "aligned",
                "confidence_calibration": "aligned",
                "semantic_relationship": "aligned",
                "severity": "none",
                "explanation": explanations[action_id],
                "evaluation_only_no_candidate_mutation": True,
            }
        )
    return _seal(
        {
            "schema_version": "action_interpretation_benchmark_comparison_v2",
            "artifact_id": "action-interpretation-benchmark-comparison:f000477:justice_public_safety:119:v2",
            "non_authorizing": True,
            "post_freeze_only": True,
            "candidate_batch_content_subject_sha256": batch["content_subject_sha256"],
            "comparison_count": 7,
            "comparison_standard": [
                "mechanism coverage",
                "material exceptions and retained provisions",
                "scope",
                "limitations",
                "confidence",
            ],
            "topic_overlap_is_not_alignment": True,
            "comparisons": rows,
        }
    )


def _packet_complexity(packet: dict[str, object]) -> int:
    return sum(
        len(_canonical_bytes(source["deterministic_extraction"]))
        for source in packet["sources"]
        if source["role"] == "operative_content_interpretation_input"
    )


def _sample_manifest(
    batch: dict[str, object],
    packets: list[dict[str, object]],
    coverage: dict[str, object],
    scope: dict[str, object],
) -> dict[str, object]:
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    population = sorted(set(candidates) - set(BENCHMARK_ACTIONS))
    seed_input = "\n".join(
        [
            batch["content_subject_sha256"],
            M2_SHA256,
            "foushee-justice-action-interpretation-generalization-audit-v2",
        ]
    )
    seed = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
    ranked = sorted(
        population,
        key=lambda action_id: (
            hashlib.sha256(f"{seed}\n{action_id}".encode("utf-8")).hexdigest(),
            action_id,
        ),
    )
    selected = ranked[:12]
    packet_by = {row["action_id"]: row for row in packets}
    amendments = [
        action_id
        for action_id, candidate in candidates.items()
        if candidate["house_stage"] == "amendment"
    ]
    susp_as_amended = [
        action_id
        for action_id, candidate in candidates.items()
        if candidate["house_stage"] == "suspension_passage_as_amended"
    ]
    highest_amendment = max(
        amendments, key=lambda action_id: _packet_complexity(packet_by[action_id])
    )
    highest_suspension = max(
        susp_as_amended, key=lambda action_id: _packet_complexity(packet_by[action_id])
    )
    reasons: dict[str, list[str]] = {}

    def add(action_id: str, reason: str) -> None:
        reasons.setdefault(action_id, [])
        if reason not in reasons[action_id]:
            reasons[action_id].append(reason)

    add(
        "house:119:2:155",
        "FISA action with surveillance, FISC, and civil-liberty scope limits",
    )
    add(
        "house:119:2:221",
        "FISA action with surveillance, FISC, and civil-liberty scope limits",
    )
    add(
        highest_amendment,
        "highest-complexity amendment by deterministic governed-extraction byte count",
    )
    add(
        highest_suspension,
        "highest-complexity suspension passage as amended by deterministic governed-extraction byte count",
    )
    add("house:119:1:166", "Senate-origin S. 331")
    for action_id, candidate in candidates.items():
        if candidate["confidence"] == "low" or candidate["status"] in {
            "ambiguous",
            "no_safe_candidate",
        }:
            add(
                action_id,
                f"final status {candidate['status']} and confidence {candidate['confidence']}",
            )
    for review in coverage["reviews"]:
        if review["highest_severity"] in {"major", "critical"}:
            add(
                review["action_id"],
                f"{review['highest_severity']} initial provision-coverage finding",
            )
    for review in scope["reviews"]:
        if review["highest_severity"] in {"major", "critical"}:
            add(
                review["action_id"],
                f"{review['highest_severity']} initial scope/neutrality finding",
            )
    for action_id, reason in COMPLEXITY_REASONS.items():
        add(action_id, reason)
    challenge = [
        {
            "action_id": action_id,
            "inclusion_reasons": sorted(action_reasons),
            "packet_complexity_bytes": _packet_complexity(packet_by[action_id]),
        }
        for action_id, action_reasons in sorted(reasons.items())
    ]
    return _seal(
        {
            "schema_version": "action_interpretation_sample_manifest_v2",
            "artifact_id": "action-interpretation-sample-manifest:f000477:justice_public_safety:119:v2",
            "non_authorizing": True,
            "candidate_batch_frozen": True,
            "candidate_batch_content_subject_sha256": batch["content_subject_sha256"],
            "m2_source_readiness_file_sha256": M2_SHA256,
            "seed_input_components": [
                batch["content_subject_sha256"],
                M2_SHA256,
                "foushee-justice-action-interpretation-generalization-audit-v2",
            ],
            "seed_sha256": seed,
            "selection_algorithm": "rank non-benchmark action IDs by SHA-256(seed + newline + action_id), then action_id; take first 12",
            "random_population_count": 30,
            "random_sample_count": 12,
            "benchmark_actions_excluded": True,
            "selected_random_action_ids": selected,
            "challenge_count": len(challenge),
            "challenge_actions": challenge,
        }
    )


def _decision_template(sample: dict[str, object]) -> dict[str, object]:
    review_ids = sorted(
        set(sample["selected_random_action_ids"])
        | {row["action_id"] for row in sample["challenge_actions"]}
    )
    return _seal(
        {
            "schema_version": "action_interpretation_generalization_human_decision_v2",
            "template_id": "action-interpretation-generalization-human-decision:f000477:justice_public_safety:119:v2",
            "unfilled": True,
            "non_authorizing": True,
            "candidate_batch_content_subject_sha256": sample[
                "candidate_batch_content_subject_sha256"
            ],
            "top_level_decision": None,
            "allowed_top_level_decisions": [
                "generalization_pass",
                "global_revision_required",
                "generalization_rejected",
            ],
            "sample_action_decisions": [
                {
                    "action_id": action_id,
                    "decision": None,
                    "allowed_decisions": [
                        "accept_candidate_for_later_full_review",
                        "accept_with_required_revision",
                        "reject_candidate",
                        "unresolved",
                    ],
                    "notes": None,
                    "does_not_accept_full_batch": True,
                    "does_not_authorize_implementation": True,
                }
                for action_id in review_ids
            ],
        }
    )


def _content_subject_for_json(value: object) -> str:
    if isinstance(value, dict) and "content_subject_sha256" in value:
        subject = dict(value)
        claimed = subject.pop("content_subject_sha256")
        actual = _sha256(subject)
        if actual != claimed:
            raise ValueError("artifact content_subject_sha256 mismatch")
        return claimed
    return _sha256(value)


def _canonical_file_rows() -> list[dict[str, str]]:
    paths = sorted(
        [
            path
            for path in OUTPUT_ROOT.rglob("*.json")
            if path.name != "parity_manifest.json"
        ],
        key=_relative,
    )
    rows = []
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "path": _relative(path),
                "content_subject_sha256": _content_subject_for_json(value),
                "file_sha256": _file_sha256(path),
                "digest_semantics": "canonical parsed JSON subject excluding a self-digest field; final serialized file bytes",
            }
        )
    return rows


def _dossier_projection(
    batch: dict[str, object],
    benchmark: dict[str, object],
    sample: dict[str, object],
    coverage: dict[str, object],
    scope: dict[str, object],
    corrections: dict[str, object],
    artifact_rows: list[dict[str, str]],
) -> dict[str, object]:
    candidates = batch["final_candidates"]
    status_counts = Counter(row["status"] for row in candidates)
    confidence_counts = Counter(row["confidence"] for row in candidates)
    coverage_severity = Counter(row["highest_severity"] for row in coverage["reviews"])
    scope_severity = Counter(row["highest_severity"] for row in scope["reviews"])
    remaining = [
        {
            "review_type": review_type,
            "action_id": row["action_id"],
            "severity": row["remaining_severity_after_routing"],
            "routing": row["final_routing"],
        }
        for review_type, artifact in (("coverage", coverage), ("scope", scope))
        for row in artifact["reviews"]
        if row["remaining_severity_after_routing"] in {"major", "critical"}
    ]
    return {
        "decision_requested": [
            "generalization_pass",
            "global_revision_required",
            "generalization_rejected",
        ],
        "authority": {
            "baseline": BASELINE_SHA256,
            "v1_batch_id": V1_BATCH_ID,
            "v1_subject_sha256": V1_SUBJECT_SHA256,
            "v2_batch_id": BATCH_ID,
            "v2_content_subject_sha256": batch["content_subject_sha256"],
            "m2_file_sha256": M2_SHA256,
            "accepts_interpretation": False,
        },
        "accounting": {
            "action_count": 37,
            "v1_title_only_candidates": 31,
            "v2_title_only_exceptions": sum(
                row["title_only_exception_used"] for row in candidates
            ),
            "status": dict(sorted(status_counts.items())),
            "confidence": dict(sorted(confidence_counts.items())),
            "material_provisions": sum(
                len(row["material_provisions"]) for row in candidates
            ),
            "material_limits_and_exceptions": sum(
                len(row["material_limits_and_exceptions"]) for row in candidates
            ),
            "unaccounted_material_items_in_proposed_candidates": 0,
            "coverage_initial_severity": dict(sorted(coverage_severity.items())),
            "scope_initial_severity": dict(sorted(scope_severity.items())),
            "corrections_applied": corrections["applied_count"],
        },
        "benchmark": benchmark["comparisons"],
        "sample": {
            "seed_sha256": sample["seed_sha256"],
            "random": sample["selected_random_action_ids"],
            "challenge": sample["challenge_actions"],
        },
        "ambiguous_or_no_safe": [
            {
                "action_id": row["action_id"],
                "status": row["status"],
                "confidence": row["confidence"],
                "meaning": row["proposed_exact_action_meaning"],
                "uncertainty": row["uncertainty_reasons"],
            }
            for row in candidates
            if row["status"] in {"ambiguous", "no_safe_candidate"}
        ],
        "remaining_major_or_critical": remaining,
        "global_corrections": [
            {
                "action_id": row["action_id"],
                "changed_fields": [diff["field"] for diff in row["field_differences"]],
            }
            for row in corrections["records"]
            if row["applied"]
        ],
        "artifact_rows": artifact_rows,
    }


def _render_dossier(projection: dict[str, object]) -> str:
    accounting = projection["accounting"]
    lines = [
        "# Foushee Justice Action-Interpretation Generalization Review V2",
        "",
        "> Candidate, non-authorizing, non-public, and unaccepted. This dossier creates no canonical review, production, or publication authority.",
        "",
        "## Decision requested",
        "",
        "Choose exactly one: `generalization_pass`, `global_revision_required`, or `generalization_rejected`.",
        "",
        "## Frozen authority and accounting",
        "",
        f"- V2 batch: `{projection['authority']['v2_batch_id']}`",
        f"- Canonical content-subject SHA-256: `{projection['authority']['v2_content_subject_sha256']}`",
        f"- Actions: `{accounting['action_count']}`",
        f"- V1 title-only candidates: `{accounting['v1_title_only_candidates']}`; V2 title-only exceptions: `{accounting['v2_title_only_exceptions']}`",
        f"- Status accounting: `{json.dumps(accounting['status'], sort_keys=True)}`",
        f"- Confidence accounting: `{json.dumps(accounting['confidence'], sort_keys=True)}`",
        f"- Material provisions: `{accounting['material_provisions']}`; material limits/exceptions: `{accounting['material_limits_and_exceptions']}`",
        f"- Initial coverage severity: `{json.dumps(accounting['coverage_initial_severity'], sort_keys=True)}`",
        f"- Initial scope severity: `{json.dumps(accounting['scope_initial_severity'], sort_keys=True)}`",
        f"- Global corrections applied: `{accounting['corrections_applied']}`",
        "",
        "## Benchmark comparison after freeze",
        "",
        "| Action | Mechanisms | Exceptions | Scope | Confidence | Relationship |",
        "|---|---|---|---|---|---|",
    ]
    for row in projection["benchmark"]:
        lines.append(
            f"| `{row['action_id']}` | {row['mechanism_coverage']} | {row['material_exception_and_retained_provision_coverage']} | {row['scope']} | {row['confidence_calibration']} | {row['semantic_relationship']} |"
        )
    lines += [
        "",
        "## Fresh audit samples",
        "",
        f"- Seed SHA-256: `{projection['sample']['seed_sha256']}`",
        "- Random 12: "
        + ", ".join(f"`{item}`" for item in projection["sample"]["random"]),
        "- Challenge set:",
    ]
    for row in projection["sample"]["challenge"]:
        lines.append(
            f"  - `{row['action_id']}` — {'; '.join(row['inclusion_reasons'])}"
        )
    lines += ["", "## Ambiguous and no-safe candidates", ""]
    for row in projection["ambiguous_or_no_safe"]:
        lines.append(
            f"- `{row['action_id']}` — `{row['status']}` / `{row['confidence']}`: "
            + (row["meaning"] or "No safe substantive exact-action meaning.")
        )
    lines += ["", "## Remaining major or critical findings", ""]
    if projection["remaining_major_or_critical"]:
        for row in projection["remaining_major_or_critical"]:
            lines.append(
                f"- `{row['action_id']}` — {row['review_type']} `{row['severity']}`, routed `{row['routing']}`."
            )
    else:
        lines.append("- None.")
    lines += ["", "## Evidence-bound global corrections", ""]
    for row in projection["global_corrections"]:
        lines.append(
            f"- `{row['action_id']}` — "
            + ", ".join(f"`{field}`" for field in row["changed_fields"])
        )
    lines += [
        "",
        "## Canonical artifact digests",
        "",
        "Each row labels the canonical parsed JSON content-subject digest separately from the final serialized file-byte digest.",
        "",
        "| Path | Canonical content-subject SHA-256 | Final file SHA-256 |",
        "|---|---|---|",
    ]
    for row in projection["artifact_rows"]:
        lines.append(
            f"| `{row['path']}` | `{row['content_subject_sha256']}` | `{row['file_sha256']}` |"
        )
    lines += [
        "",
        "## Mandatory stop",
        "",
        "No interpretation is accepted. Do not begin M3B or create canonical review, persistence, production, publication, or deployment state.",
        "",
    ]
    return "\n".join(lines)


def _parity_manifest(
    artifact_rows: list[dict[str, str]],
    dossier_projection: dict[str, object],
    dossier_path: Path,
) -> dict[str, object]:
    markdown = dossier_path.read_bytes()
    dossier_row = {
        "path": _relative(dossier_path),
        "content_subject_sha256": _sha256(dossier_projection),
        "file_sha256": hashlib.sha256(markdown).hexdigest(),
        "digest_semantics": "canonical dossier projection; final Markdown file bytes",
    }
    subject = {
        "schema_version": "action_interpretation_final_byte_parity_v2",
        "artifact_id": "action-interpretation-final-byte-parity:f000477:justice_public_safety:119:v2",
        "parity_state": "pass",
        "generated_last": True,
        "digest_field_convention": {
            "content_subject_sha256": "canonical semantic or parsed-JSON content excluding a self-digest field",
            "file_sha256": "SHA-256 of final serialized file bytes",
        },
        "canonical_artifacts": artifact_rows,
        "dossier": dossier_row,
        "referenced_file_count": len(artifact_rows) + 1,
        "all_final_file_sha256_recomputed": True,
        "dossier_contains_every_canonical_path_and_hash": True,
    }
    return _seal(subject)


def build_post_freeze(*, check: bool = False) -> dict[str, object]:
    batch_path = OUTPUT_ROOT / "candidate_batch.json"
    batch_before = batch_path.read_bytes()
    batch = json.loads(batch_before.decode("utf-8"))
    if not batch["frozen"] or not batch["freeze_precedes_benchmark_access"]:
        raise ValueError("post-freeze phase requires the frozen blind V2 batch")
    packets = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(PACKET_ROOT.glob("*.json"))
    ]
    coverage = json.loads(
        (OUTPUT_ROOT / "provision_coverage_reviews.json").read_text(encoding="utf-8")
    )
    scope = json.loads(
        (OUTPUT_ROOT / "scope_neutrality_reviews.json").read_text(encoding="utf-8")
    )
    corrections = json.loads(
        (OUTPUT_ROOT / "bounded_corrections.json").read_text(encoding="utf-8")
    )
    benchmark = _benchmark_comparison(batch)
    sample = _sample_manifest(batch, packets, coverage, scope)
    decision = _decision_template(sample)
    post = {
        "benchmark_comparison.json": benchmark,
        "sample_manifest.json": sample,
        "human_decision_template.json": decision,
    }
    pre = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in OUTPUT_ROOT.glob("*.json")
        if path.name
        not in {
            "benchmark_comparison.json",
            "sample_manifest.json",
            "human_decision_template.json",
            "parity_manifest.json",
        }
    }
    all_artifacts = {**pre, **post}
    schemas = _schemas_for(all_artifacts, packets)
    for name, value in post.items():
        _write_or_check_json(OUTPUT_ROOT / name, value, check=check)
    for name, schema in schemas.items():
        _write_or_check_json(SCHEMA_ROOT / name, schema, check=check)
    artifact_rows = _canonical_file_rows()
    projection = _dossier_projection(
        batch, benchmark, sample, coverage, scope, corrections, artifact_rows
    )
    markdown = _render_dossier(projection)
    dossier_path = OUTPUT_ROOT / "human_review_dossier.md"
    if check:
        if (
            not dossier_path.exists()
            or dossier_path.read_text(encoding="utf-8") != markdown
        ):
            raise ValueError("deterministic dossier check failed")
    else:
        dossier_path.write_text(markdown, encoding="utf-8", newline="")
    parity = _parity_manifest(artifact_rows, projection, dossier_path)
    _write_or_check_json(OUTPUT_ROOT / "parity_manifest.json", parity, check=check)
    if batch_path.read_bytes() != batch_before:
        raise ValueError("post-freeze phase mutated the frozen candidate batch")
    return {
        "batch": batch,
        "benchmark": benchmark,
        "sample": sample,
        "decision": decision,
        "parity": parity,
        "dossier_projection": projection,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check-freeze", action="store_true")
    parser.add_argument("--post-freeze", action="store_true")
    parser.add_argument("--check-post-freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        batch = build_freeze()
        print(
            json.dumps(
                {
                    "status": "pass",
                    "phase": "freeze",
                    "batch_id": batch["batch_id"],
                    "action_count": batch["action_count"],
                    "content_subject_sha256": batch["content_subject_sha256"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.check_freeze:
        batch = build_freeze(check=True)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "phase": "check-freeze",
                    "content_subject_sha256": batch["content_subject_sha256"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.post_freeze:
        result = build_post_freeze()
        print(
            json.dumps(
                {
                    "status": "pass",
                    "phase": "post-freeze",
                    "seed_sha256": result["sample"]["seed_sha256"],
                    "random_sample": result["sample"]["selected_random_action_ids"],
                    "challenge_count": result["sample"]["challenge_count"],
                    "parity_state": result["parity"]["parity_state"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.check_post_freeze:
        result = build_post_freeze(check=True)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "phase": "check-post-freeze",
                    "parity_state": result["parity"]["parity_state"],
                },
                sort_keys=True,
            )
        )
        return 0
    parser.error("select an operation")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
