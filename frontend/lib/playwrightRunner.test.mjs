import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const frontend = fileURLToPath(new URL("../", import.meta.url));
const configURL = new URL("../playwright.config.mjs", import.meta.url).href;
const playwrightURL = pathToFileURL(path.join(
  path.dirname(require.resolve("@playwright/test/package.json")), "index.mjs",
)).href;
const cli = require.resolve("@playwright/test/cli");

// Exercise the real CLI/plugin boundary without a browser or a giant repository
// diff. Only optional diff/fetch subprocesses are replaced; commit capture is real.
function runCanary(t, failAssertion) {
  const outputRoot = path.join(frontend, "test-results");
  fs.mkdirSync(outputRoot, { recursive: true });
  const scratch = fs.mkdtempSync(path.join(outputRoot, "runner-contract-"));
  assert.equal(path.dirname(scratch), outputRoot);
  t.after(() => fs.rmSync(scratch, { recursive: true, force: true }));
  const callsFile = path.join(scratch, "git-calls.jsonl");
  const reportFile = path.join(scratch, "report.json");
  const hookFile = path.join(scratch, "git-hook.cjs");
  fs.writeFileSync(hookFile, `
    const cp = require("node:child_process");
    const fs = require("node:fs");
    const original = cp.spawn;
    cp.spawn = function(command, args, options) {
      if (command === "git") {
        fs.appendFileSync(process.env.RUNNER_GIT_CALLS, JSON.stringify(args) + "\\n");
        if (args[0] === "fetch" || args[0] === "diff") {
          // Finite, bounded stand-in for the CI diff that overflows V8 strings.
          const script = args[0] === "diff"
            ? 'process.stdout.write("x".repeat(1024 * 1024))' : '';
          return original.call(this, process.execPath, ["-e", script], options);
        }
      }
      return original.call(this, command, args, options);
    };
  `);
  const configFile = path.join(scratch, "playwright.config.mjs");
  fs.writeFileSync(configFile, `
    import base from ${JSON.stringify(configURL)};
    export default {
      ...base,
      testDir: ${JSON.stringify(scratch)},
      outputDir: ${JSON.stringify(path.join(scratch, "results"))},
      webServer: undefined,
      workers: 1,
      retries: 0,
      reporter: [["json", { outputFile: ${JSON.stringify(reportFile)} }]],
    };
  `);
  fs.writeFileSync(path.join(scratch, "canary.spec.mjs"), `
    import { test, expect } from ${JSON.stringify(playwrightURL)};
    test("runner assertion canary", () => {
      expect(${JSON.stringify(failAssertion)}).toBe(false);
    });
  `);
  const eventFile = path.join(scratch, "event.json");
  const head = spawnSync("git", ["rev-parse", "HEAD"], {
    cwd: frontend, encoding: "utf8", timeout: 10_000,
  });
  assert.equal(head.status, 0, head.stderr);
  const sha = head.stdout.trim();
  fs.writeFileSync(eventFile, JSON.stringify({
    pull_request: { title: "Runner contract", number: 1, base: { sha } },
  }));
  const result = spawnSync(process.execPath, ["--require", hookFile, cli,
    "test", "--config", configFile], {
    cwd: frontend,
    encoding: "utf8",
    timeout: 30_000,
    maxBuffer: 2 * 1024 * 1024,
    env: {
      ...process.env,
      CI: "true",
      GITHUB_ACTIONS: "true",
      GITHUB_EVENT_PATH: eventFile,
      GITHUB_SERVER_URL: "https://github.com",
      GITHUB_REPOSITORY: "fixture/runner",
      GITHUB_SHA: sha,
      GITHUB_RUN_ID: "1",
      RUNNER_GIT_CALLS: callsFile,
      PLAYWRIGHT_JSON_OUTPUT_FILE: reportFile,
    },
  });
  assert.ifError(result.error);
  assert.equal(result.signal, null);
  assert.equal(result.status, failAssertion ? 1 : 0, result.stdout + result.stderr);
  const report = JSON.parse(fs.readFileSync(reportFile, "utf8"));
  assert.equal(report.stats.expected, failAssertion ? 0 : 1);
  assert.equal(report.stats.unexpected, failAssertion ? 1 : 0);
  assert.equal(report.stats.skipped, 0);
  assert.equal(report.stats.flaky, 0);
  assert.equal(report.config.metadata.gitCommit.hash, sha);
  const calls = fs.readFileSync(callsFile, "utf8").trim().split("\n").map(JSON.parse);
  assert.ok(calls.some(([operation]) => operation === "log"), "commit capture must run");
  assert.deepEqual(calls.filter(([operation]) => ["diff", "fetch"].includes(operation)), [],
    "optional PR diff capture must not spawn or buffer git diff/fetch");
  assert.equal(report.config.metadata.gitDiff, undefined);
  if (failAssertion) {
    const result = report.suites[0].specs[0].tests[0].results[0];
    assert.equal(result.status, "failed");
    assert.match(result.error.message, /toBe/);
  }
}

test("CI runner avoids optional PR diff capture and retains actual commit metadata", (t) => {
  runCanary(t, false);
});

test("CI runner still reports assertion failures and exits nonzero without diff capture", (t) => {
  runCanary(t, true);
});
