from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import pytest
from fastapi.testclient import TestClient

from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.education_workforce_m14g_integration_candidate import (
    ACCEPTED_PUBLIC_COPY_SUBJECT_SHA,
    BASELINE_MAIN_SHA,
    EXPECTED_WORDING_SHAS,
    OLD_HR5408_MEANING,
    EducationWorkforceM14GError,
    merge_m14g_preview_evidence,
    select_m14g_preview,
    validate_m14g_candidate,
)
from app.main import app


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = (
    ROOT
    / "docs/editorial/site_integration_candidates/"
    "f000477_education_workforce_m14g_v1/site_integration_candidate.json"
)
M14F_PATH = (
    ROOT
    / "docs/editorial/public_wording_candidates/"
    "f000477_education_workforce_m14f_v1/accepted_public_copy.json"
)
CORE_PATH = ROOT / "docs/editorial/shared_corpora/house_119_v2/shared_action_core.json"
MEMBER_PROJECTION_PATH = (
    ROOT / "docs/editorial/shared_corpora/house_119_v2/member_projections/f000477.json"
)
LEDGER_PATH = (
    ROOT
    / "docs/editorial/analytical_candidates/"
    "f000477_education_workforce_m14d_v1/accepted_behavioral_findings.json"
)


def candidate() -> dict:
    return json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))


def education(payload: dict) -> dict:
    return next(
        row for row in payload["presentations"] if row["issue_id"] == "EDUCATION_WORKFORCE"
    )


def all_items(presentation: dict) -> list[dict]:
    return [
        presentation["overview"],
        *presentation["repeated_patterns"],
        *presentation["notable_choices"],
    ]


def test_m14g_pins_exact_m14f_copy_authority_and_four_wording_shas() -> None:
    data = candidate()
    accepted = json.loads(M14F_PATH.read_text(encoding="utf-8"))
    bindings = data["subject"]["input_bindings"]
    assert accepted["accepted_public_copy_subject_sha256"] == ACCEPTED_PUBLIC_COPY_SUBJECT_SHA
    assert bindings["m14f_accepted_public_copy"]["subject_sha256"] == ACCEPTED_PUBLIC_COPY_SUBJECT_SHA
    assert bindings["m14f_human_authority"]["subject_sha256"] == (
        "9b1962e1d33dd144a609cd9cbcb5114f81c51a8ce4195bc24112ba9fb10d0cfb"
    )
    assert len(accepted["subject"]["accepted_wording_records"]) == 4
    assert data["subject"]["accepted_wording_item_sha256s"] == EXPECTED_WORDING_SHAS


def test_m14g_exact_hierarchy_lineage_directions_and_finding_count() -> None:
    presentation = candidate()["subject"]["presentation"]
    assert presentation["tier"] == "reviewed_conclusion"
    assert presentation["tier_badge"] == "Full issue review"
    assert presentation["overview"]["wording_item_id"] == "m14f:issue_overview:education_workforce"
    assert len(presentation["overview"]["action_ids"]) == 4
    assert len(presentation["overview"]["episode_ids"]) == 3
    assert len(presentation["repeated_patterns"]) == 2
    assert len(presentation["notable_choices"]) == 1
    assert presentation["syntheses"] == []
    assert presentation["policy_trajectories"] == []
    assert all(item["show_direction"] is False for item in presentation["repeated_patterns"])
    notable = presentation["notable_choices"][0]
    assert (notable["direction"], notable["direction_label"], notable["direction_symbol"]) == (
        "mixed",
        "Mixed",
        "±",
    )
    assert notable["episode_ids"] == ["hr-1048-amendment-and-final-passage"]
    assert len(notable["action_ids"]) == 2
    assert len(presentation["evidence_metadata"]["display_action_ids"]) == 6
    assert sum(len(presentation[field]) for field in (
        "repeated_patterns", "policy_trajectories", "notable_choices"
    )) == 3


