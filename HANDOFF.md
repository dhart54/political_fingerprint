# Handoff

## Current Status

The original MVP plan in `TASKS.md` is complete.

Phase 2 / post-MVP work completed through:

- legislator search API and picker
- database-first API read layer
- deterministic DB seeding
- persistent ETL writes
- DB-centered summary caching
- official-style House and Senate sample adapters
- official source fetch layer
- cache-backed live pipeline
- mixed House + Senate live ETL support
- provenance and summary UX improvements
- comparison API and UI
- starter and expanded real-data import scripts
- bulk real-data import tooling and persistence optimization
- successful large House + Senate real-data backfill into Supabase
- major frontend framing, density, and interpretability passes

Most recent commits:

- `32f5c69` `Add vote-direction context to comparison`
- `1c11533` `Promote position by issue as primary read`
- `638ceeb` `Connect ZIP lookup to profile flow`
- `185568e` `Feature ZIP lookup as primary entry path`
- `3cdcffc` `Seed comparison from ZIP lookup`
- `b98ec54` `Prioritize vote-direction comparison flow`
- `2e8907d` `Add plain-language position labels`

## Live Data / Database State

Database target:

- Supabase Postgres via pooler `DATABASE_URL` in `backend/.env`

Verified:

- backend can connect to Supabase
- initial schema from `backend/migrations/0001_initial_schema.sql` has been applied

Real-data imports completed:

1. Starter batch
2. Expanded batch
3. Controlled bulk backfill
4. Full cached House + Senate bulk persist using Postgres `COPY`

Latest persisted Supabase row counts after the successful full bulk backfill:

- `legislators`: `548`
- `bills`: `234`
- `roll_calls`: `419`
- `votes_cast`: `154767`
- `vote_classifications`: `419`
- `fingerprints`: `4384`
- `chamber_medians`: `48`
- `drift_scores`: `548`
- `summaries`: `548`
- `zip_district_map`: `4`

Coverage reality check:

- `fingerprints_ge_5`: `4352`
- `fingerprints_ge_20`: `3456`
- `fingerprints_max_total_votes`: `58`

Implication:

- the frontend is now reading a substantial real legislator roster and meaningful computed rows from Supabase
- House members now have materially useful issue-focus, vote-direction, and drift signals
- comparison is now more useful because it includes deterministic per-domain yea/nay context

## Important Runtime Notes

Local app setup:

- frontend site runs on `http://127.0.0.1:3000`
- backend API runs on `http://127.0.0.1:8000`

Important Windows runtime lesson from this session:

- do not leave multiple uvicorn processes bound to port `8000`
- if requests hang, check `netstat -ano | findstr :8000`
- safest local backend startup command:

```cmd
cd C:\Users\Dylan\Documents\Data Science\political_fingerprint\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend restart if stale:

```cmd
cd C:\Users\Dylan\Documents\Data Science\political_fingerprint\frontend
rmdir /s /q .next
npm run dev
```

## Important Repo Instructions

On resume, re-read:

- `AGENTS.md`
- `DECISIONS.md`
- `SKILLS.md`
- `CONSTRAINTS.md`
- `TASKS.md`
- `FIXTURES.md`
- this `HANDOFF.md`

Continue following repo instructions strictly.

## Key Decisions Still In Effect

Fixture decision from earlier work remains locked:

- prioritize `10` policy roll calls in fixtures

Do not silently change fixture assumptions later without user approval.

## Current Verification State

Most recent validations completed:

- `npm run build` in `frontend` passes after the latest interpretability/layout work
- live bulk data now persists successfully into Supabase
- local UI was verified against real data, including:
  - meaningful fingerprint outputs
  - meaningful drift outputs for many House members
  - real legislator search results

## Product Reality Check

The current site is now much closer to the actual voter use case:

- `Position by Issue` is now the primary signal
- comparison now uses vote-direction context within issue domains
- issue focus and change-over-time are now supporting context rather than the headline read

Important interpretation boundary still in effect:

- issue focus shows what topics absorbed attention
- vote direction shows how the legislator tended to vote inside those topics
- drift only measures change in issue-attention mix over time, not ideological consistency or belief change

## Next Recommended Task

Next highest-value work is to deepen the now-corrected voter workflow:

1. make ZIP lookup seed comparison more aggressively
2. let a user compare their House member against each senator with one click
3. keep pushing the product center toward `Position by Issue`, with radar/drift clearly secondary

Best next implementation target:

- tighten the comparison and ZIP-to-profile journey even more, or
- improve the single-legislator `Position by Issue` section with richer domain-level interpretation

## Fast Resume Prompt

Use this tomorrow:

“Read `HANDOFF.md` plus the repo instruction files, then continue from the ZIP-to-comparison / position-by-issue improvement step.”
