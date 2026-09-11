"""
AnalyzaX — Phase 11: Deterministic Preprocessing Pipeline.
Builds leakage-free scikit-learn ColumnTransformer / Pipelines fitted STRICTLY
on training data. Tracks transformations for feature importance back-mapping.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, OrdinalEncoder, RobustScaler, StandardScaler

from backend.app.core.config import settings
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import (
    CategoricalEncodeStrategy,
    CategoricalImputeStrategy,
    NumericImputeStrategy,
    NumericScaleStrategy,
    PreprocessingConfig,
    PreprocessingStep,
)


def build_preprocessing_pipeline(
    df_sample: pd.DataFrame,
    feature_columns: List[str],
    config: PreprocessingConfig,
) -> Tuple[ColumnTransformer, List[PreprocessingStep], List[str], List[str]]:
    """
    Constructs an unfitted ColumnTransformer tailored to the column types in feature_columns.
    Returns:
        (pipeline, steps_metadata, numeric_cols, categorical_cols)
    """
    numeric_cols: List[str] = []
    categorical_cols: List[str] = []
    boolean_cols: List[str] = []

    for col in feature_columns:
        if col not in df_sample.columns:
            raise MLException(
                f"Feature '{col}' not found in dataset columns.",
                MLErrorCode.ML_INVALID_FEATURES,
            )
        dtype = df_sample[col].dtype
        if pd.api.types.is_numeric_dtype(dtype) and not pd.api.types.is_bool_dtype(dtype):
            numeric_cols.append(col)
        elif pd.api.types.is_bool_dtype(dtype):
            boolean_cols.append(col)
        else:
            categorical_cols.append(col)

    # Boolean columns can be treated as numeric (0/1) with median or most_frequent imputation
    numeric_cols.extend(boolean_cols)

    transformers = []
    steps_meta: List[PreprocessingStep] = []
    step_order = 1

    # 1. Numeric Pipeline
    if numeric_cols:
        num_steps = []
        # Imputation
        if config.numeric_impute == NumericImputeStrategy.MEDIAN:
            num_steps.append(("imputer", SimpleImputer(strategy="median")))
        elif config.numeric_impute == NumericImputeStrategy.MEAN:
            num_steps.append(("imputer", SimpleImputer(strategy="mean")))
        elif config.numeric_impute == NumericImputeStrategy.CONSTANT:
            fill_val = config.numeric_impute_value if config.numeric_impute_value is not None else 0.0
            num_steps.append(("imputer", SimpleImputer(strategy="constant", fill_value=fill_val)))

        # Scaling
        if config.numeric_scale == NumericScaleStrategy.STANDARD:
            num_steps.append(("scaler", StandardScaler()))
        elif config.numeric_scale == NumericScaleStrategy.MINMAX:
            num_steps.append(("scaler", MinMaxScaler()))
        elif config.numeric_scale == NumericScaleStrategy.ROBUST:
            num_steps.append(("scaler", RobustScaler()))
        elif config.numeric_scale == NumericScaleStrategy.PASSTHROUGH:
            pass

        numeric_pipeline = Pipeline(num_steps)
        transformers.append(("numeric", numeric_pipeline, numeric_cols))

        steps_meta.append(
            PreprocessingStep(
                step_id="step_numeric_pipeline",
                operation=f"impute({config.numeric_impute.value}) + scale({config.numeric_scale.value})",
                input_columns=numeric_cols,
                output_columns=numeric_cols,
                parameters={"impute": config.numeric_impute.value, "scale": config.numeric_scale.value},
                ordering=step_order,
            )
        )
        step_order += 1

    # 2. Categorical Pipeline
    if categorical_cols:
        cat_steps = []
        # Imputation
        if config.categorical_impute == CategoricalImputeStrategy.MOST_FREQUENT:
            cat_steps.append(("imputer", SimpleImputer(strategy="most_frequent")))
        elif config.categorical_impute == CategoricalImputeStrategy.CONSTANT:
            cat_steps.append(
                ("imputer", SimpleImputer(strategy="constant", fill_value=config.categorical_impute_value or "missing"))
            )

        # Encoding
        if config.categorical_encode == CategoricalEncodeStrategy.ONE_HOT:
            cat_steps.append(
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False,
                        max_categories=getattr(settings, "ML_MAX_ONE_HOT_CARDINALITY", 50),
                    ),
                )
            )
        elif config.categorical_encode == CategoricalEncodeStrategy.ORDINAL:
            cat_steps.append(
                (
                    "encoder",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value",
                        unknown_value=-1,
                    ),
                )
            )

        categorical_pipeline = Pipeline(cat_steps)
        transformers.append(("categorical", categorical_pipeline, categorical_cols))

        steps_meta.append(
            PreprocessingStep(
                step_id="step_categorical_pipeline",
                operation=f"impute({config.categorical_impute.value}) + encode({config.categorical_encode.value})",
                input_columns=categorical_cols,
                output_columns=[f"{c}_encoded" for c in categorical_cols],
                parameters={
                    "impute": config.categorical_impute.value,
                    "encode": config.categorical_encode.value,
                    "handle_unknown": "ignore",
                },
                ordering=step_order,
            )
        )
        step_order += 1

    column_transformer = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )

    return column_transformer, steps_meta, numeric_cols, categorical_cols


def get_feature_names_and_mapping(
    fitted_transformer: ColumnTransformer,
    numeric_cols: List[str],
    categorical_cols: List[str],
) -> Tuple[List[str], Dict[str, str]]:
    """
    Extracts output feature names after transformation and constructs a dictionary
    mapping each transformed feature name back to its original source column.
    """
    feature_names: List[str] = []
    source_mapping: Dict[str, str] = {}

    try:
        names = list(fitted_transformer.get_feature_names_out())
        feature_names = names
        for feat in names:
            # Match transformed feature back to original categorical or numeric column
            matched = False
            for cat_col in categorical_cols:
                if feat.startswith(cat_col) or feat.startswith(f"categorical__{cat_col}"):
                    source_mapping[feat] = cat_col
                    matched = True
                    break
            if not matched:
                for num_col in numeric_cols:
                    if feat == num_col or feat == f"numeric__{num_col}":
                        source_mapping[feat] = num_col
                        matched = True
                        break
            if not matched:
                source_mapping[feat] = feat
    except Exception:
        # Fallback if get_feature_names_out fails
        for c in numeric_cols:
            feature_names.append(c)
            source_mapping[c] = c
        for c in categorical_cols:
            name = f"{c}_encoded"
            feature_names.append(name)
            source_mapping[name] = c

    return feature_names, source_mapping
