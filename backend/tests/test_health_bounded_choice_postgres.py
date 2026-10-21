"""Actual staged migration and writes ONLY in a dedicated loopback test DB."""

from __future__ import annotations

import copy
import os
from datetime import datetime, timezone

import psycopg
import pytest
from psycopg.rows import dict_row

from app.editorial_presentations import bounded_choice_publication as p
from app.editorial_presentations import bounded_choice_review as r
from app.editorial_presentations.publication_activation_governance_v2 import (
    POSITIVE_AUTHORIZATIONS_V2,
)
from app.editorial_artifacts.repository import EditorialArtifactRepository
from scripts.disposable_database_url import require_exact_loopback_postgres_url
from test_health_bounded_choice import synthetic_candidate
from health_choice_registered_fixture import registered_fixture

DSN = os.getenv("HEALTH_CHOICE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="explicit HEALTH_CHOICE_TEST_DATABASE_URL required"
)
STAGED = (
    r.ROOT
    / "backend/migrations/staged/20261019231216_bounded_health_choice_publication.sql"
)


@pytest.fixture
def db():
    url = require_exact_loopback_postgres_url(DSN)
    conn = psycopg.connect(url, autocommit=True, row_factory=dict_row)
    assert (
        conn.execute("SELECT current_database() AS name").fetchone()["name"]
        == "pf_health_choice_test"
    ), "refuse to reset any other database"
    conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
    for role in ["anon", "authenticated"]:
        conn.execute(
            f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{role}') THEN CREATE ROLE {role} NOLOGIN; END IF; END $$"
        )
    for migration in sorted((r.ROOT / "backend/migrations").glob("*.sql")):
        conn.execute(migration.read_text(encoding="utf-8"))
    for member, name in [("F000477", "Valerie Foushee"), ("M001184", "Thomas Massie")]:
        conn.execute(
            "INSERT INTO legislators (bioguide_id,name_display,chamber,state,district,party) VALUES (%s,%s,'house','NC','4','I')",
            (member, name),
        )
    assert EditorialArtifactRepository(conn).bounded_choice_publication_selector() == []
    conn.execute(STAGED.read_text(encoding="utf-8"))
    yield conn
    conn.close()


def activation(conn, member="F000477", *, value=None):
    mode = {"allow_test_authority": True} if value is None else {}
    value = synthetic_candidate(member) if value is None else value
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        baseline = p.observe_baseline(conn, value)
    now = datetime.now(timezone.utc).isoformat()
    runtime = {
        "reviewed_runtime_manifest_sha256": p.canonical_digest(r.rendering_manifest()),
        "reviewed_source_commit": r.BASE,
    }
    preparation = {
        "artifact_id": "SYNTHETIC-TEST-preparation",
        "authority_subject_sha256": "a" * 64,
        "decision_recorded_at_utc": "2026-10-19T00:00:00Z",
    }
    writes = p.build_write_set(
        value,
        preparation=preparation,
        runtime=runtime,
        baseline=baseline,
        **mode,
    )
    subject = {
        "decision": "approve_exact_publication_activation_v2",
        "decision_recorded_at_utc": now,
        "reviewer": "SYNTHETIC TEST ONLY",
        "reviewer_authority": "publication_activation_review_authority_v2",
        "member_bioguide_id": member,
        "issue_id": r.ISSUE,
        "congress": 119,
        "accepted_site_integration_binding": writes["subject"][
            "accepted_site_integration_binding"
        ],
        "semantic_authority_lineage": [
            p.binding(
                value["acceptance"], value["acceptance"]["receipt_subject_sha256"]
            )
        ],
        "preparation_authority_binding": preparation,
        "stable_runtime_binding": runtime,
        "stable_production_baseline": baseline,
        "exact_write_set_subject_sha256": writes["write_set_subject_sha256"],
        "publication_registry_target": p.target(value),
        "rollback_contract_sha256": p.canonical_digest(
            writes["subject"]["rollback_contract"]
        ),
        "expected_postconditions_sha256": p.canonical_digest(
            writes["subject"]["expected_postconditions"]
        ),
        "authorizations": POSITIVE_AUTHORIZATIONS_V2,
    }
    authority = {
        "schema_version": "site_integration_publication_activation_authority_v2",
        "artifact_id": "SYNTHETIC-TEST-activation",
        "immutable": True,
        "sealed": True,
        "accepted": True,
        "subject": subject,
        "activation_authority_subject_sha256": p.canonical_digest(subject),
    }
    proof = r.seal(
        {
            "schema_version": "publication_activation_runtime_execution_evidence_v2",
            "captured_at_utc": now,
            "healthy": True,
            "deployed_commit": r.BASE,
            "health_commit": r.BASE,
            "current_runtime_manifest_sha256": runtime[
                "reviewed_runtime_manifest_sha256"
            ],
        },
        "runtime_health_proof_subject_sha256",
    )
    return dict(
        value=value,
        write_set=writes,
        authority=authority,
        runtime_proof=proof,
        **mode,
    )


