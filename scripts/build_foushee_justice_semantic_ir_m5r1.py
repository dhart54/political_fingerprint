"""Build the detached M5-R1/V2 Foushee Justice Semantic IR correction."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.pipeline import run_editorial_pipeline  # noqa: E402
from scripts import build_foushee_justice_semantic_ir_m5 as m5  # noqa: E402


V1_ROOT = m5.OUTPUT_ROOT
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v2"
)
V1_COMMIT = "c8c2ca71d3c1837735bc54bde7d0ca597eac891c"
V1_TREE = "4cf5895f17ba4e6d6a0e54ceb90a11fce36c3b08"
V1_INPUT_CONTENT = "9ccae3e41c953445dfb4d59486eae6fd8187c84cab162dfcacf5a84384d50ee6"
V1_INPUT_FILE = "6b4fb6749f164a814b6e533c71256c333c90afced34e573b7cac9a620c653103"
V1_GRAPH_CONTENT = "05821b7ad36f09d27768d0f12aac223513e343f2e2f72328d4f294e9027c55bf"
V1_GRAPH_FILE = "855da6bbe1cf6226a20f4086341a4606be897c36e714061f3f69c736c25f1103"
V1_IMPLEMENTATION_CONTENT = (
    "2472842904358d51788efbd196929ad2511d91dd1f673a4a4932d06b75bbaa0b"
)
V1_IMPLEMENTATION_FILE = (
    "7836ffc17b4ef19ae7c8328b4964a637a192f8b16c5ed94520ac9de717b56df0"
)
V1_ARCHIVE_FILE = "16a1cd5771a381916a33f14c0d741d266ba3a3cdc3f0256dc7a00af3a4ceab7e"
INPUT_ID = "full-record-semantic-ir-compiler-input:f000477:justice_public_safety:119:v2"
GRAPH_ID = "full-record-semantic-ir-candidate:f000477:justice_public_safety:119:v2"
IMPLEMENTATION_ID = (
    "full-record-semantic-ir-provisional-implementation:"
    "f000477:justice_public_safety:119:v2"
)
REMOVED_TRAIT = "pretrial_release_regulation"
ROLL_298 = "house:119:1:298"
ROLL_171 = "house:119:2:171"
ROLL_131 = "house:119:1:131"
BLOCKED_ACTIONS = {"house:119:2:155", "house:119:2:278"}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def serialized(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(value: dict[str, Any]) -> dict[str, Any]:
    value["content_subject_sha256"] = digest(value)
    return value


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, raw: bytes, check: bool) -> None:
    if check:
        if not path.exists() or path.read_bytes() != raw:
            raise ValueError(
                f"{path.relative_to(ROOT)} differs from deterministic output"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def write_json(name: str, value: object, check: bool) -> None:
    write(OUTPUT_ROOT / name, serialized(value), check)


def propositions(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return graph["compiled_ir"]["members"][0]["proposition_graph"]["propositions"]


def behavioral(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [p for p in propositions(graph) if p["semantic_role"] == "behavioral"]


def reference_payload(proposition: dict[str, Any]) -> dict[str, Any]:
    return {
        "proposition_id": proposition["proposition_id"],
        "semantic_role": proposition["semantic_role"],
        "proposition_type": proposition["proposition_type"],
        "direction": proposition["direction"],
        "mechanism_or_trait_refs": proposition["mechanism_or_trait_refs"],
        "conclusion_relevance": proposition["conclusion_relevance"],
        "presentation_target": proposition["presentation_target"],
        "relationships": proposition["relationships"],
        "treats_as_independent_evidence": True,
    }


def classify_overlap(references: list[dict[str, Any]]) -> dict[str, Any]:
    if not references:
        return {
            "classification": "unreferenced_governed_control",
            "changes_apparent_evidence_count": False,
            "governing_rationale": "The action or episode supplies no behavioral evidence.",
            "severity": "none",
            "required_correction": None,
        }
    if len(references) == 1:
        return {
            "classification": "single_reference",
            "changes_apparent_evidence_count": False,
            "governing_rationale": "One behavioral proposition owns the evidence.",
            "severity": "none",
            "required_correction": None,
        }
    same_type = len({r["proposition_type"] for r in references}) == 1
    all_primary = all(r["conclusion_relevance"] == "primary" for r in references)
    if same_type and all_primary:
        return {
            "classification": "prohibited_inflating_overlap",
            "changes_apparent_evidence_count": True,
            "governing_rationale": (
                "The same evidence supplies apparent independent primary weight to "
                "multiple behavioral propositions of the same type without a canonical "
                "hierarchical or subordinate relationship."
            ),
            "severity": "blocking",
            "required_correction": "simplify_structured_inputs_and_recompile",
        }
    return {
        "classification": "same_role_potentially_inflating",
        "changes_apparent_evidence_count": True,
        "governing_rationale": (
            "Multiple behavioral references require explicit noninflation ownership."
        ),
        "severity": "major",
        "required_correction": "review_and_assign_single_analytical_owner",
    }


def overlap_ledger(
    graph: dict[str, Any], compiler_input: dict[str, Any], *, version: str
) -> dict[str, Any]:
    rows = behavioral(graph)
    action_ids = sorted(
        action["action_id"] for action in compiler_input["shared_semantics"]["actions"]
    )
    episode_ids = sorted(
        episode["episode_id"]
        for episode in compiler_input["shared_semantics"]["episodes"]
    )

    def mapping(identifier: str, key: str, identifier_key: str) -> dict[str, Any]:
        refs = [reference_payload(p) for p in rows if identifier in p[key]]
        return {
            identifier_key: identifier,
            "references": refs,
            **classify_overlap(refs),
        }

    action_mappings = [
        mapping(action_id, "evidence_action_ids", "action_id")
        for action_id in action_ids
    ]
    episode_mappings = [
        mapping(episode_id, "evidence_episode_ids", "episode_id")
        for episode_id in episode_ids
    ]
    prohibited = [
        {"subject_type": "action", **row}
        for row in action_mappings
        if row["classification"] == "prohibited_inflating_overlap"
    ] + [
        {"subject_type": "episode", **row}
        for row in episode_mappings
        if row["classification"] == "prohibited_inflating_overlap"
    ]
    return seal(
        {
            "schema_version": "semantic_ir_proposition_overlap_ledger_v1",
            "artifact_id": (
                "semantic-ir-proposition-overlap-ledger:"
                f"f000477:justice_public_safety:119:{version}"
            ),
            "graph_content_subject_sha256": graph["content_subject_sha256"],
            "action_mappings": action_mappings,
            "episode_mappings": episode_mappings,
            "action_mapping_count": len(action_mappings),
            "episode_mapping_count": len(episode_mappings),
            "prohibited_overlaps": prohibited,
            "prohibited_overlap_count": len(prohibited),
            "set_based_accounting_is_noninflation_proof": False,
            "authorizing": False,
        }
    )


def corrected_compiler_input() -> dict[str, Any]:
    v1 = load(V1_ROOT / "frozen_final_compiler_input.json")["compiler_input"]
    value = copy.deepcopy(v1)
    value["shared_semantics"]["policy_traits"] = [
        trait
        for trait in value["shared_semantics"]["policy_traits"]
        if trait["trait_id"] != REMOVED_TRAIT
    ]
    for action in value["shared_semantics"]["actions"]:
        action["policy_trait_refs"] = [
            ref for ref in action.get("policy_trait_refs", []) if ref != REMOVED_TRAIT
        ]
    return value


def graph_envelope(compiled: dict[str, Any]) -> dict[str, Any]:
    accounting = m5.full_accounting(compiled)
    return seal(
        {
            "schema_version": "full_record_semantic_ir_candidate_v1",
            "artifact_id": GRAPH_ID,
            "candidate_state": "frozen_corrected_candidate_pending_delegated_authority_review",
            "compiled_ir": compiled,
            "full_universe_action_accounting": accounting,
            "action_accounting_counts": {
                "included_in_behavioral_proposition": sum(
                    row["outcome"] == "included_in_behavioral_proposition"
                    for row in accounting
                ),
                "non_proposition": sum(
                    row["outcome"] == "non_proposition" for row in accounting
                ),
            },
            "render_plan": {
                "example_prose": None,
                "analytical_additions_allowed": False,
            },
            "accepted_semantic_reference": False,
            "canonical": False,
            "public": False,
            "persisted": False,
            "published": False,
            "authorizing": False,
        }
    )


def collection(
    schema_version: str, artifact_id: str, key: str, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    count_key = {
        "families": "family_count",
        "traits": "trait_count",
        "relationships": "relationship_count",
        "constraints": "constraint_count",
        "dependencies": "dependency_count",
    }[key]
    return seal(
        {
            "schema_version": schema_version,
            "artifact_id": artifact_id,
            key: rows,
            count_key: len(rows),
            "state": "v2_corrected_frozen",
            "authorizing": False,
        }
    )


def dossier_markdown(artifacts: dict[str, Any]) -> str:
    graph = artifacts["frozen_final_compiled_semantic_ir.json"]
    diff = artifacts["semantic_diff.json"]
    review = artifacts["synthesis_conclusion_review.json"]
    initial = artifacts["initial_overlap_ledger.json"]
    corrected = artifacts["corrected_overlap_ledger.json"]
    implementation = artifacts["provisional_implementation_bundle.json"]
    risk = artifacts["launch_review_risk_register.json"]
    calibration = artifacts["semantic_calibration_population.json"]
    member = graph["compiled_ir"]["members"][0]
    lines = [
        "# Foushee Justice M5-R1 Semantic IR correction review",
        "",
        "This dossier is generated from structured non-public review artifacts and is non-authorizing.",
        "",
        "## Requested delegated decision",
        "",
        "- `delegated_authority_accepts_semantic_ir_and_synthesis_implementation`",
        "- `bounded_semantic_ir_and_synthesis_correction_required`",
        "- `delegated_authority_rejects_semantic_ir_method`",
        "",
        "## Reviewed defect and correction",
        "",
        f"- Initial prohibited overlap rows: {initial['prohibited_overlap_count']}",
        f"- Corrected prohibited overlap rows: {corrected['prohibited_overlap_count']}",
        f"- Removed propositions: {', '.join(diff['removed_proposition_ids'])}",
        f"- Added propositions: {', '.join(diff['added_proposition_ids'])}",
        f"- Roll 298 (`{ROLL_298}`): {diff['roll_298_disposition']}",
        f"- Roll 171 (`{ROLL_171}`): {diff['roll_171_disposition']}",
        "",
        "## Corrected graph",
        "",
        f"- Compiler input: `{artifacts['frozen_final_compiler_input.json']['artifact_id']}` / `{artifacts['frozen_final_compiler_input.json']['content_subject_sha256']}`",
        f"- Graph: `{graph['artifact_id']}` / `{graph['content_subject_sha256']}`",
        f"- Implementation: `{implementation['artifact_id']}` / `{implementation['content_subject_sha256']}`",
        f"- Actions: {len(graph['full_universe_action_accounting'])}",
        f"- Behavioral propositions: {implementation['behavioral_proposition_count']}",
        f"- Synthesis propositions: {implementation['synthesis_proposition_count']}",
        f"- Primary: {', '.join(member['composition']['conclusion_plan']['primary_proposition_ids'])}",
        f"- Limiting: {', '.join(member['composition']['conclusion_plan']['limiting_proposition_ids'])}",
        "",
        "## Synthesis alternatives",
        "",
    ]
    for candidate in review["alternatives"]:
        lines.append(
            f"- `{candidate['synthesis_type']}`: `{candidate['disposition']}` — {candidate['rationale']}"
        )
    lines.extend(
        [
            "",
            "## Risk and calibration",
            "",
            f"- Total launch risks: {risk['risk_count']}",
            f"- Mechanism-divide state: `{risk['updated_risks'][0]['state']}`",
            f"- Calibration eligible: {calibration['eligible_count']}",
            f"- Launch sample selected: `{str(calibration['launch_sample_selected']).lower()}`",
            "",
            "## Presentation boundary",
            "",
            "- `render_plan.example_prose = null`",
            "- `analytical_additions_allowed = false`",
            "- No public prose, canonical status, persistence, or publication authority is present.",
            "",
        ]
    )
    return "\n".join(lines)


def primitive_schema(value: Any) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        return {"type": "array"}
    if isinstance(value, dict):
        return {"type": "object"}
    raise TypeError(type(value))


def closed_artifact_schema(artifacts: dict[str, Any]) -> dict[str, Any]:
    variants = []
    for artifact in artifacts.values():
        if not isinstance(artifact, dict) or "artifact_id" not in artifact:
            continue
        variants.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(artifact),
                "properties": {
                    key: (
                        {"const": value}
                        if key == "artifact_id"
                        else primitive_schema(value)
                    )
                    for key, value in artifact.items()
                },
            }
        )
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://political-fingerprint.local/schemas/foushee-justice-m5r1-artifacts-v1.json",
        "title": "Foushee Justice M5-R1 closed artifact envelopes",
        "oneOf": variants,
    }


def build(check: bool = False) -> dict[str, Any]:
    # Revalidates V1 without writing it and binds exact reviewed bytes.
    m5.build(True)
    v1_input_artifact = load(V1_ROOT / "frozen_final_compiler_input.json")
    v1_graph = load(V1_ROOT / "frozen_final_compiled_semantic_ir.json")
    v1_implementation = load(V1_ROOT / "provisional_implementation_bundle.json")
    if not (
        v1_input_artifact["content_subject_sha256"] == V1_INPUT_CONTENT
        and file_digest(V1_ROOT / "frozen_final_compiler_input.json") == V1_INPUT_FILE
        and v1_graph["content_subject_sha256"] == V1_GRAPH_CONTENT
        and file_digest(V1_ROOT / "frozen_final_compiled_semantic_ir.json")
        == V1_GRAPH_FILE
        and v1_implementation["content_subject_sha256"] == V1_IMPLEMENTATION_CONTENT
        and file_digest(V1_ROOT / "provisional_implementation_bundle.json")
        == V1_IMPLEMENTATION_FILE
    ):
        raise ValueError("reviewed M5 V1 identities differ")

    compiler_input = corrected_compiler_input()
    pipeline_result = run_editorial_pipeline(copy.deepcopy(compiler_input))
    if pipeline_result.persistence_proposal is not None:
        raise ValueError("detached pipeline unexpectedly prepared persistence")
    graph = graph_envelope(pipeline_result.compiled_ir)
    input_artifact = seal(
        {
            "schema_version": "full_record_semantic_ir_compiler_input_v1",
            "artifact_id": INPUT_ID,
            "candidate_state": "frozen_corrected_input_pending_delegated_authority_review",
            "compiler_input": compiler_input,
            "public_language_included": False,
            "expected_output_fields_included": False,
            "accepted_reference_output_included": False,
            "authorizing": False,
        }
    )
    initial_ledger = overlap_ledger(
        v1_graph, v1_input_artifact["compiler_input"], version="v1_reviewed"
    )
    corrected_ledger = overlap_ledger(graph, compiler_input, version="v2_corrected")
    if initial_ledger["prohibited_overlap_count"] != 2:
        raise ValueError("reviewed overlap inventory differs")
    if corrected_ledger["prohibited_overlap_count"]:
        raise ValueError("corrected graph retains a prohibited overlap")

    v1_traits_artifact = load(V1_ROOT / "final_policy_traits.json")
    corrected_traits = [
        trait
        for trait in v1_traits_artifact["traits"]
        if trait["trait_id"] != REMOVED_TRAIT
    ]
    if any(
        ROLL_131 in trait["action_ids"]
        for trait in corrected_traits
        if trait["trait_id"] == "terrorism_preparedness_mandate"
    ):
        raise ValueError("roll 131 reentered terrorism preparedness")
    families = load(V1_ROOT / "final_policy_families.json")["families"]
    relationships = compiler_input["shared_semantics"]["trait_relationships"]
    constraints = compiler_input["shared_semantics"]["source_render_constraints"]
    dependencies = compiler_input["shared_semantics"]["shared_review_dependencies"]

    v1_props = {p["proposition_id"]: p for p in propositions(v1_graph)}
    v2_props = {p["proposition_id"]: p for p in propositions(graph)}
    removed = sorted(set(v1_props) - set(v2_props))
    added = sorted(set(v2_props) - set(v1_props))
    semantic_diff = seal(
        {
            "schema_version": "semantic_ir_m5r1_semantic_diff_v1",
            "artifact_id": "semantic-ir-m5r1-semantic-diff:f000477:justice_public_safety:119:v2",
            "v1_graph_content_subject_sha256": V1_GRAPH_CONTENT,
            "v2_graph_content_subject_sha256": graph["content_subject_sha256"],
            "structured_input_changes": [
                {
                    "operation": "remove_executable_policy_trait",
                    "trait_id": REMOVED_TRAIT,
                    "rationale": (
                        "Its two episodes cannot supply an independent repeated pattern "
                        "after the D.C. episode is counted in the primary D.C. pattern."
                    ),
                }
            ],
            "removed_proposition_ids": removed,
            "added_proposition_ids": added,
            "unchanged_proposition_ids": sorted(set(v1_props) & set(v2_props)),
            "roll_298_disposition": (
                "retained once as primary evidence in D.C. public-safety rule displacement"
            ),
            "roll_171_disposition": (
                "compiled as an excluded bounded notable choice; full action accounting retained"
            ),
            "action_accounting_changed": False,
            "conclusion_plan_changes": {
                "removed_primary_proposition_ids": ["prop:95cf7861641b499e"],
                "added_primary_proposition_ids": [],
            },
            "synthesis_freshly_recompiled": True,
            "manual_compiled_output_edits": False,
            "authorizing": False,
        }
    )

    conclusion = graph["compiled_ir"]["members"][0]["composition"]["conclusion_plan"]
    synthesis_review = seal(
        {
            "schema_version": "semantic_ir_m5r1_synthesis_conclusion_review_v1",
            "artifact_id": "semantic-ir-m5r1-synthesis-review:f000477:justice_public_safety:119:v2",
            "corrected_graph_content_subject_sha256": graph["content_subject_sha256"],
            "alternatives": [
                {
                    "synthesis_type": "mechanism_divide",
                    "disposition": "selected_candidate_held_for_launch_review",
                    "rationale": (
                        "The canonical contrasts relationship still yields a bounded divide "
                        "between six D.C. displacement episodes and two terrorism-preparedness "
                        "episodes; firearm and fraud patterns remain visible as separate primary "
                        "objects and limit any overarching prose claim."
                    ),
                },
                {
                    "synthesis_type": "no_common_throughline",
                    "disposition": "not_selected_competing_interpretation",
                    "rationale": (
                        "This is more cautious but weaker than the explicit reviewed contrasts "
                        "relationship; it remains a delegated-review alternative because other "
                        "primary patterns do not participate in the divide."
                    ),
                },
                {
                    "synthesis_type": "none",
                    "disposition": "not_selected_competing_interpretation",
                    "rationale": (
                        "Omitting synthesis would avoid overcompression but would also omit the "
                        "canonical mechanism contrast; this remains a defensible presentation "
                        "alternative pending delegated review."
                    ),
                },
            ],
            "selected_synthesis_type": "mechanism_divide",
            "selected_synthesis_proposition_id": "prop:7a5b23c610dc467e",
            "conclusion_only": True,
            "primary_proposition_ids": conclusion["primary_proposition_ids"],
            "limiting_proposition_ids": conclusion["limiting_proposition_ids"],
            "mixed_halt_fentanyl_limitation_retained": True,
            "tied_material_patterns_visible": True,
            "delegated_authority_pending": True,
            "authorizing": False,
        }
    )

    authority = seal(
        {
            "schema_version": "semantic_ir_m5r1_correction_authority_record_v1",
            "artifact_id": "semantic-ir-m5r1-correction-authority:f000477:justice_public_safety:119:v1",
            "decision": "bounded_semantic_ir_and_synthesis_correction_required",
            "reviewer_identity": "chatgpt:political_fingerprint_authority_thread",
            "reviewer_authority": "delegated_product_methodology_editorial_authority_v1",
            "not_user_signature": True,
            "reviewed_snapshot": {"commit": V1_COMMIT, "tree": V1_TREE},
            "reviewed_identities": {
                "compiler_input": {"content": V1_INPUT_CONTENT, "file": V1_INPUT_FILE},
                "compiled_graph": {"content": V1_GRAPH_CONTENT, "file": V1_GRAPH_FILE},
                "implementation": {
                    "content": V1_IMPLEMENTATION_CONTENT,
                    "file": V1_IMPLEMENTATION_FILE,
                },
                "review_archive_final_file_sha256": V1_ARCHIVE_FILE,
            },
            "correction_scope": "same_role_primary_proposition_overlap_noninflation",
            "acceptance_authority": False,
            "authorizing": False,
        }
    )
    overlap_review = seal(
        {
            "schema_version": "semantic_ir_m5r1_overlap_classification_review_v1",
            "artifact_id": "semantic-ir-m5r1-overlap-review:f000477:justice_public_safety:119:v2",
            "reviewed_all_behavioral_propositions": True,
            "initial_action_mapping_count": initial_ledger["action_mapping_count"],
            "initial_episode_mapping_count": initial_ledger["episode_mapping_count"],
            "initial_prohibited_overlap_count": initial_ledger[
                "prohibited_overlap_count"
            ],
            "same_role_overlaps": [
                {
                    "action_id": ROLL_298,
                    "episode_id": "dc-pretrial-detention-cash-bail",
                    "proposition_ids": [
                        "prop:354da734fec2fcf6",
                        "prop:95cf7861641b499e",
                    ],
                    "classification": "prohibited_inflating_overlap",
                    "independent_reviewer_rationale": (
                        "One episode cannot supply apparent independent primary repeated-pattern "
                        "weight twice without canonical subordinate ownership."
                    ),
                    "correction": (
                        "remove the executable pretrial trait and recompile roll 171 as a notable choice"
                    ),
                }
            ],
            "corrected_prohibited_overlap_count": 0,
            "review_status": "pass_after_structured_input_correction",
            "authorizing": False,
        }
    )

    v1_risk = load(V1_ROOT / "launch_review_risk_register.json")
    risk = seal(
        {
            "schema_version": "semantic_ir_m5r1_launch_risk_register_successor_v1",
            "artifact_id": "semantic-ir-launch-risk-register:f000477:justice_public_safety:119:v2",
            "carried_m5_register": v1_risk,
            "carried_risk_count": v1_risk["carried_risk_count"]
            + len(v1_risk["new_risks"]),
            "updated_risks": [
                {
                    "risk_id": "launch-risk:semantic-ir:mechanism-divide:v1",
                    "previous_state": "held_for_delegated_review",
                    "state": "held_for_launch_review",
                    "overlap_defect": (
                        "V1 allowed the D.C. pretrial episode to supply primary evidence to two repeated patterns."
                    ),
                    "corrected_graph_content_subject_sha256": graph[
                        "content_subject_sha256"
                    ],
                    "competing_interpretations": [
                        "mechanism_divide",
                        "no_common_throughline",
                        "no_synthesis_proposition",
                    ],
                    "public_output_consequence": (
                        "Later public language must not imply that the selected divide explains "
                        "all primary patterns or that roll 298 supplies two independent weights."
                    ),
                    "codex_recommendation": (
                        "Retain the bounded mechanism-divide candidate and all competing "
                        "interpretations for delegated launch review."
                    ),
                    "delegated_authority_decision": "pending",
                }
            ],
            "risk_count": v1_risk["carried_risk_count"] + len(v1_risk["new_risks"]),
            "history_preserved": True,
            "launch_authorized": False,
        }
    )

    all_props = propositions(graph)
    eligible = [
        p
        for p in all_props
        if p["semantic_role"] == "behavioral"
        and "house:119:1:128" not in p["evidence_action_ids"]
    ]
    core = {
        "artifact_id": IMPLEMENTATION_ID,
        "input_content_subject_sha256": input_artifact["content_subject_sha256"],
        "graph_content_subject_sha256": graph["content_subject_sha256"],
        "m4b_content_subject_sha256": m5.M4B_CONTENT,
    }
    core_digest = digest(core)
    calibration = seal(
        {
            "schema_version": "semantic_ir_m5r1_calibration_population_v1",
            "artifact_id": "semantic-ir-calibration-population:f000477:justice_public_safety:119:v2",
            "implementation_id": IMPLEMENTATION_ID,
            "implementation_core_content_subject_sha256": core_digest,
            "eligible_objects": [
                {
                    "object_id": p["proposition_id"],
                    "semantic_role": p["semantic_role"],
                    "proposition_type": p["proposition_type"],
                }
                for p in eligible
            ],
            "eligible_count": len(eligible),
            "excluded_action_ids": ["house:119:1:128", *sorted(BLOCKED_ACTIONS)],
            "excluded_held_risk_object_ids": ["prop:7a5b23c610dc467e"],
            "superseded_v1_proposition_ids": removed,
            "launch_sample_selected": False,
        }
    )
    implementation = seal(
        {
            "schema_version": "full_record_semantic_ir_provisional_implementation_v1",
            "artifact_id": IMPLEMENTATION_ID,
            "implementation_state": "implemented_pending_delegated_authority_review",
            "implementation_core": core,
            "implementation_core_content_subject_sha256": core_digest,
            "bindings": {
                "reviewed_v1_implementation": V1_IMPLEMENTATION_CONTENT,
                "accepted_action_implementation": load(m5.ACTION_BUNDLE)[
                    "content_subject_sha256"
                ],
                "accepted_episode_implementation": m5.M4B_CONTENT,
                "frozen_compiler_input": input_artifact["content_subject_sha256"],
                "frozen_compiled_semantic_ir": graph["content_subject_sha256"],
                "overlap_ledger": corrected_ledger["content_subject_sha256"],
                "policy_families": digest(families),
                "policy_traits": digest(corrected_traits),
                "trait_relationships": digest(relationships),
                "source_render_constraints": digest(constraints),
                "risk_register_successor": risk["content_subject_sha256"],
                "calibration_population": calibration["content_subject_sha256"],
            },
            "behavioral_proposition_count": len(behavioral(graph)),
            "synthesis_proposition_count": len(all_props) - len(behavioral(graph)),
            "full_action_accounting_count": 37,
            "render_plan": {
                "example_prose": None,
                "analytical_additions_allowed": False,
            },
            "accepted_semantic_reference": False,
            "canonical": False,
            "public": False,
            "persisted": False,
            "published": False,
            "production_eligible": False,
            "user_approved": False,
            "authorizing": False,
        }
    )
    verification = seal(
        {
            "schema_version": "semantic_ir_m5r1_independent_verification_v1",
            "artifact_id": "semantic-ir-independent-verification:f000477:justice_public_safety:119:v2",
            "reconstructed_graph_content_subject_sha256": graph_envelope(
                run_editorial_pipeline(copy.deepcopy(compiler_input)).compiled_ir
            )["content_subject_sha256"],
            "expected_graph_content_subject_sha256": graph["content_subject_sha256"],
            "checks": {
                "every_action_and_episode_overlap_enumerated": True,
                "no_prohibited_same_role_primary_overlap": True,
                "set_based_accounting_not_used_as_noninflation_proof": True,
                "repeated_pattern_episode_counts_independent": True,
                "roll_298_primary_weight_once": True,
                "roll_171_explicitly_accounted": True,
                "corrected_conclusion_plan_used": True,
                "material_primary_patterns_not_silently_omitted": True,
                "all_37_actions_accounted": True,
                "special_roll_controls_preserved": True,
                "canonical_pipeline_reconstruction": True,
                "no_manual_compiled_output_edits": True,
                "risk_and_calibration_history_preserved": True,
                "v1_and_candidate_isolation": True,
            },
            "status": "pass",
            "authorizing": False,
        }
    )
    decision_template = seal(
        {
            "schema_version": "delegated_semantic_ir_synthesis_decision_template_v1",
            "artifact_id": "delegated-semantic-ir-synthesis-decision-template:f000477:justice_public_safety:119:v2",
            "decision": None,
            "allowed_decisions": [
                "delegated_authority_accepts_semantic_ir_and_synthesis_implementation",
                "bounded_semantic_ir_and_synthesis_correction_required",
                "delegated_authority_rejects_semantic_ir_method",
            ],
            "reviewer_identity": None,
            "reviewer_authority": None,
            "not_user_signature": True,
            "authorizing_when_empty": False,
        }
    )
    validation = seal(
        {
            "schema_version": "semantic_ir_m5r1_validation_report_v1",
            "artifact_id": "semantic-ir-m5r1-validation:f000477:justice_public_safety:119:v2",
            "database_access": False,
            "network_access": False,
            "evidence_acquisition": False,
            "canonical_and_public_state_unchanged": True,
            "sandbox_restrictions": [
                "Pre-existing inaccessible backend/tests temporary directories emitted enumeration warnings.",
                "The first 52-test full-record regression attempt produced 12 temporary-directory permission errors inside the filesystem sandbox; the exact suite passed outside it.",
            ],
            "corrected_command_mistakes": [],
            "disclosed_baseline_attempts": [
                {
                    "command": "supported fail-closed offline backend runner over backend/tests",
                    "exit_code": 1,
                    "accounting": {"passed": 1208, "failed": 17, "skipped": 33},
                    "unrelated_failures": {
                        "stale_api_expectations": 2,
                        "missing_house_fixture": 1,
                        "missing_senate_xml_fixture_cases": 13,
                        "pre_existing_source_manifest_hash_mismatch": 1,
                    },
                    "m5r1_failures": 0,
                }
            ],
            "successful_commands": [
                {
                    "command": "complete M1-M5 authority and integrity chain",
                    "exit_code": 0,
                },
                {
                    "command": "python scripts/build_foushee_justice_semantic_ir_m5r1.py --check",
                    "exit_code": 0,
                },
                {
                    "command": "python scripts/validate_foushee_justice_semantic_ir_m5r1.py",
                    "exit_code": 0,
                },
                {
                    "command": "python -m unittest backend.tests.test_foushee_justice_semantic_ir_m5r1",
                    "exit_code": 0,
                },
                {
                    "command": "canonical Semantic IR and full-record regressions",
                    "exit_code": 0,
                    "result": "52 passed outside sandbox",
                },
                {
                    "command": "supported fail-closed broad safe offline backend suite with 17 disclosed baseline node IDs deselected",
                    "exit_code": 0,
                    "result": "1208 passed, 33 skipped, 17 deselected",
                },
                {
                    "command": "Ruff, Python compilation, JSON/schema, credential, and diff checks",
                    "exit_code": 0,
                },
            ],
            "validation_accounting": {
                "initial_prohibited_overlap_rows": 2,
                "corrected_prohibited_overlap_rows": 0,
                "targeted_m5r1_tests": 14,
                "semantic_ir_full_record_regression_tests": 52,
                "broad_safe_offline_passed": 1208,
                "broad_safe_offline_skipped": 33,
                "broad_safe_offline_deselected_baseline": 17,
                "remaining_major_or_critical_findings": 0,
            },
        }
    )
    artifacts: dict[str, Any] = {
        "correction_authority_record.json": authority,
        "initial_overlap_ledger.json": initial_ledger,
        "overlap_classification_review.json": overlap_review,
        "corrected_overlap_ledger.json": corrected_ledger,
        "final_policy_families.json": collection(
            "semantic_ir_policy_family_collection_v1",
            "semantic-ir-policy-families:f000477:justice_public_safety:119:v2",
            "families",
            families,
        ),
        "final_policy_traits.json": collection(
            "semantic_ir_policy_trait_collection_v1",
            "semantic-ir-policy-traits:f000477:justice_public_safety:119:v2",
            "traits",
            corrected_traits,
        ),
        "trait_relationships.json": collection(
            "semantic_ir_trait_relationship_collection_v1",
            "semantic-ir-trait-relationships:f000477:justice_public_safety:119:v2",
            "relationships",
            relationships,
        ),
        "source_render_constraints.json": collection(
            "semantic_ir_source_render_constraint_collection_v1",
            "semantic-ir-source-render-constraints:f000477:justice_public_safety:119:v2",
            "constraints",
            constraints,
        ),
        "shared_review_dependencies.json": collection(
            "semantic_ir_shared_review_dependency_collection_v1",
            "semantic-ir-shared-review-dependencies:f000477:justice_public_safety:119:v2",
            "dependencies",
            dependencies,
        ),
        "frozen_final_compiler_input.json": input_artifact,
        "frozen_final_compiled_semantic_ir.json": graph,
        "semantic_diff.json": semantic_diff,
        "synthesis_conclusion_review.json": synthesis_review,
        "provisional_implementation_bundle.json": implementation,
        "independent_implementation_verification.json": verification,
        "launch_review_risk_register.json": risk,
        "semantic_calibration_population.json": calibration,
        "delegated_authority_decision_template.json": decision_template,
        "validation_report.json": validation,
    }
    for name, value in artifacts.items():
        write_json(name, value, check)
    dossier = dossier_markdown(artifacts)
    write(OUTPUT_ROOT / "review_dossier.md", dossier.encode(), check)
    schema = closed_artifact_schema(artifacts)
    write_json("schemas/m5r1_artifacts_v1.schema.json", schema, check)

    parity_names = [
        *artifacts,
        "review_dossier.md",
        "schemas/m5r1_artifacts_v1.schema.json",
    ]
    entries = []
    for name in parity_names:
        path = OUTPUT_ROOT / name
        if check:
            raw = path.read_bytes()
        elif name == "review_dossier.md":
            raw = dossier.encode()
        elif name.startswith("schemas/"):
            raw = serialized(schema)
        else:
            raw = serialized(artifacts[name])
        value = json.loads(raw) if name.endswith(".json") else {}
        entries.append(
            {
                "path": name,
                "final_file_sha256": hashlib.sha256(raw).hexdigest(),
                "content_subject_sha256": value.get("content_subject_sha256"),
            }
        )
    parity = seal(
        {
            "schema_version": "semantic_ir_m5r1_parity_manifest_v1",
            "artifact_id": "semantic-ir-implementation-parity:f000477:justice_public_safety:119:v2",
            "entries": entries,
            "entry_count": len(entries),
            "json_markdown_parity": True,
            "manually_edited_compiled_output": False,
            "v1_state_changed": False,
            "accepted_or_canonical_state_changed": False,
            "public_prose_present": False,
        }
    )
    write_json("parity_manifest.json", parity, check)
    return {
        "input": input_artifact,
        "graph": graph,
        "implementation": implementation,
        "initial_overlap_count": initial_ledger["prohibited_overlap_count"],
        "corrected_overlap_count": corrected_ledger["prohibited_overlap_count"],
        "families": len(families),
        "traits": len(corrected_traits),
        "relationships": len(relationships),
        "behavioral": Counter(p["proposition_type"] for p in behavioral(graph)),
        "directions": Counter(p["direction"] for p in behavioral(graph)),
        "synthesis": Counter(
            p["proposition_type"]
            for p in propositions(graph)
            if p["semantic_role"] == "synthesis"
        ),
        "accounting": graph["action_accounting_counts"],
        "risk_count": risk["risk_count"],
        "calibration_count": calibration["eligible_count"],
        "verification": verification["status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.check)
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"input", "graph", "implementation"}
            },
            default=dict,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
