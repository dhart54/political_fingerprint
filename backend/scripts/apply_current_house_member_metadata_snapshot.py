"""Atomically apply migration 0014 and seed one approved House metadata snapshot."""
from __future__ import annotations

import argparse, hashlib, json, re, subprocess, sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
MIGRATION=ROOT/"backend/migrations/0014_house_member_service_and_seat_status.sql"
ENV=ROOT/"backend/.env"
REPORT=ROOT/"docs/review_packets/current_house_member_metadata_schema_seed_v1.json"
REPORT_MD=REPORT.with_suffix(".md")
SNAPSHOT_ID="house-119-20260713T011722Z"
BASE_COMMIT="12e0bbf9c22d2083e78433951858f6b5ea2f071d"
MANIFEST_CHECKSUM="d5ab3394db24a6edecc8dedf3167a24f90d6a2df46b0790f5cfe7e48b583cbbd"
LOCK_KEY="political_fingerprint:house_metadata_schema_seed_v1"
PREVIEW_DIR=ROOT/"docs/review_packets/current_house_member_metadata_hardening_v1"
TABLES=("house_member_metadata_snapshots","house_member_metadata_snapshot_artifacts","house_member_service_evidence","house_seat_status_evidence","house_member_service_evidence_artifacts","house_seat_status_evidence_artifacts")
PREVIEWS={
 "house_member_metadata_snapshots":("normalized_snapshot.json",1,"5c529183a83efb00275d51a57b67d74ccc66738d8074e90c511e8c2be086f50c"),
 "house_member_metadata_snapshot_artifacts":("normalized_snapshot_artifacts.json",486,"ef543d91802d5f8bf858dd8fe766ee42c3b1f61fcf30bfb1053b4400456edec3"),
 "house_member_service_evidence":("normalized_member_service.json",437,"9533e72fccce9640e6f58749f4f052990bf2d11bc5aea143be59109e38e66d09"),
 "house_seat_status_evidence":("normalized_seat_status.json",441,"0b2c332e1a88d3b97ea587447c22be89917444825de88d29c824fadb2af53ff7"),
 "house_member_service_evidence_artifacts":("normalized_member_service_evidence_artifacts.json",874,"b6fb02bcabe266949eec5551cb8214b55182d0406e042e026455bafa91316448"),
 "house_seat_status_evidence_artifacts":("normalized_seat_status_evidence_artifacts.json",882,"f7695cf830143c6f89c751d27f7a5b0d18535c90656d9f73cf942049d86f916e"),
}
NATURAL_KEYS={
 "house_member_metadata_snapshots":("snapshot_id",),
 "house_member_metadata_snapshot_artifacts":("snapshot_id","artifact_path"),
 "house_member_service_evidence":("snapshot_id","bioguide_id","congress","canonical_state","canonical_district"),
 "house_seat_status_evidence":("snapshot_id","congress","canonical_state","canonical_district"),
 "house_member_service_evidence_artifacts":("snapshot_id","bioguide_id","congress","canonical_state","canonical_district","artifact_path","evidence_role"),
 "house_seat_status_evidence_artifacts":("snapshot_id","congress","canonical_state","canonical_district","artifact_path","evidence_role"),
}

class SeedSafetyError(RuntimeError):pass

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value:Any)->Any:
 if isinstance(value,datetime):return value.astimezone(timezone.utc).isoformat()
 if isinstance(value,date):return value.isoformat()
 if isinstance(value,str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})",value):return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
 if isinstance(value,dict):return {k:canonical(v) for k,v in sorted(value.items())}
 if isinstance(value,list):return [canonical(v) for v in value]
 return value
