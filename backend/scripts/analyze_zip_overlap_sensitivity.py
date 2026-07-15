"""Read-only ZIP/ZCTA overlap sensitivity analysis for the pinned Census file."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.scripts import apply_current_house_member_metadata_snapshot as house
from backend.scripts import dry_run_zip_source_import as source_import
from backend.scripts.evaluate_zip_source_member_readiness import (
    ensure_repository_state_safe,
    inspect_repository_state,
)

SCHEMA_VERSION = "zip_overlap_sensitivity_bounded_staging_design_v1"
PARSER_VERSION = "zip_overlap_area_parser_v1"
ANALYSIS_ID = "zip-overlap-sensitivity-v1-57fad59f"
SNAPSHOT_ID = "house-119-20260713T011722Z"
EXPECTED_BASELINE = {
    "raw_rows": 40_397,
    "accepted_rows": 39_967,
    "rejected_rows": 430,
    "unique_zctas": 33_642,
    "states_dc": 51,
    "source_state_district_pairs": 436,
    "same_state_multi_district_zctas": 5_725,
    "multi_state_zctas": 137,
}
EXPECTED_TERRITORY_REJECTIONS = {"AS": 2, "GU": 8, "MP": 4, "PR": 133, "VI": 7}
TERRITORY_FIPS = {"60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI"}
DEFAULT_JSON = ROOT / "docs/review_packets/zip_overlap_sensitivity_bounded_staging_design_v1.json"
DEFAULT_MD = ROOT / "docs/review_packets/zip_overlap_sensitivity_bounded_staging_design_v1.md"
LOCAL_ROOT = ROOT / ".local/zip_overlap_sensitivity" / ANALYSIS_ID
MANIFEST_PATH = ROOT / "docs/source_manifests/zip_overlap_sensitivity_v1.json"
CANDIDATE_MIGRATION = ROOT / "backend/migrations/0015_zip_mapping_source_evidence.sql"
EXPECTED_CANDIDATE_MIGRATION_SHA256 = "e2b8d526d7e0fac31a0368e04ffc11e59cabc8613ed0afb6a478276f46c636c3"
THRESHOLDS = (
    ("gt_0_percent", Fraction(0), False),
    ("gte_0_01_percent", Fraction(1, 10_000), True),
    ("gte_0_05_percent", Fraction(5, 10_000), True),
    ("gte_0_1_percent", Fraction(1, 1_000), True),
    ("gte_0_5_percent", Fraction(5, 1_000), True),
    ("gte_1_percent", Fraction(1, 100), True),
    ("gte_2_percent", Fraction(2, 100), True),
    ("gte_5_percent", Fraction(5, 100), True),
    ("gte_10_percent", Fraction(10, 100), True),
    ("gte_25_percent", Fraction(25, 100), True),
    ("gte_50_percent", Fraction(50, 100), True),
)
FORBIDDEN_SQL = re.compile(r"\b(insert|update|delete|copy|alter|drop|truncate|create)\b", re.I)


class AnalysisSafetyError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def deterministic_checksum(value: Any) -> str:
    return sha256_bytes((canonical_json(value) + "\n").encode("utf-8"))


def parse_nonnegative_integer(value: Any, field: str, line_number: int) -> int:
    text = "" if value is None else str(value).strip()
    if not re.fullmatch(r"\d+", text):
        raise AnalysisSafetyError(f"line {line_number}: {field} must be a nonnegative integer; got {text!r}")
    return int(text)


def fraction_record(value: Fraction | None) -> dict[str, Any] | None:
    if value is None:
        return None
    scaled = value * 100
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": decimal_text(value, 14),
        "percent_decimal": decimal_text(scaled, 12),
    }


def ratio_record(value: Fraction | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": decimal_text(value, 14),
    }


def decimal_text(value: Fraction, places: int) -> str:
    with localcontext() as context:
        context.prec = max(50, len(str(abs(value.numerator))) + len(str(value.denominator)) + places)
        rendered = format(Decimal(value.numerator) / Decimal(value.denominator), f".{places}f")
    return rendered.rstrip("0").rstrip(".") or "0"


def normalize_official_rows(input_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    identity = source_import.inspect_official_file_identity(input_path)
    if not identity["official_file_identity_verified"]:
        raise AnalysisSafetyError("only the exact pinned official source file is accepted")
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.DictReader(handle, delimiter="|"))
    normalized = []
    rejected = []
    territory_counts = Counter()
    for index, raw in enumerate(raw_rows, start=2):
        adapted = source_import.adapt_official_census_row(raw)
        parsed = source_import.normalize_row(adapted, line_number=index)
        fips = str(raw.get("GEOID_CD119_20", ""))[:2]
        if fips in TERRITORY_FIPS:
            territory_counts[TERRITORY_FIPS[fips]] += 1
        if parsed["rejected"]:
            rejected.append({
                "line_number": index,
                "source_congressional_geoid": raw.get("GEOID_CD119_20", ""),
                "zcta": raw.get("GEOID_ZCTA5_20", ""),
                "arealand_part": int(raw["AREALAND_PART"]) if str(raw.get("AREALAND_PART", "")).isdigit() else None,
                "areawater_part": int(raw["AREAWATER_PART"]) if str(raw.get("AREAWATER_PART", "")).isdigit() else None,
                "reasons": parsed["rejection_reasons"],
            })
            continue
        land_zcta = parse_nonnegative_integer(raw.get("AREALAND_ZCTA5_20"), "AREALAND_ZCTA5_20", index)
        water_zcta = parse_nonnegative_integer(raw.get("AREAWATER_ZCTA5_20"), "AREAWATER_ZCTA5_20", index)
        land_part = parse_nonnegative_integer(raw.get("AREALAND_PART"), "AREALAND_PART", index)
        water_part = parse_nonnegative_integer(raw.get("AREAWATER_PART"), "AREAWATER_PART", index)
        normalized.append({
            "source_line_number": index,
            "zcta": parsed["zip"],
            "source_congressional_geoid": raw["GEOID_CD119_20"],
            "canonical_source_state": parsed["state"],
            "source_district": parsed["district"],
            "arealand_zcta5_20": land_zcta,
            "areawater_zcta5_20": water_zcta,
            "arealand_part": land_part,
            "areawater_part": water_part,
            "positive_land_overlap": land_part > 0,
            "positive_water_overlap": water_part > 0,
            "positive_total_overlap": land_part + water_part > 0,
            "water_only_overlap": land_part == 0 and water_part > 0,
            "zero_area_relationship": land_part == 0 and water_part == 0,
            "land_share": Fraction(land_part, land_zcta) if land_zcta else None,
            "water_share": Fraction(water_part, water_zcta) if water_zcta else None,
            "total_share": Fraction(land_part + water_part, land_zcta + water_zcta) if land_zcta + water_zcta else None,
            "source_artifact_sha256": identity["actual_sha256"],
            "parser_version": PARSER_VERSION,
        })
    groups = group_rows(normalized)
    baseline = {
        "raw_rows": len(raw_rows),
        "accepted_rows": len(normalized),
        "rejected_rows": len(rejected),
        "unique_zctas": len(groups),
        "states_dc": len({r["canonical_source_state"] for r in normalized}),
        "source_state_district_pairs": len({pair(r) for r in normalized}),
        "same_state_multi_district_zctas": sum(classify(rows) == "same_state_multi_district" for rows in groups.values()),
        "multi_state_zctas": sum(classify(rows) == "multi_state" for rows in groups.values()),
    }
    if baseline != EXPECTED_BASELINE:
        raise AnalysisSafetyError(f"official parser baseline changed: expected {EXPECTED_BASELINE}, got {baseline}")
    if dict(sorted(territory_counts.items())) != EXPECTED_TERRITORY_REJECTIONS:
        raise AnalysisSafetyError(
            f"territory rejection counts changed: expected {EXPECTED_TERRITORY_REJECTIONS}, got {dict(territory_counts)}"
        )
    return normalized, rejected, {"identity": identity, "baseline": baseline, "territory_rejections": dict(territory_counts)}


def pair(row: dict[str, Any]) -> tuple[str, str]:
    return row["canonical_source_state"], row["source_district"]


def group_rows(rows: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[row["zcta"]].append(row)
    return dict(sorted(result.items()))


def classify(rows: list[dict[str, Any]]) -> str:
    pairs = {pair(r) for r in rows}
    states = {state for state, _ in pairs}
    if not pairs:
        return "no_surviving_relationship"
    if len(states) > 1:
        return "multi_state"
    if len(pairs) > 1:
        return "same_state_multi_district"
    return "exactly_one_district"


def validate_geographic_integrity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = group_rows(rows)
    anomalies: dict[str, list[Any]] = defaultdict(list)
    reconciliation = Counter()
    for zcta, items in groups.items():
        lands = {r["arealand_zcta5_20"] for r in items}
        waters = {r["areawater_zcta5_20"] for r in items}
        if len(lands) != 1:
            anomalies["inconsistent_land_denominator"].append(zcta)
        if len(waters) != 1:
            anomalies["inconsistent_water_denominator"].append(zcta)
        if len(lands) != 1 or len(waters) != 1:
            continue
        land, water = next(iter(lands)), next(iter(waters))
        land_diff = sum(r["arealand_part"] for r in items) - land
        water_diff = sum(r["areawater_part"] for r in items) - water
        total_diff = land_diff + water_diff
        for name, diff in (("land", land_diff), ("water", water_diff), ("total", total_diff)):
            reconciliation[f"{name}_exact"] += diff == 0
            reconciliation[f"{name}_over"] += diff > 0
            reconciliation[f"{name}_under"] += diff < 0
            if diff:
                anomalies[f"{name}_{'over' if diff > 0 else 'under'}_allocation"].append({"zcta": zcta, "difference_square_meters": diff})
    duplicate_keys = Counter((r["zcta"], *pair(r)) for r in rows)
    anomalies["duplicate_source_relationships"] = [list(k) + [n] for k, n in sorted(duplicate_keys.items()) if n > 1]
    anomalies["zero_area_relationships"] = [row_key(r) for r in rows if r["zero_area_relationship"]]
    anomalies["water_only_relationships"] = [row_key(r) for r in rows if r["water_only_overlap"]]
    anomalies["positive_land_sliver_relationships_lt_0_01_percent"] = [
        row_key(r) for r in rows if r["land_share"] is not None and Fraction(0) < r["land_share"] < Fraction(1, 10_000)
    ]
    if anomalies["inconsistent_land_denominator"] or anomalies["inconsistent_water_denominator"]:
        raise AnalysisSafetyError("ZCTA area denominators conflict across accepted relationship rows")
    full_lists = {k: sorted(v, key=canonical_json) for k, v in sorted(anomalies.items())}
    return {
        "zcta_count": len(groups),
        "denominator_conditions": {
            "zero_land_denominator_zctas": sum(next(iter({r["arealand_zcta5_20"] for r in items})) == 0 for items in groups.values()),
            "zero_water_denominator_zctas": sum(next(iter({r["areawater_zcta5_20"] for r in items})) == 0 for items in groups.values()),
            "zero_total_denominator_zctas": sum(next(iter({r["arealand_zcta5_20"] + r["areawater_zcta5_20"] for r in items})) == 0 for items in groups.values()),
            "share_policy_behavior": "undefined shares are preserved as null and fail closed for policies requiring that share",
        },
        "reconciliation_counts": dict(sorted(reconciliation.items())),
        "anomaly_counts": {k: len(v) for k, v in full_lists.items()},
        "bounded_examples": {k: v[:10] for k, v in full_lists.items()},
        "full_list_checksum": deterministic_checksum(full_lists),
        "full_lists": full_lists,
    }


def explain_partition_discrepancies(integrity: dict[str, Any], rejected: list[dict[str, Any]]) -> dict[str, Any]:
    under = {item["zcta"]: -item["difference_square_meters"] for item in integrity["full_lists"].get("water_under_allocation", [])}
    zz_water = Counter()
    positive_zz_rows = 0
    for row in rejected:
        if row["zcta"] and row["source_congressional_geoid"].endswith("ZZ") and (row["areawater_part"] or 0) > 0:
            zz_water[row["zcta"]] += row["areawater_part"]
            positive_zz_rows += 1
    zz_map = dict(sorted(zz_water.items()))
    under_map = dict(sorted(under.items()))
    maps_equal = zz_map == under_map
    totals_equal = sum(zz_map.values()) == sum(under_map.values())
    if not maps_equal or not totals_equal:
        raise AnalysisSafetyError("partition discrepancies could not be bounded to rejected non-district ZZ water rows")
    return {
        "status": "bounded_and_explained",
        "rejected_positive_water_zz_row_count": positive_zz_rows,
        "affected_zctas": len(under_map),
        "explanation": "Accepted district rows reconcile all ZCTA land exactly. The water/total under-allocation for these ZCTAs equals the official file's state-ZZ water partition, which the existing parser rejects because ZZ is not a House district.",
        "rejected_non_district_zz_water_square_meters": sum(zz_map.values()),
        "accepted_partition_water_shortfall_square_meters": sum(under_map.values()),
        "full_partition_maps_equal": maps_equal,
        "aggregate_totals_equal": totals_equal,
        "partition_map_checksum": deterministic_checksum(sorted(zz_map.items())),
    }


def row_key(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "line": row["source_line_number"],
        "zcta": row["zcta"],
        "mapping": f"{row['canonical_source_state']}-{row['source_district']}",
        "land_part": row["arealand_part"],
        "water_part": row["areawater_part"],
    }


def survives(row: dict[str, Any], policy: dict[str, Any]) -> bool:
    kind = policy["kind"]
    if kind == "any":
        return True
    if kind == "positive_total":
        return row["positive_total_overlap"]
    if kind == "positive_land":
        return row["positive_land_overlap"]
    share = row["land_share"]
    if share is None:
        return False
    threshold = policy["threshold"]
    return share >= threshold if policy["inclusive"] else share > threshold


def policies() -> list[dict[str, Any]]:
    result = [
        {"id": "policy_a_any_accepted", "kind": "any", "definition": "every relationship accepted by the existing parser"},
        {"id": "policy_b_positive_total", "kind": "positive_total", "definition": "AREALAND_PART + AREAWATER_PART > 0"},
        {"id": "policy_c_positive_land", "kind": "positive_land", "definition": "AREALAND_PART > 0"},
    ]
    for name, threshold, inclusive in THRESHOLDS:
        op = ">=" if inclusive else ">"
        result.append({
            "id": f"policy_d_{name}",
            "kind": "land_share",
            "threshold": threshold,
            "inclusive": inclusive,
            "definition": f"AREALAND_PART / AREALAND_ZCTA5_20 {op} {fraction_record(threshold)['percent_decimal']}%",
        })
    for policy in result:
        definition_payload = {
            key: ({"numerator": value.numerator, "denominator": value.denominator} if isinstance(value, Fraction) else value)
            for key, value in policy.items()
        }
        policy["definition_sha256"] = deterministic_checksum(definition_payload)
    return result


def top_share_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    shares = sorted((r["land_share"] for r in items if r["land_share"] is not None), reverse=True)
    top = shares[0] if shares else None
    second = shares[1] if len(shares) > 1 else None
    margin = top - second if top is not None and second is not None else None
    ratio = top / second if top is not None and second not in (None, 0) else None
    return {"top": top, "second": second, "margin": margin, "ratio": ratio}


def bucket(value: Fraction | None) -> str:
    if value is None:
        return "undefined"
    for label, boundary in (("0", Fraction(0)), ("lt_0_01", Fraction(1, 10_000)), ("lt_0_1", Fraction(1, 1_000)), ("lt_1", Fraction(1, 100)), ("lt_10", Fraction(1, 10)), ("lt_25", Fraction(1, 4)), ("lt_50", Fraction(1, 2)), ("lt_75", Fraction(3, 4)), ("lt_100", Fraction(1))):
        if label == "0" and value == 0:
            return label
        if label != "0" and value < boundary:
            return label
    return "gte_100"


def seat_classification(row: dict[str, Any], seats: dict[tuple[str, str], dict[str, Any]]) -> str:
    key = pair(row)
    if key == ("DC", "98"):
        candidate = seats.get(("DC", "00"))
        if candidate and candidate["seat_type"] == "delegate" and candidate["seat_status"] == "filled":
            return "candidate_dc_normalization"
        return "no_seeded_seat_match"
    seat = seats.get(key)
    if not seat:
        return "no_seeded_seat_match"
    if seat["congress"] != 119 or seat["snapshot_id"] != SNAPSHOT_ID:
        return "no_seeded_seat_match"
    if seat["seat_status"] == "source_conflict":
        return "source_conflict"
    if seat["seat_status"] == "vacant":
        return "officially_vacant"
    if seat["seat_status"] != "filled" or seat["metadata_currentness"] in {"stale_snapshot", "unknown", "parser_or_layout_unverified"}:
        return "source_conflict"
    if seat["seat_type"] in {"voting_district", "voting_at_large"}:
        return "filled_current_voting_seat"
    if seat["seat_type"] == "delegate":
        return "filled_current_delegate"
    if seat["seat_type"] == "resident_commissioner":
        return "current_resident_commissioner"
    return "no_seeded_seat_match"


def policy_result(
    all_rows: list[dict[str, Any]],
    policy: dict[str, Any],
    baseline_classes: dict[str, str],
    positive_land_classes: dict[str, str],
    seats: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    retained = [r for r in all_rows if survives(r, policy)]
    groups = group_rows(retained)
    all_zctas = sorted({r["zcta"] for r in all_rows})
    classes = {z: classify(groups.get(z, [])) for z in all_zctas}
    class_counts = Counter(classes.values())
    seat_counts = Counter(seat_classification(r, seats) for r in retained)
    stats = {z: top_share_stats(items) for z, items in groups.items()}
    top_distribution = Counter(bucket(v["top"]) for v in stats.values())
    second_distribution = Counter(bucket(v["second"]) for v in stats.values())
    margin_distribution = Counter(bucket(v["margin"]) for v in stats.values())
    changed_a = [z for z in all_zctas if classes[z] != baseline_classes[z]]
    changed_c = [z for z in all_zctas if classes[z] != positive_land_classes[z]]
    ambiguous = {"multi_state", "same_state_multi_district"}
    readiness = readiness_metrics(all_zctas, groups, seats)
    removed = [r for r in all_rows if not survives(r, policy)]
    result = {
        "policy_id": policy["id"],
        "definition": policy["definition"],
        "policy_definition_sha256": policy["definition_sha256"],
        "equality_included": policy.get("inclusive"),
        "retained_relationship_rows": len(retained),
        "removed_relationship_rows": len(removed),
        "retained_unique_zctas": len(groups),
        "zctas_with_no_surviving_relationship": class_counts["no_surviving_relationship"],
        "exactly_one_state_zctas": sum(len({r["canonical_source_state"] for r in items}) == 1 for items in groups.values()),
        "multi_state_zctas": class_counts["multi_state"],
        "exactly_one_district_zctas": class_counts["exactly_one_district"],
        "same_state_multi_district_zctas": class_counts["same_state_multi_district"],
        "total_ambiguous_zctas": class_counts["multi_state"] + class_counts["same_state_multi_district"],
        "classification_changed_from_policy_a": len(changed_a),
        "classification_changed_from_policy_c": len(changed_c),
        "ambiguity_eliminated_from_policy_a": sum(baseline_classes[z] in ambiguous and classes[z] not in ambiguous for z in all_zctas),
        "ambiguity_eliminated_from_policy_c": sum(positive_land_classes[z] in ambiguous and classes[z] not in ambiguous for z in all_zctas),
        "mapping_seat_classifications": dict(sorted(seat_counts.items())),
        **readiness,
        "production_auto_select_eligible_zctas": 0,
        "largest_land_share_distribution": dict(sorted(top_distribution.items())),
        "second_largest_land_share_distribution": dict(sorted(second_distribution.items())),
        "top_minus_second_margin_distribution": dict(sorted(margin_distribution.items())),
        "largest_share_below_50_percent_zctas": sum(v["top"] is not None and v["top"] < Fraction(1, 2) for v in stats.values()),
        "two_or_more_districts_each_exceed_10_percent_zctas": sum(sum(r["land_share"] is not None and r["land_share"] > Fraction(1, 10) for r in items) >= 2 for items in groups.values()),
        "removed_water_only_relationships": sum(r["water_only_overlap"] for r in removed),
        "removed_positive_land_relationships": sum(r["positive_land_overlap"] for r in removed),
        "changed_classification_checksum": deterministic_checksum(changed_a),
        "top_share_records": {
            z: {k: fraction_record(vv) for k, vv in vals.items()} for z, vals in sorted(stats.items())
        },
        "classes": classes,
    }
    return result, changed_a


def readiness_metrics(
    all_zctas: list[str],
    groups: dict[str, list[dict[str, Any]]],
    seats: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, int]:
    supported = {"filled_current_voting_seat", "filled_current_delegate", "current_resident_commissioner"}
    metrics = Counter()
    for zcta in all_zctas:
        items = groups.get(zcta, [])
        pair_classes: dict[tuple[str, str], str] = {}
        for item in items:
            key = pair(item)
            classification = seat_classification(item, seats)
            prior = pair_classes.setdefault(key, classification)
            if prior != classification:
                raise AnalysisSafetyError(f"inconsistent seat classification for surviving pair {key[0]}-{key[1]}")
        classifications = set(pair_classes.values())
        complete = bool(pair_classes) and classifications <= supported
        if complete:
            metrics["all_surviving_mappings_have_supported_current_seat_evidence_zctas"] += 1
            if len(pair_classes) > 1:
                metrics["ambiguous_zctas_with_complete_current_seat_evidence"] += 1
        if len(pair_classes) == 1:
            classification = next(iter(classifications))
            if classification in supported:
                metrics["single_mapping_current_seat_ready_zctas"] += 1
            elif classification == "officially_vacant":
                metrics["single_mapping_officially_vacant_zctas"] += 1
            elif classification == "candidate_dc_normalization":
                metrics["single_mapping_candidate_dc_normalization_zctas"] += 1
            elif classification == "no_seeded_seat_match":
                metrics["single_mapping_no_seeded_seat_match_zctas"] += 1
    return {name: metrics[name] for name in (
        "all_surviving_mappings_have_supported_current_seat_evidence_zctas",
        "single_mapping_current_seat_ready_zctas",
        "ambiguous_zctas_with_complete_current_seat_evidence",
        "single_mapping_officially_vacant_zctas",
        "single_mapping_candidate_dc_normalization_zctas",
        "single_mapping_no_seeded_seat_match_zctas",
    )}


def analyze_policies(rows: list[dict[str, Any]], seats: dict[tuple[str, str], dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    policy_defs = policies()
    all_zctas = sorted({r["zcta"] for r in rows})
    baseline_groups = group_rows(rows)
    positive_groups = group_rows(r for r in rows if r["positive_land_overlap"])
    baseline_classes = {z: classify(baseline_groups.get(z, [])) for z in all_zctas}
    positive_classes = {z: classify(positive_groups.get(z, [])) for z in all_zctas}
    outputs = []
    changed_lists = {}
    for policy in policy_defs:
        result, changed = policy_result(rows, policy, baseline_classes, positive_classes, seats)
        changed_lists[policy["id"]] = changed
        outputs.append(result)
    by_id = {p["policy_id"]: p for p in outputs}
    a_classes = by_id["policy_a_any_accepted"]["classes"]
    b_classes = by_id["policy_b_positive_total"]["classes"]
    c_classes = by_id["policy_c_positive_land"]["classes"]
    water_eliminated = [z for z in all_zctas if a_classes[z] in {"multi_state", "same_state_multi_district"} and c_classes[z] == "exactly_one_district"]
    sliver_policy = by_id["policy_d_gte_0_01_percent"]
    sliver_eliminated = [z for z in all_zctas if c_classes[z] in {"multi_state", "same_state_multi_district"} and sliver_policy["classes"][z] == "exactly_one_district"]
    persistent_25 = [z for z in all_zctas if by_id["policy_d_gte_25_percent"]["classes"][z] in {"multi_state", "same_state_multi_district"}]
    nondominant = [z for z, v in by_id["policy_a_any_accepted"]["top_share_records"].items() if v["top"] and Fraction(v["top"]["numerator"], v["top"]["denominator"]) < Fraction(1, 2)]
    vacant = sorted({r["zcta"] for r in rows if seat_classification(r, seats) == "officially_vacant"})
    dc = sorted({r["zcta"] for r in rows if pair(r) == ("DC", "98")})
    examples = {
        "ambiguity_eliminated_solely_by_removing_water_only_rows": water_eliminated[:10],
        "ambiguity_eliminated_by_removing_positive_land_below_0_01_percent": sliver_eliminated[:10],
        "ambiguity_persists_at_25_percent": persistent_25[:10],
        "multi_state_ambiguity": [z for z in all_zctas if a_classes[z] == "multi_state"][:10],
        "largest_mapping_not_dominant": nondominant[:10],
        "linked_to_currently_vacant_seat": vacant[:10],
        "affected_by_dc_delegate_candidate_normalization": dc[:10],
    }
    summary = {
        "water_only_relationship_count": sum(r["water_only_overlap"] for r in rows),
        "water_only_affected_zcta_count": len({r["zcta"] for r in rows if r["water_only_overlap"]}),
        "zero_area_relationship_count": sum(r["zero_area_relationship"] for r in rows),
        "ambiguity_eliminated_by_removing_water_only_relationships": {
            "total": len(water_eliminated),
            "same_state_multi_district": sum(a_classes[z] == "same_state_multi_district" for z in water_eliminated),
            "multi_state": sum(a_classes[z] == "multi_state" for z in water_eliminated),
        },
        "positive_land_sliver_counts_strictly_below_threshold": {
            name: sum(r["land_share"] is not None and Fraction(0) < r["land_share"] < threshold for r in rows)
            for name, threshold, _ in THRESHOLDS if threshold > 0
        },
        "examples": examples,
        "changed_lists": changed_lists,
    }
    for item in outputs:
        item.pop("classes")
        item.pop("top_share_records")
    return outputs, summary


def execute_select(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    if FORBIDDEN_SQL.search(sql):
        raise AnalysisSafetyError("non-read-only SQL refused")
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def candidate_migration_sha256(sql: str) -> str:
    """Hash the exact reviewed repository text as UTF-8 with canonical LF bytes."""
    return sha256_bytes(sql.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def split_top_level_sql_statements(sql: str) -> list[str]:
    text = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.M | re.S)
    statements: list[str] = []
    start = 0
    depth = 0
    single_quoted = False
    double_quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if single_quoted:
            if char == "'" and next_char == "'":
                index += 2
                continue
            if char == "'":
                single_quoted = False
        elif double_quoted:
            if char == '"' and next_char == '"':
                index += 2
                continue
            if char == '"':
                double_quoted = False
        elif char == "'":
            single_quoted = True
        elif char == '"':
            double_quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise AnalysisSafetyError("candidate migration has unbalanced SQL parentheses")
        elif char == ";" and depth == 0:
            statement = text[start:index].strip()
            if statement:
                statements.append(statement)
            start = index + 1
        index += 1
    if single_quoted or double_quoted or depth != 0 or text[start:].strip():
        raise AnalysisSafetyError("candidate migration has unterminated or unbalanced top-level SQL")
    return statements


def validate_candidate_migration(sql: str) -> dict[str, Any]:
    actual_sha256 = candidate_migration_sha256(sql)
    if actual_sha256 != EXPECTED_CANDIDATE_MIGRATION_SHA256:
        raise AnalysisSafetyError(
            f"candidate migration checksum mismatch: expected {EXPECTED_CANDIDATE_MIGRATION_SHA256}, got {actual_sha256}"
        )
    statements = split_top_level_sql_statements(sql)
    lines = sql.splitlines()
    nonempty = [line.strip() for line in lines if line.strip()]
    if not nonempty or nonempty[0].upper() != "BEGIN;" or nonempty[-1].upper() != "COMMIT;" or sum(line.upper() == "BEGIN;" for line in nonempty) != 1 or sum(line.upper() == "COMMIT;" for line in nonempty) != 1:
        raise AnalysisSafetyError("candidate migration must have exact outer BEGIN/COMMIT wrappers")
    body = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.M | re.S).lower()
    compact = re.sub(r"\s+", " ", body).strip()
    banned = {
        name: bool(re.search(pattern, body))
        for name, pattern in {
            "alter": r"\balter\b",
            "drop": r"\bdrop\b",
            "truncate": r"\btruncate\b",
            "insert": r"\binsert\b",
            "update": r"\bupdate\b",
            "delete": r"\bdelete\s+from\b",
            "copy": r"\bcopy\b",
            "function": r"\bcreate\s+(?:or\s+replace\s+)?function\b",
            "trigger": r"\bcreate\s+trigger\b",
            "grant": r"\bgrant\b",
            "role": r"\bcreate\s+role\b",
            "extension": r"\bcreate\s+extension\b",
            "procedure": r"\bcreate\s+(?:or\s+replace\s+)?procedure\b",
            "view": r"\bcreate\s+(?:materialized\s+)?view\b",
            "sequence": r"\bcreate\s+sequence\b",
            "schema": r"\bcreate\s+schema\b",
            "route_reference": r"zip_district_map\b",
            "feature_flag": r"zip_multi_row_lookup_enabled",
            "frontend": r"\bfrontend\b",
        }.items()
    }
    expected_tables = {
        "zip_mapping_source_snapshots",
        "zip_mapping_source_artifacts",
        "zip_district_relationship_evidence",
        "zip_mapping_policy_runs",
        "zip_mapping_policy_evaluations",
    }
    actual_tables = set(re.findall(r"create table if not exists\s+(\w+)", body))
    table_bodies = {
        table: re.sub(r"\s+", " ", match.group(1)).strip()
        for table in expected_tables
        if (match := re.search(rf"create table if not exists {table}\s*\((.*?)\n\);", body, flags=re.S))
    }
    required_fragments = {
        "artifact_snapshot_fk": ("zip_mapping_source_artifacts", "snapshot_id text not null references zip_mapping_source_snapshots(snapshot_id) on delete cascade"),
        "relationship_artifact_fk": ("zip_district_relationship_evidence", "foreign key (snapshot_id, artifact_id) references zip_mapping_source_artifacts(snapshot_id, artifact_id) on delete cascade"),
        "policy_run_source_fk": ("zip_mapping_policy_runs", "snapshot_id text not null references zip_mapping_source_snapshots(snapshot_id) on delete cascade"),
        "policy_run_house_fk": ("zip_mapping_policy_runs", "seat_snapshot_id text not null references house_member_metadata_snapshots(snapshot_id) on delete restrict"),
        "evaluation_policy_run_fk": ("zip_mapping_policy_evaluations", "foreign key (snapshot_id, policy_run_id) references zip_mapping_policy_runs(snapshot_id, policy_run_id) on delete cascade"),
        "evaluation_relationship_fk": ("zip_mapping_policy_evaluations", "foreign key (snapshot_id, relationship_id, zcta) references zip_district_relationship_evidence(snapshot_id, relationship_id, zcta) on delete cascade"),
        "policy_run_relationship_unique": ("zip_mapping_policy_evaluations", "unique (policy_run_id, relationship_id)"),
        "rank_unique": ("zip_mapping_policy_evaluations", "unique (policy_run_id, zcta, presentation_rank)"),
        "rank_survivor_check": ("zip_mapping_policy_evaluations", "check (relationship_survives or presentation_rank is null)"),
        "auto_select_false": ("zip_mapping_policy_evaluations", "auto_select_eligible boolean not null default false check (auto_select_eligible = false)"),
        "artifact_retrieval_precision": ("zip_mapping_source_artifacts", "retrieved_on date not null, retrieval_precision text not null default 'date' check (retrieval_precision = 'date')"),
        "policy_definition": ("zip_mapping_policy_runs", "policy_definition jsonb not null"),
        "policy_run_identity_unique": ("zip_mapping_policy_runs", "unique (snapshot_id, seat_snapshot_id, policy_version)"),
        "relationship_zcta_unique": ("zip_district_relationship_evidence", "unique (snapshot_id, relationship_id, zcta)"),
        "artifact_composite_identity": ("zip_mapping_source_artifacts", "unique (snapshot_id, artifact_id)"),
        "policy_run_composite_identity": ("zip_mapping_policy_runs", "unique (snapshot_id, policy_run_id)"),
        "relationship_source_line_unique": ("zip_district_relationship_evidence", "unique (snapshot_id, source_line_number)"),
        "relationship_source_geoid_unique": ("zip_district_relationship_evidence", "unique (snapshot_id, zcta, source_congressional_geoid)"),
        "land_part_within_zcta": ("zip_district_relationship_evidence", "check (arealand_part <= arealand_zcta5_20)"),
        "water_part_within_zcta": ("zip_district_relationship_evidence", "check (areawater_part <= areawater_zcta5_20)"),
        "total_part_within_zcta": ("zip_district_relationship_evidence", "check ( (arealand_part::numeric + areawater_part::numeric) <= (arealand_zcta5_20::numeric + areawater_zcta5_20::numeric) )"),
        "normalization_all_or_none": ("zip_district_relationship_evidence", "check ( (candidate_normalization_rule is null and candidate_canonical_state is null and candidate_canonical_district is null) or (candidate_normalization_rule is not null and candidate_canonical_state is not null and candidate_canonical_district is not null) )"),
        "normalization_rule_nonblank": ("zip_district_relationship_evidence", "check (candidate_normalization_rule is null or btrim(candidate_normalization_rule) <> '')"),
        "normalization_state_format": ("zip_district_relationship_evidence", "check (candidate_canonical_state is null or candidate_canonical_state ~ '^[a-z]{2}$')"),
        "normalization_district_format": ("zip_district_relationship_evidence", "check (candidate_canonical_district is null or candidate_canonical_district ~ '^[0-9]{2}$')"),
    }
    required_indexes = {
        "idx_zip_mapping_source_artifacts_snapshot": "on zip_mapping_source_artifacts (snapshot_id)",
        "idx_zip_relationship_evidence_zcta": "on zip_district_relationship_evidence (snapshot_id, zcta)",
        "idx_zip_relationship_evidence_pair": "on zip_district_relationship_evidence (snapshot_id, canonical_source_state, source_district)",
        "idx_zip_mapping_policy_runs_source": "on zip_mapping_policy_runs (snapshot_id, policy_version, run_status)",
        "idx_zip_mapping_policy_runs_house_snapshot": "on zip_mapping_policy_runs (seat_snapshot_id)",
        "idx_zip_policy_evaluations_run_zcta": "on zip_mapping_policy_evaluations (policy_run_id, zcta)",
        "idx_zip_policy_evaluations_survival": "on zip_mapping_policy_evaluations (policy_run_id, relationship_survives)",
    }
    missing = [name for name, (table, fragment) in required_fragments.items() if fragment not in table_bodies.get(table, "")]
    for index_name, definition in required_indexes.items():
        if f"create index if not exists {index_name} {definition}" not in compact:
            missing.append(index_name)
    share_columns = re.findall(r"\b(?:land|water|total)_share_(?:numerator|denominator)\b", body)
    raw_area_columns = {"arealand_zcta5_20", "areawater_zcta5_20", "arealand_part", "areawater_part"}
    relationship_body = table_bodies.get("zip_district_relationship_evidence", "")
    raw_area_only = not share_columns and all(re.search(rf"\b{name}\s+bigint\s+not null", relationship_body) for name in raw_area_columns)
    if not raw_area_only:
        missing.append("raw_area_only_exact_share_contract")
    if "policy_definition_sha256" in body:
        missing.append("jsonb_is_sole_policy_definition_truth")
    expected_statement_count = 2 + len(expected_tables) + len(required_indexes)
    table_statement_names = []
    index_statement_names = []
    unapproved_statements = []
    for position, statement in enumerate(statements):
        normalized = re.sub(r"\s+", " ", statement).strip()
        if position == 0 and normalized.upper() == "BEGIN":
            continue
        if position == len(statements) - 1 and normalized.upper() == "COMMIT":
            continue
        table_match = re.fullmatch(r"create table if not exists\s+(\w+)\s*\(.*\)", statement.strip(), flags=re.I | re.S)
        index_match = re.fullmatch(r"create index if not exists\s+(\w+)\s+on\s+.*", statement.strip(), flags=re.I | re.S)
        if table_match:
            table_statement_names.append(table_match.group(1).lower())
        elif index_match:
            index_statement_names.append(index_match.group(1).lower())
        else:
            unapproved_statements.append(normalized[:120])
    if len(statements) != expected_statement_count or set(table_statement_names) != expected_tables or len(table_statement_names) != len(expected_tables) or set(index_statement_names) != set(required_indexes) or len(index_statement_names) != len(required_indexes) or unapproved_statements:
        missing.append("exact_top_level_statement_inventory")
    if any(banned.values()) or actual_tables != expected_tables or missing:
        raise AnalysisSafetyError(f"candidate migration is outside the reviewed additive evidence envelope: banned={banned}, missing={missing}, tables={sorted(actual_tables)}")
    return {
        "path": str(CANDIDATE_MIGRATION.relative_to(ROOT)).replace("\\", "/"),
        "sha256": actual_sha256,
        "tables": sorted(actual_tables),
        "required_contracts": sorted(required_fragments),
        "required_indexes": sorted(required_indexes),
        "exact_share_contract": "raw_area_only",
        "retrieval_precision": "date",
        "policy_definition_identity": "JSONB sole database source of truth; deterministic SHA-256 reported in analysis artifacts",
        "top_level_statement_count": len(statements),
        "additive_only": True,
        "contains_dml": False,
        "applied": False,
    }


def inspect_production_read_only(env_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    db_url = dotenv_values(env_path).get("DATABASE_URL")
    if not db_url:
        raise AnalysisSafetyError("DATABASE_URL missing from required environment file")
    target = house.target(str(db_url), env_path)
    previews, freshness = house.load_previews(mode="postcheck")
    repository = inspect_repository_state(ROOT)
    ensure_repository_state_safe(repository)
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(str(db_url), row_factory=dict_row, autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only=on")
        session_read_only = conn.execute("SHOW default_transaction_read_only").fetchone()["default_transaction_read_only"] == "on"
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout='30000ms'")
            tx_read_only = conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
            timeout = conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"]
            actual_by_table = {}
            checksums = {}
            counts = {}
            for table in house.TABLES:
                columns = list(previews[table][0])
                order = ",".join(house.NATURAL_KEYS[table])
                sql = f"SELECT {','.join(columns)} FROM {table} WHERE snapshot_id=%s ORDER BY {order}"
                actual = [house.canonical(r) for r in execute_select(conn, sql, (SNAPSHOT_ID,))]
                expected = [house.canonical(r) for r in sorted(previews[table], key=lambda r: tuple(str(r.get(k)) for k in house.NATURAL_KEYS[table]))]
                counts[table] = len(actual)
                checksums[table] = {
                    "expected": house.content_sha(expected),
                    "database": house.content_sha(actual),
                    "match": actual == expected,
                }
                actual_by_table[table] = actual
            zip_count = execute_select(conn, "SELECT COUNT(*) AS n FROM zip_district_mappings")[0]["n"]
            legislators = execute_select(conn, "SELECT id,bioguide_id,chamber,state,district,in_office,updated_at FROM legislators ORDER BY id")
    if not session_read_only or not tx_read_only:
        raise AnalysisSafetyError("database read-only mode was not confirmed")
    if counts != {table: house.PREVIEWS[table][1] for table in house.TABLES} or not all(v["match"] for v in checksums.values()):
        raise AnalysisSafetyError("House snapshot counts or canonical checksums differ from the approved snapshot")
    if int(zip_count) != 0:
        raise AnalysisSafetyError("zip_district_mappings is nonempty")
    seat_rows = actual_by_table["house_seat_status_evidence"]
    seat_keys = [(r["canonical_state"], r["canonical_district"]) for r in seat_rows]
    if len(seat_keys) != len(set(seat_keys)):
        raise AnalysisSafetyError("duplicate seeded seat matches block analysis readiness")
    stale = [r for r in seat_rows if r["metadata_currentness"] in {"stale_snapshot", "unknown", "parser_or_layout_unverified"}]
    conflicts = [r for r in seat_rows if r["seat_status"] in {"source_conflict", "unknown"}]
    if stale or conflicts:
        raise AnalysisSafetyError("stale, unknown, or conflicting seeded seat evidence blocks analysis readiness")
    route = repository["route_state"]
    flag = repository["feature_flag"]
    if not route["lookup_zip_reads_zip_district_map"] or not route["lookup_zip_races_reads_zip_district_map"] or route["either_public_endpoint_reads_zip_district_mappings"] or flag["enabled"]:
        raise AnalysisSafetyError("public ZIP route or feature-flag safety contract changed")
    result = {
        "target": target,
        "session_default_transaction_read_only": session_read_only,
        "transaction_read_only": tx_read_only,
        "statement_timeout": timeout,
        "snapshot_id": SNAPSHOT_ID,
        "snapshot_freshness": freshness,
        "table_counts": counts,
        "canonical_database_checksums": checksums,
        "house_snapshot_domain_counts": {
            "voting_representatives": sum(r["member_type"] == "voting_representative" for r in actual_by_table["house_member_service_evidence"]),
            "delegates": sum(r["member_type"] == "delegate" for r in actual_by_table["house_member_service_evidence"]),
            "resident_commissioner": sum(r["member_type"] == "resident_commissioner" for r in actual_by_table["house_member_service_evidence"]),
            "filled_seats": sum(r["seat_status"] == "filled" for r in seat_rows),
            "vacant_seats": sum(r["seat_status"] == "vacant" for r in seat_rows),
            "source_conflicts": sum(r["seat_status"] == "source_conflict" for r in seat_rows),
            "unknown_seats": sum(r["seat_status"] == "unknown" for r in seat_rows),
        },
        "legislators_fingerprint": house.fingerprint(legislators),
        "zip_district_mappings_row_count": int(zip_count),
        "route_state": route,
        "feature_flag": flag,
        "production_auto_select_eligible_count": 0,
    }
    return result, seat_rows


def reconcile_seats(rows: list[dict[str, Any]], seat_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]]]:
    seats: dict[tuple[str, str], dict[str, Any]] = {}
    for seat in seat_rows:
        key = (seat["canonical_state"], seat["canonical_district"])
        if key in seats:
            raise AnalysisSafetyError(f"duplicate seeded seat match: {key[0]}-{key[1]}")
        seats[key] = seat
    pair_classes = {}
    for row in rows:
        pair_classes[pair(row)] = seat_classification(row, seats)
    counts = Counter(pair_classes.values())
    row_counts = Counter(seat_classification(row, seats) for row in rows)
    dc = seats.get(("DC", "00"))
    return {
        "unique_source_pair_classifications": dict(sorted(counts.items())),
        "relationship_row_classifications": dict(sorted(row_counts.items())),
        "vacant_source_pairs": sorted(f"{s}-{d}" for (s, d), cls in pair_classes.items() if cls == "officially_vacant"),
        "dc_candidate_normalization": {
            "source_pair": "DC-98",
            "candidate_pair": "DC-00",
            "status": "candidate_normalization_only",
            "seeded_delegate_match_proved": bool(dc and dc["seat_type"] == "delegate" and dc["seat_status"] == "filled"),
            "runtime_approved": False,
            "source_row_altered": False,
        },
        "production_auto_select_eligible_count": 0,
    }, seats


def serializable_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: (fraction_record(v) if isinstance(v, Fraction) else v) for k, v in row.items()}


def per_zcta_ranking_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for zcta, items in group_rows(rows).items():
        ranked = sorted(items, key=lambda r: (r["land_share"] is None, -(r["land_share"] or Fraction(0)), r["canonical_source_state"], r["source_district"]))
        top = ranked[0] if ranked else None
        second = ranked[1] if len(ranked) > 1 else None
        top_share = top["land_share"] if top else None
        second_share = second["land_share"] if second else None
        output.append({
            "zcta": zcta,
            "top_mapping": f"{top['canonical_source_state']}-{top['source_district']}" if top else None,
            "top_land_share": fraction_record(top_share),
            "second_mapping": f"{second['canonical_source_state']}-{second['source_district']}" if second else None,
            "second_land_share": fraction_record(second_share),
            "top_minus_second_land_share_margin": fraction_record(top_share - second_share) if top_share is not None and second_share is not None else None,
            "top_to_second_ratio": ratio_record(top_share / second_share) if top_share is not None and second_share not in (None, 0) else None,
            "surviving_mapping_counts": {p["id"]: sum(survives(r, p) for r in items) for p in policies()},
        })
    return output


def write_local_artifacts(rows: list[dict[str, Any]], policy_summary: dict[str, Any], integrity: dict[str, Any]) -> dict[str, Any]:
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    payloads = {
        "normalized_relationship_evidence.jsonl": "".join(canonical_json(serializable_row(r)) + "\n" for r in sorted(rows, key=lambda r: r["source_line_number"])),
        "per_zcta_rankings.jsonl": "".join(canonical_json(r) + "\n" for r in per_zcta_ranking_rows(rows)),
        "changed_classifications.json": json.dumps(policy_summary["changed_lists"], indent=2, sort_keys=True) + "\n",
        "anomaly_lists.json": json.dumps(integrity["full_lists"], indent=2, sort_keys=True) + "\n",
    }
    files = []
    for name, text in payloads.items():
        path = LOCAL_ROOT / name
        path.write_text(text, encoding="utf-8")
        files.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "row_count": text.count("\n") if name.endswith(".jsonl") else None,
            "size_bytes": path.stat().st_size,
            "sha256": source_import.sha256_file(path),
        })
    return {"analysis_id": ANALYSIS_ID, "files": files}


def report_without_internal_lists(report: dict[str, Any]) -> dict[str, Any]:
    result = dict(report)
    result["geographic_integrity"] = {k: v for k, v in report["geographic_integrity"].items() if k != "full_lists"}
    result["sensitivity_summary"] = {k: v for k, v in report["sensitivity_summary"].items() if k != "changed_lists"}
    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ZIP Overlap Sensitivity and Bounded Mapping-Stage Design V1",
        "",
        "> Read-only analysis. Area overlap is not population share, address dominance, or a definitive representative lookup.",
        "",
        "## Source and safety",
        "",
        f"- Official source SHA-256: `{report['source']['identity']['actual_sha256']}` (verified: `{report['source']['identity']['official_file_identity_verified']}`)",
        f"- Accepted / rejected rows: `{report['source']['baseline']['accepted_rows']}` / `{report['source']['baseline']['rejected_rows']}`",
        f"- Production ZIP mapping rows before / after: `{report['production_precheck']['zip_district_mappings_row_count']}` / `{report['production_postcheck']['zip_district_mappings_row_count']}`",
        f"- Production auto-select eligible: `0`",
        "",
        "## Sensitivity results",
        "",
        "| Policy | Rows | No mapping | One district | Same-state multi | Multi-state | Ambiguous |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for p in report["policies"]:
        lines.append(
            f"| `{p['policy_id']}` | {p['retained_relationship_rows']} | {p['zctas_with_no_surviving_relationship']} | {p['exactly_one_district_zctas']} | {p['same_state_multi_district_zctas']} | {p['multi_state_zctas']} | {p['total_ambiguous_zctas']} |"
        )
    lines += [
        "",
        "## Current-seat evidence metrics",
        "",
        "The prior broad readiness metric is preserved as `all_surviving_mappings_have_supported_current_seat_evidence_zctas`. It may include ambiguous ZCTAs. `single_mapping_current_seat_ready_zctas` requires exactly one supported surviving canonical pair. Neither metric is production auto-select eligibility.",
        "",
        "| Policy | All mappings supported | Strict single mapping | Ambiguous, complete evidence | Single vacant | Single DC candidate | Single unmatched |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for p in report["policies"]:
        lines.append(
            f"| `{p['policy_id']}` | {p['all_surviving_mappings_have_supported_current_seat_evidence_zctas']} | {p['single_mapping_current_seat_ready_zctas']} | {p['ambiguous_zctas_with_complete_current_seat_evidence']} | {p['single_mapping_officially_vacant_zctas']} | {p['single_mapping_candidate_dc_normalization_zctas']} | {p['single_mapping_no_seeded_seat_match_zctas']} |"
        )
    zz = report["geographic_integrity"]["partition_discrepancy_explanation"]
    lines += [
        "",
        "## Measured overlap findings",
        "",
        f"- Water-only relationships: `{report['sensitivity_summary']['water_only_relationship_count']}` across `{report['sensitivity_summary']['water_only_affected_zcta_count']}` ZCTAs.",
        f"- Zero-area relationships: `{report['sensitivity_summary']['zero_area_relationship_count']}`.",
        f"- Integrity anomaly full-list checksum: `{report['geographic_integrity']['full_list_checksum']}`.",
        f"- Rejected positive-water state-`ZZ` rows: `{zz['rejected_positive_water_zz_row_count']}` across `{zz['affected_zctas']}` ZCTAs, totaling `{zz['rejected_non_district_zz_water_square_meters']}` square meters.",
        f"- Complete `ZZ` partition map equals the accepted-row under-allocation map: `{zz['full_partition_maps_equal']}`; checksum `{zz['partition_map_checksum']}`.",
        "",
        "## Decision boundary",
        "",
        "- Possible mappings: area evidence supports preserving all official relationships with raw land/water provenance.",
        "- Ranked mappings: land share can support an explicitly labeled, versioned presentation order, but cannot claim where residents or addresses are concentrated.",
        "- Auto-select: unsupported and disabled. Reducing ambiguity with a threshold does not establish correctness.",
        "- ZCTAs are Census approximations, not USPS ZIP delivery boundaries. Land share is not population share, and area dominance does not prove address dominance.",
        "- Recommended next accuracy source: both Census block-level population allocation and a full-address congressional-district lookup; population weighting improves ZIP-level ranking evidence, while address lookup is needed for automatic representative selection.",
        "",
        "## Staging decision",
        "",
        "The existing `zip_district_mappings` table cannot reproduce raw area evidence or policy decisions. The candidate additive migration separates immutable snapshots/artifacts/relationship evidence, immutable policy runs, and relationship evaluations. Relationship parts are constrained within ZCTA totals; candidate normalization is all-or-none and format-safe. Exact shares are derived from raw integer areas only. Artifact retrieval precision is an honest date.",
        "",
        "`policy_definition JSONB` is the sole database definition truth; `(snapshot_id, seat_snapshot_id, policy_version)` identifies one definition, while deterministic hashes live in analysis artifacts. Migration bytes and the exact five-table/seven-index statement inventory are pinned before structural checks.",
        "",
        f"Candidate migration SHA-256: `{report['candidate_migration_validation']['sha256']}`. Applied: `{report['candidate_migration_validation']['applied']}`.",
        "",
        "## Product-use decision table",
        "",
        "| Use | Any overlap | Positive land | Min land share | Dominance/margin | Block population | Full address |",
        "|---|---|---|---|---|---|---|",
        "| Display all possible districts | yes | incomplete alone | incomplete alone | no | yes | yes |",
        "| Order possible districts | weak | weak | policy-sensitive | useful presentation aid | stronger ZIP-level evidence | definitive for address |",
        "| Hide water-only by default, retain evidence | supports | supports | not needed | not needed | supports | supports |",
        "| Label low material overlap | raw area only | raw area only | supports versioned label | supports versioned label | stronger context | supports |",
        "| Ask for street address | supports need | supports need | supports need | supports need | still useful | fulfills request |",
        "| Automatically choose representative | no | no | no | no | no | yes |",
        "",
        "No production or runtime mutation occurred.",
        "",
    ]
    return "\n".join(lines)


def build_manifest(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "zip_overlap_sensitivity_source_manifest_v1",
        "analysis_id": ANALYSIS_ID,
        "source": {
            "filename": report["source"]["identity"]["actual_file_name"],
            "size_bytes": report["source"]["identity"]["actual_file_size_bytes"],
            "sha256": report["source"]["identity"]["actual_sha256"],
        },
        "parser_version": PARSER_VERSION,
        "policy_definitions": [{k: (fraction_record(v) if isinstance(v, Fraction) else v) for k, v in p.items()} for p in policies()],
        "readiness_metric_definitions": {
            "all_surviving_mappings_have_supported_current_seat_evidence_zctas": "one or more surviving mappings and every distinct pair has supported filled current-seat evidence; ambiguity is allowed",
            "single_mapping_current_seat_ready_zctas": "exactly one distinct surviving pair classified as a filled current voting seat, delegate, or resident commissioner",
            "production_auto_select_eligible_zctas": "fixed at zero",
        },
        "candidate_migration": report["candidate_migration_validation"],
        "local_artifacts": report["local_artifacts"],
        "row_counts": report["source"]["baseline"],
        "deterministic_ordering": {
            "normalized_relationship_evidence": "source_line_number ascending",
            "per_zcta_rankings": "ZCTA ascending; land share descending with canonical pair tie-break",
            "changed_classifications": "policy ID keys and ZCTA values ascending",
            "anomaly_lists": "anomaly class then canonical JSON value",
        },
        "reproduction_command": "python backend/scripts/analyze_zip_overlap_sensitivity.py --dry-run --read-only --input .local/zip_source_official/tab20_cd11920_zcta520_natl.txt --env-path backend/.env --output docs/review_packets/zip_overlap_sensitivity_bounded_staging_design_v1.json --markdown-output docs/review_packets/zip_overlap_sensitivity_bounded_staging_design_v1.md",
        "production_write_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--env-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    if not args.dry_run or not args.read_only:
        print("ERROR: refusing to run unless both --dry-run and --read-only are present", file=sys.stderr)
        return 2
    try:
        precheck, seat_rows = inspect_production_read_only(args.env_path)
        migration_validation = validate_candidate_migration(CANDIDATE_MIGRATION.read_text(encoding="utf-8"))
        rows, rejected, source = normalize_official_rows(args.input)
        integrity = validate_geographic_integrity(rows)
        integrity["partition_discrepancy_explanation"] = explain_partition_discrepancies(integrity, rejected)
        reconciliation, seats = reconcile_seats(rows, seat_rows)
        policy_results, sensitivity = analyze_policies(rows, seats)
        local = write_local_artifacts(rows, sensitivity, integrity)
        postcheck, post_seats = inspect_production_read_only(args.env_path)
        if precheck["canonical_database_checksums"] != postcheck["canonical_database_checksums"] or precheck["legislators_fingerprint"] != postcheck["legislators_fingerprint"] or precheck["zip_district_mappings_row_count"] != postcheck["zip_district_mappings_row_count"] or seat_rows != post_seats:
            raise AnalysisSafetyError("protected production state changed during analysis")
        report = {
            "schema_version": SCHEMA_VERSION,
            "analysis_id": ANALYSIS_ID,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": {"dry_run": True, "read_only": True, "production_mutation": False, "runtime_mutation": False, "auto_select_enabled": False},
            "source": {**source, "rejected_rows_checksum": deterministic_checksum(rejected), "rejected_row_examples": rejected[:10]},
            "geographic_code_handling": {
                "standard_numbered_relationship_rows": sum(r["source_district"] not in {"00", "98"} for r in rows),
                "state_at_large_00_relationship_rows": sum(r["source_district"] == "00" for r in rows),
                "dc_98_relationship_rows": sum(pair(r) == ("DC", "98") for r in rows),
                "dc_internal_delegate_convention": "DC-00",
                "dc_status": "candidate_normalization_only",
                "territory_rows_rejected_by_existing_parser": source["territory_rejections"],
                "official_source_codes_altered": False,
            },
            "geographic_integrity": integrity,
            "current_seat_reconciliation": reconciliation,
            "policies": policy_results,
            "sensitivity_summary": sensitivity,
            "local_artifacts": local,
            "candidate_migration_validation": migration_validation,
            "production_precheck": precheck,
            "production_postcheck": postcheck,
            "conclusions": {
                "possible_mapping": "supported as source-backed geographic evidence, including retained water-only and tiny-overlap rows",
                "preferred_or_ranked_mapping": "supported only as an explicitly versioned and caveated presentation aid",
                "auto_select_mapping": "not supported by area evidence; disabled",
                "recommended_next_accuracy_source": "both Census block-level population allocation and full-address congressional-district lookup",
                "existing_zip_district_mappings_schema_sufficient": False,
                "candidate_migration": "backend/migrations/0015_zip_mapping_source_evidence.sql",
                "candidate_migration_applied": False,
                "production_auto_select_eligible_count": 0,
            },
        }
        manifest = build_manifest(report)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        public_report = report_without_internal_lists(report)
        args.output.write_text(json.dumps(public_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.markdown_output.write_text(render_markdown(public_report), encoding="utf-8")
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"analysis_id": ANALYSIS_ID, "output": str(args.output), "accepted_rows": len(rows), "production_mutation": False, "production_auto_select_eligible_count": 0}, sort_keys=True))
        return 0
    except (AnalysisSafetyError, house.SeedSafetyError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
