"""
AnalyzaX — Phase 7: Missingness Analyzer
Analyzes data sparsity, complete vs incomplete records, and missingness co-occurrence patterns.
"""

from typing import List
import polars as pl

from backend.app.engines.eda.models import (
    ColumnMissingnessItem,
    MissingnessAnalysis,
    MissingnessCooccurrence,
)


class MissingnessAnalyzer:
    @staticmethod
    def analyze(df: pl.DataFrame) -> MissingnessAnalysis:
        n_rows = len(df)
        n_cols = len(df.columns)
        total_cells = n_rows * n_cols

        if n_rows == 0 or n_cols == 0:
            return MissingnessAnalysis(
                total_cells=0,
                total_missing_cells=0,
                overall_missing_percentage=0.0,
                complete_rows_count=0,
                incomplete_rows_count=0,
                column_missingness=[],
                cooccurrences=[],
            )

        col_missing_items: List[ColumnMissingnessItem] = []
        cols_with_missing: List[str] = []
        total_missing = 0

        for col in df.columns:
            null_count = df[col].null_count()
            total_missing += null_count
            pct = round((null_count / n_rows) * 100.0, 2)
            col_missing_items.append(
                ColumnMissingnessItem(
                    column=col,
                    missing_count=null_count,
                    missing_percentage=pct,
                )
            )
            if null_count > 0:
                cols_with_missing.append(col)

        # Sort column missingness descending
        col_missing_items.sort(key=lambda x: x.missing_percentage, reverse=True)

        overall_pct = round((total_missing / total_cells) * 100.0, 2) if total_cells > 0 else 0.0

        # Complete vs Incomplete rows
        complete_count = len(df.drop_nulls())
        incomplete_count = n_rows - complete_count

        # Co-occurrence analysis for columns with missing values (limit to top 10 to avoid explosion)
        cooccurrences: List[MissingnessCooccurrence] = []
        top_missing_cols = cols_with_missing[:10]

        for i in range(len(top_missing_cols)):
            col_a = top_missing_cols[i]
            for j in range(i + 1, len(top_missing_cols)):
                col_b = top_missing_cols[j]
                both_missing = (
                    df.filter(pl.col(col_a).is_null() & pl.col(col_b).is_null())
                    .shape[0]
                )
                if both_missing > 0:
                    # Ratio relative to minimum missing count between the two columns
                    min_missing = min(df[col_a].null_count(), df[col_b].null_count())
                    ratio = round(both_missing / min_missing, 4) if min_missing > 0 else 0.0
                    cooccurrences.append(
                        MissingnessCooccurrence(
                            column_a=col_a,
                            column_b=col_b,
                            both_missing_count=both_missing,
                            cooccurrence_ratio=ratio,
                        )
                    )

        cooccurrences.sort(key=lambda x: x.both_missing_count, reverse=True)

        return MissingnessAnalysis(
            total_cells=total_cells,
            total_missing_cells=total_missing,
            overall_missing_percentage=overall_pct,
            complete_rows_count=complete_count,
            incomplete_rows_count=incomplete_count,
            column_missingness=col_missing_items,
            cooccurrences=cooccurrences,
        )
