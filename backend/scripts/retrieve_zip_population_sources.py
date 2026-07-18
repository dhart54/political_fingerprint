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
PARSER_VERSION = "zip_population_source_retrieval_v1"
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
                "http_status": status,
                "content_type": content_type,
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
    if not path.is_file() or path.stat().st_size == 0:
        raise SourceContractError(f"resume artifact is missing or empty: {path.name}")
    try:
        if path.suffix == ".zip":
            with ZipFile(path) as archive:
                if not archive.namelist() or archive.testzip() is not None:
                    raise SourceContractError(f"resume ZIP CRC validation failed: {path.name}")
            content_type = "application/zip"
        elif path.suffix == ".pdf":
            if not path.read_bytes()[:5] == b"%PDF-":
                raise SourceContractError(f"resume PDF signature validation failed: {path.name}")
            content_type = "application/pdf"
        else:
            with path.open("rb") as handle:
                header = handle.readline(4096)
            if spec["role"] == "block_to_zcta" and b"GEOID_TABBLOCK_20" not in header:
                raise SourceContractError(f"resume text header validation failed: {path.name}")
            content_type = "text/plain"
    except BadZipFile as exc:
        raise SourceContractError(f"resume ZIP validation failed: {path.name}") from exc
    return {
        **spec,
        "actual_filename": path.name,
        "http_status": 200,
        "content_type": content_type,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "retry_history": [{"attempt": 0, "result": "validated_local_resume_after_interrupted_official_retrieval"}],
    }


def inventory_identity(items: list[dict[str, Any]]) -> str:
    identity = [{key: item[key] for key in ("role", "filename", "url", "release_vintage")} for item in items]
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_manifest(batch_id: str, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    expected = expected_inventory()
    return {
        "schema_version": "zip_population_weighting_source_manifest_v1",
        "batch_id": batch_id,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_precision": "timestamp",
        "parser_version": PARSER_VERSION,
        "source_vintage": SOURCE_VINTAGE,
        "allowed_hosts": sorted(ALLOWED_HOSTS),
        "landing_pages": [
            f"{PL_ROOT}/",
            f"{ZCTA_ROOT}/",
            "https://www.census.gov/geographies/mapping-files/2025/dec/rdo/119-congressional-district-bef.html",
            "https://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html",
        ],
        "expected_artifact_count": len(expected),
        "expected_inventory_sha256": inventory_identity(expected),
        "derivation_ordering_rules": [
            "state PL artifacts by lowercase postal abbreviation",
            "block GEOIDs ascending within each state",
            "ZCTA/CD aggregates by ZCTA, state, district, source relationship identity",
            "rank population share descending, population descending, state ascending, district ascending, relationship identity ascending",
        ],
        "artifacts": sorted(artifacts, key=lambda item: (item["role"], item["filename"])),
    }


def replay_manifest(manifest_path: Path, batch_root: Path | None = None) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "zip_population_weighting_source_manifest_v1":
        raise SourceContractError("unsupported manifest schema")
    if manifest.get("parser_version") != PARSER_VERSION:
        raise SourceContractError("parser version differs")
    if manifest.get("source_vintage") != SOURCE_VINTAGE:
        raise SourceContractError("source vintage differs")
    if set(manifest.get("allowed_hosts", [])) != ALLOWED_HOSTS:
        raise SourceContractError("official-host allowlist differs")
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
        if item.get("http_status") != 200 or not item.get("content_type"):
            raise SourceContractError(f"HTTP provenance incomplete: {item['filename']}")
    actual_files = {p.name for p in raw.iterdir() if p.is_file() and not p.name.endswith(".partial")}
    expected_files = {item["filename"] for item in actual}
    if actual_files != expected_files:
        raise SourceContractError(f"raw directory inventory differs: added={sorted(actual_files-expected_files)} missing={sorted(expected_files-actual_files)}")
    return {"batch_id": manifest["batch_id"], "artifact_count": len(actual), "replay_verified": True}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--retrieve-official-sources", action="store_true")
    modes.add_argument("--replay-manifest", type=Path)
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
    result = replay_manifest(args.replay_manifest, args.batch_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
