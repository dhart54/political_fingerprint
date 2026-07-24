import { hasRawIsoDateRange, publicSentenceDefects } from "./editorialTextIntegrity.mjs";
import { MEMBER_ACTION_STATUS, sharedEvidenceHasMemberSpecificText } from "./editorialSharedEvidence.mjs";

export const EDITORIAL_STANDARDIZATION_RULES = Object.freeze([
  rule("STATUS-001", "block", "Real content must remain pending, unpromoted, and production-ineligible."),
  rule("FIXTURE-001", "block", "Reference fixtures use a non-publication standardization designation."),
  rule("SHARED-001", "block", "Shared evidence must remain member-neutral."),
  rule("SHARED-002", "block", "Shared evidence facts must remain stable across member overlays."),
  rule("OVERLAY-001", "block", "Member action prose must match the recorded overlay status."),
  rule("ACTION-001", "block", "Every substantive action needs an exact identity."),
  rule("ACTION-002", "block", "Every substantive action needs a Congress and chamber context."),
  rule("ACTION-003", "block", "Every substantive action needs an exact legislative stage."),
  rule("ACTION-004", "block", "Every substantive action needs a neutral practical choice."),
  rule("ACTION-005", "block", "Prior baseline must be present or reason-coded."),
  rule("ACTION-006", "block", "Change or mechanism at stake must be present or reason-coded."),
  rule("ACTION-007", "block", "Affected groups must be present or reason-coded."),
  rule("ACTION-008", "block", "Scale and timing must be present or reason-coded."),
  rule("ACTION-009", "block", "Outcome or status must be present or reason-coded."),
  rule("ACTION-010", "block", "Official vote source is required."),
  rule("ACTION-011", "block", "Official measure or action source is required."),
  rule("ACTION-012", "block", "Argument evidence must be sourced, absent with a reason, or explicitly unresolved."),
  rule("ACTION-013", "block", "Public member action summaries must be complete sentences."),
  rule("SOURCE-001", "block", "Public sources need permitted nonblank HTTPS URLs."),
  rule("SOURCE-002", "block", "Source locators must map evidence without implying human verification."),
  rule("EPISODE-001", "block", "Episode IDs, Congress, and policy-family identities are required."),
  rule("EPISODE-002", "block", "Multi-action episodes need an explicit relationship."),
  rule("EPISODE-003", "block", "Episode action order and expected membership must match exactly."),
  rule("EPISODE-004", "block", "An action may not appear in multiple episodes without an explicit cross-reference."),
  rule("EPISODE-005", "block", "Episodes may not merge actions across Congresses."),
  rule("COVERAGE-001", "block", "Coverage counts must agree with episode and action structure."),
  rule("ANALYSIS-001", "block", "Analytical categories must meet their episode-support rules."),
  rule("ANALYSIS-002", "block", "Procedural actions may not support a substantive conclusion."),
  rule("ANALYSIS-003", "block", "Present, Not Voting, service-ineligible, and missing actions cannot count as support or opposition."),
  rule("SYNTHESIS-001", "block", "Direction-only evidence cannot substitute for a substantive repeated policy rationale."),
  rule("CONCLUSION-UTILITY-001", "block", "The conclusion must synthesize rather than reproduce the episode inventory."),
  rule("CONCLUSION-UTILITY-002", "block", "Action direction alone cannot serve as a substantive thesis."),
  rule("CONCLUSION-UTILITY-003", "block", "Repeated, selective, and divided conclusions require a supported policy dimension."),
  rule("CONCLUSION-UTILITY-004", "block", "A heterogeneous uniform record requires a concrete supported policy contrast."),
  rule("CONCLUSION-UTILITY-005", "block", "The conclusion must add synthesis rather than duplicate every analytical finding."),
  rule("CONCLUSION-UTILITY-006", "block", "Circular action-direction propositions are not reader-useful synthesis."),
  rule("CONCLUSION-UTILITY-007", "block", "A broad philosophy claim requires a supported substantive threshold."),
  rule("CONCLUSION-UTILITY-008", "warning", "Qualification should not crowd out the strongest defensible result."),
  rule("CONCLUSION-UTILITY-009", "block", "No more than two episodes may be individually named when policy clusters are available."),
  rule("CONCLUSION-UTILITY-010", "block", "The reader label must match the selected conclusion archetype."),
  rule("DETAIL-001", "block", "Motive boundaries and deterministic duplicate detail may render only once."),
  rule("DETAIL-002", "warning", "Near-duplicate detail that is not deterministically equivalent needs review."),
  rule("PUBLIC-001", "block", "Internal workflow and methodology language may not render publicly."),
  rule("PUBLIC-002", "block", "The selected rich issue may not reappear as a generic issue card."),
  rule("PUBLIC-003", "block", "A rich issue may feature no more than five episodes."),
  rule("PUBLIC-004", "block", "Raw ISO date ranges may not render publicly."),
  rule("PUBLIC-005", "block", "D.C. repeal action wording must remain bounded to most provisions."),
  rule("SERVICE-001", "block", "Service-ineligible statuses require exact action-date eligibility evidence."),
]);

