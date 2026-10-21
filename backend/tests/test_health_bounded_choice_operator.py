"""Actual operator CLI, real gates, TEST ONLY evidence and owned PostgreSQL."""

import hashlib
import itertools
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.editorial_presentations import bounded_choice_operator as op
from app.editorial_presentations import bounded_choice_publication as p
from app.editorial_presentations import bounded_choice_review as r
from health_choice_registered_fixture import registered_fixture
from test_health_bounded_choice_postgres import (
    DSN,
    activation,
    db as base_db_fixture,
    seed_legacy_gold,
    _snapshot,
)  # noqa: F401


@pytest.fixture
def db():
    if not DSN:
        pytest.skip("explicit owned PostgreSQL required")
    yield from base_db_fixture.__wrapped__()


@pytest.fixture
def rehearsal(db, tmp_path, monkeypatch):
    # Only trust-store DATA paths change. Verifiers and operator defaults run.
    values = registered_fixture(tmp_path / "trust", monkeypatch)
    monkeypatch.setattr(op, "TRUST_ROOT", tmp_path / "trust")
    monkeypatch.setenv("HEALTH_CHOICE_DATABASE_URL", DSN)
    directory = op.TRUST_ROOT / op.DIRECTORY
    registry = directory / "operator_approval_registry.json"
    registry.write_text(
        json.dumps(
            {
                "schema_version": "bounded_choice_operator_approval_registry_v1",
                "records": [],
            }
        ),
        encoding="utf-8",
    )
    (directory / "operator_production_bindings.json").write_text(
        json.dumps(
            {
                "schema_version": "bounded_choice_production_binding_observations_v1",
                "state": "pending",
                "observed": None,
                "source_evidence": [],
            }
        ),
        encoding="utf-8",
    )
    serial = itertools.count()

    def write(name, value):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def call(operation, **files):
        output = tmp_path / (f"result-{next(serial)}.json")
        argv = [operation, "--target", "owned-loopback", "--output", str(output)]
        for key, value in files.items():
            argv += ["--" + key.replace("_", "-"), str(value)]
        if operation in {"register", "publish", "rollback"}:
            argv += ["--confirm"]
        result = op.main(argv)
        assert json.loads(output.read_text(encoding="utf-8")) == result
        return result, str(output)

    def pin(approval, operation, target):
        decision_id = approval["artifact_id"]
        path = directory / "operator_approvals" / (decision_id + ".json")
        path.parent.mkdir(exist_ok=True)
        raw = (json.dumps(approval, sort_keys=True) + "\n").encode()
        path.write_bytes(raw)
        catalog = json.loads(registry.read_text(encoding="utf-8"))
        catalog["records"].append(
            {
                "approval_id": decision_id,
                "operation": operation,
                "path": path.relative_to(op.TRUST_ROOT).as_posix(),
                "file_sha256": hashlib.sha256(raw).hexdigest(),
                "subject_sha256": p.canonical_digest(approval["subject"]),
                "target_identity_sha256": p.canonical_digest(target),
                "production_bindings_sha256": None,
                "provenance": {
                    "kind": "direct_owner_decision",
                    "source_ref": "TEST ONLY temporary operator evidence",
                    "decision_quote": "TEST ONLY exact operation rehearsal; no actual owner authorization",
                },
            }
        )
        registry.write_text(json.dumps(catalog), encoding="utf-8")
        return decision_id

    def registration_approval(request, change=None):
        subject = {
            **op.registration_binding(request),
            "decision": request["plan"]["required_approval"],
            "reviewer": "TEST ONLY operator rehearsal",
            "reviewer_authority": "bounded_choice_review_authority_v1",
            "decision_recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        approval = {
            "schema_version": "bounded_choice_registration_approval_v1",
            "artifact_id": "TEST_ONLY_registration_" + str(next(serial)),
            "immutable": True,
            "sealed": True,
            "accepted": True,
            "subject": subject,
        }
        if change:
            change(approval)
        approval["subject_sha256"] = p.canonical_digest(subject)
        return pin(approval, "register", request["target"])

    def register_all():
        for member, value in values.items():
            request, path = call("prepare-registration", candidate=write(member, value))
            call("register", request=path, approval_id=registration_approval(request))

    def prepare_publish(member):
        value = values[member]
        args = activation(db, member, value=value)
        context = {
            "preparation": args["authority"]["subject"][
                "preparation_authority_binding"
            ],
            "runtime": args["authority"]["subject"]["stable_runtime_binding"],
        }
        request, path = call(
            "prepare-publication",
            candidate=write(member, value),
            context=write("context-" + member, context),
        )
        assert request["write_set"] == args["write_set"]
        approval = args["authority"]
        approval["artifact_id"] = "TEST_ONLY_publish_" + member
        approval_id = pin(approval, "publish", request["target"])
        return path, approval_id, write("proof-" + member, args["runtime_proof"])

    return dict(
        values=values,
        call=call,
        write=write,
        pin=pin,
        registry=registry,
        registration_approval=registration_approval,
        register_all=register_all,
        prepare_publish=prepare_publish,
    )


