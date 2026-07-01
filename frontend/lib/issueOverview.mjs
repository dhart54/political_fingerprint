import { deriveEvidenceGroups } from "./evidenceGrouping.mjs";
import { formatDomainLabel } from "./issueDomains.js";
import { isProceduralContextRow } from "./proceduralContext.mjs";
import {
  formatSafePublicThemePhrase,
  getPublicThemeFallback,
  getPublicThemeForFacet,
} from "./publicCopyThemes.mjs";

const ISSUE_FACET_GROUPS = {
  budget_reconciliation_and_debt_limit: {
    id: "budget_reconciliation_and_debt_limit",
    label: "budget framework",
    overviewPhrase: "a budget framework for later tax, spending, deficit, and debt-limit legislation",
    practicalLever: "budget instructions for later tax, spending, deficit, and debt-limit legislation",
    plainAction: "setting up a later budget bill",
    concreteQuestion: "whether to advance a budget framework for later tax, spending, deficit, and debt-limit legislation",
  },
  small_business_loan_eligibility: {
    id: "small_business_loan_eligibility",
    label: "SBA loan eligibility restrictions",
    overviewPhrase: "restrictions on SBA loan eligibility tied to citizenship or lawful-residency status",
    practicalLever: "eligibility rules for SBA 7(a) and 504 small-business loans",
    plainAction: "deciding eligibility rules for SBA 7(a) and 504 loans",
    concreteQuestion: "whether to restrict SBA 7(a) and 504 loan eligibility based on citizenship or lawful-residency status",
  },
  military_construction_and_va_appropriations: {
    id: "military_construction_and_va_appropriations",
    label: "military construction and Veterans Affairs appropriations",
    overviewPhrase: "military construction and Veterans Affairs funding",
    practicalLever: "annual appropriations for military construction, military housing, veterans benefits, and VA programs",
    plainAction: "funding military construction, military housing, veterans benefits, and VA programs",
    concreteQuestion: "whether to fund military construction, military housing, veterans benefits, and Veterans Affairs programs",
  },
  temporary_government_funding: {
    id: "temporary_government_funding",
    label: "short-term government funding",
    overviewPhrase: "temporary government funding",
    practicalLever: "continuing appropriations to keep agencies operating temporarily",
    plainAction: "keeping agencies funded temporarily",
    concreteQuestion: "whether to keep federal agencies operating through temporary government funding",
  },
  government_funding_and_shutdown: {
    id: "government_funding_and_shutdown",
    label: "shutdown-ending funding package",
    overviewPhrase: "a shutdown-ending funding package",
    practicalLever: "funding terms for reopening or continuing federal operations",
    plainAction: "reopening or continuing federal operations",
    concreteQuestion: "whether to accept a shutdown-ending funding package",
  },
  small_business_regulation: {
    id: "small_business_regulation",
    label: "SBA regulatory-cost cap bill",
    overviewPhrase: "an SBA regulatory-cost cap bill",
    practicalLever: "a cap on net new SBA regulatory costs for small businesses",
    plainAction: "capping net new SBA regulatory costs for small businesses",
    concreteQuestion: "whether to cap net new SBA regulatory costs for small businesses",
  },
  appropriations_amendment: {
    id: "appropriations_amendment",
    label: "appropriations amendment",
    overviewPhrase: "an appropriations amendment",
    practicalLever: "amendment terms inside an appropriations measure",
  },
  conference_instruction: {
    id: "conference_instruction",
    label: "conference instruction",
    overviewPhrase: "a conference instruction",
    practicalLever: "instructions to House negotiators rather than final bill passage",
  },
  fentanyl_scheduling_and_penalties: {
    id: "fentanyl_scheduling_and_penalties",
    label: "fentanyl scheduling and penalty thresholds",
    overviewPhrase: "fentanyl scheduling and penalty-threshold legislation",
    practicalLever: "controlled-substance scheduling, penalty thresholds, and research-registration rules for fentanyl-related substances",
    plainAction: "setting rules for fentanyl-related substances",
    concreteQuestion: "whether to permanently schedule fentanyl-related substances and apply related penalty-threshold and research-registration changes",
  },
  federal_law_enforcement_equipment: {
    id: "federal_law_enforcement_equipment",
    label: "federal law-enforcement retired weapon purchases",
    overviewPhrase: "federal law-enforcement retired service-weapon purchasing",
    practicalLever: "a GSA process for federal law-enforcement officers to buy retired agency-issued firearms",
    plainAction: "letting federal law-enforcement officers buy retired service weapons",
    concreteQuestion: "whether to create a program for federal law-enforcement officers to buy retired agency-issued firearms",
  },
  law_enforcement_safety_reporting: {
    id: "law_enforcement_safety_reporting",
    label: "law-enforcement safety reporting",
    overviewPhrase: "law-enforcement safety and wellness reporting",
    practicalLever: "Department of Justice reporting on attacks against law-enforcement officers and officer mental-health resources",
    plainAction: "requiring DOJ reporting on law-enforcement officer safety and wellness",
    concreteQuestion: "whether to require DOJ reporting on targeted attacks against law-enforcement officers, reporting-system feasibility, and officer mental-health resources",
  },
  dc_police_pursuit_policy: {
    id: "dc_police_pursuit_policy",
    label: "D.C. police pursuit policy",
    overviewPhrase: "D.C. police vehicular-pursuit policy",
    practicalLever: "standards for when D.C. police may or must pursue suspects fleeing in vehicles",
    plainAction: "changing D.C. police pursuit rules",
    concreteQuestion: "whether to change D.C. police pursuit rules by removing current restrictions and adding a general pursuit requirement with exceptions",
  },
  dc_policing_reform_repeal: {
    id: "dc_policing_reform_repeal",
    label: "D.C. policing reform repeal",
    overviewPhrase: "repeal of D.C. policing and justice reforms",
    practicalLever: "repeal of D.C. policing reforms involving neck restraints, body-worn cameras, and police disciplinary records",
    plainAction: "repealing D.C. policing and justice reforms",
    concreteQuestion: "whether to repeal D.C.'s 2022 policing and justice reform act and restore provisions changed by that act",
  },
  "Defense authorization": {
    id: "Defense authorization",
    label: "defense authorization bill",
    overviewPhrase: "defense authorization legislation",
    practicalLever: "annual defense and national-security policy authorization",
    plainAction: "authorizing defense and national-security programs",
    concreteQuestion: "whether to pass defense and national-security authorization legislation",
  },
  "Defense authorization amendment": {
    id: "Defense authorization amendment",
    label: "defense authorization amendments",
    overviewPhrase: "defense authorization amendments",
    practicalLever: "amendments tied to defense authorization, not final passage of the full defense authorization bill",
    plainAction: "reviewing defense authorization amendments",
    concreteQuestion: "whether to adopt amendments to defense authorization legislation",
  },
  "House floor procedure": {
    id: "House floor procedure",
    label: "procedural House floor action",
    overviewPhrase: "procedural House floor action",
    practicalLever: "House floor procedure rather than final passage of a policy measure",
    plainAction: "setting or advancing House floor procedure",
  },
  "Motion to commit": {
    id: "Motion to commit",
    label: "motion to commit",
    overviewPhrase: "a motion to commit",
    practicalLever: "a procedural motion that can send a bill back for further consideration rather than enact the underlying policy",
    plainAction: "using a motion to commit before final disposition",
    concreteQuestion: "whether to use a procedural motion to send the measure back for further consideration",
  },
  "Veterans cemetery administration": {
    id: "Veterans cemetery administration",
    label: "veterans cemetery administration",
    overviewPhrase: "veterans cemetery administration",
    practicalLever: "administrative rules for veterans cemetery operations or eligibility",
    plainAction: "changing veterans cemetery administration",
    concreteQuestion: "whether to pass legislation affecting veterans cemetery administration",
  },
  foreign_military_sales: {
    id: "foreign_military_sales",
    label: "foreign military sales",
    overviewPhrase: "foreign military sales",
    practicalLever: "approval or disapproval of specific foreign military sales",
    plainAction: "reviewing foreign military sales",
    concreteQuestion: "whether to allow or disapprove specific foreign military sales",
  },
  floor_rule_for_multiple_bills: {
    id: "floor_rule_for_multiple_bills",
    label: "procedural floor rule for multiple bills",
    overviewPhrase: "a procedural floor rule for multiple bills",
    practicalLever: "House floor procedure for considering multiple bills, not final passage of the underlying policies",
    plainAction: "setting floor debate terms for multiple bills",
  },
  house_of_representatives: {
    id: "house_of_representatives",
    label: "procedural House rule or motion",
    overviewPhrase: "procedural House rule or motion",
    practicalLever: "House procedure rather than a clear final policy choice",
    plainAction: "setting or advancing House procedure",
  },
  floor_rule_for_energy_and_budget_measures: {
    id: "floor_rule_for_energy_and_budget_measures",
    label: "procedural floor rule for energy and budget measures",
    overviewPhrase: "a procedural floor rule for energy and budget measures",
    practicalLever: "House floor procedure for considering energy and budget measures, not final passage of the underlying policies",
    plainAction: "setting floor debate terms for energy and budget measures",
  },
  floor_procedure_on_hydrogen_vehicle_rule: {
    id: "floor_procedure_on_hydrogen_vehicle_rule",
    label: "procedural floor action on hydrogen vehicle rules",
    overviewPhrase: "procedural floor action on hydrogen vehicle rules",
    practicalLever: "House floor procedure related to hydrogen vehicle safety standards",
    plainAction: "setting floor procedure for hydrogen vehicle safety standards",
  },
  federal_employee_collective_bargaining: {
    id: "federal_employee_collective_bargaining",
    label: "federal employee collective bargaining",
    overviewPhrase: "federal employee collective-bargaining rules",
    practicalLever: "collective-bargaining rights and procedures for federal employees",
    plainAction: "changing federal employee collective-bargaining rules",
    concreteQuestion: "whether to change collective-bargaining rules for federal employees",
  },
  school_foreign_funding_and_contract_restrictions: {
    id: "school_foreign_funding_and_contract_restrictions",
    label: "school foreign-funding and contract restrictions",
    overviewPhrase: "school foreign-funding and contract restrictions",
    practicalLever: "restrictions tied to foreign funding, contracts, or influence in schools",
    plainAction: "placing foreign-funding and contract restrictions on schools",
    concreteQuestion: "whether to add foreign-funding or contract restrictions for schools",
  },
  school_foreign_influence_parent_notifications: {
    id: "school_foreign_influence_parent_notifications",
    label: "school foreign-influence parent notifications",
    overviewPhrase: "school foreign-influence parent notification rules",
    practicalLever: "parent notification requirements tied to foreign influence in schools",
    plainAction: "requiring parent notifications about school foreign-influence issues",
    concreteQuestion: "whether to require parent notifications about foreign-influence issues in schools",
  },
  natural_gas_pipeline_and_lng_review_coordination: {
    id: "natural_gas_pipeline_and_lng_review_coordination",
    label: "natural gas pipeline and LNG review coordination",
    overviewPhrase: "natural gas pipeline and LNG review coordination",
    practicalLever: "federal review coordination for natural gas pipeline and LNG projects",
    plainAction: "coordinating federal review of natural gas pipeline and LNG projects",
    concreteQuestion: "whether to coordinate federal reviews for natural gas pipeline and LNG projects",
  },
  health_insurance_premiums: {
    id: "health_insurance_premiums",
    label: "health insurance premium assistance",
    overviewPhrase: "health insurance premium assistance",
    practicalLever: "premium assistance or affordability rules for health insurance",
    plainAction: "changing health insurance premium assistance",
    concreteQuestion: "whether to change health insurance premium assistance or affordability rules",
  },
  medicaid_payment_rules_for_minor_health_procedures: {
    id: "medicaid_payment_rules_for_minor_health_procedures",
    label: "Medicaid payment rules for specified minor health procedures",
    overviewPhrase: "Medicaid payment rules for specified minor health procedures",
    practicalLever: "federal Medicaid payment restrictions for specified procedures involving minors",
    plainAction: "changing Medicaid payment rules for specified minor health procedures",
    concreteQuestion: "whether to restrict federal Medicaid payment for specified procedures involving minors",
  },
};

