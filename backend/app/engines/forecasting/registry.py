"""
AnalyzaX — Phase 12: Central Forecasting Model Registry.
Exposes 8 robust, CPU-friendly statistical forecasting estimators with declarative
parameter schemas, validation rules, and recommendation priorities.
"""

from typing import Any, Dict, List, Optional
from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException
from backend.app.engines.forecasting.models import ForecastModelDefinition


class ForecastModelRegistry:
    """Central registry driving forecasting model discovery, UI selection, and validation."""

    def __init__(self):
        self._models: Dict[str, ForecastModelDefinition] = {}
        self._register_default_models()

    def register(self, definition: ForecastModelDefinition) -> None:
        self._models[definition.model_id] = definition

    def get(self, model_id: str) -> Optional[ForecastModelDefinition]:
        return self._models.get(model_id)

    def list_models(self) -> List[ForecastModelDefinition]:
        return sorted(list(self._models.values()), key=lambda m: m.recommendation_priority)

    def validate_parameters(self, model_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        definition = self.get(model_id)
        if not definition:
            raise ForecastException(
                code=ForecastErrorCode.FORECAST_INVALID_MODEL,
                message=f"Model '{model_id}' is not registered in the forecast model registry.",
            )

        merged = dict(definition.default_parameters)
        merged.update(params)

        # Validate against schema rules
        for key, value in params.items():
            if key not in definition.parameter_schema:
                raise ForecastException(
                    code=ForecastErrorCode.FORECAST_INVALID_PARAMETERS,
                    message=f"Unknown parameter '{key}' for model '{model_id}'.",
                )
            schema = definition.parameter_schema[key]
            val_type = schema.get("type")
            if val_type == "int" and not isinstance(value, int):
                try:
                    merged[key] = int(value)
                except (ValueError, TypeError):
                    raise ForecastException(
                        code=ForecastErrorCode.FORECAST_INVALID_PARAMETERS,
                        message=f"Parameter '{key}' must be an integer.",
                    )
            elif val_type == "float" and not isinstance(value, (int, float)):
                try:
                    merged[key] = float(value)
                except (ValueError, TypeError):
                    raise ForecastException(
                        code=ForecastErrorCode.FORECAST_INVALID_PARAMETERS,
                        message=f"Parameter '{key}' must be a float.",
                    )
            elif val_type == "enum" and value not in schema.get("allowed", []):
                raise ForecastException(
                    code=ForecastErrorCode.FORECAST_INVALID_PARAMETERS,
                    message=f"Parameter '{key}' value '{value}' not in allowed: {schema.get('allowed')}",
                )

            # Bounds
            if "min" in schema and merged[key] < schema["min"]:
                raise ForecastException(
                    code=ForecastErrorCode.FORECAST_INVALID_PARAMETERS,
                    message=f"Parameter '{key}' must be >= {schema['min']}",
                )
            if "max" in schema and merged[key] > schema["max"]:
                raise ForecastException(
                    code=ForecastErrorCode.FORECAST_INVALID_PARAMETERS,
                    message=f"Parameter '{key}' must be <= {schema['max']}",
                )

        return merged

    def _register_default_models(self) -> None:
        # 1. Naive Baseline
        self.register(
            ForecastModelDefinition(
                model_id="naive",
                display_name="Naive Baseline",
                description="Forecasts all future periods using the most recently observed value.",
                supports_seasonality=False,
                supports_trend=False,
                supports_prediction_intervals=True,
                default_parameters={},
                parameter_schema={},
                recommendation_priority=1,
            )
        )

        # 2. Seasonal Naive Baseline
        self.register(
            ForecastModelDefinition(
                model_id="seasonal_naive",
                display_name="Seasonal Naive Baseline",
                description="Forecasts future periods using the observation from the corresponding period of the previous seasonal cycle.",
                supports_seasonality=True,
                supports_trend=False,
                supports_prediction_intervals=True,
                default_parameters={"seasonal_period": 7},
                parameter_schema={
                    "seasonal_period": {
                        "type": "int",
                        "min": 2,
                        "max": 366,
                        "description": "Number of periods in a seasonal cycle (e.g., 7 for daily, 12 for monthly).",
                    }
                },
                recommendation_priority=2,
            )
        )

        # 3. Drift Baseline
        self.register(
            ForecastModelDefinition(
                model_id="drift",
                display_name="Random Walk with Drift",
                description="Forecasts future values by linearly projecting the historical average slope from first to last observation.",
                supports_seasonality=False,
                supports_trend=True,
                supports_prediction_intervals=True,
                default_parameters={},
                parameter_schema={},
                recommendation_priority=3,
            )
        )

        # 4. Simple Exponential Smoothing (SES)
        self.register(
            ForecastModelDefinition(
                model_id="simple_exp_smoothing",
                display_name="Simple Exponential Smoothing (SES)",
                description="Suitable for time series with no clear trend or seasonality, weighting recent observations exponentially higher.",
                supports_seasonality=False,
                supports_trend=False,
                supports_prediction_intervals=True,
                default_parameters={"smoothing_level": 0.2},
                parameter_schema={
                    "smoothing_level": {
                        "type": "float",
                        "min": 0.01,
                        "max": 0.99,
                        "description": "Alpha smoothing factor (closer to 1 gives more weight to recent data).",
                    }
                },
                recommendation_priority=4,
            )
        )

        # 5. Holt's Linear Trend
        self.register(
            ForecastModelDefinition(
                model_id="holt",
                display_name="Holt's Linear Trend",
                description="Captures linear upward or downward trends using separate level and slope smoothing equations.",
                supports_seasonality=False,
                supports_trend=True,
                supports_prediction_intervals=True,
                default_parameters={"damped_trend": False},
                parameter_schema={
                    "damped_trend": {
                        "type": "bool",
                        "description": "Whether to damp the trend over long forecast horizons.",
                    }
                },
                recommendation_priority=5,
            )
        )

        # 6. Holt-Winters Exponential Smoothing
        self.register(
            ForecastModelDefinition(
                model_id="holt_winters",
                display_name="Holt-Winters Exponential Smoothing",
                description="Triple exponential smoothing accounting for level, trend, and seasonal components.",
                supports_seasonality=True,
                supports_trend=True,
                supports_prediction_intervals=True,
                default_parameters={"trend": "add", "seasonal": "add", "seasonal_period": 7},
                parameter_schema={
                    "trend": {
                        "type": "enum",
                        "allowed": ["add", "mul", "none"],
                        "description": "Type of trend component.",
                    },
                    "seasonal": {
                        "type": "enum",
                        "allowed": ["add", "mul", "none"],
                        "description": "Type of seasonal component.",
                    },
                    "seasonal_period": {
                        "type": "int",
                        "min": 2,
                        "max": 366,
                        "description": "Seasonal cycle length.",
                    },
                },
                recommendation_priority=6,
            )
        )

        # 7. ARIMA
        self.register(
            ForecastModelDefinition(
                model_id="arima",
                display_name="ARIMA (AutoRegressive Integrated Moving Average)",
                description="Classical statistical time series model fitting p AR lags, d differences, and q MA shocks.",
                supports_seasonality=False,
                supports_trend=True,
                supports_prediction_intervals=True,
                default_parameters={"p": 1, "d": 1, "q": 1},
                parameter_schema={
                    "p": {"type": "int", "min": 0, "max": 5, "description": "Autoregressive order."},
                    "d": {"type": "int", "min": 0, "max": 2, "description": "Degree of differencing."},
                    "q": {"type": "int", "min": 0, "max": 5, "description": "Moving average order."},
                },
                recommendation_priority=7,
            )
        )

        # 8. SARIMA
        self.register(
            ForecastModelDefinition(
                model_id="sarima",
                display_name="SARIMA (Seasonal ARIMA)",
                description="Extends ARIMA with seasonal autoregressive (P), differencing (D), and moving average (Q) components.",
                supports_seasonality=True,
                supports_trend=True,
                supports_prediction_intervals=True,
                default_parameters={"p": 1, "d": 1, "q": 1, "P": 1, "D": 0, "Q": 1, "m": 7},
                parameter_schema={
                    "p": {"type": "int", "min": 0, "max": 4, "description": "Non-seasonal AR order."},
                    "d": {"type": "int", "min": 0, "max": 2, "description": "Non-seasonal differencing."},
                    "q": {"type": "int", "min": 0, "max": 4, "description": "Non-seasonal MA order."},
                    "P": {"type": "int", "min": 0, "max": 2, "description": "Seasonal AR order."},
                    "D": {"type": "int", "min": 0, "max": 1, "description": "Seasonal differencing."},
                    "Q": {"type": "int", "min": 0, "max": 2, "description": "Seasonal MA order."},
                    "m": {"type": "int", "min": 2, "max": 52, "description": "Seasonal cycle length."},
                },
                recommendation_priority=8,
            )
        )


forecast_model_registry = ForecastModelRegistry()
