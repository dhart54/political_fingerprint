from __future__ import annotations

from typing import Any

from app.analysis.house_comparable_families import ComparableFamilyArtifact
from app.analysis.house_record_across_congresses import (
    DISALLOWED_RESPONSE_FIELD_TERMS,
    PRODUCT_FRAMING,
    build_house_record_across_congresses_response,
)


TRANSPORT_KIND = "no_route_internal_backend_callable"
PUBLIC_ROUTE_EXPOSED = False


def build_internal_house_record_across_congresses_response(
    legislator_identifier: str,
    *,
    artifact: ComparableFamilyArtifact | None = None,
    connection: Any | None = None,
) -> dict[str, Any]:
    """Return the internal Record Across Congresses adapter response.

    This transport is intentionally not mounted as a FastAPI route. Trusted
    backend callers import it directly, which keeps the response absent from
    public routing and OpenAPI until a separate private-route design exists.
    """

    response = build_house_record_across_congresses_response(
        legislator_identifier,
        artifact=artifact,
        connection=connection,
    )
    _validate_transport_response(response)
    return response


def _validate_transport_response(response: dict[str, Any]) -> None:
    if response.get("product_framing") != PRODUCT_FRAMING:
        raise ValueError("Record Across Congresses product framing is required")
    _assert_no_disallowed_terms(response)


def _assert_no_disallowed_terms(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            for term in DISALLOWED_RESPONSE_FIELD_TERMS:
                if term in normalized_key:
                    raise ValueError(f"Disallowed transport response field: {key}")
            _assert_no_disallowed_terms(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_disallowed_terms(child)
