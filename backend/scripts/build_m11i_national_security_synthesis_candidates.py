"""Build the detached M11I National Security synthesis candidate package."""

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

from backend.app.etl.full_record_behavioral_semantic_ir_decisions import (  # noqa: E402
    seal,
    validate_implementation,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
)
from backend.app.etl.full_record_synthesis_candidates import (  # noqa: E402
    compile_synthesis_candidate_package,
    validate_synthesis_candidate_package,
)
from scripts.m11i_synthesis_candidate_data import (  # noqa: E402
    CANDIDATE_DEFINITIONS,
    PROPOSITION_ACCOUNTING,
)


POST_M11H_MERGE_MAIN = "21ea1a201cdfb58ff66af0abf98fb1ea49b1b9f6"
ACCEPTED_M11H_PR = 140
ACCEPTED_M11H_HEAD = "211691c367f653539146b9b52931093f93def3a0"
M11H_AUTHORITY_ID = (
    "human-behavioral-semantic-ir-authority:f000477:national_security_foreign:119:v1"
)
M11H_AUTHORITY_FILE_SHA256 = (
    "d1de0f28a09a01ea9b5bbe5607128564daa6aedb929a2be1255cb50f1a99fc93"
)
M11H_AUTHORITY_SUBJECT_SHA256 = (
    "22262c77622df938b3ab3642bf49452005b549706bb20160dd7c91a88ba29714"
)
M11H_IMPLEMENTATION_ID = "behavioral-semantic-ir-decision-implementation:f000477:national_security_foreign:119:v1"
M11H_IMPLEMENTATION_FILE_SHA256 = (
    "13927cade21c85f95c097acf7afe831e55bdb0de79c93e54646e14640d444ecc"
)
M11H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "6113be3d0fad4d8da21a47ed76c089f5a7d96becd45abb9c888cf2a437bf8d67"
)
M11H_PARITY_SUBJECT_SHA256 = (
    "fcd319db713eb15d65c5cef380d9800db51a3ab1d578925a6131ed63ae78859e"
)

M11H_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_national_security_foreign_119_v1"
)
M11H_AUTHORITY_PATH = M11H_ROOT / "human_behavioral_semantic_ir_authority.json"
M11H_IMPLEMENTATION_PATH = (
    M11H_ROOT / "behavioral_semantic_ir_decision_implementation.json"
)
M11H_PARITY_PATH = M11H_ROOT / "implementation_parity_manifest.json"
M11F_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_national_security_foreign_119_v1"
)
M11F_AUTHORITY_PATH = M11F_ROOT / "human_policy_episode_authority.json"
M11F_IMPLEMENTATION_PATH = M11F_ROOT / "episode_decision_implementation_bundle.json"
M11D_IMPLEMENTATION_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/interpretation_decisions/f000477_national_security_foreign_119_v1/decision_implementation_bundle.json"
)

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_national_security_foreign_119_v1"
)
PACKAGE_PATH = OUTPUT_ROOT / "synthesis_candidate_package.json"
DECISION_TEMPLATE_PATH = OUTPUT_ROOT / "human_synthesis_decision_template.json"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PACKAGE_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_candidates_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_decision_template_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_candidate_parity_v1.schema.json"
)

