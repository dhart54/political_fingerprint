"""Verify explicitly selected literal anchors in a source's order.

This checks text order only; callers own source scope and semantic interpretation.
"""
from __future__ import annotations
import re

def normalized_source_text(text: str) -> str:
    text = re.sub(r'(\w)[-\u00ad]\s*\n\s*(\w)', lambda m: m[1] + ('-' if m[1].isdigit() else '') + m[2], text)
    return re.sub(r'\s+', ' ', text).strip()

def require_source_sequence(text: str, anchors: list[str]) -> list[int]:
    if not anchors or any(not anchor for anchor in anchors):
        raise ValueError('nonempty explicit source anchors required')
    text = normalized_source_text(text)
    positions, cursor = [], 0
    for anchor in anchors:
        anchor = normalized_source_text(anchor)
        if not anchor:
            raise ValueError('nonempty explicit source anchors required')
        position = text.find(anchor, cursor)
        if position < 0:
            raise ValueError(f'missing or out-of-order source anchor: {anchor}')
        positions.append(position)
        cursor = position + len(anchor)
    return positions


def require_exact_bill_operative(text: str, bill: str) -> str:
    """Check the declared offered bill identity, without granting semantic clearance.

    A source must contain one offered-text declaration, immediately followed by
    the expected bill and enacting clause. References elsewhere cannot bind it.
    Callers still verify adoption, completeness, stage and substantive meaning.
    """
    normalized = normalized_source_text(text)
    compact = lambda value: re.sub(r'\s+', '', value).upper()
    expected = compact(bill)
    if not re.fullmatch(r'(?:S\.|H\.R\.)[1-9][0-9]*', expected):
        raise ValueError('explicit Senate or House bill identity required')
    declaration = r'The text of the bill(?:, as amended,)? is as follows:'
    starts = list(re.finditer(declaration, normalized))
    if len(starts) != 1:
        raise ValueError('exactly one offered bill text declaration required')
    body = normalized[starts[0].end():].lstrip()
    identity = re.match(r'((?:S\.|H\.\s*R\.)\s*[1-9][0-9]*)\s+Be it enacted by', body)
    if identity is None or compact(identity[1]) != expected:
        raise ValueError('offered operative bill identity differs from exact action')
    return expected
