"""Dormant exact-scope operator. No startup, migration or deployment hook.

Approvals are fixed repository data, never CLI-supplied authority. The owned
loopback profile changes only the connection target, not the approval gates.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import bounded_choice_authority as owner
from . import bounded_choice_publication as publication
from . import bounded_choice_review as review
from .bounded_choice_mutations import require_transaction_delta, transaction_counts
from .compiler import canonical_digest as digest
from .publication_activation_governance_v2 import validate_stable_positive_authority

TRUST_ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path(owner.DIRECTORY)
GREEN = {
    "host": "db.yalpfkaxkxebwolhorha.supabase.co",
    "port": 5432,
    "database": "postgres",
    "username": "postgres",
}
PROFILES = ("production-green", "owned-loopback")
HEALTH_URL = "https://political-fingerprint.onrender.com/health"
ROUTING_ENV = {
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGOPTIONS",
    "PGSSLMODE",
    "PGSSLROOTCERT",
    "PGTARGETSESSIONATTRS",
}


def normalized(value):
    return json.loads(json.dumps(value, default=str))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def snapshots(conn):
    return normalized(
        {
            name: conn.execute(f"SELECT * FROM public.{table} ORDER BY 1,2").fetchall()
            for name, table in publication.TABLES.items()
        }
    )


def validate_route(parameters, profile):
    review.require(profile in PROFILES, "unknown bounded target profile")
    review.require(
        set(parameters)
        <= {"host", "port", "dbname", "user", "password", "sslmode", "sslrootcert"},
        "unapproved connection routing option",
    )
    route = {
        "host": parameters.get("host"),
        "port": int(parameters.get("port", 5432)),
        "database": parameters.get("dbname"),
        "username": parameters.get("user"),
    }
    if profile == "production-green":
        review.require(
            route == GREEN and parameters.get("sslmode") == "verify-full",
            "production target requires exact Green route and verified TLS",
        )
    else:
        review.require(
            route["host"] in {"127.0.0.1", "::1", "localhost"}
            and route["database"] == "pf_health_choice_test"
            and isinstance(route["username"], str)
            and route["username"],
            "owned target requires the exact loopback test database",
        )
    return route


def target_identity(conn, profile):
    review.require(
        conn.info.transaction_status == 2, "target observation requires a transaction"
    )
    parameters = conn.info.get_parameters()
    review.require(
        not any(parameters.get(key) for key in ["service", "options"]),
        "actual connection has an unapproved routing override",
    )
    # Do not expose libpq parameters: they can include the password.
    route = validate_route(
        {
            k: parameters[k]
            for k in ["host", "port", "dbname", "user", "sslmode", "sslrootcert"]
            if k in parameters
        },
        profile,
    )
    if profile == "owned-loopback":
        # libpq reports a resolved hostaddr even without an input override.
        review.require(
            parameters.get("hostaddr") in {None, "", "127.0.0.1", "::1"},
            "actual owned connection address is not loopback",
        )
        publication.require_owned_test_connection(conn)
    else:
        review.require(
            conn.pgconn.ssl_in_use and parameters.get("sslmode") == "verify-full",
            "actual production connection lacks verified TLS",
        )
    observed = conn.execute(
        "SELECT current_database() AS database,current_user AS username,"
        "host(inet_server_addr()) AS server_address,inet_server_port() AS server_port"
    ).fetchone()
    review.require(
        observed["database"] == route["database"]
        and observed["username"] == route["username"]
        and observed["server_port"] == route["port"],
        "actual connected target differs",
    )
    if profile == "owned-loopback":
        review.require(
            observed["server_address"] in {"127.0.0.1", "::1"},
            "actual owned server is not loopback",
        )
    return {"profile": profile, "route": route, "observed": observed}


def capture(conn, value, profile):
    publication.validate_candidate(value)
    review.require(
        conn.info.transaction_status == 0, "operator requires an idle connection"
    )
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        target = target_identity(conn, profile)
        state = snapshots(conn)
        baseline = publication.observe_baseline(conn, value)
        readonly = (
            conn.execute("SHOW transaction_read_only").fetchone()[
                "transaction_read_only"
            ]
            == "on"
        )
    return {
        "target": target,
        "state": state,
        "baseline": baseline,
        "transaction_read_only": readonly,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def prepare_registration(conn, value, profile):
    plan = owner.registration_plan(value["acceptance"])
    observation = capture(conn, value, profile)
    review.require(
        not any(
            row["decision_id"] == plan["exact_row"]["decision_id"]
            for row in observation["state"]["owner_decisions"]
        ),
        "owner decision already registered",
    )
    return review.seal(
        {
            "schema_version": "bounded_choice_registration_request_v1",
            "value": value,
            "plan": plan,
            "target": observation["target"],
            "baseline": {
                "counts": observation["baseline"]["counts"],
                "state_fingerprint_sha256": digest(observation["state"]),
            },
            "authorizing": False,
        },
        "request_sha256",
    )


def registration_binding(request):
    return {
        "member_id": request["plan"]["member_id"],
        "pair_subject_sha256": request["value"]["acceptance"]["pair_subject_sha256"],
        "exact_row_sha256": request["plan"]["exact_row_sha256"],
        "registration_plan_sha256": digest(request["plan"]),
        "production_target_identity_sha256": digest(request["target"]),
        "stable_baseline_sha256": digest(request["baseline"]),
        "mutation_caps": copy.deepcopy(owner.REGISTRATION_CAPS),
    }


def trusted_approval(approval_id, operation, target, *, fresh_bindings=True):
    registry = read_json(TRUST_ROOT / DIRECTORY / "operator_approval_registry.json")
    review.require(
        set(registry) == {"schema_version", "records"}
        and registry["schema_version"]
        == "bounded_choice_operator_approval_registry_v1",
        "operator approval registry differs",
    )
    entries = [
        row for row in registry["records"] if row.get("approval_id") == approval_id
    ]
    review.require(
        len(entries) == 1, "separate exact operator approval is not registered"
    )
    entry = entries[0]
    review.require(
        set(entry)
        == {
            "approval_id",
            "operation",
            "path",
            "file_sha256",
            "subject_sha256",
            "target_identity_sha256",
            "provenance",
            "production_bindings_sha256",
        }
        and entry["operation"] == operation
        and entry["target_identity_sha256"] == digest(target),
        "operator approval operation or target differs",
    )
    provenance = entry["provenance"]
    review.require(
        set(provenance) == {"kind", "source_ref", "decision_quote"}
        and provenance["kind"] == "direct_owner_decision"
        and all(
            isinstance(provenance[k], str) and provenance[k].strip()
            for k in ["source_ref", "decision_quote"]
        ),
        "direct separate operator approval provenance required",
    )
    path = (TRUST_ROOT / entry["path"]).resolve()
    review.require(
        path.is_relative_to((TRUST_ROOT / DIRECTORY / "operator_approvals").resolve()),
        "operator approval path differs",
    )
    raw = path.read_bytes()
    review.require(
        hashlib.sha256(raw).hexdigest() == entry["file_sha256"],
        "operator approval bytes differ",
    )
    approval = json.loads(raw)
    review.require(
        approval["artifact_id"] == approval_id
        and digest(approval["subject"]) == entry["subject_sha256"],
        "operator approval subject differs",
    )
    if target["profile"] == "production-green" and fresh_bindings:
        bindings = read_json(
            TRUST_ROOT / DIRECTORY / "operator_production_bindings.json"
        )
        review.require(
            bindings["state"] == "observed"
            and bindings["observed"] is not None
            and digest(bindings) == entry["production_bindings_sha256"],
            "production service bindings remain unresolved",
        )
        observed = bindings["observed"]
        review.require(
            observed["supabase_project_ref"] == "yalpfkaxkxebwolhorha"
            and observed["render_database_route"] == GREEN
            and observed["vercel_project_id"] == "prj_BK1ncrlDgqWLQjf8z0yw8GW8enLp"
            and observed["frontend_api_origin"]
            == "https://political-fingerprint.onrender.com"
            and all(
                row["source_kind"] == "authorized_connector_observation"
                and row["source_ref"]
                for row in bindings["source_evidence"]
            )
            and len(bindings["source_evidence"]) >= 2,
            "recorded production binding evidence differs",
        )
        captured = datetime.fromisoformat(
            observed["captured_at_utc"].replace("Z", "+00:00")
        )
        age = (datetime.now(timezone.utc) - captured).total_seconds()
        review.require(
            captured.utcoffset().total_seconds() == 0 and age >= 0 and age <= 1800,
            "production binding observations require a fresh authorized capture",
        )
        if operation == "publish":
            source = approval["subject"]["stable_runtime_binding"][
                "reviewed_source_commit"
            ]
            review.require(
                observed["render_source_commit"] == source
                and observed["vercel_source_commit"] == source,
                "recorded deployments differ from approved source",
            )
        # This validates pinned observation records, not an invented discovery of
        # platform configuration. Real connector evidence is currently absent.
    return approval


def utc_not_future(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    review.require(
        stamp.utcoffset() is not None
        and stamp.utcoffset().total_seconds() == 0
        and stamp <= datetime.now(timezone.utc),
        "approval timestamp differs",
    )


def register(conn, request, approval_id, profile):
    review.check_seal(request, "request_sha256")
    review.require(
        request["schema_version"] == "bounded_choice_registration_request_v1"
        and request["authorizing"] is False,
        "registration request differs",
    )
    fresh = prepare_registration(conn, request["value"], profile)
    review.require(
        digest(fresh) == digest(request), "registration target or baseline changed"
    )
    approval = trusted_approval(approval_id, "register", request["target"])
    review.require(
        set(approval)
        == {
            "schema_version",
            "artifact_id",
            "immutable",
            "sealed",
            "accepted",
            "subject",
            "subject_sha256",
        }
        and approval["schema_version"] == "bounded_choice_registration_approval_v1"
        and all(approval[k] is True for k in ["immutable", "sealed", "accepted"]),
        "positive separate registration approval required",
    )
    subject = approval["subject"]
    expected = registration_binding(request)
    review.require(
        set(subject)
        == {
            *expected,
            "decision",
            "reviewer",
            "reviewer_authority",
            "decision_recorded_at_utc",
        }
        and digest({k: subject[k] for k in expected}) == digest(expected)
        and approval["subject_sha256"] == digest(subject)
        and subject["decision"] == request["plan"]["required_approval"]
        and subject["reviewer_authority"] == "bounded_choice_review_authority_v1"
        and isinstance(subject["reviewer"], str)
        and subject["reviewer"].strip(),
        "registration approval does not bind exact row, target, baseline and caps",
    )
    utc_not_future(subject["decision_recorded_at_utc"])
    with conn.transaction():
        conn.execute("SET LOCAL lock_timeout = '5s'")
        conn.execute("SET LOCAL statement_timeout = '60s'")
        conn.execute(
            "LOCK TABLE public.editorial_artifact_batches,public.editorial_artifact_versions,"
            "public.editorial_artifact_relationships,public.editorial_publication_registry,"
            "public.editorial_bounded_choice_owner_decisions IN SHARE ROW EXCLUSIVE MODE"
        )
        review.require(
            digest(target_identity(conn, profile)) == digest(request["target"]),
            "locked registration target changed",
        )
        before = snapshots(conn)
        review.require(
            digest(before) == request["baseline"]["state_fingerprint_sha256"],
            "locked registration baseline changed",
        )
        mutations = transaction_counts(conn)
        row = request["plan"]["exact_row"]
        conn.execute(
            "INSERT INTO public.editorial_bounded_choice_owner_decisions "
            "(decision_id,decision_sha256,file_sha256,decision_jsonb) VALUES (%s,%s,%s,%s)",
            (
                row["decision_id"],
                row["decision_sha256"],
                row["file_sha256"],
                Jsonb(row["decision_jsonb"]),
            ),
        )
        require_transaction_delta(
            conn, mutations, {publication.TABLES["owner_decisions"]: (1, 0, 0)}
        )
        expected_state = copy.deepcopy(before)
        expected_state["owner_decisions"] = sorted(
            before["owner_decisions"] + [row], key=lambda r: r["decision_id"]
        )
        after = snapshots(conn)
        review.require(
            digest(after) == digest(expected_state),
            "registration exceeded exact one-row delta",
        )
    return {
        "operation": "register",
        "member_id": request["plan"]["member_id"],
        "decision_id": row["decision_id"],
        "exact_row_sha256": digest(row),
        "state_fingerprint_sha256": digest(after),
        "audit_retained_on_rollback": True,
    }


def require_pair_registered(conn, value):
    pair = value["decision_subject"]
    rows = conn.execute(
        "SELECT * FROM public.editorial_bounded_choice_owner_decisions "
        "WHERE decision_jsonb->>'pair_subject_sha256'=%s",
        (pair["pair_subject_sha256"],),
    ).fetchall()
    review.require(len(rows) == 2, "both exact owner registrations are required")
    members = set()
    for row in rows:
        decision = row["decision_jsonb"]
        member = decision["member_id"]
        review.require(
            member in review.MEMBERS and member not in members,
            "registered pair member differs",
        )
        members.add(member)
        for field in [
            "semantic_subject_sha256",
            "presentation_subject_sha256",
            "rendering_subject_sha256",
        ]:
            review.require(
                decision[field] == pair["members"][member][field],
                "registered counterpart differs",
            )
        receipt = {
            **{k: decision[k] for k in owner.DECISION_FIELDS},
            "authority_evidence": {
                "kind": "owner_decision",
                "decision_id": row["decision_id"],
                "decision_sha256": row["decision_sha256"],
            },
        }
        review.require(
            digest(owner.require_trusted_decision(receipt)) == digest(row),
            "registered owner bytes differ",
        )


def require_publication_order(conn, value):
    rows = conn.execute(
        "SELECT r.*,a.payload_jsonb,a.content_sha256,a.editorial_status,"
        "a.benchmark_status,a.production_eligible,a.schema_version,a.artifact_version,"
        "a.natural_key,a.publication_basis FROM public.editorial_publication_registry r "
        "JOIN public.editorial_artifact_versions a USING(artifact_id) WHERE r.issue_id=%s "
        "AND r.member_bioguide_id IN ('F000477','M001184')",
        (review.ISSUE,),
    ).fetchall()
    if value["semantic"]["member_id"] == "F000477":
        review.require(not rows, "Foushee must be the first initial publication")
    else:
        review.require(
            len(rows) == 1
            and rows[0]["member_bioguide_id"] == "F000477"
            and publication.select_bounded_publication(
                rows[0], member_id="F000477", scope="119"
            )
            is not None
            and rows[0]["payload_jsonb"]["decision_subject"]
            == value["decision_subject"],
            "Massie requires the exact prior Foushee publication",
        )


def prepare_publication(conn, value, context, profile):
    observation = capture(conn, value, profile)
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        require_pair_registered(conn, value)
        require_publication_order(conn, value)
    writes = publication.build_write_set(
        value,
        preparation=context["preparation"],
        runtime=context["runtime"],
        baseline=observation["baseline"],
    )
    return review.seal(
        {
            "schema_version": "bounded_choice_publication_request_v1",
            "value": value,
            "write_set": writes,
            "target": observation["target"],
            "authorizing": False,
        },
        "request_sha256",
    )


def publish(conn, request, approval_id, runtime_proof, profile):
    check_publication_request(request)
    observation = capture(conn, request["value"], profile)
    review.require(
        digest(observation["target"]) == digest(request["target"]),
        "publication target differs",
    )
    approval = trusted_approval(approval_id, "publish", request["target"])
    utc_not_future(approval["subject"]["decision_recorded_at_utc"])
    if profile == "production-green":
        # Public health is observed here; it does not establish DB/alias binding.
        with urlopen(HEALTH_URL, timeout=10) as response:
            health = json.load(response)
        commit = health.get("commit_sha")
        runtime_proof = review.seal(
            {
                "schema_version": "publication_activation_runtime_execution_evidence_v2",
                "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                "healthy": health.get("status") == "ok",
                "deployed_commit": commit,
                "health_commit": commit,
                "current_runtime_manifest_sha256": digest(review.rendering_manifest()),
            },
            "runtime_health_proof_subject_sha256",
        )
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        require_pair_registered(conn, request["value"])
        require_publication_order(conn, request["value"])
    execution = publication.apply_initial(
        conn,
        value=request["value"],
        write_set=request["write_set"],
        authority=approval,
        runtime_proof=runtime_proof,
    )
    return {
        "operation": "publish",
        "request_sha256": request["request_sha256"],
        "execution": execution,
    }


def rollback(conn, request, approval_id, report, profile):
    check_publication_request(request)
    review.require(
        report["operation"] == "publish"
        and report["request_sha256"] == request["request_sha256"],
        "rollback execution request differs",
    )
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        target = target_identity(conn, profile)
    review.require(
        digest(target) == digest(request["target"]), "rollback target differs"
    )
    approval = trusted_approval(approval_id, "publish", target, fresh_bindings=False)
    validate_stable_positive_authority(
        approval, candidate=request["value"], write_set=request["write_set"]
    )
    publication.rollback_initial(
        conn,
        value=request["value"],
        write_set=request["write_set"],
        execution=report["execution"],
    )
    return {
        "operation": "rollback",
        "request_sha256": request["request_sha256"],
        "audit_evidence_deleted": False,
    }


def inspect_publication(conn, request, approval_id, profile):
    """Recover an exact execution report read-only after an uncertain CLI exit.

    Existing rollback still verifies restoration of the full approved baseline.
    A later member must be rolled back first; this is never an overwrite path.
    """
    check_publication_request(request)
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        target = target_identity(conn, profile)
        review.require(
            digest(target) == digest(request["target"]), "inspection target differs"
        )
        approval = trusted_approval(
            approval_id, "publish", target, fresh_bindings=False
        )
        validate_stable_positive_authority(
            approval, candidate=request["value"], write_set=request["write_set"]
        )
        execution = publication.verify_initial_state(
            conn,
            value=request["value"],
            write_set=request["write_set"],
            authority=approval,
        )
    return {
        "operation": "publish",
        "request_sha256": request["request_sha256"],
        "execution": execution,
    }


def check_publication_request(request):
    review.check_seal(request, "request_sha256")
    review.require(
        set(request)
        == {
            "schema_version",
            "value",
            "write_set",
            "target",
            "authorizing",
            "request_sha256",
        }
        and request["schema_version"] == "bounded_choice_publication_request_v1"
        and request["authorizing"] is False,
        "publication request differs",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=[
            "prepare-registration",
            "register",
            "prepare-publication",
            "publish",
            "rollback",
            "inspect-publication",
        ],
    )
    parser.add_argument("--target", choices=PROFILES, default="production-green")
    parser.add_argument("--candidate")
    parser.add_argument("--request")
    parser.add_argument("--context")
    parser.add_argument("--approval-id")
    parser.add_argument("--runtime-proof")
    parser.add_argument("--execution-report")
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    mutation = args.operation in {"register", "publish", "rollback"}
    if mutation and not args.confirm:
        parser.error(
            "explicit mutation confirmation and separate exact approval are required"
        )
    try:
        review.require(not Path(args.output).exists(), "output already exists")
        review.require(
            not any(os.getenv(k) for k in ROUTING_ENV),
            "inherited connection routing is forbidden",
        )
        dsn = os.environ["HEALTH_CHOICE_DATABASE_URL"]
        validate_route(conninfo_to_dict(dsn), args.target)
        value = read_json(args.candidate) if args.candidate else None
        request = read_json(args.request) if args.request else None
        review.require(
            not mutation or args.approval_id,
            "separate exact operator approval required",
        )
        with (
            Path(args.output).open("x", encoding="utf-8", newline="\n") as stream,
            psycopg.connect(
                dsn, autocommit=True, row_factory=dict_row, connect_timeout=10
            ) as conn,
        ):
            if args.operation == "prepare-registration":
                result = prepare_registration(conn, value, args.target)
            elif args.operation == "register":
                result = register(conn, request, args.approval_id, args.target)
            elif args.operation == "prepare-publication":
                result = prepare_publication(
                    conn, value, read_json(args.context), args.target
                )
            elif args.operation == "publish":
                result = publish(
                    conn,
                    request,
                    args.approval_id,
                    read_json(args.runtime_proof) if args.runtime_proof else None,
                    args.target,
                )
            elif args.operation == "rollback":
                result = rollback(
                    conn,
                    request,
                    args.approval_id,
                    read_json(args.execution_report),
                    args.target,
                )
            else:
                result = inspect_publication(
                    conn, request, args.approval_id, args.target
                )
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    except (ValueError, KeyError, TypeError, OSError, psycopg.Error):
        # Never print DSNs, libpq errors, approval quotes, or arbitrary input.
        parser.exit(
            1,
            "Health operator stopped; details withheld to protect credentials. Check state before retrying a mutation.\n",
        )
    return result


if __name__ == "__main__":
    main()