const MIN_COUNTED_ROWS_FOR_CONFIDENT_OVERVIEW = 3;
const LIMITED_ROW_DOMINANCE_SHARE = 0.5;
const MAX_MEASURE_GROUPS_IN_OVERVIEW = 5;
const DIRECTIONAL_DOMINANCE_SHARE = 2 / 3;

export function buildIssueOverview(rows, { domain = "", representativeName = "" } = {}) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return null;
  }

  const issueLabel = formatDomainLabel(domain || rows[0]?.primary_domain || "this issue");
  const issueDomain = String(domain || rows[0]?.primary_domain || "");
  const representativeLabel = formatRepresentativeReference(representativeName);
  const interpretedRows = rows.filter((row) => row.interpretation_status === "interpreted");
  const evidenceGrouping = deriveEvidenceGroups(rows);
  const directionalRows = interpretedRows.filter(isCountedDirectionalRow);
  const supportRows = directionalRows.filter((row) => row.position === row.support_position);
  const opposeRows = directionalRows.filter((row) => row.position === row.oppose_position);
  const notVotingRows = interpretedRows.filter((row) => row.position === "not_voting");
  const ambiguousRows = rows.filter((row) => row.interpretation_status && row.interpretation_status !== "interpreted");
  const proceduralContextRows = ambiguousRows.filter(isProceduralContextRow);
  const countedMeasureGroups = groupRowsByFacet(directionalRows, { allRows: rows, issueDomain });
  const notVotingMeasureGroups = groupRowsByFacet(notVotingRows, { allRows: rows, issueDomain });
  const ambiguousMeasureGroups = groupRowsByFacet(ambiguousRows, { allRows: rows, issueDomain });
  const proceduralContextMeasureGroups = groupRowsByFacet(proceduralContextRows, { allRows: rows, issueDomain });
  const partyRows = directionalRows.filter(hasPartyContext);
  const outcomeRows = directionalRows.filter(hasOutcomeContext);
  const partyMatchCount = partyRows.filter((row) => row.vote_context.member_voted_with_party_majority).length;
  const outcomeMatchCount = outcomeRows.filter((row) => row.vote_context.member_voted_with_winning_side).length;
  const passedOpposedCount = outcomeRows.filter(
    (row) =>
      row.vote_context?.final_result === "passed" &&
      row.vote_context?.member_voted_with_winning_side === false &&
      row.position === row.oppose_position,
  ).length;
  const partyLabel = directionalRows.find((row) => row.vote_context?.member_party)?.vote_context?.member_party || "";
  const votePattern = {
    interpretedYesNoCount: directionalRows.length,
    supportCount: supportRows.length,
    opposeCount: opposeRows.length,
    notVotingCount: notVotingRows.length,
    ambiguousCount: ambiguousRows.length,
    proceduralContextCount: proceduralContextRows.length,
    partyComparedCount: partyRows.length,
    partyMatchCount,
    finalOutcomeComparedCount: outcomeRows.length,
    finalOutcomeMatchCount: outcomeMatchCount,
    finalOutcomeAgainstCount: outcomeRows.length - outcomeMatchCount,
    finalOutcomePassedOpposedCount: passedOpposedCount,
    predominantPosition: summarizePredominantPosition({ opposeRows, supportRows }),
    partyPattern: summarizePartyPattern({ partyLabel, partyMatchCount, total: partyRows.length }),
    finalOutcomePattern: summarizeOutcomePattern({ matchCount: outcomeMatchCount, passedOpposedCount, total: outcomeRows.length }),
  };
  const readiness = assessOverviewReadiness({
    rows,
    directionalRows,
    ambiguousRows,
    countedMeasureGroups,
  });
  const overviewMeasureGroups = selectOverviewMeasureGroups(countedMeasureGroups, readiness);
  const additionalMeasureGroupCount = countedMeasureGroups.length - overviewMeasureGroups.length;
  const practicalPolicyLevers = uniqueStrings(
    [...countedMeasureGroups, ...notVotingMeasureGroups]
      .map((group) => group.practicalLever)
      .filter(Boolean),
  );
  const supportMeasureGroups = selectOverviewMeasureGroups(groupRowsByFacet(supportRows, { allRows: rows, issueDomain }), readiness);
  const opposeMeasureGroups = selectOverviewMeasureGroups(groupRowsByFacet(opposeRows, { allRows: rows, issueDomain }), readiness);
  const copy = buildOverviewCopy({
    additionalMeasureGroupCount,
    ambiguousMeasureGroups,
    ambiguousRows,
    countedMeasureGroups: overviewMeasureGroups,
    issueLabel,
    notVotingMeasureGroups,
    notVotingRows,
    opposeMeasureGroups,
    proceduralContextMeasureGroups,
    proceduralContextRows,
    practicalPolicyLevers,
    issueDomain,
    readiness,
    representativeLabel,
    supportMeasureGroups,
    votePattern,
  });

  return {
    issueLabel,
    representativeLabel,
    evidenceGrouping,
    measureGroups: countedMeasureGroups,
    overviewMeasureGroups,
    notVotingMeasureGroups,
    ambiguousMeasureGroups,
    proceduralContextMeasureGroups,
    practicalPolicyLevers,
    readiness,
    votePattern,
    takeaways: {
      reasonable: copy.howVoterMightRead,
      notInferred: copy.whatNotToInfer,
    },
    copy,
  };
}

