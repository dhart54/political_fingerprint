-- Phase 18 Senate amendment fact-only rollback plan.
-- Do not run unless a separately approved Phase 18/19 import has actually run.
-- Scope: only the 112 target 119th Congress / 2025 Senate amendment roll numbers in
-- docs/review_packets/senate_amendment_fact_import_manifest_phase_18.json.
--
-- This rollback intentionally does not insert, update, or delete vote_interpretations.
-- The senate_amendment_references table should remain in place after rollback unless a
-- separate schema rollback is explicitly approved.

BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM vote_interpretations vi
        JOIN roll_calls rc
          ON rc.id = vi.roll_call_id
        WHERE rc.chamber = 'senate'
          AND rc.congress = 119
          AND rc.rollcall_number = ANY(ARRAY[
              3, 4, 6, 62, 63, 64, 65, 66, 67, 68,
              69, 70, 71, 72, 73, 74, 75, 76, 77, 78,
              79, 80, 81, 82, 83, 84, 85, 86, 129, 130,
              131, 132, 170, 171, 172, 173, 174, 175, 176, 177,
              178, 179, 180, 181, 182, 183, 184, 185, 186, 187,
              188, 189, 190, 309, 310, 311, 330, 339, 341, 342,
              343, 345, 352, 355, 356, 358, 360, 361, 362, 363,
              364, 365, 366, 367, 368, 369, 370, 371, 393, 397,
              400, 402, 404, 405, 406, 407, 408, 409, 410, 472,
              473, 474, 475, 476, 477, 478, 479, 481, 512, 562,
              563, 564, 565, 566, 567, 568, 569, 612, 613, 614,
              615, 616
          ])
    ) THEN
        RAISE EXCEPTION 'Rollback refused: target Senate amendment roll calls have vote_interpretations rows.';
    END IF;
END $$;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (3), (4), (6), (62), (63), (64), (65), (66), (67), (68),
        (69), (70), (71), (72), (73), (74), (75), (76), (77), (78),
        (79), (80), (81), (82), (83), (84), (85), (86), (129), (130),
        (131), (132), (170), (171), (172), (173), (174), (175), (176), (177),
        (178), (179), (180), (181), (182), (183), (184), (185), (186), (187),
        (188), (189), (190), (309), (310), (311), (330), (339), (341), (342),
        (343), (345), (352), (355), (356), (358), (360), (361), (362), (363),
        (364), (365), (366), (367), (368), (369), (370), (371), (393), (397),
        (400), (402), (404), (405), (406), (407), (408), (409), (410), (472),
        (473), (474), (475), (476), (477), (478), (479), (481), (512), (562),
        (563), (564), (565), (566), (567), (568), (569), (612), (613), (614),
        (615), (616)
),
target_roll_call_ids AS (
    SELECT rc.id, rc.bill_id
    FROM roll_calls rc
    JOIN target_rolls tr
      ON tr.rollcall_number = rc.rollcall_number
    WHERE rc.chamber = 'senate'
      AND rc.congress = 119
)
DELETE FROM senate_amendment_references sar
USING target_roll_call_ids target
WHERE sar.roll_call_id = target.id;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (3), (4), (6), (62), (63), (64), (65), (66), (67), (68),
        (69), (70), (71), (72), (73), (74), (75), (76), (77), (78),
        (79), (80), (81), (82), (83), (84), (85), (86), (129), (130),
        (131), (132), (170), (171), (172), (173), (174), (175), (176), (177),
        (178), (179), (180), (181), (182), (183), (184), (185), (186), (187),
        (188), (189), (190), (309), (310), (311), (330), (339), (341), (342),
        (343), (345), (352), (355), (356), (358), (360), (361), (362), (363),
        (364), (365), (366), (367), (368), (369), (370), (371), (393), (397),
        (400), (402), (404), (405), (406), (407), (408), (409), (410), (472),
        (473), (474), (475), (476), (477), (478), (479), (481), (512), (562),
        (563), (564), (565), (566), (567), (568), (569), (612), (613), (614),
        (615), (616)
),
target_roll_call_ids AS (
    SELECT rc.id, rc.bill_id
    FROM roll_calls rc
    JOIN target_rolls tr
      ON tr.rollcall_number = rc.rollcall_number
    WHERE rc.chamber = 'senate'
      AND rc.congress = 119
)
DELETE FROM vote_contexts vc
USING target_roll_call_ids target
WHERE vc.roll_call_id = target.id;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (3), (4), (6), (62), (63), (64), (65), (66), (67), (68),
        (69), (70), (71), (72), (73), (74), (75), (76), (77), (78),
        (79), (80), (81), (82), (83), (84), (85), (86), (129), (130),
        (131), (132), (170), (171), (172), (173), (174), (175), (176), (177),
        (178), (179), (180), (181), (182), (183), (184), (185), (186), (187),
        (188), (189), (190), (309), (310), (311), (330), (339), (341), (342),
        (343), (345), (352), (355), (356), (358), (360), (361), (362), (363),
        (364), (365), (366), (367), (368), (369), (370), (371), (393), (397),
        (400), (402), (404), (405), (406), (407), (408), (409), (410), (472),
        (473), (474), (475), (476), (477), (478), (479), (481), (512), (562),
        (563), (564), (565), (566), (567), (568), (569), (612), (613), (614),
        (615), (616)
),
target_roll_call_ids AS (
    SELECT rc.id, rc.bill_id
    FROM roll_calls rc
    JOIN target_rolls tr
      ON tr.rollcall_number = rc.rollcall_number
    WHERE rc.chamber = 'senate'
      AND rc.congress = 119
)
DELETE FROM votes_cast vc
USING target_roll_call_ids target
WHERE vc.roll_call_id = target.id;

