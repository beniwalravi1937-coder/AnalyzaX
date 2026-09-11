"""
AnalyzaX — Phase 7: Deterministic EDA Test Fixture
Generates a representative multi-type Polars DataFrame with missing values,
outliers, strong correlations, and temporal variations for comprehensive testing.
"""

from datetime import date, datetime
from typing import Optional
import polars as pl


def create_eda_test_df() -> pl.DataFrame:
    data = {
        "customer_id": [
            "CUST_001", "CUST_002", "CUST_003", "CUST_004", "CUST_005",
            "CUST_006", "CUST_007", "CUST_008", "CUST_009", "CUST_010",
            "CUST_011", "CUST_012", "CUST_013", "CUST_014", "CUST_015",
            "CUST_016", "CUST_017", "CUST_018", "CUST_019", "CUST_020",
        ],
        "age": [
            25, 34, 45, 29, 52,
            38, 41, 23, 61, 33,
            28, 47, 36, 55, 30,
            44, 39, 26, 50, 35,
        ],
        "gender": [
            "Female", "Male", "Female", "Male", "Female",
            "Male", "Female", "Male", "Female", "Male",
            "Female", "Male", "Female", "Male", "Female",
            "Male", "Female", "Male", "Female", "Male",
        ],
        "city": [
            "New York", "Chicago", "San Francisco", "Austin", "New York",
            "Chicago", None, "Austin", "New York", "Chicago",
            "San Francisco", "Austin", "New York", None, "San Francisco",
            "Austin", "New York", "Chicago", "San Francisco", "Austin",
        ],
        "income": [
            55000.0, 68000.0, 92000.0, 48000.0, 125000.0,
            74000.0, None, 42000.0, 160000.0, 61000.0,
            58000.0, 110000.0, 71000.0, None, 64000.0,
            98000.0, 83000.0, 46000.0, 450000.0, 69000.0,  # 450000 is an outlier
        ],
        "orders": [
            2, 4, 8, 3, 15,
            6, 7, 1, 20, 5,
            4, 12, 6, 16, 5,
            10, 8, 2, 22, 6,
        ],
        "revenue": [
            210.0, 420.0, 840.0, 315.0, 1575.0,
            630.0, 735.0, 105.0, 2100.0, 525.0,
            420.0, 1260.0, 630.0, 1680.0, 525.0,
            1050.0, 840.0, 210.0, 2310.0, 630.0,
        ],
        "signup_date": [
            "2023-01-15", "2023-01-20", "2023-02-10", "2023-02-28", "2023-03-05",
            "2023-03-18", "2023-04-02", "2023-04-15", "2023-05-01", "2023-05-20",
            "2023-06-08", "2023-06-25", "2023-07-12", "2023-07-30", "2023-08-14",
            "2023-08-29", "2023-09-10", "2023-09-28", "2023-10-15", "2023-10-31",
        ],
        "is_active": [
            True, True, True, True, True,
            True, True, False, True, True,
            True, True, True, True, True,
            True, False, True, True, True,  # 90% True (dominant class)
        ],
    }
    return pl.DataFrame(data)
