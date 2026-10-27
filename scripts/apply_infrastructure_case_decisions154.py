"""Pure, sealed application of three eligibility and five binding approvals only."""
import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.semantic_ir.shared_corpus import digest, sealed_digest
BASE = 'docs/editorial/shared_candidates/house_119_infrastructure_batch149_20260916'
OUT = 'docs/editorial/shared_candidates/house_119_infrastructure_batch154_20260916'
PACKET = 'docs/review_packets/infrastructure_case_application154'
BASE_COMMIT = '3aa57b7af67894c9ec7b872031d0d67ba9cbe36b'
FROZEN_INPUT_SHA = 'd3d64fb1993884274a1ac4dc7513f714c17d1afab5745a26652b00b75eb1ac8e'
ELIGIBILITY = {'house:119:2:49': 'exclude', 'house:119:1:125': 'include', 'house:119:1:231': 'exclude'}
BINDINGS = {'house:119:1:330': 'govinfo:hr3898eh', 'house:119:1:356': 'govinfo:hr4776eh',
            'house:119:1:19': 'govinfo:hr187eh', 'house:119:1:216': 'govinfo:hr1917eh',
            'house:119:2:97': 'govinfo:hr6422eh'}
SCOPE = set(ELIGIBILITY) | set(BINDINGS)
BOUNDARY = ('Approved application154 only: exclude980 and Perry27; include2215 for named-public-site planning; '
            'resolve only3898/4776/187/1917/6422 exact EH bindings. No authored meaning acceptance, new '
            'interpretation/admission, other eligibility/binding decision, source import, publication or production authority.')


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def normalized_bytes(path, mode='lf'):
    raw = path.read_bytes()
    return raw.replace(b'\r\n', b'\n') if mode == 'lf' else raw


def load_inputs(root=ROOT):
    d = read(root / PACKET / 'governed_inputs.json')
    require(digest(d) == FROZEN_INPUT_SHA and d['inputs_sha256'] == sealed_digest(d, 'inputs_sha256'),
            'Frozen approval, subjects or source/proof identities differ')
    require(d['base_commit'] == BASE_COMMIT and d['eligibility_decisions'] == ELIGIBILITY
            and d['binding_decisions'] == BINDINGS and set(d['subjects']) == SCOPE,
            'Approved action/decision envelope differs')
    require(d['authored_meaning_acceptance_authorized'] is False and d['other_decisions_authorized'] is False,
            'Approval escalated into authored meaning or other decisions')
    return d


def validate_pins(root, d):
    for name, pin in d['preserved_main_files'].items():
        raw = normalized_bytes(root / name, pin['mode'])
        require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
                'Retained main source/proof/predecessor drift: ' + name)
    return len(d['preserved_main_files'])


def validate_state(m, u, s, d, applied):
    state = d['after_state' if applied else 'before_state']
    require(digest(m) == state['membership_object_sha256'] and digest(u) == state['universe_object_sha256'],
            'Current whole state differs; partial/unrelated changes are not authorized')
    require(m['review_sha256'] == sealed_digest(m, 'review_sha256')
            and u['proposal_sha256'] == sealed_digest(u, 'proposal_sha256')
            and u['membership_review_sha256'] == m['review_sha256'], 'State seal differs')
    require(digest(s) == d['source_pool_object_sha256'] and len(s['sources']) == 1662,
            'Canonical source pool changed')
    require(m['authoritative_for_new_editorial_work'] is False and u['approval_receipt'] is None
            and all(u[k] is False for k in ['full_record_claim', 'synthesis_eligible', 'publication_authorized',
                'episode_acceptance_authorized', 'synthesis_authorized', 'publication_changes',
                'production_writes', 'full_issue_universe_closed']), 'Candidate universe promoted')
    require(len(m['records']) == len(u['candidate_dispositions']) == 676, 'Action population changed')
    counts = dict(Counter(r['disposition'] for r in u['candidate_dispositions']))
    require(u['accounting']['counts'] == counts and counts['source_unresolved'] == 6
            and counts['pending_interpretation'] == (246 if applied else 248)
            and counts['exact_action_ineligible'] == (129 if applied else 127), 'Expected effects differ')
    require(u['unresolved_action_ids'] == [r['action_id'] for r in u['candidate_dispositions']
            if r['disposition'] in ['source_unresolved', 'pending_interpretation']], 'Unresolved accounting differs')


