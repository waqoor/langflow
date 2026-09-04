# Native authorization, teams, and sharing verification record

**Canonical repository:** `https://github.com/waqoor/langflow` \
**Delivery branch:** `feat/auth-team-sharing` \
**Fork-main base:** `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5` \
**Prior tested implementation commit:** `170dd9e1d2e5024d484769515b7bb2c511f6ef77` \
**Prior tested implementation tree:** `ae6fbd4713f182f55c4b77f13a73320e84cb2002` \
**Migration:** `bf6c22022777`, down revision `c6d8e0f2a4b7`, phase `MIGRATE` \
**Verification date:** September 5, 2026 \
**Status:** Implementation review and validation in progress. The September 5 review found additional correctness defects, so the earlier results below do not establish acceptance of the current candidate. Final commit and hosted build/test evidence are pending.

## September 5 continuation

Work continues on `feat/auth-team-sharing` from `b86381ec3b`. The objective authorizes feature-branch delivery and fork build/test validation. The eight pre-existing, unrelated working-tree edits remain user-owned and excluded from feature commits. `main`, the authoritative plan, and production configuration remain unchanged.

The new regression cases first demonstrated these failures:

- An unready native service could weaken mandatory write preconditions and return owner capabilities.
- Effective-permission discovery could invent unsupported actions for resource owners.
- Collaborator PATCH/PUT responses, including no-op responses, could expose owner credentials. Restoring a redacted value could also retain client-modified metadata that removed its secret classification.
- A previously loaded project ORM instance could validate a stale revision.
- Cached successful permission/share queries could keep mutation controls enabled after a failed refetch.
- A successful save with newer local graph edits could leave those edits carrying the old revision.
- Concurrent SQLite saves, bulk-flow deletes, and project deletes could lose the revision race when audit writes were disabled.
- The PostgreSQL CI setting did not reach the HTTP application's database fixture. HTTP clients now use private PostgreSQL databases when that engine is selected, and assert the running engine's dialect.

Current results (all local commands use the locked checkout; these are not hosted CI results):

| Check | Observed result |
|---|---|
| Full frontend Jest with `TZ=UTC` | 667 suites and 7,097 tests passed; zero failures. |
| New frontend regressions | 3 suites, 40 tests passed after the fixes. |
| Authorization regression selection excluding the separately run native HTTP and collaboration files | 422 tests passed. |
| Concurrent native HTTP saves | Both resource types and both audit modes passed: 4/4. |
| Concurrent native HTTP deletions | Before fixes: 2 failures and 4 passes. After fixes: flow and bulk-flow cases passed before a Windows package-discovery timeout in setup; remaining cases are being rerun. |
| Browser acceptance | First current run: J1/J2 passed, J3 failed on owner-observed graph content, J4-J8 did not run. A trace-enabled rerun is investigating the save sequence. These outcomes are not acceptance. |
| Canonical OpenAPI generator | Output is byte-identical to `docs/openapi/openapi.json`. |
| Feature Biome | 116 files passed. The three diagnostics in a wider working-tree check belong to untouched message-query files with user-owned edits. |
| Scoped Mypy | 9 changed production files passed using explicit backend/LFX package paths, the workspace Python executable, and skipped import traversal. |
| Full TypeScript comparison | Clean fork base: 254 errors. Candidate: 247 errors. After normalizing checkout paths, no new diagnostics and 7 resolved diagnostics. |
| CI scripts | 152 passed and 4 failed on Windows. All four failures reproduce in the clean fork-base checkout: bundle-release planning uses Windows separators in Git object paths. Authz/endpoint/principal contract selection passed 24/24. |
| SQLite/PostgreSQL full acceptance; Python 3.10/3.14; builds; hosted CI | Final candidate runs pending. |

Evidence logs are under the local temporary directory `langflow-authz-20260905-current`. The clean comparison checkout is detached at the exact fork-main base above. Later sections retain the prior candidate's history; their PASS labels must not be transferred to the current candidate without the final reruns.

## Scope and delivery boundary