def seed_legacy_gold(conn):
    """An actual 0016 gold graph remains eligible under the staged migration."""
    from psycopg.types.json import Jsonb

    batch = conn.execute(
        "INSERT INTO editorial_artifact_batches (deterministic_batch_key,source_commit_sha,manifest_sha256,status,artifact_count,relationship_count) VALUES ('SYNTHETIC-legacy',%s,%s,'applied',3,2) RETURNING batch_id",
        (r.BASE, "a" * 64),
    ).fetchone()["batch_id"]
    ids = []
    hashes = []
    for key, kind, payload in [
        ("legacy-root", "issue_public_presentation", {"blocking_findings": 0}),
        (
            "legacy-validation",
            "standardization_validation_result",
            {"successful": True, "current": True, "blocking_findings": 0},
        ),
        ("legacy-sources", "source_manifest", {"complete_required_sources": True}),
    ]:
        digest = p.canonical_digest(payload)
        ids.append(
            conn.execute(
                "INSERT INTO editorial_artifact_versions (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,editorial_status,benchmark_status,production_eligible,review_route) VALUES (%s,%s,'SYNTHETIC-legacy',1,%s,%s,%s,%s,'F000477','SYNTHETIC_LEGACY_TEST','human_approved',%s,%s,'human_exception') RETURNING artifact_id",
                (
                    kind,
                    key,
                    Jsonb(payload),
                    digest,
                    r.BASE,
                    batch,
                    "gold_benchmark" if len(ids) == 0 else "not_promoted",
                    len(ids) == 0,
                ),
            ).fetchone()["artifact_id"]
        )
        hashes.append(digest)
    for child, kind in [(ids[1], "has_validation"), (ids[2], "uses_source_manifest")]:
        conn.execute(
            "INSERT INTO editorial_artifact_relationships (parent_artifact_id,child_artifact_id,relationship_type) VALUES (%s,%s,%s)",
            (ids[0], child, kind),
        )
    metadata = {
        "presentation_natural_key": "legacy-root",
        "presentation_artifact_version": 1,
        "active_artifact_sha256": hashes[0],
        "validation_natural_key": "legacy-validation",
        "validation_artifact_version": 1,
        "validation_content_sha256": hashes[1],
        "source_manifest_natural_key": "legacy-sources",
        "source_manifest_artifact_version": 1,
        "source_manifest_content_sha256": hashes[2],
        "relationship_metadata": {},
    }
    conn.execute(
        "INSERT INTO editorial_publication_registry (member_bioguide_id,issue_id,artifact_id,publicly_active,activated_at,publication_metadata_jsonb) VALUES ('F000477','SYNTHETIC_LEGACY_TEST',%s,TRUE,NOW(),%s)",
        (ids[0], Jsonb(metadata)),
    )
    with pytest.raises(psycopg.Error, match="append-only"):
        conn.execute(
            "UPDATE editorial_artifact_versions SET benchmark_status='not_promoted' WHERE artifact_id=%s",
            (ids[0],),
        )
    return EditorialArtifactRepository(conn).publication_selector()


