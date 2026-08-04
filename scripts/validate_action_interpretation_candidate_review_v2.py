"""Fail-closed validation for the detached M3A-R1 V2 review bundle."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from action_interpretation_candidate_v2_data import (  # noqa: E402
    ACTION_DEFINITIONS,
    TARGETED_INITIAL_OMISSIONS,
)
from build_action_interpretation_candidate_review_v2 import (  # noqa: E402
    BATCH_ID,
    BENCHMARK_ACTIONS,
    M2_SHA256,
    OUTPUT_ROOT,
    PACKET_ROOT,
    SCHEMA_ROOT,
    V1_ROOT,
    V1_SUBJECT_SHA256,
    _sha256,
    build_freeze,
    build_post_freeze,
)


class CandidateReviewV2ValidationError(ValueError):
    """Raised when the V2 bundle violates a closed contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateReviewV2ValidationError(message)


def _load(name: str) -> dict[str, object]:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _verify_content_seals(value: object, path: str) -> None:
    if isinstance(value, dict):
        if (
            "content_subject_sha256" in value
            and isinstance(value["content_subject_sha256"], str)
            and len(value["content_subject_sha256"]) == 64
            and not ("path" in value and "file_sha256" in value)
        ):
            subject = dict(value)
            claimed = subject.pop("content_subject_sha256")
            _require(_sha256(subject) == claimed, f"{path}: content subject mismatch")
        if (
            "candidate_content_subject_sha256" in value
            and "proposed_exact_action_meaning" in value
        ):
            subject = dict(value)
            claimed = subject.pop("candidate_content_subject_sha256")
            _require(_sha256(subject) == claimed, f"{path}: candidate subject mismatch")
        for key, child in value.items():
            _verify_content_seals(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _verify_content_seals(child, f"{path}[{index}]")


def _schema_name(artifact_name: str) -> str:
    return artifact_name.replace(".json", "_v2.schema.json")


def _validate_schema(instance: object, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema).iter_errors(instance), key=lambda e: list(e.path)
    )
    _require(
        not errors, f"{label}: schema failure: {errors[0].message if errors else ''}"
    )


def validate_parity(
    *,
    parity_override: dict[str, object] | None = None,
    byte_overrides: dict[str, bytes] | None = None,
) -> None:
    parity = parity_override or _load("parity_manifest.json")
    byte_overrides = byte_overrides or {}
    _verify_content_seals(parity, "parity_manifest")
    _require(parity["parity_state"] == "pass", "parity state is not pass")
    _require(parity["generated_last"] is True, "parity was not generated last")
    rows = parity["canonical_artifacts"]
    _require(
        parity["referenced_file_count"] == len(rows) + 1,
        "parity referenced-file count mismatch",
    )
    expected_keys = {
        "path",
        "content_subject_sha256",
        "file_sha256",
        "digest_semantics",
    }
    seen = set()
    dossier_text = (
        byte_overrides.get(parity["dossier"]["path"])
        or (ROOT / parity["dossier"]["path"]).read_bytes()
    )
    for row in rows:
        _require(
            set(row) == expected_keys,
            f"mixed digest convention in canonical row: {row.get('path')}",
        )
        path = row["path"]
        _require(path not in seen, f"duplicate parity path: {path}")
        seen.add(path)
        data = byte_overrides.get(path) or (ROOT / path).read_bytes()
        _require(
            hashlib.sha256(data).hexdigest() == row["file_sha256"],
            f"final file SHA-256 mismatch: {path}",
        )
        value = json.loads(data.decode("utf-8"))
        if isinstance(value, dict) and "content_subject_sha256" in value:
            subject = dict(value)
            claimed = subject.pop("content_subject_sha256")
            actual_content = _sha256(subject)
            _require(claimed == actual_content, f"self content digest mismatch: {path}")
        else:
            actual_content = _sha256(value)
        _require(
            actual_content == row["content_subject_sha256"],
            f"content subject mismatch: {path}",
        )
        _require(row["path"].encode() in dossier_text, f"dossier omits path: {path}")
        _require(
            row["content_subject_sha256"].encode() in dossier_text,
            f"dossier omits content digest: {path}",
        )
        _require(
            row["file_sha256"].encode() in dossier_text,
            f"dossier omits file digest: {path}",
        )
    dossier = parity["dossier"]
    _require(set(dossier) == expected_keys, "mixed digest convention in dossier row")
    _require(
        hashlib.sha256(dossier_text).hexdigest() == dossier["file_sha256"],
        "dossier final file SHA-256 mismatch",
    )


