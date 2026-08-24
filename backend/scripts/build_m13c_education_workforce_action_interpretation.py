from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.etl.full_record_action_interpretation import (  # noqa: E402
    build_candidate_artifact,
)
from backend.app.etl.full_record_source_readiness import (  # noqa: E402
    canonical_file_sha256,
    load_json,
    sha256_json,
)
from scripts.validate_m13a_universe_authority import (  # noqa: E402
    validate_repository as validate_m13a,
)
from scripts.validate_m13b_education_workforce_source_readiness_v2 import (  # noqa: E402
    validate_repository as validate_m13b_v2,
)


POST_M13B_V2_MAIN = "9c675413b2b238bbc61d9daa1245636f6f5b161f"
ARTIFACT_ID = "action-interpretation-candidates:f000477:education_workforce:119:v1"
OUTPUT_ROOT = ROOT / (
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_education_workforce_119_v1"
)
ARTIFACT_PATH = OUTPUT_ROOT / "candidate_batch.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
DECISION_PATH = OUTPUT_ROOT / "human_decision_template.json"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
READINESS_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_education_workforce_119_interpretation_source_readiness_v2.json"
)
SCHEMA_PATH = ROOT / (
    "docs/methodology/full_record_action_interpretation_candidates_v1.schema.json"
)
DECISION_SCHEMA_PATH = ROOT / (
    "docs/methodology/human_action_interpretation_decision_template_v1.schema.json"
)
PARITY_SCHEMA_PATH = ROOT / (
    "docs/methodology/action_interpretation_candidate_parity_manifest_v1.schema.json"
)

UPSTREAM_BINDINGS = {
    "m13a": {
        "universe_authority_receipt_id": (
            "universe-authority:f000477:education_workforce:119:v1"
        ),
        "universe_authority_receipt_sha256": (
            "491b6de2314788f1566f8366f95a66b2375ec6d1271790a18387ba33cad70ea3"
        ),
        "selection_sha256": (
            "e877adf1cd5a1bff08c08ecb4ee1ee6acc1bbdff6d93899171e13480f6473f5a"
        ),
        "universe_subject_sha256": (
            "edc381362beb1e5700748ffe75fc12c31ae14f090887940197a50bf416aaac6d"
        ),
        "action_set_sha256": (
            "83b7b129eaa32d114c72782c70cb06dac55f7cd01c8681c8dc2ae2dca986cf5b"
        ),
        "approved_action_count": 17,
        "accepted_pr": 162,
        "accepted_head": "45e3c572f1824d2e3b06292ba75c67dd6e46cfc0",
    },
    "m13b_v2": {
        "source_readiness_artifact_id": (
            "interpretation-source-readiness:f000477:education_workforce:119:v2"
        ),
        "source_readiness_artifact_sha256": (
            "36cff9b3b5f3a7ad21579373c4437aad5c9c18aaf8d2f0874721695685899aa0"
        ),
        "source_readiness_subject_sha256": (
            "aeecda1d7e883a6c03ac43c85e355812dffed1e74751e2bf1e4f8a0afb325ab0"
        ),
        "ready_count": 17,
        "blocked_count": 0,
        "accepted_pr": 164,
        "accepted_head": "885b625333413b5e880808fda41937e9ff22abca",
        "reviewed_base": "e49d416b3549d87763e375079f742f7013c1c988",
        "merge_commit": POST_M13B_V2_MAIN,
        "correction_receipt_id": (
            "source-readiness-correction:f000477:education_workforce:119:m13b-v1-to-v2"
        ),
        "correction_subject_sha256": (
            "d9a896caba1b62d9fed3d4beb44fb850e43f9f0886145a264c4ba3f55756c6d3"
        ),
    },
}

