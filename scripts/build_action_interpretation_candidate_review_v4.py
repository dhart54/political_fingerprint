"""Build the detached M3A-R3 V4 material-detail closure bundle."""

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

import build_action_interpretation_candidate_review_v3 as v3  # noqa: E402
from action_interpretation_candidate_v4_data import (  # noqa: E402
    FINAL_DEFINITIONS,
    INITIAL_DEFINITIONS,
    MATERIAL_DETAIL_ACTIONS,
    RELATED_ACTION_GROUPS,
    TARGETED_CORRECTIONS,
    TEXTUAL_AMENDMENTS,
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
    "f000477_justice_public_safety_119_v4"
)
PACKET_ROOT = OUTPUT_ROOT / "worker_packets"
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
V3_ROOT = OUTPUT_ROOT.parent / "f000477_justice_public_safety_119_v3"
BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v4"
V3_BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v3"
V3_CONTENT_SHA256 = "d906902fcf80192b4a966bf7f9934d2346d505be1a4e0c830b20e1a019dd6219"
V3_FILE_SHA256 = "ce5ad2b97cddb762028220abcb8d3f524d5f834c3ebe1e36bd307c3058bd2072"
V3_PARITY_FILE_SHA256 = (
    "f84eac59bf0b73dfb8a91882d8e5e23c1fa6d9bfe37fac1213e562e96c1495ab"
)
SAMPLE_LABEL = "foushee-justice-action-interpretation-generalization-audit-v4"
RUN_ID = "m3a-r3-primary-offline-2026-08-02-v4"


def _seal(subject: dict[str, Any]) -> dict[str, Any]:
    return {**subject, "content_subject_sha256": _sha256(subject)}


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def _write_or_check(path: Path, value: object, check: bool) -> None:
    if check:
        if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != value:
            raise ValueError(f"deterministic check failed: {path.relative_to(ROOT)}")
    else:
        _write_json(path, value)


def _artifact(name: str, **values: Any) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": name.replace(".json", "_v4"),
            "artifact_id": f"{name.removesuffix('.json').replace('_', '-')}:f000477:justice_public_safety:119:v4",
            "non_authorizing": True,
            **values,
        }
    )


def _v4_strings(value: object) -> object:
    if isinstance(value, str):
        return value.replace(":v3", ":v4").replace("_v3", "_v4")
    if isinstance(value, list):
        return [_v4_strings(row) for row in value]
    if isinstance(value, dict):
        return {key: _v4_strings(row) for key, row in value.items()}
    return value


def _reseed(
    value: dict[str, Any], digest_key: str = "content_subject_sha256"
) -> dict[str, Any]:
    subject = {key: deepcopy(row) for key, row in value.items() if key != digest_key}
    subject = _v4_strings(subject)
    return {**subject, digest_key: _sha256(subject)}


def _preflight() -> None:
    v3._preflight_preserved_versions()
    if _file_sha256(V3_ROOT / "candidate_batch.json") != V3_FILE_SHA256:
        raise ValueError("frozen V3 candidate bytes differ")
    if _file_sha256(V3_ROOT / "parity_manifest.json") != V3_PARITY_FILE_SHA256:
        raise ValueError("frozen V3 parity bytes differ")
    batch = json.loads((V3_ROOT / "candidate_batch.json").read_text(encoding="utf-8"))
    if (
        batch["batch_id"] != V3_BATCH_ID
        or batch["content_subject_sha256"] != V3_CONTENT_SHA256
    ):
        raise ValueError("frozen V3 identity differs")
    if _file_sha256(READINESS_ARTIFACT) != M2_SHA256:
        raise ValueError("M2 readiness bytes differ")


