"""Pure, bounded application of three owner-approved sealed candidate records."""
import copy
import hashlib
from collections import Counter

from backend.app.semantic_ir.shared_corpus import digest, sealed_digest

TRANSCRIPT_SHA256 = '85f409d5d596273b13585fd3e0bfaa196c6dc4789be251ee837a78be33eabe9b'
SUBJECTS = {
    'house:119:1:340': ('259b7ad000bc0e76ea90396547a5f761508baa49bcc1d0ff0dc3c2f9d2529e78',
                      '762ecdbd850ddf6ab88bcc3a3c7e98815ada26f8ea9b040e1a1f8e6936cef6ca',
                      '9d1c04ac2119d9bb762fa578a10214f7184f257013a7b07cc2a19f1f58e8982d', 'exact_action_ineligible'),
    'house:119:1:12': ('0d8d42953bf221030f0761bbe00acff16b76e281c97694137d649aaf2dd132e7',
                     '29cb74d93048c2e8eb4be8025712acfab5497f0478cc69299778e848062ec91f',
                     '2d6d92a9ecdc50ee81fd9acaa4fa9a5134fa845c6bb5fff2462cadbd378c9338', 'pending_interpretation'),
    'house:119:1:108': ('e5deaca10d13892f3c68d61fccbf923ecd6de0d7f2cb8a00d059bd96cc7c3311',
                      '21c530b4f67346c3d4cff28787be411680182664dc223309b53ea229b37f5a7b',
                      'b4dbe5d9617192fe971d8fa16702d48e75371d4828d41db65490f59b26789cdc', 'exact_action_ineligible'),
}
BOUNDARY = ('Owner-approved exact three-case application: H.R.4371 and H.R.1442 '
            'excluded with reviewed passage bindings; H.R.28 remains pending for '
            'its specific research boundary. All other records, sources and '
            'authored meanings preserved. No general taxonomy, approved universe, '
            'H.R.859 admission, publication or production authority.')
