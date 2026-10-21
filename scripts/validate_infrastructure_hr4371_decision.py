"""Validate the bounded, unapplied H.R.4371 review recommendation.

This is a review-sidecar check, not a second compiler, acceptance gate, or
alternative source of governed action accounting.
"""
import copy
import json
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch134_20260916'
PACKET = ROOT / 'docs/review_packets/infrastructure_batch135_hr4371_decision'
HEAD = '748519100b888bf17a0b8147eb1dd0e60a184e84'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(packet=None):
    v = read(PACKET / 'recommendation.json') if packet is None else packet
    ss = {s['source_id']: s for s in read(BASE / 'sources.json')['sources']}
    members = read(BASE / 'membership_review.json')['records']
    before = next(r for r in members if r['action_id'] == 'house:119:1:340')
    row = next(r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions']
               if r['action_id'] == before['action_id'])
    require(v['base_head'] == HEAD and v['action_id'] == before['action_id']
            and v['domain_id'] == before['domain_id'], 'Review subject differs')
    require(v['before_record_sha256'] == digest(before)
            and v['before_universe_row_sha256'] == digest(row), 'Preimage differs')
    for key in ['applied_to_governed_inventory', 'canonical_source_corpus_changed',
                'compiled_graph_changed', 'semantic_acceptance', 'membership_accepted',
                'publication_authorized', 'production_authorized',
                'compatibility_implementation_authorized']:
        require(v[key] is False, 'Reserved or application authority asserted')
    require(v['source_acquisitions'] == v['protected_retries'] == 0
            and v['proposed_review_route'] == 'human_exception_required',
            'Research or routing boundary differs')
    require(before['disposition'] == v['current_governed_disposition'] == 'pending_interpretation'
            and before['exact_action_binding_unresolved'] is True
            and v['current_governed_binding_unresolved'] is True,
            'Governed pending state was cleared')
    expected_ids = ['clerk:119:1:340', 'govinfo:hr4371eh', 'govinfo:hr4371rh',
                    'govinfo:hres951eh', 'clerk:119:1:338', 'clerk:119:1:339',
                    'govinfo:8usc1232-2024-care-placement']
    require([e['source_id'] for e in v['evidence']] == expected_ids,
            'Adoption-chain or baseline evidence omitted')
    source_list = read(BASE / 'sources.json')['sources']
    for e in v['evidence']:
        source = ss[e['source_id']]
        require(e['source_object_sha256'] == digest(source)
                and e['parent_path'] == (BASE / 'sources.json').relative_to(ROOT).as_posix()
                and e['json_pointer'] == f'/sources/{source_list.index(source)}'
                and e['url'] == source['url'], 'Source provenance differs')
        if 'start' in e:
            require(e['total'] == len(source['text'])
                    and e['passage'] == source['text'][e['start']:e['end']],
                    'Source extent or passage differs')
        else:
            require(e['metadata'] == source['metadata'], 'Clerk metadata differs')
    eh = ss['govinfo:hr4371eh']['text']
    rh = ss['govinfo:hr4371rh']['text']
    require(len(eh) == 11304 and eh[541:10929] == rh[1261:11649]
            and v['evidence'][1]['start'] == 0 and v['evidence'][1]['end'] == 11304
            and v['evidence'][2]['start'] == 1261 and v['evidence'][2]['end'] == 11649
            and v['evidence'][3]['start'] == 6336 and v['evidence'][3]['end'] == 7307,
            'Whole EH or substitute reconciliation differs')
    rule = ss['govinfo:hres951eh']['text'][6336:7307]
    require('H.R. 4371' in rule and 'Committee on the Judiciary' in rule
            and 'shall be considered as adopted' in rule,
            'Governing adoption rule differs')
    for roll, measure, question, result in [
        (338, 'H RES 951', 'On Agreeing to the Resolution', 'Passed'),
        (339, 'H R 4371', 'On Motion to Recommit', 'Failed'),
        (340, 'H R 4371', 'On Passage', 'Passed'),
    ]:
        m = ss[f'clerk:119:1:{roll}']['metadata']
        require((m['legis-num'], m['vote-question'], m['vote-result'], m['action-date'])
                == (measure, question, result, '16-Dec-2025'), 'Stage-compatible chain differs')
    require('Passed the House of Representatives December 16, 2025.' in eh,
            'EH passage attestation differs')
    c = v['proposed_record']
    require(c['disposition'] == 'exact_action_ineligible'
            and c['exact_action_binding_unresolved'] is False
            and c['review_state'] == 'candidate_pending_external_semantic_review'
            and c['episode_candidate_id'] is None, 'Proposed exclusion state differs')
    expected = copy.deepcopy(before)
    expected.update(disposition=c['disposition'], exact_action_binding_unresolved=False,
                    rationale=c['rationale'])
    for sid in ['govinfo:hres951eh', 'clerk:119:1:338', 'clerk:119:1:339']:
        expected['sources'].append({k: ss[sid][k] for k in
                                   ['source_id', 'url', 'raw_sha256', 'governed_bytes_sha256']})
    expected['claim_source_map'].append(dict(
        source_id='govinfo:hres951eh',
        locator='Section6 retained6336:7307; substitute adoption, debate and recommittal rule; not policy-direction evidence',
        passage=rule))
    require(c == expected and v['proposed_record_sha256'] == digest(c),
            'Prior claims, flags or candidate provenance changed')
    analysis = v['eligibility_analysis']
    require(analysis['inclusion_rule'] == read(BASE / 'universe_proposal.json')['inclusion_rule']
            and analysis['recommendation'] == 'proposed_exclusion_under_existing_rule'
            and len(analysis['exact_provisions_evaluated']) == 3
            and analysis['counterevidence'] and analysis['comparator_limit'],
            'Existing rule or contested mechanisms lost')
    # Content identities make semantic edits require a new reviewable proposal;
    # structural checks alone must not silently authorize changed prose.
    require(digest(c) == '9d1c04ac2119d9bb762fa578a10214f7184f257013a7b07cc2a19f1f58e8982d',
            'Candidate meaning changed; renew explicit review subject')
    components = v['whole_choice_candidate']
    markers = ['SEC. 2.', 'SEC. 3.', 'SEC. 4.', 'SEC. 5.', 'SEC. 6.', 'Passed the House']
    require(len(components) == 5 and all(
        c['source_id'] == 'govinfo:hr4371eh'
        and c['start'] == eh.index(markers[i]) and c['end'] == eh.index(markers[i+1])
        and c['meaning'] for i, c in enumerate(components)), 'Whole-choice accounting differs')
    require(digest(components) == 'e9d679701324587dc68ed7a6a3b8244f3691c99b6d470fabff36b0cecafb502e',
            'Whole-choice meaning changed; renew explicit review subject')
    research = read(PACKET / 'retained_3507_research.json')
    source = read(PACKET / 'retained_3507_source.json')
    require(source['source_id'] == 'govinfo:44usc3507-2024'
            and len(source['text']) == 13026
            and digest(source) == 'e6726335c7c9d22cca72db7014636f3fcf4851c0cc0365801e733e935544fc72'
            and research['before_record_sha256'] == digest(before)
            and research['canonical_source_corpus_changed'] is False
            and research['source_read_slices'] == [dict(start=0,end=8000),dict(start=8000,end=13026)],
            'Optional dated3507 research provenance differs')
    require(not any(research[k] for k in ['whole_PRA_privacy_or_currentlaw_reviewed',
        'actual_approval_or_collection_outcome_determined', 'EH_displacement_or_j_predicate_import_adjudicated',
        'membership_accepted']), 'Dated context became coverage or acceptance')
    return dict(action_id=before['action_id'], proposal='unaccepted exclusion',
                route=v['proposed_review_route'], governed_inventory_changed=False,
                source_count=len(ss), governed_record_count=len(members),
                source_acquisitions=0, protected_retries=0)


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
