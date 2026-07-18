from __future__ import annotations

import hashlib
import io
import json
from email.message import Message
from fractions import Fraction
from pathlib import Path
from zipfile import ZipFile

import pytest

from backend.scripts import analyze_zip_population_weighted_ambiguity as analysis
from backend.scripts import retrieve_zip_population_sources as retrieval


def population_row(**overrides):
    row = {
        "zcta": "12345", "canonical_state": "NY", "source_district": "01",
        "source_relationship_identity": "source:1", "relationship_population": 60,
        "zcta_population": 100, "land_share_numerator": 40, "land_share_denominator": 100,
        "water_only_overlap": False, "current_seat_classification": "filled_current_voting_seat",
        "population_coverage_exact": True, "block_assignment_complete": True,
    }
    row.update(overrides)
    return row


def manifest_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    specs = [{"role": "block_population", "filename": "source.zip", "url": "https://www2.census.gov/source.zip", "release_vintage": "v1"}, {"role": "technical_documentation", "filename": "docs.pdf", "url": "https://www2.census.gov/docs.pdf", "release_vintage": "v1"}]
    monkeypatch.setattr(retrieval, "expected_inventory", lambda: specs)
    root = tmp_path / "batch"
    raw = root / "raw"
    raw.mkdir(parents=True)
    artifacts = []
    for spec in specs:
        path = raw / spec["filename"]
        path.write_bytes(spec["filename"].encode())
        artifacts.append({**spec, "actual_filename": spec["filename"], "retrieval_mode": "direct_http", "http_status": 200, "content_type": "application/octet-stream", "retrieved_at": "2026-07-18T00:00:00+00:00", "retrieval_timestamp_status": "recorded", "size_bytes": path.stat().st_size, "sha256": retrieval.sha256_file(path), "retry_history": [{"attempt": 1, "status": 200, "result": "success"}]})
    manifest = retrieval.build_manifest("batch", artifacts, batch_completed_at="2026-07-18T00:01:00+00:00")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, root, manifest


@pytest.mark.parametrize("url", ["http://www2.census.gov/a", "https://example.com/a", "file:///tmp/a"])
def test_official_host_allowlist_rejects_nonofficial_or_non_https(url):
    with pytest.raises(retrieval.SourceContractError):
        retrieval.validate_url(url)


def test_source_index_has_complete_51_state_population_inventory():
    inventory = retrieval.expected_inventory()
    assert sum(item["role"] == "block_population" for item in inventory) == 51
    assert {item["role"] for item in inventory} == {"block_population", "block_to_zcta", "block_to_cd119", "technical_documentation"}


def test_exact_approved_manifest_bytes_pass():
    assert analysis.verify_approved_source_manifest(retrieval.DEFAULT_MANIFEST) == analysis.EXPECTED_SOURCE_MANIFEST_SHA256