MEANING_OVERRIDES = {
    "house:119:1:146": {
        "meaning": (
            "The House choice was whether to pass H.R. 1642, which would amend "
            "the Small Business Act to require small business development centers "
            "and women's business centers to inform small businesses about hiring "
            "career-and-technical-education graduates and using those programs for "
            "hiring needs, inform students and graduates about center resources for "
            "starting or expanding a small business, and, as appropriate, connect "
            "businesses with those programs to identify career opportunities."
        ),
        "official_wording": (
            "To amend the Small Business Act to include requirements relating to "
            "graduates of career and technical education programs for small business "
            "development centers and women’s business centers, and for other purposes."
        ),
        "locator": "official-title",
        "coverage_assessment": "bounded_official_purpose_summary",
        "limitations": [
            "This exact Small Business Act mechanism does not establish general "
            "support for education, career and technical education, workforce "
            "spending, or small-business policy."
        ],
        "uncertainty_reasons": [],
    },
    "house:119:1:315": {
        "meaning": (
            "The House choice was whether to pass S. 356, which would extend and "
            "modify Secure Rural Schools payments for states and counties containing "
            "Federal land through fiscal year 2026, address fiscal year 2024 and 2025 "
            "payments, and extend county special-project and resource-advisory-"
            "committee authorities."
        ),
        "official_wording": (
            "To extend the Secure Rural Schools and Community Self-Determination "
            "Act of 2000."
        ),
        "locator": "official-title",
        "coverage_assessment": "bounded_official_purpose_summary",
        "limitations": [
            "The accepted supplemental official summary supplies program context "
            "that payments may support schools, roads, and other municipal services; "
            "it does not replace the operative S. 356 text as the meaning source."
        ],
        "uncertainty_reasons": [],
    },
    "house:119:1:83": {
        "meaning": (
            "The House choice was whether to pass H.R. 1048, which would amend the "
            "Higher Education Act of 1965 to strengthen disclosures of foreign gifts "
            "and contracts and prohibit contracts between institutions of higher "
            "education and certain foreign entities and countries of concern."
        ),
        "official_wording": (
            "To amend the Higher Education Act of 1965 to strengthen disclosure "
            "requirements relating to foreign gifts and con- tracts, to prohibit "
            "contracts between institutions of high- er education and certain foreign "
            "entities and countries of concern, and for other purposes."
        ),
        "locator": "official-title",
        "coverage_assessment": "package_level_bounded_summary",
        "limitations": [
            "This is a whole-package choice spanning multiple provisions. The "
            "candidate does not attribute the member's action to any individual "
            "component of the package."
        ],
        "uncertainty_reasons": [
            "The package-level candidate intentionally does not enumerate every "
            "operative provision."
        ],
    },
    "house:119:2:19": {
        "meaning": (
            "The House choice was whether to pass H.R. 2262 as the modified "
            "committee substitute adopted under House Resolution 988. Section 2 "
            "would change Fair Labor Standards Act hours-worked treatment by "
            "excluding employer-offered or facilitated education or training time "
            "when it occurs outside regular working hours, participation is voluntary "
            "and declining cannot trigger adverse action, and no work is performed; "
            "it also addresses related instruction under a bona fide apprenticeship "
            "program and applies to hours worked on or after enactment."
        ),
        "official_wording": (
            "Official GovInfo House-section record contains the modified committee "
            "substitute considered for H.R. 2262 at H677-H678, surrounding floor "
            "consideration at H678-H681, and delayed roll 19 at H692-H693."
        ),
        "locator": "operative-floor-text-pages",
        "coverage_assessment": "bounded_official_purpose_summary",
        "limitations": [
            "Source-native floor advocacy and support or opposition claims do not "
            "supply this neutral action meaning."
        ],
        "uncertainty_reasons": [],
    },
    "house:119:2:217": {
        "meaning": (
            "The House choice was whether to pass H.R. 7892, which would amend the "
            "Higher Education Act of 1965 to require the Secretary of Education to "
            "use an identity-fraud detection system to review each FAFSA for a "
            "reasonable suspicion of identity fraud."
        ),
        "official_wording": (
            "To amend the Higher Education Act of 1965 to require to the Secretary "
            "of Education to use an identity fraud detection system to review each "
            "FAFSA to determine whether the FAFSA presents a reasonable suspicion of "
            "identity fraud."
        ),
        "locator": "official-title",
        "coverage_assessment": "bounded_official_purpose_summary",
        "limitations": [],
        "uncertainty_reasons": [],
    },
}


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        + b"\n"
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest()


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _validate_schema(value: dict[str, Any], schema_path: Path, *, label: str) -> None:
    schema = load_json(schema_path)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
            for error in errors[:10]
        )
        raise ValueError(f"{label} schema validation failed: {detail}")


