"""Fail-closed validation for the detached M3A-R2 V3 review bundle."""

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

from action_interpretation_candidate_v3_data import (  # noqa: E402
    FINAL_DEFINITIONS,
    PRE_CORRECTION_MAJOR_ACTIONS,
    RELATED_ACTION_GROUPS,
)
from build_action_interpretation_candidate_review import (  # noqa: E402
    BENCHMARK_ACTIONS,
    M2_SHA256,
    _sha256,
)
from build_action_interpretation_candidate_review_v3 import (  # noqa: E402
    BATCH_ID,
    OUTPUT_ROOT,
    PACKET_ROOT,
    SAMPLE_LABEL,
    SCHEMA_ROOT,
    V1_ROOT,
    V2_ROOT,
    _file_sha256,
    _preflight_preserved_versions,
    build_freeze,
    build_post_freeze,
)


class CandidateReviewV3ValidationError(ValueError):
    """Raised when the V3 bundle violates a closed review contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateReviewV3ValidationError(message)


def _load(name: str) -> dict[str, Any]:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _verify_seals(value: object, path: str) -> None:
    if isinstance(value, dict):
        if (
            isinstance(value.get("content_subject_sha256"), str)
            and len(value["content_subject_sha256"]) == 64
            and not ("path" in value and "file_sha256" in value)
        ):
            subject = dict(value)
            claimed = subject.pop("content_subject_sha256")
            _require(_sha256(subject) == claimed, f"{path}: content seal mismatch")
        if "candidate_content_subject_sha256" in value and (
            "proposed_exact_action_meaning" in value
        ):
            subject = dict(value)
            claimed = subject.pop("candidate_content_subject_sha256")
            _require(_sha256(subject) == claimed, f"{path}: candidate seal mismatch")
        for key, child in value.items():
            _verify_seals(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _verify_seals(child, f"{path}[{index}]")


def _schema_name(name: str) -> str:
    return name.replace(".json", "_v3.schema.json")


def _validate_schema(instance: object, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema).iter_errors(instance), key=lambda e: list(e.path)
    )
    _require(
        not errors, f"{label}: schema failure: {errors[0].message if errors else ''}"
    )


def _text(candidate: dict[str, Any]) -> str:
    return " ".join(
        [
            candidate.get("proposed_exact_action_meaning") or "",
            *(row["wording"] for row in candidate["material_provisions"]),
            *(row["wording"] for row in candidate["material_limits_and_exceptions"]),
            *(row["wording"] for row in candidate["claim_components"]),
        ]
    ).casefold()


def _candidate_contract(candidate: dict[str, Any]) -> None:
    action_id = candidate["action_id"]
    _require(action_id in FINAL_DEFINITIONS, f"outside governed universe: {action_id}")
    _require(
        candidate["accepted_candidate_used"] is False,
        f"accepted input used: {action_id}",
    )
    _require(
        candidate["benchmark_used"] is False,
        f"benchmark leaked into worker: {action_id}",
    )
    _require(
        candidate["title_only_exception_used"] is False,
        f"title-only candidate: {action_id}",
    )
    if candidate["status"] == "no_safe_candidate":
        _require(
            candidate["proposed_exact_action_meaning"] is None,
            f"no-safe meaning: {action_id}",
        )
        _require(not candidate["claim_components"], f"no-safe claim: {action_id}")
        return
    _require(
        candidate["proposed_exact_action_meaning"].startswith(
            "The House choice was whether to"
        ),
        f"not exact-choice prose: {action_id}",
    )
    _require(candidate["claim_components"], f"missing source-bound claim: {action_id}")
    for row in [
        *candidate["material_provisions"],
        *candidate["material_limits_and_exceptions"],
        *candidate["claim_components"],
    ]:
        _require(
            row["source_id"] and row["locator"] not in {"", "official-title"},
            f"unbound material item: {action_id}",
        )
    if candidate["confidence"] == "high":
        _require(
            candidate["status"] == "proposed",
            f"high-confidence routed candidate: {action_id}",
        )
        _require(
            candidate["coverage_assessment"] == "complete_bounded_summary",
            f"high-confidence incomplete candidate: {action_id}",
        )


def validate_parity(
    *,
    parity_override: dict[str, Any] | None = None,
    byte_overrides: dict[str, bytes] | None = None,
) -> None:
    parity = parity_override or _load("parity_manifest.json")
    byte_overrides = byte_overrides or {}
    _verify_seals(parity, "parity_manifest")
    _require(
        parity["parity_state"] == "pass" and parity["generated_last"],
        "parity finalization gate failed",
    )
    rows = parity["canonical_artifacts"]
    _require(
        parity["referenced_file_count"] == len(rows) + 1, "parity file count mismatch"
    )
    dossier_row = parity["dossier"]
    dossier_bytes = byte_overrides.get(
        dossier_row["path"], (ROOT / dossier_row["path"]).read_bytes()
    )
    seen: set[str] = set()
    for row in rows:
        path = row["path"]
        _require(path not in seen, f"duplicate parity path: {path}")
        seen.add(path)
        data = byte_overrides.get(path, (ROOT / path).read_bytes())
        _require(
            hashlib.sha256(data).hexdigest() == row["file_sha256"],
            f"final-byte mismatch: {path}",
        )
        value = json.loads(data.decode("utf-8"))
        subject = dict(value)
        claimed = subject.pop("content_subject_sha256", None)
        actual = _sha256(subject if claimed is not None else value)
        _require(
            actual == row["content_subject_sha256"], f"content-subject mismatch: {path}"
        )
        _require(path.encode() in dossier_bytes, f"dossier omits artifact path: {path}")
        _require(
            row["content_subject_sha256"].encode() in dossier_bytes,
            f"dossier omits content digest: {path}",
        )
        _require(
            row["file_sha256"].encode() in dossier_bytes,
            f"dossier omits file digest: {path}",
        )
    _require(
        hashlib.sha256(dossier_bytes).hexdigest() == dossier_row["file_sha256"],
        "dossier final-byte mismatch",
    )


def validate_values(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    batch = artifacts["candidate_batch.json"]
    initial = artifacts["initial_candidate_batch.json"]
    expected = artifacts["expected_provision_inventories.json"]
    coverage = artifacts["source_first_coverage_reviews.json"]
    differential = artifacts["related_action_differential_reviews.json"]
    consistency = artifacts["cross_field_consistency_reviews.json"]
    scope = artifacts["scope_neutrality_reviews.json"]
    correction = artifacts["bounded_correction_diff.json"]
    benchmark = artifacts["benchmark_comparison.json"]
    sample = artifacts["sample_manifest.json"]

    _require(
        batch["batch_id"] == BATCH_ID and batch["action_count"] == 37,
        "V3 batch identity/accounting mismatch",
    )
    _require(
        batch["frozen"] and batch["freeze_precedes_benchmark_access"],
        "batch was not frozen before benchmark access",
    )
    _require(
        not batch["accepted"]
        and not batch["production_selectable"]
        and batch["non_authorizing"],
        "V3 entered an authorizing state",
    )
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    initial_by = {row["action_id"]: row for row in initial["candidates"]}
    inventories = {row["action_id"]: row for row in expected["inventories"]}
    governed_ids = set(FINAL_DEFINITIONS)
    _require(
        len(candidates) == 37 and set(candidates) == governed_ids,
        "final candidate membership mismatch",
    )
    _require(
        set(initial_by) == governed_ids and set(inventories) == governed_ids,
        "initial/inventory membership mismatch",
    )
    for candidate in candidates.values():
        _candidate_contract(candidate)

    _require(
        initial["benchmark_inaccessible"] is True,
        "initial workers could access benchmarks",
    )
    _require(
        expected["stage_1_candidate_inaccessible"] is True,
        "stage-1 reviewer could access candidates",
    )
    for inventory in inventories.values():
        _require(
            inventory["candidate_inaccessible_during_inventory_derivation"],
            f"candidate-visible inventory: {inventory['action_id']}",
        )
        expected_ids = [
            row.get("expected_provision_id") or row.get("expected_limit_id")
            for row in [
                *inventory["expected_provisions"],
                *inventory["expected_limits_and_exceptions"],
            ]
        ]
        _require(
            all(
                item_id and item_id.startswith("expected-") for item_id in expected_ids
            ),
            f"candidate IDs define inventory: {inventory['action_id']}",
        )
        _require(
            all(
                row["locator"]
                for row in [
                    *inventory["expected_provisions"],
                    *inventory["expected_limits_and_exceptions"],
                ]
            ),
            f"unbound expected item: {inventory['action_id']}",
        )

    status_counts = Counter(row["status"] for row in candidates.values())
    confidence_counts = Counter(row["confidence"] for row in candidates.values())
    _require(
        status_counts
        == Counter({"proposed": 35, "ambiguous": 1, "no_safe_candidate": 1}),
        "status accounting mismatch",
    )
    _require(
        confidence_counts == Counter({"high": 14, "medium": 21, "low": 2}),
        "confidence accounting mismatch",
    )

    s5 = _text(candidates["house:119:1:23"])
    for phrase in (
        "burglary",
        "theft",
        "larceny",
        "shoplifting",
        "assault of a law-enforcement officer",
        "death or serious bodily injury",
    ):
        _require(phrase in s5, f"S.5 omits exact trigger: {phrase}")
    hr29 = _text(candidates["house:119:1:6"])
    _require(
        "assault of a law-enforcement officer" not in hr29
        and "death or serious bodily injury" not in hr29,
        "H.R.29 absorbed Senate-only triggers",
    )
    hr1156 = _text(candidates["house:119:1:68"])
    _require(
        "four pandemic unemployment programs" in hr1156
        and "three pandemic unemployment programs" not in hr1156,
        "H.R.1156 named-count regression",
    )
    for program in (
        "pandemic unemployment assistance",
        "federal pandemic unemployment compensation",
        "mixed earner unemployment compensation",
        "pandemic emergency unemployment compensation",
    ):
        _require(program in hr1156, f"H.R.1156 omits program: {program}")

    roll155 = candidates["house:119:2:155"]
    _require(
        roll155["status"] == "ambiguous" and roll155["confidence"] == "low",
        "roll 155 ambiguity not preserved",
    )
    _require(
        roll155["source_identity_reconciliation"]["dublin_core_title"].startswith(
            "110 S4465 ES"
        ),
        "roll 155 source conflict hidden",
    )
    roll278 = candidates["house:119:2:278"]
    _require(
        roll278["status"] == "no_safe_candidate"
        and roll278["proposed_exact_action_meaning"] is None,
        "roll 278 abstention not preserved",
    )

    for name, review_rows in (
        ("coverage", coverage["reviews"]),
        ("consistency", consistency["reviews"]),
        ("scope", scope["reviews"]),
    ):
        _require(len(review_rows) == 37, f"{name} review count mismatch")
        for review in review_rows:
            if candidates[review["action_id"]]["status"] == "proposed":
                _require(
                    review[
                        "remaining_severity_after_correction"
                        if name != "scope"
                        else "remaining_severity_after_routing"
                    ]
                    not in {"major", "critical"},
                    f"proposed candidate retains {name} major finding: {review['action_id']}",
                )
    _require(
        all(
            row["stage_1_candidate_inaccessible"] and row["reviewer_cannot_accept"]
            for row in coverage["reviews"]
        ),
        "coverage reviewer independence/authority mismatch",
    )
    _require(
        len(differential["reviews"]) == len(RELATED_ACTION_GROUPS),
        "differential group accounting mismatch",
    )
    _require(
        all(
            row["candidate_blind_primary_generation"]
            and row["remaining_severity_after_correction"] not in {"major", "critical"}
            for row in differential["reviews"]
        ),
        "unresolved related-action differential",
    )
    _require(
        correction["correction_cycle_count"] == 1
        and correction["correction_count"] == 2,
        "global correction cycle mismatch",
    )
    _require(
        {row["action_id"] for row in correction["corrections"]}
        == PRE_CORRECTION_MAJOR_ACTIONS,
        "correction action set mismatch",
    )
    _require(
        correction["benchmark_used"] is False
        and correction["evidence_acquisition_performed"] is False,
        "correction exceeded authority",
    )

    _require(
        benchmark["post_freeze_only"]
        and benchmark["candidate_batch_content_subject_sha256"]
        == batch["content_subject_sha256"],
        "benchmark/freeze binding mismatch",
    )
    _require(
        {row["action_id"] for row in benchmark["comparisons"]}
        == set(BENCHMARK_ACTIONS),
        "benchmark set mismatch",
    )
    _require(
        all(row["severity"] == "none" for row in benchmark["comparisons"]),
        "benchmark comparison finding remains",
    )
    seed = hashlib.sha256(
        f"{batch['content_subject_sha256']}*{M2_SHA256}*{SAMPLE_LABEL}".encode()
    ).hexdigest()
    _require(sample["seed_sha256"] == seed, "V3 sample seed mismatch")
    population = sorted(governed_ids - set(BENCHMARK_ACTIONS))
    expected_sample = sorted(
        population,
        key=lambda action_id: hashlib.sha256(
            f"{seed}\n{action_id}".encode()
        ).hexdigest(),
    )[:12]
    _require(
        sample["selected_random_action_ids"] == expected_sample,
        "random sample is not deterministic",
    )
    _require(
        not (set(expected_sample) & set(BENCHMARK_ACTIONS)),
        "benchmark entered random sample",
    )
    challenge = {row["action_id"] for row in sample["challenge_actions"]}
    _require(
        PRE_CORRECTION_MAJOR_ACTIONS <= challenge,
        "challenge set omits corrected major action",
    )
    _require(
        {group["group_id"] for group in sample["related_action_contrast_sets"]}
        == {group["group_id"] for group in RELATED_ACTION_GROUPS},
        "contrast set mismatch",
    )
    return {
        "status_counts": dict(status_counts),
        "confidence_counts": dict(confidence_counts),
        "expected_provision_count": sum(
            len(row["expected_provisions"]) for row in inventories.values()
        ),
        "expected_limit_count": sum(
            len(row["expected_limits_and_exceptions"]) for row in inventories.values()
        ),
        "coverage_severity_counts": dict(
            Counter(row["highest_severity"] for row in coverage["reviews"])
        ),
        "differential_severity_counts": dict(
            Counter(row["highest_severity"] for row in differential["reviews"])
        ),
        "consistency_severity_counts": dict(
            Counter(row["highest_severity"] for row in consistency["reviews"])
        ),
        "scope_severity_counts": dict(
            Counter(row["highest_severity"] for row in scope["reviews"])
        ),
    }


def validate() -> dict[str, Any]:
    _preflight_preserved_versions()
    build_freeze(check=True)
    build_post_freeze(check=True)
    names = [
        "revision_directive.json",
        "review_contracts.json",
        "related_action_lineage_map.json",
        "evidence_maps.json",
        "expected_provision_inventories.json",
        "initial_candidate_batch.json",
        "source_first_coverage_reviews.json",
        "related_action_differential_reviews.json",
        "cross_field_consistency_reviews.json",
        "scope_neutrality_reviews.json",
        "bounded_correction_diff.json",
        "candidate_batch.json",
        "benchmark_comparison.json",
        "sample_manifest.json",
        "human_decision_template.json",
        "parity_manifest.json",
    ]
    artifacts = {name: _load(name) for name in names}
    for name, artifact in artifacts.items():
        _verify_seals(artifact, name)
        _validate_schema(artifact, SCHEMA_ROOT / _schema_name(name), name)
    packet_schema = SCHEMA_ROOT / "worker_packet_v3.schema.json"
    packets = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(PACKET_ROOT.glob("*.json"))
    ]
    _require(
        len(packets) == 37
        and {row["action_id"] for row in packets} == set(FINAL_DEFINITIONS),
        "worker packet accounting mismatch",
    )
    for packet in packets:
        _verify_seals(packet, packet["action_id"])
        _validate_schema(packet, packet_schema, packet["action_id"])
        serialized = json.dumps(packet, sort_keys=True).casefold()
        for forbidden in packet["worker_input_forbidden"]:
            _require(
                forbidden.casefold()
                not in serialized.replace(
                    json.dumps(packet["worker_input_forbidden"]).casefold(), ""
                ),
                f"worker blindness leak: {packet['action_id']} {forbidden}",
            )
    directive = artifacts["revision_directive.json"]
    _require(
        directive["decision"] == "global_revision_required",
        "revision decision mismatch",
    )
    _require(
        not directive["accepts_any_v1_candidate"]
        and not directive["accepts_any_v2_candidate"]
        and not directive["accepts_any_v3_candidate"],
        "revision directive accepted a candidate",
    )
    decision = artifacts["human_decision_template.json"]
    _require(
        decision["decision_state"] == "empty_pending_human_review"
        and decision["selected_decision"] is None
        and not decision["accepts_any_candidate"],
        "human decision template is filled or authorizing",
    )
    accounting = validate_values(artifacts)
    validate_parity()
    tracked_runtime = subprocess.check_output(
        ["git", "ls-files", "backend", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    marker = BATCH_ID.encode()
    _require(
        not any(
            marker in (ROOT / path).read_bytes()
            for path in tracked_runtime
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "V3 batch entered runtime/public selectors",
    )
    batch = artifacts["candidate_batch.json"]
    return {
        "status": "pass",
        "batch_id": BATCH_ID,
        "action_count": 37,
        "candidate_batch_content_subject_sha256": batch["content_subject_sha256"],
        "candidate_batch_file_sha256": _file_sha256(
            OUTPUT_ROOT / "candidate_batch.json"
        ),
        **accounting,
        "random_sample_count": 12,
        "challenge_count": artifacts["sample_manifest.json"]["challenge_count"],
        "contrast_group_count": artifacts["sample_manifest.json"][
            "contrast_group_count"
        ],
        "parity_state": "pass",
        "v1_root_preserved": _file_sha256(V1_ROOT / "candidate_batch.json"),
        "v2_root_preserved": _file_sha256(V2_ROOT / "candidate_batch.json"),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