PACKAGE_ID = "synthesis-candidates:f000477:national_security_foreign:119:v1"
DECISION_TEMPLATE_ID = (
    "human-synthesis-decision-template:f000477:national_security_foreign:119:v1"
)
PARITY_ID = "synthesis-candidate-parity:f000477:national_security_foreign:119:v1"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError(f"deterministic M11I artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    authority = load(M11H_AUTHORITY_PATH)
    implementation = load(M11H_IMPLEMENTATION_PATH)
    parity = load(M11H_PARITY_PATH)
    if not (
        canonical_file_sha256(M11H_AUTHORITY_PATH) == M11H_AUTHORITY_FILE_SHA256
        and authority["artifact_id"] == M11H_AUTHORITY_ID
        and authority["authority_subject_sha256"] == M11H_AUTHORITY_SUBJECT_SHA256
        and canonical_file_sha256(M11H_IMPLEMENTATION_PATH)
        == M11H_IMPLEMENTATION_FILE_SHA256
        and implementation["artifact_id"] == M11H_IMPLEMENTATION_ID
        and implementation["implementation_subject_sha256"]
        == M11H_IMPLEMENTATION_SUBJECT_SHA256
        and parity["parity_subject_sha256"] == M11H_PARITY_SUBJECT_SHA256
    ):
        raise ValueError("accepted M11H identity differs")
    validate_implementation(
        implementation,
        authority=authority,
        candidate=load(
            ROOT
            / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_national_security_foreign_119_v1/behavioral_semantic_ir_candidate_graph.json"
        ),
        m11f_authority=load(M11F_AUTHORITY_PATH),
        m11f_implementation=load(M11F_IMPLEMENTATION_PATH),
        m11d_implementation=load(M11D_IMPLEMENTATION_PATH),
    )
    return authority, implementation


def build_package(
    authority: dict[str, Any], implementation: dict[str, Any]
) -> dict[str, Any]:
    return compile_synthesis_candidate_package(
        authority=authority,
        implementation=implementation,
        candidate_definitions=CANDIDATE_DEFINITIONS,
        proposition_accounting=PROPOSITION_ACCOUNTING,
        subject={
            "artifact_id": PACKAGE_ID,
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "congress": 119,
            "chamber": "House",
            "base_binding": {
                "accepted_m11h_pr": ACCEPTED_M11H_PR,
                "accepted_m11h_head": ACCEPTED_M11H_HEAD,
                "post_m11h_merge_main": POST_M11H_MERGE_MAIN,
            },
            "accepted_m11h_file_bindings": {
                "authority_file_sha256": M11H_AUTHORITY_FILE_SHA256,
                "implementation_file_sha256": M11H_IMPLEMENTATION_FILE_SHA256,
                "parity_subject_sha256": M11H_PARITY_SUBJECT_SHA256,
            },
            "source_authority_boundary": (
                "Accepted M11H Behavioral Semantic IR propositions are the sole "
                "semantic inputs. Episode and action lineage is traceability only."
            ),
        },
    )


def build_decision_template(package: dict[str, Any]) -> dict[str, Any]:
    return seal(
        {
            "schema_version": "full_record_synthesis_decision_template_v1",
            "artifact_id": DECISION_TEMPLATE_ID,
            "candidate_binding": {
                "artifact_id": package["artifact_id"],
                "synthesis_candidate_package_subject_sha256": package[
                    "synthesis_candidate_package_subject_sha256"
                ],
            },
            "decision_state": "empty_pending_human_substantive_synthesis_review",
            "candidate_decisions": [
                {
                    "synthesis_candidate_id": row["synthesis_candidate_id"],
                    "candidate_subject_sha256": row[
                        "synthesis_candidate_subject_sha256"
                    ],
                    "decision": None,
                    "bounded_revision": None,
                    "reviewer_notes": None,
                }
                for row in package["subject"]["synthesis_candidates"]
            ],
            "reviewer": None,
            "reviewer_authority": None,
            "reviewed_at_utc": None,
            "authorizing": False,
            "downstream_authorizations": {
                key: False for key in package["subject"]["downstream_authorizations"]
            },
        },
        "decision_template_subject_sha256",
    )


def render_dossier(package: dict[str, Any]) -> str:
    subject = package["subject"]
    lines = [
        "# M11I National Security Synthesis Candidate Review",
        "",
        "This package proposes synthesis relationships from the exact human-accepted M11H Behavioral Semantic IR. It does not accept synthesis or authorize public wording or downstream use.",
        "",
        "## Proposed synthesis candidates",
        "",
    ]
    for index, candidate in enumerate(subject["synthesis_candidates"], start=1):
        evidence = candidate["underlying_evidence"]
        lines.extend(
            [
                f"### {index}. `{candidate['synthesis_candidate_id']}`",
                "",
                f"**Candidate proposition:** {candidate['proposition']}",
                "",
                f"**Type / direction:** `{candidate['synthesis_type']}` / `{candidate['direction']}`",
                "",
                "**Accepted Behavioral Semantic IR inputs:**",
                "",
            ]
        )
        for binding in candidate["input_bindings"]:
            lines.append(
                f"- `{binding['relationship_role']}` — `{binding['proposition_id']}`: {binding['concise_input_summary']}"
            )
        lines.extend(
            [
                "",
                f"**Non-inflated evidence:** {evidence['unique_episode_count']} unique accepted episodes and {evidence['unique_action_count']} unique accepted actions. Behavioral proposition nodes and underlying episodes are not added together.",
                "",
                f"**Why this is synthesis:** {candidate['why_synthesis_not_topic_grouping']}",
                "",
                f"**Competing interpretation:** {candidate['competing_interpretation']}",
                "",
                "**Material limitations:**",
                "",
            ]
        )
        lines.extend(f"- {value}" for value in candidate["material_limitations"])
        lines.extend(
            [
                "",
                f"**Unresolved review question:** {candidate['unresolved_ambiguity']}",
                "",
            ]
        )
    standalone = [
        row
        for row in subject["complete_proposition_accounting"]
        if row["accounting_role"] == "intentionally_standalone_no_safe_synthesis"
    ]
    lines.extend(
        [
            "## Intentionally standalone propositions",
            "",
        ]
    )
    lines.extend(f"- `{row['proposition_id']}` — {row['reason']}" for row in standalone)
    lines.extend(
        [
            "",
            "## Candidate overlap",
            "",
        ]
    )
    for row in subject["candidate_overlap_accounting"]:
        lines.append(
            f"- `{row['left_candidate_id']}` vs `{row['right_candidate_id']}`: `{row['overlap_state']}`; shared accepted propositions: {len(row['shared_proposition_ids'])}; shared underlying episodes: {len(row['shared_episode_ids'])}."
        )
    lines.extend(
        [
            "",
            "## Human decisions required",
            "",
            "For each of the two candidates, decide accept as written, accept with bounded revision, or reject. Also confirm whether each of the seven standalone dispositions should remain outside synthesis.",
            "",
            "All 15 accepted M11H propositions are accounted for in the governed JSON. The 24 contrast-only and 25 no-safe M11G episodes remain outside direct synthesis evidence.",
            "",
            "Synthesis acceptance, public wording, publication, persistence, database writes, production writes, and deployment remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def build(check: bool = False) -> dict[str, Any]:
    authority, implementation = preflight()
    package = build_package(authority, implementation)
    decision = build_decision_template(package)
    dossier = render_dossier(package)
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    Draft7Validator(load(DECISION_SCHEMA_PATH)).validate(decision)
    validate_synthesis_candidate_package(
        package,
        authority=authority,
        implementation=implementation,
    )
    package_text = json_text(package)
    decision_text = json_text(decision)
    entries = [
        {
            "path": PACKAGE_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(package_text),
            "content_subject_sha256": package[
                "synthesis_candidate_package_subject_sha256"
            ],
        },
        {
            "path": DECISION_TEMPLATE_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(decision_text),
            "content_subject_sha256": decision["decision_template_subject_sha256"],
        },
        {
            "path": DOSSIER_PATH.relative_to(OUTPUT_ROOT).as_posix(),
            "file_sha256": text_sha256(dossier),
            "content_subject_sha256": None,
        },
    ]
    parity = seal(
        {
            "schema_version": "full_record_synthesis_candidate_parity_v1",
            "artifact_id": PARITY_ID,
            "package_binding": {
                "artifact_id": package["artifact_id"],
                "synthesis_candidate_package_subject_sha256": package[
                    "synthesis_candidate_package_subject_sha256"
                ],
            },
            "entries": entries,
        },
        "parity_subject_sha256",
    )
    Draft7Validator(load(PARITY_SCHEMA_PATH)).validate(parity)
    write_or_check(PACKAGE_PATH, package_text, check)
    write_or_check(DECISION_TEMPLATE_PATH, decision_text, check)
    write_or_check(DOSSIER_PATH, dossier, check)
    write_or_check(PARITY_PATH, json_text(parity), check)
    return {"package": package, "decision": decision, "parity": parity}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(args.check)
    package = result["package"]
    print(
        json.dumps(
            {
                "artifact_id": package["artifact_id"],
                "candidate_count": package["subject"]["synthesis_candidate_count"],
                "source_proposition_count": package["subject"][
                    "source_behavioral_proposition_count"
                ],
                "package_subject_sha256": package[
                    "synthesis_candidate_package_subject_sha256"
                ],
                "decision_template_subject_sha256": result["decision"][
                    "decision_template_subject_sha256"
                ],
                "parity_subject_sha256": result["parity"]["parity_subject_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
