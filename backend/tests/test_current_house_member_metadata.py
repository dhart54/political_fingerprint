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


def write_replay_manifest(batch:Path, rows:list[dict]):
    manifest={"snapshot_id":"s1","retrieval_started_at":"2026-07-12T00:00:00+00:00","retrieval_completed_at":"2026-07-12T01:00:00+00:00","congress":119,"parser_version":metadata.PARSER_VERSION,"artifacts":rows,"artifact_allowlist":[row["path"] for row in rows],"batch_completion_status":"complete"}
    (batch/"retrieval_manifest.json").write_text(json.dumps(manifest),encoding="utf-8")


def replay_row(batch:Path,rel:str,source:str,status:int=200):
    path=batch/rel
    return {"source":source,"path":rel,"response_status":status,"sha256":metadata.sha256_file(path),"size_bytes":path.stat().st_size,"retrieved_at":"2026-07-12T00:00:00+00:00","retry_count":0}


def make_valid_replay_batch()->tuple[Path,list[dict]]:
    batch=CASES/"batch"; (batch/"member_details").mkdir(parents=True,exist_ok=True)
    house_row={"bioguideId":"A000001","terms":{"item":[{"chamber":"House of Representatives"}]}}
    pages=[
        (0,{"members":[house_row],"pagination":{"count":1,"next":metadata.list_url(250)}}),
        (250,{"members":[],"pagination":{"count":1}}),
    ]
    rows=[]
    for offset,payload in pages:
        rel=f"congress_119_current_{offset:03d}.json"; (batch/rel).write_text(json.dumps(payload),encoding="utf-8"); rows.append(replay_row(batch,rel,metadata.list_url(offset)))
    (batch/"member_details/A000001.json").write_text(json.dumps({"member":{"bioguideId":"A000001"}}),encoding="utf-8")
    rows.append(replay_row(batch,"member_details/A000001.json",metadata.detail_url("A000001")))
    for rel,source in (("house_representatives.html",metadata.HOUSE_DIRECTORY_URL),("clerk_vacancies.html",metadata.CLERK_VACANCIES_URL)):
        (batch/rel).write_text("official",encoding="utf-8"); rows.append(replay_row(batch,rel,source))
    write_replay_manifest(batch,rows)
    return batch,rows


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
    resolved_row=metadata.parse_clerk_vacancies(resolved)[0]
    assert resolved_row["active"] is False and resolved_row["seat_status"]=="filled"


@pytest.mark.parametrize(("label","expected_type"),[("Special Election","special_general"),("Special General Election","special_general"),("Special Primary Election","special_primary")])
def test_clerk_special_election_variants_and_member_name_boundary(label,expected_type):
    html=f'<h1>Vacancies of the 119th Congress</h1><li class="vacancy_release"><a href="/members/CA14/vacancy">Office</a> Resigned April 14, 2026 Rep. Eric Swalwell {label} August 18, 2026 California Secretary of State</li>'
    row=metadata.parse_clerk_vacancies(html)[0]
    assert row["former_member_name"]=="Eric Swalwell"
    assert row["special_election_type"]==expected_type and row["special_election_date"]=="2026-08-18"


def test_clerk_multiple_adjacent_active_and_resolved_records():
    html='<h1>Vacancies of the 119th Congress</h1><li class="vacancy_release"><a href="/members/GA13/vacancy">GA</a> Passed Away April 22, 2026 Rep. David Scott Special Election July 28, 2026 Georgia Secretary of State</li><li class="vacancy_release"><a href="/members/NC04/vacancy">NC</a> Resigned May 1, 2026 Representative Sample Member Special General Election June 2, 2026 Sworn in June 8, 2026</li>'
    rows=metadata.parse_clerk_vacancies(html)
    assert [(row["canonical_state"],row["active"]) for row in rows]==[("GA",True),("NC",False)]
    assert rows[0]["former_member_name"]=="David Scott" and rows[1]["former_member_name"]=="Sample Member"


def test_seat_reconciliation_single_duplicate_conflict_and_vacancy():
    member={"canonical_state":"NC","canonical_district":"04","member_type":"voting_representative","name":"Sample Member","official_url":"https://sample.house.gov"}; house=[{"canonical_state":"NC","canonical_district":"04","vacant":False,"seat_type":"voting_district","displayed_member_name":"Sample Member","member_domain":"sample.house.gov"}]
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
    assert "ifany(proposed.values()):raise" in compact
    assert "house_member_metadata_snapshots" in sql and "house_member_metadata_snapshot_artifacts" in sql
    assert "unique (snapshot_id, congress, canonical_state, canonical_district)" in sql
    assert "special_election_date date" in sql and "successor_election_date" not in sql
    assert "house_member_service_evidence_artifacts" in sql and "house_seat_status_evidence_artifacts" in sql
    assert "foreign key (snapshot_id, artifact_path)" in sql and "on delete cascade" in sql
    assert "primary key (snapshot_id, bioguide_id, congress, canonical_state, canonical_district, artifact_path, evidence_role)" in sql
    assert "primary key (snapshot_id, congress, canonical_state, canonical_district, artifact_path, evidence_role)" in sql
    assert not re.search(r"unique\s*\(\s*congress,\s*canonical_state,\s*canonical_district",sql)


