"""Govern current full-record versus benchmark-sample terminology."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERCLAIM_SENTENCE = re.compile(
    r"\b(?:benchmark|gold[\s-]+slice|reviewed[\s-]+sample|"
    r"(?:seven|7)[\s-]*action(?:[\s-]+sample)?)\b"
    r".{0,100}\b(?:is|are|represents?|establishes?|defines?|constitutes?|"
    r"equals?|serves?\s+as)\b"
    r".{0,60}\b(?:complete|full|entire|overall|final|representative[\s-]+level)\b"
    r".{0,60}\b(?:justice|issue|record|conclusion|interpretation)\b",
    re.IGNORECASE,
)
NEGATED_FULL_RECORD = re.compile(
    r"\b(?:not|never)\b.{0,40}\b(?:complete|full|entire|overall|final|"
    r"representative[\s-]+level)\b",
    re.IGNORECASE,
)
HISTORICAL_PATH_ALLOWLIST: tuple[str, ...] = ()
AUTHORITATIVE_PATHS = (
    "AGENTS.md",
    "docs/README.md",
    "docs/interpretation_principles.md",
    "docs/semantic_ir/AGENTS.md",
    "docs/semantic_ir/editorial_semantic_ir_v1.md",
    "docs/editorial_public_issue_presentation_v1.md",
    "docs/public_editorial_frontend_contract.md",
    "docs/editorial/current_state_index.json",
    "docs/editorial/current_state_index.md",
    "docs/workflows/editorial-standardization-pipeline.md",
    "docs/methodology/full_record_issue_interpretation_v1.md",
    "docs/methodology/full_record_issue_interpretation_v1.schema.json",
    "docs/editorial/full_record_reviews/f000477_justice_public_safety_119_review_state_v1.json",
)


def check_text(text: str, *, path: str) -> list[str]:
    if path in HISTORICAL_PATH_ALLOWLIST:
        return []
    errors: list[str] = []
    for paragraph in re.finditer(r"(?:^|\n)(?!\s*$)(.*?)(?=\n\s*\n|\Z)", text, re.DOTALL):
        line_number = text.count("\n", 0, paragraph.start(1)) + 1
        normalized = re.sub(r"\s+", " ", paragraph.group(1)).strip()
        for sentence in re.split(r"(?<=[.!?])\s+|[;]", normalized):
            if OVERCLAIM_SENTENCE.search(sentence) and not NEGATED_FULL_RECORD.search(
                sentence
            ):
                errors.append(
                    f"{path}:{line_number}: benchmark/sample language is combined "
                    "with an unauthorized full-record claim"
                )
    return errors


def check_review_record(value: dict[str, object], *, path: str) -> list[str]:
    axes = value.get("axes", {})
    frontend = value.get("frontend_state", {})
    authority = value.get("external_authority", {})
    if not isinstance(axes, dict) or not isinstance(frontend, dict):
        return [f"{path}: malformed full-record governance state"]
    scope = axes.get("review_scope")
    completion = axes.get("review_completion_state")
    labels = set(frontend.get("available_labels", []))
    errors: list[str] = []
    if scope in {"benchmark_sample", "bounded_partial_record"}:
        forbidden = {
            "Full review complete",
            "Full issue interpretation available",
            "Complete issue record",
            "Representative-level issue conclusion",
        }
        if labels & forbidden:
            errors.append(f"{path}: bounded scope exposes full-record labels")
        if isinstance(authority, dict) and any(authority.values()):
            errors.append(f"{path}: bounded scope carries full-record authority")
    if (
        "Full review complete" in labels
        and (scope != "full_defined_issue_record" or completion != "complete")
    ):
        errors.append(f"{path}: full-review label lacks full completed scope")
    if "Full review complete" in labels and (
        not isinstance(authority, dict)
        or authority.get("universe_manifest") is None
        or authority.get("universe_authority_receipt") is None
    ):
        errors.append(f"{path}: full-review label lacks external universe authority")
    if "Full issue interpretation available" in labels and (
        not isinstance(authority, dict)
        or any(value is None for value in authority.values())
    ):
        errors.append(f"{path}: full-interpretation label lacks external gates")
    return errors


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in AUTHORITATIVE_PATHS:
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: current authoritative document is missing")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(check_text(text, path=relative))
        if relative.startswith("docs/editorial/full_record_reviews/"):
            errors.extend(check_review_record(json.loads(text), path=relative))
    return errors


def main() -> int:
    errors = check()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Full-record terminology governance passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
