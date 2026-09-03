# Native authorization, teams, and sharing verification record

**Canonical repository:** `https://github.com/waqoor/langflow` (ID `1353667234`)
**Plan/request URL:** `https://github.com/yazeedhasan97/langflow` (redirects to the canonical repository)
**Delivery branch:** `feat/auth-team-sharing`
**Fork-main base:** `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`
**Tested implementation commit:** `e7be0a60d53e75611870888f5af060b90adc8c97`
**Tested implementation tree:** `55320ad2171eb29124b8ec7d73aa5f4368fcb662`
**Migration:** `bf6c22022777`, down revision `c6d8e0f2a4b7`, phase `MIGRATE`
**Verification date:** September 3, 2026
**Status:** Local implementation candidate complete; fork CI, ARM64 image validation, and unsupported local Python matrix entries remain explicitly unverified.

## Scope and delivery boundary

The sole implementation authority is `auth_share_implementation_plan.md`, revision 1.2. The committed copy has SHA-256 `6b648457de1e62132bad19f05f08332e35b1bd7ad0b661d6e3f87b5f837a4899`; repository hooks normalized Markdown trailing spaces but did not change its requirements. This work implements only that plan.

- `origin` fetch/push is the canonical `https://github.com/waqoor/langflow.git`. GitHub redirects the plan's `yazeedhasan97/langflow` URL to this same repository; both API paths report ID `1353667234` and the same branch SHAs.
- `upstream` fetch is `https://github.com/langflow-ai/langflow.git`; its push URL is `no_push`.
- The feature branch contains fork `main` at the base SHA above and is five commits ahead, zero behind at the implementation commit.
- No merge to `main`, upstream PR, release, deployment, production setting change, or production credential use is part of this delivery.
- Playwright reports, temporary configuration, and temporary databases are local generated artifacts and are not committed.

## Implemented contract

The candidate extends the existing authorization interface, canonical authorization tables, flow/project routes, and frontend extension seams. It does not add another identity system, policy database, API version, resource copy path, or shadow implementation.

| Area | Implemented result |
|---|---|
| Native service | `LangflowAuthorizationService` performs canonical database-backed authorization when authorization is enabled. Default-off behavior remains unchanged. Cross-user fetch and SQL visibility prefilters activate only for the ready native service. |
| Teams | Atomic non-empty creation; per-membership `admin`, `maintainer`, and `user` roles; active-user/source rules; team-scoped management; row/advisory locks; final-member and final-active-admin invariants. |
| Sharing | Existing `AuthzShare` remains canonical. User/team recipients, direct flow and project grants, inherited current/future child access, effective-access summaries, recipient search, revision tokens, and durable mutation audit rows are implemented. |
| Resource safety | Read/run/edit are evaluated separately from share administration, publication, authentication settings, ownership, move, and deletion. Direct flow sharing does not expose a private parent or siblings. Secrets remain owner-bound. |
| Concurrency | Flow/project content and share mutations expose revisions. Enabled native-collaboration mutations require `If-Match`; missing/stale requests return `428`/`412`. The enforcement-disabled owner contract is not given a new mandatory header. |
| Execution | Shared execution retains the authenticated actor and existing dependency/public-principal restrictions. Revocation affects fresh admissions without waiting for an in-process cache broadcast. |
| Frontend | Platform-admin Teams route, team roster management, Shared With Me, reusable project/workflow Share dialog, recipient search, Can use/Can edit selection, effective-access explanations, owner labels, capability-gated menus, and structured conflict handling. |
| API discovery | Capabilities, recipient search, share summary, teams, shares, shared-resource projections, and per-resource effective permissions are typed and included in the generated OpenAPI artifact. |
| CI | Authz path selection, Python/database feature matrix, exact eight-journey Playwright selection, report validation, candidate-ref plumbing, mandatory aggregate dependencies, and fork-available ARM64 runner defaults are wired into existing workflows. |

### Intentional contract-change ledger

1. The fork's registered Langflow authorization service changes from pass-through to enforcing only when `LANGFLOW_AUTHZ_ENABLED=true`; disabled mode preserves owner-scoped behavior.
2. A committed team must be non-empty. An active team must have at least one active Admin. Creation supplies the valid initial roster atomically.
3. Team membership gains role/source semantics without mapping team roles to platform superuser or resource permissions.
4. Native enabled-mode flow/project/share writes use revisions and conditional requests. Missing and stale preconditions have distinct `428` and `412` responses.
5. The reusable API retains `read`, `execute`, `write`, and `admin`. The new dialog exposes only **Can use** (`execute`) and **Can edit** (`write`); it does not silently convert existing `read` or `admin` grants.
6. Resource list and direct-fetch behavior now admit authorized direct/team/project-inherited shares while preserving owner/public and UUID-privacy rules.
7. Mutation audit rows are staged with canonical changes. Post-commit publication/invalidation failure cannot turn a committed mutation into a false retry signal.
8. Authz browser mode uses distinct accounts, the real native service, a namespaced database/config/report path, serial execution, zero retries, and a required exact journey manifest.

