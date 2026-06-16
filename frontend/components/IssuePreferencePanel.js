"use client";

import {
  GUIDED_PREFERENCE_OPTIONS,
  buildConcretePreferencePrompt,
} from "../lib/profileNarrative.mjs";

const ISSUE_OPTIONS = [
  {
    domain: "ECONOMY_TAXES",
    label: "Economy & Taxes",
    prompt: "Taxes, budgets, business, trade, and household costs",
  },
  {
    domain: "HEALTH_SOCIAL",
    label: "Health & Social Services",
    prompt: "Health care, public health, benefits, and community services",
  },
  {
    domain: "EDUCATION_WORKFORCE",
    label: "Education & Workforce",
    prompt: "Schools, job training, workers, and student support",
  },
  {
    domain: "ENVIRONMENT_ENERGY",
    label: "Environment & Energy",
    prompt: "Energy, climate, conservation, and land use",
  },
  {
    domain: "NATIONAL_SECURITY_FOREIGN",
    label: "National Security & Foreign Policy",
    prompt: "Defense, alliances, foreign aid, and global security",
  },
  {
    domain: "IMMIGRATION_BORDER",
    label: "Immigration & Border Policy",
    prompt: "Border operations, asylum, visas, and immigration systems",
  },
  {
    domain: "JUSTICE_PUBLIC_SAFETY",
    label: "Justice & Public Safety",
    prompt: "Courts, law enforcement, crime, and public safety",
  },
  {
    domain: "INFRASTRUCTURE_TECH_TRANSPORT",
    label: "Infrastructure, Tech & Transportation",
    prompt: "Roads, bridges, broadband, transit, and technology",
  },
];

const STARTER_CHECKS = [
  {
    id: "costs",
    label: "Cost of Living",
    description: "Taxes, services, infrastructure, and household-cost votes",
    domains: ["ECONOMY_TAXES", "HEALTH_SOCIAL", "INFRASTRUCTURE_TECH_TRANSPORT"],
  },
  {
    id: "community",
    label: "Community Safety",
    description: "Courts, public safety, immigration systems, and local capacity",
    domains: ["JUSTICE_PUBLIC_SAFETY", "IMMIGRATION_BORDER", "INFRASTRUCTURE_TECH_TRANSPORT"],
  },
  {
    id: "future",
    label: "Future Investment",
    description: "Schools, workforce, energy, technology, and transportation",
    domains: ["EDUCATION_WORKFORCE", "ENVIRONMENT_ENERGY", "INFRASTRUCTURE_TECH_TRANSPORT"],
  },
];

