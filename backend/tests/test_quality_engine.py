"""
Unit tests for the Data Quality Engine
Tests rules, edge cases, scoring determinism, and issue taxonomy.
"""

import duckdb
import pytest
from backend.app.engines.profiling.engine import DatasetProfiler
from backend.app.engines.quality.engine import DataQualityEngine
from backend.app.engines.quality.models import Dimension, IssueType, Severity
from backend.app.engines.quality.rules.categories import CategoryConsistencyRule
from backend.app.engines.quality.rules.completeness import CompletenessRule
from backend.app.engines.quality.rules.duplicates import DuplicatesRule
from backend.app.engines.quality.rules.formats import FormatValidationRule
from backend.app.engines.quality.rules.identifiers import IdentifiersRule
from backend.app.engines.quality.rules.outliers import OutlierRiskRule
from backend.app.engines.quality.rules.ranges import RangeValidationRule
from backend.app.engines.quality.rules.types import TypeConsistencyRule
from backend.app.engines.quality.scoring import QualityScorer


@pytest.fixture
def memory_duckdb():
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()


def test_completeness_rule_missing_and_blank(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE test_completeness AS SELECT * FROM (
            VALUES
                (1, 'Alice', 'Engineering'),
                (2, 'Bob', NULL),
                (3, 'Charlie', '   '),
                (NULL, NULL, NULL)
        ) AS t(id, name, department);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_completeness", "ds_comp")

    rule = CompletenessRule()
    issues = rule.evaluate(conn, "test_completeness", profile)

    issue_types = [i.issue_type for i in issues]
    assert IssueType.EMPTY_ROW in issue_types  # row 4 is completely NULL
    assert IssueType.BLANK_STRINGS in issue_types  # department has '   '
    assert IssueType.MISSING_VALUES in issue_types or IssueType.HIGH_MISSINGNESS in issue_types


def test_duplicates_rule(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE test_duplicates AS SELECT * FROM (
            VALUES
                (1, 'Product A', 10.0),
                (1, 'Product A', 10.0),
                (2, 'Product B', 20.0),
                (2, 'Product B', 20.0),
                (3, 'Product C', 30.0)
        ) AS t(id, product, price);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_duplicates", "ds_dup")

    rule = DuplicatesRule()
    issues = rule.evaluate(conn, "test_duplicates", profile)

    assert len(issues) == 1
    issue = issues[0]
    assert issue.issue_type == IssueType.DUPLICATES
    assert issue.affected_rows == 2  # 2 redundant duplicate rows
    assert issue.dimension == Dimension.UNIQUENESS


def test_identifiers_rule_nulls_and_duplicates(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE test_id_integrity AS SELECT * FROM (
            VALUES
                (101, 'User 1'),
                (102, 'User 2'),
                (102, 'User 2 Duplicated'),
                (NULL, 'User 3 Null ID')
        ) AS t(user_id, name);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_id_integrity", "ds_id")

    rule = IdentifiersRule()
    issues = rule.evaluate(conn, "test_id_integrity", profile)

    issue_types = [i.issue_type for i in issues]
    assert IssueType.NULL_IDENTIFIER in issue_types
    assert IssueType.DUPLICATE_IDENTIFIER in issue_types
    for i in issues:
        assert i.dimension == Dimension.INTEGRITY


def test_range_validation_rule(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE test_ranges AS SELECT * FROM (
            VALUES
                (1, 25, 85.5, 45.0, -75.0, 500.0),
                (2, -5, 115.0, -95.0, 195.0, -50.0),
                (3, 145, -10.0, 30.0, 10.0, 250.0)
        ) AS t(id, age, completion_percentage, latitude, longitude, price);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_ranges", "ds_range")

    rule = RangeValidationRule()
    issues = rule.evaluate(conn, "test_ranges", profile)

    issue_types = [i.issue_type for i in issues]
    assert IssueType.NEGATIVE_VALUE in issue_types
    assert IssueType.INVALID_RANGE in issue_types


def test_categories_and_whitespace_rule(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE test_cats AS SELECT * FROM (
            VALUES
                (1, 'Male', ' Active'),
                (2, 'male', 'Active '),
                (3, 'MALE', 'Inactive'),
                (4, 'Female', 'Active')
        ) AS t(id, gender, status);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_cats", "ds_cats")

    rule = CategoryConsistencyRule()
    issues = rule.evaluate(conn, "test_cats", profile)

    issue_types = [i.issue_type for i in issues]
    assert IssueType.CATEGORY_INCONSISTENCY in issue_types  # Male / male / MALE
    assert IssueType.WHITESPACE_INCONSISTENCY in issue_types  # ' Active' / 'Active '


def test_format_validation_rule(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE test_formats AS SELECT * FROM (
            VALUES
                (1, 'valid@example.com', 'https://analyzax.io'),
                (2, 'invalid-email-at-domain', 'not_a_valid_url'),
                (3, 'test.user@company.org', 'http://localhost:3000')
        ) AS t(id, email, website_url);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_formats", "ds_fmt")

    rule = FormatValidationRule()
    issues = rule.evaluate(conn, "test_formats", profile)

    assert any(i.column_name == "email" for i in issues)
    assert any(i.column_name == "website_url" for i in issues)


def test_outlier_risk_rule(memory_duckdb):
    conn = memory_duckdb
    # Generate 100 rows with normal values ~50, plus 2 extreme outliers: 99999 and -5000
    conn.execute("""
        CREATE TABLE test_outliers AS
        SELECT
            range AS id,
            CASE
                WHEN range = 98 THEN 99999.0
                WHEN range = 99 THEN -5000.0
                ELSE 50.0 + (range % 10)
            END AS amount
        FROM range(100);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "test_outliers", "ds_outliers")

    rule = OutlierRiskRule()
    issues = rule.evaluate(conn, "test_outliers", profile)

    assert len(issues) == 1
    assert issues[0].issue_type == IssueType.OUTLIER_RISK
    assert issues[0].affected_rows == 2


def test_scoring_determinism_and_clamping(memory_duckdb):
    conn = memory_duckdb
    conn.execute("""
        CREATE TABLE clean_table AS SELECT * FROM (
            VALUES
                (1, 'Item 1', 10.0),
                (2, 'Item 2', 20.0),
                (3, 'Item 3', 30.0)
        ) AS t(item_id, name, price);
    """)

    profiler = DatasetProfiler()
    profile = profiler.profile_table(conn, "clean_table", "ds_clean")

    engine = DataQualityEngine()
    report1 = engine.evaluate(conn, "clean_table", profile)
    report2 = engine.evaluate(conn, "clean_table", profile)

    # Determinism
    assert report1.overall_score == report2.overall_score
    assert report1.total_issues == 0
    assert report1.overall_score == 100.0
    assert report1.overall_grade == "EXCELLENT"

    for dim_score in report1.dimension_scores.values():
        assert dim_score.score == 100.0
        assert dim_score.issue_count == 0
