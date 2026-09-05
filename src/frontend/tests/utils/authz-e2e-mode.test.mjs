import assert from "node:assert/strict";
import test from "node:test";
import {
  AUTHZ_JOURNEY_IDS,
  getE2EArtifactNamespace,
  getE2EDatabaseDirectory,
  getE2ETestIgnore,
  inspectAuthzJourneyTitles,
  isAuthzE2EMode,
} from "./authz-e2e-mode.mjs";

test("keeps normal and authorization E2E state isolated", () => {
  assert.equal(isAuthzE2EMode({}), false);
  assert.equal(getE2EArtifactNamespace({}), "core");
  assert.equal(getE2EDatabaseDirectory({}), "temp");
  assert.ok(getE2ETestIgnore({}).includes("**/core/features/authz/**"));

  const authzEnv = { LANGFLOW_E2E_AUTHZ: "true" };
  assert.equal(isAuthzE2EMode(authzEnv), true);
  assert.equal(getE2EArtifactNamespace(authzEnv), "authz");
  assert.equal(getE2EDatabaseDirectory(authzEnv), "temp-authz");
  assert.ok(!getE2ETestIgnore(authzEnv).includes("**/core/features/authz/**"));
});

test("accepts exactly one occurrence of every authorization journey", () => {
  const titles = AUTHZ_JOURNEY_IDS.map((id) => `[${id}] scenario`);
  assert.deepEqual(inspectAuthzJourneyTitles(titles), {
    valid: true,
    missing: [],
    duplicates: [],
  });
});

test("rejects missing, duplicate, and extra authorization journeys", () => {
  const titles = AUTHZ_JOURNEY_IDS.slice(1).map((id) => `[${id}] scenario`);
  titles.push(`[${AUTHZ_JOURNEY_IDS[1]}] duplicate`, "untracked scenario");
  const result = inspectAuthzJourneyTitles(titles);
  assert.equal(result.valid, false);
  assert.deepEqual(result.missing, [AUTHZ_JOURNEY_IDS[0]]);
  assert.deepEqual(result.duplicates, [AUTHZ_JOURNEY_IDS[1]]);
});