def build() -> dict[str, Any]:
    validate_m13a()
    validate_m13b_v2()
    readiness = load_json(READINESS_PATH)
    artifact = build_candidate_artifact(
        readiness_artifact=readiness,
        repository_root=ROOT,
        artifact_id=ARTIFACT_ID,
        post_merge_base=POST_M13B_V2_MAIN,
        upstream_bindings=UPSTREAM_BINDINGS,
        candidate_namespace="m13c",
        source_readiness_merge_base_field="post_source_readiness_merge_base",
        meaning_overrides=MEANING_OVERRIDES,
    )
    _validate_schema(artifact, SCHEMA_PATH, label="M13C candidate")
    return artifact


def build_decision_template(artifact: dict[str, Any]) -> dict[str, Any]:
    decisions = [
        {
            "action_id": candidate["action_id"],
            "candidate_id": candidate["candidate_id"],
            "candidate_content_subject_sha256": candidate[
                "candidate_content_subject_sha256"
            ],
            "decision": None,
            "reviewer_id": None,
            "reviewer_authority": None,
            "rationale": None,
            "decision_timestamp": None,
        }
        for candidate in artifact["subject"]["candidates"]
    ]
    subject = {
        "candidate_artifact_id": artifact["artifact_id"],
        "candidate_interpretation_subject_sha256": artifact[
            "interpretation_subject_sha256"
        ],
        "decision_count": len(decisions),
        "decisions": decisions,
        "authority_effect": "none_until_completed_and_separately_validated",
        "downstream_authorizations": artifact["subject"]["downstream_authorizations"],
    }
    return {
        "schema_version": "human_action_interpretation_decision_template_v1",
        "template_id": (
            "action-interpretation-human-decisions:f000477:education_workforce:119:v1"
        ),
        "empty_non_authorizing_template": True,
        "subject": subject,
        "decision_template_subject_sha256": sha256_json(subject),
    }


