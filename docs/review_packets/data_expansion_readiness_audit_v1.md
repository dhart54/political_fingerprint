# Data Expansion Readiness Audit V1

## Summary

Political Fingerprint is ready to keep improving the current golden profile/read flow, but it is not ready to broadly expand public reads across all representatives, both chambers, both the 118th and 119th Congresses, or six years of House/Senate voting data.

The strongest current foundation is the frontend profile composition, issue-read safety contract, evidence drawers, and deterministic golden render harness. The weakest expansion dependencies are coverage inventory, legislator/ZIP metadata, chamber-aware Senate semantics, amendment identity/retrieval, per-member source coverage reporting, and production-shaped validation breadth.

Recommended next milestone: **Data inventory / source manifest**. Do not add broad production data until the app can report exactly which chambers, Congresses, sessions, roll calls, members, source links, interpretations, ZIP mappings, and caveats are loaded.

## Current Architecture Map

| Layer | Current implementation | Expansion implication |
| --- | --- | --- |
| Backend API | FastAPI routes in `backend/app/api`; database-first read layer in `backend/app/api/precomputed.py`; fixture fallback when DB reads are unavailable. | API shape can serve more members, but broad coverage requires explicit source/coverage metadata rather than silent fixture or sparse data fallback. |
| Lookup/search | `/lookup/zip/{zip}`, `/lookup/zips`, `/legislators/search`; ZIP maps to one House district plus both state senators. | Current ZIP model cannot represent split ZIPs, address ambiguity, stale districts, or multiple possible House members. |
| Profile loading | Frontend loads fingerprint and positions, then issue evidence on demand; profile scope supports `all`, `119`, and `118`. | Profile flow is reusable, but sparse members can look broken or misleading without per-member coverage labels. |
| Issue reads | `deriveIssueReadiness`, `buildRecordNarrative`, `buildIssueCardPreview`, and `buildIssueOverview` compose from interpreted support/opposition counts and opened evidence rows. | Good public-read foundation if data rows are reviewed; risky if many rows lack vote meaning, facets, source links, or chamber-specific context. |
| Evidence receipts | Evidence rows include roll call identity, source URL, interpretation fields, vote context, amendment references, and drawers/full-list surfaces. | Receipt model is strong enough to scale only if source coverage and amendment/source references are populated consistently. |
| Record Across Congresses | House-only internal adapter from comparable-family artifact, exposed to frontend through a token-gated Next route and sanitized public response. | Not a general multi-Congress comparison engine; it is a limited House family-evidence availability panel. |
| ETL/import | Fixture seed, House Clerk adapter, Senate XML adapter, current-Congress refresh, 118th historical refresh, bounded write gates, rollback helpers. | Useful scaffolding exists, but broad expansion still needs manifests, data completeness checks, and chamber-specific interpretation/audit gates. |
| Validation | Source tests plus PR #70 golden render fixture for dominant, mixed, limited, unsafe raw strings, receipts, and Record Across. | Strong for golden copy safety; insufficient for all-member, Senate, ZIP ambiguity, performance, and production-shaped breadth. |

## Current Data Coverage Map

### Fixture and local fallback coverage

- Default fallback fixtures: 3 legislators, 1 House member, 2 senators, 14 roll calls, 21 vote rows, 2 ZIP mappings.
- Fixture ZIPs: `27701` and `27601`, both mapped to `NC-04`.
- Fixture roll calls are 118th Congress rows across House and Senate.
- Frontend default profile is sample House member `Aaron Bean`; ZIP lookup auto-loads default ZIP `27701` where available.

### Local cached source files observed

| Source cache | Local count |
| --- | ---: |
| House Clerk 2023 roll XML | 724 |
| House Clerk 2024 roll XML | 517 |
| House Clerk 2025 roll XML | 0 |
| House Clerk 2026 roll XML | 222 |
| Senate XML 118 session 1 | 352 |
| Senate XML 118 session 2 | 339 |
| Senate XML 119 session 1 | 0 |
| Senate XML 119 session 2 | 178 |

These are local repository/source-cache counts, not production coverage guarantees.

### Valerie/Foushee and golden flow

