# Neutral official-contact disclosure

## Intent and scope

Connect the existing ordinary vote receipt to optional supplied official contact details while keeping exact vote meaning, limitations and sources visible. This is the established north_star_action_plan Civic Action Model/Phase B, not a new interpretation or product direction.

Authorized: a reusable disclosure/helper and isolated IssueDetail -> ChronologicalActionLedger -> ActionReceipt wiring. Explicit-open GET only; safe phone/site/form/source paths; returned member identity; stored/fallback/missing provenance and actual retrieval date; Close focus restoration; invalidate on Close, receipt collapse, member/issue/scope changes. No automatic external navigation or transmission of vote/query/referrer context. No advocacy, message creation/submission, tracking, persistence, enrichment/import, acceptance/publication, schema/security configuration/secrets changes, manual deployment or merge before independent review.

## Baseline and ownership

Isolated .w/oc / codex/voter-official-contact-disclosure from freshly verified main fc7d68f1541df30abb98ef81f3c11e84881a6de4. Root AGENTS, interpretation principles and relevant workflows read; no .agents or frontend-scoped AGENTS exists. Dependencies installed from locked offline cache (322 packages).

PR193 retains its reserved shared-card work at a1ea303; exact owned paths do not include this wiring/helper/component. No page.js, RepresentativeExperience, RecordAtAGlance, sharedRecordCard or review-route changes. Immigration .w/ib, historical checkouts and private integration receipts remain untouched. Existing contact API/read helper are reused unchanged; legacy calculated interpretation summary is not imported.

## Design decisions

- One optional disclosure below the expanded ordinary-route receipt's existing proof grid; no eager fetch or duplicate evidence narrative. Recorded-snapshot review routes remain isolated from live contact reads.
- API receives only legislatorId. Component key includes member/issue/scope; receipt lifetime plus request sequence invalidates obsolete responses, including Close/reopen and collapse. Explicit Close synchronously restores its own opening button; history/selection callbacks remain unchanged.
- Helper whitelists fields and validates exact identity/status. HTTPS House/Senate links only, no credentials/custom ports/query/fragment/control characters. Never repair, guess or substitute an unsafe path. A declared source family is shown only with a safe matching source URL. Telephone syntax comes only from supplied digits/punctuation, without inferred prefixes/extensions.
- External anchors use noopener/noreferrer and no-referrer. Date renders supplied calendar date; unknown origin/source/date remains unknown. Missing fields and unsafe fields are distinguished without fresh-verification, constituency or current-service claims.
- New suite is explicitly included in existing exact-head frontend CI. Existing receipt tests select their original direct-child expansion control now that expanded receipts have a separate optional button; assertions are retained.

## Validation and progress

- Baseline local browser case fails because the contact entry point is absent, after proving the exact receipt was loaded and no contact request occurred.
- Safety helper:20 focused units pass, including unsafe/context-bearing URLs, phone parameters, partial metadata, wrong identities, prototype-key source types and unsafe/mismatched source-family claims.
- Initial focused browsers:20 pass/1 harness failure. The card journey already auto-expands its first linked receipt; the new test mistakenly clicked it closed before inspection. Corrected to assert the established expanded state. Original JSON retained.
- Lint passes with8 existing unrelated Hook warnings; no new warning.
- Coherent focused run:25/25 Chromium tests pass (31.1 seconds, no retries/skips), including22 contact cases and3 affected existing receipt regressions. After the final source-family guard, all7 affected metadata-state cases pass separately (9.0 seconds). 320/390/1440 screenshots captured; narrow/desktop results visually inspected. Exact vote/source markup and six card IDs/links/text are compared, with history/source hash unchanged. Phone/site/form/source navigation is optional; the outbound browser case is intercepted and proves no referrer/query propagation.
- After coherent focused completion, use the established full release gate in hosted exact-head CI (units/lint/production build/11 fixture-backed suites/screenshot exports), avoiding a duplicate local full run. Deliver draft PR and actual evidence for independent review; no merge yet.

## Production, rollback and next step

Production operations in this increment: none. Browser tests intercept API/external navigation and never submit a contact form or telephone action. Rollback is reverting/removing the bounded frontend commit if later integrated. No current implementation blocker; exact diff reviewed. Next is commit/push and draft PR with the full hosted gate, followed by independent review.
