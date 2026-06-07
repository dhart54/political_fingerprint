-- Rollback for Batch 010 / Phase 9A preflight.
-- Review-only artifact. Do not run unless a later approved import of batch_010
-- needs rollback.
--
-- Scope:
-- - Limited to roll_call_id 30 only.
-- - Production preflight found an existing vote_interpretations row for roll_call_id 30.
-- - Therefore this rollback restores the previous values for that one row.
-- - If a future preflight finds no existing row before import, rollback must instead
--   delete only the inserted roll_call_id 30 row.

BEGIN;

WITH previous_values (
    roll_call_id,
    interpretation_status,
    support_position,
    oppose_position,
    interpretation_reason,
    source_url,
    interpretation_version,
    classification_version,
    plain_english_summary,
    yea_meaning,
    nay_meaning,
    policy_effect,
    issue_facet,
    confidence,
    source_basis,
    uncertainty_note,
    what_happened,
    why_it_mattered,
    member_vote_context,
    what_not_to_infer,
    reviewed_by,
    reviewed_at
) AS (
    VALUES
    (
        30,
        'ambiguous'::vote_interpretation_status,
        NULL::vote_position,
        NULL::vote_position,
        'Manual review found amendment wording without enough official amendment text to assign yea/nay meaning.',
        'https://clerk.house.gov/evs/2025/roll032.xml',
        'interpretation_v1',
        'v1',
        NULL,
        NULL,
        NULL,
        NULL,
        'administrative_law_and_regulatory_procedures',
        NULL,
        '["question", "description", "source_url"]'::jsonb,
        'The packet identifies an amendment vote, but the cached bill summary describes the underlying bill rather than the exact amendment change.',
        NULL,
        NULL,
        NULL,
        NULL,
        'codex_manual_source_enrichment',
        '2026-05-16 21:06:27.680161+00'::timestamptz
    )
)
UPDATE vote_interpretations vi
SET
    interpretation_status = pv.interpretation_status,
    support_position = pv.support_position,
    oppose_position = pv.oppose_position,
    interpretation_reason = pv.interpretation_reason,
    source_url = pv.source_url,
    interpretation_version = pv.interpretation_version,
    classification_version = pv.classification_version,
    plain_english_summary = pv.plain_english_summary,
    yea_meaning = pv.yea_meaning,
    nay_meaning = pv.nay_meaning,
    policy_effect = pv.policy_effect,
    issue_facet = pv.issue_facet,
    confidence = pv.confidence,
    source_basis = pv.source_basis,
    uncertainty_note = pv.uncertainty_note,
    what_happened = pv.what_happened,
    why_it_mattered = pv.why_it_mattered,
    member_vote_context = pv.member_vote_context,
    what_not_to_infer = pv.what_not_to_infer,
    reviewed_by = pv.reviewed_by,
    reviewed_at = pv.reviewed_at,
    updated_at = NOW()
FROM previous_values pv
WHERE vi.roll_call_id = pv.roll_call_id
  AND vi.roll_call_id = 30;

COMMIT;
