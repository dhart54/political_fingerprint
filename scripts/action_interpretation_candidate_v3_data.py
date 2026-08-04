"""Source-first V3 editorial definitions and neutral related-action audit data.

The V2 architecture is retained, but these V3 definitions are evaluated against
independently frozen expected inventories derived before candidate comparison.
Nothing in this module confers acceptance or downstream authority.
"""

from __future__ import annotations

from copy import deepcopy

from action_interpretation_candidate_v2_data import ACTION_DEFINITIONS


INITIAL_DEFINITIONS = deepcopy(ACTION_DEFINITIONS)
FINAL_DEFINITIONS = deepcopy(ACTION_DEFINITIONS)


FINAL_DEFINITIONS["house:119:1:23"] = {
    "meaning": (
        "The House choice was whether to pass the Senate version of the Laken "
        "Riley Act, requiring federal detention and DHS detainers for certain "
        "inadmissible noncitizens connected to burglary, theft, larceny, "
        "shoplifting, assault of a law-enforcement officer, or crimes resulting "
        "in death or serious bodily injury. It also would give State attorneys "
        "general standing to seek expedited injunctive relief over specified "
        "federal detention, release, parole, and visa actions."
    ),
    "provisions": (
        (
            "Require detention and DHS detainers for covered noncitizens connected "
            "to burglary, theft, larceny, shoplifting, assault of a law-enforcement "
            "officer, or crimes resulting in death or serious bodily injury.",
            "section 2",
        ),
        (
            "Create State attorney-general enforcement actions concerning specified "
            "immigration detention, release, parole, and visa duties.",
            "section 3",
        ),
    ),
    "limits": (
        (
            "State enforcement standing uses a claimed-harm threshold that includes "
            "financial harm over $100.",
            "section 3",
        ),
    ),
    "confidence": "medium",
    "official": None,
}


FINAL_DEFINITIONS["house:119:1:68"] = {
    "meaning": (
        "The House choice was whether to pass H.R. 1156, establishing a 10-year "
        "limitations period for specified criminal prosecutions and civil enforcement "
        "actions involving fraud in four pandemic unemployment programs. It also "
        "would rescind $5 million in unobligated administrative funding."
    ),
    "provisions": ACTION_DEFINITIONS["house:119:1:68"]["provisions"],
    "limits": ACTION_DEFINITIONS["house:119:1:68"]["limits"],
    "confidence": "high",
    "official": None,
}


EXPECTED_ENUMERATIONS: dict[str, list[dict[str, object]]] = {
    "house:119:1:23": [
        {
            "enumeration_id": "detention-trigger-categories",
            "count": 6,
            "items": [
                "burglary",
                "theft",
                "larceny",
                "shoplifting",
                "assault of a law-enforcement officer",
                "crimes resulting in death or serious bodily injury",
            ],
            "locator": "section 2",
        }
    ],
    "house:119:1:68": [
        {
            "enumeration_id": "pandemic-unemployment-programs",
            "count": 4,
            "items": [
                "Pandemic Unemployment Assistance",
                "Federal Pandemic Unemployment Compensation",
                "Mixed Earner Unemployment Compensation",
                "Pandemic Emergency Unemployment Compensation",
            ],
            "locator": "section 2(a)-(c)",
        }
    ],
}


RELATED_ACTION_GROUPS: list[dict[str, object]] = [
    {
        "group_id": "laken-riley-house-senate-versions",
        "relationship_basis": [
            "shared official short title",
            "same detention-and-State-enforcement policy mechanism",
            "different exact measure identity and governed operative version",
        ],
        "action_ids": ["house:119:1:6", "house:119:1:23"],
        "shared_provisions": [
            "detention and DHS-detainer coverage for burglary, theft, larceny, and shoplifting triggers",
            "State attorney-general enforcement over specified detention, release, parole, and visa duties, including the governed financial-harm threshold",
        ],
        "required_differences": [
            "S. 5 adds assault of a law-enforcement officer to the detention triggers",
            "S. 5 adds crimes resulting in death or serious bodily injury to the detention triggers",
        ],
    },
    {
        "group_id": "halt-fentanyl-house-senate-versions",
        "relationship_basis": [
            "same fentanyl-related-substances scheduling policy family",
            "House and Senate-origin measures with distinct governed texts",
        ],
        "action_ids": ["house:119:1:33", "house:119:1:166"],
        "shared_provisions": [
            "permanent Schedule I treatment for fentanyl-related substances as a class",
            "research registration pathways for Schedule I work",
            "specified Controlled Substances Act and import-export penalty treatment",
        ],
        "required_differences": [
            "S. 331 is the Senate-origin enrolled version",
            "the exact operative packages use distinct technical-correction and implementation structures",
        ],
    },
    {
        "group_id": "fisa-short-term-extensions",
        "relationship_basis": [
            "same two Title VII sunset references",
            "same short-term extension mechanism with different dates",
        ],
        "action_ids": ["house:119:2:155", "house:119:2:221"],
        "shared_provisions": [
            "short-term extension of the same two Title VII FISA repeal-date references",
        ],
        "required_differences": [
            "roll 155 changes April 30, 2026 to June 12, 2026",
            "roll 221 changes June 12, 2026 to July 2, 2026",
            "roll 155 retains a governed source-identity conflict not present for roll 221",
        ],
    },
    {
        "group_id": "dc-criminal-justice-and-policing",
        "relationship_basis": [
            "shared D.C. criminal-justice or policing subject",
            "distinct measure identities and non-interchangeable operative mechanisms",
        ],
        "action_ids": [
            "house:119:1:162",
            "house:119:1:270",
            "house:119:1:271",
            "house:119:1:274",
            "house:119:1:275",
            "house:119:1:298",
            "house:119:1:299",
        ],
        "shared_provisions": [],
        "required_differences": [
            "collective-bargaining and discipline rules",
            "youth-offender sentencing and public statistics",
            "Family Court and transfer ages",
            "judicial nomination governance",
            "vehicle-pursuit standards and alert technology",
            "detention and secured-cash-bail rules",
            "repeal with specified policing-law subtitles retained",
        ],
    },
]


PRE_CORRECTION_MAJOR_ACTIONS = {
    "house:119:1:23",
    "house:119:1:68",
}
