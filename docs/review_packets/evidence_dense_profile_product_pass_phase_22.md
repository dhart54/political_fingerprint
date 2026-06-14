# Evidence-Dense Profile Product Pass - Phase 22

## Scope

Phase 22 is a frontend/product hierarchy pass over the current accountability profile. It does not change production data, API shape, support/opposition counting, alignment logic, readiness thresholds, schema, vote classifications, or vote interpretations.

## Original product problems addressed

- Oversized first viewport: the ZIP/start panel rendered full legislator cards, race context, and ZIP coverage before the current profile.
- Weak hierarchy: issue summaries and strongest evidence were below lower-value page setup.
- Vote cards were too tall because source basis, caveats, action controls, and interpretation details were visible by default.
- Repeated pills and caveats made substantive, procedural, limited, and not-voting rows feel too visually similar.
- Drift wording used an abstract score in a primary card.
- Comparison occupied primary page space even when the voter had not asked for it.
- Procedural-context and limited rows were visible but competed too strongly with countable substantive evidence.

## Production-backed profiles reviewed

The review used the existing backend read layer and local rendered frontend against the same loaded profile data exposed by the app. Direct SQL was unavailable in this shell, so profile selection used read-only API helpers and browser rendering rather than direct database writes or imports.

| Profile | Why reviewed | Useful observed coverage |
| --- | --- | --- |
| Valerie P. Foushee | House profile with strong and weak sections | National Security had 22 rows with 19 interpreted; Justice had 13 rows with 6 interpreted and procedural/limited rows; Economy had interpreted, limited, and not-voting rows. |
| Thom Tillis | Senate profile with substantive amendment evidence | Economy had 39 rows with 34 interpreted; Health had 18 rows with 16 interpreted; amendment-heavy evidence was available. |
| Ted Budd | Senate amendment profile with different vote pattern | Economy had 39 rows with 34 interpreted; Health had 18 rows with 16 interpreted. |
| Adam B. Schiff | Mixed readiness Senate profile | Broad Senate coverage with several interpreted domains and remaining weak sections. |
| Rubio (R-FL) | Sparse/limited profile | Loaded official with zero interpreted/recorded rows in the current read layer, useful for empty-state behavior. |

## Hierarchy changes

Previous order:

1. Large marketing-style headline.
2. Full ZIP lookup result cards, race context, and ZIP coverage.
3. Current profile identity.
4. Quick read.
5. Preferences/alignment.
6. Issue evidence.
7. Comparison.

New order:

1. Compact product/ZIP entry with small official chips.
2. Current profile identity.
3. Quick read with best issue read, coverage, and plain-language change context.
4. Issue readiness and strongest evidence.
5. Evidence summary and grouped proof.
6. User preferences/alignment.
7. Comparison in a collapsed secondary section.
8. Election and search utilities.

## Initial viewport changes

- The hero headline and stats were reduced.
- The hero ZIP result no longer renders full legislator cards, upcoming-race detail, or loaded ZIP coverage.
- The hero ZIP result now renders compact House/Senate official chips that can open profiles.
- `Current Profile` and `Quick Read` are visible in the first desktop viewport.
- The first issue section begins with minimal scroll on 1440x900 and is visible on 1920x1080.

Rendered viewport metrics:

| Viewport | Result |
| --- | --- |
| 1920x1080 large desktop | Current profile visible at top 470px; quick read visible at top 607px; issue section visible at top 977px; no horizontal overflow. |
| 1440x900 desktop | Current profile and quick read visible; issue section starts at 977px, requiring a small scroll; no horizontal overflow. |
| 1366x768 laptop | Current profile and part of quick read visible; issue section requires scroll; no horizontal overflow. |
| 768x1024 tablet | Current profile and quick read visible below compact lookup; issue section requires scroll; no horizontal overflow. |
| 390x844 mobile | Header remains single-column and readable with no horizontal overflow; profile content follows the lookup stack. |

## Issue summary changes

- Issue readiness groups are more compact.
- The issue overview now appears before bill/evidence details.
- The issue overview uses three compact summary cells for what the official did, what pattern that creates, and how to read it.
- The repeated "what not to infer" content is consolidated into one expandable issue-level "Evidence limits" block.

