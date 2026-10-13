"""Validate existing roll-call→bill facts without inferring a measure binding."""
from typing import Any

MEASURE_TYPES = frozenset({"hr", "s", "hres", "sres", "hjres", "sjres", "hconres", "sconres"})
_MAX_SAFE_INTEGER = 2**53 - 1


def _positive_integer(value: Any) -> bool:
    return type(value) is int and 0 < value <= _MAX_SAFE_INTEGER


def measure_reference(congress: Any, measure_type: Any, number: Any, *, action_congress: Any) -> dict[str, Any] | None:
    """Return a nullable factual reference; chamber does not constrain bill origin."""
    if not (_positive_integer(congress) and _positive_integer(number)
            and _positive_integer(action_congress) and congress == action_congress):
        return None
    if not isinstance(measure_type, str):
        return None
    normalized_type = measure_type.strip().lower()
    if normalized_type not in MEASURE_TYPES:
        return None
    return {"congress": congress, "type": normalized_type, "number": number}


def validate_measure_reference(value: Any, *, action_congress: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or set(value) != {"congress", "type", "number"}:
        return None
    return measure_reference(value["congress"], value["type"], value["number"], action_congress=action_congress)
