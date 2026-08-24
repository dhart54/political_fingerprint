from __future__ import annotations

import copy
import os

import pytest
from fastapi.testclient import TestClient

from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_artifacts.publication_activation import load_activation_bundle
from app.editorial_presentations.selector import (
    select_public_presentations as select_public_presentations_with_authority,
)
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_ID as NATIONAL_SECURITY_ACTIVATION_AUTHORITY_ID,
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
    POSITIVE_AUTHORIZATIONS,
    active_site_integration_candidate as active_candidate_with_authority,
)
from app.main import app
from scripts.editorial_artifact_store import StoreSafetyError, _connect
from scripts.foushee_justice_full_record_activation import (
    _apply as apply_justice_full_record,
    build_bundle as build_justice_full_record_bundle,
    preflight as justice_full_record_preflight,
)
from scripts.foushee_justice_publication_activation import (
    _apply as apply_justice_compact,
)
from scripts.foushee_environment_energy_publication_preparation import (
    AUTHORITY_PATH,
    ISSUE_ID,
    POST_M12M_MAIN,
    WRITE_SET_PATH,
    _apply,
    _counts,
    _load,
    _registry_rows,
    _rollback,
    _selector_state,
    _state_fingerprint,
    activation_write_set_binding,
    build_authority,
    build_write_set,
    capture_preflight,
)
from scripts.foushee_national_security_publication_activation import (
    POST_M11M_MAIN,
    _apply as apply_national_security,
    activation_write_set_binding as national_security_write_set_binding,
    build_authority as build_national_security_authority,
    build_write_set as build_national_security_write_set,
    capture_preflight as capture_national_security_preflight,
)


DATABASE_URL = os.getenv("M12N_DISPOSABLE_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="M12N_DISPOSABLE_DATABASE_URL is required",
)


def _prepare_current_justice_state(conn) -> None:
    compact = load_activation_bundle()
    with conn.transaction():
        apply_justice_compact(conn, compact)
    justice_preflight = justice_full_record_preflight(conn, POST_M11M_MAIN)
    justice_bundle = build_justice_full_record_bundle(justice_preflight, POST_M11M_MAIN)
    with conn.transaction():
        apply_justice_full_record(conn, justice_bundle)
    m11n_preflight = capture_national_security_preflight(
        conn, deployed_commit=POST_M11M_MAIN
    )
    m11n_authority = build_national_security_authority(m11n_preflight)
    m11n_write_set = build_national_security_write_set(m11n_preflight, m11n_authority)
    m11n_activation = _synthetic_national_security_authority(m11n_write_set)
    with conn.transaction():
        apply_national_security(
            conn,
            m11n_write_set,
            m11n_authority,
            m11n_activation,
            allow_test_authority=True,
        )


