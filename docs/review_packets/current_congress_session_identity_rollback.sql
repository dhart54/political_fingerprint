-- Rollback for Phase: Current-Congress Freshness And Automated Ingestion
-- Scope: schema/metadata rollback for the session-aware roll_calls identity migration.
-- Precondition: run only after removing any 2026/current-refresh rows inserted under
-- the session-aware identity. This rollback intentionally aborts if session 2 rows exist.

BEGIN;

DO $$
DECLARE
    session_two_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO session_two_count
    FROM roll_calls
    WHERE session = 2;

    IF session_two_count > 0 THEN
        RAISE EXCEPTION 'Refusing schema rollback while % session=2 roll_calls remain. Remove refresh rows first.', session_two_count;
    END IF;
END $$;

ALTER TABLE roll_calls
    DROP CONSTRAINT IF EXISTS roll_calls_chamber_congress_session_rollcall_number_key;

DROP INDEX IF EXISTS idx_roll_calls_session_identity;

ALTER TABLE roll_calls
    DROP CONSTRAINT IF EXISTS roll_calls_session_valid;

ALTER TABLE roll_calls
    ALTER COLUMN session DROP NOT NULL;

-- Restore the exact known pre-migration nullable-session shape observed in
-- production preflight:
--   House 119 / 2025 ids 1-339 had NULL session.
--   Senate 119 / 2025 ids 340-419 had NULL session.
--   Senate 119 / 2025 ids 420-624 already had session = 1.
UPDATE roll_calls
SET session = NULL
WHERE congress = 119
  AND EXTRACT(YEAR FROM vote_date)::integer = 2025
  AND (
    (chamber = 'house' AND id BETWEEN 1 AND 339)
    OR (chamber = 'senate' AND id BETWEEN 340 AND 419)
  );

ALTER TABLE roll_calls
    ADD CONSTRAINT roll_calls_chamber_congress_rollcall_number_key
    UNIQUE (chamber, congress, rollcall_number);

COMMIT;
