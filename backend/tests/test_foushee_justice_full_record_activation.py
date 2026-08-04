from __future__ import annotations

import copy

import pytest

from app.editorial_artifacts.bundle import semantic_hash
from scripts.foushee_justice_full_record_activation import (
    BUNDLE_ID,
    _state_fingerprint,
    build_bundle,
    validate_bundle,
)
from scripts.editorial_artifact_store import StoreSafetyError


DEPLOYED = "a" * 40


class _EmptyResult:
    def fetchall(self) -> list:
        return []


class _FingerprintConnection:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> _EmptyResult:
        self.queries.append(query)
        return _EmptyResult()


def _preflight() -> dict:
    value = {
        "schema_version": "foushee_justice_full_record_preflight_v1",
        "captured_at": "2026-08-04T00:00:00+00:00",
        "deployed_commit": DEPLOYED,
        "read_only": True,
        "counts": {
            "batches": 3,
            "artifacts": 143,
            "relationships": 157,
            "publication_registry": 1,
        },
        "state_fingerprint_sha256": "b" * 64,
        "predecessor": {
            "artifact_id": 218,
            "publicly_active": True,
            "publication_metadata_jsonb": {"predecessor": "compact"},
            "natural_key": "f000477:justice_public_safety:119:v1",
            "artifact_version": 1,
            "content_sha256": (
                "fd7a8b5e440654147bbb6b738be3bb683034f07b0c9cc4e26eba9cce84e07e59"
            ),
            "payload_jsonb": {},
        },
        "target_rows": [],
        "selector": {},
    }
    value["preflight_sha256"] = semantic_hash(value)
    return value


def test_state_fingerprint_qualifies_registry_identity_columns() -> None:
    conn = _FingerprintConnection()
    _state_fingerprint(conn)
    registry_query = next(
        query for query in conn.queries if "FROM editorial_publication_registry" in query
    )
    assert "registry.member_bioguide_id" in registry_query
    assert "registry.issue_id" in registry_query


def test_bundle_is_candidate_bound_and_has_exact_write_caps() -> None:
    bundle = build_bundle(_preflight(), DEPLOYED)
    validate_bundle(bundle)
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["source_commit_sha"] == DEPLOYED
    assert bundle["expected_counts"]["before"] == _preflight()["counts"]
    assert bundle["expected_counts"]["after"] == {
        "batches": 4,
        "artifacts": 146,
        "relationships": 159,
        "publication_registry": 1,
    }
    assert bundle["write_caps"] == {
        "batch_inserts": 1,
        "artifact_inserts": 3,
        "relationship_inserts": 2,
        "registry_inserts": 0,
        "registry_updates": 1,
        "deletes_during_activation": 0,
    }
    assert bundle["public_smoke_contract"] == {
        "119": {
            "tier": "reviewed_conclusion",
            "receipt_count": 35,
            "review_scope": "full_defined_issue_record",
        },
        "all": {
            "tier": "reviewed_conclusion",
            "receipt_count": 35,
            "review_scope": "full_defined_issue_record",
        },
        "118": {
            "tier": "receipts_only",
            "receipt_count": 0,
            "review_scope": None,
        },
    }


def test_changed_preflight_or_deployed_commit_fails_closed() -> None:
    preflight = _preflight()
    preflight["counts"]["artifacts"] += 1
    with pytest.raises(StoreSafetyError, match="preflight digest mismatch"):
        build_bundle(preflight, DEPLOYED)
    with pytest.raises(StoreSafetyError, match="deployed-commit binding mismatch"):
        build_bundle(_preflight(), "c" * 40)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda bundle: bundle["write_caps"].__setitem__("registry_updates", 2),
        lambda bundle: bundle["artifacts"][0].__setitem__("content_sha256", "0" * 64),
        lambda bundle: bundle["relationships"].pop(),
    ],
)
def test_mutated_bundle_fails_closed(mutate) -> None:
    bundle = build_bundle(_preflight(), DEPLOYED)
    mutate(bundle)
    with pytest.raises(StoreSafetyError):
        validate_bundle(bundle)


def test_bundle_digest_covers_predecessor_and_review_receipts() -> None:
    first = build_bundle(_preflight(), DEPLOYED)
    changed = _preflight()
    changed["predecessor"] = copy.deepcopy(changed["predecessor"])
    changed["predecessor"]["publication_metadata_jsonb"]["predecessor"] = "changed"
    changed.pop("preflight_sha256")
    changed["preflight_sha256"] = semantic_hash(changed)
    second = build_bundle(changed, DEPLOYED)
    assert first["bundle_sha256"] != second["bundle_sha256"]
