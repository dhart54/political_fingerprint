# Family Roll-Call Evidence Drilldown

Branch: `codex/family-roll-call-drilldown`

Base: `main` at `abd67c5e9d2f758025af2b296b03ac8fbf8ce051`

## Outcome

This milestone adds a House-only family-specific roll-call evidence drilldown to the `Record Across Congresses` panel.

The existing family card action now opens an inline drawer under the selected family card. The drawer shows the selected family header, separated `118th` and `119th` sections, roll/date, official vote, vote question, evidence summary, source link, count bucket, and whether each row is counted substantive evidence.

## Drilldown Pattern

Chosen pattern: inline expanded drawer under the selected family card.

Rationale: this is the smallest pattern consistent with the existing collapsed panel. It keeps users in the family context and avoids adding a route or modal state model.

## Data Source Path

1. Browser calls the app-local route:

   `/api/record-across-congresses/house/{legislatorId}`

2. The Next.js server route reads `INTERNAL_API_TOKEN` server-side and calls the guarded backend route.

3. The sanitized frontend response provides:

   - family metadata;
   - separated counts;
   - `roll_call_ids_considered_by_congress`.

4. When a family drawer opens, browser code calls the already-public issue evidence endpoint for that family issue domain:

   `/legislators/{legislatorId}/positions/{domain}/evidence?scope=all`

5. The drawer filters returned evidence rows to the selected family's exact `roll_call_ids_considered_by_congress`.

No new backend adapter, schema change, migration, evidence ingestion, production write, or classification change was needed.

## Token And Security Boundary

- `INTERNAL_API_TOKEN` remains server-side only.
- Browser code does not reference `INTERNAL_API_TOKEN`, `X-Internal-API-Token`, or the backend internal route.
- The browser only calls the app-local Record Across Congresses proxy and existing public issue evidence route.
- Raw backend errors are not surfaced by the proxy.

Validation:

```text
rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static
```

Result: no matches.

## Visible Copy

Visible panel and drilldown copy keeps the approved `Record Across Congresses` framing:

- `Record Across Congresses`
- `Closest family match`
- `Caveated family match`
- `Open the roll-call evidence used for this family.`
- approved not-voting caveat
- approved missing/no-record caveat
- approved no-inference explanation

Row summaries are selected from existing public evidence fields only when they do not contain the disallowed Record Across Congresses terms. Otherwise the drawer uses the neutral fallback: `Reviewed roll-call evidence row.`

## Profile Validation

Targeted backend profile fixtures passed through adapter/route tests:

| Profile | Expected state | Validation result |
| --- | --- | --- |
| Valerie P. Foushee | full display state with direct and caveated families | pass: `(true, 2, 1, 1)` |
| Aaron Bean | full display state | pass: `(true, 2, 1, 1)` |
| Abraham J. Hamadeh | unavailable/no display-eligible state | pass: `(false, 0, 0, 0)` |
| Aumua Amata Coleman Radewagen | one caveated family state | pass: `(true, 1, 0, 1)` |
| James Gallagher | no eligible family state | pass: `(false, 0, 0, 0)` |

Command:

```text
python -m pytest backend\tests\test_house_record_across_congresses.py backend\tests\test_house_record_across_congresses_transport.py backend\tests\test_internal_record_across_route.py
```

Result: 25 passed.

## Rendered Validation

Rendered validation used a local mock backend with the same proxy/token boundary:

- `INTERNAL_API_TOKEN=expected-token`
- `INTERNAL_BACKEND_API_BASE_URL=http://127.0.0.1:8000`
- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`

Checks:

- desktop default viewport: drawer opens from selected family card;
- mobile `390x844`: drawer opens from selected family card;
- family name, governing question, caveat render;
- `118th` and `119th` remain separate;
- only selected family roll calls render;
- source links render;
- no horizontal overflow.

Screenshot note: the in-app browser full-page screenshot capture produced distorted artifacts for this app shell, so no screenshot artifact is retained. The rendered validation above used DOM text checks, click interactions, and viewport overflow checks against the running app.

## No-Disallowed-Copy Validation

Targeted tests verify approved visible copy and drilldown summary fallback behavior. A source scan of touched frontend files only finds the disallowed terms inside the internal denylist used to suppress unsafe row-summary text:

```text
rg -n "changed|change|trend|shifted|movement|more supportive|less supportive|consistent|flip|ideological|evolved|moderated|became|continuity|moved toward|moved away from" frontend\components\RecordAcrossCongressesPanel.js frontend\lib\recordAcrossCongresses.mjs -i
```

Result: matches only in `DISALLOWED_COPY_TERMS`.

## Tests And Build

```text
node --test frontend\lib\recordAcrossCongresses.test.mjs
```

Result: 15 passed.

```text
npm run build
```

Result: passed.

```text
npm run lint
```

Result: blocked by the known interactive `next lint` migration prompt for Next 15. This was not treated as a feature failure.

## Remaining Limitations

- Rendered validation used a local mock backend rather than production data, because no production writes or secret/config changes were authorized.
- The drilldown currently fetches public issue-domain evidence and filters it locally. If future performance or payload size becomes a concern, a sanitized server-side detail proxy could be considered.

## Recommended Next Milestone

Add hosted preview validation against production-shaped data after the PR is opened, then consider whether a public-safe family roll-call detail adapter would reduce over-fetching without changing the token boundary.
