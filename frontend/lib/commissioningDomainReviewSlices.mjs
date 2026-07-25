import {
  commissioningDomainCorrectedReviewData as commissioningDomainReviewData,
} from "./commissioningDomainCorrectedReviewData.mjs";

const sourceById = new Map(commissioningDomainReviewData.sources.map((source) => [source.source_id, source]));
const actionByRoll = new Map(commissioningDomainReviewData.actions.map((action) => [Number(action.roll), action]));
const inferenceByMember = new Map(commissioningDomainReviewData.inferences.map((item) => [item.member.bioguide_id, item]));

export const commissioningDomainReviewSlices = Object.freeze(
  commissioningDomainReviewData.overlays.map((overlay) => buildReviewCandidate({
    overlay,
    inference: inferenceByMember.get(overlay.member.bioguide_id),
  })),
);

export const commissioningDomainSharedReviewText = Object.freeze(
  (commissioningDomainReviewData.sharedReviewDependencies || []).map((item) => item.summary),
);

export const commissioningDomainRenderProfiles = Object.freeze(
  commissioningDomainReviewData.renderFixtures.fixtures.map((fixture) => {
    const overlay = commissioningDomainReviewData.overlays.find(
      (item) => item.member.bioguide_id === fixture.member_id,
    );
    return Object.freeze({
      memberId: fixture.member_id,
      label: fixture.case,
      candidate: commissioningDomainReviewSlices.find(
        (item) => item.identity.memberId === fixture.member_id,
      ),
      legislator: buildLegislator(overlay.member),
      fixtureData: buildFixtureData(overlay),
    });
  }),
);

export function buildReviewCandidate({ overlay, inference }) {
  const actionRows = new Map(overlay.roll_actions.map((item) => [Number(item.roll), item]));
  const interpretations = commissioningDomainReviewData.actions.map((action) => (
    interpretation(action, actionRows.get(Number(action.roll)), overlay.member)
  ));
  const source = Object.freeze({
    member: Object.freeze({
      bioguide_id: overlay.member.bioguide_id,
      name: overlay.member.display_name,
    }),
    domain: commissioningDomainReviewData.issue,
    human_approval_status: "human_approval_pending",
    slice_counts: Object.freeze({
      substantive_rolls: overlay.coverage.substantive_rolls_expected,
      policy_episodes: overlay.coverage.independent_episodes_expected,
      not_voting_records: overlay.coverage.not_voting_actions,
      context_controls: 0,
    }),
    interpretations: Object.freeze(interpretations),
    controls: Object.freeze([]),
    inference_candidate: inference,
  });
  return Object.freeze({
    source,
    identity: Object.freeze({
      memberId: overlay.member.bioguide_id,
      memberDisplayName: overlay.member.display_name,
      issueId: commissioningDomainReviewData.issue,
      issueDisplayName: "Environment & Energy",
      congress: 119,
      reviewedPeriod: "January–March 2026",
    }),
    episodePresentation: episodePresentation(),
    memberEpisodeTrajectories: Object.freeze(overlay.episode_trajectories),
    publication: Object.freeze({
      editorialStatus: "human_approval_pending",
      benchmarkStatus: "not_promoted",
      productionEligible: false,
      reviewLabel: "Commissioning-domain review candidate — not published",
    }),
    synthesis: Object.freeze({
      primary: inference.primary_conclusion,
      evidenceBreadth: inference.evidence_strength_label,
      readerFacingLabel: inference.reader_facing_label,
      coverageNote: inference.coverage_note,
      methodNote: inference.method_note,
      patterns: Object.freeze(
        Object.values(inference.analytical_sections || {})
          .flat()
          .map((item) => item.exact_rendered_text),
      ),
      analyticalSections: Object.freeze({
        repeatedPatterns: ownedSection(inference, "repeated_patterns"),
        policyTrajectories: ownedSection(inference, "policy_trajectories"),
        otherNotableChoices: ownedSection(inference, "other_notable_choices"),
        meaningfulExceptions: ownedSection(inference, "meaningful_exceptions"),
      }),
      conclusionModel: inference.conclusion_model,
      compressionReport: inference.compression_report,
      reviewRoute: inference.review_route,
    }),
  });
}

