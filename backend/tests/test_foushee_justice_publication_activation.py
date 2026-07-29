from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_artifacts.publication_activation import (
    ACTIVE_ARTIFACT_SHA256,
    BUNDLE_ID,
    PRESENTATION_KEY,
    SOURCE_COMMIT,
    _reviewed_text_file_sha256,
    build_activation_bundle,
    build_pre_activation_baseline,
    load_activation_bundle,
    validate_activation_bundle,
)
from app.editorial_artifacts.reconciliation import (
    compose_pre_activation_fingerprint,
    validate_pre_activation_fingerprint,
)
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_justice_publication_activation import (
    _exact_deployed_commit,
    main,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SUCCESS_RECEIPT_PATH = (
    REPOSITORY_ROOT
    / "docs/editorial/publication_activations"
    / "foushee_justice_public_safety_119_successful_activation_receipt_v1.json"
)
SUCCESS_RECEIPT_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "docs/editorial_publication_successful_activation_receipt_v1.schema.json"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_activation_bundle_is_deterministic_and_exact() -> None:
    bundle = load_activation_bundle()
    assert bundle == build_activation_bundle()
    assert bundle["bundle_id"] == BUNDLE_ID
    assert bundle["expected_counts"]["before"] == {
        "batches": 2,
        "artifacts": 140,
        "relationships": 155,
        "publication_registry": 0,
    }
    assert bundle["expected_counts"]["after"] == {
        "batches": 3,
        "artifacts": 143,
        "relationships": 157,
        "publication_registry": 1,
    }
    assert bundle["pre_activation_baseline"] == build_pre_activation_baseline()
    assert [
        item["database_batch_id"]
        for item in bundle["pre_activation_baseline"]["governed_batches"]
    ] == [1, 8]


def test_activation_source_hashes_are_checkout_eol_independent(
    tmp_path: Path,
) -> None:
    lf = tmp_path / "source-lf.json"
    crlf = tmp_path / "source-crlf.json"
    lf.write_bytes(b'{\n  "reviewed": true\n}\n')
    crlf.write_bytes(b'{\r\n  "reviewed": true\r\n}\r\n')
    assert _reviewed_text_file_sha256(lf) == _reviewed_text_file_sha256(crlf)


def test_active_presentation_is_exact_approved_candidate() -> None:
    bundle = load_activation_bundle()
    presentation = next(
        item
        for item in bundle["artifacts"]
        if item["natural_key"] == PRESENTATION_KEY
    )
    assert presentation["content_sha256"] == ACTIVE_ARTIFACT_SHA256
    assert presentation["payload"]["controls"]["editorial"][
        "human_approval_status"
    ] == "human_approved"
    assert presentation["payload"]["controls"]["benchmark"][
        "status"
    ] == "gold_benchmark"
    assert presentation["payload"]["controls"]["production"]["eligible"] is True
    assert presentation["payload"]["controls"]["publication"]["active"] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda bundle: bundle["expected_counts"]["after"].update(
            {"publication_registry": 2}
        ),
        lambda bundle: bundle["artifacts"][0].update(
            {"content_sha256": "0" * 64}
        ),
        lambda bundle: bundle["relationships"].pop(),
        lambda bundle: bundle["publication_registry"]["publication_metadata"][
            "approval_receipt"
        ].update({"receipt_id": "approval-receipt:substituted"}),
        lambda bundle: bundle["pre_activation_baseline"]["governed_batches"][
            1
        ].update({"graph_sha256": "0" * 64}),
    ],
)
def test_activation_bundle_fails_closed_on_mutation(mutate) -> None:
    bundle = copy.deepcopy(build_activation_bundle())
    mutate(bundle)
    with pytest.raises(ValueError):
        validate_activation_bundle(bundle)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["input"].update(
            {"schema_object_sha256": "0" * 64}
        ),
        lambda value: value["input"]["batches"][0].update(
            {"database_batch_id": 7}
        ),
        lambda value: value["input"]["batches"][1].update(
            {"database_batch_id": 9}
        ),
        lambda value: value["input"]["batches"][0].update(
            {"deterministic_batch_key": "substituted"}
        ),
        lambda value: value["input"]["batches"][1].update(
            {"deterministic_batch_key": "substituted"}
        ),
        lambda value: value["input"]["batches"][0].update(
            {"source_commit_sha": "0" * 40}
        ),
        lambda value: value["input"]["batches"][1].update(
            {"source_commit_sha": "0" * 40}
        ),
        lambda value: value["input"]["batches"][0].update(
            {"manifest_sha256": "0" * 64}
        ),
        lambda value: value["input"]["batches"][1].update(
            {"manifest_sha256": "0" * 64}
        ),
        lambda value: value["input"]["batches"][0].update(
            {"graph_sha256": "0" * 64}
        ),
        lambda value: value["input"]["batches"][1].update(
            {"graph_sha256": "0" * 64}
        ),
        lambda value: value["input"]["artifact_set"].update(
            {"sha256": "0" * 64}
        ),
        lambda value: value["input"]["relationship_set"].update(
            {"sha256": "0" * 64}
        ),
        lambda value: value["input"]["registry"].update({"count": 1}),
        lambda value: value["input"]["registry"].update(
            {"sha256": "0" * 64}
        ),
        lambda value: value["input"]["target_absence"]["results"][
            "artifact_rows"
        ].append(
            {
                "artifact_type": "issue_public_presentation",
                "natural_key": PRESENTATION_KEY,
                "artifact_version": 1,
                "content_sha256": ACTIVE_ARTIFACT_SHA256,
            }
        ),
    ],
)
def test_reconciled_fingerprint_fails_closed_on_component_mutation(
    mutate,
) -> None:
    fingerprint = copy.deepcopy(
        build_pre_activation_baseline()["reconciled_fingerprint"]
    )
    expected_constant = fingerprint["sha256"]
    mutate(fingerprint)
    fingerprint["sha256"] = expected_constant
    with pytest.raises(ValueError, match="fingerprint digest mismatch"):
        validate_pre_activation_fingerprint(fingerprint)


