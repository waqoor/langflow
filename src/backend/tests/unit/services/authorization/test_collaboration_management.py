"""Real-database coverage for native team and sharing collaboration."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from langflow.api.v1 import authz_capabilities, authz_recipients
from langflow.services import deps as langflow_deps
from langflow.services.authorization import collaboration, share_management, team_management
from langflow.services.authorization.concurrency import strong_etag
from langflow.services.authorization.service import LangflowAuthorizationService
from langflow.services.database.models.auth import (
    AuthzAuditLog,
    AuthzRole,
    AuthzRoleAssignment,
    AuthzShare,
    AuthzTeam,
    AuthzTeamMember,
    SharePermissionLevel,
    ShareScope,
    TeamRole,
)
from langflow.services.database.models.flow.model import Flow
from langflow.services.database.models.folder.model import Folder
from langflow.services.database.models.user.model import User
from lfx.services import deps as lfx_deps
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@dataclass(frozen=True, slots=True)
class CollaborationDatabase:
    engine: AsyncEngine
    service: LangflowAuthorizationService
    dialect: str

    def session(self) -> AsyncSession:
        return AsyncSession(self.engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def collaboration_db(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> AsyncIterator[CollaborationDatabase]:
    """Install the production enforcer over the selected real database."""
    database_url = os.getenv("LANGFLOW_AUTHZ_TEST_DATABASE_URI")
    if database_url is None:
        database_url = f"sqlite+aiosqlite:///{tmp_path / 'collaboration.db'}"
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    connect_args = {"check_same_thread": False, "timeout": 30} if database_url.startswith("sqlite") else {}
    engine = create_async_engine(database_url, connect_args=connect_args)
    tables = [
        User.__table__,
        Folder.__table__,
        Flow.__table__,
        AuthzRole.__table__,
        AuthzRoleAssignment.__table__,
        AuthzTeam.__table__,
        AuthzTeamMember.__table__,
        AuthzShare.__table__,
        AuthzAuditLog.__table__,
    ]
    async with engine.begin() as connection:
        await connection.run_sync(lambda sync_connection: SQLModel.metadata.create_all(sync_connection, tables=tables))

    settings = SimpleNamespace(
        auth_settings=SimpleNamespace(
            AUTHZ_ENABLED=True,
            AUTHZ_SUPERUSER_BYPASS=True,
            AUTHZ_AUDIT_ENABLED=False,
            AUTHZ_AUDIT_DURABLE=False,
        )
    )
    service = LangflowAuthorizationService(settings)

    @asynccontextmanager
    async def session_scope_readonly() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    monkeypatch.setattr(lfx_deps, "session_scope_readonly", session_scope_readonly)
    monkeypatch.setattr(langflow_deps, "get_authorization_service", lambda: service)
    monkeypatch.setattr(collaboration, "get_authorization_service", lambda: service)
    monkeypatch.setattr(team_management, "get_authorization_service", lambda: service)
    monkeypatch.setattr(team_management, "get_settings_service", lambda: settings)

    try:
        database = CollaborationDatabase(engine=engine, service=service, dialect=engine.dialect.name)
        expected_dialect = os.getenv("LANGFLOW_AUTHZ_EXPECTED_DIALECT")
        if expected_dialect is not None:
            assert database.dialect == expected_dialect
        yield database
    finally:
        await engine.dispose()


def _user(label: str, *, is_active: bool = True, is_superuser: bool = False) -> User:
    return User(
        username=f"{label}-{uuid4()}",
        password=str(uuid4()),
        is_active=is_active,
        is_superuser=is_superuser,
    )


async def _seed_users(database: CollaborationDatabase, *users: User) -> tuple[UUID, ...]:
    async with database.session() as session:
        session.add_all(users)
        await session.commit()
    return tuple(user.id for user in users)


@pytest.mark.asyncio
async def test_team_mutations_enforce_real_roster_and_role_invariants(collaboration_db: CollaborationDatabase):
    platform = _user("platform", is_superuser=True)
    admin = _user("admin")
    maintainer = _user("maintainer")
    ordinary = _user("ordinary")
    extra = _user("extra")
    await _seed_users(collaboration_db, platform, admin, maintainer, ordinary, extra)

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        with pytest.raises(team_management.TeamManagementError) as exc_info:
            await team_management.create_team(
                session,
                actor=actor,
                team_name="No admin",
                adom_name=f"no-admin-{uuid4()}",
                description=None,
                is_active=True,
                members=(team_management.MemberUpsert(ordinary.id, TeamRole.USER.value),),
            )
        assert exc_info.value.code == "TEAM_ACTIVE_ADMIN_REQUIRED"
        await session.rollback()

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        created = await team_management.create_team(
            session,
            actor=actor,
            team_name="Runtime",
            adom_name=f"runtime-{uuid4()}",
            description="Production team",
            is_active=True,
            members=(
                team_management.MemberUpsert(admin.id, TeamRole.ADMIN.value),
                team_management.MemberUpsert(maintainer.id, TeamRole.MAINTAINER.value),
                team_management.MemberUpsert(ordinary.id, TeamRole.USER.value),
            ),
        )
        team_id = created.team.id
        assert created.counts.member_count == 3
        assert created.counts.active_admin_count == 1
        await session.commit()

    async with collaboration_db.session() as session:
        assert await team_management.team_is_valid_recipient(session, team_id)
        audit_actions = set((await session.exec(select(AuthzAuditLog.action))).all())
        assert {"team:create", "team_member:add"} <= audit_actions

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        with pytest.raises(team_management.TeamManagementError) as exc_info:
            await team_management.change_member_role(
                session,
                actor=actor,
                team_id=team_id,
                user_id=admin.id,
                role=TeamRole.USER.value,
            )
        assert exc_info.value.code == "TEAM_LAST_ACTIVE_ADMIN"
        await session.rollback()

    async with collaboration_db.session() as session:
        actor = await session.get(User, maintainer.id)
        assert actor is not None
        with pytest.raises(team_management.TeamManagementError) as exc_info:
            await team_management.add_member(
                session,
                actor=actor,
                team_id=team_id,
                member=team_management.MemberUpsert(extra.id, TeamRole.ADMIN.value),
            )
        assert exc_info.value.code == "TEAM_OPERATION_FORBIDDEN"
        await session.rollback()

    async with collaboration_db.session() as session:
        actor = await session.get(User, maintainer.id)
        assert actor is not None
        added = await team_management.add_member(
            session,
            actor=actor,
            team_id=team_id,
            member=team_management.MemberUpsert(extra.id, TeamRole.USER.value),
        )
        assert added.member.role == TeamRole.USER.value
        await session.commit()

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        await team_management.patch_team(
            session,
            actor=actor,
            team_id=team_id,
            patch=team_management.TeamPatch(is_active=False),
        )
        await session.commit()
        assert not await team_management.team_is_valid_recipient(session, team_id)


@pytest.mark.asyncio
async def test_concurrent_final_admin_demotions_commit_only_one_valid_result(
    collaboration_db: CollaborationDatabase,
):
    platform = _user("platform", is_superuser=True)
    first_admin = _user("first-admin")
    second_admin = _user("second-admin")
    await _seed_users(collaboration_db, platform, first_admin, second_admin)

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        created = await team_management.create_team(
            session,
            actor=actor,
            team_name=f"concurrent-{uuid4()}",
            adom_name=f"concurrent-{uuid4()}",
            description=None,
            is_active=True,
            members=(
                team_management.MemberUpsert(first_admin.id, TeamRole.ADMIN.value),
                team_management.MemberUpsert(second_admin.id, TeamRole.ADMIN.value),
            ),
        )
        team_id = created.team.id
        await session.commit()

    async def demote(user_id: UUID) -> str:
        async with collaboration_db.session() as session:
            actor = await session.get(User, platform.id)
            assert actor is not None
            try:
                await team_management.change_member_role(
                    session,
                    actor=actor,
                    team_id=team_id,
                    user_id=user_id,
                    role=TeamRole.USER.value,
                )
                await session.commit()
            except team_management.TeamManagementError as exc:
                await session.rollback()
                return exc.code
            return "committed"

    outcomes = await asyncio.gather(demote(first_admin.id), demote(second_admin.id))
    assert sorted(outcomes) == ["TEAM_LAST_ACTIVE_ADMIN", "committed"]

    async with collaboration_db.session() as session:
        counts = await team_management.team_roster_counts(session, team_id)
        assert counts.member_count == 2
        assert counts.active_admin_count == 1


@pytest.mark.asyncio
async def test_capabilities_endpoint_reports_only_ready_native_service_contract(
    collaboration_db: CollaborationDatabase,
):
    platform = _user("platform", is_superuser=True)
    await _seed_users(collaboration_db, platform)

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        result = await authz_capabilities.get_authorization_capabilities(
            current_user=actor,
            session=session,
        )

    assert result.enforcement_active is True
    assert result.service_ready is True
    assert result.team_roles_supported is True
    assert result.user_team_sharing_supported is True
    assert result.share_modes == ["execute", "write"]
    assert result.conditional_writes_required is True
    assert result.can_administer_platform is True
    assert result.can_create_team is True

    collaboration_db.service.settings_service.auth_settings.AUTHZ_SUPERUSER_BYPASS = False
    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        restricted = await authz_capabilities.get_authorization_capabilities(
            current_user=actor,
            session=session,
        )

    assert restricted.can_administer_platform is False
    assert restricted.can_create_team is False


@pytest.mark.asyncio
async def test_recipient_lookup_is_authorized_and_filters_inactive_users(
    collaboration_db: CollaborationDatabase,
):
    platform = _user("platform", is_superuser=True)
    ordinary = _user("ordinary")
    active_match = _user("eligible-recipient")
    inactive_match = _user("eligible-inactive", is_active=False)
    await _seed_users(collaboration_db, platform, ordinary, active_match, inactive_match)

    async with collaboration_db.session() as session:
        actor = await session.get(User, ordinary.id)
        assert actor is not None
        with pytest.raises(HTTPException) as exc_info:
            await authz_recipients.search_authorization_recipients(
                current_user=actor,
                session=session,
                purpose="team_membership",
                kind="user",
                q="eligible",
            )
        assert exc_info.value.status_code == 403

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        page = await authz_recipients.search_authorization_recipients(
            current_user=actor,
            session=session,
            purpose="team_membership",
            kind="user",
            q="eligible",
            limit=20,
            offset=0,
        )

    assert [(item.id, item.display_name) for item in page.items] == [(active_match.id, active_match.username)]
    assert page.has_more is False
    assert page.next_offset is None


@pytest.mark.asyncio
async def test_native_service_enforces_direct_team_and_project_inherited_shares(
    collaboration_db: CollaborationDatabase,
):
    platform = _user("platform", is_superuser=True)
    owner = _user("owner")
    runner = _user("runner")
    editor = _user("editor")
    team_admin = _user("team-admin")
    await _seed_users(collaboration_db, platform, owner, runner, editor, team_admin)

    async with collaboration_db.session() as session:
        actor = await session.get(User, platform.id)
        assert actor is not None
        team_result = await team_management.create_team(
            session,
            actor=actor,
            team_name="Editors",
            adom_name=f"editors-{uuid4()}",
            description=None,
            is_active=True,
            members=(
                team_management.MemberUpsert(team_admin.id, TeamRole.ADMIN.value),
                team_management.MemberUpsert(editor.id, TeamRole.USER.value),
            ),
        )
        project = Folder(name=f"project-{uuid4()}", user_id=owner.id)
        sibling_project = Folder(name=f"sibling-{uuid4()}", user_id=owner.id)
        session.add_all([project, sibling_project])
        await session.flush()
        flow = Flow(name=f"flow-{uuid4()}", user_id=owner.id, folder_id=project.id, data={})
        sibling = Flow(name=f"sibling-flow-{uuid4()}", user_id=owner.id, folder_id=sibling_project.id, data={})
        session.add_all([flow, sibling])
        await session.flush()
        await share_management.create_share(
            session,
            actor_id=owner.id,
            resource_type="flow",
            resource_id=flow.id,
            scope=ShareScope.USER.value,
            target_id=runner.id,
            permission_level=SharePermissionLevel.EXECUTE.value,
        )
        await share_management.create_share(
            session,
            actor_id=owner.id,
            resource_type="project",
            resource_id=project.id,
            scope=ShareScope.TEAM.value,
            target_id=team_result.team.id,
            permission_level=SharePermissionLevel.WRITE.value,
        )
        team_id = team_result.team.id
        flow_id = flow.id
        sibling_id = sibling.id
        await session.commit()

    service = collaboration_db.service
    for action in ("read", "execute"):
        assert await service.enforce(user_id=runner.id, domain="*", obj=f"flow:{flow_id}", act=action)
    for action in ("write", "delete"):
        assert not await service.enforce(user_id=runner.id, domain="*", obj=f"flow:{flow_id}", act=action)

    for action in ("read", "write", "execute"):
        assert await service.enforce(user_id=editor.id, domain="*", obj=f"flow:{flow_id}", act=action)
    assert not await service.enforce(user_id=editor.id, domain="*", obj=f"flow:{flow_id}", act="delete")
    assert not await service.enforce(user_id=editor.id, domain="*", obj=f"flow:{sibling_id}", act="read")

    async with collaboration_db.session() as session:
        actor = await session.get(User, team_admin.id)
        assert actor is not None
        await team_management.remove_member(session, actor=actor, team_id=team_id, user_id=editor.id)
        await session.commit()

    assert not await service.enforce(user_id=editor.id, domain="*", obj=f"flow:{flow_id}", act="read")


@pytest.mark.asyncio
async def test_share_mutation_revision_recipient_and_audit_contract(collaboration_db: CollaborationDatabase):
    owner = _user("owner")
    recipient = _user("recipient")
    inactive = _user("inactive", is_active=False)
    await _seed_users(collaboration_db, owner, recipient, inactive)

    async with collaboration_db.session() as session:
        project = Folder(name=f"project-{uuid4()}", user_id=owner.id)
        session.add(project)
        await session.flush()
        flow = Flow(name=f"flow-{uuid4()}", user_id=owner.id, folder_id=project.id, data={})
        session.add(flow)
        await session.commit()
        flow_id = flow.id

    async with collaboration_db.session() as session:
        with pytest.raises(share_management.ShareManagementError) as exc_info:
            await share_management.create_share(
                session,
                actor_id=owner.id,
                resource_type="flow",
                resource_id=flow_id,
                scope=ShareScope.USER.value,
                target_id=inactive.id,
                permission_level=SharePermissionLevel.EXECUTE.value,
            )
        assert exc_info.value.code == "SHARE_RECIPIENT_INELIGIBLE"
        await session.rollback()

    async with collaboration_db.session() as session:
        created = await share_management.create_share(
            session,
            actor_id=owner.id,
            resource_type="flow",
            resource_id=flow_id,
            scope=ShareScope.USER.value,
            target_id=recipient.id,
            permission_level=SharePermissionLevel.EXECUTE.value,
        )
        share_id = created.row.id
        initial_etag = strong_etag("share", share_id, created.row.revision)
        await session.commit()

    async with collaboration_db.session() as session:
        with pytest.raises(share_management.ShareManagementError) as exc_info:
            await share_management.update_share(
                session,
                actor_id=owner.id,
                share_id=share_id,
                permission_level=SharePermissionLevel.WRITE.value,
                if_match=None,
                precondition_required=True,
            )
        assert (exc_info.value.status_code, exc_info.value.code) == (428, "PRECONDITION_REQUIRED")
        await session.rollback()

    async with collaboration_db.session() as session:
        updated = await share_management.update_share(
            session,
            actor_id=owner.id,
            share_id=share_id,
            permission_level=SharePermissionLevel.WRITE.value,
            if_match=initial_etag,
            precondition_required=True,
        )
        assert updated.row.revision == 2
        current_etag = strong_etag("share", share_id, updated.row.revision)
        await session.commit()

    async with collaboration_db.session() as session:
        with pytest.raises(share_management.ShareManagementError) as exc_info:
            await share_management.update_share(
                session,
                actor_id=owner.id,
                share_id=share_id,
                permission_level=SharePermissionLevel.EXECUTE.value,
                if_match=initial_etag,
                precondition_required=False,
            )
        assert (exc_info.value.status_code, exc_info.value.code) == (412, "SHARE_CHANGED")
        await session.rollback()

    async with collaboration_db.session() as session:
        await share_management.delete_share(
            session,
            actor_id=owner.id,
            share_id=share_id,
            if_match=current_etag,
            precondition_required=True,
        )
        await session.commit()

    async with collaboration_db.session() as session:
        assert await session.get(AuthzShare, share_id) is None
        audits = list(
            (
                await session.exec(
                    select(AuthzAuditLog).where(
                        AuthzAuditLog.resource_type == "flow",
                        AuthzAuditLog.resource_id == flow_id,
                    )
                )
            ).all()
        )
        assert [audit.action for audit in audits] == ["share:create", "share:update", "share:delete"]
        assert all(audit.details and audit.details.get("event") == "mutation" for audit in audits)