The sole implementation authority is `auth_share_implementation_plan.md`, revision 1.2. Its committed SHA-256 is `6b648457de1e62132bad19f05f08332e35b1bd7ad0b661d6e3f87b5f837a4899`.

- `origin` is the user fork, `https://github.com/waqoor/langflow.git`.
- `upstream` is read-only for this work: fetch is `https://github.com/langflow-ai/langflow.git` and push is disabled.
- The tested implementation is 15 commits ahead of the fork-main base and zero commits behind it.
- No parallel identity system, policy database, API version, resource-copy path, or shadow authorization runtime was added.
- No push, pull request, merge to `main`, release, deployment, production setting change, or production credential use was performed.

## Implemented contract

| Area | Implemented result |
|---|---|
| Native service | `LangflowAuthorizationService` is the single database-backed production evaluator when authorization is enabled. Default-off behavior remains owner-scoped. Unknown actions, incomplete policy data, inactive identities, and service failures deny in enabled mode. |
| Teams | Atomic non-empty creation; `admin`, `maintainer`, and `user` membership roles; active-user/source rules; team-scoped management; row/advisory locks; and final-member/final-active-admin invariants. Invalid legacy teams without an active Admin are excluded from recipient discovery. |
| Sharing | Existing `AuthzShare` remains canonical. Direct user/team flow and project grants, current/future child inheritance, effective-access summaries, recipient search, share revisions, and mutation audit rows are integrated into the existing service and routes. |
| Resource safety | Read, execute, write, and administration remain distinct. The UI exposes only **Can use** (`execute`) and **Can edit** (`write`). Sharing never grants ownership, deletion, moving, publishing, resharing, or owner-bound secrets. A direct workflow share exposes neither its private parent nor siblings. |
| Concurrency | Flow/project `edit_revision` and share `revision` support strong ETags. Enabled native-collaboration mutations require `If-Match`; missing and stale preconditions return `428` and `412`. Stale writes are not replayed automatically. |
| Execution | Shared execution preserves the authenticated actor and existing dependency/public-principal restrictions. Fresh admissions observe revocation without requiring an in-process cache broadcast. |
| Frontend | Platform-admin Teams, team roster management, Shared With Me, reusable project/workflow Share dialogs, bounded recipient search, effective-access explanations, owner labels, capability-gated controls, and conflict handling use the existing customization/query seams. Dialog state resets correctly on close/reopen. |
| API and schema | Capabilities, recipients, teams, shares, summaries, shared-resource projections, and per-resource effective permissions are typed and present in canonical OpenAPI. The additive migration extends the existing models/tables. |
| CI and E2E | Existing workflows contain path selection, SQLite/PostgreSQL and Python 3.10/3.14 jobs, the exact eight-journey serial Playwright selection, zero retries, report validation, candidate-ref plumbing, and the ARM64 runner default. |

### Final audit repairs in `d709fc7547`

- Allowed mutation audits are staged in the same transaction as the canonical write; denied decisions first roll back the doomed request transaction and then persist independently.
- Share create/update/delete retries re-resolve the resource, policy snapshot, authorization decision, and audit session on every attempt instead of reusing stale or rolled-back state.
- Active-team recipient discovery now requires an active Admin through a correlated database predicate.
- Flow/project bulk mutation and fetch paths retain owner/share semantics across concurrent removal and ORM expiration boundaries.
- SQLModel typing, flow-secret typing, and changed-route Mypy errors were resolved without weakening runtime checks.
- Baseline flow/project/user tests were aligned with the canonical default-project, account-deletion, and startup credential-scrubbing contracts.
- Frontend hook ordering, permission-query test seams, dialog reopening, folder-store typing, and affected fixtures were repaired.
- Accidentally tracked Playwright reports, test results, the test secret-key file, and the 12.48 MB SQLite test database were removed and their namespaced output directories are ignored.

### Strict browser accessibility repairs in `dbb0c20e54`

- Dynamic node and field names are encoded at the shared DOM-ID boundary, so `aria-labelledby` remains one valid ID reference even when a generated node ID contains spaces or punctuation.
- Workflow and project share-dialog state is owned by the persistent toolbar/card/sidebar surface. The originating Radix menu now closes before the modal opens, so its portalled menu is not left exposed outside a landmark behind the dialog.
- Focused Jest/axe regression coverage exercises both the unsafe node ID and the dropdown-to-dialog lifecycle.

