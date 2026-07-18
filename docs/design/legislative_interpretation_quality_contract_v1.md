# Legislative Interpretation Quality Contract V1

## Product Standard

A reasonable reader should be able to say what Congress was deciding, what would change, and what the member's recorded vote mechanically meant without knowing congressional procedure. The explanation must remain bounded to the reviewed record and must not infer motive, ideology, character, corruption, or a voting recommendation.

## Three Separately Evaluated Layers

### Measure-Level Understanding

State the prior baseline, proposed mechanism, affected entities, documented scale/timing, attributed arguments, and eventual status. Do not use the official title as the practical explanation.

### Vote-Level Meaning

State the exact stage and translate Yea and Nay into their procedural and substantive consequences. Mark whether the roll call was final, intermediate, symbolic, procedural, or limited-context. A member's position is the recorded vote plus that translation—not “supported/opposed the measure.”

### Issue-Level Synthesis

Use only approved, substantive, counting interpretations. Name recurring concrete choices and meaningful exceptions; show included and excluded receipts; state evidence coverage. Do not derive an ideology score, motive claim, prediction, or recommendation. Fewer than three substantive interpreted votes cannot support a pattern claim in V1.

## Current Pipeline Audit

| Stage | Current role | Quality risk |
|---|---|---|
| Chamber/Congress.gov ingestion | Preserves official roll call, measure, amendment, and source facts | Official titles and vote questions rarely explain practical effect |
| Deterministic classification | Assigns domain and procedural/eligibility treatment | Correctly cannot supply missing policy research |
| `vote_interpretations` | Stores status, positions, reviewed copy, source basis, uncertainty, and review metadata | Field presence varies sharply by review generation |
| Review packet export/import | Supports bounded supervised interpretation | Existing `source_basis` is often field-level rather than claim-level |
| Issue aggregation | Counts eligible interpreted Yes/No records and excludes procedure/not-voting | Count direction can be more prominent than substantive choices |
| Public-copy theme helpers | Allow curated facets/domains and reject raw/audit-like row text | Safe themes may collapse a distinct mechanism into an abstract label |
| Evidence cards | Prefer `why_it_mattered`, `what_happened`, member context, and boundary | Detailed `policy_effect`, baseline, scale, or source map may be absent from the card |
| Golden-render fixture | Deterministically exercises the current UI | It validates rendering, not whether readers comprehend the policy choice |

The present safety model is directionally correct: uncontrolled raw evidence cannot leak into top-level synthesis. The tradeoff is measurable information loss. The future contract should pass only human-approved structured public claims (`decision`, `mechanism`, `affected_entities`, `member_vote_meaning`, `outcome`) rather than allow arbitrary row text or rely only on a theme label.

## Gold Interpretation Shape

Every candidate contains:

1. `one_sentence_decision`: direct answer to “What choice was Congress making?”
2. `practical_effect`: what would change if the action succeeded.
3. `affected_entities`: direct affected people, programs, agencies, industries, jurisdictions, or authority.
4. `member_vote_meaning.yea` and `.nay`: concrete translations.
5. `credible_dispute.supporter_rationale` and `.opponent_rationale`: attributed, source-mapped positions; no manufactured symmetry.
6. `consequence_and_outcome`: passed/failed, final/intermediate, and later status.
7. `bounded_inference`: the narrow conclusion and most important unsupported inference.

`insufficient_official_evidence` and `not_applicable` are valid calibrated outputs, not filler.

## Rubric And Fatal Override

The machine-readable rubric scores twelve dimensions 0–4 for a maximum of 48: factual and procedural accuracy; mechanism, practical effect, and affected-entity specificity; member-vote meaning; credible argument framing; outcome/status; source traceability; calibration; plain language; and distinctiveness.

Hypothesis tiers are: unacceptable below 24 or with any fatal defect; generic-but-accurate 24–32; useful 33–39; strong 40–44; exceptional 45–48. A strong result also requires comprehension questions 1, 2, and 4 to be answerable. Thresholds are not approved production gates.

Fatal defects include reversed Yea/Nay mechanics; procedure described as final passage; false enactment; invented effects, amounts, or affected groups; motive attribution; advocacy presented as fact; insufficient-evidence pattern claims; title restatement as practical explanation; and a material claim without a source map.

## Genericity Taxonomy

The audit labels official-title restatement; procedural paraphrase without policy effect; generic funding language; generic supported/opposed language; missing baseline, mechanism, affected group, magnitude/timeline, credible alternative, or outcome; caveat-dominated copy; domain label substituted for theme; evidence list without synthesis; repetitive counts; safe but content-free fallback; unsupported specificity; and overbroad pattern claims.

Counts are deterministic. A label may coexist with factual accuracy; “generic” is not a euphemism for false.

## Comprehension Contract

For every roll call, ask:

1. What was Congress deciding?
2. What would have changed?
3. Who or what was affected?
4. What did this member's vote mean?

Store the answer key, allowed equivalents, critical misconceptions, and fields needed. Later testing should compare current and candidate copy without initial source lookup, code misconceptions independently, then expose receipts and measure correction. This milestone performs no external-user research.

## Human Review

Automated validation can reject malformed or unsafe candidates and highlight missing evidence. It cannot determine editorial sufficiency. Reviewers must inspect the cited source passage and verify policy mechanism, affected entities, vote mechanics, attribution, outcome/later status, and issue synthesis. Only a human-reviewed candidate may advance to `gold_benchmark`.

## Smallest Material Follow-On

**Valerie Foushee Economy & Taxes Interpretation Quality V2** should implement one slice end to end:

1. Canonical measure/amendment dossiers and claim maps for the existing slice.
2. Human verification of all material fields and vote mechanics.
3. Structured draft generation plus deterministic factual/procedural validators.
4. Human-approved public claim objects at the safety boundary.
5. Updated vote cards and one issue synthesis without changing counting semantics.
6. Golden rendering plus comprehension protocol dry-run.

Only after that slice passes should interpretation coverage expand.
