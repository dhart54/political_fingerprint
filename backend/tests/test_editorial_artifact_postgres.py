from __future__ import annotations

import copy
import os

import pytest

from app.editorial_artifacts.bundle import BATCH_KEY, build_seed_bundle
from app.editorial_artifacts.repository import EditorialArtifactRepository
from scripts.editorial_artifact_store import (
    StoreSafetyError,
    insert_bundle,
    resolve_canonical_identities,
)

DB_URL = os.getenv("EDITORIAL_DISPOSABLE_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="disposable PostgreSQL URL is not configured")


@pytest.fixture()
def connection():
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        yield conn
        conn.rollback()


def test_same_version_same_hash_is_idempotent(connection) -> None:
    bundle = build_seed_bundle()
    result = insert_bundle(connection, bundle, resolve_canonical_identities(connection, bundle))
    assert result["artifacts_inserted"] == 0
    assert result["artifacts_idempotent"] == 71
    assert result["relationships_inserted"] == 0


def test_same_version_different_hash_fails_closed(connection) -> None:
    bundle = build_seed_bundle()
    changed = copy.deepcopy(bundle)
    changed["artifacts"][0]["content_sha256"] = "1" * 64
    with pytest.raises(StoreSafetyError, match="conflicting immutable artifact version"):
        insert_bundle(connection, changed, resolve_canonical_identities(connection, changed))


def test_invalid_type_status_and_hash_are_rejected(connection) -> None:
    row = connection.execute(
        "SELECT * FROM editorial_artifact_versions ORDER BY artifact_id LIMIT 1"
    ).fetchone()
    for column, invalid in (
        ("artifact_type", "fictional_artifact"),
        ("editorial_status", "published_by_presence"),
        ("content_sha256", "bad-hash"),
    ):
        with connection.transaction(force_rollback=True):
            with pytest.raises(Exception):
                connection.execute(
                    f"""INSERT INTO editorial_artifact_versions
                        (artifact_type, natural_key, schema_version, artifact_version,
                         payload_jsonb, content_sha256, source_manifest_sha256,
                         source_commit_sha, batch_id, editorial_status, benchmark_status,
                         production_eligible, review_route)
                        VALUES (%s, %s, %s, 2, %s, %s, %s, %s, %s, %s, %s, FALSE, %s)""",
                    (
                        invalid if column == "artifact_type" else row["artifact_type"],
                        f"constraint-test:{column}",
                        row["schema_version"],
                        row["payload_jsonb"],
                        invalid if column == "content_sha256" else row["content_sha256"],
                        row["source_manifest_sha256"],
                        row["source_commit_sha"],
                        row["batch_id"],
                        invalid if column == "editorial_status" else row["editorial_status"],
                        row["benchmark_status"],
                        row["review_route"],
                    ),
                )


def test_orphan_relationship_is_rejected(connection) -> None:
    with connection.transaction(force_rollback=True):
        with pytest.raises(Exception):
            connection.execute(
                """INSERT INTO editorial_artifact_relationships
                   (parent_artifact_id, child_artifact_id, relationship_type)
                   VALUES (-1, -2, 'contains_action')"""
            )


def test_valid_supersession_is_append_only(connection) -> None:
    from psycopg.types.json import Jsonb

    row = connection.execute(
        """SELECT * FROM editorial_artifact_versions
           WHERE artifact_type = 'issue_ontology' ORDER BY artifact_id LIMIT 1"""
    ).fetchone()
    with connection.transaction(force_rollback=True):
        inserted = connection.execute(
            """INSERT INTO editorial_artifact_versions
               (artifact_type, natural_key, schema_version, artifact_version,
                payload_jsonb, content_sha256, source_manifest_sha256, source_commit_sha,
                batch_id, supersedes_artifact_id, issue_id, congress, chamber,
                editorial_status, benchmark_status, production_eligible, review_route)
               VALUES (%s,%s,%s,2,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE,%s)
               RETURNING artifact_id""",
            (
                row["artifact_type"], row["natural_key"], row["schema_version"],
                Jsonb(row["payload_jsonb"]), row["content_sha256"], row["source_manifest_sha256"],
                row["source_commit_sha"], row["batch_id"], row["artifact_id"],
                row["issue_id"], row["congress"], row["chamber"], row["editorial_status"],
                row["benchmark_status"], row["review_route"],
            ),
        ).fetchone()
        assert inserted["artifact_id"]
        with pytest.raises(Exception, match="append-only"):
            connection.execute(
                "UPDATE editorial_artifact_versions SET review_route = 'blocked' WHERE artifact_id = %s",
                (inserted["artifact_id"],),
            )


def test_publication_activation_rejects_pending_unpromoted_ineligible(connection) -> None:
    candidate = connection.execute(
        """SELECT artifact_id, member_bioguide_id, issue_id
           FROM editorial_artifact_versions
           WHERE artifact_type = 'issue_public_presentation'
           ORDER BY artifact_id LIMIT 1"""
    ).fetchone()
    with connection.transaction(force_rollback=True):
        with pytest.raises(Exception, match="fails approval"):
            connection.execute(
                """INSERT INTO editorial_publication_registry
                   (member_bioguide_id, issue_id, artifact_id, publicly_active, activated_at)
                   VALUES (%s, %s, %s, TRUE, NOW())""",
                (candidate["member_bioguide_id"], candidate["issue_id"], candidate["artifact_id"]),
            )


def test_repository_graph_pending_and_publication_contract(connection) -> None:
    repository = EditorialArtifactRepository(connection)
    pending = repository.list_pending_slices()
    assert len(pending) == 4
    candidate = repository.get_slice_candidate("M001184", "JUSTICE_PUBLIC_SAFETY")
    assert candidate and candidate["production_eligible"] is False
    assert repository.get_latest_validation("G000586", "JUSTICE_PUBLIC_SAFETY")
    assert len(repository.get_shared_evidence("JUSTICE_PUBLIC_SAFETY")) == 18
    assert repository.publication_selector() == []
    graph = repository.load_graph(candidate["artifact_id"])
    assert graph and len(graph["relationships"]) >= 7


def test_anonymous_roles_cannot_read_pending_artifacts(connection) -> None:
    for role in ("anon", "authenticated"):
        with connection.transaction(force_rollback=True):
            connection.execute(f"SET LOCAL ROLE {role}")
            with pytest.raises(Exception):
                connection.execute("SELECT * FROM editorial_artifact_versions").fetchall()


def test_exact_batch_is_present_once(connection) -> None:
    row = connection.execute(
        """SELECT COUNT(*) AS n, MIN(manifest_sha256) AS manifest_sha256
           FROM editorial_artifact_batches WHERE deterministic_batch_key = %s""",
        (BATCH_KEY,),
    ).fetchone()
    assert row["n"] == 1
