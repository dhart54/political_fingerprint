"""Non-authorizing preparation and exact fact-only M15A.2 repair operator.

Production prepare/preflight use READ ONLY. Apply/rollback are future operations
requiring exact digest confirmation and a separate explicit production flag.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from psycopg import sql
from psycopg.types.json import Jsonb
from app.editorial_artifacts.bundle import semantic_hash
from app.etl.house_clerk_adapter import load_house_clerk_bundle
from app.etl.vote_context import build_vote_contexts
from scripts.editorial_artifact_store import StoreSafetyError, _connect, target_info
from scripts.foushee_justice_receipt_evidence_repair import (
    CONTEXT_FIELDS, _action_id, _bill_key_from_ref, _jsonable,
    _actual_semantic_post_state, _expected_semantic_post_state,
)

BASELINE = "8cd2d6ee1fd31e876c0d1c67b7516f6405f1d67d"
DIRECTORY = ROOT / "docs/data_repairs/foushee_m15a2_missing_reviewed_actions"
MEMBER = "F000477"
EXTERNAL_MEMBER = "leg_valerie_p_foushee"
LOCK = "foushee_m15a2_missing_reviewed_actions_v1"
NS = "NATIONAL_SECURITY_FOREIGN"
ENV = "ENVIRONMENT_ENERGY"
EDU = "EDUCATION_WORKFORCE"
JUSTICE = "JUSTICE_PUBLIC_SAFETY"
DOMAINS = (NS, ENV, EDU, JUSTICE)
ACTION_DOMAINS = {
    **{f"house:119:2:{n}": NS for n in (232,243,244,247,248,256,260,261,262,263,264,266,268,269,276,282)},
    **{f"house:119:1:{n}": ENV for n in (52,53,58,59,77,78,110,112,114,224,225,226,294,295)},
    "house:119:2:38": ENV,
}
IDS = sorted(ACTION_DOMAINS)
CAPS = dict(bills=6, roll_calls=31, votes_cast=31, vote_contexts=31,
            vote_classifications=0, vote_interpretations=0, editorial_artifacts=0,
            publication_registry=0, updates=0, deletes=0)
LINKED = ("votes_cast", "vote_contexts", "vote_classifications",
          "vote_interpretations", "senate_amendment_references")
EDITORIAL = ("editorial_publication_registry", "editorial_artifact_versions",
             "editorial_artifact_relationships", "editorial_artifact_batches")


def require(condition, message):
    if not condition:
        raise StoreSafetyError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, body):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(_jsonable(body), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seal(body, key):
    body[key] = semantic_hash({k: v for k, v in body.items() if k != key})
    return body


def rows(conn, query, params=()):
    return _jsonable([dict(r) for r in conn.execute(query, params).fetchall()])


def fingerprint(conn, table, where="TRUE", params=()):
    # PostgreSQL SHA-256 binds all columns without exporting unrelated vote data.
    query = sql.SQL("""SELECT count(*) AS count,
        encode(sha256(convert_to(COALESCE(jsonb_agg(to_jsonb(t)
        ORDER BY to_jsonb(t)::text COLLATE "C")::text, '[]'), 'UTF8')), 'hex') AS sha256
        FROM {} t WHERE """).format(sql.Identifier(table)) + sql.SQL(where)
    return dict(conn.execute(query, params).fetchone())


def table_counts(conn):
    return {t:conn.execute(sql.SQL('SELECT count(*) AS count FROM {}').format(sql.Identifier(t))).fetchone()['count']
            for t in ('legislators','bills','roll_calls',*LINKED,*EDITORIAL)}


def identities():
    return [(a.split(':')[0], *map(int, a.split(':')[1:])) for a in IDS]


def target_rolls(conn):
    placeholders = ','.join(['(%s,%s,%s,%s)'] * len(IDS))
    return rows(conn, f"""SELECT rc.*, b.congress AS bill_congress,
        b.bill_type,b.bill_number FROM roll_calls rc LEFT JOIN bills b ON b.id=rc.bill_id
        WHERE (rc.chamber::text,rc.congress,rc.session,rc.rollcall_number)
        IN ({placeholders}) ORDER BY rc.id""", tuple(x for a in identities() for x in a))


def bill_rows(conn, facts):
    keys = sorted({_bill_key_from_ref(r['bill_ref']) for r in facts['roll_calls']})
    placeholders = ','.join(['(%s,%s,%s)'] * len(keys))
    return rows(conn, f"SELECT * FROM bills WHERE (congress,bill_type,bill_number) IN ({placeholders}) ORDER BY id",
                tuple(x for k in keys for x in k))


def publication_rows(conn):
    from app.editorial_artifacts.repository import EditorialArtifactRepository
    return _jsonable(EditorialArtifactRepository(conn).publication_selector())


def publication_guard(conn):
    # Bind active Foushee selections; unrelated append-only editorial work is allowed.
    return [r for r in publication_rows(conn) if r['member_bioguide_id'] == MEMBER]


def source_facts(manifest, archive):
    require(manifest['manifest_sha256'] == semantic_hash({k:v for k,v in manifest.items() if k!='manifest_sha256'}), 'source manifest digest differs')
    require(sorted(r['canonical_action_id'] for r in manifest['sources']) == IDS, 'source universe differs')
    require(hashlib.sha256(Path(archive).read_bytes()).hexdigest() == manifest['archive_sha256'], 'official source archive digest differs')
    sources = manifest['sources'] + [manifest['member_roster']]
    roll_parties = {}
    with tempfile.TemporaryDirectory() as directory:
        with zipfile.ZipFile(archive) as z:
            require(sorted(z.namelist()) == sorted(r['source_filename'] for r in sources), 'archive file universe differs')
            for r in sources:
                name = r['source_filename']
                require(Path(name).name == name and '/' not in name and '\\' not in name, 'unsafe source filename')
                data = z.read(name)
                require(hashlib.sha256(data).hexdigest() == r['sha256'], 'official source digest differs: '+name)
                if 'canonical_action_id' in r:
                    entries = ET.fromstring(data).findall('.//recorded-vote/legislator')
                    parties = {e.get('name-id'):e.get('party') for e in entries}
                    require(len(parties)==len(entries) and all(k and v in {'D','R','I'} for k,v in parties.items()),
                            'official roll party identity missing, duplicate, or unsupported')
                    roll_parties[r['canonical_action_id']] = parties
                (Path(directory)/name).write_bytes(data)
        parsed = load_house_clerk_bundle(source_dir=Path(directory))
    require(sorted(_action_id(r) for r in parsed.roll_calls) == IDS, 'parsed official action identities differ')
    members = [r for r in parsed.legislators if r['bioguide_id']==MEMBER]
    require(len(members)==1 and members[0]==manifest['member_identity'], 'official member identity differs')
    member = members[0]
    roll_map = {r['id']:_action_id(r) for r in parsed.roll_calls}
    votes = [{'action_id':roll_map[v['roll_call_id']], 'position':v['position']}
             for v in parsed.votes_cast if v['legislator_id']==member['id']]
    require(len(votes)==31 and {v['action_id']:v['position'] for v in votes} ==
            {r['canonical_action_id']:r['F000477_vote'] for r in manifest['sources']}, 'official member votes differ')
    # The current roster binds identity, but each exact roll binds vote-time party.
    # Reuse established context rules without assigning current parties to old votes.
    contexts = []
    for roll in parsed.roll_calls:
        parties = roll_parties[_action_id(roll)]
        roll_members = [{**m, 'party':parties[m['bioguide_id']]} for m in parsed.legislators
                        if m['bioguide_id'] in parties]
        roll_votes = [v for v in parsed.votes_cast if v['roll_call_id']==roll['id']]
        require(len(roll_members)==len(parties)==len(roll_votes), 'official roll member universe differs')
        contexts.extend({'action_id':_action_id(roll), **{k:c[k] for k in CONTEXT_FIELDS}}
                        for c in build_vote_contexts(legislators=roll_members,
                            roll_calls=[roll], votes_cast=roll_votes)
                        if c['legislator_id']==member['id'])
    # No new outcome semantics: require deterministic context to agree with Clerk.
    outcomes = {'Passed':'passed', 'Agreed to':'passed', 'Failed':'failed'}
    official = {r['canonical_action_id']:outcomes.get(r['metadata']['vote-result']) for r in manifest['sources']}
    require(all(c['final_result']==official[c['action_id']] for c in contexts), 'context outcome conflicts with official result')
    return _jsonable(dict(bills=sorted(parsed.bills,key=lambda b:b['id']),
        roll_calls=sorted(parsed.roll_calls,key=_action_id),votes_cast=sorted(votes,key=lambda v:v['action_id']),
        vote_contexts=sorted(contexts,key=lambda c:c['action_id'])))


def capture_baseline(conn, facts, *, include_counts=True):
    member = rows(conn, 'SELECT * FROM legislators WHERE bioguide_id=%s', (MEMBER,))
    require(len(member)==1, 'F000477 identity missing or duplicate')
    rolls = rows(conn, "SELECT * FROM roll_calls WHERE chamber='house' AND congress=119 AND rollcall_number=ANY(%s) ORDER BY id",
                 (sorted({int(a.rsplit(':',1)[1]) for a in IDS}),))
    collisions = [r for r in rolls if _action_id(r) not in IDS]
    collision_ids = [r['id'] for r in collisions]
    guard = {'member':member[0], 'publications':publication_guard(conn),
             'core_constraints':rows(conn,"""SELECT conrelid::regclass::text AS relation,
                 conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint
                 WHERE conrelid IN ('bills'::regclass,'roll_calls'::regclass,'votes_cast'::regclass,'vote_contexts'::regclass)
                    OR confrelid IN ('bills'::regclass,'roll_calls'::regclass,'votes_cast'::regclass,'vote_contexts'::regclass)
                 ORDER BY conrelid::regclass::text,conname"""),
             'core_triggers':rows(conn,"""SELECT tgrelid::regclass::text AS relation,
                 tgname,pg_get_triggerdef(t.oid) AS definition,pg_get_functiondef(tgfoid) AS function
                 FROM pg_trigger t WHERE NOT tgisinternal AND tgrelid IN
                   ('bills'::regclass,'roll_calls'::regclass,'votes_cast'::regclass,'vote_contexts'::regclass)
                 ORDER BY tgrelid::regclass::text,tgname"""),
             'protected_other_session_rows':collisions,
             'protected_other_session_bills':rows(conn,'SELECT * FROM bills WHERE id=ANY(%s) ORDER BY id',
                                                  ([r['bill_id'] for r in collisions if r['bill_id'] is not None],)),
             'protected_linked_fingerprints':{t:fingerprint(conn,t,'roll_call_id=ANY(%s)',(collision_ids,)) for t in LINKED},
             'reused_bills':bill_rows(conn,facts)}
    return seal({'guard':guard, 'target_roll_calls':target_rolls(conn),
                 'captured_at_utc':datetime.now(timezone.utc).isoformat(),
                 'table_counts':table_counts(conn) if include_counts else {}}, 'baseline_sha256')


def check_lineage(conn, facts):
    from app.main import app  # Install the normal M14 runtime dispatcher.
    from app.editorial_presentations.site_publication import active_site_integration_candidate
    pubs = publication_rows(conn)
    expected = {}
    for domain in (NS,ENV):
        candidate = active_site_integration_candidate(pubs,member_bioguide_id=MEMBER,issue_id=domain)
        require(candidate is not None, 'active reviewed publication missing: '+domain)
        s=candidate['subject']; receipts=s.get('receipt_projections') or s['preview_data']['evidence_119']
        expected.update({r['canonical_action_id']:r['position'] for r in receipts if r['canonical_action_id'] in IDS})
    require(expected=={v['action_id']:v['position'] for v in facts['votes_cast']}, 'official facts conflict with active publication member actions')
    education=active_site_integration_candidate(pubs,member_bioguide_id=MEMBER,issue_id=EDU)
    require(education is not None and education['artifact_id']=='site-integration-candidate:f000477:education_workforce:m14g:v1',
            'expected active M14 Education publication differs')


def prepare(conn, manifest, archive, target):
    require(conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on', 'prepare requires READ ONLY')
    facts=source_facts(manifest,archive)
    check_lineage(conn,facts)
    baseline=capture_baseline(conn,facts)
    require(not baseline['target_roll_calls'], 'PARTIAL_OR_DRIFTED: a target core row already exists')
    reused={(b['congress'],b['bill_type'],b['bill_number']) for b in baseline['guard']['reused_bills']}
    facts['bills']=[b for b in facts['bills'] if (b['congress'],b['bill_type'],b['bill_number']) not in reused]
    require(len(facts['bills'])==CAPS['bills'], 'derived missing bill count differs from reviewed six-bill graph')
    return seal({'schema_version':'m15a2_core_repair_v1','baseline_main_sha':BASELINE,
        'accepted':False, 'sealed':False, 'production_database_write':False, 'canonical_action_ids':IDS,
        'source_manifest_sha256':manifest['manifest_sha256'], 'source_archive_sha256':manifest['archive_sha256'],
        'production_target':target,'facts':facts,'baseline':baseline,'write_caps':CAPS,
        'rollback_contract':{'ownership':'exact apply receipt IDs and complete row fingerprints; never delete reused dependencies',
                             'order':['vote_contexts','votes_cast','roll_calls','bills'],
                             'require_no_new_dependents':True}},'bundle_sha256')


def validate_bundle(bundle, manifest=None, archive=None):
    require(bundle.get('schema_version')=='m15a2_core_repair_v1', 'bundle schema differs')
    require(bundle.get('bundle_sha256')==semantic_hash({k:v for k,v in bundle.items() if k!='bundle_sha256'}), 'bundle digest differs')
    require(bundle.get('canonical_action_ids')==IDS and bundle.get('write_caps')==CAPS, 'bundle universe or caps differ')
    require(bundle.get('production_database_write') is False, 'preparation cannot grant production authority')
    require(bundle.get('accepted') is False and bundle.get('sealed') is False, 'repair preparation must remain unaccepted and unsealed')
    require(bundle['baseline']['baseline_sha256']==semantic_hash({k:v for k,v in bundle['baseline'].items() if k!='baseline_sha256'}), 'baseline digest differs')
    manifest=manifest or load(DIRECTORY/'source_manifest.json')
    archive=archive or DIRECTORY/'official_sources.zip'
    facts=source_facts(manifest,archive)
    require(manifest['manifest_sha256']==bundle['source_manifest_sha256'], 'bundle source binding differs')
    reused={(b['congress'],b['bill_type'],b['bill_number']) for b in bundle['baseline']['guard']['reused_bills']}
    facts['bills']=[b for b in facts['bills'] if (b['congress'],b['bill_type'],b['bill_number']) not in reused]
    require(facts==bundle['facts'], 'write graph does not reproduce from pinned official bytes')
    require({k:len(facts[k]) for k in ('bills','roll_calls','votes_cast','vote_contexts')}==
            {k:CAPS[k] for k in ('bills','roll_calls','votes_cast','vote_contexts')}, 'fact graph counts differ')


def target_state(conn,bundle):
    rolls=target_rolls(conn); ids=[r['id'] for r in rolls]
    new_keys={(b['congress'],b['bill_type'],b['bill_number']) for b in bundle['facts']['bills']}
    bills=[b for b in bill_rows(conn,bundle['facts']) if (b['congress'],b['bill_type'],b['bill_number']) in new_keys]
    result={'legislator_id':bundle['baseline']['guard']['member']['id'], 'bills':bills,'roll_calls':rolls}
    result.update({t:rows(conn,f'SELECT * FROM {t} WHERE roll_call_id=ANY(%s) ORDER BY roll_call_id',(ids,)) for t in LINKED})
    return {'rows':result}


def guard_now(conn,bundle):
    guard=copy.deepcopy(capture_baseline(conn,bundle['facts'],include_counts=False)['guard'])
    new_keys={(b['congress'],b['bill_type'],b['bill_number']) for b in bundle['facts']['bills']}
    guard['reused_bills']=[b for b in guard['reused_bills'] if (b['congress'],b['bill_type'],b['bill_number']) not in new_keys]
    return guard


def matches_post(state,bundle):
    r=state['rows'];mid=r['legislator_id']
    if any(x['legislator_id']!=mid for t in ('votes_cast','vote_contexts') for x in r[t]) or r['senate_amendment_references']:
        return False
    return _actual_semantic_post_state(state)==_expected_semantic_post_state(bundle)


def preflight(conn,bundle):
    validate_bundle(bundle)
    require(guard_now(conn,bundle)==bundle['baseline']['guard'], 'PARTIAL_OR_DRIFTED: protected baseline or publication changed')
    state=target_state(conn,bundle)
    if matches_post(state,bundle):
        return 'ALREADY_APPLIED'
    require(not any(state['rows'][k] for k in ('bills','roll_calls',*LINKED)), 'PARTIAL_OR_DRIFTED: partial or conflicting repair')
    return 'READY'


class BorrowedConnection:
    def __init__(self,conn): self.conn=conn
    def __getattr__(self,key): return getattr(self.conn,key)
    def close(self): pass
    def cursor(self,*args,**kwargs):
        from psycopg.rows import tuple_row
        return self.conn.cursor(*args,**{**kwargs,'row_factory':tuple_row})


@contextmanager
def public_reads_in_transaction(conn):
    # Single-threaded operator only: every normal public read sees uncommitted facts.
    from app.main import app
    from app.api import precomputed, editorial_presentations
    original=(precomputed.get_connection,editorial_presentations.get_connection)
    precomputed.get_connection=editorial_presentations.get_connection=lambda:BorrowedConnection(conn)
    try: yield
    finally: precomputed.get_connection,editorial_presentations.get_connection=original


def public_state(conn, expect_repaired):
    from app.api import positions, editorial_presentations
    from app.editorial_presentations.reviewed_record import GovernedReceiptProjectionError
    result={}
    with public_reads_in_transaction(conn):
        for scope in ('119','all'):
            presentations=editorial_presentations.get_editorial_presentations(EXTERNAL_MEMBER,scope,None)
            details={}
            for domain in DOMAINS:
                try:
                    details[domain]=positions.get_legislator_position_evidence(EXTERNAL_MEMBER,domain,scope,None)
                except GovernedReceiptProjectionError as exc:
                    require(not expect_repaired and domain in (NS,ENV) and 'missing from the database ledger' in str(exc), 'unexpected public composition failure')
                    details[domain]={'status':503,'reason':str(exc)}
            if expect_repaired:
                discovery=positions.get_legislator_positions(EXTERNAL_MEMBER,scope,None)
                for domain in DOMAINS:
                    summary=next(r for r in discovery['positions'] if r['domain']==domain)
                    require(summary['total_votes']==len(details[domain]['evidence']), 'discovery/detail counts differ: '+domain)
                require(details[NS]['review_accounting']['reviewed_action_count']==82, 'National Security reviewed count differs')
                require(details[ENV]['review_accounting']['reviewed_action_count']==63, 'Environment reviewed count differs')
            else:
                require(all(details[d].get('status')==503 for d in (NS,ENV)), 'pre-repair public missing-action state differs')
            edu=details[EDU]['review_accounting']
            require(edu['reviewed_action_count']==17 and edu['available_action_count']>=17 and
                    edu['available_action_count']==17+edu['not_yet_reviewed_action_count'], 'Education review boundary differs')
            result[scope]={'presentations':presentations,'details':details}
    return _jsonable(result)


def invariant_public(before,after):
    manifest=load(DIRECTORY/'source_manifest.json')
    last_inserted=max(datetime.strptime(r['metadata']['action-date'],'%d-%b-%Y').date().isoformat()
                      for r in manifest['sources'])
    for scope in ('119','all'):
        require(before[scope]['presentations']==after[scope]['presentations'], 'accepted public wording/findings changed')
        for domain in (EDU,JUSTICE):
            old=copy.deepcopy(before[scope]['details'][domain]);new=copy.deepcopy(after[scope]['details'][domain])
            # Shared coverage is a live database range, not a reviewed finding.
            # Inserting the source-backed latest action may extend its end date.
            baseline,applied=(old,new) if before[scope]['details'][NS].get('status')==503 else (new,old)
            for left,right in ((baseline,applied),(baseline['scope_metadata'],applied['scope_metadata'])):
                require(right['window_end']==max(left['window_end'],last_inserted),'unexpected global coverage change')
                left.pop('window_end');right.pop('window_end')
            require(old==new, domain+' ledger, accounting, or receipt content changed during repair')


def insert_row(conn,table,body):
    query=sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING *').format(sql.Identifier(table),
        sql.SQL(',').join(map(sql.Identifier,body)),sql.SQL(',').join(sql.Placeholder() for _ in body))
    return _jsonable(dict(conn.execute(query,tuple(Jsonb(v) if isinstance(v,(dict,list)) else v for v in body.values())).fetchone()))


def owned_state(conn,receipt):
    result={}
    for table,records in receipt['inserted'].items():
        if table=='vote_contexts':
            result[table]=rows(conn,'SELECT * FROM vote_contexts WHERE roll_call_id=ANY(%s) ORDER BY roll_call_id',
                               ([r['roll_call_id'] for r in records],))
        else:
            result[table]=rows(conn,f'SELECT * FROM {table} WHERE id=ANY(%s) ORDER BY id',([r['id'] for r in records],))
    return result


def apply(conn,bundle,*,fault_after=None,persist_receipt=None):
    with conn.transaction():
        conn.execute("SET LOCAL timezone='UTC'")
        conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(LOCK,))
        conn.execute('LOCK TABLE bills,roll_calls,votes_cast,vote_contexts IN SHARE ROW EXCLUSIVE MODE')
        require(conn.info.transaction_status.name=='INTRANS', 'apply must own a transaction')
        state=preflight(conn,bundle)
        if state=='ALREADY_APPLIED':
            public_state(conn,True)
            return {'status':state,'writes':{k:0 for k in CAPS}}
        before=public_state(conn,False)
        counts_before=table_counts(conn)
        editorial_before={t:fingerprint(conn,t) for t in EDITORIAL}
        inserted={t:[] for t in ('bills','roll_calls','votes_cast','vote_contexts')}
        def stage(name):
            if fault_after==name: raise StoreSafetyError('injected failure after '+name)
        bill_ids={(b['congress'],b['bill_type'],b['bill_number']):b['id'] for b in bundle['baseline']['guard']['reused_bills']}
        for b in bundle['facts']['bills']:
            row=insert_row(conn,'bills',{k:b[k] for k in ('congress','bill_type','bill_number','title','summary','committee','subjects')})
            inserted['bills'].append(row);bill_ids[(b['congress'],b['bill_type'],b['bill_number'])]=row['id']
        stage('bills');roll_ids={}
        for r in bundle['facts']['roll_calls']:
            body={k:r[k] for k in ('chamber','congress','session','rollcall_number','vote_date','question','description','source_url')}
            body['bill_id']=bill_ids[_bill_key_from_ref(r['bill_ref'])]
            row=insert_row(conn,'roll_calls',body);inserted['roll_calls'].append(row);roll_ids[_action_id(r)]=row['id']
        stage('roll_calls');mid=bundle['baseline']['guard']['member']['id']
        for v in bundle['facts']['votes_cast']:
            inserted['votes_cast'].append(insert_row(conn,'votes_cast',dict(roll_call_id=roll_ids[v['action_id']],legislator_id=mid,position=v['position'])))
        stage('votes_cast')
        for c in bundle['facts']['vote_contexts']:
            inserted['vote_contexts'].append(insert_row(conn,'vote_contexts',dict(roll_call_id=roll_ids[c['action_id']],legislator_id=mid,**{k:c[k] for k in CONTEXT_FIELDS})))
        stage('vote_contexts')
        require(matches_post(target_state(conn,bundle),bundle), 'post-write exact facts differ')
        require(guard_now(conn,bundle)==bundle['baseline']['guard'], 'protected rows changed during apply')
        require(editorial_before=={t:fingerprint(conn,t) for t in EDITORIAL}, 'editorial rows changed during apply')
        after=public_state(conn,True);invariant_public(before,after);stage('public_postconditions')
        writes={**{k:0 for k in CAPS},**{k:len(v) for k,v in inserted.items()}}
        require(writes==CAPS,'actual writes differ from exact caps')
        require(table_counts(conn)=={t:n+CAPS.get(t,0) for t,n in counts_before.items()},
                'actual table count deltas differ from exact caps')
        receipt={'bundle_sha256':bundle['bundle_sha256'],'inserted':inserted,'status':'APPLIED','writes':writes}
        # Capture PK/timestamp ownership, including the context composite keys.
        receipt['inserted']=owned_state(conn,receipt)
        receipt=seal(receipt,'receipt_sha256')
        # Persist ownership before COMMIT. Failure to save the receipt aborts writes.
        # A receipt alone never proves commit; rollback also requires exact DB state.
        if persist_receipt is not None: persist_receipt(receipt)
        stage('ownership_receipt')
        return receipt


def rollback(conn,bundle,receipt):
    with conn.transaction():
        conn.execute("SET LOCAL timezone='UTC'")
        conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(LOCK,))
        conn.execute('LOCK TABLE bills,roll_calls,votes_cast,vote_contexts IN SHARE ROW EXCLUSIVE MODE')
        require(receipt.get('receipt_sha256')==semantic_hash({k:v for k,v in receipt.items() if k!='receipt_sha256'}) and
                receipt.get('bundle_sha256')==bundle['bundle_sha256'],'rollback ownership receipt differs')
        require(receipt.get('status')=='APPLIED' and receipt.get('writes')==CAPS and
                set(receipt.get('inserted',{}))=={'bills','roll_calls','votes_cast','vote_contexts'},
                'rollback ownership shape differs')
        require(preflight(conn,bundle)=='ALREADY_APPLIED','rollback requires exact applied state')
        actual=target_state(conn,bundle)['rows']
        for table in ('bills','roll_calls','votes_cast','vote_contexts'):
            keys=('roll_call_id','legislator_id') if table=='vote_contexts' else ('id',)
            require({tuple(r[k] for k in keys) for r in receipt['inserted'][table]}==
                    {tuple(r[k] for k in keys) for r in actual[table]},'rollback ownership target differs')
        require(owned_state(conn,receipt)==receipt['inserted'],'repair-owned row fingerprint differs')
        before=public_state(conn,True);editorial_before={t:fingerprint(conn,t) for t in EDITORIAL}
        counts_before=table_counts(conn)
        # Reject any unowned FK dependents; do not rely on cascading deletes.
        target_ids=[r['id'] for r in receipt['inserted']['roll_calls']]
        for table in LINKED:
            count=fingerprint(conn,table,'roll_call_id=ANY(%s)',(target_ids,))['count']
            require(count==(31 if table in ('votes_cast','vote_contexts') else 0),'new target dependents block rollback')
        new_bill_ids=[r['id'] for r in receipt['inserted']['bills']]
        require(not rows(conn,'SELECT id FROM roll_calls WHERE bill_id=ANY(%s) AND NOT(id=ANY(%s))',(new_bill_ids,target_ids)), 'new bill dependents block rollback')
        deleted={}
        for table in ('vote_contexts','votes_cast','roll_calls','bills'):
            if table=='vote_contexts':
                deleted[table]=conn.execute('DELETE FROM vote_contexts WHERE roll_call_id=ANY(%s) AND legislator_id=%s',(target_ids,bundle['baseline']['guard']['member']['id'])).rowcount
            else:
                deleted[table]=conn.execute(sql.SQL('DELETE FROM {} WHERE id=ANY(%s)').format(sql.Identifier(table)),([r['id'] for r in receipt['inserted'][table]],)).rowcount
        require(deleted=={k:CAPS[k] for k in deleted},'rollback counts differ')
        require(table_counts(conn)=={t:n-deleted.get(t,0) for t,n in counts_before.items()},
                'rollback changed unrelated table counts')
        require(preflight(conn,bundle)=='READY','rollback did not restore baseline')
        after=public_state(conn,False);invariant_public(before,after)
        require(editorial_before=={t:fingerprint(conn,t) for t in EDITORIAL},'editorial state changed during rollback')
        return {'status':'ROLLED_BACK','deleted':deleted,'restored_baseline':True}


def durable_receipt(path,body):
    """Create a complete fsynced receipt without overwriting an existing file."""
    destination=Path(path).resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    handle,name=tempfile.mkstemp(prefix='.m15a2-receipt-',dir=destination.parent)
    try:
        with os.fdopen(handle,'w',encoding='utf-8') as stream:
            stream.write(json.dumps(body,indent=2,sort_keys=True)+'\n')
            stream.flush();os.fsync(stream.fileno())
        os.link(name,destination)  # Atomic create, fails if destination exists.
        if os.name!='nt':
            folder=os.open(destination.parent,os.O_RDONLY)
            try:os.fsync(folder)
            finally:os.close(folder)
    finally:
        Path(name).unlink(missing_ok=True)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','preflight','apply','rollback'))
    p.add_argument('--target',choices=('production','disposable'),required=True)
    p.add_argument('--bundle',type=Path,default=DIRECTORY/'repair_bundle.json')
    p.add_argument('--receipt',type=Path)
    p.add_argument('--confirm-bundle-digest')
    p.add_argument('--confirm-production-repair',action='store_true')
    p.add_argument('--confirm-production-rollback',action='store_true')
    a=p.parse_args(argv)
    dsn=os.environ.get('DATABASE_URL' if a.target=='production' else 'M15A2_DISPOSABLE_DATABASE_URL')
    require(bool(dsn),'explicit target environment is required')
    target=target_info(dsn,a.target,None)
    if a.target=='disposable':
        from urllib.parse import urlsplit
        u=urlsplit(dsn)
        require(u.hostname in ('localhost','127.0.0.1') and u.path=='/pf_m15a2_repair','disposable target must be dedicated local pf_m15a2_repair')
    bundle=None if a.mode=='prepare' else load(a.bundle)
    if bundle and a.target=='production': require(target==bundle['production_target'],'production target identity differs')
    if a.mode in ('apply','rollback'):
        require(a.confirm_bundle_digest==bundle['bundle_sha256'],'exact reviewed bundle digest confirmation required')
        require(a.receipt is not None,'apply/rollback requires an ownership receipt path')
        if a.target=='production':
            require(a.confirm_production_repair if a.mode=='apply' else a.confirm_production_rollback,'explicit production authorization required')
    with _connect(dsn,autocommit=True) as conn:
        if a.mode in ('prepare','preflight'):
            with conn.transaction():
                conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
                conn.execute("SET LOCAL timezone='UTC'")
                conn.execute("SET LOCAL statement_timeout='30s'")
                result=(prepare(conn,load(DIRECTORY/'source_manifest.json'),DIRECTORY/'official_sources.zip',target)
                        if a.mode=='prepare' else {'status':preflight(conn,bundle),'writes':0})
        else:
            conn.execute("SET lock_timeout='10s'");conn.execute("SET statement_timeout='120s'")
            result=(apply(conn,bundle,persist_receipt=lambda r:durable_receipt(a.receipt,r))
                    if a.mode=='apply' else rollback(conn,bundle,load(a.receipt)))
    if a.mode=='prepare':write(a.bundle,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('facts','baseline','inserted')},sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
