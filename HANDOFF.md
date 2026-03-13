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

Most recent commits:

- `0db98bd` `Add psycopg-binary for hosted Postgres connectivity`
- `3ad7746` `Support live House and Senate source formats`
- `ce7bf65` `Add expanded real-data batch importer`

## Live Data / Database State

Database target:

- Supabase Postgres via pooler `DATABASE_URL` in `backend/.env`

Verified:

- backend can connect to Supabase
- initial schema from `backend/migrations/0001_initial_schema.sql` has been applied

Real-data imports completed:

1. Starter batch
   - 1 House roll
   - 1 Senate roll

2. Expanded batch
   - House 2025 rolls: `347`, `349`, `351`, `356`, `358`, `360`, `362`
   - Senate 119th Congress, 1st Session rolls: `127`, `133`, `318`, `372`, `480`, `618`

Latest persisted Supabase row counts after expanded batch:

- `legislators`: `540`
- `bills`: `13`
- `roll_calls`: `13`
- `votes_cast`: `3631`
- `vote_classifications`: `13`
- `fingerprints`: `4320`
- `chamber_medians`: `48`
- `drift_scores`: `540`
- `summaries`: `540`
- `zip_district_map`: `4`

Coverage reality check:

- `533` legislators have at least one eligible vote
- `0` legislators have `5+` eligible votes
- current max `total_votes` per legislator is `3`

Implication:

- the frontend is now reading real legislator roster data and real computed rows from Supabase
- but the imported vote set is still too small for rich, informative fingerprints for most legislators

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

- `backend/.venv/bin/pytest tests/test_live_pipeline.py` -> `7 passed`
- expanded real-data script dry run works
- expanded real-data batch ran successfully into Supabase

## Next Recommended Task

Next highest-value work is not UI polish.

It is a larger bulk real-data import strategy so the frontend becomes genuinely informative.

Recommended next step:

1. build a range-based or curated bulk import path for many more substantive House and Senate bill votes
2. bias imports toward bill-passage / amendment votes that are more likely to survive procedural exclusion
3. rerun ETL into Supabase
4. verify that many legislators now have meaningful non-zero fingerprints and less-empty summaries

## Fast Resume Prompt

Use this tomorrow:

“Read `HANDOFF.md` plus the repo instruction files, then continue from the bulk real-data import step.”
