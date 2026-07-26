from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.editorial_presentations.compiler import (
    artifact_digest,
    build_review_binding,
    compile_public_issue_presentation,
)
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.main import app
from app.semantic_ir.pipeline import replay_accepted_reference
from backend.tests.test_editorial_public_presentation import (
    _compiled,
    _input_for,
)


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
    controls["benchmark"]["status"] = "gold_benchmark"
    controls["production"]["eligible"] = True
    controls["publication"]["active"] = True
    controls["review_receipt"] = {
        "receipt_id": "test-only-authorized-receipt",
        "status": "approved",
        "binding": build_review_binding(compiled, authoring),
        "reviewer": {
            "reviewer_id": "test-reviewer",
            "authority": "test-authorized-editorial-reviewer",
        },
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
    identity = artifact["artifact_identity"]
    row = {
        "artifact_id": 101,
        "member_bioguide_id": "F000477",
        "issue_id": "JUSTICE_PUBLIC_SAFETY",
        "publicly_active": True,
        "deactivated_at": None,
        "editorial_status": "human_approved",
        "benchmark_status": "gold_benchmark",
        "production_eligible": True,
        "natural_key": identity["artifact_id"],
        "artifact_version": identity["artifact_version"],
        "schema_version": artifact["schema_version"],
        "content_sha256": artifact_digest(artifact),
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


def test_non_directional_tier_is_returned_without_analytical_sections() -> None:
    compiled = _compiled("semir-dev-09-not-voting-heavy-record")
    artifact = compile_public_issue_presentation(compiled, _input_for(compiled))
    member_id = artifact["artifact_identity"]["member_id"]
    result = select_public_presentations(
        [_row(artifact, member_bioguide_id=member_id)],
        legislator_id="test-legislator",
        member_bioguide_id=member_id,
        scope="119",
    )
    justice = result["presentations"][6]
    assert justice["tier"] == "non_directional_or_limited_evidence"
    assert justice["conclusion"] is None
    assert justice["repeated_patterns"] == []
    assert justice["policy_trajectories"] == []


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


def _justice(rows: list[dict], *, scope: str = "119") -> dict:
    result = select_public_presentations(
        rows,
        legislator_id="leg_valerie_p_foushee",
        member_bioguide_id="F000477",
        scope=scope,
    )
    return result["presentations"][6]


def test_valid_persistence_benchmark_vocabulary_is_enforced() -> None:
    artifact = _approved_artifact()
    assert _justice([_row(artifact)])["tier"] == "reviewed_conclusion"
    assert _justice(
        [_row(artifact, benchmark_status="not_promoted")]
    )["tier"] == "receipts_only"


def test_repository_selector_accepts_only_persistence_valid_gold_benchmark() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE editorial_artifact_versions (
            artifact_id INTEGER PRIMARY KEY,
            payload_jsonb TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            editorial_status TEXT NOT NULL,
            benchmark_status TEXT NOT NULL
                CHECK (benchmark_status IN ('not_promoted', 'gold_benchmark')),
            production_eligible INTEGER NOT NULL,
            schema_version TEXT NOT NULL,
            artifact_version INTEGER NOT NULL,
            natural_key TEXT NOT NULL
        );
        CREATE TABLE editorial_publication_registry (
            artifact_id INTEGER NOT NULL,
            member_bioguide_id TEXT NOT NULL,
            issue_id TEXT NOT NULL,
            publicly_active INTEGER NOT NULL,
            deactivated_at TEXT
        );
        """
    )
    artifact = _approved_artifact()
    payload = json.dumps(artifact)
    rows = [
        (
            1,
            payload,
            artifact_digest(artifact),
            "human_approved",
            "gold_benchmark",
            1,
            artifact["schema_version"],
            artifact["artifact_identity"]["artifact_version"],
            artifact["artifact_identity"]["artifact_id"],
        ),
        (
            2,
            payload,
            artifact_digest(artifact),
            "human_approved",
            "not_promoted",
            1,
            artifact["schema_version"],
            artifact["artifact_identity"]["artifact_version"],
            artifact["artifact_identity"]["artifact_id"],
        ),
    ]
    connection.executemany(
        """
        INSERT INTO editorial_artifact_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.executemany(
        """
        INSERT INTO editorial_publication_registry
        VALUES (?, 'F000477', 'JUSTICE_PUBLIC_SAFETY', 1, NULL)
        """,
        [(1,), (2,)],
    )
    selected = EditorialArtifactRepository(connection).publication_selector()
    connection.close()
    assert [row["artifact_id"] for row in selected] == [1]
    assert selected[0]["benchmark_status"] == "gold_benchmark"


def test_stale_derived_flags_cannot_bypass_pending_approval() -> None:
    artifact = _approved_artifact()
    artifact["controls"]["editorial"][
        "human_approval_status"
    ] = "human_approval_pending"
    artifact["controls"]["publication_gates_passed"] = True
    artifact["controls"]["effective_public_tier"] = "reviewed_conclusion"
    assert _justice([_row(artifact)])["tier"] == "receipts_only"


def test_stale_effective_tier_cannot_bypass_inactive_publication() -> None:
    artifact = _approved_artifact()
    artifact["controls"]["publication"]["active"] = False
    artifact["controls"]["effective_public_tier"] = "reviewed_conclusion"
    assert _justice([_row(artifact)])["tier"] == "receipts_only"


def test_member_issue_and_scope_substitution_fail_closed() -> None:
    artifact = _approved_artifact()
    wrong_member = copy.deepcopy(artifact)
    wrong_member["artifact_identity"]["member_id"] = "X000001"
    wrong_issue = copy.deepcopy(artifact)
    wrong_issue["artifact_identity"]["issue_id"] = "ECONOMY_TAXES"
    wrong_scope = copy.deepcopy(artifact)
    wrong_scope["artifact_identity"]["congress"] = 118
    wrong_scope["artifact_identity"]["scope"] = "118"
    for candidate in (wrong_member, wrong_issue, wrong_scope):
        assert _justice([_row(candidate)])["tier"] == "receipts_only"


def test_registry_payload_identity_and_digest_mismatches_fail_closed() -> None:
    artifact = _approved_artifact()
    assert _justice(
        [_row(artifact, natural_key="different:artifact")]
    )["tier"] == "receipts_only"
    assert _justice(
        [_row(artifact, artifact_version=2)]
    )["tier"] == "receipts_only"
    assert _justice(
        [_row(artifact, content_sha256="0" * 64)]
    )["tier"] == "receipts_only"


def test_wording_and_review_receipt_substitution_fail_closed() -> None:
    artifact = _approved_artifact()
    changed_wording = copy.deepcopy(artifact)
    changed_wording["editorial_wording"]["conclusion"]["body"]["text"] += (
        " Substituted."
    )
    changed_digest = copy.deepcopy(artifact)
    changed_digest["provenance"]["reviewed_wording_sha256"] = "0" * 64
    wrong_receipt_artifact = copy.deepcopy(artifact)
    wrong_receipt_artifact["controls"]["review_receipt"]["binding"][
        "artifact_id"
    ] = "different:artifact"
    wrong_receipt_artifact["provenance"]["review_receipt"] = copy.deepcopy(
        wrong_receipt_artifact["controls"]["review_receipt"]
    )
    for candidate in (
        changed_wording,
        changed_digest,
        wrong_receipt_artifact,
    ):
        assert _justice([_row(candidate)])["tier"] == "receipts_only"


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
