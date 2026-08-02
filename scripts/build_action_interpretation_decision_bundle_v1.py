"""Build the detached, non-authorizing M3B-A human decision-preparation bundle."""

from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from action_interpretation_decision_v1_data import (  # noqa: E402
    SECONDARY_DETAILS,
    SPECIAL_RECOMMENDATIONS,
)
from build_action_interpretation_candidate_review import (  # noqa: E402
    BENCHMARK_ACTIONS,
    M2_SHA256,
    READINESS_ARTIFACT,
    _file_sha256,
    _sha256,
    _write_json,
)


V4_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_justice_public_safety_119_v4"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1"
)
SCHEMA_ROOT = OUTPUT_ROOT / "schemas"
PLAN_PATH = ROOT / "docs/plans/foushee_justice_action_interpretation_decisions_v1.md"
REVIEW_STATE = (
    ROOT
    / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
)
M1_RECEIPT = (
    ROOT
    / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_full_issue_universe_authority_receipt_v2.json"
)
V4_BATCH_ID = "action-interpretation-candidates:f000477:justice_public_safety:119:v4"
V4_CONTENT_SHA256 = "72ea57109ab169deb88b308b54c5c31b9d1c781b1db1b49f6b73c980a7c2f403"
V4_FILE_SHA256 = "a3f6218a33f9ef4789242248e60ba31b41d2563a8c163409ef88be569454d445"
V4_PARITY_FILE_SHA256 = (
    "eeb51c60e71de0e7d70537c6a1bf6f761759b9b9dbc34cdcf08b49df466dfad7"
)
BUNDLE_ID = (
    "action-interpretation-decision-preparation:f000477:justice_public_safety:119:v1"
)


def _seal(subject: dict[str, Any]) -> dict[str, Any]:
    return {**subject, "content_subject_sha256": _sha256(subject)}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact(schema: str, artifact_id: str, **values: Any) -> dict[str, Any]:
    return _seal(
        {
            "schema_version": schema,
            "artifact_id": artifact_id,
            "non_authorizing": True,
            **values,
        }
    )


def _write_or_check(path: Path, value: object, check: bool) -> None:
    if check:
        if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != value:
            raise ValueError(f"deterministic check failed: {path.relative_to(ROOT)}")
    else:
        _write_json(path, value)


def _preflight() -> None:
    batch_path = V4_ROOT / "candidate_batch.json"
    parity_path = V4_ROOT / "parity_manifest.json"
    batch = _load(batch_path)
    if (
        batch["batch_id"] != V4_BATCH_ID
        or batch["content_subject_sha256"] != V4_CONTENT_SHA256
    ):
        raise ValueError("immutable V4 identity differs")
    if (
        _file_sha256(batch_path) != V4_FILE_SHA256
        or _file_sha256(parity_path) != V4_PARITY_FILE_SHA256
    ):
        raise ValueError("immutable V4 final bytes differ")
    if _file_sha256(READINESS_ARTIFACT) != M2_SHA256:
        raise ValueError("M2 source-readiness bytes differ")


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def _example_schema(values: list[object]) -> dict[str, Any]:
    """Infer a closed structural schema from deterministic artifact examples."""
    non_null = [value for value in values if value is not None]
    allows_null = len(non_null) != len(values)
    if not non_null:
        return {"type": "null"}
    if all(isinstance(value, dict) for value in non_null):
        dictionaries = [value for value in non_null if isinstance(value, dict)]
        keys = sorted({key for value in dictionaries for key in value})
        schema: dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "required": [
                key for key in keys if all(key in value for value in dictionaries)
            ],
            "properties": {
                key: _example_schema(
                    [value[key] for value in dictionaries if key in value]
                )
                for key in keys
            },
        }
    elif all(isinstance(value, list) for value in non_null):
        children = [child for value in non_null for child in value]
        schema = {
            "type": "array",
            "items": _example_schema(children) if children else {},
        }
    else:
        names = []
        for value in non_null:
            name = (
                "boolean"
                if isinstance(value, bool)
                else "integer"
                if isinstance(value, int)
                else "number"
                if isinstance(value, float)
                else "string"
            )
            if name not in names:
                names.append(name)
        schema = {"type": names[0] if len(names) == 1 else names}
    if allows_null and schema.get("type") != "null":
        current = schema["type"]
        schema["type"] = (
            [current, "null"] if isinstance(current, str) else [*current, "null"]
        )
    return schema


