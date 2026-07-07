# Milestone Plan: Address-Level Lookup / Ambiguity UI Design Spike V1

## Intent

- Immediate task: decide the safest product path for ZIP lookup before national rollout.
- Larger-goal alignment: prevent Political Fingerprint from incorrectly auto-selecting a House representative when ZIP-only evidence is ambiguous.

## Outcome

- User-visible or operational result: a docs-only design spike and review packet that recommend a lookup flow, privacy posture, phased implementation plan, acceptance criteria, and no-go rules.

## Scope And Boundaries

- In scope: current lookup risk recap, safe user flows, draft copy, source option assessment, privacy posture, phased implementation plan, acceptance criteria, and draft PR.
- Out of scope: public lookup behavior changes, backend route changes, frontend behavior changes, national ZIP/address data ingestion, paid API integration, external service setup, local or production DB mutation, and address-level resolver implementation.
- Files/systems likely touched: this plan and `docs/review_packets/address_lookup_ambiguity_ui_design_spike_v1.md`.

## Decision Envelope

- Codex may decide and execute: docs structure, recommendation wording, flow and copy tables, source-option matrix, and acceptance criteria.
- Explicit approval required for: code changes, public behavior changes, external API signup/use, paid services, production credentials, data ingestion, schema changes, or storing/sending real user addresses in any implementation.

## Definition Of Done

- [x] Branch created from clean `main` after PR #74.
- [x] Applicable repo instructions and requested recent docs read.
- [x] Current backend lookup/search/schema, frontend ZIP copy, home sample behavior, and recent report findings inspected.
- [x] Official source documentation checked where API availability/terms are time-sensitive.
- [x] Review packet created with recommendation, flows, copy, source matrix, privacy posture, plan, criteria, no-go items, and next milestone.
- [x] Diff confirmed docs-only.
- [x] Optional frontend checks run if cheap and not distracting.
- [ ] Focused draft PR opened.
- [ ] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/address-lookup-ambiguity-ui-design-spike-v1` from `main` after PR #74 merge commit `8c611f26be4dc117b75dd708549e871e9b509676`.
- Production/deployment state, if relevant: no production write, credential use, or behavior change authorized.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read instructions, plan conventions, interpretation guardrails, and requested recent docs.
2. Inspect current ZIP lookup, supported ZIP, search, schema, frontend, and recent report findings.
3. Check official documentation for time-sensitive address/district source options.
4. Draft the review packet and update this plan.
5. Run docs-only diff validation and optional frontend checks.
6. Stage only milestone docs, commit, push, and open a focused draft PR.

## Progress Checklist

- [x] Discovery
- [x] Source option research
- [x] Documentation
- [x] Validation
- [ ] Commit/PR readiness

## Discoveries

- Current backend ZIP lookup resolves one ZIP record and one state/district, then selects one House member by state/district.
- The schema stores `zip_district_map.zip` as the primary key, so production storage cannot represent multiple districts for one ZIP without a future schema/design change.
- The frontend auto-runs default ZIP `27701`, displays `ZIP ... maps to ...`, and auto-selects a returned House member when present.
- Supported ZIP copy currently says "Loaded ZIP Coverage" and "Showing N loaded ZIP mappings from data_source."
- Recent reports found all repository/local ZIP mappings are fixture-only and that ZIP `27601` is locally ambiguous across `NC-02` and `NC-04`.
- Recent metadata work found missing/stale/currentness caveats and Senate seat/class gaps that must gate any automatic result.
- Official Census Geocoder docs support address-to-geographies lookup, benchmark/vintage parameters, Congressional District layers, and server-side use is favored because CORS is not supported.
- Google Civic current official reference lists Elections and Divisions resources; it supports `divisionsByAddress`, but the older representative lookup surface is not the safe default for a new production design.
- Commercial address vendors can improve validation/geocoding but introduce cost, terms, privacy, key-management, and third-party data processing concerns.

## Decisions And Rationale

- Recommend a phased hybrid path: ZIP first for low-friction entry, ambiguity UI when ZIP-only evidence is uncertain, address-level resolution only when needed and only after privacy/source review, plus manual representative search fallback.
- Prefer Census Geocoder for a dev-flag prototype because it is official, no paid vendor signup is needed, and it can return geographic districts from an address, while still requiring no raw-address storage by default.
- Do not recommend national ZIP-only auto-selection because split ZIPs and stale/currentness gaps can produce the wrong House member.
- Keep all copy neutral and trust-building: explain what is known, what is uncertain, and how the user can continue without implying precision the data does not support.

## Deviations Or Corrections

- None yet.

## Validation Results

- `git diff --name-only`: empty before staging because both milestone docs were new/untracked.
- `git status --short`: showed only the two intended new milestone docs plus known unrelated untracked artifacts.
- `git diff --check`: passed.
- `node --test lib\*.test.mjs` from `frontend`: passed, 75/75. Existing Node warning remains about `frontend/package.json` not declaring `"type": "module"` while module syntax is used.
- `npm run lint` from `frontend`: passed with existing 8 React hook dependency warnings and 0 errors.
- `git diff --cached --name-only`: included only `docs/plans/address_lookup_ambiguity_ui_design_spike_v1.md` and `docs/review_packets/address_lookup_ambiguity_ui_design_spike_v1.md`.
- `git diff --check --cached`: passed.

## Production Writes

- Performed: no.
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert this docs-only spike plan and review packet from the branch.

## Blockers

- None currently. Source/vendor choice is not finalized in this milestone; a future implementation must complete terms/privacy review before integrating any third-party address API.