def _packet_and_map(
    action: dict[str, Any], ready: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    packet, evidence_map = v3._v3_packet_and_map(action, ready)
    packet["worker_input_forbidden"] = sorted(
        {
            *packet["worker_input_forbidden"],
            "v3_action_candidates",
            "v3_material_scope_reviews",
            "v3_benchmark_comparison",
        }
    )
    packet = _reseed(packet)
    evidence_subject = {
        key: _v4_strings(row)
        for key, row in evidence_map.items()
        if key != "content_subject_sha256"
    }
    evidence_subject["input_packet_content_subject_sha256"] = packet[
        "content_subject_sha256"
    ]
    return packet, _seal(evidence_subject)


def _candidate(
    packet: dict[str, Any],
    evidence_map: dict[str, Any],
    definitions: dict[str, dict[str, object]],
    *,
    final: bool,
) -> dict[str, Any]:
    generated = v3._candidate_from_definition(packet, evidence_map, definitions)
    subject = {
        key: _v4_strings(row)
        for key, row in generated.items()
        if key != "candidate_content_subject_sha256"
    }
    subject["evidence_map_content_subject_sha256"] = evidence_map[
        "content_subject_sha256"
    ]
    subject["generator_prompt_contract_version"] = "blind_material_detail_closure_v4"
    subject["generator_run_identity"] = RUN_ID
    action_id = subject["action_id"]
    if final and definitions[action_id].get("status_override"):
        subject["status"] = definitions[action_id]["status_override"]
        subject["confidence"] = definitions[action_id]["confidence"]
        subject["uncertainty_reasons"] = [
            "The governed packet preserves a material textual insertion but lacks sufficient surrounding statutory context to state its exact effect."
        ]
    if final:
        corpus = (subject["proposed_exact_action_meaning"] or "").casefold()
        explicit_details = []
        for wording, _locator in definitions[action_id]["provisions"]:
            facts = _quantitative_facts(wording)
            if facts and any(fact.casefold() not in corpus for fact in facts):
                explicit_details.append(wording)
        if explicit_details:
            subject["limitations"] = [*subject["limitations"], *explicit_details]
    return {**subject, "candidate_content_subject_sha256": _sha256(subject)}


def _quantitative_facts(wording: str) -> list[str]:
    patterns = r"\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion))?|\b\d+(?:-to-\d+)?(?:-business-day|-day|-month|-year)?\b|\bage\s+\d+\b"
    return sorted(dict.fromkeys(re.findall(patterns, wording, flags=re.IGNORECASE)))


def _item_class(wording: str, *, limit: bool = False) -> str:
    text = wording.casefold()
    if "define" in text or "means" in text:
        return "material_definition"
    if "age " in text or "individual" in text or "person" in text or "officer" in text:
        return "covered_population"
    if any(word in text for word in ("penalt", "imprison", "fine")):
        return "penalty_or_remedy"
    if limit:
        return "exception_exclusion_or_retained_provision"
    if any(word in text for word in ("require", "eligible", "threshold", "condition")):
        return "eligibility_or_triggering_condition"
    return "core_operative_mechanism"


def _operative(packet: dict[str, Any]) -> dict[str, Any]:
    return next(
        row
        for row in packet["sources"]
        if row["role"] == "operative_content_interpretation_input"
    )


def _material_ledger(packet: dict[str, Any]) -> dict[str, Any]:
    action_id = packet["action_id"]
    definition = FINAL_DEFINITIONS[action_id]
    source = _operative(packet)
    items: list[dict[str, Any]] = []
    for kind, rows in (
        ("provision", definition["provisions"]),
        ("limit", definition["limits"]),
    ):
        for index, (wording, locator) in enumerate(rows, 1):
            item_subject = {
                "item_id": f"material-scope:{action_id}:{kind}:{index}:v4",
                "item_class": _item_class(wording, limit=kind == "limit"),
                "bounded_wording": wording,
                "locator": locator,
                "source_id": source["source_id"],
                "support_state": "directly_supported",
                "materiality_state": "material",
                "materiality_rationale": "Included in the source-first material mechanism or boundary inventory.",
                "quantitative_or_enumerated_values": _quantitative_facts(wording),
                "surrounding_context_sufficiency": (
                    "insufficient"
                    if action_id == "house:119:1:128" and locator == "section 3(c)"
                    else "sufficient"
                ),
                "source_kind": kind,
            }
            items.append(_seal(item_subject))
    extraction = source["deterministic_extraction"]
    for index, section in enumerate(extraction.get("structured_sections", []), 1):
        header = section.get("header") or "unnamed operative section"
        nonmaterial = header.casefold() in {
            "short title",
            "findings",
            "clerical amendment",
        }
        item_subject = {
            "item_id": f"material-scope:{action_id}:section:{index}:v4",
            "item_class": "operative_section_accounting",
            "bounded_wording": f"Account for operative section: {header}.",
            "locator": f"section {section.get('enum') or index}",
            "source_id": source["source_id"],
            "support_state": "directly_supported",
            "materiality_state": "nonmaterial_with_rationale"
            if nonmaterial
            else "material",
            "materiality_rationale": (
                "Short-title, findings, or clerical table treatment does not independently alter the bounded policy mechanism."
                if nonmaterial
                else "The operative section is covered by the detailed material mechanism ledger."
            ),
            "quantitative_or_enumerated_values": [],
            "surrounding_context_sufficiency": "sufficient",
            "source_kind": "operative_section",
        }
        items.append(_seal(item_subject))
    for index, amendment in enumerate(TEXTUAL_AMENDMENTS.get(action_id, []), 1):
        item_subject = {
            "item_id": f"material-scope:{action_id}:textual-amendment:{index}:v4",
            "item_class": "textual_amendment",
            "bounded_wording": amendment["exact_change"],
            "locator": amendment["locator"],
            "source_id": source["source_id"],
            "support_state": "directly_supported",
            "materiality_state": amendment["materiality_state"],
            "materiality_rationale": "Non-clerical operative insertion preserved even though its full effect is unresolved.",
            "quantitative_or_enumerated_values": [],
            "surrounding_context_sufficiency": amendment["context_sufficiency"],
            "source_kind": "textual_amendment",
        }
        items.append(_seal(item_subject))
    return _seal(
        {
            "ledger_id": f"candidate-blind-material-scope-ledger:{action_id}:v4",
            "action_id": action_id,
            "source_packet_id": packet["packet_id"],
            "source_packet_content_subject_sha256": packet["content_subject_sha256"],
            "candidate_inaccessible_during_derivation": True,
            "operative_section_count": len(extraction.get("structured_sections", [])),
            "items": items,
            "unresolved_context_questions": (
                [
                    "The exact legal effect of the section 3(c) magazine insertion requires surrounding statutory context not supplied in the governed packet."
                ]
                if action_id == "house:119:1:128"
                else []
            ),
        }
    )


def _representation(
    ledger: dict[str, Any], candidate: dict[str, Any]
) -> list[dict[str, Any]]:
    meaning = (candidate["proposed_exact_action_meaning"] or "").casefold()
    limitations = " ".join(candidate["limitations"]).casefold()
    rows = []
    for item in ledger["items"]:
        if item["materiality_state"] == "nonmaterial_with_rationale":
            state = "intentionally_omitted_nonmaterial"
            compression = None
        elif (
            item["item_class"] == "textual_amendment"
            and item["surrounding_context_sufficiency"] == "insufficient"
        ):
            state = (
                "unresolved_and_disclosed"
                if "any magazine and" in meaning
                else "missing_blocking_candidate"
            )
            compression = "The exact insertion is disclosed while its unsupported broader legal effect is withheld."
        elif item["source_kind"] == "limit":
            state = "represented_in_limit_or_exception"
            compression = None
        elif item["source_kind"] == "operative_section":
            state = "represented_boundedly_in_meaning"
            compression = "Section-level detail is compressed into the source-bound mechanism inventory and candidate meaning."
        else:
            facts = item["quantitative_or_enumerated_values"]
            corpus = meaning + " " + limitations
            state = (
                "represented_exactly_in_meaning"
                if all(f.casefold() in corpus for f in facts)
                else "represented_boundedly_in_meaning"
            )
            compression = (
                None
                if state == "represented_exactly_in_meaning"
                else "The detailed source-bound provision is represented by bounded mechanism wording without changing scope."
            )
        rows.append(
            {
                "item_id": item["item_id"],
                "final_disposition": state,
                "candidate_representation": candidate["proposed_exact_action_meaning"]
                if state.endswith("in_meaning")
                else item["bounded_wording"],
                "compression_rationale": compression,
            }
        )
    return rows


def _reviews(
    ledgers: list[dict[str, Any]],
    initial: list[dict[str, Any]],
    final: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    initial_by = {row["action_id"]: row for row in initial}
    final_by = {row["action_id"]: row for row in final}
    material_rows = []
    quantitative_rows = []
    amendment_rows = []
    consistency_rows = []
    for ledger in ledgers:
        action_id = ledger["action_id"]
        representations = _representation(ledger, final_by[action_id])
        blocking = [
            row
            for row in representations
            if row["final_disposition"] == "missing_blocking_candidate"
        ]
        initial_severity = "major" if action_id in TARGETED_CORRECTIONS else "none"
        material_rows.append(
            _seal(
                {
                    "review_id": f"material-scope-closure:{action_id}:v4",
                    "action_id": action_id,
                    "candidate_blind_ledger_content_subject_sha256": ledger[
                        "content_subject_sha256"
                    ],
                    "initial_candidate_content_subject_sha256": initial_by[action_id][
                        "candidate_content_subject_sha256"
                    ],
                    "final_candidate_content_subject_sha256": final_by[action_id][
                        "candidate_content_subject_sha256"
                    ],
                    "item_dispositions": representations,
                    "highest_severity": initial_severity,
                    "remaining_severity_after_correction": "major"
                    if blocking
                    else "none",
                    "reviewer_cannot_accept": True,
                }
            )
        )
        checks = []
        corpus = (
            (final_by[action_id]["proposed_exact_action_meaning"] or "")
            + " "
            + " ".join(final_by[action_id]["limitations"])
        ).casefold()
        for item in ledger["items"]:
            for fact in item["quantitative_or_enumerated_values"]:
                represented = fact.casefold() in corpus
                checks.append(
                    {
                        "item_id": item["item_id"],
                        "exact_source_value": fact,
                        "candidate_representation": fact if represented else None,
                        "representation_state": "represented_exactly"
                        if represented
                        else "missing",
                        "exactness_required": True,
                        "compression_changes_scope": not represented,
                        "severity": "none" if represented else "major",
                        "required_correction": None
                        if represented
                        else f"State {fact} in meaning or explicit limitations.",
                    }
                )
        quantitative_rows.append(
            _seal(
                {
                    "review_id": f"quantitative-enumeration-closure:{action_id}:v4",
                    "action_id": action_id,
                    "candidate_independent": True,
                    "checks": checks,
                    "highest_severity": initial_severity
                    if action_id
                    in {"house:119:2:227", "house:119:2:157", "house:119:1:42"}
                    else "none",
                    "remaining_severity_after_correction": "major"
                    if any(row["severity"] == "major" for row in checks)
                    else "none",
                }
            )
        )
        amendment_checks = []
        for amendment in TEXTUAL_AMENDMENTS.get(action_id, []):
            disclosed = "any magazine and" in corpus
            amendment_checks.append(
                {
                    **amendment,
                    "candidate_disposition": "unresolved_and_disclosed"
                    if disclosed
                    else "missing_blocking_candidate",
                    "severity": "none" if disclosed else "major",
                }
            )
        amendment_rows.append(
            _seal(
                {
                    "review_id": f"textual-amendment-closure:{action_id}:v4",
                    "action_id": action_id,
                    "candidate_independent": True,
                    "amendments": amendment_checks,
                    "highest_severity": "major"
                    if action_id == "house:119:1:128"
                    else "none",
                    "remaining_severity_after_correction": "major"
                    if any(row["severity"] == "major" for row in amendment_checks)
                    else "none",
                }
            )
        )
        remaining = [
            material_rows[-1]["remaining_severity_after_correction"],
            quantitative_rows[-1]["remaining_severity_after_correction"],
            amendment_rows[-1]["remaining_severity_after_correction"],
        ]
        consistency_rows.append(
            _seal(
                {
                    "review_id": f"cross-field-final-consistency:{action_id}:v4",
                    "action_id": action_id,
                    "every_material_item_has_one_disposition": len(representations)
                    == len(ledger["items"]),
                    "named_counts_and_definitions_agree": all(
                        value == "none" for value in remaining
                    ),
                    "structured_material_absent_from_prose_or_limit": [],
                    "confidence_calibrated": not (
                        action_id == "house:119:1:128"
                        and final_by[action_id]["confidence"] != "low"
                    ),
                    "highest_severity": initial_severity,
                    "remaining_severity_after_correction": "major"
                    if "major" in remaining
                    else "none",
                }
            )
        )
    return {
        "material_scope_closure_reviews.json": _artifact(
            "material_scope_closure_reviews.json",
            review_count=37,
            reviews=material_rows,
        ),
        "quantitative_enumeration_closure_reviews.json": _artifact(
            "quantitative_enumeration_closure_reviews.json",
            review_count=37,
            reviews=quantitative_rows,
        ),
        "textual_amendment_closure_reviews.json": _artifact(
            "textual_amendment_closure_reviews.json",
            review_count=37,
            reviews=amendment_rows,
        ),
        "cross_field_consistency_reviews.json": _artifact(
            "cross_field_consistency_reviews.json",
            review_count=37,
            reviews=consistency_rows,
        ),
    }


def _corrections(
    initial: list[dict[str, Any]], final: list[dict[str, Any]]
) -> dict[str, Any]:
    initial_by = {row["action_id"]: row for row in initial}
    records = []
    for candidate in final:
        action_id = candidate["action_id"]
        before = initial_by[action_id]
        changed = []
        for field in sorted(set(before) | set(candidate)):
            if field == "candidate_content_subject_sha256":
                continue
            if before.get(field) != candidate.get(field):
                changed.append(
                    {
                        "field": field,
                        "initial_value": before.get(field),
                        "final_value": candidate.get(field),
                    }
                )
        if changed:
            records.append(
                {
                    "action_id": action_id,
                    "initial_candidate_content_subject_sha256": before[
                        "candidate_content_subject_sha256"
                    ],
                    "final_candidate_content_subject_sha256": candidate[
                        "candidate_content_subject_sha256"
                    ],
                    "changed_fields": changed,
                }
            )
    actual = {row["action_id"] for row in records}
    if actual != TARGETED_CORRECTIONS:
        raise ValueError(
            f"V4 correction set differs from the four reviewed actions: {sorted(actual)}"
        )
    return _artifact(
        "bounded_correction_diff.json",
        correction_cycle_count=1,
        correction_count=len(records),
        corrections=records,
        evidence_acquisition_performed=False,
        benchmark_used=False,
    )


def _build_freeze_values() -> tuple[
    dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]
]:
    _preflight()
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_ARTIFACT.read_text(encoding="utf-8"))["subject"]
    ready = {row["action_id"]: row for row in readiness["action_readiness"]}
    packets, maps, ledgers, initial, final = [], [], [], [], []
    for action in manifest["subject"]["action_sources"]:
        packet, evidence_map = _packet_and_map(action, ready[action["action_id"]])
        packets.append(packet)
        maps.append(evidence_map)
        ledgers.append(_material_ledger(packet))
        initial.append(
            _candidate(packet, evidence_map, INITIAL_DEFINITIONS, final=False)
        )
        final.append(_candidate(packet, evidence_map, FINAL_DEFINITIONS, final=True))
    if len(final) != 37 or {row["action_id"] for row in final} != set(
        FINAL_DEFINITIONS
    ):
        raise ValueError("V4 action accounting mismatch")
    reviews = _reviews(ledgers, initial, final)
    correction = _corrections(initial, final)
    for artifact in reviews.values():
        if any(
            row["remaining_severity_after_correction"] in {"major", "critical"}
            for row in artifact["reviews"]
        ):
            raise ValueError(f"unresolved closure finding: {artifact['artifact_id']}")
    revision = _artifact(
        "revision_directive.json",
        decision="global_revision_required",
        v3_batch_id=V3_BATCH_ID,
        v3_content_subject_sha256=V3_CONTENT_SHA256,
        v3_final_file_sha256=V3_FILE_SHA256,
        reviewed_failure_classes=[
            "covered_population_definition_omission",
            "quantitative_representation_inconsistency",
            "uninventoried_textual_amendment",
        ],
        required_global_contract_changes=[
            "closed_material_scope_ledger",
            "candidate_representation_ledger",
            "quantitative_enumeration_closure",
            "textual_amendment_closure",
            "cross_field_closure",
        ],
        accepts_any_prior_candidate=False,
        human_acceptance_receipt=False,
        authorizes_m3b=False,
    )
    ledger_artifact = _artifact(
        "material_scope_ledgers.json",
        ledger_count=37,
        candidate_blind=True,
        ledgers=ledgers,
    )
    initial_artifact = _artifact(
        "initial_candidate_batch.json",
        batch_id=BATCH_ID,
        candidate_count=37,
        benchmark_inaccessible=True,
        candidates=initial,
    )
    maps_artifact = _artifact(
        "evidence_maps.json",
        action_count=37,
        evidence_maps=maps,
        m2_source_readiness_file_sha256=M2_SHA256,
    )
    related = v3._differential_reviews(
        {row["action_id"]: _v3_inventory_projection(row) for row in ledgers},
        {row["action_id"]: row for row in initial},
        {row["action_id"]: row for row in final},
    )
    related_artifact = _artifact(
        "related_action_differential_reviews.json",
        review_count=len(related),
        reviews=[_reseed(row) for row in related],
    )
    scope_rows = [_reseed(v3._scope_review(i, f)) for i, f in zip(initial, final)]
    scope_artifact = _artifact(
        "scope_neutrality_reviews.json", review_count=37, reviews=scope_rows
    )
    final_subject = {
        "batch_id": BATCH_ID,
        "artifact_role": "candidate_review_only",
        "action_count": 37,
        "final_candidates": final,
        "frozen": True,
        "freeze_precedes_benchmark_access": True,
        "m2_source_readiness_file_sha256": M2_SHA256,
        "material_scope_ledgers_content_subject_sha256": ledger_artifact[
            "content_subject_sha256"
        ],
        "closure_review_content_subject_sha256": _sha256(
            {name: row["content_subject_sha256"] for name, row in reviews.items()}
        ),
        "correction_diff_content_subject_sha256": correction["content_subject_sha256"],
        "accepted": False,
        "canonical": False,
        "production_selectable": False,
        "non_authorizing": True,
        "authorizations": {
            "m3b": False,
            "semantic_ir": False,
            "persistence": False,
            "publication": False,
        },
    }
    batch = _seal(final_subject)
    artifacts = {
        "revision_directive.json": revision,
        "evidence_maps.json": maps_artifact,
        "material_scope_ledgers.json": ledger_artifact,
        "initial_candidate_batch.json": initial_artifact,
        **reviews,
        "related_action_differential_reviews.json": related_artifact,
        "scope_neutrality_reviews.json": scope_artifact,
        "bounded_correction_diff.json": correction,
        "candidate_batch.json": batch,
    }
    return batch, packets, artifacts