- Recent milestones make Valerie-like public reads the golden reference: dominant National Security, Economy, Justice; mixed Immigration; limited one-sided guards.
- Golden render fixture uses deterministic Valerie-like fixture data, not production ZIP/API access.
- Local validation history notes that ZIP `27701` was sometimes unavailable in local live data, which PR #70 addressed for rendered validation by bypassing ZIP/API dependencies.

### Sample/fallback behavior

- Backend read layer falls back to deterministic fixture outputs if DB queries return unavailable.
- Coverage metadata reports `data_source = database` or `fixtures`, but the first screen still needs stronger user-facing warnings when production is expected and fixture fallback appears.
- Frontend shows "Sample profile shown until you search your ZIP" for the default House profile.

## What The App Supports Today

1. **Representative lookup**

The app can search loaded legislators by display name and select a profile. Search returns all loaded legislators when the query is empty. It does not certify currentness beyond the loaded `legislators` rows and `in_office` usage in metadata.

2. **ZIP/district flow**

The app can map a loaded 5-digit ZIP to one state/district, one House representative, and both senators. It does not support split ZIPs, address-level lookup, district ambiguity, redistricting caveats, or stale-member alerts.

3. **Chamber assumptions**

Most public profile and issue components are chamber-generic at the rendering level. Record Across is explicitly House-only. ETL has House and Senate adapters, but Senate interpretation and amendment support are not yet public-read equivalent.

4. **Congress assumptions**

Public profile scopes are `all`, `119`, and `118`. The scope copy says "Full record" for 118th + 119th and separates Congress counts when available. This is not the same as a general six-year or all-Congress model.

5. **Current data loaded for Valerie/Foushee**

The repo contains many Valerie/Foushee interpretation batch artifacts and golden fixture scenarios. The audit did not query production, so production row counts are not asserted here. The safe conclusion is that Valerie-like public reads are the reviewed golden target, while local deterministic render validation no longer depends on live Valerie ZIP loading.

6. **Sample/fallback profile behavior**

Fallback data supports a tiny NC/118th sample. The home page starts from a sample House profile and attempts ZIP `27701`. This is useful for development, but national expansion must not allow fixture fallback to be mistaken for production coverage.

## What Would Break Or Become Misleading

| Expansion | Likely breakage or misleading read |
| --- | --- |
| All current House members | Many profiles may have sparse or uneven reviewed vote meaning. Without per-member coverage reporting, a "clearest issue read" can look comparable across members when evidence depth differs. |
| All current Senators | Senate rows use different procedure, amendment, nomination, treaty, and document-reference patterns. House-oriented copy and Record Across assumptions would not safely apply. |
| 118th + 119th House | Scope controls exist, but cross-Congress availability can be confused with continuity or change. Family-level matching only covers a limited House artifact. |
| 118th + 119th Senate | 118th/119th Senate source files/adapters exist in part, but public-safe comparable-family, amendment, and chamber-specific interpretation models are not ready. |
| Last 6 years House/Senate | The current schema can store more Congresses, but API scope, precompute windows, UI labels, Record Across artifact, and validation are locked around 118/119 assumptions. |

## Ready To Scale

- **Frontend profile flow:** reusable profile, scope, issue navigation, and evidence drilldown components are in good shape for more loaded officials.
- **Profile/card/issue read composition:** PR #65 through PR #70 established safe public-copy boundaries, reviewed-sample framing, limited/mixed guards, and receipt paths.
- **Evidence drawers:** receipt/detail surfaces can expose raw official text and source basis without leaking it into top-level copy.
- **Issue grouping:** facet/theme helpers and evidence grouping provide a workable presentation layer when reviewed facets exist.
- **Rendered validation harness:** the golden fixture route and Playwright test are a strong regression harness for public-copy safety and responsive behavior.
- **Source/caveat model:** evidence rows have fields for vote context, source basis, uncertainty, caveats, and not-to-infer text.
- **ETL safety scaffolding:** current/historical refresh modules include bounded dry-runs, approval phrases, rollback generation, deferred rows, and post-write thinking.

## Not Ready To Scale