function interpretation(action, actionRow, member) {
  const dossier = action;
  const memberAction = actionRow?.action || "Missing Evidence";
  const episodeId = commissioningDomainReviewData.episodes.find(
    (episode) => episode.rolls.includes(Number(action.roll)),
  )?.episode_id;
  const sources = dossier.source_ids.map((sourceId) => presentSource(sourceById.get(sourceId)));
  return Object.freeze({
    congress: 119,
    roll: Number(action.roll),
    measure_id: dossier.measure,
    stage: dossier.exact_stage,
    episode_id: episodeId,
    member_action: memberAction,
    action_status: memberAction,
    presentation_labels: stagePresentationLabels(dossier),
    human_approval_status: "human_approval_pending",
    ten_second: Object.freeze({
      headline: headline(memberAction, dossier.action_title),
      practical_choice: dossier.proposed_change,
      member_action_and_result: `${shortName(member)} ${actionSentence(memberAction)}. ${outcomeSentence(dossier)}`,
    }),
    thirty_second: Object.freeze({
      prior_baseline: dossier.prior_baseline,
      mechanism: dossier.mechanism,
      affected: dossier.affected_entities.join(", "),
      scale_or_timing: `${dossier.scale}; ${dossier.timing}.`,
      what_happened_next: dossier.outcome,
    }),
    two_minute: Object.freeze({
      detail: null,
      supporter_argument: presentArgument(dossier.supporter_argument, "Committee majority"),
      opponent_argument: presentArgument(dossier.opponent_argument, "Committee minority or dissenting views"),
      argument_boundary: "Arguments are attributed official positions, not evidence of the member's motive.",
      one_sided_argument_note: argumentAbsence(dossier),
      later_history: null,
      caveats: Object.freeze([
        ...dossier.caveats,
        memberAction === "Not Voting"
          ? "Not Voting is neither support nor opposition, and the record does not reveal why the member did not vote."
          : "The vote record does not reveal why the member voted this way.",
      ]),
      sources: Object.freeze(sources),
    }),
  });
}

function episodePresentation() {
  return Object.freeze({
    featuredEpisodeIds: Object.freeze(
      commissioningDomainReviewData.episodes.map((episode) => episode.episode_id),
    ),
    episodes: Object.freeze(
      commissioningDomainReviewData.episodes.map((episode) => Object.freeze({
        id: episode.episode_id,
        congress: 119,
        rolls: Object.freeze([...episode.rolls]),
        title: humanize(episode.episode_id),
        practicalQuestion: episode.shared_objective,
        mechanismFamily: humanize(episode.mechanism_family),
        policyFamilyId: episode.policy_family_id || episode.episode_id,
        conclusionRelevance: null,
        selectionRationale: episode.why,
      })),
    ),
  });
}

function buildFixtureData(overlay) {
  const rows = overlay.roll_actions
    .filter((item) => item.action !== "Missing Evidence")
    .map((item) => evidenceRow(item, actionByRoll.get(Number(item.roll))));
  const yes = overlay.roll_actions.filter((item) => item.action === "Yea").length;
  const no = overlay.roll_actions.filter((item) => item.action === "Nay").length;
  return Object.freeze({
    positions: Object.freeze({
      scope_metadata: Object.freeze({
        congresses: Object.freeze([119]),
        requested_congresses: Object.freeze([119]),
        scope_label: "January–March 2026",
      }),
      positions: Object.freeze([Object.freeze({
        domain: commissioningDomainReviewData.issue,
        recorded_votes: rows.length,
        interpreted_support_count: yes,
        interpreted_oppose_count: no,
        interpreted_other_count: rows.length - yes - no,
        yea_share: yes + no ? yes / (yes + no) : 0,
        nay_share: yes + no ? no / (yes + no) : 0,
      })]),
    }),
    evidenceByDomain: Object.freeze({
      [commissioningDomainReviewData.issue]: Object.freeze({
        domain: commissioningDomainReviewData.issue,
        evidence: Object.freeze(rows),
      }),
    }),
  });
}

