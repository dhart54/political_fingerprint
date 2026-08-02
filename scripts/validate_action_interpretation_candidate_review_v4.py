"""Fail-closed validation for the detached M3A-R3 V4 bundle."""

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

from action_interpretation_candidate_v4_data import (  # noqa: E402
    FINAL_DEFINITIONS,
    TARGETED_CORRECTIONS,
)
from build_action_interpretation_candidate_review import (  # noqa: E402
    BENCHMARK_ACTIONS,
    M2_SHA256,
    _sha256,
)
from build_action_interpretation_candidate_review_v4 import (  # noqa: E402
    BATCH_ID,
    OUTPUT_ROOT,
    PACKET_ROOT,
    SAMPLE_LABEL,
    SCHEMA_ROOT,
    V3_CONTENT_SHA256,
    V3_FILE_SHA256,
    _file_sha256,
    _preflight,
    build_freeze,
    build_post_freeze,
)


class CandidateReviewV4ValidationError(ValueError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise CandidateReviewV4ValidationError(message)


def _load(name: str) -> dict[str, Any]:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _verify_seals(value: object, path: str) -> None:
    if isinstance(value, dict):
        claimed = value.get("content_subject_sha256")
        if (
            isinstance(claimed, str)
            and len(claimed) == 64
            and not ("path" in value and "file_sha256" in value)
        ):
            subject = dict(value)
            subject.pop("content_subject_sha256")
            _require(_sha256(subject) == claimed, f"{path}: content seal mismatch")
        claimed_candidate = value.get("candidate_content_subject_sha256")
        if (
            isinstance(claimed_candidate, str)
            and "proposed_exact_action_meaning" in value
        ):
            subject = dict(value)
            subject.pop("candidate_content_subject_sha256")
            _require(
                _sha256(subject) == claimed_candidate,
                f"{path}: candidate seal mismatch",
            )
        for key, child in value.items():
            _verify_seals(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _verify_seals(child, f"{path}[{index}]")


def _schema_name(name: str) -> str:
    return name.replace(".json", "_v4.schema.json")


def _schema(instance: object, path: Path, label: str) -> None:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    errors = list(Draft7Validator(schema).iter_errors(instance))
    _require(
        not errors, f"{label}: schema failure: {errors[0].message if errors else ''}"
    )


def validate_parity(*, byte_overrides: dict[str, bytes] | None = None) -> None:
    byte_overrides = byte_overrides or {}
    parity = _load("parity_manifest.json")
    _verify_seals(parity, "parity")
    _require(
        parity["parity_state"] == "pass" and parity["generated_last"],
        "parity state/order mismatch",
    )
    _require(
        parity["referenced_file_count"] == len(parity["canonical_artifacts"]) + 1,
        "parity count mismatch",
    )
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
            f"stale dossier pair: {row['path']}",
        )


def validate_values(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    batch = artifacts["candidate_batch.json"]
    ledgers = artifacts["material_scope_ledgers.json"]
    material = artifacts["material_scope_closure_reviews.json"]
    quantitative = artifacts["quantitative_enumeration_closure_reviews.json"]
    amendments = artifacts["textual_amendment_closure_reviews.json"]
    consistency = artifacts["cross_field_consistency_reviews.json"]
    corrections = artifacts["bounded_correction_diff.json"]
    _require(
        batch["batch_id"] == BATCH_ID and batch["action_count"] == 37,
        "batch accounting mismatch",
    )
    _require(
        batch["frozen"] and batch["freeze_precedes_benchmark_access"],
        "freeze boundary missing",
    )
    _require(
        not batch["accepted"]
        and not batch["canonical"]
        and not batch["production_selectable"],
        "V4 became authorizing",
    )
    candidates = {row["action_id"]: row for row in batch["final_candidates"]}
    ledger_by = {row["action_id"]: row for row in ledgers["ledgers"]}
    _require(
        set(candidates) == set(FINAL_DEFINITIONS) == set(ledger_by),
        "governed membership mismatch",
    )
    _require(
        ledgers["candidate_blind"]
        and all(
            row["candidate_inaccessible_during_derivation"]
            for row in ledger_by.values()
        ),
        "material ledger was candidate-visible",
    )
    allowed_dispositions = {
        "represented_exactly_in_meaning",
        "represented_boundedly_in_meaning",
        "represented_in_limit_or_exception",
        "intentionally_omitted_nonmaterial",
        "unresolved_and_disclosed",
        "missing_blocking_candidate",
    }
    review_by = {row["action_id"]: row for row in material["reviews"]}
    for action_id, ledger in ledger_by.items():
        items = ledger["items"]
        dispositions = review_by[action_id]["item_dispositions"]
        _require(
            len(items) == len(dispositions)
            and {row["item_id"] for row in items}
            == {row["item_id"] for row in dispositions},
            f"incomplete item disposition: {action_id}",
        )
        _require(
            all(
                row["final_disposition"] in allowed_dispositions for row in dispositions
            ),
            f"invalid item disposition: {action_id}",
        )
        if candidates[action_id]["status"] == "proposed":
            _require(
                not any(
                    row["final_disposition"] == "missing_blocking_candidate"
                    for row in dispositions
                ),
                f"proposed candidate missing item: {action_id}",
            )
    for artifact in (material, quantitative, amendments, consistency):
        _require(
            len(artifact["reviews"]) == 37,
            f"review accounting mismatch: {artifact['artifact_id']}",
        )
        _require(
            all(
                row["remaining_severity_after_correction"] not in {"major", "critical"}
                for row in artifact["reviews"]
            ),
            f"remaining closure finding: {artifact['artifact_id']}",
        )
    _require(
        corrections["correction_cycle_count"] == 1
        and {row["action_id"] for row in corrections["corrections"]}
        == TARGETED_CORRECTIONS,
        "bounded correction mismatch",
    )
    _require(
        not corrections["evidence_acquisition_performed"]
        and not corrections["benchmark_used"],
        "correction exceeded authority",
    )

    def corpus(action_id: str) -> str:
        row = candidates[action_id]
        return (
            (row["proposed_exact_action_meaning"] or "")
            + " "
            + " ".join(row["limitations"])
        ).casefold()

    text227 = corpus("house:119:2:227")
    for phrase in (
        "age 65 or older",
        "age 18 or older",
        "mental or physical impairment",
        "15 business days",
        "10-business-day",
        "government extension",
        "trusted-contact",
        "sec recommendations",
    ):
        _require(phrase in text227, f"H.R.2478 omits {phrase}")
    text157 = corpus("house:119:2:157")
    _require(
        "$5,000" in text157 and "12 months" in text157, "H.R.2853 threshold missing"
    )
    text42 = corpus("house:119:1:42")
    for phrase in ("two years", "five to 20 years", "10 years to life"):
        _require(phrase in text42, f"H.R.35 penalty missing: {phrase}")
    text128 = corpus("house:119:1:128")
    _require(
        "any magazine and" in text128 and "exact legal effect" in text128,
        "H.R.2243 amendment disclosure missing",
    )
    _require(
        candidates["house:119:1:128"]["status"] == "ambiguous"
        and candidates["house:119:1:128"]["confidence"] == "low",
        "H.R.2243 confidence/routing mismatch",
    )
    _require(
        candidates["house:119:2:155"]["status"] == "ambiguous",
        "roll 155 ambiguity missing",
    )
    _require(
        candidates["house:119:2:278"]["status"] == "no_safe_candidate",
        "roll 278 abstention missing",
    )
    _require(
        Counter(row["status"] for row in candidates.values())
        == Counter({"proposed": 34, "ambiguous": 2, "no_safe_candidate": 1}),
        "status accounting mismatch",
    )
    return {
        "status_counts": dict(Counter(row["status"] for row in candidates.values())),
        "confidence_counts": dict(
            Counter(row["confidence"] for row in candidates.values())
        ),
        "material_item_count": sum(len(row["items"]) for row in ledger_by.values()),
        "material_item_class_counts": dict(
            Counter(
                item["item_class"]
                for row in ledger_by.values()
                for item in row["items"]
            )
        ),
        "quantitative_fact_count": sum(
            len(item["quantitative_or_enumerated_values"])
            for row in ledger_by.values()
            for item in row["items"]
        ),
        "textual_amendment_count": sum(
            item["item_class"] == "textual_amendment"
            for row in ledger_by.values()
            for item in row["items"]
        ),
    }


def validate() -> dict[str, Any]:
    _preflight()
    build_freeze(check=True)
    build_post_freeze(check=True)
    names = [
        "revision_directive.json",
        "evidence_maps.json",
        "material_scope_ledgers.json",
        "initial_candidate_batch.json",
        "material_scope_closure_reviews.json",
        "quantitative_enumeration_closure_reviews.json",
        "textual_amendment_closure_reviews.json",
        "related_action_differential_reviews.json",
        "scope_neutrality_reviews.json",
        "cross_field_consistency_reviews.json",
        "bounded_correction_diff.json",
        "candidate_batch.json",
        "benchmark_comparison.json",
        "sample_manifest.json",
        "human_decision_template.json",
        "parity_manifest.json",
    ]
    artifacts = {name: _load(name) for name in names}
    for name, value in artifacts.items():
        _verify_seals(value, name)
        _schema(value, SCHEMA_ROOT / _schema_name(name), name)
    packets = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in PACKET_ROOT.glob("*.json")
    ]
    _require(len(packets) == 37, "worker packet count mismatch")
    packet_schema = SCHEMA_ROOT / "worker_packet_v4.schema.json"
    for packet in packets:
        _verify_seals(packet, packet["action_id"])
        _schema(packet, packet_schema, packet["action_id"])
        serialized = json.dumps(packet).casefold()
        _require(
            "member_party"
            not in serialized.replace(
                json.dumps(packet["worker_input_forbidden"]).casefold(), ""
            ),
            f"worker party leak: {packet['action_id']}",
        )
    directive = artifacts["revision_directive.json"]
    _require(
        directive["decision"] == "global_revision_required"
        and directive["v3_content_subject_sha256"] == V3_CONTENT_SHA256
        and directive["v3_final_file_sha256"] == V3_FILE_SHA256,
        "revision binding mismatch",
    )
    _require(
        not directive["accepts_any_prior_candidate"]
        and not directive["human_acceptance_receipt"],
        "directive became acceptance",
    )
    decision = artifacts["human_decision_template.json"]
    _require(
        decision["selected_decision"] is None and not decision["accepts_any_candidate"],
        "decision template filled",
    )
    accounting = validate_values(artifacts)
    benchmark = artifacts["benchmark_comparison.json"]
    _require(
        benchmark["post_freeze_only"]
        and all(row["severity"] == "none" for row in benchmark["comparisons"]),
        "benchmark finding or blindness failure",
    )
    _require(
        {row["action_id"] for row in benchmark["comparisons"]}
        == set(BENCHMARK_ACTIONS),
        "benchmark set mismatch",
    )
    sample = artifacts["sample_manifest.json"]
    batch = artifacts["candidate_batch.json"]
    seed = hashlib.sha256(
        f"{batch['content_subject_sha256']}*{M2_SHA256}*{SAMPLE_LABEL}".encode()
    ).hexdigest()
    _require(
        sample["seed_sha256"] == seed
        and len(sample["selected_random_action_ids"]) == 12,
        "sample seed/count mismatch",
    )
    _require(
        TARGETED_CORRECTIONS <= set(sample["material_detail_challenge_action_ids"]),
        "material-detail sample missing corrected action",
    )
    validate_parity()
    tracked = subprocess.check_output(
        ["git", "ls-files", "backend", "frontend"], cwd=ROOT, text=True
    ).splitlines()
    _require(
        not any(
            BATCH_ID.encode() in (ROOT / path).read_bytes()
            for path in tracked
            if Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".json"}
        ),
        "V4 entered runtime/public selectors",
    )
    return {
        "status": "pass",
        "batch_id": BATCH_ID,
        "action_count": 37,
        "candidate_batch_content_subject_sha256": batch["content_subject_sha256"],
        "candidate_batch_file_sha256": _file_sha256(
            OUTPUT_ROOT / "candidate_batch.json"
        ),
        **accounting,
        "materiality_counts": dict(
            Counter(
                item["materiality_state"]
                for ledger in artifacts["material_scope_ledgers.json"]["ledgers"]
                for item in ledger["items"]
            )
        ),
        "correction_count": artifacts["bounded_correction_diff.json"][
            "correction_count"
        ],
        "random_sample_count": 12,
        "material_detail_count": len(sample["material_detail_challenge_action_ids"]),
        "parity_state": "pass",
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
