# Actual M15B replacement preparation

Merged PR #186: `5843bab9b1bed3e5db57976bae3b05466f2cbafe`, accepted
head `e223bbf676c1762337c03bc3af0e78801c14f698` on the exact reviewed base.
All accepted-head checks passed. Documented Render hook/Uvicorn and Vercel
build integrations are code-only; no manual deployment is requested.

Outcome: one reviewable persistence-authorization package for the actual NS
and Justice content. Production writes, activation, migration, rollback and
merging the preparation PR remain unauthorized.

Sequence: capture fresh read-only exact production baseline; form two bounded
immutable graphs using existing persistence; prove actual payload lifecycle in
the existing disposable PostgreSQL infrastructure; run release checks; present
one draft PR with commands, counts, recovery and unavailable activation inputs.

Scope: preserve accepted payloads and historical files, raw data and protected
untracked ZIP. No semantic generation or new publication framework. Tests use
only explicit loopback credentials, never production environment inheritance.

Validation: persistence counts/content/idempotency; exact independent registry
updates and rollback; real API/selector output in 119/all; additional unreviewed
ledger rows and controls; authority/identity/provenance/ownership failures;
injected transaction failure; other-table fingerprints; historical/release CI.

Expected footprint: bounded package/operator, persistence parameters if needed,
read-only capture, actual payload test, existing CI lane, plan/review packet/data.
New production IDs and sealed activation authority remain unresolved by design.
