"""
AnalyzaX — Phase 7: Datetime & Time-Series Analyzer
Analyzes timestamp spans, infers periodic frequencies, and builds aggregated time trends.
"""

from datetime import datetime
from typing import List, Optional
import polars as pl

from backend.app.engines.eda.models import DatetimeAnalysis, TimeSeriesPoint


class DatetimeAnalyzer:
    @classmethod
    def analyze(cls, df: pl.DataFrame, column: str) -> Optional[DatetimeAnalysis]:
        return cls.analyze_column(df, column)

    @classmethod
    def analyze_column(cls, df: pl.DataFrame, column: str) -> Optional[DatetimeAnalysis]:
        if column not in df.columns:
            return None

        col_series = df[column]
        total_len = len(col_series)
        null_cnt = col_series.null_count()
        null_pct = round((null_cnt / total_len * 100.0), 2) if total_len > 0 else 0.0

        clean_s = col_series.drop_nulls()
        valid_cnt = len(clean_s)
        if valid_cnt == 0:
            return DatetimeAnalysis(
                column=column,
                count=0,
                null_count=null_cnt,
                null_percentage=null_pct,
                unique_count=0,
                inferred_frequency="empty",
            )

        # Parse to Datetime if currently string
        dtype = clean_s.dtype
        if dtype == pl.Utf8:
            try:
                parsed_s = clean_s.str.to_datetime(strict=False)
                if parsed_s.null_count() == valid_cnt:
                    # Try date only
                    parsed_s = clean_s.str.to_date(strict=False).cast(pl.Datetime)
            except Exception:
                return None
        elif dtype.is_temporal():
            parsed_s = clean_s.cast(pl.Datetime)
        else:
            return None

        # Filter successfully parsed values
        valid_dt_s = parsed_s.drop_nulls()
        if len(valid_dt_s) == 0:
            return None

        min_dt = valid_dt_s.min()
        max_dt = valid_dt_s.max()
        unique_cnt = valid_dt_s.n_unique()

        span_days = None
        if min_dt is not None and max_dt is not None:
            span_seconds = (max_dt - min_dt).total_seconds()
            span_days = round(span_seconds / 86400.0, 2)

        # Frequency inference based on distinct date count and span
        freq = "irregular"
        if span_days is not None and span_days > 0 and unique_cnt > 3:
            avg_step_days = span_days / unique_cnt
            if 0.8 <= avg_step_days <= 1.2:
                freq = "daily"
            elif 6.0 <= avg_step_days <= 8.0:
                freq = "weekly"
            elif 25.0 <= avg_step_days <= 35.0:
                freq = "monthly"
            elif 340.0 <= avg_step_days <= 380.0:
                freq = "yearly"

        # Build temporal trend aggregation points (monthly or daily)
        trends: List[TimeSeriesPoint] = []
        try:
            temp_df = pl.DataFrame({"dt": valid_dt_s})
            if span_days is not None and span_days > 60:
                # Group by Month
                temp_df = temp_df.with_columns(pl.col("dt").dt.strftime("%Y-%m").alias("period"))
            else:
                # Group by Day
                temp_df = temp_df.with_columns(pl.col("dt").dt.strftime("%Y-%m-%d").alias("period"))

            grouped = (
                temp_df.group_by("period")
                .agg(pl.len().alias("count"))
                .sort("period")
            )

            for row in grouped.iter_rows(named=True):
                trends.append(
                    TimeSeriesPoint(
                        period=str(row["period"]),
                        timestamp=str(row["period"]),
                        count=int(row["count"]),
                    )
                )
        except Exception:
            pass

        def _fmt_dt(val):
            if val is None:
                return None
            if hasattr(val, "strftime"):
                if val.hour == 0 and val.minute == 0 and val.second == 0 and getattr(val, "microsecond", 0) == 0:
                    return val.strftime("%Y-%m-%d")
                return val.isoformat()
            s = str(val)
            if s.endswith(" 00:00:00"):
                return s.split(" ")[0]
            return s

        return DatetimeAnalysis(
            column=column,
            count=valid_cnt,
            null_count=null_cnt,
            null_percentage=null_pct,
            unique_count=unique_cnt,
            min_timestamp=_fmt_dt(min_dt),
            max_timestamp=_fmt_dt(max_dt),
            span_days=span_days,
            inferred_frequency=freq,
            temporal_trends=trends,
        )

    @classmethod
    def analyze_all(cls, df: pl.DataFrame, columns: List[str]) -> List[DatetimeAnalysis]:
        results = []
        for col in columns:
            res = cls.analyze_column(df, col)
            if res is not None:
                results.append(res)
        return results
