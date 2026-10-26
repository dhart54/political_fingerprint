"""Validate the eight approved state transitions without accepting held meaning."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
from scripts.apply_infrastructure_case_decisions154 import (
    BASE, OUT, PACKET, ELIGIBILITY, BINDINGS, SCOPE, read, require, load_inputs,
    validate_pins, validate_state, apply_exact_decisions, application_receipt, normalized_bytes,
)
from scripts.prepare_shared_domain_candidate import validate_universe_proposal

OUTPUT_MANIFEST_SHA = '53bc34543c9a932a5faa66135e44b446c9d1ca9a2735e5f56f038e6daad2f90c'


def validate(root=ROOT):
    d = load_inputs(root)
    preserved = validate_pins(root, d)
    base, out, packet = root / BASE, root / OUT, root / PACKET
    m0, u0, sources = [read(base / n) for n in ['membership_review.json', 'universe_proposal.json', 'sources.json']]
    m, u = [read(out / n) for n in ['membership_review.json', 'universe_proposal.json']]
    validate_state(m, u, sources, d, True)
    validate_universe_proposal(u, capture=sources, membership=m)
    expected_m, expected_u, fresh = apply_exact_decisions(m0, u0, sources, d)
    require(fresh['changed'] and digest(m) == digest(expected_m) and digest(u) == digest(expected_u),
            'Fresh deterministic application differs')
    _, _, repeated = apply_exact_decisions(m, u, sources, d)
    require(repeated['changed'] is False, 'Application is not idempotent')
    manifest = read(packet / 'output_manifest.json')
    require(digest(manifest) == OUTPUT_MANIFEST_SHA and manifest['manifest_sha256'] == sealed_digest(manifest, 'manifest_sha256'),
            'Frozen output manifest differs')
    expected_paths = {OUT + '/' + n for n in d['snapshot_files']} | {PACKET + '/application_receipt.json'}
    require(set(manifest['files']) == expected_paths, 'Successor output cohort differs')
    for name, pin in manifest['files'].items():
        body = normalized_bytes(root / name)
        require(len(body) == pin['bytes'] and hashlib.sha256(body).hexdigest() == pin['lf_sha256'],
                'Materialized output bytes differ: ' + name)
    for suffix in d['snapshot_files']:
        if suffix not in ['membership_review.json', 'universe_proposal.json']:
            require(normalized_bytes(out / suffix) == normalized_bytes(base / suffix),
                    'Source/old70/settled149 semantic product changed: ' + suffix)
    require(digest(read(packet / 'application_receipt.json')) == digest(application_receipt(d, m, u)),
            'Receipt or reserved authority differs')
    old = {r['action_id']: r for r in m0['records']}
    new = {r['action_id']: r for r in m['records']}
    before_rows = {r['action_id']: r for r in u0['candidate_dispositions']}
    after_rows = {r['action_id']: r for r in u['candidate_dispositions']}
    changed_records = {aid for aid in old if digest(old[aid]) != digest(new[aid])}
    changed_rows = {aid for aid in old if digest(before_rows[aid]) != digest(after_rows[aid])}
    require(changed_records == changed_rows == SCOPE, 'Application escaped the exact eight subjects')
    for aid in SCOPE:
        allowed = {'rationale', 'disposition'} if aid in ELIGIBILITY else {'rationale', 'exact_action_binding_unresolved'}
        require(digest({k: v for k, v in old[aid].items() if k not in allowed})
                == digest({k: v for k, v in new[aid].items() if k not in allowed}),
                'Record source/meaning/member state changed: ' + aid)
        allowed_row = {'disposition', 'reason', 'rationale', 'issue_boundary_status', 'unresolved_reason',
                       'exact_action_source_binding', 'review_progress'}
        require(digest({k: v for k, v in before_rows[aid].items() if k not in allowed_row})
                == digest({k: v for k, v in after_rows[aid].items() if k not in allowed_row}),
                'Official observation or unrelated row state changed: ' + aid)
        require(new[aid]['exact_action_binding_unresolved'] is (False if aid in BINDINGS else old[aid]['exact_action_binding_unresolved']),
                'Unapproved binding change: ' + aid)
        if aid in ELIGIBILITY:
            require(new[aid]['disposition'] == ('exact_action_ineligible' if ELIGIBILITY[aid] == 'exclude' else 'pending_interpretation'),
                    'Eligibility created an unauthorized meaning admission')
    require(digest(u['interpretation_action_ids']) == digest(u0['interpretation_action_ids'])
            and digest(u['proposed_action_ids']) == digest(u0['proposed_action_ids']), 'Interpreted/admitted set changed')
    for aid, evidence in d['binding_evidence'].items():
        require(evidence['target_source_id'] == BINDINGS[aid], 'Wrong approved EH target')
        require(evidence['historical_false_request_flags_remain_unchanged'] is True
                and evidence['meaning_or_eligibility_accepted_by_binding'] is False, 'Binding promoted meaning/eligibility')
        for identity in evidence['retained_source_identities']:
            pool = read(root / identity['main_source_path'])['sources']
            index = int(identity['json_pointer'].split('/')[-1])
            source = pool[index]
            require(digest(source) == identity['source_object_sha256']
                    and source['raw_sha256'] == identity['raw_sha256']
                    and source['governed_bytes_sha256'] == identity['governed_bytes_sha256'],
                    'Approved retained source identity drift')
        for proof in evidence['proofs']:
            require(digest(read(root / proof['path'])) == proof['object_sha256'], 'Approved complete-chain proof drift')
    return dict(eligibility_decisions=3, resolved_bindings=5, accepted_authored_meanings=0,
        new_interpreted_or_issue_admitted=0, pending=246, ineligible=129, sources=1662,
        preserved_files=preserved, fixed_outputs=len(expected_paths), other_records_unchanged=668,
        source_holds=6, publication=False, production=False, replay_identical=True, idempotent_no_write=True)


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
