from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


INTERNAL_API_TOKEN_ENV = "INTERNAL_API_TOKEN"
INTERNAL_API_TOKEN_HEADER = "X-Internal-API-Token"


def require_internal_api_token(
    provided_token: str | None = Header(default=None, alias=INTERNAL_API_TOKEN_HEADER),
) -> None:
    """Fail closed unless the configured internal token matches the request."""

    configured_token = os.getenv(INTERNAL_API_TOKEN_ENV, "").strip()
    if not configured_token or not provided_token:
        raise _unauthorized()
    if not hmac.compare_digest(provided_token, configured_token):
        raise _unauthorized()


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Unauthorized")
