from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.editorial_artifacts.bundle import ROOT, build_seed_bundle

DEFAULT_OUTPUT = ROOT / "docs/editorial/editorial_artifact_persistence_v1/seed_manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    bundle = build_seed_bundle()
    rendered = json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("checked-in seed manifest has drifted")
        print(json.dumps({
            "manifest_sha256": bundle["manifest_sha256"],
            "artifact_count": bundle["expected_counts"]["artifacts"],
            "relationship_count": bundle["expected_counts"]["relationships"],
            "drift": False,
        }, indent=2))
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
