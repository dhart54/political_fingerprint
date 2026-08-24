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
from backend.scripts.build_m13d_education_workforce_action_meaning_acceptance import (  # noqa: E402
    ACCEPTED_CANDIDATE_FILE_SHA256,
    ACCEPTED_CANDIDATE_SUBJECT_SHA256,
    ACCEPTED_HEAD,
    ACCEPTED_PR,
    AUTHORITY_ID,
    AUTHORITY_PATH,
    CANDIDATE_PATH,
    IMPLEMENTATION_ID,
    IMPLEMENTATION_PATH,
    POST_M13C_MERGE_MAIN,
)
from scripts.validate_m13d_education_workforce_action_meaning_acceptance import (  # noqa: E402
    validate_repository as validate_m13d_repository,
)

M13D_AUTHORITY_FILE_SHA256 = (
    "1009d66a9eae2fa360d1c1138981c5a900d28627f0fc95a1fa53de892dd6c6ca"
)
M13D_AUTHORITY_SUBJECT_SHA256 = (
    "5aea0708566b16d86df38297da5b4cc850d921ddcbda25254351cba96351ec77"
)
M13D_IMPLEMENTATION_FILE_SHA256 = (
    "074a3bd396a55f6c31b2f7acfacb63455e4b56e1cb2da522b7fa53c62523d656"
)
M13D_IMPLEMENTATION_SUBJECT_SHA256 = (
    "d66bc98e456a0d3bdfca1326a6766681a98080c53dc781f6cd65a863f133a863"
)

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates"
    / "f000477_education_workforce_119_v1"
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
M11_BATCH_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates/f000477_national_security_foreign_119_v1/policy_episode_candidate_batch.json"
)
M12_BATCH_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_candidates/f000477_environment_energy_119_v1/policy_episode_candidate_batch.json"
)

BATCH_ID = "policy-episode-candidates:f000477:education_workforce:119:v1"
DECISION_ID = "policy-episode-human-decisions:f000477:education_workforce:119:v1"
PARITY_ID = "policy-episode-candidate-parity:f000477:education_workforce:119:v1"
AMENDMENT_ACTION_ID = "house:119:1:79"
PASSAGE_ACTION_ID = "house:119:1:83"
HR1048_EPISODE_ID = "hr-1048-amendment-and-final-passage"

MULTI_ACTION_DEFINITIONS = [
    {
        "episode_id": HR1048_EPISODE_ID,
        "action_ids": [AMENDMENT_ACTION_ID, PASSAGE_ACTION_ID],
        "policy_proposition": (
            "Whether to adopt H.Amdt. 12's changes to H.R. 1048's Section 117 "
            "foreign-gift reporting provisions and whether to pass the distinct "
            "whole H.R. 1048 package."
        ),
        "grouping_rationale": (
            "H.Amdt. 12 is an exact amendment to H.R. 1048, and rolls 79 and 83 "
            "record the amendment and final-passage choices on the same legislative "
            "event and date. Grouping preserves both choices rather than treating "
            "parent identity as authority to collapse either meaning."
        ),
        "semantic_grouping_evidence": [
            "The governed Congress.gov amendment identity binds H.Amdt. 12 directly to H.R. 1048.",
            "The accepted meanings identify a Section 117 foreign-gift reporting amendment and the later whole-package H.R. 1048 passage choice.",
            "The official action date and roll sequence place the amendment choice before final passage on March 27, 2025.",
        ],
        "material_policy_differences": (
            "H.Amdt. 12 is a narrower Section 117 amendment choice; roll 83 is an "
            "indivisible whole-package passage choice. The episode cannot attribute "
            "the final-passage position to any individual provision."
        ),
        "competing_plausible_groupings": [
            "Treat the amendment and whole-package passage as separate singleton episodes because their exact policy scopes differ."
        ],
        "additional_limitations": [
            "The mixed episode direction records support for the amendment choice and opposition to the whole package; it does not infer motive or a single overall position on foreign-influence policy."
        ],
        "confidence": "medium",
    }
]