def _validate_candidate_contract(candidate: dict[str, object]) -> None:
    action_id = candidate["action_id"]
    _require(action_id in ACTION_DEFINITIONS, f"outside action: {action_id}")
    _require(
        candidate["title_only_exception_used"] is False,
        f"title-only exception used: {action_id}",
    )
    _require(
        candidate["official_title_or_purpose"]["wording"],
        f"missing official title/purpose: {action_id}",
    )
    if candidate["status"] == "no_safe_candidate":
        _require(
            candidate["proposed_exact_action_meaning"] is None,
            f"no-safe candidate has meaning: {action_id}",
        )
        _require(
            not candidate["claim_components"],
            f"no-safe candidate has claim: {action_id}",
        )
        return
    meaning = candidate["proposed_exact_action_meaning"]
    _require(
        isinstance(meaning, str)
        and meaning.startswith("The House choice was whether to"),
        f"meaning is not exact-choice plain English: {action_id}",
    )
    _require(
        meaning != candidate["official_title_or_purpose"]["wording"],
        f"official title used as interpretation: {action_id}",
    )
    material = [
        *candidate["material_provisions"],
        *candidate["material_limits_and_exceptions"],
    ]
    _require(material, f"candidate has no material inventory: {action_id}")
    _require(
        all(row["locator"] != "official-title" for row in material),
        f"material item uses title locator: {action_id}",
    )
    _require(
        all(
            row["representation_state"] != "omitted_pending_coverage_review"
            for row in material
        ),
        f"frozen candidate retains omitted item: {action_id}",
    )
    _require(
        candidate["claim_components"],
        f"candidate lacks source-bound claim component: {action_id}",
    )
    _require(
        all(
            claim["locator"] and claim["locator"] != "official-title"
            for claim in candidate["claim_components"]
        ),
        f"claim lacks operative locator: {action_id}",
    )
    if candidate["confidence"] == "high":
        _require(
            candidate["coverage_assessment"] == "complete_bounded_summary",
            f"high confidence without complete coverage: {action_id}",
        )
        _require(
            candidate["status"] == "proposed",
            f"high confidence non-proposed candidate: {action_id}",
        )


def _targeted_assertions(candidates: dict[str, dict[str, object]]) -> None:
    def text(action_id: str) -> str:
        row = candidates[action_id]
        return " ".join(
            [
                row["proposed_exact_action_meaning"] or "",
                *(item["wording"] for item in row["material_provisions"]),
                *(item["wording"] for item in row["material_limits_and_exceptions"]),
            ]
        ).casefold()

    for needle in ("10 years", "exceptions", "minor who undergoes"):
        _require(needle in text("house:119:1:351"), f"roll 351 omits {needle}")
    for needle in ("secure", "sponsor", "recognizance", "screening"):
        _require(needle in text("house:119:1:340"), f"roll 340 omits {needle}")
    for needle in ("two-year", "five-to-20", "10 years to life", "annual"):
        _require(needle in text("house:119:1:42"), f"roll 42 omits {needle}")
    for action_id, needles in {
        "house:119:1:166": ("research", "penalties", "schedule i"),
        "house:119:1:131": ("reporting system", "wellness"),
        "house:119:1:275": ("unacceptable risk", "futile", "more effective"),
        "house:119:1:299": ("retaining", "subtitles"),
        "house:119:2:221": ("june 12, 2026", "july 2, 2026"),
        "house:119:2:273": ("chaplain", "confidential", "uniform code"),
    }.items():
        for needle in needles:
            _require(needle in text(action_id), f"{action_id} omits {needle}")
    roll155 = candidates["house:119:2:155"]
    rec = roll155["source_identity_reconciliation"]
    _require(
        rec["dublin_core_title"].startswith("110 S4465 ES"),
        "roll 155 Dublin Core conflict missing",
    )
    _require(
        rec["structured_congress"] == "119th CONGRESS",
        "roll 155 structured congress missing",
    )
    _require(rec["structured_legis_num"] == "S. 4465", "roll 155 legis-num missing")
    _require(
        roll155["status"] == "ambiguous" and roll155["confidence"] == "low",
        "roll 155 not routed ambiguous/low",
    )
    _require(
        "April 30, 2026".casefold() in text("house:119:2:155")
        and "June 12, 2026".casefold() in text("house:119:2:155"),
        "roll 155 expiry extension missing",
    )
    roll278 = candidates["house:119:2:278"]
    _require(
        roll278["status"] == "no_safe_candidate" and roll278["confidence"] == "low",
        "roll 278 no-safe disposition missing",
    )


