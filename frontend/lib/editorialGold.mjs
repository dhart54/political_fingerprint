import { valerieFousheeEconomyEditorialGold } from "./valerieFousheeEconomyEditorialGold.mjs";


export function getApprovedEditorialSlice({ domain, evidenceRows = [], legislator = null }) {
  const bundle = valerieFousheeEconomyEditorialGold;
  if (legislator?.bioguide_id !== bundle.member.bioguide_id || domain !== bundle.domain) {
    return null;
  }

  const rowsByRoll = new Map(
    evidenceRows
      .filter((row) => Number(row.congress) === 119 && Number.isInteger(Number(row.rollcall_number)))
      .map((row) => [Number(row.rollcall_number), row]),
  );
  const interpretations = bundle.interpretations
    .filter((entry) => rowsByRoll.has(entry.roll))
    .map((entry) => ({ ...entry, row: rowsByRoll.get(entry.roll), kind: "interpretation" }));
  const controls = bundle.controls
    .filter((entry) => rowsByRoll.has(entry.roll))
    .map((entry) => ({ ...entry, row: rowsByRoll.get(entry.roll), kind: "control" }));

  if (!interpretations.length && !controls.length) {
    return null;
  }

  return {
    ...bundle,
    interpretations,
    controls,
    matchedRolls: new Set([...interpretations, ...controls].map((entry) => entry.roll)),
  };
}


export function isEditorialSliceRow(row, editorialSlice) {
  return Boolean(
    editorialSlice &&
      Number(row?.congress) === 119 &&
      editorialSlice.matchedRolls.has(Number(row?.rollcall_number)),
  );
}
