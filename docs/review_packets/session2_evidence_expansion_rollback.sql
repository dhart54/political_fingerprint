-- Rollback for 2026 Evidence Eligibility And Interpretation Expansion.
-- Scope: exact roll_call_ids selected by session2_evidence_expansion dry-run.
BEGIN;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1474;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll005.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1474;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1475;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll006.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1475;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1476;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll007.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1476;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1482;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll013.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1482;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1484;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll015.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1484;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1487;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll018.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1487;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"EDUCATION_WORKFORCE": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1488;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll019.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1488;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1490;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll021.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1490;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1493;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll024.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1493;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1494;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll025.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1494;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1497;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll028.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1497;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1499;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll030.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1499;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1500;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll031.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1500;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1505;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll036.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1505;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1506;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll037.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1506;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1513;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll045.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1513;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1516;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll048.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1516;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1522;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll054.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1522;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1523;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll055.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1523;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1530;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll063.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1530;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1531;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll064.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1531;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1541;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll075.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1541;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1542;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll076.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1542;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1543;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll077.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1543;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1544;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll078.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1544;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1545;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll079.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1545;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1546;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll080.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1546;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1548;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll082.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1548;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1550;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll084.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1550;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1551;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll085.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1551;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1552;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll086.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1552;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1553;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll087.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1553;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1555;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll089.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1555;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1558;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll092.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1558;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1559;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll093.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1559;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1567;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll102.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1567;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1577;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll113.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1577;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1578;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll114.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1578;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1583;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll119.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1583;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1584;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll120.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1584;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1589;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll125.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1589;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1593;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll129.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1593;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1596;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll132.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1596;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1607;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll143.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1607;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1617;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll153.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1617;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1618;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll154.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1618;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1621;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll157.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1621;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1626;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll162.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1626;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1627;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll163.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1627;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1628;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll164.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1628;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1629;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll165.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1629;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1632;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll168.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1632;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1633;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll169.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1633;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1634;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll170.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1634;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1635;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll171.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1635;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1651;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll187.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1651;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1652;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll188.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1652;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1661;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll197.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1661;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1662;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll198.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1662;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1663;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll199.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1663;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1665;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll201.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1665;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1673;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as procedural_vote.',
    source_url = 'https://clerk.house.gov/evs/2026/roll209.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1673;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"EDUCATION_WORKFORCE": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1681;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://clerk.house.gov/evs/2026/roll217.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1681;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1734;

UPDATE vote_interpretations
SET
    interpretation_status = 'insufficient_evidence'::vote_interpretation_status,
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Not interpreted because the roll call is classified as low_classification_confidence.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00113.xml',
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
    reviewed_by = NULL,
    reviewed_at = NULL,
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    updated_at = NOW()
WHERE roll_call_id = 1734;

COMMIT;
