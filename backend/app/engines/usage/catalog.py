"""
Plan Catalog and Default Entitlements for Phase 20.
Defines canonical feature keys, default tiers (FREE, PRO, TEAM, ENTERPRISE),
and entitlement specifications.
"""

from typing import Dict, List, Tuple
from backend.app.engines.usage.models import (
    FeatureType,
    LimitPolicy,
    Plan,
    PlanEntitlement,
    PlanTier,
    PlanStatus,
    QuotaPeriod,
)


class Features:
    # Storage & Datasets
    DATASET_UPLOAD = "dataset_upload"
    MAX_DATASET_SIZE_MB = "max_dataset_size_mb"
    STORAGE_LIMIT_BYTES = "storage_limit_bytes"

    # Workspace & Resources
    MAX_PROJECTS = "max_projects"
    MAX_WORKSPACE_MEMBERS = "max_workspace_members"

    # AI Analyst
    AI_ANALYST = "ai_analyst"
    AI_ANALYST_MESSAGES_MONTHLY = "ai_analyst_messages_monthly"

    # SQL & Analytics
    SQL_ANALYTICS = "sql_analytics"
    SQL_MAX_RESULT_ROWS = "sql_max_result_rows"

    # Advanced Engines
    ADVANCED_STATISTICS = "advanced_statistics"
    MACHINE_LEARNING = "machine_learning"
    FORECASTING = "forecasting"

    # Exports & Collaboration
    EXPORTS = "exports"
    EXPORTS_MONTHLY = "exports_monthly"
    TEAM_COLLABORATION = "team_collaboration"
    SHARING = "sharing"
    PUBLIC_LINKS = "public_links"


# ─────────────────────────────────────────────────────────────
# Canonical Plan Catalog
# ─────────────────────────────────────────────────────────────

def get_default_plans() -> List[Plan]:
    return [
        Plan(
            plan_id="plan_free",
            plan_code="FREE",
            name="Community Free",
            description="Essential data analytics studio for individuals and exploratory research.",
            tier=PlanTier.FREE,
            version=1,
            status=PlanStatus.ACTIVE,
            is_default=True,
            metadata={"badge": "Free Forever", "target_audience": "Individual Analysts"},
        ),
        Plan(
            plan_id="plan_pro",
            plan_code="PRO",
            name="Professional",
            description="Advanced machine learning, increased compute quotas, and full export capabilities.",
            tier=PlanTier.PRO,
            version=1,
            status=PlanStatus.ACTIVE,
            is_default=False,
            metadata={"badge": "Popular", "target_audience": "Independent Professionals"},
        ),
        Plan(
            plan_id="plan_team",
            plan_code="TEAM",
            name="Team Collaboration",
            description="Collaborative workspace with high concurrency, shared projects, and team controls.",
            tier=PlanTier.TEAM,
            version=1,
            status=PlanStatus.ACTIVE,
            is_default=False,
            metadata={"badge": "Growing Teams", "target_audience": "Data Teams & Agencies"},
        ),
        Plan(
            plan_id="plan_enterprise",
            plan_code="ENTERPRISE",
            name="Enterprise Scale",
            description="Uncapped analytical quotas, custom governance, and enterprise-grade performance.",
            tier=PlanTier.ENTERPRISE,
            version=1,
            status=PlanStatus.ACTIVE,
            is_default=False,
            metadata={"badge": "Unlimited", "target_audience": "Organizations"},
        ),
    ]


