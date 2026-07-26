"""Read-only public API for publication-gated IR-native presentations."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import get_legislator_profile
from app.db import get_connection
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.selector import select_public_presentations


router = APIRouter()


def _load_publication_rows() -> list[dict[str, Any]]:
    """Read through the established selector; avoid a connection when unconfigured."""

    if not os.getenv("DATABASE_URL"):
        return []
    connection = get_connection()
    try:
        return EditorialArtifactRepository(connection).publication_selector()
    finally:
        connection.close()


@router.get("/legislators/{legislator_id}/editorial-presentations")
def get_editorial_presentations(
    legislator_id: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
) -> dict[str, Any]:
    profile = get_legislator_profile(legislator_id=legislator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return select_public_presentations(
        _load_publication_rows(),
        legislator_id=legislator_id,
        member_bioguide_id=str(profile["bioguide_id"]),
        scope=scope,
    )