function evidenceRow(actionRow, action) {
  const position = {
    Yea: "yea",
    Nay: "nay",
    Present: "present",
    "Not Voting": "not_voting",
  }[actionRow.action];
  return Object.freeze({
    roll_call_id: `house:119:2:${action.roll}`,
    congress: 119,
    rollcall_number: Number(action.roll),
    vote_date: action.action_date,
    chamber: "house",
    description: action.action_title,
    question: action.exact_stage,
    issue_domain: commissioningDomainReviewData.issue,
    interpretation_status: "interpreted",
    position,
    support_position: "yea",
    oppose_position: "nay",
    vote_type: action.roll === 7 ? "final_passage" : "substantive",
    source_url: `https://clerk.house.gov/Votes/2026${action.roll}`,
    vote_context: Object.freeze({ final_result: action.outcome }),
  });
}

function presentSource(source) {
  const group = source.source_type === "house_clerk_roll_call"
    ? "Vote and legislative status"
    : source.source_type === "congress_gov_measure_text"
      ? "Bill or resolution text"
      : source.source_type === "house_committee_report"
        ? "Competing arguments"
        : "Nonpartisan analysis";
  return Object.freeze({
    stableId: source.source_id,
    name: source.name,
    locator: source.locator,
    group,
    url: source.url,
  });
}

function presentArgument(argument, attribution) {
  if (argument?.state !== "claim_supported") return undefined;
  return Object.freeze({ attribution, argument: argument.text });
}

function argumentAbsence(dossier) {
  const missing = ["supporter_argument", "opponent_argument"]
    .filter((field) => dossier[field]?.state === "supported_absence");
  if (!missing.length) return null;
  return "The official record did not support a bounded stage-specific argument for this package action.";
}

function headline(action, title) {
  const prefix = {
    Yea: "Supported",
    Nay: "Opposed",
    Present: "Voted Present on",
    "Not Voting": "Was not recorded on",
    "Missing Evidence": "Evidence unavailable for",
  }[action];
  return `${prefix}: ${title}`;
}

function actionSentence(action) {
  if (action === "Yea" || action === "Nay") return `voted ${action}`;
  if (action === "Present") return "voted Present";
  if (action === "Not Voting") return "was recorded as Not Voting";
  return "has no resolved evidence record for this action";
}

function ownedSection(inference, key) {
  return Object.freeze(
    (inference.analytical_sections?.[key] || []).map((item) => Object.freeze({
      semanticPropositionId: item.semantic_proposition_id,
      episodeId: item.evidence_episode_ids?.length === 1
        ? item.evidence_episode_ids[0]
        : undefined,
      episodeIds: Object.freeze([...(item.evidence_episode_ids || [])]),
      text: item.exact_rendered_text,
    })),
  );
}

function outcomeSentence(dossier) {
  const outcome = String(dossier.outcome || "").trim();
  const [houseResult, laterHistory] = outcome.split(";").map((item) => item.trim());
  const tally = houseResult.match(/(\d+)-(\d+)/);
  const tallyText = tally ? `, ${tally[1]}–${tally[2]}` : "";
  let first;
  if (/^retained/i.test(houseResult)) {
    first = `The House retained the divisions${tallyText}.`;
  } else {
    const object = /package/i.test(dossier.exact_stage || "") ? "package" : "bill";
    first = `The House passed the ${object}${tallyText}.`;
  }
  if (/later enacted as /i.test(laterHistory || "")) {
    return `${first} It was ${laterHistory.replace(/^later /i, "")}.`;
  }
  return first;
}

function stagePresentationLabels(dossier) {
  const stage = `${dossier.exact_stage || ""} ${dossier.mechanism || ""}`;
  if (!/(?:package|division|retain|appropriation)/i.test(stage)) return undefined;
  return Object.freeze({
    practicalChoice: "What this vote did",
    priorBaseline: "Stage before this vote",
    affected: "Programs and agencies covered",
    context: "Package boundary",
  });
}

function shortName(member) {
  return member.display_name;
}

function buildLegislator(member) {
  return Object.freeze({
    id: `leg_${member.bioguide_id.toLowerCase()}`,
    bioguide_id: member.bioguide_id,
    name_display: member.display_name,
    chamber: "house",
    state: member.state,
    district: "",
    party: member.party,
  });
}

function humanize(value) {
  return String(value || "")
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