const RULE_BY_ID = new Map(EDITORIAL_STANDARDIZATION_RULES.map((item) => [item.id, item]));
const REASON_CODES = new Set(["not_applicable", "not_material", "not_material_or_not_available", "adequate_official_argument_not_found", "source_unresolved", "pending_research"]);
const FORBIDDEN_PUBLIC = /how to read this conclusion|reviewed conclusion available|rerun this inference|candidate conclusion|additional annotations|immutable philosophy|open representative votes before reading this as|human_approval_pending|not_promoted|productioneligible|selection rationale|raw algorithmic|internal schema/i;
const MOTIVE_BOUNDARY = /does not (?:establish|reveal|explain).{0,40}(?:motive|reason)|do not establish the member's reason/i;

export function validateEditorialStandardization({
  candidate,
  experience,
  renderedText = "",
  genericIssueCards = [],
  serviceChecks = [],
  sharedEvidenceVariants = [],
} = {}) {
  if (!candidate || !experience) throw new TypeError("candidate and experience are required");
  const findings = [];
  const identity = candidate.identity || {};
  const sliceId = candidate.standardizationFixture?.fixtureId || `${identity.memberId}-${identity.issueId}`;
  const context = { sliceId, memberId: identity.memberId, issue: identity.issueId };
  const add = (ruleId, details = {}) => findings.push(finding(ruleId, context, details));

  validateStatus(candidate, add);
  validateSharedEvidence(candidate, sharedEvidenceVariants, add);
  validateActions(experience, add);
  validateEpisodes(candidate, experience, add);
  validateAnalysis(candidate, experience, add);
  validateConclusionUtility(candidate, experience, add);
  validatePublicSurface(candidate, experience, renderedText, genericIssueCards, add);
  validateServiceChecks(serviceChecks, add);

  const blocked = findings.some((item) => item.severity === "block");
  return Object.freeze({
    schemaVersion: "editorial_standardization_validation_v1",
    generatedFrom: "deterministic_candidate_and_public_view_contracts",
    sliceId,
    memberId: identity.memberId,
    issue: identity.issueId,
    state: blocked ? "blocked" : findings.length ? "pass_with_nonblocking_warnings" : "pass",
    publicationEligibilityMustFail: blocked,
    findings: Object.freeze(findings),
  });
}

export function summarizeValidationReports(reports) {
  const findings = reports.flatMap((report) => report.findings);
  return {
    state: reports.some((report) => report.state === "blocked") ? "blocked" : reports.some((report) => report.findings.length) ? "pass_with_nonblocking_warnings" : "pass",
    sliceCount: reports.length,
    ruleCount: EDITORIAL_STANDARDIZATION_RULES.length,
    ruleCountBySeverity: Object.fromEntries(["block", "warning"].map((severity) => [severity, EDITORIAL_STANDARDIZATION_RULES.filter((item) => item.severity === severity).length])),
    findingCountBySeverity: Object.fromEntries(["block", "warning"].map((severity) => [severity, findings.filter((item) => item.severity === severity).length])),
  };
}

