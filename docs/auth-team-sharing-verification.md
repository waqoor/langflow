# Native authorization, teams, and sharing verification record

**Canonical repository:** `https://github.com/waqoor/langflow` \
**Delivery branch:** `feat/auth-team-sharing` \
**Fork-main base:** `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5` \
**Tested implementation commit:** `dbb0c20e541aade230f85c564e1d74b28e628c23` \
**Tested implementation tree:** `6127bd2abc7d0fa5e0b3dd2ce3fb8fd9285c51a4` \
**Migration:** `bf6c22022777`, down revision `c6d8e0f2a4b7`, phase `MIGRATE` \
**Verification date:** September 4, 2026 \
**Status:** Local implementation candidate complete. Hosted Python/architecture matrices and fork Actions remain explicitly unverified because this delivery does not push, merge, deploy, or change external settings.

## Scope and delivery boundary

The sole implementation authority is `auth_share_implementation_plan.md`, revision 1.2. Its committed SHA-256 is `6b648457de1e62132bad19f05f08332e35b1bd7ad0b661d6e3f87b5f837a4899`.

- `origin` is the user fork, `https://github.com/waqoor/langflow.git`.
- `upstream` is read-only for this work: fetch is `https://github.com/langflow-ai/langflow.git` and push is disabled.
- The tested implementation is 12 commits ahead of the fork-main base and zero commits behind it.
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

## Verification results

All PASS results apply to this branch audit. Where a check predates the last small retry-test delta or required a split run, that boundary is stated rather than hidden.

| Check | Status | Actual result and boundary |
|---|---|---|
| Consolidated backend authorization/API suite | PASS | 504 tests passed across the SQLite migration, authorization API/service/policy/visibility, and deployment-route selection; 7 upstream warnings. The final share-route regression file separately passed 57 tests. |
| Exact backend CI selection on SQLite | PASS (split) | 205 passed with the Chroma case deselected, then the isolated Chroma case passed 1/1 in 46.88s. All 206 collected functional cases pass. A combined Windows process can time out after assertions while Chroma releases a temporary SQLite handle. |
| Full affected route baselines | PASS | 249 passed and 1 intentional skip across flow, project, user, secrets, and API-utility coverage. The constituent flow/project/user files also passed in their focused runs. |
| Pure policy matrix | PASS | 112 passed. |
| LFX default authorization contract | PASS | 17 passed. |
| PostgreSQL 16.15 CI selection | PASS | The exact seven-file backend CI selection passed 203 tests with 1 upstream warning in 117.51s against a disposable PostgreSQL 16.15 database. The final commit after this run contains frontend-only accessibility changes. |
| CI contract scripts | PASS | Authorization endpoint and execution-principal matrix checkers passed; their contract tests passed 24/24. Router trust validation also passed. |
| Ruff | PASS | Format check reported 75 files already formatted; lint reported no issues. |
| Scoped Mypy | PASS | 51 changed production files passed using explicit package bases, the backend/LFX source paths, and skipped import traversal. |
| Raw monorepo Mypy invocation | BASELINE, NOT A FEATURE GATE | A naive invocation followed the entire monorepo and emitted 3,741 existing optional-dependency/import diagnostics. It was replaced by the scoped changed-production-file gate above, not represented as a feature regression. |
| Frontend Biome | PASS | The final committed branch surface contains 105 frontend source/config files; all 105 passed the repository-pinned Biome check without fixes. |
| Frontend TypeScript | BASELINE | Full TSC reported 247 repository diagnostics and zero in branch-changed files. |
| Affected frontend Jest | PASS | All 30 frontend test files changed by the final commit range passed: 30 suites, 234 tests, 0 failures/skips. This includes Share dialog, menu lifecycle, node-field ARIA, Teams, permissions, autosave, and folder mutation coverage. |
| Full frontend Jest | BASELINE | 664 suites passed and 2 failed; 7,083 tests passed and 2 failed. The two failures are pre-existing locale/timezone expectations in `sort-sender-messages.test.ts` and `dateTime.test.ts`. |
| Playwright utilities | PASS | 68/68 passed, including authz mode and report-manifest validation. |
| Frontend production build | PASS | 8,019 modules transformed; the final build completed in 1m36s with existing Tailwind/chunk warnings. |
| Authz Playwright discovery | PASS | Exactly 8 `@authz` Chromium tests were collected from one file. |
| Authz Playwright execution and IBM scan | PASS | All 8 journeys passed in 6.3m with the native enforcer, distinct users, one worker, zero retries, and strict IBM assertions. The embedded report records 8 expected outcomes, one attempt per journey, and retry index 0. Five named IBM reports contain zero violations. |
| Canonical OpenAPI | PASS | Generation completed without tracked drift; 12 authz route groups are present. |
| Documentation production build | PASS | Docusaurus generated the static site after the inherited shell-only `DEBUG=release` variable was removed and Windows SSG was constrained to one worker with server-bundle retention. A default-worker rerun compiled both bundles but lost the generated server bundle during SSG; the disclosed single-worker rerun passed. Existing unresolved workflow-schema references, browser-data age, sampler, and historical-anchor warnings remain non-fatal repository baselines. |
| Managed repository hooks | PASS WITH WINDOWS WRAPPERS | Case, EOF, line ending, whitespace, Ruff, migration/router, and other applicable hooks passed. The secret baseline's one existing finding moved from line 76 to 72; a normalized-baseline scan passed. Native pinned Biome commands passed because the Bash wrapper stalls on this Windows host. No hook configuration was weakened. |
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

- The two full-Jest failures are locale/timezone-sensitive baseline assertions, not authorization failures.
- The full TSC backlog contains no diagnostic in branch-changed files.
- The raw Mypy command was over-broad; the 51-file production delta is clean under the repository source layout.
- The combined Windows RBAC selection can retain a Chroma SQLite handle during teardown. The affected test passes in isolation, so this is recorded as a same-process cleanup limitation rather than an authorization assertion failure.
- The standard secret hook normalizes all baseline paths to backslashes on this host. The authoritative baseline received only the valid line-number update, and an equivalent temporary normalized-baseline scan returned zero.
- The local pre-commit Bash wrapper for Biome stalls on this Windows host. The same pinned native Biome check and staged lint both returned zero.
- A default-worker Docusaurus rerun lost `build/__server/server.bundle.js` after successful compilation. The one-worker, retained-bundle rerun completed static generation and broken-anchor validation with exit code zero.

## Migration, API, and immutable manifest

- Migration `bf6c22022777` extends existing tables and does not create parallel team/share models.
- Upgrade, legacy repair/backfill, metadata parity, constraints, and downgrade are covered on SQLite and PostgreSQL 16.
- Canonical OpenAPI generation contains capabilities, permissions, recipients, shares, summaries, teams/members, and dynamic resource paths.
- The implementation changes exactly 211 paths relative to the fork-main base:

```bash
git diff --name-status \
  e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5..dbb0c20e541aade230f85c564e1d74b28e628c23
```

Immutable comparison:

`https://github.com/waqoor/langflow/compare/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5...dbb0c20e541aade230f85c564e1d74b28e628c23`

## Final acceptance boundary

The integrated local candidate has implementation and runtime evidence for the native service, both database engines, migration/API contracts, frontend behavior, strict IBM accessibility scans, and all eight browser journeys. Hosted Python 3.10/3.14, ARM64 image, fork Actions aggregate, and any PR/merge SHA remain NOT RUN or externally blocked. They must not be described as passing until an authorized candidate is pushed and those systems produce evidence.

This record does not authorize unrelated baseline cleanup, a push, PR, merge, deployment, release, production configuration change, or credential change.
