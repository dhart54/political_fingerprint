# Education79 adapter and disposable release proof

This follow-up leaves PR210 head `c651519ecd944382cd432cbc59678490e1a7902d`
unchanged. It has no production operator, connection, persistence or activation
entry point. A standalone hosted fixture job uses one dedicated empty loopback
PostgreSQL17 database, the already-public normalized M15B Foushee vote fixture and
the matching Foushee/shared rows and relationships from the already-public
after-Justice artifact graph. Other members' historical artifact rows are omitted
because their legislators are absent from this one-member fixture; foreign-key
constraints remain enforced. It refuses an occupied database.
Preparation audits contain the persisted immutable graph and pre-activation
registry rows. The fixture's active registry comes from the separate executed
after-Justice audit, which binds Education245/Environment239/NS248/Justice251.
This preserves the distinction between a prepared graph and executed publication.
No source bodies, live data or production credentials are acquired.

`backend/scripts/education79_locator_preparation.py` is a pure exact-packet
adapter plus a narrowly guarded **disposable-only** persistence function. It
rebuilds and compares all original candidate products. A pending or unsealed
candidate approval cannot generate eligible artifact specifications. The supplied
sealed decision must bind the exact root245, all three proposed identities,
same-source locator and final statuses: human_approved/gold_benchmark/eligible.
All three rows receive these final statuses at their immutable INSERT. There is
no later approval/eligibility UPDATE. Candidate approval expressly excludes
production execution; a separate positive V2R activation decision remains required.
All test decisions and execution evidence are visibly synthetic and cannot run
through the production selector or operator.

The proposed approval subject can be prepared for review, but this code cannot
make that decision, claim a human approved it, or seal real activation authority.
Its fixture creates synthetic approval only in the test file. A future authorized
production operator must consume a real independently approved decision and add
fresh Green identity/schema/capacity/runtime checks through the existing store;
this follow-up does not create that production operator.

The fixture proof covers:

- Three eligible immutable artifacts, two relationships and one deterministic
  batch; zero registry/public behavior changes during persistence.
- Injected late persistence failure rolls back all inserted rows. PostgreSQL
  sequence gaps are allowed; numeric IDs are read from exact complete ownership
  and never guessed, reserved or inferred from previous production maxima.
- Repeated persistence writes zero rows. Registry drift, bundle drift and batch
  ownership drift fail closed. Existing immutable artifacts remain unchanged.
- The existing pure V2R write-set builder binds actual newly persisted fixture
  IDs, the complete previous registry row and exact proposed metadata. A separate
  synthetic positive authority seals that exact write-set only for the fixture.
- A fresh READ ONLY fixture preflight precedes the existing registry replacement.
  Exactly one registry row changes; apply is idempotent, injected failure restores
  the original row, competing metadata prevents rollback, and owned rollback
  restores the complete original row while retaining the new immutable graph.
- Normal API composition reads the fixture database for Foushee119/all/118
  positions, editorial responses and all four existing released domains. Before
  and after differ by exactly six locator URL leaves, with no118 or positions
  changes. This is runtime-backed fixture proof, not a fresh production read.
- The Node card proof uses those actual API objects and resolved fixture ID.
  Existing card bindings withhold the whole card after backend replacement;
  the inert derived binding restores the identical six findings in both scopes.
  The fixture manifest is a diagnostic output, never imported by the app.

The original captured timestamps use ISO `T`; the existing V2R registry serializer
uses a space. The adapter converts only the two top-level registry timestamps
to that representation, preserving their aware instants and every other value.
Rollback must use the full exact runtime serialization, not guessed timestamps.

Run only with a freshly created dedicated fixture database:

```powershell
$env:DATABASE_URL='postgresql://invalid'
$env:EDUCATION79_DISPOSABLE_DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/pf_education79_locator'
$env:EDUCATION79_PROOF_DIR='education79-proof'
python -m pytest -q backend/tests/test_education79_locator_preparation.py backend/tests/test_education79_locator_disposable_postgres.py
node scripts/prove_education79_disposable_card.mjs education79-proof
```

Local Docker's Linux daemon was unavailable during preparation; local offline
contracts pass, but actual PostgreSQL/card proof is pending hosted execution.
Treat the first hosted report as evidence only if the exact tested head, all
assertions, synthetic boundaries and retained outputs pass. A passing fixture
does not prove fresh deployed runtime identities, current production preflight
or current official response-body bytes. The source byte proof remains the
governed cache/previously permitted retained body plus a HEAD availability check.

Future production sequence remains: exact candidate/status approval; bounded
immutable persistence authorization and guarded execution; resolve and review
actual IDs; seal exact write set and positive activation authority; coordinate
frontend card ID/natural-key/content/presentation hash binding; verify deployed
submanifests and fresh READ ONLY preflight; only then separately authorize the
one-row activation. Backend-only activation briefly withholds the whole card;
frontend-first binding also withholds it until backend matches. The release
decision must acknowledge that interval and retain both prior bindings for
rollback. No governance guard may be bypassed to hide the interval.