export function formatRenderedIssueOverview(overview) {
  if (!overview?.copy) {
    return "";
  }

  return [
    "Finding",
    `${overview.copy.whatRepresentativeDid} ${overview.copy.whatPatternThatCreates}`,
    "",
    "What these votes were about",
    overview.copy.whatTheseVotesWereAbout,
    "",
    "How a voter might read that",
    overview.copy.howVoterMightRead,
    "",
    "How to read this",
    overview.copy.whatNotToInfer,
  ].join("\n");
}

function buildOverviewCopy({
  additionalMeasureGroupCount,
  ambiguousMeasureGroups,
  ambiguousRows,
  countedMeasureGroups,
  issueLabel,
  notVotingMeasureGroups,
  notVotingRows,
  opposeMeasureGroups,
  proceduralContextMeasureGroups,
  proceduralContextRows,
  practicalPolicyLevers,
  issueDomain,
  readiness,
  representativeLabel,
  supportMeasureGroups,
  votePattern,
}) {
  if (readiness.status !== "safe") {
    return buildLimitedEvidenceOverviewCopy({
      ambiguousMeasureGroups,
      ambiguousRows,
      countedMeasureGroups,
      issueDomain,
      issueLabel,
      notVotingMeasureGroups,
      notVotingRows,
      proceduralContextMeasureGroups,
      proceduralContextRows,
      readiness,
      representativeLabel,
      votePattern,
    });
  }

  const notVotingGroupText = formatMeasureCategoryList(notVotingMeasureGroups, issueDomain, { allowFallback: false });
  const measureCategoryText = formatMeasureCategoryList(countedMeasureGroups, issueDomain);
  const policySubstanceText = formatPolicySubstanceDescription({ issueDomain, issueLabel });
  const directionalPattern = summarizeDirectionalPattern(votePattern);
  const aboutParts = [];

  if (measureCategoryText) {
    aboutParts.push(`The reviewed Yes/No votes in this section covered ${measureCategoryText}.`);
  } else {
    aboutParts.push(`The reviewed Yes/No votes in this section covered ${getPublicThemeFallback(issueDomain)}.`);
  }
  if (notVotingRows.length && notVotingGroupText) {
    aboutParts.push(
      `A separate not-voting row concerned ${notVotingGroupText}, but ${representativeLabel} was recorded as not voting, so it is explained below and not counted as support or opposition.`,
    );
  }
  if (additionalMeasureGroupCount > 0) {
    aboutParts.push(
      `${capitalize(formatNumber(additionalMeasureGroupCount))} additional ${additionalMeasureGroupCount === 1 ? "measure group is" : "measure groups are"} shown in the evidence below.`,
    );
  }
  if (ambiguousRows.length) {
    aboutParts.push(formatLimitedContextOverviewSentence({ ambiguousMeasureGroups, ambiguousRows, issueDomain, proceduralContextMeasureGroups, proceduralContextRows }));
  }

  const actionParts = [];
  if (directionalPattern.direction === "opposed" || directionalPattern.direction === "supported") {
    actionParts.push(
      `In this reviewed sample, ${representativeLabel} mostly ${directionalPattern.direction} these reviewed ${issueLabel} measures: ${votePattern.opposeCount} opposed and ${votePattern.supportCount} supported across ${votePattern.interpretedYesNoCount} interpreted Yes/No ${votePattern.interpretedYesNoCount === 1 ? "vote" : "votes"}.`,
    );
  } else if (votePattern.supportCount || votePattern.opposeCount) {
    actionParts.push(
      `In this reviewed sample, ${representativeLabel}'s interpreted Yes/No votes were split across these reviewed ${issueLabel} measures: ${votePattern.opposeCount} opposed and ${votePattern.supportCount} supported across ${votePattern.interpretedYesNoCount} interpreted Yes/No votes.`,
    );
  }

  const patternParts = [];
  const themePattern = buildThemePatternSentence({
    directionalPattern,
    issueDomain,
    measureCategoryText,
    opposeMeasureGroups,
    supportMeasureGroups,
  });
  if (themePattern) {
    patternParts.push(themePattern);
  }
  if (votePattern.partyPattern) {
    patternParts.push(votePattern.partyPattern);
  }
  if (votePattern.finalOutcomePattern) {
    patternParts.push(votePattern.finalOutcomePattern);
  }
  patternParts.push("Start with the representative votes below to inspect the record behind this read.");

  const howVoterMightRead = buildPolicyFirstVoterRead({
    measureCategoryText,
    policySubstanceText,
    representativeLabel,
    directionalPattern,
  });
  const notInferParts = [
    "This read is based on the reviewed votes shown here. Vote records show actions, not motive, ideology, character, corruption, or a voting recommendation.",
    formatFullRecordBoundary(issueDomain),
  ];
  if (notVotingRows.length || ambiguousRows.length) {
    notInferParts.push(
      proceduralContextRows.length
        ? "Not-voting, limited-context, and procedural-context rows remain visible below, but they are not forced into the pattern."
        : "Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.",
    );
  }

  return {
    whatTheseVotesWereAbout: aboutParts.join(" "),
    whatRepresentativeDid: actionParts.join(" "),
    whatPatternThatCreates: patternParts.join(" "),
    howVoterMightRead,
    whatNotToInfer: notInferParts.join(" "),
  };
}

