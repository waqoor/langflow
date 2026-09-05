"""Canonical database reads used by native authorization enforcement.

This module intentionally has no cache and no second policy store. Every new
admission reads committed Langflow rows, which makes a committed share/team
revocation authoritative across workers without an invalidation broadcast.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from lfx.services.authorization.base import ResourceVisibilityScope
from sqlalchemy import or_, update
from sqlmodel import col, select

from langflow.services.authorization.policy import project_flow_actions, share_actions
from langflow.services.database.models.auth import (
    AuthzRole,
    AuthzRoleAssignment,
    AuthzShare,
    AuthzTeam,
    AuthzTeamMember,
)
from langflow.services.database.models.deployment.model import Deployment
from langflow.services.database.models.deployment_provider_account.model import DeploymentProviderAccount
from langflow.services.database.models.file.model import File
from langflow.services.database.models.flow.model import Flow
from langflow.services.database.models.folder.model import Folder
from langflow.services.database.models.knowledge_base.model import KnowledgeBaseRecord
from langflow.services.database.models.memory_base.model import MemoryBase
from langflow.services.database.models.user.model import User
from langflow.services.database.models.variable.model import Variable

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from uuid import UUID

    from sqlmodel.ext.asyncio.session import AsyncSession


@dataclass(frozen=True, slots=True)
class ResourceRecord:
    """Server-resolved, non-secret scope for one authorization object."""

    resource_type: str
    resource_id: UUID
    owner_id: UUID | None
    project_id: UUID | None = None
    workspace_id: UUID | None = None
    display_name: str | None = None


@dataclass(frozen=True, slots=True)
class AccessSource:
    """Bounded explanation for one effective access source."""

    kind: str
    actions: tuple[str, ...]
    source_id: UUID | None = None
    label: str | None = None


@dataclass(frozen=True, slots=True)
class EffectiveAccess:
    """Allowed actions and their non-secret provenance."""

    actions: frozenset[str]
    sources: tuple[AccessSource, ...]


@dataclass(frozen=True, slots=True)
class ShareManagementScopes:
    """Compact canonical scopes whose role permits share administration."""

    all_resources: bool = False
    workspace_ids: tuple[UUID, ...] = ()
    project_ids: tuple[UUID, ...] = ()


_MODEL_BY_RESOURCE: dict[str, type[Any]] = {
    "flow": Flow,
    "project": Folder,
    "deployment": Deployment,
    "knowledge_base": KnowledgeBaseRecord,
    "variable": Variable,
    "file": File,
    "provider_account": DeploymentProviderAccount,
}

_RESOURCE_ACTIONS: dict[str, frozenset[str]] = {
    "flow": frozenset({"read", "write", "create", "delete", "execute", "deploy"}),
    "project": frozenset({"read", "write", "create", "delete"}),
    "deployment": frozenset({"read", "write", "create", "delete", "execute"}),
    "knowledge_base": frozenset({"read", "write", "create", "delete", "ingest"}),
    "variable": frozenset({"read", "write", "create", "delete"}),
    "file": frozenset({"read", "write", "create", "delete"}),
    "provider_account": frozenset({"read", "write", "create", "delete"}),
    "voice": frozenset({"read"}),
}


def supported_actions(resource_type: str) -> frozenset[str]:
    """Return the canonical action vocabulary for a resource family."""
    return _RESOURCE_ACTIONS.get(resource_type, frozenset())


def role_permission_allows(permissions: Iterable[str], *, resource_type: str, action: str) -> bool:
    """Match one canonical role permission, including its resource wildcard.

    The role API deliberately accepts ``<resource>:*``. Runtime policy must
    therefore expand that value rather than exposing the literal ``*`` as an
    effective action or silently treating the persisted permission as inert.
    """
    permission_set = permissions if isinstance(permissions, (set, frozenset)) else set(permissions)
    return f"{resource_type}:{action}" in permission_set or f"{resource_type}:*" in permission_set


def role_permission_actions(permissions: Iterable[str], *, resource_type: str) -> frozenset[str]:
    """Return concrete supported actions granted by role permission slugs."""
    supported = supported_actions(resource_type)
    return frozenset(
        action
        for action in supported
        if role_permission_allows(permissions, resource_type=resource_type, action=action)
    )


async def load_active_user(session: AsyncSession, user_id: UUID) -> User | None:
    """Return a canonical active user, never a request-supplied identity view."""
    user = await session.get(User, user_id)
    return user if user is not None and user.is_active is True else None


async def load_resource(
    session: AsyncSession,
    *,
    resource_type: str,
    resource_id: UUID,
    lock: bool = False,
) -> ResourceRecord | None:
    """Resolve one supported resource without loading graph/credential content."""
    model = _MODEL_BY_RESOURCE.get(resource_type)
    if model is None:
        return None
    if lock and session.get_bind().dialect.name == "sqlite":
        # SQLite ignores SELECT FOR UPDATE.  A no-op write establishes its
        # database-wide write transaction before the canonical resource read,
        # matching the ordered parent-row lock used by team mutations.
        await session.exec(update(model).where(model.id == resource_id).values(id=model.id))
    statement = select(model).where(model.id == resource_id)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    row = (await session.exec(statement)).first()
    if row is None and resource_type == "knowledge_base":
        fallback = select(MemoryBase).where(MemoryBase.id == resource_id)
        if lock:
            fallback = fallback.with_for_update()
        row = (await session.exec(fallback)).first()
    if row is None:
        return None
    return _resource_record_from_row(resource_type, row)


def _resource_record_from_row(resource_type: str, row: Any) -> ResourceRecord | None:
    """Project an ORM row into the only non-secret fields policy may use."""
    if resource_type == "flow":
        return ResourceRecord(
            resource_type=resource_type,
            resource_id=row.id,
            owner_id=row.user_id,
            project_id=row.folder_id,
            workspace_id=row.workspace_id,
            display_name=row.name,
        )
    if resource_type == "project":
        return ResourceRecord(
            resource_type=resource_type,
            resource_id=row.id,
            owner_id=row.user_id,
            project_id=row.id,
            workspace_id=row.workspace_id,
            display_name=row.name,
        )
    if resource_type == "deployment":
        return ResourceRecord(
            resource_type=resource_type,
            resource_id=row.id,
            owner_id=row.user_id,
            project_id=row.project_id,
            workspace_id=row.workspace_id,
            display_name=row.display_name,
        )
    if resource_type == "knowledge_base":
        return ResourceRecord(resource_type, row.id, row.user_id, display_name=row.name)
    if resource_type == "variable":
        return ResourceRecord(resource_type, row.id, row.user_id, display_name=row.name)
    if resource_type == "file":
        return ResourceRecord(resource_type, row.id, row.user_id, display_name=row.name)
    if resource_type == "provider_account":
        return ResourceRecord(resource_type, row.id, row.user_id, display_name=row.name)
    return None


async def active_team_ids_for_user(session: AsyncSession, user_id: UUID) -> tuple[UUID, ...]:
    """Return memberships in active teams that still have an active Admin."""
    statement = (
        select(AuthzTeamMember.team_id)
        .join(AuthzTeam, col(AuthzTeam.id) == col(AuthzTeamMember.team_id))
        .join(User, col(User.id) == col(AuthzTeamMember.user_id))
        .where(
            AuthzTeamMember.user_id == user_id,
            AuthzTeam.is_active == True,  # noqa: E712
            User.is_active == True,  # noqa: E712
        )
        .order_by(col(AuthzTeamMember.team_id))
    )
    candidate_ids = tuple((await session.exec(statement)).all())
    if not candidate_ids:
        return ()
    valid_ids = set(
        (
            await session.exec(
                select(AuthzTeamMember.team_id)
                .join(User, col(User.id) == col(AuthzTeamMember.user_id))
                .where(
                    col(AuthzTeamMember.team_id).in_(candidate_ids),
                    AuthzTeamMember.role == "admin",
                    User.is_active == True,  # noqa: E712
                )
            )
        ).all()
    )
    return tuple(team_id for team_id in candidate_ids if team_id in valid_ids)


async def invalid_team_ids(session: AsyncSession) -> tuple[UUID, ...]:
    """Return teams that violate the non-empty/active-Admin runtime contract."""
    teams = list((await session.exec(select(AuthzTeam).order_by(col(AuthzTeam.id)))).all())
    if not teams:
        return ()
    members = list(
        (
            await session.exec(
                select(AuthzTeamMember)
                .where(col(AuthzTeamMember.team_id).in_([team.id for team in teams]))
                .order_by(col(AuthzTeamMember.team_id))
            )
        ).all()
    )
    active_user_ids = (
        set(
            (
                await session.exec(
                    select(User.id).where(
                        col(User.id).in_([member.user_id for member in members]),
                        User.is_active == True,  # noqa: E712
                    )
                )
            ).all()
        )
        if members
        else set()
    )
    by_team: dict[UUID, list[AuthzTeamMember]] = {}
    for member in members:
        by_team.setdefault(member.team_id, []).append(member)
    invalid: list[UUID] = []
    for team in teams:
        roster = by_team.get(team.id, [])
        if not roster or (
            team.is_active is True
            and not any(member.role == "admin" and member.user_id in active_user_ids for member in roster)
        ):
            invalid.append(team.id)
    return tuple(invalid)


async def membership_for_team(
    session: AsyncSession,
    *,
    user_id: UUID,
    team_id: UUID,
) -> AuthzTeamMember | None:
    """Load one canonical membership; callers separately validate team state."""
    statement = select(AuthzTeamMember).where(
        AuthzTeamMember.user_id == user_id,
        AuthzTeamMember.team_id == team_id,
    )
    return (await session.exec(statement)).first()


def _share_applies(row: AuthzShare, *, user_id: UUID, active_team_ids: set[UUID]) -> bool:
    if row.scope == "public":
        # Anonymous/direct-link publication has a separate admission path and
        # must not make public flows discoverable in authenticated collections.
        return False
    if row.scope == "user":
        return row.target_id == user_id
    if row.scope == "team":
        return row.target_id in active_team_ids
    return False


async def _applicable_share_rows(
    session: AsyncSession,
    *,
    user_id: UUID,
    resource: ResourceRecord,
) -> tuple[AuthzShare, ...]:
    direct = (col(AuthzShare.resource_type) == resource.resource_type) & (
        col(AuthzShare.resource_id) == resource.resource_id
    )
    predicates = [direct]
    if resource.resource_type == "flow" and resource.project_id is not None:
        predicates.append(
            (col(AuthzShare.resource_type) == "project") & (col(AuthzShare.resource_id) == resource.project_id)
        )
    statement = select(AuthzShare).where(or_(*predicates)).order_by(col(AuthzShare.id))
    rows = (await session.exec(statement)).all()
    team_ids = set(await active_team_ids_for_user(session, user_id))
    return tuple(row for row in rows if _share_applies(row, user_id=user_id, active_team_ids=team_ids))


def _assignment_applies(assignment: AuthzRoleAssignment, role: AuthzRole, resource: ResourceRecord) -> bool:
    if role.workspace_id is not None and role.workspace_id != resource.workspace_id:
        return False
    if assignment.domain_type == "global":
        return assignment.domain_id is None
    if assignment.domain_type == "workspace":
        return assignment.domain_id is not None and assignment.domain_id == resource.workspace_id
    if assignment.domain_type == "project":
        return assignment.domain_id is not None and assignment.domain_id == resource.project_id
    # An organization domain requires a registered resolver; this native
    # single-instance implementation does not treat it as global authority.
    return False


def _role_permissions(
    role_id: UUID,
    *,
    role_by_id: dict[UUID, AuthzRole],
    max_depth: int = 32,
) -> frozenset[str]:
    permissions: set[str] = set()
    seen: set[UUID] = set()
    current_id: UUID | None = role_id
    for _ in range(max_depth):
        if current_id is None:
            return frozenset(permissions)
        if current_id in seen:
            return frozenset()
        seen.add(current_id)
        role = role_by_id.get(current_id)
        if role is None:
            return frozenset()
        permissions.update(permission for permission in role.permissions if isinstance(permission, str))
        current_id = role.parent_role_id
    # A chain that exceeds the bound is malformed and grants nothing.
    return frozenset()


async def applicable_role_permissions(
    session: AsyncSession,
    *,
    user_id: UUID,
    resource: ResourceRecord,
) -> tuple[frozenset[str], tuple[AccessSource, ...]]:
    """Resolve assignment scopes and bounded parent-role inheritance."""
    assignments = (
        await session.exec(
            select(AuthzRoleAssignment)
            .where(AuthzRoleAssignment.user_id == user_id)
            .order_by(col(AuthzRoleAssignment.id))
        )
    ).all()
    if not assignments:
        return frozenset(), ()
    roles = (await session.exec(select(AuthzRole))).all()
    role_by_id = {role.id: role for role in roles}
    permissions: set[str] = set()
    sources: list[AccessSource] = []
    for assignment in assignments:
        role = role_by_id.get(assignment.role_id)
        if role is None or not _assignment_applies(assignment, role, resource):
            continue
        resolved = _role_permissions(role.id, role_by_id=role_by_id)
        permissions.update(resolved)
        relevant = tuple(sorted(role_permission_actions(resolved, resource_type=resource.resource_type)))
        if relevant:
            sources.append(AccessSource("role", relevant, assignment.id, role.name))
    return frozenset(permissions), tuple(sources)


async def share_management_scopes(
    session: AsyncSession,
    *,
    user_id: UUID,
    action: str,
) -> ShareManagementScopes:
    """Resolve role-based share authority into SQL-filterable scope IDs."""
    assignments = (
        await session.exec(
            select(AuthzRoleAssignment)
            .where(AuthzRoleAssignment.user_id == user_id)
            .order_by(col(AuthzRoleAssignment.id))
        )
    ).all()
    if not assignments:
        return ShareManagementScopes()
    roles = (await session.exec(select(AuthzRole))).all()
    role_by_id = {role.id: role for role in roles}
    workspace_ids: set[UUID] = set()
    project_ids: set[UUID] = set()

    for assignment in assignments:
        role = role_by_id.get(assignment.role_id)
        if role is None or not role_permission_allows(
            _role_permissions(role.id, role_by_id=role_by_id),
            resource_type="share",
            action=action,
        ):
            continue
        if assignment.domain_type == "global" and assignment.domain_id is None:
            if role.workspace_id is None:
                return ShareManagementScopes(all_resources=True)
            workspace_ids.add(role.workspace_id)
            continue
        if assignment.domain_type == "workspace" and assignment.domain_id is not None:
            if role.workspace_id is None or role.workspace_id == assignment.domain_id:
                workspace_ids.add(assignment.domain_id)
            continue
        if assignment.domain_type != "project" or assignment.domain_id is None:
            continue
        project = await session.get(Folder, assignment.domain_id)
        if (
            project is not None
            and project.id is not None
            and (role.workspace_id is None or role.workspace_id == project.workspace_id)
        ):
            project_ids.add(project.id)

    return ShareManagementScopes(
        workspace_ids=tuple(sorted(workspace_ids, key=str)),
        project_ids=tuple(sorted(project_ids, key=str)),
    )


async def effective_access(
    session: AsyncSession,
    *,
    user_id: UUID,
    resource: ResourceRecord,
) -> EffectiveAccess:
    """Evaluate one resource through the canonical batched evaluator."""
    return (await effective_access_many(session, user_id=user_id, resources=(resource,)))[
        (resource.resource_type, resource.resource_id)
    ]


async def effective_access_many(
    session: AsyncSession,
    *,
    user_id: UUID,
    resources: Sequence[ResourceRecord],
) -> dict[tuple[str, UUID], EffectiveAccess]:
    """Evaluate a resource batch with a bounded set of canonical SQL reads."""
    unique = {(resource.resource_type, resource.resource_id): resource for resource in resources}
    if not unique:
        return {}

    assignments = list(
        (
            await session.exec(
                select(AuthzRoleAssignment)
                .where(AuthzRoleAssignment.user_id == user_id)
                .order_by(col(AuthzRoleAssignment.id))
            )
        ).all()
    )
    roles = list((await session.exec(select(AuthzRole).order_by(col(AuthzRole.id)))).all()) if assignments else []
    role_by_id = {role.id: role for role in roles}
    active_team_ids = set(await active_team_ids_for_user(session, user_id))

    direct_keys = tuple(unique)
    share_predicates = [
        (col(AuthzShare.resource_type) == resource_type) & (col(AuthzShare.resource_id) == resource_id)
        for resource_type, resource_id in direct_keys
    ]
    project_ids = {
        resource.project_id
        for resource in unique.values()
        if resource.resource_type == "flow" and resource.project_id is not None
    }
    share_predicates.extend(
        (col(AuthzShare.resource_type) == "project") & (col(AuthzShare.resource_id) == project_id)
        for project_id in project_ids
    )
    shares = list(
        (await session.exec(select(AuthzShare).where(or_(*share_predicates)).order_by(col(AuthzShare.id)))).all()
    )
    share_rows_by_resource: dict[tuple[str, UUID], list[AuthzShare]] = {}
    for share in shares:
        if not _share_applies(share, user_id=user_id, active_team_ids=active_team_ids):
            continue
        share_rows_by_resource.setdefault((share.resource_type, share.resource_id), []).append(share)

    parent_by_id: dict[UUID, Folder] = {}
    if project_ids:
        parents = (
            await session.exec(select(Folder).where(col(Folder.id).in_(project_ids)).order_by(col(Folder.id)))
        ).all()
        parent_by_id = {parent.id: parent for parent in parents if parent.id is not None}

    result: dict[tuple[str, UUID], EffectiveAccess] = {}
    for key, resource in unique.items():
        actions: set[str] = set()
        sources: list[AccessSource] = []
        supported = supported_actions(resource.resource_type)
        if resource.owner_id == user_id:
            actions.update(supported)
            sources.append(AccessSource("owner", tuple(sorted(supported)), resource.resource_id))

        if resource.resource_type == "flow" and resource.project_id is not None:
            parent = parent_by_id.get(resource.project_id)
            if parent is not None and parent.user_id == user_id:
                inherited = project_flow_actions("admin")
                actions.update(inherited)
                sources.append(AccessSource("project_owner", tuple(sorted(inherited)), parent.id, parent.name))

        for assignment in assignments:
            role = role_by_id.get(assignment.role_id)
            if role is None or not _assignment_applies(assignment, role, resource):
                continue
            resolved = _role_permissions(role.id, role_by_id=role_by_id)
            relevant = tuple(sorted(role_permission_actions(resolved, resource_type=resource.resource_type)))
            if relevant:
                actions.update(relevant)
                sources.append(AccessSource("role", relevant, assignment.id, role.name))

        direct_shares = share_rows_by_resource.get(key, ())
        inherited_shares = (
            share_rows_by_resource.get(("project", resource.project_id), ())
            if resource.resource_type == "flow" and resource.project_id is not None
            else ()
        )
        for share in (*direct_shares, *inherited_shares):
            if share.resource_type == resource.resource_type:
                granted = share_actions(resource.resource_type, share.permission_level)
                kind = f"{share.scope}_share"
            else:
                granted = project_flow_actions(share.permission_level)
                kind = f"inherited_{share.scope}_share"
            actions.update(granted)
            sources.append(AccessSource(kind, tuple(sorted(granted)), share.id))
        result[key] = EffectiveAccess(frozenset(actions & supported), tuple(sources[:50]))
    return result


async def user_can_manage_resource_shares(
    session: AsyncSession,
    *,
    user: User,
    resource: ResourceRecord,
    share_action: str,
    superuser_bypass: bool,
) -> bool:
    """Authorize share administration in the resource's actual scope."""
    if resource.owner_id == user.id:
        return True
    if user.is_superuser is True and superuser_bypass:
        return True
    role_permissions, _ = await applicable_role_permissions(session, user_id=user.id, resource=resource)
    return role_permission_allows(role_permissions, resource_type="share", action=share_action)


