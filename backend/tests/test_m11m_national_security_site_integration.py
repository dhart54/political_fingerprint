from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.editorial_presentations.integration_candidate import (
    BLOCKED_ACTION_ID,
    SiteIntegrationCandidateError,
    load_site_integration_candidate,
    select_site_integration_preview,
    validate_site_integration_candidate,
)
from app.main import app
from backend.scripts.build_m11m_national_security_site_integration import build


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = (
    ROOT / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_national_security_foreign_119_v1/site_integration_candidate.json"
)


def _candidate() -> dict:
    return load_site_integration_candidate(CANDIDATE)


def _national_security(payload: dict) -> dict:
    return next(
        row
        for row in payload["presentations"]
        if row["issue_id"] == "NATIONAL_SECURITY_FOREIGN"
    )


def test_m11m_regeneration_is_deterministic() -> None:
    result = build(check=True)
    assert result["candidate"]["candidate_subject_sha256"] == (
        "c0fa5282f061c4d27c259968dd08b5f7a804fdbe60c4b8794714e0c9ad04c5df"
    )
    assert result["review_packet"]["accounting"] == {
        "wording_items": 18,
        "mapped_unique_actions": 32,
        "mapped_unique_episodes": 32,
        "semantic_lineage_unique_actions": 32,
        "semantic_lineage_unique_episodes": 32,
        "accepted_interpreted_actions": 81,
        "accepted_episodes": 81,
        "blocked_actions": [BLOCKED_ACTION_ID],
    }


def test_candidate_has_exact_surface_and_ukraine_accounting() -> None:
    candidate = _candidate()
    subject = candidate["subject"]
    assert subject["surface_accounting"] == {
        "issue_overview": 1,
        "synthesis": 2,
        "repeated_pattern": 8,
        "trajectory": 1,
        "notable_choice": 6,
    }
    presentation = subject["presentation"]
    ukraine = next(
        row
        for row in presentation["repeated_patterns"]
        if row["wording_item_id"] == "wording:pattern:ukraine-assistance"
    )
    assert ukraine["primary_sentence"] == (
        "Opposed three proposals to restrict Ukraine aid and supported one "
        "measure authorizing support for Ukraine."
    )
    assert ukraine["evidence_count_label"] == "4 votes · 4 assistance choices"
    assert ukraine["direction"] is None
    assert ukraine["direction_symbol"] is None
    assert ukraine["show_direction"] is False
    assert ukraine["semantic_lineage_directions"] == ["mixed"]
    assert BLOCKED_ACTION_ID not in {
        action_id
        for field in (
            "syntheses",
            "repeated_patterns",
            "policy_trajectories",
            "notable_choices",
        )
        for row in presentation[field]
        for action_id in row["action_ids"]
    }


def test_war_powers_public_support_is_narrower_than_semantic_lineage() -> None:
    candidate = _candidate()
    presentation = candidate["subject"]["presentation"]
    war_powers = next(
        row
        for row in presentation["syntheses"]
        if row["wording_item_id"] == "wording:synthesis:war-powers"
    )
    country_patterns = {
        row["wording_item_id"]: set(row["public_supporting_action_ids"])
        for row in presentation["repeated_patterns"]
        if row["wording_item_id"]
        in {
            "wording:pattern:iran-war-powers",
            "wording:pattern:lebanon-war-powers",
            "wording:pattern:venezuela-war-powers",
        }
    }
    expected_country_actions = set().union(*country_patterns.values())
    assert war_powers["evidence_count_label"] == (
        "9 votes \u00b7 9 country-specific resolutions"
    )
    assert len(war_powers["semantic_lineage_action_ids"]) == 10
    assert len(war_powers["public_supporting_action_ids"]) == 9
    assert set(war_powers["action_ids"]) == expected_country_actions
    assert set(war_powers["public_supporting_action_ids"]) == expected_country_actions
    assert "house:119:1:244" in war_powers["semantic_lineage_action_ids"]
    assert "house:119:1:244" not in war_powers["public_supporting_action_ids"]

    aumf = next(
        row
        for row in presentation["notable_choices"]
        if row["wording_item_id"] == "wording:notable:aumf-repeal"
    )
    assert aumf["public_supporting_action_ids"] == ["house:119:1:244"]
    assert "house:119:1:244" in candidate["subject"]["preview_data"]["action_ids_119"]

    for row in [
        presentation["overview"],
        *presentation["syntheses"],
        *presentation["repeated_patterns"],
        *presentation["policy_trajectories"],
        *presentation["notable_choices"],
    ]:
        if row["wording_item_id"] != "wording:synthesis:war-powers":
            assert (
                row["public_supporting_action_ids"]
                == row["semantic_lineage_action_ids"]
            )


