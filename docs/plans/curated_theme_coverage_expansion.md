# Milestone Plan: Curated Theme Coverage Expansion

## Intent

- Immediate task: expand safe curated public theme coverage for reviewed issue facets after PR #65.
- Larger-goal alignment: make top-level interpretation more specific and understandable without allowing raw evidence, audit, source, or bill-title strings into public copy.

## Outcome

- User-visible or operational result: reviewed issue copy uses more curated public themes where the facet itself supports them, while ambiguous facets continue to use safe fallbacks or procedural labels.

## Scope And Boundaries

- In scope: `PUBLIC_THEME_BY_FACET`, focused helper/overview tests, audit documentation, validation, and a focused PR.
- Out of scope: backend/schema/data changes, ingestion changes, support/opposition semantics, readiness semantics, UI layout changes, LLM theme generation, and guessing themes from raw vote descriptions.
- Files/systems likely touched: `frontend/lib/publicCopyThemes.mjs`, `frontend/lib/publicCopyThemes.test.mjs`, `frontend/lib/issueOverview.test.mjs`, `docs/plans/`, `docs/review_packets/`.

## Decision Envelope

- Codex may decide and execute: exact high-confidence theme strings, tests proving fallback reduction, and documentation wording.
- Explicit approval required for: backend/data/schema changes, public-copy safety contract changes, broad inferred mappings, or any production write.

## Definition Of Done

- [x] Facet audit completed and reported before implementation.
- [x] High-confidence mappings implemented only where the facet itself supports the theme.
- [x] Existing PR #65 unsafe-string protections preserved.
- [x] Tests/build/static scan validation recorded.
- [x] Review packet or final documentation updated.
- [x] Focused PR opened.
- [x] Final reconciliation completed.

## Baseline

- Branch/base commit: `codex/curated-theme-coverage-expansion` from `main` at PR #65 merge commit `3bb247bbe214fa8f272c0aa894e349dc2a938157`.
- Production/deployment state, if relevant: PR #65 was merged and Vercel production deployment was green before this branch.
- Tracked working tree: clean before edits.
- Known unrelated untracked artifacts: `docs/review_packets/chamber_filtering_data_integrity_audit.md`, `review_bundle_frontend_data_grounding/`.

## Implementation Sequence

1. Read interpretation principles and PR #65 safety contract.
2. Audit active frontend tests/helpers and comparable reviewed evidence facets.
3. Report audit table before implementation.
4. Add only high-confidence curated mappings.
5. Add focused tests for mappings, fallback reduction, and unsafe marker preservation.
6. Run validation and static scan.
7. Open focused PR.

## Progress Checklist

- [x] Discovery
- [x] Implementation
- [x] Validation
- [x] Documentation
- [x] Commit/PR readiness

## Discoveries

- Most specific facets visible in current frontend tests already have explicit curated public themes from PR #65.
- The main quality gaps are broad domain facets that currently surface awkward safe short labels: `environment_energy`, `economy_taxes`, `justice_public_safety`, and `national_security_foreign`.
- `Motion to commit` had an explicit mapping, but it pointed to the generic national-security fallback. The facet itself supports the clearer procedural theme `motions to commit`.
- `House amendment vote` appears often in comparable reviewed evidence, but the facet only identifies vote type and does not identify policy substance. It should force the normal domain fallback rather than receive a substance theme or short-label public theme.

## Decisions And Rationale

- Add explicit domain-facet themes:
  - `economy_taxes`: `fiscal and tax measures`
  - `environment_energy`: `environment and energy measures`
  - `justice_public_safety`: `public-safety and legal-policy measures`
  - `national_security_foreign`: `national-security and foreign-policy measures`
- Change `Motion to commit` / `motion_to_commit` from a generic fallback to `motions to commit`.
- Skip `House amendment vote` because it is ambiguous and procedural without policy substance; force it to the domain fallback so it does not surface as an awkward short-label theme.
- Leave `administrative_law_and_regulatory_procedures` unchanged for now; it is a medium-confidence short-label fallback in ambiguous amendment context.

## Audit Table

| Facet id / label | Domain | Current public theme | Curated now | Generic fallback now | Recommendation | Confidence | Reason |
|---|---|---:|---:|---:|---|---|---|
| `environment_energy` | Environment & Energy | `environment energy` | no | no | `environment and energy measures` | high | Facet is broad but clear; current short label is awkward. |
| `economy_taxes` | Economy & Taxes | `economy taxes` | no | no | `fiscal and tax measures` | high | Facet supports a safe domain-level noun phrase. |
| `justice_public_safety` | Justice & Public Safety | `justice public safety` | no | no | `public-safety and legal-policy measures` | high | Facet supports the domain phrase used elsewhere. |
| `national_security_foreign` | National Security & Foreign Policy | `national security foreign` | no | no | `national-security and foreign-policy measures` | high | Facet supports a safe grammatical domain phrase. |
| `House amendment vote` | Multiple | `House amendment vote` | no | no | force domain fallback / no substance mapping | skip | Vote-type only; no policy substance without raw descriptions. |
| `Motion to commit` | National Security & Foreign Policy | `other reviewed national-security measures` | yes | yes | `motions to commit` | high | Facet itself supports a procedural theme. |
| Specific Economy facets | Economy & Taxes | curated strings | yes | no | keep existing | high/medium | Existing themes are facet-grounded. |
| Specific Justice facets | Justice & Public Safety | curated strings | yes | no | keep existing | high | Existing themes are facet-grounded. |
| Specific National Security facets | National Security & Foreign Policy | curated strings | yes | no | keep existing | high | Existing themes are facet-grounded. |
| Specific Education / Health / Environment facets | Target domains | curated strings | yes | no | keep existing | high | Existing themes are facet-grounded. |
| `administrative_law_and_regulatory_procedures` | Justice & Public Safety | `administrative law and regulatory procedures` | no | no | leave unchanged | medium | Phrase is safe, but current use is ambiguous amendment context. |

## Deviations Or Corrections

- None so far.

## Validation Results

- `node --test lib\*.test.mjs`: passed, 70/70.
- `npm run lint`: passed with 8 existing React hook dependency warnings and 0 errors.
- `npm run build`: passed with the same 8 existing React hook dependency warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static`: no matches.
- Local rendered shell at `http://127.0.0.1:3000`: desktop default had no horizontal overflow.
- Local rendered shell at `390x844`: no horizontal overflow.
- Local Valerie Foushee National Security rendered validation remains unavailable because ZIP `27701` is not in the loaded local ZIP map; source-level tests cover the public-copy safety boundary and curated theme behavior.
- The generic receipt explainer line still contains `classification reason`, consistent with the prior production smoke finding that this is receipt-affordance copy rather than top-level issue interpretation copy.
- Revision before ready review: `House amendment vote` now uses a force-fallback path so skipped vote-type-only facets do not surface as top-level short-label themes.

## Production Writes

- Performed: no
- Scope: none.
- Expected effects: none.
- Actual effects: none.

## Rollback Paths

- Revert this branch's scoped helper/test/documentation commit.

## Blockers

- None currently.

## Final Reconciliation

- Definition of done satisfied: yes.
- PR: #66.
- Final commit: `58aa150` before final documentation amendment; branch head contains the same scoped milestone changes.
- Remaining limitations: local Valerie production-like rendered validation is blocked by unavailable local ZIP/evidence data.
- Recommended next step: review PR #66, then mark ready if the audit scope and skip decisions look right.
