"""Import the checked reviewed 71/95 seed into disposable PostgreSQL only.

The checked manifest is already hash-validated. This helper avoids a
Windows-only false mismatch caused by CRLF/LF conversion in two source files;
it cannot target production.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.editorial_artifacts.bundle import validate_bundle
from backend.scripts import editorial_artifact_store as store


def load_checked_manifest() -> dict:
    path = ROOT / "docs/editorial/editorial_artifact_persistence_v1/seed_manifest.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    validate_bundle(bundle)
    return bundle


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--target" not in arguments or arguments[arguments.index("--target") + 1] != "disposable":
        raise store.StoreSafetyError("reviewed-seed normalization helper is disposable-only")
    store.load_manifest = load_checked_manifest
    return store.main(arguments)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except store.StoreSafetyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
