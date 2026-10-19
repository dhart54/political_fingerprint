"""Strict conservation for ordered shared-core candidate increments."""
import json


def _unique(rows, label):
    result = {}
    for row in rows:
        identity = row["action_id"]
        if identity in result:
            raise ValueError(f"duplicate action identity in {label}: {identity}")
        result[identity] = row
    return result


def _ordered(rows, label):
    keys = [(row["session"], row["roll"]) for row in rows]
    if len(set(keys)) != len(keys) or keys != sorted(keys):
        raise ValueError(f"{label} differs from compiler session/roll ordering")


def _complete(row):
    # Object-key order is immaterial; every value and nested array stays exact.
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def check_core_conservation(previous, current, expected_additions):
    """Reject changes/deletions/duplicates/extras while allowing sorted insertion."""
    before = _unique(previous, "previous")
    after = _unique(current, "current")
    additions = _unique(expected_additions, "expected additions")
    _ordered(previous, "previous")
    _ordered(current, "current")
    if set(before) & set(additions):
        raise ValueError("expected additions overlap previous identities")
    if set(after) != set(before) | set(additions):
        raise ValueError("current identities differ from exact previous plus intended additions")
    for identity, row in before.items():
        if _complete(after[identity]) != _complete(row):
            raise ValueError(f"complete previous core changed: {identity}")
    for identity, row in additions.items():
        if _complete(after[identity]) != _complete(row):
            raise ValueError(f"complete intended addition changed: {identity}")
    return {"conserved": len(before), "added": len(additions), "current": len(after)}
