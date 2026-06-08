-- Senate Fact-Only Expansion Rollback Plan - Phase 14
--
-- Planning artifact only. Do not run unless the explicitly approved
-- Phase 14 Senate fact-only production import has been executed.
--
-- Scope:
-- - chamber = senate
-- - congress = 119
-- - rollcall_number in the Phase 14 manifest target set
-- - no vote_interpretations rows may be deleted or modified

BEGIN;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (391), (392), (394), (395), (396), (398), (399), (401), (403), (411),
        (423), (428), (454), (455), (500), (503), (510), (513), (514), (515),
        (516), (517), (520), (521), (527), (528), (533), (534), (535), (536),
        (537), (540), (541), (542), (543), (544), (545), (548), (549), (550),
        (551), (553), (554), (555), (556), (557), (558), (559), (560), (570),
        (571), (572), (573), (575), (576), (581), (585), (590), (594), (595),
        (597), (598), (599), (600), (603), (608), (609), (610), (611), (617)
),
target_roll_calls AS (
    SELECT rc.id, rc.bill_id, rc.rollcall_number
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
        (391), (392), (394), (395), (396), (398), (399), (401), (403), (411),
        (423), (428), (454), (455), (500), (503), (510), (513), (514), (515),
        (516), (517), (520), (521), (527), (528), (533), (534), (535), (536),
        (537), (540), (541), (542), (543), (544), (545), (548), (549), (550),
        (551), (553), (554), (555), (556), (557), (558), (559), (560), (570),
        (571), (572), (573), (575), (576), (581), (585), (590), (594), (595),
        (597), (598), (599), (600), (603), (608), (609), (610), (611), (617)
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
        (391), (392), (394), (395), (396), (398), (399), (401), (403), (411),
        (423), (428), (454), (455), (500), (503), (510), (513), (514), (515),
        (516), (517), (520), (521), (527), (528), (533), (534), (535), (536),
        (537), (540), (541), (542), (543), (544), (545), (548), (549), (550),
        (551), (553), (554), (555), (556), (557), (558), (559), (560), (570),
        (571), (572), (573), (575), (576), (581), (585), (590), (594), (595),
        (597), (598), (599), (600), (603), (608), (609), (610), (611), (617)
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
DELETE FROM votes_cast vc
USING target_roll_calls trc
WHERE vc.roll_call_id = trc.id;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (391), (392), (394), (395), (396), (398), (399), (401), (403), (411),
        (423), (428), (454), (455), (500), (503), (510), (513), (514), (515),
        (516), (517), (520), (521), (527), (528), (533), (534), (535), (536),
        (537), (540), (541), (542), (543), (544), (545), (548), (549), (550),
        (551), (553), (554), (555), (556), (557), (558), (559), (560), (570),
        (571), (572), (573), (575), (576), (581), (585), (590), (594), (595),
        (597), (598), (599), (600), (603), (608), (609), (610), (611), (617)
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
DELETE FROM roll_calls rc
USING target_roll_calls trc
WHERE rc.id = trc.id;

-- Delete bills inserted solely for the Phase 14 package only when no remaining
-- roll_calls reference them. This avoids touching bills shared with existing rows.
WITH candidate_bills(congress, bill_type, bill_number) AS (
    VALUES
        (119, 'hjres', 104), (119, 'hjres', 105), (119, 'hjres', 106),
        (119, 'hr', 4), (119, 'hr', 3944), (119, 'hr', 4016),
        (119, 'hr', 5371), (119, 's', 22), (119, 's', 2296),
        (119, 's', 2806), (119, 's', 2882), (119, 's', 3012),
        (119, 'sjres', 34), (119, 'sjres', 41), (119, 'sjres', 60),
        (119, 'sjres', 69), (119, 'sjres', 71), (119, 'sjres', 77),
        (119, 'sjres', 80), (119, 'sjres', 81), (119, 'sjres', 83),
        (119, 'sjres', 88), (119, 'sjres', 90), (119, 'sres', 377),
        (119, 'sres', 412)
)
DELETE FROM bills b
USING candidate_bills cb
WHERE b.congress = cb.congress
  AND b.bill_type = cb.bill_type
  AND b.bill_number = cb.bill_number
  AND NOT EXISTS (
      SELECT 1
      FROM roll_calls rc
      WHERE rc.bill_id = b.id
  );

COMMIT;
