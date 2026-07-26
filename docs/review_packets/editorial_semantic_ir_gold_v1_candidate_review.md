# Editorial Semantic IR V1 Candidate Review

Status: `candidate_pending_external_semantic_review`

This packet reviews political meaning before prose, rendering, persistence,
population generation, or publication. The canonical review object is the
proposition graph and conclusion plan in
`docs/semantic_ir/candidates/development_cases.json`; example prose is
non-authoritative. None of these candidates changes an approval, benchmark,
production, or publication gate.

## Development candidates

| Case | Structural purpose | Evidence and hierarchy | Member evidence | Proposed graph and ownership | Conclusion, omissions, and prohibited claims | External review |
| --- | --- | --- | --- | --- | --- | --- |
| `semir-dev-01-economy-funding-stages` | Multiple stages in one episode | H.R. 5371 sources; rolls 281/285 in `government_funding_hr5371` | F000477 Nay/Nay | trajectory → `policy_trajectories`; stage limit → `meaningful_limitations` | Lead with bounded two-stage trajectory; omit repeated/notable; no motive, movement, or parent-measure inference | Same episode? Is stage distinction analytically material? |
| `semir-dev-02-economy-uniform-no-throughline` | Uniform direction without common throughline | Six actions in four independent Economy episodes; no family asserted | F000477 six Nay | uniform direction → `repeated_patterns`; no-throughline limit → `meaningful_limitations` | State direction only; omit notable; no invented agenda, motive, or trajectory | Is direction material without a common trait? |
| `semir-dev-03-economy-noncounting-boundaries` | Known Not Voting; procedural and mixed controls | Roll 310 substantive episode; rolls 263/180 context-only | F000477 Not Voting, plus two controls | coverage boundary → `coverage`; controls create no propositions | Exact coverage; controls stay in method; omit all substantive sections; no direction from non-counting rows | Is coverage alone sufficient? Should control exclusions remain method only? |
| `semir-dev-04-justice-mixed-fentanyl-trajectory` | Mixed direction within one episode | Rolls 32/33/166 in `halt-fentanyl-legislative-path` | F000477 Yea/Nay/Yea | trajectory → `policy_trajectories`; change-claim limit → `meaningful_limitations` | Preserve stage distinctions; omit repeated; no motive or personal evolution | Does the trajectory preserve each legislative stage? |
| `semir-dev-05-justice-mechanism-divide` | Repeated independent patterns and mechanism divide | Seven actions in five Justice episodes | F000477 Yea/Nay/Yea/Nay/Yea/Nay/Nay | two patterns → `repeated_patterns`; divide → `meaningful_limitations` | Retain both patterns and bounded distinction; no ideology, motive, or causality | Are both patterns defensible? Is the divide primary or limiting? |
| `semir-dev-06-justice-one-sided-argument` | Single action; one-sided official argument evidence | Roll 131 in `officer-safety-data-reporting` | F000477 Yea | notable choice → `other_notable_choices`; source boundary → `meaningful_limitations` | Disclose source boundary; omit trajectory/repeated; no balanced-debate or motive claim | Is the missing opposing argument analytical or source-detail only? |
| `semir-dev-07-environment-exact-action-gate` | Exact-action versus parent-package eligibility | Roll 6 accepted into appropriations episode; roll 5 rejected | A000372 Yea on accepted action | notable choice → `other_notable_choices` | Use exact-action basis; omit repeated/trajectory; no inherited eligibility or single-action trajectory | Are rolls 5 and 6 correctly separated? |
| `semir-dev-08-environment-separate-family-episodes` | Separate proposals within families; mechanism divide | Four episodes in mineral-supply and home-energy families | C001059 Yea/Yea/Nay/Nay | two patterns → `repeated_patterns`; divide → `meaningful_limitations` | Keep four episodes distinct; omit trajectories; no family-as-episode collapse or ideology | Are episodes independent? Are families comparable enough for a divide? |
| `semir-dev-09-not-voting-heavy-record` | Not Voting-heavy known evidence | Seven actions in six episodes/two families | H001095 five Not Voting, two Yea | coverage boundary → `coverage` | Exact coverage only; omit repeated/trajectory; no nonvote-as-opposition or unknown-evidence wording | Should coverage prevent a substantive conclusion? |
| `semir-dev-10-present-known-coverage` | Present as known non-directional evidence | Seven actions in six episodes/two families | D000230 six Yea, one Present | direction → `repeated_patterns`; Present boundary → `coverage` | Describe six directional actions; omit trajectory; no Present-as-direction or seven-action support claim | Is the direction proposition valid with Present excluded? |
| `semir-dev-11-tied-pattern-ownership` | Tied patterns, deduplication, shared pending relationship | Six episodes/two families; shared trait contract | M001231 Yea/Yea/Nay/Nay/Nay/Nay/Yea | two patterns → `repeated_patterns`; shared limit → `meaningful_limitations` | Retain both tied patterns; omit notable; no silent omission or duplicate ownership | Are both material? Does the limit constrain both? Is novelty reviewed once? |
| `semir-dev-12-identity-title-order-invariance` | Identity, title, and order invariance | Stable action/episode/family IDs; mutation evidence | F000466 R and M001214 D have identical vectors | one deduplicated pattern → `repeated_patterns`; boundary → `meaningful_limitations` | Same graph for same evidence; no party- or title-derived meaning | Do identity and ordering leave the graph unchanged? |

The JSON review packet provides the exact evidence references, proposition IDs,
relationships, conclusion IDs, omissions, and prohibited claims for every row.

## Held-out inputs

Held-out files intentionally contain no proposed graph, section ownership, or
conclusion.

| Case | Input-only question |
| --- | --- |
| `semir-held-01-partial-service-missing-evidence` | Distinguish unresolved missing evidence from verified outside-service status while stating exact known coverage. |
| `semir-held-02-source-conflict-unsupported` | Route a known action whose interpretive claim lacks adequate or consistent authoritative support. |
| `semir-held-03-title-order-invariance` | Identify what remains stable under reordered inputs, opaque titles, and identity changes. |
| `semir-held-04-cross-domain-final-passage` | Bound cross-domain final-passage eligibility without parent-package inheritance. |

## Cross-case review questions

- Is the proposition type set expressive enough without embedding prose?
- Should a mechanism divide be a primary conclusion proposition, a limiting
  proposition, or context determined by its supporting pattern strength?
- When does a fully known but non-directional coverage boundary prevent a
  substantive conclusion rather than merely qualify it?
- Which trait relationships are stable shared semantics, and which require a
  one-time human exception before candidate generation?
- Are conclusion relevance and section ownership sufficiently independent to
  prevent duplicate presentation while preserving tied material patterns?

## Gate

External semantic review is required before any candidate can move to a
separate acceptance gate. This milestone does not authorize runtime adoption,
persistence, population generation, promotion, or publication.
