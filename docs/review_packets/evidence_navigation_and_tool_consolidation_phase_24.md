# Evidence Navigation And Secondary Tool Consolidation - Phase 24

## Scope

Phase 24 is a presentation-only pass over the already restored profile evidence flow. It does not change evidence semantics, readiness thresholds, support/opposition counting, alignment logic, interpretations, classifications, schema, or production data.

## Remaining Phase 23 Problems

- Issue sections still exposed multiple overlapping explanation layers: evidence counts, grouped preview copy, issue overview, pattern copy, voter-read copy, and evidence limits.
- Grouped evidence repeated row counts and caveats before the user reached the actual vote cards.
- Large profiles needed a compact issue navigation control so users could jump among strong, mixed, limited, and procedural-heavy sections.
- Secondary workflows such as preferences, alignment setup, comparison, search/switching, and contact could still dominate the page below the main evidence.
- Long official measure titles were shortened in one component only, so display names were not consistently reusable.
- Footer/methodology copy could imply procedural rows were completely excluded from display, even though the product intentionally keeps them visible as non-counting context.

## Duplicate-Content Audit

The issue-level stack was reduced to one primary summary model:

- `Issue summary`: one compact block for what the votes were about.
- `Observed pattern`: combines the previous "what the official did" and "what pattern that creates" copy.
- `What that means`: keeps the practical voter-facing interpretation.
- `What not to infer`: collapsed behind disclosure with limits and caveats.

The separate default-visible grouped preview paragraph now uses one compact line that separates countable Yes/No votes from limited, procedural, and not-voting rows.

## New Issue-Summary Structure

Each opened issue now generally follows this order:

1. compact evidence-group scan;
2. one issue summary;
3. representative measure groups;
4. detailed vote cards with source/caveat disclosure;
5. collapsed evidence tools for contact and selected-vote context.

This keeps the strongest evidence primary while keeping proof and caveats available.

## Grouped-Evidence Compression

Grouped evidence now shows:

- concise measure label;
- evidence group type;
- countable Yes/No count;
- procedural-context count when present;
- limited-context count when present;
- not-voting count when present.

The full official title remains available inside the expanded vote-card detail.

## Issue Navigation

Large profiles now include a compact horizontal `Jump to issue` navigation row above readiness groups. It preserves the readiness sort order, exposes interpreted-count context, supports keyboard focus, and does not hide limited issues.

## Concise Measure-Name Strategy

`frontend/lib/measureDisplay.mjs` centralizes deterministic display labels for recurring long titles, including:

- FY2025 Congressional Budget Resolution
- Military Construction and VA Appropriations Act, 2026
- Temporary Government Funding Package
- Small Business Regulatory Reduction Act
- National Defense Authorization Act, 2026
- HALT Fentanyl Act
- Lower Health Care Premiums Act

Amendment labels are preserved when a title contains amendment identity, for example `Amendment 1234: National Defense Authorization Act, 2026`.

## Desktop Layout Improvements

The issue-evidence section now uses a wider evidence column on desktop and a narrower orientation column. The opened issue view avoids a full-width count banner and uses a denser two-column grouping preview where space allows.

## Secondary-Tool Consolidation

Preferences, alignment setup, comparison, election context when available, and search/switch official controls now live under one compact `Tools: preferences, comparison, and switching officials` disclosure. Contact metadata for an opened issue is also collapsed into `Evidence tools: contact and selected-vote context`.

## Issue-Selection Changes

Starter themes remain visible. Fine-grained issue controls are still available, but the full issue grid is collapsed by default. Existing guided preference semantics are unchanged: only concrete directional choices can invoke alignment.

## Copy Simplification

The UI now uses shorter language such as:

- `Jump to issue`
- `Evidence groups`
- `Issue summary`
- `Observed pattern`
- `What that means`
- `What not to infer`

The grouped preview line uses compact counts instead of repeating a paragraph of caveats.

## Methodology Wording Correction

The footer now says procedural votes may appear as context but do not count toward issue reads or alignment labels. Methodology now documents issue navigation and evidence grouping as presentation helpers that preserve official measure identity and non-counting distinctions.

## Evidence Distinctions Preserved

- Amendment evidence remains amendment evidence.
- Parent-bill context remains secondary.
- Final passage remains explicitly labeled by vote type.
- Procedural context remains visible but non-counting.
- Limited context remains non-counting.
- Not-voting rows remain excluded from support/opposition.
- Interpretations remain the only source of countable meaning.

## Production-Backed Profiles Reviewed

Bounded public API checks were run against the current Render read path:

- Valerie P. Foushee: Economy remains the strongest reviewed pattern (`0` support / `6` oppose / `1` other interpreted), while National Security (`2` support / `17` oppose) and Justice (`2` support / `4` oppose) remain mixed but interpretable.
- Thom Tillis: Senate Economy evidence returns 39 rows, 34 interpreted rows, and amendment evidence retains `senate_amendment_fact` identity with amendment references present.
- Ted Budd: Senate Economy evidence returns 39 rows, 34 interpreted rows, and amendment evidence retains `senate_amendment_fact` identity with amendment references present.
- Adam B. Schiff: mixed Senate profile returns interpreted totals and evidence fields.
- Adelita S. Grijalva: relatively sparse/limited profile returns thin interpreted evidence and limited rows without forcing a confident broad read.
- Aaron Bean: procedural/limited rows remain visible in evidence while interpreted support/opposition counts stay separate.

## Responsive Review

The code path was updated for desktop and mobile:

- issue navigation uses horizontal overflow rather than large stacked cards;
- secondary tools are collapsed;
- fine-grained issue selection is collapsed;
- grouping preview uses compact chips and two columns on wide screens;
- evidence cards keep full source details behind disclosure.

Full browser-rendered validation could not be completed locally because the Playwright browser binary is not installed in the environment and the local `next start` smoke is unreliable in the Codex-managed Windows shell. The Vercel PR preview deployed successfully, but direct unauthenticated access returned Vercel Authentication and the Vercel CLI is not installed in this environment. Rendered validation should therefore be completed against the public production deployment after merge, or against the protected preview by a logged-in Vercel user.

## Tests And Build

- Targeted frontend tests: 38 passed.
- `npm run build`: passed.
- `git diff --check`: passed.
- Production-backed API checks: passed for Valerie Foushee, Thom Tillis, Ted Budd, Adam B. Schiff, Adelita S. Grijalva, and Aaron Bean.
- Vercel PR checks: passed; preview is deployment-protected from unauthenticated automation.
- Production data writes: none.

## Known Limitations

- Rendered viewport validation still needs a browser-capable local or preview environment to record exact mobile heights.
- The compact issue navigation is a jump/open control, not a scroll-spy with live active-section tracking.
- Measure label shortening is deterministic but intentionally conservative; additional recurring measure names can be added as stable examples appear.

## Recommended Next Milestone

Run a preview-backed visual validation pass after this branch is opened, then consider measure-level guided preference choices for heterogeneous issue areas.
