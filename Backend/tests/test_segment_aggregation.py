"""
Unit tests for GroupBy Aggregation & Segment Insights Pipeline.
"""

import os
import pytest
import pandas as pd
import numpy as np
from scripts.segment_aggregation import (
    generate_segment_data,
    load_data,
    single_level_groupby,
    multi_level_groupby,
    create_pivot_table,
    rank_and_identify_performers,
    surface_actionable_insights,
    run_segment_analysis
)


@pytest.fixture
def sample_segment_df():
    """Fixture providing a deterministic sample DataFrame for segment testing."""
    data = {
        'customer_id': list(range(1, 11)),
        'customer_type': ['Enterprise', 'Enterprise', 'SMB', 'SMB', 'SMB', 'SMB', 'Startup', 'Startup', 'Startup', 'Startup'],
        'product': ['Enterprise Suite', 'Analytics Pro', 'Basic Tier', 'Cloud API', 'Basic Tier', 'Cloud API', 'Cloud API', 'Basic Tier', 'Analytics Pro', 'Cloud API'],
        'churn': [0, 0, 1, 1, 0, 0, 1, 0, 0, 0],  # Enterprise: 0%, SMB: 50%, Startup: 25%
        'revenue': [10000.0, 10000.0, 500.0, 500.0, 500.0, 500.0, 200.0, 200.0, 200.0, 200.0],
        'support_tickets': [1, 1, 5, 4, 5, 4, 3, 2, 3, 2]
    }
    return pd.DataFrame(data)


def test_generate_and_load_data(tmp_path):
    csv_file = tmp_path / "test_segment_data.csv"
    generate_segment_data(str(csv_file), n_samples=60)
    assert os.path.exists(csv_file)

    df = load_data(str(csv_file))
    assert len(df) == 60
    assert 'customer_type' in df.columns
    assert 'product' in df.columns
    assert 'churn' in df.columns
    assert 'revenue' in df.columns
    assert 'support_tickets' in df.columns


def test_single_level_groupby(sample_segment_df):
    metrics = single_level_groupby(sample_segment_df)
    expected_cols = ['churn_rate', 'total_revenue', 'customer_count', 'avg_support_tickets']
    assert list(metrics.columns) == expected_cols
    assert len(metrics) == 3
    assert 'Enterprise' in metrics.index
    assert 'SMB' in metrics.index
    assert 'Startup' in metrics.index


def test_multi_level_groupby(sample_segment_df):
    product_segment, product_segment_pivot = multi_level_groupby(sample_segment_df)
    assert 'total_revenue' in product_segment.columns
    assert 'customer_count' in product_segment.columns
    assert isinstance(product_segment_pivot, pd.DataFrame)


def test_create_pivot_table(sample_segment_df):
    pivot = create_pivot_table(sample_segment_df)
    assert isinstance(pivot, pd.DataFrame)
    assert 'Enterprise' in pivot.index
    assert pivot.loc['Enterprise', 'Enterprise Suite'] == 10000.0


def test_rank_and_identify_performers(sample_segment_df):
    metrics = single_level_groupby(sample_segment_df)
    ranked_metrics, worst_first = rank_and_identify_performers(metrics)
    
    assert 'churn_rank' in ranked_metrics.columns
    assert 'revenue_contribution' in ranked_metrics.columns
    assert worst_first.index[0] == 'SMB'  # SMB has highest churn rate (50%)
    
    # Revenue contribution sum should be 100%
    assert pytest.approx(ranked_metrics['revenue_contribution'].sum(), 0.01) == 100.0


def test_surface_actionable_insights(sample_segment_df, tmp_path):
    metrics = single_level_groupby(sample_segment_df)
    ranked_metrics, _ = rank_and_identify_performers(metrics)
    
    out_csv = tmp_path / "test_insights.csv"
    insights_df = surface_actionable_insights(ranked_metrics, output_path=str(out_csv))
    
    assert os.path.exists(out_csv)
    assert 'segment' in insights_df.columns
    assert 'churn_rate' in insights_df.columns
    assert 'revenue_contribution' in insights_df.columns
    assert 'action' in insights_df.columns
    
    # Check actions based on churn rates
    smb_row = insights_df[insights_df['segment'] == 'SMB'].iloc[0]
    assert 'HIGH PRIORITY' in smb_row['action']
    
    ent_row = insights_df[insights_df['segment'] == 'Enterprise'].iloc[0]
    assert 'Healthy' in ent_row['action']


def test_run_segment_analysis(tmp_path):
    csv_file = tmp_path / "test_data.csv"
    generate_segment_data(str(csv_file), n_samples=50)
    results = run_segment_analysis(str(csv_file))
    
    assert 'segment_metrics' in results
    assert 'insights_df' in results
    assert 'summary' in results
