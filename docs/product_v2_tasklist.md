# Product Roadmap

This roadmap moves Political Fingerprint from an MVP dashboard into an accountability-first civic product.

North star:

**Who represents me, how are they acting on the issues I care about, and what can I do next?**

The current v2 product focuses on current federal officials, interpreted voting records, issue evidence, and user-selected issue alignment. The next expansion should add a neutral civic action/contact layer before continuing broad election or challenger work.

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
- [x] Label neutral starter issue rows as record views instead of alignment conclusions.
- [x] Auto-open the ZIP-mapped House profile after lookup.
- [x] Make evidence source URLs clickable in vote drilldowns.
- [x] Replace compressed comparison counts with per-issue comparison cards.
- [x] Link comparison issue rows to the same evidence drilldown used by profile reads.
- [x] Remove dashboard-style radar, drift, summary, and API health sections from the main voter path.
- [x] Reorder the page around quick read, issue selection, alignment, evidence, and comparison.
- [x] Convert the old active-legislator/search block into a compact switch-official utility.
- [x] Keep switch-official and comparison-pair searches idle until the user types a real query.
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
- [x] Share human-readable issue-domain labels across accountability, comparison, and race evidence surfaces.

## Working Priority

Current next build target:

1. Visually review the improved Valerie Foushee / `ECONOMY_TAXES` gold slice.
2. Make the current-representative accountability dashboard the clear primary journey.
3. Keep the neutral contact layer focused on official contact metadata and evidence context.
4. Expand source-grounded manual interpretations for high-visibility current-official issue records.
5. Keep upcoming election and challenger context secondary, evidence-tiered, and non-prescriptive.

Priority hierarchy for new work:

1. Representative Accountability Dashboard
2. Civic Action / Contact Layer
3. Election / Challenger Layer

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
- [x] Show interpreted-vote coverage on issue tiles before users open evidence.
- [x] Add second reviewed interpretation batch for Valerie Foushee national-security/defense votes.
- [x] Complete remaining Valerie Foushee national-security/defense review pass with explicit ambiguity and insufficient-evidence records.
- [x] Punch up budget-resolution interpretations so evidence rows explain practical process effects, not just formal vote labels.
- [x] Add shared NC Senate national-security interpretations for foreign-military-sale disapproval motions.
- [x] Create Valerie Foushee / Economy-Taxes gold slice for replicable high-quality vote interpretation.
- [x] Tighten the Valerie Economy-Taxes gold slice with higher-specificity stakes from existing official summaries.
- [x] Make opened issue evidence reads draw a bounded, repeatable plain-language conclusion from interpreted votes.
- [x] Document the repeatable issue-read workflow from enriched packet export through browser QA.
- [x] Add Valerie Foushee visible-domain interpretation batch for Health/Social, Education/Workforce, Environment/Energy, and Immigration/Border rows.
- [x] Mark one-vote issue reads as limited signals instead of broad all-for/all-against patterns.

## Next Lens - Ballot-Aware Candidate Comparison

Goal: keep election context available after the current-representative accountability flow, using the strongest available evidence for each candidate.

This lens is now secondary to the Representative Accountability Dashboard and Civic Action / Contact Layer.

Evidence ladder:

1. Recorded governing behavior
2. Institutional record
3. Sourced stated positions
4. Insufficient evidence

### Phase 9 - Federal Ballot Proof

- [x] Identify reliable federal election/race data source options.
- [x] Document cost, license, freshness, and coverage tradeoffs for each source.
- [x] Add `upcoming_races` and `race_candidates` schema draft.
- [x] Add ZIP/state/district mapping from a user ZIP to upcoming federal House and Senate races.
- [x] Add backend endpoint for upcoming federal races by ZIP.
- [x] Move frontend upcoming-race context below the representative accountability flow.
- [x] Add initial FEC candidate-summary importer for federal House/Senate race context.
- [x] Add high-confidence incumbent candidate linkage to existing legislator voting records.
- [x] Let linked incumbent race cards open the existing voting-record profile.
- [x] Add compact linked-incumbent voting summaries to race cards.
- [x] Add candidate evidence schema and endpoint foundation for non-incumbents.
- [x] Add first reviewed candidate evidence seed for one NC-04 challenger.
- [x] Make seeded candidate evidence expandable with source links in race cards.
- [x] Label races as upcoming or past based on election dates.
- [x] Keep race display neutral and non-ranked.

