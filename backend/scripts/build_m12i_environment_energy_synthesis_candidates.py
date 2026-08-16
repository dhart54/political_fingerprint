"""Build detached M12I Environment & Energy synthesis candidates."""

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
from backend.scripts.build_m12h_environment_energy_semantic_ir_acceptance import (  # noqa: E402
    ACTION_IMPLEMENTATION_PATH,
    AUTHORITY_PATH as M12H_AUTHORITY_PATH,
    EPISODE_AUTHORITY_PATH,
    EPISODE_IMPLEMENTATION_PATH,
    IMPLEMENTATION_PATH as M12H_IMPLEMENTATION_PATH,
    PARITY_PATH as M12H_PARITY_PATH,
)


POST_M12H_BASE = "d3bc0fddad701e0621c87857ed80288c23a867aa"
M12H_AUTHORITY_FILE_SHA256 = (
    "eb6388827648aaa6ee6cabda3e45cf0c93f35116a6f97e9540263dec7ae7c4af"
)
M12H_AUTHORITY_SUBJECT_SHA256 = (
    "31b26aa0a671a3ffb5226a26862df3bca10de3aee93a795d92cfc3abe26be276"
)
M12H_IMPLEMENTATION_FILE_SHA256 = (
    "ae403e7334f02f4135e857d4663efa79a75540648184a444572138f1812da491"
)
M12H_IMPLEMENTATION_SUBJECT_SHA256 = (
    "8621aecaafc8352c31b16284ed6acde9d0d290f3e345af41ec6e231d774c9c32"
)
M12H_PARITY_FILE_SHA256 = (
    "0b03010e8038c7cce45cdc97b39e725329d807279a0ebf2bc50956aa4b5f431a"
)
M12H_PARITY_SUBJECT_SHA256 = (
    "ef8fbbb4b7a15a03518f140a47e9d57d7a2690b19e5d4a60ce24ed350325da04"
)

OUTPUT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/synthesis_candidates/f000477_environment_energy_119_v1"
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

PACKAGE_ID = "synthesis-candidates:f000477:environment_energy:119:v1"
DECISION_TEMPLATE_ID = (
    "human-synthesis-decision-template:f000477:environment_energy:119:v1"
)
PARITY_ID = "synthesis-candidate-parity:f000477:environment_energy:119:v1"

PROPOSITION_IDS = [
    "pattern-california-vehicle-emissions-waiver-disapproval-opposition",
    "pattern-doe-appliance-efficiency-rule-disapproval-opposition",
    "pattern-blm-land-decision-disapproval-opposition",
]

