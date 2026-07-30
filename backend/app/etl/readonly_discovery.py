from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence


APPLICATION_NAME = "political_fingerprint_readonly_universe_discovery"
STATEMENT_TIMEOUT_MS = 30_000
LOCK_TIMEOUT_MS = 2_000
IDLE_TRANSACTION_TIMEOUT_MS = 30_000
BEGIN_SQL = "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"
PROOF_QUERY_ID = "transaction_safety_proof"

_SPACE = re.compile(r"\s+")
_LINE_COMMENT = re.compile(r"--[^\r\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LEADING_READ = re.compile(r"^(select|with|show)\b", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b("
    r"insert|update|delete|merge|upsert|copy|create|alter|drop|truncate|"
    r"grant|revoke|lock|call|do|execute|prepare|vacuum|analyze|refresh|"
    r"cluster|reindex|comment|security\s+label|listen|notify|unlisten|"
    r"set|reset|nextval|setval|lo_import|lo_export|pg_advisory"
    r")\b",
    re.IGNORECASE,
)
_LOCKING_SELECT = re.compile(
    r"\bfor\s+(update|no\s+key\s+update|share|key\s+share)\b",
    re.IGNORECASE,
)
_FUNCTION_CALL = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\(", re.IGNORECASE)
_ALLOWED_FUNCTIONS = {
    "as",
    "count",
    "current_database",
    "current_schema",
    "current_setting",
    "date",
    "filter",
    "in",
    "lower",
    "max",
    "version",
}


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    purpose: str
    sql: str
    params: Sequence[Any] = ()
    parameter_schema: Sequence[str] = ()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def normalize_sql(sql: str) -> str:
    without_comments = _BLOCK_COMMENT.sub(" ", _LINE_COMMENT.sub(" ", sql))
    return _SPACE.sub(" ", without_comments).strip().rstrip(";").strip()


def validate_read_query(sql: str) -> str:
    normalized = normalize_sql(sql)
    if not normalized or not _LEADING_READ.match(normalized):
        raise ValueError("discovery SQL must begin with SELECT, WITH, or SHOW")
    if ";" in normalized:
        raise ValueError("discovery SQL must contain exactly one statement")
    if _FORBIDDEN.search(normalized):
        raise ValueError("discovery SQL contains a forbidden operation")
    if _LOCKING_SELECT.search(normalized):
        raise ValueError("locking SELECT statements are forbidden")
    function_names = {
        match.group(1).lower() for match in _FUNCTION_CALL.finditer(normalized)
    }
    disallowed_functions = sorted(function_names - _ALLOWED_FUNCTIONS)
    if disallowed_functions:
        raise ValueError(
            "discovery SQL contains non-allowlisted functions: "
            + ", ".join(disallowed_functions)
        )
    return normalized


def connect_read_only(dsn: str):
    from psycopg import connect
    from psycopg.rows import dict_row

    return connect(
        dsn,
        autocommit=True,
        row_factory=dict_row,
    )


class ReadOnlyDiscoverySession:
    def __init__(
        self,
        connection,
        *,
        expected_database_name: str,
        expected_server_prefix: str = "PostgreSQL ",
    ) -> None:
        self.connection = connection
        self.expected_database_name = expected_database_name
        self.expected_server_prefix = expected_server_prefix
        self.state = "connected"
        self.command_ids: list[str] = []
        self.audit: list[dict[str, Any]] = []
        self.rollback_attempted = False
        self.rollback_succeeded = False

    def begin(self) -> None:
        if self.state != "connected" or self.command_ids:
            raise RuntimeError("read-only BEGIN must be the first SQL command")
        started_at = _now()
        self.connection.execute(BEGIN_SQL)
        finished_at = _now()
        self.command_ids.append("transaction_begin")
        self.audit.append(
            _audit_record(
                query_id="transaction_begin",
                purpose=(
                    "Start the single explicit REPEATABLE READ READ ONLY "
                    "production snapshot transaction."
                ),
                sql=BEGIN_SQL,
                parameter_schema=(),
                started_at=started_at,
                finished_at=finished_at,
                rows=[],
                snapshot_started_at=started_at,
                bounded_timeout_ms=None,
            )
        )
        self.state = "begun"

    def prove(self, *, snapshot_started_at: str) -> dict[str, Any]:
        if self.state != "begun":
            raise RuntimeError("active transaction proof requires explicit read-only BEGIN")
        sql = """
        SELECT
            current_setting('default_transaction_read_only') AS default_read_only,
            current_setting('transaction_read_only') AS transaction_read_only,
            current_setting('transaction_isolation') AS transaction_isolation,
            current_database() AS database_name,
            current_schema() AS current_schema,
            version() AS postgres_version
        """
        started_at = _now()
        row = self.connection.execute(sql).fetchone()
        finished_at = _now()
        self.command_ids.append(PROOF_QUERY_ID)
        proof = dict(row)
        self.audit.append(
            _audit_record(
                query_id=PROOF_QUERY_ID,
                purpose=(
                    "Prove the active transaction is read-only and repeatable-read "
                    "and verify database/server identity."
                ),
                sql=sql,
                parameter_schema=(),
                started_at=started_at,
                finished_at=finished_at,
                rows=[proof],
                snapshot_started_at=snapshot_started_at,
                bounded_timeout_ms=None,
            )
        )
        if proof["transaction_read_only"] != "on":
            raise RuntimeError("server transaction is not read-only")
        if proof["transaction_isolation"].lower() != "repeatable read":
            raise RuntimeError("server transaction is not REPEATABLE READ")
        if proof["database_name"] != self.expected_database_name:
            raise RuntimeError("unexpected production database identity")
        if not str(proof["postgres_version"]).startswith(self.expected_server_prefix):
            raise RuntimeError("unexpected PostgreSQL server identity")
        if proof["current_schema"] != "public":
            raise RuntimeError("unexpected production schema identity")
        self.state = "proven"
        return proof

    def apply_local_controls(self, *, snapshot_started_at: str) -> None:
        if self.state != "proven":
            raise RuntimeError("transaction-local controls require a proven transaction")
        controls = [
            (
                "set_local_statement_timeout",
                "Apply the bounded statement timeout to this transaction only.",
                f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}ms'",
            ),
            (
                "set_local_lock_timeout",
                "Apply the bounded lock timeout to this transaction only.",
                f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT_MS}ms'",
            ),
            (
                "set_local_idle_timeout",
                "Apply the bounded idle-in-transaction timeout locally.",
                "SET LOCAL idle_in_transaction_session_timeout = "
                f"'{IDLE_TRANSACTION_TIMEOUT_MS}ms'",
            ),
            (
                "set_local_application_name",
                "Identify this discovery task for the current transaction only.",
                f"SET LOCAL application_name = '{APPLICATION_NAME}'",
            ),
        ]
        for query_id, purpose, sql in controls:
            started_at = _now()
            self.connection.execute(sql)
            finished_at = _now()
            self.command_ids.append(query_id)
            self.audit.append(
                _audit_record(
                    query_id=query_id,
                    purpose=purpose,
                    sql=sql,
                    parameter_schema=(),
                    started_at=started_at,
                    finished_at=finished_at,
                    rows=[],
                    snapshot_started_at=snapshot_started_at,
                )
            )
        self.state = "controlled"

    def execute(self, query: QuerySpec, *, snapshot_started_at: str):
        if self.state not in {"controlled", "querying"}:
            raise RuntimeError("data queries require a proven, controlled transaction")
        normalized = validate_read_query(query.sql)
        if len(query.params) != len(query.parameter_schema):
            raise ValueError(f"parameter schema mismatch for {query.query_id}")
        started_at = _now()
        rows = [
            dict(row)
            for row in self.connection.execute(
                query.sql, tuple(query.params)
            ).fetchall()
        ]
        finished_at = _now()
        self.command_ids.append(query.query_id)
        self.audit.append(
            _audit_record(
                query_id=query.query_id,
                purpose=query.purpose,
                sql=normalized,
                parameter_schema=query.parameter_schema,
                started_at=started_at,
                finished_at=finished_at,
                rows=rows,
                snapshot_started_at=snapshot_started_at,
            )
        )
        self.state = "querying"
        return rows

    def rollback(self) -> None:
        if self.rollback_attempted:
            return
        self.rollback_attempted = True
        try:
            if self.state != "connected":
                started_at = _now()
                self.connection.execute("ROLLBACK")
                finished_at = _now()
                self.command_ids.append("transaction_rollback")
                self.audit.append(
                    _audit_record(
                        query_id="transaction_rollback",
                        purpose=(
                            "Close the production discovery transaction without "
                            "retaining any database effect."
                        ),
                        sql="ROLLBACK",
                        parameter_schema=(),
                        started_at=started_at,
                        finished_at=finished_at,
                        rows=[],
                        snapshot_started_at=started_at,
                        bounded_timeout_ms=None,
                    )
                )
            self.rollback_succeeded = True
            self.state = "rolled_back"
        finally:
            if not self.rollback_succeeded:
                self.state = "rollback_failed"


