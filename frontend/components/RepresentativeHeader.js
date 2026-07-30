import { scopeLabel } from "../lib/frontendPassA.mjs";

export default function RepresentativeHeader({
  legislator,
  onSwitch,
  scope,
}) {
  return (
    <section className="border-b border-stone-200 py-5" aria-labelledby="representative-name">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Representative overview</p>
          <h1
            className="mt-2 font-serif text-4xl leading-none text-stone-950 sm:text-5xl"
            id="representative-name"
            tabIndex={-1}
          >
            {legislator.name_display}
          </h1>
          <p className="mt-3 text-base leading-6 text-stone-700">
            {formatChamber(legislator.chamber)} · {formatPlace(legislator)} · {formatParty(legislator.party)}
          </p>
          <p className="mt-1 text-sm text-stone-600">
            Scope: {scopeLabel(scope)}
          </p>
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
