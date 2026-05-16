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
