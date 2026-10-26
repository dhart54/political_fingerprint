"""Offline source/version and held-candidate checks. Confers no acceptance."""
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core,
    validate_shared_issue_mapping, validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT/'docs/review_packets/infrastructure_batch152_water_resources'
BASE = ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch149_20260916'
PREVIOUS = ROOT/'docs/review_packets/infrastructure_batch151_permitting'
HEALTH = ROOT/'docs/editorial/shared_candidates/house_119_health_20260916'
ACTIONS = ['house:119:1:'+str(n) for n in [19,29,125,216]]+['house:119:2:97']
BILLS = [187,776,2215,1917,6422]
MEMBERS = ['F000477','M001184']
PRODUCTS = ['shared_action_core','shared_issue_mapping','member_projections','compiler_input','compiled_ir','readable_candidates']
MANIFEST_SHA = '95f5174148cbf00f1ca3f1d2069edae7a802116aea45d9b1922a9c37c6a7be29'
PRESERVATION_SHA = 'b41f9347fb9622ff48821eaaf2ed47c4f0feb0b2bf9766316d33b873e2e815c0'


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def require(value, message):
    if not value: raise ValueError(message)
def same(a,b): return digest(a) == digest(b)


class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, text): self.parts.append(text)


def validate_files(name, expected, packet):
    m = read(P/name)
    require(digest(m) == expected and m['manifest_sha256'] == sealed_digest(m,'manifest_sha256'), 'Manifest drift: '+name)
    for name,entry in m['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to((P if packet else ROOT).resolve()), 'Manifest path escaped')
        raw = path.read_bytes()
        if entry['mode'] == 'lf': raw = raw.replace(b'\r\n',b'\n')
        require(hashlib.sha256(raw).hexdigest() == entry['sha256'] and len(raw) == entry['bytes'], 'Frozen bytes differ: '+name)
    return len(m['files'])


def validate_manifest(): return validate_files('packet_manifest.json',MANIFEST_SHA,True)
def validate_preservation(): return validate_files('preservation_manifest.json',PRESERVATION_SHA,False)


def inputs():
    names = dict(authoring='authoring.json',sources='sources.json',preflight='preparation_preflight.json',
                 bundle='decision_bundle.json',questions='source_questions.json',capture='capture_receipt.json',
                 conformance='floor_version_conformance.json',extents='source_extraction_extents.json',proof='held_replay_proof.json')
    return {**{k:read(P/n) for k,n in names.items()},'products':{n:read(P/'generated'/(n+'.json')) for n in PRODUCTS}}


def replay(authoring, sources):
    c,m,p,i,r = prepare(authoring,sources,MEMBERS)
    return dict(shared_action_core=c,shared_issue_mapping=m,member_projections=p,compiler_input=i,
                compiled_ir=r.compiled_ir,readable_candidates=readable_candidates(authoring,c,p,r))


def glyphs(text,layout=False):
    text = re.sub(r'(?m)^VerDate[^\n]*(?:\n|$)','',text)
    text = re.sub(r'(?m)^CONGRESSIONAL RECORD[^\n]*(?:\n|$)','',text)
    text = text.replace('``','"').replace("''",'"').replace('‘‘','"').replace('’’','"').replace('“','"').replace('”','"')
    text = text.replace('‘',"'").replace('’',"'").replace('`',"'").replace('--','—').replace('–','-').replace('\u00ad','')
    if layout: text = re.sub(r'-[ \t]*\n\s*','\ufff0',text)
    return ''.join(text.split()).casefold()


def compare_operative(eh, floor):
    """Only recorded layout hyphens can disappear; ordinary glyphs cannot."""
    expected = glyphs(eh); actual = glyphs(floor,True); i=j=0; edits=[]
    while i < len(actual):
        if actual[i] == '\ufff0':
            keep = j < len(expected) and expected[j] == '-'
            edits.append(dict(actual_compared_position=i,expected_compared_position=j,kept_hyphen=keep,
                              context=actual[max(0,i-20):i+22]))
            i += 1
            if keep: j += 1
            continue
        require(j < len(expected) and actual[i] == expected[j], 'Complete own floor/EH operative mismatch')
        i += 1; j += 1
    require(j == len(expected), 'Truncated own floor text')
    return expected, edits


def validate_capture(capture):
    require(same(capture,read(P/'capture_receipt.json')), 'Exact capture envelope/attempts changed')
    require(same(capture['prospective_limits'],dict(locators=15,seconds_per_invocation=45,bytes_per_response=4194304,total_raw_bytes=16777216)), 'Capture caps changed')
    rows = capture['captures']; total=0
    require(len(rows) == len({r['requested_url'] for r in rows}) == 11 and capture['retries'] == 0, 'Locator count/retry changed')
    require(capture['canonical_registration'] is capture['editorial_acceptance'] is False, 'Capture acquired authority')
    for row in rows:
        path = (ROOT/row['raw_path']).resolve()
        require(path.is_relative_to((P/'raw').resolve()), 'Raw path escaped')
        body = path.read_bytes(); total += len(body)
        require(len(body) == row['retained_bytes'] <= 4194304 and hashlib.sha256(body).hexdigest() == row['raw_sha256'], 'Raw capture changed')
        require(row['identity_accepted'] is True and row['status'] == 200 and row['final_url'] == row['requested_url']
                and not row['redirects'] and not row.get('error') and row['attempt_count'] == 1, 'Publisher identity/route changed')
    require(total == capture['total_retained_raw_bytes'] == 1950137, 'Raw accounting changed')
    return dict(invocations=11,accepted_bodies=11,retries=0,raw_bytes=total)


def validate_versions(pool, conformance, capture=None):
    from pypdf import PdfReader, __version__
    require(__version__ == '6.10.0', 'Use pinned PDF extraction dependency6.10.0')
    capture = capture or read(P/'capture_receipt.json')
    require(conformance['receipt_sha256'] == sealed_digest(conformance,'receipt_sha256')
            and conformance['binding_approved'] is conformance['binding_applied'] is False, 'Conformance acquired authority')
    require([c['bill'] for c in conformance['cases']] == [187,1917,6422], 'Wrong whole-motion set')
    for c in conformance['cases']:
        row = next(r for r in capture['captures'] if r['name'] == c['issue_name'])
        pages = [p.extract_text() for p in PdfReader(ROOT/row['raw_path']).pages];full='\n\n'.join(pages)
        require(len(pages) == c['pages'] and hashlib.sha256(full.encode()).hexdigest() == c['PDF_full_text_utf8_sha256']
                and (ROOT/c['full_extraction_path']).read_text(encoding='utf-8') == full, 'Full PDF extraction changed')
        texts = {u['role']:full[u['start']:u['end']] for u in c['selected_units']}
        require(pool[c['source_id']]['text'] == '\n\n'.join(texts.values()), 'Selected floor units changed')
        for u in c['selected_units']:
            require(hashlib.sha256(texts[u['role']].encode()).hexdigest() == u['utf8_sha256'], 'Selected extent changed')
        eh = pool[f"govinfo:hr{c['bill']}eh"]['text'];operative = eh[eh.index('Be it enacted'):eh.index('Passed the House')]
        compared,edits=compare_operative(operative,texts['operative_body'])
        require(edits == c['line_wrap_hyphen_comparisons'] and len(compared) == c['compared_glyphs']
                and hashlib.sha256(compared.encode()).hexdigest() == c['compared_glyphs_sha256'], 'Comparison receipt differs')
        motion=' '.join(texts['motion_excerpt'].split());initial=' '.join(texts['initial_question_postponement'].split())
        resumed=' '.join(texts['recorded_preface'].split());result=' '.join(texts['recorded_result'].split())
        require(f"{c['bill']}" in motion and 'as amended' in motion and 'suspend' in motion, 'Wrong own motion')
        require('yeas and nays' in initial and re.search(r'post(?:-\s*)?poned',initial), 'Preliminary voice result treated as final')
        require(str(c['bill']) in resumed and f"[Roll No. {c['roll']}]" in resumed and 'as amended' in resumed, 'Wrong resumed roll')
        require('two-thirds' in result and 'was passed' in result and 'as amended' in result and 'result of the vote' in result, 'Recorded passage result lost')
    return 3


def validate_qualifications(authoring):
    required = {
        187:['separately defines Federal waterways as waters managed by one or more of the relevant Secretaries','five named agencies','separate fishing-restriction definition','maximum extent practicable','as feasible','section4(a)/(b)','Section4 excludes','Section7 preserves','not new access rights'],
        776:['$12million','2021–2030','does not appropriate','Maryland-specific','75percent','5percent'],
        2215:['three years after funds are made available','does not itself expand boundaries','Salem Armory'],
        1917:['may purchase','specified fish-management agencies','$2.7million','2026–2030','not a claim of first-ever','not universally published'],
        6422:['$475million','2019–2031','2020 through2031','75percent per-project','only for assistance to nonfederal','FY2027 NEP funds','FY2024 plus $850000','such-sums-as-necessary','six enumerated','domiciled in, headquartered in, organized under the laws of, or with its principal place of business in','OR to any nonfederal entity for projects conducted with','alternative recipient-status or project conditions','eleven listed','not an adverse finding'],
    }
    for a in authoring['actions']:
        for field in ['meaning','compact_description']:
            for phrase in required[a['bill_number']]: require(phrase in a[field], 'Material qualification omitted: '+phrase)


def validate(data=None):
    d = inputs() if data is None else data;m=read(P/'packet_manifest.json')
    require(digest(m) == MANIFEST_SHA, 'Frozen manifest changed')
    for key,name in dict(authoring='authoring.json',sources='sources.json',preflight='preparation_preflight.json',bundle='decision_bundle.json',questions='source_questions.json',capture='capture_receipt.json',conformance='floor_version_conformance.json',extents='source_extraction_extents.json',proof='held_replay_proof.json').items():
        require(digest(d[key]) == m['object_sha256'][name], 'Frozen input drift: '+key)
    a,s,pre,b = (d[k] for k in ['authoring','sources','preflight','bundle'])
    require(pre['preflight_sha256'] == sealed_digest(pre,'preflight_sha256') and pre['base_commit'] == '28054311a295d54a1ae4392464e6c1ca8c967aaa', 'Wrong preflight')
    membership=read(BASE/'membership_review.json');universe=read(BASE/'universe_proposal.json');original=read(BASE/'sources.json')
    require(membership['review_sha256'] == pre['membership_seal'] and universe['proposal_sha256'] == pre['universe_seal'] and digest(original) == pre['source_pool_sha256'], 'Canonical149 changed')
    records={x['action_id']:x for x in membership['records']};rows={x['action_id']:x for x in universe['candidate_dispositions']}
    pool={x['source_id']:x for x in s['sources']};old={x['source_id']:x for x in original['sources']}
    require(len(pool) == len(s['sources']) == 23, 'Wrong isolated source inventory')
    for x in read(P/'retained_sources.json')['sources']: require(same(x,old[x['source_id']]) and same(x,pool[x['source_id']]), 'Original source changed')
    hp={x['source_id']:x for x in read(HEALTH/'sources.json')['sources']};pp={x['source_id']:x for x in read(PREVIOUS/'sources.json')['sources']}
    for x in read(P/'additional_preserved_sources.json')['sources']:
        src=x['source'];origin=hp if src['source_id'] in hp else pp
        require(digest(src) == x['object_sha256'] and same(src,origin[src['source_id']]) and same(src,pool[src['source_id']]), 'Reused primary witness changed')
    for ex in d['extents']['sources']:
        c=next(x for x in d['capture']['captures'] if x['name'] == ex['capture_name']);parser=Text();parser.feed((ROOT/c['raw_path']).read_text(encoding='utf-8'))
        full=' '.join(' '.join(parser.parts).split());text=full[ex['start']:ex['end']].strip()
        require(len(full) == ex['full_normalized_characters'] and text == pool[ex['source_id']]['text']
                and hashlib.sha256(text.encode()).hexdigest() == ex['governed_text_sha256'], 'Selected statutory extraction changed')
    require([x['action_id'] for x in pre['cases']] == [x['action_id'] for x in a['actions']] == [x['action_id'] for x in b['cases']] == ACTIONS, 'Exact case correspondence lost')
    require(a['blocked_episode_ids'] == ['episode:hr'+str(n)+':119' for n in BILLS], 'Episode hold removed')
    for case,action,decision,bill in zip(pre['cases'],a['actions'],b['cases'],BILLS):
        aid=case['action_id'];unresolved=bill in [187,1917,6422]
        require(same(records[aid],case['record']) and same(rows[aid],case['row']) and digest(records[aid]) == case['before_record_sha256'] and digest(rows[aid]) == case['before_row_sha256'], 'Canonical case preimage changed')
        require(records[aid]['disposition'] == 'pending_interpretation' and records[aid]['exact_action_binding_unresolved'] is unresolved
                and records[aid]['required_evidence_unavailable'] is records[aid]['authoritative_source_conflict'] is False, 'Pending/binding/source flag changed')
        require(action['bill_number'] == bill and action['stage'] == 'suspension_and_passage', 'Wrong exact choice')
        require(decision['canonical_binding_already_resolved'] is (not unresolved), 'Binding approval implied')
        for key in ['binding_approval_requested','binding_applied','meaning_accepted','eligibility_applied','canonical_sources_registered','source_holds_changed']:require(decision[key] is False, 'Decision acquired authority')
        require(decision['rationale'] and decision['strongest_counterevidence'], 'Missing independent rationale/counterevidence')
    require([x['recommendation'] for x in b['cases']] == ['propose_include_exact_case','propose_exclude_exact_case','route_exact_case_eligibility_review','propose_include_exact_case','propose_include_exact_case'], 'Proposed case decisions changed')
    require(b['bundle_sha256'] == sealed_digest(b,'bundle_sha256') and all(b[k] is False for k in ['accepted','canonical_application','publication','production']), 'Bundle acquired authority')
    validate_qualifications(a);conformed=validate_versions(pool,d['conformance'],d['capture']);actual=d['products']
    require(same(actual,replay(a,s)), 'Native held replay differs')
    core=actual['shared_action_core'];mapping=actual['shared_issue_mapping'];validate_shared_action_core(ROOT,core);validate_shared_issue_mapping(ROOT,mapping,core)
    for decision,action in zip(b['cases'],core['actions']):require(decision['candidate_core_sha256'] == action['action_core_sha256'] and decision['meaning_ref'] == action['action_meaning_ref'], 'Decision subject differs')
    for p in actual['member_projections']:
        validate_member_projection(ROOT,p,core);expected=['Yea']*5 if p['member_id']=='F000477' else ['Yea','Nay','Nay','Nay','Nay']
        require([x['official_status'] for x in p['actions']] == expected, 'Official observation changed')
    require(all(not m['proposition_graph']['propositions'] for m in actual['compiled_ir']['members']), 'Held choice generated proposition')
    require(d['proof']['product_sha256'] == {k:digest(v) for k,v in actual.items()} and d['proof']['behavioral_update_proof_exercised'] is False, 'Replay proof overclaims')
    return dict(cores=5,official_observations=10,sources=23,issue_propositions=0,whole_motion_conformances=conformed,canonical149_changed=False,binding_or_meaning_accepted=False,capture=validate_capture(d['capture']))


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(),packet_files=validate_manifest(),validation=validate()),indent=2))
