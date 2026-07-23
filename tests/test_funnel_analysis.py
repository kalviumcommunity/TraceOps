from __future__ import annotations

import os
import pytest
import pandas as pd
import numpy as np

from scripts.funnel_analysis import (
    generate_funnel_data,
    load_data,
    compute_funnel_stages,
    compute_drop_offs,
    calculate_business_impact,
    generate_recommendation_report
)


@pytest.fixture
def temp_csv_path(tmp_path):
    """Fixture providing a temporary CSV path."""
    return os.path.join(tmp_path, "test_funnel_data.csv")


@pytest.fixture
def sample_funnel_df():
    """Fixture providing a clean sequential funnel DataFrame of 10 users."""
    # Sequential progress counts: 10 signup -> 8 email -> 6 password -> 5 verified -> 4 payment -> 2 purchase
    stage1 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    stage2 = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    stage3 = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    stage4 = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    stage5 = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    stage6 = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    
    return pd.DataFrame({
        'user_id': np.arange(1, 11),
        'signup_completed': stage1,
        'email_entered': stage2,
        'password_created': stage3,
        'email_verified': stage4,
        'payment_added': stage5,
        'first_purchase': stage6
    })


def test_generate_funnel_data(temp_csv_path):
    """Verify data generation produces exact target volumes."""
    df = generate_funnel_data(temp_csv_path, total_users=100)
    
    assert os.path.exists(temp_csv_path)
    assert len(df) == 100
    assert list(df.columns) == ['user_id', 'signup_completed', 'email_entered', 'password_created', 'email_verified', 'payment_added', 'first_purchase']
    
    # Verify sequence constraints (purchases <= payments <= verified <= passwords <= emails <= signups)
    assert df['first_purchase'].sum() <= df['payment_added'].sum()
    assert df['payment_added'].sum() <= df['email_verified'].sum()
    assert df['email_verified'].sum() <= df['password_created'].sum()
    assert df['password_created'].sum() <= df['email_entered'].sum()
    assert df['email_entered'].sum() <= df['signup_completed'].sum()


def test_load_data(temp_csv_path):
    """Verify loading functions."""
    generate_funnel_data(temp_csv_path, total_users=50)
    df = load_data(temp_csv_path)
    
    assert len(df) == 50
    assert 'first_purchase' in df.columns


def test_compute_funnel_stages(sample_funnel_df):
    """Verify that stage count dictionary has correct keys and sequential volumes."""
    stages = compute_funnel_stages(sample_funnel_df)
    
    assert list(stages.keys()) == ['Sign Up', 'Email Entered', 'Password Created', 'Email Verified', 'Payment Added', 'First Purchase']
    assert stages['Sign Up'] == 10
    assert stages['Email Entered'] == 8
    assert stages['Password Created'] == 6
    assert stages['Email Verified'] == 5
    assert stages['Payment Added'] == 4
    assert stages['First Purchase'] == 2


def test_compute_drop_offs(sample_funnel_df):
    """Verify drop-off and completion percentage math."""
    stages = compute_funnel_stages(sample_funnel_df)
    funnel_df = compute_drop_offs(stages)
    
    assert len(funnel_df) == 5
    
    # Sign Up (10) -> Email Entered (8)
    first_row = funnel_df.iloc[0]
    assert first_row['users_lost'] == 2
    assert abs(first_row['completion_rate'] - 80.0) < 1e-5
    assert abs(first_row['drop_rate'] - 20.0) < 1e-5
    
    # Payment Added (4) -> First Purchase (2)
    last_row = funnel_df.iloc[-1]
    assert last_row['users_lost'] == 2
    assert abs(last_row['completion_rate'] - 50.0) < 1e-5
    assert abs(last_row['drop_rate'] - 50.0) < 1e-5


def test_calculate_business_impact(sample_funnel_df):
    """Verify revenue calculation and ranking logic."""
    stages = compute_funnel_stages(sample_funnel_df)
    funnel_df = compute_drop_offs(stages)
    impact_df = calculate_business_impact(funnel_df, revenue_per_customer=50.0)
    
    assert len(impact_df) == 5
    # First row in impact_df should be one of the largest drops (absolute users lost)
    # The absolute drop of Sign Up -> Email Entered is 2. Drop of Payment Added -> First Purchase is 2.
    assert impact_df.iloc[0]['users_lost'] == 2
    # Revenue impact for 2 lost users at $50 each should be $100
    assert impact_df.iloc[0]['revenue_impact'] == "$100"


def test_generate_recommendation_report(sample_funnel_df, temp_csv_path):
    """Verify report formatting and output writing."""
    stages = compute_funnel_stages(sample_funnel_df)
    funnel_df = compute_drop_offs(stages)
    impact_df = calculate_business_impact(funnel_df, revenue_per_customer=100.0)
    
    report_path = temp_csv_path.replace(".csv", ".txt")
    report = generate_recommendation_report(funnel_df, impact_df, revenue_per_customer=100.0, output_path=report_path)
    
    assert os.path.exists(report_path)
    assert "FUNNEL OPTIMIZATION & DROP-OFF DETECTION REPORT" in report
    assert "EXECUTIVE LEADERBOARD" in report
    assert "CRITICAL BOTTLENECK ANALYSIS" in report
    assert "ACTIONABLE STRATEGY" in report
