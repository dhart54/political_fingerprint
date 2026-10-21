"""Focused validation of two unapplied Infrastructure review sidecars."""
import copy
import json
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch134_20260916'
PACKET = ROOT / 'docs/review_packets/infrastructure_batch136_research_product_boundaries'
SUBJECTS = {
    28: ('house:119:1:12', 'pending_interpretation', False,
         '2d6d92a9ecdc50ee81fd9acaa4fa9a5134fa845c6bb5fff2462cadbd378c9338',
         '66cae239140ebabeca6f2a6f2e61b319d979a49fbac9b2d3dc74bc9802a40315'),
    1442: ('house:119:1:108', 'exact_action_ineligible', True,
           'b4dbe5d9617192fe971d8fa16702d48e75371d4828d41db65490f59b26789cdc',
           '865234626d54d024f432f43d79b11e5d9f3916a3adb595cd142e3f1dd357c05d'),
}


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def require(value, message):
    if not value:
        raise ValueError(message)


def validate(bill, packet=None):
    v = read(PACKET / f'hr{bill}_recommendation.json') if packet is None else packet
    aid, disposition, old_binding, candidate_sha, meaning_sha = SUBJECTS[bill]
    sources = read(BASE / 'sources.json')['sources']
    ss = {s['source_id']: s for s in sources}
    before = next(r for r in read(BASE / 'membership_review.json')['records'] if r['action_id'] == aid)
    u = read(BASE / 'universe_proposal.json')
    row = next(r for r in u['candidate_dispositions'] if r['action_id'] == aid)
    require(v['action_id'] == aid and v['domain_id'] == before['domain_id']
            and v['checkpoint'] == 136
            and v['base_head'] == '638178a9752744a75586b25d0aefbdf0d67f1ade', 'Subject differs')
    require(v['before_record_sha256'] == digest(before)
            and v['before_universe_row_sha256'] == digest(row), 'Preimage differs')
    require(before['disposition'] == v['current_governed_disposition'] == 'pending_interpretation'
            and before['exact_action_binding_unresolved'] is old_binding
            and v['current_governed_binding_unresolved'] is old_binding, 'Governed state changed')
    for k in ['applied_to_governed_inventory', 'canonical_source_corpus_changed',
              'compiled_graph_changed', 'semantic_acceptance', 'membership_accepted',
              'publication_authorized', 'production_authorized',
              'compatibility_implementation_authorized']:
        require(v[k] is False, 'Reserved authority or application asserted')
    require(v['source_acquisitions'] == v['protected_retries'] == 0
            and v['proposed_review_route'] == 'human_exception_required', 'Routing differs')
    cl = 'clerk:' + ':'.join(aid.split(':')[1:])
    sid = f'govinfo:hr{bill}eh'
    require([e['source_id'] for e in v['evidence']] == [cl, sid], 'Evidence role omitted')
    for e in v['evidence']:
        source = ss[e['source_id']]
        require(e['source'] == source and e['source_object_sha256'] == digest(source)
                and e['parent_path'] == (BASE / 'sources.json').relative_to(ROOT).as_posix()
                and e['json_pointer'] == f'/sources/{sources.index(source)}', 'Official source differs')
    m = ss[cl]['metadata']
    question, date, attestation, length = (
        ('On Passage', '14-Jan-2025', 'January 14, 2025', 3619) if bill == 28 else
        ('On Motion to Suspend the Rules and Pass, as Amended', '29-Apr-2025', 'April 29, 2025', 2653))
    text = ss[sid]['text']
    require((m['legis-num'], m['vote-question'], m['vote-result'], m['action-date'])
            == (f'H R {bill}', question, 'Passed', date)
            and f'H.R. {bill} Engrossed in House (EH)' in text
            and f'Passed the House of Representatives {attestation}.' in text
            and len(text) == length, 'Stage-compatible text differs')
    proposed = v['proposed_record']
    expected = copy.deepcopy(before)
    expected.update(disposition=disposition, exact_action_binding_unresolved=False,
                    rationale=proposed['rationale'])
    require(proposed == expected and proposed['review_state'] == 'candidate_pending_external_semantic_review'
            and v['proposed_record_sha256'] == digest(proposed), 'Prior claims or proposed state changed')
    require(digest(proposed) == candidate_sha, 'Candidate meaning changed; renew review subject')
    choice = v['whole_choice_candidate']
    require(choice['source_id'] == sid and choice['start'] == 0 and choice['end'] == length
            and digest(choice) == meaning_sha, 'Whole-choice meaning or extent changed')
    a = v['eligibility_analysis']
    require(a['inclusion_rule'] == u['inclusion_rule'] and a['counterevidence'] and a['resolution'],
            'Existing rule or counterargument lost')
    return dict(action_id=aid, proposed_disposition=disposition,
                governed_inventory_changed=False, accepted=False)


def validate_bundle(bundle=None):
    v = read(PACKET / 'decision_bundle.json') if bundle is None else bundle
    expected = {
        'house:119:1:340': ('docs/review_packets/infrastructure_batch135_hr4371_decision/recommendation.json',
                          '9d1c04ac2119d9bb762fa578a10214f7184f257013a7b07cc2a19f1f58e8982d'),
        'house:119:1:12': ((PACKET / 'hr28_recommendation.json').relative_to(ROOT).as_posix(), SUBJECTS[28][3]),
        'house:119:1:108': ((PACKET / 'hr1442_recommendation.json').relative_to(ROOT).as_posix(), SUBJECTS[1442][3]),
    }
    require([c['action_id'] for c in v['cases']] == list(expected), 'Bundle action set differs')
    require(v['status'] == 'prepared_for_independent_and_authorized_human_review'
            and v['governed_snapshot'] == 134 and v['governed_pending'] == 262,
            'Bundle state differs')
    for k in ['canonical_changes_authorized', 'exceptions_enacted', 'editorial_acceptance',
              'publication_authorized', 'production_authorized', 'compatibility_authorized']:
        require(v[k] is False, 'Bundle authority asserted')
    members = {r['action_id']: r for r in read(BASE / 'membership_review.json')['records']}
    for c in v['cases']:
        path, sha = expected[c['action_id']]
        subject = read(ROOT / path)
        before = members[c['action_id']]
        require(c['candidate_path'] == path and c['proposed_record_sha256'] == sha
                == digest(subject['proposed_record']), 'Bundle sealed subject differs')
        require(c['current_governed_record_sha256'] == digest(before)
                and c['current_governed_disposition'] == before['disposition']
                and c['current_governed_binding_unresolved'] is before['exact_action_binding_unresolved']
                and c['proposed_disposition'] == subject['proposed_record']['disposition']
                and c['proposed_binding_unresolved'] is subject['proposed_record']['exact_action_binding_unresolved'],
                'Bundle current/proposed state differs')
        require(c['canonical_application_authorized'] is c['semantic_acceptance'] is False
                and c['review_route'] == 'human_exception_required'
                and c['strongest_counterevidence'] and c['requested_content_bound_human_decision'],
                'Bundle case authority or decision lost')
        require(c['independent_packet_review_at_index_preparation'] ==
                ('bounded_clean' if c['action_id'] == 'house:119:1:340' else 'pending'),
                'Bundle retrospective review claim differs')
    return dict(action_count=3, exceptions_enacted=False, governed_pending=262)


if __name__ == '__main__':
    print(json.dumps(dict(cases=[validate(bill) for bill in SUBJECTS], bundle=validate_bundle()), indent=2))
