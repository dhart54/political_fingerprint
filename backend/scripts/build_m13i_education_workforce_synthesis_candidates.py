"""Build detached M13I Education & Workforce no-safe-synthesis state."""

from __future__ import annotations

import argparse
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
from backend.scripts.build_m11i_national_security_synthesis_candidates import (  # noqa: E402
    json_text,
    text_sha256,
    write_or_check,
)
from backend.scripts.build_m13h_education_workforce_semantic_ir_acceptance import (  # noqa: E402
    ACTION_IMPLEMENTATION_PATH,
    AUTHORITY_PATH as M13H_AUTHORITY_PATH,
    EPISODE_AUTHORITY_PATH,
    EPISODE_IMPLEMENTATION_PATH,
    IMPLEMENTATION_PATH as M13H_IMPLEMENTATION_PATH,
    PARITY_PATH as M13H_PARITY_PATH,
)


POST_M13H_BASE = "38a1e6faa4d766104009129ee699f8ad323bd078"
M13H_AUTHORITY_FILE_SHA256 = (
    "2a441ae485cc534677858bad82914781e94068e7d34ccd0ac95da4e4b5c55887"
)
M13H_AUTHORITY_SUBJECT_SHA256 = (
    "83e9cf85898d35e8f952db6e514e1495f5398e0bdc80a65824ab2777c8cac20c"
)
M13H_IMPLEMENTATION_FILE_SHA256 = (
    "30329ed2ca0b6d8f32b30d573858ebbc653c38f2280a6432410b8a5e491424a9"
)
M13H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "e9bdf0b1b365aa48f19b20d4f5c871bb5ad1f3aa47f2eaa035dea62be725f6c3"
)
M13H_PARITY_FILE_SHA256 = (
    "ac39a8ce1a4254eef41098df22540a06cdbfe1e28ed14a2f1473c7e6ca517acd"
)
M13H_PARITY_SUBJECT_SHA256 = (
    "c40134c79de66e75c23e8698835dfec9f7cb8dd626dbab1b50a0bd387345bdf5"
)

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_education_workforce_119_v1"
)
PACKAGE_PATH = OUTPUT_ROOT / "synthesis_candidate_package.json"
DECISION_TEMPLATE_PATH = OUTPUT_ROOT / "human_synthesis_decision_template.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
PACKAGE_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_candidates_v1.schema.json"
)
DECISION_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_decision_template_v1.schema.json"
)
PARITY_SCHEMA_PATH = (
    ROOT / "docs/methodology/full_record_synthesis_candidate_parity_v1.schema.json"
)

PACKAGE_ID = "synthesis-candidates:f000477:education_workforce:119:v1"
DECISION_TEMPLATE_ID = (
    "human-synthesis-decision-template:f000477:education_workforce:119:v1"
)
PARITY_ID = "synthesis-candidate-parity:f000477:education_workforce:119:v1"

PROPOSITION_IDS = [
    "pattern-education-relationship-triggered-funding-restriction-opposition",
    "notable-hr1048-amendment-support-final-passage-opposition",
]

CANDIDATE_DEFINITIONS: list[dict[str, Any]] = []