def test_cli_registration_then_sequential_v2_publication_and_reverse_rollback(
    db, rehearsal
):
    x = rehearsal
    legacy = seed_legacy_gold(db)
    before = _snapshot(db)
    registrations = []
    for member, value in x["values"].items():
        request, path = x["call"](
            "prepare-registration", candidate=x["write"](member, value)
        )
        assert request["authorizing"] is False
        report, _ = x["call"](
            "register", request=path, approval_id=x["registration_approval"](request)
        )
        registrations.append(report)
        assert len(_snapshot(db)["owner_decisions"]) == len(registrations)
        with pytest.raises(SystemExit):
            x["call"]("register", request=path, approval_id="replay")
    baseline = _snapshot(db)
    assert all(baseline[k] == before[k] for k in before if k != "owner_decisions")
    assert db.execute(
        "SELECT current_setting('app.bounded_choice_synthetic_test',TRUE) AS value"
    ).fetchone()["value"] in (None, "", "off")
    with pytest.raises(SystemExit):
        x["prepare_publish"]("M001184")
    executions = []
    for member in ["F000477", "M001184"]:
        request, approval_id, proof = x["prepare_publish"](member)
        report, report_path = x["call"](
            "publish", request=request, approval_id=approval_id, runtime_proof=proof
        )
        recovered, recovered_path = x["call"](
            "inspect-publication", request=request, approval_id=approval_id
        )
        assert recovered == report
        Path(report_path).unlink()  # Simulate a lost local report, never DB evidence.
        report_path = recovered_path
        executions.append((request, approval_id, report_path))
        from app.editorial_artifacts.repository import EditorialArtifactRepository

        selected = EditorialArtifactRepository(db).bounded_choice_publication_selector()
        assert len(selected) == len(executions)
        assert all(
            p.select_bounded_publication(
                row, member_id=row["member_bioguide_id"], scope="119"
            )
            for row in selected
        )
        assert all(
            p.select_bounded_publication(
                row, member_id=row["member_bioguide_id"], scope="118"
            )
            is None
            for row in selected
        )
        with pytest.raises(SystemExit):
            x["call"](
                "publish", request=request, approval_id=approval_id, runtime_proof=proof
            )
    with pytest.raises(SystemExit):
        request, approval_id, report_path = executions[0]
        x["call"](
            "rollback",
            request=request,
            approval_id=approval_id,
            execution_report=report_path,
        )
    for request, approval_id, report_path in reversed(executions):
        x["call"](
            "rollback",
            request=request,
            approval_id=approval_id,
            execution_report=report_path,
        )
    assert _snapshot(db) == baseline
    from app.editorial_artifacts.repository import EditorialArtifactRepository

    assert EditorialArtifactRepository(db).publication_selector() == legacy


