import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import {
  commissioningDomainRenderProfiles,
  commissioningDomainSharedReviewText,
} from "../frontend/lib/commissioningDomainReviewSlices.mjs";
import {
  adaptEditorialIssueSlice,
  EDITORIAL_EXPERIENCE_MODE,
} from "../frontend/lib/editorialIssueExperience.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const JSON_OUTPUT = path.join(
  ROOT,
  "docs/review_packets/commissioning_domain_v1_final_text_review.json",
);
const MARKDOWN_OUTPUT = path.join(
  ROOT,
  "docs/review_packets/commissioning_domain_v1_final_text_review.md",
);
const SECTION_DEFINITIONS = [
  ["repeatedPatterns", "Repeated patterns"],
  ["policyTrajectories", "Policy trajectories"],
  ["otherNotableChoices", "Other notable choices"],
  ["meaningfulExceptions", "Meaningful exceptions"],
];

const records = commissioningDomainRenderProfiles.map(buildRecord);
const payload = {
  schema_version: "commissioning_domain_final_text_review_v1",
  generation_contract: {
    exact_renderer_input_text: true,
    paraphrased: false,
    review_only: true,
    production_eligible: false,
  },
  shared_review_dependency_text: [...commissioningDomainSharedReviewText],
  records,
  comparison: records.map((record) => ({
    fixture: record.fixture_case,
    primary_archetype: record.primary_archetype,
    repeated_patterns: record.analytical_sections.repeatedPatterns.items.length,
    trajectories: record.analytical_sections.policyTrajectories.items.length,
    notable_choices: record.analytical_sections.otherNotableChoices.items.length,
    exceptions: record.analytical_sections.meaningfulExceptions.items.length,
    coverage_state: record.coverage_state,
  })),
};

const jsonText = `${JSON.stringify(payload, null, 2)}\n`;
const markdownText = renderMarkdown(payload);
const check = process.argv.includes("--check");
if (check) {
  const mismatches = [
    [JSON_OUTPUT, jsonText],
    [MARKDOWN_OUTPUT, markdownText],
  ].filter(([file, expected]) => !fs.existsSync(file) || fs.readFileSync(file, "utf8") !== expected);
  if (mismatches.length) {
    console.error(`Final text review drift: ${mismatches.map(([file]) => path.relative(ROOT, file)).join(", ")}`);
    process.exit(1);
  }
  console.log("Commissioning final text review exports are deterministic.");
} else {
  fs.writeFileSync(JSON_OUTPUT, jsonText, "utf8");
  fs.writeFileSync(MARKDOWN_OUTPUT, markdownText, "utf8");
  console.log(`Wrote ${path.relative(ROOT, MARKDOWN_OUTPUT)} and ${path.relative(ROOT, JSON_OUTPUT)}.`);
}

function buildRecord(profile) {
  const evidence = profile.fixtureData.evidenceByDomain[profile.candidate.identity.issueId].evidence;
  const experience = adaptEditorialIssueSlice(
    profile.candidate,
    evidence,
    EDITORIAL_EXPERIENCE_MODE.review,
  );
  const presentation = experience.publicPresentation;
  const inference = profile.candidate.source.inference_candidate;
  const renderedByKey = new Map(
    presentation.analyticalSections.map((section) => [section.key, section]),
  );
  const analyticalSections = Object.fromEntries(
    SECTION_DEFINITIONS.map(([key, title]) => {
      const section = renderedByKey.get(key);
      return [key, {
        title,
        state: section ? "rendered" : "omitted",
        items: section ? section.items.map((item) => item.text) : [],
      }];
    }),
  );
  const featuredIds = new Set(experience.featuredEpisodes.map((episode) => episode.id));
  return {
    member_display_name: profile.legislator.name_display,
    member_id: profile.memberId,
    fixture_case: profile.label,
    reader_facing_label: presentation.strengthLabel,
    primary_archetype: inference.conclusion_model.archetype,
    primary_conclusion: presentation.conclusion,
    coverage_line: presentation.coverageLine,
    coverage_state: presentation.coverage.state,
    analytical_sections: analyticalSections,
    coverage_note: presentation.coverageNote,
    method_note: presentation.methodNote,
    shared_review_dependency_text: [...commissioningDomainSharedReviewText],
    featured_policy_family_and_episode_titles: experience.featuredEpisodes.map((episode) => ({
      policy_family_title: titleCase(episode.policyFamilyId),
      episode_title: episode.title,
    })),
    episodes: experience.episodes.map((episode) => ({
      policy_family_title: titleCase(episode.policyFamilyId),
      episode_title: episode.title,
      featured: featuredIds.has(episode.id),
      action_count: episode.actionCount,
      collapsed_summary: episode.memberTrajectory,
      vote_chips: episode.actions.map((action) => `${action.memberAction} · roll ${action.roll}`),
    })),
    intentionally_omitted_sections: SECTION_DEFINITIONS
      .filter(([key]) => !renderedByKey.has(key))
      .map(([, title]) => `${title}: omitted`),
    proposition_ownership: inference.section_ownership.propositions.map((item) => ({
      semantic_proposition_id: item.semantic_proposition_id,
      evidence_episodes: item.evidence_episode_ids,
      final_section: item.assigned_section,
      exact_rendered_text: item.exact_rendered_text,
      excluded_from: item.excluded_from,
    })),
  };
}