function validateStatus(candidate, add) {
  const publication = candidate.publication || {};
  if (publication.editorialStatus !== "human_approval_pending" || publication.benchmarkStatus !== "not_promoted" || publication.productionEligible !== false) {
    add("STATUS-001", { fieldPath: "publication", explanation: "Real editorial content crossed the review-only publication boundary." });
  }
  if (candidate.standardizationFixture && !["human_reviewed_presentation_fixture", "reference_render_fixture", "standardization_regression_fixture"].includes(candidate.standardizationFixture.designation)) {
    add("FIXTURE-001", { fieldPath: "standardizationFixture.designation", explanation: "The fixture designation is absent from the allowed non-publication vocabulary." });
  }
}

function validateSharedEvidence(candidate, variants, add) {
  const shared = candidate.source?.shared_legislative_actions || [];
  const memberNames = ["Valerie P. Foushee", "Foushee", "Thomas Massie", "Massie", ...(candidate.validationMemberNames || [])];
  if (sharedEvidenceHasMemberSpecificText(shared, memberNames)) {
    add("SHARED-001", { fieldPath: "source.shared_legislative_actions", explanation: "Representative-specific language was found in shared legislative evidence." });
  }
  if (variants.length > 1) {
    const baseline = stableSharedFacts(variants[0]);
    if (variants.slice(1).some((variant) => stableSharedFacts(variant) !== baseline)) {
      add("SHARED-002", { fieldPath: "sharedEvidenceVariants", explanation: "Shared facts, effects, arguments, or sources changed across member overlays." });
    }
  }
}

function validateActions(experience, add) {
  for (const action of experience.episodes.flatMap((episode) => episode.actions)) {
    const actionContext = { episodeId: action.episodeId, actionId: action.id, roll: action.roll };
    if (!action.actionIdentity || !Number.isFinite(action.roll)) add("ACTION-001", { ...actionContext, fieldPath: "actionIdentity", explanation: "Action identity or authoritative roll is missing." });
    if (!action.legislativeStage) add("ACTION-003", { ...actionContext, fieldPath: "legislativeStage", explanation: "Exact legislative stage is missing." });
    requireValue(action.practicalChoice, "ACTION-004", "practicalChoice", actionContext, add);
    requireValue(action.whatChanged?.before, "ACTION-005", "whatChanged.before", actionContext, add);
    requireValue(action.whatChanged?.changeAtStake, "ACTION-006", "whatChanged.changeAtStake", actionContext, add);
    requireValue(action.impactAndOutcome?.affected, "ACTION-007", "impactAndOutcome.affected", actionContext, add);
    requireValue(action.impactAndOutcome?.scaleAndTiming, "ACTION-008", "impactAndOutcome.scaleAndTiming", actionContext, add);
    requireValue(action.impactAndOutcome?.outcome, "ACTION-009", "impactAndOutcome.outcome", actionContext, add);
    if (!action.date || !experience.identity?.congress) add("ACTION-002", { ...actionContext, fieldPath: "date", explanation: "Action Congress or date context is missing." });
    const sources = action.sources || [];
    if (!sources.some(isOfficialVoteSource)) add("ACTION-010", { ...actionContext, fieldPath: "sources", explanation: "No official roll-call source is attached." });
    if (!sources.some(isOfficialMeasureSource)) add("ACTION-011", { ...actionContext, fieldPath: "sources", explanation: "No official measure or action source is attached." });
    for (const source of sources) {
      if (!isPermittedUrl(source.url)) add("SOURCE-001", { ...actionContext, fieldPath: "sources[].url", explanation: "A source URL is blank, non-HTTPS, or outside the permitted official/nonpartisan source set." });
      if (!source.locator) add("SOURCE-002", { ...actionContext, fieldPath: "sources[].locator", explanation: "A source is attached without a claim locator." });
    }
    const argumentState = action.argumentSupport || {};
    if (argumentState.opponents === "unsupported" || argumentState.supporters === "unsupported") {
      add("ACTION-012", { ...actionContext, fieldPath: "argumentSupport", explanation: "Unsupported argument prose would render as sourced." });
    }
    for (const defect of publicSentenceDefects(action.actionAndResult)) {
      add("ACTION-013", { ...actionContext, fieldPath: "actionAndResult", explanation: `Incomplete public action summary (${defect}).` });
    }
    if (action.actionStatus === MEMBER_ACTION_STATUS.yea && !/voted (?:yea|yes)|supported/i.test(action.actionAndResult || "")) add("OVERLAY-001", { ...actionContext, fieldPath: "actionAndResult", explanation: "Yea overlay prose does not describe a Yea action." });
    if (action.actionStatus === MEMBER_ACTION_STATUS.nay && !/voted (?:nay|no)|opposed/i.test(action.actionAndResult || "")) add("OVERLAY-001", { ...actionContext, fieldPath: "actionAndResult", explanation: "Nay overlay prose does not describe a Nay action." });
    const combinedDetail = [action.whatChanged?.changeAtStake, action.argumentBoundary, action.additionalDetail?.detail, action.additionalDetail?.laterHistory, ...(action.importantContext || [])].filter(Boolean);
    if (combinedDetail.filter((value) => MOTIVE_BOUNDARY.test(value)).length > 1) add("DETAIL-001", { ...actionContext, fieldPath: "importantContext", explanation: "The same motive boundary appears more than once." });
    if (action.argumentBoundary && (action.importantContext || []).some((value) => /a (?:yea|nay) does not (?:reveal|establish|explain|assign)/i.test(value))) {
      add("DETAIL-001", { ...actionContext, fieldPath: "importantContext", explanation: "A generic vote-motive disclaimer repeats the neutral argument boundary." });
    }
    const normalized = combinedDetail.map(normalizeText);
    if (new Set(normalized).size !== normalized.length) add("DETAIL-001", { ...actionContext, fieldPath: "additionalDetail", explanation: "Deterministically duplicate detail is exposed more than once." });
    const semanticKeys = combinedDetail.map(detailSemanticKey).filter(Boolean);
    if (new Set(semanticKeys).size !== semanticKeys.length) add("DETAIL-001", { ...actionContext, fieldPath: "additionalDetail", explanation: "The same exact-version qualification is repeated across detail and context." });
  }
}

