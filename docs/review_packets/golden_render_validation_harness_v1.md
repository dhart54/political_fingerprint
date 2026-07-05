# Golden Render Validation Harness V1 Review Packet

## Summary

This milestone adds a deterministic rendered validation path for the golden public-read surfaces introduced across PR #65 through PR #69.

The harness avoids ZIP lookup, external API calls, production smoke, and Vercel preview access by rendering fixture data through the real frontend profile, issue, receipt, and Record Across components.

## Route

- Path: `/golden-render-fixture`
- Gate: server-side `ENABLE_GOLDEN_RENDER_FIXTURE=1`
- Normal product UI does not link to the route.
- Without the env var, the route calls `notFound()`.

## Golden Cases

- Valerie-like profile:
  - National Security mostly opposed.
  - Economy mostly opposed.
  - Justice mostly opposed.
  - Immigration mixed.
- Limited one-sided profile:
  - National Security has 1 opposed / 0 supported interpreted Yes/No votes.
  - Economy has 2 supported / 0 opposed interpreted Yes/No votes.
  - Both remain limited and avoid mostly-supported/opposed framing.
- Unsafe raw text fixture:
  - Raw strings such as `this was a direct vote`, `records a direct position`, `the House voted on whether`, `Amendment No.`, `source basis`, and `classification reason` are present in receipt/detail fields.
  - Top-level profile/card/issue-read copy is asserted not to expose those strings.

## Rendered Coverage

`npm run test:golden-render` starts the local Next app with the fixture env var enabled and runs Playwright against Chromium.

The rendered checks cover:

- profile summary;
- profile issue cards;
- National Security expanded read;
- Economy expanded read;
- Justice expanded read;
- mixed Immigration read;
- limited one-sided profile/card/read behavior;
- representative vote rows;
- full reviewed vote list opening;
- source/caveat/details drawer opening;
- nested details/source-basis receipt disclosure;
- Record Across Congresses panel rendering and opening;
- desktop horizontal overflow;
- `390x844` mobile horizontal overflow;
- visible internal token/header/internal-route text.

## Safety Boundary

The rendered test scopes unsafe-phrase assertions to top-level public copy before the `Representative votes` receipt section. It then intentionally opens receipt/detail surfaces and verifies raw receipt text can remain inspectable there.

This preserves the PR #65 public-copy safety contract while confirming receipt surfaces still work.

## How To Run

From `frontend`:

```text
npm run test:golden-render
```

The Playwright config starts:

```text
npm run dev -- --hostname 127.0.0.1 --port 3100
```

with:

```text
ENABLE_GOLDEN_RENDER_FIXTURE=1
```

The existing validation suite remains:

```text
node --test lib\*.test.mjs
npm run lint
npm run build
rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static
```

## Limitations

- The harness validates deterministic golden fixtures; it does not replace production smoke for deployment wiring or real-data regressions.
- Playwright browser binaries must be available in the environment. In this branch, `@playwright/test` and Chromium setup were verified locally.
- The route is intentionally test-only and unavailable unless the fixture env var is set.
