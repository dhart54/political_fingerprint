# Accessibility and Mobile Checklist

Use this checklist for the Frontend Pass A voter journey.

## Required flow

1. Open `/` and confirm the finder is the only primary task.
2. Search by ZIP or representative name.
3. Select a representative and verify focus moves to the representative name.
4. Change Congress scope and confirm the label, evidence, and URL update.
5. Change issue discovery order and open an issue.
6. Verify focus moves to the selected issue heading.
7. If reviewed analysis exists, follow a finding to an exact receipt and clear
   the highlight.
8. Filter, expand, collapse, and progressively disclose the chronological
   ledger.
9. Use Back, Forward, and refresh to verify route restoration.

## Keyboard and screen reader checks

- Every input, button, link, filter, card action, episode, and receipt is
  reachable in visible order.
- ZIP/name forms submit with Enter.
- Toggle controls expose `aria-pressed`; the selected issue exposes
  `aria-current`; disclosure controls expose `aria-expanded`.
- Search loading, empty, success, and failure states are announced.
- Representative and issue selection transfer focus without trapping it.
- Finding controls have specific accessible names and move focus to the exact
  canonical receipt.
- Reduced-motion preference prevents smooth scrolling.
- Status and vote states remain understandable without color.
- Receipts expose date, chamber, roll number, position, evidence state, exact
  meaning when supplied, source links, and limitations.

## Responsive and zoom checks

Check at 1440, 1024, 390, and 320 pixels, plus 200% browser/CSS zoom. Verify:

- no horizontal overflow;
- issue cards render 4/2/1 columns at their intended breakpoints;
- long titles, URLs, metadata, filters, and status labels wrap;
- controls keep at least a 44-pixel target size;
- the sticky section navigation does not cover focused headings;
- receipt expansion remains readable and does not obscure the full ledger; and
- desktop reading width and mobile spacing preserve the same hierarchy.

## Current Pass A QA note

Automated browser coverage exercises the finder, URL/history state, issue
sort/filter modes, governed sample analysis, Congress scope boundaries,
receipt highlighting, progressive disclosure, one-at-a-time expansion,
episode ordering, the four required widths, keyboard focus, reduced motion,
and 200% zoom. The removed `/golden-render-fixture` route is also required to
return 404. A local in-app browser review also confirmed the finder, selected
overview, issue/ledger hierarchy, absence of horizontal overflow, and a clean
console before handoff.
