from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from backend.scripts import analyze_zip_overlap_sensitivity as analysis


def row(zcta="00001", state="NC", district="01", land=90, water=0, zland=100, zwater=10, line=2):
    return {
        "source_line_number": line,
        "zcta": zcta,
        "source_congressional_geoid": f"00{district}",
        "canonical_source_state": state,
        "source_district": district,
        "arealand_zcta5_20": zland,
        "areawater_zcta5_20": zwater,
        "arealand_part": land,
        "areawater_part": water,
        "positive_land_overlap": land > 0,
        "positive_water_overlap": water > 0,
        "positive_total_overlap": land + water > 0,
        "water_only_overlap": land == 0 and water > 0,
        "zero_area_relationship": land == 0 and water == 0,
        "land_share": Fraction(land, zland) if zland else None,
        "water_share": Fraction(water, zwater) if zwater else None,
        "total_share": Fraction(land + water, zland + zwater) if zland + zwater else None,
        "source_artifact_sha256": "a" * 64,
        "parser_version": analysis.PARSER_VERSION,
    }


def seat(state="NC", district="01", status="filled", seat_type="voting_district", currentness="current_cross_source_confirmed"):
    return {
        "snapshot_id": analysis.SNAPSHOT_ID,
        "congress": 119,
        "canonical_state": state,
        "canonical_district": district,
        "seat_status": status,
        "seat_type": seat_type,
        "metadata_currentness": currentness,
    }


def test_official_file_identity_mismatch_fails_closed(monkeypatch):
    monkeypatch.setattr(analysis.source_import, "inspect_official_file_identity", lambda _path: {"official_file_identity_verified": False})
    with pytest.raises(analysis.AnalysisSafetyError, match="exact pinned official"):
        analysis.normalize_official_rows(analysis.ROOT / "backend/fixtures/zip_source_dry_run_sample/census_119_cd_zcta_official_layout_excerpt.txt")


def test_cli_refuses_without_both_report_only_flags():
    common = ["--input", "missing.txt", "--env-path", "missing.env"]
    assert analysis.main(common) == 2
    assert analysis.main(["--dry-run", *common]) == 2
    assert analysis.main(["--read-only", *common]) == 2


@pytest.mark.parametrize("value", ["", "1.2", "-1", "abc", None])
def test_malformed_or_negative_area_rejected(value):
    with pytest.raises(analysis.AnalysisSafetyError, match="nonnegative integer"):
        analysis.parse_nonnegative_integer(value, "AREALAND_PART", 7)


def test_inconsistent_zcta_denominators_fail_closed():
    rows = [row(district="01", zland=100), row(district="02", zland=101, line=3)]
    with pytest.raises(analysis.AnalysisSafetyError, match="denominators conflict"):
        analysis.validate_geographic_integrity(rows)


def test_exact_reconciliation_and_over_under_allocation():
    exact = [row(district="01", land=60, water=4), row(district="02", land=40, water=6, line=3)]
    result = analysis.validate_geographic_integrity(exact)
    assert result["reconciliation_counts"]["land_exact"] == 1
    over = copy.deepcopy(exact); over[1]["arealand_part"] = 41
    under = copy.deepcopy(exact); under[1]["arealand_part"] = 39
    assert analysis.validate_geographic_integrity(over)["anomaly_counts"]["land_over_allocation"] == 1
    assert analysis.validate_geographic_integrity(under)["anomaly_counts"]["land_under_allocation"] == 1


def test_zero_area_water_only_and_positive_land_sliver_detection():
    rows = [row(land=0, water=0, zland=20_000), row(district="02", land=0, water=10, zland=20_000, line=3), row(district="03", land=1, water=0, zland=20_000, line=4)]
    result = analysis.validate_geographic_integrity(rows)
    assert result["anomaly_counts"]["zero_area_relationships"] == 1
    assert result["anomaly_counts"]["water_only_relationships"] == 1
    assert result["anomaly_counts"]["positive_land_sliver_relationships_lt_0_01_percent"] == 1


def test_exact_threshold_boundary_includes_equality_and_uses_fraction():
    boundary = row(land=1, zland=10_000)
    p = next(p for p in analysis.policies() if p["id"] == "policy_d_gte_0_01_percent")
    assert isinstance(boundary["land_share"], Fraction)
    assert analysis.survives(boundary, p) is True
    assert analysis.survives(row(land=0, zland=10_000), p) is False
    assert analysis.fraction_record(Fraction(1, 10))["decimal"] == "0.1"
    assert "float" not in analysis.Path(analysis.__file__).read_text(encoding="utf-8")


