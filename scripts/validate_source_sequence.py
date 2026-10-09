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
