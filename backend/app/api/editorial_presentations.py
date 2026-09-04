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
from app.editorial_presentations.environment_integration_candidate import (
    M12M_PREVIEW_TOKEN,
    load_environment_site_integration_candidate,
    select_environment_site_integration_preview,
)
from app.editorial_presentations.education_workforce_integration_candidate import (
    M13M_PREVIEW_TOKEN,
    load_education_workforce_site_integration_candidate,
    select_education_workforce_site_integration_preview,
)


router = APIRouter()
M11M_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_national_security_foreign_119_v1/site_integration_candidate.json"
)
M12M_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_environment_energy_119_v1/site_integration_candidate.json"
)
M13M_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/editorial/full_record_reviews/site_integration_candidates/"
    "f000477_education_workforce_119_v1/site_integration_candidate.json"
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
    candidate: str | None = Query(
        default=None,
        pattern="^(m11m-national-security|m12m-environment-energy|m13m-education-workforce)$",
    ),
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
    if os.getenv("ENABLE_EDITORIAL_PRESENTATION_PREVIEW") != "1":
        return public_result
    try:
        if candidate == M11M_PREVIEW_TOKEN:
            return select_site_integration_preview(
                load_site_integration_candidate(M11M_CANDIDATE_PATH),
                legislator_id=legislator_id,
                member_bioguide_id=str(profile["bioguide_id"]),
                scope=scope,
            )
        if candidate == M12M_PREVIEW_TOKEN:
            return select_environment_site_integration_preview(
                load_environment_site_integration_candidate(M12M_CANDIDATE_PATH),
                legislator_id=legislator_id,
                member_bioguide_id=str(profile["bioguide_id"]),
                scope=scope,
            )
        if candidate == M13M_PREVIEW_TOKEN:
            return select_education_workforce_site_integration_preview(
                load_education_workforce_site_integration_candidate(
                    M13M_CANDIDATE_PATH
                ),
                legislator_id=legislator_id,
                member_bioguide_id=str(profile["bioguide_id"]),
                scope=scope,
            )
        return public_result
    except (OSError, KeyError, TypeError, ValueError):
        return public_result
