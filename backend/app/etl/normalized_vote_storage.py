"""Explicit normalized-schema ETL adapter; no change to logical context generation."""
import json
import os
from psycopg import sql
from psycopg.types.json import Jsonb

SHARED = ("chamber_session", "vote_type", "final_result", "vote_margin", "winning_position",
          "party_vote_totals", "bipartisan_majority", "sponsor_party", "context_source_list", "context_version")
MEMBER = ("roll_call_id", "legislator_id", "member_position", "member_party",
          "member_party_majority_position", "member_voted_with_party_majority", "member_voted_with_winning_side")
LOGICAL = ("roll_call_id", "legislator_id", "chamber_session", "vote_type", "member_position",
           "final_result", "vote_margin", "winning_position", "party_vote_totals", "member_party",
           "member_party_majority_position", "member_voted_with_party_majority", "member_voted_with_winning_side",
           "bipartisan_majority", "sponsor_party", "context_source_list", "context_version")


def enabled():
    return os.getenv("NORMALIZED_VOTE_STORAGE", "0") == "1"


def mapped_contexts(contexts, roll_keys, bioguides, roll_ids, member_ids):
    return [dict(row, roll_call_id=roll_ids[roll_keys[str(row["roll_call_id"])]],
                 legislator_id=member_ids[bioguides[str(row["legislator_id"])]]) for row in contexts]


def split_contexts(rows):
    shared = {}
    members = {}
    for original in rows:
        row = dict(original)
        for field in ("party_vote_totals", "context_source_list"):
            if isinstance(row[field], str): row[field] = json.loads(row[field])
        common = {field:row[field] for field in SHARED}
        rid = row["roll_call_id"]
        if rid in shared and shared[rid] != common:
            raise ValueError("roll-level context ambiguity")
        shared[rid] = common
        member = {field:row[field] for field in MEMBER}
        key=(rid,row["legislator_id"])
        if key in members and members[key] != member:
            raise ValueError("member context ambiguity")
        members[key]=member
    return shared, members


def write_contexts(cursor, rows):
    """Insert shared values once; reject drift; exact repeats write nothing.

    Caller owns transaction/rollback. This function never connects or commits.
    Only the separately opted-in normalized schema is supported here.
    """
    shared, members = split_contexts(rows)
    if not shared:return 0
    columns=["id",*["context_"+f for f in SHARED]]
    cursor.execute(sql.SQL("SELECT {} FROM public.roll_calls WHERE id=ANY(%s) ORDER BY id FOR UPDATE").format(sql.SQL(',').join(map(sql.Identifier,columns))), (sorted(shared),))
    found={}
    for result in cursor.fetchall():
        row = result if isinstance(result,dict) else dict(zip(columns,result))
        found[row['id']]=row
    if set(found)!=set(shared):raise ValueError("missing canonical roll call")
    for rid, incoming in sorted(shared.items()):
        prior=found[rid]
        if prior['context_context_version'] is not None:
            if any(prior['context_'+f]!=incoming[f] for f in SHARED):
                raise ValueError("shared context drift: explicit reviewed rebuild required")
        else:
            cursor.execute(sql.SQL("UPDATE public.roll_calls SET {} WHERE id=%s").format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier('context_'+f)) for f in SHARED)),
                           tuple(Jsonb(incoming[f]) if f in ('party_vote_totals','context_source_list') else incoming[f] for f in SHARED)+(rid,))
    cursor.execute(sql.SQL("SELECT {} FROM public.vote_context_members WHERE roll_call_id=ANY(%s)").format(sql.SQL(',').join(map(sql.Identifier,MEMBER))), (sorted(shared),))
    existing=set()
    for result in cursor.fetchall():
        row=result if isinstance(result,dict) else dict(zip(MEMBER,result))
        key=(row['roll_call_id'],row['legislator_id'])
        if key in members:
            if row!=members[key]:raise ValueError("member context drift")
            existing.add(key)
    new=[tuple(members[key][f] for f in MEMBER) for key in sorted(members) if key not in existing]
    if new:
        cursor.executemany(sql.SQL("INSERT INTO public.vote_context_members ({}) VALUES ({})").format(sql.SQL(',').join(map(sql.Identifier,MEMBER)),sql.SQL(',').join(sql.Placeholder() for _ in MEMBER)),new)
    return len(new)
