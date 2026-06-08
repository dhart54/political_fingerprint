-- Senate Fact-Only Import Rollback Plan - Phase 12
--
-- Planning artifact only. Do not run unless a later explicitly approved
-- Senate fact-only production import has been executed.
--
-- Scope:
-- - chamber = senate
-- - congress = 119
-- - rollcall_number in the Phase 11/12 manifest first-load set
-- - no vote_interpretations rows may be deleted or modified

BEGIN;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (97), (150), (151), (161), (162), (169), (191), (206),
        (207), (222), (223), (224), (228), (231), (232), (236),
        (239), (276), (277), (278), (279), (280), (281)
),
target_roll_calls AS (
    SELECT rc.id, rc.rollcall_number
    FROM roll_calls rc
    JOIN target_rolls tr
      ON tr.rollcall_number = rc.rollcall_number
    WHERE rc.chamber = 'senate'
      AND rc.congress = 119
),
interpretation_guard AS (
    SELECT COUNT(*) AS interpretation_rows
    FROM vote_interpretations vi
    JOIN target_roll_calls trc
      ON trc.id = vi.roll_call_id
)
SELECT
    CASE
        WHEN interpretation_rows = 0 THEN 'ok_no_interpretations_on_target_rolls'
        ELSE 'stop_interpretations_exist_manual_review_required'
    END AS rollback_guard_status,
    interpretation_rows
FROM interpretation_guard;

-- Stop manually if the guard query above reports interpretation_rows > 0.
-- This rollback plan is not approved to delete or modify vote_interpretations.

WITH target_rolls(rollcall_number) AS (
    VALUES
        (97), (150), (151), (161), (162), (169), (191), (206),
        (207), (222), (223), (224), (228), (231), (232), (236),
        (239), (276), (277), (278), (279), (280), (281)
),
target_roll_calls AS (
    SELECT rc.id
    FROM roll_calls rc
    JOIN target_rolls tr
      ON tr.rollcall_number = rc.rollcall_number
    WHERE rc.chamber = 'senate'
      AND rc.congress = 119
      AND NOT EXISTS (
          SELECT 1
          FROM vote_interpretations vi
          WHERE vi.roll_call_id = rc.id
      )
)
DELETE FROM vote_contexts vc
USING target_roll_calls trc
WHERE vc.roll_call_id = trc.id;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (97), (150), (151), (161), (162), (169), (191), (206),
        (207), (222), (223), (224), (228), (231), (232), (236),
        (239), (276), (277), (278), (279), (280), (281)
),
target_roll_calls AS (
    SELECT rc.id
    FROM roll_calls rc
    JOIN target_rolls tr
      ON tr.rollcall_number = rc.rollcall_number
    WHERE rc.chamber = 'senate'
      AND rc.congress = 119
      AND NOT EXISTS (
          SELECT 1
          FROM vote_interpretations vi
          WHERE vi.roll_call_id = rc.id
      )
)
DELETE FROM votes_cast v
USING target_roll_calls trc
WHERE v.roll_call_id = trc.id;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (97), (150), (151), (161), (162), (169), (191), (206),
        (207), (222), (223), (224), (228), (231), (232), (236),
        (239), (276), (277), (278), (279), (280), (281)
)
DELETE FROM roll_calls rc
USING target_rolls tr
WHERE rc.chamber = 'senate'
  AND rc.congress = 119
  AND rc.rollcall_number = tr.rollcall_number
  AND NOT EXISTS (
      SELECT 1
      FROM vote_interpretations vi
      WHERE vi.roll_call_id = rc.id
  );

-- Delete bills only when they are exact Phase 12 bill keys and no remaining
-- roll_call references them. This protects bill rows that preexisted the import
-- or are used by other House/Senate roll calls.
WITH target_bills(congress, bill_type, bill_number) AS (
    VALUES
        (119, 'hjres', 35),
        (119, 'hjres', 25),
        (119, 'hjres', 24),
        (119, 'hconres', 14),
        (119, 'hjres', 20),
        (119, 'hjres', 42),
        (119, 'hjres', 75),
        (119, 'hjres', 61),
        (119, 'hjres', 60),
        (119, 'hjres', 88),
        (119, 'hjres', 87),
        (119, 'hjres', 89)
)
DELETE FROM bills b
USING target_bills tb
WHERE b.congress = tb.congress
  AND b.bill_type = tb.bill_type
  AND b.bill_number = tb.bill_number
  AND NOT EXISTS (
      SELECT 1
      FROM roll_calls rc
      WHERE rc.bill_id = b.id
  );

COMMIT;
