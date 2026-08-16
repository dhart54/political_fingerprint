from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_policy_episode_candidates import (  # noqa: E402
    build_candidate_batch,
    build_human_decision_template,
    seal,
    validate_candidate_batch,
)
from backend.scripts.build_m11e_national_security_policy_episode_candidates import (  # noqa: E402
    inferred_schema,
)
from backend.scripts.build_m12d_environment_energy_action_meaning_acceptance import (  # noqa: E402
    ACCEPTED_CANDIDATE_FILE_SHA256,
    ACCEPTED_CANDIDATE_SUBJECT_SHA256,
    ACCEPTED_HEAD,
    ACCEPTED_PR,
    AUTHORITY_ID,
    AUTHORITY_PATH,
    IMPLEMENTATION_ID,
    IMPLEMENTATION_PATH,
    POST_M12C_MERGE_MAIN,
    CANDIDATE_PATH,
)
from scripts.validate_m12d_environment_energy_action_meaning_acceptance import (  # noqa: E402
    validate_repository as validate_m12d_repository,
)

M12D_AUTHORITY_FILE_SHA256 = (
    "f5e0fa3b94e533ac8a23c8886d227c7fa26e33da83e40ef989da5941d0cd245c"
)
M12D_AUTHORITY_SUBJECT_SHA256 = (
    "1186dfbef8a611396766f0eedc94d0773ae7b5020e197b6c02b7acfc9c119709"
)
M12D_IMPLEMENTATION_FILE_SHA256 = (
    "8cd447d71e606064c04caec0f34901e3b3bce2fb515e4dba4718806a06fff507"
)
M12D_IMPLEMENTATION_SUBJECT_SHA256 = (
    "3dac037f28ec97416094b9d80337caddd4a3cf79e9d3bff40065a1c8fa49f9a3"
)

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates"
    / "f000477_environment_energy_119_v1"
)
BATCH_PATH = OUTPUT_ROOT / "policy_episode_candidate_batch.json"
DECISION_PATH = OUTPUT_ROOT / "human_episode_decision_template.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
GENERIC_BATCH_SCHEMA_PATH = (
    ROOT
    / "docs/methodology/full_record_policy_episode_candidate_batch_generic_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_policy_episode_human_decision_v1.schema.json"
)
LEGACY_BATCH_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_policy_episode_candidate_batch_v1.schema.json"
)
M11_BATCH_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates"
    / "f000477_national_security_foreign_119_v1/policy_episode_candidate_batch.json"
)

BATCH_ID = "policy-episode-candidates:f000477:environment_energy:119:v1"
DECISION_ID = "policy-episode-human-decisions:f000477:environment_energy:119:v1"
PARITY_ID = "policy-episode-candidate-parity:f000477:environment_energy:119:v1"

MULTI_ACTION_DEFINITIONS: list[dict[str, Any]] = []

CRA_ACTION_IDS = [
    "house:119:1:110",
    "house:119:1:112",
    "house:119:1:114",
    "house:119:1:143",
    "house:119:1:224",
    "house:119:1:225",
    "house:119:1:226",
    "house:119:1:294",
    "house:119:1:295",
    "house:119:1:296",
    "house:119:1:52",
    "house:119:1:53",
    "house:119:1:58",
    "house:119:1:59",
    "house:119:1:61",
    "house:119:1:77",
    "house:119:1:78",
    "house:119:2:38",
]

