"""Independent fail-closed validation for the M5-R1/V2 correction."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import compile_semantic_ir  # noqa: E402
from backend.app.semantic_ir.pipeline import run_editorial_pipeline  # noqa: E402
from backend.app.semantic_ir.validation import validate_compiled_ir  # noqa: E402
from scripts.build_foushee_justice_semantic_ir_m5r1 import (  # noqa: E402
    BLOCKED_ACTIONS,
    OUTPUT_ROOT,
    ROLL_131,
    ROLL_171,
    ROLL_298,
    V1_GRAPH_CONTENT,
    V1_GRAPH_FILE,
    V1_IMPLEMENTATION_CONTENT,
    V1_IMPLEMENTATION_FILE,
    V1_INPUT_CONTENT,
    V1_INPUT_FILE,
    V1_ROOT,
    build,
    digest,
    file_digest,
    graph_envelope,
    load,
)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def graph_propositions(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return graph["compiled_ir"]["members"][0]["proposition_graph"]["propositions"]


def independent_overlap_maps(
    graph: dict[str, Any], compiler_input: dict[str, Any]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    action_map: dict[str, list[str]] = {
        action["action_id"]: []
        for action in compiler_input["shared_semantics"]["actions"]
    }
    episode_map: dict[str, list[str]] = {
        episode["episode_id"]: []
        for episode in compiler_input["shared_semantics"]["episodes"]
    }
    for proposition in graph_propositions(graph):
        if proposition["semantic_role"] != "behavioral":
            continue
        for action_id in proposition["evidence_action_ids"]:
            action_map[action_id].append(proposition["proposition_id"])
        for episode_id in proposition["evidence_episode_ids"]:
            episode_map[episode_id].append(proposition["proposition_id"])
    return action_map, episode_map


def validate_no_inflating_primary_overlap(graph: dict[str, Any]) -> None:
    member = graph["compiled_ir"]["members"][0]
    props = {
        proposition["proposition_id"]: proposition
        for proposition in member["proposition_graph"]["propositions"]
        if proposition["semantic_role"] == "behavioral"
    }
    primary_ids = set(
        member["composition"]["conclusion_plan"]["primary_proposition_ids"]
    )
    for proposition_id in primary_ids:
        require(
            proposition_id in props
            or any(
                p["proposition_id"] == proposition_id
                and p["semantic_role"] == "synthesis"
                for p in member["proposition_graph"]["propositions"]
            ),
            "conclusion plan has a missing primary proposition",
        )
    for key in ("evidence_action_ids", "evidence_episode_ids"):
        owners: dict[str, list[str]] = defaultdict(list)
        for proposition_id, proposition in props.items():
            for evidence_id in proposition[key]:
                owners[evidence_id].append(proposition_id)
        for evidence_id, proposition_ids in owners.items():
            if len(proposition_ids) == 1:
                continue
            primary_owners = [
                proposition_id
                for proposition_id in proposition_ids
                if proposition_id in primary_ids
            ]
            same_primary_type = (
                len(primary_owners) > 1
                and len(
                    {
                        props[proposition_id]["proposition_type"]
                        for proposition_id in primary_owners
                    }
                )
                == 1
            )
            require(
                False,
                (
                    "prohibited primary same-type overlap: "
                    if same_primary_type
                    else "unvalidated behavioral overlap: "
                )
                + evidence_id,
            )


def validate_semantic_invariants(
    graph: dict[str, Any], compiler_input: dict[str, Any]
) -> None:
    validate_no_inflating_primary_overlap(graph)
    member = graph["compiled_ir"]["members"][0]
    propositions = graph_propositions(graph)
    behavioral = [p for p in propositions if p["semantic_role"] == "behavioral"]
    primary_ids = set(
        member["composition"]["conclusion_plan"]["primary_proposition_ids"]
    )

    accounting = graph["full_universe_action_accounting"]
    require(
        len(accounting) == 37 and len({row["action_id"] for row in accounting}) == 37,
        "complete 37-action accounting differs",
    )
    require(
        any(row["action_id"] == ROLL_171 for row in accounting), "roll 171 disappeared"
    )
    roll298 = [p for p in behavioral if ROLL_298 in p["evidence_action_ids"]]
    require(
        len(roll298) == 1
        and roll298[0]["proposition_type"] == "repeated_pattern"
        and roll298[0]["proposition_id"] in primary_ids,
        "roll 298 primary evidence ownership differs",
    )
    roll171 = [p for p in behavioral if ROLL_171 in p["evidence_action_ids"]]
    require(
        len(roll171) == 1
        and roll171[0]["proposition_type"] == "notable_choice"
        and roll171[0]["conclusion_relevance"] == "excluded",
        "roll 171 notable-choice accounting differs",
    )
    for blocked in BLOCKED_ACTIONS:
        require(
            not any(blocked in p["evidence_action_ids"] for p in propositions),
            f"{blocked} entered proposition support",
        )
    traits = compiler_input["shared_semantics"]["policy_traits"]
    terrorism = next(
        trait
        for trait in traits
        if trait["trait_id"] == "terrorism_preparedness_mandate"
    )
    require(
        ROLL_131 not in terrorism["action_ids"],
        "roll 131 reentered terrorism preparedness",
    )
    require(
        not any(trait["trait_id"] == "pretrial_release_regulation" for trait in traits),
        "superseded pretrial trait remains executable",
    )
    for proposition in behavioral:
        if proposition["proposition_type"] == "repeated_pattern":
            require(
                len(set(proposition["evidence_episode_ids"]))
                == len(proposition["evidence_episode_ids"])
                and len(proposition["evidence_episode_ids"]) >= 2,
                f"{proposition['proposition_id']} independent episode count differs",
            )
    all_ids = {p["proposition_id"] for p in propositions}
    for proposition in propositions:
        if proposition["semantic_role"] == "synthesis":
            require(
                set(proposition["relationships"]["supported_by"]) <= all_ids,
                "stale synthesis support identity",
            )
            require(
                set(proposition["relationships"]["limited_by"]) <= all_ids,
                "stale synthesis limiting identity",
            )
    require(
        graph["render_plan"]
        == {"example_prose": None, "analytical_additions_allowed": False},
        "render plan differs",
    )


def validate_reconstruction(
    graph: dict[str, Any], compiler_input: dict[str, Any]
) -> None:
    compiled = compile_semantic_ir(copy.deepcopy(compiler_input))
    require(compiled == graph["compiled_ir"], "manual or stale compiled output")
    require(
        run_editorial_pipeline(copy.deepcopy(compiler_input)).compiled_ir == compiled,
        "canonical pipeline output differs",
    )
    validate_compiled_ir(compiled)
    require(
        graph_envelope(compiled)["content_subject_sha256"]
        == graph["content_subject_sha256"],
        "graph envelope digest differs",
    )


def validate_parity(parity: dict[str, Any]) -> None:
    for entry in parity["entries"]:
        path = OUTPUT_ROOT / entry["path"]
        require(path.is_file(), f"missing parity path: {entry['path']}")
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == entry["final_file_sha256"],
            f"stale parity file digest: {entry['path']}",
        )
        if entry["content_subject_sha256"]:
            value = load(path)
            subject = {
                key: child
                for key, child in value.items()
                if key != "content_subject_sha256"
            }
            require(
                digest(subject) == entry["content_subject_sha256"],
                f"stale parity content digest: {entry['path']}",
            )


def validate() -> dict[str, object]:
    expected = build(True)
    input_artifact = load(OUTPUT_ROOT / "frozen_final_compiler_input.json")
    graph = load(OUTPUT_ROOT / "frozen_final_compiled_semantic_ir.json")
    compiler_input = input_artifact["compiler_input"]
    initial_ledger = load(OUTPUT_ROOT / "initial_overlap_ledger.json")
    corrected_ledger = load(OUTPUT_ROOT / "corrected_overlap_ledger.json")
    implementation = load(OUTPUT_ROOT / "provisional_implementation_bundle.json")
    verification = load(OUTPUT_ROOT / "independent_implementation_verification.json")

    require(
        load(V1_ROOT / "frozen_final_compiler_input.json")["content_subject_sha256"]
        == V1_INPUT_CONTENT
        and file_digest(V1_ROOT / "frozen_final_compiler_input.json") == V1_INPUT_FILE
        and load(V1_ROOT / "frozen_final_compiled_semantic_ir.json")[
            "content_subject_sha256"
        ]
        == V1_GRAPH_CONTENT
        and file_digest(V1_ROOT / "frozen_final_compiled_semantic_ir.json")
        == V1_GRAPH_FILE
        and load(V1_ROOT / "provisional_implementation_bundle.json")[
            "content_subject_sha256"
        ]
        == V1_IMPLEMENTATION_CONTENT
        and file_digest(V1_ROOT / "provisional_implementation_bundle.json")
        == V1_IMPLEMENTATION_FILE,
        "M5 V1 bytes changed",
    )
    validate_reconstruction(graph, compiler_input)
    validate_semantic_invariants(graph, compiler_input)

    initial_actions, initial_episodes = independent_overlap_maps(
        load(V1_ROOT / "frozen_final_compiled_semantic_ir.json"),
        load(V1_ROOT / "frozen_final_compiler_input.json")["compiler_input"],
    )
    corrected_actions, corrected_episodes = independent_overlap_maps(
        graph, compiler_input
    )
    require(
        len(initial_ledger["action_mappings"]) == len(initial_actions) == 37
        and len(initial_ledger["episode_mappings"]) == len(initial_episodes) == 32,
        "initial overlap ledger completeness differs",
    )
    require(
        len(corrected_ledger["action_mappings"]) == len(corrected_actions) == 37
        and len(corrected_ledger["episode_mappings"]) == len(corrected_episodes) == 32,
        "corrected overlap ledger completeness differs",
    )
    require(
        initial_ledger["prohibited_overlap_count"] == 2
        and corrected_ledger["prohibited_overlap_count"] == 0,
        "overlap correction accounting differs",
    )
    for row in corrected_ledger["action_mappings"]:
        require(
            sorted(ref["proposition_id"] for ref in row["references"])
            == sorted(corrected_actions[row["action_id"]]),
            f"stale action overlap mapping: {row['action_id']}",
        )
    for row in corrected_ledger["episode_mappings"]:
        require(
            sorted(ref["proposition_id"] for ref in row["references"])
            == sorted(corrected_episodes[row["episode_id"]]),
            f"stale episode overlap mapping: {row['episode_id']}",
        )

    schema = load(OUTPUT_ROOT / "schemas/m5r1_artifacts_v1.schema.json")
    Draft7Validator.check_schema(schema)
    validator = Draft7Validator(schema)
    for path in OUTPUT_ROOT.glob("*.json"):
        if path.name == "parity_manifest.json":
            continue
        require(
            not list(validator.iter_errors(load(path))),
            f"closed schema validation differs: {path.name}",
        )
    validate_parity(load(OUTPUT_ROOT / "parity_manifest.json"))
    dossier = (OUTPUT_ROOT / "review_dossier.md").read_text(encoding="utf-8")
    require(
        "Initial prohibited overlap rows: 2" in dossier
        and "Corrected prohibited overlap rows: 0" in dossier
        and ROLL_171 in dossier
        and ROLL_298 in dossier,
        "JSON-Markdown parity differs",
    )
    require(
        verification["status"] == "pass" and all(verification["checks"].values()),
        "independent verification artifact differs",
    )
    require(
        implementation["implementation_state"]
        == "implemented_pending_delegated_authority_review"
        and all(
            implementation[key] is False
            for key in (
                "accepted_semantic_reference",
                "canonical",
                "public",
                "persisted",
                "published",
                "production_eligible",
                "user_approved",
                "authorizing",
            )
        ),
        "candidate isolation differs",
    )
    return {
        "status": "pass",
        "initial_prohibited_overlap_rows": 2,
        "corrected_prohibited_overlap_rows": 0,
        "families": expected["families"],
        "traits": expected["traits"],
        "behavioral": expected["behavioral"],
        "directions": expected["directions"],
        "synthesis": expected["synthesis"],
        "accounting": expected["accounting"],
        "risk_count": expected["risk_count"],
        "calibration_count": expected["calibration_count"],
        "independent_verification": expected["verification"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), default=dict, sort_keys=True))
