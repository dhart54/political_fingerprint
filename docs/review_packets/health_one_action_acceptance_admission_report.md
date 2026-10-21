# Health one-action: preparation and executable admission

19 October 2026. This report distinguishes an inert documentary owner decision
packet from a complete executable acceptance-chain subject. It adds no contract,
schema, methodology or authority. References use PR237 merge
`a0605e4e3e3a81751bf273155f1cf5e0cfa4d21a`.

## Conclusion and correction

A documentary pending packet using the existing typed IR review payload is
representable now. The earlier blanket stop on preparation was too broad.
Accepted-episode prerequisites apply to the optional episode-first behavioral
candidate path; they do not prohibit reviewing the already compiled shared
candidate. No schema change is necessary for this documentary deliverable.

A complete executable acceptance chain has **not** been established. In
particular, full-issue-universe authority is incompatible with this bounded
pilot. Singleton episodes, Not Voting and null decision arrays are semantically
or structurally representable; that does not establish authority/admission
compatibility. The packet must not claim otherwise.

## Existing supported preparation route

The canonical workflow uses Shared Action Core, Shared Issue Mapping and Member
Action Projection, then `shared_corpus.adapt_to_semantic_ir_input` and
`pipeline.run_editorial_pipeline` (editorial workflow lines 22-37 and 63-68).
`backend/app/semantic_ir/pipeline.py:58` rejects shared candidates when public
authoring or persistence is requested. Without those requests it compiles and
validates the candidate and calls `build_review_payload` at line 83.

`backend/app/semantic_ir/adapters.py:20-40` binds the entire compiled IR digest,
preserves candidate review state, includes both members' coverage/review routes,
and sets `approval_conferred=false`. This is an existing typed candidate review
output. It is sufficient to accompany a documentary pending owner worksheet.
The worksheet is not a new machine-consumed decision contract.

The bounded review convention also already exists:

- `full_record_issue_interpretation_v1.schema.json` pointers
  `/definitions/axes/properties/review_scope/enum` and
  `/definitions/interpretation/properties/review_state/enum` allow
  `bounded_partial_record` and `candidate` respectively.
- `scripts/validate_full_record_issue_interpretation.py:165-185`, function
  `_validate_external_authority`, requires partial/sample reviews to carry only
  null full-record authority references and returns false for full-record
  authority. It does not grant an alternative executable acceptance authority.
- `_validate_actions` at line 449 requires complete exact-denominator accounting
  and preserves Yea/Nay versus Present/Not Voting distinctions. Interpretation
  schema fragments allow candidate review; no complete new review manifest is
  claimed validated by this milestone.

## Exact incompatible full-universe authority constants

`docs/methodology/full_issue_universe_authority_receipt_v1.schema.json` fixes:

| JSON pointer | Required value | Location |
|---|---|---|
| `/properties/review_scope/const` | `full_defined_issue_record` | line 14 |
| `/properties/decision/const` | `approved_complete_issue_universe` | line 41 |
| `/properties/reviewer/properties/authority/const` | `full_issue_universe_review_authority_v1` | line 37 |

Those constants cannot truthfully describe the accepted `bounded_partial_record`
one-action pilot. Replacing them, relabeling the scope, inserting a fake approval
or borrowing another domain's receipt would change or bypass governance.

`backend/app/etl/universe_authority.py:91-102`,
`verify_manifest_and_receipt`, invokes closed schema validation on both manifest
and receipt before validating content/subject/action-set bindings. Its
`_validate_schema` at line 69 uses Draft7Validator with a format checker and
raises `UniverseAuthorityError` on errors. For a current full-record admission
example, `scripts/validate_m13b_education_workforce_source_readiness.py:78-79`
first validates the upstream universe authority; lines 95-122 enforce its exact
receipt/action-set/universe digest bindings. The upstream M13A validator checks
the receipt schema at lines 101-107 and the exact approved-complete decision at
line 118. These historical milestone checks are examples of admission, not
reusable Health authority.