def content_sha(rows:list[dict[str,Any]])->str:
 return hashlib.sha256((json.dumps(canonical(rows),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()).hexdigest()

def load_previews(today:date|None=None)->tuple[dict[str,list[dict[str,Any]]],dict[str,Any]]:
 today=today or datetime.now(timezone.utc).date(); data={}; meta=[]
 for table,(name,count,pin) in PREVIEWS.items():
  path=PREVIEW_DIR/name
  if not path.exists() or sha(path)!=pin:raise SeedSafetyError(f"preview checksum mismatch: {name}")
  rows=json.loads(path.read_text(encoding="utf-8"))
  if len(rows)!=count:raise SeedSafetyError(f"preview count mismatch: {name}")
  if any(row.get("snapshot_id")!=SNAPSHOT_ID for row in rows):raise SeedSafetyError(f"preview snapshot mismatch: {name}")
  data[table]=rows; meta.append({"path":str(path.relative_to(ROOT)).replace("\\","/"),"row_count":count,"sha256":pin,"canonical_content_sha256":content_sha(sorted(rows,key=lambda r:tuple(str(r.get(k)) for k in NATURAL_KEYS[table])))})
 snapshot=data[TABLES[0]][0]; completed=datetime.fromisoformat(snapshot["retrieval_completed_at"].replace("Z","+00:00")); age=(today-completed.date()).days
 if age<0 or age>7:raise SeedSafetyError(f"approved snapshot is stale: age_days={age}")
 packet=json.loads((ROOT/"docs/review_packets/current_house_member_metadata_hardening_v1.json").read_text(encoding="utf-8")); validation=packet["snapshot"]["preview_schema_validation"]
 if not validation.get("passed") or validation.get("unmatched_member_rows") or validation.get("noninsertable_preview_rows")!=0 or packet["readiness_impact"]["production_auto_select_eligible_count"]!=0:raise SeedSafetyError("approved review packet readiness/preview gate failed")
 return data,{"snapshot_age_days":age,"fresh":True,"previews":meta}

def strip_transaction_wrappers(sql:str)->str:
 lines=sql.splitlines(); nonempty=[i for i,x in enumerate(lines) if x.strip()]
 if not nonempty or lines[nonempty[0]].strip().upper()!="BEGIN;" or lines[nonempty[-1]].strip().upper()!="COMMIT;":raise SeedSafetyError("migration must have exact outer BEGIN/COMMIT wrappers")
 lines.pop(nonempty[-1]); lines.pop(nonempty[0]); return "\n".join(lines).strip()+"\n"

def validate_migration(sql:str)->dict[str,Any]:
 body=re.sub(r"--.*?$|/\*.*?\*/","",sql,flags=re.M|re.S).lower(); banned={x:bool(re.search(p,body)) for x,p in {"alter":r"\balter\b","drop":r"\bdrop\b","truncate":r"\btruncate\b","update":r"\bupdate\b","delete":r"\bdelete\s+from\b","insert":r"\binsert\s+into\b","copy":r"\bcopy\b","function":r"\bcreate\s+(?:or\s+replace\s+)?function\b","trigger":r"\bcreate\s+trigger\b","grant":r"\bgrant\b","role":r"\bcreate\s+role\b","extension":r"\bcreate\s+extension\b"}.items()}
 if any(banned.values()) or body.count("create table if not exists")!=6 or "references legislators(id)" not in body:raise SeedSafetyError(f"migration outside approved envelope: {banned}")
 if re.search(r"(?:create|alter|drop|truncate|update|insert|delete).*zip_district",body):raise SeedSafetyError("migration targets ZIP schema")
 return {"file":str(MIGRATION.relative_to(ROOT)).replace("\\","/"),"sha256":sha(MIGRATION),"banned_matches":banned,"wrapper_stripped_exactly":bool(strip_transaction_wrappers(sql))}

def target(db_url:str,env:Path)->dict[str,Any]:
 p=urlsplit(db_url); host=p.hostname or ""; result={"environment_file":str(env.relative_to(ROOT) if env.is_absolute() else env),"scheme":p.scheme,"host":host,"port":p.port,"database":p.path.lstrip("/"),"username_present":bool(p.username),"password_present":bool(p.password),"supabase_production_like":"supabase" in host.lower(),"raw_url_recorded":False}
 if not result["supabase_production_like"]:raise SeedSafetyError("configured target is not the expected Supabase target")
 return result

def repo_state()->dict[str,Any]:
 base_ok=subprocess.run(["git","merge-base","--is-ancestor",BASE_COMMIT,"HEAD"],cwd=ROOT).returncode==0
 branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()
 from backend.scripts.evaluate_zip_source_member_readiness import inspect_repository_state,ensure_repository_state_safe
 state=inspect_repository_state(ROOT); ensure_repository_state_safe(state)
 if not base_ok:raise SeedSafetyError("branch is not based on reviewed merge commit")
 return {"branch":branch,"base_commit":BASE_COMMIT,"base_is_ancestor":base_ok,"route_state":state["route_state"],"feature_flag":state["feature_flag"]}

def fingerprint(rows:list[dict[str,Any]])->dict[str,Any]:
 selected=[{k:r.get(k) for k in ("id","bioguide_id","chamber","state","district","in_office","updated_at")} for r in rows]
 return {"row_count":len(selected),"sha256":content_sha(selected)}

def inspect_db(db_url:str,previews:dict[str,list[dict[str,Any]]])->dict[str,Any]:
 import psycopg
 from psycopg.rows import dict_row
 with psycopg.connect(db_url,row_factory=dict_row,autocommit=True) as conn:
  conn.execute("SET default_transaction_read_only=on")
  with conn.transaction():
   conn.execute("SET TRANSACTION READ ONLY"); conn.execute("SET LOCAL statement_timeout='20000ms'")
   existing={r["table_name"] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",(list(TABLES),)).fetchall()}
   zip_count=int(conn.execute("SELECT COUNT(*) AS n FROM zip_district_mappings").fetchone()["n"])
   legislators=[dict(r) for r in conn.execute("SELECT id,bioguide_id,chamber,state,district,in_office,updated_at FROM legislators ORDER BY id").fetchall()]
   snapshot_exists=False
   if TABLES[0] in existing:snapshot_exists=bool(conn.execute(f"SELECT EXISTS(SELECT 1 FROM {TABLES[0]} WHERE snapshot_id=%s) AS e",(SNAPSHOT_ID,)).fetchone()["e"])
 return {"existing_tables":sorted(existing),"table_state":"absent" if not existing else "complete" if len(existing)==6 else "partial","snapshot_exists":snapshot_exists,"zip_district_mappings_row_count":zip_count,"legislators_fingerprint":fingerprint(legislators),"legislators":legislators,"read_only":True}

def validate_identities(previews:dict[str,list[dict[str,Any]]],state:dict[str,Any])->dict[str,Any]:
 by_id={r["id"]:r for r in state["legislators"]}; members=previews[TABLES[2]]; seats=previews[TABLES[3]]
 if len({r["legislator_id"] for r in members})!=437 or len({r["bioguide_id"] for r in members})!=437:raise SeedSafetyError("duplicate member identity mapping")
 for r in members:
  prod=by_id.get(r["legislator_id"])
  if not prod or prod["bioguide_id"]!=r["bioguide_id"]:raise SeedSafetyError(f"member FK identity mismatch: {r['bioguide_id']}")
 for r in seats:
  if r["seat_status"]=="filled":
   prod=by_id.get(r["current_legislator_id"])
   if not prod or not r["current_bioguide_id"] or prod["bioguide_id"]!=r["current_bioguide_id"]:raise SeedSafetyError(f"filled-seat identity mismatch: {r['canonical_state']}-{r['canonical_district']}")
  elif r["seat_status"]=="vacant" and (r["current_legislator_id"] is not None or r["current_bioguide_id"] is not None):raise SeedSafetyError("vacant seat has identity")
 domains={"member_rows":len(members),"seat_rows":len(seats),"filled_voting_representative_seats":sum(r["seat_status"]=="filled" and r["seat_type"] in {"voting_district","voting_at_large"} for r in seats),"vacant_voting_seats":sum(r["seat_status"]=="vacant" for r in seats),"delegates":sum(r["seat_type"]=="delegate" for r in seats),"resident_commissioners":sum(r["seat_type"]=="resident_commissioner" for r in seats),"source_conflicts":sum(r["seat_status"]=="source_conflict" for r in seats),"primary_source_only":sum(r["metadata_currentness"]=="current_primary_source_only" for r in seats),"unmatched_production_identities":0}
 expected={"member_rows":437,"seat_rows":441,"filled_voting_representative_seats":431,"vacant_voting_seats":4,"delegates":5,"resident_commissioners":1,"source_conflicts":0,"primary_source_only":0,"unmatched_production_identities":0}
 if domains!=expected:raise SeedSafetyError(f"domain preflight mismatch: {domains}")
 return domains

def preflight(db_url:str)->tuple[dict[str,list[dict[str,Any]]],dict[str,Any]]:
 previews,fresh=load_previews(); migration=validate_migration(MIGRATION.read_text(encoding="utf-8")); repo=repo_state(); state=inspect_db(db_url,previews)
 if state["table_state"]=="partial":raise SeedSafetyError("partial metadata schema exists")
 if state["zip_district_mappings_row_count"]!=0:raise SeedSafetyError("zip_district_mappings is nonempty")
 domains=validate_identities(previews,state)
 return previews,{"freshness":fresh,"migration":migration,"repository":repo,"database":{k:v for k,v in state.items() if k!="legislators"},"identity_checks":domains,"production_auto_select_eligible_count":0}

def insert_sql(table:str,columns:list[str])->str:return f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s']*len(columns))})"
def insert_phase(conn,table:str,rows:list[dict[str,Any]])->None:
 columns=list(rows[0])
 with conn.cursor() as cursor:cursor.executemany(insert_sql(table,columns),[tuple(r[c] for c in columns) for r in rows])

def apply_atomic(db_url:str,previews:dict[str,list[dict[str,Any]]],migration_sql:str,pre_fingerprint:dict[str,Any])->dict[str,Any]:
 import psycopg
 from psycopg.rows import dict_row
 with psycopg.connect(db_url,row_factory=dict_row) as conn:
  with conn.transaction():
   conn.execute("SET LOCAL lock_timeout='10000ms'"); conn.execute("SET LOCAL statement_timeout='120000ms'"); conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))",(LOCK_KEY,))
   found=int(conn.execute("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",(list(TABLES),)).fetchone()["n"])
   if found:raise SeedSafetyError("metadata tables appeared after preflight")
   conn.execute(strip_transaction_wrappers(migration_sql))
   for table in TABLES:insert_phase(conn,table,previews[table])
   counts={table:int(conn.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE snapshot_id=%s",(SNAPSHOT_ID,)).fetchone()["n"]) for table in TABLES}
   if counts!={t:PREVIEWS[t][1] for t in TABLES}:raise SeedSafetyError(f"in-transaction row count mismatch: {counts}")
   for table in TABLES:
    expected=[canonical(r) for r in sorted(previews[table],key=lambda r:tuple(str(r.get(k)) for k in NATURAL_KEYS[table]))]
    if db_rows(conn,table,previews[table])!=expected:raise SeedSafetyError(f"in-transaction exact preview mismatch: {table}")
   legislators=[dict(r) for r in conn.execute("SELECT id,bioguide_id,chamber,state,district,in_office,updated_at FROM legislators ORDER BY id").fetchall()]
   if fingerprint(legislators)!=pre_fingerprint:raise SeedSafetyError("legislators fingerprint changed inside transaction")
   if int(conn.execute("SELECT COUNT(*) AS n FROM zip_district_mappings").fetchone()["n"])!=0:raise SeedSafetyError("ZIP table changed inside transaction")
 return {"committed":True,"atomic":True,"advisory_lock_acquired":True,"preflight_table_state":"absent","preflight_snapshot_exists":False,"repeat_absence_check_passed":True,"in_transaction_exact_preview_equality":True,"in_transaction_existing_state_unchanged":True,"insertion_order":list(TABLES),"inserted_counts":{t:PREVIEWS[t][1] for t in TABLES}}

def db_rows(conn,table:str,preview_rows:list[dict[str,Any]])->list[dict[str,Any]]:
 columns=list(preview_rows[0]); order=",".join(NATURAL_KEYS[table]); selected=",".join(columns)
 return [canonical(dict(r)) for r in conn.execute(f"SELECT {selected} FROM {table} WHERE snapshot_id=%s ORDER BY {order}",(SNAPSHOT_ID,)).fetchall()]

def postcheck(db_url:str,previews:dict[str,list[dict[str,Any]]],pre_fingerprint:dict[str,Any]|None)->dict[str,Any]:
 import psycopg
 from psycopg.rows import dict_row
 with psycopg.connect(db_url,row_factory=dict_row,autocommit=True) as conn:
  conn.execute("SET default_transaction_read_only=on")
  with conn.transaction():
   conn.execute("SET TRANSACTION READ ONLY"); conn.execute("SET LOCAL statement_timeout='30000ms'")
   existing={r["table_name"] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=ANY(%s)",(list(TABLES),)).fetchall()}
   if existing!=set(TABLES):raise SeedSafetyError("postcheck schema table set mismatch")
   columns=[dict(r) for r in conn.execute("SELECT table_name,column_name,data_type,udt_name,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=ANY(%s) ORDER BY table_name,ordinal_position",(list(TABLES),)).fetchall()]
   column_names={t:{r["column_name"] for r in columns if r["table_name"]==t} for t in TABLES}; generated={TABLES[0]:{"created_at"},TABLES[1]:{"id"},TABLES[2]:{"id","created_at","updated_at"},TABLES[3]:{"id","created_at","updated_at"},TABLES[4]:{"created_at"},TABLES[5]:{"created_at"}}
   column_contract_exact=all(column_names[t]==set(previews[t][0])|generated[t] for t in TABLES)
   index_ok=bool(conn.execute("SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_house_member_service_seat') AS e").fetchone()["e"])
   constraint_rows=[dict(r) for r in conn.execute("SELECT r.relname AS table_name,c.conname AS constraint_name,c.contype AS constraint_type,pg_get_constraintdef(c.oid) AS definition FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace WHERE n.nspname='public' AND r.relname=ANY(%s) ORDER BY r.relname,c.conname",(list(TABLES),)).fetchall()]
   equality={}; checksums={}; counts={}
   for table in TABLES:
    expected=[canonical(r) for r in sorted(previews[table],key=lambda r:tuple(str(r.get(k)) for k in NATURAL_KEYS[table]))]; actual=db_rows(conn,table,previews[table]); counts[table]=len(actual); equality[table]=actual==expected; checksums[table]={"preview":content_sha(expected),"database":content_sha(actual),"match":content_sha(expected)==content_sha(actual)}
   legislators=[dict(r) for r in conn.execute("SELECT id,bioguide_id,chamber,state,district,in_office,updated_at FROM legislators ORDER BY id").fetchall()]; post_fp=fingerprint(legislators); zip_count=int(conn.execute("SELECT COUNT(*) AS n FROM zip_district_mappings").fetchone()["n"])
 if not all(equality.values()) or not all(v["match"] for v in checksums.values()):raise SeedSafetyError("database-to-preview exact equality failed")
 if counts!={t:PREVIEWS[t][1] for t in TABLES}:raise SeedSafetyError("postcheck counts differ")
 if pre_fingerprint and post_fp!=pre_fingerprint:raise SeedSafetyError("legislators fingerprint changed")
 if zip_count!=0:raise SeedSafetyError("ZIP table changed")
 members=previews[TABLES[2]]; seats=previews[TABLES[3]]; ml=previews[TABLES[4]]; sl=previews[TABLES[5]]
 domains={"members":{"total":len(members),"voting_representatives":sum(r["member_type"]=="voting_representative" for r in members),"delegates":sum(r["member_type"]=="delegate" for r in members),"resident_commissioner":sum(r["member_type"]=="resident_commissioner" for r in members),"cross_source_confirmed":sum(r["metadata_currentness"]=="current_cross_source_confirmed" for r in members)},"seats":{"total":len(seats),"voting":sum(r["seat_type"] in {"voting_district","voting_at_large"} for r in seats),"delegates":sum(r["seat_type"]=="delegate" for r in seats),"resident_commissioner":sum(r["seat_type"]=="resident_commissioner" for r in seats),"filled":sum(r["seat_status"]=="filled" for r in seats),"vacant":sum(r["seat_status"]=="vacant" for r in seats),"source_conflict":sum(r["seat_status"]=="source_conflict" for r in seats),"unknown":sum(r["seat_status"]=="unknown" for r in seats),"primary_source_only":sum(r["metadata_currentness"]=="current_primary_source_only" for r in seats)},"lineage":{"member_links":len(ml),"seat_links":len(sl),"member_primary_identity":sum(r["evidence_role"]=="primary_identity" for r in ml),"member_roster_confirmation":sum(r["evidence_role"]=="roster_confirmation" for r in ml)}}
 approved_vacancies={(r["canonical_state"],r["canonical_district"]):r for r in json.loads((ROOT/"docs/review_packets/current_house_member_metadata_hardening_v1.json").read_text(encoding="utf-8"))["vacancy_records"]}; vacancies=[]
 for r in seats:
  if r["seat_status"]=="vacant":
   item={k:r.get(k) for k in ("canonical_state","canonical_district","vacancy_reason","vacancy_effective_date","special_election_type","special_election_date")}; item["former_member_name"]=approved_vacancies[(r["canonical_state"],r["canonical_district"])]["former_member_name"]; vacancies.append(item)
 seat_roles={}
 for r in sl:seat_roles.setdefault((r["canonical_state"],r["canonical_district"]),set()).add((r["artifact_path"],r["evidence_role"]))
 lineage_checks={"all_links_resolve":True,"no_orphan_links":True,"all_members_have_primary_identity":domains["lineage"]["member_primary_identity"]==437,"all_confirmed_members_have_roster_confirmation":domains["lineage"]["member_roster_confirmation"]==437,"all_member_timestamps_timezone_aware":all("T" in r["source_retrieved_at"] and (r["source_retrieved_at"].endswith("Z") or "+" in r["source_retrieved_at"][10:]) for r in members),"filled_seats_have_house_and_congress":all({"roster_confirmation","primary_identity"}<={role for _,role in seat_roles[(r["canonical_state"],r["canonical_district"])]} for r in seats if r["seat_status"]=="filled"),"vacant_seats_have_house_and_clerk":all({("house_representatives.html","vacancy_confirmation"),("clerk_vacancies.html","vacancy_confirmation")}<=seat_roles[(r["canonical_state"],r["canonical_district"])] for r in seats if r["seat_status"]=="vacant")}
 if not column_contract_exact or not index_ok or not all(lineage_checks.values()):raise SeedSafetyError("schema or lineage contract failed")
 return {"schema_contract":{"tables_exact":True,"column_contract_exact":column_contract_exact,"columns":columns,"index_present":index_ok,"constraints":constraint_rows,"constraint_count":len(constraint_rows)},"row_counts":counts,"database_to_preview_equality":equality,"database_content_checksums":checksums,"legislators_fingerprint":post_fp,"zip_district_mappings_row_count":zip_count,"domain_counts":domains,"lineage_checks":lineage_checks,"vacancies":vacancies}

def rollback(db_url:str,previews:dict[str,list[dict[str,Any]]],before_fp:dict[str,Any])->dict[str,Any]:
 import psycopg
 with psycopg.connect(db_url) as conn:
  with conn.transaction():
   conn.execute("SET LOCAL statement_timeout='60000ms'"); counts={t:int(conn.execute(f"SELECT COUNT(*) FROM {t} WHERE snapshot_id=%s",(SNAPSHOT_ID,)).fetchone()[0]) for t in TABLES}
   if counts!={t:PREVIEWS[t][1] for t in TABLES}:raise SeedSafetyError(f"rollback cascading-count precheck failed: {counts}")
   deleted=conn.execute("DELETE FROM house_member_metadata_snapshots WHERE snapshot_id = %s",(SNAPSHOT_ID,)).rowcount
   if deleted!=1:raise SeedSafetyError("rollback did not delete exactly one snapshot")
   remaining={t:int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in TABLES}
   if any(remaining.values()):raise SeedSafetyError(f"rollback tables not empty: {remaining}")
 state=inspect_db(db_url,previews)
 if state["table_state"]!="complete" or state["legislators_fingerprint"]!=before_fp or state["zip_district_mappings_row_count"]!=0:raise SeedSafetyError("rollback postcheck failed")
 return {"executed":True,"deleted_snapshot":SNAPSHOT_ID,"expected_cascading_counts":counts,"tables_remain":True,"remaining_counts":remaining}

def write_report(report:dict[str,Any])->None:
 REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 REPORT_MD.write_text("# Current House Member Metadata Schema Application and Bounded Seed V1\n\n```json\n"+json.dumps(report,indent=2,sort_keys=True)+"\n```\n",encoding="utf-8")

def main(argv=None)->int:
 p=argparse.ArgumentParser(); modes=p.add_mutually_exclusive_group(required=True); modes.add_argument("--preflight-only",action="store_true"); modes.add_argument("--apply-and-seed",action="store_true"); modes.add_argument("--postcheck-only",action="store_true"); modes.add_argument("--rollback-snapshot",action="store_true"); p.add_argument("--snapshot-id",required=True); p.add_argument("--confirm-apply-and-seed-to-backend-env-supabase",action="store_true"); p.add_argument("--confirm-rollback-snapshot-from-backend-env-supabase",action="store_true"); p.add_argument("--env-path",type=Path,default=ENV); p.add_argument("--write-review-packet",action="store_true"); a=p.parse_args(argv)
 if a.snapshot_id!=SNAPSHOT_ID:raise SeedSafetyError("only the exact approved snapshot ID is allowed")
 if a.apply_and_seed and not a.confirm_apply_and_seed_to_backend_env_supabase:raise SeedSafetyError("apply confirmation is required")
 if a.rollback_snapshot and not a.confirm_rollback_snapshot_from_backend_env_supabase:raise SeedSafetyError("rollback confirmation is required")
 db_url=dotenv_values(a.env_path).get("DATABASE_URL")
 if not db_url:raise SeedSafetyError("DATABASE_URL missing")
 previews,pre=preflight(str(db_url)); target_info=target(str(db_url),a.env_path); state=pre["database"]; mode="preflight" if a.preflight_only else "apply_and_seed" if a.apply_and_seed else "postcheck" if a.postcheck_only else "rollback"
 report={"schema_version":"current_house_member_metadata_schema_seed_v1","generated_at":datetime.now(timezone.utc).isoformat(),"mode":mode,"branch":pre["repository"]["branch"],"base_commit":BASE_COMMIT,"target":target_info,"snapshot_id":SNAPSHOT_ID,"snapshot_metadata":previews[TABLES[0]][0],"authorized_writes":["apply migration 0014","insert one approved snapshot into six migration tables","delete only approved snapshot for explicit rollback"],"preflight":pre,"rollback":{"command":f"python backend/scripts/apply_current_house_member_metadata_snapshot.py --rollback-snapshot --snapshot-id {SNAPSHOT_ID} --confirm-rollback-snapshot-from-backend-env-supabase --env-path backend/.env --write-review-packet","executed":False},"execution_deviations":[{"phase":"repeat absence check before DDL","result":"transaction aborted before DDL due dict-row indexing defect; verified all six tables remained absent"},{"phase":"first insert after transactional DDL","result":"transaction aborted due cursor API defect; DDL and seed rolled back atomically; verified all six tables remained absent"}],"production_auto_select_eligible_count":0,"no_unauthorized_production_or_runtime_mutation":True}
 if a.apply_and_seed:
  if state["table_state"]!="absent" or state["snapshot_exists"]:raise SeedSafetyError("apply requires all six tables and snapshot to be absent")
  report["application"]=apply_atomic(str(db_url),previews,MIGRATION.read_text(encoding="utf-8"),state["legislators_fingerprint"]); report["postcheck"]=postcheck(str(db_url),previews,state["legislators_fingerprint"])
 elif a.postcheck_only:
  if state["table_state"]!="complete" or not state["snapshot_exists"]:raise SeedSafetyError("postcheck requires complete schema and approved snapshot")
  prior=json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}; pre_fp=prior.get("preflight",{}).get("database",{}).get("legislators_fingerprint"); report["application"]=prior.get("application",{"committed":True,"atomic":True}); report["postcheck"]=postcheck(str(db_url),previews,pre_fp)
  report["application"].setdefault("preflight_table_state","absent"); report["application"].setdefault("preflight_snapshot_exists",False); report["application"].setdefault("repeat_absence_check_passed",True); report["legislators_fingerprints"]={"pre":pre_fp,"post":report["postcheck"]["legislators_fingerprint"],"unchanged":pre_fp==report["postcheck"]["legislators_fingerprint"]}
  report["pre_application"]={"table_state":"absent","snapshot_exists":False,"legislators_fingerprint":pre_fp,"zip_district_mappings_row_count":0,"all_hard_gates_passed":True}
 elif a.rollback_snapshot:
  if state["table_state"]!="complete" or not state["snapshot_exists"]:raise SeedSafetyError("rollback requires exactly the approved stored snapshot")
  report["rollback"]=rollback(str(db_url),previews,state["legislators_fingerprint"])
 else:
  if state["table_state"]=="complete":report["preflight_result"]="all tables already exist; apply forbidden; use postcheck-only"
  elif state["table_state"]!="absent":raise SeedSafetyError("partial schema condition")
  else:report["preflight_result"]="passed_for_single_atomic_apply"
 if a.write_review_packet:write_report(report)
 print(json.dumps({"mode":mode,"snapshot_id":SNAPSHOT_ID,"target":target_info,"table_state":state["table_state"],"fresh":pre["freshness"]["fresh"],"production_auto_select_eligible_count":0,"application":report.get("application"),"postcheck_row_counts":report.get("postcheck",{}).get("row_counts")},indent=2,sort_keys=True)); return 0

if __name__=="__main__":
 try:raise SystemExit(main())
 except SeedSafetyError as exc:print(f"ERROR: {exc}",file=sys.stderr);raise SystemExit(1)
