# Legislative Measure Dossier Contract V1

## Purpose

A dossier is the reusable, source-verified factual layer beneath interpretations. It separates what a measure would do from what a particular roll call did. This is a design contract only; it does not change the database, API, classifier, or public product.

## Object Hierarchy

1. **Measure dossier**: baseline, mechanism, affected entities, scale, documented dispute, and lifecycle for a bill, resolution, nomination, or other policy object.
2. **Amendment dossier**: the amendment's own text and effect, linked to—but never replaced by—the parent measure dossier.
3. **Roll-call interpretation**: chamber, question, stage, outcome, and the mechanical meaning of Yea and Nay at that stage.
4. **Member-specific vote context**: the recorded position, party/outcome context, and non-vote handling.
5. **Issue-synthesis evidence unit**: an approved, counting roll-call interpretation plus bounded claim tags.

Multiple roll calls may reuse a measure dossier. An amendment needs its own dossier whenever its effect differs from the parent measure. A procedural vote may reference a parent dossier for orientation but cannot inherit the parent's substantive vote meaning.

## Required Dossier Fields

Every field is structured and claim-mapped. Unknown facts use `insufficient_official_evidence`; fields that genuinely do not apply use `not_applicable`.

| Field | Meaning | Human verification |
|---|---|---|
| `chamber`, `congress`, `roll_call_identifier` | Stable official identity | Required |
| `measure_identity` | Bill, amendment, nomination, resolution, or motion | Required |
| `official_vote_question`, `vote_date`, `vote_stage_type` | What the chamber recorded | Required |
| `measure_status_at_vote` | Lifecycle state at the instant of the vote | Required |
| `policy_baseline` | Rule, funding, authority, eligibility, or program state before the proposal | Required |
| `proposed_policy_mechanism` | Concrete government lever the measure would change | Required |
| `practical_effect_if_adopted` | Neutral, source-grounded consequence of adoption | Required |
| `affected_entities` | Directly affected people, programs, agencies, industries, jurisdictions, or authorities | Required |
| `documented_amounts_dates_thresholds` | Amounts, deadlines, thresholds, or implementation periods | Required when claimed |
| `supporter_rationale`, `opponent_rationale` | Attributed arguments, never neutralized advocacy | Required when present |
| `roll_call_outcome` | Passed/failed and vote totals where documented | Required |
| `subsequent_legislative_or_legal_status` | Later chamber, enactment, veto, court, or implementation status | Required when claimed |
| `member_vote_meaning_yea`, `member_vote_meaning_nay` | Direct translation of each recorded side | Required |
| `importance_consequence` | Consequential, intermediate, symbolic, procedural, or limited-context | Required |
| `uncertainty`, `what_not_to_infer` | Evidence gap and narrow inference boundary | Required |
| `claim_level_source_map` | Material claim → URL, source role, retrieval date, optional short excerpt | Required |

## Claim Map

Each entry contains:

```json
{
  "claim": "proposed_policy_mechanism",
  "source_url": "https://...",
  "source_role": "crs_summary",
  "retrieved_at": "2026-07-18",
  "support_kind": "direct",
  "review_note": "Paraphrase checked against section 3."
}
```

A URL alone is not verification. Review must confirm that the source supports the precise claim. Material claims may map to multiple sources. Search snippets are never sources. Sponsor or opposition statements are labeled advocacy, not neutral fact.

## Source Hierarchy

Prefer, in order: Congress.gov measure/amendment/nomination/action and official roll-call records; CRS; CBO; committee reports; statutory or amendment text; Congressional Record; official executive-agency material; official sponsor/opposition statements labeled as advocacy; other directly relevant government reports.

Use the narrowest source that proves the claim. The official roll call proves the question, member position, totals, and result; it usually does not prove the full practical effect. Parent-measure context cannot substitute for amendment text.

## Structural Rules

- Yea and Nay meanings must be logical opposites at the actual stage, except where parliamentary mechanics require a more precise description.
- Procedure cannot be described as final passage or enactment.
- A later status must include an as-of date and must not be projected backward as the legal effect at the vote stage.
- `not_voting` produces no member support/opposition position.
- Pure procedure remains non-counting for substantive issue synthesis.
- Amounts, affected populations, and legal effects require direct claim maps.
- Missing opposition rationale is not evidence that no opposition existed; use `insufficient_official_evidence` unless `not_applicable` is genuinely justified.

## Reuse And Versioning

Suggested identifiers are `measure_dossier_id`, `amendment_dossier_id`, `roll_call_interpretation_id`, and `member_vote_context_id`. Each object carries `schema_version`, `content_version`, `source_retrieved_at`, and review status. A changed source or corrected claim increments content version; downstream interpretations retain the version they used.

The V1 benchmark conservatively estimates reuse from shared reviewed artifacts and facets. The next milestone should calculate reuse from canonical measure/amendment identities, which will be more accurate.

## Review Statuses

`machine_draft` → `structurally_validated` → `source_verified` → `human_reviewed` → `gold_benchmark`.

At any stage a record may become `rejected`. Machines may assemble source candidates, draft paraphrases, identify omissions, and run validators. Humans must verify mechanism, affected entities, yea/nay meaning, attributed dispute, outcome/status, and any issue-pattern conclusion.

## Safety Boundary

This contract supplies evidence; it does not decide counting eligibility, support/opposition, readiness, alignment, or issue patterns. Those remain deterministic product decisions. No dossier draft is public merely because it passes structural validation.
