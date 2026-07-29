from __future__ import annotations

import os
import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.editorial_artifacts.publication_activation import (
    SOURCE_COMMIT,
    load_activation_bundle,
)
from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.compiler import (
    _copy_display_wording,
    semantic_tier_for_artifact,
)
from app.editorial_presentations.selector import select_public_presentations
from app.main import app
from scripts.editorial_artifact_store import _connect
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_justice_publication_activation import (
    LOCK_KEY,
    _apply,
    _counts,
    _postcheck,
    _preflight,
    _preflight_report,
    _prepare_backup,
    _rollback,
    _verify_backup_proof,
    _verify_preflight_report,
    _write_json,
    main,
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
            preflight = _preflight(conn, bundle)
            assert preflight["counts"] == {
                "batches": 2,
                "artifacts": 140,
                "relationships": 155,
                "publication_registry": 0,
            }
            assert [item["database_batch_id"] for item in preflight[
                "governed_baseline"
            ]["batches"]] == [1, 8]
            assert [
                item["graph_sha256"]
                for item in preflight["governed_baseline"]["batches"]
            ] == [
                item["graph_sha256"]
                for item in bundle["pre_activation_baseline"][
                    "governed_batches"
                ]
            ]
            assert preflight["governed_baseline"][
                "canonical_semantic_hashes"
            ] == bundle["pre_activation_baseline"][
                "canonical_semantic_hashes"
            ]
            assert preflight["governed_baseline"][
                "reconciled_fingerprint"
            ] == bundle["pre_activation_baseline"]["reconciled_fingerprint"]
            assert preflight["selector"] == {
                "rows": 0,
                "F000477": {
                    "119": "receipts_only",
                    "all": "receipts_only",
                    "118": "receipts_only",
                },
            }
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))", (LOCK_KEY,)
            )
            applied = _apply(conn, bundle)
            assert applied["already_applied"] is False
            assert applied["rows_inserted"] == 7
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
        with patch.dict(os.environ, {"DATABASE_URL": DATABASE_URL}):
            client = TestClient(app)
            response = client.get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "all"},
            )
            response_119 = client.get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "119"},
            )
            response_118 = client.get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "118"},
            )
            other_member = client.get(
                "/legislators/leg_alex_morgan/editorial-presentations",
                params={"scope": "119"},
            )
        assert {
            response.status_code,
            response_119.status_code,
            response_118.status_code,
            other_member.status_code,
        } == {200}
        justice = next(
            item
            for item in response.json()["presentations"]
            if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        )
        justice_119 = next(
            item
            for item in response_119.json()["presentations"]
            if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        )
        justice_118 = next(
            item
            for item in response_118.json()["presentations"]
            if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        )
        other_justice = next(
            item
            for item in other_member.json()["presentations"]
            if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        )
        economy = next(
            item
            for item in response_119.json()["presentations"]
            if item["issue_id"] == "ECONOMY_TAXES"
        )
        assert justice["tier"] == "reviewed_conclusion"
        assert justice_119["tier"] == "reviewed_conclusion"
        assert justice_118["tier"] == "receipts_only"
        assert other_justice["tier"] == "receipts_only"
        assert economy["tier"] == "receipts_only"
        approved_artifact = next(
            item
            for item in bundle["artifacts"]
            if item["artifact_type"] == "issue_public_presentation"
        )["payload"]
        approved = _copy_display_wording(
            approved_artifact["editorial_wording"],
            semantic_tier=semantic_tier_for_artifact(approved_artifact),
        )
        for field in (
            "tier",
            "tier_badge",
            "teaser",
            "coverage_text",
            "scope_boundary",
            "conclusion",
            "repeated_patterns",
            "policy_trajectories",
            "limitations",
        ):
            assert justice_119[field] == approved[field]
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
            assert rolled_back["governed_baseline"][
                "reconciled_fingerprint"
            ] == bundle["pre_activation_baseline"]["reconciled_fingerprint"]
            assert rolled_back["target_absent"] is True
            assert rolled_back["selector"]["F000477"] == {
                "119": "receipts_only",
                "all": "receipts_only",
                "118": "receipts_only",
            }
        with conn.transaction():
            assert _counts(conn) == bundle["expected_counts"]["before"]
        with patch.dict(os.environ, {"DATABASE_URL": DATABASE_URL}):
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


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_machine_generated_backup_restore_and_tamper_rejection(tmp_path: Path) -> None:
    bundle = load_activation_bundle()
    parsed = urlsplit(DATABASE_URL)
    restored_name = f"pf_restore_{uuid4().hex}"
    admin_url = urlunsplit(
        (parsed.scheme, parsed.netloc, "/postgres", parsed.query, parsed.fragment)
    )
    restored_url = urlunsplit(
        (parsed.scheme, parsed.netloc, f"/{restored_name}", parsed.query, parsed.fragment)
    )
    import psycopg
    from psycopg import sql

    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restored_name)))
    try:
        with _connect(DATABASE_URL, autocommit=True) as conn:
            report = _preflight_report(conn, bundle, SOURCE_COMMIT)
        input_report = tmp_path / "input-preflight-report.json"
        _write_json(input_report, report)
        evidence_dir = tmp_path / "evidence"
        proof_path = _prepare_backup(
            DATABASE_URL,
            restored_url,
            evidence_dir,
            bundle,
            SOURCE_COMMIT,
            input_report,
        )
        copied_report = evidence_dir / "preflight-report.json"
        assert _verify_backup_proof(
            proof_path, bundle, SOURCE_COMMIT, copied_report
        )["verified"] is True
        source_inventory = json.loads(
            (evidence_dir / "source-inventory.json").read_text(encoding="utf-8")
        )
        restored_inventory_json = json.loads(
            (evidence_dir / "restored-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        expected_fingerprint = bundle["pre_activation_baseline"][
            "reconciled_fingerprint"
        ]
        assert source_inventory["governed_baseline"][
            "reconciled_fingerprint"
        ] == expected_fingerprint
        assert restored_inventory_json["governed_baseline"][
            "reconciled_fingerprint"
        ] == expected_fingerprint
        assert source_inventory["governed_baseline"] == restored_inventory_json[
            "governed_baseline"
        ]
        with _connect(restored_url) as restored_conn:
            with restored_conn.transaction(force_rollback=True):
                restored_conn.execute(
                    """UPDATE editorial_artifact_relationships
                       SET metadata_jsonb = '{"restored-drift":true}'::jsonb
                       WHERE parent_artifact_id = (
                         SELECT MIN(parent_artifact_id)
                         FROM editorial_artifact_relationships
                       )"""
                )
                assert _counts(restored_conn) == bundle["expected_counts"]["before"]
                with pytest.raises(StoreSafetyError):
                    _preflight(restored_conn, bundle)
            with restored_conn.transaction(force_rollback=True):
                _apply(restored_conn, bundle)
                restored_conn.execute(
                    """UPDATE editorial_artifact_relationships
                       SET metadata_jsonb =
                         '{"restored-rollback-drift":true}'::jsonb
                       WHERE parent_artifact_id = (
                         SELECT MIN(parent_artifact_id)
                         FROM editorial_artifact_relationships
                       )"""
                )
                assert _counts(restored_conn) == bundle["expected_counts"]["after"]
                with pytest.raises(StoreSafetyError):
                    _rollback(restored_conn, bundle)

        snapshot = evidence_dir / "pre-activation.dump"
        original_snapshot = snapshot.read_bytes()
        missing_snapshot = evidence_dir / "missing.dump"
        snapshot.rename(missing_snapshot)
        with pytest.raises(StoreSafetyError, match="snapshot file mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )
        missing_snapshot.rename(snapshot)
        snapshot.write_bytes(original_snapshot + b"tampered")
        with pytest.raises(StoreSafetyError, match="snapshot file mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )
        snapshot.write_bytes(original_snapshot)

        restored_inventory_path = evidence_dir / "restored-inventory.json"
        restored_inventory = restored_inventory_path.read_text(encoding="utf-8")
        restored_inventory_path.write_text(
            restored_inventory + " ", encoding="utf-8"
        )
        with pytest.raises(StoreSafetyError, match="restored_inventory"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )
        restored_inventory_path.write_text(restored_inventory, encoding="utf-8")

        original_proof = proof_path.read_text(encoding="utf-8")
        proof = json.loads(original_proof)
        proof["snapshot"]["sha256"] = "0" * 64
        proof["proof_sha256"] = semantic_hash(
            {key: value for key, value in proof.items() if key != "proof_sha256"}
        )
        _write_json(proof_path, proof)
        with pytest.raises(StoreSafetyError, match="snapshot file mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )

        proof = json.loads(original_proof)
        proof["snapshot"]["byte_size"] += 1
        proof["proof_sha256"] = semantic_hash(
            {key: value for key, value in proof.items() if key != "proof_sha256"}
        )
        _write_json(proof_path, proof)
        with pytest.raises(StoreSafetyError, match="snapshot file mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )

        proof = json.loads(original_proof)
        proof["source_inventory"] = copy.deepcopy(proof["restored_inventory"])
        proof["proof_sha256"] = semantic_hash(
            {key: value for key, value in proof.items() if key != "proof_sha256"}
        )
        _write_json(proof_path, proof)
        with pytest.raises(StoreSafetyError, match="chain mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )

        proof = json.loads(original_proof)
        proof["created_at"] = "2000-01-01T00:00:00Z"
        proof["proof_sha256"] = semantic_hash(
            {key: value for key, value in proof.items() if key != "proof_sha256"}
        )
        _write_json(proof_path, proof)
        with pytest.raises(StoreSafetyError, match="stale"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )

        proof = json.loads(original_proof)
        proof["restore_passed"] = True
        proof["proof_sha256"] = semantic_hash(
            {key: value for key, value in proof.items() if key != "proof_sha256"}
        )
        _write_json(proof_path, proof)
        with pytest.raises(StoreSafetyError, match="schema mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )

        proof_path.write_text(original_proof, encoding="utf-8")
        receipt_path = evidence_dir / "restore-receipt.json"
        original_receipt = receipt_path.read_text(encoding="utf-8")
        receipt = json.loads(original_receipt)
        receipt["restored_counts"]["artifacts"] = 72
        receipt["receipt_sha256"] = semantic_hash(
            {
                key: value
                for key, value in receipt.items()
                if key != "receipt_sha256"
            }
        )
        _write_json(receipt_path, receipt)
        proof = json.loads(original_proof)
        proof["restore_receipt"]["byte_size"] = receipt_path.stat().st_size
        proof["restore_receipt"]["sha256"] = hashlib.sha256(
            receipt_path.read_bytes()
        ).hexdigest()
        proof["proof_sha256"] = semantic_hash(
            {key: value for key, value in proof.items() if key != "proof_sha256"}
        )
        _write_json(proof_path, proof)
        with pytest.raises(StoreSafetyError, match="chain mismatch"):
            _verify_backup_proof(
                proof_path, bundle, SOURCE_COMMIT, copied_report
            )
        receipt_path.write_text(original_receipt, encoding="utf-8")
        proof_path.write_text(original_proof, encoding="utf-8")
    finally:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (restored_name,),
            )
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(restored_name)
                )
            )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_deployed_commit_preflight_is_read_only_and_apply_binding_is_exact(
    tmp_path: Path,
) -> None:
    bundle = load_activation_bundle()
    before: dict[str, int]
    with _connect(DATABASE_URL, autocommit=True) as conn:
        before = _counts(conn)
    report_path = tmp_path / "preflight.json"
    assert (
        main(
            [
                "preflight",
                "--database-url",
                DATABASE_URL,
                "--bundle-id",
                bundle["bundle_id"],
                "--deployed-commit",
                SOURCE_COMMIT,
                "--report-path",
                str(report_path),
            ]
        )
        == 0
    )
    with _connect(DATABASE_URL, autocommit=True) as conn:
        assert _counts(conn) == before
        with pytest.raises(StoreSafetyError, match="identity mismatch"):
            _verify_preflight_report(
                report_path,
                bundle,
                "63c5f171bbaae8a20a42515122cc0ea3fa1a4336",
                conn,
            )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_preflight_rejects_governed_baseline_batch_identity_drift() -> None:
    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            conn.execute(
                """UPDATE editorial_artifact_batches
                   SET source_commit_sha = %s
                   WHERE deterministic_batch_key =
                     'commissioning-domain-v1-environment-energy-final-composition'""",
                ("0" * 40,),
            )
            with pytest.raises(
                StoreSafetyError,
                match="governed baseline batch identity mismatch",
            ):
                _preflight(conn, bundle)


@pytest.mark.parametrize(
    "batch_key",
    [
        "editorial-artifact-persistence-v1-88d6f344",
        "commissioning-domain-v1-environment-energy-final-composition",
    ],
)
@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_preflight_rejects_canonical_batch_graph_drift(
    batch_key: str,
) -> None:
    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            conn.execute(
                """UPDATE editorial_artifact_relationships rel
                   SET metadata_jsonb = '{"drift":true}'::jsonb
                   FROM editorial_artifact_versions parent,
                        editorial_artifact_batches batch
                   WHERE parent.artifact_id = rel.parent_artifact_id
                     AND batch.batch_id = parent.batch_id
                     AND batch.deterministic_batch_key = %s
                     AND rel.parent_artifact_id = (
                       SELECT MIN(rel2.parent_artifact_id)
                       FROM editorial_artifact_relationships rel2
                       JOIN editorial_artifact_versions parent2
                         ON parent2.artifact_id = rel2.parent_artifact_id
                       WHERE parent2.batch_id = batch.batch_id
                     )""",
                (batch_key,),
            )
            with pytest.raises(StoreSafetyError):
                _preflight(conn, bundle)


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_preflight_rejects_wrong_canonical_full_set_hash() -> None:
    bundle = copy.deepcopy(load_activation_bundle())
    bundle["pre_activation_baseline"]["canonical_semantic_hashes"][
        "artifacts_sha256"
    ] = "0" * 64
    with _connect(DATABASE_URL) as conn:
        with conn.transaction():
            with pytest.raises(
                StoreSafetyError,
                match="canonical full-set hash mismatch",
            ):
                _preflight(conn, bundle)


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_stale_preflight_rejects_relationship_drift(
    tmp_path: Path,
) -> None:
    bundle = load_activation_bundle()
    report_path = tmp_path / "preflight-report.json"
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            report = _preflight_report(conn, bundle, SOURCE_COMMIT)
            _write_json(report_path, report)
            conn.execute(
                """UPDATE editorial_artifact_relationships
                   SET metadata_jsonb = '{"stale":true}'::jsonb
                   WHERE parent_artifact_id = (
                     SELECT MIN(parent_artifact_id)
                     FROM editorial_artifact_relationships
                   )"""
            )
            with pytest.raises(StoreSafetyError):
                _verify_preflight_report(
                    report_path,
                    bundle,
                    SOURCE_COMMIT,
                    conn,
                )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_stale_preflight_rejects_artifact_drift(tmp_path: Path) -> None:
    bundle = load_activation_bundle()
    report_path = tmp_path / "preflight-report.json"
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            report = _preflight_report(conn, bundle, SOURCE_COMMIT)
            _write_json(report_path, report)
            artifact = conn.execute(
                """SELECT artifact.artifact_id, batch.deterministic_batch_key
                   FROM editorial_artifact_versions artifact
                   JOIN editorial_artifact_batches batch
                     ON batch.batch_id = artifact.batch_id
                   WHERE NOT EXISTS (
                     SELECT 1
                     FROM editorial_artifact_relationships rel
                     WHERE rel.parent_artifact_id = artifact.artifact_id
                        OR rel.child_artifact_id = artifact.artifact_id
                   )
                   ORDER BY artifact.artifact_id
                   LIMIT 1"""
            ).fetchone()
            assert artifact is not None
            conn.execute(
                "SELECT set_config('app.editorial_artifact_rollback_batch', %s, true)",
                (artifact["deterministic_batch_key"],),
            )
            conn.execute(
                "DELETE FROM editorial_artifact_versions WHERE artifact_id = %s",
                (artifact["artifact_id"],),
            )
            with pytest.raises(StoreSafetyError):
                _verify_preflight_report(
                    report_path,
                    bundle,
                    SOURCE_COMMIT,
                    conn,
                )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_stale_preflight_rejects_target_state_change(tmp_path: Path) -> None:
    bundle = load_activation_bundle()
    report_path = tmp_path / "preflight-report.json"
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            report = _preflight_report(conn, bundle, SOURCE_COMMIT)
            _write_json(report_path, report)
            _apply(conn, bundle)
            with pytest.raises(StoreSafetyError):
                _verify_preflight_report(
                    report_path,
                    bundle,
                    SOURCE_COMMIT,
                    conn,
                )


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_rollback_rejects_baseline_graph_drift_with_matching_counts() -> None:
    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            _apply(conn, bundle)
            conn.execute(
                """UPDATE editorial_artifact_relationships
                   SET metadata_jsonb = '{"rollback-drift":true}'::jsonb
                   WHERE parent_artifact_id = (
                     SELECT MIN(parent_artifact_id)
                     FROM editorial_artifact_relationships
                   )"""
            )
            assert _counts(conn) == bundle["expected_counts"]["after"]
            with pytest.raises(
                StoreSafetyError,
                match="graph differs from repository manifest",
            ):
                _rollback(conn, bundle)


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
@pytest.mark.parametrize(
    "corruption",
    [
        "missing_validation",
        "missing_source",
        "redirected_validation",
        "redirected_source",
        "duplicate_validation",
        "duplicate_source",
        "wrong_digest_validation",
        "wrong_digest_source",
    ],
)
def test_runtime_selector_fails_closed_on_relationship_graph_corruption(
    corruption: str,
) -> None:
    from psycopg.types.json import Jsonb

    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            _apply(conn, bundle)
            presentation_id = conn.execute(
                "SELECT artifact_id FROM editorial_publication_registry "
                "WHERE member_bioguide_id = %s AND issue_id = %s",
                ("F000477", "JUSTICE_PUBLIC_SAFETY"),
            ).fetchone()["artifact_id"]
            assert len(
                EditorialArtifactRepository(conn).publication_selector()
            ) == 1
            relationship_type = (
                "uses_source_manifest"
                if corruption.endswith("source")
                else "has_validation"
            )
            artifact_type = (
                "source_manifest"
                if relationship_type == "uses_source_manifest"
                else "standardization_validation_result"
            )
            target_rel = conn.execute(
                """SELECT rel.child_artifact_id, rel.ordinal, rel.metadata_jsonb
                   FROM editorial_artifact_relationships rel
                   WHERE rel.parent_artifact_id = %s
                     AND rel.relationship_type = %s""",
                (presentation_id, relationship_type),
            ).fetchone()
            other_artifact = conn.execute(
                """SELECT artifact_id FROM editorial_artifact_versions
                   WHERE artifact_type = %s
                     AND artifact_id <> %s
                   ORDER BY artifact_id LIMIT 1""",
                (artifact_type, target_rel["child_artifact_id"]),
            ).fetchone()
            if corruption.startswith("missing"):
                conn.execute(
                    """DELETE FROM editorial_artifact_relationships
                       WHERE parent_artifact_id = %s
                         AND child_artifact_id = %s
                         AND relationship_type = %s""",
                    (
                        presentation_id,
                        target_rel["child_artifact_id"],
                        relationship_type,
                    ),
                )
            elif corruption.startswith("redirected"):
                conn.execute(
                    """DELETE FROM editorial_artifact_relationships
                       WHERE parent_artifact_id = %s
                         AND child_artifact_id = %s
                         AND relationship_type = %s""",
                    (
                        presentation_id,
                        target_rel["child_artifact_id"],
                        relationship_type,
                    ),
                )
                conn.execute(
                    """INSERT INTO editorial_artifact_relationships
                       (parent_artifact_id, child_artifact_id, relationship_type,
                        ordinal, metadata_jsonb)
                       VALUES (%s,%s,%s,0,%s)""",
                    (
                        presentation_id,
                        other_artifact["artifact_id"],
                        relationship_type,
                        Jsonb({"activation_bundle_id": bundle["bundle_id"]}),
                    ),
                )
            elif corruption.startswith("duplicate"):
                conn.execute(
                    """INSERT INTO editorial_artifact_relationships
                       (parent_artifact_id, child_artifact_id, relationship_type,
                        ordinal, metadata_jsonb)
                       VALUES (%s,%s,%s,1,%s)""",
                    (
                        presentation_id,
                        other_artifact["artifact_id"],
                        relationship_type,
                        Jsonb({"activation_bundle_id": bundle["bundle_id"]}),
                    ),
                )
            else:
                digest_field = (
                    "source_manifest_content_sha256"
                    if relationship_type == "uses_source_manifest"
                    else "validation_content_sha256"
                )
                conn.execute(
                    f"""UPDATE editorial_publication_registry
                       SET publication_metadata_jsonb = jsonb_set(
                         publication_metadata_jsonb,
                         '{{{digest_field}}}',
                         to_jsonb(%s::text))
                       WHERE member_bioguide_id = 'F000477'
                         AND issue_id = 'JUSTICE_PUBLIC_SAFETY'""",
                    ("0" * 64,),
                )
            rows = EditorialArtifactRepository(conn).publication_selector()
            assert rows == []
            selected = select_public_presentations(
                rows,
                legislator_id="leg_valerie_p_foushee",
                member_bioguide_id="F000477",
                scope="119",
            )
            justice = next(
                item
                for item in selected["presentations"]
                if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
            )
            assert justice["tier"] == "receipts_only"
            conn.execute(
                "DELETE FROM editorial_artifact_relationships "
                "WHERE parent_artifact_id = %s AND relationship_type = %s",
                (presentation_id, relationship_type),
            )
            conn.execute(
                """INSERT INTO editorial_artifact_relationships
                   (parent_artifact_id, child_artifact_id, relationship_type,
                    ordinal, metadata_jsonb)
                   VALUES (%s,%s,%s,%s,%s)""",
                (
                    presentation_id,
                    target_rel["child_artifact_id"],
                    relationship_type,
                    target_rel["ordinal"],
                    Jsonb(target_rel["metadata_jsonb"]),
                ),
            )
            conn.execute(
                """UPDATE editorial_publication_registry
                   SET publication_metadata_jsonb = %s
                   WHERE member_bioguide_id = 'F000477'
                     AND issue_id = 'JUSTICE_PUBLIC_SAFETY'""",
                (Jsonb(bundle["publication_registry"]["publication_metadata"]),),
            )
            assert len(
                EditorialArtifactRepository(conn).publication_selector()
            ) == 1


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires an explicitly provisioned disposable PostgreSQL database",
)
def test_preexisting_registry_conflict_is_unchanged_on_rejected_activation() -> None:
    from psycopg.types.json import Jsonb

    bundle = load_activation_bundle()
    with _connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            historical = conn.execute(
                """SELECT artifact_id FROM editorial_artifact_versions
                   WHERE artifact_type = 'issue_public_presentation'
                   ORDER BY artifact_id LIMIT 1"""
            ).fetchone()
            conn.execute(
                "ALTER TABLE editorial_publication_registry "
                "DISABLE TRIGGER editorial_publication_registry_fail_closed"
            )
            conn.execute(
                """INSERT INTO editorial_publication_registry
                   (member_bioguide_id, issue_id, artifact_id, publicly_active,
                    activated_at, publication_metadata_jsonb)
                   VALUES ('F000477', 'JUSTICE_PUBLIC_SAFETY', %s, TRUE, NOW(), %s)""",
                (
                    historical["artifact_id"],
                    Jsonb({"conflicting_fixture": True}),
                ),
            )
            conn.execute(
                "ALTER TABLE editorial_publication_registry "
                "ENABLE TRIGGER editorial_publication_registry_fail_closed"
            )
            before = dict(
                conn.execute(
                    "SELECT * FROM editorial_publication_registry "
                    "WHERE member_bioguide_id = 'F000477' "
                    "AND issue_id = 'JUSTICE_PUBLIC_SAFETY'"
                ).fetchone()
            )
            before_counts = _counts(conn)
            with pytest.raises(StoreSafetyError, match="counts mismatch"):
                _preflight(conn, bundle)
            after = dict(
                conn.execute(
                    "SELECT * FROM editorial_publication_registry "
                    "WHERE member_bioguide_id = 'F000477' "
                    "AND issue_id = 'JUSTICE_PUBLIC_SAFETY'"
                ).fetchone()
            )
            assert after == before
            assert _counts(conn) == before_counts == {
                "batches": 2,
                "artifacts": 140,
                "relationships": 155,
                "publication_registry": 1,
            }