### Final consistency and Windows acceptance repairs in `170dd9e1d2`

- Team, user-lifecycle, and share writers now follow the documented cross-entity order: plugin preflight, UUID-sorted users, UUID-sorted teams/resources, and then memberships/shares. Unlocked identifier hints are re-read under canonical locks and boundedly replayed if the lock set changed.
- SQLite writers establish the database-wide writer transaction before authoritative invariant reads. PostgreSQL locked ORM reads use `populate_existing` so an identity-map object loaded for the preliminary hint cannot bypass the post-lock canonical state.
- A stale share whose user or team recipient is no longer eligible remains revocable, while create/update continue to reject an ineligible recipient. Multi-resource cleanup locks all share rows once in UUID order.
- The Share dialog and Team details were split into focused subcomponents below the repository complexity threshold. Team-member pagination uses a 51-row lookahead for 50-row pages and resets when the selected team changes; inline mutation errors are announced.
- Vite excludes generated Playwright result, report, coverage, and blob directories from its watcher. This prevents Windows `EBUSY` crashes when Chromium holds a trace file open, with a cross-platform path-policy regression test.

## Prior candidate verification results

The following results were recorded for the prior candidate identified at the top. Current continuation results and unresolved failures take precedence. Where a Windows runner required a split run, that boundary is stated rather than hidden.

