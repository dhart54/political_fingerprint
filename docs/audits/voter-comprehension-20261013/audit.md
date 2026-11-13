# Live voter-comprehension audit — 2026-10-13

Read-only expert heuristic assessment of the current public Political Fingerprint journey. No product edits, commits, merges, publication changes, deployments, contact submissions or outgoing contact messages. Repository implementation and editorial state are unchanged.

## Scope and limits

Existing installed Windows headless Chromium/Playwright, authorized by parent after native/browser surfaces were unavailable. Desktop 1440×900 and narrow 390×844; actual live public responses, no fixture responses. A request guard aborted non-GET/HEAD requests; none were attempted. This is not the user's Chrome profile, a physical phone/IME test, a human study, or evidence that users can understand the record within 60 seconds. Automation/harness durations are not human task times. The earlier browser-choice question is resolved by the supplied headless instruction and is non-blocking; no card-dismissal API is exposed.

Tested a ZIP example (27701, not the user's location), Valerie P. Foushee's published War Powers finding in Congress119, and Thomas Massie's receipts-only/missing-contact path in Congress119. Some intermediate screenshots captured loading states; only the settled evidence specified below supports conclusions. The Clerk source's first popup request was not captured by the late popup observer; no measured-referrer claim is made for that request.

## Three prioritized gaps

### 1. Known bill number can miss an already loaded exact receipt — recommended next increment

Starting at the [Foushee War Powers supporting receipts](https://political-fingerprint.vercel.app/?representative=leg_valerie_p_foushee&scope=119&issue=NATIONAL_SECURITY_FOREIGN&finding=wording%3Asynthesis%3Awar-powers&source=4efd82dad8ce77dd267d152e57634e1a41a4a1fdaa1ca466511539438351bc04&view=receipts#vote-record), expand House Roll282. The receipt states H.Con.Res.89. Enter `H.Con.Res. 89` into “Filter loaded receipts by measure, roll or title”: zero of nine loaded linked receipts match. Enter `roll 282`: the matching receipt appears. Reproduced at both widths.

Evidence: `07-known-measure-no-match-desktop.png`, `08-roll-search-success-desktop.png`, `12-known-measure-no-match-mobile.png`, and command/DOM history in `audit-steps.json`. The [official Clerk XML](https://clerk.house.gov/evs/2026/roll282.xml) identifies Congress119/session2/roll282, H CON RES89, On Agreeing to the Resolution, July23,2026, and Passed. Screenshot `06-official-source-desktop.png` shows the live primary source. The individual Foushee XML row was not independently inspected.

Implementation evidence: `frontend/lib/localRecordFilter.mjs` indexes the printed action title, parent measure, chamber and roll, rather than `bill_id` or hidden interpretation text. This observed gap follows that approved contract; it is not evidence of a regression in literal matching. The exact bill number is present in expanded meaning but absent from the indexed row header.

Next coherent engineering increment: verify the canonical/API exact-measure identifier contract, render that sourced identifier alongside the existing receipt title/type, and include the same visible identifier in the local filter. Require exact Congress/measure identity and preserve existing order, linked accounting, Vote/Type intersection, source links, local-only querying and history. If the identifier is absent or ambiguous upstream, stop at that boundary and propose the bounded identity-field contract rather than parse URLs, guess from parent context, or index all hidden prose. This audit does not authorize implementation.

### 2. ZIP entry leaves current representation unconfirmed without a verification path

At the [home page](https://political-fingerprint.vercel.app/), enter27701 and choose Find by ZIP. The result explicitly says “Lookup source needs confirmation,” explains that the lookup source date is not confirmed, and asks the user to confirm the representative before relying on it. Foushee, Budd and Tillis are offered as loaded records; statewide Senate handling is explained. Name search selects a record but does not independently verify residence/current district membership.

Evidence: settled desktop `02-zip-unconfirmed-desktop.png` and the ZIP DOM steps in `audit-steps.json`. Narrow `14-zip-result-mobile-arrival.png` shows the viewport still at the ZIP form, with the result below the fold. The follow-up `15-zip-unconfirmed-mobile.png` captured unsettled scrolling and is not stable layout evidence.

Impact: the honest warning protects against false certainty, but the core “Who represents me?” task remains incomplete for this example. This is not evidence that the listed representatives are wrong.

Next product/data increment: a source-backed current-representation verification path, with explicit lookup provenance/date and address-versus-ZIP limitations. Preserve the uncertain state until authoritative evidence supports confirmation. Do not fix this by removing the warning or labeling a loaded record as the user's current representative. Currentness/district mapping requires an upstream provenance decision; layout feedback can be evaluated separately.

### 3. Missing contact details end the optional neutral next step

Open [Massie Congress119 Economy & Taxes](https://political-fingerprint.vercel.app/?representative=leg_thomas_massie&scope=119&issue=ECONOMY_TAXES), expand House Roll164, then choose Official contact information. The settled panel says “Contact details are not loaded for this record.” It offers a close control but no official directory/verification exit or other contact route.

Evidence: settled `17-massie-contact-missing-mobile.png` and `18-massie-contact-missing-desktop.png`, DOM in `audit-steps.json`, and GET `/legislators/leg_thomas_massie/contact` with only the site-origin referrer. The final desktop capture was taken after the explicit missing-data text appeared and was visually inspected; its earlier loading capture is not evidence of absence. No contact submission or external contact link was activated.

Impact: the missing-data language is correct, but a person ready to act has no supported next step through this panel. This is a data-availability/product gap, not grounds to invent an email, website or phone number.

Next bounded increment: review a neutral, source-backed official-directory fallback for unavailable contact data, preserving the missing status and member identity. Any stored-contact ingestion/provenance or fallback policy requires its own authorized scope. Do not transmit vote/finding context in external links.

## Behaviors that support the one-minute goal

| Task | Live observation | Evidence |
| --- | --- | --- |
| Select person and session | Foushee and Massie show chamber/state/district/party plus selected Congress; scope controls say recorded actions do not imply methodological review. ZIP currentness remains explicitly uncertain. | `03-foushee-overview-desktop.png`, `16-massie-overview-mobile.png`, `19-massie-overview-desktop.png` |
| Read a bounded finding | War Powers detail states support across Iran/Lebanon/Venezuela and visible qualifications: wording, dates and House sessions differ; it does not establish a position on every intervention/authorization. Narrow layout fits the finding, qualifications and receipt CTA. | `04-finding-desktop.png`, `11-finding-mobile.png` |
| Reach exact receipt and source | See9Housevotes leads to the nine linked receipts. House119/session2/roll282 expands the exact action and result, and Official vote opens real Clerk XML. Legislative-actions API key warning remains truthful. | `05-supporting-receipts-desktop.png`, `06-official-source-desktop.png` |
| Distinguish missing review from inactivity | Massie says no reviewed findings are available and directs users to issue vote records. His selected Economy issue shows19 recorded actions,12 substantive Yea/Nay receipts, and no issue summary for the scope. Procedural/context and unresolved rows remain marked. | `16-massie-overview-mobile-full.png`, `19-massie-overview-desktop-full.png`, DOM log |
| Take optional official contact step when data exists | Foushee's panel includes stored phone, official website/contact form, source and retrieved date2026-05-19. Links use noopener/noreferrer and no-referrer with no vote/finding query appended. No contact link was activated. | `09-contact-loaded-desktop.png`, `13-contact-loaded-mobile.png` |

The Clerk XML is technically readable rather than an ordinary voter explanation; source reachability is established, human source-verification comprehension is not. No broad stance, motive, ideology, voting recommendation or claim of actual troop withdrawal was added by this audit.

## Reserved boundaries and delivery

Product North Star supplies the practical identification/evidence/neutral-action goal; historical roadmap features are not automatically current defects. Interpretation principles preserve bounded findings, exact actions and qualifications. `docs/workflows/editorial-issue-frontend.md` explicitly says the API does not emit expected-but-missing actions or service-status absence rows, and React must not synthesize them. Do not turn absence of reviewed findings into inactivity, reconstruct missing events in React, revise accepted claims, or change counting/eligibility/publication to fill these gaps.

Recommended next increment is gap1 only, after identity-contract inspection and specific authorization. ZIP provenance and contact fallback are separate product/data decisions. No PR193, Immigration, Education activation or validation-only PR209 work occurred. Historical PR203–208 integration is complete and was not reexecuted. Parent message delivery through `send_message_to_thread` returned thread-not-found; commentary and this report preserve progress, and the final response provides automatic delivery. No audit access blocker remains.

Raw evidence: `audit-steps.json` contains93 command observations,84 request observations, zero blocked write attempts, zero page errors and zero observed horizontal overflow. It includes URLs, controls, source links, receipt IDs and viewport state. `audit-phase1.json` retains pre-popup-restart history. Four harness-only command errors (exact-name mismatch, receipt wait, early popup bookkeeping and one contact-toggle wait) are excluded from product/performance conclusions; initial launch API repair occurred before live observations. The owned headless browser closed successfully at completion; all artifacts remain in this Temp directory. The implementation worktree `.w/ls` remains clean for tracked files. Unrelated root/worktree state was preserved.
