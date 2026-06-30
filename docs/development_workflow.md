# Development Workflow

This repo has two local verification modes. Use fixture mode for product and API behavior. Use Supabase mode only when validating migrations, persistence, ETL writes, or real-data reads.

Before changing product copy, summaries, evidence language, UI interpretation, Record Across Congresses copy, party-context language, caveat/limit placement, finding-card language, or methodology-adjacent user-facing copy, read `docs/interpretation_principles.md`.

## Fixture Mode

Fixture mode is the default low-cost development loop. It is deterministic and does not require a working database connection.

Backend focused tests:

```powershell
cd backend
$env:DATABASE_URL='postgresql://invalid'
pytest --basetemp=..\.local\pytest_basetemp tests\test_api_alignment.py tests\test_api_compare.py
```

Backend full tests:

```powershell
cd backend
$env:DATABASE_URL='postgresql://invalid'
pytest --basetemp=..\.local\pytest_basetemp
```

Use `--basetemp=..\.local\pytest_basetemp` on Windows so pytest writes temporary files inside the repo workspace instead of `AppData\Local\Temp`, which can be permission-blocked in this environment. `.local/` and `backend/.pytest_tmp/` are ignored by Git.

In Codex desktop, tests that use pytest `tmp_path` may still need approval to run outside the sandbox. If the suite fails with `PermissionError` while creating or cleaning the basetemp directory, rerun the same command with elevated execution.

Frontend build:

```powershell
cd frontend
npm run build
```

Local servers:

```powershell
cd backend
uvicorn app.main:app --reload
```

```powershell
cd frontend
npm run dev
```

Use fixture ZIPs `27701` and `27601` for local UI checks until broader ZIP coverage is added.

## Supabase Mode

Use Supabase mode when checking real stored rows or ETL persistence. This requires `backend\.env` to contain a valid `DATABASE_URL`.

Backend API tests against Supabase-backed reads:

```powershell
cd backend
pytest tests\test_api_fingerprint.py tests\test_api_positions.py tests\test_api_alignment.py tests\test_api_compare.py
```

Persist fixture-derived computed rows into the configured database:

```powershell
cd backend
python -m app.etl.run_all --fixtures
```

Run compute without writing:

```powershell
cd backend
python -m app.etl.run_all --fixtures --compute-only
```

Do not use Supabase mode for routine UI copy, layout, or deterministic alignment behavior unless the change specifically depends on database state.

## Windows Next.js Cache Reset

If the browser shows stale Next.js chunks or an error such as `__webpack_modules__[moduleId] is not a function`, stop the dev server, remove `.next`, and restart.

Avoid running `npm run build` while `npm run dev` is still active. On Windows, building over an active dev server can leave the browser attached to stale Webpack chunks. If that happens, use this reset workflow before continuing browser QA.

Find the process:

```powershell
netstat -ano | findstr :3000
```

Stop it:

```powershell
Stop-Process -Id <PID> -Force
```

Clear the cache:

```powershell
Remove-Item -LiteralPath frontend\.next -Recurse -Force
```

Restart the frontend:

```powershell
cd frontend
npm run dev
```