def test_preview_scope_is_bounded_and_other_scope_fails_closed() -> None:
    candidate = _candidate()
    kwargs = {
        "legislator_id": "leg_valerie_p_foushee",
        "member_bioguide_id": "F000477",
    }
    scoped = select_site_integration_preview(candidate, scope="119", **kwargs)
    assert _national_security(scoped)["tier"] == "reviewed_conclusion"
    all_scope = select_site_integration_preview(candidate, scope="all", **kwargs)
    assert (
        "bounded to the 119th-Congress record"
        in _national_security(all_scope)["scope_boundary"]
    )
    old_scope = select_site_integration_preview(candidate, scope="118", **kwargs)
    assert _national_security(old_scope)["tier"] == "receipts_only"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["subject"]["controls"].__setitem__(
                "publication_active", True
            ),
            "authority leaked",
        ),
        (
            lambda value: [
                value["subject"]["presentation"]["repeated_patterns"][0][field].append(
                    BLOCKED_ACTION_ID
                )
                for field in (
                    "action_ids",
                    "public_supporting_action_ids",
                    "semantic_lineage_action_ids",
                )
            ],
            "blocked action",
        ),
        (
            lambda value: value["subject"]["presentation"]["repeated_patterns"][0][
                "mapping"
            ].__setitem__("raw_yea_nay_maps_to_direction", True),
            "semantic mapping",
        ),
    ],
)
def test_adversarial_candidate_mutations_fail_closed(mutation, message: str) -> None:
    changed = copy.deepcopy(_candidate())
    mutation(changed)
    changed["candidate_subject_sha256"] = __import__(
        "app.editorial_presentations.compiler", fromlist=["canonical_digest"]
    ).canonical_digest(changed["subject"])
    with pytest.raises(SiteIntegrationCandidateError, match=message):
        validate_site_integration_candidate(changed)


def test_api_requires_server_opt_in_and_exact_preview_token(monkeypatch) -> None:
    profile = {"bioguide_id": "F000477"}
    with patch(
        "app.api.editorial_presentations.get_legislator_profile",
        return_value=profile,
    ):
        client = TestClient(app)
        default = client.get(
            "/legislators/leg_valerie_p_foushee/editorial-presentations",
            params={"scope": "119", "candidate": "m11m-national-security"},
        )
        assert default.status_code == 200
        assert _national_security(default.json())["tier"] == "receipts_only"

        monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
        preview = client.get(
            "/legislators/leg_valerie_p_foushee/editorial-presentations",
            params={"scope": "119", "candidate": "m11m-national-security"},
        )
        assert preview.status_code == 200
        assert _national_security(preview.json())["tier"] == "reviewed_conclusion"
        assert (
            _national_security(preview.json())["review_state"]["candidate_preview"]
            is True
        )

        invalid = client.get(
            "/legislators/leg_valerie_p_foushee/editorial-presentations",
            params={"scope": "119", "candidate": "anything-else"},
        )
        assert invalid.status_code == 422


def test_preview_positions_and_evidence_close_the_82_action_record(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
    client = TestClient(app)
    params = {"scope": "119", "candidate": "m11m-national-security"}
    positions = client.get(
        "/legislators/leg_valerie_p_foushee/positions", params=params
    )
    assert positions.status_code == 200
    national_security = next(
        row
        for row in positions.json()["positions"]
        if row["domain"] == "NATIONAL_SECURITY_FOREIGN"
    )
    assert national_security["total_votes"] == 82
    assert national_security["interpreted_total"] == 81

    evidence = client.get(
        "/legislators/leg_valerie_p_foushee/positions/"
        "NATIONAL_SECURITY_FOREIGN/evidence",
        params=params,
    )
    assert evidence.status_code == 200
    rows = evidence.json()["evidence"]
    assert len(rows) == 82
    assert len({row["canonical_action_id"] for row in rows}) == 82
    blocked = next(
        row for row in rows if row["canonical_action_id"] == BLOCKED_ACTION_ID
    )
    assert blocked["governed_receipt_projection"] is None
    assert blocked["governed_receipt_control"]["status"] == "noncounting_control"
    assert all(
        row["governed_receipt_projection"] is not None
        for row in rows
        if row["canonical_action_id"] != BLOCKED_ACTION_ID
    )


def test_candidate_json_is_parseable_and_contains_no_internal_ui_copy() -> None:
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    presentation_text = json.dumps(
        candidate["subject"]["presentation"], ensure_ascii=False
    )
    for forbidden in (
        "M11L",
        "semantic IR",
        "content_subject_sha256",
        "implementation_record_id",
        "candidate_state",
    ):
        assert forbidden not in presentation_text
