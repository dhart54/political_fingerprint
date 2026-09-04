"""Detached, explicitly gated HTTP surface for M14G review."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.editorial_presentations.education_workforce_m14g_integration_candidate import (
    M14G_PREVIEW_TOKEN,
    load_m14g_candidate,
    merge_m14g_preview_evidence,
    merge_m14g_preview_positions,
    select_m14g_preview,
)


router = APIRouter(prefix="/preview/m14g", tags=["m14g-preview"])
CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/editorial/site_integration_candidates/"
    "f000477_education_workforce_m14g_v1/site_integration_candidate.json"
)
FOUSHEE_ID = "leg_valerie_p_foushee"
FOUSHEE_PROFILE: dict[str, object] = {
    "id": FOUSHEE_ID,
    "bioguide_id": "F000477",
    "name_display": "Valerie P. Foushee",
    "chamber": "house",
    "state": "NC",
    "district": "04",
    "party": "D",
}


def _candidate(candidate: str | None) -> dict[str, Any]:
    if not (
        os.getenv("EDITORIAL_PRESENTATION_PREVIEW") == "1"
        and candidate == M14G_PREVIEW_TOKEN
    ):
        raise HTTPException(status_code=404, detail="M14G preview not found")
    try:
        return load_m14g_candidate(CANDIDATE_PATH)
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=404, detail="M14G preview not found") from error


def _profile(legislator_id: str) -> dict[str, object]:
    if legislator_id != FOUSHEE_ID:
        raise HTTPException(status_code=404, detail="Legislator not found")
    return dict(FOUSHEE_PROFILE)


@router.get("/legislators/{legislator_id}/profile")
def get_m14g_profile(
    legislator_id: str,
    candidate: str | None = Query(default=None),
) -> dict[str, object]:
    _candidate(candidate)
    return _profile(legislator_id)


@router.get("/legislators/{legislator_id}/editorial-presentations")
def get_m14g_editorial_presentations(
    legislator_id: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
    candidate: str | None = Query(default=None),
) -> dict[str, Any]:
    data = _candidate(candidate)
    profile = _profile(legislator_id)
    return select_m14g_preview(
        data,
        legislator_id=legislator_id,
        member_bioguide_id=str(profile["bioguide_id"]),
        scope=scope,
    )


@router.get("/legislators/{legislator_id}/positions")
def get_m14g_positions(
    legislator_id: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
    candidate: str | None = Query(default=None),
) -> dict[str, object]:
    data = _candidate(candidate)
    _profile(legislator_id)
    base: dict[str, Any] = {
        "legislator_id": legislator_id,
        "scope": scope,
        "positions": [],
    }
    evidence = (
        data["subject"]["receipt_projections"] if scope in {"119", "all"} else []
    )
    if not evidence:
        return base
    return merge_m14g_preview_positions(base, governed_evidence=evidence)


@router.get("/legislators/{legislator_id}/positions/{domain}/evidence")
def get_m14g_evidence(
    legislator_id: str,
    domain: str,
    scope: str = Query(default="all", pattern="^(all|119|118)$"),
    candidate: str | None = Query(default=None),
) -> dict[str, object]:
    data = _candidate(candidate)
    _profile(legislator_id)
    normalized_domain = domain.strip().upper()
    base: dict[str, Any] = {
        "legislator_id": legislator_id,
        "domain": normalized_domain,
        "scope": scope,
        "evidence": [],
    }
    return merge_m14g_preview_evidence(
        base, data, domain=normalized_domain, scope=scope
    )
