"""Explicit review proposals, not acceptance and not a directional-vote fallback.

Authored from the approved M14B/M14C records before consulting M13H output.
Only bounded relationships claims live here; source quotations are projected
unchanged from accepted records by the builder.
"""

PATTERNS = [
    {
        "key": "covered_china_linked_funding_exclusions",
        "actions": ["house:119:1:120", "house:119:1:313"],
        "summary": "Foushee opposed two proposals making education institutions ineligible for specified federal funds because of covered China-linked relationships, each with a waiver route.",
        "bounded_choice": "Withhold a defined stream of federal funding from an education institution for maintaining specified China-linked relationships, subject to statutory waiver conditions.",
        "support": [
            "H.R.881 would withhold DHS funds for covered institutional ties to Confucius Institutes, the Thousand Talents Program or defined Chinese entities of concern; ending the relationship or a qualifying renewable one-year waiver restores eligibility. Foushee voted Nay.",
            "H.R.1069 would withhold covered federal education funds from K–12 schools maintaining specified Chinese-government-backed partnerships or resources; qualifying pre-enactment contracts may receive discretionary waivers through termination. Foushee voted Nay.",
        ],
        "differences": [
            "H.R.881 covers higher education and DHS funding; H.R.1069 covers K–12 schools and its defined federal education programs. Neither means all federal funding.",
            "The covered entities and relationships differ. H.R.881's renewable national-security waiver is not H.R.1069's qualifying pre-existing-contract waiver; H.R.1069's prohibition begins one year after enactment.",
            "The relationship concerns these funding exclusions, not opposition to foreign-money disclosure generally. H.R.1048 contains mixed member choices and remains a separate whole-episode notable-choice proposal; H.R.1005 is Not Voting.",
        ],
        "value": "Identifies a shared eligibility mechanism across college and K–12 measures while separating it from reporting, contract prohibitions and different waiver conditions.",
    },
    {
        "key": "continuity_of_collective_bargaining",
        "actions": ["house:119:1:332", "house:119:2:216"],
        "summary": "Across two different labor systems, Foushee supported keeping collective bargaining in force during potential disruptions. She voted to restore bargaining coverage and preserve existing agreements for specified federal workers, and separately voted to require continued bargaining and unchanged employment terms while newly represented workers pursued a first contract.",
        "bounded_choice": "Keep bargaining in force across distinct disruptions: H.R.2550 restores statutory bargaining coverage affected by EO14251 and preserves specified existing federal union agreements; H.R.5408 maintains employment terms and bargaining duties while an agreement is pending and adds first-contract bargaining, mediation and arbitration requirements. These are distinct statutory mechanisms, not identical contract protections.",
        "support": [
            "H.R.2550 would nullify the named order's exclusions from federal and Foreign Service labor-management coverage, prohibit implementation spending, and preserve covered March 26, 2025 union agreements through their stated terms. Foushee voted Yea.",
            "H.R.5408 would maintain wages, hours and employment terms pending agreement and continue the employer's bargaining duty absent election-based decertification; it also adds first-contract bargaining, mediation and binding-arbitration deadlines. Foushee voted Yea.",
        ],
        "differences": [
            "H.R.2550 concerns specified federal and Foreign Service bodies and an executive order; H.R.5408 amends the NLRA system. Their workers, statutory regimes and legal tools are different.",
            "Keeping existing federal union agreements effective through their terms differs from maintaining employment terms pending agreement and continuing a bargaining duty. The proposed shared relationship is continuity of bargaining, not identical contract protection.",
            "H.R.5408 also mandates a first-contract timetable and binding arbitration. H.R.2550 does not. Support for either whole measure cannot be assigned exclusively to its continuity provisions.",
            "EO14251's agency subdivisions, exceptions and delegated powers remain bounded by the approved action limitations. This is not a claim about all federal employees, actual litigation outcomes, or a general pro-labor position.",
        ],
        "value": "Tests whether the newly concrete meanings support a useful relationship between preserving existing bargaining coverage and maintaining bargaining obligations. Independent review must decide whether the sector and remedy differences leave enough shared substance.",
    },
]

NOTABLE = {
    "key": "hr1048_substitute_and_package",
    "actions": ["house:119:1:79", "house:119:1:83"],
    "summary": "Within one H.R.1048 episode, Foushee supported the substitute's threshold-based foreign-gift reporting, exceptions and negotiated rules, then opposed the final package of reporting, contract restrictions and enforcement.",
    "differences": [
        "The substitute would replace the printed text with its own thresholds, public reports, exclusions, fines and negotiated-rulemaking duties. Its reporting requirements are not inferred from the parent bill.",
        "The final package includes institution and individual disclosures, specified contract prohibitions with waivers, investment reports and enforcement. The Nay vote applies to the whole package; it does not establish opposition to any one component.",
        "The amendment failed in the House and the final package passed the House. Neither outcome establishes enactment. These same-day choices are one episode, not a cross-episode trajectory or a change of position over time.",
        "The paired votes distinguish support for this disclosure substitute from opposition to this final package; they do not establish why Foushee made either choice or a preferred universal disclosure regime.",
    ],
    "value": "The newly supported substitute meaning makes the within-episode contrast substantively legible without treating every directional action as independently notable.",
}

