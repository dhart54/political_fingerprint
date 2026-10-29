"""Offline HTTP parity through real query/selector code, with DB-API doubles.

These tests do not execute SQL or validate database publication eligibility.
Publication rows represent repository query results, not registry writes.
"""

from contextlib import nullcontext
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock, get_ident
import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app import db
from app.api import editorial_presentations, positions, precomputed
from app.main import app
from backend.tests.test_api_editorial_presentations import _approved_artifact, _row
from backend.tests.test_governed_receipt_projection import _presentation


MEMBER = "leg_valerie_p_foushee"
DOMAINS = ("JUSTICE_PUBLIC_SAFETY", "NATIONAL_SECURITY_FOREIGN",
           "ENVIRONMENT_ENERGY", "EDUCATION_WORKFORCE")


@pytest.fixture(scope="module")
def publication_fixture():
    # Reuse existing test-only approval fixtures; never mutate their source files.
    return _row(_approved_artifact()), _presentation()


def raw(action, position):
    chamber, congress, session, roll = action.split(":")
    return dict(roll_call_id=action, chamber=chamber, congress=int(congress),
                session=int(session), rollcall_number=int(roll), position=position,
                vote_date=f"{1789 + (int(congress) - 1) * 2}-02-06",
                question="Fixture question", description="Fixture description",
                classification_reason="eligible")


class DatabaseDouble:
    def __init__(self, publication_fixture, scope, state="active", barrier=None):
        row, presentation = deepcopy(publication_fixture)
        self.publications = [row] if state not in {"empty", "inactive"} else []
        if state == "mismatch":
            row["content_sha256"] = "0" * 64
        actions = {r["canonical_action_id"]: r["member_action"].lower().replace(" ", "_")
                   for r in presentation["exact_action_receipts"]}
        self.reviewed = [raw(a, actions.get(a, "nay")) for a in presentation["reviewed_action_ids"]]
        self.scope, self.state, self.barrier = scope, state, barrier
        self.trace, self.events, self.connections = [], [], []
        self.lock = Lock()

    def connect(self, kind):
        database = self

        class Connection:
            def __init__(self):
                self.kind, self.owner = kind, get_ident()
                self.closed = False
                self.rollbacks = self.cursor_closes = self.queries = 0

            def cursor(self):
                connection = self

                class Cursor:
                    def execute(self, query, params=()):
                        assert not connection.closed and connection.owner == get_ident()
                        connection.queries += 1
                        with database.lock:
                            database.trace.append((kind, query, params))
                            database.events.append(("query", connection))
                        rows = database.rows(kind, query, params)
                        self.description = [(key,) for key in rows[0]] if rows else []
                        self.values = [tuple(row.values()) for row in rows]
                        return self

                    def fetchall(self):
                        return deepcopy(self.values)

                    def close(self):
                        connection.cursor_closes += 1

                return Cursor()

            def execute(self, query, params=()):
                return self.cursor().execute(query, params)

            def rollback(self):
                assert not self.closed and self.owner == get_ident()
                self.rollbacks += 1

            def close(self):
                assert not self.closed and self.owner == get_ident()
                self.closed = True
                with database.lock:
                    database.events.append(("close", self))

        result = Connection()
        with self.lock:
            self.connections.append(result)
            self.events.append(("open", result))
        return result

    def rows(self, kind, query, params):
        if kind == "publication":
            assert "FROM editorial_publication_registry registry" in query
            if self.barrier:
                self.barrier.wait(timeout=5)
            if self.state == "publication_error":
                raise RuntimeError("private publication fault")
            return self.publications
        if self.state == "query_error":
            raise RuntimeError("private query fault")
        if "FROM legislators" in query:
            return [] if self.state == "missing" else [dict(id=1, bioguide_id="F000477",
                name_display="Valerie P. Foushee", chamber="house", state="NC", district="4", party="D")]
        if "SELECT classification_version" in query:
            return [{"classification_version": "v1"}]
        if "MIN(DATE(rc.vote_date))" in query:
            return [dict(window_start="2023-01-01", window_end="2026-12-31",
                         congresses=[118, 119], eligible_roll_call_count=20)]
        if "COUNT(*) AS vote_count" in query:
            return [{"domain": domain, "vote_count": 5} for domain in DOMAINS]
        if "AS yea_count" in query:
            return []  # Composed summaries below must replace these empty aggregates.
        if "rc.id AS roll_call_id" in query:
            if "governed_publication_evidence" in query:
                identities = [tuple(params[i:i + 4]) for i in range(1, len(params), 4)]
                return [r for r in self.reviewed if
                        (r["chamber"], r["congress"], r["session"], r["rollcall_number"]) in identities]
            assert params[1] in DOMAINS
            rows = [raw("house:118:1:9999", "not_voting"), raw("house:119:1:9999", "present")]
            if params[1] == "JUSTICE_PUBLIC_SAFETY":
                rows += self.reviewed[1:]  # One reviewed action requires the governed query.
            return sorted([r for r in rows if self.scope == "all" or r["congress"] == int(self.scope)],
                          key=lambda r: (r["vote_date"], r["rollcall_number"]))
        raise AssertionError(f"Unexpected query: {query}")

    def install(self, monkeypatch):
        monkeypatch.delenv("ENABLE_FIXTURE_FALLBACK", raising=False)
        monkeypatch.delenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW", raising=False)
        monkeypatch.setattr(precomputed, "get_connection", lambda: self.connect("precomputed"))
        monkeypatch.setattr(editorial_presentations, "get_connection", lambda: self.connect("publication"))

    def peak(self):
        active = peak = 0
        for event, _ in self.events:
            active += (event == "open") - (event == "close")
            peak = max(peak, active)
        assert active == 0
        return peak