function assessOverviewReadiness({ rows, directionalRows, ambiguousRows, countedMeasureGroups }) {
  const totalRows = rows.length;
  const countedYesNoCount = directionalRows.length;
  const limitedCount = ambiguousRows.length;
  const limitedShare = totalRows ? limitedCount / totalRows : 0;
  const reasons = [];

  if (countedYesNoCount < MIN_COUNTED_ROWS_FOR_CONFIDENT_OVERVIEW) {
    reasons.push("too_few_counted_interpreted_yes_no_rows");
  }
  if (limitedCount > countedYesNoCount || limitedShare >= LIMITED_ROW_DOMINANCE_SHARE) {
    reasons.push("limited_or_ambiguous_rows_dominate");
  }

  return {
    status: reasons.length ? "limited" : "safe",
    reasons,
    countedYesNoCount,
    limitedCount,
    totalRows,
    limitedShare,
    measureGroupCount: countedMeasureGroups.length,
    maxMeasureGroupsShown: MAX_MEASURE_GROUPS_IN_OVERVIEW,
  };
}

function selectOverviewMeasureGroups(groups, readiness) {
  if (groups.length <= readiness.maxMeasureGroupsShown) {
    return groups;
  }

  return [...groups]
    .sort((left, right) => right.rowCount - left.rowCount || groups.indexOf(left) - groups.indexOf(right))
    .slice(0, readiness.maxMeasureGroupsShown);
}

