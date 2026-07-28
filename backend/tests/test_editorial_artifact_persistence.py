from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.editorial_artifacts.bundle import (
    ARTIFACT_TYPES,
    BATCH_KEY,
    ROOT,
    _frozen_crlf_file_sha256,
    build_seed_bundle,
    semantic_hash,
    validate_bundle,
)
from app.editorial_artifacts.migration import MIGRATION, TABLES, validate_migration


@pytest.fixture(scope="module")
def bundle() -> dict:
    return build_seed_bundle()


def artifact(bundle: dict, natural_key: str) -> dict:
    return next(row for row in bundle["artifacts"] if row["natural_key"] == natural_key)


def test_checked_in_manifest_is_deterministic(bundle: dict) -> None:
    checked_in = json.loads(
        (ROOT / "docs/editorial/editorial_artifact_persistence_v1/seed_manifest.json")
        .read_text(encoding="utf-8")
    )
    assert checked_in == bundle
    assert bundle["deterministic_batch_key"] == BATCH_KEY
    assert bundle["manifest_sha256"] == semantic_hash({
        key: value for key, value in bundle.items() if key != "manifest_sha256"
    })


def test_frozen_manifest_byte_identity_is_checkout_eol_independent(
    tmp_path: Path,
) -> None:
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(b'{\n  "frozen": true\n}\n')
    crlf.write_bytes(b'{\r\n  "frozen": true\r\n}\r\n')
    assert _frozen_crlf_file_sha256(lf) == _frozen_crlf_file_sha256(crlf)


def test_taxonomy_counts_and_relationships_are_exact(bundle: dict) -> None:
    assert set(bundle["expected_counts"]["by_type"]) == set(ARTIFACT_TYPES)
    assert bundle["expected_counts"]["artifacts"] == 71
    assert bundle["expected_counts"]["relationships"] == 95
    assert bundle["expected_counts"]["by_type"]["shared_action_dossier"] == 22
    keys = {row["natural_key"] for row in bundle["artifacts"]}
    assert all(rel["parent_natural_key"] in keys for rel in bundle["relationships"])
    assert all(rel["child_natural_key"] in keys for rel in bundle["relationships"])


def test_every_seed_artifact_is_pending_unpromoted_and_ineligible(bundle: dict) -> None:
    assert all(row["editorial_status"] == "human_approval_pending" for row in bundle["artifacts"])
    assert all(row["benchmark_status"] == "not_promoted" for row in bundle["artifacts"])
    assert all(row["production_eligible"] is False for row in bundle["artifacts"])
    assert bundle["publication_registry_expected_rows"] == 0


def test_foushee_economy_semantics(bundle: dict) -> None:
    overlay = artifact(bundle, "f000477:economy_taxes:overlay")["payload"]["overlay"]
    reviewed = overlay["interpretations"]
    controls = overlay["controls"]
    substantive = [
        row for row in reviewed
        if row["member_action"]["recorded"] in {"Yea", "Nay"}
    ]
    not_voting = [
        row for row in reviewed
        if row["member_action"]["recorded"] == "Not Voting"
    ]
    trajectory = artifact(bundle, "f000477:economy_taxes:trajectory")["payload"]
    assert len(substantive) == 6
    assert len(not_voting) == 1
    assert len(controls) == 2
    assert len(trajectory["trajectories"]) == 4
    assert artifact(bundle, "f000477:economy_taxes:propositions")["payload"]["primary_conclusion"]


@pytest.mark.parametrize(
    ("member_id", "signature"),
    [
        ("f000477", "Yea/Nay/Yea"),
        ("m001184", "Nay/Nay/Nay"),
        ("g000586", "Nay/Nay/Nay"),
    ],
)
def test_justice_trajectory_semantics(bundle: dict, member_id: str, signature: str) -> None:
    overlay = artifact(bundle, f"{member_id}:justice_public_safety:overlay")["payload"]["overlay"]
    trajectory = artifact(bundle, f"{member_id}:justice_public_safety:trajectory")["payload"]
    substantive = [row for row in overlay["roll_actions"] if row["counting"] is True]
    assert len(substantive) == 7
    assert len(trajectory["trajectories"]) == 5
    assert signature in json.dumps(trajectory, ensure_ascii=False)


