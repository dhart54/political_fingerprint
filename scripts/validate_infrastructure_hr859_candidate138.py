"""Replay the isolated H.R.859 candidate; grant no admission authority."""
import copy
import hashlib
import json
from pathlib import Path

from backend.app.semantic_ir.shared_corpus import digest
from scripts.prepare_shared_domain_candidate import prepare, readable_candidates

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'docs/review_packets/infrastructure_batch138_hr859_candidate'
BASE = ROOT / 'docs/editorial/shared_candidates/house_119_infrastructure_batch134_20260916'
EVIDENCE = ROOT / 'docs/review_packets/infrastructure_batch137_hr859_scope'
MEMBERS = ['F000477', 'M001184']
OUTPUTS = ['shared_action_core', 'shared_issue_mapping', 'member_projections',
           'compiler_input', 'compiled_ir', 'readable_candidates']
INPUT_HASH = '5b058b6317f68ede06338171ba6366e27655621fb539baba639117398debdb3a'
CAPTURE_HASH = '468f3f95fa1e7ef956cb25f434ff7653db2d4bf704abb67ab313326b42f72163'
RECORD_HASH = '4e23300ba2251b7fa3f1902f9bb8a3952c8c0dbd41180f6194e0912e7582085a'
CORE_HASH = '653d3eda949247371b1972f3848cb5f2ca87bf607153c7115241c6df85ca7977'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def require(value, message):
    if not value:
        raise ValueError(message)


