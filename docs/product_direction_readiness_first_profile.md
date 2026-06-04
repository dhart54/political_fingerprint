# Readiness-First Accountability Profile

## Product Framing

This product is an evidence-based accountability profile, not a full ideology score.

The representative page should lead with the issue areas where reviewed voting evidence is strongest and most useful for a voter to inspect. Strong issue reads should explain what the reviewed measures were about, how the representative voted, and what a voter can reasonably take away from the record.

Limited evidence should stay visible, but it should not be over-summarized. Rows with ambiguous, procedural, insufficient, or not-voting context should help users see the limits of the record rather than being forced into a confident pattern.

## User Promise

In 60 seconds, understand where your representative's reviewed voting record is clearest, where evidence is mixed, and where the record is too limited to summarize confidently.

## Representative Page Hierarchy

1. Best issue reads
2. Mixed but interpretable
3. Limited evidence
4. Not enough to summarize
5. Evidence cards and sources

## Issue Section Hierarchy

1. Bottom line
2. What these votes were about
3. How the representative voted
4. How a voter might read that
5. Limits
6. Grouped evidence

## Readiness Labels

### Strong Evidence

The issue section has enough reviewed, source-grounded Yes/No vote meaning to support a clear issue-level read. Limited or not-voting rows may still appear, but they do not dominate the section and are not forced into the summarized pattern.

### Mixed But Interpretable

The issue section has enough reviewed vote meaning to describe the record, but the representative's interpreted votes do not point in one simple direction. The section should explain the mix without turning it into a broad ideology claim.

### Limited Evidence

The issue section contains some useful reviewed rows, but ambiguous, procedural, insufficient, or not-voting rows materially limit how confidently the product can summarize the pattern. The section should remain visible and cautious.

### Not Enough To Summarize

The issue section does not have enough source-grounded interpreted vote meaning for a reliable issue-level read. The product may show available evidence rows and source links, but should not present a bottom-line pattern.

## What Not To Build Yet

- No personalized alignment quiz yet.
- No broad ideology score.
- No source enrichment implementation yet.
- No automated LLM interpretation rollout yet.

## How This Guides Future Work

Guardrails and readiness come before source enrichment implementation. The product should first make clear which issue sections are safe to summarize, which are limited, and which should remain evidence-only.

Source enrichment should move rows from insufficient or contextual into stronger reviewed evidence when source material supports a practical vote meaning. Enrichment should improve readiness; it should not manufacture confidence.

LLM interpretation should draft inside confidence and readiness constraints. It may help produce plain-language text for reviewed source-grounded rows, but it should not decide eligibility, alignment, vote meaning, or whether a section is ready to summarize.
