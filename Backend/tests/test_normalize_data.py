"""
Unit tests for NumPy Normalization & Vectorization Pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from scripts.normalize_data import run_normalization_pipeline


@pytest.fixture
def sample_revenue_df():
    """Provides a sample DataFrame with a revenue column for testing normalization."""
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'revenue': [100.0, 500.0, 250.0, 1000.0, 150.0],
        'age': [25, 34, 45, 19, 29]
    })


def test_min_max_normalization(sample_revenue_df):
    """Test Task 1: Min-Max normalization computes correct values with NumPy."""
    df_result = run_normalization_pipeline(sample_revenue_df)
    
    assert 'revenue_normalized' in df_result.columns
    # min is 100.0, max is 1000.0
    # Alice (100.0) -> (100 - 100) / 900 = 0.0
    # Dan (1000.0) -> (1000 - 100) / 900 = 1.0
    assert np.isclose(df_result.loc[df_result['customer_id'] == 1, 'revenue_normalized'].iloc[0], 0.0)
    assert np.isclose(df_result.loc[df_result['customer_id'] == 4, 'revenue_normalized'].iloc[0], 1.0)


def test_zscore_normalization(sample_revenue_df):
    """Test Task 2: Z-Score normalization matches mean and standard deviation formula."""
    df_result = run_normalization_pipeline(sample_revenue_df)
    
    assert 'revenue_zscore' in df_result.columns
    # Check that standard deviation is roughly 1 and mean is roughly 0 for z-scores
    z_vals = df_result['revenue_zscore'].values
    assert np.isclose(z_vals.mean(), 0.0)
    assert np.isclose(z_vals.std(ddof=0), 1.0) or np.isclose(z_vals.std(ddof=1), 1.0)


def test_rankings_verbatim(sample_revenue_df):
    """Test Task 3 & 5: Rankings argsort matches sorting indices."""
    df_result = run_normalization_pipeline(sample_revenue_df)
    
    assert 'revenue_rank' in df_result.columns
    # Verbatim Task 5 uses: df['revenue_rank'] = rankings = np.argsort(-revenue_array)
    # revenue: [100.0, 500.0, 250.0, 1000.0, 150.0]
    # -revenue: [-100.0, -500.0, -250.0, -1000.0, -150.0]
    # argsort(-revenue) -> [3, 1, 2, 4, 0] (indices of descending values: 1000 at idx 3, 500 at idx 1, 250 at idx 2, 150 at idx 4, 100 at idx 0)
    expected_rankings = [3, 1, 2, 4, 0]
    assert list(df_result['revenue_rank'].values) == expected_rankings


def test_dataframe_integration_dtypes(sample_revenue_df):
    """Test Task 5: Verify correct types and shapes of integration."""
    df_result = run_normalization_pipeline(sample_revenue_df)
    
    assert df_result.shape == (5, 6)
    assert pd.api.types.is_float_dtype(df_result['revenue_normalized'])
    assert pd.api.types.is_float_dtype(df_result['revenue_zscore'])
    assert pd.api.types.is_integer_dtype(df_result['revenue_rank'])
