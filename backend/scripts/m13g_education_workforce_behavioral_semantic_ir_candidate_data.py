"""Human-review candidate definitions for M13G Education & Workforce."""

from __future__ import annotations


PROPOSITIONS = [
    {
        "proposition_id": "pattern-education-relationship-triggered-funding-restriction-opposition",
        "proposition_type": "repeated_pattern",
        "proposition": (
            "Across two separate proposals, Foushee opposed conditioning or "
            "withholding federal funding from educational institutions based on "
            "specified institutional relationships or support: Confucius Institute "
            "relationships in H.R. 881 and Chinese-government support in H.R. 1069."
        ),
        "direction": "opposition",
        "evidence_episode_ids": [
            "single-119-hr-881-1-120",
            "single-119-hr-1069-1-313",
        ],
        "rationale": (
            "H.R. 881 would impose Department of Homeland Security funding "
            "restrictions on higher-education institutions with Confucius Institute "
            "relationships, while H.R. 1069 would prohibit federal education funds "
            "for elementary and secondary schools receiving Chinese-government "
            "support. Both are distinct federal-funding restriction choices "
            "triggered by the specified institutional relationship or support, and "
            "both accepted episode directions are opposition."
        ),
        "material_limitations": [
            "The proposals govern different federal funding streams and different education sectors.",
            "H.R. 881 concerns Confucius Institute relationships at institutions of higher education; H.R. 1069 concerns direct or indirect Chinese-government support for elementary and secondary schools.",
            "The pattern is limited to the two accepted funding-restriction choices and does not establish a general position on China, foreign influence, disclosure, education funding, or school governance.",
        ],
        "competing_interpretations": [
            "Keep the two episodes separate because their funding streams, covered institutions, and triggering relationships differ."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": ["single-119-hr-1049-1-314"],
                "reason": "H.R. 1049 uses a parent-awareness purpose rather than the bounded federal-funding restriction mechanism shared by H.R. 881 and H.R. 1069.",
            },
            {
                "episode_ids": ["single-119-hr-1005-1-312"],
                "reason": "H.R. 1005 concerns school foreign-source disclosure and is non-directional because Foushee was recorded Not Voting.",
            },
            {
                "episode_ids": ["hr-1048-amendment-and-final-passage"],
                "reason": "The H.R. 1048 episode concerns a Section 117 amendment and a distinct whole-package passage choice, not the same funding-restriction mechanism, and its accepted direction is mixed.",
            },
        ],
        "trajectory_change": None,
        "conclusion_relevance": "primary",
    },
    {
        "proposition_id": "notable-hr1048-amendment-support-final-passage-opposition",
        "proposition_type": "notable_choice",
        "proposition": (
            "Within the H.R. 1048 legislative episode, Foushee supported H.Amdt. "
            "12's Section 117 reporting changes and later opposed final passage of "
            "the distinct whole H.R. 1048 package."
        ),
        "direction": "mixed",
        "evidence_episode_ids": ["hr-1048-amendment-and-final-passage"],
        "rationale": (
            "This is the only accepted multi-action episode and preserves two "
            "different exact choices with opposite accepted effects on the same "
            "legislative date. Its bounded mixed structure is independently notable "
            "without converting it into one general foreign-influence or higher-"
            "education position."
        ),
        "material_limitations": [
            "H.Amdt. 12 is a narrower Section 117 amendment choice; final passage is an indivisible whole-package choice.",
            "Opposition to final passage cannot be attributed to any individual H.R. 1048 component, including the accepted amendment.",
            "The mixed episode does not establish motive or a single overall position on foreign influence, higher education, China, or Section 117 policy.",
            "This is a notable mixed episode, not a trajectory candidate: the accepted episode is one primary semantic unit and M13G does not split it into synthetic episodes.",
        ],
        "competing_interpretations": [
            "Retain the episode only in no-safe-aggregation accounting because its two choices should not be elevated beyond the accepted episode record."
        ],
        "overlap_relationships": [],
        "relevant_contrasts": [
            {
                "episode_ids": [
                    "single-119-hr-881-1-120",
                    "single-119-hr-1005-1-312",
                    "single-119-hr-1049-1-314",
                    "single-119-hr-1069-1-313",
                ],
                "reason": "These are separate foreign-influence-related education choices with different mechanisms and cannot resolve or generalize the mixed H.R. 1048 episode.",
            }
        ],
        "trajectory_change": None,
        "conclusion_relevance": "primary",
    },
]


CONTRAST_ACTIONS = {
    "foreign-influence-parent-awareness-different-mechanism": {"house:119:1:314"},
}
