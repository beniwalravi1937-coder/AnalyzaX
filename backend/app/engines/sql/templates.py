"""
AnalyzaX — Phase 8: Schema-Aware SQL Template Generator
Generates intelligent, executable SQL templates adapted to the columns,
types, and domain of the active dataset version.
"""

from typing import List, Optional
from backend.app.engines.sql.models import SQLTemplate, SchemaTableInfo


class SQLTemplateGenerator:
    """
    Produces context-aware SQL query templates for the schema explorer and quick-start bar.
    """

    @classmethod
    def generate_templates(cls, schema: SchemaTableInfo) -> List[SQLTemplate]:
        table_alias = schema.table_alias or "dataset"
        templates: List[SQLTemplate] = []

        num_cols = [c.name for c in schema.columns if c.semantic_type == "numeric"]
        cat_cols = [c.name for c in schema.columns if c.semantic_type == "categorical"]
        date_cols = [c.name for c in schema.columns if c.semantic_type == "datetime"]
        all_cols = [c.name for c in schema.columns]

        # 1. Preview Table
        templates.append(
            SQLTemplate(
                id="preview_rows",
                title="Preview Rows",
                description="View the first 25 records of the dataset",
                category="General",
                sql=f"SELECT * FROM {table_alias} LIMIT 25;",
            )
        )

        # 2. Record & Column Counts
        templates.append(
            SQLTemplate(
                id="count_records",
                title="Record Count",
                description="Count total records and distinct values",
                category="General",
                sql=f"SELECT count(*) AS total_rows FROM {table_alias};",
            )
        )

        # 3. Numeric Summary
        if num_cols:
            first_num = num_cols[0]
            templates.append(
                SQLTemplate(
                    id="numeric_summary",
                    title="Numeric Aggregations",
                    description=f"Calculate mean, min, max, and stddev for {first_num}",
                    category="Aggregation",
                    sql=(
                        f"SELECT\n"
                        f"  count({first_num}) AS non_null_count,\n"
                        f"  avg({first_num}) AS avg_val,\n"
                        f"  min({first_num}) AS min_val,\n"
                        f"  max({first_num}) AS max_val,\n"
                        f"  stddev({first_num}) AS stddev_val\n"
                        f"FROM {table_alias};"
                    ),
                )
            )

        # 4. Category Frequency Distribution
        if cat_cols:
            first_cat = cat_cols[0]
            templates.append(
                SQLTemplate(
                    id="category_frequency",
                    title="Category Frequencies",
                    description=f"Count occurrences by {first_cat}",
                    category="Aggregation",
                    sql=(
                        f"SELECT\n"
                        f"  {first_cat},\n"
                        f"  count(*) AS total_count,\n"
                        f"  round(count(*) * 100.0 / sum(count(*)) OVER (), 2) AS percentage\n"
                        f"FROM {table_alias}\n"
                        f"GROUP BY {first_cat}\n"
                        f"ORDER BY total_count DESC\n"
                        f"LIMIT 15;"
                    ),
                )
            )

        # 5. Null Analysis
        if all_cols:
            null_checks = ",\n  ".join(f"sum(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) AS {col}_nulls" for col in all_cols[:6])
            templates.append(
                SQLTemplate(
                    id="null_inspection",
                    title="Missingness Inspection",
                    description="Inspect null count across leading columns",
                    category="Data Quality",
                    sql=f"SELECT\n  {null_checks}\nFROM {table_alias};",
                )
            )

        # 6. Time-Series Aggregation
        if date_cols and num_cols:
            d_col = date_cols[0]
            n_col = num_cols[0]
            templates.append(
                SQLTemplate(
                    id="time_series_agg",
                    title="Temporal Trend",
                    description=f"Aggregate {n_col} by date",
                    category="Time Series",
                    sql=(
                        f"SELECT\n"
                        f"  date_trunc('day', cast({d_col} AS TIMESTAMP)) AS day,\n"
                        f"  count(*) AS record_count,\n"
                        f"  avg({n_col}) AS avg_metric,\n"
                        f"  sum({n_col}) AS total_metric\n"
                        f"FROM {table_alias}\n"
                        f"WHERE {d_col} IS NOT NULL\n"
                        f"GROUP BY 1\n"
                        f"ORDER BY 1 ASC\n"
                        f"LIMIT 100;"
                    ),
                )
            )

        # 7. Window Function Ranking
        if num_cols and cat_cols:
            c_col = cat_cols[0]
            n_col = num_cols[0]
            templates.append(
                SQLTemplate(
                    id="window_ranking",
                    title="Window Function Ranking",
                    description=f"Rank records within {c_col} by {n_col}",
                    category="Advanced",
                    sql=(
                        f"SELECT\n"
                        f"  {c_col},\n"
                        f"  {n_col},\n"
                        f"  row_number() OVER (PARTITION BY {c_col} ORDER BY {n_col} DESC) AS rank_in_group\n"
                        f"FROM {table_alias}\n"
                        f"WHERE {n_col} IS NOT NULL\n"
                        f"QUALIFY rank_in_group <= 3\n"
                        f"ORDER BY {c_col}, rank_in_group;"
                    ),
                )
            )

        # 8. Duplicate Detection
        if len(all_cols) >= 2:
            key_cols = ", ".join(all_cols[:2])
            templates.append(
                SQLTemplate(
                    id="find_duplicates",
                    title="Duplicate Row Check",
                    description=f"Identify records with duplicate values on ({key_cols})",
                    category="Data Quality",
                    sql=(
                        f"SELECT\n"
                        f"  {key_cols},\n"
                        f"  count(*) AS occurrences\n"
                        f"FROM {table_alias}\n"
                        f"GROUP BY {key_cols}\n"
                        f"HAVING count(*) > 1\n"
                        f"ORDER BY occurrences DESC\n"
                        f"LIMIT 50;"
                    ),
                )
            )

        return templates
