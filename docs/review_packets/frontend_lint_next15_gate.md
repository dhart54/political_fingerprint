# Frontend Lint Next 15 Gate Review Packet

## Intent

Restore `frontend` `npm run lint` as a non-interactive, repeatable validation gate for local and CI use.

## Previous Problem

- `frontend/package.json` used `next lint`.
- Under Next 15, `next lint` opened the interactive ESLint migration/setup prompt instead of running configured linting.
- Recent review packets treated lint as a tooling limitation because the command was not suitable for automated validation.

## Chosen Command

```text
npm run lint
```

now runs:

```text
eslint .
```

This uses the ESLint CLI directly, exits non-zero for lint errors, and does not invoke the deprecated/interstitial Next lint migration flow.

## Config Changes

- Added explicit frontend dev dependencies:
  - `eslint`
  - `eslint-config-next`
- Added `frontend/eslint.config.mjs`.
- The config uses ESLint flat config with `FlatCompat` to load Next 15's `next/core-web-vitals` rules.
- Ignored generated/runtime directories: `.next/**`, `node_modules/**`, and `out/**`.

## Product-Code Fix

- Escaped one JSX apostrophe in `frontend/components/FingerprintRadar.js` to satisfy `react/no-unescaped-entities`.
- No product semantics, UI structure, evidence handling, schema, backend, or production data changed.

## Validation Results

Run from `frontend`:

```text
npm run lint
```

Result: passed, exit `0`. The command ran non-interactively as `eslint .`. It reports 8 existing `react-hooks/exhaustive-deps` warnings and 0 errors.

```text
npm run build
```

Result: passed. Next build completed successfully and repeated the same 8 hook dependency warnings.

```text
node --test lib\*.test.mjs
```

Result: passed, 55/55 tests. Node emitted the existing `MODULE_TYPELESS_PACKAGE_JSON` warning for ESM files in a package without `"type": "module"`.

```text
rg -n "INTERNAL_API_TOKEN|X-Internal-API-Token|/internal/record-across-congresses" .next\static
```

Result: clean. No matches in `.next\static`; `rg` exited `1` because no matches were found.

## Remaining Limitations

- ESLint now exposes 8 existing hook dependency warnings. They do not fail the gate and were not changed because resolving them may require behavior-sensitive component effect changes.
- `npm install`/package metadata audit reports 2 existing dependency vulnerabilities, 1 moderate and 1 high. Dependency remediation is outside this frontend lint-gate milestone.
- Targeted Node tests still emit the pre-existing module type warning; tests pass.

## Production Writes

None. No deployment required for this milestone.
