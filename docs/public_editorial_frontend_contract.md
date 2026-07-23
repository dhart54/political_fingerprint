# Public Editorial Frontend Contract

This contract defines how reviewed legislative analysis becomes a reader-facing issue experience. It changes presentation, not analytical meaning or publication authority.

## Runtime path

The representative route follows one production path:

1. `frontend/app/page.js` supplies the selected representative to `PositionByIssue`.
2. `PositionByIssue` loads issue summaries and vote evidence with `fetchPositions` and `fetchPositionEvidence`.
3. `selectEditorialIssueExperience` matches the representative, issue, and evidence, then applies the production-eligibility gates.
4. `adaptEditorialIssueSlice` creates a public view model with `buildPublicEditorialPresentation`.
5. `EditorialIssueExperience` renders that view model. If no eligible slice exists, `PositionByIssue` renders the basic-evidence presentation and the same vote receipts.

React must not infer support, opposition, service eligibility, episodes, featured evidence, patterns, philosophy, or publication status from raw rolls. Those decisions remain upstream. The presentation adapter may group supplied contracts and translate already-supplied analytical states into public language.

The reusable evidence model is:

`shared legislative action + shared episode relationship + member action overlay + member issue synthesis`

Shared actions contain only legislative facts, stage-specific arguments, caveats, and sources. Member identity, action direction, action-and-result copy, service status, and episode trajectory belong to the overlay. Shared evidence must not name a reviewed member or assign a reason for a member's vote.

## Public hierarchy

An eligible editorial slice is presented in this order:

1. one member-and-issue title;
2. the supplied conclusion, when the coverage state permits one;
3. a reader-facing evidence label and compact coverage line;
4. supplied `Repeated patterns`, `Policy trajectories`, `Other notable choices`, and `Meaningful exceptions` sections that actually contain content;
5. three to five upstream-selected featured policy episodes;
6. a collapsed complete reviewed record grouped by policy family, Congress, episode, and action;
7. secondary procedural and voting context disclosures.

The default surface remains bounded: episodes and the complete record start collapsed, regardless of whether an issue contains 6, 20, or 40 actions. The standardized action card remains the detailed receipt inside its episode. Repeated legislative stages are not flattened into independent top-level policy positions.

Party alignment is secondary voting context, never the finding. Procedural records and Not Voting remain visible but do not become support or opposition. A narrow amendment record is not presented as final-passage evidence for its parent measure.

## Coverage states

| State | Public treatment | Conclusion behavior |
| --- | --- | --- |
| `reviewed_conclusion` | Reviewed conclusion available | Show the supplied conclusion and its bounded evidence-strength label. |
| `developing_record` | Developing record | Suppress the broad conclusion; explain that meaningful evidence exists but the repeated pattern is still developing. |
| `limited_evidence` | Limited evidence | Suppress the broad conclusion; explain that too few independent episodes are complete. |
| `no_editorial_coverage` | Vote evidence | Show receipts and counts without combining them into an issue conclusion. |
| `procedural_context_only` | Procedural context only | Explain that the records concern floor process and do not establish a direct position on the underlying issue. |

Incomplete evidence is a coverage statement, not evidence that the representative has no position. Missing expected in-service records must be disclosed. `Not Voting` and `Present` are reported as actions, not folded into substantive Yes/No counts. `not yet serving` and `no longer serving` are outside-service states, not Not Voting, missing data, or reduced evidence quality. `missing evidence` applies only to an expected action during the member's service. Service dates and eligibility are supplied upstream and are never inferred in React.

When `inference_candidate.coverage` is present, its expected and observed action counts, Yes/No, Present, Not Voting, missing-action counts, and complete/partial/missing episode counts are authoritative. Interpretation-array counting is a legacy fallback only when the complete structured coverage object is absent. A supported upstream conclusion may remain visible with an explicitly disclosed coverage gap; contested and insufficient upstream inference states remain developing and limited, respectively.

The rich surface does not render a large coverage panel or a generic issue-level methodology/limitations panel. Breadth appears in the compact coverage line. A neutral debate-attribution boundary appears once per expanded action containing arguments. Concrete measure limitations stay with the relevant episode or action. `Meaningful exceptions` is reserved for evidence that materially complicates the issue conclusion.

## Episode and policy-family hierarchy

Closely related actions within one Congress may share an episode. Related legislation in different Congresses remains in separate episodes because legislative text, mechanism, coalition, and service eligibility may differ. An optional policy-family ID may group those Congress-specific episodes without implying one uninterrupted trajectory or a change in the member's position.

`featuredEpisodeIds` is an upstream editorial selection, normally limited to five. React does not choose featured evidence from chronology, vote margin, party alignment, or counts. Internal selection rationales remain in review artifacts and are not public copy.

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

Issue navigation is hidden when only one issue is available; when multiple issues are available it is keyboard reachable and exposes the selected issue with `aria-current`. Episode, complete-record, action, context, and source disclosures use native `details`/`summary` semantics. Focus rings must remain visible. Public panels must not create horizontal page overflow at 390 px, tablet, laptop, or wide desktop widths; the issue-navigation row may scroll horizontally within its own container.
