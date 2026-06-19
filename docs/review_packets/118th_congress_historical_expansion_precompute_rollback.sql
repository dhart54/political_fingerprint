-- Rollback for 118th Congress historical expansion derived-output precompute.
-- Prewrite dry-run found zero existing rows for window_end 2026-06-19 / classification_version v1.

BEGIN;

DELETE FROM summaries
WHERE window_end = DATE '2026-06-19'
  AND classification_version = 'v1';

DELETE FROM drift_scores
WHERE window_end = DATE '2026-06-19'
  AND classification_version = 'v1';

DELETE FROM chamber_medians
WHERE window_end = DATE '2026-06-19'
  AND classification_version = 'v1';

DELETE FROM fingerprints
WHERE window_end = DATE '2026-06-19'
  AND classification_version = 'v1';

COMMIT;
