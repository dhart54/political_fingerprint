from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path

import pytest

from backend.app.etl import current_house_member_metadata as metadata


ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/"backend/fixtures/current_house_member_metadata_sample/congress_member_detail.json"
CASES=ROOT/"backend/tests/_current_house_member_metadata_cases"
MIGRATION=ROOT/"backend/migrations/0014_house_member_service_and_seat_status.sql"
SCRIPT=ROOT/"backend/scripts/dry_run_current_house_member_metadata.py"


def setup_function():
    if CASES.exists():shutil.rmtree(CASES)


def teardown_function():
    if CASES.exists():shutil.rmtree(CASES)


def parse_detail(payload:dict):
    folder=CASES/"details"; folder.mkdir(parents=True); (folder/"member.json").write_text(json.dumps(payload),encoding="utf-8"); return metadata.parse_congress_details(folder,retrieved_on=date(2026,7,12))


def test_congress_list_pagination_is_bounded_and_current_house_filtering():
    assert metadata.MAX_LIST_PAGES==3 and metadata.MAX_CURRENT_MEMBERS==700 and metadata.MAX_DETAIL_REQUESTS==600
    assert "offset=250" in metadata.list_url(250)
    assert metadata.is_house_list_row({"terms":{"item":[{"chamber":"House of Representatives"}]}})
    assert not metadata.is_house_list_row({"terms":{"item":[{"chamber":"Senate"}]}})


def test_representative_at_large_and_year_precision():
    row=parse_detail(json.loads(FIXTURE.read_text(encoding="utf-8")))[0]
    assert row["member_type"]=="voting_representative" and row["source_district"]=="0" and row["canonical_district"]=="00"
    assert row["service_start_year"]==2025 and row["service_date_precision"]=="year"
    assert "service_start_date" not in row


@pytest.mark.parametrize(("state","kind","expected"),[("DC","Delegate","delegate"),("GU","Delegate","delegate"),("PR","Resident Commissioner","resident_commissioner")])
def test_nonvoting_member_normalization_preserves_role(state,kind,expected):
    payload=json.loads(FIXTURE.read_text(encoding="utf-8")); member=payload["member"]; member["bioguideId"]="X000001"; member["district"]=None; term=member["terms"][0]; term["stateCode"]=state; term["district"]=None; term["memberType"]=kind
    row=parse_detail(payload)[0]; assert row["member_type"]==expected and row["source_district"]=="" and row["canonical_district"]=="00"


def test_dc_98_reconciliation_rule_is_explicit_in_report_script():
    text=SCRIPT.read_text(encoding="utf-8")
    assert '("DC","00") if pair==("DC","98")' in text
    assert "dc_census_98_to_house_delegate_00_v1" in text


def test_house_location_roles_and_layout_failure():
    assert metadata.parse_house_location("Alaska At Large")==("AK","00","voting_at_large")
    assert metadata.parse_house_location("District of Columbia Delegate")==("DC","00","delegate")
    assert metadata.parse_house_location("Puerto Rico Resident Commissioner")==("PR","00","resident_commissioner")
    with pytest.raises(metadata.SourceContractError):metadata.parse_house_directory("changed layout")


def test_clerk_active_vacancy_and_later_oath_resolution():
    active='<h1>Vacancies of the 119th Congress</h1><li class="vacancy_release"><a href="/members/TX23/vacancy">Office</a><p>Resigned April 14, 2026</p></li>'
    assert metadata.parse_clerk_vacancies(active)[0]["canonical_district"]=="23"
    resolved=active.replace("</li>","Took the Oath of Office</li>")
    assert metadata.parse_clerk_vacancies(resolved)==[]


def test_seat_reconciliation_single_duplicate_conflict_and_vacancy():
    member={"canonical_state":"NC","canonical_district":"04"}; house=[{"canonical_state":"NC","canonical_district":"04","vacant":False}]
    assert metadata.reconcile_seats([member],house,[])[("NC","04")]=="current_cross_source_confirmed"
    assert metadata.reconcile_seats([member,member],house,[])[("NC","04")]=="source_conflict"
    assert metadata.reconcile_seats([],house,[{"canonical_state":"NC","canonical_district":"04"}])[("NC","04")]=="vacant_officially_confirmed"
    assert metadata.reconcile_seats([member],house,[{"canonical_state":"NC","canonical_district":"04"}])[("NC","04")]=="source_conflict"


def test_stale_snapshot_and_primary_only_status():
    assert metadata.metadata_currentness(retrieved_on=date(2026,7,1),today=date(2026,7,12),cross_source_confirmed=True)=="stale_snapshot"
    assert metadata.metadata_currentness(retrieved_on=date(2026,7,12),today=date(2026,7,12),cross_source_confirmed=False)=="current_primary_source_only"


def test_missing_bioguide_and_layout_fail_closed():
    payload=json.loads(FIXTURE.read_text(encoding="utf-8")); del payload["member"]["bioguideId"]
    with pytest.raises(metadata.SourceContractError):parse_detail(payload)


def test_no_api_key_is_blocked_without_network():
    with pytest.raises(metadata.SourceContractError,match="blocked_no_api_key"):metadata.retrieve_official(api_key="",output_dir=CASES)


def test_migration_is_additive_separates_service_and_seat_and_is_not_executed():
    sql=MIGRATION.read_text(encoding="utf-8").lower(); script=SCRIPT.read_text(encoding="utf-8").lower()
    assert "create table if not exists house_member_service_evidence" in sql
    assert "create table if not exists house_seat_status_evidence" in sql
    assert "on delete set null" in sql and "seat_status <> 'vacant'" in sql
    assert not re.search(r"\b(drop|truncate|alter)\b|\bdelete\s+from\b|\bupdate\s+\w+\s+set\b",sql)
    assert "0014_house_member_service_and_seat_status.sql" in script
    compact=script.replace(" ","").lower()
    assert "migration_applied=any(proposed_tables.values())" in compact
    assert "ifmigration_applied:raise" in compact


def test_database_paths_are_read_only_and_final_production_eligibility_zero():
    script=SCRIPT.read_text(encoding="utf-8").lower()
    evaluator=(ROOT/"backend/scripts/evaluate_zip_source_member_readiness.py").read_text(encoding="utf-8").lower()
    assert "inspect_members_read_only" in script
    assert "set transaction read only" in evaluator and "default_transaction_read_only" in evaluator
    for statement in ("insert into","delete from","truncate ","drop table","copy ",".commit("):
        assert statement not in script
    assert '"production_auto_select_eligible_count":0' in script
