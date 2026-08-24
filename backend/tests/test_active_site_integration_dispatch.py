from __future__ import annotations

import copy
import json

import pytest
from fastapi.testclient import TestClient

from app.api.editorial_presentations import M11M_CANDIDATE_PATH, M12M_CANDIDATE_PATH
from app.api.positions import _merge_site_integration_evidence
from app.editorial_presentations.environment_integration_candidate import (
    merge_environment_preview_evidence,
)
from app.editorial_presentations.integration_candidate import (
    governed_position_summary,
    merge_site_integration_preview_evidence,
)
from app.main import app


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _base_evidence(domain: str, scope: str) -> dict:
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
    rows = [prior] if scope == "118" else [current]
    if scope == "all":
        rows = [current, prior]
    return {"domain": domain, "evidence": rows}


def _publication_db_unavailable():
    raise RuntimeError("publication DB unavailable")


def test_active_candidate_dispatch_is_identity_aware_and_fail_closed() -> None:
    national_security = _load(M11M_CANDIDATE_PATH)
    environment = _load(M12M_CANDIDATE_PATH)

    with pytest.raises(ValueError, match="M11M candidate identity differs"):
        merge_site_integration_preview_evidence(
            {}, environment, domain="NATIONAL_SECURITY_FOREIGN", scope="119"
        )
    with pytest.raises(ValueError, match="M12M identity differs"):
        merge_environment_preview_evidence(
            {}, national_security, domain="ENVIRONMENT_ENERGY", scope="119"
        )
    with pytest.raises(
        ValueError, match="unknown active site-integration candidate identity"
    ):
        _merge_site_integration_evidence(
            {}, {"artifact_id": "unknown"}, domain="ENVIRONMENT_ENERGY", scope="119"
        )


def test_simultaneously_active_candidates_enrich_independently(monkeypatch) -> None:
    candidates = {
        "NATIONAL_SECURITY_FOREIGN": _load(M11M_CANDIDATE_PATH),
        "ENVIRONMENT_ENERGY": _load(M12M_CANDIDATE_PATH),
    }
    evidence = {
        issue_id: candidate["subject"]["preview_data"]["evidence_119"]
        for issue_id, candidate in candidates.items()
    }
    justice = {
        "domain": "JUSTICE_PUBLIC_SAFETY",
        "yea_count": 7,
        "nay_count": 3,
    }

    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr("app.api.positions._load_publication_rows", lambda: [])
    monkeypatch.setattr(
        "app.api.positions._active_site_integration_publication",
        lambda **kwargs: candidates.get(kwargs["issue_id"]),
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_response",
        lambda **kwargs: {
            "legislator_id": kwargs["legislator_id"],
            "scope": kwargs["scope"],
            "positions": [
                copy.deepcopy(justice),
                {"domain": "NATIONAL_SECURITY_FOREIGN", "total_votes": 0},
                {"domain": "ENVIRONMENT_ENERGY", "total_votes": 0},
            ],
        },
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_evidence_response",
        lambda **kwargs: {
            "domain": kwargs["domain"],
            "evidence": copy.deepcopy(evidence[kwargs["domain"]]),
        },
    )

    response = TestClient(app).get(
        "/legislators/leg_valerie_p_foushee/positions", params={"scope": "119"}
    )
    assert response.status_code == 200
    rows = {row["domain"]: row for row in response.json()["positions"]}
    assert rows["JUSTICE_PUBLIC_SAFETY"] == justice
    assert rows["ENVIRONMENT_ENERGY"] == {
        "domain": "ENVIRONMENT_ENERGY",
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
    assert rows["NATIONAL_SECURITY_FOREIGN"] == governed_position_summary(
        evidence["NATIONAL_SECURITY_FOREIGN"],
        domain="NATIONAL_SECURITY_FOREIGN",
    )


@pytest.mark.parametrize("scope", ["119", "all"])
@pytest.mark.parametrize(
    ("preview_token", "preview_issue", "expected_summary"),
    [
        (
            "m11m-national-security",
            "NATIONAL_SECURITY_FOREIGN",
            {
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
            },
        ),
        (
            "m12m-environment-energy",
            "ENVIRONMENT_ENERGY",
            {
                "domain": "ENVIRONMENT_ENERGY",
                "yea_count": 15,
                "nay_count": 47,
                "other_count": 1,
                "total_votes": 63,
                "recorded_votes": 62,
                "interpreted_support_count": 15,
                "interpreted_oppose_count": 47,
                "interpreted_other_count": 1,
                "interpreted_total": 63,
            },
        ),
    ],
)
def test_explicit_preview_survives_publication_database_failure(
    monkeypatch,
    scope: str,
    preview_token: str,
    preview_issue: str,
    expected_summary: dict,
) -> None:
    candidates = {
        "NATIONAL_SECURITY_FOREIGN": _load(M11M_CANDIDATE_PATH),
        "ENVIRONMENT_ENERGY": _load(M12M_CANDIDATE_PATH),
    }
    base_rows = [
        {"domain": "JUSTICE_PUBLIC_SAFETY", "total_votes": 10},
        {"domain": "NATIONAL_SECURITY_FOREIGN", "total_votes": 20},
        {"domain": "ENVIRONMENT_ENERGY", "total_votes": 30},
    ]
    monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_response",
        lambda **kwargs: {
            "legislator_id": kwargs["legislator_id"],
            "scope": kwargs["scope"],
            "positions": copy.deepcopy(base_rows),
        },
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_evidence_response",
        lambda **kwargs: {
            "domain": kwargs["domain"],
            "evidence": copy.deepcopy(
                candidates[kwargs["domain"]]["subject"]["preview_data"]["evidence_119"]
            ),
        },
    )
    monkeypatch.setattr(
        "app.api.positions._load_publication_rows",
        _publication_db_unavailable,
    )

    response = TestClient(app).get(
        "/legislators/leg_valerie_p_foushee/positions",
        params={"scope": scope, "candidate": preview_token},
    )
    assert response.status_code == 200
    rows = {row["domain"]: row for row in response.json()["positions"]}
    assert rows[preview_issue] == expected_summary
    assert rows["JUSTICE_PUBLIC_SAFETY"] == base_rows[0]
    unrequested_issue = (
        "ENVIRONMENT_ENERGY"
        if preview_issue == "NATIONAL_SECURITY_FOREIGN"
        else "NATIONAL_SECURITY_FOREIGN"
    )
    assert rows[unrequested_issue] == next(
        row for row in base_rows if row["domain"] == unrequested_issue
    )


