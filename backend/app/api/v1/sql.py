"""
AnalyzaX — Phase 8: SQL API Routes
FastAPI router providing the complete REST API for SQL Studio: query execution,
AST validation, explain plans, schema introspection, templates, history, and saved queries.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.engines.eda.models import ChartSpec
from backend.app.engines.sql.chart_advisor import SQLChartAdvisor
from backend.app.engines.sql.models import (
    QueryHistoryEntry,
    SavedQuery,
    SavedQueryCreateRequest,
    SavedQueryUpdateRequest,
    SchemaTableInfo,
    SQLExplainResult,
    SQLQueryRequest,
    SQLQueryResponse,
    SQLTemplate,
    SQLValidationResult,
    VisualizationRequest,
)
from backend.app.services.sql.history_service import sql_history_service
from backend.app.services.sql.introspection_service import sql_introspection_service
from backend.app.services.sql.query_service import sql_query_service
from backend.app.services.sql.saved_query_service import sql_saved_query_service

router = APIRouter(prefix="/sql", tags=["sql"])


class ValidateRequest(SQLQueryRequest):
    pass


class ExplainRequest(SQLQueryRequest):
    pass


# ─────────────────────────────────────────────────────────────
# Query Execution & Validation
# ─────────────────────────────────────────────────────────────

@router.post("/query", response_model=SQLQueryResponse, summary="Execute a read-only SQL query")
async def execute_sql(req: SQLQueryRequest):
    try:
        return sql_query_service.execute_query(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate", response_model=SQLValidationResult, summary="Validate SQL query AST and schema")
async def validate_sql(req: ValidateRequest):
    try:
        return sql_query_service.validate_query(
            dataset_id=req.dataset_id,
            sql=req.sql,
            version_id=req.version_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/explain", response_model=SQLExplainResult, summary="Generate execution plan for SQL query")
async def explain_sql(req: ExplainRequest):
    try:
        return sql_query_service.explain_query(
            dataset_id=req.dataset_id,
            sql=req.sql,
            version_id=req.version_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cancel/{query_id}", summary="Cancel a running SQL query")
async def cancel_query(query_id: str):
    success = sql_query_service.cancel_query(query_id)
    return {"query_id": query_id, "cancelled": success}


# ─────────────────────────────────────────────────────────────
# Schema Introspection & Templates
# ─────────────────────────────────────────────────────────────

@router.get("/schema/{dataset_id}", response_model=SchemaTableInfo, summary="Introspect dataset schema")
async def get_schema(
    dataset_id: str,
    version_id: Optional[str] = Query(default=None, description="Specific dataset version (e.g. v1)"),
):
    try:
        return sql_introspection_service.get_schema(dataset_id=dataset_id, version_id=version_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/templates/{dataset_id}", response_model=List[SQLTemplate], summary="Get dynamic SQL templates")
async def get_templates(
    dataset_id: str,
    version_id: Optional[str] = Query(default=None, description="Specific dataset version (e.g. v1)"),
):
    try:
        return sql_introspection_service.get_templates(dataset_id=dataset_id, version_id=version_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Visualization Advice
# ─────────────────────────────────────────────────────────────

@router.post("/visualize", response_model=List[ChartSpec], summary="Generate chart specifications for query results")
async def visualize_results(req: VisualizationRequest):
    try:
        return SQLChartAdvisor.advise(
            dataset_id=req.dataset_id,
            version_id=req.version_id,
            columns=req.columns,
            rows=req.rows,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Query History
# ─────────────────────────────────────────────────────────────

@router.get("/history", response_model=List[QueryHistoryEntry], summary="List execution history")
async def list_history(
    dataset_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    return sql_history_service.list_history(
        dataset_id=dataset_id,
        status=status,
        search=search,
        limit=limit,
    )


@router.delete("/history", summary="Clear query history")
async def clear_history(
    dataset_id: Optional[str] = Query(default=None, description="Optional dataset ID to clear for"),
):
    count = sql_history_service.clear_history(dataset_id=dataset_id)
    return {"cleared_count": count}


# ─────────────────────────────────────────────────────────────
# Saved Queries
# ─────────────────────────────────────────────────────────────

@router.get("/saved", response_model=List[SavedQuery], summary="List saved queries")
async def list_saved_queries(
    dataset_id: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
):
    return sql_saved_query_service.list(dataset_id=dataset_id, tag=tag)


@router.post("/saved", response_model=SavedQuery, status_code=status.HTTP_201_CREATED, summary="Save a query")
async def create_saved_query(req: SavedQueryCreateRequest):
    return sql_saved_query_service.create(req)


@router.get("/saved/{saved_query_id}", response_model=SavedQuery, summary="Get saved query by ID")
async def get_saved_query(saved_query_id: str):
    query = sql_saved_query_service.get(saved_query_id)
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved query not found.")
    return query


@router.put("/saved/{saved_query_id}", response_model=SavedQuery, summary="Update saved query")
async def update_saved_query(saved_query_id: str, req: SavedQueryUpdateRequest):
    updated = sql_saved_query_service.update(saved_query_id, req)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved query not found.")
    return updated


@router.delete("/saved/{saved_query_id}", summary="Delete saved query")
async def delete_saved_query(saved_query_id: str):
    success = sql_saved_query_service.delete(saved_query_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved query not found.")
    return {"deleted": True, "id": saved_query_id}
