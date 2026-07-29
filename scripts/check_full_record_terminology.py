"""Govern current full-record versus benchmark-sample terminology."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"\bfull[- ]issue conclusion\b", re.IGNORECASE)
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
    return [
        f"{path}:{line_number}: benchmark-broadening term "
        f"{match.group(0)!r} is forbidden in current authority"
        for line_number, line in enumerate(text.splitlines(), 1)
        for match in FORBIDDEN.finditer(line)
    ]


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in AUTHORITATIVE_PATHS:
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: current authoritative document is missing")
            continue
        errors.extend(check_text(path.read_text(encoding="utf-8"), path=relative))
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