def test_formatting_only_approved_manifest_change_fails(tmp_path):
    value = json.loads(retrieval.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    changed = tmp_path / "manifest.json"
    changed.write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(analysis.PopulationAnalysisError, match="exact-byte"):
        analysis.verify_approved_source_manifest(changed)


def test_coordinated_raw_and_manifest_checksum_replacement_still_fails_manifest_pin(tmp_path):
    value = json.loads(retrieval.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    value["artifacts"][0]["sha256"] = hashlib.sha256(b"replacement").hexdigest()
    changed = tmp_path / "manifest.json"
    changed.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(analysis.PopulationAnalysisError, match="exact-byte"):
        analysis.verify_approved_source_manifest(changed)


def test_replay_accepts_exact_inventory(tmp_path, monkeypatch):
    path, root, _ = manifest_fixture(tmp_path, monkeypatch)
    assert retrieval.replay_manifest(path, root)["replay_verified"] is True


def test_replay_rejects_checksum_mismatch(tmp_path, monkeypatch):
    path, root, _ = manifest_fixture(tmp_path, monkeypatch)
    (root / "raw/source.zip").write_bytes(b"mutated")
    with pytest.raises(retrieval.SourceContractError, match="byte size differs|checksum differs"):
        retrieval.replay_manifest(path, root)


@pytest.mark.parametrize("mutation", ["omit", "extra"])
def test_replay_rejects_manifest_omission_or_extra(tmp_path, monkeypatch, mutation):
    path, root, manifest = manifest_fixture(tmp_path, monkeypatch)
    if mutation == "omit":
        manifest["artifacts"].pop()
    else:
        manifest["artifacts"].append(dict(manifest["artifacts"][0], filename="extra.zip"))
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(retrieval.SourceContractError, match="inventory mismatch"):
        retrieval.replay_manifest(path, root)


def test_replay_rejects_extra_raw_artifact(tmp_path, monkeypatch):
    path, root, _ = manifest_fixture(tmp_path, monkeypatch)
    (root / "raw/extra.bin").write_bytes(b"extra")
    with pytest.raises(retrieval.SourceContractError, match="raw directory inventory differs"):
        retrieval.replay_manifest(path, root)


def test_replay_rejects_incompatible_geography_vintage(tmp_path, monkeypatch):
    path, root, manifest = manifest_fixture(tmp_path, monkeypatch)
    manifest["source_vintage"] = "2024 blocks"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(retrieval.SourceContractError, match="source vintage differs"):
        retrieval.replay_manifest(path, root)


@pytest.mark.parametrize("field,error", [("landing_pages", "landing-page"), ("derivation_ordering_rules", "ordering")])
def test_replay_rejects_landing_page_or_ordering_mutation(tmp_path, monkeypatch, field, error):
    path, root, manifest = manifest_fixture(tmp_path, monkeypatch)
    manifest[field] = ["mutated"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(retrieval.SourceContractError, match=error):
        retrieval.replay_manifest(path, root)


def test_replay_rejects_artifact_url_mutation(tmp_path, monkeypatch):
    path, root, manifest = manifest_fixture(tmp_path, monkeypatch)
    manifest["artifacts"][0]["url"] = "https://www2.census.gov/replacement.zip"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(retrieval.SourceContractError, match="inventory mismatch"):
        retrieval.replay_manifest(path, root)


def test_local_resume_validation_has_no_fabricated_http_provenance(tmp_path):
    spec = {"role": "block_population", "filename": "source.zip", "url": "https://www2.census.gov/source.zip", "release_vintage": "v1"}
    path = tmp_path / "source.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("member.txt", "official bytes")
    result = retrieval.resume_existing(spec, path)
    assert result["retrieval_mode"] == "validated_local_resume"
    assert result["validated_at"]
    assert result["validation"]["result"] == "passed"
    assert result["original_http_status"] is None
    assert result["original_retrieved_at"] is None
    assert "http_status" not in result and "retrieved_at" not in result


def test_direct_http_retrieval_records_actual_response_provenance(tmp_path, monkeypatch):
    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(b"official bytes")
            self.headers = Message()
            self.headers["Content-Type"] = "application/zip"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(retrieval.urllib.request, "urlopen", lambda request, timeout: Response())
    spec = {"role": "block_population", "filename": "source.zip", "url": "https://www2.census.gov/source.zip", "release_vintage": "v1"}
    result = retrieval.retrieve_one(spec, tmp_path / "source.zip")
    assert result["retrieval_mode"] == "direct_http"
    assert result["http_status"] == 200
    assert result["content_type"] == "application/zip"
    assert result["retrieved_at"] and result["retrieval_timestamp_status"] == "recorded"
    assert result["retry_history"] == [{"attempt": 1, "status": 200, "result": "success"}]


def test_manifest_completion_is_distinct_from_artifact_retrieval(tmp_path, monkeypatch):
    _, _, manifest = manifest_fixture(tmp_path, monkeypatch)
    assert manifest["batch_completed_at"] != manifest["artifacts"][0]["retrieved_at"]
    assert "retrieved_at" not in {key: value for key, value in manifest.items() if key != "artifacts"}


def test_malformed_block_geoid_fails():
    with pytest.raises(analysis.PopulationAnalysisError, match="malformed"):
        analysis.parse_block_geoid("123", 1)


def test_duplicate_block_fails():
    with pytest.raises(analysis.PopulationAnalysisError, match="duplicate block"):
        analysis.validate_population_records([("010010001001000", 1), ("010010001001000", 1)])


def test_negative_or_missing_population_fails():
    with pytest.raises(analysis.PopulationAnalysisError, match="negative"):
        analysis.validate_population_records([("010010001001000", -1)])
    with pytest.raises(analysis.PopulationAnalysisError, match="missing"):
        analysis.parse_population(None, 1)


def test_conflicting_population_fails():
    with pytest.raises(analysis.PopulationAnalysisError, match="conflicting population"):
        analysis.validate_population_records([("010010001001000", 1), ("010010001001000", 2)])


def test_conflicting_zcta_assignment_fails():
    with pytest.raises(analysis.PopulationAnalysisError, match="conflicting ZCTA"):
        analysis.validate_assignment("010010001001000", 0, ["12345", "12346"], ["01"])


def test_conflicting_district_assignment_fails_for_populated_block():
    with pytest.raises(analysis.PopulationAnalysisError, match="split_populated_block_unresolved"):
        analysis.validate_assignment("010010001001000", 1, ["12345"], ["01", "02"])


def test_zero_population_split_block_is_classified():
    assert analysis.validate_assignment("010010001001000", 0, ["12345"], ["01", "02"]) == "split_zero_population_block"


def test_official_colorado_split_assignment_is_exact():
    assert analysis.validate_assignment(analysis.SPLIT_BLOCK, 10, ["80000"], ["08"]) == "exact_official_assignment"


def test_exact_population_reconciliation():
    assert analysis.validate_population_records([("010010001001000", 3), ("010010001001001", 7)]) == {"block_count": 2, "population": 10}


def test_exact_fraction_thresholds_have_inclusive_equality():
    assert analysis.exact_threshold(1, 10_000, Fraction(1, 10_000))
    assert not analysis.exact_threshold(0, 10_000, Fraction(1, 10_000))
    assert analysis.exact_threshold(1, 100, Fraction(0), positive=True)


def test_deterministic_population_ranking():
    rows = [population_row(source_district="02", source_relationship_identity="b", relationship_population=40), population_row(source_district="01", source_relationship_identity="a", relationship_population=60)]
    assert [row["source_district"] for row in analysis.rank_population_rows(rows)] == ["01", "02"]


def test_population_rank_tie_is_explicit_and_deterministic():
    rows = [population_row(source_district="02", source_relationship_identity="b", relationship_population=50), population_row(source_district="01", source_relationship_identity="a", relationship_population=50)]
    ranked = analysis.rank_population_rows(rows)
    assert [row["source_district"] for row in ranked] == ["01", "02"]
    assert all(row["population_rank_tied"] for row in ranked)


@pytest.mark.parametrize("mapping_count", [1, 2])
def test_zero_population_zcta_has_no_population_rank_or_winner(mapping_count):
    rows = [population_row(source_district=f"{index:02d}", source_relationship_identity=str(index), relationship_population=0, zcta_population=0) for index in range(1, mapping_count + 1)]
    ranked = analysis.rank_population_rows(rows)
    assert [row["deterministic_relationship_order"] for row in ranked] == list(range(1, mapping_count + 1))
    assert all(row["population_rank"] is None and row["population_rank_tied"] is None for row in ranked)
    assert all(row["population_rank_status"] == "undefined_zero_population_zcta" for row in ranked)


def test_zero_population_zcta_is_excluded_from_land_population_agreement():
    comparison = analysis.compare_land_population([population_row(relationship_population=0, zcta_population=0)])
    assert comparison["counts"]["zero_population_zctas_excluded_from_ranking"] == 1
    assert comparison["counts"].get("positive_population_unique_top_agreement", 0) == 0


def test_land_population_top_disagreement():
    rows = [population_row(source_district="01", relationship_population=60, land_share_numerator=40), population_row(source_district="02", source_relationship_identity="source:2", relationship_population=40, land_share_numerator=60)]
    assert analysis.compare_land_population(rows)["counts"]["positive_population_unique_top_disagreement"] == 1


def test_exact_half_is_inclusive_but_not_strict_majority():
    status = analysis.majority_status(50, 100)
    assert status == {"inclusive_gte_50_percent": True, "strict_majority": False, "exactly_half": True, "no_strict_majority": True}
    assert analysis.majority_status(5001, 10_000)["strict_majority"] is True


def test_zero_population_relationship_removed_by_p1():
    rows = [population_row(), population_row(source_district="02", source_relationship_identity="source:2", relationship_population=0)]
    policy = analysis.classify_policy(rows, "p1_positive", Fraction(0))
    assert policy["retained_relationships"] == 1
    assert policy["removed_zero_population_relationships"] == 1


def test_small_land_meaningful_population_is_computable_exactly():
    row = population_row(relationship_population=10, zcta_population=100, land_share_numerator=1, land_share_denominator=10_000)
    assert analysis.exact_threshold(row["relationship_population"], row["zcta_population"], Fraction(1, 10))
    assert Fraction(row["land_share_numerator"], row["land_share_denominator"]) == Fraction(1, 10_000)


def test_zero_population_unassigned_block_preserves_population_not_block_coverage():
    assert analysis.coverage_status(1, 0) == {"population_coverage_exact": True, "block_assignment_complete": False}
    with pytest.raises(analysis.PopulationAnalysisError, match="prevents exact"):
        analysis.coverage_status(1, 1)


def test_no_common_block_relationship_is_not_labeled_exact():
    land_row = {"zcta": "12345", "canonical_source_state": "NY", "source_district": "01", "source_artifact_sha256": "a" * 64, "source_line_number": 2, "arealand_part": 1, "arealand_zcta5_20": 1, "water_only_overlap": False}
    row = analysis.combine_relationships([land_row], {})[0]
    assert row["assignment_quality"] == "no_common_block_relationship"
    assert row["contributing_common_blocks"] == 0


def test_compact_pl_fixture_parses_logrecno_summary_level_and_p1(tmp_path):
    path = tmp_path / "aa2020.pl.zip"
    geo_rows = [
        "x|x|040|x|x|x|x|0001|x|010010001001000\n",
        "x|x|750|x|x|x|x|0002|x|010010001001001\n",
    ]
    data_rows = ["x|x|x|x|0001|999\n", "x|x|x|x|0002|7\n"]
    with ZipFile(path, "w") as archive:
        archive.writestr("aageo2020.pl", "".join(geo_rows))
        archive.writestr("aa000012020.pl", "".join(data_rows))
    assert list(analysis.pl_block_rows(path, "aa")) == [("010010001001001", 7, 2)]


def test_external_sort_and_full_common_block_merge(tmp_path):
    directory = tmp_path / "sort"
    directory.mkdir()
    path = directory / "01.txt"
    path.write_text("010010001001001|b|2\n010010001001000|a|1\n", encoding="ascii")
    assert analysis._external_sort_state_files(directory, chunk_size=1)["reordered_states"] == 1
    zcta = list(analysis._derived_rows(path))
    district = [("010010001001000", "01", 1), ("010010001001001", "02", 2)]
    population = [("010010001001000", 3, 1), ("010010001001001", 7, 2)]
    merged = list(analysis.merge_state_blocks(population, zcta, district))
    assert [(row[0], row[1], row[3], row[5]) for row in merged] == [("010010001001000", 3, "a", "01"), ("010010001001001", 7, "b", "02")]


@pytest.mark.parametrize("side", ["zcta", "district"])
def test_common_block_merge_rejects_leftovers(side):
    block = "010010001001000"
    population = [(block, 1, 1)]
    zcta = [(block, "12345", 1)]
    district = [(block, "01", 1)]
    extra = ("010010001001001", "12345" if side == "zcta" else "01", 2)
    (zcta if side == "zcta" else district).append(extra)
    with pytest.raises(analysis.PopulationAnalysisError, match="does not cover"):
        list(analysis.merge_state_blocks(population, zcta, district))


def test_common_block_merge_rejects_duplicate_population_assignment():
    block = "010010001001000"
    with pytest.raises(analysis.PopulationAnalysisError, match="duplicate or unsorted"):
        list(analysis.merge_state_blocks([(block, 1, 1), (block, 1, 2)], [(block, "12345", 1)], [(block, "01", 1)]))


def test_vacancy_and_dc_candidate_classification():
    seats = {
        ("TX", "23"): {"congress": 119, "snapshot_id": analysis.SNAPSHOT_ID, "seat_status": "vacant", "seat_type": "voting_district", "metadata_currentness": "current"},
        ("DC", "00"): {"congress": 119, "snapshot_id": analysis.SNAPSHOT_ID, "seat_status": "filled", "seat_type": "delegate", "metadata_currentness": "current"},
    }
    assert analysis.land.seat_classification({"canonical_source_state": "TX", "source_district": "23"}, seats) == "officially_vacant"
    assert analysis.land.seat_classification({"canonical_source_state": "DC", "source_district": "98"}, seats) == "candidate_dc_normalization"


def test_wrong_house_snapshot_fails_closed():
    seats = {("NY", "01"): {"congress": 118, "snapshot_id": "wrong", "seat_status": "filled", "seat_type": "voting_district", "metadata_currentness": "current"}}
    assert analysis.land.seat_classification({"canonical_source_state": "NY", "source_district": "01"}, seats) == "no_seeded_seat_match"


def test_production_contract_is_read_only_and_eligibility_zero():
    source = Path(analysis.land.__file__).read_text(encoding="utf-8")
    assert "SET default_transaction_read_only=on" in source
    assert "SET TRANSACTION READ ONLY" in source
    assert '"production_auto_select_eligible_count": 0' in Path(analysis.__file__).read_text(encoding="utf-8")


def test_project_specific_target_and_zip_empty_gate_are_reused():
    source = Path(analysis.land.__file__).read_text(encoding="utf-8")
    assert "target = house.target" in source
    assert "zip_district_mappings is nonempty" in source


def test_route_and_feature_flag_gate_is_reused():
    source = Path(analysis.land.__file__).read_text(encoding="utf-8")
    assert "public ZIP route or feature-flag safety contract changed" in source


def test_0015_hash_is_pinned_and_no_0016_is_created():
    assert analysis.land.candidate_migration_sha256(analysis.land.CANDIDATE_MIGRATION.read_text(encoding="utf-8")) == analysis.EXPECTED_0015_SHA256
    assert not (analysis.ROOT / "backend/migrations/0016_zip_population_evidence.sql").exists()
