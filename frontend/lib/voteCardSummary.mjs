export function buildVoteCardSummary(row, { representativeName = "" } = {}) {
  if (!row || row.interpretation_status !== "interpreted") {
    return "";
  }

  const position = formatVotePosition(row.position);
  const facetSummary = buildFacetSpecificVoteCardSummary(row, { representativeName, position });
  if (facetSummary) {
    return facetSummary;
  }

  const action = cleanSummarySentence(row.what_happened || buildUsefulInterpretationText(row.plain_english_summary));
  const stakes = cleanSummarySentence(row.why_it_mattered || buildPlainTakeaway(row));
  const voteMeaning = buildPlainVoteMeaning(row, { representativeName });
  const context = buildPlainPartyOutcomeContext(row);
  const voteAndContext = combineVoteMeaningAndContext(voteMeaning, context);

  return [position, action, stakes, voteAndContext]
    .filter(Boolean)
    .map((piece, index) => (index === 0 ? `${piece}.` : ensurePeriod(piece)))
    .join(" ");
}

export function buildLimitedContextSummary(row) {
  const position = formatVotePosition(row?.position);

  if (row?.interpretation_status === "ambiguous" || row?.interpretation_status === "insufficient_evidence") {
    const explanation =
      row.uncertainty_note ||
      row.interpretation_reason ||
      "The available source text does not explain the practical policy effect.";
    return `${position}. ${cleanSummarySentence(explanation)}. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.`;
  }

  return "";
}

function buildFacetSpecificVoteCardSummary(row, { representativeName = "", position }) {
  const memberLabel = formatRepresentativeReference(representativeName) || extractMemberLabel(row);
  const context = buildPlainPartyOutcomeContext(row);
  const voteMeaning = `${memberLabel} voted ${formatPassageDirection(row)} passing the bill`;
  const voteAndContext = combineVoteMeaningAndContext(voteMeaning, context);
  const facet = String(row.issue_facet || "");
  let action = "";

  if (facet === "fentanyl_scheduling_and_penalties") {
    action =
      "The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths";
  } else if (facet === "federal_law_enforcement_equipment") {
    action =
      "The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms";
  }

  if (!action) {
    return "";
  }

  return [position, action, voteAndContext]
    .filter(Boolean)
    .map((piece, index) => (index === 0 ? `${piece}.` : ensurePeriod(piece)))
    .join(" ");
}

export function formatVotePosition(position) {
  if (position === "not_voting") {
    return "Not voting";
  }
  return String(position || "")
    .split("_")
    .map((segment) => (segment ? segment[0].toUpperCase() + segment.slice(1) : segment))
    .join(" ");
}

function formatPassageDirection(row) {
  if (row.position === row.oppose_position) {
    return "against";
  }
  if (row.position === row.support_position) {
    return "for";
  }
  return "on";
}

function buildPlainVoteMeaning(row, { representativeName = "" } = {}) {
  const memberLabel = formatRepresentativeReference(representativeName) || extractMemberLabel(row);
  const facet = String(row.issue_facet || "");

  if (row.position === "not_voting") {
    return `${memberLabel} was recorded as not voting, so this row does not count as support or opposition`;
  }

  const votedAgainst = row.position === row.oppose_position;
  const votedFor = row.position === row.support_position;
  const direction = votedAgainst ? "against" : votedFor ? "for" : "on";

  if (facet === "budget_reconciliation_and_debt_limit") {
    return `${memberLabel} voted ${direction} that budget framework`;
  }
  if (facet === "small_business_loan_eligibility") {
    return `${memberLabel} voted ${direction} adding those eligibility restrictions`;
  }
  if (facet === "military_construction_and_va_appropriations") {
    return `${memberLabel} voted ${direction} that military construction and Veterans Affairs funding bill`;
  }
  if (facet === "temporary_government_funding") {
    return `${memberLabel} voted ${direction} that temporary funding bill`;
  }
  if (facet === "government_funding_and_shutdown") {
    return `${memberLabel} voted ${direction} that shutdown-ending funding package`;
  }
  if (facet === "small_business_regulation") {
    return `${memberLabel} voted ${direction} that SBA regulatory-cost cap bill`;
  }

  return `${memberLabel} voted ${formatVotePosition(row.position)}`;
}

