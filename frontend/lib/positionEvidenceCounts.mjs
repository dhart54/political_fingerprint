export function hasInterpretedCountFields(row) {
  return [
    "interpreted_support_count",
    "interpreted_oppose_count",
    "interpreted_other_count",
    "interpreted_total",
  ].some((field) => Object.prototype.hasOwnProperty.call(row || {}, field));
}

export function deriveInterpretedCountsFromEvidence(evidenceRows) {
  const counts = {
    interpreted_support_count: 0,
    interpreted_oppose_count: 0,
    interpreted_other_count: 0,
    interpreted_total: 0,
  };

  for (const row of evidenceRows || []) {
    if (row?.interpretation_status !== "interpreted") {
      continue;
    }

    if (row.position === row.support_position) {
      counts.interpreted_support_count += 1;
    } else if (row.position === row.oppose_position) {
      counts.interpreted_oppose_count += 1;
    } else {
      counts.interpreted_other_count += 1;
    }
  }

  counts.interpreted_total =
    counts.interpreted_support_count +
    counts.interpreted_oppose_count +
    counts.interpreted_other_count;

  return counts;
}

export async function fillMissingInterpretedCounts({ payload, fetchEvidence, legislatorId }) {
  const positions = payload?.positions || [];
  if (!positions.some((row) => !hasInterpretedCountFields(row) && (row?.total_votes || row?.recorded_votes || 0) > 0)) {
    return payload;
  }

  const enrichedRows = await Promise.all(
    positions.map(async (row) => {
      if (hasInterpretedCountFields(row) || !(row?.total_votes || row?.recorded_votes || 0)) {
        return row;
      }

      try {
        const evidencePayload = await fetchEvidence({
          legislatorId,
          domain: row.domain,
        });
        return {
          ...row,
          ...deriveInterpretedCountsFromEvidence(evidencePayload?.evidence || []),
        };
      } catch (error) {
        return row;
      }
    }),
  );

  return {
    ...payload,
    positions: enrichedRows,
  };
}
