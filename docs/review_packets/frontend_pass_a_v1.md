# Frontend Pass A V1 Review Packet

## Review decision requested

Review the corrected representative journey on draft PR #121. This packet does
not request editorial approval, publication activation, production data writes,
manual deployment, merge, or ready-for-review status.

## Delivery identity and preview boundary

- PR: `dhart54/political_fingerprint#121`
- Branch: `codex/frontend-pass-a-representative-issue-foundation`
- Corrected runtime commit:
  `d49de4c07634675de7951c80ef94226df02e1dc5`
- Base: `13a51154c3c5dfce38ca717db1f3819b1fef9e23`

PR #121 changes backend and frontend contracts. Vercel deploys only the
frontend branch and has no matching branch backend, so its preview is a
frontend-shell check rather than authoritative end-to-end proof. The
authoritative product evidence is the matching commit on loopback, a disposable
PostgreSQL dataset, real Uvicorn, and real Chromium.

## Corrections under review

### Governed exact-action receipt projection

The Roll 32 contradiction came from two public surfaces reading different
layers: reviewed findings used the governed full-record interpretation while
the receipt rendered a stale raw `limited_context` row. The public catalog now
contains a closed projection for every governed action, bound to member, issue,
Congress scope, published artifact, canonical action ID, interpretation ID and
digest, vote sources, and action-meaning sources.

The selector requires agreement across all seven reviewed actions, the
published sample, source contract, display mappings, scope, and artifact
identity. Missing or conflicting state fails closed to receipts-only. The API
preserves the original database row under `raw_evidence`, exposes the governed
projection separately, and replaces only public display fields. React renders
that supplied projection and does not infer analytical meaning.

Roll 32 now identifies `house:119:1:32`, the overdose-reduction certification
amendment, `clerk_roll_032`, and `congress_hamdt5`; it no longer displays the
stale limited-context interpretation or an internal row number.

### Representative name search

Database and fallback search now share deterministic Unicode token matching.
Case, repeated whitespace, punctuation, apostrophes, hyphens, diacritics, and
intervening middle initials normalize consistently. Every query token must be
present, but token order is not significant, so `Valerie Foushee`,
`Valerie P. Foushee`, and `Foushee Valerie` resolve the same representative
without fuzzy guessing.

### Zero-match exact-action behavior

Finding controls still expose the linked count and open the first matching
receipt when one, two, or three actions resolve. If none resolve, the ledger
now remains on the full record, clears stale highlights and expansion, and
announces the fallback through an accessible status message. A normal filter
choice or Congress-scope change also clears stale exact-action state.

## Durable visual review package

The capture package is
`docs/review_packets/frontend_pass_a_v1/screenshots/`; its exact identities,
viewports, data boundary, command, and SHA-256 digests are recorded in
`docs/review_packets/frontend_pass_a_v1/manifest.json`.

The final capture used:

- frontend `http://127.0.0.1:3100`;
- matching branch backend `http://127.0.0.1:8000`;
- disposable loopback PostgreSQL only;
- seven governed Foushee receipts plus 69 explicitly unreviewed navigation
  receipts, for a deterministic 76-action ledger;
- no public fixture route and no production write.

Screenshot identities:

- `01-finder-full-name-results-1440.png`: ordinary full-name search;
- `02-selected-overview-recommended-1440.png`: selected header and reviewed
  Justice card;
- `03-visible-focus-issue-selection-1440.png`: visible keyboard focus;
- `04-justice-detail-ledger-1440.png`: reviewed analysis and full ledger;
- `05-exact-actions-focused-1440.png`: three matches and first receipt open;
- `06-corrected-roll-32-expanded-1440.png`: corrected governed Roll 32 receipt;
- `07-returned-to-complete-record-1440.png`: one-click return to all 76 actions;
- `08-filtered-ledger-1024.png`: tablet layout;
- `09-corrected-roll-32-expanded-390.png`: mobile governed receipt;
- `10-filtered-ledger-320.png`: narrow mobile layout;
- `11-effective-zoom-200.png`: 200% browser zoom;
- `12-zero-match-fallback-full-ledger-1440.png`: accessible zero-match fallback.

The capture asserts no horizontal overflow, no profile image, no deferred
tools, keyboard focus transfer, reduced-motion scrolling, accessible matched
counts, all three exact actions, automatic first-receipt expansion, and the
one-click return to the complete record.

## Environment-boundary note

During an earlier validation attempt, the local backend `.env` was discovered
to point to a remote Supabase pooler. Read-only requests had already occurred
before that was detected. Work stopped immediately; no write was made, and all
screenshots from that path were discarded. The final evidence in this packet
was rebuilt from a verified loopback-only disposable database. The manifest
distinguishes the final capture boundary from this validation incident.

## Validation evidence

- Deterministic public review-state catalog build/check: passed.
- Semantic validation pipeline: 7 checks passed.
- Focused backend/API validation: 178 passed; the final correction-focused
  rerun was 29 passed.
- Publication activation PostgreSQL suite: 23 passed.
- PostgreSQL row-contract and lifecycle validation: 58 passed.
- Fresh backup chain and authoritative owned-lifecycle real-Uvicorn proof for
  `d49de4c07634675de7951c80ef94226df02e1dc5`: passed, including exact
  activation, rollback, baseline restoration, Uvicorn stop, and Docker resource
  absence.
- Frontend unit tests: 110 passed.
- Frontend Pass A browser suite: 15 passed and 1 opt-in capture case skipped.
- Cutover browser suite: 3 passed; IR presentation suite: 4 passed.
- Final loopback live-data capture: 1 passed across 1440, 1024, 390, 320,
  keyboard focus, reduced motion, zero-match fallback, and 200% zoom.
- Lint: 0 errors and 8 unchanged warnings in deferred components.
- Production frontend build: passed.
- Repository parsing: 249 JSON and 2 YAML files passed.
- Final screenshot hashes, intended-file diff, and `git diff --check`: passed.

## Known review limitations

- The disposable navigation dataset deliberately labels its raw measure rows
  as disposable identities and reports zero substantive Yea/Nay receipts on the
  issue card. It exists to prove navigation and projection behavior; it is not
  a production-data content sample. The seven governed projections and their
  official identities remain exact.
- The selected journey and expanded receipt are long on 390px and 320px
  screens because the complete discovery and evidence hierarchy is preserved.
- The receipt uses a deliberately narrow desktop reading column.
- Full-page screenshots can catch the sticky section navigation at an
  intermediate document position; normal viewport scrolling keeps it at the
  top edge.
- The Vercel preview cannot prove representative search or governed receipts
  without the matching backend deployment.

## Reviewer checklist

- [ ] Full-name search resolves Valerie P. Foushee.
- [ ] Roll 32 shows the governed certification meaning and official identities.
- [ ] Findings expose exact-action counts and open the first matching receipt.
- [ ] Zero matches retain and announce the complete ledger.
- [ ] Returning to all actions remains one click away.
- [ ] Scope changes clear stale exact-action state.
- [ ] Keyboard, reduced-motion, mobile, and 200% zoom behavior remain usable.
- [ ] Required GitHub checks are green; Vercel is treated as a frontend shell.
