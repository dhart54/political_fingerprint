"use client";
import HomePage from "../app/page";
import { recordCardReviewClient } from "../lib/recordCardReviewClient.mjs";

export default function RecordCardReviewJourney({ candidate, profiles }) {
  return <HomePage dataClient={recordCardReviewClient} reviewCandidate={candidate} reviewProfiles={profiles} />;
}
