# Source-to-ledger vote audit

This diagnostic compares raw House Clerk or Senate XML to the fact ledger by
chamber, Congress, session, roll number, and Bioguide ID. It detects missing
rolls, missing member pairs on already populated rolls, position conflicts, and
ledger-only pairs. Existing refresh planning skips an entire existing roll and
therefore cannot establish member-pair completeness. This audit does not change
that writer or authorize repair.

Run from `backend` with an explicitly bounded range (at most 2,000 rolls):

```powershell
python -m app.etl.vote_ledger_audit --chamber house --congress 119 --session 2 --first-roll 1 --last-roll 92 --source-dir C:\path\to\house\2026 --database --output ..\.local\house-audit.json
```

Use an already authorized database connection via `DATABASE_URL`. The reader
uses one repeatable-read, read-only transaction, 30-second statement timeout,
3-second lock timeout, and rollback/close on success or failure. It selects only
`roll_calls`, `votes_cast`, and legislator identity. It does not commit, import,
classify, interpret, create credentials, or change the database/schema.

For deterministic offline replay, replace `--database` with `--ledger-json PATH`.
The JSON must contain `scope` with chamber/congress/session/first_roll/last_roll,
`captured_at`, `rolls` as four-element keys, and `votes` as objects containing
`roll_key`, `bioguide_id`, and canonical `position`. It must describe the complete
ledger snapshot for that range; do not pass a paginated or truncated export.
The tool validates scope, duplicates, positions, and member identities, but cannot
prove an external export is complete. A database run obtains its own snapshot.

Sources use the existing cache names `rollNNN.xml` and `vote_NNN.xml`. Supply
`--senate-member-file PATH` to resolve Senate LIS IDs from an explicit official
member mapping; unresolved former/current members remain unresolved. No names,
current-seat guesses, fixture fallback, or automatic network fetching is used.
Missing, malformed, wrong-session, empty, duplicate-member, unknown-position,
or unresolved-identity inputs prevent a clean result. Rolls without a supported
bill reference are still audited. Present and Not Voting remain distinct.
Published aggregate vote totals, when present, must match the parsed positions.
Missing aggregate totals are recorded as null rather than synthesized.

For scattered or renamed captures, use `--source-manifest PATH` instead of
`--source-dir`. The manifest contains the exact same `scope` object and a `files`
array of objects with `roll_key`, `file`, and lowercase `sha256`. Relative file
paths resolve beside the manifest. Each roll may have only one explicit capture;
bytes and XML identity are verified before comparison. Missing entries stay
uncompared. This reuses existing files without copying XML to another cache.

Output is exclusive-created JSON with source hashes, capture time, compact
per-roll deltas, counts, and explicit limitations. It does not duplicate matched
member records or copy source XML. Keep operational reports under ignored
`.local/` or an existing external evidence directory, not in Git or the database.
Exit codes: `0` exact match within supplied scope, `1` differences, `2` incomplete
source coverage. A cached-source result does not claim current official coverage,
source freshness, legislative eligibility, service status, or editorial readiness.

Validation:

```powershell
python -m pytest backend/tests/test_vote_ledger_audit.py backend/tests/test_current_congress_refresh.py
git diff --check
```
