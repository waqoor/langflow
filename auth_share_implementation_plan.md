# Authentication, Authorization, Teams, and Resource Sharing — Implementation Plan

**Implementation repository:** `yazeedhasan97/langflow`
**Implementation URL:** `https://github.com/yazeedhasan97/langflow`
**Fork delivery target:** `yazeedhasan97/langflow:main`
**Proposed implementation branch:** `feat/auth-team-sharing` in the fork; not created by this update
**Upstream reference repository:** `langflow-ai/langflow` — source and compatibility reference, not the implementation/push destination
**Verified fork baseline:** `main` at `9e978f50a3700d079df62ecb2bd5909421093587`
**Historical upstream source baseline:** the same commit; later upstream/release heads must be checked separately
**Plan date:** September 1, 2026
**Document revision:** 1.2 — explicit fork delivery and implementation/E2E readiness recheck — September 1, 2026
**Deliverable:** `auth_share_implementation_plan.md`; intended repository-relative location is the fork root when implementation is authorized
**Status:** Design and implementation instructions only. No application code, database, repository configuration, or deployment has been changed, and no application tests have been executed.

## Purpose

Extend the existing Langflow implementation in **`yazeedhasan97/langflow`** so Platform Admins can manage non-empty teams, users can hold different management roles in different teams, and resource owners can share projects and workflows with specific users or teams as either **Not editable — Can use** or **Editable — Can edit**.

This plan specifies one integrated implementation using Langflow's existing authentication, authorization service interface, resource models, APIs, and frontend extension points. It is not a proposal for a replacement application or a second access-control system.

The source baseline is pinned so existing behavior is distinguishable from proposed changes. References such as **[S01]** identify repository evidence in the source appendix. Proposed files, fields, methods, routes, and policy decisions are explicitly described as additions; they must not be mistaken for features already present upstream.

## Revision summary — fork delivery and execution readiness

This revision makes **the user-owned fork the sole implementation and delivery destination**, with `origin` pointing to `yazeedhasan97/langflow` and a proposed feature-branch PR targeting that fork's `main`. Upstream remains a read-only reference unless the user separately requests an upstream contribution. All repository-relative implementation paths in this document refer to the fork.

The complete feature specification and the previous upstream CI/compatibility work are retained. The fork must run the applicable inherited regression checks and the new production-enforcer tests; upstream maintainer acceptance is not a prerequisite for delivery in the fork.

Section 23.13 records the latest read-only repository and local-runner checks. Repository access and a local synthetic Chromium interaction were verified; Langflow dependency installation, application execution, full E2E execution, workflow-file write scope, and actual fork runner availability were **not** verified. No code, workflow, branch, PR, repository setting, or deployment has been changed by this update. [FORK01–FORK07]

### Previous revision retained — upstream CI and merge alignment

The original plan covered the feature's tests but did not fully specify upstream PR/merge checks or fork-compatible test execution. Revision 1.1 retained the agreed feature design and added those requirements in Section 23; this revision retains them with explicit fork-versus-upstream scope.

Key corrections are the upstream release-candidate PR target, exact required check names, browser-test path/tag discovery, production-enforcer E2E invocation, fork-authorized runners and reporting, migration/quality/package checks, candidate-SHA verification, and a ledger for intentional API/test-contract changes. [CI01–CI23]

Two API compatibility refinements are incorporated into the original design sections, not left as conflicting appendix instructions: keep the established API permission values while the new Share dialog offers only Can use/Can edit; and require new write preconditions in the enabled native collaboration contract without imposing a new mandatory header on the unchanged enforcement-disabled owner contract. Both configurations use the same models, routes, mutation helpers, and registered service.

**Evidence status:** repository sources, workflow definitions, and readable public merge rules have been reviewed. This update also checked fork metadata, its branch and workflow-run records, local tools, network reachability, and a synthetic browser interaction. None of those diagnostics is a Langflow test or proof that the feature passes. Application implementation and CI remain unexecuted. Passing checks and any optional upstream maintainer acceptance remain results to demonstrate.

## Contents