function summarizeDirectionalPattern(votePattern) {
  const total = votePattern.interpretedYesNoCount || 0;
  if (!total) {
    return { direction: "insufficient", share: 0 };
  }

  const opposeShare = votePattern.opposeCount / total;
  const supportShare = votePattern.supportCount / total;
  if (opposeShare >= DIRECTIONAL_DOMINANCE_SHARE) {
    return { direction: "opposed", share: opposeShare };
  }
  if (supportShare >= DIRECTIONAL_DOMINANCE_SHARE) {
    return { direction: "supported", share: supportShare };
  }
  return { direction: "split", share: Math.max(opposeShare, supportShare) };
}

function buildThemePatternSentence({
  directionalPattern,
  issueDomain,
  measureCategoryText,
  opposeMeasureGroups,
  supportMeasureGroups,
}) {
  const opposedThemeText = formatMeasureCategoryList(opposeMeasureGroups, issueDomain, { allowFallback: false });
  const supportedThemeText = formatMeasureCategoryList(supportMeasureGroups, issueDomain, { allowFallback: false });
  const canSeparateThemes =
    (directionalPattern.direction === "opposed" || directionalPattern.direction === "supported") &&
    opposedThemeText &&
    supportedThemeText &&
    opposedThemeText !== supportedThemeText;

  if (canSeparateThemes) {
    return `The opposed measures centered on ${opposedThemeText}. The supported votes centered on ${supportedThemeText}.`;
  }

  if (measureCategoryText) {
    return `The reviewed measures included ${measureCategoryText}.`;
  }

  return "";
}

function formatPolicySubstanceDescription({ issueDomain, issueLabel }) {
  const issueMeasures = formatIssueAreaMeasures(issueDomain);
  if (issueMeasures !== "measures") {
    return issueMeasures;
  }

  const label = String(issueLabel || "policy").replace(/\s*&\s*/g, " and ").toLowerCase();
  return `${label} measures`;
}

function formatMeasureCategoryList(groups, issueDomain, { allowFallback = true } = {}) {
  const labels = uniqueStrings(
    groups
      .map((group) => formatMeasureThemePhrase(group))
      .map((value) => cleanSentence(value))
      .filter(Boolean),
  );

  if (labels.length) {
    return formatList(labels.slice(0, MAX_MEASURE_GROUPS_IN_OVERVIEW));
  }

  if (!allowFallback) {
    return "";
  }

  const fallback = formatIssueAreaMeasures(issueDomain);
  return fallback === "measures" ? "" : fallback;
}

