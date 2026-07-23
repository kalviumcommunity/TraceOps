"""
Unit tests for SQL Business Metrics Query Design pipeline (scripts/sql_business_metrics.py).
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine

from scripts.sql_business_metrics import (
    setup_database_connection,
    seed_database_tables,
    load_query,
    execute_metrics_pipeline,
    validate_metrics,
)


@pytest.fixture
def memory_db_engine():
    """Fixture to provide a seeded in-memory database engine."""
    engine = create_engine("sqlite:///:memory:")
    seed_database_tables(engine)
    return engine


def test_load_query_files():
    """Test that all required SQL query files exist and can be loaded."""
    for query_name in ["monthly_active_users", "revenue_by_segment", "conversion_funnel", "active_users"]:
        query_sql = load_query(query_name)
        assert isinstance(query_sql, str)
        assert len(query_sql.strip()) > 0
        assert "SELECT" in query_sql.upper()
        assert "FROM" in query_sql.upper()


def test_load_query_file_not_found():
    """Test error handling when query file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_query("non_existent_metric_query")


def test_execute_metrics_pipeline(memory_db_engine):
    """Test execution of metric queries returning structured DataFrames."""
    mau_df, revenue_df, funnel_df = execute_metrics_pipeline(memory_db_engine)

    # Validate MAU DataFrame structure
    assert isinstance(mau_df, pd.DataFrame)
    assert not mau_df.empty
    expected_mau_cols = ["month", "active_users", "enterprise_users", "smb_users"]
    for col in expected_mau_cols:
        assert col in mau_df.columns

    # Validate Revenue DataFrame structure
    assert isinstance(revenue_df, pd.DataFrame)
    assert not revenue_df.empty
    expected_rev_cols = [
        "customer_type",
        "month",
        "order_count",
        "monthly_revenue",
        "avg_order_value",
        "unique_customers",
        "revenue_per_customer",
    ]
    for col in expected_rev_cols:
        assert col in revenue_df.columns

    # Validate Funnel DataFrame structure
    assert isinstance(funnel_df, pd.DataFrame)
    assert not funnel_df.empty
    expected_funnel_cols = [
        "signup_date",
        "signups",
        "email_verified",
        "first_purchase",
        "conversion_pct",
    ]
    for col in expected_funnel_cols:
        assert col in funnel_df.columns


def test_validate_metrics_success(memory_db_engine):
    """Test that validate_metrics returns True for valid metric DataFrames."""
    mau_df, revenue_df, funnel_df = execute_metrics_pipeline(memory_db_engine)
    result = validate_metrics(mau_df, revenue_df, funnel_df)
    assert result is True


def test_validate_metrics_null_error(memory_db_engine):
    """Test validate_metrics raises AssertionError when null values exist."""
    mau_df, revenue_df, funnel_df = execute_metrics_pipeline(memory_db_engine)
    mau_df.loc[0, "active_users"] = None
    with pytest.raises(AssertionError, match="MAU has nulls"):
        validate_metrics(mau_df, revenue_df, funnel_df)


def test_validate_metrics_invalid_revenue_range(memory_db_engine):
    """Test validate_metrics raises AssertionError when revenue is negative."""
    mau_df, revenue_df, funnel_df = execute_metrics_pipeline(memory_db_engine)
    revenue_df.loc[0, "monthly_revenue"] = -50.0
    with pytest.raises(AssertionError, match="Revenue <= 0"):
        validate_metrics(mau_df, revenue_df, funnel_df)


def test_validate_metrics_invalid_conversion_percentage(memory_db_engine):
    """Test validate_metrics raises AssertionError when conversion percentage is invalid."""
    mau_df, revenue_df, funnel_df = execute_metrics_pipeline(memory_db_engine)
    funnel_df.loc[0, "conversion_pct"] = 150.0
    with pytest.raises(AssertionError, match="Conversion out of range"):
        validate_metrics(mau_df, revenue_df, funnel_df)
