import { formatDomainLabel } from "./issueDomains.js";

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
};

export function buildIssueOverview(rows, { domain = "", representativeName = "" } = {}) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return null;
  }

  const issueLabel = formatDomainLabel(domain || rows[0]?.primary_domain || "this issue");
  const issueDomain = String(domain || rows[0]?.primary_domain || "");
  const representativeLabel = formatRepresentativeReference(representativeName);
  const interpretedRows = rows.filter((row) => row.interpretation_status === "interpreted");
  const directionalRows = interpretedRows.filter(isCountedDirectionalRow);
  const supportRows = directionalRows.filter((row) => row.position === row.support_position);
  const opposeRows = directionalRows.filter((row) => row.position === row.oppose_position);
  const notVotingRows = interpretedRows.filter((row) => row.position === "not_voting");
  const ambiguousRows = rows.filter((row) => row.interpretation_status && row.interpretation_status !== "interpreted");
  const countedMeasureGroups = groupRowsByFacet(directionalRows);
  const notVotingMeasureGroups = groupRowsByFacet(notVotingRows);
  const ambiguousMeasureGroups = groupRowsByFacet(ambiguousRows);
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
  const practicalPolicyLevers = uniqueStrings(
    [...countedMeasureGroups, ...notVotingMeasureGroups]
      .map((group) => group.practicalLever)
      .filter(Boolean),
  );
  const concreteQuestions = uniqueStrings(countedMeasureGroups.map((group) => group.concreteQuestion).filter(Boolean));
  const copy = buildOverviewCopy({
    ambiguousMeasureGroups,
    ambiguousRows,
    countedMeasureGroups,
    issueLabel,
    notVotingMeasureGroups,
    notVotingRows,
    practicalPolicyLevers,
    concreteQuestions,
    issueDomain,
    representativeLabel,
    votePattern,
  });

  return {
    issueLabel,
    representativeLabel,
    measureGroups: countedMeasureGroups,
    notVotingMeasureGroups,
    ambiguousMeasureGroups,
    practicalPolicyLevers,
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
    "What these votes were about",
    overview.copy.whatTheseVotesWereAbout,
    "",
    "What Foushee did",
    overview.copy.whatRepresentativeDid,
    "",
    "What pattern that creates",
    overview.copy.whatPatternThatCreates,
    "",
    "How a voter might read that",
    overview.copy.howVoterMightRead,
    "",
    "What not to infer",
    overview.copy.whatNotToInfer,
  ].join("\n");
}

