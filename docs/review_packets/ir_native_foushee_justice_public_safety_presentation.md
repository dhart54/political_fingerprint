# Review Packet: Revised IR-native Foushee Justice presentation

## Decision scope

- Member: Valerie P. Foushee (`F000477`)
- Issue: `JUSTICE_PUBLIC_SAFETY`
- Reviewed scope: 119th Congress
- Artifact: `f000477:justice_public_safety:119:v1`
- Full-record semantic source:
  `semir-dev-05-justice-mechanism-divide`
- Focused validation:
  `semir-dev-04-justice-mixed-fentanyl-trajectory` and
  `semir-dev-06-justice-one-sided-argument`
- Editorial status: `human_approval_pending`
- Benchmark status: `not_promoted`
- Production eligible: `false`
- Publication active: `false`
- Effective public tier: `receipts_only`

This packet is a revised candidate for a new human decision. It does not
approve wording, promote a benchmark, establish production eligibility, or
authorize publication.

## Exact revised candidate copy

- Tier label: **Reviewed conclusion**
- Teaser: “The reviewed 119th-Congress sample shows support for reporting and
  for evidence, research, or implementation conditions in two independent
  episodes, alongside opposition to three specific proposals concerning
  retired-service firearm access, broader D.C. police pursuit authority, or
  repeal of most reviewed D.C. policing restrictions.”
- Headline: “A divide by policy mechanism in the reviewed sample”
- Issue summary: “In this reviewed 119th-Congress sample, Foushee supported
  reporting and evidence, research, or implementation conditions in two
  independent episodes, while opposing three specific proposals concerning
  retired-service firearm access, broader D.C. police pursuit authority, and
  repeal of most reviewed D.C. policing restrictions.”
- Coverage: “This conclusion covers 7 reviewed substantive actions across 5
  independent policy episodes in the 119th Congress.”
- First pattern heading: “Certification, fentanyl research provisions, and
  officer-safety reporting”
- First pattern body: “Across independent episodes, Foushee supported an
  overdose-reduction certification condition, a later fentanyl framework with
  research provisions, and officer-safety reporting requirements.”
- Second pattern heading: “Retired-service firearm access, D.C. pursuit
  authority, and policing-rule rollbacks”
- Second pattern body: “Across independent episodes, Foushee opposed creating
  a reviewed federal program for eligible current and retired officers to buy
  qualifying retired agency firearms, broader D.C. police pursuit authority,
  and repeal of most reviewed D.C. policing restrictions.”
- Fentanyl heading: “The fentanyl episode is mixed”
- Fentanyl body: “Within one fentanyl legislative episode, Foushee supported a
  certification amendment, opposed the earlier House bill, and supported a
  later related framework that permanently scheduled fentanyl-related
  substances and included research provisions. These related stages count as
  one episode for breadth and do not establish a change in position, motive,
  or philosophy.”
- Scope: “This conclusion remains bounded to the reviewed 119th-Congress
  sample.”

The pending artifact itself exposes only the `Vote receipts` tier and the
non-analytical receipts-only teaser.

## Sentence-level mapping and direct provenance

Every mapped sentence has a unique statement ID and mapping ID. Each action
lists both its House Clerk vote receipt and the official source or sources
required to establish the action’s policy meaning.

