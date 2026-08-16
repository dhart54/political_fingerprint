from __future__ import annotations

import json

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.environment_integration_candidate import (
    M12M_ARTIFACT_ID,
)
from app.editorial_presentations.site_publication import (
    validate_environment_candidate_preparation_authority,
)
from scripts.foushee_environment_energy_publication_preparation import (
    ACTIVATION_TEMPLATE_PATH,
    AUTHORITY_PATH,
    CURRENT_COUNTS,
    EXPECTED_AFTER_COUNTS,
    NON_DIRECTIONAL_ACTION_ID,
    PARITY_PATH,
    PREFLIGHT_PATH,
    WRITE_SET_PATH,
    build,
    reviewed_runtime_manifest,
    validate_preflight,
    validate_write_set,
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_m12n_governed_package_is_deterministic_and_non_authorizing() -> None:
    result = build(check=True)
    authority = result["authority"]
    write_set = result["write_set"]
    template = _load(ACTIVATION_TEMPLATE_PATH)
    validate_preflight(_load(PREFLIGHT_PATH), require_current_runtime=True)
    validate_write_set(write_set, authority=authority)
    validate_environment_candidate_preparation_authority(
        authority,
        candidate=next(
            row["payload"]
            for row in write_set["artifacts"]
            if row["natural_key"] == M12M_ARTIFACT_ID
        ),
    )
    assert write_set["expected_counts"] == {
        "before": CURRENT_COUNTS,
        "after": EXPECTED_AFTER_COUNTS,
    }
    assert write_set["write_caps"] == {
        "batch_inserts": 1,
        "artifact_inserts": 3,
        "relationship_inserts": 2,
        "registry_inserts": 1,
        "registry_updates": 0,
        "deletes_during_activation": 0,
        "justice_rows_touched": 0,
        "national_security_rows_touched": 0,
    }
    assert write_set["activation_authorized"] is False
    assert write_set["production_write_authorized"] is False
    assert template["sealed"] is False and template["accepted"] is False
    assert all(
        value is None
        for value in template["subject"][
            "completion_required_after_live_runtime_deployment"
        ]["authorizations"].values()
    )
    assert result["parity"] == _load(PARITY_PATH)


def test_m12n_exact_environment_accounting_and_isolation() -> None:
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    by_key = {row["natural_key"]: row for row in write_set["artifacts"]}
    presentation = by_key[M12M_ARTIFACT_ID]["payload"]
    validation = next(
        row["payload"]
        for row in write_set["artifacts"]
        if row["artifact_type"] == "standardization_validation_result"
    )
    assert presentation["candidate_subject_sha256"] == (
        "d4c64fb13a356fe80e13cfad529b1d8c5b79858e23542291185fe2bbc98183f3"
    )
    assert semantic_hash(presentation) == by_key[M12M_ARTIFACT_ID]["content_sha256"]
    assert validation["approved_universe_actions"] == 63
    assert validation["accepted_interpreted_actions"] == 63
    assert validation["unused_non_directional_actions"] == [NON_DIRECTIONAL_ACTION_ID]
    assert (
        write_set["rollback"]["justice_registry_row_unchanged"]["content_sha256"]
        == "1c088fc4a98e8442263899faffd7e203967cf60c387944884e4ce755d6ba7943"
    )
    assert (
        write_set["rollback"]["national_security_registry_row_unchanged"][
            "content_sha256"
        ]
        == "05661086601991075f04195090a41e0febaad7f8e6acda53f0cab838f97e860c"
    )
    assert (
        authority["subject"]["accepted_site_integration_binding"]["file_sha256"]
        == "1d040db73b2d223942f8226764dbd0906cb56cfa83108cd4993c234a1df803c5"
    )


def test_current_runtime_manifest_is_not_historical_m11n_snapshot() -> None:
    manifest = reviewed_runtime_manifest()
    assert manifest["schema_version"] == "m12n_reviewed_runtime_manifest_v1"
    assert any(
        row["path"].endswith("foushee_environment_energy_publication_preparation.py")
        for row in manifest["files"]
    )
