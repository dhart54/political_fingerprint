# Real Data Runbook

This is the fastest path to getting non-sample data into the frontend.

## Prerequisites

Set these backend environment variables:

- `DATABASE_URL`
- `CONGRESS_API_KEY`

The backend reads from precomputed Postgres tables, so the pipeline must write into your target database before the frontend can show real rows.

## Fastest Path

From the repo root:

```bash
cd backend
.venv/bin/python ../scripts/run_real_data_starter.py
```

Windows `cmd`:

```cmd
cd backend
python ..\scripts\run_real_data_starter.py
```

What the starter script does:

- fetches House member XML
- fetches House roll `362` from the official 2025 Clerk feed
- fetches Senate member XML
- fetches Senate roll `372` from the official 119th Congress, 1st Session Senate feed
- fetches Congress.gov bill metadata for:
  - `119:hr:498`
  - `119:hr:1`
- runs mixed House+Senate cache-backed ETL
- persists the merged results into Postgres

## Why These Starter Inputs

They are current official examples with stable public pages:

- House roll `362` on `H.R. 498` from the 2025 House Clerk vote index
- Senate roll `372` on `H.R. 1` from the 119th Congress, 1st Session Senate roll call list

## Verify

After the script finishes:

1. start the backend
2. start the frontend
3. load the page
4. confirm the API-backed panels reflect the newly seeded database rows

## Dry Run

To inspect the plan without downloading or writing data:

```bash
cd backend
.venv/bin/python ../scripts/run_real_data_starter.py --dry-run
```

## Optional Variants

House-only:

```bash
cd backend
.venv/bin/python ../scripts/run_real_data_starter.py --skip-senate
```

Senate-only:

```bash
cd backend
.venv/bin/python ../scripts/run_real_data_starter.py --skip-house
```

## Larger Curated Batch

To move beyond mostly zero-state profiles, use the expanded batch script. It pulls a wider set of House and Senate bill votes and infers the matching Congress.gov bill metadata directly from the downloaded roll XML.

From the repo root:

```bash
cd backend
.venv/bin/python ../scripts/run_real_data_expanded.py
```

Windows `cmd`:

```cmd
cd backend
python ..\scripts\run_real_data_expanded.py
```

Default expanded coverage:

- House 2025 rolls:
  - `347`
  - `349`
  - `351`
  - `356`
  - `358`
  - `360`
  - `362`
- Senate 119th Congress, 1st Session rolls:
  - `127`
  - `133`
  - `318`
  - `372`
  - `480`
  - `618`

Dry run:

```bash
cd backend
.venv/bin/python ../scripts/run_real_data_expanded.py --dry-run
```
