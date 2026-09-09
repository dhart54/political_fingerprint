# M15A.2 source-verified core repair preparation

This package is **not accepted, not sealed, and does not authorize production
database writes**. The runtime remains at
`8cd2d6ee1fd31e876c0d1c67b7516f6405f1d67d`. No accepted interpretation or publication
is replaced. Independent review and explicit authorization must precede any
future production apply.

## Exact evidence and graph

`source_manifest.json` identifies the 31 user-scoped official Clerk roll-call
files and the official House roster. `official_sources.zip` preserves their exact
bytes. Preparation reparses those bytes through `load_house_clerk_bundle`, checks
Congress/session/roll and F000477, and compares normalized votes against the
active reviewed publications. Existing adapter aliases Aye/Yea and No/Nay are
retained. Deterministic contexts use the full official vote universe and each
exact roll’s recorded vote-time party attributes, not current roster parties.
The existing context builder runs separately for each roll; all 31 party totals
are checked directly against official recorded votes. Context outcomes must
agree with Clerk (including “Agreed to” as passed).

`repair_bundle.json` binds the fresh READ ONLY production baseline, target
identity, active publications, every proposed fact row, and exact caps:

| Table/operation | Inserts |
|---|---:|
| bills | 6 |
| roll_calls | 31 |
| votes_cast, F000477 only | 31 |
| vote_contexts, F000477 only | 31 |
| classifications, interpretations, editorial artifacts, publication registry | 0 |
| updates and deletes during apply | 0 |

Fourteen pre-existing referenced bills are reused unchanged. The 26 existing
different-session collisions, their linked vote/context/classification/amendment
state, and their referenced bills are protected. Core identity/FK constraints and
triggers are also bound. Aggregate table counts describe the observed baseline;
they do not freeze unrelated append-only activity between preparation and apply.

The exact action/member lookup remains session-aware. No existing different-session
record is reused, relabeled, transferred, or deleted. No classifications or
interpretations are needed to establish the missing governed core actions.

## Proof and reproducibility

`disposable_baseline.json.gz` is a bounded snapshot of public legislative facts
and the existing publication rows required by the normal selector. It reproduces
the relevant protected production state in a dedicated disposable database; it
does not synthesize editorial approval. `review_package.json` records the source,
bundle, fixture, and implementation bindings plus the disposable validation results.

Run the focused proof with `M15A2_DISPOSABLE_DATABASE_URL` pointing only to a local
database named `pf_m15a2_repair`:

```powershell
python -m pytest -q backend/tests/test_m15a2_core_repair.py backend/tests/test_m15a2_core_repair_postgres.py
```

The tests deliberately rebuild that dedicated disposable database. The existing
`receipt-evidence-repair-postgres` CI lane runs the same proof in its own database.

Production preparation/preflight uses the existing target pin, an explicitly
READ ONLY transaction, and bounded statements. `prepare` reproduces the graph
from pinned bytes and freshly checks active publication/member-vote consistency.
Any partial or conflicting target state fails closed; it is never completed
automatically. All exact target facts already present and matching yield
`ALREADY_APPLIED` with zero writes.

## Future execution and rollback boundary

The narrow operator is `backend/scripts/foushee_m15a2_core_repair.py`. Future
production apply requires the reviewed bundle digest, a new ownership-receipt
path, and a separate explicit `--confirm-production-repair` authorization flag.
Rollback requires the same bundle, its exact ownership receipt, and a separate
`--confirm-production-rollback` flag. No such production operation occurred here.

Apply acquires the repair advisory transaction lock, rechecks the protected
baseline, inserts in FK order, verifies exact facts and actual table deltas,
and runs normal public reads against the same uncommitted transaction before
commit. The ownership receipt is atomically created and fsynced **before commit**;
receipt storage failure rolls the transaction back. A receipt alone does not
prove commit. Database preflight and exact owned-row fingerprints determine
whether rollback is permitted. Repeating apply preserves an existing receipt.

Rollback removes only receipt-owned contexts, votes, roll calls, and the six new
bills, rejecting drift or new dependencies. It preserves reused bills and all
different-session rows. Sequence gaps from PostgreSQL's nontransactional ID
allocation are allowed; no sequence is rewound and no pre-existing data row changes.

The disposable proof requires National Security 82/82 and Environment 63/63
reviewed actions to resolve, 119/all detail to return 200, and discovery/detail
counts to agree. Education stays 25 available = 17 reviewed + 8 unreviewed, with
the additional actions outside accepted findings. Justice receipts and all
accepted presentation wording remain unchanged. The shared database coverage end
date may extend only to the exact latest source-backed inserted vote date; this
is not a change to any reviewed interpretation.
