-- Rollback for 2026 Evidence Eligibility And Interpretation Expansion derived precompute refresh.
-- Scope: the 2026-06-17 v1 precomputed output window refreshed after the
-- session-2 classification and interpretation update.
--
-- This rollback removes only derived outputs. It does not touch bills,
-- legislators, roll_calls, votes_cast, vote_contexts, vote_classifications,
-- or vote_interpretations. Re-running the approved precompute refresh can
-- rebuild the derived window after rollback.

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