function renderMarkdown(data) {
  const lines = [
    "# Commissioning Domain V1 — Final Exact-Text Review",
    "",
    "This export reproduces the exact final strings supplied to the review-only public-style renderer. It does not paraphrase the generated text and does not confer approval, promotion, publication, or production eligibility.",
    "",
  ];
  for (const record of data.records) {
    lines.push(
      `## ${record.member_display_name} (${record.member_id})`,
      "",
      `- Fixture case: \`${record.fixture_case}\``,
      `- Reader-facing label: ${record.reader_facing_label}`,
      `- Primary conclusion: ${record.primary_conclusion ?? "omitted"}`,
      `- Coverage line: ${record.coverage_line}`,
      "",
    );
    for (const [key, title] of SECTION_DEFINITIONS) {
      const section = record.analytical_sections[key];
      lines.push(`### ${title}`, "");
      if (section.state === "omitted") {
        lines.push(`${title}: omitted`, "");
      } else {
        for (const item of section.items) lines.push(`- ${item}`);
        lines.push("");
      }
    }
    lines.push(
      "### Coverage note",
      "",
      record.coverage_note || "Coverage note: omitted",
      "",
      "### Method note",
      "",
      record.method_note || "Method note: omitted",
      "",
      "### Shared-review dependencies visible in review mode",
      "",
    );
    for (const item of record.shared_review_dependency_text) lines.push(`- ${item}`);
    lines.push("", "### Episodes", "");
    for (const episode of record.episodes) {
      lines.push(
        `#### ${episode.policy_family_title} — ${episode.episode_title}`,
        "",
        `- Action count: ${episode.action_count}`,
        `- Collapsed summary: ${episode.collapsed_summary}`,
        `- Vote chips: ${episode.vote_chips.join("; ")}`,
        `- Featured: ${episode.featured ? "yes" : "no"}`,
        "",
      );
    }
    lines.push(
      "### Intentionally omitted sections",
      "",
      ...(record.intentionally_omitted_sections.length
        ? record.intentionally_omitted_sections.map((item) => `- ${item}`)
        : ["- None"]),
      "",
      "### Proposition ownership",
      "",
      "| Semantic proposition ID | Evidence episodes | Final section | Exact rendered text | Excluded from |",
      "| --- | --- | --- | --- | --- |",
    );
    for (const item of record.proposition_ownership) {
      lines.push(`| ${escapeCell(item.semantic_proposition_id)} | ${escapeCell(item.evidence_episodes.join(", "))} | ${escapeCell(item.final_section)} | ${escapeCell(item.exact_rendered_text)} | ${escapeCell(item.excluded_from.join(", "))} |`);
    }
    lines.push("");
  }
  lines.push(
    "## Fixture comparison",
    "",
    "| Fixture | Primary archetype | Repeated patterns | Trajectories | Notable choices | Exceptions | Coverage state |",
    "| --- | --- | ---: | ---: | ---: | ---: | --- |",
  );
  for (const item of data.comparison) {
    lines.push(`| ${item.fixture} | ${item.primary_archetype} | ${item.repeated_patterns} | ${item.trajectories} | ${item.notable_choices} | ${item.exceptions} | ${item.coverage_state} |`);
  }
  return `${lines.join("\n")}\n`;
}

function titleCase(value) {
  return String(value || "")
    .replace(/[-_]+/g, " ")
    .replace(/\bfy(\d{4})\b/gi, "FY$1")
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
    .replace(/\bFy(\d{4})\b/g, "FY$1");
}

function escapeCell(value) {
  return String(value ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ");
}
