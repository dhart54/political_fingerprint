"""Read-only research packet binding checks; no candidate/runtime imports or writes.

Run from any checkout of this repository:
  python -X utf8 path/to/roll271/verify_packet.py --ref HEAD
Omit --ref to check current files. --ref reads every delivered file from that
exact commit/index; source material always comes from the fixed source commit.
This verifies literal bindings and coverage, not legal meaning or actual reading.
"""
import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

BASE = 'docs/review_packets/immigration_research_support_20261014/roll271/'
SNAPSHOT = '72b55fef7063cf4a2cf9af5fc317216b43a12aa0'
BANK = 'docs/editorial/shared_candidates/house_119_immigration_20260916/sources.json'
SOURCE_ID = 'govinfo:hr6955eh'
OUTER = ['1','101','102','103','104','201','202','203','204','301','302',
         '303','304','401','402','403','501','502','601','602','603','604',
         '701','702','703','801','802','803']
NESTED = [('177','203'),('178','203'),('1012','301'),('1013','302'),
          ('1014','302'),('1015','302'),('1016','302')]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git_blob(ref, path):
    spec = ':' + path if ref == 'INDEX' else ref + ':' + path
    return subprocess.check_output(['git', 'show', spec])


def validate(documents, raw_bank):
    identities = documents['source_identities.json']
    ledger = documents['section_ledger.json']
    imports = documents['imports.json']
    reading = documents['read_receipt.json']
    sources = json.loads(raw_bank)['sources']
    by_id = {x['source_id']: x for x in sources}
    assert identities['snapshot'] == SNAPSHOT
    assert identities['bank_path'] == BANK
    assert identities['bank_git_blob_sha256'] == digest(raw_bank)
    oid = subprocess.check_output(['git','rev-parse',SNAPSHOT+':'+BANK],text=True).strip()
    assert identities['bank_git_blob_oid'] == oid
    verified_ids = set()
    for ident in identities['sources']:
        source = by_id[ident['source_id']]
        seal = digest(json.dumps({k:v for k,v in source.items()
                                  if k != 'governed_bytes_sha256'},
                                 sort_keys=True,ensure_ascii=False,
                                 separators=(',',':')).encode())
        assert seal == source['governed_bytes_sha256'] == ident['governed_bytes_sha256']
        for key in ['source_type','url','text_version','raw_sha256']:
            assert ident[key] == source.get(key)
        assert ident['source_row_index'] == sources.index(source)
        assert ident['text_characters'] == len(source['text'])
        assert ident['text_utf8_sha256'] == digest(source['text'].encode())
        verified_ids.add(ident['source_id'])
    count = 0

    def walk(value):
        nonlocal count
        if isinstance(value,dict):
            if {'source_id','start','end','text','passage_utf8_sha256'} <= value.keys():
                assert value['source_id'] in verified_ids
                text = by_id[value['source_id']]['text']
                a,b = value['start'],value['end']
                assert 0 <= a < b <= len(text)
                assert text[a:b] == value['text']
                assert digest(text[a:b].encode()) == value['passage_utf8_sha256']
                count += 1
            for child in value.values():
                walk(child)
        elif isinstance(value,list):
            for child in value:
                walk(child)
    for document in [ledger,imports]:
        walk(document)
    for value in [ledger,imports,reading]:
        assert value['source_snapshot'] == SNAPSHOT
    assert ledger['action_id'] == 'house:119:2:271'
    rows = ledger['sections']
    assert [r['section'] for r in rows] == OUTER
    text = by_id[SOURCE_ID]['text']
    assert len(text) == 151645
    assert reading['source_id'] == SOURCE_ID
    assert reading['full_source_utf8_sha256'] == digest(text.encode())
    assert set(reading['section_notes']) == set(OUTER)
    end = 0
    for part in [ledger['preamble']] + [r['passage'] for r in rows]:
        assert part['source_id'] == SOURCE_ID and part['start'] == end
        end = part['end']
    assert end == len(text)
    for row in rows:
        heading = 'SECTION 1.' if row['section']=='1' else 'SEC. '+row['section']+'.'
        assert row['passage']['text'].startswith(heading)
        assert row['operator_conditions_exceptions_dates'] == reading['section_notes'][row['section']]
        assert row['external_dependency_scope']
    nested = ledger['inserted_section_locators']
    assert [(r['inserted_section'],r['outer_section']) for r in nested] == NESTED
    for row in nested:
        parent = next(r for r in rows if r['section']==row['outer_section'])['passage']
        assert parent['start'] < row['start'] < row['index_end'] <= parent['end']
        assert text[row['start']:].startswith('SEC. '+row['inserted_section']+'.')
        assert row['heading']['start'] == row['start']
    windows = reading['emission_windows']
    assert [(w['start'],w['end'])for w in windows] == [tuple(w)for w in reading['acknowledged_intervals']]
    end = 0
    for w in windows:
        assert w['start'] == end
        end = w['end']
        assert digest(text[w['start']:end].encode()) == w['passage_utf8_sha256']
    assert end == len(text) and reading['complete_captured_EH_read'] is True
    assert {r['section']for r in imports['missing_qualification']} == set(OUTER)-{'1'}
    assert len(imports['qualified_bounded_witnesses']) == 4
    assert len(imports['stage_witnesses']) == 3
    for witness in imports['qualified_bounded_witnesses']+imports['stage_witnesses']:
        assert witness['identity'] in identities['sources']
    return {'outer_sections':len(rows),'inserted_locators':len(nested),
            'bound_passages':count,'source_identities':len(verified_ids),
            'complete_captured_characters':len(text)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref')
    args = parser.parse_args()
    repo = Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
    def load_bytes(name):
        return git_blob(args.ref,BASE+name) if args.ref else (repo/BASE/name).read_bytes()
    names = ['source_identities.json','section_ledger.json','imports.json','read_receipt.json']
    docs = {name:json.loads(load_bytes(name))for name in names}
    raw_bank = git_blob(SNAPSHOT,BANK)
    result = validate(docs,raw_bank)
    probes = []
    def probe(name, mutate):
        changed = copy.deepcopy(docs)
        mutate(changed)
        try:
            validate(changed,raw_bank)
        except (AssertionError,KeyError,ValueError):
            probes.append(name)
        else:
            raise AssertionError('Mutation was not rejected: '+name)
    probe('changed literal',lambda d:d['section_ledger.json']['sections'][2]['passage'].__setitem__('text','changed'))
    probe('one-character coverage gap',lambda d:d['section_ledger.json']['sections'][2]['passage'].__setitem__('start',4140))
    probe('missing outer section',lambda d:d['section_ledger.json']['sections'].pop())
    probe('inserted heading promoted to outer',lambda d:d['section_ledger.json']['sections'][1].__setitem__('section','177'))
    probe('wrong source seal',lambda d:d['source_identities.json']['sources'][0].__setitem__('governed_bytes_sha256','0'*64))
    probe('wrong snapshot',lambda d:d['read_receipt.json'].__setitem__('source_snapshot','0'*40))
    receipt = json.loads(load_bytes('delivered_blobs.json'))
    for name, expected in receipt['sha256'].items():
        assert digest(load_bytes(name)) == expected, name
    result.update({'negative_probes_rejected':probes,'delivered_blobs_checked':len(receipt['sha256']),
                   'reading_and_legal_meaning':'Reading receipt is attributed to author; these mechanical checks cannot certify actual reading, legal meaning, import sufficiency or candidate integration.'})
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