def validate(authoring=None, capture=None, proposal=None, outputs=None):
    a = read(PACKET / 'authoring.json') if authoring is None else authoring
    s = read(PACKET / 'sources.json') if capture is None else capture
    p = read(PACKET / 'proposal.json') if proposal is None else proposal
    o = {k: read(PACKET / 'generated' / (k + '.json')) for k in OUTPUTS} if outputs is None else outputs
    for name, sha in [('authoring.json', 'f435bd0beda209617923bbec462b71566b2b47f65b9b5530086d72b007d76c06'),
                      ('sources.json', 'd5e8b0576c5d6aa12593fef694987351c7767ba623fa85b554f9fc00f0cd826e'),
                      ('proposal.json', 'a0356604f13e83cdfe34dccfc96ca306513c6c72aaedce468d305bc71a04dbb0')]:
        require(hashlib.sha256((PACKET / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == sha,
                'Frozen review file bytes changed')
    require(digest(a) == INPUT_HASH, 'Authored review subject changed')
    require(digest(s) == CAPTURE_HASH, 'Source review subject changed')
    require(len(a['actions']) == 1 and a['actions'][0]['action_id'] == p['action_id'] == 'house:119:1:109'
            and a['review_state'] == 'candidate_pending_external_semantic_review', 'Candidate subject differs')
    for key in ['governed_inventory_changed', 'registered_source_pool_changed',
                'prior_sealed_decisions_or_index_changed', 'canonical_admission_authorized',
                'semantic_acceptance', 'issue_membership_accepted',
                'approved_universe_or_full_issue_claim', 'publication_authorized',
                'production_authorized', 'compatibility_change_performed', 'Health_activated']:
        require(p[key] is False, 'Candidate gained application or acceptance authority')
    require(p['isolated_partial_scope'] is True and p['proposed_review_route'] == 'human_exception_required'
            and p['strongest_counterevidence'] and p['requested_content_bound_human_disposition'],
            'Eligibility counterargument or human decision lost')
    require(p == read(PACKET / 'proposal.json'), 'Sealed proposal metadata changed')
    originals = {x['source_id']: x for x in read(BASE / 'sources.json')['sources']}
    links = read(PACKET / 'source_links.json')['sources']
    units = {u['source_key']: u for u in read(EVIDENCE / 'source_questions.json')['source_units']}
    require(len(s['sources']) == len(links) == 8, 'Source inventory differs')
    for i, (source, link) in enumerate(zip(s['sources'], links)):
        require(link['source_id'] == source['source_id'] and link['candidate_pointer'] == f'/sources/{i}'
                and link['candidate_object_sha256'] == digest(source)
                and link['raw_sha256'] == source['raw_sha256']
                and link['governed_bytes_sha256'] == source['governed_bytes_sha256'], 'Source link differs')
        if source['source_id'] in originals:
            require(source == originals[source['source_id']], 'Retained source changed')
        else:
            key = source['source_id'].split(':')[1].removesuffix('-2024')
            c = read(EVIDENCE / (key + '_capture.json'))
            require(source['text'] == c['normalized_text'] and source['url'] == c['requested_url']
                    and source['raw_sha256'] == c['raw_response_sha256']
                    and any(x['source_id'] == source['source_id'] and x['passage'] == units[key]['passage']
                            for x in a['actions'][0]['claim_source_map']), 'Selected dated context changed')
    before = next(r for r in read(BASE / 'membership_review.json')['records'] if r['action_id'] == p['action_id'])
    row = next(r for r in read(BASE / 'universe_proposal.json')['candidate_dispositions'] if r['action_id'] == p['action_id'])
    require(digest(before) == p['current_governed_record_sha256']
            and digest(row) == p['current_governed_row_sha256']
            and before['disposition'] == p['current_governed_disposition'] == 'pending_interpretation'
            and before['exact_action_binding_unresolved'] is p['current_governed_binding_unresolved'] is False,
            'Governed preimage or state changed')
    core, mapping, projections, inputs, result = prepare(a, s, MEMBERS)
    rendered = readable_candidates(a, core, projections, result)
    expected = dict(shared_action_core=core, shared_issue_mapping=mapping, member_projections=projections,
                    compiler_input=inputs, compiled_ir=result.compiled_ir, readable_candidates=rendered)
    require(o['shared_action_core']['authoritative_for_new_editorial_work'] is False
            and o['shared_issue_mapping']['authoritative_for_new_editorial_work'] is False
            and o['readable_candidates']['production_eligible'] is False
            and o['shared_issue_mapping']['action_mappings'][0]['eligibility']['decision'] == 'proposed',
            'Generated candidate gained authority')
    require(o == expected, 'Generated candidate replay differs')
    require(core['actions'][0]['action_core_sha256'] == p['shared_action_core_sha256'] == CORE_HASH
            and core['corpus_sha256'] == p['shared_corpus_sha256']
            and mapping['mapping_sha256'] == p['shared_mapping_sha256'], 'Shared meaning seal differs')
    expected_record = copy.deepcopy(before)
    expected_record.update(disposition='interpreted_substantive_directional', rationale=p['proposed_record']['rationale'],
                           sources=[{k: x[k] for k in ['source_id', 'url', 'raw_sha256', 'governed_bytes_sha256']}
                                    for x in s['sources']],
                           claim_source_map=a['actions'][0]['claim_source_map'], episode_candidate_id='episode:hr859:119')
    require(p['proposed_record'] == expected_record
            and digest(expected_record) == p['proposed_record_sha256'] == RECORD_HASH, 'Proposed record differs')
    for projection, status, effect in zip(projections, ['Yea', 'Nay'], ['supports_exact_choice', 'opposes_exact_choice']):
        action = projection['actions'][0]
        require(action['official_status'] == status and action['exact_choice_effect'] == effect
                and action['action_core_sha256'] == CORE_HASH
                and projection['authoritative_legislative_meaning'] is False, 'Official member projection differs')
    replay = read(PACKET / 'generated/replay_receipt.json')
    require(replay['identical_replay'] is True and replay['input_sha256'] == digest(a)
            and replay['capture_sha256'] == digest(s)
            and replay['output_sha256'] == {k: digest(v) for k, v in expected.items()}
            and replay['canonical_mutation'] is replay['semantic_acceptance'] is replay['publication_authorized'] is False,
            'Replay receipt differs')
    return dict(action_id=p['action_id'], shared_core=CORE_HASH, source_objects=8,
                proposed_record=RECORD_HASH, member_statuses=dict(zip(MEMBERS, ['Yea', 'Nay'])),
                candidate_propositions=result.validation['proposition_count'], governed_inventory_changed=False,
                semantic_acceptance=False)


def validate_transport(receipt=None):
    r = read(PACKET / 'validation_receipt.json') if receipt is None else receipt
    expected = {'authoring.json', 'sources.json', 'proposal.json', 'source_links.json', 'README.md'} | {
        'generated/' + name + '.json' for name in OUTPUTS + ['replay_receipt']}
    require(r['packet_byte_units'] == 'committed_LF_UTF8', 'Transport byte units differ')
    require(len(r['packet_files']) == len(expected), 'Transport cohort differs')
    actual = set()
    for f in r['packet_files']:
        path = (ROOT / f['path']).resolve()
        require(path.is_relative_to(PACKET.resolve()), 'Transport path escaped packet')
        actual.add(path.relative_to(PACKET.resolve()).as_posix())
        lf = path.read_bytes().replace(b'\r\n', b'\n')
        require(len(lf) == f['bytes'] < 200000 and hashlib.sha256(lf).hexdigest() == f['lf_sha256'],
                'Committed LF count or hash differs')
    require(actual == expected, 'Transport file set differs')
    return dict(files=len(expected), byte_units='committed_LF_UTF8')


if __name__ == '__main__':
    print(json.dumps(dict(candidate=validate(), transport=validate_transport()), indent=2))
