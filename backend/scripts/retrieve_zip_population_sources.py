"""Retrieve or replay the pinned Census inputs for ZIP population weighting.

Raw artifacts are intentionally stored below .local/.  The committed manifest is
the independently reviewable inventory and checksum contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[2]
LOCAL_ROOT = ROOT / ".local" / "zip_population_weighting"
DEFAULT_MANIFEST = ROOT / "docs" / "source_manifests" / "zip_population_weighting_v1.json"
PARSER_VERSION = "zip_population_source_retrieval_v2"
ALLOWED_HOSTS = {"census.gov", "www.census.gov", "www2.census.gov", "api.census.gov"}
SOURCE_VINTAGE = "2020 Census tabulation blocks and resident population; 2020 ZCTAs; 119th Congressional District whole-block tabulation plan"

STATE_DIRECTORIES = {
    "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas",
    "ca": "California", "co": "Colorado", "ct": "Connecticut", "de": "Delaware",
    "dc": "District_of_Columbia", "fl": "Florida", "ga": "Georgia", "hi": "Hawaii",
    "id": "Idaho", "il": "Illinois", "in": "Indiana", "ia": "Iowa",
    "ks": "Kansas", "ky": "Kentucky", "la": "Louisiana", "me": "Maine",
    "md": "Maryland", "ma": "Massachusetts", "mi": "Michigan", "mn": "Minnesota",
    "ms": "Mississippi", "mo": "Missouri", "mt": "Montana", "ne": "Nebraska",
    "nv": "Nevada", "nh": "New_Hampshire", "nj": "New_Jersey", "nm": "New_Mexico",
    "ny": "New_York", "nc": "North_Carolina", "nd": "North_Dakota", "oh": "Ohio",
    "ok": "Oklahoma", "or": "Oregon", "pa": "Pennsylvania", "ri": "Rhode_Island",
    "sc": "South_Carolina", "sd": "South_Dakota", "tn": "Tennessee", "tx": "Texas",
    "ut": "Utah", "vt": "Vermont", "va": "Virginia", "wa": "Washington",
    "wv": "West_Virginia", "wi": "Wisconsin", "wy": "Wyoming",
}

PL_ROOT = "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171"
ZCTA_ROOT = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520"
CD_ROOT = "https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files/2025/119-congressional-district-befs"
EXPECTED_LANDING_PAGES = [
    f"{PL_ROOT}/",
    f"{ZCTA_ROOT}/",
    "https://www.census.gov/geographies/mapping-files/2025/dec/rdo/119-congressional-district-bef.html",
    "https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html",
]
EXPECTED_ORDERING_RULES = [
    "state PL artifacts by lowercase postal abbreviation",
    "block GEOIDs ascending within each state",
    "ZCTA/CD aggregates by ZCTA, state, district, source relationship identity",
    "rank population share descending, population descending, state ascending, district ascending, relationship identity ascending",
]


class SourceContractError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_inventory() -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for abbreviation, directory in sorted(STATE_DIRECTORIES.items()):
        filename = f"{abbreviation}2020.pl.zip"
        artifacts.append({
            "role": "block_population",
            "filename": filename,
            "url": f"{PL_ROOT}/{directory}/{filename}",
            "release_vintage": "2020 Census PL 94-171 state redistricting file, released 2021-08-12",
        })
    artifacts.extend([
        {
            "role": "block_to_zcta",
            "filename": "tab20_zcta520_tabblock20_natl.txt",
            "url": f"{ZCTA_ROOT}/tab20_zcta520_tabblock20_natl.txt",
            "release_vintage": "2020 ZCTA to 2020 tabulation block relationship file, posted 2021-12-09",
        },
        {
            "role": "block_to_cd119",
            "filename": "cd119.zip",
            "url": f"{CD_ROOT}/cd119.zip",
            "release_vintage": "119th Congress whole 2020 Census block tabulation plan, 2024 election cycle",
        },
        {
            "role": "technical_documentation",
            "filename": "2020Census_PL94_171Redistricting_StatesTechDoc_English.pdf",
            "url": "https://www2.census.gov/programs-surveys/decennial/2020/technical-documentation/complete-tech-docs/summary-file/2020Census_PL94_171Redistricting_StatesTechDoc_English.pdf",
            "release_vintage": "2020 Census PL 94-171 states technical documentation",
        },
        {
            "role": "technical_documentation",
            "filename": "explanation_tab20_zcta520_tabblock20_natl.pdf",
            "url": "https://www2.census.gov/geo/pdfs/maps-data/data/rel2020/zcta520/explanation_tab20_zcta520_tabblock20_natl.pdf",
            "release_vintage": "2020 ZCTA/tabulation-block relationship explanation",
        },
        {
            "role": "technical_documentation",
            "filename": "CD119_BlockSplits.pdf",
            "url": f"{CD_ROOT}/CD119_BlockSplits.pdf",
            "release_vintage": "119th Congress split-block listing",
        },
    ])
    return sorted(artifacts, key=lambda item: (item["role"], item["filename"]))


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise SourceContractError(f"official-host allowlist failure: {url}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_local_artifact(spec: dict[str, str], path: Path) -> dict[str, str]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SourceContractError(f"local artifact is missing or empty: {path.name}")
    try:
        if path.suffix == ".zip":
            with ZipFile(path) as archive:
                if not archive.namelist() or archive.testzip() is not None:
                    raise SourceContractError(f"ZIP CRC validation failed: {path.name}")
            method = "zip_crc_and_member_inventory"
        elif path.suffix == ".pdf":
            with path.open("rb") as handle:
                signature = handle.read(5)
            if signature != b"%PDF-":
                raise SourceContractError(f"PDF signature validation failed: {path.name}")
            method = "pdf_signature"
        else:
            with path.open("rb") as handle:
                header = handle.readline(4096)
            if spec["role"] == "block_to_zcta" and b"GEOID_TABBLOCK_20" not in header:
                raise SourceContractError(f"text header validation failed: {path.name}")
            method = "required_text_header"
    except BadZipFile as exc:
        raise SourceContractError(f"ZIP validation failed: {path.name}") from exc
    return {"method": method, "result": "passed"}


def retrieve_one(spec: dict[str, str], destination: Path, retries: int = 3) -> dict[str, Any]:
    validate_url(spec["url"])
    history: list[dict[str, Any]] = []
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "PoliticalFingerprintSourceAudit/1.0"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
                status = int(getattr(response, "status", 200))
                content_type = response.headers.get_content_type()
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            history.append({"attempt": attempt, "status": status, "result": "success"})
            return {
                **spec,
                "actual_filename": destination.name,
                "retrieval_mode": "direct_http",
                "http_status": status,
                "content_type": content_type,
                "retrieved_at": utc_now(),
                "retrieval_timestamp_status": "recorded",
                "size_bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
                "retry_history": history,
            }
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            destination.unlink(missing_ok=True)
            history.append({"attempt": attempt, "result": "error", "error_type": type(exc).__name__})
            if attempt == retries:
                raise SourceContractError(f"retrieval failed for {spec['url']}: {type(exc).__name__}") from exc
            time.sleep(min(2 ** (attempt - 1), 4))
    raise AssertionError("unreachable")


def resume_existing(spec: dict[str, str], path: Path) -> dict[str, Any]:
    """Revalidate a completed artifact left by the same interrupted retrieval."""
    validation = validate_local_artifact(spec, path)
    return {
        **spec,
        "actual_filename": path.name,
        "retrieval_mode": "validated_local_resume",
        "validated_at": utc_now(),
        "validation": validation,
        "original_http_status": None,
        "original_content_type": None,
        "original_retrieved_at": None,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "retry_history": [{"attempt": 0, "result": "validated_local_resume_after_interrupted_official_retrieval"}],
    }


def inventory_identity(items: list[dict[str, Any]]) -> str:
    identity = [{key: item[key] for key in ("role", "filename", "url", "release_vintage")} for item in items]
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_manifest(batch_id: str, artifacts: list[dict[str, Any]], *, batch_completed_at: str | None = None) -> dict[str, Any]:
    expected = expected_inventory()
    return {
        "schema_version": "zip_population_weighting_source_manifest_v2",
        "batch_id": batch_id,
        "batch_completed_at": batch_completed_at or utc_now(),
        "batch_completion_precision": "timestamp",
        "parser_version": PARSER_VERSION,
        "source_vintage": SOURCE_VINTAGE,
        "allowed_hosts": sorted(ALLOWED_HOSTS),
        "landing_pages": EXPECTED_LANDING_PAGES,
        "expected_artifact_count": len(expected),
        "expected_inventory_sha256": inventory_identity(expected),
        "derivation_ordering_rules": EXPECTED_ORDERING_RULES,
        "artifacts": sorted(artifacts, key=lambda item: (item["role"], item["filename"])),
    }


def replay_manifest(manifest_path: Path, batch_root: Path | None = None) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "zip_population_weighting_source_manifest_v2":
        raise SourceContractError("unsupported manifest schema")
    if manifest.get("parser_version") != PARSER_VERSION:
        raise SourceContractError("parser version differs")
    if manifest.get("source_vintage") != SOURCE_VINTAGE:
        raise SourceContractError("source vintage differs")
    if set(manifest.get("allowed_hosts", [])) != ALLOWED_HOSTS:
        raise SourceContractError("official-host allowlist differs")
    if manifest.get("landing_pages") != EXPECTED_LANDING_PAGES:
        raise SourceContractError("approved landing-page set differs")
    if manifest.get("derivation_ordering_rules") != EXPECTED_ORDERING_RULES:
        raise SourceContractError("approved derivation ordering rules differ")
    if not manifest.get("batch_completed_at") or manifest.get("retrieved_at") is not None:
        raise SourceContractError("batch completion and retrieval provenance fields differ")
    expected = expected_inventory()
    actual = manifest.get("artifacts", [])
    if manifest.get("expected_artifact_count") != len(expected):
        raise SourceContractError("expected artifact count differs")
    if manifest.get("expected_inventory_sha256") != inventory_identity(expected):
        raise SourceContractError("expected source inventory checksum differs")
    expected_keys = {(x["role"], x["filename"], x["url"], x["release_vintage"]) for x in expected}
    actual_keys = {(x.get("role"), x.get("filename"), x.get("url"), x.get("release_vintage")) for x in actual}
    if actual_keys != expected_keys or len(actual) != len(expected):
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        raise SourceContractError(f"manifest inventory mismatch: missing={missing[:3]} extra={extra[:3]}")
    if not any(x["role"] == "technical_documentation" for x in actual):
        raise SourceContractError("required technical documentation absent")
    root = batch_root or LOCAL_ROOT / manifest["batch_id"]
    raw = root / "raw"
    for item in actual:
        validate_url(item["url"])
        path = raw / item["actual_filename"]
        if item["actual_filename"] != item["filename"]:
            raise SourceContractError(f"filename differs: {item['filename']}")
        if not path.is_file():
            raise SourceContractError(f"artifact missing: {item['filename']}")
        if path.stat().st_size != item["size_bytes"]:
            raise SourceContractError(f"byte size differs: {item['filename']}")
        if sha256_file(path) != item["sha256"]:
            raise SourceContractError(f"checksum differs: {item['filename']}")
        mode = item.get("retrieval_mode")
        if mode == "direct_http":
            if item.get("http_status") != 200 or not item.get("content_type"):
                raise SourceContractError(f"direct HTTP provenance incomplete: {item['filename']}")
            if item.get("retrieved_at") is None and item.get("retrieval_timestamp_status") != "unavailable_not_persisted":
                raise SourceContractError(f"direct HTTP retrieval time uncertainty is not explicit: {item['filename']}")
            if item.get("retrieved_at") is not None and item.get("retrieval_timestamp_status") != "recorded":
                raise SourceContractError(f"direct HTTP retrieval time status differs: {item['filename']}")
            if not item.get("retry_history") or item["retry_history"][-1].get("result") != "success":
                raise SourceContractError(f"direct HTTP retry history incomplete: {item['filename']}")
        elif mode == "validated_local_resume":
            if item.get("http_status") is not None or item.get("content_type") is not None:
                raise SourceContractError(f"local resume fabricates current HTTP provenance: {item['filename']}")
            if item.get("original_http_status") is not None or item.get("original_content_type") is not None or item.get("original_retrieved_at") is not None:
                raise SourceContractError(f"local resume fabricates original HTTP provenance: {item['filename']}")
            if not item.get("validated_at") or item.get("validation", {}).get("result") != "passed":
                raise SourceContractError(f"local resume validation provenance incomplete: {item['filename']}")
        else:
            raise SourceContractError(f"unsupported retrieval provenance mode: {item['filename']}")
    actual_files = {p.name for p in raw.iterdir() if p.is_file() and not p.name.endswith(".partial")}
    expected_files = {item["filename"] for item in actual}
    if actual_files != expected_files:
        raise SourceContractError(f"raw directory inventory differs: added={sorted(actual_files-expected_files)} missing={sorted(expected_files-actual_files)}")
    return {"batch_id": manifest["batch_id"], "artifact_count": len(actual), "replay_verified": True}


def revalidate_existing_manifest(manifest_path: Path, manifest_output: Path, batch_root: Path | None = None) -> dict[str, Any]:
    old = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = batch_root or LOCAL_ROOT / old["batch_id"]
    raw = root / "raw"
    expected_by_name = {item["filename"]: item for item in expected_inventory()}
    artifacts = []
    for item in old.get("artifacts", []):
        spec = expected_by_name.get(item.get("filename"))
        if spec is None:
            raise SourceContractError(f"existing manifest contains an unexpected artifact: {item.get('filename')}")
        path = raw / spec["filename"]
        if path.stat().st_size != item.get("size_bytes") or sha256_file(path) != item.get("sha256"):
            raise SourceContractError(f"existing artifact identity differs before provenance rewrite: {spec['filename']}")
        prior_resume = item.get("retrieval_mode") == "validated_local_resume" or (
            item.get("retry_history") and item["retry_history"][0].get("attempt") == 0
        )
        if prior_resume:
            normalized = resume_existing(spec, path)
        else:
            validation = validate_local_artifact(spec, path)
            normalized = {
                **spec,
                "actual_filename": path.name,
                "retrieval_mode": "direct_http",
                "http_status": item.get("http_status"),
                "content_type": item.get("content_type"),
                "retrieved_at": item.get("retrieved_at"),
                "retrieval_timestamp_status": "recorded" if item.get("retrieved_at") else "unavailable_not_persisted",
                "retry_history": item.get("retry_history", []),
                "local_validation": {**validation, "validated_at": utc_now()},
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        artifacts.append(normalized)
    manifest = build_manifest(old["batch_id"], artifacts)
    manifest_output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return {"batch_id": old["batch_id"], "artifact_count": len(artifacts), "manifest": str(manifest_output), "revalidated_without_download": True}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--retrieve-official-sources", action="store_true")
    modes.add_argument("--replay-manifest", type=Path)
    modes.add_argument("--revalidate-existing-manifest", type=Path)
    parser.add_argument("--batch-id")
    parser.add_argument("--batch-root", type=Path)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--resume", action="store_true", help="CRC/signature-check completed artifacts from the same interrupted official retrieval")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.retrieve_official_sources:
        if not args.batch_id or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{5,80}", args.batch_id):
            raise SourceContractError("--batch-id is required and must be a stable safe identifier")
        root = args.batch_root or LOCAL_ROOT / args.batch_id
        raw = root / "raw"
        (root / "derived").mkdir(parents=True, exist_ok=True)
        raw.mkdir(parents=True, exist_ok=True)
        artifacts = []
        for spec in expected_inventory():
            destination = raw / spec["filename"]
            artifacts.append(resume_existing(spec, destination) if args.resume and destination.exists() else retrieve_one(spec, destination))
        manifest = build_manifest(args.batch_id, artifacts)
        args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"batch_id": args.batch_id, "artifact_count": len(artifacts), "manifest": str(args.manifest_output)}))
        return 0
    if args.revalidate_existing_manifest:
        result = revalidate_existing_manifest(args.revalidate_existing_manifest, args.manifest_output, args.batch_root)
        print(json.dumps(result, sort_keys=True))
        return 0
    result = replay_manifest(args.replay_manifest, args.batch_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
