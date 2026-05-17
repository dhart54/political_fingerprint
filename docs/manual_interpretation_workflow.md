# Manual Vote Interpretation Workflow

This workflow supports the first cached "DC-speak breakdown" pass without adding an OpenAI API key or any live LLM dependency.

Core rule: interpret what the vote appears to do. Do not judge whether that outcome is good or bad.

## Shape

The database stores manual/plain-language interpretation fields on `vote_interpretations`:

- `plain_english_summary`
- `yea_meaning`
- `nay_meaning`
- `policy_effect`
- `issue_facet`
- `confidence`
- `source_basis`
- `uncertainty_note`
- `reviewed_by`
- `reviewed_at`

The original deterministic fields remain:

- `interpretation_status`
- `support_position`
- `oppose_position`
- `interpretation_reason`
- `interpretation_version`
- `classification_version`

## Export Packets

Export a bounded batch from Supabase:

```powershell
cd backend
python -m app.etl.manual_interpretations export --output ..\docs\interpretation_batches\batch_001_packets.json --legislator-id leg_valerie_p_foushee --domain ECONOMY_TAXES --limit 25
```

Useful starter domains:

- `ECONOMY_TAXES`
- `HEALTH_SOCIAL`
- `INFRASTRUCTURE_TECH_TRANSPORT`
- `JUSTICE_PUBLIC_SAFETY`
- `IMMIGRATION_BORDER`
- `EDUCATION_WORKFORCE`
- `ENVIRONMENT_ENERGY`

## Draft Interpretations

Each packet includes official/source text and a `draft_template`.

Accepted statuses:

- `interpreted`
- `ambiguous`
- `insufficient_evidence`

For `interpreted` records, fill:

- `plain_english_summary`
- `yea_meaning`
- `nay_meaning`
- `policy_effect`
- `issue_facet`
- `confidence`
- `source_basis`

Use `insufficient_evidence` when the official text does not clearly say what the vote would change.

## Gold Slice Standard

Before scaling a new issue area, create one gold slice for one official and one issue domain. A good slice should let a user understand the record without already knowing congressional procedure.

For each interpreted vote:

- `plain_english_summary` should answer: what was this vote, in one or two plain sentences?
- `policy_effect` should answer: what would change if this action succeeded?
- `yea_meaning` and `nay_meaning` should describe the side of the action, not just say "supported the bill" or "opposed the bill" when a more concrete action is source-grounded.
- `issue_facet` should name the practical issue within the broader domain, such as `small_business_loan_eligibility`, `temporary_government_funding`, or `budget_reconciliation_and_debt_limit`.
- `interpretation_reason` should explain why the source is enough, or why it is not enough.

For procedural votes, do not collapse procedure into final policy. Say exactly what procedural step was being voted on. If the packet does not include the exact amendment, conference instruction, rule text, or motion effect, use `ambiguous` or `insufficient_evidence`.

For a legislator's recorded vote, the frontend should read the stored yea/nay meaning back in the context of their actual position. A `not_voting` record must be shown as a non-position, even when the underlying roll call itself is interpreted. The public UI should not lead with separate `Yea meant` and `Nay meant` boxes when the selected legislator's vote is already known. Prefer:

- why this mattered
- what this vote was
- their vote and what that recorded position meant

The first gold slice is Valerie Foushee / `ECONOMY_TAXES`, stored in:

```text
docs/interpretation_batches/batch_006_valerie_economy_gold_interpretations.json
```

## Import Reviewed JSON

The import file should contain:

```json
{
  "schema_version": "manual_interpretation_v1",
  "interpretations": []
}
```

Then import:

```powershell
cd backend
python -m app.etl.manual_interpretations import --input ..\docs\interpretation_batches\batch_001_interpretations.json --reviewed-by codex_manual_review
```

The importer rejects records with persuasion/judgment language, invalid statuses, invalid confidence labels, missing source basis for interpreted records, or support/oppose positions that do not make sense for the status.

## UI Direction

After a first batch is imported, the frontend should surface:

- what the vote appears to do
- what a Yea vote meant
- what a Nay vote meant
- how the selected official voted
- source link
- confidence or insufficient-evidence status

This is an interpretation layer, not voting advice.
