import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator
from dotenv import load_dotenv

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

    return connect(dsn)
