# Foushee Justice 119 Universe Discovery V1

## Review status

Recommendation: **READY FOR HUMAN UNIVERSE BOUNDARY REVIEW**.

This packet describes a proposed, non-authorizing Justice & Public Safety action
universe for Valerie Foushee (`F000477`). It does not establish
`full_defined_issue_record`, authorize a universe, interpret newly discovered
actions, construct episodes, synthesize behavior, alter publication state, or
write to production.

The active seven-action public artifact remains a `reviewed_conclusion` within
its `benchmark_sample`, with public claim class `reviewed_sample_finding`.

## Boundary and cutoff

- Chamber and Congress: House, 119th Congress, sessions 1 and 2.
- Included action dates: January 3, 2025 through June 11, 2026.
- Production snapshot began: July 30, 2026 at
  `2026-07-30T17:08:25.915204Z`.
- Latest production roll-call source ingest represented in the member rows:
  `2026-06-17T22:02:51.619523+00:00`.
- Official-source acquisition was reconciled on July 30, 2026.
- Latest official House action observed: July 23, 2026, roll 283.
- The proposed universe is complete only through the June 11 recorded cutoff.
  It is not complete through the future end of the 119th Congress, and the 61
  observed actions after that cutoff require a later refresh.

The governed member-service evidence represents Foushee as the serving NC-04
House member throughout every included action date. Its service boundary begins
in 2023, has year-level precision, and has no recorded service end.

## Production read-only controls