function validateEpisodes(candidate, experience, add) {
  const seenActions = new Set();
  for (const episode of experience.episodes) {
    const episodeContext = { episodeId: episode.id };
    if (!episode.id || !episode.congress || !episode.policyFamilyId) add("EPISODE-001", { ...episodeContext, fieldPath: "episodes[]", explanation: "Episode identity, Congress, or policy family is missing." });
    if (episode.actions.length > 1 && !episode.relationship) add("EPISODE-002", { ...episodeContext, fieldPath: "relationship", explanation: "A multi-action episode lacks an explicit relationship." });
    if (episode.actions.map((action) => action.roll).join(",") !== (episode.rolls || []).join(",")) add("EPISODE-003", { ...episodeContext, fieldPath: "rolls", explanation: "Expected actions, actual actions, or their order do not match." });
    for (const action of episode.actions) {
      if (seenActions.has(action.id)) add("EPISODE-004", { ...episodeContext, actionId: action.id, fieldPath: "actions", explanation: "The same action appears in multiple episodes." });
      seenActions.add(action.id);
      if (action.congress && action.congress !== episode.congress) add("EPISODE-005", { ...episodeContext, actionId: action.id, fieldPath: "actions[].congress", explanation: "An episode crosses Congress boundaries." });
    }
  }
  const coverage = experience.publicPresentation?.coverage || {};
  if (coverage.completeEpisodes === 0 && experience.episodes.some((episode) => episode.coverageStatus === "complete")) add("COVERAGE-001", { fieldPath: "publicPresentation.coverage.completeEpisodes", explanation: "Coverage reports zero complete episodes despite complete episode structure." });
  if (coverage.expectedEpisodes && coverage.expectedEpisodes !== experience.episodes.length) add("COVERAGE-001", { fieldPath: "publicPresentation.coverage.expectedEpisodes", explanation: "Expected episode count does not match the shared episode contract." });
  if (candidate.validationHints?.crossCongressRelationshipWithoutFamily) add("EPISODE-005", { fieldPath: "validationHints.crossCongressRelationshipWithoutFamily", explanation: "A cross-Congress relationship lacks policy-family separation." });
}

