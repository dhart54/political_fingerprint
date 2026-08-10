"""Human-review candidate definitions for M11I synthesis construction."""

from __future__ import annotations


CANDIDATE_DEFINITIONS = [
    {
        "synthesis_candidate_id": "synthesis-war-powers-cross-target-uniform-direction",
        "semantic_role": "synthesis",
        "synthesis_type": "uniform_direction",
        "direction": "support",
        "conclusion_relevance": "primary",
        "proposition": (
            "Across the accepted Iran, Lebanon, and Venezuela patterns, Foushee "
            "repeatedly supported War Powers measures directing the removal of "
            "United States armed forces from the bounded hostilities described in "
            "those measures."
        ),
        "inputs": [
            {
                "proposition_id": "pattern-iran-war-powers-removal-support",
                "relationship_role": "primary_support",
                "concise_input_summary": "Support across five Iran War Powers removal resolutions.",
            },
            {
                "proposition_id": "pattern-lebanon-war-powers-removal-support",
                "relationship_role": "primary_support",
                "concise_input_summary": "Support across two Lebanon War Powers removal resolutions.",
            },
            {
                "proposition_id": "pattern-venezuela-war-powers-removal-support",
                "relationship_role": "primary_support",
                "concise_input_summary": "Support across two Venezuela War Powers removal resolutions.",
            },
            {
                "proposition_id": "notable-aumf-repeal-1991-2002",
                "relationship_role": "contextual_support",
                "concise_input_summary": "One excluded choice supporting repeal of the 1991 and 2002 AUMFs.",
            },
        ],
        "relationship_basis": {
            "basis_type": "shared_policy_mechanism_across_distinct_targets",
            "semantic_relationship": (
                "Three independently accepted repeated patterns use the same War "
                "Powers removal mechanism across three distinct country targets and "
                "share the same accepted direction."
            ),
            "topic_similarity_only": False,
        },
        "relationship_rationale": (
            "The synthesis relates three already accepted recurring patterns by a "
            "shared legal mechanism and direction while preserving their distinct "
            "country targets. The AUMF repeal singleton is contextual only."
        ),
        "why_synthesis_not_topic_grouping": (
            "It identifies a repeated cross-target relationship among accepted "
            "patterns that all concern directing termination of specified armed-forces "
            "involvement under congressional authorization mechanisms; it does not "
            "group every military or foreign-policy proposition."
        ),
        "material_limitations": [
            "The country targets, resolution wording, dates, and House sessions differ.",
            "The proposition is confined to the accepted Iran, Lebanon, and Venezuela War Powers patterns.",
            "The AUMF repeal choice is a singleton and remains excluded at the Behavioral Semantic IR layer.",
            "The record does not establish a position on all military intervention or every authorization question.",
        ],
        "competing_interpretation": (
            "Keep all three country patterns independent because their targets and "
            "resolution language differ, using the shared mechanism only as review context."
        ),
        "unresolved_ambiguity": (
            "Human review must decide whether the shared War Powers mechanism adds "
            "enough explanatory structure beyond the three accepted patterns."
        ),
        "prohibited_inferences": [
            "pacifism",
            "isolationism",
            "anti-military ideology",
            "motive",
            "opposition to all military intervention",
        ],
    },
    {
        "synthesis_candidate_id": "synthesis-security-assistance-interpretive-boundary",
        "semantic_role": "synthesis",
        "synthesis_type": "interpretive_boundary",
        "direction": "mixed",
        "conclusion_relevance": "primary",
        "proposition": (
            "The accepted security-assistance record is differentiated rather than "
            "uniform: the Ukraine pattern is mixed, the Jordan pattern opposes "
            "assistance restrictions, an excluded Taiwan choice opposed striking "
            "security-cooperation funding, and an excluded Israel choice supported a "
            "specific Foreign Military Financing reduction."
        ),
        "inputs": [
            {
                "proposition_id": "pattern-ukraine-assistance-mixed",
                "relationship_role": "primary_support",
                "concise_input_summary": "Mixed choices across four Ukraine-assistance measures.",
            },
            {
                "proposition_id": "pattern-jordan-assistance-restriction-opposition",
                "relationship_role": "primary_support",
                "concise_input_summary": "Opposition to two Jordan-assistance restrictions.",
            },
            {
                "proposition_id": "notable-taiwan-security-cooperation-funding",
                "relationship_role": "contextual_support",
                "concise_input_summary": "One excluded choice opposing removal of Taiwan security-cooperation funding.",
            },
            {
                "proposition_id": "notable-israel-foreign-military-financing-reduction",
                "relationship_role": "contrast",
                "concise_input_summary": "One excluded choice supporting a specific $3.3 billion Israel FMF reduction.",
            },
        ],
        "relationship_basis": {
            "basis_type": "bounded_cross_policy_contrast",
            "semantic_relationship": (
                "Accepted country-specific assistance propositions carry mixed or "
                "contrasting effects that bound any single-direction assistance conclusion."
            ),
            "topic_similarity_only": False,
        },
        "relationship_rationale": (
            "The candidate explains why the accepted country-specific assistance "
            "inputs cannot safely compile to a general pro-aid or anti-aid conclusion. "
            "The excluded Taiwan and Israel choices remain contextual and contrast "
            "evidence rather than recurring patterns."
        ),
        "why_synthesis_not_topic_grouping": (
            "The relationship is an explicit interpretive boundary created by "
            "different accepted directions across comparable assistance choices, not "
            "a claim that every foreign-assistance proposition shares one position."
        ),
        "material_limitations": [
            "The countries, accounts, measures, and restriction mechanisms differ.",
            "The Ukraine proposition is itself mixed and includes one whole-measure authorization.",
            "The Taiwan and Israel inputs are singleton notable choices and remain excluded at the Behavioral Semantic IR layer.",
            "No reason for the country-specific differences is inferred.",
        ],
        "competing_interpretation": (
            "Keep every country-specific proposition independent because the record "
            "may support only separate bounded choices rather than a cross-country boundary."
        ),
        "unresolved_ambiguity": (
            "Human review must decide whether the contrast is explanatory enough to "
            "retain as synthesis or should remain a dossier-only caution."
        ),
        "prohibited_inferences": [
            "pro-aid",
            "anti-aid",
            "pro-alliance",
            "anti-Israel",
            "ideological alignment",
            "motive",
        ],
    },
]