def test_reconciled_fingerprint_is_canonically_composed() -> None:
    baseline = build_pre_activation_baseline()
    fingerprint = baseline["reconciled_fingerprint"]
    fingerprint_input = fingerprint["input"]
    recomposed = compose_pre_activation_fingerprint(
        schema_object_sha256=fingerprint_input["schema_object_sha256"],
        batches=fingerprint_input["batches"],
        artifact_count=fingerprint_input["artifact_set"]["count"],
        artifact_set_sha256=fingerprint_input["artifact_set"]["sha256"],
        relationship_count=fingerprint_input["relationship_set"]["count"],
        relationship_set_sha256=fingerprint_input["relationship_set"]["sha256"],
        registry_count=fingerprint_input["registry"]["count"],
        registry_sha256=fingerprint_input["registry"]["sha256"],
        target_absence=fingerprint_input["target_absence"],
    )
    assert recomposed == fingerprint


def test_tool_rejects_wrong_bundle_digest_and_schema_expectation() -> None:
    with pytest.raises(StoreSafetyError, match="bundle digest"):
        main(["verify-bundle", "--bundle-sha256", "0" * 64])
    with pytest.raises(StoreSafetyError, match="migration 0016"):
        main(["verify-bundle", "--required-schema", "0017"])


def test_tool_rejects_unproven_deployed_commit() -> None:
    with pytest.raises(StoreSafetyError, match="not proven"):
        _exact_deployed_commit("0" * 40)


def test_exact_compatible_deployed_commit_is_accepted() -> None:
    assert _exact_deployed_commit(SOURCE_COMMIT) == {
        "required_ancestor": SOURCE_COMMIT,
        "supplied_identity": SOURCE_COMMIT,
        "compatible": True,
        "verification_method": "git_merge_base_is_ancestor",
    }


@pytest.mark.parametrize(
    "identity",
    [
        "",
        "unknown",
        "f" * 39,
        "88d6f3446f54b07735e084cbc958c1614b190fab",
    ],
)
def test_missing_malformed_placeholder_or_incompatible_deployment_fails(
    identity: str,
) -> None:
    if not identity:
        with pytest.raises(StoreSafetyError, match="deployed backend commit"):
            main(["preflight", "--bundle-id", BUNDLE_ID])
    else:
        with pytest.raises(StoreSafetyError):
            _exact_deployed_commit(identity)


