export const AUTHZ_JOURNEY_IDS: readonly string[];
export function isAuthzE2EMode(env?: NodeJS.ProcessEnv): boolean;
export function getE2EArtifactNamespace(
  env?: NodeJS.ProcessEnv,
): "authz" | "core";
export function getE2EDatabaseDirectory(
  env?: NodeJS.ProcessEnv,
): "temp-authz" | "temp";
export function getE2ETestIgnore(env?: NodeJS.ProcessEnv): string[];
export function inspectAuthzJourneyTitles(titles: string[]): {
  valid: boolean;
  missing: string[];
  duplicates: string[];
};
