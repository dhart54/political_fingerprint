BEGIN;

ALTER TABLE vote_interpretations
    ADD COLUMN IF NOT EXISTS what_happened TEXT,
    ADD COLUMN IF NOT EXISTS why_it_mattered TEXT,
    ADD COLUMN IF NOT EXISTS member_vote_context TEXT,
    ADD COLUMN IF NOT EXISTS what_not_to_infer TEXT;

COMMIT;