def _synthetic_national_security_authority(write_set: dict) -> dict:
    metadata = write_set["publication_registry"]["publication_metadata"]
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-14T12:00:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
        "congress": 119,
        "accepted_m11m_binding": write_set["accepted_m11m_binding"],
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "activation_write_set_binding": national_security_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "presentation_natural_key": write_set["publication_registry"][
                "presentation_natural_key"
            ],
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": metadata["rollback_binding"],
        "runtime_binding": {
            "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
                "reviewed_runtime_manifest_sha256"
            ],
            "reviewed_commit": write_set["preflight_binding"]["deployed_commit"],
            "deployed_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_proof_subject_sha256": "b" * 64,
        },
        "production_target_identity_sha256": metadata[
            "production_target_identity_sha256"
        ],
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": NATIONAL_SECURITY_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def _synthetic_activation_authority(write_set: dict) -> dict:
    metadata = write_set["publication_registry"]["publication_metadata"]
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-14T12:00:00Z",
        "reviewer": "synthetic-disposable-reviewer",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": ISSUE_ID,
        "congress": 119,
        "accepted_site_integration_binding": write_set[
            "accepted_site_integration_binding"
        ],
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "activation_write_set_binding": activation_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": ISSUE_ID,
            "presentation_natural_key": write_set["publication_registry"][
                "presentation_natural_key"
            ],
            "presentation_artifact_version": 1,
        },
        "presentation_content_sha256": metadata["active_artifact_sha256"],
        "preflight_binding": metadata["preflight_binding"],
        "rollback_binding": metadata["rollback_binding"],
        "runtime_binding": {
            "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
                "reviewed_runtime_manifest_sha256"
            ],
            "reviewed_commit": write_set["preflight_binding"]["deployed_commit"],
            "deployed_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_commit": write_set["preflight_binding"]["deployed_commit"],
        },
        "ratification_runtime_evidence_binding": {
            "runtime_health_proof_subject_sha256": "a" * 64,
            "captured_at_utc": "2026-08-14T11:59:00Z",
            "reviewed_runtime_manifest_sha256": metadata["reviewed_runtime_binding"][
                "reviewed_runtime_manifest_sha256"
            ],
            "deployed_commit": write_set["preflight_binding"]["deployed_commit"],
            "health_commit": write_set["preflight_binding"]["deployed_commit"],
        },
        "production_target_identity_sha256": metadata[
            "production_target_identity_sha256"
        ],
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": ENVIRONMENT_ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": True,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def test_m12n_apply_idempotency_drift_guard_and_exact_rollback(monkeypatch) -> None:
    assert DATABASE_URL is not None
    with _connect(DATABASE_URL, autocommit=False) as conn:
        _prepare_current_justice_state(conn)
        governed_authority = _load(AUTHORITY_PATH)
        governed_write_set = _load(WRITE_SET_PATH)
        preflight = capture_preflight(
            conn,
            deployed_commit=POST_M12M_MAIN,
            allow_test_activation_authority=True,
        )
        authority = build_authority(preflight)
        write_set = build_write_set(preflight, authority)
        assert governed_authority["authority_subject_sha256"] == (
            "d3fda11480c9ce2bbc72db26130ac16b464280e42f27f9a2c03193b2e58b4fa6"
        )
        assert governed_write_set["write_set_subject_sha256"] == (
            "ab7cef360fd9323ae22ffe418d7475ad54ea247a301e16fd29b795877550033f"
        )
        for key in (
            "accepted_site_integration_binding",
            "artifacts",
            "relationships",
            "expected_counts",
            "write_caps",
            "public_smoke_contract",
            "activation_authorized",
            "production_write_authorized",
        ):
            assert write_set[key] == governed_write_set[key]
        assert {
            key: write_set["publication_registry"][key]
            for key in (
                "member_bioguide_id",
                "issue_id",
                "presentation_natural_key",
                "presentation_artifact_version",
                "publicly_active",
            )
        } == {
            key: governed_write_set["publication_registry"][key]
            for key in (
                "member_bioguide_id",
                "issue_id",
                "presentation_natural_key",
                "presentation_artifact_version",
                "publicly_active",
            )
        }
        for key in (
            "delete_registry_primary_key",
            "delete_relationship_count",
            "delete_artifact_natural_keys",
            "delete_batch_key",
            "restore_counts",
        ):
            assert write_set["rollback"][key] == governed_write_set["rollback"][key]
        for issue_key in (
            "justice_registry_row_unchanged",
            "national_security_registry_row_unchanged",
        ):
            assert (
                write_set["rollback"][issue_key]["content_sha256"]
                == (governed_write_set["rollback"][issue_key]["content_sha256"])
            )
            assert (
                write_set["rollback"][issue_key]["natural_key"]
                == (governed_write_set["rollback"][issue_key]["natural_key"])
            )
        activation_authority = _synthetic_activation_authority(write_set)
        before_counts = _counts(conn)
        before_fingerprint = _state_fingerprint(conn)
        before_registry = _registry_rows(conn)
        before_selector = _selector_state(conn)
        before_publication_rows = EditorialArtifactRepository(
            conn
        ).publication_selector()
        assert before_counts == write_set["expected_counts"]["before"]
        assert (
            before_fingerprint
            == write_set["preflight_binding"]["state_fingerprint_sha256"]
        )

        with pytest.raises(ValueError, match="synthetic activation authority"):
            with conn.transaction(force_rollback=True):
                _apply(
                    conn,
                    write_set,
                    authority,
                    activation_authority,
                    allow_test_authority=False,
                )

        wrong_binding = copy.deepcopy(activation_authority)
        wrong_binding["subject"]["activation_write_set_binding"][
            "write_set_subject_sha256"
        ] = "f" * 64
        wrong_binding["activation_authority_subject_sha256"] = semantic_hash(
            wrong_binding["subject"]
        )
        with pytest.raises(ValueError, match="binding differs"):
            with conn.transaction(force_rollback=True):
                _apply(
                    conn,
                    write_set,
                    authority,
                    wrong_binding,
                    allow_test_authority=True,
                )

        drifted = copy.deepcopy(write_set)
        drifted["preflight_binding"]["state_fingerprint_sha256"] = "0" * 64
        drifted["publication_registry"]["publication_metadata"]["preflight_binding"][
            "state_fingerprint_sha256"
        ] = "0" * 64
        drifted_body = copy.deepcopy(drifted)
        drifted_body.pop("write_set_subject_sha256")
        drifted["write_set_subject_sha256"] = semantic_hash(drifted_body)
        drift_activation = _synthetic_activation_authority(drifted)
        with pytest.raises(StoreSafetyError, match="drifted from M12N preflight"):
            with conn.transaction(force_rollback=True):
                _apply(
                    conn,
                    drifted,
                    authority,
                    drift_activation,
                    allow_test_authority=True,
                )

        with conn.transaction():
            first = _apply(
                conn,
                write_set,
                authority,
                activation_authority,
                allow_test_authority=True,
            )
        assert first["already_applied"] is False
        assert first["postcheck"]["counts"] == write_set["expected_counts"]["after"]
        assert len(first["artifact_ids"]) == 3
        active_selector = _selector_state(conn, allow_test_activation_authority=True)[
            "scopes"
        ]
        assert active_selector["119"][ISSUE_ID]["tier"] == "reviewed_conclusion"
        assert active_selector["all"][ISSUE_ID]["tier"] == "reviewed_conclusion"
        assert active_selector["118"][ISSUE_ID]["tier"] == "receipts_only"

        publication_rows = EditorialArtifactRepository(conn).publication_selector()
        candidates = {
            issue_id: active_candidate_with_authority(
                publication_rows,
                member_bioguide_id="F000477",
                issue_id=issue_id,
                allow_test_authority=True,
            )
            for issue_id in ("NATIONAL_SECURITY_FOREIGN", ISSUE_ID)
        }
        assert all(candidates.values())

        def base_evidence(*, domain: str, scope: str, **_kwargs) -> dict:
            prior = {
                "canonical_action_id": "house:118:1:999",
                "congress": 118,
                "issue_domain": domain,
                "position": "yea",
            }
            current = {
                "canonical_action_id": "house:119:1:999",
                "congress": 119,
                "issue_domain": domain,
                "position": "nay",
            }
            evidence = [prior] if scope == "118" else [current]
            if scope == "all":
                evidence = [current, prior]
            return {"domain": domain, "evidence": evidence}

        monkeypatch.setattr(
            "app.api.editorial_presentations.get_legislator_profile",
            lambda **_kwargs: {"bioguide_id": "F000477"},
        )
        monkeypatch.setattr(
            "app.api.editorial_presentations._load_publication_rows",
            lambda: publication_rows,
        )
        monkeypatch.setattr(
            "app.api.editorial_presentations.select_public_presentations",
            lambda rows, **kwargs: select_public_presentations_with_authority(
                rows, **kwargs, allow_test_activation_authority=True
            ),
        )
        monkeypatch.setattr(
            "app.api.positions.get_legislator_profile",
            lambda **_kwargs: {"bioguide_id": "F000477"},
        )
        monkeypatch.setattr(
            "app.api.positions._load_publication_rows", lambda: publication_rows
        )
        monkeypatch.setattr(
            "app.api.positions.active_site_integration_candidate",
            lambda rows, **kwargs: active_candidate_with_authority(
                rows, **kwargs, allow_test_authority=True
            ),
        )
        monkeypatch.setattr(
            "app.api.positions._has_governed_presentation_candidate",
            lambda **_kwargs: False,
        )
        monkeypatch.setattr(
            "app.api.positions.get_position_response",
            lambda **kwargs: {
                "legislator_id": kwargs["legislator_id"],
                "scope": kwargs["scope"],
                "positions": [
                    {"domain": "JUSTICE_PUBLIC_SAFETY", "total_votes": 10},
                    {"domain": "NATIONAL_SECURITY_FOREIGN", "total_votes": 0},
                    {"domain": ISSUE_ID, "total_votes": 0},
                ],
            },
        )
        monkeypatch.setattr(
            "app.api.positions.get_position_evidence_response", base_evidence
        )

        client = TestClient(app)
        environment_presentation = None
        for scope, expected_environment_tier in (
            ("119", "reviewed_conclusion"),
            ("all", "reviewed_conclusion"),
            ("118", "receipts_only"),
        ):
            presentations = client.get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": scope},
            )
            assert presentations.status_code == 200
            presentation_rows = {
                item["issue_id"]: item for item in presentations.json()["presentations"]
            }
            environment_presentation = presentation_rows[ISSUE_ID]
            assert environment_presentation["tier"] == expected_environment_tier
            before_presentations = select_public_presentations_with_authority(
                before_publication_rows,
                legislator_id="leg_valerie_p_foushee",
                member_bioguide_id="F000477",
                scope=scope,
                allow_test_activation_authority=True,
            )
            before_by_issue = {
                item["issue_id"]: item for item in before_presentations["presentations"]
            }
            assert (
                presentation_rows["JUSTICE_PUBLIC_SAFETY"]
                == before_by_issue["JUSTICE_PUBLIC_SAFETY"]
            )
            assert (
                presentation_rows["NATIONAL_SECURITY_FOREIGN"]
                == before_by_issue["NATIONAL_SECURITY_FOREIGN"]
            )

        assert environment_presentation is not None
        presentations_119 = client.get(
            "/legislators/leg_valerie_p_foushee/editorial-presentations",
            params={"scope": "119"},
        ).json()["presentations"]
        environment_presentation = next(
            item for item in presentations_119 if item["issue_id"] == ISSUE_ID
        )
        assert len(environment_presentation["syntheses"]) == 1
        assert len(environment_presentation["repeated_patterns"]) == 3
        wording_items = [
            environment_presentation["overview"],
            *environment_presentation["syntheses"],
            *environment_presentation["repeated_patterns"],
        ]
        support_counts = {
            item["title"]: len(item["public_supporting_action_ids"])
            for item in wording_items
        }
        assert support_counts == {
            "Environment & Energy": 13,
            "Congressional efforts to overturn agency decisions": 13,
            "California vehicle-emissions waivers": 2,
            "Appliance and commercial-equipment rules": 4,
            "Bureau of Land Management decisions": 7,
        }

        positions = client.get(
            "/legislators/leg_valerie_p_foushee/positions", params={"scope": "119"}
        )
        assert positions.status_code == 200
        position_rows = {row["domain"]: row for row in positions.json()["positions"]}
        assert position_rows["JUSTICE_PUBLIC_SAFETY"]["total_votes"] == 10
        assert position_rows[ISSUE_ID] == {
            "domain": ISSUE_ID,
            "yea_count": 15,
            "nay_count": 47,
            "other_count": 1,
            "total_votes": 63,
            "recorded_votes": 62,
            "interpreted_support_count": 15,
            "interpreted_oppose_count": 47,
            "interpreted_other_count": 1,
            "interpreted_total": 63,
        }
        assert position_rows["NATIONAL_SECURITY_FOREIGN"] == {
            "domain": "NATIONAL_SECURITY_FOREIGN",
            "yea_count": 39,
            "nay_count": 43,
            "other_count": 0,
            "total_votes": 82,
            "recorded_votes": 82,
            "interpreted_support_count": 39,
            "interpreted_oppose_count": 42,
            "interpreted_other_count": 0,
            "interpreted_total": 81,
        }

        for scope, expected_count, expected_119 in (
            ("119", 63, 63),
            ("all", 64, 63),
            ("118", 1, 0),
        ):
            evidence_response = client.get(
                f"/legislators/leg_valerie_p_foushee/positions/{ISSUE_ID}/evidence",
                params={"scope": scope},
            )
            assert evidence_response.status_code == 200
            evidence_rows = evidence_response.json()["evidence"]
            assert len(evidence_rows) == expected_count
            governed_119 = [
                row for row in evidence_rows if int(row.get("congress", 0) or 0) == 119
            ]
            assert len(governed_119) == expected_119
            assert (
                len({row["canonical_action_id"] for row in governed_119})
                == expected_119
            )
            if governed_119:
                assert all(
                    row.get("governed_receipt_projection") for row in governed_119
                )
                hr_6387 = next(
                    row
                    for row in governed_119
                    if row["canonical_action_id"] == "house:119:2:136"
                )
                assert (
                    hr_6387["governed_receipt_projection"][
                        "exact_choice_position_effect"
                    ]
                    == "non_directional_not_voting"
                )

        with conn.transaction():
            second = _apply(
                conn,
                write_set,
                authority,
                activation_authority,
                allow_test_authority=True,
            )
        assert second["already_applied"] is True
        assert second["postcheck"]["counts"] == write_set["expected_counts"]["after"]
        registry = _registry_rows(conn)
        assert len(registry) == 3
        assert (
            next(row for row in registry if row["issue_id"] == ISSUE_ID)["natural_key"]
            == write_set["publication_registry"]["presentation_natural_key"]
        )

        with conn.transaction():
            rolled_back = _rollback(
                conn,
                write_set,
                authority,
                activation_authority,
                allow_test_authority=True,
            )
        assert rolled_back["counts"] == before_counts
        assert rolled_back["state_fingerprint_sha256"] == before_fingerprint
        assert _registry_rows(conn) == before_registry
        assert _selector_state(conn) == before_selector
