from __future__ import annotations

import copy
import os

import pytest
from psycopg.errors import ReadOnlySqlTransaction

from app.editorial_presentations.compiler import canonical_digest
from app.editorial_presentations.publication_activation_governance_v2 import (
    validate_execution_v2,
)
from scripts.editorial_artifact_store import _connect
from scripts.foushee_education_workforce_publication_preparation import (
    _counts,
    _registry_rows,
    _state_fingerprint,
)
from test_m13n_r_education_publication_preparation_postgres import (
    _prepare_post_m12n_baseline,
)
from test_publication_activation_governance_v2 import (
    NOW,
    _package,
    _preflight,
    _runtime_proof,
)

DATABASE_URL = os.getenv("PUBLICATION_GOVERNANCE_V2_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="PUBLICATION_GOVERNANCE_V2_DATABASE_URL is required",
)


def _registry_identities(rows: list[dict]) -> list[dict]:
    return sorted(
        [
            {
                "member_bioguide_id": row["member_bioguide_id"],
                "issue_id": row["issue_id"],
                "artifact_id": row["artifact_id"],
                "artifact_version": row["artifact_version"],
                "presentation_natural_key": row["natural_key"],
                "content_sha256": row["content_sha256"],
                "source_commit_sha": row["source_commit_sha"],
                "publication_metadata_sha256": canonical_digest(
                    row["publication_metadata_jsonb"]
                ),
                "publicly_active": row["publicly_active"],
            }
            for row in rows
        ],
        key=lambda item: (item["member_bioguide_id"], item["issue_id"]),
    )


def _bind_observed_baseline(
    candidate: dict,
    write_set: dict,
    authority: dict,
    *,
    counts: dict,
    fingerprint: str,
    registry_rows: list[dict],
) -> None:
    baseline = authority["subject"]["stable_production_baseline"]
    baseline["counts"] = counts
    baseline["state_fingerprint_sha256"] = fingerprint
    baseline["existing_registry_identities"] = _registry_identities(registry_rows)
    rollback = write_set["subject"]["rollback_contract"]
    rollback["restore_counts"] = counts
    rollback["restore_state_fingerprint_sha256"] = fingerprint
    after = copy.deepcopy(counts)
    after["batches"] += 1
    after["artifacts"] += 1
    after["publication_registry"] += 1
    write_set["subject"]["expected_postconditions"]["counts"] = after
    write_set["subject"]["stable_production_baseline_binding_sha256"] = (
        canonical_digest(baseline)
    )
    write_set["write_set_subject_sha256"] = canonical_digest(write_set["subject"])
    authority["subject"]["exact_write_set_subject_sha256"] = write_set[
        "write_set_subject_sha256"
    ]
    authority["subject"]["rollback_contract_sha256"] = canonical_digest(rollback)
    authority["subject"]["expected_postconditions_sha256"] = canonical_digest(
        write_set["subject"]["expected_postconditions"]
    )
    authority["activation_authority_subject_sha256"] = canonical_digest(
        authority["subject"]
    )
    assert write_set["subject"]["artifacts"][0]["payload"] == candidate


def test_v2_execution_gate_uses_fresh_transaction_read_only_database_state() -> None:
    assert DATABASE_URL is not None
    candidate, write_set, authority = _package()
    with _connect(DATABASE_URL, autocommit=False) as conn:
        _prepare_post_m12n_baseline(conn)
        before_counts = _counts(conn)
        before_fingerprint = _state_fingerprint(conn)
        before_registry = _registry_rows(conn)
        _bind_observed_baseline(
            candidate,
            write_set,
            authority,
            counts=before_counts,
            fingerprint=before_fingerprint,
            registry_rows=before_registry,
        )

        conn.commit()
        with pytest.raises(ReadOnlySqlTransaction):
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                assert (
                    conn.execute("SHOW transaction_read_only").fetchone()[
                        "transaction_read_only"
                    ]
                    == "on"
                )
                observed_counts = _counts(conn)
                observed_fingerprint = _state_fingerprint(conn)
                observed_registry = _registry_rows(conn)
                assert observed_counts == before_counts
                assert observed_fingerprint == before_fingerprint
                assert observed_registry == before_registry
                assert (
                    conn.execute(
                        """SELECT COUNT(*) FROM editorial_publication_registry
                       WHERE member_bioguide_id = %s AND issue_id = %s""",
                        ("F000477", "SYNTHETIC_CONTRACT_TEST"),
                    ).fetchone()["count"]
                    == 0
                )
                assert (
                    conn.execute(
                        """SELECT COUNT(*) FROM editorial_artifacts
                       WHERE natural_key = %s""",
                        (
                            "test-site-integration-candidate:"
                            "f000477:synthetic_contract:119:v1",
                        ),
                    ).fetchone()["count"]
                    == 0
                )
                conn.execute(
                    """INSERT INTO editorial_artifact_batches
                       (deterministic_batch_key, source_commit_sha,
                        manifest_sha256, status, artifact_count,
                        relationship_count)
                       VALUES (%s, %s, %s, 'applied', 0, 0)""",
                    ("v2-write-must-fail", "0" * 40, "0" * 64),
                )

        fresh_preflight = _preflight("2026-08-26T01:59:00Z")
        baseline = authority["subject"]["stable_production_baseline"]
        fresh_preflight["counts"] = baseline["counts"]
        fresh_preflight["state_fingerprint_sha256"] = baseline[
            "state_fingerprint_sha256"
        ]
        fresh_preflight["existing_registry_identities"] = baseline[
            "existing_registry_identities"
        ]
        fresh_preflight["preflight_subject_sha256"] = canonical_digest(
            {
                key: value
                for key, value in fresh_preflight.items()
                if key != "preflight_subject_sha256"
            }
        )
        result = validate_execution_v2(
            authority=authority,
            candidate=candidate,
            write_set=write_set,
            runtime_proof=_runtime_proof("2026-08-26T01:59:00Z"),
            production_preflight=fresh_preflight,
            now=NOW,
        )
        assert result["status"] == "VALID_FOR_EXECUTION"
        assert _counts(conn) == before_counts
        assert _state_fingerprint(conn) == before_fingerprint
        assert _registry_rows(conn) == before_registry
