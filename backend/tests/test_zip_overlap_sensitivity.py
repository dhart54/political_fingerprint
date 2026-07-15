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


def test_readiness_metrics_separate_complete_ambiguous_from_strict_ready():
    mappings = [
        row(zcta="00001", district="01"),
        row(zcta="00001", district="02", line=3),
        row(zcta="00002", district="01", line=4),
        row(zcta="00003", district="03", line=5),
        row(zcta="00004", state="DC", district="98", line=6),
    ]
    seats = {
        ("NC", "01"): seat(district="01"),
        ("NC", "02"): seat(district="02"),
        ("NC", "03"): seat(district="03", status="vacant"),
        ("DC", "00"): seat(state="DC", district="00", seat_type="delegate"),
    }
    metrics = analysis.readiness_metrics(
        ["00001", "00002", "00003", "00004", "00005"],
        analysis.group_rows(mappings),
        seats,
    )
    assert metrics["all_surviving_mappings_have_supported_current_seat_evidence_zctas"] == 2
    assert metrics["ambiguous_zctas_with_complete_current_seat_evidence"] == 1
    assert metrics["single_mapping_current_seat_ready_zctas"] == 1
    assert metrics["single_mapping_officially_vacant_zctas"] == 1
    assert metrics["single_mapping_candidate_dc_normalization_zctas"] == 1
    assert metrics["single_mapping_no_seeded_seat_match_zctas"] == 0


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
    assert len(result["tables"]) == 5
    assert result["exact_share_contract"] == "raw_area_only"
    assert result["retrieval_precision"] == "date"
    assert result["sha256"] == analysis.EXPECTED_CANDIDATE_MIGRATION_SHA256
    assert result["top_level_statement_count"] == 14


@pytest.mark.parametrize("sql", ["ALTER TABLE x ADD y int", "INSERT INTO x VALUES (1)", "DROP TABLE x"])
def test_candidate_migration_rejects_out_of_envelope_sql(sql):
    with pytest.raises(analysis.AnalysisSafetyError):
        analysis.validate_candidate_migration(sql)


@pytest.mark.parametrize("mutation", ["comment", "whitespace", "character", "substitute"])
def test_candidate_migration_exact_reviewed_bytes_are_pinned(mutation):
    sql = analysis.CANDIDATE_MIGRATION.read_text(encoding="utf-8")
    changed = {
        "comment": sql.replace("BEGIN;", "BEGIN;\n-- comment-only change", 1),
        "whitespace": sql.replace("BEGIN;", "BEGIN; ", 1),
        "character": sql.replace("Unapplied", "unapplied", 1),
        "substitute": sql.replace("zip_mapping_policy_runs", "zip_mapping_policy_runz"),
    }[mutation]
    with pytest.raises(analysis.AnalysisSafetyError, match="checksum mismatch"):
        analysis.validate_candidate_migration(changed)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("FOREIGN KEY (snapshot_id, policy_run_id)", "FOREIGN KEY (policy_run_id)"),
        ("REFERENCES zip_mapping_source_artifacts(snapshot_id, artifact_id)\n        ON DELETE CASCADE", "REFERENCES zip_mapping_source_artifacts(snapshot_id, artifact_id)\n        ON DELETE RESTRICT"),
        ("REFERENCES house_member_metadata_snapshots(snapshot_id) ON DELETE RESTRICT", "REFERENCES house_member_metadata_snapshots(snapshot_id) ON DELETE CASCADE"),
        ("UNIQUE (policy_run_id, relationship_id)", "UNIQUE (relationship_id)"),
        ("UNIQUE (policy_run_id, zcta, presentation_rank)", "UNIQUE (policy_run_id, presentation_rank)"),
        ("CHECK (relationship_survives OR presentation_rank IS NULL)", "CHECK (presentation_rank IS NULL)"),
        ("arealand_part BIGINT NOT NULL", "arealand_part BIGINT NOT NULL,\n    land_share_numerator BIGINT"),
        ("CREATE INDEX IF NOT EXISTS idx_zip_policy_evaluations_run_zcta", "CREATE INDEX IF NOT EXISTS removed_zip_policy_evaluations_run_zcta"),
        ("CHECK (arealand_part <= arealand_zcta5_20)", "CHECK (arealand_part >= 0)"),
        ("CHECK (areawater_part <= areawater_zcta5_20)", "CHECK (areawater_part >= 0)"),
        ("(arealand_part::NUMERIC + areawater_part::NUMERIC)", "(arealand_part + areawater_part)"),
        ("candidate_normalization_rule IS NULL\n         AND candidate_canonical_state IS NULL", "candidate_normalization_rule IS NULL\n         OR candidate_canonical_state IS NULL"),
        ("BTRIM(candidate_normalization_rule) <> ''", "candidate_normalization_rule <> ''"),
        ("candidate_canonical_state ~ '^[A-Z]{2}$'", "candidate_canonical_state ~ '^[A-Z]+$'"),
        ("candidate_canonical_district ~ '^[0-9]{2}$'", "candidate_canonical_district ~ '^[0-9]+$'"),
        ("UNIQUE (snapshot_id, seat_snapshot_id, policy_version)", "UNIQUE (snapshot_id, policy_version)"),
        ("policy_definition JSONB NOT NULL", "policy_definition JSONB NOT NULL,\n    policy_definition_sha256 TEXT"),
    ],
)
def test_candidate_migration_required_contract_mutations_fail(monkeypatch, old, new):
    sql = analysis.CANDIDATE_MIGRATION.read_text(encoding="utf-8")
    assert old in sql
    changed = sql.replace(old, new, 1)
    monkeypatch.setattr(analysis, "EXPECTED_CANDIDATE_MIGRATION_SHA256", analysis.candidate_migration_sha256(changed))
    with pytest.raises(analysis.AnalysisSafetyError):
        analysis.validate_candidate_migration(changed)


