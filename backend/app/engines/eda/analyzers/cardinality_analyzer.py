"""
AnalyzaX — Phase 7: Cardinality Analyzer
Classifies column cardinality and identifies constants and candidate unique identifiers.
"""

from typing import List
import polars as pl

from backend.app.engines.eda.models import (
    CardinalityAnalysis,
    CardinalityClass,
    CardinalityColumnSummary,
)


class CardinalityAnalyzer:
    @staticmethod
    def analyze(df: pl.DataFrame) -> CardinalityAnalysis:
        n_rows = len(df)
        columns_summary: List[CardinalityColumnSummary] = []
        constants: List[str] = []
        identifiers: List[str] = []

        if n_rows == 0:
            return CardinalityAnalysis(
                columns=[], constant_columns=[], identifier_candidates=[]
            )

        for col in df.columns:
            s = df[col]
            n_unique = s.n_unique()
            ratio = round(n_unique / n_rows, 4) if n_rows > 0 else 0.0

            # Classification
            if n_unique <= 1:
                c_class = CardinalityClass.CONSTANT
                constants.append(col)
                is_id = False
            elif ratio >= 0.9 and n_rows >= 10:
                c_class = CardinalityClass.UNIQUE
                is_id = True
                identifiers.append(col)
            elif n_unique <= 5:
                c_class = CardinalityClass.VERY_LOW
                is_id = False
            elif n_unique <= 20:
                c_class = CardinalityClass.LOW
                is_id = False
            elif n_unique <= 100:
                c_class = CardinalityClass.MEDIUM
                is_id = False
            else:
                c_class = CardinalityClass.HIGH
                is_id = False

            # Check column name heuristics for identifier candidate (e.g. id, _id, uuid)
            col_lower = col.lower()
            if (col_lower.endswith("_id") or col_lower == "id" or "uuid" in col_lower) and ratio > 0.8:
                is_id = True
                if col not in identifiers:
                    identifiers.append(col)

            columns_summary.append(
                CardinalityColumnSummary(
                    column=col,
                    unique_count=n_unique,
                    total_count=n_rows,
                    cardinality_ratio=ratio,
                    cardinality_class=c_class,
                    is_identifier_candidate=is_id,
                )
            )

        return CardinalityAnalysis(
            columns=columns_summary,
            constant_columns=constants,
            identifier_candidates=identifiers,
        )