CANDIDATE_DEFINITIONS = [
    {
        "synthesis_candidate_id": "synthesis-congressional-disapproval-uniform-opposition",
        "semantic_role": "synthesis",
        "synthesis_type": "uniform_direction",
        "direction": "opposition",
        "conclusion_relevance": "primary",
        "proposition": (
            "Across three independently accepted patterns covering 13 resolutions, "
            "Foushee repeatedly opposed congressional disapproval of distinct EPA "
            "California vehicle-emissions waiver decisions, Department of Energy "
            "appliance or equipment rules, and Bureau of Land Management "
            "land-management decisions."
        ),
        "inputs": [
            {
                "proposition_id": PROPOSITION_IDS[0],
                "relationship_role": "primary_support",
                "concise_input_summary": (
                    "Opposition across two resolutions disapproving distinct EPA "
                    "California vehicle-emissions waiver decisions."
                ),
            },
            {
                "proposition_id": PROPOSITION_IDS[1],
                "relationship_role": "primary_support",
                "concise_input_summary": (
                    "Opposition across four resolutions disapproving distinct DOE "
                    "appliance or commercial-equipment rules."
                ),
            },
            {
                "proposition_id": PROPOSITION_IDS[2],
                "relationship_role": "primary_support",
                "concise_input_summary": (
                    "Opposition across seven resolutions disapproving distinct BLM "
                    "land-management decisions."
                ),
            },
        ],
        "relationship_basis": {
            "basis_type": "shared_congressional_disapproval_mechanism_across_distinct_policy_classes",
            "semantic_relationship": (
                "Three independently accepted repeated patterns share the bounded "
                "congressional-disapproval mechanism and the same accepted opposition "
                "direction while retaining distinct agencies, policy objects, and "
                "underlying decisions."
            ),
            "topic_similarity_only": False,
        },
        "relationship_rationale": (
            "The candidate adds mechanism-level structure across three accepted "
            "pattern classes rather than regrouping raw environment or energy votes. "
            "Each pattern remains an independent semantic input, and the 13 underlying "
            "episodes are deduplicated lineage rather than additional proposition nodes."
        ),
        "why_synthesis_not_topic_grouping": (
            "The relationship is the same congressional choice to oppose disapproval "
            "across three independently accepted pattern classes, not shared subject "
            "matter, agency identity, party, sponsor, or environmental-policy labeling."
        ),
        "material_limitations": [
            "The EPA, DOE, and BLM decisions concern different agencies, statutes, geographies, products, standards, plans, leases, withdrawals, and regulatory functions.",
            "Consistent opposition to congressional disapproval does not establish unrestricted support for the underlying rules, standards, plans, leases, withdrawals, or agencies.",
            "The candidate does not establish support for environmental regulation generally, climate policy generally, energy-efficiency mandates generally, or BLM policy generally.",
            "Only the three accepted M12H repeated patterns are semantic inputs; contrast-only, no-safe, non-directional, and whole-package episodes remain outside synthesis.",
        ],
        "competing_interpretation": (
            "Keep the three accepted patterns standalone because their agencies and "
            "operative decisions differ materially and the shared disapproval mechanism "
            "may add too little explanatory value beyond the accepted pattern texts."
        ),
        "unresolved_ambiguity": (
            "Human review must decide whether the common congressional-disapproval "
            "mechanism adds enough bounded explanatory information to justify synthesis "
            "across the three distinct pattern classes."
        ),
        "prohibited_inferences": [
            "motive",
            "ideology",
            "party loyalty",
            "support for all environmental regulation",
            "support for all climate policy",
            "support for all energy-efficiency mandates",
            "support for every EPA, DOE, or BLM decision",
        ],
    }
]

