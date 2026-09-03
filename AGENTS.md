# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

Langflow is a visual workflow builder for AI-powered agents. It has a Python/FastAPI backend, React/TypeScript frontend, and a lightweight executor CLI (lfx).

## Prerequisites

- **Python:** 3.10-3.14
- **uv:** >=0.4 (Python package manager)
- **Node.js:** >=20.19.0 (v22.12 LTS recommended)
- **npm:** v10.9+
- **make:** For build coordination

## Common Commands

### Development Setup
```bash
make init              # Install all dependencies + pre-commit hooks
make run_cli           # Build and run Langflow (http://localhost:7860)
make run_clic          # Clean build and run (use when frontend issues occur)
```

### Development Mode (Hot Reload)
```bash
make backend           # FastAPI on port 7860 (terminal 1)
make frontend          # Vite dev server on port 3000 (terminal 2)
```

For component development, enable dynamic loading:
```bash
LFX_DEV=1 make backend                    # Load all components dynamically
LFX_DEV=mistral,openai make backend       # Load only specific modules
```

### Code Quality
```bash
make format_backend    # Format Python (ruff) - run FIRST before lint
make format_frontend   # Format TypeScript (biome)
make format            # Both
make lint              # mypy type checking
```

### Testing
```bash
make unit_tests                    # Backend unit tests (pytest, parallel)
make unit_tests async=false        # Sequential tests
uv run pytest path/to/test.py      # Single test file
uv run pytest path/to/test.py::test_name  # Single test

make test_frontend                 # Jest unit tests
make tests_frontend                # Playwright e2e tests
```

### Database Migrations
```bash
make alembic-revision message="Description"  # Create migration
make alembic-upgrade                         # Apply migrations
make alembic-downgrade                       # Rollback one version
```

## Architecture

### Monorepo Structure
```
src/
├── backend/
│   ├── base/langflow/     # Core backend package (langflow-base)
│   │   ├── api/           # FastAPI routes (v1/, v2/)
│   │   ├── components/    # Built-in Langflow components
│   │   ├── services/      # Service layer (auth, database, cache, etc.)
│   │   ├── graph/         # Flow graph execution engine
│   │   └── custom/        # Custom component framework
│   └── tests/             # Backend tests
├── frontend/              # React/TypeScript UI
│   └── src/
│       ├── components/    # UI components
│       ├── stores/        # Zustand state management
│       └── icons/         # Component icons
├── langflow-core/         # Usable provider-free Langflow distribution
├── bundles/               # Curated provider integrations
└── lfx/                   # Lightweight executor and shared primitives
```

### Key Packages
- **langflow**: Full end-user package; depends on `langflow-core` and curated provider bundles
- **langflow-core**: Service-complete, provider-bundle-free distribution; owns the `langflow` CLI
- **langflow-base**: Modular application platform (API, services, graph engine); extras add service integrations
- **lfx**: Shared execution primitives and standalone CLI (`lfx serve`, `lfx run`)

The public dependency direction is `langflow → langflow-core → langflow-base → lfx`.
Provider packages under `src/bundles/` are added only by the full `langflow` distribution.

### Service Layer
Backend services in `src/backend/base/langflow/services/`:
- `auth/` - Authentication
- `authorization/` - Authorization (RBAC) plugin layer — see below
- `database/` - SQLAlchemy models and migrations
- `cache/` - Caching layer
- `storage/` - File storage
- `tracing/` - Observability integrations

### Authorization (RBAC)

Authorization is a pluggable layer separate from authentication:

- `lfx` owns `BaseAuthorizationService` and its provider-free, pass-through default.
- The full Langflow application registers `LangflowAuthorizationService`, a native evaluator that reads committed `authz_*`, user, and resource rows. It is the single production policy path for built-in teams and sharing; it does not maintain a shadow policy database or require Redis for correctness.
- A deployment can replace that service through the `authorization_service` entry in `lfx.toml`. A replacement must advertise the collaboration capabilities it actually implements; the frontend fails closed when the service is unavailable or incomplete.

Enforcement is default **off** through `LANGFLOW_AUTHZ_ENABLED=false`, preserving historical owner-scoped behavior. With the native Langflow service and the flag enabled, unknown actions, missing policy data, inactive identities, and service failures deny rather than degrading to pass-through behavior.

