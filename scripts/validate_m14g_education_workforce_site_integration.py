"""Focused deterministic validator for the detached M14G preview."""

from __future__ import annotations

import json
from pathlib import Path
import re
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
    "backend/app/api/m14g_preview.py",
    "backend/app/main.py",
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
POST_CAPTURE_FILES = {
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/review_package.json",
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/screenshot_manifest.json",
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/screenshots/desktop_overview.png",
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/screenshots/desktop_notable_expanded.png",
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/screenshots/desktop_hr5408_receipt.png",
    "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/screenshots/mobile_overview.png",
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    missing = sorted(path for path in EXPECTED_FILES if not (OUTPUT / path).exists())
    if missing:
        raise SystemExit(f"missing M14G review files: {missing}")
    manifest = json.loads((OUTPUT / "screenshot_manifest.json").read_text(encoding="utf-8"))
    if len(manifest["captures"]) != 4 or any(not row["file_sha256"] for row in manifest["captures"]):
        raise SystemExit("M14G screenshot manifest is incomplete")
    capture_head = manifest.get("source_head_at_capture", "")
    if not re.fullmatch(r"[0-9a-f]{40}", capture_head):
        raise SystemExit("M14G capture head is not an exact commit")
    git("cat-file", "-e", f"{capture_head}^{{commit}}")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", capture_head, "HEAD"], cwd=ROOT
    ).returncode:
        raise SystemExit("M14G capture head is not an ancestor of the final head")
    if any(row.get("source_commit") != capture_head for row in manifest["captures"]):
        raise SystemExit("M14G screenshot source commits differ from the capture head")
    post_capture = set(git("diff", "--name-only", capture_head, "HEAD").splitlines())
    unexpected_post_capture = post_capture - POST_CAPTURE_FILES
    if unexpected_post_capture:
        raise SystemExit(
            f"M14G post-capture file set differs: {sorted(unexpected_post_capture)}"
        )
    required_bindings = {
        "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/review_package.json",
        "docs/editorial/site_integration_candidates/f000477_education_workforce_m14g_v1/screenshot_manifest.json",
    }
    if not required_bindings.issubset(post_capture):
        raise SystemExit("M14G final screenshot bindings were not sealed after capture")
    candidate = json.loads((OUTPUT / "site_integration_candidate.json").read_text(encoding="utf-8"))
    if len(candidate["subject"]["receipt_projections"]) != 17:
        raise SystemExit("M14G receipt accounting differs")
    changed = git("diff", "--name-only", BASE, "HEAD").splitlines()
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
