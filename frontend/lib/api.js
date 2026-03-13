const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return response.json();
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function fetchFingerprint({
  legislatorId,
  comparisonParty = "ALL",
}) {
  const response = await fetch(
    `${API_BASE_URL}/legislators/${legislatorId}/fingerprint?comparison_party=${comparisonParty}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(`Fingerprint request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchDrift({ legislatorId }) {
  const response = await fetch(`${API_BASE_URL}/legislators/${legislatorId}/drift`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Drift request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchSummary({ legislatorId }) {
  const response = await fetch(`${API_BASE_URL}/legislators/${legislatorId}/summary`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Summary request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchZipLookup({ zipCode }) {
  const response = await fetch(`${API_BASE_URL}/lookup/zip/${zipCode}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`ZIP lookup request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchLegislatorSearch({ query = "" } = {}) {
  const searchParams = new URLSearchParams();
  if (query) {
    searchParams.set("q", query);
  }

  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/legislators/search${suffix}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Legislator search request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchLegislatorComparison({
  leftLegislatorId,
  rightLegislatorId,
  comparisonParty = "ALL",
}) {
  const searchParams = new URLSearchParams({
    left_legislator_id: leftLegislatorId,
    right_legislator_id: rightLegislatorId,
    comparison_party: comparisonParty,
  });

  const response = await fetch(`${API_BASE_URL}/compare/legislators?${searchParams.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Comparison request failed with status ${response.status}`);
  }

  return response.json();
}
