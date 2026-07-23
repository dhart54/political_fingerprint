export const MEMBER_ACTION_STATUS = Object.freeze({
  yea: "yea",
  nay: "nay",
  present: "present",
  notVoting: "not_voting",
  notYetServing: "not_yet_serving",
  noLongerServing: "no_longer_serving",
  missingEvidence: "missing_evidence",
});

const ACTION_STATUS_ALIASES = new Map([
  ["yea", MEMBER_ACTION_STATUS.yea],
  ["yes", MEMBER_ACTION_STATUS.yea],
  ["nay", MEMBER_ACTION_STATUS.nay],
  ["no", MEMBER_ACTION_STATUS.nay],
  ["present", MEMBER_ACTION_STATUS.present],
  ["not voting", MEMBER_ACTION_STATUS.notVoting],
  ["not_voting", MEMBER_ACTION_STATUS.notVoting],
  ["not yet serving", MEMBER_ACTION_STATUS.notYetServing],
  ["not_yet_serving", MEMBER_ACTION_STATUS.notYetServing],
  ["no longer serving", MEMBER_ACTION_STATUS.noLongerServing],
  ["no_longer_serving", MEMBER_ACTION_STATUS.noLongerServing],
  ["expected action missing from the evidence source", MEMBER_ACTION_STATUS.missingEvidence],
  ["missing evidence", MEMBER_ACTION_STATUS.missingEvidence],
  ["missing_evidence", MEMBER_ACTION_STATUS.missingEvidence],
]);

const NEUTRAL_ARGUMENT_BOUNDARY = "The arguments shown summarize the debate; they do not establish the member's reason for voting.";

export function normalizeMemberActionStatus(value) {
  const normalized = ACTION_STATUS_ALIASES.get(String(value || "").trim().toLowerCase());
  if (!normalized) throw new TypeError(`Unsupported member action status: ${value}`);
  return normalized;
}

export function memberActionStatusCopy(status, memberName = "The member") {
  const normalized = normalizeMemberActionStatus(status);
  return {
    [MEMBER_ACTION_STATUS.yea]: { label: "Yea", sentence: `${memberName} voted Yea.`, analyticallyEligible: true },
    [MEMBER_ACTION_STATUS.nay]: { label: "Nay", sentence: `${memberName} voted Nay.`, analyticallyEligible: true },
    [MEMBER_ACTION_STATUS.present]: { label: "Present", sentence: `${memberName} voted Present.`, analyticallyEligible: false },
    [MEMBER_ACTION_STATUS.notVoting]: { label: "Not Voting", sentence: `${memberName} was recorded as Not Voting.`, analyticallyEligible: false },
    [MEMBER_ACTION_STATUS.notYetServing]: { label: "Before service", sentence: "This action occurred before the member began serving in Congress.", analyticallyEligible: false },
    [MEMBER_ACTION_STATUS.noLongerServing]: { label: "After service", sentence: "This action occurred after the member's congressional service ended.", analyticallyEligible: false },
    [MEMBER_ACTION_STATUS.missingEvidence]: { label: "Evidence unavailable", sentence: "The member was eligible for this action, but the expected evidence record is unavailable or unresolved.", analyticallyEligible: false },
  }[normalized];
}

export function buildSharedLegislativeAction(entry, row = {}, { episodeId = null, policyFamilyId = null } = {}) {
  const oneSidedBoundary = entry?.two_minute?.one_sided_argument_note
    || (/no adequate stage-specific opposing argument/i.test(entry?.two_minute?.argument_boundary || "")
    ? "No adequate stage-specific opposing argument was found in the reviewed official materials."
    : null);
  return Object.freeze({
    id: `roll-${entry.roll}`,
    roll: Number(entry.roll),
    actionIdentity: `House roll call ${entry.roll}`,
    episodeId,
    policyFamilyId,
    measure: row.description || row.question || entry.measure_id,
    legislativeStage: entry.stage,
    date: row.vote_date,
    practicalChoice: entry.ten_second?.practical_choice,
    whatChanged: Object.freeze({
      before: entry.thirty_second?.prior_baseline,
      changeAtStake: entry.thirty_second?.mechanism,
    }),
    impactAndOutcome: Object.freeze({
      affected: entry.thirty_second?.affected,
      scaleAndTiming: entry.thirty_second?.scale_or_timing,
      outcome: entry.thirty_second?.what_happened_next,
    }),
    arguments: Object.freeze({
      supporters: neutralArgument(entry.two_minute?.supporter_argument),
      opponents: neutralArgument(entry.two_minute?.opponent_argument),
    }),
    argumentBoundary: NEUTRAL_ARGUMENT_BOUNDARY,
    oneSidedArgumentNote: oneSidedBoundary,
    additionalDetail: Object.freeze({
      detail: substantiveDetail(entry.two_minute?.detail),
      laterHistory: substantiveLaterHistory(entry.two_minute?.later_history),
    }),
    importantContext: Object.freeze(neutralContext(entry.two_minute?.caveats || [])),
    sources: Object.freeze((entry.two_minute?.sources || []).map(neutralSource)),
  });
}

