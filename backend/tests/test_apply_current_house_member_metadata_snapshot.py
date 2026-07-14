from __future__ import annotations
import copy, json
from datetime import date
from pathlib import Path
import shutil
import pytest
from backend.scripts import apply_current_house_member_metadata_snapshot as seed

def test_pinned_snapshot_id_enforced():
    with pytest.raises(seed.SeedSafetyError,match="exact approved snapshot"):
        seed.main(["--preflight-only","--snapshot-id","wrong"])

def test_pinned_previews_counts_checksums_and_freshness():
    previews,meta=seed.load_previews(today=date(2026,7,13))
    assert [len(previews[t]) for t in seed.TABLES]==[1,486,437,441,874,882]
    assert meta["within_application_freshness_window"] is True and meta["freshness_enforced_for_mode"] is True and meta["snapshot_age_days"]==0

CASES=seed.ROOT/"backend/tests/_house_metadata_seed_cases"

def setup_function():
    if CASES.exists():shutil.rmtree(CASES)
    CASES.mkdir(parents=True)

def teardown_function():
    if CASES.exists():shutil.rmtree(CASES)

def test_preview_checksum_mismatch(monkeypatch):
    tmp_path=CASES
    monkeypatch.setattr(seed,"PREVIEW_DIR",tmp_path)
    with pytest.raises(seed.SeedSafetyError,match="checksum mismatch"):seed.load_previews(today=date(2026,7,13))

def test_preview_count_mismatch(monkeypatch):
    tmp_path=CASES
    source=seed.PREVIEW_DIR/"normalized_snapshot.json"; target=tmp_path/source.name; target.write_text("[]",encoding="utf-8")
    changed=dict(seed.PREVIEWS); changed[seed.TABLES[0]]=(source.name,1,seed.sha(target)); monkeypatch.setattr(seed,"PREVIEWS",changed); monkeypatch.setattr(seed,"PREVIEW_DIR",tmp_path)
    with pytest.raises(seed.SeedSafetyError,match="count mismatch"):seed.load_previews(today=date(2026,7,13))

def test_stale_snapshot_rejected():
    with pytest.raises(seed.SeedSafetyError,match="stale"):seed.load_previews(today=date(2026,7,25))

@pytest.mark.parametrize("mode",["preflight","apply_and_seed"])
def test_eight_day_snapshot_blocks_application_authorization_modes(mode):
    with pytest.raises(seed.SeedSafetyError,match=f"stale for {mode}"):seed.load_previews(today=date(2026,7,21),mode=mode)

@pytest.mark.parametrize("mode",["postcheck","rollback"])
def test_eight_day_snapshot_is_informational_for_durable_modes(mode):
    _,meta=seed.load_previews(today=date(2026,7,21),mode=mode)
    assert meta["snapshot_age_days"]==8
    assert meta["within_application_freshness_window"] is False
    assert meta["freshness_enforced_for_mode"] is False
    assert meta["freshness_role"]=="informational_only"
    assert meta[f"{mode}_valid_outside_freshness_window" if mode=="postcheck" else "rollback_available_outside_freshness_window"] is True

@pytest.mark.parametrize("sql",["ALTER TABLE legislators ADD x int;","DROP TABLE x;","TRUNCATE legislators;","UPDATE legislators SET in_office=false;","DELETE FROM legislators;","INSERT INTO legislators(id) VALUES(1);","COPY legislators FROM STDIN;","CREATE FUNCTION x() RETURNS void AS $$ $$ LANGUAGE sql;"])
def test_banned_migration_sql(sql):
    wrapped=f"BEGIN;\n{sql}\nCOMMIT;\n"
    with pytest.raises(seed.SeedSafetyError):seed.validate_migration(wrapped)

def test_migration_wrapper_stripping_is_exact():
    body=seed.strip_transaction_wrappers("BEGIN;\n-- c\nCREATE TABLE x(a int);\nCOMMIT;\n")
    assert body=="-- c\nCREATE TABLE x(a int);\n"
    with pytest.raises(seed.SeedSafetyError):seed.strip_transaction_wrappers("BEGIN TRANSACTION;\nSELECT 1;\nCOMMIT;")

