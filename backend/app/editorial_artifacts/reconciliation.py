from __future__ import annotations

import copy
from typing import Any

from app.editorial_artifacts.bundle import semantic_hash

BATCH_GRAPH_SCHEMA_VERSION = "editorial_persistence_batch_graph_v1"
TARGET_ABSENCE_SCHEMA_VERSION = "editorial_publication_target_absence_v1"
FINGERPRINT_SCHEMA_VERSION = (
    "editorial_publication_pre_activation_fingerprint_v1"
)

BATCH_IDENTITY_KEYS = (
    "database_batch_id",
    "deterministic_batch_key",
    "source_commit_sha",
    "manifest_sha256",
    "status",
    "artifact_count",
    "relationship_count",
)


def canonical_artifacts(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        copy.deepcopy(artifacts),
        key=lambda item: (
            item["artifact_type"],
            item["natural_key"],
            item["artifact_version"],
        ),
    )


def canonical_relationships(
    relationships: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_by_key = {
        item["natural_key"]: item
        for item in artifacts
    }
    if len(artifact_by_key) != len(artifacts):
        raise ValueError("canonical relationship artifact keys are not unique")
    canonical = []
    for relationship in relationships:
        parent = artifact_by_key.get(relationship["parent_natural_key"])
        child = artifact_by_key.get(relationship["child_natural_key"])
        if parent is None or child is None:
            raise ValueError("canonical relationship endpoint is absent")
        canonical.append(
            {
                "parent_natural_key": parent["natural_key"],
                "parent_artifact_version": parent["artifact_version"],
                "parent_content_sha256": parent["content_sha256"],
                "child_natural_key": child["natural_key"],
                "child_artifact_version": child["artifact_version"],
                "child_content_sha256": child["content_sha256"],
                "relationship_type": relationship["relationship_type"],
                "ordinal": relationship["ordinal"],
                "metadata": copy.deepcopy(relationship["metadata"]),
            }
        )
    return sorted(
        canonical,
        key=lambda item: (
            item["parent_natural_key"],
            item["relationship_type"],
            item["ordinal"],
            item["child_natural_key"],
        ),
    )


def canonical_batch_graph(
    batch: dict[str, Any],
    artifacts: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    if set(batch) != set(BATCH_IDENTITY_KEYS):
        raise ValueError("canonical batch identity fields mismatch")
    return {
        "schema_version": BATCH_GRAPH_SCHEMA_VERSION,
        "batch": {key: batch[key] for key in BATCH_IDENTITY_KEYS},
        "artifacts": canonical_artifacts(artifacts),
        "relationships": canonical_relationships(relationships, artifacts),
    }


def canonical_batch_graph_sha256(
    batch: dict[str, Any],
    artifacts: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> str:
    return semantic_hash(canonical_batch_graph(batch, artifacts, relationships))


def canonical_target_absence(
    *,
    artifact_identities: list[dict[str, Any]],
    active_content_sha256: str,
    inactive_content_sha256: str,
    activation_batch_key: str,
    registry_primary_key: dict[str, str],
    artifact_rows: list[dict[str, Any]],
    activation_batch_rows: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
    partial_activation_relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": TARGET_ABSENCE_SCHEMA_VERSION,
        "artifact_identities": sorted(
            copy.deepcopy(artifact_identities),
            key=lambda item: (
                item["natural_key"],
                item["artifact_version"],
            ),
        ),
        "content_sha256": {
            "active": active_content_sha256,
            "inactive": inactive_content_sha256,
        },
        "activation_batch_key": activation_batch_key,
        "registry_primary_key": copy.deepcopy(registry_primary_key),
        "results": {
            "artifact_rows": sorted(
                copy.deepcopy(artifact_rows),
                key=lambda item: (
                    item["natural_key"],
                    item["artifact_version"],
                    item["content_sha256"],
                ),
            ),
            "activation_batch_rows": sorted(
                copy.deepcopy(activation_batch_rows),
                key=lambda item: item["deterministic_batch_key"],
            ),
            "registry_rows": sorted(
                copy.deepcopy(registry_rows),
                key=lambda item: (
                    item["member_bioguide_id"],
                    item["issue_id"],
                ),
            ),
            "partial_activation_relationships": sorted(
                copy.deepcopy(partial_activation_relationships),
                key=lambda item: (
                    item["parent_natural_key"],
                    item["relationship_type"],
                    item["ordinal"],
                    item["child_natural_key"],
                ),
            ),
        },
    }


def compose_pre_activation_fingerprint(
    *,
    schema_object_sha256: str,
    batches: list[dict[str, Any]],
    artifact_count: int,
    artifact_set_sha256: str,
    relationship_count: int,
    relationship_set_sha256: str,
    registry_count: int,
    registry_sha256: str,
    target_absence: dict[str, Any],
) -> dict[str, Any]:
    ordered_batches = sorted(
        copy.deepcopy(batches),
        key=lambda item: item["database_batch_id"],
    )
    fingerprint_input = {
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "schema_object_sha256": schema_object_sha256,
        "batches": ordered_batches,
        "artifact_set": {
            "count": artifact_count,
            "sha256": artifact_set_sha256,
        },
        "relationship_set": {
            "count": relationship_count,
            "sha256": relationship_set_sha256,
        },
        "registry": {
            "count": registry_count,
            "sha256": registry_sha256,
        },
        "target_absence": copy.deepcopy(target_absence),
        "target_absence_sha256": semantic_hash(target_absence),
    }
    return {
        "input": fingerprint_input,
        "sha256": semantic_hash(fingerprint_input),
    }


def validate_pre_activation_fingerprint(
    fingerprint: dict[str, Any],
) -> None:
    if set(fingerprint) != {"input", "sha256"}:
        raise ValueError("pre-activation fingerprint envelope mismatch")
    fingerprint_input = fingerprint["input"]
    if fingerprint["sha256"] != semantic_hash(fingerprint_input):
        raise ValueError("pre-activation fingerprint digest mismatch")
    if (
        fingerprint_input["target_absence_sha256"]
        != semantic_hash(fingerprint_input["target_absence"])
    ):
        raise ValueError("target-absence fingerprint digest mismatch")
