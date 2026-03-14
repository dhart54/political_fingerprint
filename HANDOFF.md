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

- `95972fa` `Lead with plain-English takeaways`
- `913bd3c` `Reorganize issue focus layout`
- `ce5a7d2` `Optimize desktop layout for large monitors`

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
- House members now have materially useful issue-focus and drift signals
- comparison still feels weaker than users expect because it compares issue focus, not vote direction within issue

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

The current site is now credible and much more understandable, but one important limitation remains:

- casual users can still expect comparison to show political difference more strongly than it currently can
- the current fingerprint and comparison logic measure issue focus, not vote direction within issue

This means two legislators can legitimately look similar if they voted on the same kinds of issues, even if they took different sides on some of those votes.

## Next Recommended Task

Next highest-value work is a product feature, not more generic polish:

1. add a vote-direction or position layer within issue domains for comparison
2. keep it deterministic and descriptive
3. make comparison answer not just “what issues dominated” but also “did they tend to take different sides on those issues?”

This is the clearest next step to make the product more useful for casual voters.

## Fast Resume Prompt

Use this tomorrow:

“Read `HANDOFF.md` plus the repo instruction files, then continue from the vote-direction / comparison-improvement step.”