def test_reviewed_migration_is_additive_and_pinned():
    result=seed.validate_migration(seed.MIGRATION.read_text(encoding="utf-8"))
    assert result["sha256"]==seed.EXPECTED_MIGRATION_SHA256==seed.sha(seed.MIGRATION)
    assert not any(result["banned_matches"].values())

@pytest.mark.parametrize("mutation", ["comment", "character", "substitute", "stripped"])
def test_any_nonreviewed_migration_bytes_fail_before_structure(mutation):
    sql=seed.MIGRATION.read_text(encoding="utf-8")
    changed={"comment":sql.replace("BEGIN;","BEGIN;\n-- changed",1),"character":sql.replace("Additive","additive",1),"substitute":"BEGIN;\nCREATE TABLE IF NOT EXISTS x(a INTEGER);\nCOMMIT;\n","stripped":seed.strip_transaction_wrappers(sql)}[mutation]
    with pytest.raises(seed.SeedSafetyError,match="checksum mismatch"):seed.validate_migration(changed)

def approved_username_hash(value):return seed.hashlib.sha256(seed.unicodedata.normalize("NFC",value).encode("utf-8")).hexdigest()

def test_exact_target_username_identity_is_pinned_and_credentials_masked(monkeypatch):
    monkeypatch.setattr(seed,"EXPECTED_DATABASE_USERNAME_SHA256",approved_username_hash("approved-user"))
    result=seed.target("postgresql://approved-user:secret@aws-1-us-east-1.pooler.supabase.com:5432/postgres",Path("backend/.env"))
    rendered=json.dumps({"target":result})
    assert result["exact_approved_target"] and result["username_identity_pinned"] and result["username_sha256_matches"]
    assert result["raw_url_recorded"] is False and "approved-user" not in rendered and "secret" not in rendered

def test_different_or_case_altered_username_fails_on_same_database(monkeypatch):
    monkeypatch.setattr(seed,"EXPECTED_DATABASE_USERNAME_SHA256",approved_username_hash("approved-user"))
    for username in ("different-user","Approved-user"):
        with pytest.raises(seed.SeedSafetyError,match="exact approved target"):
            seed.target(f"postgresql://{username}:secret@aws-1-us-east-1.pooler.supabase.com:5432/postgres",Path("backend/.env"))

def test_url_encoded_equivalent_username_passes_strict_nfc_rule(monkeypatch):
    monkeypatch.setattr(seed,"EXPECTED_DATABASE_USERNAME_SHA256",approved_username_hash("approved user"))
    result=seed.target("postgresql://approved%20user:secret@aws-1-us-east-1.pooler.supabase.com:5432/postgres",Path("backend/.env"))
    assert result["username_sha256_matches"] is True

@pytest.mark.parametrize("username",["bad%ZZname","bad%FFname"])
def test_username_decoding_failure_is_closed(monkeypatch,username):
    monkeypatch.setattr(seed,"EXPECTED_DATABASE_USERNAME_SHA256",approved_username_hash("approved-user"))
    with pytest.raises(seed.SeedSafetyError,match="percent encoding|decoding failed"):
        seed.target(f"postgresql://{username}:secret@aws-1-us-east-1.pooler.supabase.com:5432/postgres",Path("backend/.env"))

@pytest.mark.parametrize("url",[
    "postgresql://user:secret@other.supabase.com:5432/postgres",
    "postgresql://user:secret@aws-1-us-east-1.pooler.supabase.com:6543/postgres",
    "postgresql://user:secret@aws-1-us-east-1.pooler.supabase.com:5432/other",
    "postgresql://user:secret@localhost:5432/postgres",
    "postgresql://aws-1-us-east-1.pooler.supabase.com:5432/postgres",
    "postgresql://user@aws-1-us-east-1.pooler.supabase.com:5432/postgres",
])
def test_target_mismatches_fail_closed(url):
    with pytest.raises(seed.SeedSafetyError,match="exact approved target|database username"):seed.target(url,Path("backend/.env"))

def test_plain_insert_has_no_upsert_or_conflict_ignore():
    sql=seed.insert_sql(seed.TABLES[2],["snapshot_id","bioguide_id"])
    assert sql=="INSERT INTO house_member_service_evidence (snapshot_id,bioguide_id) VALUES (%s,%s)"
    assert "conflict" not in sql.lower() and "update" not in sql.lower()
    assert "with conn.cursor() as cursor:cursor.executemany" in Path(seed.__file__).read_text(encoding="utf-8")