function formatMeasureThemePhrase(group) {
  const phrase = formatSafePublicThemePhrase(group?.publicTheme || group?.overviewPhrase || group?.label, { curated: true });
  return phrase;
}

function buildPolicyFirstVoterRead({ measureCategoryText, policySubstanceText, representativeLabel, directionalPattern }) {
  const favoredMeasures = measureCategoryText
    ? `the reviewed measures on ${measureCategoryText},`
    : `the reviewed ${policySubstanceText} in this sample,`;
  const specificMeasures = measureCategoryText
    ? `the reviewed measures on ${measureCategoryText}`
    : `the reviewed ${policySubstanceText} in this sample`;

  if (directionalPattern.direction === "opposed") {
    return `If you favored ${favoredMeasures} ${representativeLabel}'s votes were mostly opposed. If you opposed those measures or objected to their terms, this record was mostly aligned with that view.`;
  }
  if (directionalPattern.direction === "supported") {
    return `If you favored ${favoredMeasures} ${representativeLabel}'s votes were mostly aligned with that view. If you opposed those measures or objected to their terms, this record was mostly opposed.`;
  }

  return `If your view depends on the specific terms of ${specificMeasures}, inspect the representative votes below; this record is split rather than mostly support or mostly opposition.`;
}

function buildLimitedEvidenceOverviewCopy({
  ambiguousMeasureGroups,
  ambiguousRows,
  countedMeasureGroups,
  issueDomain,
  issueLabel,
  notVotingMeasureGroups,
  notVotingRows,
  proceduralContextMeasureGroups,
  proceduralContextRows,
  readiness,
  representativeLabel,
  votePattern,
}) {
  const countedThemeText = formatMeasureCategoryList(countedMeasureGroups, issueDomain);
  const notVotingGroupText = formatMeasureCategoryList(notVotingMeasureGroups, issueDomain, { allowFallback: false });
  const aboutParts = [];

  if (votePattern.interpretedYesNoCount) {
    aboutParts.push(
      `This ${issueLabel} sample has limited interpreted evidence. The rows that can be summarized concern ${countedThemeText || getPublicThemeFallback(issueDomain)}.`,
    );
  } else {
    aboutParts.push(`This ${issueLabel} sample has limited interpreted evidence and does not yet support a clear issue overview.`);
  }
  if (readiness.reasons.includes("too_few_counted_interpreted_yes_no_rows")) {
    aboutParts.push(
      `Only ${readiness.countedYesNoCount} reviewed Yes/No ${readiness.countedYesNoCount === 1 ? "vote could" : "votes could"} be interpreted, so the section should not be read as a stable pattern.`,
    );
  }
  if (notVotingRows.length && notVotingGroupText) {
    aboutParts.push(
      `A not-voting row concerned ${notVotingGroupText}, but ${representativeLabel} was recorded as not voting, so it is explained below and not counted as support or opposition.`,
    );
  }
  if (ambiguousRows.length) {
    aboutParts.push(formatLimitedContextOverviewSentence({ ambiguousMeasureGroups, ambiguousRows, issueDomain, proceduralContextMeasureGroups, proceduralContextRows }));
  }

  const actionParts = [];
  if (votePattern.supportCount || votePattern.opposeCount) {
    actionParts.push(
      `Of the ${votePattern.interpretedYesNoCount} reviewed Yes/No ${votePattern.interpretedYesNoCount === 1 ? "vote" : "votes"} that could be interpreted, ${votePattern.supportCount} supported the measures shown and ${votePattern.opposeCount} opposed them.`,
    );
  } else {
    actionParts.push(`${representativeLabel} does not have enough interpreted Yes/No votes in this sample to summarize support or opposition.`);
  }
  if (votePattern.partyPattern) {
    actionParts.push(votePattern.partyPattern);
  }
  if (votePattern.finalOutcomePattern) {
    actionParts.push(votePattern.finalOutcomePattern);
  }

  const limitedReason = readiness.reasons.includes("limited_or_ambiguous_rows_dominate")
    ? "limited-context rows make up much of this sample"
    : "the interpreted evidence is still thin";

  return {
    whatTheseVotesWereAbout: aboutParts.join(" "),
    whatRepresentativeDid: actionParts.join(" "),
    whatPatternThatCreates: `This section is best read as limited evidence, not a stable issue pattern, because ${limitedReason}.`,
    howVoterMightRead:
      "A voter can use these rows as source-backed examples of what was reviewed, then open the individual evidence cards before drawing a broader issue-area conclusion.",
    whatNotToInfer: [
      "This read is limited to reviewed votes in this sample and does not assign motive, ideology, character, corruption, or a voting recommendation.",
      formatFullRecordBoundary(issueDomain),
      proceduralContextRows.length
        ? "Not-voting, limited-context, and procedural-context rows remain visible below, but they are not forced into the pattern."
        : "Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.",
    ].join(" "),
  };
}

