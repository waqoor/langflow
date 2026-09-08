# Authentication, Authorization, Teams, and Resource Sharing — Implementation Plan

**Document revision:** 1.7  
**Revision date:** September 7, 2026  
**Source document:** `auth_share_implementation_plan_updated_latest 002(1).md`, Revision 1.6  
**Implementation repository:** `waqoor/langflow`  
**Existing contribution branch:** `feat/auth-team-sharing`  
**Fork delivery target:** `waqoor/langflow:main`  
**Upstream reference:** `langflow-ai/langflow`  
**Related issue:** `langflow-ai/langflow#14932`

**Selected technical design:** one optional, registered, in-process Casbin-backed `BaseAuthorizationService` implementation within the existing Langflow backend package. This is a replacement of the native policy-decision core, not an additional evaluator.

**Decision status:** the contributor has selected this design. Upstream maintainer acceptance of production adoption and source-tree packaging is **not established by the supplied evidence**. The existing requirement for that acceptance is not silently waived by this document. The native implementation remains the deployed baseline until the approved, fully validated replacement is ready; there is no native/Casbin runtime selector.

**Validation status:** the supplied records describe a validated native implementation and a contributor-reported standalone Casbin assertion suite. The combined registered Langflow–Casbin implementation, transaction store, and E2E suite have **not** been executed or validated by this plan revision. All new acceptance criteria remain unverified until supported by final-candidate evidence.

### Recorded baseline — historical identifiers, not a fresh branch-head claim

| Item | Identifier recorded by Revision 1.6 |
|---|---|
| Fork `main` after PR #1 | `e4ae38be2636f2532053eeee3ebcb19ea08cc406` |
| Original fork/upstream baseline | `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5` |
| Feature branch head | `63215eccf8c06b291567e25fb5772bf9e90bab52` |
| Validated native code candidate | `39e0d87ca7187739a3f105200dae67afd7eaf097` |
| Existing feature migration | `bf6c22022777`; down revision `c6d8e0f2a4b7`; phase `MIGRATE` |
| Historical fork PR | `waqoor/langflow#1`, recorded as merged September 5, 2026, 13:01:03 UTC |

Re-resolve actual branch heads, migrations, and repository instructions before implementation. Do not reset newer work to these identifiers or relabel historical native test results as Casbin results. [P1]

### How to read this revision

- Sections 1–3 preserve the contribution boundary and explain baseline versus target.
- Section 4 selects packaging and responsibility boundaries; it no longer offers two production packaging implementations.
- Sections 5–7 specify the model, compiler, consistency protocol, and native retirement.
- Sections 8–18 retain the product/API/UI contracts and add only necessary integration clarifications.
- Section 19 assigns concrete code integration points; Sections 20–23 define implementation, verification, and completion.
- Sections 24–25 record prohibitions, provenance, and evidence limitations.

Requirement text is normative for this contribution. Historical observations and externally verified technical facts are identified separately in Section 25. New module names and new hook names are explicitly proposals, not claims that those symbols already exist.

---

## 1. Purpose and non-negotiable contribution boundary

Preserve the already implemented team-based RBAC and project/workflow sharing feature while replacing its native policy evaluator with the selected registered Casbin implementation when the production-adoption prerequisite is satisfied.

The original plan is already implemented. This is a focused integration and alignment round, not a restart, feature expansion, authentication redesign, or general Langflow refactor. The existing product remains the behavioral baseline. [P1]

The feature must continue to provide:

- Platform-admin team creation and lifecycle management; team-scoped `admin`, `maintainer`, and `user` roles.
- Non-empty initial membership and active-Team-Admin invariants.
- Sharing projects/workflows with existing users or teams; **Can use → `execute`**, **Can edit → `write`**.
- Dynamic inheritance to current/future direct child workflows, without copied grants.
- Direct workflow access without revealing its private parent or siblings.
- Creator ownership, authenticated-recipient execution, and private-dependency isolation.
- Committed revocation/downgrade applying to new admissions, plus optimistic collaboration revisions.
- Agreement between API decisions, runtime admission, lists, capability responses, and UI controls.

### 1.1 Scope is an acceptance condition

This is a contribution to an upstream repository the contributor does not own. Unnecessary changes risk rejection of the entire contribution.

Every production, dependency, test, configuration, schema, documentation, or CI change must implement a specific requirement in this document or repair a regression directly caused by that implementation. Use the smallest correct change consistent with existing Langflow conventions.

Do not:

- repair unrelated defects, reformat unrelated files, upgrade unrelated dependencies, or refactor adjacent modules opportunistically;
- introduce speculative abstractions, generic relationship frameworks, new tenancy, new resource ownership, extra sharing modes, or unrelated security/deployment systems;
- broaden the eight product E2E journeys into new product scenarios;
- rewrite the plan or weaken a contract merely to make the contributor's fixture pass;
- erase another agent's or the user's changes during scope cleanup.

Trace each meaningful change to the relevant section during implementation. Before completion, remove only your own unjustified changes. Record material out-of-scope blockers briefly without implementing unrelated fixes.

### 1.2 Clarify “no parallel” and “no staging”

Two coding agents may work concurrently on non-overlapping files. That does not authorize parallel runtime implementations, selectable policy engines, V2 APIs, shadow evaluation, canaries, or staged alternative architectures.

“Transaction staging” in this document means adding canonical/derived/audit changes to the **same database transaction before commit**. It is mandatory database correctness, not a staging deployment or approval system.

---

## 2. Baseline, selected target, and evidence status

### 2.1 Preserve the native feature baseline

Revision 1.6 records an integrated implementation covering database migration, authorization, team/share APIs, project/workflow enforcement, collaboration revisions, UI, tests, CI, and documentation. Its verification ledger reports SQLite/PostgreSQL 16 authorization coverage, Python 3.10/3.14 coverage, eight connected authorization journeys, frontend Jest, and inherited checks on identified native candidates. These are historical results, with their recorded limitations; they are not new Casbin evidence. [P1]

Inspect current code and repository instructions before editing. Preserve completed behavior, IDs, migrations, API error contracts, authentication/session behavior, and execution identity. Do not recreate finished features or reset the branch.

### 2.2 Current and target responsibility maps

Recorded baseline:

```text
authentication / canonical request resolution / credential ceilings
    -> existing guards and BaseAuthorizationService
    -> native role/share/team policy decisions
    -> operation restrictions / revisions / mutation or execution
```

Selected replacement:

```text
existing Langflow guards and application callers
    -> ONE registered CasbinAuthorizationService (BaseAuthorizationService)
       -> canonical active identity, resource, destination, and applicable scopes
       -> unchanged owner/platform semantics and narrower credential ceilings
       -> ONE Casbin policy engine for scoped roles, team operations, and shares
       -> operation-specific restrictions and transactional invariants
    -> existing application mutation/execution paths
```

Policy construction, separately from the call direction:

```text
canonical authz_* + relevant canonical user/resource state
    -> deterministic compiler
    -> transaction-owned reconciliation into existing casbin_rule
    -> fresh, immutable-per-admission policy snapshot
    -> Casbin allow/deny decisions inside the selected service
```

These diagrams distinguish data flow from call flow. Routes call the authorization service, not Casbin followed by the service.

### 2.3 Upstream alignment versus contributor selection

At the recorded upstream baseline, Langflow documents a framework-neutral authorization interface, a default pass-through implementation, route guards, canonical `authz_*` tables, and compiled `casbin_rule` storage. LFX exposes configuration-based registration under `authorization_service`. [R1, R2]

This revision selects that registered-service architecture for the contribution. It does not assert that upstream has accepted adding this particular optional implementation, changing its default distribution, or merging the contribution.

The default OSS stub and the registered enforcing service are different deployment configurations of the existing extension contract. They must not be used as two evaluators or a fallback chain within the enabled collaboration configuration.

### 2.4 Accepted decisions and resolved review issues

| ID | Selected decision |
|---|---|
| D01 | Registered, in-process backend Casbin implementation; optional dependency; no new monorepo package or service registry. |
| D02 | One four-field request, literal domain equality, exact actions, one grouping relation, constrained internal object matching. |
| D03 | Canonical role inheritance flattened with role/assignment scope intersection and explicit permission expansion. |
| D04 | Team sharing membership and exact-team management authority use separate principal meanings through the same `g`. |
| D05 | Creation stays `flow:*` plus `create` in the canonical destination domain. |
| D06 | Canonical writes, derived reconciliation, and required audit commit together under one writer-ordering protocol. |
| D07 | PostgreSQL transaction-level advisory writer lock; SQLite early write transaction; coherent, fresh admission snapshots. |
| D08 | Capabilities, lists, counts, summaries, and mutations use the same selected policy meaning; no residual Python evaluator. |
| D09 | Suspension removes team-resource authority without indiscriminately erasing existing management/repair access. |
| D10 | Native historical CI and community standalone assertions do not constitute combined implementation acceptance. |

### 2.5 Community contribution status

The supplied response reports 368 corresponding assertions in Go Casbin v2.135.0 and Python Casbin 1.43.0, including mutation tests. It explicitly states that database atomicity and the real Langflow service/E2E matrix were not run. The supplied material is prose and excerpts, not the full executable compiler and fixtures. Treat those counts as contributor-reported model evidence only. [P2]

Request a reviewable contribution with the actual model, compiler, fixture, Python tests, source revision, and required provenance through the existing GitHub contribution process. Do not authorize direct writes to the working branch merely because the response reports passing tests. Do not introduce a Go runtime or new Go CI requirement into Langflow for this work.

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

### 3.6 Selected implementation and immutable application contracts

The target has one registered Casbin policy implementation and no retained native role/share/team/scoped-role evaluator. Framework-neutral default stubs remain only for the existing non-enforcing compatibility configuration; a failed selected plugin must never switch to one.

“One enforcer” means one engine/model and decision procedure, not one mutable process-global policy instance. Separate request-scoped enforcer instances loaded from coherent snapshots are expected; they are not competing implementations.

Canonical owner/platform rules, credential ceilings, and domain invariants remain in their established Langflow boundaries. They must not become a second evaluator for scoped roles, shares, or team-management permissions.

### 3.7 No new authority through compilation

Internal principal prefixes, finite operation encodings, transaction locks, and request snapshots are implementation details. None may create new user-facing permission scopes, a team-to-workspace ownership relationship, an additional authority table, or a role-management API.

Unknown actions, malformed identities, invalid scopes, unsupported public contracts, and unresolved canonical context never become global access.

---

## 4. Selected packaging and adoption decision

### 4.1 Decision status — technical selection is complete; upstream acceptance is separate

The contributor has selected **registered, in-process Casbin packaging**. Do not reopen native-versus-plugin implementation alternatives inside this plan or build both.

The supplied evidence does not establish the maintainer acceptance required by Revision 1.6 for production adoption. Therefore:

1. Retain the current native implementation as the deployed baseline while that prerequisite is unresolved.
2. Model/compiler review and isolated tests may proceed without adding a production engine, dependency, selector, or alternate deployment path.
3. Record authoritative maintainer feedback concerning the registered implementation's source-tree/distribution placement before production integration/cutover under this contribution.
4. Once accepted, implement the single target described below and run its combined acceptance. Replace, rather than retain, the native policy core.
5. Do not describe a native-only delivery as completion of this selected Casbin replacement, or historical native CI as validation of it.

This is a contribution/acceptance distinction, not authorization to build an approval service, authority gate, staged deployment, or runtime switching system. If maintainers choose a materially different direction, reconcile this document explicitly; agents must not silently implement another architecture.

### 4.2 Concrete package location

Place the enforcing implementation under the existing `langflow-base` backend package:

```text
src/backend/base/langflow/services/authorization/
    service.py                  # existing default service, restored to approved OSS semantics
    repository.py               # shared canonical loaders, not a native policy fallback
    policy.py                   # shared vocabulary/mappings/invariants, not final role decisions
    team_management.py          # canonical team transactions and invariant validation
    share_management.py         # canonical share transactions
    lifecycle.py                # existing framework-neutral lifecycle delegation
    casbin/                     # PROPOSED implementation subpackage
        __init__.py
        service.py              # PROPOSED CasbinAuthorizationService
        compiler.py             # PROPOSED pure canonical-state compiler
        store.py                # PROPOSED async DB/session and policy loading integration
        model.conf              # ONE packaged model
```

