BEGIN;

-- Roll-call numbers restart by official session inside a Congress. The previous
-- uniqueness model keyed only on chamber/congress/rollcall_number, which cannot
-- safely store both 2025 and 2026 rows for the 119th Congress.

ALTER TABLE roll_calls
    ADD COLUMN IF NOT EXISTS session INTEGER;

UPDATE roll_calls
SET session = CASE
    WHEN EXTRACT(YEAR FROM vote_date)::integer = (1789 + ((congress - 1) * 2)) THEN 1
    WHEN EXTRACT(YEAR FROM vote_date)::integer = (1790 + ((congress - 1) * 2)) THEN 2
    ELSE session
END
WHERE session IS NULL;

ALTER TABLE roll_calls
    ADD CONSTRAINT roll_calls_session_valid
    CHECK (session IN (1, 2)) NOT VALID;

ALTER TABLE roll_calls
    VALIDATE CONSTRAINT roll_calls_session_valid;

ALTER TABLE roll_calls
    ALTER COLUMN session SET NOT NULL;

DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO duplicate_count
    FROM (
        SELECT chamber, congress, session, rollcall_number
        FROM roll_calls
        GROUP BY chamber, congress, session, rollcall_number
        HAVING COUNT(*) > 1
    ) duplicates;

    IF duplicate_count > 0 THEN
        RAISE EXCEPTION 'roll_calls contains duplicate session-aware identities: %', duplicate_count;
    END IF;
END $$;

ALTER TABLE roll_calls
    DROP CONSTRAINT IF EXISTS roll_calls_chamber_congress_rollcall_number_key;

ALTER TABLE roll_calls
    ADD CONSTRAINT roll_calls_chamber_congress_session_rollcall_number_key
    UNIQUE (chamber, congress, session, rollcall_number);

CREATE INDEX IF NOT EXISTS idx_roll_calls_session_identity
    ON roll_calls (chamber, congress, session, rollcall_number);

COMMIT;