function groupRowsByFacet(rows, { allRows = rows, issueDomain = "" } = {}) {
  const groups = new Map();
  const allRowsByFacet = new Map();

  allRows.forEach((row) => {
    const facet = String(row.issue_facet || "").trim();
    if (!facet) {
      return;
    }
    const current = allRowsByFacet.get(facet) || [];
    current.push(row);
    allRowsByFacet.set(facet, current);
  });

  rows.forEach((row) => {
    const facet = String(row.issue_facet || "").trim();
    const publicTheme = getPublicThemeForFacet(facet, { domain: issueDomain });
    const group = ISSUE_FACET_GROUPS[facet] || {
      id: facet || "unlabeled_measure",
      label: publicTheme,
      overviewPhrase: publicTheme,
      practicalLever: publicTheme,
      plainAction: publicTheme,
      concreteQuestion: "",
    };
    const current = groups.get(group.id) || {
      ...group,
      publicTheme: getPublicThemeForFacet(group.id, {
        domain: issueDomain,
        curatedTheme: group.publicTheme || group.overviewPhrase || group.label,
      }),
      rows: [],
      statusRows: allRowsByFacet.get(facet) || [],
      positions: {},
    };
    current.rows.push(row);
    current.positions[row.position || "unknown"] = (current.positions[row.position || "unknown"] || 0) + 1;
    groups.set(group.id, current);
  });

  return Array.from(groups.values()).map(formatMeasureGroup);
}

function formatMeasureGroup(group) {
  const copy = buildDynamicMeasureGroupCopy(group);
  const publicTheme = getPublicThemeForFacet(copy.id, {
    curatedTheme: copy.publicTheme || copy.overviewPhrase || copy.label,
  });

  return {
    id: group.id,
    label: copy.label,
    overviewPhrase: copy.overviewPhrase,
    publicTheme,
    practicalLever: copy.practicalLever,
    plainAction: copy.plainAction,
    concreteQuestion: copy.concreteQuestion,
    rowCount: group.rows.length,
    positions: group.positions,
    rollCalls: group.rows.map((row) => ({
      roll_call_id: row.roll_call_id,
      rollcall_number: row.rollcall_number,
      position: row.position,
      interpretation_status: row.interpretation_status,
      description: row.description || row.question || "",
    })),
  };
}

function buildDynamicMeasureGroupCopy(group) {
  if (group.id !== "Defense authorization amendment") {
    return group;
  }

  const statusRows = group.statusRows?.length ? group.statusRows : group.rows;
  const interpretedCount = statusRows.filter((row) => row.interpretation_status === "interpreted").length;
  const limitedCount = statusRows.filter(
    (row) => row.interpretation_status === "ambiguous" || row.interpretation_status === "insufficient_evidence" || !row.interpretation_status,
  ).length;
  const totalCount = statusRows.length || 1;
  const interpretedShare = interpretedCount / totalCount;
  const limitedShare = limitedCount / totalCount;
  const baseCopy = {
    ...group,
    practicalLever: "amendments tied to defense authorization, not final passage of the full defense authorization bill",
    plainAction: "reviewing defense authorization amendments",
  };

  if (interpretedShare >= 0.67) {
    return {
      ...baseCopy,
      label: "defense authorization amendments",
      overviewPhrase: "defense authorization amendments",
      concreteQuestion: "whether to adopt amendments to defense authorization legislation",
    };
  }

  if (limitedShare >= 0.67) {
    return {
      ...baseCopy,
      label: "limited-context defense authorization amendments",
      overviewPhrase: "limited-context defense authorization amendments",
      concreteQuestion: "",
    };
  }

  return {
    ...baseCopy,
    label: "mixed-context defense authorization amendments",
    overviewPhrase: "mixed-context defense authorization amendments",
    concreteQuestion: "whether to adopt some defense authorization amendments, while other amendment rows remain limited-context",
  };
}

function isCountedDirectionalRow(row) {
  return (
    row.interpretation_status === "interpreted" &&
    (row.position === "yea" || row.position === "nay") &&
    (row.position === row.support_position || row.position === row.oppose_position)
  );
}

function hasPartyContext(row) {
  return row.vote_context?.member_voted_with_party_majority !== null && row.vote_context?.member_voted_with_party_majority !== undefined;
}

function hasOutcomeContext(row) {
  return row.vote_context?.member_voted_with_winning_side !== null && row.vote_context?.member_voted_with_winning_side !== undefined;
}

function summarizePredominantPosition({ opposeRows, supportRows }) {
  const total = opposeRows.length + supportRows.length;
  if (!total) {
    return "insufficient interpreted vote pattern";
  }
  if (opposeRows.length / total >= DIRECTIONAL_DOMINANCE_SHARE) {
    return "mostly opposed interpreted measures";
  }
  if (supportRows.length / total >= DIRECTIONAL_DOMINANCE_SHARE) {
    return "mostly supported interpreted measures";
  }
  return "split interpreted vote pattern";
}

function summarizePartyPattern({ partyLabel, partyMatchCount, total }) {
  if (!total) {
    return "";
  }

  const partyName = partyLabel ? `most ${formatPartyName(partyLabel)}s` : "most members of their party";
  return `${capitalize(formatSharePhrase(partyMatchCount, total))} of those votes matched ${partyName}.`;
}

