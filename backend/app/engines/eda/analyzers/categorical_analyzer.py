"""
AnalyzaX — Phase 7: Univariate Categorical Analyzer
Computes class balance, top frequencies, rare category grouping, and cardinality classification.
"""

from typing import List, Optional
import polars as pl

from backend.app.engines.eda.models import (
    CardinalityClass,
    CategoryFrequencyItem,
    UnivariateCategorical,
)


class CategoricalAnalyzer:
    TOP_N = 10
    RARE_THRESHOLD_PCT = 1.0  # categories under 1% count as rare

    @classmethod
    def analyze(cls, df: pl.DataFrame, column: str) -> Optional[UnivariateCategorical]:
        return cls.analyze_column(df, column)

    @classmethod
    def analyze_column(cls, df: pl.DataFrame, column: str) -> Optional[UnivariateCategorical]:
        if column not in df.columns:
            return None

        col_series = df[column]
        total_len = len(col_series)
        null_cnt = col_series.null_count()
        null_pct = round((null_cnt / total_len * 100.0), 2) if total_len > 0 else 0.0

        clean_s = col_series.drop_nulls()
        valid_cnt = len(clean_s)
        if valid_cnt == 0:
            return UnivariateCategorical(
                column=column,
                count=0,
                null_count=null_cnt,
                null_percentage=null_pct,
                unique_count=0,
                cardinality_class=CardinalityClass.CONSTANT,
            )

        unique_cnt = clean_s.n_unique()
        ratio = (unique_cnt / valid_cnt) if valid_cnt > 0 else 0.0

        # Classify cardinality
        if unique_cnt == 1:
            card_class = CardinalityClass.CONSTANT
        elif unique_cnt <= 5:
            card_class = CardinalityClass.VERY_LOW
        elif unique_cnt <= 20:
            card_class = CardinalityClass.LOW
        elif unique_cnt <= 100:
            card_class = CardinalityClass.MEDIUM
        elif ratio >= 0.9 and valid_cnt >= 20:
            card_class = CardinalityClass.UNIQUE
        else:
            card_class = CardinalityClass.HIGH

        # Frequency distribution
        val_counts = clean_s.value_counts(sort=True)
        # val_counts has columns [column, "count"]
        val_col_name = val_counts.columns[0]
        cnt_col_name = val_counts.columns[1]

        top_items: List[CategoryFrequencyItem] = []
        other_cnt = 0
        rare_cnt = 0
        dominant_pct = 0.0

        for i, row in enumerate(val_counts.iter_rows(named=True)):
            val = str(row[val_col_name]) if row[val_col_name] is not None else "null"
            cnt = int(row[cnt_col_name])
            pct = round((cnt / valid_cnt * 100.0), 2)

            if i == 0:
                dominant_pct = pct

            if pct < cls.RARE_THRESHOLD_PCT:
                rare_cnt += 1

            if i < cls.TOP_N:
                top_items.append(CategoryFrequencyItem(
                    category=val,
                    count=cnt,
                    percentage=pct,
                ))
            else:
                other_cnt += cnt

        other_pct = round((other_cnt / valid_cnt * 100.0), 2) if valid_cnt > 0 else 0.0

        return UnivariateCategorical(
            column=column,
            count=valid_cnt,
            null_count=null_cnt,
            null_percentage=null_pct,
            unique_count=unique_cnt,
            cardinality_class=card_class,
            top_categories=top_items,
            other_count=other_cnt,
            other_percentage=other_pct,
            rare_categories_count=rare_cnt,
            dominant_category_percentage=dominant_pct,
        )

    @classmethod
    def analyze_all(cls, df: pl.DataFrame, columns: List[str]) -> List[UnivariateCategorical]:
        results = []
        for col in columns:
            res = cls.analyze_column(df, col)
            if res is not None:
                results.append(res)
        return results