def test_publication_database_failure_without_preview_returns_base_positions(
    monkeypatch,
) -> None:
    base_response = {
        "legislator_id": "leg_valerie_p_foushee",
        "scope": "119",
        "positions": [{"domain": "JUSTICE_PUBLIC_SAFETY", "total_votes": 10}],
    }
    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_response",
        lambda **_kwargs: copy.deepcopy(base_response),
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_evidence_response",
        lambda **_kwargs: pytest.fail("inactive candidates must not request evidence"),
    )
    monkeypatch.setattr(
        "app.api.positions._load_publication_rows",
        _publication_db_unavailable,
    )

    response = TestClient(app).get(
        "/legislators/leg_valerie_p_foushee/positions", params={"scope": "119"}
    )
    assert response.status_code == 200
    assert response.json() == base_response


@pytest.mark.parametrize(
    ("scope", "expected_count", "expected_119"),
    [("119", 63, 63), ("all", 64, 63), ("118", 1, 0)],
)
def test_active_environment_evidence_route_uses_governed_candidate_ledger(
    monkeypatch, scope: str, expected_count: int, expected_119: int
) -> None:
    environment = _load(M12M_CANDIDATE_PATH)
    monkeypatch.setattr(
        "app.api.positions.get_legislator_profile",
        lambda **_kwargs: {"bioguide_id": "F000477"},
    )
    monkeypatch.setattr(
        "app.api.positions.get_position_evidence_response",
        lambda **kwargs: _base_evidence(kwargs["domain"], kwargs["scope"]),
    )
    monkeypatch.setattr(
        "app.api.positions._active_site_integration_publication",
        lambda **kwargs: (
            environment if kwargs["issue_id"] == "ENVIRONMENT_ENERGY" else None
        ),
    )
    monkeypatch.setattr(
        "app.api.positions._has_governed_presentation_candidate",
        lambda **_kwargs: False,
    )

    response = TestClient(app).get(
        "/legislators/leg_valerie_p_foushee/positions/ENVIRONMENT_ENERGY/evidence",
        params={"scope": scope},
    )
    assert response.status_code == 200
    rows = response.json()["evidence"]
    assert len(rows) == expected_count
    governed_119 = [row for row in rows if int(row.get("congress", 0) or 0) == 119]
    assert len(governed_119) == expected_119
    assert len({row["canonical_action_id"] for row in governed_119}) == expected_119
    if scope in {"119", "all"}:
        assert all(row.get("governed_receipt_projection") for row in governed_119)
        hr_6387 = next(
            row
            for row in governed_119
            if row["canonical_action_id"] == "house:119:2:136"
        )
        assert (
            hr_6387["governed_receipt_projection"]["exact_choice_position_effect"]
            == "non_directional_not_voting"
        )


def test_environment_supporting_navigation_sets_remain_exact() -> None:
    candidate = _load(M12M_CANDIDATE_PATH)
    presentation = candidate["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["syntheses"],
        *presentation["repeated_patterns"],
    ]
    by_title = {item["title"]: item for item in items}
    assert len(by_title["Environment & Energy"]["public_supporting_action_ids"]) == 13
    assert (
        len(
            by_title["Congressional efforts to overturn agency decisions"][
                "public_supporting_action_ids"
            ]
        )
        == 13
    )
    assert (
        len(
            by_title["California vehicle-emissions waivers"][
                "public_supporting_action_ids"
            ]
        )
        == 2
    )
    assert (
        len(
            by_title["Appliance and commercial-equipment rules"][
                "public_supporting_action_ids"
            ]
        )
        == 4
    )
    assert (
        len(
            by_title["Bureau of Land Management decisions"][
                "public_supporting_action_ids"
            ]
        )
        == 7
    )
    assert all(item["show_direction"] is False for item in items)
    assert "house:119:2:136" not in {
        action_id
        for item in items
        for action_id in item["public_supporting_action_ids"]
    }
