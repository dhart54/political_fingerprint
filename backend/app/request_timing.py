"""Bounded, non-identifying diagnostics through the existing Uvicorn handler.

Stage durations are cumulative call wall time, not database CPU time. Composition
is inclusive (overlaps DB stages); neither its sum nor request wall time is TTFB.
Only the four named public handlers emit, and no request values are serialized.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import json
import logging
from threading import Lock
from time import perf_counter


_current = ContextVar("request_timing", default=None)
_logger = logging.getLogger("uvicorn.error")
_STAGES = frozenset({
    "connection_ms", "execute_ms", "fetch_ms", "row_conversion_ms",
    "composition_ms",
})
_FAMILIES = {
    "legislator_profile": "profile",
    "get_legislator_positions": "positions",
    "get_editorial_presentations": "presentation",
    "get_legislator_position_evidence": "evidence",
}


class RequestTiming:
    def __init__(self):
        self.started = perf_counter()
        self.lock = Lock()
        self.closed = False
        self.durations = {}

    def begin(self):
        with self.lock:
            return None if self.closed else perf_counter()

    def end(self, stage, started):
        if started is None:
            return
        with self.lock:
            if not self.closed:
                self.durations[stage] = self.durations.get(stage, 0.0) + (perf_counter() - started) * 1000

    def finish(self, scope, *, aborted):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            family = _FAMILIES.get(getattr(scope.get("endpoint"), "__name__", ""))
            if family is None:
                return
            durations = dict(self.durations)
            label = "request_aborted_wall_ms" if aborted else "request_wall_ms"
            durations[label] = (perf_counter() - self.started) * 1000
            record = {family: {key: round(value, 3) for key, value in durations.items()}}
        try:
            # Reuse the configured diagnostic handler, never the access formatter.
            _logger.info("request_timing %s", json.dumps(record, sort_keys=True))
        except Exception:
            # Diagnostics cannot replace the application's result or exception.
            pass


@contextmanager
def timing_stage(stage):
    if stage not in _STAGES:
        raise ValueError("Unknown timing stage")
    timing = _current.get()
    started = timing.begin() if timing is not None else None
    try:
        yield
    finally:
        if timing is not None:
            timing.end(stage, started)


def timed_composition(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with timing_stage("composition_ms"):
            return function(*args, **kwargs)
    return wrapped


class RequestTimingMiddleware:
    """ASGI scope owns one accumulator, shared with copied sync-worker contexts.

    Close at final body delivery or abnormal exit. A worker outliving cancellation
    retains only a closed object; it cannot add samples or emit a second record.
    No response headers, status, body or cancellation semantics are changed.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        timing = RequestTiming()
        token = _current.set(timing)

        async def timed_send(message):
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                timing.finish(scope, aborted=False)

        try:
            await self.app(scope, receive, timed_send)
        finally:
            try:
                timing.finish(scope, aborted=True)
            finally:
                _current.reset(token)
