from dataclasses import dataclass
from datetime import date
from statistics import median

from app.etl.classify import ClassificationStepResult, run_classification
from app.etl.ingest import IngestResult, run_ingest
from app.metrics.drift import DriftResult, compute_drift
from app.metrics.fingerprint import EligibleVote, FingerprintRecord, build_eligible_vote, compute_fingerprint


@dataclass(frozen=True)
class ChamberMedianRecord:
    chamber: str
    party: str
    domain: str
    median_share: float
    legislator_count: int


@dataclass(frozen=True)
class ComputeStepResult:
    source: str
    records_loaded: int
    records_classified: int
    fingerprints_computed: int
    chamber_medians_computed: int
    drift_scores_computed: int
    fingerprint_records: list[FingerprintRecord]
    chamber_medians: list[ChamberMedianRecord]
    drift_results: list[DriftResult]


def run_compute(
    classification_result: ClassificationStepResult,
    ingest_result: IngestResult,
    *,
    as_of: date,
) -> ComputeStepResult:
    eligible_votes = build_eligible_votes(ingest_result, classification_result)
    legislators = ingest_result.fixtures.legislators

    fingerprints: list[FingerprintRecord] = []
    drift_results: list[DriftResult] = []
    legislator_metadata = {legislator["id"]: legislator for legislator in legislators}

    for legislator in legislators:
        fingerprints.extend(
            compute_fingerprint(
                legislator_id=legislator["id"],
                votes=eligible_votes,
                as_of=as_of,
                classification_version="v1",
            )
        )
        drift_results.append(
            compute_drift(
                legislator_id=legislator["id"],
                votes=eligible_votes,
                as_of=as_of,
                classification_version="v1",
            )
        )

    chamber_medians = compute_chamber_medians(
        fingerprints=fingerprints,
        legislator_metadata=legislator_metadata,
    )

    return ComputeStepResult(
        source=classification_result.source,
        records_loaded=classification_result.records_loaded,
        records_classified=classification_result.records_classified,
        fingerprints_computed=len(fingerprints),
        chamber_medians_computed=len(chamber_medians),
        drift_scores_computed=len(drift_results),
        fingerprint_records=fingerprints,
        chamber_medians=chamber_medians,
        drift_results=drift_results,
    )


def run_etl(*, source: str = "fixtures", as_of: date | None = None) -> ComputeStepResult:
    ingest_result: IngestResult = run_ingest(source=source)
    classification_result = run_classification(ingest_result, classification_version="v1")
    return run_compute(
        classification_result,
        ingest_result,
        as_of=as_of or date.today(),
    )


def build_eligible_votes(
    ingest_result: IngestResult,
    classification_result: ClassificationStepResult,
) -> list[EligibleVote]:
    roll_calls_by_id = {roll_call["id"]: roll_call for roll_call in ingest_result.fixtures.roll_calls}
    classified_roll_calls = {
        classified_roll_call.roll_call_id: classified_roll_call
        for classified_roll_call in classification_result.classified_roll_calls
        if classified_roll_call.is_eligible and classified_roll_call.primary_domain is not None
    }

    return [
        build_eligible_vote(
            legislator_id=vote["legislator_id"],
            vote_date=roll_calls_by_id[vote["roll_call_id"]]["vote_date"],
            primary_domain=classified_roll_calls[vote["roll_call_id"]].primary_domain,
        )
        for vote in ingest_result.fixtures.votes_cast
        if vote["roll_call_id"] in classified_roll_calls
    ]


def compute_chamber_medians(
    *,
    fingerprints: list[FingerprintRecord],
    legislator_metadata: dict[str, dict[str, str]],
) -> list[ChamberMedianRecord]:
    records: list[ChamberMedianRecord] = []
    grouping_rules = ("ALL", "D", "R")

    for chamber in ("house", "senate"):
        chamber_records = [
            record
            for record in fingerprints
            if legislator_metadata[record.legislator_id]["chamber"] == chamber
        ]
        for party in grouping_rules:
            for domain in sorted({record.domain for record in fingerprints}):
                party_records = [
                    record
                    for record in chamber_records
                    if party == "ALL" or legislator_metadata[record.legislator_id]["party"] == party
                ]
                shares = [record.vote_share for record in party_records if record.domain == domain]
                records.append(
                    ChamberMedianRecord(
                        chamber=chamber,
                        party=party,
                        domain=domain,
                        median_share=median(shares) if shares else 0.0,
                        legislator_count=len(shares),
                    )
                )

    return records


if __name__ == "__main__":
    result = run_etl()
    print(result)
