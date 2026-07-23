"""
Unit tests for Revenue Distribution Analysis Pipeline.
"""

import os
import pytest
import pandas as pd
import numpy as np
from scipy import stats

from scripts.analyze_distributions import (
    generate_skewed_data,
    analyze_distributions,
)


@pytest.fixture(scope="module")
def setup_skewed_data(tmp_path_factory):
    """Generates synthetic skewed revenue data inside a temporary directory."""
    temp_dir = tmp_path_factory.mktemp("raw_data")
    file_path = temp_dir / "skewed_revenue_data.csv"
    generate_skewed_data(str(file_path))
    return str(file_path)


def test_generated_skewed_data_statistics(setup_skewed_data):
    """Verify that the generated dataset meets target mean ~450 and skewness ~2.5 requirements."""
    df = pd.read_csv(setup_skewed_data)
    
    assert len(df) == 1000
    assert 'revenue' in df.columns
    
    # Calculate statistics
    mean_val = df['revenue'].mean()
    skew_val = stats.skew(df['revenue'])
    
    # Assert they are reasonably close to the target (mean ~450, skewness ~2.5)
    assert np.isclose(mean_val, 450.0, rtol=0.05)
    assert np.isclose(skew_val, 2.5, rtol=0.05)


def test_analyze_distributions_computes_correct_metrics(setup_skewed_data, tmp_path):
    """Verify that analyze_distributions computes and returns the correct skewness, kurtosis, and percentiles."""
    df = pd.read_csv(setup_skewed_data)
    
    # Run analysis
    skewness, kurtosis, percentiles = analyze_distributions(df)
    
    # Validate return types and values
    assert isinstance(skewness, float)
    assert isinstance(kurtosis, float)
    assert isinstance(percentiles, pd.Series)
    
    assert np.isclose(skewness, 2.47, rtol=0.02)
    assert np.isclose(kurtosis, 13.15, rtol=0.02)
    assert len(percentiles) == 6
    assert set(percentiles.index) == {0.25, 0.50, 0.75, 0.90, 0.95, 0.99}


def test_output_plots_generated(setup_skewed_data, monkeypatch, tmp_path):
    """Verify that output plots are created in the designated folder."""
    df = pd.read_csv(setup_skewed_data)
    
    # Redirect output dir to tmp_path to prevent overwriting prod artifacts
    monkeypatch.setattr("scripts.analyze_distributions.OUTPUT_DIR", str(tmp_path))
    
    # Run analysis
    analyze_distributions(df)
    
    # Verify plots exist
    assert os.path.exists(tmp_path / 'revenue_distribution.png')
    assert os.path.exists(tmp_path / 'segment_comparison.png')