These new paths are the selected proposed layout, not existing files. Reuse an equivalent canonical module if current code already provides it. Add no duplicate repository/resource registry, separate distribution, microservice, sidecar, or generic adapter registry.

`compiler.py` operates on immutable validated snapshots, not HTTP requests or frontend state. `store.py` uses the existing database model/session layer. `service.py` implements the authorization contract and holds no long-lived positive-permission cache.

### 4.3 Registration and optional dependency

Use the existing deployment configuration, not a new engine-selection flag:

```toml
# Proposed value in the existing lfx.toml service configuration.
# This path becomes usable only after the implementation is installed and validated.
[services]
authorization_service = "langflow.services.authorization.casbin.service:CasbinAuthorizationService"
```

Retain `LANGFLOW_AUTHZ_ENABLED` and all existing settings semantics. Installation and service selection are distinct: installing an optional dependency must not automatically replace the OSS service in every deployment. Configuration-based registration is already supported by LFX. [R2]

Declare the Python Casbin dependency in the existing backend package's optional dependency mechanism; choose and document one appropriately named extra using project conventions. Do not add it to LFX, make it unconditional in unrelated distributions, register it through a global import side effect, or introduce a competing entry-point registration that overrides the explicit configuration.

PyCasbin is the Python implementation; the referenced Python distribution/import is `casbin`. The reported `1.43.0` fixture version is a reproduction reference, not automatic acceptance of a production pin. Resolve a compatible version through the repository's normal dependency/security process, record the exact locked version, and test supported Python/package combinations. No unrelated dependency upgrades are authorized. [T4]

Include `model.conf` in built wheels and source distributions, and load it via package resources rather than relying on the checkout's current working directory. No deployment-authorable policy CSV or model editor is introduced; CSV is a test fixture only.

### 4.4 Default compatibility and selected-plugin failure

Without the optional plugin selected, preserve the upstream-approved default pass-through behavior and owner-scoped fetch protections. Do not enable cross-user collaboration merely because `LANGFLOW_AUTHZ_ENABLED=true` while only the default stub is present. [R1]

When the collaboration configuration explicitly selects the Casbin implementation, missing dependencies, missing model data, constructor failures, misresolved service selection, unavailable canonical schema, or unusable policy must fail readiness and protected collaboration admission. Do not accept a default stub as proof that the selected plugin loaded.

Verify resolved service selection and required collaboration capabilities through the existing factory/service manager and readiness surfaces. If the discovery layer's warning-and-skip behavior can silently substitute a default, make only the smallest authorization-specific validation correction; do not redesign general discovery semantics for unrelated services. The expected selection must come from the trusted deployment configuration, not a client parameter.

The existing native evaluator is not retained as a safety fallback. Readiness failures do not imply authorization is disabled.

### 4.5 Application, compiler, and enforcer responsibilities

| Boundary | Responsibility | Not permitted |
|---|---|---|
| Authentication/guards | Resolve verified caller and credential ceilings; preserve existing owner/platform/public exceptions and audit contracts. | Trust client identity/scope; treat failed enforcement as disabled. |
| Canonical loaders | Resolve active user, resource, owner, destination, project/workspace, membership, and mutation classification. | Decide scoped-role/share/team allow/deny independently. |
| Compiler | Turn canonical grants, scope restrictions, role mappings, and membership into finite `p`/`g` facts. | Invent ownership, tenancy, policy precedence, or new actions. |
| Casbin service | Evaluate all scoped-role/share/team policy, including policy-derived share management, through one model. | Call a native fallback, expose Casbin to routes, or return stale capabilities. |
| Domain transactions | Enforce roster/provenance/revision/ownership-bound field invariants and stage canonical/derived/audit writes. | Let a successful policy check override an invalid resulting state. |
| Frontend | Display server-derived capabilities and preserve unsaved content on rejection. | Become a policy authority or infer access from team labels. |

### 4.6 Retirement is part of the replacement

Move enforcing responsibilities into the selected implementation, restore default OSS semantics only at the approved compatibility boundary, and remove superseded native policy paths from the delivered runtime. Do not leave dormant engine files merely to make rollback selectable. Use ordinary version-control history for the historical implementation; runtime dual evaluation and shadow comparison are forbidden.

---

## 5. Selected policy model and canonical semantics

These requirements define the replacement target after Section 4's adoption prerequisite. They do not authorize an alternative runtime alongside native enforcement.

### 5.1 Request and identity normalization

Preserve Langflow's framework-neutral request meaning:

```text
subject = user:<uuid>                  # derived from the verified caller/user_id
 domain = project:<uuid> | workspace:<uuid> | *
 object = flow:<uuid> | project:<uuid> | flow:* | other existing resource syntax
 action = existing resource action, e.g. read / write / create / execute / delete
```

The actual service method may continue accepting `user_id: UUID`; it derives the subject rather than adding a new API argument. Maintain all existing public signatures and context/error conventions unless a minimal default-compatible transaction context extension is demonstrably required.

The compiler and enforcer share one normalization definition. Internal objects use validated `<resource-type>/<uuid>` and permitted collection patterns such as `flow/*`; domains remain canonical colon-form scope values. Bare UUID subjects and prefixed subjects must not be mixed accidentally.

Only server-resolved context determines ownership, resource type/ID, project, workspace, destination, membership, and applicable domain chain. Reject malformed resource types, UUIDs, inconsistent containment, unknown actions, and unsupported scope types without widening authority. A truly unscoped resource is different from a failed scope lookup.

### 5.2 One minimal model

