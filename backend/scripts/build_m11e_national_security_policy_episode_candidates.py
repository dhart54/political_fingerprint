"""Build the detached M11E National Security policy-episode review package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    build_candidate_batch,
    build_human_decision_template,
    seal,
    validate_candidate_batch,
)


POST_M11D_MERGE_MAIN = "104e0bf67854342b0cde5c7247cfa302a338c527"
ACCEPTED_M11D_HEAD = "8452ca3dfb5ba740343983c2288303fe87064b19"
M11D_AUTHORITY_ID = (
    "human-action-interpretation-authority:f000477:national_security_foreign:119:v1"
)
M11D_AUTHORITY_FILE_SHA256 = (
    "b67fc818a59e441055a6b6ca32ee0f09cc91c0eec1ec99e6d4f6cd61499cc544"
)
M11D_AUTHORITY_SUBJECT_SHA256 = (
    "cde23f35cf8f876909dc5e7b779dbb600f919dc4aaa36dcd37cd08aecbacfa82"
)
M11D_IMPLEMENTATION_ID = "action-interpretation-decision-implementation:f000477:national_security_foreign:119:v1"
M11D_IMPLEMENTATION_FILE_SHA256 = (
    "402928780286f98fec90242132a829058f57517328c532e60371afab3c2173ff"
)
M11D_IMPLEMENTATION_SUBJECT_SHA256 = (
    "360f0ce47d52cb5a0d0234a88026411e94697c38cac9fca8dc87a7db6ad9ad5b"
)
M11C_CANDIDATE_ID = (
    "action-interpretation-candidates:f000477:national_security_foreign:119:v1"
)
M11C_CANDIDATE_FILE_SHA256 = (
    "6d3c0c26d56b7ace999debbc45efc0945f27320425b0f2bda55aca013630543d"
)
M11C_CANDIDATE_SUBJECT_SHA256 = (
    "db88b7e4e5f180fa72f901132b56e8f41b975a5e12d102600b45a7df766ad840"
)

IMPLEMENTATION_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/decision_implementation_bundle.json"
)
CANDIDATE_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_candidates/f000477_national_security_foreign_119_v1/candidate_batch.json"
)
OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates/f000477_national_security_foreign_119_v1"
)
BATCH_PATH = OUTPUT_ROOT / "policy_episode_candidate_batch.json"
DECISION_PATH = OUTPUT_ROOT / "human_episode_decision_template.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
BATCH_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_policy_episode_candidate_batch_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_policy_episode_human_decision_v1.schema.json"
)

BATCH_ID = "policy-episode-candidates:f000477:national_security_foreign:119:v1"
DECISION_ID = (
    "policy-episode-human-decision-template:f000477:national_security_foreign:119:v1"
)


MULTI_ACTION_DEFINITIONS = [
    {
        "episode_id": "iran-war-powers-hostilities-removal",
        "action_ids": [
            "house:119:2:85",
            "house:119:2:114",
            "house:119:2:170",
            "house:119:2:199",
            "house:119:2:282",
        ],
        "policy_proposition": "Whether to direct removal of United States Armed Forces from hostilities with or against Iran under section 5(c) of the War Powers Resolution.",
        "grouping_rationale": "Each accepted meaning independently identifies a House choice to direct removal from Iran hostilities under the same War Powers mechanism; the repeated measures present the same bounded policy proposition for human episode review.",
        "semantic_grouping_evidence": [
            "All five accepted meanings specify removal of United States Armed Forces from Iran hostilities.",
            "Four accepted meanings expressly identify section 5(c) of the War Powers Resolution; the fifth names the same removal object and Iran hostilities.",
        ],
        "material_policy_differences": "The resolutions are separate measures considered on different dates and use small wording differences such as with, against, and unauthorized hostilities.",
        "competing_plausible_groupings": [
            "Treat each resolution as a separate repeated legislative episode because each is a distinct measure and House event."
        ],
        "additional_limitations": [
            "The shared proposition does not by itself prove that the factual hostilities or legal posture were unchanged across all five dates."
        ],
        "confidence": "medium",
    },
    {
        "episode_id": "lebanon-war-powers-hostilities-removal",
        "action_ids": ["house:119:2:201", "house:119:2:232"],
        "policy_proposition": "Whether to direct removal of United States Armed Forces from hostilities in Lebanon under section 5(c) of the War Powers Resolution.",
        "grouping_rationale": "Both accepted meanings state the same Lebanon-hostilities removal choice under the same War Powers mechanism.",
        "semantic_grouping_evidence": [
            "Both accepted meanings identify removal of United States Armed Forces from hostilities in Lebanon.",
            "Both accepted meanings identify section 5(c) of the War Powers Resolution.",
        ],
        "material_policy_differences": "H.Con.Res. 84 and H.Con.Res. 108 are separate resolutions considered on different dates.",
        "competing_plausible_groupings": [
            "Treat the two resolutions as separate repeated legislative episodes."
        ],
        "additional_limitations": [
            "The M11A relationship was only a review hint; this candidate is newly grounded in the accepted M11D meanings and remains non-authorizing."
        ],
        "confidence": "medium",
    },
    {
        "episode_id": "venezuela-war-powers-hostilities-removal",
        "action_ids": ["house:119:1:346", "house:119:2:48"],
        "policy_proposition": "Whether to direct removal of United States Armed Forces from unauthorized hostilities within or against Venezuela.",
        "grouping_rationale": "Both accepted meanings identify the same removal choice concerning unauthorized Venezuela hostilities.",
        "semantic_grouping_evidence": [
            "Both accepted meanings identify removal of United States Armed Forces from unauthorized Venezuela hostilities."
        ],
        "material_policy_differences": "H.Con.Res. 64 and H.Con.Res. 68 are separate resolutions in different House sessions and use within-or-against versus from-Venezuela wording.",
        "competing_plausible_groupings": [
            "Treat the two resolutions as separate repeated legislative episodes."
        ],
        "additional_limitations": [],
        "confidence": "medium",
    },
    {
        "episode_id": "fisa-title-vii-extension-attempts",
        "action_ids": ["house:119:2:155", "house:119:2:221"],
        "policy_proposition": "Whether to extend the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978.",
        "grouping_rationale": "The accepted meanings for both measures state the same bounded operative purpose: extending FISA title VII authorities.",
        "semantic_grouping_evidence": [
            "Both accepted meanings expressly state extension of title VII authorities under the FISA Amendments Act of 2008."
        ],
        "material_policy_differences": "S. 4465 and H.R. 9238 are different measures and the H.R. 9238 action was a failed suspension vote using committee-discharged House text.",
        "competing_plausible_groupings": [
            "Treat each bill as a separate legislative episode despite the matching top-level extension purpose."
        ],
        "additional_limitations": [
            "Matching top-level purposes do not establish that every provision or duration was identical."
        ],
        "confidence": "medium",
    },
]

CONTRAST_GROUPS = [
    {
        "contrast_id": "parent-package-amendments-remain-distinct",
        "action_ids": [
            "house:119:1:208",
            "house:119:1:209",
            "house:119:1:210",
            "house:119:1:212",
            "house:119:1:244",
            "house:119:1:246",
            "house:119:1:248",
            "house:119:1:249",
            "house:119:1:250",
            "house:119:1:251",
            "house:119:1:252",
            "house:119:1:255",
            "house:119:1:257",
            "house:119:1:258",
            "house:119:1:259",
            "house:119:1:260",
            "house:119:1:262",
            "house:119:2:174",
            "house:119:2:175",
            "house:119:2:243",
            "house:119:2:244",
            "house:119:2:247",
            "house:119:2:256",
            "house:119:2:259",
            "house:119:2:260",
            "house:119:2:261",
            "house:119:2:262",
            "house:119:2:263",
            "house:119:2:264",
            "house:119:2:265",
            "house:119:2:266",
            "house:119:2:268",
            "house:119:2:269",
            "house:119:2:273",
            "house:119:2:275",
            "house:119:2:276",
        ],
        "review_conclusion": "Same-parent organization does not establish one policy episode. Each amendment and each whole-package passage choice remains distinct because the accepted meanings establish different mechanisms or propositions.",
    },
    {
        "contrast_id": "ukraine-assistance-scope-differences",
        "action_ids": [
            "house:119:1:209",
            "house:119:1:255",
            "house:119:2:207",
            "house:119:2:264",
        ],
        "review_conclusion": "Ukraine-related actions remain separate: they concern different measures and scopes, including broad support, all assistance, foreign-aid funding, or security assistance with an embassy-security exception.",
    },
    {
        "contrast_id": "jordan-assistance-scope-differences",
        "action_ids": ["house:119:1:208", "house:119:2:244"],
        "review_conclusion": "Jordan-related restrictions remain separate because one concerns armed-forces support and the other reduces multiple specified accounts across a different appropriations measure.",
    },
    {
        "contrast_id": "military-sex-gender-mechanisms-remain-distinct",
        "action_ids": [
            "house:119:1:246",
            "house:119:1:248",
            "house:119:1:249",
            "house:119:2:266",
            "house:119:2:268",
        ],
        "review_conclusion": "The actions remain distinct because they regulate different mechanisms: medical treatment, forms, single-sex spaces, service eligibility, and school athletics.",
    },
    {
        "contrast_id": "defense-energy-regulatory-mechanisms-remain-distinct",
        "action_ids": [
            "house:119:1:250",
            "house:119:1:251",
            "house:119:1:259",
            "house:119:2:259",
            "house:119:2:260",
            "house:119:2:261",
            "house:119:2:262",
        ],
        "review_conclusion": "Shared defense-readiness framing does not merge choices concerning wind radar certification, vehicle preferences, endangered-species rules, injunctions, a pipeline, refining preemption study, or recycling standards.",
    },
]

PERMITTED_CROSS_MEASURE_SETS = {
    frozenset(definition["action_ids"]) for definition in MULTI_ACTION_DEFINITIONS
}

PROHIBITED_GROUPED_SETS = [set(group["action_ids"]) for group in CONTRAST_GROUPS]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    if check:
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"{path.relative_to(ROOT)} differs from regeneration")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def inferred_schema(value: object) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        children = value
        return {
            "type": "array",
            "items": inferred_schema(children[0]) if children else {},
        }
    if isinstance(value, dict):
        return {
            "type": "object",
            "additionalProperties": False,
            "required": sorted(value),
            "properties": {
                key: inferred_schema(child) for key, child in sorted(value.items())
            },
        }
    raise TypeError(type(value))


def make_schema(value: dict[str, Any], schema_id: str) -> dict[str, Any]:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": schema_id,
        **inferred_schema(value),
    }
    if "candidate_batch" in schema_id:
        effects = schema["properties"]["subject"]["properties"]["episodes"]["items"][
            "properties"
        ]["direction_derivation"]["properties"]["accepted_position_effects_by_action"]
        effects["additionalProperties"] = {"type": "string"}
        effects["required"] = []
        effects["properties"] = {}
    return schema


def concise(value: str, limit: int = 170) -> str:
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def dossier(batch: dict[str, Any]) -> str:
    subject = batch["subject"]
    multi = [row for row in subject["episodes"] if len(row["primary_action_ids"]) > 1]
    singles = [
        row for row in subject["episodes"] if len(row["primary_action_ids"]) == 1
    ]
    lines = [
        "# M11E National Security Policy-Episode Candidate Review",
        "",
        "This package proposes episode organization only. No episode is accepted, canonical, public, or authorizing.",
        "",
        "## Review accounting",
        "",
        f"- Accepted M11D actions available: {subject['accepted_action_count']}.",
        f"- Proposed episodes: {subject['episode_count']}.",
        f"- Single-action episodes: {subject['single_action_episode_count']}.",
        f"- Multi-action episodes: {subject['multi_action_episode_count']}.",
        f"- Cross-measure episodes: {subject['cross_measure_episode_count']}.",
        "- Ambiguous or unassigned accepted actions: 0.",
        "- H.R. 8800 final passage remains source-blocked, uninterpreted, and unavailable.",
        "",
        "## High-priority multi-action and cross-measure decisions",
        "",
    ]
    for episode in multi:
        lines.extend(
            [
                f"### `{episode['episode_id']}`",
                "",
                f"- Proposition: {episode['policy_proposition']}",
                f"- Direction candidate: `{episode['member_direction_candidate']}`.",
                f"- Actions: `{', '.join(episode['primary_action_ids'])}`.",
                f"- Rationale: {episode['grouping_rationale']}",
                f"- Relevant differences: {episode['material_policy_differences']}",
                f"- Competing grouping: {'; '.join(episode['competing_plausible_groupings'])}",
                f"- Material limitations: {'; '.join(episode['material_limitations'])}",
                "- Accepted meanings:",
                "",
            ]
        )
        for action in episode["actions"]:
            lines.append(
                f"  - `{action['action_id']}` — {concise(action['accepted_exact_action_meaning'])}"
            )
        lines.extend(
            [
                "",
                "Detailed interpretation hashes and source bindings are retained in the governed JSON.",
                "",
            ]
        )
    lines.extend(
        [
            "## Single-action episode ledger",
            "",
            "Each row is a separate candidate because no broader grouping was safely established from accepted meanings.",
            "",
            "| Episode | Action | Direction | Bounded proposition | Limits |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for episode in singles:
        lines.append(
            "| `{}` | `{}` | `{}` | {} | {} |".format(
                episode["episode_id"],
                episode["primary_action_ids"][0],
                episode["member_direction_candidate"],
                concise(episode["policy_proposition"], 130).replace("|", "\\|"),
                concise("; ".join(episode["material_limitations"]), 90).replace(
                    "|", "\\|"
                ),
            )
        )
    lines.extend(
        [
            "",
            "## Contrast reviews that must not become automatic grouping",
            "",
        ]
    )
    for contrast in subject["contrast_reviews"]:
        lines.extend(
            [
                f"- `{contrast['contrast_id']}`: {contrast['review_conclusion']}",
                f"  Actions: `{', '.join(contrast['action_ids'])}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Human decisions required",
            "",
            "Review each proposed episode as written, with particular attention to all four cross-measure candidates. For each episode, select accept as written, accept with bounded revision, reject and reassign, or retain the affected actions as unassigned/ambiguous. Acceptance must be recorded in a later governed authority milestone.",
            "",
            "Do not infer approval from this dossier or its empty decision template. Policy-episode acceptance, Semantic IR, synthesis, public wording, publication, persistence, database writes, production, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    if file_sha256(IMPLEMENTATION_PATH) != M11D_IMPLEMENTATION_FILE_SHA256:
        raise ValueError("M11D implementation final-file digest differs")
    if file_sha256(CANDIDATE_PATH) != M11C_CANDIDATE_FILE_SHA256:
        raise ValueError("M11C candidate final-file digest differs")
    implementation = load_json(IMPLEMENTATION_PATH)
    candidate = load_json(CANDIDATE_PATH)
    if not (
        implementation["artifact_id"] == M11D_IMPLEMENTATION_ID
        and implementation["implementation_subject_sha256"]
        == M11D_IMPLEMENTATION_SUBJECT_SHA256
        and candidate["artifact_id"] == M11C_CANDIDATE_ID
        and candidate["interpretation_subject_sha256"] == M11C_CANDIDATE_SUBJECT_SHA256
    ):
        raise ValueError("accepted M11C/M11D identity differs")
    return implementation, candidate


def build(*, check: bool = False) -> dict[str, Any]:
    implementation, candidate = preflight()
    batch = build_candidate_batch(
        artifact_id=BATCH_ID,
        subject={
            "member_name": "Valerie Foushee",
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
            "chamber": "house",
            "official_cutoff": "2026-07-23",
        },
        input_bindings={
            "accepted_m11d_pr": 136,
            "accepted_m11d_head": ACCEPTED_M11D_HEAD,
            "post_m11d_merge_main": POST_M11D_MERGE_MAIN,
            "m11d_authority": {
                "artifact_id": M11D_AUTHORITY_ID,
                "final_file_sha256": M11D_AUTHORITY_FILE_SHA256,
                "authority_subject_sha256": M11D_AUTHORITY_SUBJECT_SHA256,
            },
            "m11d_implementation": {
                "artifact_id": M11D_IMPLEMENTATION_ID,
                "final_file_sha256": M11D_IMPLEMENTATION_FILE_SHA256,
                "implementation_subject_sha256": M11D_IMPLEMENTATION_SUBJECT_SHA256,
            },
            "m11c_candidate": {
                "artifact_id": M11C_CANDIDATE_ID,
                "final_file_sha256": M11C_CANDIDATE_FILE_SHA256,
                "interpretation_subject_sha256": M11C_CANDIDATE_SUBJECT_SHA256,
            },
        },
        implementation=implementation,
        candidate_artifact=candidate,
        multi_action_definitions=MULTI_ACTION_DEFINITIONS,
        contrast_groups=CONTRAST_GROUPS,
        blocked_action={
            "action_id": "house:119:2:278",
            "state": "source_blocked_uninterpreted_unavailable_for_episode_construction",
            "primary_episode_id": None,
        },
    )
    accounting = validate_candidate_batch(
        batch=batch,
        implementation=implementation,
        candidate_artifact=candidate,
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id="house:119:2:278",
    )
    decision = build_human_decision_template(batch=batch, artifact_id=DECISION_ID)
    batch_schema = make_schema(
        batch,
        "https://politicalfingerprint.example/schemas/full_record_policy_episode_candidate_batch_v1",
    )
    decision_schema = make_schema(
        decision,
        "https://politicalfingerprint.example/schemas/full_record_policy_episode_human_decision_v1",
    )
    Draft7Validator.check_schema(batch_schema)
    Draft7Validator.check_schema(decision_schema)
    batch_errors = list(Draft7Validator(batch_schema).iter_errors(batch))
    if batch_errors:
        raise ValueError(
            "generated batch does not satisfy generated schema: "
            + "; ".join(error.message for error in batch_errors[:5])
        )
    decision_errors = list(Draft7Validator(decision_schema).iter_errors(decision))
    if decision_errors:
        raise ValueError(
            "generated decision template does not satisfy schema: "
            + "; ".join(error.message for error in decision_errors[:5])
        )

    json_outputs = {
        BATCH_PATH: batch,
        DECISION_PATH: decision,
        BATCH_SCHEMA_PATH: batch_schema,
        DECISION_SCHEMA_PATH: decision_schema,
    }
    for path, value in json_outputs.items():
        content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        write_or_check(path, content, check=check)
    dossier_text = dossier(batch)
    write_or_check(DOSSIER_PATH, dossier_text, check=check)

    referenced = []
    for path in [
        BATCH_PATH,
        DECISION_PATH,
        DOSSIER_PATH,
        BATCH_SCHEMA_PATH,
        DECISION_SCHEMA_PATH,
    ]:
        raw = path.read_bytes() if check else path.read_bytes()
        item = {
            "path": path.relative_to(ROOT).as_posix(),
            "final_file_sha256": file_sha256(path),
        }
        if path.suffix == ".json" and path not in {
            BATCH_SCHEMA_PATH,
            DECISION_SCHEMA_PATH,
        }:
            parsed = json.loads(raw)
            for field in (
                "episode_candidate_subject_sha256",
                "decision_template_subject_sha256",
            ):
                if field in parsed:
                    item[field] = parsed[field]
        referenced.append(item)
    parity = seal(
        {
            "schema_version": "full_record_policy_episode_candidate_parity_v1",
            "artifact_id": "policy-episode-candidate-parity:f000477:national_security_foreign:119:v1",
            "candidate_batch": {
                "artifact_id": BATCH_ID,
                "episode_candidate_subject_sha256": batch[
                    "episode_candidate_subject_sha256"
                ],
            },
            "referenced_artifacts": referenced,
            "parity_state": "pass",
            "generated_last": True,
            "candidate": True,
            "accepted": False,
            "canonical": False,
            "public": False,
            "authorizing": False,
        },
        "parity_subject_sha256",
    )
    parity_content = (
        json.dumps(parity, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    write_or_check(PARITY_PATH, parity_content, check=check)
    return {
        "artifact_id": BATCH_ID,
        "artifact_file_sha256": hashlib.sha256(
            (
                json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
        ).hexdigest(),
        "episode_candidate_subject_sha256": batch["episode_candidate_subject_sha256"],
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "parity_subject_sha256": parity["parity_subject_sha256"],
        **accounting,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
