export const economyEpisodePresentation = Object.freeze({
  featuredEpisodeIds: Object.freeze([
    "government_funding_hr5371",
    "budget_framework_hconres14",
    "milcon_va_hr3944",
    "sba_loan_eligibility_hr2966",
  ]),
  episodes: Object.freeze([
    episode({
      id: "government_funding_hr5371",
      familyId: "federal-government-funding",
      title: "Government funding in 2025",
      rolls: [281, 285],
      question: "How Congress would fund federal operations while the regular FY2026 spending bills remained unfinished.",
      relationship: "The House first considered a short-term extension. After a funding lapse, it later considered a broader Senate revision that reopened funded operations and enacted three full-year funding divisions.",
      changes: "The later package changed the temporary deadline and added full-year Agriculture, Legislative Branch, and Military Construction-VA funding.",
      relevance: "Repeated opposition across two materially different stages",
      selectionRationale: "The two-stage enacted funding path is necessary to understand the repeated pattern.",
    }),
    episode({
      id: "budget_framework_hconres14",
      familyId: "federal-budget-framework",
      title: "FY2025–FY2034 budget framework",
      rolls: [50, 100],
      question: "Whether Congress should set a ten-year budget framework and instructions for later tax-and-spending legislation.",
      relationship: "The House adopted an initial framework and later considered the Senate-revised framework. Neither action itself changed taxes, benefits, annual funding, or the debt limit.",
      changes: "The second action concerned revised committee instructions and parameters after the Senate changed the House framework.",
      relevance: "Repeated opposition across both framework stages",
      selectionRationale: "The paired stages are the second repeated episode supporting the conclusion.",
    }),
    episode({
      id: "milcon_va_hr3944",
      familyId: "military-construction-veterans-funding",
      title: "Military construction and veterans funding",
      rolls: [182],
      question: "Whether to pass the House proposal funding military construction, veterans programs, and related accounts.",
      relationship: "This was House passage of an intermediate package; later enacted funding differed.",
      relevance: "A significant one-off funding choice",
      selectionRationale: "A major one-off funding proposal broadens the record without being mislabeled as repetition.",
    }),
    episode({
      id: "sba_loan_eligibility_hr2966",
      familyId: "sba-loan-eligibility",
      title: "SBA-backed loan eligibility",
      rolls: [156],
      question: "Whether to add immigration-status documentation and eligibility restrictions to SBA 7(a) and 504 loans.",
      relationship: "This was one House-passage action on a distinct small-business lending mechanism.",
      relevance: "A significant one-off eligibility choice",
      selectionRationale: "The eligibility proposal is distinct from the two repeated funding and framework episodes.",
    }),
  ]),
});

export const justiceEpisodePresentation = Object.freeze({
  featuredEpisodeIds: Object.freeze([
    "halt-fentanyl-legislative-path",
    "officer-safety-data-reporting",
    "retired-service-weapon-purchases",
    "dc-police-pursuit-rules",
    "dc-policing-reform-repeal",
  ]),
  episodes: Object.freeze([
    episode({
      id: "halt-fentanyl-legislative-path",
      familyId: "fentanyl-scheduling-and-research",
      title: "Fentanyl scheduling and research framework",
      rolls: [32, 33, 166],
      question: "How Congress would make classwide fentanyl-related-substance scheduling permanent while addressing implementation and research.",
      relationship: "The House first considered a certification condition and the earlier H.R. 27, then later considered the related but different Senate framework that became law.",
      changes: "The first action would have conditioned implementation; the second passed the earlier House bill without that condition; the final action included the later permanent framework and research provisions.",
      relevance: "A three-action policy trajectory",
      selectionRationale: "The only multi-action Justice episode is load-bearing for both reviewed conclusions.",
    }),
    episode({
      id: "retired-service-weapon-purchases",
      familyId: "police-tools-and-equipment",
      title: "Retired federal service firearms",
      rolls: [130],
      question: "Whether eligible current and retired officers could buy qualifying retired agency-issued firearms through a federal program.",
      relationship: "One House-passage action concerning a defined purchase program, eligible officers, participating agencies, and excluded weapons.",
      relevance: "A police-tool proposal",
      selectionRationale: "This episode helps establish the police-tool side of the reviewed divide.",
    }),
    episode({
      id: "officer-safety-data-reporting",
      familyId: "officer-safety-information",
      title: "Officer safety and wellness reporting",
      rolls: [131],
      question: "Whether DOJ should report on attacks against officers, reporting-system feasibility, and officer wellness resources.",
      relationship: "One House-passage action centered on information gathering and reporting.",
      relevance: "A notable reporting choice",
      selectionRationale: "This choice is important but is not recast as an expansion of police tools or authority.",
    }),
    episode({
      id: "dc-police-pursuit-rules",
      familyId: "dc-police-operational-authority",
      title: "D.C. police pursuit authority",
      rolls: [275],
      question: "Whether to broaden when D.C. police could begin vehicle pursuits while retaining risk and effectiveness limits.",
      relationship: "One House-passage action on the substitute's pursuit standard and its retained exceptions.",
      relevance: "A police-authority proposal",
      selectionRationale: "This episode is one of the independent police-authority records supporting the divide.",
    }),
    episode({
      id: "dc-policing-reform-repeal",
      familyId: "dc-policing-rules-and-oversight",
      title: "D.C. policing-reform repeal",
      rolls: [299],
      question: "Whether to repeal most, but not every provision, of D.C.'s 2022 policing reform law.",
      relationship: "One House-passage action on a package affecting multiple local policing rules and safeguards.",
      relevance: "A policing-rules proposal",
      selectionRationale: "The episode materially contributes to the repeated police-authority and rollback record.",
    }),
  ]),
});

export const economyEpisodeByRoll = Object.freeze(Object.fromEntries(
  economyEpisodePresentation.episodes.flatMap((item) => item.rolls.map((roll) => [roll, item.id])),
));

function episode({ id, familyId, title, rolls, question, relationship, changes = "", relevance = "", selectionRationale }) {
  return Object.freeze({
    id,
    policyFamilyId: familyId,
    congress: 119,
    title,
    rolls: Object.freeze(rolls),
    sharedQuestion: question,
    relationship,
    materialDifferences: changes,
    conclusionRelevance: relevance,
    selectionRationale,
  });
}