def test_initial_two_member_apply_selector_replay_and_exact_reverse_rollback(db):
    legacy_before = seed_legacy_gold(db)
    assert len(legacy_before) == 1
    first = activation(db)
    before = first["authority"]["subject"]["stable_production_baseline"]
    assert p.capture_preflight(db, first["value"])["transaction_read_only"] is True
    stale_second = activation(db, "M001184")
    result1 = p.apply_initial(db, **first)
    assert (
        len(EditorialArtifactRepository(db).bounded_choice_publication_selector()) == 0
    )
    with pytest.raises(ValueError):
        p.apply_initial(db, **first)  # exact replay writes nothing
    with pytest.raises(ValueError):
        p.apply_initial(db, **stale_second)
    second = activation(db, "M001184")
    result2 = p.apply_initial(db, **second)
    rows = EditorialArtifactRepository(db).bounded_choice_publication_selector()
    # Explicit synthetic graph exercises mutation/rollback, never public serving.
    assert rows == []
    assert (
        db.execute(
            "SELECT count(*) AS n FROM editorial_publication_registry WHERE issue_id='HEALTH_SOCIAL'"
        ).fetchone()["n"]
        == 2
    )
    with db.transaction():
        db.execute("SET LOCAL app.bounded_choice_synthetic_test = 'on'")
        assert (
            EditorialArtifactRepository(db).bounded_choice_publication_selector() == []
        )
    assert EditorialArtifactRepository(db).publication_selector() == legacy_before
    with pytest.raises(ValueError):
        p.rollback_initial(
            db, value=first["value"], write_set=first["write_set"], execution=result1
        )
    p.rollback_initial(
        db, value=second["value"], write_set=second["write_set"], execution=result2
    )
    p.rollback_initial(
        db, value=first["value"], write_set=first["write_set"], execution=result1
    )
    assert p.observe_baseline(db, first["value"]) == before


def test_schema_rollback_preserves_legacy_and_requires_bounded_data_rollback(db):
    legacy = seed_legacy_gold(db)
    rollback = (
        r.ROOT
        / "docs/editorial/review_packages/health_bounded_choice_v1/staged-migration-rollback.sql"
    ).read_text()
    args = activation(db)
    execution = p.apply_initial(db, **args)
    with pytest.raises(psycopg.Error, match="roll back all bounded data"):
        try:
            db.execute(rollback)
        finally:
            db.execute("ROLLBACK")
    p.rollback_initial(
        db, value=args["value"], write_set=args["write_set"], execution=execution
    )
    db.execute(rollback)
    assert EditorialArtifactRepository(db).bounded_choice_publication_selector() == []
    assert EditorialArtifactRepository(db).publication_selector() == legacy
    db.execute(STAGED.read_text())
    assert EditorialArtifactRepository(db).publication_selector() == legacy


@pytest.mark.parametrize(
    "mutation",
    [
        lambda x: x["authority"]["subject"].update(member_bioguide_id="M001184"),
        lambda x: x["authority"]["subject"].update(semantic_authority_lineage=[]),
        lambda x: x["write_set"]["subject"]["mutation_caps"].update(insert_artifacts=5),
        lambda x: x["runtime_proof"].update(captured_at_utc="2020-01-01T00:00:00Z"),
        lambda x: x["runtime_proof"].update(current_runtime_manifest_sha256="0" * 64),
    ],
)
def test_authority_cap_and_runtime_adversaries_write_nothing(db, mutation):
    args = activation(db)
    before = p.observe_baseline(db, args["value"])
    mutation(args)
    args["runtime_proof"] = r.seal(
        args["runtime_proof"], "runtime_health_proof_subject_sha256"
    )
    with pytest.raises(ValueError):
        p.apply_initial(db, **args)
    assert p.observe_baseline(db, args["value"]) == before


@pytest.mark.parametrize("fault", ["artifacts", "relationships", "registry"])
def test_faults_restore_exact_baseline_and_allow_safe_retry(db, fault):
    args = activation(db)
    with pytest.raises(RuntimeError, match="injected"):
        p.apply_initial(db, **args, fault_after=fault)
    assert (
        p.observe_baseline(db, args["value"])
        == args["authority"]["subject"]["stable_production_baseline"]
    )
    result = p.apply_initial(db, **args)
    p.rollback_initial(
        db, value=args["value"], write_set=args["write_set"], execution=result
    )


def test_partial_member_failure_preserves_first_then_retries_second(db):
    first = activation(db)
    result1 = p.apply_initial(db, **first)
    second = activation(db, "M001184")
    with pytest.raises(RuntimeError):
        p.apply_initial(db, **second, fault_after="registry")
    assert (
        len(EditorialArtifactRepository(db).bounded_choice_publication_selector()) == 0
    )
    result2 = p.apply_initial(db, **second)
    p.rollback_initial(
        db, value=second["value"], write_set=second["write_set"], execution=result2
    )
    p.rollback_initial(
        db, value=first["value"], write_set=first["write_set"], execution=result1
    )


