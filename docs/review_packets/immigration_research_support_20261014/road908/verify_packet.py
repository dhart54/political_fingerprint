"""Verify retained sources and conditional §101 textual operations, offline.

Uses actual retained source text, not hash substitutes for source checks. No
candidate imports, network, writes, production effects or legal certification.
"""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
from pathlib import Path
from source_tools import pre,normalize,code_statute,section,replay

BASE='docs/review_packets/immigration_research_support_20261014/road908/'
SNAPSHOT='770419240bcf0b672c701886f14d5fa8e0d31f82'
BANK='docs/editorial/shared_candidates/house_119_immigration_20260916/sources.json'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def git_blob(ref,path):return subprocess.check_output(['git','show',(''if ref=='INDEX'else ref)+':'+path])


def validate(load):
    ledger=json.loads(load('ledger.json'));ident=json.loads(load('source_identities.json'))
    raw_bank=git_blob(SNAPSHOT,BANK);bank=json.loads(raw_bank)['sources'];by={r['source_id']:r for r in bank}
    assert ledger['source_snapshot']==ident['source_snapshot']==SNAPSHOT
    assert ident['bank_blob_sha256']==sha(raw_bank)
    assert ident['bank_git_oid']==subprocess.check_output(['git','rev-parse',SNAPSHOT+':'+BANK],text=True).strip()
    for sid,wanted in ident['governed_sources'].items():
        row=by[sid]
        seal=sha(json.dumps({k:v for k,v in row.items()if k!='governed_bytes_sha256'},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
        assert seal==wanted['governed_bytes_sha256']==row['governed_bytes_sha256']
        for key in ['source_id','source_type','url','text_version','raw_sha256']:assert wanted[key]==row[key]
        assert wanted['row_index']==bank.index(row)
        assert wanted['text_characters']==len(row['text'])
        assert wanted['text_utf8_sha256']==sha(row['text'].encode())
    captures=json.loads(load('capture_receipts.json'));assert len(captures)==2
    for cap in captures:
        raw=load(cap['file']);assert cap['http_status']==200 and cap['usable'] is True
        assert len(raw)==cap['raw_bytes'] and sha(raw)==cap['raw_sha256']
    law_raw=load('pl119101.html');code_raw=load('usc1813_2024.html')
    assert b'United States Code, 2024 Edition'in code_raw
    assert re.search(rb'currentthrough:(\d+)',code_raw).group(1)==b'20250106'
    law=pre(law_raw);code=code_statute(code_raw);a,b,body=section(law,908,909);baseline=normalize(body)
    assert len(body)==6535 and len(baseline)==5147
    assert baseline.startswith('SEC. 908. PROMOTING NEW BANK FORMATION.')
    assert 'SEC. 105.' not in body and 'SEC. 909.'not in body
    assert load('section908_display.txt').decode()==body
    assert load('section908_operative.txt').decode()==baseline+'\n'
    assert load('usc1813_operative.txt').decode()==code and len(code)==21172
    prior=ident['prior_classification_source'];lead_raw=git_blob(prior['commit'],prior['path'])
    assert sha(lead_raw)==prior['raw_sha256']
    eh=by['govinfo:hr6955eh']['text'];comp=by['govinfo:hr6644eas2']['text']
    texts={'law_pre':law,'baseline_operative':baseline,'FDIA1813_operative':code,
           'FDIA1813_raw_utf8':code_raw.decode(),'EH':eh,'EAS2':comp,
           'reviewed_classification_pre':pre(lead_raw)}
    for key,wanted in ident['derived_sources'].items():
        assert len(texts[key])==wanted['characters']
        assert sha(texts[key].encode())==wanted['text_utf8_sha256']
    bindings=0
    def walk(value):
        nonlocal bindings
        if isinstance(value,dict):
            if {'source_text','start','end','text','text_utf8_sha256'}<=value.keys():
                text=texts[value['source_text']];start,end=value['start'],value['end']
                assert 0<=start<end<=len(text) and text[start:end]==value['text']
                assert sha(text[start:end].encode())==value['text_utf8_sha256'];bindings+=1
            for child in value.values():walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(ledger)
    identity=ledger['source_identity']
    assert identity['starting_page_marker']['text']=='[[Page 140 STAT. 973]]'
    assert '[[Page 140 STAT. 974]]'in body and '[[Page 140 STAT. 975]]'in body
    assert ledger['base_source_kind']=='enacted_public_law'
    assert identity['law_number']=='119-101' and identity['short_title']=='21st Century ROAD to Housing Act'
    assert 'Public Law 119-101'in law[:1000]
    law_date=re.search(r'has become law without his signature on (July 11, 2026)',normalize(identity['enactment_note']['text'])).group(1)
    enacted=datetime.datetime.strptime(law_date,'%B %d, %Y').date()
    assert identity['enactment_date']==enacted.isoformat()
    assert identity['enactment_mode']=='without President signature per OFR note'
    stage_text=re.search(r'Passed the House of Representatives (July 21, 2026)\.',eh).group(1)
    stage=datetime.datetime.strptime(stage_text,'%B %d, %Y').date()
    assert identity['House_stage_date']==stage.isoformat() and enacted<stage
    assert ledger['temporal_boundary']['enacted_before_stage'] is True
    assert ledger['temporal_boundary']['express_908_delay_in_complete_section_found'] is False
    assert not re.search(r'effective date|take effect',baseline,re.I)
    assert ledger['temporal_boundary']['section1001_specific_delay_applied_to908'] is False
    _,_,other=section(law,1001,1101)
    assert 'subsections (b) and (d) of this section'in normalize(other)
    ea=eh.index('SEC. 101.');eb=eh.index('SEC. 102.',ea);result=replay(baseline,eh[ea:eb])
    assert load('proposed_after_101.txt').decode()==result['after']+'\n'
    assert ledger['synthetic_after']['text_utf8_sha256']==sha(load('proposed_after_101.txt'))
    ops=ledger['operators'];assert [r['id']for r in ops]==['101(1)','101(2)(A)','101(2)(B)','101(2)(C)','101(3)']
    for index,old,new in [(0,'before_b2','after_b2'),(1,'before_heading','after_heading'),(2,'before_report','after_report'),(4,'before_dates','after_dates')]:
        assert ops[index]['before']==result[old] and ops[index]['after']==result[new]
    assert ops[3]['before'] is None and ops[3]['after']==result['inserted_c2']
    clocks=ledger['clock_and_branch_inventory']
    assert [clocks[k]for k in ['baseline_b2','baseline_b3','after_b2','after_b3']]==['180-day','90-day','90-day','90-day unchanged']
    b3=baseline[baseline.index('(3) Result of failure to act.'):baseline.index('(c) Pilot Program Study.')]
    assert 'within the 90-day period required under paragraph (2)'in b3
    assert b3 in result['after'] and '180-day'in result['before_b2'] and '90-day'in result['after_b2']
    for begin,end in [('(a) Pilot Phase-in','(2) Review of changes.'),
                      ('(1) Study.--','(2) Report to congress.'),
                      ('(d) Study on De Novo','(e) Definitions.')]:
        old=baseline[baseline.index(begin):baseline.index(end,baseline.index(begin))]
        assert old in result['after']
    assert 'Not later than December 31, 2031'in result['after_report']
    assert 'including its holding company and all of its subsidiaries and affiliates'in result['after']
    assert 'less than $10,000,000,000'in result['after']
    for phrase in ['may, jointly, determine','Not earlier than January 1, 2031, and not later than June 30, 2031','Unless the Federal banking agencies make the determination','shall be permanent','before the date of such determination','make such report available to the public','the reasons for such determination']:
        assert phrase in result['inserted_c2']
    comparator=ledger['EAS2_comparator'];assert comparator['source_id']=='govinfo:hr6644eas2'
    ca=comp.rfind('SEC. 908.');cb=comp.index('SEC. 909.',ca);current=normalize(comp[ca:cb])
    assert '180-day'in comparator['b2'] and comparator['b2']in current
    assert '90-day'in comparator['b3'] and comparator['b3']in current
    assert comparator['clock_discrepancy_retained'] is True and comparator['whole_text_equivalence_claim'] is False
    reading=json.loads(load('read_receipt.json'));assert reading['source_snapshot']==SNAPSHOT
    position=0
    for interval in reading['completed_definition_read_partition']:
        assert interval['start']==position and interval['end']>position
        position=interval['end']
        assert sha(code[interval['start']:position].encode())==interval['text_utf8_sha256']
    assert position==len(code)
    return {'literal_binding_records':bindings,'textual_operations':5,'complete_section_characters':6535,
            'normalized_before_characters':5147,'synthetic_after_characters':6234,
            'read_dated_definition_characters':21172,'existing_governed_seals':2,'raw_captures':2,
            'enactment_before_stage':'2026-07-11 < 2026-07-21, without presidential signature',
            'limit':'Conditional textual replay; no exhaustive updating, application, implementation or candidate certification.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ref');args=parser.parse_args();root=Path(__file__).resolve().parent
    def load(name):return git_blob(args.ref,BASE+name)if args.ref else(root/name).read_bytes()
    result=validate(load);receipt=json.loads(load('delivered_blobs.json'))
    for name,wanted in receipt['sha256'].items():
        raw=load(name);assert sha(raw)==wanted and len(raw)==receipt['bytes'][name]
        assert subprocess.check_output(['git','hash-object','--stdin'],input=raw).decode().strip()==receipt['git_blob_oid'][name]
    result['final_git_blobs']=len(receipt['sha256']);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