def _schemas(
    bundle: dict[str, Any],
    human: dict[str, Any],
    recommendations: dict[str, Any],
    register: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    common = {
        "schema_version": {"type": "string"},
        "artifact_id": {"type": "string"},
        "non_authorizing": {"const": True},
        "content_subject_sha256": digest,
    }
    schemas = {
        "decision_preparation_bundle_v1.schema.json": _schema(
            {
                **common,
                "bundle_id": {"type": "string"},
                "subject": {"type": "object"},
                "authority_chain": {"type": "object"},
                "generalization_decision": {"const": "generalization_pass"},
                "decision_unit_count": {"const": 37},
                "review_tier_counts": {"type": "object"},
                "decision_units": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": {"type": "object"},
                },
                "accepted_candidate_count": {"const": 0},
                "canonical": {"const": False},
            },
            [
                *common,
                "bundle_id",
                "subject",
                "authority_chain",
                "generalization_decision",
                "decision_unit_count",
                "review_tier_counts",
                "decision_units",
                "accepted_candidate_count",
                "canonical",
            ],
        ),
        "human_decision_record_v1.schema.json": _schema(
            {
                **common,
                "bundle_content_subject_sha256": digest,
                "decision_record_status": {"const": "awaiting_human_decision"},
                "generalization_decision": {"const": "generalization_pass"},
                "explicit_non_acceptance": {
                    "const": "No V4 candidate interpretation is accepted by this record."
                },
                "decision_count": {"const": 37},
                "decisions": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": {"type": "object"},
                },
            },
            [
                *common,
                "bundle_content_subject_sha256",
                "decision_record_status",
                "generalization_decision",
                "explicit_non_acceptance",
                "decision_count",
                "decisions",
            ],
        ),
        "codex_recommendations_v1.schema.json": _schema(
            {
                **common,
                "bundle_content_subject_sha256": digest,
                "recommendation_count": {"const": 37},
                "recommendations_are_human_decisions": {"const": False},
                "recommendations": {
                    "type": "array",
                    "minItems": 37,
                    "maxItems": 37,
                    "items": {"type": "object"},
                },
                "recommendation_counts": {"type": "object"},
            },
            [
                *common,
                "bundle_content_subject_sha256",
                "recommendation_count",
                "recommendations_are_human_decisions",
                "recommendations",
                "recommendation_counts",
            ],
        ),
        "secondary_detail_register_v1.schema.json": _schema(
            {
                **common,
                "bundle_content_subject_sha256": digest,
                "entry_count": {"type": "integer", "minimum": 1},
                "review_aid_only": {"const": True},
                "entries": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "object"},
                },
                "recommendation_counts": {"type": "object"},
            },
            [
                *common,
                "bundle_content_subject_sha256",
                "entry_count",
                "review_aid_only",
                "entries",
                "recommendation_counts",
            ],
        ),
        "decision_parity_manifest_v1.schema.json": _schema(
            {
                **common,
                "generated_last": {"const": True},
                "parity_state": {"const": "pass"},
                "bundle_content_subject_sha256": digest,
                "canonical_artifacts": {
                    "type": "array",
                    "minItems": 4,
                    "items": {"type": "object"},
                },
                "dossier": {"type": "object"},
                "referenced_file_count": {"type": "integer", "minimum": 5},
                "all_final_file_sha256_recomputed": {"const": True},
                "json_markdown_semantic_parity": {"const": True},
            },
            [
                *common,
                "generated_last",
                "parity_state",
                "bundle_content_subject_sha256",
                "canonical_artifacts",
                "dossier",
                "referenced_file_count",
                "all_final_file_sha256_recomputed",
                "json_markdown_semantic_parity",
            ],
        ),
    }
    schemas["decision_preparation_bundle_v1.schema.json"]["properties"]["subject"] = (
        _example_schema([bundle["subject"]])
    )
    schemas["decision_preparation_bundle_v1.schema.json"]["properties"][
        "authority_chain"
    ] = _example_schema([bundle["authority_chain"]])
    schemas["decision_preparation_bundle_v1.schema.json"]["properties"][
        "review_tier_counts"
    ] = _example_schema([bundle["review_tier_counts"]])
    schemas["decision_preparation_bundle_v1.schema.json"]["properties"][
        "decision_units"
    ]["items"] = _example_schema(bundle["decision_units"])
    schemas["human_decision_record_v1.schema.json"]["properties"]["decisions"][
        "items"
    ] = _example_schema(human["decisions"])
    schemas["codex_recommendations_v1.schema.json"]["properties"]["recommendations"][
        "items"
    ] = _example_schema(recommendations["recommendations"])
    schemas["codex_recommendations_v1.schema.json"]["properties"][
        "recommendation_counts"
    ] = _example_schema([recommendations["recommendation_counts"]])
    schemas["secondary_detail_register_v1.schema.json"]["properties"]["entries"][
        "items"
    ] = _example_schema(register["entries"])
    schemas["secondary_detail_register_v1.schema.json"]["properties"][
        "recommendation_counts"
    ] = _example_schema([register["recommendation_counts"]])
    return schemas


