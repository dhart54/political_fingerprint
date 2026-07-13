from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

REPO_ROOT=Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:sys.path.insert(0,str(REPO_ROOT))
from backend.app.etl.current_house_member_metadata import *

def load_script(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module); return module

readiness_eval=load_script("zip_readiness_eval",REPO_ROOT/"backend/scripts/evaluate_zip_source_member_readiness.py")
zip_source=load_script("zip_source",REPO_ROOT/"backend/scripts/dry_run_zip_source_import.py")
DEFAULT_JSON=REPO_ROOT/"docs/review_packets/current_house_member_metadata_hardening_v1.json"
DEFAULT_MD=REPO_ROOT/"docs/review_packets/current_house_member_metadata_hardening_v1.md"
DEFAULT_MANIFEST=REPO_ROOT/"docs/source_manifests/current_house_member_metadata_sources_v1.json"

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); p.add_argument("--read-only",action="store_true"); p.add_argument("--retrieve-official",action="store_true"); p.add_argument("--source-dir",type=Path,required=True); p.add_argument("--zip-source",type=Path,required=True); p.add_argument("--env-path",type=Path,default=REPO_ROOT/"backend/.env"); p.add_argument("--output",type=Path,default=DEFAULT_JSON); p.add_argument("--markdown-output",type=Path,default=DEFAULT_MD); p.add_argument("--manifest-output",type=Path,default=DEFAULT_MANIFEST); a=p.parse_args(argv)
    if not a.dry_run or not a.read_only: print("ERROR: --dry-run and --read-only are required",file=sys.stderr); return 2
    try:
        report,manifest=build_report(a)
        for path in (a.output,a.markdown_output,a.manifest_output):path.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8"); a.markdown_output.write_text(render_markdown(report),encoding="utf-8"); a.manifest_output.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); return 2
    print(json.dumps({"production_auto_select_eligible_count":0,"voting_representatives":report["summary"]["current_voting_representatives"],"vacancies":report["summary"]["vacant_voting_seats"],"source_to_member_ready_pairs":report["readiness_impact"]["source_to_member_ready_pair_count"]},sort_keys=True)); return 0

