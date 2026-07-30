import { scopeLabel } from "../lib/frontendPassA.mjs";

const OPTIONS = ["all", "119", "118"];

export default function ScopeControl({ onChange, scope }) {
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
