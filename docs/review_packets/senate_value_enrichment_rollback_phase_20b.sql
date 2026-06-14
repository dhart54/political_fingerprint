-- Rollback plan for a future approved import of batch_016_senate_amendment_value_substantive_candidates.
-- Scope: vote_interpretations rows for the exact Phase 20B substantive package only.
-- This rollback does not touch vote_classifications, roll_calls, votes_cast, vote_contexts,
-- senate_amendment_references, bills, support/opposition logic, or alignment logic.

BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM vote_interpretations vi
    WHERE vi.roll_call_id = ANY(ARRAY[524, 526, 535, 545, 561, 563, 578, 581, 468, 618]::bigint[])
      AND vi.interpretation_version IS DISTINCT FROM 'interpretation_v1'
  ) THEN
    RAISE EXCEPTION 'Phase 20B rollback stopped: target rows have unexpected interpretation_version values.';
  END IF;
END $$;

DELETE FROM vote_interpretations
WHERE roll_call_id = ANY(ARRAY[524, 526, 535, 545, 561, 563, 578, 581, 468, 618]::bigint[]);

COMMIT;