def test_wrong_bundle_id_fails_before_database_access() -> None:
    with pytest.raises(StoreSafetyError, match="bundle ID"):
        main(
            [
                "preflight",
                "--bundle-id",
                "substituted-bundle",
                "--deployed-commit",
                SOURCE_COMMIT,
            ]
        )


def test_wrong_confirmed_bundle_digest_fails_before_mutation() -> None:
    with pytest.raises(StoreSafetyError, match="confirm-bundle-digest"):
        main(
            [
                "apply",
                "--bundle-id",
                BUNDLE_ID,
                "--confirm-bundle-digest",
                "0" * 64,
                "--deployed-commit",
                SOURCE_COMMIT,
                "--database-url",
                "postgresql://unused@127.0.0.1:1/unused",
            ]
        )


def test_runbook_distinguishes_semantic_availability_and_cosmetic_failures() -> None:
    runbook = (
        Path(__file__).resolve().parents[2]
        / "docs/workflows/foushee-justice-publication-activation.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(runbook.split())
    assert "Rollback immediately after any semantic or identity failure" in normalized
    assert "two confirmed attempts within 60 seconds" in normalized
    assert (
        "One transient availability failure alone does not meet the rollback threshold"
        in normalized
    )
    assert "cosmetic-only defect" in normalized
    assert "all seven row inserts" in normalized
    assert "all five inserts" not in normalized


def test_db_modes_require_explicit_bundle_id_at_argument_boundary() -> None:
    with pytest.raises(SystemExit):
        main(["preflight", "--deployed-commit", "0" * 40])


def test_preflight_rejects_unproven_deployment_before_database_access() -> None:
    with pytest.raises(StoreSafetyError, match="not proven"):
        main(
            [
                "preflight",
                "--bundle-id",
                BUNDLE_ID,
                "--deployed-commit",
                "0" * 40,
                "--database-url",
                "postgresql://unused:unused@127.0.0.1:1/unused",
            ]
        )


def test_successful_activation_receipt_validates_and_hashes_exactly() -> None:
    receipt = _json(SUCCESS_RECEIPT_PATH)
    schema = _json(SUCCESS_RECEIPT_SCHEMA_PATH)
    Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    ).validate(receipt)

    assert receipt["activation_result_sha256"] == semantic_hash(
        receipt["activation_result"]
    )
    receipt_body = copy.deepcopy(receipt)
    claimed_receipt_sha256 = receipt_body.pop("canonical_receipt_sha256")
    assert claimed_receipt_sha256 == semantic_hash(receipt_body)
    assert claimed_receipt_sha256 == (
        "1d1d29392b9058058649e67341a3af78d9a2fa4921b7682380baf97be3326c9c"
    )


def test_successful_activation_receipt_matches_approved_bundle_identities() -> None:
    receipt = _json(SUCCESS_RECEIPT_PATH)
    bundle = load_activation_bundle()
    assert receipt["bundle"] == {
        "bundle_id": bundle["bundle_id"],
        "bundle_sha256": bundle["bundle_sha256"],
    }
    assert bundle["bundle_sha256"] == (
        "df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813"
    )

    receipt_artifacts = [
        {
            key: artifact[key]
            for key in (
                "artifact_type",
                "natural_key",
                "artifact_version",
                "content_sha256",
            )
        }
        for artifact in receipt["database_identities"]["artifacts"]
    ]
    bundle_artifacts = [
        {
            key: artifact[key]
            for key in (
                "artifact_type",
                "natural_key",
                "artifact_version",
                "content_sha256",
            )
        }
        for artifact in bundle["artifacts"]
    ]
    assert receipt_artifacts == bundle_artifacts
    assert receipt["relationships"] == bundle["relationships"]
    assert receipt["registry"] == {
        "member_bioguide_id": bundle["publication_registry"][
            "member_bioguide_id"
        ],
        "issue_id": bundle["publication_registry"]["issue_id"],
        "artifact_id": 218,
        "publicly_active": True,
    }
    approval = bundle["publication_registry"]["publication_metadata"][
        "approval_receipt"
    ]
    assert receipt["subject"]["approval_receipt_id"] == approval["receipt_id"]
    assert receipt["subject"]["approval_subject_sha256"] == approval["binding"][
        "approval_subject_sha256"
    ]
    assert receipt["subject"]["presentation_content_sha256"] == approval[
        "binding"
    ]["presentation_content_sha256"]