| Statement / mapping | Proposition or boundary | Actions | Episodes | Direct vote and action-meaning sources |
|---|---|---|---|---|
| `statement:teaser:mechanism-divide` / `mapping:teaser:mechanism-divide` | `prop:af269162633f4c5c` | `32,130,131,275,299` | all five | Clerk `032,130,131,275,299`; `congress_hamdt5`, `congress_hr2255_text`, `congress_hr2240`, `hrpt_119_079`, `congress_hr5143`, `rules_print_119_11`, `congress_hr5107`, `hrpt_119_317` |
| `statement:conclusion:headline` / `mapping:conclusion:headline` | `prop:af269162633f4c5c` | `32,130,131,275,299` | all five | Same direct sources as teaser |
| `statement:conclusion:body` / `mapping:conclusion:body` | `prop:af269162633f4c5c` | `32,130,131,275,299` | all five | Same direct sources as teaser |
| `statement:coverage:reviewed-actions` / `mapping:coverage:reviewed-actions` | `boundary:coverage:f000477:justice_public_safety:119` | all seven | all five | All seven Clerk receipts and all required official action-meaning sources |
| `statement:scope:reviewed-119` / `mapping:scope:reviewed-119` | `boundary:scope:f000477:justice_public_safety:119` | all seven | all five | All seven Clerk receipts and all required official action-meaning sources |
| `statement:repeated-support:heading` / `mapping:repeated-support:heading` | `prop:c428677c0dbee5e0` | `32,131,166` | fentanyl; reporting | Clerk `032,131,166`; `congress_hamdt5`, `congress_hr2240`, `hrpt_119_079`, `congress_s331`, `public_law_119_26`, `cbo_s331` |
| `statement:repeated-support:body` / `mapping:repeated-support:body` | `prop:c428677c0dbee5e0` | `32,131,166` | fentanyl; reporting | Same direct sources as support heading |
| `statement:repeated-opposition:heading` / `mapping:repeated-opposition:heading` | `prop:abbe87a63baefb7d` | `130,275,299` | firearm; pursuit; repeal | Clerk `130,275,299`; `congress_hr2255_text`, `congress_hr5143`, `rules_print_119_11`, `congress_hr5107`, `hrpt_119_317` |
| `statement:repeated-opposition:body` / `mapping:repeated-opposition:body` | `prop:abbe87a63baefb7d` | `130,275,299` | firearm; pursuit; repeal | Same direct sources as opposition heading |
| `statement:trajectory-fentanyl:heading` / `mapping:trajectory-fentanyl:heading` | `prop:bc08a2271517ebb7` | `32,33,166` | fentanyl | Clerk `032,033,166`; `congress_hamdt5`, `congress_hr27`, `congress_s331`, `public_law_119_26`, `cbo_s331` |
| `statement:trajectory-fentanyl:body` / `mapping:trajectory-fentanyl:body` | `prop:bc08a2271517ebb7` | `32,33,166` | fentanyl | Same direct sources as trajectory heading |

Canonical action IDs use `house:119:1:<roll>`. All statement mappings also
retain:

- `docs/semantic_ir/accepted/acceptance_receipt.json`; and
- `docs/review_packets/valerie_foushee_justice_public_safety_editorial_gold_v1.md`.

## Material limitations for human acknowledgment

1. Seven substantive actions across five independent episodes are a bounded
   119th-Congress sample, not the complete Justice record.
2. The three related fentanyl actions form one mixed episode and do not
   establish a change in position, motive, or philosophy.
3. The later fentanyl framework combined permanent scheduling and enforcement
   consequences with research provisions.
4. The retired-firearm action does not establish a general position on police
   tools or police equipment.
5. The D.C. pursuit proposal included risk, futility, and
   alternative-apprehension exceptions.
6. The D.C. reform-repeal substitute retained the neck-restraint and
   vehicular-pursuit subtitles.
7. The reviewed H.R. 2240 official argument evidence was one-sided; no opposing
   argument was synthesized.
8. Party alignment is context only and does not establish motive, ideology,
   character, or philosophy.

## Immutable approval subject and compiler receipt

- Compiled IR SHA-256:
  `f6acbacca4b32f7daf3deef757d14538add4c8b81d0fc80923f0cf3caf8aa3f1`
- Reviewed wording SHA-256:
  `30636227799244522d07a9608e06878561439f0fb9819931989727277607ae92`
- Mapping-set SHA-256:
  `c71926699df244e9cbd1e6438cd06139570462765c2b7374d35c209bfc692bcd`
- Evidence/provenance SHA-256:
  `1e08c8fb326200ab50a9b434273c3b538d1e8b81ec1ad1ac80c3a7ebf42edc4b`
- Immutable presentation-content SHA-256:
  `b04f0c7df8eb54a588aaf2141cd40da700433b842a08c85183813753e21f2cbf`
- Approval-subject SHA-256:
  `3c0d4b41005ebbb16260079ecccae12fa8bef6c1f0f6ece32af34219b2cdbb94`
- Pending compiled artifact SHA-256:
  `abf1c5f091e27e336b9d06802f673f4cb4d48af127e7648c010260384c25dad1`

The compiler receipt is the complete approval subject plus its digest. The
approval subject covers immutable reviewed content, mappings, evidence, scope,
and identity. It excludes the detached receipt itself and mutable publication
controls, eliminating the prior self-referential digest cycle.

The unsigned template is:

`docs/editorial/presentations/f000477_justice_public_safety_119_approval_receipt_template.json`

It remains `human_approval_pending`, has no reviewer, authority, timestamp, or
approved IDs, records all decisions as pending, and keeps publication
activation false and out of scope.

### Unsigned detached approval-receipt payload