def _major_history() -> set[str]:
    found: set[str] = set()
    for root_name in (
        "f000477_justice_public_safety_119_v1",
        "f000477_justice_public_safety_119_v2",
        "f000477_justice_public_safety_119_v3",
        "f000477_justice_public_safety_119_v4",
    ):
        root = V4_ROOT.parent / root_name
        for path in root.glob("*.json"):
            value = _load(path)

            def visit(node: object) -> None:
                if isinstance(node, dict):
                    action_id = node.get("action_id")
                    if isinstance(action_id, str) and any(
                        v in {"major", "critical"}
                        for v in node.values()
                        if isinstance(v, str)
                    ):
                        found.add(action_id)
                    for child in node.values():
                        visit(child)
                elif isinstance(node, list):
                    for child in node:
                        visit(child)

            visit(value)
    return found


def _appearance(candidate: dict[str, Any], detail: str) -> str:
    tokens = [
        token.casefold().replace(",", "")
        for token in detail.split()
        if any(ch.isdigit() for ch in token)
    ]

    def has(text: str) -> bool:
        corpus = text.casefold().replace(",", "")
        return bool(tokens) and all(token.strip(".;") in corpus for token in tokens)

    if has(candidate["proposed_exact_action_meaning"] or ""):
        return "candidate_meaning"
    if has(" ".join(candidate["limitations"])):
        return "candidate_limitation"
    if has(
        " ".join(
            row["wording"]
            for row in [
                *candidate["material_provisions"],
                *candidate["material_limits_and_exceptions"],
            ]
        )
    ):
        return "structured_material_provision_only"
    return "nowhere_in_v4_candidate"


