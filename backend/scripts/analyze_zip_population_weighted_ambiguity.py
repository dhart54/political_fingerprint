"""Exact 2020-block population evaluation for ZCTA/CD119 ambiguity.

The primary method is a three-way common-block join.  No geometry or area
apportionment is used for population allocation.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import io
import json
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Iterator, TextIO
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.scripts import analyze_zip_overlap_sensitivity as land
from backend.scripts import dry_run_zip_source_import as source_import
from backend.scripts import retrieve_zip_population_sources as retrieval

PARSER_VERSION = "zip_population_common_block_parser_v1"
SCHEMA_VERSION = "zip_population_weighted_ambiguity_evaluation_v1"
SNAPSHOT_ID = land.SNAPSHOT_ID
EXPECTED_0015_SHA256 = land.EXPECTED_CANDIDATE_MIGRATION_SHA256
EXPECTED_SOURCE_MANIFEST_SHA256 = "df3201bad66134eee6be59f53cd72e19c9d39c286fe5ce1389a1021412c9a851"
EXPECTED_NATIONAL_INVARIANTS = {
    "block_count": 8_132_968,
    "source_population": 331_449_281,
    "population_bearing_blocks": 5_769_942,
    "zero_population_blocks": 2_363_026,
    "assigned_zcta_population": 331_440_751,
    "outside_zcta_population": 8_530,
    "unassigned_district_blocks": 89,
    "unassigned_district_population": 0,
}
EXPECTED_STATE_TOTALS_SHA256 = "624c188080e4a00878785d95a1d9bf2ff53f16bdd0ab06bc3824e8bad5b7ad2f"
EXPECTED_LAND_SOURCE = {"filename": "tab20_cd11920_zcta520_natl.txt", "size_bytes": 6_195_997, "sha256": "57fad59f65af5179ddd18dcfb8f72482dc0cf04fe26e2b9b2b34c51c04405f77"}
EXPECTED_LAND_BASELINE = {
    "raw_rows": 40_397, "accepted_rows": 39_967, "rejected_rows": 430,
    "unique_zctas": 33_642, "source_state_district_pairs": 436,
}
SPLIT_BLOCK = "080010096072000"
SPLIT_BLOCK_CD = "08"
POPULATION_THRESHOLDS = (
    ("p0_all", None), ("p1_positive", Fraction(0)),
    ("gte_0_01_percent", Fraction(1, 10_000)), ("gte_0_05_percent", Fraction(5, 10_000)),
    ("gte_0_1_percent", Fraction(1, 1_000)), ("gte_0_5_percent", Fraction(5, 1_000)),
    ("gte_1_percent", Fraction(1, 100)), ("gte_2_percent", Fraction(2, 100)),
    ("gte_5_percent", Fraction(5, 100)), ("gte_10_percent", Fraction(10, 100)),
    ("gte_25_percent", Fraction(25, 100)), ("gte_50_percent", Fraction(1, 2)),
)
DOMINANCE_THRESHOLDS = tuple(Fraction(x, 100) for x in (50, 60, 70, 75, 80, 90, 95))
MARGIN_THRESHOLDS = tuple(Fraction(x, 100) for x in (1, 5, 10, 20, 25, 33, 50))


class PopulationAnalysisError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def checksum(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def verify_approved_source_manifest(path: Path) -> str:
    actual = retrieval.sha256_file(path)
    if actual != EXPECTED_SOURCE_MANIFEST_SHA256:
        raise PopulationAnalysisError(
            f"approved source manifest exact-byte SHA-256 differs: expected {EXPECTED_SOURCE_MANIFEST_SHA256}, got {actual}"
        )
    return actual


def parse_block_geoid(value: str, line_number: int) -> str:
    value = value.strip()
    if not re.fullmatch(r"\d{15}", value):
        raise PopulationAnalysisError(f"line {line_number}: malformed 15-digit block GEOID: {value!r}")
    return value


def parse_population(value: str | None, line_number: int) -> int:
    if value is None or not re.fullmatch(r"\d+", value.strip()):
        raise PopulationAnalysisError(f"line {line_number}: missing or invalid total population")
    result = int(value)
    if result < 0:
        raise PopulationAnalysisError(f"line {line_number}: negative population")
    return result


def validate_population_records(records: Iterable[tuple[str, int]]) -> dict[str, int]:
    observed: dict[str, int] = {}
    total = 0
    for line_number, (raw_geoid, population) in enumerate(records, 1):
        geoid = parse_block_geoid(raw_geoid, line_number)
        if population < 0:
            raise PopulationAnalysisError(f"line {line_number}: negative population")
        if geoid in observed:
            if observed[geoid] != population:
                raise PopulationAnalysisError(f"conflicting population for block {geoid}")
            raise PopulationAnalysisError(f"duplicate block GEOID: {geoid}")
        observed[geoid] = population
        total += population
    return {"block_count": len(observed), "population": total}


def exact_threshold(numerator: int, denominator: int, threshold: Fraction, *, positive: bool = False) -> bool:
    if denominator <= 0:
        return False
    if positive and threshold == 0:
        return numerator > 0
    return numerator * threshold.denominator >= denominator * threshold.numerator


def majority_status(numerator: int, denominator: int) -> dict[str, bool]:
    if denominator <= 0:
        return {
            "inclusive_gte_50_percent": False,
            "strict_majority": False,
            "exactly_half": False,
            "no_strict_majority": True,
        }
    doubled = numerator * 2
    return {
        "inclusive_gte_50_percent": doubled >= denominator,
        "strict_majority": doubled > denominator,
        "exactly_half": doubled == denominator,
        "no_strict_majority": doubled <= denominator,
    }


def population_rank_key(row: dict[str, Any]) -> tuple[Any, ...]:
    denominator = int(row["zcta_population"])
    population = int(row["relationship_population"])
    share = Fraction(population, denominator) if denominator else Fraction(0)
    return (-share, -population, row["canonical_state"], row["source_district"], row["source_relationship_identity"])


def rank_population_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted((dict(row) for row in rows), key=population_rank_key)
    if not ranked:
        return ranked
    zero_population = all(int(row["zcta_population"]) == 0 for row in ranked)
    previous: tuple[int, int] | None = None
    rank = 0
    for index, row in enumerate(ranked, 1):
        row["deterministic_relationship_order"] = index
        if zero_population:
            row["population_rank"] = None
            row["population_rank_tied"] = None
            row["population_rank_status"] = "undefined_zero_population_zcta"
            continue
        signature = (int(row["relationship_population"]), int(row["zcta_population"]))
        if signature != previous:
            rank = index
        row["population_rank"] = rank
        row["population_rank_tied"] = sum(
            int(other["relationship_population"]) * int(row["zcta_population"])
            == int(row["relationship_population"]) * int(other["zcta_population"])
            for other in ranked
        ) > 1
        row["population_rank_status"] = "ranked_positive_population"
        previous = signature
    return ranked


def validate_assignment(block: str, population: int, zctas: list[str], districts: list[str]) -> str:
    if len(set(zctas)) > 1:
        raise PopulationAnalysisError(f"conflicting ZCTA assignment for block {block}")
    if len(set(districts)) > 1:
        if population > 0:
            raise PopulationAnalysisError(f"split_populated_block_unresolved: {block}")
        return "split_zero_population_block"
    if block == SPLIT_BLOCK:
        if districts != [SPLIT_BLOCK_CD]:
            raise PopulationAnalysisError("Colorado split block lacks the authoritative CD08 tabulation assignment")
        return "exact_official_assignment"
    return "exact_official_common_block"


def _open_outputs(directory: Path) -> dict[str, TextIO]:
    directory.mkdir(parents=True, exist_ok=True)
    return {fips: (directory / f"{fips}.txt").open("w", encoding="ascii", newline="\n") for fips in source_import.STATE_FIPS_TO_ABBR}


def _external_sort_state_files(directory: Path, chunk_size: int = 250_000) -> dict[str, int]:
    duplicate_count = 0
    reordered_states = 0
    for path in sorted(directory.glob("*.txt")):
        chunks: list[Path] = []
        source_was_sorted = True
        previous_input = ""
        with path.open("r", encoding="ascii") as source:
            while True:
                lines = [line for _, line in zip(range(chunk_size), source)]
                if not lines:
                    break
                for line in lines:
                    geoid = line[:15]
                    if previous_input and geoid < previous_input:
                        source_was_sorted = False
                    previous_input = geoid
                lines.sort()
                chunk = path.with_name(f"{path.name}.chunk{len(chunks):03d}")
                with chunk.open("w", encoding="ascii", newline="\n") as output:
                    output.writelines(lines)
                chunks.append(chunk)
        temp = path.with_suffix(".sorted")
        handles = [chunk.open("r", encoding="ascii") for chunk in chunks]
        previous = ""
        try:
            with temp.open("w", encoding="ascii", newline="\n") as output:
                for line in heapq.merge(*handles):
                    geoid = line[:15]
                    if geoid == previous:
                        duplicate_count += 1
                    elif previous and geoid < previous:
                        raise PopulationAnalysisError(f"external block sort failed: {path.name}")
                    previous = geoid
                    output.write(line)
        finally:
            for handle in handles:
                handle.close()
            for chunk in chunks:
                chunk.unlink(missing_ok=True)
        temp.replace(path)
        reordered_states += not source_was_sorted
    return {"duplicate_block_geoids": duplicate_count, "reordered_states": reordered_states}


def split_cd119(raw_zip: Path, derived: Path) -> dict[str, Any]:
    outputs = _open_outputs(derived / "cd_by_state")
    counts = Counter()
    try:
        with ZipFile(raw_zip) as archive:
            names = set(archive.namelist())
            expected = {"NationalCD119.txt", "01_AL_CD119.txt", "13_GA_CD119.txt", "22_LA_CD119.txt", "36_NY_CD119.txt", "37_NC_CD119.txt"}
            if names != expected:
                raise PopulationAnalysisError(f"CD119 ZIP inventory differs: {sorted(names)}")
            with archive.open("NationalCD119.txt") as source:
                header = source.readline().decode("ascii").strip()
                if header != "GEOID,CDFP":
                    raise PopulationAnalysisError("CD119 header differs")
                for line_number, raw in enumerate(source, 2):
                    geoid, district = raw.decode("ascii").strip().split(",")
                    geoid = parse_block_geoid(geoid, line_number)
                    fips = geoid[:2]
                    if fips not in outputs:
                        continue
                    if district != "ZZ" and not re.fullmatch(r"(?:00|98|0[1-9]|[1-4]\d|5[0-3])", district):
                        raise PopulationAnalysisError(f"line {line_number}: malformed CD119 code")
                    outputs[fips].write(f"{geoid}|{district}|{line_number}\n")
                    counts[fips] += 1
    finally:
        for output in outputs.values():
            output.close()
    ordering = _external_sort_state_files(derived / "cd_by_state")
    if ordering["duplicate_block_geoids"]:
        raise PopulationAnalysisError(f"duplicate CD119 block GEOIDs: {ordering['duplicate_block_geoids']}")
    return {"supported_block_rows": sum(counts.values()), "state_counts": dict(sorted(counts.items())), **ordering}


def split_zcta_blocks(raw_path: Path, derived: Path) -> dict[str, Any]:
    outputs = _open_outputs(derived / "zcta_by_state")
    counts = Counter()
    unassigned = 0
    try:
        with raw_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter="|")
            required = {"GEOID_ZCTA5_20", "GEOID_TABBLOCK_20", "AREALAND_PART", "AREAWATER_PART"}
            if not required.issubset(reader.fieldnames or []):
                raise PopulationAnalysisError("ZCTA/block relationship layout differs")
            for line_number, row in enumerate(reader, 2):
                geoid = parse_block_geoid(row["GEOID_TABBLOCK_20"], line_number)
                fips = geoid[:2]
                if fips not in outputs:
                    continue
                zcta = row["GEOID_ZCTA5_20"].strip()
                if zcta and not re.fullmatch(r"\d{5}", zcta):
                    raise PopulationAnalysisError(f"line {line_number}: malformed ZCTA")
                outputs[fips].write(f"{geoid}|{zcta}|{line_number}\n")
                counts[fips] += 1
                unassigned += not bool(zcta)
    finally:
        for output in outputs.values():
            output.close()
    ordering = _external_sort_state_files(derived / "zcta_by_state")
    if ordering["duplicate_block_geoids"]:
        raise PopulationAnalysisError(f"blocks assigned to multiple ZCTAs: {ordering['duplicate_block_geoids']}")
    return {"supported_block_rows": sum(counts.values()), "state_counts": dict(sorted(counts.items())), "unassigned_zcta_blocks": unassigned, **ordering}


def _derived_rows(path: Path) -> Iterator[tuple[str, str, int]]:
    with path.open("r", encoding="ascii") as handle:
        for raw in handle:
            geoid, assignment, line = raw.rstrip("\n").split("|")
            yield geoid, assignment, int(line)


def _next_or_none(iterator: Iterator[Any]) -> Any | None:
    try:
        return next(iterator)
    except StopIteration:
        return None


def pl_block_rows(path: Path, abbreviation: str) -> Iterator[tuple[str, int, int]]:
    geo_name = f"{abbreviation}geo2020.pl"
    data_name = f"{abbreviation}000012020.pl"
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        if geo_name not in names or data_name not in names:
            raise PopulationAnalysisError(f"PL ZIP layout differs for {abbreviation}")
        with archive.open(geo_name) as geo, archive.open(data_name) as data:
            previous = ""
            for line_number, (geo_raw, data_raw) in enumerate(zip(geo, data, strict=True), 1):
                g = geo_raw.decode("latin-1").rstrip("\r\n").split("|")
                p = data_raw.decode("ascii").rstrip("\r\n").split("|")
                if len(g) < 10 or len(p) < 6 or g[7] != p[4]:
                    raise PopulationAnalysisError(f"PL geography/data LOGRECNO mismatch at {abbreviation}:{line_number}")
                if g[2] != "750":
                    continue
                geoid = parse_block_geoid(g[9], line_number)
                if geoid <= previous:
                    raise PopulationAnalysisError(f"duplicate or unsorted PL block GEOID: {geoid}")
                previous = geoid
                yield geoid, parse_population(p[5], line_number), line_number


def merge_state_blocks(
    population_rows: Iterable[tuple[str, int, int]],
    zcta_rows: Iterable[tuple[str, str, int]],
    district_rows: Iterable[tuple[str, str, int]],
) -> Iterator[tuple[str, int, int, str, int, str, int]]:
    z_iter = iter(zcta_rows)
    c_iter = iter(district_rows)
    zrow = _next_or_none(z_iter)
    crow = _next_or_none(c_iter)
    previous = ""
    for block, population, pl_line in population_rows:
        if block <= previous:
            raise PopulationAnalysisError(f"duplicate or unsorted population block GEOID: {block}")
        previous = block
        if zrow is None or zrow[0] != block:
            raise PopulationAnalysisError(f"block population cannot join exact ZCTA GEOID: {block}")
        if crow is None or crow[0] != block:
            raise PopulationAnalysisError(f"block population cannot join exact CD119 GEOID: {block}")
        yield block, population, pl_line, zrow[1], zrow[2], crow[1], crow[2]
        zrow = _next_or_none(z_iter)
        crow = _next_or_none(c_iter)
    if zrow is not None or crow is not None:
        raise PopulationAnalysisError("population source does not cover every official block assignment")


def join_common_blocks(raw: Path, derived: Path, batch_id: str) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, dict[str, int]]]:
    aggregates: dict[tuple[str, str, str], dict[str, Any]] = {}
    zcta_unassigned: dict[str, Counter[str]] = defaultdict(Counter)
    anomalies = Counter()
    totals = Counter()
    affected_population = Counter()
    state_totals: list[dict[str, Any]] = []
    split_record: dict[str, Any] | None = None
    ledger_path = derived / "normalized_block_population_evidence.jsonl.gz"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    raw_ledger = ledger_path.open("wb")
    compressed = gzip.GzipFile(filename="", mode="wb", fileobj=raw_ledger, mtime=0)
    ledger = io.TextIOWrapper(compressed, encoding="utf-8", newline="\n")
    inverse = {abbr.lower(): fips for fips, abbr in source_import.STATE_FIPS_TO_ABBR.items()}
    try:
        for abbreviation in sorted(retrieval.STATE_DIRECTORIES):
            fips = inverse[abbreviation]
            state = source_import.STATE_FIPS_TO_ABBR[fips]
            z_iter = _derived_rows(derived / "zcta_by_state" / f"{fips}.txt")
            c_iter = _derived_rows(derived / "cd_by_state" / f"{fips}.txt")
            state_total = Counter()
            merged = merge_state_blocks(pl_block_rows(raw / f"{abbreviation}2020.pl.zip", abbreviation), z_iter, c_iter)
            for block, population, pl_line, zcta, zcta_line, district, cd_line in merged:
                totals["blocks"] += 1
                totals["source_population"] += population
                totals["population_bearing_blocks"] += population > 0
                totals["zero_population_blocks"] += population == 0
                state_total["block_count"] += 1
                state_total["population"] += population
                state_total["population_bearing_blocks"] += population > 0
                state_total["zero_population_blocks"] += population == 0
                base_quality = validate_assignment(block, population, [zcta], [district])
                quality = "unassigned_zcta" if not zcta else "unassigned_district" if district == "ZZ" else base_quality
                if base_quality == "exact_official_assignment":
                    split_record = {"block_geoid": block, "population": population, "zcta": zcta, "district": district, "assignment_quality": base_quality, "pl_record": pl_line, "zcta_record": zcta_line, "cd_record": cd_line}
                ledger_row = {
                    "source_snapshot_id": batch_id,
                    "population_source_artifact": f"{abbreviation}2020.pl.zip",
                    "geography_source_artifacts": ["tab20_zcta520_tabblock20_natl.txt", "cd119.zip"],
                    "block_geoid": block, "state_fips": block[:2], "county_fips": block[2:5],
                    "tract": block[5:11], "block": block[11:15], "zcta": zcta or None,
                    "source_cd119_geoid": f"{fips}{district}", "canonical_state": state,
                    "source_district": district, "total_population": population,
                    "zcta_assignment_method": "official_2020_zcta_tabblock_relationship",
                    "district_assignment_method": "official_cd119_whole_block_equivalency",
                    "assignment_quality": quality,
                    "source_record_identity": {"pl_logical_record": pl_line, "zcta_line": zcta_line, "cd119_line": cd_line},
                    "parser_version": PARSER_VERSION,
                }
                ledger.write(canonical_json(ledger_row) + "\n")
                if not zcta:
                    anomalies["unassigned_zcta"] += 1
                    affected_population["unassigned_zcta"] += population
                elif district == "ZZ":
                    anomalies["unassigned_district"] += 1
                    affected_population["unassigned_district"] += population
                    zcta_unassigned[zcta]["block_count"] += 1
                    zcta_unassigned[zcta]["population"] += population
                    if population:
                        raise PopulationAnalysisError(f"population-bearing block without district: {block}")
                else:
                    key = (zcta, state, district)
                    row = aggregates.setdefault(key, {
                        "zcta": zcta, "canonical_state": state, "source_district": district,
                        "relationship_population": 0, "contributing_blocks": 0,
                        "populated_contributing_blocks": 0, "zero_population_contributing_blocks": 0,
                        "excluded_block_count": 0, "excluded_population": 0,
                        "assignment_quality_counts": Counter(),
                    })
                    row["relationship_population"] += population
                    row["contributing_blocks"] += 1
                    row["populated_contributing_blocks"] += population > 0
                    row["zero_population_contributing_blocks"] += population == 0
                    row["assignment_quality_counts"][base_quality] += 1
                    totals["assigned_zcta_population"] += population
            state_totals.append({"fips": fips, "state": state, **dict(state_total)})
    finally:
        ledger.flush()
        ledger.close()
    if split_record is None:
        raise PopulationAnalysisError("official Colorado split-block assignment was not observed")
    quality_counts = Counter()
    for row in aggregates.values():
        quality_counts.update(row["assignment_quality_counts"])
        row["assignment_quality_counts"] = dict(sorted(row["assignment_quality_counts"].items()))
        row["assignment_quality"] = "exact_official_assignment" if "exact_official_assignment" in row["assignment_quality_counts"] else "exact_official_common_block"
    state_totals = sorted(state_totals, key=lambda row: row["fips"])
    affected_zctas = [
        {"zcta": zcta, "block_count": values["block_count"], "population": values["population"]}
        for zcta, values in sorted(zcta_unassigned.items()) if zcta
    ]
    state_totals_sha256 = checksum(state_totals)
    integrity = {
        "block_count": totals["blocks"], "source_population": totals["source_population"],
        "population_bearing_blocks": totals["population_bearing_blocks"], "zero_population_blocks": totals["zero_population_blocks"],
        "assigned_zcta_population": totals["assigned_zcta_population"],
        "anomaly_counts": dict(sorted(anomalies.items())),
        "affected_population": dict(sorted(affected_population.items())),
        "assignment_quality_counts": dict(sorted(quality_counts.items())),
        "state_totals": state_totals,
        "state_totals_sha256": state_totals_sha256,
        "unassigned_district_coverage": {
            "affected_zcta_count": len(affected_zctas),
            "block_count": anomalies["unassigned_district"],
            "population": affected_population["unassigned_district"],
            "affected_zctas_sha256": checksum(affected_zctas),
        },
        "split_block": split_record,
    }
    block_artifact = {"path": str(ledger_path.relative_to(ROOT)).replace("\\", "/"), "row_count": totals["blocks"], "size_bytes": ledger_path.stat().st_size, "sha256": retrieval.sha256_file(ledger_path), "compression": "gzip_mtime_0"}
    return aggregates, integrity, block_artifact, {zcta: dict(values) for zcta, values in zcta_unassigned.items()}


def load_land_relationships() -> list[dict[str, Any]]:
    report = json.loads((ROOT / "docs/review_packets/zip_overlap_sensitivity_bounded_staging_design_v1.json").read_text(encoding="utf-8"))
    source = report["source"]["identity"]
    actual_baseline = {key: report["source"]["baseline"][key] for key in EXPECTED_LAND_BASELINE}
    if actual_baseline != EXPECTED_LAND_BASELINE:
        raise PopulationAnalysisError(f"PR #89 baseline changed: {actual_baseline}")
    if source["expected_file_name"] != EXPECTED_LAND_SOURCE["filename"] or source["actual_file_size_bytes"] != EXPECTED_LAND_SOURCE["size_bytes"] or source["actual_sha256"] != EXPECTED_LAND_SOURCE["sha256"]:
        raise PopulationAnalysisError("PR #89 official source identity changed")
    migration = land.validate_candidate_migration(land.CANDIDATE_MIGRATION.read_text(encoding="utf-8"))
    if migration["sha256"] != EXPECTED_0015_SHA256:
        raise PopulationAnalysisError("candidate migration 0015 checksum changed")
    path = ROOT / ".local/zip_overlap_sensitivity/zip-overlap-sensitivity-v1-57fad59f/normalized_relationship_evidence.jsonl"
    if not path.is_file():
        raise PopulationAnalysisError("pinned local PR #89 normalized relationship evidence is missing")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 39_967 or retrieval.sha256_file(path) != "b78117536e5383da0cef64b8a1e715c1b7ee51a4eb49f382e0abeda1d386f69a":
        raise PopulationAnalysisError("PR #89 normalized relationship evidence identity changed")
    return rows


def coverage_status(unassigned_block_count: int, unassigned_population: int) -> dict[str, bool]:
    if unassigned_population:
        raise PopulationAnalysisError("population-bearing unassigned-district block prevents exact population coverage")
    return {
        "population_coverage_exact": True,
        "block_assignment_complete": unassigned_block_count == 0,
    }


def combine_relationships(
    land_rows: list[dict[str, Any]],
    aggregates: dict[tuple[str, str, str], dict[str, Any]],
    zcta_unassigned: dict[str, dict[str, int]] | None = None,
) -> list[dict[str, Any]]:
    zcta_unassigned = zcta_unassigned or {}
    zcta_pop = Counter()
    for (zcta, _, _), row in aggregates.items():
        zcta_pop[zcta] += row["relationship_population"]
    result = []
    accepted_keys = {(r["zcta"], r["canonical_source_state"], r["source_district"]) for r in land_rows}
    unexpected = set(aggregates) - accepted_keys
    if unexpected:
        raise PopulationAnalysisError(f"population assignments fall outside accepted PR #89 relationships: {sorted(unexpected)[:10]}")
    for land_row in land_rows:
        key = (land_row["zcta"], land_row["canonical_source_state"], land_row["source_district"])
        pop = aggregates.get(key)
        population = int(pop["relationship_population"]) if pop else 0
        denominator = int(zcta_pop[land_row["zcta"]])
        excluded = zcta_unassigned.get(land_row["zcta"], {})
        excluded_blocks = int(excluded.get("block_count", 0))
        excluded_population = int(excluded.get("population", 0))
        coverage = coverage_status(excluded_blocks, excluded_population)
        row = {
            "zcta": land_row["zcta"], "canonical_state": land_row["canonical_source_state"],
            "source_district": land_row["source_district"],
            "source_relationship_identity": f"{land_row['source_artifact_sha256']}:{land_row['source_line_number']}",
            "relationship_population": population, "zcta_population": denominator,
            "population_share_numerator": population, "population_share_denominator": denominator,
            "contributing_common_blocks": int(pop["contributing_blocks"]) if pop else 0,
            "contributing_populated_blocks": int(pop["populated_contributing_blocks"]) if pop else 0,
            "contributing_zero_population_blocks": int(pop["zero_population_contributing_blocks"]) if pop else 0,
            "relationship_excluded_block_count": 0,
            "relationship_excluded_population": 0,
            "zcta_unassigned_district_block_count": excluded_blocks,
            "zcta_unassigned_district_population": excluded_population,
            **coverage,
            "assignment_quality": pop["assignment_quality"] if pop else "no_common_block_relationship",
            "land_share_numerator": int(land_row["arealand_part"]),
            "land_share_denominator": int(land_row["arealand_zcta5_20"]),
            "water_only_overlap": bool(land_row["water_only_overlap"]),
            "source_line_number": int(land_row["source_line_number"]),
            "production_auto_select_eligible": False,
        }
        result.append(row)
    by_zcta: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in result:
        by_zcta[row["zcta"]].append(row)
    final = []
    for zcta in sorted(by_zcta):
        pop_ranked = rank_population_rows(by_zcta[zcta])
        land_ranked = sorted(by_zcta[zcta], key=lambda r: (-Fraction(r["land_share_numerator"], r["land_share_denominator"]), r["canonical_state"], r["source_district"], r["source_relationship_identity"]))
        land_ranks = {r["source_relationship_identity"]: i for i, r in enumerate(land_ranked, 1)}
        for row in pop_ranked:
            row["land_rank"] = land_ranks[row["source_relationship_identity"]]
            row["population_minus_land_rank_difference"] = None if row["population_rank"] is None else row["population_rank"] - row["land_rank"]
            if row["zcta_population"] and row["land_share_denominator"]:
                difference = Fraction(row["relationship_population"], row["zcta_population"]) - Fraction(row["land_share_numerator"], row["land_share_denominator"])
                row["population_share_minus_land_share"] = {"numerator": difference.numerator, "denominator": difference.denominator}
            else:
                row["population_share_minus_land_share"] = None
            final.append(row)
    return final


def classify_policy(rows: list[dict[str, Any]], policy_id: str, threshold: Fraction | None) -> dict[str, Any]:
    by_zcta: dict[str, list[dict[str, Any]]] = defaultdict(list)
    removed_zero = 0
    retained = []
    for row in rows:
        keep = True if threshold is None else exact_threshold(row["relationship_population"], row["zcta_population"], threshold, positive=policy_id == "p1_positive")
        if keep:
            retained.append(row); by_zcta[row["zcta"]].append(row)
        elif row["relationship_population"] == 0:
            removed_zero += 1
    all_zctas = {row["zcta"] for row in rows}
    ambiguous = [items for items in by_zcta.values() if len(items) > 1]
    single = [items[0] for items in by_zcta.values() if len(items) == 1]
    return {
        "policy_id": policy_id,
        "threshold": None if threshold is None else {"numerator": threshold.numerator, "denominator": threshold.denominator},
        "retained_relationships": len(retained), "removed_zero_population_relationships": removed_zero,
        "retained_zctas": len(by_zcta), "no_survivor_zctas": len(all_zctas - set(by_zcta)),
        "exactly_one_district_zctas": sum(len(items) == 1 for items in by_zcta.values()),
        "same_state_multi_district_zctas": sum(len(items) > 1 and len({x['canonical_state'] for x in items}) == 1 for items in by_zcta.values()),
        "multi_state_zctas": sum(len({x['canonical_state'] for x in items}) > 1 for items in by_zcta.values()),
        "total_ambiguous_zctas": len(ambiguous), "production_auto_select_eligible": 0,
        "strict_single_mapping_supported_current_seat_zctas": sum(x.get("current_seat_classification") in {"filled_current_voting_seat", "filled_current_delegate", "current_resident_commissioner"} for x in single),
        "ambiguous_zctas_with_complete_current_seat_evidence": sum(all(x.get("current_seat_classification") in {"filled_current_voting_seat", "filled_current_delegate", "current_resident_commissioner"} for x in items) for items in ambiguous),
        "single_mapping_vacancy_zctas": sum(x.get("current_seat_classification") == "officially_vacant" for x in single),
        "single_mapping_dc_candidate_zctas": sum(x.get("current_seat_classification") == "candidate_dc_normalization" for x in single),
        "unmatched_or_unsupported_zctas": sum(any(x.get("current_seat_classification") in {"no_seeded_seat_match", "source_conflict", "unsupported_territory"} for x in items) for items in by_zcta.values()),
    }


def compare_land_population(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_zcta: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows: by_zcta[row["zcta"]].append(row)
    counts = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    margins: list[Fraction] = []
    absolute_differences: list[Fraction] = []
    concentration = Counter()
    meaningful = Counter()
    case_studies: dict[str, Any] = {}
    counts["all_accepted_zctas"] = len(by_zcta)
    for zcta, items in sorted(by_zcta.items()):
        counts["positive_land_zero_population"] += sum(x["land_share_numerator"] > 0 and x["relationship_population"] == 0 for x in items)
        counts["water_only_nonzero_population"] += sum(x["water_only_overlap"] and x["relationship_population"] > 0 for x in items)
        concentration[str(len(items))] += 1
        if not items[0]["zcta_population"]:
            counts["zero_population_zctas_excluded_from_ranking"] += 1
            counts["undefined_zero_population_cases"] += 1
            continue
        counts["positive_population_zctas"] += 1
        counts["positive_population_ambiguous_zctas"] += len(items) > 1
        pop = sorted(items, key=population_rank_key)
        land_order = sorted(items, key=lambda r: (-Fraction(r["land_share_numerator"], r["land_share_denominator"]), r["canonical_state"], r["source_district"], r["source_relationship_identity"]))
        top_pop_tied = len(pop) > 1 and pop[0]["relationship_population"] * pop[1]["zcta_population"] == pop[1]["relationship_population"] * pop[0]["zcta_population"]
        top_land_tied = len(land_order) > 1 and land_order[0]["land_share_numerator"] * land_order[1]["land_share_denominator"] == land_order[1]["land_share_numerator"] * land_order[0]["land_share_denominator"]
        counts["tied_population_winner"] += top_pop_tied
        counts["tied_land_winner"] += top_land_tied
        counts["positive_population_tied_top"] += top_pop_tied
        pop_pair = (pop[0]["canonical_state"], pop[0]["source_district"])
        land_pair = (land_order[0]["canonical_state"], land_order[0]["source_district"])
        if top_pop_tied:
            counts["positive_population_nonunique_top"] += 1
        elif pop_pair == land_pair:
            counts["positive_population_unique_top_agreement"] += 1
            counts["positive_population_ambiguous_unique_top_agreement"] += len(items) > 1
        else:
            counts["positive_population_unique_top_disagreement"] += 1
            counts["positive_population_ambiguous_unique_top_disagreement"] += len(items) > 1
            if len(examples["top_disagrees"]) < 10: examples["top_disagrees"].append({"zcta": zcta, "population_top": "-".join(pop_pair), "land_top": "-".join(land_pair)})
            case_studies.setdefault("top_population_differs_from_top_land", examples["top_disagrees"][-1])
        pop_majority = majority_status(pop[0]["relationship_population"], pop[0]["zcta_population"])
        land_majority = majority_status(land_order[0]["land_share_numerator"], land_order[0]["land_share_denominator"])
        counts["strict_population_majority_land_not"] += pop_majority["strict_majority"] and not land_majority["strict_majority"]
        counts["strict_land_majority_population_not"] += land_majority["strict_majority"] and not pop_majority["strict_majority"]
        counts["exactly_half_population"] += pop_majority["exactly_half"]
        counts["exactly_half_land"] += land_majority["exactly_half"]
        counts["no_strict_population_majority"] += pop_majority["no_strict_majority"]
        counts["no_strict_land_majority"] += land_majority["no_strict_majority"]
        for item in items:
            if item["zcta_population"] and item["land_share_denominator"]:
                pop_share = Fraction(item["relationship_population"], item["zcta_population"])
                land_share = Fraction(item["land_share_numerator"], item["land_share_denominator"])
                absolute_differences.append(abs(pop_share - land_share))
                if 0 < land_share <= Fraction(1, 10_000):
                    meaningful["gte_1_person"] += item["relationship_population"] >= 1
                    meaningful["gte_10_people"] += item["relationship_population"] >= 10
                    meaningful["gte_100_people"] += item["relationship_population"] >= 100
                    meaningful["gte_1_percent"] += pop_share >= Fraction(1, 100)
                    meaningful["gte_5_percent"] += pop_share >= Fraction(5, 100)
                    meaningful["gte_10_percent"] += pop_share >= Fraction(10, 100)
                    if item["relationship_population"] >= 10 or pop_share >= Fraction(1, 100):
                        case_studies.setdefault("tiny_land_sliver_meaningful_population", {"zcta": zcta, "mapping": f"{item['canonical_state']}-{item['source_district']}", "population": item["relationship_population"], "zcta_population": item["zcta_population"], "land_share": {"numerator": land_share.numerator, "denominator": land_share.denominator}})
                if land_share >= Fraction(1, 4) and (item["relationship_population"] == 0 or pop_share <= Fraction(1, 1000)):
                    case_studies.setdefault("large_land_share_zero_or_negligible_population", {"zcta": zcta, "mapping": f"{item['canonical_state']}-{item['source_district']}", "population": item["relationship_population"], "zcta_population": item["zcta_population"], "land_share": {"numerator": land_share.numerator, "denominator": land_share.denominator}})
                if item["relationship_population"] == 0:
                    case_studies.setdefault("zero_population_relationship_removed_by_p1", {"zcta": zcta, "mapping": f"{item['canonical_state']}-{item['source_district']}", "water_only": item["water_only_overlap"], "land_part": item["land_share_numerator"]})
        if len(pop) > 1 and pop[0]["zcta_population"]:
            margin = Fraction(pop[0]["relationship_population"] - pop[1]["relationship_population"], pop[0]["zcta_population"])
            margins.append(margin)
            top_share = Fraction(pop[0]["relationship_population"], pop[0]["zcta_population"])
            top_land_share = Fraction(land_order[0]["land_share_numerator"], land_order[0]["land_share_denominator"])
            if top_share >= Fraction(3, 4) and top_land_share < Fraction(3, 4):
                case_studies.setdefault("population_weighting_resolves_land_ambiguity", {"zcta": zcta, "population_top": "-".join(pop_pair), "population_share": {"numerator": top_share.numerator, "denominator": top_share.denominator}, "land_top": "-".join(land_pair), "land_top_share": {"numerator": top_land_share.numerator, "denominator": top_land_share.denominator}})
            if top_share < Fraction(3, 5):
                case_studies.setdefault("population_ambiguity_remains_severe", {"zcta": zcta, "top_mapping": "-".join(pop_pair), "top_share": {"numerator": top_share.numerator, "denominator": top_share.denominator}, "margin": {"numerator": margin.numerator, "denominator": margin.denominator}})
            if top_share <= Fraction(1, 2):
                case_studies.setdefault("no_population_majority", {"zcta": zcta, "top_mapping": "-".join(pop_pair), "top_share": {"numerator": top_share.numerator, "denominator": top_share.denominator}})
            if margin <= Fraction(1, 100):
                case_studies.setdefault("nearly_tied_population_shares", {"zcta": zcta, "top_mapping": "-".join(pop_pair), "second_mapping": f"{pop[1]['canonical_state']}-{pop[1]['source_district']}", "margin": {"numerator": margin.numerator, "denominator": margin.denominator}})
        if len({x["canonical_state"] for x in items}) > 1:
            case_studies.setdefault("multi_state_zcta", {"zcta": zcta, "mappings": [f"{x['canonical_state']}-{x['source_district']}" for x in pop]})
        if any(x.get("current_seat_classification") == "officially_vacant" for x in items):
            case_studies.setdefault("currently_vacant_district", {"zcta": zcta, "mappings": [f"{x['canonical_state']}-{x['source_district']}" for x in pop], "classifications": [x.get("current_seat_classification") for x in pop]})
        if any(x.get("current_seat_classification") == "candidate_dc_normalization" for x in items):
            case_studies.setdefault("dc_98_candidate_normalization", {"zcta": zcta, "source_mapping": "DC-98", "runtime_approved": False})
    if counts["water_only_nonzero_population"]:
        raise PopulationAnalysisError("water-only relationship has nonzero assigned population")
    dominance = {}
    margin_results = {}
    all_ambiguous_groups = [items for items in by_zcta.values() if len(items) > 1]
    ambiguous_groups = [items for items in all_ambiguous_groups if items[0]["zcta_population"] > 0]
    for threshold in DOMINANCE_THRESHOLDS:
        qualifying = [sorted(group, key=population_rank_key) for group in ambiguous_groups]
        qualifying = [items for items in qualifying if items[0]["zcta_population"] and exact_threshold(items[0]["relationship_population"], items[0]["zcta_population"], threshold)]
        dominance[f"gte_{threshold.numerator * 100 // threshold.denominator}_percent"] = {
            "qualifying_zctas": len(qualifying), "qualifying_formerly_ambiguous_zctas": len(qualifying),
            "nonqualifying_ambiguous_zctas": len(ambiguous_groups) - len(qualifying),
            "ties": sum(len(items) > 1 and items[0]["relationship_population"] * items[1]["zcta_population"] == items[1]["relationship_population"] * items[0]["zcta_population"] for items in qualifying),
            "vacancies": sum(any(x.get("current_seat_classification") == "officially_vacant" for x in items) for items in qualifying),
            "dc_candidate_normalization_cases": sum(any(x.get("current_seat_classification") == "candidate_dc_normalization" for x in items) for items in qualifying),
            "mappings_without_exact_population_coverage": sum(not item["population_coverage_exact"] for items in qualifying for item in items),
            "mappings_without_complete_block_assignment": sum(not item["block_assignment_complete"] for items in qualifying for item in items),
            "top_district_changed_from_land": sum((items[0]["canonical_state"], items[0]["source_district"]) != (sorted(items, key=lambda r: (-Fraction(r["land_share_numerator"], r["land_share_denominator"]), r["canonical_state"], r["source_district"]))[0]["canonical_state"], sorted(items, key=lambda r: (-Fraction(r["land_share_numerator"], r["land_share_denominator"]), r["canonical_state"], r["source_district"]))[0]["source_district"]) for items in qualifying),
        }
        dominance[f"gte_{threshold.numerator * 100 // threshold.denominator}_percent"]["top_district_agrees_with_land"] = len(qualifying) - dominance[f"gte_{threshold.numerator * 100 // threshold.denominator}_percent"]["top_district_changed_from_land"]
    for threshold in MARGIN_THRESHOLDS:
        qualifying_count = sum(value >= threshold for value in margins)
        margin_results[f"gte_{threshold.numerator * 100 // threshold.denominator}_points"] = {"qualifying_ambiguous_zctas": qualifying_count, "nonqualifying_positive_population_ambiguous_zctas": len(ambiguous_groups) - qualifying_count, "undefined_zero_population_zctas": len(all_ambiguous_groups) - len(ambiguous_groups)}
    difference_distribution = {f"gte_{points}_points": sum(value >= Fraction(points, 100) for value in absolute_differences) for points in (1, 5, 10, 20, 25, 50)}
    return {"counts": dict(sorted(counts.items())), "all_ambiguous_zctas": len(all_ambiguous_groups), "positive_population_ambiguous_zctas": len(ambiguous_groups), "dominance": dominance, "margins": margin_results, "meaningful_population_for_land_slivers_lte_0_01_percent": dict(sorted(meaningful.items())), "absolute_population_vs_land_share_difference": difference_distribution, "population_concentration_by_relationship_count": dict(sorted(concentration.items(), key=lambda x: int(x[0]))), "bounded_examples": dict(examples), "case_studies": case_studies}


def validate_national_invariants(integrity: dict[str, Any]) -> None:
    actual = {
        "block_count": integrity["block_count"],
        "source_population": integrity["source_population"],
        "population_bearing_blocks": integrity["population_bearing_blocks"],
        "zero_population_blocks": integrity["zero_population_blocks"],
        "assigned_zcta_population": integrity["assigned_zcta_population"],
        "outside_zcta_population": integrity["source_population"] - integrity["assigned_zcta_population"],
        "unassigned_district_blocks": integrity["anomaly_counts"].get("unassigned_district", 0),
        "unassigned_district_population": integrity["affected_population"].get("unassigned_district", 0),
    }
    if actual != EXPECTED_NATIONAL_INVARIANTS:
        raise PopulationAnalysisError(f"approved national parser invariants differ: {actual}")
    if integrity["state_totals_sha256"] != EXPECTED_STATE_TOTALS_SHA256:
        raise PopulationAnalysisError(
            f"approved state totals checksum differs: expected {EXPECTED_STATE_TOTALS_SHA256}, got {integrity['state_totals_sha256']}"
        )


def population_reconciliation(rows: list[dict[str, Any]], integrity: dict[str, Any]) -> dict[str, Any]:
    zcta_totals: dict[str, int] = {}
    district_totals = Counter()
    relationship_total = 0
    for row in rows:
        existing = zcta_totals.setdefault(row["zcta"], row["zcta_population"])
        if existing != row["zcta_population"]:
            raise PopulationAnalysisError(f"conflicting ZCTA population denominator: {row['zcta']}")
        relationship_total += row["relationship_population"]
        district_totals[f"{row['canonical_state']}-{row['source_district']}"] += row["relationship_population"]
    zcta_population_total = sum(zcta_totals.values())
    if relationship_total != integrity["assigned_zcta_population"] or zcta_population_total != relationship_total:
        raise PopulationAnalysisError("aggregate population does not reconcile to normalized blocks")
    district_rows = [{"mapping": key, "population": value} for key, value in sorted(district_totals.items())]
    zcta_rows = [{"zcta": key, "population": value} for key, value in sorted(zcta_totals.items())]
    no_common = [
        {"zcta": row["zcta"], "state": row["canonical_state"], "district": row["source_district"], "identity": row["source_relationship_identity"]}
        for row in rows if row["contributing_common_blocks"] == 0
    ]
    incomplete_zctas = sorted({row["zcta"] for row in rows if not row["block_assignment_complete"]})
    zcta_excluded_blocks = {
        zcta: next(row["zcta_unassigned_district_block_count"] for row in rows if row["zcta"] == zcta)
        for zcta in incomplete_zctas
    }
    if sum(zcta_excluded_blocks.values()) != integrity["unassigned_district_coverage"]["block_count"]:
        raise PopulationAnalysisError("per-ZCTA unassigned-district block counts do not reconcile nationally")
    return {
        "source_population": integrity["source_population"], "assigned_zcta_population": integrity["assigned_zcta_population"],
        "unassigned_zcta_population": integrity["source_population"] - integrity["assigned_zcta_population"],
        "relationship_population_sum": relationship_total, "zcta_population_sum": zcta_population_total,
        "district_count": len(district_rows), "district_totals_sha256": checksum(district_rows),
        "zcta_count": len(zcta_rows), "zcta_totals_sha256": checksum(zcta_rows),
        "zero_population_zctas": sum(value == 0 for value in zcta_totals.values()),
        "zero_population_relationships": sum(row["relationship_population"] == 0 for row in rows),
        "relationships_with_common_blocks": sum(row["contributing_common_blocks"] > 0 for row in rows),
        "relationships_with_zero_common_blocks": len(no_common),
        "zero_common_block_relationships_sha256": checksum(no_common),
        "relationships_with_exact_population_coverage": sum(row["population_coverage_exact"] for row in rows),
        "relationships_without_exact_population_coverage": sum(not row["population_coverage_exact"] for row in rows),
        "relationships_without_complete_block_assignment": sum(not row["block_assignment_complete"] for row in rows),
        "zctas_without_complete_block_assignment": len(incomplete_zctas),
        "zctas_without_complete_block_assignment_sha256": checksum(incomplete_zctas),
        "per_zcta_unassigned_district_block_count": zcta_excluded_blocks,
        "full_relationship_population_checksum": checksum([{"zcta": r["zcta"], "state": r["canonical_state"], "district": r["source_district"], "population": r["relationship_population"], "denominator": r["zcta_population"]} for r in rows]),
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows: handle.write(canonical_json(row) + "\n")
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "row_count": len(rows), "size_bytes": path.stat().st_size, "sha256": retrieval.sha256_file(path)}


def markdown(report: dict[str, Any]) -> str:
    policies = report["population_policies"]
    comparison = report["population_vs_land"]
    counts = comparison["counts"]
    reconciliation = report["population_reconciliation"]
    integrity = report["block_integrity"]
    lines = [
        "# ZIP Population-Weighted Ambiguity Evaluation V1", "",
        "> Read-only Census-only analysis. Population-ranked ZCTA mappings are not address-resolved representation.", "",
        "## Result", "",
        "Official Census sources support an exact common-2020-block population allocation to the Census Bureau's whole-block CD119 tabulation plan. Population weighting changes presentation ordering in a bounded minority of ZCTAs and sharply distinguishes zero/low-population relationships, but it does not justify representative auto-selection.", "",
        "## Official sources", "",
        f"The committed manifest pins all 51 PL 94-171 state/DC artifacts individually. Batch: `{report['source_manifest']['batch_id']}`; completion: `{report['source_manifest']['batch_completed_at']}`; manifest SHA-256: `{report['source_manifest']['manifest_sha256']}`.",
        f"Provenance modes: `{canonical_json(report['source_manifest']['retrieval_mode_counts'])}`. Local resume timestamps describe validation, not retrieval.", "",
    ]
    for item in report["source_manifest"]["artifacts"]:
        if item["role"] != "block_population":
            lines.append(f"- `{item['filename']}` — {item['size_bytes']:,} bytes — SHA-256 `{item['sha256']}` — {item['url']}")
    lines.extend(["", "## Compatibility and method", "",
        f"- Method: `{report['compatibility']['method']}`; compatible: `{report['compatibility']['compatible']}`.",
        "- Population, ZCTA assignment, and congressional assignment share the 15-digit 2020 Census tabulation-block GEOID.",
        "- Population is 2020 Census P1 total resident population from PL 94-171 summary-level 750 records.",
        "- District assignment is the CD119 whole-block tabulation plan for the 2024 election cycle; no spatial apportionment was used.",
        f"- Colorado split block `{integrity['split_block']['block_geoid']}` has `{integrity['split_block']['population']}` people and an authoritative whole-block assignment to CD{integrity['split_block']['district']}.", "",
        "## Coverage and reconciliation", "",
        f"- Blocks: `{integrity['block_count']:,}` (`{integrity['population_bearing_blocks']:,}` populated; `{integrity['zero_population_blocks']:,}` zero-population).",
        f"- 50-state/DC source population: `{reconciliation['source_population']:,}`.",
        f"- Population assigned to ZCTAs and reconciled through relationship/ZCTA aggregates: `{reconciliation['assigned_zcta_population']:,}`.",
        f"- Official blocks without a ZCTA contain `{reconciliation['unassigned_zcta_population']:,}` people across `{integrity['anomaly_counts']['unassigned_zcta']:,}` blocks.",
        f"- Unassigned-district blocks: `{integrity['anomaly_counts']['unassigned_district']:,}`; affected population: `{integrity['affected_population']['unassigned_district']:,}`.",
        f"- Unassigned-district blocks affect `{integrity['unassigned_district_coverage']['affected_zcta_count']:,}` ZCTAs; affected-ZCTA checksum: `{integrity['unassigned_district_coverage']['affected_zctas_sha256']}`. Their zero population preserves exact population coverage, but block assignment is incomplete.",
        f"- Aggregate rows: `{report['zcta_district_population_row_count']:,}`; ZCTAs: `{reconciliation['zcta_count']:,}`; district pairs: `{reconciliation['district_count']:,}`.",
        f"- Relationships with common blocks: `{reconciliation['relationships_with_common_blocks']:,}`; with zero common blocks: `{reconciliation['relationships_with_zero_common_blocks']:,}` (checksum `{reconciliation['zero_common_block_relationships_sha256']}`).",
        f"- Exact-population-coverage relationships: `{reconciliation['relationships_with_exact_population_coverage']:,}`; relationships/ZCTAs with incomplete block assignment: `{reconciliation['relationships_without_complete_block_assignment']:,}` / `{reconciliation['zctas_without_complete_block_assignment']:,}`.",
        f"- Zero-population ZCTAs: `{reconciliation['zero_population_zctas']:,}`; zero-population relationships: `{reconciliation['zero_population_relationships']:,}`.",
        f"- ZCTA totals checksum: `{reconciliation['zcta_totals_sha256']}`; district totals checksum: `{reconciliation['district_totals_sha256']}`; state parser totals checksum: `{integrity['state_totals_sha256']}`.", "",
        "## Population policy grid", "",
        "| Policy | Relationships | ZCTAs | Ambiguous | Single | No survivor | Auto-select |", "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in policies:
        lines.append(f"| {row['policy_id']} | {row['retained_relationships']:,} | {row['retained_zctas']:,} | {row['total_ambiguous_zctas']:,} | {row['exactly_one_district_zctas']:,} | {row['no_survivor_zctas']:,} | 0 |")
    tiny = comparison["meaningful_population_for_land_slivers_lte_0_01_percent"]
    lines.extend(["", "## Population versus land", "",
        f"- Accepted ZCTAs: `{counts['all_accepted_zctas']:,}`; positive-population: `{counts['positive_population_zctas']:,}`; zero-population excluded from ranking: `{counts['zero_population_zctas_excluded_from_ranking']:,}`.",
        f"- Positive-population unique top agrees for `{counts['positive_population_unique_top_agreement']:,}` ZCTAs and differs for `{counts['positive_population_unique_top_disagreement']:,}`; tied population tops: `{counts['positive_population_tied_top']:,}`.",
        f"- Positive-population ambiguous ZCTAs: `{counts['positive_population_ambiguous_zctas']:,}`; unique-top agreement/disagreement within them: `{counts['positive_population_ambiguous_unique_top_agreement']:,}` / `{counts['positive_population_ambiguous_unique_top_disagreement']:,}`.",
        f"- Strict population majority exists while strict land majority does not: `{counts['strict_population_majority_land_not']:,}`; strict land majority exists while strict population majority does not: `{counts['strict_land_majority_population_not']:,}`.",
        f"- Exact-half population/land cases: `{counts['exactly_half_population']:,}` / `{counts['exactly_half_land']:,}`. The separate `>=50%` sensitivity row remains inclusive.",
        f"- Positive-land relationships with zero population: `{counts['positive_land_zero_population']:,}`; water-only relationships with nonzero population: `{counts['water_only_nonzero_population']:,}`.",
        f"- Tiny positive-land relationships at or below 0.01% include `{tiny.get('gte_1_person', 0):,}` with at least one person and `{tiny.get('gte_10_people', 0):,}` with at least ten people.", "",
        "## Dominance and margins", "",
        "| Top population share | Qualifying ambiguous ZCTAs | Nonqualifying | Land top differs |", "|---|---:|---:|---:|",
    ])
    for label, item in comparison["dominance"].items():
        lines.append(f"| {label} | {item['qualifying_zctas']:,} | {item['nonqualifying_ambiguous_zctas']:,} | {item['top_district_changed_from_land']:,} |")
    lines.extend(["", "| Top-minus-second margin | Qualifying ambiguous ZCTAs | Nonqualifying | Zero-population undefined |", "|---|---:|---:|---:|"])
    for label, item in comparison["margins"].items():
        lines.append(f"| {label} | {item['qualifying_ambiguous_zctas']:,} | {item['nonqualifying_positive_population_ambiguous_zctas']:,} | {item['undefined_zero_population_zctas']:,} |")
    lines.extend(["", "## Deterministic case studies", ""])
    for label, value in comparison["case_studies"].items():
        lines.append(f"- `{label}`: `{canonical_json(value)}`")
    seat = report["current_seat_reconciliation"]
    pre = report["production_precheck"]
    lines.extend(["", "## Current-seat reconciliation", "",
        f"- Unique pair classes: `{canonical_json(seat['unique_source_pair_classifications'])}`.",
        f"- Relationship row classes: `{canonical_json(seat['relationship_row_classifications'])}`.",
        f"- Vacancies: `{', '.join(seat['vacant_source_pairs'])}`.",
        "- DC-98 remains candidate normalization to seeded DC-00 only; runtime approval is false.", "",
        "## Product boundary", "",
        "Population share may preserve and order possible districts and support versioned low/zero-population labels. The measurement is from 2020, current residents may differ, and minority-district addresses remain valid. Population concentration cannot identify a user's district or authorize representative auto-selection. A validated full-address resolver remains necessary.", "",
        "## Staging decision", "",
        "No `0016` migration is proposed. The aggregate-evidence model is preferred over a production block ledger, but production storage should wait for independent review and a separate implementation milestone. Migration `0015` remains unchanged, SHA-pinned, and unapplied.", "",
        "## Production safety", "",
        f"- House snapshot: `{pre['snapshot_id']}`; legislators fingerprint: `{pre['legislators_fingerprint']['sha256']}` across `{pre['legislators_fingerprint']['row_count']}` rows.",
        f"- House domain counts: `{canonical_json(pre['house_snapshot_domain_counts'])}`.",
        f"- `zip_district_mappings` rows: `{pre['zip_district_mappings_row_count']}` before and `{report['production_postcheck']['zip_district_mappings_row_count']}` after.",
        f"- Routes use `zip_district_map` and do not read `zip_district_mappings`: `{not pre['route_state']['either_public_endpoint_reads_zip_district_mappings']}`; feature flag: `{pre['feature_flag']['status']}`.",
        "- Session and transaction read-only modes were confirmed with a bounded 30-second statement timeout. Canonical House checksums and the legislators fingerprint matched before/after. No production/runtime mutation occurred. Production auto-select eligibility remains zero.",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=retrieval.DEFAULT_MANIFEST)
    parser.add_argument("--batch-root", type=Path)
    parser.add_argument("--env-path", type=Path, default=ROOT / "backend/.env")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/review_packets/zip_population_weighted_ambiguity_evaluation_v1.json")
    parser.add_argument("--markdown-output", type=Path, default=ROOT / "docs/review_packets/zip_population_weighted_ambiguity_evaluation_v1.md")
    parser.add_argument("--read-only", action="store_true", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_sha256 = verify_approved_source_manifest(args.manifest)
    replay = retrieval.replay_manifest(args.manifest, args.batch_root)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = args.batch_root or retrieval.LOCAL_ROOT / manifest["batch_id"]
    raw, derived = root / "raw", root / "derived"
    precheck, seats = land.inspect_production_read_only(args.env_path)
    land_rows = load_land_relationships()
    cd_split = split_cd119(raw / "cd119.zip", derived)
    zcta_split = split_zcta_blocks(raw / "tab20_zcta520_tabblock20_natl.txt", derived)
    aggregates, integrity, block_artifact, zcta_unassigned = join_common_blocks(raw, derived, manifest["batch_id"])
    validate_national_invariants(integrity)
    rows = combine_relationships(land_rows, aggregates, zcta_unassigned)
    seat_input = [dict(row, canonical_source_state=row["canonical_state"]) for row in rows]
    seat_reconciliation, seat_map = land.reconcile_seats(seat_input, seats)
    for row in rows:
        row["current_seat_classification"] = land.seat_classification(dict(row, canonical_source_state=row["canonical_state"]), seat_map)
    policies = [classify_policy(rows, policy_id, threshold) for policy_id, threshold in POPULATION_THRESHOLDS]
    comparison = compare_land_population(rows)
    comparison["case_studies"]["populated_block_unsafe_under_spatial_apportionment"] = integrity["split_block"]
    reconciliation = population_reconciliation(rows, integrity)
    relationship_artifact = write_jsonl(derived / "zcta_district_population_evidence.jsonl", rows)
    postcheck, post_seats = land.inspect_production_read_only(args.env_path)
    if seats != post_seats or precheck["canonical_database_checksums"] != postcheck["canonical_database_checksums"] or precheck["legislators_fingerprint"] != postcheck["legislators_fingerprint"] or precheck["zip_district_mappings_row_count"] != postcheck["zip_district_mappings_row_count"]:
        raise PopulationAnalysisError("production read-only pre/post state differs")
    report = {
        "schema_version": SCHEMA_VERSION, "parser_version": PARSER_VERSION,
        "analysis_id": f"zip-population-weighting-v1-{manifest_sha256[:12]}",
        "source_manifest": {
            "batch_id": manifest["batch_id"],
            "batch_completed_at": manifest["batch_completed_at"],
            "replay": replay,
            "manifest_sha256": manifest_sha256,
            "retrieval_mode_counts": dict(sorted(Counter(item["retrieval_mode"] for item in manifest["artifacts"]).items())),
            "artifacts": manifest["artifacts"],
        },
        "compatibility": {"compatible": True, "method": "method_a_exact_common_block_assignment", "population_vintage": "2020 Census", "zcta_vintage": "2020", "block_vintage": "2020 Census tabulation block", "district_vintage": "119th Congress whole-block tabulation plan for 2024 election cycle", "spatial_apportionment_used": False},
        "source_split_results": {"cd119": cd_split, "zcta": zcta_split},
        "block_integrity": integrity,
        "population_reconciliation": reconciliation,
        "zcta_district_population_row_count": len(rows),
        "population_policies": policies,
        "population_vs_land": comparison,
        "current_seat_reconciliation": seat_reconciliation,
        "local_artifacts": [block_artifact, relationship_artifact],
        "candidate_migration": {"0015_sha256": EXPECTED_0015_SHA256, "0015_modified": False, "0015_applied": False, "0016_created": False, "decision": "defer_schema_until_independent_review; prefer aggregate evidence over full block ledger"},
        "product_use": {"preserve_possible_mappings": True, "population_rank_for_positive_population_presentation": True, "zero_population_rank_status": "undefined_zero_population_zcta", "hide_zero_population_by_default": "potentially_after_product_decision", "automatic_representative_selection": False, "production_auto_select_eligible_count": 0, "full_address_lookup": "still required for address-resolved representative selection"},
        "production_precheck": precheck, "production_postcheck": postcheck,
        "safety": {"production_write_performed": False, "runtime_mutation_performed": False, "migration_applied": False, "production_auto_select_eligible_count": 0},
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "relationships": len(rows), "population": integrity["source_population"], "positive_population_unique_top_disagreements": comparison["counts"].get("positive_population_unique_top_disagreement", 0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
