# Current state

> **THIS FILE IS A CONVENIENCE SNAPSHOT. GitHub, active PRs, exact branch heads,
> CI, Supabase, Render and live behavior override it when newer.** Reconcile the
> [operating brief](DOT_OPERATING_BRIEF.md) with those authorities before acting.

## Repository

- Repository: `dhart54/political_fingerprint`.
- Snapshot: **2026-10-06, 10:52 EDT (14:52 UTC)**.
- GitHub `main`: `862b290cceea8af7d6c1c800d1ecdfa52386a490`, verified through
  GitHub and fetched locally. This documentation branch starts from that SHA.
- Scope of this update: operating documentation only; Immigration work was read,
  not resumed. No candidate, registry, production, configuration or runtime changes.

## Active objective

The active substantive workstream is the candidate-only **Immigration & Border
shared corpus**, House 119 sessions 1–2 through September 16, 2026, with mechanical
Foushee (`F000477`) / Massie (`M001184`) projection. The objective is **incomplete,
checkpointed at the overnight time limit**. No universe closure, final audit PASS,
independent-review readiness, acceptance or publication is claimed. This is the
committed/PR checkpoint status, not a claim that a local task is currently running.

## Active development

- [Draft PR #198: Immigration & Border shared candidate](https://github.com/dhart54/political_fingerprint/pull/198)
  is OPEN, based on `main`.
- Branch: `codex/foushee-immigration-border-shared`.
- Exact remote/local checkpoint head: `bac767abf68781ff4bbcda4774e2893d42e2cd33`.
- Existing local worktree: `.w/ib`; tracked files were clean when inspected.
  The local deadline file records the expired eight-hour boundary; terminal-marker
  creation was described in the PR, but a terminal marker was not found at the
  worktree root. Do not infer goal completion or running status from that file.
- [Committed plan and latest checkpoint](https://github.com/dhart54/political_fingerprint/blob/bac767abf68781ff4bbcda4774e2893d42e2cd33/docs/plans/foushee_immigration_border_shared_interpretation.md)
  owns continuation. Other open draft PRs include #193 (record-card reproducibility),
  #187 (M15B preparation) and #100 (older generality work); their open state does
  not authorize resuming them or establish a new priority.

## Current progress

Read directly from the [exact checkpoint corpus](https://github.com/dhart54/political_fingerprint/tree/bac767abf68781ff4bbcda4774e2893d42e2cd33/docs/editorial/shared_candidates/house_119_immigration_20260916)
and [audit JSON](https://github.com/dhart54/political_fingerprint/blob/bac767abf68781ff4bbcda4774e2893d42e2cd33/docs/review_packets/immigration_semantic_audit_in_progress.json): `authoring.json`, `membership_review.json`,
`universe_proposal.json`, generated mapping/projections/readable outputs and audit
receipts establish the following:

| Receipt | Current result |
|---|---|
| Fixed discovery inventory | 676 exact actions |
| Shared meanings | 37 |
| Governed reviews | 453: 37 interpreted, 211 procedural, 203 excluded, 2 expressive |
| Ordinary screenings unfinished | 223 |
| Episodes | 35; H.R. 4 and H.R. 7147 each retain two stages |
| Member observations | 74: 72 directional, 1 Present, 1 Not Voting |
| Readable/IR findings | 68: Foushee 35, Massie 33 |
| Separate review questions | 21 legal/cross-domain/application interactions |
| Governed sources | 1,189; latest checkpoint records 988 unchanged Health reuses and 201 new |

All 37 meanings have a separate same-owner primary reconstruction/comparison.
Audit JSON records 94 distinct action assessments: 1 Critical, 7 Major, 3 Minor,
83 No Defect. Historical corrected findings remain visible; distinct issues are
1 Critical, 3 Major, 2 Minor. Controls cover 40 retained exclusions, 15 procedures
and both expressive actions. This is not a second independent reviewer or final
full-corpus verdict. Ordinary unfinished work and the 21 review questions are
separate units, not additive missing-source counts.

## Validation

- Latest committed audit/checkpoint receipt: **217 focused tests**, 38.695 seconds;
  **seven canonical semantic checks** and **seven byte-identical generated outputs**.
- Source/hash/Clerk/accounting/audit integrity, public/persistence rejection,
  protected-baseline preservation and actual readable/status/mixed-episode
  inspection are recorded. These receipts were inspected, not rerun for this
  documentation-only change.
- GitHub confirms all **nine backend jobs SUCCESS at `bac767ab…`** in
  [run 37448394605](https://github.com/dhart54/political_fingerprint/actions/runs/37448394605),
  completed October 6, 2026. Vercel checks also succeeded.
- The committed audit JSON still says current-head CI is pending push and points
  to the prior head. The newer hosted run and PR receipt supersede that field.
  Older narrative prefaces also retain earlier counts; structured artifacts and
  the latest checkpoint control this snapshot.

## Exact resume point

Continue in the existing branch/worktree after reconciling newer state. The latest
committed checkpoint prioritizes **H.R. 1 House passage `house:119:1:145` versus
Senate-amendment concurrence `house:119:1:190`**: exact EH and adopted H.Res. 492/499
corrections versus EAS. Then address remaining continuing/omnibus and NDAA packages
with material immigration clauses, followed by the remaining narrow screenings.

Additional ordinary research leads recorded at the checkpoint: S. 3971's material
security/eligibility baselines (`638g/o/vv`); S. 2403's material Revenue Ruling 59-60
valuation authority; failed 84/108 exact floor-body bindings, for which outcome-only
Record pages are insufficient. These are preserved leads, not newly researched
or adjudicated by this documentation task. Keep the 21 legal questions separate.

## Known blockers/dependencies

- Full candidate completion requires the 223 remaining ordinary screenings and
  appropriate audit/coverage closure. They are work remaining, not blanket
  unavailable-evidence blockers.
- The 21 source-supported review questions remain routed for independent candidate
  review; material legal/cross-domain choices must not be silently resolved.
- No final independent/full-corpus audit verdict or acceptance authority exists
  for this checkpoint. Safe bounded research can continue under the authorized
  workstream without treating later review as a universal stop condition.

## Current product/runtime notes

- Public `GET /health` reported `status=ok` and main SHA `862b290c…` at inspection.
  An initial 30-second timeout was followed by a successful bounded retry; this
  alone does not establish a reliability defect.
- Foushee editorial API `scope=119` returned `reviewed_conclusion` for Justice,
  National Security, Environment and Education, and `receipts_only` for Economy,
  Health, Immigration and Infrastructure. This verifies API selection, not a
  full rendered frontend review or current database-target identity.
- **Maintenance debt:** current smoke YAML requests nonexistent `leg_alex_morgan`
  (live 404) and expects older Justice identity/wording/receipt constants that
  differ from the current API. The latest listed main smoke run
  [34975635674](https://github.com/dhart54/political_fingerprint/actions/runs/34975635674)
  failed at older head `f790163f…`; it is not current-head main CI. These are not
  domain-research blockers and were not repaired here.
- The Health audit is committed on main with **PASS WITH CORRECTIONS**, candidate-only.
  [PR #197](https://github.com/dhart54/political_fingerprint/pull/197) merged into
  its Health continuation base, and [PR #196](https://github.com/dhart54/political_fingerprint/pull/196)
  subsequently merged. The candidate remains receipts-only publicly.
- Earlier green-migration/preparation notes are historical; later authorized
  [activation execution receipts](editorial/publication_replacements/m15b_green_activation_execution/README.md)
  document National Security/Justice activation. Supabase target, service settings,
  current registry rows and frontend deployment SHA were **not inspected live**
  in this task. Recover them read-only when relevant; do not infer them from an
  earlier plan's paused status or from this snapshot.

## Next expected milestone

A source-bound Immigration candidate increment covering the exact H.R. 1 version
choices, with updated screening/audit receipts and preserved candidate/publication
isolation. This snapshot records the next research milestone; it does not launch it.
