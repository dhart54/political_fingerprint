# Valerie Foushee Economy & Taxes Editorial Gold V2

This bundle is the first reader-first, source-checked editorial gold-slice proposal for the named member and domain. “Gold” describes the milestone target, not the status: every candidate remains `human_approval_pending` and none is `human_approved` or `gold_benchmark`.

## Contents

- Five dossiers under `measures/` for H.R. 2965, H.R. 5371, H.R. 3944, H.R. 2966, and H.Con.Res. 14.
- `source_manifest.json` and `claim_source_map.json` for official evidence and claim-level locators.
- `house_clerk_roll_snapshots.json` for the nine checked-in Foushee action records.
- `review_packet.json` for seven layered interpretation candidates and two controls.
- `policy_episode_map.json` and `issue_synthesis.md` for four-episode deduplication.
- `editorial_workflow_contract.md` for the future human approval and freeze process.
- `comprehension_protocol.md` for moderated reader review.
- `side_by_side_review.md`, generated deterministically from the JSON packet.

## Integrity boundaries

- Six substantive Nay rolls become four episodes, not six independent signals.
- Roll 310 remains Not Voting and is excluded from pattern evidence.
- Roll 263 has an exact, source-grounded WIC instruction but remains a nonbinding, non-counting procedural control.
- Roll 180 remains a mixed en-bloc control rather than a forced single policy position.
- H.R. 5371 stages and H.Con.Res. 14 stages remain separate.
- Later legislation is labeled context; it never replaces what was voted on.
- Every dossier includes source-grounded, attributed supporter and opponent arguments; those institutional arguments are never assigned to Foushee as her motive.
- `public_field_availability_proxy` is not the exact runtime renderer.
- Automated checks are structural and heuristic diagnostics only. Human factual review, editorial scoring, comprehension testing, and approval are pending.

## Dramatic before-and-after examples

### H.R. 5371, roll 281

Before: “This was initial House passage of a short-term FY2026 funding bill.”

After: **Voted against this short-term funding proposal through November 21.** Before FY2026 began, the House considered temporarily continuing the prior year's funding and operating rules for federal agencies through November 21. Foushee voted No on this short-term proposal. The House passed it, but it did not become the final law.

Why better: the deadline, baseline, member action, and version boundary are visible without knowing what “continuing appropriations” means.

### H.Con.Res. 14, roll 100

Before: “This was the House vote to agree to the Senate-amended budget blueprint.”

After: **Voted against the revised framework for later budget legislation.** The House decided whether to accept revised instructions for committees to write later legislation on taxes, spending, deficits, and the debt limit. Foushee voted No. Congress adopted the framework, but this vote did not itself change taxes, benefits, annual funding, or the debt limit.

Why better: it translates both concurrence and reconciliation, while placing the framework-versus-law boundary in the collapsed layer.

### H.R. 2966, roll 156

Before: “This was final House passage of a bill changing who could qualify for SBA 7(a) and 504 small-business loans.”

After: **Voted against immigration-status limits on SBA business loans.** The House considered limiting SBA 7(a) and 504 loans to applicants whose required owners were citizens, U.S. nationals, or lawful permanent residents. Foushee voted No. The bill passed the House but had not become law.

Why better: it names the eligibility rule and affected applicants immediately, then separates the House proposal from current law.

## Human-review queue

1. Verify every claim/source pair and locator.
2. Score each field and both attributed arguments for factual accuracy, clarity, specificity, civic neutrality, and lifecycle correctness.
3. Run the five-question comprehension protocol with nonexpert readers.
4. Resolve the few field-level questions recorded in `review_packet.json`.
5. Approve, reject, or request changes per field and per roll.
6. Only after approval, design production persistence and exact rendering behavior in a separate milestone.

No schema, migration, database, API, frontend, production, counting, alignment, or runtime behavior is changed by this bundle.
