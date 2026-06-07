-- Procedural Context Production Import Preflight - Phase 6 rollback artifact
-- Review-only artifact. Do not run unless a later approved import needs rollback.
--
-- Scope:
-- - Limited to roll_call_id values 145, 146, 246, 247, 269, and 270.
-- - Production preflight found all six vote_interpretations rows already exist.
-- - Therefore rollback restores the previous values for those six rows.
-- - If a future import scope changes and inserts a target row that did not exist before,
--   delete only that inserted target row instead of touching any other records.

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
    (145, 'insufficient_evidence'::vote_interpretation_status, NULL::vote_position, NULL::vote_position, NULL, 'https://clerk.house.gov/evs/2025/roll160.xml', 'interpretation_v1', 'v1', NULL, NULL, NULL, NULL, 'house_of_representatives', NULL, '["question", "description", "source_url"]'::jsonb, NULL, NULL, NULL, NULL, NULL, 'codex_manual_source_enrichment', '2026-05-16 21:06:27.680087+00'::timestamptz),
    (146, 'insufficient_evidence'::vote_interpretation_status, NULL::vote_position, NULL::vote_position, NULL, 'https://clerk.house.gov/evs/2025/roll161.xml', 'interpretation_v1', 'v1', NULL, NULL, NULL, NULL, 'house_of_representatives', NULL, '["question", "description", "source_url"]'::jsonb, NULL, NULL, NULL, NULL, NULL, 'codex_manual_source_enrichment', '2026-05-16 21:06:27.680083+00'::timestamptz),
    (246, 'insufficient_evidence'::vote_interpretation_status, NULL::vote_position, NULL::vote_position, NULL, 'https://clerk.house.gov/evs/2025/roll267.xml', 'interpretation_v1', 'v1', NULL, NULL, NULL, NULL, 'house_of_representatives', NULL, '["question", "description", "source_url"]'::jsonb, NULL, NULL, NULL, NULL, NULL, 'codex_manual_source_enrichment', '2026-05-16 21:06:27.680055+00'::timestamptz),
    (247, 'insufficient_evidence'::vote_interpretation_status, NULL::vote_position, NULL::vote_position, NULL, 'https://clerk.house.gov/evs/2025/roll268.xml', 'interpretation_v1', 'v1', NULL, NULL, NULL, NULL, 'house_of_representatives', NULL, '["question", "description", "source_url"]'::jsonb, NULL, NULL, NULL, NULL, NULL, 'codex_manual_source_enrichment', '2026-05-16 21:06:27.680050+00'::timestamptz),
    (269, 'insufficient_evidence'::vote_interpretation_status, NULL::vote_position, NULL::vote_position, NULL, 'https://clerk.house.gov/evs/2025/roll290.xml', 'interpretation_v1', 'v1', NULL, NULL, NULL, NULL, 'house_of_representatives', NULL, '["question", "description", "source_url"]'::jsonb, NULL, NULL, NULL, NULL, NULL, 'codex_manual_source_enrichment', '2026-05-16 21:06:27.680025+00'::timestamptz),
    (270, 'insufficient_evidence'::vote_interpretation_status, NULL::vote_position, NULL::vote_position, NULL, 'https://clerk.house.gov/evs/2025/roll291.xml', 'interpretation_v1', 'v1', NULL, NULL, NULL, NULL, 'house_of_representatives', NULL, '["question", "description", "source_url"]'::jsonb, NULL, NULL, NULL, NULL, NULL, 'codex_manual_source_enrichment', '2026-05-16 21:06:27.680021+00'::timestamptz)
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
  AND vi.roll_call_id IN (145, 146, 246, 247, 269, 270);

COMMIT;
