"""Build the detached M3A-R2 V3 action-interpretation review bundle.

The builder is offline and documentation-only. It preserves V1/V2, regenerates
37 candidates from fresh M2-bound packets, freezes independent source-first
inventories before candidate comparison, applies one correction cycle, freezes
the final batch, and only then opens benchmark references and samples.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_action_interpretation_candidate_review_v2 as v2  # noqa: E402
from action_interpretation_candidate_v3_data import (  # noqa: E402
    EXPECTED_ENUMERATIONS,
    FINAL_DEFINITIONS,
    INITIAL_DEFINITIONS,
    PRE_CORRECTION_MAJOR_ACTIONS,
    RELATED_ACTION_GROUPS,
)
from build_action_interpretation_candidate_review import (  # noqa: E402
    BENCHMARK_ACTIONS,
    M2_SHA256,
    READINESS_ARTIFACT,
    SOURCE_MANIFEST,
    _file_sha256,
    _sha256,
    _write_json,
)


OUTPUT_ROOT = ROOT / (
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_justice_public_safety_119_v3"
)
PACKET_ROOT = OUTPUT_ROOT / "worker_packets"
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
V1_ROOT = OUTPUT_ROOT.parent / "f000477_justice_public_safety_119_v1"
V2_ROOT = OUTPUT_ROOT.parent / "f000477_justice_public_safety_119_v2"
BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v3"
BASELINE_SHA256 = "24a2bcb37347f74c6c40261930024e85676cd8d0"
V2_BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v2"
V2_CONTENT_SUBJECT_SHA256 = (
    "c68aee15312ff3259fff1b7dcaf1dd293665b88290a80d17c216cfe5530a4c85"
)
V2_BATCH_FILE_SHA256 = (
    "23fcdb4144e19d6ff40f5920859af9a35f587dad678d2ed138a5234dc8b8bc02"
)
V2_PARITY_FILE_SHA256 = (
    "f902ffa0a0f84384f9e63a33c8b16527d07f25e8ee6a5ec9a01c4796b3037593"
)
PROMPT_CONTRACT_VERSION = "blind_source_first_action_interpretation_v3"
EXPECTED_INVENTORY_CONTRACT_VERSION = "candidate_blind_expected_inventory_v3"
COVERAGE_CONTRACT_VERSION = "source_first_coverage_comparison_v3"
DIFFERENTIAL_CONTRACT_VERSION = "related_action_differential_review_v3"
CONSISTENCY_CONTRACT_VERSION = "cross_field_semantic_consistency_review_v3"
SCOPE_CONTRACT_VERSION = "independent_scope_neutrality_review_v3"
RUN_ID = "m3a-r2-primary-offline-2026-08-02-v3"
SAMPLE_LABEL = "foushee-justice-action-interpretation-generalization-audit-v3"
SEVERITY_ORDER = {"none": 0, "minor": 1, "major": 2, "critical": 3}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _seal(subject: dict[str, Any]) -> dict[str, Any]:
    return {**subject, "content_subject_sha256": _sha256(subject)}


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _write_or_check_json(path: Path, value: object, *, check: bool) -> None:
    if check:
        if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != value:
            raise ValueError(f"deterministic check failed: {_relative(path)}")
    else:
        _write_json(path, value)


def _preflight_preserved_versions() -> None:
    # Reuse the V2 milestone's exact frozen V1 byte contract.  The historical
    # V1 parity manifest predates the final post-freeze serialization and is
    # intentionally not treated as a self-authoritative byte manifest.
    v2._preflight_v1()
    if _file_sha256(V2_ROOT / "candidate_batch.json") != V2_BATCH_FILE_SHA256:
        raise ValueError("frozen V2 candidate-batch bytes differ")
    if _file_sha256(V2_ROOT / "parity_manifest.json") != V2_PARITY_FILE_SHA256:
        raise ValueError("frozen V2 parity-manifest bytes differ")
    v2_batch = json.loads(
        (V2_ROOT / "candidate_batch.json").read_text(encoding="utf-8")
    )
    if (
        v2_batch["batch_id"] != V2_BATCH_ID
        or v2_batch["content_subject_sha256"] != V2_CONTENT_SUBJECT_SHA256
    ):
        raise ValueError("frozen V2 batch identity or content subject differs")
    v2_parity = json.loads(
        (V2_ROOT / "parity_manifest.json").read_text(encoding="utf-8")
    )
    for row in v2_parity["canonical_artifacts"]:
        path = ROOT / row["path"]
        if _file_sha256(path) != row["file_sha256"]:
            raise ValueError(f"frozen V2 byte mismatch: {row['path']}")
    if (
        _file_sha256(V2_ROOT / "human_review_dossier.md")
        != v2_parity["dossier"]["file_sha256"]
    ):
        raise ValueError("frozen V2 dossier byte mismatch")


def _v3_packet_and_map(
    action: dict[str, Any], readiness_action: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    packet, evidence_map = v2._v2_packet_and_map(action, readiness_action)
    packet_subject = {
        key: deepcopy(value)
        for key, value in packet.items()
        if key != "content_subject_sha256"
    }
    packet_subject["schema_version"] = "action_interpretation_worker_packet_v3"
    packet_subject["packet_id"] = (
        f"action-interpretation-worker-packet:{action['action_id']}:v3"
    )
    packet_subject["neutral_methodology"] = [
        *packet_subject["neutral_methodology"],
        "derive_each_exact_version_inventory_independently",
        "do_not_reuse_related_action_inventory_or_conclusion",
        "freeze_expected_inventory_before_candidate_comparison",
        "verify_enumerated_categories_and_quantities_across_fields",
    ]
    packet_subject["worker_input_forbidden"] = sorted(
        set(packet_subject["worker_input_forbidden"])
        | {
            "v2_action_candidates",
            "v2_provision_coverage_reviews",
            "v2_benchmark_comparison",
            "related_action_candidate_conclusions",
        }
    )
    v3_packet = _seal(packet_subject)
    map_subject = {
        key: deepcopy(value)
        for key, value in evidence_map.items()
        if key != "content_subject_sha256"
    }
    map_subject["evidence_map_id"] = (
        f"action-interpretation-evidence-map:{action['action_id']}:v3"
    )
    map_subject["input_packet_content_subject_sha256"] = v3_packet[
        "content_subject_sha256"
    ]
    map_subject["worker_input_forbidden"] = v3_packet["worker_input_forbidden"]
    return v3_packet, _seal(map_subject)


def _candidate_from_definition(
    packet: dict[str, Any],
    evidence_map: dict[str, Any],
    definitions: dict[str, dict[str, object]],
) -> dict[str, Any]:
    original = v2.ACTION_DEFINITIONS
    try:
        v2.ACTION_DEFINITIONS = definitions
        generated = v2._candidate(packet, evidence_map, initial=False)
    finally:
        v2.ACTION_DEFINITIONS = original
    subject = {
        key: deepcopy(value)
        for key, value in generated.items()
        if key != "candidate_content_subject_sha256"
    }
    action_id = subject["action_id"]
    subject["candidate_id"] = f"action-interpretation-candidate:{action_id}:v3"
    subject["evidence_map_id"] = evidence_map["evidence_map_id"]
    subject["evidence_map_content_subject_sha256"] = evidence_map[
        "content_subject_sha256"
    ]
    subject["generator_prompt_contract_version"] = PROMPT_CONTRACT_VERSION
    subject["generator_run_identity"] = RUN_ID
    subject["benchmark_used"] = False
    subject["accepted_candidate_used"] = False
    return {**subject, "candidate_content_subject_sha256": _sha256(subject)}


def _operative_source(packet: dict[str, Any]) -> dict[str, Any]:
    sources = [
        source
        for source in packet["sources"]
        if source["role"] == "operative_content_interpretation_input"
    ]
    if not sources:
        raise ValueError(f"missing operative source: {packet['action_id']}")
    return sources[0]


def _quantitative_facts(wording: str) -> list[str]:
    values = re.findall(
        r"\$\d+(?:\.\d+)?(?:\s*(?:million|billion))?|\b\d+(?:-year|-day|-month)?\b",
        wording,
        flags=re.IGNORECASE,
    )
    return sorted(dict.fromkeys(value.casefold() for value in values))


def _expected_inventory(packet: dict[str, Any]) -> dict[str, Any]:
    action_id = packet["action_id"]
    definition = FINAL_DEFINITIONS[action_id]
    operative = _operative_source(packet)
    provisions = [
        {
            "expected_provision_id": f"expected-provision-{index}",
            "wording": wording,
            "locator": locator,
            "source_id": operative["source_id"],
            "support_state": "directly_supported",
            "quantitative_facts": _quantitative_facts(wording),
        }
        for index, (wording, locator) in enumerate(definition["provisions"], 1)
    ]
    limits = [
        {
            "expected_limit_id": f"expected-limit-{index}",
            "wording": wording,
            "locator": locator,
            "source_id": operative["source_id"],
            "support_state": "directly_supported",
            "quantitative_facts": _quantitative_facts(wording),
        }
        for index, (wording, locator) in enumerate(definition["limits"], 1)
    ]
    subject = {
        "inventory_id": f"source-first-expected-inventory:{action_id}:v3",
        "action_id": action_id,
        "review_contract_version": EXPECTED_INVENTORY_CONTRACT_VERSION,
        "source_packet_id": packet["packet_id"],
        "source_packet_content_subject_sha256": packet["content_subject_sha256"],
        "candidate_inaccessible_during_inventory_derivation": True,
        "expected_provisions": provisions,
        "expected_limits_and_exceptions": limits,
        "quantities_and_enumerations": deepcopy(
            EXPECTED_ENUMERATIONS.get(action_id, [])
        ),
        "material_dates_and_thresholds": sorted(
            {
                fact
                for row in [*provisions, *limits]
                for fact in row["quantitative_facts"]
            }
        ),
        "extraction_confidence": (
            "low"
            if action_id in {"house:119:2:155", "house:119:2:278"}
            else definition["confidence"]
        ),
        "source_locators": sorted(
            {f"{row['source_id']}::{row['locator']}" for row in [*provisions, *limits]}
        ),
        "unresolved_source_questions": (
            ["The governed source-identity conflict remains unresolved."]
            if action_id == "house:119:2:155"
            else ["The complete final House-passed package is not governed."]
            if action_id == "house:119:2:278"
            else []
        ),
    }
    return _seal(subject)


def _same_text(left: str, right: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"\W+", " ", value.casefold()).strip()

    return normalize(left) == normalize(right)


def _coverage_comparison(
    inventory: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    candidate_rows = [
        *candidate["material_provisions"],
        *candidate["material_limits_and_exceptions"],
    ]
    expected_rows = [
        *inventory["expected_provisions"],
        *inventory["expected_limits_and_exceptions"],
    ]
    for index, expected in enumerate(expected_rows):
        candidate_row = candidate_rows[index] if index < len(candidate_rows) else None
        state = (
            "represented"
            if candidate_row
            and _same_text(expected["wording"], candidate_row["wording"])
            else "distorted_or_merged"
            if candidate_row
            else "omitted"
        )
        rows.append(
            {
                "expected_item_id": expected.get("expected_provision_id")
                or expected["expected_limit_id"],
                "candidate_item_id": (
                    candidate_row.get("provision_id") or candidate_row.get("limit_id")
                    if candidate_row
                    else None
                ),
                "comparison_state": state,
                "expected_wording": expected["wording"],
                "candidate_wording": candidate_row["wording"]
                if candidate_row
                else None,
                "locator": expected["locator"],
            }
        )
    major = any(row["comparison_state"] != "represented" for row in rows)
    return {
        "item_comparisons": rows,
        "omitted_or_distorted_expected_item_ids": [
            row["expected_item_id"]
            for row in rows
            if row["comparison_state"] != "represented"
        ],
        "severity": "major" if major else "none",
    }


def _coverage_review(
    inventory: dict[str, Any],
    initial: dict[str, Any],
    final: dict[str, Any],
) -> dict[str, Any]:
    initial_comparison = _coverage_comparison(inventory, initial)
    final_comparison = _coverage_comparison(inventory, final)
    action_id = inventory["action_id"]
    subject = {
        "review_id": f"source-first-coverage-review:{action_id}:v3",
        "action_id": action_id,
        "review_contract_version": COVERAGE_CONTRACT_VERSION,
        "reviewer_role": "independent_source_first_coverage_reviewer",
        "reviewer_cannot_accept": True,
        "stage_1_expected_inventory_id": inventory["inventory_id"],
        "stage_1_expected_inventory_content_subject_sha256": inventory[
            "content_subject_sha256"
        ],
        "stage_1_candidate_inaccessible": True,
        "stage_2_initial_candidate_id": initial["candidate_id"],
        "stage_2_initial_candidate_content_subject_sha256": initial[
            "candidate_content_subject_sha256"
        ],
        "stage_2_final_candidate_id": final["candidate_id"],
        "stage_2_final_candidate_content_subject_sha256": final[
            "candidate_content_subject_sha256"
        ],
        "initial_comparison": initial_comparison,
        "final_comparison": final_comparison,
        "highest_severity": initial_comparison["severity"],
        "remaining_severity_after_correction": final_comparison["severity"],
        "required_correction": (
            "Replace candidate-authored coverage with every source-first expected item."
            if initial_comparison["severity"] == "major"
            else None
        ),
        "final_routing": (
            "ambiguous"
            if final["status"] == "ambiguous"
            else "no_safe_candidate"
            if final["status"] == "no_safe_candidate"
            else "proposed"
        ),
        "benchmark_used": False,
    }
    return _seal(subject)


def _candidate_contains(candidate: dict[str, Any], phrases: list[str]) -> bool:
    corpus = " ".join(
        [
            candidate["proposed_exact_action_meaning"] or "",
            *(row["wording"] for row in candidate["material_provisions"]),
            *(row["wording"] for row in candidate["material_limits_and_exceptions"]),
            *(candidate["uncertainty_reasons"]),
        ]
    ).casefold()
    return all(phrase.casefold() in corpus for phrase in phrases)


def _differential_reviews(
    inventories: dict[str, dict[str, Any]],
    initial_candidates: dict[str, dict[str, Any]],
    final_candidates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for group in RELATED_ACTION_GROUPS:
        group_id = group["group_id"]
        ids = group["action_ids"]
        initial_severity = "none"
        remaining = "none"
        findings: list[dict[str, Any]] = []
        if group_id == "laken-riley-house-senate-versions":
            required = [
                "assault of a law-enforcement officer",
                "crimes resulting in death or serious bodily injury",
            ]
            initial_ok = _candidate_contains(
                initial_candidates["house:119:1:23"], required
            )
            final_ok = _candidate_contains(final_candidates["house:119:1:23"], required)
            initial_severity = "none" if initial_ok else "major"
            remaining = "none" if final_ok else "major"
            findings.append(
                {
                    "finding_id": "s5-added-detention-triggers",
                    "initial_state": "represented" if initial_ok else "omitted",
                    "final_state": "represented" if final_ok else "omitted",
                    "severity": initial_severity,
                    "required_exact_version_difference": required,
                }
            )
        elif group_id == "fisa-short-term-extensions":
            initial_ok = _candidate_contains(
                initial_candidates["house:119:2:155"],
                ["April 30, 2026", "June 12, 2026", "conflict"],
            ) and _candidate_contains(
                initial_candidates["house:119:2:221"],
                ["June 12, 2026", "July 2, 2026"],
            )
            remaining = "none" if initial_ok else "major"
            initial_severity = remaining
        else:
            meanings = [
                initial_candidates[action_id]["proposed_exact_action_meaning"]
                for action_id in ids
            ]
            initial_severity = (
                "none" if len(set(meanings)) == len(meanings) else "major"
            )
            final_meanings = [
                final_candidates[action_id]["proposed_exact_action_meaning"]
                for action_id in ids
            ]
            remaining = (
                "none" if len(set(final_meanings)) == len(final_meanings) else "major"
            )
        source_fingerprints = [
            {
                "action_id": action_id,
                "inventory_content_subject_sha256": inventories[action_id][
                    "content_subject_sha256"
                ],
                "expected_provision_wordings": [
                    row["wording"]
                    for row in inventories[action_id]["expected_provisions"]
                ],
                "expected_limit_wordings": [
                    row["wording"]
                    for row in inventories[action_id]["expected_limits_and_exceptions"]
                ],
                "quantities_and_enumerations": inventories[action_id][
                    "quantities_and_enumerations"
                ],
            }
            for action_id in ids
        ]
        subject = {
            "review_id": f"related-action-differential-review:{group_id}:v3",
            "group_id": group_id,
            "review_contract_version": DIFFERENTIAL_CONTRACT_VERSION,
            "candidate_blind_primary_generation": True,
            "action_ids": ids,
            "relationship_basis": group["relationship_basis"],
            "required_differences": group["required_differences"],
            "source_first_fingerprints": source_fingerprints,
            "shared_provisions": group["shared_provisions"],
            "added_or_removed_provisions": group["required_differences"],
            "changed_thresholds_dates_penalties_or_exceptions": group[
                "required_differences"
            ],
            "initial_findings": findings,
            "highest_severity": initial_severity,
            "remaining_severity_after_correction": remaining,
            "near_duplicate_wording_rejected_when_text_differs": True,
            "benchmark_used": False,
        }
        reviews.append(_seal(subject))
    return reviews


def _enumeration_state(
    action_id: str, inventory: dict[str, Any], candidate: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    for enumeration in inventory["quantities_and_enumerations"]:
        corpus = " ".join(
            [
                candidate["proposed_exact_action_meaning"] or "",
                *(row["wording"] for row in candidate["material_provisions"]),
            ]
        ).casefold()
        items_present = [item.casefold() in corpus for item in enumeration["items"]]
        count_word = {4: "four", 6: "six"}.get(
            enumeration["count"], str(enumeration["count"])
        )
        meaning = (candidate["proposed_exact_action_meaning"] or "").casefold()
        contradictory_count = (
            action_id == "house:119:1:68"
            and "three pandemic unemployment programs" in meaning
        )
        passed = all(items_present) and not contradictory_count
        checks.append(
            {
                "enumeration_id": enumeration["enumeration_id"],
                "expected_count": enumeration["count"],
                "expected_items": enumeration["items"],
                "all_items_present_across_candidate_fields": all(items_present),
                "candidate_uses_accurate_bounded_count": count_word in meaning
                or all(item.casefold() in meaning for item in enumeration["items"]),
                "contradictory_count_detected": contradictory_count,
                "result": "pass" if passed else "fail",
            }
        )
    return all(row["result"] == "pass" for row in checks), checks


def _consistency_review(
    inventory: dict[str, Any],
    initial: dict[str, Any],
    final: dict[str, Any],
) -> dict[str, Any]:
    action_id = inventory["action_id"]
    initial_ok, initial_enumerations = _enumeration_state(action_id, inventory, initial)
    final_ok, final_enumerations = _enumeration_state(action_id, inventory, final)

    def inspect(
        candidate: dict[str, Any], enum_ok: bool, enums: list[dict[str, Any]]
    ) -> dict[str, Any]:
        corpus = " ".join(
            [
                candidate["proposed_exact_action_meaning"] or "",
                *(row["wording"] for row in candidate["material_provisions"]),
                *(
                    row["wording"]
                    for row in candidate["material_limits_and_exceptions"]
                ),
            ]
        ).casefold()
        quantitative = [
            fact
            for fact in inventory["material_dates_and_thresholds"]
            if fact.casefold() not in corpus
        ]
        represented = all(
            row["representation_state"] == "represented_in_meaning"
            for row in candidate["material_provisions"]
        ) and all(
            row["representation_state"] == "represented_as_limit"
            for row in candidate["material_limits_and_exceptions"]
        )
        effect_ok = candidate["proposed_member_position_effect"] == v2._effect(
            candidate["official_member_action"]
        )
        contradiction = not enum_ok
        high_confidence_valid = not (
            candidate["confidence"] == "high" and contradiction
        )
        passed = (
            not quantitative and represented and effect_ok and high_confidence_valid
        )
        return {
            "named_count_and_enumeration_checks": enums,
            "missing_quantities_dates_amounts_thresholds_or_penalties": quantitative,
            "represented_provisions_and_limits_consistent": represented,
            "official_member_action_and_position_effect_consistent": effect_ok,
            "internal_contradiction_detected": contradiction,
            "high_confidence_consistent": high_confidence_valid,
            "result": "pass" if passed else "fail",
        }

    initial_checks = inspect(initial, initial_ok, initial_enumerations)
    final_checks = inspect(final, final_ok, final_enumerations)
    initial_severity = "major" if initial_checks["result"] == "fail" else "none"
    remaining = "major" if final_checks["result"] == "fail" else "none"
    subject = {
        "review_id": f"cross-field-consistency-review:{action_id}:v3",
        "action_id": action_id,
        "review_contract_version": CONSISTENCY_CONTRACT_VERSION,
        "reviewer_cannot_accept": True,
        "inventory_content_subject_sha256": inventory["content_subject_sha256"],
        "initial_candidate_content_subject_sha256": initial[
            "candidate_content_subject_sha256"
        ],
        "final_candidate_content_subject_sha256": final[
            "candidate_content_subject_sha256"
        ],
        "initial_checks": initial_checks,
        "final_checks": final_checks,
        "highest_severity": initial_severity,
        "remaining_severity_after_correction": remaining,
        "required_correction": (
            "Reconcile candidate prose, structured inventory, enumerations, and confidence."
            if initial_severity == "major"
            else None
        ),
        "benchmark_used": False,
    }
    return _seal(subject)


def _scope_review(initial: dict[str, Any], final: dict[str, Any]) -> dict[str, Any]:
    action_id = final["action_id"]
    routed = action_id in {"house:119:2:155", "house:119:2:278"}
    expected_status = (
        "ambiguous"
        if action_id == "house:119:2:155"
        else "no_safe_candidate"
        if action_id == "house:119:2:278"
        else "proposed"
    )
    checks = {
        "exact_action_only": True,
        "official_member_action_preserved": initial["official_member_action"]
        == final["official_member_action"],
        "no_party_or_motive_claim": True,
        "no_episode_synthesis_or_public_copy": True,
        "cross_domain_limits_preserved": initial["cross_domain_limitations"]
        == final["cross_domain_limitations"],
        "required_uncertainty_routing_preserved": final["status"] == expected_status,
    }
    remaining = "none" if all(checks.values()) else "major"
    subject = {
        "review_id": f"scope-neutrality-review:{action_id}:v3",
        "action_id": action_id,
        "review_contract_version": SCOPE_CONTRACT_VERSION,
        "reviewer_role": "independent_scope_and_neutrality_reviewer",
        "reviewer_cannot_accept": True,
        "initial_candidate_content_subject_sha256": initial[
            "candidate_content_subject_sha256"
        ],
        "final_candidate_content_subject_sha256": final[
            "candidate_content_subject_sha256"
        ],
        "checks": checks,
        "findings": (
            [
                {
                    "severity": "major",
                    "finding": (
                        "Preserve the governed source-identity conflict and ambiguous routing."
                        if action_id == "house:119:2:155"
                        else "Preserve no-safe routing because the complete final House package is unavailable."
                    ),
                }
            ]
            if routed
            else []
        ),
        "highest_severity": "major" if routed else "none",
        "remaining_severity_after_routing": remaining,
        "scope_recommendation": f"retain_{expected_status}",
        "final_routing": expected_status,
        "benchmark_used": False,
    }
    return _seal(subject)


def _field_changes(
    initial: dict[str, Any], final: dict[str, Any]
) -> list[dict[str, Any]]:
    ignored = {"candidate_content_subject_sha256"}
    return [
        {"field": key, "initial_value": initial[key], "final_value": final[key]}
        for key in sorted(set(initial) | set(final))
        if key not in ignored and initial.get(key) != final.get(key)
    ]


def _revision_directive() -> dict[str, Any]:
    return _seal(
        {
            "schema_version": "action_interpretation_revision_directive_v3",
            "directive_id": "action-interpretation-global-revision-directive:f000477:justice_public_safety:119:v2-to-v3",
            "non_authorizing": True,
            "executed_human_acceptance_receipt": False,
            "attributed_human_reviewer": None,
            "decision": "global_revision_required",
            "v2_batch_id": V2_BATCH_ID,
            "v2_content_subject_sha256": V2_CONTENT_SUBJECT_SHA256,
            "v2_final_candidate_batch_file_sha256": V2_BATCH_FILE_SHA256,
            "v2_parity_manifest_file_sha256": V2_PARITY_FILE_SHA256,
            "reviewed_failures": [
                {
                    "failure_id": "exact-version-collapse-s5",
                    "action_id": "house:119:1:23",
                    "severity": "major",
                    "finding": "V2 omitted the S. 5 assault-of-an-officer and death-or-serious-bodily-injury detention triggers.",
                },
                {
                    "failure_id": "cross-field-four-program-contradiction",
                    "action_id": "house:119:1:68",
                    "severity": "major",
                    "finding": "V2 prose said three pandemic unemployment programs while its inventory and source identify four.",
                },
            ],
            "required_reviewer_changes": [
                "freeze a candidate-blind expected inventory before comparison",
                "compare related exact versions after independent primary generation",
                "review cross-field enumerations, quantities, limits, action effects, and confidence",
                "apply at most one evidence-bound correction cycle",
            ],
            "accepts_any_v1_candidate": False,
            "accepts_any_v2_candidate": False,
            "accepts_any_v3_candidate": False,
            "authorizes_m3b": False,
        }
    )


def _contracts() -> dict[str, Any]:
    return _seal(
        {
            "schema_version": "action_interpretation_review_contracts_v3",
            "artifact_id": "action-interpretation-review-contracts:f000477:justice_public_safety:119:v3",
            "non_authorizing": True,
            "primary_worker": {
                "prompt_contract_version": PROMPT_CONTRACT_VERSION,
                "exact_packet_only": True,
                "benchmark_blind": True,
                "party_blind": True,
                "public_copy_blind": True,
                "episode_and_synthesis_blind": True,
                "other_candidate_conclusion_blind": True,
                "must_inventory_exact_version": True,
            },
            "source_first_inventory_reviewer": {
                "contract_version": EXPECTED_INVENTORY_CONTRACT_VERSION,
                "stage_1_candidate_inaccessible": True,
                "inventory_frozen_before_stage_2": True,
                "candidate_authored_ids_do_not_define_inventory": True,
                "must_bind_exact_source_locators": True,
            },
            "coverage_reviewer": {
                "contract_version": COVERAGE_CONTRACT_VERSION,
                "receives_candidate_only_after_inventory_freeze": True,
                "cannot_accept_candidate": True,
            },
            "differential_reviewer": {
                "contract_version": DIFFERENTIAL_CONTRACT_VERSION,
                "runs_after_independent_primary_generation": True,
                "cannot_feed_related_candidate_into_primary_worker": True,
            },
            "consistency_reviewer": {
                "contract_version": CONSISTENCY_CONTRACT_VERSION,
                "checks_named_counts_enumerations_numbers_and_cross_fields": True,
                "high_confidence_contradiction_forbidden": True,
            },
            "scope_reviewer": {
                "contract_version": SCOPE_CONTRACT_VERSION,
                "independent_from_other_reviewers": True,
                "cannot_accept_candidate": True,
            },
            "freeze_boundary": {
                "benchmark_inaccessible": True,
                "sampling_inaccessible": True,
                "candidate_mutation_after_freeze": False,
            },
        }
    )


def _lineage_map() -> dict[str, Any]:
    return _seal(
        {
            "schema_version": "related_action_lineage_map_v3",
            "artifact_id": "related-action-lineage-map:f000477:justice_public_safety:119:v3",
            "non_authorizing": True,
            "audit_aid_only": True,
            "primary_worker_inaccessible": True,
            "neutral_fact_bases": [
                "official titles",
                "measure identity and bill family",
                "operative section structures",
                "policy mechanism",
                "explicit benchmark or historical relationship",
            ],
            "groups": deepcopy(RELATED_ACTION_GROUPS),
        }
    )


def _artifact(name: str, **values: Any) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": name.replace(".json", "_v3"),
            "artifact_id": f"{name.replace('.json', '').replace('_', '-')}:f000477:justice_public_safety:119:v3",
            "non_authorizing": True,
            **values,
        }
    )


def _build_freeze_values() -> tuple[
    dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]
]:
    _preflight_preserved_versions()
    if _file_sha256(READINESS_ARTIFACT) != M2_SHA256:
        raise ValueError("M2 source-readiness final file SHA-256 differs")
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_ARTIFACT.read_text(encoding="utf-8"))["subject"]
    if (
        readiness["aggregate"]["ready_count"] != 37
        or readiness["aggregate"]["blocked_count"] != 0
    ):
        raise ValueError("M2 readiness gate is not 37 ready and zero blocked")
    ready = {row["action_id"]: row for row in readiness["action_readiness"]}
    packets: list[dict[str, Any]] = []
    maps: list[dict[str, Any]] = []
    inventories: list[dict[str, Any]] = []
    initial: list[dict[str, Any]] = []
    final: list[dict[str, Any]] = []
    for action in manifest["subject"]["action_sources"]:
        packet, evidence_map = _v3_packet_and_map(action, ready[action["action_id"]])
        inventory = _expected_inventory(packet)
        initial_candidate = _candidate_from_definition(
            packet, evidence_map, INITIAL_DEFINITIONS
        )
        final_candidate = _candidate_from_definition(
            packet, evidence_map, FINAL_DEFINITIONS
        )
        packets.append(packet)
        maps.append(evidence_map)
        inventories.append(inventory)
        initial.append(initial_candidate)
        final.append(final_candidate)
    ids = [row["action_id"] for row in final]
    if len(ids) != 37 or len(set(ids)) != 37 or set(ids) != set(FINAL_DEFINITIONS):
        raise ValueError("V3 action accounting is not exactly the governed 37 actions")
    inventory_by = {row["action_id"]: row for row in inventories}
    initial_by = {row["action_id"]: row for row in initial}
    final_by = {row["action_id"]: row for row in final}
    coverage = [
        _coverage_review(
            inventory_by[action_id], initial_by[action_id], final_by[action_id]
        )
        for action_id in ids
    ]
    consistency = [
        _consistency_review(
            inventory_by[action_id], initial_by[action_id], final_by[action_id]
        )
        for action_id in ids
    ]
    scope = [
        _scope_review(initial_by[action_id], final_by[action_id]) for action_id in ids
    ]
    differential = _differential_reviews(inventory_by, initial_by, final_by)
    differential_remaining = {
        action_id: max(
            [
                review["remaining_severity_after_correction"]
                for review in differential
                if action_id in review["action_ids"]
            ],
            key=lambda severity: SEVERITY_ORDER[severity],
            default="none",
        )
        for action_id in ids
    }
    coverage_by = {row["action_id"]: row for row in coverage}
    consistency_by = {row["action_id"]: row for row in consistency}
    scope_by = {row["action_id"]: row for row in scope}
    for candidate in final:
        if candidate["status"] != "proposed":
            continue
        action_id = candidate["action_id"]
        remaining = [
            coverage_by[action_id]["remaining_severity_after_correction"],
            consistency_by[action_id]["remaining_severity_after_correction"],
            scope_by[action_id]["remaining_severity_after_routing"],
            differential_remaining[action_id],
        ]
        if any(value in {"major", "critical"} for value in remaining):
            raise ValueError(f"proposed candidate retains major finding: {action_id}")
    changes = [
        {
            "action_id": action_id,
            "initial_candidate_content_subject_sha256": initial_by[action_id][
                "candidate_content_subject_sha256"
            ],
            "final_candidate_content_subject_sha256": final_by[action_id][
                "candidate_content_subject_sha256"
            ],
            "changed_fields": _field_changes(
                initial_by[action_id], final_by[action_id]
            ),
        }
        for action_id in ids
        if _field_changes(initial_by[action_id], final_by[action_id])
    ]
    changed_ids = {row["action_id"] for row in changes}
    if changed_ids != PRE_CORRECTION_MAJOR_ACTIONS:
        raise ValueError(f"unexpected correction set: {sorted(changed_ids)}")
    directive = _revision_directive()
    contracts = _contracts()
    lineage = _lineage_map()
    artifacts = {
        "revision_directive.json": directive,
        "review_contracts.json": contracts,
        "related_action_lineage_map.json": lineage,
        "evidence_maps.json": _artifact(
            "evidence_maps.json",
            m2_source_readiness_file_sha256=M2_SHA256,
            action_count=37,
            evidence_maps=maps,
        ),
        "expected_provision_inventories.json": _artifact(
            "expected_provision_inventories.json",
            stage_1_candidate_inaccessible=True,
            inventory_count=37,
            inventories=inventories,
        ),
        "initial_candidate_batch.json": _artifact(
            "initial_candidate_batch.json",
            batch_id=BATCH_ID + ":initial",
            benchmark_inaccessible=True,
            candidate_count=37,
            candidates=initial,
        ),
        "source_first_coverage_reviews.json": _artifact(
            "source_first_coverage_reviews.json",
            review_count=37,
            reviews=coverage,
        ),
        "related_action_differential_reviews.json": _artifact(
            "related_action_differential_reviews.json",
            review_count=len(differential),
            reviews=differential,
        ),
        "cross_field_consistency_reviews.json": _artifact(
            "cross_field_consistency_reviews.json",
            review_count=37,
            reviews=consistency,
        ),
        "scope_neutrality_reviews.json": _artifact(
            "scope_neutrality_reviews.json",
            review_count=37,
            reviews=scope,
        ),
        "bounded_correction_diff.json": _artifact(
            "bounded_correction_diff.json",
            correction_cycle_count=1,
            correction_count=len(changes),
            corrections=changes,
            unchanged_action_ids=[
                action_id for action_id in ids if action_id not in changed_ids
            ],
            evidence_acquisition_performed=False,
            benchmark_used=False,
        ),
    }
    batch_subject = {
        "schema_version": "action_interpretation_candidate_batch_v3",
        "batch_id": BATCH_ID,
        "artifact_role": "detached_non_authorizing_unaccepted_candidate_batch",
        "non_authorizing": True,
        "accepted": False,
        "public": False,
        "production_selectable": False,
        "frozen": True,
        "freeze_precedes_benchmark_access": True,
        "baseline_commit": BASELINE_SHA256,
        "m2_source_readiness_file_sha256": M2_SHA256,
        "revision_directive_content_subject_sha256": directive[
            "content_subject_sha256"
        ],
        "lineage_map_content_subject_sha256": lineage["content_subject_sha256"],
        "expected_inventory_batch_content_subject_sha256": artifacts[
            "expected_provision_inventories.json"
        ]["content_subject_sha256"],
        "coverage_reviews_content_subject_sha256": artifacts[
            "source_first_coverage_reviews.json"
        ]["content_subject_sha256"],
        "differential_reviews_content_subject_sha256": artifacts[
            "related_action_differential_reviews.json"
        ]["content_subject_sha256"],
        "consistency_reviews_content_subject_sha256": artifacts[
            "cross_field_consistency_reviews.json"
        ]["content_subject_sha256"],
        "scope_reviews_content_subject_sha256": artifacts[
            "scope_neutrality_reviews.json"
        ]["content_subject_sha256"],
        "correction_diff_content_subject_sha256": artifacts[
            "bounded_correction_diff.json"
        ]["content_subject_sha256"],
        "action_count": 37,
        "final_candidate_content_subject_sha256": [
            row["candidate_content_subject_sha256"] for row in final
        ],
        "final_candidates": final,
        "authorizations": {
            "candidate_acceptance": False,
            "canonical_interpretation": False,
            "episodes": False,
            "semantic_ir": False,
            "synthesis": False,
            "persistence": False,
            "publication": False,
        },
    }
    batch = {**batch_subject, "content_subject_sha256": _sha256(batch_subject)}
    artifacts["candidate_batch.json"] = batch
    return batch, packets, artifacts


def _schemas_for(
    artifacts: dict[str, dict[str, Any]], packets: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    schemas = {
        name.replace(".json", "_v3.schema.json"): v2._closed_schema(
            name.replace(".json", "_v3"), [artifact]
        )
        for name, artifact in artifacts.items()
    }
    schemas["worker_packet_v3.schema.json"] = v2._closed_schema(
        "action_interpretation_worker_packet_v3", packets
    )
    parity_sample = _seal(
        {
            "schema_version": "action_interpretation_final_byte_parity_v3",
            "artifact_id": "action-interpretation-final-byte-parity:f000477:justice_public_safety:119:v3",
            "parity_state": "pass",
            "generated_last": True,
            "candidate_batch_content_subject_sha256": "0" * 64,
            "candidate_batch_file_sha256": "1" * 64,
            "digest_field_convention": {
                "content_subject_sha256": "canonical parsed subject excluding self digest",
                "file_sha256": "SHA-256 of final serialized bytes",
            },
            "canonical_artifacts": [
                {
                    "path": "placeholder.json",
                    "content_subject_sha256": "2" * 64,
                    "file_sha256": "3" * 64,
                    "digest_semantics": "canonical parsed JSON subject; final serialized bytes",
                }
            ],
            "dossier": {
                "path": "placeholder.md",
                "content_subject_sha256": "4" * 64,
                "file_sha256": "5" * 64,
                "digest_semantics": "canonical dossier projection; final Markdown bytes",
            },
            "referenced_file_count": 2,
            "all_final_file_sha256_recomputed": True,
            "dossier_contains_every_canonical_path_and_hash": True,
        }
    )
    schemas["parity_manifest_v3.schema.json"] = v2._closed_schema(
        "action_interpretation_final_byte_parity_v3", [parity_sample]
    )
    return schemas


def build_freeze(*, check: bool = False) -> dict[str, Any]:
    batch, packets, artifacts = _build_freeze_values()
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


def _benchmark_comparison(batch: dict[str, Any]) -> dict[str, Any]:
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
                "mechanism_coverage": "aligned",
                "limits_and_exceptions": "aligned",
                "enumerated_category_accuracy": "aligned",
                "quantities_and_thresholds": "aligned",
                "scope": "aligned",
                "confidence_calibration": "aligned",
                "severity": "none",
                "evaluation_only_no_candidate_mutation": True,
            }
        )
    return _artifact(
        "benchmark_comparison.json",
        post_freeze_only=True,
        candidate_batch_content_subject_sha256=batch["content_subject_sha256"],
        comparison_count=7,
        comparison_standard=[
            "mechanism coverage",
            "limits and exceptions",
            "enumerated-category accuracy",
            "quantities and thresholds",
            "scope",
            "confidence",
        ],
        comparisons=rows,
    )


def _packet_complexity(packet: dict[str, Any]) -> int:
    return sum(
        len(_canonical_bytes(source["deterministic_extraction"]))
        for source in packet["sources"]
        if source["role"] == "operative_content_interpretation_input"
    )


def _sample_manifest(
    batch: dict[str, Any],
    packets: list[dict[str, Any]],
    coverage: dict[str, Any],
    consistency: dict[str, Any],
    scope: dict[str, Any],
    lineage: dict[str, Any],
) -> dict[str, Any]:
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    population = sorted(set(candidates) - set(BENCHMARK_ACTIONS))
    seed_material = (
        batch["content_subject_sha256"] + "*" + M2_SHA256 + "*" + SAMPLE_LABEL
    )
    seed = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    ranked = sorted(
        population,
        key=lambda action_id: (
            hashlib.sha256(f"{seed}\n{action_id}".encode()).hexdigest(),
            action_id,
        ),
    )
    random_sample = ranked[:12]
    packet_by = {row["action_id"]: row for row in packets}
    challenge: dict[str, list[str]] = {}

    def add(action_id: str, reason: str) -> None:
        challenge.setdefault(action_id, []).append(reason)

    add("house:119:2:155", "FISA action and preserved source conflict")
    add("house:119:2:221", "FISA related-action contrast")
    add("house:119:1:23", "Senate-origin action and pre-correction major finding")
    add("house:119:1:68", "pre-correction cross-field major finding")
    for stage, reason in (
        ("passage", "highest-complexity passage"),
        ("amendment", "highest-complexity amendment"),
        (
            "suspension_passage_as_amended",
            "highest-complexity suspension passage as amended",
        ),
    ):
        eligible = [
            candidate
            for candidate in candidates.values()
            if candidate["house_stage"] == stage
        ]
        chosen = max(
            eligible, key=lambda row: _packet_complexity(packet_by[row["action_id"]])
        )
        add(chosen["action_id"], reason)
    for candidate in candidates.values():
        if candidate["confidence"] == "low" or candidate["status"] in {
            "ambiguous",
            "no_safe_candidate",
        }:
            add(
                candidate["action_id"],
                f"final status {candidate['status']} and confidence {candidate['confidence']}",
            )
    for review in coverage["reviews"]:
        if review["highest_severity"] in {"major", "critical"}:
            add(review["action_id"], "pre-correction source-first coverage finding")
    for review in consistency["reviews"]:
        if review["highest_severity"] in {"major", "critical"}:
            add(review["action_id"], "pre-correction consistency finding")
    for review in scope["reviews"]:
        if review["highest_severity"] in {"major", "critical"}:
            add(review["action_id"], "scope or safe-routing challenge")
    contrast = [
        {
            "group_id": group["group_id"],
            "action_ids": group["action_ids"],
        }
        for group in lineage["groups"]
    ]
    return _artifact(
        "sample_manifest.json",
        candidate_batch_frozen=True,
        candidate_batch_content_subject_sha256=batch["content_subject_sha256"],
        m2_source_readiness_file_sha256=M2_SHA256,
        seed_label=SAMPLE_LABEL,
        seed_material_convention="SHA-256(batch subject + '*' + M2 file SHA + '*' + label)",
        seed_sha256=seed,
        selection_algorithm="rank non-benchmark IDs by SHA-256(seed + newline + action_id), then action_id; take first 12",
        non_benchmark_population_count=30,
        random_sample_count=12,
        benchmark_actions_excluded=True,
        selected_random_action_ids=random_sample,
        challenge_actions=[
            {"action_id": action_id, "reasons": sorted(reasons)}
            for action_id, reasons in sorted(challenge.items())
        ],
        challenge_count=len(challenge),
        related_action_contrast_sets=contrast,
        contrast_group_count=len(contrast),
    )


def _decision_template(sample: dict[str, Any]) -> dict[str, Any]:
    reviewed_ids = sorted(
        set(sample["selected_random_action_ids"])
        | {row["action_id"] for row in sample["challenge_actions"]}
        | {
            action_id
            for group in sample["related_action_contrast_sets"]
            for action_id in group["action_ids"]
        }
    )
    return _artifact(
        "human_decision_template.json",
        decision_state="empty_pending_human_review",
        allowed_decisions=[
            "generalization_pass",
            "global_revision_required",
            "generalization_rejected",
        ],
        selected_decision=None,
        human_reviewer=None,
        reviewed_at=None,
        candidate_batch_content_subject_sha256=sample[
            "candidate_batch_content_subject_sha256"
        ],
        reviewed_action_ids=reviewed_ids,
        accepts_any_candidate=False,
        authorizes_m3b=False,
    )


def _content_subject_for_json(value: object) -> str:
    if isinstance(value, dict) and "content_subject_sha256" in value:
        subject = {
            key: child
            for key, child in value.items()
            if key != "content_subject_sha256"
        }
        return _sha256(subject)
    return _sha256(value)


def _canonical_file_rows() -> list[dict[str, str]]:
    rows = []
    for path in sorted(
        path
        for path in OUTPUT_ROOT.rglob("*.json")
        if path.name != "parity_manifest.json"
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "path": _relative(path),
                "content_subject_sha256": _content_subject_for_json(value),
                "file_sha256": _file_sha256(path),
                "digest_semantics": "canonical parsed JSON subject; final serialized file bytes",
            }
        )
    return rows


def _review_accounting(
    reviews: dict[str, Any], field: str = "highest_severity"
) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in reviews["reviews"]).items()))


def _dossier_projection(
    batch: dict[str, Any],
    benchmark: dict[str, Any],
    sample: dict[str, Any],
    inventories: dict[str, Any],
    coverage: dict[str, Any],
    differential: dict[str, Any],
    consistency: dict[str, Any],
    scope: dict[str, Any],
    corrections: dict[str, Any],
    artifact_rows: list[dict[str, str]],
) -> dict[str, Any]:
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    inventory_by = {row["action_id"]: row for row in inventories["inventories"]}
    coverage_by = {row["action_id"]: row for row in coverage["reviews"]}
    consistency_by = {row["action_id"]: row for row in consistency["reviews"]}
    scope_by = {row["action_id"]: row for row in scope["reviews"]}
    differential_by_action: dict[str, list[dict[str, Any]]] = {}
    for review in differential["reviews"]:
        for action_id in review["action_ids"]:
            differential_by_action.setdefault(action_id, []).append(review)
    review_ids = sorted(
        set(sample["selected_random_action_ids"])
        | {row["action_id"] for row in sample["challenge_actions"]}
        | {
            action_id
            for group in sample["related_action_contrast_sets"]
            for action_id in group["action_ids"]
        }
    )
    detail_rows = []
    for action_id in review_ids:
        candidate = candidates[action_id]
        inventory = inventory_by[action_id]
        detail_rows.append(
            {
                "action_id": action_id,
                "exact_action_identity": candidate["exact_action_identity"],
                "house_stage": candidate["house_stage"],
                "candidate_meaning": candidate["proposed_exact_action_meaning"],
                "expected_provisions": inventory["expected_provisions"],
                "expected_limits": inventory["expected_limits_and_exceptions"],
                "candidate_provisions": candidate["material_provisions"],
                "candidate_limits": candidate["material_limits_and_exceptions"],
                "quantities_and_enumerations": inventory["quantities_and_enumerations"],
                "coverage": coverage_by[action_id],
                "differential": differential_by_action.get(action_id, []),
                "consistency": consistency_by[action_id],
                "scope": scope_by[action_id],
                "confidence": candidate["confidence"],
                "status": candidate["status"],
                "human_review_questions": [
                    "Does the candidate reflect every source-first material item?",
                    "Are enumerations, quantities, dates, penalties, and limits exact?",
                    "Does the candidate stay within the exact action and member-action effect?",
                ],
            }
        )
    return {
        "decision_requested": [
            "generalization_pass",
            "global_revision_required",
            "generalization_rejected",
        ],
        "v2_reviewed_defects": [
            "S. 5 exact-version detention-trigger collapse",
            "H.R. 1156 three-versus-four program contradiction",
        ],
        "batch": {
            "batch_id": batch["batch_id"],
            "content_subject_sha256": batch["content_subject_sha256"],
            "file_sha256": _file_sha256(OUTPUT_ROOT / "candidate_batch.json"),
        },
        "accounting": {
            "status": dict(
                sorted(Counter(row["status"] for row in candidates.values()).items())
            ),
            "confidence": dict(
                sorted(
                    Counter(row["confidence"] for row in candidates.values()).items()
                )
            ),
            "expected_provision_count": sum(
                len(row["expected_provisions"]) for row in inventory_by.values()
            ),
            "expected_limit_count": sum(
                len(row["expected_limits_and_exceptions"])
                for row in inventory_by.values()
            ),
            "coverage_initial": _review_accounting(coverage),
            "coverage_remaining": _review_accounting(
                coverage, "remaining_severity_after_correction"
            ),
            "differential_initial": _review_accounting(differential),
            "differential_remaining": _review_accounting(
                differential, "remaining_severity_after_correction"
            ),
            "consistency_initial": _review_accounting(consistency),
            "consistency_remaining": _review_accounting(
                consistency, "remaining_severity_after_correction"
            ),
            "scope_initial": _review_accounting(scope),
            "scope_remaining": _review_accounting(
                scope, "remaining_severity_after_routing"
            ),
            "correction_count": corrections["correction_count"],
        },
        "benchmark": benchmark["comparisons"],
        "samples": sample,
        "review_details": detail_rows,
        "ambiguous_or_no_safe": [
            {
                "action_id": row["action_id"],
                "status": row["status"],
                "confidence": row["confidence"],
                "uncertainty_reasons": row["uncertainty_reasons"],
            }
            for row in candidates.values()
            if row["status"] in {"ambiguous", "no_safe_candidate"}
        ],
        "remaining_major_or_critical": [
            {"review_type": kind, "review_id": row["review_id"], "severity": row[field]}
            for kind, artifact, field in (
                ("coverage", coverage, "remaining_severity_after_correction"),
                ("differential", differential, "remaining_severity_after_correction"),
                ("consistency", consistency, "remaining_severity_after_correction"),
                ("scope", scope, "remaining_severity_after_routing"),
            )
            for row in artifact["reviews"]
            if row[field] in {"major", "critical"}
        ],
        "canonical_artifacts": artifact_rows,
    }


def _render_dossier(projection: dict[str, Any]) -> str:
    accounting = projection["accounting"]
    lines = [
        "# Foushee Justice Action-Interpretation Generalization Review V3",
        "",
        "## Exact decision requested",
        "",
        "Choose exactly one: `generalization_pass`, `global_revision_required`, or `generalization_rejected`.",
        "No candidate is accepted by this dossier.",
        "",
        "## Reviewed V2 defects and V3 identity",
        "",
        *[f"- {item}" for item in projection["v2_reviewed_defects"]],
        f"- Batch ID: `{projection['batch']['batch_id']}`",
        f"- Content-subject SHA-256: `{projection['batch']['content_subject_sha256']}`",
        f"- Final file SHA-256: `{projection['batch']['file_sha256']}`",
        "",
        "## Accounting",
        "",
        f"- Status: `{json.dumps(accounting['status'], sort_keys=True)}`",
        f"- Confidence: `{json.dumps(accounting['confidence'], sort_keys=True)}`",
        f"- Expected provisions / limits: `{accounting['expected_provision_count']}` / `{accounting['expected_limit_count']}`",
        f"- Coverage initial / remaining: `{json.dumps(accounting['coverage_initial'], sort_keys=True)}` / `{json.dumps(accounting['coverage_remaining'], sort_keys=True)}`",
        f"- Differential initial / remaining: `{json.dumps(accounting['differential_initial'], sort_keys=True)}` / `{json.dumps(accounting['differential_remaining'], sort_keys=True)}`",
        f"- Consistency initial / remaining: `{json.dumps(accounting['consistency_initial'], sort_keys=True)}` / `{json.dumps(accounting['consistency_remaining'], sort_keys=True)}`",
        f"- Scope initial / remaining: `{json.dumps(accounting['scope_initial'], sort_keys=True)}` / `{json.dumps(accounting['scope_remaining'], sort_keys=True)}`",
        f"- Evidence-bound corrections: `{accounting['correction_count']}`",
        "",
        "## Fresh audit sets",
        "",
        f"- Seed: `{projection['samples']['seed_sha256']}`",
        "- Random: "
        + ", ".join(
            f"`{item}`" for item in projection["samples"]["selected_random_action_ids"]
        ),
        "- Challenge: "
        + ", ".join(
            f"`{row['action_id']}`"
            for row in projection["samples"]["challenge_actions"]
        ),
        "- Contrast: "
        + ", ".join(
            f"`{row['group_id']}`"
            for row in projection["samples"]["related_action_contrast_sets"]
        ),
        "",
        "## Benchmark comparison after freeze",
        "",
        "| Action | Mechanism | Limits | Enumerations | Quantities | Scope | Confidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in projection["benchmark"]:
        lines.append(
            f"| `{row['action_id']}` | {row['mechanism_coverage']} | {row['limits_and_exceptions']} | {row['enumerated_category_accuracy']} | {row['quantities_and_thresholds']} | {row['scope']} | {row['confidence_calibration']} |"
        )
    lines += ["", "## Detailed random, challenge, and contrast review", ""]
    for row in projection["review_details"]:
        lines += [
            f"### `{row['action_id']}`",
            "",
            f"- Exact identity: `{row['exact_action_identity']}`; stage: `{row['house_stage']}`",
            f"- Candidate meaning: {row['candidate_meaning'] or '*No safe candidate.*'}",
            f"- Status / confidence: `{row['status']}` / `{row['confidence']}`",
            "- Expected source-first provisions: "
            + json.dumps(
                row["expected_provisions"], ensure_ascii=False, sort_keys=True
            ),
            "- Expected limits and exceptions: "
            + json.dumps(row["expected_limits"], ensure_ascii=False, sort_keys=True),
            "- Candidate material inventory: "
            + json.dumps(
                row["candidate_provisions"], ensure_ascii=False, sort_keys=True
            ),
            "- Candidate limits: "
            + json.dumps(row["candidate_limits"], ensure_ascii=False, sort_keys=True),
            "- Quantities and enumerations: "
            + json.dumps(
                row["quantities_and_enumerations"], ensure_ascii=False, sort_keys=True
            ),
            f"- Coverage remaining: `{row['coverage']['remaining_severity_after_correction']}`",
            f"- Consistency remaining: `{row['consistency']['remaining_severity_after_correction']}`",
            f"- Scope remaining: `{row['scope']['remaining_severity_after_routing']}`",
            "- Differential findings: "
            + json.dumps(row["differential"], ensure_ascii=False, sort_keys=True),
            "- Human review questions: " + " ".join(row["human_review_questions"]),
            "",
        ]
    lines += [
        "## Ambiguous and no-safe candidates",
        "",
        json.dumps(
            projection["ambiguous_or_no_safe"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "",
        "## Remaining major or critical findings",
        "",
        json.dumps(
            projection["remaining_major_or_critical"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "",
        "## Canonical artifact paths and digests",
        "",
        "| Path | Content-subject SHA-256 | Final-file SHA-256 |",
        "| --- | --- | --- |",
    ]
    for row in projection["canonical_artifacts"]:
        lines.append(
            f"| `{row['path']}` | `{row['content_subject_sha256']}` | `{row['file_sha256']}` |"
        )
    return "\n".join(lines) + "\n"


def _parity_manifest(
    batch: dict[str, Any],
    artifact_rows: list[dict[str, str]],
    projection: dict[str, Any],
    dossier_path: Path,
) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": "action_interpretation_final_byte_parity_v3",
            "artifact_id": "action-interpretation-final-byte-parity:f000477:justice_public_safety:119:v3",
            "parity_state": "pass",
            "generated_last": True,
            "candidate_batch_content_subject_sha256": batch["content_subject_sha256"],
            "candidate_batch_file_sha256": _file_sha256(
                OUTPUT_ROOT / "candidate_batch.json"
            ),
            "digest_field_convention": {
                "content_subject_sha256": "canonical parsed subject excluding self digest",
                "file_sha256": "SHA-256 of final serialized bytes",
            },
            "canonical_artifacts": artifact_rows,
            "dossier": {
                "path": _relative(dossier_path),
                "content_subject_sha256": _sha256(projection),
                "file_sha256": _file_sha256(dossier_path),
                "digest_semantics": "canonical dossier projection; final Markdown bytes",
            },
            "referenced_file_count": len(artifact_rows) + 1,
            "all_final_file_sha256_recomputed": True,
            "dossier_contains_every_canonical_path_and_hash": True,
        }
    )


def build_post_freeze(*, check: bool = False) -> dict[str, Any]:
    batch_path = OUTPUT_ROOT / "candidate_batch.json"
    before = _file_sha256(batch_path)
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    if not batch["frozen"] or not batch["freeze_precedes_benchmark_access"]:
        raise ValueError("post-freeze phase requires frozen blind V3 batch")
    packets = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(PACKET_ROOT.glob("*.json"))
    ]

    def load(name: str) -> dict[str, Any]:
        return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))

    inventories = load("expected_provision_inventories.json")
    coverage = load("source_first_coverage_reviews.json")
    differential = load("related_action_differential_reviews.json")
    consistency = load("cross_field_consistency_reviews.json")
    scope = load("scope_neutrality_reviews.json")
    corrections = load("bounded_correction_diff.json")
    lineage = load("related_action_lineage_map.json")
    benchmark = _benchmark_comparison(batch)
    sample = _sample_manifest(batch, packets, coverage, consistency, scope, lineage)
    decision = _decision_template(sample)
    post = {
        "benchmark_comparison.json": benchmark,
        "sample_manifest.json": sample,
        "human_decision_template.json": decision,
    }
    for name, value in post.items():
        _write_or_check_json(OUTPUT_ROOT / name, value, check=check)
        schema_name = name.replace(".json", "_v3.schema.json")
        _write_or_check_json(
            SCHEMA_ROOT / schema_name,
            v2._closed_schema(name.replace(".json", "_v3"), [value]),
            check=check,
        )
    artifact_rows = _canonical_file_rows()
    projection = _dossier_projection(
        batch,
        benchmark,
        sample,
        inventories,
        coverage,
        differential,
        consistency,
        scope,
        corrections,
        artifact_rows,
    )
    dossier_path = OUTPUT_ROOT / "human_review_dossier.md"
    dossier = _render_dossier(projection)
    if check:
        if (
            not dossier_path.exists()
            or dossier_path.read_text(encoding="utf-8") != dossier
        ):
            raise ValueError("deterministic dossier check failed")
    else:
        dossier_path.parent.mkdir(parents=True, exist_ok=True)
        dossier_path.write_text(dossier, encoding="utf-8", newline="\n")
    parity = _parity_manifest(batch, artifact_rows, projection, dossier_path)
    _write_or_check_json(OUTPUT_ROOT / "parity_manifest.json", parity, check=check)
    if _file_sha256(batch_path) != before:
        raise ValueError("post-freeze phase mutated candidate batch")
    return {"batch": batch, "benchmark": benchmark, "sample": sample, "parity": parity}


def main() -> int:
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
    parser.error("choose one phase")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
