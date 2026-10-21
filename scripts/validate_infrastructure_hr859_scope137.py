"""Authenticate selected source research without clearing action semantics."""
import base64
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'docs/review_packets/infrastructure_batch137_hr859_scope'
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch134_20260916'
SOURCES = {
    '15usc45b': (1296, 1398, 10908, 15747, '83b26f946d5a503fb89946dad35fef6b381327c18052d9a3de704bb15c87c5a6'),
    '47usc617': (315, 7403, 7896, 11374, '197decf27a2294680183d496c2f90285c76f406147c8f1d3abe48fffbcce7b14'),
    '47usc303': (14252, 16947, 66197, 81720, '92f1108d92311ab418eb0c0b28e199801836889091f54dcc0127d99572656851'),
    '47usc619': (331, 2055, 2482, 4143, '31a1e47764a5b537f3edfeacfc39da9f0e762cdf81db0e6d99f6b37fd9466ed4'),
    '47usc255': (330, 2051, 2474, 4672, 'f717fbbd845a1c79490ec8cee12a7db140b20a76e090d8eddcd2fd50db4276e3'),
}


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def require(value, message):
    if not value:
        raise ValueError(message)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, text):
        self.parts.append(text)


def validate(packet=None, captures=None, diagnosis=None):
    p = read(PACKET / 'source_questions.json') if packet is None else packet
    d = read(PACKET / 'access_diagnosis_and_followup.json') if diagnosis is None else diagnosis
    require(p['base_head'] == '28437fb5f0c79f7aa3b63faa705c8bb58ac1d7d0'
            and p['action_id'] == 'house:119:1:109', 'Research subject differs')
    record = next(r for r in read(BASE / 'membership_review.json')['records'] if r['action_id'] == p['action_id'])
    row = next(r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions'] if r['action_id'] == p['action_id'])
    require(p['current_governed_record_sha256'] == digest(record)
            and p['current_governed_universe_row_sha256'] == digest(row)
            and p['current_governed_disposition'] == record['disposition'] == 'pending_interpretation'
            and p['current_governed_binding_unresolved'] is record['exact_action_binding_unresolved'] is False,
            'Governed preimage or state changed')
    for k in ['canonical_state_changed', 'whole_action_meaning_completed',
              'new_shared_action_core_authored', 'device_exception_scope_cleared',
              'actual_device_classified', 'current_law_certified',
              'all_incorporated_regulations_reviewed', 'semantic_acceptance',
              'publication_authorized', 'production_authorized',
              'compatibility_authorized', 'Health_activated',
              'exhaustive_regulatory_device_scope_cleared']:
        require(p[k] is False, 'Research became completion, authority or classification')
    require(p['canonical_source_objects_added'] == 0
            and p['successful_original_raw_captures'] == 5
            and p['raw_transport_attempts'] == 6
            and p['raw_transport_content_validation_failures'] == 1
            and p['bounded_followups_after_unclassified_tool_failures'] == 2
            and p['ordinary_publisher_located_source_attempts'] == 1,
            'Attempt/source accounting differs')
    require([u['source_key'] for u in p['source_units']] == list(SOURCES), 'Selected source cohort differs')
    for u in p['source_units']:
        key = u['source_key']
        start, end, total, raw_size, raw_sha = SOURCES[key]
        path = ROOT / u['capture_path']
        require(path.parent == PACKET and path.name == key + '_capture.json', 'Capture path differs')
        c = read(path) if captures is None else captures[key]
        raw = base64.b64decode(c['raw_response_base64'], validate=True)
        require(c['http_status'] == 200 and c['source_registered'] is False
                and c['canonical_state_changed'] is False and c['raw_capture_attempts'] == 1
                and len(raw) == c['raw_response_bytes'] == raw_size
                and hashlib.sha256(raw).hexdigest() == c['raw_response_sha256'] == u['raw_response_sha256'] == raw_sha,
                'Original source bytes, status or registration differ')
        parser = TextParser()
        parser.feed(raw.decode('utf8'))
        text = ' '.join(' '.join(parser.parts).split())
        require(text == c['normalized_text'] and len(text) == c['normalized_text_characters'] == total
                and hashlib.sha256(text.encode()).hexdigest() == c['normalized_text_sha256'] == u['normalized_text_sha256'],
                'Raw-to-text reconstruction differs')
        require(c['requested_url'] == u['url'] and 'www.govinfo.gov/content/pkg/USCODE-2024-' in u['url'],
                'Dated official source location differs')
        require(u['source_extent'] == dict(start=start, end=end, total=total)
                and u['passage'] == text[start:end]
                and u['passage_sha256'] == hashlib.sha256(text[start:end].encode()).hexdigest()
                and u['whole_source_reviewed'] is False and u['bounded_claim'] and u['limits'],
                'Selected reading expanded or passage changed')
        if key == '47usc255':
            require('subchapII-partII-sec255' in u['url']
                    and c['publisher_locator_url'].endswith('subchapII-partII-sec255')
                    and c['raw_response_retained'] is True
                    and c['content_markers'] == dict(request_access=False, page_not_found=False,
                                                    expected_section=True, expected_edition=True),
                    'Publisher-located255provenance differs')
            a = u['annotation_extent']
            require(u['annotation'] == text[a['start']:a['end']]
                    and a['end'] == a['total'] == total
                    and 'par. (2)(A)' in u['annotation'] and 'par. (1)(A)' in u['annotation'],
                    'Literal255reference-note qualification lost')
    sources = read(BASE / 'sources.json')['sources']
    b = next(s for s in sources if s['source_id'] == 'govinfo:hr859eh')
    e = p['retained_bill_evidence']
    require(e['source_object_sha256'] == digest(b) and e['passage'] == b['text']
            and e['full_retained_text_characters'] == 4855
            and e['json_pointer'] == f'/sources/{sources.index(b)}', 'Retained whole bill witness differs')
    original = read(PACKET / 'acquisition_observations.json')['browser_open_observations']
    require(len(original) == 5, 'Original browser observation cohort differs')
    for key in ['47usc255', '47usc619']:
        o = next(o for o in original if o['source_key'] == key)
        require(o['http_status'] is None and o['raw_response_hash'] is None
                and o['response_body_retained'] is False
                and o['result'] == 'unclassified_tool_access_failure', 'Original tool failure upgraded or erased')
    failed = read(PACKET / '47usc255_failed_capture.json')
    require(failed['http_status'] == 200 and failed['raw_response_retained'] is False
            and 'raw_response_base64' not in failed and 'raw_response_sha256' not in failed,
            'Missing original255body reconstructed or relabeled')
    f = next(f for f in d['followups'] if f['source_key'] == '47usc255')
    require(f['raw_response_retained'] is False and f['raw_response_sha256'] is None
            and f['http_status'] == 200 and f['provenance_limit'], 'Missing-body provenance limit lost')
    require(d['retained617_href_inspection']['hrefs_containing255'] == []
            and d['retained617_href_inspection']['alternate_official_location_established'] is False
            and d['publisher_locator_followup']['original_failure_body_reconstructed'] is False
            and d['publisher_locator_followup']['response_retained_before_validation'] is True,
            'Publisher locator conflated with617href or earlier body')
    helper = d['executed_locator_capture_helper']
    code = helper['source']
    raw_at, parse_at = code.find('r.update(raw_response_bytes='), code.find('parser=Parser()')
    require(hashlib.sha256(code.encode()).hexdigest() == helper['LF_sha256']
            and 0 <= raw_at < parse_at and 'write();assert len(raw)' in code,
            'Executed capture-ordering snapshot differs')
    return dict(action_id=p['action_id'], selected_sources=5, selected_primary_unit_characters=13330,
                original_raw_bytes=117656, canonical_source_objects_added=0,
                whole_case_completed=False, actual_device_classified=False)


def validate_transport(receipt=None):
    r = read(PACKET / 'validation_receipt.json') if receipt is None else receipt
    require(r['packet_byte_units'] == 'committed_LF_UTF8', 'Transport byte units differ')
    expected = {key + '_capture.json' for key in SOURCES} | {
        '47usc255_failed_capture.json', 'source_questions.json',
        'acquisition_observations.json', 'access_diagnosis_and_followup.json', 'README.md'}
    require({Path(f['path']).name for f in r['packet_files']} == expected
            and len(r['packet_files']) == len(expected), 'Transport file set differs')
    for f in r['packet_files']:
        path = ROOT / f['path']
        require(path.parent == PACKET, 'Transport path differs')
        lf = path.read_bytes().replace(b'\r\n', b'\n')
        require(len(lf) == f['bytes'] and hashlib.sha256(lf).hexdigest() == f['lf_sha256'],
                'Committed LF transport size or hash differs')
    return dict(files=len(expected), byte_units='committed_LF_UTF8')


if __name__ == '__main__':
    print(json.dumps(dict(source_scope=validate(), transport=validate_transport()), indent=2))
