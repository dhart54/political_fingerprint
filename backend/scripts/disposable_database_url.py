"""Strict validation for write-capable disposable PostgreSQL scripts."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit


APPROVED_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
ROUTING_OVERRIDE_PARAMETERS = frozenset(
    {"host", "hostaddr", "service", "servicefile"}
)


def require_exact_loopback_postgres_url(database_url: str | None) -> str:
    """Return a structurally validated loopback PostgreSQL connection URL."""

    if not database_url:
        raise ValueError("a disposable PostgreSQL database URL is required")
    try:
        parsed = urlsplit(database_url)
        scheme = parsed.scheme.casefold()
        hostname = (parsed.hostname or "").casefold()
        port = parsed.port
        query_parameters = {
            key.casefold()
            for key, _value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
        }
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "the disposable PostgreSQL database target is malformed"
        ) from exc
    if scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "the disposable PostgreSQL database target must use postgres or postgresql"
        )
    if hostname not in APPROVED_LOOPBACK_HOSTS:
        raise ValueError(
            "the disposable PostgreSQL database host is not an approved loopback host"
        )
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("the disposable PostgreSQL database port is invalid")
    if (
        not parsed.path.startswith("/")
        or not parsed.path[1:]
        or "/" in parsed.path[1:]
    ):
        raise ValueError(
            "the disposable PostgreSQL database target requires a database name"
        )
    if parsed.fragment:
        raise ValueError(
            "the disposable PostgreSQL database target must not include a fragment"
        )
    blocked_parameters = sorted(
        query_parameters & ROUTING_OVERRIDE_PARAMETERS
    )
    if blocked_parameters:
        raise ValueError(
            "the disposable PostgreSQL database target contains a forbidden "
            f"routing parameter: {', '.join(blocked_parameters)}"
        )
    return database_url