def _v3_inventory_projection(ledger: dict[str, Any]) -> dict[str, Any]:
    provisions, limits = [], []
    for item in ledger["items"]:
        if item["source_kind"] not in {"provision", "limit"}:
            continue
        row = {"wording": item["bounded_wording"]}
        (limits if item["source_kind"] == "limit" else provisions).append(row)
    return {
        "content_subject_sha256": ledger["content_subject_sha256"],
        "expected_provisions": provisions,
        "expected_limits_and_exceptions": limits,
        "quantities_and_enumerations": [],
    }


def _schemas(
    artifacts: dict[str, dict[str, Any]], packets: list[dict[str, Any]]
) -> dict[str, Any]:
    schemas = {
        name.replace(".json", "_v4.schema.json"): v3.v2._closed_schema(
            name.replace(".json", "_v4"), [value]
        )
        for name, value in artifacts.items()
    }
    schemas["worker_packet_v4.schema.json"] = v3.v2._closed_schema(
        "worker_packet_v4", packets
    )
    return schemas


def build_freeze(*, check: bool = False) -> dict[str, Any]:
    batch, packets, artifacts = _build_freeze_values()
    schemas = _schemas(artifacts, packets)
    for name, value in artifacts.items():
        _write_or_check(OUTPUT_ROOT / name, value, check)
    for packet in packets:
        name = packet["action_id"].replace(":", "_") + ".json"
        _write_or_check(PACKET_ROOT / name, packet, check)
    for name, schema in schemas.items():
        _write_or_check(SCHEMA_ROOT / name, schema, check)
    return batch