The generic source-readiness schema additionally requires the authority receipt,
universe proposal, selection and source inventory at
`/definitions/inputBindings/required` (line 44). Its methodology requires an
already approved complete issue universe and exact authority membership. The
generic evaluator validates source mechanics; it does not independently grant
universe authority. A loosely typed binding object passing syntax is insufficient.

## Other candidate and implementation gates

The specific rejecting call reproduced in investigation was candidate
compilation, **not** acceptance implementation:
`backend/app/semantic_ir/compiler.py:995` delegates to
`_compile_behavioral_candidate_ir`; lines 1035-1041 require
`canonical_internal_policy_episode=true`. This is the opt-in episode-first
candidate path described by `full_record_behavioral_semantic_ir_candidates_v1.md:9`.

The candidate-package schema requires accepted policy-episode authority and
implementation bindings at lines 137-145, plus an episode evidence ledger and
complete accounting. It describes a graph that is still unaccepted but whose
upstream episodes are accepted. The current canonical Health IR is a different
existing output; it is not this envelope. Its Foushee proposition has
`conclusion_relevance=supporting`; the optional envelope's enum at line 70 is
`primary|limiting|excluded`. No relabeling or conversion is performed here.

`full_record_behavioral_semantic_ir_decisions.validate_implementation`, lines
253-266, separately requires accepted policy-episode authority, episode
implementation and action-interpretation implementation. Lines 285 onward
verify seals and lineage. `validate_authority`, lines 136-221, requires actual
accepted immutable human authority, exact proposition content decisions and
complete accepted episode dispositions. None is invoked by this preparation.

Existing decision templates are deliberately unaccepted:

- The action decision schema requires empty/non-authorizing state, null
  decisions/reviewer/authority/timestamps and real candidate/content digests.
- `full_record_policy_episode_candidates.build_human_decision_template:536`
  produces null selected decisions and false acceptance/authority flags. A
  complete instance still requires a real typed candidate batch and its digests;
  its batch builder derives episode content from accepted action records.
- The behavioral human-decision schema requires `empty_not_authorizing`, null
  decisions/reviewer/timestamp and authorizing=false. Its decision array allows
  one Foushee proposition decision and an empty Massie proposition list. Its
  complete envelope still requires a truthful candidate ID/content digest.

Hashing a candidate or empty template establishes identity. Some helpers call
that operation `seal`; they also hash explicitly unaccepted objects. This is
distinct from creating a human acceptance-authority seal or accepting content.
Syntax/fragment checks cannot supply missing upstream acceptance or admission.

## Replayable raw evidence versus normalized Health captures

The full-record source-readiness path requires actual replayable official bytes:

- Schema `/definitions/rawProvenance/required` requires `governed_local_path`
  and `sha256` (line 72); the path pattern at line 76 fixes the evidence root.
- `full_record_source_readiness._resolve_governed_path:152` confines paths to
  that root. `_source_integrity:165-197` checks official source type/host, actual
  file existence and SHA-256 at line 193, plus neutral-projection digest.
- For whole-measure sources, `_derive_criteria:343-397` requires supported
  operative content; the normal bill-text branch requires official bill-text
  source type, XML and an operative body at lines 378-382, with ES/EAH version
  compatibility. The explicit Congressional Record PDF path has its own bounded
  content verification. A rendered text excerpt alone is not either raw format.
- `full_record_action_interpretation.validate_candidate_artifact:1031-1040`
  resolves each evidence-map raw path and checks actual file SHA-256 again.

The Health `governed_sources.json` contains governed normalized records: two
Clerk member rows plus metadata/party totals, and the captured 1,736-character
ES text. Its recorded raw hashes are not proof that matching raw bytes are
present. It contains no `raw_provenance.governed_local_path`. Git reconstruction
authenticates those stored objects; it does not turn them into raw XML or verify
the original ZIP, which remains unverified.