The production snapshot used one Supavisor session-mode connection and one
explicit transaction. The first SQL command was:

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
```

The immediate server proof reported:

- active `transaction_read_only=on`;
- `transaction_isolation=repeatable read`;
- informational `default_transaction_read_only=off`;
- expected database identity, `public` schema, and PostgreSQL 17.6 identity.

Only eight fixed, repository-defined, parameterized data queries ran after the
proof and transaction-local controls. The audit records stable query IDs,
normalized query digests, parameter schemas, purposes, time bounds, row counts,
and deterministic result digests without parameter values or connection
details. Every production query ran inside the single proven transaction. The
transaction ended with `ROLLBACK`, the connection closed, and no production
write was attempted.

Disposable PostgreSQL 17 separately proved that:

- the active transaction rejects an attempted write at the database layer;
- the client allowlist rejects write SQL before execution;
- ordered results are deterministic;
- missing, duplicate, conflicting, unresolved-source, and changed-snapshot
  cases remain detectable.

The disposable container held only throwaway fixtures and was removed after the
test.

## Production lineage

| Layer | Production objects | Stable identity | Current public consumers |
| --- | --- | --- | --- |
| Member and service | `legislators`, `house_member_service_evidence`, `house_member_metadata_snapshots` | Bioguide ID and governed snapshot ID | Member/profile read paths |
| Actions and member votes | `roll_calls`, `votes_cast`, `bills`, `vote_contexts` | `chamber:congress:session:rollcall_number`; legislator/roll-call relationship | Position evidence |
| Classification, interpretation, and precompute | `vote_classifications`, `vote_interpretations`, `fingerprints` | Roll-call ID; member/domain/window/version | Positions and evidence |
| Governed editorial publication | `editorial_artifact_versions`, `editorial_artifact_relationships`, `editorial_publication_registry` | Artifact ID; member/issue registry key | Editorial presentations and governed receipt projection |

The canonical public action ID is constructed from chamber, Congress, session,
and roll number. Internal database row IDs remain only in the secure raw
snapshot.

## Reconciled sets

| Set | Count | SHA-256 |
| --- | ---: | --- |
| Complete member-action IDs through cutoff | 577 | `b5e53f51a4b5c27f58a9094f53c55279f30624ec08a107b7fd5c8d56f03850bc` |
| Sanitized complete action records | 577 | `0b4f2b94297db15269ec6bd65e79963d13f33fa287b7a856b8675404b1c7eca7` |
| Direct production member-action IDs | 555 | `82297e80e967f7b3c52f410a74ca2d69354138f4c227398626035b63723936a8` |
| Sanitized direct production action records | 555 | `5c29ccbf8dad628353a500a5dc40764ee61f0fc7c9dca7e6540f055ff0185c29` |
| Current production primary Justice set | 24 | `2a8f77071165bda1186516ec00385d7b649ce1fb889cbcacf9cecc27f57a88a6` |
| High-recall Justice candidates | 111 | `fe735b755cc6d04235a0acaf8de4d96b76e41ea61257bcbee7bd1532885ed7a9` |
| Proposed Justice universe | 27 | `852100ab4a1056b071c2dfe60acd1fd08f9bdd6f8c6bcc1cff0e0b213e41638e` |
| Unresolved boundary candidates | 13 | `011871e3234332487ce4c3468b22e27948de79e9adcbaf58afde60d4d713600a` |

Disposition totals are:

- 26 `proposed_in_scope_substantive`;
- one `proposed_in_scope_non_directional`;
- 55 `procedural_context`;
- 16 `proposed_exact_action_ineligible`;
- 13 `boundary_review_required`;
- no missing, unresolved, or conflicting official source after the completed
  Congress.gov acquisition.

The one non-directional proposed action is roll 158, where the official member
action is `Not Voting`. No support or opposition meaning is assigned.

## Recall and boundary rules

Recall united four independent lanes:

1. current primary and secondary/provisional production Justice signals;
2. the governed seven-action benchmark;
3. repository and official Clerk acquisition records;
4. broad text recall plus Congress.gov policy-area metadata.

Keywords only surfaced candidates. They never established membership. Proposed
membership requires a substantive exact action and either official
`Crime and Law Enforcement`/`Law` policy-area evidence or the governed
exact-action benchmark. Rules, previous-question votes, recommit/commit motions,
tabling/referral/discharge actions, and other procedural controls remain
non-counting context.

The 13 unresolved human boundary decisions are:

- `house:119:1:6` — Laken Riley Act, House measure;
- `house:119:1:17` — Preventing Violence Against Women by Illegal Aliens Act;
- `house:119:1:23` — Laken Riley Act, Senate measure;
- `house:119:1:159` — resolution on antisemitic and political violence;
- `house:119:1:179` — resolution on attacks against Minnesota lawmakers;
- `house:119:1:220` — Stop Chinese Fentanyl Act;
- `house:119:1:286` — vehicular-terrorism prevention measure;
- `house:119:2:5` — retaining the Commerce/Justice/Science appropriations
  division;
- `house:119:2:7` — passage of a multi-division appropriations measure;
- `house:119:2:87` — DHS appropriations passage;
- `house:119:2:102` — resolution supporting DHS;
- `house:119:2:155` — FISA title-VII extension;
- `house:119:2:221` — later FISA title-VII extension.

These remain visible because they cross Immigration, International Affairs,
Transportation, appropriations, civil-rights, or national-security boundaries.
None is silently excluded.

## Benchmark reconciliation

All seven benchmark actions are present, unchanged in canonical identity, and
included in the proposal:

`house:119:1:32`, `house:119:1:33`, `house:119:1:130`,
`house:119:1:131`, `house:119:1:166`, `house:119:1:275`, and
`house:119:1:299`.

The public governed overlay changes the raw stored interpretation status of
roll 32 from `ambiguous` to its separately approved exact-action projection.
That is a governed presentation-layer distinction, not a production-row
mutation or a new interpretation in this milestone.

## Production, repository, official, and API reconciliation

- Production-only actions through cutoff: none.
- Repository/official actions through cutoff absent from the production member
  join: 22. These are explicit potential ingestion gaps, mostly environmental
  Congressional Review Act measures; none entered the Justice candidate set.
- Official actions after cutoff: 61, rolls 223–283. They are outside this
  snapshot and require refresh.
- Duplicate production rows: none.
- Duplicate canonical identities: none.
- Conflicting member vote/date state across the 555 overlaps: none.
- Differing measure identities: seven Senate resolutions are stored in
  production as generic bill type `s`, while Clerk preserves `sjres` or
  `sconres` (`house:119:1:61`, `:95`, `:96`, `:137`, `:143`, `:296`, and
  `house:119:2:143`). This is recorded as a potential production bill-linkage
  defect; canonical roll-call and member-vote identities still agree.
- Proposed actions not currently primary Justice: 15.
- Current primary Justice actions not proposed: 12; ten are procedural controls
  and two (`house:119:2:87`, `house:119:2:102`) remain boundary-review cases.
- Missing candidate Congress.gov metadata at closeout: none. The 25 records
  absent from the repository cache were acquired securely with metadata,
  summaries, subjects, actions, text-version listings, amendments, and
  committees.

The live public API returned:

- `scope=119`: 24 Justice evidence rows;
- `scope=all`: 76 Justice evidence rows;
- `scope=118`: 52 Justice evidence rows.

The 119 evidence IDs exactly match the direct production primary Justice set.
The seven governed benchmark projections are available for `119` and `all`;
`118` remains receipts-only. Positions, Justice evidence, and editorial
presentations were checked at all three scopes. No fallback or fixture evidence
was detected. The API coverage window ends June 16, while Foushee's direct
production member-action rows end June 11; this is recorded as a coverage-window
versus member-row distinction.

## Final production freshness

A new production snapshot began at `2026-07-30T17:46:57.928657Z`, using the
same corrected read-only contract and ending with `ROLLBACK`. All eight fixed
data-query result digests matched the baseline exactly. The direct 555-action
ID set, sanitized member-action record digest, 24-action primary Justice set,
seven benchmark identities, database identity, query sequence, June 11 latest
member-vote date, and June 17 source-ingest timestamp were unchanged. The
freshness result-bundle SHA-256 is
`7360de0a65135651266178f0df6c8bb2f194c31d6e70c944f6bcae33db519ac2`.

## Artifacts

- Proposed manifest:
  `docs/editorial/full_record_reviews/proposals/f000477_justice_public_safety_119_full_issue_universe_manifest_v1.json`
  - ID:
    `full-universe:f000477:justice_public_safety:119:proposed:v1`
  - file SHA-256:
    `89303c8c041906e9d628e457c96e03714cc45424ae58a69458115049b904ac2a`
  - universe-subject SHA-256:
    `d312b23ca67541b227270203b7cdab4fd51818eb3900c73d98c0bce13b3f98e7`
- Discovery artifact:
  `docs/editorial/full_record_reviews/proposals/f000477_justice_public_safety_119_full_issue_universe_discovery_v1.json`
  - ID:
    `universe-discovery:F000477:JUSTICE_PUBLIC_SAFETY:119:v1`
  - file SHA-256:
    `51de2e7d8249133eb19d90108290cadc3572c8a51e2eae2428a3b88767db294d`
- Sanitized source inventory:
  `docs/editorial/full_record_reviews/proposals/f000477_justice_public_safety_119_source_inventory_v1.json`
  - file SHA-256:
    `30b6c0097e2b34b494f2aa95ac0c8236782399495dd1c4abb6bbdb84dfc0a85d`

Full raw production, public-API, Clerk, and Congress.gov evidence remains in the
restricted local evidence directory and is not committed. Committed artifacts
contain public legislative fields, canonical IDs, sanitized proof fields, and
content digests only.

## Why this remains non-authorizing

The proposal directory contains no
`full_issue_universe_authority_receipt_v1`. The discovery record fixes
`authority_status=pending_human_universe_review`,
`full_record_claim=false`, and `synthesis_eligible=false`. The existing
full-record review state and active benchmark publication are unchanged.

Human review must decide:

1. whether the 27 proposed actions correctly express the Justice boundary;
2. how to resolve the 13 cross-domain boundary candidates;
3. whether the 22 through-cutoff and 61 post-cutoff ingestion gaps are
   sufficiently understood for a refreshed proposal;
4. whether the seven lossy Senate-resolution bill links need production repair;
5. whether source completeness is adequate to issue a detached authority
   receipt in a separate, explicitly authorized milestone.