export default function IssuePreferencePanel({ positionRows = [], preferences, onChange }) {
  const selectedCount = Object.keys(preferences).length;
  const positionByDomain = new Map((positionRows || []).map((row) => [row.domain, row]));

  function toggleIssue(domain) {
    if (preferences[domain]) {
      const next = { ...preferences };
      delete next[domain];
      onChange(next);
      return;
    }

    onChange({
      ...preferences,
      [domain]: "not_sure",
    });
  }

  function setStance(domain, stance) {
    onChange({
      ...preferences,
      [domain]: stance,
    });
  }

  function applyStarterCheck(starterCheck) {
    const nextPreferences = { ...preferences };
    starterCheck.domains.forEach((domain) => {
      nextPreferences[domain] = preferences[domain] || "not_sure";
    });
    onChange(nextPreferences);
  }

  function clearPreferences() {
    onChange({});
  }

  return (
    <section className="mt-5 rounded-2xl border border-stone-200 bg-white px-4 py-4 shadow-[0_10px_28px_rgba(15,23,42,0.06)] lg:px-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-cyan-800">
            Your Issues
          </p>
          <h3 className="mt-1 max-w-[760px] font-serif text-[1.55rem] leading-[1.05] text-stone-950 sm:text-[2rem]">
            Compare the record to concrete choices.
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-700">
            Pick an issue, then say how you generally read the reviewed measures. Alignment appears only for a concrete for-or-against choice.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="rounded-full border border-cyan-900/10 bg-cyan-50 px-4 py-2 text-xs uppercase tracking-[0.22em] text-cyan-900">
            {selectedCount} selected
          </div>
          {selectedCount > 0 ? (
            <button
              className="rounded-full border border-stone-300 bg-white px-4 py-2 text-xs uppercase tracking-[0.18em] text-stone-700"
              onClick={clearPreferences}
              type="button"
            >
              Clear
            </button>
          ) : null}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {STARTER_CHECKS.map((starterCheck) => {
          const isActive = starterCheck.domains.every((domain) => preferences[domain]);

          return (
            <button
              aria-pressed={isActive}
              className={`rounded-full border px-3 py-2 text-left text-sm transition focus:outline-none focus:ring-2 focus:ring-cyan-800 focus:ring-offset-2 ${
                isActive
                  ? "border-cyan-800 bg-cyan-900 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.18)]"
                  : "border-stone-200 bg-stone-50 text-stone-800 hover:border-cyan-700/50 hover:bg-cyan-50"
              }`}
              key={starterCheck.id}
              onClick={() => applyStarterCheck(starterCheck)}
              type="button"
              title={starterCheck.description}
            >
              {starterCheck.label}
            </button>
          );
        })}
      </div>

      <details className="mt-4 rounded-xl border border-stone-200 bg-stone-50 px-3 py-3" open>
        <summary className="cursor-pointer text-sm font-medium text-stone-900">
          Fine-tune individual issue domains
        </summary>
        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
          {ISSUE_OPTIONS.map((issue) => {
            const selectedStance = preferences[issue.domain];
            const isSelected = Boolean(selectedStance);
            const prompt = buildConcretePreferencePrompt(positionByDomain.get(issue.domain));

            return (
              <article
                className={`rounded-xl border px-3 py-3 transition ${
                  isSelected
                    ? "border-cyan-800 bg-cyan-50"
                    : "border-stone-200 bg-white"
                }`}
                key={issue.domain}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-medium leading-5 text-stone-950">{issue.label}</h4>
                    <p className="mt-1 text-xs leading-5 text-stone-600">
                      {prompt.canAsk ? prompt.prompt : issue.prompt}
                    </p>
                  </div>
                  <button
                    className={`h-9 min-w-9 rounded-full border px-3 text-sm ${
                      isSelected
                        ? "border-cyan-800 bg-cyan-900 text-white"
                        : "border-stone-300 bg-white text-stone-700"
                    }`}
                    onClick={() => toggleIssue(issue.domain)}
                    type="button"
                    aria-label={isSelected ? `Remove ${issue.label}` : `Select ${issue.label}`}
                  >
                    {isSelected ? "x" : "+"}
                  </button>
                </div>

                {isSelected ? (
                  <div className="mt-3 grid gap-2">
                    {prompt.canAsk ? (
                      <p className="rounded-lg border border-cyan-900/10 bg-white px-3 py-2 text-xs leading-5 text-stone-700">
                        Choose the option closest to your view of these reviewed measures. If your view differs by measure, inspect the evidence instead of forcing one label.
                      </p>
                    ) : (
                      <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-stone-700">
                        Not enough reviewed Yes/No vote meaning is available for a safe alignment prompt yet.
                      </p>
                    )}
                    {GUIDED_PREFERENCE_OPTIONS.map((stance) => (
                      <button
                        className={`rounded-full px-3 py-2 text-left text-xs uppercase tracking-[0.16em] ${
                          selectedStance === stance.value
                            ? "bg-cyan-900 text-white"
                            : "bg-white text-stone-700"
                        }`}
                        aria-pressed={selectedStance === stance.value}
                        key={stance.value}
                        onClick={() => setStance(issue.domain, stance.value)}
                        type="button"
                      >
                        {stance.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      </details>

      <div className="mt-3 rounded-xl border border-stone-200 bg-stone-50 px-3 py-2 text-sm leading-5 text-stone-700">
        {selectedCount === 0
          ? "No issue choices yet. Pick a concrete prompt when you want a personalized alignment check."
          : `${selectedCount} issue ${selectedCount === 1 ? "choice is" : "choices are"} active. Not sure and views-differ choices do not create alignment labels.`}
      </div>
    </section>
  );
}