| Check | Status | Actual result and boundary |
|---|---|---|
| Consolidated backend authorization/API suite | PASS | 504 tests passed across the SQLite migration, authorization API/service/policy/visibility, and deployment-route selection; 7 upstream warnings. The final share-route regression file separately passed 57 tests. |
| Exact backend CI selection on SQLite | PASS | All 207 collected tests passed together with 1 upstream warning in 132.22s against a fresh SQLite database. |
| Full affected route baselines | PASS | 249 passed and 1 intentional skip across flow, project, user, secrets, and API-utility coverage. The constituent flow/project/user files also passed in their focused runs. |
| Pure policy matrix | PASS | 112 passed. |
| LFX default authorization contract | PASS | 17 passed. |
| PostgreSQL 16.15 CI selection | PASS (Windows split) | The same seven-file selection passed 206 tests with 1 deselection and 1 upstream warning in 103.61s against a fresh disposable PostgreSQL 16.15 database; the one Chroma-enabled case passed separately 1/1 in 22.52s. Thus all 207 collected cases pass, including PostgreSQL roster concurrency and migration round-trip coverage. The combined Windows process can retain a Chroma SQLite handle during teardown; this platform boundary is not represented as a product assertion failure. |
| CI contract scripts | PASS | Authorization endpoint and execution-principal matrix checkers passed; their contract tests passed 24/24. Router trust validation also passed. |
| Ruff | PASS | The final 8-file backend audit delta was already formatted and reported no lint issues. Earlier broad changed-backend coverage remains green. |
| Scoped Mypy | PASS | The final 5 changed production backend files passed using explicit package bases, the backend/LFX source paths, and skipped import traversal. Earlier broad changed-production coverage remains green. |
| Raw monorepo Mypy invocation | BASELINE, NOT A FEATURE GATE | A naive invocation followed the entire monorepo and emitted 3,741 existing optional-dependency/import diagnostics. It was replaced by the scoped changed-production-file gate above, not represented as a feature regression. |
| Frontend Biome | PASS | All 116 frontend source/config files in the tested feature surface passed the repository-pinned Biome check without fixes. Eight unrelated user-owned working-tree files were preserved and excluded from the implementation commit. |
| Frontend TypeScript | BASELINE | Full TSC reproduced exactly 247 repository diagnostics in 83 files and none in the final audit delta. |
| Affected frontend Jest | PASS | All 30 affected Jest files passed: 30 suites, 236 tests, 0 failures/skips. This includes Share dialog, menu lifecycle, node-field ARIA, Teams/pagination, permissions, autosave, and folder mutation coverage. Locale-key parity also passed in the focused recheck. |
| Full frontend Jest | BASELINE | 664 suites passed and 3 failed; 7,089 tests passed and 3 failed. All three failures are outside the feature diff: two existing locale/timezone expectations in `sort-sender-messages.test.ts` and `dateTime.test.ts`, plus `FormKeyRender.test.tsx`, whose active-preset test derives a UTC date while the implementation intentionally derives a local date. |
| Playwright utilities | PASS | 69/69 passed, including authz mode, report-manifest validation, and the generated-artifact watcher policy. |
| Frontend production build | PASS | 8,024 modules transformed; the post-repair build completed in 1m28s with existing Tailwind/chunk warnings. |
| Authz Playwright discovery | PASS | Exactly 8 `@authz` Chromium tests were collected from one file. |
| Authz Playwright execution and IBM scan | PASS | All 8 journeys passed in 8.7m with the native enforcer, a fresh database, distinct users, one worker, zero retries, full traces, and strict IBM assertions. The JSON report gate confirmed 8 expected outcomes, one attempt per journey, and zero failures/flaky results. Five named IBM reports contain zero violations and 12,762 passing checks. |
| Canonical OpenAPI | PASS | Generation completed without tracked drift; 12 authz route groups are present. |
| Documentation production build | PASS | A one-worker, retained-server-bundle `npm run build` generated the static site after the inherited shell-only `DEBUG` variable was removed for the child process. Existing unresolved workflow-schema references, browser-data age, sampler, and historical-anchor warnings remain non-fatal repository baselines. |
| Managed repository hooks | PASS WITH WINDOWS WRAPPERS | Staged case, EOF, line-ending, whitespace, Ruff, router-trust, and secret hooks passed. The Bash-based local Biome hook again stalled on Windows and was interrupted only after the equivalent repository-pinned native Biome check passed all 116 files; the two Biome hook IDs were skipped for the commit on that evidence. No hook configuration was weakened. |
| `git diff --check` | PASS | The implementation index and commit range are whitespace-clean. |
| `actionlint` | NOT RUN | The binary is unavailable locally. Repository CI contract tests and YAML parsing provide partial local coverage, but are not represented as `actionlint`. |
| Python 3.10 local runtime | NOT RUN | No local interpreter was available; the fork workflow includes Python 3.10. |
| Python 3.14 full integration | BLOCKED EXTERNAL | Locked dependency preparation requires an MSVC C++ linker/workload unavailable on this Windows host. No Python 3.14 integration test is claimed. |
| ARM64 Docker candidate image | NOT RUN | The workflow targets `ubuntu-24.04-arm`, but no eligible fork Actions run was started. |
| Fork GitHub Actions | NOT RUN | No candidate was pushed, so no run/job/attempt URL or hosted artifact exists. Local PASS results are not described as GitHub CI. |
| Upstream submission/acceptance | NOT APPLICABLE | No upstream PR, maintainer review, merge queue, or acceptance claim was requested or performed. |
| Deployment/merge | NOT APPLICABLE | No deployment, release, or merge to fork `main` was performed. |

### Representative commands

```powershell
uv run pytest <authorization-and-route-selection> -q --tb=short
uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q --tb=short
uv run pytest src/backend/tests/unit/api/v1/test_flows.py -q --tb=short
uv run pytest src/backend/tests/unit/api/v1/test_projects.py -q --tb=short
uv run pytest src/backend/tests/unit/test_user.py -q --tb=short

uv run python scripts/ci/check_authz_endpoint_matrix.py
uv run python scripts/ci/check_execution_principal_matrix.py
uv run pytest scripts/ci/test_authz_endpoint_matrix.py `
  scripts/ci/test_execution_principal_matrix.py `
  scripts/ci/test_authz_workflow_contract.py -q --tb=short

$env:LANGFLOW_E2E_AUTHZ = "true"
$env:RUN_A11Y = "true"
$env:RUN_A11Y_ASSERT = "true"
npx playwright test tests/core/features/authz --grep "@authz" --project=chromium --list
npx playwright test tests/core/features/authz --grep "@authz" --project=chromium --workers=1 --retries=0
npm run test:e2e-utilities
npm run build

$env:DOCUSAURUS_SSG_WORKER_THREAD_COUNT = "1"
$env:DOCUSAURUS_KEEP_SERVER_BUNDLE = "true"
Remove-Item Env:DEBUG -ErrorAction SilentlyContinue
npm run --prefix docs build
```

