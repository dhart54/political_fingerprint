const PUBLIC_THEME_BY_FACET = {
  budget_reconciliation_and_debt_limit: "budget framework and reconciliation",
  small_business_loan_eligibility: "small-business loan eligibility",
  military_construction_and_va_appropriations: "military and veterans appropriations",
  temporary_government_funding: "temporary government funding",
  government_funding_and_shutdown: "shutdown-ending government funding",
  small_business_regulation: "small-business regulatory-cost limits",
  appropriations_amendment: "appropriations amendments",
  conference_instruction: "conference instructions",
  fentanyl_scheduling_and_penalties: "fentanyl scheduling and penalty thresholds",
  federal_law_enforcement_equipment: "federal law-enforcement retired weapon purchasing",
  law_enforcement_safety_reporting: "law-enforcement safety and wellness reporting",
  dc_police_pursuit_policy: "D.C. police pursuit policy",
  dc_policing_reform_repeal: "D.C. policing reform repeal",
  "Defense authorization": "defense authorization legislation",
  defense_authorization: "defense authorization legislation",
  "Defense authorization amendment": "defense authorization amendments",
  defense_authorization_amendment: "defense authorization amendments",
  "House floor procedure": "procedural House floor action",
  house_of_representatives: "procedural House rule or motion",
  "Motion to commit": "other reviewed national-security measures",
  motion_to_commit: "other reviewed national-security measures",
  "Veterans cemetery administration": "veterans cemetery administration",
  veterans_cemetery_administration: "veterans cemetery administration",
  foreign_military_sales: "foreign military sales",
  floor_rule_for_multiple_bills: "procedural floor rules for multiple bills",
  floor_rule_for_energy_and_budget_measures: "procedural floor rules for energy and budget measures",
  floor_procedure_on_hydrogen_vehicle_rule: "procedural floor action on hydrogen vehicle rules",
  federal_employee_collective_bargaining: "federal employee collective-bargaining rules",
  school_foreign_funding_and_contract_restrictions: "school foreign-funding and contract restrictions",
  school_foreign_influence_parent_notifications: "school foreign-influence parent notifications",
  natural_gas_pipeline_and_lng_review_coordination: "natural gas pipeline and LNG review coordination",
  health_insurance_premiums: "health insurance premium assistance",
  health_insurance_premium_assistance: "health insurance premium assistance",
  medicaid_payment_rules_for_minor_health_procedures: "Medicaid payment rules for specified minor health procedures",
  medicaid_payment_rules: "Medicaid payment rules for specified minor health procedures",
  china_related_security_restrictions: "China-related security restrictions",
  iran_related_security_measures: "Iran-related security measures",
  war_powers_votes: "war-powers votes",
};

const PUBLIC_THEME_BY_DOMAIN = {
  ECONOMY_TAXES: "other reviewed fiscal measures",
  HEALTH_SOCIAL: "other reviewed health and social-service measures",
  EDUCATION_WORKFORCE: "other reviewed education and workforce measures",
  ENVIRONMENT_ENERGY: "other reviewed environment and energy measures",
  NATIONAL_SECURITY_FOREIGN: "other reviewed national-security measures",
  IMMIGRATION_BORDER: "other reviewed immigration and border measures",
  JUSTICE_PUBLIC_SAFETY: "other reviewed public-safety measures",
  INFRASTRUCTURE_TECH_TRANSPORT: "other reviewed infrastructure and technology measures",
};

const UNSAFE_PUBLIC_THEME_MARKERS = [
  "this was a direct vote",
  "this vote is useful",
  "the vote is useful",
  "records a direct position",
  "recorded a direct position",
  "the house voted on whether",
  "the senate voted on whether",
  "whether to agree to",
  "whether that amendment would",
  "part a amendment",
  "part b amendment",
  "amendment no.",
  "the amendment redirects",
  "the amendment decreases",
  "the amendment increases",
  "official roll call",
  "roll-call description",
  "classification",
  "source basis",
];

const MAX_UNCURATED_THEME_WORDS = 8;
const MAX_UNCURATED_THEME_LENGTH = 72;

export function getPublicThemeForFacet(facet, { domain = "", curatedTheme = "" } = {}) {
  const exactFacet = String(facet || "").trim();
  const normalizedFacet = normalizeThemeKey(exactFacet);
  const explicitTheme = PUBLIC_THEME_BY_FACET[exactFacet] || PUBLIC_THEME_BY_FACET[normalizedFacet] || "";

  if (explicitTheme && isSafePublicThemePhrase(explicitTheme, { curated: true })) {
    return explicitTheme;
  }

  const approvedTheme = formatSafePublicThemePhrase(curatedTheme, { curated: true });
  if (approvedTheme) {
    return approvedTheme;
  }

  const keywordTheme = getKeywordPublicTheme(normalizedFacet);
  if (keywordTheme) {
    return keywordTheme;
  }

  const shortFacetLabel = formatSafePublicThemePhrase(formatFacetLabel(exactFacet), { curated: false });
  if (shortFacetLabel) {
    return shortFacetLabel;
  }

  return getPublicThemeFallback(domain);
}

export function getPublicThemeFallback(domain) {
  return PUBLIC_THEME_BY_DOMAIN[String(domain || "").trim()] || "other reviewed policy measures";
}

export function formatSafePublicThemePhrase(phrase, { curated = false } = {}) {
  const cleaned = cleanThemePhrase(phrase);
  return isSafePublicThemePhrase(cleaned, { curated }) ? cleaned : "";
}

export function isSafePublicThemePhrase(phrase, { curated = false } = {}) {
  const cleaned = cleanThemePhrase(phrase);
  if (!cleaned) {
    return false;
  }

  const lower = cleaned.toLowerCase();
  if (UNSAFE_PUBLIC_THEME_MARKERS.some((marker) => lower.includes(marker))) {
    return false;
  }

  if (!curated) {
    const wordCount = cleaned.split(/\s+/).filter(Boolean).length;
    if (wordCount > MAX_UNCURATED_THEME_WORDS || cleaned.length > MAX_UNCURATED_THEME_LENGTH) {
      return false;
    }
    if (/[.!?]/.test(cleaned.replace(/\bD\.C\./g, "DC"))) {
      return false;
    }
    if (/\b(act|resolution|amendment no|roll call|roll-call)\b/i.test(cleaned)) {
      return false;
    }
    if (/^(this|the house|the senate|the vote|a vote)\b/i.test(cleaned)) {
      return false;
    }
  }

  return true;
}

function getKeywordPublicTheme(normalizedFacet) {
  const tokens = normalizedFacet.split("_").filter(Boolean);
  if (tokens.includes("china")) {
    return "China-related security restrictions";
  }
  if (tokens.includes("iran")) {
    return "Iran-related security measures";
  }
  if (tokens.includes("war") && (tokens.includes("power") || tokens.includes("powers"))) {
    return "war-powers votes";
  }
  return "";
}

function formatFacetLabel(value) {
  return String(value || "")
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
}

function normalizeThemeKey(value) {
  return String(value || "")
    .trim()
    .replace(/([a-z])([A-Z])/g, "$1_$2")
    .replace(/[\s-]+/g, "_")
    .toLowerCase();
}

function cleanThemePhrase(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .replace(/\.$/, "")
    .trim();
}
