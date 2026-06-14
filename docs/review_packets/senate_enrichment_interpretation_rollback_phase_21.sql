-- Rollback for Phase 21 Senate interpretation imports.
-- Scope: exact batch_017 and batch_018 target roll_call_ids only.
-- For procedural update rows 381-386, Phase 21 overwrote the exact prior
-- reviewed_at/updated_at metadata. Those exact historical timestamp values are
-- no longer recoverable from current production, so this rollback does not
-- fabricate them. It restores the best-supported pre-Phase-21 product content
-- from docs/interpretation_batches/batch_007_thom_infra_interpretations.json
-- and restores reviewed_by to codex_manual_review, supported by untouched
-- sibling row 390 from the same prior batch. This is a timestamp metadata
-- limitation only; support/oppose positions remain null and non-counting.
BEGIN;

DELETE FROM vote_interpretations
WHERE roll_call_id = ANY(ARRAY[518, 520, 522, 523, 530, 531, 532, 534, 536, 537, 538, 540, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 562, 564, 565, 579, 580, 582, 583, 584, 585, 586, 587, 588, 471]::bigint[]);

UPDATE vote_interpretations
SET interpretation_status = 'ambiguous',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Manual review left this as ambiguous because the vote concerned a parliamentary appeal rather than direct passage or rejection of the underlying joint resolution.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00266.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = 'floor_procedure_on_hydrogen_vehicle_rule',
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = 'The official record identifies a motion to table a parliamentary appeal during consideration of S.J.Res.55. The packet does not explain the appeal well enough to map the vote to a clear policy position on hydrogen-vehicle safety standards.',
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = 'codex_manual_review',
    reviewed_at = NULL
WHERE roll_call_id = 381;

UPDATE vote_interpretations
SET interpretation_status = 'ambiguous',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Manual review left this as ambiguous because the vote was a floor-timing motion, not passage or rejection of the underlying joint resolution.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00267.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = 'floor_procedure_on_hydrogen_vehicle_rule',
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = 'The official record identifies a motion to recess for ninety minutes during consideration of S.J.Res.55. It does not show a direct policy choice on hydrogen-vehicle safety standards.',
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = 'codex_manual_review',
    reviewed_at = NULL
WHERE roll_call_id = 382;

UPDATE vote_interpretations
SET interpretation_status = 'ambiguous',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Manual review left this as ambiguous because the vote was a floor-timing motion, not passage or rejection of the underlying joint resolution.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00268.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = 'floor_procedure_on_hydrogen_vehicle_rule',
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = 'The official record identifies a motion to recess for sixty minutes during consideration of S.J.Res.55. It does not show a direct policy choice on hydrogen-vehicle safety standards.',
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = 'codex_manual_review',
    reviewed_at = NULL
WHERE roll_call_id = 383;

UPDATE vote_interpretations
SET interpretation_status = 'ambiguous',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Manual review left this as ambiguous because the vote was a floor-timing motion, not passage or rejection of the underlying joint resolution.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00269.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = 'floor_procedure_on_hydrogen_vehicle_rule',
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = 'The official record identifies a motion to recess for thirty minutes during consideration of S.J.Res.55. It does not show a direct policy choice on hydrogen-vehicle safety standards.',
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = 'codex_manual_review',
    reviewed_at = NULL
WHERE roll_call_id = 384;

UPDATE vote_interpretations
SET interpretation_status = 'ambiguous',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Manual review left this as ambiguous because the vote was a floor-timing motion, not passage or rejection of the underlying joint resolution.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00270.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = 'floor_procedure_on_hydrogen_vehicle_rule',
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = 'The official record identifies a motion to recess for fifteen minutes during consideration of S.J.Res.55. It does not show a direct policy choice on hydrogen-vehicle safety standards.',
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = 'codex_manual_review',
    reviewed_at = NULL
WHERE roll_call_id = 385;

UPDATE vote_interpretations
SET interpretation_status = 'ambiguous',
    support_position = NULL,
    oppose_position = NULL,
    interpretation_reason = 'Manual review left this as ambiguous because the vote was a floor-timing motion, not passage or rejection of the underlying joint resolution.',
    source_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1191/vote_119_1_00271.xml',
    interpretation_version = 'interpretation_v1',
    classification_version = 'v1',
    plain_english_summary = NULL,
    yea_meaning = NULL,
    nay_meaning = NULL,
    policy_effect = NULL,
    issue_facet = 'floor_procedure_on_hydrogen_vehicle_rule',
    confidence = NULL,
    source_basis = '[]'::jsonb,
    uncertainty_note = 'The official record identifies a motion to recess for ten minutes during consideration of S.J.Res.55. It does not show a direct policy choice on hydrogen-vehicle safety standards.',
    what_happened = NULL,
    why_it_mattered = NULL,
    member_vote_context = NULL,
    what_not_to_infer = NULL,
    reviewed_by = 'codex_manual_review',
    reviewed_at = NULL
WHERE roll_call_id = 386;

COMMIT;
