"""Offline timing/privacy contracts; no network, database, or performance load."""

import asyncio
from contextvars import copy_context
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app import db, request_timing as timing
from app.api import precomputed
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.main import app


class Clock:
    value = 0.0

    def __call__(self):
        return self.value

    def advance(self, milliseconds):
        self.value += milliseconds / 1000


@pytest.fixture
def capture(monkeypatch):
    records = []
    monkeypatch.setattr(timing._logger, "info", lambda message, payload: records.append(json.loads(payload)))
    return records


@pytest.fixture
def clock(monkeypatch):
    value = Clock()
    monkeypatch.setattr(timing, "perf_counter", value)
    return value


def scope(name="get_legislator_positions"):
    return {"type": "http", "endpoint": SimpleNamespace(__name__=name),
            "path": "/private-member-id", "query_string": b"q=private-search",
            "headers": [(b"authorization", b"private-token")]}


async def receive():
    return {"type": "http.request", "body": b"private-body"}


def run(application, request_scope=None, send=None):
    messages = []

    async def collect(message):
        messages.append(message)

    asyncio.run(timing.RequestTimingMiddleware(application)(request_scope or scope(), receive, send or collect))
    assert timing._current.get() is None
    return messages


def test_stages_and_final_body_clock_have_explicit_nonadditive_semantics(clock, capture):
    async def application(request_scope, receive, send):
        with timing.timing_stage("composition_ms"):
            for stage, duration in [("connection_ms", 2), ("execute_ms", 3),
                                    ("execute_ms", 4), ("fetch_ms", 5), ("row_conversion_ms", 6)]:
                with timing.timing_stage(stage):
                    clock.advance(duration)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"first", "more_body": True})
        clock.advance(7)
        await send({"type": "http.response.body", "body": b"last"})
        clock.advance(100)  # Work after final delivery is outside the response clock.
        with timing.timing_stage("execute_ms"):
            clock.advance(100)

    messages = run(application)
    assert len(messages) == 3
    assert capture == [{"positions": {"connection_ms": 2, "execute_ms": 7,
        "fetch_ms": 5, "row_conversion_ms": 6, "composition_ms": 20, "request_wall_ms": 27}}]


def test_send_wait_is_included_and_headers_body_are_unchanged(clock, capture):
    supplied = [{"type": "http.response.start", "status": 201, "headers": [(b"x-test", b"kept")]},
                {"type": "http.response.body", "body": b"unchanged"}]
    delivered = []

    async def application(request_scope, receive, send):
        for message in supplied:
            await send(message)

    async def send(message):
        clock.advance(3)
        delivered.append(message)

    run(application, send=send)
    assert delivered == supplied
    assert capture == [{"positions": {"request_wall_ms": 6}}]


@pytest.mark.parametrize("exception", [RuntimeError("private-error"), asyncio.CancelledError()])
def test_error_and_cancellation_close_reset_and_preserve_exception(clock, capture, exception):
    retained = []

    async def application(request_scope, receive, send):
        retained.append(copy_context())
        with timing.timing_stage("execute_ms"):
            clock.advance(9)
            raise exception

    with pytest.raises(type(exception)) as caught:
        run(application)
    assert caught.value is exception
    assert timing._current.get() is None
    record = capture.copy()

    def late_work():
        with timing.timing_stage("execute_ms"):
            clock.advance(50)
        timing._current.get().finish(scope(), aborted=False)

    retained[0].run(late_work)
    assert capture == record == [{"positions": {"execute_ms": 9, "request_aborted_wall_ms": 9}}]


def test_inflight_worker_cannot_record_after_request_closes(clock, capture):
    async def scenario():
        started = asyncio.Event()
        release = asyncio.Event()

        async def worker():
            with timing.timing_stage("execute_ms"):
                started.set()
                await release.wait()
                clock.advance(100)

        async def application(request_scope, receive, send):
            task = asyncio.create_task(worker())
            await started.wait()
            await send({"type": "http.response.body", "body": b"done"})
            release.set()
            await task

        async def send(message):
            pass

        await timing.RequestTimingMiddleware(application)(scope(), receive, send)
        assert timing._current.get() is None

    asyncio.run(scenario())
    assert capture == [{"positions": {"request_wall_ms": 0}}]


def test_concurrent_requests_and_copied_sync_worker_contexts_are_isolated(capture):
    async def scenario():
        ready = [asyncio.Event(), asyncio.Event()]
        accumulators = []

        def sync_stage(stage):
            accumulators.append(timing._current.get())
            with timing.timing_stage(stage):
                pass

        async def application(request_scope, receive, send):
            index = request_scope["test_index"]
            ready[index].set()
            await ready[1 - index].wait()
            await asyncio.to_thread(sync_stage, ["execute_ms", "fetch_ms"][index])
            await send({"type": "http.response.body", "body": b"ok"})

        async def send(message):
            pass

        await asyncio.gather(*(timing.RequestTimingMiddleware(application)(
            {**scope(name), "test_index": index}, receive, send)
            for index, name in enumerate(["get_legislator_positions", "get_editorial_presentations"])))
        assert timing._current.get() is None
        assert len({id(item) for item in accumulators}) == 2

    asyncio.run(scenario())
    assert len(capture) == 2
    by_family = {key: value for record in capture for key, value in record.items()}
    assert set(by_family["positions"]) == {"execute_ms", "request_wall_ms"}
    assert set(by_family["presentation"]) == {"fetch_ms", "request_wall_ms"}


