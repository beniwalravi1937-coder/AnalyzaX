"""
REST API Router for Project Memberships & Access (Phase 18).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user
from backend.app.engines.auth.models import User
from backend.app.engines.collaboration.models import (
    AddProjectMemberRequest,
    ProjectMemberResponse,
    UpdateProjectMemberRequest,
)
from backend.app.services.collaboration.project_access_service import project_access_service

router = APIRouter(prefix="/projects", tags=["Project Memberships"])


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: str,
    user: User = Depends(get_current_user),
) -> List[ProjectMemberResponse]:
    """Lists explicit project members."""
    return project_access_service.list_project_members(
        project_id=project_id,
        requesting_user_id=user.user_id,
    )


@router.post("/{project_id}/members", status_code=201)
def add_project_member(
    project_id: str,
    req: AddProjectMemberRequest,
    user: User = Depends(get_current_user),
):
    """Adds a workspace member to a specific project with a defined role."""
    member = project_access_service.add_project_member(
        project_id=project_id,
        target_user_id=req.user_id,
        role=req.role,
        requesting_user_id=user.user_id,
    )
    return {
        "message": "Project member added successfully",
        "membership_id": member.membership_id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role.value,
    }


@router.patch("/{project_id}/members/{target_user_id}")
def update_project_member_role(
    project_id: str,
    target_user_id: str,
    req: UpdateProjectMemberRequest,
    user: User = Depends(get_current_user),
):
    """Updates a member's role on a specific project."""
    member = project_access_service.update_project_member_role(
        project_id=project_id,
        target_user_id=target_user_id,
        new_role=req.role,
        requesting_user_id=user.user_id,
    )
    return {
        "message": "Project role updated successfully",
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role.value,
    }


@router.delete("/{project_id}/members/{target_user_id}")
def remove_project_member(
    project_id: str,
    target_user_id: str,
    user: User = Depends(get_current_user),
):
    """Removes a user's explicit access to a project."""
    project_access_service.remove_project_member(
        project_id=project_id,
        target_user_id=target_user_id,
        requesting_user_id=user.user_id,
    )
    return {"message": "Project member removed successfully"}
