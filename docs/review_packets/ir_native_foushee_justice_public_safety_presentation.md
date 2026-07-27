# Review Packet: Revised IR-native Foushee Justice presentation

## Decision scope

- Member: Valerie P. Foushee (`F000477`)
- Issue: `JUSTICE_PUBLIC_SAFETY`
- Reviewed scope: 119th Congress
- Artifact: `f000477:justice_public_safety:119:v1`
- Semantic source: `semir-dev-05-justice-mechanism-divide`
- Focused validation: `semir-dev-04-justice-mixed-fentanyl-trajectory` and
  `semir-dev-06-justice-one-sided-argument`
- Editorial status: `human_approved`
- Benchmark status: `gold_benchmark`
- Production eligible: `true`
- Publication active: `false`
- Effective public tier: `receipts_only`

Reviewer `reviewer:dhart54`, acting under
`editorial_publication_review_authority_v1`, approved the exact wording, gold
benchmark promotion, and production eligibility on 2026-07-27. The reviewer
acknowledged all seven canonical limitations. Publication activation was
explicitly kept inactive.

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

The approved but publication-inactive artifact exposes only the non-analytical
`Vote receipts` tier.

## Independent exact-action source authority

The compiler receives
`docs/editorial/action_source_contracts/foushee_justice_public_safety_119_v1.json`
separately from presentation authoring. Its contract ID is
`foushee_justice_public_safety_119_v1`; its canonical SHA-256 is
`0ee8575db526d4b021d7b26d2befbe9c22eb7af9473c12ac2ecec616f3ae9386`.

The contract is tied by raw-file SHA-256 to the frozen source manifest and
accepted claim/source map. It authorizes these exact pairs:

| Action | Vote source | Action-meaning source(s) |
|---|---|---|
| `house:119:1:32` | `clerk_roll_032` | `congress_hamdt5` |
| `house:119:1:33` | `clerk_roll_033` | `congress_hr27` |
| `house:119:1:130` | `clerk_roll_130` | `congress_hr2255_text` |
| `house:119:1:131` | `clerk_roll_131` | `congress_hr2240`, `hrpt_119_079` |
| `house:119:1:166` | `clerk_roll_166` | `congress_s331`, `public_law_119_26`, `cbo_s331` |
| `house:119:1:275` | `clerk_roll_275` | `congress_hr5143`, `rules_print_119_11` |
| `house:119:1:299` | `clerk_roll_299` | `congress_hr5107`, `hrpt_119_317` |

Every analytical mapping includes the Clerk receipt and all required
action-meaning sources for each mapped action. Unknown pairs, cross-action
substitutions, and vote-only mechanism provenance fail closed.

## Canonical material limitations

The approval subject binds the following exact, canonically sorted IDs and
texts. The limitation-set SHA-256 is
`822098797ffce236c0018576b02969e15a6495c82ca577c5c74e69f5dd2a58df`.

1. `bounded-reviewed-sample`: Seven substantive actions across five independent
   episodes are a bounded 119th-Congress sample, not the complete Justice
   record.
2. `dc-pursuit-exceptions`: The D.C. pursuit proposal included risk, futility,
   and alternative-apprehension exceptions.
3. `dc-repeal-exceptions`: The D.C. reform-repeal substitute retained the
   neck-restraint and vehicular-pursuit subtitles.
4. `fentanyl-package-content`: The later fentanyl framework combined permanent
   scheduling and enforcement consequences with research provisions.
5. `mixed-fentanyl-trajectory`: The three related fentanyl actions form one
   mixed episode and do not establish a change in position, motive, or
   philosophy.
6. `one-sided-hr2240-arguments`: The reviewed H.R. 2240 official argument
   evidence was one-sided; no opposing argument was synthesized.
7. `retired-firearm-scope`: The retired-firearm action does not establish a
   general position on police tools or police equipment.

Party alignment remains context only under the interpretation principles; it is
not an artifact-specific receipt limitation.

## Immutable approval subject and compiler receipt

- Compiled IR SHA-256:
  `f6acbacca4b32f7daf3deef757d14538add4c8b81d0fc80923f0cf3caf8aa3f1`
- Reviewed wording SHA-256:
  `30636227799244522d07a9608e06878561439f0fb9819931989727277607ae92`
- Mapping-set SHA-256:
  `c71926699df244e9cbd1e6438cd06139570462765c2b7374d35c209bfc692bcd`
- Evidence/provenance SHA-256:
  `a37fc3468f1af932c5bf062789f25551337b40eefe4502df7afd469d0af795f6`
- Immutable presentation-content SHA-256:
  `5813d5e556542d0ef2234dc05b1e1e24d5811d8c0e22af7775cd1e9b82aa55ca`
- Approval-subject SHA-256:
  `67e67001ca678e70debba52e9049632f90d99da4d6f1dcaea60da40beaa87874`
- Approved, publication-inactive compiled artifact SHA-256:
  `b05e4a9e5212bac50c9c2cbeb0afd4cd5a07818b022c977c2f10252d01d3f2c4`

The compiler receipt repeats the complete approval subject. The subject binds
identity, scope, compiled meaning, wording, mappings, all immutable provenance,
the independent source-contract ID and digest, the exact limitation set, and
the immutable presentation content. Mutable publication controls and the
detached receipt are excluded, preventing a digest cycle.

The signed decision is
`docs/editorial/presentations/f000477_justice_public_safety_119_approval_receipt.json`.
Its receipt ID is
`approval-receipt:f000477-justice-public-safety-119-v1-20260727-dhart54`.
It binds the exact statement and mapping sets, all seven limitations, and the
complete approval subject. The unsigned template remains solely as a
non-authorizing regression fixture.

An approved receipt must use an ID matching
`approval-receipt:[a-z0-9][a-z0-9._-]{2,127}`, a reviewer ID matching
`reviewer:[a-z0-9][a-z0-9._-]{2,127}`, recognized authority
`editorial_publication_review_authority_v1`, and a timezone-aware decision
timestamp. It must exactly acknowledge the seven bound limitation IDs and
texts and exactly match every approval-subject field.

## Remaining independent decision

Publication activation remains inactive and requires a separate future
authorization and operational milestone. Approval, benchmark promotion, and
production eligibility do not activate publication by themselves.

## Production effects

None. No database, production system, live registry, publication state, or
deployment was accessed or changed.
