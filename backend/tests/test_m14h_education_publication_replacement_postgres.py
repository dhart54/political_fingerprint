from __future__ import annotations

import copy
import os

import pytest

from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.compiler import canonical_digest
from scripts.editorial_artifact_store import _connect
from scripts.foushee_education_workforce_m14h_replacement import (
    BASE_SHA,
    ISSUE_ID,
    PRESENTATION_KEY,
    _counts,
    _registry_identity,
    _registry_rows,
    _selector_state,
    _state_fingerprint,
    apply_replacement,
    build_package,
    capture_preflight,
    load_candidate,
    rollback_replacement,
    target_identity,
)
from scripts.foushee_education_workforce_publication_preparation import (
    _apply as apply_m13,
    activation_write_set_binding as m13_write_set_binding,
    build_authority as build_m13_authority,
    build_write_set as build_m13_write_set,
    capture_preflight as capture_m13_preflight,
)
from test_m13n_r_education_publication_preparation_postgres import (
    _activation,
    _prepare_post_m12n_baseline,
)

DATABASE_URL = os.getenv("M14H_DISPOSABLE_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="M14H_DISPOSABLE_DATABASE_URL is required"
)


def _prepare_old_education(conn) -> None:
    _prepare_post_m12n_baseline(conn)
    preflight = capture_m13_preflight(
        conn, deployed_commit="a" * 40, allow_test_activation_authority=True
    )
    authority = build_m13_authority(preflight)
    write_set = build_m13_write_set(preflight, authority)
    activation = _activation(
        write_set,
        issue_id=ISSUE_ID,
        artifact_id="publication-activation-authority:f000477:education_workforce:119:v1",
        write_binding=m13_write_set_binding(write_set),
    )
    with conn.transaction():
        apply_m13(
            conn, write_set, authority, activation, allow_test_authority=True
        )


def _sealed(template: dict) -> dict:
    subject = copy.deepcopy(template["subject"])
    subject["decision_recorded_at_utc"] = "2026-09-03T12:00:00Z"
    subject["reviewer"] = "synthetic-disposable-reviewer"
    return {
        "schema_version": template["schema_version"],
        "artifact_id": template["artifact_id"],
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": canonical_digest(subject),
    }


def _package(conn):
    preflight = capture_preflight(
        conn,
        production_target_identity_sha256=target_identity(DATABASE_URL, "disposable"),
        allow_test_authority=True,
    )
    package = build_package(preflight, backend_health_commit=BASE_SHA)
    write_set = package["publication_replacement_write_set.json"]
    activation = _sealed(package["positive_replacement_activation_candidate.json"])
    return preflight, package, write_set, activation