CREATE TEMP TABLE phase18_target_bill_ids ON COMMIT DROP AS
WITH target_rolls(rollcall_number) AS (
    VALUES
        (3), (4), (6), (62), (63), (64), (65), (66), (67), (68),
        (69), (70), (71), (72), (73), (74), (75), (76), (77), (78),
        (79), (80), (81), (82), (83), (84), (85), (86), (129), (130),
        (131), (132), (170), (171), (172), (173), (174), (175), (176), (177),
        (178), (179), (180), (181), (182), (183), (184), (185), (186), (187),
        (188), (189), (190), (309), (310), (311), (330), (339), (341), (342),
        (343), (345), (352), (355), (356), (358), (360), (361), (362), (363),
        (364), (365), (366), (367), (368), (369), (370), (371), (393), (397),
        (400), (402), (404), (405), (406), (407), (408), (409), (410), (472),
        (473), (474), (475), (476), (477), (478), (479), (481), (512), (562),
        (563), (564), (565), (566), (567), (568), (569), (612), (613), (614),
        (615), (616)
)
SELECT DISTINCT rc.bill_id
FROM roll_calls rc
JOIN target_rolls tr
  ON tr.rollcall_number = rc.rollcall_number
WHERE rc.chamber = 'senate'
  AND rc.congress = 119
  AND rc.bill_id IS NOT NULL;

WITH target_rolls(rollcall_number) AS (
    VALUES
        (3), (4), (6), (62), (63), (64), (65), (66), (67), (68),
        (69), (70), (71), (72), (73), (74), (75), (76), (77), (78),
        (79), (80), (81), (82), (83), (84), (85), (86), (129), (130),
        (131), (132), (170), (171), (172), (173), (174), (175), (176), (177),
        (178), (179), (180), (181), (182), (183), (184), (185), (186), (187),
        (188), (189), (190), (309), (310), (311), (330), (339), (341), (342),
        (343), (345), (352), (355), (356), (358), (360), (361), (362), (363),
        (364), (365), (366), (367), (368), (369), (370), (371), (393), (397),
        (400), (402), (404), (405), (406), (407), (408), (409), (410), (472),
        (473), (474), (475), (476), (477), (478), (479), (481), (512), (562),
        (563), (564), (565), (566), (567), (568), (569), (612), (613), (614),
        (615), (616)
)
DELETE FROM roll_calls rc
USING target_rolls tr
WHERE rc.chamber = 'senate'
  AND rc.congress = 119
  AND rc.rollcall_number = tr.rollcall_number;

DELETE FROM bills b
USING phase18_target_bill_ids target
WHERE b.id = target.bill_id
  AND NOT EXISTS (
      SELECT 1
      FROM roll_calls rc
      WHERE rc.bill_id = b.id
  );

COMMIT;