### Phase 10 - Candidate Evidence Tiers

- [x] Add candidate profile schema with evidence tier fields.
- [x] Support incumbent candidate linkage to existing legislator voting records.
- [x] Support prior-officeholder linkage when candidate has a past voting record.
- [x] Add sourced stated-position records for candidates without voting history.
- [x] Add reviewed institutional-record seed for one candidate without a federal voting history.
- [x] Store source URL, source type, retrieved date, issue domain, statement text, and confidence label.
- [x] Add candidate evidence endpoint.
- [x] Add tests that stated positions are marked lower confidence than recorded votes.
- [x] Document stated-position methodology and forbidden persuasion language.

### Phase 11 - Race Comparison UI

- [x] Add race page or race panel for ZIP-selected upcoming races.
- [x] Compare candidates by selected user issues.
- [x] Show "recorded votes," "stated positions," and "insufficient evidence" as separate evidence types.
- [x] Make every candidate claim expandable to source details.
- [x] Avoid aggregate candidate scores or ranking language.
- [x] Add empty states for uncontested races and missing candidate data.
- [x] Cap noisy low-signal race candidate lists while disclosing hidden rows.

### Phase 12 - North Carolina State Pilot

- [x] Research NC state legislative voting and election data availability.
- [x] Document NC source reliability, access method, and update cadence.
- [x] Add NC state district mapping plan.
- [ ] Add one NC state office/race pilot before broad state expansion.
- [x] Keep state-level methodology separate from federal methodology where source formats differ.

### Phase 13 - Broader State and Local Expansion

- [x] Create a state adapter checklist.
- [ ] Add states only when source quality and maintenance burden are understood.
- [ ] Evaluate local election data vendors or civic data partnerships.
- [ ] Treat local coverage as lower priority until federal and NC pilot flows are useful.

## Next Lens - Civic Action / Contact Layer

Goal: let users move from source-grounded evidence to a neutral next step with their current representatives.

Current action surface:

1. Show official contact paths for the current representative.
2. Preserve the issue and optional roll-call context the user is looking at.
3. Do not create ask, thank, or track modes until there is a validated need for them.

Rules:

- Actions must be user-directed and optional.
- Current action UI should show official contact information and evidence context without generating a message body.
- Actions must not imply a voting recommendation or electoral persuasion.
- Action history must not affect vote classification, vote interpretation, alignment, or candidate evidence tiers.

### Phase 14 - Contact Metadata Foundation

- [x] Identify a low-cost, reliable source for current federal official contact metadata.
- [x] Document source fields, update cadence, review workflow, and failure modes.
- [x] Confirm legal/source-access caveats before broad automated contact expansion.
- [x] Add minimal backend model or read adapter for contact links.
- [x] Add reviewed NC federal contact seed and importer keyed by Bioguide ID.
- [x] Add reviewed official contact seed for the other loaded federal demo ZIP officials.
- [x] Apply the contact metadata migration and NC pilot seed to Supabase.
- [x] Add tests for loaded and missing contact metadata.
- [x] Update `docs/methodology.md` with contact/action boundaries.

### Phase 15 - Evidence-Linked Actions

- [x] Add action entry points from representative profile, issue cards, and interpreted vote evidence rows.
- [x] Collapse contact/action UI to official contact information plus evidence context.
- [x] Clarify that evidence-linked contact UI has not sent, saved, or tracked anything.
- [x] Keep cited vote/source context visible when an action starts from evidence.
- [x] Keep ask, thank, track, newsletters, and persistent reminders out of scope until users validate a need.
- [x] Add tests proving contact/reference state does not change alignment labels or evidence tiers.
