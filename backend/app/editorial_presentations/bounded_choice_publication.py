"""Dormant initial publication for the two exact bounded Health subjects.

No command, environment flag or startup hook executes this module. A caller must
supply accepted content/rendering evidence AND separate positive V2 activation
authority. Tests use only an explicitly named ephemeral loopback database.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone

from psycopg.types.json import Jsonb

from . import bounded_choice_review as review
from .compiler import canonical_digest
from .publication_activation_governance_v2 import (
    ACTIVATION_WRITE_SET_SCHEMA_VERSION_V2,
    PREFLIGHT_EVIDENCE_SCHEMA_VERSION_V2,
    validate_execution_v2,
    stable_write_set_subject_sha256,
)

TABLES = {
    "batches": "editorial_artifact_batches",
    "artifacts": "editorial_artifact_versions",
    "relationships": "editorial_artifact_relationships",
    "publication_registry": "editorial_publication_registry",
    "owner_decisions": "editorial_bounded_choice_owner_decisions",
}
CAPS = {
    "insert_batches": 1,
    "insert_artifacts": 4,
    "insert_relationships": 3,
    "insert_registry_rows": 1,
    "updates": 0,
    "deletes": 0,
    "unauthorized_table_writes": 0,
}


def require_owned_test_connection(conn) -> None:
    """Check the actual connection, never a caller's claimed environment label."""
    review.require(
        conn.info.host in {"127.0.0.1", "::1", "localhost"}
        and conn.info.dbname == "pf_health_choice_test",
        "synthetic writes require the owned loopback test database",
    )
    actual = conn.execute(
        "SELECT current_database() AS name, rolsuper FROM pg_roles WHERE rolname=session_user"
    ).fetchone()
    review.require(
        actual["name"] == "pf_health_choice_test" and actual["rolsuper"] is True,
        "synthetic writes require the owned test database superuser",
    )


