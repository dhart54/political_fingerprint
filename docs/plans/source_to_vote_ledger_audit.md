# Source-to-vote-ledger audit

Outcome: detect missing factual member votes even when the roll-call row already
exists. Owner: ledger reconciliation lane, `codex/reconcile-vote-ledger`, starting
at `3cdc7840`. The interrupted worktree was clean.

Scope: a read-only audit over explicitly bounded House/Senate source captures and
ledger rows, keyed by chamber/Congress/session/roll/Bioguide. Preserve positions,
surface source/mapping gaps, retain compact per-roll deltas rather than another
full source or vote store. No production writes, refresh-writer changes, semantic
decisions, publication, migrations, push, or deployment.

Sequence: inspect existing adapters and refresh; implement raw-source comparison
and guarded database/offline reader; adversarial focused tests; inspect final
diff; independent review; bounded evidence replay where inputs permit.

Definition of done: missing rolls and partially populated rolls are separately
visible; same-number rolls cannot collide across sessions; unknown source data
cannot produce a clean report; no mutation path exists. Tests and independent
review establish the implementation, not production repair or full current
source coverage.

Validation: focused Python audit/refresh/adapter tests and diff checks. Report
real-input coverage and any access/freshness limitations separately.

## Verified result, November 11, 2026

The audit is implemented with no writer changes. The focused audit, refresh,
House adapter, and Senate adapter suite passes 66 tests. The first attempt had
19 fixture-setup errors because the ignored `.local/` parent directory was absent;
creating that directory resolved them. No product failure was suppressed.

A single read-only Green SELECT captured all rows for House 119/session 2,
rolls 223-314 at `2026-11-11T15:29:05.681607Z`. Export lengths were checked against
the same statement's counts: 24 rolls and 24 member votes. All 92 preserved
official XML captures were verified against their inventory hashes, including
an independently rechecked serialization-only variant for roll 247. All 92
published aggregate tallies match their parsed member rows.

Result: 39,821 source pairs, 24 matching stored pairs, 39,797 missing pairs.
There are 68 missing rolls and 24 partially populated existing rolls; 10,404
missing pairs belong to those existing rolls. Zero position conflicts,
ledger-only pairs, unresolved source rows, or unverified stored pairs.

Ignored local receipts: `.local/house92_ledger_20261111.json`,
`.local/house92_ledger_capture_20261111.json`,
`.local/house92_source_manifest_20261111.json`, and
`.local/house92_complete_audit_20261111.json`. The final audit SHA256 is
`2443d149d0372c71a130e9e44f32d0a61711f010e403476a945f6ed2812f6f30`.
The audit is about 1.15 MB of per-roll metadata and missing-pair deltas; no XML
was copied, no matched member-record store was added, and no data artifacts enter Git.

Independent review identified and verified the correction of one duplicate-LIS
identity defect, then replayed the complete 92-roll result with identical deltas.
The final direct-reader transaction guard additionally checks both read-only and
repeatable-read state and uses psycopg-compatible SET TRANSACTION.

Limits: this is a fresh database snapshot against preserved source captures,
not a live-source freshness census. Senate acquisition/mapping completeness was
not established. Direct psycopg database enforcement is unit-tested with a mock;
the actual production comparison used the existing connector and offline replay.
There were no production writes, refreshes, publication changes, pushes, merges,
or deployments. Missing-fact repair remains a separately bounded, approved
production operation, not an automatic consequence of this diagnostic.
