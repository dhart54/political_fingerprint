from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.editorial_presentations.compiler import compile_public_issue_presentation
from app.editorial_presentations.selector import select_public_presentations
from app.main import app
from app.semantic_ir.pipeline import replay_accepted_reference


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_review_fixture.json"
)
CASES = ROOT / "docs/semantic_ir/accepted/development_cases.json"


def _approved_artifact() -> dict:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    case = next(
        item
        for item in cases
        if item["case_id"] == "semir-dev-05-justice-mechanism-divide"
    )
    compiled = replay_accepted_reference(case).compiled_ir
    authoring = json.loads(FIXTURE.read_text(encoding="utf-8"))
    controls = authoring["controls"]
    controls["editorial"]["human_approval_status"] = "human_approved"
    controls["benchmark"]["status"] = "promoted"
    controls["production"]["eligible"] = True
    controls["publication"]["active"] = True
    controls["review_receipt"] = {
        "receipt_id": "test-only-authorized-receipt",
        "status": "approved",
        "approvals": {
            "bounded_issue_conclusion": True,
            "repeated_pattern_statements": True,
            "fentanyl_limitation": True,
            "claim_source_mappings": True,
            "benchmark_promotion": True,
            "production_eligibility": True,
        },
    }
    return compile_public_issue_presentation(compiled, authoring)


def _row(artifact: dict, **overrides: object) -> dict:
    row = {
        "artifact_id": 1,
        "member_bioguide_id": "F000477",
        "issue_id": "JUSTICE_PUBLIC_SAFETY",
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "promoted",
        "production_eligible": True,
        "payload_jsonb": artifact,
    }
    row.update(overrides)
    return row


def test_receipts_only_fallback_is_supplied_when_selector_is_empty() -> None:
    result = select_public_presentations(
        [],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    justice = next(
        item
        for item in result["presentations"]
        if item["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
    )
    assert justice["tier"] == "receipts_only"
    assert justice["tier_badge"] == "Vote receipts"
    assert justice["conclusion"] is None


def test_approved_artifact_is_visible_for_119_and_bounded_under_all() -> None:
    row = _row(_approved_artifact())
    recent = select_public_presentations(
        [row],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    full = select_public_presentations(
        [row],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="all",
    )
    recent_justice = recent["presentations"][6]
    full_justice = full["presentations"][6]
    assert recent_justice["tier"] == "reviewed_conclusion"
    assert recent_justice["reviewed_scope"] == "119"
    assert "119th-Congress" in full_justice["scope_boundary"]


def test_approved_artifact_is_not_visible_for_118() -> None:
    result = select_public_presentations(
        [_row(_approved_artifact())],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="118",
    )
    assert result["presentations"][6]["tier"] == "receipts_only"


def test_pending_ineligible_inactive_and_wrong_member_rows_are_never_exposed() -> None:
    artifact = _approved_artifact()
    rows = [
        _row(artifact, editorial_status="human_approval_pending"),
        _row(artifact, production_eligible=False),
        _row(artifact, publicly_active=False),
        _row(artifact, member_bioguide_id="X000001"),
    ]
    result = select_public_presentations(
        rows,
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    assert result["presentations"][6]["tier"] == "receipts_only"


def test_raw_vote_reordering_and_yea_nay_fields_cannot_change_conclusion() -> None:
    artifact = _approved_artifact()
    baseline = select_public_presentations(
        [_row(artifact)],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    mutated_row = _row(copy.deepcopy(artifact))
    mutated_row["raw_votes"] = [
        {"position": "Nay", "roll": 999},
        {"position": "Yea", "roll": 1},
    ]
    mutated = select_public_presentations(
        [mutated_row],
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope="119",
    )
    assert mutated["presentations"][6] == baseline["presentations"][6]


def test_api_uses_read_only_selector_payload() -> None:
    with patch(
        "app.api.editorial_presentations._load_publication_rows",
        return_value=[_row(_approved_artifact())],
    ):
        response = TestClient(app).get(
            "/legislators/leg_valerie_p_foushee/editorial-presentations",
            params={"scope": "119"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["member_bioguide_id"] == "F000477"
    assert payload["presentations"][6]["tier"] == "reviewed_conclusion"