def test_disposable_apply_idempotency_fault_rollback_and_selector() -> None:
    assert DATABASE_URL is not None
    with _connect(DATABASE_URL, autocommit=False) as conn:
        _prepare_old_education(conn)
        before_counts = _counts(conn)
        before_fingerprint = _state_fingerprint(conn)
        before_registry = _registry_rows(conn)
        before_selector = _selector_state(conn, allow_test_authority=True)
        prior_id = next(
            row["artifact_id"] for row in before_registry if row["issue_id"] == ISSUE_ID
        )
        prior_artifact = conn.execute(
            "SELECT to_jsonb(a) AS row FROM editorial_artifact_versions a WHERE artifact_id=%s",
            (prior_id,),
        ).fetchone()["row"]

        _, _, write_set, activation = _package(conn)
        for fault in ("batch", "artifacts", "relationships", "registry_update"):
            with pytest.raises(RuntimeError, match="injected failure"):
                with conn.transaction():
                    apply_replacement(
                        conn, write_set, activation,
                        allow_test_authority=True, fault_after=fault,
                    )
            assert _counts(conn) == before_counts
            assert _state_fingerprint(conn) == before_fingerprint
            assert _registry_rows(conn) == before_registry

        with conn.transaction():
            applied = apply_replacement(
                conn, write_set, activation, allow_test_authority=True
            )
        assert applied["status"] == "APPLIED"
        assert applied["mutation_counts"] == {
            "insert_batches": 1,
            "insert_artifacts": 3,
            "insert_relationships": 2,
            "insert_registry_rows": 0,
            "update_registry_rows": 1,
            "other_updates": 0,
            "deletes_during_activation": 0,
            "unauthorized_table_writes": 0,
        }
        assert _counts(conn) == {
            **before_counts,
            "batches": before_counts["batches"] + 1,
            "artifacts": before_counts["artifacts"] + 3,
            "relationships": before_counts["relationships"] + 2,
        }
        after_registry = _registry_rows(conn)
        assert len(after_registry) == len(before_registry)
        education = next(row for row in after_registry if row["issue_id"] == ISSUE_ID)
        assert education["natural_key"] == PRESENTATION_KEY
        inserted = conn.execute(
            """SELECT payload_jsonb,supersedes_artifact_id
                 FROM editorial_artifact_versions WHERE artifact_id=%s""",
            (education["artifact_id"],),
        ).fetchone()
        assert inserted["payload_jsonb"] == load_candidate()
        assert inserted["supersedes_artifact_id"] == prior_id
        assert conn.execute(
            "SELECT to_jsonb(a) AS row FROM editorial_artifact_versions a WHERE artifact_id=%s",
            (prior_id,),
        ).fetchone()["row"] == prior_artifact
        before_other = {
            row["issue_id"]: _registry_identity(row)
            for row in before_registry if row["issue_id"] != ISSUE_ID
        }
        after_other = {
            row["issue_id"]: _registry_identity(row)
            for row in after_registry if row["issue_id"] != ISSUE_ID
        }
        assert after_other == before_other
        selector = _selector_state(conn, allow_test_authority=True)
        assert [selector["scopes"][scope][ISSUE_ID] for scope in ("119", "all", "118")] == [
            "reviewed_conclusion", "reviewed_conclusion", "receipts_only"
        ]
        presentation = next(
            row["payload_jsonb"]
            for row in EditorialArtifactRepository(conn).publication_selector()
            if row["issue_id"] == ISSUE_ID
        )["subject"]["presentation"]
        assert len(presentation["repeated_patterns"]) == 2
        assert len(presentation["notable_choices"]) == 1
        assert presentation["notable_choices"][0]["direction"] == "mixed"
        findings = [*presentation["repeated_patterns"], *presentation["notable_choices"]]
        assert sum(len(item["public_supporting_action_ids"]) for item in findings) == 6
        assert len(presentation["overview"]["public_supporting_action_ids"]) == 4
        assert len(presentation["overview"]["public_supporting_episode_ids"]) == 3
        assert len(presentation["limitations"]) + sum(
            len(item["limitations"]) for item in findings
        ) == 7
        assert len(presentation["exact_action_receipts"]) == 17
        assert len({
            row["governed_receipt_projection"]["episode_id"]
            for row in load_candidate()["subject"]["receipt_projections"]
        }) == 16
        hr5408 = next(
            row for row in presentation["exact_action_receipts"]
            if row["canonical_action_id"] == "house:119:2:216"
        )
        assert "Current wages, hours, and employment terms" in hr5408["exact_action_meaning"]
        hr1005 = next(
            row for row in presentation["exact_action_receipts"]
            if row["canonical_action_id"] == "house:119:1:312"
        )
        assert hr1005["exact_choice_position_effect"] == "resolved_non_directional"
        hr1048 = [
            row for row in presentation["exact_action_receipts"]
            if row["episode_id"] == "hr-1048-amendment-and-final-passage"
        ]
        assert len(hr1048) == 2
        assert all(
            source["label"] == source["public_label"]
            for receipt in presentation["exact_action_receipts"]
            for source in [*receipt["vote_sources"], *receipt["action_meaning_sources"]]
        )

        with conn.transaction():
            second = apply_replacement(
                conn, write_set, activation, allow_test_authority=True
            )
        assert second == {"status": "ALREADY_APPLIED", "writes": 0}

        with conn.transaction():
            rolled_back = rollback_replacement(
                conn, write_set, activation, allow_test_authority=True
            )
        assert rolled_back["status"] == "ROLLED_BACK"
        assert _counts(conn) == before_counts
        assert _state_fingerprint(conn) == before_fingerprint
        assert _registry_rows(conn) == before_registry
        assert _selector_state(conn, allow_test_authority=True) == before_selector
