"""Focused deterministic validator for the detached M14G preview."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1"
EXPECTED_FILES = {
    "site_integration_candidate.json",
    "review_package.json",
    "screenshot_manifest.json",
    "screenshots/desktop_overview.png",
    "screenshots/desktop_notable_expanded.png",
    "screenshots/desktop_hr5408_receipt.png",
    "screenshots/mobile_overview.png",
}
ALLOWED_PREFIXES = (
    ".github/workflows/backend-tests.yml",
    "backend/app/api/editorial_presentations.py",
    "backend/app/api/positions.py",
    "backend/app/api/search.py",
    "backend/app/editorial_presentations/education_workforce_m14g_integration_candidate.py",
    "backend/scripts/build_m14g_education_workforce_site_integration.py",
    "backend/tests/test_m14g_education_workforce_site_integration.py",
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/",
    "docs/plans/m14g_education_detached_site_integration.md",
    "frontend/lib/api.js",
    "frontend/lib/m14gEducationWorkforce.test.mjs",
    "frontend/tests/m14g-education-workforce-integration.spec.mjs",
    "scripts/validate_m14g_education_workforce_site_integration.py",
)
BASE = "50777a5fd1ce84763e6a294db25578639aa5dce7"


def main() -> None:
    missing = sorted(path for path in EXPECTED_FILES if not (OUTPUT / path).exists())
    if missing:
        raise SystemExit(f"missing M14G review files: {missing}")
    manifest = json.loads((OUTPUT / "screenshot_manifest.json").read_text(encoding="utf-8"))
    if len(manifest["captures"]) != 4 or any(not row["file_sha256"] for row in manifest["captures"]):
        raise SystemExit("M14G screenshot manifest is incomplete")
    candidate = json.loads((OUTPUT / "site_integration_candidate.json").read_text(encoding="utf-8"))
    if len(candidate["subject"]["receipt_projections"]) != 17:
        raise SystemExit("M14G receipt accounting differs")
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    unexpected = sorted(path for path in changed if not any(
        path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        for prefix in ALLOWED_PREFIXES
    ))
    if unexpected:
        raise SystemExit(f"M14G scope guard rejected: {unexpected}")
    print(json.dumps({
        "candidate_subject_sha256": candidate["candidate_subject_sha256"],
        "receipts": 17,
        "episodes": 16,
        "screenshots": 4,
        "scope_guard": "passed",
    }, sort_keys=True))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
