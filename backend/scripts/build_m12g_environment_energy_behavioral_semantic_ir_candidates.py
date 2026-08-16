"""Build detached M12G Environment & Energy behavioral Semantic IR candidates."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.compiler import compile_behavioral_candidate_ir  # noqa: E402
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)


POST_M12E_MERGE_MAIN = "450a759c5a2d0eaf767e68bc999c7d3ec8e9ca1e"
M12F_AUTHORITY = {
    "artifact_id": "human-policy-episode-authority:f000477:environment_energy:119:v1",
    "file_sha256": "fc25868d77a1bb7091d4556b566da6819659e5cb756dc29c89bafa66711cfbff",
    "authority_subject_sha256": "4c678975138f16380eb7df853a71a7024e1f8a49e42c4d8c9399819949b013fa",
}
M12F_IMPLEMENTATION = {
    "artifact_id": "policy-episode-decision-implementation:f000477:environment_energy:119:v1",
    "file_sha256": "ab2bc01875239e65a5224dbc4b718e18b9a301b304f78ff642b97f2f33be039d",
    "implementation_subject_sha256": "0ee66969a8d2514cce322d6ed437119cc2b1612fb53092cc0754e0ba2a2637d2",
}
M12F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_environment_energy_119_v1"
)
AUTHORITY_PATH = M12F_ROOT / "human_policy_episode_authority.json"
IMPLEMENTATION_PATH = M12F_ROOT / "episode_decision_implementation_bundle.json"
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_environment_energy_119_v1"
)
GRAPH_PATH = OUTPUT_ROOT / "behavioral_semantic_ir_candidate_graph.json"
DECISION_PATH = OUTPUT_ROOT / "human_behavioral_semantic_ir_decision_template.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
GRAPH_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_candidate_package_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_behavioral_semantic_ir_human_decision_v1.schema.json"
)
GRAPH_ID = "behavioral-semantic-ir-candidates:f000477:environment_energy:119:v1"
DECISION_ID = (
    "behavioral-semantic-ir-human-decision-template:f000477:environment_energy:119:v1"
)

INSUFFICIENT_BASES = [
    "shared_topic",
    "shared_agency",
    "shared_statute",
    "shared_cra_mechanism",
    "shared_vote_direction",
    "party",
    "sponsor",
    "ideology",
]

PROPOSITIONS = [
    {
        "proposition_id": "pattern-california-vehicle-emissions-waiver-disapproval-opposition",
        "proposition_type": "repeated_pattern",
        "proposition": (
            "Across two separate resolutions, Foushee opposed congressional "
            "disapproval of two distinct EPA California vehicle-emissions "
            "waiver-of-preemption decisions."
        ),
        "direction": "opposition",
        "evidence_episode_ids": [
            "single-119-hjres-89-1-112",
            "single-119-hjres-88-1-114",
        ],
        "rationale": (
            "Both accepted meanings concern the same bounded congressional choice: "
            "whether to disapprove an EPA California vehicle-emissions waiver-of-"
            "preemption decision; both accepted directions oppose disapproval."
        ),
        "material_limitations": [
            "H.J.Res. 88 and H.J.Res. 89 concern distinct waiver decisions and distinct emissions standards.",
            "Opposition to congressional disapproval does not establish unrestricted support for every aspect of either underlying rule or waiver decision.",
        ],
        "competing_interpretations": [
            "Keep the resolutions only as separate episodes because the underlying California standards and waiver decisions differ."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [],
        "trajectory_change": None,
        "conclusion_relevance": "primary",
    },
    {
        "proposition_id": "pattern-doe-appliance-efficiency-rule-disapproval-opposition",
        "proposition_type": "repeated_pattern",
        "proposition": (
            "Across four separate resolutions, Foushee opposed congressional "
            "disapproval of distinct Department of Energy appliance or commercial-"
            "equipment energy-conservation standards, certification, labeling, or "
            "enforcement rules."
        ),
        "direction": "opposition",
        "evidence_episode_ids": [
            "single-119-hjres-20-1-53",
            "single-119-hjres-42-1-59",
            "single-119-hjres-24-1-77",
            "single-119-hjres-75-1-78",
        ],
        "rationale": (
            "Each accepted meaning states a congressional-disapproval choice over a "
            "DOE energy-conservation rule governing appliances or commercial "
            "equipment, and every accepted direction opposes disapproval."
        ),
        "material_limitations": [
            "The four resolutions concern different products and different regulatory functions, including standards, certification, labeling, and enforcement.",
            "The pattern is limited to the disapproval choices and does not establish general support for regulation or for every underlying requirement.",
        ],
        "competing_interpretations": [
            "Treat the product and regulatory-function differences as too material for one repeated pattern."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": [
                    "single-119-hr-5184-2-12",
                    "single-119-hr-4593-2-23",
                    "single-119-hr-4626-2-76",
                    "single-119-hr-4758-2-78",
                ],
                "reason": "These related energy-efficiency measures use different statutory choices rather than congressional disapproval of the four identified rules.",
            }
        ],
        "trajectory_change": None,
        "conclusion_relevance": "primary",
    },
    {
        "proposition_id": "pattern-blm-land-decision-disapproval-opposition",
        "proposition_type": "repeated_pattern",
        "proposition": (
            "Across seven separate resolutions, Foushee opposed congressional "
            "disapproval of distinct Bureau of Land Management land-management, "
            "leasing, activity-plan, or withdrawal decisions."
        ),
        "direction": "opposition",
        "evidence_episode_ids": [
            "single-119-hjres-104-1-224",
            "single-119-hjres-106-1-225",
            "single-119-hjres-105-1-226",
            "single-119-hjres-130-1-294",
            "single-119-hjres-131-1-295",
            "single-119-sjres-80-1-296",
            "single-119-hjres-140-2-38",
        ],
        "rationale": (
            "Every accepted meaning states a congressional-disapproval choice over "
            "a distinct BLM land-management, leasing, activity-plan, or withdrawal "
            "decision, and every accepted direction opposes disapproval."
        ),
        "material_limitations": [
            "Each resolution concerns a separate geographic area and distinct plan, amendment, leasing decision, activity plan, or withdrawal order.",
            "Opposition to disapproval does not establish support for every component of every underlying BLM decision.",
        ],
        "competing_interpretations": [
            "Retain only the seven separate episodes because their geographies and operative land decisions differ materially."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": ["single-119-hjres-60-1-110"],
                "reason": "The National Park Service motor-vehicle rule is a different agency, land unit, and regulatory choice.",
            }
        ],
        "trajectory_change": None,
        "conclusion_relevance": "primary",
    },
]

CONTRAST_ACTIONS = {
    "other-distinct-cra-rules": {
        "house:119:1:52",
        "house:119:1:58",
        "house:119:1:61",
        "house:119:1:110",
        "house:119:1:143",
    },
    "other-appliance-efficiency-choices": {
        "house:119:2:12",
        "house:119:2:23",
        "house:119:2:76",
        "house:119:2:78",
    },
    "distinct-electricity-reliability-proposals": {
        "house:119:1:279",
        "house:119:1:323",
        "house:119:1:324",
        "house:119:1:342",
        "house:119:1:347",
    },
    "distinct-clean-air-act-choices": {
        "house:119:2:116",
        "house:119:2:118",
        "house:119:2:136",
        "house:119:2:164",
    },
    "distinct-mining-and-mineral-proposals": {
        "house:119:1:358",
        "house:119:2:55",
        "house:119:2:64",
    },
    "indivisible-whole-packages": {"house:119:1:25", "house:119:1:330"},
    "distinct-natural-gas-and-petrochemical-proposals": {
        "house:119:1:303",
        "house:119:1:304",
        "house:119:1:334",
    },
}


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sealed(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = digest(result)
    return result


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"{path.relative_to(ROOT)} differs from regeneration")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def preflight() -> dict[str, Any]:
    if canonical_file_sha256(AUTHORITY_PATH) != M12F_AUTHORITY["file_sha256"]:
        raise ValueError("M12F authority digest differs")
    if canonical_file_sha256(IMPLEMENTATION_PATH) != M12F_IMPLEMENTATION["file_sha256"]:
        raise ValueError("M12F implementation digest differs")
    authority = load(AUTHORITY_PATH)
    implementation = load(IMPLEMENTATION_PATH)
    if not (
        authority["artifact_id"] == M12F_AUTHORITY["artifact_id"]
        and authority["authority_subject_sha256"]
        == M12F_AUTHORITY["authority_subject_sha256"]
        and implementation["artifact_id"] == M12F_IMPLEMENTATION["artifact_id"]
        and implementation["implementation_subject_sha256"]
        == M12F_IMPLEMENTATION["implementation_subject_sha256"]
    ):
        raise ValueError("M12F accepted identity differs")
    return implementation


def build_input(implementation: dict[str, Any]) -> dict[str, Any]:
    subject = implementation["subject"]
    episodes = subject["implementation_records"]
    episodes_by_id = {row["episode_id"]: row for row in episodes}
    candidates = []
    relationship_evidence = {}
    owners: dict[str, str] = {}
    owner_types: dict[str, str] = {}
    for definition in PROPOSITIONS:
        episode_ids = definition["evidence_episode_ids"]
        candidate = {
            **definition,
            "source_relationship_binding": {
                "relationship_subject_sha256": None,
                "inherited_authority": False,
                "use": "independently_derived_from_accepted_m12f_episode_meanings_and_directions",
            },
            "episode_semantic_evidence": {
                episode_id: episodes_by_id[episode_id]["policy_proposition"]
                for episode_id in episode_ids
            },
        }
        candidates.append(candidate)
        relationship_evidence[definition["proposition_id"]] = {
            "shared_bounded_choice": definition["rationale"],
            "episode_support": {
                episode_id: episodes_by_id[episode_id]["policy_proposition"]
                for episode_id in episode_ids
            },
            "insufficient_bases_rejected": INSUFFICIENT_BASES,
            "material_differences_preserved": definition["material_limitations"],
        }
        for episode_id in episode_ids:
            if episode_id in owners:
                raise ValueError(f"multiple primary owners for {episode_id}")
            owners[episode_id] = definition["proposition_id"]
            owner_types[episode_id] = definition["proposition_type"]

    accounting = []
    for episode in sorted(episodes, key=lambda row: row["episode_id"]):
        episode_id = episode["episode_id"]
        action_ids = set(episode["primary_action_ids"])
        contrast_ids = sorted(
            contrast_id
            for contrast_id, action_set in CONTRAST_ACTIONS.items()
            if action_ids & action_set
        )
        if episode_id in owners:
            disposition = "supports_proposed_repeated_pattern"
            reason = "Accepted episode meaning and direction independently support the bounded repeated-choice proposition."
        elif episode["member_direction"] == "non_directional_not_voting":
            disposition = "unused_non_directional_evidence"
            reason = "Not Voting is resolved but non-directional and cannot support a directional behavioral proposition."
        elif contrast_ids:
            disposition = "retained_as_limit_or_contrast"
            reason = (
                "Retained as contrast evidence for "
                + ", ".join(contrast_ids)
                + "; shared topic, agency, statute, mechanism, or direction does not establish one bounded behavioral proposition."
            )
        else:
            disposition = "no_safe_higher_level_behavioral_proposition"
            reason = "No recurring bounded choice, structured direction change, or independently selective notable-choice basis was established."
        accounting.append(
            {
                "episode_id": episode_id,
                "primary_proposition_id": owners.get(episode_id),
                "disposition": disposition,
                "reason": reason,
            }
        )
    return {
        "subject": subject["subject"],
        "episodes": episodes,
        "blocked_action_ids": [],
        "proposition_candidates": candidates,
        "episode_accounting": accounting,
        "relationship_evidence_by_proposition": relationship_evidence,
    }


def concise(value: str, limit: int = 240) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def dossier(graph: dict[str, Any], episodes: dict[str, Any]) -> str:
    propositions = graph["proposition_graph"]["propositions"]
    counts = Counter(row["disposition"] for row in graph["episode_accounting"])
    lines = [
        "# M12G Environment & Energy Behavioral Semantic IR Candidate Review",
        "",
        "This detached package proposes three repeated patterns from the 63 accepted M12F episodes. It accepts no Semantic IR, creates no synthesis, and contains no public wording.",
        "",
        "## Review summary",
        "",
        "- Repeated-pattern candidates: 3.",
        "- Trajectory candidates: 0; no related accepted episode set combines strict chronology, changed direction, and a supported substantive change.",
        "- Notable-choice candidates: 0; no otherwise-unused singleton was promoted without an independently selective basis.",
        f"- Episodes supporting candidates: {counts['supports_proposed_repeated_pattern']}.",
        f"- Episodes retained as contrasts: {counts['retained_as_limit_or_contrast']}.",
        f"- Episodes retained without a safe higher-level proposition: {counts['no_safe_higher_level_behavioral_proposition']}.",
        f"- Non-directional unused episodes: {counts['unused_non_directional_evidence']}.",
        "- Primary overlaps: 0.",
        "",
        "## Proposed candidates",
        "",
    ]
    for proposition in propositions:
        lines.extend(
            [
                f"### `{proposition['proposition_id']}`",
                "",
                f"- Type/direction: `{proposition['proposition_type']}` / `{proposition['direction']}`.",
                f"- Candidate: {proposition['proposition']}",
                f"- Evidence episodes: `{', '.join(proposition['evidence_episode_ids'])}`.",
                f"- Rationale: {proposition['rationale']}",
                f"- Material limitations: {'; '.join(proposition['material_limitations'])}",
                f"- Competing interpretation: {'; '.join(proposition['competing_interpretations'])}",
                f"- Relevant contrasts: {'; '.join(item['reason'] for item in proposition['relevant_contrasts']) or 'None beyond the recorded limitations.'}",
                "- Overlap relationships: none.",
                "- Episode-level evidence:",
                "",
            ]
        )
        for episode_id in proposition["evidence_episode_ids"]:
            episode = episodes[episode_id]
            action = episode["actions"][0]
            lines.append(
                f"  - {action['official_action_date']} — `{episode_id}` / `{action['action_id']}` — {concise(episode['policy_proposition'])}"
            )
        lines.extend(["", "This candidate has no synthesis effect.", ""])
    lines.extend(
        [
            "## Compact non-proposition accounting",
            "",
            "H.R. 6387 / `single-119-hr-6387-2-136` remains `non_directional_not_voting` and is explicitly unused as directional evidence.",
            "",
            "The remaining accounting rows are preserved in the governed graph. Contrast classes cover other heterogeneous CRA rules, other appliance-efficiency mechanisms, electricity-reliability bills, Clean Air Act choices, mining/mineral bills, natural-gas/petrochemical bills, and the two indivisible whole packages. Shared topic or vote direction alone did not create a candidate.",
            "",
            "H.R. 471 and H.R. 3898 remain whole-package evidence only; no component is attributed as a separate member position.",
            "",
            "Semantic IR acceptance, synthesis, public wording, publication, persistence, database writes, production, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    implementation = preflight()
    compiler_input = build_input(implementation)
    compiled = compile_behavioral_candidate_ir(compiler_input)
    episodes = {row["episode_id"]: row for row in compiler_input["episodes"]}
    ledger = [
        {
            "episode_id": episode["episode_id"],
            "episode_record_id": episode["record_id"],
            "episode_record_subject_sha256": episode["record_subject_sha256"],
            "member_direction": episode["member_direction"],
            "policy_proposition": episode["policy_proposition"],
            "primary_action_ids": episode["primary_action_ids"],
            "material_limitations": episode["material_limitations"],
            "actions": [
                {
                    "action_id": action["action_id"],
                    "official_action_date": action["official_action_date"],
                    "accepted_exact_action_meaning": action[
                        "accepted_exact_action_meaning"
                    ],
                    "accepted_interpretation_record_id": action[
                        "accepted_interpretation_record_id"
                    ],
                    "accepted_interpretation_record_subject_sha256": action[
                        "accepted_interpretation_record_subject_sha256"
                    ],
                    "source_references": action["source_references"],
                }
                for action in episode["actions"]
            ],
        }
        for episode in compiler_input["episodes"]
    ]
    graph = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_candidate_package_v1",
            "artifact_id": GRAPH_ID,
            "candidate_state": "complete_pending_human_substantive_review",
            "base_binding": {"post_m12e_merge_main": POST_M12E_MERGE_MAIN},
            "accepted_policy_episode_authority_binding": M12F_AUTHORITY,
            "accepted_policy_episode_implementation_binding": M12F_IMPLEMENTATION,
            "blocked_action_ids": [],
            "episode_evidence_ledger": ledger,
            "compiled_candidate_ir": compiled,
            "accepted_semantic_ir": False,
            "canonical_semantic_ir": False,
            "synthesis_included": False,
            "public_wording_included": False,
            "authorizing": False,
        },
        "candidate_subject_sha256",
    )
    decision = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_human_decision_template_v1",
            "artifact_id": DECISION_ID,
            "candidate_artifact_id": GRAPH_ID,
            "candidate_subject_sha256": graph["candidate_subject_sha256"],
            "decision_state": "empty_not_authorizing",
            "decisions": [
                {
                    "proposition_id": row["proposition_id"],
                    "decision": None,
                    "bounded_revision": None,
                    "reviewer_notes": None,
                }
                for row in compiled["proposition_graph"]["propositions"]
            ],
            "reviewer": None,
            "reviewed_at_utc": None,
            "authorizing": False,
        },
        "decision_template_subject_sha256",
    )
    dossier_text = dossier(compiled, episodes)
    for path, value, schema_path in (
        (GRAPH_PATH, graph, GRAPH_SCHEMA_PATH),
        (DECISION_PATH, decision, DECISION_SCHEMA_PATH),
    ):
        errors = sorted(Draft7Validator(load(schema_path)).iter_errors(value), key=str)
        if errors:
            raise ValueError(f"{path.name} schema error: {errors[0].message}")
        write_or_check(path, json_text(value), check=check)
    write_or_check(DOSSIER_PATH, dossier_text, check=check)
    entries = [
        {
            "path": path.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "content_subject_sha256": subject_sha,
        }
        for path, content, subject_sha in (
            (GRAPH_PATH, json_text(graph), graph["candidate_subject_sha256"]),
            (
                DECISION_PATH,
                json_text(decision),
                decision["decision_template_subject_sha256"],
            ),
            (DOSSIER_PATH, dossier_text, None),
        )
    ]
    parity = sealed(
        {
            "schema_version": "full_record_behavioral_semantic_ir_candidate_parity_v1",
            "artifact_id": "behavioral-semantic-ir-candidate-parity:f000477:environment_energy:119:v1",
            "entries": entries,
        },
        "parity_subject_sha256",
    )
    write_or_check(PARITY_PATH, json_text(parity), check=check)
    return {
        "graph": graph,
        "decision": decision,
        "parity": parity,
        "counts": Counter(
            row["proposition_type"]
            for row in compiled["proposition_graph"]["propositions"]
        ),
        "accounting": Counter(
            row["disposition"] for row in compiled["episode_accounting"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(check=args.check)
    print(
        json.dumps(
            {
                "artifact_id": GRAPH_ID,
                "candidate_subject_sha256": result["graph"]["candidate_subject_sha256"],
                "proposition_counts": result["counts"],
                "episode_accounting": result["accounting"],
                "episode_count": len(
                    result["graph"]["compiled_candidate_ir"]["episode_accounting"]
                ),
                "parity_subject_sha256": result["parity"]["parity_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
