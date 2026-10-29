"""Owned real-SQL HTTP experiment; never connects through application settings.

Legislative tables use existing migrations. Editorial tables use the unchanged
DDL/index prefix of 0016; this tests selector SQL, not RLS/immutability/migration
deployment. Justice uses existing test-only approval fixtures. Other domains
have populated raw votes, not invented publication authority.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from copy import deepcopy
import json
import os
from pathlib import Path
from threading import Barrier, Event, Lock, get_ident
from time import perf_counter

import httpx
import pytest
from fastapi.testclient import TestClient
from psycopg import IsolationLevel
from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

from app import db
from app.api import editorial_presentations, positions, precomputed
from app.main import app
from backend.tests.positions_disposable_postgres import DisposablePostgres
from backend.tests.test_positions_read_scope_http import (
    DatabaseDouble, DOMAINS, MEMBER, _approved_artifact, _presentation, _row, raw,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / ".tmp/positions-reuse/real-route-2026-10-29"
pytestmark = pytest.mark.skipif(os.getenv("RUN_POSITIONS_DISPOSABLE") != "1",
                               reason="explicit owned local PostgreSQL opt-in required")


@pytest.fixture(scope="module")
def postgres():
    records = []
    server = DisposablePostgres(EVIDENCE)
    try:
        with server:
            with server.connect() as connection:
                connection.autocommit = True
                for name in ("0001_initial_schema.sql", "0002_vote_interpretations.sql",
                             "0003_vote_interpretation_details.sql", "0008_vote_contexts.sql",
                             "0009_vote_interpretation_so_what_fields.sql", "0010_senate_amendment_references.sql"):
                    connection.execute((ROOT / "backend/migrations" / name).read_text(encoding="utf-8-sig"))
                ddl = (ROOT / "backend/migrations/0016_editorial_artifact_persistence.sql").read_text()
                connection.execute(ddl.split("CREATE FUNCTION public.guard_editorial_artifact_immutability()")[0] + "COMMIT;")
            fixture = (_row(_approved_artifact()), _presentation())
            seed(server, fixture)
            yield server, fixture, records
    finally:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        stopped = not (server.directory / "postmaster.pid").exists()
        (EVIDENCE / "latest-results.json").write_text(json.dumps({
            "cluster": str(server.directory), "server_stopped": stopped,
            "observations": records,
        }, indent=2), encoding="utf-8")
        assert stopped


def seed(server, fixture):
    publication, presentation = fixture
    model = DatabaseDouble(fixture, "all")
    rows = [(DOMAINS[0], r) for r in model.reviewed]
    for i, domain in enumerate(DOMAINS):
        rows += [(domain, raw(f"house:{congress}:1:{9000 + i}", position))
                 for congress, position in ((118, "not_voting"), (119, "present"))]
    with server.connect() as connection:
        connection.execute("INSERT INTO legislators (id, bioguide_id, name_display, chamber, state, district, party) VALUES (1, 'F000477', 'Valerie P. Foushee', 'house', 'NC', '4', 'D')")
        connection.execute("INSERT INTO legislators (id, bioguide_id, name_display, chamber, state, party) VALUES (2, 'X000001', 'Fixture Member', 'senate', 'NC', 'D')")
        for i, (domain, row) in enumerate(rows, 1):
            connection.execute("INSERT INTO roll_calls (id, chamber, congress, session, rollcall_number, vote_date, question, description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (i, row["chamber"], row["congress"], row["session"], row["rollcall_number"], row["vote_date"], row["question"], row["description"]))
            connection.execute("INSERT INTO votes_cast (roll_call_id, legislator_id, position) VALUES (%s,1,%s),(%s,2,%s)", (i, row["position"], i, row["position"]))
            if i != 1:  # Exact reviewed action absent from the classified selection.
                connection.execute("INSERT INTO vote_classifications (roll_call_id,is_eligible,eligibility_reason,primary_domain,classification_version) VALUES (%s,true,'fixture',%s,'v1')", (i, domain))
        connection.execute("INSERT INTO editorial_artifact_batches (batch_id,deterministic_batch_key,source_commit_sha,manifest_sha256,status,artifact_count,relationship_count) VALUES (1,'local-route-fixture',%s,%s,'applied',3,2)", ("0" * 40, "0" * 64))
        identity = publication["payload_jsonb"]["artifact_identity"]
        artifacts = [
            (101, "issue_public_presentation", identity["artifact_id"], publication["schema_version"], publication["payload_jsonb"], publication["content_sha256"], True),
            (102, "standardization_validation_result", "local-validation", "editorial_publication_validation_v1", {}, "a" * 64, False),
            (103, "source_manifest", "local-source", "editorial_publication_source_manifest_v1", {}, "b" * 64, False),
        ]
        for artifact_id, kind, key, schema, payload, digest, eligible in artifacts:
            connection.execute("INSERT INTO editorial_artifact_versions (artifact_id,artifact_type,natural_key,schema_version,artifact_version,payload_jsonb,content_sha256,source_commit_sha,batch_id,editorial_status,benchmark_status,production_eligible,review_route) VALUES (%s,%s,%s,%s,1,%s,%s,%s,1,'human_approved',%s,%s,'standard_generation')",
                (artifact_id, kind, key, schema, Jsonb(payload), digest, "0" * 40, "gold_benchmark" if eligible else "not_promoted", eligible))
        relationship = {"activation_bundle_id": "local-route-fixture"}
        metadata = {**deepcopy(publication["publication_metadata_jsonb"]),
            "presentation_natural_key": identity["artifact_id"], "presentation_artifact_version": 1,
            "active_artifact_sha256": publication["content_sha256"],
            "validation_natural_key": "local-validation", "validation_artifact_version": 1,
            "validation_content_sha256": "a" * 64, "source_manifest_natural_key": "local-source",
            "source_manifest_artifact_version": 1, "source_manifest_content_sha256": "b" * 64,
            "relationship_metadata": relationship}
        connection.execute("INSERT INTO editorial_publication_registry (member_bioguide_id,issue_id,artifact_id,publicly_active,activated_at,publication_metadata_jsonb) VALUES ('F000477','JUSTICE_PUBLIC_SAFETY',101,true,now(),%s)", (Jsonb(metadata),))
        for child, kind in ((102, "has_validation"), (103, "uses_source_manifest")):
            connection.execute("INSERT INTO editorial_artifact_relationships VALUES (101,%s,%s,0,%s)", (child, kind, Jsonb(relationship)))
    server.fixture_metadata = metadata


class Trace:
    def __init__(self, server, mode, isolation=IsolationLevel.READ_COMMITTED, gate=None, fault=None):
        self.server, self.mode, self.isolation = server, mode, isolation
        self.gate, self.fault = gate, fault
        self.connections, self.queries, self.events = [], [], []
        self.lock = Lock()
        self.done = Event()

    def connect(self, kind):
        trace = self
        raw_connection = self.server.connect()
        raw_connection.isolation_level = self.isolation

        class Connection:
            def __init__(self):
                self.kind, self.owner = kind, get_ident()
                self.opened, self.closed_at = perf_counter(), None
                self.raw = raw_connection
                self.rollbacks = self.reads = self.cursor_closes = 0

            def cursor(self):
                connection = self
                cursor = self.raw.cursor()

                class Cursor:
                    @property
                    def description(self):
                        return cursor.description

                    def execute(self, query, params=()):
                        assert connection.owner == get_ident() and not connection.raw.closed
                        assert connection.raw.info.transaction_status == TransactionStatus.IDLE
                        connection.reads += 1
                        with trace.lock:
                            trace.queries.append((kind, query, params))
                        if kind == "publication" and trace.gate:
                            trace.gate.wait(timeout=5)
                        late_fault = (trace.fault == "late_precomputed" and kind == "precomputed"
                                      and any(c.kind == "publication" for c in trace.connections))
                        if trace.fault == kind or late_fault:
                            cursor.execute("SELECT 1 / 0")  # Real server-side query error.
                        cursor.execute(query, params)
                        return self

                    def fetchall(self):
                        result = cursor.fetchall()
                        assert connection.raw.info.transaction_status == TransactionStatus.INTRANS
                        return result

                    def close(self):
                        cursor.close()
                        connection.cursor_closes += 1

                return Cursor()

            def execute(self, query, params=()):
                return self.cursor().execute(query, params)

            def rollback(self):
                self.raw.rollback()
                assert self.raw.info.transaction_status == TransactionStatus.IDLE
                self.rollbacks += 1

            def close(self):
                assert self.owner == get_ident() and self.closed_at is None
                self.raw.close()
                self.closed_at = perf_counter()
                with trace.lock:
                    trace.events.append((self.closed_at, -1))
                trace.done.set()

        result = Connection()
        with self.lock:
            self.connections.append(result)
            self.events.append((result.opened, 1))
        return result

    def install(self, patch):
        patch.delenv("ENABLE_FIXTURE_FALLBACK", raising=False)
        patch.delenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", raising=False)
        patch.setattr(precomputed, "get_connection", lambda: self.connect("precomputed"))
        patch.setattr(editorial_presentations, "get_connection", lambda: self.connect("publication"))
        patch.setattr(positions, "precomputed_read_scope", nullcontext if self.mode == "fresh" else db.precomputed_read_scope)
        patch.setattr(positions, "release_precomputed_read_connection",
                      db.release_precomputed_read_connection if self.mode == "release" else lambda: None)

    def summary(self):
        assert all(c.raw.closed and c.closed_at is not None for c in self.connections)
        active = peak = 0
        for _, delta in sorted(self.events):
            active += delta
            peak = max(peak, active)
        assert active == 0
        return {"mode": self.mode, "queries": len(self.queries), "peak": peak,
                "opens": len(self.connections), "connections": [
                    {"kind": c.kind, "hold_ms": (c.closed_at - c.opened) * 1000,
                     "reads": c.reads, "rollbacks": c.rollbacks} for c in self.connections]}


def request(scope="119", member=MEMBER):
    return TestClient(app).get(f"/legislators/{member}/positions", params={"scope": scope})


@pytest.mark.parametrize("scope", ["118", "119", "all"])
@pytest.mark.parametrize("state", ["active", "inactive", "mismatch"])
def test_populated_real_sql_parity(postgres, monkeypatch, scope, state):
    server, fixture, records = postgres
    metadata = deepcopy(server.fixture_metadata)
    if state == "mismatch":
        metadata["validation_content_sha256"] = "c" * 64
    with server.connect() as setup:
        setup.execute("UPDATE editorial_publication_registry SET deactivated_at = CASE WHEN %s THEN now() ELSE NULL END, publication_metadata_jsonb=%s", (state == "inactive", Jsonb(metadata)))
    results = []
    try:
        for mode in ("fresh", "held", "release"):
            trace = Trace(server, mode)
            with monkeypatch.context() as patch:
                trace.install(patch)
                response = request(scope)
            assert response.status_code == 200, response.text
            summary = trace.summary()
            records.append({"test": "parity", "scope": scope, "state": state, **summary})
            assert summary["peak"] == (2 if mode == "held" else 1)
            assert summary["opens"] == (len(trace.queries) if mode == "fresh" else 2 if mode == "held" else 3)
            for connection in trace.connections:
                if mode != "fresh" and connection.kind == "precomputed":
                    assert connection.rollbacks == connection.reads == connection.cursor_closes
            results.append((response, trace.queries))
        for result in results[1:]:
            assert result[0].content == results[0][0].content
            assert result[0].headers == results[0][0].headers
            assert result[1] == results[0][1]
        rows = {r["domain"]: r for r in results[-1][0].json()["positions"]}
        assert all(rows[d]["total_votes"] > 0 for d in DOMAINS)
        assert all(rows[d]["recorded_votes"] == 0 for d in DOMAINS[1:])
        expected = len(fixture[1]["reviewed_action_ids"]) if state == "active" and scope != "118" else 0
        assert rows[DOMAINS[0]]["reviewed_action_count"] == expected
    finally:
        with server.connect() as setup:
            setup.execute("UPDATE editorial_publication_registry SET deactivated_at=NULL,publication_metadata_jsonb=%s", (Jsonb(server.fixture_metadata),))


@pytest.mark.parametrize("mode", ["fresh", "held", "release"])
@pytest.mark.parametrize("fault", ["precomputed", "late_precomputed", "publication", "missing"])
def test_real_sql_failures_close_connections(postgres, monkeypatch, mode, fault):
    server, _, records = postgres
    trace = Trace(server, mode, fault=fault)
    trace.install(monkeypatch)
    response = request(member="not-a-member" if fault == "missing" else MEMBER)
    assert response.status_code == (404 if fault == "missing" else 503)
    assert response.json() == {"detail": "Legislator not found" if fault == "missing" else "Public record data is unavailable right now."}
    records.append({"test": "failure", "fault": fault, **trace.summary()})


@pytest.mark.parametrize("mode", ["fresh", "held", "release"])
def test_two_real_sql_http_workers(postgres, monkeypatch, mode):
    server, _, records = postgres
    trace = Trace(server, mode, gate=Barrier(2))
    trace.install(monkeypatch)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(request) for _ in range(2)]
        responses = [f.result(timeout=15) for f in futures]
    assert responses[0].status_code == responses[1].status_code == 200
    assert responses[0].content == responses[1].content
    summary = trace.summary()
    assert summary["peak"] == (4 if mode == "held" else 2)
    assert len({c.owner for c in trace.connections}) == 2
    records.append({"test": "two_workers", **summary})


@pytest.mark.parametrize("isolation", [IsolationLevel.READ_COMMITTED, IsolationLevel.REPEATABLE_READ])
def test_release_route_keeps_transaction_boundaries(postgres, monkeypatch, isolation):
    server, _, records = postgres
    trace = Trace(server, "release", isolation=isolation)
    trace.install(monkeypatch)
    assert request().status_code == 200
    for connection in trace.connections:
        assert connection.raw.isolation_level == isolation
        assert connection.raw.autocommit is False
    records.append({"test": "isolation", "isolation": isolation.name, **trace.summary()})


def test_real_sql_cancelled_waiter_keeps_worker_ownership(postgres, monkeypatch):
    server, _, records = postgres
    entered, release = Event(), Event()

    class Gate:
        def wait(self, timeout):
            entered.set()
            assert release.wait(timeout)

    trace = Trace(server, "release", gate=Gate())
    trace.install(monkeypatch)
    # Observe end-of-worker separately from the first pre-publication close.
    completed = Event()
    original = positions._get_legislator_positions

    def observed(*args):
        try:
            return original(*args)
        finally:
            completed.set()

    monkeypatch.setattr(positions, "_get_legislator_positions", observed)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            task = asyncio.create_task(client.get(f"/legislators/{MEMBER}/positions?scope=119"))
            try:
                assert await asyncio.to_thread(entered.wait, 3)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
                assert sum(not c.raw.closed for c in trace.connections) == 1
                assert trace.connections[0].raw.closed
            finally:
                release.set()
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            assert await asyncio.to_thread(completed.wait, 5)
            # The outer scope's final close follows the inner handler's finally.
            for _ in range(100):
                if all(c.raw.closed for c in trace.connections):
                    break
                await asyncio.sleep(0.01)
        records.append({"test": "cancellation", **trace.summary()})

    asyncio.run(scenario())