CONTRAST_GROUPS = [
    {
        "contrast_id": "distinct-congressional-disapproval-rules",
        "action_ids": CRA_ACTION_IDS,
        "review_conclusion": (
            "The shared Congressional Review Act mechanism does not make these one "
            "episode: each resolution targets a distinct agency rule, waiver, land-use "
            "decision, or energy standard and remains a separate House policy event."
        ),
    },
    {
        "contrast_id": "distinct-energy-efficiency-and-appliance-proposals",
        "action_ids": [
            "house:119:1:53",
            "house:119:1:59",
            "house:119:1:77",
            "house:119:1:78",
            "house:119:2:12",
            "house:119:2:23",
            "house:119:2:76",
            "house:119:2:78",
        ],
        "review_conclusion": (
            "Shared energy-efficiency subject matter is insufficient to merge separate "
            "rule disapprovals and bills addressing different products, standards, "
            "definitions, feasibility limits, recommendations, or subsidies."
        ),
    },
    {
        "contrast_id": "distinct-blm-land-decisions",
        "action_ids": [
            "house:119:1:224",
            "house:119:1:225",
            "house:119:1:226",
            "house:119:1:294",
            "house:119:1:295",
            "house:119:1:296",
            "house:119:2:38",
        ],
        "review_conclusion": (
            "These disapprovals address different BLM field offices, resource plans, "
            "leasing decisions, activity plans, or withdrawals; agency identity and "
            "mechanism do not establish one legislative episode."
        ),
    },
    {
        "contrast_id": "distinct-electricity-reliability-proposals",
        "action_ids": [
            "house:119:1:279",
            "house:119:1:323",
            "house:119:1:324",
            "house:119:1:342",
            "house:119:1:347",
        ],
        "review_conclusion": (
            "Interconnection queues, state generation standards, supply-chain reports, "
            "retirement notices, and bulk-power regulatory review are distinct measures "
            "and policy choices despite a shared electricity-reliability topic."
        ),
    },
    {
        "contrast_id": "distinct-mining-and-mineral-proposals",
        "action_ids": [
            "house:119:1:358",
            "house:119:2:55",
            "house:119:2:64",
        ],
        "review_conclusion": (
            "Hardrock mill sites and abandoned mines, executive-order codification, and "
            "critical-energy-resource supply are separate proposals, not one episode."
        ),
    },
    {
        "contrast_id": "distinct-clean-air-act-proposals",
        "action_ids": [
            "house:119:2:116",
            "house:119:2:118",
            "house:119:2:136",
            "house:119:2:164",
        ],
        "review_conclusion": (
            "Foreign emissions, proposed-legislation review, exceptional-events data, "
            "and the ethanol Reid-vapor-pressure waiver are distinct Clean Air Act "
            "proposals. Shared statute and vote direction cannot merge them."
        ),
    },
    {
        "contrast_id": "indivisible-whole-packages-remain-separate",
        "action_ids": ["house:119:1:25", "house:119:1:330"],
        "review_conclusion": (
            "H.R. 471 and H.R. 3898 remain indivisible whole-package actions with "
            "different statutes and policy objects; neither may be split into component "
            "episodes or merged with the other."
        ),
    },
]

PERMITTED_CROSS_MEASURE_SETS: set[frozenset[str]] = set()
PROHIBITED_GROUPED_SETS = [set(group["action_ids"]) for group in CONTRAST_GROUPS]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_or_check(path: Path, content: str, *, check: bool) -> None:
    normalized = content.encode("utf-8")
    if check:
        if (
            not path.is_file()
            or path.read_bytes().replace(b"\r\n", b"\n") != normalized
        ):
            raise ValueError(
                f"deterministic regeneration mismatch: {path.relative_to(ROOT)}"
            )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(normalized)


def make_generic_batch_schema(batch: dict[str, Any]) -> dict[str, Any]:
    schema = inferred_schema(batch)
    schema.update(
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": (
                "https://politicalfingerprint.example/schemas/"
                "full_record_policy_episode_candidate_batch_generic_v1"
            ),
        }
    )
    current_binding = schema["properties"]["subject"]["properties"]["input_bindings"]
    legacy_binding = load(LEGACY_BATCH_SCHEMA_PATH)["properties"]["subject"][
        "properties"
    ]["input_bindings"]
    schema["properties"]["subject"]["properties"]["input_bindings"] = {
        "oneOf": [legacy_binding, current_binding]
    }
    episode_schema = schema["properties"]["subject"]["properties"]["episodes"]["items"]
    episode_schema["properties"]["direction_derivation"]["properties"][
        "accepted_position_effects_by_action"
    ] = {
        "type": "object",
        "additionalProperties": {"type": "string"},
    }
    return schema


