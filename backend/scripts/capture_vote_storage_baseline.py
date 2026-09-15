"""Capture public legislative state only, in one bounded read-only snapshot."""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.editorial_artifact_store import target_info

SHARED = ("chamber_session", "vote_type", "final_result", "vote_margin", "winning_position",
          "party_vote_totals", "bipartisan_majority", "sponsor_party", "context_source_list", "context_version")
MEMBER = ("roll_call_id", "legislator_id", "member_position", "member_party",
          "member_party_majority_position", "member_voted_with_party_majority",
          "member_voted_with_winning_side", "created_at", "updated_at")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from dotenv import dotenv_values
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    conn = None
    try:
        url = dotenv_values(args.env_path).get("DATABASE_URL")
        target_info(url, "production", None)
        conn = psycopg.connect(url, connect_timeout=15, options="-c statement_timeout=120000 -c lock_timeout=3000", row_factory=dict_row)
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        assert conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
        fields = sql.SQL(',').join(sql.Identifier(f) for f in SHARED)
        conflicts = conn.execute(sql.SQL("SELECT count(*) n FROM (SELECT roll_call_id FROM public.vote_contexts GROUP BY roll_call_id HAVING count(DISTINCT ROW({}))<>1) x").format(fields)).fetchone()['n']
        if conflicts:
            raise ValueError("shared field ambiguity")
        metadata = conn.execute("SELECT now() captured_at,pg_database_size(current_database()) database_bytes").fetchone()
        metadata.update(shared_fields=SHARED, member_fields=MEMBER, shared_conflicts=conflicts)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Columnar records avoid repeated field names and duplicated shared JSON.
        # No auth, vault, settings, credentials, or private service state is exported.
        tables = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
        allowed={'bills','candidate_evidence','chamber_medians','drift_scores','editorial_artifact_batches','editorial_artifact_relationships','editorial_artifact_versions','editorial_publication_registry','fingerprints','house_member_metadata_snapshot_artifacts','house_member_metadata_snapshots','house_member_service_evidence','house_member_service_evidence_artifacts','house_seat_status_evidence','house_seat_status_evidence_artifacts','legislator_contacts','legislators','race_candidates','roll_calls','senate_amendment_references','summaries','upcoming_races','vote_classifications','vote_contexts','vote_interpretations','votes_cast','zip_district_map','zip_district_mappings'}
        if {t['tablename'] for t in tables}!=allowed:raise ValueError('unexpected public schema; review export scope')
        counts = {}
        with gzip.open(args.output, "wt", encoding="utf-8") as out:
            out.write(json.dumps({"metadata":metadata}, default=str) + "\n")
            for entry in tables:
                name=entry['tablename']
                columns=[r['column_name'] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (name,))]
                if name=='vote_contexts': columns=list(MEMBER)
                out.write(json.dumps({'table':name,'columns':columns})+'\n')
                count=0
                with conn.cursor(name='storage_export') as cur:
                    cur.itersize=5000
                    cur.execute(sql.SQL('SELECT {} FROM public.{} ORDER BY 1,2').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(name)))
                    for row in cur:
                        out.write(json.dumps([row[c] for c in columns],default=str,separators=(',',':'))+'\n');count+=1
                        if count>2000000:raise ValueError('bounded table export cap exceeded')
                counts[name]=count
                out.write('null\n')
            columns=['roll_call_id',*SHARED]
            out.write(json.dumps({'table':'shared_context_snapshot','columns':columns})+'\n')
            for row in conn.execute(sql.SQL('SELECT DISTINCT ON (roll_call_id) {} FROM public.vote_contexts ORDER BY roll_call_id,legislator_id').format(sql.SQL(',').join(map(sql.Identifier,columns)))):
                out.write(json.dumps([row[c] for c in columns],default=str,separators=(',',':'))+'\n')
            out.write('null\n')
        conn.rollback();conn.close();conn=None
        print(json.dumps({'counts':counts,'compressed_bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'production_writes':False}))
    except Exception as error:
        if conn is not None:conn.rollback();conn.close()
        raise SystemExit('Read-only capture failed: '+type(error).__name__) from None

if __name__=='__main__':main()