def test_security_immutability_and_source_validation_guards(db):
    args = activation(db)
    result = p.apply_initial(db, **args)
    root = result["artifact_ids"][args["value"]["artifact_id"]]
    with pytest.raises(psycopg.Error, match="append-only"):
        db.execute(
            "UPDATE editorial_artifact_versions SET benchmark_status='gold_benchmark' WHERE artifact_id=%s",
            (root,),
        )
    with pytest.raises(psycopg.Error, match="exact rollback"):
        db.execute(
            "DELETE FROM editorial_artifact_versions WHERE artifact_id=%s", (root,)
        )
    for role in ["anon", "authenticated"]:
        for table in list(p.TABLES.values()) + [
            "editorial_bounded_choice_publications"
        ]:
            assert (
                db.execute(
                    "SELECT has_table_privilege(%s,%s,'SELECT,INSERT,UPDATE,DELETE') AS allowed",
                    (role, "public." + table),
                ).fetchone()["allowed"]
                is False
            )
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with db.transaction():
                db.execute(f"SET LOCAL ROLE {role}")
                db.execute("SELECT * FROM public.editorial_bounded_choice_publications")
        assert (
            db.execute(
                "SELECT has_function_privilege(%s,'public.bounded_choice_graph_valid(bigint)','EXECUTE') AS allowed",
                (role,),
            ).fetchone()["allowed"]
            is False
        )
    assert db.execute(
        "SELECT reloptions FROM pg_class WHERE oid='editorial_bounded_choice_publications'::regclass"
    ).fetchone()["reloptions"] == ["security_invoker=true"]
    assert (
        db.execute(
            "SELECT count(*) AS n FROM pg_class WHERE relname LIKE 'editorial_%' AND relkind='r' AND NOT relrowsecurity"
        ).fetchone()["n"]
        == 0
    )
    # Direct SQL cannot turn a pending/mismatched subject into an eligible root,
    # even when the writer supplies human_approved/production_eligible flags.
    forged = copy.deepcopy(args["value"])
    forged["acceptance"]["decision"] = None
    with pytest.raises(psycopg.Error, match="exact accepted subject"):
        db.execute(
            """INSERT INTO editorial_artifact_versions
          (artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_manifest_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,congress,chamber,canonical_action_id,episode_id,editorial_status,benchmark_status,production_eligible,review_route,publication_basis,bounded_acceptance_artifact_id)
          SELECT artifact_type,natural_key,schema_version,artifact_version,%s,%s,source_manifest_sha256,source_commit_sha,batch_id,member_bioguide_id,issue_id,congress,chamber,canonical_action_id,episode_id,editorial_status,benchmark_status,production_eligible,review_route,publication_basis,bounded_acceptance_artifact_id
          FROM editorial_artifact_versions WHERE artifact_id=%s""",
            (psycopg.types.json.Jsonb(forged), p.canonical_digest(forged), root),
        )
    # Relationships are not content authority: deleting one immediately hides the
    # candidate; reinserting a duplicate or wrong child cannot keep it visible.
    with db.transaction(force_rollback=True):
        db.execute(
            "DELETE FROM editorial_artifact_relationships WHERE parent_artifact_id=%s AND relationship_type='uses_source_manifest'",
            (root,),
        )
        assert (
            EditorialArtifactRepository(db).bounded_choice_publication_selector() == []
        )
        with pytest.raises(psycopg.Error, match="bounded activation"):
            with db.transaction():
                db.execute(
                    "UPDATE editorial_publication_registry SET activated_at=activated_at WHERE artifact_id=%s",
                    (root,),
                )
    p.rollback_initial(
        db, value=args["value"], write_set=args["write_set"], execution=result
    )


def test_database_rejects_pending_even_when_writer_forges_eligibility(db):
    args = activation(db)
    value = copy.deepcopy(args["value"])
    value["acceptance"]["decision"] = None
    assert (
        db.execute(
            "SELECT public.bounded_choice_receipt_matches(%s,%s) AS valid",
            (psycopg.types.json.Jsonb(value), "F000477"),
        ).fetchone()["valid"]
        is False
    )
    for mutation in [
        lambda x: x["semantic"].update(member_id="M001184"),
        lambda x: x["presentation"].update(display_role="primary"),
        lambda x: x["acceptance"].update(semantic_subject_sha256="0" * 64),
    ]:
        value = copy.deepcopy(args["value"])
        mutation(value)
        assert (
            db.execute(
                "SELECT public.bounded_choice_receipt_matches(%s,%s) AS valid",
                (psycopg.types.json.Jsonb(value), "F000477"),
            ).fetchone()["valid"]
            is False
        )