PROPOSITION_ACCOUNTING = [
    {
        "proposition_id": "pattern-fisa-title-vii-extension-opposition",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "Title VII extension opposition concerns a surveillance-authority mechanism not safely related to the proposed War Powers or assistance syntheses.",
    },
    {
        "proposition_id": "pattern-iran-war-powers-removal-support",
        "accounting_role": "primary_input",
        "reason": "Primary recurring input to the bounded cross-target War Powers candidate.",
    },
    {
        "proposition_id": "pattern-lebanon-war-powers-removal-support",
        "accounting_role": "primary_input",
        "reason": "Primary recurring input to the bounded cross-target War Powers candidate.",
    },
    {
        "proposition_id": "pattern-venezuela-war-powers-removal-support",
        "accounting_role": "primary_input",
        "reason": "Primary recurring input to the bounded cross-target War Powers candidate.",
    },
    {
        "proposition_id": "pattern-terrorism-preparedness-support",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "Preparedness requirements use distinct domestic security mechanisms and do not safely combine with surveillance, military, or assistance propositions.",
    },
    {
        "proposition_id": "pattern-ukraine-assistance-mixed",
        "accounting_role": "primary_input",
        "reason": "Primary accepted pattern supporting the country-specific assistance interpretive boundary.",
    },
    {
        "proposition_id": "pattern-jordan-assistance-restriction-opposition",
        "accounting_role": "primary_input",
        "reason": "Primary accepted pattern supporting the country-specific assistance interpretive boundary.",
    },
    {
        "proposition_id": "pattern-military-dod-sex-gender-restriction-opposition",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "The enumerated military and DoD restrictions do not share a safe mechanism-level relationship with the proposed candidates.",
    },
    {
        "proposition_id": "trajectory-milcon-va-appropriations-direction-change",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "The limiting annual-package trajectory has no accepted broader appropriations synthesis to limit and cannot safely become a primary synthesis input.",
    },
    {
        "proposition_id": "notable-israel-foreign-military-financing-reduction",
        "accounting_role": "contrast_input",
        "reason": "Excluded singleton retained only as a country-specific contrast within the assistance boundary candidate.",
    },
    {
        "proposition_id": "notable-aumf-repeal-1991-2002",
        "accounting_role": "contextual_input",
        "reason": "Excluded singleton retained only as contextual authorization evidence for the War Powers candidate.",
    },
    {
        "proposition_id": "notable-international-criminal-court-sanctions-opposition",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "The sanctions choice is a singleton with no safe accepted recurring relationship.",
    },
    {
        "proposition_id": "notable-taiwan-security-cooperation-funding",
        "accounting_role": "contextual_input",
        "reason": "Excluded singleton retained only as contextual evidence within the assistance boundary candidate.",
    },
    {
        "proposition_id": "notable-haiti-temporary-protected-status",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "The Haiti TPS choice is a singleton and does not safely combine with the proposed security mechanism relationships.",
    },
    {
        "proposition_id": "notable-fy2026-ndaa-package-opposition",
        "accounting_role": "intentionally_standalone_no_safe_synthesis",
        "reason": "The broad whole-package NDAA choice cannot safely establish a component or cross-mechanism synthesis.",
    },
]
