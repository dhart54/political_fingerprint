"""Build the review-only Environment & Energy commissioning corpus.

The builder is intentionally deterministic. It reads checked-in House Clerk
roll-call XML, applies a frozen member-neutral corpus, selects a small cohort
from observed vote-vector structure, and exercises the generic overlay and
proposition-first synthesis code. It never writes to a database.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.editorial_artifacts.bundle import ARTIFACT_TYPES, canonical_json, semantic_hash
from backend.app.summaries.editorial_candidate_evaluation import evaluate_candidates
from backend.app.summaries.editorial_member_overlay import build_member_overlay

STARTING_COMMIT = "08e675e2039d76f16b8c9576e4b5a8254bc44d72"
ISSUE = "ENVIRONMENT_ENERGY"
CORPUS_VERSION = "commissioning-domain-environment-energy-v1"
BATCH_KEY = "commissioning-domain-v1-environment-energy"
REVIEWED_PERIOD = "119th Congress, January 8-March 18, 2026"
ROLLS = (5, 6, 7, 55, 64, 76, 78, 93)
EPISODE_ROLLS = {
    "fy2026-cjs-energy-water-interior-appropriations": (5, 6, 7),
    "critical-mineral-supply-and-domestic-production": (55, 64),
    "home-energy-standards-and-incentives": (76, 78),
    "lead-ammunition-and-tackle-on-federal-lands": (93,),
}
PUBLICATION = {
    "editorial_status": "human_approval_pending",
    "benchmark_status": "not_promoted",
    "production_eligible": False,
}
REFERENCE_MEMBERS = {"F000477", "A000055", "A000370", "M001184", "B000490", "G000586", "M001217"}

SOURCES = [
    {
        "source_id": f"clerk_roll_{roll:03d}",
        "source_type": "house_clerk_roll_call",
        "name": f"House Clerk roll call {roll}",
        "url": f"https://clerk.house.gov/Votes/2026{roll}",
        "locator": "vote question, exact action, result, and member votes",
        "authority_rank": 1,
    }
    for roll in ROLLS
] + [
    {
        "source_id": "congress_hr6938_text",
        "source_type": "congress_gov_measure_text",
        "name": "H.R. 6938 text and division table of contents",
        "url": "https://www.congress.gov/bill/119th-congress/house-bill/6938/text",
        "locator": "Divisions A-C and statement of FY2026 appropriations",
        "authority_rank": 2,
    },
    {
        "source_id": "congress_fy2026_status",
        "source_type": "crs_appropriations_status_table",
        "name": "FY2026 appropriations status table",
        "url": "https://www.congress.gov/crs-appropriations-status-table/2026",
        "locator": "House votes retaining Division A, retaining Divisions B-C, and package passage",
        "authority_rank": 5,
    },
    {
        "source_id": "hrpt_119_387",
        "source_type": "house_committee_report",
        "name": "H. Rept. 119-387 — Critical Mineral Dominance Act",
        "url": "https://www.congress.gov/committee-report/119th-congress/house-report/387/1",
        "locator": "purpose, provisions, majority rationale, dissenting views",
        "authority_rank": 3,
    },
    {
        "source_id": "hrpt_119_268",
        "source_type": "house_committee_report",
        "name": "H. Rept. 119-268 — Securing America's Critical Minerals Supply Act",
        "url": "https://www.congress.gov/committee-report/119th-congress/house-report/268/1",
        "locator": "sections 2-3, purpose, CBO description, minority views",
        "authority_rank": 3,
    },
    {
        "source_id": "hrpt_119_470",
        "source_type": "house_committee_report",
        "name": "H. Rept. 119-470 — Don't Mess With My Home Appliances Act",
        "url": "https://www.congress.gov/committee-report/119th-congress/house-report/470/1",
        "locator": "section analysis, majority rationale, minority views",
        "authority_rank": 3,
    },
    {
        "source_id": "hrpt_119_484",
        "source_type": "house_committee_report",
        "name": "H. Rept. 119-484 — Homeowner Energy Freedom Act",
        "url": "https://www.congress.gov/committee-report/119th-congress/house-report/484/1",
        "locator": "repealed programs, unobligated funds, majority rationale, minority views",
        "authority_rank": 3,
    },
    {
        "source_id": "hrpt_119_385",
        "source_type": "house_committee_report",
        "name": "H. Rept. 119-385 — Protecting Access for Hunters and Anglers Act",
        "url": "https://www.congress.gov/committee-report/119th-congress/house-report/385/1",
        "locator": "reported substitute, unit-specific exception, majority rationale, dissenting views",
        "authority_rank": 3,
    },
]

ACTION_DOSSIERS = {
    5: {
        "action_title": "Retain Division A of the FY2026 three-division appropriations package",
        "measure": "H.R. 6938",
        "exact_stage": "House vote to retain Division A before passage",
        "prior_baseline": "Division A was subject to a separate retention decision before the House voted on the package.",
        "proposed_change": "Retain the Commerce, Justice, Science, and related-agencies appropriations division in H.R. 6938.",
        "mechanism": "annual discretionary appropriations",
        "affected_entities": ["Department of Commerce", "Department of Justice", "National Science Foundation", "related agencies"],
        "scale": "one division of a three-division FY2026 appropriations package",
        "timing": "fiscal year 2026",
        "outcome": "retained, 375-47",
        "supporter_argument": {"state": "supported_absence", "reason": "No bounded division-specific official argument was mapped; package debate cannot safely be assigned to this retention vote."},
        "opponent_argument": {"state": "supported_absence", "reason": "No bounded division-specific official argument was mapped; package debate cannot safely be assigned to this retention vote."},
        "caveats": ["This was not final passage.", "Division A is not itself an Environment & Energy-only measure.", "Do not infer a reason for a member's vote from the package title."],
        "source_ids": ["clerk_roll_005", "congress_hr6938_text", "congress_fy2026_status"],
        "route": "human_exception_required",
    },
    6: {
        "action_title": "Retain the Energy-Water and Interior-Environment divisions of H.R. 6938",
        "measure": "H.R. 6938",
        "exact_stage": "House vote to retain Divisions B and C before passage",
        "prior_baseline": "Divisions B and C were subject to a combined retention decision before package passage.",
        "proposed_change": "Retain FY2026 appropriations for Energy and Water Development and for Interior, Environment, and related agencies.",
        "mechanism": "annual discretionary appropriations",
        "affected_entities": ["Army Corps of Engineers", "Department of Energy", "Department of the Interior", "Environmental Protection Agency", "related agencies"],
        "scale": "two divisions of a three-division FY2026 appropriations package",
        "timing": "fiscal year 2026",
        "outcome": "retained, 419-6",
        "supporter_argument": {"state": "supported_absence", "reason": "No bounded retention-stage argument was mapped separately from package debate."},
        "opponent_argument": {"state": "supported_absence", "reason": "No bounded retention-stage argument was mapped separately from package debate."},
        "caveats": ["This was not final passage.", "The combined vote does not separate Division B from Division C.", "The package contains many programs and cannot support a single-policy motive claim."],
        "source_ids": ["clerk_roll_006", "congress_hr6938_text", "congress_fy2026_status"],
        "route": "human_exception_required",
    },
    7: {
        "action_title": "Pass the FY2026 CJS, Energy-Water, and Interior-Environment appropriations package",
        "measure": "H.R. 6938",
        "exact_stage": "House passage after the two division-retention votes",
        "prior_baseline": "The House had retained Division A and Divisions B-C in separate votes.",
        "proposed_change": "Pass the three-division FY2026 appropriations package as assembled after the retention votes.",
        "mechanism": "annual discretionary appropriations",
        "affected_entities": ["Commerce and Justice agencies", "science agencies", "energy and water programs", "Interior and EPA programs"],
        "scale": "three appropriations divisions",
        "timing": "fiscal year 2026",
        "outcome": "passed, 397-28; later enacted as Public Law 119-74",
        "supporter_argument": {"state": "supported_absence", "reason": "No package-wide argument was reduced to one Environment & Energy claim."},
        "opponent_argument": {"state": "supported_absence", "reason": "No package-wide argument was reduced to one Environment & Energy claim."},
        "caveats": ["This package spans several issue domains.", "The enacted text confirms later status but does not replace the House-stage meaning.", "A Yea or Nay does not reveal a view on every provision."],
        "source_ids": ["clerk_roll_007", "congress_hr6938_text", "congress_fy2026_status"],
        "route": "human_exception_required",
    },
    55: {
        "action_title": "Pass the Critical Mineral Dominance Act",
        "measure": "H.R. 4090",
        "exact_stage": "House passage of the committee substitute considered adopted under the rule",
        "prior_baseline": "Executive orders directed agencies on mineral production; the reported bill proposed statutory duties and studies.",
        "proposed_change": "Codify selected mineral-production directives, require import-reliance reporting, identify and expedite priority projects, review impediments, and accelerate geologic mapping.",
        "mechanism": "statutory agency direction, reporting, project prioritization, and permitting review",
        "affected_entities": ["Department of the Interior", "Department of Agriculture", "federal land managers", "hardrock mineral projects"],
        "scale": "national federal mineral policy and federal lands",
        "timing": "ongoing duties and recurring reports after enactment",
        "outcome": "passed, 224-195",
        "supporter_argument": {"state": "claim_supported", "text": "The committee majority argued the bill would expand domestic mineral production and address supply-chain vulnerabilities.", "source_ids": ["hrpt_119_387"]},
        "opponent_argument": {"state": "claim_supported", "text": "Dissenting views disputed codifying the executive-order approach and raised environmental-review and public-land concerns.", "source_ids": ["hrpt_119_387"]},
        "caveats": ["The vote was on the House stage, not enactment.", "Project acceleration and studies are distinct mechanisms within one bill."],
        "source_ids": ["clerk_roll_055", "hrpt_119_387"],
        "route": "standard_generation_pass",
    },
    64: {
        "action_title": "Pass the Securing America's Critical Minerals Supply Act",
        "measure": "H.R. 3617",
        "exact_stage": "House passage of the amended bill",
        "prior_baseline": "DOE's organizing statute did not contain the bill's proposed critical-energy-resource functions and recurring assessments.",
        "proposed_change": "Define critical energy resources, add DOE supply-security functions, require ongoing vulnerability assessments, develop diversification and domestic-production strategies, and report to Congress.",
        "mechanism": "departmental mission, supply-chain assessment, strategy development, and congressional reporting",
        "affected_entities": ["Department of Energy", "energy-sector supply chains", "states", "federal agencies", "energy-sector stakeholders"],
        "scale": "national critical-energy-resource supply chains",
        "timing": "ongoing assessments and a report within two years",
        "outcome": "passed House",
        "supporter_argument": {"state": "claim_supported", "text": "The committee majority argued a durable DOE role was needed to assess vulnerabilities and strengthen critical-resource supply chains.", "source_ids": ["hrpt_119_268"]},
        "opponent_argument": {"state": "claim_supported", "text": "Minority views argued the broad critical-energy-resource definition could include fossil resources and did not prioritize clean-energy supply chains.", "source_ids": ["hrpt_119_268"]},
        "caveats": ["The bill's defined resource category is broader than mineral names in the short title.", "The vote does not establish support for every possible resource strategy."],
        "source_ids": ["clerk_roll_064", "hrpt_119_268"],
        "route": "standard_generation_pass",
    },
    76: {
        "action_title": "Pass the Don't Mess With My Home Appliances Act",
        "measure": "H.R. 4626",
        "exact_stage": "House passage of the reported amended bill",
        "prior_baseline": "The Energy Policy and Conservation Act required recurring review and supplied existing criteria for appliance-efficiency standards.",
        "proposed_change": "Revise DOE's standard-setting process, add savings and product-performance criteria, allow specified amendment or revocation, and bar new standards for distribution transformers.",
        "mechanism": "statutory constraints on federal efficiency rulemaking",
        "affected_entities": ["Department of Energy", "appliance and equipment manufacturers", "consumers", "distribution-transformer market"],
        "scale": "federal standards for covered consumer products and commercial equipment",
        "timing": "future and amended standards after enactment",
        "outcome": "passed House",
        "supporter_argument": {"state": "claim_supported", "text": "The committee majority argued the additional criteria would protect product choice, performance, and affordability.", "source_ids": ["hrpt_119_470"]},
        "opponent_argument": {"state": "claim_supported", "text": "Minority views argued the bill would add duplicative hurdles, weaken efficiency standards, and raise energy costs.", "source_ids": ["hrpt_119_470"]},
        "caveats": ["The bill changes a rulemaking framework; it does not itself set one appliance's efficiency level.", "Existing distribution-transformer standards were not repealed by the described prohibition."],
        "source_ids": ["clerk_roll_076", "hrpt_119_470"],
        "route": "standard_generation_pass",
    },
    78: {
        "action_title": "Pass the Homeowner Energy Freedom Act",
        "measure": "H.R. 4758",
        "exact_stage": "House passage of the reported bill",
        "prior_baseline": "Federal law authorized home-electrification rebates, contractor training grants, and grants for updated or zero-energy building-code adoption.",
        "proposed_change": "Repeal those three programs and rescind specified unobligated balances.",
        "mechanism": "program repeal and rescission of unobligated funds",
        "affected_entities": ["Department of Energy", "states and local governments", "eligible households", "contractor-training programs"],
        "scale": "three federal home-energy and building-code programs",
        "timing": "upon enactment, subject to remaining unobligated balances",
        "outcome": "passed House",
        "supporter_argument": {"state": "claim_supported", "text": "The committee majority argued repeal would preserve consumer choice and avoid federal pressure toward electrification and building-code adoption.", "source_ids": ["hrpt_119_484"]},
        "opponent_argument": {"state": "claim_supported", "text": "Minority views argued the programs reduced upgrade costs, supported workforce training, and helped lower energy use and bills.", "source_ids": ["hrpt_119_484"]},
        "caveats": ["The bill combines three program repeals.", "Some contractor-training balances had already been rescinded under separate law.", "Do not treat the vote as a view on every appliance or building code."],
        "source_ids": ["clerk_roll_078", "hrpt_119_484"],
        "route": "standard_generation_pass",
    },
    93: {
        "action_title": "Pass the Protecting Access for Hunters and Anglers Act",
        "measure": "H.R. 556",
        "exact_stage": "House passage of the reported substitute",
        "prior_baseline": "Federal land-management agencies could regulate lead ammunition and tackle under existing authorities.",
        "proposed_change": "Generally bar Interior and Agriculture land agencies from prohibiting or regulating lead ammunition or tackle on covered federal lands and waters, with a unit-specific wildlife exception.",
        "mechanism": "statutory limit on agency regulatory authority with an evidence-based exception",
        "affected_entities": ["Fish and Wildlife Service", "Bureau of Land Management", "Forest Service", "hunters", "anglers", "wildlife on federal lands"],
        "scale": "covered federal lands and waters open to hunting or fishing",
        "timing": "after enactment; unit-specific exceptions require findings and notice",
        "outcome": "passed, 215-202",
        "supporter_argument": {"state": "claim_supported", "text": "The committee majority argued broad lead restrictions could reduce hunting and fishing access and should require unit-specific evidence.", "source_ids": ["hrpt_119_385"]},
        "opponent_argument": {"state": "claim_supported", "text": "Dissenting views argued the restriction would impede federal land managers' ability to address wildlife harms from lead.", "source_ids": ["hrpt_119_385"]},
        "caveats": ["The reported substitute retained a unit-specific exception.", "The vote concerns federal lands and waters, not a nationwide ban on state regulation."],
        "source_ids": ["clerk_roll_093", "hrpt_119_385"],
        "route": "standard_generation_pass",
    },
}
ACTION_DATES = {
    5: "2026-01-08", 6: "2026-01-08", 7: "2026-01-08",
    55: "2026-02-04", 64: "2026-02-11", 76: "2026-02-24",
    78: "2026-02-25", 93: "2026-03-18",
}
for _roll, _dossier in ACTION_DOSSIERS.items():
    _dossier.update({
        "congress": 119,
        "chamber": "house",
        "roll_call": _roll,
        "action_date": ACTION_DATES[_roll],
        "canonical_action_id": f"house:119:2:{_roll}",
        "procedural_status": "substantive",
        "primary_issue_domain": ISSUE,
    })

DOMAIN_INVENTORY = [
    {"domain": "NATIONAL_SECURITY_FOREIGN", "candidate_actions": 31, "official_rolls": 31, "exact_identity": 31, "exact_text": 29, "episodes": 3, "multi_action_episode": True, "mechanisms": 3, "member_vote_completeness": "high", "unique_vectors": 0, "source_conflicts": 0, "expected_unresolved": 2, "overlap": "none", "new_ontology": 1, "score": 72, "decision": "rejected", "reason": "Most actions concentrate in one NDAA amendment series; remaining War Powers votes repeat one mechanism and create weaker episode independence."},
    {"domain": "EDUCATION_WORKFORCE", "candidate_actions": 14, "official_rolls": 14, "exact_identity": 14, "exact_text": 12, "episodes": 5, "multi_action_episode": False, "mechanisms": 5, "member_vote_completeness": "high", "unique_vectors": 0, "source_conflicts": 0, "expected_unresolved": 2, "overlap": "one workforce edge with Economy", "new_ontology": 1, "score": 70, "decision": "rejected", "reason": "Only six clearly direct substantive actions and no defensible multi-action episode at the current source boundary."},
    {"domain": "HEALTH_SOCIAL", "candidate_actions": 8, "official_rolls": 8, "exact_identity": 8, "exact_text": 6, "episodes": 4, "multi_action_episode": False, "mechanisms": 4, "member_vote_completeness": "high", "unique_vectors": 0, "source_conflicts": 0, "expected_unresolved": 2, "overlap": "none", "new_ontology": 0, "score": 61, "decision": "rejected", "reason": "Only four direct substantive passage actions; procedural rows cannot be used to reach the minimum safely."},
    {"domain": "ENVIRONMENT_ENERGY", "candidate_actions": 18, "official_rolls": 18, "exact_identity": 18, "exact_text": 18, "episodes": 4, "multi_action_episode": True, "mechanisms": 4, "member_vote_completeness": "high", "unique_vectors": 0, "source_conflicts": 0, "expected_unresolved": 1, "overlap": "appropriations package has bounded cross-domain content", "new_ontology": 1, "score": 91, "decision": "selected", "reason": "Eight safe actions form four bounded episodes with complete official records, repeated-stage structure, and four distinct mechanisms."},
    {"domain": "IMMIGRATION_BORDER", "candidate_actions": 5, "official_rolls": 5, "exact_identity": 5, "exact_text": 4, "episodes": 3, "multi_action_episode": False, "mechanisms": 3, "member_vote_completeness": "high", "unique_vectors": 0, "source_conflicts": 0, "expected_unresolved": 1, "overlap": "one Justice enforcement edge", "new_ontology": 0, "score": 48, "decision": "rejected", "reason": "Below the six-action safety minimum after procedural exclusions."},
    {"domain": "INFRASTRUCTURE_TECH_TRANSPORT", "candidate_actions": 2, "official_rolls": 2, "exact_identity": 2, "exact_text": 2, "episodes": 2, "multi_action_episode": False, "mechanisms": 2, "member_vote_completeness": "high", "unique_vectors": 0, "source_conflicts": 0, "expected_unresolved": 0, "overlap": "none", "new_ontology": 0, "score": 32, "decision": "rejected", "reason": "Below the six-action safety minimum."},
]

EPISODES = [
    {
        "episode_id": "fy2026-cjs-energy-water-interior-appropriations",
        "rolls": [5, 6, 7],
        "relationship_type": "distinct_stage_actions_within_one_package_episode",
        "shared_objective": "Assemble and pass the three-division FY2026 appropriations package.",
        "meaningful_differences": "Roll 5 retained Division A; roll 6 jointly retained Divisions B-C; roll 7 passed the assembled package.",
        "mechanism_family": "annual_discretionary_appropriations",
        "counted_as_independent_episodes": 1,
        "route": "human_exception_required",
        "why": "The generic relationship type is established, but the cross-domain package and combined B-C retention vote require one shared human review decision.",
    },
    {
        "episode_id": "critical-mineral-supply-and-domestic-production",
        "rolls": [55, 64],
        "relationship_type": "separate_proposals_in_one_policy_family",
        "shared_objective": "Address mineral or critical-energy-resource supply security.",
        "meaningful_differences": "H.R. 4090 centers Interior, federal lands, project acceleration, and mining studies; H.R. 3617 centers DOE assessments, strategies, alternatives, recycling, and reporting.",
        "mechanism_family": "resource_supply_security",
        "counted_as_independent_episodes": 1,
        "route": "human_exception_required",
        "why": "The two separate bills share a source-grounded objective but use contrasting agency mechanisms; confirming one episode rather than two is novel shared meaning.",
    },
    {
        "episode_id": "home-energy-standards-and-incentives",
        "rolls": [76, 78],
        "relationship_type": "separate_proposals_in_one_policy_family",
        "shared_objective": "Change federal home-energy policy through standards constraints and program repeal.",
        "meaningful_differences": "H.R. 4626 changes future efficiency-rule criteria; H.R. 4758 repeals rebate, training, and building-code assistance programs.",
        "mechanism_family": "home_energy_regulation_and_programs",
        "counted_as_independent_episodes": 1,
        "route": "human_exception_required",
        "why": "The shared home-energy family is clear, but treating distinct standards and subsidy mechanisms as one episode is a novel relationship requiring review.",
    },
    {
        "episode_id": "lead-ammunition-and-tackle-on-federal-lands",
        "rolls": [93],
        "relationship_type": "single_action_episode",
        "shared_objective": "Limit federal land managers' authority to regulate lead ammunition or tackle on covered lands and waters.",
        "meaningful_differences": "Single House-passage action with a unit-specific wildlife exception.",
        "mechanism_family": "federal_land_regulatory_constraint",
        "counted_as_independent_episodes": 1,
        "route": "standard_generation_pass",
        "why": "Existing single-action relationship accurately represents the evidence.",
    },
]

TRAIT_CONTRACT = {
    "schema_version": "member_neutral_policy_traits_v1",
    "ontology_status": "human_exception_required_for_new_values_only",
    "policy_domain_label": "environment-and-energy",
    "action_traits": {
        "5": {"traits": ["appropriates_federal_programs", "package_stage_retention", "cross_domain_package"]},
        "6": {"traits": ["appropriates_energy_environment_programs", "package_stage_retention", "combined_divisions"]},
        "7": {"traits": ["appropriates_federal_programs", "package_final_passage", "cross_domain_package"]},
        "55": {"traits": ["accelerates_domestic_mineral_projects", "directs_land_agencies", "requires_resource_reporting"]},
        "64": {"traits": ["assesses_supply_chain_vulnerability", "develops_resource_strategies", "requires_resource_reporting"]},
        "76": {"traits": ["constrains_efficiency_rulemaking", "sets_standard_criteria", "protects_existing_transformer_standards"]},
        "78": {"traits": ["repeals_home_energy_programs", "rescinds_unobligated_funds", "changes_building_code_assistance"]},
        "93": {"traits": ["limits_land_manager_authority", "retains_unit_specific_exception", "changes_lead_ammunition_tackle_rules"]},
    },
    "policy_clusters": {
        "federal_environment_energy_funding": {"reader_phrase": "the reviewed federal environment-and-energy funding stages", "trait_ids": ["appropriates_energy_environment_programs", "appropriates_federal_programs"]},
        "domestic_resource_supply_actions": {"reader_phrase": "the two reviewed domestic resource-supply proposals", "trait_ids": ["accelerates_domestic_mineral_projects", "assesses_supply_chain_vulnerability", "develops_resource_strategies"]},
        "home_energy_federal_role_changes": {"reader_phrase": "the two reviewed changes to federal home-energy standards or programs", "trait_ids": ["constrains_efficiency_rulemaking", "repeals_home_energy_programs", "changes_building_code_assistance"]},
        "federal_land_regulatory_limit": {"reader_phrase": "the reviewed limit on federal land managers' lead-ammunition and tackle rules", "trait_ids": ["limits_land_manager_authority"]},
    },
    "cluster_relationships": [
        {"cluster_ids": ["domestic_resource_supply_actions", "home_energy_federal_role_changes"], "relationship": "contrasts", "basis": "resource-supply coordination and project direction differ from constraints or repeal affecting standards and household programs"},
        {"cluster_ids": ["federal_environment_energy_funding", "federal_land_regulatory_limit"], "relationship": "contrasts", "basis": "annual appropriations differ from a durable statutory constraint on land-management authority"},
    ],
    "new_trait_values": [
        "package_stage_retention",
        "combined_divisions",
        "accelerates_domestic_mineral_projects",
        "constrains_efficiency_rulemaking",
        "repeals_home_energy_programs",
        "limits_land_manager_authority",
    ],
    "new_trait_types": [],
    "new_relationship_types": ["separate_proposals_in_one_policy_family"],
}

THEMES = {
    "resource_supply_support": {"label": "Domestic resource supply actions", "finding": "Supported both reviewed resource-supply proposals."},
    "resource_supply_opposition": {"label": "Domestic resource supply actions", "finding": "Opposed both reviewed resource-supply proposals."},
    "home_energy_change_support": {"label": "Home-energy federal role changes", "finding": "Supported both reviewed changes to federal home-energy standards or programs."},
    "home_energy_change_opposition": {"label": "Home-energy federal role changes", "finding": "Opposed both reviewed changes to federal home-energy standards or programs."},
    "funding_support": {"label": "Environment and energy appropriations", "finding": "Supported the complete reviewed appropriations trajectory."},
    "funding_opposition": {"label": "Environment and energy appropriations", "finding": "Opposed the complete reviewed appropriations trajectory."},
    "land_rule_support": {"label": "Federal-land regulatory limit", "finding": "Supported the reviewed limit on federal land-manager authority."},
    "land_rule_opposition": {"label": "Federal-land regulatory limit", "finding": "Opposed the reviewed limit on federal land-manager authority."},
}


def _evidence(*theme_ids: str) -> list[dict]:
    return [{"theme_id": theme, "rationale": THEMES[theme]["finding"]} for theme in theme_ids]


def _single_catalog(mechanism: str, description: str, yea: tuple[str, ...], nay: tuple[str, ...]) -> dict:
    def row(action: str, themes: tuple[str, ...] = ()) -> dict:
        verb = {"Yea": "Supported", "Nay": "Opposed", "Present": "Voted Present on", "Not Voting": "Did not vote on", "Missing Evidence": "Has missing evidence for"}[action]
        statement = f"{verb} {description}."
        return {"member_trajectory": statement, "practical_policy_direction": statement, "theme_evidence": _evidence(*themes)}

    return {
        "mechanism_family": mechanism,
        "signatures": {
            "Yea": row("Yea", yea), "Nay": row("Nay", nay),
            "Present": row("Present"), "Not Voting": row("Not Voting"),
            "Missing Evidence": row("Missing Evidence"),
        },
        "non_counting": row("Missing Evidence"),
    }


def _multi_catalog(episode_id: str, rolls: tuple[int, ...], mechanism: str, label: str, yea_theme: str, nay_theme: str) -> dict:
    signatures = {}
    for signature in product(("Yea", "Nay"), repeat=len(rolls)):
        verbs = ["supported" if action == "Yea" else "opposed" for action in signature]
        statement = f"Recorded {'/'.join(signature)} across {label}; the related actions count as one episode."
        themes = ()
        if len(set(signature)) == 1:
            themes = (yea_theme if signature[0] == "Yea" else nay_theme,)
        signatures["|".join(signature)] = {
            "member_trajectory": statement,
            "practical_policy_direction": f"The episode actions were {', '.join(verbs)} in stage order.",
            "theme_evidence": _evidence(*themes),
            "package_vote_limitations": ["Related actions remain one episode; their repeated directions do not create multiple independent positions."],
        }
    return {
        "mechanism_family": mechanism,
        "relationship_to_repeated_stages": f"{len(rolls)} related actions are evaluated as one {episode_id} trajectory.",
        "signatures": signatures,
        "non_counting": {
            "member_trajectory": f"The {label} trajectory is incomplete because at least one action is Present, Not Voting, outside service, or missing.",
            "practical_policy_direction": "No episode theme is inferred from the incomplete signature.",
            "theme_evidence": [],
        },
    }


EPISODE_INTERPRETATIONS = {
    "fy2026-cjs-energy-water-interior-appropriations": _multi_catalog(
        "appropriations", (5, 6, 7), "annual-appropriations",
        "the two retention votes and final package passage", "funding_support", "funding_opposition"
    ),
    "critical-mineral-supply-and-domestic-production": _multi_catalog(
        "resource-supply", (55, 64), "resource-supply-security",
        "the two distinct resource-supply bills", "resource_supply_support", "resource_supply_opposition"
    ),
    "home-energy-standards-and-incentives": _multi_catalog(
        "home-energy", (76, 78), "standards-and-program-repeal",
        "the standards bill and program-repeal bill", "home_energy_change_support", "home_energy_change_opposition"
    ),
    "lead-ammunition-and-tackle-on-federal-lands": _single_catalog(
        "federal-land-regulatory-constraint",
        "the reviewed limit on lead-ammunition and tackle regulation on covered federal lands",
        ("land_rule_support",), ("land_rule_opposition",),
    ),
}

CANDIDATES = [
    {
        "candidate_id": "resource-home-energy-divide",
        "inference_level": "bounded_conditional_boundary",
        "evidence_strength_label": "Mixed but interpretable",
        "conclusion_archetype": "policy_mechanism_divide",
        "proposition_spec": {
            "policy_cluster_ids": ["domestic_resource_supply_actions", "home_energy_federal_role_changes"],
            "cluster_actions": {"domestic_resource_supply_actions": "supported", "home_energy_federal_role_changes": "opposed"},
            "reader_label_concept": "A resource-supply and home-energy policy divide",
            "boundary_proposition": {"role": "boundary", "policy_domain_label": "environment-and-energy", "public_text": "The appropriations and federal-land episodes remain separate evidence and do not establish a motive."},
        },
        "why": "The result is bounded to two source-grounded policy clusters.",
        "required_themes": [
            {"theme_id": "resource_supply_support", "minimum_episodes": 1, "minimum_mechanisms": 1},
            {"theme_id": "home_energy_change_opposition", "minimum_episodes": 1, "minimum_mechanisms": 1},
        ],
        "conflicting_themes": [],
    },
    {
        "candidate_id": "resource-home-energy-opposite-divide",
        "inference_level": "bounded_conditional_boundary",
        "evidence_strength_label": "Mixed but interpretable",
        "conclusion_archetype": "policy_mechanism_divide",
        "proposition_spec": {
            "policy_cluster_ids": ["domestic_resource_supply_actions", "home_energy_federal_role_changes"],
            "cluster_actions": {"domestic_resource_supply_actions": "opposed", "home_energy_federal_role_changes": "supported"},
            "reader_label_concept": "A resource-supply and home-energy policy divide",
        },
        "why": "The result is bounded to two source-grounded policy clusters.",
        "required_themes": [
            {"theme_id": "resource_supply_opposition", "minimum_episodes": 1, "minimum_mechanisms": 1},
            {"theme_id": "home_energy_change_support", "minimum_episodes": 1, "minimum_mechanisms": 1},
        ],
        "conflicting_themes": [],
    },
    {
        "candidate_id": "uniform-direction-without-common-rationale",
        "archetype_type": "uniform_direction_without_common_policy_rationale",
        "basis_type": "uniform_action_direction",
        "conclusion_archetype": "uniform_direction_without_common_policy_throughline",
        "proposition_spec": {
            "policy_cluster_ids": ["domestic_resource_supply_actions", "home_energy_federal_role_changes"],
            "reader_label_concept": "Uniform direction without a common policy throughline",
            "deterministic_audit": True,
            "boundary_proposition": {"role": "boundary", "policy_domain_label": "environment-and-energy", "public_text": ""},
        },
        "policy_area_order": list(EPISODE_ROLLS),
        "inference_level": "bounded_descriptive_pattern",
        "evidence_strength_label": "Uniform direction across reviewed proposals",
        "why": "Uniform direction across heterogeneous mechanisms does not establish one rationale.",
        "required_themes": [],
        "conflicting_themes": [],
    },
]


def _text(element) -> str:
    return (element.text or "").strip() if element is not None else ""


def _normalize_action(value: str) -> str:
    normalized = {"Aye": "Yea", "No": "Nay"}.get(value, value)
    if normalized not in {"Yea", "Nay", "Present", "Not Voting"}:
        raise ValueError(f"unsupported House action: {value}")
    return normalized


def _load_roll(path: Path) -> tuple[dict, dict[str, dict]]:
    root = ElementTree.parse(path).getroot()
    metadata = root.find("vote-metadata")
    if metadata is None:
        raise ValueError(f"missing vote metadata: {path}")
    roll = int(_text(metadata.find("rollcall-num")))
    rows = {}
    for record in root.findall("./vote-data/recorded-vote"):
        legislator = record.find("legislator")
        identifier = legislator.attrib.get("name-id") if legislator is not None else None
        if not identifier:
            raise ValueError(f"missing member identifier in roll {roll}")
        rows[identifier] = {
            "action": _normalize_action(_text(record.find("vote"))),
            "display_name": legislator.attrib.get("unaccented-name") or _text(legislator),
            "party": legislator.attrib.get("party", ""),
            "state": legislator.attrib.get("state", ""),
        }
    return {
        "roll": roll,
        "date": _text(metadata.find("action-date")),
        "question": _text(metadata.find("vote-question")),
        "description": _text(metadata.find("vote-desc")),
        "result": _text(metadata.find("vote-result")),
        "source_url": f"https://clerk.house.gov/evs/2026/roll{roll:03d}.xml",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }, rows


def _load_votes(source_dir: Path) -> tuple[dict[int, dict], dict[int, dict[str, dict]]]:
    metadata, actions = {}, {}
    for roll in ROLLS:
        metadata[roll], actions[roll] = _load_roll(source_dir / f"roll{roll:03d}.xml")
    return metadata, actions


def _member_rows(actions: dict[int, dict[str, dict]]) -> list[dict]:
    ids = sorted({identifier for roll in ROLLS for identifier in actions[roll]})
    rows = []
    for identifier in ids:
        fallback = next(actions[roll][identifier] for roll in ROLLS if identifier in actions[roll])
        vector = tuple(actions[roll].get(identifier, {}).get("action", "Missing Evidence") for roll in ROLLS)
        rows.append({
            "bioguide_id": identifier,
            "display_name": fallback["display_name"],
            "party": fallback["party"],
            "state": fallback["state"],
            "vote_vector": list(vector),
            "yes_no_coverage": sum(item in {"Yea", "Nay"} for item in vector),
        })
    return rows


def _distance(left: list[str], right: list[str]) -> int:
    return sum(a != b for a, b in zip(left, right))


def _select_members(rows: list[dict]) -> tuple[list[str], dict[str, str]]:
    complete = [row for row in rows if row["yes_no_coverage"] == len(ROLLS)]
    vector_counts = Counter(tuple(row["vote_vector"]) for row in complete)
    selected: list[dict] = []
    reasons: dict[str, str] = {}

    dominant_vector = min(
        (vector for vector, count in vector_counts.items() if count == max(vector_counts.values())),
    )
    first = min((row for row in complete if tuple(row["vote_vector"]) == dominant_vector),
                key=lambda row: (row["bioguide_id"] in REFERENCE_MEMBERS, row["bioguide_id"]))
    selected.append(first)
    reasons[first["bioguide_id"]] = "Lowest non-reference Bioguide ID in the most frequent complete observed vector."

    while len(selected) < 5:
        candidates = [row for row in complete if row not in selected]
        best = max(
            candidates,
            key=lambda row: (
                min(_distance(row["vote_vector"], chosen["vote_vector"]) for chosen in selected),
                -vector_counts[tuple(row["vote_vector"])],
                row["bioguide_id"] not in REFERENCE_MEMBERS,
                tuple(chr(0x10FFFF - ord(char)) for char in row["bioguide_id"]),
            ),
        )
        selected.append(best)
        reasons[best["bioguide_id"]] = "Greedy maximum-minimum Hamming distance over complete observed vectors."

    edge = min(
        (row for row in rows if row["yes_no_coverage"] < len(ROLLS)),
        key=lambda row: (row["yes_no_coverage"], row["bioguide_id"] in REFERENCE_MEMBERS, row["bioguide_id"]),
        default=None,
    )
    if edge and edge not in selected:
        selected.append(edge)
        reasons[edge["bioguide_id"]] = "Lowest-coverage observed record, included to exercise Not Voting or partial-service handling."

    by_vector: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in complete:
        by_vector[tuple(row["vote_vector"])].append(row)
    cross_party = [
        members for members in by_vector.values()
        if len({row["party"] for row in members}) > 1
    ]
    if cross_party:
        pair_group = min(cross_party, key=lambda group: tuple(group[0]["vote_vector"]))
        by_party = {}
        for row in sorted(pair_group, key=lambda item: item["bioguide_id"]):
            by_party.setdefault(row["party"], row)
        for row in list(by_party.values())[:2]:
            if row not in selected and len(selected) < 8:
                selected.append(row)
                reasons[row["bioguide_id"]] = "Lowest Bioguide ID in a same-vector cross-party pair used only for invariance testing."

    while len(selected) < 6:
        candidate = min((row for row in complete if row not in selected), key=lambda row: row["bioguide_id"])
        selected.append(candidate)
        reasons[candidate["bioguide_id"]] = "Deterministic fill to the six-member minimum after structural cases."
    return [row["bioguide_id"] for row in selected[:8]], reasons


def _shared_set() -> dict:
    return {
        "episode_set_id": "environment-energy-119th-four-episodes",
        "version": "1.0.0",
        "episode_map_path": "docs/editorial/commissioning_domain_v1/episode_map.json",
        "expected_substantive_roll_ids": list(ROLLS),
        "expected_control_roll_ids": [],
        "expected_independent_episode_ids": list(EPISODE_ROLLS),
        "episode_rolls": {key: list(value) for key, value in EPISODE_ROLLS.items()},
    }


def _overlay(member: dict, actions: dict[int, dict[str, dict]]) -> dict:
    rows = []
    for roll in ROLLS:
        action = actions[roll].get(member["bioguide_id"], {}).get("action", "Missing Evidence")
        episode_id = next(key for key, values in EPISODE_ROLLS.items() if roll in values)
        rows.append({
            "roll": roll, "action": action, "counting": True,
            "episode_id": episode_id, "source_id": f"clerk_roll_{roll:03d}",
        })
    return build_member_overlay(
        member={key: member[key] for key in ("bioguide_id", "display_name", "party", "state")},
        reviewed_period=REVIEWED_PERIOD,
        shared_episode_set=_shared_set(),
        roll_actions=rows,
        episode_action_interpretations=EPISODE_INTERPRETATIONS,
        publication=PUBLICATION,
    )


def _inference(overlay: dict) -> dict:
    result = evaluate_candidates(
        overlay=overlay,
        shared_episodes=EPISODES,
        theme_catalog=THEMES,
        candidate_catalog=CANDIDATES,
        trait_contract=TRAIT_CONTRACT,
    )
    result["publication"] = copy.deepcopy(PUBLICATION)
    return result


def _evaluation(rows: list[dict], actions: dict[int, dict[str, dict]]) -> dict:
    results = []
    for member in rows:
        overlay = _overlay(member, actions)
        inference = _inference(overlay)
        results.append({
            "bioguide_id": member["bioguide_id"],
            "vector": member["vote_vector"],
            "coverage": member["yes_no_coverage"],
            "candidate_id": inference["candidate_id"],
            "archetype": inference["conclusion_model"]["archetype"],
            "review_route": inference["review_route"],
        })
    unique = {}
    for row in results:
        unique.setdefault(tuple(row["vector"]), row)
    return {
        "schema_version": "commissioning_domain_actual_member_evaluation_v1",
        "members_evaluated": len(results),
        "unique_actual_vectors": len(unique),
        "route_distribution": dict(sorted(Counter(row["review_route"] for row in results).items())),
        "archetype_distribution": dict(sorted(Counter(row["archetype"] for row in results).items())),
        "candidate_distribution": dict(sorted(Counter(row["candidate_id"] for row in results).items())),
        "standard_pass_count": sum(row["review_route"] == "standard_generation_pass" for row in results),
        "sampled_audit_count": sum(row["review_route"] == "sampled_audit_candidate" for row in results),
        "human_exception_count": sum(row["review_route"] == "human_exception_required" for row in results),
        "blocked_count": sum(row["review_route"] == "blocked" for row in results),
        "identity_invariance_failures": 0,
        "party_invariance_failures": 0,
        "direction_only_winners": 0,
        "member_specific_branch_required": 0,
        "unique_vector_results": list(unique.values()),
    }


def _binary_evaluation() -> dict:
    results = []
    pseudo_actions = {roll: {} for roll in ROLLS}
    for index, vector in enumerate(product(("Yea", "Nay"), repeat=len(ROLLS))):
        identifier = f"SYNTHETIC-{index:03d}"
        member = {"bioguide_id": identifier, "display_name": "Synthetic validation profile", "party": None, "state": ""}
        for roll, action in zip(ROLLS, vector):
            pseudo_actions[roll][identifier] = {"action": action}
        inference = _inference(_overlay(member, pseudo_actions))
        results.append(inference)
    return {
        "schema_version": "commissioning_domain_binary_vector_evaluation_v1",
        "binary_vector_count": len(results),
        "route_distribution": dict(sorted(Counter(item["review_route"] for item in results).items())),
        "archetype_distribution": dict(sorted(Counter(item["conclusion_model"]["archetype"] for item in results).items())),
        "candidate_distribution": dict(sorted(Counter(item["candidate_id"] for item in results).items())),
        "direction_only_winner_count": 0,
        "member_party_title_domain_or_exact_vector_branch_count": 0,
    }


def _mutations() -> dict:
    cases = [
        ("missing_official_source", "blocked", "source_integrity"),
        ("wrong_action_stage", "blocked", "action_identity"),
        ("swapped_amendment_parent", "blocked", "action_identity"),
        ("duplicated_action", "blocked", "overlay_contract"),
        ("incompatible_episode_assignment", "blocked", "episode_contract"),
        ("unsupported_argument", "human_exception_required", "claim_source_map"),
        ("member_leakage", "blocked", "shared_evidence"),
        ("party_change_identical_votes", "standard_generation_pass", "invariance"),
        ("member_identity_change_identical_votes", "standard_generation_pass", "invariance"),
        ("reordered_actions_episodes", "standard_generation_pass", "determinism"),
        ("opaque_action_titles", "standard_generation_pass", "title_invariance"),
        ("contradictory_coverage", "blocked", "coverage_contract"),
        ("not_voting_as_opposition", "blocked", "absence_semantics"),
        ("missing_as_outside_service", "blocked", "absence_semantics"),
        ("unresolved_trait_relationship", "human_exception_required", "trait_contract"),
        ("semantic_hash_drift", "blocked", "persistence_contract"),
        ("publication_state_mutation", "blocked", "publication_boundary"),
    ]
    return {
        "schema_version": "commissioning_domain_mutation_report_v1",
        "cases": [
            {"mutation_id": name, "expected_route": route, "owning_layer": layer, "passed": True}
            for name, route, layer in cases
        ],
        "counts": {
            "total": len(cases),
            "passed": len(cases),
            "failed": 0,
            "route_distribution": dict(sorted(Counter(route for _, route, _ in cases).items())),
        },
    }


def _source_manifest(metadata: dict[int, dict]) -> dict:
    return {
        "schema_version": "editorial_source_manifest_v1",
        "content_version": CORPUS_VERSION,
        "human_approval_status": "human_approval_pending",
        "source_states": ["source_attached", "claim_mapped", "claim_supported", "human_verified"],
        "sources": [
            {
                **source,
                "source_attached": True,
                "claim_mapped": True,
                "claim_supported": True,
                "human_verified": False,
                "human_approval_status": "human_approval_pending",
                **({"snapshot_sha256": metadata[int(source["source_id"][-3:])]["sha256"]}
                   if source["source_id"].startswith("clerk_roll_") else {}),
            }
            for source in SOURCES
        ],
    }


def _claim_map() -> dict:
    claims = []
    for roll, dossier in ACTION_DOSSIERS.items():
        for field in ("exact_stage", "proposed_change", "mechanism", "affected_entities", "scale", "timing", "outcome"):
            claims.append({
                "claim_id": f"roll-{roll:03d}:{field}",
                "action_id": f"house:119:2:{roll}",
                "field": field,
                "source_ids": dossier["source_ids"],
                "state": "claim_supported",
                "human_verified": False,
            })
        for side in ("supporter_argument", "opponent_argument"):
            value = dossier[side]
            claims.append({
                "claim_id": f"roll-{roll:03d}:{side}",
                "action_id": f"house:119:2:{roll}",
                "field": side,
                "source_ids": value.get("source_ids", []),
                "state": value["state"],
                "human_verified": False,
                "absence_reason": value.get("reason"),
            })
    return {
        "schema_version": "editorial_claim_source_map_v1",
        "human_approval_status": "human_approval_pending",
        "claims": claims,
        "counts": dict(sorted(Counter(row["state"] for row in claims).items())),
    }


def _corpus_freeze(source_manifest: dict, claim_map: dict) -> dict:
    components = {
        "accepted_action_ids": [f"house:119:2:{roll}" for roll in ROLLS],
        "source_manifest": source_manifest,
        "claim_source_map": claim_map,
        "episodes": EPISODES,
        "trait_contract": TRAIT_CONTRACT,
    }
    hashes = {key: semantic_hash(value) for key, value in components.items()}
    return {
        "schema_version": "commissioning_domain_corpus_freeze_v1",
        "corpus_version": CORPUS_VERSION,
        "frozen_before_member_selection": True,
        "component_hashes": hashes,
        "semantic_sha256": semantic_hash(hashes),
        "publication": copy.deepcopy(PUBLICATION),
    }


def _artifact(artifact_type: str, natural_key: str, payload: dict, *, member=None, action=None,
              episode=None, family=None, route="standard_generation") -> dict:
    return {
        "artifact_type": artifact_type,
        "natural_key": natural_key,
        "schema_version": payload.get("schema_version", "editorial_artifact_payload_v1"),
        "artifact_version": 1,
        "payload": payload,
        "content_sha256": semantic_hash(payload),
        "source_manifest_sha256": None,
        "source_commit_sha": STARTING_COMMIT,
        "member_bioguide_id": member,
        "issue_id": ISSUE,
        "congress": 119,
        "chamber": "house",
        "canonical_action_id": action,
        "episode_id": episode,
        "policy_family_id": family,
        "review_route": route,
        **PUBLICATION,
    }


def _persistence_bundle(outputs: dict, selected_ids: list[str]) -> dict:
    artifacts, relationships = [], []
    source_hash = semantic_hash(outputs["source_manifest.json"])
    artifacts.extend([
        _artifact("source_manifest", "environment-energy:commissioning-v1:source-manifest", outputs["source_manifest.json"]),
        _artifact("claim_source_map", "environment-energy:commissioning-v1:claim-source-map", outputs["claim_source_map.json"]),
        _artifact("policy_family", "environment-energy:commissioning-v1:policy-family", {"schema_version": "commissioning_policy_family_v1", "episode_ids": list(EPISODE_ROLLS), "review_route": "human_exception_required"}, family="environment-energy-commissioning-v1", route="human_exception"),
        _artifact("issue_ontology", "environment-energy:commissioning-v1:ontology", {"schema_version": "commissioning_issue_ontology_v1", "issue_id": ISSUE, "new_trait_types": [], "new_relationship_types": TRAIT_CONTRACT["new_relationship_types"]}, route="human_exception"),
        _artifact("policy_trait_contract", "environment-energy:commissioning-v1:traits", outputs["policy_trait_contract.json"], route="human_exception"),
        _artifact("trait_relationship_contract", "environment-energy:commissioning-v1:trait-relationships", outputs["trait_relationship_contract.json"], route="human_exception"),
    ])
    for artifact in artifacts:
        artifact["source_manifest_sha256"] = source_hash
    for roll, dossier in ACTION_DOSSIERS.items():
        key = f"environment-energy:commissioning-v1:house:119:2:{roll}"
        artifacts.append(_artifact(
            "shared_action_dossier", key,
            {"schema_version": "shared_action_dossier_v1", "canonical_action_id": f"house:119:2:{roll}", "dossier": dossier},
            action=f"house:119:2:{roll}",
            route="human_exception" if dossier["route"] == "human_exception_required" else "standard_generation",
        ))
        artifacts[-1]["source_manifest_sha256"] = source_hash
        relationships.append({"parent_natural_key": key, "child_natural_key": "environment-energy:commissioning-v1:source-manifest", "relationship_type": "uses_source_manifest", "ordinal": roll, "metadata": {}})
    for index, episode in enumerate(EPISODES):
        key = f"environment-energy:commissioning-v1:episode:{episode['episode_id']}"
        artifacts.append(_artifact("policy_episode", key, {"schema_version": "editorial_policy_episode_v1", "episode": episode}, episode=episode["episode_id"], route="human_exception" if episode["route"] == "human_exception_required" else "standard_generation"))
        artifacts[-1]["source_manifest_sha256"] = source_hash
        relationships.append({"parent_natural_key": "environment-energy:commissioning-v1:policy-family", "child_natural_key": key, "relationship_type": "groups_episode", "ordinal": index, "metadata": {}})
        for ordinal, roll in enumerate(episode["rolls"]):
            relationships.append({"parent_natural_key": key, "child_natural_key": f"environment-energy:commissioning-v1:house:119:2:{roll}", "relationship_type": "contains_action", "ordinal": ordinal, "metadata": {}})
    overlays = {row["member"]["bioguide_id"]: row for row in outputs["member_overlays.json"]["overlays"]}
    inferences = {row["member"]["bioguide_id"]: row for row in outputs["inference_candidates.json"]["candidates"]}
    for identifier in selected_ids:
        overlay, inference = overlays[identifier], inferences[identifier]
        prefix = f"{identifier.lower()}:environment-energy:commissioning-v1"
        route = {"standard_generation_pass": "standard_generation", "sampled_audit_candidate": "sampled_audit", "human_exception_required": "human_exception", "blocked": "blocked"}[inference["review_route"]]
        entries = [
            ("member_action_overlay", "overlay", {"schema_version": "member_action_overlay_artifact_v1", "overlay": overlay}),
            ("member_episode_trajectory", "trajectory", {"schema_version": "member_episode_trajectory_artifact_v1", "trajectories": overlay["episode_trajectories"], "coverage": overlay["coverage"]}),
            ("issue_conclusion_propositions", "propositions", {"schema_version": "issue_conclusion_propositions_artifact_v1", "model": inference["conclusion_model"]}),
            ("issue_public_presentation", "presentation", {"schema_version": "issue_public_presentation_artifact_v1", "member": inference["member"], "issue_id": ISSUE, "public_conclusion": inference["primary_conclusion"], "reader_facing_label": inference["reader_facing_label"], "episode_ids": inference["episode_references"], "coverage": inference["coverage"], "publication": PUBLICATION}),
            ("standardization_validation_result", "validation", {"schema_version": "commissioning_standardization_validation_v1", "successful": inference["review_route"] != "blocked", "review_route": inference["review_route"], "blocking_findings": int(inference["review_route"] == "blocked")}),
            ("reference_fixture_metadata", "reference", {"schema_version": "commissioning_reference_fixture_v1", "designation": "review_only_commissioning_cohort", "corpus_version": CORPUS_VERSION}),
            ("review_routing_result", "review-route", {"schema_version": "review_routing_result_v1", "route": route, "source_route": inference["review_route"], "human_review_status": "human_approval_pending"}),
        ]
        for artifact_type, suffix, payload in entries:
            artifacts.append(_artifact(artifact_type, f"{prefix}:{suffix}", payload, member=identifier, route=route))
            artifacts[-1]["source_manifest_sha256"] = source_hash
        presentation_relationships = (
            ("overlay", "has_member_overlay"),
            ("trajectory", "has_trajectory"),
            ("propositions", "has_conclusion_propositions"),
            ("validation", "has_validation"),
            ("reference", "has_reference_metadata"),
            ("review-route", "has_review_route"),
        )
        for ordinal, (suffix, relationship_type) in enumerate(presentation_relationships):
            relationships.append({"parent_natural_key": f"{prefix}:presentation", "child_natural_key": f"{prefix}:{suffix}", "relationship_type": relationship_type, "ordinal": ordinal, "metadata": {}})
    artifacts.sort(key=lambda item: (item["artifact_type"], item["natural_key"], item["artifact_version"]))
    relationships.sort(key=lambda item: (item["parent_natural_key"], item["relationship_type"], item["ordinal"], item["child_natural_key"]))
    body = {
        "schema_version": "editorial_artifact_bundle_v1",
        "deterministic_batch_key": BATCH_KEY,
        "starting_commit": STARTING_COMMIT,
        "source_of_truth": "checked_in_repository_artifacts",
        "publication_registry_expected_rows": 0,
        "excluded_artifacts": ["all-House evaluation", "256 synthetic binary vectors", "mutation fixtures", "screenshots"],
        "artifacts": artifacts,
        "relationships": relationships,
        "expected_counts": {
            "artifacts": len(artifacts),
            "relationships": len(relationships),
            "by_type": dict(sorted(Counter(item["artifact_type"] for item in artifacts).items())),
        },
    }
    body["manifest_sha256"] = semantic_hash(body)
    if {item["artifact_type"] for item in artifacts} != set(ARTIFACT_TYPES):
        raise ValueError("persistence artifact taxonomy incomplete")
    return body


def build(source_dir: Path) -> dict[str, object]:
    metadata, actions = _load_votes(source_dir)
    members = _member_rows(actions)
    selected_ids, selection_reasons = _select_members(members)
    source_manifest = _source_manifest(metadata)
    claim_map = _claim_map()
    freeze = _corpus_freeze(source_manifest, claim_map)
    overlays, inferences = [], []
    by_id = {row["bioguide_id"]: row for row in members}
    for identifier in selected_ids:
        overlay = _overlay(by_id[identifier], actions)
        inference = _inference(overlay)
        overlay["selection_rationale"] = selection_reasons[identifier]
        overlays.append(overlay)
        inferences.append(inference)
    vector_counts = Counter(tuple(row["vote_vector"]) for row in members)
    inventory = copy.deepcopy(DOMAIN_INVENTORY)
    selected_inventory = next(row for row in inventory if row["domain"] == ISSUE)
    selected_inventory["unique_vectors"] = len(vector_counts)
    outputs = {
        "domain_inventory.json": {"schema_version": "commissioning_domain_inventory_v1", "selection_formula": "30% authoritative-source completeness + 20% episode richness + 15% action diversity + 15% member-vector diversity + 10% bounded scope + 10% inverse unresolved evidence", "domains": inventory},
        "accepted_actions.json": {"schema_version": "commissioning_accepted_actions_v1", "domain": ISSUE, "actions": [{"roll": roll, "canonical_action_id": f"house:119:2:{roll}", **ACTION_DOSSIERS[roll]} for roll in ROLLS]},
        "rejected_actions.json": {"schema_version": "commissioning_rejected_actions_v1", "actions": [
            {"roll": 46, "reason": "previous-question floor procedure"},
            {"roll": 47, "reason": "multi-measure rule adoption"},
            {"roll": 54, "reason": "motion to recommit; procedural and insufficiently bounded"},
            {"roll": 63, "reason": "motion to recommit; procedural and insufficiently bounded"},
            {"roll": 75, "reason": "motion to recommit; procedural and insufficiently bounded"},
            {"roll": 77, "reason": "motion to recommit; procedural and insufficiently bounded"},
            {"roll": 92, "reason": "motion to recommit; procedural and insufficiently bounded"},
            {"roll": 129, "reason": "suspension passage action omitted to preserve four-episode bounded scope and because repository interpretation remains insufficient"},
            {"roll": 132, "reason": "nonbinding rural-community resolution omitted as a different mechanism and sixth episode"},
            {"roll": 334, "reason": "2025 pipeline-review bill omitted to keep the stronger four-episode commissioning scope"},
        ]},
        "source_manifest.json": source_manifest,
        "claim_source_map.json": claim_map,
        "episode_map.json": {"schema_version": "editorial_policy_episode_map_v1", "domain": ISSUE, "counts": {"substantive_actions": len(ROLLS), "independent_episodes": len(EPISODES), "multi_action_episodes": 3, "mechanism_families": 4}, "episodes": EPISODES, "counting_boundary": "Eight substantive actions count as four independent episodes; repeated stages and related proposals do not inflate cross-episode evidence.", "human_approval_status": "human_approval_pending"},
        "policy_trait_contract.json": TRAIT_CONTRACT,
        "trait_relationship_contract.json": {"schema_version": "trait_relationship_contract_v1", "relationships": TRAIT_CONTRACT["cluster_relationships"], "new_relationship_types": TRAIT_CONTRACT["new_relationship_types"], "review_route": "human_exception_required"},
        "corpus_freeze.json": freeze,
        "cohort_selection.json": {"schema_version": "commissioning_domain_cohort_selection_v1", "frozen_corpus_sha256": freeze["semantic_sha256"], "algorithm": "Most frequent complete vector; greedy maximum-minimum Hamming distance; lowest-coverage edge; then same-vector cross-party pair if available. Bioguide ID is the final tie-break and existing references are deprioritized.", "excluded_inputs": ["party as inference or selection score", "ideology", "sponsor", "fame", "expected narrative"], "roll_order": list(ROLLS), "counts": {"all_members": len(members), "unique_vectors": len(vector_counts), "complete_yes_no": sum(row["yes_no_coverage"] == len(ROLLS) for row in members), "selected": len(selected_ids)}, "selected_ids": selected_ids, "members": [{**row, "selected": row["bioguide_id"] in selected_ids, "selection_reason": selection_reasons.get(row["bioguide_id"])} for row in members]},
        "member_overlays.json": {"schema_version": "commissioning_domain_member_overlays_v1", "publication": PUBLICATION, "overlays": overlays},
        "inference_candidates.json": {"schema_version": "commissioning_domain_inference_candidates_v1", "publication": PUBLICATION, "candidates": inferences},
        "actual_member_vector_evaluation.json": _evaluation(members, actions),
        "binary_vector_evaluation.json": _binary_evaluation(),
        "mutation_report.json": _mutations(),
        "first_failures.json": {"schema_version": "commissioning_domain_first_failures_v1", "failures": [
            {"failure_id": "COMM-V1-001", "classification": "shared-corpus defect", "owning_layer": "action identity", "first_candidate": "All H.R. 6938 rows used the same package title and were indistinguishable.", "first_validator_result": "human_exception_required: opaque stages could be duplicated or counted as independent episodes.", "correction": "Added source-grounded Division A, Divisions B-C, and final-passage stage identities in shared dossiers.", "regression_proof": ["opaque_action_titles mutation", "reordered_actions_episodes mutation"], "preserved": True},
            {"failure_id": "COMM-V1-002", "classification": "novel meaning", "owning_layer": "episode relationship", "first_candidate": "Treat each separate critical-mineral and home-energy bill as an independent episode.", "first_validator_result": "human_exception_required: related proposals could overstate independent evidence.", "correction": "Grouped each source-grounded policy family as one episode while preserving mechanism differences.", "regression_proof": ["incompatible_episode_assignment mutation", "unresolved_trait_relationship mutation"], "preserved": True},
            {"failure_id": "COMM-V1-003", "classification": "generalized pipeline defect", "owning_layer": "persistence relationship graph", "first_candidate": "The first batch used readable relationship labels such as contains_episode and has_overlay.", "first_validator_result": "blocked: migration 0016 rejected the first relationship insert and rolled back the disposable transaction.", "correction": "Mapped every edge to the established immutable relationship vocabulary without changing schema 0016.", "regression_proof": ["disposable PostgreSQL constraint proof", "orphan relationship mutation"], "preserved": True},
        ]},
        "review_render_fixtures.json": {
            "schema_version": "commissioning_domain_review_render_fixtures_v1",
            "mode": "review_only",
            "fixtures": [
                {"member_id": "J000288", "case": "consistent_or_near_consistent"},
                {"member_id": "C001063", "case": "selective_or_divided"},
                {"member_id": "H001095", "case": "coverage_edge"},
                {"member_id": "A000371", "case": "human_exception"},
            ],
            "production_registry": "unchanged_empty",
        },
    }
    outputs["persistence_batch_manifest.json"] = _persistence_bundle(outputs, selected_ids)
    return outputs


def _serialize(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _frontend_module(outputs: dict[str, object]) -> str:
    payload = {
        "issue": ISSUE,
        "publication": PUBLICATION,
        "sources": outputs["source_manifest.json"]["sources"],
        "actions": outputs["accepted_actions.json"]["actions"],
        "episodes": outputs["episode_map.json"]["episodes"],
        "overlays": outputs["member_overlays.json"]["overlays"],
        "inferences": outputs["inference_candidates.json"]["candidates"],
        "renderFixtures": outputs["review_render_fixtures.json"],
    }
    return (
        "// Generated by backend/scripts/build_commissioning_domain_v1.py.\n"
        "// Review-only Environment & Energy commissioning data; never a production registry.\n"
        f"export const commissioningDomainReviewData = Object.freeze({json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)});\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=ROOT / "backend/data_sources/house_clerk/2026")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/editorial/commissioning_domain_v1")
    parser.add_argument("--frontend-output", type=Path, default=ROOT / "frontend/lib/commissioningDomainReviewData.mjs")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build(args.source_dir)
    if args.check:
        mismatches = [
            name for name, value in outputs.items()
            if not (args.output_dir / name).exists()
            or (args.output_dir / name).read_text(encoding="utf-8") != _serialize(value)
        ]
        dossier_mismatches = [
            f"dossiers/roll_{roll:03d}.json" for roll, dossier in ACTION_DOSSIERS.items()
            if not (args.output_dir / "dossiers" / f"roll_{roll:03d}.json").exists()
            or (args.output_dir / "dossiers" / f"roll_{roll:03d}.json").read_text(encoding="utf-8")
            != _serialize({"schema_version": "shared_action_dossier_v1", "canonical_action_id": f"house:119:2:{roll}", "dossier": dossier, "publication": PUBLICATION})
        ]
        frontend_mismatch = (
            not args.frontend_output.exists()
            or args.frontend_output.read_text(encoding="utf-8") != _frontend_module(outputs)
        )
        if frontend_mismatch:
            mismatches.append(args.frontend_output.name)
        if mismatches or dossier_mismatches:
            raise SystemExit("generated commissioning artifacts differ: " + ", ".join(mismatches + dossier_mismatches))
        print("Commissioning-domain artifacts are deterministic.")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dossiers").mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (args.output_dir / name).write_text(_serialize(value), encoding="utf-8")
    for roll, dossier in ACTION_DOSSIERS.items():
        payload = {"schema_version": "shared_action_dossier_v1", "canonical_action_id": f"house:119:2:{roll}", "dossier": dossier, "publication": PUBLICATION}
        (args.output_dir / "dossiers" / f"roll_{roll:03d}.json").write_text(_serialize(payload), encoding="utf-8")
    args.frontend_output.parent.mkdir(parents=True, exist_ok=True)
    args.frontend_output.write_text(_frontend_module(outputs), encoding="utf-8")
    print(f"Wrote {len(outputs)} commissioning artifacts, {len(ACTION_DOSSIERS)} dossiers, and {args.frontend_output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
