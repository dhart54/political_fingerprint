"""Public data availability and explicit local/demo fixture configuration."""

import os

from fastapi import HTTPException


def fixture_fallback_enabled() -> bool:
    return os.getenv("ENABLE_FIXTURE_FALLBACK") == "1"


class PublicDataUnavailable(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=503, detail="Public record data is unavailable right now.")