## Verification results

All local PASS results below apply to the implementation tree identified above. Warnings and unrelated baseline failures are not silently converted into success.

| Check | Status | Actual result and boundary |
|---|---|---|
| Focused backend authorization/API suite | PASS | 353 passed, 0 failed, 0 skipped, 3 warnings across 11 affected files. |
| Pure policy matrix after final range formatting | PASS | 112 passed, 0 failed, 0 skipped, 1 existing deprecation warning in 0.88s. |
| RBAC production-service integration selection | PASS | 10 passed, 0 failed, 1 deselected, 1 warning in 102.19s. The deselected Chroma case is classified separately below. |
| LFX authorization service contract | PASS | 17 passed, 0 failed, 0 skipped, 4 warnings in an isolated LFX project environment. |
| SQLite migration matrix | PASS | 16 passed and 8 dialect-inapplicable skips; migration upgrade/backfill/downgrade and metadata checks executed on SQLite. |
| PostgreSQL 16 migration/model matrix | PASS | 23 passed, 1 dialect-inapplicable skip, 1 warning in 42.93s against disposable PostgreSQL 16.15. |
| PostgreSQL native collaboration/concurrency | PASS | 6 passed, 0 failed, 0 skipped, 1 warning against a fresh PostgreSQL database, including concurrent final-admin mutation protection. |
| CI contract scripts | PASS | Both authorization endpoint and execution-principal matrix generators/checkers passed. Their pytest contract suite passed 24/24 in 2.12s. |
| Changed workflow/config YAML parse | PASS | Eight changed YAML files parsed with PyYAML. |
| Ruff | PASS | Format and lint checks passed over all 62 changed/new Python files. |
| Focused authz Mypy | PASS | 24 production authorization source files: `Success: no issues found`. |
| Full `langflow` Mypy | FAIL | 50 inherited errors in optional deployment/tracing/Celery/import surfaces. Four diagnostics occur in touched files but on unchanged lines; none occurs in a plan-change hunk. See baseline classification. |
| Frontend Biome | PASS | Repository-pinned Biome 2.1.1 checked exactly 95 staged frontend files; no fixes. Staged no-`any` lint also passed all 95. |
| Frontend terminating TypeScript check | FAIL | 256 repository-baseline diagnostics, zero in plan-changed files. The normal script's Vite sidecar was not treated as a terminating typecheck. |
| Affected frontend Jest suites | PASS | 20 suites, 144 tests, 0 failures/skips. Includes dialog and Teams accessibility assertions. |
| Playwright utility tests | PASS | 68/68 passed, including authz mode and report-manifest checks. |
| Frontend production build | PASS | 8,019 modules transformed; build completed in 1m43s. Existing Tailwind mixed-unit and chunk/import warnings remain baseline warnings. |
| Authz Playwright discovery | PASS | Exactly 8 tests collected from one file for Chromium under `LANGFLOW_E2E_AUTHZ=true` and `@authz`. |
| Authz Playwright execution | PASS | 8 passed in 5.0m with one worker, 0 failed, 0 skipped, 0 retries/flaky results. |
| Canonical OpenAPI generation | PASS | Generation completed; the artifact contains 12 authz path groups covering capabilities, permissions, recipients, shares, summaries, and teams/members. |
| Documentation production build | PASS | Docusaurus production build completed after this evidence update. Existing `/api/v2/workflows` reference, browsers-data, sampler, and historical-version anchor warnings were non-fatal and remain outside this feature scope. |
| Staged repository hooks | PASS | Case, EOF, line endings, whitespace, Ruff, migration validator/phase, router trust, and secrets passed. Biome and staged no-`any` passed through the same pinned binary directly because Windows resolved the hook's `bash` entry to the WSL launcher and stalled. No hook/configuration was weakened. |
| `git diff --check` | PASS | Implementation commit range is whitespace-clean. |
| `actionlint` | NOT RUN | Tool is unavailable locally; changed YAML was parsed and repository workflow contract tests passed, but that is not `actionlint`. |
| Python 3.10 local runtime | NOT RUN | Interpreter is unavailable locally; the fork workflow matrix includes Python 3.10. |
| Python 3.14 full integration | BLOCKED EXTERNAL | Dependency preparation stopped while building locked `litellm==1.93.0`: the available Windows `link.exe` is not the required MSVC C++ linker/workload. No test executed in that environment. |
| ARM64 Docker candidate image | NOT RUN | Workflow is parameterized for `ubuntu-24.04-arm`, but no eligible fork Actions run was started locally. |
| Fork GitHub Actions candidate run | NOT RUN | No run/job/attempt URL or CI artifact exists for this candidate at the time of this record. Local PASS results are not represented as GitHub CI. |
| Upstream submission/acceptance | NOT APPLICABLE (not requested) | No upstream PR, maintainer review, merge queue, or upstream acceptance claim. |
| Deployment/merge | NOT APPLICABLE (outside plan delivery) | No deployment, release, or merge to fork `main` was performed. |

