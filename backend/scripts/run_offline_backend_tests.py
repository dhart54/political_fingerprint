"""Run backend tests only after a fail-closed offline database preflight."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from scripts.offline_database_preflight import (  # noqa: E402
    DISPOSABLE_DATABASE_ENVS,
    INVALID_OFFLINE_DATABASE_URL,
    OfflineDatabaseSafetyError,
    inspect_offline_database_environment,
)


def build_child_environment(
    environment: dict[str, str],
    *,
    allow_disposable_integration: bool,
) -> tuple[dict[str, str], str]:
    result = inspect_offline_database_environment(
        environment,
        allow_disposable_integration=allow_disposable_integration,
    )
    child = dict(environment)
    child.setdefault("DATABASE_URL", INVALID_OFFLINE_DATABASE_URL)
    if not allow_disposable_integration:
        for name in DISPOSABLE_DATABASE_ENVS:
            child.pop(name, None)
    summary = (
        "offline_database_preflight=pass "
        f"database_url_state={result.database_url_state} "
        "disposable_integration="
        + ("enabled" if result.disposable_integration_enabled else "disabled")
    )
    return child, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-disposable-integration", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        command = [sys.executable, "-m", "pytest", "-q", "backend/tests"]
    try:
        child_environment, summary = build_child_environment(
            dict(os.environ),
            allow_disposable_integration=args.allow_disposable_integration,
        )
    except OfflineDatabaseSafetyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(summary, flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=child_environment,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