PostgreSQL evidence used a disposable `postgres:16` container, synthetic test-only credentials, and a fresh database. Disposable databases/containers were removed after verification.

## Eight connected browser journeys

Runtime: Windows x64, uv Python 3.12, Node/npm from the repository development environment, repository Playwright/Chromium, SQLite, the real `LangflowAuthorizationService`, and distinct admin/owner/direct-recipient/team-recipient accounts.

| Journey | Status | Connected outcome |
|---|---|---|
| `AUTHZ-JOURNEY-01` | PASS | Platform Admin creates a non-empty team; scoped roles control member UI. |
| `AUTHZ-JOURNEY-02` | PASS | An owner grants Can use; the recipient runs but cannot save. |
| `AUTHZ-JOURNEY-03` | PASS | The owner upgrades the same grant; the recipient edits content visible to the owner. |
| `AUTHZ-JOURNEY-04` | PASS | A team project share covers existing, future, and collaborator-created workflows. |
| `AUTHZ-JOURNEY-05` | PASS | Removing team membership revokes fresh team access while ownership and another direct grant survive. |
| `AUTHZ-JOURNEY-06` | PASS | Downgrade rejects an already-open editor save and retains local unsaved content. |
| `AUTHZ-JOURNEY-07` | PASS | Concurrent editors produce one success and one stale-write conflict without replay. |
| `AUTHZ-JOURNEY-08` | PASS | Direct workflow sharing exposes neither the private parent project nor sibling workflows. |

Local browser output is namespaced under `src/frontend/playwright-report-authz/`, `src/frontend/test-results-authz/`, `src/frontend/temp-authz`, and `src/frontend/temp-authz-config/`. These are ignored generated artifacts, not committed evidence. The five strict local scan labels were `authz-admin-teams`, `authz-shared-with-me`, `authz-read-only-flow-editor`, `authz-resource-share-dialog`, and `authz-member-teams`; each reported zero violations. CI is configured to upload a report and validate the exact journey manifest when a hosted run is authorized.

## Requirements-to-evidence map

| Requirement/scenario family | Primary evidence |
|---|---|
| `REQ-01`–`REQ-04`, `TEAM-*` | Team policy/service/admin-route tests, team UI tests, journeys 01 and 05. |
| `REQ-05`–`REQ-08`, `SHARE-*` | Share routes, native evaluator tests, Share dialog/customization tests, journeys 02, 03, 05, and 06. |
| `REQ-09`, `PROJ-*` | Native collaboration/RBAC integration, flow/project guard tests, journey 04. |
| `REQ-10`–`REQ-11`, `AUTH-*`, `WRITE-*` | RBAC/capability/route tests, save/autosave/delete/folder mutation tests, journeys 02, 03, 05, 06, 07, and 08. |
| `REQ-12`, `RUN-*` | Execution-principal contracts, deployment handlers, matrix checker, journeys 02 and 08. |
| `AUDIT-*` | Audit retention, lifecycle, collaboration/share mutation, rollback, and retry tests. |
| `MIG-*` | Migration upgrade/backfill/constraint/model-parity/downgrade coverage on SQLite and PostgreSQL. |
| `REG-*` | LFX default service, backend/route baselines, affected and full Jest, production build, OpenAPI, CI contracts, and exact browser discovery/execution. |

The map identifies primary coverage. It does not inflate parameterized tests into extra browser journeys or claim unexecuted hosted/architecture combinations.

## Baseline and runner classification