def select_bounded_publication(row: dict, *, member_id: str, scope: str) -> dict | None:
    if scope not in {"all", "119"} or member_id not in review.MEMBERS:
        return None
    try:
        review.require(
            row["publication_basis"] == "bounded_choice_review"
            and row["member_bioguide_id"] == member_id
            and row["issue_id"] == review.ISSUE
            and row["publicly_active"] is True
            and row["deactivated_at"] is None
            and row["editorial_status"] == "human_approved"
            and row["benchmark_status"] == "not_promoted"
            and row["production_eligible"] is True,
            "bounded row is inactive or ineligible",
        )
        value = row["payload_jsonb"]
        validate_candidate(value)
        review.require(
            value["semantic"]["member_id"] == member_id
            and row["schema_version"] == value["schema_version"]
            and row["artifact_version"] == 1
            and row["natural_key"] == value["artifact_id"]
            and row["content_sha256"] == canonical_digest(value),
            "bounded stored identity differs",
        )
        metadata = row["publication_metadata_jsonb"]
        review.require(
            metadata["publication_basis"] == "bounded_choice_review"
            and metadata["presentation_natural_key"] == value["artifact_id"]
            and metadata["presentation_artifact_version"] == 1
            and metadata["active_artifact_sha256"] == row["content_sha256"],
            "bounded registry identity differs",
        )
        review.require(
            isinstance(metadata.get("activation_authority_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", metadata["activation_authority_sha256"]),
            "bounded activation evidence identity is missing",
        )
    except (KeyError, TypeError, ValueError, OSError):
        return None
    return {
        "issue_id": review.ISSUE,
        "requested_scope": scope,
        "tier": "bounded_choice_review",
        "presentation_branch": "bounded_choice_review",
        "bounded_choice": copy.deepcopy(value["presentation"]),
        "conclusion": None,
        "teaser": None,
        "repeated_patterns": [],
        "policy_trajectories": [],
        "notable_choices": [],
        "policy_episodes": [],
        "review_state": {
            "review_scope": "bounded_partial_record",
            "review_completion_state": "in_progress",
            "public_claim_class": "vote_record_only",
            "congress_scope": [119],
            "total_recorded_actions": 1,
            "complete_episode_count": 1,
            "full_issue_synthesis_eligible": False,
            "benchmark_sample_available": False,
            "conclusion_teaser": None,
        },
        "evidence_metadata": {
            "display_action_ids": [review.ACTION] if member_id == "F000477" else []
        },
    }


def candidate(
    subject: dict,
    presentation: dict,
    rendering: dict,
    receipt: dict,
    *,
    allow_test_authority: bool = False,
) -> dict:
    from .bounded_choice_pair import validate_pair_subject

    value = {
        "schema_version": "bounded_choice_publication_v1",
        "artifact_id": presentation["artifact_id"],
        "semantic": subject,
        "presentation": presentation,
        "rendering": rendering,
        "acceptance": receipt,
        "decision_subject": validate_pair_subject(),
        "blocking_findings": 0,
    }
    validate_candidate(value, allow_test_authority=allow_test_authority)
    return value


def validate_candidate(value: dict, *, allow_test_authority: bool = False) -> None:
    review.require(isinstance(value, dict), "bounded publication must be an object")
    review.require(
        set(value)
        == {
            "schema_version",
            "artifact_id",
            "semantic",
            "presentation",
            "rendering",
            "acceptance",
            "decision_subject",
            "blocking_findings",
        }
        and value["schema_version"] == "bounded_choice_publication_v1"
        and value["artifact_id"] == value["presentation"]["artifact_id"]
        and type(value["blocking_findings"]) is int
        and value["blocking_findings"] == 0,
        "bounded publication envelope differs",
    )
    review.validate_receipt(
        value["acceptance"],
        subject=value["semantic"],
        presentation=value["presentation"],
        rendering=value["rendering"],
        allow_test_authority=allow_test_authority,
    )
    review.source_evidence()
    from .bounded_choice_pair import validate_pair_subject

    review.require(
        canonical_digest(value["decision_subject"])
        == canonical_digest(validate_pair_subject()),
        "publication pair binding differs",
    )


def graph(
    value: dict, *, allow_test_authority: bool = False
) -> tuple[list[dict], list[dict]]:
    validate_candidate(value, allow_test_authority=allow_test_authority)
    key = value["artifact_id"]
    sources = {
        "schema_version": "bounded_choice_sources_v1",
        "member_id": value["semantic"]["member_id"],
        "complete_required_sources": True,
        "normalized_source_sha256": review.FOUNDATION["governed_sources.json"],
        "additional_raw_evidence": review.source_evidence(),
    }
    validation = {
        "schema_version": "bounded_choice_validation_v1",
        "member_id": sources["member_id"],
        "successful": True,
        "current": True,
        "blocking_findings": 0,
        "candidate_sha256": canonical_digest(value),
        "runtime_manifest_sha256": canonical_digest(review.rendering_manifest()),
    }
    items = [
        (key + ":receipt", "reference_fixture_metadata", value["acceptance"]),
        (key + ":sources", "source_manifest", sources),
        (key + ":validation", "standardization_validation_result", validation),
        (key, "issue_public_presentation", value),
    ]
    artifacts = [
        {
            "natural_key": k,
            "artifact_type": kind,
            "payload": payload,
            "content_sha256": canonical_digest(payload),
        }
        for k, kind, payload in items
    ]
    relationships = [
        {"parent": key, "child": key + suffix, "type": kind}
        for suffix, kind in [
            (":receipt", "has_reference_metadata"),
            (":sources", "uses_source_manifest"),
            (":validation", "has_validation"),
        ]
    ]
    return artifacts, relationships


def target(value: dict) -> dict:
    return {
        "member_bioguide_id": value["semantic"]["member_id"],
        "issue_id": review.ISSUE,
        "presentation_natural_key": value["artifact_id"],
        "presentation_artifact_version": 1,
    }


def binding(value: dict, subject_hash: str) -> dict:
    return {
        "artifact_id": value["artifact_id"],
        "subject_sha256": subject_hash,
        "file_sha256": canonical_digest(value),
        "content_sha256": canonical_digest(value),
    }


def observe_baseline(conn, value: dict) -> dict:
    """Observe real state; callers acquire READ ONLY before the first query."""
    snapshots = {
        name: conn.execute(f"SELECT * FROM public.{table} ORDER BY 1, 2").fetchall()
        for name, table in TABLES.items()
    }
    counts = {name: len(rows) for name, rows in snapshots.items()}
    serialized = json.loads(json.dumps(snapshots, default=str))
    identity = conn.execute(
        "SELECT current_database() AS database, inet_server_addr()::text AS host, inet_server_port() AS port"
    ).fetchone()
    identities = conn.execute(
        """SELECT r.*, a.natural_key, a.artifact_version, a.content_sha256, a.source_commit_sha FROM public.editorial_publication_registry r JOIN public.editorial_artifact_versions a USING (artifact_id) ORDER BY r.member_bioguide_id, r.issue_id"""
    ).fetchall()
    registry = [
        {
            "member_bioguide_id": r["member_bioguide_id"],
            "issue_id": r["issue_id"],
            "artifact_id": r["artifact_id"],
            "artifact_version": r["artifact_version"],
            "presentation_natural_key": r["natural_key"],
            "content_sha256": r["content_sha256"],
            "source_commit_sha": r["source_commit_sha"],
            "publication_metadata_sha256": canonical_digest(
                r["publication_metadata_jsonb"]
            ),
            "publicly_active": r["publicly_active"],
        }
        for r in identities
    ]
    keys = sorted(
        value["artifact_id"] + suffix
        for suffix in ["", ":receipt", ":sources", ":validation"]
    )
    found = [
        r["natural_key"] for r in snapshots["artifacts"] if r["natural_key"] in keys
    ]
    occupied = [
        r
        for r in snapshots["publication_registry"]
        if r["member_bioguide_id"] == value["semantic"]["member_id"]
        and r["issue_id"] == review.ISSUE
    ]
    return {
        "production_target_identity_sha256": canonical_digest(identity),
        "state_fingerprint_sha256": canonical_digest(serialized),
        "counts": counts,
        "existing_registry_identities": registry,
        "target_registry_identity": target(value),
        "target_artifact_natural_keys": keys,
        "state_predicates": {
            "existing_publication_rows_unchanged": True,
            "target_registry_row_absent": not occupied,
            "target_artifacts_absent": not found,
        },
        "write_preconditions": {
            "artifact_natural_keys_available": not found,
            "registry_primary_key_available": not occupied,
            "relationship_graph_insertable": True,
        },
    }


def build_write_set(
    value: dict,
    *,
    preparation: dict,
    runtime: dict,
    baseline: dict,
    allow_test_authority: bool = False,
) -> dict:
    """Accepted subjects only. Stable baseline is distinct for EACH member."""
    artifacts, relationships = graph(value, allow_test_authority=allow_test_authority)
    review.require(
        runtime["reviewed_runtime_manifest_sha256"]
        == canonical_digest(review.rendering_manifest()),
        "runtime manifest differs from reviewed rendering",
    )
    after = copy.deepcopy(baseline["counts"])
    for key, count in [
        ("batches", 1),
        ("artifacts", 4),
        ("relationships", 3),
        ("publication_registry", 1),
    ]:
        after[key] += count
    subject = {
        "accepted_site_integration_binding": binding(
            value, value["presentation"]["presentation_subject_sha256"]
        ),
        "preparation_authority_binding": preparation,
        "stable_runtime_binding": runtime,
        "stable_production_baseline_binding_sha256": canonical_digest(baseline),
        "production_target_identity_sha256": baseline[
            "production_target_identity_sha256"
        ],
        "artifacts": artifacts,
        "relationships": relationships,
        "publication_registry_target": target(value),
        "mutation_caps": CAPS,
        "rollback_contract": {
            "owned_artifact_natural_keys": sorted(a["natural_key"] for a in artifacts),
            "restore_counts": baseline["counts"],
            "restore_state_fingerprint_sha256": baseline["state_fingerprint_sha256"],
        },
        "expected_postconditions": {
            "counts": after,
            "existing_domain_isolation": True,
            "selector": {"119": "bounded_choice_review", "118": "receipts_only"},
        },
    }
    result = {
        "schema_version": ACTIVATION_WRITE_SET_SCHEMA_VERSION_V2,
        "artifact_id": value["artifact_id"] + ":initial-write-v2",
        "immutable": True,
        "subject": copy.deepcopy(subject),
        "write_set_subject_sha256": canonical_digest(subject),
    }
    stable_write_set_subject_sha256(result)
    return result


def capture_preflight(conn, value: dict) -> dict:
    review.require(
        conn.info.transaction_status == 0, "preflight requires an idle connection"
    )
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        current = observe_baseline(conn, value)
        readonly = (
            conn.execute("SHOW transaction_read_only").fetchone()[
                "transaction_read_only"
            ]
            == "on"
        )
    proof = {
        "schema_version": PREFLIGHT_EVIDENCE_SCHEMA_VERSION_V2,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "transaction_read_only": readonly,
        **{
            k: current[k]
            for k in [
                "production_target_identity_sha256",
                "state_fingerprint_sha256",
                "counts",
                "existing_registry_identities",
                "target_registry_identity",
                "state_predicates",
                "write_preconditions",
            ]
        },
        "target_registry_rows": []
        if current["state_predicates"]["target_registry_row_absent"]
        else ["occupied"],
        "target_artifact_natural_keys_checked": current["target_artifact_natural_keys"],
        "target_artifact_natural_keys_found": []
        if current["state_predicates"]["target_artifacts_absent"]
        else ["occupied"],
    }
    return review.seal(proof, "preflight_subject_sha256")


def apply_initial(
    conn,
    *,
    value: dict,
    write_set: dict,
    authority: dict,
    runtime_proof: dict,
    fault_after: str | None = None,
    allow_test_authority: bool = False,
) -> dict:
    """Initial insert only. Separate V2 authority, fresh actual DB checks and caps.

    A failing member transaction rolls back its entire write set. A previous
    member's successful transaction remains independently identifiable/rollbackable.
    """
    if allow_test_authority:
        require_owned_test_connection(conn)
    artifacts, relationships = graph(value, allow_test_authority=allow_test_authority)
    subject = write_set["subject"]
    review.require(
        subject["artifacts"] == artifacts
        and subject["relationships"] == relationships
        and subject["mutation_caps"] == CAPS
        and subject["publication_registry_target"] == target(value),
        "initial write graph or caps differ",
    )
    a = authority["subject"]
    review.require(
        a["member_bioguide_id"] == value["semantic"]["member_id"]
        and a["issue_id"] == review.ISSUE
        and a["congress"] == 119
        and a["semantic_authority_lineage"]
        == [
            binding(value["acceptance"], value["acceptance"]["receipt_subject_sha256"])
        ],
        "V2 activation does not bind the accepted bounded subject",
    )
    review.require(
        write_set
        == build_write_set(
            value,
            preparation=a["preparation_authority_binding"],
            runtime=a["stable_runtime_binding"],
            baseline=a["stable_production_baseline"],
            allow_test_authority=allow_test_authority,
        ),
        "initial write set differs from the exact deterministic plan",
    )
    review.require(
        fault_after in {None, "artifacts", "relationships", "registry"},
        "unknown fault boundary",
    )
    preflight = capture_preflight(conn, value)
    validate_execution_v2(
        authority=authority,
        candidate=value,
        write_set=write_set,
        runtime_proof=runtime_proof,
        production_preflight=preflight,
    )
    batch_key = "bounded-choice-initial:" + write_set["write_set_subject_sha256"]
    with conn.transaction():
        if allow_test_authority:
            conn.execute("SET LOCAL app.bounded_choice_synthetic_test = 'on'")
        # Prevent a race after the read-only observation. This also serializes
        # independent member initial writes; the second needs a fresh baseline.
        conn.execute(
            "LOCK TABLE public.editorial_artifact_batches, public.editorial_artifact_versions, public.editorial_artifact_relationships, public.editorial_publication_registry, public.editorial_bounded_choice_owner_decisions IN SHARE ROW EXCLUSIVE MODE"
        )
        observed = observe_baseline(conn, value)
        review.require(
            observed == a["stable_production_baseline"],
            "baseline changed before initial mutation",
        )
        batch_id = conn.execute(
            """INSERT INTO public.editorial_artifact_batches (deterministic_batch_key, source_commit_sha, manifest_sha256, status, artifact_count, relationship_count, applied_at) VALUES (%s,%s,%s,'applied',4,3,NOW()) RETURNING batch_id""",
            (
                batch_key,
                a["stable_runtime_binding"]["reviewed_source_commit"],
                write_set["write_set_subject_sha256"],
            ),
        ).fetchone()["batch_id"]
        ids = {}
        for artifact in artifacts:
            root = artifact["artifact_type"] == "issue_public_presentation"
            ids[artifact["natural_key"]] = conn.execute(
                """INSERT INTO public.editorial_artifact_versions (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_manifest_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,congress,chamber,canonical_action_id,episode_id,editorial_status,benchmark_status,production_eligible,review_route,publication_basis,bounded_acceptance_artifact_id) VALUES (%s,%s,%s,1,%s,%s,%s,%s,%s,%s,%s,119,'house',%s,%s,'human_approved','not_promoted',%s,'human_exception',%s,%s) RETURNING artifact_id""",
                (
                    artifact["artifact_type"],
                    artifact["natural_key"],
                    artifact["payload"]["schema_version"],
                    Jsonb(artifact["payload"]),
                    artifact["content_sha256"],
                    review.FOUNDATION["governed_sources.json"],
                    a["stable_runtime_binding"]["reviewed_source_commit"],
                    batch_id,
                    value["semantic"]["member_id"],
                    review.ISSUE,
                    review.ACTION,
                    review.EPISODE,
                    root,
                    "bounded_choice_review" if root else "legacy_gold",
                    ids.get(value["artifact_id"] + ":receipt") if root else None,
                ),
            ).fetchone()["artifact_id"]
        if fault_after == "artifacts":
            raise RuntimeError("injected failure after artifacts")
        for rel in relationships:
            conn.execute(
                "INSERT INTO public.editorial_artifact_relationships (parent_artifact_id,child_artifact_id,relationship_type) VALUES (%s,%s,%s)",
                (ids[rel["parent"]], ids[rel["child"]], rel["type"]),
            )
        if fault_after == "relationships":
            raise RuntimeError("injected failure after relationships")
        conn.execute(
            """INSERT INTO public.editorial_publication_registry (member_bioguide_id,issue_id,artifact_id,publicly_active,activated_at,publication_metadata_jsonb) VALUES (%s,%s,%s,TRUE,NOW(),%s)""",
            (
                value["semantic"]["member_id"],
                review.ISSUE,
                ids[value["artifact_id"]],
                Jsonb(
                    {
                        "publication_basis": "bounded_choice_review",
                        "presentation_natural_key": value["artifact_id"],
                        "presentation_artifact_version": 1,
                        "active_artifact_sha256": canonical_digest(value),
                        "activation_authority_sha256": authority[
                            "activation_authority_subject_sha256"
                        ],
                    }
                ),
            ),
        )
        if fault_after == "registry":
            raise RuntimeError("injected failure after registry")
        after = observe_baseline(conn, value)
        review.require(
            after["counts"] == subject["expected_postconditions"]["counts"]
            and after["existing_registry_identities"]
            == sorted(
                a["stable_production_baseline"]["existing_registry_identities"]
                + [
                    r
                    for r in after["existing_registry_identities"]
                    if r["member_bioguide_id"] == value["semantic"]["member_id"]
                    and r["issue_id"] == review.ISSUE
                ],
                key=lambda r: (r["member_bioguide_id"], r["issue_id"]),
            ),
            "initial publication postconditions differ",
        )
    return {
        "batch_key": batch_key,
        "artifact_ids": ids,
        "counts": after["counts"],
        "state_fingerprint_sha256": after["state_fingerprint_sha256"],
    }


def rollback_initial(conn, *, value: dict, write_set: dict, execution: dict) -> None:
    """Exact owned batch only; transaction fails if any baseline cannot restore."""
    review.require(
        conn.info.transaction_status == 0, "rollback requires an idle connection"
    )
    expected = "bounded-choice-initial:" + write_set["write_set_subject_sha256"]
    review.require(execution["batch_key"] == expected, "rollback batch differs")
    with conn.transaction():
        conn.execute(
            "LOCK TABLE public.editorial_artifact_batches, public.editorial_artifact_versions, public.editorial_artifact_relationships, public.editorial_publication_registry IN SHARE ROW EXCLUSIVE MODE"
        )
        current = observe_baseline(conn, value)
        review.require(
            current["state_fingerprint_sha256"]
            == execution["state_fingerprint_sha256"],
            "rollback current state differs; reverse later member writes first",
        )
        batch = conn.execute(
            "SELECT batch_id FROM public.editorial_artifact_batches WHERE deterministic_batch_key=%s",
            (expected,),
        ).fetchone()
        review.require(batch is not None, "rollback batch is absent")
        owned = conn.execute(
            "SELECT artifact_id,natural_key FROM public.editorial_artifact_versions WHERE batch_id=%s",
            (batch["batch_id"],),
        ).fetchall()
        review.require(
            {r["natural_key"]: r["artifact_id"] for r in owned}
            == execution["artifact_ids"],
            "rollback owned set differs",
        )
        root = execution["artifact_ids"][value["artifact_id"]]
        deleted = conn.execute(
            "DELETE FROM public.editorial_publication_registry WHERE artifact_id=%s AND member_bioguide_id=%s AND issue_id=%s RETURNING artifact_id",
            (root, value["semantic"]["member_id"], review.ISSUE),
        ).fetchall()
        review.require(len(deleted) == 1, "rollback registry differs")
        edges = conn.execute(
            "DELETE FROM public.editorial_artifact_relationships WHERE parent_artifact_id=%s RETURNING child_artifact_id",
            (root,),
        ).fetchall()
        review.require(len(edges) == 3, "rollback relationship count differs")
        conn.execute(
            "SELECT set_config('app.editorial_artifact_rollback_batch',%s,TRUE)",
            (expected,),
        )
        conn.execute(
            "DELETE FROM public.editorial_artifact_versions WHERE artifact_id=%s",
            (root,),
        )
        conn.execute(
            "DELETE FROM public.editorial_artifact_versions WHERE batch_id=%s",
            (batch["batch_id"],),
        )
        conn.execute(
            "DELETE FROM public.editorial_artifact_batches WHERE batch_id=%s",
            (batch["batch_id"],),
        )
        restored = observe_baseline(conn, value)
        contract = write_set["subject"]["rollback_contract"]
        review.require(
            restored["counts"] == contract["restore_counts"]
            and restored["state_fingerprint_sha256"]
            == contract["restore_state_fingerprint_sha256"],
            "rollback did not restore the exact baseline",
        )
