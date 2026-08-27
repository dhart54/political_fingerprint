# M14D — approved shared actions and detached Education re-analysis

## Intent and outcome

Promote exactly 17 human-approved Action Interpretability records into the
issue-neutral House 119 V2 corpus, then prepare explicit behavioral candidates
for independent ChatGPT ACCEPT / REVISE / OMIT review. This advances reusable,
source-grounded explanations without treating every understood vote as a finding.

## Baseline and envelope

- Baseline main: `582f785074d9380f2949571627f1afdc72466b44`.
- Isolated branch/worktree; unrelated original-worktree changes remain untouched.
- Existing Shared Legislative Corpus V1 contract and candidate compiler only.
- 53 core actions: 36 unchanged inherited, one approved overlap revision, 16 new.
- Foushee only; no Education mapping acceptance, synthesis, wording, frontend,
  publication, production, database, merge, or manual deployment authority.
- M13 and House V1 artifacts, M14A builder/tests and all other domains are frozen.

## Sequence and definition of done

1. Inspect accepted records, additive authorities, source roles, and M13F structure.
2. Implement deterministic V2 projection and content-bound promotion manifest.
3. Author explicit relationships from approved meanings, reconstruct only episode
   structure, and compile detached candidates with complete episode accounting.
4. Add focused positive/mutation tests, no-write reproduction, scope guard and
   exact-head CI; compare generated candidates to M13H only afterward.
5. Inspect diff and behavior, commit, open draft PR, report exact head/checks, stop.

Expected change size: about 10 files, with 5–6 bounded generated artifacts.
Validation: semantic/domain-focused offline checks (minutes); hosted existing
CI may take longer. No release, browser, or production validation is needed.

## Progress

- [x] Baseline isolated; interpretation principles and governing contracts read.
- [x] V2 promotion and member projection.
- [x] Detached analytical candidates and full accounting.
- [x] Focused checks, mutation tests, diff and behavior inspection.
- [x] Draft PR packaging and exact-head CI configuration.
- [x] Hosted draft PR [#178](https://github.com/dhart54/political_fingerprint/pull/178)
  opened; exact-head CI is pending at this documentation commit and its final
  result is reported in the task/PR.

## Decisions and discoveries

- V2 is a corpus version, not a new schema. Rich accepted candidates stay immutable.
- Clerk identifiers require explicit alias binding from `clerk:house:...` to the
  existing core contract's `clerk:...`; raw source identity is preserved.
- M13F contributes memberships, action lineage, dates and directions only. Its
  old action/episode prose does not enter candidate generation.
- The milestone's cross-episode trajectory rule controls; same-day H.R.1048
  amendment and passage stay one episode and cannot form a trajectory.
- Acceptance is external and additive; candidate flags are not rewritten.

## Validation, corrections and final reconciliation

- 11 files, including six bounded generated JSON artifacts; no new schema or
  runtime/compiler change. Review uses source locators rather than duplicating
  all claim text; the immutable full records remain the rich semantic authority.
- V2: 53 identities, 36 record-identical inherited records, one H.R.1156 overlap
  revision, 16 new identities; Foushee has all 53 official states.
- Core digest: `fc7b376cd3e0b485e0ac28c15ba7a5111a1e41c4855a3cbb99354b4ac04d0aa2`.
- Member digest: `d1ad8f68ca8a419427ce23e6b0c870c02a450de0ae3309df33db691c78e46892`.
- Three detached proposals: funding exclusions (two episodes), bargaining
  continuity (two episodes), and one H.R.1048 within-episode contrast. Zero
  trajectories, synthesis, issue-mapping acceptance or analytical acceptance.
- All 16 episodes accounted: 4 pattern support, 1 notable support, 2 useful
  contrasts, 1 non-directional receipt, 8 understood receipts without elevation.
- Post-generation M13H comparison: bargaining continuity is new; the other two
  findings have materially more specific semantic bases; none is inherited as
  accepted. Eight receipt dispositions distinguish non-elevation from evidence
  failure. Historical artifacts are unchanged.
- M14A/M14B/M14C/M14D no-write builders pass. Focused suites: **89 passed**,
  including 13 M14D tests. Core Semantic IR validator passed all reference groups;
  `unittest backend.tests.test_editorial_semantic_ir`: **26 passed**.
- Local AJV lookup initially failed in the new worktree; rerun used the existing
  original-worktree frontend dependencies through `NODE_PATH`. No files changed.
- Initial pytest cache creation hit a Windows permission warning; subsequent
  local runs disabled the optional cache provider and passed. No product failure.
- Corrected the M13F `non_directional_not_voting` to core
  `resolved_non_directional` representation with an exact Not Voting check.
- CI has a dedicated PR-head checkout and durable reproduction tests. The
  milestone-wide diff allowlist runs only for this M14D branch, so it cannot
  accidentally ban unrelated future work. V1 frozen-input tests remain durable.
- Inspected exact action/source boundaries for H.R.1156, the substitute,
  EO14251 and EO14168; each operative/incorporated source remains bound.

No production writes. Rollback is reversion of this isolated branch's artifacts;
no historical or production rollback needed. No implementation blocker remains.
Stop after draft PR and hosted check reporting for independent ChatGPT
ACCEPT / REVISE / OMIT review; do not begin M14E.
