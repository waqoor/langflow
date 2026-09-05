# Native authorization, teams, and sharing verification record

**Canonical repository:** `https://github.com/waqoor/langflow` \
**Delivery branch:** `feat/auth-team-sharing` \
**Fork-main base:** `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5` \
**Feature acceptance candidate:** `9896d8f024713d671a71be3a644869b4732e9934` \
**Feature candidate tree:** `a6bf170e17c7beb6658aec7296be4bffe1c362e7` \
**Fixture correction candidate:** `ca12f44f272797cf39e5348ad15244915ab9c49c` \
**Fixture candidate tree:** `e8883c81d656fcc7d8d55ce25b289b6ec4d248b6` \
**Migration:** `bf6c22022777`, down revision `c6d8e0f2a4b7`, phase `MIGRATE` \
**Verification date:** September 5, 2026 \
**Status:** Scope corrections are implemented and committed. All eight journeys, their report gate and the four native database/Python jobs passed on hosted candidate `9896d8f024`; the feature's four IBM scans report zero violations. The deletion-fixture corrections in `ca12f44f27` passed local and hosted checks. [CI run 33939382192](https://github.com/waqoor/langflow/actions/runs/33939382192) subsequently exposed a contribution regression in the first-request external sign-in permissions lookup. The narrow session-dependency fix passed all 121 existing login and authorization-route tests locally; its hosted validation remains pending. Overall acceptance is not yet claimed.

## Scope-corrected candidate evidence

