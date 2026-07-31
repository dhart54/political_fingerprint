from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_full_record_terminology import check, check_text  # noqa: E402
from backend.app.semantic_ir.compiler import (  # noqa: E402
    compile_semantic_ir,
    project_compiler_input,
)
from scripts.validate_full_record_issue_interpretation import (  # noqa: E402
    FullRecordValidationError,
    _file_digest_matches,
    compute_universe_sha256,
    interpretation_digest,
    validate_review,
)

REVIEW_PATH = (
    ROOT
    / "docs/editorial/full_record_reviews/"
    "f000477_justice_public_safety_119_review_state_v1.json"
)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _ref(
    path: Path,
    schema_version: str,
    artifact_id: str,
    *,
    subject_sha256: str | None = None,
    bound_receipt_id: str | None = None,
) -> dict[str, str | None]:
    return {
        "path": path.name,
        "schema_version": schema_version,
        "sha256": _file_digest(path),
        "artifact_id": artifact_id,
        "subject_sha256": subject_sha256,
        "bound_receipt_id": bound_receipt_id,
    }


def _review() -> dict[str, Any]:
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def _synthetic_review(
    root: Path,
    *,
    outcome: str = "uniform_direction",
    claim_class: str = "full_issue_synthesis",
    semantic_tier: str = "reviewed_conclusion",
) -> dict[str, Any]:
    cases = json.loads(
        (ROOT / "docs/semantic_ir/accepted/development_cases.json").read_text(
            encoding="utf-8"
        )
    )["cases"]
    template = cases[5] if outcome == "no_safe_synthesis" else cases[1]
    serialized = json.dumps(template)
    serialized = serialized.replace("F000477", "T000001")
    serialized = serialized.replace("ECONOMY_COST_OF_LIVING", "SYNTHETIC_TEST")
    serialized = serialized.replace("JUSTICE_PUBLIC_SAFETY", "SYNTHETIC_TEST")
    serialized = serialized.replace("house:119:1:", "house:999:1:")
    compiled_ir = compile_semantic_ir(project_compiler_input(json.loads(serialized)))
    compiled_member = compiled_ir["members"][0]
    propositions = compiled_member["proposition_graph"]["propositions"]
    action_ids = sorted(
        {
            action_id
            for proposition in propositions
            if proposition["semantic_role"] == "behavioral"
            for action_id in proposition["evidence_action_ids"]
        }
        | {
            item["action_id"]
            for item in compiled_member["action_accounting"]["non_proposition_reasons"]
        }
    )
    action_direction: dict[str, str] = {}
    action_episode: dict[str, str] = {}
    for proposition in propositions:
        if proposition["semantic_role"] != "behavioral":
            continue
        for action_id in proposition["evidence_action_ids"]:
            action_direction[action_id] = proposition["direction"]
            action_episode[action_id] = proposition["evidence_episode_ids"][0]

    actions: list[dict[str, Any]] = []
    for index, action_id in enumerate(action_ids, start=1):
        direction = action_direction.get(action_id, "support")
        member_action = "Nay" if direction == "opposition" else "Yea"
        episode_id = action_episode.get(action_id, f"synthetic-episode-{index}")
        interpretation: dict[str, Any] = {
            "interpretation_id": f"action-interpretation:synthetic:999:{index}",
            "action_meaning_id": f"action-meaning:synthetic:999:{index}",
            "exact_action_meaning": f"Synthetic exact action {index}.",
            "member_action": member_action,
            "evidence_status": "official_record_resolved",
            "service_status": "in_service",
            "vote_source_refs": [f"synthetic-roll-source-{index}"],
            "action_meaning_source_refs": [f"synthetic-meaning-source-{index}"],
            "episode_id": episode_id,
            "review_state": "human_reviewed",
            "interpretation_receipt_refs": [
                f"synthetic-interpretation-receipt-{index}"
            ],
            "interpretation_sha256": "0" * 64,
        }
        interpretation["interpretation_sha256"] = interpretation_digest(
            interpretation
        )
        actions.append(
            {
                "action_id": action_id,
                "action_date": f"2099-01-{index + 1:02d}",
                "disposition": "interpreted_substantive_directional",
                "review_friendliness": {
                    "substantive_candidate": True,
                    "stable_canonical_action_identity": True,
                    "service_status": "in_service",
                    "member_action": member_action,
                    "exact_action_issue_eligibility": "eligible",
                    "action_meaning_evidence": "sufficient",
                    "vote_provenance": "authoritative",
                    "action_meaning_provenance": "authoritative",
                    "source_conflict_state": "none",
                    "is_review_friendly": True,
                },
                "episode_id": episode_id,
                "episode_membership_state": "established",
                "episode_membership_reason": None,
                "interpretation": interpretation,
            }
        )
    episodes: list[dict[str, Any]] = []
    for episode_id in sorted(set(action_episode.values())):
        episode_actions = [
            action for action in actions if action["episode_id"] == episode_id
        ]
        directions = {
            action_direction[action["action_id"]] for action in episode_actions
        }
        episode_outcome = (
            "directional_opposition"
            if directions == {"opposition"}
            else "directional_support"
            if directions == {"support"}
            else "mixed_or_qualified"
        )
        episodes.append(
            {
                "episode_id": episode_id,
                "action_ids": [action["action_id"] for action in episode_actions],
                "chronological_action_ids": [
                    action["action_id"] for action in episode_actions
                ],
                "latest_action_date": episode_actions[-1]["action_date"],
                "policy_question": f"Synthetic policy question for {episode_id}.",
                "action_interpretation_refs": [
                    {
                        "action_id": action["action_id"],
                        "interpretation_id": action["interpretation"][
                            "interpretation_id"
                        ],
                        "interpretation_sha256": action["interpretation"][
                            "interpretation_sha256"
                        ],
                    }
                    for action in episode_actions
                ],
                "member_record": [
                    {
                        "action_id": action["action_id"],
                        "member_action": action["interpretation"]["member_action"],
                    }
                    for action in episode_actions
                ],
                "outcome": episode_outcome,
                "contrary_or_limiting_evidence": [],
                "source_completeness": "complete",
                "source_refs": [
                    source
                    for action in episode_actions
                    for source in (
                        action["interpretation"]["vote_source_refs"][0],
                        action["interpretation"]["action_meaning_source_refs"][0],
                    )
                ],
                "completion_state": "complete",
                "unresolved_action_ids": [],
            }
        )
    eligible = outcome != "no_safe_synthesis"
    labels = ["Full review complete", "Vote receipts available"]
    teaser: dict[str, str] | None = {
        "text": "Synthetic full-record conclusion.",
        "valid_scope": "full_defined_issue_record",
    }
    blockers: list[str] = []
    if claim_class == "full_issue_synthesis":
        labels.insert(1, "Full issue interpretation available")
    elif claim_class == "full_review_no_common_throughline":
        labels.insert(1, "No common throughline found")
    else:
        labels.insert(1, "No safe synthesis available")
        teaser = None
        blockers = ["no_safe_synthesis"]
    review: dict[str, Any] = {
        "schema_version": "full_record_issue_interpretation_v1",
        "review_id": "full-review:synthetic:999:v1",
        "subject": {
            "member_id": "T000001",
            "issue_id": "SYNTHETIC_TEST",
            "congress_scope": [999],
        },
        "axes": {
            "semantic_tier": semantic_tier,
            "review_scope": "full_defined_issue_record",
            "review_completion_state": "complete",
            "public_claim_class": claim_class,
        },
        "issue_universe": {
            "snapshot_id": "issue-universe:synthetic:999:v1",
            "snapshot_sha256": "0" * 64,
            "definition": "Separately governed synthetic full universe.",
            "as_of_date": "2099-01-02",
            "action_ids": action_ids,
            "source_refs": ["synthetic-acquisition"],
        },
        "action_accounting": actions,
        "episodes": episodes,
        "synthesis": {
            "outcome": outcome,
            "full_record_action_accounting": "passed",
            "all_interpreted_episode_outcomes_supplied": True,
            "contradictory_and_mixed_evidence_retained": True,
            "source_boundaries": "resolved",
            "semantic_validation": "passed",
            "human_editorial_review": "approved",
            "human_approval_receipt_refs": ["approval.json"],
            "full_issue_synthesis_eligible": eligible,
            "eligibility_blockers": blockers,
        },
        "benchmark": {
            "benchmark_sample_available": False,
            "role": "no_benchmark",
            "benchmark_refs": [],
            "confers_full_record_scope": False,
            "confers_full_record_completion": False,
        },
        "historical_publication": {
            "state": "none",
            "artifact_id": None,
            "effective_semantic_tier": None,
            "publication_receipt_refs": [],
            "historical_truth_note": "Synthetic test authority only.",
            "mutated_by_this_record": False,
        },
        "frontend_state": {
            "review_scope": "full_defined_issue_record",
            "review_completion_state": "complete",
            "public_claim_class": claim_class,
            "total_recorded_actions": len(actions),
            "review_friendly_actions": len(actions),
            "interpreted_actions": len(actions),
            "unresolved_actions": 0,
            "procedural_context_actions": 0,
            "present_actions": 0,
            "not_voting_actions": 0,
            "complete_episode_count": len(episodes),
            "partial_episode_count": 0,
            "full_issue_synthesis_eligible": eligible,
            "benchmark_sample_available": False,
            "conclusion_teaser": teaser,
            "available_labels": labels,
        },
        "external_authority": {},
        "provenance": {
            "contract_path": "docs/methodology/full_record_issue_interpretation_v1.md",
            "schema_path": "docs/methodology/full_record_issue_interpretation_v1.schema.json",
            "created_from_repository_commit": "1" * 40,
            "source_refs": ["synthetic:test-authority"],
            "protected_files": [],
        },
    }
    review["issue_universe"]["snapshot_sha256"] = compute_universe_sha256(review)

    acquisition = root / "acquisition.json"
    _write(acquisition, {"schema": "synthetic_acquisition_v1", "actions": action_ids})
    manifest = {
        "schema_version": "full_issue_universe_manifest_v1",
        "manifest_id": "full-universe:synthetic:999:v1",
        "manifest_version": 1,
        "subject": review["subject"],
        "boundary": {
            "sessions": [1],
            "start_date": "2099-01-01",
            "end_date": "2099-01-02",
            "as_of_date": "2099-01-02",
            "chambers": ["house"],
            "service_boundary": "Synthetic member in service for the full test interval.",
        },
        "rules": {
            "inclusion": ["Every acquired exact action in SYNTHETIC_TEST."],
            "exclusion": ["Procedural controls."],
        },
        "source_manifests": [
            {
                "artifact_id": "synthetic-acquisition-v1",
                "path": acquisition.name,
                "sha256": _file_digest(acquisition),
            }
        ],
        "action_ids": action_ids,
        "action_count": len(action_ids),
        "action_set_sha256": _digest(action_ids),
        "snapshot_source_commit": "2" * 40,
        "universe_subject_sha256": "0" * 64,
    }
    manifest["universe_subject_sha256"] = _digest(
        {k: v for k, v in manifest.items() if k != "universe_subject_sha256"}
    )
    manifest_path = root / "universe.json"
    _write(manifest_path, manifest)
    universe_receipt = {
        "schema_version": "full_issue_universe_authority_receipt_v1",
        "receipt_id": "universe-authority:synthetic:999:v1",
        "manifest_id": manifest["manifest_id"],
        "manifest_sha256": _file_digest(manifest_path),
        "member_id": review["subject"]["member_id"],
        "issue_id": review["subject"]["issue_id"],
        "review_scope": "full_defined_issue_record",
        "boundary": manifest["boundary"],
        "boundary_sha256": _digest(manifest["boundary"]),
        "action_set_sha256": manifest["action_set_sha256"],
        "action_count": len(action_ids),
        "source_manifest_identities": ["synthetic-acquisition-v1"],
        "universe_subject_sha256": manifest["universe_subject_sha256"],
        "reviewer": {
            "reviewer_id": "reviewer:synthetic-test",
            "authority": "full_issue_universe_review_authority_v1",
        },
        "decision_timestamp": "2099-01-03T12:00:00+00:00",
        "decision": "approved_complete_issue_universe",
    }
    universe_receipt_path = root / "universe-receipt.json"
    _write(universe_receipt_path, universe_receipt)
    compiled_path = root / "compiled-ir.json"
    _write(compiled_path, compiled_ir)
    compiled_proposition_ids = [
        proposition["proposition_id"] for proposition in propositions
    ]
    semantic = {
        "schema_version": "full_record_semantic_artifact_v1",
        "artifact_id": "full-semantic:synthetic:999:v1",
        "member_id": review["subject"]["member_id"],
        "issue_id": review["subject"]["issue_id"],
        "universe_manifest_id": manifest["manifest_id"],
        "universe_subject_sha256": manifest["universe_subject_sha256"],
        "action_accounting_sha256": _digest(review["action_accounting"]),
        "episode_set_sha256": _digest(review["episodes"]),
        "semantic_tier": semantic_tier,
        "synthesis_outcome": outcome,
        "compiled_ir_path": compiled_path.name,
        "compiled_ir_sha256": _file_digest(compiled_path),
        "proposition_ids": compiled_proposition_ids,
        "conclusion_plan": compiled_member["composition"]["conclusion_plan"],
        "semantic_subject_sha256": "0" * 64,
    }
    semantic["semantic_subject_sha256"] = _digest(
        {k: v for k, v in semantic.items() if k != "semantic_subject_sha256"}
    )
    semantic_path = root / "semantic.json"
    _write(semantic_path, semantic)
    validation = {
        "schema_version": "full_record_semantic_validation_receipt_v1",
        "receipt_id": "semantic-validation:synthetic:999:v1",
        "universe_manifest_id": manifest["manifest_id"],
        "universe_subject_sha256": manifest["universe_subject_sha256"],
        "semantic_artifact_id": semantic["artifact_id"],
        "semantic_artifact_sha256": _file_digest(semantic_path),
        "action_accounting_sha256": semantic["action_accounting_sha256"],
        "episode_set_sha256": semantic["episode_set_sha256"],
        "semantic_tier": semantic_tier,
        "synthesis_outcome": outcome,
        "validator": {
            "tool_id": "scripts/validate_full_record_issue_interpretation.py",
            "version": "full_record_validator_v1",
        },
        "validation_run_id": "synthetic-validation-run-v1",
        "status": "passed",
        "blockers": [],
    }
    validation_path = root / "validation.json"
    _write(validation_path, validation)
    approval = {
        "schema_version": "full_record_synthesis_approval_receipt_v1",
        "receipt_id": "full-synthesis-approval:synthetic:999:v1",
        "member_id": review["subject"]["member_id"],
        "issue_id": review["subject"]["issue_id"],
        "review_scope": "full_defined_issue_record",
        "universe_manifest_id": manifest["manifest_id"],
        "universe_manifest_sha256": _file_digest(manifest_path),
        "semantic_artifact_id": semantic["artifact_id"],
        "semantic_artifact_sha256": _file_digest(semantic_path),
        "semantic_validation_receipt_id": validation["receipt_id"],
        "semantic_validation_receipt_sha256": _file_digest(validation_path),
        "synthesis_outcome": outcome,
        "public_claim_class": claim_class,
        "presentation_subject_sha256": _digest(
            {
                "conclusion_teaser": review["frontend_state"]["conclusion_teaser"],
                "available_labels": review["frontend_state"]["available_labels"],
            }
        ),
        "wording_ids": [] if teaser is None else ["wording:synthetic"],
        "mapping_ids": [] if teaser is None else ["mapping:synthetic"],
        "limitation_ids": ["limitation:synthetic"],
        "provenance_ids": ["provenance:synthetic"],
        "reviewer": {
            "reviewer_id": "reviewer:synthetic-test",
            "authority": "full_record_synthesis_review_authority_v1",
        },
        "decision_timestamp": "2099-01-04T12:00:00+00:00",
        "decision": "approved",
    }
    approval_path = root / "approval.json"
    _write(approval_path, approval)
    review["external_authority"] = {
        "universe_manifest": _ref(
            manifest_path,
            manifest["schema_version"],
            manifest["manifest_id"],
            subject_sha256=manifest["universe_subject_sha256"],
            bound_receipt_id=universe_receipt["receipt_id"],
        ),
        "universe_authority_receipt": _ref(
            universe_receipt_path,
            universe_receipt["schema_version"],
            universe_receipt["receipt_id"],
        ),
        "semantic_artifact": _ref(
            semantic_path,
            semantic["schema_version"],
            semantic["artifact_id"],
            subject_sha256=manifest["universe_subject_sha256"],
            bound_receipt_id=validation["receipt_id"],
        ),
        "semantic_validation_receipt": _ref(
            validation_path, validation["schema_version"], validation["receipt_id"]
        ),
        "human_approval_receipt": _ref(
            approval_path, approval["schema_version"], approval["receipt_id"]
        ),
    }
    return review


