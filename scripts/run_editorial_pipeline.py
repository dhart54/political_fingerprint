"""Canonical developer command for Editorial Semantic IR V1."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.pipeline import replay_accepted_reference  # noqa: E402
from scripts.compare_accepted_semantic_references import compare_case  # noqa: E402

CORPORA = (
    ROOT / "docs/semantic_ir/accepted/development_cases.json",
    ROOT / "docs/semantic_ir/accepted/held_out_cases.json",
)


def _run(command: list[str]) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    result = {
        "command": subprocess.list2cmdline(command),
        "status": "pass" if completed.returncode == 0 else "fail",
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"{result['command']} failed: {detail}")
    return result


def _semantic_loop() -> dict[str, Any]:
    commands = [
        ["node", "scripts/validate_editorial_semantic_ir_schema.mjs"],
        [sys.executable, "scripts/validate_editorial_semantic_ir.py"],
        [sys.executable, "scripts/compare_accepted_semantic_references.py"],
        [
            sys.executable,
            "-m",
            "unittest",
            "backend.tests.test_editorial_semantic_ir",
            "backend.tests.test_editorial_pipeline",
        ],
        [sys.executable, "scripts/check_documentation_governance.py"],
    ]
    return {
        "tier": "semantic",
        "commands": [_run(command) for command in commands],
    }


def _accepted_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in CORPORA:
        cases.extend(json.loads(path.read_text(encoding="utf-8"))["cases"])
    return cases


def _domain_loop(domains: list[str], case_ids: list[str]) -> dict[str, Any]:
    selected = [
        case
        for case in _accepted_cases()
        if (not domains or case["domain"] in domains)
        and (not case_ids or case["case_id"] in case_ids)
    ]
    if not selected:
        raise ValueError("no accepted references matched --domain/--case")
    missing = set(case_ids) - {case["case_id"] for case in selected}
    if missing:
        raise ValueError(f"unknown or domain-mismatched case(s): {sorted(missing)}")

    started = time.perf_counter()
    results = []
    for case in selected:
        compare_case(case)
        pipeline_result = replay_accepted_reference(case)
        results.append(
            {
                "case_id": case["case_id"],
                "domain": case["domain"],
                "member_count": pipeline_result.validation["member_count"],
                "proposition_count": pipeline_result.validation["proposition_count"],
                "review_routes": [
                    member["review_route"]
                    for member in pipeline_result.compiled_ir["members"]
                ],
                "compiled_ir_sha256": pipeline_result.review_payload[
                    "compiled_ir_sha256"
                ],
            }
        )
    return {
        "tier": "domain",
        "status": "pass",
        "pipeline": "backend.app.semantic_ir.pipeline.run_editorial_pipeline",
        "read_only": True,
        "persistence_proposal_prepared": False,
        "publication_attempted": False,
        "cases": results,
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }


def _release_loop(
    *, include_frontend: bool, include_persistence: bool
) -> dict[str, Any]:
    result = _semantic_loop()
    result["tier"] = "release"
    if include_persistence:
        result["commands"].append(
            _run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "backend.tests.test_editorial_artifact_persistence",
                ]
            )
        )
    if include_frontend:
        result["commands"].append(
            _run(["npm", "run", "build", "--prefix", "frontend"])
        )
    result["frontend_included"] = include_frontend
    result["persistence_included"] = include_persistence
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Editorial Semantic IR V1 command surface"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument(
        "--tier", required=True, choices=("semantic", "domain", "release")
    )
    validate.add_argument("--domain", action="append", default=[])
    validate.add_argument("--case", action="append", default=[])
    validate.add_argument("--include-frontend", action="store_true")
    validate.add_argument("--include-persistence", action="store_true")
    validate.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.tier == "semantic":
            result = _semantic_loop()
        elif args.tier == "domain":
            result = _domain_loop(args.domain, args.case)
        else:
            result = _release_loop(
                include_frontend=args.include_frontend,
                include_persistence=args.include_persistence,
            )
    except (RuntimeError, ValueError) as exc:
        print(f"Editorial pipeline validation failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        count = len(result.get("cases", result.get("commands", [])))
        print(f"Editorial pipeline {result['tier']} validation passed: {count} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
