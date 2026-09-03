"""Per-user effective-permissions endpoint, used by the frontend permission gate.

The UI calls this once per page load with the list of resource IDs it wants to
render and learns which actions to enable/disable per resource — without making
a 403-triggering request for each one. Backed by
:meth:`BaseAuthorizationService.get_effective_permissions`. Full Langflow uses
the native canonical-table evaluator; a substituted service must report only
the capabilities it actually enforces.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSessionReadOnly
from langflow.services.auth.context import current_auth_context_for_authz
from langflow.services.authorization.access_ceiling import (
    EXTERNAL_ACCESS_ADMIN,
    external_access_allows,
    filter_actions_by_external_access_ceiling,
    get_current_external_access_context,
)
from langflow.services.authorization.collaboration import (
    CollaborationCapabilityError,
    discover_collaboration_capabilities,
)
from langflow.services.authorization.guards import should_apply_owner_override
from langflow.services.authorization.repository import (
    load_active_user,
    resolve_resources,
    user_can_manage_resource_shares,
)
from langflow.services.database.models.deployment.model import Deployment
from langflow.services.database.models.file.model import File as UserFile
from langflow.services.database.models.flow.model import Flow
from langflow.services.database.models.folder.model import Folder
from langflow.services.database.models.knowledge_base.model import KnowledgeBaseRecord
from langflow.services.database.models.user.model import User
from langflow.services.database.models.variable.model import Variable
from langflow.services.deps import get_authorization_service, get_settings_service

router = APIRouter(prefix="/authz/me", tags=["Authorization"])

# Match the resource slugs used by ensure_*_permission helpers.
ResourceTypeLiteral = Literal[
    "flow",
    "deployment",
    "project",
    "knowledge_base",
    "variable",
    "file",
    "component",
]

# Default action vocabulary aligned with the authorization plugin's known actions.
_DEFAULT_ACTIONS: tuple[str, ...] = ("read", "write", "execute", "delete", "create")
_MAX_RESOURCE_IDS = 500
# Cap actions per request to bound the batch_enforce cartesian product
# (resource_ids x actions). Headroom over the 6 known actions
# (read/write/execute/delete/create/manage) covers future additions without
# letting a client request `["read"] * 100000` to flood the enforcer.
_MAX_ACTIONS = 10

_RESOURCE_OWNER_LOOKUPS: dict[str, tuple[Any, str]] = {
    "flow": (Flow, "user_id"),
    "deployment": (Deployment, "user_id"),
    "project": (Folder, "user_id"),
    "knowledge_base": (KnowledgeBaseRecord, "user_id"),
    "variable": (Variable, "user_id"),
    "file": (UserFile, "user_id"),
}


class EffectivePermissionsRequest(BaseModel):
    """Body for :func:`get_effective_permissions`."""

    resource_type: ResourceTypeLiteral
    resource_ids: list[UUID] = Field(
        ...,
        description="Resource IDs to evaluate. Capped at 500 per request to keep batch_enforce bounded.",
    )
    actions: list[str] | None = Field(
        default=None,
        description=(
            "Actions to check. Each entry is lowercased and de-duplicated; the list is "
            f"capped at {_MAX_ACTIONS}. Defaults to read/write/execute/delete/create."
        ),
    )
    domain: str = Field(
        default="*",
        description="Authorization domain — typically ``project:{folder_id}`` or ``*``.",
    )

    @field_validator("actions")
    @classmethod
    def _normalize_actions(cls, value: list[str] | None) -> list[str] | None:
        """Lowercase, strip, de-duplicate (order-preserving), and cap the actions list.

        Returns ``None`` when the caller omitted the field (handler substitutes
        ``_DEFAULT_ACTIONS``). An empty list after normalization also returns
        ``None`` so the default kicks in rather than producing an empty cartesian
        product downstream.
        """
        if value is None:
            return None
        seen: set[str] = set()
        normalized: list[str] = []
        for raw in value:
            if not isinstance(raw, str):
                # Pydantic field_validators must raise ValueError (not TypeError)
                # to be wrapped into a ValidationError -> HTTP 422 response.
                msg = "actions must be strings"
                raise ValueError(msg)  # noqa: TRY004
            cleaned = raw.strip().lower()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        if len(normalized) > _MAX_ACTIONS:
            msg = f"actions capped at {_MAX_ACTIONS} unique entries"
            raise ValueError(msg)
        return normalized or None


class EffectivePermissionsResponse(BaseModel):
    """Response: ``{resource_id: [allowed_actions]}``."""

    resource_type: ResourceTypeLiteral
    permissions: dict[UUID, list[str]]
    capabilities: dict[UUID, "ResourceCapabilities"]


class ResourceCapabilities(BaseModel):
    """Route-aligned operations for one resolved resource."""

    can_use: bool = False
    can_edit: bool = False
    can_create_flow: bool = False
    can_delete: bool = False
    can_move: bool = False
    can_manage_shares: bool = False
    can_manage_publication: bool = False


def _empty_capabilities(resource_ids: list[UUID]) -> dict[UUID, ResourceCapabilities]:
    return {resource_id: ResourceCapabilities() for resource_id in resource_ids}


async def _derive_resource_capabilities(
    *,
    session: AsyncSession,
    current_user: User,
    resource_type: str,
    resource_ids: list[UUID],
    permissions: dict[UUID, list[str]],
) -> dict[UUID, ResourceCapabilities]:
    derived = _empty_capabilities(resource_ids)
    if resource_type == "component":
        return derived
    try:
        collaboration = await discover_collaboration_capabilities()
        superuser_bypass = bool(getattr(get_settings_service().auth_settings, "AUTHZ_SUPERUSER_BYPASS", True))
    except CollaborationCapabilityError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "AUTHORIZATION_NOT_READY", "message": "Authorization is not ready."},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "AUTHORIZATION_NOT_READY", "message": "Authorization is not ready."},
        ) from exc

    resources = await resolve_resources(
        session,
        resource_type=resource_type,
        resource_ids=resource_ids,
    )
    external_context = get_current_external_access_context()
    credential_can_manage_shares = external_context is None or external_context.level == EXTERNAL_ACCESS_ADMIN
    for resource_id, resource in resources.items():
        allowed = set(permissions.get(resource_id, ()))
        owns = resource.owner_id == current_user.id
        platform_admin = current_user.is_superuser is True and superuser_bypass
        can_manage_shares = False
        if collaboration.collaboration_ready:
            can_manage_shares = await user_can_manage_resource_shares(
                session,
                user=current_user,
                resource=resource,
                share_action="read",
                superuser_bypass=superuser_bypass,
            )
        derived[resource_id] = ResourceCapabilities(
            can_use=("execute" in allowed if resource.resource_type == "flow" else "read" in allowed),
            can_edit="write" in allowed and external_access_allows("write"),
            can_create_flow=(
                resource.resource_type == "project" and "write" in allowed and external_access_allows("create")
            ),
            can_delete="delete" in allowed and external_access_allows("delete"),
            can_move=(
                resource.resource_type == "flow"
                and "write" in allowed
                and (owns or platform_admin)
                and external_access_allows("write")
            ),
            can_manage_shares=can_manage_shares and credential_can_manage_shares,
            can_manage_publication=(
                resource.resource_type == "flow" and (owns or platform_admin) and external_access_allows("deploy")
            ),
        )
    return derived


async def _owned_resource_ids(
    *,
    session: AsyncSession,
    resource_type: str,
    resource_ids: list[UUID],
    user_id: UUID,
) -> set[UUID]:
    """Return requested resource IDs owned by ``user_id``."""
    lookup = _RESOURCE_OWNER_LOOKUPS.get(resource_type)
    if lookup is None or not resource_ids:
        return set()
    model, owner_attr = lookup
    resource_id_column = model.id
    owner_column = getattr(model, owner_attr)
    stmt = select(resource_id_column).where(
        col(resource_id_column).in_(resource_ids),
        owner_column == user_id,
    )
    return set((await session.exec(stmt)).all())


async def _apply_owner_permissions(
    *,
    session: AsyncSession,
    permissions: dict[UUID, list[str]],
    resource_type: str,
    resource_ids: list[UUID],
    actions: tuple[str, ...],
    user_id: UUID,
) -> dict[UUID, list[str]]:
    """Mirror route guard owner override for the UI permission endpoint."""
    normalized = {resource_id: list(permissions.get(resource_id, [])) for resource_id in resource_ids}
    if not await should_apply_owner_override():
        return normalized

    owned_ids = await _owned_resource_ids(
        session=session,
        resource_type=resource_type,
        resource_ids=resource_ids,
        user_id=user_id,
    )
    for resource_id in owned_ids:
        allowed = dict.fromkeys(normalized.get(resource_id, []))
        allowed.update(dict.fromkeys(actions))
        normalized[resource_id] = list(allowed)
    return normalized


@router.post("/permissions", response_model=EffectivePermissionsResponse)
async def get_effective_permissions(
    body: EffectivePermissionsRequest,
    current_user: CurrentActiveUser,
    session: DbSessionReadOnly,
) -> EffectivePermissionsResponse:
    """Return per-resource allowed actions for the current user.

    Use this to render the UI permission gate (greyed-out buttons etc.) without
    flooding the audit log with denied probes. Empty list for a resource_id
    means the user cannot perform any of the requested actions on that resource.
    """
    if not body.resource_ids:
        return EffectivePermissionsResponse(resource_type=body.resource_type, permissions={}, capabilities={})
    if len(body.resource_ids) > _MAX_RESOURCE_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"resource_ids capped at {_MAX_RESOURCE_IDS}",
        )

    actor = await load_active_user(session, current_user.id)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    authz = get_authorization_service()
    actions = tuple(body.actions) if body.actions else _DEFAULT_ACTIONS
    permissions = await authz.get_effective_permissions(
        user_id=current_user.id,
        resource_type=body.resource_type,
        resource_ids=body.resource_ids,
        actions=actions,
        domain=body.domain,
        context={
            **current_auth_context_for_authz(),
            "is_superuser": current_user.is_superuser,
        },
    )
    permissions = await _apply_owner_permissions(
        session=session,
        permissions=permissions,
        resource_type=body.resource_type,
        resource_ids=body.resource_ids,
        actions=actions,
        user_id=current_user.id,
    )
    permissions = {
        resource_id: filter_actions_by_external_access_ceiling(allowed_actions)
        for resource_id, allowed_actions in permissions.items()
    }
    capabilities = await _derive_resource_capabilities(
        session=session,
        current_user=actor,
        resource_type=body.resource_type,
        resource_ids=body.resource_ids,
        permissions=permissions,
    )
    return EffectivePermissionsResponse(
        resource_type=body.resource_type,
        permissions=permissions,
        capabilities=capabilities,
    )
