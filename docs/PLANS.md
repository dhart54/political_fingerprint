# Living Execution Plans

Substantial milestones need a living execution plan. The plan is the compact operational map for the current branch; it is not a second giant prompt.

Create a plan for work that is:

- multi-system
- expected to take substantial time
- likely to involve production or deployment
- broader than a small isolated fix
- dependent on multiple validation stages

## Active Plan Location

Create one active plan under `docs/plans/`.

Use `docs/plans/TEMPLATE.md` as the starting point. Name the active plan after the milestone, for example:

```text
docs/plans/phase_25_example.md
```

Completed plans may remain in `docs/plans/` as branch artifacts when they explain the review history. If a later cleanup is needed, move old plans into a dated archive in the same directory rather than deleting them silently.

## Required Contents

The active plan should include:

1. milestone intent
2. larger-goal alignment
3. user-visible or operational outcome
4. scope and boundaries
5. decision envelope
6. definition of done
7. current repository/production baseline
8. implementation sequence
9. progress checklist
10. discoveries
11. decisions and rationale
12. deviations/corrections
13. validation results
14. production writes performed
15. rollback paths
16. blockers
17. final reconciliation

For milestones touching product copy, summaries, evidence language, UI interpretation, caveat placement, party-context language, finding-card language, or methodology-adjacent user-facing copy, read `docs/interpretation_principles.md` before implementation and note any relevant interpretation-boundary decisions in the plan.

## Plan Rules

- Update the plan during execution.
- Mark stages complete as they are completed.
- Record material corrections and discoveries.
- Do not treat plan creation as task completion.
- Continue implementation after planning.
- Keep the plan operational and concise.
- Do not copy the full milestone prompt into the plan.
- The plan cannot override the user's request, `AGENTS.md`, or safety guardrails.