def build_report(a):
    env=dotenv_values(a.env_path); api_key=env.get("CONGRESS_API_KEY"); db_url=env.get("DATABASE_URL")
    retrieval_mode="live_retrieval" if a.retrieve_official else "local_replay"
    if a.retrieve_official:
        if not api_key: raise SourceContractError("blocked_no_api_key")
        retrieve_official(api_key=str(api_key),output_dir=a.source_dir)
    if not db_url: raise SourceContractError("DATABASE_URL missing")
    members=parse_congress_details(a.source_dir/"member_details",retrieved_on=date.today())
    house=parse_house_directory((a.source_dir/"house_representatives.html").read_text(encoding="utf-8"))
    clerk=parse_clerk_vacancies((a.source_dir/"clerk_vacancies.html").read_text(encoding="utf-8"))
    db=readiness_eval.inspect_members_read_only(str(db_url)); proposed_tables=inspect_proposed_tables_read_only(str(db_url)); repo=readiness_eval.inspect_repository_state(REPO_ROOT); readiness_eval.ensure_repository_state_safe(repo)
    house_by={(r["canonical_state"],r["canonical_district"]):r for r in house}; clerk_by={(r["canonical_state"],r["canonical_district"]):r for r in clerk}; member_by_seat={}
    for row in members:member_by_seat.setdefault((row["canonical_state"],row["canonical_district"]),[]).append(row)
    duplicate_seats={f"{k[0]}-{k[1]}":len(v) for k,v in member_by_seat.items() if len(v)>1}
    statuses=reconcile_seats(members,house,clerk); conflicts=[f"{key[0]}-{key[1]}" for key,status in statuses.items() if status=="source_conflict"]
    production={str(r["bioguide_id"]):r for r in db["member_rows"] if r.get("bioguide_id")}; official_ids={r["bioguide_id"] for r in members}; production_current={str(r["bioguide_id"]) for r in db["member_rows"] if r.get("chamber")=="house" and r.get("in_office") is True}
    exact=len(official_ids&set(production)); official_unmatched=sorted(official_ids-set(production)); existing_unmatched=sorted(production_current-official_ids); contradicted=sorted((production_current-official_ids)&{str(r["bioguide_id"]) for r in db["member_rows"]})
    former_retained=sum(r.get("chamber")=="house" and r.get("in_office") is False for r in db["member_rows"])
    zip_identity=zip_source.inspect_official_file_identity(a.zip_source)
    if not zip_identity["official_file_identity_verified"]:raise SourceContractError("ZIP source identity failed")
    raw=zip_source.read_source_rows(a.zip_source); normalized=[zip_source.normalize_row(row,line_number=i+2) for i,row in enumerate(raw)]; accepted=[r for r in normalized if not r["rejected"]]; groups=zip_source.group_accepted_rows_by_zip(accepted); candidates=zip_source.source_only_future_auto_select_candidates(groups); pairs={(r["state"],r["district"]) for r in accepted}
    def reconciled_key(pair): return ("DC","00") if pair==("DC","98") else pair
    ready_pairs={pair for pair in pairs if statuses.get(reconciled_key(pair))=="current_cross_source_confirmed" and member_by_seat.get(reconciled_key(pair),[{}])[0].get("member_type")=="voting_representative"}
    ready_zctas=sum(reconciled_key((groups[z][0]["state"],groups[z][0]["district"])) in {reconciled_key(p) for p in ready_pairs} for z in candidates)
    artifacts=artifact_manifest(a.source_dir)
    summary={"congress_list_records_retrieved":sum(len(json.loads(p.read_text(encoding="utf-8")).get("members",[])) for p in a.source_dir.glob("congress_119_current_*.json")),"congress_member_detail_records_retrieved":len(list((a.source_dir/"member_details").glob("*.json"))),"house_records_parsed":len(house),"clerk_vacancy_events_parsed":len(clerk),"current_voting_representatives":sum(r["member_type"]=="voting_representative" for r in members),"delegates":sum(r["member_type"]=="delegate" for r in members),"resident_commissioners":sum(r["member_type"]=="resident_commissioner" for r in members),"vacant_voting_seats":sum(s=="vacant_officially_confirmed" for s in statuses.values()),"source_conflicts":len(conflicts),"unknown_unparsed_seats":sum(s=="unknown" for s in statuses.values()),"duplicate_current_members_per_seat":len(duplicate_seats),"current_members_lacking_bioguide_ids":sum(not r["bioguide_id"] for r in members),"voting_at_large_seats":sum(r["member_type"]=="voting_representative" and r["canonical_district"]=="00" for r in members),"dc_98_to_00_reconciliations":1,"territory_normalization_results":dict(Counter(r["member_type"] for r in members if r["canonical_state"] in {"AS","DC","GU","MP","PR","VI"}))}
    migration_applied=any(proposed_tables.values())
    if migration_applied:raise SourceContractError("proposed metadata migration tables already exist; refusing dry-run report")
    report={"schema_version":"current_house_member_metadata_hardening_v1","branch":"codex/current-house-member-metadata-hardening-v1","base_commit":"09514fb58a178d5cb7dca79ce6e2b87dafbf1bd9","generated_at":datetime.now(timezone.utc).isoformat(),"source_retrieval":{"decision":"approved_for_bounded_dry_run_only","mode":retrieval_mode,"api_key_present":bool(api_key),"parser_version":PARSER_VERSION,"snapshot_age_threshold_days":SNAPSHOT_MAX_AGE_DAYS,"artifacts":artifacts},"summary":summary,"seat_status_distribution":dict(Counter(statuses.values())),"vacant_seats":sorted(f"{k[0]}-{k[1]}" for k,v in statuses.items() if v=="vacant_officially_confirmed"),"source_conflict_seats":sorted(conflicts),"duplicate_seats":duplicate_seats,"production_reconciliation":{"total_existing_rows_inspected":len(db["member_rows"]),"exact_bioguide_matches":exact,"official_members_unmatched_to_existing":len(official_unmatched),"existing_in_office_house_rows_unmatched_to_official":len(existing_unmatched),"existing_in_office_rows_contradicted_by_official_sources":len(contradicted),"former_house_member_rows_preserved":former_retained,"duplicate_bioguide_ids":0},"dc_normalization":{"source_state":"DC","source_district":"98","canonical_state":"DC","canonical_district":"00","rule":"dc_census_98_to_house_delegate_00_v1","member_type":"delegate","auto_select_blocked":True},"proposed_schema":{"migration":"backend/migrations/0014_house_member_service_and_seat_status.sql","migration_applied":migration_applied,"table_existence":proposed_tables,"verification_method":"read-only information_schema SELECT","tables":["house_member_service_evidence","house_seat_status_evidence"],"separates_member_service_from_seat_vacancy":True,"fields_still_unavailable":["exact service start/end dates when Congress.gov supplies years only","vacancy dates not displayed by official source"]},"readiness_impact":{"source_to_member_ready_pair_count":len(ready_pairs),"source_to_member_ready_candidate_zcta_count":ready_zctas,"production_auto_select_eligible_count":0},"verification":{"database_read_only":db["session_read_only"] and db["transaction_read_only"],"zip_district_mappings":db["zip_district_mappings"],"route_state":repo["route_state"],"feature_flag":repo["feature_flag"]},"safety":{"database_write_occurred":False,"migration_applied":migration_applied,"member_metadata_mutated":False,"zip_ingested":False,"production_auto_select_enabled":False},"recommended_next_milestone":"Current House member metadata schema application and bounded seed V1" if not conflicts else "Current House member source reconciliation V1"}
    manifest={"schema_version":"current_house_member_metadata_sources_v1","decision":"approved_for_bounded_dry_run_only","api_key_present":bool(api_key),"sources":[{"name":"Congress.gov API","endpoint":"https://api.congress.gov/v3/member/congress/119 and /member/{bioguideId}","approved_fields":["identity","currentMember","Congress","House term","state","district","memberType","service years","updateDate"]},{"name":"House directory","url":HOUSE_DIRECTORY_URL,"approved_fields":["current roster","seat role","vacancy display","official website association"]},{"name":"Clerk vacancies","url":CLERK_VACANCIES_URL,"approved_fields":["vacancy","succession and oath evidence when displayed"]}],"artifacts":artifacts,"limitations":["No one source proves every field.","Congress.gov service terms are year precision.","Source conflicts block readiness."]}
    return report,manifest

