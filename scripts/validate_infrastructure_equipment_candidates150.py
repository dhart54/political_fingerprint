"""Offline held-candidate replay and exact source/preservation checks for150."""
import copy
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
    validate_member_projection, candidate_update_impact, SharedCorpusValidationError,
)
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

P = ROOT/'docs/review_packets/infrastructure_batch150_equipment_rule_disapprovals'
BASE = ROOT/'docs/editorial/shared_candidates/house_119_infrastructure_batch149_20260916'
ACTIONS = ['house:119:1:53', 'house:119:1:59', 'house:119:1:77', 'house:119:1:78', 'house:119:1:58']
NUMBERS = [20, 42, 24, 75, 61]
DOCS = ['2024-30369', '2024-21950', '2024-28474', '2024-31214', '2024-26895']
CITATIONS = ['89FR105188', '89FR81994', '89FR104616', '90FR7464', '89FR94886']
NAMES = ['water-heater', 'certification', 'walk-in', 'commercial-refrigeration', 'rubber-tire']
MEMBERS = ['F000477', 'M001184']
PRODUCTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections', 'compiler_input', 'compiled_ir', 'readable_candidates']
MANIFEST_SHA = 'b180bbb1cb3667be6657229a5483c79c7564b36d5d41e053af2b4738a3a0d6e7'
PRESERVATION_SHA = '0db391db56ea88f618fb577a6e3fee414524d101bb14af37da6289e2872df57b'


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def require(value, message):
    if not value: raise ValueError(message)
def same(a, b): return digest(a) == digest(b)
def lfhash(path): return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


class RuleText(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []; self.pre = False
    def handle_starttag(self, tag, attrs):
        if tag == 'pre': self.pre = True
    def handle_endtag(self, tag):
        if tag == 'pre': self.pre = False
    def handle_data(self, text):
        if self.pre: self.parts.append(text)


def validate_preservation():
    m = read(P/'preservation_manifest.json')
    require(digest(m) == PRESERVATION_SHA and m['manifest_sha256'] == sealed_digest(m, 'manifest_sha256'), 'Historical preservation manifest drift')
    for name, expected in m['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT.resolve()) and lfhash(path) == expected, 'Preserved predecessor changed: '+name)
    return len(m['files'])


def validate_manifest():
    m = read(P/'packet_manifest.json')
    require(digest(m) == MANIFEST_SHA and m['manifest_sha256'] == sealed_digest(m, 'manifest_sha256'), 'Frozen packet manifest drift')
    for name, expected in m['files'].items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(P.resolve()), 'Packet manifest path escaped')
        raw = path.read_bytes()
        if expected['mode'] == 'lf': raw = raw.replace(b'\r\n', b'\n')
        require(hashlib.sha256(raw).hexdigest() == expected['sha256'] and len(raw) == expected['bytes'], 'Frozen packet bytes drift: '+name)
    return len(m['files'])


def inputs():
    return {'authoring': read(P/'authoring.json'), 'sources': read(P/'sources.json'),
            'preflight': read(P/'preparation_preflight.json'), 'bundle': read(P/'decision_bundle.json'),
            'questions': read(P/'source_questions.json'), 'capture': read(P/'capture_receipt.json'),
            'proof': read(P/'held_replay_proof.json'),
            'products': {n: read(P/'generated'/(n+'.json')) for n in PRODUCTS}}


def validate_capture(capture):
    require(same(capture['prospective_limits'], {'locators': 15, 'seconds_per_invocation': 45, 'bytes_per_response': 4194304, 'total_raw_bytes': 16777216}), 'Capture envelope changed')
    require(capture['canonical_registration'] is capture['editorial_acceptance'] is False, 'Capture acquired editorial authority')
    rows = capture['captures']; urls = [r['requested_url'] for r in rows]
    require(len(rows) == len(set(urls)) == 9, 'Duplicate, omitted or retried capture locator')
    require([r['name'] for r in rows] == NAMES + ['certification-pdf', 'walk-in-pdf', 'commercial-refrigeration-pdf', 'rubber-tire-pdf'], 'Capture cohort differs')
    days = ['2024-12-26', '2024-10-09', '2024-12-23', '2025-01-21', '2024-11-29']
    expected_urls = [f'https://www.govinfo.gov/content/pkg/FR-{day}/html/{doc}.htm' for day,doc in zip(days,DOCS)]
    expected_urls += [f'https://www.govinfo.gov/content/pkg/FR-{days[i]}/pdf/{DOCS[i]}.pdf' for i in [1,2,3,4]]
    require(urls == expected_urls, 'Capture locator version or route changed')
    total = 0
    for row in rows:
        path = (ROOT/row['raw_path']).resolve()
        require(path.is_relative_to((P/'raw').resolve()), 'Capture path escaped')
        body = path.read_bytes(); total += len(body)
        require(row['status'] == 200 and row['redirects'] == [] and row['final_url'] == row['requested_url']
                and len(body) == row['retained_bytes'] <= 4194304
                and hashlib.sha256(body).hexdigest() == row['raw_sha256'], 'Capture bytes or publisher identity drift')
        if row['name'] in ['walk-in-pdf', 'commercial-refrigeration-pdf']:
            require(row['identity_accepted'] is False and not body
                    and int(row['headers']['Content-Length']) > 4194304
                    and row['error'] == 'RuntimeError: Declared body exceeds capture cap; not read', 'Closed over-cap PDF route changed')
        else:
            require(row['identity_accepted'] is True and not row.get('error'), 'Accepted source became a rejected capture')
    require(total == capture['total_retained_raw_bytes'] == 5355713 and total < 16777216, 'Total capture bytes differ')
    # Authenticate the two retained PDFs independently of publisher URL metadata.
    from pypdf import PdfReader
    norm = lambda text: ' '.join(text.replace('\u2013', '-').replace('\u2014', '-').split()).casefold()
    for row in rows:
        if row['name'] not in ['certification-pdf', 'rubber-tire-pdf']: continue
        pages = [p.extract_text() for p in PdfReader(ROOT/row['raw_path']).pages]
        require(len(pages) == row['PDF_pages'] and row['document_identity_verified_from_complete_PDF_text'] is True
                and row['document_identity_verification_pending'] is False
                and norm(row['expected_document']) in norm('\n'.join(pages))
                and row['expected_page'] in pages[0]
                and norm(row['expected_title']) in norm('\n'.join(pages[:2])), 'Retained PDF document identity differs')
    return {'attempts': 9, 'retained_bodies': 7, 'closed_overcap_PDFs': 2, 'raw_bytes': total}


def replay(authoring, sources):
    core, mapping, projections, compiler, result = prepare(authoring, sources, MEMBERS)
    return dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                compiler_input=compiler, compiled_ir=result.compiled_ir,
                readable_candidates=readable_candidates(authoring, core, projections, result))


