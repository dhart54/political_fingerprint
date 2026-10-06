"""Offline inventory/accounting checks for the fixed Immigration candidate.

These checks cannot establish operative meaning or confer review/public authority.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest
from scripts.prepare_shared_domain_candidate import validate_universe_proposal
from scripts.shared_candidate_research import research_queue

DATA = ROOT / 'docs/editorial/shared_candidates/house_119_immigration_20260916'
INVENTORY_ID_SHA256 = 'e1a0ecb12b1697b6c5bbc43147ea66d155ed1e10b543efb18eaa05d677be5d25'


def normalized_status(value):
    return {'Aye': 'Yea', 'No': 'Nay', 'yea': 'Yea', 'nay': 'Nay',
            'present': 'Present', 'not_voting': 'Not Voting'}.get(value, value)


def normalized_measure(value):
    if not value:
        return None
    match = re.fullmatch(r'bill_119_(hr|s|hres|hjres|sjres|hconres|sconres)_(\d+)', value)
    if not match:
        return value
    prefix = {'hr': 'H R', 's': 'S', 'hres': 'H RES', 'hjres': 'H J RES',
              'sjres': 'S J RES', 'hconres': 'H CON RES', 'sconres': 'S CON RES'}
    return f'{prefix[match[1]]} {match[2]}'


def validate(authoring, capture, universe, membership, *, require_complete=False):
    validate_universe_proposal(universe, authoring, capture, membership)
    if authoring['domain_id'] != 'IMMIGRATION_BORDER' or universe['subject']['issue_id'] != 'IMMIGRATION_BORDER':
        raise ValueError('Immigration domain identity differs')
    if any(date != '2026-09-16' for date in [authoring['discovery_cutoff'],
            authoring['interpretation_action_set_cutoff'], universe['cutoff']['end_date'],
            membership['discovery_cutoff']]):
        raise ValueError('fixed September 16 cutoff differs')
    rows = universe['candidate_dispositions']
    ids = [r['action_id'] for r in rows]
    expected = [f'house:119:{session}:{roll}' for session, last in [(1, 362), (2, 314)]
                for roll in range(1, last + 1)]
    if ids != expected or digest(ids) != INVENTORY_ID_SHA256:
        raise ValueError('fixed committed inventory identity differs')
    sources = {s['source_id']: s for s in capture['sources']}
    if len(sources) != len(capture['sources']):
        raise ValueError('duplicate governed source identity')
    for row in rows:
        source = sources[row['source']['source_id']]
        if any(source[k] != row['source'][k] for k in ['url', 'raw_sha256', 'governed_bytes_sha256']):
            raise ValueError(f'inventory source identity differs: {row["action_id"]}')
        meta = source['metadata']
        actual_id = f'house:{int(meta["congress"])}:{int(meta["session"][0])}:{int(meta["rollcall-num"])}'
        date = datetime.strptime(meta['action-date'], '%d-%b-%Y').date().isoformat()
        if (row['action_id'] != actual_id or row['date'] != date or date > '2026-09-16'
                or row['question'] != meta['vote-question']
                or normalized_measure(row['measure']) != meta.get('legis-num')):
            raise ValueError(f'exact Clerk action identity differs: {row["action_id"]}')
        if normalized_status(row['member_action']) != normalized_status(source['member_records']['F000477']['official_label']):
            raise ValueError(f'Clerk member observation differs: {row["action_id"]}')
        if set(source['member_records']) != {'F000477', 'M001184'}:
            raise ValueError(f'both named Clerk observations required: {row["action_id"]}')
    accounting = universe['accounting']
    if accounting['total_candidate_actions'] != len(rows) or universe['complete_member_action_count'] != len(rows):
        raise ValueError('inventory count differs')
    expected_sets = {key: [r['action_id'] for r in rows if r['disposition'] == key]
                     for key in Counter(r['disposition'] for r in rows)}
    if accounting['action_ids_by_disposition'] != expected_sets:
        raise ValueError('disposition identity accounting differs')
    if universe['unresolved_action_ids'] != expected_sets.get('source_unresolved', []):
        raise ValueError('unresolved identity accounting differs')
    expected_subject = digest(dict(subject=universe['subject'], cutoff=universe['cutoff'], candidate_records=rows))
    if universe['universe_subject_sha256'] != expected_subject:
        raise ValueError('universe subject identity differs')
    reviewed = {r['action_id']: r for r in membership['records']}
    unfinished = [r['action_id'] for r in rows if r['action_id'] not in reviewed
                  or not reviewed[r['action_id']]['substantive_review_performed']]
    if require_complete and unfinished:
        raise ValueError(f'ordinary screening remains incomplete: {len(unfinished)} actions')
    queue = research_queue(universe, membership, limit=676)
    return dict(authority='Mechanical integrity only; no semantic acceptance or publication',
                inventory_count=len(rows), ordered_action_ids_sha256=digest(ids),
                governed_review_count=len(reviewed), unfinished_screenings=len(unfinished),
                queue_count=len(queue), disposition_counts=accounting['counts'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DATA)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    values = [json.loads((args.input / (name+'.json')).read_text(encoding='utf-8'))
              for name in ['authoring', 'sources', 'universe_proposal', 'membership_review']]
    print(json.dumps(validate(*values, require_complete=args.require_complete)))


if __name__ == '__main__':
    main()
