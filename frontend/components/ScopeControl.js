import { scopeLabel } from "../lib/frontendPassA.mjs";

const OPTIONS = ["all", "119", "118"];

export default function ScopeControl({ onChange, scope, compact = false }) {
  if (compact) return <section className="flex flex-wrap items-center gap-3 py-4">
    <label htmlFor="compact-scope" className="text-sm font-semibold text-stone-700">Recorded votes</label>
    <select id="compact-scope" className="min-h-11 max-w-full rounded-lg border border-stone-300 bg-white px-3 text-sm text-stone-900" value={scope} onChange={(event) => onChange(event.target.value)}>
      {OPTIONS.map((value) => <option value={value} key={value}>{scopeLabel(value)}</option>)}
    </select>
  </section>;
  return (
    <section className="py-5" aria-labelledby="scope-control-heading">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-base font-semibold text-stone-950" id="scope-control-heading">
            Congress scope
          </h2>
          <p className="mt-1 text-sm leading-6 text-stone-600">
            This changes the recorded actions shown. It does not imply a completed methodological review.
          </p>
        </div>
        <div
          aria-label="Congress scope"
          className="grid grid-cols-1 gap-2 sm:grid-cols-3"
          role="group"
        >
          {OPTIONS.map((value) => (
            <button
              aria-pressed={scope === value}
              className={`scope-button ${scope === value ? "scope-button-selected" : ""}`}
              key={value}
              onClick={() => onChange(value)}
              type="button"
            >
              {scopeLabel(value)}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
