"""Fail-closed database environment checks for ordinary offline validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

from .disposable_database_url import (
    APPROVED_LOOPBACK_HOSTS,
    require_exact_loopback_postgres_url,
)


INVALID_OFFLINE_DATABASE_URL = "postgresql://invalid"
PRIMARY_DATABASE_ENV = "DATABASE_URL"
DISPOSABLE_DATABASE_ENVS = (
    "EDITORIAL_DISPOSABLE_DATABASE_URL",
    "UNIVERSE_DISCOVERY_DISPOSABLE_DATABASE_URL",
)
KNOWN_DATABASE_ENVS = (PRIMARY_DATABASE_ENV, *DISPOSABLE_DATABASE_ENVS)


class OfflineDatabaseSafetyError(ValueError):
    """Raised before a test subprocess when an inherited target is unsafe."""


@dataclass(frozen=True)
class OfflineDatabasePreflight:
    database_url_state: str
    disposable_integration_enabled: bool
    disposable_environment_names: tuple[str, ...]


def _state(value: str | None) -> str:
    if not value:
        return "unset"
    if value == INVALID_OFFLINE_DATABASE_URL:
        return "invalid_sentinel"
    try:
        hostname = (urlsplit(value).hostname or "").casefold()
    except (TypeError, ValueError):
        return "malformed"
    return "loopback" if hostname in APPROVED_LOOPBACK_HOSTS else "non_loopback"


def _require_offline_value(name: str, value: str | None) -> str:
    state = _state(value)
    if state in {"unset", "invalid_sentinel"}:
        return state
    if state != "loopback":
        raise OfflineDatabaseSafetyError(
            f"offline database preflight rejected {name}: state={state}"
        )
    try:
        require_exact_loopback_postgres_url(value)
    except ValueError as exc:
        raise OfflineDatabaseSafetyError(
            f"offline database preflight rejected {name}: state=malformed_loopback"
        ) from exc
    return "loopback"


def inspect_offline_database_environment(
    environment: Mapping[str, str],
    *,
    allow_disposable_integration: bool = False,
) -> OfflineDatabasePreflight:
    primary_state = _require_offline_value(
        PRIMARY_DATABASE_ENV, environment.get(PRIMARY_DATABASE_ENV)
    )
    configured_disposable: list[str] = []
    for name in DISPOSABLE_DATABASE_ENVS:
        value = environment.get(name)
        state = _require_offline_value(name, value)
        if state == "loopback":
            configured_disposable.append(name)
            if not allow_disposable_integration:
                raise OfflineDatabaseSafetyError(
                    "offline database preflight rejected disposable integration: "
                    f"environment={name} state=loopback opt_in=missing"
                )
    if allow_disposable_integration and not configured_disposable:
        raise OfflineDatabaseSafetyError(
            "offline database preflight rejected disposable integration: "
            "state=missing_loopback_target"
        )
    return OfflineDatabasePreflight(
        database_url_state=(
            "invalid_sentinel" if primary_state == "unset" else primary_state
        ),
        disposable_integration_enabled=allow_disposable_integration,
        disposable_environment_names=tuple(configured_disposable),
    )