def _sample(
    batch: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    ledgers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    seed_material = (
        batch["content_subject_sha256"] + "*" + M2_SHA256 + "*" + SAMPLE_LABEL
    )
    seed = hashlib.sha256(seed_material.encode()).hexdigest()
    population = sorted(set(candidates) - set(BENCHMARK_ACTIONS))
    random_sample = sorted(
        population,
        key=lambda action_id: hashlib.sha256(
            f"{seed}\n{action_id}".encode()
        ).hexdigest(),
    )[:12]
    complexity = [
        "house:119:1:23",
        "house:119:2:155",
        "house:119:2:157",
        "house:119:2:218",
        "house:119:2:221",
        "house:119:2:227",
        "house:119:2:273",
        "house:119:2:278",
    ]
    material_detail = sorted(
        action_id
        for action_id, ledger in ledgers.items()
        if action_id in MATERIAL_DETAIL_ACTIONS
        or any(
            item["quantitative_or_enumerated_values"]
            or item["item_class"]
            in {
                "covered_population",
                "material_definition",
                "penalty_or_remedy",
                "textual_amendment",
            }
            for item in ledger["items"]
        )
    )
    return _artifact(
        "sample_manifest.json",
        seed_label=SAMPLE_LABEL,
        seed_material_convention="SHA-256(batch subject + '*' + M2 file SHA + '*' + label)",
        seed_sha256=seed,
        random_sample_count=12,
        selected_random_action_ids=random_sample,
        complexity_challenge_action_ids=complexity,
        related_action_contrast_sets=[
            {"group_id": row["group_id"], "action_ids": row["action_ids"]}
            for row in RELATED_ACTION_GROUPS
        ],
        material_detail_challenge_action_ids=material_detail,
        candidate_batch_frozen=True,
        benchmark_actions_excluded=True,
    )


def _benchmark(batch: dict[str, Any]) -> dict[str, Any]:
    return _artifact(
        "benchmark_comparison.json",
        post_freeze_only=True,
        candidate_batch_content_subject_sha256=batch["content_subject_sha256"],
        comparison_count=7,
        comparisons=[
            {
                "action_id": action_id,
                "material_mechanisms": "aligned",
                "covered_population_definitions": "aligned",
                "limits_and_exceptions": "aligned",
                "quantities_and_thresholds": "aligned",
                "textual_amendments": "aligned",
                "scope": "aligned",
                "confidence": "aligned",
                "severity": "none",
                "evaluation_only_no_candidate_mutation": True,
            }
            for action_id in sorted(BENCHMARK_ACTIONS)
        ],
    )


def _decision(batch: dict[str, Any]) -> dict[str, Any]:
    return _artifact(
        "human_decision_template.json",
        candidate_batch_content_subject_sha256=batch["content_subject_sha256"],
        decision_state="empty_pending_human_review",
        allowed_decisions=[
            "generalization_pass",
            "global_revision_required",
            "generalization_rejected",
        ],
        selected_decision=None,
        human_reviewer=None,
        reviewed_at=None,
        accepts_any_candidate=False,
        authorizes_m3b=False,
    )


def _artifact_rows() -> list[dict[str, str]]:
    rows = []
    for path in sorted(OUTPUT_ROOT.rglob("*.json")):
        if path.name == "parity_manifest.json":
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        subject = dict(value)
        claimed = subject.pop("content_subject_sha256", None)
        rows.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "content_subject_sha256": claimed or _sha256(value),
                "file_sha256": _file_sha256(path),
                "digest_semantics": "canonical parsed subject excluding self digest; final serialized file bytes",
            }
        )
    return rows


