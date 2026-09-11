"""
Dependency Analyzer and Lineage Engine for Phase 16.
Resolves asset dependency graphs, evaluates deletion/archive impact,
builds lineage DAGs, and detects broken references.
"""

from typing import Dict, List, Optional, Set
import os

from backend.app.core.config import settings
from backend.app.engines.workspace.models import (
    Asset,
    AssetRelationship,
    AssetStatus,
    AssetType,
    BrokenReference,
    DependencyItem,
    DependencySummary,
    LineageEdge,
    LineageGraph,
    LineageNode,
    ProjectHealth,
    RelationshipType,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo


class DependencyAnalyzer:
    """
    Analyzes dependency relationships between analytical assets,
    detects breaking changes before archive/deletion, and constructs lineage graphs.
    """

    def __init__(self, repository: Optional[WorkspaceRepository] = None):
        self._repo = repository or workspace_repo

    def get_dependencies(self, asset_id: str) -> DependencySummary:
        """
        Analyze downstream and upstream dependencies for a given asset.
        Answers: 'What will be affected if I archive/delete this asset?'
        """
        root_asset = self._repo.get_asset(asset_id)
        if not root_asset:
            raise ValueError(f"Asset '{asset_id}' not found")

        # Recursive downstream collection
        downstream_items: List[DependencyItem] = []
        visited_down = {asset_id}
        queue_down = [asset_id]
        while queue_down:
            curr = queue_down.pop(0)
            rels = self._repo.list_relationships(source_asset_id=curr)
            for rel in rels:
                target = self._repo.get_asset(rel.target_asset_id)
                if target and target.status != AssetStatus.DELETED:
                    downstream_items.append(
                        DependencyItem(
                            asset_id=target.asset_id,
                            name=target.name,
                            asset_type=target.asset_type,
                            relationship_type=rel.relationship_type,
                        )
                    )
                    if target.asset_id not in visited_down:
                        visited_down.add(target.asset_id)
                        queue_down.append(target.asset_id)

        # Recursive upstream collection
        upstream_items: List[DependencyItem] = []
        visited_up = {asset_id}
        queue_up = [asset_id]
        while queue_up:
            curr = queue_up.pop(0)
            rels = self._repo.list_relationships(target_asset_id=curr)
            for rel in rels:
                source = self._repo.get_asset(rel.source_asset_id)
                if source and source.status != AssetStatus.DELETED:
                    upstream_items.append(
                        DependencyItem(
                            asset_id=source.asset_id,
                            name=source.name,
                            asset_type=source.asset_type,
                            relationship_type=rel.relationship_type,
                        )
                    )
                    if source.asset_id not in visited_up:
                        visited_up.add(source.asset_id)
                        queue_up.append(source.asset_id)

        warnings: List[str] = []
        can_safely_delete = True
        can_safely_archive = True

        # Check impact on critical assets
        active_dependents = [d for d in downstream_items]
        dashboards = [d for d in active_dependents if d.asset_type == AssetType.DASHBOARD]
        reports = [d for d in active_dependents if d.asset_type == AssetType.REPORT]
        visualizations = [d for d in active_dependents if d.asset_type == AssetType.VISUALIZATION]

        if dashboards:
            warnings.append(
                f"Referenced by {len(dashboards)} dashboard(s): {', '.join(d.name for d in dashboards[:3])}"
            )
            can_safely_delete = False
        if reports:
            warnings.append(
                f"Referenced by {len(reports)} report(s): {', '.join(r.name for r in reports[:3])}"
            )
            can_safely_delete = False
        if visualizations:
            warnings.append(f"Visualized in {len(visualizations)} chart(s)")

        # Archiving is reversible, but should carry clear warnings
        if active_dependents:
            can_safely_archive = True

        return DependencySummary(
            asset_id=root_asset.asset_id,
            asset_name=root_asset.name,
            asset_type=root_asset.asset_type,
            dependent_assets=downstream_items,
            downstream_dependencies=downstream_items,
            upstream_assets=upstream_items,
            upstream_dependencies=upstream_items,
            can_safely_archive=can_safely_archive,
            can_safely_delete=can_safely_delete,
            warnings=warnings,
        )

    def build_lineage_graph(self, asset_id: str, user_id: Optional[str] = None) -> LineageGraph:
        """
        Builds a complete upstream and downstream DAG lineage graph around the asset.
        If user_id is provided, masks nodes the user lacks access to as 'Restricted source'.
        """
        root_asset = self._repo.get_asset(asset_id)
        if not root_asset:
            raise ValueError(f"Asset '{asset_id}' not found")

        visited_nodes: Set[str] = set()
        nodes: List[LineageNode] = []
        edges: List[LineageEdge] = []

        def add_node(asset: Asset):
            if asset.asset_id in visited_nodes:
                return
            visited_nodes.add(asset.asset_id)

            can_see = True
            if user_id and asset.asset_id != asset_id:
                try:
                    from backend.app.services.collaboration.access_service import access_service
                    from backend.app.engines.collaboration.models import ResourceType
                    eff = access_service.resolve_effective_access(user_id, ResourceType.DATASET, asset.asset_id)
                    can_see = eff.can_view
                except Exception:
                    can_see = True

            nodes.append(
                LineageNode(
                    id=asset.asset_id if can_see else f"restricted_{asset.asset_id[:8]}",
                    label=asset.name if can_see else "Restricted source",
                    type=asset.asset_type.value if can_see else "RESTRICTED",
                    status=asset.status.value,
                    is_stale=asset.metadata.get("is_stale", False) if can_see else False,
                    metadata=asset.metadata if can_see else {},
                )
            )

        add_node(root_asset)

        # BFS downstream
        down_visited = {asset_id}
        queue = [asset_id]
        while queue:
            curr_id = queue.pop(0)
            rels = self._repo.list_relationships(source_asset_id=curr_id)
            for r in rels:
                target = self._repo.get_asset(r.target_asset_id)
                if target:
                    add_node(target)
                    edges.append(
                        LineageEdge(
                            id=r.relationship_id,
                            source=curr_id,
                            target=target.asset_id,
                            label=r.relationship_type.value,
                        )
                    )
                    if target.asset_id not in down_visited:
                        down_visited.add(target.asset_id)
                        queue.append(target.asset_id)

        # BFS upstream
        up_visited = {asset_id}
        queue = [asset_id]
        while queue:
            curr_id = queue.pop(0)
            rels = self._repo.list_relationships(target_asset_id=curr_id)
            for r in rels:
                source = self._repo.get_asset(r.source_asset_id)
                if source:
                    add_node(source)
                    edges.append(
                        LineageEdge(
                            id=r.relationship_id,
                            source=source.asset_id,
                            target=curr_id,
                            label=r.relationship_type.value,
                        )
                    )
                    if source.asset_id not in up_visited:
                        up_visited.add(source.asset_id)
                        queue.append(source.asset_id)

        return LineageGraph(
            root_asset_id=asset_id,
            nodes=nodes,
            edges=edges,
        )

    def evaluate_project_health(self, project_id: str) -> ProjectHealth:
        """
        Calculates organizational project health metrics and detects broken references.
        """
        project = self._repo.get_project(project_id)
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        assets = self._repo.list_assets(project_id=project_id)
        datasets_ready = 0
        datasets_failed = 0
        archived_datasets = 0
        broken_refs: List[BrokenReference] = []

        for asset in assets:
            if asset.asset_type == AssetType.DATASET:
                if asset.status == AssetStatus.ARCHIVED:
                    archived_datasets += 1
                elif asset.metadata.get("status") == "FAILED":
                    datasets_failed += 1
                else:
                    datasets_ready += 1

            # Broken reference check: verify source entity exists where applicable
            if asset.asset_type == AssetType.DATASET:
                # Check parquet file path
                parquet_path = asset.metadata.get("processed_file_path") or asset.metadata.get("file_path")
                if parquet_path and not os.path.exists(parquet_path):
                    broken_refs.append(
                        BrokenReference(
                            source_asset_id=asset.asset_id,
                            source_name=asset.name,
                            source_type=asset.asset_type,
                            reason=f"Underlying dataset file missing: {os.path.basename(parquet_path)}",
                        )
                    )

            # Check if any outbound relationship targets a missing asset
            out_rels = self._repo.list_relationships(source_asset_id=asset.asset_id)
            for r in out_rels:
                target = self._repo.get_asset(r.target_asset_id)
                if not target or target.status == AssetStatus.DELETED:
                    broken_refs.append(
                        BrokenReference(
                            source_asset_id=asset.asset_id,
                            source_name=asset.name,
                            source_type=asset.asset_type,
                            target_asset_id=r.target_asset_id,
                            reason=f"Target asset '{r.target_asset_id}' is deleted or missing",
                        )
                    )

        status = "HEALTHY"
        if datasets_failed > 0 or len(broken_refs) > 0:
            status = "CRITICAL" if len(broken_refs) > 3 else "WARNING"

        return ProjectHealth(
            project_id=project_id,
            workspace_id=project.workspace_id,
            status=status,
            datasets_ready=datasets_ready,
            datasets_failed=datasets_failed,
            archived_datasets=archived_datasets,
            total_assets=len(assets),
            broken_references=broken_refs,
            failed_jobs_count=datasets_failed,
        )


dependency_analyzer = DependencyAnalyzer()