@pytest.mark.parametrize(
    "change",
    ["missing", "caps", "row", "target", "baseline", "pending", "future", "bytes"],
)
def test_cli_registration_bad_approval_or_binding_has_no_write(db, rehearsal, change):
    x = rehearsal
    request, path = x["call"](
        "prepare-registration",
        candidate=x["write"]("candidate", x["values"]["F000477"]),
    )

    def alter(approval):
        subject = approval["subject"]
        if change == "caps":
            subject["mutation_caps"]["insert_owner_decision_rows"] = 2
        elif change == "row":
            subject["exact_row_sha256"] = "0" * 64
        elif change == "target":
            subject["production_target_identity_sha256"] = "0" * 64
        elif change == "baseline":
            subject["stable_baseline_sha256"] = "0" * 64
        elif change == "pending":
            approval["accepted"] = False
        elif change == "future":
            subject["decision_recorded_at_utc"] = (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat()

    approval_id = (
        "missing" if change == "missing" else x["registration_approval"](request, alter)
    )
    if change == "bytes":
        catalog = json.loads(x["registry"].read_text(encoding="utf-8"))
        target = op.TRUST_ROOT / catalog["records"][0]["path"]
        target.write_text(target.read_text(encoding="utf-8") + " ", encoding="utf-8")
    before = _snapshot(db)
    with pytest.raises(SystemExit):
        x["call"]("register", request=path, approval_id=approval_id)
    assert _snapshot(db) == before


def test_cli_registration_stale_baseline_and_changed_request_reject(db, rehearsal):
    x = rehearsal
    request, path = x["call"](
        "prepare-registration",
        candidate=x["write"]("candidate", x["values"]["F000477"]),
    )
    approval_id = x["registration_approval"](request)
    seed_legacy_gold(db)
    before = _snapshot(db)
    with pytest.raises(SystemExit):
        x["call"]("register", request=path, approval_id=approval_id)
    request["target"]["route"]["host"] = "wrong.invalid"
    request = r.seal(request, "request_sha256")
    with pytest.raises(SystemExit):
        x["call"](
            "register",
            request=x["write"]("wrong-target", request),
            approval_id=approval_id,
        )
    assert _snapshot(db) == before


def test_separate_registrations_require_second_fresh_baseline(db, rehearsal):
    x = rehearsal
    requests = []
    for member, value in x["values"].items():
        request, path = x["call"](
            "prepare-registration", candidate=x["write"](member, value)
        )
        requests.append((path, x["registration_approval"](request)))
    x["call"]("register", request=requests[0][0], approval_id=requests[0][1])
    first = _snapshot(db)
    with pytest.raises(SystemExit):
        x["call"]("register", request=requests[1][0], approval_id=requests[1][1])
    assert _snapshot(db) == first and len(first["owner_decisions"]) == 1


def test_lock_recheck_catches_change_after_read_only_preflight(
    db, rehearsal, monkeypatch
):
    x = rehearsal
    request, path = x["call"](
        "prepare-registration",
        candidate=x["write"]("candidate", x["values"]["F000477"]),
    )
    approval = x["registration_approval"](request)
    real_verifier = op.trusted_approval
    changed = []

    def concurrent_change(*args, **kwargs):
        result = real_verifier(*args, **kwargs)
        seed_legacy_gold(db)  # Independent autocommit connection, owned test DB.
        changed.append(_snapshot(db))
        return result

    monkeypatch.setattr(op, "trusted_approval", concurrent_change)
    with pytest.raises(SystemExit):
        x["call"]("register", request=path, approval_id=approval)
    assert len(changed) == 1 and _snapshot(db) == changed[0]


def test_production_pending_bindings_cannot_be_promoted_by_approval_record(
    db, rehearsal
):
    x = rehearsal
    request, _ = x["call"](
        "prepare-registration",
        candidate=x["write"]("candidate", x["values"]["F000477"]),
    )
    request["target"]["profile"] = "production-green"
    request["target"]["route"] = op.GREEN
    approval = x["registration_approval"](request)
    before = _snapshot(db)
    with pytest.raises(ValueError, match="bindings remain unresolved"):
        op.trusted_approval(approval, "register", request["target"])
    assert _snapshot(db) == before


@pytest.mark.parametrize("deferred", [False, True])
def test_registration_trigger_side_effect_rolls_back_entire_transaction(
    db, rehearsal, deferred
):
    x = rehearsal
    db.execute(
        "CREATE TABLE operator_canary (id int PRIMARY KEY, value int); INSERT INTO operator_canary VALUES(1,0)"
    )
    db.execute(
        "CREATE FUNCTION operator_bad_trigger() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN UPDATE operator_canary SET value=value+1; RETURN NEW; END $$"
    )
    if deferred:
        db.execute(
            "CREATE CONSTRAINT TRIGGER operator_bad AFTER INSERT ON editorial_bounded_choice_owner_decisions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION operator_bad_trigger()"
        )
    else:
        db.execute(
            "CREATE TRIGGER operator_bad AFTER INSERT ON editorial_bounded_choice_owner_decisions FOR EACH ROW EXECUTE FUNCTION operator_bad_trigger()"
        )
    request, path = x["call"](
        "prepare-registration",
        candidate=x["write"]("candidate", x["values"]["F000477"]),
    )
    before = _snapshot(db)
    with pytest.raises(SystemExit):
        x["call"](
            "register", request=path, approval_id=x["registration_approval"](request)
        )
    assert _snapshot(db) == before
    assert db.execute("SELECT value FROM operator_canary").fetchone()["value"] == 0


def test_second_publication_failure_retains_first_until_exact_operator_rollback(
    db, rehearsal
):
    x = rehearsal
    x["register_all"]()
    baseline = _snapshot(db)
    first, authority, proof = x["prepare_publish"]("F000477")
    _, first_report = x["call"](
        "publish", request=first, approval_id=authority, runtime_proof=proof
    )
    after_first = _snapshot(db)
    second, second_authority, proof = x["prepare_publish"]("M001184")
    db.execute(
        "CREATE FUNCTION operator_fail_second() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.member_bioguide_id='M001184' THEN RAISE EXCEPTION 'TEST ONLY second member failure'; END IF; RETURN NEW; END $$"
    )
    db.execute(
        "CREATE TRIGGER operator_failure AFTER INSERT ON editorial_publication_registry FOR EACH ROW EXECUTE FUNCTION operator_fail_second()"
    )
    with pytest.raises(SystemExit):
        x["call"](
            "publish", request=second, approval_id=second_authority, runtime_proof=proof
        )
    assert _snapshot(db) == after_first
    x["call"](
        "rollback", request=first, approval_id=authority, execution_report=first_report
    )
    assert _snapshot(db) == baseline


@pytest.mark.parametrize(
    "change", ["edge_ordinal", "edge_metadata", "registry_authority", "baseline"]
)
def test_report_recovery_rejects_same_count_state_changes(db, rehearsal, change):
    x = rehearsal
    seed_legacy_gold(db)
    x["register_all"]()
    request, approval, proof = x["prepare_publish"]("F000477")
    report, _ = x["call"](
        "publish", request=request, approval_id=approval, runtime_proof=proof
    )
    root = report["execution"]["artifact_ids"][x["values"]["F000477"]["artifact_id"]]
    if change == "edge_ordinal":
        db.execute(
            "UPDATE editorial_artifact_relationships SET ordinal=1 WHERE parent_artifact_id=%s",
            (root,),
        )
    elif change == "edge_metadata":
        db.execute(
            "UPDATE editorial_artifact_relationships SET metadata_jsonb='{\"changed\":true}' WHERE parent_artifact_id=%s",
            (root,),
        )
    elif change == "registry_authority":
        db.execute(
            "UPDATE editorial_publication_registry SET publication_metadata_jsonb=jsonb_set(publication_metadata_jsonb,'{activation_authority_sha256}',to_jsonb(%s::text)) WHERE artifact_id=%s",
            ("0" * 64, root),
        )
    else:
        db.execute(
            "UPDATE editorial_artifact_batches SET status='rolled_back' WHERE deterministic_batch_key<>%s",
            (report["execution"]["batch_key"],),
        )
    before = _snapshot(db)
    with pytest.raises(SystemExit):
        x["call"]("inspect-publication", request=request, approval_id=approval)
    assert _snapshot(db) == before


@pytest.mark.parametrize(
    "change", ["inactive", "authority", "artifact_metadata", "json_boolean"]
)
def test_before_insert_rewrite_cannot_commit_successful_publication(
    db, rehearsal, change
):
    x = rehearsal
    x["register_all"]()
    request, approval, proof = x["prepare_publish"]("F000477")
    if change == "artifact_metadata":
        table = "editorial_artifact_versions"
        body = "NEW.review_route='sampled_audit';"
    else:
        table = "editorial_publication_registry"
        body = (
            "NEW.deactivated_at=NEW.activated_at;"
            if change == "inactive"
            else "NEW.publication_metadata_jsonb=jsonb_set(NEW.publication_metadata_jsonb,'{activation_authority_sha256}',to_jsonb(repeat('0',64)));"
        )
        if change == "json_boolean":
            body = "NEW.publication_metadata_jsonb=jsonb_set(NEW.publication_metadata_jsonb,'{presentation_artifact_version}','true'::jsonb);"
    db.execute(
        "CREATE FUNCTION operator_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
        + body
        + " RETURN NEW; END $$"
    )
    db.execute(
        "CREATE TRIGGER operator_rewrite BEFORE INSERT ON "
        + table
        + " FOR EACH ROW EXECUTE FUNCTION operator_rewrite()"
    )
    before = _snapshot(db)
    with pytest.raises(SystemExit):
        x["call"]("publish", request=request, approval_id=approval, runtime_proof=proof)
    assert _snapshot(db) == before


def test_durable_approval_lookup_does_not_require_refreshed_global_observations(
    db, rehearsal
):
    x = rehearsal
    x["register_all"]()
    _, approval_id, _ = x["prepare_publish"]("F000477")
    catalog = json.loads(x["registry"].read_text(encoding="utf-8"))
    entry = next(row for row in catalog["records"] if row["approval_id"] == approval_id)
    approval = json.loads((op.TRUST_ROOT / entry["path"]).read_text(encoding="utf-8"))
    approval["artifact_id"] += "_production_lookup_TEST_ONLY"
    target = {
        "profile": "production-green",
        "route": op.GREEN,
        "observed": {"TEST_ONLY": True},
    }
    approval_id = x["pin"](approval, "publish", target)
    bindings = op.TRUST_ROOT / op.DIRECTORY / "operator_production_bindings.json"
    # No production connection is made. Fixed approval bytes and target remain
    # mandatory; only current deployment observations cease governing recovery.
    assert (
        op.trusted_approval(approval_id, "publish", target, fresh_bindings=False)
        == approval
    )
    with pytest.raises(ValueError, match="bindings remain unresolved"):
        op.trusted_approval(approval_id, "publish", target)
    bindings.unlink()
    assert (
        op.trusted_approval(approval_id, "publish", target, fresh_bindings=False)
        == approval
    )
    with pytest.raises(OSError):
        op.trusted_approval(approval_id, "publish", target)
    entry = next(
        row
        for row in json.loads(x["registry"].read_text(encoding="utf-8"))["records"]
        if row["approval_id"] == approval_id
    )
    with (op.TRUST_ROOT / entry["path"]).open("a", encoding="utf-8") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="bytes differ"):
        op.trusted_approval(approval_id, "publish", target, fresh_bindings=False)


