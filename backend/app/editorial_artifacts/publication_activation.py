from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from app.editorial_presentations.compiler import (
    approval_subject_for_artifact,
    artifact_digest,
    compile_public_issue_presentation,
    detached_receipt_matches,
    validate_trusted_action_source_contract,
)
from app.editorial_presentations.validation import (
    validate_public_issue_presentation,
)
from app.semantic_ir.pipeline import replay_accepted_reference

from .bundle import build_seed_bundle, canonical_json, semantic_hash


ROOT = Path(__file__).resolve().parents[3]
BUNDLE_ID = "foushee_justice_public_safety_119_publication_activation_v1"
BATCH_KEY = "foushee-justice-public-safety-119-publication-activation-v1-bae70a36"
SOURCE_COMMIT = "bae70a3623b66a68cda40ac537dc4a1740e87f92"
PRESENTATION_KEY = "f000477:justice_public_safety:119:v1"
VALIDATION_KEY = f"{PRESENTATION_KEY}:publication-validation"
SOURCE_KEY = f"{PRESENTATION_KEY}:publication-source-manifest"
MEMBER_ID = "F000477"
ISSUE_ID = "JUSTICE_PUBLIC_SAFETY"
RECEIPT_ID = (
    "approval-receipt:f000477-justice-public-safety-119-v1-20260727-dhart54"
)
APPROVAL_SUBJECT_SHA256 = (
    "67e67001ca678e70debba52e9049632f90d99da4d6f1dcaea60da40beaa87874"
)
PRESENTATION_CONTENT_SHA256 = (
    "5813d5e556542d0ef2234dc05b1e1e24d5811d8c0e22af7775cd1e9b82aa55ca"
)
ACTIVE_ARTIFACT_SHA256 = (
    "fd7a8b5e440654147bbb6b738be3bb683034f07b0c9cc4e26eba9cce84e07e59"
)
INACTIVE_ARTIFACT_SHA256 = (
    "b05e4a9e5212bac50c9c2cbeb0afd4cd5a07818b022c977c2f10252d01d3f2c4"
)
ACTION_SOURCE_SHA256 = (
    "0ee8575db526d4b021d7b26d2befbe9c22eb7af9473c12ac2ecec616f3ae9386"
)
LIMITATIONS_SHA256 = (
    "822098797ffce236c0018576b02969e15a6495c82ca577c5c74e69f5dd2a58df"
)