class ContractTests(unittest.TestCase):
    def test_test_only_authority_requires_explicit_test_opt_in(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "backend/tests") as temp:
            root = Path(temp)
            review = _synthetic_review(root)
            with self.assertRaisesRegex(FullRecordValidationError, "test authority"):
                validate_review(review, authority_root=root)

    def test_committed_benchmark_state_validates_without_full_authority(self) -> None:
        review = _review()
        self.assertEqual(validate_review(review)["action_count"], 7)
        self.assertTrue(all(value is None for value in review["external_authority"].values()))

    def test_relabelled_benchmark_cannot_self_attest_full_scope(self) -> None:
        review = _review()
        review["axes"]["review_scope"] = "full_defined_issue_record"
        review["issue_universe"]["snapshot_sha256"] = compute_universe_sha256(review)
        with self.assertRaisesRegex(FullRecordValidationError, "requires universe_manifest"):
            validate_review(review)

    def test_independently_attested_synthetic_full_universe_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            review = _synthetic_review(Path(temp))
            validate_review(review, authority_root=Path(temp), allow_test_authority=True)

    def test_universe_receipt_for_another_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review = _synthetic_review(root)
            path = root / "universe-receipt.json"
            receipt = json.loads(path.read_text())
            receipt["manifest_id"] = "full-universe:another:v1"
            _write(path, receipt)
            review["external_authority"]["universe_authority_receipt"]["sha256"] = _file_digest(path)
            with self.assertRaisesRegex(FullRecordValidationError, "another universe"):
                validate_review(review, authority_root=root, allow_test_authority=True)

    def test_altered_universe_action_or_boundary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review = _synthetic_review(root)
            review["issue_universe"]["action_ids"] = ["house:999:1:2"]
            review["issue_universe"]["snapshot_sha256"] = compute_universe_sha256(review)
            with self.assertRaisesRegex(
                FullRecordValidationError,
                "membership mismatch|action accounting must exactly equal",
            ):
                validate_review(review, authority_root=root, allow_test_authority=True)
            review = _synthetic_review(root)
            path = root / "universe.json"
            manifest = json.loads(path.read_text())
            manifest["boundary"]["end_date"] = "2099-01-03"
            manifest["universe_subject_sha256"] = _digest(
                {k: v for k, v in manifest.items() if k != "universe_subject_sha256"}
            )
            _write(path, manifest)
            review["external_authority"]["universe_manifest"]["sha256"] = _file_digest(path)
            review["external_authority"]["universe_manifest"]["subject_sha256"] = manifest[
                "universe_subject_sha256"
            ]
            with self.assertRaises(FullRecordValidationError):
                validate_review(review, authority_root=root, allow_test_authority=True)

    def test_missing_acquisition_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review = _synthetic_review(root)
            (root / "acquisition.json").unlink()
            with self.assertRaisesRegex(FullRecordValidationError, "missing acquisition"):
                validate_review(review, authority_root=root, allow_test_authority=True)

    def test_semantic_or_approval_self_assertion_is_rejected(self) -> None:
        review = _review()
        review["axes"]["review_scope"] = "full_defined_issue_record"
        review["issue_universe"]["snapshot_sha256"] = compute_universe_sha256(review)
        review["synthesis"]["human_approval_receipt_refs"] = []
        with self.assertRaises(FullRecordValidationError):
            validate_review(review)

    def test_wrong_semantic_digest_and_changed_outcome_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review = _synthetic_review(root)
            review["external_authority"]["semantic_artifact"]["sha256"] = "f" * 64
            with self.assertRaisesRegex(FullRecordValidationError, "digest mismatch"):
                validate_review(review, authority_root=root, allow_test_authority=True)
            review = _synthetic_review(root)
            review["synthesis"]["outcome"] = "mechanism_divide"
            with self.assertRaisesRegex(FullRecordValidationError, "synthesis_outcome mismatch"):
                validate_review(review, authority_root=root, allow_test_authority=True)
            review = _synthetic_review(root)
            review["frontend_state"]["conclusion_teaser"]["text"] = "Changed after approval."
            with self.assertRaisesRegex(
                FullRecordValidationError, "presentation_subject_sha256 mismatch"
            ):
                validate_review(review, authority_root=root, allow_test_authority=True)

    def test_empty_or_wrong_approval_receipt_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            review = _synthetic_review(root)
            review["synthesis"]["human_approval_receipt_refs"] = []
            with self.assertRaisesRegex(FullRecordValidationError, "empty or mismatched"):
                validate_review(review, authority_root=root, allow_test_authority=True)
            review = _synthetic_review(root)
            path = root / "approval.json"
            approval = json.loads(path.read_text())
            approval["synthesis_outcome"] = "mechanism_divide"
            _write(path, approval)
            review["external_authority"]["human_approval_receipt"]["sha256"] = _file_digest(path)
            with self.assertRaisesRegex(FullRecordValidationError, "synthesis_outcome mismatch"):
                validate_review(review, authority_root=root, allow_test_authority=True)

    def test_episode_reference_cannot_add_contradictory_meaning(self) -> None:
        review = _review()
        review["episodes"][0]["action_interpretation_refs"][0]["meaning"] = "Contradiction."
        with self.assertRaisesRegex(FullRecordValidationError, "schema validation failed"):
            validate_review(review)

    def test_known_substantive_action_cannot_be_omitted_or_duplicated(self) -> None:
        review = _review()
        review["action_accounting"][-1]["episode_id"] = None
        with self.assertRaises(FullRecordValidationError):
            validate_review(review)
        review = _review()
        review["episodes"][1]["action_ids"].append("house:119:1:299")
        review["episodes"][1]["chronological_action_ids"].append("house:119:1:299")
        with self.assertRaises(FullRecordValidationError):
            validate_review(review)

    def test_unresolved_membership_and_authored_complete_partial_episode_reject(self) -> None:
        review = _review()
        action = review["action_accounting"][-1]
        action["disposition"] = "source_unresolved"
        action["interpretation"] = None
        action["review_friendliness"].update(
            {
                "action_meaning_evidence": "unresolved",
                "action_meaning_provenance": "unresolved",
                "source_conflict_state": "unresolved",
                "is_review_friendly": False,
            }
        )
        action["episode_membership_state"] = "unresolved"
        action["episode_id"] = None
        action["episode_membership_reason"] = None
        with self.assertRaises(FullRecordValidationError):
            validate_review(review)
        review = _review()
        action = review["action_accounting"][-1]
        action["disposition"] = "source_conflicting"
        action["interpretation"] = None
        action["review_friendliness"].update(
            {
                "action_meaning_evidence": "conflicting",
                "action_meaning_provenance": "conflicting",
                "source_conflict_state": "conflicting",
                "is_review_friendly": False,
            }
        )
        episode = review["episodes"][0]
        episode["action_interpretation_refs"] = []
        episode["outcome"] = "unresolved"
        episode["source_completeness"] = "partial"
        episode["unresolved_action_ids"] = [action["action_id"]]
        with self.assertRaisesRegex(FullRecordValidationError, "partial episode"):
            validate_review(review)

    def test_claim_compatibility_matrix_rejects_invalid_tiers(self) -> None:
        for tier, claim in (
            ("receipts_only", "full_issue_synthesis"),
            ("receipts_only", "full_review_no_common_throughline"),
            ("developing_read", "full_issue_synthesis"),
        ):
            with self.subTest(tier=tier, claim=claim), tempfile.TemporaryDirectory() as temp:
                outcome = "no_common_throughline" if "no_common" in claim else "uniform_direction"
                review = _synthetic_review(
                    Path(temp), outcome=outcome, claim_class=claim, semantic_tier=tier
                )
                with self.assertRaises(FullRecordValidationError):
                    validate_review(
                        review, authority_root=Path(temp), allow_test_authority=True
                    )

    def test_valid_no_common_and_no_safe_outcomes_pass(self) -> None:
        cases = (
            ("no_common_throughline", "full_review_no_common_throughline", "reviewed_conclusion"),
            ("no_safe_synthesis", "full_review_no_safe_synthesis", "receipts_only"),
        )
        for outcome, claim, tier in cases:
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as temp:
                review = _synthetic_review(
                    Path(temp), outcome=outcome, claim_class=claim, semantic_tier=tier
                )
                validate_review(
                    review, authority_root=Path(temp), allow_test_authority=True
                )

    def test_action_accounting_order_party_and_protected_invariants(self) -> None:
        review = _review()
        review["issue_universe"]["action_ids"].reverse()
        review["action_accounting"].reverse()
        validate_review(review)
        party = _review()
        party["subject"]["party"] = "R"
        with self.assertRaisesRegex(FullRecordValidationError, "schema validation failed"):
            validate_review(party)
        for protected in _review()["provenance"]["protected_files"]:
            self.assertTrue(
                _file_digest_matches(
                    ROOT / protected["path"], protected["sha256"]
                ),
                protected["path"],
            )


class TerminologyTests(unittest.TestCase):
    def test_current_authoritative_documents_pass(self) -> None:
        self.assertEqual(check(), [])

    def test_required_overclaim_variants_reject(self) -> None:
        examples = (
            "The seven-action benchmark is Foushee's complete Justice conclusion.",
            "The gold slice represents her full Justice record.",
            "This reviewed sample is the representative-level issue interpretation.",
            "The benchmark establishes the complete issue conclusion.",
            "THE 7-ACTION SAMPLE—IS THE FINAL CONCLUSION.",
        )
        for text in examples:
            with self.subTest(text=text):
                self.assertTrue(check_text(text, path="docs/current.md"))

    def test_bounded_language_is_allowed(self) -> None:
        examples = (
            "The seven-action benchmark supports a reviewed finding within its approved sample.",
            "The full Justice record has not yet been established.",
        )
        for text in examples:
            self.assertEqual(check_text(text, path="docs/current.md"), [])


if __name__ == "__main__":
    unittest.main()
