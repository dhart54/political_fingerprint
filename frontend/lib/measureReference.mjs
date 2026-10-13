const TYPE_LABELS = {
  hr: "H.R.", s: "S.", hres: "H.Res.", sres: "S.Res.",
  hjres: "H.J.Res.", sjres: "S.J.Res.", hconres: "H.Con.Res.", sconres: "S.Con.Res.",
};

export function measureReferenceLabel(row = {}) {
  const reference = row.measure_reference;
  if (!reference || typeof reference !== "object" || Array.isArray(reference)
    || Object.keys(reference).length !== 3
    || !Number.isSafeInteger(reference.congress) || reference.congress <= 0
    || !Number.isSafeInteger(reference.number) || reference.number <= 0
    || reference.congress !== row.congress
    || typeof reference.type !== "string"
    || !Object.hasOwn(TYPE_LABELS, reference.type)) return "";
  return `${TYPE_LABELS[reference.type]} ${reference.number} (Congress ${reference.congress})`;
}
