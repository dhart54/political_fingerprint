from __future__ import annotations

import copy
import re
from contextlib import contextmanager
from datetime import date

import pytest

from backend.scripts import apply_current_house_member_metadata_snapshot as seed


class Result:
    def __init__(self, rows=None, rowcount=0):
        self.rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self.rows[0]

    def fetchall(self):
        return self.rows


class FakeCursor:
    def __init__(self, db): self.db = db
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def executemany(self, sql, values):
        table = re.search(r"INSERT INTO (\w+) \(([^)]+)\)", sql).group(1)
        self.db.events.append(f"insert:{table}")
        if self.db.fail_table == table: raise RuntimeError(f"failure:{table}")
        columns = re.search(r"\(([^)]+)\)", sql).group(1).split(",")
        self.db.rows[table].extend(dict(zip(columns, row)) for row in values)


class FakeDB:
    def __init__(self, previews, schema=False):
        self.rows = {t: copy.deepcopy(previews[t]) if schema else [] for t in seed.TABLES}
        self.schema = set(seed.TABLES) if schema else set()
        self.fail_table = None
        self.row_mismatch = False
        self.zip_count = 0
        self.events = []
        members = previews[seed.TABLES[2]]
        self.legislators = [{"id": r["legislator_id"], "bioguide_id": r["bioguide_id"], "chamber": "house", "state": r["canonical_state"], "district": r["canonical_district"], "in_office": True, "updated_at": None} for r in members]
        expected = seed.expected_schema_contract(seed.MIGRATION.read_text(encoding="utf-8"))
        self.columns = []
        for table, columns in expected["columns"].items():
            for name, value in columns.items():
                default = "nextval('x'::regclass)" if value["default"] == "sequence" else value["default"]
                self.columns.append({"table_name": table, "column_name": name, "data_type": value["data_type"], "udt_name": value["udt_name"], "is_nullable": value["nullable"], "column_default": default})
        self.constraints = [{"table_name": t, "constraint_name": f"c{i}", "constraint_type": "x", "definition": d} for i, (t, d) in enumerate(sorted(expected["constraints"]))]
        self.indexes = [{"indexname": "idx_house_member_service_seat", "tablename": "house_member_service_evidence", "indexdef": "CREATE INDEX idx_house_member_service_seat ON public.house_member_service_evidence USING btree (congress, canonical_state, canonical_district)"}]

    def cursor(self): return FakeCursor(self)
    def __enter__(self): return self
    def __exit__(self, *_): return False

    @contextmanager
    def transaction(self):
        before = (copy.deepcopy(self.rows), set(self.schema))
        self.events.append("begin")
        try:
            yield
        except Exception:
            self.rows, self.schema = before
            self.events.append("rollback")
            raise
        else:
            self.events.append("commit")

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        low = normalized.lower()
        if "pg_advisory_xact_lock" in low: self.events.append("lock"); return Result([{}])
        if low.startswith("set "): return Result()
        if low.startswith("create table") or "create table if not exists" in low:
            self.schema = set(seed.TABLES); self.events.append("ddl"); return Result()
        if "information_schema.tables" in low:
            if "count(*)" in low: return Result([{"n": len(self.schema)}])
            return Result([{"table_name": t} for t in sorted(self.schema)])
        if "information_schema.columns" in low: return Result(copy.deepcopy(self.columns))
        if "from pg_constraint" in low: return Result(copy.deepcopy(self.constraints))
        if "from pg_indexes" in low: return Result(copy.deepcopy(self.indexes))
        if low.startswith("delete from house_member_metadata_snapshots"):
            existed = any(r["snapshot_id"] == seed.SNAPSHOT_ID for r in self.rows[seed.TABLES[0]])
            for table in seed.TABLES: self.rows[table] = [r for r in self.rows[table] if r["snapshot_id"] != seed.SNAPSHOT_ID]
            self.events.append("delete-target"); return Result(rowcount=1 if existed else 0)
        if "from legislators" in low: return Result(copy.deepcopy(self.legislators))
        if "from zip_district_mappings" in low: return Result([{"n": self.zip_count}])
        if low.startswith("select exists(select 1 from house_member_metadata_snapshots"):
            return Result([{"e": any(r["snapshot_id"] == params[0] for r in self.rows[seed.TABLES[0]])}])
        table = next((t for t in sorted(seed.TABLES, key=len, reverse=True) if re.search(rf"from {t}(?:\s|$)", low)), None)
        if table:
            selected = [r for r in self.rows[table] if not params or r["snapshot_id"] == params[0]]
            if "count(*)" in low: return Result([{"n": len(selected)}])
            order = low.split(" order by ", 1)[1].split(",") if " order by " in low else []
            selected.sort(key=lambda r: tuple(str(r.get(k.strip())) for k in order))
            selected = copy.deepcopy(selected)
            if self.row_mismatch and selected: selected[0][next(iter(selected[0]))] = "mismatch"
            return Result(selected)
        raise AssertionError(f"unhandled SQL: {normalized}")


@pytest.fixture
def previews(): return seed.load_previews(today=date(2026, 7, 13))[0]


def install(monkeypatch, db):
    import psycopg
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: db)


def test_atomic_success_executes_lock_ddl_and_exact_insert_order(monkeypatch, previews):
    db = FakeDB(previews); install(monkeypatch, db); before = seed.fingerprint(db.legislators)
    result = seed.apply_atomic("unused", previews, seed.MIGRATION.read_text(encoding="utf-8"), before)
    assert result["committed"]
    assert db.events.index("lock") < db.events.index("ddl") < db.events.index(f"insert:{seed.TABLES[0]}")
    assert [x.removeprefix("insert:") for x in db.events if x.startswith("insert:")] == list(seed.TABLES)


