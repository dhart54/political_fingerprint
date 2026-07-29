from __future__ import annotations

import copy
import json
import sqlite3
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.editorial_presentations.compiler import (
    approval_subject_for_artifact,
    artifact_digest,
    compile_public_issue_presentation as _compile_public_issue_presentation,
)
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.main import app
from app.main import get_deployed_commit_sha
from app.semantic_ir.pipeline import replay_accepted_reference
from backend.tests.test_editorial_public_presentation import (
    _approved_receipt,
    _compiled,
    _input_for,
    _trusted_contract,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    ROOT
    / "docs/editorial/presentations/"
    "f000477_justice_public_safety_119_review_fixture.json"
)
CASES = ROOT / "docs/semantic_ir/accepted/development_cases.json"


def test_health_exposes_validated_deployed_commit(monkeypatch) -> None:
    commit = "a" * 40
    monkeypatch.setenv("RENDER_GIT_COMMIT", commit.upper())
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "commit_sha": commit}
    monkeypatch.setenv("RENDER_GIT_COMMIT", "untrusted")
    assert get_deployed_commit_sha() == "unknown"


def compile_public_issue_presentation(compiled: dict, authoring: dict) -> dict:
    return _compile_public_issue_presentation(
        compiled,
        authoring,
        trusted_action_source_contract=_trusted_contract(compiled, authoring),
    )


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
        "publication_metadata_jsonb": {
            "approval_receipt": _approved_receipt(artifact)
        },
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


def test_embedded_provenance_receipt_injection_cannot_authorize_copy() -> None:
    artifact = _approved_artifact()
    artifact["provenance"]["review_receipt"] = _approved_receipt(artifact)
    assert _justice([_row(artifact)])["tier"] == "receipts_only"


