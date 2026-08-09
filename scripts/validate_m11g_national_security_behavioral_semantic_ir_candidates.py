"""Independent validation for the detached M11G candidate package."""

from __future__ import annotations

import copy
from collections import Counter
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


EXPECTED_CANDIDATE_EPISODES = {
    "pattern-fisa-title-vii-extension-opposition": [
        "single-119-s-4465-2-155",
        "single-119-hr-9238-2-221",
    ],
    "pattern-iran-war-powers-removal-support": [
        "single-119-hconres-38-2-85",
        "single-119-hconres-40-2-114",
        "single-119-hconres-75-2-170",
        "single-119-hconres-86-2-199",
        "single-119-hconres-89-2-282",
    ],
    "pattern-lebanon-war-powers-removal-support": [
        "single-119-hconres-84-2-201",
        "single-119-hconres-108-2-232",
    ],
    "pattern-venezuela-war-powers-removal-support": [
        "single-119-hconres-64-1-346",
        "single-119-hconres-68-2-48",
    ],
    "pattern-terrorism-preparedness-support": [
        "single-119-hr-1608-1-286",
        "single-119-hr-3106-2-234",
    ],
    "pattern-ukraine-assistance-mixed": [
        "single-119-hamdt-57-1-209",
        "single-119-hamdt-93-1-255",
        "single-119-hamdt-252-2-264",
        "single-119-hr-2913-2-207",
    ],
    "pattern-jordan-assistance-restriction-opposition": [
        "single-119-hamdt-56-1-208",
        "single-119-hamdt-236-2-244",
    ],
    "pattern-military-dod-sex-gender-restriction-opposition": [
        "single-119-hamdt-86-1-246",
        "single-119-hamdt-88-1-248",
        "single-119-hamdt-89-1-249",
        "single-119-hamdt-254-2-266",
        "single-119-hamdt-256-2-268",
    ],
    "trajectory-milcon-va-appropriations-direction-change": [
        "single-119-hr-3944-1-182",
        "single-119-hr-8469-2-175",
    ],
    "notable-israel-foreign-military-financing-reduction": [
        "single-119-hamdt-235-2-243"
    ],
    "notable-aumf-repeal-1991-2002": ["single-119-hamdt-99-1-244"],
    "notable-international-criminal-court-sanctions-opposition": [
        "single-119-hr-23-1-7"
    ],
    "notable-taiwan-security-cooperation-funding": ["single-119-hamdt-95-1-257"],
    "notable-haiti-temporary-protected-status": ["single-119-hr-1689-2-120"],
    "notable-fy2026-ndaa-package-opposition": ["single-119-s-1071-1-320"],
}


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
    proposition_counts = Counter(row["proposition_type"] for row in propositions)
    require(
        len(propositions) == 15
        and proposition_counts
        == {"repeated_pattern": 8, "trajectory": 1, "notable_choice": 6},
        "bounded proposition set differs",
    )
    require(
        {row["proposition_id"]: row["evidence_episode_ids"] for row in propositions}
        == EXPECTED_CANDIDATE_EPISODES,
        "exact corrected candidate/evidence set differs",
    )
    require(
        all(
            len(row["evidence_episode_ids"]) >= 2
            for row in propositions
            if row["proposition_type"] == "repeated_pattern"
        ),
        "repeated-pattern minimum differs",
    )
    require(
        all(
            len(row["evidence_episode_ids"]) == 1
            for row in propositions
            if row["proposition_type"] == "notable_choice"
        ),
        "notable-choice episode boundary differs",
    )
    require(not graph["synthesis_propositions"], "synthesis leaked into M11G")
    require(
        graph_artifact["public_wording_included"] is False
        and graph_artifact["accepted_semantic_ir"] is False
        and graph_artifact["canonical_semantic_ir"] is False
        and graph_artifact["authorizing"] is False,
        "candidate/public/acceptance authority leaked",
    )
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
        {
            episode_id
            for relationship in relationships
            for episode_id in relationship["replacement_primary_episode_ids"]
        }
        <= set(owners),
        "four relationship dispositions differ",
    )
    require(
        all(
            row["source_relationship_binding"]["inherited_authority"] is False
            for row in propositions
        ),
        "relationship hint gained authority",
    )
    accounting_counts = Counter(
        row["disposition"] for row in graph["episode_accounting"]
    )
    require(
        accounting_counts
        == {
            "supports_proposed_repeated_pattern": 24,
            "supports_proposed_trajectory": 2,
            "supports_proposed_notable_choice": 6,
            "retained_as_limit_or_contrast": 24,
            "no_safe_higher_level_behavioral_proposition": 25,
        },
        "corrected primary episode accounting differs",
    )
    trajectory = next(
        row for row in propositions if row["proposition_type"] == "trajectory"
    )
    require(
        trajectory["direction"] == "mixed"
        and trajectory["conclusion_relevance"] == "limiting"
        and trajectory["trajectory_change"]["change_type"] == "direction_change",
        "structured trajectory differs",
    )
    fisa = next(
        row
        for row in propositions
        if row["proposition_id"] == "pattern-fisa-title-vii-extension-opposition"
    )
    require(
        "stated purpose included extending" in fisa["proposition"]
        and any("complete measures" in value for value in fisa["material_limitations"]),
        "FISA whole-measure boundary differs",
    )
    ukraine = next(
        row
        for row in propositions
        if row["proposition_id"] == "pattern-ukraine-assistance-mixed"
    )
    require(
        ukraine["direction"] == "mixed"
        and any("whole measure" in value for value in ukraine["material_limitations"]),
        "Ukraine mixed/package boundary differs",
    )
    ndaa = next(
        row
        for row in propositions
        if row["proposition_id"] == "notable-fy2026-ndaa-package-opposition"
    )
    require(
        any("whole-package choice" in value for value in ndaa["material_limitations"]),
        "NDAA component-inference boundary differs",
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
    require(
        {row["proposition_id"] for row in decision["decisions"]}
        == {row["proposition_id"] for row in propositions}
        and len(decision["decisions"]) == 15,
        "decision template candidate set differs",
    )
    dossier = DOSSIER_PATH.read_text(encoding="utf-8")
    require(
        "Proposed repeated patterns: 8" in dossier
        and "Proposed notable choices: 6" in dossier
        and "Proposed trajectories: 1" in dossier
        and "retained as limits or contrasts: 24" in dossier
        and "retained without a safe higher-level proposition: 25" in dossier,
        "dossier parity differs",
    )
    state = load(ROOT / "docs/editorial/current_state_index.json")[
        "active_behavioral_semantic_ir_candidate_milestone"
    ]
    require(
        state["post_m11f_merge_base"] == POST_M11F_MERGE_MAIN
        and state["candidate_identity"]["candidate_subject_sha256"]
        == graph_artifact["candidate_subject_sha256"]
        and state["milestone_state"] == "completed_human_reviewed_accepted"
        and state["accepted_head"] == "8ef00da6c0d92662c887874d015024a5b038d66a"
        and state["post_merge_main"] == "8bd2ec2da7c5da6828c28217cc035c651c7c6f76",
        "canonical current state differs",
    )
    return {
        "status": "pass",
        "episode_count": 81,
        "proposition_counts": dict(proposition_counts),
        "proposition_episode_count": len(owners),
        "unused_episode_count": 81 - len(owners),
        "limit_or_contrast_episode_count": 24,
        "no_safe_proposition_episode_count": 25,
        "blocked_action_ids": ["house:119:2:278"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
