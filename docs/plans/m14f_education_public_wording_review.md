# M14F: Education public wording and prominence review

## Intent and stopping point

Express the exact human-accepted M14D findings and M14E internal synthesis as a
detached four-item public-wording candidate package. Compare a proposed Main
Takeaway with a valid no-Main-Takeaway presentation, open a draft PR, and stop
for independent product review. No wording or prominence decision is made here.

## Baseline, scope, and non-scope

- Exact main: `ad469a0f76fb43c16204ec23d68cca73a0cc70c8`.
- Isolated branch: `codex/m14f-education-public-wording`, initially clean.
- Seven files expected: one current-path compiler, builder, focused tests, this
  plan, exact-head CI, and two JSON review outputs.
- Preserve the accepted M14D and M14E artifacts, Shared Action Core V2, Member
  Projection V2, M14B/C, historical M13 wording/site integration, other
  domains, frontend, publication, persistence, and production state.
- No human wording acceptance, Main Takeaway acceptance, canonical public copy,
  site integration, database write, deployment, or merge.

## Implementation sequence and definition of done

1. Pin and validate the four exact M14D/M14E accepted artifacts.
2. Compile four exact wording candidates only from accepted semantic sources,
   deriving all episode/action lineage and accounting every source limitation.
3. Preserve all three behavioral items in both prominence variants; prove the
   zero-overview variant compiles without reopening M14E semantics.
4. Generate only the two requested review artifacts and keep every downstream
   authorization false.
5. Run focused and inherited semantic validation, inspect the final diff, open
   a draft PR, and verify exact-head CI.

## Decisions and review boundary

- Option A proposes the accepted foreign-influence synthesis as the issue
  overview because it is the only accepted cross-finding relationship. Its
  explicit opening scope bounds it to that policy slice.
- Option B omits the overview while retaining all three independent behavioral
  findings. It loses no evidence-layer semantics and avoids overweighting three
  episodes within a sixteen-episode issue record.
- The package records both options and leaves public prominence pending. M14E
  semantic validity is fixed and is not part of this decision.
- Limitation treatment is explicit per item. Seven treatments are retained in
  public copy and eleven are compressed or omitted with concrete reasons.

## Progress and validation

- [x] Exact baseline, accepted inputs, interpretation rules, and historical
  comparison boundary inspected.
- [x] Narrow current-path compiler, builder, and two candidate artifacts added.
- [x] Focused mutation tests and inherited M14A-M14E validation pass.
- [ ] Exact seven-file diff reviewed; draft PR opened and exact-head CI passes.

Local validation: 118 focused tests passed, including 17 new M14F tests and the
unchanged M14A-M14E suites. Twenty-six core Semantic IR tests, the semantic
reference validator, all M14A-M14E no-write builders, exact regeneration, and
the scope guard passed. The core unittest needed the existing root-checkout
`frontend/node_modules` through `NODE_PATH` because isolated worktrees do not
duplicate ignored dependencies; no dependency or frontend file changed.

Review inspection confirms four exact wording items, a valid three-item
zero-overview variant, behavioral lineage of three findings/five episodes/six
actions, overview lineage of two findings/three episodes/four actions, one
mixed H.R.1048 episode/two actions, and H.R.1005 excluded as Not Voting.

No production write or rollback applies. Leaving the draft branch unmerged is
the rollback for this detached candidate milestone.