def test_synthetic_authority_requires_explicit_owned_test_context_and_never_serves(db):
    args = activation(db)
    before = p.observe_baseline(db, args["value"])
    ordinary = {k: v for k, v in args.items() if k != "allow_test_authority"}
    with pytest.raises(ValueError, match="owner decision"):
        p.apply_initial(db, **ordinary)
    assert p.observe_baseline(db, args["value"]) == before
    for evidence in [
        None,
        {},
        {
            "kind": "owner_decision",
            "decision_id": "invented",
            "decision_sha256": "a" * 64,
        },
    ]:
        forged = copy.deepcopy(args["value"])
        forged["acceptance"].update(
            authority_evidence=evidence, reviewer="Plausible owner"
        )
        forged["acceptance"] = r.seal(forged["acceptance"], "receipt_subject_sha256")
        for flag in ["on", "off"]:
            with db.transaction():
                db.execute(
                    "SELECT set_config('app.bounded_choice_synthetic_test',%s,TRUE)",
                    (flag,),
                )
                assert (
                    db.execute(
                        "SELECT bounded_choice_receipt_matches(%s,'F000477') AS valid",
                        (psycopg.types.json.Jsonb(forged),),
                    ).fetchone()["valid"]
                    is False
                )
    # The owned context is necessary even for otherwise-valid synthetic content.
    value = args["value"]
    assert (
        db.execute(
            "SELECT bounded_choice_receipt_matches(%s,'F000477') AS valid",
            (psycopg.types.json.Jsonb(value),),
        ).fetchone()["valid"]
        is False
    )
    with db.transaction():
        db.execute("SET LOCAL app.bounded_choice_synthetic_test = 'on'")
        assert (
            db.execute(
                "SELECT bounded_choice_receipt_matches(%s,'F000477') AS valid",
                (psycopg.types.json.Jsonb(value),),
            ).fetchone()["valid"]
            is True
        )
        assert (
            db.execute(
                "SELECT bounded_choice_owner_evidence_matches(%s,FALSE) AS valid",
                (psycopg.types.json.Jsonb(value["acceptance"]),),
            ).fetchone()["valid"]
            is False
        )
        for part, path, wrong in [
            (
                "semantic",
                ["accounting_review", "frontend_state", "total_recorded_actions"],
                True,
            ),
            ("presentation", ["congress"], 119.0),
        ]:
            mutated = copy.deepcopy(value)
            node = mutated[part]
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = wrong
            assert (
                db.execute(
                    "SELECT bounded_choice_receipt_matches(%s,'F000477') AS valid",
                    (psycopg.types.json.Jsonb(mutated),),
                ).fetchone()["valid"]
                is False
            )
    assert (
        db.execute(
            "SELECT count(*) AS n FROM editorial_bounded_choice_owner_decisions"
        ).fetchone()["n"]
        == 0
    )
    assert p.observe_baseline(db, value) == before


def test_synthetic_connection_guard_uses_actual_connection_identity():
    from types import SimpleNamespace

    for host, name in [
        ("production.example", "pf_health_choice_test"),
        ("127.0.0.1", "postgres"),
    ]:
        conn = SimpleNamespace(info=SimpleNamespace(host=host, dbname=name))
        with pytest.raises(ValueError, match="owned loopback"):
            p.require_owned_test_connection(conn)


def test_default_api_is_identical_without_a_bounded_activation(db, monkeypatch):
    from app.api import editorial_presentations as api
    from app.editorial_presentations.selector import select_public_presentations

    monkeypatch.setattr(
        api,
        "get_connection",
        lambda: psycopg.connect(DSN, autocommit=True, row_factory=dict_row),
    )
    monkeypatch.setattr(
        api, "get_legislator_profile", lambda **_: {"bioguide_id": "F000477"}
    )
    expected = select_public_presentations(
        EditorialArtifactRepository(db).publication_selector(),
        legislator_id="test",
        member_bioguide_id="F000477",
        scope="119",
    )
    assert (
        api.get_editorial_presentations("test", scope="119", candidate=None) == expected
    )