def test_database_paths_are_read_only_and_final_production_eligibility_zero():
    script=SCRIPT.read_text(encoding="utf-8").lower()
    evaluator=(ROOT/"backend/scripts/evaluate_zip_source_member_readiness.py").read_text(encoding="utf-8").lower()
    assert "inspect_members_read_only" in script
    assert "set transaction read only" in evaluator and "default_transaction_read_only" in evaluator
    for statement in ("insert into","delete from","truncate ","drop table","copy ",".commit("):
        assert statement not in script
    assert '"production_auto_select_eligible_count":0' in script


def test_current_member_false_detail_is_rejected():
    payload=json.loads(FIXTURE.read_text(encoding="utf-8")); payload["member"]["currentMember"]=False
    with pytest.raises(metadata.SourceContractError,match="current-list/detail disagreement"):parse_detail(payload)


def test_manifest_replay_checksum_orphan_and_stale_failures():
    batch,rows=make_valid_replay_batch()
    assert metadata.load_retrieval_batch(batch,today=date(2026,7,12))[0]["replay_completeness"]["detail_set_exact"] is True
    (batch/"orphan.json").write_text("{}",encoding="utf-8")
    with pytest.raises(metadata.SourceContractError,match="orphan"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))
    (batch/"orphan.json").unlink(); artifact=batch/"congress_119_current_000.json"; artifact.write_text("tampered",encoding="utf-8")
    with pytest.raises(metadata.SourceContractError,match="integrity"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))
    make_valid_replay_batch()
    with pytest.raises(metadata.SourceContractError,match="stale"):metadata.load_retrieval_batch(batch,today=date(2026,7,25))


def test_replay_rejects_omitted_detail_even_with_self_consistent_manifest():
    batch,rows=make_valid_replay_batch(); (batch/"member_details/A000001.json").unlink(); rows=[row for row in rows if row["path"]!="member_details/A000001.json"]; write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="detail artifact set mismatch"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))


def test_replay_rejects_extra_detail_and_wrong_filename_bioguide():
    batch,rows=make_valid_replay_batch(); extra=batch/"member_details/B000002.json"; extra.write_text(json.dumps({"member":{"bioguideId":"B000002"}}),encoding="utf-8"); rows.append(replay_row(batch,"member_details/B000002.json",metadata.detail_url("B000002"))); write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="detail artifact set mismatch"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))
    shutil.rmtree(CASES); batch,rows=make_valid_replay_batch(); detail=batch/"member_details/A000001.json"; detail.write_text(json.dumps({"member":{"bioguideId":"B000002"}}),encoding="utf-8"); rows=[replay_row(batch,row["path"],row["source"]) if row["path"]=="member_details/A000001.json" else row for row in rows]; write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="Bioguide ID disagrees"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))


def test_replay_rejects_missing_page_incorrect_offset_non_success_and_unexpected_url():
    batch,rows=make_valid_replay_batch(); (batch/"congress_119_current_250.json").unlink(); rows=[row for row in rows if row["path"]!="congress_119_current_250.json"]; write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="missing Congress list page"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))
    shutil.rmtree(CASES); batch,rows=make_valid_replay_batch(); first=batch/"congress_119_current_000.json"; payload=json.loads(first.read_text()); payload["pagination"]["next"]=metadata.list_url(500); first.write_text(json.dumps(payload)); rows=[replay_row(batch,row["path"],row["source"]) if row["path"]==first.name else row for row in rows]; write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="incorrect Congress pagination offset"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))
    shutil.rmtree(CASES); batch,rows=make_valid_replay_batch(); rows[0]["response_status"]=500; write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="non-success HTTP status"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))
    shutil.rmtree(CASES); batch,rows=make_valid_replay_batch(); next(row for row in rows if row["path"]=="house_representatives.html")["source"]="https://example.gov/unexpected"; write_replay_manifest(batch,rows)
    with pytest.raises(metadata.SourceContractError,match="required official artifact"):metadata.load_retrieval_batch(batch,today=date(2026,7,12))


def test_house_same_seat_wrong_member_is_primary_only():
    member={"canonical_state":"NC","canonical_district":"04","member_type":"voting_representative","name":"Alice One","official_url":"https://alice.house.gov"}
    house={"canonical_state":"NC","canonical_district":"04","vacant":False,"seat_type":"voting_district","displayed_member_name":"Bob Two","member_domain":"bob.house.gov"}
    assert metadata.reconcile_seats([member],[house],[])[("NC","04")]=="current_primary_source_only"