def test_cancelled_request_closes_while_real_sync_worker_is_still_running(capture):
    from threading import Event

    worker_started, release_worker, worker_done = Event(), Event(), Event()
    retained = []

    def worker():
        retained.append(timing._current.get())
        try:
            with timing.timing_stage("execute_ms"):
                worker_started.set()
                assert release_worker.wait(5)
        finally:
            worker_done.set()

    async def scenario():
        async def application(request_scope, receive, send):
            await asyncio.to_thread(worker)

        async def send(message):
            pass

        task = asyncio.create_task(timing.RequestTimingMiddleware(application)(scope(), receive, send))
        try:
            assert await asyncio.to_thread(worker_started.wait, 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert len(capture) == 1
            assert set(capture[0]["positions"]) == {"request_aborted_wall_ms"}
            assert retained[0].closed
        finally:
            release_worker.set()
            assert await asyncio.to_thread(worker_done.wait, 5)
        assert retained[0].durations == {}
        assert timing._current.get() is None

    asyncio.run(scenario())
    assert len(capture) == 1


def test_send_failure_is_aborted_and_original_failure_survives(clock, capture):
    failure = OSError("private-transport-error")

    async def application(request_scope, receive, send):
        await send({"type": "http.response.body", "body": b"private-body"})

    async def send(message):
        clock.advance(2)
        raise failure

    with pytest.raises(OSError) as caught:
        run(application, send=send)
    assert caught.value is failure
    assert capture == [{"positions": {"request_aborted_wall_ms": 2}}]


def test_logger_failure_does_not_change_success_or_error(monkeypatch):
    monkeypatch.setattr(timing._logger, "info", Mock(side_effect=RuntimeError("logging unavailable")))

    async def success(request_scope, receive, send):
        await send({"type": "http.response.body", "body": b"ok"})

    assert run(success)[0]["body"] == b"ok"

    async def failure(request_scope, receive, send):
        raise ValueError("original failure")

    with pytest.raises(ValueError, match="original failure"):
        run(failure)


@pytest.mark.parametrize("name,family", list(timing._FAMILIES.items()))
def test_finite_families_only_no_request_values(name, family, capture, clock):
    async def application(request_scope, receive, send):
        await receive()
        await send({"type": "http.response.body", "body": b"private-response"})

    run(application, scope(name))
    assert capture == [{family: {"request_wall_ms": 0}}]


def test_unknown_endpoint_and_non_http_do_not_emit(capture):
    async def application(request_scope, receive, send):
        return None

    run(application, scope("private-endpoint-name"))
    run(application, {"type": "lifespan"})
    assert capture == []


@pytest.mark.parametrize("repository", [False, True])
def test_real_read_helpers_measure_execute_fetch_conversion_without_sql_or_values(monkeypatch, clock, capture, repository):
    class Cursor:
        description = [("private-column",)]

        def execute(self, *args):
            clock.advance(2)
            return self

        def fetchall(self):
            clock.advance(3)
            return [("private-row",)]

        def cursor(self):
            return self

        def close(self):
            pass

    monkeypatch.setattr(precomputed, "get_connection", Cursor)

    async def application(request_scope, receive, send):
        rows = (EditorialArtifactRepository(Cursor())._all("private-sql", ("private-param",))
                if repository else precomputed._query_all_dicts("private-sql", ("private-param",)))
        assert rows == [{"private-column": "private-row"}]
        await send({"type": "http.response.body", "body": b"ok"})

    run(application)
    assert capture == [{"positions": {"execute_ms": 2, "fetch_ms": 3,
                                      "row_conversion_ms": 0, "request_wall_ms": 5}}]


def test_real_connection_boundary_does_not_log_dsn(monkeypatch, clock, capture):
    import psycopg

    def connect(dsn):
        assert dsn == "private-dsn"
        clock.advance(4)
        return "connection"

    monkeypatch.setattr(psycopg, "connect", connect)

    async def application(request_scope, receive, send):
        assert db.psycopg_connect("private-dsn") == "connection"
        await send({"type": "http.response.body", "body": b"ok"})

    run(application)
    assert capture == [{"positions": {"connection_ms": 4, "request_wall_ms": 4}}]


def test_actual_sync_route_logging_and_response_parity(monkeypatch, caplog, clock):
    def read_profile(*args):
        with timing.timing_stage("execute_ms"):
            clock.advance(2)
        return None

    monkeypatch.setattr(precomputed, "_get_db_legislator_by_external_id", read_profile)
    monkeypatch.delenv("ENABLE_FIXTURE_FALLBACK", raising=False)
    with caplog.at_level("INFO", logger="uvicorn.error"):
        response = TestClient(app).get("/legislators/private-member-id/profile?q=private-search")
    assert response.status_code == 404
    assert response.json() == {"detail": "Legislator not found"}
    assert "server-timing" not in response.headers
    records = [record.getMessage() for record in caplog.records if record.name == "uvicorn.error"]
    assert len(records) == 1
    assert records[0] == 'request_timing {"profile": {"execute_ms": 2.0, "request_wall_ms": 2.0}}'
    assert "private" not in records[0]
