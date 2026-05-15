"use client";

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

const STANCE_OPTIONS = [
  {
    value: "support_more_action",
    label: "Support more action",
  },
  {
    value: "oppose_more_action",
    label: "Oppose more action",
  },
  {
    value: "show_record",
    label: "Just show record",
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

export default function IssuePreferencePanel({ preferences, onChange }) {
  const selectedCount = Object.keys(preferences).length;

  function toggleIssue(domain) {
    if (preferences[domain]) {
      const next = { ...preferences };
      delete next[domain];
      onChange(next);
      return;
    }

    onChange({
      ...preferences,
      [domain]: "show_record",
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
      nextPreferences[domain] = preferences[domain] || "show_record";
    });
    onChange(nextPreferences);
  }

  function clearPreferences() {
    onChange({});
  }

  return (
    <section className="mt-8 rounded-[2rem] border border-stone-200 bg-white px-5 py-5 shadow-[0_16px_40px_rgba(15,23,42,0.08)] lg:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-800">
            Your Issues
          </p>
          <h3 className="mt-2 max-w-[760px] font-serif text-[2rem] leading-[1] text-stone-950 sm:text-[2.65rem] sm:leading-[0.96]">
            Pick what you want this record checked against.
          </h3>
          <p className="mt-3 max-w-2xl text-[15px] leading-7 text-stone-700">
            Your picks only guide which records appear first. They do not change the vote record.
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

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {STARTER_CHECKS.map((starterCheck) => (
          <button
            className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4 text-left transition hover:border-cyan-700/50 hover:bg-cyan-50"
            key={starterCheck.id}
            onClick={() => applyStarterCheck(starterCheck)}
            type="button"
          >
            <span className="text-xs uppercase tracking-[0.24em] text-cyan-800">
              Starter Check
            </span>
            <span className="mt-2 block text-[18px] leading-6 text-stone-950">
              {starterCheck.label}
            </span>
            <span className="mt-2 block text-sm leading-6 text-stone-600">
              {starterCheck.description}
            </span>
          </button>
        ))}
      </div>

      <details className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4" open={selectedCount === 0}>
        <summary className="cursor-pointer text-sm font-medium text-stone-900">
          Fine-tune individual issue domains
        </summary>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {ISSUE_OPTIONS.map((issue) => {
            const selectedStance = preferences[issue.domain];
            const isSelected = Boolean(selectedStance);

            return (
              <article
                className={`rounded-[1.25rem] border px-4 py-4 transition ${
                  isSelected
                    ? "border-cyan-800 bg-cyan-50"
                    : "border-stone-200 bg-white"
                }`}
                key={issue.domain}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-[17px] leading-6 text-stone-950">{issue.label}</h4>
                    <p className="mt-2 text-sm leading-6 text-stone-600">{issue.prompt}</p>
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
                  <div className="mt-4 grid gap-2">
                    {STANCE_OPTIONS.map((stance) => (
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

      <div className="mt-4 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-4 py-4 text-sm leading-6 text-stone-700">
        {selectedCount === 0
          ? "No issues selected yet. Pick one or more topics to add a record check below the ZIP lookup."
          : `${selectedCount} issue ${selectedCount === 1 ? "selection is" : "selections are"} active for the alignment and comparison sections on this page.`}
      </div>
    </section>
  );
}
