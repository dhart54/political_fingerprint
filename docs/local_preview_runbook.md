# Local Preview Runbook

Use this when the frontend is open at `http://localhost:3000/` but the app cannot load ZIP lookup, search, or Valerie Foushee evidence.

## Windows Startup Path

The checked-in `backend/.venv` is Linux-style and is not usable as a Windows Python environment. Do not spend time trying to run it on Windows.

Use the Windows venv:

```powershell
cd "C:\Users\Dylan\Documents\Data Science\political_fingerprint\backend"
.\.venv_win\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Do **not** use `--reload` in this local Codex/Windows preview workflow. Uvicorn reload can fail with Windows multiprocessing/named-pipe permission errors such as `WinError 5 Access is denied`.

In another terminal, start the frontend:

```powershell
cd "C:\Users\Dylan\Documents\Data Science\political_fingerprint\frontend"
npm run dev
```

Then open:

```text
http://localhost:3000
```

## Quick Checks

```powershell
netstat -ano | Select-String ':8000|:3000'
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
```

Expected:

- backend listening on `127.0.0.1:8000`
- frontend listening on `localhost:3000`
- ZIP `27701` should load Valerie P. Foushee
- search `fou` should find Valerie P. Foushee

## Failure Discipline

If either server fails to start, stop and report the exact failing command and error. Do not keep trying alternate launch paths or browser workarounds without first telling the user what is blocked.
