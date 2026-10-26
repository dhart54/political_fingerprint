"""Read-only validation of unfinished checkpoint144 evidence; no candidate acceptance."""
import json,re,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pypdf import PdfReader
import io
from backend.app.semantic_ir.shared_corpus import digest,sealed_digest
from scripts.validate_infrastructure_disaster_candidates142 import reconstruct_capture,normalized_pdf,TextParser,sha

def read(p):return json.loads(p.read_text(encoding='utf8'))
def check(value,message):
    if not value:raise ValueError(message)
def validate():
    m=read(P/'checkpoint_manifest.json');check(sealed_digest(m,'manifest_sha256')==m['manifest_sha256'],'Checkpoint manifest seal differs')
    actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file() and p.name not in ['checkpoint_manifest.json','checkpoint_validation.json'] and '__pycache__' not in p.parts}
    check(actual==set(m['files']),'Checkpoint file cohort differs')
    for name,expected in m['files'].items():
        raw=(P/name).read_bytes().replace(b'\r\n',b'\n');check(sha(raw)==expected['lf_sha256'] and len(raw)==expected['bytes']<195000,'Checkpoint bytes differ: '+name)
    retained=read(P/'retained_input_manifest.json');check(retained['canonical_state_changed'] is False and retained['existing_Health_candidates_accepted'] is False,'Retained candidate gained authority')
    for name,expected in retained['preserved_snapshot_files'].items():check(sha((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))==expected,'Retained snapshot changed: '+name)
    s=read(P/'sources.json');pool={x['source_id']:x for x in s['sources']};check(len(pool)==len(s['sources'])==39,'Source cohort differs')
    for x in pool.values():check(sealed_digest(x,'governed_bytes_sha256')==x['governed_bytes_sha256'],'Source seal differs')
    for r in retained['retained_objects']:
        old=next(x for x in read(ROOT/r['snapshot']/'sources.json')['sources'] if x['source_id']==r['source_id']);check(digest(pool[r['source_id']])==digest(old)==r['source_object_sha256'],'Retained object differs')
    captures={p.name.removesuffix('_capture.json'):read(p) for p in P.glob('*_capture.json')};check(len(captures)==7 and sum(c['raw_response_bytes'] for c in captures.values())==2476271,'Capture accounting differs')
    readers={};texts={};pages={};qa=read(P/'pdf_pages_review.json');check(len(qa['pages'])==20 and qa['whole_House_parent_PDFs_claimed_read'] is False,'PDF extent scope differs')
    for key,c in captures.items():
        raw=reconstruct_capture(c,P);check(c['requested_url']==c['final_url'],'Unexpected source route')
        if c.get('format')=='pdf':readers[key]=PdfReader(io.BytesIO(raw))
        else:
            parser=TextParser();parser.feed(raw.decode('utf8'));text=' '.join(' '.join(parser.parts).split());check(sha(text.encode())==c['normalized_text_sha256'],'HTML text differs');texts[key]=text
    for q in qa['pages']:
        text=readers[q['capture_key']].pages[q['one_based_pdf_page']-1].extract_text() or '';check(text==q['raw_page_text'] and sha(text.encode())==q['raw_page_text_sha256'] and sha(normalized_pdf(text).encode())==q['normalized_page_text_sha256'] and q['visual_read_completed'] is True,'PDF reconstruction/review record differs');pages[(q['capture_key'],q['one_based_pdf_page'])]=normalized_pdf(text)
    u=read(P/'source_units.json');check(len(u['units'])==23 and u['canonical_state_changed'] is u['source_registered'] is u['current_law_certified'] is False,'Selected units gained authority')
    for x in u['units']:
        source=pool[x['source_id']];check(digest(source)==x['source_object_sha256'] and source['raw_sha256']==captures[x['capture_key']]['raw_response_sha256'],'Selected identity differs')
        if 'html_extent' in x:
            e=x['html_extent'];text=texts[x['capture_key']][e['start']:e['end']]
        else:text=x['page_join_marker'].join(pages[(x['capture_key'],e['page'])][e['start']:e['end']] for e in x['pdf_normalized_page_extents'])
        check(text==source['text'] and sha(text.encode())==x['passage_sha256'],'Selected passage differs')
    um={x['unit_key']:pool[x['source_id']]['text'] for x in u['units']};token=lambda z:re.sub('[^a-z0-9]','',z.casefold())
    for b,roll in [(586,89),(1039,90),(530,115),(1286,133),(980,49)]:
        eh=pool[f'govinfo:hr{b}eh']['text'];eh=eh[eh.index('Be it enacted'):eh.index('Passed the House')];floor=um[f'hr{b}_floor_operative'];floor=floor[floor.index('Be it enacted'):].replace(' [page boundary] ',' ');check(token(eh)==token(floor),'Whole operative text differs')
        check('postpon' in um[f'hr{b}_question_postponement'] and f'(H.R. {b})' in um[f'hr{b}_resumption_roll{roll}'] and f'[Roll No. {roll}]' in um[f'hr{b}_resumption_roll{roll}'] and 'bill, as amended, was passed' in um[f'hr{b}_passage_result'],'Own floor chain differs')
    current={r['action_id']:r for r in read(ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch145_20260916/membership_review.json')['records']}
    for p in P.glob('historical_shared_*.json'):
        h=read(p);aid=h['action_id'];check(digest(current[aid])==h['Infrastructure_before_record_sha256'] and h['meaning_previously_accepted'] is h['Health_artifacts_rewritten'] is False,'Historical/current case drift')
    check(not (P/'authoring.json').exists() and not (P/'generated').exists(),'Unfinished research relabelled as authored candidates')
    return dict(state='unfinished_research_checkpoint_only',cases=5,source_objects=39,unchanged_retained_objects=16,new_selected_units=23,capture_invocations=7,raw_bytes=2476271,visually_reviewed_selected_pages=20,new_candidate_meanings=0,canonical_mutation=False,meaning_acceptance=False)
if __name__=='__main__':print(json.dumps(validate(),indent=2))
