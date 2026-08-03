from __future__ import annotations

import os
import pytest
import numpy as np
import pandas as pd

from scripts.rolling_metrics import (
    generate_time_series_data,
    load_and_preprocess_data,
    handle_missing_gaps,
    resample_data,
    compute_rolling_averages,
    calculate_mom_change,
    compute_cumulative_sum,
    analyze_trends
)


@pytest.fixture
def temp_csv_path(tmp_path):
    """Fixture providing a temporary filepath for tests."""
    return os.path.join(tmp_path, "test_daily_revenue.csv")


@pytest.fixture
def sample_daily_df():
    """Fixture providing a simple 10-day clean daily DataFrame."""
    dates = pd.date_range(start='2025-01-01', periods=10, freq='D')
    # Simple linear revenue: 10k, 11k, ..., 19k
    revenue = [10000.0 + i * 1000 for i in range(10)]
    orders = [100 + i * 5 for i in range(10)]
    return pd.DataFrame({
        'date': dates,
        'revenue': revenue,
        'orders': orders
    })


def test_generate_time_series_data(temp_csv_path):
    """Verify that synthetic data generation creates the file and has correct structure."""
    df = generate_time_series_data(temp_csv_path, start_date='2025-01-01', periods=14)
    
    assert os.path.exists(temp_csv_path)
    assert len(df) == 14
    assert list(df.columns) == ['date', 'revenue', 'orders']
    assert pd.api.types.is_numeric_dtype(df['revenue'])
    assert pd.api.types.is_integer_dtype(df['orders'])
    
    # Tuesday index 1 is 2025-01-02? Wait, 2025-01-01 is Wednesday.
    # 2025-01-05 is Sunday (dayofweek = 6). Sunday should be peak.
    df['date'] = pd.to_datetime(df['date'])
    sunday_revenue = df.loc[df['date'].dt.dayofweek == 6, 'revenue'].iloc[0]
    friday_revenue = df.loc[df['date'].dt.dayofweek == 4, 'revenue'].iloc[0]
    assert sunday_revenue > friday_revenue


def test_load_and_preprocess_data(temp_csv_path):
    """Verify loading and parsing of date column."""
    generate_time_series_data(temp_csv_path, start_date='2025-01-01', periods=5)
    df = load_and_preprocess_data(temp_csv_path)
    
    assert pd.api.types.is_datetime64_any_dtype(df['date'])
    assert len(df) == 5


def test_handle_missing_gaps(sample_daily_df):
    """Verify reindexing and gap filling (forward-fill and linear interpolation)."""
    # Drop index 4 and 7 (creating gaps)
    df_gaps, df_filled = handle_missing_gaps(sample_daily_df, gap_fraction=0.2)
    
    # df_gaps should have dropped records (8 rows left instead of 10)
    assert len(df_gaps) < len(sample_daily_df)
    
    # df_filled should have 10 rows again (fully restored date range)
    assert len(df_filled) == len(sample_daily_df)
    assert df_filled['revenue'].isnull().sum() == 0
    assert df_filled['orders'].isnull().sum() == 0
    
    # Check linear interpolation value for index 4 (between 13000 and 15000 if 14000 was dropped)
    # The gap fill should accurately approximate dropped linear value
    restored_row = df_filled.loc[df_filled['date'] == '2025-01-05']
    assert abs(restored_row['revenue'].values[0] - 14000.0) < 1e-5


def test_resample_data(sample_daily_df):
    """Verify resampling aggregates correctly."""
    weekly, monthly = resample_data(sample_daily_df)
    
    # 10 days spans 2 weeks
    assert len(weekly) >= 2
    # 10 days in Jan 2025 is 1 month
    assert len(monthly) == 1
    
    # Sum of resampled weekly revenue should match total revenue
    assert abs(weekly['weekly_revenue'].sum() - sample_daily_df['revenue'].sum()) < 1e-5
    assert abs(monthly['monthly_revenue'].sum() - sample_daily_df['revenue'].sum()) < 1e-5


def test_compute_rolling_averages(sample_daily_df):
    """Verify rolling average calculation."""
    df_roll = compute_rolling_averages(sample_daily_df)
    
    assert 'revenue_ma7' in df_roll.columns
    assert 'revenue_ma30' in df_roll.columns
    
    # min_periods=1 means no NaNs
    assert df_roll['revenue_ma7'].isnull().sum() == 0
    assert df_roll['revenue_ma30'].isnull().sum() == 0
    
    # First row MA7 should equal first row revenue
    assert abs(df_roll['revenue_ma7'].iloc[0] - sample_daily_df['revenue'].iloc[0]) < 1e-5
    
    # Row 6 MA7 should be average of rows 0 to 6
    expected_ma7_row_6 = sample_daily_df['revenue'].iloc[0:7].mean()
    assert abs(df_roll['revenue_ma7'].iloc[6] - expected_ma7_row_6) < 1e-5


def test_calculate_mom_change():
    """Verify percentage change logic."""
    monthly_revenue = pd.Series([10000.0, 15000.0, 12000.0])
    monthly_metrics = pd.DataFrame({
        'monthly_revenue': monthly_revenue
    })
    
    mom_change = calculate_mom_change(monthly_metrics)
    
    assert len(mom_change) == 3
    assert pd.isna(mom_change.iloc[0])
    # 10000 -> 15000 is +50%
    assert abs(mom_change.iloc[1] - 50.0) < 1e-5
    # 15000 -> 12000 is -20%
    assert abs(mom_change.iloc[2] - (-20.0)) < 1e-5


def test_compute_cumulative_sum(sample_daily_df):
    """Verify cumulative sum increases monotonically."""
    df_cum = compute_cumulative_sum(sample_daily_df)
    
    assert 'cumulative_revenue' in df_cum.columns
    assert df_cum['cumulative_revenue'].iloc[0] == sample_daily_df['revenue'].iloc[0]
    assert df_cum['cumulative_revenue'].iloc[-1] == sample_daily_df['revenue'].sum()
    assert df_cum['cumulative_revenue'].is_monotonic_increasing


def test_analyze_trends(sample_daily_df):
    """Verify trend direction and report content."""
    df_roll = compute_rolling_averages(sample_daily_df)
    
    # Create fake MoM change
    mom_change = pd.Series([np.nan, 10.0], index=pd.to_datetime(['2025-01-31', '2025-02-28']))
    
    # Trend report string
    report = analyze_trends(df_roll, mom_change)
    
    assert "TIME-SERIES TREND ANALYSIS REPORT" in report
    assert "ROLLING AVERAGE TREND" in report
    assert "PERIOD-OVER-PERIOD MONTHLY PERFORMANCE" in report
    assert "BUSINESS IMPLICATIONS" in report