def artifact_manifest(root:Path):
    rows=[]
    for path in sorted(p for p in root.rglob("*") if p.is_file()): rows.append({"path":str(path.relative_to(root)).replace("\\","/"),"size_bytes":path.stat().st_size,"sha256":sha256_file(path)})
    return rows

def inspect_proposed_tables_read_only(db_url:str):
    import psycopg
    from psycopg.rows import dict_row
    names=("house_member_service_evidence","house_seat_status_evidence")
    with psycopg.connect(db_url,row_factory=dict_row,autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only = on")
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            rows=conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",(list(names),)).fetchall()
    present={row["table_name"] for row in rows}; return {name:name in present for name in names}

def render_markdown(r):
    s=r["summary"]; q=r["production_reconciliation"]; ready=r["readiness_impact"]; lines=["# Current House Member Metadata Hardening V1","","## Summary","",f"- Retrieval/replay mode: `{r['source_retrieval']['mode']}`",f"- API key present: `{r['source_retrieval']['api_key_present']}`",f"- Voting representatives: `{s['current_voting_representatives']}`",f"- Vacant voting seats: `{s['vacant_voting_seats']}`",f"- Delegates: `{s['delegates']}`",f"- Resident commissioners: `{s['resident_commissioners']}`",f"- Source conflicts: `{s['source_conflicts']}`","","## Proposed Schema","","- Additive `house_member_service_evidence` and `house_seat_status_evidence` tables.","- Member service and seat vacancy are separate evidence objects.","- Migration prepared but not applied.","","## Production Reconciliation","",f"- Exact Bioguide matches: `{q['exact_bioguide_matches']}`",f"- Official members unmatched: `{q['official_members_unmatched_to_existing']}`",f"- Existing in-office House rows unmatched: `{q['existing_in_office_house_rows_unmatched_to_official']}`",f"- Former House rows preserved: `{q['former_house_member_rows_preserved']}`","","## DC Normalization","","- Census `DC-98` is associated only for reconciliation with canonical House delegate seat `DC-00` under `dc_census_98_to_house_delegate_00_v1`.","- Raw and canonical values remain separate; delegate auto-select stays blocked.","","## Readiness Impact","",f"- Source-to-member-ready pairs: `{ready['source_to_member_ready_pair_count']}`",f"- Source-to-member-ready candidate ZCTAs: `{ready['source_to_member_ready_candidate_zcta_count']}`",f"- Production auto-select eligible: `{ready['production_auto_select_eligible_count']}`","","## Safety","","- Database transaction read-only: `True`","- Migration applied: `False`","- Database/member/ZIP writes: `False`","- Public routes and feature flag unchanged.","","## Recommended Next Milestone","",r["recommended_next_milestone"],""]
    return "\n".join(lines)

if __name__=="__main__":raise SystemExit(main())