def validate() -> dict[str, object]:
    build_freeze(check=True)
    build_post_freeze(check=True)
    names = [
        "revision_directive.json",
        "review_contracts.json",
        "evidence_maps.json",
        "initial_candidate_batch.json",
        "provision_coverage_reviews.json",
        "scope_neutrality_reviews.json",
        "bounded_corrections.json",
        "candidate_batch.json",
        "benchmark_comparison.json",
        "sample_manifest.json",
        "human_decision_template.json",
        "parity_manifest.json",
    ]
    artifacts = {name: _load(name) for name in names}
    for name, artifact in artifacts.items():
        _verify_content_seals(artifact, name)
        _validate_schema(artifact, SCHEMA_ROOT / _schema_name(name), name)
    packets = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(PACKET_ROOT.glob("*.json"))
    ]
    packet_schema = SCHEMA_ROOT / "worker_packet_v2.schema.json"
    for packet in packets:
        _verify_content_seals(packet, packet["action_id"])
        _validate_schema(packet, packet_schema, packet["action_id"])
        serialized = json.dumps(packet, sort_keys=True).casefold()
        for forbidden in (
            "accepted_benchmark_text",
            "benchmark_conclusion",
            "member_party",
            "semantic_ir",
            "episode_membership",
            "synthesis_outcomes",
            "other_action_candidates",
        ):
            if forbidden not in packet["worker_input_forbidden"]:
                _require(
                    forbidden not in serialized,
                    f"worker blindness leak: {packet['action_id']} {forbidden}",
                )
    _require(
        len(packets) == 37
        and {row["action_id"] for row in packets} == set(ACTION_DEFINITIONS),
        "worker packet accounting mismatch",
    )
    directive = artifacts["revision_directive.json"]
    _require(
        directive["decision"] == "global_revision_required",
        "revision decision mismatch",
    )
    _require(
        not directive["human_approval"] and not directive["accepts_any_interpretation"],
        "revision directive became acceptance",
    )
    v1_batch = json.loads(
        (V1_ROOT / "candidate_batch.json").read_text(encoding="utf-8")
    )
    _require(
        v1_batch["candidate_batch_subject_sha256"] == V1_SUBJECT_SHA256,
        "V1 subject changed",
    )
    batch = artifacts["candidate_batch.json"]
    _require(
        batch["batch_id"] == BATCH_ID and batch["action_count"] == 37,
        "V2 batch identity/accounting mismatch",
    )
    _require(
        batch["frozen"] and batch["freeze_precedes_benchmark_access"],
        "freeze gate missing",
    )
    _require(
        not batch["accepted"]
        and not batch["canonical_review_state"]
        and not batch["production_selector_eligible"],
        "candidate entered authorized state",
    )
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    _require(
        len(candidates) == 37 and set(candidates) == set(ACTION_DEFINITIONS),
        "candidate accounting mismatch",
    )
    for candidate in candidates.values():
        _validate_candidate_contract(candidate)
    _targeted_assertions(candidates)
    _require(
        Counter(row["status"] for row in candidates.values())
        == Counter({"proposed": 35, "ambiguous": 1, "no_safe_candidate": 1}),
        "status accounting mismatch",
    )
    _require(
        Counter(row["confidence"] for row in candidates.values())
        == Counter({"high": 14, "medium": 21, "low": 2}),
        "confidence accounting mismatch",
    )
    _require(
        sum(len(row["material_provisions"]) for row in candidates.values()) == 97,
        "material provision accounting mismatch",
    )
    _require(
        sum(len(row["material_limits_and_exceptions"]) for row in candidates.values())
        == 33,
        "material limit accounting mismatch",
    )
    initial = artifacts["initial_candidate_batch.json"]
    _require(
        initial["benchmark_inaccessible"] is True,
        "benchmark accessible to initial workers",
    )
    initial_by = {row["action_id"]: row for row in initial["candidates"]}
    for action_id, omitted in TARGETED_INITIAL_OMISSIONS.items():
        material = [
            *initial_by[action_id]["material_provisions"],
            *initial_by[action_id]["material_limits_and_exceptions"],
        ]
        actual = {
            row.get("provision_id", row.get("limit_id"))
            for row in material
            if row["representation_state"] == "omitted_pending_coverage_review"
        }
        _require(
            actual == set(omitted), f"initial omission inventory mismatch: {action_id}"
        )
    coverage = artifacts["provision_coverage_reviews.json"]
    scope = artifacts["scope_neutrality_reviews.json"]
    _require(
        Counter(row["highest_severity"] for row in coverage["reviews"])
        == Counter({"none": 29, "major": 8}),
        "coverage severity accounting mismatch",
    )
    _require(
        Counter(row["highest_severity"] for row in scope["reviews"])
        == Counter({"none": 35, "major": 2}),
        "scope severity accounting mismatch",
    )
    _require(
        all(
            row["reviewer_role"] == "independent_provision_coverage_reviewer"
            and row["reviewer_cannot_accept"]
            for row in coverage["reviews"]
        ),
        "coverage reviewer role/authority mismatch",
    )
    _require(
        all(
            row["reviewer_role"] == "independent_scope_and_neutrality_reviewer"
            and row["reviewer_cannot_accept"]
            for row in scope["reviews"]
        ),
        "scope reviewer role/authority mismatch",
    )
    corrections = artifacts["bounded_corrections.json"]
    _require(
        corrections["correction_cycles"] == 1
        and corrections["record_count"] == 37
        and corrections["applied_count"] == 8,
        "bounded correction accounting mismatch",
    )
    _require(
        all(not row["benchmark_used"] for row in corrections["records"]),
        "benchmark leaked into corrections",
    )
    benchmark = artifacts["benchmark_comparison.json"]
    _require(
        benchmark["post_freeze_only"]
        and benchmark["candidate_batch_content_subject_sha256"]
        == batch["content_subject_sha256"],
        "benchmark freeze binding mismatch",
    )
    _require(
        {row["action_id"] for row in benchmark["comparisons"]}
        == set(BENCHMARK_ACTIONS),
        "benchmark action set mismatch",
    )
    _require(
        all(
            row["semantic_relationship"] == "aligned" and row["severity"] == "none"
            for row in benchmark["comparisons"]
        ),
        "benchmark mechanism comparison mismatch",
    )
    sample = artifacts["sample_manifest.json"]
    seed = hashlib.sha256(
        "\n".join(
            [
                batch["content_subject_sha256"],
                M2_SHA256,
                "foushee-justice-action-interpretation-generalization-audit-v2",
            ]
        ).encode()
    ).hexdigest()
    _require(sample["seed_sha256"] == seed, "sample seed mismatch")
    _require(
        len(sample["selected_random_action_ids"]) == 12
        and not (set(sample["selected_random_action_ids"]) & set(BENCHMARK_ACTIONS)),
        "random sample boundary mismatch",
    )
    challenge = {row["action_id"] for row in sample["challenge_actions"]}
    required_challenge = {
        "house:119:2:155",
        "house:119:2:221",
        "house:119:2:273",
        "house:119:2:157",
        "house:119:1:166",
        "house:119:2:278",
        *TARGETED_INITIAL_OMISSIONS,
    }
    _require(required_challenge <= challenge, "challenge set omits required action")
    decision = artifacts["human_decision_template.json"]
    _require(
        decision["unfilled"]
        and decision["top_level_decision"] is None
        and decision["non_authorizing"] is True,
        "decision template is authorizing or filled",
    )
    validate_parity()
    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    runtime_files = [
        ROOT / path
        for path in tracked_runtime
        if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
    ]
    marker = BATCH_ID.encode()
    _require(
        not any(marker in path.read_bytes() for path in runtime_files),
        "V2 candidate batch is referenced by runtime/public selectors",
    )
    return {
        "status": "pass",
        "batch_id": BATCH_ID,
        "action_count": 37,
        "candidate_batch_content_subject_sha256": batch["content_subject_sha256"],
        "status_counts": dict(Counter(row["status"] for row in candidates.values())),
        "confidence_counts": dict(
            Counter(row["confidence"] for row in candidates.values())
        ),
        "material_provision_count": 97,
        "material_limit_count": 33,
        "title_only_exception_count": 0,
        "coverage_severity_counts": dict(
            Counter(row["highest_severity"] for row in coverage["reviews"])
        ),
        "scope_severity_counts": dict(
            Counter(row["highest_severity"] for row in scope["reviews"])
        ),
        "correction_count": corrections["applied_count"],
        "random_sample_count": len(sample["selected_random_action_ids"]),
        "challenge_count": len(sample["challenge_actions"]),
        "parity_state": "pass",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
