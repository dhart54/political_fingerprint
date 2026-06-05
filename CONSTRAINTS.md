# CONSTRAINTS.md — System Invariants and Non-Negotiable Rules

This document defines hard invariants that MUST NEVER be violated.

These constraints override implementation convenience.

If a requested change would violate these constraints, Codex must STOP and ask for clarification.

---

# Section 1 — Determinism Requirement (Absolute)

All computed outputs must be deterministic functions of stored database inputs.

The following must NEVER use LLM inference:

- vote eligibility
- vote classification
- evidence tier assignment for recorded governing behavior
- fingerprint calculation
- chamber median calculation
- drift calculation

These must be reproducible exactly from database state.

Allowed LLM usage:

- summary and explainer drafting ONLY
- summaries and explainers must be cached
- summaries and explainers must not influence any computed metric
- LLM text MUST NOT decide vote eligibility, domain classification, vote meaning, evidence tier, alignment, or recommendations

---

# Section 2 — Fingerprint Mathematical Definition (Invariant)

Fingerprint is defined as:

For legislator L over window W:

Let:

eligible_votes = all votes where vote_classifications.is_eligible = true

For each domain D:

domain_vote_count(L,D,W) =
count of eligible votes cast by L in domain D during W

total_votes(L,W) =
sum over all domains of domain_vote_count(L,D,W)

Fingerprint share:

vote_share(L,D,W) =
domain_vote_count(L,D,W) / total_votes(L,W)

If domain_vote_count = 0:

vote_share MUST equal 0 exactly.

vote_share MUST NEVER be null.

vote_share MUST NEVER be omitted.

vote_share MUST NEVER be normalized against anything except total_votes.

---

# Section 3 — Eligibility Constraint

A vote MUST be excluded if procedural.

Procedural votes MUST NOT appear in:

- fingerprints
- drift
- medians

Procedural determination must be deterministic and versioned.

vote_classifications.is_eligible is authoritative.

---

# Section 4 — Domain Constraint

Each eligible vote MUST have exactly one primary_domain.

primary_domain MUST be one of the issue_domain enum values.

primary_domain MUST NOT be null for eligible votes.

Ineligible votes MUST NOT have primary_domain.

---

# Section 5 — Drift Mathematical Definition (Invariant)

Window W is split into:

early_window = older half of W
recent_window = newer half of W

Compute share vectors:

P_early[D]
P_recent[D]

Drift is defined as:

drift = 0.5 × sum over domains D of abs(P_recent[D] − P_early[D])

Drift MUST satisfy:

0 ≤ drift ≤ 1

If total eligible votes in W < 20:

drift MUST be marked insufficient_data

drift MUST NOT be estimated or extrapolated.

---

# Section 6 — Chamber Median Definition

For chamber C and domain D:

Collect all legislators in chamber C with total_votes ≥ minimum threshold.

Compute:

median_share(C,D) =
median of vote_share(L,D) across legislators L

Median MUST be computed independently for:

- all legislators
- Democrats
- Republicans

Median MUST be precomputed and stored.

Median MUST NOT be computed at request time.

---

# Section 7 — Precomputation Requirement

The following MUST be stored in database tables:

- fingerprints
- chamber_medians
- drift_scores
- vote_classifications
- summaries
- vote_interpretations

API endpoints MUST read from these tables only.

API endpoints MUST NOT compute shared metrics dynamically.

User-specific alignment may be computed at request time ONLY as a lightweight comparison between:

- explicit user-selected preferences
- precomputed vote_interpretations
- stored votes_cast positions

This exception exists because user preferences are session inputs. The endpoint MUST NOT perform vote classification, vote interpretation, or heavy aggregation at request time.

---

# Section 8 — Versioning Requirement

The following MUST include version identifiers:

vote_classifications.classification_version
summaries.classification_version

If classification_version changes:

fingerprints MUST be recomputed
drift_scores MUST be recomputed
summaries MUST be regenerated

---

# Section 9 — Null Handling Constraint

The following MUST NEVER be null:

fingerprints.vote_share
fingerprints.vote_count
fingerprints.total_votes

If no votes exist:

vote_count MUST be 0
vote_share MUST be 0

---

# Section 10 — Time Window Constraint

Fingerprint window MUST be exactly:

rolling 730 days from computation timestamp.

Drift window split MUST be exactly:

early: older 365 days
recent: newer 365 days

No alternative window definitions allowed.

---

# Section 11 — API Contract Stability Constraint

The following API endpoints MUST remain stable:

GET /legislators/{id}/fingerprint
GET /legislators/{id}/drift
GET /legislators/{id}/summary
GET /lookup/zip/{zip}

Response field names MUST NOT change without explicit approval.

---

# Section 12 — Cost Constraint

The system MUST prefer:

precompute once → read many times

The system MUST avoid:

per-request heavy computation

The system MUST remain operable under $50/month hosting cost.

---

# Section 13 — Summary Neutrality Constraint

Summary, explainer, and alignment language MUST NOT include:

corrupt
extreme
radical
worst
best
biased
bought

Language MUST be descriptive only.

Language MUST NOT imply causation.

Language MUST NOT rank legislators.

Language MUST NOT prescribe voting behavior, including:

- "vote for"
- "vote against"
- "should vote for"
- "should vote against"
- "support this candidate"
- "oppose this candidate"

Allowed alignment labels are limited to evidence terms such as:

