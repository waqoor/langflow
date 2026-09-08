# Authentication, Authorization, Teams, and Resource Sharing — Final Implementation Plan

**Implementation repository:** `waqoor/langflow`  
**Implementation URL:** `https://github.com/waqoor/langflow`  
**Delivery branch:** `feat/auth-team-sharing`  
**Fork delivery target:** `waqoor/langflow:main`  
**Upstream reference:** `langflow-ai/langflow`  
**Related upstream issue:** `langflow-ai/langflow#14932`  
**Current fork main:** `e4ae38be2636f2532053eeee3ebcb19ea08cc406` (PR #1 merged September 5, 2026, 13:01:03 UTC)  
**Original fork / upstream baseline:** `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`  
**Current feature branch head:** `63215eccf8c06b291567e25fb5772bf9e90bab52`  
**Validated implementation candidate:** `39e0d87ca7187739a3f105200dae67afd7eaf097`  
**Current migration:** `bf6c22022777`, down revision `c6d8e0f2a4b7`, phase `MIGRATE`  
**Plan date:** September 6, 2026  
**Document revision:** 1.6  
**Status:** The feature is substantially implemented and validated in the fork. This is the final implementation/alignment plan for the current contribution. The current native evaluator remains the active fork baseline unless Langflow maintainers explicitly select a Casbin-backed packaging direction. If Casbin is selected, this revision defines the preferred single-engine replacement: one minimal domain-scoped Casbin decision core covering scoped roles, team-management authority, team membership, and user/team shares, while canonical ownership, resource resolution, credential ceilings, transactional invariants, and mutation concurrency remain Langflow responsibilities. Casbin is never added beside the native evaluator, and this plan does not authorize a V2 path, sidecar, shadow evaluator, second policy authority, or scope expansion.

---

## 1. Purpose

Preserve and upstream-align the existing team-based RBAC and project/workflow sharing enhancement while keeping one authorization architecture, one canonical policy source, one runtime decision path, and the existing Langflow authentication and execution boundaries.

This revision supersedes stale planning assumptions from revision 1.2. It treats the current fork implementation as the working baseline and defines only the corrections, invariants, architecture rules, and remaining decisions required for a production-quality and upstream-reviewable result.

The feature must continue to provide:

- Platform-admin team creation and lifecycle management.
- Team-scoped `admin`, `maintainer`, and `user` roles.
- Non-empty team creation and active-Team-Admin invariants.
- User and team sharing for projects and workflows.
- Two UI sharing modes:
  - **Can use** → canonical `execute`.
  - **Can edit** → canonical `write`.
- Dynamic project → workflow inheritance without copied child grants.
- Direct workflow sharing without exposing private parent projects or siblings.
- Preserved creator ownership.
- Authenticated-recipient execution identity.
- Immediate policy effect for newly admitted requests after committed revocation/downgrade.
- Optimistic concurrency for collaborative writes.
- Consistent backend, list, direct-URL, UI, and runtime authorization.

---

## 2. Current implementation baseline

### 2.1 Current state

The implementation is no longer a design-only or initial-policy-only branch.

The validated candidate already contains the integrated backend, database migration, authorization service, team/share APIs, project/workflow enforcement, concurrency handling, frontend, tests, CI wiring, and documentation required by the original feature scope.

The current verification record reports, among other evidence:

- Native authorization matrix passing on SQLite and PostgreSQL 16.
- Python 3.10 and 3.14 coverage for the native authorization matrix.
- All eight connected multi-user authorization browser journeys passing.
- Full frontend Jest passing.
- Inherited backend, LFX, integration, bundle, documentation, and ARM64 candidate-image checks passing on the recorded candidate, subject to the explicitly recorded inherited limitations.

Do not restart the feature from the original revision-1.2 assumptions. Inspect the current branch first and modify the existing implementation in place.

### 2.2 Current architecture

The current fork implements enforcement directly in:

`langflow.services.authorization.service.LangflowAuthorizationService`

with canonical database reads from `authz_*` and supporting resource tables.

The current runtime decision path is conceptually:

```text
authentication
    -> canonical resource resolution
    -> credential/access ceilings
    -> BaseAuthorizationService
    -> current native authorization evaluator
    -> operation-specific restrictions
    -> concurrency check
    -> mutation/execution
```

The current native evaluator is the only enforcing decision engine in the fork.

### 2.3 Upstream architecture direction

Upstream Langflow currently defines authorization as a pluggable layer:

- `BaseAuthorizationService` is the application-facing contract.
- OSS retains a pass-through `LangflowAuthorizationService`.
- Canonical administration/policy data lives in `authz_*`.
- `casbin_rule` exists as compiled-policy storage.
- A registered authorization implementation/plugin may compile `authz_*` into `casbin_rule` and enforce through the existing service boundary.

Therefore the fork's current native enforcing implementation is a deliberate distribution difference from upstream's present OSS packaging model.

That packaging difference must remain explicit. Do not describe it as already accepted upstream.

### 2.4 Final review conclusions

The final review locks the following conclusions:

1. **The feature behavior is already the working baseline.** Do not rebuild teams, sharing, inheritance, concurrency, frontend, or execution identity from revision-1.2 assumptions.
2. **The only unresolved architectural question is enforcement packaging.** The current fork uses native enforcement; upstream currently documents real enforcement behind the registered authorization-service/plugin seam.
3. **The community Casbin comment is design input, not maintainer direction.** Do not refactor a validated branch solely because of that comment.
4. **No Casbin production work begins unless the packaging direction is explicitly selected.** The fork can remain complete with the current native evaluator; an upstream submission may require a packaging correction.
5. **If Casbin is selected, it replaces the policy-decision core.** It does not coexist with the current native evaluator.
6. **The fork PR description has been reconciled.** PR #1 now describes the implemented database/API/frontend/E2E work and the exact `39e0d87ca7` candidate evidence; it was merged into fork `main` at `e4ae38be26`. Further integration corrections must record their own validation without relabelling that historical evidence or describing the merged PR as WIP.
7. **The community Casbin sketches are useful design evidence but are not implementation authority.** The later domain-scoped sketch validates the direction of literal domains, direct team principals, bounded actions, canonical ownership outside Casbin, and `keyMatch2` isolation. This revision keeps those strengths but completes the missing Langflow semantics: scoped `AuthzRoleAssignment`, project -> workspace -> `*` domain-chain evaluation, same-enforcer team-management authorization, explicit project child `flow:create`, active-user/team lifecycle, and atomic canonical + derived-policy revocation correctness. External Go/Casbin assertions remain model evidence only until reproduced through the selected Python implementation and Langflow real-service/E2E tests.

These conclusions do not create a runtime approval gate. They define how the contribution must remain internally consistent while upstream review determines whether the final enforcer is packaged natively or behind the existing plugin boundary.

---

## 3. Locked architecture constraints

These constraints are mandatory for all further work.

### 3.1 Single source of truth

The following remain the canonical writable authorization state:

- `authz_role`
- `authz_role_assignment`
- `authz_role_assignment_grant`
- `authz_team`
- `authz_team_member`
- `authz_share`
- canonical user/resource ownership and scope rows

No other policy store may become independently authoritative.

### 3.2 Single application authorization boundary

All protected application paths continue to authorize through:

`BaseAuthorizationService`

using the existing service manager/dependency accessors and route guards.

Do not introduce:

- authorization middleware that bypasses the service;
- direct Casbin calls from routes/components;
- frontend policy evaluation as authority;
- a second service registry key;
- a second authz API family;
- a replacement V2 authorization API.

### 3.3 Single active decision engine

Exactly one runtime evaluator may make role/share/team policy decisions.

Forbidden:

```text
native evaluator OR Casbin
native evaluator AND Casbin
native evaluator with Casbin fallback
Casbin with native fallback
feature flag choosing between two production evaluators
shadow comparison in production
dual-write policy engines
```

Test-time parity comparison is allowed during a replacement refactor, but only one evaluator may ship as the active implementation.

### 3.4 Authentication stays separate

Keep existing:

- local sessions/JWT;
- API-key authentication;
- external authentication/JIT identity;
- credential-scoped access ceilings;
- existing identity and principal resolution.

Authorization must never replace authentication or infer the caller from request-supplied user/team fields.

### 3.5 Domain/business invariants stay above the policy engine

Casbin or any other policy engine must not become the transactional domain-validation layer.

The following remain application/database responsibilities:

- non-empty team roster;
- active team has at least one active Team Admin;
- final-member/final-active-admin protection;
- source-managed membership rules;
- account/team lifecycle transitions;
- ownership rules;
- resource/destination canonicalization;
- owner-managed field restrictions;
- optimistic concurrency;
- publication/authentication-setting restrictions;
- complete-set delete validation;
- audit transaction rules.

---

## 4. Final Casbin decision

### 4.1 Default implementation path

Do **not** integrate Casbin into the production branch merely because it was suggested or because an isolated policy sketch passes external model tests.

The current `waqoor/langflow` evaluator is already implemented and validated. Until Langflow maintainers explicitly select or accept a Casbin-backed packaging direction for this contribution, it remains the single production evaluator in the fork.

Allowed before that decision:

- review and refine `model.conf` proposals;
- validate Casbin semantics against the existing acceptance matrix;
- discuss domain/resource relationships and compiler behavior;
- create isolated model tests that do not enter the production dependency/runtime path.

Not allowed before that decision:

- adding `pycasbin` to the production dependency graph;
- populating `casbin_rule` for runtime use;
- adding a dormant Casbin service behind a feature flag;
- calling Casbin directly from routes/components;
- keeping native enforcement and Casbin selectable or active together.

If no maintainer packaging direction is received, finish and report the fork with the current native evaluator and document the packaging difference from upstream. Do not manufacture a second implementation in anticipation of a possible review request.

### 4.2 If Casbin is selected

Casbin is introduced only as a **clean replacement of the current policy-decision core**.

The selected architecture is:

```text
CANONICAL LANGFLOW STATE
authz_* + users + resource ownership/project/workspace scope
                  |
                  | deterministic compilation
                  v
DERIVED / REBUILDABLE POLICY
casbin_rule
                  |
                  v
ONE CASBIN ENFORCER
                  |
                  v
BaseAuthorizationService
                  |
                  v
existing guards/routes/UI/runtime
```

`authz_*` and canonical resource/user rows remain authoritative. `casbin_rule` is only a materialized policy projection.

Deleting and deterministically rebuilding the derived rules from canonical state must restore equivalent authorization. No public API, admin UI, CLI, migration, or operational procedure may treat `casbin_rule` as independently authorable policy.

### 4.3 Packaging selection

Upstream Langflow's authorization direction remains:

```text
OSS Langflow
    -> BaseAuthorizationService + pass-through default
    -> registered authorization implementation
    -> real enforcement
```

For an upstream-oriented contribution, registered authorization implementation/plugin packaging is the default alignment assumption unless maintainers explicitly accept native OSS enforcement.

If registered/plugin packaging is selected:

- preserve/restore the upstream pass-through semantics of the default OSS `LangflowAuthorizationService`;
- register exactly one Casbin-backed implementation through the existing authorization-service seam;
- move the feature's policy-decision logic into that implementation;
- remove the current native policy evaluator from the active feature path;
- use only public Langflow contracts; do not copy unavailable Enterprise implementation code.

If native packaging is explicitly selected:

- keep one `LangflowAuthorizationService`;
- replace only its internal policy-decision core with Casbin;
- retain `BaseAuthorizationService` as the application boundary;
- do not additionally register another Casbin service.

Only one packaging result may ship. Do not implement both and defer the choice to a runtime flag.

### 4.4 One policy engine; Langflow still owns domain semantics

If Casbin becomes the selected decision engine, **all policy-based authorization decisions** move to that one enforcer, including:

- scoped application-role permissions;
- Team Admin/Maintainer/User management authority;
- direct user shares;
- team-targeted resource shares;
- project-inherited child permissions;
- share-management permissions that come from policy rather than canonical owner/platform semantics.

Do not keep `team_operation_allowed()`, `effective_access*`, role-permission evaluation, share-action evaluation, or another Python helper as a competing final allow/deny engine after Casbin is selected.

Langflow application/domain code still owns facts and invariants that are not policy-engine decisions, including:

- authentication and active-user resolution;
- narrower credential/external-auth ceilings;
- canonical resource, project, workspace, owner, and destination resolution;
- configured Platform Admin/superuser semantics;
- canonical owner semantics;
- non-empty team roster and active-Team-Admin invariants;
- source/provenance restrictions;
- target/new-role classification for team mutations;
- ownership-bound fields, publication/authentication restrictions, and dependency isolation;
- optimistic concurrency and complete-set mutation validation;
- audit transaction rules.

The boundary is:

```text
Langflow determines WHAT the canonical request means and whether the resulting state is valid.
Casbin determines WHETHER the canonical principal has the requested policy permission.
```

### 4.5 Minimal-Casbin principle

Do **not** recreate Langflow's authorization model as a second relationship graph inside Casbin.

The target is:

```text
Langflow canonical state
        |
        v
small deterministic compiler
        |
        v
minimal Casbin policy/relationships
        |
        v
one enforcer
```

The following concepts remain semantically distinct in Langflow:

- scoped application roles;
- Team Admin/Maintainer/User management roles;
- team membership;
- user/team resource sharing;
- canonical resource ownership.

Semantic separation does not require one Casbin relationship manager per concept.

Start with the smallest model that satisfies the acceptance matrix. Do not introduce `g2`, `g3`, additional role managers, ReBAC layers, intermediate editor/viewer resource roles, or a custom relationship subsystem unless focused tests prove the smaller model cannot preserve semantics without policy fanout, duplicated policy, or semantic distortion.

An additional Casbin relationship mechanism is allowed only when it is the smallest justified solution and remains internal to the one selected enforcer.

---

## 5. Casbin policy model requirements

This section applies only if Casbin is selected.

### 5.1 Preserve the Langflow request contract

Keep the framework-neutral request contract:

```text
subject
domain
object
action
```

Canonical application examples remain:

```text
subject = user:<uuid>
domain  = project:<uuid> | workspace:<uuid> | *
object  = flow:<uuid> | project:<uuid> | flow:* | ...
action  = read | execute | write | create | delete | deploy | ...
```

The backend resolves the canonical resource and domain chain from stored data. Caller-supplied `domain`, `workspace_id`, `folder_id`, `owner_id`, team ID, or user ID never becomes policy authority.

Do not collapse domain scope into a hierarchical `obj` string. Teams are not resource containers; never replace Langflow's project/workspace/resource model with `team/.../project/.../workflow/...` paths.

Casbin may use a private normalized representation such as `flow/<uuid>` or `flow/*` internally when a matcher requires slash-safe paths. That normalization is an enforcer/compiler detail only; it does not change Langflow's external `flow:<uuid>` / domain contract.

### 5.2 Preferred minimal model

Start with a model equivalent to:

```ini
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = (r.sub == p.sub || g(r.sub, p.sub)) && r.dom == p.dom && objectMatch(r.obj, p.obj) && r.act == p.act
```

`objectMatch` should be exact object equality plus the minimum required type wildcard such as `flow/*`. If `keyMatch2` is used internally, only feed it normalized slash-safe internal object keys and keep domain matching literal.

Use `g` primarily for the relationship that materially avoids policy fanout:

```text
active user -> active valid team principal
```

Do not introduce extra grouping systems merely because Casbin supports them.

Prefer direct `p` compilation for:

- direct user shares;
- scoped application-role permissions after compiler flattening;
- team-management permissions after canonical role/target classification.

This keeps the Casbin model small while still making Casbin the sole policy evaluator.

### 5.3 Compile scoped `AuthzRoleAssignment` permissions; do not keep a Python role evaluator

Existing `AuthzRole`, parent-role relationships, `AuthzRoleAssignment`, assignment provenance, and domain scopes are part of the authorization model and must be preserved.

The compiler resolves them from canonical state and **flattens effective role permissions** before writing derived policy. Do not reproduce the full Langflow role hierarchy as a second Casbin role graph unless a demonstrated requirement makes flattening incorrect.

Required compiler behavior:

- resolve parent-role permissions with cycle detection and a strict depth bound;
- malformed/cyclic chains grant nothing;
- expand persisted `<resource>:*` role permission slugs to the explicit currently supported action set; never emit `act="*"`;
- preserve surviving assignment provenance in canonical tables; enforcement policy need not duplicate provenance metadata;
- compile project assignments only to `project:<uuid>`;
- compile workspace assignments only to `workspace:<uuid>`;
- compile global assignments only to `*`;
- do not treat unsupported `org` scope as global; it requires an actual registered resolver.

Conceptually:

```text
AuthzRoleAssignment(user=U, domain=project:P, effective_permissions={flow:read, flow:write})
        |
        v
p, U, project:P, flow/*, read
p, U, project:P, flow/*, write
```

Equivalent direct concrete-resource policies may be used where the permission contract requires them, but the compiler must not broaden the canonical assignment domain.

### 5.4 Domain-chain evaluation: project -> workspace -> global

Use literal domain equality inside Casbin. Do not use pattern matching for authorization domains.

For each resource, `BaseAuthorizationService` resolves the applicable canonical domain chain from stored state and evaluates the **same enforcer** against that chain:

```text
project-contained resource:
    project:<project-id>
    workspace:<workspace-id>   # when canonically present
    *

workspace-scoped resource:
    workspace:<workspace-id>
    *

truly global/unscoped resource:
    *
```

The more specific domain is evaluated first. A surviving grant in any applicable canonical domain permits the action, subject to ceilings and operation-specific restrictions.

Do not compile workspace/global grants into every project as a workaround. Do not use one reserved `global` domain for resources that actually belong to distinct workspaces.

Exact resource shares are resource-bound rather than container-role assignments. Where an exact direct share is intended to survive project/workspace moves, prefer a stable exact-object policy in `*`:

```text
p, <user-or-team-principal>, *, flow/<flow-id>, <action>
```

This remains safe because the object ID is exact and globally canonical; it must never become `p, principal, *, flow/*, ...` unless the canonical source itself is truly global authority.

Project inheritance remains project-scoped and does not use this exact-resource rule.

### 5.5 Team membership and resource access

A team share must not compile into one user-resource policy per member.

For every **active user** who is a member of an **active, valid team**:

```text
g, <user>, team/<team-id>
```

A team is valid for resource access only when its canonical runtime invariants are satisfied, including at least one active Team Admin for an active team.

All active members receive team-shared resource access regardless of whether their management role is `admin`, `maintainer`, or `user`. Team role controls management authority, not membership in the resource-sharing principal.

Therefore promoting/demoting an active member among `admin` / `maintainer` / `user` must not itself grant or revoke the team's resource shares.

Membership alone grants nothing until a `p` rule targets that team principal.

### 5.6 Team-management authorization uses the same enforcer

Team `admin`, `maintainer`, and `user` remain management roles, not resource permission levels.

When Casbin is selected, team-management allow/deny decisions must also come from the same Casbin enforcer.

Prefer direct policy compilation per active membership rather than introducing another role manager:

```text
canonical membership role
        |
        v
explicit team-operation p rules for that user/team
```

The application first resolves the exact team, target member, current target role, requested new role, source/provenance, and whether the operation concerns an ordinary or privileged member. This is canonical request classification, not authorization.

The selected enforcer then decides the corresponding canonical team operation.

Examples of policy-level distinctions that must remain enforceable:

- Team User: roster read only;
- Maintainer: add/remove ordinary `user` members only;
- Team Admin: permitted team metadata and privileged membership/role operations;
- Platform Admin: existing configured platform authority path;
- cross-team operations: deny.

Transactional invariants remain outside Casbin and can still reject an otherwise authorized operation, including final-member/final-active-admin protection and source-managed mutation restrictions.

Do not retain `team_operation_allowed()` as the production policy decision after Casbin adoption; it may remain only as test/reference code during replacement and must be removed/retired from the active runtime path before completion.

### 5.7 Direct shares and project inheritance

Compile `AuthzShare` as directly as practical because its canonical meaning is already:

```text
principal + resource + permission
```

Direct user share:

```text
p, <user>, *, <exact-resource>, <explicit-action>
```

Direct team share:

```text
p, team/<team-id>, *, <exact-resource>, <explicit-action>
```

Project share compiles two distinct projections:

1. exact access to the project object itself;
2. child-flow policy in the canonical `project:<project-id>` domain.

For a project share:

```text
p, <principal>, *, project/<project-id>, <project-action>
p, <principal>, project:<project-id>, flow/*, <child-action>
```

Do not create one child policy row per workflow. Future direct child workflows inherit automatically because authorization uses the project domain plus `flow/*`.

A moved workflow immediately evaluates under its new canonical domain chain. Direct exact-resource shares continue to apply independently; inherited project access stops/starts according to the new project.

A direct workflow share does not grant parent project access or sibling access.

### 5.8 `flow:create` is an explicit policy action

Creation inside another user's shared/scoped project must not be inferred later from generic project `write` in application code.

When a project grant/role canonically permits creation of child flows, compile `create` explicitly on the project-domain flow collection:

```text
p, <principal>, project:<project-id>, flow/*, create
```

For the existing share mapping, editable project access produces the explicit child actions required by the current product contract, including `create` when write-level project access authorizes child creation and excluding child `delete` where the contract does not grant collaborator-owned child deletion.

The application remains responsible for canonical destination resolution, deriving the authenticated creator as owner, assigning the generated ID, workspace/project fields, and validating the resulting mutation.

Personal/intrinsic creation that the existing Langflow contract grants to an active user for a resource the server will own to that same user may remain a canonical application semantic inside `BaseAuthorizationService`; it must not be implemented as a broad global role merely to avoid the absence of a pre-existing object ID.

### 5.9 Ownership, Platform Admin, and share administration

Do not introduce a Team Owner role or duplicate normal resource ownership into Casbin.

Canonical ownership remains:

```text
Flow.user_id
Folder.user_id
```

Preserve the ordering:

1. authenticate and resolve active principal;
2. apply narrower credential/external ceiling;
3. apply configured Platform Admin/superuser semantics where allowed;
4. apply canonical resource-owner semantics where the route/resource contract permits;
5. evaluate the Casbin policy engine for scoped roles/team/share authority;
6. apply operation-specific owner-only/manage restrictions and invariants;
7. deny if no path remains.

Resource `write` does not imply share administration. Owner/platform semantics may authorize share management directly; any non-owner scoped share-management permission must come through the same selected enforcer, not a separate Python permission evaluator.

Do not generate ordinary Casbin policies merely to imitate `User.is_superuser` or canonical resource ownership.

Personal workspaces remain part of Langflow's existing resource/workspace model; never model them as teams-of-one.

### 5.10 Share/action semantics are explicit and bounded

Keep the canonical permission vocabulary:

| Stored permission | Effective share actions |
|---|---|
| `read` | `read` |
| `execute` | `read`, `execute` |
| `write` | `read`, `write`, `execute` |
| `admin` | `read`, `write`, `execute`, `delete` where supported |

The UI continues to offer only:

- Can use -> `execute`
- Can edit -> `write`

Do not rewrite existing `read` or `admin` grants.

Never compile normal `admin` as `act="*"`. Expand every permission to explicit currently supported actions. Newly introduced future actions are denied until the canonical permission mapping explicitly includes them.

This feature remains additive allow-union policy plus existing credential/external ceilings. Do not add explicit deny, priority policy effects, ordered deny rules, or `eft` semantics as part of this contribution.

### 5.11 Matcher safety

Domain matching is always literal.

If `keyMatch2` or an equivalent path matcher is used internally for compact object patterns:

- only use normalized slash-safe internal object values such as `flow/<uuid>` and `flow/*`;
- never feed canonical colon-scoped domain strings into path matching;
- keep canonical external object/domain syntax unchanged;
- prove root-versus-subtree behavior explicitly;
- prove cross-project/cross-workspace/cross-team negatives;
- prove split-format keys fail closed rather than widen access.

---

## 6. Canonical-to-Casbin compilation and consistency contract

This section applies only if Casbin is selected.

### 6.1 Deterministic compiler

Create one deterministic compiler from canonical Langflow authorization state to derived Casbin rules.

It must be:

- idempotent;
- order-stable;
- rebuildable;
- testable without HTTP;
- independent of frontend state;
- minimal: emit only facts needed by the selected model;
- incapable of inventing users, resources, roles, teams, ownership, or scopes absent from canonical state;
- incapable of introducing Team Owner, personal-team, team-rooted resource-container, wildcard-action, or duplicate-policy authority semantics.

### 6.2 Canonical compiler inputs

Compile only from canonical, validated state:

- active users where relevant;
- `AuthzRole` and parent relationships;
- `AuthzRoleAssignment` plus surviving provenance;
- active/valid `AuthzTeam`;
- `AuthzTeamMember` plus canonical user activation state;
- `AuthzShare`;
- canonical project/workspace/resource relationships required to derive domains and project inheritance;
- current explicit action vocabularies/mappings.

Ownership may be read as canonical evaluation context, but ordinary `Flow.user_id` / `Folder.user_id` ownership is not copied into a synthetic ownership role.

Do not compile from JWT permission claims, frontend capability state, browser caches, audit history, stale saved graph metadata, or request-supplied owner/domain identifiers.

### 6.3 Derived representation rules

`casbin_rule` is derived/rebuildable only.

Required invariants:

- no independent Casbin-policy CRUD API/UI;
- no manual policy row authoring as intended durable access;
- no migration that transfers canonical authority from `authz_*` to `casbin_rule`;
- deterministic full rebuild restores equivalent policy;
- role hierarchy is flattened from canonical roles unless a tested requirement proves another representation is necessary;
- team membership relationship exists only for active users in active valid teams;
- all active team roles participate equally in the team resource-sharing principal;
- team-management policy is explicit and separate from resource-share policy;
- workspace/project/global scopes remain distinct;
- no blanket reserved `global` domain replaces actual workspace domains;
- no per-child workflow policy fanout for project inheritance;
- no per-member-per-resource fanout for team shares;
- no `act="*"` for normal share/admin or flattened role permissions;
- no Team Owner role or personal-workspace-to-team conversion.

### 6.4 Atomic canonical + derived policy mutation

Authorization correctness must not depend on best-effort post-commit policy refresh.

For every policy-relevant mutation, canonical state and the required derived `casbin_rule` changes are staged in the **same database transaction**:

```text
BEGIN
    mutate canonical authz/resource state
    validate canonical invariants
    compile affected derived policy
    stage casbin_rule changes
    stage required mutation audit
COMMIT
```

If required derived compilation/persistence fails, the canonical policy mutation fails/rolls back.

Reuse existing framework-neutral transaction-stage lifecycle hooks where their public contracts already cover the mutation. For share mutations, add only the smallest backward-compatible framework-neutral transaction-stage snapshot/hook if the existing contract cannot stage share-derived policy safely before commit.

Post-commit hooks may invalidate an optimization cache or publish compatibility notifications, but they are not the authorization correctness boundary.

Apply this to:

- role create/update/delete;
- role assignment create/delete/reconciliation;
- team create/update/delete;
- membership add/remove/role change;
- team activation/suspension/retirement;
- user disable/delete where policy changes;
- share create/update/delete;
- project/resource moves that change inherited derived policy when required;
- lifecycle cleanup.

### 6.5 Freshness and revocation

A newly admitted request after commit must observe committed policy on every worker without waiting for TTL, message delivery, or process restart.

For this contribution, prefer request/admission-scoped or otherwise strictly fresh loading of the relevant committed derived policy, reusing one loaded enforcer within `batch_enforce()` for that admission.

Do not treat share/resource `revision` fields as a global authorization-policy generation. They remain optimistic-concurrency metadata for their canonical records.

Do not add a long-lived positive authorization cache whose correctness depends on a revision/epoch protocol as part of this contribution. A future policy-generation cache may be added only through a separately reviewed design; if introduced later, generation checking is an optimization over already-atomic canonical/derived state, never the source of truth.

No effective authorization is embedded in long-lived JWT claims or saved resource objects.

### 6.6 Lifecycle synchronization

Derived membership, team-management, scoped-role, and share policies must track canonical lifecycle deterministically.

Dedicated tests must prove that:

- disabling/deleting a user removes their effective derived team/role access;
- removing team membership removes the `user -> team` relationship;
- team role changes update only management policy and do not alter team-shared resource membership while the user remains active;
- suspending/invalidating a team removes its effective team-principal resource access;
- role assignment/provenance removal preserves surviving canonical grants and removes only the affected derived policy;
- resource/project moves update inherited policy semantics without reviving stale project grants;
- rebuild from empty `casbin_rule` produces equivalent decisions.

The lifecycle requirement does not authorize synthetic ownership roles or duplicated canonical grants.

### 6.7 Readiness and rebuild

Provide operator-safe verification/rebuild functionality only if Casbin is selected.

Required behavior:

- verify canonical schema and team invariants first;
- validate/compare derived policy deterministically;
- rebuild only `casbin_rule`, never canonical grants;
- fail closed when enforcement is configured and derived policy cannot be loaded/validated;
- do not silently fall back to the retired native evaluator.

A rebuild tool is repair/verification functionality, not a second runtime evaluator.

---

## 7. Current native evaluator treatment

Until Casbin is adopted, retain the current evaluator.

If Casbin is adopted:

### 7.1 `service.py`

Keep `BaseAuthorizationService` behavior and public method contracts.

Replace the internal scoped-role/team/share policy-decision core while preserving canonical resource/owner/domain resolution and public method contracts.

Do not change route callers to know about Casbin.

### 7.2 `repository.py`

Keep:

- canonical user/resource loaders;
- owner/project/workspace resolution;
- bounded SQL access;
- resource registry;
- visibility-support queries where they remain non-authoritative candidate prefilters.

Remove or stop using any `effective_access*` implementation as a competing final permission evaluator.

### 7.3 `policy.py`

While the native evaluator remains selected, keep the existing pure policy helpers used by that single implementation.

If Casbin is adopted:

Keep only non-Casbin domain/invariant helpers that are not competing authorization decisions, including:

- team role vocabulary;
- team roster validation;
- invariant error types;
- pure normalization/constants needed by mutation validation.

Move/remove runtime authorization decisions that Casbin now owns, including:

- team-operation allow/deny decisions;
- scoped-role/role-assignment allow/deny decisions;
- share-level action expansion used as the final permission decision;
- project-share inheritance and child-create expansion used as the final permission decision.

The canonical permission/action mapping must have one authoritative definition for compilation/tests. It must not remain executable in parallel as a second production policy engine.


### 7.4 Visibility

`get_resource_visibility()` and list prefilters must not become a divergent policy engine.

Allowed approaches:

- derive exact visibility from the same compiled policy representation; or
- produce a conservative candidate scope and post-filter with the one active `batch_enforce()`.

Never let a broader SQL prefilter become the final authorization decision merely for performance.

---

## 8. Team contract

### 8.1 Roles

Each membership has exactly one team-scoped role:

- `admin`
- `maintainer`
- `user`

Never map these values to `User.is_superuser`.

### 8.2 Team management matrix

| Operation | Platform Admin | Team Admin | Maintainer | User |
|---|---:|---:|---:|---:|
| Create team | Yes | No | No | No |
| Delete team | Yes | No | No | No |
| List all teams | Yes | No | No | No |
| Read own team/roster | Yes | Yes | Yes | Yes |
| Rename/describe own team | Yes | Yes | No | No |
| Add ordinary user | Yes | Yes | Yes | No |
| Remove ordinary user | Yes | Yes | Yes | No |
| Assign Admin/Maintainer | Yes | Yes | No | No |
| Change/remove privileged member | Yes | Yes, invariant-bound | No | No |
| Activate/deactivate team | Yes | No | No | No |
| Change external directory binding | Yes | No | No | No |

### 8.3 Invariants

Every committed team must:

- contain at least one member;
- if active, contain at least one active Team Admin.

All writers must enforce the final-state invariant transactionally.

Manual removal/demotion of the final active Team Admin is rejected.

Security-driven account disablement or authoritative source removal is not blocked merely to preserve an Admin; instead suspend/retire the affected team according to the existing lifecycle contract.

### 8.4 Provenance

Manual operations must not forge or overwrite authoritative membership provenance.

Source-managed membership removal remains source-controlled.

A local team-management role on a source-managed membership ends if the authoritative membership ends.

---

## 9. Resource sharing contract

### 9.1 Recipients

Targeted project/workflow shares support:

- active existing user;
- active valid team.

No non-user email invitation is introduced.

### 9.2 Modes

New UI:

```text
Can use  -> execute
Can edit -> write
```

No `editable` boolean is persisted.

### 9.3 Share administration

Resource share administration is separate from edit access.

A normal editor may not create/update/delete another owner's grants.

Share administration must resolve the canonical resource owner and scope server-side.

### 9.4 Inheritance

Project shares:

- apply to current direct child workflows;
- apply to future direct child workflows;
- stop applying when a workflow moves out;
- begin applying when an authorized workflow moves in;
- do not create child share rows.

Direct workflow shares:

- do not expose parent project;
- do not expose siblings;
- remain valid independently of project visibility.

### 9.5 Overlapping grants

Effective access is the union of surviving applicable grants after upper-bound ceilings.

Examples:

| State | Effective result |
|---|---|
| direct execute + team write | write |
| direct execute + inherited project write | write |
| direct share removed, team write survives | write survives |
| team membership removed, owned flow remains | ownership survives |
| no ownership/grant | denied/hidden |

The UI must explain surviving access sources without exposing private resource metadata.

---

## 10. Ownership and protected operations

### 10.1 Ownership

Keep:

- `Flow.user_id` = authenticated creator/owner;
- `Folder.user_id` = project owner.

A workflow created inside another user's editable shared project remains owned by its authenticated creator.

Removing a share/team membership does not transfer or erase ownership.

### 10.2 Ordinary editable content

A non-owner editor may modify permitted content such as:

- name;
- description;
- graph data;
- tags;
- icons/display metadata;
- nodes/edges within graph rules.

### 10.3 Separately controlled operations

`write` does not automatically grant:

- ownership transfer;
- `user_id` change;
- arbitrary `folder_id` / `workspace_id` change;
- publication/access-type change;
- endpoint/publication identity changes;
- MCP/A2A/public exposure changes;
- authentication settings;
- resource lock bypass;
- deletion;
- reshare;
- moving another user's workflow;
- using another user's credentials/provider account.

Apply restrictions to effective changes, including derived publication state.

---

## 11. Concurrency

Keep current optimistic revision semantics.

### 11.1 Flow/project

Use `edit_revision`.

Under the collaboration contract:

- read returns current revision/ETag;
- update/delete requires matching observed revision;
- missing required precondition → `428`;
- stale precondition → `412`;
- successful effective change increments revision once;
- no-op does not increment;
- stale payload is never automatically replayed.

### 11.2 Share

Use share `revision`.

- stale permission update/delete → `412`;
- duplicate create remains `409`;
- no implicit upsert/escalation.

### 11.3 Authorization ordering

Authorize before disclosing current revision to an unauthorized caller.

A stale editor that has also lost permission receives the authorization-safe result required by the route contract, without leaking newer protected state.

---

## 12. Execution identity and dependency isolation

### 12.1 Authenticated shared execution

The authenticated recipient remains the execution principal.

Sharing a workflow does not delegate:

- owner's identity;
- owner's API keys;
- owner's variables;
- owner's files;
- owner's provider account;
- owner's private dependencies;
- owner's sessions/history.

### 12.2 Dependency failures

Flow authorization and dependency availability are separate.

If the recipient cannot access a required dependency, fail safely rather than falling back to the owner.

### 12.3 Runtime families

Preserve the existing route-family matrix.

Targeted shares must not silently widen:

- legacy/project MCP;
- webhook admission;
- protected A2A;
- historical jobs/messages/sessions;
- provider/deployment credentials.

Existing public entry points retain their dedicated public-principal contract.

---

## 13. Public and anonymous access

Targeted user/team sharing is not publication.

Do not modify public state when targeted shares change.

Public anonymous requests continue through the explicit public-principal authorization seam.

Never make anonymous requests inherit authenticated owner/team/share semantics.

If the selected authorization implementation cannot safely resolve the public domain/tenant contract, fail closed rather than widening access.

---

## 14. API contract

Preserve existing API families.

### 14.1 Teams

Continue using:

`/api/v1/authz/teams`

including membership-role operations already implemented in the fork.

### 14.2 Shares

Continue using:

`/api/v1/authz/shares`

No new share API version.

### 14.3 Permissions/capabilities

Continue using the existing effective-permission/capability surfaces.

Frontend controls are advisory projections of server decisions, never the authorization source.

### 14.4 Recipient search

Keep recipient lookup bounded and resource/team-management scoped.

Do not open the general user directory to ordinary users.

---

## 15. Frontend contract

Keep the existing implemented UI architecture.

### 15.1 Teams

One platform administration Teams surface plus one team-scoped management surface.

Reuse common components and server-derived capabilities.

### 15.2 Sharing

Use one reusable flow/project Share dialog through existing extension/menu locations.

Show:

- User/Team recipient;
- Can use / Can edit;
- existing grants;
- inherited/surviving access explanations;
- stale/revoked state.

Do not add:

- public-link management into this dialog;
- non-user invitation flow;
- third UI permission mode.

### 15.3 Permission state

When authorization is enabled:

- unresolved/error state is not allow;
- controls remain disabled until capabilities resolve;
- backend remains authoritative.

On `412`, preserve unsaved local graph and stop automatic save retries.

On revocation, stop mutations and preserve unsaved local work locally.

---

## 16. Data model and migrations

Preserve the current canonical schema work unless an actual defect is found.

Existing feature fields include:

- team membership role/timestamps/checks/indexes;
- team inactivation reason;
- share revision/timestamp;
- flow/project edit revision;
- existing `casbin_rule` table.

Do not:

- add another membership table;
- add another share table;
- add a second canonical policy table;
- persist an `editable` boolean;
- copy grants to children/team members;
- edit already-published upstream migrations.

If Casbin adoption requires only the existing `casbin_rule` schema, do not create a migration merely to mark the architectural change.

Add indexes only when justified by measured filtered-policy loading/query needs.

---

## 17. Audit and transaction rules

### 17.1 Mutation audit

Keep authorization mutation audit in the canonical transaction where required.

A required mutation audit failure must roll back that mutation.

### 17.2 Decision audit

Decision-audit durability remains governed by the existing configuration.

Capability reads are not mutation events.

### 17.3 Casbin-specific rule

If Casbin is adopted, compilation/persistence of derived policy for a canonical authorization mutation is part of correctness, not best-effort telemetry.

Do not report success if canonical authorization changed but required derived rules failed to update.

---

## 18. Readiness and failure behavior

When enforcement is configured:

- service resolution failure is not equivalent to disabled authorization;
- canonical-policy read failure denies/fails unavailable;
- invalid team state prevents collaboration readiness;
- Casbin load/compile failure, if Casbin is adopted, denies/fails unavailable;
- no error path falls back to allow-all or to a retired evaluator.

`AUTHZ_ENABLED=false` may preserve the established non-enforcing compatibility behavior, but only when the server positively establishes that configuration.

A settings/readiness error cannot select the disabled contract.

---

## 19. Current implementation inventory and change discipline

Treat the current branch as an integrated implementation. Before any additional architecture change, inspect and preserve the actual canonical modules rather than creating replacements.

Key backend policy/runtime modules currently include:

- `src/backend/base/langflow/services/authorization/service.py`
- `src/backend/base/langflow/services/authorization/repository.py`
- `src/backend/base/langflow/services/authorization/policy.py`
- `src/backend/base/langflow/services/authorization/guards.py`
- `src/backend/base/langflow/services/authorization/team_management.py`
- `src/backend/base/langflow/services/authorization/share_management.py`
- `src/backend/base/langflow/services/authorization/collaboration.py`
- `src/backend/base/langflow/services/authorization/concurrency.py`
- `src/backend/base/langflow/services/authorization/lifecycle.py`
- `src/backend/base/langflow/services/authorization/audit.py`
- `src/backend/base/langflow/services/authorization/fetch.py`

Canonical API/data surfaces include:

- `src/backend/base/langflow/api/v1/authz_teams.py`
- `src/backend/base/langflow/api/v1/authz_shares.py`
- `src/backend/base/langflow/api/v1/authz_me.py`
- `src/backend/base/langflow/api/v1/authz_capabilities.py`
- `src/backend/base/langflow/api/v1/authz_recipients.py`
- `src/backend/base/langflow/services/database/models/auth/authz.py`
- flow/project models and revision-aware mutation helpers
- migration `bf6c22022777`

Framework-neutral contract:

- `src/lfx/src/lfx/services/authorization/base.py`

Frontend/user surfaces include the existing Teams page, team management components, Shared With Me view, reusable Share dialog, permissions context/query hooks, revision-aware save hooks, and current menu extension points.

Verification surfaces include the real-service backend authorization matrix, the eight authz Playwright journeys, route/principal matrices, inherited backend/LFX/frontend regression suites, migration checks, and fork CI wiring.

Rules:

- extend these canonical modules where needed;
- do not create “CasbinV2”, `authorization_v2`, a new route family, or a second frontend permission store;
- if a new compiler/model module is required after Casbin selection, place it inside the **one selected authorization implementation package** and remove/retire the superseded runtime decision logic;
- do not add dependencies or files merely to preserve an unused alternative architecture.

---

## 20. Testing strategy

### 20.1 Regression baseline

Treat the current validated native implementation as the behavioral baseline.

Any architecture replacement must retain the already validated:

- team-role behavior;
- sharing modes;
- inherited project access;
- direct-flow privacy;
- owner/creator semantics;
- concurrency;
- revocation;
- execution principal;
- external-access ceiling;
- public/transport boundaries;
- UI controls;
- eight connected E2E journeys.

### 20.2 If Casbin is not adopted

Do not add Casbin-only dependencies/tests to the production branch. Continue using the current real-service tests and existing CI acceptance.

### 20.3 If Casbin is adopted

Replace native-evaluator acceptance with the actual selected **Python Casbin-backed production enforcer**. Community Go/Casbin assertion suites are useful model-design evidence only; they do not count as Langflow implementation acceptance.

Required focused acceptance includes:

1. deterministic canonical -> Casbin compilation and rebuild;
2. canonical subject/domain/object/action normalization;
3. literal project/workspace/global domain-chain evaluation;
4. workspace roles never cross workspaces;
5. project roles never cross projects;
6. global roles apply only where canonically global;
7. `AuthzRoleAssignment` parent-role flattening, cycle detection, depth bound, and explicit wildcard-action expansion;
8. surviving assignment provenance/removal behavior;
9. Team Admin/Maintainer/User management authorization through the one Casbin enforcer;
10. target/new-role classification plus final-state team invariants;
11. all active team roles receive team-shared resource access equally;
12. team membership alone grants no resource access;
13. team role change does not add/remove team-shared resource access while active membership survives;
14. direct user share;
15. direct team share without per-member/per-resource fanout;
16. exact direct share survives resource/project moves where the canonical share is resource-bound;
17. dynamic project -> flow inheritance with no child policy fanout;
18. explicit `flow:create` on editable project access;
19. project share does not grant child delete unless explicitly supported by the contract;
20. direct flow share without parent/sibling exposure;
21. bounded share-level action mapping; `admin` never grants unspecified/future actions;
22. overlapping grants / allow-union behavior;
23. canonical ownership remains equivalent with no Team Owner/ownership policy;
24. Platform Admin/superuser and narrower credential/external ceiling ordering;
25. share-management authority does not derive from ordinary resource `write`;
26. inactive/invalid team exclusion;
27. user disable/delete removes effective derived access;
28. role/team/share revoke leaves no stale derived relationship;
29. canonical + derived policy staging failure rolls back the canonical authorization mutation;
30. share-policy transaction-stage failure rolls back the canonical share mutation;
31. two independent service instances observe committed revocation on the next admission;
32. request/batch enforcement equivalence;
33. visibility-prefilter/final-enforce equivalence;
34. public-principal behavior remains separate;
35. personal workspace behavior remains unchanged and is not modeled as a team;
36. SQLite and PostgreSQL behavior;
37. no paid/external model-provider dependency in core authorization acceptance;
38. if `keyMatch2` or equivalent matching is used internally: cross-project/workspace/team leakage, identifier parsing, split-format, and root-versus-subtree negatives;
39. no unnecessary additional Casbin relationship manager/resource-role layer is needed for the accepted model.

### 20.4 No production dual-run

A temporary test harness may compare native expected outcomes to Casbin outcomes during development.

Do not ship dual execution, shadow decisions, native fallback, Casbin fallback, or runtime comparison logging. The replacement is complete only when the superseded native policy decision path is removed from the active runtime.

### 20.5 Existing connected E2E journeys

The eight connected browser journeys remain mandatory:

1. Platform Admin creates/manages team and role boundaries.
2. Direct Can use share: read/run, no edit.
3. Upgrade to Can edit: permitted save.
4. Team project share: inherited current/future workflows.
5. Membership removal/team suspension: new requests lose access.
6. Downgrade while editor open: save denied, local content retained.
7. Concurrent editors: stale save rejected.
8. Direct flow share: parent/siblings remain private.

Run with distinct users, `LANGFLOW_AUTO_LOGIN=false`, the actual selected production authorization implementation, no permission-policy mocks, and zero retries for feature acceptance.

---

## 21. CI and quality

Preserve the current fork CI integration and all applicable inherited Langflow checks.

At minimum:

- authorization backend matrix;
- SQLite;
- PostgreSQL 16;
- supported Python versions required by the workflow;
- backend regression;
- LFX regression;
- frontend Jest;
- authz Playwright;
- inherited core Playwright;
- migration validation;
- CI scripts/matrices;
- Ruff/Biome/pre-commit/secret checks;
- scoped typing plus existing full-project comparison reporting;
- documentation build/accessibility;
- candidate Docker/ARM64 validation where selected.

Do not:

- weaken coverage;
- add blanket skips/xfails;
- hide failed tests behind reporting failures;
- replace real enforcer tests with `_policy_double.py`;
- change `CI Success` semantics to ignore feature jobs;
- treat collection-only as execution;
- treat a released upstream package/image as validation of the fork candidate.

If Casbin adds dependencies, validate packaging in every distribution that actually imports the implementation. Do not add Casbin to `lfx` unless the framework-neutral package truly needs it.

---

## 22. Work packages from current state

These are sequential refinements of one implementation, not parallel versions.

### WP-01 — Rebaseline and preserve current behavior

- Treat `waqoor/langflow` as the sole fork destination.
- Record current fork/head/migration/CI evidence.
- Inspect current diff and instructions before edits.
- Preserve the already validated feature behavior.

**Done when:** plan, code, verification record, and repository state describe the same implementation.

### WP-02 — Resolve upstream enforcement packaging

- Keep the current native evaluator active while packaging is unresolved.
- Use authoritative maintainer feedback and current Langflow authorization contracts to select one final packaging.
- Treat community Casbin model/test work as design evidence, not authority or implementation proof.
- Do not add production Casbin code until one packaging direction is selected.

**Done when:** one packaging direction is selected or the current native fork remains the final implementation; no branch contains two feature enforcers.

### WP-03 — Final Casbin model proof, only if selected

- Use the minimal `sub/dom/obj/act` model with literal domains.
- Prove project -> workspace -> `*` domain-chain behavior.
- Prove direct exact-resource shares, dynamic project inheritance, and explicit `flow:create`.
- Prove active team membership, all-role resource-share equivalence, and team-management authorization through the same enforcer.
- Prove flattened scoped `AuthzRoleAssignment` semantics including parent roles and wildcard permission expansion.
- Prove no Team Owner, no personal-workspace-as-team, no wildcard admin, no unnecessary relationship manager, and no path-matcher leakage.
- Reproduce the accepted model semantics using the actual selected Python Casbin package.

**Done when:** focused model tests demonstrate the smallest sufficient model against the complete Langflow authorization semantics before production replacement.

### WP-04 — Single-engine Casbin replacement, only if selected

- Add Casbin/adapter dependencies only at the package layer owning the selected enforcer; keep LFX framework-neutral unless it truly imports them.
- Implement one deterministic compiler from canonical Langflow state.
- Compile scoped roles, team-management policies, team membership, user/team shares, project inheritance, and explicit child-create policy.
- Preserve canonical owner/superuser/ceiling/invariant semantics outside synthetic policy relationships.
- Use one Casbin enforcer for all policy-based decisions.
- Remove/retire `effective_access*`, `team_operation_allowed()`, native role/share/team decision logic, and any other competing final evaluator from the active path.

**Done when:** exactly one production policy decision engine remains and route/UI callers remain engine-agnostic.

### WP-05 — Atomic derived-policy consistency, only if selected

- Reuse current transaction-stage lifecycle hooks where they already cover the mutation.
- Add only the minimal backward-compatible share transaction-stage contract needed for share-derived policy.
- Stage canonical mutation, derived `casbin_rule`, and required mutation audit in one transaction.
- Use strictly fresh/request-scoped derived policy for new admissions; do not depend on revision-driven cache correctness.
- Ensure next-request revocation across independent workers.
- Add deterministic rebuild/readiness behavior.

**Done when:** no successful canonical mutation can leave stale derived authorization for a newly admitted request.

### WP-06 — Full regression verification

- Run the final selected production enforcer through the real-service authorization matrix.
- Run all eight browser journeys with distinct users, `LANGFLOW_AUTO_LOGIN=false`, and zero feature retries.
- Run SQLite/PostgreSQL authorization and transaction coverage.
- Run applicable inherited backend/LFX/frontend/docs/container CI and route/principal matrix checks.
- Fix attributable defects without broadening scope or weakening tests.

**Done when:** final-SHA evidence is recorded with no false-green classification.

### WP-07 — Documentation and delivery reconciliation

Update only affected authorization/authentication/sharing documentation, `.env.example`, endpoint/principal matrices, verification evidence, and PR description.

Document the final packaging, canonical source of truth, domain chain, minimal Casbin representation if selected, scoped-role flattening, team-role/resource-share separation, explicit child-create semantics, revocation boundary, team invariants, ownership/dependency isolation, and inherited limitations.

**Done when:** documentation, code, PR metadata, and verification evidence describe the exact same final implementation.

---

## 23. Definition of done

The final implementation must satisfy all of the following.

### Product

- [ ] Team creation is atomic and non-empty.
- [ ] Every active team has an active Team Admin.
- [ ] Admin/Maintainer/User remain team-scoped.
- [ ] Team roles never elevate platform superuser.
- [ ] Owners can share with existing users/teams.
- [ ] Can use / Can edit retain canonical execute/write mapping.
- [ ] Project inheritance is dynamic and has no child-grant fanout.
- [ ] Direct flow share does not expose parent/siblings.
- [ ] Creator ownership is retained.
- [ ] Editors cannot reshare/delete/transfer/publish unless separately authorized.
- [ ] Revocation/downgrade affects newly admitted requests.
- [ ] Stale writes cannot overwrite newer content.
- [ ] Shared execution keeps recipient principal/dependency boundaries.
- [ ] Public and owner-scoped transport exceptions remain intact.

### Architecture

- [ ] `authz_*` and canonical resource/user state remain the only writable authorization authority.
- [ ] `BaseAuthorizationService` remains the only application authorization boundary.
- [ ] Exactly one production policy evaluator is active.
- [ ] No V2/replacement authorization API, second policy store, parallel/shadow/canary/fallback path, or separate authorization microservice exists.
- [ ] If Casbin is used, `casbin_rule` is derived/rebuildable only.
- [ ] If Casbin is used, Langflow's explicit subject/domain/object/action contract remains intact.
- [ ] If Casbin is used, domains remain literal and canonical: project -> workspace -> `*`; no blanket `global` replacement for workspace domains.
- [ ] If Casbin is used, the model is the smallest sufficient representation and does not recreate Langflow as a second relationship graph.
- [ ] If Casbin is used, `AuthzRoleAssignment` and parent-role semantics are compiled/flattened into the same enforcer rather than left as a Python policy engine.
- [ ] If Casbin is used, team-management authorization and resource authorization are both decided by the one Casbin enforcer; transactional invariants remain Langflow logic.
- [ ] If Casbin is used, all active team roles participate equally in team-targeted resource sharing while role-specific management authority remains separate.
- [ ] If Casbin is used, project child `flow:create` is an explicit policy action rather than inferred from generic project write after enforcement.
- [ ] If Casbin is used, exact direct shares remain resource-bound and project inheritance remains project-domain-bound without policy fanout.
- [ ] If Casbin is used, canonical `Flow.user_id` / `Folder.user_id` ownership remains authoritative; no Team Owner or synthetic ownership policy is introduced.
- [ ] If Casbin is used, normal `admin` and role wildcards expand to explicit supported actions; no `act="*"` future authority exists.
- [ ] If Casbin is used, canonical + derived policy mutations are atomic and next-request correctness does not depend on revision/cache propagation.
- [ ] If Casbin is used, the old native role/share/team/scoped-role policy evaluators are removed from the active runtime path.
- [ ] If Casbin is not used, the current native evaluator remains the only enforcer and no dormant production Casbin dependency/path is added.

### Quality

- [ ] Final implementation passes the required real-service authorization matrix.
- [ ] All eight authz E2E journeys execute and pass.
- [ ] SQLite/PostgreSQL behavior is validated.
- [ ] Applicable inherited backend/LFX/frontend/docs/container checks remain intact.
- [ ] No required check is converted to false-green by skip/continue-on-error/reporting behavior.
- [ ] Documentation and PR status match the exact final implementation.

---

## 24. Explicitly forbidden implementation choices

Do not introduce any of the following:

- second canonical policy source or direct independent authoring of `casbin_rule`;
- native + Casbin runtime dual evaluation, fallback, runtime selector, shadowing, or canary;
- V2 authorization API or separate authorization microservice;
- Redis/JWT/resource-object authorization state as source of truth;
- competing Python policy evaluators after Casbin adoption, including active `team_operation_allowed()`, role-assignment evaluation, or `effective_access*` final decisions;
- replacing Langflow's explicit domain model with team-rooted hierarchical resource paths;
- collapsing distinct workspace scopes into one reserved `global` domain;
- compiling workspace/global role grants into every project as policy fanout;
- unnecessary `g2`/`g3`/additional Casbin role-manager, ReBAC, or intermediate resource-role layers without acceptance-test evidence that the simpler model is insufficient;
- per-child workflow policy/share rows for project inheritance;
- per-member-per-resource policy/share fanout for team sharing;
- making only the `user` team role receive resource shares; active Admin/Maintainer/User memberships all represent team membership for resource sharing;
- synthetic Team Owner roles or duplicated resource ownership relationships;
- treating personal workspaces as teams-of-one;
- inferring shared-project `flow:create` from generic project `write` after the policy decision instead of explicit create policy;
- compiling normal `admin` or persisted role wildcard permissions to `act="*"` or unspecified future authority;
- explicit-deny/priority semantics introduced only for this contribution;
- revision/epoch-driven stale-cache correctness without atomic canonical + derived persistence;
- long-lived positive policy caches as a new correctness dependency;
- copied workflows/credentials as an authorization mechanism;
- team role -> `is_superuser` mapping;
- resource `write` -> implicit share/publication/ownership-transfer authority;
- caller-supplied domain/owner/team identity as authorization authority;
- automatic stale-save replay;
- arbitrary legacy-team admin promotion;
- broad test skips/xfails/coverage reductions;
- production approval/authority/staging/canary/shadow systems;
- copying or recreating unavailable Enterprise implementation code instead of using public Langflow contracts.

---

## 25. Source and evidence baseline

### Current fork

- Repository: `https://github.com/waqoor/langflow`
- Feature branch: `feat/auth-team-sharing`
- Branch head reviewed for this revision: `63215eccf8c06b291567e25fb5772bf9e90bab52`
- Validated implementation candidate recorded by the branch verification document: `39e0d87ca7187739a3f105200dae67afd7eaf097`
- Verification record: `docs/auth-team-sharing-verification.md`
- Merged PR: `https://github.com/waqoor/langflow/pull/1` (merged September 5, 2026, 13:01:03 UTC)

### Upstream

- Repository: `https://github.com/langflow-ai/langflow`
- Main reviewed: `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`
- Upstream architecture guidance: `AGENTS.md`
- OSS authorization foundations: PR `#13153`
- Current release-1.12 RBAC foundations/Enterprise-Casbin alignment evidence: PR `#14215`
- Share-policy contract alignment: PR `#14293`
- Related collaborative-access issue: `#1864`
- Current enhancement issue: `#14932`

### Final review evidence

The final review used:

- the current generated revision-1.3 plan as the document baseline;
- `waqoor/langflow` feature branch `feat/auth-team-sharing` at `63215eccf8c06b291567e25fb5772bf9e90bab52`;
- `waqoor/langflow:main` and upstream `langflow-ai/langflow:main` at `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`;
- the current fork verification record showing candidate `39e0d87ca7187739a3f105200dae67afd7eaf097` and successful final scoped acceptance evidence;
- upstream `AGENTS.md` authorization guidance;
- upstream PR `#13153` (OSS authorization foundations / pass-through + plugin split);
- upstream PR `#14215` (release-1.12 OSS foundations consumed by Enterprise Casbin enforcement);
- upstream PR `#14293` (share-level contract alignment to Enterprise enforcement);
- issue `#14932` and its successive community Casbin model sketches, including the later domain-scoped 90-assertion model as design evidence only.

Community model/test results do not change the packaging decision by themselves. They are design evidence; final acceptance requires the selected Python implementation and Langflow real-service/E2E verification.

### Architecture interpretation

The authoritative current distinction is:

```text
Langflow application/API
        |
        v
BaseAuthorizationService
        |
        +--> current upstream OSS default: pass-through
        |
        +--> registered enforcement implementation: real policy
```

The fork currently replaces the OSS pass-through body with native enforcement.

This plan preserves the fork's current implementation until the packaging decision is resolved, and permits Casbin only as a clean single-engine replacement. It does not authorize introducing Casbin as an additional evaluator.

---

**Revision 1.6 outcome:** this plan integrates the final architecture decisions from the domain-scoped Casbin review without expanding product scope. If Casbin is selected, one minimal enforcer owns scoped-role, team-management, membership/share, and project-inheritance policy decisions; Langflow retains canonical identity/resource/domain/ownership semantics, credential ceilings, invariants, concurrency, and lifecycle facts. Existing `AuthzRoleAssignment` hierarchy is flattened during deterministic compilation; canonical domains are evaluated as project -> workspace -> `*`; team shares reach every active member regardless of management role; editable project access compiles explicit child `flow:create`; canonical and derived policy mutate atomically; and request correctness never depends on revision-driven cache propagation. No V2, competing scope, parallel/fallback evaluator, staging, shadow, canary, second policy authority, Team Owner, blanket global workspace domain, wildcard future authority, or relationship-graph proliferation is authorized. No code, branch, PR, migration, repository setting, or deployment is changed by this document revision.