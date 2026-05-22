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

When Congress.gov cache enrichment is available, packets also include `so_what_context`:

- bill lifecycle: introduced date, origin chamber, latest action, public-law status
- enrichment availability counts: text versions, amendments, actions, committees, CBO estimates
- CBO estimate links when listed by Congress.gov
- text-version metadata and links when listed by Congress.gov
- recent bill actions
- amendment and committee subresource rows when cached
- prompt reminders for practical mechanism, direct stakes, lifecycle, and evidence boundary

Accepted statuses:

- `interpreted`
- `ambiguous`
- `insufficient_evidence`

For `interpreted` records, fill:

- `vote_type`
- `practical_mechanism`
- `direct_stakes`
- `evidence_boundary`
- `so_what_summary`
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
- `vote_type` should identify whether the roll call was final passage, an amendment, a rule/procedure vote, appropriations, CRA disapproval, a motion, or another action.
- `practical_mechanism` should identify the government lever changed: funding, eligibility, penalties, agency authority, reporting, repeal, delay, enforcement, procurement, disclosure, procedure, or another concrete lever.
- `direct_stakes` should name the program, agency, regulated entity, legal standard, or group directly affected when the source supports it.
- `so_what_summary` should explain in one neutral sentence why the vote matters for civic understanding.
- `evidence_boundary` should state what the available source text does not prove.
- `yea_meaning` and `nay_meaning` should describe the side of the action, not just say "supported the bill" or "opposed the bill" when a more concrete action is source-grounded.
- `issue_facet` should name the practical issue within the broader domain, such as `small_business_loan_eligibility`, `temporary_government_funding`, or `budget_reconciliation_and_debt_limit`.
- `interpretation_reason` should explain why the source is enough, or why it is not enough.

For procedural votes, do not collapse procedure into final policy. Say exactly what procedural step was being voted on. If the packet does not include the exact amendment, conference instruction, rule text, or motion effect, use `ambiguous` or `insufficient_evidence`.

For a legislator's recorded vote, the frontend should read the stored yea/nay meaning back in the context of their actual position. A `not_voting` record must be shown as a non-position, even when the underlying roll call itself is interpreted. The public UI should not lead with separate `Yea meant` and `Nay meant` boxes when the selected legislator's vote is already known. Prefer:

- why this mattered
- what this vote was
- their vote and what that recorded position meant

Reviewer prompt:

```text
You are creating a source-grounded civic vote interpretation.

Use only the provided official/source text. Do not infer motive, ideology, corruption, quality, or whether the vote was good or bad.

For each roll call, answer:

1. Vote type:
   Was this final passage, amendment, motion, rule/procedure, appropriations, CRA disapproval, confirmation, or another action?

2. Practical mechanism:
   If the winning side prevailed, what government lever changed?
   Use concrete language: funding, eligibility, penalties, agency authority, reporting, repeal, delay, enforcement, procurement, disclosure, procedure, or another source-grounded lever.

3. Direct stakes:
   Who or what would be directly affected, according to the source text?
   Name programs, agencies, populations, regulated entities, or legal standards when the source supports it.

4. Yea/Nay meaning:
   Explain what a Yea did and what a Nay did in relation to that action.
   Do not say only "supported/opposed the bill" if a more concrete source-grounded meaning is available.

5. Legislator vote:
   State what this legislator's recorded vote meant.

6. Evidence boundary:
   Say what cannot be concluded from this vote.
   If the source does not include amendment text, rule effect, final enactment status, or implementation details, mark ambiguous or insufficient evidence.

7. So-what summary:
   In one plain sentence, explain why a normal constituent might care, without telling them what position to take.
```

The first gold slice is Valerie Foushee / `ECONOMY_TAXES`, stored in:

```text
docs/interpretation_batches/batch_006_valerie_economy_gold_interpretations.json
```

## Replicating the Issue-Read Standard

Use this checklist when moving the gold-slice quality bar to another official or issue domain.

1. Pick one visible accountability slice:
   - one current official
   - one issue domain
   - enough eligible roll calls to make the section worth reading

2. Export packets from Supabase:

```powershell
cd backend
python -m app.etl.manual_interpretations export --output ..\docs\interpretation_batches\<batch>_packets.json --legislator-id <legislator_id> --domain <DOMAIN> --limit 25
```

3. Fetch bounded Congress.gov enrichment for the bills in that packet:
   - bill detail
   - summaries
   - subjects
   - actions
   - text versions
   - amendments
   - committees

Use `--include-enrichment` on each bill reference so the next packet export can include `so_what_context`.

4. Re-export the same slice to a `*_so_what.json` packet and review each row against:
   - vote type
   - practical mechanism
   - direct stakes
   - yea/nay meaning
   - actual recorded vote
   - evidence boundary
   - one-sentence civic so-what

5. Write or refresh the reviewed interpretation JSON:
   - use concrete `issue_facet` values that can be grouped into practical measure descriptions
   - keep amendment, rule, conference, and motion rows ambiguous when the official packet does not show the exact effect
   - do not turn lifecycle context into a stronger claim than the vote supports

6. Import the reviewed file:

```powershell
cd backend
python -m app.etl.manual_interpretations import --input ..\docs\interpretation_batches\<batch>_interpretations.json --reviewed-by <reviewer_id>
```

7. Verify the API and UI:
   - API evidence rows show the refreshed `plain_english_summary`, `policy_effect`, `issue_facet`, and `source_basis`
   - the opened issue's high-level read says whether interpreted yea/nay votes were for, against, mostly for, mostly against, or split
   - the read names the practical measures in plain terms
   - the read states the scope: interpreted yea/nay count, total rows, other records, and caution rows
   - the read says it is not a broad ideology score or voting recommendation

8. Run checks before committing:

```powershell
cd backend
pytest --basetemp=..\.local\pytest_<batch> tests\test_manual_interpretations.py tests\test_api_positions.py

cd ..\frontend
npm run build
```

9. Browser QA the opened issue section. A user should be able to answer:
   - What did this official do in the interpreted votes?
   - What kinds of measures were those votes about?
   - Which rows are excluded from the conclusion, and why?
   - What broader conclusion is the product explicitly not making?

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
