import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from threading import get_ident
from typing import TYPE_CHECKING, Iterator
from dotenv import load_dotenv
from app.request_timing import timing_stage

if TYPE_CHECKING:
    from psycopg import Connection


load_dotenv()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")
    return database_url


@dataclass(frozen=True)
class Database:
    dsn: str

    def connect(self) -> "Connection":
        return psycopg_connect(self.dsn)

    @contextmanager
    def connection(self) -> Iterator["Connection"]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()


def get_database() -> Database:
    return Database(dsn=get_database_url())


def get_connection() -> "Connection":
    return get_database().connect()


def psycopg_connect(dsn: str) -> "Connection":
    from psycopg import connect

    with timing_stage("connection_ms"):
        return connect(dsn)


class ReadScopeCleanupError(RuntimeError):
    """A scoped read connection could not be closed."""


class _ReadScope:
    def __init__(self):
        self.owner = get_ident()
        self.active = True
        self.busy = False
        self.connection = None

    def check(self):
        if not self.active or self.owner != get_ident() or self.busy:
            raise RuntimeError("Read scope is closed, foreign, or already borrowed")

    def discard(self):
        connection, self.connection = self.connection, None
        if connection is not None:
            connection.close()

    def close(self):
        self.active = False
        try:
            self.discard()
        except Exception:
            raise ReadScopeCleanupError("Read scope cleanup failed") from None


_read_scope = ContextVar("precomputed_read_scope", default=None)


def release_precomputed_read_connection():
    """Close an idle scoped connection, keeping the scope available for reuse.

    Positions calls this before its independently owned publication read so the
    two connections do not overlap. Outside a read scope this is a no-op.
    """
    scope = _read_scope.get()
    if scope is None:
        return
    scope.check()
    try:
        scope.discard()
    except Exception:
        raise ReadScopeCleanupError("Read scope cleanup failed") from None


@contextmanager
def precomputed_read_scope():
    """Opt-in synchronous worker ownership; never an ASGI response lifetime.

    Only precomputed_read_connection borrows this resource. Each successful
    SELECT ends with rollback, retaining the existing uncommitted read boundary.
    Publication reads and all get_connection callers remain independent.
    """
    if _read_scope.get() is not None:
        raise RuntimeError("Nested read scopes are not supported")
    scope = _ReadScope()
    token = _read_scope.set(scope)
    try:
        try:
            yield
        except BaseException:
            try:
                scope.close()
            except Exception:
                pass  # Cleanup must not replace the original route failure.
            raise
        else:
            scope.close()
    finally:
        _read_scope.reset(token)


@contextmanager
def precomputed_read_connection(connect=None):
    connect = get_connection if connect is None else connect
    scope = _read_scope.get()
    if scope is None:
        connection = connect()
        try:
            yield connection
        finally:
            connection.close()
        return
    scope.check()
    scope.busy = True
    try:
        if scope.connection is None:
            scope.connection = connect()
        try:
            yield scope.connection
            # A fresh transaction for the next query, even at REPEATABLE READ.
            # Psycopg also clears its prepared-statement cache on rollback.
            scope.connection.rollback()
        except BaseException:
            try:
                scope.discard()
            except Exception:
                pass
            raise
    finally:
        scope.busy = False