def test_staged_migration_does_not_require_new_grants_for_legacy_reader(db):
    legacy = seed_legacy_gold(db)
    db.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='health_legacy_reader_test') THEN CREATE ROLE health_legacy_reader_test NOLOGIN BYPASSRLS; END IF; END $$"
    )
    db.execute("GRANT USAGE ON SCHEMA public TO health_legacy_reader_test")
    for table in p.TABLES.values():
        db.execute(f"GRANT SELECT ON public.{table} TO health_legacy_reader_test")
    with db.transaction():
        db.execute("SET LOCAL ROLE health_legacy_reader_test")
        repo = EditorialArtifactRepository(db)
        assert repo.publication_selector() == legacy
        assert repo.bounded_choice_publication_selector() == []


@pytest.mark.parametrize(
    "missing", ["owner_table", "owner_function", "envelope_function"]
)
def test_partial_bounded_reader_preserves_legacy_when_new_dependency_is_missing(
    db, missing
):
    legacy = seed_legacy_gold(db)
    role = "health_partial_reader_test"
    db.execute(
        f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{role}') THEN CREATE ROLE {role} NOLOGIN BYPASSRLS; END IF; END $$"
    )
    db.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
    for table in list(p.TABLES.values()) + ["editorial_bounded_choice_publications"]:
        db.execute(f"GRANT SELECT ON public.{table} TO {role}")
    for function in [
        "bounded_choice_graph_valid(bigint)",
        "bounded_choice_receipt_matches(jsonb,text)",
        "bounded_choice_digest(jsonb)",
        "bounded_choice_canonical_json(jsonb)",
        "bounded_choice_owner_evidence_matches(jsonb,boolean)",
        "bounded_choice_owner_decision_valid(jsonb)",
    ]:
        db.execute(f"GRANT EXECUTE ON FUNCTION public.{function} TO {role}")
    if missing == "owner_table":
        db.execute(
            f"REVOKE SELECT ON public.editorial_bounded_choice_owner_decisions FROM {role}"
        )
    elif missing == "owner_function":
        db.execute(
            f"REVOKE EXECUTE ON FUNCTION public.bounded_choice_owner_evidence_matches(jsonb,boolean) FROM {role}"
        )
    else:
        db.execute(
            f"REVOKE EXECUTE ON FUNCTION public.bounded_choice_owner_decision_valid(jsonb) FROM {role}"
        )
    with db.transaction():
        db.execute(f"SET LOCAL ROLE {role}")
        repository = EditorialArtifactRepository(db)
        assert repository.bounded_choice_publication_selector() == []
        assert repository.publication_selector() == legacy


def _snapshot(conn):
    return {
        name: conn.execute(f"SELECT * FROM public.{table} ORDER BY 1,2").fetchall()
        for name, table in p.TABLES.items()
    }


def _register_test_evidence(conn, value):
    # Test fixture writes only, after checking the actual owned DB identity.
    # There is no production registration executor or authority in this package.
    p.require_owned_test_connection(conn)
    plan = r.owner_authority.registration_plan(value["acceptance"])
    assert (
        plan["required_approval"]
        == "separate_positive_exact_owner_evidence_database_registration"
    )
    assert plan["authorizing"] is False
    assert plan["mutation_caps"] == r.owner_authority.REGISTRATION_CAPS
    assert plan["mutation_caps"]["insert_owner_decision_rows"] == 1
    assert all(
        v == 0
        for k, v in plan["mutation_caps"].items()
        if k != "insert_owner_decision_rows"
    )
    before = _snapshot(conn)
    row = plan["exact_row"]
    assert p.canonical_digest(row) == plan["exact_row_sha256"]
    assert "TEST_ONLY" in row["decision_id"]
    conn.execute(
        "INSERT INTO editorial_bounded_choice_owner_decisions (decision_id,decision_sha256,file_sha256,decision_jsonb) VALUES (%s,%s,%s,%s)",
        (
            row["decision_id"],
            row["decision_sha256"],
            row["file_sha256"],
            psycopg.types.json.Jsonb(row["decision_jsonb"]),
        ),
    )
    after = _snapshot(conn)
    assert len(after["owner_decisions"]) - len(before["owner_decisions"]) == 1
    assert all(after[k] == before[k] for k in before if k != "owner_decisions")
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute(
            "INSERT INTO editorial_bounded_choice_owner_decisions (decision_id,decision_sha256,file_sha256,decision_jsonb) VALUES (%s,%s,%s,%s)",
            (
                row["decision_id"],
                row["decision_sha256"],
                row["file_sha256"],
                psycopg.types.json.Jsonb(row["decision_jsonb"]),
            ),
        )
    assert _snapshot(conn) == after
    return plan