def validate(data=None):
    d = inputs() if data is None else data
    m = read(P/'packet_manifest.json')
    require(digest(m) == MANIFEST_SHA, 'Frozen packet manifest drift')
    # Authenticate semantic input objects independently of their self-seals.
    for key, name in [('authoring','authoring.json'), ('sources','sources.json'), ('preflight','preparation_preflight.json'),
                      ('bundle','decision_bundle.json'), ('questions','source_questions.json'), ('capture','capture_receipt.json'), ('proof','held_replay_proof.json')]:
        require(digest(d[key]) == m['object_sha256'][name], 'Frozen input drift: '+key)
    a, s, pre, bundle = (d[k] for k in ['authoring','sources','preflight','bundle'])
    require(pre['preflight_sha256'] == sealed_digest(pre, 'preflight_sha256') and pre['base_commit'] == '5ab0233a449b2cda7db574584ee99c29783afd51', 'Wrong current149 preflight')
    require([r['action_id'] for r in pre['cases']] == [x['action_id'] for x in a['actions']] == ACTIONS, 'Wrong action cohort')
    require(a['blocked_episode_ids'] == [x['episode_id'] for x in a['actions']] and len(set(a['blocked_episode_ids'])) == 5, 'A held episode was released or merged')
    current_m = read(BASE/'membership_review.json'); current_u = read(BASE/'universe_proposal.json'); canonical = read(BASE/'sources.json')
    require(current_m['review_sha256'] == sealed_digest(current_m, 'review_sha256') == pre['membership_seal']
            and current_u['proposal_sha256'] == sealed_digest(current_u, 'proposal_sha256') == pre['universe_seal']
            and digest(canonical) == pre['sources_object_sha256'], 'Canonical149 snapshot changed')
    records = {r['action_id']: r for r in current_m['records']}; rows = {r['action_id']: r for r in current_u['candidate_dispositions']}
    original_pool = {r['source_id']: r for r in canonical['sources']}; pool = {r['source_id']: r for r in s['sources']}
    require(len(pool) == len(s['sources']) == 15, 'Isolated source cohort changed')
    require(bundle['bundle_sha256'] == sealed_digest(bundle, 'bundle_sha256'), 'Decision bundle self-seal drift')
    require([r['action_id'] for r in bundle['cases']] == ACTIONS and bundle['accepted'] is bundle['canonical_application'] is bundle['publication'] is bundle['production'] is False,
            'Bundle acquired authority or changed scope')
    for case, action, doc, number, name in zip(pre['cases'], a['actions'], DOCS, NUMBERS, NAMES):
        aid = case['action_id']; record = records[aid]
        require(digest(record) == case['before_record_sha256'] and digest(rows[aid]) == case['before_row_sha256']
                and same(record, case['record']) and same(rows[aid], case['row']), 'Current exact case preimage changed')
        require(record['disposition'] == 'pending_interpretation' and record['exact_action_binding_unresolved'] is False
                and record['required_evidence_unavailable'] is record['authoritative_source_conflict'] is False, 'Current pending/binding/source state changed')
        require(case['meaning_accepted'] is case['eligibility_applied'] is case['canonical_state_changed'] is False, 'Preflight acquired authority')
        require(action['bill_number'] == number and type(action['bill_number']) is int and action['bill_type'] == 'hjres'
                and action['stage'] == 'final_passage' and action['episode_id'] == f'episode:hjres{number}:119'
                and action['additional_source_ids'] == ['govinfo:rule150:'+doc], 'Whole rule/bill/stage binding differs')
        for sid in ['clerk:'+aid.removeprefix('house:'), case['EH_source_id']]:
            require(same(pool[sid], original_pool[sid]), 'Reused official object changed')
        capture = next(c for c in d['capture']['captures'] if c['name'] == name)
        parser = RuleText(); parser.feed((ROOT/capture['raw_path']).read_text(encoding='utf-8'))
        text = ''.join(parser.parts).replace('\r\n', '\n'); source = pool['govinfo:rule150:'+doc]
        require(source['text'] == text == (P/'raw'/(name+'.txt')).read_text(encoding='utf-8')
                and source['url'] == capture['requested_url'] and source['raw_sha256'] == capture['raw_sha256']
                and source['governed_bytes_sha256'] == sealed_digest(source, 'governed_bytes_sha256'), 'Rule extraction, raw or governed identity changed')
        require(doc in text and capture['expected_page'] in text, 'Wrong named rule text')
        decision = next(c for c in bundle['cases'] if c['action_id'] == aid)
        require(decision['meaning_accepted'] is decision['eligibility_applied'] is decision['binding_approval_requested'] is
                decision['canonical_sources_registered'] is decision['source_holds_changed'] is False
                and decision['canonical_binding_already_resolved'] is True, 'Candidate recommendation became applied')
    actual = d['products']; expected = replay(a, s)
    require(same(actual, expected), 'Typed held products differ from actual native replay')
    core, mapping = actual['shared_action_core'], actual['shared_issue_mapping']
    validate_shared_action_core(ROOT, core); validate_shared_issue_mapping(ROOT, mapping, core)
    require(core['authoritative_for_new_editorial_work'] is mapping['authoritative_for_new_editorial_work'] is False
            and [x['action_id'] for x in core['actions']] == ACTIONS
            and all(x['eligibility']['decision'] == 'proposed' and x['eligibility']['parent_context_used'] is False for x in mapping['action_mappings']), 'Candidate role/eligibility changed')
    cores_by_id = {c['action_id']:c for c in core['actions']}
    for case, decision in zip(pre['cases'], bundle['cases']):
        require(decision['candidate_core_sha256'] == cores_by_id[case['action_id']]['action_core_sha256']
                and decision['meaning_ref'] == cores_by_id[case['action_id']]['action_meaning_ref']
                and decision['before_record_sha256'] == case['before_record_sha256']
                and decision['before_row_sha256'] == case['before_row_sha256'], 'Decision bundle subject correspondence differs')
    for projection in actual['member_projections']:
        validate_member_projection(ROOT, projection, core)
        expected_status = 'Nay' if projection['member_id'] == 'F000477' else 'Yea'
        require(len(projection['actions']) == 5 and all(r['official_status'] == expected_status for r in projection['actions']), 'Official member observation changed')
    for member in actual['compiled_ir']['members']:
        require(member['proposition_graph']['propositions'] == [], 'Held episode generated a proposition')
    require(d['proof']['identical_replay'] is True and d['proof']['behavioral_update_proof_exercised'] is False
            and d['proof']['product_sha256'] == {k:digest(v) for k,v in actual.items()}, 'Held replay proof overclaims')
    return {'cores': 5, 'official_observations': 10, 'sources': 15, 'issue_propositions': 0,
            'canonical149_changed': False, 'editorial_acceptance': False, 'capture': validate_capture(d['capture'])}


if __name__ == '__main__':
    print(json.dumps(dict(preserved_files=validate_preservation(), packet_files=validate_manifest(), validation=validate()), indent=2))