def get_default_entitlements() -> List[PlanEntitlement]:
    entitlements: List[PlanEntitlement] = []

    # 1. FREE Plan Entitlements
    entitlements.extend([
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.DATASET_UPLOAD,
            enabled=True,
            value=10,
            unit="uploads/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.MAX_DATASET_SIZE_MB,
            enabled=True,
            value=50,
            unit="MB",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.STORAGE_LIMIT_BYTES,
            enabled=True,
            value=1 * 1024 * 1024 * 1024,  # 1 GB
            unit="Bytes",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.MAX_PROJECTS,
            enabled=True,
            value=3,
            unit="projects",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.MAX_WORKSPACE_MEMBERS,
            enabled=True,
            value=3,
            unit="members",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.AI_ANALYST,
            enabled=True,
            value=100,
            unit="messages/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.SQL_ANALYTICS,
            enabled=True,
            value=1000,
            unit="queries/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.SQL_MAX_RESULT_ROWS,
            enabled=True,
            value=10000,
            unit="rows",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.MACHINE_LEARNING,
            enabled=True,
            value=20,
            unit="experiments/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.FORECASTING,
            enabled=True,
            value=20,
            unit="runs/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.ADVANCED_STATISTICS,
            enabled=True,
            value=50,
            unit="analyses/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.EXPORTS,
            enabled=True,
            value=20,
            unit="exports/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.TEAM_COLLABORATION,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.SHARING,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_free",
            feature_key=Features.PUBLIC_LINKS,
            enabled=False,
            value=False,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
    ])

    # 2. PRO Plan Entitlements
    entitlements.extend([
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.DATASET_UPLOAD,
            enabled=True,
            value=100,
            unit="uploads/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.MAX_DATASET_SIZE_MB,
            enabled=True,
            value=500,
            unit="MB",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.STORAGE_LIMIT_BYTES,
            enabled=True,
            value=20 * 1024 * 1024 * 1024,  # 20 GB
            unit="Bytes",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.MAX_PROJECTS,
            enabled=True,
            value=20,
            unit="projects",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.MAX_WORKSPACE_MEMBERS,
            enabled=True,
            value=10,
            unit="members",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.AI_ANALYST,
            enabled=True,
            value=1000,
            unit="messages/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.SQL_ANALYTICS,
            enabled=True,
            value=10000,
            unit="queries/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.SQL_MAX_RESULT_ROWS,
            enabled=True,
            value=100000,
            unit="rows",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.MACHINE_LEARNING,
            enabled=True,
            value=200,
            unit="experiments/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.FORECASTING,
            enabled=True,
            value=200,
            unit="runs/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.ADVANCED_STATISTICS,
            enabled=True,
            value=500,
            unit="analyses/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.EXPORTS,
            enabled=True,
            value=200,
            unit="exports/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.TEAM_COLLABORATION,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.SHARING,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_pro",
            feature_key=Features.PUBLIC_LINKS,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
    ])

    # 3. TEAM Plan Entitlements
    entitlements.extend([
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.DATASET_UPLOAD,
            enabled=True,
            value=500,
            unit="uploads/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.MAX_DATASET_SIZE_MB,
            enabled=True,
            value=2000,  # 2 GB
            unit="MB",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.STORAGE_LIMIT_BYTES,
            enabled=True,
            value=100 * 1024 * 1024 * 1024,  # 100 GB
            unit="Bytes",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.MAX_PROJECTS,
            enabled=True,
            value=100,
            unit="projects",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.MAX_WORKSPACE_MEMBERS,
            enabled=True,
            value=50,
            unit="members",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.AI_ANALYST,
            enabled=True,
            value=5000,
            unit="messages/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.SQL_ANALYTICS,
            enabled=True,
            value=50000,
            unit="queries/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.SQL_MAX_RESULT_ROWS,
            enabled=True,
            value=500000,
            unit="rows",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.MACHINE_LEARNING,
            enabled=True,
            value=1000,
            unit="experiments/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.FORECASTING,
            enabled=True,
            value=1000,
            unit="runs/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.ADVANCED_STATISTICS,
            enabled=True,
            value=2500,
            unit="analyses/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.EXPORTS,
            enabled=True,
            value=1000,
            unit="exports/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.BLOCK_NEW_OPERATION,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.TEAM_COLLABORATION,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.SHARING,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_team",
            feature_key=Features.PUBLIC_LINKS,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
    ])

    # 4. ENTERPRISE Plan Entitlements
    entitlements.extend([
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.DATASET_UPLOAD,
            enabled=True,
            value=None,  # Unlimited
            unit="uploads/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.MAX_DATASET_SIZE_MB,
            enabled=True,
            value=10000,  # 10 GB
            unit="MB",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.STORAGE_LIMIT_BYTES,
            enabled=True,
            value=1000 * 1024 * 1024 * 1024,  # 1 TB
            unit="Bytes",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.MAX_PROJECTS,
            enabled=True,
            value=None,  # Unlimited
            unit="projects",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.MAX_WORKSPACE_MEMBERS,
            enabled=True,
            value=None,  # Unlimited
            unit="members",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.AI_ANALYST,
            enabled=True,
            value=None,  # Unlimited
            unit="messages/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.SQL_ANALYTICS,
            enabled=True,
            value=None,  # Unlimited
            unit="queries/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.SQL_MAX_RESULT_ROWS,
            enabled=True,
            value=2000000,
            unit="rows",
            limit_type=FeatureType.LIMIT,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.MACHINE_LEARNING,
            enabled=True,
            value=None,
            unit="experiments/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.FORECASTING,
            enabled=True,
            value=None,
            unit="runs/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.ADVANCED_STATISTICS,
            enabled=True,
            value=None,
            unit="analyses/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.EXPORTS,
            enabled=True,
            value=None,
            unit="exports/mo",
            limit_type=FeatureType.QUOTA,
            period=QuotaPeriod.MONTHLY,
            policy=LimitPolicy.SOFT_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.TEAM_COLLABORATION,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.SHARING,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
        PlanEntitlement(
            plan_id="plan_enterprise",
            feature_key=Features.PUBLIC_LINKS,
            enabled=True,
            value=True,
            limit_type=FeatureType.BOOLEAN,
            period=QuotaPeriod.CURRENT,
            policy=LimitPolicy.HARD_LIMIT,
        ),
    ])

    return entitlements


PLAN_CATALOG = get_default_plans()
