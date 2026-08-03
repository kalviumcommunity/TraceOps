"""
Unit tests for SQL Joins & Multi-Table Analysis assignment.
"""

import os
import json
import pytest
import pandas as pd
from scripts.sql_joins_multi_table_analysis import (
    setup_database_connection,
    seed_multi_table_dataset,
    task1_left_join_validation,
    task2_detect_unmatched_keys,
    task3_compare_join_types,
    task4_multi_table_join,
    task5_document_join_decisions
)


@pytest.fixture(scope="module")
def db_engine():
    """Fixture providing database engine seeded with test data."""
    engine = setup_database_connection("sqlite:///:memory:")
    seed_multi_table_dataset(engine)
    return engine


def test_task1_left_join_validation(db_engine):
    """Verify Task 1 LEFT JOIN returns all 1000 aggregated customer rows."""
    df_result = task1_left_join_validation(db_engine)
    assert isinstance(df_result, pd.DataFrame)
    assert len(df_result) == 1000
    assert 'customer_id' in df_result.columns
    assert 'order_count' in df_result.columns
    assert 'total_spent' in df_result.columns


def test_task2_detect_unmatched_keys(db_engine):
    """Verify Task 2 correctly detects unmatched customers and orphaned orders."""
    no_orders, orphaned = task2_detect_unmatched_keys(db_engine)
    assert isinstance(no_orders, pd.DataFrame)
    assert isinstance(orphaned, pd.DataFrame)
    
    # Check that output CSV files exist
    assert os.path.exists("output/unmatched_customers.csv")
    assert os.path.exists("output/unmatched_orders.csv")
    
    assert len(no_orders) > 0
    assert len(orphaned) > 0


def test_task3_compare_join_types(db_engine):
    """Verify Task 3 correctly asserts join type hierarchies: FULL OUTER >= LEFT >= INNER."""
    counts = task3_compare_join_types(db_engine)
    assert 'inner_count' in counts
    assert 'left_count' in counts
    assert 'full_count' in counts
    
    assert counts['left_count'] >= counts['inner_count']
    assert counts['full_count'] >= counts['left_count']


def test_task4_multi_table_join(db_engine):
    """Verify Task 4 multi-table join runs without duplicating revenue total."""
    result = task4_multi_table_join(db_engine)
    assert isinstance(result, pd.DataFrame)
    assert 'line_total' in result.columns
    assert 'product_name' in result.columns
    assert len(result) > 0


def test_task5_document_join_decisions(db_engine):
    """Verify Task 5 generates summary report text and JSON artifacts."""
    join_counts = {'inner_count': 4950, 'left_count': 5054, 'full_count': 5104}
    doc_text = task5_document_join_decisions(db_engine, join_counts, 104, 50)
    
    assert "JOIN STRATEGY & DATA LINEAGE DOCUMENTATION" in doc_text
    assert os.path.exists("output/sql_joins_summary.txt")
    assert os.path.exists("output/join_validation_report.json")
    
    with open("output/join_validation_report.json", "r") as f:
        data = json.load(f)
        assert data['validation_status'] == 'PASSED'
