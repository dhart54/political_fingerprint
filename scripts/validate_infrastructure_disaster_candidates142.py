"""Authenticate isolated five-case research and replay existing typed contracts.

No network access, canonical admission, acceptance, or publication operation.
"""
import base64
import gzip
import hashlib
import io
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates
from scripts.validate_infrastructure_hr859_scope137 import TextParser

PACKET = ROOT / 'docs/review_packets/infrastructure_batch142_disaster_baselines'
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch139_20260916'
MEMBERS = ['F000477', 'M001184']
ACTIONS = ['house:119:1:'+str(n) for n in [9, 10, 13, 49, 88]]
OUTPUTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
           'compiler_input', 'compiled_ir', 'readable_candidates']
BUNDLE_SHA = '5ae115e381d009896db611688182d6c273bbcf293b05dbf1765bde8487ad6003'
MANIFEST_SHA = '86c4db968f8a2d0d6e4a11d7591d3131db876e99ef787c8362b3df60c68749c2'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized_pdf(text):
    return ' '.join(re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', text).split())


def reconstruct_capture(capture, packet=PACKET):
    """Reconstruct preserved responses, rejecting escaped/changed part payloads."""
    c = capture
    require(c['http_status'] == 200 and c['attempt_number'] == 1
            and c['transport_error'] is None and c['body_exceeds_cap'] is False
            and c['source_registered'] is c['canonical_state_changed'] is False,
            'Capture status, attempt or authority differs')
    encoded = c.get('raw_response_base64')
    if encoded is None:
        chunks = []
        for i, meta in enumerate(c['raw_response_base64_parts']):
            path = (ROOT / meta['path']).resolve()
            require(path.parent == packet.resolve() and meta['index'] == i,
                    'Capture part path or order differs')
            part = read(path)
            require(part['index'] == i and len(part['data']) == part['characters'] == meta['characters']
                    and sha(part['data'].encode()) == part['sha256'] == meta['sha256'],
                    'Capture part bytes differ')
            chunks.append(part['data'])
        encoded = ''.join(chunks)
        require(len(encoded) == c['raw_response_base64_characters'], 'Capture part total differs')
    body = base64.b64decode(encoded, validate=True)
    require(c['raw_response_encoding'] in {'base64', 'gzip+base64'}, 'Capture encoding differs')
    if c['raw_response_encoding'] == 'gzip+base64':
        body = gzip.decompress(body)
    require(len(body) == c['raw_response_bytes'] and sha(body) == c['raw_response_sha256'],
            'Original response bytes differ')
    return body


def validate_transport():
    receipt = read(PACKET / 'packet_manifest.json')
    require(digest(receipt) == MANIFEST_SHA, 'Frozen packet manifest differs')
    actual = {p.relative_to(PACKET).as_posix() for p in PACKET.rglob('*') if p.is_file()
              and p.name != 'packet_manifest.json'}
    require(actual == set(receipt['files']), 'Packet file cohort differs')
    for name, item in receipt['files'].items():
        path = (PACKET / name).resolve()
        require(path.is_relative_to(PACKET.resolve()), 'Packet path escaped')
        body = path.read_bytes().replace(b'\r\n', b'\n')
        require(len(body) == item['bytes'] < 195000 and sha(body) == item['lf_sha256'],
                'Frozen LF packet bytes differ: '+name)
    for name, expected in receipt['canonical_baseline_files'].items():
        body = (BASE / name).read_bytes().replace(b'\r\n', b'\n')
        require(sha(body) == expected, 'Canonical baseline changed: '+name)
    return len(actual)


def validate_sources(capture=None, units=None):
    from pypdf import PdfReader
    s = read(PACKET / 'sources.json') if capture is None else capture
    u = read(PACKET / 'source_units.json') if units is None else units
    pool = {x['source_id']: x for x in s['sources']}
    require(len(pool) == len(s['sources']) == 24, 'Isolated source inventory differs')
    old = {x['source_id']: x for x in read(BASE / 'sources.json')['sources']}
    retained = [x for x in s['sources'] if x['source_id'] in old]
    require(len(retained) == 11 and all(x == old[x['source_id']] for x in retained),
            'Retained sources changed')
    captures = {f.name.removesuffix('_capture.json'): read(f) for f in PACKET.glob('*_capture.json')}
    require(len(captures) == u['raw_HTTP_attempts'] == 12
            and sum(c['raw_response_bytes'] for c in captures.values()) == u['total_raw_response_bytes'] == 3472019,
            'Response/attempt accounting differs')
    texts, pages = {}, {}
    qa = read(PACKET / 'pdf_page_review.json')
    require(len(qa['pages']) == 3 and qa['original_PDFs_unchanged'] is True
            and qa['other_PDF_pages_claimed_reviewed'] is False, 'PDF review boundary differs')
    for key, c in captures.items():
        require(c['requested_url'] == c['final_url'] and c['requested_url'].startswith('https://www.govinfo.gov/content/pkg/'),
                'Official source route differs')
        raw = reconstruct_capture(c)
        if c.get('format') == 'pdf':
            reader = PdfReader(io.BytesIO(raw))
            for page in [p for p in qa['pages'] if p['capture_key'] == key]:
                text = reader.pages[page['one_based_pdf_page']-1].extract_text()
                require(text == page['raw_page_text'] and sha(text.encode()) == page['raw_page_text_sha256']
                        and sha(normalized_pdf(text).encode()) == page['normalized_page_text_sha256']
                        and page['visual_read_completed'] is True, 'Selected PDF page extraction differs')
                pages[(key, page['one_based_pdf_page'])] = normalized_pdf(text)
        else:
            parser = TextParser(); parser.feed(raw.decode('utf8'))
            text = ' '.join(' '.join(parser.parts).split())
            require(len(text) == c['normalized_text_characters']
                    and sha(text.encode()) == c['normalized_text_sha256'], 'Raw-to-HTML text differs')
            if 'normalized_text' in c:
                require(text == c['normalized_text'], 'Retained normalized text differs')
            texts[key] = text
    require(len(u['units']) == u['selected_context_sources'] == 13
            and u['retained_objects'] == 11, 'Selected unit inventory differs')
    for unit in u['units']:
        source = pool[unit['source_id']]; key = unit['capture_key']; c = captures[key]
        require(unit['whole_document_reviewed'] is False and source['url'] == c['requested_url']
                and source['raw_sha256'] == c['raw_response_sha256']
                and source['governed_bytes_sha256'] == sealed_digest(source, 'governed_bytes_sha256')
                and unit['source_object_sha256'] == digest(source), 'Selected source identity differs')
        if 'source_extent' in unit:
            e = unit['source_extent']
            require(e['total'] == len(texts[key]) and 0 <= e['start'] < e['end'] <= e['total'], 'HTML extent differs')
            text = texts[key][e['start']:e['end']]
        else:
            selected = [pages[(key, e['page'])][e['start']:e['end']] for e in unit['pdf_normalized_page_extents']]
            text = (unit['page_join_marker'] or '').join(selected)
        require(text == source['text'] and sha(text.encode()) == unit['passage_sha256'], 'Selected source passage differs')
    return s


def validate(authoring=None, bundle=None, outputs=None):
    a = read(PACKET / 'authoring.json') if authoring is None else authoring
    b = read(PACKET / 'decision_bundle.json') if bundle is None else bundle
    s = validate_sources()
    require(digest(b) == BUNDLE_SHA, 'Frozen content-bound decision subject differs')
    require(b['bundle_sha256'] == sealed_digest(b, 'bundle_sha256'), 'Decision bundle seal differs')
    require(digest(a) == b['authoring_sha256'] and digest(s) == b['source_pool_sha256'], 'Candidate input subject differs')
    require([x['action_id'] for x in a['actions']] == [x['action_id'] for x in b['cases']] == ACTIONS,
            'Five-action cohort differs')
    for key in ['canonical_state_changed', 'semantic_acceptance', 'source_registered', 'publication_authorized',
                'production_authorized', 'approved_universe_or_full_issue_claim', 'prior_HR859_or_HR28_decision_changed',
                'six_source_holds_changed', 'issue_propositions_authorized']:
        require(b[key] is False, 'Candidate gained authority: '+key)
    require(b['baseline_accounting'] == dict(records=676,sources=1621,authored_meanings=70,pending=260,
                                           ineligible=122,source_holds=6,ordinary_unscreened=0), 'Baseline accounting differs')
    records = {r['action_id']:r for r in read(BASE / 'membership_review.json')['records']}
    rows = {r['action_id']:r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions']}
    pool = {x['source_id']:x for x in s['sources']}
    require(a['blocked_episode_ids'] == [x['episode_id'] for x in a['actions']], 'An eligibility hold was removed')
    for i, case in enumerate(b['cases']):
        aid = case['action_id']; record = records[aid]
        require(case['candidate_sha256'] == sealed_digest(case, 'candidate_sha256')
                and digest(record) == case['governed_before_record_sha256']
                and digest(rows[aid]) == case['governed_before_row_sha256']
                and record['disposition'] == 'pending_interpretation'
                and record['exact_action_binding_unresolved'] is (aid == ACTIONS[-1]), 'Case preimage/binding differs')
        require(case['eligibility_accepted'] is case['canonical_binding_changed'] is False
                and case['strongest_case_specific_counterevidence'] and case['requested_content_bound_decision'],
                'Case review gate lost')
        clerk = pool['clerk:'+aid.removeprefix('house:')]
        require(case['actual_official_member_records'] == {m:clerk['member_records'][m] for m in MEMBERS},
                'Official member observation differs')
    core, mapping, projections, inputs, result = prepare(a, s, MEMBERS)
    expected = dict(shared_action_core=core,shared_issue_mapping=mapping,member_projections=projections,
                    compiler_input=inputs,compiled_ir=result.compiled_ir,
                    readable_candidates=readable_candidates(a,core,projections,result))
    actual = {k:read(PACKET/'generated'/(k+'.json')) for k in OUTPUTS} if outputs is None else outputs
    require(digest(actual) == digest(expected), 'Typed candidate replay differs')
    require(result.validation['proposition_count'] == 0
            and result.validation['source_render_constraint_count'] == 1
            and mapping['authoritative_for_new_editorial_work'] is False
            and expected['readable_candidates']['production_eligible'] is False,
            'Held candidates acquired behavioral or production authority')
    for p, statuses in zip(projections,[['Yea']*5,['Yea','Yea','Nay','Yea','Yea']]):
        require([x['official_status'] for x in p['actions']] == statuses, 'Official choices changed')
    receipt=read(PACKET/'generated/replay_receipt.json')
    require(receipt['input_sha256']==digest(a) and receipt['capture_sha256']==digest(s)
            and receipt['output_sha256']=={k:digest(v) for k,v in expected.items()}
            and receipt['canonical_mutation'] is receipt['semantic_acceptance'] is receipt['publication_authorized'] is False,
            'Replay receipt differs')
    binding = read(PACKET/'amended_binding_review.json')
    require(binding['binding_candidate_sha256'] == sealed_digest(binding, 'binding_candidate_sha256')
            and binding['canonical_binding_changed'] is binding['acceptance_authorized'] is False,
            'Amended binding candidate authority differs')
    for clause in binding['clause_comparisons']:
        require(clause['verbatim_in_both'] is True
                and clause['passage'] in pool[clause['March31_source_id']]['text']
                and clause['passage'] in pool[clause['EH_source_id']]['text'], 'Operative EH/floor clause differs')
    for step in binding['floor_sequence']:
        require(step['passage'] in pool[step['source_id']]['text'], 'Amended motion sequence differs')
    sba = next(x for x in a['actions'] if x['bill_number']==804)
    require(any(x['locator'].startswith('sba7b:rural16;') and 'rural area' in x['passage'] for x in sba['claim_source_map'])
            and any(x['locator'].startswith('sba7b:limitations16;') and 'COVID' in x['passage'] for x in sba['claim_source_map']),
            'Distinct printed SBA16 source units lost')
    return dict(actions=5,shared_cores=5,official_member_observations=10,source_objects=24,
                context_units=13,raw_responses=12,issue_propositions=0,canonical_state_changed=False)


if __name__ == '__main__':
    print(json.dumps(dict(packet_files=validate_transport(),candidate=validate()),indent=2))
