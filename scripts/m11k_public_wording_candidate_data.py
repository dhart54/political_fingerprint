"""Human-authored M11K wording proposals compiled against accepted semantics."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


BEHAVIORAL_IDS = [
    "pattern-fisa-title-vii-extension-opposition",
    "pattern-iran-war-powers-removal-support",
    "pattern-lebanon-war-powers-removal-support",
    "pattern-venezuela-war-powers-removal-support",
    "pattern-terrorism-preparedness-support",
    "pattern-ukraine-assistance-mixed",
    "pattern-jordan-assistance-restriction-opposition",
    "pattern-military-dod-sex-gender-restriction-opposition",
    "trajectory-milcon-va-appropriations-direction-change",
    "notable-israel-foreign-military-financing-reduction",
    "notable-aumf-repeal-1991-2002",
    "notable-international-criminal-court-sanctions-opposition",
    "notable-taiwan-security-cooperation-funding",
    "notable-haiti-temporary-protected-status",
    "notable-fy2026-ndaa-package-opposition",
]
SYNTHESIS_IDS = [
    "synthesis-war-powers-cross-target-uniform-direction",
    "synthesis-security-assistance-interpretive-boundary",
]


def _display(direction: str) -> dict[str, str]:
    return {
        "support": {"label": "Support", "symbol": "+"},
        "opposition": {"label": "Opposition", "symbol": "−"},
        "mixed": {"label": "Mixed", "symbol": "±"},
    }[direction]


def _guard(explicit_elements: list[str]) -> dict[str, Any]:
    return {
        "statement_basis": "accepted_semantic_proposition_content",
        "raw_yea_nay_maps_to_direction": False,
        "direction_metadata_alone_establishes_public_meaning": False,
        "explicit_behavior_elements": explicit_elements,
    }


SPECS: list[dict[str, Any]] = [
    {
        "wording_item_id": "wording:issue-overview:national-security-foreign:119",
        "surface": "issue_overview",
        "semantic_sources": [
            *(
                {"source_kind": "behavioral", "source_id": value}
                for value in BEHAVIORAL_IDS
            ),
            *(
                {"source_kind": "synthesis", "source_id": value}
                for value in SYNTHESIS_IDS
            ),
        ],
        "public_title": "National security and foreign policy",
        "primary_sentence": "The reviewed record shows repeated support for country-specific War Powers resolutions to remove U.S. forces, while security-assistance choices differed by country and proposal.",
        "secondary_clarification": "Other accepted findings cover surveillance, terrorism preparedness, military and defense policy, annual appropriations, sanctions, Taiwan, Haiti, and individual authorization choices.",
        "evidence_count_label": "15 behavioral findings · 32 votes across 32 legislative episodes",
        "direction_display": None,
        "retained": [
            (
                "synthesis",
                SYNTHESIS_IDS[0],
                3,
                "This does not describe a position on every military intervention or authorization question.",
            ),
            (
                "synthesis",
                SYNTHESIS_IDS[1],
                3,
                "The record does not show one uniform position on assistance across countries.",
            ),
        ],
        "compression_notes": "The overview names the two accepted cross-pattern conclusions and lists the remaining finding areas without repeating legislative detail.",
        "prohibited_inference_risks": [
            "motive",
            "ideology",
            "a uniform position across all military action or security assistance",
        ],
        "semantic_guard": _guard(
            [
                "War Powers removal support",
                "country- and proposal-specific assistance choices",
            ]
        ),
    },
    {
        "wording_item_id": "wording:synthesis:war-powers",
        "surface": "synthesis",
        "semantic_sources": [
            {"source_kind": "synthesis", "source_id": SYNTHESIS_IDS[0]}
        ],
        "public_title": "War Powers resolutions across three countries",
        "primary_sentence": "Across Iran, Lebanon, and Venezuela, Foushee repeatedly supported War Powers measures to remove U.S. forces from the hostilities covered by each resolution.",
        "secondary_clarification": None,
        "evidence_count_label": "9 votes · 9 country-specific resolutions",
        "direction_display": _display("support"),
        "retained": [
            (
                "synthesis",
                SYNTHESIS_IDS[0],
                0,
                "The countries, wording, dates, and House sessions differ.",
            ),
            (
                "synthesis",
                SYNTHESIS_IDS[0],
                3,
                "This does not establish a position on every military intervention or authorization question.",
            ),
        ],
        "compression_notes": "Shortens the legal mechanism while retaining the distinct country targets and bounded hostilities.",
        "prohibited_inference_risks": [
            "pacifism",
            "isolationism",
            "opposition to all military action",
            "motive",
            "ideology",
        ],
        "semantic_guard": _guard(
            ["support", "War Powers removal mechanism", "Iran, Lebanon, and Venezuela"]
        ),
    },
    {
        "wording_item_id": "wording:synthesis:security-assistance",
        "surface": "synthesis",
        "semantic_sources": [
            {"source_kind": "synthesis", "source_id": SYNTHESIS_IDS[1]}
        ],
        "public_title": "Security assistance differed by country and proposal",
        "primary_sentence": "Foushee opposed reviewed restrictions involving Ukraine and Jordan, supported a Ukraine-support measure, opposed removing Taiwan security-cooperation funding, and supported one $3.3 billion cut to Israel military financing.",
        "secondary_clarification": None,
        "evidence_count_label": "8 votes across 8 country-specific choices",
        "direction_display": None,
        "retained": [
            (
                "synthesis",
                SYNTHESIS_IDS[1],
                0,
                "The countries, funding accounts, measures, and restriction mechanisms differ.",
            ),
            (
                "synthesis",
                SYNTHESIS_IDS[1],
                3,
                "These choices do not show one uniform position on assistance across countries.",
            ),
        ],
        "compression_notes": "Replaces the internal mixed direction metadata with the exact accepted country-by-country behavior.",
        "prohibited_inference_risks": [
            "uniform support for foreign aid",
            "uniform opposition to foreign aid",
            "motive",
            "ideology",
            "mixed substantive orientation toward Ukraine aid",
        ],
        "semantic_guard": _guard(
            [
                "three Ukraine restriction oppositions",
                "one Ukraine authorization support",
                "Jordan restriction opposition",
                "Taiwan funding-removal opposition",
                "specific Israel financing reduction support",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:fisa-title-vii",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[0]}
        ],
        "public_title": "FISA Title VII extensions",
        "primary_sentence": "Opposed two bills that would extend FISA Title VII surveillance authorities.",
        "secondary_clarification": None,
        "evidence_count_label": "2 votes · 2 episodes",
        "direction_display": _display("opposition"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[0],
                2,
                "Both votes were on complete bills, not isolated Title VII provisions.",
            )
        ],
        "compression_notes": "Omits formal amendatory language and the generic 'other purposes' clause.",
        "prohibited_inference_risks": [
            "opposition to every FISA authority",
            "a position on each provision in either bill",
        ],
        "semantic_guard": _guard(
            ["opposition", "two complete bills", "Title VII extension"]
        ),
    },
    {
        "wording_item_id": "wording:pattern:iran-war-powers",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[1]}
        ],
        "public_title": "Iran War Powers resolutions",
        "primary_sentence": "Supported five resolutions directing the removal of U.S. forces from hostilities with or against Iran.",
        "secondary_clarification": None,
        "evidence_count_label": "5 votes · 5 episodes",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[1],
                0,
                "The resolutions were separate events with wording and timing differences.",
            )
        ],
        "compression_notes": "Uses U.S. forces in place of the formal Armed Forces phrase while keeping the removal mechanism and target.",
        "prohibited_inference_risks": [
            "unchanged facts or legal posture across dates",
            "pacifism",
            "motive",
        ],
        "semantic_guard": _guard(
            ["support", "five separate resolutions", "removal", "Iran"]
        ),
    },
    {
        "wording_item_id": "wording:pattern:lebanon-war-powers",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[2]}
        ],
        "public_title": "Lebanon War Powers resolutions",
        "primary_sentence": "Supported two resolutions directing the removal of U.S. forces from hostilities in Lebanon.",
        "secondary_clarification": None,
        "evidence_count_label": "2 votes · 2 episodes",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[2],
                0,
                "These were separate resolutions, not one continuing legislative episode.",
            )
        ],
        "compression_notes": "Shortens the formal War Powers Resolution phrasing without changing the mechanism or target.",
        "prohibited_inference_risks": ["motive", "one continuous episode"],
        "semantic_guard": _guard(
            ["support", "two separate resolutions", "removal", "Lebanon"]
        ),
    },
    {
        "wording_item_id": "wording:pattern:venezuela-war-powers",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[3]}
        ],
        "public_title": "Venezuela War Powers resolutions",
        "primary_sentence": "Supported two resolutions directing the removal of U.S. forces from unauthorized hostilities within or against Venezuela.",
        "secondary_clarification": None,
        "evidence_count_label": "2 votes · 2 episodes",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[3],
                0,
                "The resolutions occurred in different House sessions and used different location wording.",
            )
        ],
        "compression_notes": "Keeps the accepted unauthorized-hostilities boundary and combines the two location formulations.",
        "prohibited_inference_risks": [
            "one continuous episode",
            "opposition to every military action involving Venezuela",
        ],
        "semantic_guard": _guard(
            [
                "support",
                "two separate resolutions",
                "unauthorized hostilities",
                "Venezuela",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:terrorism-preparedness",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[4]}
        ],
        "public_title": "Terrorism preparedness requirements",
        "primary_sentence": "Supported two federal preparedness measures addressing vehicle attacks and cascading infrastructure failures.",
        "secondary_clarification": "One required an assessment and report; the other required an exercise.",
        "evidence_count_label": "2 votes · 2 episodes",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[4],
                1,
                "The two measures used different mechanisms: an assessment and report versus an exercise.",
            )
        ],
        "compression_notes": "Compresses critical-infrastructure terminology while retaining the distinct mechanisms in clarification.",
        "prohibited_inference_risks": [
            "a broader homeland-security ideology",
            "identical preparedness mechanisms",
        ],
        "semantic_guard": _guard(
            [
                "support",
                "two measures",
                "vehicle attacks",
                "cascading infrastructure effects",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:ukraine-assistance",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[5]}
        ],
        "public_title": "Ukraine assistance",
        "primary_sentence": "Opposed three proposals to restrict Ukraine aid and supported one measure authorizing support for Ukraine.",
        "secondary_clarification": None,
        "evidence_count_label": "4 votes · 4 episodes",
        "direction_display": None,
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[5],
                0,
                "The three restrictions differed in scope.",
            ),
            (
                "behavioral",
                BEHAVIORAL_IDS[5],
                1,
                "The supporting vote was on a complete measure that also covered other purposes.",
            ),
            (
                "behavioral",
                BEHAVIORAL_IDS[5],
                2,
                "The complete-measure vote does not isolate a position on every provision.",
            ),
        ],
        "compression_notes": "States the four accepted choices directly and intentionally does not use the internal mixed direction label as a policy characterization.",
        "prohibited_inference_risks": [
            "Mixed on Ukraine aid",
            "a position on every provision in H.R. 2913",
            "motive",
        ],
        "semantic_guard": _guard(
            [
                "opposition to three restrictive proposals",
                "support for one authorizing measure",
            ]
        ),
    },
    {
        "wording_item_id": "wording:pattern:jordan-assistance",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[6]}
        ],
        "public_title": "Jordan assistance restrictions",
        "primary_sentence": "Opposed two proposals to cut or restrict U.S. assistance to Jordan.",
        "secondary_clarification": None,
        "evidence_count_label": "2 votes · 2 episodes",
        "direction_display": _display("opposition"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[6],
                2,
                "The proposals affected different accounts and used different mechanisms.",
            )
        ],
        "compression_notes": "Uses plain-language cut or restrict while retaining that the proposals were not identical.",
        "prohibited_inference_risks": [
            "identical affected accounts",
            "a position on all aid to Jordan",
        ],
        "semantic_guard": _guard(
            ["opposition", "two proposals", "Jordan assistance restrictions"]
        ),
    },
    {
        "wording_item_id": "wording:pattern:military-dod-sex-gender",
        "surface": "repeated_pattern",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[7]}
        ],
        "public_title": "Five military and DoD sex-and-gender policy amendments",
        "primary_sentence": "Opposed five amendments restricting gender-related health care or imposing biological-sex-based rules in specified military and Defense Department settings.",
        "secondary_clarification": "The amendments addressed service, forms, facilities, school athletics, and health care in different ways.",
        "evidence_count_label": "5 votes · 5 episodes",
        "direction_display": _display("opposition"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[7],
                2,
                "This pattern covers only the five listed military and DoD amendments.",
            ),
            (
                "behavioral",
                BEHAVIORAL_IDS[7],
                3,
                "It does not establish a broader position outside those settings.",
            ),
        ],
        "compression_notes": "Groups the enumerated settings in one sentence while retaining the five-amendment boundary and a short clarification.",
        "prohibited_inference_risks": [
            "a position on every transgender policy",
            "a position on every sex/gender policy",
            "a position outside the listed military and DoD settings",
        ],
        "semantic_guard": _guard(
            ["opposition", "five amendments", "enumerated military and DoD contexts"]
        ),
    },
    {
        "wording_item_id": "wording:trajectory:milcon-va",
        "surface": "trajectory",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[8]}
        ],
        "public_title": "Successive military construction and veterans appropriations packages",
        "primary_sentence": "Opposed the FY2026 package and supported the FY2027 package.",
        "secondary_clarification": None,
        "evidence_count_label": "2 votes · 2 annual packages",
        "direction_display": _display("mixed"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[8],
                0,
                "Both votes were on complete appropriations packages.",
            ),
            (
                "behavioral",
                BEHAVIORAL_IDS[8],
                1,
                "The package contents differed between fiscal years.",
            ),
            (
                "behavioral",
                BEHAVIORAL_IDS[8],
                3,
                "The votes do not identify which provisions explain the different directions.",
            ),
        ],
        "compression_notes": "Presents the bounded year-to-year vote directions without inferring motive, trend, or a broader spending philosophy.",
        "prohibited_inference_risks": [
            "motive",
            "a generalized change in philosophy",
            "opposition or support for each package component",
        ],
        "semantic_guard": _guard(
            ["FY2026 opposition", "FY2027 support", "different complete packages"]
        ),
    },
    {
        "wording_item_id": "wording:notable:israel-fmf-reduction",
        "surface": "notable_choice",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[9]}
        ],
        "public_title": "Israel military financing reduction",
        "primary_sentence": "Supported an amendment barring funds under the act from being used for Israel and cutting the Foreign Military Financing account by $3.3 billion.",
        "secondary_clarification": None,
        "evidence_count_label": "1 vote · individual notable choice",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[9],
                0,
                "This single amendment does not establish a recurring pattern.",
            )
        ],
        "compression_notes": "Shortens the amendment effect while retaining both the funding prohibition and exact account reduction.",
        "prohibited_inference_risks": ["a recurring Israel policy pattern", "motive"],
        "semantic_guard": _guard(
            ["support", "specific amendment", "$3.3 billion FMF reduction"]
        ),
    },
    {
        "wording_item_id": "wording:notable:aumf-repeal",
        "surface": "notable_choice",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[10]}
        ],
        "public_title": "1991 and 2002 military-force authorizations",
        "primary_sentence": "Supported repealing the 1991 and 2002 Authorizations for Use of Military Force.",
        "secondary_clarification": None,
        "evidence_count_label": "1 vote · individual notable choice",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[10],
                0,
                "This remains separate from the country-specific War Powers patterns.",
            )
        ],
        "compression_notes": "Removes amendment boilerplate while preserving the exact authorizations.",
        "prohibited_inference_risks": [
            "a repeated War Powers pattern",
            "a position on every authorization question",
        ],
        "semantic_guard": _guard(["support", "repeal", "1991 and 2002 AUMFs"]),
    },
    {
        "wording_item_id": "wording:notable:icc-sanctions",
        "surface": "notable_choice",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[11]}
        ],
        "public_title": "International Criminal Court sanctions bill",
        "primary_sentence": "Opposed a bill imposing sanctions over certain International Criminal Court actions against protected people from the United States and its allies.",
        "secondary_clarification": None,
        "evidence_count_label": "1 vote · complete bill",
        "direction_display": _display("opposition"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[11],
                0,
                "The vote was on the complete bill and does not establish a broader position on the Court.",
            )
        ],
        "compression_notes": "Compresses the investigate-arrest-detain-prosecute list into certain Court actions without broadening the protected-person scope.",
        "prohibited_inference_risks": [
            "a broad position on the ICC",
            "a position on every bill provision",
        ],
        "semantic_guard": _guard(
            ["opposition", "complete sanctions bill", "specified ICC actions"]
        ),
    },
    {
        "wording_item_id": "wording:notable:taiwan-funding",
        "surface": "notable_choice",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[12]}
        ],
        "public_title": "Taiwan security-cooperation funding",
        "primary_sentence": "Opposed removing funding for the Taiwan Security Cooperation Initiative.",
        "secondary_clarification": None,
        "evidence_count_label": "1 vote · individual notable choice",
        "direction_display": _display("opposition"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[12],
                0,
                "This single amendment does not establish a broader Taiwan policy.",
            )
        ],
        "compression_notes": "Uses removing funding in place of the formal strike-funding language.",
        "prohibited_inference_risks": ["a broader Taiwan policy", "motive"],
        "semantic_guard": _guard(
            ["opposition", "removing Taiwan Security Cooperation Initiative funding"]
        ),
    },
    {
        "wording_item_id": "wording:notable:haiti-tps",
        "surface": "notable_choice",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[13]}
        ],
        "public_title": "Temporary Protected Status for Haiti",
        "primary_sentence": "Supported a bill requiring the Homeland Security secretary to designate Haiti for Temporary Protected Status.",
        "secondary_clarification": None,
        "evidence_count_label": "1 vote · complete bill",
        "direction_display": _display("support"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[13],
                0,
                "The complete-bill vote does not establish a broader immigration pattern.",
            )
        ],
        "compression_notes": "Uses the public-facing office title while preserving the mandatory designation and country.",
        "prohibited_inference_risks": ["a broader immigration pattern", "motive"],
        "semantic_guard": _guard(["support", "complete bill", "Haiti TPS designation"]),
    },
    {
        "wording_item_id": "wording:notable:fy2026-ndaa",
        "surface": "notable_choice",
        "semantic_sources": [
            {"source_kind": "behavioral", "source_id": BEHAVIORAL_IDS[14]}
        ],
        "public_title": "FY2026 defense authorization package",
        "primary_sentence": "Opposed House passage of the FY2026 National Defense Authorization Act package.",
        "secondary_clarification": None,
        "evidence_count_label": "1 vote · complete package",
        "direction_display": _display("opposition"),
        "retained": [
            (
                "behavioral",
                BEHAVIORAL_IDS[14],
                0,
                "The package covered many defense and national-security matters; the vote does not isolate a position on any individual component.",
            )
        ],
        "compression_notes": "Omits the long component list from primary copy and retains the whole-package boundary.",
        "prohibited_inference_risks": [
            "opposition to any individual NDAA provision",
            "opposition to defense generally",
            "motive",
        ],
        "semantic_guard": _guard(
            ["opposition", "House passage", "complete FY2026 NDAA package"]
        ),
    },
]


def build_wording_definitions(
    behavioral_implementation: dict[str, Any],
    synthesis_implementation: dict[str, Any],
) -> list[dict[str, Any]]:
    """Expand exact limitation accounting for each human-authored wording spec."""

    behavioral = {
        row["proposition_id"]: row["accepted_candidate_content"]
        for row in behavioral_implementation["subject"]["implementation_records"]
    }
    synthesis = {
        row["synthesis_candidate_id"]: row["implemented_synthesis_content"]
        for row in synthesis_implementation["subject"]["implementation_records"]
    }
    definitions = []
    for raw in SPECS:
        spec = deepcopy(raw)
        retained = spec.pop("retained")
        retained_by_key: dict[tuple[str, str, str], str] = {}
        for kind, source_id, index, public_copy in retained:
            content = (
                behavioral[source_id] if kind == "behavioral" else synthesis[source_id]
            )
            limitation = content["material_limitations"][index]
            retained_by_key[(kind, source_id, limitation)] = public_copy
        treatments = []
        for ref in spec["semantic_sources"]:
            kind = ref["source_kind"]
            source_id = ref["source_id"]
            content = (
                behavioral[source_id] if kind == "behavioral" else synthesis[source_id]
            )
            for limitation in content["material_limitations"]:
                key = (kind, source_id, limitation)
                if key in retained_by_key:
                    treatments.append(
                        {
                            "source_kind": kind,
                            "source_id": source_id,
                            "source_limitation": limitation,
                            "treatment": "retained_public_copy",
                            "public_copy": retained_by_key[key],
                            "reason": None,
                        }
                    )
                else:
                    treatments.append(
                        {
                            "source_kind": kind,
                            "source_id": source_id,
                            "source_limitation": limitation,
                            "treatment": "compressed_or_omitted",
                            "public_copy": None,
                            "reason": spec["compression_notes"],
                        }
                    )
        if set(retained_by_key) - {
            (row["source_kind"], row["source_id"], row["source_limitation"])
            for row in treatments
        }:
            raise ValueError(
                f"retained limitation is not bound: {spec['wording_item_id']}"
            )
        spec["limitation_treatments"] = treatments
        definitions.append(spec)
    return definitions