def test_m14g_renders_only_seven_retained_public_limitation_instances() -> None:
    data = candidate()
    presentation = data["subject"]["presentation"]
    accepted = json.loads(M14F_PATH.read_text(encoding="utf-8"))
    retained = [
        treatment["public_copy"]
        for record in accepted["subject"]["accepted_wording_records"]
        for treatment in record["limitation_treatments"]
        if treatment["treatment"] == "retained_public_copy"
    ]
    compressed_text = {
        treatment["text"]
        for record in accepted["subject"]["accepted_wording_records"]
        for treatment in record["limitation_treatments"]
        if treatment["treatment"] == "compressed_or_omitted"
    }
    rendered = [
        *(row["body"] for row in presentation["limitations"]),
        *(value for item in presentation["repeated_patterns"] for value in item["limitations"]),
        *(value for item in presentation["notable_choices"] for value in item["limitations"]),
    ]
    assert len(rendered) == len(retained) == 7
    assert sorted(rendered) == sorted(retained)
    assert compressed_text.isdisjoint(rendered)
    assert presentation["overview"]["limitations"] == []
    assert presentation["limitations"] == [{
        "heading": "Final H.R. 1048 vote",
        "body": "The final H.R. 1048 vote applied to the whole package and does not show which provision Foushee opposed.",
    }]


def test_m14g_uses_exact_m14d_ledger_and_v2_receipt_semantics() -> None:
    data = candidate()
    core = json.loads(CORE_PATH.read_text(encoding="utf-8"))
    member_projection = json.loads(MEMBER_PROJECTION_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))["subject"][
        "accepted_episode_disposition_ledger"
    ]
    core_by_id = {row["action_id"]: row for row in core["actions"]}
    projection_by_id = {
        row["action_id"]: row for row in member_projection["actions"]
    }
    receipts = data["subject"]["receipt_projections"]
    ledger_ids = {action_id for episode in ledger for action_id in episode["action_ids"]}
    assert len(receipts) == 17
    assert len({row["canonical_action_id"] for row in receipts}) == 17
    assert {row["canonical_action_id"] for row in receipts} == ledger_ids
    assert len({row["governed_receipt_projection"]["episode_id"] for row in receipts}) == 16
    for row in receipts:
        action_id = row["canonical_action_id"]
        assert row["action_core_sha256"] == core_by_id[action_id]["action_core_sha256"]
        assert row["member_projection_action_core_sha256"] == row["action_core_sha256"]
        assert row["governed_receipt_projection"]["exact_action_meaning"] == (
            core_by_id[action_id]["accepted_exact_action_meaning"]
        )
        assert row["governed_receipt_projection"]["caveats"] == (
            core_by_id[action_id]["accepted_shared_limitations"]
        )
        assert row["governed_receipt_projection"]["member_action"] == (
            projection_by_id[action_id]["official_status"]
        )
        assert row["governed_receipt_projection"]["exact_choice_position_effect"] == (
            projection_by_id[action_id]["exact_choice_effect"]
        )
        assert row["source_identity_bindings"]["governed_action_meaning"] == (
            core_by_id[action_id]["operative_meaning_source_identities"]
        )
        assert row["source_identity_bindings"]["official_member_action"] == (
            projection_by_id[action_id]["member_action_source_identities"]
        )


def test_m14g_hr5408_rich_meaning_and_hr1005_non_directional() -> None:
    receipts = candidate()["subject"]["receipt_projections"]
    hr5408 = next(row for row in receipts if row["canonical_action_id"] == "house:119:2:216")
    meaning = hr5408["governed_receipt_projection"]["exact_action_meaning"]
    assert meaning.startswith("Current wages, hours, and employment terms would have to be maintained")
    assert "mediation" in meaning and "arbitration" in meaning
    assert OLD_HR5408_MEANING not in json.dumps(candidate(), ensure_ascii=False)
    hr1005 = next(row for row in receipts if row["canonical_action_id"] == "house:119:1:312")
    assert hr1005["position"] == "not_voting"
    assert hr1005["governed_receipt_projection"]["member_action"] == "Not Voting"
    assert hr1005["governed_receipt_projection"]["exact_choice_position_effect"] == (
        "resolved_non_directional"
    )
    assert "house:119:1:312" not in candidate()["subject"]["presentation"][
        "evidence_metadata"
    ]["display_action_ids"]


