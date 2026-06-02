ALTER TABLE race_candidates
    ADD COLUMN IF NOT EXISTS external_candidate_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_race_candidates_external_source
    ON race_candidates (race_id, source_type, external_candidate_id)
    WHERE external_candidate_id IS NOT NULL;