def test_registered_evidence_ordinary_defaults_two_member_serving_and_audit_retaining_rollback(
    db, tmp_path, monkeypatch
):
    from app.editorial_presentations.selector import select_public_presentations

    values = registered_fixture(tmp_path, monkeypatch)
    legacy = seed_legacy_gold(db)
    before_registration = _snapshot(db)
    for value in values.values():
        _register_test_evidence(db, value)
    baseline = _snapshot(db)
    assert len(baseline["owner_decisions"]) == 2
    assert all(
        baseline[k] == before_registration[k]
        for k in baseline
        if k != "owner_decisions"
    )
    assert db.execute(
        "SELECT current_setting('app.bounded_choice_synthetic_test',TRUE) AS mode"
    ).fetchone()["mode"] in (None, "", "off")
    executions = []
    for member, value in values.items():
        args = activation(db, member, value=value)
        assert "allow_test_authority" not in args
        assert (
            args["write_set"]["subject"]["expected_postconditions"]["counts"][
                "owner_decisions"
            ]
            == 2
        )
        executions.append((args, p.apply_initial(db, **args)))
        rows = EditorialArtifactRepository(db).bounded_choice_publication_selector()
        assert len(rows) == len(executions)
        for row in rows:
            identity = row["member_bioguide_id"]
            for scope in ["119", "all"]:
                selected = p.select_bounded_publication(
                    row, member_id=identity, scope=scope
                )
                assert selected["bounded_choice"]["proposition_ids"] == (
                    ["prop:75edca987585935c"] if identity == "F000477" else []
                )
                payload = select_public_presentations(
                    rows,
                    legislator_id=r.MEMBERS[identity][1],
                    member_bioguide_id=identity,
                    scope=scope,
                )
                assert len(payload["presentations"]) == 8
                assert (
                    next(
                        x for x in payload["presentations"] if x["issue_id"] == r.ISSUE
                    )
                    == selected
                )
            assert (
                p.select_bounded_publication(row, member_id=identity, scope="118")
                is None
            )
    audit_before = _snapshot(db)["owner_decisions"]
    compatibility = (
        r.ROOT
        / "docs/editorial/review_packages/health_bounded_choice_v1/staged-migration-rollback.sql"
    ).read_text()
    with pytest.raises(psycopg.Error, match="roll back all bounded data"):
        try:
            db.execute(compatibility)
        finally:
            db.execute("ROLLBACK")
    for args, execution in reversed(executions):
        p.rollback_initial(
            db, value=args["value"], write_set=args["write_set"], execution=execution
        )
    assert _snapshot(db) == baseline
    # Deliberately grant an audit reader access before rollback; compatibility
    # rollback must revoke even custom ACLs, while retaining every audit byte.
    role = "health_retained_audit_reader_test"
    db.execute(
        f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{role}') THEN CREATE ROLE {role} NOLOGIN BYPASSRLS; END IF; END $$"
    )
    db.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
    db.execute(f"GRANT SELECT ON editorial_bounded_choice_owner_decisions TO {role}")
    column_role = "health_column_audit_reader_test"
    grantor_role = "health_grantor_audit_reader_test"
    delegated_role = "health_delegated_audit_reader_test"
    for reader in [column_role, grantor_role, delegated_role]:
        db.execute(
            f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{reader}') THEN CREATE ROLE {reader} NOLOGIN BYPASSRLS; END IF; END $$"
        )
        db.execute(f"GRANT USAGE ON SCHEMA public TO {reader}")
    db.execute(
        f"GRANT SELECT (decision_jsonb) ON editorial_bounded_choice_owner_decisions TO {column_role}"
    )
    db.execute(
        f"GRANT SELECT ON editorial_bounded_choice_owner_decisions TO {grantor_role} WITH GRANT OPTION"
    )
    with db.transaction():
        db.execute(f"SET LOCAL ROLE {grantor_role}")
        db.execute(
            f"GRANT SELECT ON editorial_bounded_choice_owner_decisions TO {delegated_role}"
        )
    assert (
        db.execute(
            "SELECT has_column_privilege(%s,'editorial_bounded_choice_owner_decisions','decision_jsonb','SELECT') AS allowed",
            (column_role,),
        ).fetchone()["allowed"]
        is True
    )
    assert (
        db.execute(
            "SELECT has_table_privilege(%s,'editorial_bounded_choice_owner_decisions','SELECT') AS allowed",
            (delegated_role,),
        ).fetchone()["allowed"]
        is True
    )
    db.execute(compatibility)
    assert (
        db.execute(
            "SELECT * FROM editorial_bounded_choice_owner_decisions ORDER BY 1,2"
        ).fetchall()
        == audit_before
    )
    assert EditorialArtifactRepository(db).publication_selector() == legacy
    assert EditorialArtifactRepository(db).bounded_choice_publication_selector() == []
    for name in [
        "editorial_bounded_choice_publications",
        "bounded_choice_owner_evidence_matches(jsonb,boolean)",
    ]:
        expression = (
            "to_regclass" if name.startswith("editorial_") else "to_regprocedure"
        )
        assert (
            db.execute(
                f"SELECT {expression}(%s) AS object", ("public." + name,)
            ).fetchone()["object"]
            is None
        )
    security = db.execute(
        "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='editorial_bounded_choice_owner_decisions'::regclass"
    ).fetchone()
    assert security == {"relrowsecurity": True, "relforcerowsecurity": True}
    for reader in [
        role,
        column_role,
        grantor_role,
        delegated_role,
        "anon",
        "authenticated",
    ]:
        assert (
            db.execute(
                "SELECT has_table_privilege(%s,'editorial_bounded_choice_owner_decisions','SELECT,INSERT,UPDATE,DELETE') AS allowed",
                (reader,),
            ).fetchone()["allowed"]
            is False
        )
        assert (
            db.execute(
                "SELECT has_any_column_privilege(%s,'editorial_bounded_choice_owner_decisions','SELECT,INSERT,UPDATE,REFERENCES') AS allowed",
                (reader,),
            ).fetchone()["allowed"]
            is False
        )
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with db.transaction():
                db.execute(f"SET LOCAL ROLE {reader}")
                db.execute(
                    "SELECT decision_jsonb FROM public.editorial_bounded_choice_owner_decisions"
                )
    for operation in [
        "UPDATE editorial_bounded_choice_owner_decisions SET file_sha256=file_sha256",
        "DELETE FROM editorial_bounded_choice_owner_decisions",
    ]:
        with pytest.raises(psycopg.Error, match="append-only"):
            db.execute(operation)
    assert (
        db.execute(
            "SELECT * FROM editorial_bounded_choice_owner_decisions ORDER BY 1,2"
        ).fetchall()
        == audit_before
    )
    # Explicitly authorized future reapplication can restore the schema without
    # recreating or erasing retained evidence; this is still only the owned DB.
    db.execute(STAGED.read_text())
    assert _snapshot(db) == baseline
    assert EditorialArtifactRepository(db).publication_selector() == legacy
    assert EditorialArtifactRepository(db).bounded_choice_publication_selector() == []