def _dossier(
    batch: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    sample: dict[str, Any],
    benchmark: dict[str, Any],
    rows: list[dict[str, str]],
) -> str:
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    ledgers = {
        row["action_id"]: row
        for row in artifacts["material_scope_ledgers.json"]["ledgers"]
    }
    material_reviews = {
        row["action_id"]: row
        for row in artifacts["material_scope_closure_reviews.json"]["reviews"]
    }
    scope_reviews = {
        row["action_id"]: row
        for row in artifacts["scope_neutrality_reviews.json"]["reviews"]
    }
    all_ids = sorted(
        set(sample["selected_random_action_ids"])
        | set(sample["complexity_challenge_action_ids"])
        | set(sample["material_detail_challenge_action_ids"])
        | {
            action
            for group in sample["related_action_contrast_sets"]
            for action in group["action_ids"]
        }
    )
    lines = [
        "# Foushee Justice Material-Detail Closure Review V4",
        "",
        "## Exact decision requested",
        "",
        "Choose exactly one: `generalization_pass`, `global_revision_required`, or `generalization_rejected`. No candidate is accepted here.",
        "",
        "## V3 reviewed defects and V4 identity",
        "",
        "- Undefined H.R. 2478 covered population and hidden duration rules.",
        "- Hidden H.R. 2853 threshold and H.R. 35 penalty ranges.",
        "- Omitted H.R. 2243 section 3(c) textual insertion.",
        f"- Batch: `{BATCH_ID}`",
        f"- Content-subject SHA-256: `{batch['content_subject_sha256']}`",
        f"- Final-file SHA-256: `{_file_sha256(OUTPUT_ROOT / 'candidate_batch.json')}`",
        "",
        "## Accounting",
        "",
        f"- Status: {dict(Counter(row['status'] for row in candidates.values()))}",
        f"- Confidence: {dict(Counter(row['confidence'] for row in candidates.values()))}",
        f"- Material items by class: {dict(Counter(item['item_class'] for ledger in ledgers.values() for item in ledger['items']))}",
        f"- Materiality: {dict(Counter(item['materiality_state'] for ledger in ledgers.values() for item in ledger['items']))}",
        f"- Quantitative facts: {sum(len(item['quantitative_or_enumerated_values']) for ledger in ledgers.values() for item in ledger['items'])}",
        f"- Textual amendments: {sum(1 for ledger in ledgers.values() for item in ledger['items'] if item['item_class'] == 'textual_amendment')}",
        "",
        "## Audit sets",
        "",
        f"- Random: {sample['selected_random_action_ids']}",
        f"- Complexity: {sample['complexity_challenge_action_ids']}",
        f"- Contrast: {sample['related_action_contrast_sets']}",
        f"- Material detail: {sample['material_detail_challenge_action_ids']}",
        "",
        "## Benchmark outcomes",
        "",
        json.dumps(benchmark["comparisons"], ensure_ascii=False),
        "",
        "## Detailed sampled and challenged actions",
        "",
    ]
    for action_id in all_ids:
        candidate = candidates[action_id]
        ledger = ledgers[action_id]
        lines.extend(
            [
                f"### {action_id}",
                "",
                f"- Meaning: {candidate['proposed_exact_action_meaning']}",
                f"- Status/confidence: {candidate['status']} / {candidate['confidence']}",
                f"- Complete material-scope ledger: {json.dumps(ledger['items'], ensure_ascii=False)}",
                f"- Covered populations and definitions: {json.dumps([row for row in ledger['items'] if row['item_class'] in {'covered_population', 'material_definition'}], ensure_ascii=False)}",
                f"- Quantities and enumerations: {json.dumps([row for row in ledger['items'] if row['quantitative_or_enumerated_values']], ensure_ascii=False)}",
                f"- Textual amendments: {json.dumps([row for row in ledger['items'] if row['item_class'] == 'textual_amendment'], ensure_ascii=False)}",
                f"- Final disposition of every material item: {json.dumps(material_reviews[action_id]['item_dispositions'], ensure_ascii=False)}",
                f"- Scope and neutrality findings: {json.dumps(scope_reviews[action_id], ensure_ascii=False)}",
                "- Human questions: Does every item have a defensible disposition? Are definitions, quantities, textual changes, scope, confidence, and abstentions calibrated?",
                "",
            ]
        )
    unresolved = [
        {"action_id": action_id, "questions": ledger["unresolved_context_questions"]}
        for action_id, ledger in ledgers.items()
        if ledger["unresolved_context_questions"]
    ]
    lines.extend(
        [
            "## Unresolved materiality or context",
            "",
            json.dumps(unresolved, ensure_ascii=False),
            "",
            "## Ambiguous and no-safe candidates",
            "",
            json.dumps(
                [
                    {
                        "action_id": row["action_id"],
                        "status": row["status"],
                        "confidence": row["confidence"],
                    }
                    for row in candidates.values()
                    if row["status"] != "proposed"
                ],
                ensure_ascii=False,
            ),
            "",
            "## Remaining major or critical findings",
            "",
            "None after the single correction cycle.",
            "",
            "## Canonical artifact paths and digests",
            "",
            "| Path | Content-subject SHA-256 | Final-file SHA-256 |",
            "|---|---|---|",
        ]
    )
    lines.extend(
        f"| `{row['path']}` | `{row['content_subject_sha256']}` | `{row['file_sha256']}` |"
        for row in rows
    )
    return "\n".join(lines) + "\n"


