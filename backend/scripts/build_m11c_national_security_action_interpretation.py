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


POST_M11B_MERGE_BASE = "13f8ad58f3aee32eb90369e8b454830cfbbf130b"
ARTIFACT_ID = (
    "action-interpretation-candidates:f000477:national_security_foreign:119:v1"
)
OUTPUT_ROOT = ROOT / (
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_national_security_foreign_119_v1"
)
ARTIFACT_PATH = OUTPUT_ROOT / "candidate_batch.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
DECISION_PATH = OUTPUT_ROOT / "human_decision_template.json"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
READINESS_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_national_security_foreign_119_interpretation_source_readiness_v1.json"
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
    "m11a": {
        "universe_authority_receipt_id": (
            "universe-authority:f000477:national_security_foreign:119:v1"
        ),
        "universe_authority_receipt_sha256": (
            "89b7a27236ab0256b867c2525627408d84c6493c982c474ec4de3c2c36e79c87"
        ),
        "selection_sha256": (
            "a018b597705132f0e891c575af1dac4b880c31b0d98469f2f47001982dce0b81"
        ),
        "universe_subject_sha256": (
            "b1e1a4588a4fcef6beb9dfd836ff5c2f32d8fdb340359f11453c6a0c947a17a5"
        ),
        "action_set_sha256": (
            "190bda45c25cd32ae0a6847c862f85837eafc4a82dfda237746a66467c550400"
        ),
        "approved_action_count": 82,
        "accepted_pr": 133,
        "accepted_head": "1860ef0fab3f65ffb303c5b74b380f41fe929421",
    },
    "m11b": {
        "source_readiness_artifact_id": (
            "interpretation-source-readiness:f000477:national_security_foreign:119:v1"
        ),
        "source_readiness_artifact_sha256": (
            "acfd656ccce57e8ef0668bcedeb5c51b0ea6342097310db13236ffc5d16bf86c"
        ),
        "source_readiness_subject_sha256": (
            "53af365c4b06d4cc96fdeba17a1d65c80d89ae960d8cf986b7a5bf9599ec51bd"
        ),
        "ready_count": 81,
        "blocked_count": 1,
        "accepted_pr": 134,
        "accepted_head": "fcc988b867a49086d7545832f9575130aef0f8ea",
        "reviewed_base": "434c972132e99628bddec4cc6392adc741e03205",
        "merge_commit": POST_M11B_MERGE_BASE,
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
    readiness = load_json(READINESS_PATH)
    artifact = build_candidate_artifact(
        readiness_artifact=readiness,
        repository_root=ROOT,
        artifact_id=ARTIFACT_ID,
        post_merge_base=POST_M11B_MERGE_BASE,
        upstream_bindings=UPSTREAM_BINDINGS,
    )
    _validate_schema(artifact, SCHEMA_PATH, label="M11C candidate")
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
            "action-interpretation-human-decisions:f000477:"
            "national_security_foreign:119:v1"
        ),
        "empty_non_authorizing_template": True,
        "subject": subject,
        "decision_template_subject_sha256": sha256_json(subject),
    }


def render_dossier(artifact: dict[str, Any]) -> str:
    subject = artifact["subject"]
    aggregate = subject["aggregate"]
    lines = [
        "# M11C National Security Action-Interpretation Human Review",
        "",
        "Status: detached candidate package; no action meaning is accepted.",
        "",
        f"- Exact post-M11B merge base: `{subject['post_m11b_merge_base']}`",
        f"- Candidate artifact: `{artifact['artifact_id']}`",
        f"- Interpretation subject SHA-256: `{artifact['interpretation_subject_sha256']}`",
        f"- Approved universe: {aggregate['approved_universe_count']}",
        f"- Interpretation eligible: {aggregate['interpretation_eligible_count']}",
        f"- Candidate interpretations: {aggregate['candidate_count']}",
        f"- Source blocked: {aggregate['source_blocked_count']}",
        f"- Evidence/source bindings across eligible actions: {aggregate['evidence_source_binding_count']}",
        "- Blocked action: `house:119:2:278` / H.R. 8800; no candidate exists.",
        "",
        "The exact committed M11C PR head is supplied by the PR and consolidated "
        "review report. The artifact binds the immutable post-M11B base and its "
        "complete content subject; a commit cannot contain its own SHA.",
        "",
        "## Governing boundary",
        "",
        "Each row is a proposal for the exact recorded House choice. Yea/Nay is "
        "used only after meaning is established. Party, sponsor, ideology, "
        "episodes, desired synthesis, and public wording were excluded.",
        "",
        "Broad packages use `package_level_bounded_summary`: the whole-package "
        "choice is described without attributing the member's action to any one "
        "component.",
        "",
        "## Aggregate candidate accounting",
        "",
        f"- Candidate status counts: `{json.dumps(aggregate['candidate_status_counts'], sort_keys=True)}`",
        f"- Coverage counts: `{json.dumps(aggregate['coverage_assessment_counts'], sort_keys=True)}`",
        f"- Member-action counts: `{json.dumps(aggregate['member_action_counts'], sort_keys=True)}`",
        f"- Exact-choice effect counts: `{json.dumps(aggregate['position_effect_counts'], sort_keys=True)}`",
        "",
        "## Candidate ledger",
        "",
        "| Action | Exact object | Member action | Effect | Coverage | Confidence | Proposed exact-action meaning | Limitations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in subject["candidates"]:
        lines.append(
            "| "
            + " | ".join(
                _escape(value)
                for value in (
                    candidate["action_id"],
                    candidate["exact_action_identity"],
                    candidate["official_member_action"],
                    candidate["proposed_member_position_effect"],
                    candidate["coverage_assessment"],
                    candidate["confidence"],
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
            "Review every candidate against its evidence-map digest and official "
            "source bindings. For each row, the separate empty decision template "
            "must later record accept, revise, ambiguity-preserving disposition, "
            "or reject/no-safe-meaning. Package-level candidates require explicit "
            "judgment about whether the bounded whole-package meaning is sufficient.",
            "",
            "No decision in this package authorizes episodes, Semantic IR, "
            "synthesis, public wording, publication, persistence, production, or "
            "deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[Path, bytes]:
    artifact = build()
    decision = build_decision_template(artifact)
    _validate_schema(decision, DECISION_SCHEMA_PATH, label="M11C decision template")
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
        "candidate_count": 81,
        "blocked_count": 1,
        "json_markdown_substantive_parity": True,
    }
    parity = {
        "schema_version": "action_interpretation_candidate_parity_manifest_v1",
        "manifest_id": (
            "action-interpretation-candidate-parity:f000477:"
            "national_security_foreign:119:v1"
        ),
        "subject": parity_subject,
        "parity_subject_sha256": sha256_json(parity_subject),
    }
    _validate_schema(parity, PARITY_SCHEMA_PATH, label="M11C parity manifest")
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
            raise SystemExit(f"M11C deterministic output mismatch: {mismatches}")
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
