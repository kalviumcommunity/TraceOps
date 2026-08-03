"""
Unit tests for Date & Time Feature Engineering Pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from scripts.datetime_feature_engineering import (
    parse_timestamps,
    extract_day_and_hour,
    compute_week_and_resample,
    compute_recency_metrics,
    build_time_indexed_aggregations,
)


@pytest.fixture
def sample_df():
    """Fixture providing sample transaction DataFrame with string timestamps."""
    return pd.DataFrame({
        'transaction_id': ['TX01', 'TX02', 'TX03', 'TX04', 'TX05'],
        'customer_id': ['CUST1', 'CUST2', 'CUST1', 'CUST3', 'CUST2'],
        'transaction_date': [
            '2025-01-15 14:30:45',
            '2025-01-16 09:15:00',
            '2025-01-22 18:45:30',
            '2025-01-29 11:00:00',
            '2025-02-05 20:10:15'
        ],
        'amount': [100.0, 250.0, 150.0, 300.0, 75.0]
    })


def test_parse_timestamps_explicit_format(sample_df):
    """Task 1 Test: Ensure timestamp string is parsed to datetime64 with explicit format."""
    df_parsed = parse_timestamps(sample_df, date_col='transaction_date', date_format='%Y-%m-%d %H:%M:%S')
    
    assert pd.api.types.is_datetime64_any_dtype(df_parsed['transaction_date'])
    assert df_parsed['transaction_date'].iloc[0] == pd.Timestamp('2025-01-15 14:30:45')


def test_parse_timestamps_invalid_format_raises(sample_df):
    """Task 1 Test: Ensure mismatch in format string raises ValueError."""
    with pytest.raises(ValueError):
        parse_timestamps(sample_df, date_col='transaction_date', date_format='%d/%m/%Y %H:%M:%S')


def test_extract_day_and_hour(sample_df):
    """Task 2 Test: Ensure day_of_week and hour columns are correctly extracted."""
    df_parsed = parse_timestamps(sample_df, date_col='transaction_date')
    df_features = extract_day_and_hour(df_parsed, date_col='transaction_date')
    
    assert 'day_of_week' in df_features.columns
    assert 'dow_numeric' in df_features.columns
    assert 'hour' in df_features.columns
    
    # 2025-01-15 was Wednesday, hour 14
    assert df_features['day_of_week'].iloc[0] == 'Wednesday'
    assert df_features['hour'].iloc[0] == 14
    assert df_features['dow_numeric'].iloc[0] == 2  # 0=Mon, 1=Tue, 2=Wed


def test_compute_week_and_resample(sample_df):
    """Task 3 Test: Ensure ISO week number extraction and weekly resampling."""
    df_parsed = parse_timestamps(sample_df, date_col='transaction_date')
    df_features, weekly_metrics = compute_week_and_resample(df_parsed, date_col='transaction_date', value_col='amount')
    
    assert 'week_num' in df_features.columns
    assert df_features['week_num'].iloc[0] == 3  # 2025-01-15 is in ISO week 3
    
    # Check weekly resample output structure
    assert 'total_revenue' in weekly_metrics.columns
    assert 'transaction_count' in weekly_metrics.columns
    assert 'avg_transaction_value' in weekly_metrics.columns
    assert weekly_metrics['total_revenue'].sum() == sample_df['amount'].sum()


def test_compute_recency_metrics(sample_df):
    """Task 4 Test: Ensure days-since-event metric uses datetime arithmetic."""
    df_parsed = parse_timestamps(sample_df, date_col='transaction_date')
    ref_date = pd.Timestamp('2025-02-10 00:00:00')
    df_features, customer_recency = compute_recency_metrics(
        df_parsed, customer_col='customer_id', date_col='transaction_date', reference_date=ref_date
    )
    
    assert 'days_since_last_purchase' in df_features.columns
    # CUST1 last purchase was 2025-01-22 18:45:30. Ref date 2025-02-10 00:00:00 -> 18 days difference
    cust1_recency = customer_recency.loc['CUST1', 'days_since_last_purchase']
    assert isinstance(cust1_recency, (int, np.integer))
    assert cust1_recency == 18


def test_build_time_indexed_aggregations(sample_df):
    """Task 5 Test: Ensure multi-dimensional aggregations and pivot table work."""
    df_parsed = parse_timestamps(sample_df, date_col='transaction_date')
    df_features = extract_day_and_hour(df_parsed, date_col='transaction_date')
    hourly_daily, pivot_table = build_time_indexed_aggregations(df_features, date_col='transaction_date', value_col='amount')
    
    assert isinstance(pivot_table, pd.DataFrame)
    assert pivot_table.index.name == 'hour'
    assert 'Wednesday' in pivot_table.columns
    assert pivot_table.loc[14, 'Wednesday'] == 100.0