function buildOverviewCopy({
  ambiguousMeasureGroups,
  ambiguousRows,
  countedMeasureGroups,
  issueLabel,
  notVotingMeasureGroups,
  notVotingRows,
  practicalPolicyLevers,
  concreteQuestions,
  issueDomain,
  representativeLabel,
  votePattern,
}) {
  const notVotingGroupText = formatList(notVotingMeasureGroups.map((group) => group.overviewPhrase));
  const concreteQuestionText = formatList(concreteQuestions, { semicolon: true });
  const aboutParts = [];

  if (concreteQuestionText) {
    aboutParts.push(
      `In this ${issueLabel} sample, the reviewed votes where ${representativeLabel} cast a Yes or No covered several ${formatQuestionCategory(issueDomain)}: ${concreteQuestionText}.`,
    );
  } else {
    aboutParts.push(`In this ${issueLabel} sample, the reviewed rows did not create a clear Yes or No issue pattern.`);
  }
  if (notVotingRows.length && notVotingGroupText) {
    aboutParts.push(
      `A separate not-voting row concerned ${notVotingGroupText}, but ${representativeLabel} was recorded as not voting, so it is explained below and not counted as support or opposition.`,
    );
  }
  if (ambiguousRows.length) {
    aboutParts.push(formatLimitedContextOverviewSentence({ ambiguousMeasureGroups, ambiguousRows, issueDomain }));
  }

  const actionParts = [];
  if (votePattern.opposeCount && !votePattern.supportCount) {
    actionParts.push(`${representativeLabel} voted No on all ${votePattern.opposeCount} reviewed votes where she cast a Yes or No.`);
  } else if (votePattern.supportCount && !votePattern.opposeCount) {
    actionParts.push(`${representativeLabel} voted Yes on all ${votePattern.supportCount} reviewed votes where she cast a Yes or No.`);
  } else if (votePattern.supportCount || votePattern.opposeCount) {
    actionParts.push(
      `Of the ${votePattern.interpretedYesNoCount} reviewed Yes/No votes that could be interpreted, ${votePattern.supportCount} supported the measures shown and ${votePattern.opposeCount} opposed them.`,
    );
  }
  if (votePattern.partyComparedCount === votePattern.opposeCount && votePattern.partyMatchCount === votePattern.opposeCount && votePattern.finalOutcomeAgainstCount === votePattern.opposeCount) {
    actionParts.push("Each of those votes matched most House Democrats, and each was against the final House outcome.");
  } else {
    if (votePattern.partyPattern) {
      actionParts.push(votePattern.partyPattern);
    }
    if (votePattern.finalOutcomePattern) {
      actionParts.push(votePattern.finalOutcomePattern);
    }
  }

  const patternParts = [];
  if (votePattern.opposeCount && !votePattern.supportCount) {
    patternParts.push(
      `${representativeLabel} consistently opposed the House Republican ${formatIssueAreaMeasures(issueDomain)} reviewed in this sample.`,
    );
  } else if (votePattern.supportCount && !votePattern.opposeCount) {
    patternParts.push(`${representativeLabel} consistently supported the measures reviewed in this sample.`);
  } else if (votePattern.supportCount || votePattern.opposeCount) {
    patternParts.push(`${representativeLabel}'s reviewed votes where she cast a Yes or No in this sample were mixed.`);
  }
  if (concreteQuestionText) {
    patternParts.push(
      `Her record here is best read as ${formatPatternBoundary(votePattern)} this specific set of Republican-led House measures, ${formatSimpleStatementBoundary(issueDomain)}`,
    );
  }

  const howVoterMightRead =
    issueDomain === "ECONOMY_TAXES"
      ? "If you generally favored these House Republican packages, this section may look misaligned with your views. If you generally wanted Democrats to oppose those packages or objected to their terms, this section may look aligned. The vote record alone does not show her motive."
      : "If you generally favored these House Republican measures, this section may look misaligned with your views. If you generally wanted Democrats to oppose those measures or objected to their terms, this section may look aligned. The vote record alone does not show her motive.";
  const notInferParts = [
    "Do not infer motive, ideology, character, corruption, or a voting recommendation from this section.",
    formatFullRecordBoundary(issueDomain),
  ];
  if (notVotingRows.length || ambiguousRows.length) {
    notInferParts.push("Not-voting and limited-context rows remain visible below, but they are not forced into the pattern.");
  }

  return {
    whatTheseVotesWereAbout: aboutParts.join(" "),
    whatRepresentativeDid: actionParts.join(" "),
    whatPatternThatCreates: patternParts.join(" "),
    howVoterMightRead,
    whatNotToInfer: notInferParts.join(" "),
  };
}