### Commands used for the primary evidence

```powershell
uv run pytest `
  src/backend/tests/unit/api/v1/test_authz_admin_authorization_ordering.py `
  src/backend/tests/unit/api/v1/test_authz_admin_routes.py `
  src/backend/tests/unit/api/v1/test_authz_lifecycle_contract.py `
  src/backend/tests/unit/api/v1/test_authz_share_routes.py `
  src/backend/tests/unit/api/v1/test_deployment_route_handlers.py `
  src/backend/tests/unit/api/v1/test_execution_principal_contract.py `
  src/backend/tests/unit/services/authorization/test_audit_retention.py `
  src/backend/tests/unit/services/authorization/test_authorization_service.py `
  src/backend/tests/unit/services/authorization/test_capability_flag.py `
  src/backend/tests/unit/services/authorization/test_collaboration_management.py `
  src/backend/tests/unit/services/authorization/test_flow_route_guards.py -q --tb=short

uv run pytest src/backend/tests/unit/services/authorization/test_rbac_enforcement_integration.py `
  -q --tb=short -k "not developer_can_create_files_and_knowledge_bases"

uv run --isolated --project src/lfx pytest `
  src/lfx/tests/unit/services/authorization/test_default_authorization_service.py -q --tb=short

uv run python scripts/ci/check_authz_endpoint_matrix.py
uv run python scripts/ci/check_execution_principal_matrix.py
uv run pytest scripts/ci/test_authz_endpoint_matrix.py `
  scripts/ci/test_execution_principal_matrix.py `
  scripts/ci/test_authz_workflow_contract.py -q --tb=short

uv run --with mypy mypy --namespace-packages -p langflow --no-error-summary --no-pretty