def test_successful_receipt_is_historical_and_never_authorizes_mutation() -> None:
    receipt = _json(SUCCESS_RECEIPT_PATH)
    assert receipt["authorization"] == {
        "record_scope": "historical_record_only",
        "authorizes_activation": False,
        "authorizes_deactivation": False,
        "authorizes_deployment": False,
        "authorizes_rollback": False,
    }
    assert (
        receipt["rollback_readiness"]["requires_live_identity_verification"] is True
    )
    assert receipt["rollback_readiness"]["refuses_registry_or_graph_drift"] is True
    assert receipt["rollback_readiness"]["rollback_authorized"] is False


def test_current_state_records_active_publication_and_exact_scope_boundary() -> None:
    state = _json(REPOSITORY_ROOT / "docs/editorial/current_state_index.json")
    frontend = state["frontend"]
    assert frontend["f000477_justice_119_publication_state"] == (
        "human_approved_gold_production_eligible_publication_active"
    )
    assert frontend["f000477_justice_119_activation_bundle_state"] == (
        "applied_production_active"
    )
    assert frontend["f000477_justice_effective_tiers"] == {
        "119": "reviewed_conclusion",
        "all": "reviewed_conclusion",
        "118": "receipts_only",
    }
    assert frontend["f000477_justice_scope_all_boundary"] == "reviewed_119_record"
    assert state["publication_and_persistence_state"]["public_selection_count"] == 1
    assert state["production_publication_state"]["activation_rows_inserted"] == 7
    assert state["production_publication_state"]["rollback_status"] == "not_triggered"


def test_public_smoke_contract_pins_active_scopes_and_stable_identities() -> None:
    workflow = (
        REPOSITORY_ROOT / ".github/workflows/render-backend-smoke.yml"
    ).read_text(encoding="utf-8")
    for scope in ("scope=119", "scope=all", "scope=118"):
        assert scope in workflow
    assert '"119": "reviewed_conclusion"' in workflow
    assert '"all": "reviewed_conclusion"' in workflow
    assert '"118": "receipts_only"' in workflow
    assert "f000477:justice_public_safety:119:v1" in workflow
    assert (
        "approval-receipt:f000477-justice-public-safety-119-v1-20260727-dhart54"
        in workflow
    )
    assert "reviewed 119th-Congress record" in workflow
    assert "leg_alex_morgan" in workflow
    assert "ECONOMY_TAXES" in workflow
    for unstable_database_id in ("218", "219", "220"):
        assert unstable_database_id not in workflow


def test_incident_is_closed_without_rewriting_failed_attempt_history() -> None:
    incident = (
        REPOSITORY_ROOT
        / "docs/incidents/2026-07-28-foushee-justice-activation-http500.md"
    ).read_text(encoding="utf-8")
    assert "Status: resolved and closed; corrected publication active." in incident
    assert "batch 12, artifacts 215-217" in incident
    assert "HTTP 500 Internal Server Error" in incident
    assert "batch 13" in incident
    assert "without an HTTP 500" in incident
    assert "rollback was not triggered" in incident
    assert "no production log content was accessed" in incident


def test_historical_inactive_approval_boundary_remains_immutable() -> None:
    bundle = load_activation_bundle()
    approval = bundle["publication_registry"]["publication_metadata"][
        "approval_receipt"
    ]
    assert approval["publication_activation"] == {
        "active": False,
        "decision_scope": "out_of_scope",
    }
    assert bundle["bundle_sha256"] == (
        "df081ea7fc93039926b5a8ac1e468444f30e28b25bb2862bb2980f7d2d83e813"
    )