function buildPlainPartyOutcomeContext(row) {
  const context = row.vote_context;
  const pieces = [];

  if (context?.member_voted_with_party_majority === true) {
    const partyName = context.member_party ? formatPartyName(context.member_party) : "party";
    pieces.push(`matching most ${partyName}s`);
  } else if (context?.member_voted_with_party_majority === false) {
    const partyName = context.member_party ? formatPartyName(context.member_party) : "party";
    pieces.push(`not matching most ${partyName}s`);
  }

  const outcome = buildPlainOutcomeSentence(row);
  if (pieces.length && outcome) {
    return `${pieces.join(", ")}. ${outcome}`;
  }
  if (pieces.length) {
    return pieces.join(", ");
  }
  return outcome;
}

function combineVoteMeaningAndContext(voteMeaning, context) {
  if (!voteMeaning) {
    return context;
  }
  if (!context) {
    return voteMeaning;
  }
  if (/^(matching|not matching)\b/.test(context)) {
    return `${voteMeaning}, ${context}`;
  }
  return `${voteMeaning}. ${context}`;
}

function buildPlainOutcomeSentence(row) {
  const context = row.vote_context;
  if (!context?.final_result) {
    return "";
  }

  if (context.final_result === "failed") {
    return "The measure failed";
  }
  if (context.final_result !== "passed") {
    return "";
  }
  if (Number(context.vote_margin) > 0 && Number(context.vote_margin) <= 5) {
    return "The measure passed narrowly";
  }
  if (context.vote_type === "final_passage") {
    return "The bill passed the House";
  }
  return "The measure passed";
}

function buildPlainTakeaway(row) {
  const summary = buildUsefulInterpretationText(row.plain_english_summary);
  const effect = buildUsefulInterpretationText(row.policy_effect);
  const text = `${summary} ${effect}`.toLowerCase();

  if (text.includes("budget blueprint") || text.includes("reconciliation")) {
    return "This vote helped set the rules for a later fast-track budget bill that could affect taxes, spending, deficits, and the debt limit.";
  }
  if (text.includes("shutdown") || text.includes("continuing appropriations") || text.includes("short-term funding")) {
    if (text.includes("back pay") || text.includes("reduction-in-force")) {
      return "This vote was about ending a shutdown, paying federal workers, and deciding how agencies would operate while longer-term funding was still unresolved.";
    }
    return "This vote was about avoiding a shutdown by keeping most federal agencies temporarily funded while longer-term spending bills were unfinished.";
  }
  if (text.includes("small business administration") || text.includes("sba")) {
    if (text.includes("loan")) {
      return "This vote was about restricting access to certain SBA-backed small-business loans based on immigration or residency status.";
    }
    return "This vote was about limiting net new SBA rulemaking costs for small businesses.";
  }
  if (text.includes("military construction") || text.includes("veterans affairs")) {
    return "This vote was about funding military construction, military housing, and veterans-related agencies and programs.";
  }

  return effect || summary;
}

function extractMemberLabel(row) {
  const memberContext = String(row?.member_vote_context || "");
  const match = memberContext.match(/^([A-Z][A-Za-z.'-]+)/);
  return match?.[1] || "This representative";
}

function formatRepresentativeReference(name) {
  const cleaned = String(name || "").trim();
  if (!cleaned) {
    return "";
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

function cleanSummarySentence(value) {
  return String(value || "")
    .replace(/\.$/, "")
    .trim();
}

function ensurePeriod(value) {
  const text = String(value || "").trim();
  if (!text) {
    return "";
  }
  return /[.!?]$/.test(text) ? text : `${text}.`;
}

function buildUsefulInterpretationText(value) {
  return String(value || "")
    .replace(/^This was a vote on (adopting|passing|agreeing to) (the|a) (resolution|bill|measure)\.?\s*/i, "")
    .replace(/^This was a vote on (adopting|passing|agreeing to) .+?\.\s*/i, "")
    .trim();
}
