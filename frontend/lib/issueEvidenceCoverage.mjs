export const DOMAIN_DESCRIPTIONS = Object.freeze({
  ECONOMY_TAXES:
    "Budgets, taxation, government funding, financial regulation, and small-business policy.",
  EDUCATION_WORKFORCE:
    "Schools, higher education, job training, labor standards, and workforce policy.",
  ENVIRONMENT_ENERGY:
    "Energy production, environmental regulation, conservation, federal lands, and resource policy.",
  HEALTH_SOCIAL:
    "Health coverage, public health, medical care, nutrition, and social-service programs.",
  IMMIGRATION_BORDER:
    "Immigration rules, border operations, visas, citizenship, and enforcement policy.",
  INFRASTRUCTURE_TECH_TRANSPORT:
    "Transportation, public infrastructure, communications, technology, and cybersecurity policy.",
  JUSTICE_PUBLIC_SAFETY:
    "Criminal law, policing, courts, sentencing, public safety, and law-enforcement oversight.",
  NATIONAL_SECURITY_FOREIGN:
    "Defense, diplomacy, international security, foreign assistance, and sanctions policy.",
});

export const DOMAIN_ORDER = Object.freeze(Object.keys(DOMAIN_DESCRIPTIONS));

export function getDomainDescription(domain) {
  return DOMAIN_DESCRIPTIONS[domain] || "Reviewed legislation and recorded actions in this issue area.";
}

export function getEvidenceCoverage(row) {
  const yea = count(row?.yea_count);
  const nay = count(row?.nay_count);
  const other = count(row?.other_count);
  const suppliedTotal = optionalCount(row?.total_votes);
  const total = suppliedTotal ?? yea + nay + other;
  const reviewedYesNo =
    count(row?.interpreted_support_count) + count(row?.interpreted_oppose_count);
  const context = Math.max(other, count(row?.interpreted_other_count));
  const reviewedShare = total > 0 ? reviewedYesNo / total : 0;

  return {
    context,
    nay,
    other,
    reviewedShare,
    reviewedYesNo,
    total,
    yea,
  };
}

export function getEvidenceCoverageLabel(row) {
  const coverage = getEvidenceCoverage(row);
  if (coverage.total <= 0) {
    return "No evidence";
  }
  if (coverage.reviewedYesNo >= 8 && coverage.reviewedShare >= 0.6) {
    return "Broad reviewed record";
  }
  if (coverage.reviewedYesNo >= 3) {
    return "Developing record";
  }
  if (coverage.reviewedYesNo >= 1) {
    return "Limited record";
  }
  if (coverage.yea + coverage.nay === 0 && coverage.other > 0) {
    return "Non-directional evidence";
  }
  return "Receipts only";
}

export function getRecordedActionComposition(row) {
  const { yea, nay, other, total } = getEvidenceCoverage(row);
  return [
    { key: "yea", label: "Yea", count: yea },
    { key: "nay", label: "Nay", count: nay },
    {
      key: "other",
      label: "Present / Not Voting / other",
      count: other,
    },
  ].map((segment) => ({
    ...segment,
    percent: total > 0 ? (segment.count / total) * 100 : 0,
  }));
}

export function orderIssueRowsByEvidenceUsefulness(rows = []) {
  return rows
    .map((row, originalIndex) => ({ originalIndex, row }))
    .sort((left, right) => {
      const leftCoverage = getEvidenceCoverage(left.row);
      const rightCoverage = getEvidenceCoverage(right.row);
      return (
        rightCoverage.total - leftCoverage.total ||
        rightCoverage.reviewedYesNo - leftCoverage.reviewedYesNo ||
        rightCoverage.context - leftCoverage.context ||
        domainRank(left.row?.domain) - domainRank(right.row?.domain) ||
        left.originalIndex - right.originalIndex
      );
    })
    .map(({ row }) => row);
}

function domainRank(domain) {
  const index = DOMAIN_ORDER.indexOf(domain);
  return index === -1 ? DOMAIN_ORDER.length : index;
}

function optionalCount(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function count(value) {
  return optionalCount(value) ?? 0;
}
