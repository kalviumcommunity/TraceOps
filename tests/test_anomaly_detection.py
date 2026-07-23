from __future__ import annotations

import os
import pytest
import numpy as np
import pandas as pd

from scripts.anomaly_detection import (
    generate_anomaly_data,
    load_data,
    check_thresholds,
    detect_anomalies_zscore,
    classify_severity,
    log_anomalies,
    visualize_anomalies,
    ALERT_RULES
)


@pytest.fixture
def temp_csv_path(tmp_path):
    """Fixture providing temporary CSV path."""
    return os.path.join(tmp_path, "test_anomaly_data.csv")


@pytest.fixture
def sample_metrics_df():
    """Fixture providing clean daily metric series with clear anomalies."""
    dates = pd.date_range(start="2026-07-01", periods=10, freq="D")
    # Mean = 1000, Std = 10
    values = [1000.0, 995.0, 1005.0, 1002.0, 998.0, 1000.0, 999.0, 1001.0, 2000.0, 1000.0]
    return pd.DataFrame({
        'date': dates,
        'daily_revenue': values,
        'transaction_count': [500] * 10,
        'signup_rate': [150] * 10
    })


def test_generate_anomaly_data(temp_csv_path):
    """Verify synthetic anomaly data generation."""
    df = generate_anomaly_data(temp_csv_path, n_days=30)
    assert os.path.exists(temp_csv_path)
    assert len(df) == 30
    assert list(df.columns) == ['date', 'daily_revenue', 'transaction_count', 'signup_rate']


def test_check_thresholds():
    """Verify threshold alert checking logic."""
    metrics_normal = {'daily_revenue': 20000, 'transaction_count': 500, 'signup_rate': 100}
    alerts_normal = check_thresholds(metrics_normal, ALERT_RULES)
    assert len(alerts_normal) == 0
    
    metrics_anomaly = {'daily_revenue': 2500, 'transaction_count': 50, 'signup_rate': 600}
    alerts_anomaly = check_thresholds(metrics_anomaly, ALERT_RULES)
    
    assert len(alerts_anomaly) == 3
    directions = [a['direction'] for a in alerts_anomaly]
    assert 'BELOW_MIN' in directions
    assert 'ABOVE_MAX' in directions


def test_detect_anomalies_zscore(sample_metrics_df):
    """Verify statistical Z-score detection."""
    series = sample_metrics_df.set_index('date')['daily_revenue']
    anomalies, z_scores = detect_anomalies_zscore(series, threshold=2.0)
    
    # Value 2000.0 on Day 9 is far above mean ~1100, should be detected
    assert len(anomalies) == 1
    assert float(anomalies.iloc[0]) == 2000.0
    assert float(z_scores.max()) > 2.0


def test_classify_severity():
    """Verify severity classification function."""
    mean = 100.0
    std = 10.0
    
    assert classify_severity(105.0, mean, std) == 'LOW'      # z = 0.5
    assert classify_severity(118.0, mean, std) == 'MEDIUM'   # z = 1.8
    assert classify_severity(125.0, mean, std) == 'HIGH'     # z = 2.5
    assert classify_severity(135.0, mean, std) == 'CRITICAL' # z = 3.5


def test_log_anomalies(sample_metrics_df, tmp_path):
    """Verify audit log persistence."""
    log_csv = os.path.join(tmp_path, "test_log.csv")
    df_log = log_anomalies(sample_metrics_df, metric_col='daily_revenue', output_csv=log_csv)
    
    assert os.path.exists(log_csv)
    assert len(df_log) == 1
    assert df_log.iloc[0]['metric'] == 'daily_revenue'
    assert df_log.iloc[0]['status'] == 'OPEN'


def test_visualize_anomalies(sample_metrics_df, tmp_path):
    """Verify plot generation."""
    plot_path = os.path.join(tmp_path, "test_plot.png")
    visualize_anomalies(sample_metrics_df, metric_col='daily_revenue', output_path=plot_path)
    assert os.path.exists(plot_path)
