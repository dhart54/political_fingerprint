# M11I National Security Synthesis Candidate Review

This package proposes synthesis relationships from the exact human-accepted M11H Behavioral Semantic IR. It does not accept synthesis or authorize public wording or downstream use.

## Proposed synthesis candidates

### 1. `synthesis-war-powers-cross-target-uniform-direction`

**Candidate proposition:** Across the accepted Iran, Lebanon, and Venezuela patterns, Foushee repeatedly supported War Powers measures directing the removal of United States armed forces from the bounded hostilities described in those measures.

**Type / direction:** `uniform_direction` / `support`

**Accepted Behavioral Semantic IR inputs:**

- `primary_support` — `pattern-iran-war-powers-removal-support`: Support across five Iran War Powers removal resolutions.
- `primary_support` — `pattern-lebanon-war-powers-removal-support`: Support across two Lebanon War Powers removal resolutions.
- `primary_support` — `pattern-venezuela-war-powers-removal-support`: Support across two Venezuela War Powers removal resolutions.
- `contextual_support` — `notable-aumf-repeal-1991-2002`: One excluded choice supporting repeal of the 1991 and 2002 AUMFs.

**Non-inflated evidence:** 10 unique accepted episodes and 10 unique accepted actions. Behavioral proposition nodes and underlying episodes are not added together.

**Why this is synthesis:** It identifies a repeated cross-target relationship among accepted patterns that all concern directing termination of specified armed-forces involvement under congressional authorization mechanisms; it does not group every military or foreign-policy proposition.

**Competing interpretation:** Keep all three country patterns independent because their targets and resolution language differ, using the shared mechanism only as review context.

**Material limitations:**

- The country targets, resolution wording, dates, and House sessions differ.
- The proposition is confined to the accepted Iran, Lebanon, and Venezuela War Powers patterns.
- The AUMF repeal choice is a singleton and remains excluded at the Behavioral Semantic IR layer.
- The record does not establish a position on all military intervention or every authorization question.

**Unresolved review question:** Human review must decide whether the shared War Powers mechanism adds enough explanatory structure beyond the three accepted patterns.

### 2. `synthesis-security-assistance-interpretive-boundary`

**Candidate proposition:** The accepted security-assistance record is differentiated rather than uniform: the Ukraine pattern is mixed, the Jordan pattern opposes assistance restrictions, an excluded Taiwan choice opposed striking security-cooperation funding, and an excluded Israel choice supported a specific Foreign Military Financing reduction.

**Type / direction:** `interpretive_boundary` / `mixed`

**Accepted Behavioral Semantic IR inputs:**

- `primary_support` — `pattern-ukraine-assistance-mixed`: Mixed choices across four Ukraine-assistance measures.
- `primary_support` — `pattern-jordan-assistance-restriction-opposition`: Opposition to two Jordan-assistance restrictions.
- `contextual_support` — `notable-taiwan-security-cooperation-funding`: One excluded choice opposing removal of Taiwan security-cooperation funding.
- `contrast` — `notable-israel-foreign-military-financing-reduction`: One excluded choice supporting a specific $3.3 billion Israel FMF reduction.

**Non-inflated evidence:** 8 unique accepted episodes and 8 unique accepted actions. Behavioral proposition nodes and underlying episodes are not added together.

**Why this is synthesis:** The relationship is an explicit interpretive boundary created by different accepted directions across comparable assistance choices, not a claim that every foreign-assistance proposition shares one position.

**Competing interpretation:** Keep every country-specific proposition independent because the record may support only separate bounded choices rather than a cross-country boundary.

**Material limitations:**

- The countries, accounts, measures, and restriction mechanisms differ.
- The Ukraine proposition is itself mixed and includes one whole-measure authorization.
- The Taiwan and Israel inputs are singleton notable choices and remain excluded at the Behavioral Semantic IR layer.
- No reason for the country-specific differences is inferred.

**Unresolved review question:** Human review must decide whether the contrast is explanatory enough to retain as synthesis or should remain a dossier-only caution.

## Intentionally standalone propositions

- `notable-fy2026-ndaa-package-opposition` — The broad whole-package NDAA choice cannot safely establish a component or cross-mechanism synthesis.
- `notable-haiti-temporary-protected-status` — The Haiti TPS choice is a singleton and does not safely combine with the proposed security mechanism relationships.
- `notable-international-criminal-court-sanctions-opposition` — The sanctions choice is a singleton with no safe accepted recurring relationship.
- `pattern-fisa-title-vii-extension-opposition` — Title VII extension opposition concerns a surveillance-authority mechanism not safely related to the proposed War Powers or assistance syntheses.
- `pattern-military-dod-sex-gender-restriction-opposition` — The enumerated military and DoD restrictions do not share a safe mechanism-level relationship with the proposed candidates.
- `pattern-terrorism-preparedness-support` — Preparedness requirements use distinct domestic security mechanisms and do not safely combine with surveillance, military, or assistance propositions.
- `trajectory-milcon-va-appropriations-direction-change` — The limiting annual-package trajectory has no accepted broader appropriations synthesis to limit and cannot safely become a primary synthesis input.

## Candidate overlap

- `synthesis-war-powers-cross-target-uniform-direction` vs `synthesis-security-assistance-interpretive-boundary`: `no_overlap`; shared accepted propositions: 0; shared underlying episodes: 0.

## Human decisions required

For each of the two candidates, decide accept as written, accept with bounded revision, or reject. Also confirm whether each of the seven standalone dispositions should remain outside synthesis.

All 15 accepted M11H propositions are accounted for in the governed JSON. The 24 contrast-only and 25 no-safe M11G episodes remain outside direct synthesis evidence.

Synthesis acceptance, public wording, publication, persistence, database writes, production writes, and deployment remain unauthorized.
