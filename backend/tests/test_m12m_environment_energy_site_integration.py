import copy
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.environment_integration_candidate import (
    EnvironmentSiteIntegrationCandidateError,
    select_environment_site_integration_preview,
    validate_environment_site_integration_candidate,
)
from app.main import app
from backend.scripts.build_m12m_environment_energy_site_integration import build


def candidate():
    return build(check=True)["candidate"]


def environment(payload):
    return next(
        row
        for row in payload["presentations"]
        if row["issue_id"] == "ENVIRONMENT_ENERGY"
    )


def test_m12m_exact_surfaces_lineage_and_no_direction() -> None:
    value = candidate()
    presentation = value["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["syntheses"],
        *presentation["repeated_patterns"],
    ]
    assert len(items) == 5
    assert (
        len(presentation["syntheses"]) == 1
        and len(presentation["repeated_patterns"]) == 3
    )
    assert presentation["policy_trajectories"] == presentation["notable_choices"] == []
    assert all(
        not item["show_direction"]
        and item["direction_label"] is None
        and item["direction_symbol"] is None
        for item in items
    )
    counts = {
        item["wording_item_id"]: len(item["public_supporting_action_ids"])
        for item in items
    }
    assert counts["wording:synthesis:congressional-disapproval"] == 13
    assert counts["wording:pattern:california-emissions-waivers"] == 2
    assert counts["wording:pattern:doe-appliance-equipment-rules"] == 4
    assert counts["wording:pattern:blm-land-decisions"] == 7
    assert "house:119:2:136" not in {
        action for item in items for action in item["semantic_lineage_action_ids"]
    }


def test_m12m_scopes_fail_closed() -> None:
    kwargs = {"legislator_id": "leg_valerie_p_foushee", "member_bioguide_id": "F000477"}
    assert (
        environment(
            select_environment_site_integration_preview(
                candidate(), scope="119", **kwargs
            )
        )["tier"]
        == "reviewed_conclusion"
    )
    assert (
        environment(
            select_environment_site_integration_preview(
                candidate(), scope="all", **kwargs
            )
        )["tier"]
        == "reviewed_conclusion"
    )
    assert (
        environment(
            select_environment_site_integration_preview(
                candidate(), scope="118", **kwargs
            )
        )["tier"]
        == "receipts_only"
    )


def test_m12m_direction_attack_fails_even_when_resealed() -> None:
    changed = copy.deepcopy(candidate())
    changed["subject"]["presentation"]["syntheses"][0]["show_direction"] = True
    changed["candidate_subject_sha256"] = canonical_digest(changed["subject"])
    with pytest.raises(EnvironmentSiteIntegrationCandidateError):
        validate_environment_site_integration_candidate(changed)


def test_m12m_api_requires_server_opt_in_and_exact_token(monkeypatch) -> None:
    with (
        patch(
            "app.api.editorial_presentations.get_legislator_profile",
            return_value={"bioguide_id": "F000477"},
        ),
        patch(
            "app.api.editorial_presentations._load_publication_rows", return_value=[]
        ),
    ):
        client = TestClient(app)
        params = {"scope": "119", "candidate": "m12m-environment-energy"}
        assert (
            environment(
                client.get(
                    "/legislators/leg_valerie_p_foushee/editorial-presentations",
                    params=params,
                ).json()
            )["tier"]
            == "receipts_only"
        )
        monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
        assert (
            environment(
                client.get(
                    "/legislators/leg_valerie_p_foushee/editorial-presentations",
                    params=params,
                ).json()
            )["tier"]
            == "reviewed_conclusion"
        )
        assert (
            client.get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "119", "candidate": "wrong"},
            ).status_code
            == 422
        )


def test_m12m_positions_and_evidence_use_all_63_governed_rows(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
    evidence = candidate()["subject"]["preview_data"]["evidence_119"]
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
        lambda **kwargs: {"domain": kwargs["domain"], "evidence": evidence},
    )
    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr("app.api.positions._load_publication_rows", lambda: [])
    client = TestClient(app)
    params = {"scope": "119", "candidate": "m12m-environment-energy"}
    positions = client.get(
        "/legislators/leg_valerie_p_foushee/positions", params=params
    )
    row = next(
        item
        for item in positions.json()["positions"]
        if item["domain"] == "ENVIRONMENT_ENERGY"
    )
    assert row["total_votes"] == row["interpreted_total"] == 63
    receipts = client.get(
        "/legislators/leg_valerie_p_foushee/positions/ENVIRONMENT_ENERGY/evidence",
        params=params,
    )
    assert len(receipts.json()["evidence"]) == 63
