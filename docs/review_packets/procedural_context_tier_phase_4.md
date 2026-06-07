# Procedural Context Tier - Phase 4

Date: 2026-06-07

Scope: define and implement a display-only procedural-context tier for weak House procedural/floor-rule evidence rows discovered in Phase 3B.

No production data was written. No Supabase rows were modified. No import was run. No API shape, UI route, support/opposition counting, or alignment logic changed.

## Why This Tier Exists

Phase 3B found that the scalable weak pattern was not another amendment-heavy batch. The strongest repeated opportunity was six weak Justice & Public Safety `house_of_representatives` rows repeated across roughly 430 officials.

Those rows can improve voter comprehension because they explain House floor process around rule resolutions and previous-question votes. They are also risky if treated like ordinary interpreted Yes/No policy rows, because a procedural rule vote is not final passage of the underlying bill and may bundle several measures.

## Product Treatment

The product now distinguishes:

| Treatment | What it may explain | What it counts toward |
| --- | --- | --- |
| Source-grounded substantive vote meaning | Practical policy action, why it mattered, member vote meaning, and what not to infer | Support/opposition counts and alignment only when stored as `interpreted` and mapped to support/oppose positions |
| Procedural-context explanation | Floor process, rule or motion context, related bill/package/rule, and what not to infer | Display only; no support/opposition, alignment, or readiness promotion |
| Insufficient evidence | Available source text does not support a practical vote meaning | Display only; no support/opposition or alignment |
| Not voting | The member was recorded as not voting on an interpreted row | Display only; no support/opposition or alignment |

Procedural-context rows may say:

- what the procedural vote was
- what rule, bill package, or floor step it related to
- why the step may matter for understanding House floor process
- that the row is visible but excluded from support/opposition and alignment

Procedural-context rows must not say:

- that the representative supported or opposed the underlying bill as a substantive policy position
- that the row proves broad issue ideology
- that the row aligns or misaligns with a user preference
- motive, character, corruption, or voting advice

## Schema Feasibility

No schema change was needed.

The current stored statuses remain:

- `interpreted`
- `ambiguous`
- `insufficient_evidence`

Procedural context is derived in the frontend from existing fields such as `issue_facet`, `vote_context.vote_type`, roll-call question, description, bill title, and measure title. Because the stored row remains non-interpreted, existing backend alignment and support/opposition counting continue to exclude it.

## Six Valerie / Justice Examples

These Phase 3B candidates were not imported. They remain examples for how the tier should render if production rows are later approved under a contextual treatment.

| Roll | Bill | Current status | Vote | Procedural rendering | Counts? |
| ---: | --- | --- | --- | --- | --- |
| 160 | `119:hres:489` | `insufficient_evidence` | Nay | Procedural-context row explaining a previous-question vote tied to the floor rule | No |
| 161 | `119:hres:489` | `insufficient_evidence` | Nay | Procedural-context row explaining agreement to the rule resolution | No |
| 267 | `119:hres:707` | `insufficient_evidence` | Nay | Procedural-context row explaining a previous-question vote tied to the floor rule | No |
| 268 | `119:hres:707` | `insufficient_evidence` | Nay | Procedural-context row explaining agreement to the rule resolution | No |
| 290 | `119:hres:879` | `insufficient_evidence` | Nay | Procedural-context row explaining a floor-rule procedural step | No |
| 291 | `119:hres:879` | `insufficient_evidence` | Nay | Procedural-context row explaining agreement to the rule resolution | No |

If rendered under this tier, the rows receive a visible confidence label: `Procedural context`.

They remain visible in evidence cards and grouped evidence preview. They are not used in support/oppose counts, aligned/not-aligned labels, or confident issue-position summaries.

## Readiness Behavior

Procedural-context rows can reduce scroll/value mismatch because the UI can explain why the rows are present.

They do not automatically promote issue readiness. They still remain part of the limited/ambiguous row burden for issue overview readiness, so a section dominated by procedural context remains cautious unless substantive interpreted Yes/No rows independently support a stronger read.

## Scale Assessment

This pattern can scale across the repeated roughly 430-official cluster because the same six roll calls and source packets recur. The safe scale path is:

1. keep the row treatment contextual
2. keep support/opposition positions null unless a later schema explicitly supports non-counted contextual interpretations
3. verify every imported contextual record preserves a clear `what_not_to_infer`
4. prove import logic cannot add contextual rows to alignment or support/opposition counts

## Later Production Import Gate

A later import would require explicit approval and a separate import design. Approval should confirm:

- whether contextual records stay stored as `insufficient_evidence`/`ambiguous` with richer reviewed text, or require a new database status
- how the API exposes contextual text without changing alignment or count behavior
- that imported rows do not populate support_position or oppose_position as ordinary issue positions
- rollback instructions for the contextual import
- validation proving production support/opposition counts and alignment payloads are unchanged

## Product Conclusion

The procedural-context tier is feasible without schema changes for display behavior. It materially improves scroll/value mismatch by naming and explaining weak procedural rows instead of showing them as generic unexplained evidence.

The six Valerie procedural candidates should not be imported as ordinary interpreted records. They are reasonable candidates for a later explicitly approved procedural-context import, provided the import preserves the no-counting boundary.

Recommended next milestone: procedural-context production import only if the storage/API exposure model is explicitly approved. Otherwise, continue with broader coverage expansion that produces substantive interpreted rows rather than procedural context.
