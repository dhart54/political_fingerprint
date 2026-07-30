"""Shared deterministic token matching for representative names."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable


def normalize_name_tokens(value: object) -> tuple[str, ...]:
    """Normalize Unicode, case, whitespace, and ordinary name punctuation."""

    normalized = unicodedata.normalize("NFKD", str(value or "")).casefold()
    characters = []
    for character in normalized:
        category = unicodedata.category(character)
        if category == "Mn":
            continue
        characters.append(" " if category.startswith(("P", "Z")) else character)
    return tuple("".join(characters).split())


def name_tokens_match(query: object, candidate: object) -> bool:
    """Match every query token, independent of a candidate's middle-name tokens."""

    query_tokens = set(normalize_name_tokens(query))
    if not query_tokens:
        return True
    return query_tokens <= set(normalize_name_tokens(candidate))


def filter_name_matches(
    rows: Iterable[dict[str, object]],
    *,
    query: object,
) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if name_tokens_match(query, row.get("name_display"))
    ]
