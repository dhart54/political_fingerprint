export const DOMAIN_LABELS = {
  ECONOMY_TAXES: "Economy & Taxes",
  EDUCATION_WORKFORCE: "Education & Workforce",
  ENVIRONMENT_ENERGY: "Environment & Energy",
  HEALTH_SOCIAL: "Health & Social Services",
  IMMIGRATION_BORDER: "Immigration & Border Policy",
  INFRASTRUCTURE_TECH_TRANSPORT: "Infrastructure, Tech & Transportation",
  JUSTICE_PUBLIC_SAFETY: "Justice & Public Safety",
  NATIONAL_SECURITY_FOREIGN: "National Security & Foreign Policy",
};

export function formatDomainLabel(domain) {
  const label = DOMAIN_LABELS[domain];
  if (label) {
    return label;
  }

  return String(domain || "")
    .split("_")
    .filter(Boolean)
    .map((segment) => segment[0] + segment.slice(1).toLowerCase())
    .join(" ");
}
