"""
Global Search Application Service for Phase 16.
Provides safe, indexed, parameterized search across workspaces, projects, and all asset types.
"""

from typing import Any, List, Optional

from backend.app.core.config import settings
from backend.app.engines.workspace.models import (
    Asset,
    AssetStatus,
    AssetType,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo


class SearchService:
    """
    Search and discovery engine for workspace assets.
    Performs cross-project queries, relevance ranking, and filtering.
    """

    ALLOWED_SORT_FIELDS = {"relevance", "name", "created_at", "updated_at"}

    def __init__(
        self,
        repository: Optional[WorkspaceRepository] = None,
        access_service: Optional[Any] = None,
    ):
        self._repo = repository or workspace_repo
        self._access = access_service

    def search(self, req: SearchRequest, user_id: Optional[str] = None) -> SearchResponse:
        """
        Executes search over assets with relevance scoring, filtering,
        pagination, and security access gating.
        """
        # Validate sort field
        sort_by = req.sort_by if req.sort_by in self.ALLOWED_SORT_FIELDS else "relevance"
        sort_order = req.sort_order.lower() if req.sort_order.lower() in ("asc", "desc") else "desc"

        # Fetch candidate assets
        assets = self._repo.list_assets(
            project_id=req.project_id,
            workspace_id=req.workspace_id,
            status=req.status or AssetStatus.ACTIVE,
            is_favorite=req.is_favorite,
        )

        query = req.query.strip().lower() if req.query else ""
        matched_results: List[SearchResult] = []

        # Cache project names for display
        project_names = {}
        for p in self._repo.list_projects(workspace_id=req.workspace_id):
            project_names[p.project_id] = p.name

        for asset in assets:
            # Security filter: ensure user has effective VIEW permission
            if user_id:
                try:
                    acc_svc = self._access
                    if acc_svc is None:
                        from backend.app.services.collaboration.access_service import access_service
                        acc_svc = access_service

                    from backend.app.engines.collaboration.models import ResourceType
                    try:
                        r_type = ResourceType(asset.asset_type.value)
                    except ValueError:
                        val = asset.asset_type.value
                        if "STAT" in val:
                            r_type = ResourceType.STATISTICAL_RESULT
                        elif "ML" in val:
                            r_type = ResourceType.ML_RESULT
                        elif "FORECAST" in val:
                            r_type = ResourceType.FORECAST_RESULT
                        elif "AI" in val:
                            r_type = ResourceType.AI_ANALYSIS
                        else:
                            r_type = ResourceType.DATASET

                    eff = acc_svc.resolve_effective_access(user_id, r_type, asset.asset_id)
                    if not eff.can_view:
                        continue
                except Exception:
                    pass
            # Asset type filter
            if req.asset_types and asset.asset_type not in req.asset_types:
                continue

            # Tag filter
            if req.tags:
                tag_matched = any(t.lower() in [at.lower() for at in asset.tags] for t in req.tags)
                if not tag_matched:
                    continue

            # Query text filter & score
            score = 0
            if query:
                name_lower = asset.name.lower()
                desc_lower = (asset.description or "").lower()
                tags_lower = [t.lower() for t in asset.tags]

                if query == name_lower:
                    score += 100
                elif name_lower.startswith(query):
                    score += 50
                elif query in name_lower:
                    score += 30

                if query in desc_lower:
                    score += 15

                if any(query in t for t in tags_lower):
                    score += 20

                if score == 0:
                    continue
            else:
                score = 1

            nav_url = self._compute_navigation_url(asset)

            matched_results.append(
                SearchResult(
                    asset_id=asset.asset_id,
                    asset_type=asset.asset_type,
                    name=asset.name,
                    description=asset.description,
                    project_id=asset.project_id,
                    project_name=project_names.get(asset.project_id, "Project"),
                    workspace_id=asset.workspace_id,
                    status=asset.status,
                    is_favorite=asset.is_favorite,
                    tags=asset.tags,
                    created_at=asset.created_at,
                    updated_at=asset.updated_at,
                    navigation_url=nav_url,
                    source_entity_id=asset.source_entity_id,
                )
            )

        # Sorting
        if sort_by == "name":
            matched_results.sort(key=lambda r: r.name.lower(), reverse=(sort_order == "desc"))
        elif sort_by == "created_at":
            matched_results.sort(key=lambda r: r.created_at, reverse=(sort_order == "desc"))
        elif sort_by == "updated_at":
            matched_results.sort(key=lambda r: r.updated_at, reverse=(sort_order == "desc"))
        else:
            # Relevance default: sort by score / recency
            matched_results.sort(key=lambda r: r.updated_at, reverse=True)

        # Pagination
        total = len(matched_results)
        page = max(1, req.page)
        page_size = min(settings.SEARCH_MAX_RESULTS, max(1, req.page_size))
        start = (page - 1) * page_size
        paginated = matched_results[start : start + page_size]

        return SearchResponse(
            query=req.query,
            total=total,
            page=page,
            page_size=page_size,
            results=paginated,
        )

    def _compute_navigation_url(self, asset: Asset) -> str:
        """Determines target route for an asset type."""
        type_urls = {
            AssetType.DATASET: "/dataset",
            AssetType.DATASET_VERSION: "/dataset",
            AssetType.DASHBOARD: f"/dashboard",
            AssetType.REPORT: "/exports",
            AssetType.EXPORT: "/exports",
            AssetType.QUERY: "/sql",
            AssetType.VISUALIZATION: "/visualization",
            AssetType.STATISTICAL_ANALYSIS: "/statistics",
            AssetType.ML_EXPERIMENT: "/ml",
            AssetType.ML_RESULT: "/ml",
            AssetType.FORECAST_EXPERIMENT: "/forecasting",
            AssetType.FORECAST_RESULT: "/forecasting",
            AssetType.AI_SESSION: "/ai-analyst",
        }
        return type_urls.get(asset.asset_type, "/dataset")


search_service = SearchService()
