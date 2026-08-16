from __future__ import annotations

import copy
import io
import json

import pytest
from fastapi.testclient import TestClient

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.integration_candidate import (
    BLOCKED_ACTION_ID,
    select_site_integration_preview,
)
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_presentations.site_publication import (
    ACTIVATION_AUTHORITY_ID,
    ACTIVATION_AUTHORITY_SCHEMA_VERSION,
    ACTIVATION_REVIEWER_AUTHORITY,
    POSITIVE_AUTHORIZATIONS,
    eligible_site_integration_candidate,
    select_site_integration_public,
)
from app.main import app
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_national_security_publication_activation import (
    AUTHORITY_PATH,
    ACTIVATION_TEMPLATE_PATH,
    CURRENT_COUNTS,
    EXPECTED_AFTER_COUNTS,
    M11M_ARTIFACT_ID,
    M11M_PATH,
    PREFLIGHT_PATH,
    WRITE_SET_PATH,
    _state_fingerprint,
    activation_write_set_binding,
    build,
    build_activation_decision_template,
    build_authority,
    capture_runtime_health,
    main,
    publication_metadata_for_activation,
    reviewed_runtime_manifest,
    reviewed_runtime_manifest_for_preflight,
    validate_preflight,
    validate_runtime_health_proof,
    validate_write_set,
)


class _EmptyResult:
    def fetchall(self) -> list:
        return []


class _FingerprintConnection:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, query: str) -> _EmptyResult:
        self.queries.append(query)
        return _EmptyResult()


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _activation_authority(write_set: dict, *, synthetic: bool = False) -> dict:
    metadata = write_set["publication_registry"]["publication_metadata"]
    subject = {
        "decision": "approve_exact_publication_activation",
        "decision_recorded_at_utc": "2026-08-14T12:00:00Z",
        "reviewer": "synthetic-disposable-reviewer" if synthetic else "dhart54",
        "reviewer_authority": ACTIVATION_REVIEWER_AUTHORITY,
        "product_owner": "dhart54",
        "member_bioguide_id": "F000477",
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
        "congress": 119,
        "accepted_m11m_binding": write_set["accepted_m11m_binding"],
        "candidate_preparation_authority_binding": write_set["authority_binding"],
        "activation_write_set_binding": activation_write_set_binding(write_set),
        "publication_registry_target": {
            "member_bioguide_id": "F000477",
            "issue_id": "NATIONAL_SECURITY_FOREIGN",
            "presentation_natural_key": M11M_ARTIFACT_ID,
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
            "health_proof_subject_sha256": "a" * 64,
        },
        "production_target_identity_sha256": metadata[
            "production_target_identity_sha256"
        ],
        "authorizations": copy.deepcopy(POSITIVE_AUTHORIZATIONS),
    }
    return {
        "schema_version": ACTIVATION_AUTHORITY_SCHEMA_VERSION,
        "artifact_id": ACTIVATION_AUTHORITY_ID,
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "test_only_synthetic": synthetic,
        "subject": subject,
        "activation_authority_subject_sha256": semantic_hash(subject),
    }


def _row(
    write_set: dict,
    *,
    activation_authority: dict | None = None,
    allow_test_authority: bool = False,
) -> dict:
    presentation = next(
        item
        for item in write_set["artifacts"]
        if item["natural_key"] == M11M_ARTIFACT_ID
    )
    metadata = copy.deepcopy(write_set["publication_registry"]["publication_metadata"])
    if activation_authority is not None:
        metadata = publication_metadata_for_activation(
            write_set,
            _load(AUTHORITY_PATH),
            activation_authority,
            allow_test_authority=allow_test_authority,
        )
    return {
        "member_bioguide_id": "F000477",
        "issue_id": "NATIONAL_SECURITY_FOREIGN",
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "schema_version": presentation["schema_version"],
        "artifact_version": 1,
        "natural_key": M11M_ARTIFACT_ID,
        "content_sha256": presentation["content_sha256"],
        "payload_jsonb": presentation["payload"],
        "publication_metadata_jsonb": metadata,
    }


def test_m11n_regeneration_is_deterministic() -> None:
    result = build(check=True)
    assert result["authority"]["authority_subject_sha256"] == (
        "6c0038c80a9b4802dc6451f3efc2ce1d7ce5a4e1b139f24f6bef830dddcc6e6f"
    )
    assert (
        result["write_set"]["write_set_subject_sha256"]
        == (_load(WRITE_SET_PATH)["write_set_subject_sha256"])
    )
    assert result["activation_template"] == _load(ACTIVATION_TEMPLATE_PATH)