def test_m14g_selection_and_evidence_fail_closed_by_member_issue_and_scope() -> None:
    data = candidate()
    selected = select_m14g_preview(
        data,
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    assert education(selected)["tier"] == "reviewed_conclusion"
    for kwargs in (
        {"legislator_id": "leg_alex_morgan", "member_bioguide_id": "H000001", "scope": "119"},
        {"legislator_id": "leg_valerie_p_foushee", "member_bioguide_id": "F000477", "scope": "118"},
    ):
        assert education(select_m14g_preview(data, **kwargs))["tier"] == "receipts_only"
    base = {"evidence": [{"canonical_action_id": "unchanged"}]}
    assert merge_m14g_preview_evidence(base, data, domain="HEALTHCARE", scope="119") == base
    assert merge_m14g_preview_evidence(base, data, domain="EDUCATION_WORKFORCE", scope="118") == base
    all_scope = select_m14g_preview(
        data,
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="all",
    )
    assert education(all_scope)["scope_boundary"].endswith(
        "The analytical summary remains bounded to the 119th-Congress record."
    )


def test_m14g_api_requires_new_server_opt_in_and_explicit_token(monkeypatch) -> None:
    path = "/preview/m14g/legislators/leg_valerie_p_foushee/editorial-presentations"
    params = {"scope": "119", "candidate": "m14g-education-workforce"}
    client = TestClient(app)
    monkeypatch.delenv("EDITORIAL_PRESENTATION_PREVIEW", raising=False)
    monkeypatch.setenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", "1")
    assert client.get(path, params=params).status_code == 404
    monkeypatch.setenv("EDITORIAL_PRESENTATION_PREVIEW", "1")
    assert client.get(path, params={"scope": "119"}).status_code == 404
    assert education(client.get(path, params=params).json())["tier"] == "reviewed_conclusion"
    assert client.get(path, params={"scope": "119", "candidate": "wrong"}).status_code == 404


def test_m14g_preview_off_preserves_public_api_exactly(monkeypatch) -> None:
    for relative in (
        "backend/app/api/positions.py",
        "backend/app/api/editorial_presentations.py",
        "backend/app/api/search.py",
    ):
        baseline = subprocess.run(
            ["git", "rev-parse", f"{BASELINE_MAIN_SHA}:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        working = subprocess.run(
            ["git", "hash-object", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert working == baseline


def test_m14g_preview_profile_is_gated_and_exact(monkeypatch) -> None:
    client = TestClient(app)
    params = {"candidate": "m14g-education-workforce"}
    path = "/preview/m14g/legislators/leg_valerie_p_foushee/profile"
    monkeypatch.delenv("EDITORIAL_PRESENTATION_PREVIEW", raising=False)
    assert client.get(path, params=params).status_code == 404
    monkeypatch.setenv("EDITORIAL_PRESENTATION_PREVIEW", "1")
    response = client.get(path, params=params)
    assert response.status_code == 200
    assert response.json() == {
        "id": "leg_valerie_p_foushee",
        "bioguide_id": "F000477",
        "name_display": "Valerie P. Foushee",
        "chamber": "house",
        "state": "NC",
        "district": "04",
        "party": "D",
    }


def test_m14g_positions_and_evidence_use_detached_rows_without_database(monkeypatch) -> None:
    monkeypatch.setenv("EDITORIAL_PRESENTATION_PREVIEW", "1")
    params = {"scope": "119", "candidate": "m14g-education-workforce"}
    client = TestClient(app)
    positions = client.get(
        "/preview/m14g/legislators/leg_valerie_p_foushee/positions", params=params
    )
    evidence = client.get(
        "/preview/m14g/legislators/leg_valerie_p_foushee/positions/EDUCATION_WORKFORCE/evidence",
        params=params,
    )
    assert positions.status_code == 200
    education_position = next(
        row for row in positions.json()["positions"] if row["domain"] == "EDUCATION_WORKFORCE"
    )
    assert education_position["total_votes"] == 17
    assert evidence.status_code == 200
    rows = evidence.json()["evidence"]
    assert len(rows) == 17
    hr5408 = next(row for row in rows if row["canonical_action_id"] == "house:119:2:216")
    assert hr5408["governed_receipt_projection"]["exact_action_meaning"].startswith(
        "Current wages, hours, and employment terms would have to be maintained"
    )


def test_m14g_receipt_sources_use_exact_governed_locators_and_labels() -> None:
    serialized = json.dumps(candidate(), ensure_ascii=False)
    assert "https://www.federalregister.gov/presidential-documents/executive-orders" not in serialized
    assert "https://uscode.house.gov/" not in serialized
    expected = {
        "https://www.govinfo.gov/content/pkg/FR-2025-04-03/html/2025-05836.htm": "Executive order",
        "https://www.govinfo.gov/content/pkg/FR-2025-01-30/html/2025-02090.htm": "Executive order",
        "https://www.govinfo.gov/content/pkg/USCODE-2024-title20/html/USCODE-2024-title20-chap28-subchapIV-partG-sec1094.htm": "U.S. Code",
    }
    links = [
        link
        for row in candidate()["subject"]["receipt_projections"]
        for link in row["governed_receipt_projection"]["action_meaning_sources"]
    ]
    by_url = {link["url"]: link["label"] for link in links}
    for url, label in expected.items():
        assert by_url[url] == label
        assert next(link for link in links if link["url"] == url)["public_label"] == label
    assert all(
        link["label"] != "Bill or amendment text"
        for link in links
        if link["url"] in expected
    )


def test_m14g_validation_rejects_authority_or_semantic_tampering() -> None:
    changed = copy.deepcopy(candidate())
    changed["public"] = True
    with pytest.raises(EducationWorkforceM14GError):
        validate_m14g_candidate(changed)
    changed = copy.deepcopy(candidate())
    hr5408 = next(
        row
        for row in changed["subject"]["receipt_projections"]
        if row["canonical_action_id"] == "house:119:2:216"
    )
    hr5408["governed_receipt_projection"][
        "exact_action_meaning"
    ] = OLD_HR5408_MEANING
    changed["candidate_subject_sha256"] = canonical_digest(changed["subject"])
    with pytest.raises(EducationWorkforceM14GError):
        validate_m14g_candidate(changed)


def test_m14g_preserves_protected_ui_historical_m13_and_m14a_through_m14f() -> None:
    protected = [
        "frontend/components/IssueDetail.js",
        "frontend/components/ReviewedAnalysisSection.js",
        "frontend/lib/selectedIssueExperience.mjs",
        "backend/app/editorial_presentations/education_workforce_integration_candidate.py",
        "backend/scripts/build_m13m_education_workforce_site_integration.py",
        "scripts/validate_m13m_education_workforce_site_integration.py",
        "docs/editorial/full_record_reviews/site_integration_candidates/f000477_education_workforce_119_v1",
        "docs/editorial/analytical_candidates/f000477_education_workforce_m14d_v1",
        "docs/editorial/synthesis_candidates/f000477_education_workforce_m14e_v1",
        "docs/editorial/public_wording_candidates/f000477_education_workforce_m14f_v1",
        "docs/editorial/shared_corpora/house_119_v1",
        "docs/editorial/shared_corpora/house_119_v2",
    ]
    result = subprocess.run(
        ["git", "diff", "--name-only", BASELINE_MAIN_SHA, "--", *protected],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""


def test_m14g_has_no_downstream_authority() -> None:
    data = candidate()
    assert all(data[key] is False for key in (
        "accepted", "authorizing", "public", "production_selectable",
        "publication_eligible", "publication_active", "database_writes",
        "production_writes", "deployment",
    ))


def test_frontend_routes_only_explicit_m14g_token_to_detached_surface() -> None:
    source = (ROOT / "frontend/lib/api.js").read_text(encoding="utf-8")
    for token in (
        "m11m-national-security",
        "m12m-environment-energy",
        "m13m-education-workforce",
    ):
        assert source.count(f'"{token}"') == 1
    assert source.count('"m14g-education-workforce"') == 2
    assert 'const M14G_PREVIEW_TOKEN = "m14g-education-workforce"' in source
    assert "`/preview/m14g${path}`" in source