The selected candidate model is:

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
m = (r.sub == p.sub || g(r.sub, p.sub)) && r.dom == p.dom && keyMatch2(r.obj, p.obj) && r.act == p.act
```

Keep `keyMatch2` only behind the constrained object grammar in Section 5.11. The schema's default allow effect does not authorize explicit deny/priority columns or independently authored policy.

Use the existing `g` for two disjoint principal meanings:

```text
user:<U> -> team/<T>                     # eligible resource-sharing membership
user:<U> -> team-role/<T>/<role>          # exact-team management membership
```

No edges link a team-management principal to a team-sharing principal, an owner, or an application role. No team nesting or role hierarchy is recreated through transitive grouping. The compiler emits only direct user-to-team or user-to-team-role links.

Compile scoped application-role permissions and direct user shares directly to `p`. Team shares target `team/<T>`; management policies target `team-role/<T>/<role>`. This uses one grouping mechanism, not one mechanism per canonical concept.

Do not simultaneously emit direct per-user and role-principal copies of the same team-management model. The selected representation is team-role principals; a different equivalent representation would require an explicit design correction, not a runtime alternative. No `g2`, ReBAC subsystem, resource editor/viewer intermediary, or synthetic ownership role is needed by the currently selected design.

### 5.3 Scoped application roles: flatten and intersect, never broaden

Compile `AuthzRole`, its parent chain, `AuthzRoleAssignment`, and surviving assignment provenance from canonical state. Preserve the current assigned role's `workspace_id` restriction in addition to assignment scope. This restriction exists in the reviewed native evaluator and must not be lost. [R4]

The effective scope is the intersection of the assignment's permitted resources and the assigned role's canonical workspace restriction:

| Assignment | Assigned role restriction | Resulting policy scope |
|---|---|---|
| Valid global; no domain ID | None | `*` |
| Valid global; no domain ID | Workspace W | `workspace:W` |
| Workspace W | None or W | `workspace:W` |
| Workspace W1 | Workspace W2, W1 differs from W2 | No applicable grant |
| Project P | None | `project:P` |
| Project P | Workspace W containing P | `project:P`, retaining the canonical W restriction when context is resolved |
| Project P | Workspace not containing P | No applicable grant |
| Missing required scope ID, malformed combination, unsupported organization scope | Any | No widened grant; use the existing invalid-state/unsupported-scope behavior |

The global-to-workspace reduction above narrows an already restricted assignment; it must not be described as turning restricted authority into a new global policy.

Compiler rules:

- Traverse parents with the current cycle detection and depth bound; malformed/cyclic/over-depth inheritance does not grant permissions.
- Preserve the existing parent-role semantics. Do not add new inheritance restrictions on parent rows merely because the compiler reads them.
- Expand supported `<resource>:*` slugs into the current resource's finite action vocabulary. Emit no `act="*"`.
- Preserve concrete role permissions that differ from sharing levels. A `flow:write` role alone is not automatically a `flow:create` role; share-level expansion and role-permission expansion are separate canonical mappings.
- Resolve provenance using the existing manual/IdP survival rules, including any supported legacy assignments. Do not invent a new requirement that deletes valid legacy authority, and do not keep an assignment after its canonical effective lifetime ends.
- Sort inputs and normalized emitted tuples; deduplicate output. Database row order is not a deterministic contract.
- A role/assignment update, parent update, provenance reconciliation, or containment change that affects the intersection must reconcile the projection in the same mutation transaction.
- Canonical resource context must retain all scope restrictions when evaluating a request. Inconsistent resource/project/workspace rows must not bypass a role's workspace restriction.

Example, with normalized user identity:

```text
p, user:<U>, project:<P>, flow/*, read
p, user:<U>, project:<P>, flow/*, write
```

No runtime Python role traversal may grant access outside Casbin after replacement. Shared compiler helpers may still normalize roles and expand finite action sets; they are not a second request evaluator.

### 5.4 Canonical domain-chain evaluation

Resolve the chain from one coherent canonical snapshot:

```text
Project-contained resource: project:P -> workspace:W (when present) -> *
Workspace-scoped resource:  workspace:W -> *
Truly unscoped resource:    *
Exact team management:     * with an exact team/T object and team-specific principal
```

Use the same loaded enforcer for the applicable domains and union the valid grants after credential ceilings. A literal `*` is an explicit unscoped policy domain, not a string wildcard in the matcher. A `project:*` policy must not match all projects.

Do not copy workspace/global policies into each project. Do not collapse genuinely separate workspaces into `global`. Conversely, do not fabricate a workspace on currently personal/unscoped variables, files, or knowledge bases that have no such canonical field. Use each actual resource's registered resolver and preserve its existing ownership/publication boundaries. [R1, R4]

A project move or workflow move changes the chain immediately for later admissions. If it also changes compiled assignment restrictions, the mutation must reconcile policy under the writer protocol. Direct shares remain exact-resource grants as specified below.

### 5.5 Team resource membership and management membership

For resource sharing, emit `g, user:<U>, team/<T>` only when the user is active, canonical membership exists, and the team is active and valid, including the active-admin invariant.

All active `admin`, `maintainer`, and `user` members qualify equally. A role-only promotion/demotion among these values does not alter resource-sharing membership while the other eligibility conditions remain satisfied. Resource membership alone grants nothing until an applicable policy targets that team principal.

For management, emit `g, user:<U>, team-role/<T>/<role>` for the active canonical user's valid membership where the existing management contract permits that team to be managed. **Do not filter this relationship solely by team sharing eligibility.**

| Canonical condition | Team-resource relationship/policies | Team-management authority |
|---|---|---|
| Active user in active valid team | Eligible for all-role sharing | Exact-team role matrix |
| Active user in an inactive/suspended but existing team | No effective team-resource access | Preserve permitted inspection/management/repair operations; no new activation authority |
| Inactive user | No effective derived user/team/scoped-role access | No management allow |
| Removed membership or deleted/retired team | No surviving relationship for that membership/team | No role authority from the removed identity |
| Team unexpectedly invalid while active | No team-resource access; readiness handles invalid canonical state | Do not invent members/admins or silently rewrite state to repair it |

Suspension is not deletion. The reviewed fork distinguishes active recipient validity from management membership resolution. Preserve that behavior rather than deleting every management relationship for an inactive team. Platform-only activation/deletion operations remain platform-only. [R5]

### 5.6 Exact-team operation classification and finite actions

Teams are not resource containers and the reviewed `AuthzTeam` has no workspace/organization ownership field. Use an exact team object and team-specific management principal in `*`; do not add containment columns or infer a team's domain from shared resources. [R6]

The server loads the target member, current target role, requested new role, and provenance before classifying the operation. It validates allowed role strings first. These facts are not taken from a client-provided capability or actor-role claim.

Use finite internal actions compatible with existing route operations, for example:

| Existing operation | Internal policy action | Granted by team role |
|---|---|---|
| READ | `read` | Admin, Maintainer, User |
| UPDATE metadata | `update` | Admin |
| ADD_MEMBER, new role user | `add_member:user` | Admin, Maintainer |
| ADD_MEMBER, new role admin/maintainer | `add_member:admin`, `add_member:maintainer` | Admin |
| REMOVE_MEMBER, current role user | `remove_member:user` | Admin, Maintainer |
| REMOVE_MEMBER, current role admin/maintainer | `remove_member:admin`, `remove_member:maintainer` | Admin |
| CHANGE_ROLE | `change_role:<current-role>:<new-role>` for the finite validated role pairs | Admin |

These are private policy encodings, not new REST actions. Generate the finite valid set from one immutable mapping. A literal `change_role:*` is not an allowed shortcut under exact action equality. No-op updates keep their existing revision/audit behavior.

```text
g, user:<U>, team-role/<T>/maintainer
p, team-role/<T>/maintainer, *, team/<T>, read
p, team-role/<T>/maintainer, *, team/<T>, add_member:user
p, team-role/<T>/maintainer, *, team/<T>, remove_member:user
```

`CREATE`, `DELETE`, `LIST_ALL`, `SET_ACTIVE`, and `CHANGE_DIRECTORY_BINDING` remain canonical platform-administration operations, not grants to ordinary team roles. `LIST_ALL` means administrative enumeration of all teams; it does not prohibit the existing caller-scoped list of teams they may read.

Use the same selected service for mutation authorization and advertised team capabilities. The legacy `team_operation_allowed()` may inform characterization fixtures, but it must not remain the final runtime evaluator or be wrapped inside a custom Casbin matcher.

Roster validity, source-controlled membership, locking, and final-admin restrictions can reject an otherwise authorized mutation. They remain application invariants.

### 5.7 Direct shares and dynamic project inheritance

Use one direct compilation of `AuthzShare`, without editor/viewer role intermediaries or member/resource fanout:

```text
Direct user share:
p, user:<U>, *, flow/<F>, <explicit-supported-action>

Direct team share:
p, team/<T>, *, flow/<F>, <explicit-supported-action>

Project share:
p, <principal>, *, project/<P>, <supported-project-action>
p, <principal>, project:<P>, flow/*, <supported-inherited-child-action>
```

The exact `*`-domain resource share is stable across permitted moves because the object is exact; it does not bypass resource existence, current principal eligibility, scope validation, or protected-operation restrictions. Never widen it to a type wildcard unless the canonical source truly grants that broader scope.

Project shares cover current and future **direct** child workflows. They do not create child policy rows, expose siblings through a direct share, or create recursive folder inheritance. A moved flow loses old-project inheritance and gains new-project inheritance according to current canonical containment.

Filter direct user policies by active-user eligibility, and team share policies by eligible team state for resource sharing. Retain canonical grants as the lifecycle contract requires so reactivation can restore intended access; omitting derived access is not permission to delete canonical shares.

### 5.8 Creation stays `flow:*` plus `create`

Preserve the existing service/guard request:

```text
domain = project:<destination-project>
object = flow:*
action = create
```

Internally it maps to `flow/*` plus `create`. Compile explicit child creation only from canonical permissions that grant it:

```text
p, <principal>, project:<P>, flow/*, create
```

For editable project shares, use `project_flow_actions()`'s existing semantics at compilation: child read/write/execute as applicable, explicit create, and **no inherited child delete**. For scoped roles, preserve their actual `flow:create` permission rather than assuming generic project/flow write grants create.

Do not introduce `project/<P>` plus `flow:create` as a second policy shape or translate generic project write into create after enforcement. The contributor's fixtures must be corrected to the existing Langflow contract. [R7]

The application resolves and validates destination/ownership before authorization; no missing object ID can enable owner override based on a caller-supplied future owner. Existing container-owner creation semantics and personal intrinsic creation remain canonical application behavior where explicitly supported.

### 5.9 Owner, platform, credential, and share-management boundaries

Keep the existing ordering and route-specific exceptions:

1. Resolve the active authenticated principal and trusted credential context.
2. Enforce narrower external/API-key ceilings before any owner or superuser allow.
3. Apply configured platform-superuser and canonical owner semantics where the existing contract permits.
4. Evaluate scoped-role/team/share policy through Casbin.
5. Enforce protected-field, publication, destination, lifecycle, and revision restrictions before mutation.
6. Deny if no valid authority remains; preserve existing privacy-safe error mapping.

Owner/Platform Admin checks are not synthetic Casbin roles and do not authorize bypassing credential ceilings. Do not build a general ABAC system for `Flow.user_id` / `Folder.user_id`.

Share administration remains separate from resource write. Canonical owner/platform authorization may remain application semantics. **Policy-derived** non-owner `share:<action>` authority is compiled and evaluated by the same service. Preserve existing access-summary/self-read behavior through the same resource decisions; do not restore an independent role evaluator in share management or capability helpers.

PUBLIC shares stay on the existing explicit public-principal path. Targeted shares must not make public resources discoverable in authenticated lists or let an anonymous caller inherit an authenticated principal. Do not introduce another engine to implement the public exception.

### 5.10 Explicit action sets and additive grants

| Stored share level | Expansion, intersected with supported actions of the resource |
|---|---|
| `read` | `read` |
| `execute` | `read`, `execute` |
| `write` | `read`, `write`, `execute` |
| `admin` | `read`, `write`, `execute`, `delete` where supported |

Project child permissions use their separate existing mapping: no inherited child delete, and child creation where editable access grants it. A project-object delete permission does not bypass complete-set authorization of child deletion or other route restrictions.

The UI still exposes only Can use/Can edit. Preserve existing read/admin API values. No `act="*"`, implicit publication/reshare/ownership transfer, future-action allowance, explicit deny, priority ordering, or new `eft` policy authority is added.

Role permission wildcards are expanded only to the finite supported vocabulary at compilation. Any later change to that vocabulary must follow the ordinary explicit project change/test process; it is not a reason to add speculative actions now.

### 5.11 Matcher and grammar safety

Keep literal domain equality and exact action equality. For every loaded/emitted policy row:

- Validate user/team/team-role principal kinds and canonical IDs; reject collisions and malformed prefixes.
- Restrict internal resource objects to a registered resource type plus a canonical UUID, or an explicitly allowed type collection wildcard.
- Allow `flow/*` and other required existing type collections only at their intended scope; reject arbitrary path parameters, regex fragments, recursive wildcards, client-defined patterns, or team-rooted project paths.
- Canonical `flow:<uuid>` is accepted at the service boundary and translated once. It must not reach `keyMatch2` unnormalized.
- Permit collection-shaped **requests** only for existing server-classified collection/create operations, never as a client-selected replacement for a concrete lookup.
- Reject malformed derived rows rather than silently broadening or switching to native evaluation.

Test cross-project/workspace/team denials, root/subtree behavior, mixed formats, direct versus collection objects, unknown actions, and principal-role collisions. The model file alone does not prove these loader/compiler boundary checks.

---

## 6. Compiler, transaction-owned persistence, and consistency

### 6.1 One deterministic compiler

Implement one pure compiler over immutable canonical-state snapshots. Its output is a sorted, deduplicated set of normalized rule tuples. The same canonical input, current mappings, and model version produce the same semantic tuples regardless of SQL row order.

Required input includes active users; all canonical teams needed to distinguish management from sharing eligibility; memberships; roles and parent relationships; role workspace restrictions; assignments and provenance; shares; and relevant canonical resource/containment state. Do not discard inactive teams before deciding whether legitimate management access survives.

Keep graph content, secrets, credentials, browser state, JWT permission claims, historic audit results, and request-supplied ownership out of compiler input. Ownership can be read as canonical context but is not emitted as a synthetic ownership role.

Invalid canonical grants must follow the existing fail-closed semantics. Unknown or malformed permission values do not become allow-all. Unexpected compiler/storage failures abort the mutation; they must not produce a partial “best effort” policy set. Preserve the distinction between deliberately inert invalid grants and an incomplete/failed canonical read.

### 6.2 Existing `CasbinRule` is the only derived storage

Use the existing Alembic-owned `casbin_rule` model and table. Proposed slot mapping:

| Rule | `ptype` | `v0` | `v1` | `v2` | `v3` | `v4`, `v5` |
|---|---|---|---|---|---|---|
| Policy | `p` | subject | literal domain | normalized object/pattern | exact action | NULL |
| Group | `g` | canonical user subject | team or team-role principal | NULL | NULL | NULL |

Normalize unused slots consistently. Rule identity for reconciliation is the normalized semantic tuple, not the database-generated `id`. Validate field lengths/types and recognized policy/group types before loading.

No new canonical policy table, provenance-to-policy authority table, policy-generation column, migration solely to announce Casbin, or adapter-owned schema is authorized. Add an index only if measured query behavior justifies it through an ordinary forward-only migration.

Use one small `store.py` integration over the existing async session layer. A thin Casbin loader/adapter interface may be implemented there if required by the selected Python API; it must not own a second engine/session pool or transaction.

Disable Casbin AutoSave and any independent runtime `save_policy` persistence. Do not expose Casbin policy CRUD. In-memory population during a snapshot load is allowed; it must have no persistence side effect. Casbin's documented adapter persistence behavior must not be assumed to match Langflow transaction ownership. [T3]

### 6.3 Selected write strategy: complete computation, differential persistence

Initially compute the required complete policy set for each genuinely policy-relevant mutation and reconcile it atomically against stored rules:

```text
wanted = deterministic_compile(canonical_state_after_mutation)
stored = normalized_current_projection
insert = wanted - stored
delete = stored - wanted
```

Leave unchanged rules untouched. Resolve pre-existing duplicate derived rows deterministically without altering canonical grants. Multiple canonical sources yielding one policy row must remain allowed until the last applicable source disappears; set reconciliation naturally preserves that union.

This is one compiler and one persistence path, not a full-rebuild mode plus a separately implemented incremental engine. Operator rebuild uses the same compiler/reconciler. Do not unconditionally truncate/reinsert all policy rows, introduce an incremental dependency framework, or defer updates to a worker queue.

Compute once at the final canonical state of a logical batch wherever existing transaction orchestration permits. If existing lifecycle hooks invoke reconciliation more than once in the same transaction, keep it idempotent and ensure the last relevant write is covered. Do not postpone correctness into post-commit work just to save a compile.

Ordinary content-only graph saves, capability reads, and unrelated metadata updates do not trigger a full policy compile. A move, policy-relevant lifecycle transition, or deletion affecting the projection does. Measure the complete-computation cost before accepting production readiness; Section 20 defines the evidence. Performance failure is a scoped implementation issue, not permission to add stale caching or a second engine.

### 6.4 One ordered canonical/derived/audit transaction

The selected transaction sequence is:

```text
CALLER opens/owns the write transaction
    acquire authorization projection writer lock before authoritative compiler reads
    acquire existing entity locks in the repository's established order
    reload/revalidate active actor, authorization, affected scopes, and preconditions
    apply canonical mutation and validate final-state invariants
    flush canonical changes
    compile the required final projection from this transaction's state
    reconcile existing casbin_rule rows
    stage required canonical mutation audit
CALLER commits
```

Audit may be staged earlier inside the same transaction when current helpers already do so. The invariant is one all-or-nothing commit, not a new audit ordering framework.

The store/plugin must not commit, roll back, begin a nested independent transaction, call external services, or publish uncommitted policy to other requests. On failure it raises; the transaction owner rolls back. No success response is sent when required canonical, derived, or audit persistence failed.

Authorization for a policy-mutating request uses the valid **pre-mutation** authority under the ordered transaction; do not grant the caller permission using a role/share they are in the process of creating. A later legitimate operation in the same caller-owned transaction may use already-staged state only under the existing transaction contract.

Atomicity alone is not the concurrency guarantee. The selected design also requires complete writer participation and coherent admission reads. A full rebuild computed from an obsolete snapshot can otherwise restore revoked policy.

### 6.5 PostgreSQL writer ordering

Use one transaction-scoped advisory lock for the authorization projection in the relevant database/schema. Select one documented, deterministic lock identifier using existing repository conventions; do not use Python's randomized `hash()` or an attacker-controlled key.

Acquire it before policy-relevant canonical/compiler reads and before the existing user/team/resource locks. Every participating mutation, lifecycle writer, startup rebuild, and maintenance rebuild must follow this order. The lock is database-wide for this selected projection, not a newly invented tenant scope. Do not narrow it based on advisory `kind`/user IDs before canonical state is known.

Use a normal fresh Read Committed writer transaction with canonical reloads after acquiring the lock. Do not construct the compiler snapshot first and then wait for the lock; do not reuse a Repeatable Read snapshot established before the preceding writer committed. Clear/refresh stale ORM identity-map values as needed after waiting.

Preserve the existing inner entity lock order and bounded transaction-retry/error conventions. Use bounded lock waits; acquire no network/provider resources while holding the lock. A lock timeout must not fall back to unlocked policy writes.

PostgreSQL advisory locks coordinate only participating application code; transaction-scoped locks are released at transaction end. The writer inventory and tests, not the SQL primitive alone, establish coverage. [T1]

### 6.6 SQLite writer ordering

Establish the database write transaction before the compiler/invariant snapshot, using `BEGIN IMMEDIATE` or the repository's verified equivalent early-write mechanism. SQLite has one writer; `SELECT FOR UPDATE` must not be treated as its concurrency mechanism. [T2]

Integrate with the existing transaction owner. Do not issue a nested `BEGIN` after SQLAlchemy has already started a conflicting transaction, commit unrelated caller work to obtain a lock, or silently change global database behavior for other features.

If an existing deferred/read transaction or an authentication/JIT flow makes the early-write guarantee unavailable, use the existing whole-transaction retry/orchestration path to restart safely and reload canonical data; do not reuse a stale snapshot or silently upgrade it after a conflicting writer. Validate actual SQLite/aiosqlite transaction behavior on the supported runtime matrix. ORM transaction objects alone do not prove the database has established the intended read/write transaction. [T5]

Do not acquire writer ownership for read-only admission or capability discovery. Keep transactions short and use existing bounded busy/retry handling.

### 6.7 Required lifecycle hook integration

Existing public hooks include `acquire_identity_mutation_lock()` and `stage_identity_mutation()`. The former is lock-only and runs before canonical identity reads; the latter stages policy in the caller's transaction. They must retain their documented default-compatible behavior and signatures. [R3]

| Mutation family | Integration requirement |
|---|---|
| User activation/disable/delete; relevant identity changes | Existing early identity lock and stage hooks; cover active-user and downstream team effects. |
| Role, parent, workspace restriction, assignment, provenance | Existing identity transaction hooks where their event schema already applies; lock before reads and reconcile after final writes. |
| Team/membership/role/suspension/retirement | Existing team transactions plus identity hooks; cover bulk and lifecycle writers, not just one HTTP endpoint. |
| Share create/update/delete | Add the smallest framework-neutral early-lock and pre-commit staging contract missing from the existing share seam. |
| Resource/project moves or deletion affecting projection/role scope | Join the same writer ordering and final reconciliation at existing mutation orchestration; use a minimal explicit resource-policy hook only if the existing contract cannot represent the change. |
| Directory reconciliation and user/team cleanup | Reuse canonical ingestion/cleanup transactions and lifecycle hooks; never rely solely on post-commit broadcasts. |
| Rebuild/initialization | Same writer lock, snapshot, compiler, reconciliation, and caller-owned transaction as normal policy writes. |

For new hooks, proposed descriptive names such as `acquire_share_mutation_lock()` / `stage_share_mutation()` or their minimal resource-policy equivalents are **not existing API claims**. Final names must follow the reviewed framework-neutral contract. The semantics are mandatory: early lock, immutable mutation facts, caller-owned session, no commit, and no-op defaults for unaffected services/plugins.

Keep event/snapshot types in LFX free of Langflow ORM and Casbin imports. Do not overload identity or audit hooks with undocumented share/resource payloads. Do not trigger policy compilation recursively from `stage_audit_events()` or from every decision audit.

If required transaction-scoped enforcement cannot safely reuse the caller's session via existing service/context conventions, add only the smallest default-compatible internal context contract. Do not add a second authorization API, a concrete-session dependency to routes, or a mandatory Casbin method on unrelated plugins.

### 6.8 Writer inventory and retry correctness

Before replacement, enumerate all actual writers of the compiler's policy-relevant inputs in the existing verification record. Include HTTP/bulk routes, directory/JIT reconciliation, administrative user lifecycle, membership repair, role mutations, share cleanup, moves/deletes, initialization, and maintenance repair.

A writer outside the protocol is a blocker for the complete-reconciliation design. Apply only the minimal hook at the existing transaction boundary; do not redesign an unrelated subsystem. If a registered external writer cannot participate, document the unresolved integration boundary and do not claim global freshness.

All retries must reload state, reauthorize, and preserve the original client-observed revision requirement. Deadlock/serialization/busy retries are not permission to replay stale `412` content, ignore `428`, perform implicit upserts, or emit duplicate committed audit events. Recheck initial/new actor role and source provenance on retry.

Post-commit `sync_share`, invalidation, and legacy notification callbacks may remain for compatible observers, but cannot author policy from stale event snapshots. The selected plugin may make redundant notifications inert or reconcile current canonical state under the same protocol. Do not create a second post-commit writer that can overwrite a newer projection.

### 6.9 Fresh, coherent admission snapshots

Load active-user state, resource/destination scope, relevant group/policy rows, and policy-dependent response data from a coherent authorization snapshot. Reuse one immutable loaded enforcer for that admission's domain-chain checks and batch requests.

For PostgreSQL, use a short read-only Repeatable Read transaction for standalone multi-query authorization admission. Establish isolation before the relevant reads; the first snapshot must belong to this admission, not a prior request. Read Committed can expose different committed states to successive queries, whereas Repeatable Read provides a stable transaction snapshot. [T1]

For SQLite, establish a real read transaction covering the canonical and derived reads, using the actual driver's verified transaction behavior. Never use `BEGIN IMMEDIATE` for these read-only requests.

Important boundaries:

- New requests after a revocation commit take a new snapshot and observe the committed result on every worker.
- A request already admitted before that commit may finish according to the existing in-flight contract. This design does not introduce retroactive cancellation or an execution sandbox.
- Existing resumable/protected execution boundaries perform a new admission where the current route contract requires it; do not reuse a pre-revocation snapshot across them.
- Do not hold a read transaction throughout model/provider calls or long-running flow execution.
- For canonical write operations, reuse the caller's correctly ordered transaction and its appropriate in-transaction policy view; do not start an unrelated read-only transaction to authorize staged user/JIT/share state.
- Preserve authentication's existing shared-session behavior. A newly authenticated or JIT-created user must not disappear from authorization because a separate connection cannot see the caller's staged state.
- Async tasks must not share one `AsyncSession` concurrently; keep its reads sequential or use the repository's existing safe batching conventions.

SQLAlchemy isolation configuration and transaction ownership must be applied through the repository's session infrastructure, not changed after an incompatible transaction has begun or by altering the global engine default for the whole application. [T5]

### 6.10 Filtered policy loading and snapshot integrity

Use bounded async queries for the caller's direct policies, both kinds of grouping membership, applicable team-role/team policies, exact objects, type patterns, and required domain chain including `*`. Include all referenced group closure; filtering grouping rows only by the resource's project domain would incorrectly remove domain-independent team membership.

Load `g` and `p` from the same snapshot. A mixed load from two different committed policy states can create an allow that existed in neither state; test that interleaving explicitly. A lock or cache invalidation signal does not replace snapshot integrity.

Construct the enforcer only after the required load is complete. Never expose a partially built or mutable shared enforcer to concurrent requests. Loaded policy is discarded at the end of its admission. Immutable model metadata may be reused; permission decisions and positive grant caches may not persist across admissions.

Measure query counts and loaded rule counts for single/batch/list paths. No per-member/per-resource derived grants, full policy scan per row, or unbounded hidden N+1 query loops are acceptable shortcuts.

### 6.11 Rebuild, readiness, and recovery

Provide one operator-safe verify/rebuild path through existing command/startup conventions, backed by the same compiler, lock, and reconciler. The exact command name is to follow the repository; do not invent an unrelated operations framework.

Before enabling collaboration:

1. Verify expected service selection, optional package/model availability, canonical schema, and existing team invariants.
2. Establish ownership of this derived projection. Do not silently destroy policy belonging to an unknown/unavailable prior provider merely because it uses the same table; reconcile explicit provider replacement as part of the accepted adoption procedure.
3. Under the writer protocol, compare and initialize/reconcile required derived policy from current canonical state.
4. Validate the resulting model/rules and advertise collaboration readiness only after commit and successful load.

Multiple worker startups/rebuilds must converge safely and idempotently. A crash/failure before commit leaves the previous committed canonical/derived state, never an exposed half-populated table. An empty legitimate canonical grant set is different from a failed or incomplete load.

Rebuild modifies only the selected derived projection. It never grants itself platform authority, creates a Team Owner, auto-promotes legacy members, changes canonical ownership, or becomes an independently authorable policy source. Corrupt/unknown policy causes fail-closed behavior until an authorized repair succeeds.

### 6.12 No cache-generation correctness system

Share `revision` and resource `edit_revision` remain optimistic-concurrency metadata, not global policy epochs. Do not add long-lived enforcer caches, generation tables, Redis policy authority, watcher-dependent allow decisions, or TTL-based revocation for this contribution.

The selected correctness condition is:

```text
atomic canonical + derived + required audit writes
AND complete writer ordering
AND coherent, fresh admission reads
```

A later cache design is outside this contribution and cannot be introduced as an implementation convenience here.

---

## 7. Native retirement, service integration, and decision parity

### 7.1 Preserve the existing application service interface

Implement the selected service through `BaseAuthorizationService`, using existing dependency accessors/factories. Do not subclass the native service simply to retain its permission logic. Reuse canonical loaders and immutable context types instead.

The selected implementation must correctly cover `enforce()`, `batch_enforce()`, `get_effective_permissions()`, `list_visible_resource_ids()` / `get_resource_visibility()`, supported collaboration capabilities, relevant public-principal behavior, and required lifecycle contracts. Returned batch lengths/order and error semantics must remain compatible. [R3]

Restore `services/authorization/service.py` to the approved default stub semantics at replacement completion. Installing/selecting the new implementation must not leave both native and Casbin evaluators available as alternative feature engines.

### 7.2 Reuse repository facts; remove repository decisions

Keep canonical user/resource loaders, owner/project/workspace resolution, resource registry, bounded SQL access, and facts needed for visibility/policy compilation. Remove runtime dependencies on native `effective_access*`, role-permission evaluation, share-grant evaluation, and exact-visibility functions that independently decide access.

A query prefilter is not permission to retain a hidden native evaluator. All final policy eligibility comes from the same selected model. A helper may retain its name only if its implementation genuinely delegates to the selected service and does not reintroduce an alternative path; otherwise remove it and update its callers.

### 7.3 Keep invariants and compiler mappings; retire runtime policy helpers

Retain `validate_team_roster()`, vocabulary, invariant errors, normalization, finite share/role action maps, and existing mutation validation. One authoritative set of mappings may be used by compilation and independent expectation tests, but tests must not merely compute their expected answer through the exact production code under test.

Retire `team_operation_allowed()` as a production allow/deny function. Do not call it on each request through a Casbin custom function, or preserve `effective_access()` as a fallback when compiled policy is absent. Use version history or temporary isolated characterization tests for the old behavior; do not ship an unused duplicate native engine.

### 7.4 Move team capabilities and team mutations together

Update `require_team_operation()`, `team_actor_capabilities()`, `team_actor_capabilities_for_role()` and their route/capability consumers as necessary so role-derived answers come from the selected service. A role-only synchronous helper cannot remain the authoritative capability calculator. Batch appropriate exact-team operation probes without creating a new frontend contract.

Canonical platform-authority facts may remain the existing platform rule, with active-user and credential ceilings. Ordinary membership roles must be decided through the finite Casbin management policies. Roster/provenance/revision checks remain in `team_management.py`.

### 7.5 Share administration and access summaries

Keep canonical share writes in `share_management.py`, not the compiler. Replace any non-owner role-policy checks in share management, list scope helpers, or capability probes with the selected enforcer.

For summaries, load bounded canonical provenance and labels in the same authorized snapshot and tie them to the selected engine's allowed facts. Do not reconstruct an independent Python permission union to explain access. Do not add a second persistent explanation/permission model. Never reveal private parent labels, sibling metadata, or another recipient's private resource context through an explanation.

### 7.6 Visibility, pagination, and counts

Use the same compiled representation and canonical context for enforcement and visibility. Preserve owner visibility, active-user/credential limits, and public-list exceptions.

The initial correctness path may obtain a conservative candidate set and apply the selected enforcer in bounded batches. Authorization must occur **before** final pagination/count semantics. Do not fetch one unfiltered page, discard denied entries, and report its count as the authorized collection.

For exact totals, evaluate all relevant candidates or use an exact compiled-policy-derived scope query proven equivalent to enforcement. For cursor/streamed endpoints, preserve the existing contract while advancing only through authorized entries. Avoid unbounded resource loading solely for a performance shortcut; measure the actual list workload.

A compact SQL projection derived from the same finite policy representation is allowed where current visibility contracts support it, but it must not implement a divergent role/share engine. Test equal results between direct decisions, batches, effective permissions, list IDs/counts, and advertised capabilities on the same canonical snapshot.

### 7.7 Preserved guards and frontend boundaries

Route guards continue to resolve trusted context, apply ceilings, use the service, and map denials safely. They do not import Casbin or know model filenames. Cross-user fetch support remains gated by actual loaded service capabilities and readiness.

Keep the existing Teams surfaces, Share dialog, Shared With Me, query/hooks/store architecture, revision-aware saves, and server capability vocabulary. Any frontend change must be required by an actual plan-defined integration defect; no UI redesign or alternate client-side permission store is authorized.

### 7.8 Failure and session parity

Verify that permission probes, authenticated reads, writes, JIT login, public admission, batch checks, and background/resumable entry points retain their existing session/principal semantics. Do not lose the canonical caller, bypass external/API-key ceilings, leak current revisions on a denial, or report permission errors as authorization-disabled behavior.

Capability probes remain reads, not successful mutation audit events. Failed/unsupported service resolution must not advertise collaboration or return inherited allow-all behavior for the selected configuration.

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

### 8.5 Suspended-team management and all-role resource membership

Team sharing eligibility and team-management authority are separate. Active users retaining valid membership can continue the existing permitted inspection/management/repair behavior on an inactive team. This does not grant them activation, deletion, or directory-binding authority reserved to Platform Admins.

Remove effective resource-sharing relationships/policies for inactive or invalid teams, but do not indiscriminately remove their valid management relationships. Deleted/retired teams and removed memberships grant neither. Preserve the existing behavior of security-driven suspension and repair rather than inventing a new lifecycle.

Every active Admin/Maintainer/User receives the same applicable team-resource share while the team is eligible. Management-role-only changes do not alter that participation. An inactive user cannot benefit from either relationship.

`LIST_ALL` in the management matrix is the platform-wide administration operation, not the caller-scoped “my teams” list.

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

### 9.6 Derived policy versus canonical sharing

Direct exact-resource policies use stable object identities; inherited child policies use the actual project domain. Both preserve the same canonical `AuthzShare` row and existing permission level.

Omitting derived access for an ineligible user/team is not permission to delete an otherwise surviving canonical share. Reactivation/reconciliation follows the existing lifecycle contract. Shared-resource lists and access-source explanations must use the same decision snapshot without exposing unauthorized parent/sibling metadata.

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

### 10.4 Replacement must preserve complete-set operations

A project `admin` share can include supported project-object delete permission, but that policy fact alone does not authorize deleting other users' child workflows through a cascade. Preserve the existing complete-set deletion and owner-bound operation checks. No compiler projection may turn a container action into implicitly broader child authority.

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

### 11.4 Policy consistency is not an edit-revision system

`edit_revision` and share `revision` keep their existing object-level semantics. They are not used as policy-cache generations. Retry only retryable database conflicts through existing helpers, reload/reauthorize against current state, and retain the original observed revision so a stale save is still rejected.

After a role downgrade or membership revocation, a stale editor cannot use a previously successful capability response as authorization. The authoritative mutation check and any required resumable execution boundary perform current admission as defined in Section 6.

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

### 12.4 Snapshot lifetime does not extend through execution

Complete and release the authorization read snapshot before long-running provider/model operations. Preserve the same authenticated recipient and existing dependency boundaries. New protected/resumable admission boundaries reload policy; no long-lived in-memory grant from an earlier admission authorizes later requests.

This does not introduce a tenant execution sandbox, retroactive job cancellation, team-owned credentials, or delegated owner identity.

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

### 14.5 No API changes for the internal engine

Do not rename external subjects, domain/object values, route families, or action enums to match the contributor's standalone fixture. Slash normalization and finite team-operation strings are internal to the selected implementation.

Creation stays the existing flow collection action (`flow:*`, `create`) with server-resolved destination context. Share-administration capability probes and grant CRUD keep their distinct current contracts.

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

### 15.4 Capability and session correctness

After replacement, server capabilities are produced by the selected service, including team-management operations. Do not continue generating them through the retired native role helper.

Keep existing unresolved/error disabled states, unsaved-content preservation, account-switch/logout invalidation, and separate controls for write, share, move, publication, delete, and ownership. Only plan-attributable frontend corrections are in scope.

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

### 16.1 Packaging and schema boundaries

Reuse the existing `CasbinRule` model and columns. Adapters do not call `create_all()`, create another rule table, add their own engine, or run migrations during enforcement. No generation/cache-authority table or team workspace/organization ownership column is part of the selected design.

The optional backend dependency and packaged `model.conf` are distribution changes, not reasons to add a data migration. Any measured index change must follow the existing forward-only migration process and supported database checks.

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

### 17.4 Transaction and decision-audit placement

Mutation audit remains in the caller's canonical/derived transaction; compilation and audit failures roll the mutation back. Decision audits retain the existing durability/configuration contract and never masquerade as completed mutation events.

When standalone admission uses a read-only snapshot, preserve the decision result/context and use the existing audit path without attempting an incompatible write inside that read-only snapshot. Do not keep a SQLite read transaction open across an independent audit write if that creates a lock upgrade/deadlock. Mutation checks already inside a writer transaction use that transaction's existing audit conventions.

Capability probes produce no new mutation events and do not trigger policy reconciliation. `stage_audit_events()` must not become a hidden generic policy compiler hook.

---

## 18. Readiness and failure behavior

### 18.1 Preserve default OSS compatibility

An installation that deliberately uses the unchanged default OSS service keeps its existing behavior and owner-scoped fetch floor. Do not globally redefine `AUTHZ_ENABLED` for all unrelated services/plugins.

The pass-through default must not falsely advertise the selected team's sharing/enforcement capabilities. The optional Casbin implementation is not selected merely by installing its dependency.

### 18.2 Explicitly selected collaboration configuration

When the trusted configuration selects this implementation and enforcement is enabled:

- missing or failed plugin loading is not a successful default-service resolution;
- absent dependency or packaged model fails readiness;
- canonical state/schema/required invariant failure fails collaboration readiness;
- incomplete policy loading, malformed rules, compilation/storage failure, or inability to establish required consistency fails closed;
- no fallback to the native evaluator, default stub, stale cache, or “disabled” contract is allowed;
- cross-user fetch/capabilities become available only through the expected ready implementation;
- a timeout or rejected transaction is reported honestly and cannot produce a successful mutation response.

Use existing error/status conventions, with private resource details suppressed. A positively established disabled configuration is different from a settings error; only the former may preserve existing non-enforcing compatibility.

### 18.3 First initialization and repair

The selected service must verify/initialize its required derived projection through the ordered transaction path before reporting collaboration readiness. Startup and operator repair share one compiler/reconciler, and parallel worker startups must converge.

Normal requests do not repair canonical teams, create missing administrators, change grants, or run expensive full-policy rebuilds as an error fallback. A missing/invalid projection remains unavailable until the authorized initialization/repair succeeds.

---

## 19. Concrete integration inventory and change ownership

### 19.1 Existing and proposed modules

Paths in this table are relative to the repository root. “Existing” refers to the recorded implementation inventory; verify actual current locations before edits. “Proposed” is a selected new implementation location, not a claim that code already exists. [P1, R3–R8]

| Location | Status | Exact implementation responsibility |
|---|---|---|
| `src/backend/base/langflow/services/authorization/casbin/service.py` | Proposed | One registered `BaseAuthorizationService` implementation; canonical snapshot orchestration, Casbin decisions, batches, capabilities, visibility, relevant lifecycle overrides. |
| `.../authorization/casbin/compiler.py` | Proposed | Pure immutable-input compiler; role inheritance/scope intersection; team/resource relationship separation; finite actions; normalized deterministic tuples. |
| `.../authorization/casbin/store.py` | Proposed | Existing async session integration; writer ordering implementation; complete-set reconciliation; coherent filtered loading; no independent engine/commit. |
| `.../authorization/casbin/model.conf` and `__init__.py` | Proposed | One packaged model and normal package initialization; no automatic engine-selection side effect. |
| `src/backend/base/pyproject.toml` and existing workspace lockfile | Existing | Optional Python Casbin dependency and model package-data inclusion; no unrelated upgrades or new distribution. |
| Existing `lfx.toml` / deployment service configuration | Existing seam | Explicit selected `authorization_service` value; do not ship multiple engine choices. |
| `src/backend/base/langflow/services/authorization/service.py` | Existing | Restore approved default OSS semantics at replacement; remove native policy core, not default compatibility floors. |
| `src/backend/base/langflow/services/authorization/factory.py` and existing discovery/readiness integration | Existing | Verify normal selected-service resolution; do not hard-code an unconditional replacement or rewrite the registry. |
| `src/backend/base/langflow/services/authorization/repository.py` | Existing | Retain canonical loaders/registry and non-authoritative prefilters; retire independent effective-permission and scoped-role decisions. |
| `src/backend/base/langflow/services/authorization/policy.py` | Existing | Retain vocabulary, finite compiler mappings, and roster invariants; retire native request-policy decisions. |
| `src/backend/base/langflow/services/authorization/team_management.py` | Existing | Convert `require_team_operation()` and team-capability helpers to selected-service decisions; preserve canonical transactions, locks, invariants, and source handling. |
| `src/backend/base/langflow/services/authorization/share_management.py` | Existing | Share create/update/delete/cleanup joins early policy lock and final pre-commit reconciliation in its caller-owned transaction. |
| `src/backend/base/langflow/services/authorization/lifecycle.py` | Existing | Delegate existing and minimally added transaction hooks; cover all real policy writers. |
| `src/lfx/src/lfx/services/authorization/base.py` and existing event definitions | Existing | Preserve public contracts; add only missing framework-neutral no-op-compatible share/resource preflight/stage snapshots/hooks. |
| Existing `api/v1/authz_teams.py`, `authz_shares.py`, `authz_me.py`, `authz_capabilities.py`, `authz_recipients.py` | Existing | Preserve APIs; consume service capabilities/permissions; maintain session consistency, scoped recipient access, and transaction boundaries. |
| Existing role/assignment/user/API-key/directory writers | Existing | Reuse early identity hooks and ensure every affected canonical writer participates; do not add new provider features. |
| Existing flow/project mutation helpers and guards | Existing | Preserve creation and protected-operation contracts; hook only projection-relevant moves/deletes/scope changes. |
| `services/authorization/collaboration.py`, `concurrency.py`, `audit.py`, `fetch.py`, `guards.py` | Existing | Preserve revision/principal/privacy semantics; make only required service/session/readiness corrections. |
| Existing Teams/Share/Shared With Me frontend and permission hooks | Existing | Keep UI/query/store contracts, consuming authoritative capabilities; correct only demonstrated integration defects. |
| `scripts/ci/check_authz_endpoint_matrix.py`, existing persona/matrix files, pytest and Playwright suites | Existing | Structural coverage plus real service semantics, transaction tests, and exactly the eight connected product journeys. |
| `docs/auth-team-sharing-verification.md` and affected auth/sharing/config docs | Existing | Record exact new candidate evidence and configuration; preserve historical native results and limitations. |

Ellipses in proposed package rows mean the same `src/backend/base/langflow/services` prefix shown in the first row; they are not extra package locations.

### 19.2 Minimal internal contracts

Use existing data types wherever suitable. The following conceptual contracts describe responsibilities, not mandatory new public APIs:

- An immutable canonical policy snapshot containing only required non-secret state.
- Normalized immutable policy/group tuples using the existing `CasbinRule` fields.
- A compiler producing the complete desired tuple set.
- A store reconciling/loading those tuples through a caller-owned session with the required consistency.
- A service-private admission context tying principal/resource scope and loaded policy to one snapshot.

No generic graph framework, new canonical source, independent permission datastore, or externally callable policy editor is introduced. Keep dependency direction `langflow-base -> lfx`; LFX does not import Langflow ORM or the Casbin runtime.

### 19.3 Integration closure checks

Find and close all direct runtime consumers of the old policy helpers, including capability and summary paths. Merely moving the main `enforce()` implementation is incomplete.

Verify constructor/import configuration, optional package data, single/batch agreement, capability semantics, direct and list fetch behavior, share-management role paths, creation, lifecycle locks/staging, readiness, public transport exceptions, and historical external-sign-in/session regressions. Use the existing endpoint/persona matrix to find affected paths; do not expand the feature inventory.

### 19.4 Two-agent implementation discipline

If the contributor uses two agents, partition work by file ownership rather than architecture variants:

| Owner | Exclusive editing responsibility |
|---|---|
| Agent 1 — backend | All backend/LFX authorization and integration code, canonical mutation hooks, proposed Casbin package, backend dependency/lockfile changes, service configuration, and backend/unit/database tests. This includes flow/project backend call-site corrections. |
| Agent 2 — consumers/verification | Frontend source/tests, the existing eight Playwright journeys, plan-required CI scripts/workflows/matrices, affected documentation and verification ledger. No backend evaluator or mutation implementation edits. |

Read both sides freely. Before editing a shared manifest or fixture, assign it to one agent; never overwrite the other agent's work. Cross-boundary defects are transferred with a minimal reproducer/contract, not independently reimplemented. Do not create additional reporting artifacts or runtime coordination infrastructure.

Independent tasks may proceed concurrently after the baseline and internal contract are fixed. Final connected E2E/acceptance runs only against the **combined** candidate. A green isolated branch does not prove the integrated result. Agent 2 records evidence supplied by Agent 1 without claiming unexecuted commands succeeded.

---

## 20. Test- and behavior-driven validation

### 20.1 Evidence rules and implementation method

Use TDD/BDD within the existing test frameworks. For each actual correction, first reproduce the failing/missing contract with the smallest relevant test; implement the minimal clean change; rerun that test and materially affected regressions; fix attributable failures. Existing passing characterization tests are sufficient where they already express the required behavior—do not duplicate tests merely to increase counts.

State observable behavior in Given/When/Then terms, but do not add a new BDD dependency, runner, or test framework solely for this contribution. Use the real selected service for acceptance. Compiler fixtures and structural route/persona checks complement runtime tests; neither substitutes for the other.

The contributor-reported 368 assertions per runtime are reproduction inputs, not a target count and not proof of database/session correctness. Adapt incorrect creation, role-scope, team-domain, and lifecycle assumptions; record actual resulting counts. Do not add a Go runtime/CI job simply to preserve their demonstration. [P2]

Final acceptance must identify the exact combined SHA, selected service configuration, locked Casbin/runtime/database versions, commands, and executed/passed/failed/skipped counts. Do not claim passing results for unexecuted, collected-only, skipped, dependency-blocked, or historical candidate checks.

### 20.2 Registration, packaging, and compatibility

Use real built artifacts and actual service discovery where applicable. Cover:

- Default install without the extra: no accidental Casbin imports, correct default stub/fetch floors, no false collaboration capabilities.
- Optional package installed but not selected: no unconditional replacement of the default service.
- Explicit Casbin selection with enforcement enabled: expected service, model resource available, ready policy, and exactly one final evaluator.
- Missing dependency/model, invalid import/class, constructor failure, misresolved registration, or policy-load failure: selected configuration fails readiness/closed rather than using a default allow path.
- Existing third-party/default service contracts remain compatible with new no-op lifecycle hooks.
- Wheels/source distribution include `model.conf`; execution works without a repository working directory.
- Existing supported Python/package combinations import and load the exact optional implementation; record actual support rather than inferring it from package metadata.

### 20.3 Policy/compiler acceptance matrix

Implement or retain focused tests covering the following requirements. IDs are documentation traceability labels, not new product features.

| ID | Required behavior |
|---|---|
| PC-01 | Same canonical state produces sorted, deduplicated semantic tuples under shuffled input/query order. |
| PC-02 | Empty/rebuilt projection is equivalent; unchanged reconciliation performs no unnecessary row replacement. |
| PC-03 | Subject/object normalization is consistent; malformed UUIDs/principals/unknown actions/scopes fail closed. |
| PC-04 | Literal domain-chain union uses canonical project/workspace/`*` without per-project policy copies. |
| PC-05 | Scoped role inheritance preserves depth/cycle handling, finite wildcard expansion, and provenance survival. |
| PC-06 | `AuthzRole.workspace_id` intersects global/workspace/project assignment scope without widening. |
| PC-07 | Project move out of a role's permitted workspace removes affected authority; moving into it restores only canonically valid authority. |
| PC-08 | Team principal and exact-team role principal remain disjoint; cross-team management and resource escalation deny. |
| PC-09 | All eligible active Admin/Maintainer/User members receive team shares equally; role-only promotion does not lose resource access. |
| PC-10 | Membership with no share grants no resource access; resource write grants no team management. |
| PC-11 | Finite team-operation matrix covers ordinary/privileged targets and valid old/new role pairs; literal action wildcards do not expand. |
| PC-12 | Platform-only create/delete/list-all/activation/directory operations stay unavailable to ordinary team roles. |
| PC-13 | Inactive/suspended team loses resource authority but retains existing permitted active-member management/repair behavior. |
| PC-14 | Disabled user loses direct-share, scoped-role, team-sharing, and team-management authority; reactivation respects surviving canonical state. |
| PC-15 | Direct user/team exact-resource grants survive permitted moves independently of inheritance and never reveal private parents/siblings. |
| PC-16 | Project share covers current/future direct flows without child grants and loses inheritance when a flow moves out. |
| PC-17 | Creation uses `flow:*`/`create`; editable project share permits it, read-only share and ordinary flow-write alone do not. |
| PC-18 | Project share does not confer child delete; exact project deletion still respects complete-set mutation restrictions. |
| PC-19 | Share-level expansion and role-permission expansion remain distinct and finite; no unspecified future/admin wildcard authority. |
| PC-20 | Canonical owner/platform semantics and narrower external/API-key ceilings retain ordering; no synthetic ownership roles. |
| PC-21 | Scoped role-derived share management uses the selected service; ordinary resource write cannot reshare. |
| PC-22 | Overlapping sources survive removal of only one source; deduplication never drops remaining intended access. |
| PC-23 | Personal/unscoped resource behavior is unchanged; no fabricated workspace/team/organization containment. |
| PC-24 | PUBLIC admission stays separate and does not widen authenticated discovery or authenticated-owner semantics. |
| PC-25 | Loaded grouping closure includes both principal kinds; filtering by resource domains cannot accidentally remove required memberships. |
| PC-26 | `keyMatch2` receives only the validated internal grammar; root/subtree, mixed-key, parameter, regex/wildcard, and cross-scope negatives hold. |

Reuse the contributor's useful negative/mutation assertions where they match these contracts. Deliberately changing domain equality, adding an action wildcard, dropping grouping membership, or accepting unsafe object syntax must be caught by the relevant tests. This is scoped policy testing, not a new platform-wide mutation-testing program.

### 20.4 Real database transaction and concurrency acceptance

Use actual SQLite and PostgreSQL 16 connections with independent sessions, deterministic interleaving barriers, and failure injection. Do not simulate database isolation with one mocked session or infer it from pure compiler tests.

| ID | Given / When / Then requirement |
|---|---|
| TX-01 | Given a canonical grant mutation, when compilation fails, then canonical rows, derived rows, and required mutation audit do not commit. |
| TX-02 | Given successful compilation, when derived insert/delete or required audit fails, then the complete mutation rolls back with no success response. |
| TX-03 | Given writer A holds the projection lock and revokes access, when writer B waits then rebuilds, B rereads after A commits and cannot restore A's obsolete grant. |
| TX-04 | Given concurrent membership/share/role/provenance changes, both commit in the required order and final projection equals compilation of the final canonical state. |
| TX-05 | Given two rebuild/startup workers, they converge without partial-table exposure, duplicate rows, or overwriting a newer canonical mutation. |
| TX-06 | Given a project move and a concurrent role/workspace restriction update, resulting authority respects the final canonical intersection. |
| TX-07 | Given two independent service instances, a new admission after a revocation commit denies on both without restart/TTL/invalidation delivery. |
| TX-08 | Given an old policy state with membership but no share and a new state with share but no membership, an interleaved load cannot combine them into an allow that existed in neither state. |
| TX-09 | Given canonical scope changes while policy is loaded, the decision/response uses one coherent snapshot, not old context with new rules or vice versa. |
| TX-10 | Given SQLite contention or PostgreSQL lock/deadlock/serialization failure, bounded transaction retry reloads and reauthorizes; no stale client revision is silently accepted. |
| TX-11 | Given an early hook invoked with incomplete/advisory identity metadata, lock scope remains sufficient and contention is bounded; no premature policy writes or commits occur. |
| TX-12 | Given staged authentication/JIT user/assignment changes, the legitimate caller's subsequent permissions lookup preserves required shared-session behavior; other requests cannot see uncommitted policy. |
| TX-13 | Given a content-only flow update or capability read, no unnecessary complete compiler/reconciliation runs. |
| TX-14 | Given in-flight admission before revocation, its handling follows the existing contract; any later protected/resumable boundary loads fresh policy. |
| TX-15 | Given public/private/targeted share cleanup or user/team deletion, every affected canonical writer joins the transaction protocol and leaves no stale effective relationship. |
| TX-16 | Given a late/retried legacy post-commit event, the selected plugin does not write stale event-derived policy over newer committed state. |
| TX-17 | Given disabled sharing eligibility but valid inactive-team management membership, reconciliation preserves permitted management while removing resource access. |
| TX-18 | Given a failure or cancellation before commit, worker shutdown/connection cleanup leaves no leaked lock, partially published enforcer, or independent adapter commit. |

Lock-order and snapshot tests must exercise the actual configured driver/isolation settings. Savepoint-only mocks and logical ORM `begin()` assertions do not prove SQLite `BEGIN` behavior or PostgreSQL fresh-after-lock reads.

### 20.5 Application parity, privacy, and pagination

Run real-service tests demonstrating:

- `enforce`, `batch_enforce`, effective-permission responses, team/share capabilities, direct reads, and list results agree on the same state.
- One output per batch request is returned in order; multiple resource/domain checks do not race through a shared async session.
- Filtering happens before final pagination/counts, including interleaved allowed/denied rows and surviving overlapping grants.
- Shared-resource explanations and recipient lookup reveal only permitted labels/metadata.
- Owner/share/platform/protected-operation distinctions survive across HTTP, editor save, execution, and existing public/owner-scoped transport exceptions.
- Capability probes do not become mutation events; decision audit remains compatible with read-only snapshot handling and failure policy.
- Stale/revoked save rejection retains local unsaved content; no automatic old-payload replay or false write capability remains.
- Account switching/logout cannot reuse another principal's permission/resource snapshot.

Structural endpoint/persona coverage and real permission behavior must both pass. Do not replace either with `_policy_double.py` or a UI mock.

### 20.6 Existing eight connected E2E journeys — unchanged product scope

The mandatory product journeys remain exactly:

1. Platform Admin creates/manages team and role boundaries.
2. Direct Can use share: recipient reads/runs but cannot edit.
3. Upgrade to Can edit: recipient saves permitted changes.
4. Team project share: existing and future direct workflows inherit.
5. Membership removal/team suspension: new resource requests lose access unless another canonical source survives.
6. Downgrade while editor is open: save denied and unsaved local content retained.
7. Concurrent editors: stale save rejected rather than silently overwriting.
8. Direct flow share: private parent and siblings remain undisclosed.

Add only the necessary assertions within these journeys; do not invent a ninth product journey or expand into invitations, public-link management, tenancy, or unrelated editor redesign. Low-level compiler/transaction cases above are validation of these existing semantics, not new end-user features.

Run against the combined candidate using distinct authenticated users, `LANGFLOW_AUTO_LOGIN=false`, the actual registered service with enforcement positively enabled, real persisted canonical/derived policy, no policy mocks, and zero feature retries. Use deterministic local/loopback model providers; no paid model calls are needed.

### 20.7 Performance and boundedness evidence

Measure the selected initial design rather than asserting it is fast because the model is small. Use existing representative fixtures and deployment/test budgets where recorded. Capture:

- compiler elapsed time and peak rule count versus canonical users/teams/assignments/shares;
- lock wait/hold time and actual changed-rule writes for a policy mutation;
- no-op reconciliation write count;
- single/batch/list authorization latency and SQL query/loaded-rule counts;
- memory and query growth without per-child/per-member resource grant fanout;
- contention/failure behavior on both supported database engines.

Compare against the same environment's native baseline where available. Do not invent a numerical production capacity/SLO claim absent from the source evidence. A material regression or unbounded scan must be corrected within the selected architecture or recorded as an unresolved acceptance issue. It does not authorize a long-lived permission cache, distributed lock service, new policy datastore, or unrelated benchmark program.

### 20.8 Honest completion and no deployed dual evaluation

Temporary test-only comparison with fixed native expectations is allowed. Do not ship native/Casbin comparison logs, shadow decisions, dual-run flags, fallback evaluators, or a retired native module still reachable from the production service.

Record failed or unavailable checks accurately and finish the scoped implementation as far as possible; do not manufacture a green result. The combined replacement is complete only when its required tests execute successfully and the old runtime policy path is removed.

---

## 21. CI, code quality, and distribution validation

Preserve the existing CI structure, supported runtime matrix, and applicable inherited checks. Do not redesign CI or lower coverage to accommodate the replacement.

Required applicable validation includes the real authorization backend matrix; SQLite/PostgreSQL 16; supported Python versions required by the existing workflow; backend/LFX regression; frontend Jest; the eight authz Playwright journeys; inherited core browser checks; migrations; endpoint/persona and CI-script checks; Ruff/Biome/pre-commit/secret checks; scoped typing and existing baseline comparison; affected documentation/accessibility; and candidate package/container/ARM64 checks where selected. [P1]

Make only necessary selection/configuration changes so acceptance genuinely loads the registered Casbin service and exact optional dependency from the final candidate. Both backend and browser jobs must record/assert the expected service and enabled collaboration capability, not just set an environment variable.

Verify:

- Test discovery is non-empty and all eight feature journeys actually execute.
- Distinct browser suites use non-colliding reports/artifacts.
- Aggregate CI cannot pass by silently skipping the feature suite or ignoring required failures.
- No blanket skip/xfail, retry inflation, `continue-on-error`, policy mocking, or reduced coverage converts failures to apparent success.
- Default/no-extra compatibility jobs stay valid without importing Casbin.
- Built artifacts include model resources and optional installation works in the actual importing distributions.
- No released upstream image/package is used as evidence for the unbuilt fork candidate.
- Historical baseline typing/optional-provider/release-conditional limitations remain explicit and are not relabeled as newly fixed or executed.

Package the selected dependency through the backend extra and the existing lockfile process. Keep LFX framework-neutral. Do not add tests into deployment execution, generate migrations during runtime, change unrelated workflows/dependencies, or create a Go build pipeline for standalone contributor assertions.

---

## 22. Work packages and implementation order

These packages refine one contribution. Internal tasks can run concurrently under Section 19.4, but dependent integration/validation cannot be skipped or represented as parallel runtime versions.

### WP-01 — Rebaseline without reopening product scope

Read the complete current plan, `AGENTS.md`, package-specific instructions, existing code, and current diff. Confirm the actual branch/head, upstream reference, feature migration, dependency locks, and historical native evidence. Preserve newer work and do not reset to historical SHAs.

Capture focused native characterization where current tests do not already specify a required replacement boundary. Enumerate actual policy-relevant writers and all native policy-helper consumers, including capability/list/summary paths. Use existing verification documentation; no separate audit project is required.

**Done when:** current baseline and scope are recorded accurately, agent file ownership is clear, and neither completed features nor unrelated behavior are being recreated.

### WP-02 — Record selected packaging and obtain the missing upstream acceptance

Record D01 as the selected technical architecture: optional registered in-process implementation in the existing backend package, one `authorization_service` selection, no extra service/package/engine selector.

Check authoritative issue/PR feedback for maintainer acceptance of that placement and production adoption. Do not infer it from community test counts or contributor agreement. While it remains absent, preserve deployed native behavior and perform only the allowed isolated design/model/compiler work.

Obtain the complete proposed contributor patch/fixtures/Python tests through a reviewable PR, not direct mutation of the working branch. Verify source/provenance through the existing project contribution process. No new CLA or approval infrastructure is introduced.

Confirm optional dependency identity/version compatibility and the normal registration/model-resource packaging path. Record unknowns as such; do not invent acceptance or select a second architecture.

**Done when:** the selected design and upstream acceptance status are explicit. Production integration starts only when the retained prerequisite is satisfied; a pending condition is not a completed task or a new runtime gate.

### WP-03 — Prove the corrected minimal model/compiler

Use the accepted four-field model, one `g`, exact actions, literal domains, and constrained object matching. Port the useful contributor fixtures into existing Python test conventions without adopting their known conflicting assumptions.

Implement/prove role workspace/assignment intersection, parent flattening, finite permission expansion, provenance, exact-team management principals, all-role team sharing, suspended-team management separation, canonical domain chains, exact shares across moves, dynamic inheritance, and `flow:*`/`create`.

Use independent expectations and negative/mutation tests for the required semantics. Do not add ABAC/deny/priority, a Team Owner, workspace-owned teams, or extra grouping systems.

**Done when:** focused Python model/compiler tests cover Section 20.3 using actual accepted dependency behavior; no fixture omission is being mistaken for full-system coverage.

### WP-04 — Implement the registered service and remove native policy paths

After the adoption prerequisite, add the proposed package and optional dependency/model resources; configure the one registered implementation through the existing seam. Preserve non-enforcing/default distribution semantics and add the narrow selected-service readiness checks necessary to prevent silent stub substitution.

Implement canonical admission context, domain-chain enforcement, batching, capabilities, share-management policy, public-principal compatibility, and visibility using the same compiled representation. Move team capability/mutation decisions together. Preserve the established API creation and authentication/shared-session contracts.

Retire all superseded native role/share/team/scoped-role decision paths and update their real consumers. Reuse loaders and invariants rather than subclassing or keeping a dormant native evaluator.

**Done when:** a single selected policy implementation owns all policy-based decisions, default compatibility remains safe, and callers/frontends are still engine-agnostic. Do not activate an intermediate implementation without WP-05 consistency.

### WP-05 — Complete transaction ordering, storage, and fresh reads

Implement `store.py` over the existing `CasbinRule`/session infrastructure, with AutoSave/independent commit disabled. Reconcile the complete normalized desired rule set via semantic insert/delete differences.

Connect all policy-relevant writers to early PostgreSQL advisory/SQLite write ordering and final canonical/derived/audit staging. Reuse existing hooks and add only missing default-compatible share/resource contracts. Cover lifecycle cleanup, role/workspace changes, moves, and rebuilds.

Implement coherent fresh read snapshots, filtered `g`/`p` loading, caller-owned write-session reuse, and bounded retry semantics. Make startup/rebuild idempotent and verify selected-service readiness. Do not add a generation/cache correctness system.

**Done when:** Section 20.4 database tests pass on actual independent connections and final projection equals canonical compilation after concurrent mutations, failures, retries, and rebuilds.

### WP-06 — Validate the combined candidate and fix scoped regressions

Integrate both agents' changes into one candidate and run real service, application parity, writer concurrency, packaging/readiness, list/count/privacy, and performance checks. Run the same eight connected E2E journeys with real users, enabled selected service, deterministic providers, and zero feature retries.

Run applicable inherited backend/LFX/frontend/migration/docs/container checks. Repair only plan-attributable failures. Repeat affected acceptance after the final changes; do not cite isolated branch or native-candidate results as combined proof.

**Done when:** final-SHA commands/results demonstrate required behavior, consistency, scope, and packaging. Blocked/unrun checks are explicit; acceptance is not called complete until the mandatory combined checks execute successfully.

### WP-07 — Reconcile documentation and contribution delivery

Update only affected `AGENTS.md`/authorization/authentication/sharing documentation, existing service configuration examples, optional installation/model-data notes, endpoint/persona matrices, verification ledger, and current contribution PR/status descriptions.

Document registration, default versus selected-service behavior, canonical source of truth, domain and role intersection, creation, team-management/resource separation, writer protocol, admission freshness, rebuild, owner/dependency boundaries, actual measured limitations, and exact final candidate evidence.

Preserve historical native records and the recorded merged PR #1 status. Do not rewrite a merged historical PR as a new WIP or relabel its test results. Change live issue/PR metadata only under the contributor's authorized workflow.

Review the complete diff, remove only own unrelated changes, verify no retained alternative evaluator/authority, and leave minimal final reporting: implementation summary, actual tests/results, and material unresolved blockers.

**Done when:** source, configuration, documentation, current PR status, and verification evidence agree without changing the contribution's product scope.

---

## 23. Definition of done

Unchecked items are requirements, not claims of current completion. The selected replacement is complete only with evidence from its final integrated candidate.

### 23.1 Decision and contribution boundary

- [ ] Registered in-process optional packaging is the single selected technical target.
- [ ] Required upstream acceptance is evidenced or still explicitly marked pending; contributor approval is not mislabeled as maintainer approval.
- [ ] The complete diff is traceable to this plan; no unrelated code, dependency, test, CI, schema, or documentation changes remain.
- [ ] The original feature is preserved, not recreated, and recorded native evidence retains its actual SHA and limitations.

### 23.2 Product behavior

- [ ] Team creation is atomic/non-empty and nominates required active Admin membership; active teams retain the invariant through all writers.
- [ ] Admin/Maintainer/User remain team-scoped and never become platform superusers or implicit resource owners.
- [ ] All eligible active members receive team shares equally; promotion alone does not revoke them.
- [ ] Suspended teams confer no resource access while existing permitted management/repair behavior is preserved.
- [ ] Owners share with existing users/teams; Can use/Can edit retain execute/write mapping.
- [ ] Project inheritance covers current/future direct flows without child or per-member grant fanout.
- [ ] Direct shares remain exact-resource grants and preserve private parent/sibling boundaries through permitted moves.
- [ ] Creator ownership and recipient execution/dependency boundaries remain intact.
- [ ] Ordinary editing does not imply sharing, deletion, transfer, move, publication, authentication, or deployment authority.
- [ ] Stale/revoked writes are rejected without replay; unsaved local content is preserved.
- [ ] Existing public, API-key, external-auth, and owner-scoped transport contracts remain intact.

### 23.3 Model, compiler, and authority

- [ ] `authz_*` plus canonical user/resource state is the sole writable policy authority; `casbin_rule` is rebuildable derived state.
- [ ] One registered `BaseAuthorizationService` implementation owns all scoped-role/share/team policy decisions and derived capabilities.
- [ ] One minimal `g` relation represents separate team sharing and team-management principals; no additional graph system exists.
- [ ] Subject/domain/object/action contracts are preserved; object normalization is internal and validated.
- [ ] Domains use canonical project/workspace/`*` evaluation; no workspace or team containment is invented.
- [ ] Role scope compilation includes the assigned role's workspace restriction, assignment domain, parent semantics, provenance, and explicit wildcard expansion.
- [ ] Containment/role updates reconcile affected restrictions without stale grants.
- [ ] Creation remains `flow:*` with `create`; no alternative `project/P + flow:create` permission shape exists.
- [ ] Team operations are finite and target-aware; platform-only actions remain platform-only.
- [ ] No wildcard admin authority, explicit-deny/priority expansion, synthetic owner role, or personal-team model exists.
- [ ] Native `effective_access*`, `team_operation_allowed()`, scoped-role evaluation, and other retired final decision paths are not reachable in the delivered runtime.

### 23.4 Storage, freshness, and readiness

- [ ] The store uses the existing model and caller-owned sessions; no AutoSave, independent commits, adapter schema, or second policy datastore exists.
- [ ] Desired-rule reconciliation changes only semantic insertions/deletions and is deterministic/idempotent.
- [ ] Every policy-relevant canonical writer and rebuild participates in early writer ordering before authoritative reads.
- [ ] PostgreSQL advisory locking and SQLite early write transactions are verified through actual database behavior.
- [ ] Required canonical/derived/audit changes are atomic; failure, cancellation, and retry cannot publish partial state.
- [ ] Concurrent rebuild/revocation and role/move tests cannot restore obsolete policy.
- [ ] Fresh admission snapshots load canonical context and grouping/policy consistently; new requests observe committed revocation across workers.
- [ ] Caller-owned authentication/JIT/write sessions retain correct visibility without separate-connection regressions.
- [ ] Read snapshots end before long-running execution; no long-lived positive policy cache or generation authority is introduced.
- [ ] Startup/rebuild is safe across workers, unknown prior policy is not silently destroyed, and selected-plugin failures cannot fall back to the OSS stub/native evaluator.

### 23.5 Application and verification

- [ ] Single/batch enforcement, team/share capabilities, effective permissions, summaries, list pagination/counts, and direct-resource results agree.
- [ ] Optional packaging, model resources, actual registration, and default/no-extra compatibility pass.
- [ ] Real Python Casbin service/compiler/database tests execute on required supported runtimes and SQLite/PostgreSQL.
- [ ] All eight connected authorization E2E journeys execute and pass against the combined candidate, with real distinct users and zero feature retries.
- [ ] Applicable inherited checks remain intact; no skip/mock/reporting loophole produces false-green acceptance.
- [ ] Query/rule growth, reconciliation cost, lock contention, and single/batch/list performance are measured; material regressions are resolved or recorded as blockers.
- [ ] Documentation, contributor PR/status, and verification evidence describe the same exact implementation and actual acceptance results.

---

## 24. Explicitly forbidden implementation choices

Do not introduce:

- A second canonical permission source, independently authored Casbin rows, separate policy database, policy-management UI/API, or adapter-owned schema/session pool.
- Native/Casbin dual evaluation, fallback, runtime feature-engine selection, shadowing, canary, V2 authorization APIs, a sidecar, or a separate authorization microservice.
- A default stub silently substituted for an explicitly selected enforcing implementation.
- Competing native policy decisions in helpers, SQL visibility logic, capability endpoints, public handling, or frontend state.
- New workspace/organization ownership for teams, team-rooted resource paths, synthetic Team Owner/ownership roles, or personal workspaces converted into teams.
- Additional `g2`/`g3`, role-manager registries, ReBAC/ABAC systems, policy-precedence frameworks, or resource editor/viewer intermediaries not required by the selected model.
- Per-child policy/share fanout for project inheritance or per-member/per-resource copies for team sharing.
- Team role promotion/demotion changing sharing membership when canonical eligibility otherwise survives, or inactive-team resource exclusion erasing legitimate management/repair access indiscriminately.
- Blanket `global` domains for actual workspaces, treating unknown scopes as global, or ignoring `AuthzRole.workspace_id` restrictions.
- Wildcard action authority, wildcard team mutation actions under an exact-action matcher, unbounded future admin actions, or explicit deny/priority added for this contribution.
- A second creation contract such as `project/P + flow:create`, or request-time inference of flow creation from generic project write after enforcement.
- AutoSave, independent policy commits, unconditional full-table truncation, compilation from a pre-lock stale snapshot, partial policy publication, or stale-event post-commit overwrites.
- Advisory locks acquired only after conflicting entity locks, incomplete writer participation, indefinite waits, or retries that ignore original stale-write preconditions.
- Mixed-snapshot canonical/group/policy decisions, reused snapshots from earlier requests, or shared async sessions used concurrently.
- Long-lived positive permission caches, policy generation tables, Redis/JWT/resource-object authority, or watcher/TTL-dependent revocation.
- Holding authorization transactions open across provider execution, copied credentials, owner-principal execution fallback, or a new execution sandbox.
- Filtering only an already paginated page while misreporting authorized totals, or exposing private parent metadata through access explanations.
- Opportunistic cleanup, unrelated bugs/features/security systems, unrelated dependency/CI changes, blanket test skips/xfails, weakened assertions, or false-green reporting.
- Production approval/authority/staging systems; ordinary transaction staging is required and is not such a system.
- Copying unavailable proprietary Enterprise implementation code, adding a Go runtime to Langflow for the contributor's demonstration, or claiming unexecuted model/database/E2E results.

---

## 25. Sources, evidence, and revision reconciliation

### 25.1 Evidence categories

**Source baseline [P1].** The attached Revision 1.6 is the product/structure baseline. Its recorded branch/candidate/migration/PR identifiers and test claims are historical. Sections 8–18 retain those product contracts and add only decision-linked integration clarifications.

**Community material [P2].** The supplied response describes the evolving Casbin model and reports standalone Go/Python assertions. It is not the complete implementation patch and explicitly excludes database atomicity and Langflow service/E2E validation. The reported 368 assertions per runtime were not independently reproduced by this document update.

**Selected design [D01–D10].** The user accepted the preceding integration recommendation. Those are contribution design decisions, not statements that upstream has approved them or that production code already implements them.

**Reviewed repository sources [R1–R8].** These are public contracts and code at recorded commits used in this conversation. Targeted service/documentation reads were rechecked during this revision; this is not a fresh whole-repository audit or a claim that the recorded commits are today's branch heads.

**External technical verification [T1–T5].** Official database, ORM, and Casbin documentation supports the limited primitive/packaging facts cited in the relevant sections. The complete transaction/snapshot protocol is the selected integration design and still requires implementation tests; documentation does not certify it.

### 25.2 Source index

- **[P1]** `auth_share_implementation_plan_updated_latest 002(1).md`, supplied Revision 1.6, September 6, 2026. This document supersedes it as Revision 1.7 without altering the original attachment.
- **[P2]** Supplied community response / `Pasted markdown(3).md`: four-field model; same-`g` team management; compiler excerpts; domain-chain evaluation; reported Go Casbin v2.135.0 and Python Casbin 1.43.0 tests; explicit storage/service/E2E limitations.
- **[R1]** Upstream `AGENTS.md`, authorization architecture and guard contract, recorded commit `e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5`. `https://github.com/langflow-ai/langflow/blob/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5/AGENTS.md`
- **[R2]** Upstream `src/lfx/PLUGGABLE_SERVICES.md`, existing service registration and identity-lock contract, same upstream commit. `https://github.com/langflow-ai/langflow/blob/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5/src/lfx/PLUGGABLE_SERVICES.md`
- **[R3]** Fork `src/lfx/src/lfx/services/authorization/base.py`, service/batch/visibility and caller-owned mutation contracts, recorded fork commit `e4ae38be2636f2532053eeee3ebcb19ea08cc406`. `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/src/lfx/src/lfx/services/authorization/base.py`
- **[R4]** Fork `src/backend/base/langflow/services/authorization/repository.py`, canonical resource resolution, role workspace/assignment checks, inheritance, share administration, and effective access, same fork commit. `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/src/backend/base/langflow/services/authorization/repository.py`
- **[R5]** Fork `src/backend/base/langflow/services/authorization/team_management.py`, existing capability/operation consumers, ordered transactions, management membership versus eligible sharing recipient, same fork commit. `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/src/backend/base/langflow/services/authorization/team_management.py`
- **[R6]** Fork `src/backend/base/langflow/services/database/models/auth/authz.py`, existing canonical and derived models; no new team workspace/organization ownership, same fork commit. `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/src/backend/base/langflow/services/database/models/auth/authz.py`
- **[R7]** Upstream `services/authorization/guards.py` and fork `services/authorization/policy.py`, existing resource/create/owner and project-child action contracts, at the respective recorded commits. `https://github.com/langflow-ai/langflow/blob/e3abffc1b8da1e38cc2f21a9cf1b23b4a21c15d5/src/backend/base/langflow/services/authorization/guards.py` and `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/src/backend/base/langflow/services/authorization/policy.py`
- **[R8]** Fork `services/authorization/share_management.py` and `docs/auth-team-sharing-verification.md`, canonical transaction helpers and historical candidate-specific evidence, at the recorded fork commit. `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/src/backend/base/langflow/services/authorization/share_management.py` and `https://github.com/waqoor/langflow/blob/e4ae38be2636f2532053eeee3ebcb19ea08cc406/docs/auth-team-sharing-verification.md`
- **[T1]** PostgreSQL 16 official documentation: transaction-level advisory locks/consistent lock ordering and Read Committed versus Repeatable Read. `https://www.postgresql.org/docs/16/explicit-locking.html` and `https://www.postgresql.org/docs/16/transaction-iso.html`
- **[T2]** SQLite official transaction documentation: read/write transactions, `BEGIN IMMEDIATE`, writer contention, and rollback boundaries. `https://www.sqlite.org/lang_transaction.html`
- **[T3]** Casbin official adapter documentation: AutoSave and explicit policy persistence behavior. `https://casbin.org/docs/adapters/`
- **[T4]** Publisher package documentation for the Python distribution/import `casbin`; the cited version is a reproduction reference, not a latest-version or production-compatibility claim. `https://pypi.org/project/casbin/1.43.0/`
- **[T5]** SQLAlchemy 2.0 official transaction and SQLite dialect documentation: session transaction ownership/isolation and actual SQLite driver transaction-control differences. `https://docs.sqlalchemy.org/en/20/orm/session_transaction.html` and `https://docs.sqlalchemy.org/en/20/dialects/sqlite.html`

### 25.3 Remaining evidence, not new architecture alternatives

The following remain to be established during the authorized implementation workflow:

- Actual current repository heads/instructions and the exact final integrated candidate.
- Maintainer acceptance required for production adoption/source-tree placement.
- Full contributor compiler/model/fixture/Python test patch and applicable project contribution provenance.
- Locked optional Python package version, real package resources, and supported runtime compatibility.
- Complete policy-writer inventory, actual session/lock/snapshot integration, and real SQLite/PostgreSQL correctness results.
- Combined service/capability/list/runtime/E2E acceptance and measured performance/limits.

Do not fill these gaps with claims of completed work. Their absence does not authorize a parallel implementation, alternate deployment, broader contribution, or weakened test.

### 25.4 What Revision 1.7 changes from 1.6

| Earlier ambiguity or omission | Revision 1.7 resolution |
|---|---|
| Packaging was an unresolved choice between native and registered implementations. | Registered optional in-process packaging is the selected technical target; upstream adoption acceptance remains separately evidenced. |
| Team-management policy favored direct per-user rows. | One `g` also represents exact-team management principals; one selected representation, not both. |
| Scoped-role compilation described assignment domains without explicit role workspace intersection. | Section 5.3 specifies the intersection and containment-change reconciliation. |
| Creation and team domains could be redefined by standalone fixtures. | Preserve `flow:*`/`create`; no invented team workspace/organization ownership. |
| Inactive-team filtering could remove all management policy. | Separate sharing eligibility from existing management/repair access. |
| Atomic staging could be mistaken for complete concurrency safety. | Early writer ordering, complete participation, stale-snapshot prevention, and coherent admission loading are explicit. |
| Full rebuild could mean unconditional truncate/reinsert on every operation. | One complete deterministic computation with differential persistence only on relevant mutations. |
| Main enforcement could move while capabilities/lists retained native decisions. | Concrete consumer inventory and combined parity/pagination/count tests are mandatory. |
| Community model assertions could appear equivalent to acceptance. | Contributor-reported standalone evidence is separated from unexecuted Langflow/database/E2E proof. |

---

**Revision 1.7 outcome:** the selected integration is now specified as one optional registered backend Casbin service, with concrete modules, preserved domain/API/product semantics, complete scoped-role compilation, exact-team management, explicit creation, transaction-owned differential policy reconciliation, database writer ordering, coherent fresh reads, and combined verification. Product scope is unchanged. No code, branch, issue/PR, migration, repository setting, or deployment was modified by this document update. No combined Langflow–Casbin runtime test result is claimed.