CONTRAST_GROUPS = [
    {
        "contrast_id": "distinct-foreign-influence-education-measures",
        "action_ids": [
            "house:119:1:120",
            "house:119:1:312",
            "house:119:1:313",
            "house:119:1:314",
            PASSAGE_ACTION_ID,
        ],
        "review_conclusion": (
            "Foreign-source or foreign-influence subject matter does not merge "
            "separate higher-education funding restrictions, K-12 disclosure or "
            "funding measures, and the bounded H.R. 1048 legislative event."
        ),
    },
    {
        "contrast_id": "distinct-higher-education-measures",
        "action_ids": [
            PASSAGE_ACTION_ID,
            "house:119:2:217",
            "house:119:2:47",
            "house:119:2:82",
        ],
        "review_conclusion": (
            "Shared Higher Education Act or institution context is insufficient: "
            "foreign-gift rules, FAFSA identity review, pregnant-student resources, "
            "and territorial in-state tuition are distinct choices."
        ),
    },
    {
        "contrast_id": "distinct-labor-and-workforce-mechanisms",
        "action_ids": [
            "house:119:1:146",
            "house:119:1:332",
            "house:119:2:19",
            "house:119:2:216",
            "house:119:2:31",
        ],
        "review_conclusion": (
            "Workforce subject matter does not establish one episode across CTE-small "
            "business connections, federal labor-management relations, FLSA training "
            "time, NLRA contracting, and ERISA investment-factor requirements."
        ),
    },
    {
        "contrast_id": "distinct-k12-school-governance-measures",
        "action_ids": [
            "house:119:1:312",
            "house:119:1:313",
            "house:119:1:314",
            "house:119:2:184",
        ],
        "review_conclusion": (
            "School setting alone cannot merge foreign-source disclosure or funding "
            "choices with parental-consent requirements for student records and accommodations."
        ),
    },
]

PERMITTED_CROSS_MEASURE_SETS = {
    frozenset(row["action_ids"]) for row in MULTI_ACTION_DEFINITIONS
}
PROHIBITED_GROUPED_SETS = [set(row["action_ids"]) for row in CONTRAST_GROUPS]


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