- **Data ingestion:** no single manifest currently reconciles source files, production tables, coverage windows, deferred rows, interpretation coverage, source-link coverage, and derived outputs.
- **Legislator metadata:** loaded members can be found by Bioguide/display slug, but currentness, term boundaries, House vacancies, Senate class/seat context, and district changes need hardening.
- **Vote source coverage:** source URL count exists, but public/product gates need per-chamber, per-Congress, per-member, per-domain source coverage and missing-source reporting.
- **Senate support:** adapters exist, but public reads need chamber-aware nomination/treaty/cloture/amendment/rule equivalents and Senate-specific caveats.
- **Issue classification:** keyword/subject scoring is deterministic but broad; large-scale classification needs validation by chamber, Congress, bill type, amendment type, and false-positive domains.
- **Amendment identity/retrieval:** House and Senate amendment work exists, but broad amendment reads still need robust identity, parent/child context, and source-purpose retrieval before counting.
- **District/ZIP lookup:** one ZIP to one district is not safe for national coverage.
- **Performance:** broad all-member, all-domain, multi-Congress reads may stress client fill-in evidence calls and unindexed/scope-heavy read paths unless measured.
- **Validation/CI:** current golden harness does not cover hundreds of profiles, Senate, split ZIPs, source coverage warnings, or large evidence lists.
- **User-facing caveats:** current caveats are good for golden reads, but expansion needs prominent loaded-coverage and stale/limited-data warnings.

## Biggest Trust Risks

| Risk | Why it matters | Mitigation before expansion |
| --- | --- | --- |
| Thin evidence being overread | A member with 1-2 interpreted votes can appear to have a meaningful issue pattern. | Per-profile and per-issue coverage badges; hard no-top-level-read thresholds; fixture tests for sparse profiles. |
| Chamber procedure differences | Senate nominations, cloture, treaties, and amendment handling differ from House floor votes. | Senate compatibility audit and chamber-aware interpretation rules before Senate public reads. |
| Congress-to-Congress overclaiming | Side-by-side counts can imply change or consistency. | Keep Record Across as evidence availability only; no trend/change labels without explicit methodology. |
| Party/outcome context dominating the read | Party majority and outcome facts can be mistaken for motive or quality. | Keep party/outcome context secondary and receipt-grounded; avoid evaluative party-break language. |
| Stale district/member data | Incorrect current representative undermines the entire product promise. | Metadata refresh manifest, term/currentness validation, and stale-data labels. |
| ZIP ambiguity | Split ZIPs can select the wrong House district. | Address-level or ambiguity-handling milestone before national ZIP expansion. |
| Incomplete source links | Receipts are central to trust; missing links weaken top-level claims. | Source-link coverage gates and no-go thresholds by member/domain. |
| Raw procedural text leaking into top-level copy | PR #65-#70 fixed the golden surface, but new facets can regress. | Expand golden fixtures with new facets/chambers before public rollout. |

## House Readiness Assessment

House expansion is the nearest safe path, but only as a bounded current-Congress pilot after inventory and metadata hardening.

Ready pieces:

- House Clerk adapter handles session-aware roll identities and official XML source URLs.
- Profile and issue UI can render House records with receipts.
- Record Across has a House-only limited availability model.
- Current analysis artifacts show possible House coverage for comparable families, but also show strict contracts can drop coverage to zero.

Not-ready pieces:

- 119th House session 1 local cache is absent in this checkout, while 2026 session 2 cache is partial.
- ZIP/district and current-member metadata are not national-grade.
- Source/interpretation coverage is not surfaced per member before opening a profile.
- Amendment-heavy rows still require careful source-grounded review and cannot be bulk-counted from parent measure context.

Assessment: **pilot-ready after inventory and metadata gates; not broad-rollout ready.**

## Senate Readiness Assessment

Senate expansion is not ready for public broad reads.

Ready pieces:

- Senate XML adapter exists.
- Senate source caches and tests exist.
- Senate fact/classification/enrichment review artifacts indicate active groundwork.

Not-ready pieces:

- Public UI/read copy is not Senate-specific enough.
- Record Across has no Senate equivalent.
- Senate nominations, treaties, cloture, amendment references, and document naming need explicit public-read semantics.
- Local source caches for 119th Senate session 1 are absent in this checkout; 119th session 2 is partial.
- Senate member identity mapping has known LIS/Bioguide handling complexity.

Assessment: **audit-ready, not public-expansion ready.**

## Multi-Congress Readiness Assessment

The app can show `118`, `119`, and `all` profile scopes, and Record Across can display House family evidence availability across 118th and 119th Congresses. It should not yet be treated as a general cross-time comparison system.

