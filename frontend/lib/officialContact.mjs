// Contact metadata is separate from vote meaning. Never infer or repair a path.
const SOURCE_TYPES = new Map([["official_house_website", "Official House website"], ["official_senate_website", "Official Senate website"]]);
function officialUrl(value) {
  if (typeof value !== "string" || /[\u0000-\u0020\u007f\\]/.test(value)) return null;
  try {
    const url = new URL(value);
    const official = ["house.gov", "senate.gov"].some((host) => url.hostname === host || url.hostname.endsWith(`.${host}`));
    return url.protocol === "https:" && official && !url.username && !url.password
      && !url.port && !url.search && !url.hash ? value : null;
  } catch { return null; }
}

function phoneLink(value) {
  if (typeof value !== "string" || value.length > 64 || /[\u0000-\u001f\u007f]/.test(value)) return null;
  const text = value.trim();
  if (!/^\+?[\d(). -]+$/.test(text)) return null;
  const digits = text.replace(/\D/g, "");
  return digits.length >= 10 && digits.length <= 15
    ? { text, href: `tel:${text.startsWith("+") ? "+" : ""}${digits}` } : null;
}

function retrievalDate(value) {
  if (typeof value !== "string") return null;
  const match = value.match(/^(\d{4}-\d{2}-\d{2})(?:$|[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$)/);
  if (!match || (value.length > 10 && Number.isNaN(Date.parse(value)))) return null;
  const date = new Date(`${match[1]}T00:00:00Z`);
  return !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === match[1] ? match[1] : null;
}

export function buildContactDetails(payload, legislatorId) {
  if (!legislatorId || !payload || Array.isArray(payload) || payload.legislator_id !== legislatorId
    || !["loaded", "not_loaded"].includes(payload.contact_status)) {
    throw new Error("Contact record identity or shape mismatch");
  }
  if (payload.contact_status === "not_loaded") return {
    status: "missing", origin: "missing", phone: null, websiteUrl: null, formUrl: null,
    sourceUrl: null, sourceType: null, retrievedAt: null, withheld: false,
  };
  const phone = phoneLink(payload.phone);
  const websiteUrl = officialUrl(payload.official_website_url);
  const formUrl = officialUrl(payload.contact_form_url);
  const sourceUrl = officialUrl(payload.source_url);
  const sourceHost = sourceUrl ? new URL(sourceUrl).hostname : "";
  const sourceDomain = { official_house_website: "house.gov", official_senate_website: "senate.gov" };
  const declaredDomain = Object.hasOwn(sourceDomain, payload.source_type) ? sourceDomain[payload.source_type] : null;
  return {
    status: "loaded",
    origin: ["database", "curated_fallback"].includes(payload.data_source) ? payload.data_source : "not_supplied",
    phone, websiteUrl, formUrl, sourceUrl,
    sourceType: declaredDomain && (sourceHost === declaredDomain || sourceHost.endsWith(`.${declaredDomain}`))
      ? SOURCE_TYPES.get(payload.source_type) : null,
    retrievedAt: retrievalDate(payload.source_retrieved_at),
    withheld: [[payload.phone, phone], [payload.official_website_url, websiteUrl],
      [payload.contact_form_url, formUrl], [payload.source_url, sourceUrl]].some(([supplied, safe]) => Boolean(supplied) && !safe),
  };
}
