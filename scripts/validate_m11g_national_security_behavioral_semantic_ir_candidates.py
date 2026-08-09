"""Independent validation for the detached M11G candidate package."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import (  # noqa: E402
    SemanticCompilerInputError,
    compile_behavioral_candidate_ir,
)
from backend.scripts.build_m11g_national_security_behavioral_semantic_ir_candidates import (  # noqa: E402
    DECISION_PATH,
    DOSSIER_PATH,
    GRAPH_PATH,
    IMPLEMENTATION_PATH,
    M11F_IMPLEMENTATION,
    PARITY_PATH,
    POST_M11F_MERGE_MAIN,
    build,
    build_input,
    digest,
    file_digest,
    load,
    preflight,
)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def expect_rejected(payload: dict, message: str) -> None:
    try:
        compile_behavioral_candidate_ir(payload)
    except (SemanticCompilerInputError, KeyError):
        return
    raise ValueError(message)


def validate() -> dict[str, object]:
    build(True)
    implementation = preflight()
    compiler_input, relationships = build_input(implementation)
    graph_artifact = load(GRAPH_PATH)
    graph_schema = load(
        ROOT
        / "docs/methodology/full_record_behavioral_semantic_ir_candidate_package_v1.schema.json"
    )
    decision_schema = load(
        ROOT
        / "docs/methodology/full_record_behavioral_semantic_ir_human_decision_v1.schema.json"
    )
    Draft7Validator(graph_schema).validate(graph_artifact)
    graph = graph_artifact["compiled_candidate_ir"]
    require(
        compile_behavioral_candidate_ir(compiler_input) == graph,
        "independent compilation differs",
    )
    require(
        file_digest(IMPLEMENTATION_PATH) == M11F_IMPLEMENTATION["file_sha256"],
        "M11F implementation changed",
    )
    require(
        graph_artifact["base_binding"]["post_m11f_merge_main"] == POST_M11F_MERGE_MAIN,
        "post-M11F base differs",
    )
    require(
        digest(
            {
                key: value
                for key, value in graph_artifact.items()
                if key != "candidate_subject_sha256"
            }
        )
        == graph_artifact["candidate_subject_sha256"],
        "candidate subject digest differs",
    )

    episodes = {
        row["episode_id"]: row
        for row in implementation["subject"]["implementation_records"]
    }
    require(len(episodes) == 81, "M11F episode count differs")
    require(
        len(graph["episode_accounting"]) == 81
        and {row["episode_id"] for row in graph["episode_accounting"]} == set(episodes),
        "complete episode accounting differs",
    )
    propositions = graph["proposition_graph"]["propositions"]
    require(
        len(propositions) == 4
        and {row["proposition_type"] for row in propositions} == {"repeated_pattern"},
        "bounded proposition set differs",
    )
    require(
        all(len(row["evidence_episode_ids"]) >= 2 for row in propositions),
        "repeated-pattern minimum differs",
    )
    require(not graph["synthesis_propositions"], "synthesis leaked into M11G")
    require(
        all(value is False for value in graph["downstream_authorizations"].values()),
        "downstream authority leaked",
    )
    require(
        graph_artifact["blocked_action_ids"] == ["house:119:2:278"],
        "blocked action binding differs",
    )
    require(
        not any(
            "house:119:2:278" in row["evidence_action_ids"] for row in propositions
        ),
        "blocked action entered proposition evidence",
    )
    require(
        len(graph_artifact["episode_evidence_ledger"]) == 81,
        "episode evidence ledger differs",
    )

    owners: dict[str, list[str]] = {}
    for proposition in propositions:
        for episode_id in proposition["evidence_episode_ids"]:
            owners.setdefault(episode_id, []).append(proposition["proposition_id"])
        derived = sorted(
            action_id
            for episode_id in proposition["evidence_episode_ids"]
            for action_id in episodes[episode_id]["primary_action_ids"]
        )
        require(
            derived == proposition["evidence_action_ids"],
            "action lineage differs from episode lineage",
        )
    require(
        all(len(value) == 1 for value in owners.values()),
        "primary evidence inflation detected",
    )
    require(
        set(owners)
        == {
            episode_id
            for relationship in relationships
            for episode_id in relationship["replacement_primary_episode_ids"]
        },
        "four relationship dispositions differ",
    )
    require(
        all(
            row["source_relationship_binding"]["inherited_authority"] is False
            for row in propositions
        ),
        "relationship hint gained authority",
    )

    # Generic adversarial checks.
    changed = copy.deepcopy(compiler_input)
    changed["proposition_candidates"][0]["evidence_episode_ids"] = changed[
        "proposition_candidates"
    ][0]["evidence_episode_ids"][:1]
    expect_rejected(changed, "one-episode repeated pattern was accepted")
    changed = copy.deepcopy(compiler_input)
    changed["proposition_candidates"][0]["direction"] = "support"
    expect_rejected(
        changed, "raw or supplied direction overrode accepted episode directions"
    )
    changed = copy.deepcopy(compiler_input)
    changed["proposition_candidates"][0]["evidence_episode_ids"].append(
        "single-119-hr-8595-2-247"
    )
    expect_rejected(changed, "same-topic unsupported grouping was accepted")
    changed = copy.deepcopy(compiler_input)
    changed["proposition_candidates"].append(
        {
            "proposition_id": "bad-overlap",
            "proposition_type": "notable_choice",
            "proposition": "bad",
            "direction": "opposition",
            "rationale": "bad",
            "material_limitations": [],
            "competing_interpretations": [],
            "overlap_relationships": [],
            "trajectory_change": None,
            "source_relationship_id": "none",
            "evidence_episode_ids": [
                compiler_input["proposition_candidates"][0]["evidence_episode_ids"][0]
            ],
            "source_relationship_binding": {"inherited_authority": False},
        }
    )
    expect_rejected(changed, "undeclared overlap was accepted")
    changed = copy.deepcopy(compiler_input)
    changed["proposition_candidates"].append(
        {
            "proposition_id": "bad-trajectory",
            "proposition_type": "trajectory",
            "proposition": "dates only",
            "direction": "opposition",
            "rationale": "dates only",
            "material_limitations": [],
            "competing_interpretations": [],
            "overlap_relationships": [],
            "trajectory_change": None,
            "source_relationship_id": "none",
            "evidence_episode_ids": [
                "single-119-hr-3838-1-262",
                "single-119-s-1071-1-320",
            ],
            "source_relationship_binding": {"inherited_authority": False},
        }
    )
    expect_rejected(changed, "date-only trajectory was accepted")

    parity = load(PARITY_PATH)
    for entry in parity["entries"]:
        path = GRAPH_PATH.parent / entry["path"]
        require(
            file_digest(path) == entry["file_sha256"],
            f"stale parity digest: {entry['path']}",
        )
    decision = load(DECISION_PATH)
    Draft7Validator(decision_schema).validate(decision)
    require(
        decision["authorizing"] is False
        and all(row["decision"] is None for row in decision["decisions"]),
        "decision template is not empty/non-authorizing",
    )
    dossier = DOSSIER_PATH.read_text(encoding="utf-8")
    require(
        "Proposed repeated patterns: 4" in dossier
        and "retained as limits or contrasts: 39" in dossier
        and "retained without a safe higher-level proposition: 31" in dossier,
        "dossier parity differs",
    )
    state = load(ROOT / "docs/editorial/current_state_index.json")[
        "active_behavioral_semantic_ir_candidate_milestone"
    ]
    require(
        state["post_m11f_merge_base"] == POST_M11F_MERGE_MAIN
        and state["candidate_identity"]["candidate_subject_sha256"]
        == graph_artifact["candidate_subject_sha256"]
        and state["milestone_state"] == "complete_pending_human_substantive_review",
        "canonical current state differs",
    )
    return {
        "status": "pass",
        "episode_count": 81,
        "proposition_counts": {
            "notable_choice": 0,
            "repeated_pattern": 4,
            "trajectory": 0,
        },
        "proposition_episode_count": len(owners),
        "unused_episode_count": 81 - len(owners),
        "limit_or_contrast_episode_count": 39,
        "no_safe_proposition_episode_count": 31,
        "blocked_action_ids": ["house:119:2:278"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