def concise(value: str, limit: int = 165) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def render_dossier(batch: dict[str, Any]) -> str:
    subject = batch["subject"]
    episodes = subject["episodes"]
    nondirectional = [
        row
        for row in episodes
        if row["member_direction_candidate"].startswith("non_directional")
    ]
    lines = [
        "# M12E Environment & Energy Policy-Episode Candidate Review",
        "",
        "Status: detached, non-authorizing candidates pending independent semantic review.",
        "",
        f"- Candidate artifact: `{batch['artifact_id']}`",
        f"- Candidate subject SHA-256: `{batch['episode_candidate_subject_sha256']}`",
        "- Primary accounting: 63 accepted M12D actions assigned exactly once",
        "- Proposed episodes: 63",
        "- Single-action episodes: 63",
        "- Multi-action/same-measure episodes: 0",
        "- Cross-measure episodes: 0",
        "- Ambiguous/unassigned actions: 0",
        "",
        "## Review decision summary",
        "",
        "All accepted actions are proposed as singletons. Every measure identity is "
        "unique in this record, and no accepted meaning plus legislative relationship "
        "affirmatively establishes a multi-action event. Shared topic, agency, statute, "
        "CRA mechanism, or member direction was not used as episode authority.",
        "",
        "## 1. Mechanically safe singleton ledger",
        "",
        "| Action | Measure | Direction | Accepted proposition | Contrast review |",
        "| --- | --- | --- | --- | --- |",
    ]
    for episode in episodes:
        action = episode["actions"][0]
        lines.append(
            "| "
            + " | ".join(
                (
                    action["action_id"],
                    action["exact_action_identity"],
                    episode["member_direction_candidate"],
                    concise(episode["policy_proposition"]),
                    ", ".join(episode["relevant_contrast_ids"]) or "none",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 2. Multi-action/same-measure episodes",
            "",
            "None proposed. The 63 accepted records cover 63 unique measures and one "
            "House passage/adoption action per measure.",
            "",
            "## 3. Cross-measure grouping candidates",
            "",
            "None proposed. No cross-measure set had affirmative legislative-event "
            "continuity sufficient to overcome the singleton default.",
            "",
            "## 4. Ambiguous or competing groupings",
            "",
            "None. Topic-level alternatives were evaluated only as contrast reviews and "
            "rejected as primary grouping bases.",
            "",
            "### Contrast decisions requiring reviewer awareness",
            "",
        ]
    )
    for contrast in subject["contrast_reviews"]:
        lines.extend(
            [
                f"- **{contrast['contrast_id']}** — {contrast['review_conclusion']}",
                f"  Actions: `{', '.join(contrast['action_ids'])}`",
            ]
        )
    lines.extend(
        [
            "",
            "## 5. Non-directional episode accounting",
            "",
        ]
    )
    for episode in nondirectional:
        action = episode["actions"][0]
        lines.append(
            f"- `{action['action_id']}` / {action['exact_action_identity']} remains "
            f"`{episode['member_direction_candidate']}`. It is assigned to its legislative "
            "episode for complete accounting but supplies no support/opposition direction."
        )
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            "The decision template is empty. No episode is accepted, canonical, public, "
            "or production-selectable. M12F, Semantic IR, synthesis, public wording, "
            "publication, persistence, database writes, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_m12d_repository()
    if file_sha256(AUTHORITY_PATH) != M12D_AUTHORITY_FILE_SHA256:
        raise ValueError("M12D authority file digest differs")
    if file_sha256(IMPLEMENTATION_PATH) != M12D_IMPLEMENTATION_FILE_SHA256:
        raise ValueError("M12D implementation file digest differs")
    if file_sha256(CANDIDATE_PATH) != ACCEPTED_CANDIDATE_FILE_SHA256:
        raise ValueError("accepted M12C candidate file digest differs")
    implementation = load(IMPLEMENTATION_PATH)
    candidate = load(CANDIDATE_PATH)
    if not (
        implementation["artifact_id"] == IMPLEMENTATION_ID
        and implementation["implementation_subject_sha256"]
        == M12D_IMPLEMENTATION_SUBJECT_SHA256
        and candidate["interpretation_subject_sha256"]
        == ACCEPTED_CANDIDATE_SUBJECT_SHA256
    ):
        raise ValueError("accepted M12C/M12D identity differs")
    return implementation, candidate


def build(*, check: bool = False) -> dict[str, Any]:
    implementation, candidate = preflight()
    batch = build_candidate_batch(
        artifact_id=BATCH_ID,
        subject={
            "member_name": "Valerie Foushee",
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "issue_id": "ENVIRONMENT_ENERGY",
            "congress": 119,
            "chamber": "house",
            "official_cutoff": "2026-07-23",
        },
        input_bindings={
            "accepted_action_interpretation_review_pr": ACCEPTED_PR,
            "accepted_action_interpretation_head": ACCEPTED_HEAD,
            "post_candidate_merge_main": POST_M12C_MERGE_MAIN,
            "action_interpretation_authority": {
                "artifact_id": AUTHORITY_ID,
                "final_file_sha256": M12D_AUTHORITY_FILE_SHA256,
                "authority_subject_sha256": M12D_AUTHORITY_SUBJECT_SHA256,
            },
            "action_interpretation_implementation": {
                "artifact_id": IMPLEMENTATION_ID,
                "final_file_sha256": M12D_IMPLEMENTATION_FILE_SHA256,
                "implementation_subject_sha256": M12D_IMPLEMENTATION_SUBJECT_SHA256,
            },
            "action_interpretation_candidate": {
                "artifact_id": candidate["artifact_id"],
                "final_file_sha256": ACCEPTED_CANDIDATE_FILE_SHA256,
                "interpretation_subject_sha256": ACCEPTED_CANDIDATE_SUBJECT_SHA256,
            },
        },
        implementation=implementation,
        candidate_artifact=candidate,
        multi_action_definitions=MULTI_ACTION_DEFINITIONS,
        contrast_groups=CONTRAST_GROUPS,
        blocked_action=None,
        accepted_interpretation_stage="M12D",
    )
    accounting = validate_candidate_batch(
        batch=batch,
        implementation=implementation,
        candidate_artifact=candidate,
        permitted_cross_measure_sets=PERMITTED_CROSS_MEASURE_SETS,
        prohibited_grouped_sets=PROHIBITED_GROUPED_SETS,
        blocked_action_id=None,
    )
    decision = build_human_decision_template(batch=batch, artifact_id=DECISION_ID)
    generic_schema = make_generic_batch_schema(batch)
    Draft7Validator.check_schema(generic_schema)
    for value in (load(M11_BATCH_PATH), batch):
        errors = list(Draft7Validator(generic_schema).iter_errors(value))
        if errors:
            raise ValueError(f"generic episode schema failure: {errors[0].message}")
    decision_schema = load(DECISION_SCHEMA_PATH)
    decision_errors = list(Draft7Validator(decision_schema).iter_errors(decision))
    if decision_errors:
        raise ValueError(
            f"episode decision schema failure: {decision_errors[0].message}"
        )

    json_outputs = {
        BATCH_PATH: batch,
        DECISION_PATH: decision,
        GENERIC_BATCH_SCHEMA_PATH: generic_schema,
    }
    for path, value in json_outputs.items():
        write_or_check(
            path,
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            check=check,
        )
    dossier_text = render_dossier(batch)
    write_or_check(DOSSIER_PATH, dossier_text, check=check)

    referenced = []
    for path in (BATCH_PATH, DECISION_PATH, DOSSIER_PATH, GENERIC_BATCH_SCHEMA_PATH):
        item = {
            "path": path.relative_to(ROOT).as_posix(),
            "final_file_sha256": file_sha256(path),
        }
        if path in {BATCH_PATH, DECISION_PATH}:
            parsed = load(path)
            digest_field = (
                "episode_candidate_subject_sha256"
                if path == BATCH_PATH
                else "decision_template_subject_sha256"
            )
            item[digest_field] = parsed[digest_field]
        referenced.append(item)
    parity = seal(
        {
            "schema_version": "full_record_policy_episode_candidate_parity_v1",
            "artifact_id": PARITY_ID,
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
    write_or_check(
        PARITY_PATH,
        json.dumps(parity, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        check=check,
    )
    return {
        "artifact_id": BATCH_ID,
        "artifact_file_sha256": file_sha256(BATCH_PATH),
        "episode_candidate_subject_sha256": batch["episode_candidate_subject_sha256"],
        "decision_template_file_sha256": file_sha256(DECISION_PATH),
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "dossier_file_sha256": file_sha256(DOSSIER_PATH),
        "parity_file_sha256": file_sha256(PARITY_PATH),
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