def test_authority_is_content_bound_and_non_activating() -> None:
    preflight = _load(PREFLIGHT_PATH)
    authority = build_authority(preflight)
    subject = authority["subject"]
    assert subject["accepted_m11m_binding"] == {
        "artifact_id": M11M_ARTIFACT_ID,
        "subject_sha256": (
            "c0fa5282f061c4d27c259968dd08b5f7a804fdbe60c4b8794714e0c9ad04c5df"
        ),
        "file_sha256": (
            "d2a7a65eb56f4be68b0d0477eeb8f75f793be5bbb458c86db13560b8eae35cc4"
        ),
        "content_sha256": semantic_hash(_load(M11M_PATH)),
    }
    assert subject["authorizations"]["record_production_eligibility"] is True
    assert subject["authorizations"]["build_publication_activation_candidate"] is True
    assert all(
        subject["authorizations"][key] is False
        for key in (
            "production_database_write",
            "publication_registry_mutation",
            "publication_activation",
            "deployment",
        )
    )


def test_activation_decision_template_is_unsealed_and_non_authorizing() -> None:
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    template = build_activation_decision_template(write_set, authority)
    assert template == _load(ACTIVATION_TEMPLATE_PATH)
    assert template["sealed"] is False
    assert template["accepted"] is False
    completion = template["subject"][
        "completion_required_after_live_runtime_deployment"
    ]
    assert completion["decision"] is None
    assert all(value is None for value in completion["authorizations"].values())
    assert template["subject"]["fixed_bindings"][
        "activation_write_set_binding"
    ] == activation_write_set_binding(write_set)


def test_live_runtime_proof_uses_health_response_not_expected_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deployed_commit = "1" * 40
    payload = io.BytesIO(json.dumps({"commit_sha": deployed_commit}).encode())
    monkeypatch.setattr(
        "scripts.foushee_national_security_publication_activation.urlopen",
        lambda endpoint, timeout: payload,
    )
    proof = capture_runtime_health("https://production.example.test")
    assert proof["health_endpoint"] == "https://production.example.test/health"
    assert proof["deployed_commit"] == deployed_commit
    assert proof["health_commit"] == deployed_commit
    validate_runtime_health_proof(proof, require_fresh=True)
    validate_runtime_health_proof(
        proof, require_fresh=True, require_current_runtime=True
    )


def test_unbound_disposable_preflight_uses_current_runtime_manifest() -> None:
    assert reviewed_runtime_manifest_for_preflight({}) == reviewed_runtime_manifest()


def test_write_set_is_exact_additive_graph_and_preserves_m11m() -> None:
    authority = _load(AUTHORITY_PATH)
    write_set = _load(WRITE_SET_PATH)
    validate_write_set(write_set, authority=authority)
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
    }
    presentation = next(
        item
        for item in write_set["artifacts"]
        if item["natural_key"] == M11M_ARTIFACT_ID
    )
    assert presentation["payload"] == _load(M11M_PATH)
    assert write_set["activation_authorized"] is False
    assert write_set["production_write_authorized"] is False


def test_hr8800_remains_blocked_and_outside_every_public_finding() -> None:
    candidate = _load(M11M_PATH)
    presentation = candidate["subject"]["presentation"]
    action_ids = {
        action_id
        for field in (
            "syntheses",
            "repeated_patterns",
            "policy_trajectories",
            "notable_choices",
        )
        for item in presentation[field]
        for action_id in item["action_ids"]
    }
    assert BLOCKED_ACTION_ID not in action_ids
    assert presentation["noncounting_controls"] == [
        {
            "canonical_action_id": BLOCKED_ACTION_ID,
            "boundary_type": "source_blocked_uninterpreted",
            "detail": "No public analytical meaning is available for this action.",
        }
    ]


