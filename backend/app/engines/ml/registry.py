"""
AnalyzaX — Phase 11: Machine Learning Model Registry.
Central catalog of supported estimators, parameter schemas, capability flags, and factories.
"""

from typing import Any, Callable, Dict, List, Optional
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.cluster import KMeans, MiniBatchKMeans

from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import (
    HyperparameterDefinition,
    MLModelDefinition,
    MLTaskType,
)


class MLModelRegistry:
    """Central registry of supported ML models, hyperparameter definitions, and estimator factories."""

    def __init__(self) -> None:
        self._models: Dict[str, MLModelDefinition] = {}
        self._factories: Dict[str, Callable[[Dict[str, Any], int], Any]] = {}
        self._register_all()

    def _register(
        self,
        definition: MLModelDefinition,
        factory: Callable[[Dict[str, Any], int], Any],
    ) -> None:
        self._models[definition.model_id] = definition
        self._factories[definition.model_id] = factory

    def get_model(self, model_id: str) -> MLModelDefinition:
        if model_id not in self._models:
            raise MLException(
                f"Model '{model_id}' is not registered in the ML registry.",
                error_code=MLErrorCode.ML_UNSUPPORTED_MODEL,
            )
        return self._models[model_id]

    def list_models(self, task_type: Optional[MLTaskType] = None) -> List[MLModelDefinition]:
        models = list(self._models.values())
        if task_type:
            models = [m for m in models if task_type in m.task_types]
        return sorted(models, key=lambda m: m.recommendation_priority)

    def create_estimator(self, model_id: str, parameters: Dict[str, Any], random_seed: int = 42) -> Any:
        if model_id not in self._factories:
            raise MLException(
                f"Estimator factory for '{model_id}' not found.",
                error_code=MLErrorCode.ML_UNSUPPORTED_MODEL,
            )
        # Validate parameters against schema
        validated_params = self.validate_parameters(model_id, parameters)
        return self._factories[model_id](validated_params, random_seed)

    def validate_parameters(self, model_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        defn = self.get_model(model_id)
        schema_map = {p.name: p for p in defn.parameter_schema}
        sanitized: Dict[str, Any] = dict(defn.default_parameters)

        for k, v in params.items():
            if k not in schema_map:
                continue  # ignore unknown or arbitrary keys safely
            spec = schema_map[k]
            # Validate types & ranges
            if spec.param_type == "int":
                try:
                    val_int = int(v)
                    if spec.min_val is not None and val_int < spec.min_val:
                        raise ValueError(f"{k} must be >= {spec.min_val}")
                    if spec.max_val is not None and val_int > spec.max_val:
                        raise ValueError(f"{k} must be <= {spec.max_val}")
                    sanitized[k] = val_int
                except Exception as e:
                    raise MLException(f"Invalid integer parameter '{k}': {e}", MLErrorCode.ML_TRAINING_ERROR)
            elif spec.param_type == "float":
                try:
                    val_float = float(v)
                    if spec.min_val is not None and val_float < spec.min_val:
                        raise ValueError(f"{k} must be >= {spec.min_val}")
                    if spec.max_val is not None and val_float > spec.max_val:
                        raise ValueError(f"{k} must be <= {spec.max_val}")
                    sanitized[k] = val_float
                except Exception as e:
                    raise MLException(f"Invalid float parameter '{k}': {e}", MLErrorCode.ML_TRAINING_ERROR)
            elif spec.param_type == "choice":
                if spec.allowed_values and v not in spec.allowed_values:
                    raise MLException(
                        f"Parameter '{k}' must be one of {spec.allowed_values}, got '{v}'",
                        MLErrorCode.ML_TRAINING_ERROR,
                    )
                sanitized[k] = v
            elif spec.param_type == "bool":
                sanitized[k] = bool(v)
            else:
                sanitized[k] = v

        return sanitized

    def _register_all(self) -> None:
        # =====================================================================
        # BASELINES
        # =====================================================================
        self._register(
            MLModelDefinition(
                model_id="dummy_regressor",
                display_name="Baseline: Dummy Regressor",
                description="Predicts the training set mean or median as a reference performance benchmark.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"strategy": "mean"},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="strategy",
                        display_name="Strategy",
                        param_type="choice",
                        default="mean",
                        allowed_values=["mean", "median"],
                        description="Strategy used to predict target values.",
                    )
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=False,
                resource_class="light",
                recommendation_priority=999,
            ),
            lambda p, s: DummyRegressor(strategy=p.get("strategy", "mean")),
        )

        self._register(
            MLModelDefinition(
                model_id="dummy_classifier",
                display_name="Baseline: Dummy Classifier",
                description="Predicts majority class or class priors as a reference performance benchmark.",
                task_types=[MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION],
                default_parameters={"strategy": "prior"},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="strategy",
                        display_name="Strategy",
                        param_type="choice",
                        default="prior",
                        allowed_values=["prior", "most_frequent"],
                        description="Strategy used to predict target class.",
                    )
                ],
                supports_probability=True,
                supports_feature_importance=False,
                supports_coefficients=False,
                resource_class="light",
                recommendation_priority=999,
            ),
            lambda p, s: DummyClassifier(strategy=p.get("strategy", "prior"), random_state=s),
        )

        # =====================================================================
        # REGRESSION MODELS
        # =====================================================================
        self._register(
            MLModelDefinition(
                model_id="linear_regression",
                display_name="Ordinary Least Squares (Linear Regression)",
                description="Classical linear regression fitting optimal linear coefficients minimizing residual sum of squares.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"fit_intercept": True},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="fit_intercept",
                        display_name="Fit Intercept",
                        param_type="bool",
                        default=True,
                        description="Whether to calculate the intercept for this model.",
                    )
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=True,
                resource_class="light",
                recommendation_priority=1,
            ),
            lambda p, s: LinearRegression(fit_intercept=p.get("fit_intercept", True)),
        )

        self._register(
            MLModelDefinition(
                model_id="ridge",
                display_name="Ridge Regression (L2 Regularized)",
                description="Linear least squares with L2 penalty, stabilizing estimates and reducing multicollinearity.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"alpha": 1.0},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="alpha",
                        display_name="Regularization Strength (alpha)",
                        param_type="float",
                        default=1.0,
                        min_val=0.0001,
                        max_val=1000.0,
                        description="L2 regularization weight.",
                    )
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=True,
                resource_class="light",
                recommendation_priority=2,
            ),
            lambda p, s: Ridge(alpha=p.get("alpha", 1.0), random_state=s),
        )

        self._register(
            MLModelDefinition(
                model_id="lasso",
                display_name="Lasso Regression (L1 Regularized)",
                description="Linear regression with L1 penalty, encouraging sparse coefficients and performing intrinsic feature selection.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"alpha": 1.0, "max_iter": 2000},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="alpha",
                        display_name="Regularization Strength (alpha)",
                        param_type="float",
                        default=1.0,
                        min_val=0.0001,
                        max_val=1000.0,
                        description="L1 regularization weight.",
                    ),
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=2000,
                        min_val=100,
                        max_val=10000,
                        description="Maximum number of coordinate descent iterations.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=True,
                resource_class="light",
                recommendation_priority=3,
            ),
            lambda p, s: Lasso(alpha=p.get("alpha", 1.0), max_iter=p.get("max_iter", 2000), random_state=s),
        )

        self._register(
            MLModelDefinition(
                model_id="elastic_net",
                display_name="ElasticNet (L1 + L2 Regularized)",
                description="Linear regression combining L1 and L2 penalties for balanced sparsity and collinearity management.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"alpha": 1.0, "l1_ratio": 0.5, "max_iter": 2000},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="alpha",
                        display_name="Regularization Strength (alpha)",
                        param_type="float",
                        default=1.0,
                        min_val=0.0001,
                        max_val=1000.0,
                        description="Overall penalty weight.",
                    ),
                    HyperparameterDefinition(
                        name="l1_ratio",
                        display_name="L1 Ratio",
                        param_type="float",
                        default=0.5,
                        min_val=0.0,
                        max_val=1.0,
                        description="Mixing parameter (0 = pure L2, 1 = pure L1).",
                    ),
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=2000,
                        min_val=100,
                        max_val=10000,
                        description="Maximum number of coordinate descent iterations.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=True,
                resource_class="light",
                recommendation_priority=4,
            ),
            lambda p, s: ElasticNet(
                alpha=p.get("alpha", 1.0),
                l1_ratio=p.get("l1_ratio", 0.5),
                max_iter=p.get("max_iter", 2000),
                random_state=s,
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="random_forest_regressor",
                display_name="Random Forest Regressor",
                description="Ensemble of randomized decision trees averaging predictions to model non-linear patterns with low variance.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"n_estimators": 100, "max_depth": 10, "min_samples_split": 2},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="n_estimators",
                        display_name="Number of Trees",
                        param_type="int",
                        default=100,
                        min_val=10,
                        max_val=300,
                        description="Number of trees in the forest.",
                    ),
                    HyperparameterDefinition(
                        name="max_depth",
                        display_name="Max Depth",
                        param_type="int",
                        default=10,
                        min_val=2,
                        max_val=30,
                        description="Maximum depth of each decision tree.",
                    ),
                    HyperparameterDefinition(
                        name="min_samples_split",
                        display_name="Min Samples Split",
                        param_type="int",
                        default=2,
                        min_val=2,
                        max_val=20,
                        description="Minimum number of samples required to split an internal node.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=True,
                supports_coefficients=False,
                resource_class="medium",
                recommendation_priority=5,
            ),
            lambda p, s: RandomForestRegressor(
                n_estimators=p.get("n_estimators", 100),
                max_depth=p.get("max_depth", 10),
                min_samples_split=p.get("min_samples_split", 2),
                random_state=s,
                n_jobs=-1,
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="gradient_boosting_regressor",
                display_name="Gradient Boosting Regressor",
                description="Sequential tree ensemble minimizing gradient loss step-by-step for high predictive accuracy.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="n_estimators",
                        display_name="Number of Boosting Stages",
                        param_type="int",
                        default=100,
                        min_val=10,
                        max_val=300,
                        description="Number of sequential boosting stages.",
                    ),
                    HyperparameterDefinition(
                        name="learning_rate",
                        display_name="Learning Rate",
                        param_type="float",
                        default=0.1,
                        min_val=0.01,
                        max_val=1.0,
                        description="Shrinkage factor per boosting step.",
                    ),
                    HyperparameterDefinition(
                        name="max_depth",
                        display_name="Max Tree Depth",
                        param_type="int",
                        default=3,
                        min_val=1,
                        max_val=10,
                        description="Maximum depth of individual regression estimators.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=True,
                supports_coefficients=False,
                resource_class="medium",
                recommendation_priority=6,
            ),
            lambda p, s: GradientBoostingRegressor(
                n_estimators=p.get("n_estimators", 100),
                learning_rate=p.get("learning_rate", 0.1),
                max_depth=p.get("max_depth", 3),
                random_state=s,
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="hist_gradient_boosting_regressor",
                display_name="Histogram Gradient Boosting Regressor",
                description="High-speed binned gradient boosting optimized for larger datasets, with native missing-value tolerance.",
                task_types=[MLTaskType.REGRESSION],
                default_parameters={"max_iter": 100, "learning_rate": 0.1, "max_depth": 6},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=100,
                        min_val=20,
                        max_val=300,
                        description="Maximum boosting iterations.",
                    ),
                    HyperparameterDefinition(
                        name="learning_rate",
                        display_name="Learning Rate",
                        param_type="float",
                        default=0.1,
                        min_val=0.01,
                        max_val=1.0,
                        description="Shrinkage parameter.",
                    ),
                    HyperparameterDefinition(
                        name="max_depth",
                        display_name="Max Depth",
                        param_type="int",
                        default=6,
                        min_val=2,
                        max_val=15,
                        description="Maximum tree depth.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=False,
                resource_class="light",
                recommendation_priority=7,
            ),
            lambda p, s: HistGradientBoostingRegressor(
                max_iter=p.get("max_iter", 100),
                learning_rate=p.get("learning_rate", 0.1),
                max_depth=p.get("max_depth", 6),
                random_state=s,
            ),
        )

        # =====================================================================
        # CLASSIFICATION MODELS
        # =====================================================================
        self._register(
            MLModelDefinition(
                model_id="logistic_regression",
                display_name="Logistic Regression",
                description="Linear model predicting class probabilities via sigmoid or softmax transformation.",
                task_types=[MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION],
                default_parameters={"C": 1.0, "max_iter": 1000},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="C",
                        display_name="Inverse Regularization Strength (C)",
                        param_type="float",
                        default=1.0,
                        min_val=0.001,
                        max_val=1000.0,
                        description="Smaller values specify stronger regularization.",
                    ),
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=1000,
                        min_val=100,
                        max_val=5000,
                        description="Maximum solver convergence iterations.",
                    ),
                ],
                supports_probability=True,
                supports_feature_importance=False,
                supports_coefficients=True,
                resource_class="light",
                recommendation_priority=1,
            ),
            lambda p, s: LogisticRegression(
                C=p.get("C", 1.0),
                max_iter=p.get("max_iter", 1000),
                random_state=s,
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="random_forest_classifier",
                display_name="Random Forest Classifier",
                description="Ensemble of randomized classification trees aggregating majority votes or class probabilities.",
                task_types=[MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION],
                default_parameters={"n_estimators": 100, "max_depth": 10, "min_samples_split": 2},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="n_estimators",
                        display_name="Number of Trees",
                        param_type="int",
                        default=100,
                        min_val=10,
                        max_val=300,
                        description="Number of trees in the forest.",
                    ),
                    HyperparameterDefinition(
                        name="max_depth",
                        display_name="Max Tree Depth",
                        param_type="int",
                        default=10,
                        min_val=2,
                        max_val=30,
                        description="Maximum depth of each tree.",
                    ),
                    HyperparameterDefinition(
                        name="min_samples_split",
                        display_name="Min Samples Split",
                        param_type="int",
                        default=2,
                        min_val=2,
                        max_val=20,
                        description="Minimum number of samples required to split a node.",
                    ),
                ],
                supports_probability=True,
                supports_feature_importance=True,
                supports_coefficients=False,
                resource_class="medium",
                recommendation_priority=2,
            ),
            lambda p, s: RandomForestClassifier(
                n_estimators=p.get("n_estimators", 100),
                max_depth=p.get("max_depth", 10),
                min_samples_split=p.get("min_samples_split", 2),
                random_state=s,
                n_jobs=-1,
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="gradient_boosting_classifier",
                display_name="Gradient Boosting Classifier",
                description="Additive forward boosting of trees with negative log-likelihood loss for classification.",
                task_types=[MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION],
                default_parameters={"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="n_estimators",
                        display_name="Number of Boosting Stages",
                        param_type="int",
                        default=100,
                        min_val=10,
                        max_val=300,
                        description="Number of boosting stages to perform.",
                    ),
                    HyperparameterDefinition(
                        name="learning_rate",
                        display_name="Learning Rate",
                        param_type="float",
                        default=0.1,
                        min_val=0.01,
                        max_val=1.0,
                        description="Shrinkage parameter.",
                    ),
                    HyperparameterDefinition(
                        name="max_depth",
                        display_name="Max Depth",
                        param_type="int",
                        default=3,
                        min_val=1,
                        max_val=10,
                        description="Maximum depth of individual estimators.",
                    ),
                ],
                supports_probability=True,
                supports_feature_importance=True,
                supports_coefficients=False,
                resource_class="medium",
                recommendation_priority=3,
            ),
            lambda p, s: GradientBoostingClassifier(
                n_estimators=p.get("n_estimators", 100),
                learning_rate=p.get("learning_rate", 0.1),
                max_depth=p.get("max_depth", 3),
                random_state=s,
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="hist_gradient_boosting_classifier",
                display_name="Histogram Gradient Boosting Classifier",
                description="Fast binned gradient tree boosting with native missing-value tolerance and multi-core scalability.",
                task_types=[MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION],
                default_parameters={"max_iter": 100, "learning_rate": 0.1, "max_depth": 6},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=100,
                        min_val=20,
                        max_val=300,
                        description="Number of boosting rounds.",
                    ),
                    HyperparameterDefinition(
                        name="learning_rate",
                        display_name="Learning Rate",
                        param_type="float",
                        default=0.1,
                        min_val=0.01,
                        max_val=1.0,
                        description="Shrinkage factor.",
                    ),
                    HyperparameterDefinition(
                        name="max_depth",
                        display_name="Max Depth",
                        param_type="int",
                        default=6,
                        min_val=2,
                        max_val=15,
                        description="Maximum tree depth.",
                    ),
                ],
                supports_probability=True,
                supports_feature_importance=False,
                supports_coefficients=False,
                resource_class="light",
                recommendation_priority=4,
            ),
            lambda p, s: HistGradientBoostingClassifier(
                max_iter=p.get("max_iter", 100),
                learning_rate=p.get("learning_rate", 0.1),
                max_depth=p.get("max_depth", 6),
                random_state=s,
            ),
        )

        # =====================================================================
        # CLUSTERING MODELS
        # =====================================================================
        self._register(
            MLModelDefinition(
                model_id="kmeans",
                display_name="K-Means Clustering",
                description="Partitions data into k Voronoi cells minimizing within-cluster sum-of-squares (inertia).",
                task_types=[MLTaskType.CLUSTERING],
                default_parameters={"n_clusters": 3, "max_iter": 300},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="n_clusters",
                        display_name="Number of Clusters (k)",
                        param_type="int",
                        default=3,
                        min_val=2,
                        max_val=20,
                        description="The number of clusters to form.",
                    ),
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=300,
                        min_val=50,
                        max_val=1000,
                        description="Maximum number of iterations of the k-means algorithm for a single run.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=False,
                resource_class="light",
                recommendation_priority=1,
            ),
            lambda p, s: KMeans(
                n_clusters=p.get("n_clusters", 3),
                max_iter=p.get("max_iter", 300),
                random_state=s,
                n_init="auto",
            ),
        )

        self._register(
            MLModelDefinition(
                model_id="minibatch_kmeans",
                display_name="Mini-Batch K-Means",
                description="Fast approximate K-Means using mini-batches to optimize convergence speed on large datasets.",
                task_types=[MLTaskType.CLUSTERING],
                default_parameters={"n_clusters": 3, "batch_size": 256, "max_iter": 100},
                parameter_schema=[
                    HyperparameterDefinition(
                        name="n_clusters",
                        display_name="Number of Clusters (k)",
                        param_type="int",
                        default=3,
                        min_val=2,
                        max_val=20,
                        description="The number of clusters to form.",
                    ),
                    HyperparameterDefinition(
                        name="batch_size",
                        display_name="Batch Size",
                        param_type="int",
                        default=256,
                        min_val=32,
                        max_val=2048,
                        description="Size of the mini-batches.",
                    ),
                    HyperparameterDefinition(
                        name="max_iter",
                        display_name="Max Iterations",
                        param_type="int",
                        default=100,
                        min_val=20,
                        max_val=500,
                        description="Maximum iterations over the complete dataset.",
                    ),
                ],
                supports_probability=False,
                supports_feature_importance=False,
                supports_coefficients=False,
                resource_class="light",
                recommendation_priority=2,
            ),
            lambda p, s: MiniBatchKMeans(
                n_clusters=p.get("n_clusters", 3),
                batch_size=p.get("batch_size", 256),
                max_iter=p.get("max_iter", 100),
                random_state=s,
                n_init="auto",
            ),
        )


model_registry = MLModelRegistry()
