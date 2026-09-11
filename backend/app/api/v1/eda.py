"""
AnalyzaX — Phase 7: Exploratory Data Analysis (EDA) API Router
Exposes deterministic EDA report generation, column explorer, interactive relationship queries,
and structured automated analytical findings.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.core.logging import logger
from backend.app.engines.eda.models import (
    EDAFinding,
    EDAReport,
    FindingCategory,
    FindingSeverity,
    RelationshipQueryRequest,
    RelationshipQueryResponse,
)
from backend.app.services.eda_service import eda_service

router = APIRouter(prefix="/datasets", tags=["eda"])


# ─────────────────────────────────────────────────────────────
# Version-specific EDA Endpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{dataset_id}/versions/{version_id}/eda",
    response_model=EDAReport,
    summary="Get or compute EDA report for a dataset version",
    description="Returns deterministic exploratory analysis including overview, distributions, correlations, time trends, findings, and ChartSpecs.",
)
async def get_version_eda_report(dataset_id: str, version_id: str):
    try:
        return eda_service.get_or_create_eda_report(
            dataset_id=dataset_id, version_id=version_id, force_refresh=False
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to generate EDA report for {dataset_id}/{version_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate EDA report: {str(e)}",
        )


@router.post(
    "/{dataset_id}/versions/{version_id}/eda/refresh",
    response_model=EDAReport,
    summary="Force refresh EDA report for a dataset version",
    description="Invalidates cached EDA report on disk and computes a fresh deterministic analysis.",
)
async def refresh_version_eda_report(dataset_id: str, version_id: str):
    try:
        return eda_service.get_or_create_eda_report(
            dataset_id=dataset_id, version_id=version_id, force_refresh=True
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to refresh EDA report for {dataset_id}/{version_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh EDA report: {str(e)}",
        )


@router.get(
    "/{dataset_id}/versions/{version_id}/eda/columns/{column}",
    summary="Deep drilldown analysis for a single column",
    description="Returns detailed univariate statistics, sample values, and ChartSpecs for a single feature.",
)
async def get_version_column_analysis(dataset_id: str, version_id: str, column: str):
    try:
        return eda_service.get_column_analysis(
            dataset_id=dataset_id, column=column, version_id=version_id
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to analyze column {column} for {dataset_id}/{version_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze column: {str(e)}",
        )


@router.post(
    "/{dataset_id}/versions/{version_id}/eda/relationship",
    response_model=RelationshipQueryResponse,
    summary="Interactive bivariate relationship exploration",
    description="Analyzes relationship between any two selected columns (Numeric-Numeric, Numeric-Categorical, Categorical-Categorical).",
)
async def analyze_version_relationship(
    dataset_id: str,
    version_id: str,
    body: RelationshipQueryRequest,
):
    try:
        return eda_service.analyze_relationship(
            dataset_id=dataset_id,
            col_x=body.column_x,
            col_y=body.column_y,
            version_id=version_id,
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to analyze relationship between {body.column_x} and {body.column_y}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze relationship: {str(e)}",
        )


@router.get(
    "/{dataset_id}/versions/{version_id}/eda/findings",
    response_model=List[EDAFinding],
    summary="Get automated analytical findings for a dataset version",
    description="Returns filtered rule-based findings categorized by distribution, relationships, anomalies, missingness, etc.",
)
async def get_version_eda_findings(
    dataset_id: str,
    version_id: str,
    category: Optional[FindingCategory] = Query(None, description="Filter by finding category"),
    severity: Optional[FindingSeverity] = Query(None, description="Filter by severity level"),
):
    try:
        return eda_service.get_findings(
            dataset_id=dataset_id,
            version_id=version_id,
            category=category,
            severity=severity,
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to get findings for {dataset_id}/{version_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get EDA findings: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────
# Active Version Fallback Endpoints (without version_id in URL)
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{dataset_id}/eda",
    response_model=EDAReport,
    summary="Get or compute EDA report for active dataset version",
)
async def get_active_eda_report(dataset_id: str):
    try:
        return eda_service.get_or_create_eda_report(
            dataset_id=dataset_id, version_id=None, force_refresh=False
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to generate active EDA report for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate EDA report: {str(e)}",
        )


@router.post(
    "/{dataset_id}/eda/refresh",
    response_model=EDAReport,
    summary="Force refresh EDA report for active dataset version",
)
async def refresh_active_eda_report(dataset_id: str):
    try:
        return eda_service.get_or_create_eda_report(
            dataset_id=dataset_id, version_id=None, force_refresh=True
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to refresh active EDA report for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh EDA report: {str(e)}",
        )


@router.get(
    "/{dataset_id}/eda/columns/{column}",
    summary="Deep drilldown analysis for active dataset version column",
)
async def get_active_column_analysis(dataset_id: str, column: str):
    try:
        return eda_service.get_column_analysis(
            dataset_id=dataset_id, column=column, version_id=None
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to analyze column {column} for active dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze column: {str(e)}",
        )


@router.post(
    "/{dataset_id}/eda/relationship",
    response_model=RelationshipQueryResponse,
    summary="Interactive bivariate relationship exploration for active version",
)
async def analyze_active_relationship(
    dataset_id: str,
    body: RelationshipQueryRequest,
):
    try:
        return eda_service.analyze_relationship(
            dataset_id=dataset_id,
            col_x=body.column_x,
            col_y=body.column_y,
            version_id=None,
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to analyze active relationship {body.column_x} vs {body.column_y}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze relationship: {str(e)}",
        )


@router.get(
    "/{dataset_id}/eda/findings",
    response_model=List[EDAFinding],
    summary="Get automated analytical findings for active dataset version",
)
async def get_active_eda_findings(
    dataset_id: str,
    category: Optional[FindingCategory] = Query(None, description="Filter by finding category"),
    severity: Optional[FindingSeverity] = Query(None, description="Filter by severity level"),
):
    try:
        return eda_service.get_findings(
            dataset_id=dataset_id,
            version_id=None,
            category=category,
            severity=severity,
        )
    except ValueError as e:
        err = str(e)
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    except Exception as e:
        logger.error(f"Failed to get active findings for {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get EDA findings: {str(e)}",
        )
