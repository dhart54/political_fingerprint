"""Verify retained research bytes, source slices and conditional textual replay.

Run from this Git repository with --ref INDEX or --ref HEAD. No network/writes,
candidate imports, production effects or general legal-language interpretation.
"""
import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from source_tools import display_text,field,table_pre,replay

BASE='docs/review_packets/immigration_research_support_20261014/fdic401/'
SNAPSHOT='770419240bcf0b672c701886f14d5fa8e0d31f82'
BANK='docs/editorial/shared_candidates/house_119_immigration_20260916/sources.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git_blob(ref,path):
    return subprocess.check_output(['git','show',(''if ref=='INDEX'else ref)+':'+path])


def title12_rows(raw):
    return [line for line in table_pre(raw).splitlines()if re.match(r'^12\s+\S+',line)]


def classification_check(raw,expected_count,controls):
    rows=title12_rows(raw)
    assert len(rows)==expected_count
    sections={line.split()[1]for line in rows}
    assert '1812' not in sections
    assert set(controls)<=sections
    return rows


def validate(load):
    captures=json.loads(load('capture_receipts.json'))
    comparison=json.loads(load('comparison.json'))
    currency=json.loads(load('currency_boundary.json'))
    identities=json.loads(load('source_identities.json'))
    raw_bank=git_blob(SNAPSHOT,BANK)
    bank=json.loads(raw_bank)['sources']
    proposal=next(x for x in bank if x['source_id']=='govinfo:hr6955eh')
    assert identities['source_snapshot']==comparison['source_snapshot']==currency['source_snapshot']==SNAPSHOT
    assert identities['bank_blob_sha256']==digest(raw_bank)
    assert identities['bank_git_oid']==subprocess.check_output(['git','rev-parse',SNAPSHOT+':'+BANK],text=True).strip()
    seal=digest(json.dumps({k:v for k,v in proposal.items()if k!='governed_bytes_sha256'},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
    assert identities['source_bank_seal_recomputed']==proposal['governed_bytes_sha256']==seal
    for key in ['source_id','source_type','url','text_version','raw_sha256','governed_bytes_sha256']:
        assert identities['proposal_source'][key]==proposal[key]
    assert identities['proposal_source']['row_index']==bank.index(proposal)
    assert identities['proposal_source']['text_utf8_sha256']==digest(proposal['text'].encode())
    assert identities['proposal_source']['characters']==len(proposal['text'])
    for capture in captures:
        raw=load(capture['file'])
        assert len(raw)==capture['bytes'] and digest(raw)==capture['raw_sha256']
        assert capture['http_status']==200
        if capture['file']=='govinfo_2025_1812.html':
            assert b'Page Not Found | GovInfo' in raw and capture['usable'] is False
        else:
            assert capture['usable'] is True
    raw=load('govinfo_2024_1812.html')
    assert b'United States Code, 2024 Edition' in raw
    assert re.search(rb'currentthrough:(\d+)',raw).group(1)==b'20250106'
    assert currency['baseline_currentthrough']=='2025-01-06'
    assert currency['vote_stage_date']=='2026-07-21'
    full=display_text(raw);operative=field(raw,'statute');eh=proposal['text']
    assert load('baseline_full.txt').decode()==full
    assert load('baseline_operative.txt').decode()==operative
    texts={'baseline_full':full,'baseline_operative':operative,'EH':eh,
           'baseline_raw_utf8':raw.decode('utf8')}
    for name in ['olrc_classification_index.html','olrc_119_1_code_order.html','olrc_119_2_code_order.html']:
        texts[name+':display']=display_text(load(name))
        if 'code_order'in name:
            texts[name+':pre']=table_pre(load(name))
    for key,ident in identities['derived_sources'].items():
        assert ident['characters']==len(texts[key])
        assert ident['text_utf8_sha256']==digest(texts[key].encode())
    count=0
    def walk(value):
        nonlocal count
        if isinstance(value,dict):
            if {'source_text','start','end','text','text_utf8_sha256'}<=value.keys():
                original=texts[value['source_text']];a,b=value['start'],value['end']
                assert 0<=a<b<=len(original)
                assert original[a:b]==value['text']
                assert digest(original[a:b].encode())==value['text_utf8_sha256']
                count+=1
            for child in value.values():walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(comparison);walk(currency)
    a=eh.index('SEC. 401.');b=eh.index('SEC. 402.',a);result=replay(operative,eh[a:b])
    assert load('proposed_after_2024.txt').decode()==result['after_text']
    assert comparison['synthetic_after']['text_utf8_sha256']==digest(result['after_text'].encode())
    operators=comparison['operators']
    assert [x['id']for x in operators]==['401(1)','401(2)','401(3)(A)','401(3)(B)']
    assert len(operators[0]['occurrences'])==result['rename_count']==5
    actual=[(m.start(),m.end())for m in re.finditer(re.escape(result['rename_from']),operative)]
    assert [(x['occurrence_start'],x['occurrence_end'])for x in operators[0]['occurrences']]==actual
    for entry in operators[0]['occurrences']:
        assert operative[entry['occurrence_start']:entry['occurrence_end']]==entry['before_token']==result['rename_from']
        assert entry['after_token']==result['rename_to']
    assert operators[1]['before']==result['old_C'] and operators[1]['after']==result['new_C']
    assert operators[2]['before']==result['old_c1'] and operators[2]['after']==result['new_c1']
    assert operators[3]['before'] is None and operators[3]['after']==result['new_c4']
    assert [r['target']for r in operators[1:]]==['§1812(a)(1)(C)','§1812(c)(1)','§1812(c)(4)']
    for key in ['citizenship','state_experience']:
        item=comparison['carried_language'][key]
        assert item['text'] in result['old_C'] and item['text'] in result['new_C']
        assert item['present_before'] is True and item['present_after'] is True
        assert item['textually_new'] is False
    assert comparison['carried_language']['experience_addition'] in result['new_C']
    assert comparison['tenure_context']['target_subsection']=='(c)'
    assert comparison['tenure_context']['not_targeted_political_affiliation']=='(a)(2)'
    for begin,end in [('(2) Political affiliation','(b) Chairperson'),
                      ('(b) Chairperson','(c) Terms'),
                      ('(2) Interim appointments','(3) Continuation of service'),
                      ('(3) Continuation of service','(d) Vacancy')]:
        part=operative[operative.index(begin):operative.index(end)]
        assert part in result['after_text']
    for entry in currency['table_checks']:
        rows=classification_check(load(entry['file']),entry['title12_row_count'],entry['positive_control_sections'])
        assert entry['title12_block']['text']=='\n'.join(rows)
        assert entry['no_12_1812_entry'] is True
    assert [e['title12_row_count']for e in currency['table_checks']]==[21,46]
    return {'source_bound_passage_records':count,'operators':4,'bureau_rename_occurrences':5,
            'title12_classification_rows':[21,46],'baseline_currency':'2025-01-06',
            'proposal_stage':'2026-07-21','after_status':'Conditional synthetic text only; intervening-law and application limits unresolved.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ref');args=parser.parse_args()
    root=Path(__file__).resolve().parent
    def load(name):return git_blob(args.ref,BASE+name)if args.ref else(root/name).read_bytes()
    result=validate(load)
    receipt=json.loads(load('delivered_blobs.json'))
    for name,wanted in receipt['sha256'].items():
        raw=load(name)
        assert digest(raw)==wanted and len(raw)==receipt['bytes'][name],name
        assert subprocess.check_output(['git','hash-object','--stdin'],input=raw).decode().strip()==receipt['git_blob_oid'][name],name
    result['delivered_blobs']=len(receipt['sha256'])
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