BUNDLE_PATH = (
    ROOT
    / "docs/editorial/publication_activations/"
    "foushee_justice_public_safety_119_publication_activation_v1.json"
)
FIXTURE_PATH = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_review_fixture.json"
)
RECEIPT_PATH = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_approval_receipt.json"
)
ACTION_SOURCE_PATH = (
    ROOT
    / "docs/editorial/action_source_contracts/"
    "foushee_justice_public_safety_119_v1.json"
)
CASES_PATH = ROOT / "docs/semantic_ir/accepted/development_cases.json"
BUNDLE_SCHEMA_PATH = (
    ROOT / "docs/editorial_publication_activation_bundle_v1.schema.json"
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_record(path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _artifact(
    artifact_type: str,
    natural_key: str,
    payload: dict[str, Any],
    *,
    source_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload["schema_version"],
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": source_manifest_sha256,
        "source_commit_sha": SOURCE_COMMIT,
        "member_bioguide_id": MEMBER_ID,
        "issue_id": ISSUE_ID,
        "congress": 119,
        "chamber": "house",
        "canonical_action_id": None,
        "episode_id": None,
        "policy_family_id": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "review_route": "human_exception",
    }


def _active_presentation() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    cases = _load(CASES_PATH)["cases"]
    case = next(
        item
        for item in cases
        if item["case_id"] == "semir-dev-05-justice-mechanism-divide"
    )
    compiled = replay_accepted_reference(copy.deepcopy(case)).compiled_ir
    authoring = _load(FIXTURE_PATH)
    source_contract = _load(ACTION_SOURCE_PATH)
    validate_trusted_action_source_contract(source_contract)
    if semantic_hash(source_contract) != ACTION_SOURCE_SHA256:
        raise ValueError("exact-action source-contract digest mismatch")
    inactive = compile_public_issue_presentation(
        compiled,
        copy.deepcopy(authoring),
        trusted_action_source_contract=source_contract,
    )
    if artifact_digest(inactive) != INACTIVE_ARTIFACT_SHA256:
        raise ValueError("inactive presentation artifact digest mismatch")
    controls = authoring["controls"]
    controls["editorial"]["human_approval_status"] = "human_approved"
    controls["benchmark"]["status"] = "gold_benchmark"
    controls["production"]["eligible"] = True
    controls["publication"]["active"] = True
    artifact = compile_public_issue_presentation(
        compiled,
        authoring,
        trusted_action_source_contract=source_contract,
    )
    validate_public_issue_presentation(artifact)
    receipt = _load(RECEIPT_PATH)
    subject = approval_subject_for_artifact(artifact)
    if not detached_receipt_matches(receipt, expected_subject=subject):
        raise ValueError("approved receipt does not bind to the active presentation")
    if subject["approval_subject_sha256"] != APPROVAL_SUBJECT_SHA256:
        raise ValueError("approval-subject digest mismatch")
    if subject["presentation_content_sha256"] != PRESENTATION_CONTENT_SHA256:
        raise ValueError("presentation-content digest mismatch")
    if subject["limitations_sha256"] != LIMITATIONS_SHA256:
        raise ValueError("canonical limitation-set digest mismatch")
    if approval_subject_for_artifact(inactive) != subject:
        raise ValueError("publication control changed the immutable approval subject")
    if artifact_digest(artifact) != ACTIVE_ARTIFACT_SHA256:
        raise ValueError("active presentation artifact digest mismatch")
    return artifact, inactive, receipt, source_contract


def build_activation_bundle() -> dict[str, Any]:
    historical = build_seed_bundle()
    presentation, inactive, receipt, source_contract = _active_presentation()
    source_files = [
        _file_record(ACTION_SOURCE_PATH),
        _file_record(
            ROOT
            / source_contract["source_manifest"]["path"]
        ),
        _file_record(
            ROOT
            / source_contract["claim_source_map"]["path"]
        ),
        _file_record(CASES_PATH),
        _file_record(FIXTURE_PATH),
        _file_record(RECEIPT_PATH),
    ]
    source_manifest_sha256 = semantic_hash(source_files)
    source_payload = {
        "schema_version": "editorial_publication_source_manifest_v1",
        "complete_required_sources": True,
        "activation_bundle_id": BUNDLE_ID,
        "source_contract": source_contract,
        "source_files": source_files,
        "reviewed_action_ids": sorted(source_contract["actions"]),
    }
    validation_payload = {
        "schema_version": "editorial_publication_validation_v1",
        "validation_run_id": f"{BUNDLE_ID}:local-release-validation",
        "successful": True,
        "current": True,
        "blocking_findings": 0,
        "activation_bundle_id": BUNDLE_ID,
        "presentation_identity": {
            "natural_key": PRESENTATION_KEY,
            "artifact_version": 1,
            "artifact_sha256": ACTIVE_ARTIFACT_SHA256,
            "approval_subject_sha256": APPROVAL_SUBJECT_SHA256,
            "presentation_content_sha256": PRESENTATION_CONTENT_SHA256,
            "approval_receipt_id": RECEIPT_ID,
        },
        "contract_versions": {
            "presentation": presentation["schema_version"],
            "selector": "editorial_public_presentations_api_v1",
            "persistence": "0016_editorial_artifact_persistence",
        },
        "validation_commands": [
            "python backend/scripts/build_editorial_artifact_seed.py --check",
            "python backend/scripts/build_foushee_justice_publication_activation.py --check",
            "python backend/scripts/foushee_justice_publication_activation.py verify-bundle",
            "python -m pytest -q backend/tests/test_foushee_justice_publication_activation.py backend/tests/test_foushee_justice_publication_activation_postgres.py backend/tests/test_api_editorial_presentations.py",
        ],
    }
    artifacts = [
        _artifact(
            "issue_public_presentation",
            PRESENTATION_KEY,
            presentation,
            source_manifest_sha256=source_manifest_sha256,
        ),
        _artifact(
            "source_manifest",
            SOURCE_KEY,
            source_payload,
            source_manifest_sha256=source_manifest_sha256,
        ),
        _artifact(
            "standardization_validation_result",
            VALIDATION_KEY,
            validation_payload,
            source_manifest_sha256=source_manifest_sha256,
        ),
    ]
    artifacts.sort(
        key=lambda item: (
            item["artifact_type"],
            item["natural_key"],
            item["artifact_version"],
        )
    )
    relationships = [
        {
            "parent_natural_key": PRESENTATION_KEY,
            "child_natural_key": VALIDATION_KEY,
            "relationship_type": "has_validation",
            "ordinal": 0,
            "metadata": {"activation_bundle_id": BUNDLE_ID},
        },
        {
            "parent_natural_key": PRESENTATION_KEY,
            "child_natural_key": SOURCE_KEY,
            "relationship_type": "uses_source_manifest",
            "ordinal": 0,
            "metadata": {"activation_bundle_id": BUNDLE_ID},
        },
    ]
    relationships.sort(
        key=lambda item: (
            item["parent_natural_key"],
            item["relationship_type"],
            item["child_natural_key"],
        )
    )
    body = {
        "schema_version": "editorial_publication_activation_bundle_v1",
        "bundle_id": BUNDLE_ID,
        "deterministic_batch_key": BATCH_KEY,
        "source_commit_sha": SOURCE_COMMIT,
        "target_environment_class": "production_postgresql",
        "historical_seed": {
            "deterministic_batch_key": historical["deterministic_batch_key"],
            "manifest_sha256": historical["manifest_sha256"],
            "expected_counts": {
                "batches": 1,
                "artifacts": historical["expected_counts"]["artifacts"],
                "relationships": historical["expected_counts"]["relationships"],
                "publication_registry": 0,
            },
        },
        "activation_target": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "congress": 119,
            "scope": "119",
            "presentation_natural_key": PRESENTATION_KEY,
            "presentation_artifact_version": 1,
            "approval_receipt_id": RECEIPT_ID,
            "approval_subject_sha256": APPROVAL_SUBJECT_SHA256,
            "presentation_content_sha256": PRESENTATION_CONTENT_SHA256,
            "active_artifact_sha256": ACTIVE_ARTIFACT_SHA256,
            "inactive_artifact_sha256": artifact_digest(inactive),
            "detached_approval_receipt_sha256": semantic_hash(receipt),
            "action_source_contract_id": source_contract["contract_id"],
            "action_source_contract_sha256": semantic_hash(source_contract),
            "limitations_sha256": LIMITATIONS_SHA256,
        },
        "artifacts": artifacts,
        "relationships": relationships,
        "publication_registry": {
            "member_bioguide_id": MEMBER_ID,
            "issue_id": ISSUE_ID,
            "presentation_natural_key": PRESENTATION_KEY,
            "presentation_artifact_version": 1,
            "publicly_active": True,
            "publication_metadata": {
                "activation_bundle_id": BUNDLE_ID,
                "approval_receipt": receipt,
                "approval_subject_sha256": APPROVAL_SUBJECT_SHA256,
                "presentation_content_sha256": PRESENTATION_CONTENT_SHA256,
                "active_artifact_sha256": ACTIVE_ARTIFACT_SHA256,
                "validation_natural_key": VALIDATION_KEY,
                "source_manifest_natural_key": SOURCE_KEY,
            },
        },
        "expected_counts": {
            "before": {
                "batches": 1,
                "artifacts": 71,
                "relationships": 95,
                "publication_registry": 0,
            },
            "after": {
                "batches": 2,
                "artifacts": 74,
                "relationships": 97,
                "publication_registry": 1,
            },
        },
        "rollback_identity": {
            "deterministic_batch_key": BATCH_KEY,
            "artifact_versions": [
                {
                    "natural_key": item["natural_key"],
                    "artifact_version": item["artifact_version"],
                    "content_sha256": item["content_sha256"],
                }
                for item in artifacts
            ],
            "relationship_sha256": semantic_hash(relationships),
            "registry_primary_key": {
                "member_bioguide_id": MEMBER_ID,
                "issue_id": ISSUE_ID,
            },
            "approval_receipt_id": RECEIPT_ID,
            "restore_expected_counts": {
                "batches": 1,
                "artifacts": 71,
                "relationships": 95,
                "publication_registry": 0,
            },
            "deletion_order": [
                "editorial_publication_registry:F000477:JUSTICE_PUBLIC_SAFETY",
                "editorial_artifact_relationships:2 exact bundle relationships",
                "editorial_artifact_versions:3 exact bundle artifact versions",
                f"editorial_artifact_batches:{BATCH_KEY}",
            ],
        },
        "public_smoke_contract": {
            "before": {
                "119": "receipts_only",
                "all": "receipts_only",
                "118": "receipts_only",
            },
            "after": {
                "119": "reviewed_conclusion",
                "all": "reviewed_conclusion_with_reviewed_119_boundary",
                "118": "receipts_only",
            },
            "approved_counts": {
                "actions": 7,
                "episodes": 5,
                "repeated_patterns": 2,
            },
            "cross_identity": "receipts_only_for_other_members_and_issues",
        },
        "semantic_hashes": {
            "artifacts_sha256": semantic_hash(artifacts),
            "relationships_sha256": semantic_hash(relationships),
            "publication_registry_sha256": semantic_hash(
                {
                    "member_bioguide_id": MEMBER_ID,
                    "issue_id": ISSUE_ID,
                    "presentation_natural_key": PRESENTATION_KEY,
                    "presentation_artifact_version": 1,
                    "publicly_active": True,
                }
            ),
        },
    }
    body["bundle_sha256"] = semantic_hash(body)
    validate_activation_bundle(body)
    return body


def validate_activation_bundle(bundle: dict[str, Any]) -> None:
    schema = _load(BUNDLE_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(bundle),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise ValueError(
            "activation bundle JSON Schema mismatch: "
            + "; ".join(error.message for error in errors[:3])
        )
    required = {
        "schema_version",
        "bundle_id",
        "deterministic_batch_key",
        "source_commit_sha",
        "target_environment_class",
        "historical_seed",
        "activation_target",
        "artifacts",
        "relationships",
        "publication_registry",
        "expected_counts",
        "rollback_identity",
        "public_smoke_contract",
        "semantic_hashes",
        "bundle_sha256",
    }
    if set(bundle) != required:
        raise ValueError("activation bundle top-level schema mismatch")
    copy_for_hash = copy.deepcopy(bundle)
    claimed = copy_for_hash.pop("bundle_sha256")
    if claimed != semantic_hash(copy_for_hash):
        raise ValueError("activation bundle digest mismatch")
    if (
        bundle["schema_version"]
        != "editorial_publication_activation_bundle_v1"
        or bundle["bundle_id"] != BUNDLE_ID
        or bundle["deterministic_batch_key"] != BATCH_KEY
        or bundle["source_commit_sha"] != SOURCE_COMMIT
        or bundle["target_environment_class"] != "production_postgresql"
    ):
        raise ValueError("activation bundle identity mismatch")
    if bundle["expected_counts"]["before"] != {
        "batches": 1,
        "artifacts": 71,
        "relationships": 95,
        "publication_registry": 0,
    } or bundle["expected_counts"]["after"] != {
        "batches": 2,
        "artifacts": 74,
        "relationships": 97,
        "publication_registry": 1,
    }:
        raise ValueError("activation bundle count contract mismatch")
    artifacts = bundle["artifacts"]
    if len(artifacts) != 3 or {
        item["artifact_type"] for item in artifacts
    } != {
        "issue_public_presentation",
        "source_manifest",
        "standardization_validation_result",
    }:
        raise ValueError("activation artifact set mismatch")
    keys = {item["natural_key"] for item in artifacts}
    if keys != {PRESENTATION_KEY, SOURCE_KEY, VALIDATION_KEY}:
        raise ValueError("activation artifact identity mismatch")
    for item in artifacts:
        if item["content_sha256"] != semantic_hash(item["payload"]):
            raise ValueError(f"activation content digest mismatch: {item['natural_key']}")
        if (
            item["editorial_status"] != "human_approved"
            or item["benchmark_status"] != "gold_benchmark"
            or item["production_eligible"] is not True
        ):
            raise ValueError("activation artifact approval state mismatch")
    presentation = next(
        item for item in artifacts if item["natural_key"] == PRESENTATION_KEY
    )
    validate_public_issue_presentation(presentation["payload"])
    if presentation["content_sha256"] != ACTIVE_ARTIFACT_SHA256:
        raise ValueError("active artifact digest is not pinned")
    target = bundle["activation_target"]
    if (
        target["inactive_artifact_sha256"] != INACTIVE_ARTIFACT_SHA256
        or target["action_source_contract_sha256"] != ACTION_SOURCE_SHA256
        or target["limitations_sha256"] != LIMITATIONS_SHA256
    ):
        raise ValueError("approved activation digest set mismatch")
    source = next(item for item in artifacts if item["natural_key"] == SOURCE_KEY)
    validation = next(
        item for item in artifacts if item["natural_key"] == VALIDATION_KEY
    )
    if source["payload"].get("complete_required_sources") is not True:
        raise ValueError("activation source manifest is incomplete")
    if {
        validation["payload"].get("successful"),
        validation["payload"].get("current"),
    } != {True} or validation["payload"].get("blocking_findings") != 0:
        raise ValueError("activation validation receipt is not successful/current")
    if len(bundle["relationships"]) != 2:
        raise ValueError("activation relationship count mismatch")
    relation_set = {
        (
            item["parent_natural_key"],
            item["child_natural_key"],
            item["relationship_type"],
        )
        for item in bundle["relationships"]
    }
    if relation_set != {
        (PRESENTATION_KEY, VALIDATION_KEY, "has_validation"),
        (PRESENTATION_KEY, SOURCE_KEY, "uses_source_manifest"),
    }:
        raise ValueError("activation relationship contract mismatch")
    metadata = bundle["publication_registry"]["publication_metadata"]
    if not detached_receipt_matches(
        metadata["approval_receipt"],
        expected_subject=approval_subject_for_artifact(presentation["payload"]),
    ):
        raise ValueError("registry receipt does not bind to presentation")
    if bundle["semantic_hashes"] != {
        "artifacts_sha256": semantic_hash(artifacts),
        "relationships_sha256": semantic_hash(bundle["relationships"]),
        "publication_registry_sha256": semantic_hash(
            {
                "member_bioguide_id": MEMBER_ID,
                "issue_id": ISSUE_ID,
                "presentation_natural_key": PRESENTATION_KEY,
                "presentation_artifact_version": 1,
                "publicly_active": True,
            }
        ),
    }:
        raise ValueError("activation semantic hashes mismatch")


def load_activation_bundle() -> dict[str, Any]:
    checked = _load(BUNDLE_PATH)
    generated = build_activation_bundle()
    if checked != generated:
        raise ValueError("checked activation bundle differs from deterministic build")
    validate_activation_bundle(checked)
    return checked


def bundle_json() -> str:
    return json.dumps(build_activation_bundle(), indent=2, ensure_ascii=False) + "\n"
