"""Source-bound V4 corrections for material-detail closure."""

from __future__ import annotations

from copy import deepcopy

from action_interpretation_candidate_v3_data import (
    FINAL_DEFINITIONS as V3_FINAL_DEFINITIONS,
    RELATED_ACTION_GROUPS as V3_RELATED_ACTION_GROUPS,
)


INITIAL_DEFINITIONS = deepcopy(V3_FINAL_DEFINITIONS)
FINAL_DEFINITIONS = deepcopy(V3_FINAL_DEFINITIONS)
RELATED_ACTION_GROUPS = deepcopy(V3_RELATED_ACTION_GROUPS)

FINAL_DEFINITIONS["house:119:2:227"] = {
    "meaning": (
        "The House choice was whether to pass H.R. 2478 as amended, allowing participating open-end investment companies and transfer agents to delay specified-adult account redemptions when they reasonably believe financial exploitation occurred, is occurring, or was attempted. A specified adult is a person age 65 or older, or age 18 or older whom the company or agent reasonably believes has a mental or physical impairment preventing the person from protecting their interests. The ordinary delay is up to 15 business days, with a possible additional 10-business-day internal extension and further government extension. The elective direct-at-fund regime includes trusted-contact requests, a trusted-contact notice exception when exploitation is suspected, internal review and records, and SEC recommendations."
    ),
    "provisions": (
        (
            "Allow an elective trusted-contact and financial-exploitation protection regime for non-institutional direct-at-fund accounts.",
            "section 2(a), new subsection (h)",
        ),
        (
            "Define a specified adult as an individual age 65 or older, or age 18 or older whom the company or transfer agent reasonably believes has a mental or physical impairment preventing the individual from protecting their interests.",
            "section 2(a), new subsection (i)(3)",
        ),
        (
            "Permit an ordinary 15-business-day redemption delay, a possible additional 10-business-day internal extension, and further extension by a competent government authority.",
            "section 2(a), new subsection (i)(2)",
        ),
        (
            "Require internal review, notices, procedures, disclosures, and retained records.",
            "section 2(a), new subsection (i)",
        ),
        ("Require SEC regulatory and legislative recommendations.", "section 2(b)"),
    ),
    "limits": (
        (
            "Notice to a trusted contact is not required when the firm reasonably believes that contact is involved in exploitation.",
            "section 2(a), new subsection (i)(2)(D)",
        ),
    ),
    "confidence": "medium",
    "official": None,
}

FINAL_DEFINITIONS["house:119:2:157"] = deepcopy(INITIAL_DEFINITIONS["house:119:2:157"])
FINAL_DEFINITIONS["house:119:2:157"]["meaning"] = (
    "The House choice was whether to pass H.R. 2853 as amended, expanding specified federal theft, stolen-goods, forfeiture, and money-laundering rules for organized retail and supply-chain crime, including a $5,000 aggregate threshold over 12 months for specified transported or received stolen goods. It also would establish a Homeland Security coordination center for federal, State, local, and private-sector investigations and information sharing."
)

FINAL_DEFINITIONS["house:119:1:42"] = deepcopy(INITIAL_DEFINITIONS["house:119:1:42"])
FINAL_DEFINITIONS["house:119:1:42"]["meaning"] = (
    "The House choice was whether to pass H.R. 35, creating a federal offense for intentionally fleeing specified pursuing officers by motor vehicle within 100 miles of the border. The offense carries a general maximum of two years, five to 20 years when serious bodily injury results, and 10 years to life when death results. The bill also would impose specified immigration consequences and require annual Justice and Homeland Security reporting."
)

FINAL_DEFINITIONS["house:119:1:128"] = {
    **deepcopy(INITIAL_DEFINITIONS["house:119:1:128"]),
    "meaning": (
        "The House choice was whether to pass H.R. 2243, expanding where qualified current and retired law-enforcement officers may carry concealed firearms, including specified school zones, publicly accessible transport property, National Park System units, and lower-security federal public facilities. It also would revise retired-officer qualification periods and documentation. Section 3(c) separately inserts the words ‘any magazine and’ into two LEOSA provisions; the governed packet identifies the insertion but lacks enough surrounding statutory context to state its exact legal effect safely."
    ),
    "limits": (
        (
            "Section 3(c) inserts ‘any magazine and’ into 18 U.S.C. 926B(e)(2) and 926C(e)(1)(B); its exact legal effect remains unresolved because the governed packet does not include sufficient surrounding statutory context.",
            "section 3(c)",
        ),
    ),
    "confidence": "low",
    "status_override": "ambiguous",
    "official": None,
}


TARGETED_CORRECTIONS = {
    "house:119:2:227",
    "house:119:2:157",
    "house:119:1:42",
    "house:119:1:128",
    # The all-37 quantitative closure pass also found source-bound values in
    # these two existing structured inventories that were absent from prose.
    "house:119:1:162",
    "house:119:1:351",
}

TEXTUAL_AMENDMENTS = {
    "house:119:1:128": [
        {
            "exact_change": "insert ‘any magazine and’ after ‘includes’ in two referenced LEOSA provisions",
            "locator": "section 3(c)",
            "context_sufficiency": "insufficient",
            "expected_effect": None,
            "unresolved_effect": "The exact legal effect cannot be stated safely from the supplied surrounding context.",
            "materiality_state": "material",
        }
    ]
}

MATERIAL_DETAIL_ACTIONS = set(TARGETED_CORRECTIONS)