Ready pieces:

- Scope selector and scope metadata exist.
- Position rows can include Congress breakdowns.
- Record Across copy explicitly avoids change, movement, consistency, and causal claims.

Not-ready pieces:

- Record Across artifact is limited to 118/119 House policy-question families.
- Six-year windows are not represented in API scope, UI copy, derived artifacts, or tests.
- Broad domains alone are too coarse for cross-Congress comparison and can hide different agendas.
- Strict comparable-family contracts currently reduce broad coverage sharply, which is a feature for trust but a product limitation.

Assessment: **limited House 118/119 availability display is ready; broad multi-Congress interpretation is not.**

## Validation Harness Gap Analysis

The PR #70 harness is valuable and should be expanded, not bypassed.

Current coverage:

- dominant, mixed, and limited issue reads;
- unsafe raw strings present in receipts but absent from top-level copy;
- representative votes, full reviewed list, details drawers;
- Record Across panel visibility;
- desktop and `390x844` overflow;
- internal token/header/internal-route leakage checks.

Gaps before expansion:

- no all-member fixture batch;
- no Senate golden fixture;
- no split-ZIP or stale-member fixture;
- no source-link-missing warning fixture;
- no profile with many domains and hundreds of evidence rows;
- no performance budget assertions;
- no fixture proving fallback database/fixture source is prominently labeled;
- no Record Across sparse/no-family and Senate-hidden coverage across production-shaped members.

## Recommended Next Implementation Milestones

1. **Data inventory / source manifest**

Create a read-only manifest that reports loaded chambers, Congresses, sessions, roll-call counts, member counts, vote counts, source URL coverage, classification coverage, interpretation coverage, deferred rows, and derived output coverage. Make it runnable locally and against production read-only credentials.

2. **Legislator metadata hardening**

Add term/currentness/district metadata checks, stale-member detection, member identity reconciliation, and current-office coverage reporting. Include Senate identity mapping checks.

3. **ZIP and district ambiguity hardening**

Replace one-ZIP-one-district assumptions with ambiguity handling. Do not auto-select a House member when a ZIP crosses districts without address-level resolution or an explicit ambiguity UI.

4. **House current-Congress expansion pilot**

Pilot a bounded House-only, current-Congress slice with source manifest gates, source-link thresholds, per-member coverage badges, rollback, and rendered fixtures for sparse/dense profiles.

5. **Render fixture expansion**

Add production-shaped House fixtures: sparse member, dense member, missing source links, many evidence rows, no ZIP match, and Record Across sparse/eligible states.

6. **Senate compatibility audit**

Audit Senate vote types, source coverage, amendment references, nominations, treaties, cloture, and public caveats. Produce no public Senate reads from House assumptions.

7. **Chamber-aware vote interpretation rules**

Define and test chamber-specific eligibility, vote type, amendment, procedural, nomination, treaty, and source-basis rules before Senate support/opposition reads.

8. **Multi-Congress comparison hardening**

Expand family-level matching only where source-grounded comparability exists. Keep broad issue-domain side-by-side views from implying change, consistency, or movement.

9. **Production rollout gates**

Define no-go thresholds for per-member interpreted Yes/No coverage, source links, stale metadata, ZIP ambiguity, source manifest mismatches, rendered validation, and rollback readiness.

## Explicit No-Go Items

- Do not publish Senate reads using House assumptions.
- Do not claim cross-Congress change, consistency, trend, or movement from broad issue-domain counts.
- Do not expand ZIP lookup nationally without split-ZIP/address ambiguity handling.
- Do not add hundreds of representatives without source and interpretation coverage reporting.
- Do not generate top-level reads for members with thin or unreviewed vote meaning.
- Do not count amendment rows from parent-measure context when the amendment purpose/identity is not source-grounded.
- Do not allow fixture fallback to appear like production coverage.
- Do not treat procedural, limited-context, or not-voting rows as support/opposition evidence.
- Do not open production writes from this audit PR.

## Final Recommendation

Proceed with **Data inventory / source manifest** next. The product should earn broader coverage by making loaded data visible and falsifiable before adding more public reads. The House current-Congress pilot should wait until the manifest and legislator/ZIP hardening are in place; Senate and multi-year expansion should wait for separate chamber-aware and cross-Congress methodology gates.