def _materialize(membership, universe, d):
    m, u = copy.deepcopy(membership), copy.deepcopy(universe)
    proposed = {aid: x['proposed_record'] for aid, x in d['subjects'].items()}
    m['records'] = [copy.deepcopy(proposed.get(r['action_id'], r)) for r in m['records']]
    m['review_sha256'] = sealed_digest(m, 'review_sha256')
    for row in u['candidate_dispositions']:
        aid = row['action_id']
        if aid not in proposed:
            continue
        r = proposed[aid]
        row.update(disposition=r['disposition'], reason=r['rationale'], rationale=r['rationale'],
                   issue_boundary_status=r['disposition'], unresolved_reason=d['subjects'][aid]['after_unresolved_reason'])
        row['exact_action_source_binding']['complete'] = not r['exact_action_binding_unresolved']
        row['review_progress'].update({k: r[k] for k in ['substantive_review_performed',
            'exact_action_binding_unresolved', 'required_evidence_unavailable', 'authoritative_source_conflict']})
        row['review_progress']['shared_review_record_sha256'] = digest(r)
    counts = dict(Counter(r['disposition'] for r in u['candidate_dispositions']))
    u.update(proposal_id='full-universe-proposal:f000477:infrastructure:119:20260916:candidate-batch154',
             membership_review_sha256=m['review_sha256'],
             unresolved_action_ids=[r['action_id'] for r in u['candidate_dispositions']
                 if r['disposition'] in ['source_unresolved', 'pending_interpretation']])
    u['accounting'].update(counts=counts, action_ids_by_disposition={k: [r['action_id']
        for r in u['candidate_dispositions'] if r['disposition'] == k] for k in counts},
        exact_action_ineligible_actions=counts['exact_action_ineligible'],
        unresolved_boundary_cases=len(u['unresolved_action_ids']), accounting_scope=BOUNDARY)
    # Preserve the established legacy counter's meaning; this is not a count of unresolved binding flags.
    u['accounting']['official_source_readiness']['pending_package_version_bindings'] = counts['pending_interpretation']
    u['universe_subject_sha256'] = digest(dict(subject=u['subject'], cutoff=u['cutoff'],
                                             candidate_records=u['candidate_dispositions']))
    u['proposal_sha256'] = sealed_digest(u, 'proposal_sha256')
    return m, u


def apply_exact_decisions(membership, universe, sources, d):
    require(digest(d) == FROZEN_INPUT_SHA, 'Frozen approval/input drift')
    current = (digest(membership), digest(universe))
    before = tuple(d['before_state'][k] for k in ['membership_object_sha256', 'universe_object_sha256'])
    after = tuple(d['after_state'][k] for k in ['membership_object_sha256', 'universe_object_sha256'])
    require(current in [before, after], 'Partial, unrelated or unauthorized current state')
    already = current == after
    validate_state(membership, universe, sources, d, already)
    if already:
        return copy.deepcopy(membership), copy.deepcopy(universe), {'changed': False, 'action_ids': sorted(SCOPE)}
    m, u = _materialize(membership, universe, d)
    validate_state(m, u, sources, d, True)
    return m, u, {'changed': True, 'action_ids': sorted(SCOPE)}


def application_receipt(d, m, u):
    r = dict(kind='approved_eligibility_and_binding_only_application154', base_commit=BASE_COMMIT,
        predecessor=BASE, successor=OUT, governed_inputs_sha256=digest(d),
        human_approval_message_id=d['owner_evidence']['user_message_id'],
        approval_provenance=d['owner_evidence']['provenance'], eligibility_decisions=ELIGIBILITY,
        newly_resolved_bindings=BINDINGS, before_state=d['before_state'], after_state=d['after_state'],
        cases=d['subjects'], binding_evidence=d['binding_evidence'],
        accepted_authored_meanings=[], new_issue_admissions=[], new_sources=[],
        unchanged_other_records=668, canonical_sources=1662,
        preserved_semantic_facets='Old70 candidate and settled149 nine accepted/seven admitted; byte-identical inherited products.',
        meaning_eligibility_binding_are_separate=True, original8_binding_proposals_applied=False,
        other25_eligibility_decisions_applied=False, historical_falseflags_rewritten=False,
        source_holds_changed=False, source_acquisition=False, public_selection_changed=False,
        publication_authorized=False, production_authorized=False, Health_activation=False,
        full_day_PDF_verification_claimed=False,
        limitations=d['binding_limitations'], accounting=dict(u['accounting']['counts']))
    r['receipt_sha256'] = sealed_digest(r, 'receipt_sha256')
    return r


def materialize(root=ROOT, check=False):
    d = load_inputs(root)
    validate_pins(root, d)
    base, out = root / BASE, root / OUT
    require(not check or out.exists(), 'Successor is not materialized')
    current = out if out.exists() else base
    m, u, result = apply_exact_decisions(read(current / 'membership_review.json'),
        read(current / 'universe_proposal.json'), read(base / 'sources.json'), d)
    if result['changed']:
        require(not check and not out.exists(), 'Refuse partial overwrite or check-mode write')
        out.mkdir(parents=True)
        for suffix in d['snapshot_files']:
            target = out / suffix
            target.parent.mkdir(parents=True, exist_ok=True)
            if suffix not in ['membership_review.json', 'universe_proposal.json']:
                target.write_bytes((base / suffix).read_bytes())
        for name, value in [('membership_review.json', m), ('universe_proposal.json', u)]:
            (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (root / PACKET / 'application_receipt.json').write_text(
            json.dumps(application_receipt(d, m, u), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        require(digest(read(root / PACKET / 'application_receipt.json')) == digest(application_receipt(d, m, u)),
                'Existing application receipt drift')
        for suffix in d['snapshot_files']:
            if suffix not in ['membership_review.json', 'universe_proposal.json']:
                require(normalized_bytes(out / suffix) == normalized_bytes(base / suffix),
                        'Existing inherited source/semantic product drift: ' + suffix)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(materialize(check=args.check), indent=2))
