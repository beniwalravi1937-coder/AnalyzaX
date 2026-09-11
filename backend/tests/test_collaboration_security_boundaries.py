"""
Security Boundary & Dependency Protection Tests for Phase 18.
Validates dataset version isolation, dashboard dependency masking, search security,
lineage masking, and export permission gating.
"""

from typing import Optional
import pytest

from backend.app.engines.collaboration.models import (
    CreateShareRequest,
    ResourceType,
    SharePermission,
    ShareRecipientType,
)
from backend.app.engines.workspace.models import Asset, AssetType, RelationshipType
from backend.app.services.workspace.search_service import SearchService
from backend.tests.test_collaboration_fixtures import CollabTestContext


def test_dataset_version_sharing_boundary():
    ctx = CollabTestContext()
    try:
        # Create Version 1 and Version 2 assets
        ver_1 = Asset(
            asset_id="ds_ver_1",
            source_entity_id="ds_ver_1",
            project_id=ctx.proj_a.project_id,
            workspace_id=ctx.ws_a.workspace_id,
            asset_type=AssetType.DATASET_VERSION,
            name="Version 1",
            created_by=ctx.user_a.user_id,
        )
        ver_2 = Asset(
            asset_id="ds_ver_2",
            source_entity_id="ds_ver_2",
            project_id=ctx.proj_a.project_id,
            workspace_id=ctx.ws_a.workspace_id,
            asset_type=AssetType.DATASET_VERSION,
            name="Version 2",
            created_by=ctx.user_a.user_id,
        )
        ctx.ws_repo.save_asset(ver_1)
        ctx.ws_repo.save_asset(ver_2)

        # Explicitly share ONLY Version 1 with external user
        req = CreateShareRequest(
            resource_type=ResourceType.DATASET_VERSION,
            resource_id="ds_ver_1",
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_external.user_id,
            permission=SharePermission.VIEW,
        )
        ctx.share_service.create_share(ctx.user_a.user_id, req)

        # Check effective access on Version 1
        eff_ver1 = ctx.access.resolve_effective_access(
            ctx.user_external.user_id,
            ResourceType.DATASET_VERSION,
            "ds_ver_1",
        )
        assert eff_ver1.can_view is True

        # Check effective access on Version 2: MUST BE DENIED!
        eff_ver2 = ctx.access.resolve_effective_access(
            ctx.user_external.user_id,
            ResourceType.DATASET_VERSION,
            "ds_ver_2",
        )
        assert eff_ver2.can_view is False
    finally:
        ctx.cleanup()


def test_search_respects_effective_access():
    ctx = CollabTestContext()
    try:
        search_svc = SearchService(ctx.ws_repo, access_service=ctx.access)

        # User external has no workspace membership and no shares initially
        from backend.app.engines.workspace.models import SearchRequest
        res_initial = search_svc.search(SearchRequest(query="Alpha"), user_id=ctx.user_external.user_id)
        assert len(res_initial.results) == 0

        # Share ONLY Report Alpha with external user
        req = CreateShareRequest(
            resource_type=ResourceType.REPORT,
            resource_id=ctx.report_a.asset_id,
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_external.user_id,
            permission=SharePermission.VIEW,
        )
        ctx.share_service.create_share(ctx.user_a.user_id, req)

        # Search again: only Report Alpha must appear; Dataset and Dashboard must NOT appear!
        res_after = search_svc.search(SearchRequest(query="Alpha"), user_id=ctx.user_external.user_id)
        found_ids = [item.asset_id for item in res_after.results]
        assert ctx.report_a.asset_id in found_ids
        assert ctx.ds_a.asset_id not in found_ids
        assert ctx.dash_a.asset_id not in found_ids
    finally:
        ctx.cleanup()


def test_lineage_masks_inaccessible_upstream_nodes():
    ctx = CollabTestContext()
    try:
        # Create dependency: Dataset A -> Dashboard A
        from backend.app.engines.workspace.models import AssetRelationship
        rel = AssetRelationship(
            source_asset_id=ctx.ds_a.asset_id,
            target_asset_id=ctx.dash_a.asset_id,
            relationship_type=RelationshipType.GENERATED_FROM,
        )
        ctx.ws_repo.save_relationship(rel)

        # Share Dashboard A with user_external (but NOT Dataset A)
        req = CreateShareRequest(
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
            recipient_type=ShareRecipientType.USER,
            recipient_id=ctx.user_external.user_id,
            permission=SharePermission.VIEW,
        )
        ctx.share_service.create_share(ctx.user_a.user_id, req)

        # Build lineage graph for user_external
        from backend.app.engines.workspace.dependency_analyzer import DependencyAnalyzer
        analyzer = DependencyAnalyzer(ctx.ws_repo)
        graph = analyzer.build_lineage_graph(ctx.dash_a.asset_id, user_id=ctx.user_external.user_id)

        # Inaccessible upstream dataset node must be masked as 'Restricted source'
        ds_node = next((n for n in graph.nodes if n.id != ctx.dash_a.asset_id), None)
        if ds_node:
            assert ds_node.label == "Restricted source"
            assert ds_node.type == "RESTRICTED"
            assert ds_node.metadata == {}
    finally:
        ctx.cleanup()


def test_view_permission_does_not_imply_export():
    ctx = CollabTestContext()
    try:
        # Share Dashboard A with User C with VIEW only
        eff = ctx.access.resolve_effective_access(
            user_id=ctx.user_c.user_id,
            resource_type=ResourceType.DASHBOARD,
            resource_id=ctx.dash_a.asset_id,
        )
        assert eff.can_view is True
        assert eff.can_export is False
        assert eff.can_edit is False
    finally:
        ctx.cleanup()