export function buildMemberActionOverlay(entry, memberDisplayName) {
  const status = normalizeMemberActionStatus(entry.action_status || entry.member_action);
  const statusCopy = memberActionStatusCopy(status, memberShortName(memberDisplayName));
  const suppliedResult = entry.ten_second?.member_action_and_result;
  return Object.freeze({
    actionId: `roll-${entry.roll}`,
    status,
    label: statusCopy.label,
    headline: entry.ten_second?.headline || `${statusCopy.label} on this action`,
    actionAndResult: isServiceOrMissing(status) ? statusCopy.sentence : suppliedResult || statusCopy.sentence,
    analyticallyEligible: statusCopy.analyticallyEligible,
  });
}

export function sharedEvidenceHasMemberSpecificText(value, memberNames = []) {
  const serialized = JSON.stringify(value);
  return memberNames.some((name) => {
    const last = String(name).trim().split(/\s+/).at(-1);
    return name && new RegExp(escapeRegex(name), "i").test(serialized)
      || last && new RegExp(`\\b${escapeRegex(last)}\\b`, "i").test(serialized);
  }) || /why\s+[A-Z][a-z]+\s+voted|member-specific action|party-specific member explanation/i.test(serialized);
}

export function neutralizeSharedSources(sources = []) {
  return Object.freeze(sources.map(neutralSource));
}

export function inclusionClassForStatus(status) {
  const normalized = normalizeMemberActionStatus(status);
  if (normalized === MEMBER_ACTION_STATUS.notVoting) return "not_voting";
  if (normalized === MEMBER_ACTION_STATUS.present) return "present";
  if (normalized === MEMBER_ACTION_STATUS.notYetServing || normalized === MEMBER_ACTION_STATUS.noLongerServing) return "service_ineligible";
  if (normalized === MEMBER_ACTION_STATUS.missingEvidence) return "missing_evidence";
  return "substantive";
}

function neutralArgument(argument) {
  if (!argument?.argument) return undefined;
  return Object.freeze({ attribution: argument.attribution, argument: argument.argument });
}

function neutralSource(source) {
  return Object.freeze({
    ...source,
    locator: String(source.locator || "")
      .replace(/,?\s+and\s+[A-Z][A-Za-z.' -]+\s+(?:Yea|Nay|Yes|No|Present|Not Voting)\b/gi, ""),
  });
}

function neutralContext(items) {
  const result = [];
  for (const item of items) {
    if (!item) continue;
    if (/one policy episode|belongs? to one episode|vote does not (?:reveal|establish)|does not establish motive|does not reveal why|why [A-Z][a-z]+|reason assigned to|a (?:yea|nay) does not assign a reason/i.test(item)) continue;
    if (/^the amendment failed\.?$/i.test(item)) continue;
    result.push(item);
  }
  return [...new Set(result)];
}

function substantiveDetail(value) {
  if (!value) return undefined;
  if (/substantive condition.*not a generic procedural vote|eligibility, transfer rules, exclusions, and agency participation were defined/i.test(value)) return undefined;
  return value;
}

function substantiveLaterHistory(value) {
  if (!value || /^received in the senate after house passage\.?$/i.test(value)) return undefined;
  return value;
}

function isServiceOrMissing(status) {
  return [MEMBER_ACTION_STATUS.notYetServing, MEMBER_ACTION_STATUS.noLongerServing, MEMBER_ACTION_STATUS.missingEvidence].includes(status);
}

function memberShortName(value) {
  return String(value || "The member").trim().replace(/,?\s+(?:Jr\.?|Sr\.?|II|III|IV)$/i, "").split(/\s+/).at(-1) || "The member";
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