Team-management roles are distinct from resource permissions: `admin`, `maintainer`, and `user` apply only to one team's roster and settings. Platform authority remains an active `User.is_superuser`, subject to the configured bypass and credential ceiling. Resource access comes from ownership, scoped roles, user/team shares, and direct-project inheritance.

The sharing dialog exposes only **Can use** (`execute`) and **Can edit** (`write`) for flow/project user or team grants. The low-level API retains `read`, `execute`, `write`, and `admin`; do not collapse or silently promote those values. An editable grant does not confer ownership, deletion, moving, publishing, or resharing authority.

Route guards live in `langflow.services.authorization.guards` (the legacy `langflow.services.authorization.utils` path re-exports them for backward compatibility):
- `ensure_flow_permission(user, FlowAction.*, flow_id=..., flow_user_id=..., workspace_id=..., folder_id=...)` — single-flow CRUD + execute
- `ensure_deployment_permission(user, DeploymentAction.*, deployment_id=..., deployment_user_id=..., workspace_id=..., project_id=...)`
- `ensure_project_permission(user, ProjectAction.*, project_id=..., project_user_id=..., workspace_id=...)`
- `ensure_knowledge_base_permission(user, KnowledgeBaseAction.*, kb_name=..., kb_user_id=...)`
- `ensure_variable_permission(user, VariableAction.*, variable_id=..., variable_user_id=...)`
- `ensure_file_permission(user, FileAction.*, file_id=..., file_user_id=...)`
- `ensure_share_permission(user, ShareAction.*, share_id=..., share_user_id=...)`
- `filter_visible_resources(user, resource_type=..., candidates=..., act=...)` — list-endpoint filter; safe no-op in OSS

The enforcement request shape is `(subject, domain, object, action)`:
- subject = `user:{uuid}`
- domain = `project:{uuid}` → `workspace:{uuid}` → `*` (resolved by `_resolve_flow_domain`; the more specific domain wins so project-scoped grants match directly while workspace-scoped grants still flow down via plugin-side role inheritance)
- object = `flow:{uuid}` / `deployment:{uuid}` / `project:{uuid}` / `flow:*` / etc.
- action = `read` / `write` / `create` / `delete` / `execute` / `deploy`

**Share-aware fetch:** route fetch helpers (`_read_flow`, `get_flow_by_id_or_endpoint_name`, `get_deployment`, project reads in `projects.py`, v2 file fetcher, variable PATCH/DELETE in `variable.py`) branch on `BaseAuthorizationService.supports_cross_user_fetch()`. The native service returns exact database-prefiltered visibility IDs and lets `ensure_*_permission` decide direct access. A substituted service that declines this capability retains owner-scoped queries. Route handlers can convert a deny to `404` with `langflow.services.authorization.fetch.deny_to_404` to preserve UUID privacy.

**Share CRUD API:** `/api/v1/authz/shares` provides POST / GET / PATCH / DELETE plus the resource-scoped `/summary` view. Mutations resolve the stored resource, enforce resource-specific share administration, validate active recipients, and commit the share plus mutation audit atomically. Enabled services advertising conditional writes require the observed strong ETag through `If-Match` for share updates/deletes and flow/project mutations; missing/stale preconditions return `428`/`412`. Never retry a stale edit automatically.

**Collaboration discovery:** `/api/v1/authz/capabilities` reports enforcement/readiness/team/sharing/conditional-write support without secrets. `/api/v1/authz/recipients` performs bounded, purpose-specific user/team search only after the caller is authorized for the intended resource or team operation. `/api/v1/authz/me/permissions` is the fail-closed UI capability source.

**Audit query API (Phase 4):** `GET /api/v1/authz/audit` (superuser-only) exposes a paginated, filterable view of `authz_audit_log`. Supports `user_id`, `resource_type`, `resource_id`, `action`, `result`, `since`, `until` filters; page size capped at 200.

**Default role catalog:** the foundations migration `7c8d9e0f1a2b_authz_foundations` seeds the three built-in `is_system=True` roles (viewer / developer / admin) with `"{resource}:{action}"` permission slugs. The native service evaluates them directly; a replacement service may consume the same canonical catalog.

