from __future__ import annotations

import copy
import json

import pytest
from fastapi.testclient import TestClient

from app.editorial_artifacts.bundle import semantic_hash
from app.editorial_presentations.integration_candidate import BLOCKED_ACTION_ID
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_presentations.site_publication import (
    eligible_site_integration_candidate,
)
from app.main import app
from scripts.editorial_artifact_store import StoreSafetyError
from scripts.foushee_national_security_publication_activation import (
    AUTHORITY_PATH,
    CURRENT_COUNTS,
    EXPECTED_AFTER_COUNTS,
    M11M_ARTIFACT_ID,
    M11M_PATH,
    PREFLIGHT_PATH,
    WRITE_SET_PATH,
    _state_fingerprint,
    build,
    build_authority,
    main,
    validate_preflight,
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


def _row(write_set: dict) -> dict:
    presentation = next(
        item
        for item in write_set["artifacts"]
        if item["natural_key"] == M11M_ARTIFACT_ID
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
        "publication_metadata_jsonb": write_set["publication_registry"][
            "publication_metadata"
        ],
    }


def test_m11n_regeneration_is_deterministic() -> None:
    result = build(check=True)
    assert result["authority"]["authority_subject_sha256"] == (
        "2c784f3771ccbe8edc71d3799438a5ea2cd5ec54b3334321a2782fb0e2873f8b"
    )
    assert result["write_set"]["write_set_subject_sha256"] == (
        "e81343483d38598b27f90bd0ee91f389d7dbdea23d411900ec795b34337c03b7"
    )


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


def test_selector_is_fail_closed_then_projects_exact_accepted_presentation() -> None:
    write_set = _load(WRITE_SET_PATH)
    row = _row(write_set)
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
    expected = copy.deepcopy(_load(M11M_PATH)["subject"]["presentation"])
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
    assert actual == expected


def test_active_publication_projects_complete_positions_and_blocked_control(
    monkeypatch,
) -> None:
    candidate = _load(M11M_PATH)
    evidence = candidate["subject"]["preview_data"]["evidence_119"]
    row = _row(_load(WRITE_SET_PATH))
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
    "mutate",
    [
        lambda row: row.__setitem__("production_eligible", False),
        lambda row: row.__setitem__("benchmark_status", "not_promoted"),
        lambda row: row.__setitem__("content_sha256", "0" * 64),
        lambda row: row["publication_metadata_jsonb"].__setitem__(
            "accepted_m11m_subject_sha256", "0" * 64
        ),
        lambda row: row["publication_metadata_jsonb"][
            "production_eligibility_publication_authority"
        ]["subject"]["authorizations"].__setitem__("publication_activation", True),
    ],
)
def test_selector_adversarial_mutations_fail_closed(mutate) -> None:
    row = copy.deepcopy(_row(_load(WRITE_SET_PATH)))
    mutate(row)
    assert (
        eligible_site_integration_candidate(row, member_bioguide_id="F000477") is None
    )


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


@pytest.mark.parametrize("mode", ["dry-run", "apply", "rollback"])
def test_production_mutation_modes_fail_before_database_access(mode: str) -> None:
    with pytest.raises(StoreSafetyError, match="does not authorize"):
        main([mode, "--target", "production"])
