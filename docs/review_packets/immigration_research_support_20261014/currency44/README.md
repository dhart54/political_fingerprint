# Roll2:44 currency diagnostic:24 extraction/parser failures explained

Research-only follow-up to [independently reviewed batch4](https://github.com/dhart54/political_fingerprint/blob/196c68a8d431c4a3f789e47a5536be2a97a58425/docs/review_packets/immigration_research_support_20261014/batch4/README.md). Source parent, selected-page strings, original diagnostics and prior views are reused at exact commit `196c68a8d431c4a3f789e47a5536be2a97a58425`; no new primary acquisition or restricted batch2 target was accessed. [PR198 research-only claim6194907777](https://github.com/dhart54/political_fingerprint/pull/198#issuecomment-6194907777) followed current ownership/branch checks. Sole writer was on234WRDA, with272/286next; no overlap on this exact diagnostic was observed. No private writer worktree access, message or interrupt.

## Finding and exact scope

The nine rejected literals were only part of the problem. The old regex also accepted **15partial numeric fragments** inside split extracted amounts. `1 5,000,000` became5,000,000; `2,000 ,000` became2,000; `82 0,000` became0. These are extraction-spacing/parser errors, not zero appropriations. Maximal numeric spans expose the full candidate token, but **do not authorize a normalized source or a transcription**. Each of the24affected Amount($) cells was separately read from a page image; literal text and reading remain distinct in [reviewed_rows.json](reviewed_rows.json). All24printed target amounts are legible. No column displacement or account-boundary error was observed in this checked set; no genuine printed-amount ambiguity remains among these24targets.

The helper retains all **989source row spans**, with the same account counts and page/row offsets as the legacy diagnostic. It preserves literal strings and flags absent, multiple, malformed, attached or divergent numeric runs. It requires a separate source-bound visual reading for changed/rejected values, rejects wrong columns or stale offsets/views, and retains disagreement as unresolved. It never chooses values to make an account balance. Output objects are independent copies; caller mutation cannot change the input fixtures or a later call. Code is isolated in this research directory, with no runtime/compiler/candidate import or registration.

## Target field ledger (dollars)

Row numbers are mechanical within each printed page; full project/account identity, source offsets and passage hashes disambiguate the exact row. **Column4 is Amount($)**, between Project and the House/Senate Requestor columns. Nine new3000pixel page views are supplied; pages250/260/262/264reuse the exact batch4views. All view identities are bound in the review JSON. No OCR or generative image alteration was used.

| PDF:start / printed page / table row | Project/recipient label | Literal extracted numeric span | Old diagnostic value | Separate visual reading |
| --- | --- | --- | --- | --- |
| 248:6519 / H1600 / row33 | Ilisagvik College | `2 50,000` | 50,000 | 250,000 |
| 250:5138 / H1602 / row28 | AIDS Resource Alliance | `37 5,000` | 5,000 | 375,000 |
| 251:5059 / H1603 / row26 | Bullhead City Fire District | `2 94,000` | 94,000 | 294,000 |
| 252:634 / H1604 / row3 | Circle the City | `84 0,000` | 0 | 840,000 |
| 252:4992 / H1604 / row27 | Community Dental | `2 ,334,000` | not parsed | 2,334,000 |
| 252:6203 / H1604 / row34 | Conway Medical Center | `1 ,410,000` | not parsed | 1,410,000 |
| 254:779 / H1606 / row4 | Grant County Courthouse | `310,0 00` | not parsed | 310,000 |
| 254:1891 / H1606 / row10 | Hale Makua Health Services | `1,850,00 0` | not parsed | 1,850,000 |
| 254:4845 / H1606 / row26 | Illinois Eye Institute | `750,00 0` | not parsed | 750,000 |
| 254:4988 / H1606 / row27 | Inspira Health Network | `2,000 ,000` | 2,000 | 2,000,000 |
| 254:6249 / H1606 / row34 | Ketchikan Gateway Borough | `347 ,000` | not parsed | 347,000 |
| 254:7062 / H1606 / row39 | Lawrence General Hospital | `1,36 7,000` | 7,000 | 1,367,000 |
| 255:3545 / H1607 / row17 | McDermott Center | `2 68,000` | 68,000 | 268,000 |
| 255:7055 / H1607 / row35 | Morrow County Health District | `6 52,000` | 52,000 | 652,000 |
| 258:6098 / H1610 / row32 | Union County Hospital Authority | `2,0 00,000` | 0 | 2,000,000 |
| 259:1572 / H1611 / row8 | University of Kentucky | `1 5,000,000` | 5,000,000 | 15,000,000 |
| 260:508 / H1612 / row2 | Versiti | `3,0 00,000` | 0 | 3,000,000 |
| 262:5860 / H1614 / row31 | Anchorage Coalition to End Homelessness | `4 50,000` | 50,000 | 450,000 |
| 263:2503 / H1615 / row14 | Easter Seals North Georgia | `7 67,000` | 67,000 | 767,000 |
| 263:6659 / H1615 / row39 | So What Else | `750,00 0` | not parsed | 750,000 |
| 264:2367 / H1616 / row13 | Westbay Community Action | `100,0 00` | not parsed | 100,000 |
| 264:4093 / H1616 / row24 | Denver Regional Council of Governments | `82 0,000` | 0 | 820,000 |
| 264:5842 / H1616 / row35 | Matrix Human Services | `1,0 00,000` | 0 | 1,000,000 |
| 268:1151 / H1620 / row7 | Rhode Island Marine Trade Association | `480,00 0` | not parsed | 480,000 |

## Checked arithmetic, without forced balancing

| IH branch | Same mechanical rows | Legacy diagnostic sum | Revised diagnostic sum | Delta from24visual readings |
| --- | --- | --- | --- | --- |
| P1 | 108 | 95,301,000 | 95,501,000 | 200,000 |
| P2 | 386 | 830,224,000 | 857,793,000 | 27,569,000 |
| P3 | 79 | 54,311,000 | 54,311,000 | 0 |
| P4 | 63 | 38,851,000 | 40,801,000 | 1,950,000 |
| P5 | 36 | 12,148,000 | 13,968,000 | 1,820,000 |
| P6 | 156 | 99,667,000 | 100,147,000 | 480,000 |
| P7 | 161 | 224,377,000 | 224,377,000 | 0 |

The revised total is **1,386,898,000**, from legacy1,354,879,000 plus the explicit **32,019,000** row-adjustment ledger. Arithmetic uses965unchanged mechanically agreeing fields plus24separate visual readings. **This is not all989-row visual certification.** Other source fields/rows have not gained a visual/semantic certificate merely because the totals agree.

The four initially unreconciled fixed IH branches P1/P2/P4/P5 now match their literal statutory amounts95,501,000 /857,793,000 /40,801,000 /13,968,000; P3remains54,311,000. These comparisons were made **after** transcription and summation and are absent from the helper's value-selection logic. [arithmetic.json](arithmetic.json) binds each comparison to the exact batch3IH witness/passage and carries the24-row adjustment ledger. P6/P7are derived table subtotals100,147,000 /224,377,000; no fixed IH CPF subtotal or fiscal/legal conclusion is invented for them.

## Reproduce and validate

From the repository root (no installation/new source acquisition):

```powershell
python -X utf8 -B docs/review_packets/immigration_research_support_20261014/currency44/test_diagnostic.py -v
python -X utf8 -B docs/review_packets/immigration_research_support_20261014/currency44/diagnose_currency.py --repo . --artifact-ref HEAD --without-reviews
python -X utf8 -B docs/review_packets/immigration_research_support_20261014/currency44/diagnose_currency.py --repo . --artifact-ref HEAD
```

The first CLI reports24unresolved target fields; the second verifies source-view identities and reproduces [diagnostic_report.json](diagnostic_report.json), resolving only those24fields through separate readings. Both use the identical196c68a8fixture/989rows and do not write inputs. Before commit use `--artifact-ref index` for the staged review/views. Requires ordinary Python/Git; the CLI uses standard-library code only. Source rendering/extraction versions/timing are separately disclosed; rendering is not rerun on every diagnostic call.

**15focused regression methods pass.** They reproduce nine rejections/15partial matches; retain ambiguity/missing reviews/disagreement; reject page/offset/account/column/image and duplicate mutations; preserve all row boundaries and inputs; and test nested output isolation. One stronger isolation probe failed and exposed a shallow-copy bug, repaired with independent output copies. The original failed tool/probe runs remain in [timing_and_validation.json](timing_and_validation.json). No candidate/full owner gate ran. `delivered_blobs.json` binds all other final Git blobs; final exact-head unit/CLI/report/blob checks and CI observation are in the handoff. No older restricted artifact is replayed for preservation.

## Residual decisions and stopping point

No targeted printed currency ambiguity remains, but965fields are mechanically carried, not newly visually reviewed. Prepared committee-version equivalence, §4/direct-appropriation interaction, recipient/program/beneficiary qualifications, fiscal effects and Immigration membership remain for the sole writer/reserved review. No candidate completion, interpretation, screening credit, publication or acceptance is supplied. The previous packet's limited failed diagnostic remains historical and unchanged, rather than silently rewritten.

The compact [PLAN](PLAN.md) bounds the work. First tool14:46:44UTC; timing includes ownership, claim, tool failures, visual inspection, helper/test rework and packet preparation. Native settings unchanged; no profiling/monitor, speed-tier change or performance-improvement claim. Existing caches/load were not controlled; unallocated elapsed is not model latency/idle time. Stop after this coherent delivery for independent review; no merge, deployment or production effect.
