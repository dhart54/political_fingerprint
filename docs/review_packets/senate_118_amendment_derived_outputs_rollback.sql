-- Rollback coverage for 118th Senate amendment source-enrichment derived outputs.
-- No derived-output tables were written in this milestone.
-- The scoped public reads validated after the bounded write use the updated classifications
-- and interpretations directly, and retaining a rolling precompute recompute would risk
-- changing current 119th public outputs.
BEGIN;
-- No-op by design.
COMMIT;
