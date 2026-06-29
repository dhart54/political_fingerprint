# Record Across Congresses Frontend Prototype

Branch: `codex/record-across-congresses-frontend-prototype`  
Base: `main` at `8f99ee7ce63424550228c308e57b2573c160e47a`

## Summary

This milestone adds the first guarded frontend prototype for the House `Record Across Congresses` panel. The panel renders factual reviewed House family-evidence availability and separated counts from the already guarded backend response. It remains collapsed, secondary to the strongest issue evidence path, and does not make interpretive cross-Congress claims.

## Frontend Placement

The panel is mounted on the profile page after:

1. `ProfileQuickRead`
2. `PositionByIssue` with the current strongest issue evidence title

It is not part of the scope controls and is not the primary profile answer.

Runtime House guard:

- The panel renders only when `legislator.chamber` is `house`.
- It returns `null` for Senate or non-House profiles.

## Server-Side Token Boundary

Chosen pattern: Next.js server route proxy.

Browser path:

```text
/api/record-across-congresses/house/{legislatorId}
```

Server-to-backend path:

```text
/internal/record-across-congresses/house/{legislatorId}
```

The browser calls only the app-local frontend route. The server route reads `INTERNAL_API_TOKEN` server-side and sends it as `X-Internal-API-Token` to the backend internal route. The browser/client component and `frontend/lib/api.js` do not reference `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, or the backend internal route.

The proxy fails closed when `INTERNAL_API_TOKEN` is missing or blank, returning a sanitized `503` body:

```json
{"detail":"Record unavailable"}
```

Backend non-OK responses are mapped to sanitized `404` or `502` responses. Raw backend errors and internal metadata are not returned to the browser.

## Sanitized Response

The proxy returns only fields needed by the UI:

- `product_framing`
- `legislator_identifier`
- `supported_congresses`
- safe legislator display fields
- display summary counts
- eligible family fields
- separated 118th/119th count buckets
- caveats
- roll-call ids considered by Congress

It strips raw `non_authorization_metadata` and refuses to return data if `product_framing` is not exactly `Record Across Congresses`.

## Visible Copy

The panel uses approved copy from `record_across_congresses_frontend_copy_guardrails.json`:

- `Record Across Congresses`
- `Reviewed House vote evidence exists in both the 118th and 119th Congresses for these policy-question families.`
- `Closest family match`
- `Caveated family match`
- approved sparse-state copy
- not-voting and missing/no-record caveats
- related-row exclusion note
- no-inference explanation
- evidence drilldown prompt

Additional short labels are limited to factual UI labels such as `118th`, `119th`, count bucket names, and availability count headings.

## Sparse States

Covered sparse states:

- no eligible family
- 118th-only evidence
- 119th-only evidence

Sparse states use approved copy and keep missing/no-record separately explained.

## Validation Profiles

Component-level fixtures cover the required profile states:

| Profile | Covered state |
|---|---|
| Valerie Foushee | full display state |
| Aaron Bean | rendered full display state via local mock |
| Adam Smith | full display state |
| Abraham J. Hamadeh | 119th-only / no display-eligible state |
| Allred | 118th-only / no display-eligible state |
| Aumua Amata Coleman Radewagen | caveated-family state |
| James Gallagher | no eligible family state |

Live production token access was not used in frontend tests. Local rendered validation used a mock backend that required the same `X-Internal-API-Token` header and returned production-shaped data through the actual Next.js proxy.

## Rendered Validation

Rendered validation was run locally at:

```text
http://127.0.0.1:3010
```

Setup:

- mock backend on `127.0.0.1:8765`
- `INTERNAL_API_TOKEN=expected-token`
- `INTERNAL_BACKEND_API_BASE_URL=http://127.0.0.1:8765`
- actual Next.js route proxy exercised

Results:

- collapsed panel present exactly once
- collapsed by default
- expanded desktop viewport `1366x900`: both family labels present, 118th and 119th count buckets present, no horizontal overflow
- mobile viewport `390x844`: panel present, collapsed, both family labels and count buckets present in component DOM, no horizontal overflow
- no disallowed wording found in the expanded panel text
- no token/header text found in the expanded panel text

Note: the broader page depends on public backend API calls that were not mocked for this frontend-only rendered pass, so surrounding profile sections showed existing unavailable states. The `Record Across Congresses` proxy and panel still rendered through the mocked internal route.

## No-Disallowed-Copy Validation

Targeted tests assert approved visible panel copy does not include disallowed terms from the guardrail artifact. Browser DOM validation also found no disallowed terms in the expanded panel text.

## No-Token-To-Browser Validation

Validation performed:

```text
rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static
```

Result: no matches.

Source tests also assert:

- the route handler is the only new frontend source file that reads `INTERNAL_API_TOKEN`;
- client API code calls `/api/record-across-congresses/house/...`;
- client API/component source does not reference the backend internal route or internal token.

## Tests And Build

Passed:

```text
node --test lib\recordAcrossCongresses.test.mjs
```

Result: `10` tests passed.

Passed:

```text
node --test lib\*.test.mjs
```

Result: `50` tests passed.

Passed:

```text
npm run build
```

Result: Next.js build compiled successfully and included the dynamic proxy route.

Attempted:

```text
npm run lint
```

Result: Next 15 `next lint` opened the interactive ESLint migration prompt and exited instead of running a configured linter. This is a local tooling limitation; build and targeted tests passed.

## Remaining Limitations

- The evidence drilldown button reuses the existing issue-domain evidence path rather than a roll-call-id-specific drilldown route, because no existing safe roll-call-family frontend path exists yet.
- Live production-rendered validation with real internal token access was not performed from frontend tests.
- The broader profile page still needs its normal public backend to avoid unrelated unavailable states during local rendering.

## Next Recommended Milestone

Add a dedicated evidence drilldown path for a comparable family's roll-call ids, still preserving amendment/final-passage/procedural/not-voting distinctions and still avoiding cross-Congress interpretation.
