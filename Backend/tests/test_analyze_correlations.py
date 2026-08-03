"""
Unit tests for Correlation & Relationship Analysis Pipeline.
"""

import os
import pytest
import pandas as pd
import numpy as np
from scripts.analyze_correlations import (
    generate_churn_data,
    load_data,
    compute_correlations,
    visualize_correlation_heatmap,
    identify_strong_correlations,
    analyze_business_causation,
    perform_feature_selection,
    analyze_correlations
)


@pytest.fixture
def sample_churn_df(tmp_path):
    """Fixture providing synthetic churn dataset for testing."""
    np.random.seed(42)
    n = 100
    customer_pain = np.random.normal(0, 1, n)
    usage = np.random.normal(10, 3, n)

    churn = (customer_pain > 0).astype(int)
    support_tickets = (5 + 3.5 * customer_pain + np.random.normal(0, 0.5, n)).astype(int)
    transactions_per_month = np.maximum(1, (usage).astype(int))
    engagement = 0.92 * transactions_per_month + np.random.normal(0, 0.5, n)

    df = pd.DataFrame({
        'customer_id': np.arange(1, n + 1),
        'engagement': engagement,
        'transactions_per_month': transactions_per_month,
        'support_tickets': support_tickets,
        'churn': churn
    })
    return df


def test_generate_and_load_data(tmp_path):
    csv_file = tmp_path / "test_churn_data.csv"
    generate_churn_data(str(csv_file), n_samples=50)
    assert os.path.exists(csv_file)

    df = load_data(str(csv_file))
    assert len(df) == 50
    assert 'churn' in df.columns
    assert 'support_tickets' in df.columns


def test_compute_correlations(sample_churn_df):
    pearson_corr, spearman_corr, comparison = compute_correlations(sample_churn_df)
    assert 'churn' in pearson_corr.columns
    assert 'churn' in spearman_corr.columns
    assert 'pearson' in comparison.columns
    assert 'spearman' in comparison.columns
    assert 'support_tickets' in comparison.index


def test_visualize_correlation_heatmap(sample_churn_df, tmp_path):
    pearson_corr, _, _ = compute_correlations(sample_churn_df)
    heatmap_file = tmp_path / "test_heatmap.png"
    visualize_correlation_heatmap(pearson_corr, str(heatmap_file))
    assert os.path.exists(heatmap_file)
    assert os.path.getsize(heatmap_file) > 0


def test_identify_strong_correlations(sample_churn_df):
    pearson_corr, _, _ = compute_correlations(sample_churn_df)
    strong_pairs = identify_strong_correlations(pearson_corr, threshold=0.5)
    assert not strong_pairs.empty
    assert (strong_pairs != 1.0).all()


def test_analyze_business_causation():
    analysis = analyze_business_causation(0.8)
    assert 'support_tickets <-> churn' in analysis
    key_info = analysis['support_tickets <-> churn']
    assert key_info['correlation'] == 0.8
    assert len(key_info['possible_directions']) == 3
    assert 'data_indicates' in key_info
    assert 'action' in key_info


def test_perform_feature_selection(sample_churn_df):
    df_features = perform_feature_selection(sample_churn_df)
    assert 'engagement' not in df_features.columns
    assert 'transactions_per_month' in df_features.columns
    assert 'support_tickets' in df_features.columns
    assert 'churn' in df_features.columns


def test_analyze_correlations_pipeline(sample_churn_df):
    pearson, spearman, strong_pairs, analysis, selected_features = analyze_correlations(sample_churn_df)
    assert isinstance(pearson, pd.DataFrame)
    assert isinstance(spearman, pd.DataFrame)
    assert isinstance(analysis, dict)
    assert 'engagement' not in selected_features.columns
