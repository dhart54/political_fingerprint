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

The required production-backed public API review could not be rerun in this session because the network escalation layer rejected the bounded API command after the account usage limit was reached. The implementation remains tied to the same API fields validated in Phase 23/24:

- Valerie P. Foushee: strong Economy, mixed National Security/Justice.
- Thom Tillis: Senate amendment-heavy evidence.
- Ted Budd: Senate substantive evidence.
- Adam B. Schiff: mixed readiness profile.
- Adelita S. Grijalva: relatively sparse profile example.
- Aaron Bean: procedural-context visibility example.

## Responsive Review

The code path was updated for desktop and mobile:

- issue navigation uses horizontal overflow rather than large stacked cards;
- secondary tools are collapsed;
- fine-grained issue selection is collapsed;
- grouping preview uses compact chips and two columns on wide screens;
- evidence cards keep full source details behind disclosure.

Full browser-rendered validation could not be completed locally because the Playwright browser binary is not installed in the environment and the local `next start` smoke hit the known Windows `Start-Process` `Path`/`PATH` issue before starting a server. The production build did pass.

## Tests And Build

- Targeted frontend tests: 38 passed.
- `npm run build`: passed.
- Production data writes: none.

## Known Limitations

- Rendered viewport validation still needs a browser-capable local or preview environment to record exact mobile heights.
- The compact issue navigation is a jump/open control, not a scroll-spy with live active-section tracking.
- Measure label shortening is deterministic but intentionally conservative; additional recurring measure names can be added as stable examples appear.

## Recommended Next Milestone

Run a preview-backed visual validation pass after this branch is opened, then consider measure-level guided preference choices for heterogeneous issue areas.
