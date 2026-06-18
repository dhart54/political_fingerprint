-- Rollback for Current-Congress Freshness derived precompute refresh.
-- Scope: the 2026-06-17 v1 precomputed output window created after the
-- 2026 House/Senate fact refresh.
--
-- This rollback does not touch bills, legislators, roll_calls, votes_cast,
-- vote_contexts, vote_classifications, or vote_interpretations.

BEGIN;

DELETE FROM summaries
WHERE window_end = DATE '2026-06-17'
  AND classification_version = 'v1';

DELETE FROM drift_scores
WHERE window_end = DATE '2026-06-17'
  AND classification_version = 'v1';

DELETE FROM chamber_medians
WHERE window_end = DATE '2026-06-17'
  AND classification_version = 'v1';

DELETE FROM fingerprints
WHERE window_end = DATE '2026-06-17'
  AND classification_version = 'v1';

COMMIT;
