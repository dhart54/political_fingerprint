"""Validate the detached, non-authorizing M3A candidate review bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_action_interpretation_candidate_review import (  # noqa: E402
    BATCH_ID,
    BENCHMARK_ACTIONS,
    M2_SHA256,
    OUTPUT_ROOT,
    PACKET_ROOT,
    _file_sha256,
    _sha256,
    build_post_freeze,
)


class CandidateReviewValidationError(ValueError):
    """Raised when the M3A bundle fails closed validation."""


def _load(name: str) -> dict[str, object]:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateReviewValidationError(message)


def _validate_artifact_hash(artifact: dict[str, object], name: str) -> None:
    subject = dict(artifact)
    claimed = subject.pop("artifact_sha256")
    _require(_sha256(subject) == claimed, f"{name}: artifact SHA-256 mismatch")


def validate() -> dict[str, object]:
    evidence = _load("evidence_maps.json")
    batch = _load("candidate_batch.json")
    reviews = _load("adversarial_reviews.json")
    benchmark = _load("benchmark_comparison.json")
    sample = _load("sample_manifest.json")
    decision = _load("human_decision_template.json")
    parity = _load("parity_manifest.json")
    artifacts = {
        "evidence_maps": evidence,
        "candidate_batch": batch,
        "adversarial_reviews": reviews,
        "benchmark_comparison": benchmark,
        "sample_manifest": sample,
        "human_decision_template": decision,
        "parity_manifest": parity,
    }
    schema_names = {
        "evidence_maps": "evidence_maps_v1.schema.json",
        "candidate_batch": "candidate_batch_v1.schema.json",
        "adversarial_reviews": "adversarial_reviews_v1.schema.json",
        "benchmark_comparison": "benchmark_comparison_v1.schema.json",
        "sample_manifest": "sample_manifest_v1.schema.json",
        "human_decision_template": "human_decision_template_v1.schema.json",
        "parity_manifest": "parity_manifest_v1.schema.json",
    }
    for key, artifact in artifacts.items():
        schema = json.loads(
            (OUTPUT_ROOT / "schemas" / schema_names[key]).read_text(encoding="utf-8")
        )
        errors = sorted(
            Draft7Validator(schema).iter_errors(artifact),
            key=lambda error: list(error.path),
        )
        _require(
            not errors, f"{key}: schema failure: {errors[0].message if errors else ''}"
        )
        _validate_artifact_hash(artifact, key)

    _require(batch["batch_id"] == BATCH_ID, "candidate batch identity mismatch")
    _require(
        batch["frozen"] and batch["freeze_precedes_benchmark_access"],
        "candidate batch is not validly frozen",
    )
    _require(
        batch["non_authorizing"] and batch["non_public"] and not batch["accepted"],
        "candidate authority boundary failed",
    )
    primary = {row["action_id"]: row for row in batch["primary_candidates"]}
    final = {row["action_id"]: row for row in batch["final_candidates"]}
    maps = {row["action_id"]: row for row in evidence["evidence_maps"]}
    review_by = {row["action_id"]: row for row in reviews["reviews"]}
    _require(
        len(primary) == len(final) == len(maps) == len(review_by) == 37,
        "37-action accounting failed",
    )
    _require(
        set(primary) == set(final) == set(maps) == set(review_by),
        "cross-artifact action set mismatch",
    )
    for action_id, candidate in final.items():
        subject = dict(candidate)
        claimed = subject.pop("candidate_sha256")
        _require(_sha256(subject) == claimed, f"{action_id}: candidate hash mismatch")
        _require(
            candidate["evidence_map_sha256"] == maps[action_id]["evidence_map_sha256"],
            f"{action_id}: evidence map binding mismatch",
        )
        source_ids = {source["source_id"] for source in maps[action_id]["sources"]}
        for claim in candidate["claim_components"]:
            _require(
                claim["source_id"] in source_ids, f"{action_id}: unbound claim source"
            )
        if candidate["status"] == "no_safe_candidate":
            _require(
                candidate["proposed_exact_action_meaning"] is None
                and not candidate["claim_components"],
                f"{action_id}: unsafe candidate retains substantive prose",
            )
        else:
            _require(
                bool(candidate["proposed_exact_action_meaning"])
                and bool(candidate["claim_components"]),
                f"{action_id}: candidate lacks source-bound meaning",
            )
        packet_path = PACKET_ROOT / (action_id.replace(":", "_") + ".json")
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        packet_subject = dict(packet)
        packet_subject.pop("schema_version")
        packet_subject.pop("packet_id")
        claimed_packet = packet_subject.pop("input_packet_sha256")
        _require(
            _sha256(packet_subject)
            == claimed_packet
            == maps[action_id]["input_packet_sha256"],
            f"{action_id}: input-packet hash mismatch",
        )
        keys = set(packet)
        _require(
            not keys.intersection(packet["worker_input_forbidden"]),
            f"{action_id}: forbidden packet field present",
        )
        _require(
            "accepted_semantic_reference"
            not in packet_path.read_text(encoding="utf-8"),
            f"{action_id}: accepted benchmark leaked into packet",
        )

    batch_subject = {
        "batch_id": BATCH_ID,
        "action_count": 37,
        "final_candidate_hashes": [
            row["candidate_sha256"] for row in batch["final_candidates"]
        ],
        "evidence_maps_artifact_sha256": evidence["artifact_sha256"],
        "adversarial_reviews_artifact_sha256": reviews["artifact_sha256"],
    }
    _require(
        _sha256(batch_subject) == batch["candidate_batch_subject_sha256"],
        "batch subject SHA-256 mismatch",
    )
    _require(
        len(batch["corrections"]) == 2
        and all(
            not row["benchmark_used"] and row["correction_cycle"] == 1
            for row in batch["corrections"]
        ),
        "bounded correction contract failed",
    )
    _require(
        {row["action_id"] for row in benchmark["comparisons"]} == BENCHMARK_ACTIONS,
        "benchmark comparison set mismatch",
    )
    _require(
        all(
            row["evaluation_only_no_candidate_mutation"]
            for row in benchmark["comparisons"]
        ),
        "benchmark evaluation boundary failed",
    )

    population = sample["ordered_population"]
    _require(
        len(population) == 30 and not set(population).intersection(BENCHMARK_ACTIONS),
        "random population blindness failed",
    )
    seed_input = "\n".join(
        [
            batch["candidate_batch_subject_sha256"],
            M2_SHA256,
            "foushee-justice-action-interpretation-generalization-audit-v1",
        ]
    )
    seed_sha = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
    ranked = sorted(
        population,
        key=lambda action_id: (
            hashlib.sha256(f"{seed_sha}\n{action_id}".encode()).hexdigest(),
            action_id,
        ),
    )
    _require(
        sample["seed_input"] == seed_input
        and sample["seed_sha256"] == seed_sha
        and sample["selected_random_action_ids"] == ranked[:12],
        "deterministic random selection mismatch",
    )
    challenge = {
        row["action_id"]: row["inclusion_reasons"]
        for row in sample["challenge_actions"]
    }
    _require(
        {"house:119:2:155", "house:119:2:221", "house:119:1:166"}.issubset(challenge),
        "mandatory challenge actions missing",
    )
    for action_id, candidate in final.items():
        if (
            candidate["confidence"] == "low"
            or candidate["status"] != "proposed"
            or review_by[action_id]["highest_severity"] in {"major", "critical"}
        ):
            _require(
                action_id in challenge,
                f"{action_id}: required challenge inclusion missing",
            )

    _require(
        decision["unfilled"] and decision["top_level_decision"] is None,
        "human decision template is not empty",
    )
    dossier = OUTPUT_ROOT / "human_review_dossier.md"
    _require(
        _file_sha256(dossier) == parity["dossier_sha256"],
        "Markdown digest/parity mismatch",
    )
    build_post_freeze(check=True)
    review_state = (
        ROOT
        / "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json"
    )
    _require(
        "interpretation_candidates" not in review_state.read_text(encoding="utf-8"),
        "canonical review state selects candidate artifacts",
    )
    return {
        "status": "pass",
        "action_count": 37,
        "candidate_batch_subject_sha256": batch["candidate_batch_subject_sha256"],
        "random_sample_count": 12,
        "challenge_count": len(challenge),
        "correction_count": len(batch["corrections"]),
        "parity_state": parity["parity_state"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
