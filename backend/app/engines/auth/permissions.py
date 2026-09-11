"""
Centralized Role & Permission definitions for AnalyzaX RBAC.
Defines explicit permissions and the canonical Role -> Permission matrix across:
OWNER, ADMIN, EDITOR, ANALYST, VIEWER.
"""

from typing import Dict, List, Set

from backend.app.engines.auth.models import RoleName


# ─────────────────────────────────────────────────────────────
# Canonical Permission Strings
# ─────────────────────────────────────────────────────────────

class Permissions:
    # Workspace
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_UPDATE = "workspace.update"
    WORKSPACE_ARCHIVE = "workspace.archive"
    WORKSPACE_DELETE = "workspace.delete"
    WORKSPACE_MANAGE_MEMBERS = "workspace.manage_members"
    WORKSPACE_TRANSFER_OWNERSHIP = "workspace.transfer_ownership"

    # Project
    PROJECT_READ = "project.read"
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_ARCHIVE = "project.archive"
    PROJECT_DELETE = "project.delete"

    # Dataset
    DATASET_READ = "dataset.read"
    DATASET_CREATE = "dataset.create"
    DATASET_UPDATE = "dataset.update"
    DATASET_ARCHIVE = "dataset.archive"
    DATASET_DELETE = "dataset.delete"

    # Analysis (EDA, Quality, Statistics, ML, Forecasting, AI)
    ANALYSIS_READ = "analysis.read"
    ANALYSIS_CREATE = "analysis.create"
    ANALYSIS_DELETE = "analysis.delete"

    # Visualization
    VISUALIZATION_READ = "visualization.read"
    VISUALIZATION_CREATE = "visualization.create"
    VISUALIZATION_UPDATE = "visualization.update"
    VISUALIZATION_DELETE = "visualization.delete"

    # Dashboard
    DASHBOARD_READ = "dashboard.read"
    DASHBOARD_CREATE = "dashboard.create"
    DASHBOARD_UPDATE = "dashboard.update"
    DASHBOARD_DELETE = "dashboard.delete"

    # Report
    REPORT_READ = "report.read"
    REPORT_CREATE = "report.create"
    REPORT_UPDATE = "report.update"
    REPORT_DELETE = "report.delete"

    # Export
    EXPORT_CREATE = "export.create"
    EXPORT_READ = "export.read"
    EXPORT_DELETE = "export.delete"

    # Query (SQL)
    QUERY_READ = "query.read"
    QUERY_CREATE = "query.create"
    QUERY_UPDATE = "query.update"
    QUERY_DELETE = "query.delete"

    # Audit
    AUDIT_READ = "audit.read"

    # Usage & Plans (Phase 20)
    USAGE_READ = "usage.read"
    USAGE_MANAGE = "usage.manage"
    PLAN_MANAGE = "plan.manage"

    # Billing & Subscriptions (Phase 21)
    BILLING_READ = "billing.read"
    BILLING_MANAGE = "billing.manage"
    BILLING_CHECKOUT = "billing.checkout"
    SUBSCRIPTION_CHANGE = "subscription.change"
    SUBSCRIPTION_CANCEL = "subscription.cancel"
    INVOICE_READ = "invoice.read"


# ─────────────────────────────────────────────────────────────
# Role -> Permission Matrix
# ─────────────────────────────────────────────────────────────

ALL_PERMISSIONS: Set[str] = {
    getattr(Permissions, attr)
    for attr in dir(Permissions)
    if not attr.startswith("_") and isinstance(getattr(Permissions, attr), str)
}

ROLE_PERMISSIONS: Dict[RoleName, Set[str]] = {
    RoleName.OWNER: set(ALL_PERMISSIONS),

    RoleName.ADMIN: {
        p for p in ALL_PERMISSIONS
        if p not in (Permissions.WORKSPACE_TRANSFER_OWNERSHIP, Permissions.WORKSPACE_DELETE)
    },

    RoleName.EDITOR: {
        Permissions.WORKSPACE_READ,
        Permissions.PROJECT_READ,
        Permissions.PROJECT_CREATE,
        Permissions.DATASET_READ,
        Permissions.DATASET_CREATE,
        Permissions.DATASET_UPDATE,
        Permissions.ANALYSIS_READ,
        Permissions.ANALYSIS_CREATE,
        Permissions.VISUALIZATION_READ,
        Permissions.VISUALIZATION_CREATE,
        Permissions.VISUALIZATION_UPDATE,
        Permissions.VISUALIZATION_DELETE,
        Permissions.DASHBOARD_READ,
        Permissions.DASHBOARD_CREATE,
        Permissions.DASHBOARD_UPDATE,
        Permissions.DASHBOARD_DELETE,
        Permissions.REPORT_READ,
        Permissions.REPORT_CREATE,
        Permissions.REPORT_UPDATE,
        Permissions.REPORT_DELETE,
        Permissions.EXPORT_CREATE,
        Permissions.EXPORT_READ,
        Permissions.EXPORT_DELETE,
        Permissions.QUERY_READ,
        Permissions.QUERY_CREATE,
        Permissions.QUERY_UPDATE,
        Permissions.QUERY_DELETE,
        Permissions.USAGE_READ,
    },

    RoleName.ANALYST: {
        Permissions.WORKSPACE_READ,
        Permissions.PROJECT_READ,
        Permissions.DATASET_READ,
        Permissions.ANALYSIS_READ,
        Permissions.ANALYSIS_CREATE,
        Permissions.VISUALIZATION_READ,
        Permissions.VISUALIZATION_CREATE,
        Permissions.VISUALIZATION_UPDATE,
        Permissions.DASHBOARD_READ,
        Permissions.REPORT_READ,
        Permissions.EXPORT_CREATE,
        Permissions.EXPORT_READ,
        Permissions.QUERY_READ,
        Permissions.QUERY_CREATE,
        Permissions.QUERY_UPDATE,
        Permissions.USAGE_READ,
    },

    RoleName.VIEWER: {
        Permissions.WORKSPACE_READ,
        Permissions.PROJECT_READ,
        Permissions.DATASET_READ,
        Permissions.ANALYSIS_READ,
        Permissions.VISUALIZATION_READ,
        Permissions.DASHBOARD_READ,
        Permissions.REPORT_READ,
        Permissions.EXPORT_READ,
        Permissions.QUERY_READ,
        Permissions.USAGE_READ,
    },
}


def get_role_permissions(role: RoleName) -> Set[str]:
    """Returns the set of permissions granted to a given role."""
    return ROLE_PERMISSIONS.get(role, set()).copy()


def has_permission(role: RoleName, permission: str) -> bool:
    """Checks if a role grants a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


# Aliases for convenience and compatibility
Permission = Permissions
setattr(Permissions, "WORKSPACE_MEMBERS_MANAGE", Permissions.WORKSPACE_MANAGE_MEMBERS)
setattr(Permissions, "WORKSPACE_MEMBERS_READ", Permissions.WORKSPACE_READ)