1. [Scope and agreed product contract](#1-scope-and-agreed-product-contract)
2. [Verified backend fit and existing integration points](#2-verified-backend-fit-and-existing-integration-points)
3. [Roles and permission semantics](#3-roles-and-permission-semantics)
4. [Ownership, inheritance, and overlapping grants](#4-ownership-inheritance-and-overlapping-grants)
5. [Architecture and enforcement design](#5-architecture-and-enforcement-design)
6. [Exact data-model changes](#6-exact-data-model-changes)
7. [Migrations and existing-data treatment](#7-migrations-and-existing-data-treatment)
8. [Team administration API changes](#8-team-administration-api-changes)
9. [Share API changes](#9-share-api-changes)
10. [Capabilities, recipient search, and access explanations](#10-capabilities-recipient-search-and-access-explanations)
11. [Authorization service and guard changes](#11-authorization-service-and-guard-changes)
12. [Project and workflow integration](#12-project-and-workflow-integration)
13. [Execution, dependencies, and other API families](#13-execution-dependencies-and-other-api-families)
14. [Concurrent editing and stale requests](#14-concurrent-editing-and-stale-requests)
15. [Lifecycle, revocation, auditing, and transactions](#15-lifecycle-revocation-auditing-and-transactions)
16. [Frontend implementation](#16-frontend-implementation)
17. [Authentication and deployment configuration](#17-authentication-and-deployment-configuration)
18. [File-by-file change inventory](#18-file-by-file-change-inventory)
19. [Required verification and end-to-end scenarios](#19-required-verification-and-end-to-end-scenarios)
20. [Implementation work packages](#20-implementation-work-packages)
21. [Documentation and operational updates](#21-documentation-and-operational-updates)
22. [Definition of done and implementation constraints](#22-definition-of-done-and-implementation-constraints)
23. [Fork delivery, upstream compatibility, and CI acceptance](#23-fork-delivery-upstream-compatibility-and-ci-acceptance)
24. [Source appendix](#24-source-appendix)

---

## 1. Scope and agreed product contract

### 1.1 Required outcomes

| ID | Required outcome |
|---|---|
| REQ-01 | Provide a **Teams** tab in the administration area for Platform Admins. |
| REQ-02 | A Platform Admin can create a team with initial members and at least one designated active Team Admin in the same operation. A team must never be committed empty. |
| REQ-03 | Support membership roles `admin`, `maintainer`, and `user`, scoped to each team membership. |
| REQ-04 | Support membership and role changes with last-member and last-active-admin protection. |
| REQ-05 | Add **Share** to the existing project sidebar three-dot menu and workflow action menus. |
| REQ-06 | A resource owner can share their resource even when they are not a Platform Admin. A Platform Admin can administer resource shares according to the configured administrative policy. |
| REQ-07 | Recipients can be an existing active user or an existing active team. |
| REQ-08 | Each user/team grant has one of two selectable modes: **Not editable — Can use**, or **Editable — Can edit**. The owner can change the mode later. |
| REQ-09 | Sharing a project applies to its current and future workflows through inherited authorization. Sharing a single workflow does not expose its siblings. |
| REQ-10 | The homepage, direct resource URLs, backend APIs, editor, execution endpoints, and effective-permission responses agree on access. |
| REQ-11 | Removing membership or a share, or downgrading its mode, changes newly admitted access without a process restart. Other surviving grants remain effective and are explained to the owner. |
| REQ-12 | Existing authentication and execution-identity boundaries remain in place. Teams organize trusted collaborators; this feature does not promise a tenant execution sandbox. |

### 1.2 Meaning of the two sharing modes

**Not editable — Can use** means the recipient may view a workflow and run its saved definition with ordinary runtime inputs. The recipient cannot change its saved graph, metadata, publication settings, owner, location, or sharing configuration. Execution can still call external services and produce normal workflow side effects.

**Editable — Can edit** means the recipient may view, run, and modify permitted workflow content. On a project it additionally allows creating workflows in that project and editing the project's name and description. It does not automatically permit deleting resources, changing publication or authentication settings, moving other people's workflows, transferring ownership, or resharing.

These modes describe **this grant**, not an absolute restriction overriding ownership, another team grant, or a broader existing role. The UI must show effective access separately when it differs.

### 1.3 Planning decisions needed to make implementation deterministic

The following choices operationalize the discussion; they are planned behavior, not assertions about upstream implementation:

- Team Admin and Maintainer receive a team-scoped management screen; they do not receive the whole Platform Admin area.
- Only Platform Admins create/delete teams through public administration endpoints. Team Admins manage the membership and ordinary settings of their own teams.
- Only resource owners and configured Platform Admins manage the new user/team sharing controls. Edit access does not imply resharing authority.
- New workflows remain owned by their authenticated creator, including workflows created inside another user's shared project. The project owner gains content-management access to its children, but ownership is not transferred.
- Existing owner rights survive the removal of a team/direct grant. Removing a collaborator from a team does not revoke ownership of workflows that collaborator created.
- Existing direct grants survive moves between projects; inherited access is recomputed from the new project. Only appropriately authorized owners/Platform Admins can move an existing workflow.
- Use committed canonical authorization tables for decisions; do not introduce a separate policy database or require Redis to determine whether access is allowed.
- Apply optimistic concurrency to saved workflow/project content and share-level updates. This is lost-update protection, not a real-time collaborative editor.
- This implementation targets a trusted, single-instance collaboration domain. It must respect existing non-null workspace scopes but does not create an organization/workspace tenancy product.

### 1.4 Explicit exclusions

Do not add a new login system, new identity store, new API generation, duplicated team/share tables, a second policy engine, copied workflows per recipient, per-member copies of team grants, or per-flow copies of inherited project grants.

Do not bundle email invitations to non-users, billing, live co-editing, team-owned credentials, ownership-transfer workflows, new SSO providers, a tenant sandbox, or broader MCP/webhook sharing into this feature.

Do not introduce V2 replacement paths, parallel implementations, shadow/canary execution, staging infrastructure, or human approval/authority workflows. Existing upstream `/api/v2` execution routes are existing integration surfaces, not a reason to add another version. Disposable automated-test processes/databases, an ordinary Git feature branch, and the repository's existing PR reviews/checks/merge queue are not application approval workflows or parallel production implementations; preserve those contribution requirements rather than bypassing them. See Section 23.

### 1.5 Fork-specific implementation and delivery boundary

- **Write destination:** only `yazeedhasan97/langflow`; every path in Sections 6–23 is relative to that repository's root.
- **Git remotes:** `origin` is the user's fork. `upstream` is `langflow-ai/langflow` for fetching source/compatibility updates only. Never infer a write destination from a source citation.
- **Branch/PR:** use one ordinary feature branch, proposed `feat/auth-team-sharing`, based on the verified fork `main`; the feature PR's base repository is `yazeedhasan97/langflow` and base branch is `main`. If the branch already exists when implementation begins, inspect and reuse the authorized work rather than overwrite it or create a duplicate implementation.
- **CI/build ownership:** run the fork's workflow definitions and build its exact candidate source. Reusable jobs and local actions must not silently check out upstream's default branch or test a released upstream wheel/image instead.
- **Upstream integration:** keep the applicable upstream standards, tests, shared interfaces, and security fixes. An actual upstream PR, its active release-candidate base, maintainer review, or merge queue is conditional on a separate upstream-submission request.
- **No implicit mutations now:** this plan update is a downloadable document only. It does not commit the plan, create a branch/PR, dispatch CI, change Actions permissions/protection, merge, publish, or deploy anything.

The retained `CONTRIBUTING.md` release-candidate instruction describes contributions to **upstream**. Document this fork-specific `main` delivery convention in the fork's contribution guidance during implementation without rewriting upstream historical guidance or treating the fork as an upstream release branch. [CI01, FORK01, FORK02]

---

## 2. Verified backend fit and existing integration points

| Area | Baseline evidence | Planned treatment |
|---|---|---|
| Authentication | Local JWT/session/API-key and external-identity paths already exist. [S01, S17, S18] | Retain them; consume the authenticated active identity and credential context. |
| Authorization | `LangflowAuthorizationService` currently permits every check. `BaseAuthorizationService` defines enforcement, batching, visibility, public-principal, and lifecycle hooks. [S02, S03] | Implement enforcing behavior in the existing Langflow service for the enhanced distribution; keep one active service. |
| Team models | `AuthzTeam` and `AuthzTeamMember` exist; membership has `source` but no team role. [S04] | Extend membership and the current CRUD path. |
| Team APIs | `/api/v1/authz/teams` and membership APIs exist; writes currently require superuser authority. Team creation does not accept initial members. [S05, S06] | Add atomic initial membership, team-scoped management, and role updates. |
| Share persistence/API | `AuthzShare` supports resource IDs, user/team targets, and permission levels; `ShareUpdate` already changes `permission_level`. [S04, S07, S08] | Reuse these fields and endpoints; add validation, concurrency, and complete resource context. |
| Projects/workflows | Projects are `Folder`; workflows are `Flow` with `folder_id`, `user_id`, and optional workspace scope. [S09, S10] | Keep models/ownership; implement inheritance over this relationship. |
| Fetch/list helpers | Cross-user fetch requires enabled authorization plus capability support; list helpers support database prefilters. [S11, S12] | Implement both exact-resource access and collection visibility. |
| Existing CRUD helpers | `_new_flow`, `_read_flow`, `_patch_flow`, `_update_existing_flow`, and destination helpers already distinguish ownership/scope. [S13] | Extend these shared paths rather than adding sharing-only CRUD. |
| Permission discovery | `/api/v1/authz/me/permissions` exists and backs `PermissionsProvider`. [S14, S21] | Keep the response's existing permission map and add resource capabilities. |
| Frontend hooks | Project menu calls `CustomResourceShareAction`; workflow menus call `CustomFlowShareAction`; OSS implementations return `null`. [S19, S20] | Implement these hooks using one reusable dialog. |
| Admin layout | The OSS admin-menu hook is empty; the route file includes admin login but not a complete public OSS administration layout. [S22] | Add one administration layout through the existing routing hook when absent; reuse an existing layout in an actual customized checkout. |
| Runtime contracts | Endpoint authorization and execution-principal matrices specify route-family behavior. [S23, S24] | Update them alongside the affected tests; do not treat structural matrix validation as runtime proof. |

**Distribution decision:** upgrading the OSS pass-through class into an enforcing implementation changes the intentional upstream OSS packaging behavior. This plan is for the enhanced distribution/fork discussed here. It does not assume Enterprise source is available or that upstream maintainers have agreed to this packaging choice. Preserve the existing authorization interface and registration mechanism. [S01–S03]

---

## 3. Roles and permission semantics

### 3.1 Three independent kinds of authority

1. **Platform authority:** active `User.is_superuser`, subject to the deployment's existing administrative bypass policy and any narrower credential ceiling.
2. **Team management:** `AuthzTeamMember.role`, only for that team's settings/membership.
3. **Resource access:** ownership, applicable existing scoped roles, direct shares, active-team shares, and inherited project access.

Never derive `is_superuser` from a team role. Never interpret a team role as a workflow permission level. Never put team-role values into `AuthzShare.permission_level`.

### 3.2 Team management matrix

| Operation | Platform Admin | Team Admin | Team Maintainer | Team User |
|---|---:|---:|---:|---:|
| Create a team | Yes | No | No | No |
| Delete a team through administration API | Yes | No | No | No |
| List all teams for administration | Yes | No | No | No |
| View own team's roster | Yes | Yes | Yes | Yes |
| Edit own team's name/description | Yes | Yes | No | No |
| Add an ordinary `user` member | Yes | Yes | Yes | No |
| Remove an ordinary `user` member | Yes | Yes | Yes | No |
| Assign/change Admin or Maintainer roles | Yes | Yes | No | No |
| Modify/remove a Team Admin or Maintainer | Yes | Yes, subject to invariants | No | No |
| Activate/deactivate a team | Yes | No | No | No |
| Change external group identifier `adom_name` | Yes | No | No | No |
| Access a workflow shared with the team | According to resource policy | According to share | According to share | According to share |

Additional rules:

- Platform Admin does not become a member of every team automatically.
- A creator must nominate at least one initial active Team Admin; the creator can select themselves or someone else.
- Membership management is an access-delegation operation: adding a person gives them the team's current resource grants. Show this consequence in the interface and record it in the audit trail.
- Maintainers may not promote themselves, modify their own role, assign privileged roles, or remove privileged members by calling the API directly.
- Source-managed membership removal follows its authoritative source, not a manual endpoint pretending to be SSO. Membership roles remain explicit local administrative assignments unless a future, separately specified provider integration authorizes role synchronization.

### 3.3 Resource sharing matrix

| Capability | Non-editable flow share | Editable flow share | Non-editable project share | Editable project share |
|---|---:|---:|---:|---:|
| Read resource content | Yes | Yes | Yes | Yes |
| Read contained workflows | Not applicable | Not applicable | Yes | Yes |
| Execute saved workflow | Yes | Yes | Yes, for children | Yes, for children |
| Edit saved workflow content | No | Yes | No | Yes, for children |
| Edit project name/description | No | No | No | Yes |
| Create a workflow inside the shared project | No | No | No | Yes |
| Delete an existing shared workflow | No | No | No | No |
| Delete the shared project | No | No | No | No |
| Reshare/change grants | No | No | No | No |
| Publish publicly/change transport authentication | No | No | No | No |
| Transfer ownership | No | No | No | No |
| Move another user's workflow | No | No | No | No |
| Deploy using someone else's provider account | No | No | No | No |

Resource owners retain their established ownership operations; applicable broader legacy roles can supply additional rights. The table describes rights conferred by the two new sharing modes alone.

### 3.4 Canonical storage and action mapping

For `flow`/`project` shares created through the new dialog with `scope=user|team`:

- **Can use** → `permission_level="execute"`.
- **Can edit** → `permission_level="write"`.

Do not add a redundant persisted `editable` boolean. UI labels map to the canonical value at the API boundary.

A project has no canonical `execute` action. Interpret an `execute`-level project share as `project:read` plus `flow:read`/`flow:execute` for its children. Interpret a `write`-level project share as those actions plus `project:write`, `flow:write`, and `flow:create` into that project. Creating a new project is separate and is not granted by sharing an existing project. [S15]

**API compatibility:** keep `read`, `execute`, `write`, and `admin` in the underlying share create/update schemas and honor their resource-specific semantics under the normal administration checks. The new dialog offers only `execute` and `write`; it does not replace the reusable API vocabulary. Existing or API-created `read`/`admin` rows remain intact and appear as read-only/administrative grants. Converting such a grant to a dialog mode requires an explicit authorized action. Never silently convert `read` to `execute`, because that adds execution permission. Existing public and other-resource share restrictions remain in force. [S07, S08, S32]

### 3.5 Permission precedence

For a supported action:

1. Validate active authenticated identity and canonical resource/destination.
2. Apply narrower credential restrictions and external access ceilings.
3. Apply a configured Platform Admin bypass, where that bypass is explicitly permitted.
4. Evaluate ownership and applicable existing role grants.
5. Add applicable direct, active-team, and project-inherited grants.
6. Enforce operation-specific limitations: field restrictions, publication authority, move/delete authority, locked/deployed-resource rules, and concurrency preconditions.
7. Deny when no sufficient grant exists or when required policy data is unavailable.

A restrictive share is not an explicit deny. An `execute` direct grant does not cancel a `write` team grant. Do not add an explicit-deny policy language in this work.

---

## 4. Ownership, inheritance, and overlapping grants

### 4.1 Workflow ownership stays separate from project ownership

Keep `Flow.user_id` as the actual creator/owner and `Folder.user_id` as the project owner. Do not change the flow owner to a team ID, the editor, or the project owner during an ordinary save.

For a new workflow in a shared project:

- The backend resolves and authorizes the destination project.
- The authenticated creator becomes `Flow.user_id`.
- `folder_id` is the authorized project ID.
- `workspace_id` comes from the stored destination project, not an independently supplied client value.
- The project owner receives content access to that child equivalent to the editable project grant: read, execute, and write.
- The creator retains ownership if their team/share grant is later removed. They do not thereby retain permission to browse the project's other workflows.

The interface and documentation must disclose this retained ownership. Removing a team member is not an ownership-transfer mechanism.

### 4.2 Project inheritance is dynamic

Resolve inherited permissions against the workflow's current canonical project. Do not create share rows for every child workflow. New children inherit immediately; moved children inherit from their new project; deleted project grants no longer contribute access.

No implicit recursion through `Folder.parent_id` is introduced. The initial contract covers a project's directly contained workflows. Existing nested-folder behavior must remain intact, but recursive descendant sharing requires a separately explicit policy rather than an accidental wildcard.

### 4.3 Direct workflow shares do not expose a private project

A recipient can find/open an individually shared workflow through a **Shared with me** view or the accessible workflow list without being allowed to fetch the private parent project. Do not grant parent-project access as a convenience fix for navigation.

Hide unauthorized parent metadata in breadcrumbs. Use a neutral label such as **Shared workflow** rather than fetching or displaying a private project name.

### 4.4 Moves and deletes

Moving an existing workflow requires ownership of that workflow or permitted Platform Admin authority, plus authorization to create/place it in the destination. An editor of someone else's workflow cannot move it. The workflow owner can remove their own workflow from a project even after their inherited team access ends, provided the destination is authorized and deployment/lock constraints permit the move.

Before a move, show that inherited access changes while existing direct/team flow grants remain. Revalidate the source flow, destination project, and any deployment restrictions inside the mutation path; never silently redirect an explicitly requested inaccessible destination to a personal default folder.

Deleting a project must not silently cascade-delete collaborators' workflows on the strength of a mere project grant. Require project deletion authority and deletion authority for every affected child/deployment. Validate the complete affected set before deleting anything. A project owner without deletion rights to a collaborator-owned child receives a conflict/permission explanation and can have that child moved by its owner or handled by a Platform Admin.

### 4.5 Overlapping grants and access explanations

Effective access may come from ownership, a direct share, multiple teams, a project, or an existing scoped role. Return the source and effective capabilities in the management response.

Examples:

| Situation | Expected result |
|---|---|
| Direct Can use + Team Can edit | Can edit, with Team source shown. |
| Project Can edit + direct flow Can use | Can edit; the direct grant is not a deny. |
| Remove a direct share but a team grant remains | Access remains; the response explains the remaining grant. |
| Remove team membership but user owns the flow | Ownership rights remain; unrelated project access ends. |
| No remaining grant on a foreign private resource | Omit from lists; direct read returns a privacy-preserving not-found result. |

---

## 5. Architecture and enforcement design

### 5.1 One active authorization service

For this enhanced OSS-based distribution, replace the pass-through implementation body of **`LangflowAuthorizationService` in `services/authorization/service.py`** with a database-backed enforcing implementation when `AUTHZ_ENABLED=true`.

Keep the existing class name, factory, service key, and dependency accessor. Do not leave the old allow-all implementation active beside a separate team enforcer. The LFX interface stays framework-neutral and must not import Langflow ORM models. [S02, S03, S25]

Use private helper modules under `langflow/services/authorization/` to keep policy evaluation, database loading, team mutation, and share mutation maintainable. These are parts of the same implementation, not independently registered services or separate access-control stores.

Preserve the supported `AUTHZ_ENABLED=false` contract and framework-neutral LFX defaults, while proving enabled-mode behavior with the actual enforcing service. Classify existing tests that assert an enabled OSS stub always allows as deliberate fork-contract changes; replace only those obsolete expectations with substantive allow/deny coverage. Do not keep a hidden enabled-mode allow-all path or silently alter unrelated package defaults to obtain a green suite. Section 23.7 defines the required compatibility ledger.

If a real authorization plugin is already registered in the implementation checkout, first identify it. Extend that single active implementation to satisfy the contract instead of silently replacing its credential restrictions. The reviewed baseline did not include that plugin's implementation. Do not claim compatibility with an uninspected Enterprise plugin.

### 5.2 Canonical-table evaluation, not a new compiled-policy store

The selected implementation reads `authz_role`, `authz_role_assignment`, `authz_team`, `authz_team_member`, `authz_share`, users, and canonical resource scope/ownership from the existing database.

- No cross-request allow/deny cache is required for correctness.
- Request-local batching is permitted within a single admission/evaluation step.
- Do not keep a positive permission snapshot through a later write request or HITL resume.
- Existing invalidation/sync hooks still run for interface consistency, but this implementation does not rely on best-effort publication to notice canonical revocation.
- Do not maintain a second copy of canonical grants in `casbin_rule` merely because that table exists. Leave the existing table/schema intact for compatibility; the selected native evaluator does not require it.
- Keep queries bounded and prefilter visible lists in SQL before pagination.

This choice limits implementation and operational scope while making every new admission observe the committed canonical policy state.

### 5.3 Request path

```text
Existing authentication and active-user check
    -> canonical resource/destination resolution
    -> credential ceiling and authorization evaluation
    -> field-level/operation-specific restrictions
    -> concurrency precondition
    -> existing resource operation
    -> canonical mutation/audit commit
    -> response and frontend query invalidation
```

Authorization must happen before protected graph expansion, storage writes, secret lookup, provider calls, or workflow dispatch. Existing execution endpoints continue to use the actual actor as specified in their runtime contract. [S23, S24]

### 5.4 Personal creation must remain usable

Turning on deny-by-default must not force users into global developer roles merely to create their own private projects or supporting resources.

Implement explicit intrinsic permissions for an active user to create resources that the backend will unconditionally own to that user, subject to credential restrictions and existing configuration. For a flow in another user's project, require destination-specific `flow:create` through an editable project grant.

Add trusted internal creation context where necessary. Do not use caller-supplied ownership fields to obtain this intrinsic permission, and do not equate `project:create` with visibility over all projects.

### 5.5 Availability behavior

When sharing is configured for this distribution but the enforcing service is unavailable, an unsupported stub is active, or canonical policy reads fail:

- Do not issue a successful effective-permission answer.
- Do not accept share/team mutations that pretend enforcement is active.
- Return a sanitized unavailable response or the existing fail-closed denial where required by the guard contract.
- Do not expose another user's resource because a policy lookup failed.
- Report capabilities honestly so the frontend does not render a working-looking Share action backed by a no-op service.

This is configuration/runtime correctness, not an approval workflow.

---

## 6. Exact data-model changes

### 6.1 Existing `AuthzTeamMember`

**File:** `src/backend/base/langflow/services/database/models/auth/authz.py`

Add:

| Field/constraint | Definition |
|---|---|
| `role` | Non-null string with canonical values `admin`, `maintainer`, `user`; default `user` for new non-privileged membership paths. |
| `updated_at` | Timezone-aware UTC timestamp using the existing authz timestamp helpers. |
| `ck_authz_team_member_role` | Database check restricting the role vocabulary. |
| `ix_authz_team_member_team_role` | Composite index on `(team_id, role)` for role/invariant queries. |

Retain the unique membership constraint `(team_id, user_id)`, both foreign keys, `source`, and `created_at`. Preserve the ORM/schema consistency conventions used by existing authz models. [S04]

Do not add a global `User.team_role`, a second membership table, or a role per share target.

### 6.2 Existing `AuthzTeam`

Retain current fields. Add nullable `inactivation_reason` with constrained values `manual` or `no_active_admin` when inactive; use `null` for an active team. This records whether administrative repair is required after account/source lifecycle changes.

Do not add a team resource-owner field that changes ownership of shared projects/workflows. Administrative actors and detailed changes belong in the audit log.

Cross-row non-empty and active-admin invariants cannot be guaranteed by a simple membership column check. Enforce them through one transactional team-mutation path used by all relevant writers.

### 6.3 Existing `AuthzShare`

Retain its resource/target uniqueness constraints and canonical `permission_level`. Add:

| Field | Definition |
|---|---|
| `revision` | Non-null integer, initial value `1`, incremented for each effective share-level update. |
| `updated_at` | Timezone-aware UTC timestamp. |

Use `revision` for conditional share updates/deletes so two management dialogs cannot unknowingly overwrite or remove each other's changes. Do not add an `editable` column or a new share-type enum.

### 6.4 Existing `Flow` and `Folder`

Add non-null integer **`edit_revision`**, initial value `1`, to each existing model. Expose it on read models and relevant frontend types. Do not make it a client-writable persisted field.

Every effective user-visible mutation to protected flow/project content increments the revision exactly once. No-op saves do not increment it. This revision is separate from existing published flow versions and from `Flow.locked`.

Add conditional-write preconditions to the existing mutation endpoints; do not add an alternative save endpoint. Existing flow versions continue to represent their current product meaning.

### 6.5 Framework-neutral contracts

**File:** `src/lfx/src/lfx/services/authorization/base.py`

Add the membership-role mutation kind `TEAM_MEMBER_ROLE_CHANGED` to `AuthorizationMutationKind` and include it in the affected-user invalidation adapter. Add typed, non-secret context keys needed for server-resolved share resource/recipient and owned-creation checks.

Add an explicit capability probe for supporting the team-role/user-team-share contract, defaulting to **false** in the base class. The enhanced service must implement it as true only when it actually supplies the required behavior. Preserve compatibility of existing method signatures by using optional context fields or optional keyword arguments; never introduce Langflow ORM dependencies in LFX.


## 7. Migrations and existing-data treatment

### 7.1 Schema revisions

Generate new Alembic revisions from the actual implementation checkout's current head. Do not edit the already-published `7c8d9e0f1a2b_authz_foundations` migration or invent a revision identifier in advance.

The revisions must add the fields/checks/indexes in Section 6, backfill non-null timestamps/revisions, and match SQLModel metadata on both supported SQLite and PostgreSQL paths. Use the repository's migration utilities and batch-alter conventions where required. Include an accurate `Phase: EXPAND`, `MIGRATE`, or `CONTRACT` marker on every revision and pass the existing migration validator and model/migration consistency suite. Add non-null fields using valid server defaults/backfills; do not exempt this feature from validation or mislabel destructive changes. These migration phases do not authorize parallel runtime paths or staging infrastructure. [CI10, CI11]

Treat `edit_revision=1` and `AuthzShare.revision=1` as the initial state of existing records. Backfill `AuthzTeamMember.role="user"` unless an explicit existing administrative mapping supplies a different role. Never infer a Team Admin from membership order, username, SSO group text, or arbitrary creation timestamps.

### 7.2 Legacy team repair

Provide one offline administrative CLI command in the existing `langflow authz` command group, implemented in proposed `cli/authz_team_preflight.py`:

- `langflow authz teams-check`: read-only report of empty teams, inactive-only membership, missing active Team Admin, orphan references, and duplicate/inconsistent source records.
- `langflow authz teams-repair --mapping-file <path>`: apply explicit data-repair instructions through the same team-management logic after the new schema exists.

A repair mapping identifies the team UUID and either a nominated active administrator or explicit deletion of an empty team. It contains identifiers and intended roles, not passwords, tokens, or copied policy data. Validate the entire supplied mapping before applying a repair transaction.

For existing active teams, require an explicit nominated active administrator to retain active status. When no administrator is nominated, report the unresolved team and leave it inactive rather than promote someone or continue granting access with invalid governance. Empty legacy teams must be repaired with nominated membership or explicitly retired before the enhanced application accepts collaboration traffic.

The one-time transition operates while the application is not serving writes. Existing invalid legacy records are migration findings, not permissible states for the new runtime. New application requests must never create/commit an empty team.

Retiring an empty team removes its team-targeted share rows and records a canonical audit summary; it never deletes the projects/workflows those rows referenced. Do not restore deleted legacy team IDs on an unrelated later team creation.

### 7.3 Existing shares and roles

- Preserve existing targeted `read` and `admin` rows and existing public/other-resource shares.
- Report dangling recipient/resource references. Do not use them to grant access. Remove them only through a recorded repair or the corresponding lifecycle cleanup.
- Do not assign every user the global developer/admin role as a bootstrap shortcut.
- Preserve manual/identity-provider provenance on existing role assignments. Removing one manual grant must not remove surviving source-derived assignments. [S27]
- Do not rewrite published role definitions merely to make the share dialog show two choices.
- Do not copy flows, folders, credentials, or model-provider configurations during migration.

### 7.4 Deployment and downgrade treatment

Apply schema and reviewed data repair, deploy the integrated backend/frontend together, then start the application with the enhanced authorization configuration. These are one release's implementation/deployment dependencies, not parallel runtime versions.

Record the exact pre-change backup and migration revision in the operational instructions. Downgrading code after writes to new role/revision fields is not automatically lossless. Document a restore-based recovery procedure and any data loss from dropping the new columns. Do not promise a seamless downgrade or rely on a destructive downgrade to repair an authorization error.

No tests are added to startup, migrations, Docker entrypoints, or the deployment command.

---

## 8. Team administration API changes

### 8.1 Preserve and extend `/api/v1/authz/teams`

Keep the existing router and route family. Refactor its mutation bodies to call one team-management implementation, while retaining authentication dependencies. Replace blanket superuser checks only for operations intentionally delegated to Team Admin/Maintainer.

| Endpoint | Exact planned change |
|---|---|
| `POST /authz/teams` | Require initial `members`; create team/members/roles atomically; Platform Admin only. |
| `GET /authz/teams` | Preserve paginated list shape; add an explicit view filter for directory, own membership, own managed teams, or Platform Admin's all-team view. |
| `GET /authz/teams/{team_id}` | Return permitted metadata and caller capabilities; do not expose unrestricted rosters. |
| `PATCH /authz/teams/{team_id}` | Enforce field/role-specific authority; support atomic membership replacement operations as specified below. |
| `DELETE /authz/teams/{team_id}` | Platform Admin only; remove memberships and team share rows, retain actual resources, audit atomically. |
| `GET /authz/teams/{team_id}/members` | Platform Admin or member of that team; paginated; return membership role/source and minimal user display information. |
| `POST /authz/teams/{team_id}/members` | Accept role; enforce Admin/Maintainer limits; default new membership to `user`; no forged SSO provenance. |
| `PATCH /authz/teams/{team_id}/members/{user_id}` **new** | Change the membership role; Platform Admin or Team Admin only; enforce active-admin invariant. |
| `DELETE /authz/teams/{team_id}/members/{user_id}` | Enforce role/source boundaries and non-empty/admin invariants in the transaction. |

Paths in this table are relative to `/api/v1`.

### 8.2 Create schema

Extend `TeamCreate` in `api/v1/schemas/authz_teams.py` with:

- `members`: non-empty list, maximum 200 initial entries.
- Each entry: `user_id: UUID`, `role: Literal["admin", "maintainer", "user"]`.
- Reject duplicate user IDs, whitespace-only names, unknown/inactive users, invalid roles, and an initial roster without an active administrator.
- Preserve `team_name`, `adom_name`, `description`, and `is_active`; apply normalized length checks.
- Require a non-empty roster even for an initially inactive team. The ordinary UI creates active teams with an active Admin.
- The server sets public-request membership `source="manual"`.

Illustrative contract, with placeholder identities:

```json
{
  "team_name": "AI Engineering",
  "adom_name": "ai-engineering",
  "description": "Internal workflow development team",
  "is_active": true,
  "members": [
    {
      "user_id": "11111111-1111-4111-8111-111111111111",
      "role": "admin"
    },
    {
      "user_id": "22222222-2222-4222-8222-222222222222",
      "role": "maintainer"
    },
    {
      "user_id": "33333333-3333-4333-8333-333333333333",
      "role": "user"
    }
  ]
}
```

Return `201` with the existing team fields plus `member_count`, `active_member_count`, `active_admin_count`, `current_user_role`, `inactivation_reason`, and caller management capabilities. Compute counts with aggregate queries; do not store duplicate counters that can drift.

### 8.3 Atomic roster changes

Extend `TeamUpdate` with optional:

- `member_upserts`: list of `{user_id, role}` for adding members or changing roles.
- `remove_member_ids`: list of user UUIDs to remove.

These changes are a patch, not full roster replacement. Reject a user occurring in both collections and duplicate operations. Apply the final proposed roster's invariants once inside one transaction. This allows replacing the last Admin with another active Admin without committing an invalid intermediate state.

The single-member endpoints delegate to the same implementation. Maintainers can use only operations affecting ordinary manually managed `user` members, including in a batch; they cannot bypass restrictions by combining metadata and membership operations.

For a request to change a member's role:

```json
{
  "role": "maintainer"
}
```

Return the updated membership with `updated_at`. Even a no-op request must check the actor's authority; it must not reveal another team's administrative metadata.

### 8.4 Source-aware membership

Retain `source` on reads. New public mutation requests cannot claim `source="sso"` or take over an SSO-owned membership. Reject attempts to remove source-managed membership through manual management with an actionable conflict response.

A local Team Admin can assign a local team-management role to an existing eligible source-managed member, but this does not turn the membership into a manual one. If the authoritative source removes that membership, its team role ends with it. No role is resurrected automatically when the person is later re-added.

Do not infer that the current singular `source` field represents multiple independent membership grants. Supporting overlapping manual/SSO membership provenance is not introduced by silently changing its meaning.

### 8.5 Error contract

Use existing authentication status handling. Add stable machine-readable codes in the existing `detail` response envelope for new domain errors:

| Status | Code | Meaning |
|---|---|---|
| `422` | `TEAM_MEMBERS_REQUIRED` | Initial roster absent or empty. |
| `422` | `TEAM_ACTIVE_ADMIN_REQUIRED` | Proposed active team has no eligible active Admin. |
| `409` | `TEAM_LAST_MEMBER` | Manual mutation would leave no membership. |
| `409` | `TEAM_LAST_ACTIVE_ADMIN` | Manual mutation would remove/demote the last active Admin. |
| `409` | `TEAM_MEMBERSHIP_EXISTS` | Duplicate add to an existing membership. |
| `409` | `TEAM_MEMBERSHIP_SOURCE_MANAGED` | Manual action conflicts with authoritative source management. |
| `403` | `TEAM_OPERATION_FORBIDDEN` | Caller knows the team but cannot perform the operation. |
| `404` | Existing not-found wording | Team/membership is absent or not visible to the caller. |
| `503` | `AUTHORIZATION_NOT_READY` | Required enforcement/database state is unavailable. |

Do not change unrelated API errors merely for stylistic uniformity. Adapt the frontend's error extraction to the structured codes for these operations.

---

## 9. Share API changes

### 9.1 Supported new sharing operation

Reuse `POST /api/v1/authz/shares` with the current canonical payload:

```json
{
  "resource_type": "flow",
  "resource_id": "44444444-4444-4444-8444-444444444444",
  "scope": "team",
  "target_id": "55555555-5555-4555-8555-555555555555",
  "permission_level": "write"
}
```

Change `resource_type` to `project` for a project grant. Use `scope="user"` and that user's ID for an individual. Use `permission_level="execute"` for non-editable access.

The new dialog only sends `execute`/`write` with `scope=user|team` for `flow|project`. Preserve the existing API's `read`/`admin` values for authorized callers; do not reject a valid value merely because it is not one of the new dialog's two choices. Apply the established resource/scope restrictions and canonical resource-specific action map. UI restrictions are not a substitute for backend authorization. [S07, S08]

Existing and API-created read-only/administrative grants remain readable and removable. Explicit conversion to `execute`/`write` is permitted. Verify recipient existence/status, resource-scoped share administration, and narrower credential ceilings for every accepted value. Keep new public flow share restrictions unchanged, and never silently increase a requested permission level to fit a UI label.

### 9.2 Create/update/delete authorization sequence

For every share mutation:

1. Require the real active authenticated caller and a ready enforcing service.
2. Resolve the exact target resource and its owner/project/workspace from stored data, without serializing its graph or secret content.
3. Verify resource-scoped share administration: owner or permitted Platform Admin; preserve narrower credential ceilings.
4. Validate the requested scope/mode and target existence/status/domain eligibility.
5. Lock/re-read relevant rows before mutation; verify no recipient/team/resource lifecycle change invalidated the request.
6. Check uniqueness for create or revision for update/delete.
7. Persist the canonical share and its mutation audit record in one transaction.
8. Commit, then call interface invalidation hooks and return the durable result.

For update/delete, derive the resource/target from the stored share row. Do not trust resource fields supplied alongside the share ID. Share creator status alone is not permanent management authority after resource ownership or administrative authority changes.

### 9.3 Do not authorize against a global `share:*` alone

Add a shared guard/helper **`ensure_resource_share_administration`** under the existing authorization package. Its planned inputs are the authenticated user, share action, server-resolved resource type/ID/owner/project/workspace, and optional stored share/recipient context.

Use it from share create/read-management/update/delete, the access summary, and recipient search. This closes the context gap in the current create guard, which does not supply the resource/recipient detail needed for granular checks. [S07]

The `ShareAction` vocabulary remains `read/create/update/delete`. `can_manage_shares` is a derived capability, not a new global grant inferred from `flow:write`.

### 9.4 Conditional updates

Extend `ShareRead` with `revision` and `updated_at`. Return a strong ETag on individual share reads and successful updates using the form `"share:<uuid>:<revision>"`.

Require `If-Match` for `PATCH` and `DELETE` under the enabled native collaboration contract. Missing precondition returns `428 PRECONDITION_REQUIRED`; a stale revision returns `412 SHARE_CHANGED`. Authenticate/authorize before returning current revision information. The common precondition helper always honors a supplied condition but does not impose a mandatory new header on an unrelated enforcement-disabled owner operation or a substituted plugin that has not opted into this contract. This compatibility rule does not bypass the share API's readiness/administration checks: the new targeted-sharing feature still requires a functioning enforcer. A settings/service error must never select the less restrictive contract.

```http
PATCH /api/v1/authz/shares/66666666-6666-4666-8666-666666666666
If-Match: "share:66666666-6666-4666-8666-666666666666:3"
Content-Type: application/json

{
  "permission_level": "execute"
}
```

A changed share increments revision to `4`; an authorized identical no-op keeps revision `3`. Do not automatically retry a stale permission change after reading a newer revision. Refetch and let the user act on the current state.

Keep duplicate create as `409` rather than converting it into an implicit update that could accidentally increase access. The UI can refetch and select the existing grant.

### 9.5 Listing and pagination

Filter share visibility in SQL **before** applying offset/limit. The current handler's post-page filtering can produce incomplete pages. [S07]

Owners/Platform Admins can manage the resource's applicable direct grants. Other users can read only the share/access information necessary to explain their own access; seeing a grant does not allow changing it.

Public grants remain direct-link grants and are not added to user/team discovery lists. Owner/publication management stays separate from this new dialog.

### 9.6 Revoking one grant

The delete response means the named share row was removed, not that every possible route to the resource ended. Invalidate/refetch the access summary so any surviving role, team, project, or ownership source is visible.

Never change `Flow.access_type`, A2A settings, or unrelated grants when removing a user/team share. Conversely, the user/team dialog must not claim to make a legacy-public flow private.

---

## 10. Capabilities, recipient search, and access explanations

### 10.1 Deployment capabilities — new endpoint

Add **`GET /api/v1/authz/capabilities`**, authenticated, under proposed `api/v1/authz_capabilities.py`.

Return only non-secret product capabilities:

```json
{
  "enforcement_active": true,
  "service_ready": true,
  "team_roles_supported": true,
  "user_team_sharing_supported": true,
  "share_modes": ["execute", "write"],
  "conditional_writes_required": true,
  "can_administer_platform": false,
  "can_create_team": false
}
```

Obtain these values from the actual registered service and current identity. Never infer support merely from `LANGFLOW_AUTHZ_ENABLED=true`, the existence of authz tables, or a service class name. `share_modes` describes the two new dialog choices, not an exhaustive replacement for API permission values. Add a non-abstract `supports_conditional_writes()` capability hook on `BaseAuthorizationService`, defaulting to false; the native implementation reports support, and the response sets `conditional_writes_required=true` only when that supported contract is enabled. This hook and the common mutation helper must agree. Preserve existing plugin source compatibility. Failed service/setting resolution must fail closed rather than advertise a false/disabled mode.

If capability discovery fails, the UI displays an unavailable state and disables protected mutations. It must not interpret an absent response as permission to edit or share.

### 10.2 Restricted recipient search — new endpoint

Add **`GET /api/v1/authz/recipients`** under proposed `api/v1/authz_recipients.py`.

Query parameters:

| Parameter | Contract |
|---|---|
| `purpose` | `share` or `team_membership`. |
| `kind` | `user` or `team`; team-membership purpose only supports `user`. |
| `q` | Trimmed search text, minimum 2 and maximum 100 characters. |
| `limit` | Default 20, maximum 50. |
| `offset` | Non-negative; stable ordering by normalized display name and UUID. |
| `resource_type`, `resource_id` | Required for `purpose=share`; only `flow` or `project`. |
| `team_id` | Required for managing an existing team; omitted only when a Platform Admin is creating a new team. |

Authorization:

- Share search requires management authority for that exact resource.
- Team search requires ability to add members to that exact team or Platform Admin team-creation authority.
- Return active users only; return active, valid teams only.
- A team recipient need not include the sharer; eligibility is based on the configured collaboration domain.
- Single-instance deployments use their active local directory. Preserve applicable existing workspace restrictions; do not invent organization membership from a UUID field.

Response items contain only `id`, `kind`, `display_name`, and optional display avatar. Do not return user passwords, API keys, SSO claims, administrative flags, full profiles, or team rosters. Return `has_more`/`next_offset`, not an unrestricted directory dump.

Do not remove the superuser restriction from the existing `/api/v1/users/` endpoint to populate this picker. [S38]

### 10.3 Resource-effective capabilities — extend existing endpoint

Keep **`POST /api/v1/authz/me/permissions`** and its existing `permissions` field. Add a `capabilities` map keyed by the same requested resource UUIDs:

- `can_use`
- `can_edit`
- `can_create_flow` for projects
- `can_delete`
- `can_move`
- `can_manage_shares`
- `can_manage_publication`

Each boolean is derived from the same policy and operation/field-level rules as the actual route. Unsupported capabilities are false. Missing or unreadable resources receive no actions and false capabilities; the endpoint must not become a resource-existence oracle.

Resolve actual resource domains from the database. The request's existing `domain` field is a hint/filter, not authority to evaluate a flow under a more permissive foreign project. Respect the current resource/action batch bounds. [S14]

Do not compute `can_manage_shares` as `is_superuser || can_write` or `can_create_flow` as a generic `project:create` grant.

### 10.4 Access summary — new static route in the existing share router

Add **`GET /api/v1/authz/shares/summary?resource_type=...&resource_id=...`** before the dynamic `/{share_id}` route.

Return:

- Resource identity and display name only after read/management authorization.
- Whether the caller owns it and may manage shares.
- Direct grant rows, including canonical permission value, display mode, revision, and target name.
- Parent-project inheritance information the caller is allowed to see.
- The caller's effective access and bounded source explanations.
- A warning when an additional source means changing this grant will not remove editing/access.
- A legacy public/administrative-grant indicator where the caller is permitted to see it.

Support an optional `subject_user_id` for the owner/Platform Admin to inspect one recipient's effective access. Ordinary recipients cannot inspect arbitrary other users' access. Do not enumerate all team members to render a summary.

Paginate direct grants when needed and do not return private parent names/UUIDs merely to explain a source. Use a generic inherited-access explanation where the source itself is not readable.

---

## 11. Authorization service and guard changes

### 11.1 Implement the existing service methods

**Primary file:** `src/backend/base/langflow/services/authorization/service.py`

| Method/contract | Exact responsibility |
|---|---|
| `is_enabled()` | Report the configured enforcement state without turning initialization/policy failure into disabled enforcement. Keep readiness separate; when enforcement is configured but unavailable, reject affected requests rather than re-enable an owner-only or permissive fallback. |
| `supports_cross_user_fetch()` | True only for the implementing service; enables safe foreign-row resolution followed by enforcement. |
| Team/share capability probe | Advertise the complete contract, not schema presence; implement the default-compatible conditional-write support hook and derive its active requirement from verified enforcement state. |
| `enforce(...)` | Resolve actual resource scope, active identity, applicable grants, and action; deny unsupported/missing cases. |
| `batch_enforce(...)` | Load users/roles/teams/shares/resources in batches, preserve request order and result cardinality, reuse the same evaluator. |
| `get_resource_visibility(...)` | Return an exact `ResourceVisibilityScope` for the requested action; include direct and project-inherited team/user grants and applicable roles. |
| `list_visible_resource_ids(...)` | Implement the compatibility hook through the same policy if a caller uses it; do not create a divergent algorithm. |
| `get_effective_permissions(...)` | Resolve each resource's canonical domain and reuse the same batch decision logic. |
| `invalidate_*` / `sync_share` / `remove_share_rules` | Keep the interface valid and release any request-local metadata; no cross-request positive cache is retained by the selected evaluator. |
| Identity lifecycle hooks | Support new team-role/user lifecycle events without independently committing the caller's transaction. |
| Public-principal hooks | Preserve explicitly permitted public behavior as described in Section 13; never use authenticated allow-all behavior for anonymous callers. |

The factory already constructs `LangflowAuthorizationService`; keep that integration and its dependency accessor. Do not add an unrelated policy middleware that bypasses or duplicates these methods. [S03, S25]

### 11.2 Canonical resource registry

Centralize model lookup, owner field, project/workspace extraction, and supported action sets. Reuse the existing action enums. Keep flow, project, deployment, file, variable, knowledge-base, and other already-guarded resource families functional under enabled enforcement. [S15]

The new sharing UI is limited to flow/project, but switching on the service affects existing guards elsewhere. For resources outside the new feature, preserve verified owner/role behavior and existing share semantics; never respond with a blanket allow simply because that family was not in the UI requirements.

Resolve Memory Base records under the existing knowledge-base namespace where the current implementation does so. Handle component/catalog surfaces according to their existing policy rather than treating an arbitrary component ID as an unverified database resource.

Unknown actions and unresolved scopes deny. Scope-less `create` calls require verified intrinsic-creation context; a caller cannot manufacture ownership through `context` or JSON fields.

### 11.3 Scoped roles and inheritance

Honor the existing `AuthzRole.permissions`, role-parent relationships, and `AuthzRoleAssignment` scope. Validate parent chains with cycle detection and a bound even if data is malformed.

- Global assignments apply only as their explicit existing permission slugs allow.
- Workspace assignments apply only to server-resolved resources in that workspace.
- Project assignments apply only to the actual project/its applicable child resource scope.
- `org` assignments require an actual registered domain-resolution implementation. Do not silently map an unknown organization to global scope.
- Effective permissions include all surviving assignment sources; manual removal does not erase IdP-derived provenance.

Do not seed a broader global role to compensate for missing visibility code.

### 11.4 Guards and sensitive fields

Retain `ensure_flow_permission`, `ensure_project_permission`, `ensure_share_permission`, existing other resource guards, and privacy helpers. Add the resource-scoped share administration helper and team-management checks as cohesive additions in the same package.

Ensure the owner fast path cannot skip an applicable external-access or supported API-key ceiling. Audit owner overrides distinctly. Do not widen visibility from a request-controlled `workspace_id`, `folder_id`, `user_id`, or a permissions-domain hint. [S11, S18]

Apply restrictions to **effective changes**, not merely to fields echoed unchanged by a full-object client. Reject unauthorized changes clearly; do not silently save a partial resource while reporting full success.

### 11.5 Listing correctness

Update `services/authorization/listing.py` integrations so accessible rows are filtered before counting/pagination. Return compact project/workspace scopes when exact; return specific IDs when broader scopes would leak resources. Preserve credential restrictions when unioning owned rows—ownership must not bypass a narrower scoped credential.

Do not return `None` as an error fallback when it would silently restore an owner-only query or all-resource query. `None` is the interface's deliberate no-prefilter result, not an authorization-unavailable result. [S12]

Batch decisions and SQL prefilters must be tested for equivalence, including null owners, system examples, project-owner content access, inactive teams, and mixed grant sources.


## 12. Project and workflow integration

### 12.1 Projects — `api/v1/projects.py`

Update the existing functions and their shared helpers:

| Function/path | Planned change |
|---|---|
| `read_projects` | Include owned projects and authorized shared projects using the service's exact visibility scope; preserve owner display metadata. |
| `read_project` | Evaluate project access, then filter its flows using the same policy regardless of whether the caller owns the project. Eliminate the owner-only child branch that hides collaborator-created workflows. |
| `_new_project` / `create_project` | Preserve personal project creation without global role grants; validate any initial flow moves individually. |
| `_apply_project_update` | Allow shared editors to change name/description, but not authentication, parent scope, or ownership-bound settings. Process any flow/component membership operation through authorized move rules. |
| `update_project` / `upsert_project` | Apply canonical authorization and conditional revision checks in their shared mutation path. |
| `delete_project` | Authorize the project and the complete child/deployment deletion set before cascade deletion. |
| Project download/upload | Enforce authorized children before archive creation or extraction/persistence; use the same effective child policy as browsing. |

Do not assign a filtered list back into `Folder.flows`: its delete-orphan behavior can turn a read into deletion. Serialize a filtered response model instead, preserving the baseline safeguard. [S26]

For a non-owner project reader/editor, omit private `auth_settings` values and transport credential configuration. A content editor is not a project-authentication administrator. Do not return encrypted credential material merely because it is not plaintext.

### 12.2 Flows — `api/v1/flows.py`, `flows_helpers.py`, and `authz_route_dependencies.py`

Use the existing authorized dependencies for reads/writes/deletes. Extend `_read_flow`, `_new_flow`, `_patch_flow`, `_update_existing_flow`, `_canonicalize_flow_destination`, `_resolve_flow_destination`, and their callers rather than introducing shared-flow variants.

Required behavior:

- Include owned, directly shared, team-shared, and project-inherited workflows in the correct collections.
- An explicitly supplied inaccessible/missing destination fails; it is not silently replaced with the caller's default project. An omitted destination may still resolve to the caller's default.
- Creation inside a foreign project requires editable-project `flow:create` and preserves the creator as owner.
- Creation ignores a client attempt to nominate another owner and derives the owner from the authenticated actor.
- Updates never replace owner, folder, workspace, or filesystem scope with the editor's values.
- Check uniqueness against the stored flow owner's namespace, not the acting editor's namespace.
- For full-object updates, unchanged protected fields may be echoed without error; actual forbidden changes must fail rather than be silently dropped.
- Server-side authorization is rechecked for saves even if the editor loaded successfully earlier.

The baseline helper already contains ownership-aware shared-edit behavior and restricts several non-owner scope/publication changes. Extend that path consistently; do not remove its protections to make shared editing succeed. [S13]

### 12.3 Separate editable content from owner-managed fields

For a non-owner editor, allow changes to content fields such as `name`, `description`, `data`, `tags`, `icon`, `icon_bg_color`, and `gradient`, subject to existing validation/component policy. Editing the graph includes adding/removing its nodes and edges; removing a node is a `flow:write` content operation, not deletion of the workflow resource.

Treat these as owner/Platform-Admin-managed operations, not ordinary edit access:

- `user_id`, resource `id`, `folder_id`, `workspace_id`, `fs_path`.
- `access_type`, `mcp_enabled`, `a2a_enabled`, `a2a_card_overrides`.
- Publication identity/configuration such as `endpoint_name`, `action_name`, `action_description`, and changes of published resource kind.
- `locked` and attempts to bypass a locked/deployed resource's rules.
- Project `auth_settings`, `parent_id`, and other scope/authentication fields.
- Direct or derived changes that newly enable an external publication surface, including webhook eligibility where it is derived from graph content.

Ownership transfer is not implemented even for an arbitrary `user_id` update from a Platform Admin; it remains an explicit excluded feature.

Apply equivalent checks to derived fields. Rejecting a submitted publication flag is insufficient if saving a graph can recreate that publication change automatically.

### 12.4 Redacted graph data and safe saves

Reuse current secret-stripping and graph-validation utilities on shared reads and exports. Do not leak owner's credentials, encrypted secret values, or unrelated private configuration in a read response.

A shared editor saving a redacted graph must not accidentally erase retained hidden secret fields because the client only received placeholders. Preserve server-held secret material for retained nodes unless a separately authorized owner operation explicitly changes it. Do not merge arbitrary client-supplied internal metadata into the persisted graph.

Removing a node may remove its binding from the graph, but it does not delete the underlying credential/resource record. Any new dependency must be valid under existing dependency/credential policy; sharing does not clone a provider configuration.

Editable access deliberately permits trusted collaborators to change content that an owner may later execute. It is not a guarantee that the owner's later execution is isolated from the editor's authorship.

### 12.5 Exports, imports, batches, and duplication

- Export only authorized resources and sanitize secrets using existing helpers.
- Read access permits obtaining the readable graph; this is not a DRM or no-copy feature.
- Do not export internal share rows, team memberships, ownership assertions, or local optimistic revision tokens as authority in another instance.
- A copied/new flow is owned by its creator and receives no automatic copy of the original's direct grants. Its destination can confer project inheritance.
- A stable-ID import that would update an existing flow must authorize that existing flow, carry its current local revision precondition, and preserve its owner.
- Add a bounded per-item `expected_edit_revision` map to existing bulk/update/import request contracts where a single HTTP ETag cannot express multiple resources. Treat it as input-only precondition data.
- Validate the full intended mutation set before storage/provider side effects; do not apply authorized items and silently skip unauthorized items while returning whole-operation success.
- Preserve existing deployment guards and error sanitization in all paths.

### 12.6 Workflow identifier ambiguity

Existing endpoint names are owner-scoped rather than globally unique. For sharing-aware execution by endpoint name, do not use an unrestricted `.first()` and accidentally choose another owner's flow.

Keep owner-qualified name resolution where appropriate. Shared clients should use the workflow UUID. If more than one authorized candidate matches an unqualified name, return a sanitized ambiguity response instead of choosing arbitrarily. Never reveal the names/owners of inaccessible candidates.

---

## 13. Execution, dependencies, and other API families

### 13.1 Preserve actor identity

Shared authenticated execution uses the authenticated recipient as the execution principal. It does not impersonate the flow owner. Dependency lookup, messages, jobs, sessions, nested flows, and runtime credentials remain under that principal or separately authorized shared dependencies. [S24]

Distinguish:

- **Flow access granted**: the user can read/run/edit the saved flow.
- **Dependency available**: the user may use the resources that execution requires.

Report missing dependency access without copying owner credentials, granting broad resource access, or pretending the share failed to persist.

### 13.2 Route-family matrix

| Existing surface | Required integration |
|---|---|
| V1 `/run`, session run, advanced run | Reuse execute authorization for shared flows; retain V1's owner-only client-tweak restriction; use the caller's runtime identity. |
| Interactive `/build/{id}/flow` | Can use runs the saved graph; Can edit may submit authorized unsaved graph content through the existing writer-override helper. |
| V2 workflow execution | Same saved/unsaved distinction supported by the existing runtime; require actor execute access and writer authorization for graph overrides. |
| HITL resume / job continuation | Retain the original admitted job principal and recheck current relevant execute permission at resume. |
| OpenAI-compatible responses / voice | Apply the same flow execute admission where already share-aware; do not expose owner secret/provider error details. |
| Monitoring, history, trace, session, job APIs | A flow share is not automatic access to other users' historical messages, job streams, or provider details. Preserve their separate ownership checks. |
| Legacy/project MCP | Keep existing owner-scoped admission. A user/team flow share does not automatically authorize these transports. |
| Webhooks | Keep existing owner-scoped admission and server-generated webhook input mapping. |
| Protected A2A | Keep its owner-scoped protected admission contract. |
| Public flow / public A2A | Keep distinct explicit-public admission and anonymous runtime isolation; targeted shares never make a resource public. |
| Deployments | Keep actor authorization distinct from the provider owner's execution namespace; no implicit credential-sharing extension. |

These limits prevent the plan from claiming universal transport sharing when the existing release intentionally treats some families differently. [S23, S24]

### 13.3 Non-editable means no graph substitution

Ordinary input values, selected allowed outputs, and appropriately isolated session IDs are not saved graph edits. Continue to accept them under execute access.

Non-editable recipients cannot supply a replacement graph, component code, or protected parameter overrides through another runtime endpoint. Follow the endpoint-family contract for whether disallowed overrides are rejected or omitted; document any deliberate normalization and test that the override never affects the graph that actually executes.

Do not change V1's owner-only tweak rule merely to make its behavior match an editor-facing build endpoint. The existing `flow_data_override.py` is the writer-aware integration point for supported chat/V2 surfaces. [S36]

### 13.4 Public behavior when authorization is enabled

Enabling the new service must not accidentally disable or broaden existing explicitly public flows.

Implement the existing public-principal hooks for this trusted single-instance deployment using the exact resource and deployment-owned domain, not caller-provided Host/domain claims. Reuse canonical/legacy-public grant checks and allow only the read/execute public actions already supported by the runtime. No public discovery is added to ordinary lists.

Do not use `enforce()`'s authenticated ownership/role path for anonymous users. Do not change `access_type` when creating/removing a targeted share. Preserve existing public file/session isolation and error sanitization. If a different registered plugin cannot safely resolve the public domain, fail closed rather than claiming anonymous support. [S28]

### 13.5 Component and global runtime policy

Team/resource permissions do not bypass existing custom-component, model-provider, file-path, catalog, or execution policies. Editable access authorizes ordinary content editing; it is not a license to execute a component disallowed by the installation.

---

## 14. Concurrent editing and stale requests

### 14.1 Workflow/project optimistic concurrency

Use the new `edit_revision` fields from Section 6. Return strong ETags on individual reads/updates:

- Flow: `"flow:<uuid>:<edit_revision>"`.
- Project: `"project:<uuid>:<edit_revision>"`.

Require `If-Match` on updates/deletes of existing resources when the native collaboration contract is enabled. Missing preconditions return `428`; stale preconditions return `412 RESOURCE_CHANGED`. Authorization runs first so an unauthorized caller does not learn a revision. In the positively established enforcement-disabled owner contract, retain legitimate header-less operation acceptance in the same mutation helper. Always validate an explicitly supplied condition. No client-controlled option, missing capability response, or service error may choose the less restrictive contract.

For a create-only stable-ID PUT operation, support `If-None-Match: *`; a conflicting existing resource must not be silently updated. Native collaboration clients distinguish create from updates to a resource they have read. Preserve the established owner upsert contract when collaboration is disabled; do not add a replacement PUT endpoint.

Mandatory preconditions are an intentional change for enabled collaboration, not a claim that old callers already supply them. Update all in-repository writers in the same implementation: editor autosave, rename, lock/publication controls, moves, API clients/examples, imports/batches, and agentic tools that persist a flow/project. The updated UI sends its observed revision in both modes. Include success-test fixtures and direct-API browser helpers in that inventory. Each changed expectation must be linked to this requirement in the Section 23.7 ledger; retain separate missing/stale-header negative cases and real UI-persistence checks. Do not auto-fetch a newer revision and replay an old payload, bypass required conditions for superusers, or disable enabled-mode checks to keep old tests green.

### 14.2 Database enforcement

A row lock alone does not prevent lost updates from two previously loaded editors. After authorization, atomically compare the caller's observed revision with the stored revision and increment it alongside the content write. A zero-row conditional update means a conflict, not success.

For ORM paths, use one consistent optimistic-version mechanism or a centralized compare-and-update helper; do not mix an unchecked ORM update with a checked API path. Keep existing `lock_flow_for_update` and deployed/locked-resource guards for their current purposes. [S35]

A trusted internal mutation that derives its patch from fresh data under the same transaction can use the observed revision from that read. An internal tool holding an old graph must carry the revision it actually observed; it cannot opt out by labeling itself internal.

### 14.3 Editor behavior

- Keep the revision from the latest authoritative resource response.
- Send it with autosave and update it only after success.
- On `412`, stop automatic retries, preserve unsaved local content, and display **This workflow changed. Reload the latest version before saving.**
- On permission loss, stop saves, disable mutation controls, preserve local unsaved state without posting it, and explain that editing access changed.
- Do not automatically fetch a newer revision and retry the stale graph; that would defeat concurrency protection.
- Distinguish locked-resource errors, stale-content errors, and revoked editing rights.

Do not implement live cursors, real-time graph merging, or an operational `AuthzEditLock` lease system merely because an edit-lock table already exists. Optimistic concurrency is the selected protection; the existing table is not evidence of complete collaborative editing.

### 14.4 Revocation versus work already admitted

The guaranteed boundary is **new admission after a committed revocation/downgrade**. Fresh requests and rechecked resumes must observe current canonical policy. The UI may display cached controls briefly, but the new backend request is authoritative.

This feature does not cancel already-admitted execution or retroactively undo an in-flight operation that was authorized before the revocation committed. Document this boundary instead of claiming instantaneous cancellation of all ongoing work. Before a mutation is applied, perform its current permission and concurrency checks in the normal mutation path.

---

## 15. Lifecycle, revocation, auditing, and transactions

### 15.1 Team invariants on every writer

Every committed team must have at least one membership. Every active team must have an active Admin. Enforce these invariants on:

- Create, single-member add/remove, role changes, and batched roster changes.
- Team activation/deactivation.
- User deactivation/deletion.
- Applicable authoritative membership synchronization.
- Legacy data repair and administrative scripts introduced by this work.

Do not rely only on the UI or an in-process mutex.

### 15.2 Account and authoritative-source changes

Security-driven user disablement or authoritative membership removal must not be refused merely to preserve a team administrator.

- If memberships remain but no active Admin remains, atomically deactivate the team with `inactivation_reason="no_active_admin"`. Active-team shares no longer grant access.
- If account deletion or authoritative membership removal would leave no memberships, retire that empty team atomically and remove its team-targeted grants, while retaining all actual resources and audit evidence.
- A manual last-member removal continues to return `409`; the caller must nominate a replacement or request an authorized team deletion.
- Only Platform Admin reactivation is supported, and it must verify a valid roster and active Admin. Do not automatically reactivate a suspended team when a disabled user logs in again.
- Authoritative source changes must not be treated as an empty authoritative roster when the provider snapshot is incomplete, absent, malformed, or over-limit.

The automatic retirement rule applies only to unavoidable account/source lifecycle removal, not as a way for ordinary team members to invoke team deletion through a manual endpoint.

**Hard account deletion and resource ownership:** do not create ownerless live resources or implicitly transfer ownership. If the user still owns canonical projects/workflows or other resources whose deletion would cascade into shared content, reject hard deletion with `409 RESOURCE_OWNERSHIP_REQUIRES_DISPOSITION` and a bounded impact explanation. The Platform Admin must first resolve those resources through existing authorized operations; account disablement and credential revocation remain available immediately and are not blocked by this requirement. Once hard deletion is permitted, the team-retirement cleanup must not delete resources merely because they were shared with that team. Update the user-delete route and its tests to prevent unchecked ORM cascades from bypassing this rule.

### 15.3 Transaction and lock ordering

Use the repository's existing session/retry abstractions. At minimum, all affected membership writers must serialize through a team-row lock and re-read the current roster before validating/applying a mutation.

For PostgreSQL, use transaction-scoped row locks. For SQLite, `SELECT FOR UPDATE` is not the concurrency guarantee: obtain its write transaction/parent-row write lock before invariant reads and use bounded database-lock retries. Reuse `database/lock_retry.py`; do not sleep/retry indefinitely inside HTTP handlers.

Use one documented lock order across multi-entity operations: existing plugin preflight lock, affected user rows sorted by UUID, affected team rows sorted by UUID, affected projects/flows in deterministic order, then membership/share rows. Preliminary identifier reads are hints; re-read the canonical state under the acquired locks and retry boundedly if the affected set changed.

A plugin lifecycle hook may stage state in the caller's transaction but must not independently commit or roll back it. [S03, S16]

### 15.4 Revocation without cross-worker cache dependence

The selected native evaluator reads canonical committed state for every new admission. Consequently, deleting a share or removing/deactivating a team does not depend on another worker receiving a best-effort invalidation message. Do not reuse an old authentication transaction snapshot as the authoritative policy read for a later admission: establish a fresh short-lived read boundary when necessary, and close it before long-running execution.

Do not cache effective access in JWT claims, `User` fields, long-lived process dictionaries, or saved workflow objects. The UI's cached display is advisory and must never authorize a backend mutation.

Where another existing service caches metadata/graphs, preserve its independent identity/source validation and invalidate affected UI queries. A cached graph does not constitute a cached authorization grant.

### 15.5 Audit mutations in the canonical transaction

Use the existing `authz_audit_log`, credential context, actor identity, and `details.event` conventions. Add a helper in the existing authorization audit module to stage a **mutation** record in the same database transaction as team/share/role changes covered by this feature.

Required events:

- Team created/updated/activated/deactivated/deleted/retired by lifecycle repair.
- Team member added/removed and role changed.
- Share created, level changed, removed, or cleaned up because its target/resource was deleted.
- Permission-relevant project/flow move and publication denial where already audited.
- Migration repair outcomes and conflicts that prevent a requested invalid state.

Record actor ID/type, affected IDs, previous/new role or permission where applicable, reason, timestamp, and event identity. Do not log passwords, bearer tokens, API keys, raw identity-provider claims, secret values, or full graphs.

Avoid duplicate post-commit mutation audit rows for operations now staged atomically. Guard **decision** audit rows remain separately classified; UI capability probes are not actual mutations. [S33]

If staging a required mutation audit record fails, roll back the mutation. Post-commit publication failure must not turn a durable success into a misleading failure encouraging duplicate writes. Ordinary decision-audit durability retains the explicit existing setting.

### 15.6 Resource deletion and dangling grants

Sharing targets are polymorphic and cannot rely on one conventional foreign key to every resource type. Explicitly remove affected shares on supported resource deletion; clean corresponding team-targeted grants on team retirement/deletion. [S04]

Never treat a stale share pointing to a missing/inactive recipient, team, or resource as sufficient access. Stable-ID imports must not resurrect grants belonging to a previously deleted resource.

---

## 16. Frontend implementation

### 16.1 Platform administration

Implement **Teams** under the existing administration shell. At the reviewed OSS baseline, the shell/menu hook is incomplete; add one protected administration layout only where absent, through `CustomRoutesStorePages` and `CustomAdminPageMenuItem`. Do not introduce both `/admin` and a separate competing administration application. Preserve an existing customized administration route if the implementation checkout already provides it. [S22]

For the baseline OSS target, use `/admin/teams` as the Teams tab route. Only a Platform Admin can enter the platform administration area. Reuse existing user-management views if present; a new user-administration redesign is not part of this feature.

The Teams page includes:

- Searchable/paginated team list, status, member count, active Admin count.
- Create Team dialog with name, optional description, initial users, and roles.
- Required nomination of an initial Team Admin before saving.
- Team detail with paginated roster and role/source badges.
- Add/remove members, role changes, rename/description edits, activation/deactivation, deletion.
- Clear errors for last-member/last-admin conflicts and source-managed membership.
- Repair indication for `no_active_admin`, without offering a misleading automatic promotion.

### 16.2 Team-scoped management

Provide `/teams` for a user's own teams and teams they may manage. Reuse the same team-management components with server-derived capabilities; do not duplicate business logic or create a second set of APIs.

Team Admins/Maintainers see only permitted controls. Team Users may see their roster but not mutation controls. The backend still evaluates the operation independently.

### 16.3 Existing project and workflow Share hooks

Implement:

- `customization/components/custom-flow-share-action.tsx`.
- `customization/components/custom-resource-share-action.tsx` for the `project` case.

Both open the same **ResourceShareDialog** component. Keep existing extension behavior for non-target resource types rather than unexpectedly exposing unfinished sharing UI.

The project sidebar already places the hook between its existing commands inside `select-options.tsx`. The workflow card/list dropdown and editor dropdown already have a flow-share extension hook. Reuse these placements and prevent menu clicks from triggering navigation. [S19, S20]

### 16.4 Dialog behavior

Title: **Share “{resourceName}”**.

Controls:

1. Recipient type: **User** or **Team**.
2. Debounced recipient search through the restricted search endpoint.
3. Access selector:
   - **Not editable — Can use**: “Can view and run. Cannot change this resource.”
   - **Editable — Can edit**: “Can view, run, and edit. Cannot reshare or delete it.”
4. Save action and visible request state.
5. Existing grants with editability controls and Remove actions for authorized managers.
6. Inheritance/effective-access explanation and legacy grant indicators.

For a project, describe that access applies to its current and future workflows, and that editable access allows creating workflows inside it. For a team grant, describe that eligible current and future members receive access.

Do not include public-link controls, non-user email invitations, or an undocumented third access mode in this dialog.

A non-manager may see a read-only **Access** summary where useful, but cannot see an enabled Share mutation control. Compute availability from `can_manage_shares`, not global admin status or edit permission alone.

### 16.5 Resource discovery

Show shared projects in the existing project navigation with an owner/shared indication. Show individually shared workflows without granting access to their private parent project.

Add a **Shared with me** filter or view within the existing homepage data flow. It is a view over existing accessible resources, not separate persistence or a copied-workflow collection. Count/page using the same backend visibility policy as normal lists.

Use owner-qualified display names when different owners have identically named projects/workflows. Do not change the underlying uniqueness constraints to force global names.

### 16.6 Editing and execution controls

Wire `PermissionsProvider` and the enriched capability response into:

- Graph/node/edge editing and deletion, component property forms, undo/redo mutations, paste/import into a graph, and autosave.
- Rename/description controls and bulk operations.
- Create/import workflow into a project.
- Run/Playground and supported unsaved-graph execution.
- Lock, publication, move, and delete controls according to their separate capabilities.

Disable protected actions while permission state is loading or unavailable in enforcement-enabled contexts. The baseline UI's fail-open utility must not be the behavior of a shared editor awaiting permission data. Preserve non-enforcing OSS behavior only when the server explicitly reports that mode; an error is not an off flag. [S21]

### 16.7 Query and session handling

Extend existing React Query request-processor hooks rather than making ad hoc fetch calls. Include user identity, resource type/ID, and relevant filter inputs in query keys; never cache a permission result under a resource-only key across user changes.

After share/team/member/role changes, invalidate affected permission, resource-list, project-content, and share-summary queries. Existing user logout/account switching clears authorization-related query data and editor state.

On mutation denial, refetch capabilities and render the correct state. On a stale revision, retain unsaved user content but do not retry automatically.

Use the project's existing dropdown/dialog/table/form components, translation keys, keyboard/focus conventions, and error presentation. Add tests for behavior and accessibility of this feature; do not expand into unrelated themes or visual redesign.

---

## 17. Authentication and deployment configuration

### 17.1 Retain authentication

Keep existing JWT sessions, API-key authentication, and external-identity provisioning. Team/resource decisions use the authenticated active identity returned by those paths. No new session-token format is needed.

Do not trust client-submitted `user_id`, team role, or username to identify the acting user. A request that fails authentication cannot use the team directory or sharing APIs.

Do not embed team permissions into a new long-lived token and rely on token refresh for revocation. Preserve existing credential type/API-key metadata in authorization context. [S17, S18]

### 17.2 Enhanced fork distribution defaults

Document and configure the enhanced deployment built from `yazeedhasan97/langflow` to use:

```dotenv
LANGFLOW_AUTO_LOGIN=false
LANGFLOW_AUTHZ_ENABLED=true
LANGFLOW_AUTHZ_AUDIT_ENABLED=true
LANGFLOW_AUTHZ_AUDIT_DURABLE=true
```

Keep existing secure credential generation, secret management, and bootstrap-user configuration; do not embed an administrator password in Compose or the plan. Use secure cookies for HTTPS deployments while retaining an explicitly documented local-development configuration.

The shared LFX settings package also serves other hosts. Do not indiscriminately change its global defaults for every downstream consumer. Apply enhanced-distribution defaults through the actual Langflow startup/deployment configuration and validate that the enforcing implementation is registered.

Configure baseline regression fixtures and enhanced collaboration fixtures explicitly. Preserve the existing default-host/CLI behavior that is outside this feature; the dedicated collaboration suite must use the enhanced settings above. Test disabled-mode ownership preservation and enabled-mode enforcement separately on the same implementation. An auto-login regression test must not be counted as a distinct-user authorization test. [CI05, CI08, CI09]

Only update existing deployment manifests that actually ship the enhanced application. Do not create new Compose stacks, staging environments, or separate authorization services. The implementation must inventory those actual manifest paths before editing them; this plan does not invent a deployment filename.

### 17.3 Existing external authentication

Preserve verified group-reconciliation and incomplete-snapshot semantics. Do not map an external claim named `admin` directly into `is_superuser` or the new Team Admin role without an explicitly authorized mapping.

Existing external access ceilings and any actually registered API-key scope restrictions remain upper bounds. The new team role cannot override them. Do not claim API-key scoping support merely to satisfy a capability probe when the implementation has no scope data/enforcement.

Changing native logout/token-revocation design, adding MFA, and replacing external SSO are outside this implementation. Do not describe ordinary logout as revoking every copied bearer token.

### 17.4 Readiness and operator visibility

At startup, report the actual authorization service identity, enforcement readiness, enabled sharing capabilities, and invalid legacy-team count without printing secrets. With the enhanced feature enabled, fail initialization if required schema/service functionality is absent rather than quietly running a no-op authorization service.

These checks validate configuration/data invariants; they are not a runtime test suite and must not run tests during deployment.


## 18. File-by-file change inventory

All paths below are relative to **`yazeedhasan97/langflow`**, not the upstream working tree. Upstream links in the evidence appendix explain inherited code; they are not edit or push targets. Prefixes are exact abbreviations for readability:

- **B** = `src/backend/base/langflow/`
- **L** = `src/lfx/src/lfx/`
- **F** = `src/frontend/src/`

An entry marked **new** is a proposed addition. A generated migration's exact revision prefix must be produced against the actual Alembic head; no fabricated revision is prescribed.

### 18.1 Existing backend and shared-contract files

| Path | Exact implementation responsibility |
|---|---|
| `B/services/database/models/auth/authz.py` | Add membership role/timestamp/check/index, team inactivation reason, share revision/timestamp. Keep canonical tables and existing IDs. |
| `B/services/database/models/auth/__init__.py` | Export any newly introduced model enums/types without changing existing imports. |
| `B/services/database/models/flow/model.py` | Add server-managed `edit_revision`; expose it on appropriate read schemas; exclude it from editable payload data. |
| `B/services/database/models/folder/model.py` | Add server-managed `edit_revision`; update project read schemas and safe shared projections. |
| `B/services/database/models/flow/guards.py` | Integrate revision conflict checks with existing locked-flow checks; do not confuse row locks with optimistic versioning. |
| `B/alembic/versions/` | Generate new forward migrations for fields/checks/indexes and deterministic scalar backfills. Do not edit released foundations migration. |
| `L/services/authorization/base.py` | Add team-role mutation event, non-secret context/capability contract, and corresponding default lifecycle invalidation support. Keep LFX independent from ORM. Add the optional default-false `supports_conditional_writes()` hook; do not add a new abstract-method requirement for existing plugins. |
| `B/services/authorization/service.py` | Upgrade the existing class to the selected native enforcing implementation. Implement enforcement, batched decisions, visibility, effective permissions, and relevant public/lifecycle hooks. |
| `B/services/authorization/factory.py` | Preserve the single factory registration and verify it resolves the implementing class. Adjust typing only as needed. |
| `B/services/authorization/guards.py` | Resource-scoped share administration, typed team operation checks, owned-creation context, consistent credential ceiling and operation checks. |
| `B/services/authorization/actions.py` | Retain canonical resource action values. Add only any typed team-operation vocabulary actually required, without pretending `project:execute` already exists. |
| `B/services/authorization/listing.py` | Integrate exact SQL prefilters; maintain owner/credential restrictions and parity with per-object decisions. |
| `B/services/authorization/fetch.py` | Keep capability-gated foreign-resource fetch; preserve error privacy; use locking/re-read options for mutation. |
| `B/services/authorization/lifecycle.py` | Route membership-role and unavoidable account/source events through the same invariant/policy lifecycle. |
| `B/services/authorization/audit.py` | Add atomic mutation-audit staging into the existing table; preserve decision/mutation distinction and actor context. |
| `B/services/authorization/public_access.py` | Keep explicit public-grant/anonymous behavior correct with the new registered service. No targeted-share-to-public conversion. |
| `B/services/authorization/flow_data_override.py` | Reuse writer-aware unsaved-graph authorization; update misleading ownership wording where necessary. |
| `B/services/authorization/decorators.py` | Verify internal/agentic/nested-flow callers obey the same canonical actor and action policy. |
| `B/api/v1/schemas/authz_teams.py` | Add initial members, role fields, batch membership patch, safe counts/capabilities, source rules, and response shapes. |
| `B/api/v1/authz_teams.py` | Replace duplicate route mutation logic with domain helpers; implement team-role permissions and new member PATCH. |
| `B/api/v1/schemas/authz_shares.py` | Add revision/timestamp and summary types; preserve API scope/permission vocabulary and public restrictions; keep the two-mode selection in the new dialog without weakening backend checks. |
| `B/api/v1/authz_shares.py` | Complete resource/target checks; conditional updates/deletes; pre-pagination visibility; summary route before dynamic ID route; canonical audit transaction. |
| `B/api/v1/authz_me.py` | Add derived capability map; resolve domains server-side; support unknown/missing resources without privacy leakage. |
| `B/api/v1/projects.py` | Shared project discovery; collaborator-created child visibility; content versus auth field restrictions; revision checks; safe complete-set deletion. |
| `B/api/v1/projects_files.py` | Inherited flow export/import authorization, safe graph serialization, and per-item overwrite preconditions. |
| `B/api/v1/flows.py` | Shared list/read/write/execution entry behavior, field protections, request preconditions, batch/upload/download coverage. |
| `B/api/v1/flows_helpers.py` | Preserve owners/storage/destinations; reject explicit inaccessible destinations; centralize conditional mutation and no-op semantics. |
| `B/api/v1/authz_route_dependencies.py` | Enforce canonical source/destination actions and resource-specific error behavior before sensitive operations. |
| `B/helpers/flow.py` | Audit internal lookup callers; keep caller identity; handle shared endpoint-name ambiguity without unqualified first-match resolution. |
| `B/api/v1/users.py` | User disable/delete cleanup of team invariants, owned-resource hard-delete protection, and impact errors; do not loosen the administrator user-directory endpoint. |
| `B/services/auth/service.py` | Preserve credential/external-group behavior; connect applicable user/directory lifecycle events to team invariants without inventing SSO role mapping. |
| `B/api/v1/api_key.py` | Verify existing credential lifecycle and scope context continue to constrain newly enabled authorization; no new API-key subsystem. |
| `B/api/router.py` and `B/api/v1/__init__.py` | Register new capabilities and recipient-search routers once. Preserve existing API prefixes. |
| `B/__main__.py` | Add the offline team-check/repair subcommands to the existing authz CLI group; do not duplicate the command group. |
| `B/services/deps.py`, `B/services/utils.py`, and existing startup wiring | Verify the single service is selected and readiness is enforced at the existing initialization boundary; change only the actual wiring needed. |
| `.env.example` and existing enhanced-distribution startup/deployment configuration | Document/set distinct-user mode and actual enforcement. No test execution on deployment. |

Existing execution files requiring policy-coverage verification, with modifications only at the affected boundary:

`B/api/v1/endpoints.py`, `B/api/v1/chat.py`, `B/api/v1/openai_responses.py`, `B/api/v1/voice_mode.py`, `B/api/v1/mcp.py`, `B/api/v1/mcp_projects.py`, `B/api/v1/a2a.py`, `B/api/v1/deployments.py`, `B/api/v2/workflow.py`, `B/api/v2/hitl.py`, `B/api/v2/workflow_public.py`, and their referenced runtime/monitoring helpers. The endpoint matrices are the inventory to reconcile; do not rewrite these subsystems wholesale. [S23, S24]

### 18.2 Proposed new backend modules

| New path | Responsibility |
|---|---|
| `B/services/authorization/policy.py` | Pure typed policy rules: team operations, grant-to-action mapping, inheritance, capability derivation. No database writes. |
| `B/services/authorization/repository.py` | Batched canonical policy/resource reads and shared SQL predicate construction used by the service. No second persistence model. |
| `B/services/authorization/team_management.py` | Single transaction-aware team/membership/role mutation implementation and invariant enforcement. |
| `B/services/authorization/share_management.py` | Resource-scoped share mutation/cleanup logic called by the existing router and relevant lifecycle paths. |
| `B/api/v1/authz_capabilities.py` | Authenticated product/service capability endpoint. |
| `B/api/v1/authz_recipients.py` | Restricted, bounded recipient directory endpoint. |
| `B/api/v1/schemas/authz_capabilities.py` | Typed capability responses if kept out of route modules. |
| `B/api/v1/schemas/authz_recipients.py` | Recipient search query/result models and normalization. |
| `B/cli/authz_team_preflight.py` | Offline team consistency report and explicit legacy-data repair command. |

Do not add these files if the actual checkout already has an equivalent canonical module; extend that module and record the exact final path. This rule avoids duplication, not feature deferral.

### 18.3 Existing frontend files

| Path | Exact implementation responsibility |
|---|---|
| `F/customization/components/custom-admin-page-menu-item.tsx` | Render the authorized administration entry to the one actual admin route. |
| `F/customization/utils/custom-routes-store-pages.tsx` and `F/routes.tsx` | Integrate the admin Teams and team-scoped pages through the existing confirmed hook; do not add duplicate routes. |
| `F/customization/components/custom-flow-share-action.tsx` | Implement flow Share action using derived capabilities and the common dialog. |
| `F/customization/components/custom-resource-share-action.tsx` | Implement project sharing without exposing unfinished other-resource UI. |
| `F/components/core/folderSidebarComponent/components/sideBarFolderButtons/components/select-options.tsx` | Keep Share in the existing three-dot menu; wire capability state and dialog trigger. |
| `F/components/core/folderSidebarComponent/components/sideBarFolderButtons/index.tsx` | Shared project labels, creator/owner visibility, create/import/rename controls, project revisions. |
| `F/pages/MainPage/components/dropdown/index.tsx` | Workflow menu sharing, conditional mutation state, and scope-safe commands. |
| `F/components/core/flowToolbarComponent/components/deploy-dropdown.tsx` | Shared dialog entry and separation of edit versus publication permissions. |
| `F/contexts/permissionsContext.tsx` | Consume capabilities and fail closed for unresolved enforcement-enabled shared editing. |
| `F/utils/permissionUtils.ts` | Keep pure capability normalization/decision behavior consistent; unknown permission is not allow in the enabled collaboration context. |
| `F/controllers/API/queries/permissions/use-get-effective-permissions.ts` | Extend types/keys/response handling while keeping the existing request processor. |
| `F/controllers/API/queries/flows/use-patch-update-flow.ts` | Accept observed revision, send If-Match, consume updated revision/ETag, expose stale-versus-denied errors. |
| `F/hooks/flows/use-autosave-flow.ts` | Stop unauthorized/stale saves, preserve local content, avoid stale overwrite retry. |
| `F/types/permissions/index.ts` | Add response capabilities and supported feature types without deleting the existing permission map. |
| `F/types/flow/index.ts` | Add server revision and relevant derived metadata; do not use one global editable flag as grant storage. |
| `F/pages/MainPage/entities/index.tsx` | Add project revision and shared/owner response fields used in navigation. |
| `F/stores/flowsManagerStore.ts` and `F/stores/foldersStore.ts` | Preserve revisions/caller-specific state through existing save/update flows; clear on identity changes. Resolve any store extension in the actual checkout. |
| Existing folder mutation hooks under `F/controllers/API/queries/folders/` | Send project revision preconditions for rename/update/delete and retain authorized destination behavior. |
| Existing translation catalogs and `F/utils/apiError.ts` | Add this feature's labels/errors and support structured error codes, without changing unrelated copy/design. |
| `src/frontend/playwright.config.ts` | Add the same-file, CI-wired authorization-test mode and explicit path/tag selection; separate collection/execution/report settings from the original auto-login regression harness without bypassing either suite. [S40, CI09] |

Where a folder/table/store module is split differently in the implementation checkout, follow the imported canonical implementation and record the resolved filename. Do not create a new module just to match an outdated filename.

### 18.4 Proposed new frontend modules

| New path | Responsibility |
|---|---|
| `F/pages/AdminPage/index.tsx` | One administration layout for the baseline OSS target, only if absent. |
| `F/pages/AdminPage/TeamsPage/index.tsx` | Platform Teams tab using common team components. |
| `F/pages/TeamsPage/index.tsx` | Current user's scoped team-management view. |
| `F/components/core/teamManagementComponent/index.tsx` | Reusable list/detail/roster management; subcomponents may be colocated here. |
| `F/components/core/resourceShareDialog/index.tsx` | One user/team share dialog for flows and projects. |
| `F/types/authz/index.ts` | Team roles, team membership, recipients, share summaries/revisions, and capability response types. |
| `F/controllers/API/queries/teams/index.ts` | Exports for typed team CRUD/member/role hooks in this directory. |
| `F/controllers/API/queries/shares/index.ts` | Exports for typed share CRUD/summary hooks in this directory. |
| `F/controllers/API/queries/authorization/index.ts` | Capability and recipient-search hooks; share the existing API client/request processor. |

The new directories can contain small colocated files where the repository convention expects one hook per file. Keep one implementation of each operation and export it from these barrels.

### 18.5 Existing CI, repository instructions, and test-selection files

Section 23.6 supplies the exact per-file CI changes. They are part of implementation completeness, not optional follow-up work:

| File/group | Required integration |
|---|---|
| `.github/workflows/ci.yml` and `.github/changes-filter.yaml` | Preserve original selections/checks; add required authz jobs, full-validation inputs/conditions, correct base/ref handling, and non-skipped success checks. |
| `.github/workflows/typescript_test.yml` | Typed authz-mode input, matching discovery/execution, explicit supported tags, feature no-retry acceptance, collision-free reports, complete journey accounting. |
| `.github/workflows/python_test.yml` and `.github/workflows/jest_test.yml` | Preserve actual test coverage, handle genuinely optional secrets and fork-read-only reporting without hiding failures. |
| `.github/workflows/docker_test.yml` and `scripts/ci/test_docker_images.sh` | Exact candidate checkout, available authorized runner, all original build/package assertions, disposable-runner cleanup safety. |
| `.github/workflows/migration-validation.yml`, `.github/workflows/ci-scripts-test.yml`, and route-matrix scripts/tests | Actual base comparison, original migration checks plus feature transaction tests, complete changed-path coverage and validator parity. |
| `.github/workflows/lint-js.yml`, `.github/workflows/docs_test.yml`, and applicable reusable jobs | Ensure claimed candidate checks use the intended ref and retain selected lint/build/accessibility checks. |
| `CONTRIBUTING.md`, `AGENTS.md`, applicable nested instructions, `.pre-commit-config.yaml` | Read and follow actual rules; do not weaken upstream standards or protections. Document the fork's deliberate behavioral changes without rewriting historical upstream claims. |

No workflow or repository file is modified by generating this plan. These rows specify changes for the later implementation.

---

## 19. Required verification and end-to-end scenarios

**Current status of every test below: not run.** These are acceptance instructions for the future implementation, not test results.

### 19.1 Test strategy

Final fork acceptance includes **all applicable inherited upstream CI/regression checks run on the fork candidate, plus the feature checks in Section 23**, not only the new feature tests below. Upstream PR review/queue acceptance is a separate conditional outcome, not a prerequisite for fork completion. Focused testing during development reduces redundant work; it does not permit skipping an existing required/selected test, lowering coverage thresholds, or concealing a regression.

Use test-driven/behavior-driven implementation for the changed authorization boundaries. Concentrate tests on policy, identity, transactions, concurrency, resource visibility, and the actual UI flows. Do not add broad theme, animation, or unrelated component regression work. The scenario IDs below are acceptance coverage, not a requirement for a separate expensive end-to-end test per row; parameterize policy/route cases and reserve browser tests for the eight connected journeys.

Tests asserting the new behavior must instantiate the **actual production authorization service**, not only the repository's `_policy_double.py` test enforcer. Existing test doubles can remain for interface-isolation tests, but they are not proof that the new service enforces anything. [S32]

Use real database transactions for invariant, pagination, cleanup, and concurrency tests. Cover SQLite and PostgreSQL where the implementation uses different locking/migration behavior. Use a deterministic no-external-service flow for most run tests; provider stubs are sufficient for identity-boundary checks and do not require paid API calls.

### 19.2 Policy and administration acceptance matrix

| Test ID | Scenario | Expected result |
|---|---|---|
| AUTH-01 | Anonymous team/share/directory request | Rejected without private directory/resource data. |
| AUTH-02 | Inactive user with a valid unexpired token | Cannot acquire team/resource access. |
| AUTH-03 | Ordinary owner opens Share | Allowed without Platform Admin role. |
| AUTH-04 | Team Admin attempts platform administration | Denied; `is_superuser` unchanged. |
| AUTH-05 | Authorization flag enabled with a non-implementing stub | Sharing unavailable; no false success or widened access. |
| AUTH-06 | Canonical policy database unavailable | Deny/unavailable before side effects; no allow fallback. |
| AUTH-07 | External viewer ceiling plus an editable share | No edit; the narrower ceiling wins. |
| AUTH-08 | Existing scoped API-key restriction plus owner/team grant | Scope restriction remains enforced when that feature is actually supported. |
| TEAM-01 | Create a team with valid initial Admin and User | One transaction; team never appears empty. |
| TEAM-02 | Create a team with no members | Rejected; no team row. |
| TEAM-03 | Create active team without active Admin | Rejected; no partial roster. |
| TEAM-04 | Duplicate user in initial roster | Rejected before persistence. |
| TEAM-05 | Team Admin changes roles within own team | Allowed within invariants. |
| TEAM-06 | Team Admin modifies a different team | Denied. |
| TEAM-07 | Maintainer adds/removes ordinary manual User | Allowed. |
| TEAM-08 | Maintainer promotes self or modifies Admin/Maintainer | Denied, including batch endpoint attempts. |
| TEAM-09 | User attempts membership mutation | Denied. |
| TEAM-10 | Remove final member manually | `409`; roster unchanged. |
| TEAM-11 | Demote/remove final active Admin manually | `409`; role/roster unchanged. |
| TEAM-12 | Atomic replacement of final Admin | Succeeds with valid final roster and no invalid committed state. |
| TEAM-13 | Two concurrent final-admin removals/demotions | At most a valid final state commits on both database engines. |
| TEAM-14 | Disable final active Admin account | Account disabled; team suspended; team access ends. |
| TEAM-15 | Delete account that is final team membership | Team/grants retired atomically; actual flows/projects retained. |
| TEAM-16 | Reactivate suspended team without active Admin | Rejected. |
| TEAM-17 | Forge `source=sso` in manual request | Rejected; provenance unchanged. |
| TEAM-18 | Incomplete external membership snapshot | No destructive empty-roster interpretation. |
| TEAM-19 | Active team gains a new eligible User | User receives current team grants without share-row fanout. |
| TEAM-20 | Team deleted | All team-derived access ends; shared resource rows remain. |
| TEAM-21 | Hard-delete account that still owns live shared resources | `409` with impact explanation; no unchecked resource cascade; account disablement remains available. |

### 19.3 Sharing, inheritance, and mutation acceptance matrix

| Test ID | Scenario | Expected result |
|---|---|---|
| SHARE-01 | Direct user Can use | Can list/read/run saved flow; cannot save/edit/reshare/delete. |
| SHARE-02 | Direct user Can edit | Can edit allowed graph/content; cannot publish/move/transfer/reshare another user's flow. |
| SHARE-03 | Team Can use / Can edit | Only active eligible members receive the corresponding grant. |
| SHARE-04 | Share with inactive/nonexistent recipient | Rejected before grant persistence. |
| SHARE-05 | Share with inactive/invalid team | Rejected; no ineffective success row. |
| SHARE-06 | Recipient search without resource-sharing authority | Rejected without directory enumeration. |
| SHARE-07 | Team Admin receives a non-editable resource | Team role does not elevate it to editable. |
| SHARE-08 | Editable recipient attempts own share creation | Denied; write is not share administration. |
| SHARE-09 | Share downgrade while recipient editor is open | New save rejected, controls update, local unsaved content preserved. |
| SHARE-10 | Delete grant with no alternate source | Resource disappears from lists; direct foreign read denied. |
| SHARE-11 | Delete/downgrade direct grant with writable team/project grant | Effective edit remains and UI names the surviving source. |
| SHARE-12 | Concurrent share-level updates with same revision | One change wins; stale operation receives `412`. |
| SHARE-13 | Duplicate share create | `409`; no implicit escalation/upsert. |
| SHARE-14 | Share-list pagination with many invisible rows | Correct visible page contents/count semantics; no post-page truncation artifact. |
| SHARE-15 | Existing or API-created targeted read/admin grant | Valid API values remain accepted under normal authorization; no silent rewrite; the new dialog still offers only Can use/Can edit. |
| SHARE-16 | User/team share create/delete on legacy-public flow | Public status unchanged; dialog does not claim exclusive/private access. |
| PROJ-01 | Non-editable project grant | Browse/read/run authorized children; no child creation or project/content edit. |
| PROJ-02 | Editable project grant | Create child flows and edit permitted project/flow content; no implicit delete/publication/reshare. |
| PROJ-03 | Add workflow after project was shared | Correct inherited access without new share rows. |
| PROJ-04 | Collaborator creates workflow in owner's project | Creator remains owner; project owner and authorized collaborators can see it. |
| PROJ-05 | Revoke creator's team membership | Creator retains owned-flow access but not unrelated project access. |
| PROJ-06 | Direct flow share under unreadable project | Flow is reachable; parent/siblings remain private. |
| PROJ-07 | Unauthorized explicit destination in create/move/import | Fails; no silent personal-default redirect. |
| PROJ-08 | Authorized owner moves own workflow | Destination rechecked; inherited access changes; direct grants remain. |
| PROJ-09 | Shared editor tries moving another user's workflow | Denied. |
| PROJ-10 | Project deletion includes collaborator-owned child without delete authority | No partial/cascade deletion; actionable rejection. |
| PROJ-11 | Paginated and unpaginated shared project reads | Same per-flow access decisions. |
| PROJ-12 | Read filters hidden flows | No ORM relationship mutation or accidental orphan deletion. |
| WRITE-01 | Two editors save same observed flow revision | One succeeds; stale graph cannot overwrite it. |
| WRITE-02 | Native collaboration caller omits required update precondition | `428` after normal identity/resource authorization; disabled-owner compatibility is covered separately. |
| WRITE-03 | Full-object echo of unchanged protected fields | Allowed where the actual operation is authorized; no accidental privilege increase. |
| WRITE-04 | Effective publication/authentication/owner-field change by editor | Rejected across PATCH, PUT, imports, and derived fields. |
| WRITE-05 | Save a redacted shared graph | Hidden retained secrets are neither leaked nor accidentally erased. |
| WRITE-06 | Bulk import includes forbidden overwrite | No claimed complete success or unauthorized partial mutation. |
| WRITE-07 | Owner and editor rename collisions | Enforced in original owner's namespace. |
| WRITE-08 | Stale autosave after `412` | No automatic overwrite retry with a refreshed revision. |

### 19.4 Runtime, audit, and compatibility acceptance matrix

| Test ID | Scenario | Expected result |
|---|---|---|
| RUN-01 | Non-owner executes shared flow | Graph/components use the recipient principal, not the owner. |
| RUN-02 | Owner dependency unavailable to recipient | Clear dependency failure; no owner-credential fallback. |
| RUN-03 | Can use caller supplies replacement graph/code/tweaks | Replacement does not execute; endpoint contract enforced. |
| RUN-04 | Can edit caller uses supported chat/V2 unsaved graph | Writer policy checked; actual caller identity retained. |
| RUN-05 | V1 non-owner client tweaks | Existing owner-only restriction retained. |
| RUN-06 | Share revoked before HITL resume | Resume rechecks and denies if no grant survives. |
| RUN-07 | Shared caller requests another user's historical job/stream/session | Separate ownership/privacy boundary remains effective. |
| RUN-08 | Team share used against legacy/project MCP or webhook admission | No unplanned transport widening. |
| RUN-09 | Existing public flow with real authorization enabled | Explicit public policy works, or fails closed on unsupported domain; targeted shares never supply public access. |
| RUN-10 | Same endpoint name under different owners | No arbitrary foreign-first match; UUID/qualified resolution or sanitized ambiguity. |
| AUDIT-01 | Team/share mutation succeeds | Canonical mutation audit event commits with it and identifies actor/target. |
| AUDIT-02 | Mutation audit persistence fails | Mutation rolls back; no durable unaudited success. |
| AUDIT-03 | Post-commit publication hook fails | Committed result is not falsely rolled back/reported as a duplicate-retry failure. |
| AUDIT-04 | Capability page render | Does not claim an action happened merely because its permission was checked. |
| AUDIT-05 | Remove grant on worker A, request resource on worker B | Fresh admission reflects committed canonical policy without waiting for cache TTL. |
| MIG-01 | SQLite/PostgreSQL migrations | Correct data types/checks/indexes and scalar backfills; rerun/repair behavior explicit. |
| MIG-02 | Invalid legacy teams | Explicit repair data required; no arbitrary admin promotion. |
| MIG-03 | Resource deletion plus stable-ID reimport | Old deleted-resource shares cannot silently revive. |
| REG-01 | Owner personal project/flow creation | Works without global broad roles. |
| REG-02 | Existing private owner operations and credential ceilings | Preserve intended behavior under enabled enforcement. |
| REG-03 | Out-of-scope guarded resource families | No blanket allow or accidental total denial introduced by activating the service. |
| REG-04 | UI account switch/logout | No previous user's resource permissions or open graph reused. |
| REG-05 | Enforcement-disabled owner operation omits If-Match | Established legitimate operation remains accepted through the same helper; supplied stale conditions still fail. |
| REG-06 | Default LFX stub or separately registered plugin | Existing interface/default behavior remains intact; native feature capabilities/preconditions are not falsely imposed. |
| REG-07 | Failed readiness or capability discovery | No error path treats configured enforcement as disabled or permits editing by default. |
| REG-08 | CI mode, tags, and directory selection | All eight authz journeys collected and executed; empty selection or wrong-mode reports cannot satisfy acceptance. |

### 19.5 End-to-end user journeys

Implement focused browser tests in proposed `src/frontend/tests/core/features/authz/authz-team-sharing.spec.ts` using isolated users and the actual backend:

1. Platform Admin creates a team with Admin, Maintainer, and User, then verifies role-specific management behavior with separate browser contexts.
2. Ordinary owner shares a workflow directly as Can use; recipient can run but cannot edit or use direct API saves.
3. Owner changes the same share to Can edit; recipient edits allowed graph content, and owner sees the saved change.
4. Owner shares a project with a team; existing and newly created workflows appear for members with the correct editability.
5. A member is removed or team suspended; new list/read/save/run requests are denied unless ownership/another grant remains.
6. Owner downgrades access while the recipient's editor is open; save is rejected and local unsaved content is retained.
7. Two editors save concurrently; stale content receives a conflict and is not silently retried.
8. A directly shared flow remains accessible without exposing its private parent or sibling workflows.

### 19.6 Existing Playwright harness and CI selection changes

The inspected `src/frontend/playwright.config.ts` sets `LANGFLOW_AUTO_LOGIN=true`; the main CI caller defaults to `tests/core`, and its reusable browser workflow also filters by supported tags. The new suite must therefore live at `src/frontend/tests/core/features/authz/authz-team-sharing.spec.ts` and be explicitly selected in a multi-user test invocation. [S40, CI06, CI09]

Use the **same** Playwright configuration with the test-only `LANGFLOW_E2E_AUTHZ` switch, supplied by a declared `authz-mode` workflow input. In enhanced mode:

- Select the authorization directory, with the existing `@api`, `@database`, `@workspace`, and `@release` tags plus an identifying `@authz` tag; do not invent an unsupported suite input.
- Start the actual production authorization service with `LANGFLOW_AUTO_LOGIN=false`, `LANGFLOW_AUTHZ_ENABLED=true`, and explicit test audit settings.
- Use an isolated disposable database/configuration and synthetic bootstrap credentials, never production credentials. Create and activate distinct users using authorized fixtures/API calls.
- Refuse reuse of an arbitrary already-running backend. Verify actual enforcer capabilities and distinct user identities before testing.
- Apply the same selection/configuration during collection, shard calculation, and execution. Require all eight journey IDs to be collected and executed, with no blanket skips or retry-to-green acceptance.
- Keep external model calls on the existing deterministic loopback fixture. Do not mock permission APIs, policy decisions, or the persistence operation the journey is meant to verify.
- Keep mode-specific reports, coverage, database paths, and logs separate to avoid collisions with the normal browser suite.

The normal regression invocation keeps its intended configuration and excludes only the authorization directory owned by the separate **mandatory** enhanced invocation. Add the enhanced invocation through the existing reusable browser workflow and include its result in `CI Success`, as specified in Sections 23.5–23.6. A test that is never selected is not a passing test.

This changes test configuration and CI wiring only. It does not introduce a parallel production service, rollout mode, or deployment test step.

### 19.7 Test organization and commands

Extend existing policy/route tests where they cover the changed boundary. Proposed new test files, when equivalent suites do not exist:

- `src/backend/tests/unit/services/authorization/test_team_share_policy.py`
- `src/backend/tests/unit/services/authorization/test_team_lifecycle.py`
- `src/backend/tests/unit/api/v1/test_team_roles_api.py`
- `src/backend/tests/unit/api/v1/test_targeted_share_api.py`
- `src/backend/tests/unit/api/v1/test_shared_project_inheritance.py`
- `src/backend/tests/unit/api/v1/test_shared_resource_concurrency.py`
- `src/backend/tests/unit/api/v1/test_authz_recipients.py`
- `src/backend/tests/integration/test_team_sharing_transactions.py`
- Colocated frontend unit tests for team management, sharing dialog, and permission/revision behavior.
- `src/frontend/tests/core/features/authz/authz-team-sharing.spec.ts`

Illustrative future verification commands, after the tests/configuration are implemented:

```bash
uv sync --group dev --package langflow-base
uv run pytest src/backend/tests/unit/services/authorization/
uv run pytest src/backend/tests/unit/api/v1/test_team_roles_api.py \
  src/backend/tests/unit/api/v1/test_targeted_share_api.py \
  src/backend/tests/unit/api/v1/test_shared_project_inheritance.py \
  src/backend/tests/unit/api/v1/test_shared_resource_concurrency.py \
  src/backend/tests/unit/api/v1/test_authz_recipients.py
uv run pytest src/backend/tests/integration/test_team_sharing_transactions.py
uv run python scripts/ci/check_authz_endpoint_matrix.py
uv run python scripts/ci/check_execution_principal_matrix.py
uv run pytest scripts/ci/ -v
cd src/frontend
LANGFLOW_E2E_AUTHZ=true npx playwright test tests/core/features/authz --grep '@authz' --project=chromium --list
LANGFLOW_E2E_AUTHZ=true npx playwright test tests/core/features/authz --grep '@authz' --project=chromium --retries=0
```

The exact route-matrix checker was verified as `scripts/ci/check_authz_endpoint_matrix.py`; run it together with the execution-principal checker and the corresponding script tests. Also run all applicable baseline jobs, quality checks, package checks, and database tests specified in Section 23. PostgreSQL tests need an explicitly configured disposable database; report a missing environment as **NOT RUN / BLOCKED EXTERNAL**, not success. In a CI job promising PostgreSQL coverage, an unreachable configured service must fail the job rather than cause its tests to skip; backend environment selection and the actual executed engine must be recorded. [CI08–CI20]

Record exact commands, service configuration, database engines, passing/failing counts, and unexecuted external boundaries in verification documentation. Do not add these commands to startup or deployment.

---

## 20. Implementation work packages

The packages below are execution order for one integrated implementation. They are not deployable parallel versions or a requirement to ship incomplete behavior.

| Package | Required work | Completion evidence |
|---|---|---|
| WP-01 — Baseline and contracts | Pin `yazeedhasan97/langflow:main` and the implementation branch; retain the recorded upstream source baseline; inspect fork contribution/nested-agent instructions, rulesets, workflows, actual service/admin route, and execution prerequisites; reconcile drift; add failing policy/API tests and the intentional contract-change ledger. Recheck an upstream PR target only when upstream submission is requested. | Fork-scoped source/CI inventory, correct base repository/branch, runner-readiness and baseline execution status, agreed matrices, no undocumented privilege assumptions. |
| WP-02 — Schema and data | Add model fields/migrations, revision types, repair commands, and legacy-data policy. | SQLite/PostgreSQL migration checks; explicit invalid-team treatment; no copied grants/resources. |
| WP-03 — Native enforcement | Implement the existing service, canonical loaders/evaluator, intrinsic creation, scope/visibility/effective-permission parity, and public compatibility boundary. | Tests use real service and show allow/deny—not only guard wiring. |
| WP-04 — Teams lifecycle | Extend team/member APIs, role checks, atomic roster changes, user/source cleanup, and mutation auditing. | Non-empty/active-admin tests, concurrent removal tests, correct account-disable behavior. |
| WP-05 — Sharing contracts | Strengthen share routes, add recipient search/capabilities/summary, revision checks, validation, and pre-pagination filtering. | Ordinary-owner sharing, recipient validation, no resharing escalation, overlap explanations. |
| WP-06 — Resources/runtime | Reconcile project child visibility, flow destinations/field restrictions, imports/exports/deletes, optimistic writes, and relevant execution families. | Inheritance/creator ownership tests, stale-write tests, caller-principal tests, updated matrices. |
| WP-07 — UI integration | Implement one Teams management component family and one sharing dialog through current menu hooks; wire capability/revision handling and shared discovery. | Browser journeys pass with distinct users and enforcement enabled. |
| WP-08 — Verification/docs | Run feature tests and all applicable upstream regression/quality/package/migration checks; fix attributable failures; document actual implementation and intended API changes. | Requirements-to-tests evidence, accurate results/blockers, and operator/user documentation. |

Do not declare WP-07 complete because the dialog can create rows while WP-03 enforcement or WP-06 visibility is missing. The feature is complete only as a connected behavior. Section 23.12 adds WP-09 (upstream/CI reconciliation) and WP-10 (final integration verification). Start CI reconciliation with WP-01, implement the job wiring alongside feature tests, and finish final-SHA validation after the integrated code is complete; package numbers are not a reason to postpone CI compatibility until the end.

---

## 21. Documentation and operational updates

Update the existing documentation with the final implemented state, not only a roadmap promise:

| Document/location | Required content |
|---|---|
| `AGENTS.md` | Enhanced distribution's enabled-enforcement implementation, single-source architecture, team roles, two dialog modes versus preserved API values, conditional-write capability, and CI selection. Retain default-off/interface distinctions and contribution instructions; do not rewrite standards to excuse a failing check. |
| `docs/docs/Develop/authorization.mdx` | Native/enhanced enforcement setup, exact team and resource permissions, inheritance, overlapping grants, revocation boundary, capabilities, recipient lookup, and API status/preconditions. |
| `docs/docs/Develop/authentication-overview.mdx` | Authentication remains separate; distinct-user mode and authorization configuration required for collaboration. |
| `docs/docs/Develop/external-authentication.mdx` | No automatic team-admin elevation; source-managed membership and ceiling behavior; distinguish verified integration from untested provider behavior. |
| Existing project/workflow user documentation | Share button placement, two modes, inherited access, retained creator ownership, inability to reshare/delete as editor, and dependency access explanation. |
| `.env.example` and actual deployment documentation | Real service enabled, auto-login disabled, audit behavior, bootstrap/HTTPS requirements, no startup tests. |
| `scripts/ci/authz_endpoint_matrix.json` | New/changed team/share/capability/recipient endpoints, precise domains, privacy, side-effect ordering, and references to actual tests. |
| `scripts/ci/execution_principal_matrix.json` | Preserve family exceptions and update any actual affected behavior/test references. |
| Generated API documentation/OpenAPI process | Publish new schemas/routes and conditional-write semantics; note that some existing authentication routes remain excluded from OpenAPI. |
| New verification note in the project's established documentation location | Exact touched files, migration IDs, commands/results, candidate/base/merge SHAs, workflow/job/attempt URLs, collected/executed/skipped/flaky counts, database/architecture coverage, contract-change ledger, and separately classified external blockers/upstream acceptance. |

Correct the known documentation mismatches discovered in the review where these sections are touched: the seeded viewer role includes flow execution, and supported chat/V2 writer overrides are not universally owner-only. Document source-specific behavior rather than replacing one inaccurate blanket claim with another. [S01, S24, S29, S36]

Do not edit historical versioned documentation to claim an old release contained the new feature. Apply the repository's normal versioning process when the enhanced distribution is released.

Operator instructions must explain:

- How to identify the actual registered enforcer and whether sharing is ready.
- How to repair legacy empty/adminless teams without arbitrary promotion.
- Why removing one grant can leave effective access through another source.
- Why creator ownership survives a team removal.
- Why sharing a workflow does not supply missing owner credentials/dependencies.
- Why new-request revocation does not cancel already-admitted executions.
- How to resolve stale-save conflicts without overwriting another person's work.
- How to handle inactive/retired teams and restore an installation from a known backup if needed.

---

## 22. Definition of done and implementation constraints

### 22.1 Functional completion

The implementation is complete only when all required outcomes are demonstrated:

- [ ] Platform Admin can create/manage teams from the Teams tab.
- [ ] Team creation requires initial members and a valid active Admin in one operation.
- [ ] Admin/Maintainer/User roles are scoped per membership and enforced server-side.
- [ ] Manual last-member/last-admin operations are protected under concurrency.
- [ ] Account/source revocation can proceed safely without keeping a compromised user active.
- [ ] Ordinary owners can share flows/projects with specific existing users/teams.
- [ ] Can use and Can edit are persisted per grant through the existing share model.
- [ ] The owner can change or remove a grant through the same dialog/API.
- [ ] Team management does not imply workflow editing; resource editing does not imply sharing authority.
- [ ] Project inheritance covers current/future children without grant fanout.
- [ ] Collaborator-created flows remain creator-owned and visible according to the explicit project policy.
- [ ] Individual flow sharing does not expose private parents/siblings.
- [ ] Lists, direct URLs, save APIs, run APIs, and permission discovery agree.
- [ ] Publication, authentication settings, ownership-bound fields, moves, and deletes remain separately controlled.
- [ ] Overlapping grants and retained ownership are visible in access explanations.
- [ ] Newly admitted requests reflect committed revocation across workers.
- [ ] Stale editing/permission-management requests cannot silently overwrite newer changes.
- [ ] Shared execution preserves actor identity and dependency restrictions.
- [ ] Existing explicit public behavior and owner-scoped transport exceptions are not accidentally widened.
- [ ] Team/share mutation audit records are durable with their canonical changes.
- [ ] Existing guarded non-target resource families remain operational under the actual enforcer.
- [ ] The browser tests use distinct accounts and the production authorization service, not auto-login-superuser behavior.
- [ ] All affected documentation and verification evidence match what was actually implemented.
- [ ] All applicable inherited upstream CI/regression requirements and fork delivery requirements in Section 23 are satisfied with actual fork final-candidate evidence; required feature tests are not omitted/skipped. Upstream-only submission rules apply only to an actual requested upstream PR.
- [ ] Intentional changes to original tests/API contracts are documented and retain substantive positive/negative coverage.
- [ ] Any upstream submission targets the verified active release candidate and satisfies its actual required checks/reviews/queue; fork test success is not misreported as upstream acceptance.

### 22.2 Engineering constraints

- Extend existing models/services/routes and use the established monorepo boundaries.
- Keep one canonical authorization implementation active per deployment.
- Preserve the authentication/authorization separation and existing credential ceilings.
- Use typed schemas, explicit action maps, clean error contracts, and shared domain logic rather than route-specific duplicated permission code.
- Use test-driven/behavior-driven corrections focused on materially affected behavior.
- Do not add tests to deployment/startup.
- Do not invent source behavior, claim an external plugin was tested when it was not, or interpret a structural matrix pass as end-to-end security verification.
- Do not introduce application approvals, authority workflows, canary/shadow paths, replacement API versions, or alternative persistent models. Preserve the repository's existing human review/status-check/merge-queue requirements; do not bypass them.
- Do not copy another user's workflow or credentials as a substitute for authorization.
- Do not introduce arbitrary team-role/permission promotions to get failing tests to pass.
- Fix regressions and stale code attributable to these changes before declaring completion.

### 22.3 Evidence and limits

This document specifies the agreed feature and the explicit design choices above, now including the upstream CI/contribution requirements in Section 23. It is not a patch, a runtime verification report, a guarantee that future checks pass, a claim of upstream acceptance, or a claim of sandbox isolation. All application/test execution remains pending.

The actual implementation must reconcile any drift from the pinned commit and record the final exact file paths/migration identifiers. Conditional environment facts—such as a separately installed Enterprise enforcer or existing customized admin layout—must be inspected rather than assumed. That inspection must not be used to introduce duplicate implementations.


---

## 23. Fork delivery, upstream compatibility, and CI acceptance

### 23.1 What this revision adds, and what it does not claim

The original plan specified feature acceptance tests, production-enforcer testing, PostgreSQL/SQLite coverage, and selected quality checks. It did **not** map the complete upstream PR workflow, required status-check names, contribution target, fork runner constraints, or test-discovery rules. This section supplies that integration contract alongside Sections 1–22. Fork CI/test acceptance is mandatory; upstream-only submission requirements are conditional and do not turn optional upstream contribution into a fork release dependency.

This is a **plan update only**. No application changes, PR, merge, migration, GitHub Actions execution, or Langflow runtime tests have been performed by this revision. Section 23.13 separately identifies the limited local environment diagnostics that were actually run. Every implementation/test acceptance item remains **NOT IMPLEMENTED / NOT RUN** until supported by evidence from the final code. Reading workflow YAML establishes requirements, not that those requirements pass.

Keep three outcomes distinct:

1. **Fork implementation readiness:** the agreed feature works in `yazeedhasan97/langflow` and passes its applicable CI and this plan's feature acceptance tests.
2. **Upstream integration compatibility:** the patch is reconciled against the explicitly selected upstream branch, preserves unaffected contracts, and passes the relevant workflow definitions on the actual candidate tree.
3. **Upstream merge acceptance:** maintainers accept the product/API changes and GitHub's effective review/check/queue rules permit the PR. A green fork run cannot establish this outcome.

The native enforcer, required initial team membership, team-role administration, strict mutation preconditions, and non-empty-team rules deliberately change upstream behavior. Do not claim that every existing assertion can remain byte-for-byte unchanged, that the feature is an upstream-approved OSS product decision, or that a planning document guarantees a future green CI run. Do not remove agreed functionality merely to avoid those compatibility decisions. [S01–S03, CI01, CI02]

### 23.2 Repositories, branch targets, and recorded baseline

| Item | Verified planning baseline / required treatment |
|---|---|
| Implementation repository | `yazeedhasan97/langflow`, repository ID `1353667234`, public and not archived. This is the sole code/plan/CI write destination. |
| Implementation URL | `https://github.com/yazeedhasan97/langflow` |
| Git origin | `https://github.com/yazeedhasan97/langflow.git` |
| Fork base | `main`, rechecked at `9e978f50a3700d079df62ecb2bd5909421093587`; tree `afc339fd9d5450327580f535f8ba557a0682321a`. Recheck again before the first code change. |
| Feature delivery | Proposed branch `feat/auth-team-sharing` in the fork, PR base `yazeedhasan97/langflow:main`. No branch or PR exists as a result of this plan update. |
| Upstream reference | `langflow-ai/langflow`; fetch-only source/standards reference. Keep the earlier reviewed main SHA as historical evidence, not a claim that upstream never changes. |
| Upstream contribution policy | The inherited `CONTRIBUTING.md` directs upstream PRs to the active `release-X.Y.Z` candidate, not upstream `main`. This does not replace the explicitly selected fork-main delivery target. |
| Earlier upstream candidate observation | Revision 1.1 inspected `release-1.12.0` at `c379987876964818d7cc09994fbfd165f7546cc4`. This is historical evidence only; reconfirm the appropriate base if an upstream submission is requested. |
| Fork protection observation | The rechecked branch response reports `protected=false`; the readable repository-ruleset query including parents returned `[]`. This is a dated observation, not permission to bypass validation or assume all account/organization settings are known. |
| Fork CI observation | The repository workflow-run query returned `total_count=0`. It proves no runs were returned, not that Actions is disabled, enabled, or usable with a particular runner. |
| Source links | Retain commit-pinned upstream evidence for provenance. For the same baseline, the corresponding implementation source is `https://github.com/yazeedhasan97/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/<repository-relative-path>`. |

Sources: [CI01, CI03, CI04, FORK01–FORK04]. Record `IMPLEMENTATION_REPOSITORY=yazeedhasan97/langflow`, `DELIVERY_BASE_REF=main`, `FORK_BASE_SHA`, `IMPLEMENTATION_HEAD_SHA`, and, when present, `PR_TEST_MERGE_SHA` / `MERGE_GROUP_SHA`. Record `UPSTREAM_REVIEW_BASE_SHA` as source provenance. Record a separate `UPSTREAM_SUBMISSION_BASE_SHA` only when a real upstream submission is in scope. Treat all branch heads as mutable.

Before implementation, perform read-only inventory of the fork's root `AGENTS.md`, applicable nested `AGENTS.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, actual PR template if present, relevant `.agents` guidance, package instructions, workflows/local actions, and path-filter configuration. Follow the most specific applicable rules and document the fork-main delivery exception explicitly. Do not invent missing instruction files. [CI01, CI05]

When incorporating upstream updates, fetch into the fork working copy and reconcile canonical files there. Do not use a blanket “ours” strategy, drop upstream security fixes, regenerate IDs to bypass a conflict, or leave duplicate authorization implementations. After a base change, resolve migration ancestry against the actual Alembic head, revalidate schemas/lockfiles/route matrices, and rerun affected tests on the combined fork candidate. A clean text merge is not proof of semantic compatibility. Do not automatically merge an upstream release branch merely to implement this plan.

### 23.3 Actual upstream required checks and merge rules

**Scope:** these observations govern an optional upstream submission. Preserve inherited check producers and applicable test content when implementing the fork, but do not assume upstream rulesets are installed in `yazeedhasan97/langflow`, add new fork approval requirements, or delay fork completion for an upstream review that was never requested. Fork protection/settings changes require separate authorization. [FORK03]

The public ruleset responses for **Merge Rule** (`986381`) and **Protect main** (`13786507`) reported active required status checks named exactly:

- `CI Success`
- `Validate PR`

Both responses associate these checks with GitHub Actions integration ID `15368` and specify one approving review plus merge-queue rules. The rulesets overlap and contain different queue/merge settings. Do not derive a single effective queue algorithm from only one response, or copy main-specific rules onto a release branch. Inspect the actual target's effective rules and PR merge box immediately before delivery. The public rulesets were readable. Legacy protection fields in a branch response do not describe every ruleset restriction, and an empty legacy check list is not evidence that the branch has no required checks. [CI02]

Required behavior:

- Preserve existing status-check names and producers. Do not replace `CI Success` with an unrelated always-green workflow or forge statuses under its name.
- Use a complete semantic PR title, for example `feat(authz): add team roles and editable project sharing`. Explain breaking API changes in the description and use the target repository's breaking-change convention when applicable.
- `Validate PR` is produced by `.github/workflows/conventional-labels.yml`; it runs on `pull_request_target` and `merge_group`. Keep it metadata-only. Never add checkout/execution of untrusted PR code to that privileged event.
- `.github/workflows/ci.yml` handles `pull_request`, `merge_group`, reusable calls, and dispatch. Preserve the PR lifecycle trigger that covers `ready_for_review`.
- Run the applicable checks on the final code and integration tree. Do not count a prior successful head after subsequent code, workflow, dependency, or base-branch changes.
- If a merge queue is used, retain `merge_group` coverage and validate the queue candidate. PR-head success alone is not queue success.
- Existing repository reviews and status checks are external contribution requirements, **not new runtime approval/authority features**. Do not disable/bypass them to satisfy the plan's prohibition on application approval workflows.
- Do not merge, force-push, rewrite shared branches, alter upstream rulesets, or publish releases merely because this plan was updated. Implementation and delivery actions remain separate from this document revision.

Sources: [CI02, CI06, CI07, CI21]. The fork's protection configuration is independent; inspect it rather than assume upstream protection was inherited.

### 23.4 Required CI inventory and acceptance mapping

The following workflows were inspected at the shared pinned source baseline. Run their applicable fork copies against the exact `yazeedhasan97/langflow` candidate; repeat the inventory when the fork base or an explicitly requested upstream target differs. A workflow's existence, its being selected, and its being a GitHub-required status check are separate facts.

| Workflow / entry point | Observed responsibility | Required implementation acceptance |
|---|---|---|
| `.github/workflows/ci.yml` | PR/queue orchestrator, path filters, draft/fast-track conditions, nightly-publication check, backend/frontend/docs/templates/Docker jobs, coverage merge, `CI Success`. | Preserve applicable jobs; add the feature verification jobs to its dependency/reporting logic; require their actual success when selected. Do not equate aggregate green with proof every needed test ran. |
| `.github/workflows/conventional-labels.yml` | Semantic PR validation and labeling; produces `Validate PR`. | Complete semantic title and safe metadata-only operation; retain queue trigger. |
| `.github/workflows/python_test.yml` | Backend unit suite in five groups, integration tests without live API keys, LFX suite, bundle-installed tests, and CLI/package checks. | Retain all applicable groups and test families. PR CI currently supplies Python `3.10` and `3.14`; the reusable workflow also supports `3.11`–`3.13`. Match actual caller inputs. |
| `.github/workflows/jest_test.yml` | `make test_frontend_ci`, JUnit results and coverage. | New/changed UI and pure permission tests are discovered; actual tests pass; preserve JUnit/coverage artifacts and test-count validation. Make write-only reporting fork-safe without hiding Jest failure. |
| `.github/workflows/typescript_test.yml` | Node 22 / Python 3.13, Playwright 1.60.0, tag-based suite selection, shards, blob-report completeness/merge checks, optional live smokes. | Preserve existing suites and reports; run the new multi-user suite explicitly using the real enforcer; match collection and execution configuration. |
| `.github/workflows/lint-js.yml` | Changed-file Biome checks; the orchestrator intentionally excludes this job from `CI Success` dependencies. | Still fix introduced frontend lint errors. Informational status is not permission to introduce them. Do not incorrectly document it as an upstream required status check. |
| `.github/workflows/lint-py.yml` | Reusable/dispatched Mypy suite over supported Python versions; not directly called by the inspected main CI orchestrator. | Run the relevant typing checks explicitly for changed Python/shared contracts; record whether they came from a workflow or direct command. |
| `.pre-commit-config.yaml` | Ruff, formatting, secrets scan, line/case checks, migration phase/pattern checks, Biome and touched-path policy scripts. | Run all applicable hooks; fix introduced errors; do not disable hooks or blanket-expand ignores. |
| `.github/workflows/migration-validation.yml` | PostgreSQL 16 model/migration consistency, migration-pattern validation, and real PostgreSQL/Redis background execution regression tests. | Require changed schema/migration checks to pass and preserve other jobs selected by the change. Add focused authorization transaction coverage without replacing migration checks with mocks. |
| `.github/workflows/db-migration-validation.yml` | Separate stable-to-nightly release migration workflow using published/installable artifacts. | Do not call a published upstream image a test of the fork patch. Add candidate-built upgrade evidence where needed; only run release-oriented paths safely with candidate artifacts. This is not a blanket mandatory PR-triggered job in the inspected baseline. |
| `.github/workflows/ci-scripts-test.yml` | `python -m pytest scripts/ci/ -v`, including repository automation/contract validation tests. | Update touched endpoint/principal matrices and their real test references; run the script suite and exact checkers. |
| `.github/workflows/docs_test.yml` | Docusaurus build and existing IBM Equal Access light/dark documentation checks. | Docs changes pass the selected build/accessibility jobs. “Minimize UI/theme testing” does not waive pre-existing applicable CI checks. |
| `.github/workflows/a11y-unit-tests.yml` | Frontend changes select the existing `jest-axe` job using `make test_frontend_a11y_unit_ci`. | Preserve component accessibility regression locks and verify the new menu/dialog/team controls, labels, focus, and disabled states. [CI23] |
| `.github/workflows/docker_test.yml` and `scripts/ci/test_docker_images.sh` | Build/test the full, base, backend, and frontend images; verify package versions, provider-free base contents and health. Uses an upstream-specific ARM64 runner. | Build the candidate sources on an available suitable runner, preserving assertions. A skipped/queued job or released upstream image is not candidate container validation. |
| Other workflows selected by the actual diff or rules | The directory also contains cross-bundle, extension-migration, security, accessibility, release-inventory, and cross-platform workflows. | Inventory their exact triggers at implementation time; execute every applicable non-publishing check and record applicability. Do not assert all are required or all passed from their filenames alone. Never run publishing/deployment workflows as a substitute for tests. |

Sources: [CI06–CI17, CI20]. Keep inherited upstream test selection and add only missing feature coverage. During development, focused tests are appropriate; before fork completion, the whole applicable inherited workflow set must run against the fork candidate. Do not replace the broad regression jobs with only the new authorization suite.

### 23.5 Exact browser-test discovery and isolation changes

**Corrected canonical new spec path:**

`src/frontend/tests/core/features/authz/authz-team-sharing.spec.ts`

Use the existing `src/frontend/playwright.config.ts`. Do not add another production app, an independent permission implementation, or a permanently deployed test stack.

Why this correction is necessary: the main CI workflow's default `frontend-tests-folder` is `tests/core`, while the original plan proposed `tests/authz-team-sharing.spec.ts`. The reusable browser workflow also applies tag-based `--grep`; moving a file alone does not guarantee collection. [CI06, CI09]

Implement this exact selection contract:

1. Mark the feature journeys with the existing applicable `@api`, `@database`, `@workspace`, and `@release` tags. Add `@authz` only as an identifying tag, not as a new unsupported suite value.
2. Add the typed boolean `authz-mode`, default `false`, to **both** `workflow_call` and `workflow_dispatch` inputs of `.github/workflows/typescript_test.yml`.
3. Derive `LANGFLOW_E2E_AUTHZ` from that input at workflow/job scope so it has the same value during `--list`, shard calculation, execution, report validation, and fixture setup. Do not set it only on the execution step.
4. In `playwright.config.ts`, use `LANGFLOW_E2E_AUTHZ=true` to select only the new authorization directory and configure `AUTO_LOGIN=false`, `AUTHZ_ENABLED=true`, the production enforcer, explicit test audit settings, and an isolated disposable database. In normal mode, exclude the authorization directory **because the separate mandatory authz invocation owns it**, while preserving the original suite's other paths. Do not mark the new suite `test.skip()` to avoid auto-login failures.
5. Add a CI job `test-authz-e2e`, display name `Run Team Sharing E2E`, which calls the **same** `typescript_test.yml` with `authz-mode: true`, `tests_folder: tests/core/features/authz`, explicit supported suites `["api", "database", "workspace"]`, and the exact candidate ref. Keep the existing frontend job in normal mode.
6. Use independent browser contexts and users. Assert that the logged-in identities differ and that the backend capability response identifies the actual production enforcer before starting the journeys.
7. Refuse reuse of an arbitrary backend in authz mode. Allocate isolated database/config/log paths and owned processes; teardown only those resources. Use the existing loopback model fixture where a model is required. Never mock permission endpoints or use a test-only allow/deny service for E2E.
8. Discovery must list all eight journey IDs before tests run. Execution must report every planned journey as executed. A zero-test match, skipped feature suite, missing shard artifact, setup failure, or test omission is a verification failure.
9. Use zero retries for the new authorization acceptance invocation so race/permission defects are not hidden by retries. Preserve the upstream regression suite's existing retry behavior separately, and record retries/flakes rather than reporting them as clean first-attempt results.
10. Retain the reusable workflow's complete blob-report collection and JSON/HTML report validation. Prefix/isolate feature artifacts by suite/mode as well as OS, shard, and attempt. Normal and authz invocations in the same run must not overwrite each other's blob reports, JSON reports, HTML reports, coverage, or server logs, and the normal coverage merger must not silently combine incompatible directories.
11. Extend `npm run test:e2e-utilities` coverage for the mode/collection contract and any changed persistence/error helpers. Keep its existing provider-isolation and full-flow-autosave policies passing. Do not make a direct test-fixture PATCH masquerade as evidence that the real UI autosave persisted a graph.

These are two test configurations for the **same application**, not parallel production architectures. Core regression tests retain their intended fixture settings; the new authorization suite proves multi-user behavior under enhanced settings.

### 23.6 Exact CI changes needed in the fork

The following changes are implementation instructions for **the copies in `yazeedhasan97/langflow`**, not changes made by this document update. Keep reusable calls local (`./.github/workflows/...`) where they already are; do not replace them with `langflow-ai/langflow@main`. Checkouts must resolve the fork candidate repository and SHA. Do not add upstream-owned runner access, registry publishing, or deployment as prerequisites for the code-test jobs.

| File | Planned change |
|---|---|
| `.github/changes-filter.yaml` | Add a dedicated `authz-sharing` filter covering Langflow auth/authz services, team/share/permission/user/API-key/project/flow routes and schemas, resource models/migrations, relevant execution helpers, LFX auth/authz/settings contracts, frontend team/share/editor/permission/menu/store/hooks, their tests, `.env.example`, package/lock files, Makefile, browser config, and the CI files controlling these checks. Keep all current Python/frontend/database/API/Docker/docs categories intact. |
| `.github/workflows/ci.yml` | Expose the new path-filter output; add `test-authz-e2e` and `test-authz-backend` dependencies to `CI Success`; enforce success rather than skipped when these jobs are required. Trigger both on relevant changes and final full-validation requests. Preserve existing check names/triggers. |
| `.github/workflows/ci.yml` | Declare `run-all-tests` and `frontend-tests-folder` under dispatch as well as reusable-call inputs if the implementation needs to dispatch them; the inspected dispatch schema does not expose those two inputs. Make final validation include the existing Docker job, whose inspected condition does not currently honor `run-all-tests`. Do not describe a dispatch input as usable until it exists. |
| `.github/workflows/ci.yml` | For `merge_group`, resolve the changed base/head from the event or conservatively run all impacted categories; for manual runs use a trusted explicit base or `run-all-tests=true`. A failed/no-decision filter must fail required aggregate validation, not skip it green. |
| `.github/workflows/ci.yml` | Add `test-authz-backend`, display name `Run Team Sharing Backend Tests`, covering the production enforcer, real SQLite and PostgreSQL 16 transactions, migrations, lifecycle and concurrent changes. Test Python 3.10 and 3.14 for changed shared/runtime code. Reuse existing environment setup and repository test commands; do not duplicate the policy engine. |
| `.github/workflows/typescript_test.yml` | Add the `authz-mode` contract in Section 23.5, consistent discovery/execution state, feature no-retry setting, and collision-free artifacts. Keep existing suite validation and report completeness checks. |
| `src/frontend/playwright.config.ts` | Implement the same-file mode split, isolated multi-user fixtures, deterministic provider setup, and owned process cleanup; do not leak authz-mode variables into legacy core tests. |
| `src/frontend/tests/core/features/authz/authz-team-sharing.spec.ts` | Implement the eight connected user journeys and accepted tags. This path replaces the previously proposed root-level spec path everywhere in the plan. |
| `.github/workflows/jest_test.yml` | Keep Jest execution and local JUnit/result validation blocking. Restrict PR comments/check-publishing steps to events/tokens that may perform them; for read-only fork events retain local report validation and upload artifacts. Do not turn an authorization error in a reporter into false evidence of test failure or swallow actual failed tests. |
| `.github/workflows/python_test.yml` | Audit the reusable secret contract. Since the new required suites are credential-free and the existing no-key integration path is available, make genuinely unused live-provider secret inputs optional for those paths. Keep existing live tests correctly classified; do not invent credentials, remove assertions, or change unrelated selection policy. |
| `.github/workflows/docker_test.yml` | Add typed `ref` and `runs-on` inputs to reusable/dispatch paths, thread the exact candidate ref through each checkout, and parameterize the runner instead of requiring upstream's private label in a fork. Preserve both attempts and the actual image checks. |
| `.github/workflows/ci.yml` → Docker caller | Select an available fork-authorized ARM64 runner for `yazeedhasan97/langflow`; never unconditionally depend on upstream's private runner label. Preserve upstream runner behavior only in any future separately reviewed upstream contribution. `ubuntu-24.04-arm` is a documented hosted option for public repositories, but its smaller disk/resource envelope must be tested against the actual image build. Resource exhaustion requires an adequate runner, not silently dropping images or accepting an x64-only result as ARM64 proof. |
| `scripts/ci/test_docker_images.sh` | Preserve actual candidate-source image builds and version/base-content checks. Run only on a disposable runner: its existing cleanup prunes container resources broadly. Never execute it on a production Docker host or a shared developer host with unrelated containers. Any disk accommodation must preserve all assertions and image targets. |
| `.github/workflows/migration-validation.yml` | Keep model/pattern/real-service tests. Replace hard-coded diff-base assumptions where necessary with the actual PR/queue/dispatch base so a release-branch PR validates the right migrations. Make comments fork-safe. Include focused authz tests against the real service or call their existing shared test command. |
| `.github/workflows/ci-scripts-test.yml` | Extend touched-path coverage to all new authorization routes/contracts and CI selection logic where needed. Keep `python -m pytest scripts/ci/ -v`. |
| `scripts/ci/authz_endpoint_matrix.json`, `scripts/ci/execution_principal_matrix.json` and their checkers/tests | Add the new route families and concrete test references. Add new action/persona vocabulary only when the implementation truly introduces it; extend validator tests rather than disabling unknown-action/missing-route detection. |
| `.github/workflows/lint-js.yml`, `docs_test.yml`, and other called workflows lacking an explicit reusable `ref` | Thread a candidate ref through their declared inputs/checkouts if used to validate a dispatched candidate. Preserve their existing event-default behavior and inspect Docker/local composite actions too. Every claimed candidate check must operate on that candidate, not silently fall back to default-branch code. |
| `src/frontend/package.json` / existing test utility scripts | Use the locked toolchain and add only necessary CI commands/utility tests. The current `type-check` script starts Vite after `tsc`; use a terminating compiler invocation for CI or add a clearly named non-serving script. Do not let a type-check job hang on a dev server. |
| `AGENTS.md`, test/CI documentation, verification report | Document the changed fork behavior, exact suite selection, actual invocation, rule/check mapping, intentional test-contract changes, and retained upstream limitations. |

Sources: [CI06–CI20, CI22]. The extra database services and runner jobs are disposable **test infrastructure**, not deployment/staging/canary infrastructure. Do not insert tests into application startup, Docker entrypoints, migrations, or deployment commands.

### 23.7 Preserve regression coverage while reconciling intended changes

Create a test-contract change ledger before changing expectations. Each entry must contain: original test/file, original behavior, linked requirement/design section, intended new behavior, minimal fixture/assertion change, and retained negative/regression coverage.

Required reconciliation areas:

| Existing assumption | Required reconciliation |
|---|---|
| OSS authorization calls always allow | Preserve/test disabled-mode behavior where still supported; add enabled-mode production-enforcer tests. Do not keep enabled-mode allow-all behavior just to satisfy an old stub expectation. Keep isolated LFX/default-interface tests testing their actual package contract. |
| Team creation has no initial roster | Update team route/schema success fixtures to supply valid initial members/admin. Add rejection cases for empty/adminless teams and retain duplicate/source/authorization coverage. ORM construction used to set up an intentionally invalid migration case is not a public team-create success test. |
| All team mutation routes are superuser-only | Extend role-specific success and denial cases without removing cross-team or privilege-escalation assertions. Preserve platform-only creation/deletion. |
| Existing share/flow/project mutations have no revision header | Update enabled-native-contract success fixtures, UI hooks, CLI/API clients under repository control, and direct-API browser fixtures to use the observed revision. Preserve legitimate enforcement-disabled owner acceptance in the same helper; explicit stale conditions still fail. Retain native-enabled `428`/`412` negative tests, no automatic stale retry, and no superuser bypass. |
| New dialog has two choices but the existing API has four values | Preserve low-level `read`/`execute`/`write`/`admin` acceptance with current resource restrictions and full authorization. Test that two UI choices do not silently translate read-only grants into executable grants. |
| Shared UI extension hooks return `null` | Replace obsolete null-render assertions for the enhanced fork with enabled/disabled/unauthorized capability cases. Retain no-render behavior when sharing is unsupported; test that errors/loading do not enable edits. |
| Main browser harness auto-logs in a superuser | Keep the normal regression harness explicitly configured; use separate distinct-user authz mode on the same application/config. Never count superuser-only UI success as recipient permission verification. |
| Project visibility is owner-filtered | Preserve personal-owner behavior and add collaborator-created child, direct-only child, inheritance, and pagination cases. Never alter an ORM relationship during a read merely to filter response contents. |
| Factories/plugins expect existing interfaces | Keep existing signatures compatible, default new capabilities safely, cover import/registration and lifecycle-adapter tests, and maintain `langflow → langflow-core → langflow-base → lfx` dependency direction. |
| Published examples/import fixtures omit new read-only fields | Add server-generated revisions without requiring them on brand-new resource creation. Require observed revisions only where the defined mutation contract needs them. Update exported schemas/examples consciously; do not rewrite historical release documentation. |

Run unchanged baseline suites at the pinned base when possible, then the corresponding suites at the candidate. Baseline defects, unavailable external infrastructure, and feature regressions need separate classifications. A baseline defect is not automatically excused: record it, show reproducer/log evidence, and do not claim the relevant check passed. Fix implementation-attributable regressions and closely related compatibility defects before completion.

Forbidden shortcuts: reducing coverage thresholds, broadening test excludes, adding blanket `skip`/`xfail`, suppressing import failures, bypassing selectors, granting every user an admin role, using a mocked policy engine for feature acceptance, deleting failing assertions, or adding `continue-on-error` to mandatory feature tests. Do not silently update snapshots to the new output without inspecting the behavioral change.

### 23.8 Migration, quality, package, and documentation checks

**Migrations.** All new revisions need the actual current `down_revision`, valid phase documentation, portable server defaults/backfills, and metadata parity on SQLite/PostgreSQL. The upstream pre-commit hooks and migration workflow require `Phase: EXPAND`, `MIGRATE`, or `CONTRACT` and validate migration patterns. Use phases accurately; they describe migration operations, not a request for parallel runtime implementations or staged deployment. Do not label destructive operations EXPAND, edit historical migrations, rename models/tables to dodge compatibility, or add a checker exemption for the feature. New non-null scalar fields need safe defaults/backfill treatment. [CI10, CI11]

Verify fresh database creation, populated pre-change upgrade, metadata/schema agreement, repeated application startup, and the explicit empty/adminless legacy-team repair policy. A migration fixture may intentionally contain invalid legacy teams; distinguish successful schema migration from collaboration readiness. Invalid records must not become valid by arbitrary administrator promotion. A candidate upgrade test must install/build candidate packages, not fetch an unmodified upstream nightly as the upgrade target. [CI12]

**Quality.** Match pinned Ruff/Biome/tool versions, supported Python syntax, React/TypeScript conventions, and applicable pre-commit hooks. Run Mypy and a terminating `tsc` check for changed contracts. Do not introduce `Any`, ignored security errors, or no-op exception handlers to silence checks. Keep no-any staged checks and secret scanning effective; test credentials must be clearly synthetic and only narrowly allowlisted where repository policy permits. [CI05, CI10, CI14, CI15, CI19]

**Packages.** Run backend and LFX suites in their intended separate contexts: both trees use a `tests` package and should not be collected together indiscriminately. Preserve provider-free `langflow-base` and `lfx` boundaries; no Langflow ORM import may be added to LFX. Check the bundled installation paths when selected, not just a default sync that silently skips bundle-guarded tests. Do not upgrade unrelated provider dependencies, widen bundle pins, or regenerate component catalogs solely to fix a local environment. Candidate package/image smoke tests must report the imported module paths and installed distribution versions. [CI08, CI20]

**Documentation/accessibility.** Run the current docs build and its applicable accessibility checks. Preserve existing accessibility coverage for the touched admin/share dialogs: labels, keyboard access, focus return, errors, and disabled permissions. This is functional regression/accessibility work, not an expansion into unrelated design/theme testing. Do not edit historical versioned documentation to imply these features existed in older releases. [CI16]

### 23.9 Future commands and deterministic execution record

These commands are instructions for the later implementation. They have **not** been executed by this plan update. Use the exact selected branch's commands/settings if they evolve, and record the differences.

```bash
# Repository root: lock-resolved development dependencies and original test entry points.
uv sync --group dev --package langflow-base
make unit_tests
make integration_tests_no_api_keys
make lfx_tests
make test_frontend_ci

# Structural contracts are additional checks, not replacements for runtime tests.
uv run python scripts/ci/check_authz_endpoint_matrix.py
uv run python scripts/ci/check_execution_principal_matrix.py
uv run pytest scripts/ci/ -v

# Match the actual upstream migration workflow in a disposable PostgreSQL environment.
# Supply LANGFLOW_TEST_DATABASE_URI from the test runner; never a production URI.
uv sync --extra postgresql
MIGRATION_VALIDATION_CI=true uv run pytest \
  src/backend/tests/unit/alembic/test_migration_execution.py -x -v

# Additional changed-code type checks. Run in the installed package context used by CI.
uv run mypy --namespace-packages -p langflow

# Frontend: lock-resolved dependencies, policy utilities, terminating type check and build.
cd src/frontend
npm ci
npm run test:e2e-utilities
npx tsc --noEmit --pretty --project tsconfig.json
npm run build

# Multi-user feature collection and execution: use the SAME configuration for both.
LANGFLOW_E2E_AUTHZ=true npx playwright test \
  tests/core/features/authz --grep '@authz' --project=chromium --list
LANGFLOW_E2E_AUTHZ=true npx playwright test \
  tests/core/features/authz --grep '@authz' --project=chromium --retries=0
```

Run the new focused tests named in Section 19 as well as the upstream commands. Configure PostgreSQL credentials/services through disposable fixtures and run the required Python-version matrix in CI; the single shell listing above is not a claim of matrix coverage. Ensure test extras remain installed for each invocation—do not run an automatic environment sync that removes required test/provider extras mid-job.

For changed-file hooks, derive an actual merge base, then run `uv run pre-commit run --from-ref "$MERGE_BASE" --to-ref HEAD`. Inspect auto-fixes and rerun. Execute staged-only hooks in their required staged context; an unstaged no-op run of the staged no-any hook is not evidence it checked the patch. For new migrations, run the exact validator command from `.pre-commit-config.yaml` / the migration workflow on every changed revision. If Python aliases/environment preparation differ, reproduce the repository's configured hook rather than invent a weaker replacement.

For the existing docs jobs, follow `.github/workflows/docs_test.yml`; for the Docker build, follow `.github/workflows/docker_test.yml` and execute `bash scripts/ci/test_docker_images.sh` **only on a dedicated disposable runner**. Never run its broad cleanup against a production/shared Docker daemon.

Add CI workflow syntax validation and tests of the changed selection/aggregate logic, including PR, ready-for-review, queue, manual full-run, fork read-only, and docs-only events. Verify that dynamic matrices, reusable inputs, runner strings/arrays, and action versions resolve in GitHub Actions. A YAML parse alone cannot prove workflow expressions or called inputs are valid.

### 23.10 Fork safety, external blockers, and false-green prevention

The intended core acceptance path requires no production credentials and no paid model calls. Keep it operational with deterministic flows, the actual application/enforcer, real disposable databases, and the existing loopback provider fixture.

Distinguish these conditions in reporting:

| Condition | Required handling |
|---|---|
| Fork PR token cannot write comments/check reports | Keep tests and local report validation blocking; conditionally omit only unavailable write-side reporting and retain downloadable artifacts. Never expose secrets through a privileged untrusted checkout. |
| Upstream-only self-hosted runner unavailable | Use the parameterized verified fork runner; queued jobs do not count as executed. Record architecture/resource coverage. |
| Upstream nightly-publication check fails | The inspected `CI Success` calculation can depend on today's upstream PyPI dev release, independently of patch correctness. Report the external blocker. A supported dispatch run can provide code-test evidence, but is not an upstream PR/queue green result. Do not fake publication, auto-add `skip-nightly-check`, or remove that policy from upstream. |
| `fast-track`, draft state, or path filter bypasses tests | Do not use those paths for final feature verification. A skipped test path is not feature acceptance. Use a non-draft candidate with the explicit required jobs, or a full validation run, and inspect job evidence. |
| `run-all-tests` unavailable/miswired or skips Docker | Implement the declared input/caller/condition corrections in Section 23.6; do not assume the option overrides every job or nested selector automatically. |
| Browser report gate says clean but feature tests were absent | Require the expected journey inventory and non-zero executed feature results. Report artifact completeness alone does not establish scenario coverage. |
| Reusable workflow checks a different ref | Reject its result as candidate evidence until checkout SHA/import paths/artifacts match the actual tested tree. |
| External security/coverage service unavailable | Retain its intended policy; record unavailable separately. A local scan is useful additional evidence, not fabricated success from the required GitHub App. |
| A check allows failure in the baseline | Preserve accurate upstream classification, but do not use that allowance to excuse defects introduced by this feature or to classify incomplete mandatory feature tests as passed. |
| Merge/base/security rules change after review | Refresh target rules/workflows/SHAs and rerun relevant checks. Previously recorded success does not transfer automatically. |

Sources: [CI02, CI06–CI09, CI17, CI21, CI22]. Do not enable release publishing, package upload, deployment, or upstream infrastructure credentials in the fork merely to run tests. Do not modify repository/organization security settings as an implicit side effect of the feature patch.

### 23.11 Required merge-test procedure and evidence

Before implementation, capture a baseline run when the runner is available, including selected/skipped jobs and collected test IDs. After implementation:

1. Reconcile `yazeedhasan97/langflow:feat/auth-team-sharing` (or the recorded authorized feature branch) with the actual fork `main` base. Preserve a reviewable, feature-focused diff and additive migration chain. Record every intentional API/test-contract change. Reconcile an upstream submission base separately only if requested.
2. Run the targeted feature tests and all applicable inherited upstream jobs from the fork on its implementation candidate. Run migration/concurrency checks on both database engines and ensure enabled-mode tests use the real service.
3. Validate the actual PR test-merge tree; if upstream contribution is intended, use the currently approved release-candidate base rather than substitute `main`.
4. For a queued merge, run checks on the queue-generated tree and record that SHA separately. Do not merge automatically or bypass maintainers' rules.
5. If the candidate/base changes, rerun tests affected by the final changes and obtain fresh required statuses. Preserve evidence of earlier failures and their fixes; do not present results for an older tree as final.
6. Produce a verification record mapping requirements and acceptance scenarios to tests, workflow/job names, run URLs, attempts, actual checkout SHA, database engine, Python/Node/browser versions, collected/executed/passed/failed/skipped/flaky counts, artifacts, and outstanding blockers.

Use these statuses explicitly: `PASS`, `FAIL`, `NOT RUN`, `BLOCKED EXTERNAL`, and `NOT APPLICABLE (reason)`. Keep upstream PR acceptance `NOT SUBMITTED / PENDING / ACCEPTED` separate from code-test results. Do not call a test suite passed when it only collected tests, imported a module, generated a matrix, uploaded an empty report, or passed after skipping all relevant tests.

### 23.12 Additional work packages and definition of done

The original work packages remain; extend WP-01 and WP-08 with this section and add the following connected work, not a separate implementation version. Start WP-09 during baseline/contract work and complete its wiring alongside the feature tests. WP-10 is final integrated verification, not background work or a separate release:

| Package | Required work | Completion evidence |
|---|---|---|
| WP-09 — Fork/CI reconciliation | Inventory the fork's actual instructions/rules/workflows and inherited upstream test requirements, fix discovery/refs/fork runners/reporting, classify intentional contract changes, and integrate feature jobs into existing CI. | Workflow selector/aggregate tests, actual non-empty feature collection, candidate checkouts, preserved baseline regression jobs. |
| WP-10 — Final integration verification | Run candidate/base/queue checks as applicable, fix attributable failures, verify migrations and artifacts, and complete evidence. | Final-SHA results and requirements-to-tests map; external blockers and upstream acceptance stated independently. |

Additional mandatory completion items:

- [ ] The plan's implementation repository is the user's fork; the upstream reference and candidate PR target are clearly distinguished.
- [ ] Root and applicable nested instructions were read and reflected in the final patch.
- [ ] Fork delivery targets `yazeedhasan97/langflow:main`. If upstream submission is separately requested, its active release-candidate target is verified and no upstream PR is incorrectly targeted at upstream `main`.
- [ ] `CI Success` and `Validate PR` keep the expected names/producers and have final-candidate evidence where required.
- [ ] Applicable merge-queue checks run on the actual queue tree; no claim of automatic upstream acceptance is made.
- [ ] Existing backend/LFX/frontend/templates/docs/Docker/migration and other selected regression jobs remain intact.
- [ ] The eight multi-user journeys are explicitly discovered and executed in the production-enforcer mode, not hidden by folders/tags/auto-login.
- [ ] Normal and authz browser invocations cannot overwrite each other's reports, coverage, or temporary databases.
- [ ] Required feature jobs cannot skip or fail while the aggregate reports feature completion.
- [ ] SQLite/PostgreSQL behavior and supported Python/package boundaries are verified.
- [ ] Changed-code lint/type/secret/migration checks pass without weakened policies.
- [ ] Deliberately changed upstream test expectations have a requirement-linked reviewable ledger, and negative coverage remains.
- [ ] Fork runner/permission limitations are handled without exposing secrets or running untrusted code in `pull_request_target`.
- [ ] Actual candidate packages/images are tested; public upstream releases are not misrepresented as the patch.
- [ ] Upstream nightly/service blockers and missing coverage are explicit, not converted into success.
- [ ] No application code or CI configuration has been changed by this planning revision itself; implementation/test statuses remain unclaimed until execution.

### 23.13 Fork access and implementation/E2E readiness — rechecked September 1, 2026

This is a **dated capability assessment**, not a feature test report. Recheck volatile facts at implementation time. The evidence below must not be reclassified as successful application implementation, migration, security validation, or E2E execution.

| Capability / prerequisite | Observed result | Meaning for implementation |
|---|---|---|
| Repository discovery/read access | **VERIFIED.** The connected GitHub integration returned `yazeedhasan97/langflow`, ID `1353667234`, public, not archived, default branch `main`. | The fork is reachable through the connector even though local terminal networking is unavailable. [FORK01] |
| Repository-level permissions | **REPORTED AVAILABLE.** Repository metadata reports `pull`, `push`, `admin`, `maintain`, and `triage` as true. No remote write was attempted in this plan-only update. | Source-edit/PR work is supported by the available connector actions, subject to their actual authorization at write time; this is not proof that every token scope exists. [FORK01] |
| Baseline alignment | **VERIFIED.** Fork `main` remains at `9e978f50a3700d079df62ecb2bd5909421093587`, matching the reviewed source baseline. | No baseline drift was observed in the fork during this recheck. Reconfirm before mutation. [FORK02] |
| Workflow-file editing permission | **UNVERIFIED.** No `.github/workflows` write was attempted and no token-scope claim was inferred from the repository's `admin`/`push` flags. | Contents/Workflows authorization is distinct; validate it when the authorized workflow change is made. Never request a token in chat or weaken CI because a workflow write is denied. [FORK06] |
| Fork Actions execution | **UNVERIFIED.** The workflow-run endpoint returned zero runs; no workflow was dispatched or PR created. | Check Actions enablement, allowed actions, runner eligibility/capacity, and a real run before claiming CI is operational. Zero runs does not establish why no runs exist. [FORK04, FORK07] |
| CI job/log/artifact tools | **AVAILABLE INTERFACES.** The connector exposes job/log/artifact reads, artifact download, and job-rerun actions; no existing run was available to exercise them here. | These provide a route to inspecting real results once a run exists. Their existence does not prove Actions-write authorization. |
| Initial CI trigger | **NOT EXERCISED.** Available GitHub actions inspected here do not expose a direct initial `workflow_dispatch` action. The generic public-resource fetch is GET-only. | During authorized implementation, an eligible same-fork PR/code-update event can trigger the existing configured workflow. Do not pretend to dispatch through a read endpoint. If the available tools cannot perform a required administrative/dispatch step, report the exact limitation and use a separately authorized invocation path. |
| Local language tools | **VERIFIED.** Python `3.13.5`, Node `22.16.0`, npm `10.9.2`, uv `0.10.0`, and Git are available. | Local file editing and some standalone checks are possible. These versions are environment facts, not changes to the repository's lockfiles or CI matrix. |
| Local application dependencies | **INCOMPLETE.** Import checks found `pytest`, Python Playwright, FastAPI, and Alembic, but not `sqlmodel`, `langflow`, `lfx`, `psycopg`, or `psycopg2`. | The actual Langflow backend cannot be assumed runnable in the current local environment. Dependency resolution/install and the locked frontend toolchain remain to be demonstrated. |
| Local network for source/dependencies | **BLOCKED HERE.** GET probes for the fork's Git transport, raw GitHub content, PyPI, and npm failed with temporary name-resolution errors. | Normal local clone/dependency installation is not currently available. The connected GitHub read path is separate and remains usable. Do not claim a clone or dependency install succeeded. |
| Browser process and interaction | **VERIFIED, LIMITED.** Python Playwright launched system Chromium `144.0.7559.96`, loaded a synthetic HTML page, and clicked a button successfully. | This proves local browser control only. It did not load Langflow, install the repository-pinned Node Playwright/browser build, test authentication, or exercise any sharing scenario. |
| Local PostgreSQL/container tooling | **UNAVAILABLE HERE.** `docker`, `podman`, `postgres`, and `psql` were not found; PostgreSQL Python drivers were also absent. | Database/container acceptance needs a prepared disposable runner or equivalent correctly provisioned environment. This does not weaken SQLite/PostgreSQL/ARM64 coverage requirements. |
| Inherited Docker CI runner | **CONFIRMED CONFIGURATION, ACCESS UNVERIFIED.** Fork `docker_test.yml` names `langflow-ai-arm64-40gb-ephemeral`, an upstream-specific self-hosted ARM64 label. | Apply the already planned runner parameterization and validate a runner available to the fork. Merely copying a label does not grant runner access. [FORK05] |
| Actual feature code, application tests, E2E, migration or container results | **NOT IMPLEMENTED / NOT RUN.** | Full correctness and E2E completion remain outcomes to demonstrate on the exact final fork commit. |

**Capability conclusion:** the implementation is feasible on the reviewed architecture, and repository access plus local artifact editing are established. A complete, correctly validated delivery is **conditional on a usable dependency/build/test execution environment and the required GitHub permissions**. This session has not proved those execution prerequisites. Do not turn “the code can be developed” into an unconditional promise that every test can already be run from this session.

The intended execution route is fork-owned, build-and-test-only GitHub Actions using the existing workflows with the specific fixes in Sections 19 and 23.5–23.10. It must run the production enforcer, separate users, real databases, and the candidate frontend/backend. No paid provider call or production secret is required for the core sharing acceptance journeys. No repository or Actions settings are modified by this assessment.

### 23.14 Exact fork workflow for the authorized implementation

The following commands and actions are **future implementation instructions only**. None was executed by updating this Markdown file. They require a network-enabled development runner for Git/install commands and the appropriate GitHub authorization for remote actions.

#### A. Establish the working copy and destination

For a fresh working copy:

```bash
git clone --origin origin https://github.com/yazeedhasan97/langflow.git
cd langflow
git remote add upstream https://github.com/langflow-ai/langflow.git
git fetch origin main
git switch --create feat/auth-team-sharing origin/main
git config remote.pushDefault origin
git config branch.feat/auth-team-sharing.pushRemote origin
git remote -v
git rev-parse HEAD
```

For an existing working copy, inspect its remotes, current branch, dirty files, and existing feature branch before changing anything; do not rerun `clone`, `remote add`, or `switch --create` blindly. Preserve the user's local work. Verify `origin` is the exact user fork and record the actual base SHA. The source baseline in this plan is a verification anchor, not an instruction to reset a newer branch or discard commits.

The intended plan location is `/auth_share_implementation_plan.md` at the fork root when plan/code publication is authorized. Copy the latest delivered revision without replacing source evidence with unverified claims. Use the fork's own `AGENTS.md` and actual dependency/test manifests.

#### B. Establish executable validation before claiming test readiness

1. Determine whether the selected execution environment can fetch/install the locked dependencies, run the required Python matrix, start the frontend/backend, and provision disposable PostgreSQL/SQLite/browser/container resources.
2. Check the fork's Actions settings/runner availability through an authorized route. If the available connector cannot read/modify those settings, do not infer their values from repository metadata or zero workflow runs. Report the specific unverified capability.
3. Make only the requested feature/CI changes on the feature branch when implementation is authorized. The first actual workflow-file write establishes whether the connected credential is allowed to update that path; a repository permission flag alone does not.
4. Start only a build/test run through a supported event or separately authorized dispatch. A same-fork PR from the feature branch into the fork's `main` can use the existing `pull_request` trigger after Actions is actually usable. Do not open an upstream PR, start a release/publishing workflow, modify protections, or request production secrets for this purpose.
5. Run available baseline checks and classify existing failures/environment blockers. Then implement and validate the feature with the production service. Fix attributable errors, rerun the affected checks, and include the required final full-regression pass.

Fork-owned Actions are the planned runtime route because local dependency networking is currently blocked, not because CI is already verified. If that route is also unavailable, complete only the work actually possible and report unexecuted acceptance items without calling the full implementation E2E-validated. Do not use artificial passes, skipped required tests, or a test-only authorization double as substitutes.

#### C. Deliver and verify the exact fork candidate

After implementation is authorized and the feature branch is ready for remote validation, use the explicit fork destination rather than an implicit remote:

```bash
git push origin HEAD:refs/heads/feat/auth-team-sharing
```

Set PR metadata explicitly:

```text
Base repository: yazeedhasan97/langflow
Base branch: main
Head repository: yazeedhasan97/langflow
Head branch: feat/auth-team-sharing
```

Creating the PR or pushing code is an implementation/delivery action, not authorized merely by this document update. Do not auto-merge it. Check out and test the fork implementation SHA and its actual PR integration SHA; use the fork's Actions run/job IDs and artifacts in the final report. When a reusable job builds from another tree or resolves an unmodified published backend, its result is not acceptance evidence for this feature.

Final evidence must identify the fork URL, exact commits, code/migration/doc scope, actual commands and configurations, all eight browser journeys, real policy/database assertions, collected/executed/passed/failed/skipped counts, retries, artifacts, and outstanding blockers. Preserve the full acceptance requirements in Sections 19 and 23. Upstream submission stays `NOT REQUESTED` unless the user separately requests it; it does not prevent a verified fork delivery.

---


## 24. Source appendix

Repository file paths below are pinned to the reviewed commit. Ruleset/branch/release responses and external documentation are dated observations rather than commit-pinned policy; recheck them at submission. These references identify evidence for the current baseline, not future implementation completion. Some files were examined through targeted ranges or import/search references; this is not a claim that every repository file was read or that any runtime test was executed. The earlier review also inspected representative tests and the RBAC foundations discussion.

All URLs are supplied as code-formatted source references so the Markdown remains portable. Historical upstream evidence is deliberately retained: it establishes what was reviewed, not where edits should be pushed. **Every implementation path in the body belongs to `yazeedhasan97/langflow`.** The fork baseline matches the cited upstream commit, so the same repository-relative paths identify the corresponding fork files at that baseline. New `FORKxx` references below record this revision's destination/readiness checks. Line numbers may shift when implementation begins.

### S01 — Architecture, goals, and OSS/enforcer boundary

`docs/docs/Develop/authorization.mdx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/docs/docs/Develop/authorization.mdx`

`AGENTS.md`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/AGENTS.md`

### S02 — Existing Langflow pass-through implementation

`src/backend/base/langflow/services/authorization/service.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/service.py`

### S03 — Authorization interface, capabilities, and lifecycle contracts

`src/lfx/src/lfx/services/authorization/base.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/lfx/src/lfx/services/authorization/base.py`

### S04 — Canonical role, team, membership, share, and audit models

`src/backend/base/langflow/services/database/models/auth/authz.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/database/models/auth/authz.py`

### S05 — Existing team and membership API

`src/backend/base/langflow/api/v1/authz_teams.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_teams.py`

### S06 — Existing team/membership request and response schemas

`src/backend/base/langflow/api/v1/schemas/authz_teams.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/schemas/authz_teams.py`

### S07 — Share administration, visibility, and post-commit policy hooks

`src/backend/base/langflow/api/v1/authz_shares.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_shares.py`

### S08 — Canonical share create/update/read schemas

`src/backend/base/langflow/api/v1/schemas/authz_shares.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/schemas/authz_shares.py`

### S09 — Project Folder ownership and child relationships

`src/backend/base/langflow/services/database/models/folder/model.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/database/models/folder/model.py`

### S10 — Workflow ownership, scope, publication, and read models

`src/backend/base/langflow/services/database/models/flow/model.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/database/models/flow/model.py`

### S11 — Share-aware fetch and identifier privacy

`src/backend/base/langflow/services/authorization/fetch.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/fetch.py`

### S12 — List visibility and SQL prefilter integration

`src/backend/base/langflow/services/authorization/listing.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/listing.py`

### S13 — Shared flow CRUD, canonical destinations, and owner-bound fields

`src/backend/base/langflow/api/v1/flows_helpers.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/flows_helpers.py`

`src/backend/base/langflow/api/v1/authz_route_dependencies.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_route_dependencies.py`

### S14 — Effective-permission API and owner override

`src/backend/base/langflow/api/v1/authz_me.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_me.py`

### S15 — Canonical resource action vocabulary

`src/backend/base/langflow/services/authorization/actions.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/actions.py`

### S16 — Transaction-scoped authorization lifecycle helpers

`src/backend/base/langflow/services/authorization/lifecycle.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/lifecycle.py`

### S17 — Existing credential authentication and external group reconciliation

`src/backend/base/langflow/services/auth/service.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/auth/service.py`

`src/backend/base/langflow/services/auth/utils.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/auth/utils.py`

### S18 — Existing authentication, authorization, and audit settings

`src/lfx/src/lfx/services/settings/auth.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/lfx/src/lfx/services/settings/auth.py`

### S19 — Project sidebar Share placement and empty OSS resource extension

`src/frontend/src/components/core/folderSidebarComponent/components/sideBarFolderButtons/components/select-options.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/components/core/folderSidebarComponent/components/sideBarFolderButtons/components/select-options.tsx`

`src/frontend/src/customization/components/custom-resource-share-action.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/customization/components/custom-resource-share-action.tsx`

### S20 — Workflow Share extension and existing menu integration

`src/frontend/src/customization/components/custom-flow-share-action.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/customization/components/custom-flow-share-action.tsx`

`src/frontend/src/pages/MainPage/components/dropdown/index.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/pages/MainPage/components/dropdown/index.tsx`

`src/frontend/src/components/core/flowToolbarComponent/components/deploy-dropdown.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/components/core/flowToolbarComponent/components/deploy-dropdown.tsx`

### S21 — Frontend permission context, utilities, types, and query hook

`src/frontend/src/contexts/permissionsContext.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/contexts/permissionsContext.tsx`

`src/frontend/src/utils/permissionUtils.ts`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/utils/permissionUtils.ts`

`src/frontend/src/types/permissions/index.ts`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/types/permissions/index.ts`

`src/frontend/src/controllers/API/queries/permissions/use-get-effective-permissions.ts`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/controllers/API/queries/permissions/use-get-effective-permissions.ts`

### S22 — Actual frontend routing and empty administration/custom-page hooks

`src/frontend/src/routes.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/routes.tsx`

`src/frontend/src/customization/components/custom-admin-page-menu-item.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/customization/components/custom-admin-page-menu-item.tsx`

`src/frontend/src/customization/utils/custom-routes-store-pages.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/customization/utils/custom-routes-store-pages.tsx`

### S23 — Declared route-to-authorization contracts

`scripts/ci/authz_endpoint_matrix.json`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/authz_endpoint_matrix.json`

### S24 — Declared execution principals and endpoint-family exceptions

`scripts/ci/execution_principal_matrix.json`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/execution_principal_matrix.json`

`scripts/ci/check_execution_principal_matrix.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/check_execution_principal_matrix.py`

### S25 — Existing single Langflow authorization factory

`src/backend/base/langflow/services/authorization/factory.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/factory.py`

### S26 — Project CRUD, shared child filtering, and ORM deletion safeguards

`src/backend/base/langflow/api/v1/projects.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/projects.py`

### S27 — Role/assignment administration and surviving source provenance

`src/backend/base/langflow/api/v1/authz_roles.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_roles.py`

`src/backend/base/langflow/api/v1/authz_role_assignments.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_role_assignments.py`

`src/backend/base/langflow/api/v1/schemas/authz_role_assignments.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/schemas/authz_role_assignments.py`

### S28 — Explicit public grants and anonymous execution isolation

`src/backend/base/langflow/services/authorization/public_access.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/public_access.py`

`src/backend/base/langflow/api/utils/flow_utils.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/utils/flow_utils.py`

### S29 — Published authz foundations and seeded role permissions

`src/backend/base/langflow/alembic/versions/7c8d9e0f1a2b_authz_foundations.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/alembic/versions/7c8d9e0f1a2b_authz_foundations.py`

### S30 — Pluggable service discovery and registration conventions

`src/lfx/PLUGGABLE_SERVICES.md`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/lfx/PLUGGABLE_SERVICES.md`

### S31 — Repository development and test guidance

`AGENTS.md`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/AGENTS.md`

### S32 — Test-only enforcer, explicitly not OSS production policy

`src/backend/tests/unit/services/authorization/_policy_double.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/tests/unit/services/authorization/_policy_double.py`

### S33 — Audit query contract and decision/mutation classification

`src/backend/base/langflow/api/v1/authz_audit.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/authz_audit.py`

`src/backend/base/langflow/services/authorization/guards.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/guards.py`

### S34 — Existing API router registration

`src/backend/base/langflow/api/router.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/router.py`

`src/backend/base/langflow/api/v1/__init__.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/__init__.py`

### S35 — Existing locked-flow guards and row-lock helper

`src/backend/base/langflow/services/database/models/flow/guards.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/database/models/flow/guards.py`

### S36 — Writer-aware graph override for supported build routes

`src/backend/base/langflow/services/authorization/flow_data_override.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/services/authorization/flow_data_override.py`

### S37 — Representative actual execution-principal regression tests

`src/backend/tests/unit/api/v1/test_execution_principal_contract.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/tests/unit/api/v1/test_execution_principal_contract.py`

### S38 — User directory protection and native session endpoints

`src/backend/base/langflow/api/v1/users.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/users.py`

`src/backend/base/langflow/api/v1/login.py`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/backend/base/langflow/api/v1/login.py`

### S39 — Frontend mutation hook and project response-type location

`src/frontend/src/controllers/API/queries/flows/use-patch-update-flow.ts`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/controllers/API/queries/flows/use-patch-update-flow.ts`

`src/frontend/src/pages/MainPage/entities/index.tsx`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/src/pages/MainPage/entities/index.tsx`

### S40 — Browser-test harness: existing auto-login and isolated tests directory

`src/frontend/playwright.config.ts`
`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/playwright.config.ts`

### Additional official documentation checked

`https://docs.langflow.org/next/authorization`
`https://docs.langflow.org/authentication-overview`

Published documentation can describe a different release from `main`. The pinned source takes precedence for implementation-specific findings. The full plan above is the proposed enhancement, not a statement that the public documentation already describes it.

### RBAC foundations discussion

`https://github.com/langflow-ai/langflow/pull/13153`

The reviewed discussion explains the deliberate OSS foundations/enforcement split. It is historical design evidence, not proof that every issue raised in old review comments remains present at the pinned commit.

---

**End of plan. No implementation has been performed as part of generating this file.**

### CI evidence added by this revision

The following references support Section 23. Repository files are pinned; live GitHub rules/ref/release responses and official documentation were checked on September 1, 2026. Descriptions report source inspection, not successful test runs.

### CI01 — Upstream contribution target and PR conventions

Contributors are directed to the active release-candidate branch, not main; semantic title and maintainer review requirements are stated.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/CONTRIBUTING.md`

### CI02 — Public merge rulesets and protection-read limitation

Reviewed September 1, 2026. Both returned active CI Success / Validate PR requirements and review/queue rules. Effective rules differ by target and can change. Legacy branch fields alone are insufficient to establish effective rules; inspect target rulesets and the actual PR requirements.

`https://api.github.com/repos/langflow-ai/langflow/rulesets/986381`

`https://api.github.com/repos/langflow-ai/langflow/rulesets/13786507`

### CI03 — Rechecked upstream and fork refs

Both main refs returned the historical review SHA on September 1, 2026. These API URLs are mutable; record actual SHAs when implementing.

`https://api.github.com/repos/langflow-ai/langflow/branches/main`

`https://api.github.com/repos/yazeedhasan97/langflow/git/ref/heads/main`

### CI04 — Release metadata and candidate release branch

The release branch response returned c379987876964818d7cc09994fbfd165f7546cc4. Branch existence does not replace confirmation of the current accepted PR target.

`https://api.github.com/repos/langflow-ai/langflow/branches/release-1.12.0`

### CI05 — Root agent instructions and development conventions

Root guidance establishes package architecture, development commands, supported toolchains, and test practices. Applicable nested instructions and any target-branch updates must additionally be inspected during implementation.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/AGENTS.md`

### CI06 — CI orchestrator, default paths, conditions, and aggregate result

Reviewed PR/merge-group triggers, reusable versus dispatch inputs, Python matrix, tests/core caller default, path/job conditions, nightly-publication dependency, and CI Success aggregation.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/ci.yml`

### CI07 — Actual Validate PR producer

Metadata-only conventional PR validation on pull_request_target and merge_group; no untrusted code checkout should be added to this privileged event.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/conventional-labels.yml`

### CI08 — Backend, LFX, bundle-installed, integration, and CLI tests

Inspected relevant workflow jobs, test commands, caller-selected Python versions, package-context isolation, and externally conditional CLI checks. Reinspect the complete selected workflow when executing.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/python_test.yml`

### CI09 — Playwright suite/tag selection, shards, and report validation

Inspected discovery and execution/report jobs, tool versions, supported suite values, retry behavior, and artifact completeness rules. Optional live-provider/store jobs are not the credential-free feature acceptance path.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/typescript_test.yml`

### CI10 — Configured pre-commit and migration-phase hooks

Ruff, formatting, phase validation, migration patterns, secret scanning, Biome/staged no-any, and file-triggered trust/policy hooks.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.pre-commit-config.yaml`

### CI11 — PR migration consistency, patterns, and real services

PostgreSQL 16 model/migration checks, background tests with Redis, phase/pattern validation, and the current hard-coded main diff-base assumption.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/migration-validation.yml`

### CI12 — Separate published stable-to-nightly migration workflow

This separately called/dispatched workflow tests published artifacts. Candidate upgrade verification must not substitute an unchanged upstream nightly for the fork code.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/db-migration-validation.yml`

### CI13 — CI-script suite and authorization route checker

Exact script-suite command and route/principal contract checker locations; existence/reference checks do not prove runtime enforcement.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/ci-scripts-test.yml`

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/check_authz_endpoint_matrix.py`

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/test_authz_endpoint_matrix.py`

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/check_execution_principal_matrix.py`

### CI14 — Frontend lint behavior

Changed-file Biome check and dispatch/ref behavior; CI currently treats this job as informational outside the CI Success dependency list.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/lint-js.yml`

### CI15 — Python typing workflow

Reusable/dispatched Mypy checks and supported-version matrix. This workflow is not automatically evidence of execution in every PR run.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/lint-py.yml`

### CI16 — Documentation build and accessibility

Docusaurus build plus applicable light/dark IBM Equal Access scans; preserve checks selected by the current workflow.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/docs_test.yml`

### CI17 — Docker runner, ref, and retry integration

Original image checks require an upstream-labeled self-hosted ARM64 runner. Fork runner/ref parameterization must preserve actual build assertions.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/docker_test.yml`

### CI18 — Changed-file selectors

Original Python/frontend/API/database/docs/Docker category paths, including broad Docker selection for backend/frontend/LFX changes.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/changes-filter.yaml`

### CI19 — Frontend tool commands and real autosave test policy

Verified Playwright version, utility suite, Vite build, and type-check script that also starts Vite; use a terminating tsc invocation in CI. Preserve actual full-flow UI persistence evidence.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/package.json`

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/src/frontend/tests/utils/flow-editor-persistence-policy.test.mjs`

### CI20 — Jest result artifacts and candidate-image package checks

Jest execution/JUnit/coverage reporting and source-built image/version/base-package/health assertions. Docker cleanup is broad and requires a dedicated disposable runner.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/jest_test.yml`

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/scripts/ci/test_docker_images.sh`

### CI21 — GitHub event security and required-check semantics

Official documentation checked for fork event permissions, merge-group execution, and check results tied to candidate SHAs. Apply current event/token behavior and do not execute untrusted PR code in a privileged target event.

`https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows`

`https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks`

`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue`

`https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target`

### CI22 — Hosted runner availability and resource limits

Official documentation lists public-repository ARM64 hosted runners including ubuntu-24.04-arm. Availability does not guarantee adequate disk/capacity for all Langflow images; validate resources or use an authorized adequate runner.

`https://docs.github.com/en/actions/reference/runners/github-hosted-runners`

---

### CI23 — Existing component accessibility job

Frontend changes select the existing jest-axe workflow, which invokes `make test_frontend_a11y_unit_ci`. Retain this regression coverage as well as new feature-specific accessibility assertions.

`https://github.com/langflow-ai/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/a11y-unit-tests.yml`

---

### FORK01 — Implementation repository and reported access

Read through the connected GitHub integration on September 1, 2026: repository ID `1353667234`, `yazeedhasan97/langflow`, public, not archived, default branch `main`; repository permissions reported `pull/push/admin/maintain/triage=true`. No remote write was attempted in this revision and those flags are not a token-scope audit.

`https://github.com/yazeedhasan97/langflow`

`https://api.github.com/repos/yazeedhasan97/langflow`

### FORK02 — Verified fork branch and tree

Fork `main` was rechecked at commit `9e978f50a3700d079df62ecb2bd5909421093587`, tree `afc339fd9d5450327580f535f8ba557a0682321a`.

`https://api.github.com/repos/yazeedhasan97/langflow/branches/main`

`https://github.com/yazeedhasan97/langflow/tree/9e978f50a3700d079df62ecb2bd5909421093587`

### FORK03 — Fork protection/ruleset observations

The branch response reported `protected=false`. The readable ruleset collection including parents returned an empty array. Treat these as dated responses; do not infer every possible external/account restriction or alter protections from this plan.

`https://api.github.com/repos/yazeedhasan97/langflow/rulesets?includes_parents=true&per_page=100`

### FORK04 — Workflow-run record

The repository run query returned `{"total_count":0,"workflow_runs":[]}`. No Actions run was initiated by this check. This is not proof of Actions enablement or disablement.

`https://api.github.com/repos/yazeedhasan97/langflow/actions/runs?per_page=5`

`https://github.com/yazeedhasan97/langflow/actions`

### FORK05 — Actual inherited Docker runner dependency

The fork's pinned workflow was read directly and still specifies the upstream-specific self-hosted ARM64 label on both attempts. Runner authorization/capacity was not established.

`https://github.com/yazeedhasan97/langflow/blob/9e978f50a3700d079df62ecb2bd5909421093587/.github/workflows/docker_test.yml`

### FORK06 — Workflow-file permissions are distinct from repository metadata

Official GitHub documentation was rechecked. Updating workflow files needs the appropriate workflow authorization in addition to normal repository-content access for the token type. The connected credential's exact scope was not established by this plan update.

`https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents`

### FORK07 — Actions settings, triggering, and local execution observations

Official documentation used for settings/event semantics:

`https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository`

`https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows`

The local-tool, Python import, network-reachability, and synthetic browser checks in Section 23.13 are direct environment observations from this conversation on September 1, 2026, not facts inferred from these documentation pages. The browser interaction used synthetic local HTML only. No Langflow test was run and no package install, repository clone, workflow dispatch, or remote write was performed.

---

**Revision outcome:** the downloadable plan now explicitly targets the user fork throughout delivery, CI, and verification instructions. Only the Markdown and local preparation/diagnostic artifacts were changed. No application code, repository branch/PR/workflow, GitHub setting, migration, deployment, or Langflow test/CI run was changed or executed by this revision. A local synthetic browser smoke check is recorded separately and is not application E2E evidence.
