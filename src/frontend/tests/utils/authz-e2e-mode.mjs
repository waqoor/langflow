export const AUTHZ_JOURNEY_IDS = Object.freeze(
  Array.from(
    { length: 8 },
    (_, index) => `AUTHZ-JOURNEY-${String(index + 1).padStart(2, "0")}`,
  ),
);

// Vite watches the frontend root during Playwright runs. Windows cannot watch
// Playwright trace files while Chromium has them locked, so generated runner
// directories must stay outside the dev server's watcher.
export const E2E_ARTIFACT_WATCH_IGNORE =
  /(?:^|[\\/])(?:test-results(?:-authz)?|playwright-report(?:-authz)?|blob-report-(?:authz|core)|coverage)(?:[\\/]|$)/;

export function isAuthzE2EMode(env = process.env) {
  return env.LANGFLOW_E2E_AUTHZ === "true";
}

export function getE2EArtifactNamespace(env = process.env) {
  return isAuthzE2EMode(env) ? "authz" : "core";
}

export function getE2EDatabaseDirectory(env = process.env) {
  return isAuthzE2EMode(env) ? "temp-authz" : "temp";
}

export function getE2ETestIgnore(env = process.env) {
  return isAuthzE2EMode(env)
    ? ["**/live/**"]
    : ["**/live/**", "**/core/features/authz/**"];
}

export function inspectAuthzJourneyTitles(titles) {
  const counts = new Map(AUTHZ_JOURNEY_IDS.map((id) => [id, 0]));
  for (const title of titles) {
    for (const id of AUTHZ_JOURNEY_IDS) {
      if (String(title).includes(`[${id}]`)) {
        counts.set(id, (counts.get(id) ?? 0) + 1);
      }
    }
  }

  const missing = AUTHZ_JOURNEY_IDS.filter((id) => counts.get(id) === 0);
  const duplicates = AUTHZ_JOURNEY_IDS.filter(
    (id) => (counts.get(id) ?? 0) > 1,
  );
  return {
    valid:
      titles.length === AUTHZ_JOURNEY_IDS.length &&
      missing.length === 0 &&
      duplicates.length === 0,
    missing,
    duplicates,
  };
}