def render_dossier(artifact: dict[str, Any]) -> str:
    subject = artifact["subject"]
    aggregate = subject["aggregate"]
    lines = [
        "# M13C Education & Workforce Action-Interpretation Human Review",
        "",
        "Status: detached non-authorizing candidates pending independent semantic review.",
        "",
        f"- Exact post-M13B-v2 main: `{subject['post_source_readiness_merge_base']}`",
        f"- Candidate artifact: `{artifact['artifact_id']}`",
        f"- Interpretation subject SHA-256: `{artifact['interpretation_subject_sha256']}`",
        f"- Approved universe: {aggregate['approved_universe_count']}",
        f"- Candidate interpretations: {aggregate['candidate_count']}",
        f"- Source blocked: {aggregate['source_blocked_count']}",
        f"- Evidence/source bindings: {aggregate['evidence_source_binding_count']}",
        "- Human action-meaning decisions completed: zero.",
        "",
        "## Governing boundary",
        "",
        "Each meaning is limited to the exact House choice and accepted operative "
        "source. Source-native advocacy, party, sponsor, ideology, motive, episodes, "
        "synthesis, and public wording are excluded. Yea/Nay effects describe only "
        "the exact choice; Not Voting remains non-directional.",
        "",
        "## Aggregate accounting",
        "",
        f"- Candidate status counts: `{json.dumps(aggregate['candidate_status_counts'], sort_keys=True)}`",
        f"- Coverage counts: `{json.dumps(aggregate['coverage_assessment_counts'], sort_keys=True)}`",
        f"- Member-action counts: `{json.dumps(aggregate['member_action_counts'], sort_keys=True)}`",
        f"- Exact-choice effect counts: `{json.dumps(aggregate['position_effect_counts'], sort_keys=True)}`",
        "",
        "## Candidate ledger",
        "",
        "| Action | Exact object | Member action | Exact-choice effect | Evidence bindings | Proposed exact-action meaning | Material limitations |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    evidence_by_id = {
        item["evidence_map_id"]: item for item in subject["evidence_maps"]
    }
    for candidate in subject["candidates"]:
        binding_count = len(
            evidence_by_id[candidate["evidence_map_id"]]["source_bindings"]
        )
        lines.append(
            "| "
            + " | ".join(
                _escape(value)
                for value in (
                    candidate["action_id"],
                    candidate["exact_action_identity"],
                    candidate["official_member_action"],
                    candidate["proposed_member_position_effect"],
                    binding_count,
                    candidate["proposed_exact_action_meaning"],
                    "; ".join(candidate["limitations"]) or "None recorded",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Human decisions required",
            "",
            "Review all 17 meanings, exact-choice effects, limitations, and source "
            "bindings. Give focused attention to H.Amdt. 12, H.R. 1642, S. 356, "
            "H.R. 1005 Not Voting, and the corrected H.R. 2262 floor-text candidate. "
            "The decision template is intentionally empty and non-authorizing.",
            "",
            "No candidate authorizes action-meaning acceptance, policy episodes, "
            "Semantic IR, synthesis, public wording, integration, publication, "
            "persistence, production, deployment, or merge.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[Path, bytes]:
    artifact = build()
    decision = build_decision_template(artifact)
    _validate_schema(decision, DECISION_SCHEMA_PATH, label="M13C decision template")
    artifact_bytes = _json_bytes(artifact)
    decision_bytes = _json_bytes(decision)
    dossier_bytes = render_dossier(artifact).encode("utf-8")
    if not dossier_bytes.endswith(b"\n"):
        dossier_bytes += b"\n"
    parity_subject = {
        "candidate_artifact_id": artifact["artifact_id"],
        "candidate_interpretation_subject_sha256": artifact[
            "interpretation_subject_sha256"
        ],
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": _sha256_bytes(content),
            }
            for path, content in (
                (ARTIFACT_PATH, artifact_bytes),
                (DECISION_PATH, decision_bytes),
                (DOSSIER_PATH, dossier_bytes),
            )
        ],
        "candidate_count": len(artifact["subject"]["candidates"]),
        "blocked_count": len(artifact["subject"]["blocked_action_ids"]),
        "json_markdown_substantive_parity": True,
    }
    parity = {
        "schema_version": "action_interpretation_candidate_parity_manifest_v1",
        "manifest_id": (
            "action-interpretation-candidate-parity:f000477:education_workforce:119:v1"
        ),
        "subject": parity_subject,
        "parity_subject_sha256": sha256_json(parity_subject),
    }
    _validate_schema(parity, PARITY_SCHEMA_PATH, label="M13C parity manifest")
    return {
        ARTIFACT_PATH: artifact_bytes,
        DECISION_PATH: decision_bytes,
        DOSSIER_PATH: dossier_bytes,
        PARITY_PATH: _json_bytes(parity),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.check:
        mismatches = [
            path.relative_to(ROOT).as_posix()
            for path, content in outputs.items()
            if not path.is_file()
            or path.read_bytes().replace(b"\r\n", b"\n") != content
        ]
        if mismatches:
            raise SystemExit(f"M13C deterministic output mismatch: {mismatches}")
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    artifact = (
        load_json(ARTIFACT_PATH) if args.check else json.loads(outputs[ARTIFACT_PATH])
    )
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "interpretation_subject_sha256": artifact[
                    "interpretation_subject_sha256"
                ],
                "artifact_sha256": (
                    canonical_file_sha256(ARTIFACT_PATH)
                    if ARTIFACT_PATH.is_file()
                    else _sha256_bytes(outputs[ARTIFACT_PATH])
                ),
                "aggregate": artifact["subject"]["aggregate"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
