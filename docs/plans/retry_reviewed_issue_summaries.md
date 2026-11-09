# Retry reviewed issue summaries

## Problem and bounded scope

At main a8b7d99ee5da098ea0bc857abd0b7622eb4c8779, a failed or invalid
editorial-presentations response leaves otherwise available vote receipts usable,
but offers no way to recover the reviewed summaries without reloading or changing
context. This undermines the interpretation-first journey during transient faults.

Add an explicit Retry issue summaries control to the existing issue-discovery
failure state. The control reuses the same request, identity validation, card
projection and context lifetime. It does not refetch positions or vote receipts,
change the selected issue or Congress, create interpretations, relax publication
checks, or change editorial content. A valid receipts-only response is not a
failure and does not offer this retry. Card source-binding failures still remain
closed under their existing contract.

## Behavior

- Network, HTTP, incomplete and identity-mismatch responses remain unverified.
- A retry is single-flight; repeated activation while pending does not refetch.
- Failed retries remain actionable for a subsequent attempt.
- Late results cannot replace a newer member or Congress context.
- Existing receipt state and route remain intact while summaries recover.
- Keyboard focus moves to the persistent completion status only if the reader
  remains on the retry button. A reader who chooses another control keeps focus.
- The completion status also anchors the viewport when the successful retry
  removes its button. Existing late-layout and reader-cancellation logic remains.

## Validation

- Production Next.js build passed.
- All 319 frontend unit contracts passed.
- Scoped ESLint and git diff --check passed.
- Full independent-loading and history-anchor suites: 71/71 passed before the
  final two failure-recovery cases were added.
- All eight new recovery cases repeated three times: 24/24 passed, two workers,
  zero retries. Includes HTTP/network/identity recovery, duplicate activation,
  no receipt refetch, retained/moved focus, stale member/scope results, and
  subsequent recovery after failed or identity-invalid retry responses.
- Full fixture-backed CI browser selection and independent review pending.

No push, merge, publication, deployment or production-data writes performed.
Local logs and browser outputs are in ignored .tmp/.