PROPOSITION_ACCOUNTING = [
    {
        "proposition_id": proposition_id,
        "accounting_role": "primary_input",
        "reason": (
            "Primary independently accepted repeated-pattern input to the bounded "
            "congressional-disapproval uniform-direction candidate."
        ),
    }
    for proposition_id in PROPOSITION_IDS
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    expected = {
        M12H_AUTHORITY_PATH: M12H_AUTHORITY_FILE_SHA256,
        M12H_IMPLEMENTATION_PATH: M12H_IMPLEMENTATION_FILE_SHA256,
        M12H_PARITY_PATH: M12H_PARITY_FILE_SHA256,
    }
    for path, expected_sha in expected.items():
        if canonical_file_sha256(path) != expected_sha:
            raise ValueError(f"accepted M12H input differs: {path.relative_to(ROOT)}")
    authority = load(M12H_AUTHORITY_PATH)
    implementation = load(M12H_IMPLEMENTATION_PATH)
    parity = load(M12H_PARITY_PATH)
    if not (
        authority["authority_subject_sha256"] == M12H_AUTHORITY_SUBJECT_SHA256
        and implementation["implementation_subject_sha256"]
        == M12H_IMPLEMENTATION_SUBJECT_SHA256
        and parity["parity_subject_sha256"] == M12H_PARITY_SUBJECT_SHA256
    ):
        raise ValueError("accepted M12H subject identity differs")
    validate_implementation(
        implementation,
        authority=authority,
        candidate=load(
            ROOT
            / "docs/editorial/full_record_reviews/semantic_ir_candidates/f000477_environment_energy_119_v1/behavioral_semantic_ir_candidate_graph.json"
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
            "issue_id": "ENVIRONMENT_ENERGY",
            "congress": 119,
            "chamber": "House",
            "base_binding": {
                "post_m12g_merge_main": POST_M12H_BASE,
                "m12h_authority_subject_sha256": M12H_AUTHORITY_SUBJECT_SHA256,
                "m12h_implementation_subject_sha256": M12H_IMPLEMENTATION_SUBJECT_SHA256,
            },
            "accepted_behavioral_semantic_ir_file_bindings": {
                "authority_file_sha256": M12H_AUTHORITY_FILE_SHA256,
                "implementation_file_sha256": M12H_IMPLEMENTATION_FILE_SHA256,
                "parity_file_sha256": M12H_PARITY_FILE_SHA256,
                "parity_subject_sha256": M12H_PARITY_SUBJECT_SHA256,
            },
            "source_authority_boundary": (
                "Accepted M12H Behavioral Semantic IR proposition records are the "
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
    candidate = package["subject"]["synthesis_candidates"][0]
    evidence = candidate["underlying_evidence"]
    lines = [
        "# M12I Environment & Energy Synthesis Candidate Review",
        "",
        "This detached package proposes one synthesis judgment from the exact three accepted M12H Behavioral Semantic IR propositions. It does not accept synthesis or authorize public wording or downstream use.",
        "",
        f"## `{candidate['synthesis_candidate_id']}`",
        "",
        f"**Candidate proposition:** {candidate['proposition']}",
        "",
        f"**Type / direction / relevance:** `{candidate['synthesis_type']}` / `{candidate['direction']}` / `{candidate['conclusion_relevance']}`",
        "",
        "**Accepted M12H inputs and relationship roles:**",
        "",
    ]
    for row in candidate["input_bindings"]:
        lines.append(
            f"- `{row['relationship_role']}` — `{row['proposition_id']}`: {row['concise_input_summary']}"
        )
    lines.extend(
        [
            "",
            f"**Relationship basis:** {candidate['relationship_basis']['semantic_relationship']}",
            "",
            f"**Relationship rationale:** {candidate['relationship_rationale']}",
            "",
            f"**Why this is synthesis:** {candidate['why_synthesis_not_topic_grouping']}",
            "",
            f"**Deduplicated lineage:** {evidence['unique_episode_count']} unique episodes and {evidence['unique_action_count']} unique actions. The three accepted proposition records are the semantic evidence units; their lineage is not additive evidence.",
            "",
            "**Material limitations:**",
            "",
        ]
    )
    lines.extend(f"- {value}" for value in candidate["material_limitations"])
    lines.extend(
        [
            "",
            f"**Competing interpretation:** {candidate['competing_interpretation']}",
            "",
            f"**Unresolved ambiguity:** {candidate['unresolved_ambiguity']}",
            "",
            "**Prohibited inferences:**",
            "",
        ]
    )
    lines.extend(f"- {value}" for value in candidate["prohibited_inferences"])
    lines.extend(
        [
            "",
            "## Accounting and rejected alternatives",
            "",
            "- All three accepted M12H propositions are primary inputs; none is intentionally standalone.",
            "- Candidate overlap accounting is empty because there is only one candidate.",
            "- A separate interpretive-boundary candidate was not generated because it would repeat this candidate's required limitations rather than add independent explanatory structure.",
            "- No mechanism divide exists: all three accepted patterns have the same direction and shared congressional-disapproval mechanism.",
            "- No no-common-throughline candidate is warranted because the bounded mechanism-level throughline is supported.",
            "- The 25 contrast-only, 24 no-safe, and one unused non-directional episodes remain outside synthesis, as do the H.R. 471 and H.R. 3898 whole-package episodes.",
            "",
            "## Human decision required",
            "",
            "Decide accept as written, accept with bounded revision, or reject for the single candidate. The decision template is empty and non-authorizing.",
            "",
            "Synthesis acceptance, public wording, publication, persistence, database or production writes, and deployment remain unauthorized.",
            "",
        ]
    )
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
