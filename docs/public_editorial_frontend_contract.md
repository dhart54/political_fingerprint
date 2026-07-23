# Public Editorial Frontend Contract

This contract defines how reviewed legislative analysis becomes a reader-facing issue experience. It changes presentation, not analytical meaning or publication authority.

## Runtime path

The representative route follows one production path:

1. `frontend/app/page.js` supplies the selected representative to `PositionByIssue`.
2. `PositionByIssue` loads issue summaries and vote evidence with `fetchPositions` and `fetchPositionEvidence`.
3. `selectEditorialIssueExperience` matches the representative, issue, and evidence, then applies the production-eligibility gates.
4. `adaptEditorialIssueSlice` creates a public view model with `buildPublicEditorialPresentation`.
5. `EditorialIssueExperience` renders that view model. If no eligible slice exists, `PositionByIssue` renders the basic-evidence presentation and the same vote receipts.

React must not infer support, opposition, episodes, patterns, philosophy, or publication status from raw rolls. Those decisions remain upstream. The presentation adapter may count supplied records, describe whether expected records are present, and translate already-supplied analytical states into public language.

## Public hierarchy

An eligible editorial slice is presented in this order:

1. what the reviewed record suggests;
2. the supplied conclusion, when the coverage state permits one;
3. a public evidence-strength label;
4. coverage of the conclusion, including reviewed period and record counts;
5. patterns, important exceptions, voting context, and limits when supplied;
6. progressively disclosed vote explanations and official sources.

Party alignment is secondary voting context, never the finding. Procedural records and Not Voting remain visible but do not become support or opposition. A narrow amendment record is not presented as final-passage evidence for its parent measure.

## Coverage states

| State | Public treatment | Conclusion behavior |
| --- | --- | --- |
| `reviewed_conclusion` | Reviewed conclusion available | Show the supplied conclusion and its bounded evidence-strength label. |
| `developing_record` | Developing record | Suppress the broad conclusion; explain that meaningful evidence exists but the repeated pattern is still developing. |
| `limited_evidence` | Limited evidence | Suppress the broad conclusion; explain that too few independent episodes are complete. |
| `no_editorial_coverage` | Vote evidence | Show receipts and counts without combining them into an issue conclusion. |
| `procedural_context_only` | Procedural context only | Explain that the records concern floor process and do not establish a direct position on the underlying issue. |

Incomplete evidence is a coverage statement, not evidence that the representative has no position. Missing expected records must be disclosed. `Not Voting` and `Present` are reported as actions, not folded into substantive Yes/No counts.

When `inference_candidate.coverage` is present, its expected and observed action counts, Yes/No, Present, Not Voting, missing-action counts, and complete/partial/missing episode counts are authoritative. Interpretation-array counting is a legacy fallback only when the complete structured coverage object is absent. A supported upstream conclusion may remain visible with an explicitly disclosed coverage gap; contested and insufficient upstream inference states remain developing and limited, respectively.

Public limitations are generated from structured coverage plus explicitly public-safe limitation fields. Arbitrary internal methodology prose is not rendered. Summary exceptions prefer explicitly public exceptions, then weakening or conflicting evidence, then relevant caveats from distinct episodes, with semantic deduplication and a four-item limit. Additional measure-specific caveats remain in their vote cards.

## Public-copy glossary

Internal analytical and workflow terms stay outside public surfaces. The adapter owns these translations:

| Internal concept | Reader-facing language |
| --- | --- |
| `bounded_repeated_pattern` | A consistent pattern in the reviewed record |
| `bounded_selective_pattern` | A selective pattern in the reviewed record |
| `bounded_conditional_boundary` | A mixed record with a clear boundary |
| `contested_candidate` | A developing pattern |
| `insufficient_evidence` | Not enough reviewed evidence yet |
| eligible editorial slice | Reviewed analysis |
| interpreted substantive rows without an editorial slice | Vote evidence |
| no interpreted substantive rows | Limited record |

Public copy must not expose candidate IDs, inference codes, benchmark or approval workflow, production flags, source or claim IDs, internal domain identifiers, or review-harness instructions. Avoid moral judgments, motive claims, unsupported ideology, rankings, predictions, and voting recommendations.

## Public versus review presentation

The public renderer contains only public content. Review warnings and fixture controls belong to outer harness chrome marked with `data-review-harness`; they are not children of a `data-public-surface` element.

Pending real slices may be passed explicitly to the guarded golden-render route in review mode. They still travel through the production selector, adapter, and renderer. Synthetic fixtures may exercise production-eligible and partial-coverage states, but are test data only. Production representative pages read only `frontend/lib/editorialIssueProductionSlices.mjs` and still require every existing publication gate.

## Accessibility and responsive behavior

Issue navigation is keyboard reachable and exposes the selected issue with `aria-current`. Vote disclosures retain native button semantics and allow one expanded parent record at a time. Focus rings must remain visible. Public panels must not create horizontal page overflow at 390 px, tablet, laptop, or wide desktop widths; the issue-navigation row may scroll horizontally within its own container.
