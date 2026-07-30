const OPTIONS = [
  ["recommended", "Recommended"],
  ["most_evidence", "Most evidence"],
  ["reviewed_analysis", "Reviewed analysis"],
  ["a_z", "A–Z"],
];

const EXPLANATIONS = {
  recommended:
    "Reviewed public analysis appears first, followed by evidence usefulness and stable issue order.",
  most_evidence:
    "Orders by recorded actions, then substantive Yea/Nay receipts.",
  reviewed_analysis:
    "Shows only issues with a valid backend-supplied public analytical claim.",
  a_z: "Orders by the public issue name.",
};

export default function IssueDiscoveryControls({ mode, onChange }) {
  return (
    <div className="mt-5">
      <div
        aria-label="Issue discovery order"
        className="flex flex-wrap gap-2"
        role="group"
      >
        {OPTIONS.map(([value, label]) => (
          <button
            aria-pressed={mode === value}
            className={`filter-button ${mode === value ? "filter-button-selected" : ""}`}
            key={value}
            onClick={() => onChange(value)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      <p className="mt-3 text-sm leading-6 text-stone-600">
        {EXPLANATIONS[mode]}
      </p>
    </div>
  );
}