**Required authorization CI:** backend acceptance is the `Run Team Sharing Backend Tests` SQLite/PostgreSQL 16 and Python 3.10/3.14 matrix. Browser acceptance is `Run Team Sharing E2E`, which sets `LANGFLOW_E2E_AUTHZ=true`, selects `tests/core/features/authz`, requires all eight `J1`-`J8` `@authz` journeys, uses distinct users, one worker, and zero retries. Normal Playwright mode excludes only that separately owned directory. Both jobs are mandatory in `CI Success` whenever `authz-sharing` paths or `run-all-tests` select them.

## Component Development

Components live in `src/backend/base/langflow/components/`. To add a new component:

1. Create component class inheriting from `Component`
2. Define `display_name`, `description`, `icon`, `inputs`, `outputs`
3. Add to `__init__.py` (alphabetical order)
4. Run with `LFX_DEV=1 make backend` for hot reload

**IMPORTANT:** Changing a component's class name is a breaking change and should never be done. The class name serves as an identifier used to match components in saved flows and to flag them for updates in the UI. Renaming it will break existing flows that use that component.

### Component Structure
```python
from langflow.custom import Component
from langflow.io import MessageTextInput, Output

class MyComponent(Component):
    display_name = "My Component"
    description = "What it does"
    icon = "component-icon"  # Lucide icon name or custom

    inputs = [
        MessageTextInput(name="input_value", display_name="Input"),
    ]
    outputs = [
        Output(display_name="Output", name="output", method="process"),
    ]

    def process(self) -> Message:
        # Component logic
        return Message(text=self.input_value)
```

### Component Testing
Tests go in `src/backend/tests/unit/components/`. Use base classes:
- `ComponentTestBaseWithClient` - Components needing API access
- `ComponentTestBaseWithoutClient` - Pure logic components

Required fixtures: `component_class`, `default_kwargs`, `file_names_mapping`

## Frontend Development

- **React 19** + TypeScript + Vite
- **Zustand** for state management
- **@xyflow/react** for graph visualization
- **Tailwind CSS** for styling

### Custom Icons
1. Create SVG component in `src/frontend/src/icons/YourIcon/`
2. Export with `forwardRef` and `isDark` prop support
3. Add to `lazyIconImports.ts`
4. Set `icon = "YourIcon"` in Python component

## Testing Notes

- `@pytest.mark.api_key_required` - Tests requiring external API keys
- `@pytest.mark.no_blockbuster` - Skip blockbuster plugin
- Database tests may fail in batch but pass individually
- Pre-commit hooks require `uv run git commit`
- Always use `uv run` when running Python commands
- When running tests inside a sub-package (e.g. `langflow-base`, `lfx`), sync that package's dev group first: `uv sync --group dev --package langflow-base`. The default `uv sync` only resolves the top-level workspace and may leave dev-only test deps (e.g. `fakeredis`) uninstalled.

### Graph Testing Pattern

Proper Graph tests follow this pattern:
1. Build graph with connected components
2. Connect them via `.set()` calls
3. Call `async_start` and iterate over the results
4. Validate the results

### Testing Best Practices

- Avoid mocking in tests when possible
- Prefer real integrations for more reliable tests

## Version Management
```bash
make patch v=1.5.0  # Update version across all packages
```

This updates: `pyproject.toml`, `src/backend/base/pyproject.toml`, `src/frontend/package.json`

## Pre-commit Workflow

Pre-commit hooks run ruff and biome automatically on `git commit`, so manual
formatting is not required. To avoid an extra commit cycle when you have many
changes:

1. Run `make format_backend` once before staging - fixes most ruff issues up front.
2. Run `uv run git commit` (the `uv run` ensures pre-commit finds the right Python).
3. If you touched backend code, run `make unit_tests` locally for faster feedback than CI.

## Pull Request Guidelines

- Follow [semantic commit conventions](https://www.conventionalcommits.org/)
- Reference any issues fixed (e.g., `Fixes #1234`)
- Ensure all tests pass before submitting

## Documentation

Documentation uses Docusaurus and lives in `docs/`:
```bash
cd docs
yarn install
yarn start        # Dev server on port 3000 (prompts for 3001 if 3000 is in use)
```