async def resource_visibility_scope(
    session: AsyncSession,
    *,
    user_id: UUID,
    resource_type: str,
    action: str,
) -> ResourceVisibilityScope:
    """Build an exact compact scope for list-query prefiltering.

    Concrete user/team shares remain IDs. Project-inherited flow access,
    project ownership, and scoped role assignments remain project/workspace
    scopes so list endpoints can filter before counting and pagination without
    first loading every resource in the installation.
    """
    if action not in supported_actions(resource_type):
        return ResourceVisibilityScope()

    assignments = list(
        (
            await session.exec(
                select(AuthzRoleAssignment)
                .where(AuthzRoleAssignment.user_id == user_id)
                .order_by(col(AuthzRoleAssignment.id))
            )
        ).all()
    )
    roles = list((await session.exec(select(AuthzRole).order_by(col(AuthzRole.id)))).all()) if assignments else []
    role_by_id = {role.id: role for role in roles}

    candidate_project_ids = {
        assignment.domain_id
        for assignment in assignments
        if assignment.domain_type == "project" and assignment.domain_id is not None
    }
    scoped_projects = (
        list(
            (
                await session.exec(
                    select(Folder).where(col(Folder.id).in_(candidate_project_ids)).order_by(col(Folder.id))
                )
            ).all()
        )
        if candidate_project_ids
        else []
    )
    project_by_id = {project.id: project for project in scoped_projects if project.id is not None}

    workspace_ids: set[UUID] = set()
    project_ids: set[UUID] = set()
    all_resources = False
    for assignment in assignments:
        role = role_by_id.get(assignment.role_id)
        if role is None:
            continue
        permissions = _role_permissions(role.id, role_by_id=role_by_id)
        if not role_permission_allows(permissions, resource_type=resource_type, action=action):
            continue
        if assignment.domain_type == "global" and assignment.domain_id is None:
            if role.workspace_id is None:
                all_resources = True
                break
            workspace_ids.add(role.workspace_id)
            continue
        if assignment.domain_type == "workspace" and assignment.domain_id is not None:
            if role.workspace_id is None or role.workspace_id == assignment.domain_id:
                workspace_ids.add(assignment.domain_id)
            continue
        if assignment.domain_type != "project" or assignment.domain_id is None:
            # Organization domains require a registered resolver and malformed
            # scope rows never become global authority.
            continue
        project = project_by_id.get(assignment.domain_id)
        if (
            project is not None
            and project.id is not None
            and (role.workspace_id is None or role.workspace_id == project.workspace_id)
        ):
            project_ids.add(project.id)

    if all_resources:
        return ResourceVisibilityScope(all_resources=True)

    active_team_ids = set(await active_team_ids_for_user(session, user_id))
    target_predicates = [
        (col(AuthzShare.scope) == "user") & (col(AuthzShare.target_id) == user_id),
    ]
    if active_team_ids:
        target_predicates.append((col(AuthzShare.scope) == "team") & col(AuthzShare.target_id).in_(active_team_ids))
    resource_predicates = [col(AuthzShare.resource_type) == resource_type]
    if resource_type == "flow":
        resource_predicates.append(col(AuthzShare.resource_type) == "project")
    shares = list(
        (
            await session.exec(
                select(AuthzShare)
                .where(or_(*target_predicates), or_(*resource_predicates))
                .order_by(col(AuthzShare.id))
            )
        ).all()
    )

    resource_ids: set[UUID] = set()
    for share in shares:
        if share.resource_type == resource_type:
            if action in share_actions(resource_type, share.permission_level):
                resource_ids.add(share.resource_id)
        elif resource_type == "flow" and action in project_flow_actions(share.permission_level):
            project_ids.add(share.resource_id)

    if resource_type == "flow" and action in project_flow_actions("admin"):
        owned_project_ids = (
            await session.exec(select(Folder.id).where(Folder.user_id == user_id).order_by(col(Folder.id)))
        ).all()
        project_ids.update(project_id for project_id in owned_project_ids if project_id is not None)

    return ResourceVisibilityScope(
        resource_ids=tuple(sorted(resource_ids, key=str)),
        workspace_ids=tuple(sorted(workspace_ids, key=str)),
        project_ids=tuple(sorted(project_ids, key=str)),
    )


