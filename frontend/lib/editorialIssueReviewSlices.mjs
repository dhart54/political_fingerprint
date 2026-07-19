import { valerieFousheeEconomyEditorialGold } from "./valerieFousheeEconomyEditorialGold.mjs";
import { valerieFousheeJusticePublicSafetyEditorialGold } from "./valerieFousheeJusticePublicSafetyEditorialGold.mjs";

export const reviewEditorialIssueSlices = Object.freeze([
  Object.freeze({
    source: valerieFousheeEconomyEditorialGold,
    identity: Object.freeze({
      memberId: "F000477",
      memberDisplayName: "Valerie P. Foushee",
      issueId: "ECONOMY_TAXES",
      issueDisplayName: "Economy & Taxes",
      congress: 119,
      reviewedPeriod: "119th Congress",
    }),
    publication: Object.freeze({
      editorialStatus: "human_approval_pending",
      benchmarkStatus: "not_promoted",
      productionEligible: false,
      reviewLabel: "Editorial review preview \u2014 not published",
    }),
    synthesis: Object.freeze({
      primary:
        "In this sample, Foushee voted against specific proposals involving government funding, frameworks for later tax-and-spending legislation, military construction and veterans programs, and SBA loan eligibility. The six substantive votes represent four policy episodes. They reveal several specific voting patterns, but this sample is not yet broad enough to establish one overarching Economy & Taxes philosophy.",
      patterns: Object.freeze([
        "Opposed both stages of the 2025 government-funding episode.",
        "Opposed both stages of the FY2025\u2013FY2034 budget-framework episode.",
        "Opposed the House military-construction and veterans funding proposal.",
        "Opposed immigration-status restrictions on SBA-backed business loans.",
      ]),
      votingContext:
        "Foushee voted with the majority of House Democrats on all 6 substantive roll calls in this sample, covering 4 policy episodes.",
      votingContextBoundary:
        "Party alignment describes how these votes compared with other Democrats. It does not explain why Foushee voted that way, and repeated stages are not separate policy positions.",
      howToRead:
        "These votes concern several different funding, budget-process, veterans, and small-business policy choices. A recorded No establishes opposition to the proposal at that stage. Repeated votes across independent policy episodes may support broader voting themes, but one vote does not reveal motive or establish a position on every provision in a package.",
      evidenceBreadth: "Bounded voting pattern",
    }),
  }),
  Object.freeze({
    source: valerieFousheeJusticePublicSafetyEditorialGold,
    identity: Object.freeze({
      memberId: "F000477",
      memberDisplayName: "Valerie P. Foushee",
      issueId: "JUSTICE_PUBLIC_SAFETY",
      issueDisplayName: "Justice & Public Safety",
      congress: 119,
      reviewedPeriod: "119th Congress",
    }),
    publication: Object.freeze({
      editorialStatus: "human_approval_pending",
      benchmarkStatus: "not_promoted",
      productionEligible: false,
      reviewLabel: "Editorial review preview — not published",
    }),
    synthesis: Object.freeze({
      primary: "In this reviewed sample, Foushee took a mixed approach across five Justice & Public Safety policy episodes. She supported delaying an earlier fentanyl bill pending agency certification, opposed that House version, and later supported a related Senate bill that became law. She supported a bipartisan officer-safety reporting bill and opposed proposals for retired federal officers to buy agency firearms, to replace D.C. pursuit restrictions, and to repeal most of a broader D.C. policing reform law. These seven substantive votes show bounded choices across distinct mechanisms, not one overarching Justice philosophy.",
      patterns: Object.freeze([
        "Took mixed actions across three related fentanyl votes in one policy episode.",
        "Supported officer-safety reporting and opposed a service-weapon purchase program.",
        "Opposed both reviewed House bills changing D.C.-enacted policing rules.",
      ]),
      votingContext: "Foushee voted with the majority of House Democrats on all 7 substantive roll calls in this sample, covering 5 policy episodes.",
      votingContextBoundary: "Party alignment is descriptive, not an explanation. Democratic splits on the two fentanyl passage votes were close, and repeated stages are not separate policy positions.",
      howToRead: "These votes concern distinct enforcement, research, officer-safety, firearm-transfer, local-governance, and policing-rule choices. A recorded vote establishes the action at that stage, not motive or a view on every provision.",
      evidenceBreadth: "Mixed but interpretable bounded pattern",
    }),
  }),
]);