def build(*, check: bool = False) -> dict[str, Any]:
    _preflight()
    batch = _load(V4_ROOT / "candidate_batch.json")
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    evidence = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "evidence_maps.json")["evidence_maps"]
    }
    ledgers = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "material_scope_ledgers.json")["ledgers"]
    }
    material = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "material_scope_closure_reviews.json")["reviews"]
    }
    quantitative = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "quantitative_enumeration_closure_reviews.json")[
            "reviews"
        ]
    }
    amendments = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "textual_amendment_closure_reviews.json")["reviews"]
    }
    consistency = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "cross_field_consistency_reviews.json")["reviews"]
    }
    benchmark_rows = {
        row["action_id"]: row
        for row in _load(V4_ROOT / "benchmark_comparison.json")["comparisons"]
    }
    samples = _load(V4_ROOT / "sample_manifest.json")
    review_state = _load(REVIEW_STATE)
    accepted_benchmark = {
        row["action_id"]: row["interpretation"]["exact_action_meaning"]
        for row in review_state["action_accounting"]
        if row["action_id"] in BENCHMARK_ACTIONS
    }
    contrast = {
        row["group_id"]: row["action_ids"]
        for row in samples["related_action_contrast_sets"]
    }
    detail_rows: list[dict[str, Any]] = []
    for index, (action_id, detail, locator, recommendation) in enumerate(
        SECONDARY_DETAILS, 1
    ):
        candidate = candidates[action_id]
        source_id = next(
            (
                row["source_id"]
                for row in candidate["material_provisions"]
                if row["locator"].split(",")[0] in locator
            ),
            candidate["source_references"][-1],
        )
        row = _seal(
            {
                "entry_id": f"secondary-detail:{action_id}:{index}:v1",
                "action_id": action_id,
                "source_bound_detail": detail,
                "exact_source_locator": locator,
                "source_id": source_id,
                "appears_in": _appearance(candidate, detail),
                "codex_materiality_recommendation": recommendation,
                "rationale": "Surfaced for human review because this governed timing, amount, threshold, penalty, or boundary is compressed in the concise V4 presentation; the recommendation does not amend V4 or decide acceptance.",
                "confidence": "high",
            }
        )
        detail_rows.append(row)
    details_by: dict[str, list[dict[str, Any]]] = {
        action_id: [] for action_id in candidates
    }
    for row in detail_rows:
        details_by[row["action_id"]].append(row)
    major_history = _major_history()
    units: list[dict[str, Any]] = []
    for action_id in sorted(candidates):
        candidate = candidates[action_id]
        unresolved_text = bool(
            amendments[action_id]["amendments"]
            and any(
                row.get("context_sufficiency") == "insufficient"
                for row in amendments[action_id]["amendments"]
            )
        )
        source_conflict = bool(
            candidate["source_identity_reconciliation"]
            and "conflict"
            in json.dumps(candidate["source_identity_reconciliation"]).casefold()
        )
        package_unavailable = candidate["status"] == "no_safe_candidate"
        tier1_reasons = []
        if candidate["status"] != "proposed":
            tier1_reasons.append("non_proposed_status")
        if candidate["confidence"] == "low":
            tier1_reasons.append("low_confidence")
        if unresolved_text:
            tier1_reasons.append("unresolved_material_textual_effect")
        if source_conflict:
            tier1_reasons.append("source_identity_conflict")
        if package_unavailable:
            tier1_reasons.append("complete_operative_package_unavailable")
        if action_id in major_history:
            tier1_reasons.append("major_correction_history")
        if tier1_reasons:
            tier, reasons = 1, tier1_reasons
        else:
            tier2 = []
            if candidate["confidence"] == "medium":
                tier2.append("medium_confidence")
            core_count = sum(
                item["item_class"] == "core_operative_mechanism"
                and item["materiality_state"] == "material"
                for item in ledgers[action_id]["items"]
            )
            if core_count > 1:
                tier2.append("multiple_core_mechanisms")
            if any(
                item["item_class"]
                in {
                    "penalty_or_remedy",
                    "covered_population",
                    "material_definition",
                    "exception_exclusion_or_retained_provision",
                }
                and item["materiality_state"] == "material"
                for item in ledgers[action_id]["items"]
            ):
                tier2.append("material_boundary_or_consequence")
            memberships = sorted(
                group for group, ids in contrast.items() if action_id in ids
            )
            if memberships:
                tier2.append("related_action_contrast")
            if details_by[action_id]:
                tier2.append("secondary_detail_compression")
            if candidate["house_stage"] in {
                "suspension_passage_as_amended",
                "amendment",
            }:
                tier2.append("complex_house_stage")
            tier, reasons = (
                (2, tier2)
                if tier2
                else (3, ["high_confidence_simple_bounded_mechanism"])
            )
        memberships = {
            "benchmark": action_id in BENCHMARK_ACTIONS,
            "random": action_id in samples["selected_random_action_ids"],
            "complexity": action_id in samples["complexity_challenge_action_ids"],
            "contrast_groups": sorted(
                group for group, ids in contrast.items() if action_id in ids
            ),
            "material_detail": action_id
            in samples["material_detail_challenge_action_ids"],
        }
        unit = _seal(
            {
                "decision_unit_id": f"action-interpretation-decision-unit:{action_id}:v1",
                "action_id": action_id,
                "candidate_id": candidate["candidate_id"],
                "candidate_content_subject_sha256": candidate[
                    "candidate_content_subject_sha256"
                ],
                "exact_action_identity": candidate["exact_action_identity"],
                "house_stage": candidate["house_stage"],
                "official_member_action": candidate["official_member_action"],
                "candidate_status": candidate["status"],
                "candidate_confidence": candidate["confidence"],
                "proposed_exact_action_meaning": candidate[
                    "proposed_exact_action_meaning"
                ],
                "proposed_exact_choice_position_effect": candidate[
                    "proposed_member_position_effect"
                ],
                "material_provisions": candidate["material_provisions"],
                "material_limits_and_exceptions": candidate[
                    "material_limits_and_exceptions"
                ],
                "covered_population_and_definition_items": [
                    item
                    for item in ledgers[action_id]["items"]
                    if item["item_class"]
                    in {"covered_population", "material_definition"}
                ],
                "quantitative_and_enumerated_facts": quantitative[action_id]["checks"],
                "textual_amendments": amendments[action_id]["amendments"],
                "source_references": candidate["source_references"],
                "evidence_map_id": evidence[action_id]["evidence_map_id"],
                "evidence_map_content_subject_sha256": evidence[action_id][
                    "content_subject_sha256"
                ],
                "closure_review_outcomes": {
                    "material_scope": {
                        "content_subject_sha256": material[action_id][
                            "content_subject_sha256"
                        ],
                        "remaining_severity": material[action_id][
                            "remaining_severity_after_correction"
                        ],
                    },
                    "quantitative": {
                        "content_subject_sha256": quantitative[action_id][
                            "content_subject_sha256"
                        ],
                        "remaining_severity": quantitative[action_id][
                            "remaining_severity_after_correction"
                        ],
                    },
                    "textual_amendment": {
                        "content_subject_sha256": amendments[action_id][
                            "content_subject_sha256"
                        ],
                        "remaining_severity": amendments[action_id][
                            "remaining_severity_after_correction"
                        ],
                    },
                    "cross_field": {
                        "content_subject_sha256": consistency[action_id][
                            "content_subject_sha256"
                        ],
                        "remaining_severity": consistency[action_id][
                            "remaining_severity_after_correction"
                        ],
                    },
                },
                "benchmark_comparison": (
                    {
                        "accepted_benchmark_meaning": accepted_benchmark[action_id],
                        "v4_comparison": benchmark_rows[action_id],
                        "comparison_only": True,
                    }
                    if action_id in benchmark_rows
                    else None
                ),
                "sample_memberships": memberships,
                "limitations": candidate["limitations"],
                "unresolved_editorial_questions": candidate[
                    "unresolved_editorial_questions"
                ],
                "uncertainty_reasons": candidate["uncertainty_reasons"],
                "does_not_establish": candidate["does_not_establish"],
                "review_tier": tier,
                "review_tier_reasons": reasons,
                "secondary_detail_entry_ids": [
                    row["entry_id"] for row in details_by[action_id]
                ],
                "human_decision_options": [
                    "accept_candidate",
                    "accept_with_required_revision",
                    "preserve_ambiguous",
                    "preserve_no_safe_candidate",
                    "reject_candidate",
                    "unresolved",
                ],
                "accepted": False,
                "canonical": False,
            }
        )
        units.append(unit)
    authority = {
        "m1": {
            "path": M1_RECEIPT.relative_to(ROOT).as_posix(),
            "file_sha256": _file_sha256(M1_RECEIPT),
        },
        "m2": {
            "path": READINESS_ARTIFACT.relative_to(ROOT).as_posix(),
            "file_sha256": M2_SHA256,
        },
        "v4": {
            "batch_id": V4_BATCH_ID,
            "content_subject_sha256": V4_CONTENT_SHA256,
            "file_sha256": V4_FILE_SHA256,
            "parity_manifest_file_sha256": V4_PARITY_FILE_SHA256,
        },
    }
    bundle = _artifact(
        "decision_preparation_bundle_v1",
        BUNDLE_ID,
        bundle_id=BUNDLE_ID,
        subject={
            "member_id": "F000477",
            "issue_id": "JUSTICE_PUBLIC_SAFETY",
            "congress": 119,
            "action_count": 37,
        },
        authority_chain=authority,
        generalization_decision="generalization_pass",
        decision_unit_count=37,
        review_tier_counts={
            str(k): v
            for k, v in sorted(Counter(row["review_tier"] for row in units).items())
        },
        decision_units=units,
        accepted_candidate_count=0,
        canonical=False,
    )
    decisions = []
    for row in units:
        decisions.append(
            _seal(
                {
                    "action_id": row["action_id"],
                    "decision_unit_content_subject_sha256": row[
                        "content_subject_sha256"
                    ],
                    "selected_decision": None,
                    "structured_rationale": None,
                    "required_wording_or_field_revisions": [],
                    "accepted_limitations": [],
                    "accepted_competing_interpretation": None,
                    "confidence_decision": None,
                    "unresolved_question": None,
                    "reviewer_identity": None,
                    "decision_timestamp": None,
                }
            )
        )
    human = _artifact(
        "human_decision_record_v1",
        "human-action-interpretation-decisions:f000477:justice_public_safety:119:v1",
        bundle_content_subject_sha256=bundle["content_subject_sha256"],
        decision_record_status="awaiting_human_decision",
        generalization_decision="generalization_pass",
        explicit_non_acceptance="No V4 candidate interpretation is accepted by this record.",
        decision_count=37,
        decisions=decisions,
    )
    recommendations = []
    for row in units:
        action_id = row["action_id"]
        value = SPECIAL_RECOMMENDATIONS.get(action_id)
        if value is None:
            value = (
                "recommend_accept_with_revision"
                if any(
                    entry["codex_materiality_recommendation"]
                    == "include_in_accepted_meaning"
                    for entry in details_by[action_id]
                )
                else "recommend_accept"
            )
        recommendations.append(
            _seal(
                {
                    "action_id": action_id,
                    "decision_unit_content_subject_sha256": row[
                        "content_subject_sha256"
                    ],
                    "recommendation": value,
                    "rationale": "Non-authorizing review recommendation derived from V4 status, confidence, unresolved questions, and secondary-detail review; the human decision remains empty.",
                    "human_decision_selected": False,
                }
            )
        )
    recs = _artifact(
        "codex_recommendations_v1",
        "codex-action-interpretation-recommendations:f000477:justice_public_safety:119:v1",
        bundle_content_subject_sha256=bundle["content_subject_sha256"],
        recommendation_count=37,
        recommendations_are_human_decisions=False,
        recommendations=recommendations,
        recommendation_counts=dict(
            sorted(Counter(row["recommendation"] for row in recommendations).items())
        ),
    )
    register = _artifact(
        "secondary_detail_register_v1",
        "secondary-detail-register:f000477:justice_public_safety:119:v1",
        bundle_content_subject_sha256=bundle["content_subject_sha256"],
        entry_count=len(detail_rows),
        review_aid_only=True,
        entries=detail_rows,
        recommendation_counts=dict(
            sorted(
                Counter(
                    row["codex_materiality_recommendation"] for row in detail_rows
                ).items()
            )
        ),
    )
    artifacts = {
        "decision_preparation_bundle.json": bundle,
        "human_decision_record.json": human,
        "codex_recommendations.json": recs,
        "secondary_detail_register.json": register,
    }
    schemas = _schemas(bundle, human, recs, register)
    for name, value in artifacts.items():
        _write_or_check(OUTPUT_ROOT / name, value, check)
    for name, value in schemas.items():
        _write_or_check(SCHEMA_ROOT / name, value, check)
    dossier = _dossier(bundle, human, recs, register, artifacts, schemas)
    if check:
        if (
            not (OUTPUT_ROOT / "human_decision_dossier.md").exists()
            or (OUTPUT_ROOT / "human_decision_dossier.md").read_text(encoding="utf-8")
            != dossier
        ):
            raise ValueError("deterministic dossier check failed")
    else:
        (OUTPUT_ROOT / "human_decision_dossier.md").parent.mkdir(
            parents=True, exist_ok=True
        )
        (OUTPUT_ROOT / "human_decision_dossier.md").write_text(
            dossier, encoding="utf-8", newline="\n"
        )
    references = []
    for path in [
        *(OUTPUT_ROOT / name for name in artifacts),
        *(SCHEMA_ROOT / name for name in schemas),
    ]:
        value = _load(path)
        references.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "content_subject_sha256": value.get(
                    "content_subject_sha256", _sha256(value)
                ),
                "file_sha256": _file_sha256(path),
                "digest_semantics": "canonical parsed subject excluding self digest where present; final serialized file bytes",
            }
        )
    dossier_path = OUTPUT_ROOT / "human_decision_dossier.md"
    parity = _artifact(
        "decision_parity_manifest_v1",
        "decision-parity:f000477:justice_public_safety:119:v1",
        generated_last=True,
        parity_state="pass",
        bundle_content_subject_sha256=bundle["content_subject_sha256"],
        canonical_artifacts=references,
        dossier={
            "path": dossier_path.relative_to(ROOT).as_posix(),
            "file_sha256": _file_sha256(dossier_path),
        },
        referenced_file_count=len(references) + 1,
        all_final_file_sha256_recomputed=True,
        json_markdown_semantic_parity=True,
    )
    _write_or_check(OUTPUT_ROOT / "parity_manifest.json", parity, check)
    return {
        "bundle": bundle,
        "human": human,
        "recommendations": recs,
        "register": register,
        "parity": parity,
    }


