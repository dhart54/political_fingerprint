import { blindEditorialPipelineValidationData } from "./blindEditorialPipelineValidationData.mjs";
import { buildJusticeMemberReviewProfile } from "./justiceCrossMemberReviewSlices.mjs";

export const blindEditorialPipelineReviewProfile = buildJusticeMemberReviewProfile({
  overlay: blindEditorialPipelineValidationData.overlay,
  inference: blindEditorialPipelineValidationData.inference,
  fixtureId: "blind-editorial-pipeline-validation-v1",
  designation: "reference_render_fixture",
  featuredEpisodeIds: blindEditorialPipelineValidationData.featuredEpisodeIds,
});

export const blindEditorialPipelineValidationFixture = Object.freeze({
  id: "blind-editorial-pipeline-validation-v1",
  designation: blindEditorialPipelineReviewProfile.candidate.standardizationFixture.designation,
  candidate: blindEditorialPipelineReviewProfile.candidate,
  evidenceRows:
    blindEditorialPipelineReviewProfile.fixtureData
      .evidenceByDomain
      .JUSTICE_PUBLIC_SAFETY
      .evidence,
});