- aligned
- not aligned
- mixed
- insufficient evidence

Alignment labels MUST refer to the user's stated preferences and the available voting record, not to moral quality or electoral worthiness.

---

# Section 14 — Schema Integrity Constraint

Tables:

fingerprints
chamber_medians
drift_scores
vote_classifications

are authoritative outputs.

Other tables MUST NOT duplicate these values.

---

# Section 15 — Failure Behavior Constraint

If required inputs are missing:

System MUST return:

- insufficient_data status

System MUST NOT estimate missing values.

System MUST NOT fabricate data.

---

# Section 16 - Vote Interpretation Constraint

Vote interpretation records MUST be deterministic and source-grounded.

For each interpreted roll call, store:

- roll_call_id
- support_position, when determinable
- oppose_position, when determinable
- interpretation_status
- interpretation_reason
- source_url or source reference, when available
- classification_version or interpretation_version

If yea/nay meaning is ambiguous:

- interpretation_status MUST be insufficient_evidence or ambiguous
- alignment MUST NOT count the vote as aligned or not aligned

---

# Section 17 - User Alignment Constraint

User alignment MUST be computed only from:

- explicit user preference inputs
- eligible classified votes
- stored vote_interpretations
- stored vote positions

Alignment MUST NOT:

- rank legislators globally
- create a composite influence score
- infer motives
- infer causality
- tell the user how to vote
- compare users to other users

Alignment MUST expose enough evidence for a user to inspect why a label was shown.

Alignment language such as aligned or not aligned may be used only when the user has selected an explicit directional preference.

When no directional preference is selected, the product MUST use neutral record/evidence language such as:

- selected issue records
- reviewed records
- evidence available
- insufficient evidence

No-preference states MUST NOT imply the product has determined alignment or misalignment.

---

# Section 18 - Candidate Evidence Tier Constraint

Candidate and race expansion MUST preserve the evidence ladder:

1. recorded governing behavior
2. institutional record
3. sourced stated positions
4. insufficient evidence

Recorded votes and official actions are the highest-confidence evidence.

Stated positions from campaign websites, questionnaires, debates, interviews, or public statements MUST be labeled as stated positions and MUST NOT be presented as equivalent to recorded governing behavior.

Candidate comparison MUST NOT:

- rank candidates
- declare a winner
- prescribe voting behavior
- hide source confidence
- merge stated positions into vote-based alignment math

Every candidate claim MUST be traceable to a source URL or explicit source reference when available.

---

# Section 19 - Readiness-First Evidence Constraint

Readiness labels are evidence-confidence / presentation labels, not ideology labels.

Allowed readiness labels:

- Strong Evidence
- Mixed But Interpretable
- Limited Evidence
- Not Enough To Summarize

Readiness labels MUST be based on available reviewed evidence, interpreted vote counts, limited/ambiguous/insufficient rows, and not-voting treatment.

Readiness labels MUST NOT imply comprehensive coverage of every possible vote.

Highest vote volume MUST NOT be treated as equivalent to clearest reviewed vote meaning.

The product MUST distinguish "most recorded votes" from "clearest reviewed issue read" when they differ.

Limited or not-ready issue areas may remain visible, but MUST NOT receive confident issue-pattern summaries.

Readiness labels MUST NOT change support/opposition counting, alignment logic, vote interpretation status, or classification math.

---

# Section 20 - Evidence Confidence Label Constraint

Card-level confidence labels are presentation labels only.

Allowed labels include:

- Reviewed meaning
- Limited context
- Needs source support
- Not counted

Reviewed meaning may be shown only when source-grounded vote meaning is available.

Limited context must be used for procedural, amendment, or limited-source rows where practical policy effect is not fully supported.

Needs source support must be used when the row lacks enough source detail for confident interpretation.

Not counted must be used for rows that do not count toward support/opposition due to not-voting, ambiguity, insufficiency, or procedural status.

Confidence labels MUST NOT upgrade a row's interpretation status.

Confidence labels MUST NOT cause ambiguous, insufficient, procedural, or not-voting rows to count as support/opposition.

---

# Section 21 - Grouped Evidence Constraint

Grouped evidence is for scanability only.

Grouping MUST NOT change:

- support/opposition counts
- alignment labels
- vote interpretation status
- eligibility
- domain classification
- fingerprint/drift/median calculations

Grouping should use stable bill/measure identifiers first.

Normalized title or measure text may be used as a fallback.

Broad issue domain or issue_facet alone MUST NOT be used as the sole grouping key.

Procedural, amendment, or limited-context groups MUST NOT be presented as final policy claims unless source support exists.

Group labels must remain cautious when the underlying rows are mixed, procedural, or limited-source.

If grouping label confidence is weak, the UI should prefer cautious wording or expose the rows without over-summarizing.

---

# Section 22 - Chamber Consistency Constraint

Evidence rows for a legislator MUST match the legislator's chamber.

House members MUST NOT receive Senate roll-call evidence rows.

Senators MUST NOT receive House roll-call evidence rows.

Any fixture, seed, ETL, or review-bundle data that intentionally uses synthetic cross-chamber examples MUST clearly label them as synthetic and non-representative-specific.

Production/API evidence endpoints should rely on valid votes_cast links and should eventually enforce or validate legislator.chamber == roll_call.chamber.

Chamber mismatch must be treated as a data-integrity error, not a frontend copy issue.

---

# End of CONSTRAINTS.md