def test_exact_house_seat_universe_and_missing_delegate_failure():
    records=[]
    for i in range(435):records.append({"seat_type":"voting_district"})
    records += [{"seat_type":"delegate"} for _ in range(5)] + [{"seat_type":"resident_commissioner"}]
    assert metadata.validate_house_seat_universe(records)["total"]==441
    with pytest.raises(metadata.SourceContractError):metadata.validate_house_seat_universe(records[:-1])


def test_clerk_entry_scoping_prevents_later_oath_from_resolving_prior_entry():
    html='<h1>Vacancies of the 119th Congress</h1><li class="vacancy_release"><a href="/members/TX23/vacancy">TX</a> Resigned April 14, 2026 <a href="/members/NC04/vacancy">NC</a> Sworn in May 1, 2026'
    rows=metadata.parse_clerk_vacancies(html)
    assert rows[0]["active"] is True and rows[0]["vacancy_effective_date"]=="2026-04-14"
    assert rows[1]["active"] is False and rows[1]["oath_date"]=="2026-05-01"


def test_normalized_previews_map_exactly_to_schema_and_lineage_targets():
    artifacts=[]
    for rel,source in (("congress_119_current_000.json",metadata.list_url(0)),("member_details/A000001.json",metadata.detail_url("A000001")),("house_representatives.html",metadata.HOUSE_DIRECTORY_URL),("clerk_vacancies.html",metadata.CLERK_VACANCIES_URL)):
        artifacts.append({"path":rel,"source":source,"response_status":200,"retrieved_at":"2026-07-12T01:00:00+00:00","size_bytes":1,"sha256":"a"*64,"retry_count":0})
    manifest={"snapshot_id":"s1","retrieval_started_at":"2026-07-12T00:00:00+00:00","retrieval_completed_at":"2026-07-12T01:00:00+00:00","parser_version":metadata.PARSER_VERSION,"artifacts":artifacts}
    member={"bioguide_id":"A000001","congress":119,"chamber":"house","canonical_state":"NC","canonical_district":"04","source_state":"NC","source_district":"4","normalization_rule":"house_member_district_v1","member_type":"voting_representative","current_member":True,"service_start_year":2025,"service_end_year":None,"service_date_precision":"year","party":"D","official_url":"https://sample.house.gov","source_name":"Congress.gov API","source_type":"official_api","source_url":metadata.detail_url("A000001"),"source_update_date":"2026-07-12","source_retrieved_at":"2026-07-12","source_checksum":"b"*64,"parser_version":metadata.PARSER_VERSION}
    house=[{"canonical_state":"NC","canonical_district":"04","source_state":"NC","source_district":"04","seat_type":"voting_district"},{"canonical_state":"CA","canonical_district":"14","source_state":"CA","source_district":"14","seat_type":"voting_district"}]
    clerk=[{"canonical_state":"CA","canonical_district":"14","vacancy_reason":"resigned","vacancy_effective_date":"2026-04-14","special_election_type":"special_general","special_election_date":"2026-08-18","successor_name":None,"succession_date":None,"oath_date":None}]
    statuses={("NC","04"):"current_cross_source_confirmed",("CA","14"):"vacant_officially_confirmed"}
    previews=metadata.build_seed_previews(manifest=manifest,manifest_checksum="c"*64,members=[member],house_records=house,clerk_events=clerk,statuses=statuses,production_rows=[{"id":42,"bioguide_id":"A000001"}])
    result=metadata.validate_seed_previews(previews,migration_sql=MIGRATION.read_text(encoding="utf-8"))
    assert result=={"passed":True,"errors":[],"unmatched_member_rows":[],"noninsertable_preview_rows":0}
    assert set(previews["normalized_member_service.json"][0])==metadata.MEMBER_PREVIEW_COLUMNS
    ca=next(row for row in previews["normalized_seat_status.json"] if row["canonical_state"]=="CA")
    assert ca["seat_status"]=="vacant" and ca["metadata_currentness"]=="vacant_officially_confirmed"
    assert ca["current_legislator_id"] is None and ca["special_election_date"]=="2026-08-18"
    assert len(previews["normalized_member_service_evidence_artifacts.json"])==2
    assert len(previews["normalized_seat_status_evidence_artifacts.json"])==4
    changed_sql=MIGRATION.read_text(encoding="utf-8").replace("special_election_date DATE","successor_election_date DATE")
    with pytest.raises(metadata.SourceContractError,match="does not map exactly to migration table"):
        metadata.validate_seed_previews(previews,migration_sql=changed_sql)
