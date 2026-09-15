"""Opt-in normalized-storage migration runner for disposable validation only.

Production/green execution requires a separately reviewed target-bound operator;
this runner deliberately cannot authorize a remote database.
"""
import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

MIGRATION=Path(__file__).resolve().parents[1]/'migrations/staged/normalize_vote_storage.sql'


def validate(conn):
    row=conn.execute("SELECT (SELECT count(*) FROM public.vote_context_members) members,(SELECT count(*) FROM public.roll_calls WHERE context_context_version IS NOT NULL) shared_rolls,(SELECT count(*) FROM public.vote_context_members m LEFT JOIN public.roll_calls r ON r.id=m.roll_call_id WHERE r.context_context_version IS NULL) orphans").fetchone()
    if row['orphans']:raise ValueError('orphan member contexts')
    return row


def apply_disposable(conn):
    # Enforce target even when called directly, before any mutation.
    info=conn.info
    if info.host not in ('127.0.0.1','localhost') or info.dbname!='pf_normalized_storage':
        raise ValueError('dedicated loopback disposable database required')
    state=conn.execute("SELECT relkind FROM pg_class WHERE oid='public.vote_contexts'::regclass").fetchone()['relkind']
    if state=='v':return {'status':'ALREADY_NORMALIZED',**validate(conn)}
    if state!='r':raise ValueError('unexpected source relation')
    conn.execute(MIGRATION.read_text(encoding='utf-8'))
    return {'status':'NORMALIZED',**validate(conn)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('check','apply'))
    args=parser.parse_args()
    import psycopg
    from psycopg.rows import dict_row
    url=os.environ['NORMALIZED_STORAGE_DISPOSABLE_DATABASE_URL']
    target=urlsplit(url)
    if target.hostname not in ('localhost','127.0.0.1') or target.path!='/pf_normalized_storage':
        raise SystemExit('dedicated loopback disposable database required')
    with psycopg.connect(url,autocommit=True,row_factory=dict_row) as conn:
        print(apply_disposable(conn) if args.operation=='apply' else validate(conn))

if __name__=='__main__':main()
