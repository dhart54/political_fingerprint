import { scopeLabel } from "../lib/frontendPassA.mjs";

export default function RepresentativeHeader({
  legislator,
  onSwitch,
  scope,
  compact = false,
}) {
  return (
    <section className={`border-b border-stone-200 ${compact ? "py-3" : "py-5"}`} aria-labelledby="representative-name">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          {!compact ? <p className="eyebrow">Representative overview</p> : null}
          <h1
            className={`font-serif leading-tight text-stone-950 ${compact ? "text-3xl sm:text-4xl" : "mt-2 text-4xl sm:text-5xl"}`}
            id="representative-name"
            tabIndex={-1}
          >
            {legislator.name_display}
          </h1>
          <p className={`${compact ? "mt-1" : "mt-3"} text-base leading-6 text-stone-700`}>
            {formatChamber(legislator.chamber)} · {formatPlace(legislator)} · {formatParty(legislator.party)}
          </p>
          {!compact ? <p className="mt-1 text-sm text-stone-600">
            Scope: {scopeLabel(scope)}
          </p> : null}
        </div>
        <button className="secondary-button" onClick={onSwitch} type="button">
          Switch representative
        </button>
      </div>
    </section>
  );
}

function formatChamber(chamber) {
  return chamber === "senate" ? "U.S. Senate" : "U.S. House";
}

function formatPlace(legislator) {
  return legislator.district
    ? `${legislator.state} district ${String(legislator.district).replace(/^0/, "")}`
    : `${legislator.state}, statewide`;
}

function formatParty(party) {
  return { D: "Democratic", R: "Republican", I: "Independent" }[party]
    || String(party || "Party not listed");
}