def test_top_second_margin_and_ratio_are_deterministic_fractions():
    stats = analysis.top_share_stats([row(land=60), row(district="02", land=25, line=3)])
    assert stats == {"top": Fraction(3, 5), "second": Fraction(1, 4), "margin": Fraction(7, 20), "ratio": Fraction(12, 5)}


def test_multi_state_and_same_state_ambiguity():
    assert analysis.classify([row(), row(state="SC", district="07", line=3)]) == "multi_state"
    assert analysis.classify([row(), row(district="02", line=3)]) == "same_state_multi_district"


def test_ambiguity_eliminated_and_no_survivor_under_policy():
    rows = [row(land=100), row(district="02", land=0, water=10, line=3)]
    groups = analysis.group_rows(r for r in rows if r["positive_land_overlap"])
    assert analysis.classify(groups["00001"]) == "exactly_one_district"
    high = next(p for p in analysis.policies() if p["id"] == "policy_d_gte_50_percent")
    assert not [r for r in [row(land=49)] if analysis.survives(r, high)]


def test_vacant_conflict_stale_and_wrong_snapshot_classification():
    mapping = row()
    assert analysis.seat_classification(mapping, {("NC", "01"): seat(status="vacant")}) == "officially_vacant"
    assert analysis.seat_classification(mapping, {("NC", "01"): seat(status="source_conflict")}) == "source_conflict"
    assert analysis.seat_classification(mapping, {("NC", "01"): seat(currentness="stale_snapshot")}) == "source_conflict"
    wrong = seat(); wrong["snapshot_id"] = "wrong"
    assert analysis.seat_classification(mapping, {("NC", "01"): wrong}) == "no_seeded_seat_match"


def test_seeded_seat_duplicate_blocks_reconciliation():
    with pytest.raises(analysis.AnalysisSafetyError, match="duplicate seeded seat"):
        analysis.reconcile_seats([row()], [seat(), seat()])


def test_dc_98_is_candidate_normalization_only():
    mapping = row(state="DC", district="98")
    seats = {("DC", "00"): seat(state="DC", district="00", seat_type="delegate")}
    assert analysis.seat_classification(mapping, seats) == "candidate_dc_normalization"
    result, _ = analysis.reconcile_seats([mapping], list(seats.values()))
    assert result["dc_candidate_normalization"]["status"] == "candidate_normalization_only"
    assert result["dc_candidate_normalization"]["runtime_approved"] is False


def test_territory_rejection_counts_are_pinned():
    assert analysis.EXPECTED_TERRITORY_REJECTIONS == {"AS": 2, "GU": 8, "MP": 4, "PR": 133, "VI": 7}


def test_read_only_sql_enforcement():
    class Connection:
        def execute(self, *_args, **_kwargs):
            raise AssertionError("must refuse before execution")
    with pytest.raises(analysis.AnalysisSafetyError, match="non-read-only SQL"):
        analysis.execute_select(Connection(), "UPDATE zip_district_mappings SET zip='x'")


def test_project_specific_target_verifier_is_reused():
    assert analysis.house.target is not None
    text = analysis.Path(analysis.__file__).read_text(encoding="utf-8")
    assert "house.target(str(db_url), env_path)" in text


def test_zip_nonempty_route_flag_and_production_eligibility_guards_are_static():
    text = analysis.Path(analysis.__file__).read_text(encoding="utf-8")
    assert 'if int(zip_count) != 0' in text
    assert 'route["either_public_endpoint_reads_zip_district_mappings"]' in text
    assert 'flag["enabled"]' in text
    assert text.count('"production_auto_select_eligible_count": 0') >= 3


def test_candidate_migration_is_additive_and_unapplied():
    result = analysis.validate_candidate_migration(analysis.CANDIDATE_MIGRATION.read_text(encoding="utf-8"))
    assert result["additive_only"] is True and result["contains_dml"] is False and result["applied"] is False
    assert len(result["tables"]) == 4


@pytest.mark.parametrize("sql", ["ALTER TABLE x ADD y int", "INSERT INTO x VALUES (1)", "DROP TABLE x"])
def test_candidate_migration_rejects_out_of_envelope_sql(sql):
    with pytest.raises(analysis.AnalysisSafetyError):
        analysis.validate_candidate_migration(sql)


def test_partition_shortfall_must_match_rejected_zz_water():
    integrity = analysis.validate_geographic_integrity([row(land=100, water=5, zwater=10)])
    rejected = [{"zcta": "00001", "source_congressional_geoid": "37ZZ", "areawater_part": 5}]
    result = analysis.explain_partition_discrepancies(integrity, rejected)
    assert result["status"] == "bounded_and_explained"
