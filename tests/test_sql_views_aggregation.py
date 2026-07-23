"""
Unit tests for SQL Views & Aggregation Layer pipeline (scripts/sql_views_aggregation.py).
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine, text

from scripts.sql_views_aggregation import (
    setup_database_connection,
    prepare_database_schema,
    execute_sql_file,
    create_views_and_aggregations,
    query_data_layer,
    benchmark_query_performance,
)


@pytest.fixture
def test_db_engine():
    """Fixture to provide a database engine connected to analytics.db."""
    engine = create_engine("sqlite:///analytics.db")
    prepare_database_schema(engine)
    return engine


def test_sql_files_exist():
    """Test that all required version-controlled SQL files exist."""
    view1_file = os.path.join("database", "views", "vw_active_customers.sql")
    view2_file = os.path.join("database", "views", "vw_product_performance.sql")
    agg_file = os.path.join("database", "aggregations", "agg_daily_metrics.sql")

    for filepath in [view1_file, view2_file, agg_file]:
        assert os.path.exists(filepath), f"Missing SQL file: {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content.strip()) > 0
            assert "-- View:" in content or "-- Table" in content


def test_create_views_and_aggregations(test_db_engine):
    """Test execution of view and table creation DDL."""
    create_views_and_aggregations(test_db_engine)

    with test_db_engine.connect() as conn:
        # Check views exist in sqlite_master
        views = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='view'")
        ).fetchall()
        view_names = [v[0] for v in views]
        assert "vw_active_customers" in view_names
        assert "vw_product_performance" in view_names

        # Check table exists in sqlite_master
        tables = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "agg_daily_metrics" in table_names


def test_query_active_customers_view(test_db_engine):
    """Test querying vw_active_customers view structure and contents."""
    create_views_and_aggregations(test_db_engine)
    df = pd.read_sql("SELECT * FROM vw_active_customers LIMIT 10", test_db_engine)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_cols = [
        "customer_id",
        "customer_name",
        "segment",
        "order_count_30d",
        "revenue_30d",
        "last_order_date",
        "days_since_order",
    ]
    for col in expected_cols:
        assert col in df.columns


def test_query_product_performance_view(test_db_engine):
    """Test querying vw_product_performance view structure and contents."""
    create_views_and_aggregations(test_db_engine)
    df = pd.read_sql("SELECT * FROM vw_product_performance LIMIT 10", test_db_engine)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_cols = [
        "product_id",
        "product_name",
        "category",
        "total_orders",
        "units_sold",
        "total_revenue",
        "avg_unit_price",
        "last_sold_date",
    ]
    for col in expected_cols:
        assert col in df.columns


def test_query_agg_daily_metrics(test_db_engine):
    """Test structure, row population, and updated_at timestamp in agg_daily_metrics."""
    create_views_and_aggregations(test_db_engine)
    df = pd.read_sql("SELECT * FROM agg_daily_metrics LIMIT 10", test_db_engine)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_cols = [
        "aggregation_date",
        "metric_name",
        "metric_value",
        "row_count",
        "updated_at",
    ]
    for col in expected_cols:
        assert col in df.columns

    # Verify updated_at is populated
    assert df["updated_at"].notnull().all()


def test_benchmark_performance(test_db_engine):
    """Test benchmarking query performance on pre-aggregated table."""
    create_views_and_aggregations(test_db_engine)
    elapsed_ms, bench_df = benchmark_query_performance(test_db_engine)

    assert elapsed_ms >= 0.0
    assert isinstance(bench_df, pd.DataFrame)
    assert not bench_df.empty
    assert "total_value" in bench_df.columns