- The three full-Jest failures are date/locale-sensitive baseline assertions in files unchanged by the feature, not authorization failures.
- The full TSC backlog contains no diagnostic in the final audit delta.
- The raw Mypy command was over-broad; the 51-file production delta is clean under the repository source layout.
- The combined Windows PostgreSQL-mode RBAC selection can retain a Chroma SQLite handle during teardown. The other 206 cases and the affected test pass in split runs, so this is recorded as a same-process cleanup limitation rather than an authorization assertion failure.
- The first traced browser attempt exposed a Vite watcher crash on a locked Playwright `.network` file. The generated-artifact exclusion in `170dd9e1d2` fixed the harness, and the subsequent clean-database run passed all eight journeys with the same full-trace setting.
- The standard secret hook normalizes all baseline paths to backslashes on this host. The authoritative baseline received only the valid line-number update, and an equivalent temporary normalized-baseline scan returned zero.
- The local pre-commit Bash wrapper for Biome stalls on this Windows host. The same pinned native Biome check and staged lint both returned zero.
- A prior default-worker Docusaurus rerun lost `build/__server/server.bundle.js` after successful compilation. The final one-worker, retained-bundle run completed static generation and broken-anchor validation with exit code zero.

## Migration, API, and immutable manifest

- Migration `bf6c22022777` extends existing tables and does not create parallel team/share models.
- Upgrade, legacy repair/backfill, metadata parity, constraints, and downgrade are covered on SQLite and PostgreSQL 16.
- Canonical OpenAPI generation contains capabilities, permissions, recipients, shares, summaries, teams/members, and dynamic resource paths.
- The tested implementation changes exactly 219 paths relative to the fork-main base:

```bash
git diff --name-status \
  e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5..170dd9e1d2e5024d484769515b7bb2c511f6ef77
```

Immutable comparison:

`https://github.com/waqoor/langflow/compare/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5...170dd9e1d2e5024d484769515b7bb2c511f6ef77`

## Final acceptance boundary

## Test-contract change ledger (September 5 review)

The authoritative requirements are in `auth_share_implementation_plan.md`. This ledger reconstructs the existing branch changes against `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5` and records the additional regressions before changing their expectations. Earlier test results above are historical; the current review has not yet certified the revised candidate.

