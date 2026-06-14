-- Rollback for Phase 21 deterministic Senate vote classifications.
-- Scope: exact Phase 21 classification manifest target rows only.
BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM vote_interpretations
    WHERE roll_call_id = ANY(ARRAY[546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 562, 564, 565, 579, 580, 582, 583, 584, 585, 586, 587, 588, 471, 518, 520, 522, 523, 530, 531, 532, 534, 536, 537, 538, 539, 540]::bigint[])
  ) THEN
    RAISE EXCEPTION 'Phase 21 classification rollback stopped: target roll calls have interpretations.';
  END IF;
END $$;

DELETE FROM vote_classifications
WHERE roll_call_id = ANY(ARRAY[546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 562, 564, 565, 579, 580, 582, 583, 584, 585, 586, 587, 588, 471, 518, 520, 522, 523, 530, 531, 532, 534, 536, 537, 538, 539, 540]::bigint[])
  AND classification_version = 'v1';

COMMIT;
