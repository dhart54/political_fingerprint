# Legislative interpretation editorial workflow contract

Status: proposed operating model. Runtime implementation and human approval are outside this milestone.

## Workflow

1. Identify one canonical measure and one exact roll-call action. Record chamber, Congress, roll, date, question, result, and measure stage.
2. Assemble a bounded official source packet using the hierarchy: House Clerk; Congress.gov text, summary, actions, and amendments; CRS; CBO; committee reports; Congressional Record; official agencies; attributed official advocacy.
3. Build or reuse the measure dossier. Reuse baseline research, never the meaning of a different roll stage.
4. Reconcile the named member against the official roll record by stable member identifier. Preserve `Not Voting`, `Present`, and variant Clerk labels without inferring a side.
5. Draft the 10-second, 30-second, and two-minute layers. Lead with the real-world choice, then mechanism, affected group, scale, status, and caveats.
6. Map every material claim to an official source, locator, support status, and uncertainty. Source presence is not proof; a reviewer must verify that the cited passage supports the exact claim.
7. Run deterministic structural and safety diagnostics. These are heuristic diagnostics, not verified editorial-quality judgments. A “strong” result would mean strong under that diagnostic rubric only.
8. Perform human factual review, editorial scoring, and comprehension testing. Candidate text remains a machine draft until these steps are complete.
9. Freeze an approved structured claim only after human approval, recording content version, approval status, source-manifest hash, reviewer, review date, lifecycle status, and supersession history.
10. Import and render only approved claims. Reopen review when legislative status, measure text, a material source, or the public rendering contract changes.
11. Build issue synthesis only from approved roll claims, deduplicated by policy episode and excluding Not Voting and non-counting controls.

## Status model

Codex may assign only:

- `machine_draft`
- `agent_source_checked`
- `human_approval_pending`
- `insufficient_evidence`

Codex must not assign `human_approved` or `gold_benchmark`.

## Frozen-record contract for future implementation

An approved record will need:

```json
{
  "content_version": "...",
  "approval_status": "human_approved",
  "source_manifest_hash": "sha256:...",
  "reviewer": "...",
  "review_date": "YYYY-MM-DD",
  "lifecycle_status": "...",
  "supersedes": "... or null"
}
```

This milestone does not create that production schema or assign those values.

## Field-level human review

For each roll, the reviewer records `approve`, `reject`, or `request_changes` for:

- headline;
- practical choice;
- member action and result;
- prior baseline;
- mechanism;
- affected group;
- scale or timing;
- later history;
- caveats;
- each claim/source pair; and
- each comprehension expected answer.

Any rejected material claim blocks approval of every public field that depends on it.

## Reopen triggers

- a measure advances, fails, or becomes law;
- official text or an action record is corrected;
- a source locator no longer supports the claim;
- a later stage makes prior status wording stale;
- public rendering drops a required caveat;
- reader testing reveals a repeatable misconception; or
- the synthesis episode mapping changes.

## Acceptance boundary

Readability formulas, source-map completeness, genericity checks, and other automated results are diagnostic inputs. They cannot certify factual support or editorial quality. Human approval and comprehension evidence remain pending for every record in this bundle.
