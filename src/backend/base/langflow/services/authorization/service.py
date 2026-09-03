"""Native Langflow authorization service backed by canonical application rows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from lfx.log.logger import logger
from lfx.services.authorization.base import (
    BaseAuthorizationService,
    PublicAuthorizationRequest,
    PublicResourceAction,
    ResourceVisibilityScope,
)
from sqlmodel import select

from langflow.services.authorization.actions import ShareAction
from langflow.services.authorization.repository import (
    ResourceRecord,
    all_resource_ids,
    effective_access,
    effective_access_many,
    exact_visibility_ids,
    invalid_team_ids,
    load_active_user,
    load_resource,
    resolve_resources,
    resource_visibility_scope,
    supported_actions,
    user_can_manage_resource_shares,
)
from langflow.services.database.models.auth import AuthzShare

if TYPE_CHECKING:
    from collections.abc import Sequence

    from lfx.services.settings.auth import AuthSettings
    from lfx.services.settings.service import SettingsService
    from sqlmodel.ext.asyncio.session import AsyncSession


class LangflowAuthorizationService(BaseAuthorizationService):
    """Enforce roles, ownership, teams, and shares from committed Langflow data.

    Enforcement remains opt-in through ``LANGFLOW_AUTHZ_ENABLED``. When it is
    disabled, this class preserves Langflow's historical pass-through contract.
    When enabled, missing users/resources, unknown actions, and database/service
    failures deny; callers never silently fall back to the disabled behavior.
    """

    SUPPORTS_CROSS_USER_FETCH = True
    SUPPORTS_PUBLIC_PRINCIPALS = True

    def __init__(self, settings_service: SettingsService) -> None:
        super().__init__()
        self.settings_service = settings_service
        self.set_ready()
        logger.debug("Native Langflow authorization service initialized")

    def _authz_settings(self) -> AuthSettings:
        return self.settings_service.auth_settings

    def _superuser_bypass(self) -> bool:
        return bool(getattr(self._authz_settings(), "AUTHZ_SUPERUSER_BYPASS", True))

    async def is_enabled(self) -> bool:
        return bool(self._authz_settings().AUTHZ_ENABLED)

    async def supports_team_roles(self) -> bool:
        return True

    async def supports_user_team_sharing(self) -> bool:
        return True

    async def supports_conditional_writes(self) -> bool:
        return True

    async def collaboration_ready(self) -> bool:
        """Verify that the native schema can be read before advertising support."""
        if not self.ready:
            return False
        try:
            from lfx.services.deps import session_scope_readonly

            async with session_scope_readonly() as raw_session:
                session = cast("AsyncSession", raw_session)
                await session.exec(select(AuthzShare.id).limit(1))
                invalid_teams = await invalid_team_ids(session)
                if invalid_teams:
                    logger.error(
                        "Native authorization is not ready: %d team(s) violate roster invariants",
                        len(invalid_teams),
                    )
                    return False
        except Exception:  # noqa: BLE001 - capability discovery must fail closed
            logger.exception("Native authorization schema readiness check failed")
            return False
        return True

    @staticmethod
    def _parse_object(obj: str) -> tuple[str, UUID | None] | None:
        resource_type, separator, raw_id = obj.partition(":")
        if not separator or not resource_type:
            return None
        if raw_id == "*":
            return resource_type, None
        try:
            return resource_type, UUID(raw_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _canonical_voice_owner(context: dict[str, Any]) -> UUID | None:
        """Validate the server-resolved owner used for provider-backed voices."""
        raw_owner_id = context.get("voice_user_id")
        if raw_owner_id is None:
            return None
        try:
            return UUID(str(raw_owner_id))
        except (TypeError, ValueError):
            return None

    async def _virtual_creation_resource(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        resource_type: str,
        context: dict[str, Any],
    ) -> ResourceRecord | None:
        if context.get("intrinsic_creation") is not True:
            return None

        if resource_type in {"flow", "deployment"}:
            raw_project_id = context.get("folder_id") or context.get("project_id")
            if raw_project_id is None:
                return None
            try:
                project_id = UUID(str(raw_project_id))
            except (TypeError, ValueError):
                return None
            project = await load_resource(session, resource_type="project", resource_id=project_id)
            if project is None:
                return None
            return ResourceRecord(
                resource_type=resource_type,
                resource_id=UUID(int=0),
                owner_id=None,
                project_id=project.resource_id,
                workspace_id=project.workspace_id,
            )

        # These are personal create operations: the route has already selected
        # the canonical current identity and has no existing row to inspect.
        if resource_type in {
            "project",
            "knowledge_base",
            "variable",
            "file",
            "provider_account",
        }:
            return ResourceRecord(resource_type, UUID(int=0), user_id)
        return None

    async def _enforce_share_operation(
        self,
        session: AsyncSession,
        *,
        user: Any,
        share_action: str,
        context: dict[str, Any],
    ) -> bool:
        if share_action not in {action.value for action in ShareAction}:
            return False
        raw_resource_type = context.get("resource_type")
        raw_resource_id = context.get("resource_id")
        if not isinstance(raw_resource_type, str) or raw_resource_id is None:
            return False
        try:
            resource_id = UUID(str(raw_resource_id))
        except (TypeError, ValueError):
            return False
        resource = await load_resource(
            session,
            resource_type=raw_resource_type,
            resource_id=resource_id,
        )
        if resource is None:
            return False
        can_manage = await user_can_manage_resource_shares(
            session,
            user=user,
            resource=resource,
            share_action=share_action,
            superuser_bypass=self._superuser_bypass(),
        )
        if can_manage:
            return True
        if share_action != "read":
            return False
        raw_subject = context.get("subject_user_id")
        if raw_subject is not None:
            try:
                subject_id = UUID(str(raw_subject))
            except (TypeError, ValueError):
                return False
            if subject_id != user.id:
                return False
        return "read" in (await effective_access(session, user_id=user.id, resource=resource)).actions

    async def _enforce_in_session(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        obj: str,
        act: str,
        context: dict[str, Any] | None,
    ) -> bool:
        parsed = self._parse_object(obj)
        if parsed is None:
            return False
        resource_type, resource_id = parsed
        context = dict(context or {})
        user = await load_active_user(session, user_id)
        if user is None:
            return False

        if resource_type == "share":
            return await self._enforce_share_operation(
                session,
                user=user,
                share_action=act,
                context=context,
            )

        if act not in supported_actions(resource_type):
            return False

        if resource_id is None:
            # Voice records live at the provider rather than in a Langflow
            # table. The guarded route supplies the canonical credential
            # owner, so this is an owner-scoped collection read rather than an
            # unqualified wildcard grant.
            if resource_type == "voice":
                voice_owner_id = self._canonical_voice_owner(context)
                if voice_owner_id is None:
                    return False
                if user.is_superuser is True and self._superuser_bypass():
                    return True
                return act == "read" and voice_owner_id == user_id
            if act != "create":
                return False
            resource = await self._virtual_creation_resource(
                session,
                user_id=user_id,
                resource_type=resource_type,
                context=context,
            )
            if resource is None:
                return False
            if user.is_superuser is True and self._superuser_bypass():
                return True
            if resource_type not in {"flow", "deployment"}:
                return True
        else:
            resource = await load_resource(
                session,
                resource_type=resource_type,
                resource_id=resource_id,
            )
            if resource is None:
                # Voice IDs are provider data rather than Langflow rows. The
                # guarded route supplies only its canonical credential owner.
                if resource_type != "voice":
                    return False
                voice_owner_id = self._canonical_voice_owner(context)
                if voice_owner_id is None:
                    return False
                if user.is_superuser is True and self._superuser_bypass():
                    return True
                return voice_owner_id == user_id and act == "read"

        if user.is_superuser is True and self._superuser_bypass():
            return True

        return act in (await effective_access(session, user_id=user_id, resource=resource)).actions

    async def enforce(
        self,
        *,
        user_id: UUID,
        domain: str,  # noqa: ARG002 - canonical scope is resolved from database rows
        obj: str,
        act: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        if not await self.is_enabled():
            return True
        from lfx.services.deps import session_scope_readonly

        async with session_scope_readonly() as raw_session:
            session = cast("AsyncSession", raw_session)
            return await self._enforce_in_session(
                session,
                user_id=user_id,
                obj=obj,
                act=act,
                context=context,
            )

    async def batch_enforce(
        self,
        *,
        user_id: UUID,
        domain: str,  # noqa: ARG002 - each object resolves its canonical scope
        requests: Sequence[tuple[str, str]],
        context: dict[str, Any] | None = None,
    ) -> list[bool]:
        if not requests:
            return []
        if not await self.is_enabled():
            return [True] * len(requests)
        from lfx.services.deps import session_scope_readonly

        async with session_scope_readonly() as raw_session:
            session = cast("AsyncSession", raw_session)
            user = await load_active_user(session, user_id)
            if user is None:
                return [False] * len(requests)
            superuser_bypass = user.is_superuser is True and self._superuser_bypass()

            parsed = [self._parse_object(obj) for obj, _act in requests]
            ids_by_type: dict[str, list[UUID]] = {}
            for parsed_object, (_obj, act) in zip(parsed, requests, strict=True):
                if parsed_object is None:
                    continue
                resource_type, resource_id = parsed_object
                if resource_type == "share" or resource_id is None or act not in supported_actions(resource_type):
                    continue
                ids_by_type.setdefault(resource_type, []).append(resource_id)

            canonical: dict[tuple[str, UUID], ResourceRecord] = {}
            for resource_type, resource_ids in ids_by_type.items():
                resolved = await resolve_resources(
                    session,
                    resource_type=resource_type,
                    resource_ids=resource_ids,
                )
                canonical.update({(resource_type, resource_id): row for resource_id, row in resolved.items()})
            access = (
                {}
                if superuser_bypass
                else await effective_access_many(
                    session,
                    user_id=user_id,
                    resources=tuple(canonical.values()),
                )
            )

            decisions: list[bool] = []
            for parsed_object, (_obj, act) in zip(parsed, requests, strict=True):
                if parsed_object is None:
                    decisions.append(False)
                    continue
                resource_type, resource_id = parsed_object
                if resource_type == "share":
                    decisions.append(
                        await self._enforce_share_operation(
                            session,
                            user=user,
                            share_action=act,
                            context=dict(context or {}),
                        )
                    )
                    continue
                if act not in supported_actions(resource_type):
                    decisions.append(False)
                    continue
                if resource_id is None:
                    if resource_type == "voice":
                        voice_owner_id = self._canonical_voice_owner(dict(context or {}))
                        decisions.append(
                            voice_owner_id is not None
                            and (superuser_bypass or (act == "read" and voice_owner_id == user_id))
                        )
                        continue
                    if act != "create":
                        decisions.append(False)
                        continue
                    resource = await self._virtual_creation_resource(
                        session,
                        user_id=user_id,
                        resource_type=resource_type,
                        context=dict(context or {}),
                    )
                    if resource is None:
                        decisions.append(False)
                    elif superuser_bypass:
                        decisions.append(True)
                    elif resource_type in {"flow", "deployment"}:
                        decisions.append(
                            act
                            in (
                                await effective_access_many(
                                    session,
                                    user_id=user_id,
                                    resources=(resource,),
                                )
                            )[(resource_type, resource.resource_id)].actions
                        )
                    else:
                        decisions.append(True)
                    continue
                resource = canonical.get((resource_type, resource_id))
                if resource is None:
                    voice_owner_id = self._canonical_voice_owner(dict(context or {}))
                    decisions.append(
                        resource_type == "voice"
                        and voice_owner_id is not None
                        and (superuser_bypass or (voice_owner_id == user_id and act == "read"))
                    )
                    continue
                decisions.append(superuser_bypass or act in access[(resource_type, resource_id)].actions)
            return decisions

    async def get_effective_permissions(
        self,
        *,
        user_id: UUID,
        resource_type: str,
        resource_ids: Sequence[UUID],
        actions: Sequence[str],
        domain: str = "*",  # noqa: ARG002 - request domain is never authority
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> dict[UUID, list[str]]:
        if not await self.is_enabled():
            return {resource_id: list(actions) for resource_id in resource_ids}
        from lfx.services.deps import session_scope_readonly

        result: dict[UUID, list[str]] = {resource_id: [] for resource_id in resource_ids}
        async with session_scope_readonly() as raw_session:
            session = cast("AsyncSession", raw_session)
            user = await load_active_user(session, user_id)
            if user is None:
                return result
            canonical = await resolve_resources(
                session,
                resource_type=resource_type,
                resource_ids=resource_ids,
            )
            access = await effective_access_many(
                session,
                user_id=user_id,
                resources=tuple(canonical.values()),
            )
            for resource_id, resource in canonical.items():
                if user.is_superuser is True and self._superuser_bypass():
                    result[resource_id] = [action for action in actions if action in supported_actions(resource_type)]
                    continue
                allowed = access[(resource.resource_type, resource.resource_id)].actions
                result[resource_id] = [action for action in actions if action in allowed]
        return result

    async def list_visible_resource_ids(
        self,
        *,
        user_id: UUID,
        resource_type: str,
        domain: str = "*",  # noqa: ARG002
        act: str = "read",
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[UUID] | None:
        if not await self.is_enabled():
            return None
        if act not in supported_actions(resource_type):
            return []
        from lfx.services.deps import session_scope_readonly

        async with session_scope_readonly() as raw_session:
            session = cast("AsyncSession", raw_session)
            user = await load_active_user(session, user_id)
            if user is None:
                return []
            if user.is_superuser is True and self._superuser_bypass():
                return list(await all_resource_ids(session, resource_type=resource_type))
            return list(
                await exact_visibility_ids(
                    session,
                    user_id=user_id,
                    resource_type=resource_type,
                    action=act,
                )
            )

    async def get_resource_visibility(
        self,
        *,
        user_id: UUID,
        resource_type: str,
        domain: str = "*",  # noqa: ARG002 - scopes are resolved from canonical rows
        act: str = "read",
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ResourceVisibilityScope | None:
        if not await self.is_enabled():
            return None
        if act not in supported_actions(resource_type):
            return ResourceVisibilityScope()

        from lfx.services.deps import session_scope_readonly

        async with session_scope_readonly() as raw_session:
            session = cast("AsyncSession", raw_session)
            user = await load_active_user(session, user_id)
            if user is None:
                return ResourceVisibilityScope()
            if user.is_superuser is True and self._superuser_bypass():
                return ResourceVisibilityScope(all_resources=True)
            return await resource_visibility_scope(
                session,
                user_id=user_id,
                resource_type=resource_type,
                action=act,
            )

    async def resolve_public_tenant(self, request: PublicAuthorizationRequest) -> str | None:
        """Use only the already server-resolved domain hint as a local tenant."""
        return request.domain_hint if request.domain_hint else None

    async def enforce_public(self, request: PublicAuthorizationRequest, *, tenant: str) -> bool:
        if not await self.is_enabled() or tenant != request.domain_hint:
            return False
        if request.resource_type != "flow" or request.action not in {
            PublicResourceAction.READ,
            PublicResourceAction.EXECUTE,
        }:
            return False
        if request.grant_source != "authz_share":
            # Compatibility grants were resolved from the current Flow row by
            # public_access immediately before this hook.
            return request.grant_source in {"legacy_access_type", "a2a_auth_none"}

        from lfx.services.deps import session_scope_readonly

        async with session_scope_readonly() as raw_session:
            session = cast("AsyncSession", raw_session)
            statement = select(AuthzShare.permission_level).where(
                AuthzShare.resource_type == "flow",
                AuthzShare.resource_id == request.resource_id,
                AuthzShare.scope == "public",
            )
            permission = (await session.exec(statement)).first()
        if request.action is PublicResourceAction.READ:
            return permission in {"read", "execute", "write", "admin"}
        return permission in {"execute", "write", "admin"}
