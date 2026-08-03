from __future__ import annotations

import os
import pytest
import numpy as np
import pandas as pd

from scripts.root_cause_investigation import (
    generate_investigation_data,
    load_data,
    isolate_time_window,
    analyze_segments,
    analyze_correlations,
    generate_investigation_report,
    visualize_investigation
)


@pytest.fixture
def temp_csv_path(tmp_path):
    """Fixture providing a temporary CSV path."""
    return os.path.join(tmp_path, "test_telemetry.csv")


@pytest.fixture
def sample_telemetry_df():
    """Fixture providing a controlled telemetry dataset with an injected hour 14 credit_card outage."""
    records = []
    base_date = pd.Timestamp("2026-07-18 00:00:00")
    
    for hour in range(24):
        h_dt = base_date + pd.Timedelta(hours=hour)
        for _ in range(20):
            # Credit card
            status = 'failed' if (hour == 14) else 'success'
            err = 'Stripe API Connection Timeout' if (hour == 14) else 'None'
            records.append({
                'transaction_id': f"TX_{hour}_CC",
                'timestamp': h_dt,
                'customer_id': 'C1',
                'customer_type': 'Enterprise',
                'payment_method': 'credit_card',
                'region': 'US-East',
                'device_type': 'Desktop',
                'amount': 100.0,
                'status': status,
                'error_message': err,
                'success_rate': 0 if status == 'failed' else 1
            })
            
            # Debit card (always success)
            records.append({
                'transaction_id': f"TX_{hour}_DB",
                'timestamp': h_dt,
                'customer_id': 'C2',
                'customer_type': 'SMB',
                'payment_method': 'debit',
                'region': 'US-West',
                'device_type': 'Mobile',
                'amount': 50.0,
                'status': 'success',
                'error_message': 'None',
                'success_rate': 1
            })
            
    df = pd.DataFrame(records)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def test_generate_investigation_data(temp_csv_path):
    """Verify synthetic dataset generation."""
    df = generate_investigation_data(temp_csv_path, n_days=2)
    assert os.path.exists(temp_csv_path)
    assert len(df) > 0
    assert list(df.columns) == ['transaction_id', 'timestamp', 'customer_id', 'customer_type', 'payment_method', 'region', 'device_type', 'amount', 'status', 'error_message']


def test_isolate_time_window(sample_telemetry_df):
    """Verify isolation of anomaly date and hour."""
    problem_day, problem_hour, hourly_df = isolate_time_window(sample_telemetry_df)
    
    assert problem_day == pd.Timestamp("2026-07-18").date()
    assert problem_hour == 14
    assert len(hourly_df) == 24


def test_analyze_segments(sample_telemetry_df):
    """Verify segment breakdown isolates credit card failures."""
    problem_day = pd.Timestamp("2026-07-18").date()
    problem_hour = 14
    
    affected_segment, by_payment = analyze_segments(sample_telemetry_df, problem_day, problem_hour)
    
    assert affected_segment == 'credit_card'
    assert by_payment.loc['credit_card', 'mean'] == 0.0
    assert by_payment.loc['debit', 'mean'] == 1.0


def test_analyze_correlations(sample_telemetry_df):
    """Verify error message correlation identifies Stripe timeout."""
    problem_day = pd.Timestamp("2026-07-18").date()
    problem_hour = 14
    
    top_error, error_pct = analyze_correlations(sample_telemetry_df, problem_day, problem_hour)
    
    assert top_error == 'Stripe API Connection Timeout'
    assert abs(error_pct - 1.0) < 1e-5


def test_generate_investigation_report(sample_telemetry_df, tmp_path):
    """Verify investigation report formatting and output creation."""
    problem_day = pd.Timestamp("2026-07-18").date()
    problem_hour = 14
    report_path = os.path.join(tmp_path, "test_report.txt")
    
    report = generate_investigation_report(
        sample_telemetry_df,
        problem_day,
        problem_hour,
        'credit_card',
        'Stripe API Connection Timeout',
        1.0,
        output_path=report_path
    )
    
    assert os.path.exists(report_path)
    assert "ROOT CAUSE INVESTIGATION REPORT" in report
    assert "OBSERVATION" in report
    assert "credit_card" in report
    assert "Stripe API Connection Timeout" in report
    assert "ROOT CAUSE CONFIRMED" in report


def test_visualize_investigation(sample_telemetry_df, tmp_path):
    """Verify plot generation."""
    problem_day = pd.Timestamp("2026-07-18").date()
    problem_hour = 14
    plot_path = os.path.join(tmp_path, "test_plot.png")
    
    visualize_investigation(sample_telemetry_df, problem_day, problem_hour, output_path=plot_path)
    assert os.path.exists(plot_path)
