from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.integration_candidate import governed_position_summary
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    EDUCATION_ACTIVATION_AUTHORITY_ID,
)
from scripts.editorial_artifact_store import StoreSafetyError, _connect
from scripts.foushee_education_workforce_publication_preparation import (
    ISSUE_ID,
    _apply,
    _counts,
    _registry_rows,
    _rollback,
    _selector_state,
    _state_fingerprint,
    activation_write_set_binding,
    build_authority,
    build_write_set,
    capture_preflight,
)
from test_m13n_r_education_publication_preparation_postgres import (
    _activation,
    _prepare_post_m12n_baseline,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = (
    ROOT / "docs/editorial/full_record_reviews/publication_activation_candidates/"
    "f000477_education_workforce_119_v1"
)
DATABASE_URL = os.getenv("M13N_DISPOSABLE_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="M13N_DISPOSABLE_DATABASE_URL is required"
)


def _load(name: str) -> dict:
    return json.loads((OUTPUT_ROOT / name).read_text(encoding="utf-8"))


def _synthetic_activation(candidate: dict) -> dict:
    subject = copy.deepcopy(candidate["prospective_authority_subject"])
    subject.pop("candidate_prepared_at_utc")
    subject.pop("expected_live_postconditions")
    subject["decision_recorded_at_utc"] = "2026-08-26T00:55:00Z"
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": EDUCATION_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def test_governed_m13n_graph_disposable_lifecycle() -> None:
    assert DATABASE_URL is not None
    packaged_write_set = _load("expected_production_write_set.json")
    preflight = _load("current_production_preflight.json")
    with _connect(DATABASE_URL, autocommit=False) as conn:
        _prepare_post_m12n_baseline(conn)
        before_counts = _counts(conn)
        before_fingerprint = _state_fingerprint(conn)
        before_registry = _registry_rows(conn)
        before_selector = _selector_state(conn, allow_test_activation_authority=True)
        assert before_counts == preflight["counts"]
        production_registry = preflight["baseline_registry_rows"]
        assert {
            row["issue_id"]: (
                row["natural_key"],
                row["content_sha256"],
                row["publicly_active"],
            )
            for row in before_registry
        } == {
            issue_id: (
                row["natural_key"],
                row["content_sha256"],
                row["publicly_active"],
            )
            for issue_id, row in production_registry.items()
        }

        disposable_preflight = capture_preflight(
            conn,
            deployed_commit=preflight["deployed_commit"],
            allow_test_activation_authority=True,
        )
        authority = build_authority(
            disposable_preflight,
            reviewer="synthetic-disposable-reviewer",
            decision_recorded_at_utc="2026-08-26T00:55:00Z",
        )
        write_set = build_write_set(disposable_preflight, authority)
        for key in (
            "accepted_site_integration_binding",
            "artifacts",
            "relationships",
            "expected_counts",
        ):
            assert write_set[key] == packaged_write_set[key]
        assert (
            write_set["publication_registry"]["presentation_natural_key"]
            == packaged_write_set["publication_registry"]["presentation_natural_key"]
        )
        activation = _activation(
            write_set,
            issue_id=ISSUE_ID,
            artifact_id=EDUCATION_ACTIVATION_AUTHORITY_ID,
            write_binding=activation_write_set_binding(write_set),
        )

        with pytest.raises(ValueError, match="synthetic activation authority"):
            with conn.transaction(force_rollback=True):
                _apply(
                    conn,
                    write_set,
                    authority,
                    activation,
                    allow_test_authority=False,
                )

        with pytest.raises(StoreSafetyError):
            with conn.transaction(force_rollback=True):
                conn.execute(
                    """INSERT INTO editorial_artifact_batches
                       (deterministic_batch_key,source_commit_sha,manifest_sha256,
                        status,artifact_count,relationship_count)
                       VALUES ('m13n-state-drift-test',%s,%s,'applied',0,0)""",
                    ("0" * 40, "0" * 64),
                )
                _apply(
                    conn,
                    write_set,
                    authority,
                    activation,
                    allow_test_authority=True,
                )

        with conn.transaction():
            first = _apply(
                conn,
                write_set,
                authority,
                activation,
                allow_test_authority=True,
            )
        assert first["already_applied"] is False
        assert first["postcheck"]["counts"] == write_set["expected_counts"]["after"]
        scopes = first["postcheck"]["selector"]["scopes"]
        assert scopes["119"][ISSUE_ID] == "reviewed_conclusion"
        assert scopes["all"][ISSUE_ID] == "reviewed_conclusion"
        assert scopes["118"][ISSUE_ID] == "receipts_only"
        for existing in (
            "JUSTICE_PUBLIC_SAFETY",
            "NATIONAL_SECURITY_FOREIGN",
            "ENVIRONMENT_ENERGY",
        ):
            assert scopes["119"][existing] == "reviewed_conclusion"
            assert scopes["all"][existing] == "reviewed_conclusion"
            assert scopes["118"][existing] == "receipts_only"

        payload = next(
            item["payload"]
            for item in write_set["artifacts"]
            if item["natural_key"]
            == "site-integration-candidate:f000477:education_workforce:119:v1"
        )
        presentation = payload["subject"]["presentation"]
        assert len(presentation["syntheses"]) == 0
        assert len(presentation["repeated_patterns"]) == 1
        assert len(presentation["notable_choices"]) == 1
        assert [
            presentation["overview"]["title"],
            presentation["repeated_patterns"][0]["title"],
            presentation["notable_choices"][0]["title"],
        ] == [
            "Education & Workforce",
            "Funding restrictions tied to institutional relationships or support",
            "H.R. 1048 amendment and final passage",
        ]
        evidence = payload["subject"]["preview_data"]["evidence_119"]
        assert (
            len(evidence) == len({row["canonical_action_id"] for row in evidence}) == 17
        )
        assert (
            len({row["governed_receipt_projection"]["episode_id"] for row in evidence})
            == 16
        )
        assert governed_position_summary(evidence, domain=ISSUE_ID) == {
            "domain": ISSUE_ID,
            "yea_count": 6,
            "nay_count": 10,
            "other_count": 1,
            "total_votes": 17,
            "recorded_votes": 16,
            "interpreted_support_count": 6,
            "interpreted_oppose_count": 10,
            "interpreted_other_count": 1,
            "interpreted_total": 17,
        }
        hr1005 = next(
            row for row in evidence if row["canonical_action_id"] == "house:119:1:312"
        )
        assert (
            hr1005["governed_receipt_projection"]["exact_choice_position_effect"]
            == "non_directional_not_voting"
        )

        with conn.transaction():
            second = _apply(
                conn,
                write_set,
                authority,
                activation,
                allow_test_authority=True,
            )
        assert second["already_applied"] is True
        assert second["postcheck"]["counts"] == first["postcheck"]["counts"]

        with conn.transaction():
            rolled_back = _rollback(
                conn,
                write_set,
                authority,
                activation,
                allow_test_authority=True,
            )
        assert rolled_back["counts"] == before_counts
        assert rolled_back["state_fingerprint_sha256"] == before_fingerprint
        assert _registry_rows(conn) == before_registry
        assert (
            _selector_state(conn, allow_test_activation_authority=True)
            == before_selector
        )


def test_governed_m13n_candidate_refuses_runtime_and_target_drift() -> None:
    candidate = _load("positive_activation_ratification_candidate.json")
    activation = _synthetic_activation(candidate)
    from scripts.foushee_education_workforce_publication_preparation import (
        validate_production_execution_inputs,
    )

    with pytest.raises(StoreSafetyError, match="non-exact production target"):
        validate_production_execution_inputs(
            database_url="postgresql://wrong.invalid/db",
            preflight=_load("current_production_preflight.json"),
            write_set=_load("expected_production_write_set.json"),
            candidate_authority=_load(
                "production_eligibility_publication_authority.json"
            ),
            activation_authority=activation,
            runtime_proof=None,
        )
    activation["subject"]["runtime_binding"]["reviewed_runtime_manifest_sha256"] = (
        "0" * 64
    )
    activation["activation_authority_subject_sha256"] = semantic_hash(
        activation["subject"]
    )
    assert activation["subject"]["production_target_identity_sha256"] != "0" * 64
    with pytest.raises((StoreSafetyError, ValueError)):
        from scripts.foushee_education_workforce_publication_preparation import (
            publication_metadata_for_activation,
        )

        publication_metadata_for_activation(
            _load("expected_production_write_set.json"),
            _load("production_eligibility_publication_authority.json"),
            activation,
            allow_test_authority=True,
        )