function validateAnalysis(candidate, experience, add) {
  const episodeById = new Map(experience.episodes.map((episode) => [episode.id, episode]));
  const supplied = candidate.synthesis?.analyticalSections || {};
  for (const item of asArray(supplied.repeatedPatterns)) {
    const refs = item.episodeIds || (item.episodeId ? [item.episodeId] : []);
    if (refs.length === 1 && (episodeById.get(refs[0])?.actionCount || 0) < 2) add("ANALYSIS-001", { episodeId: refs[0], fieldPath: "synthesis.analyticalSections.repeatedPatterns", explanation: "A one-action episode is labeled as a repeated pattern." });
  }
  for (const item of asArray(supplied.policyTrajectories)) {
    if (item.episodeId && (episodeById.get(item.episodeId)?.actionCount || 0) < 2) add("ANALYSIS-001", { episodeId: item.episodeId, fieldPath: "synthesis.analyticalSections.policyTrajectories", explanation: "A policy trajectory has fewer than two related actions." });
  }
  if (candidate.validationHints?.proceduralConclusionRolls?.length) add("ANALYSIS-002", { roll: candidate.validationHints.proceduralConclusionRolls[0], fieldPath: "synthesis.primary", explanation: "A procedural action is cited as substantive conclusion support." });
  if (candidate.validationHints?.nonYesNoCounted) add("ANALYSIS-003", { fieldPath: "source.inference_candidate.coverage", explanation: "A non-Yes/No action was counted as support or opposition." });
  const sampleBoundaryCount = (candidate.synthesis?.primary?.match(/\b(?:reviewed )?sample\b/gi) || []).length;
  if (sampleBoundaryCount > 1) add("DETAIL-001", { fieldPath: "synthesis.primary", explanation: "The bounded sample phrase is deterministically duplicated in the primary conclusion." });
  validateSynthesisBasis(candidate, experience, supplied, add);
}

function detailSemanticKey(value) {
  const text = String(value || "").toLowerCase();
  if (/substitute/.test(text) && /exception/.test(text)) return "substitute-exceptions";
  if (/not repeal every|most provisions/.test(text)) return "bounded-repeal";
  return null;
}

function validateSynthesisBasis(candidate, experience, supplied, add) {
  const inference = candidate.source?.inference_candidate || {};
  const basis = inference.candidate_basis || {};
  const primary = candidate.synthesis?.primary || "";
  const uniformArchetype = inference.candidate_id === "uniform_direction_without_common_policy_rationale"
    && basis.basis_type === "uniform_action_direction";
  const directionOnlyThemes = new Set(["cross-mechanism-opposition", "cross-mechanism-support"]);
  const substantiveThemes = asArray(basis.substantive_theme_ids).filter((id) => !directionOnlyThemes.has(id));
  const circularDirection = /(?:support|oppos|yea|nay).{0,100}(?:(?:across|distinct|different|multiple|heterogeneous).{0,80}(?:mechanism|proposal|action)|(?:mechanism|proposal|action).{0,80}(?:across|distinct|different|multiple|heterogeneous))/i.test(primary);

  if (!uniformArchetype && (
    basis.basis_type === "uniform_action_direction"
    || (basis.basis_type === "substantive_repeated_pattern" && substantiveThemes.length === 0)
    || circularDirection
  )) {
    add("SYNTHESIS-001", {
      fieldPath: "source.inference_candidate.candidate_basis",
      explanation: "The primary conclusion substitutes common action direction across heterogeneous mechanisms for a shared substantive policy dimension.",
    });
  }

  for (const item of asArray(supplied.repeatedPatterns)) {
    const text = item.text || "";
    if (/(?:support|oppos|yea|nay).{0,80}(?:reviewed )?(?:actions?|proposals?|mechanisms?)(?:\s+across|\s+in)?/i.test(text)
      && !/(?:D\.C\.|fentanyl|report|firearm|pursuit|polic|safeguard|research|evidence|authority)/i.test(text)) {
      add("SYNTHESIS-001", {
        fieldPath: "synthesis.analyticalSections.repeatedPatterns",
        explanation: "A repeated pattern contains action direction but no shared substantive policy theme.",
      });
    }
  }

  const statuses = experience.episodes
    .flatMap((episode) => episode.actions)
    .filter((action) => action.inclusionClass === "substantive")
    .map((action) => action.actionStatus);
  const homogeneous = statuses.length > 1 && new Set(statuses).size === 1;
  if (homogeneous && /(?:coherent|overarching|consistent).{0,50}(?:philosophy|approach|orientation|stance)/i.test(primary)
    && !/(?:does not|do not|cannot|not enough to) establish/i.test(primary)) {
    add("SYNTHESIS-001", {
      fieldPath: "synthesis.primary",
      explanation: "A homogeneous action vector is described as a coherent policy philosophy without a substantive shared-theme basis.",
    });
  }
}

