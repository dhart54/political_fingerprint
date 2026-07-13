from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from backend.app.etl.current_house_member_metadata import *

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
readiness=load("readiness",ROOT/"backend/scripts/evaluate_zip_source_member_readiness.py"); zips=load("zips",ROOT/"backend/scripts/dry_run_zip_source_import.py")
OUT=ROOT/"docs/review_packets/current_house_member_metadata_hardening_v1.json"; MD=OUT.with_suffix(".md"); MAN=ROOT/"docs/source_manifests/current_house_member_metadata_sources_v1.json"

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); p.add_argument("--read-only",action="store_true"); p.add_argument("--retrieve-official",action="store_true"); p.add_argument("--source-dir",type=Path,required=True); p.add_argument("--zip-source",type=Path,required=True); p.add_argument("--env-path",type=Path,default=ROOT/"backend/.env"); p.add_argument("--output",type=Path,default=OUT); p.add_argument("--markdown-output",type=Path,default=MD); p.add_argument("--manifest-output",type=Path,default=MAN); a=p.parse_args(argv)
    if not a.dry_run or not a.read_only:return 2
    try:
        report,manifest=build(a)
        for path,payload in ((a.output,json.dumps(report,indent=2,sort_keys=True)+"\n"),(a.markdown_output,render(report)),(a.manifest_output,json.dumps(manifest,indent=2,sort_keys=True)+"\n")):path.parent.mkdir(parents=True,exist_ok=True); path.write_text(payload,encoding="utf-8")
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); return 2
    print(json.dumps({"snapshot_id":report["snapshot"]["snapshot_id"],"ready_pairs":report["readiness_impact"]["source_to_member_ready_pair_count"],"production_auto_select_eligible_count":0},sort_keys=True)); return 0

