"""
Unit tests for SQL Filtering, Grouping & Aggregation pipeline (scripts/sql_filtering_grouping_aggregation.py).
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine

from scripts.sql_filtering_grouping_aggregation import (
    setup_database_connection,
    seed_database_tables,
    load_query,
    execute_filtering_pipeline,
    compute_percentage_share,
    validate_results,
)


@pytest.fixture
def memory_db_engine():
    """Fixture providing a seeded in-memory SQLite database engine."""
    engine = create_engine("sqlite:///:memory:")
    seed_database_tables(engine)
    return engine


def test_load_query_files():
    """Test that all 5 SQL query files exist and can be loaded cleanly."""
    query_names = [
        "where_filtering",
        "group_by_aggregation",
        "having_filtering",
        "where_having_combined",
        "order_by_ranking",
    ]
    for q_name in query_names:
        query_sql = load_query(q_name)
        assert isinstance(query_sql, str)
        assert len(query_sql.strip()) > 0
        assert "SELECT" in query_sql.upper()
        assert "FROM" in query_sql.upper()


def test_load_query_file_not_found():
    """Test error handling when requesting a non-existent query file."""
    with pytest.raises(FileNotFoundError):
        load_query("non_existent_sql_file")


def test_execute_filtering_pipeline(memory_db_engine):
    """Test execution of all 5 filtering and aggregation tasks."""
    results = execute_filtering_pipeline(memory_db_engine)

    assert "task1_where" in results
    assert "task2_group_by" in results
    assert "task3_having" in results
    assert "task4_combined" in results
    assert "task5_ranking" in results

    # Verify Task 1 columns
    t1_df = results["task1_where"]
    assert isinstance(t1_df, pd.DataFrame)
    assert "customer_id" in t1_df.columns
    assert "annual_revenue" in t1_df.columns
    assert "transaction_count" in t1_df.columns

    # Verify Task 2 columns (GROUP BY 2+ dimensions, 3+ aggregates)
    t2_df = results["task2_group_by"]
    assert "customer_type" in t2_df.columns
    assert "month" in t2_df.columns
    assert "unique_customers" in t2_df.columns
    assert "monthly_revenue" in t2_df.columns
    assert "avg_transaction" in t2_df.columns

    # Verify Task 3 columns (HAVING filter)
    t3_df = results["task3_having"]
    assert (t3_df["annual_revenue"] > 10000).all()
    assert (t3_df["transaction_count"] >= 5).all()

    # Verify Task 5 columns (ORDER BY & Ranking)
    t5_df = results["task5_ranking"]
    assert "revenue_rank" in t5_df.columns
    assert "industry" in t5_df.columns


def test_validate_results_success(memory_db_engine):
    """Test that validate_results returns True on valid output."""
    results = execute_filtering_pipeline(memory_db_engine)
    assert validate_results(results) is True


def test_percentage_share_computation(memory_db_engine):
    """Test percentage share computation returns percentages summing to ~100%."""
    pct_df = compute_percentage_share(memory_db_engine)
    assert isinstance(pct_df, pd.DataFrame)
    assert "pct_share_of_total" in pct_df.columns
    assert not pct_df.empty
    total_pct = pct_df["pct_share_of_total"].sum()
    assert abs(total_pct - 100.0) < 1.0