def execute_query_pack(
    session: ReadOnlyDiscoverySession,
    queries: Iterable[QuerySpec],
    *,
    started_at: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}
    for query in queries:
        rows = session.execute(query, snapshot_started_at=started_at)
        results[query.query_id] = rows
    return results, list(session.audit)


def write_raw_snapshot(
    output_dir: Path,
    *,
    snapshot_id: str,
    proof: dict[str, Any],
    results: dict[str, list[dict[str, Any]]],
    audit: list[dict[str, Any]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{snapshot_id}.json"
    payload = {
        "snapshot_id": snapshot_id,
        "read_only_session_proof": proof,
        "query_audit": audit,
        "results": results,
    }
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def write_completion_record(
    output_dir: Path,
    *,
    snapshot_id: str,
    raw_snapshot_path: Path,
    results: dict[str, list[dict[str, Any]]],
    audit: list[dict[str, Any]],
    command_ids: Sequence[str],
    rollback_attempted: bool,
    rollback_succeeded: bool,
    connection_close_attempted: bool,
    connection_close_succeeded: bool,
    connection_closed_state_supported: bool,
    connection_closed_state_verified: bool,
) -> Path:
    """Write the post-close, digest-bound completion envelope for a snapshot."""
    result_digests = {
        key: sha256_json(value) for key, value in sorted(results.items())
    }
    data_query_ids = [
        row["query_id"]
        for row in audit
        if row["query_id"]
        not in {
            "transaction_begin",
            PROOF_QUERY_ID,
            "set_local_statement_timeout",
            "set_local_lock_timeout",
            "set_local_idle_timeout",
            "set_local_application_name",
            "transaction_rollback",
        }
    ]
    payload = {
        "schema_version": "readonly_discovery_completion_v1",
        "snapshot_id": snapshot_id,
        "first_sql_command": BEGIN_SQL,
        "final_data_query_id": data_query_ids[-1] if data_query_ids else None,
        "executed_query_ids": list(command_ids),
        "rollback": {
            "attempted": rollback_attempted,
            "succeeded": rollback_succeeded,
            "audit_query_id": "transaction_rollback",
        },
        "connection_close": {
            "attempted": connection_close_attempted,
            "succeeded": connection_close_succeeded,
            "client_closed_state_supported": connection_closed_state_supported,
            "client_closed_state_verified": connection_closed_state_verified,
        },
        "raw_snapshot": {
            "filename": raw_snapshot_path.name,
            "sha256": hashlib.sha256(raw_snapshot_path.read_bytes()).hexdigest(),
        },
        "result_digests": result_digests,
        "result_bundle_sha256": sha256_json(result_digests),
        "query_audit_sha256": sha256_json(audit),
        "completion_sequence": [
            "final_data_query_completed",
            "transaction_rollback_succeeded",
            "connection_close_succeeded",
            "client_closed_state_verified",
            "raw_snapshot_written",
            "completion_record_written",
        ],
        "completion_subject_sha256": "",
    }
    payload["completion_subject_sha256"] = sha256_json(
        {
            key: value
            for key, value in payload.items()
            if key != "completion_subject_sha256"
        }
    )
    path = output_dir / f"{snapshot_id}.completion.json"
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def validate_completion_record(
    raw_snapshot_path: Path,
    completion_record_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reject missing, false, malformed, substituted, or cross-run proof."""
    snapshot = json.loads(raw_snapshot_path.read_text(encoding="utf-8"))
    completion = json.loads(completion_record_path.read_text(encoding="utf-8"))
    required_sequence = [
        "final_data_query_completed",
        "transaction_rollback_succeeded",
        "connection_close_succeeded",
        "client_closed_state_verified",
        "raw_snapshot_written",
        "completion_record_written",
    ]
    control_query_ids = {
        "transaction_begin",
        PROOF_QUERY_ID,
        "set_local_statement_timeout",
        "set_local_lock_timeout",
        "set_local_idle_timeout",
        "set_local_application_name",
        "transaction_rollback",
    }
    data_query_ids = [
        row["query_id"]
        for row in snapshot.get("query_audit", [])
        if row["query_id"] not in control_query_ids
    ]
    checks = {
        "schema_version": (
            completion.get("schema_version")
            == "readonly_discovery_completion_v1"
        ),
        "snapshot_identity": (
            completion.get("snapshot_id") == snapshot.get("snapshot_id")
        ),
        "raw_filename": (
            completion.get("raw_snapshot", {}).get("filename")
            == raw_snapshot_path.name
        ),
        "raw_sha256": (
            completion.get("raw_snapshot", {}).get("sha256")
            == hashlib.sha256(raw_snapshot_path.read_bytes()).hexdigest()
        ),
        "first_sql_command": completion.get("first_sql_command") == BEGIN_SQL,
        "executed_query_ids": (
            completion.get("executed_query_ids")
            == [row["query_id"] for row in snapshot.get("query_audit", [])]
        ),
        "final_data_query_id": (
            bool(data_query_ids)
            and completion.get("final_data_query_id")
            == data_query_ids[-1]
        ),
        "rollback_audit_last": bool(snapshot.get("query_audit"))
        and snapshot["query_audit"][-1].get("query_id")
        == "transaction_rollback",
        "rollback_attempted": (
            completion.get("rollback", {}).get("attempted") is True
        ),
        "rollback_succeeded": (
            completion.get("rollback", {}).get("succeeded") is True
        ),
        "rollback_audit_query_id": (
            completion.get("rollback", {}).get("audit_query_id")
            == "transaction_rollback"
        ),
        "close_attempted": (
            completion.get("connection_close", {}).get("attempted") is True
        ),
        "close_succeeded": (
            completion.get("connection_close", {}).get("succeeded") is True
        ),
        "closed_state_supported": (
            completion.get("connection_close", {}).get(
                "client_closed_state_supported"
            )
            is True
        ),
        "closed_state_verified": (
            completion.get("connection_close", {}).get(
                "client_closed_state_verified"
            )
            is True
        ),
        "result_digests": completion.get("result_digests")
        == {
            key: sha256_json(value)
            for key, value in sorted(snapshot.get("results", {}).items())
        },
        "query_audit_sha256": (
            completion.get("query_audit_sha256")
            == sha256_json(snapshot.get("query_audit", []))
        ),
        "completion_sequence": (
            completion.get("completion_sequence") == required_sequence
        ),
        "completion_subject_sha256": (
            completion.get("completion_subject_sha256")
            == sha256_json(
                {
                    key: value
                    for key, value in completion.items()
                    if key != "completion_subject_sha256"
                }
            )
        ),
    }
    if completion.get("result_digests") is not None:
        checks["result_bundle_sha256"] = (
            completion.get("result_bundle_sha256")
            == sha256_json(completion["result_digests"])
        )
    failed = sorted(key for key, value in checks.items() if not value)
    if failed:
        raise ValueError(
            "invalid read-only completion record: " + ", ".join(failed)
        )
    return snapshot, completion


def sanitized_session_proof(proof: dict[str, Any]) -> dict[str, Any]:
    database_identity = hashlib.sha256(
        str(proof["database_name"]).encode("utf-8")
    ).hexdigest()
    version = str(proof["postgres_version"]).split(",", 1)[0]
    return {
        "default_transaction_read_only": proof["default_read_only"],
        "transaction_read_only": proof["transaction_read_only"],
        "transaction_isolation": proof["transaction_isolation"],
        "statement_timeout_ms": STATEMENT_TIMEOUT_MS,
        "lock_timeout_ms": LOCK_TIMEOUT_MS,
        "idle_in_transaction_session_timeout_ms": IDLE_TRANSACTION_TIMEOUT_MS,
        "application_name": APPLICATION_NAME,
        "database_identity_sha256": database_identity,
        "schema": proof["current_schema"],
        "postgres_version": version,
    }


def _audit_record(
    *,
    query_id: str,
    purpose: str,
    sql: str,
    parameter_schema: Sequence[str],
    started_at: str,
    finished_at: str,
    rows: list[dict[str, Any]],
    snapshot_started_at: str,
    bounded_timeout_ms: int | None = STATEMENT_TIMEOUT_MS,
) -> dict[str, Any]:
    normalized = normalize_sql(sql)
    return {
        "query_id": query_id,
        "purpose": purpose,
        "normalized_query_sha256": hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest(),
        "parameter_schema": list(parameter_schema),
        "started_at": started_at,
        "finished_at": finished_at,
        "bounded_timeout_ms": bounded_timeout_ms,
        "row_count": len(rows),
        "result_set_sha256": sha256_json(rows),
        "snapshot_started_at": snapshot_started_at,
    }


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")