# Every non-elevated episode has an individually authored analytical disposition.
REMAINDER = {
    "house:119:1:312": ("non_directional_receipt", "H.R.1005 is understood, but Foushee's official Not Voting status supplies no support or opposition evidence."),
    "house:119:1:314": ("retained_as_useful_contrast", "H.R.1049 imposes parent access and notice duties for foreign sources/materials. Its Nay is not another vote for withholding funds because of covered relationships; retain the distinct disclosure mechanism without enlarging the funding-exclusion pattern."),
    "house:119:2:19": ("retained_as_useful_contrast", "H.R.2262 concerns whether specified voluntary training counts as paid work. Its Nay is distinct from collective-bargaining coverage or continuity; it cannot enlarge the bargaining pattern merely because it concerns workers."),
    "house:119:1:68": ("receipt_only_no_elevation", "H.R.1156 extends specified pandemic-unemployment fraud enforcement periods and rescinds funding. H.R.7892's prospective identity-screening duties are not the same bounded choice; shared fraud language and Nay votes are insufficient."),
    "house:119:1:146": ("receipt_only_no_elevation", "H.R.1642 adds small-business-center outreach for CTE graduates. Neither territorial tuition eligibility nor excluding training from paid time expresses that same mechanism; the standalone outreach choice adds no independently established finding here."),
    "house:119:1:315": ("receipt_only_no_elevation", "S.356 extends federal-land county payments and related authorities. Support does not establish a general education-spending pattern with unrelated tuition or small-business services."),
    "house:119:2:184": ("receipt_only_no_elevation", "H.R.2616 combines parental-consent conditions and a separate incorporated use-of-funds prohibition. H.R.1049's parent disclosure rights do not establish the same bounded policy choice; a shared school-governance topic or funding instrument is insufficient."),
    "house:119:2:31": ("receipt_only_no_elevation", "H.R.2988 is an indivisible ERISA fiduciary, disclosure and study package. Its Nay cannot be projected onto one component or merged with collective bargaining merely because both affect workplaces."),
    "house:119:2:47": ("receipt_only_no_elevation", "H.R.6359 disseminates specified pregnancy resources and complaint information. H.R.1049's parent access to foreign-source materials serves a different informational purpose; disclosure duties alone do not establish an explanatory pattern."),
    "house:119:2:82": ("receipt_only_no_elevation", "H.R.6472 extends in-state tuition treatment to defined territorial U.S. nationals. It is not the same bounded service or payment choice as CTE outreach or rural-county payments."),
    "house:119:2:217": ("receipt_only_no_elevation", "H.R.7892 conditions aid disbursement on identity verification after screening flags; it is not H.R.1156's retrospective enforcement-period extension. A flag is not a finding of fraud."),
}

SEARCH_REVIEW = [
    {"lane": "foreign influence", "actions": ["house:119:1:79", "house:119:1:83", "house:119:1:120", "house:119:1:312", "house:119:1:313", "house:119:1:314"], "result": "Propose the two funding-exclusion episodes and the single mixed H.R.1048 episode separately. Reject a broad foreign-influence pattern: disclosure, withholding funds and contract prohibitions differ, and Not Voting cannot be counted."},
    {"lane": "labor and workforce", "actions": ["house:119:1:146", "house:119:1:332", "house:119:2:19", "house:119:2:31", "house:119:2:216"], "result": "Propose the bounded bargaining-continuity relationship for review. Do not add training-pay exclusions, CTE outreach or ERISA investments: common workforce context is insufficient."},
    {"lane": "school governance and information rights", "actions": ["house:119:1:314", "house:119:2:184", "house:119:2:47"], "result": "No repeated pattern proposed. Foreign-source inspection, consent plus use restrictions, and pregnancy-resource dissemination differ in beneficiaries, policy objects and operative duties."},
    {"lane": "fraud controls", "actions": ["house:119:1:68", "house:119:2:217"], "result": "No repeated pattern proposed. Enforcement time limits plus rescission and prospective aid verification do not express the same mechanism despite common fraud framing and Nay votes."},
    {"lane": "access, services and payments", "actions": ["house:119:1:146", "house:119:1:315", "house:119:2:82"], "result": "No repeated pattern proposed. Outreach, federal-land county payments and tuition treatment are materially distinct; Yea direction and education-related benefits alone cannot link them."},
    {"lane": "cross-lane and chronology", "actions": [], "result": "No additional common bounded choice found across the lanes. No trajectory proposed: the potentially comparable funding-exclusion and bargaining episodes keep the same direction. The mixed H.R.1048 episode cannot be split; other direction differences cross different policy objects or mechanisms."},
]