async def exact_visibility_ids(
    session: AsyncSession,
    *,
    user_id: UUID,
    resource_type: str,
    action: str,
) -> tuple[UUID, ...]:
    """Materialize exact visible IDs through the same evaluator.

    The list APIs consume compact scopes where possible, but the legacy hook
    requires IDs. This compatibility path intentionally favors correctness
    over speed and is bounded by the caller's existing pagination path.
    """
    model = _MODEL_BY_RESOURCE.get(resource_type)
    if model is None:
        return ()
    ids: Iterable[UUID] = (await session.exec(select(model.id).order_by(model.id))).all()
    resources = await resolve_resources(session, resource_type=resource_type, resource_ids=tuple(ids))
    access = await effective_access_many(session, user_id=user_id, resources=tuple(resources.values()))
    return tuple(resource_id for resource_id in resources if action in access[(resource_type, resource_id)].actions)


async def all_resource_ids(session: AsyncSession, *, resource_type: str) -> tuple[UUID, ...]:
    """Return all IDs for a supported family (Platform Admin visibility)."""
    model = _MODEL_BY_RESOURCE.get(resource_type)
    if model is None:
        return ()
    return tuple((await session.exec(select(model.id).order_by(model.id))).all())


async def resolve_resources(
    session: AsyncSession,
    *,
    resource_type: str,
    resource_ids: Sequence[UUID],
) -> dict[UUID, ResourceRecord]:
    """Resolve a bounded resource batch without exposing missing IDs."""
    requested = tuple(dict.fromkeys(resource_ids))
    if not requested:
        return {}
    model = _MODEL_BY_RESOURCE.get(resource_type)
    if model is None:
        return {}
    rows = (await session.exec(select(model).where(col(model.id).in_(requested)).order_by(model.id))).all()
    resolved = {
        row.id: resource for row in rows if (resource := _resource_record_from_row(resource_type, row)) is not None
    }
    if resource_type == "knowledge_base":
        missing = tuple(resource_id for resource_id in requested if resource_id not in resolved)
        if missing:
            fallback_rows = (
                await session.exec(
                    select(MemoryBase).where(col(MemoryBase.id).in_(missing)).order_by(col(MemoryBase.id))
                )
            ).all()
            resolved.update(
                {
                    row.id: ResourceRecord("knowledge_base", row.id, row.user_id, display_name=row.name)
                    for row in fallback_rows
                }
            )
    return resolved
