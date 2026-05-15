# Product v2 Autonomous Tasklist

This tasklist moves Political Fingerprint from an MVP dashboard into a quick voter-facing product for checking whether current officials' recorded votes align with issues the user cares about.

Core rule: inform the user, do not persuade the user. The product may show evidence-based alignment relative to user-selected preferences. It must not tell the user how to vote.

## Phase 1 - Trust Rules and Local Stability

- [x] Update `AGENTS.md` to allow Product v2 alignment, vote interpretation, and evidence drilldown.
- [x] Update `CONSTRAINTS.md` with vote-interpretation and user-alignment constraints.
- [x] Update `docs/methodology.md` to document Product v2 methodology.
- [x] Split local verification into fixture-mode and Supabase-mode test commands.
- [x] Document the Windows Next.js cache reset workflow.
- [x] Fix or quarantine the locked `backend/.pytest_tmp` local permission issue.

## Phase 2 - Evidence Drilldown

- [x] Add backend read support for the votes behind a legislator/domain pair.
- [x] Return roll call date, bill title, question, description, vote position, classification reason, score breakdown, and source URL.
- [x] Add tests for the evidence endpoint response shape.
- [x] Add a frontend domain drilldown panel from `Position by Issue`.
- [x] Make each quick-read claim traceable to the relevant evidence rows.

## Phase 3 - Vote Interpretation Foundation

- [x] Add `vote_interpretations` migration.
- [x] Add deterministic interpretation types and statuses.
- [x] Build an initial deterministic interpreter for obvious bill-passage and amendment cases.
- [x] Mark ambiguous roll calls as `ambiguous` or `insufficient_evidence`.
- [x] Persist interpretation records during ETL.
- [x] Add tests for unambiguous and ambiguous interpretation cases.
- [x] Update methodology with exact interpretation rules.

## Phase 4 - Issue Preference Onboarding

- [x] Add a short preference picker using the 8 issue domains.
- [x] Let users mark each selected issue as "support more action", "oppose more action", or "just show me the record" where interpretation supports it.
- [x] Keep language plain and nonpartisan.
- [x] Store preferences client-side for the current session.
- [x] Add empty, mixed, and insufficient-evidence states.

## Phase 5 - User Alignment API

- [x] Add an alignment endpoint that accepts explicit preference inputs.
- [x] Compute lightweight alignment from stored vote interpretations and votes.
- [x] Return aligned, not aligned, mixed, or insufficient_evidence per issue.
- [x] Include evidence counts and underlying vote ids.
- [x] Add tests proving ambiguous votes do not count toward alignment.

## Phase 6 - Alignment UI

- [x] Add a "Your Issues" read after ZIP lookup.
- [x] Show each official against the same selected preferences.
- [x] Use counts and labels instead of scores or rankings.
- [x] Make evidence drilldown one click away from every alignment label.
- [x] Preserve neutral copy: no "vote for", "vote against", or candidate recommendation language.

## Phase 7 - Comparison Reframe

- [x] Reframe comparison around user-selected issues, not generic politician-vs-politician contrast.
- [x] Compare House rep and senators against the same preference set.
- [x] Show where records are aligned, not aligned, mixed, or insufficiently evidenced.
- [x] Keep the current generic comparison as a secondary exploration tool only if it remains useful.

## Phase 8 - Launch Usefulness

- [x] Improve ZIP coverage beyond fixture/demo mappings.
- [x] Surface data freshness and source coverage in the first viewport.
- [x] Add production deployment docs for Render and Vercel.
- [x] Add lightweight error monitoring guidance.
- [x] Add accessibility and mobile layout checks for the full voter journey.
- [x] Add neutral starter issue checks to reduce first-use friction.
- [x] Auto-open the ZIP-mapped House profile after lookup.
- [x] Make evidence source URLs clickable in vote drilldowns.
- [x] Replace compressed comparison counts with per-issue comparison cards.
- [x] Link comparison issue rows to the same evidence drilldown used by profile reads.
- [x] Remove dashboard-style radar, drift, summary, and API health sections from the main voter path.
- [x] Reorder the page around quick read, issue selection, alignment, evidence, and comparison.
- [x] Convert the old active-legislator/search block into a compact switch-official utility.
- [x] Polish mobile headings, first-viewport height, issue selection, and comparison supporting context.
- [x] Polish insufficient-evidence copy so missing vote-meaning data reads as an honest evidence status.

## Working Priority

Current next build target:

1. Continue with comparison search/selector UX tightening now that browser QA is restored.
2. Use `pytest --basetemp=..\.local\pytest_basetemp` for full Windows fixture-mode test runs.