## Vote-card compression

Default vote rows now show:

- date/chamber/roll number;
- vote type when available, such as amendment or final passage;
- measure/question;
- concise practical meaning;
- recorded vote position;
- one confidence label.

Expanded detail now contains:

- full interpretation breakdown;
- what happened;
- why it mattered;
- what not to infer;
- source basis;
- official source link;
- civic action record selector.

## Pill and caveat reductions

- Removed the default-visible "Plain-English interpretation available" badge.
- Removed party-majority and winning-side badges from the badge list; that context remains available as plain detail text.
- Replaced repeated per-card caveat visibility with a single issue-level expandable evidence-limits note plus row-specific details on demand.
- Kept only materially useful labels: vote position, confidence, amendment/final-passage/procedural type, and readiness.

## Evidence ordering and default visibility

Evidence groups and rows now sort for voter value:

1. countable interpreted substantive rows;
2. interpreted not-voting rows;
3. procedural-context rows;
4. ambiguous or insufficient rows.

This is display ordering only. It does not change stored rows, counts, alignment, readiness thresholds, or API responses.

## Procedural-context treatment

- Procedural-context rows remain visible.
- They are visually quieter than countable substantive rows.
- They remain labeled as procedural context where applicable.
- They remain non-counting and do not become support/opposition or alignment evidence.

## Drift decision

The primary quick-read card no longer says "drift score" as the main concept. It now uses "Change context" and plain language such as "steady mix", "some shift", or "shifted mix" with the numeric value only as secondary context.

## Comparison decision

Comparison is retained but moved out of the primary flow. It now sits in a collapsed "Compare with another official" section after the evidence and alignment surfaces, because comparison is useful only after the voter understands the selected official's own record.

## Alignment placement

Issue preferences and alignment now appear after the quick read and issue evidence starter. This keeps alignment from replacing the evidence summary. No-preference state remains neutral, and procedural rows remain excluded by existing logic.

## Amendment and final-passage validation

Rendered evidence validation after opening Valerie's best read confirmed:

- issue overview appears;
- grouped evidence preview appears;
- expandable "Source, caveats, and full context" appears;
- amendment labels appear where available;
- final-passage labels appear where available;
- procedural-context labels appear where available;
- limited-context and not-counted labels appear where available.

The UI still distinguishes amendment evidence from final passage by using the stored `vote_context.vote_type` or row vote type. Parent bill context remains supporting context.

## Rendered review method

- `next dev` hit the known Windows/Codex `spawn EPERM` issue.
- `npm run build` succeeded.
- `next start` served the production build locally at `http://127.0.0.1:3000`.
- FastAPI served local read endpoints at `http://127.0.0.1:8000`.
- In-app Browser checks validated viewport metrics and evidence labels.
- No screenshots were committed; the reproducible rendered review output is summarized above.

## Tests and build

- Targeted frontend tests:
  - `node --test frontend\lib\proceduralContext.test.mjs frontend\lib\evidenceGrouping.test.mjs frontend\lib\issueOverview.test.mjs frontend\lib\issueReadiness.test.mjs frontend\lib\profileMvpProfile.test.mjs frontend\lib\voteCardSummary.test.mjs`
  - Result: 29 passed.
- Production build:
  - `npm run build`
  - Result: passed.

## Known limitations

- On 1440x900 and 1366x768, the first issue section starts just below the first viewport; the profile identity and quick read are visible immediately, and issue content needs a small scroll.
- Mobile still necessarily stacks ZIP lookup, current profile, quick read, and issue content vertically; the pass prevents horizontal overflow but does not remove mobile scrolling.
- Browser automation used rendered metrics and text checks rather than committed screenshots.
- The sparse-profile check used loaded placeholder-style data for Rubio (R-FL), which is useful for empty-state behavior but not a rich evidence review.

## Recommendation

Phase 22 is ready for PR review after final checks. The next milestone should be either:

1. a mobile-first profile compression pass if the remaining mobile scroll is too high; or
2. a focused evidence-navigation pass that adds explicit "jump to best evidence" anchors and show-more behavior for very large Senate issue sections.
