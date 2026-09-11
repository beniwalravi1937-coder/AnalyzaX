"""
Activity Feed Application Service for Phase 19.
Generates and serves user-facing project and workspace activity feeds,
strictly separated from security audit logs and protected by authorization boundaries.
"""

from typing import Optional
from fastapi import HTTPException

from backend.app.engines.auth.permissions import Permission
from backend.app.engines.auth.repository import AuthRepository, auth_repo
from backend.app.engines.notifications.models import (
    ActivityFeedItem,
    ActivityListResponse,
    ApplicationEvent,
    ApplicationEventType,
)
from backend.app.engines.notifications.repository import (
    NotificationRepository,
    notification_repo,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.services.auth.authorization_service import AuthorizationService, authz_service


class ActivityService:
    """Manages collaborative and project activity feeds."""

    def __init__(
        self,
        repository: Optional[NotificationRepository] = None,
        authz: Optional[AuthorizationService] = None,
        auth_repository: Optional[AuthRepository] = None,
        ws_repository: Optional[WorkspaceRepository] = None,
    ):
        self._repo = repository or notification_repo
        self._authz = authz or authz_service
        self._auth_repo = auth_repository or auth_repo
        self._ws_repo = ws_repository or workspace_repo

    def record_activity(self, event: ApplicationEvent) -> Optional[ActivityFeedItem]:
        """
        Transforms an application event into a user-facing activity item.
        Excludes low-level auth events (login/logout/token) to keep feeds relevant.
        """
        # Exclude internal auth and low-value events from team activity feed
        if event.event_type in (
            ApplicationEventType.USER_LOGIN,
            ApplicationEventType.USER_LOGOUT,
            ApplicationEventType.USER_REGISTERED,
            ApplicationEventType.SECURITY_ALERT,
        ):
            return None

        actor_name = "System"
        if event.actor_user_id:
            user = self._auth_repo.get_user(event.actor_user_id)
            if user:
                actor_name = user.display_name

        action_name = event.event_type.value.replace("_", " ").title()
        description = self._format_description(event, actor_name)
        resource_name = event.metadata.get("resource_name") or event.resource_id
        deep_link = self._compute_deep_link(event)

        item = ActivityFeedItem(
            event_id=event.event_id,
            actor_user_id=event.actor_user_id,
            actor_name=actor_name,
            action=action_name,
            description=description,
            workspace_id=event.workspace_id,
            project_id=event.project_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            resource_name=resource_name,
            deep_link=deep_link,
            timestamp=event.timestamp,
            metadata=event.metadata,
        )
        self._repo.save_activity(item)
        return item

    def get_project_activity(
        self,
        project_id: str,
        requesting_user_id: str,
        page: int = 1,
        page_size: int = 20,
        actor: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        event_type: Optional[ApplicationEventType] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ActivityListResponse:
        """Retrieves paginated activity for a project, enforcing project read permission."""
        project = self._ws_repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Invariant: User must have project read permission
        if not self._authz.can(requesting_user_id, Permission.PROJECT_READ, project_id=project_id):
            raise HTTPException(status_code=403, detail="Permission denied to access project activity")

        eff_limit = limit or page_size
        eff_page = page
        if cursor:
            try:
                eff_page = int(cursor)
            except ValueError:
                eff_page = 1
        eff_actor = actor or actor_user_id

        items, total = self._repo.list_project_activity(
            project_id=project_id,
            page=eff_page,
            page_size=eff_limit,
            actor=eff_actor,
            resource_type=resource_type,
        )
        has_more = (eff_page * eff_limit) < total
        next_cursor = str(eff_page + 1) if has_more else None

        return ActivityListResponse(
            items=items,
            total=total,
            total_count=total,
            page=eff_page,
            page_size=eff_limit,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    def get_workspace_activity(
        self,
        workspace_id: str,
        requesting_user_id: str,
        page: int = 1,
        page_size: int = 20,
        actor: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        event_type: Optional[ApplicationEventType] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ActivityListResponse:
        """Retrieves paginated activity for a workspace, enforcing workspace read permission."""
        workspace = self._ws_repo.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        if not self._authz.can(requesting_user_id, Permission.WORKSPACE_READ, workspace_id=workspace_id):
            raise HTTPException(status_code=403, detail="Permission denied to access workspace activity")

        eff_limit = limit or page_size
        eff_page = page
        if cursor:
            try:
                eff_page = int(cursor)
            except ValueError:
                eff_page = 1
        eff_actor = actor or actor_user_id

        items, total = self._repo.list_workspace_activity(
            workspace_id=workspace_id,
            page=eff_page,
            page_size=eff_limit,
            actor=eff_actor,
            resource_type=resource_type,
        )
        has_more = (eff_page * eff_limit) < total
        next_cursor = str(eff_page + 1) if has_more else None

        return ActivityListResponse(
            items=items,
            total=total,
            total_count=total,
            page=eff_page,
            page_size=eff_limit,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    def _format_description(self, event: ApplicationEvent, actor_name: str) -> str:
        r_name = event.metadata.get("resource_name") or event.resource_id or "an asset"
        et = event.event_type

        if et == ApplicationEventType.RESOURCE_SHARED:
            recipient_name = event.metadata.get("recipient_name", "team")
            return f"{actor_name} shared {r_name} with {recipient_name}."
        elif et == ApplicationEventType.RESOURCE_SHARE_REVOKED:
            return f"{actor_name} revoked share access for {r_name}."
        elif et == ApplicationEventType.MEMBER_ADDED:
            member_email = event.metadata.get("email", "new member")
            return f"{actor_name} added {member_email} to the team."
        elif et == ApplicationEventType.MEMBER_ROLE_CHANGED:
            role = event.metadata.get("role", "updated role")
            return f"{actor_name} changed member role to {role}."
        elif et == ApplicationEventType.EXPORT_COMPLETED:
            return f"Export for {r_name} completed successfully."
        elif et == ApplicationEventType.REPORT_CREATED:
            return f"{actor_name} created report '{r_name}'."
        elif et == ApplicationEventType.DASHBOARD_CREATED:
            return f"{actor_name} created dashboard '{r_name}'."
        elif et == ApplicationEventType.DASHBOARD_UPDATED:
            return f"{actor_name} updated dashboard '{r_name}'."
        elif et == ApplicationEventType.DATASET_CREATED:
            return f"{actor_name} uploaded dataset '{r_name}'."
        elif et == ApplicationEventType.ML_EXPERIMENT_COMPLETED:
            return f"ML training for '{r_name}' completed."
        elif et == ApplicationEventType.FORECAST_COMPLETED:
            return f"Forecast predictions generated for '{r_name}'."
        return f"{actor_name} performed {et.value.replace('_', ' ').lower()} on {r_name}."

    def _compute_deep_link(self, event: ApplicationEvent) -> Optional[str]:
        if not event.resource_type or not event.resource_id:
            return None
        rtype = event.resource_type.upper()
        if rtype == "DASHBOARD":
            return f"/dashboard/{event.resource_id}"
        elif rtype == "REPORT":
            return "/reports"
        elif rtype == "EXPORT":
            return "/exports"
        elif rtype in ("DATASET", "DATASET_VERSION"):
            return "/dataset"
        elif rtype in ("ML_RESULT", "ML_EXPERIMENT"):
            return "/ml"
        elif rtype in ("FORECAST_RESULT", "FORECAST_EXPERIMENT"):
            return "/forecasting"
        return None


# Singleton instance
activity_service = ActivityService()