def test_candidate_migration_requires_exact_outer_wrappers(monkeypatch):
    sql = analysis.CANDIDATE_MIGRATION.read_text(encoding="utf-8")
    changed = sql.replace("BEGIN;", "BEGIN TRANSACTION;", 1)
    monkeypatch.setattr(analysis, "EXPECTED_CANDIDATE_MIGRATION_SHA256", analysis.candidate_migration_sha256(changed))
    with pytest.raises(analysis.AnalysisSafetyError, match="outer BEGIN/COMMIT"):
        analysis.validate_candidate_migration(changed)


@pytest.mark.parametrize("statement", [
    "CREATE TABLE unapproved_table (id INTEGER);",
    "CREATE VIEW unapproved_view AS SELECT 1 AS id;",
    "CREATE MATERIALIZED VIEW unapproved_materialized_view AS SELECT 1 AS id;",
    "CREATE SEQUENCE unapproved_sequence;",
    "CREATE INDEX IF NOT EXISTS idx_unapproved_extra ON zip_mapping_source_snapshots (congress);",
    "CREATE SCHEMA unapproved_schema;",
    "CREATE FUNCTION unapproved_function() RETURNS INTEGER LANGUAGE SQL AS 'SELECT 1';",
    "CREATE PROCEDURE unapproved_procedure() LANGUAGE SQL AS 'SELECT 1';",
    "CREATE TRIGGER unapproved_trigger BEFORE INSERT ON zip_mapping_source_snapshots EXECUTE FUNCTION unapproved_function();",
    "GRANT SELECT ON zip_mapping_source_snapshots TO PUBLIC;",
    "CREATE ROLE unapproved_role;",
    "CREATE EXTENSION pgcrypto;",
    "SELECT 1;",
    "TRUNCATE zip_mapping_source_snapshots;",
    "COPY zip_mapping_source_snapshots FROM STDIN;",
])
def test_candidate_migration_rejects_every_extra_top_level_statement(monkeypatch, statement):
    sql = analysis.CANDIDATE_MIGRATION.read_text(encoding="utf-8")
    changed = sql.replace("COMMIT;", f"{statement}\n\nCOMMIT;", 1)
    monkeypatch.setattr(analysis, "EXPECTED_CANDIDATE_MIGRATION_SHA256", analysis.candidate_migration_sha256(changed))
    with pytest.raises(analysis.AnalysisSafetyError):
        analysis.validate_candidate_migration(changed)


def test_partition_shortfall_must_match_rejected_zz_water():
    integrity = analysis.validate_geographic_integrity([row(land=100, water=5, zwater=10)])
    rejected = [{"zcta": "00001", "source_congressional_geoid": "37ZZ", "areawater_part": 5}]
    result = analysis.explain_partition_discrepancies(integrity, rejected)
    assert result["status"] == "bounded_and_explained"
    assert result["full_partition_maps_equal"] is True
    assert result["rejected_positive_water_zz_row_count"] == 1


@pytest.mark.parametrize("rejected", [
    [
        {"zcta": "00001", "source_congressional_geoid": "37ZZ", "areawater_part": 5},
        {"zcta": "99999", "source_congressional_geoid": "37ZZ", "areawater_part": 1},
    ],
    [{"zcta": "00001", "source_congressional_geoid": "37ZZ", "areawater_part": 4}],
])
def test_partition_shortfall_rejects_extra_or_mismatched_zz_water(rejected):
    integrity = analysis.validate_geographic_integrity([row(land=100, water=5, zwater=10)])
    with pytest.raises(analysis.AnalysisSafetyError, match="could not be bounded"):
        analysis.explain_partition_discrepancies(integrity, rejected)
