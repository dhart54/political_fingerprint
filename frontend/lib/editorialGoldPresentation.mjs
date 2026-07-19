export const fousheeEconomyIssueRead = Object.freeze({
  primarySummary:
    "In this sample, Foushee voted against specific proposals involving government funding, frameworks for later tax-and-spending legislation, military construction and veterans programs, and SBA loan eligibility. The six substantive votes represent four policy episodes. They reveal several specific voting patterns, but this sample is not yet broad enough to establish one overarching Economy & Taxes philosophy.",
  patterns: Object.freeze([
    "Opposed both stages of the 2025 government-funding episode.",
    "Opposed both stages of the FY2025–FY2034 budget-framework episode.",
    "Opposed the House military-construction and veterans funding proposal.",
    "Opposed immigration-status restrictions on SBA-backed business loans.",
  ]),
  votingContext:
    "Foushee voted with the majority of House Democrats on all 6 substantive roll calls in this sample, covering 4 policy episodes.",
  votingContextBoundary:
    "Party alignment describes how these votes compared with other Democrats. It does not explain why Foushee voted that way, and repeated stages are not separate policy positions.",
  howToRead:
    "These votes concern several different funding, budget-process, veterans, and small-business policy choices. A recorded No establishes opposition to the proposal at that stage. Repeated votes across independent policy episodes may support broader voting themes, but one vote does not reveal motive or establish a position on every provision in a package.",
});


export const editorialInferenceLadder = Object.freeze({
  recordedAction: Object.freeze({
    level: 1,
    description: "A factual description of one verified vote at its recorded legislative stage.",
  }),
  boundedVotingPattern: Object.freeze({
    level: 2,
    description:
      "A summary of verified actions across clearly defined policy episodes, with repeated stages identified as stages rather than independent positions.",
  }),
  broaderPoliticalPhilosophy: Object.freeze({
    level: 3,
    description:
      "A calibrated generalization across enough independent episodes, mechanisms, contrary evidence, and time to demonstrate a broader voting theme without inferring motive.",
    allowedWhenSupported: true,
  }),
});


export const fousheeEconomyInferenceLevel = "boundedVotingPattern";


export function buildImportantContext(entry) {
  const context = [];
  const seen = new Set();

  appendUnique(context, seen, entry.two_minute.later_history);
  for (const caveat of entry.two_minute.caveats) {
    if (isMotiveBoundary(caveat) || isArgumentBoundary(caveat)) {
      continue;
    }
    appendUnique(context, seen, caveat);
  }

  appendUnique(
    context,
    seen,
    entry.member_action === "Not Voting"
      ? "The record does not reveal why Foushee did not vote."
      : "The vote record does not reveal why Foushee voted this way.",
  );
  appendUnique(
    context,
    seen,
    "Supporter and opponent arguments are attributed advocacy, not evidence of Foushee's motive.",
  );

  return context;
}


export function groupOfficialSources(sources) {
  const groups = new Map();
  const seenUrls = new Set();

  for (const source of sources) {
    const canonicalUrl = canonicalizeUrl(source.url);
    if (seenUrls.has(canonicalUrl)) {
      continue;
    }
    seenUrls.add(canonicalUrl);
    if (!groups.has(source.group)) {
      groups.set(source.group, []);
    }
    groups.get(source.group).push(source);
  }

  const preferredOrder = [
    "Vote and legislative status",
    "Bill or resolution text",
    "Nonpartisan analysis",
    "Competing arguments",
    "Additional official evidence",
  ];

  return [...groups.entries()]
    .map(([name, items]) => ({ name, items }))
    .sort((left, right) => preferredOrder.indexOf(left.name) - preferredOrder.indexOf(right.name));
}


function appendUnique(result, seen, value) {
  const key = normalizeContext(value);
  if (!value || seen.has(key)) {
    return;
  }
  seen.add(key);
  result.push(value);
}


function normalizeContext(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}


function isMotiveBoundary(value) {
  return /does not (reveal|explain)|why foushee|foushee's rationale|foushee’s rationale/i.test(value);
}


function isArgumentBoundary(value) {
  return /attributed|argument|advocacy|debate documents competing/i.test(value);
}


function canonicalizeUrl(value) {
  return String(value || "").trim().replace(/\/$/, "");
}