function groupRowsByFacet(rows) {
  const groups = new Map();

  rows.forEach((row) => {
    const facet = String(row.issue_facet || "").trim();
    const group = ISSUE_FACET_GROUPS[facet] || {
      id: facet || "unlabeled_measure",
      label: facet ? formatIssueFacet(facet).toLowerCase() : "unlabeled measure",
      overviewPhrase: buildFallbackMeasurePhrase(row, facet),
      practicalLever: cleanSentence(row.policy_effect || row.why_it_mattered || row.what_happened),
      plainAction: cleanSentence(row.why_it_mattered || row.what_happened || row.policy_effect),
      concreteQuestion: cleanSentence(row.why_it_mattered || row.what_happened || row.policy_effect),
    };
    const current = groups.get(group.id) || {
      ...group,
      rows: [],
      positions: {},
    };
    current.rows.push(row);
    current.positions[row.position || "unknown"] = (current.positions[row.position || "unknown"] || 0) + 1;
    groups.set(group.id, current);
  });

  return Array.from(groups.values()).map((group) => ({
    id: group.id,
    label: group.label,
    overviewPhrase: group.overviewPhrase,
    practicalLever: group.practicalLever,
    plainAction: group.plainAction,
    concreteQuestion: group.concreteQuestion,
    rowCount: group.rows.length,
    positions: group.positions,
    rollCalls: group.rows.map((row) => ({
      roll_call_id: row.roll_call_id,
      rollcall_number: row.rollcall_number,
      position: row.position,
      interpretation_status: row.interpretation_status,
      description: row.description || row.question || "",
    })),
  }));
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
  if (opposeRows.length > supportRows.length && supportRows.length === 0) {
    return "consistently opposed interpreted measures";
  }
  if (supportRows.length > opposeRows.length && opposeRows.length === 0) {
    return "consistently supported interpreted measures";
  }
  if (opposeRows.length || supportRows.length) {
    return "mixed interpreted vote pattern";
  }
  return "insufficient interpreted vote pattern";
}

function summarizePartyPattern({ partyLabel, partyMatchCount, total }) {
  if (!total) {
    return "";
  }

  const partyName = partyLabel ? `most ${formatPartyName(partyLabel)}s` : "most members of their party";
  return `${capitalize(formatSharePhrase(partyMatchCount, total))} of those votes matched ${partyName}.`;
}

function formatLimitedContextOverviewSentence({ ambiguousMeasureGroups, ambiguousRows, issueDomain }) {
  if (issueDomain !== "ECONOMY_TAXES") {
    return `${capitalize(formatNumber(ambiguousRows.length))} additional ${ambiguousRows.length === 1 ? "row remains" : "rows remain"} visible below but ${ambiguousRows.length === 1 ? "is" : "are"} not counted because the available source text does not clearly explain the practical policy effect.`;
  }

  const ambiguousText = formatList(ambiguousMeasureGroups.map((group) => group.overviewPhrase));
  return ambiguousText
    ? `${capitalize(formatNumber(ambiguousRows.length))} ambiguous or limited-context ${ambiguousRows.length === 1 ? "row remains" : "rows remain"} visible for ${ambiguousText}, but ${ambiguousRows.length === 1 ? "it is" : "they are"} not used to summarize the vote pattern.`
    : `${capitalize(formatNumber(ambiguousRows.length))} ambiguous or limited-context ${ambiguousRows.length === 1 ? "row remains" : "rows remain"} visible, but ${ambiguousRows.length === 1 ? "it is" : "they are"} not used to summarize the vote pattern.`;
}

function buildFallbackMeasurePhrase(row, facet) {
  const reviewedText = cleanSentence(row.what_happened || row.why_it_mattered || row.policy_effect);
  if (reviewedText) {
    return reviewedText[0].toLowerCase() + reviewedText.slice(1);
  }
  if (facet) {
    return formatIssueFacet(facet).toLowerCase();
  }
  return "a reviewed measure";
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

function formatIssueFacet(value) {
  return String(value || "")
    .split("_")
    .filter(Boolean)
    .map((segment) => segment[0].toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatQuestionCategory(domain) {
  if (domain === "ECONOMY_TAXES") {
    return "concrete fiscal questions";
  }
  if (domain === "JUSTICE_PUBLIC_SAFETY") {
    return "public-safety and legal-policy questions";
  }
  return "policy questions";
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

function formatPatternBoundary(votePattern) {
  if (votePattern.opposeCount && !votePattern.supportCount) {
    return "opposition to";
  }
  if (votePattern.supportCount && !votePattern.opposeCount) {
    return "support for";
  }
  return "a mixed record on";
}

function formatSimpleStatementBoundary(domain) {
  if (domain === "ECONOMY_TAXES") {
    return 'not as a simple statement that she is "for" or "against taxes."';
  }
  return "not as a simple statement that she is broadly for or against this issue area.";
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
