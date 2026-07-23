"""
Unit tests for Customer Feature Engineering Pipeline.
"""

import pytest
import pandas as pd
import numpy as np

from scripts.customer_feature_engineering import (
    engineer_features,
)


@pytest.fixture
def sample_customer_df():
    """Provides a sample customer DataFrame for feature engineering tests."""
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Carol', 'Dan', 'Eve'],
        'email': ['a@x.com', 'b@x.com', 'c@x.com', 'd@x.com', 'e@x.com'],
        'signup_date': pd.to_datetime(['2025-01-01', '2025-01-05', '2025-01-10', '2025-01-15', '2025-01-20']),
        'purchase_count': [1, 10, 5, 20, 2],
        'total_transactions': [1, 10, 5, 20, 2],
        'total_spent': [50.0, 500.0, 250.0, 1000.0, 100.0],
        'days_as_customer': [35, 31, 26, 21, 16],
        'days_since_last_purchase': [10, 1, 5, 2, 8]
    })


def test_ratio_features(sample_customer_df):
    """Test Task 1: Ratio calculations are correct."""
    df_feat = engineer_features(sample_customer_df)
    
    # Assert columns exist
    assert 'transactions_per_month' in df_feat.columns
    assert 'avg_spend_per_transaction' in df_feat.columns
    assert 'lifetime_value_per_month' in df_feat.columns

    # Alice (customer_id 1):
    # transactions_per_month = 1 / (35 / 30) = 0.85714
    # avg_spend_per_transaction = 50 / 1 = 50.0
    # lifetime_value_per_month = 50 / (35 / 30) = 42.85714
    assert np.isclose(df_feat.loc[df_feat['customer_id'] == 1, 'transactions_per_month'].iloc[0], 1.0 / (35.0 / 30.0))
    assert np.isclose(df_feat.loc[df_feat['customer_id'] == 1, 'avg_spend_per_transaction'].iloc[0], 50.0)
    assert np.isclose(df_feat.loc[df_feat['customer_id'] == 1, 'lifetime_value_per_month'].iloc[0], 50.0 / (35.0 / 30.0))


def test_equal_width_binning(sample_customer_df):
    """Test Task 2: Equal width binning logic for engagement tier."""
    df_feat = engineer_features(sample_customer_df)
    
    assert 'engagement_tier' in df_feat.columns
    # Check that tier is categorized into low, medium, or high
    # Alice: transactions_per_month = 0.857 (<= 2) -> 'low'
    # Bob: transactions_per_month = 10 / (31/30) = 9.67 (<= 10) -> 'medium'
    # Dan: transactions_per_month = 20 / (21/30) = 28.57 (> 10) -> 'high'
    assert df_feat.loc[df_feat['customer_id'] == 1, 'engagement_tier'].iloc[0] == 'low'
    assert df_feat.loc[df_feat['customer_id'] == 2, 'engagement_tier'].iloc[0] == 'medium'
    assert df_feat.loc[df_feat['customer_id'] == 4, 'engagement_tier'].iloc[0] == 'high'


def test_quantile_binning(sample_customer_df):
    """Test Task 3: Quantile-based binning for total spent."""
    df_feat = engineer_features(sample_customer_df)
    
    assert 'spend_quartile' in df_feat.columns
    # Check category codes and labels are assigned correctly
    assert set(df_feat['spend_quartile'].unique()) == {'Q1', 'Q2', 'Q3', 'Q4'}


def test_composite_score(sample_customer_df):
    """Test Task 4: RFM composite scores are computed and ranges are valid."""
    df_feat = engineer_features(sample_customer_df)
    
    assert 'recency_score' in df_feat.columns
    assert 'frequency_score' in df_feat.columns
    assert 'monetary_score' in df_feat.columns
    assert 'rfm_score' in df_feat.columns

    # Verify RFM components can be cast to int and range is correct
    assert (df_feat['rfm_score'] >= 3).all()
    assert (df_feat['rfm_score'] <= 15).all()


def test_feature_validation_no_nans(sample_customer_df):
    """Test Task 5: No NaNs are introduced in finalized feature columns."""
    df_feat = engineer_features(sample_customer_df)
    
    assert df_feat['engagement_tier'].isna().sum() == 0
    assert df_feat['spend_quartile'].isna().sum() == 0
    assert df_feat['rfm_score'].isna().sum() == 0
