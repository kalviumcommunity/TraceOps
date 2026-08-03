import os
import pytest
import pandas as pd
import numpy as np
from scripts.detect_outliers import (
    detect_zscore_outliers,
    detect_iqr_outliers,
    cap_outliers,
    flag_outliers,
    save_cleaning_log,
)

@pytest.fixture
def sample_df():
    """Provides a sample DataFrame containing outliers for testing."""
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'revenue': [100.0, 150.0, 120.0, 200.0, 1000000.0, 110.0, 95.0, 80.0, 130.0, 140.0],
        'age': [25, 30, 35, 40, 150, 28, 22, 33, 45, -5]
    })

def test_detect_zscore_outliers(sample_df):
    """Ensure Z-score detects extreme outliers (> 3 std dev from mean)."""
    outliers, z_scores = detect_zscore_outliers(sample_df, 'revenue', threshold=2.5)
    
    # The value 1,000,000 should be detected with a high threshold
    assert outliers.sum() == 1
    assert outliers.iloc[4] == True

def test_detect_iqr_outliers(sample_df):
    """Ensure IQR method identifies outliers beyond 1.5 * IQR bounds."""
    outliers, lower_bound, upper_bound = detect_iqr_outliers(sample_df, 'revenue', factor=1.5)
    
    # 1,000,000 is way above upper bound
    assert outliers.sum() == 1
    assert outliers.iloc[4] == True
    assert upper_bound > 0
    assert lower_bound < upper_bound

def test_cap_outliers(sample_df):
    """Ensure capping replaces values outside bounds with boundary values."""
    _, lower_bound, upper_bound = detect_iqr_outliers(sample_df, 'revenue', factor=1.5)
    df_capped = cap_outliers(sample_df, 'revenue', lower_bound, upper_bound)
    
    assert 'revenue_capped' in df_capped.columns
    assert df_capped['revenue_capped'].iloc[4] == upper_bound
    assert df_capped['revenue_capped'].min() >= lower_bound
    assert df_capped['revenue_capped'].max() <= upper_bound

def test_flag_outliers(sample_df):
    """Ensure outliers from both methods are correctly flagged with 1, others 0."""
    outliers_iqr, _, _ = detect_iqr_outliers(sample_df, 'revenue')
    outliers_zscore, _ = detect_zscore_outliers(sample_df, 'revenue')
    
    df_flagged = flag_outliers(sample_df, outliers_iqr, outliers_zscore)
    
    assert 'is_outlier' in df_flagged.columns
    assert df_flagged['is_outlier'].iloc[4] == 1
    assert df_flagged['is_outlier'].iloc[0] == 0

def test_save_cleaning_log(tmp_path):
    """Ensure cleaning log can be written to disk correctly."""
    log_data = [{
        'column': 'revenue',
        'method': 'IQR',
        'action': 'cap',
        'threshold_lower': 10.0,
        'threshold_upper': 500.0,
        'affected_rows': 1,
        'date': '2026-07-22T12:00:00'
    }]
    
    log_file = tmp_path / "cleaning_log.csv"
    save_cleaning_log(log_data, filepath=str(log_file))
    
    assert os.path.exists(log_file)
    saved_df = pd.read_csv(log_file)
    assert len(saved_df) == 1
    assert saved_df['column'].iloc[0] == 'revenue'
    assert saved_df['action'].iloc[0] == 'cap'
