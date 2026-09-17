# Reproducible record-card candidate — #192

**Implementation ready; nonempty second-member reuse proof blocked by an eligible
reviewed IR-native finding/presentation for a real second member.** This is a draft
policy/form review, not public adoption. PR191 and its six-entry production card
are unchanged.

The [policy](record_card_reproducibility_policy.md), executable
[`prove_record_card_reproducibility.mjs`](../../scripts/prove_record_card_reproducibility.mjs)
and [generated results](record_card_reproducibility_results.json) define and measure
the candidate. No member code, selection array, copied member interpretation,
storage, scheduler, publication gate or registry was added.

## Implementation and review boundary

`sharedRecordCard.mjs` consumes the same publication-gated eight-issue response as
the released frontend. It mechanically projects complete findings and typed
contextual bundles, preserves display restrictions and source text, and selects
with stable domain/identity order and a 500-word ceiling. The current reference
produces **five entries / 495 words / four reviewed domains**, not a target count.
The unmodified V1 generator still verifies its six accepted entries separately.

Opening text and immediately visible detail use shared forms. Complete component
qualifications keep their source titles; source sentences are never truncated or
rewritten. Remaining verbosity reflects that preservation, not a claim that every
existing finding already has an ideal compact form. Education's directionless
display remains neutral. Mixed paired choices remain atomic even when omitted for
space. Every omission has a precise reason in the generated report.

On each API refresh, current content regenerates in memory. No frozen whole-card
hash replacement, member JSON bundle or frontend deployment is needed for an
upstream content revision after adoption. Source fingerprints and old deep links
still reject mismatches independently of issue summaries. Backend publication,
identity and source validation remain authoritative and unchanged.

The candidate is available only through the existing locally enabled review page:

- Snapshot: `/review/record-card?policy=shared&data=snapshot&representative=leg_valerie_p_foushee&scope=119`
- Live read interface: same URL with `data=live`; uses the configured ordinary API
  client and never falls back to snapshot data. Tests intercept those existing API
  URLs with recorded responses; this is not a claim of a production deployment.

Both require `ENABLE_RECORD_CARD_REVIEW=1`; Vercel remains unconditionally excluded.
The ordinary public route continues using released V1. Proposed future mechanical
operation without duplicate card-specific approvals requires this consolidated
rule/form review and adoption authorization; neither is assumed here.

## Actual proof results and limitations

| Proof | Result |
|---|---|
| Reference | Actual post-M15B Foushee 119 response; five complete units; repeat output identical. |
| Routine authorized update | Actual pre/post M15B activation responses; NS removed `wording:trajectory:milcon-va`, Justice/NS source identities changed. Source bindings and URLs regenerated with no card edit. Selected visible copy did **not** change in this historical update. Controlled tests separately prove revised source text propagates to detail. |
| Held aside | Previously unevaluated intermediate `after-ns-live`, Foushee `all` response, after final rule corrections; five units, explicit reviewed-119 boundary. No selection adjustment after this evaluation. This is a different source-state/scope case, not an independent member. |
| Unsupported | One semantic exception for War Powers' excluded contextual action versus complete lineage. No narrowed synthetic substitute; independent units continue. |
| Real second member | **Not completed.** The reviewed public catalog contains only F000477. Actual Massie response is receipts-only and is not counted as reuse. |

The smallest identified upstream starting point is Glenn Grothman (`G000576`):
the existing shared Justice corpus has 37 official member actions and a historical
24-proposition compiler proof. Replaying the exact existing two-member input
reproduced his member digest
`516b0db591c82e1a83f6f4d19abcc7b507cf30c537c7a6139fa8c5a67902ed6e`.
That proves shared-meaning reuse only. It supplies neither an accepted member
finding/public wording package nor content-bound display approval. The dependency
is that eligible IR-native finding/presentation package with complete mappings;
no new member/domain publication work was performed to manufacture it. Historical
pre-IR cross-member prose was not adapted.

## Manual work measured

One shared rule/form proposal and implementation was authored for consolidated
review. New shared legislative meaning: **0**. Member-specific edits: **0**.
Hand-selected finding arrays: **0**. New upstream approvals: **0**.
Reference, held-aside, historical update and unchanged repeat each needed **0**
additional interventions in those categories. The second-member case remains
blocked and is excluded from success counts. No maintenance-frequency or broad
scalability claim follows from this bounded evidence.

## Validation and rendered evidence

- 177 frontend unit tests pass, including nine new focused shared-policy tests.
- 118 backend publication/read-interface/integrity regressions pass.
- 51 browser tests pass; one existing optional capture test skips. Five shared
  candidate browser tests also pass in the final screenshot recapture.
- Production build passes; eight pre-existing React hook warnings remain.
- Both deterministic generators pass `--check`; V1 content remains byte-stable.
- Exact-head hosted checks and commit identity are recorded in the draft PR.

Representative captures: [desktop card](record_card_reproducibility_screenshots/desktop-live-card.png),
[mobile card](record_card_reproducibility_screenshots/mobile-snapshot-card.png),
[desktop detail](record_card_reproducibility_screenshots/desktop-live-detail.png),
[mobile detail](record_card_reproducibility_screenshots/mobile-snapshot-detail.png).
Whole-card links, complete detail, eight assistance receipts, paired Education
choices, scope/source/member failures, sparse/no-summary/unavailable states,
history, refresh, focus, return and full-record paths were checked. No eager ledger
fetch or snapshot requests occurred in the live-interface candidate tests.

No production application-data writes, publication changes, deployment, merge,
backend configuration, paid service, blue changes, or protected archive access.
The branch is added to the existing Vercel deployment-disabled list.
