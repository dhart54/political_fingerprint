-- Rollback for 118th Senate amendment source-enrichment interpretations.
-- Scope: exact source-packet-approved roll_call_ids only.
BEGIN;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1181/vote_118_1_00071.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 2454;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1181/vote_118_1_00073.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 2456;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1181/vote_118_1_00074.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 2457;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1181/vote_118_1_00076.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 2459;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1182/vote_118_2_00081.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 3047;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1182/vote_118_2_00107.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 3055;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1182/vote_118_2_00108.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = NULL,
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = NULL,
    updated_at = NOW()
WHERE roll_call_id = 3056;

COMMIT;
