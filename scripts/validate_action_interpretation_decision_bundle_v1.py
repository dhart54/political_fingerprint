"""Fail-closed validation for the detached M3B-A decision-preparation bundle."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_action_interpretation_candidate_review import BENCHMARK_ACTIONS, _sha256  # noqa: E402
from build_action_interpretation_decision_bundle_v1 import (  # noqa: E402
    BUNDLE_ID,
    OUTPUT_ROOT,
    SCHEMA_ROOT,
    SPECIAL_RECOMMENDATIONS,
    V4_BATCH_ID,
    V4_CONTENT_SHA256,
    _preflight,
    build,
)


class DecisionBundleValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DecisionBundleValidationError(message)


def _load(name: str) -> dict[str, Any]:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _verify_seals(node: object, path: str) -> None:
    if isinstance(node, dict):
        claimed = node.get("content_subject_sha256")
        if (
            isinstance(claimed, str)
            and not ("path" in node and "file_sha256" in node)
            and not ("batch_id" in node and "file_sha256" in node)
            and "remaining_severity" not in node
        ):
            subject = dict(node)
            subject.pop("content_subject_sha256")
            _require(_sha256(subject) == claimed, f"{path}: content seal mismatch")
        for key, child in node.items():
            _verify_seals(child, f"{path}.{key}")
    elif isinstance(node, list):
        for index, child in enumerate(node):
            _verify_seals(child, f"{path}[{index}]")


def validate_parity(*, byte_overrides: dict[str, bytes] | None = None) -> None:
    byte_overrides = byte_overrides or {}
    parity = _load("parity_manifest.json")
    _verify_seals(parity, "parity")
    _require(
        parity["generated_last"] and parity["parity_state"] == "pass",
        "parity state/order mismatch",
    )
    _require(parity["json_markdown_semantic_parity"], "JSON-Markdown parity missing")
    dossier = parity["dossier"]
    dossier_bytes = byte_overrides.get(
        dossier["path"], (ROOT / dossier["path"]).read_bytes()
    )
    _require(
        hashlib.sha256(dossier_bytes).hexdigest() == dossier["file_sha256"],
        "dossier final-byte mismatch",
    )
    for row in parity["canonical_artifacts"]:
        data = byte_overrides.get(row["path"], (ROOT / row["path"]).read_bytes())
        _require(
            hashlib.sha256(data).hexdigest() == row["file_sha256"],
            f"final-byte mismatch: {row['path']}",
        )
        value = json.loads(data.decode("utf-8"))
        subject = dict(value)
        claimed = subject.pop("content_subject_sha256", None)
        actual = _sha256(subject if claimed else value)
        _require(
            actual == row["content_subject_sha256"],
            f"content digest mismatch: {row['path']}",
        )
        _require(
            row["path"].encode() in dossier_bytes
            and row["file_sha256"].encode() in dossier_bytes,
            f"JSON-Markdown path/hash pair missing: {row['path']}",
        )
    _require(
        parity["referenced_file_count"] == len(parity["canonical_artifacts"]) + 1,
        "parity count mismatch",
    )


def validate_values(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    bundle = artifacts["decision_preparation_bundle.json"]
    human = artifacts["human_decision_record.json"]
    recs = artifacts["codex_recommendations.json"]
    register = artifacts["secondary_detail_register.json"]
    _require(
        bundle["bundle_id"] == BUNDLE_ID
        and bundle["generalization_decision"] == "generalization_pass",
        "bundle identity/decision mismatch",
    )
    _require(
        bundle["decision_unit_count"] == 37 and len(bundle["decision_units"]) == 37,
        "decision-unit completeness mismatch",
    )
    ids = [row["action_id"] for row in bundle["decision_units"]]
    _require(len(set(ids)) == 37, "duplicated decision unit")
    _require(
        bundle["authority_chain"]["v4"]["batch_id"] == V4_BATCH_ID
        and bundle["authority_chain"]["v4"]["content_subject_sha256"]
        == V4_CONTENT_SHA256,
        "V4 authority binding mismatch",
    )
    _require(
        bundle["accepted_candidate_count"] == 0 and not bundle["canonical"],
        "bundle became accepted or canonical",
    )
    for row in bundle["decision_units"]:
        _require(
            row["accepted"] is False and row["canonical"] is False,
            f"{row['action_id']}: unit became accepted",
        )
        _require(
            row["human_decision_options"]
            == [
                "accept_candidate",
                "accept_with_required_revision",
                "preserve_ambiguous",
                "preserve_no_safe_candidate",
                "reject_candidate",
                "unresolved",
            ],
            f"{row['action_id']}: decision options differ",
        )
    _require(
        human["decision_record_status"] == "awaiting_human_decision"
        and human["decision_count"] == 37,
        "human record status/count mismatch",
    )
    decision_ids = [row["action_id"] for row in human["decisions"]]
    _require(decision_ids == ids, "human decision membership/order mismatch")
    nullable = (
        "selected_decision",
        "structured_rationale",
        "accepted_competing_interpretation",
        "confidence_decision",
        "unresolved_question",
        "reviewer_identity",
        "decision_timestamp",
    )
    for row in human["decisions"]:
        _require(
            all(row[key] is None for key in nullable),
            f"{row['action_id']}: human scalar field filled",
        )
        _require(
            row["required_wording_or_field_revisions"] == []
            and row["accepted_limitations"] == [],
            f"{row['action_id']}: human list field filled",
        )
    _require(
        recs["recommendations_are_human_decisions"] is False
        and recs["recommendation_count"] == 37,
        "recommendation-decision separation failed",
    )
    rec_by = {row["action_id"]: row for row in recs["recommendations"]}
    _require(
        set(rec_by) == set(ids)
        and all(not row["human_decision_selected"] for row in rec_by.values()),
        "recommendation membership or separation failed",
    )
    for action_id, recommendation in SPECIAL_RECOMMENDATIONS.items():
        _require(
            rec_by[action_id]["recommendation"] == recommendation,
            f"{action_id}: special recommendation mismatch",
        )
    unit_by = {row["action_id"]: row for row in bundle["decision_units"]}
    for action_id in SPECIAL_RECOMMENDATIONS:
        _require(
            unit_by[action_id]["review_tier"] == 1,
            f"{action_id}: mandatory Tier 1 missing",
        )
    _require(
        bundle["review_tier_counts"]
        == {
            str(k): v
            for k, v in sorted(
                Counter(row["review_tier"] for row in bundle["decision_units"]).items()
            )
        },
        "review-tier accounting mismatch",
    )
    _require(
        register["review_aid_only"]
        and register["entry_count"] == len(register["entries"]),
        "secondary register accounting mismatch",
    )
    required_actions = {
        "house:119:1:130",
        "house:119:1:131",
        "house:119:1:33",
        "house:119:1:166",
        "house:119:1:27",
        "house:119:1:270",
        "house:119:1:275",
        "house:119:1:286",
        "house:119:1:289",
        "house:119:2:157",
        "house:119:2:218",
        "house:119:2:227",
        "house:119:2:240",
    }
    _require(
        required_actions <= {row["action_id"] for row in register["entries"]},
        "required secondary-detail action missing",
    )
    corpus = " ".join(
        row["source_bound_detail"] for row in register["entries"]
    ).casefold()
    for marker in (
        "one year",
        "270 days",
        "five years",
        "180 days",
        "three years",
        "15 days",
        "seven years",
        "$10,000,000",
        "$50,000",
        "$100 billion",
        "two days",
        "90 days",
        "30 days",
    ):
        _require(marker in corpus, f"secondary-detail marker missing: {marker}")
    _require(
        set(BENCHMARK_ACTIONS)
        == {
            row["action_id"]
            for row in bundle["decision_units"]
            if row["benchmark_comparison"] is not None
        },
        "benchmark projection mismatch",
    )
    return {
        "action_count": 37,
        "tier_counts": bundle["review_tier_counts"],
        "recommendation_counts": recs["recommendation_counts"],
        "secondary_detail_count": register["entry_count"],
    }


def validate() -> dict[str, Any]:
    _preflight()
    names = (
        "decision_preparation_bundle.json",
        "human_decision_record.json",
        "codex_recommendations.json",
        "secondary_detail_register.json",
    )
    artifacts = {name: _load(name) for name in names}
    for name, value in artifacts.items():
        _verify_seals(value, name)
        schema = json.loads(
            (SCHEMA_ROOT / name.replace(".json", "_v1.schema.json")).read_text(
                encoding="utf-8"
            )
        )
        Draft7Validator.check_schema(schema)
        errors = list(Draft7Validator(schema).iter_errors(value))
        _require(
            not errors, f"{name}: schema failure: {errors[0].message if errors else ''}"
        )
    parity_schema = json.loads(
        (SCHEMA_ROOT / "decision_parity_manifest_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    errors = list(
        Draft7Validator(parity_schema).iter_errors(_load("parity_manifest.json"))
    )
    _require(
        not errors, f"parity schema failure: {errors[0].message if errors else ''}"
    )
    accounting = validate_values(artifacts)
    validate_parity()
    build(check=True)
    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend/app", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    marker = BUNDLE_ID.encode()
    _require(
        not any(
            marker in (ROOT / path).read_bytes()
            for path in tracked_runtime
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "decision bundle entered runtime/public selectors",
    )
    review_state = (
        ROOT
        / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
    )
    _require(
        V4_BATCH_ID.encode() not in review_state.read_bytes()
        and BUNDLE_ID.encode() not in review_state.read_bytes(),
        "canonical review state changed",
    )
    return {
        "status": "pass",
        "bundle_id": BUNDLE_ID,
        "bundle_content_subject_sha256": artifacts["decision_preparation_bundle.json"][
            "content_subject_sha256"
        ],
        **accounting,
        "parity_state": "pass",
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
