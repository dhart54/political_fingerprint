# Golden Profile Read V1 Review Packet

## Intent

This focused PR improves profile-level record summary and issue-card preview copy so the landing read better matches the expanded issue reads introduced in PR #68.

## Checkpoint Findings

| Surface | Current Copy Shape | Working | Weak / Disconnected | Target |
| --- | --- | --- | --- | --- |
| Profile record summary | Strongest evidence headline, party-context opening, strongest issue line, mixed issue line, Congress-count note | Uses reviewed-sample framing; avoids ideology/motive/recommendation claims; names strongest and mixed issue | Leads with methodology; does not point clearly to issue cards and receipts; does not summarize multiple dominant issue areas | Lead with reviewed-sample issue pattern, separate mixed/limited reads, and point to issue cards and representative votes |
| Profile issue cards | Domain, `Mostly opposed - for / against`, static theme list | Compact and safe; counts are present | Count order differs from expanded issue read; no receipt CTA; themes are static previews only | Use status, opposed/supported counts, compact safe theme preview, and receipt CTA |
| National Security card vs read | Card says mostly opposed and `22 for / 128 against`; expanded read says `128 opposed and 22 supported` with opposition concentration | Status and counts agree when translated; top-level raw safety holds | Card does not preview opposition-concentrated pattern; count order mismatch | `Mostly opposed`, `128 opposed / 22 supported`, safe compact national-security themes |
| Economy card vs read | Card says mostly opposed and `3 for / 59 against`; expanded read says `59 opposed and 3 supported` | Correct dominant state; safe themes | Count order mismatch; no policy-first preview | `59 opposed / 3 supported`, compact fiscal theme preview |
| Justice card vs read | Card says mostly opposed and `7 for / 51 against`; expanded read says `51 opposed and 7 supported` | Production Justice is correctly dominant | Same count mismatch; preview does not bridge to expanded read | `51 opposed / 7 supported`, compact public-safety theme preview |
| Mixed Immigration card/read | Card says mixed, but not counts; expanded read says `8 opposed and 5 supported` and avoids mostly framing | Mixed stays mixed | Card lacks counts and expanded-read caution | `8 opposed / 5 supported`, votes point in more than one direction, inspect receipts first |

## Implementation

- Added `buildIssueCardPreview` in `frontend/lib/profileNarrative.mjs`.
- Updated profile narrative body to lead with reviewed-sample issue patterns and point to issue cards and representative vote receipts.
- Updated profile summary cards to use preview status, counts, and theme copy.
- Updated issue evidence cards to use the same preview helper for status, count line, theme line, and receipt line.
- Preserved expanded issue overview composition from PR #68.

## Safety Boundary

- Profile and issue-card preview copy uses aggregate issue rows, readiness, counts, domain labels, and safe static domain themes.
- It does not use vote descriptions, questions, summaries, uncertainty notes, interpretation reasons, classification reasons, source basis, or raw audit text.
- Raw vote text remains in receipt/detail/full-list surfaces only.

## Before / After Examples

Before:

> Valerie P. Foushee's strongest reviewed evidence is in National Security & Foreign Policy.

After:

> Valerie P. Foushee's clearest reviewed issue read is National Security & Foreign Policy.

Before:

> National Security & Foreign Policy / Mostly opposed - 22 for / 128 against

After:

> Mostly opposed in reviewed sample / 128 opposed / 22 supported across 150 reviewed Yes/No votes.

Before:

> Reviewed votes point in more than one direction. Useful comparison read.

After:

> 8 opposed / 5 supported across 13 reviewed Yes/No votes. Votes point in more than one direction...

## Tests Added Or Updated

- Profile narrative tests now assert reviewed-sample framing, issue-card/receipt guidance, no ideology/motive/recommendation language, and raw-field safety.
- Added direct `buildIssueCardPreview` tests for National Security, Economy, Justice, and mixed Immigration-style rows.
- Updated component source tests to assert the shared preview helper and receipt-oriented preview fields.
- Preserved PR #65-#68 public-copy and issue-overview safety tests.

## Validation

- `node --test lib\profileNarrative.test.mjs lib\issueOverview.test.mjs` passed: 26 tests.
- `node --test lib\*.test.mjs` passed: 71 tests.
- `npm run lint` passed with 8 existing React hook dependency warnings.
- `npm run build` passed with the same existing warnings.
- `rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static` returned no matches.

## Rendered Validation

- Local built app shell at `http://localhost:3000` rendered.
- Desktop shell: no horizontal overflow; no visible internal token/header/internal-route text.
- Mobile `390x844`: no horizontal overflow; no visible internal token/header/internal-route text.
- Limitation: local ZIP/data path did not load Valerie Foushee for ZIP `27701`; the local app showed the sample profile and unavailable quick read. Valerie-specific rendered validation should be repeated on hosted preview/production after deployment.

## Limitations

- Issue-card theme previews are compact safe domain-theme previews from aggregate issue rows; they intentionally do not recompute the full expanded issue overview group list because vote-level evidence rows are not present in the collapsed card data.
- This PR does not change support/opposition/readiness semantics, backend data, schema, issue overview composition, or receipt surfaces.
