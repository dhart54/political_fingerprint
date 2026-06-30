# Interpretation Principles

Political Fingerprint is a plain-English voting-record interpreter with receipts.

The product should help users understand what an elected official has done in the reviewed voting record. It should not require users to read every bill, group every vote, and draw every conclusion on their own. The app should make clear, evidence-backed interpretations, then show the proof.

Political Fingerprint is not a raw vote archive, a partisan scorecard, a recommendation engine, or a moral ranking system.

## Core Product Standard

Use clear interpretation backed by reviewed evidence.

Do not use charged language, moral judgment, motive claims, unsupported ideology labels, or unsupported cross-time movement claims.

The product should be able to say:

> In this reviewed sample, this representative mostly opposed Republican-led national-security and defense measures.

The product should not say:

> This representative is anti-national-security.

The difference is specificity. The first claim is tied to reviewed votes, named measure types, and a bounded sample. The second turns voting behavior into a broad character or values judgment.

## Product Promise

Political Fingerprint should answer:

1. What was the measure about?
2. How did the representative vote?
3. How did most of their party vote?
4. Was this vote typical or notable compared with party alignment?
5. What pattern appears across reviewed votes?
6. How strong is the evidence?
7. Where are the receipts?

The user-facing order should usually be:

1. Finding
2. Plain-English explanation
3. Evidence counts
4. Party and vote-context
5. Receipts
6. Limits and caveats

Avoid leading with methodology unless the user is in a methodology or source-detail view.

## Evidence-Backed Interpretation

The app may interpret voting behavior when the interpretation is grounded in reviewed vote evidence.

Allowed interpretation examples:

- “In this reviewed sample, the representative mostly voted against these measures.”
- “The clearest reviewed evidence is in National Security & Foreign Policy.”
- “The reviewed record shows repeated opposition to this set of Republican-led defense and national-security measures.”
- “This issue area is mixed but interpretable.”
- “The record is not one-directional.”
- “Most of these votes matched most Democrats.”
- “This vote stood apart from most of the representative’s party.”
- “The vote record alone does not show motive.”

Disallowed interpretation examples:

- “This representative is good for national security.”
- “This representative is bad on the border.”
- “This representative does not care about veterans.”
- “This representative is corrupt.”
- “This representative betrayed voters.”
- “This representative is extreme.”
- “This proves the representative changed position.”
- “This proves the representative’s motive.”
- “This predicts how the representative will vote in the future.”

## Interpret the Measure, Not the Slogan

Interpretation should be tied to the specific measure or policy object.

Good:

> Voted against this bill to limit federal banking regulators’ authority.

Risky:

> Voted against financial stability.

Good:

> Voted for this amendment restricting funds for Ukraine assistance.

Risky:

> Voted against Ukraine.

Good:

> Mostly opposed Republican-led immigration enforcement measures in this reviewed sample.

Risky:

> Opposes border safety.

Good:

> Mostly opposed Republican-led national-security amendments in this reviewed sample.

Risky:

> Opposes national security.

When possible, name the concrete policy action: authorize, restrict, fund, prohibit, repeal, regulate, require, report, investigate, amend, or pass.

## Party Context

Party context is essential. A vote is easier to understand when users know whether it matched or departed from most of the representative’s party.

The app may say:

- “Most Democrats opposed this measure.”
- “Most Republicans supported this measure.”
- “The representative’s vote matched most Democrats.”
- “The representative’s vote stood apart from most Democrats.”
- “This was a notable party break.”
- “This was not a clean party-line vote.”

The app should avoid implying motive from party breaks.

Do not say:

- “This party break proves conviction.”
- “This vote shows true beliefs.”
- “This was political courage.”
- “This was betrayal.”

Safer wording:

> Party breaks are useful to inspect because party alignment alone does not explain the vote.

## Findings

A finding is a user-facing interpretation backed by reviewed evidence.

A strong finding should include:

1. A specific policy area or measure type.
2. A direction of voting behavior.
3. A reviewed evidence basis.
4. Party or chamber context where available.
5. A clear path to receipts.
6. A bounded statement of what is and is not being claimed.

Recommended finding structure:

```text
Finding:
In this reviewed sample, Foushee mostly opposed Republican-led national-security and defense measures.

Why we say that:
22 supported / 128 opposed across 150 reviewed Yes/No votes.

Party context:
Most of these votes matched most Democrats.

Examples:
Defense authorization amendments, foreign military assistance restrictions, and national-security policy measures.

Receipts:
Show votes.

Limit:
This describes the reviewed vote sample, not motive or a broad claim about all national-security policy.
```

