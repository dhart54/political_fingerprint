from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api import internal_record_across  # noqa: E402
from app.internal_auth import INTERNAL_API_TOKEN_ENV, INTERNAL_API_TOKEN_HEADER  # noqa: E402
from app.main import app  # noqa: E402


INTERNAL_PATH = "/internal/record-across-congresses/house/leg_valerie_p_foushee"


def fake_response(identifier: str) -> dict[str, Any]:
    return {
        "response_kind": "internal_house_record_across_congresses_family_evidence",
        "product_framing": "Record Across Congresses",
        "availability_explanation": "This internal response reports factual family-level evidence availability and counts only.",
        "legislator_identifier": identifier,
        "requested_legislator_identifier": identifier,
        "artifact_version": "house-comparable-policy-question-families-v1",
        "supported_congresses": [118, 119],
        "legislator": {"legislator_identifier": identifier, "chamber": "house"},
        "summary": {
            "eligible_comparable_family_count": 2,
            "record_across_congresses_available": True,
            "display_eligible_family_count": 2,
            "directly_comparable_display_eligible_family_count": 1,
            "conditionally_comparable_display_eligible_family_count": 1,
        },
        "non_authorization_metadata": {
            "internal_response_only": True,
            "public_route_exposed": False,
            "only_factual_evidence_availability_and_counts": True,
        },
        "families": [
            {
                "family_id": "direct_family",
                "comparability_status": "directly_comparable",
                "comparability_caveat": "Direct caveat.",
                "record_across_congresses_available": True,
                "family_evidence_counts_by_congress": {
                    "118": {
                        "cast_substantive_yes_count": 1,
                        "cast_substantive_no_count": 0,
                        "not_voting_count": 1,
                        "present_count": 0,
                        "missing_no_record_count": 0,
                    },
                    "119": {
                        "cast_substantive_yes_count": 0,
                        "cast_substantive_no_count": 1,
                        "not_voting_count": 0,
                        "present_count": 1,
                        "missing_no_record_count": 0,
                    },
                },
            }
        ],
    }


def test_missing_internal_secret_fails_closed(monkeypatch) -> None:
    monkeypatch.delenv(INTERNAL_API_TOKEN_ENV, raising=False)
    client = TestClient(app)

    response = client.get(INTERNAL_PATH, headers={INTERNAL_API_TOKEN_HEADER: "token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_empty_internal_secret_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv(INTERNAL_API_TOKEN_ENV, "  ")
    client = TestClient(app)

    response = client.get(INTERNAL_PATH, headers={INTERNAL_API_TOKEN_HEADER: "token"})

    assert response.status_code == 401


def test_missing_request_token_fails(monkeypatch) -> None:
    monkeypatch.setenv(INTERNAL_API_TOKEN_ENV, "expected-token")
    client = TestClient(app)

    response = client.get(INTERNAL_PATH)

    assert response.status_code == 401


def test_incorrect_request_token_fails(monkeypatch) -> None:
    monkeypatch.setenv(INTERNAL_API_TOKEN_ENV, "expected-token")
    client = TestClient(app)

    response = client.get(INTERNAL_PATH, headers={INTERNAL_API_TOKEN_HEADER: "wrong-token"})

    assert response.status_code == 401


def test_correct_request_token_succeeds_and_uses_transport(monkeypatch) -> None:
    monkeypatch.setenv(INTERNAL_API_TOKEN_ENV, "expected-token")
    expected = fake_response("leg_valerie_p_foushee")
    monkeypatch.setattr(
        internal_record_across,
        "build_internal_house_record_across_congresses_response",
        lambda identifier: fake_response(identifier),
    )
    client = TestClient(app)

    response = client.get(INTERNAL_PATH, headers={INTERNAL_API_TOKEN_HEADER: "expected-token"})

    assert response.status_code == 200
    assert response.json() == expected


def test_internal_route_is_excluded_from_openapi() -> None:
    openapi_paths = set(app.openapi()["paths"])

    assert "/internal/record-across-congresses/house/{legislator_identifier}" not in openapi_paths
    assert not any(path.startswith("/internal/") for path in openapi_paths)


def test_no_public_record_congress_comparable_or_family_route() -> None:
    public_paths = [
        getattr(route, "path", "")
        for route in app.routes
        if not getattr(route, "path", "").startswith("/internal/")
    ]

    assert not any("record" in path or "congress" in path or "comparable" in path or "family" in path for path in public_paths)


def test_response_guardrails_and_approved_copy_artifact(monkeypatch) -> None:
    monkeypatch.setenv(INTERNAL_API_TOKEN_ENV, "expected-token")
    monkeypatch.setattr(
        internal_record_across,
        "build_internal_house_record_across_congresses_response",
        lambda identifier: fake_response(identifier),
    )
    response = TestClient(app).get(INTERNAL_PATH, headers={INTERNAL_API_TOKEN_HEADER: "expected-token"}).json()
    guardrail = json.loads(
        (REPO_ROOT / "docs" / "review_packets" / "record_across_congresses_frontend_copy_guardrails.json").read_text()
    )
    response_text = json.dumps(response, sort_keys=True).lower()
    approved_text = json.dumps(guardrail["approved_copy"], sort_keys=True).lower()

    assert response["product_framing"] == "Record Across Congresses"
    assert response["non_authorization_metadata"]["internal_response_only"] is True
    assert not [term for term in guardrail["disallowed_terms"] if term.lower() in response_text]
    assert not [term for term in guardrail["disallowed_terms"] if term.lower() in approved_text]


def test_validation_profile_summaries_through_authorized_route(monkeypatch) -> None:
    monkeypatch.setenv(INTERNAL_API_TOKEN_ENV, "expected-token")

    def profile_response(identifier: str) -> dict[str, Any]:
        response = fake_response(identifier)
        if identifier in {"leg_abraham_j_hamadeh", "leg_allred", "leg_james_gallagher"}:
            response["summary"]["record_across_congresses_available"] = False
            response["summary"]["display_eligible_family_count"] = 0
            response["summary"]["directly_comparable_display_eligible_family_count"] = 0
            response["summary"]["conditionally_comparable_display_eligible_family_count"] = 0
        elif identifier == "leg_aumua_amata_coleman_radewagen":
            response["summary"]["display_eligible_family_count"] = 1
            response["summary"]["directly_comparable_display_eligible_family_count"] = 0
            response["summary"]["conditionally_comparable_display_eligible_family_count"] = 1
        return response

    monkeypatch.setattr(internal_record_across, "build_internal_house_record_across_congresses_response", profile_response)
    client = TestClient(app)
    expected = {
        "leg_valerie_p_foushee": (True, 2, 1, 1),
        "leg_aaron_bean": (True, 2, 1, 1),
        "leg_adam_smith": (True, 2, 1, 1),
        "leg_abraham_j_hamadeh": (False, 0, 0, 0),
        "leg_allred": (False, 0, 0, 0),
        "leg_aumua_amata_coleman_radewagen": (True, 1, 0, 1),
        "leg_james_gallagher": (False, 0, 0, 0),
    }

    for identifier, summary_values in expected.items():
        response = client.get(
            f"/internal/record-across-congresses/house/{identifier}",
            headers={INTERNAL_API_TOKEN_HEADER: "expected-token"},
        )
        summary = response.json()["summary"]
        assert response.status_code == 200
        assert (
            summary["record_across_congresses_available"],
            summary["display_eligible_family_count"],
            summary["directly_comparable_display_eligible_family_count"],
            summary["conditionally_comparable_display_eligible_family_count"],
        ) == summary_values
