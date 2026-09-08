# M15A: Public record integrity

Baseline: `1a0c6dcdf2d367506d69817a86070934d169bb0b`.

Outcome: preserve the current scoped database ledger under exact reviewed overlays;
separate available/reviewed action counts; fail closed on public database failure.
Stop at one draft PR with hosted CI results. No production writes, deployment,
merge, accepted-artifact edits, regeneration, or new legislative interpretation.

## Read path and implementation

Discovery reads `/positions`; detail reads scoped evidence. Justice attachment and
M11/M12/M13/M14 integration merges currently replace reviewed Congress rows.
Discovery recomputes three site domains but omits Justice, and ordinary evidence
serialization omits the issue identity expected by the summary. Registry selection
continues to own publication authority; runtime composition alone changes.

1. Share exact identity validation, ledger union, overlay, and review accounting.
   Both classification-selected and reviewed-identity-selected rows must come from
   the database. Snapshot rows may enrich matching rows, never create live votes.
2. Reuse composed detail evidence for discovery counts across 118/119/all.
3. Add positive fixture opt-in and a sanitized data-unavailable exception boundary;
   keep successful no-result distinct and make demo scope explicit.
4. Add compact unreviewed receipt text and focused product tests.
5. Run relevant backend/frontend regressions, review the diff and immutable
   artifact boundaries, then open a draft PR and inspect hosted CI.

Expected change: backend composition/API, small frontend treatment, tests and
directly affected CI/documentation (roughly 15–25 files). Release-level validation
is appropriate because public runtime behavior changes. No generated output.

## Definition of done

A synthetic eighteenth M14 action stays visible, analytically unreviewed, and
does not change the seventeen reviewed projections or accepted findings. Exact
duplicates fail; missing identity never joins by date/title. Available counts
match detail for all four domains and three scopes. Default DB failure is 503,
successful missing is 404, and explicit fixture responses are marked and scoped.
Accepted M14 semantics and artifacts remain unchanged. Relevant tests pass and
one draft PR is open with hosted CI results reported.

## Progress and evidence

- Implementation complete: one shared exact overlay/identity helper now serves
  Justice and M11/M12/M13/M14 runtime composition. Both queries remain database
  selections; duplicate or contradictory identities fail closed. Detail and
  discovery share the composed ledger for all four current domains/scopes.
- Database query failures now raise a sanitized explicit exception, including
  connection cleanup failures. Only the public dispatch can opt into demo data.
  Fixture summaries retain provenance and never persist as live summaries.
- Additional raw receipts carry a neutral review relationship and small UI label.
  Missing canonical identities retain distinct raw navigation anchors.
- Validation: 363 focused/relevant backend tests and 41 frontend unit tests passed after
  the final internal DB exception-boundary refinement. Two rendered
  M14 browser cases passed (17/18 actions), with screenshot inspection. Frontend
  production build and lint passed (eight pre-existing hook warnings).
- One broader backend pass found Windows long-path/missing source and CRLF frozen
  artifact limitations. These unrelated artifacts were not edited. Linux hosted
  CI will validate the exact Git objects and disposable Postgres contracts.
- Change-size deviation: more test files than initially estimated needed explicit
  fixture opt-in, and two obsolete runtime-byte assertions needed historical Git
  replay or behavior assertions. Candidate builders and accepted artifacts remain
  unchanged. No general CI cleanup or new milestone job was added.
- Historical M13N tests now compare the six-file manifest against the captured
  deployment's Git objects; current production activation gates remain unchanged.
- Draft PR #183 opened from the exact baseline. Initial hosted CI exposed an
  import alias mismatch in standalone validators and a PostgreSQL test expecting
  an absent demo member to appear as live data. Relative imports support both
  package entry points; the disposable DB test now requires 404 for that member.
  Local candidate check and affected overlay tests passed after correction.
- Eight of nine hosted jobs passed on the second head, including M14H release
  validation, the new browser test, and the full-record benchmark. The remaining
  M12N PostgreSQL test supplied only one raw query lane and still expected the
  synthetic current action to disappear. Its raw-query setup and accounting now
  preserve that action; publication, idempotency and rollback assertions remain.
- Local implementation and draft-PR milestones are complete. The final hosted
  result is recorded in PR #183's checks and completion report; stop after the
  corrected head passes, without merge or deployment.
- Production-write envelope: none. Rollback: revert this code change before any
  separately authorized release; no persistence changes require reversal.
- Discoveries: reviewed identity queries intentionally include database actions
  absent from the classifier's domain ledger. Union those database records by
  exact identity, validating overlapping member actions, before overlaying.
- No production operations performed. Draft PR and hosted CI remain the stopping gate.
