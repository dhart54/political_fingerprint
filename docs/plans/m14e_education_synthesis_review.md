# M14E: Education synthesis candidate review

## Intent and outcome

Test one bounded mechanism-divide hypothesis over accepted M14D findings. Produce
two detached review artifacts and a draft PR; zero accepted synthesis remains the
outcome. This advances source-grounded interpretation without public conclusions.

## Baseline and scope

- Exact main: `79995a5a4d8840e2e3783905327ba02c6d40cffa`.
- Isolated branch: `codex/m14e-education-synthesis-review`, initially clean.
- Seven files expected: current-path module, builder, tests, this plan, CI, two
  JSON outputs. Semantic validation should take seconds locally, minutes in CI.
- Preserve M14D records/authority, all 16 episodes, V2, M14B/C, historical M13,
  other domains, and unrelated work in the original checkout.
- No acceptance authority, Main Takeaway, public wording, frontend, publication,
  persistence, database writes, deployment, or merge.

## Decision envelope and implementation sequence

1. Verify the exact accepted findings/authority; do not fabricate legacy inputs.
2. Add a narrow current-path compiler for zero or one `mechanism_divide` candidate.
3. Derive lineage and limitations; account for all three accepted findings.
4. Build two review artifacts; test invariants and mutations; add exact-head CI.
5. Inspect the candidate and final diff, open a draft PR, and verify CI.

## Decisions and discoveries

- Read interpretation principles and editorial workflow. Only the supplied
  observed mechanism contrast is proposed, not a durable regulatory preference.
- Source findings retain non-authorizing candidate provenance. Their separate,
  pinned human authority establishes accepted input status, not synthesis status.
- Two primary inputs imply three episodes/four actions, not four independent
  propositions. H.R.1048 remains one mixed episode and a material limiter.
- All three accepted findings span five episodes/six actions; the complete
  M14D ledger still contains 16 episodes/17 actions, including Not Voting.
- The old ETL synthesis compiler is historical for this task and is not adapted.
- Structural source binding and explicit mechanism evidence are mechanical
  gates; the usefulness of the relationship remains an independent review judgment.

## Definition of done and progress

- [x] Baseline, boundaries, and existing contracts inspected.
- [x] Narrow module, two review artifacts, and focused regression tests complete.
- [x] Exact input bindings, full accounting, zero-candidate behavior, inherited
  limits, mixed-episode ambiguity, and downstream denials validated.
- [x] M14A/B/C/D unchanged and passing; final diff reviewed.
- [ ] Draft PR opened and exact-head CI verified.

## Validation results

- 109 focused tests passed, including 15 new M14E tests and the unchanged
  shared-corpus, interpretability, M14C, M14D, and behavioral-candidate suites.
- 26 core Semantic IR tests and the semantic-reference validator passed.
- M14A/B/C/D no-write builders passed; M14E reproduction and scope checks passed.
- Exact accepted source records, 16-episode ledger, and prior CI jobs are
  unchanged. Review inspection confirms two findings / three episodes / four
  actions in the candidate, seven inherited input limitations, and the mixed
  H.R.1048 episode as a material limiter. Bargaining remains standalone.
- M14E candidate digest:
  `e1f897237de6934c96f034205b4e2fdf6b73afafbe6081507c5d3861180bdc4d`.
- Hosted exact-head CI is the remaining external validation; its result and the
  final commit are recorded in the draft PR and task report.

## Deviations, blockers, and rollback

Initial document-pin inspection used Windows default decoding; corrected it to
explicit UTF-8 before successful generation. No source document changed. No
scope deviation or blocker. No production writes or production rollback required. The isolated branch
can be left unmerged; reverting its scoped additions removes this candidate path.

## Final reconciliation

Local implementation and review are complete; draft PR/hosted CI remain pending.
Independent review may accept, revise, or omit
the candidate in a separately authorized milestone; this milestone accepts none.
