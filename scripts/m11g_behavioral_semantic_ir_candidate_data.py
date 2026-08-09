"""Human-reviewed M11G behavioral proposition candidate definitions."""

from __future__ import annotations

from typing import Any


def candidate(
    proposition_id: str,
    proposition_type: str,
    proposition: str,
    direction: str,
    episode_ids: list[str],
    *,
    rationale: str,
    limitations: list[str],
    competing: str,
    contrasts: list[dict[str, Any]] | None = None,
    relevance: str = "primary",
    relationship_id: str | None = None,
    trajectory_change: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "proposition_id": proposition_id,
        "source_relationship_id": relationship_id,
        "proposition_type": proposition_type,
        "proposition": proposition,
        "direction": direction,
        "evidence_episode_ids": episode_ids,
        "rationale": rationale,
        "material_limitations": limitations,
        "competing_interpretations": [competing],
        "relevant_contrasts": contrasts or [],
        "conclusion_relevance": relevance,
        "overlap_relationships": [],
        "trajectory_change": trajectory_change,
    }


CORRECTED_PROPOSITIONS = [
    candidate(
        "pattern-fisa-title-vii-extension-opposition",
        "repeated_pattern",
        "Across two separate measures, Foushee opposed House passage of bills whose stated purpose included extending the authorities of title VII of the Foreign Intelligence Surveillance Act of 1978.",
        "opposition",
        ["single-119-s-4465-2-155", "single-119-hr-9238-2-221"],
        relationship_id="fisa-title-vii-extension-attempts",
        rationale="Both accepted episode meanings describe complete bills whose stated purpose includes extending title VII authorities, and both accepted episode directions oppose House passage.",
        limitations=[
            "These are separate legislative events.",
            "The measures may differ beyond their shared stated purpose.",
            "The votes are on complete measures and do not prove opposition to an isolated provision independent of the rest of each bill.",
        ],
        competing="Retain the two complete-measure choices only as separate episodes because their provisions may differ beyond the shared stated purpose.",
        contrasts=[
            {
                "episode_ids": ["single-119-s-1318-2-142"],
                "reason": "S. 1318 is a multi-title package; its whole-package vote cannot establish a component position on title VII.",
            }
        ],
    ),
    candidate(
        "pattern-iran-war-powers-removal-support",
        "repeated_pattern",
        "Across five separate resolutions, Foushee supported directing removal of United States Armed Forces from hostilities with or against Iran under the War Powers Resolution.",
        "support",
        [
            "single-119-hconres-38-2-85",
            "single-119-hconres-40-2-114",
            "single-119-hconres-75-2-170",
            "single-119-hconres-86-2-199",
            "single-119-hconres-89-2-282",
        ],
        relationship_id="iran-war-powers-hostilities-removal",
        rationale="Each accepted episode meaning independently states the same removal mechanism and Iran-hostilities target, and all five accepted episode directions support it.",
        limitations=[
            "The resolutions are separate events with small wording differences, including with, against, and unauthorized hostilities.",
            "The pattern does not establish that the factual hostilities or legal posture were unchanged across dates.",
        ],
        competing="Treat wording and timing differences as too material for one repeated-pattern proposition.",
        contrasts=[
            {
                "episode_ids": [
                    "single-119-hconres-61-1-345",
                    "single-119-hamdt-99-1-244",
                ],
                "reason": "A different War Powers target and repeal of earlier AUMFs use different targets or mechanisms and do not enlarge the Iran pattern.",
            }
        ],
    ),
    candidate(
        "pattern-lebanon-war-powers-removal-support",
        "repeated_pattern",
        "Across two separate resolutions, Foushee supported directing removal of United States Armed Forces from hostilities in Lebanon under the War Powers Resolution.",
        "support",
        ["single-119-hconres-84-2-201", "single-119-hconres-108-2-232"],
        relationship_id="lebanon-war-powers-hostilities-removal",
        rationale="Both accepted episode meanings state the same Lebanon-hostilities removal mechanism, and both accepted episode directions support it.",
        limitations=[
            "The resolutions are separate legislative events; recurrence does not establish a single episode or motive."
        ],
        competing="Retain the two choices only as separate episodes because each resolution may reflect a distinct factual context.",
        contrasts=[
            {
                "episode_ids": ["single-119-hamdt-60-1-210"],
                "reason": "Prohibiting assistance to the Lebanese Armed Forces is a funding choice, not the War Powers removal proposition.",
            }
        ],
    ),
    candidate(
        "pattern-venezuela-war-powers-removal-support",
        "repeated_pattern",
        "Across two separate resolutions, Foushee supported directing removal of United States Armed Forces from unauthorized hostilities within or against Venezuela.",
        "support",
        ["single-119-hconres-64-1-346", "single-119-hconres-68-2-48"],
        relationship_id="venezuela-war-powers-hostilities-removal",
        rationale="Both accepted episode meanings state the same unauthorized-hostilities removal choice, and both accepted episode directions support it.",
        limitations=[
            "The resolutions occurred in different House sessions and use within-or-against versus from-Venezuela wording."
        ],
        competing="Treat the wording and session difference as too material for a repeated-pattern proposition.",
        contrasts=[
            {
                "episode_ids": [
                    "single-119-hconres-61-1-345",
                    "single-119-hconres-38-2-85",
                ],
                "reason": "Other War Powers resolutions concern different targets; shared mechanism alone does not merge country-specific propositions.",
            }
        ],
    ),
    candidate(
        "pattern-terrorism-preparedness-support",
        "repeated_pattern",
        "Across two separate measures, Foushee supported federal terrorism-preparedness requirements addressing vehicular attacks and cascading critical-infrastructure effects.",
        "support",
        ["single-119-hr-1608-1-286", "single-119-hr-3106-2-234"],
        rationale="The accepted National Security episode meanings independently establish two federal terrorism-preparedness requirements, and both accepted directions support them.",
        limitations=[
            "The measures use different preparedness mechanisms.",
            "One is an assessment/reporting requirement and the other an exercise requirement.",
            "The proposition establishes recurring support for bounded terrorism-preparedness requirements, not a broader homeland-security ideology.",
            "An accepted Justice calibration relationship exists for this pair but contributes no National Security authority; this candidate derives independently from the accepted M11F episodes.",
        ],
        competing="Keep the assessment/reporting and exercise requirements as unrelated single choices because their mechanisms differ.",
    ),
    candidate(
        "pattern-ukraine-assistance-mixed",
        "repeated_pattern",
        "Across four separate Ukraine-assistance choices, Foushee opposed three amendments that would restrict or prohibit assistance and supported a measure authorizing support for Ukraine.",
        "mixed",
        [
            "single-119-hamdt-57-1-209",
            "single-119-hamdt-93-1-255",
            "single-119-hamdt-252-2-264",
            "single-119-hr-2913-2-207",
        ],
        rationale="The accepted episode meanings establish three distinct assistance restrictions and one whole-measure authorization; their accepted directions mechanically produce a mixed Semantic IR direction.",
        limitations=[
            "The three restrictive amendments differ in scope.",
            "H.R. 2913 is a whole measure and includes ‘other purposes’.",
            "No position is inferred on any H.R. 2913 component beyond its accepted bounded whole-measure meaning.",
        ],
        competing="Retain the whole-measure authorization separately because it is structurally different from the three amendments.",
    ),
    candidate(
        "pattern-jordan-assistance-restriction-opposition",
        "repeated_pattern",
        "Across two separate amendments, Foushee opposed reductions or prohibitions on United States assistance to Jordan.",
        "opposition",
        ["single-119-hamdt-56-1-208", "single-119-hamdt-236-2-244"],
        rationale="Both accepted meanings describe amendments reducing or prohibiting Jordan assistance, and both accepted episode directions oppose those amendments.",
        limitations=[
            "H.Amdt. 56 concerns funding for the Jordanian armed forces.",
            "H.Amdt. 236 has a broader funding/account scope.",
            "The mechanisms and affected accounts are not claimed to be identical.",
        ],
        competing="Keep the armed-forces support prohibition distinct from the broader account reductions.",
    ),
    candidate(
        "pattern-military-dod-sex-gender-restriction-opposition",
        "repeated_pattern",
        "Across five separate amendments, Foushee opposed military or Department of Defense restrictions involving gender-related health care or biological-sex-based requirements for service, forms, facilities, or school athletics.",
        "opposition",
        [
            "single-119-hamdt-86-1-246",
            "single-119-hamdt-88-1-248",
            "single-119-hamdt-89-1-249",
            "single-119-hamdt-254-2-266",
            "single-119-hamdt-256-2-268",
        ],
        rationale="The five accepted episode meanings enumerate bounded military or DoD restrictions and all five accepted episode directions oppose them.",
        limitations=[
            "These are different mechanisms.",
            "They affect different populations and settings.",
            "The proposition is confined to the five enumerated military/DoD choices.",
            "It does not establish a broader position outside these contexts.",
        ],
        competing="Keep the health-care, information-form, facilities, service-eligibility, and school-athletics mechanisms separate.",
    ),
    candidate(
        "trajectory-milcon-va-appropriations-direction-change",
        "trajectory",
        "Across successive Military Construction and Veterans Affairs appropriations packages, Foushee opposed the FY2026 package and supported the FY2027 package.",
        "mixed",
        ["single-119-hr-3944-1-182", "single-119-hr-8469-2-175"],
        relevance="limiting",
        rationale="The accepted chronological episode record changes from opposition on the FY2026 whole package to support on the FY2027 whole package.",
        limitations=[
            "Both are whole-package choices.",
            "Package contents differ between fiscal years.",
            "This establishes a change in direction on successive annual packages only.",
            "It does not identify which provisions caused the change.",
            "It does not establish motive or a generalized change in defense/veterans spending philosophy.",
        ],
        competing="Treat the packages only as two unrelated annual choices because their contents differ.",
        trajectory_change={
            "change_type": "direction_change",
            "ordered_evidence_episode_ids": [
                "single-119-hr-3944-1-182",
                "single-119-hr-8469-2-175",
            ],
            "accepted_chronology": [
                {
                    "episode_id": "single-119-hr-3944-1-182",
                    "accepted_date": "2025-06-25",
                },
                {
                    "episode_id": "single-119-hr-8469-2-175",
                    "accepted_date": "2026-05-15",
                },
            ],
            "accepted_before_direction": "opposes_policy_proposition",
            "accepted_after_direction": "supports_policy_proposition",
            "bounded_change_description": "The accepted direction changes from opposition on the FY2026 Military Construction and Veterans Affairs appropriations package to support on the successive FY2027 package.",
        },
    ),
    candidate(
        "notable-israel-foreign-military-financing-reduction",
        "notable_choice",
        "Foushee supported an amendment that would prohibit funds under the act from being used for Israel and reduce the Foreign Military Financing Program account by $3.3 billion.",
        "support",
        ["single-119-hamdt-235-2-243"],
        relevance="excluded",
        rationale="The accepted episode meaning states a specific country, program, and dollar reduction.",
        limitations=[
            "This is one amendment choice and does not establish a recurring pattern."
        ],
        competing="Retain as a standalone episode without notable-choice promotion.",
    ),
    candidate(
        "notable-aumf-repeal-1991-2002",
        "notable_choice",
        "Foushee supported an amendment to repeal the 1991 and 2002 Authorizations for Use of Military Force.",
        "support",
        ["single-119-hamdt-99-1-244"],
        relevance="excluded",
        rationale="The accepted episode meaning identifies repeal of two named AUMFs as a bounded, independently informative choice.",
        limitations=[
            "This remains distinct from country-specific War Powers repeated patterns and has no overlapping primary ownership."
        ],
        competing="Retain only as an episode until later synthesis review considers mechanism relationships.",
        contrasts=[
            {
                "episode_ids": [
                    "single-119-hconres-38-2-85",
                    "single-119-hconres-64-1-346",
                ],
                "reason": "Country-specific War Powers removal choices use a different legal mechanism and remain separately owned.",
            }
        ],
    ),
    candidate(
        "notable-international-criminal-court-sanctions-opposition",
        "notable_choice",
        "Foushee opposed H.R. 23, which would impose sanctions concerning International Criminal Court efforts to investigate, arrest, detain, or prosecute protected persons of the United States and its allies.",
        "opposition",
        ["single-119-hr-23-1-7"],
        relevance="excluded",
        rationale="The accepted whole-measure meaning states a specific sanctions policy and protected-person scope.",
        limitations=[
            "This is a complete-measure choice and does not establish a broader position on the Court."
        ],
        competing="Retain as a standalone sanctions episode without notable-choice promotion.",
    ),
    candidate(
        "notable-taiwan-security-cooperation-funding",
        "notable_choice",
        "Foushee opposed an amendment to strike funding for the Taiwan Security Cooperation Initiative.",
        "opposition",
        ["single-119-hamdt-95-1-257"],
        relevance="excluded",
        rationale="The accepted episode meaning states a specific funding-removal choice involving the Taiwan Security Cooperation Initiative.",
        limitations=[
            "This is one amendment choice and does not establish a broader Taiwan policy."
        ],
        competing="Retain as a standalone funding episode without notable-choice promotion.",
    ),
    candidate(
        "notable-haiti-temporary-protected-status",
        "notable_choice",
        "Foushee supported H.R. 1689, which would require the Secretary of Homeland Security to designate Haiti for Temporary Protected Status.",
        "support",
        ["single-119-hr-1689-2-120"],
        relevance="excluded",
        rationale="The accepted whole-measure meaning states a specific Haiti Temporary Protected Status requirement.",
        limitations=[
            "This is one complete-measure choice and does not establish a broader immigration pattern."
        ],
        competing="Retain as a standalone episode without notable-choice promotion.",
    ),
    candidate(
        "notable-fy2026-ndaa-package-opposition",
        "notable_choice",
        "Foushee opposed House passage of S. 1071, the National Defense Authorization Act for Fiscal Year 2026 package.",
        "opposition",
        ["single-119-s-1071-1-320"],
        relevance="excluded",
        rationale="The accepted meaning identifies the annual FY2026 defense authorization package as an independently informative whole-package choice.",
        limitations=[
            "This is a whole-package choice spanning defense authorization, military construction, Department of Energy national-security authorization, State Department authorization, intelligence authorization, Coast Guard authorization, funding tables, and other matters. No position is attributed to any individual component."
        ],
        competing="Retain only as a whole-package episode because its breadth limits behavioral inference.",
    ),
]