def test_preparation_authority_alone_cannot_publish() -> None:
    write_set = _load(WRITE_SET_PATH)
    row = _row(write_set)
    assert (
        eligible_site_integration_candidate(row, member_bioguide_id="F000477") is None
    )
    selected = select_public_presentations(
        [row],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    national_security = next(
        item
        for item in selected["presentations"]
        if item["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
    )
    assert national_security["tier"] == "receipts_only"


def test_exact_positive_authority_projects_normalized_public_presentation() -> None:
    write_set = _load(WRITE_SET_PATH)
    activation = _activation_authority(write_set)
    row = _row(write_set, activation_authority=activation)
    candidate = eligible_site_integration_candidate(row, member_bioguide_id="F000477")
    assert candidate == _load(M11M_PATH)

    for scope in ("119", "all", "118"):
        selected = select_public_presentations(
            [row],
            legislator_id="leg_valerie_p_foushee",
            member_bioguide_id="F000477",
            scope=scope,
        )
        national_security = next(
            item
            for item in selected["presentations"]
            if item["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
        )
        assert national_security["tier"] == (
            "reviewed_conclusion" if scope in {"119", "all"} else "receipts_only"
        )
    selected_119 = select_public_presentations(
        [row],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    actual = next(
        item
        for item in selected_119["presentations"]
        if item["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
    )
    assert actual["public_status_label"] == "Full issue interpretation available"
    assert "candidate_preview" not in actual["review_state"]
    assert actual["overview"] == _load(M11M_PATH)["subject"]["presentation"]["overview"]


def test_preview_projection_retains_preview_state_but_public_projection_does_not() -> (
    None
):
    candidate = _load(M11M_PATH)
    preview = select_site_integration_preview(
        candidate,
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    public = select_site_integration_public(
        candidate,
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    presentation = next(
        item
        for item in public["presentations"]
        if item["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
    )
    preview_presentation = next(
        item
        for item in preview["presentations"]
        if item["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
    )
    assert preview_presentation["review_state"]["candidate_preview"] is True
    assert preview_presentation["public_status_label"] == "Issue summary candidate"
    assert presentation["public_status_label"] == "Full issue interpretation available"
    assert "candidate_preview" not in presentation["review_state"]
    assert "Issue summary candidate" not in json.dumps(public)


def test_published_api_normalizes_operational_preview_metadata(monkeypatch) -> None:
    write_set = _load(WRITE_SET_PATH)
    row = _row(write_set, activation_authority=_activation_authority(write_set))
    monkeypatch.setattr(
        "app.api.editorial_presentations._load_publication_rows", lambda: [row]
    )
    monkeypatch.setattr(
        "app.api.editorial_presentations.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    response = TestClient(app).get(
        "/legislators/leg_valerie_p_foushee/editorial-presentations",
        params={"scope": "119"},
    )
    assert response.status_code == 200
    presentation = next(
        item
        for item in response.json()["presentations"]
        if item["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
    )
    assert presentation["public_status_label"] == "Full issue interpretation available"
    assert "candidate_preview" not in presentation["review_state"]
    assert "Issue summary candidate" not in response.text


def test_active_publication_projects_complete_positions_and_blocked_control(
    monkeypatch,
) -> None:
    candidate = _load(M11M_PATH)
    evidence = candidate["subject"]["preview_data"]["evidence_119"]
    write_set = _load(WRITE_SET_PATH)
    row = _row(write_set, activation_authority=_activation_authority(write_set))
    monkeypatch.setattr("app.api.positions._load_publication_rows", lambda: [row])
    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_response",
        lambda **_kwargs: {
            "legislator_id": "leg_valerie_p_foushee",
            "scope": "119",
            "positions": [],
        },
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_evidence_response",
        lambda **kwargs: {
            "legislator_id": "leg_valerie_p_foushee",
            "domain": kwargs["domain"],
            "evidence": evidence,
        },
    )
    monkeypatch.setattr(
        "app.api.positions._has_governed_presentation_candidate",
        lambda **_kwargs: False,
    )
    client = TestClient(app)
    positions = client.get(
        "/legislators/leg_valerie_p_foushee/positions", params={"scope": "119"}
    )
    assert positions.status_code == 200
    summary = next(
        item
        for item in positions.json()["positions"]
        if item["domain"] == "NATIONAL_SECURITY_FOREIGN"
    )
    assert summary["total_votes"] == 82
    assert summary["interpreted_total"] == 81

    response = client.get(
        "/legislators/leg_valerie_p_foushee/positions/"
        "NATIONAL_SECURITY_FOREIGN/evidence",
        params={"scope": "119"},
    )
    assert response.status_code == 200
    rows = response.json()["evidence"]
    assert len(rows) == 82
    blocked = next(
        item for item in rows if item["canonical_action_id"] == BLOCKED_ACTION_ID
    )
    assert blocked["governed_receipt_projection"] is None
    assert blocked["governed_receipt_control"]["status"] == "noncounting_control"


@pytest.mark.parametrize(
    ("name", "mutate", "reseal"),
    [
        ("inactive", lambda row: row.__setitem__("publicly_active", False), False),
        (
            "wrong-row-member",
            lambda row: row.__setitem__("member_bioguide_id", "X"),
            False,
        ),
        (
            "wrong-issue",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"].__setitem__("issue_id", "JUSTICE_PUBLIC_SAFETY"),
            True,
        ),
        (
            "wrong-authority-member",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"].__setitem__("member_bioguide_id", "X"),
            True,
        ),
        (
            "wrong-congress",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"].__setitem__("congress", 118),
            True,
        ),
        (
            "wrong-m11m",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"]["accepted_m11m_binding"].__setitem__(
                "content_sha256", "0" * 64
            ),
            True,
        ),
        (
            "wrong-write-set",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"]["activation_write_set_binding"].__setitem__(
                "write_set_subject_sha256", "0" * 64
            ),
            True,
        ),
        (
            "wrong-preflight",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"]["preflight_binding"].__setitem__(
                "state_fingerprint_sha256", "0" * 64
            ),
            True,
        ),
        (
            "wrong-rollback",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"]["rollback_binding"].__setitem__(
                "delete_relationship_count", 1
            ),
            True,
        ),
        (
            "missing-decision-timestamp",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"].__setitem__("decision_recorded_at_utc", ""),
            True,
        ),
        (
            "wrong-runtime",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"]["runtime_binding"].__setitem__("health_commit", "0" * 40),
            True,
        ),
        (
            "wrong-production-target",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"].__setitem__("production_target_identity_sha256", "0" * 64),
            True,
        ),
        (
            "missing-reviewed-runtime-binding",
            lambda row: row["publication_metadata_jsonb"].pop(
                "reviewed_runtime_binding"
            ),
            False,
        ),
        (
            "wrong-reviewer-authority",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ]["subject"].__setitem__("reviewer_authority", "self_authorized"),
            True,
        ),
        (
            "unsealed",
            lambda row: row["publication_metadata_jsonb"][
                "publication_activation_authority"
            ].__setitem__("sealed", False),
            False,
        ),
    ],
)
def test_selector_adversarial_activation_authorities_fail_closed(
    name, mutate, reseal
) -> None:
    write_set = _load(WRITE_SET_PATH)
    row = _row(write_set, activation_authority=_activation_authority(write_set))
    mutate(row)
    if reseal:
        activation = row["publication_metadata_jsonb"][
            "publication_activation_authority"
        ]
        activation["activation_authority_subject_sha256"] = semantic_hash(
            activation["subject"]
        )
        row["publication_metadata_jsonb"]["activation_authority_subject_sha256"] = (
            activation["activation_authority_subject_sha256"]
        )
    assert (
        eligible_site_integration_candidate(row, member_bioguide_id="F000477") is None
    ), name


def test_missing_positive_activation_authority_fails_closed() -> None:
    row = _row(_load(WRITE_SET_PATH))
    row["publication_metadata_jsonb"].pop("publication_activation_authority", None)
    assert (
        eligible_site_integration_candidate(row, member_bioguide_id="F000477") is None
    )


def test_synthetic_authority_requires_explicit_test_gate() -> None:
    write_set = _load(WRITE_SET_PATH)
    synthetic = _activation_authority(write_set, synthetic=True)
    row = _row(
        write_set,
        activation_authority=synthetic,
        allow_test_authority=True,
    )
    assert (
        eligible_site_integration_candidate(row, member_bioguide_id="F000477") is None
    )
    assert eligible_site_integration_candidate(
        row,
        member_bioguide_id="F000477",
        allow_test_authority=True,
    ) == _load(M11M_PATH)


def test_preflight_and_write_set_drift_fail_closed() -> None:
    preflight = _load(PREFLIGHT_PATH)
    changed = copy.deepcopy(preflight)
    changed["counts"]["artifacts"] += 1
    with pytest.raises(StoreSafetyError, match="preflight digest mismatch"):
        validate_preflight(changed)
    write_set = _load(WRITE_SET_PATH)
    write_set["write_caps"]["registry_updates"] = 1
    with pytest.raises(StoreSafetyError, match="write-set digest mismatch"):
        validate_write_set(write_set, authority=_load(AUTHORITY_PATH))


def test_fingerprint_query_qualifies_registry_columns() -> None:
    conn = _FingerprintConnection()
    _state_fingerprint(conn)
    registry_query = next(
        query
        for query in conn.queries
        if "FROM editorial_publication_registry" in query
    )
    assert "registry.member_bioguide_id" in registry_query
    assert "registry.issue_id" in registry_query


@pytest.mark.parametrize("mode", ["dry-run", "apply", "postcheck", "rollback"])
def test_production_mutation_modes_fail_before_database_access(mode: str) -> None:
    with pytest.raises(StoreSafetyError, match="positive activation authority"):
        main([mode, "--target", "production"])