def test_owner_evidence_sql_rejects_omitted_null_wrong_type_and_extra_fields(
    db, tmp_path, monkeypatch
):
    values = registered_fixture(tmp_path, monkeypatch)
    row = r.owner_authority.registration_plan(values["F000477"]["acceptance"])[
        "exact_row"
    ]
    original = row["decision_jsonb"]
    bad = []
    for key in original:
        for mode in ["omitted", "null", "wrong_type"]:
            value = copy.deepcopy(original)
            if mode == "omitted":
                del value[key]
            else:
                value[key] = None if mode == "null" else 0
            bad.append(value)
    for key in original["provenance"]:
        for mode in ["omitted", "null", "wrong_type"]:
            value = copy.deepcopy(original)
            if mode == "omitted":
                del value["provenance"][key]
            else:
                value["provenance"][key] = None if mode == "null" else 0
            bad.append(value)
    bad.append({**original, "extra": "unreviewed"})
    bad.append(
        {**original, "provenance": {**original["provenance"], "extra": "unreviewed"}}
    )
    for value in bad:
        with pytest.raises(psycopg.errors.CheckViolation):
            db.execute(
                "INSERT INTO editorial_bounded_choice_owner_decisions (decision_id,decision_sha256,file_sha256,decision_jsonb) VALUES (%s,%s,%s,%s)",
                (
                    row["decision_id"],
                    p.canonical_digest(value),
                    row["file_sha256"],
                    psycopg.types.json.Jsonb(value),
                ),
            )
        assert (
            db.execute(
                "SELECT bounded_choice_owner_decision_valid(%s) AS valid",
                (psycopg.types.json.Jsonb(value),),
            ).fetchone()["valid"]
            is False
        )
    _register_test_evidence(db, values["F000477"])
