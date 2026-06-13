-- Rollback for Phase 20B Senate evidence classification writes.
-- Scope: vote_classifications rows from senate_evidence_classification_manifest_phase_20b.json only.
-- This rollback does not touch roll_calls, votes_cast, vote_contexts, senate_amendment_references, or vote_interpretations.
BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM vote_interpretations
    WHERE roll_call_id = ANY(ARRAY[516, 517, 524, 525, 526, 528, 529, 535, 545, 561, 563, 426, 578, 581, 468, 618]::bigint[])
  ) THEN
    RAISE EXCEPTION 'Phase 20B rollback stopped: target roll calls have vote_interpretations rows.';
  END IF;
END $$;

DELETE FROM vote_classifications
WHERE roll_call_id = ANY(ARRAY[516, 517, 524, 525, 526, 528, 529, 535, 545, 561, 563, 426, 578, 581, 468, 618]::bigint[])
  AND classification_version = 'v1';

COMMIT;