PROPOSITION_ACCOUNTING = [
    {
        "proposition_id": proposition_id,
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": (
            "No safe cross-proposition synthesis survives: the funding-restriction "
            "pattern is narrowly directional, while the H.R. 1048 notable is mixed, "
            "mechanistically distinct, and cannot become directional support."
        ),
    }
    for proposition_id in PROPOSITION_IDS
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    expected = {
        M13H_AUTHORITY_PATH: M13H_AUTHORITY_FILE_SHA256,
        M13H_IMPLEMENTATION_PATH: M13H_IMPLEMENTATION_FILE_SHA256,
        M13H_PARITY_PATH: M13H_PARITY_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted M13H input differs: {path.relative_to(ROOT)}")
    authority = load(M13H_AUTHORITY_PATH)
    implementation = load(M13H_IMPLEMENTATION_PATH)
    parity = load(M13H_PARITY_PATH)
    if not (
        authority["authority_subject_sha256"] == M13H_AUTHORITY_SUBJECT_SHA256
        and implementation["implementation_subject_sha256"]
        == M13H_IMPLEMENTATION_SUBJECT_SHA256
        and parity["parity_subject_sha256"] == M13H_PARITY_SUBJECT_SHA256
    ):
        raise ValueError("accepted M13H subject identity differs")
    validate_implementation(
        implementation,
        authority=authority,
        candidate=load(
            ROOT
            / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_education_workforce_119_v1/behavioral_semantic_ir_candidate_graph.json"
        ),
        accepted_episode_authority=load(EPISODE_AUTHORITY_PATH),
        accepted_episode_implementation=load(EPISODE_IMPLEMENTATION_PATH),
        accepted_action_interpretation_implementation=load(ACTION_IMPLEMENTATION_PATH),
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
        legacy_binding_names=False,
        subject={
            "artifact_id": PACKAGE_ID,
            "member_bioguide_id": "F000477",
            "member_slug": "leg_valerie_p_foushee",
            "issue_id": "EDUCATION_WORKFORCE",
            "congress": 119,
            "chamber": "House",
            "base_binding": {
                "post_m13g_merge_main": POST_M13H_BASE,
                "m13h_authority_subject_sha256": M13H_AUTHORITY_SUBJECT_SHA256,
                "m13h_implementation_subject_sha256": M13H_IMPLEMENTATION_SUBJECT_SHA256,
            },
            "accepted_behavioral_semantic_ir_file_bindings": {
                "authority_file_sha256": M13H_AUTHORITY_FILE_SHA256,
                "implementation_file_sha256": M13H_IMPLEMENTATION_FILE_SHA256,
                "parity_file_sha256": M13H_PARITY_FILE_SHA256,
                "parity_subject_sha256": M13H_PARITY_SUBJECT_SHA256,
            },
            "source_authority_boundary": (
                "Accepted M13H Behavioral Semantic IR proposition records are the "
                "sole semantic inputs. Episode and action lineage is traceability only."
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
    lines = [
        "# M13I Education & Workforce No-Safe-Synthesis Review",
        "",
        "The exact two accepted M13H Behavioral Semantic IR propositions do not support a safe higher-level synthesis. This detached package records an explicit zero-candidate, no-safe-synthesis state for independent review.",
        "",
        "## Accepted IR retained standalone",
        "",
        "- `pattern-education-relationship-triggered-funding-restriction-opposition`: bounded opposition across only H.R. 881 and H.R. 1069.",
        "- `notable-hr1048-amendment-support-final-passage-opposition`: mixed support for H.Amdt. 12 and opposition to final passage of the distinct H.R. 1048 package.",
        "",
        "## Why no synthesis is safe",
        "",
        "The two records do not share a synthesis-level direction or mechanism. The H.R. 1048 notable is mixed and cannot become directional evidence for the funding-restriction pattern. Treating shared China or foreign-influence subject matter as a relationship would broaden two distinct funding restrictions and one distinct amendment/package episode beyond the accepted IR.",
        "",
        "H.R. 1005 remains non-directional Not Voting. H.R. 1049 is contrast-only. The eleven no-safe episodes do not become semantic inputs and cannot broaden the conclusion.",
        "",
        "The education sectors, funding streams, triggering relationships, amendment choice, and whole-package choice remain distinct. No general China, foreign-influence, disclosure, education-funding, school-governance, higher-education, or Section 117 position is established.",
        "",
        "## Review boundary",
        "",
        "Review whether the explicit zero-candidate state and complete standalone accounting are correct. The empty decision template has no candidate decisions and every downstream authorization remains false.",
        "",
        "Synthesis acceptance, public wording, publication, persistence, database or production writes, and deployment remain unauthorized.",
        "",
    ]
    return "\n".join(lines)


def build(*, check: bool = False) -> dict[str, Any]:
    authority, implementation = preflight()
    package = build_package(authority, implementation)
    decision = build_decision_template(package)
    dossier = render_dossier(package)
    Draft7Validator(load(PACKAGE_SCHEMA_PATH)).validate(package)
    Draft7Validator(load(DECISION_SCHEMA_PATH)).validate(decision)
    validate_synthesis_candidate_package(
        package, authority=authority, implementation=implementation
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
    return {
        "artifact_id": PACKAGE_ID,
        "candidate_count": package["subject"]["synthesis_candidate_count"],
        "package_file_sha256": canonical_file_sha256(PACKAGE_PATH),
        "package_subject_sha256": package["synthesis_candidate_package_subject_sha256"],
        "decision_template_file_sha256": canonical_file_sha256(DECISION_TEMPLATE_PATH),
        "decision_template_subject_sha256": decision[
            "decision_template_subject_sha256"
        ],
        "dossier_file_sha256": canonical_file_sha256(DOSSIER_PATH),
        "parity_file_sha256": canonical_file_sha256(PARITY_PATH),
        "parity_subject_sha256": parity["parity_subject_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