def build(a):
    env=dotenv_values(a.env_path); key=env.get("CONGRESS_API_KEY"); db_url=env.get("DATABASE_URL"); batch=a.source_dir; mode="live_retrieval" if a.retrieve_official else "local_replay"
    if a.retrieve_official:
        if not key:raise SourceContractError("blocked_no_api_key")
        got=retrieve_official(api_key=str(key),output_dir=a.source_dir); first=got[0].path; batch=first.parent.parent if first.parent.name=="member_details" else first.parent
    if not db_url:raise SourceContractError("DATABASE_URL missing")
    utc_today=datetime.now(timezone.utc).date(); rm,retrieved_on=load_retrieval_batch(batch,today=utc_today); sid=rm["snapshot_id"]; allowed={Path(x).name for x in rm["artifact_allowlist"] if x.startswith("member_details/")}
    members=parse_congress_details(batch/"member_details",retrieved_on=retrieved_on,allowed_files=allowed); house=parse_house_directory((batch/"house_representatives.html").read_text(encoding="utf-8")); clerk=parse_clerk_vacancies((batch/"clerk_vacancies.html").read_text(encoding="utf-8")); universe=validate_house_seat_universe(house)
    db=readiness.inspect_members_read_only(str(db_url)); proposed=inspect_proposed_tables(str(db_url)); repo=readiness.inspect_repository_state(ROOT); readiness.ensure_repository_state_safe(repo)
    if any(proposed.values()):raise SourceContractError("proposed migration tables already exist")
    by_seat={}
    for row in members:by_seat.setdefault((row["canonical_state"],row["canonical_district"]),[]).append(row)
    duplicate_seats={f"{k[0]}-{k[1]}":len(v) for k,v in by_seat.items() if len(v)>1}; statuses=reconcile_seats(members,house,clerk); conflicts=[f"{k[0]}-{k[1]}" for k,v in statuses.items() if v=="source_conflict"]
    official_dupes=dupes([r["bioguide_id"] for r in members]); production_dupes=dupes([str(r["bioguide_id"]) for r in db["member_rows"] if r.get("bioguide_id")]);
    if official_dupes:raise SourceContractError(f"duplicate official identities: {official_dupes}")
    official_ids={r["bioguide_id"] for r in members}; prod_ids={str(r["bioguide_id"]) for r in db["member_rows"] if r.get("bioguide_id")}; current=[r for r in db["member_rows"] if r.get("chamber")=="house" and r.get("in_office") is True]; current_ids={str(r["bioguide_id"]) for r in current}; vacant={k for k,v in statuses.items() if v=="vacant_officially_confirmed"}
    vacancy_conf=[{"bioguide_id":r.get("bioguide_id"),"seat":f"{r.get('state')}-{str(r.get('district')).zfill(2)}"} for r in current if (str(r.get("state")),str(r.get("district")).zfill(2)) in vacant]
    different=[]
    for r in current:
        seat=(str(r.get("state")),str(r.get("district")).zfill(2)); candidate=by_seat.get(seat,[])
        if len(candidate)==1 and candidate[0]["bioguide_id"]!=r.get("bioguide_id") and seat not in vacant:different.append({"seat":f"{seat[0]}-{seat[1]}","production":r.get("bioguide_id"),"official":candidate[0]["bioguide_id"]})
    zi=zips.inspect_official_file_identity(a.zip_source)
    if not zi["official_file_identity_verified"]:raise SourceContractError("ZIP identity failed")
    raw=zips.read_source_rows(a.zip_source); norm=[zips.normalize_row(r,line_number=i+2) for i,r in enumerate(raw)]; accepted=[r for r in norm if not r["rejected"]]; groups=zips.group_accepted_rows_by_zip(accepted); candidates=zips.source_only_future_auto_select_candidates(groups); pairs={(r["state"],r["district"]) for r in accepted}
    canon=lambda pair:("DC","00") if pair==("DC","98") else pair
    ready={p for p in pairs if statuses.get(canon(p))=="current_cross_source_confirmed" and by_seat.get(canon(p),[{}])[0].get("member_type")=="voting_representative"}; ready_z=sum(canon((groups[z][0]["state"],groups[z][0]["district"])) in {canon(p) for p in ready} for z in candidates)
    previews={"normalized_member_service.json":[{"snapshot_id":sid,"source_artifact":f"member_details/{r['bioguide_id']}.json",**r} for r in sorted(members,key=lambda x:x["bioguide_id"])],"normalized_seat_status.json":[{"snapshot_id":sid,"canonical_state":k[0],"canonical_district":k[1],"status":v,"supporting_artifacts":["house_representatives.html","clerk_vacancies.html"]} for k,v in sorted(statuses.items())]}; preview_meta=[]
    for name,payload in previews.items():
        path=batch/name; path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8"); preview_meta.append({"path":name,"size_bytes":path.stat().st_size,"sha256":sha256_file(path)})
    rm["normalized_previews"]=preview_meta; mp=batch/"retrieval_manifest.json"; mp.write_text(json.dumps(rm,indent=2,sort_keys=True)+"\n",encoding="utf-8"); mch=sha256_file(mp)
    summary={"house_seat_universe":universe,"current_voting_representatives":sum(r["member_type"]=="voting_representative" for r in members),"delegates":sum(r["member_type"]=="delegate" for r in members),"resident_commissioners":sum(r["member_type"]=="resident_commissioner" for r in members),"identity_confirmed_member_count":sum(v=="current_cross_source_confirmed" for v in statuses.values()),"primary_source_only_count":sum(v=="current_primary_source_only" for v in statuses.values()),"source_conflicts":len(conflicts),"active_vacancies":sum(e["active"] for e in clerk),"resolved_vacancies":sum(not e["active"] for e in clerk),"current_member_false_count":0,"current_list_detail_disagreement_count":0,"official_duplicate_bioguide_count":len(official_dupes),"production_duplicate_bioguide_count":len(production_dupes)}
    reconciliation={"exact_bioguide_matches":len(official_ids&prod_ids),"official_members_unmatched_to_production":sorted(official_ids-prod_ids),"production_in_office_absent_from_official":sorted(current_ids-official_ids),"production_current_rows_on_officially_vacant_seats":vacancy_conf,"production_current_rows_contradicted_by_different_member":different,"production_rows_missing_bioguide":sum(not r.get("bioguide_id") for r in db["member_rows"]),"official_duplicate_bioguide_ids":official_dupes,"production_duplicate_bioguide_ids":production_dupes}
    report={"schema_version":"current_house_member_metadata_hardening_v1","snapshot":{"snapshot_id":sid,"authoritative_retrieval_timestamp":rm["retrieval_completed_at"],"snapshot_age_days":(date.today()-retrieved_on).days,"fresh":True,"manifest_checksum":mch,"normalized_previews":preview_meta},"source_retrieval":{"mode":mode,"api_key_present":bool(key),"artifact_count":len(rm["artifacts"]),"artifact_provenance_complete":True,"current_member_false_count":0,"current_list_detail_disagreement_count":0},"summary":summary,"vacancy_records":clerk,"production_reconciliation":reconciliation,"dc_normalization":{"source_district":"98","canonical_district":"00","rule":"dc_census_98_to_house_delegate_00_v1","auto_select_blocked":True},"proposed_schema":{"migration":"backend/migrations/0014_house_member_service_and_seat_status.sql","migration_applied":False,"table_existence":proposed,"snapshot_tables":["house_member_metadata_snapshots","house_member_metadata_snapshot_artifacts"],"rollback_key":"snapshot_id"},"readiness_impact":{"source_to_member_ready_pair_count":len(ready),"source_to_member_ready_candidate_zcta_count":ready_z,"production_auto_select_eligible_count":0},"verification":{"database_read_only":True,"zip_district_mappings":db["zip_district_mappings"],"route_state":repo["route_state"],"feature_flag":repo["feature_flag"]},"safety":{"database_write_occurred":False,"migration_applied":False,"production_auto_select_enabled":False}}
    report["snapshot"]["snapshot_age_days"]=(utc_today-retrieved_on).days
    manifest={"schema_version":"current_house_member_metadata_sources_v1","decision":"approved_for_bounded_dry_run_only","api_key_present":bool(key),"snapshot":report["snapshot"],"retrieval_batch":{k:v for k,v in rm.items() if k!="artifacts"},"artifact_count":len(rm["artifacts"]),"artifacts":rm["artifacts"]}
    return report,manifest