def test_limitation_digest_substitution_fails_selection() -> None:
    artifact = _approved_artifact()
    row = _row(artifact)
    row["publication_metadata_jsonb"]["approval_receipt"][
        "limitations_sha256"
    ] = "0" * 64
    assert _justice([row])["tier"] == "receipts_only"


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
            natural_key TEXT NOT NULL,
            artifact_type TEXT NOT NULL
        );
        CREATE TABLE editorial_publication_registry (
            artifact_id INTEGER NOT NULL,
            member_bioguide_id TEXT NOT NULL,
            issue_id TEXT NOT NULL,
            publicly_active INTEGER NOT NULL,
            deactivated_at TEXT,
            publication_metadata_jsonb TEXT NOT NULL
        );
        CREATE TABLE editorial_artifact_relationships (
            parent_artifact_id INTEGER NOT NULL,
            child_artifact_id INTEGER NOT NULL,
            relationship_type TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            metadata_jsonb TEXT NOT NULL
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
            "issue_public_presentation",
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
            "issue_public_presentation",
        ),
        (3, "{}", "a" * 64, "human_approved", "not_promoted", 0,
         "editorial_publication_validation_v1", 1, "validation-key",
         "standardization_validation_result"),
        (4, "{}", "b" * 64, "human_approved", "not_promoted", 0,
         "editorial_publication_source_manifest_v1", 1, "source-key",
         "source_manifest"),
    ]
    connection.executemany(
        """
        INSERT INTO editorial_artifact_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    metadata = json.dumps(
        {
            "presentation_natural_key": artifact["artifact_identity"]["artifact_id"],
            "presentation_artifact_version": 1,
            "active_artifact_sha256": artifact_digest(artifact),
            "validation_natural_key": "validation-key",
            "validation_artifact_version": 1,
            "validation_content_sha256": "a" * 64,
            "source_manifest_natural_key": "source-key",
            "source_manifest_artifact_version": 1,
            "source_manifest_content_sha256": "b" * 64,
            "relationship_metadata": {"activation_bundle_id": "bundle"},
        },
        separators=(",", ":"),
    )
    connection.executemany(
        """
        INSERT INTO editorial_publication_registry
        VALUES (?, 'F000477', 'JUSTICE_PUBLIC_SAFETY', 1, NULL, ?)
        """,
        [(1, metadata), (2, metadata)],
    )
    connection.executemany(
        "INSERT INTO editorial_artifact_relationships VALUES (?, ?, ?, 0, ?)",
        [
            (1, 3, "has_validation", json.dumps({"activation_bundle_id": "bundle"}, separators=(",", ":"))),
            (1, 4, "uses_source_manifest", json.dumps({"activation_bundle_id": "bundle"}, separators=(",", ":"))),
        ],
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


def test_wording_and_detached_receipt_substitution_fail_closed() -> None:
    artifact = _approved_artifact()
    changed_wording = copy.deepcopy(artifact)
    changed_wording["editorial_wording"]["conclusion"]["body"]["text"] += (
        " Substituted."
    )
    changed_digest = copy.deepcopy(artifact)
    changed_digest["provenance"]["reviewed_wording_sha256"] = "0" * 64
    wrong_receipt_row = _row(artifact)
    wrong_receipt_row["publication_metadata_jsonb"]["approval_receipt"]["binding"][
        "artifact_id"
    ] = "different:artifact"
    assert _justice([_row(changed_wording)])["tier"] == "receipts_only"
    assert _justice([_row(changed_digest)])["tier"] == "receipts_only"
    assert _justice([wrong_receipt_row])["tier"] == "receipts_only"


def test_detached_receipt_scope_identity_and_stale_wording_fail_closed() -> None:
    artifact = _approved_artifact()
    for field, value in (
        ("member_id", "X000001"),
        ("issue_id", "ECONOMY_TAXES"),
        ("approved_scope", "118"),
        ("reviewed_wording_sha256", "0" * 64),
    ):
        row = _row(artifact)
        row["publication_metadata_jsonb"]["approval_receipt"]["binding"][
            field
        ] = value
        assert _justice([row])["tier"] == "receipts_only"


def test_pending_or_unsigned_detached_receipt_fails_closed() -> None:
    artifact = _approved_artifact()
    row = _row(artifact)
    receipt = row["publication_metadata_jsonb"]["approval_receipt"]
    receipt["status"] = "human_approval_pending"
    receipt["reviewer"] = {
        "reviewer_id": "not_supplied",
        "authority": "not_supplied",
    }
    receipt["decision_timestamp"] = None
    receipt["approved_statement_ids"] = []
    receipt["approved_mapping_ids"] = []
    receipt["decisions"] = {
        "editorial_wording": "pending",
        "gold_benchmark_promotion": "pending",
        "production_eligibility": "pending",
    }
    assert _justice([row])["tier"] == "receipts_only"


def test_publication_controls_are_outside_subject_but_still_enforced() -> None:
    artifact = _approved_artifact()
    baseline_subject = approval_subject_for_artifact(artifact)
    inactive = copy.deepcopy(artifact)
    inactive["controls"]["publication"]["active"] = False
    inactive["controls"]["publication_gates_passed"] = False
    inactive["controls"]["effective_public_tier"] = "receipts_only"
    assert approval_subject_for_artifact(inactive) == baseline_subject
    assert _justice([_row(inactive)])["tier"] == "receipts_only"


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


def test_repository_normalizes_default_dbapi_tuple_rows() -> None:
    class Cursor:
        description = [
            SimpleNamespace(name="artifact_id"),
            SimpleNamespace(name="payload_jsonb"),
        ]

        @staticmethod
        def fetchall() -> list[tuple[object, ...]]:
            return [(101, {"schema_version": "test"})]

        @staticmethod
        def fetchone() -> tuple[object, ...]:
            return (101, {"schema_version": "test"})

    class Connection:
        @staticmethod
        def execute(_query: str, _params: tuple[object, ...]) -> Cursor:
            return Cursor()

    rows = EditorialArtifactRepository(Connection())._all("SELECT test")

    assert rows == [
        {"artifact_id": 101, "payload_jsonb": {"schema_version": "test"}}
    ]
    assert EditorialArtifactRepository(Connection())._one("SELECT test") == rows[0]


def test_repository_normalizes_list_row_with_standard_dbapi_metadata() -> None:
    marker = {"nested": [1, None]}
    result = EditorialArtifactRepository._row_to_dict(
        SimpleNamespace(description=[("artifact_id", None), ("payload_jsonb", None)]),
        [101, marker],
    )
    assert result == {"artifact_id": 101, "payload_jsonb": marker}
    assert result["payload_jsonb"] is marker


def test_repository_rejects_tuple_row_width_mismatch() -> None:
    cursor = SimpleNamespace(
        description=[
            SimpleNamespace(name="artifact_id"),
            SimpleNamespace(name="payload_jsonb"),
        ]
    )
    with pytest.raises(ValueError, match="row width"):
        EditorialArtifactRepository._row_to_dict(cursor, (101,))
    with pytest.raises(ValueError, match="row width"):
        EditorialArtifactRepository._row_to_dict(cursor, (101, {}, "extra"))


def test_repository_preserves_supported_mapping_values_and_key_identity() -> None:
    values = {
        "uuid_value": UUID("3f7fa76a-fc18-4ab9-a8e0-786dd28f0c0c"),
        "datetime_value": datetime(2026, 7, 28, tzinfo=UTC),
        "json_value": {"nested": [1, True]},
        "null_value": None,
    }
    result = EditorialArtifactRepository._row_to_dict(
        SimpleNamespace(description=None), values
    )
    assert result == values
    assert list(result) == list(values)
    assert all(result[key] is value for key, value in values.items())


@pytest.mark.parametrize(
    "row",
    [
        "ab",
        b"ab",
        bytearray(b"ab"),
        memoryview(b"ab"),
        {1, 2},
        iter((1, 2)),
        (value for value in (1, 2)),
    ],
)
def test_repository_rejects_arbitrary_iterables_as_rows(row: object) -> None:
    cursor = SimpleNamespace(description=[("first",), ("second",)])
    with pytest.raises(TypeError, match="mapping or a non-string sequence"):
        EditorialArtifactRepository._row_to_dict(cursor, row)


class _ArbitraryIterable:
    def __iter__(self) -> Iterator[int]:
        return iter((1, 2))


def test_repository_rejects_arbitrary_nonsequence_iterable() -> None:
    with pytest.raises(TypeError, match="mapping or a non-string sequence"):
        EditorialArtifactRepository._row_to_dict(
            SimpleNamespace(description=[("first",), ("second",)]),
            _ArbitraryIterable(),
        )


class _NonStringKeyMapping(Mapping[object, object]):
    def __getitem__(self, key: object) -> object:
        return {1: "integer", "1": "string"}[key]

    def __iter__(self) -> Iterator[object]:
        return iter((1, "1"))

    def __len__(self) -> int:
        return 2


@pytest.mark.parametrize(
    "row",
    [
        _NonStringKeyMapping(),
        {"": 1},
        {"   ": 1},
    ],
)
def test_repository_rejects_invalid_mapping_keys(row: Mapping[object, object]) -> None:
    with pytest.raises(TypeError, match="mapping row"):
        EditorialArtifactRepository._row_to_dict(
            SimpleNamespace(description=None), row
        )


def test_repository_rejects_missing_cursor_description() -> None:
    with pytest.raises(TypeError, match="did not provide row metadata"):
        EditorialArtifactRepository._row_to_dict(
            SimpleNamespace(description=None), (1,)
        )


@pytest.mark.parametrize(
    "description",
    [
        [("same",), ("same",)],
        [SimpleNamespace(name="same"), SimpleNamespace(name="same")],
    ],
)
def test_repository_rejects_duplicate_cursor_names(description: object) -> None:
    with pytest.raises(ValueError, match="duplicate column name 'same'"):
        EditorialArtifactRepository._row_to_dict(
            SimpleNamespace(description=description), (1, 2)
        )


@pytest.mark.parametrize(
    "description",
    [
        [(1,)],
        [("",)],
        [("   ",)],
        [SimpleNamespace(name=1)],
        [SimpleNamespace(name="")],
        [SimpleNamespace(name="   ")],
        [[]],
        [object()],
        (item for item in [("value",)]),
    ],
)
def test_repository_rejects_invalid_cursor_metadata(description: object) -> None:
    with pytest.raises(TypeError, match="description|column name|metadata"):
        EditorialArtifactRepository._row_to_dict(
            SimpleNamespace(description=description), (1,)
        )


def test_operational_database_failure_is_not_recast_as_receipts_only() -> None:
    with patch(
        "app.api.editorial_presentations._load_publication_rows",
        side_effect=RuntimeError("database unavailable"),
    ):
        with pytest.raises(RuntimeError, match="database unavailable"):
            TestClient(app).get(
                "/legislators/leg_valerie_p_foushee/editorial-presentations",
                params={"scope": "119"},
            )
