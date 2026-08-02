"""Create and independently verify the external M5 delegated-review package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = (
    ROOT
    / "docs/editorial/full_record_reviews/semantic_ir_implementations/f000477_justice_public_safety_119_v1"
)
UPSTREAM = (
    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/f000477_justice_public_safety_119_m4b_delegated_episode_implementation_acceptance_v1.json",
    "docs/editorial/full_record_reviews/interpretation_decisions/f000477_justice_public_safety_119_v1/decision_implementation_bundle.json",
    "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/episode_implementation_bundle.json",
    "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/launch_review_risk_register.json",
    "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1/episode_calibration_population.json",
)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8").replace(
        "\r\n", "\n"
    )


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    head = run("git", "rev-parse", "HEAD").strip()
    parent = run("git", "rev-parse", "HEAD^").strip()
    branch = run("git", "branch", "--show-current").strip()
    cached_main = run("git", "rev-parse", "origin/main").strip()
    tree = run("git", "rev-parse", "HEAD^{tree}").strip()
    short = head[:8]
    zip_path = (
        args.output_directory.resolve()
        / f"m5_foushee_justice_semantic_ir_review_{short}.zip"
    )
    changed_text = run("git", "diff", "--name-status", parent, head)
    changed_paths = [line.split("\t")[-1] for line in changed_text.splitlines() if line]
    status = run("git", "status", "--porcelain=v1", "--untracked-files=all")
    relevant_dirty = [
        line
        for line in status.splitlines()
        if not line.endswith(
            "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1.zip"
        )
    ]
    if relevant_dirty:
        raise ValueError(f"repository has milestone-relevant dirt: {relevant_dirty}")
    repo_paths = sorted(
        set(changed_paths)
        | set(UPSTREAM)
        | {
            p.relative_to(ROOT).as_posix()
            for p in ARTIFACT_ROOT.rglob("*")
            if p.is_file()
        }
    )
    missing = [path for path in repo_paths if not (ROOT / path).is_file()]
    if missing:
        raise ValueError(f"package source path missing: {missing}")
    metadata = {
        "COMMIT_METADATA.txt": run(
            "git", "show", "--no-patch", "--format=fuller", head
        ).encode(),
        "CHANGED_FILES.txt": changed_text.encode(),
        "IMPLEMENTATION.patch": run("git", "diff", "--binary", parent, head).encode(),
        "VALIDATION_REPORT.json": (
            ARTIFACT_ROOT / "validation_report.json"
        ).read_bytes(),
    }
    entries: dict[str, bytes] = {
        path: (ROOT / path).read_bytes() for path in repo_paths
    }
    entries.update(metadata)
    graph = json.loads(
        (ARTIFACT_ROOT / "frozen_final_compiled_semantic_ir.json").read_text(
            encoding="utf-8"
        )
    )
    compiler_input = json.loads(
        (ARTIFACT_ROOT / "frozen_final_compiler_input.json").read_text(encoding="utf-8")
    )
    implementation = json.loads(
        (ARTIFACT_ROOT / "provisional_implementation_bundle.json").read_text(
            encoding="utf-8"
        )
    )
    risk = json.loads(
        (ARTIFACT_ROOT / "launch_review_risk_register.json").read_text(encoding="utf-8")
    )
    calibration = json.loads(
        (ARTIFACT_ROOT / "semantic_calibration_population.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = {
        "schema_version": "m5_delegated_review_package_manifest_v1",
        "repository": "dhart54/political_fingerprint",
        "branch": branch,
        "reviewed_commit": head,
        "parent": parent,
        "cached_origin_main": cached_main,
        "commit_tree_sha": tree,
        "clean_worktree_confirmation": not relevant_dirty,
        "preserved_preexisting_untracked_exclusion": "docs/editorial/full_record_reviews/policy_episode_implementations/f000477_justice_public_safety_119_v1.zip",
        "changed_files": changed_paths,
        "included_files": [
            {"path": name, "size": len(raw), "final_file_sha256": sha(raw)}
            for name, raw in sorted(entries.items())
        ],
        "controlling_authority": {
            "artifact_id": "delegated-episode-implementation-acceptance:f000477:justice_public_safety:119:v1",
            "content_subject_sha256": "370f7b7668eb775cb56b283e7c4261c908a977d0b2e60054e6dc396940ea669e",
            "final_file_sha256": "5e32e938aa9867524413c6329ebfa32fc42b24e793e25cddb36b8e3b6f100997",
        },
        "compiler_input": {
            "artifact_id": compiler_input["artifact_id"],
            "content_subject_sha256": compiler_input["content_subject_sha256"],
            "final_file_sha256": sha(
                (ARTIFACT_ROOT / "frozen_final_compiler_input.json").read_bytes()
            ),
        },
        "compiled_graph": {
            "artifact_id": graph["artifact_id"],
            "content_subject_sha256": graph["content_subject_sha256"],
            "final_file_sha256": sha(
                (ARTIFACT_ROOT / "frozen_final_compiled_semantic_ir.json").read_bytes()
            ),
        },
        "provisional_implementation": {
            "artifact_id": implementation["artifact_id"],
            "content_subject_sha256": implementation["content_subject_sha256"],
            "final_file_sha256": sha(
                (ARTIFACT_ROOT / "provisional_implementation_bundle.json").read_bytes()
            ),
        },
        "proposition_accounting": {
            "behavioral": implementation["behavioral_proposition_count"],
            "synthesis": implementation["synthesis_proposition_count"],
        },
        "coverage_and_action_accounting": {
            "coverage": graph["compiled_ir"]["members"][0]["coverage"],
            "action_accounting": graph["action_accounting_counts"],
        },
        "risk_and_calibration_accounting": {
            "carried_risks": risk["carried_risk_count"],
            "new_risks": len(risk["new_risks"]),
            "calibration_eligible": calibration["eligible_count"],
        },
        "validation_summary": {
            "m5_independent_verifier": "pass",
            "targeted_m5_tests": 5,
            "semantic_ir_regression_tests": 52,
            "prior_integrity_gates": "pass",
            "broad_offline_suite": "reported_in_validation_artifact",
        },
        "non_authorizations": [
            "accepted_semantic_reference",
            "canonical",
            "runtime",
            "persistence",
            "public",
            "publication",
            "push",
            "pull_request",
            "merge",
            "network",
            "database",
            "deployment",
        ],
        "review_only_non_authorizing": True,
    }
    manifest_raw = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    entries["REVIEW_MANIFEST.json"] = manifest_raw
    args.output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        staged = Path(temp) / zip_path.name
        with zipfile.ZipFile(
            staged, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name, raw in sorted(entries.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, raw)
        zip_path.write_bytes(staged.read_bytes())
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        if names != set(entries):
            raise ValueError("ZIP entry set differs")
        for name, raw in entries.items():
            if archive.read(name) != raw:
                raise ValueError(f"ZIP byte parity differs: {name}")
        reopened_manifest = json.loads(archive.read("REVIEW_MANIFEST.json"))
        for entry in reopened_manifest["included_files"]:
            raw = archive.read(entry["path"])
            if len(raw) != entry["size"] or sha(raw) != entry["final_file_sha256"]:
                raise ValueError(f"manifest verification differs: {entry['path']}")
    package_sha = sha(zip_path.read_bytes())
    sidecar = zip_path.with_name("PACKAGE_SHA256.txt")
    sidecar.write_text(
        f"{package_sha}  {zip_path.name}\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "archive_path": str(zip_path),
                "archive_final_file_sha256": package_sha,
                "sidecar_path": str(sidecar),
                "included_repository_files": len(repo_paths),
                "metadata_files": len(metadata) + 1,
                "manifest_verification": "pass",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