```json
{
  "schema_version": "editorial_public_issue_approval_receipt_v1",
  "receipt_id": "not_supplied",
  "status": "human_approval_pending",
  "binding": {
    "artifact_id": "f000477:justice_public_safety:119:v1",
    "artifact_version": 1,
    "member_id": "F000477",
    "issue_id": "JUSTICE_PUBLIC_SAFETY",
    "congress": 119,
    "approved_scope": "119",
    "schema_version": "editorial_public_issue_presentation_v1",
    "compiled_ir_sha256": "f6acbacca4b32f7daf3deef757d14538add4c8b81d0fc80923f0cf3caf8aa3f1",
    "reviewed_wording_sha256": "30636227799244522d07a9608e06878561439f0fb9819931989727277607ae92",
    "mapping_set_sha256": "c71926699df244e9cbd1e6438cd06139570462765c2b7374d35c209bfc692bcd",
    "evidence_provenance_sha256": "1e08c8fb326200ab50a9b434273c3b538d1e8b81ec1ad1ac80c3a7ebf42edc4b",
    "presentation_content_sha256": "b04f0c7df8eb54a588aaf2141cd40da700433b842a08c85183813753e21f2cbf",
    "statement_ids": [
      "statement:conclusion:body",
      "statement:conclusion:headline",
      "statement:coverage:reviewed-actions",
      "statement:repeated-opposition:body",
      "statement:repeated-opposition:heading",
      "statement:repeated-support:body",
      "statement:repeated-support:heading",
      "statement:scope:reviewed-119",
      "statement:teaser:mechanism-divide",
      "statement:trajectory-fentanyl:body",
      "statement:trajectory-fentanyl:heading"
    ],
    "mapping_ids": [
      "mapping:conclusion:body",
      "mapping:conclusion:headline",
      "mapping:coverage:reviewed-actions",
      "mapping:repeated-opposition:body",
      "mapping:repeated-opposition:heading",
      "mapping:repeated-support:body",
      "mapping:repeated-support:heading",
      "mapping:scope:reviewed-119",
      "mapping:teaser:mechanism-divide",
      "mapping:trajectory-fentanyl:body",
      "mapping:trajectory-fentanyl:heading"
    ],
    "approval_subject_sha256": "3c0d4b41005ebbb16260079ecccae12fa8bef6c1f0f6ece32af34219b2cdbb94"
  },
  "approved_statement_ids": [],
  "approved_mapping_ids": [],
  "reviewer": {
    "reviewer_id": "not_supplied",
    "authority": "not_supplied"
  },
  "decision_timestamp": null,
  "limitations_acknowledged": [
    {
      "limitation_id": "bounded-reviewed-sample",
      "text": "Seven substantive actions across five independent episodes are a bounded 119th-Congress sample, not the complete Justice record.",
      "acknowledged": false
    },
    {
      "limitation_id": "mixed-fentanyl-trajectory",
      "text": "The three related fentanyl actions form one mixed episode and do not establish a change in position, motive, or philosophy.",
      "acknowledged": false
    },
    {
      "limitation_id": "fentanyl-package-content",
      "text": "The later fentanyl framework combined permanent scheduling and enforcement consequences with research provisions.",
      "acknowledged": false
    },
    {
      "limitation_id": "retired-firearm-scope",
      "text": "The retired-firearm action does not establish a general position on police tools or police equipment.",
      "acknowledged": false
    },
    {
      "limitation_id": "dc-pursuit-exceptions",
      "text": "The D.C. pursuit proposal included risk, futility, and alternative-apprehension exceptions.",
      "acknowledged": false
    },
    {
      "limitation_id": "dc-repeal-exceptions",
      "text": "The D.C. reform-repeal substitute retained the neck-restraint and vehicular-pursuit subtitles.",
      "acknowledged": false
    },
    {
      "limitation_id": "one-sided-hr2240-arguments",
      "text": "The reviewed H.R. 2240 official argument evidence was one-sided; no opposing argument was synthesized.",
      "acknowledged": false
    }
  ],
  "decisions": {
    "editorial_wording": "pending",
    "gold_benchmark_promotion": "pending",
    "production_eligibility": "pending"
  },
  "publication_activation": {
    "active": false,
    "decision_scope": "out_of_scope"
  }
}
```

## Independent human decisions still required

An authorized human must separately decide:

1. whether to approve the exact revised editorial wording;
2. whether to promote this artifact to `gold_benchmark`; and
3. whether to mark it production eligible.

No decision is inferred from compilation, validation, or this packet.
Publication activation remains a separate future operational action after a
valid detached receipt is merged.

## Production effects

None. No database, production system, live registry, publication state, or
deployment was accessed or changed.