$env:LANGFLOW_E2E_AUTHZ = "true"
npx playwright test tests/core/features/authz --grep "@authz" --project=chromium --list
npx playwright test tests/core/features/authz --grep "@authz" --project=chromium --retries=0
npm run test:e2e-utilities
npm run build
```

PostgreSQL checks used a disposable `postgres:16` container on local port `55432`, synthetic test-only credentials, `uv sync --extra postgresql`, and a Windows selector event-loop wrapper for psycopg compatibility. The server reported PostgreSQL 16.15. The test database and container were removed after verification.

## Eight connected browser journeys

Runtime: Windows x64, uv Python 3.12.13, Node 24.16.0, npm 11.13.0, repository `@playwright/test` 1.60.0, Chromium 148.0.7778.96, SQLite, real `LangflowAuthorizationService`, separate admin/owner/direct-recipient/team-recipient accounts.

| Journey | Status | Connected outcome |
|---|---|---|
| `AUTHZ-JOURNEY-01` | PASS | Platform Admin creates a non-empty team; scoped roles control member UI. |
| `AUTHZ-JOURNEY-02` | PASS | Ordinary owner grants Can use; recipient can run but cannot save. |
| `AUTHZ-JOURNEY-03` | PASS | Owner upgrades the same grant; recipient edits graph content visible to owner. |
| `AUTHZ-JOURNEY-04` | PASS | Team project share covers existing, future, and collaborator-created workflows. |
| `AUTHZ-JOURNEY-05` | PASS | Removing team membership revokes fresh team access while ownership and another direct grant survive. |
| `AUTHZ-JOURNEY-06` | PASS | Downgrade rejects an already-open editor save and retains local unsaved content. |
| `AUTHZ-JOURNEY-07` | PASS | Concurrent editors produce one success and one stale-write conflict without replay. |
| `AUTHZ-JOURNEY-08` | PASS | Direct flow sharing exposes neither private parent project nor sibling workflows. |

Local outputs were written under `src/frontend/playwright-report-authz/`, `src/frontend/test-results-authz/`, `src/frontend/temp-authz`, and `src/frontend/temp-authz-config/`. They are intentionally untracked because they contain generated run state. The CI workflow uploads namespaced reports and validates the exact journey manifest; that CI artifact path is still NOT RUN.

## Requirements-to-tests map

| Requirement/scenario family | Primary evidence |
|---|---|
| `REQ-01`–`REQ-04`, `TEAM-*` | `test_team_share_policy.py`, `test_collaboration_management.py`, `test_authz_admin_routes.py`, team dialog/details Jest suites, journeys 01 and 05. |
| `REQ-05`–`REQ-08`, `SHARE-*` | `test_authz_share_routes.py`, `test_authorization_service.py`, resource Share dialog/custom-seam Jest suites, journeys 02, 03, 05, and 06. |
| `REQ-09`, `PROJ-*` | Native collaboration/RBAC integration tests, flow/project guard tests, journey 04. |
| `REQ-10`–`REQ-11`, `AUTH-*`, `WRITE-*` | RBAC integration, capability/route tests, flow save/autosave/delete and folder mutation Jest suites, journeys 02, 03, 05, 06, 07, and 08. |
| `REQ-12`, `RUN-*` | `test_execution_principal_contract.py`, deployment handler tests, execution-principal matrix and checker, journeys 02 and 08. |
| `AUDIT-*` | `test_audit_retention.py`, lifecycle route tests, collaboration/share mutation tests. |
| `MIG-*` | `test_authz_team_sharing_migration.py`, repository migration execution suite, SQLite and PostgreSQL results above. |
| `REG-*` | LFX default-service tests, 353-test affected backend suite, 20 Jest suites, frontend build, both CI matrix checkers, workflow contract tests, and exact eight-journey discovery/execution. |

The map identifies primary coverage; it does not inflate parameterized unit cases into additional browser journeys or claim unexecuted CI/architecture combinations.

## Baseline and blocker classification

### Full Mypy baseline

The full package command reports 50 errors across existing optional integrations such as deployments, tracing, Celery, and duplicate `langwatch.dspy` module discovery. Four diagnostics name touched files but are outside changed hunks:

- `src/backend/base/langflow/__main__.py:46` and `:47`: missing `multiprocess` stubs.
- `src/backend/base/langflow/__main__.py:1288`: missing `pyperclip` stubs.
- `src/backend/base/langflow/services/utils.py:30`: missing `lfx.services.settings.manager` import target.

The implementation changes in those files are at different lines. The focused 24-file authorization Mypy run is clean. These baseline errors were not repaired because they are outside the approved plan.

### Full TypeScript baseline

The terminating compiler run reports 256 existing repository diagnostics and zero in the plan-changed frontend paths. The 95 changed files pass Biome, staged no-`any`, affected Jest, and the production build. The unrelated compiler backlog was not modified.

### Remaining RBAC integration case

`test_developer_can_create_files_and_knowledge_bases` reached Windows cleanup with a Chroma SQLite file still locked and raised `PermissionError [WinError 32]` for a temporary `chroma.sqlite3`. It did not reach an authorization assertion failure. The other ten RBAC cases passed. Storage cleanup was not changed because it is unrelated to the authorization plan.

## Migration and API artifact evidence

- Migration `bf6c22022777` extends the existing tables; it does not create parallel team/share models.
- Upgrade, legacy backfill, model parity, constraints, and downgrade were exercised on SQLite and PostgreSQL 16.
- The PostgreSQL native-service suite exercised direct, team, and inherited project evaluation plus concurrent final-admin protection against real database locks.
- `docs/openapi/openapi.json` was generated from the candidate. New path groups include `/api/v1/authz/capabilities`, `/me/permissions`, `/recipients`, `/shares`, `/shares/summary`, and `/teams` with dynamic share/team/member paths.

## Exact file manifest

The candidate changes exactly 183 paths relative to the fork-main base. The immutable authoritative manifest is produced by:

```bash
git diff --name-status \
  e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5..e7be0a60d53e75611870888f5af060b90adc8c97
```

The corresponding immutable comparison is:

`https://github.com/waqoor/langflow/compare/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5...e7be0a60d53e75611870888f5af060b90adc8c97`

The manifest covers only these plan-owned groups:

- fork instructions/configuration and nine existing CI/workflow files;
- the implementation plan, this verification record, seven affected documentation pages, and generated OpenAPI;
- authorization/execution matrices and their CI contract tests;
- LFX authorization context/settings;
- the native backend authorization repository/service/policy/team/share/concurrency/lifecycle layers;
- the one additive migration, existing flow/project/user/deployment route integration, schemas, CLI preflight, and affected backend tests;
- frontend authorization query/mutation hooks, permissions, Teams, Shared With Me, Share dialog/menu integration, revisions/conflict handling, seven locale files, affected component tests, and the eight-journey Playwright harness.

## Final acceptance boundary

Local production-service behavior, both database engines, the exact eight browser journeys, affected tests, frontend build, generated OpenAPI, lint/format, and scoped typing are evidenced as PASS. GitHub-hosted Python 3.10/3.14, ARM64 Docker image validation, fork Actions aggregate checks, and any PR integration/queue SHA remain NOT RUN or BLOCKED EXTERNAL exactly as listed above. They must not be described as passing until an eligible fork run exists.

This record authorizes no scope expansion to repair the repository-wide Mypy, TypeScript, Chroma cleanup, optional integration, or dependency-toolchain baselines.
