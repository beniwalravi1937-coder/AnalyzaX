"""
AnalyzaX — Phase 25: AI Generation Provenance Engine.
Records and verifies audit trails, model versions, tool references, and dataset versions
for all AI-synthesized objects without logging raw sensitive prompt contents.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIGenerationProvenance(BaseModel):
    """Immutable audit record for an AI-generated insight, narrative, or recommendation."""
    ai_generation_id: str
    provider: str
    model: str
    model_version: Optional[str] = None
    prompt_template_version: str = "v25.1"
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    semantic_model_version: Optional[str] = None
    input_references: List[str] = Field(default_factory=list)
    tool_references: List[str] = Field(default_factory=list)
    sanitized_prompt_hash: Optional[str] = None
    created_at: str


class ProvenanceEngine:
    """Creates structured provenance records for AI outputs."""

    @staticmethod
    def create_provenance(
        provider: str,
        model: str,
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
        semantic_version: Optional[str] = None,
        tool_references: Optional[List[str]] = None,
        input_references: Optional[List[str]] = None,
    ) -> AIGenerationProvenance:
        """Generates a complete provenance object."""
        return AIGenerationProvenance(
            ai_generation_id=f"aigen_{uuid.uuid4().hex[:12]}",
            provider=provider,
            model=model,
            model_version="1.0",
            prompt_template_version="v25.1",
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            semantic_model_version=semantic_version,
            input_references=input_references or [],
            tool_references=tool_references or [],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
