from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.publication_activation import BUNDLE_PATH, bundle_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = bundle_json()
    if args.write:
        BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BUNDLE_PATH.write_text(generated, encoding="utf-8", newline="\n")
    if args.check:
        if not BUNDLE_PATH.exists() or BUNDLE_PATH.read_text(encoding="utf-8") != generated:
            raise SystemExit("checked activation bundle is stale")
    print(BUNDLE_PATH.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