function validateConclusionUtility(candidate, experience, add) {
  const inference = candidate.source?.inference_candidate || {};
  const model = candidate.synthesis?.conclusionModel || inference.conclusion_model;
  const report = candidate.synthesis?.compressionReport || inference.compression_report;
  if (!model || !report) return;
  const primary = candidate.synthesis?.primary || inference.primary_conclusion || "";
  const substantiveArchetypes = new Set(["substantive_repeated_pattern", "selective_or_conditional_pattern", "policy_mechanism_divide"]);
  const sourceCount = Number(report.source_episode_count || experience.episodes.length);
  const clusteredCount = Number(report.policy_cluster_count || 0);
  const namedCount = Number(report.individually_named_episode_count || 0);
  const represented = asArray(model.evidence_episode_ids).length;

  if (sourceCount > 2 && clusteredCount === 0 && represented >= sourceCount - 1) {
    add("CONCLUSION-UTILITY-001", { fieldPath: "synthesis.conclusionModel", explanation: "The primary conclusion represents most episodes individually instead of through policy clusters." });
  }
  if (substantiveArchetypes.has(model.archetype) && model.thesis_proposition?.policy_dimension_present !== true) {
    add("CONCLUSION-UTILITY-002", { fieldPath: "synthesis.conclusionModel.thesis_proposition", explanation: "The substantive thesis has no basis beyond the action direction." });
    add("CONCLUSION-UTILITY-003", { fieldPath: "synthesis.conclusionModel.supporting_policy_clusters", explanation: "The selected archetype lacks a source-grounded policy dimension." });
  }
  if (model.archetype === "uniform_direction_without_common_policy_throughline" && !model.contrast_proposition) {
    add("CONCLUSION-UTILITY-004", { fieldPath: "synthesis.conclusionModel.contrast_proposition", explanation: "The no-common-throughline result lacks the required concrete contrast between supported policy clusters." });
  }
  if (asArray(report.duplicated_analytical_propositions).length) {
    add("CONCLUSION-UTILITY-005", { fieldPath: "synthesis.compressionReport.duplicated_analytical_propositions", explanation: "The primary conclusion duplicates detailed analytical propositions without additional synthesis." });
  }
  if (/(?:consistent|repeated|uniform) (?:support|opposition).{0,80}(?:because|shown by).{0,40}(?:supported|opposed|yea|nay)|(?:opposition|support) across (?:different|multiple) (?:mechanisms|proposals)/i.test(primary)) {
    add("CONCLUSION-UTILITY-006", { fieldPath: "synthesis.primary", explanation: "The conclusion restates action direction as its own policy explanation." });
  }
  if (/(?:coherent|overarching|consistent|comprehensive).{0,50}(?:philosophy|ideology|orientation|stance)/i.test(primary)
    && !/(?:does not|do not|cannot|not enough to|without)/i.test(primary)) {
    add("CONCLUSION-UTILITY-007", { fieldPath: "synthesis.primary", explanation: "The conclusion makes a broad philosophy claim without the required substantive evidence threshold." });
  }
  const qualificationWords = (primary.match(/\b(?:but|however|although|does not|do not|cannot|not enough|limited|caveat)\b/gi) || []).length;
  if (qualificationWords >= 4 || Number(report.boundary_count || 0) > 2) {
    add("CONCLUSION-UTILITY-008", { fieldPath: "synthesis.primary", explanation: "Qualification occupies more of the conclusion than the bounded substantive result." });
  }
  if (sourceCount > 2 && clusteredCount > 0 && namedCount > 2) {
    add("CONCLUSION-UTILITY-009", { fieldPath: "synthesis.compressionReport.individually_named_episode_count", explanation: "More than two episodes are individually named despite valid policy clusters." });
  }
  const actualLabel = candidate.synthesis?.conclusionModel
    ? candidate.synthesis?.readerFacingLabel || inference.reader_facing_label
    : null;
  if (actualLabel && model.reader_label_concept && actualLabel !== model.reader_label_concept) {
    add("CONCLUSION-UTILITY-010", { fieldPath: "synthesis.readerFacingLabel", explanation: "The reader label does not match the proposition model's archetype concept." });
  }
}