def test_massie_has_no_foushee_leakage(bundle: dict) -> None:
    massie = artifact(bundle, "m001184:justice_public_safety:overlay")
    serialized = json.dumps(massie, ensure_ascii=False)
    assert "M001184" in serialized
    assert "F000477" not in serialized
    assert "Foushee" not in serialized


def test_garcia_is_uniform_opposition_sampled_audit_calibration(bundle: dict) -> None:
    overlay = artifact(bundle, "g000586:justice_public_safety:overlay")["payload"]["overlay"]
    substantive = [row for row in overlay["roll_actions"] if row["counting"] is True]
    assert {row["action"] for row in substantive} == {"Nay"}
    proposition = artifact(bundle, "g000586:justice_public_safety:propositions")
    assert "does not reveal one consistent" in proposition["payload"]["primary_conclusion"]
    assert proposition["review_route"] == "sampled_audit"
    assert artifact(bundle, "g000586:justice_public_safety:reference")["payload"]["designation"] == "sampled_audit_calibration"


def test_shared_justice_evidence_is_not_copied_per_member(bundle: dict) -> None:
    justice_shared = [
        row for row in bundle["artifacts"]
        if row["issue_id"] == "JUSTICE_PUBLIC_SAFETY"
        and row["artifact_type"] in {"shared_action_dossier", "policy_episode"}
    ]
    assert len([row for row in justice_shared if row["artifact_type"] == "shared_action_dossier"]) == 13
    assert len([row for row in justice_shared if row["artifact_type"] == "policy_episode"]) == 5
    assert all(row["member_bioguide_id"] is None for row in justice_shared)


def test_synthetic_universes_are_metadata_only(bundle: dict) -> None:
    serialized_payloads = json.dumps(bundle["artifacts"], ensure_ascii=False)
    assert "synthetic-large-record-v1" not in serialized_payloads
    assert not any("synthetic-vector" in row["natural_key"] for row in bundle["artifacts"])
    assert "128 synthetic Justice vectors" in bundle["excluded_artifacts"]


def test_bundle_validation_rejects_content_conflict(bundle: dict) -> None:
    changed = copy.deepcopy(bundle)
    changed["artifacts"][0]["payload"]["conflict"] = True
    changed_without_hash = {key: value for key, value in changed.items() if key != "manifest_sha256"}
    changed["manifest_sha256"] = semantic_hash(changed_without_hash)
    with pytest.raises(ValueError, match="content hash mismatch"):
        validate_bundle(changed)


def test_migration_is_additive_and_pinned() -> None:
    result = validate_migration()
    assert result["identifier"] == "0016"
    assert set(result["tables"]) == TABLES
    assert len(result["sha256"]) == 64
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "from anon, authenticated" in sql
    assert "editorial_publication_registry_fail_closed" in sql
    assert "editorial_artifact_versions_immutable" in sql


def test_public_frontend_has_no_editorial_store_or_legacy_registry() -> None:
    assert not (ROOT / "frontend/lib/editorialIssueProductionSlices.mjs").exists()
    route_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "frontend/app", ROOT / "frontend/components")
        for path in root.rglob("*.js")
    )
    assert "editorial_artifact_versions" not in route_sources
    assert "editorial_publication_registry" not in route_sources
    assert "editorialIssueProductionSlices" not in route_sources


def test_no_public_api_route_references_editorial_store() -> None:
    route_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "backend/app/api").glob("*.py")
    )
    assert "editorial_artifact_versions" not in route_sources
    assert "editorial_publication_registry" not in route_sources
