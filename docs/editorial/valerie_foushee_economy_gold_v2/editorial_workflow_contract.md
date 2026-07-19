# Legislative interpretation editorial workflow contract

Status: proposed operating model. Runtime implementation and human approval are outside this milestone.

## Workflow

1. Identify one canonical measure and one exact roll-call action. Record chamber, Congress, roll, date, question, result, and measure stage.
2. Assemble a bounded official source packet using the hierarchy: House Clerk; Congress.gov text, summary, actions, and amendments; CRS; CBO; committee reports; Congressional Record; official agencies; attributed official advocacy.
3. Build or reuse the measure dossier. Reuse canonical identity, enacted baseline, source collection, and lifecycle research across members; revalidate it against the current text and date. Never reuse a member action, an inferred position, or the meaning of a different roll stage.
4. Reconcile the named member against the official roll record by stable member identifier. Preserve `Not Voting`, `Present`, and variant Clerk labels without inferring a side.
5. Draft the 10-second, 30-second, and two-minute layers. Lead with the real-world choice, then mechanism, affected group, scale, status, and caveats.
6. Extract the strongest documented supporter and opponent arguments from official committee reports, floor debate, hearing records, or attributed official statements. Record the argument, institutional or named attribution, source IDs, locator, support status, and evidence limit. Never infer an argument from party, vote direction, or bill outcome, and never assign an institutional argument to the member without a member-specific source.
7. Map every material claim to an official source, locator, support status, and uncertainty. Source presence is not proof; a reviewer must verify that the cited passage supports the exact claim.
8. Run deterministic structural and safety diagnostics. These are heuristic diagnostics, not verified editorial-quality judgments. A “strong” result would mean strong under that diagnostic rubric only.
9. Perform human factual review, editorial review, and the applicable comprehension test. Candidate text remains a machine draft until the required humans approve it; automated checks cannot approve, waive, or promote a record.
10. Freeze an approved structured claim only after human approval, recording content version, approval status, source-manifest hash, reviewer, review date, lifecycle status, and supersession history.
11. Import and render only approved claims. Reopen review when legislative status, measure text, a material source, or the public rendering contract changes.
12. Build issue synthesis only from approved roll claims, deduplicated by policy episode and excluding Not Voting and non-counting controls.

## Competing-argument gate

Every dossier must contain `documented_supporter_argument` and `documented_opponent_argument` with attribution, source IDs, claim IDs, support status, and uncertainty/evidence limits.

Allowed evidence states are:

- `supported_official_attributed`: the exact argument and attribution were reviewed in an official source;
- `official_evidence_not_yet_reviewed`: potentially relevant official material exists but has not been reviewed claim by claim; this always blocks editorial completion; and
- `insufficient_official_evidence_after_review`: the search log identifies the official sources and locators reviewed and accurately explains why no adequate argument could be promoted.

A dossier is editorially complete only with a supported pair, or after a human factual reviewer accepts a documented `insufficient_official_evidence_after_review` limitation. A generic absence of a source, party-based inference, or a vote-based inference cannot satisfy the gate.

## Review tiers

- **Full gold review:** required for multi-stage measures, omnibus or mixed packages, reconciliation or budget frameworks, Not Voting/Present records, procedural controls, disputed lifecycle status, or any candidate carrying a high-risk civic misconception. It requires independent factual review, line editing, five-question reader testing, and approval-editor signoff.
- **Routine lower-risk review:** available only for a single-stage, single-mechanism roll with complete sources, supported arguments, unambiguous member action, and stable lifecycle status. It still requires a human factual reviewer and approval editor; automation cannot approve it.

Any reviewer may elevate a routine record to full gold. Failing a source, argument, lifecycle, or comprehension gate automatically elevates and blocks publication.

## Human roles and separation

