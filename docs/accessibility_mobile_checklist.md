# Accessibility and Mobile Checklist

Use this checklist before sharing the site outside development. It is written for the voter journey, not just isolated components.

## Required Flow

1. Open the home page.
2. Read the hero coverage context.
3. Use a loaded ZIP suggestion.
4. Open the House profile.
5. Select at least one issue preference.
6. Inspect the alignment label evidence.
7. Open Quick Read vote evidence.
8. Compare House and senator records.
9. Search for a different legislator.

## Keyboard Checks

- Every input and button can be reached with `Tab`.
- Focus order follows the visible page order.
- ZIP lookup can be submitted with `Enter`.
- Issue cards can be selected, removed, and stance-switched without a mouse.
- Alignment `Inspect Votes` buttons open the evidence panel.
- Quick Read `Open Votes` buttons open the same evidence panel.
- Comparison left/right selection buttons announce their selected state.
- No keyboard trap appears inside the comparison search list or evidence panel.

## Screen Reader Checks

- ZIP input has an accessible name.
- Legislator search inputs have accessible names.
- Icon-like issue select/remove buttons have explicit labels.
- Toggle-style buttons expose selected state with `aria-pressed`.
- Status messages are understandable without relying on color alone.
- Evidence rows include roll call date, chamber, roll number, vote position, and classification reason.

## Mobile Layout Checks

Check at:

- 390 x 844
- 430 x 932
- 768 x 1024
- 1280 x 720

Verify:

- hero headline does not cover the ZIP lookup card
- ZIP form stacks cleanly
- loaded ZIP chips wrap without horizontal scrolling
- issue cards remain readable with stance buttons visible
- alignment cards do not overflow
- evidence rows wrap long bill titles and source URLs
- comparison cards stack before desktop width
- all button text fits without clipping

## Known Local Limitation

The Codex in-app browser currently blocks `localhost` and `127.0.0.1` in this thread with `ERR_BLOCKED_BY_CLIENT`, so this checklist has not been completed visually here. Until browser access is unblocked, use build checks plus manual browser review.

