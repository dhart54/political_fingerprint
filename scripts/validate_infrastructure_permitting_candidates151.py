"""Offline validation of held151 source/version choices; grants no authority."""
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import (
    digest, sealed_digest, validate_shared_action_core, validate_shared_issue_mapping,
    validate_member_projection,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT/'docs/review_packets/infrastructure_batch151_permitting'
BASE = ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch149_20260916'
HEALTH = ROOT/'docs/editorial/shared_candidates/house_119_health_20260916'
ACTIONS = ['house:119:1:'+str(n) for n in [330, 352, 353, 354, 356]]
MEMBERS = ['F000477', 'M001184']
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections', 'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = 'a5bf76b207b03ca04990682254f7b029c4a61c41a31fb5c58e2b0d02d597d173'
PRESERVATION_SHA = 'a85c36c0eeb3d55c4130e93fb23832b6d7b9286e5474bbc698a10e4aec952021'


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def require(value, message):
    if not value: raise ValueError(message)
def same(a, b): return digest(a) == digest(b)
def lfhash(path): return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []; self.preparts = []; self.pre = False
    def handle_starttag(self, tag, attrs):
        if tag == 'pre': self.pre = True
    def handle_endtag(self, tag):
        if tag == 'pre': self.pre = False
    def handle_data(self, text):
        self.parts.append(text)
        if self.pre: self.preparts.append(text)


def validate_manifest():
    m = read(P/'packet_manifest.json')
    require(digest(m) == MANIFEST_SHA and m['manifest_sha256'] == sealed_digest(m, 'manifest_sha256'), 'Frozen packet manifest drift')
    for name, entry in m['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(P.resolve()), 'Packet path escaped')
        raw = path.read_bytes()
        if entry['mode'] == 'lf': raw = raw.replace(b'\r\n', b'\n')
        require(hashlib.sha256(raw).hexdigest() == entry['sha256'] and len(raw) == entry['bytes'], 'Frozen packet bytes differ: '+name)
    return len(m['files'])


def validate_preservation():
    m = read(P/'preservation_manifest.json')
    require(digest(m) == PRESERVATION_SHA and m['manifest_sha256'] == sealed_digest(m, 'manifest_sha256'), 'Preservation manifest drift')
    for name, entry in m['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT.resolve()), 'Preservation path escaped')
        raw = path.read_bytes()
        if entry['mode'] == 'lf': raw = raw.replace(b'\r\n', b'\n')
        require(hashlib.sha256(raw).hexdigest() == entry['sha256'] and len(raw) == entry['bytes'], 'Preserved predecessor changed: '+name)
    return len(m['files'])


def inputs():
    return {'authoring': read(P/'authoring.json'), 'sources': read(P/'sources.json'),
            'preflight': read(P/'preparation_preflight.json'), 'bundle': read(P/'decision_bundle.json'),
            'questions': read(P/'source_questions.json'), 'capture': read(P/'capture_receipt.json'),
            'version': read(P/'version_reconciliation.json'), 'conformance': read(P/'3898_floor_conformance.json'),
            'proof': read(P/'held_replay_proof.json'),
            'products': {n: read(P/'generated'/(n+'.json')) for n in PRODUCTS}}


def replay(authoring, sources):
    core, mapping, projections, compiler, result = prepare(authoring, sources, MEMBERS)
    return dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                compiler_input=compiler, compiled_ir=result.compiled_ir,
                readable_candidates=readable_candidates(authoring, core, projections, result))


def validate_capture(capture):
    expected = read(P/'packet_manifest.json')['object_sha256']['capture_receipt.json']
    require(digest(capture) == expected, 'Capture contract or exact attempts changed')
    require(same(capture['prospective_limits'], {'locators': 15, 'seconds_per_invocation': 45,
                'bytes_per_response': 4194304, 'total_raw_bytes': 16777216}), 'Capture envelope changed')
    rows = capture['captures']; urls = [r['requested_url'] for r in rows]
    require(len(rows) == len(set(urls)) == 13 and capture['retries'] == 0, 'Retried, omitted or expanded locator')
    require(capture['canonical_registration'] is capture['editorial_acceptance'] is False, 'Capture acquired authority')
    require([r['name'] for r in rows if not r['identity_accepted']] ==
            ['42usc4321-2024', '3898-floor-H5768', '3898-floor-H5790', '3898-Record-package-metadata'], 'Closed route changed')
    total = 0
    for row in rows:
        path = (ROOT/row['raw_path']).resolve()
        require(path.is_relative_to((P/'raw').resolve()), 'Capture path escaped')
        body = path.read_bytes(); total += len(body)
        require(len(body) == row['retained_bytes'] <= 4194304 and hashlib.sha256(body).hexdigest() == row['raw_sha256'], 'Capture body changed')
        if row['identity_accepted']:
            require(row['status'] == 200 and row['final_url'] == row['requested_url'] and not row['redirects'] and not row.get('error'), 'Accepted publisher identity changed')
        else:
            require(bool(row.get('error')), 'Rejected locator silently accepted')
    require(total == capture['total_retained_raw_bytes'] == 5051071, 'Raw capture accounting changed')
    from pypdf import PdfReader
    for name, pages, page in [('3898-floor-H5768-2', 1, 'H5768'), ('3898-floor-H5793', 2, 'H5793')]:
        row = next(r for r in rows if r['name'] == name)
        texts = [p.extract_text() for p in PdfReader(ROOT/row['raw_path']).pages]
        full = ' '.join('\n'.join(texts).split())
        require(len(texts) == pages == row['PDF_pages'] and page in full and '3898' in full
                and 'December 11, 2025' in full and 'PROMOTING EFFICIENT REVIEW' in full, 'Selected physical PDF identity changed')
    return {'invocations': 13, 'accepted_bodies': 9, 'rejected_routes': 4, 'raw_bytes': total}


def normalized(text):
    text = re.sub(r'\[\[Page [^]]+\]\]', '', text)
    text = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '-', text)
    return ' '.join(text.split()).replace('-- ', '--')


def sections(text, end):
    starts = list(re.finditer(r'(?:SECTION|SEC\.) (\d+)\.', text))
    return {int(m[1]): normalized(text[m.start():starts[i+1].start() if i+1 < len(starts) else end]) for i,m in enumerate(starts)}


def validate_versions(pool, conformance):
    rh = pool['govinfo:hr4776rh']['text']; eh = pool['govinfo:hr4776eh']['text']
    require(rh[rh.index('SECTION 1.'):rh.rindex('Union Calendar')].strip() ==
            eh[eh.index('SECTION 1.'):eh.index('SEC. 4.')].strip(), '4776 RH/EH sections1–3 differ')
    section4 = eh[eh.index('SEC. 4.'):eh.index('Passed the House')].strip()
    require(section4 in pool['govinfo:hres953eh']['text'] and 'January 20, 2025' in section4
            and 'regardless of whether' in section4, '4776 whole section4/HRes953 binding lost')
    rh = pool['govinfo:permitting151:hr3898rh']['text']; eh = pool['govinfo:hr3898eh']['text']
    floor = pool['govinfo:permitting151:3898-PERMIT-article']['text']
    before = sections(rh, rh.rindex('Union Calendar')); after = sections(eh, eh.index('Passed the House'))
    start = floor.index('SECTION 1.'); end = floor.index('  The Acting CHAIR. No further amendment', start)
    require(before == sections(floor[start:end], end-start), '3898 printed substitute differs from RH')
    heads = list(re.finditer(r'Amendment No\. ([1-8]) Offered', floor)); edits = {}; units = []
    for i,m in enumerate(heads):
        end = heads[i+1].start() if i+1 < len(heads) else len(floor); chunk = floor[m.start():end]
        start = chunk.index('The text of the amendment is as follows:')+len('The text of the amendment is as follows:')
        finish = chunk.index('  The Acting CHAIR.', start); outcome = chunk.index('The amendment was agreed to.')
        edits[int(m[1])] = normalized(chunk[start:finish])
        units.append((int(m[1]), m.start()+start, m.start()+finish, m.start()+outcome))
    require(list(edits) == [1,2,3,4,6,7,8] and 'amendment No. 5 will not be offered.' in floor, '3898 actual offerings/outcomes differ')
    reconstructed = {n:s for n,s in before.items() if 2 <= n <= 15}
    require(reconstructed[5].endswith("annually.''."), '3898 amendment2 target missing')
    reconstructed[5] = reconstructed[5][:-len("annually.''.")]+"annually. "+edits[2][edits[2].index('``(h)'):]
    for old,new in [(16,17),(17,19),(18,20),(19,21),(20,22),(21,23)]:
        reconstructed[new] = before[old].replace(f'SEC. {old}.', f'SEC. {new}.', 1)
    reconstructed[20] = reconstructed[20].replace('five years', 'ten years')
    for amendment,number in [(1,16),(6,18),(4,24),(7,25),(8,26)]:
        text = edits[amendment][edits[amendment].index('SEC. '):]
        reconstructed[number] = re.sub(r'^SEC\. (?:__|22)\.', f'SEC. {number}.', text, count=1)
    require(all(reconstructed[n] == after[n] for n in range(2,27)), '3898 RH/amendments do not reconstruct whole EH operative sections')
    for actual, recorded in zip(units, conformance['amendment_units']):
        require(actual == (recorded['amendment'], recorded['legal_start'], recorded['legal_end'], recorded['outcome_start']), 'Recorded floor extent changed')
    require(conformance['receipt_sha256'] == sealed_digest(conformance, 'receipt_sha256')
            and conformance['binding_applied_or_approved'] is False and conformance['canonical_binding_unresolved'] is True, 'Conformance acquired binding authority')
    return 25


def validate(data=None):
    d = inputs() if data is None else data; manifest = read(P/'packet_manifest.json')
    require(digest(manifest) == MANIFEST_SHA, 'Frozen manifest changed')
    files = {'authoring':'authoring.json', 'sources':'sources.json', 'preflight':'preparation_preflight.json',
             'bundle':'decision_bundle.json', 'questions':'source_questions.json', 'capture':'capture_receipt.json',
             'version':'version_reconciliation.json', 'conformance':'3898_floor_conformance.json', 'proof':'held_replay_proof.json'}
    for key,name in files.items(): require(digest(d[key]) == manifest['object_sha256'][name], 'Frozen input drift: '+key)
    a,s,pre,bundle = (d[k] for k in ['authoring','sources','preflight','bundle'])
    require(pre['preflight_sha256'] == sealed_digest(pre, 'preflight_sha256') and pre['base_commit'] == '3054ae67740759a14a8548d8b30c5ae21fc056df', 'Wrong current preimages')
    membership = read(BASE/'membership_review.json'); universe = read(BASE/'universe_proposal.json'); original = read(BASE/'sources.json')
    require(membership['review_sha256'] == pre['membership_seal'] and universe['proposal_sha256'] == pre['universe_seal']
            and digest(original) == pre['source_pool_sha256'], 'Canonical149 changed')
    records = {r['action_id']:r for r in membership['records']}; rows = {r['action_id']:r for r in universe['candidate_dispositions']}
    pool = {r['source_id']:r for r in s['sources']}; oldpool = {r['source_id']:r for r in original['sources']}
    healthpool = {r['source_id']:r for r in read(HEALTH/'sources.json')['sources']}
    retained = read(P/'retained_sources.json')['sources']; extra = read(P/'additional_preserved_sources.json')['sources']
    require(len(pool) == len(s['sources']) == 43 and len(retained) == 27 and len(extra) == 9, 'Isolated source inventory changed')
    for source in retained: require(same(pool[source['source_id']], source) and same(source, oldpool[source['source_id']]), 'Original27 source object changed')
    for entry in extra:
        source = entry['source']; origin = oldpool if entry['origin'] == 'current149' else healthpool
        require(digest(source) == entry['object_sha256'] and same(source, origin[source['source_id']]) and same(source, pool[source['source_id']]), 'Additional existing witness changed')
    new = [x for x in s['sources'] if x['source_id'].startswith('govinfo:permitting151:')]
    require(len(new) == 7, 'New source inventory changed')
    for source in new:
        capture = next(c for c in d['capture']['captures'] if c['requested_url'] == source['url'] and c['identity_accepted'])
        parser = Text(); parser.feed((ROOT/capture['raw_path']).read_text(encoding='utf-8'))
        full = ''.join(parser.preparts).replace('\r\n','\n') if source['source_type'] == 'congressional_record' else ' '.join(' '.join(parser.parts).split())
        if source['source_type'] == 'congressional_record': expected = full
        else:
            extent = source['source_text_extents'][0]; require(len(full) == extent['total'], 'Material source full length differs')
            expected = full[extent['start']:extent['end']].strip()
        require(source['text'] == expected and source['raw_sha256'] == capture['raw_sha256']
                and source['governed_bytes_sha256'] == sealed_digest(source, 'governed_bytes_sha256'), 'New source extraction or identity changed')
    require([c['action_id'] for c in pre['cases']] == [c['action_id'] for c in bundle['cases']] == [c['action_id'] for c in a['actions']] == ACTIONS, 'Five case correspondence differs')
    require(a['blocked_episode_ids'] == ['episode:hr3898:119','episode:hr4776:119'], 'Episode hold lost')
    for i,(case,action,decision) in enumerate(zip(pre['cases'], a['actions'], bundle['cases'])):
        aid = case['action_id']; unresolved = i in (0,4)
        require(digest(records[aid]) == case['before_record_sha256'] and digest(rows[aid]) == case['before_row_sha256']
                and same(records[aid],case['record']) and same(rows[aid],case['row']), 'Exact record/row preimage changed')
        require(records[aid]['disposition'] == 'pending_interpretation' and records[aid]['exact_action_binding_unresolved'] is unresolved
                and records[aid]['required_evidence_unavailable'] is records[aid]['authoritative_source_conflict'] is False, 'Canonical pending/binding/source flags changed')
        require(action['bill_number'] == (3898 if i == 0 else 4776) and action['stage'] == ('final_passage' if unresolved else 'amendment'), 'Exact stage/bill differs')
        require(decision['canonical_binding_already_resolved'] is (not unresolved), 'Candidate claims binding acceptance')
        for key in ['binding_approval_requested','binding_applied','meaning_accepted','eligibility_applied','canonical_sources_registered','source_holds_changed']:
            require(decision[key] is False, 'Decision acquired authority: '+key)
    require(bundle['bundle_sha256'] == sealed_digest(bundle,'bundle_sha256') and all(bundle[k] is False for k in ['accepted','canonical_application','publication','production']), 'Bundle acquired authority')
    conformed = validate_versions(pool, d['conformance']); actual = d['products']; expected = replay(a,s)
    require(same(actual, expected), 'Typed products differ from actual held replay')
    core = actual['shared_action_core']; mapping = actual['shared_issue_mapping']
    validate_shared_action_core(ROOT,core); validate_shared_issue_mapping(ROOT,mapping,core)
    require(core['authoritative_for_new_editorial_work'] is mapping['authoritative_for_new_editorial_work'] is False, 'Candidate authority changed')
    for decision,action in zip(bundle['cases'],core['actions']):
        require(decision['candidate_core_sha256'] == action['action_core_sha256'] and decision['meaning_ref'] == action['action_meaning_ref'], 'Decision subject differs')
    for projection in actual['member_projections']:
        validate_member_projection(ROOT,projection,core); status = 'Nay' if projection['member_id'] == 'F000477' else 'Yea'
        require(len(projection['actions']) == 5 and all(r['official_status'] == status for r in projection['actions']), 'Official member observation changed')
    require(all(not m['proposition_graph']['propositions'] for m in actual['compiled_ir']['members']), 'Held action generated proposition')
    require(d['proof']['product_sha256'] == {k:digest(v) for k,v in actual.items()} and d['proof']['behavioral_update_proof_exercised'] is False, 'Held proof overclaims')
    return {'cores':5,'official_observations':10,'sources':43,'issue_propositions':0,'3898_operative_sections_conformed':conformed,
            'canonical149_changed':False,'binding_or_meaning_accepted':False,'capture':validate_capture(d['capture'])}


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(),packet_files=validate_manifest(),validation=validate()),indent=2))
