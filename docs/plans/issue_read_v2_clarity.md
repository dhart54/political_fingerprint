# Milestone Plan: Issue Read v2 Clarity

## Intent

- Make issue reads feel like public interpretation, not evidence plumbing.
- Keep the product promise: clear voting-record interpretation with receipts.

## Outcome

- Dominant interpreted Yes/No records are labeled as mostly supported/opposed in the reviewed sample instead of primarily mixed.
- Issue summaries synthesize policy themes instead of leaking raw roll-call/classification text.
- Representative vote rows lead with what the vote did and how the representative voted, with audit rationale kept in drawers/details.

## Scope And Boundaries

- In scope: frontend issue-read labels, issue overview copy helpers, public theme synthesis, vote-card visible summaries, focused tests, rendered validation, review packet.
- Out of scope: backend, schema, ingestion, methodology, token/config, production writes, Record Across methodology, broad redesign.

## Decision Envelope

- Codex may use existing client-side fields, facet labels, overview phrases, policy effects, vote descriptions, and current evidence grouping helpers to synthesize safer public themes.
- Codex may revise labels/copy when support/opposition counts are already computed and dominant.
- Explicit approval is required for new data semantics, backend changes, or unsupported inference.

## Definition Of Done

- [x] Required audit completed.
- [x] Dominant records with at least two-thirds support or opposition are not labeled primarily mixed.
- [x] Public issue summaries use short policy themes, not raw audit/classification fragments.
- [x] `What that means` is concise and policy-substance-first.
- [x] Representative vote rows do not lead with audit rationale.
- [x] Source/caveat drawers and full reviewed vote list remain available.
- [x] Focused tests added/updated for dominant vs split labels, raw-text avoidance, concise theme copy, vote-row copy, drawers, and full-list access.
- [x] Required validation passes: node tests, lint, build, static internal-route/token scan.
- [x] Rendered desktop and 390x844 validation completed or limitations documented.
- [x] Review packet created.
- [ ] PR opened and ready for review unless a stop condition is reached.

## Baseline

- Branch/base: `codex/issue-read-v2-clarity` from `main` at `58b687a4aed436d841cad0142eb3ba3c3f67db86`.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.
- Production writes: not authorized.

## Implementation Sequence

1. Audit labels, issue overview helpers, vote-card summaries, and tests.
2. Design the smallest safe theme synthesis and dominant-label changes using existing fields.
3. Implement copy/label updates.
4. Add focused regression tests.
5. Run required validation and static scan.
6. Perform rendered validation with Valerie Foushee National Security if practical.
7. Create review packet and reconcile plan.
8. Commit, push, and open PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- `docs/interpretation_principles.md` was read before implementation. This work should use clear findings, policy substance first, receipts available, and avoid motive/ideology/character claims.
- Audit found the stale mixed framing in `deriveIssueReadiness`, profile narrative labels, and issue card labels. `buildIssueOverview` already had concrete measure-category copy available, but the finding line still preferred broad domain wording.
- Vote rows already used public summaries first in most mapped cases, but generic fallback summaries could still inherit audit-leading source text such as "The vote is useful because".

## Decisions And Rationale

- Keep the existing two-thirds dominance threshold already used by issue overview copy.
- Treat mixed support/opposition as a strong read when one side reaches that two-thirds threshold; reserve `mixed_but_interpretable` for close splits.
- Use concrete reviewed measure categories in the issue finding line when available, with broad issue-area language only as fallback.
- Strip audit-lead phrases from generic vote-card summaries while keeping source/caveat details in drawers.

## Deviations Or Corrections

- None currently.

## Validation Results

- `node --test lib\*.test.mjs`: passed, 61 tests.
- `npm run lint`: passed with 8 existing React hook dependency warnings.
- `npm run build`: passed with the same 8 warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- Rendered local production shell at `http://localhost:3007`: desktop and 390x844 mobile had no page-level horizontal overflow.

## Production Writes

- Performed: no.
- Scope: not authorized.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert the focused Issue Read v2 branch commit(s).

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes.
- Remaining limitations: local production shell rendered, but data-backed Valerie Foushee National Security issue cards were not locally renderable in this workspace. Source-level tests cover the 128 opposed / 22 supported National Security case, concrete categories, full-list access, and drawer preservation.
- Commit: `26c723bb91a28792fbb2ca2d82c00dc7e8f8bef6`.
- PR: #64, `https://github.com/dhart54/political_fingerprint/pull/64`.
- Recommended next step: wait for PR checks and review.
