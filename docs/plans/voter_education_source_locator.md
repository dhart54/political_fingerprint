# Education source locator preparation

Fifth bounded voter reliability increment. Isolated `.w/vl`, branch
`codex/education-record-source-locator`, verified main `f494324`. Follow repository
AGENTS, interpretation principles, and editorial standardization workflow.
No overlapping edits to PR193 or prior reliability PR heads.

## Authorized outcome

Prepare the existing Education roll 79 source locator using its governed catalog.
The current generated `/app/details/CREC-2025-03-25-pt1-PgH1241` locator fails;
the governed same-source HTML locator is
`https://www.govinfo.gov/content/pkg/CREC-2025-03-25/html/CREC-2025-03-25-pt1-PgH1241.htm`.
Source ID: `govinfo:CREC-2025-03-25-pt1-PgH1241:amendment-3`.
SHA256: `eaafafb53de434c894f475a864a1cd951118a32f2f98e1e487109f7ef71f5b32`.
The current downloaded HTML and governed cached bytes independently match that SHA.

This is inert preparation only. An optional catalog argument prepares row 79's
two existing URL fields. Default compiler behavior, other 16 rows, all accepted
wording, source identities, versions, hashes, frozen output bytes and publication
registries remain unchanged. Missing, duplicate, conflicting identity/hash/type,
or non-content locators fail closed. No new raw bytes are published.

## Validation and integration gate

- [x] Exact current HTML URL and governed-byte identity verified read-only.
- [x] Tests compare all 17 default rows with frozen receipt projections.
- [x] Opt-in projection differs only in the two exact row 79 URL fields.
- [x] Inputs and frozen artifact bytes remain unchanged.
- [x] Conflicting/missing identity and invalid locator tests fail closed.
- [x] Existing candidate generator `--check` passes without artifact edits.
- [ ] Draft PR and hosted exact-head backend checks.

The Windows local acceptance harness compares CRLF checkout bytes with LF Git
blobs and fails its existing reviewed-byte assertions (8 acceptance tests), while
the integration module passes. Do not normalize or rewrite frozen artifacts or
weaken the acceptance gate. Hosted Linux exact-head validation must pass before
integration; prior PRs on this same base passed that gate.

## Resume and boundaries

Serving URLs are deliberately still unchanged. An explicit authorized published
artifact/URL revision is required to activate the prepared locator and revise its
bindings. Code revert is rollback; no production writes, promotion, approval,
merge, manual deployment, source substitution, or credentials changes.
Parent owns reviewed integration. PR203-206 all passed exact-head hosted checks.
Next `.w/vi` prepares a neutral notice for fault-injected partial receipt responses.
Parent messaging returned thread not found; keep readable state instead of retrying.