function formatLimitedContextOverviewSentence({ ambiguousMeasureGroups, ambiguousRows, issueDomain, proceduralContextMeasureGroups = [], proceduralContextRows = [] }) {
  if (proceduralContextRows.length === ambiguousRows.length && proceduralContextRows.length) {
    const proceduralText = formatMeasureCategoryList(proceduralContextMeasureGroups, issueDomain, { allowFallback: false });
    return proceduralText
      ? `${capitalize(formatNumber(proceduralContextRows.length))} procedural-context ${proceduralContextRows.length === 1 ? "row remains" : "rows remain"} visible for ${proceduralText}, but ${proceduralContextRows.length === 1 ? "it explains" : "they explain"} floor process and ${proceduralContextRows.length === 1 ? "is" : "are"} not used to summarize support, opposition, or alignment.`
      : `${capitalize(formatNumber(proceduralContextRows.length))} procedural-context ${proceduralContextRows.length === 1 ? "row remains" : "rows remain"} visible, but ${proceduralContextRows.length === 1 ? "it explains" : "they explain"} floor process and ${proceduralContextRows.length === 1 ? "is" : "are"} not used to summarize support, opposition, or alignment.`;
  }
  if (proceduralContextRows.length) {
    const otherLimitedCount = ambiguousRows.length - proceduralContextRows.length;
    return `${capitalize(formatNumber(ambiguousRows.length))} additional rows remain visible below, including ${formatNumber(proceduralContextRows.length)} procedural-context ${proceduralContextRows.length === 1 ? "row" : "rows"} and ${formatNumber(otherLimitedCount)} other limited-context ${otherLimitedCount === 1 ? "row" : "rows"}; they are not used to summarize support, opposition, or alignment.`;
  }
  if (issueDomain !== "ECONOMY_TAXES") {
    return `${capitalize(formatNumber(ambiguousRows.length))} additional ${ambiguousRows.length === 1 ? "row remains" : "rows remain"} visible below but ${ambiguousRows.length === 1 ? "is" : "are"} not counted because the available source text does not clearly explain the practical policy effect.`;
  }

  const ambiguousText = formatMeasureCategoryList(ambiguousMeasureGroups, issueDomain, { allowFallback: false });
  return ambiguousText
    ? `${capitalize(formatNumber(ambiguousRows.length))} ambiguous or limited-context ${ambiguousRows.length === 1 ? "row remains" : "rows remain"} visible for ${ambiguousText}, but ${ambiguousRows.length === 1 ? "it is" : "they are"} not used to summarize the vote pattern.`
    : `${capitalize(formatNumber(ambiguousRows.length))} ambiguous or limited-context ${ambiguousRows.length === 1 ? "row remains" : "rows remain"} visible, but ${ambiguousRows.length === 1 ? "it is" : "they are"} not used to summarize the vote pattern.`;
}

function summarizeOutcomePattern({ matchCount, passedOpposedCount, total }) {
  if (!total) {
    return "";
  }

  const againstCount = total - matchCount;
  if (againstCount > matchCount) {
    if (passedOpposedCount === againstCount) {
      return `${capitalize(formatSharePhrase(againstCount, total))} opposed measures that passed the House.`;
    }
    return `${capitalize(formatSharePhrase(againstCount, total))} were against the final House outcome.`;
  }
  if (matchCount > againstCount) {
    return `${capitalize(formatSharePhrase(matchCount, total))} were with the final House outcome.`;
  }
  return "Those votes split evenly between the final House outcome and the side that did not prevail.";
}

function formatIssueAreaMeasures(domain) {
  if (domain === "ECONOMY_TAXES") {
    return "fiscal, funding, and small-business measures";
  }
  if (domain === "JUSTICE_PUBLIC_SAFETY") {
    return "public-safety and legal-policy measures";
  }
  return "measures";
}

function formatFullRecordBoundary(domain) {
  if (domain === "ECONOMY_TAXES") {
    return "The rows show recorded votes and reviewed bill meaning for this sample, not her full fiscal record.";
  }
  return "The rows show recorded votes and reviewed bill meaning for this sample, not her full record in this issue area.";
}

function formatRepresentativeReference(name) {
  const cleaned = String(name || "").trim();
  if (!cleaned) {
    return "this representative";
  }

  const parts = cleaned.split(/\s+/).filter(Boolean);
  return parts.length > 1 ? parts[parts.length - 1] : cleaned;
}

function formatPartyName(party) {
  const labels = {
    D: "Democrat",
    R: "Republican",
    I: "Independent",
  };

  return labels[party] || String(party || "party member");
}

function formatSharePhrase(count, total) {
  if (count === total) {
    return "all";
  }
  if (count === 0) {
    return "none";
  }
  if (count > total / 2) {
    return "most";
  }
  if (count === total / 2) {
    return "half";
  }
  return `${count} of ${total}`;
}

function formatCount(count, noun) {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

function formatNumber(value) {
  const labels = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
  };

  return labels[value] || String(value);
}

function formatList(values, { semicolon = false } = {}) {
  const cleanValues = values.filter(Boolean);
  if (cleanValues.length === 0) {
    return "";
  }
  if (cleanValues.length === 1) {
    return cleanValues[0];
  }
  if (cleanValues.length === 2) {
    return `${cleanValues[0]} and ${cleanValues[1]}`;
  }
  const separator = semicolon ? "; " : ", ";
  const finalSeparator = semicolon ? "; and " : ", and ";
  return `${cleanValues.slice(0, -1).join(separator)}${finalSeparator}${cleanValues[cleanValues.length - 1]}`;
}

function uniqueStrings(values) {
  return Array.from(new Set(values.map((value) => cleanSentence(value)).filter(Boolean)));
}

function cleanSentence(value) {
  return String(value || "")
    .replace(/\.$/, "")
    .trim();
}

function capitalize(value) {
  const text = String(value || "");
  return text ? text[0].toUpperCase() + text.slice(1) : "";
}
