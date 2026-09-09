# M15B independent review

All remediation and treatment decisions remain pending independent review. No
publication, semantic acceptance, production write, merge or deployment is
authorized by these artifacts.

- `trajectory_review.json`: forward rule, exact accepted source bindings and the
  two active trajectory items. National Security fails substantive comparability;
  Justice's mixed HALT episode needs human semantic review. Environment and M14
  Education have no active trajectories. Only National Security has a remediation
  candidate in this milestone.
- `before_after_public_review.json`: exact selected National Security before and
  simulated after, plus old/new limitation output for all active governed receipts
  and the National Security control caveat. The after view is a review simulation,
  not a newly accepted publication artifact. Historical mapping hashes are source
  references, not valid approvals of its edited overview. Later accepted replacement
  must create new governed bindings.
- `active_limitation_treatment_review.json`: all 35 suppressed occurrences, one
  distinct Justice caveat, proposed PUBLIC with unchanged wording. No rewritten
  public copy is proposed. “Candidate” is a noun in a substantive limitation here,
  not an assertion of process state. The entire affected set remains visible for
  review; the frontend no longer deletes it by prefix.

National Security candidate delta: trajectories 1 → 0; ordinary findings 15 → 14;
finding-supporting actions 32 → 30. Remove the overview's annual-appropriations
reference and its linkage to that finding. Preserve both underlying receipts,
exact accepted meanings, all independent findings and all unrelated limitations.
No replacement pattern, notable choice or synthesis is invented. Active runtime
trajectory selection remains unchanged.

Reproduce with `python scripts/build_m15b_review.py --check`. Generation reads
only the pinned accepted repository artifacts and the baseline frontend filter.
The initial read-only public snapshot matched all four active caveat sets, the
complete selected National Security presentation and both trajectory wordings.
The snapshot is not a database-repair verification or production operation.

The real React analysis component is rendered in `frontend/lib/m15bTrust.test.mjs`.
An existing Playwright receipt test now protects the substantive limit while
retaining its structural metadata assertions. Synthetic mixed-copy tests exercise
authored “Official amendment text is incomplete” without asserting that new copy
for Foushee. No semantic sentence extraction runs in JavaScript.
