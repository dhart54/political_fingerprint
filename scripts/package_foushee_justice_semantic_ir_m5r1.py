"""Create and independently verify the external M5-R1 delegated-review ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_foushee_justice_semantic_ir_m5r1 import (  # noqa: E402
    OUTPUT_ROOT,
    V1_COMMIT,
    V1_GRAPH_CONTENT,
    V1_IMPLEMENTATION_CONTENT,
    V1_INPUT_CONTENT,
    V1_ROOT,
    build,
    load,
)
from scripts.validate_foushee_justice_semantic_ir_m5r1 import validate  # noqa: E402


USER_ZIP = (
    "docs/editorial/full_record_reviews/policy_episode_implementations/"
    "f000477_justice_public_safety_119_v1.zip"
)
UPSTREAM_FILES = [
    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/decision_implementation_bundle.json",
    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/f000477_justice_public_safety_119_m3bb_delegated_acceptance_v1.json",
    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/f000477_justice_public_safety_119_m4a_delegated_episode_acceptance_v1.json",
    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/f000477_justice_public_safety_119_m4b_delegated_episode_implementation_acceptance_v1.json",
    "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/episode_implementation_bundle.json",
    "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/launch_review_risk_register.json",
    "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/episode_calibration_population.json",
]


def run(*args: str) -> str:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def package(output_directory: Path) -> dict[str, Any]:
    build(True)
    validation = validate()
    head = run("git", "rev-parse", "HEAD").strip()
    parent = run("git", "rev-parse", "HEAD^").strip()
    if parent != V1_COMMIT:
        raise ValueError("M5-R1 commit parent differs from reviewed M5 V1")
    if (
        run("git", "diff", "--name-only").strip()
        or run("git", "diff", "--cached", "--name-only").strip()
    ):
        raise ValueError("tracked worktree or index is dirty")
    untracked = {
        line.replace("\\", "/")
        for line in run(
            "git", "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        if line
    }
    if untracked != {USER_ZIP}:
        raise ValueError(f"unexpected untracked paths: {sorted(untracked)}")

    changed_status = run(
        "git", "diff-tree", "--no-commit-id", "--name-status", "-r", head
    )
    changed_paths = [line.split("\t")[-1] for line in changed_status.splitlines()]
    required = set(changed_paths)
    required.update(
        path.relative_to(ROOT).as_posix()
        for path in V1_ROOT.rglob("*")
        if path.is_file()
    )
    required.update(UPSTREAM_FILES)
    required.discard(USER_ZIP)
    missing = [path for path in sorted(required) if not (ROOT / path).is_file()]
    if missing:
        raise ValueError(f"package source paths missing: {missing}")

    files = []
    for relative in sorted(required):
        raw = (ROOT / relative).read_bytes()
        files.append(
            {
                "path": relative,
                "size": len(raw),
                "final_file_sha256": sha(raw),
            }
        )
    graph = load(OUTPUT_ROOT / "frozen_final_compiled_semantic_ir.json")
    compiler_input = load(OUTPUT_ROOT / "frozen_final_compiler_input.json")
    implementation = load(OUTPUT_ROOT / "provisional_implementation_bundle.json")
    ledger = load(OUTPUT_ROOT / "corrected_overlap_ledger.json")
    risk = load(OUTPUT_ROOT / "launch_review_risk_register.json")
    calibration = load(OUTPUT_ROOT / "semantic_calibration_population.json")
    manifest = {
        "schema_version": "m5r1_delegated_review_package_manifest_v1",
        "repository": "dhart54/political_fingerprint",
        "branch": run("git", "branch", "--show-current").strip(),
        "reviewed_commit": head,
        "parent": parent,
        "cached_origin_main": run("git", "rev-parse", "origin/main").strip(),
        "commit_tree_sha": run("git", "show", "-s", "--format=%T", head).strip(),
        "tracked_worktree_and_index_clean": True,
        "preserved_untracked_user_zip": USER_ZIP,
        "changed_files": changed_status.splitlines(),
        "included_repository_files": files,
        "v1_bindings": {
            "compiler_input_content_subject_sha256": V1_INPUT_CONTENT,
            "compiled_graph_content_subject_sha256": V1_GRAPH_CONTENT,
            "implementation_content_subject_sha256": V1_IMPLEMENTATION_CONTENT,
        },
        "v2_identities": {
            "compiler_input": {
                "artifact_id": compiler_input["artifact_id"],
                "content_subject_sha256": compiler_input["content_subject_sha256"],
                "final_file_sha256": sha(
                    (OUTPUT_ROOT / "frozen_final_compiler_input.json").read_bytes()
                ),
            },
            "compiled_graph": {
                "artifact_id": graph["artifact_id"],
                "content_subject_sha256": graph["content_subject_sha256"],
                "final_file_sha256": sha(
                    (
                        OUTPUT_ROOT / "frozen_final_compiled_semantic_ir.json"
                    ).read_bytes()
                ),
            },
            "implementation": {
                "artifact_id": implementation["artifact_id"],
                "content_subject_sha256": implementation["content_subject_sha256"],
                "final_file_sha256": sha(
                    (
                        OUTPUT_ROOT / "provisional_implementation_bundle.json"
                    ).read_bytes()
                ),
            },
        },
        "overlap_accounting": {
            "initial_prohibited_rows": 2,
            "corrected_prohibited_rows": ledger["prohibited_overlap_count"],
        },
        "proposition_accounting": {
            "behavioral": implementation["behavioral_proposition_count"],
            "synthesis": implementation["synthesis_proposition_count"],
            "actions": implementation["full_action_accounting_count"],
        },
        "risk_count": risk["risk_count"],
        "calibration_eligible_count": calibration["eligible_count"],
        "validation_summary": validation,
        "non_authorizations": [
            "accepted_semantic_reference",
            "canonical",
            "runtime",
            "persistence",
            "public",
            "publication",
            "production",
            "push",
            "pull_request",
            "merge",
            "deployment",
        ],
        "review_only_and_non_authorizing": True,
    }
    metadata = {
        "REVIEW_MANIFEST.json": (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode(),
        "COMMIT_METADATA.txt": run(
            "git", "show", "--no-patch", "--format=fuller", head
        ).encode(),
        "CHANGED_FILES.txt": changed_status.encode(),
        "IMPLEMENTATION.patch": run("git", "diff", "--binary", parent, head).encode(),
        "VALIDATION_REPORT.json": (OUTPUT_ROOT / "validation_report.json").read_bytes(),
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    zip_path = (
        output_directory / f"m5r1_foushee_justice_semantic_ir_review_{head[:8]}.zip"
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(metadata.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)
        for relative in sorted(required):
            raw = (ROOT / relative).read_bytes()
            info = zipfile.ZipInfo(
                f"repository/{relative}", date_time=(1980, 1, 1, 0, 0, 0)
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)

    expected = {**metadata}
    expected.update(
        {f"repository/{path}": (ROOT / path).read_bytes() for path in required}
    )
    with zipfile.ZipFile(zip_path, "r") as archive:
        if set(archive.namelist()) != set(expected):
            raise ValueError("ZIP entry set differs")
        for name, raw in expected.items():
            if archive.read(name) != raw:
                raise ValueError(f"ZIP byte parity differs: {name}")
    package_sha = sha(zip_path.read_bytes())
    sidecar = output_directory / "PACKAGE_SHA256.txt"
    sidecar.write_text(
        f"{package_sha}  {zip_path.name}\n", encoding="utf-8", newline="\n"
    )
    return {
        "archive_path": str(zip_path),
        "archive_final_file_sha256": package_sha,
        "included_repository_files": len(required),
        "metadata_files": len(metadata),
        "manifest_verification": "pass",
        "sidecar_path": str(sidecar),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.output_directory), sort_keys=True))


if __name__ == "__main__":
    main()