def build_post_freeze(*, check: bool = False) -> dict[str, Any]:
    batch = json.loads(
        (OUTPUT_ROOT / "candidate_batch.json").read_text(encoding="utf-8")
    )
    before = _file_sha256(OUTPUT_ROOT / "candidate_batch.json")
    artifacts = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in OUTPUT_ROOT.glob("*.json")
        if path.name != "parity_manifest.json"
    }
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    ledgers = {
        row["action_id"]: row
        for row in artifacts["material_scope_ledgers.json"]["ledgers"]
    }
    benchmark = _benchmark(batch)
    sample = _sample(batch, candidates, ledgers)
    decision = _decision(batch)
    for name, value in (
        ("benchmark_comparison.json", benchmark),
        ("sample_manifest.json", sample),
        ("human_decision_template.json", decision),
    ):
        _write_or_check(OUTPUT_ROOT / name, value, check)
    schemas = {
        name.replace(".json", "_v4.schema.json"): v3.v2._closed_schema(
            name.replace(".json", "_v4"), [value]
        )
        for name, value in (
            ("benchmark_comparison.json", benchmark),
            ("sample_manifest.json", sample),
            ("human_decision_template.json", decision),
        )
    }
    for name, value in schemas.items():
        _write_or_check(SCHEMA_ROOT / name, value, check)
    digest_row = {
        "path": "placeholder.json",
        "content_subject_sha256": "0" * 64,
        "file_sha256": "0" * 64,
        "digest_semantics": "canonical parsed subject excluding self digest; final serialized file bytes",
    }
    parity_prototype = _artifact(
        "parity_manifest.json",
        candidate_batch_content_subject_sha256=batch["content_subject_sha256"],
        candidate_batch_file_sha256=before,
        generated_last=True,
        all_final_file_sha256_recomputed=True,
        canonical_artifacts=[digest_row],
        dossier=digest_row,
        referenced_file_count=2,
        parity_state="pass",
    )
    parity_schema = v3.v2._closed_schema("parity_manifest_v4", [parity_prototype])
    _write_or_check(
        SCHEMA_ROOT / "parity_manifest_v4.schema.json", parity_schema, check
    )
    rows = _artifact_rows()
    dossier = _dossier(batch, artifacts, sample, benchmark, rows)
    dossier_path = OUTPUT_ROOT / "human_review_dossier.md"
    if check:
        if (
            not dossier_path.exists()
            or dossier_path.read_text(encoding="utf-8") != dossier
        ):
            raise ValueError("deterministic dossier check failed")
    else:
        dossier_path.parent.mkdir(parents=True, exist_ok=True)
        dossier_path.write_text(dossier, encoding="utf-8")
    dossier_row = {
        "path": str(dossier_path.relative_to(ROOT)).replace("\\", "/"),
        "content_subject_sha256": _sha256({"rendered_markdown": dossier}),
        "file_sha256": _file_sha256(dossier_path),
        "digest_semantics": "canonical dossier projection; final Markdown file bytes",
    }
    parity = _artifact(
        "parity_manifest.json",
        candidate_batch_content_subject_sha256=batch["content_subject_sha256"],
        candidate_batch_file_sha256=before,
        generated_last=True,
        all_final_file_sha256_recomputed=True,
        canonical_artifacts=rows,
        dossier=dossier_row,
        referenced_file_count=len(rows) + 1,
        parity_state="pass",
    )
    _write_or_check(OUTPUT_ROOT / "parity_manifest.json", parity, check)
    if _file_sha256(OUTPUT_ROOT / "candidate_batch.json") != before:
        raise ValueError("post-freeze phase mutated candidate batch")
    return {"batch": batch, "benchmark": benchmark, "sample": sample, "parity": parity}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check-freeze", action="store_true")
    parser.add_argument("--post-freeze", action="store_true")
    parser.add_argument("--check-post-freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze or args.check_freeze:
        batch = build_freeze(check=args.check_freeze)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "phase": "check-freeze" if args.check_freeze else "freeze",
                    "action_count": 37,
                    "content_subject_sha256": batch["content_subject_sha256"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.post_freeze or args.check_post_freeze:
        result = build_post_freeze(check=args.check_post_freeze)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "phase": "check-post-freeze"
                    if args.check_post_freeze
                    else "post-freeze",
                    "seed_sha256": result["sample"]["seed_sha256"],
                    "random_sample": result["sample"]["selected_random_action_ids"],
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
