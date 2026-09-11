"""
Unit tests for Phase 17 Role -> Permission Matrix (RBAC).
"""

from backend.app.engines.auth.models import RoleName
from backend.app.engines.auth.permissions import (
    ALL_PERMISSIONS,
    Permissions,
    get_role_permissions,
    has_permission,
)


def test_owner_permissions():
    owner_perms = get_role_permissions(RoleName.OWNER)
    assert owner_perms == ALL_PERMISSIONS
    assert has_permission(RoleName.OWNER, Permissions.WORKSPACE_TRANSFER_OWNERSHIP) is True
    assert has_permission(RoleName.OWNER, Permissions.WORKSPACE_MANAGE_MEMBERS) is True
    assert has_permission(RoleName.OWNER, Permissions.DATASET_DELETE) is True


def test_admin_permissions():
    admin_perms = get_role_permissions(RoleName.ADMIN)
    assert Permissions.WORKSPACE_TRANSFER_OWNERSHIP not in admin_perms
    assert has_permission(RoleName.ADMIN, Permissions.WORKSPACE_MANAGE_MEMBERS) is True
    assert has_permission(RoleName.ADMIN, Permissions.PROJECT_CREATE) is True
    assert has_permission(RoleName.ADMIN, Permissions.DATASET_DELETE) is True
    assert has_permission(RoleName.ADMIN, Permissions.AUDIT_READ) is True


def test_editor_permissions():
    editor_perms = get_role_permissions(RoleName.EDITOR)
    # Cannot administer workspace or manage members
    assert has_permission(RoleName.EDITOR, Permissions.WORKSPACE_MANAGE_MEMBERS) is False
    assert has_permission(RoleName.EDITOR, Permissions.WORKSPACE_ARCHIVE) is False
    assert has_permission(RoleName.EDITOR, Permissions.AUDIT_READ) is False
    # Can create and modify analytical assets
    assert has_permission(RoleName.EDITOR, Permissions.DATASET_CREATE) is True
    assert has_permission(RoleName.EDITOR, Permissions.DASHBOARD_CREATE) is True
    assert has_permission(RoleName.EDITOR, Permissions.VISUALIZATION_DELETE) is True
    assert has_permission(RoleName.EDITOR, Permissions.QUERY_CREATE) is True


def test_analyst_permissions():
    analyst_perms = get_role_permissions(RoleName.ANALYST)
    # Cannot delete datasets, manage members, or delete dashboards
    assert has_permission(RoleName.ANALYST, Permissions.DATASET_DELETE) is False
    assert has_permission(RoleName.ANALYST, Permissions.DASHBOARD_DELETE) is False
    assert has_permission(RoleName.ANALYST, Permissions.WORKSPACE_MANAGE_MEMBERS) is False
    # Can read datasets, run analyses, create visualizations, run SQL
    assert has_permission(RoleName.ANALYST, Permissions.DATASET_READ) is True
    assert has_permission(RoleName.ANALYST, Permissions.ANALYSIS_CREATE) is True
    assert has_permission(RoleName.ANALYST, Permissions.QUERY_CREATE) is True
    assert has_permission(RoleName.ANALYST, Permissions.EXPORT_CREATE) is True


def test_viewer_permissions():
    viewer_perms = get_role_permissions(RoleName.VIEWER)
    # Viewer has NO mutating permissions
    assert has_permission(RoleName.VIEWER, Permissions.DATASET_CREATE) is False
    assert has_permission(RoleName.VIEWER, Permissions.DATASET_DELETE) is False
    assert has_permission(RoleName.VIEWER, Permissions.DASHBOARD_CREATE) is False
    assert has_permission(RoleName.VIEWER, Permissions.REPORT_CREATE) is False
    assert has_permission(RoleName.VIEWER, Permissions.EXPORT_CREATE) is False
    assert has_permission(RoleName.VIEWER, Permissions.WORKSPACE_UPDATE) is False
    # Viewer can strictly read
    assert has_permission(RoleName.VIEWER, Permissions.WORKSPACE_READ) is True
    assert has_permission(RoleName.VIEWER, Permissions.PROJECT_READ) is True
    assert has_permission(RoleName.VIEWER, Permissions.DATASET_READ) is True
    assert has_permission(RoleName.VIEWER, Permissions.DASHBOARD_READ) is True
    assert has_permission(RoleName.VIEWER, Permissions.REPORT_READ) is True