def dupes(values):
    counts=Counter(values); return sorted(v for v,c in counts.items() if c>1)

def inspect_proposed_tables(db_url):
    import psycopg
    from psycopg.rows import dict_row
    names=("house_member_metadata_snapshots","house_member_metadata_snapshot_artifacts","house_member_service_evidence","house_seat_status_evidence")
    with psycopg.connect(db_url,row_factory=dict_row,autocommit=True) as conn:
        conn.execute("SET default_transaction_read_only=on")
        with conn.transaction():conn.execute("SET TRANSACTION READ ONLY"); rows=conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",(list(names),)).fetchall()
    present={r["table_name"] for r in rows}; return {n:n in present for n in names}

def render(r):
    s=r["summary"]; q=r["production_reconciliation"]; v=r["vacancy_records"]; return "\n".join(["# Current House Member Metadata Hardening V1","",f"- Snapshot: `{r['snapshot']['snapshot_id']}`",f"- Retrieval timestamp: `{r['snapshot']['authoritative_retrieval_timestamp']}`",f"- Fresh: `{r['snapshot']['fresh']}`",f"- Seat universe: `{json.dumps(s['house_seat_universe'],sort_keys=True)}`",f"- Identity confirmed: `{s['identity_confirmed_member_count']}`",f"- Primary source only: `{s['primary_source_only_count']}`",f"- Active/resolved vacancies: `{s['active_vacancies']}` / `{s['resolved_vacancies']}`",f"- Vacancy records: `{json.dumps(v,sort_keys=True)}`",f"- Vacancy contradictions: `{json.dumps(q['production_current_rows_on_officially_vacant_seats'],sort_keys=True)}`",f"- Ready pairs/ZCTAs: `{r['readiness_impact']['source_to_member_ready_pair_count']}` / `{r['readiness_impact']['source_to_member_ready_candidate_zcta_count']}`","- Production auto-select: `0`","- Migration applied: `False`",""])

if __name__=="__main__":raise SystemExit(main())