@pytest.mark.parametrize("scope", ["118", "119", "all"])
@pytest.mark.parametrize("state", ["active", "inactive", "mismatch", "empty", "missing", "query_error", "publication_error"])
def test_populated_http_parity(monkeypatch, publication_fixture, scope, state):
    results = []
    for reuse in (False, True):
        database = DatabaseDouble(publication_fixture, scope, state)
        with monkeypatch.context() as patch:
            database.install(patch)
            patch.setattr(positions, "precomputed_read_scope", db.precomputed_read_scope if reuse else nullcontext)
            response = TestClient(app).get(f"/legislators/{MEMBER}/positions", params={"scope": scope})
        assert all(c.closed for c in database.connections)
        results.append((response, database))
    baseline, candidate = results
    assert candidate[0].status_code == baseline[0].status_code
    assert candidate[0].content == baseline[0].content
    assert candidate[0].headers == baseline[0].headers
    assert candidate[1].trace == baseline[1].trace
    expected_status = 404 if state == "missing" else 503 if "error" in state else 200
    assert candidate[0].status_code == expected_status, candidate[0].text
    assert "private" not in candidate[0].text
    pre = [c for c in candidate[1].connections if c.kind == "precomputed"]
    pub = [c for c in candidate[1].connections if c.kind == "publication"]
    assert len(pre) == (2 if expected_status == 200 else 1)
    if state != "query_error":
        assert all(c.rollbacks == c.queries == c.cursor_closes for c in pre)
    if state not in {"missing", "query_error"}:
        assert len(pub) == 1 and pub[0] is not pre[0] and pub[0].rollbacks == 0
        assert baseline[1].peak() == candidate[1].peak() == 1
        events = candidate[1].events
        assert events.index(("close", pre[0])) < events.index(("open", pub[0]))
        if len(pre) == 2:
            assert events.index(("close", pub[0])) < events.index(("open", pre[1]))
    if expected_status == 200:
        rows = {r["domain"]: r for r in candidate[0].json()["positions"]}
        assert all(rows[d]["total_votes"] > 0 for d in DOMAINS)
        for d in DOMAINS[1:]:
            assert rows[d]["recorded_votes"] == 0  # Present/Not Voting stay non-directional.
        justice = rows[DOMAINS[0]]
        if state == "active" and scope != "118":
            assert justice["reviewed_action_count"] == len(publication_fixture[1]["reviewed_action_ids"])
        else:
            assert justice["reviewed_action_count"] == 0


def test_overlapping_fastapi_workers_keep_separate_connections(monkeypatch, publication_fixture):
    database = DatabaseDouble(publication_fixture, "119", barrier=Barrier(2))
    database.install(monkeypatch)
    def request():
        return TestClient(app).get(f"/legislators/{MEMBER}/positions?scope=119")
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(request) for _ in range(2)]
        responses = [future.result(timeout=10) for future in futures]
    assert all(r.status_code == 200 for r in responses)
    assert responses[0].content == responses[1].content
    assert len(database.connections) == 6 and database.peak() == 2
    assert len({c.owner for c in database.connections}) == 2
    assert all(c.closed for c in database.connections)
    for owner in {c.owner for c in database.connections}:
        assert sorted(c.kind for c in database.connections if c.owner == owner) == ["precomputed", "precomputed", "publication"]


def test_cancelled_http_waiter_leaves_cleanup_with_worker(monkeypatch, publication_fixture):
    entered, release, done = Event(), Event(), Event()

    class Gate:
        def wait(self, timeout):
            entered.set()
            assert release.wait(timeout)

    database = DatabaseDouble(publication_fixture, "119", barrier=Gate())
    connect = database.connect

    def observed_connect(kind):
        connection = connect(kind)
        close = connection.close

        def observed_close():
            close()
            if kind == "precomputed" and len(database.connections) == 3:
                done.set()

        connection.close = observed_close
        return connection

    database.connect = observed_connect
    database.install(monkeypatch)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            task = asyncio.create_task(client.get(f"/legislators/{MEMBER}/positions?scope=119"))
            try:
                assert await asyncio.to_thread(entered.wait, 3)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
                assert len(database.connections) == 2
                assert database.connections[0].closed
                assert not database.connections[1].closed
            finally:
                release.set()
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            assert await asyncio.to_thread(done.wait, 5)
        assert all(c.closed for c in database.connections)
        assert database.peak() == 1
        assert all(c.rollbacks == c.queries for c in database.connections if c.kind == "precomputed")

    asyncio.run(scenario())
