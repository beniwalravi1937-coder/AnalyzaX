"""
Cleaning & Versioning Services Package
"""

from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.cleaning.recommendation_service import RecommendationService
from backend.app.services.cleaning.comparison_service import ComparisonService
from backend.app.services.cleaning.plan_service import PlanService

version_service = VersionService()
recommendation_service = RecommendationService()
comparison_service = ComparisonService()
plan_service = PlanService()

__all__ = [
    "VersionService",
    "RecommendationService",
    "ComparisonService",
    "PlanService",
    "version_service",
    "recommendation_service",
    "comparison_service",
    "plan_service",
]
