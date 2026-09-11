"""
ChartSpec validator and version compatibility engine.
Enforces strict security, field existence, aggregation validity, and schema isolation.
"""

from typing import Any, Dict, List, Optional

from backend.app.engines.visualization.models import (
    AggregationType,
    ChartSpec,
    ChartType,
    StructuredFilter,
    ValidationErrorItem,
    ValidationWarningItem,
    VisualizationValidationResult,
)

VALID_OPERATORS = {
    "equals",
    "not_equals",
    "in",
    "not_in",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "between",
    "contains",
    "starts_with",
    "is_null",
    "is_not_null",
}

NUMERIC_AGGREGATIONS = {
    AggregationType.SUM,
    AggregationType.AVG,
    AggregationType.MEDIAN,
    AggregationType.MIN,
    AggregationType.MAX,
}


from backend.app.engines.visualization.registry import (
    get_chart_definition,
    is_chart_supported,
)


class ChartSpecValidator:
    """
    Validates ChartSpec contracts before rendering or persisting.
    Detects missing fields, invalid encodings, malicious operators, unsupported tiers, and schema drift.
    """

    def validate(
        self,
        spec: ChartSpec,
        schema_columns: Optional[Dict[str, str]] = None,  # name -> physical/semantic type
    ) -> VisualizationValidationResult:
        errors: List[ValidationErrorItem] = []
        warnings: List[ValidationWarningItem] = []
        is_compatible = True
        incomp_reason = None

        # 1. Chart Type validity and Tier Check (VIZ-T08, VIZ-T09)
        if not spec.chart_type:
            errors.append(
                ValidationErrorItem(
                    code="MISSING_CHART_TYPE",
                    message="Chart specification must declare a valid chart_type.",
                )
            )
        else:
            chart_def = get_chart_definition(spec.chart_type)
            if not chart_def:
                errors.append(
                    ValidationErrorItem(
                        code="INVALID_CHART_TYPE",
                        message=f"Unknown chart type '{spec.chart_type}'. Must be registered in central chart registry.",
                    )
                )
            elif not chart_def.is_supported:
                # Tier 3 check (VIZ-T09)
                errors.append(
                    ValidationErrorItem(
                        code="UNSUPPORTED_CHART_TIER",
                        message=(
                            f"Chart type '{spec.chart_type}' is a Tier {chart_def.tier.value} ({chart_def.display_name}) "
                            f"specialized chart whose renderer is deferred in Phase 9. Please select a Tier 1 or Tier 2 chart."
                        ),
                    )
                )
            else:
                # Check required encodings defined in registry
                for req in chart_def.required_encodings:
                    val = getattr(spec, req, None)
                    if not val:
                        errors.append(
                            ValidationErrorItem(
                                code="MISSING_REQUIRED_ENCODING",
                                message=f"Chart type '{spec.chart_type}' requires encoding '{req}'.",
                                field=req,
                            )
                        )

        # 2. Check field references
        referenced_fields: List[str] = []
        if spec.x:
            referenced_fields.append(spec.x)
        if spec.y:
            referenced_fields.append(spec.y)
        if spec.series:
            referenced_fields.append(spec.series)
        if spec.color:
            referenced_fields.append(spec.color)
        if spec.size:
            referenced_fields.append(spec.size)

        for filt in spec.filters:
            referenced_fields.append(filt.field)

        # 3. Schema column compatibility check (VIZ-41, VIZ-61)
        if schema_columns is not None:
            missing_in_schema = [f for f in referenced_fields if f not in schema_columns]
            if missing_in_schema:
                is_compatible = False
                incomp_reason = f"Fields {missing_in_schema} do not exist in dataset version {spec.dataset_version_id}."
                errors.append(
                    ValidationErrorItem(
                        code="SCHEMA_INCOMPATIBLE",
                        message=incomp_reason,
                        field=missing_in_schema[0],
                        suggested_fix="Reconfigure visual encodings for the current version.",
                    )
                )

        # 4. Aggregation check
        if spec.aggregation:
            agg_lower = spec.aggregation.lower()
            try:
                agg_type = AggregationType(agg_lower)
            except ValueError:
                errors.append(
                    ValidationErrorItem(
                        code="INVALID_AGGREGATION",
                        message=f"Unsupported aggregation '{spec.aggregation}'. Must be one of {[a.value for a in AggregationType]}.",
                    )
                )
            else:
                # If aggregation is numeric (SUM, AVG, MEDIAN), verify target field is numeric
                if agg_type in NUMERIC_AGGREGATIONS and schema_columns is not None:
                    target_field = spec.y or spec.x
                    if target_field and target_field in schema_columns:
                        col_type = schema_columns[target_field].lower()
                        if not any(t in col_type for t in ("int", "float", "double", "num", "dec", "real")):
                            warnings.append(
                                ValidationWarningItem(
                                    code="NON_NUMERIC_AGGREGATION",
                                    message=f"Applying {agg_type.value} on non-numeric column '{target_field}' ({col_type}) may fail.",
                                    field=target_field,
                                )
                            )

        # 5. Filter validation (VIZ-22, VIZ-50)
        for filt in spec.filters:
            if filt.operator not in VALID_OPERATORS:
                errors.append(
                    ValidationErrorItem(
                        code="INVALID_FILTER_OPERATOR",
                        message=f"Filter operator '{filt.operator}' is not permitted.",
                        field=filt.field,
                    )
                )
            # Prevent injection payloads in string values
            if isinstance(filt.value, str):
                val_lower = filt.value.lower()
                bad_tokens = ["<script", "javascript:", "eval(", "exec(", "; drop", "; delete", "; update", "; insert", "--"]
                if any(b in val_lower for b in bad_tokens):
                    errors.append(
                        ValidationErrorItem(
                            code="MALICIOUS_FILTER_INPUT",
                            message="Filter value contains prohibited script or SQL injection tokens.",
                            field=filt.field,
                        )
                    )

        # 6. Top-N validation
        if spec.top_n:
            if spec.top_n.n < 1 or spec.top_n.n > 100:
                warnings.append(
                    ValidationWarningItem(
                        code="TOP_N_OUT_OF_BOUNDS",
                        message=f"Top-N value {spec.top_n.n} clamped to valid range [1, 100].",
                    )
                )

        return VisualizationValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            is_compatible=is_compatible,
            incompatibility_reason=incomp_reason,
        )