Additional raw evidence **is** retained in the pinned Git tree, under
`docs/editorial/full_record_reviews/source_readiness/evidence/f000477_national_security_foreign_119_v1/`:

| Raw object | Actual SHA-256 |
|---|---|
| `BILLS-119s2393es.xml` | `04f063befa42e8b335fc14539b218401408cfb806c3e734438a67d944db10689` |
| `roll119_2_180.xml` | `d52d940529fbb4eab886c5c32ad6e712097829f93c886d5adb8cd171541c5e52` |
| `119_s_2393_actions.json` | `a143f675f626923c67e3b3b50b242be832f4daab6389caed725b3f70ccef7bc0` |

Each full filename is its hash plus `_` plus the name above. Local actual bytes
matched these hashes using the repository's Windows long-path helper; plain
Path checks initially missed these long paths. Pinned Git blob bytes also match.
The builder binds exact full paths/Git blob identities and parses the ES
identity/provisions, roll metadata and both actual member statuses, and the
recorded House suspension/pass stage. Historical Foushee source-readiness replay
returns ready with no blockers; no Health or Massie readiness authority follows.

These raw identities differ from the original Health recorded raw hashes. They
are additional preparation evidence, not replacements or archive matches. Reuse
of official evidence does not transfer National Security meaning, membership,
episode or member acceptance. No fresh acquisition is required or performed.
Later events in the retained actions feed add no claim to the bounded packet.

## Missing artifacts and bounded alternatives

| If pursuing the optional executable chain | Missing for this Health subject | Effect/limit |
|---|---|---|
| Universe/source admission | Compatible bounded authority/admission basis; truthful source-readiness artifact and source bindings | The full-universe receipt is not compatible. Existing raw evidence can support reconciliation but cannot cure scope authority. |
| Action interpretation | Typed candidate/evidence maps/parity, content-bound empty action decision templates, applicable accepted authority and deterministic implementation records | Drafting candidates/templates is distinct from accepting or implementing them. No new authority is inferred from the documentary Accept. |
| Policy episodes | Typed candidate batch/empty decision template, then separately governed authority and implementation | The singleton issue-mapping episode is not automatically an accepted episode implementation. |
| Opt-in behavioral IR | Compatible candidate envelope/episode ledger and fully bound empty decision templates | Cannot be claimed ready by copying the current IR or inventing required IDs/hashes. |

Recommended existing-governance next step: prepare the documentary pending packet
with the existing typed review payload, exact graph/wording/source identities,
Foushee's one pending proposition decision and Massie's explicit nondirectional
disposition. Keep both decisions unset and all seven mappings unchanged. Record
missing executable prerequisites in prose, rather than fake fields inside a
schema-conformance claim. This is the currently authorized deliverable.

A later executable bounded-acceptance path needs its own precise admission
reconciliation/decision. Expanding to a complete Health universe would be a
different product milestone and is not recommended as a workaround. Changing an
authority schema or creating a new executable bridge is outside this milestone.
Historical National Security acceptance is not an alternative authority source.

## Validation and authority limits

Read-only probes reproduced the canonical candidate IR and unapproved review
payload, both public/persistence rejections, the separate opt-in accepted-episode
rejection, and schema-format support for null Foushee decisions/empty Massie
propositions and candidate interpretation fragments. Whole-receipt schema
validation rejected an in-memory bounded/pending variation of a historical
receipt on both exact constants; no altered receipt was saved. The bounded
external-authority branch accepts null references while conferring no authority.
Fragment/branch probes do not claim a complete new review manifest passed.

The implementation adds deterministic packet validation and adversarial tests in
the already hosted-selected Health test module. Original packet SHA-256 remains
`3b6b60a88bb7ca9ef42abe4fb80714910d490ea9dac4eb8b79a6cfc547960347`.
No contract, guard, graph, seven mappings, accepted wording, normalized source
or authority is changed. No new acceptance, DB operation, public artifact,
registry/runtime activation or manual deployment is performed. Test/delivery
results are recorded in the active milestone plan and PR.