def test_confirmation_and_routing_fail_before_connect_or_secret_output(
    monkeypatch, capsys, tmp_path
):
    connect = Mock()
    monkeypatch.setattr(op.psycopg, "connect", connect)
    with pytest.raises(SystemExit):
        op.main(["register", "--output", str(tmp_path / "unused")])
    monkeypatch.setenv(
        "HEALTH_CHOICE_DATABASE_URL",
        "postgresql://postgres:SECRET_SENTINEL@wrong.invalid/postgres?sslmode=verify-full",
    )
    with pytest.raises(SystemExit):
        op.main(["prepare-registration", "--output", str(tmp_path / "unused")])
    connect.assert_not_called()
    assert "SECRET_SENTINEL" not in capsys.readouterr().err


@pytest.mark.parametrize(
    "environment", ["PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS"]
)
def test_inherited_routing_rejects_before_any_connection(
    monkeypatch, tmp_path, environment
):
    connect = Mock()
    monkeypatch.setattr(op.psycopg, "connect", connect)
    monkeypatch.setenv(environment, "unapproved-routing")
    with pytest.raises(SystemExit):
        op.main(["prepare-registration", "--output", str(tmp_path / "unused")])
    connect.assert_not_called()


@pytest.mark.skipif(not DSN, reason="explicit owned PostgreSQL required")
def test_target_default_acl_profile_exposes_privileged_server_access_and_retains_audit(
    db,
):
    # Recreate only the staged objects under the actual creator's target-like
    # default ACLs. This is the owned loopback database, never Green.
    compatibility = (
        r.ROOT / r.owner_authority.DIRECTORY / "staged-migration-rollback.sql"
    ).read_text(encoding="utf-8")
    db.execute(compatibility)
    db.execute("DROP TABLE editorial_bounded_choice_owner_decisions CASCADE")
    db.execute(
        "DO $$ BEGIN IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='service_role') THEN CREATE ROLE service_role NOLOGIN BYPASSRLS; END IF; END $$"
    )
    db.execute("ALTER ROLE service_role BYPASSRLS")
    db.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role"
    )
    db.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
    )
    db.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO service_role"
    )
    staged = (
        r.ROOT
        / "backend/migrations/staged/20261019231216_bounded_health_choice_publication.sql"
    ).read_text(encoding="utf-8")
    db.execute(staged)
    privileges = db.execute(
        "SELECT has_table_privilege('service_role','editorial_bounded_choice_owner_decisions','SELECT,INSERT') AS server_audit, has_table_privilege('service_role','editorial_bounded_choice_publications','SELECT') AS server_view,has_function_privilege('service_role','bounded_choice_graph_valid(bigint)','EXECUTE') AS server_function,has_table_privilege('anon','editorial_bounded_choice_owner_decisions','SELECT') AS anon_audit,has_table_privilege('authenticated','editorial_bounded_choice_publications','SELECT') AS authenticated_view"
    ).fetchone()
    assert privileges == dict(
        server_audit=True,
        server_view=True,
        server_function=True,
        anon_audit=False,
        authenticated_view=False,
    )
    db.execute(compatibility)
    assert db.execute(
        "SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='editorial_bounded_choice_owner_decisions'::regclass"
    ).fetchone() == dict(relrowsecurity=True, relforcerowsecurity=True)
    assert (
        db.execute(
            "SELECT has_table_privilege('service_role','editorial_bounded_choice_owner_decisions','SELECT,INSERT') AS allowed"
        ).fetchone()["allowed"]
        is False
    )