def test_exact_insertion_order_is_dependency_order():
    assert seed.TABLES==("house_member_metadata_snapshots","house_member_metadata_snapshot_artifacts","house_member_service_evidence","house_seat_status_evidence","house_member_service_evidence_artifacts","house_seat_status_evidence_artifacts")

def test_timestamp_normalization_and_exact_row_mismatch():
    assert seed.canonical("2026-07-12T07:40:20Z")=="2026-07-12T07:40:20+00:00"
    rows=[{"snapshot_id":seed.SNAPSHOT_ID,"source_retrieved_at":"2026-07-12T07:40:20Z"}]
    changed=copy.deepcopy(rows); changed[0]["source_retrieved_at"]="2026-07-12T07:40:21Z"
    assert seed.content_sha(rows)!=seed.content_sha(changed)

def test_identity_requirements_and_production_mapping():
    previews,_=seed.load_previews(today=date(2026,7,13)); ids={r["legislator_id"]:r["bioguide_id"] for r in previews[seed.TABLES[2]]}
    legislators=[{"id":i,"bioguide_id":b,"chamber":"house","state":"NC","district":"01","in_office":True,"updated_at":None} for i,b in ids.items()]
    state={"legislators":legislators}
    assert seed.validate_identities(previews,state)["unmatched_production_identities"]==0
    bad=copy.deepcopy(previews); bad[seed.TABLES[2]][0]["legislator_id"]=-1
    with pytest.raises(seed.SeedSafetyError,match="identity mismatch"):seed.validate_identities(bad,state)

def test_filled_and_vacant_seat_identity_rules():
    previews,_=seed.load_previews(today=date(2026,7,13)); member_ids={r["legislator_id"]:r["bioguide_id"] for r in previews[seed.TABLES[2]]}; legislators=[{"id":i,"bioguide_id":b} for i,b in member_ids.items()]; state={"legislators":legislators}
    filled=next(r for r in previews[seed.TABLES[3]] if r["seat_status"]=="filled"); filled["current_legislator_id"]=None
    with pytest.raises(seed.SeedSafetyError,match="filled-seat"):seed.validate_identities(previews,state)
    previews,_=seed.load_previews(today=date(2026,7,13)); vacant=next(r for r in previews[seed.TABLES[3]] if r["seat_status"]=="vacant"); vacant["current_legislator_id"]=1
    with pytest.raises(seed.SeedSafetyError,match="vacant seat"):seed.validate_identities(previews,state)

def test_advisory_lock_and_rollback_are_narrow_static_contracts():
    text=Path(seed.__file__).read_text(encoding="utf-8").lower()
    assert "pg_advisory_xact_lock" in text and "delete from house_member_metadata_snapshots where snapshot_id = %s" in text
    assert "--rollback-snapshot" in text and "--confirm-rollback-snapshot-from-backend-env-supabase" in text
    assert "production_auto_select_eligible_count\":0" in text.replace(" ","")

def test_transaction_rollback_structure_covers_all_insert_phases():
    text=Path(seed.__file__).read_text(encoding="utf-8")
    assert "with conn.transaction():" in text
    assert "for table in TABLES:insert_phase" in text
    apply_body=text[text.index("def apply_atomic"):text.index("def db_rows")]
    assert apply_body.index("pg_advisory_xact_lock")<apply_body.index("strip_transaction_wrappers")<apply_body.index("for table in TABLES:insert_phase")
    assert 'SELECT COUNT(*) AS n FROM information_schema.tables' in apply_body and 'fetchone()["n"]' in apply_body

def test_fingerprint_changes_on_legislator_or_zip_safety_input():
    rows=[{"id":1,"bioguide_id":"A000001","chamber":"house","state":"NC","district":"01","in_office":True,"updated_at":None}]
    before=seed.fingerprint(rows); rows[0]["in_office"]=False
    assert seed.fingerprint(rows)!=before

def test_expected_postcheck_counts_are_pinned():
    assert {t:seed.PREVIEWS[t][1] for t in seed.TABLES}==dict(zip(seed.TABLES,[1,486,437,441,874,882]))
