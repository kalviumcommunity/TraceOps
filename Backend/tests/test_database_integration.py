"""
Unit tests for SQL Environment & Database Integration (Tasks 1-5).
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from scripts.database_integration import (
    setup_database_connection,
    prepare_cleaned_customer_data,
    load_dataframe_to_table,
    validate_table_schema,
    execute_analytical_queries,
    load_cleaned_data_to_database,
)


@pytest.fixture
def sample_cleaned_df():
    """Fixture providing sample cleaned customer DataFrame."""
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'email': ['c1@ex.com', 'c2@ex.com', 'c3@ex.com', 'c4@ex.com', 'c5@ex.com'],
        'signup_date': ['2025-01-01'] * 5,
        'customer_type': ['Enterprise', 'SMB', 'Startup', 'Enterprise', 'SMB'],
        'product': ['Suite', 'Pro', 'Basic', 'Suite', 'Pro'],
        'churn': [0, 0, 1, 0, 0],
        'revenue': [15000.0, 500.0, 200.0, 12000.0, 600.0],
        'lifetime_value': [15000.0, 500.0, 200.0, 12000.0, 600.0],
        'support_tickets': [1, 3, 5, 2, 4]
    })


@pytest.fixture
def memory_db_engine():
    """Fixture providing in-memory SQLite database engine."""
    engine = create_engine("sqlite:///:memory:")
    return engine


def test_task1_setup_database_connection():
    """Task 1: Verify database connection setup and validation."""
    engine = setup_database_connection("sqlite:///:memory:")
    assert isinstance(engine, Engine)
    with engine.connect() as conn:
        val = conn.execute(text("SELECT 1")).scalar()
        assert val == 1


def test_task2_load_dataframe_to_table(sample_cleaned_df, memory_db_engine):
    """Task 2: Verify loading DataFrame to database table and verifying table existence & row count."""
    rows = load_dataframe_to_table(sample_cleaned_df, "test_customers", memory_db_engine, if_exists="replace")
    assert rows == 5

    inspector = inspect(memory_db_engine)
    tables = inspector.get_table_names()
    assert "test_customers" in tables

    count_df = pd.read_sql("SELECT COUNT(*) as ct FROM test_customers", memory_db_engine)
    assert count_df.iloc[0]['ct'] == 5


def test_task3_validate_table_schema(sample_cleaned_df, memory_db_engine):
    """Task 3: Verify schema inspection, column types, and data type validation."""
    load_dataframe_to_table(sample_cleaned_df, "test_customers", memory_db_engine, if_exists="replace")

    expected_types = {
        'customer_id': 'INTEGER',
        'email': 'VARCHAR',
        'signup_date': 'DATE'
    }

    report = validate_table_schema(memory_db_engine, "test_customers", expected_types)
    assert 'schema' in report
    assert 'validation' in report
    assert 'customer_id' in report['schema']
    assert report['validation']['customer_id']['valid'] is True


def test_task4_execute_analytical_queries(sample_cleaned_df, memory_db_engine):
    """Task 4: Verify simple SELECT query and SQL aggregation query execution into DataFrames."""
    load_dataframe_to_table(sample_cleaned_df, "test_customers", memory_db_engine, if_exists="replace")

    simple_df, agg_df = execute_analytical_queries(memory_db_engine, "test_customers")

    # Simple query test
    assert len(simple_df) == 2
    assert all(simple_df['customer_type'] == 'Enterprise')

    # Aggregation query test
    assert isinstance(agg_df, pd.DataFrame)
    assert 'customer_type' in agg_df.columns
    assert 'count' in agg_df.columns
    assert 'avg_ltv' in agg_df.columns
    assert len(agg_df) == 3  # Enterprise, SMB, Startup


def test_task5_repeatable_loading_wrapper(sample_cleaned_df, tmp_path):
    """Task 5: Verify reusable function load_cleaned_data_to_database."""
    db_file = os.path.join(tmp_path, "test_analytics.db")
    engine = load_cleaned_data_to_database(
        df=sample_cleaned_df,
        table_name="customers_cleaned",
        database_path=db_file,
        if_exists="replace"
    )

    assert isinstance(engine, Engine)
    assert os.path.exists(db_file)

    # Downstream reuse test
    res = pd.read_sql("SELECT COUNT(*) as ct FROM customers_cleaned", engine)
    assert res.iloc[0]['ct'] == len(sample_cleaned_df)
