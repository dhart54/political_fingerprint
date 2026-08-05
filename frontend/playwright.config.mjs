import { defineConfig, devices } from "@playwright/test";

const useProductionBuild = process.env.PLAYWRIGHT_PRODUCTION_BUILD === "1";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
  },
  webServer: {
    command: useProductionBuild
      ? "npm run start -- --hostname 127.0.0.1 --port 3100"
      : "npm run dev -- --hostname 127.0.0.1 --port 3100",
    env: {
      ...process.env,
      ENABLE_ZIP_LOOKUP_STATE_FIXTURE: "1",
      ENABLE_M6_REVIEW_FIXTURE: "1",
    },
    reuseExistingServer: !process.env.CI && !useProductionBuild,
    timeout: 120_000,
    url: "http://127.0.0.1:3100/",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: {
          width: 1280,
          height: 900,
        },
      },
    },
  ],
});
