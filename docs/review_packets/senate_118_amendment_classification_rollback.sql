-- Rollback for 118th Senate amendment source-enrichment classifications.
-- Scope: exact source-packet-approved roll_call_ids only.
BEGIN;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2454;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2456;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2457;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2459;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3047;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3055;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3056;

COMMIT;
