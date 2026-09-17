"use client";
import HomePage from "../app/page";
import { recordCardReviewClient } from "../lib/recordCardReviewClient.mjs";
import { fetchLegislatorProfile, fetchPositions, fetchEditorialPresentations, fetchPositionEvidence } from "../lib/api";
const liveClient = { fetchLegislatorProfile, fetchPositions, fetchEditorialPresentations, fetchPositionEvidence };

export default function RecordCardReviewJourney({ candidate, profiles, dataSource = "snapshot" }) {
  return <HomePage dataClient={dataSource === "live" ? liveClient : recordCardReviewClient} reviewCandidate={candidate} reviewProfiles={profiles} reviewDataSource={dataSource} />;
}