| Original test/file and behavior | Plan requirement | Intended behavior and minimal change | Retained negative/regression coverage |
| --- | --- | --- | --- |
| `test_authorization_service.py`, `test_capability_flag.py`: application service always passes through | 5, 11.1, 17.2 | Native enabled service reads canonical rows; LFX and disabled mode retain their interface defaults. Adjust application capability fixtures only. | Unknown actions/resources, inactive identities, disabled mode and LFX defaults remain covered. |
| `test_authz_admin_routes.py`: superuser-only team mutations and rosterless creation | 3, 8, 15.1 | Supply an active initial Admin and test team-scoped roles using the canonical transaction service. Duplicate-member assertions use `TEAM_MEMBERSHIP_EXISTS`. | Real roster/final-Admin race and transaction-audit assertions live in `test_collaboration_management.py`; route isolation tests retain source, duplicate and authorization checks. |
| `test_authz_share_routes.py`: share creator visibility, generic 403 errors and post-route membership audit callback | 9.2, 9.5, 15.5 | Management depends on stored resource authority; inaccessible grants return 404; canonical mutation service owns atomic audit staging. Fixtures model the new service boundary. | Owner/recipient visibility, public execute-only validation, all four API grant values, scoped authorization and retry rollback remain covered. |
| `test_flows.py`, `test_projects.py`: implicit foreign-ID copies/moves and owner-only child filtering | 4, 12.1, 12.5, 14.1 | Reject unauthorized complete-set mutations; include independently authorized collaborator children and server-generated revision fields. | Foreign resources remain unchanged after rejection; owner-scoped disabled behavior, defaults, rollback and pagination assertions remain. |
| `test_user.py`, `test_users.py`, `test_authz_lifecycle_contract.py`: hard deletion cascades through owned resources | 15.2, 15.6 | Return `409 RESOURCE_OWNERSHIP_REQUIRES_DISPOSITION` while owned resources exist; fixtures use actual active identities and explicit lifecycle locks. | Self-delete/non-admin denial, inactive login, password secrecy, transaction rollback and resource preservation remain. |
| `test_execution_principal_contract.py` and matrix fixtures: shared webhook/SSE fetch | 13.1-13.4 | Keep operational webhook/SSE transport owner-scoped. Add assertions on real fetch arguments. | Actor credentials, public principal and graph-substitution checks remain. |
| `permissionsContext.test.tsx`, `permissionUtils.test.ts`: missing permissions implicitly allow | 10.3, 16.6 | Missing/loading/error state denies; only a confirmed enforcement-disabled response permits compatibility fallback. | Positive explicit grants, default-deny, disabled-mode fallback and component gate cases remain. |
| Share extension, toolbar/sidebar and routing fixtures: extension always renders null | 16.1-16.5 | Render supported authorized actions and provide explicit capability fixtures. | Unsupported resources, ordinary-user admin denial, menu closure/focus and accessibility assertions remain. |
| Flow/folder mutation hook fixtures: headerless writes | 9.4, 14.1-14.3 | Send observed revisions; unlock then save uses the successful unlock revision. Add revision fields to persisted fixtures. | Stale edits reject without replay; unsaved graph content, scope updates and locked-flow behavior remain. |
| `foldersStore.test.ts`: exact equality for a partial flow fixture | 6, 12.1 | Include server-generated revision metadata while retaining the original flow identity check. | Folder/store identity, owner labels and response merge behavior remain. |
| Existing `use-save-flow.test.ts` in-flight edit regression: never calls the editor setter | 14.3 | Keep the newer unsaved graph and advance only its observed revision after a successful save. Replace the setter-spy assertion with content and next-request assertions. | No lost edges, no stale automatic retry, no updates to a different open flow. |
| Added native HTTP and database regressions: previously uncovered save responses, failed readiness, unknown owner actions, cached project state | 9.4, 10.1, 10.3, 11.2, 12.4, 14.2 | Use the registered production service and stored users/resources. Reject unavailable authorization, redact every collaborator save response, validate the locked revision and restrict owner actions to the canonical vocabulary. | Successful owner/recipient behavior, retained stored secrets, changed/no-op writes and stale/missing revision denials. |
| Added cached-query regressions for permission context and share dialog | 10.3, 16.4, 16.6 | A refetch failure must disable operations even if React Query retains a previous successful result. | Ready-state grants and confirmed disabled-mode behavior remain covered. |
| `tests/conftest.py` HTTP client: always starts SQLite, including the PostgreSQL authorization job | 19.1, 23.6, 23.8 | Honor the explicit authorization database selection using an isolated temporary PostgreSQL database per HTTP client; assert the running application's dialect. Default tests continue to use isolated SQLite. | The same HTTP assertions run on both engines; no authorization, migration or transaction implementation is replaced. |
| New concurrent HTTP save regression, with auditing both enabled and disabled | 14.1-14.2, 15.3 | Exactly one of two writes with the same observed revision succeeds; the other returns 412. SQLite must acquire its writer transaction before reading the revision. | Both flow/project variants verify the winning persisted content and a single revision increment, independent of audit configuration. |
| New concurrent HTTP update versus single-flow, bulk-flow or project deletion | 14.1-14.2, 15.3 | Deletion must use the same locked revision contract as updates. | Real concurrent requests verify that a successful edit survives a stale delete, or a successful delete makes the edit return 404, with auditing enabled and disabled. |
| `test_fetch.py` SQL-shape fixture | 14.1-14.2, 15.3 | Supply the PostgreSQL dialect on the fake session now that the production helper selects the database-specific lock operation. | Existing owner predicates, FOR UPDATE and identity-map refresh assertions remain unchanged; real SQLite/PostgreSQL HTTP tests cover the lock behavior. |

The current candidate is not yet accepted. The prior candidate's runtime record covers the native service, database engines, migrations, frontend, and browser journeys; additional defects found during continuation require fresh final validation. Hosted Python 3.10/3.14, ARM64 images, fork Actions, and any PR integration SHA must not be described as passing until those systems produce evidence for the delivered candidate.

The attached implementation objective and plan govern authorization. Feature-branch delivery and fork build/test runs are in scope; merging, publishing, deployment, protection changes, and production credential changes are excluded.
