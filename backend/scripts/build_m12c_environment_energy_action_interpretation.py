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
from scripts.validate_m12a_universe_authority import (  # noqa: E402
    validate_repository as validate_m12a,
)
from scripts.validate_m12b_environment_energy_source_readiness import (  # noqa: E402
    validate_repository as validate_m12b,
)


POST_M12B_MERGE_BASE = "7d4754aed87296796a1ead277a8dab242ab26027"
ARTIFACT_ID = "action-interpretation-candidates:f000477:environment_energy:119:v1"
OUTPUT_ROOT = ROOT / (
    "docs/editorial/full_record_reviews/interpretation_candidates/"
    "f000477_environment_energy_119_v1"
)
ARTIFACT_PATH = OUTPUT_ROOT / "candidate_batch.json"
DOSSIER_PATH = OUTPUT_ROOT / "human_review_dossier.md"
DECISION_PATH = OUTPUT_ROOT / "human_decision_template.json"
PARITY_PATH = OUTPUT_ROOT / "parity_manifest.json"
READINESS_PATH = ROOT / (
    "docs/editorial/full_record_reviews/source_readiness/"
    "f000477_environment_energy_119_interpretation_source_readiness_v1.json"
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
    "m12a": {
        "universe_authority_receipt_id": (
            "universe-authority:f000477:environment_energy:119:v1"
        ),
        "universe_authority_receipt_sha256": (
            "58a0d7a4f59069d747629311fdf0680385d6d802b506d585699904859773a31e"
        ),
        "selection_sha256": (
            "e18fcf736f5febac352d823b35c5a81b2c18deb36fda26b41acbef0005755fa1"
        ),
        "universe_subject_sha256": (
            "29b42a593639a1c62745e959554596a40a8dbf8205e1b3a6af83234c8f49866e"
        ),
        "action_set_sha256": (
            "843740a27ef191294bcf0cc3d2b29aeda1751351d775f8fadd7f44708e2312c8"
        ),
        "approved_action_count": 63,
        "accepted_pr": 149,
        "accepted_head": "3d031790a072ed0194720931aef0c587ecf0d8b6",
        "merge_commit": "801d6f0932b222f40d25f694c85445ec98a87c17",
    },
    "m12b": {
        "source_readiness_artifact_id": (
            "interpretation-source-readiness:f000477:environment_energy:119:v1"
        ),
        "source_readiness_artifact_sha256": (
            "ebdb1ba1a3fc40394ebd108e229a885a27eaadd964151a0843fa64e8c5e947ba"
        ),
        "source_readiness_subject_sha256": (
            "3d86b24930c0f4d1e97612da60b4b6dcba8aaadd712c12df01ce62c409a63a95"
        ),
        "ready_count": 63,
        "blocked_count": 0,
        "accepted_pr": 150,
        "accepted_head": "2973fc234de292ed6e61cadca966fcc2f586ca4f",
        "reviewed_base": "801d6f0932b222f40d25f694c85445ec98a87c17",
        "merge_commit": POST_M12B_MERGE_BASE,
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
    validate_m12a()
    validate_m12b()
    readiness = load_json(READINESS_PATH)
    artifact = build_candidate_artifact(
        readiness_artifact=readiness,
        repository_root=ROOT,
        artifact_id=ARTIFACT_ID,
        post_merge_base=POST_M12B_MERGE_BASE,
        upstream_bindings=UPSTREAM_BINDINGS,
        candidate_namespace="m12c",
        source_readiness_merge_base_field="post_source_readiness_merge_base",
    )
    _validate_schema(artifact, SCHEMA_PATH, label="M12C candidate")
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
            "action-interpretation-human-decisions:f000477:environment_energy:119:v1"
        ),
        "empty_non_authorizing_template": True,
        "subject": subject,
        "decision_template_subject_sha256": sha256_json(subject),
    }


def render_dossier(artifact: dict[str, Any]) -> str:
    subject = artifact["subject"]
    aggregate = subject["aggregate"]
    broad = [
        candidate
        for candidate in subject["candidates"]
        if candidate["coverage_assessment"] == "package_level_bounded_summary"
        or candidate["official_title_or_purpose"]["locator"]
        == "structured_operative_summary"
    ]
    lines = [
        "# M12C Environment & Energy Action-Interpretation Human Review",
        "",
        "Status: detached non-authorizing candidates pending independent semantic review.",
        "",
        f"- Exact post-M12B merge base: `{subject['post_source_readiness_merge_base']}`",
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
        "Meaning is proposed from each action's accepted stage-compatible operative "
        "evidence before the recorded member action is converted into an exact-choice "
        "effect. Party, sponsor, ideology, episodes, synthesis, public wording, "
        "motive, and voting advice are excluded.",
        "",
        "A broad-package candidate describes only the whole House choice. It does "
        "not attribute support or opposition to any individual component.",
        "",
        "## Aggregate accounting",
        "",
        f"- Candidate status counts: `{json.dumps(aggregate['candidate_status_counts'], sort_keys=True)}`",
        f"- Coverage counts: `{json.dumps(aggregate['coverage_assessment_counts'], sort_keys=True)}`",
        f"- Member-action counts: `{json.dumps(aggregate['member_action_counts'], sort_keys=True)}`",
        f"- Exact-choice effect counts: `{json.dumps(aggregate['position_effect_counts'], sort_keys=True)}`",
        "",
        "## Broad-package and structured-summary review class",
        "",
    ]
    if broad:
        for candidate in broad:
            lines.append(
                f"- `{candidate['action_id']}` / `{candidate['exact_action_identity']}`: "
                f"`{candidate['coverage_assessment']}` / "
                f"`{candidate['official_title_or_purpose']['locator']}` — "
                f"{candidate['proposed_exact_action_meaning']}"
            )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Candidate ledger",
            "",
            "| Action | Exact object | Member action | Effect | Coverage | Confidence | Evidence map | Source bindings | Proposed exact-action meaning | Limitations |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
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
                    candidate["evidence_map_id"],
                    "; ".join(candidate["source_references"]),
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
            "Review all 63 proposed meanings and exact-choice effects, with focused "
            "class review of every broad-package or structured-summary candidate and "
            "the single non-directional action. The decision template is intentionally "
            "empty and non-authorizing.",
            "",
            "No candidate authorizes action-meaning acceptance, episodes, Semantic IR, "
            "synthesis, public wording, publication, persistence, production, or "
            "deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[Path, bytes]:
    artifact = build()
    decision = build_decision_template(artifact)
    _validate_schema(decision, DECISION_SCHEMA_PATH, label="M12C decision template")
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
            "action-interpretation-candidate-parity:f000477:environment_energy:119:v1"
        ),
        "subject": parity_subject,
        "parity_subject_sha256": sha256_json(parity_subject),
    }
    _validate_schema(parity, PARITY_SCHEMA_PATH, label="M12C parity manifest")
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
            raise SystemExit(f"M12C deterministic output mismatch: {mismatches}")
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