STATE_SEALS = {
    False: ('0beaa11b015482d43f81681d678a7200257f031b385dccdc56804d08b77dbad7',
            '661bad54322f4f0afb66fe2dd6dd0378219f6498f8cad4eb96af594c49aade64'),
    True: ('d149216e429afa0d988bd9f4aa29573997814b9ea578f652715f5a4116e8754b',
           '4c15b2dd9624ba0aca3710bfcb78612be6120b22612167f45b51c03756d017fa'),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def validate_state(membership, universe, applied):
    """Authenticate the whole bounded state, including the no-write path.

    Fixed pre/post seals reject even self-resealed bookkeeping or unrelated-row
    drift. Checking only the three record seals cannot authenticate a replay.
    """
    require(membership['authoritative_for_new_editorial_work'] is False
            and universe['approval_receipt'] is None
            and universe['publication_authorized'] is universe['full_record_claim'] is False,
            'Application escalated authority')
    counts = dict(Counter(row['disposition'] for row in universe['candidate_dispositions']))
    require(universe['accounting']['counts'] == counts, 'Derived accounting differs')
    require(universe['accounting']['action_ids_by_disposition'] == {
        key: [row['action_id'] for row in universe['candidate_dispositions'] if row['disposition'] == key]
        for key in counts}, 'Derived action groups differ')
    require(universe['unresolved_action_ids'] == [row['action_id'] for row in universe['candidate_dispositions']
            if row['disposition'] in ['source_unresolved', 'pending_interpretation']],
            'Derived unresolved actions differ')
    expected_m, expected_u = STATE_SEALS[applied]
    require(membership['review_sha256'] == sealed_digest(membership, 'review_sha256') == expected_m,
            'Bounded membership state differs')
    require(universe['proposal_sha256'] == sealed_digest(universe, 'proposal_sha256') == expected_u
            and universe['membership_review_sha256'] == expected_m
            and universe['universe_subject_sha256'] == digest(dict(subject=universe['subject'],
                cutoff=universe['cutoff'], candidate_records=universe['candidate_dispositions'])),
            'Bounded universe rows, accounting or authority differ')


def apply_exact_decisions(membership, universe, capture, proposals, authority):
    """Return new objects only; validate every subject before any mutation.

    Authority is honestly recorded trusted forwarded human history, not a
    cryptographic owner signature. Independent precommit review remains required.
    """
    require(hashlib.sha256(authority['three_case_transcript'].encode()).hexdigest() == TRANSCRIPT_SHA256
            and authority['scope']['reviewed_bundle_head'] == '28437fb5f0c79f7aa3b63faa705c8bb58ac1d7d0'
            and set(authority['scope']['case_actions']) == set(SUBJECTS)
            and authority['scope']['require_exact_seal_match'] is True
            and authority['scope']['case_independent_review_before_commit_push'] is True,
            'Owner evidence or bounded approval scope differs')
    require(set(proposals) == set(SUBJECTS), 'Approved action cohort differs')
    records = {r['action_id']: r for r in membership['records']}
    rows = {r['action_id']: r for r in universe['candidate_dispositions']}
    sources = {s['source_id']: s for s in capture['sources']}
    require(len(records) == len(rows) == 676 and len(sources) == 1621, 'Universe or source population differs')
    already = []
    for aid, (before_sha, row_sha, after_sha, disposition) in SUBJECTS.items():
        proposed = proposals[aid]['proposed_record']
        require(digest(proposed) == proposals[aid]['proposed_record_sha256'] == after_sha
                and proposed['action_id'] == aid and proposed['disposition'] == disposition,
                f'Approved proposed subject drift: {aid}')
        current_sha = digest(records[aid])
        require(current_sha in {before_sha, after_sha}, f'Current subject drift: {aid}')
        is_after = current_sha == after_sha
        if not is_after:
            require(digest(rows[aid]) == row_sha, f'Current universe row drift: {aid}')
        else:
            require(rows[aid]['review_progress']['shared_review_record_sha256'] == after_sha
                    and rows[aid]['disposition'] == disposition
                    and rows[aid]['exact_action_source_binding']['complete'] is True,
                    f'Already-applied universe row differs: {aid}')
        already.append(is_after)
        for ref in proposed['sources']:
            require(ref['source_id'] in sources
                    and all(sources[ref['source_id']][k] == v for k, v in ref.items()),
                    f'Approved source binding drift: {aid}')
        for claim in proposed['claim_source_map']:
            require(claim['source_id'] in {s['source_id'] for s in proposed['sources']}
                    and claim['passage'] in sources[claim['source_id']]['text'], f'Approved claim drift: {aid}')
    require(all(already) or not any(already), 'Partial application requires explicit reconciliation')
    validate_state(membership, universe, all(already))
    if all(already):
        return copy.deepcopy(membership), copy.deepcopy(universe), dict(changed=False, action_ids=list(SUBJECTS))
    m, u = copy.deepcopy(membership), copy.deepcopy(universe)
    changed_records = {aid: copy.deepcopy(proposals[aid]['proposed_record']) for aid in SUBJECTS}
    m['records'] = [changed_records.get(r['action_id'], r) for r in m['records']]
    m['review_sha256'] = sealed_digest(m, 'review_sha256')
    for row in u['candidate_dispositions']:
        aid = row['action_id']
        if aid not in changed_records:
            continue
        r = changed_records[aid]
        row.update(disposition=r['disposition'], reason=r['rationale'], rationale=r['rationale'],
                   issue_boundary_status=r['disposition'], sources=r['sources'], episode_candidate_id=r['episode_candidate_id'])
        if r['disposition'] == 'exact_action_ineligible':
            row['unresolved_reason'] = None
        row['exact_action_source_binding'].update(source_ids=[s['source_id'] for s in r['sources']],
                                                  complete=not r['exact_action_binding_unresolved'])
        row['review_progress'].update({k: r[k] for k in ['substantive_review_performed',
            'exact_action_binding_unresolved', 'required_evidence_unavailable', 'authoritative_source_conflict']})
        row['review_progress']['shared_review_record_sha256'] = digest(r)
    counts = dict(Counter(r['disposition'] for r in u['candidate_dispositions']))
    u.update(proposal_id='full-universe-proposal:f000477:infrastructure:119:20260916:candidate-batch139',
             membership_review_sha256=m['review_sha256'],
             unresolved_action_ids=[r['action_id'] for r in u['candidate_dispositions']
                                    if r['disposition'] in ['source_unresolved', 'pending_interpretation']])
    u['accounting'].update(counts=counts,
        action_ids_by_disposition={k: [r['action_id'] for r in u['candidate_dispositions'] if r['disposition'] == k] for k in counts},
        exact_action_ineligible_actions=counts['exact_action_ineligible'],
        unresolved_boundary_cases=len(u['unresolved_action_ids']), accounting_scope=BOUNDARY)
    u['accounting']['official_source_readiness']['pending_package_version_bindings'] = counts['pending_interpretation']
    u['universe_subject_sha256'] = digest(dict(subject=u['subject'], cutoff=u['cutoff'], candidate_records=u['candidate_dispositions']))
    u['proposal_sha256'] = sealed_digest(u, 'proposal_sha256')
    require(counts['pending_interpretation'] == 260 and counts['exact_action_ineligible'] == 122
            and counts['source_unresolved'] == 6 and counts['interpreted_substantive_directional'] == 69
            and counts['interpreted_substantive_non_directional'] == 1, 'Expected bounded effects differ')
    require(m['authoritative_for_new_editorial_work'] is False and u['approval_receipt'] is None
            and u['publication_authorized'] is u['full_record_claim'] is False, 'Application escalated authority')
    validate_state(m, u, True)
    return m, u, dict(changed=True, action_ids=list(SUBJECTS), before_counts=universe['accounting']['counts'],
                      after_counts=counts, other_records_unchanged=673, registered_sources_unchanged=1621)
