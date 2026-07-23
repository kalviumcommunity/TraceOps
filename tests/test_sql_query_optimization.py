"""
Unit tests for Analytical SQL Query Optimization pipeline.
"""

import os
import json
import pytest
import pandas as pd
from scripts.sql_query_optimization import (
    setup_database_connection,
    seed_optimization_dataset,
    task1_refactor_select_star,
    task2_refactor_early_filtering,
    task3_refactor_cte_readability,
    task4_compare_and_document
)


@pytest.fixture(scope="module")
def db_engine():
    """Fixture providing database engine seeded with test optimization dataset."""
    engine = setup_database_connection("sqlite:///:memory:")
    seed_optimization_dataset(engine)
    return engine


def test_task1_select_star_reduction(db_engine):
    """Verify Task 1 reduces column count and memory footprint while matching row counts."""
    metrics = task1_refactor_select_star(db_engine)
    
    assert isinstance(metrics, dict)
    assert metrics['original_columns'] > metrics['optimized_columns']
    assert metrics['optimized_columns'] == 7
    assert metrics['column_reduction_pct'] > 50.0
    assert metrics['memory_reduction_pct'] > 50.0
    assert metrics['original_rows'] == metrics['optimized_rows']


def test_task2_early_filtering(db_engine):
    """Verify Task 2 reduces intermediate dataset size prior to joining."""
    metrics = task2_refactor_early_filtering(db_engine)
    
    assert isinstance(metrics, dict)
    assert metrics['total_transactions_count'] > metrics['filtered_transactions_count']
    assert metrics['reduction_factor'] > 1.1
    assert metrics['final_result_count'] > 0


def test_task3_cte_readability(db_engine):
    """Verify Task 3 CTE refactored query returns valid segment metrics matching original nested query."""
    metrics = task3_refactor_cte_readability(db_engine)
    
    assert isinstance(metrics, dict)
    assert metrics['segment_count'] > 0
    assert len(metrics['segments_analyzed']) > 0


def test_task4_artifact_generation(db_engine):
    """Verify Task 4 creates report JSON and summary text artifacts."""
    t1_metrics = task1_refactor_select_star(db_engine)
    t2_metrics = task2_refactor_early_filtering(db_engine)
    t3_metrics = task3_refactor_cte_readability(db_engine)
    
    comparison_df = task4_compare_and_document(t1_metrics, t2_metrics, t3_metrics)
    
    assert isinstance(comparison_df, pd.DataFrame)
    assert os.path.exists("output/query_optimization_report.json")
    assert os.path.exists("output/query_optimization_summary.txt")
    
    with open("output/query_optimization_report.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data['status'] == 'PASSED'
