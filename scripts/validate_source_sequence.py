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


def require_same_action_passage_stages(declaration: dict, initial: dict,
                                      next_action: dict, recorded: dict,
                                      bill: str, roll: int) -> str:
    """Bind explicitly scoped passage stages to one declared bill and parent.

    The caller must verify that next_action is the next offered-bill callup in
    the parent. Literal text order alone cannot establish legislative identity.
    This bounded check grants no semantic, source-completeness or review clearance.
    """
    compact = lambda value: re.sub(r'\s+', '', value).upper()
    expected = compact(bill)
    if not re.fullmatch(r'(?:S\.|H\.R\.)[1-9][0-9]*', expected):
        raise ValueError('explicit Senate or House bill identity required')
    if isinstance(roll, bool) or not isinstance(roll, int) or roll < 1:
        raise ValueError('explicit positive roll required')
    parent = tuple(declaration.get(key) for key in
                   ('url', 'raw_sha256', 'captured_full_text_sha256'))
    if not all(parent):
        raise ValueError('governed common source parent required')
    extents = []
    for source in (declaration, initial, next_action, recorded):
        if tuple(source.get(key) for key in
                 ('url', 'raw_sha256', 'captured_full_text_sha256')) != parent:
            raise ValueError('passage stages must share the exact source parent')
        ranges = source.get('source_text_extents', [])
        if len(ranges) != 1:
            raise ValueError('one literal source interval per stage required')
        extent = ranges[0]
        start, end, total = (extent.get(key) for key in ('start', 'end', 'total'))
        if (any(type(value) is not int for value in (start, end, total)) or
                not 0 <= start < end <= total or
                end - start != len(source['text'])):
            raise ValueError('literal stage interval differs from source text')
        extents.append((start, end, total))
    if len({extent[2] for extent in extents}) != 1:
        raise ValueError('passage stages must share the exact parent extent')
    callup = r'call up the bill\s*\(((?:S\.|H\.\s*R\.)\s*[1-9][0-9]*)\)'
    identities = re.findall(callup, normalized_source_text(declaration['text']))
    following = re.findall(callup, normalized_source_text(next_action['text']))
    if len(identities) != 1 or compact(identities[0]) != expected:
        raise ValueError('offered declaration differs from exact action')
    if len(following) != 1 or compact(following[0]) == expected:
        raise ValueError('explicit distinct next-action callup required')
    if not (extents[0][1] <= extents[1][0] < extents[1][1] <= extents[2][0]
            and extents[2][1] <= extents[3][0]):
        raise ValueError('initial passage is outside the declared action boundary')
    require_source_sequence(initial['text'], ['question is on', 'ayes appeared',
                            'demand the yeas and nays', 'yeas and nays were ordered',
                            'proceedings on this question will be postponed'])
    result = normalized_source_text(recorded['text'])
    resume = re.search(r'unfinished business is the vote on passage of the bill\s*'
                       r'\(((?:S\.|H\.\s*R\.)\s*[1-9][0-9]*)\)', result)
    if resume is None or compact(resume[1]) != expected:
        raise ValueError('recorded resumption differs from exact action')
    require_source_sequence(result, ['unfinished business', 'question is on the passage',
                            'vote was taken by electronic', f'[Roll No. {roll}]',
                            'So the bill was passed'])
    return expected