@pytest.mark.parametrize("failed_table", seed.TABLES)
def test_each_insert_failure_rolls_back_rows_and_ddl(monkeypatch, previews, failed_table):
    db = FakeDB(previews); db.fail_table = failed_table; install(monkeypatch, db)
    with pytest.raises(RuntimeError, match="failure"):
        seed.apply_atomic("unused", previews, seed.MIGRATION.read_text(encoding="utf-8"), seed.fingerprint(db.legislators))
    assert db.schema == set() and all(not db.rows[t] for t in seed.TABLES) and db.events[-1] == "rollback"


def test_row_fingerprint_and_zip_mismatches_prevent_commit(monkeypatch, previews):
    for fault in ("row", "fingerprint", "zip"):
        db = FakeDB(previews); install(monkeypatch, db); expected = seed.fingerprint(db.legislators)
        if fault == "row": db.row_mismatch = True
        elif fault == "fingerprint": expected = {"row_count": 0, "sha256": "bad"}
        else: db.zip_count = 1
        with pytest.raises(seed.SeedSafetyError): seed.apply_atomic("unused", previews, seed.MIGRATION.read_text(encoding="utf-8"), expected)
        assert db.schema == set() and db.events[-1] == "rollback"


def test_exact_postcheck_success_and_missing_schema_failure(monkeypatch, previews):
    db = FakeDB(previews, schema=True); install(monkeypatch, db); before = seed.fingerprint(db.legislators)
    assert seed.postcheck("unused", previews, before)["schema_contract"]["schema_contract_exact"]
    db.schema.remove(seed.TABLES[-1])
    with pytest.raises(seed.SeedSafetyError, match="schema table set mismatch"): seed.postcheck("unused", previews, before)


def test_snapshot_scoped_rollback_preserves_unrelated_rows(monkeypatch, previews):
    db = FakeDB(previews, schema=True)
    for table in seed.TABLES:
        other = copy.deepcopy(previews[table][0]); other["snapshot_id"] = "unrelated-snapshot"; db.rows[table].append(other)
    install(monkeypatch, db); before = seed.fingerprint(db.legislators)
    result = seed.rollback("unused", previews, before)
    assert result["unrelated_rows_preserved"] and "lock" in db.events and "delete-target" in db.events
    assert all([r["snapshot_id"] for r in db.rows[t]] == ["unrelated-snapshot"] for t in seed.TABLES)


@pytest.mark.parametrize("drift", ["cascade", "fk_target", "check", "unique", "type", "default", "nullability", "index"])
def test_schema_drift_blocks_rollback_before_delete(monkeypatch, previews, drift):
    db = FakeDB(previews, schema=True)
    if drift == "cascade":
        row = next(r for r in db.constraints if "on delete cascade" in r["definition"]); row["definition"] = row["definition"].replace(" on delete cascade", "")
    elif drift == "fk_target":
        row = next(r for r in db.constraints if "references legislators id" in r["definition"]); row["definition"] = row["definition"].replace("references legislators id", "references other_table id")
    elif drift in {"check", "unique"}:
        row = next(r for r in db.constraints if r["definition"].startswith(drift)); row["definition"] = row["definition"].replace(drift, f"changed_{drift}", 1)
    elif drift == "type": db.columns[0]["data_type"] = "smallint"
    elif drift == "default":
        row = next(r for r in db.columns if r["column_default"] == "0"); row["column_default"] = "1"
    elif drift == "nullability": db.columns[0]["is_nullable"] = "YES"
    else: db.indexes = []
    install(monkeypatch, db)
    with pytest.raises(seed.SeedSafetyError, match="live schema contract mismatch"):
        seed.rollback("unused", previews, seed.fingerprint(db.legislators))
    assert "delete-target" not in db.events and db.events[-1] == "rollback"


def test_schema_contract_mutations_fail_closed():
    expected = seed.expected_schema_contract(seed.MIGRATION.read_text(encoding="utf-8"))
    columns = [{"table_name": t, "column_name": c, "data_type": v["data_type"], "udt_name": v["udt_name"], "is_nullable": v["nullable"], "column_default": "nextval('x'::regclass)" if v["default"] == "sequence" else v["default"]} for t, cs in expected["columns"].items() for c, v in cs.items()]
    constraints = [{"table_name": t, "definition": d} for t, d in expected["constraints"]]
    indexes = [{"indexname": "idx_house_member_service_seat", "tablename": "house_member_service_evidence", "indexdef": "CREATE INDEX x ON y (congress, canonical_state, canonical_district)"}]
    assert seed.verify_schema_contract(columns, constraints, indexes, seed.MIGRATION.read_text(encoding="utf-8"))["schema_contract_exact"]
    mutations = []
    for field, value in (("data_type", "smallint"), ("is_nullable", "YES"), ("column_default", "1")):
        changed = copy.deepcopy(columns); changed[0][field] = value; mutations.append((changed, constraints, indexes))
    for old, new in (("on delete cascade", ""), ("references legislators id", "references other_table id"), ("unique", "changed_unique"), ("check", "changed_check")):
        changed = copy.deepcopy(constraints); row = next(r for r in changed if old in r["definition"]); row["definition"] = row["definition"].replace(old, new, 1); mutations.append((columns, changed, indexes))
    mutations.append((columns, constraints, []))
    for c, k, i in mutations: assert not seed.verify_schema_contract(c, k, i, seed.MIGRATION.read_text(encoding="utf-8"))["schema_contract_exact"]