function validatePublicSurface(candidate, experience, renderedText, genericIssueCards, add) {
  const publicText = renderedText || candidate.validationRenderedText || "";
  if (FORBIDDEN_PUBLIC.test(publicText)) add("PUBLIC-001", { fieldPath: "renderedText", explanation: "Internal workflow or methodology language is exposed publicly." });
  if (genericIssueCards.includes(candidate.identity.issueId)) add("PUBLIC-002", { fieldPath: "genericIssueCards", explanation: "The active rich issue is repeated as a weaker generic card." });
  if (experience.featuredEpisodes.length > 5 || candidate.episodePresentation?.featuredEpisodeIds?.length > 5) add("PUBLIC-003", { fieldPath: "featuredEpisodes", explanation: "More than five episodes are featured by default." });
  if (hasRawIsoDateRange(publicText) || experience.featuredEpisodes.some((episode) => hasRawIsoDateRange(episode.dateSpan))) add("PUBLIC-004", { fieldPath: "dateSpan", explanation: "A raw ISO date range is exposed publicly." });
  const dc = experience.episodes.find((episode) => episode.id === "dc-policing-reform-repeal");
  if (dc && (!/proposal to repeal most provisions of D\.C\.'s 2022 policing reform law/i.test(dc.sharedQuestion || "") || /repeal (?:all|the entirety) of/i.test(JSON.stringify(dc)))) {
    add("PUBLIC-005", { episodeId: dc.id, fieldPath: "sharedQuestion", explanation: "The D.C. action is not bounded to the proposal to repeal most provisions." });
  }
}

function validateServiceChecks(checks, add) {
  for (const check of checks) {
    if ([MEMBER_ACTION_STATUS.notYetServing, MEMBER_ACTION_STATUS.noLongerServing].includes(check.classifiedStatus)
      && (check.serviceDatePrecision !== "day" || !check.exactEligibilityEstablished)) {
      add("SERVICE-001", { actionId: check.actionId, fieldPath: "serviceChecks", explanation: "Year-only or ambiguous service metadata was presented as exact eligibility." });
    }
  }
}

function requireValue(value, ruleId, fieldPath, context, add) {
  if (value || REASON_CODES.has(value?.state) || REASON_CODES.has(value)) return;
  add(ruleId, { ...context, fieldPath, explanation: `${fieldPath} is missing without a supported reason code.` });
}

function isOfficialVoteSource(source) {
  return /clerk\.house\.gov/i.test(source?.url || "") && /roll|vote/i.test(`${source?.name || ""} ${source?.locator || ""}`);
}

function isOfficialMeasureSource(source) {
  return /(?:congress\.gov|govinfo\.gov)/i.test(source?.url || "") && !/congressional-record/i.test(source?.url || "");
}

function isPermittedUrl(url) {
  return /^https:\/\/(?:www\.)?(?:clerk\.house\.gov|congress\.gov|govinfo\.gov|cbo\.gov)\//i.test(String(url || ""));
}

function stableSharedFacts(value) {
  return JSON.stringify(value, (key, item) => ["memberAction", "member_action", "actionStatus", "action_status", "headline", "actionAndResult", "member_action_and_result"].includes(key) ? undefined : item);
}

function normalizeText(value) {
  return String(value || "").toLowerCase().replace(/\b(?:the|a|an)\b/g, " ").replace(/[^a-z0-9]+/g, " ").replace(/\s+/g, " ").trim();
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function rule(id, severity, description) {
  return Object.freeze({ id, severity, description });
}

function finding(ruleId, context, details) {
  const contract = RULE_BY_ID.get(ruleId);
  return Object.freeze({
    ruleId,
    severity: contract.severity,
    sliceId: context.sliceId,
    memberId: context.memberId || null,
    issue: context.issue || null,
    episodeId: details.episodeId || null,
    actionId: details.actionId || null,
    roll: details.roll || null,
    fieldPath: details.fieldPath || null,
    explanation: details.explanation || contract.description,
    suggestedRemediation: details.suggestedRemediation || contract.description,
    publicationEligibilityMustFail: contract.severity === "block",
  });
}