def concise(value: str, limit: int = 150) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def render_dossier(batch: dict[str, Any]) -> str:
    subject = batch["subject"]
    lines = [
        "# M13E Education & Workforce Policy-Episode Candidate Review",
        "",
        "Status: detached, non-authorizing candidates pending independent semantic review.",
        "",
        f"- Candidate artifact: `{batch['artifact_id']}`",
        f"- Candidate subject SHA-256: `{batch['episode_candidate_subject_sha256']}`",
        "- Primary accounting: 17 accepted M13D actions assigned exactly once",
        "- Proposed episodes: 16 (15 single-action and one two-action episode)",
        "- Ambiguous/unassigned/blocked actions: 0",
        "",
        "## Episode ledger",
        "",
        "| Episode | Actions | Identities | Direction | Proposition | Grouping basis | Exclusion boundary | Limitations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for episode in subject["episodes"]:
        lines.append(
            "| "
            + " | ".join(
                (
                    episode["episode_id"],
                    ", ".join(episode["primary_action_ids"]),
                    ", ".join(
                        row["exact_action_identity"] for row in episode["actions"]
                    ),
                    episode["member_direction_candidate"],
                    concise(episode["policy_proposition"]),
                    concise(episode["grouping_rationale"]),
                    concise(episode["material_policy_differences"]),
                    concise("; ".join(episode["material_limitations"])),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## H.Amdt. 12 / H.R. 1048 judgment",
            "",
            "Proposed as one policy episode with two distinct legislative choices. The affirmative basis is the governed amendment-to-parent relationship plus the same-day amendment/final-passage sequence. The amendment meaning, whole-package meaning, effects, and limitations remain separate inside the episode; same-parent identity alone would not have been sufficient.",
            "",
            "## Rejected grouping bases",
            "",
        ]
    )
    for contrast in subject["contrast_reviews"]:
        lines.append(
            f"- **{contrast['contrast_id']}** — {contrast['review_conclusion']} Actions: `{', '.join(contrast['action_ids'])}`"
        )
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            "The decision template is empty. No episode is accepted, canonical, public, or production-selectable. M13F, Semantic IR, synthesis, public wording, site integration, publication, persistence, database writes, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_m13d_repository()
    if file_sha256(AUTHORITY_PATH) != M13D_AUTHORITY_FILE_SHA256:
        raise ValueError("M13D authority file digest differs")
    if file_sha256(IMPLEMENTATION_PATH) != M13D_IMPLEMENTATION_FILE_SHA256:
        raise ValueError("M13D implementation file digest differs")
    implementation = load(IMPLEMENTATION_PATH)
    candidate = load(CANDIDATE_PATH)
    if not (
        file_sha256(CANDIDATE_PATH) == ACCEPTED_CANDIDATE_FILE_SHA256
        and candidate["interpretation_subject_sha256"]
        == ACCEPTED_CANDIDATE_SUBJECT_SHA256
        and implementation["artifact_id"] == IMPLEMENTATION_ID
        and implementation["implementation_subject_sha256"]
        == M13D_IMPLEMENTATION_SUBJECT_SHA256
    ):
        raise ValueError("accepted M13C/M13D identity differs")
    return implementation, candidate


def build(*, check: bool = False) -> dict[str, Any]:
    implementation, candidate = preflight()
    batch = build_candidate_batch(
        artifact_id=BATCH_ID,
        subject={
            "member_name": "Valerie Foushee",
            "member_id": "F000477",
            "legislator_id": "leg_valerie_p_foushee",
            "issue_id": "EDUCATION_WORKFORCE",
            "congress": 119,
            "chamber": "house",
            "official_cutoff": "2026-07-23",
        },
        input_bindings={
            "accepted_action_interpretation_review_pr": ACCEPTED_PR,
            "accepted_action_interpretation_head": ACCEPTED_HEAD,
            "post_candidate_merge_main": POST_M13C_MERGE_MAIN,
            "action_interpretation_authority": {
                "artifact_id": AUTHORITY_ID,
                "final_file_sha256": M13D_AUTHORITY_FILE_SHA256,
                "authority_subject_sha256": M13D_AUTHORITY_SUBJECT_SHA256,
            },
            "action_interpretation_implementation": {
                "artifact_id": IMPLEMENTATION_ID,
                "final_file_sha256": M13D_IMPLEMENTATION_FILE_SHA256,
                "implementation_subject_sha256": M13D_IMPLEMENTATION_SUBJECT_SHA256,
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
        accepted_interpretation_stage="M13D",
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
    batch_schema = load(GENERIC_BATCH_SCHEMA_PATH)
    Draft7Validator.check_schema(batch_schema)
    for value in (load(M11_BATCH_PATH), load(M12_BATCH_PATH), batch):
        errors = list(Draft7Validator(batch_schema).iter_errors(value))
        if errors:
            raise ValueError(f"generic episode schema failure: {errors[0].message}")
    decision_errors = list(
        Draft7Validator(load(DECISION_SCHEMA_PATH)).iter_errors(decision)
    )
    if decision_errors:
        raise ValueError(
            f"episode decision schema failure: {decision_errors[0].message}"
        )

    for path, value in ((BATCH_PATH, batch), (DECISION_PATH, decision)):
        write_or_check(
            path,
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            check=check,
        )
    write_or_check(DOSSIER_PATH, render_dossier(batch), check=check)
    referenced = []
    for path in (BATCH_PATH, DECISION_PATH, DOSSIER_PATH, GENERIC_BATCH_SCHEMA_PATH):
        item = {
            "path": path.relative_to(ROOT).as_posix(),
            "final_file_sha256": file_sha256(path),
        }
        if path in {BATCH_PATH, DECISION_PATH}:
            parsed = load(path)
            field = (
                "episode_candidate_subject_sha256"
                if path == BATCH_PATH
                else "decision_template_subject_sha256"
            )
            item[field] = parsed[field]
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
