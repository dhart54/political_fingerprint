# Two-member pilot readiness

## Purpose and boundary

Finish a useful, honest first representative slice before expanding every issue
or treating the four-choice candidate as a completed second profile. The bounded
pilot members are Valerie Foushee (F000477) and Thomas Massie (M001184).

This is an operational inventory and milestone sequence, not a new product,
methodology, readiness-scoring, editorial-approval, or publication contract.
Existing source, review, and publication gates remain authoritative.

## Delivered: repeatable public coverage inventory

Run from the repository root, using a fresh ignored output path each time:

```powershell
python scripts/audit_pilot_slice.py --scope 119 --output .local/pilot-119.json
python scripts/audit_pilot_slice.py --scope all --output .local/pilot-all.json
python -m unittest backend.tests.test_pilot_slice_inventory
```

The tool performs 26 GETs per run: health before/after and 12 resources per member.
At most four resource reads run concurrently, with no retries, credentials,
fixture fallback, database access, or mutations. Existing transport limits cap
individual responses at 8 MiB; socket timeouts are not a whole-run deadline.

It records identities, publication tiers supplied by the public selector, contact
availability, action/receipt counts, missing canonical finding links, duplicate
canonical receipt identities, and missing source URLs. Failed or mismatched
responses remain unknown, never zero evidence. Counts are per issue and may
overlap across issues. Count mismatches and missing source/identity fields are
reported diagnostics, not a reinterpretation of the vote record.

`observed` means the inventory and checked finding links were obtained on one
identified deployed commit. It does not mean user-ready, editorially accepted,
source-verified, complete, or approved for release. `incomplete` means a transport,
identity, shape, linkage, or deployment-binding check did not complete cleanly.

To keep storage lean, the output retains compact observations plus SHA-256 of
canonical JSON and byte counts for each response, not response bodies or another
source corpus. These digests bind the observation to fetched payloads but cannot
reconstruct those payloads. Use the existing governed artifacts for source truth.
Existing capture files are never overwritten.

## Next milestones, in value order

1. **Finish Foushee's first-user journey.** Use the four already-published issue
   reads as the first public slice, with the other four explicitly receipts-only.
   Verify discovery, the default all-Congress scope, a published finding, its exact
   vote, scope boundaries, source handoff, and optional contact. The November 11
   journey audit already covered live Foushee finding-to-receipt/contact and the
   candidate preview; preserve it rather than regenerate the frozen candidate.
   The new inventory covers the whole eight-issue API menu for both members.
   Human comprehension remains unproven: a brief user session should test whether
   someone can explain the proposal, the member's whole vote, the evidence limit,
   and where to verify it. Do not infer comprehension from passing browser tests.

2. **Complete Massie's bounded evidence journey.** Keep the public experience
   explicitly receipts-only until an accepted, published interpretation exists.
   Check the same discovery-to-receipt path and the existing official-directory
   fallback when stored contact metadata is unavailable. Missing stored contact
   is a transparent fallback, not permission to invent or write metadata. Reuse
   shared exact-action meaning for candidate work; do not independently author a
   second meaning for the same action. The frozen four-choice prototype remains
   a candidate, not an issue-wide or profile-wide conclusion.

3. **Resolve one narrow interpretation gate.** Prepare a decision-ready packet
   for an existing candidate with exact scope, member actions, source bindings,
   review results, and unresolved qualifications. Seek the specific editorial
   decision only when the packet is complete. Publication and production writes
   are separate milestones requiring their existing authorization and rollback
   contracts. Adding eight summaries or more politicians before this gate is
   lower value than proving one understandable and trustworthy end-to-end slice.

## Definition of done for a first slice

- The two members and requested Congress scope stay distinct throughout.
- Published findings lead to their exact recorded votes and source paths.
- Receipt-only issues and non-directional actions remain honest about limits.
- Contact or an official-directory fallback is available without persuasion.
- The user can explain a tested example without reading every receipt; record
  actual comprehension observations rather than declaring success in advance.
- Candidate, accepted, and published states remain separate. No milestone in
  this document authorizes acceptance, publication, deployment, or data writes.

## Validation scope

The inventory's offline tests cover empty versus unavailable data, member/scope/
issue mismatches, malformed response shapes, missing and duplicate domains,
public versus private action references, missing exact receipts, non-directional
positions, diagnostic count mismatches, deployment changes, invalid URLs and
timeouts, and preservation of previous captures. No frontend or semantic runtime
is changed by this milestone; their full release suites are not implied to pass.