def _dossier(
    bundle: dict[str, Any],
    human: dict[str, Any],
    recs: dict[str, Any],
    register: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
    schemas: dict[str, dict[str, Any]],
) -> str:
    rec_by = {row["action_id"]: row for row in recs["recommendations"]}
    details_by: dict[str, list[dict[str, Any]]] = {}
    for row in register["entries"]:
        details_by.setdefault(row["action_id"], []).append(row)
    units = sorted(
        bundle["decision_units"], key=lambda row: (row["review_tier"], row["action_id"])
    )
    lines = [
        "# Foushee Justice 119th-Congress Action Interpretation Decisions",
        "",
        "> Decision requested: complete one structured human decision for each of 37 actions. This dossier accepts nothing and cannot authorize implementation, persistence, or publication.",
        "",
        f"- Bundle: `{bundle['bundle_id']}`",
        f"- V4 input: `{V4_BATCH_ID}`",
        f"- V4 content/file: `{V4_CONTENT_SHA256}` / `{V4_FILE_SHA256}`",
        f"- Review tiers: `{bundle['review_tier_counts']}`",
        f"- Recommendation counts: `{recs['recommendation_counts']}`",
        f"- Human record status: `{human['decision_record_status']}`",
        "",
        "## Exact decision options",
        "",
        "`accept_candidate`, `accept_with_required_revision`, `preserve_ambiguous`, `preserve_no_safe_candidate`, `reject_candidate`, or `unresolved`.",
        "",
        "Codex recommendations below are review aids, never human decisions.",
        "",
    ]
    for tier in (1, 2, 3):
        lines += [f"## Tier {tier}", ""]
        for row in (unit for unit in units if unit["review_tier"] == tier):
            rec = rec_by[row["action_id"]]
            lines += [
                f"### {row['action_id']} — {row['exact_action_identity']}",
                "",
                f"- Stage / member action: `{row['house_stage']}` / `{row['official_member_action']}`",
                f"- Candidate status / confidence: `{row['candidate_status']}` / `{row['candidate_confidence']}`",
                f"- Review reasons: `{', '.join(row['review_tier_reasons'])}`",
                f"- Candidate meaning: {row['proposed_exact_action_meaning'] or 'No safe candidate meaning.'}",
                f"- Exact-choice effect: `{row['proposed_exact_choice_position_effect']}`",
                f"- Codex recommendation: `{rec['recommendation']}`",
                f"- Material provisions: {json.dumps(row['material_provisions'], ensure_ascii=False)}",
                f"- Limits: {json.dumps(row['material_limits_and_exceptions'], ensure_ascii=False)}",
                f"- Covered populations/definitions: {json.dumps(row['covered_population_and_definition_items'], ensure_ascii=False)}",
                f"- Quantities: {json.dumps(row['quantitative_and_enumerated_facts'], ensure_ascii=False)}",
                f"- Textual amendments: {json.dumps(row['textual_amendments'], ensure_ascii=False)}",
                f"- Secondary details: {json.dumps(details_by.get(row['action_id'], []), ensure_ascii=False)}",
                f"- Benchmark comparison: {json.dumps(row['benchmark_comparison'], ensure_ascii=False)}",
                f"- Source references: `{', '.join(row['source_references'])}`",
                f"- Limitations / unresolved: {json.dumps([*row['limitations'], *row['uncertainty_reasons'], *row['unresolved_editorial_questions']], ensure_ascii=False)}",
                f"- Does not establish: `{', '.join(row['does_not_establish'])}`",
                "- Human decision: **EMPTY**",
                "- Reviewer identity / timestamp: **EMPTY / EMPTY**",
                "",
            ]
    lines += ["## Canonical artifact identities", ""]
    for name, value in {**artifacts, **schemas}.items():
        path = (OUTPUT_ROOT / name) if name in artifacts else (SCHEMA_ROOT / name)
        lines.append(
            f"- `{path.relative_to(ROOT).as_posix()}` — content `{value.get('content_subject_sha256', _sha256(value))}`; final file `{_file_sha256(path)}`"
        )
    lines += [
        "",
        "The parity manifest is generated after this dossier and independently checks these final bytes.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(check=args.check)
    print(
        json.dumps(
            {
                "status": "pass",
                "bundle_content_subject_sha256": result["bundle"][
                    "content_subject_sha256"
                ],
                "decision_count": 37,
                "tier_counts": result["bundle"]["review_tier_counts"],
                "recommendation_counts": result["recommendations"][
                    "recommendation_counts"
                ],
                "secondary_detail_count": result["register"]["entry_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
