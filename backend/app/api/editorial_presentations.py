"""Read-only public API for publication-gated IR-native presentations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.precomputed import get_legislator_profile
from app.db import get_connection
from app.editorial_artifacts.repository import EditorialArtifactRepository
from app.editorial_presentations.selector import select_public_presentations
from app.editorial_presentations.integration_candidate import (
    M11M_PREVIEW_TOKEN,
    load_site_integration_candidate,
    select_site_integration_preview,
)


router = APIRouter()
M11M_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_national_security_foreign_119_v1/site_integration_candidate.json"
)


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
    candidate: str | None = Query(default=None, pattern="^m11m-national-security$"),
) -> dict[str, Any]:
    profile = get_legislator_profile(legislator_id=legislator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Legislator not found")
    public_result = select_public_presentations(
        _load_publication_rows(),
        legislator_id=legislator_id,
        member_bioguide_id=str(profile["bioguide_id"]),
        scope=scope,
    )
    if not (
        candidate == M11M_PREVIEW_TOKEN
        and os.getenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW") == "1"
    ):
        return public_result
    try:
        preview = load_site_integration_candidate(M11M_CANDIDATE_PATH)
        return select_site_integration_preview(
            preview,
            legislator_id=legislator_id,
            member_bioguide_id=str(profile["bioguide_id"]),
            scope=scope,
        )
    except (OSError, KeyError, TypeError, ValueError):
        return public_result
