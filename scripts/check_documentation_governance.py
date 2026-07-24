"""Deterministic documentation-link and plan-status validation."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


LINK_RE = re.compile(r"!?\[[^\]]*]\(\s*(<[^>]+>|[^)\s]+)")
ACTIVE_RE = re.compile(r"^Active plan:\s*\[[^\]]+]\(([^)]+)\)", re.MULTILINE)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
FORBIDDEN_LOCAL_RE = re.compile(
    r"^(?:file://|/mnt/[a-z]/|[a-z]:[\\/](?:users|documents)[\\/])",
    re.IGNORECASE,
)
STATUS_HEADINGS = {
    "active plan",
    "retained unresolved plans",
    "archived plans",
}


def tracked_markdown(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [root / line for line in result.stdout.splitlines() if line]


def clean_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def is_external_or_anchor(raw: str) -> bool:
    lowered = raw.lower()
    return (
        not raw
        or raw.startswith("#")
        or lowered.startswith(("http://", "https://", "mailto:", "data:"))
    )


def resolve_target(root: Path, source: Path, target: str) -> Path:
    if target.startswith("/"):
        return root / target.lstrip("/")
    return source.parent / target


def plan_status_targets(index_path: Path) -> tuple[dict[str, set[str]], list[str]]:
    categories = {heading: set() for heading in STATUS_HEADINGS}
    errors: list[str] = []
    current: str | None = None
    for line_number, line in enumerate(index_path.read_text(encoding="utf-8").splitlines(), 1):
        heading = HEADING_RE.match(line)
        if heading:
            candidate = heading.group(1).strip().lower()
            current = candidate if candidate in STATUS_HEADINGS else None
            continue
        if current is None:
            continue
        for match in LINK_RE.finditer(line):
            target = clean_target(match.group(1))
            if not target.endswith(".md"):
                continue
            name = Path(target).name.lower()
            if name in {"readme.md", "template.md", "plans.md"}:
                continue
            categories[current].add(target.replace("\\", "/"))

    seen: dict[str, str] = {}
    for category, targets in categories.items():
        for target in targets:
            prior = seen.get(target)
            if prior is not None:
                errors.append(
                    f"{index_path.relative_to(index_path.parents[2])}: plan "
                    f"{target!r} appears in both {prior!r} and {category!r}"
                )
            seen[target] = category
    return categories, errors


def check(root: Path) -> list[str]:
    errors: list[str] = []
    markdown_files = tracked_markdown(root)
    navigation_files = {
        root / "README.md",
        root / "docs" / "README.md",
        root / "docs" / "PLANS.md",
        root / "docs" / "plans" / "README.md",
    }
    navigation_files.update((root / "docs" / "workflows").glob("*.md"))

    for source in markdown_files:
        text = source.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in LINK_RE.finditer(line):
                raw_target = match.group(1).strip("<>")
                if source in navigation_files and FORBIDDEN_LOCAL_RE.match(raw_target):
                    errors.append(
                        f"{source.relative_to(root)}:{line_number}: "
                        f"machine-specific navigational link {raw_target!r}"
                    )
                if is_external_or_anchor(raw_target):
                    continue
                target = clean_target(raw_target)
                if FORBIDDEN_LOCAL_RE.match(target):
                    continue
                resolved = resolve_target(root, source, target)
                if not resolved.exists():
                    errors.append(
                        f"{source.relative_to(root)}:{line_number}: "
                        f"missing Markdown target {raw_target!r}"
                    )

    docs_readme = root / "docs" / "README.md"
    active_match = ACTIVE_RE.search(docs_readme.read_text(encoding="utf-8"))
    if active_match is None:
        errors.append("docs/README.md: missing 'Active plan:' Markdown link")
    else:
        active_target = clean_target(active_match.group(1))
        active_path = resolve_target(root, docs_readme, active_target)
        if not active_path.exists():
            errors.append(f"docs/README.md: active plan does not exist: {active_target}")
        try:
            active_relative = active_path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            errors.append(f"docs/README.md: active plan is outside repository: {active_target}")
        else:
            if active_relative.startswith("docs/plans/archive/"):
                errors.append("docs/README.md: archived plan identified as active")

    plans_index = root / "docs" / "plans" / "README.md"
    categories, category_errors = plan_status_targets(plans_index)
    errors.extend(category_errors)
    active_list = categories["active plan"]
    if len(active_list) != 1:
        errors.append(
            "docs/plans/README.md: active plan category must contain exactly one plan"
        )
    if any("/archive/" in f"/{target}" for target in active_list):
        errors.append("docs/plans/README.md: archived plan identified as active")

    archive_dir = root / "docs" / "plans" / "archive" / "2026"
    archived_plans = [
        path for path in archive_dir.glob("*.md") if path.name.lower() != "readme.md"
    ]
    if archived_plans and not (archive_dir / "README.md").exists():
        errors.append("docs/plans/archive/2026/README.md is required")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Documentation governance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
