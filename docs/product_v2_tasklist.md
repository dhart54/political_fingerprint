# Product Roadmap

This roadmap moves Political Fingerprint from an MVP dashboard into a ballot-aware civic product.

North star:

**Who is on my ballot, and what does the evidence show about how they act on the issues I care about?**

The current v2 product focuses on current federal officials and interpreted voting records. The next expansion should add upcoming races and candidate evidence tiers while preserving the original trust rules.

Core rule: inform the user, do not persuade the user. The product may show evidence-based alignment relative to user-selected preferences. It must not tell the user how to vote.

Execution detail lives in `docs/north_star_action_plan.md`.

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
- [x] Collapse comparison legislator search into a secondary pair-edit drawer.
- [x] Add compact method, evidence, and limits notes to the footer.
- [x] Tighten first-screen copy around ZIP lookup, auto-open behavior, and issue selection.
- [x] Add final staging-readiness accessibility and CORS configuration polish.
- [x] Document staging readiness, deployment checks, and review focus.
- [x] Remove confusing comparison overlay toggle from the selected-issues comparison view.
- [x] Group evidence roll calls by bill or measure and show roll-call count versus bill count.
- [x] Make ZIP lookup comparison preset buttons show hover, focus, and selected states.
- [x] Compact evidence row metadata so source access remains available without giving internal classification labels primary space.
- [x] Run final frontend pass and polish starter-check selected states plus narrow evidence-card spacing.

## Working Priority

Current next build target:

1. Confirm deployment through the latest main commit and smoke-test interpreted issue patterns.
2. Expand source-grounded manual interpretations for high-visibility federal/starter issue records.
3. Begin federal ballot proof: ZIP to upcoming federal races and candidate records.
4. Add candidate evidence tiers before expanding beyond current officials.

## Shelved Product Ideas

- Voting neighbors: a future deterministic "who votes similarly?" module showing a small set of officials with similar yea/nay patterns across shared categorized roll calls. It should avoid leaderboard language, separate low-overlap cases, and explain overlap/evidence before launch consideration.

## Next Lens - DC-Speak Breakdown

- [x] Add database fields for cached plain-English vote interpretation details.
- [x] Add offline packet export and reviewed JSON import workflow for manual interpretation batches.
- [x] Document the no-API-key manual interpretation workflow.
- [x] Export the first high-impact batch for ZIP demo officials and starter issue bundles.
- [x] Draft reviewed interpretations for that batch.
- [x] Import reviewed interpretations into Supabase.
- [x] Surface plain-English vote meaning in evidence rows.
- [x] Aggregate interpreted vote meanings into neutral issue pattern cards.

## Next Lens - Ballot-Aware Candidate Comparison

Goal: move from "current officials by ZIP" to "current officials plus upcoming races by ZIP," using the strongest available evidence for each candidate.

Evidence ladder:

1. Recorded governing behavior
2. Institutional record
3. Sourced stated positions
4. Insufficient evidence

### Phase 9 - Federal Ballot Proof

- [x] Identify reliable federal election/race data source options.
- [ ] Document cost, license, freshness, and coverage tradeoffs for each source.
- [x] Add `upcoming_races` and `race_candidates` schema draft.
- [x] Add ZIP/state/district mapping from a user ZIP to upcoming federal House and Senate races.
- [x] Add backend endpoint for upcoming federal races by ZIP.
- [x] Add frontend "Your Upcoming Federal Races" section after ZIP lookup.
- [x] Add initial FEC candidate-summary importer for federal House/Senate race context.
- [ ] Label races as upcoming, active, or past based on election dates.
- [ ] Keep race display neutral and non-ranked.

### Phase 10 - Candidate Evidence Tiers

- [ ] Add candidate profile schema with evidence tier fields.
- [ ] Support incumbent candidate linkage to existing legislator voting records.
- [ ] Support prior-officeholder linkage when candidate has a past voting record.
- [ ] Add sourced stated-position records for candidates without voting history.
- [ ] Store source URL, source type, retrieved date, issue domain, statement text, and confidence label.
- [ ] Add candidate evidence endpoint.
- [ ] Add tests that stated positions are marked lower confidence than recorded votes.
- [ ] Document stated-position methodology and forbidden persuasion language.

### Phase 11 - Race Comparison UI

- [ ] Add race page or race panel for ZIP-selected upcoming races.
- [ ] Compare candidates by selected user issues.
- [ ] Show "recorded votes," "stated positions," and "insufficient evidence" as separate evidence types.
- [ ] Make every candidate claim expandable to source details.
- [ ] Avoid aggregate candidate scores or ranking language.
- [ ] Add empty states for uncontested races and missing candidate data.

### Phase 12 - North Carolina State Pilot

- [ ] Research NC state legislative voting and election data availability.
- [ ] Document NC source reliability, access method, and update cadence.
- [ ] Add NC state district mapping plan.
- [ ] Add one NC state office/race pilot before broad state expansion.
- [ ] Keep state-level methodology separate from federal methodology where source formats differ.

### Phase 13 - Broader State and Local Expansion

- [ ] Create a state adapter checklist.
- [ ] Add states only when source quality and maintenance burden are understood.
- [ ] Evaluate local election data vendors or civic data partnerships.
- [ ] Treat local coverage as lower priority until federal and NC pilot flows are useful.
