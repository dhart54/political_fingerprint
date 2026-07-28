from __future__ import annotations

import os
import copy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.editorial_artifacts.publication_activation import load_activation_bundle
from app.main import app
from scripts.editorial_artifact_store import _connect
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_justice_publication_activation import (
    LOCK_KEY,
    _apply,
    _counts,
    _postcheck,
    _preflight,
    _rollback,
)


DATABASE_URL = os.getenv("EDITORIAL_DISPOSABLE_DATABASE_URL")


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_transactional_apply_idempotency_postcheck_and_rollback() -> None:
    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            assert _preflight(conn, bundle)["counts"] == {
                "batches": 1,
                "artifacts": 71,
                "relationships": 95,
                "publication_registry": 0,
            }
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,)
            )
            applied = _apply(conn, bundle)
            assert applied["already_applied"] is False
            assert applied["rows_inserted"] == 6
        with conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,)
            )
            repeated = _apply(conn, bundle)
            assert repeated["already_applied"] is True
            assert repeated["rows_inserted"] == 0
            post = _postcheck(conn, bundle)
            assert post["selector"]["F000477"] == {
                "119": "reviewed_conclusion",
                "all": "reviewed_conclusion",
                "118": "receipts_only",
            }
            row = conn.execute(
                """SELECT registry.*, artifact.payload_jsonb,
                          artifact.content_sha256, artifact.editorial_status,
                          artifact.benchmark_status, artifact.production_eligible,
                          artifact.schema_version, artifact.artifact_version,
                          artifact.natural_key
                   FROM editorial_publication_registry registry
                   JOIN editorial_artifact_versions artifact
                     ON artifact.artifact_id = registry.artifact_id"""
            ).fetchone()
            from app.editorial_presentations.selector import (
                select_public_presentations,
            )

            selected = select_public_presentations(
                [dict(row)],
                legislator_id="leg_valerie_p_foushee",
                member_bioguide_id="F000477",
                scope="119",
            )
            assert all(
                item["tier"] == "receipts_only"
                for item in selected["presentations"]
                if item["issue_id"] != "JUSTICE_PUBLIC_SAFETY"
            )
        with patch(
            "app.api.editorial_presentations.get_connection",
            side_effect=lambda: _connect(DATABASE_URL, autocommit=True),
        ):
            response = TestClient(app).get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "all"},
            )
        assert response.status_code == 200
        justice = next(
            item
            for item in response.json()["presentations"]
            if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        )
        assert justice["tier"] == "reviewed_conclusion"
        assert "119th-Congress" in justice["scope_boundary"]
        assert len(justice["evidence_metadata"]["action_ids"]) == 7
        assert len(justice["evidence_metadata"]["episode_ids"]) == 5
        assert len(justice["repeated_patterns"]) == 2
        assert any(
            "mixed" in item["heading"].lower()
            and "fentanyl" in item["body"].lower()
            and "change in position" in item["body"].lower()
            for item in justice["policy_trajectories"]
        )
        assert justice["provenance"]["review_receipt_id"] == (
            "approval-receipt:f000477-justice-public-safety-119-v1-"
            "20260727-dhart54"
        )
        with conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,)
            )
            rolled_back = _rollback(conn, bundle)
            assert rolled_back["counts"] == bundle["expected_counts"]["before"]
        with conn.transaction():
            assert _counts(conn) == bundle["expected_counts"]["before"]
        with patch(
            "app.api.editorial_presentations.get_connection",
            side_effect=lambda: _connect(DATABASE_URL, autocommit=True),
        ):
            response = TestClient(app).get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "119"},
            )
        justice = next(
            item
            for item in response.json()["presentations"]
            if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        )
        assert justice["tier"] == "receipts_only"


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_relationship_failure_rolls_back_the_entire_transaction() -> None:
    bundle = copy.deepcopy(load_activation_bundle())
    bundle["relationships"][0]["relationship_type"] = "not_a_contract_type"
    with _connect(DATABASE_URL) as conn:
        with pytest.raises(Exception):
            with conn.transaction():
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,)
                )
                _apply(conn, bundle)
        with conn.transaction():
            assert _counts(conn) == bundle["expected_counts"]["before"]


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_rollback_refuses_registry_identity_drift() -> None:
    from psycopg.types.json import Jsonb

    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            _apply(conn, bundle)
        with conn.transaction():
            conn.execute(
                """UPDATE editorial_publication_registry
                   SET publication_metadata_jsonb =
                     jsonb_set(publication_metadata_jsonb,
                       '{approval_receipt,receipt_id}',
                       '"approval-receipt:substituted"'::jsonb)
                   WHERE member_bioguide_id = 'F000477'
                     AND issue_id = 'JUSTICE_PUBLIC_SAFETY'"""
            )
        with pytest.raises(StoreSafetyError, match="identity mismatch"):
            with conn.transaction():
                _rollback(conn, bundle)
        with conn.transaction():
            assert _counts(conn) == bundle["expected_counts"]["after"]
            conn.execute(
                """UPDATE editorial_publication_registry
                   SET publication_metadata_jsonb = %s
                   WHERE member_bioguide_id = 'F000477'
                     AND issue_id = 'JUSTICE_PUBLIC_SAFETY'""",
                (Jsonb(bundle["publication_registry"]["publication_metadata"]),),
            )
            _rollback(conn, bundle)
