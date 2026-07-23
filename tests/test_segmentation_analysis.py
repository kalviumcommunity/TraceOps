from __future__ import annotations

import os
import pytest
import pandas as pd
import numpy as np

from scripts.segmentation_analysis import (
    generate_behavior_data,
    load_data,
    compute_segment_metrics,
    create_summary_statistics_table,
    generate_report
)


@pytest.fixture
def temp_csv_path(tmp_path):
    """Fixture providing a temporary CSV file path."""
    return os.path.join(tmp_path, "test_customer_behavior.csv")


@pytest.fixture
def sample_behavior_df():
    """Fixture providing a clean sample behavioral DataFrame."""
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'customer_type': ['Enterprise', 'SMB', 'Startup', 'SMB', 'Startup'],
        'lifetime_value': [150000.0, 8000.0, 2000.0, 9000.0, 1800.0],
        'churn': [0, 1, 0, 0, 1],
        'support_tickets': [1, 5, 2, 4, 3],
        'retention_days': [650, 180, 240, 200, 220]
    })


def test_generate_behavior_data(temp_csv_path):
    """Verify that data generation works and creates expected schema and partitions."""
    df = generate_behavior_data(temp_csv_path, n_samples=100)
    
    assert os.path.exists(temp_csv_path)
    assert len(df) == 100
    assert list(df.columns) == ['customer_id', 'customer_type', 'lifetime_value', 'churn', 'support_tickets', 'retention_days']
    
    # Check that segments exist
    unique_types = df['customer_type'].unique()
    assert 'Enterprise' in unique_types
    assert 'SMB' in unique_types
    assert 'Startup' in unique_types


def test_load_data(temp_csv_path):
    """Verify that load_data loads a generated file correctly."""
    generate_behavior_data(temp_csv_path, n_samples=20)
    df = load_data(temp_csv_path)
    
    assert len(df) == 20
    assert 'customer_type' in df.columns


def test_compute_segment_metrics(sample_behavior_df):
    """Verify that segment metrics are correctly aggregated."""
    metrics = compute_segment_metrics(sample_behavior_df)
    
    # Check shape: 3 segments
    assert len(metrics) == 3
    assert list(metrics.columns) == ['avg_ltv', 'churn_rate', 'avg_tickets', 'avg_retention', 'count']
    
    # Enterprise count is 1, avg LTV is 150000, churn rate is 0%
    assert metrics.loc['Enterprise', 'count'] == 1
    assert metrics.loc['Enterprise', 'avg_ltv'] == 150000.0
    assert metrics.loc['Enterprise', 'churn_rate'] == 0.0
    
    # SMB count is 2, avg LTV is 8500 (mean of 8000 and 9000), churn rate is 50% (mean of 1 and 0)
    assert metrics.loc['SMB', 'count'] == 2
    assert metrics.loc['SMB', 'avg_ltv'] == 8500.0
    assert metrics.loc['SMB', 'churn_rate'] == 0.5


def test_create_summary_statistics_table(sample_behavior_df):
    """Verify rankings are calculated correctly."""
    metrics = compute_segment_metrics(sample_behavior_df)
    summary = create_summary_statistics_table(metrics)
    
    assert 'ltv_rank' in summary.columns
    assert 'churn_rank' in summary.columns
    
    # Enterprise has highest LTV (150k) -> rank 1
    assert summary.loc['Enterprise', 'ltv_rank'] == 1
    
    # Enterprise has churn 0%, Startup has 50% (1/2), SMB has 50% (1/2)
    # Lower churn gets better rank (ascending)
    assert summary.loc['Enterprise', 'churn_rank'] == 1


def test_generate_report(sample_behavior_df, temp_csv_path):
    """Verify strategy report contents."""
    metrics = compute_segment_metrics(sample_behavior_df)
    report_path = temp_csv_path.replace(".csv", ".txt")
    report = generate_report(metrics, report_path)
    
    assert os.path.exists(report_path)
    assert "CUSTOMER BEHAVIORAL ANALYSIS & USER SEGMENTATION" in report
    assert "PERFORMANCE LEADERBOARD" in report
    assert "STRATEGIC SEGMENT PLAYBOOKS" in report
    assert "ENTERPRISE" in report
    assert "SMB" in report
    assert "STARTUP" in report