- **Researcher/drafter:** assembles the dossier and candidate copy.
- **Factual reviewer:** checks every claim against the cited passage, including attribution and roll/lifecycle identity.
- **Editorial reviewer:** scores clarity, specificity, neutrality, progressive disclosure, and information loss.
- **Comprehension moderator:** runs the protocol without coaching and records responses verbatim.
- **Approval editor:** resolves the final field decisions and is the only role allowed to assign human approval in a future authorized system.
- **Lifecycle owner:** monitors source/status changes and opens refresh work.

For full gold, the factual reviewer and approval editor must be different people from the researcher/drafter. One person may hold editorial and approval roles only after factual review and comprehension results are complete.

## Disagreement and escalation

Reviewers record disagreements at the field or claim level with the competing readings and exact source locators. A factual conflict with an authoritative source, ambiguity about the roll's civic meaning, or disagreement about whether a caveat is required blocks approval and escalates to the editorial lead plus civic-integrity reviewer. If authoritative sources conflict or the current model cannot safely represent the vote, the record remains `insufficient_evidence`; deadline pressure does not lower the gate.

## Comprehension thresholds

- **Full gold:** at least five nonexpert participants. All must correctly identify the member action and lifecycle status without a substantive error; at least four of five must answer each of the other three standard questions correctly without prompting or after one neutral probe. No critical misconception may recur in two participants.
- **Routine lower-risk:** at least three nonexpert participants. All must correctly identify member action and lifecycle; at least two of three must answer each remaining question correctly. Any repeated critical misconception requires revision and full-gold retesting.

Critical misconceptions include treating Not Voting as No, House passage as enactment, a budget framework as the later law, a procedural control as a policy outcome, or an attributed advocate argument as the member's motive. Changed top-layer fields are retested with a fresh minimum participant set.

## Lifecycle ownership and service levels

Editorial Operations owns the review queue; the assigned lifecycle owner owns each frozen record. Automated monitoring may create alerts but cannot change approval status or public copy.

- Corrected roll or source record, enactment, veto, or material text change: unpublish or mark stale within one business day; complete triage within two business days.
- Other chamber action, committee referral, conference action, or source-link failure: triage within three business days.
- Render-contract or repeatable comprehension failure: block the affected field immediately and open review within one business day.
- Stable records: scheduled source and lifecycle check every 90 days while the Congress is active and once at adjournment.

Refresh work records the trigger, owner, opened time, source delta, affected claims, disposition, and completion time.

## Status model

Codex may assign only:

- `machine_draft`
- `agent_source_checked`
- `human_approval_pending`
- `insufficient_evidence`

Codex must not assign `human_approved` or `gold_benchmark`.

## Frozen-record contract for future implementation

An approved record will need:

```json
{
  "content_version": "...",
  "approval_status": "human_approved",
  "source_manifest_hash": "sha256:...",
  "reviewer": "...",
  "review_date": "YYYY-MM-DD",
  "lifecycle_status": "...",
  "supersedes": "... or null"
}
```

This milestone does not create that production schema or assign those values.

## Field-level human review

For each roll, the reviewer records `approve`, `reject`, or `request_changes` for:

- headline;
- practical choice;
- member action and result;
- prior baseline;
- mechanism;
- affected group;
- scale or timing;
- later history;
- caveats;
- each claim/source pair; and
- each comprehension expected answer.

Any rejected material claim blocks approval of every public field that depends on it.

Missing or unverified competing arguments, an unresolved lifecycle state, an unsupported material claim, a stale source locator, or a failed comprehension threshold blocks approval of the dossier and every dependent roll or synthesis field.

## Reopen triggers

- a measure advances, fails, or becomes law;
- official text or an action record is corrected;
- a source locator no longer supports the claim;
- a later stage makes prior status wording stale;
- public rendering drops a required caveat;
- reader testing reveals a repeatable misconception; or
- the synthesis episode mapping changes.

## Acceptance boundary

Readability formulas, source-map completeness, genericity checks, and other automated results are diagnostic inputs. They cannot certify factual support or editorial quality. Human approval and comprehension evidence remain pending for every record in this bundle.
