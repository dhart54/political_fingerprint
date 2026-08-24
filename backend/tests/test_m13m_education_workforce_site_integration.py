import copy
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.education_workforce_integration_candidate import (
    EducationWorkforceSiteIntegrationCandidateError,
    select_education_workforce_site_integration_preview,
    validate_education_workforce_site_integration_candidate,
)
from app.main import app
from backend.scripts.build_m13m_education_workforce_site_integration import build


def candidate():
    return build(check=True)["candidate"]


def education(payload):
    return next(
        row
        for row in payload["presentations"]
        if row["issue_id"] == "EDUCATION_WORKFORCE"
    )


def test_m13m_exact_surfaces_lineage_and_mixed_only_on_notable() -> None:
    value = candidate()
    presentation = value["subject"]["presentation"]
    items = [
        presentation["overview"],
        *presentation["repeated_patterns"],
        *presentation["notable_choices"],
    ]
    assert len(items) == 3
    assert presentation["syntheses"] == presentation["policy_trajectories"] == []
    assert [item["direction_label"] for item in items] == [None, None, "Mixed"]
    assert len(value["subject"]["semantic_lineage"]["unique_action_ids"]) == 4
    assert len(value["subject"]["semantic_lineage"]["unique_episode_ids"]) == 3


def test_m13m_full_record_accounting_and_hr1005_non_directional() -> None:
    evidence = candidate()["subject"]["preview_data"]["evidence_119"]
    assert len(evidence) == 17
    assert (
        len({row["governed_receipt_projection"]["episode_id"] for row in evidence})
        == 16
    )
    hr1005 = next(
        row for row in evidence if row["canonical_action_id"] == "house:119:1:312"
    )
    assert (
        hr1005["governed_receipt_projection"]["exact_choice_position_effect"]
        == "non_directional_not_voting"
    )


def test_m13m_scopes_fail_closed() -> None:
    kwargs = {"legislator_id": "leg_valerie_p_foushee", "member_bioguide_id": "F000477"}
    assert (
        education(
            select_education_workforce_site_integration_preview(
                candidate(), scope="119", **kwargs
            )
        )["tier"]
        == "reviewed_conclusion"
    )
    assert (
        education(
            select_education_workforce_site_integration_preview(
                candidate(), scope="all", **kwargs
            )
        )["tier"]
        == "reviewed_conclusion"
    )
    assert (
        education(
            select_education_workforce_site_integration_preview(
                candidate(), scope="118", **kwargs
            )
        )["tier"]
        == "receipts_only"
    )


def test_m13m_direction_and_synthesis_attacks_fail_even_when_resealed() -> None:
    changed = copy.deepcopy(candidate())
    changed["subject"]["presentation"]["repeated_patterns"][0]["show_direction"] = True
    changed["candidate_subject_sha256"] = canonical_digest(changed["subject"])
    with pytest.raises(EducationWorkforceSiteIntegrationCandidateError):
        validate_education_workforce_site_integration_candidate(changed)
    changed = copy.deepcopy(candidate())
    changed["subject"]["presentation"]["syntheses"] = [
        copy.deepcopy(changed["subject"]["presentation"]["repeated_patterns"][0])
    ]
    changed["candidate_subject_sha256"] = canonical_digest(changed["subject"])
    with pytest.raises(EducationWorkforceSiteIntegrationCandidateError):
        validate_education_workforce_site_integration_candidate(changed)


def test_m13m_api_requires_server_opt_in_and_exact_token(monkeypatch) -> None:
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
        params = {"scope": "119", "candidate": "m13m-education-workforce"}
        path = "/legislators/leg_valerie_p_foushee/editorial-presentations"
        assert (
            education(client.get(path, params=params).json())["tier"] == "receipts_only"
        )
        monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
        assert (
            education(client.get(path, params=params).json())["tier"]
            == "reviewed_conclusion"
        )
        assert (
            client.get(path, params={"scope": "119", "candidate": "wrong"}).status_code
            == 422
        )