## Caveat Placement

Caveats are important, but they should not overwhelm the user.

Use this principle:

> Clear finding first. Receipts always available. Limits shown once per claim type, not repeated everywhere.

Avoid repeating “what this does not prove” on every card. Repetition makes the product feel defensive and academic.

Preferred caveat locations:

- one “How to read this” or “Limits of this read” note near a major section;
- source, caveat, and full-context drawers at the vote level;
- methodology pages;
- one concise boundary line when a claim type is introduced.

Do not remove boundaries entirely. Consolidate them.

## Bounded Phrases

Use bounded phrases to keep interpretation disciplined without overloading the UI with caveats.

Preferred phrases:

- “In this reviewed sample...”
- “Across reviewed Yes/No votes...”
- “On these measures...”
- “In this set of votes...”
- “The reviewed record shows...”
- “The vote record alone does not show motive.”
- “This does not describe every possible issue in this policy area.”

Avoid overusing:

- “This does not prove...”
- “What not to infer...”
- “This is not a broad claim...”
- “Caution...”
- “Limited context...”

These phrases can appear, but should not dominate top-level product copy.

## Confidence and Evidence Strength

The app should distinguish between strong, mixed, limited, and non-interpretable evidence.

Useful labels:

- “Strong reviewed sample”
- “Mixed but interpretable”
- “Limited reviewed evidence”
- “Not enough reviewed evidence”
- “Mostly supported”
- “Mostly opposed”
- “Split record”
- “Party-aligned vote”
- “Notable party break”

Avoid labels that imply value judgment or unsupported ideology:

- “good”
- “bad”
- “extreme”
- “moderate”
- “weak”
- “strong leader”
- “principled”
- “dishonest”

## Cross-Congress Interpretation

Do not claim cross-time change, movement, drift, consistency, or trend unless the reviewed evidence supports direct comparison.

Avoid:

- “changed”
- “shifted”
- “moved toward”
- “moved away from”
- “trend”
- “drift”
- “steady”
- “consistent with prior Congress”
- “less one-directional”

Safer alternatives:

- “Reviewed votes are available in both Congresses.”
- “Congress-specific counts are shown separately.”
- “This family has reviewed vote evidence in both the 118th and 119th Congresses.”
- “The app places the evidence side by side; it does not infer a change in position.”

## Vote-Level Receipts

Every important interpretation should lead to receipts.

Receipt views should show:

- roll call number;
- date;
- vote type;
- measure name;
- primary purpose;
- representative vote;
- party vote context;
- final House outcome where available;
- source link;
- caveats and full context.

Vote-level detail can be more technical than top-level findings, but should still prioritize plain English.

## Manual Interpretation Guidance

When manually interpreting a bill, amendment, or vote family:

1. Identify the measure’s primary purpose.
2. Identify the concrete policy action.
3. Identify whether the vote was final passage, amendment, procedural, messaging, or limited-context.
4. Identify the representative’s vote.
5. Identify how most of the representative’s party voted.
6. Identify whether the vote matched or broke from most of the party.
7. Summarize only what the vote supports.
8. Avoid motive, moral judgment, and unsupported broad issue claims.
9. Preserve caveats in source detail or methodology, not every top-level sentence.

## Examples

### Good

> Foushee voted No on this Republican-led amendment to reduce funding for foreign assistance. Most Democrats also voted No. The amendment failed.

### Better

> Foushee opposed this Republican-led foreign-assistance funding restriction, matching most Democrats. The amendment failed.

### Too Broad

> Foushee opposed foreign aid accountability.

### Good

> In this reviewed sample, the representative mostly opposed Republican-led defense authorization amendments.

### Too Broad

> The representative is against defense.

### Good

> This vote stood apart from most Democrats and is worth inspecting separately.

### Too Broad

> This vote shows the representative’s true conviction.

## Operating Rule for Future Work

When adding or revising product copy, ask:

1. Is the claim understandable to a normal voter?
2. Is the claim grounded in reviewed evidence?
3. Is the policy object specific enough?
4. Are party and vote-type context included where useful?
5. Are receipts available?
6. Does the copy avoid moral judgment and motive claims?
7. Are limits available without overwhelming the user?

If the answer is yes, the product should make the interpretation clearly.