| Check | Status | Exact evidence and boundary |
|---|---|---|
| Native SQLite, Python 3.10 | PASS | [242 passed, no failures/skips](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736082), candidate `9896d8f024`, 216.80 seconds. |
| Native SQLite, Python 3.14 | PASS | [242 passed, no failures/skips](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736110), candidate `9896d8f024`, 179.76 seconds. |
| Native PostgreSQL 16, Python 3.10 | PASS | [242 passed, no failures/skips](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736097), candidate `9896d8f024`, 247.04 seconds. |
| Native PostgreSQL 16, Python 3.14 | PASS | [242 passed, no failures/skips](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736105), candidate `9896d8f024`, 169.88 seconds. |
| Local connected browser journeys | PASS | Candidate `a96d823c10`: 8 collected/executed/passed in 7.9 minutes, one worker, zero retries, real distinct users and native enforcement. Local tracing was disabled; assertions and strict IBM scans remained enabled. The four current reports show zero violations and 7,201 passing checks. The stale, removed whole-editor scan report is excluded. |
| Final hosted connected browser journeys | PASS | [Execution job 101225941476](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225941476) and [report gate 101228192607](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101228192607), candidate `9896d8f024`: eight collected/executed/passed, zero skipped/failed/flaky, one worker, zero retries, full traces, 11.2 minutes. JSON artifact `9960840882` records these counts. |
| Final hosted feature accessibility | PASS | IBM checker 4.0.26: four feature reports, zero violations and 6,558 passing checks. Artifact `9960658836` contains Teams administration, member Teams, Shared With Me and the populated Share dialog; no whole-editor acceptance scan or unrelated graph repair is included. Runtime: Playwright 1.60.0 / Chromium 148.0.7778.96, hosted Node 22 / Python 3.13. |
| CI script contracts | PASS | [157 passed](https://github.com/waqoor/langflow/actions/runs/33934796737/job/101220505367), candidate `5c269be67c`, four upstream warnings. |
| Full TypeScript comparison | FAIL (existing baseline) | `a96d823c10`: 252 diagnostics versus 254 on clean fork base; no introduced diagnostics, two resolved by required contract types. Generic sidebar typing cleanup was removed. This is not a claim that full TSC passes. |
| Scoped backend Mypy | PASS | Nine native authorization contract modules passed with explicit backend/LFX paths and skipped import traversal after the scope removals. This is not a full-monorepo typing result. |
| Scope-removal regressions | PASS | 16 backend destination/publication cases, 63 frontend cases in five suites, 7 sidebar cases, and 81 browser utility cases passed. The original exact folder-store equality assertion passed separately. |
| Full project route regression file | PASS | Candidate `9896d8f024`: 66 passed, one existing skip and one upstream warning in 619.52 seconds. The corrected starter-project fixture passed. `test_read_projects_empty` retains its pre-existing skip when default projects exist; it is not counted as executed coverage. |
| Flow retry fixture follow-up | PASS | Test-file content committed in `ca12f44f27`, command `uv run --no-sync pytest src/backend/tests/unit/api/v1/test_flows.py -q --tb=short`: all 90 existing tests passed with one upstream warning in 791.29 seconds on local Python 3.12 / SQLite. Both adjusted fixtures retain their original assertions and use the real rollback before the competing write. The earlier targeted bulk-delete run passed four tests with 86 deselected. No production code or native acceptance test changed. |
| External sign-in permissions regression | PASS | The unchanged existing test first failed locally with 401. After reusing authentication's `DbSession` for the permissions route, `uv run --no-sync pytest src/backend/tests/unit/test_login.py src/backend/tests/unit/api/v1/test_authz_admin_routes.py -q --tb=short` passed all 121 tests with one upstream warning in 137.71 seconds. No test expectation changed. |
| Permissions-session correction quality checks | PASS | Ruff formatting left the single changed source unchanged; all applicable two-file pre-commit hooks passed. Scoped Mypy passed `authz_me.py` with explicit backend/LFX package paths and skipped import traversal. |
| Final frontend Jest | PASS | [566 suites, 6,654 tests passed](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760742), candidate `ca12f44f27`, 1,208.09 seconds. This workflow excludes its separately owned accessibility suites; focused local accessibility checks are recorded separately. |
| Inherited core browser regression | PASS | Candidate `ca12f44f27`: all 35 shards succeeded; the [merged report gate](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101237789932) validated 173 collected, 161 passed, 12 skipped, zero failed and zero flaky tests. The skips retain existing auto-login, optional-bundle, credential and disabled-test conditions; none is counted as feature acceptance. JSON artifact `9961820574` records the counts. |
| Completed inherited backend unit groups | PASS | `9896d8f024`, Python 3.14: [group 1](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736555) has 2,696 passed / 124 skipped / three expected failures; [group 5](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736571) has 2,684 passed / 139 skipped. Each required one inherited pytest rerun: `test_database.py::test_create_flow` and `test_facade_real_services.py::test_startup_terminalizes_unavailable_encrypted_overrides[sqlite-missing]`, respectively. Their causes are unclassified; these are not clean first-attempt results or proof of baseline defects. |
| Final LFX regression suite | PASS | `ca12f44f27`: [Python 3.10](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760707) has 8,046 passed / 60 skipped in 406.64 seconds; [Python 3.14](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760660) has 8,049 passed / 57 skipped in 275.13 seconds. Each retains five existing expected failures and one unexpected pass; no new skip/xfail was added for this contribution. |
| Final backend integration | PASS | `ca12f44f27`: [Python 3.10](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760809) and [Python 3.14](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760671) each passed 76 tests, with eight existing skips and 65 deselections in the inherited workflow. |
| Final bundle-installed regression | PASS | `ca12f44f27`: [Python 3.10](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760659) and [Python 3.14](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760695) each passed 299 tests with 62 skips and 19 deselections, followed by 10 passing HTTP-entrypoint tests. |
| Inherited release-dependent CLI checks | NOT RUN | The jobs report success, but their test steps skip because version `1.12.0` is not published. This applies to `9896d8f024` ([Python 3.10](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736395), [Python 3.14](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736321)) and `ca12f44f27` ([Python 3.10](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760713), [Python 3.14](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760703)). They are not executed CLI coverage; the existing release condition is unchanged. |
| Final ARM64 candidate image | PASS | [Job 101233760701](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760701) passed on its first attempt for `ca12f44f27`; the conditional retry job correctly skipped. |
| Final documentation build | PASS | [Job 101233760779](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760779), candidate `ca12f44f27`. |
| Inherited documentation accessibility job | PASS | [Job 101233760716](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760716), candidate `ca12f44f27`, completed under its existing warning policy. The log includes scan retries and warnings that accessibility violations were found. This is not a zero-violation result for the documentation site; no general documentation accessibility repair is included. The four strict feature reports remain separate above. |
| Final starter-template checks | PASS | [Job 101233760511](https://github.com/waqoor/langflow/actions/runs/33939382192/job/101233760511), candidate `ca12f44f27`: 232 passed, 12 skipped and three warnings in 458.45 seconds. |
| Candidate hooks | PASS | The three-path delta committed in `9896d8f024` passed all applicable repository hooks using Git Bash on Windows, including Ruff, both Biome hooks and secret scanning. A preceding WSL Bash invocation passed an empty filename to Biome; its incidental formatting was reversed before the successful scoped run. |
| Fixture correction hooks | PASS | `ca12f44f27`: `uv run --no-sync pre-commit run --files docs/auth-team-sharing-verification.md src/backend/tests/unit/api/v1/test_flows.py` passed every applicable hook, including Ruff and secret scanning. Unrelated hooks reported no files to check. The eight pre-existing frontend working-tree edits are unchanged and excluded from the commit. |

Candidate `9896d8f024` changes only the project-session test fixture, five Teams page-readiness assertions and this ledger after `a96d823c10`. The latter restores the unrelated sidebar typing change and scopes the Share-dialog scan fixture after `5c269be67c`. Each result above identifies its actual checkout explicitly; earlier results are not relabelled as tests of the final commit. The separate browser [run 33935909962](https://github.com/waqoor/langflow/actions/runs/33935909962) also passed all eight journeys and report validation on `9896d8f024` before the full CI browser job completed.

Full run `33936593227` finished with 66 successful jobs, six skipped, seven backend unit jobs cancelled by the inherited fail-fast matrix, and two failed. The failing [Python 3.14 group 3](https://github.com/waqoor/langflow/actions/runs/33936593227/job/101225736492) reported one failure, 595 passes, 52 skips and six reruns on its last inherited action attempt. `test_bulk_delete_retry_rebuilds_authorized_owner_map` tried a competing SQLite delete while the request held its writer transaction; the competing write failed with `database is locked`, so the final deleted count was two instead of one. `CI Success` correctly rejected the run. The five Python 3.10 unit groups and Python 3.14 groups 2 and 4 were cancelled, not passed. The two follow-up fixture changes move the competing write after the real retry helper's rollback, retaining the original assertions and production behavior; their test-contract entries below were recorded before editing, and the full local flow file now passes.

The incremental run `33939382192` uses exact candidate `ca12f44f272797cf39e5348ad15244915ab9c49c`, comparison base `9896d8f024713d671a71be3a644869b4732e9934`, Python 3.10/3.14, `tests/core`, `run-all-tests=false`, and `release=false`. That actual delta contains only `test_flows.py` and this record. Plan Section 23.11(5) requires rerunning checks affected by a final change; the unchanged selectors choose the affected jobs. Native/backend feature tests, browser tests and all production sources are byte-identical to `9896d8f024`; their earlier results above retain that SHA and are not presented as executions on `ca12f44f27`. The fork-main base remains `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`.

Run `33939382192` finished with 61 successful jobs, eight skipped, four cancelled and two failed. Python 3.14 group 4 and the correctly rejecting `CI Success` failed. The group's first inherited action attempt logged one failure / 2,330 passes / 138 skips / one expected failure / five reruns; its second logged one failure / 339 passes / 42 skips / five reruns. Both failed the unchanged `test_login.py::test_external_access_ceiling_filters_effective_permissions` with 401 instead of 200. The contribution had added a canonical active-user lookup through a separate session, which could not see a JIT-created external user in authentication's still-open request transaction. The follow-up changes only the permissions route to reuse that existing transaction. Python 3.10 groups 1, 2, 4 and 5 were cancelled by the inherited fail-fast matrix and are not counted as passes. The two corrected deletion fixtures passed first-attempt on Python 3.14 in groups 2 and 3.

The complete earlier run [33934794698](https://github.com/waqoor/langflow/actions/runs/33934794698) finished with 61 successful jobs, eight skipped, nine backend jobs cancelled by the inherited fail-fast matrix, and four failed. Failures were the project-session fixture, J1's five-second Teams readiness assertion, its rejecting report gate, and `CI Success`. Both underlying causes are recorded in the ledger and corrected in `9896d8f024`. The final CI dispatch uses `run-all-tests=false`, `base-ref=e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`, Python 3.10/3.14, `tests/core`, and the existing hosted Linux/ARM64 runners; no path selector or gate was weakened. The fork base and pushed candidate were rechecked before dispatch.

## Previous hosted candidate validation

The full build/test run [33933277196](https://github.com/waqoor/langflow/actions/runs/33933277196), attempt 1, used historical candidate `41d269885bd9c968bf41a0f3274448ac902ecefe`, tree `05c465c1b76a3862fb705367b7aaae7bdc3cc346`, and was cancelled when the scope-correction candidate was dispatched. It is incomplete evidence, not final acceptance. No release or deployment was enabled.

The separate [CI Scripts Tests run 33933278780](https://github.com/waqoor/langflow/actions/runs/33933278780/job/101216133018) on the same candidate passed all 157 tests with four upstream warnings. Native acceptance passed 246 cases on Python 3.10 with both engines and Python 3.14 with SQLite. [Python 3.14 / PostgreSQL](https://github.com/waqoor/langflow/actions/runs/33933277196/job/101216145957) failed the project PUT commit-visibility assertion after 72 passes. Core browser shard 13 separately failed before test execution when `setup-uv` timed out fetching its version manifest. Neither failure is counted as passing acceptance.

## September 5 continuation

Work continues on `feat/auth-team-sharing` from `b86381ec3b`. The objective authorizes feature-branch delivery and fork build/test validation. The eight pre-existing, unrelated working-tree edits remain user-owned and excluded from feature commits. `main`, the authoritative plan, and production configuration remain unchanged.

### Scope correction requested by the contributor

The user's September 5 correction limits the patch to the plan and defects caused by this contribution. The complete branch inventory was checked against Sections 1, 12-19 and 23. The following extra work is removed rather than retained as general project maintenance:

| Removed work | Scope reason | Required coverage retained |
|---|---|---|
| Generic HTTP response-before-commit test added in `c68aa684fd` and its uncommitted creation variants | The fork base already defers these commits to dependency teardown; the plan requires atomic revision checks, not a general response-timing redesign. No proposed transaction cleanup was applied. | Native sharing, missing/stale revisions, concurrent saves/deletes, collaborator redaction, and project inheritance. |
| Global node/parameter DOM-ID encoding and its added helper/component tests | The existing graph label defect is independent of team/resource sharing. Restore the original components/helper and preserve their original tests. | Functional read-only editor and execution checks, plus existing component accessibility regressions. |
| Additional whole-editor IBM scan in J2 | The plan requests accessibility checks for this feature's controls; it does not require remediation of the existing graph editor. | All eight functional journeys, and IBM scans for Teams, Shared With Me and the Share dialog. |
| Global Vite artifact-watcher exclusion and its dedicated test/export | This is a general Windows development-runner workaround. | The plan's isolated authorization database/configuration/report paths and unchanged normal browser selection. |
| Incidental typing cleanup in existing exception traversal, service imports, role/audit query expressions, the sidebar import parser, flow-naming helpers and folder-store declarations | These edits are independent of the new authorization and revision contracts. | New contract types, enforcement/credential checks and required revision fields remain. |

Restoring the old folder-store fixture's `as any` failed the existing staged no-any hook. Section 23.8 explicitly requires that hook to remain effective, and this file needs the new project revision fields. The fixture therefore keeps a typed flow value, while its original exact-equality assertion is restored instead of the later partial-match assertion. No lint rule or check was weakened.

Focused validation after these removals passed 16/16 backend destination/publication cases (before correction: 6 failed, 10 passed), 63/63 frontend cases in five suites, and 81/81 browser utility cases. The exact folder-store fixture comparison also passed its separate rerun. Applicable repository hooks passed, including both Biome hooks and secret scanning. These are focused results; the final eight-journey and hosted results must be recorded separately.

The first scoped browser run on `5c269be67c` passed J1/J2 and all J3 sharing/editing assertions, then failed its full-page Share-dialog scan on two pre-existing graph label IDs behind the dialog; J4-J8 did not run. The dialog scan now uses a separate empty workflow with a real editable user grant. This preserves the new dialog's populated grant controls and strict scanner assertions while the earlier part of J3 still proves editing and owner-observed persistence on the runnable graph. No graph fix, rule suppression or blanket baseline was added.

The CI candidate started immediately before the newly downloaded backend failure log was inspected (`33934265802`, commit `57199b480a`) was cancelled during setup. It is not acceptance evidence. Further validation follows the scoped patch; unrelated upstream failures are recorded without product fixes.

The new regression cases first demonstrated these failures:

- An unready native service could weaken mandatory write preconditions and return owner capabilities.
- Effective-permission discovery could invent unsupported actions for resource owners.
- Collaborator PATCH/PUT responses, including no-op responses, could expose owner credentials. Restoring a redacted value could also retain client-modified metadata that removed its secret classification.
- A previously loaded project ORM instance could validate a stale revision.
- Cached successful permission/share queries could keep mutation controls enabled after a failed refetch.
- A successful save with newer local graph edits could leave those edits carrying the old revision.
- Concurrent SQLite saves, bulk-flow deletes, and project deletes could lose the revision race when audit writes were disabled.
- The PostgreSQL CI setting did not reach the HTTP application's database fixture. HTTP clients now use private PostgreSQL databases when that engine is selected, and assert the running engine's dialect.

Earlier continuation results before scope removal (all commands used their locked checkout; the current table above takes precedence):

| Check | Observed result |
|---|---|
| Full frontend Jest with `TZ=UTC` | 667 suites and 7,097 tests passed; zero failures. |
| New frontend regressions | 3 suites, 40 tests passed after the fixes. |
| Authorization regression selection excluding the separately run native HTTP and collaboration files | 422 tests passed. |
| Concurrent native HTTP saves | Both resource types and both audit modes passed: 4/4. |
| Concurrent native HTTP deletions | Before fixes: 2 failures and 4 passes. The local rerun encountered a Windows package-discovery timeout in setup. All six cases subsequently passed on both engines and Python versions in hosted native acceptance. |
| Additional generic HTTP success-response transaction observation | OUT OF SCOPE. The initial four-case observer passed locally but failed on hosted PostgreSQL. A stronger local route observer produced 5 failures and 3 passes, exposing dependency-teardown commit timing already present in the fork base. These newly introduced generic assertions are removed in response to the user's scope correction; no upstream transaction cleanup is included and no failure is reclassified as passing. |
| Browser acceptance | First current run: J1/J2 passed, J3 failed on owner-observed graph content, J4-J8 did not run. The trace-enabled rerun passed all eight. The final run on `c68aa684fd` also passed all eight with the stronger J3 request/response correlation assertion, one worker, zero retries and strict IBM scans. |
| Existing account CRUD browser journey | Passed with one worker and zero retries after explicit owner-scoped cleanup of the default project and login-created variables. The 409 ownership rejection, successful delete/recreate/rename, user login and cross-user flow isolation all remain asserted. |
| Canonical OpenAPI generator | Output is byte-identical to `docs/openapi/openapi.json`. |
| Feature Biome | 116 files passed. The three diagnostics in a wider working-tree check belong to untouched message-query files with user-owned edits. |
| Scoped Mypy | 9 changed production files passed using explicit backend/LFX package paths, the workspace Python executable, and skipped import traversal. |
| Full TypeScript comparison | Clean fork base: 254 errors. Candidate: 247 errors. After normalizing checkout paths, no new diagnostics and 7 resolved diagnostics. |
| CI scripts | 152 passed and 4 failed on Windows. All four failures reproduce in the clean fork-base checkout: bundle-release planning uses Windows separators in Git object paths. Authz/endpoint/principal contract selection passed 24/24. |
| LFX default service | 17/17 passed in an isolated LFX environment. |
| Assistant MCP runner/component baselines | 39/39 passed after correcting synchronous database-bind mocks; existing assertions are unchanged. |
| Repository pre-commit hooks | Applicable hooks passed over all 230 feature paths, including the final CI/report changes. Secret scanning required two explicit synthetic-test-value annotations and five existing baseline line-number updates; all 853 secret identities and classifications are unchanged. |
| Playwright utility and workflow contracts | 82/82 utility tests and 6/6 workflow contract tests passed; actionlint passed for both revised reporting workflows. |
| Frontend production build | Passed. |
| Documentation production build | Passed after removing the inherited `DEBUG=release` variable from the child process. Existing OpenAPI-reference and historical-anchor warnings remain. |

Hosted run [33931056991](https://github.com/waqoor/langflow/actions/runs/33931056991), attempt 1, checks out exactly `c0a9e4823520c6d5be67086a4234a9c705f1b43d`:

| Check | Observed result |
|---|---|
| Python 3.10 / PostgreSQL 16 | [242 passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209591821), zero skipped/failed. |
| Python 3.10 / SQLite | [242 passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209591920), zero skipped/failed. |
| Python 3.14 / PostgreSQL 16 | [242 passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209591728), zero skipped/failed. |
| Python 3.14 / SQLite | [242 passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209591808), zero skipped/failed. |
| Required sharing browser execution | [8/8 passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209831295), 9.1 minutes, one worker and zero retries. The report-validator job failed because the single downloaded artifact had no enclosing artifact-name directory. The revised resolver handles this layout while retaining complete-report and exact-journey validation. |
| ARM64 Docker images | [Passed on the first attempt](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209592111). |
| Documentation build | [Passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209591970). The separate [IBM docs scan also passed](https://github.com/waqoor/langflow/actions/runs/33931056991/job/101209592012). |
| Broad backend unit group | Two existing assistant session mocks fail after the common flow guard starts inspecting the database dialect. Fixture-only corrections retain the locked-flow assertions and require a fresh CI run. Other unit groups were cancelled by the existing matrix fail-fast setting. |
| Broad browser regression | The user CRUD journey failed because a newly created account owns a default project and cannot be implicitly cascade-deleted. The revised journey first verifies the 409 ownership impact, then explicitly removes its own project through an independent owner session before retaining the successful delete/recreate and flow-isolation assertions. |
| Full run / CI Success | FAIL: 60 jobs succeeded, 8 were skipped, 9 were cancelled by the backend matrix, and 5 failed (the backend unit group, one core browser shard, both report gates, and CI Success). The core report gate correctly rejected the failed CRUD journey; the authz report gate failed on the sole-artifact layout. |

Evidence logs are under the local temporary directory `langflow-authz-20260905-current`. The clean comparison checkout is detached at the exact fork-main base above. Later sections retain the prior candidate's history; their PASS labels must not be transferred to the current candidate without the final reruns.

The standalone Linux [CI Scripts Tests run 33932889216](https://github.com/waqoor/langflow/actions/runs/33932889216) on `fbafc5cac71fc9e49827d1dfffadb6816f317863` passed all 157 cases, including the four Windows-specific failures described above. Full run [33932888030](https://github.com/waqoor/langflow/actions/runs/33932888030) on that candidate was cancelled during early execution after the local CRUD test revealed that login-created variables also require explicit disposal. It is not acceptance evidence. The corrected CRUD test subsequently passed locally; the final candidate requires a fresh complete hosted run.

## Scope and delivery boundary

The sole implementation authority is `auth_share_implementation_plan.md`, revision 1.2. Its committed SHA-256 is `6b648457de1e62132bad19f05f08332e35b1bd7ad0b661d6e3f87b5f837a4899`.

- `origin` is the user fork, `https://github.com/waqoor/langflow.git`.
- `upstream` is read-only for this work: fetch is `https://github.com/langflow-ai/langflow.git` and push is disabled.
- The implementation descends from the exact fork-main base above.
- No parallel identity system, policy database, API version, resource-copy path, or shadow authorization runtime was added.
- The feature branch was pushed to the fork and its build/test workflow was dispatched. No pull request, merge to `main`, release, deployment, production setting change, or production credential use was performed.

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

### Historical accessibility changes in `dbb0c20e54` (scope removals noted)

- The global node/field DOM-ID encoding change was later removed as unrelated to this contribution.
- Workflow and project share-dialog state is owned by the persistent toolbar/card/sidebar surface. The originating Radix menu now closes before the modal opens, so its portalled menu is not left exposed outside a landmark behind the dialog.
- The extra node-ID coverage was removed; dropdown-to-dialog lifecycle coverage remains.

### Final consistency and Windows acceptance repairs in `170dd9e1d2`

- Team, user-lifecycle, and share writers now follow the documented cross-entity order: plugin preflight, UUID-sorted users, UUID-sorted teams/resources, and then memberships/shares. Unlocked identifier hints are re-read under canonical locks and boundedly replayed if the lock set changed.
- SQLite writers establish the database-wide writer transaction before authoritative invariant reads. PostgreSQL locked ORM reads use `populate_existing` so an identity-map object loaded for the preliminary hint cannot bypass the post-lock canonical state.
- A stale share whose user or team recipient is no longer eligible remains revocable, while create/update continue to reject an ineligible recipient. Multi-resource cleanup locks all share rows once in UUID order.
- The Share dialog and Team details were split into focused subcomponents below the repository complexity threshold. Team-member pagination uses a 51-row lookahead for 50-row pages and resets when the selected team changes; inline mutation errors are announced.
- The general Vite generated-artifact watcher workaround and its added test were later removed as out of scope. Local scoped acceptance uses `--trace=off`; hosted Linux acceptance retains full traces.

## Prior candidate verification results

The following results were recorded for prior commit `170dd9e1d2e5024d484769515b7bb2c511f6ef77`, tree `ae6fbd4713f182f55c4b77f13a73320e84cb2002`. Current candidate results and unresolved failures take precedence. Where a Windows runner required a split run, that boundary is stated rather than hidden.

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

## Prior candidate: eight connected browser journeys

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

## Prior candidate: baseline and runner classification

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
- Candidate `ca12f44f27` changes exactly 224 paths relative to the fork-main base (24,287 insertions and 2,373 deletions). This includes the two existing retry-fixture corrections after feature candidate `9896d8f024`; a subsequent documentation-only commit updates this record:

```bash
git diff --name-status \
  e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5..ca12f44f272797cf39e5348ad15244915ab9c49c
```

Immutable comparison:

`https://github.com/waqoor/langflow/compare/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5...ca12f44f272797cf39e5348ad15244915ab9c49c`

## Final acceptance boundary

The native matrix and browser acceptance passed on `9896d8f024`. The deletion fixtures are corrected in `ca12f44f27`; the subsequent permissions-session regression is fixed locally with its original tests passing. Hosted acceptance of that final correction and the cancelled unit groups remains pending. Unrelated failures and cleanup are outside the contribution.

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
| Additional generic HTTP response-before-commit assertions, introduced in `c68aa684fd` and extended locally | User's explicit scope correction; plan 14 requires atomic revision checks but does not mandate a generic ASGI response-timing redesign | Remove only this continuation's extra test function and abandon the proposed general transaction cleanup. The fork base already uses `flush()` plus request-dependency commit in these routes/helpers. Record the failed observation as an excluded upstream behavior, not a fixed contribution defect. | No upstream test is removed. All required missing/stale revision, concurrent save/delete, native enforcement, collaborator-response redaction, creation and inheritance cases remain. The required hosted selection returns from 246 to 242 cases. |
| `test_flows_helpers.py` PATCH publication denials expect individual field names | 12.3 | The contribution's shared-editor guard rejects both publication changes with its canonical ownership/publication message before the older field-specific branches. Update only those message expectations. | Keep both 403 assertions and verify the stored publication flag and card remain unchanged. Existing PUT field-specific assertions stay intact. |
| `test_flow_folder_integrity.py` explicit missing destinations fall back to a default folder | 12.2, 12.5 | Align create, PATCH, batch and upload expectations with the plan's explicit-destination rejection. Use omitted destinations for successful canonical-default tests; retain rejected import and rejected move cases. | Successful default creation/import still validates ownership and canonical workspace; rejected requests create no flow or preserve the original flow. Existing valid-destination, zero-folder, orphan adoption and PUT rejection cases remain. |
| J3 Share-dialog accessibility fixture scanned an unrelated populated graph in the page background | 16.7, 23.8 and the user's scope correction | Scan the same dialog on an empty workflow with a real editable grant, excluding the pre-existing graph-label defect from this contribution's acceptance scope. | Retain all runnable-graph editing and persistence assertions, a populated editable-grant row in the dialog, all eight journeys, zero retries, and strict feature-control accessibility assertions. |
| Teams route readiness assertions use Playwright's default five-second limit | 16.1-16.2, 19.5 | Hosted run `33934794698`, job `101220802307`, stopped J1 while the page showed `Checking authorization`. Its trace records successful session/capability responses and a successful team-list response about 65 ms after the assertion deadline. Use the harness's existing `TIMEOUTS.standard` page-load limit for the five Teams route-root assertions; do not change application behavior. | Keep visible-page, role-specific enabled/disabled controls, non-empty roster, distinct-user, strict accessibility, all-eight-journey and zero-retry assertions. This is a readiness wait, not a five-second performance requirement in the plan. |
| J3 autosave response matching | 14.3, 19.5 | The edit journey previously accepted the first workflow PATCH response, which could belong to editor hydration. Require the user's unique marker in both the submitted graph and successful response. | The owner API read and owner editor must still show the same marker; all eight journeys, real requests, and zero retries remain required. |
| Assistant MCP runner and component-update session fixtures | 14.1-14.2, 15.3 | Existing untyped `AsyncMock` sessions incorrectly model SQLAlchemy's synchronous `get_bind()` as async. Declare their PostgreSQL dialect when the shared flow guard inspects the engine. | Locked-flow cases must still refresh under `FOR UPDATE`, reject the write and skip persistence; the assistant commits only the pre-run transaction release. Native SQLite/PostgreSQL HTTP acceptance covers actual database locking. |
| `test_projects.py::test_update_project_cannot_rename_system_starter` session fixture | 14.1-14.2, 15.3 | Hosted job `101220526842` fails before its starter-project assertion because the contribution's locked project fetch calls synchronous `get_bind()` on an untyped `AsyncMock`. Supply the fixture's PostgreSQL dialect with a synchronous mock, matching SQLAlchemy. | Retain the existing 403 status and cannot-be-renamed message assertions. The protected starter project and production locking behavior are unchanged. |
| `test_flows.py::test_bulk_delete_retry_rebuilds_authorized_owner_map` competing-write timing | 14.2, 15.3 | Hosted job `101225736492` shows the simulated competing delete failing with SQLite `database is locked`: the contribution now holds the required writer transaction before the injected error. Move that competing write to the next attempt boundary, after the real `run_with_lock_retry` rollback and before the new authoritative read. | Keep the real retry helper and competing database session, assert the failed request transaction is already closed, and preserve the exact deleted-count and both owner-map assertions. No production lock, retry rule, or assertion is removed. |
| `test_flows.py::test_delete_flow_retry_is_idempotent_when_concurrent_delete_wins` uses the same competing-write window | 14.2, 15.3 | The unchanged local test timed out with the competing SQLite delete blocked by the request's writer transaction. Inject its existing lock error first, then perform the competing delete after the real retry helper rolls back. | Retain the real retry helper, real competing database write, 200 response and exact one-call deletion assertion; additionally verify the request transaction has closed before the competing write. |
| `test_login.py::test_external_access_ceiling_filters_effective_permissions` first-request external identity | 10.3, 17.1, 17.3 | Hosted job `101233760885` and the unchanged local test return 401 instead of 200. The contribution's new canonical active-user lookup uses a separate read-only session, which cannot see the user just created by authentication in the same request. Reuse authentication's existing `DbSession` dependency for the permissions route. | Keep the original test unchanged: 200 with exactly `read` permitted under the viewer ceiling. Retain the canonical active-user check, the external credential ceiling, and the existing request transaction boundary; no global or early-commit change is introduced. |
| Existing auto-login-off user CRUD browser journey | 15.2, TEAM-21 | A newly created user owns a default project, so implicit cascade deletion must return `409 RESOURCE_OWNERSHIP_REQUIRES_DISPOSITION`. Explicitly dispose of that test-owned project and the default variables created on login through the owner's authenticated API before asserting successful admin account deletion. | Retain successful creation, deletion, recreation, rename, login and cross-user flow isolation. Assert the ownership rejection before cleanup; do not ignore failed cleanup requests. |
| Hosted Playwright artifact report gate | 19.5, 23.9 | `actions/download-artifact@v8` flattens a sole matching artifact into the destination root. Resolve that documented runtime layout while retaining named-directory handling for multiple artifacts and attempts. | Reject missing/extra/ambiguous reports, retain newest-attempt selection per shard, and run the existing full JSON journey/zero-retry validator after merging. |
| Jest reporting on read-only fork/Dependabot events | 23.6, 23.10 | Keep the existing JUnit action's local parsing and failure checks active in annotation-only mode when check-writing permission is unavailable; restrict PR comments to trusted same-repository events. | Missing, malformed, failed and zero-passed reports fail validation. Upload the raw JUnit file; do not conditionally skip Jest execution or result validation. |

The current candidate is not yet accepted. The prior candidate's runtime record covers the native service, database engines, migrations, frontend, and browser journeys; additional defects found during continuation require fresh final validation. Hosted Python 3.10/3.14, ARM64 images, fork Actions, and any PR integration SHA must not be described as passing until those systems produce evidence for the delivered candidate.

The attached implementation objective and plan govern authorization. Feature-branch delivery and fork build/test runs are in scope; merging, publishing, deployment, protection changes, and production credential changes are excluded.
